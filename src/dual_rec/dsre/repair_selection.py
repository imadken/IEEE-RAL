"""Fixed six-channel telemetry menu and exact offline observation refinement."""

import math
import random
from collections import Counter, defaultdict
from itertools import combinations

from .features import ObservationHistory

OPTIONAL = (
    "object_left_of_goal_02",
    "object_right_of_goal_02",
    "object_behind_goal_02",
    "object_ahead_of_goal_02",
    "hand_left_of_object_02",
    "hand_right_of_object_02",
)


def optional_values(history: ObservationHistory):
    frame = history.current
    obj, goal, hand = frame.object_position, frame.goal_position, frame.tcp_position

    def delta(left, right, coordinate):
        if left is None or right is None:
            return None
        value = left[coordinate] - right[coordinate]
        return value if math.isfinite(value) else None

    dx, dy, hx = delta(obj, goal, 0), delta(obj, goal, 1), delta(hand, obj, 0)
    return tuple(
        None if v is None else v < -0.02 if sign < 0 else v > 0.02
        for v, sign in ((dx, -1), (dx, 1), (dy, -1), (dy, 1), (hx, -1), (hx, 1))
    )


def values(row, selected, privileged=False):
    result = tuple(row["features"]) + tuple(
        row["optional_features"][i] for i in selected
    )
    return result + tuple(row["privileged_features"][-2:]) if privileged else result


def good(row):
    outcomes = row["outcomes"]
    if not row.get("qualified", True) or None in outcomes.values():
        return set()
    return {a for a in ("continue", "recover") if outcomes[a + "_value"]}


def partition(rows, selected, privileged=False):
    groups = defaultdict(list)
    for row in rows:
        groups[values(row, selected, privileged)].append(row)
    return groups


def ceiling_mass(rows, selected, privileged=False):
    total = 0
    for group in partition(rows, selected, privileged).values():
        actions = {"continue", "recover"}
        for row in group:
            actions &= good(row)
        if actions:
            total += len(group)
    return total


def conditional_entropy(rows, selected):
    if not rows:
        return 0.0
    entropy = 0.0
    for group in partition(rows, selected).values():
        counts = Counter(tuple(sorted(good(row))) for row in group)
        entropy -= sum(n * math.log2(n / len(group)) for n in counts.values()) / len(
            rows
        )
    return entropy


def select_channels(
    rows, budget, method="exact_coverage", available=tuple(range(6)), seed=20261113
):
    if (
        budget not in range(4)
        or len(set(available)) != len(available)
        or any(i not in range(6) for i in available)
    ):
        raise ValueError(
            "Fixed budget0..3 and unique declared channel indices required"
        )
    available = tuple(sorted(available))
    if method == "exact_coverage":
        candidates = [
            subset
            for count in range(min(budget, len(available)) + 1)
            for subset in combinations(available, count)
        ]
        return min(candidates, key=lambda j: (-ceiling_mass(rows, j), len(j), j))
    if method in ("canonical", "random"):
        order = (
            list(available)
            if method == "canonical"
            else random.Random(seed).sample(list(available), len(available))
        )
        return tuple(sorted(order[:budget]))
    if method not in ("greedy_coverage", "greedy_entropy"):
        raise ValueError("Unregistered channel selector")
    chosen = ()
    score = (
        (lambda j: ceiling_mass(rows, j))
        if method == "greedy_coverage"
        else (lambda j: -conditional_entropy(rows, j))
    )
    for _ in range(min(budget, len(available))):
        candidates = [tuple(sorted((*chosen, i))) for i in available if i not in chosen]
        maximum = max(score(j) for j in candidates)
        tolerance = 1e-12 if method == "greedy_entropy" else 0
        best = min(j for j in candidates if score(j) >= maximum - tolerance)
        if score(best) <= score(chosen) + tolerance:
            break
        chosen = best
    return chosen


def profile(rows, selected, privileged=False):
    details = []
    for signature, group in sorted(
        partition(rows, selected, privileged).items(), key=lambda p: str(p[0])
    ):
        sets = [good(row) for row in group]
        common = set.intersection(*sets) if sets else set()
        inadequate = [
            r
            for r in group
            if r["outcomes"] == {"continue_value": False, "recover_value": False}
        ]
        left = next((r for r in group if good(r) == {"continue"}), None)
        right = next((r for r in group if good(r) == {"recover"}), None)
        details.append(
            {
                "signature": signature,
                "mass": len(group),
                "parents": len({r["group"] for r in group}),
                "ids": [r["id"] for r in group],
                "good": sorted(common),
                "inadequate": bool(inadequate),
                "ambiguity": left is not None and right is not None,
                "inadequate_witness": [inadequate[0]["id"]] if inadequate else [],
                "ambiguity_witness": [left["id"], right["id"]]
                if left and right
                else [],
            }
        )
    return {
        "channels": selected,
        "privileged": privileged,
        "groups": len(details),
        "rows": len(rows),
        "actionable_mass": sum(g["mass"] for g in details if g["good"]),
        "inadequate_mass": sum(g["mass"] for g in details if g["inadequate"]),
        "ambiguous_mass": sum(g["mass"] for g in details if g["ambiguity"]),
        "overlap_mass": sum(
            g["mass"] for g in details if g["inadequate"] and g["ambiguity"]
        ),
        "absolute_actionable_upper_mass": sum(bool(good(r)) for r in rows),
        "signatures": details,
    }
