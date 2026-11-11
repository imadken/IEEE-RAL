"""Development permutation control and limited nominal-reference shift check."""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from dual_rec.reboot.audit import episode_arrays, physical_hash
from dual_rec.reboot.overnight_data import (
    EXTERNAL,
    OLD,
    save_json,
    sensor_features,
    sha,
    verified_inputs,
)
from dual_rec.reboot.overnight_experiment import models_for, predict_bundle
from dual_rec.reboot.overnight_metrics import (
    METHODS,
    calibrate,
    outcome,
    persistent_capacity,
)


def development(root):
    registry = [
        r for r in json.loads((root / "registry.json").read_text()) if r["eligible"]
    ]
    thresholds = json.loads((root / "thresholds.json").read_text())
    results, mappings = [], []
    for fold in range(5):
        train = sorted(
            [
                r
                for r in registry
                if r["role"] == "recovery" and r["fold"] not in (fold, (fold + 1) % 5)
            ],
            key=lambda r: r["group"],
        )
        mappings.append(
            {
                "fold": fold,
                "training_donors": {
                    r["group"]: train[(i + 1) % len(train)]["group"]
                    for i, r in enumerate(train)
                },
            }
        )
        calibration = [r for r in registry if r["fold"] == (fold + 1) % 5]
        for variant in ("Q", "QC"):

            def load(row, fold=fold, variant=variant):
                return dict(
                    np.load(
                        root
                        / "development"
                        / f"fold{fold}_{variant}_{row['group'].split(':')[1]}.npz"
                    )
                )

            records = [load(r) for r in calibration if r["role"] == "reference"]
            fit = calibrate([(d["time"], d["scores"]) for d in records])
            horizon = json.loads((root / "registration.json").read_text())["folds"][
                fold
            ]["horizon"]
            for row in calibration:
                data = load(row)
                result = outcome(
                    row, data["time"], data["scores"], fit["threshold"], horizon
                )
                result.update(
                    variant=variant,
                    method="B2_training_interval_permutation",
                    scope="development_only",
                )
                results.append(result)
                main = dict(
                    np.load(
                        root
                        / "predictions"
                        / f"fold{fold}"
                        / variant
                        / "clean/calibration"
                        / (row["group"].split(":")[1] + ".npz")
                    )
                )
                result = outcome(
                    row,
                    main["time"],
                    main["B2"],
                    thresholds[f"{fold}:{variant}:B2"]["threshold"],
                    horizon,
                )
                result.update(
                    variant=variant,
                    method="B2_original_training_labels",
                    scope="development_only",
                )
                results.append(result)
    save_json(root / "permutation_mapping.json", mappings)
    save_json(root / "development_sanity.json", results)
    print(
        json.dumps(
            {
                "development_rows": len(results),
                "scope": "No evaluation labels used; not the primary OOF comparison",
            }
        )
    )


def external(root):
    main_seal = json.loads((root / "main_prediction_seal.json").read_text())
    for name, value in main_seal["sha256"].items():
        if sha(root / name) != value:
            raise ValueError("Frozen main models/predictions changed")
    verified_inputs(root, external=True)
    source_info = json.loads(
        (OLD / "data/16mm-cylinder_install/meta/info.json").read_text()
    )
    thresholds = json.loads((root / "thresholds.json").read_text())
    registration = json.loads((root / "registration.json").read_text())
    compatibility, rows, data_by_group = [], [], {}
    for name in EXTERNAL:
        info = json.loads((OLD / "data" / name / "meta/info.json").read_text())
        checks = {
            "robot": info["robot_type"] == source_info["robot_type"],
            "frequency": info["fps"] == source_info["fps"] == 30,
        }
        for channel in ("action", "observation.state"):
            checks[channel] = all(
                info["features"][channel][key] == source_info["features"][channel][key]
                for key in ("names", "shape", "dtype")
            )
        compatibility.append(
            {
                "repository": name,
                "checks": checks,
                "compatible": all(checks.values()),
                "unit_scope": "Shared declared robot/absolute joint-and-gripper .pos export, no rescaling or remapping; physical SI calibration is not independently certified. Native-export shift diagnostic only.",
            }
        )
        if not all(checks.values()):
            continue
        for episode, arrays in episode_arrays(OLD, name).items():
            group = "recording:" + physical_hash(arrays)
            rows.append(
                {
                    "group": group,
                    "repository": name,
                    "episode": episode,
                    "frames": len(arrays["timestamp"]),
                }
            )
            data_by_group[group] = arrays
    save_json(root / "external_compatibility.json", compatibility)
    save_json(root / "external_registry.json", rows)
    outcomes = []
    for fold in range(5):
        horizon = registration["folds"][fold]["horizon"]
        for variant in ("Q", "QC"):
            bundle = models_for(root, fold, variant)
            directory = root / "external_predictions" / f"fold{fold}" / variant
            directory.mkdir(parents=True, exist_ok=True)
            for row in rows:
                path = directory / (row["group"].split(":")[1] + ".npz")
                if path.exists():
                    prediction = dict(np.load(path))
                else:
                    series = sensor_features(
                        data_by_group[row["group"]], row["group"], variant=variant
                    )
                    series = {
                        key: value[series["time"] < horizon]
                        for key, value in series.items()
                    }
                    started = time.monotonic()
                    raw = predict_bundle(bundle, series)
                    elapsed = time.monotonic() - started
                    prediction = {
                        "time": series["time"],
                        "inference_seconds": np.array(elapsed),
                        **{m: raw[m] for m in METHODS if m in raw},
                    }
                    np.savez_compressed(path, **prediction)
                for method in METHODS:
                    if method not in prediction:
                        continue
                    threshold = thresholds[f"{fold}:{variant}:{method}"]["threshold"]
                    from dual_rec.reboot.overnight_metrics import first_alarm

                    alarm = first_alarm(
                        prediction["time"], prediction[method], threshold
                    )
                    finite = prediction[method][np.isfinite(prediction[method])]
                    outcomes.append(
                        {
                            "group": row["group"],
                            "repository": row["repository"],
                            "fold": fold,
                            "variant": variant,
                            "method": method,
                            "alarm": alarm is not None,
                            "alarm_time": alarm,
                            "exposed": bool(
                                np.isfinite(
                                    persistent_capacity(
                                        prediction["time"], prediction[method]
                                    )
                                )
                            ),
                            "exposure_seconds": min(
                                horizon,
                                float(data_by_group[row["group"]]["timestamp"][-1]),
                            ),
                            "score_mean": float(finite.mean()) if len(finite) else None,
                            "score_p95": float(np.percentile(finite, 95))
                            if len(finite)
                            else None,
                            "bundle_inference_seconds": float(
                                prediction["inference_seconds"]
                            ),
                            "scored_frames": len(prediction["time"]),
                        }
                    )
    groups = defaultdict(list)
    for row in outcomes:
        groups[(row["repository"], row["variant"], row["method"], row["fold"])].append(
            row
        )
    summary = [
        {
            "repository": key[0],
            "variant": key[1],
            "method": key[2],
            "fold": key[3],
            "alarms": sum(r["alarm"] for r in group),
            "exposed": sum(r["exposed"] for r in group),
            "recordings": len(group),
            "exposure_seconds": sum(r["exposure_seconds"] for r in group),
            "mean_score": float(
                np.mean([r["score_mean"] for r in group if r["score_mean"] is not None])
            ),
        }
        for key, group in groups.items()
    ]
    save_json(root / "external_outcomes.json", outcomes)
    save_json(root / "external_summary.json", summary)
    print(
        json.dumps(
            {
                "unique_external_recordings": len(data_by_group),
                "per_fold_recordings": len(rows),
                "repeated_analysis_rows": len(outcomes),
                "interpretation": "Native nominal-reference shift only; no target failure labels or sensitivity",
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("development", "external"), required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    import pyarrow as pa

    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    (development if args.stage == "development" else external)(args.root)


if __name__ == "__main__":
    main()
