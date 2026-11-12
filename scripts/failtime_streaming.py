"""Packet-only B4/MCSFA replay with annotations confined to offline examples."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from pydantic import BaseModel, ConfigDict, Field

from dual_rec.failtime.models import GRU32


class RuntimePacket(BaseModel):
    """Only currently received robot observations and the known robot stratum."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)
    time: float = Field(ge=0)
    eef: list[float] = Field(min_length=16, max_length=16)
    robot: str = Field(min_length=1)


class StreamingAlarm:
    """Constant threshold, one latched first alarm, and state carried from t=0."""

    def __init__(
        self, method: str, fits: Any, threshold: float | None, persistence: float = 0.1
    ):
        if method not in ("B4", "MCSFA"):
            raise ValueError("Only the frozen B4 and MCSFA models are supported")
        if persistence < 0 or not np.isfinite(persistence):
            raise ValueError("Finite nonnegative persistence required")
        if threshold is not None and not np.isfinite(threshold):
            raise ValueError("Deployable threshold must be finite or unavailable")
        self.method = method
        self.fits = fits
        self.threshold = threshold
        self.persistence = persistence
        self.previous = None
        self.beginning = None
        self.latched = False
        self.cusum = 0.0
        self.networks = []
        self.hidden = []
        if method == "B4":
            if not fits:
                raise ValueError("An ensemble must contain at least one frozen fit")
            for fit in fits:
                model = GRU32(fit["channels"]).eval()
                model.load_state_dict(fit["state_dict"])
                self.networks.append(model)
                self.hidden.append(None)

    def update(self, packet: RuntimePacket) -> dict[str, Any]:
        started = time.perf_counter()
        value = np.asarray(packet.eef, dtype=np.float64)
        if self.previous is not None:
            if packet.time <= self.previous.time:
                raise ValueError("Packet decision times must strictly increase")
            if packet.robot != self.previous.robot:
                raise ValueError("Robot stratum cannot change during an episode")
            difference = value - np.asarray(self.previous.eef, dtype=np.float64)
            derivative = difference / (packet.time - self.previous.time)
        else:
            difference = np.zeros(16)
            derivative = np.zeros(16)
        features = np.r_[value, derivative]
        explanation: dict[str, Any] = {
            "decision_grid_motion_norm": float(
                np.linalg.norm(derivative[[0, 1, 2, 8, 9, 10]])
            ),
            "initial_derivative_zero": self.previous is None,
        }
        if self.method == "B4":
            scores = []
            with torch.no_grad():
                for i, (fit, model) in enumerate(
                    zip(self.fits, self.networks, strict=True)
                ):
                    normalized = np.clip(
                        (features - fit["scaler"]["mean"]) / fit["scaler"]["std"],
                        -10,
                        10,
                    )
                    tensor = torch.as_tensor(normalized, dtype=torch.float32)[
                        None, None
                    ]
                    evidence, self.hidden[i] = model.gru(tensor, self.hidden[i])
                    scores.append(
                        float(torch.sigmoid(model.failure(evidence))[0, 0, 0])
                    )
            risk = float(np.mean(scores))
            explanation["per_seed_scores"] = scores
        else:
            nominal = self.fits["robots"].get(packet.robot)
            if nominal is None:
                risk = np.nan
                explanation.update(
                    mode=None, global_backoff=True, missing_robot_nominal=True
                )
            else:
                steps = np.array(
                    [np.sum(difference[:3] ** 2), np.sum(difference[8:11] ** 2)]
                )
                signs = np.sign(difference[[7, 15]])
                arm = ((signs + 1) * 2 + (steps > nominal["motion_floor"])).astype(int)
                mode = int(arm[0] * 6 + arm[1])
                supported = mode in nominal["modes"]
                distribution = (
                    nominal["modes"][mode] if supported else nominal["global"]
                )
                residual = np.clip(
                    (derivative - distribution["mean"]) / distribution["std"], -10, 10
                )
                evidence = float(np.mean(residual**2))
                increment = evidence / max(distribution["drift"], 1e-6) - 1.0
                self.cusum = max(0.0, self.cusum + increment)
                risk = self.cusum
                explanation.update(
                    mode=mode,
                    global_backoff=not supported,
                    standardized_residual_energy=evidence,
                    nominal_drift=distribution["drift"],
                    increment=increment,
                    cusum_state=self.cusum,
                )
        if self.threshold is None or not np.isfinite(risk) or risk < self.threshold:
            self.beginning = None
        elif self.beginning is None:
            self.beginning = packet.time
        duration = 0.0 if self.beginning is None else packet.time - self.beginning
        first = (
            self.beginning is not None
            and duration >= self.persistence - 1e-7
            and not self.latched
        )
        self.latched |= first
        self.previous = packet
        return {
            "time": packet.time,
            "risk": float(risk) if np.isfinite(risk) else None,
            "threshold": self.threshold,
            "first_alarm": bool(first),
            "alarm_latched": bool(self.latched),
            "persistence_seconds": duration,
            "abstention": self.threshold is None or not np.isfinite(risk),
            "explanation": explanation,
            "inference_seconds": time.perf_counter() - started,
        }


def read(root, name):
    return json.loads((root / name).read_text())


def load_runtime(root: Path, method: str) -> StreamingAlarm:
    """Only calibration-only thresholds bound by the pre-evaluation seal load."""
    seal = read(root, "models_source_seal.json")
    if not seal.get("scope", "").startswith(
        "Frozen development models and matched calibration"
    ):
        raise ValueError("Runtime requires a frozen development/calibration seal")
    threshold_file = root / "thresholds.json"
    expected = seal["sha256"].get("thresholds.json")
    if expected != hashlib.sha256(threshold_file.read_bytes()).hexdigest():
        raise ValueError("Calibration thresholds changed after the seal")
    settings = read(root, "thresholds.json")
    setting = next(r for r in settings if r["method"] == method and r["alpha"] == 0.1)
    if setting.get("scope") != "calibration_only":
        raise ValueError("Hindsight or evaluation thresholds cannot be deployed")
    allowed = set(seal["calibration_ids"])
    for population in setting["populations"].values():
        if not {r["sample"] for r in population} <= allowed:
            raise ValueError("A threshold population contains a noncalibration episode")

    def fit(name):
        path = root / "models" / (name + ".pt")
        if hashlib.sha256(path.read_bytes()).hexdigest() != seal["sha256"].get(
            str(path.relative_to(root))
        ):
            raise ValueError("Frozen checkpoint changed")
        return torch.load(path, map_location="cpu", weights_only=False)["fit"]

    bundle = (
        [fit(f"B4_seed{seed}") for seed in (11, 23, 37)]
        if method == "B4"
        else fit("nominal")
    )
    return StreamingAlarm(method, bundle, setting["threshold"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Completed campaign is sealed")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    outcomes = [
        r
        for r in read(root, "outcomes.json")
        if r["stress"] == "clean" and r["alpha"] == 0.1 and r["persistence"] == 0.1
    ]
    cohort = {r["sample"]: r for r in read(root, "cohort_qualification.json")}
    examples = []
    checks = []
    destination = root / "streaming"
    destination.mkdir(exist_ok=True)
    for method in ("B4", "MCSFA"):
        rows = [r for r in outcomes if r["method"] == method]
        selected = {}
        for category in (
            "timely",
            "premature",
            "late",
            "missed",
            "clean_alarm",
            "clean_quiet",
        ):
            candidates = sorted(
                [r for r in rows if r["status"] == category],
                key=lambda r: hashlib.sha256(r["sample"].encode()).hexdigest(),
            )
            if not candidates:
                examples.append(
                    {"method": method, "category": category, "available": False}
                )
                continue
            row = candidates[0]
            selected[row["sample"]] = row
            examples.append(
                {
                    "method": method,
                    "category": category,
                    "available": True,
                    "sample": row["sample"],
                    "raw_annotation": {
                        k: cohort[row["sample"]].get(k)
                        for k in ("verdict", "onset", "type", "reason")
                    },
                    "provenance": {
                        k: cohort[row["sample"]].get(k)
                        for k in ("task_id", "robot", "hdf5", "sha256", "arrays")
                    },
                    "offline_outcome": row,
                    "trace": str(
                        (
                            destination / (method + "_" + row["sample"] + ".jsonl")
                        ).relative_to(root)
                    ),
                }
            )
        for sample, outcome in sorted(selected.items()):
            with np.load(
                root / "risks/evaluation/clean" / (sample + ".npz"), allow_pickle=False
            ) as stream:
                times = stream["time"]
                eef = stream["eef"]
                expected = stream[method]
                source_time = stream["source_time"]
            monitor = load_runtime(root, method)
            traces = []
            for i, (now, pose) in enumerate(zip(times, eef, strict=True)):
                trace = monitor.update(
                    RuntimePacket(
                        time=float(now),
                        eef=pose.tolist(),
                        robot=cohort[sample]["robot"],
                    )
                )
                trace["offline_source_age_seconds"] = (
                    float(now - source_time[i]) if np.isfinite(source_time[i]) else None
                )
                traces.append(trace)
            actual = np.array(
                [r["risk"] if r["risk"] is not None else np.nan for r in traces]
            )
            finite = np.isfinite(expected) & np.isfinite(actual)
            maximum = (
                float(np.max(np.abs(actual[finite] - expected[finite])))
                if finite.any()
                else 0.0
            )
            finite_equal = bool(
                np.array_equal(np.isfinite(actual), np.isfinite(expected))
            )
            first = next((r["time"] for r in traces if r["first_alarm"]), None)
            passed = finite_equal and maximum <= 1e-6 and first == outcome["alarm_time"]
            with (destination / (method + "_" + sample + ".jsonl")).open("w") as handle:
                for trace in traces:
                    handle.write(json.dumps(trace, allow_nan=False) + "\n")
            checks.append(
                {
                    "method": method,
                    "sample": sample,
                    "status": "PASS" if passed else "FAIL",
                    "maximum_absolute_batch_stream_score_difference": maximum,
                    "finite_masks_identical": finite_equal,
                    "batch_alarm": outcome["alarm_time"],
                    "stream_alarm": first,
                    "status_from_offline_labels": outcome["status"],
                    "mean_inference_ms": 1000
                    * float(np.mean([r["inference_seconds"] for r in traces])),
                }
            )
    uncertain = [
        {
            "sample": r["sample"],
            "split": "evaluation"
            if r["sample"] in read(root, "registration.json")["splits"]["evaluation"]
            else "non-evaluation",
            "onset": r.get("onset"),
            "observed_duration": r["duration"],
            "reason": "Released onset extends beyond observed causal history; censored, not physically adjudicated",
            "provenance": {
                k: r.get(k) for k in ("task_id", "robot", "hdf5", "sha256", "arrays")
            },
        }
        for r in cohort.values()
        if r.get("onset_within_observed") is False
    ]
    for example in uncertain:
        paths = [
            root / "risks" / split / "clean" / (example["sample"] + ".npz")
            for split in ("train", "calibration", "evaluation")
        ]
        available = next((path for path in paths if path.exists()), None)
        example["saved_model_trace"] = {
            "path": str(available.relative_to(root)) if available else None,
            "arrays": ["time", "eef", "B4", "MCSFA", "mode", "mode_backoff"],
            "scope": "Saved causal risk history for offline censored-annotation review; no relabeling or threshold fitting",
        }
    report = {
        "status": "PASS" if all(r["status"] == "PASS" for r in checks) else "FAIL",
        "scope": "Incremental recurrent B4 and mode/evidence/CUSUM MCSFA; no annotation enters packet API",
        "selection": "First SHA256(sample) in every available clean primary outcome category, deduplicated per method",
        "checks": checks,
        "examples": examples,
        "uncertain_annotation_examples": uncertain,
        "numeric_policy": "Score tolerance 1e-6; alarm equality exact; any boundary discrepancy is retained without retuning",
    }
    (root / "streaming_parity.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "examples": len(checks),
                "uncertain": len(uncertain),
                "maximum_score_difference": max(
                    (
                        r["maximum_absolute_batch_stream_score_difference"]
                        for r in checks
                    ),
                    default=0.0,
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
