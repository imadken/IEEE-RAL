"""Independent direct-stream audit; imports no detector or compared scorer."""

from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from scipy.special import expit

OLD = Path("results/reboot-overnight/20261111T224622Z")
METHODS = ("B0", "B1", "B2", "B3", "P0", "P1", "P2", "B2R")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(root, name):
    return json.loads((root / name).read_text())


def brute_stream(times, scores):
    """Simultaneously run every raw threshold and immediately above each tie."""
    values = np.unique(scores[np.isfinite(scores)])
    thresholds = (
        np.unique(np.r_[values, np.nextafter(values, np.inf), np.inf])
        if len(values)
        else np.array([0.0, np.inf])
    )
    start = np.full(len(thresholds), np.nan)
    first = np.full(len(thresholds), np.nan)
    capacities = np.full(len(times), -np.inf)
    for index, now in enumerate(times):
        above = np.isfinite(scores[index]) & (scores[index] >= thresholds)
        start[~above] = np.nan
        start[above & np.isnan(start)] = now
        ending = above & (now - start >= 0.1 - 2e-6)
        if ending.any():
            capacities[index] = np.max(thresholds[ending])
        first[ending & np.isnan(first)] = now
    return thresholds, first, capacities


def at_threshold(grid, first, theta):
    index = np.searchsorted(grid, theta, side="left")
    return first[index] if index < len(grid) else np.nan


def own_windows(x, t):
    values = []
    for end in range(len(t)):
        chosen = (t[: end + 1] >= t[end] - 1 - 2e-6) & np.isfinite(x[: end + 1]).all(
            axis=1
        )
        block = x[: end + 1][chosen]
        time = t[: end + 1][chosen]
        if not len(block):
            values.append(np.full(4 * x.shape[1], np.nan))
            continue
        centered = time - time.mean()
        slope = (
            centered @ block / (centered @ centered)
            if len(block) > 1
            else np.zeros(x.shape[1])
        )
        values.append(np.r_[block[-1], block.mean(0), block.std(0), slope])
    return np.asarray(values)


def supplemental(root):
    """Check annotation contrasts and source-role inference without rank helpers."""
    rows = {r["group"]: r for r in read(OLD, "registry.json") if r["eligible"]}
    outcomes = read(root, "outcomes.json")
    for result in outcomes:
        row = rows[result["group"]]
        exposure = min(result["horizon"], row["frames"] / 30 - 1 / 30)
        assert result["censored_exposure"] == bool(
            row["frames"] / 30 - 1 / 30 < result["horizon"] - 2e-6
        )
        first = result["alarm_time"]
        if row["role"] == "reference":
            assert result["status"] == (
                "reference_quiet" if first is None else "reference_alarm"
            )
            assert not result["evaluable"]
        else:
            high = min(row["recovery"], exposure)
            assert result["evaluable"] == bool(row["onset"] < high)
            assert result["full_target_observed"] == bool(
                row["recovery"] <= exposure + 2e-6
            )
            status = (
                "unobservable_target"
                if row["onset"] >= high
                else "no_alarm"
                if first is None
                else "premature"
                if first < row["onset"]
                else "timely"
                if first < high
                else "late"
            )
            assert result["status"] == status
            assert result["lead"] == (
                row["recovery"] - first if status == "timely" else None
            )
    contrasts = read(root, "within_recording.json")
    for result in contrasts:
        row = rows[result["group"]]
        variant = result["variant"]
        method = result["method"]
        gap = result["gap"]
        path = (
            OLD
            / "predictions"
            / f"fold{row['fold']}"
            / variant
            / "clean/evaluation"
            / (row["group"].split(":")[1] + ".npz")
        )
        with np.load(path) as data:
            t = data["time"]
            s = data[method]
            h = float(data["horizon"])
        _, _, capacity = brute_stream(t, s)
        before = [
            i
            for i, now in enumerate(t)
            if row["onset"] - gap - 1 <= now < row["onset"] - gap and np.isfinite(s[i])
        ]
        after = [
            i
            for i, now in enumerate(t)
            if row["onset"] + gap
            <= now
            < min(row["onset"] + gap + 1, row["recovery"], h)
            and np.isfinite(s[i])
        ]
        n = min(len(before), len(after))
        assert result["samples"] == n
        if n:
            a, b = before[-n:], after[:n]
            assert result["mean_change"] == float(s[b].mean() - s[a].mean())
            ca, cb = max(capacity[a]), max(capacity[b])
            assert result["capacity_pre"] == (float(ca) if np.isfinite(ca) else None)
            assert result["capacity_target"] == (float(cb) if np.isfinite(cb) else None)
            assert result["target_capacity_greater"] == bool(cb > ca)
    rng = np.random.default_rng(20261112)
    predictions = read(root, "source_role_predictions.json")
    for report in read(root, "source_role_summary.json"):
        population = sorted(
            [r for r in predictions if r["variant"] == report["variant"]],
            key=lambda r: r["group"],
        )
        y = np.array([r["role"] == "recovery" for r in population])
        s = np.array([r["score"] for r in population])
        assert len(y) == 116 and sum(y) == 54

        def metrics(labels, scores):
            p = scores[labels]
            n = scores[~labels]
            auc = ((p[:, None] > n).sum() + 0.5 * (p[:, None] == n).sum()) / (
                len(p) * len(n)
            )
            ba = ((p >= 0.5).mean() + (n < 0.5).mean()) / 2
            return float(auc), float(ba)

        np.testing.assert_allclose(
            metrics(y, s), [report["auroc"], report["balanced_accuracy"]], atol=1e-12
        )
        positive = np.flatnonzero(y)
        negative = np.flatnonzero(~y)
        boot = []
        for _ in range(2000):
            indices = np.r_[
                rng.choice(positive, len(positive)), rng.choice(negative, len(negative))
            ]
            boot.append(metrics(y[indices], s[indices]))
        np.testing.assert_allclose(
            np.quantile(boot, [0.025, 0.975], axis=0).T, report["ci95"], atol=1e-12
        )
    result = {
        "status": "PASS",
        "independent_status_censoring_rows": len(outcomes),
        "within_recording_rows": len(contrasts),
        "source_role_predictions": len(predictions),
        "scope": "Independent brute-stream capacities and direct pairwise AUROC/recording bootstrap",
    }
    (root / "independent_controls_audit.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.controls_only:
        supplemental(root)
        return
    rows = [r for r in read(OLD, "registry.json") if r["eligible"]]
    by_id = {r["group"]: r for r in rows}
    assert len(by_id) == 117 and sum(r["role"] == "recovery" for r in rows) == 55
    registration = read(root, "registration.json")
    old_registration = read(OLD, "registration.json")
    assert registration["folds"] == old_registration["folds"]
    assert registration["prior_registry_sha256"] == digest(OLD / "registry.json")
    for fold in range(5):
        assert set(registration["folds"][fold]["train"]) == {
            r["group"] for r in rows if r["fold"] not in (fold, (fold + 1) % 5)
        }
        assert set(registration["folds"][fold]["evaluation"]) == {
            r["group"] for r in rows if r["fold"] == fold
        }
        assert set(registration["folds"][fold]["calibration"]) == {
            r["group"] for r in rows if r["fold"] == (fold + 1) % 5
        }

    @lru_cache(maxsize=1600)
    def data(fold, variant, split, group, stress="clean"):
        path = (
            OLD
            / "predictions"
            / f"fold{fold}"
            / variant
            / stress
            / split
            / (group.split(":")[1] + ".npz")
        )
        with np.load(path) as d:
            return {
                k: d[k]
                for k in (
                    "time",
                    "features",
                    "native_frame",
                    "horizon",
                    "B0",
                    "B1",
                    "B2",
                    "B3",
                    "P0",
                    "P1",
                    "P2",
                )
            }

    @lru_cache(maxsize=2000)
    def new_score(fold, variant, split, group, stress="clean"):
        path = (
            root
            / "b2r_predictions"
            / f"fold{fold}"
            / variant
            / stress
            / split
            / (group.split(":")[1] + ".npz")
        )
        with np.load(path) as d:
            return d["scores"]

    def score(fold, variant, split, group, method, stress="clean"):
        return (
            new_score(fold, variant, split, group, stress)
            if method == "B2R"
            else data(fold, variant, split, group, stress)[method]
        )

    @lru_cache(maxsize=2000)
    def brute(fold, variant, split, group, method):
        d = data(fold, variant, split, group)
        return brute_stream(d["time"], score(fold, variant, split, group, method))

    @lru_cache(maxsize=2000)
    def caps(fold, variant, split, group, method):
        row = by_id[group]
        d = data(fold, variant, split, group)
        _, _, r = brute(fold, variant, split, group, method)
        if row["role"] == "reference":
            return -np.inf, -np.inf, float(max(r))
        high = min(row["recovery"], float(d["horizon"]), row["frames"] / 30 - 1 / 30)
        a = r[d["time"] < row["onset"]]
        b = r[(d["time"] >= row["onset"]) & (d["time"] < high)]
        return float(max(a, default=-np.inf)), float(max(b, default=-np.inf)), -np.inf

    feasibility = read(root, "score_feasibility.json")
    checks = 0
    for result in feasibility:
        row = by_id[result["group"]]
        fold = row["fold"]
        variant = result["variant"]
        method = result["method"]
        a, b, c = caps(fold, variant, "evaluation", row["group"], method)
        for k, v in zip(("A", "B", "C"), (a, b, c), strict=True):
            assert result[k] == (float(v) if np.isfinite(v) else None)
        grid, first, r = brute(fold, variant, "evaluation", row["group"], method)
        d = data(fold, variant, "evaluation", row["group"])
        if row["role"] == "recovery":
            high = min(
                row["recovery"], float(d["horizon"]), row["frames"] / 30 - 1 / 30
            )
            direct = np.isfinite(first) & (first >= row["onset"]) & (first < high)
            np.testing.assert_array_equal(direct, (a < grid) & (grid <= b))
            np.testing.assert_array_equal(
                np.isfinite(first) & (first < row["onset"]), grid <= a
            )
            assert result["feasible"] == bool(direct.any())
        else:
            np.testing.assert_array_equal(np.isfinite(first), grid <= c)
        checks += len(grid)
    envelopes = read(root, "hindsight_ceilings.json")
    for fold in range(5):
        population = [r for r in rows if r["fold"] == fold]
        for variant in ("Q", "QC"):
            for method in METHODS:
                saved = dict(
                    np.load(
                        root / "hindsight_only" / f"fold{fold}_{variant}_{method}.npz"
                    )
                )
                breakpoints = np.unique(
                    np.concatenate(
                        [
                            score(fold, variant, "evaluation", r["group"], method)
                            for r in population
                        ]
                    )
                )
                breakpoints = breakpoints[np.isfinite(breakpoints)]
                expected = np.unique(
                    np.r_[breakpoints, np.nextafter(breakpoints, np.inf), np.inf]
                )
                np.testing.assert_array_equal(saved["threshold"], expected)
                timely = np.zeros(len(expected), dtype=int)
                premature = timely.copy()
                reference = timely.copy()
                for row in population:
                    grid, first, _ = brute(
                        fold, variant, "evaluation", row["group"], method
                    )
                    when = first[np.searchsorted(grid, expected, side="left")]
                    if row["role"] == "reference":
                        reference += np.isfinite(when)
                    else:
                        high = min(
                            row["recovery"], registration["folds"][fold]["horizon"]
                        )
                        timely += (
                            np.isfinite(when) & (when >= row["onset"]) & (when < high)
                        )
                        premature += np.isfinite(when) & (when < row["onset"])
                np.testing.assert_array_equal(saved["timely"], timely)
                np.testing.assert_array_equal(saved["premature"], premature)
                np.testing.assert_array_equal(saved["reference"], reference)
                nrec = sum(r["role"] == "recovery" for r in population)
                nref = len(population) - nrec
                for alpha in (0.05, 0.1, 0.2):
                    allowed = (premature <= np.floor(alpha * nrec)) & (
                        reference <= np.floor(alpha * nref)
                    )
                    ceiling = int(max(timely[allowed]))
                    index = np.flatnonzero(allowed & (timely == ceiling))[-1]
                    report = next(
                        r
                        for r in envelopes
                        if r["fold"] == fold
                        and r["variant"] == variant
                        and r["method"] == method
                        and r["alpha"] == alpha
                    )
                    assert (
                        report["timely"] == ceiling
                        and report["scope"] == "HINDSIGHT_ONLY_NOT_DEPLOYABLE"
                    )
                    assert report["oracle_threshold"] == (
                        float(expected[index]) if np.isfinite(expected[index]) else None
                    )
    calibration = read(root, "calibrations.json")
    assert calibration["scope"] == "calibration_only"
    for identifier, result in calibration["thresholds"].items():
        fold, variant, method, alpha, rule = identifier.split(":")
        fold = int(fold)
        alpha = float(alpha)
        population = [r for r in rows if r["fold"] == (fold + 1) % 5]
        collections = {"reference": [], "recovery_prefix": []}
        for row in population:
            a, _, c = caps(fold, variant, "calibration", row["group"], method)
            pop = "reference" if row["role"] == "reference" else "recovery_prefix"
            collections[pop].append((row["group"], c if pop == "reference" else a))
        fitted = {}
        for pop, records in collections.items():
            valid = [v for _, v in records if np.isfinite(v)]
            fitted[pop] = float(
                np.nextafter(
                    sorted(valid, reverse=True)[int(np.floor(alpha * len(valid)))],
                    np.inf,
                )
            )
            actual = result["populations"][pop]
            assert {r["group"] for r in actual} == {g for g, _ in records}
            for r in actual:
                v = dict(records)[r["group"]]
                assert r["valid"] == bool(np.isfinite(v))
                assert r["capacity"] == (v if np.isfinite(v) else None)
        theta = fitted["reference"] if rule == "C0" else max(fitted.values())
        assert theta == result["threshold"]
        if rule == "C0" and alpha == 0.1 and method != "B2R":
            assert (
                theta
                == read(OLD, "thresholds.json")[f"{fold}:{variant}:{method}"][
                    "threshold"
                ]
            )
    outcomes = read(root, "outcomes.json")
    old_outcomes = {
        (r["group"], r["variant"], r["method"]): r
        for r in read(OLD, "outcomes.json")
        if r["stress"] == "clean" and r["boundary_delta"] == 0
    }
    for result in outcomes:
        row = by_id[result["group"]]
        fold = row["fold"]
        variant = result["variant"]
        method = result["method"]
        stress = result["stress"]
        d = data(fold, variant, "evaluation", row["group"], stress)
        scores = score(fold, variant, "evaluation", row["group"], method, stress)
        theta = calibration["thresholds"][
            f"{fold}:{variant}:{method}:{result['alpha']:g}:{result['rule']}"
        ]["threshold"]
        # Direct scalar monitor, independent of capacities for every outcome.
        begin = None
        first = None
        for now, value in zip(d["time"], scores, strict=True):
            if not np.isfinite(value) or value < theta:
                begin = None
            else:
                if begin is None:
                    begin = now
                if now - begin >= 0.1 - 2e-6:
                    first = float(now)
                    break
        assert result["alarm_time"] == first
        exposure = min(float(d["horizon"]), row["frames"] / 30 - 1 / 30)
        assert abs(result["exposure"] - exposure) < 1e-12
        if row["role"] == "reference":
            assert result["reference_alarm"] == (first is not None)
        else:
            high = min(row["recovery"], exposure)
            assert result["timely"] == (
                first is not None and row["onset"] <= first < high
            )
            assert result["premature"] == (first is not None and first < row["onset"])
            if result["timely"]:
                assert abs(result["delay"] - (first - row["onset"])) < 1e-12
        if (
            result["rule"] == "C0"
            and result["alpha"] == 0.1
            and stress == "clean"
            and method != "B2R"
        ):
            before = old_outcomes[(row["group"], variant, method)]
            for field in (
                "alarm_time",
                "timely",
                "premature",
                "reference_alarm",
                "status",
                "evaluable",
            ):
                assert before[field] == result[field]
    model_paths = list((root / "models").glob("*.pt"))
    assert len(model_paths) == 20
    maximum_prediction_error = 0.0
    for path in model_paths:
        model = torch.load(path, map_location="cpu", weights_only=False)
        fold = int(path.stem[4])
        variant = path.stem.split("_")[1]
        kind = model["kind"]
        expected = [
            r
            for r in rows
            if r["fold"] not in (fold, (fold + 1) % 5)
            and (kind == "source_role" or r["role"] == "recovery")
        ]
        if kind == "source_role":
            expected = [
                r for r in expected if r["role"] == "reference" or r["onset"] > 1
            ]
        assert model["training_ids"] == [r["group"] for r in expected]
        assert model["registration_sha256"] == digest(root / "registration.json")
        train_x = []
        train_y = []
        train_masks = []
        for row in expected:
            d = data(row["fold"], variant, "evaluation", row["group"])
            if kind == "source_role":
                keep = d["time"] <= 1 + 2e-6
                x = own_windows(d["features"][keep], d["time"][keep])[-1:]
                y = np.array([row["role"] == "recovery"], dtype=float)
                mask = np.ones(1, bool)
            else:
                x = own_windows(d["features"], d["time"])
                y = (d["time"] >= row["onset"]).astype(float)
                mask = (d["time"] < row["recovery"]) & (
                    d["time"] < registration["folds"][fold]["horizon"]
                )
            train_x.append(x)
            train_y.append(y)
            train_masks.append(mask)
        mean = np.mean(
            [x[m].mean(0) for x, m in zip(train_x, train_masks, strict=True)], 0
        )
        second = np.mean(
            [(x[m] ** 2).mean(0) for x, m in zip(train_x, train_masks, strict=True)], 0
        )
        std = np.maximum(np.sqrt(np.maximum(second - mean * mean, 0)), 1e-6)
        np.testing.assert_allclose(model["scaler"]["mean"], mean, atol=1e-12)
        np.testing.assert_allclose(model["scaler"]["std"], std, atol=1e-12)
        ratio = min(
            10.0,
            sum(((1 - y)[m]).sum() for y, m in zip(train_y, train_masks, strict=True))
            / sum(y[m].sum() for y, m in zip(train_y, train_masks, strict=True)),
        )
        assert abs(ratio - model["positive_weight"]) < 1e-12

        def infer(x, mean=mean, std=std, model=model):
            return expit(
                np.c_[np.ones(len(x)), np.clip((x - mean) / std, -10, 10)]
                @ model["beta"]
            )

        if kind == "source_role":
            reports = [
                r
                for r in read(root, "source_role_predictions.json")
                if r["fold"] == fold and r["variant"] == variant
            ]
            for result in reports:
                row = by_id[result["group"]]
                assert row["role"] == "reference" or row["onset"] > 1
                d = data(fold, variant, "evaluation", row["group"])
                keep = d["time"] <= 1 + 2e-6
                probability = float(
                    infer(own_windows(d["features"][keep], d["time"][keep])[-1:])[0]
                )
                maximum_prediction_error = max(
                    maximum_prediction_error, abs(probability - result["score"])
                )
                assert abs(probability - result["score"]) < 1e-9
        else:
            for split, population in (
                ("calibration", [r for r in rows if r["fold"] == (fold + 1) % 5]),
                ("evaluation", [r for r in rows if r["fold"] == fold]),
            ):
                for stress in (
                    ("clean",)
                    if split == "calibration"
                    else ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
                ):
                    for row in population:
                        d = data(fold, variant, split, row["group"], stress)
                        independent = infer(own_windows(d["features"], d["time"]))
                        saved = new_score(fold, variant, split, row["group"], stress)
                        finite = np.isfinite(saved)
                        maximum_prediction_error = max(
                            maximum_prediction_error,
                            float(np.max(np.abs(saved[finite] - independent[finite]))),
                        )
                        np.testing.assert_allclose(
                            saved, independent, atol=1e-9, equal_nan=True
                        )
    rng = np.random.default_rng(20261112)
    clean = [r for r in outcomes if r["stress"] == "clean"]
    for contrast in read(root, "paired_effects.json"):
        a, b = contrast["contrast"].split("-")
        ma, ca = a.split("/")
        mb, cb = b.split("/")
        left = {
            r["group"]: r
            for r in clean
            if r["variant"] == contrast["variant"]
            and r["alpha"] == contrast["alpha"]
            and r["method"] == ma
            and r["rule"] == ca
        }
        right = {
            r["group"]: r
            for r in clean
            if r["variant"] == contrast["variant"]
            and r["alpha"] == contrast["alpha"]
            and r["method"] == mb
            and r["rule"] == cb
        }
        for metric, role in (
            ("timely", "recovery"),
            ("premature", "recovery"),
            ("reference_alarm", "reference"),
        ):
            ids = sorted(g for g, r in by_id.items() if r["role"] == role)
            differences = np.array(
                [int(left[g][metric]) - int(right[g][metric]) for g in ids]
            )
            draws = rng.integers(0, len(ids), (2000, len(ids)))
            ci = np.quantile(differences[draws].mean(1), [0.025, 0.975])
            report = contrast["effects"][metric]
            assert abs(report["difference"] - differences.mean()) < 1e-12
            np.testing.assert_allclose(report["ci95"], ci, atol=1e-12)
    for name, expected in read(root, "consumed_inputs.json").items():
        assert digest(Path(name)) == expected
    result = {
        "status": "PASS",
        "scope": "Independent direct-stream threshold brute force, A/B/C identities, all shared-threshold breakpoints, C0/C1 populations, outcomes/censoring, train-only new scalers, direct logistic predictions and paired bootstrap; no detector/scorer imported",
        "feasibility_rows": len(feasibility),
        "direct_threshold_checks": checks,
        "hindsight_cells": len(envelopes),
        "calibration_cells": len(calibration["thresholds"]),
        "outcome_rows": len(outcomes),
        "new_fits": len(model_paths),
        "maximum_logistic_prediction_error": maximum_prediction_error,
        "outcomes_sha256": digest(root / "outcomes.json"),
        "feasibility_sha256": digest(root / "score_feasibility.json"),
        "paired_effects_sha256": digest(root / "paired_effects.json"),
    }
    (root / "independent_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
