"""Prespecified calibration matrix, within-recording controls and uncertainty."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from dual_rec.reboot.onset_specificity import (
    ALPHAS,
    METHODS,
    OLD,
    capacities,
    encoded,
    inherited,
    load_scores,
    maximum,
    persistence_series,
    population_threshold,
    progress,
    read,
    registry,
)
from dual_rec.reboot.overnight_data import save_json, sha
from dual_rec.reboot.overnight_metrics import outcome


def key(fold, variant, method, alpha, rule):
    return f"{fold}:{variant}:{method}:{alpha:g}:{rule}"


def deployment_threshold(root, fold, variant, method, alpha, rule):
    if (
        rule not in ("C0", "C1")
        or alpha not in ALPHAS
        or method not in (*METHODS, "B2R")
    ):
        raise ValueError(
            "Only registered score models and C0/C1 calibration are deployable"
        )
    artifact = read(root, "calibrations.json")
    if artifact.get("scope") != "calibration_only" or artifact.get(
        "registration_sha256"
    ) != sha(root / "registration.json"):
        raise ValueError(
            "Not a registered calibration artifact; hindsight cannot be deployed"
        )
    row = artifact["thresholds"][key(fold, variant, method, alpha, rule)]
    if not row["available"]:
        raise ValueError("Calibration population unavailable")
    return row["threshold"]


def compare(root):
    rows = registry()
    thresholds = {}
    outcomes = []
    inherited_thresholds = read(OLD, "thresholds.json")
    for fold in range(5):
        calibration = [r for r in rows if r["fold"] == (fold + 1) % 5]
        evaluation = [r for r in rows if r["fold"] == fold]
        for variant in ("Q", "QC"):
            for method in (*METHODS, "B2R"):
                populations = {"reference": [], "recovery_prefix": []}
                for row in calibration:
                    data, scores = load_scores(
                        root, fold, variant, "calibration", row, method
                    )
                    value, _ = capacities(row, data, scores)
                    pop = (
                        "reference" if row["role"] == "reference" else "recovery_prefix"
                    )
                    cap = value["C"] if pop == "reference" else value["A"]
                    populations[pop].append(
                        {
                            "group": row["group"],
                            "fold": row["fold"],
                            "capacity": encoded(cap),
                            "valid": bool(np.isfinite(cap)),
                            "invalid_reason": None
                            if np.isfinite(cap)
                            else "no_finite_persistent_capacity",
                            "mask": "whole available horizon"
                            if pop == "reference"
                            else "strictly time < released onset",
                        }
                    )
                for alpha in ALPHAS:
                    fitted = {
                        pop: population_threshold(
                            [r["capacity"] if r["valid"] else -np.inf for r in values],
                            alpha,
                        )
                        for pop, values in populations.items()
                    }
                    for rule in ("C0", "C1"):
                        available = fitted["reference"]["available"] and (
                            rule == "C0" or fitted["recovery_prefix"]["available"]
                        )
                        theta = fitted["reference"]["threshold"] if available else None
                        if rule == "C1" and available:
                            theta = max(theta, fitted["recovery_prefix"]["threshold"])
                        if method in METHODS and alpha == 0.1 and rule == "C0":
                            assert (
                                theta
                                == inherited_thresholds[f"{fold}:{variant}:{method}"][
                                    "threshold"
                                ]
                            )
                        realized = {
                            pop: {
                                "alarms": sum(
                                    r["valid"] and r["capacity"] >= theta
                                    for r in values
                                )
                                if available
                                else None,
                                "valid_count": sum(r["valid"] for r in values),
                                "total_count": len(values),
                            }
                            for pop, values in populations.items()
                        }
                        thresholds[key(fold, variant, method, alpha, rule)] = {
                            "available": available,
                            "threshold": theta,
                            "fold": fold,
                            "variant": variant,
                            "method": method,
                            "alpha": alpha,
                            "rule": rule,
                            "populations": populations,
                            "separate_fits": fitted,
                            "realized": realized,
                        }
                        if not available:
                            continue
                        for stress in (
                            "clean",
                            "drop0.1",
                            "drop0.3",
                            "delay0.2",
                            "delay0.5",
                        ):
                            for row in evaluation:
                                data, scores = load_scores(
                                    root,
                                    fold,
                                    variant,
                                    "evaluation",
                                    row,
                                    method,
                                    stress,
                                )
                                result = outcome(
                                    row,
                                    data["time"],
                                    scores,
                                    theta,
                                    float(data["horizon"]),
                                )
                                result.pop("optimistic_post_onset_reset", None)
                                result.update(
                                    variant=variant,
                                    method=method,
                                    alpha=alpha,
                                    rule=rule,
                                    stress=stress,
                                )
                                outcomes.append(result)
    save_json(
        root / "calibrations.json",
        {
            "scope": "calibration_only",
            "registration_sha256": sha(root / "registration.json"),
            "thresholds": thresholds,
        },
    )
    save_json(root / "outcomes.json", outcomes)
    progress(
        root,
        "CALIBRATION_MATRIX_COMPLETE",
        thresholds=len(thresholds),
        outcomes=len(outcomes),
    )


def within_recording(root):
    result = []
    for row in registry():
        if row["role"] != "recovery":
            continue
        for variant in ("Q", "QC"):
            data = inherited(row["fold"], variant, "evaluation", row["group"])
            t = data["time"]
            for method in ("B0", "B2", "B3", "P0", "P1", "P2"):
                scores = data[method]
                r = persistence_series(t, scores)
                for gap in (0, 0.5):
                    pre = np.flatnonzero(
                        (t >= row["onset"] - gap - 1)
                        & (t < row["onset"] - gap)
                        & np.isfinite(scores)
                    )
                    target = np.flatnonzero(
                        (t >= row["onset"] + gap)
                        & (
                            t
                            < min(
                                row["onset"] + gap + 1,
                                row["recovery"],
                                float(data["horizon"]),
                            )
                        )
                        & np.isfinite(scores)
                    )
                    n = min(len(pre), len(target))
                    a, b = pre[-n:] if n else pre[:0], target[:n]
                    before, after = maximum(r[a]), maximum(r[b])
                    result.append(
                        {
                            "group": row["group"],
                            "fold": row["fold"],
                            "variant": variant,
                            "method": method,
                            "gap": gap,
                            "samples": n,
                            "pre_available": len(pre),
                            "target_available": len(target),
                            "included": n > 0,
                            "reason": None
                            if n
                            else "insufficient_equal_finite_samples",
                            "mean_pre": float(scores[a].mean()) if n else None,
                            "mean_target": float(scores[b].mean()) if n else None,
                            "mean_change": float(scores[b].mean() - scores[a].mean())
                            if n
                            else None,
                            "capacity_pre": encoded(before),
                            "capacity_target": encoded(after),
                            "capacity_change": float(after - before)
                            if np.isfinite(before) and np.isfinite(after)
                            else None,
                            "capacity_margin_reason": None
                            if np.isfinite(before) and np.isfinite(after)
                            else "one_or_both_capacities_minus_infinity",
                            "target_capacity_greater": bool(after > before)
                            if n
                            else None,
                            "pre_bounds": [float(t[a[0]]), float(t[a[-1]])]
                            if n
                            else None,
                            "target_bounds": [float(t[b[0]]), float(t[b[-1]])]
                            if n
                            else None,
                        }
                    )
    save_json(root / "within_recording.json", result)
    progress(root, "WITHIN_RECORDING_COMPLETE", rows=len(result))


def wilson(success, total):
    if not total:
        return None
    z = 1.959963984540054
    p = success / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return [float(max(0, center - half)), float(min(1, center + half))]


def summarize(root):
    outcomes = read(root, "outcomes.json")
    groups = defaultdict(list)
    for row in outcomes:
        groups[
            (row["variant"], row["method"], row["alpha"], row["rule"], row["stress"])
        ].append(row)
    summary = []
    for (variant, method, alpha, rule, stress), rows in groups.items():
        recovery = [r for r in rows if r["role"] == "recovery"]
        refs = [r for r in rows if r["role"] == "reference"]
        observed = [r for r in recovery if r["evaluable"]]
        detected = [r for r in observed if r["timely"]]
        timely = len(detected)
        prem = sum(r["premature"] for r in recovery)
        alarms = sum(r["reference_alarm"] for r in refs)
        summary.append(
            {
                "variant": variant,
                "method": method,
                "alpha": alpha,
                "rule": rule,
                "stress": stress,
                "timely": timely,
                "evaluable": len(observed),
                "premature": prem,
                "recoveries": len(recovery),
                "reference_alarms": alarms,
                "references": len(refs),
                "timely_wilson95": wilson(timely, len(observed)),
                "premature_wilson95": wilson(prem, len(recovery)),
                "reference_wilson95": wilson(alarms, len(refs)),
                "late": sum(r["status"] == "late" for r in recovery),
                "no_alarm": sum(r["status"] == "no_alarm" for r in recovery),
                "unobservable": sum(not r["evaluable"] for r in recovery),
                "censored_exposures": sum(r["censored_exposure"] for r in rows),
                "total_reference_exposure": sum(r["exposure"] for r in refs),
                "missed": len(observed) - timely,
                "median_detected_delay": float(
                    np.median([r["delay"] for r in detected])
                )
                if detected
                else None,
                "delays": [r["delay"] for r in detected],
                "lead_times": [r["lead"] for r in detected],
            }
        )
    save_json(root / "summary.json", summary)
    clean = [r for r in outcomes if r["stress"] == "clean"]
    index = {
        (r["variant"], r["method"], r["alpha"], r["rule"], r["group"]): r for r in clean
    }
    by_group = {r["group"]: r for r in registry()}
    contrasts = []
    rng = np.random.default_rng(20261112)
    for variant in ("Q", "QC"):
        for alpha in ALPHAS:
            pairs = [(method, "C1", method, "C0") for method in (*METHODS, "B2R")]
            pairs += [
                (a, "C1", b, "C1")
                for a, b in (("B2R", "B2"), ("P1", "P0"), ("P1", "P2"))
            ]
            for a, ca, b, cb in pairs:
                effects = {}
                for metric, role in (
                    ("timely", "recovery"),
                    ("premature", "recovery"),
                    ("reference_alarm", "reference"),
                ):
                    selected = sorted(
                        g for g, r in by_group.items() if r["role"] == role
                    )
                    differences = np.array(
                        [
                            float(index[(variant, a, alpha, ca, g)][metric])
                            - float(index[(variant, b, alpha, cb, g)][metric])
                            for g in selected
                        ]
                    )
                    boot = differences[
                        rng.integers(0, len(selected), (2000, len(selected)))
                    ].mean(1)
                    effects[metric] = {
                        "difference": float(differences.mean()),
                        "ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
                        "recordings": len(selected),
                    }
                contrasts.append(
                    {
                        "variant": variant,
                        "alpha": alpha,
                        "contrast": f"{a}/{ca}-{b}/{cb}",
                        "primary": variant == "Q" and alpha == 0.1 and a != b,
                        "effects": effects,
                    }
                )
    save_json(root / "paired_effects.json", contrasts)
    source = read(root, "source_role_predictions.json")
    source_summary = []
    rng = np.random.default_rng(20261112)
    for variant in ("Q", "QC"):
        population = sorted(
            [r for r in source if r["variant"] == variant], key=lambda r: r["group"]
        )
        y = np.array([r["role"] == "recovery" for r in population])
        s = np.array([r["score"] for r in population])

        def metrics(labels, scores):
            pos = int(labels.sum())
            neg = len(labels) - pos
            auc = (rankdata(scores)[labels].sum() - pos * (pos + 1) / 2) / (pos * neg)
            accuracy = (
                (scores[labels] >= 0.5).mean() + (scores[~labels] < 0.5).mean()
            ) / 2
            return float(auc), float(accuracy)

        point = metrics(y, s)
        boot = []
        positive = np.flatnonzero(y)
        negative = np.flatnonzero(~y)
        for _ in range(2000):
            indexes = np.r_[
                rng.choice(positive, len(positive)), rng.choice(negative, len(negative))
            ]
            boot.append(metrics(y[indexes], s[indexes]))
        source_summary.append(
            {
                "variant": variant,
                "recordings": len(y),
                "recovery": int(y.sum()),
                "reference": int((~y).sum()),
                "auroc": point[0],
                "balanced_accuracy": point[1],
                "ci95": np.quantile(boot, [0.025, 0.975], axis=0).T.tolist(),
                "folds": [
                    {
                        "fold": fold,
                        "count": sum(r["fold"] == fold for r in population),
                        "metrics": metrics(
                            y[[r["fold"] == fold for r in population]],
                            s[[r["fold"] == fold for r in population]],
                        ),
                    }
                    for fold in range(5)
                ],
            }
        )
    save_json(root / "source_role_summary.json", source_summary)
    progress(
        root,
        "SUMMARY_AND_UNCERTAINTY_COMPLETE",
        summary_cells=len(summary),
        paired_contrasts=len(contrasts),
    )


def review_examples(root):
    selected = []
    sequences = {}
    feasibility = {
        (r["group"], r["variant"], r["method"]): r
        for r in read(root, "score_feasibility.json")
    }
    outcomes = [
        r
        for r in read(root, "outcomes.json")
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["rule"] == "C0"
    ]
    rows = {r["group"]: r for r in registry()}
    for variant in ("Q", "QC"):
        for method in (*METHODS, "B2R"):
            population = [
                r
                for r in outcomes
                if r["variant"] == variant
                and r["method"] == method
                and r["role"] == "recovery"
            ]
            categories = {
                "premature_infeasible": lambda r, variant=variant, method=method: (
                    not feasibility[(r["group"], variant, method)]["feasible"]
                    and r["premature"]
                ),
                "premature_feasible": lambda r, variant=variant, method=method: (
                    feasibility[(r["group"], variant, method)]["feasible"]
                    and r["premature"]
                ),
                "timely": lambda r: r["timely"],
                "miss": lambda r: r["status"] in ("late", "no_alarm"),
            }
            for category, predicate in categories.items():
                examples = sorted(
                    [r for r in population if predicate(r)], key=lambda r: r["group"]
                )[:3]
                block = {
                    "variant": variant,
                    "method": method,
                    "category": category,
                    "available": len(examples),
                    "examples": [],
                }
                for result in examples:
                    row = rows[result["group"]]
                    fold = row["fold"]
                    data, scores = load_scores(
                        root, fold, variant, "evaluation", row, method
                    )
                    name = f"{variant}_{method}_{category}_{row['group'].split(':')[1]}"
                    sequences[name + "_time"] = data["time"]
                    sequences[name + "_score"] = scores
                    sequences[name + "_capacity"] = persistence_series(
                        data["time"], scores
                    )
                    block["examples"].append(
                        {
                            "group": row["group"],
                            "fold": fold,
                            "raw_annotation": row["raw_annotation"],
                            "feasibility": feasibility[(row["group"], variant, method)],
                            "original_outcome": result,
                            "source_repository": row["repository"],
                            "source_episode": row["episode"],
                            "series_prefix": name,
                            "C1_threshold": read(root, "calibrations.json")[
                                "thresholds"
                            ][key(fold, variant, method, 0.1, "C1")]["threshold"],
                        }
                    )
                selected.append(block)
    save_json(root / "annotation_review.json", selected)
    np.savez_compressed(root / "annotation_review_scores.npz", **sequences)
    progress(
        root,
        "ANNOTATION_REVIEW_COMPLETE",
        categories=len(selected),
        examples=sum(r["available"] for r in selected),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("compare", "within", "summarize", "review"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {
        "compare": compare,
        "within": within_recording,
        "summarize": summarize,
        "review": review_examples,
    }[args.stage](args.root)


if __name__ == "__main__":
    main()
