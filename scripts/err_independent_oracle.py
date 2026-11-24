"""Independent exhaustive/MILP checks; never import production cover helpers."""

from fractions import Fraction
from itertools import combinations
from math import lcm

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def parse(raw):
    worlds = sorted(raw["worlds"], key=lambda w: w["world_id"])
    experiments = sorted(raw["experiments"], key=lambda e: e["experiment_id"])
    pairs = [
        (a["world_id"], b["world_id"])
        for a, b in combinations(worlds, 2)
        if a["obligation_verdict"] != b["obligation_verdict"]
    ]
    laws = {
        e["experiment_id"]: {
            row["world_id"]: dict(
                zip(e["alphabet"], map(Fraction, row["probabilities"]), strict=True)
            )
            for row in e["laws"]
        }
        for e in experiments
    }
    return experiments, pairs, laws


def exhaustive(raw):
    experiments, pairs, laws = parse(raw)
    choices = []
    for k in range(len(experiments) + 1):
        for selected in combinations(experiments, k):
            if all(
                any(
                    laws[e["experiment_id"]][a] != laws[e["experiment_id"]][b]
                    for e in selected
                )
                for a, b in pairs
            ):
                names = tuple(e["experiment_id"] for e in selected)
                choices.append(
                    (
                        sum((Fraction(e["cost"]) for e in selected), Fraction(0)),
                        k,
                        names,
                    )
                )
    if not choices:
        return None
    cost, _, names = min(choices)
    return cost, names


def integer_program(raw):
    experiments, pairs, laws = parse(raw)
    if not pairs:
        return Fraction(0), ()
    if not experiments:
        return None
    n = len(experiments)
    costs = [Fraction(e["cost"]) for e in experiments]
    scale = lcm(*(c.denominator for c in costs))
    tie_unit = 2**n
    major = (n + 1) * tie_unit
    objective = [
        int(c * scale) * major + tie_unit - 2 ** (n - i - 1)
        for i, c in enumerate(costs)
    ]
    if max(objective, default=0) > 2**40:
        raise ValueError("MILP_DOUBLE_INTEGER_RANGE_UNSUPPORTED_USE_EXACT_ORACLE")
    matrix = np.array(
        [
            [
                int(laws[e["experiment_id"]][a] != laws[e["experiment_id"]][b])
                for e in experiments
            ]
            for a, b in pairs
        ],
        dtype=float,
    )
    result = milp(
        np.array(objective, dtype=float),
        integrality=np.ones(n),
        bounds=Bounds(np.zeros(n), np.ones(n)),
        constraints=LinearConstraint(
            matrix, np.ones(len(pairs)), np.full(len(pairs), np.inf)
        ),
        options={"mip_rel_gap": 0.0},
    )
    if result.status == 2:
        return None
    assert result.success, result.message
    bits = np.rint(result.x).astype(int)
    assert np.max(abs(result.x - bits)) < 1e-7 and np.all(matrix @ bits >= 1)
    selected = tuple(
        e["experiment_id"] for e, bit in zip(experiments, bits, strict=True) if bit
    )
    cost = sum((c for c, bit in zip(costs, bits, strict=True) if bit), Fraction(0))
    return cost, selected


def greedy(raw, *, reverse_delete=False):
    experiments, pairs, laws = parse(raw)
    remaining = set(pairs)
    covers = {
        e["experiment_id"]: {
            (a, b)
            for a, b in pairs
            if laws[e["experiment_id"]][a] != laws[e["experiment_id"]][b]
        }
        for e in experiments
    }
    selected = []
    while remaining:
        capable = [e for e in experiments if covers[e["experiment_id"]] & remaining]
        if not capable:
            return None

        def key(e, remaining=remaining):
            gain, cost = (
                len(covers[e["experiment_id"]] & remaining),
                Fraction(e["cost"]),
            )
            return (
                0 if cost == 0 else 1,
                -gain if cost == 0 else -Fraction(gain, 1) / cost,
                e["experiment_id"],
            )

        best = min(capable, key=key)
        selected.append(best)
        remaining -= covers[best["experiment_id"]]
    if reverse_delete:
        for e in list(reversed(selected)):
            other = [x for x in selected if x["experiment_id"] != e["experiment_id"]]
            if set().union(*(covers[x["experiment_id"]] for x in other)) == set(pairs):
                selected = other
    return sum((Fraction(e["cost"]) for e in selected), Fraction(0)), tuple(
        sorted(e["experiment_id"] for e in selected)
    )


def verify_witnesses(raw, result):
    experiments, pairs, laws = parse(raw)
    if result["status"] == "NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE":
        a, b = result["impossibility"]["worlds"]
        assert (a, b) in pairs and all(
            laws[e["experiment_id"]][a] == laws[e["experiment_id"]][b]
            for e in experiments
        )
        assert len(result["impossibility"]["identical_laws"]) == len(experiments)
        original_worlds = {
            w["world_id"]: w["obligation_verdict"] for w in raw["worlds"]
        }
        assert result["impossibility"]["verdicts"] == [
            original_worlds[a],
            original_worlds[b],
        ]
        for witness in result["impossibility"]["identical_laws"]:
            given = dict(
                zip(
                    witness["alphabet"],
                    map(Fraction, witness["probabilities"]),
                    strict=True,
                )
            )
            assert (
                given
                == laws[witness["experiment_id"]][a]
                == laws[witness["experiment_id"]][b]
            )
        return
    chosen = set(result["selected_experiments"])
    assert all(any(laws[e][a] != laws[e][b] for e in chosen) for a, b in pairs)
    assert len(result["coverage"]) == len(pairs)
    for record in result["coverage"]:
        a, b = record["worlds"]
        assert (a, b) in pairs
        assert record["experiments"] and all(
            e in chosen and laws[e][a] != laws[e][b] for e in record["experiments"]
        )
    assert len(result["removal_witnesses"]) == len(chosen)
    for witness in result["removal_witnesses"]:
        removed = witness["removed_experiment"]
        a, b = witness["unseparated_opposing_worlds"]
        assert (a, b) in pairs and removed in chosen
        assert all(laws[e][a] == laws[e][b] for e in chosen - {removed})
