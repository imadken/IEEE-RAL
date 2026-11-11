"""Paired finite event/observation schedules and development-only calibration.

Only existing grounded symbolic actions change evaluator state. Observation
corruption is a separate persistent channel. Runtime contexts contain histories
and assumed parameters; actual rates, event identities and truth stay outside.
"""

import hashlib
import json
import math
import random
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.semantics import Action, Lit, Model, apply_action, regress
from dual_rec.monitoring.semantics import relevant_atoms as constraint_closure

from .contracts import FreshEpisode, Parameters, RevalidationContext

REGIMES = (
    "no_external",
    "hidden_nominal",
    "hidden_low",
    "hidden_high",
    "unrelated_event",
    "missing30",
    "noise02",
    "noise10",
    "delayed",
    "recent",
    "known_action",
)

RATES = {
    "no_external": (0.0, 0.0, 0.0),
    "hidden_nominal": (0.10, 0.0, 0.0),
    "hidden_low": (0.03, 0.0, 0.0),
    "hidden_high": (0.30, 0.0, 0.0),
    "unrelated_event": (1.0, 0.0, 0.0),
    "missing30": (0.10, 0.0, 0.30),
    "noise02": (0.0, 0.02, 0.0),
    "noise10": (0.0, 0.10, 0.0),
    "delayed": (0.10, 0.0, 0.0),
    "recent": (0.10, 0.0, 0.0),
    "known_action": (0.0, 0.0, 0.0),
}


def _random(key: str) -> random.Random:
    return random.Random(
        int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    )


def _event_probability(hazard: float, steps: int) -> float:
    if not steps or not hazard:
        return 0.0
    if hazard == 1:
        return 1.0
    return -math.expm1(steps * math.log1p(-hazard))


@lru_cache(maxsize=4096)
def _successors(
    actions: tuple[Action, ...], state: frozenset[str]
) -> tuple[tuple[Action, frozenset[str]], ...]:
    """Uniform over applicable changing actions, retaining action multiplicity."""
    result = []
    for action in sorted(actions, key=lambda item: item.name):
        if any((lit.atom in state) != lit.positive for lit in action.pre):
            continue
        successor = apply_action(action, state)
        if successor != state:
            result.append((action, successor))
    return tuple(result)


def _event(
    actions: tuple[Action, ...],
    state: frozenset[str],
    hazard: float,
    steps: int,
    rng: random.Random,
) -> tuple[frozenset[str], str | None]:
    chance = _event_probability(hazard, steps)
    if rng.random() >= chance:
        return state, None
    candidates = _successors(actions, state)
    if not candidates:
        return state, None
    action, successor = candidates[rng.randrange(len(candidates))]
    return successor, action.name


@lru_cache(maxsize=4096)
def support_consequence(
    plan: tuple[Action, ...], goal: tuple[Lit, ...]
) -> dict[str, float]:
    """Signed initial-support causal descendants; no current-action boost here."""
    required = regress(plan, goal)
    if required is None:
        raise ValueError("Nominal retained plan has contradictory regression")
    producer = {}
    edges = []
    for index in range(len(plan) + 1):
        conditions = goal if index == len(plan) else plan[index].pre
        for literal in conditions:
            edges.append((producer.get(literal, -1), index, literal))
        if index < len(plan):
            effects = [Lit(atom=atom) for atom in plan[index].add]
            effects += [Lit(atom=atom, positive=False) for atom in plan[index].delete]
            for literal in effects:
                producer.pop(literal.negate(), None)
                producer[literal] = index
    result = {}
    for literal in required:
        reached = {
            target
            for source, target, condition in edges
            if source == -1 and condition == literal
        }
        frontier = list(reached)
        while frontier:
            node = frontier.pop()
            for source, target, _ in edges:
                if source == node and target not in reached:
                    reached.add(target)
                    frontier.append(target)
        result[literal.atom] = 1.0 + sum(0 <= node < len(plan) for node in reached)
    return result


def _task_inputs(
    task: dict,
) -> tuple[
    Model, tuple[Action, ...], tuple[Action, ...], tuple[Lit, ...], tuple[str, ...]
]:
    model = Model.model_validate(task["model"])
    actions = tuple(Action.model_validate(a) for a in task["actions"])
    plan = tuple(Action.model_validate(a) for a in task["plan"])
    goal = tuple(Lit.model_validate(lit) for lit in task["goal"])
    if not plan:
        raise ValueError("An empty nominal plan supplies no pending action")
    fixed = {clause[0].atom for clause in model.constraints if len(clause) == 1}
    dynamic = tuple(sorted(model.atoms - fixed))
    return model, actions, plan, goal, dynamic


def generate_episodes(
    tasks: list[dict], split: str, parameters: Parameters, schedules: int = 8
) -> Iterator[FreshEpisode]:
    """Yield fixed paired histories without exposing evaluator labels at runtime."""
    if split not in {"development", "qualification", "control"}:
        raise ValueError("Unknown split")
    if type(schedules) is not int or schedules < 1:
        raise ValueError("Schedule count must be positive")
    for task in tasks:
        if task.get("split") != split:
            continue
        model, actions, plan, goal, dynamic = _task_inputs(task)
        queries = tuple(Query(name=atom, atoms=frozenset({atom})) for atom in dynamic)
        checkpoints = sorted({len(plan) // 3, (2 * len(plan)) // 3})
        for checkpoint in checkpoints:
            suffix = plan[checkpoint:]
            full_closure = constraint_closure(model, {}, suffix, goal)
            nominal = frozenset(task["nominal_states"][checkpoint])
            consequence = support_consequence(suffix, goal)
            for schedule in range(schedules):
                default_age = (1, 2, 4)[schedule % 3]
                for regime in REGIMES:
                    episode_id = f"{task['task_id']}/{checkpoint}/{schedule}/{regime}"
                    rng = _random("evaluation/" + episode_id)
                    hazard, eta, missing = RATES[regime]
                    age = 0 if regime in {"recent", "known_action"} else default_age
                    pre_gap = 0 if regime in {"unrelated_event", "known_action"} else 1
                    cache_time = -1 if regime == "known_action" else 0
                    known = ()
                    anchor = nominal
                    if regime == "known_action":
                        if checkpoint == 0:
                            raise ValueError(
                                "Known-action control requires a preceding action"
                            )
                        anchor = frozenset(task["nominal_states"][checkpoint - 1])
                        known = (plan[checkpoint - 1],)
                    cache_world, pre_event = _event(
                        actions, anchor, hazard, pre_gap, rng
                    )
                    bias = frozenset(atom for atom in dynamic if rng.random() < eta)
                    cached = {atom: atom in cache_world for atom in sorted(model.atoms)}
                    for atom in dynamic:
                        cached[atom] = (atom in cache_world) != (atom in bias)
                        if rng.random() < missing:
                            cached[atom] = None
                    after_known = cache_world
                    for action in known:
                        after_known = apply_action(action, after_known)
                    if regime == "unrelated_event":
                        choices = [
                            (a, successor)
                            for a, successor in _successors(actions, after_known)
                            if not ((successor ^ after_known) & full_closure)
                        ]
                        if choices:
                            action, world = choices[rng.randrange(len(choices))]
                            post_event = action.name
                        else:
                            world, post_event = after_known, None
                    else:
                        world, post_event = _event(
                            actions, after_known, hazard, age, rng
                        )
                    missing_queries = frozenset(
                        atom for atom in dynamic if rng.random() < missing
                    )
                    anchor_time = cache_time - pre_gap
                    observed_at = {
                        atom: cache_time if cached[atom] is not None else anchor_time
                        for atom in sorted(model.atoms)
                    }
                    updated_at = dict(observed_at)
                    observation_sources = {
                        atom: "symbolic_model"
                        if atom not in dynamic
                        else "symbolic_inspection"
                        if cached[atom] is not None
                        else "trusted_anchor"
                        for atom in sorted(model.atoms)
                    }
                    update_sources = dict(observation_sources)
                    evidence = {
                        atom: cached[atom]
                        if cached[atom] is not None
                        else atom in anchor
                        for atom in sorted(model.atoms)
                    }
                    for action in known:
                        for atom in action.add:
                            evidence[atom] = True
                            updated_at[atom] = 0
                            update_sources[atom] = "known_action:" + action.name
                        for atom in action.delete:
                            evidence[atom] = False
                            updated_at[atom] = 0
                            update_sources[atom] = "known_action:" + action.name
                    base = Context(
                        model=model,
                        evidence=evidence,
                        plan=suffix,
                        goal=goal,
                        queries=queries,
                        consequence=dict(consequence),
                        schedule_offset=0,
                    )
                    ctx = RevalidationContext(
                        base=base,
                        actions=actions,
                        trusted_anchor=anchor,
                        cache_observations=cached,
                        observed_at=observed_at,
                        updated_at=updated_at,
                        observation_sources=observation_sources,
                        update_sources=update_sources,
                        known_after_cache=known,
                        pre_gap=pre_gap,
                        age=age,
                        cache_time=cache_time,
                        query_delay=age if regime == "delayed" else 0,
                        parameters=parameters,
                    )
                    yield FreshEpisode(
                        episode_id=episode_id,
                        parent_id=task["task_id"],
                        family=task["family"],
                        split=split,
                        checkpoint=checkpoint,
                        schedule=schedule,
                        regime=regime,
                        context=ctx,
                        oracle_cache_state=cache_world,
                        oracle_state=world,
                        persistent_bias=bias,
                        missing_queries=missing_queries,
                        external_actions=(pre_event, post_event),
                        actual_event_hazard=hazard,
                        actual_sensor_error=eta,
                        source_hashes=task["source_hashes"],
                    )


def calibration(tasksdev: list[dict], output: Path) -> Parameters:
    """Fit only development observations, with predeclared supervised truth audit.

    The independent validated source trajectory and exact public transition
    model provide offline development labels. Qualification observations or
    frequencies are not accepted. Global event hazard uses Beta(1,9) smoothing;
    bit-error probability uses Beta(1,49). No scheduler outcome selects a value.
    """
    if not tasksdev or any(task.get("split") != "development" for task in tasksdev):
        raise ValueError("Calibration requires development-only tasks")
    events = intervals = errors = measured_bits = 0
    parents = []
    for task in tasksdev:
        _, actions, plan, _, dynamic = _task_inputs(task)
        parents.append(task["task_id"])
        for checkpoint in sorted({len(plan) // 3, (2 * len(plan)) // 3}):
            anchor = frozenset(task["nominal_states"][checkpoint])
            for schedule in range(64):
                rng = _random(f"calibration/{task['task_id']}/{checkpoint}/{schedule}")
                after, event = _event(actions, anchor, 0.10, 1, rng)
                events += event is not None
                intervals += 1
                for atom in dynamic:
                    corrupted = rng.random() < 0.02
                    reading = (atom in after) != corrupted
                    errors += reading != (atom in after)
                    measured_bits += 1
    parameters = Parameters(
        event_hazard=(events + 1) / (intervals + 10),
        sensor_error=(errors + 1) / (measured_bits + 50),
        missing_probability=0.10,
        permission_threshold=0.95,
        periodic_interval=1,
        expiry_steps=1,
    )
    payload = {
        "scope": "Supervised development-only transition/sensor calibration; no qualification frequencies",
        "parents": sorted(parents),
        "n_parents": len(parents),
        "unit_intervals": intervals,
        "observed_state_changes": events,
        "sensor_bits": measured_bits,
        "sensor_errors": errors,
        "event_model": "At most one uniformly selected applicable changing action per interval",
        "true_development_event_hazard": 0.10,
        "true_development_sensor_error": 0.02,
        "smoothing": {"event": "Beta(1,9)", "sensor": "Beta(1,49)"},
        "parameters": parameters.model_dump(mode="json"),
        "source_hashes": {task["task_id"]: task["source_hashes"] for task in tasksdev},
    }
    output = Path(output)
    if output.suffix != ".json":
        output = output / "calibration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
    return parameters
