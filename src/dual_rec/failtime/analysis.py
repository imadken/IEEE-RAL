"""Fixed descriptive aggregation, task-paired uncertainty and scientific gates."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np

from dual_rec.failtime.experiment import read, save


def aggregate(rows):
    fail = [r for r in rows if r["is_failure"]]
    success = [r for r in rows if not r["is_failure"]]
    counts = {
        k: sum(r[k] for r in rows)
        for k in ("timely", "premature", "late", "missed", "abstention")
    }
    exposure = sum(r["exposure"] for r in success)
    alarms = sum(r["clean_alarm"] for r in success)
    delays = [r["delay"] for r in fail if r["timely"]]
    return {
        **counts,
        "failures": len(fail),
        "successes": len(success),
        "clean_alarms": alarms,
        "abstentions": counts.pop("abstention"),
        "rates": {
            "timely": counts["timely"] / len(fail) if fail else None,
            "premature": counts["premature"] / len(fail) if fail else None,
            "clean_alarm": alarms / len(success) if success else None,
            "burden": (counts["premature"] + alarms) / len(rows) if rows else None,
        },
        "clean_exposure_seconds": exposure,
        "false_alarms_per_hour": 3600 * alarms / exposure if exposure else None,
        "observable_failures": sum(r["observable_window"] for r in fail),
        "delays": delays,
        "median_delay": float(np.median(delays)) if delays else None,
    }


def summarize(root):
    outcomes = read(root, "outcomes.json")
    registry = {r["sample"]: r for r in read(root, "cohort_qualification.json")}
    grouped = defaultdict(list)
    for r in outcomes:
        grouped[
            (r["method"], r["alpha"], r["persistence"], r["stress"], r["split"])
        ].append(r)
    summary = []
    stratified = []
    for key, rows in grouped.items():
        spec = dict(
            zip(("method", "alpha", "persistence", "stress", "split"), key, strict=True)
        )
        summary.append({**spec, **aggregate(rows)})
        if spec["alpha"] == 0.1 and spec["persistence"] == 0.1:
            for dimension in ("task_id", "robot"):
                for value in sorted({r[dimension] for r in rows}):
                    stratified.append(
                        {
                            **spec,
                            "stratum_type": dimension,
                            "stratum": value,
                            **aggregate([r for r in rows if r[dimension] == value]),
                        }
                    )
    save(root / "summary.json", summary)
    save(root / "stratified.json", stratified)
    clean = [
        r
        for r in outcomes
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["persistence"] == 0.1
    ]
    index = {(r["sample"], r["method"]): r for r in clean}
    ids = sorted({r["sample"] for r in clean})
    tasks = sorted({registry[s]["task_id"] for s in ids})
    contrasts = []
    for baseline in ("B2", "B3", "B4", "MCSFA_no_accum"):
        rng = np.random.default_rng(20261112)
        metrics = {}
        for metric in ("timely", "premature", "clean_alarm", "burden"):
            population = (
                ids
                if metric == "burden"
                else [
                    s
                    for s in ids
                    if registry[s]["verdict"]
                    == ("success" if metric == "clean_alarm" else "fail")
                ]
            )

            def indicator(s, m, metric=metric):
                return (
                    int(index[(s, m)]["premature"]) + int(index[(s, m)]["clean_alarm"])
                    if metric == "burden"
                    else int(index[(s, m)][metric])
                )

            delta = np.array(
                [indicator(s, "MCSFA") - indicator(s, baseline) for s in population],
                float,
            )
            clusters = [registry[s]["task_id"] for s in population]
            boot = []
            invalid = 0
            for _ in range(2000):
                chosen = rng.choice(tasks, len(tasks), replace=True)
                weights = np.array([np.sum(chosen == task) for task in clusters])
                if not weights.sum():
                    invalid += 1
                    continue
                boot.append(float(np.sum(delta * weights) / weights.sum()))
            metrics[metric] = {
                "difference": float(delta.mean()) if len(delta) else None,
                "ci95": np.quantile(boot, [0.025, 0.975]).tolist() if boot else None,
                "valid_draws": len(boot),
                "invalid_draws": invalid,
            }
        contrasts.append(
            {
                "method": "MCSFA",
                "baseline": baseline,
                "alpha": 0.1,
                "persistence": 0.1,
                "stress": "clean",
                "metrics": metrics,
            }
        )
    save(
        root / "paired_effects.json",
        {"seed": 20261112, "draws": 2000, "unit": "task_id", "contrasts": contrasts},
    )
    role = read(root, "source_role_predictions.json")
    source = []
    for split in ("train", "calibration", "evaluation"):
        all_rows = [r for r in role if r["split"] == split]
        rows = [r for r in all_rows if r["eligible"]]
        pos = np.array([r["score"] for r in rows if r["label"]])
        neg = np.array([r["score"] for r in rows if not r["label"]])
        diff = pos[:, None] - neg
        auc = (
            float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / diff.size)
            if diff.size
            else None
        )
        accuracy = (
            float(((pos >= 0.5).mean() + (neg < 0.5).mean()) / 2)
            if len(pos) and len(neg)
            else None
        )
        source.append(
            {
                "split": split,
                "recordings": len(rows),
                "failures": len(pos),
                "successes": len(neg),
                "excluded": len(all_rows) - len(rows),
                "auroc": auc,
                "balanced_accuracy": accuracy,
            }
        )
    save(root / "source_role_summary.json", source)
    # Fixed method screening against the same-modality sequential comparatorB2.
    cells = {
        r["method"]: r
        for r in summary
        if r["alpha"] == 0.1 and r["persistence"] == 0.1 and r["stress"] == "clean"
    }
    m, b = cells["MCSFA"], cells["B2"]
    effect = contrasts[0]["metrics"]
    point_a = (
        m["rates"]["timely"] - b["rates"]["timely"] >= 0.05 - 1e-12
        and m["rates"]["premature"] <= b["rates"]["premature"]
        and m["rates"]["clean_alarm"] <= b["rates"]["clean_alarm"]
    )
    ci_a = effect["timely"]["ci95"][0] > 0
    point_b = (
        b["rates"]["burden"] > 0
        and m["rates"]["burden"] <= 0.8 * b["rates"]["burden"]
        and m["rates"]["timely"] >= b["rates"]["timely"] - 0.02 - 1e-12
    )
    ci_b = effect["burden"]["ci95"][1] < 0
    contrasts_dev = read(root, "development_contrasts.json")
    dev = []
    for method in cells:
        records = [
            r
            for r in contrasts_dev
            if r["method"] == method and r["mean_change"] is not None
        ]
        dev.append(
            {
                "method": method,
                "included": len(records),
                "positive_changes": sum(r["mean_change"] > 0 for r in records),
                "median_change": float(np.median([r["mean_change"] for r in records]))
                if records
                else None,
            }
        )
    save(root / "development_contrast_summary.json", dev)
    gate = {
        "G0": read(root, "data_gate.json")["status"],
        "G1": "DEVELOPMENT_CONTRAST_RECORDED_CONTEXT_SPECIFICITY_INCONCLUSIVE",
        "G1_reason": "Development contrasts and early-prefix role controls are quantified; without independently time-matched counterfactual histories they do not establish event specificity beyond normal progress.",
        "G2": "PASS_SCREENING"
        if point_a and ci_a or point_b and ci_b
        else "METHOD_NO_GO",
        "G2_details": {
            "timely_route_point": point_a,
            "timely_ci_favorable": ci_a,
            "burden_route_point": point_b,
            "burden_ci_favorable": ci_b,
            "reference": "B2 global same-modality sequential baseline",
        },
        "G3": "NOT_ESTIMABLE_NO_HELDOUT_SO101",
        "G3_reason": "Fixed task hash yields2ALOHAevaluationtasks only; no cross-platform held-out result.",
        "disposition": "Exploratory screening only; no physical recovery or publication-readiness claim",
    }
    save(root / "gates.json", gate)
    print(gate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    summarize(args.root)


if __name__ == "__main__":
    main()
