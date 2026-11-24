"""Finite, same-input controls; not executions of published robotics software."""

import copy
import math
from fractions import Fraction

from rpd_independent_oracle import exhaustive, index, rollout


def greedy_tree(raw, mode, support=None, h=None, budget="ROOT"):
    states, g, probes = index(raw)
    support = tuple(sorted(raw["initial_support"])) if support is None else support
    h = raw["horizon"] if h is None else h
    if budget == "ROOT":
        budget = (
            None if raw["max_probe_cost"] is None else Fraction(raw["max_probe_cost"])
        )
    safe = raw["require_physical_safety"]
    stop = ("STOP", None, ())
    if safe and any(not states[s]["physically_allowed"] for s in support):
        return stop
    for a in sorted(raw["recovery_actions"]):
        if all(
            g[s][a]["task_success"] and (not safe or g[s][a]["path_safe"])
            for s in support
        ):
            return "RECOVER", a, ()
    if not h or mode == "no_probe":
        return stop
    candidates = []
    for name, p in sorted(probes.items()):
        cost = Fraction(p["cost"])
        if budget is not None and cost > budget:
            continue
        rows = [p["table"][s] for s in support]
        if not all(row["enabled"] for row in rows):
            continue
        if safe and any(
            not row["path_safe"] or not states[row["successor"]]["physically_allowed"]
            for row in rows
        ):
            continue
        groups = {}
        for row in rows:
            groups.setdefault(row["observation"], set()).add(row["successor"])
        weights = {
            o: sum(row["observation"] == o for row in rows) / len(rows) for o in groups
        }
        entropy = -sum(w * math.log2(w) for w in weights.values())
        if mode == "physical_entropy":
            score = entropy
        elif mode == "one_step_consensus":
            score = min(
                max(
                    sum(
                        g[s][a]["task_success"] and (not safe or g[s][a]["path_safe"])
                        for s in members
                    )
                    / len(members)
                    for a in raw["recovery_actions"]
                )
                for members in groups.values()
            )
        else:
            raise ValueError(mode)
        candidates.append((-score, cost, name, groups))
    if not candidates:
        return stop
    _, cost, name, groups = min(candidates, key=lambda row: row[:3])
    return (
        "PROBE",
        name,
        tuple(
            (
                o,
                greedy_tree(
                    raw,
                    mode,
                    tuple(sorted(members)),
                    h - 1,
                    None if budget is None else budget - cost,
                ),
            )
            for o, members in sorted(groups.items())
        ),
    )


def static_transition_ablation(raw):
    wrong = copy.deepcopy(raw)
    for p in wrong["probes"]:
        for row in p["transitions"]:
            if row["enabled"]:
                row["successor"] = row["state_id"]
    result, _ = exhaustive(wrong)
    return ("STOP", None, ()) if result is None else result[1]


def metrics(raw, tree):
    episodes = [rollout(raw, tree, s) for s in raw["initial_support"]]
    n = len(episodes)
    return {
        "all_worlds_success": all(r[0] for r in episodes),
        "uniform_initial_completion": str(Fraction(sum(r[0] for r in episodes), n)),
        "worst_probe_cost": str(max(r[1] for r in episodes)),
        "mean_probe_cost": str(sum((r[1] for r in episodes), Fraction(0)) / n),
        "per_initial_world": [
            {"initial": s, "success": r[0], "probe_cost": str(r[1]), "trace": r[2]}
            for s, r in zip(raw["initial_support"], episodes, strict=True)
        ],
        "scope": "ANALYTICAL_ONLY_NOT_ROBOT_OUTCOMES",
    }


def named_comparison(raw, exact_tree):
    controls = {
        "exact_strong_policy_oracle": exact_tree,
        **{
            mode: greedy_tree(raw, mode)
            for mode in ("no_probe", "physical_entropy", "one_step_consensus")
        },
        "static_ERR_transition_ignored_ABLATION": static_transition_ablation(raw),
    }
    result = {
        name: {"tree": tree, "metrics": metrics(raw, tree)}
        for name, tree in controls.items()
    }
    result["static_ERR_transition_ignored_ABLATION"]["valid_model_based_competitor"] = (
        False
    )
    result["static_ERR_transition_ignored_ABLATION"]["limitation"] = (
        "Deliberately violates the physical transition model; no robust model-based guarantee. Independent empirical terminal calibration would be a separate, source-scoped claim."
    )
    return result
