"""Common bounded adapter to LOGIV's existing retained-plan repair mechanism."""

from collections import deque
from functools import lru_cache
from time import process_time

from .contracts import Context
from .semantics import Action, Lit, certify, regress
from .upstream import as_action, load_upstream


@lru_cache(maxsize=50000)
def _operator(action: Action):
    upstream = load_upstream()
    name, *arguments = action.name.split()
    return upstream.Operator(
        name,
        tuple(arguments),
        frozenset(
            upstream.Literal(tuple(lit.atom.split()), lit.positive)
            for lit in action.pre
        ),
        frozenset(
            [upstream.Literal(tuple(atom.split())) for atom in action.add]
            + [upstream.Literal(tuple(atom.split()), False) for atom in action.delete]
        ),
    )


def recover(
    context: Context, evidence: dict[str, bool | None], actions: tuple[Action, ...]
) -> dict:
    """No evaluator state is accepted; successful combined plans are conformant."""
    upstream = load_upstream()
    from logiv.core.graph import START, build_graph
    from logiv.core.repair import Repairer
    from logiv.core.verification import Failure, FailureKind
    from logiv.planning.solver import Validation

    required = regress(context.plan, context.goal)
    if required is None:
        return {"success": False, "reason": "IMPOSSIBLE_NOMINAL_PLAN", "plan": []}
    operators = tuple(_operator(action) for action in actions)
    retained = tuple(_operator(action) for action in context.plan)
    goal = frozenset(
        upstream.Literal(tuple(lit.atom.split()), lit.positive) for lit in context.goal
    )
    # Compile only the declared plan's support graph. This witness is not used as
    # runtime evidence, a guessed completion, or a planning initial state.
    compile_state = upstream.State(
        frozenset(tuple(lit.atom.split()) for lit in required if lit.positive)
    )
    graph = build_graph(compile_state, retained, goal)
    state = upstream.State(
        frozenset(
            tuple(atom.split()) for atom, value in evidence.items() if value is True
        ),
        frozenset(
            tuple(atom.split())
            for atom in context.model.atoms
            if evidence.get(atom) is None
        ),
    )
    search_started = process_time()
    stats = {"expanded": 0, "planner_calls": 0, "validator_calls": 0, "limit_hits": 0}

    class Planner:
        def plan(self, initial, target):
            stats["planner_calls"] += 1
            start = process_time()
            queue = deque([(initial, ())])
            seen = {(initial.facts, initial.unknown)}
            while queue:
                if stats["expanded"] >= 2000 or process_time() - start >= 0.10:
                    stats["limit_hits"] += 1
                    return None
                current, fragment = queue.popleft()
                stats["expanded"] += 1
                if current.holds(target):
                    return fragment
                if len(fragment) >= 8:
                    continue
                for action in operators:
                    if not current.holds(action.preconditions):
                        continue
                    successor = action.apply(current)
                    key = successor.facts, successor.unknown
                    if key not in seen:
                        if len(seen) >= 2000:
                            stats["limit_hits"] += 1
                            return None
                        seen.add(key)
                        queue.append((successor, fragment + (action,)))
            return None

    class Validator:
        def validate(self, initial, plan, target):
            stats["validator_calls"] += 1
            knowledge = {
                atom: initial.truth(upstream.Literal(tuple(atom.split())))
                for atom in context.model.atoms
            }
            own_goal = tuple(
                Lit(atom=" ".join(lit.atom), positive=lit.positive)
                for lit in sorted(target)
            )
            own_plan = tuple(as_action(action) for action in plan)
            if certify(context.model, knowledge, own_plan, own_goal) == "VALID":
                return Validation(True)
            for index in range(len(own_plan)):
                if (
                    certify(
                        context.model, knowledge, own_plan[:index], own_plan[index].pre
                    )
                    != "VALID"
                ):
                    return Validation(False, index, "UNIVERSAL_PRECONDITION_FAILURE")
            return Validation(False, detail="UNIVERSAL_GOAL_FAILURE")

    broken = next(
        (
            edge
            for edge in graph.edges
            if edge.source == START
            and edge.condition is not None
            and evidence.get(" ".join(edge.condition.atom)) is not None
            and evidence[" ".join(edge.condition.atom)] != edge.condition.positive
        ),
        None,
    )
    false_index = broken.target if broken is not None else 0
    kind = (
        FailureKind.GOAL if false_index == graph.goal_node else FailureKind.PRECONDITION
    )
    failure = Failure(kind, false_index, broken.condition if broken else None, broken)
    repaired = Repairer(Planner(), Validator()).repair(state, failure, graph)
    result = {
        "success": repaired is not None,
        "reason": "REPAIRED" if repaired else "NO_CERTIFIED_REPAIR",
        "plan": [as_action(action).model_dump(mode="json") for action in repaired.plan]
        if repaired
        else [],
        "cpu_seconds": process_time() - search_started,
        **stats,
    }
    if repaired is not None:
        assert (
            certify(
                context.model,
                evidence,
                tuple(as_action(a) for a in repaired.plan),
                context.goal,
            )
            == "VALID"
        )
    return result
