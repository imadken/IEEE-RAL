"""Declared analytical probe models; no physical observations or task outcomes."""

import itertools
import random
from fractions import Fraction

from dual_rec.recoverability.schema import FiniteProbeProblem


def model(
    successes,
    transitions,
    observations,
    *,
    costs=None,
    safe=None,
    enabled=None,
    path_safe=None,
    recovery_safe=None,
    initial=None,
    horizon=1,
    budget=None,
    require_safety=True,
    name="analytical",
):
    names = sorted(successes)
    actions = sorted(next(iter(successes.values())))
    costs = costs or {p: 1 for p in transitions}
    safe = safe or {s: True for s in names}
    states = [
        {
            "state_id": s,
            "physically_allowed": safe[s],
            "recoveries": [
                {
                    "action_id": a,
                    "task_success": successes[s][a],
                    "path_safe": (recovery_safe or {}).get((s, a), True),
                }
                for a in actions
            ],
        }
        for s in names
    ]
    probes = []
    for p, table in transitions.items():
        rows = []
        for s in names:
            on = (enabled or {}).get((p, s), True)
            row = {"state_id": s, "enabled": on}
            if on:
                target = table[s]
                row.update(
                    successor=target,
                    observation=observations[p][target],
                    path_safe=(path_safe or {}).get((p, s), True),
                )
            rows.append(row)
        probes.append({"probe_id": p, "cost": costs[p], "transitions": rows})
    return FiniteProbeProblem(
        model_id=name,
        source_scope="DECLARED_DETERMINISTIC_FINITE_MODEL",
        evidence_origin="ANALYTICAL_TRUTH_TABLE_NOT_ROBOT_OUTCOMES",
        calibration_available=False,
        assumptions=(
            "Complete known deterministic finite transition model",
            "All possible initial states retained; observations follow physical transitions",
            "Truth-table task success is analytical, not calibrated physical performance",
        ),
        states=states,
        recovery_actions=actions,
        probes=probes,
        initial_support=initial or names,
        horizon=horizon,
        max_probe_cost=budget,
        cost_unit="DECLARED_PROBE_COST_UNITS",
        require_physical_safety=require_safety,
    )


def three_world(*, horizon=1, budget=None):
    names = ("A", "B", "C", "dead_C")
    g = {s: {"retry": s in ("A", "B"), "realign": s == "C"} for s in names}
    t = {
        "full_diagnostic": {s: ("dead_C" if s == "C" else s) for s in names},
        "coarse_safe": {s: s for s in names},
    }
    o = {
        "full_diagnostic": {s: ("C" if s == "dead_C" else s) for s in names},
        "coarse_safe": {
            s: ("left" if s in ("A", "B") else "right" if s == "C" else "dead")
            for s in names
        },
    }
    return model(
        g,
        t,
        o,
        costs={"full_diagnostic": 1, "coarse_safe": 2},
        initial=["A", "B", "C"],
        horizon=horizon,
        budget=budget,
        name="supervisor_three_world_with_explicit_dead_state",
    )


def chain(depth):
    states = [f"{s}{i}" for s in ("A", "B") for i in range(depth + 1)]
    g = {s: {"retry": s == f"A{depth}", "realign": s == f"B{depth}"} for s in states}
    t, o, enabled = {}, {}, {}
    for j in range(depth):
        p = f"advance_{j}"
        t[p] = {s: f"{s[0]}{min(j + 1, depth)}" for s in states}
        o[p] = {s: (s[0] if j == depth - 1 else "unresolved") for s in states}
        enabled.update({(p, s): int(s[1:]) == j for s in states})
    return model(
        g,
        t,
        o,
        enabled=enabled,
        initial=["A0", "B0"],
        horizon=depth,
        name=f"requires_{depth}_physical_steps",
    )


def named_cases():
    cases = {
        "three_world": three_world(),
        "three_world_no_probe_horizon": three_world(horizon=0),
        "three_world_budget_one": three_world(budget=1),
        "two_step_required": chain(2),
        "three_step_required": chain(3),
    }
    g = {"A": {"retry": True}, "B": {"retry": True}}
    cases["immediate_common_macro"] = model(g, {}, {}, horizon=0)
    g = {"dead": {"retry": False}}
    cases["physically_allowed_but_irrecoverable"] = model(g, {}, {}, horizon=4)
    g = {"A": {"retry": True, "realign": False}, "B": {"retry": False, "realign": True}}
    cases["individual_options_no_common_diagnosis"] = model(
        g,
        {"blind": {"A": "A", "B": "B"}},
        {"blind": {"A": "same", "B": "same"}},
        horizon=3,
    )
    cases["zero_cost_loop_cannot_reset"] = model(
        g,
        {"loop": {"A": "A", "B": "B"}},
        {"loop": {"A": "same", "B": "same"}},
        costs={"loop": 0},
        horizon=4,
    )
    t = {"A_probe": {"A": "A", "B": "B"}, "B_probe": {"A": "A", "B": "B"}}
    o = {p: {s: s for s in g} for p in t}
    cases["exact_rational_cost_trap"] = model(
        g, t, o, costs={"A_probe": 1, "B_probe": Fraction(1) - Fraction(1, 10**30)}
    )
    cases["unsafe_intermediate_safe_endpoint"] = model(
        g, t, o, path_safe={("A_probe", "A"): False}, costs={"A_probe": 0, "B_probe": 2}
    )
    for on in (False, True):
        cases[f"terminal_macro_path_safety_{on}"] = model(
            {"A": {"retry": True}},
            {},
            {},
            recovery_safe={("A", "retry"): False},
            require_safety=on,
        )
        cases[f"initial_state_safety_{on}"] = model(
            {"A": {"retry": True}}, {}, {}, safe={"A": False}, require_safety=on
        )
    # A physically restorative action can improve success without revealing a bit.
    cases["physical_restoration_no_information"] = model(
        {"broken": {"retry": False}, "ready": {"retry": True}},
        {"restore": {"broken": "ready", "ready": "ready"}},
        {"restore": {"ready": "same", "broken": "same"}},
        initial=["broken"],
    )
    return cases


def random_cases(registration):
    rng = random.Random(registration["random_seed"])
    grid = registration["random_grid"]
    for n, m, h, rep in itertools.product(
        grid["states"], grid["probes"], grid["horizons"], range(grid["replicates"])
    ):
        states = [f"s{i}" for i in range(n)]
        g = {s: {a: bool(rng.randrange(2)) for a in ("r0", "r1")} for s in states}
        t = {f"p{j}": {s: rng.choice(states) for s in states} for j in range(m)}
        o = {p: {s: str(rng.randrange(2)) for s in states} for p in t}
        enabled = {(p, s): rng.random() > 0.10 for p in t for s in states}
        paths = {(p, s): rng.random() > 0.10 for p in t for s in states}
        safe = {s: rng.random() > 0.10 for s in states}
        costs = {p: Fraction(rng.randrange(4), rng.randrange(1, 4)) for p in t}
        budget = None if rep % 3 else Fraction(rng.randrange(5), 2)
        yield (
            (n, m, h, rep),
            model(
                g,
                t,
                o,
                costs=costs,
                safe=safe,
                enabled=enabled,
                path_safe=paths,
                initial=states,
                horizon=h,
                budget=budget,
                require_safety=rep % 2 == 0,
                name=f"seeded_{n}_{m}_{h}_{rep}",
            ),
        )


def exhaustive_cases():
    states = ("s0", "s1")
    for bits, targets, observed, safety, enable, h, on in itertools.product(
        itertools.product((False, True), repeat=2),
        itertools.product(states, repeat=2),
        itertools.product(("0", "1"), repeat=2),
        itertools.product((False, True), repeat=2),
        itertools.product((False, True), repeat=2),
        range(3),
        (False, True),
    ):
        yield model(
            {s: {"r": v} for s, v in zip(states, bits, strict=True)},
            {"p": dict(zip(states, targets, strict=True))},
            {"p": dict(zip(states, observed, strict=True))},
            safe=dict(zip(states, safety, strict=True)),
            enabled={("p", s): v for s, v in zip(states, enable, strict=True)},
            horizon=h,
            require_safety=on,
            name="complete_two_state_grid",
        )
