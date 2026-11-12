"""Independent direct-stream numerical audit for the fixed FailTime campaign.

No model implementation, feature extractor, calibration code or metric scorer
is imported. Saved causal risks are evaluated by a scalar state machine, and
source-role logits are reconstructed from exported numerical coefficients.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

METHODS = (
    "B0_time",
    "B0_prior",
    "B1",
    "B2",
    "B3",
    "B4",
    "MCSFA",
    "MCSFA_no_mode",
    "MCSFA_no_accum",
)
ALPHAS = (0.05, 0.1, 0.2)
TOLERANCE = 1e-7


def read(root: Path, name: str):
    return json.loads((root / name).read_text())


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def direct_first(
    times: np.ndarray, risks: np.ndarray, threshold: float, persistence: float
) -> float | None:
    """Alarm once from recording start; annotations never enter this function."""
    start = None
    for now, risk in zip(times, risks, strict=True):
        if not np.isfinite(risk) or risk < threshold:
            start = None
        else:
            if start is None:
                start = float(now)
            if float(now) - start >= persistence - TOLERANCE:
                return float(now)
    return None


def direct_capacity(
    times: np.ndarray, risks: np.ndarray, persistence: float = 0.1
) -> float:
    """Largest threshold permitting a persistent alarm anywhere in the prefix.

    Each finite-run ending position searches earlier starts directly. The
    shortest suffix long enough to satisfy persistence has maximal minimum.
    """
    best = -np.inf
    run_start = 0
    for end in range(len(times)):
        if not np.isfinite(risks[end]):
            run_start = end + 1
            continue
        begin = end
        while (
            begin >= run_start and times[end] - times[begin] < persistence - TOLERANCE
        ):
            begin -= 1
        if begin >= run_start:
            best = max(best, float(min(risks[begin : end + 1])))
    return best


def population_threshold(
    values: list[float], alpha: float
) -> tuple[float | None, int, int]:
    valid = sorted((value for value in values if np.isfinite(value)), reverse=True)
    if not valid:
        return None, 0, 0
    allowed = int(np.floor(alpha * len(valid)))
    return float(np.nextafter(valid[allowed], np.inf)), len(valid), allowed


def independent_window(features: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Direct B2 last/mean/std/slope at the final first-second observation."""
    keep = times >= times[-1] - 1 - 2e-6
    block, clock = features[keep], times[keep]
    finite = np.isfinite(block).all(1)
    block, clock = block[finite], clock[finite]
    centered = clock - clock.mean()
    slope = (
        centered @ block / (centered @ centered)
        if len(block) > 1
        else np.zeros(block.shape[1])
    )
    return np.r_[block[-1], block.mean(0), block.std(0), slope]


def own_features(times: np.ndarray, eef: np.ndarray) -> np.ndarray:
    features = np.full((len(times), 32), np.nan)
    last = None
    for index, now in enumerate(times):
        if not np.isfinite(eef[index]).all():
            continue
        delta = (
            np.zeros(16)
            if last is None
            else (eef[index] - eef[last]) / (now - times[last])
        )
        features[index] = np.r_[eef[index], delta]
        last = index
    return features


def source_metrics(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    positive, negative = scores[labels], scores[~labels]
    if not len(positive) or not len(negative):
        return float("nan"), float("nan")
    pair = positive[:, None] - negative
    auc = ((pair > 0).sum() + 0.5 * (pair == 0).sum()) / pair.size
    balanced = ((positive >= 0.5).mean() + (negative < 0.5).mean()) / 2
    return float(auc), float(balanced)


def _assert_close(actual, expected, context, atol=1e-12):
    if expected is None:
        assert actual is None, context
    else:
        assert actual is not None and abs(float(actual) - float(expected)) <= atol, (
            context,
            actual,
            expected,
        )


def audit_source_role(
    root: Path, registry: dict[str, dict], splits: dict[str, list[str]]
) -> dict:
    predictions = read(root, "source_role_predictions.json")
    assert len(predictions) == len(registry) and {
        r["sample"] for r in predictions
    } == set(registry), (
        "Source-role predictions must contain each canonical recording exactly once"
    )
    expected_training = {
        sample
        for sample in splits["train"]
        if registry[sample]["duration"] >= 1
        and (registry[sample]["verdict"] == "success" or registry[sample]["onset"] > 1)
    }
    actual_training = read(root, "source_role_training_ids.json")
    assert set(actual_training) == expected_training, (
        "Source-role fit used incorrect training population"
    )
    parameters = dict(np.load(root / "source_role_model.npz", allow_pickle=False))
    training_vectors = []
    maximum_error = 0.0
    for record in predictions:
        sample = record["sample"]
        row = registry[sample]
        eligible = row["duration"] >= 1 and (
            row["verdict"] == "success" or row["onset"] > 1
        )
        assert record["eligible"] == eligible, ("Source-role eligibility", sample)
        if not eligible:
            continue
        assert record["split"] == next(
            split for split, ids in splits.items() if sample in ids
        )
        assert bool(record["label"]) == (row["verdict"] == "fail"), (
            "Source-role target",
            sample,
        )
        with np.load(root / "arrays" / (sample + ".npz"), allow_pickle=False) as saved:
            native_t = saved["time"]
            native_eef = saved["eef"]
        # Parent records selected first-second packet times for exact sensor
        # schedule matching; no future samples are used to compute any feature.
        if "time" in parameters:
            raise AssertionError("Source-role parameters must not encode episode time")
        with np.load(
            root / "risks" / record["split"] / "clean" / (sample + ".npz"),
            allow_pickle=False,
        ) as saved:
            clean_times = saved["time"]
        times = np.asarray(
            record.get("feature_times", clean_times[clean_times <= 1 + TOLERANCE]),
            dtype=float,
        )
        indices = np.searchsorted(native_t, times + TOLERANCE, side="right") - 1
        assert (indices >= 0).all() and (native_t[indices] <= times + TOLERANCE).all()
        x = own_features(times, native_eef[indices])
        summary = independent_window(x, times)
        if sample in expected_training:
            training_vectors.append(summary)
        design = np.r_[
            1.0, np.clip((summary - parameters["mean"]) / parameters["std"], -10, 10)
        ]
        logit = float(design @ parameters["beta"])
        probability = float(np.exp(-np.logaddexp(0.0, -logit)))
        maximum_error = max(maximum_error, abs(probability - record["score"]))
        assert abs(probability - record["score"]) < 1e-8, (
            "Source-role probability",
            sample,
            probability,
            record["score"],
        )
    matrix = np.asarray(training_vectors)
    mean = matrix.mean(0)
    std = np.maximum(
        np.sqrt(np.maximum((matrix * matrix).mean(0) - mean * mean, 0)), 1e-6
    )
    np.testing.assert_allclose(
        parameters["mean"],
        mean,
        atol=1e-12,
        rtol=0,
        err_msg="Source-role train-only mean",
    )
    np.testing.assert_allclose(
        parameters["std"],
        std,
        atol=1e-10,
        rtol=0,
        err_msg="Source-role train-only standard deviation",
    )
    metrics = []
    for split in ("train", "calibration", "evaluation"):
        rows = sorted(
            [r for r in predictions if r["split"] == split and r["eligible"]],
            key=lambda r: r["sample"],
        )
        if rows:
            auc, ba = source_metrics(
                np.array([bool(r["label"]) for r in rows]),
                np.array([r["score"] for r in rows]),
            )
            metrics.append(
                {
                    "split": split,
                    "n": len(rows),
                    "auroc": auc if np.isfinite(auc) else None,
                    "balanced_accuracy": ba if np.isfinite(ba) else None,
                }
            )
    return {
        "predictions_checked": len(predictions),
        "training_records": len(actual_training),
        "maximum_probability_error": maximum_error,
        "metrics": metrics,
    }


def audit_pairing(root, registry, outcomes):
    artifact = read(root, "paired_effects.json")
    assert (
        artifact["seed"] == 20261112
        and artifact["draws"] == 2000
        and artifact["unit"] == "task_id"
    )
    clean = [
        r
        for r in outcomes
        if r["split"] == "evaluation"
        and r["stress"] == "clean"
        and r["alpha"] == 0.1
        and r["persistence"] == 0.1
    ]
    method_index = {(r["sample"], r["method"]): r for r in clean}
    ids = sorted({r["sample"] for r in clean})
    tasks = sorted({registry[s]["task_id"] for s in ids})
    assert len(tasks) >= 1
    checked = []
    for report in artifact["contrasts"]:
        method, baseline = report["method"], report["baseline"]
        assert method == "MCSFA" and baseline in ("B2", "B3", "B4", "MCSFA_no_accum")
        assert (
            report["alpha"] == 0.1
            and report["persistence"] == 0.1
            and report["stress"] == "clean"
        )
        rng = np.random.default_rng(20261112)
        for metric in ("timely", "premature", "clean_alarm", "burden"):
            if metric == "burden":
                selected = ids
                difference = np.array(
                    [
                        int(method_index[(s, method)]["premature"])
                        + int(method_index[(s, method)]["clean_alarm"])
                        - int(method_index[(s, baseline)]["premature"])
                        - int(method_index[(s, baseline)]["clean_alarm"])
                        for s in selected
                    ],
                    dtype=float,
                )
            else:
                role = "success" if metric == "clean_alarm" else "fail"
                selected = [s for s in ids if registry[s]["verdict"] == role]
                difference = np.array(
                    [
                        int(method_index[(s, method)][metric])
                        - int(method_index[(s, baseline)][metric])
                        for s in selected
                    ],
                    dtype=float,
                )
            task_lookup = [registry[s]["task_id"] for s in selected]
            _assert_close(
                report["metrics"][metric]["difference"],
                float(difference.mean()) if len(difference) else None,
                ("Paired point estimate", baseline, metric),
            )
            boot = []
            invalid = 0
            for _ in range(2000):
                chosen = rng.choice(tasks, len(tasks), replace=True)
                weights = np.array([np.sum(chosen == task) for task in task_lookup])
                if not weights.sum():
                    invalid += 1
                    continue
                boot.append(float(np.sum(difference * weights) / weights.sum()))
            expected = np.quantile(boot, [0.025, 0.975]).tolist() if boot else None
            actual = report["metrics"][metric]["ci95"]
            if expected is None:
                assert actual is None, ("No valid bootstrap support", baseline, metric)
            else:
                np.testing.assert_allclose(
                    actual,
                    expected,
                    atol=1e-12,
                    rtol=0,
                    err_msg=f"Cluster bootstrap {baseline} {metric}",
                )
            if "invalid_draws" in report["metrics"][metric]:
                assert report["metrics"][metric]["invalid_draws"] == invalid
            checked.append(
                {
                    "baseline": baseline,
                    "metric": metric,
                    "difference": report["metrics"][metric]["difference"],
                    "ci95": expected,
                    "invalid_draws": invalid,
                }
            )
    assert {r["baseline"] for r in artifact["contrasts"]} == {
        "B2",
        "B3",
        "B4",
        "MCSFA_no_accum",
    }, "Incomplete prescribed paired contrasts"
    return checked


def audit_seal(root):
    seal = read(root, "models_source_seal.json")
    checked = []
    for key in ("registration_sha256", "thresholds_sha256"):
        if key in seal:
            target = root / (key.removesuffix("_sha256") + ".json")
            assert sha(target) == seal[key], ("Frozen configuration changed", key)
            checked.append(str(target))
    for category in ("sha256", "files", "source_sha256", "model_sha256"):
        mapping = seal.get(category, {})
        if not isinstance(mapping, dict):
            continue
        for name, digest in mapping.items():
            if not isinstance(digest, str) or len(digest) != 64:
                continue
            target = Path(name)
            if not target.is_file():
                target = root / name
            assert target.is_file() and sha(target) == digest, (
                "Frozen input/model/source changed",
                name,
            )
            checked.append(str(target))
    assert checked, "Frozen model/source seal exposes no verifiable file hashes"
    return {
        "seal_sha256": sha(root / "models_source_seal.json"),
        "files_checked": len(checked),
    }


def audit_packets(root, registry, risk_manifest):
    """Reconstruct packet availability with a forward pointer, never lookahead."""
    checked = 0
    for entry in risk_manifest:
        sample = entry["sample"]
        stress = entry["stress"]
        with np.load(root / registry[sample]["arrays"], allow_pickle=False) as original:
            native_t = original["time"]
            native_eef = original["eef"]
        with np.load(root / entry["path"], allow_pickle=False) as saved:
            data = {name: saved[name] for name in saved.files}
        expected_grid = (
            np.arange(int(np.floor((native_t[-1] + 1e-7) / 0.1)) + 1, dtype=float) / 10
        )
        np.testing.assert_array_equal(data["time"], expected_grid)
        indices = np.arange(len(native_t))
        delay = 0.0
        if stress.startswith("drop"):
            seed = 20261112 + int(hashlib.sha256(sample.encode()).hexdigest()[:16], 16)
            keep = np.random.default_rng(seed).random(len(native_t)) >= float(
                stress[4:]
            )
            indices = indices[keep]
        elif stress.startswith("delay"):
            delay = float(stress[5:])
        source = np.full(len(expected_grid), -1, dtype=int)
        cursor = 0
        latest = -1
        for end, now in enumerate(expected_grid):
            while (
                cursor < len(indices)
                and native_t[indices[cursor]] <= now - delay + TOLERANCE
            ):
                latest = int(indices[cursor])
                cursor += 1
            source[end] = latest
        np.testing.assert_array_equal(data["source_index"], source)
        available = source >= 0
        expected_eef = np.full_like(data["eef"], np.nan, dtype=float)
        expected_eef[available] = native_eef[source[available]]
        np.testing.assert_array_equal(data["eef"], expected_eef)
        expected_time = np.full(len(source), np.nan)
        expected_time[available] = native_t[source[available]]
        np.testing.assert_array_equal(data["source_time"], expected_time)
        np.testing.assert_allclose(
            data["features"],
            own_features(expected_grid, expected_eef),
            atol=1e-12,
            rtol=0,
            equal_nan=True,
        )
        ensemble = np.mean(
            [data["B4_seed11"], data["B4_seed23"], data["B4_seed37"]], axis=0
        )
        # Unavailable initial packets mask runtime risks after ensembling.
        ensemble[~available] = np.nan
        np.testing.assert_array_equal(data["B4"], ensemble)
        np.testing.assert_array_equal(data["B2"], data["MCSFA_no_mode"])
        checked += 1
    return {
        "risk_packet_streams_verified": checked,
        "training_risk_streams_verified": sum(
            r["split"] == "train" for r in risk_manifest
        ),
        "calibration_risk_streams_verified": sum(
            r["split"] == "calibration" for r in risk_manifest
        ),
        "evaluation_risk_streams_verified": sum(
            r["split"] == "evaluation" for r in risk_manifest
        ),
        "scope": "Native packet indices, deterministic dropout/delay, sample hold, causal backward differences and declared GRU probability ensemble",
    }


def audit_development_contrasts(root, registry, splits, risk):
    rows = read(root, "development_contrasts.json")
    expected = {
        (sample, method)
        for sample in splits["train"]
        if registry[sample]["verdict"] == "fail"
        for method in METHODS
    }
    actual = set()
    for record in rows:
        sample, method = record["sample"], record["method"]
        assert (sample, method) not in actual, (
            "Duplicate development contrast",
            sample,
            method,
        )
        actual.add((sample, method))
        t, values = risk("train", "clean", sample, method)
        onset = registry[sample]["onset"]
        # Match the frozen windows exactly; no onset reset or score recomputation.
        before = [
            i
            for i, now in enumerate(t)
            if onset - 1 <= now < onset and np.isfinite(values[i])
        ]
        after = [
            i
            for i, now in enumerate(t)
            if onset <= now <= onset + 1 and np.isfinite(values[i])
        ]
        n = min(len(before), len(after))
        assert record["samples"] == n
        change = (
            float(values[after[:n]].mean() - values[before[-n:]].mean()) if n else None
        )
        _assert_close(
            record["mean_change"], change, ("Development mean contrast", sample, method)
        )
    assert actual == expected, "Incomplete development contrast matrix"
    return {
        "rows_verified": len(rows),
        "scope": "Frozen training-only one-second before/after equal-sample means; annotations delimit offline diagnostics only",
    }


def audit_seed_sensitivity(root, registry, splits, risk):
    if not (root / "seed_sensitivity.json").exists():
        return {"available": False}
    artifact = read(root, "seed_sensitivity.json")
    methods = ("B4_seed11", "B4_seed23", "B4_seed37")
    calibrated = {}
    for record in artifact["thresholds"]:
        method, alpha = record["method"], record["alpha"]
        assert method in methods and alpha in ALPHAS
        caps = {"success": {}, "prefix": {}}
        for sample in splits["calibration"]:
            row = registry[sample]
            time, values = risk("calibration", "clean", sample, method)
            population = "success" if row["verdict"] == "success" else "prefix"
            if population == "prefix":
                keep = time < row["onset"]
                time, values = time[keep], values[keep]
            caps[population][sample] = direct_capacity(time, values)
        fitted = {}
        for population, capacities in caps.items():
            saved = record["populations"][population]
            assert len(saved) == len(capacities) and {
                r["sample"] for r in saved
            } == set(capacities)
            for item in saved:
                value = capacities[item["sample"]]
                _assert_close(
                    item["capacity"],
                    value if np.isfinite(value) else None,
                    ("Seed calibration capacity", method, alpha, item["sample"]),
                )
            fitted[population] = population_threshold(list(capacities.values()), alpha)
            _, valid, allowed = fitted[population]
            fit = record["fits"][population]
            assert (
                fit["valid"] == valid
                and fit["invalid"] == len(capacities) - valid
                and fit["allowed"] == allowed
            )
        theta = (
            max(fit[0] for fit in fitted.values())
            if all(fit[0] is not None for fit in fitted.values())
            else None
        )
        _assert_close(
            record["threshold"],
            theta,
            ("Seed matched threshold", method, alpha),
            atol=0.0,
        )
        assert (
            record["available"] == (theta is not None)
            and record["scope"] == "calibration_only"
        )
        for population, capacities in caps.items():
            realized = (
                sum(
                    value >= theta
                    for value in capacities.values()
                    if np.isfinite(value)
                )
                if theta is not None
                else None
            )
            assert record["fits"][population]["realized_alarms"] == realized
            if theta is not None:
                assert realized <= fitted[population][2]
        assert (method, alpha) not in calibrated
        calibrated[(method, alpha)] = theta
    assert set(calibrated) == {
        (method, alpha) for method in methods for alpha in ALPHAS
    }
    outcomes = read(root, "seed_outcomes.json")
    seen = set()
    grouped = defaultdict(list)
    for record in outcomes:
        sample, method, alpha, stress, persistence = (
            record[k] for k in ("sample", "method", "alpha", "stress", "persistence")
        )
        identifier = (sample, method, alpha, stress, persistence)
        assert identifier not in seen
        seen.add(identifier)
        row = registry[sample]
        t, values = risk("evaluation", stress, sample, method)
        theta = calibrated[(method, alpha)]
        assert record["split"] == "evaluation" and sample in splits["evaluation"]
        _assert_close(
            record["threshold"],
            theta,
            ("Seed deployed threshold", identifier),
            atol=0.0,
        )
        first = (
            direct_first(t, values, theta, persistence) if theta is not None else None
        )
        _assert_close(
            record["alarm_time"], first, ("Seed first alarm", identifier), atol=0.0
        )
        failure = row["verdict"] == "fail"
        onset = row.get("onset")
        timely = bool(
            failure and first is not None and onset <= first <= onset + 1 + TOLERANCE
        )
        premature = bool(failure and first is not None and first < onset)
        late = bool(failure and first is not None and first > onset + 1 + TOLERANCE)
        missed = bool(failure and first is None)
        clean = bool(not failure and first is not None)
        status = (
            "timely"
            if timely
            else "premature"
            if premature
            else "late"
            if late
            else "missed"
            if failure
            else "clean_alarm"
            if clean
            else "clean_quiet"
        )
        exposure = float(min(row["duration"], t[-1])) if len(t) else 0.0
        delay = first - onset if timely else None
        abstention = theta is None or not np.isfinite(values).any()
        for name, expected in (
            ("timely", timely),
            ("premature", premature),
            ("late", late),
            ("missed", missed),
            ("clean_alarm", clean),
            ("status", status),
            ("is_failure", failure),
            ("abstention", abstention),
        ):
            assert record[name] == expected, ("Seed outcome", identifier, name)
        _assert_close(record["exposure"], exposure, ("Seed exposure", identifier))
        _assert_close(record["delay"], delay, ("Seed delay", identifier))
        assert record["observable_window"] == bool(
            not failure or onset + 1 <= exposure + TOLERANCE
        )
        grouped[(method, alpha, stress, persistence)].append(record)
    expected = {
        (sample, method, alpha, stress, persistence)
        for sample in splits["evaluation"]
        for method in methods
        for alpha in ALPHAS
        for stress in ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
        for persistence in (0.0, 0.1, 0.2)
    }
    assert seen == expected, "Incomplete fixed-seed outcome matrix"
    summary_cells = set()
    for report in artifact["summary"]:
        key = tuple(report[k] for k in ("method", "alpha", "stress", "persistence"))
        assert key not in summary_cells
        summary_cells.add(key)
        rows = grouped[key]
        failures = [r for r in rows if registry[r["sample"]]["verdict"] == "fail"]
        successes = [r for r in rows if registry[r["sample"]]["verdict"] == "success"]
        for metric in ("timely", "premature", "late", "missed"):
            assert report[metric] == sum(r[metric] for r in failures)
        clean_count = sum(r["clean_alarm"] for r in successes)
        clean_exposure = sum(r["exposure"] for r in successes)
        assert report["clean_alarms"] == clean_count
        assert report["failures"] == len(failures) and report["successes"] == len(
            successes
        )
        assert report["abstentions"] == sum(r["abstention"] for r in rows)
        assert report["observable_failures"] == sum(
            r["observable_window"] for r in failures
        )
        _assert_close(
            report["clean_exposure_seconds"],
            clean_exposure,
            ("Seed summary exposure", key),
        )
        _assert_close(
            report["false_alarms_per_hour"],
            3600 * clean_count / clean_exposure if clean_exposure else None,
            ("Seed alarms/hour", key),
        )
        delays = [r["delay"] for r in failures if r["timely"]]
        assert report["delays"] == delays
        _assert_close(
            report["median_delay"],
            float(np.median(delays)) if delays else None,
            ("Seed median delay", key),
        )
        for metric, numerator, denominator in (
            ("timely", sum(r["timely"] for r in failures), len(failures)),
            ("premature", sum(r["premature"] for r in failures), len(failures)),
            ("clean_alarm", clean_count, len(successes)),
            ("burden", sum(r["premature"] for r in failures) + clean_count, len(rows)),
        ):
            _assert_close(
                report["rates"][metric],
                numerator / denominator if denominator else None,
                ("Seed summary rate", key, metric),
            )
    assert summary_cells == set(grouped), "Incomplete seed summary cells"
    return {
        "available": True,
        "calibration_cells_verified": len(calibrated),
        "outcomes_verified": len(outcomes),
        "summary_cells_verified": len(summary_cells),
        "seed_sensitivity_sha256": sha(root / "seed_sensitivity.json"),
        "seed_outcomes_sha256": sha(root / "seed_outcomes.json"),
        "scope": "Fixed-seed descriptive sensitivity only; no seed selection or refitting",
    }


def audit(root: Path) -> dict:
    registry = {
        r["sample"]: r
        for r in read(root, "cohort_qualification.json")
        if r["status"] == "verified"
    }
    registration = read(root, "registration.json")
    splits = registration["splits"]
    assert set(splits) == {"train", "calibration", "evaluation"}
    assigned = [sample for ids in splits.values() for sample in ids]
    assert len(assigned) == len(set(assigned)) and set(assigned) == set(registry), (
        "Recording split leakage or omission"
    )
    task_sets = {
        name: {(registry[s]["robot"], registry[s]["task_id"]) for s in ids}
        for name, ids in splits.items()
    }
    names = list(task_sets)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            assert not task_sets[left] & task_sets[right], (
                "Task split leakage",
                left,
                right,
            )
    native_hash_checks = 0
    for row in registry.values():
        path = root / row["arrays"]
        assert sha(path) == row["arrays_sha256"], (
            "Qualified arrays changed",
            row["sample"],
        )
        native_hash_checks += 1
    model_index = read(root, "models_index.json")
    expected_models = {
        "nominal",
        "B3",
        "B4_seed11",
        "B4_seed23",
        "B4_seed37",
        "source_role",
    }
    assert set(model_index) == expected_models, (
        "Unexpected or missing prescribed checkpoints"
    )
    for name, entry in model_index.items():
        assert sha(root / entry["path"]) == entry["sha256"], ("Checkpoint hash", name)
        if name == "nominal":
            expected_ids = {
                sample
                for sample in splits["train"]
                if registry[sample]["verdict"] == "success"
            }
        elif name == "source_role":
            expected_ids = {
                sample
                for sample in splits["train"]
                if registry[sample]["duration"] >= 1
                and (
                    registry[sample]["verdict"] == "success"
                    or registry[sample]["onset"] > 1
                )
            }
        else:
            expected_ids = set(splits["train"])
        assert set(entry["training_ids"]) == expected_ids, (
            "Training population leakage",
            name,
        )
        assert entry["registration_sha256"] == sha(root / "registration.json"), (
            "Checkpoint registration",
            name,
        )
    risk_manifest = read(root, "risk_registry.json")
    expected_risks = {
        (split, stress, sample)
        for split, ids in splits.items()
        for stress in (
            ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
            if split == "evaluation"
            else ("clean",)
        )
        for sample in ids
    }
    assert {
        (r["split"], r["stress"], r["sample"]) for r in risk_manifest
    } == expected_risks
    assert len(risk_manifest) == len(expected_risks), "Duplicated risk files"
    for entry in risk_manifest:
        assert sha(root / entry["path"]) == entry["sha256"], (
            "Risk file hash",
            entry["path"],
        )
    packet_audit = audit_packets(root, registry, risk_manifest)
    cache = {}

    def risk(split, stress, sample, method):
        key = (split, stress, sample)
        if key not in cache:
            with np.load(
                root / "risks" / split / stress / (sample + ".npz"),
                allow_pickle=False,
            ) as data:
                cache[key] = {k: data[k] for k in data.files}
            t = cache[key]["time"]
            assert np.isfinite(t).all() and (np.diff(t) > 0).all(), (
                "Bad risk timestamps",
                key,
            )
            assert set(METHODS) <= set(cache[key]), ("Missing registered methods", key)
            finite_source = np.isfinite(cache[key]["source_time"])
            delay = float(stress[5:]) if stress.startswith("delay") else 0.0
            assert (
                cache[key]["source_time"][finite_source]
                <= t[finite_source] - delay + TOLERANCE
            ).all(), ("Future observations", key)
            assert t[0] == 0 and np.allclose(np.diff(t), 0.1, atol=1e-7, rtol=0), (
                "Unregistered risk schedule",
                key,
            )
            assert t[-1] <= registry[sample]["duration"] + TOLERANCE, (
                "Decision after available raw history",
                key,
            )
            np.testing.assert_array_equal(
                cache[key]["B2"],
                cache[key]["MCSFA_no_mode"],
                err_msg=f"No-mode ablation must equal global comparator {key}",
            )
        return cache[key]["time"], cache[key][method]

    thresholds = read(root, "thresholds.json")
    if isinstance(thresholds, dict):
        thresholds = thresholds.get("thresholds", list(thresholds.values()))
    tau = {}
    for report in thresholds:
        method, alpha = report["method"], report["alpha"]
        assert method in METHODS and alpha in ALPHAS
        populations = {"success": [], "prefix": []}
        ids = {"success": set(), "prefix": set()}
        for sample in splits["calibration"]:
            row = registry[sample]
            t, s = risk("calibration", "clean", sample, method)
            category = "success" if row["verdict"] == "success" else "prefix"
            if category == "prefix":
                mask = t < row["onset"]
                t, s = t[mask], s[mask]
            populations[category].append(direct_capacity(t, s))
            ids[category].add(sample)
        for category, capacities in populations.items():
            actual = report["populations"][category]
            assert {r["sample"] for r in actual} == ids[category], (
                "Threshold population IDs",
                method,
                alpha,
                category,
            )
            direct = dict(
                zip(
                    [
                        s
                        for s in splits["calibration"]
                        if (registry[s]["verdict"] == "success")
                        == (category == "success")
                    ],
                    capacities,
                    strict=True,
                )
            )
            for item in actual:
                value = direct[item["sample"]]
                _assert_close(
                    item["capacity"],
                    value if np.isfinite(value) else None,
                    ("Population capacity", method, item["sample"]),
                )
        fitted = [
            population_threshold(populations[category], alpha)
            for category in ("success", "prefix")
        ]
        expected = (
            max(r[0] for r in fitted) if all(r[0] is not None for r in fitted) else None
        )
        _assert_close(
            report["threshold"],
            expected,
            ("Matched calibration threshold", method, alpha),
            atol=0.0,
        )
        for category, (_, n_valid, allowed) in zip(
            ("success", "prefix"), fitted, strict=True
        ):
            metadata = report["fits"][category]
            assert (
                metadata["valid"] == n_valid
                and metadata["invalid"] == len(populations[category]) - n_valid
            )
            assert metadata["allowed"] == allowed
            realized = (
                sum(
                    value >= expected
                    for value in populations[category]
                    if np.isfinite(value)
                )
                if expected is not None
                else None
            )
            assert metadata["realized_alarms"] == realized
        if expected is not None:
            for values, (_, valid, allowed) in zip(
                populations.values(), fitted, strict=True
            ):
                assert sum(v >= expected for v in values if np.isfinite(v)) <= allowed
                assert allowed == int(np.floor(alpha * valid))
        tau[(method, alpha)] = expected
    assert set(tau) == {(method, alpha) for method in METHODS for alpha in ALPHAS}, (
        "Incomplete calibration matrix"
    )
    outcomes = read(root, "outcomes.json")
    counts = defaultdict(lambda: defaultdict(int))
    seen = set()
    for report in outcomes:
        sample, split, stress, method = (
            report["sample"],
            report["split"],
            report["stress"],
            report["method"],
        )
        alpha, persistence = report["alpha"], report["persistence"]
        row = registry[sample]
        assert sample in splits[split]
        identifier = (sample, split, stress, method, alpha, persistence)
        assert identifier not in seen, ("Duplicated outcome", identifier)
        seen.add(identifier)
        t, s = risk(split, stress, sample, method)
        theta = tau[(method, alpha)]
        assert theta is not None, (
            "Unavailable calibration must not yield evaluated performance"
        )
        _assert_close(
            report["threshold"], theta, ("Deployed threshold", identifier), atol=0.0
        )
        first = direct_first(t, s, theta, persistence)
        _assert_close(
            report["alarm_time"], first, ("First alarm from t0", identifier), atol=0.0
        )
        failure = row["verdict"] == "fail"
        onset = row.get("onset")
        timely = bool(
            failure and first is not None and onset <= first <= onset + 1 + TOLERANCE
        )
        premature = bool(failure and first is not None and first < onset)
        late = bool(failure and first is not None and first > onset + 1 + TOLERANCE)
        missed = bool(failure and first is None)
        clean = bool(not failure and first is not None)
        for field, value in [
            ("timely", timely),
            ("premature", premature),
            ("late", late),
            ("missed", missed),
            ("clean_alarm", clean),
        ]:
            assert report[field] == value, ("Outcome class", identifier, field)
        expected_status = (
            "timely"
            if timely
            else "premature"
            if premature
            else "late"
            if late
            else "missed"
            if failure
            else "clean_alarm"
            if clean
            else "clean_quiet"
        )
        assert report["status"] == expected_status, ("Outcome status", identifier)
        assert int(timely) + int(premature) + int(late) + int(missed) == int(failure)
        if report["delay"] is not None:
            _assert_close(
                report["delay"], first - onset, ("Conditional delay", identifier)
            )
        assert bool(report["observable_window"]) == bool(
            not failure or onset + 1 <= report["exposure"] + TOLERANCE
        ), ("Censoring", identifier)
        assert 0 <= report["exposure"] <= row["duration"] + TOLERANCE, (
            "Exposure beyond raw recording",
            identifier,
        )
        group = (split, stress, method, alpha, persistence)
        counts[group]["failures" if failure else "successes"] += 1
        for field, value in [
            ("timely", timely),
            ("premature", premature),
            ("late", late),
            ("missed", missed),
            ("clean_alarm", clean),
        ]:
            counts[group][field] += int(value)
        counts[group]["clean_exposure"] += report["exposure"] if not failure else 0
    expected_outcomes = {
        (sample, "evaluation", stress, method, alpha, persistence)
        for sample in splits["evaluation"]
        for stress in ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
        for method in METHODS
        for alpha in ALPHAS
        for persistence in (0.0, 0.1, 0.2)
    }
    assert seen == expected_outcomes, (
        "Fixed evaluation matrix has omitted or extra cells"
    )
    # Exposure equality must hold across methods/alphas/persistence variants.
    exposures = defaultdict(set)
    for row in outcomes:
        exposures[(row["sample"], row["split"], row["stress"])].add(row["exposure"])
    assert all(len(values) == 1 for values in exposures.values()), (
        "Unequal opportunity/exposure across compared methods"
    )
    development = audit_development_contrasts(root, registry, splits, risk)
    seeds = audit_seed_sensitivity(root, registry, splits, risk)
    source = audit_source_role(root, registry, splits)
    paired = audit_pairing(root, registry, outcomes)
    seal = audit_seal(root)
    result = {
        "status": "PASS",
        "scope": "Independent scalar first alarms, persistent calibration populations, split IDs/task separation, all outcome indicators, censoring, common exposure and source-role logits; no model/scorer import",
        "native_array_hashes_checked": native_hash_checks,
        "risk_files_checked": len(cache),
        "threshold_cells": len(tau),
        "outcome_rows": len(outcomes),
        "source_role": source,
        "development_contrasts": development,
        "seed_sensitivity": seeds,
        "packet_audit": packet_audit,
        "paired_effects": paired,
        "frozen_seal": seal,
        "outcomes_sha256": sha(root / "outcomes.json"),
        "thresholds_sha256": sha(root / "thresholds.json"),
        "independent_counts": [
            {
                "split": key[0],
                "stress": key[1],
                "method": key[2],
                "alpha": key[3],
                "persistence": key[4],
                **dict(value),
            }
            for key, value in sorted(counts.items())
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    result = audit(root)
    (root / "independent_numerical_audit.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "risk_files_checked",
                    "threshold_cells",
                    "outcome_rows",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
