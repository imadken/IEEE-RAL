"""Independent stored-trial audit. Does not load or call a development fitter."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np


def close(a, b):
    if a is None or b is None:
        assert a is b
    else:
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)


def interval(values, repetitions, seed):
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return None
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(repetitions):
        samples.append(float(values[rng.integers(0, len(values), len(values))].mean()))
    return {
        "mean": float(values.mean()),
        "ci": np.quantile(samples, [0.025, 0.975]).tolist(),
    }


def compare_interval(values, reported, repetitions, seed):
    actual = interval(values, repetitions, seed)
    if actual is None:
        assert reported is None
    else:
        close(actual["mean"], reported["mean"])
        close(actual["ci"], reported["ci"])
        assert reported["independent_seeds"] == len(values)


def metric_values(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    pos = p[y == 1]
    neg = p[y == 0]
    auc = float(
        ((pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])).mean()
    )
    balanced = 0.5 * (np.mean(pos >= 0.5) + np.mean(neg < 0.5))
    clipped = np.clip(p, 1e-12, 1 - 1e-12)
    ece = 0.0
    for k in range(5):
        mask = np.minimum((p * 5).astype(int), 4) == k
        if mask.any():
            ece += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return {
        "auroc": auc,
        "balanced_accuracy": float(balanced),
        "brier": float(np.mean((y - p) ** 2)),
        "log_loss": float(
            -np.mean(y * np.log(clipped) + (1 - y) * np.log(1 - clipped))
        ),
        "ece_5_bins": float(ece),
    }


def binomial_interval(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    scale = 1 + z**2 / total
    mid = (p + z**2 / (2 * total)) / scale
    half = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / scale
    return [max(0.0, mid - half), min(1.0, mid + half)]


def check_distribution(values, reported):
    if not values:
        assert reported is None
    else:
        for name, q in [("min", 0), ("median", 0.5), ("p95", 0.95), ("max", 1)]:
            close(np.quantile(values, q), reported[name])


def valid_error(error):
    return bool(
        error.get("contacts", False)
        and error.get("success", False)
        and all(
            error.get(k, float("inf")) <= limit
            for k, limit in [
                ("position", 1e-5),
                ("angle", 1e-4),
                ("velocity", 1e-4),
                ("qpos", 1e-4),
                ("observation", 1e-4),
                ("time", 1e-9),
            ]
        )
    )


def recorded_effort(actions, task):
    # JSON numbers lose ndarray dtype. Restore the acquisition action tape dtype
    # before independently recomputing its recorded floating-point cost.
    dtype = np.float64 if task == "Lift" else np.float32
    bound = 0.6 if task == "Lift" else 0.25
    tape = np.asarray(actions, dtype=dtype)
    return float(
        np.clip(np.linalg.norm(tape[:, :3], axis=1) / (np.sqrt(3) * bound), 0, 1).mean()
    )


def audit_physics(task, condition, edit):
    scale = 8 if condition == "mass8" else 1
    if task == "Lift":
        close(edit["mass_after"], edit["mass_before"] * scale)
        close(edit["inertia_after"], np.asarray(edit["inertia_before"]) * scale)
        close(edit["com_before"], edit["com_after"])
        close(edit["axes_before"], edit["axes_after"])
        return
    before, after = (
        (edit["before"], edit["after"])
        if task == "PushCube-v1"
        else (edit["cube_before"], edit["cube_after"])
    )
    np.testing.assert_allclose(after["mass_kg"], before["mass_kg"] * scale, rtol=1e-6)
    np.testing.assert_allclose(
        after["inertia_kg_m2"], np.asarray(before["inertia_kg_m2"]) * scale, rtol=1e-6
    )
    close(before["center_of_mass_pose"], after["center_of_mass_pose"])
    if condition in ("low_friction_001", "friction"):
        for shape in after["shape_materials"]:
            np.testing.assert_allclose(
                [shape["static_friction"], shape["dynamic_friction"]], 0.01, rtol=1e-6
            )
        for shape in edit["finger_after"]:
            np.testing.assert_allclose(
                [shape["static"], shape["dynamic"]], 0.01, rtol=1e-6
            )


def audit_pick(root, cfg):
    report = json.loads((root / "d7b/evaluation/report.json").read_text())
    rows = [
        json.loads(line)
        for path in sorted((root / "d7b").glob("qualification-*/outcomes.jsonl"))
        for line in path.read_text().splitlines()
    ]
    seeds = cfg["d7b"]["qualification_seeds"]
    seal = json.loads((root / "d7b/fitted/seal.json").read_text())
    assert seal["training_seeds"] == cfg["d7b"]["development_seeds"]
    assert not set(seal["training_seeds"]) & set(seeds)
    model = root / "d7b/fitted/models.json.gz"
    if model.exists():
        assert hashlib.sha256(model.read_bytes()).hexdigest() == seal["model_sha256"]
    calibration = json.loads((root / "d7b/calibration/initials.json").read_text())
    selection = json.loads((root / "d7b/selection.json").read_text())
    assert len(calibration) == 28
    assert (
        sum(
            r["initial_success"]
            for r in calibration
            if r["evaluation_only_fault"]["name"] == "nominal"
        )
        >= 3
    )
    for mechanism, grid, selected in [
        ("friction", cfg["d7b"]["friction_grid"], selection["friction"]),
        ("offset", cfg["d7b"]["offset_grid_m"], selection["offset_x"]),
    ]:
        eligible = [
            v
            for v in grid
            if sum(
                r["failed"]
                for r in calibration
                if r["evaluation_only_fault"]["name"] == f"{mechanism}-{v}"
            )
            >= 2
        ]
        assert eligible[0] == selected
    keys = [(r["seed"], r["condition"], r["recovery"]) for r in rows]
    assert len(keys) == len(set(keys)) == 72
    assert set(keys) == {
        (s, c, p)
        for s in seeds
        for c in ["nominal", "friction", "offset"]
        for p in ["nominal", "regrasp", "conservative"]
    }
    all_cases = []
    for line in (root / "audit/scenario_registry.jsonl").read_text().splitlines():
        case = json.loads(line)
        if case["split"] == "calibration":
            continue
        assert case["history_steps"] == list(range(len(case["prefix_actions"]) + 1))
        assert case["decision_step"] <= 90
        assert not case["failed"] or not case["initial_success"]
        audit_physics(
            "PickCube-v1", case["evaluation_only_fault"]["name"], case["edit"]
        )
        all_cases.append(case)
    all_outcomes = {
        (r["seed"], r["condition"], r["recovery"]): r
        for path in (root / "d7b").glob("*/outcomes.jsonl")
        for r in map(json.loads, path.read_text().splitlines())
    }
    action_rows = list(
        map(
            json.loads, (root / "audit/recovery_actions.jsonl").read_text().splitlines()
        )
    )
    assert len(action_rows) == len(all_outcomes) == 180
    for trial in action_rows:
        out = all_outcomes[trial["seed"], trial["condition"], trial["recovery"]]
        actions = np.asarray(trial["actions"])
        assert actions.shape == (70, 4)
        effort = np.clip(
            np.linalg.norm(actions[:, :3], axis=1) / (np.sqrt(3) * 0.25), 0, 1
        ).mean()
        close(out["utility"], (int(out["success"]) - 0.05 * effort - 0.05 + 0.10) / 1.1)
        assert out["parity"]["passed"] and out["parity"]["contact_agreement"]
    cases = {(r["seed"], r["evaluation_only_fault"]["name"]): r for r in all_cases}
    assert len(cases) == 60
    counts = {
        c: sum(cases[s, c]["failed"] for s in seeds)
        for c in ["nominal", "friction", "offset"]
    }
    assert counts == report["failure_counts"]
    paired = [
        s
        for s in seeds
        if cases[s, "friction"]["failed"] and cases[s, "offset"]["failed"]
    ]
    assert paired == report["matched_failed_seeds"]
    for row in rows:
        assert (
            row["parity"]["passed"]
            and row["parity"]["contact_agreement"]
            and row["parity"]["sensor_max"] <= 1e-4
        )
    for condition, policies in report["matrix"].items():
        for policy, cohorts in policies.items():
            cell = [
                r
                for r in rows
                if r["condition"] == condition and r["recovery"] == policy
            ]
            for cohort, reported in cohorts.items():
                selected = (
                    cell
                    if cohort == "all_setups"
                    else [r for r in cell if r["initial_failed"]]
                )
                assert len(selected) == reported["independent_seeds"]
                assert sum(r["success"] for r in selected) == reported["successes"]
                close(
                    binomial_interval(reported["successes"], len(selected)),
                    reported["wilson_95"],
                )
                compare_interval(
                    [r["utility"] for r in selected],
                    reported["utility"],
                    cfg["bootstrap_repetitions"],
                    cfg["analysis_seed"],
                )
    lookup = {(r["seed"], r["condition"], r["recovery"]): r for r in rows}
    for c in ["friction", "offset"]:
        compare_interval(
            [
                lookup[s, c, "nominal"]["utility"] - lookup[s, c, "regrasp"]["utility"]
                for s in paired
            ],
            report["contrasts"][c],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
    predictions = [
        json.loads(line)
        for line in (root / "d7b/evaluation/predictions.jsonl").read_text().splitlines()
    ]
    assert len(predictions) == 64
    for regime in ["full", "realistic"]:
        for model in ["logistic", "rbf_kernel_logistic"]:
            selected = [
                r for r in predictions if r["regime"] == regime and r["model"] == model
            ]
            values = metric_values(
                [r["target"] for r in selected],
                [r["probability_offset"] for r in selected],
            )
            for name, value in values.items():
                close(value, report["diagnostics"][regime][model]["all_setups"][name])
            matched = [r for r in selected if r["matched_failed"]]
            matched_values = metric_values(
                [r["target"] for r in matched],
                [r["probability_offset"] for r in matched],
            )
            for name, value in matched_values.items():
                close(
                    value,
                    report["diagnostics"][regime][model]["matched_failures"][name],
                )
            rng = np.random.default_rng(cfg["analysis_seed"])
            samples = {name: [] for name in values}
            for _ in range(cfg["bootstrap_repetitions"]):
                sampled = [
                    r
                    for s in rng.choice(seeds, len(seeds), replace=True)
                    for r in selected
                    if r["seed"] == s
                ]
                metrics = metric_values(
                    [r["target"] for r in sampled],
                    [r["probability_offset"] for r in sampled],
                )
                for name, value in metrics.items():
                    samples[name].append(value)
            for name, values in samples.items():
                close(
                    np.quantile(values, [0.025, 0.975]),
                    report["diagnostics"][regime][model]["all_setups_clustered_95"][
                        name
                    ],
                )
    uncertain = [
        s
        for s in paired
        if all(
            0.25 <= r["probability_offset"] <= 0.75
            for r in predictions
            if r["seed"] == s and r["regime"] == "realistic"
        )
    ]
    assert uncertain == report["uncertain_realistic_seeds"]
    a, b = report["contrasts"].values()
    meaningful = (
        a["mean"] * b["mean"] < 0 and min(abs(a["mean"]), abs(b["mean"])) >= 0.10
    )
    assert not meaningful and report["status"] == "NO-GO"
    return {
        "status": report["status"],
        "reason": report["reason"],
        "failure_counts": counts,
        "paired_failed_seeds": paired,
        "primary_contrasts": {
            c: interval(
                [
                    lookup[s, c, "nominal"]["utility"]
                    - lookup[s, c, "regrasp"]["utility"]
                    for s in paired
                ],
                cfg["bootstrap_repetitions"],
                cfg["analysis_seed"],
            )
            for c in ["friction", "offset"]
        },
        "realistic_uncertain_seeds": uncertain,
        "qualification_recovery_pairs": len(rows),
        "all_selected_scenarios": len(all_cases),
        "fitter_consulted": False,
        "all_means_and_intervals_recomputed": True,
        "all_passive_point_metrics_recomputed": True,
    }


def audit_b(root, cfg):
    report = json.loads((root / "b/analysis/report.json").read_text())
    rows = [
        json.loads(line)
        for path in sorted((root / "b").glob("*/trials.jsonl"))
        for line in path.read_text().splitlines()
    ]
    expected = {
        (task, s, c, stage, policy)
        for task, seeds in cfg["b"]["seed_ranges"].items()
        for s in seeds
        for c in cfg["b"]["conditions"][task]
        for stage in cfg["b"]["stages"]
        for policy in cfg["b"]["continuations"]
    }
    keys = [
        (r["task"], r["seed"], r["condition"], r["stage"], r["policy"]) for r in rows
    ]
    assert len(keys) == len(set(keys)) == len(expected) and set(keys) == expected
    reached = [r for r in rows if r["stage_reached"]]
    complete = [r for r in reached if r.get("test") is not None]
    assert report["planned_trial_rows"] == len(rows)
    assert report["stage_reached_rows"] == len(reached)
    assert report["complete_pairs"] == len(complete)
    assert report["test_restore_failures"] == len(reached) - len(complete)
    assert report["success_disagreements"] == sum(
        r["gold"]["success"] != r["test"]["success"] for r in complete
    )
    for row in reached:
        audit_physics(row["task"], row["condition"], row["physical_edit"])
        assert row["gold_prefix"]["passed"] and row["gold_continuation"]["passed"]
        assert row["gold_prefix"]["steps"] == len(row["prefix_actions"]) + 1
        assert row["gold_continuation"]["steps"] == 40
        effort = recorded_effort(row["continuation_actions"], row["task"])
        for method in ["native", "gold", "test"]:
            if row.get(method) is None:
                continue
            close(row[method]["effort"], effort)
            close(
                row[method]["utility"],
                (int(row[method]["success"]) - 0.05 * effort - 0.05 + 0.10) / 1.1,
            )
        if row.get("test") is not None:
            assert len(row["test_errors"]) == 40
            assert (
                all(valid_error(e) for e in row["test_errors"])
                == row["test_continuation"]["passed"]
            )
            for key in ["position", "angle", "velocity", "qpos", "observation", "time"]:
                close(
                    max(e[key] for e in row["test_errors"]),
                    row["test_continuation"]["maxima"][key],
                )
            close(
                np.mean([e["contacts"] for e in row["test_errors"]]),
                row["test_continuation"]["contact_agreement"],
            )
    rank_flip_total = 0
    for group in report["groups"].values():
        cell = [
            r
            for r in reached
            if (r["task"], r["condition"], r["stage"])
            == (group["task"], group["condition"], group["stage"])
        ]
        for policy, stats in group["policies"].items():
            attempted = [r for r in cell if r["policy"] == policy]
            pairs = [r for r in attempted if r.get("test") is not None]
            assert len(attempted) == stats["attempted_states"]
            assert len(attempted) - len(pairs) == stats["test_failures"]
            assert (
                sum(r["gold"]["success"] for r in attempted) == stats["gold_successes"]
            )
            assert (
                sum(r["test"]["success"] for r in pairs)
                == stats["test_successes_complete"]
            )
            close(
                binomial_interval(stats["gold_successes"], len(attempted)),
                stats["gold_success_wilson_95"],
            )
            close(
                binomial_interval(stats["test_successes_complete"], len(pairs)),
                stats["test_success_wilson_95_complete"],
            )
            assert stats["continuation_invalid_count"] == sum(
                not r.get("test_continuation", {}).get("passed", False)
                for r in attempted
            )
            assert stats["immediate_invalid_count"] == sum(
                not valid_error(r.get("test_immediate_error", {})) for r in attempted
            )
            assert stats["contact_changed_pair_count"] == sum(
                r["test_continuation"]["contact_agreement"] < 1 for r in pairs
            )
            assert stats["success_disagreement_count"] == sum(
                r["gold"]["success"] != r["test"]["success"] for r in pairs
            )
            check_distribution(
                [1 - r["test_continuation"]["contact_agreement"] for r in pairs],
                stats["contact_disagreement_fraction"],
            )
            for key in ["position", "angle", "velocity", "qpos", "observation", "time"]:
                for phase in ["immediate", "continuation_max"]:
                    values = [
                        r["test_immediate_error"][key]
                        if phase == "immediate"
                        else r["test_continuation"]["maxima"][key]
                        for r in pairs
                    ]
                    check_distribution(values, stats["error_distributions"][phase][key])
                close(
                    max(
                        (r["test_continuation"]["maxima"][key] for r in pairs),
                        default=None,
                    ),
                    stats["max_continuation_errors"][key],
                )
            for key, distribution in stats["exposed_field_errors"].items():
                check_distribution(
                    [r["omitted_or_integration_fields_error"][key] for r in pairs],
                    distribution,
                )
            compare_interval(
                [r["test"]["utility"] - r["gold"]["utility"] for r in pairs],
                stats["utility_difference"],
                cfg["bootstrap_repetitions"],
                cfg["analysis_seed"],
            )
            compare_interval(
                [int(r["test"]["success"]) - int(r["gold"]["success"]) for r in pairs],
                stats["success_difference"],
                cfg["bootstrap_repetitions"],
                cfg["analysis_seed"],
            )
        by_key = {
            (r["seed"], r["policy"]): r for r in cell if r.get("test") is not None
        }
        ranks = []
        gold_values, test_values = [], []
        for s in sorted({r["seed"] for r in cell}):
            if not all((s, p) in by_key for p in ["nominal", "alternative"]):
                continue
            a, b = by_key[s, "nominal"], by_key[s, "alternative"]
            assert a["prefix_actions"] == b["prefix_actions"]
            assert a["branch_record"] == b["branch_record"]
            gold = a["gold"]["utility"] - b["gold"]["utility"]
            test = a["test"]["utility"] - b["test"]["utility"]
            gold_values.append(gold)
            test_values.append(test)
            stored = next(r for r in group["ranking_pairs"] if r["seed"] == s)
            close(gold, stored["gold_contrast"])
            close(test, stored["test_contrast"])
            assert stored["raw_sign_reversal"] == (gold * test < 0)
            for margin, key in [(0.01, "reversal_001"), (0.10, "reversal_010")]:
                assert stored[key] == (
                    gold * test < 0 and min(abs(gold), abs(test)) >= margin
                )
            ranks.append(
                (
                    test - gold,
                    gold * test < 0 and min(abs(gold), abs(test)) >= 0.01,
                    gold * test < 0 and min(abs(gold), abs(test)) >= 0.10,
                )
            )
        rank_flip_total += sum(r[1] for r in ranks)
        compare_interval(
            gold_values,
            group["gold_contrast"],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
        compare_interval(
            test_values,
            group["test_contrast"],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
        close(
            binomial_interval(sum(r[1] for r in ranks), len(ranks)),
            group["ranking_reversal_001_wilson_95"],
        )
        close(
            binomial_interval(sum(r[2] for r in ranks), len(ranks)),
            group["ranking_reversal_010_wilson_95"],
        )
        compare_interval(
            [r[0] for r in ranks],
            group["contrast_error"],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
        compare_interval(
            [r[1] for r in ranks],
            group["ranking_reversal_001"],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
        compare_interval(
            [r[2] for r in ranks],
            group["ranking_reversal_010"],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
    statuses = [
        json.loads(path.read_text()) for path in (root / "b").glob("*/status.json")
    ]
    attempted = sum(s["attempted_continuations"] for s in statuses)
    assert attempted <= 1000
    tasks = {}
    for task in cfg["b"]["seed_ranges"]:
        cell = [r for r in complete if r["task"] == task]
        groups = [g for g in report["groups"].values() if g["task"] == task]
        rank_pairs = [r for g in groups for r in g["ranking_pairs"]]
        tasks[task] = {
            "independent_base_seeds": len({r["seed"] for r in cell}),
            "complete_pairs": len(cell),
            "snapshot_continuation_passes": sum(
                r["test_continuation"]["passed"] for r in cell
            ),
            "contact_changed_pairs": sum(
                r["test_continuation"]["contact_agreement"] < 1 for r in cell
            ),
            "success_disagreements": sum(
                r["gold"]["success"] != r["test"]["success"] for r in cell
            ),
            "action_ranking_pairs": len(rank_pairs),
            "raw_sign_reversals": sum(r["raw_sign_reversal"] for r in rank_pairs),
            "ranking_reversals_001": sum(r["reversal_001"] for r in rank_pairs),
            "ranking_reversals_010": sum(r["reversal_010"] for r in rank_pairs),
        }
    return {
        "planned_rows": len(rows),
        "stage_reached": len(reached),
        "complete_native_gold_test_pairs": len(complete),
        "restore_exceptions": len(reached) - len(complete),
        "success_disagreements": report["success_disagreements"],
        "ranking_reversals_001": int(rank_flip_total),
        "attempted_continuations": attempted,
        "by_task": tasks,
        "all_gold_passed": True,
        "all_outcomes_costs_contrasts_and_intervals_recomputed": True,
        "fitter_consulted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-report", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(Path("config/overnight_20261111.json").read_text())
    previous = json.loads((args.root / "prior_local_sha256.json").read_text())
    for path, sha in previous.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, path
    initial = json.loads((args.root / "initial.json").read_text())
    for path, sha in initial["preserved_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, path
    base = initial["base_sha"]
    assert Path(
        "config/overnight_20261111.json"
    ).read_bytes() == subprocess.check_output(
        ["git", "show", "68798cd:config/overnight_20261111.json"]
    )
    for path in [
        "src/dual_rec/replay.py",
        "scripts/mani_runner.py",
        "scripts/qualify.py",
        "src/dual_rec/physical_faults.py",
    ]:
        assert Path(path).read_bytes() == subprocess.check_output(
            ["git", "show", base + ":" + path]
        ), path
    result = {
        "prior_local_artifacts_preserved": len(previous),
        "original_adapters_unchanged": True,
        "locked_dependencies_and_guidance_preserved": True,
        "D7B": audit_pick(args.root, cfg),
        "B": audit_b(args.root, cfg),
        "STOPPED_WITHIN_AUTHORIZED_BOUNDARY": True,
        "NO_PAPER_CLAIM": True,
    }
    if args.verify_report:
        match = re.search(
            r"<!-- OVERNIGHT_VERIFIED_STATISTICS_START -->\s*```json\s*(.*?)\s*```\s*<!-- OVERNIGHT_VERIFIED_STATISTICS_END -->",
            Path("GATE_REPORTS.md").read_text(),
            re.DOTALL,
        )
        assert match, "Missing independently checkable report statistics"
        saved = json.loads(match[1])
        assert saved == {"D7B": result["D7B"], "B": result["B"]}
        result["human_report_statistics_verified"] = True
    args.output.open("x").write(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
