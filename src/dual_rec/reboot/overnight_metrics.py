"""First-alarm scoring and exploratory recording-level paired inference."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np

from dual_rec.reboot.overnight_data import save_json, sha

METHODS = ("B0", "B1", "B2", "B3", "P0", "P1", "P2")


def first_alarm(times, scores, threshold):
    beginning = None
    for now, score in zip(times, scores, strict=True):
        if not np.isfinite(score) or score < threshold:
            beginning = None
        else:
            if beginning is None:
                beginning = now
            if now - beginning >= 0.1 - 2e-6:
                return float(now)
    return None


def persistent_capacity(times, scores):
    values = []
    for end, now in enumerate(times):
        start = np.searchsorted(times, now - 0.1 + 2e-6, side="right") - 1
        if start >= 0 and start < end and np.isfinite(scores[start : end + 1]).all():
            values.append(float(np.min(scores[start : end + 1])))
    return max(values) if values else -np.inf


def calibrate(records):
    capacities = sorted([persistent_capacity(t, s) for t, s in records], reverse=True)
    allowed = int(np.floor(0.1 * len(capacities)))
    boundary = capacities[allowed]
    if not np.isfinite(boundary):
        raise ValueError("Calibration lacks reference exposure")
    threshold = float(np.nextafter(boundary, np.inf))
    alarms = sum(first_alarm(t, s, threshold) is not None for t, s in records)
    assert alarms <= allowed
    return {
        "threshold": threshold,
        "reference_alarms": alarms,
        "reference_count": len(records),
        "allowed": allowed,
        "reference_capacities": capacities,
    }


def outcome(row, times, scores, threshold, horizon, *, delta=0):
    alarm = first_alarm(times, scores, threshold)
    result = {
        "group": row["group"],
        "role": row["role"],
        "fold": row["fold"],
        "alarm_time": alarm,
        "threshold": threshold,
        "horizon": horizon,
        "exposure": float(min(horizon, row["frames"] / 30 - 1 / 30)),
        "censored_exposure": bool(row["frames"] / 30 - 1 / 30 < horizon - 2e-6),
        "timely": False,
        "premature": False,
        "reference_alarm": False,
        "evaluable": False,
        "delay": None,
        "lead": None,
        "boundary_delta": delta,
    }
    if row["role"] == "reference":
        result.update(
            status="reference_alarm" if alarm is not None else "reference_quiet",
            reference_alarm=alarm is not None,
        )
        return result
    low, high = (
        row["onset"] + delta,
        min(row["recovery"] - delta, horizon, result["exposure"]),
    )
    result["evaluable"] = bool(low < high)
    result["full_target_observed"] = bool(
        row["recovery"] <= min(horizon, result["exposure"]) + 2e-6
    )
    result["premature"] = bool(alarm is not None and alarm < row["onset"])
    result["optimistic_post_onset_reset"] = False
    selected = times >= row["onset"]
    reset = first_alarm(times[selected], scores[selected], threshold)
    if reset is not None:
        result["optimistic_post_onset_reset"] = bool(
            reset < min(row["recovery"], horizon)
        )
    if not result["evaluable"]:
        status = "unobservable_target"
    elif alarm is None:
        status = "no_alarm"
    elif low <= alarm < high:
        status = "timely"
        result.update(
            timely=True, delay=alarm - row["onset"], lead=row["recovery"] - alarm
        )
    elif (
        delta > 0
        and min(abs(alarm - row["onset"]), abs(alarm - row["recovery"])) <= delta
    ):
        status = "timing_ambiguous"
    elif alarm < low:
        status = "premature"
    else:
        status = "late"
    result["status"] = status
    return result


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[
            (row["variant"], row["method"], row["stress"], row["boundary_delta"])
        ].append(row)
    result = []
    for (variant, method, stress, delta), group in groups.items():
        rec = [r for r in group if r["role"] == "recovery"]
        eligible = [r for r in rec if r["evaluable"]]
        refs = [r for r in group if r["role"] == "reference"]
        detected = [r for r in eligible if r["timely"]]
        result.append(
            {
                "variant": variant,
                "method": method,
                "stress": stress,
                "boundary_delta": delta,
                "timely": len(detected),
                "evaluable": len(eligible),
                "recovery_recordings": len(rec),
                "premature": sum(r["premature"] for r in rec),
                "reference_alarms": sum(r["reference_alarm"] for r in refs),
                "references": len(refs),
                "misses_including_premature_and_late": len(eligible) - len(detected),
                "median_detected_delay": float(
                    np.median([r["delay"] for r in detected])
                )
                if detected
                else None,
                "median_detected_lead": float(np.median([r["lead"] for r in detected]))
                if detected
                else None,
                "optimistic_reset_timely": sum(
                    r.get("optimistic_post_onset_reset", False) for r in rec
                ),
                "status_counts": dict(Counter(r["status"] for r in group)),
                "censored_recordings": sum(r["censored_exposure"] for r in group),
                "total_exposure_seconds": sum(r["exposure"] for r in group),
            }
        )
    return result


def paired_effects(rows):
    clean = [r for r in rows if r["stress"] == "clean"]
    result = []
    rng = np.random.default_rng(20261111)
    for variant in ("Q", "QC"):
        for delta in (0, 0.5, 1.0):
            for a, b in (("B3", "B2"), ("P1", "P0"), ("P1", "P2")):
                left = {
                    r["group"]: r
                    for r in clean
                    if r["variant"] == variant
                    and r["method"] == a
                    and r["boundary_delta"] == delta
                }
                right = {
                    r["group"]: r
                    for r in clean
                    if r["variant"] == variant
                    and r["method"] == b
                    and r["boundary_delta"] == delta
                }
                if not left or not right:
                    continue
                values = {}
                for metric, role in (
                    ("timely", "recovery"),
                    ("premature", "recovery"),
                    ("reference_alarm", "reference"),
                ):
                    common = sorted(
                        g
                        for g in left.keys() & right.keys()
                        if left[g]["role"] == role
                        and (
                            metric != "timely"
                            or left[g]["evaluable"]
                            and right[g]["evaluable"]
                        )
                    )
                    differences = np.array(
                        [
                            float(left[g][metric]) - float(right[g][metric])
                            for g in common
                        ]
                    )
                    if not len(differences):
                        values[metric] = None
                        continue
                    draws = differences[
                        rng.integers(0, len(differences), size=(2000, len(differences)))
                    ].mean(axis=1)
                    values[metric] = {
                        "difference": float(differences.mean()),
                        "ci95": np.quantile(draws, [0.025, 0.975]).tolist(),
                        "recordings": len(differences),
                    }
                result.append(
                    {
                        "variant": variant,
                        "delta": delta,
                        "contrast": f"{a}-{b}",
                        "effects": values,
                    }
                )
    return result


def score(root):
    registry = [
        r for r in json.loads((root / "registry.json").read_text()) if r["eligible"]
    ]
    by_group = {r["group"]: r for r in registry}
    thresholds, outcomes, seeds, phase_rows = {}, [], [], []
    prediction_hashes = {}
    for fold in range(5):
        for variant in ("Q", "QC"):
            base = root / "predictions" / f"fold{fold}" / variant
            calibration = [
                r
                for r in registry
                if r["fold"] == (fold + 1) % 5 and r["role"] == "reference"
            ]
            loaded_cal = {
                r["group"]: dict(
                    np.load(
                        base / "clean/calibration" / (r["group"].split(":")[1] + ".npz")
                    )
                )
                for r in calibration
            }
            methods = [m for m in METHODS if m in next(iter(loaded_cal.values()))]
            for method in methods:
                key = f"{fold}:{variant}:{method}"
                thresholds[key] = calibrate(
                    [(d["time"], d[method]) for d in loaded_cal.values()]
                )
                if method in ("B3", "P0", "P1", "P2"):
                    for index, seed in enumerate((11, 23, 37)):
                        thresholds[key + f":{seed}"] = calibrate(
                            [
                                (d["time"], d[method + "_seeds"][index])
                                for d in loaded_cal.values()
                            ]
                        )
            for path in sorted(base.glob("*/evaluation/*.npz")):
                prediction_hashes[str(path.relative_to(root))] = sha(path)
                data = dict(np.load(path))
                row = by_group["recording:" + path.stem]
                stress = path.parent.parent.name
                for method in methods:
                    threshold = thresholds[f"{fold}:{variant}:{method}"]["threshold"]
                    for delta in (0, 0.5, 1.0) if stress == "clean" else (0,):
                        result = outcome(
                            row,
                            data["time"],
                            data[method],
                            threshold,
                            float(data["horizon"]),
                            delta=delta,
                        )
                        result.update(variant=variant, method=method, stress=stress)
                        outcomes.append(result)
                    if stress == "clean" and method in ("B3", "P0", "P1", "P2"):
                        for i, seed in enumerate((11, 23, 37)):
                            result = outcome(
                                row,
                                data["time"],
                                data[method + "_seeds"][i],
                                thresholds[f"{fold}:{variant}:{method}:{seed}"][
                                    "threshold"
                                ],
                                float(data["horizon"]),
                            )
                            result.update(
                                variant=variant,
                                method=method,
                                stress="clean",
                                seed=seed,
                            )
                            seeds.append(result)
                if (
                    stress == "clean"
                    and row["role"] == "recovery"
                    and "phase_P0" in data
                ):
                    bounds = row["raw_annotation"]["phase_boundaries"]
                    truth = np.full(len(data["time"]), -1)
                    for i in range(5):
                        mask = (
                            (data["native_frame"] >= bounds[f"tau_{i}"])
                            & (data["native_frame"] < bounds[f"tau_{i + 1}"])
                            & (data["time"] < row["recovery"])
                        )
                        truth[mask] = i
                    valid = truth >= 0
                    grammar = json.loads(
                        (root / f"fold{fold}_{variant}_grammar.json").read_text()
                    )
                    for method in ("P0", "P1", "P2"):
                        estimated = data["phase_" + method].argmax(1)
                        accuracy = float(np.mean(estimated[valid] == truth[valid]))
                        violations = sum(
                            not grammar["allowed"][int(a)][int(b)]
                            for a, b in pairwise(estimated)
                        )
                        phase_rows.append(
                            {
                                "group": row["group"],
                                "fold": fold,
                                "variant": variant,
                                "method": method,
                                "frames": int(valid.sum()),
                                "correct": int(
                                    np.sum(estimated[valid] == truth[valid])
                                ),
                                "episode_accuracy": accuracy,
                                "marginal_argmax_graph_violations_full_stream": violations,
                                "unresolved_seed_frames": int(
                                    data["phase_unresolved"].sum()
                                ),
                            }
                        )
    save_json(root / "thresholds.json", thresholds)
    save_json(root / "outcomes.json", outcomes)
    save_json(root / "seed_outcomes.json", seeds)
    save_json(root / "phase_results.json", phase_rows)
    save_json(root / "summary.json", summarize(outcomes))
    save_json(root / "paired_effects.json", paired_effects(outcomes))
    # A seal of the main predictions precedes any external-reference evaluation.
    for path in sorted((root / "models").glob("*.pt")):
        prediction_hashes[str(path.relative_to(root))] = sha(path)
    for path in sorted((root / "predictions").glob("fold*/*/clean/calibration/*.npz")):
        prediction_hashes[str(path.relative_to(root))] = sha(path)
    save_json(
        root / "main_prediction_seal.json",
        {
            "registration_sha256": sha(root / "registration.json"),
            "sha256": prediction_hashes,
        },
    )
    print(
        json.dumps(
            [
                r
                for r in summarize(outcomes)
                if r["stress"] == "clean" and r["boundary_delta"] == 0
            ]
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    score(args.root)


if __name__ == "__main__":
    main()
