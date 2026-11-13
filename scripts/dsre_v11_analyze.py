"""Checkpoint-level metrics and paired seed-group uncertainty for frozen v1.1."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

FIELDS = (
    "episodes",
    "recommended",
    "abstained",
    "other_action",
    "adequate",
    "unacceptable",
    "regret",
    "literals",
    "support",
    "strict",
    "provisional",
    "status_errors",
)
RATIOS = {
    "coverage": ("recommended", "episodes"),
    "unacceptable_rate": ("unacceptable", "recommended"),
    "absolute_success_given_recommendation": ("adequate", "recommended"),
    "successful_recommendations_per_checkpoint": ("adequate", "episodes"),
    "mean_literals": ("literals", "recommended"),
    "mean_support": ("support", "recommended"),
    "mean_regret": ("regret", "recommended"),
    "strict_fraction_recommended": ("strict", "recommended"),
    "provisional_fraction_recommended": ("provisional", "recommended"),
}


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def key(method, beta):
    return method + "/" + (f"{beta:g}" if beta is not None else "boundary")


def record(result, row, action="all"):
    chosen = result["action"]
    emitted = chosen is not None and (action == "all" or chosen == action)
    success = int(row["outcomes"][chosen + "_value"]) if emitted else 0
    strict = result.get("tier") == "STRICT_FINITE_REFERENCE"
    provisional = result.get("tier") == "PROVISIONAL_RISK_RULE"
    bad_status = provisional and result["status"] != "PROVISIONAL_UNCALIBRATED"
    return [
        1,
        int(emitted),
        int(chosen is None),
        int(chosen is not None and not emitted),
        success,
        int(emitted) - success,
        int(max(row["outcomes"].values())) - success if emitted else 0,
        len(result["evidence"]) if emitted else 0,
        result["support"] if emitted else 0,
        int(emitted and strict),
        int(emitted and provisional),
        int(bad_status),
    ]


def summarize(array, weights):
    counts, samples = array.sum(axis=0), weights @ array
    n_groups = int((array[:, 1] > 0).sum())
    rates = {}
    for name, (num, den) in RATIOS.items():
        a, b = FIELDS.index(num), FIELDS.index(den)
        valid = samples[:, b] > 0
        sparse = den == "recommended" and n_groups < 10
        interval = (
            np.quantile(samples[valid, a] / samples[valid, b], [0.025, 0.975]).tolist()
            if valid.any() and not sparse
            else None
        )
        rates[name] = {
            "value": float(counts[a] / counts[b]) if counts[b] else None,
            "parent_percentile95": interval,
            "sparse_stratum": sparse,
            "constant_interval_not_population_equivalence": interval is not None
            and interval[0] == interval[1],
        }
    return {
        "counts": dict(zip(FIELDS, map(int, counts), strict=True)),
        "rates": rates,
        "recommending_seed_groups": n_groups,
        "seed_groups": int((array[:, 0] > 0).sum()),
    }


def flatten_outputs(root):
    outputs, cold = [], []
    for path in sorted((root / "crossfit").glob("*.json")):
        checkpoint = load(path)
        cold.extend(
            {"task": checkpoint["task"], **d} for d in checkpoint["decisions"].values()
        )
        for p in checkpoint["predictions"]:
            decision = checkpoint["decisions"][p["decision_id"]]
            outputs.append(p | {"result": decision["result"]})
    return outputs, cold


def analyze(root):
    config = load(Path("config/dsre_v11.json"))
    old = Path(config["input_root"])
    source = [
        json.loads(s) for s in (old / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    pairs = {r["id"]: r for r in source}
    tasks = ["PickCube-v1", "PushCube-v1"]
    groups = [
        g
        for task in tasks
        for g in sorted({r["group"] for r in source if r["task"] == task})
    ]
    group_index = {g: i for i, g in enumerate(groups)}
    weights = []
    bootstrap_indices = {}
    for index, task in enumerate(tasks):
        task_groups = [g for g in groups if g.startswith(task + "/")]
        draws = np.random.default_rng(config["bootstrap_seed"] + index).integers(
            0, len(task_groups), (config["bootstrap_draws"], len(task_groups))
        )
        weights.append(
            np.stack([np.bincount(draw, minlength=len(task_groups)) for draw in draws])
        )
        bootstrap_indices[task] = {
            "seed": config["bootstrap_seed"] + index,
            "groups": task_groups,
            "draws_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
        }
    weight_matrix = np.hstack(weights)
    save(
        root / "uncertainty_plan.json",
        {
            "draws": config["bootstrap_draws"],
            "task_stratified": True,
            "unit": "task/seed with both conditions together",
            "indices": bootstrap_indices,
        },
    )
    outputs, cold = flatten_outputs(root)
    arrays = defaultdict(lambda: np.zeros((len(groups), len(FIELDS)), dtype=np.int64))
    per_input = defaultdict(dict)
    for p in outputs:
        row = pairs[p["id"]]
        name = key(p["method"], p["beta"])
        per_input[row["id"]][name] = p["result"]
        for task in (row["task"], "combined"):
            for action in ("all", "continue", "recover"):
                for population in ("all_starts", "failed_starts"):
                    if population == "failed_starts" and row["initial_success"]:
                        continue
                    arrays[(task, name, action, population)][
                        group_index[row["group"]]
                    ] += record(p["result"], row, action)
    metrics = {
        "|".join(k): summarize(a, weight_matrix) for k, a in sorted(arrays.items())
    }
    save(root / "metrics.json", metrics)
    frontier = []
    for (task, name, action, population), array in sorted(arrays.items()):
        if action != "all" or population != "all_starts" or task == "combined":
            continue
        m = metrics[f"{task}|{name}|{action}|{population}"]
        frontier.append(
            {
                "task": task,
                "method_point": name,
                "recommended": m["counts"]["recommended"],
                "unacceptable": m["counts"]["unacceptable"],
                "coverage": m["rates"]["coverage"]["value"],
                "unacceptable_rate": m["rates"]["unacceptable_rate"]["value"],
                "mean_literals": m["rates"]["mean_literals"]["value"],
            }
        )
    for point in frontier:
        point["pareto"] = point["unacceptable_rate"] is not None and not any(
            q["task"] == point["task"]
            and q["unacceptable_rate"] is not None
            and q["coverage"] >= point["coverage"]
            and q["unacceptable_rate"] <= point["unacceptable_rate"]
            and q["mean_literals"] <= point["mean_literals"]
            and (
                q["coverage"] > point["coverage"]
                or q["unacceptable_rate"] < point["unacceptable_rate"]
                or q["mean_literals"] < point["mean_literals"]
            )
            for q in frontier
        )
    with (root / "frontier.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(frontier[0]))
        writer.writeheader()
        writer.writerows(frontier)
    matched, paired = {}, {}
    for task in (*tasks, "combined"):
        for beta in (0.1, 0.05):
            target = key("DSRE_v11", beta)
            a = arrays[(task, target, "all", "all_starts")]
            ca, sa = a.sum(axis=0), weight_matrix @ a
            competitors = [
                key("S_strict", 0),
                key("B7_exact", 0),
                key("B5_v11", beta),
                key("B1_two_v11", beta),
                *[key("CART_depth" + str(d), beta) for d in (1, 2, 3)],
                key("full_signature", beta),
                key("always_recover", None),
            ]
            for other in competitors:
                b = arrays[(task, other, "all", "all_starts")]
                cb, sb = b.sum(axis=0), weight_matrix @ b
                differences = {}
                for metric in (
                    "coverage",
                    "unacceptable_rate",
                    "successful_recommendations_per_checkpoint",
                    "mean_literals",
                ):
                    num, den = RATIOS[metric]
                    i, j = FIELDS.index(num), FIELDS.index(den)
                    valid = (sa[:, j] > 0) & (sb[:, j] > 0)
                    sparse = (
                        den == "recommended"
                        and min(int((a[:, 1] > 0).sum()), int((b[:, 1] > 0).sum())) < 10
                    )
                    dif = sa[valid, i] / sa[valid, j] - sb[valid, i] / sb[valid, j]
                    differences[metric] = {
                        "value": float(ca[i] / ca[j] - cb[i] / cb[j])
                        if ca[j] and cb[j]
                        else None,
                        "parent_percentile95": np.quantile(dif, [0.025, 0.975]).tolist()
                        if len(dif) and not sparse
                        else None,
                    }
                common = np.zeros((len(groups), 3), dtype=np.int64)
                equal = 0
                provisional = 0
                provisional_equal = 0
                for row in source:
                    if task != "combined" and row["task"] != task:
                        continue
                    r, s = per_input[row["id"]][target], per_input[row["id"]][other]
                    equal += all(
                        r[f] == s[f] for f in ("action", "evidence", "support")
                    )
                    if r.get("tier") == "PROVISIONAL_RISK_RULE":
                        provisional += 1
                        provisional_equal += all(
                            r[f] == s[f] for f in ("action", "evidence", "support")
                        )
                    if r["action"] and s["action"]:
                        common[group_index[row["group"]]] += [
                            1,
                            len(r["evidence"]) - len(s["evidence"]),
                            int(r["action"] == s["action"]),
                        ]
                cs = weight_matrix @ common
                valid = cs[:, 0] > 0
                common_n = int(common[:, 0].sum())
                common_groups = int((common[:, 0] > 0).sum())
                paired[task + "|" + target + " minus " + other] = {
                    "differences": differences,
                    "equal_action_evidence_support": int(equal),
                    "provisional_cases": provisional,
                    "provisional_equal": provisional_equal,
                    "common_recommendations": common_n,
                    "common_action_agreement": int(common[:, 2].sum()),
                    "common_mean_literal_difference": float(
                        common[:, 1].sum() / common_n
                    )
                    if common_n
                    else None,
                    "common_literal_parent95": np.quantile(
                        cs[valid, 1] / cs[valid, 0], [0.025, 0.975]
                    ).tolist()
                    if valid.any() and common_groups >= 10
                    else None,
                }
            if task != "combined":
                n, k = int(ca[1]), int(ca[5])
                points = [
                    p
                    for p in frontier
                    if p["task"] == task and p["method_point"] != target
                ]
                matched[task + "|" + target] = {
                    "target_recommended": n,
                    "target_unacceptable": k,
                    "criterion": "equal achieved conditional unacceptable rate; diagnostic comparison only, no threshold selection",
                    "exact_risk_matches": [
                        p
                        for p in points
                        if n
                        and p["recommended"]
                        and k * p["recommended"] == p["unacceptable"] * n
                    ],
                }
    save(root / "paired_comparisons.json", paired)
    save(root / "matched_risk_frontier.json", matched)
    times = defaultdict(list)
    for d in cold:
        times[d["task"] + "|" + key(d["method"], d["beta"])].append(
            d["cold_latency_ms"]
        )
    save(
        root / "runtime.json",
        {
            k: {
                "cold_queries": len(v),
                "mean_ms": float(np.mean(v)),
                "median_ms": float(np.median(v)),
                "max_ms": max(v),
            }
            for k, v in sorted(times.items())
        },
    )
    feasibility = {}
    for task in tasks:
        for method in (
            "DSRE_v11/0.1",
            "B5_v11/0.1",
            "B1_two_v11/0.1",
            "CART_depth1/0.1",
            "CART_depth2/0.1",
            "CART_depth3/0.1",
            "full_signature/0.1",
        ):
            for action in ("continue", "recover"):
                m = metrics[f"{task}|{method}|{action}|all_starts"]
                n, mass = m["counts"]["episodes"], m["counts"]["recommended"]
                rate = mass / n
                feasibility[task + "|" + method + "|" + action] = {
                    "assigned_checkpoints": mass,
                    "development_checkpoints": n,
                    "assignment_frequency": rate,
                    "assigned_seed_groups": m["recommending_seed_groups"],
                    "expected_from_200": 200 * rate,
                    "required_zero_error_independent_assigned": 42,
                    "expected_parents_for_42": math.ceil(42 / rate) if rate else None,
                    "expected_200_can_reach_42": 200 * rate >= 42,
                    "deployment_enabled": False,
                    "calibration": "NO_INDEPENDENT_COHORT",
                }
    save(
        root / "calibration_feasibility.json",
        {
            "alpha": 0.1,
            "total_delta": 0.05,
            "delta_per_stratum": 0.0125,
            "strata": 4,
            "method_comparisons_require_further_multiplicity_if_selected_together": True,
            "assignment_source": "out-of-fold checkpoint marginal; two conditions/seed are dependent, future one assignment/independent parent assumed",
            "planning_not_guarantee": True,
            "strata_by_method": feasibility,
        },
    )
    save(
        root / "analysis_completed.json",
        {
            "status": "COMPLETE",
            "prediction_rows": len(outputs),
            "metric_cells": len(metrics),
            "paired_cells": len(paired),
            "false_status_count": sum(
                int(
                    p["result"].get("tier") == "PROVISIONAL_RISK_RULE"
                    and p["result"]["status"] != "PROVISIONAL_UNCALIBRATED"
                )
                for p in outputs
            ),
            "calibration": "NOT_RUN",
        },
    )
    print(json.dumps(load(root / "analysis_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    analyze(args.root)
