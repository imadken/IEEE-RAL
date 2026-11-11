"""Common finite-query interface with original LOGIV and simple baselines."""

from collections.abc import Callable
from time import perf_counter

from .contracts import Context, Decision, Query
from .semantics import certify, relevant_atoms
from .upstream import load_upstream

Sensing = Callable[[str], dict[str, bool]]


def run_method(context: Context, method: str, budget: int, sense: Sensing) -> Decision:
    if method not in {"M0", "M1", "M2", "M3", "M3_no_consequence", "M4"}:
        raise ValueError(method)
    if type(budget) is not int or not 0 <= budget <= 3:
        raise ValueError("Budget must be 0..3")
    started = perf_counter()
    evidence = dict(context.evidence)
    names, atoms, answers = [], [], []
    sensor_seconds = 0.0
    irrelevant_atoms = 0
    total_atoms = 0
    queries = tuple(sorted(context.queries, key=lambda query: query.name))

    def acquire(query: Query) -> None:
        nonlocal sensor_seconds, irrelevant_atoms, total_atoms
        if (
            sum(next(q.cost for q in queries if q.name == name) for name in names)
            + query.cost
            > budget
        ):
            raise RuntimeError("Observation budget exceeded")
        if query.name in names:
            raise RuntimeError("A view cannot be queried twice")
        relevant = relevant_atoms(context.model, evidence, context.plan, context.goal)
        before = perf_counter()
        response = sense(query.name)
        sensor_seconds += perf_counter() - before
        if set(response) != query.atoms or any(
            type(v) is not bool for v in response.values()
        ):
            raise ValueError("Sensing response differs from the common query contract")
        names.append(query.name)
        atoms.append(tuple(sorted(query.atoms)))
        answers.append(dict(response))
        irrelevant_atoms += len(query.atoms - relevant)
        total_atoms += len(query.atoms)
        evidence.update(response)

    periodic = (
        queries[context.schedule_offset % len(queries) :]
        + queries[: context.schedule_offset % len(queries)]
        if queries
        else ()
    )
    if method == "M0":
        upstream = load_upstream()
        from logiv.core.verification import Observation, Verifier

        class Runtime:
            index = 0

            def observe(self, active=False):
                if active and self.index < len(periodic):
                    acquire(periodic[self.index])
                    self.index += 1
                return Observation(
                    raw={tuple(atom.split()): value for atom, value in evidence.items()}
                )

        class Perception:
            def assess(self, observation, requested):
                return {atom: observation.raw.get(atom) for atom in requested}

        fixed = {
            clause[0].atom for clause in context.model.constraints if len(clause) == 1
        }
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
        runtime = Runtime()
        required = frozenset(
            upstream.Literal(tuple(lit.atom.split()), lit.positive)
            for lit in context.plan[0].pre
        )
        verifier = Verifier(
            runtime,
            Perception(),
            additional_observations=min(budget, len(queries)),
            tracked_atoms=frozenset(
                tuple(atom.split()) for atom in context.model.atoms - fixed
            ),
            static_predicates=frozenset(atom.split()[0] for atom in fixed),
        )
        state, _, resolved = verifier.state_gate(state, required, runtime.observe())
        if not resolved:
            status, choice = "UNRESOLVED", "ABSTAIN"
        elif state.holds(required):
            status, choice = "CURRENT_VALID", "CONTINUE"
        else:
            status, choice = "CURRENT_INVALID", "RECOVER"
    else:
        if method == "M4":
            from .oracle import select_exact

            # Enforce the reference's declared bounds even for an already
            # resolved continuation; never silently call it a general ceiling.
            select_exact(context, evidence, budget)
        if method == "M2":
            for query in periodic[:budget]:
                acquire(query)
        status = certify(context.model, evidence, context.plan, context.goal)
        while (
            method in {"M1", "M3", "M3_no_consequence", "M4"}
            and status == "UNRESOLVED"
            and len(names) < budget
        ):
            relevant = relevant_atoms(
                context.model, evidence, context.plan, context.goal
            )
            candidates = [
                q for q in queries if q.name not in names and q.atoms & relevant
            ]
            if not candidates:
                break
            if method == "M4":
                name = select_exact(context, evidence, budget - len(names))
                if name is None:
                    break
                selected = next(q for q in candidates if q.name == name)
            else:

                def score(query, relevant=relevant):
                    if method == "M3":
                        return (
                            sum(
                                context.consequence.get(atom, 1.0)
                                for atom in query.atoms & relevant
                            )
                            / query.cost
                        )
                    return len(query.atoms & relevant) / query.cost

                selected = min(candidates, key=lambda q: (-score(q), q.name))
            acquire(selected)
            status = certify(context.model, evidence, context.plan, context.goal)
        choice = (
            "CONTINUE"
            if status == "VALID"
            else "RECOVER"
            if status == "INVALID"
            else "ABSTAIN"
        )
    return Decision(
        method=method,
        choice=choice,
        evidence=evidence,
        status=status,
        query_names=tuple(names),
        query_atoms=tuple(atoms),
        query_answers=tuple(answers),
        query_seconds=sensor_seconds,
        decision_seconds=perf_counter() - started,
        query_irrelevant_atoms=irrelevant_atoms,
        query_total_atoms=total_atoms,
    )
