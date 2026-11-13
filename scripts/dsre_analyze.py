"""Measured joint frontiers and paired parent uncertainty, independent of routing."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


FIELDS = [
    "episodes",
    "emitted",
    "acceptable",
    "success",
    "unacceptable",
    "regret",
    "literal_sum",
    "inadequacy",
    "neither_recommended",
]
RATIOS = {
    "coverage": ("emitted", "episodes"),
    "acceptable_accuracy": ("acceptable", "emitted"),
    "absolute_success_given_recommendation": ("success", "emitted"),
    "unacceptable_frequency": ("unacceptable", "emitted"),
    "mean_regret_given_recommendation": ("regret", "emitted"),
    "mean_literals_given_recommendation": ("literal_sum", "emitted"),
    "successful_recommendations_per_episode": ("success", "episodes"),
}


def evaluate(recommendation, pair):
    action = recommendation["action"]
    outcomes = pair["outcomes"]
    selected = int(outcomes[action + "_value"]) if action else 0
    best = max(int(v) for v in outcomes.values())
    emitted = int(action is not None)
    return [
        1,
        emitted,
        selected,
        selected,
        emitted - selected,
        best - selected if emitted else 0,
        len(recommendation["evidence"]) if emitted else 0,
        emitted - selected,
        int(emitted and best == 0),
    ]


def summarize(counts, samples, recommending_groups):
    total = dict(zip(FIELDS, map(int, counts), strict=True))
    result = {
        "counts": total,
        "recommending_seed_groups": recommending_groups,
        "rates": {},
    }
    for name, (n, d) in RATIOS.items():
        ni, di = FIELDS.index(n), FIELDS.index(d)
        point = float(counts[ni] / counts[di]) if counts[di] else None
        valid = samples[:, di] > 0
        interval = None
        sparse = d == "emitted" and recommending_groups < 10
        if valid.any() and not sparse:
            distribution = samples[valid, ni] / samples[valid, di]
            interval = np.quantile(distribution, [0.025, 0.975]).tolist()
        result["rates"][name] = {
            "value": point,
            "parent_percentile95": interval,
            "sparse_stratum": sparse,
            "constant_interval_not_population_equivalence": interval is not None
            and interval[0] == interval[1],
        }
    return result


def raw_category(pair):
    c, r = pair["outcomes"]["continue_value"], pair["outcomes"]["recover_value"]
    return (
        "both"
        if c and r
        else "continue_only"
        if c
        else "recover_only"
        if r
        else "neither"
    )


def analyze(root):
    config = load(Path("config/dsre_stage1.json"))
    source = list(rows(root / "qualified_pairs.jsonl"))
    by_id = {r["id"]: r for r in source}
    all_metrics, paired, frontier, details, timings, failed_start = (
        {},
        {},
        [],
        [],
        defaultdict(list),
        {},
    )
    numerical = (root / "scored_primary.jsonl").open("w")
    for variant in config["feature_variants"]:
        for task in config["tasks"]:
            population = [r for r in source if r["task"] == task]
            group_names = sorted({r["group"] for r in population})
            gindex = {name: i for i, name in enumerate(group_names)}
            group_count = len(group_names)
            primary, per_method = (
                defaultdict(dict),
                defaultdict(
                    lambda group_count=group_count: np.zeros((group_count, len(FIELDS)))
                ),
            )
            length_counts, reasons, assigned = (
                defaultdict(Counter),
                defaultdict(Counter),
                defaultdict(Counter),
            )
            failed = defaultdict(lambda: np.zeros(len(FIELDS)))
            for path in sorted(
                (root / "crossfit").glob(f"{variant}__{task}__fold*.jsonl")
            ):
                for prediction in rows(path):
                    pair = by_id[prediction["id"]]
                    rec = prediction["recommendation"]
                    method = prediction["method"] + "/" + prediction["point"]
                    scored = evaluate(rec, pair)
                    per_method[method][gindex[pair["group"]]] += scored
                    if rec["action"]:
                        length_counts[method][len(rec["evidence"])] += 1
                        assigned[method][rec["action"]] += 1
                    else:
                        reasons[method].update(rec["reason"].split("+"))
                    if prediction["point"] == "primary":
                        primary[pair["id"]][prediction["method"]] = prediction
                        numerical.write(
                            json.dumps(
                                {
                                    "id": pair["id"],
                                    "group": pair["group"],
                                    "task": task,
                                    "variant": variant,
                                    "method": prediction["method"],
                                    "metrics": dict(zip(FIELDS, scored, strict=True)),
                                }
                            )
                            + "\n"
                        )
                        if not pair["initial_success"]:
                            failed[prediction["method"]] += scored
            names = sorted(per_method)
            array = np.stack([per_method[name] for name in names], axis=1)
            rng = np.random.default_rng(config["bootstrap_seed"])
            indices = rng.integers(
                0, len(group_names), (config["bootstrap_draws"], len(group_names))
            )
            weights = np.stack(
                [np.bincount(i, minlength=len(group_names)) for i in indices]
            )
            samples = (weights @ array.reshape(len(group_names), -1)).reshape(
                config["bootstrap_draws"], len(names), len(FIELDS)
            )
            for i, name in enumerate(names):
                total = array[:, i].sum(axis=0)
                info = summarize(total, samples[:, i], int((array[:, i, 1] > 0).sum()))
                info.update(
                    length_histogram={
                        str(k): v for k, v in sorted(length_counts[name].items())
                    },
                    insufficiency_or_abstention_reasons=dict(reasons[name]),
                    assigned_actions=dict(assigned[name]),
                    seed_groups=len(group_names),
                )
                all_metrics[variant + "/" + task + "/" + name] = info
                frontier.append(
                    {
                        "variant": variant,
                        "task": task,
                        "method_point": name,
                        "episodes": int(total[0]),
                        "recommendations": int(total[1]),
                        "unacceptable": int(total[4]),
                        "coverage": info["rates"]["coverage"]["value"],
                        "unacceptable_frequency": info["rates"][
                            "unacceptable_frequency"
                        ]["value"],
                        "mean_literals": info["rates"][
                            "mean_literals_given_recommendation"
                        ]["value"],
                    }
                )
            failed_start[variant + "/" + task] = {
                m: dict(zip(FIELDS, map(int, counts), strict=True))
                for m, counts in failed.items()
            }
            for method in config["methods"]:
                if method == "DSRE":
                    continue
                a, b = names.index("DSRE/primary"), names.index(method + "/primary")
                comparisons = {}
                for metric in [
                    "coverage",
                    "unacceptable_frequency",
                    "mean_literals_given_recommendation",
                    "successful_recommendations_per_episode",
                ]:
                    n, d = RATIOS[metric]
                    ni, di = FIELDS.index(n), FIELDS.index(d)
                    left, right = array[:, a].sum(axis=0), array[:, b].sum(axis=0)
                    valid = (samples[:, a, di] > 0) & (samples[:, b, di] > 0)
                    delta = (
                        float(left[ni] / left[di] - right[ni] / right[di])
                        if left[di] and right[di]
                        else None
                    )
                    enough = (
                        d == "episodes"
                        or min(
                            int((array[:, a, 1] > 0).sum()),
                            int((array[:, b, 1] > 0).sum()),
                        )
                        >= 10
                    )
                    dist = (
                        samples[valid, a, ni] / samples[valid, a, di]
                        - samples[valid, b, ni] / samples[valid, b, di]
                    )
                    comparisons[metric] = {
                        "DSRE_minus_comparator": delta,
                        "paired_parent_percentile95": np.quantile(
                            dist, [0.025, 0.975]
                        ).tolist()
                        if valid.any() and enough
                        else None,
                        "conditional_populations_may_differ": d == "emitted",
                    }
                common, agreements = [], Counter()
                common_groups = np.zeros((len(group_names), 2))
                for identifier, predictions in primary.items():
                    left, right = (
                        predictions["DSRE"]["recommendation"],
                        predictions[method]["recommendation"],
                    )
                    if left["action"] and right["action"]:
                        difference = len(left["evidence"]) - len(right["evidence"])
                        common.append(difference)
                        common_groups[gindex[by_id[identifier]["group"]]] += [
                            difference,
                            1,
                        ]
                    agreements.update(
                        same_action=int(left["action"] == right["action"]),
                        same_evidence=int(left["evidence"] == right["evidence"]),
                        cases=1,
                    )
                common_draws = weights @ common_groups
                common_valid = common_draws[:, 1] > 0
                common_interval = (
                    np.quantile(
                        common_draws[common_valid, 0] / common_draws[common_valid, 1],
                        [0.025, 0.975],
                    ).tolist()
                    if common_valid.any() and (common_groups[:, 1] > 0).sum() >= 10
                    else None
                )
                paired[variant + "/" + task + "/DSRE-minus-" + method] = {
                    "comparisons": comparisons,
                    "common_recommendation_episodes": len(common),
                    "mean_literal_difference_common_episodes": sum(common) / len(common)
                    if common
                    else None,
                    "paired_parent_percentile95_common_length": common_interval,
                    "agreement": dict(agreements),
                }
            for identifier, predictions in primary.items():
                dsre = predictions["DSRE"]["recommendation"]
                policy = predictions["B4_policy"]["recommendation"]
                pair = by_id[identifier]
                if (
                    dsre["action"]
                    and policy["action"]
                    and dsre["action"] != policy["action"]
                ):
                    details.append(
                        {
                            "id": identifier,
                            "variant": variant,
                            "task": task,
                            "measured_outcomes": pair["outcomes"],
                            "dsre": dsre,
                            "policy_faithful": policy,
                            "interpretation": "Distinct justified decision target, not automatically an improvement",
                        }
                    )
            print(
                json.dumps(
                    {
                        "analyzed": variant + "/" + task,
                        "operating_points": len(names),
                        "parents": len(population),
                    }
                ),
                flush=True,
            )
    numerical.close()
    for path in sorted((root / "crossfit").glob("*.model.json")):
        metadata = load(path)
        for record in metadata["uncached_prediction_latencies"]:
            timings[record["method"]].append(record["latency_ms"])
    save(root / "metrics.json", all_metrics)
    save(root / "paired_comparisons.json", paired)
    save(root / "failed_start_metrics.json", failed_start)
    save(root / "policy_outcome_disagreements.json", details)
    save(
        root / "method_runtime.json",
        {
            name: {
                "uncached_queries": len(v),
                "total_ms": sum(v),
                "mean_ms": float(np.mean(v)),
                "median_ms": float(np.median(v)),
                "p95_ms": float(np.quantile(v, 0.95)),
                "max_ms": max(v),
                "scope": "Unique queries/operating points; cached repeated signatures excluded and reported separately in predictions",
            }
            for name, v in timings.items()
        },
    )
    for row in frontier:
        possible = [
            p
            for p in frontier
            if p["variant"] == row["variant"]
            and p["task"] == row["task"]
            and p["recommendations"]
        ]
        row["pareto_nondominated"] = bool(row["recommendations"]) and not any(
            p["coverage"] >= row["coverage"]
            and p["unacceptable_frequency"] <= row["unacceptable_frequency"]
            and p["mean_literals"] <= row["mean_literals"]
            and (
                p["coverage"] > row["coverage"]
                or p["unacceptable_frequency"] < row["unacceptable_frequency"]
                or p["mean_literals"] < row["mean_literals"]
            )
            for p in possible
        )
    with (root / "frontier.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(frontier[0]))
        writer.writeheader()
        writer.writerows(frontier)
    matches = {}
    for variant in config["feature_variants"]:
        for task in config["tasks"]:
            current = [
                r for r in frontier if r["variant"] == variant and r["task"] == task
            ]
            dsre = next(r for r in current if r["method_point"] == "DSRE/primary")
            for method in config["methods"]:
                if method == "DSRE":
                    continue
                choices = [
                    r
                    for r in current
                    if r["method_point"].split("/")[0] == method
                    and r["recommendations"] == dsre["recommendations"]
                    and r["unacceptable"] == dsre["unacceptable"]
                ]
                if not dsre["recommendations"]:
                    choices = []
                matches[variant + "/" + task + "/" + method] = {
                    "status": "EXACT_COVERAGE_AND_ERROR_MATCH"
                    if choices
                    else "INFEASIBLE_NO_DSRE_RECOMMENDATIONS"
                    if not dsre["recommendations"]
                    else "INFEASIBLE_ON_REGISTERED_OPERATING_POINTS",
                    "DSRE": dsre,
                    "comparator_points": choices,
                    "note": "Zero-width coverage/error bands, descriptive frontier only; not outcome-selected deployment thresholds",
                }
    save(root / "matched_frontier.json", matches)
    collisions, examples, prevalence = {}, [], defaultdict(Counter)
    for pair in source:
        prevalence[pair["task"]].update(
            pairs=1,
            **{raw_category(pair): 1},
            initially_successful=int(pair["initial_success"]),
        )
        if not pair["initial_success"]:
            prevalence[pair["task"]].update(
                failed_start=1, **{"failed_start_" + raw_category(pair): 1}
            )
            for action in ("continue", "recover"):
                prevalence[pair["task"]]["new_first_hit_" + action] += int(
                    pair["new_first_hits"][action]
                )
    for task in config["tasks"]:
        population = [r for r in source if r["task"] == task]
        for field in ("features", "privileged_features", "coarse_features"):
            groups = defaultdict(list)
            for pair in population:
                groups[tuple(pair[field])].append(pair)
            records = []
            for pattern, members in sorted(groups.items(), key=lambda v: str(v[0])):
                categories = Counter(raw_category(r) for r in members)
                incompatible = bool(
                    categories["continue_only"] and categories["recover_only"]
                )
                inadequate = bool(categories["neither"])
                compatible_members = [
                    r
                    for r in population
                    if all(
                        value is None or r[field][i] is None or value == r[field][i]
                        for i, value in enumerate(pattern)
                    )
                ]
                compatible_categories = Counter(
                    raw_category(r) for r in compatible_members
                )
                records.append(
                    {
                        "pattern": pattern,
                        "rows": len(members),
                        "seed_groups": len({r["group"] for r in members}),
                        "categories": dict(categories),
                        "incompatible_nonempty_actions": incompatible,
                        "contains_inadequate_row": inadequate,
                        "conservative_compatible_rows": len(compatible_members),
                        "conservative_categories": dict(compatible_categories),
                        "conservative_incompatible_actions": bool(
                            compatible_categories["continue_only"]
                            and compatible_categories["recover_only"]
                        ),
                        "ids": [r["id"] for r in members],
                    }
                )
            collisions[task + "/" + field] = {
                "distinct_patterns": len(groups),
                "incompatible_patterns": sum(
                    r["incompatible_nonempty_actions"] for r in records
                ),
                "inadequacy_contaminated_patterns": sum(
                    r["contains_inadequate_row"] for r in records
                ),
                "records": records,
            }
    full = load(root / "full_table_certificates.json")
    for category in (
        "short_sound_certificate",
        "ambiguity",
        "inadequacy",
        "missing_support",
    ):
        for record in full:
            c = record["certificate"]
            if (
                record["minimum_support"] != config["minimum_support"]
                or record["variant"] != "pose_proprioception"
            ):
                continue
            qualifies = (
                bool(c["action"]) and len(c["evidence"]) <= 2
                if category == "short_sound_certificate"
                else (
                    "OBSERVATION_AMBIGUITY"
                    if category == "ambiguity"
                    else "INADEQUATE_REPERTOIRE"
                    if category == "inadequacy"
                    else "INSUFFICIENT_REFERENCE_SUPPORT"
                )
                in c["reasons"]
            )
            if qualifies:
                examples.append(
                    {
                        "category": category,
                        "selection": "first deterministic full-table pattern satisfying the predeclared example category; illustrative, not a separate trial",
                        **record,
                    }
                )
                break
    save(root / "witness_examples.json", examples)
    save(root / "feature_collisions.json", collisions)
    save(
        root / "paired_outcome_prevalence.json",
        {t: dict(v) for t, v in prevalence.items()},
    )
    print(
        json.dumps(
            {
                "completed_metric_cells": len(all_metrics),
                "paired_comparisons": len(paired),
                "disagreements": len(details),
                "witness_example_categories": [e["category"] for e in examples],
            }
        ),
        flush=True,
    )


def planning(root):
    config = load(Path("config/dsre_stage1.json"))
    source = list(rows(root / "qualified_pairs.jsonl"))
    full = load(root / "full_table_certificates.json")
    needed = math.ceil(math.log(0.0125) / math.log1p(-0.1))
    need05 = math.ceil(math.log(0.0125) / math.log1p(-0.05))
    feasibility, plans = [], []
    router = {
        "table_sha256": hashlib.sha256(
            (root / "qualified_pairs.jsonl").read_bytes()
        ).hexdigest(),
        "solver_sha256": hashlib.sha256(
            Path("src/dual_rec/dsre/solver.py").read_bytes()
        ).hexdigest(),
        "scope": config,
        "training_parent_ids": sorted({r["group"] for r in source}),
        "status": "FROZEN_UNCALIBRATED_NO_DEPLOYMENT_PERMISSION",
    }
    router_sha = hashlib.sha256(json.dumps(router, sort_keys=True).encode()).hexdigest()
    save(root / "frozen_router.json", router | {"sha256": router_sha})
    for task_index, task in enumerate(config["tasks"]):
        population = [r for r in source if r["task"] == task]
        routing = Counter()
        for record in full:
            if (
                record["task"] == task
                and record["variant"] == "pose_proprioception"
                and record["minimum_support"] == config["minimum_support"]
            ):
                routing[record["certificate"]["action"] or "abstain"] += len(
                    record["matching_input_ids"]
                )
        costs = [sum(r["route_wall_seconds"].values()) for r in population]
        for action in ("continue", "recover"):
            frequency = routing[action] / len(population)
            feasibility.append(
                {
                    "task": task,
                    "action": action,
                    "development_routed": routing[action],
                    "development_parent_checkpoints": len(population),
                    "routing_frequency_planning_only": frequency,
                    "required_assigned_zero_error_alpha10": needed,
                    "required_assigned_zero_error_alpha05": need05,
                    "expected_assigned_from200": 200 * frequency,
                    "expected_new_parents_for_required_count": math.ceil(
                        needed / frequency
                    )
                    if frequency
                    else None,
                    "minimum_expected_count_feasible_at200": 200 * frequency >= needed,
                    "warning": "Expected counts under unchanged routing, not guaranteed accrual or an error bound; no independent cohort evaluated",
                }
            )
        candidates = sorted(
            range(2000000 + task_index * 1000000, 2010000 + task_index * 1000000),
            key=lambda seed, task=task: hashlib.sha256(
                f"dsre-fresh-v1/{task}/{seed}".encode()
            ).hexdigest(),
        )[:400]
        conditions = ["nominal", "offset002" if task == "PickCube-v1" else "misaligned"]
        old_seeds = {r["seed"] for r in population}
        assert not old_seeds & set(candidates)
        for i, seed in enumerate(candidates):
            plans.append(
                {
                    "task": task,
                    "seed": seed,
                    "parent_id": f"{task}/{seed}",
                    "split": "calibration" if i < 200 else "confirmation",
                    "condition_audit_only": conditions[i % 2],
                    "status": "PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED",
                }
            )
        save(
            root / (task + "_prospective_cost.json"),
            {
                "paired_parent_count": 400,
                "condition_assignment": "one existing registered condition per new seed, balanced deterministically before outcomes",
                "measured_median_two_fresh_route_wall_seconds": float(np.median(costs)),
                "estimate_reference_plus_fresh_qualified_branch_seconds": float(
                    np.median(costs)
                )
                * 2
                * 400,
                "conservative_1_5x_estimate_seconds": float(np.median(costs)) * 3 * 400,
                "continuations_reference_plus_fresh": 1600,
                "continuation_control_steps": 1600 * 70,
                "complete_prefix_controls_estimate": 1600
                * float(np.median([r["prefix_controls"] for r in population])),
                "assumptions": "Same host/controllers; two references plus two fresh replay branches per parent; actual orchestration, I/O and load may change cost",
            },
        )
    save(
        root / "calibration_feasibility.json",
        {
            "status": "INTERFACE_IMPLEMENTED_INDEPENDENT_CALIBRATION_NOT_RUN",
            "router_sha256": router_sha,
            "alpha": 0.1,
            "total_delta": 0.05,
            "delta_per_four_strata": 0.0125,
            "zero_error_assigned_n": needed,
            "all_deployment_actions_disabled": True,
            "strata": feasibility,
        },
    )
    save(
        root / "prospective_fresh_seed_plan.json",
        {
            "status": "NO_PHYSICS_AUTHORIZED",
            "router_sha256": router_sha,
            "parents": plans,
            "cohorts": "200 independent calibration and 200 separate confirmation parents per task; no hidden outcome-conditioned balancing",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    analyze(args.root)
    planning(args.root)
