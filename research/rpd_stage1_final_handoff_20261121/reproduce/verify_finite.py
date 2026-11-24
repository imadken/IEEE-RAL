"""Independent exhaustive one-probe oracle for the V4.4 analytical illustration."""

import argparse
import json
import math
from fractions import Fraction
from itertools import product
from pathlib import Path


def policy_oracle(worlds, successor, observation, recovery):
    """Enumerate all response-contingent actions, including explicit STOP.

    Physical transitions occur exactly once, before correction. Dead successors
    cannot be reset to their root world. Every path has one probe+one action tick.
    """
    responses = sorted({observation[w] for w in worlds})
    best = Fraction(0)
    robust = False
    for actions in product(("a0", "a1", "STOP"), repeat=len(responses)):
        plan = dict(zip(responses, actions))
        flags = [plan[observation[w]] in recovery[successor[w]] for w in worlds]
        best = max(best, Fraction(sum(flags), len(worlds)))
        robust |= all(flags)
    return best, robust


def common_set_test(worlds, successor, observation, recovery):
    actions_by_response = {}
    for world in worlds:
        response = observation[world]
        if response not in actions_by_response:
            actions_by_response[response] = set(recovery[successor[world]])
        else:
            actions_by_response[response] &= recovery[successor[world]]
    return all(actions_by_response.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    worlds = [z + str(k) for z in "ABC" for k in range(2)]
    recovery = {w: ({"a0"} if w[0] in "AB" else {"a1"}) for w in worlds}
    recovery["dead"] = set()
    identity = {w: w for w in worlds}
    fine = {w: w[0] for w in worlds}
    coarse = {w: "AB" if w[0] in "AB" else "C" for w in worlds}
    rows = []
    for intensity, destroyed in ((".2", ()), (".5", ("C0",)), (".8", ("C0", "C1"))):
        successor = {w: ("dead" if w in destroyed else w) for w in worlds}
        fine_value, robust_fine = policy_oracle(worlds, successor, fine, recovery)
        coarse_value, robust_coarse = policy_oracle(worlds, identity, coarse, recovery)
        erased = sum(bool(recovery[w]) and not recovery[successor[w]] for w in worlds)
        assert fine_value == 1 - Fraction(erased, 6)
        assert coarse_value == 1 and robust_coarse
        assert robust_fine == (not destroyed)
        rows.append(
            {
                "intensity": intensity,
                "hold_preserves": "1",
                "fine_erasure": str(Fraction(erased, 6)),
                "fine_completion": str(fine_value),
                "RPD_completion": str(coarse_value),
                "same_objective_planner_completion": str(coarse_value),
                "physically_allowed_states_include_dead": True,
            }
        )
    # Independent full enumeration of 64 recovery catalogues, 27 transitions and
    # five observation partitions: logical existence vs a policy-tree oracle.
    roots = ["A", "B", "C"]
    partitions = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 2)]
    checked = 0
    for masks in product(range(4), repeat=3):
        success = {
            w: {a for bit, a in enumerate(("a0", "a1")) if mask & (1 << bit)}
            for w, mask in zip(roots, masks)
        }
        for destinations in product(roots, repeat=3):
            transition = dict(zip(roots, destinations))
            for labels in partitions:
                observations = dict(zip(roots, labels))
                _, oracle = policy_oracle(roots, transition, observations, success)
                criterion = common_set_test(roots, transition, observations, success)
                assert oracle == criterion
                checked += 1
    report = {
        "scope": "ANALYTICAL_ONLY; not robot episodes or a new planning theorem",
        "fine_mode_information_nats": math.log(3),
        "coarse_mode_information_nats": -2 / 3 * math.log(2 / 3)
        - 1 / 3 * math.log(1 / 3),
        "constructed_sweep": rows,
        "independent_policy_tree_cases": checked,
        "common_set_criterion_matches_oracle": True,
        "same_objective_equivalence": True,
        "implicit_resets": 0,
        "physics_episodes": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
