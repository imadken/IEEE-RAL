"""Compact-record-only statistics for restoration validity; no development fitter."""

from __future__ import annotations

import numpy as np

from dual_rec.passive import mean_interval, wilson


def descriptive(values):
    if not values:
        return None
    return {
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "p95": float(np.quantile(values, 0.95)),
        "max": float(np.max(values)),
    }


def summarize_replay(rows: list[dict], repetitions=2000, seed=11817) -> dict:
    expected = [r for r in rows if r["stage_reached"]]
    if any(
        r.get("integrity_failure")
        or not r["gold_prefix"]["passed"]
        or not r["gold_continuation"]["passed"]
        for r in expected
    ):
        raise ValueError("Invalid GOLD reference cannot become a physics result")
    groups = {}
    for task, condition, stage in sorted(
        {(r["task"], r["condition"], r["stage"]) for r in rows}
    ):
        cell = [
            r
            for r in expected
            if (r["task"], r["condition"], r["stage"]) == (task, condition, stage)
        ]
        policies = {}
        for policy in ["nominal", "alternative"]:
            trials = [r for r in cell if r["policy"] == policy]
            complete = [r for r in trials if r.get("test") is not None]
            policies[policy] = {
                "attempted_states": len(trials),
                "test_failures": len(trials) - len(complete),
                "complete_pairs": len(complete),
                "gold_successes": sum(r["gold"]["success"] for r in trials),
                "gold_success_wilson_95": wilson(
                    sum(r["gold"]["success"] for r in trials), len(trials)
                ),
                "test_successes_complete": sum(r["test"]["success"] for r in complete),
                "test_success_wilson_95_complete": wilson(
                    sum(r["test"]["success"] for r in complete), len(complete)
                ),
                "success_difference": mean_interval(
                    [
                        int(r["test"]["success"]) - int(r["gold"]["success"])
                        for r in complete
                    ],
                    repetitions,
                    seed,
                ),
                "utility_difference": mean_interval(
                    [r["test"]["utility"] - r["gold"]["utility"] for r in complete],
                    repetitions,
                    seed,
                ),
                "immediate_invalid_count": sum(
                    not r.get("test_immediate_error", {}).get("contacts", False)
                    or not r.get("test_immediate_error", {}).get("success", False)
                    or any(
                        r.get("test_immediate_error", {}).get(k, float("inf")) > limit
                        for k, limit in [
                            ("position", 1e-5),
                            ("angle", 1e-4),
                            ("velocity", 1e-4),
                            ("qpos", 1e-4),
                            ("observation", 1e-4),
                            ("time", 1e-9),
                        ]
                    )
                    for r in trials
                ),
                "continuation_invalid_count": sum(
                    not r.get("test_continuation", {}).get("passed", False)
                    for r in trials
                ),
                "success_disagreement_count": sum(
                    r["gold"]["success"] != r["test"]["success"] for r in complete
                ),
                "contact_changed_pair_count": sum(
                    r["test_continuation"]["contact_agreement"] < 1 for r in complete
                ),
                "max_continuation_errors": {
                    key: max(
                        (r["test_continuation"]["maxima"][key] for r in complete),
                        default=None,
                    )
                    for key in [
                        "position",
                        "angle",
                        "velocity",
                        "qpos",
                        "observation",
                        "time",
                    ]
                },
                "error_distributions": {
                    phase: {
                        key: descriptive(
                            [
                                r["test_immediate_error"][key]
                                if phase == "immediate"
                                else r["test_continuation"]["maxima"][key]
                                for r in complete
                            ]
                        )
                        for key in [
                            "position",
                            "angle",
                            "velocity",
                            "qpos",
                            "observation",
                            "time",
                        ]
                    }
                    for phase in ["immediate", "continuation_max"]
                },
                "contact_disagreement_fraction": descriptive(
                    [1 - r["test_continuation"]["contact_agreement"] for r in complete]
                ),
                "exposed_field_errors": {
                    key: descriptive(
                        [
                            r["omitted_or_integration_fields_error"][key]
                            for r in complete
                        ]
                    )
                    for key in sorted(
                        {
                            key
                            for r in complete
                            for key in r.get("omitted_or_integration_fields_error", {})
                        }
                    )
                },
            }
        lookup = {(r["seed"], r["policy"]): r for r in cell}
        rank = []
        for base_seed in sorted({r["seed"] for r in cell}):
            if not all(
                (base_seed, p) in lookup
                and lookup[base_seed, p].get("test") is not None
                for p in ["nominal", "alternative"]
            ):
                continue
            a, b = lookup[base_seed, "nominal"], lookup[base_seed, "alternative"]
            delta_gold = a["gold"]["utility"] - b["gold"]["utility"]
            delta_test = a["test"]["utility"] - b["test"]["utility"]
            opposite = delta_gold * delta_test < 0
            rank.append(
                {
                    "seed": base_seed,
                    "gold_contrast": delta_gold,
                    "test_contrast": delta_test,
                    "contrast_error": delta_test - delta_gold,
                    "raw_sign_reversal": opposite,
                    "reversal_001": opposite
                    and min(abs(delta_gold), abs(delta_test)) >= 0.01,
                    "reversal_010": opposite
                    and min(abs(delta_gold), abs(delta_test)) >= 0.10,
                }
            )
        groups[f"{task}/{condition}/{stage}"] = {
            "task": task,
            "condition": condition,
            "stage": stage,
            "policies": policies,
            "independent_seed_count": len({r["seed"] for r in cell}),
            "ranking_pairs": rank,
            "contrast_error": mean_interval(
                [r["contrast_error"] for r in rank], repetitions, seed
            ),
            "gold_contrast": mean_interval(
                [r["gold_contrast"] for r in rank], repetitions, seed
            ),
            "test_contrast": mean_interval(
                [r["test_contrast"] for r in rank], repetitions, seed
            ),
            "ranking_reversal_001_wilson_95": wilson(
                sum(r["reversal_001"] for r in rank), len(rank)
            ),
            "ranking_reversal_010_wilson_95": wilson(
                sum(r["reversal_010"] for r in rank), len(rank)
            ),
            "ranking_reversal_001": mean_interval(
                [r["reversal_001"] for r in rank], repetitions, seed
            ),
            "ranking_reversal_010": mean_interval(
                [r["reversal_010"] for r in rank], repetitions, seed
            ),
        }
    complete = [r for r in expected if r.get("test") is not None]
    return {
        "planned_trial_rows": len(rows),
        "stage_reached_rows": len(expected),
        "stage_unreached_rows": len(rows) - len(expected),
        "test_restore_failures": len(expected) - len(complete),
        "all_gold_passed": True,
        "complete_pairs": len(complete),
        "snapshot_continuation_parity_passes": sum(
            r["test_continuation"]["passed"] for r in complete
        ),
        "success_disagreements": sum(
            r["gold"]["success"] != r["test"]["success"] for r in complete
        ),
        "independent_seeds_by_task": {
            task: sorted({r["seed"] for r in rows if r["task"] == task})
            for task in sorted({r["task"] for r in rows})
        },
        "groups": groups,
    }
