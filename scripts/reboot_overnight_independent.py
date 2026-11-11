"""Independent scoring from saved arrays/labels; no detector or scorer imports."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def alarm(times, scores, threshold):
    streak = []
    for index in range(len(times)):
        if np.isfinite(scores[index]) and scores[index] >= threshold:
            streak.append(index)
            if times[index] - times[streak[0]] + 2e-6 >= 0.1:
                return float(times[index])
        else:
            streak = []
    return None


def capacity(times, scores):
    candidates = []
    for start in range(len(times)):
        end = start + 1
        while end < len(times) and times[end] - times[start] < 0.1 - 2e-6:
            end += 1
        if end < len(times) and np.isfinite(scores[start : end + 1]).all():
            candidates.append(float(min(scores[start : end + 1])))
    return max(candidates, default=-np.inf)


def raw_recordings(old, name):
    import pyarrow.parquet as pq

    pieces = defaultdict(list)
    for path in sorted((old / "projected" / name / "data").rglob("*.parquet")):
        table = pq.ParquetFile(path).read(
            columns=[
                "observation.state",
                "action",
                "timestamp",
                "frame_index",
                "episode_index",
            ]
        )
        for row in table.to_pylist():
            pieces[row["episode_index"]].append(row)
    result = {}
    for index, records in pieces.items():
        records.sort(key=lambda r: r["frame_index"])
        q = np.asarray([r["observation.state"] for r in records], dtype="<f4")
        a = np.asarray([r["action"] for r in records], dtype="<f4")
        t = np.asarray([r["timestamp"] for r in records], dtype="<f4")
        frames = np.asarray([r["frame_index"] for r in records])
        assert np.array_equal(frames, np.arange(len(frames)))
        signature = hashlib.sha256(q.tobytes() + a.tobytes() + t.tobytes()).hexdigest()
        result[index] = {
            "signature": signature,
            "q": q,
            "a": a,
            "t": t,
            "frames": frames,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    import pyarrow as pa

    pa.set_cpu_count(2)
    old = Path("results/reboot-phase/20261111T204459Z")
    registration = json.loads((root / "registration.json").read_text())
    entries = json.loads((root / "registry.json").read_text())
    rows = {r["group"]: r for r in entries if r["eligible"]}
    assert (
        len(rows) == 117 and sum(r["role"] == "recovery" for r in rows.values()) == 55
    )
    samples = raw_recordings(old, "sample_recovery-demonstration")
    recoveries = raw_recordings(old, "16mm-cylinder_recovery_install")
    references = raw_recordings(old, "16mm-cylinder_install")
    raw_labels = json.loads(
        (old / "data/sample_recovery-demonstration/meta/phase.json").read_text()
    )["episodes"]
    crosswalk = {}
    excluded = []
    for raw in raw_labels:
        episode = int(raw["episode_index"])
        source = samples[episode]
        matches = [
            i
            for i, target in recoveries.items()
            if target["signature"] == source["signature"]
        ]
        assert len(matches) == 1
        for key in ("q", "a", "t", "frames"):
            np.testing.assert_array_equal(source[key], recoveries[matches[0]][key])
        group = "recording:" + source["signature"]
        crosswalk[group] = source
        failure = raw["failure"]
        schema = (
            type(failure["originating_phase"]) is int
            and 1 <= failure["originating_phase"] <= 5
        )
        left, right = failure["induced_at_frame"], failure["recovery_started_at_frame"]
        eligible = schema and 0 <= left < right < len(source["t"])
        registered = next(r for r in entries if r.get("sample_episode") == episode)
        assert registered["group"] == group and registered["eligible"] == eligible
        assert (
            registered["raw_annotation"] == raw and registered["episode"] == matches[0]
        )
        if eligible:
            assert registered["onset"] == float(source["t"][left])
            assert registered["recovery"] == float(source["t"][right])
        else:
            excluded.append(episode)
    assert sorted(excluded) == [16, 26, 35, 37, 48]
    for target in references.values():
        crosswalk["recording:" + target["signature"]] = target
    for row in rows.values():
        if row["role"] == "reference":
            assert (
                row["group"] == "recording:" + references[row["episode"]]["signature"]
            )
    for role in ("reference", "recovery"):
        ordered = sorted(
            [r for r in rows.values() if r["role"] == role],
            key=lambda r: hashlib.sha256(
                ("reboot-overnight-v1:" + r["group"]).encode()
            ).hexdigest(),
        )
        assert all(r["fold"] == i % 5 for i, r in enumerate(ordered))
    for spec in registration["folds"]:
        k = spec["fold"]
        training = [r for r in rows.values() if r["fold"] not in (k, (k + 1) % 5)]
        assert set(spec["train"]) == {r["group"] for r in training}
        assert set(spec["evaluation"]) == {g for g, r in rows.items() if r["fold"] == k}
        assert set(spec["calibration"]) == {
            g for g, r in rows.items() if r["fold"] == (k + 1) % 5
        }
        horizon = min(
            30.0,
            *[
                np.percentile(
                    [
                        crosswalk[r["group"]]["t"][-1]
                        for r in training
                        if r["role"] == role
                    ],
                    5,
                )
                for role in ("reference", "recovery")
            ],
        )
        assert abs(horizon - spec["horizon"]) < 1e-10
        counts, initial, support = np.zeros((5, 5)), np.ones(5), np.zeros(5, dtype=int)
        for row in training:
            if row["role"] != "recovery":
                continue
            raw = crosswalk[row["group"]]
            indexes = raw["frames"][::3]
            times = raw["t"][::3]
            phase = np.full(len(indexes), -1)
            bounds = row["raw_annotation"]["phase_boundaries"]
            for state in range(5):
                chosen = (
                    (indexes >= bounds[f"tau_{state}"])
                    & (indexes < bounds[f"tau_{state + 1}"])
                    & (times < horizon)
                    & (times < row["recovery"])
                )
                phase[chosen] = state
                support[state] += chosen.sum()
            valid = phase[phase >= 0]
            initial[valid[0]] += 1
            for a, b in pairwise(phase):
                if a >= 0 and b >= 0:
                    counts[a, b] += 1
        allowed = (counts > 0) | np.eye(5, dtype=bool)
        matrix = np.where(allowed, counts + 1, 0)
        matrix /= matrix.sum(1, keepdims=True)
        for variant in ("Q", "QC"):
            saved = json.loads((root / f"fold{k}_{variant}_grammar.json").read_text())
            np.testing.assert_array_equal(saved["counts"], counts)
            np.testing.assert_allclose(saved["matrix"], matrix)
            np.testing.assert_allclose(saved["initial"], initial / initial.sum())
            np.testing.assert_array_equal(saved["support"], support)
    thresholds = json.loads((root / "thresholds.json").read_text())
    cache = {}

    def prediction(fold, variant, stress, split, group):
        path = (
            root
            / "predictions"
            / f"fold{fold}"
            / variant
            / stress
            / split
            / (group.split(":")[1] + ".npz")
        )
        if path not in cache:
            cache[path] = dict(np.load(path, allow_pickle=False))
            data = cache[path]
            native = crosswalk[group]
            q, a, t = (
                native["q"].astype(float),
                native["a"].astype(float),
                native["t"].astype(float),
            )
            drop = float(stress[4:]) if stress.startswith("drop") else 0
            ticks = round(float(stress[5:]) * 10) if stress.startswith("delay") else 0
            generator = np.random.default_rng(
                int(
                    hashlib.sha256(("sensor-v1:" + group).encode()).hexdigest()[:16], 16
                )
            )
            discarded = generator.random(len(data["time"])) < drop
            last, held = None, None
            expected = np.full_like(data["features"], np.nan)
            for j in range(len(data["time"])):
                packet = j - ticks
                if packet >= 0 and not discarded[packet]:
                    frame = packet * 3
                    v = (
                        np.zeros(14)
                        if last is None
                        else (q[frame] - q[last]) / (t[frame] - t[last])
                    )
                    target = q[0] if frame == 0 else a[frame - 1]
                    held = np.r_[q[frame], v, target - q[frame]]
                    last = frame
                assert data["source_frame"][j] == (-1 if last is None else last)
                if held is not None:
                    expected[j] = held[:28] if variant == "Q" else held
            np.testing.assert_allclose(
                data["features"], expected, atol=1e-12, equal_nan=True
            )
        return cache[path]

    for key, fit in thresholds.items():
        tokens = key.split(":")
        fold, variant, method = int(tokens[0]), tokens[1], tokens[2]
        refs = [
            r
            for r in rows.values()
            if r["role"] == "reference" and r["fold"] == (fold + 1) % 5
        ]
        capacities, alarms = [], 0
        for row in refs:
            data = prediction(fold, variant, "clean", "calibration", row["group"])
            scores = (
                data[method]
                if len(tokens) == 3
                else data[method + "_seeds"][(11, 23, 37).index(int(tokens[3]))]
            )
            capacities.append(capacity(data["time"], scores))
            alarms += alarm(data["time"], scores, fit["threshold"]) is not None
        expected = np.nextafter(
            sorted(capacities, reverse=True)[len(refs) // 10], np.inf
        )
        assert (
            expected == fit["threshold"]
            and alarms == fit["reference_alarms"] <= len(refs) // 10
        )
    outcomes = json.loads((root / "outcomes.json").read_text())
    seed_outcomes = json.loads((root / "seed_outcomes.json").read_text())
    checked = 0
    for result in outcomes + seed_outcomes:
        row = rows[result["group"]]
        data = prediction(
            row["fold"], result["variant"], result["stress"], "evaluation", row["group"]
        )
        key = f"{row['fold']}:{result['variant']}:{result['method']}"
        if "seed" in result:
            key += f":{result['seed']}"
        threshold = thresholds[key]["threshold"]
        scores = (
            data[result["method"]]
            if "seed" not in result
            else data[result["method"] + "_seeds"][(11, 23, 37).index(result["seed"])]
        )
        first = alarm(data["time"], scores, threshold)
        assert first == result["alarm_time"]
        horizon = registration["folds"][row["fold"]]["horizon"]
        assert np.all(data["time"] < horizon)
        native = crosswalk[row["group"]]
        np.testing.assert_array_equal(data["time"], native["t"][data["native_frame"]])
        if result["role"] == "reference":
            assert result["reference_alarm"] == (first is not None)
            assert result["status"] == (
                "reference_alarm" if first is not None else "reference_quiet"
            )
        else:
            delta = result["boundary_delta"]
            high = min(row["recovery"] - delta, horizon, row["frames"] / 30 - 1 / 30)
            assert result["evaluable"] == (row["onset"] + delta < high)
            timely = (
                first is not None
                and row["onset"] + delta <= first < high
                and result["evaluable"]
            )
            assert result["timely"] == timely
            assert result["premature"] == (first is not None and first < row["onset"])
            if not result["evaluable"]:
                status = "unobservable_target"
            elif first is None:
                status = "no_alarm"
            elif timely:
                status = "timely"
            elif (
                delta > 0
                and min(abs(first - row["onset"]), abs(first - row["recovery"]))
                <= delta
            ):
                status = "timing_ambiguous"
            elif first < row["onset"] + delta:
                status = "premature"
            else:
                status = "late"
            assert result["status"] == status
            if timely:
                assert abs(result["delay"] - (first - row["onset"])) < 1e-10
                assert abs(result["lead"] - (row["recovery"] - first)) < 1e-10
            selected = data["time"] >= row["onset"]
            reset = alarm(data["time"][selected], scores[selected], threshold)
            assert result["optimistic_post_onset_reset"] == (
                reset is not None and reset < min(row["recovery"], horizon)
            )
        if result["method"] in ("B3", "P0", "P1", "P2"):
            np.testing.assert_allclose(
                data[result["method"]],
                data[result["method"] + "_seeds"].mean(0),
                atol=1e-14,
                equal_nan=True,
            )
        checked += 1
    # Independent bootstrap traversal and random draws in exactly registered order.
    reported = json.loads((root / "paired_effects.json").read_text())
    rng = np.random.default_rng(20261111)
    for effect in reported:
        a, b = effect["contrast"].split("-")
        left, right = {}, {}
        for r in outcomes:
            if (
                r["variant"] == effect["variant"]
                and r["stress"] == "clean"
                and r["boundary_delta"] == effect["delta"]
            ):
                if r["method"] == a:
                    left[r["group"]] = r
                elif r["method"] == b:
                    right[r["group"]] = r
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
                    metric != "timely" or left[g]["evaluable"] and right[g]["evaluable"]
                )
            )
            d = np.asarray(
                [int(left[g][metric]) - int(right[g][metric]) for g in common],
                dtype=float,
            )
            samples = rng.integers(0, len(d), (2000, len(d)))
            intervals = np.percentile(d[samples].mean(1), [2.5, 97.5])
            saved = effect["effects"][metric]
            assert (
                len(d) == saved["recordings"]
                and abs(d.mean() - saved["difference"]) < 1e-12
            )
            np.testing.assert_allclose(intervals, saved["ci95"], atol=1e-12)
    phase_results = json.loads((root / "phase_results.json").read_text())
    for result in phase_results:
        row = rows[result["group"]]
        data = prediction(
            row["fold"], result["variant"], "clean", "evaluation", row["group"]
        )
        truth = np.full(len(data["time"]), -1)
        bounds = row["raw_annotation"]["phase_boundaries"]
        for state in range(5):
            valid = (
                (data["native_frame"] >= bounds[f"tau_{state}"])
                & (data["native_frame"] < bounds[f"tau_{state + 1}"])
                & (data["time"] < row["recovery"])
            )
            truth[valid] = state
        selected = truth >= 0
        labels = np.argmax(data["phase_" + result["method"]], axis=1)
        correct = int(np.sum(labels[selected] == truth[selected]))
        assert result["frames"] == int(selected.sum()) and result["correct"] == correct
        assert abs(result["episode_accuracy"] - correct / selected.sum()) < 1e-12
        allowed = json.loads(
            (root / f"fold{row['fold']}_{result['variant']}_grammar.json").read_text()
        )["allowed"]
        violations = sum(not allowed[int(a)][int(b)] for a, b in pairwise(labels))
        assert result["marginal_argmax_graph_violations_full_stream"] == violations
    mappings = json.loads((root / "permutation_mapping.json").read_text())
    for item in mappings:
        k = item["fold"]
        population = sorted(
            g
            for g, r in rows.items()
            if r["role"] == "recovery" and r["fold"] not in (k, (k + 1) % 5)
        )
        assert item["training_donors"] == {
            g: population[(i + 1) % len(population)] for i, g in enumerate(population)
        }
    development = json.loads((root / "development_sanity.json").read_text())
    for result in development:
        row = rows[result["group"]]
        k = (row["fold"] - 1) % 5
        assert result["scope"] == "development_only"
        if result["method"] == "B2_training_interval_permutation":
            data = dict(
                np.load(
                    root
                    / "development"
                    / f"fold{k}_{result['variant']}_{result['group'].split(':')[1]}.npz"
                )
            )
            scores = data["scores"]
        else:
            data = prediction(
                k, result["variant"], "clean", "calibration", row["group"]
            )
            scores = data["B2"]
        first = alarm(data["time"], scores, result["threshold"])
        assert first == result["alarm_time"]
        if row["role"] == "recovery":
            assert result["timely"] == (
                first is not None and row["onset"] <= first < row["recovery"]
            )
    # Validate all source-consumption and main-prediction hashes after scoring.
    consumed = {}
    for name in ("consumed_inputs.json", "external_inputs.json"):
        consumed.update(json.loads((root / name).read_text()))
    for name, value in consumed.items():
        assert digest(Path(name)) == value
    main_seal = json.loads((root / "main_prediction_seal.json").read_text())
    for name, value in main_seal["sha256"].items():
        assert digest(root / name) == value
    external_cache = {}
    external_outcomes = json.loads((root / "external_outcomes.json").read_text())
    external_ids = {
        r["group"] for r in json.loads((root / "external_registry.json").read_text())
    }
    assert len(external_ids) == 306
    for result in external_outcomes:
        path = (
            root
            / "external_predictions"
            / f"fold{result['fold']}"
            / result["variant"]
            / (result["group"].split(":")[1] + ".npz")
        )
        if path not in external_cache:
            external_cache[path] = dict(np.load(path, allow_pickle=False))
        data = external_cache[path]
        threshold = thresholds[
            f"{result['fold']}:{result['variant']}:{result['method']}"
        ]["threshold"]
        when = alarm(data["time"], data[result["method"]], threshold)
        assert result["alarm_time"] == when and result["alarm"] == (when is not None)
        assert result["exposed"] == bool(
            np.isfinite(capacity(data["time"], data[result["method"]]))
        )
    import torch

    checkpoints = list((root / "models").glob("*.pt"))
    neural = 0
    for path in checkpoints:
        value = torch.load(path, map_location="cpu", weights_only=False)
        assert value["registration_sha256"] == digest(root / "registration.json")
        if value["kind"] == "neural":
            neural += 1
            assert value["epochs"] == len(value["loss"]) == 30 and value["seed"] in (
                11,
                23,
                37,
            )
            assert np.isfinite(value["loss"]).all() and value["positive_weight"] <= 10
    assert len(checkpoints) == 95 and neural == 60
    result = {
        "status": "PASS",
        "scope": "Independent raw joins, native timing, folds/horizons/train-only grammar, conservative thresholds, first alarms, boundary/censoring support, seed ensembles and paired bootstrap from saved predictions; no detector/scorer imported",
        "eligible_unique_recordings": len(rows),
        "sample_alias_joins": len(raw_labels),
        "excluded_sample_ids": excluded,
        "outcome_rows_checked": checked,
        "thresholds_checked": len(thresholds),
        "paired_contrasts_checked": len(reported),
        "sensor_alignment_prediction_files": len(cache),
        "external_outcome_rows_checked": len(external_outcomes),
        "phase_result_rows_checked": len(phase_results),
        "development_result_rows_checked": len(development),
        "unique_external_recordings": len(external_ids),
        "consumed_input_hashes_checked": len(consumed),
        "neural_checkpoints": neural,
        "total_checkpoints": len(checkpoints),
        "outcomes_sha256": digest(root / "outcomes.json"),
        "paired_effects_sha256": digest(root / "paired_effects.json"),
    }
    (root / "independent_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
