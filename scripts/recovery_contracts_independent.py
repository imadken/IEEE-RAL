"""Independent pooled arithmetic and original standalone fold verification.

No imports from the contract package or compared prediction/scoring code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path

import numpy as np


def read(root, name):
    return json.loads((root / name).read_text())


def audit_derived(root):
    role = read(root, "source_role_oof.json")
    assert (
        len(role["predictions"])
        == len({r["sample"] for r in role["predictions"]})
        == 100
    )
    for row in role["predictions"]:
        child = root / "failtime" / f"fold{row['fold']}"
        original = next(
            r
            for r in read(child, "source_role_predictions.json")
            if r["sample"] == row["sample"]
        )
        assert {k: v for k, v in row.items() if k != "fold"} == original
    eligible = [r for r in role["predictions"] if r["eligible"]]
    positives = [r["score"] for r in eligible if r["label"]]
    negatives = [r["score"] for r in eligible if not r["label"]]
    auc = sum(
        1 if a > b else 0.5 if a == b else 0 for a in positives for b in negatives
    ) / (len(positives) * len(negatives))
    accuracy = (
        sum(p >= 0.5 for p in positives) / len(positives)
        + sum(p < 0.5 for p in negatives) / len(negatives)
    ) / 2
    np.testing.assert_allclose(
        [role["summary"]["auroc"], role["summary"]["balanced_accuracy"]],
        [auc, accuracy],
        rtol=0,
        atol=1e-14,
    )
    peaks = read(root, "retrospective_peaks.json")
    for row in read(root, "retrospective_summary.json"):
        chosen = [r for r in peaks if r["method"] == row["method"]]
        assert row["failures"] == len(chosen) == 57
        assert row["within_one_second"] == sum(r["within_one_second"] for r in chosen)
        errors = [
            r["absolute_error"] for r in chosen if r["absolute_error"] is not None
        ]
        assert row["finite_estimates"] == len(errors)
        np.testing.assert_allclose(
            row["mean_absolute_error"], sum(errors) / len(errors), rtol=0, atol=1e-12
        )
        observable = [r for r in chosen if r["full_window_observable"]]
        assert row["observable_window_counterpart"]["failures"] == len(observable) == 56
        assert row["observable_window_counterpart"]["within_one_second"] == sum(
            r["within_one_second"] for r in observable
        )
        errors = [
            r["absolute_error"] for r in observable if r["absolute_error"] is not None
        ]
        np.testing.assert_allclose(
            row["observable_window_counterpart"]["mean_absolute_error"],
            sum(errors) / len(errors),
            rtol=0,
            atol=1e-12,
        )
    applications = {
        r["name"]: {c["check"]: c["status"] for c in r["checks"]}
        for r in read(root, "contract_applications.json")
    }
    assert len(applications) == 136
    for k in range(5):
        assert all(
            applications[f"failtime_fold{k}_design"][check] == "PASS"
            for check in (
                "numeric_duplicates",
                "group_separation",
                "independent_calibration",
                "runtime_information",
            )
        )
    expected = [
        ("failtime_event_labels", "event_bounds", "PASS"),
        ("failtime_event_labels", "event_semantics", "PASS"),
        ("failtime_unjustified_label_reinterpretation", "event_semantics", "FAIL"),
        ("reboot_uncollapsed_aliases", "numeric_duplicates", "FAIL"),
        ("reboot_missing_temporal_target", "event_bounds", "UNKNOWN"),
        ("recoverbench_identity_stack", "simulator_identity", "UNKNOWN"),
        ("recoverbench_identity_pick_place", "simulator_identity", "FAIL"),
        ("recoverbench_forwarding_only", "physical_execution", "FAIL"),
    ]
    for name, check, status in expected:
        assert applications[name][check] == status, (name, check)
    assert all(
        checks["intervention_effect"] == "UNKNOWN" for checks in applications.values()
    )
    assert all(
        applications[f"recoverbench_executed_{i:02d}"]["physical_execution"] == "PASS"
        for i in range(24)
    )
    assert all(
        checks["continuous_alarm"] == "PASS" and checks["causal_time"] == "PASS"
        for name, checks in applications.items()
        if name.startswith("failtime_stream_")
    )
    return {
        "status": "PASS",
        "scope": "Independent aggregation of audited OOF role predictions, all offline peak summaries and expected case-specific obligation verdicts; no claim that declarations prove universal absence of hidden leakage",
        "oof_role_eligible": len(eligible),
        "role_auroc": auc,
        "role_balanced_accuracy": accuracy,
        "peak_summary_cells": 9,
        "claim_contexts": len(applications),
        "unidentified_intervention_effect": "All contexts UNKNOWN as required",
    }


def audit(root):
    independent = runpy.run_path("scripts/failtime_numerical_audit.py")["audit"]
    fold_reports = []
    for k in range(5):
        child = root / "failtime" / f"fold{k}"
        result = independent(child)
        (child / "independent_numerical_audit.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        fold_reports.append(
            {
                "fold": k,
                "status": result["status"],
                "outcomes": result["outcome_rows"],
                "risks": result["risk_files_checked"],
                "thresholds": result["threshold_cells"],
            }
        )
    raw = [
        r
        for k in range(5)
        for r in read(root / "failtime" / f"fold{k}", "outcomes.json")
    ]
    pooled = read(root, "failtime_outcomes.json")
    assert len(raw) == len(pooled) == 40500

    def key(r):
        return (r["sample"], r["method"], r["stress"], r["alpha"], r["persistence"])

    assert len({key(r) for r in pooled}) == len(pooled)
    assert {key(r): r for r in raw} == {
        key(r): {k: v for k, v in r.items() if k != "fold"} for r in pooled
    }
    registry = {
        r["sample"]: r
        for r in read(root / "failtime/fold0", "cohort_qualification.json")
    }
    group_folds = {}
    for robot in sorted({r["robot"] for r in registry.values()}):
        groups = {
            robot + "/" + r["task_id"] for r in registry.values() if r["robot"] == robot
        }
        ordered = sorted(
            groups,
            key=lambda g: hashlib.sha256(
                ("recovery-contracts-v1|" + g).encode()
            ).digest(),
        )
        group_folds.update({g: i % 5 for i, g in enumerate(ordered)})
    assert group_folds == read(root, "registration.json")["failtime"]["group_folds"]
    signatures = []
    for s, row in registry.items():
        with np.load(root / "failtime/fold0" / row["arrays"]) as d:
            signature = hashlib.sha256(
                np.ascontiguousarray(d["time"]).tobytes()
                + np.ascontiguousarray(d["eef"]).tobytes()
            ).hexdigest()
            assert signature == row["signal_sha256"], s
            assert row["duration"] == float(d["time"][-1]), s
        signatures.append(signature)
    assert len(set(signatures)) == 100
    seen = Counter(
        s
        for k in range(5)
        for s in read(root / "failtime" / f"fold{k}", "registration.json")["splits"][
            "evaluation"
        ]
    )
    assert set(seen) == set(registry) and set(seen.values()) == {1}
    for cell in read(root, "failtime_summary.json"):
        rows = [
            r
            for r in raw
            if all(
                r[f] == cell[f] for f in ("method", "stress", "alpha", "persistence")
            )
        ]
        counts = Counter(r["status"] for r in rows)
        for field in ("timely", "premature", "late", "missed"):
            assert cell[field] == counts[field]
        assert cell["failures"] == 57 and cell["successes"] == 43
        assert cell["clean_alarms"] == counts["clean_alarm"]
        assert cell["timely"] + cell["premature"] + cell["late"] + cell["missed"] == 57
        observed = [r for r in rows if r["is_failure"] and r["observable_window"]]
        assert cell["observable_window_counterpart"]["failures"] == len(observed)
        # Independent score-test interval arithmetic.
        for metric, successes, n in (
            ("timely", counts["timely"], 57),
            ("premature", counts["premature"], 57),
            ("clean_alarm", counts["clean_alarm"], 43),
        ):
            z = 1.959963984540054
            den = n + z**2
            center = (successes + z**2 / 2) / den
            radius = z * np.sqrt(successes * (n - successes) / n + z**2 / 4) / den
            np.testing.assert_allclose(
                cell["wilson95"][metric],
                [center - radius, center + radius],
                rtol=0,
                atol=1e-14,
            )
    main = {
        (r["sample"], r["method"]): r
        for r in raw
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["persistence"] == 0.1
    }
    for cell in read(root, "failtime_stratified.json"):
        subset = [
            r
            for r in pooled
            if r["alpha"] == 0.1
            and r["persistence"] == 0.1
            and r["stress"] == "clean"
            and r["method"] == cell["method"]
            and r[cell["dimension"]] == cell["stratum"]
        ]
        assert cell["failures"] == sum(r["is_failure"] for r in subset)
        assert cell["successes"] == sum(not r["is_failure"] for r in subset)
        for metric in ("timely", "premature", "late", "missed"):
            assert cell[metric] == sum(r[metric] for r in subset)
        assert cell["clean_alarms"] == sum(r["clean_alarm"] for r in subset)
    ids = sorted(registry)
    tasks = sorted({r["task_id"] for r in registry.values()})
    task_robot = {r["task_id"]: r["robot"] for r in registry.values()}
    checked = []
    for filename, stratified in (
        ("paired_effects.json", False),
        ("paired_effects_robot_stratified.json", True),
    ):
        artifact = read(root, filename)
        for contrast in artifact["contrasts"]:
            rng = np.random.default_rng(20261112)
            for metric in ("timely", "premature", "clean_alarm", "burden"):
                selection = (
                    ids
                    if metric == "burden"
                    else [
                        s
                        for s in ids
                        if registry[s]["verdict"]
                        == ("success" if metric == "clean_alarm" else "fail")
                    ]
                )
                differences = []
                for s in selection:
                    a, b = main[(s, "MCSFA")], main[(s, contrast["baseline"])]
                    differences.append(
                        (
                            int(a["premature"])
                            + int(a["clean_alarm"])
                            - int(b["premature"])
                            - int(b["clean_alarm"])
                        )
                        if metric == "burden"
                        else int(a[metric]) - int(b[metric])
                    )
                values, invalid = [], 0
                for _ in range(2000):
                    chosen = []
                    for robot in (
                        sorted(set(task_robot.values())) if stratified else [None]
                    ):
                        pool = [
                            t for t in tasks if not stratified or task_robot[t] == robot
                        ]
                        chosen.extend(
                            rng.choice(pool, size=len(pool), replace=True).tolist()
                        )
                    # Expand sampled clusters, rather than use the analysis weights.
                    draw = [
                        d
                        for task in chosen
                        for s, d in zip(selection, differences, strict=True)
                        if registry[s]["task_id"] == task
                    ]
                    if draw:
                        values.append(sum(draw) / len(draw))
                    else:
                        invalid += 1
                expected = contrast["metrics"][metric]
                np.testing.assert_allclose(
                    expected["difference"], np.mean(differences), rtol=0, atol=1e-14
                )
                np.testing.assert_allclose(
                    expected["ci95"],
                    np.quantile(values, [0.025, 0.975]),
                    rtol=0,
                    atol=1e-14,
                )
                assert expected["invalid_draws"] == invalid
                checked.append([filename, contrast["baseline"], metric])
    for peak in read(root, "retrospective_peaks.json"):
        child = root / "failtime" / f"fold{peak['fold']}"
        with np.load(child / "risks/evaluation/clean" / (peak["sample"] + ".npz")) as d:
            candidates = [
                (float(score), -i)
                for i, score in enumerate(d[peak["method"]])
                if np.isfinite(score)
            ]
            expected = float(d["time"][-max(candidates)[1]]) if candidates else None
        assert peak["peak_time"] == expected
        assert peak["absolute_error"] == (
            abs(expected - peak["onset"]) if expected is not None else None
        )
        assert peak["within_one_second"] == (
            expected is not None and abs(expected - peak["onset"]) <= 1 + 1e-7
        )
    # REBOOT main reproduction already checks all outputs against its historical
    # independent audit. Recount the paired invalid-reset change here.
    reboot = read(root, "reboot_outcomes.json")
    q = [
        r
        for r in reboot
        if r["variant"] == "Q" and r["method"] == "B3" and r["role"] == "recovery"
    ]
    assert (
        len(q) == 55
        and sum(r["timely"] for r in q) == 1
        and sum(r["INVALID_onset_reset_timely"] for r in q) == 51
    )
    assert len(read(root, "reboot_reproduction.json")["duplicate_alias_pairs"]) == 60
    return {
        "status": "PASS",
        "scope": "Original independent scalar fold auditor plus independent pooled counts, once-only IDs, Wilson arithmetic, expanded-cluster paired resampling and global maxima; independent implementation, same operator (no independent human replication)",
        "folds": fold_reports,
        "pooled_outcomes": len(raw),
        "paired_checks": len(checked),
        "numeric_signatures_recomputed": len(signatures),
        "registered_group_hash_assignment": "PASS",
        "reboot_Q_B3": {"n": 55, "continuous": 1, "INVALID_reset": 51},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--derived-only", action="store_true")
    args = parser.parse_args()
    assert not (args.root / "completion_manifest.json").exists()
    result = audit_derived(args.root) if args.derived_only else audit(args.root)
    filename = (
        "independent_derived_audit.json"
        if args.derived_only
        else "independent_numerical_audit.json"
    )
    (args.root / filename).write_text(json.dumps(result, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    main()
