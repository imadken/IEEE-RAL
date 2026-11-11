"""Locked paired observation schedules for public symbolic task instances."""

import hashlib
import random
from collections.abc import Iterator

from .contracts import Context, Episode, Query
from .semantics import Action, Lit, Model, apply_action

REGIMES = (
    "complete",
    "missing10",
    "missing30",
    "missing50",
    "structured",
    "delayed",
    "noise05",
    "invalidated",
)


def generate_episodes(
    prepared: list[dict], split: str, schedules: int = 4
) -> Iterator[Episode]:
    for task in prepared:
        if task["split"] != split:
            continue
        model = Model.model_validate(task["model"])
        actions = tuple(Action.model_validate(a) for a in task["actions"])
        plan = tuple(Action.model_validate(a) for a in task["plan"])
        goal = tuple(Lit.model_validate(lit) for lit in task["goal"])
        fixed = {clause[0].atom for clause in model.constraints if len(clause) == 1}
        dynamic = sorted(model.atoms - fixed)
        groups: dict[str, set[str]] = {}
        for atom in dynamic:
            groups.setdefault(atom.split()[0], set()).add(atom)
        queries = tuple(
            Query(name=name, atoms=frozenset(atoms))
            for name, atoms in sorted(groups.items())
        )
        checkpoints = sorted({0, len(plan) // 2, len(plan) - 1})
        for checkpoint in checkpoints:
            nominal = frozenset(task["nominal_states"][checkpoint])
            for schedule in range(schedules):
                for regime in REGIMES:
                    episode_id = f"{task['task_id']}/{checkpoint}/{schedule}/{regime}"
                    key = int.from_bytes(
                        hashlib.sha256(episode_id.encode()).digest()[:8], "big"
                    )
                    rng = random.Random(key)
                    world = nominal
                    disturbance = None
                    timing = {
                        "measured_at": checkpoint,
                        "available_at": checkpoint,
                        "invalidated": [],
                    }
                    readings = {atom: atom in nominal for atom in sorted(model.atoms)}
                    if regime.startswith("missing"):
                        rate = int(regime.removeprefix("missing")) / 100
                        for atom in dynamic:
                            if rng.random() < rate:
                                readings[atom] = None
                    elif regime == "structured":
                        hidden = queries[rng.randrange(len(queries))]
                        for atom in hidden.atoms:
                            readings[atom] = None
                        timing["missing_channel"] = hidden.name
                    elif regime == "delayed" and checkpoint:
                        previous = frozenset(task["nominal_states"][checkpoint - 1])
                        prior_action = plan[checkpoint - 1]
                        readings = {
                            atom: atom in previous for atom in sorted(model.atoms)
                        }
                        for atom in prior_action.add | prior_action.delete:
                            readings[atom] = None
                        timing = {
                            "measured_at": checkpoint - 1,
                            "available_at": checkpoint,
                            "invalidated": sorted(
                                prior_action.add | prior_action.delete
                            ),
                        }
                    elif regime == "invalidated":
                        applicable = []
                        for action in actions:
                            if action.name == plan[checkpoint].name:
                                continue
                            try:
                                successor = apply_action(action, nominal)
                            except ValueError:
                                continue
                            if successor != nominal:
                                applicable.append((action, successor))
                        if applicable:
                            action, world = applicable[rng.randrange(len(applicable))]
                            disturbance = action.name
                        timing["unannounced_external_transition"] = disturbance
                        for atom in dynamic:
                            if rng.random() < 0.30:
                                readings[atom] = None
                    answers = {atom: atom in world for atom in dynamic}
                    if regime == "noise05":
                        for atom in dynamic:
                            if rng.random() < 0.05:
                                readings[atom] = not readings[atom]
                                answers[atom] = not answers[atom]
                        timing["model_misspecification"] = (
                            "persistent_5_percent_bit_corruption"
                        )
                    weights = task.get("consequence", [{}] * len(plan))[checkpoint]
                    yield Episode(
                        episode_id=episode_id,
                        parent_id=task["task_id"],
                        family=task["family"],
                        split=split,
                        checkpoint=checkpoint,
                        schedule=schedule,
                        regime=regime,
                        context=Context(
                            model=model,
                            evidence=readings,
                            plan=plan[checkpoint:],
                            goal=goal,
                            queries=queries,
                            consequence=weights,
                            schedule_offset=checkpoint + schedule,
                        ),
                        oracle_state=world,
                        nominal_state=nominal,
                        sensor_answers=answers,
                        actions=actions,
                        source_hashes=task["source_hashes"],
                        evidence_timing=timing,
                        disturbance_action=disturbance,
                    )
