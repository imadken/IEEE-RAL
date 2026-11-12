"""Registered descriptive analysis of fixed out-of-fold prediction streams."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np

from dual_rec.contracts.cases import peak_readout
from dual_rec.failtime.analysis import aggregate
from dual_rec.failtime.experiment import read, save


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    radius = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(center - radius), float(center + radius)]


def effects(outcomes, registry, stratified=False):
    clean = [
        r
        for r in outcomes
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["persistence"] == 0.1
    ]
    index = {(r["sample"], r["method"]): r for r in clean}
    ids = sorted({r["sample"] for r in clean})
    tasks = sorted({registry[s]["task_id"] for s in ids})
    task_robot = {registry[s]["task_id"]: registry[s]["robot"] for s in ids}
    contrasts = []
    for baseline in ("B2", "B3", "B4", "MCSFA_no_accum"):
        rng = np.random.default_rng(20261112)
        metrics = {}
        for metric in ("timely", "premature", "clean_alarm", "burden"):
            selected = (
                ids
                if metric == "burden"
                else [
                    s
                    for s in ids
                    if registry[s]["verdict"]
                    == ("success" if metric == "clean_alarm" else "fail")
                ]
            )

            def indicator(s, method, metric=metric):
                row = index[(s, method)]
                return (
                    int(row["premature"]) + int(row["clean_alarm"])
                    if metric == "burden"
                    else int(row[metric])
                )

            delta = np.array(
                [indicator(s, "MCSFA") - indicator(s, baseline) for s in selected],
                float,
            )
            clusters = [registry[s]["task_id"] for s in selected]
            boot = []
            invalid = 0
            for _ in range(2000):
                if stratified:
                    chosen = np.concatenate(
                        [
                            rng.choice(
                                [t for t in tasks if task_robot[t] == robot],
                                sum(task_robot[t] == robot for t in tasks),
                                replace=True,
                            )
                            for robot in sorted(set(task_robot.values()))
                        ]
                    )
                else:
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
    return {
        "seed": 20261112,
        "draws": 2000,
        "unit": "task_id",
        "robot_stratified": stratified,
        "contrasts": contrasts,
        "scope": "Conditional task bootstrap of fixed cross-fitted predictions; overlapping training folds and model-fitting uncertainty not resampled. Degenerate zero intervals do not establish equivalence.",
    }


def with_intervals(rows):
    result = aggregate(rows)
    result["wilson95"] = {
        "timely": wilson(result["timely"], result["failures"]),
        "premature": wilson(result["premature"], result["failures"]),
        "clean_alarm": wilson(result["clean_alarms"], result["successes"]),
    }
    observable = [r for r in rows if r["observable_window"]]
    result["observable_window_counterpart"] = aggregate(observable)
    return result


def role_summary(rows):
    rows = [r for r in rows if r["eligible"]]
    pos = np.array([r["score"] for r in rows if r["label"]])
    neg = np.array([r["score"] for r in rows if not r["label"]])
    diff = pos[:, None] - neg
    return {
        "n": len(rows),
        "failures": len(pos),
        "successes": len(neg),
        "auroc": float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / diff.size)
        if diff.size
        else None,
        "balanced_accuracy": float(((pos >= 0.5).mean() + (neg < 0.5).mean()) / 2)
        if len(pos) and len(neg)
        else None,
    }


def summarize(root):
    all_rows, role, peaks, coverage = [], [], [], []
    registry = {
        r["sample"]: r
        for r in read(root / "failtime/fold0", "cohort_qualification.json")
    }
    for fold in range(5):
        child = root / "failtime" / f"fold{fold}"
        outcomes = read(child, "outcomes.json")
        save(child / "paired_effects.json", effects(outcomes, registry))
        all_rows.extend([{**r, "fold": fold} for r in outcomes])
        predictions = read(child, "source_role_predictions.json")
        role.extend(
            [{**r, "fold": fold} for r in predictions if r["split"] == "evaluation"]
        )
        splits = read(child, "registration.json")["splits"]
        coverage.append(
            {
                "fold": fold,
                "partitions": [
                    {
                        "split": split,
                        "records": len(ids),
                        "tasks": sorted(
                            {
                                registry[s]["robot"] + "/" + registry[s]["task_id"]
                                for s in ids
                            }
                        ),
                        "failures": sum(registry[s]["verdict"] == "fail" for s in ids),
                        "successes": sum(
                            registry[s]["verdict"] == "success" for s in ids
                        ),
                    }
                    for split, ids in splits.items()
                ],
            }
        )
        for sample in splits["evaluation"]:
            row = registry[sample]
            if row["verdict"] != "fail":
                continue
            with np.load(child / "risks/evaluation/clean" / (sample + ".npz")) as data:
                for method in (
                    "B0_time",
                    "B0_prior",
                    "B1",
                    "B2",
                    "B3",
                    "B4",
                    "MCSFA",
                    "MCSFA_no_mode",
                    "MCSFA_no_accum",
                ):
                    peaks.append(
                        {
                            "sample": sample,
                            "fold": fold,
                            "method": method,
                            "onset": row["onset"],
                            "robot": row["robot"],
                            "task_id": row["task_id"],
                            "onset_within_observed": row["onset_within_observed"],
                            "full_window_observable": row["onset"] + 1
                            <= float(data["time"][-1]) + 1e-7,
                            **peak_readout(data["time"], data[method], row["onset"]),
                        }
                    )
    # Exactly one OOF evaluation per recording for every registered operating cell.
    primary = [
        r
        for r in all_rows
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["persistence"] == 0.1
    ]
    assert len(primary) == 900 and len({r["sample"] for r in primary}) == 100
    assert (
        len(
            {
                (r["sample"], r["method"], r["stress"], r["alpha"], r["persistence"])
                for r in all_rows
            }
        )
        == 40500
        == len(all_rows)
    )
    grouped = defaultdict(list)
    for r in all_rows:
        grouped[(r["method"], r["alpha"], r["persistence"], r["stress"])].append(r)
    summary = [
        {
            **dict(zip(("method", "alpha", "persistence", "stress"), key, strict=True)),
            **with_intervals(rows),
        }
        for key, rows in sorted(grouped.items())
    ]
    stratified = []
    for dimension in ("robot", "task_id", "fold"):
        for value in sorted({r[dimension] for r in primary}):
            for method in sorted({r["method"] for r in primary}):
                rows = [
                    r
                    for r in primary
                    if r[dimension] == value and r["method"] == method
                ]
                stratified.append(
                    {
                        "dimension": dimension,
                        "stratum": value,
                        "method": method,
                        **with_intervals(rows),
                    }
                )
    retrospective = []
    for method in sorted({r["method"] for r in peaks}):
        rows = [r for r in peaks if r["method"] == method]
        errors = [r["absolute_error"] for r in rows if r["absolute_error"] is not None]
        retrospective.append(
            {
                "method": method,
                "failures": len(rows),
                "finite_estimates": len(errors),
                "mean_absolute_error": float(np.mean(errors)) if errors else None,
                "within_one_second": sum(r["within_one_second"] for r in rows),
                "observable_window_counterpart": {
                    "failures": sum(r["full_window_observable"] for r in rows),
                    "within_one_second": sum(
                        r["within_one_second"]
                        for r in rows
                        if r["full_window_observable"]
                    ),
                    "mean_absolute_error": float(
                        np.mean(
                            [
                                r["absolute_error"]
                                for r in rows
                                if r["full_window_observable"]
                                and r["absolute_error"] is not None
                            ]
                        )
                    ),
                },
                "readout": "Earliest finite global maximum; retrospective diagnostic only, no threshold deployment or author-score reproduction",
            }
        )
    save(root / "failtime_outcomes.json", all_rows)
    save(root / "failtime_summary.json", summary)
    save(root / "failtime_stratified.json", stratified)
    save(root / "fold_coverage.json", coverage)
    save(root / "paired_effects.json", effects(all_rows, registry))
    save(
        root / "paired_effects_robot_stratified.json", effects(all_rows, registry, True)
    )
    save(root / "retrospective_peaks.json", peaks)
    save(root / "retrospective_summary.json", retrospective)
    save(
        root / "source_role_oof.json",
        {
            "predictions": role,
            "summary": role_summary(role),
            "folds": [
                {"fold": k, **role_summary([r for r in role if r["fold"] == k])}
                for k in range(5)
            ],
            "scope": "Same original early-prefix classifier; pooled scores come from different models; source-role separability is not onset specificity",
        },
    )
    save(
        root / "pilot_informativeness.json",
        {
            "old_evaluation": {
                "records": 8,
                "tasks": 2,
                "robots": ["aloha"],
                "timely": 0,
                "failures": 5,
                "timely_wilson95": wilson(0, 5),
                "zero_of_three_reference_wilson95": wilson(0, 3),
            },
            "new_oof": {
                "records": 100,
                "tasks": 13,
                "robots": ["aloha", "so101"],
                "failures": 57,
                "successes": 43,
            },
            "scope": "Coverage comparison, not a paired causal effect of larger sample size. All data exposed; folds have overlapping training sets.",
        },
    )
    print(
        {
            "outcomes": len(all_rows),
            "checkpoints": sum(
                len(read(root / "failtime" / f"fold{k}", "models_index.json"))
                for k in range(5)
            ),
            "source_role": role_summary(role),
        }
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    summarize(args.root)


if __name__ == "__main__":
    main()
