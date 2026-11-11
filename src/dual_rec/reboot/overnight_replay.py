"""Incremental frozen-model replay; annotations live only in the evaluator."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from dual_rec.reboot.overnight_data import SensorPacket, arrays_for, save_json, sha
from dual_rec.reboot.overnight_experiment import models_for
from dual_rec.reboot.overnight_models import SmallGRU, filter_step, scaled


class StreamingDetector:
    """Accept only currently received robot packets; reset at recording start."""

    def __init__(self, bundle, threshold, *, method="P1", variant="Q"):
        self.method, self.variant, self.threshold = method, variant, threshold
        family = "B3" if method == "B3" else "P"
        self.fits, self.networks = bundle[family], []
        for fit in self.fits:
            network = SmallGRU(fit["channels"], phase=fit["phase"]).eval()
            network.load_state_dict(fit["state_dict"])
            self.networks.append(network)
        self.grammar = bundle.get("grammar")
        self.hidden = [None] * len(self.fits)
        self.alpha = (
            [self.grammar["initial"].copy() for _ in self.fits] if self.grammar else []
        )
        self.smooth = [None] * len(self.fits)
        self.previous = None
        self.beginning = None
        self.alarmed = False

    def update(self, packet: SensorPacket):
        started = time.perf_counter()
        q = np.asarray(packet.qpos)
        if packet.source_time > packet.time + 2e-6:
            raise ValueError("Observation has not arrived yet")
        if self.previous is None:
            velocity = np.zeros(14)
        else:
            dt = packet.source_time - self.previous.source_time
            if dt <= 0 or packet.time <= self.previous.time:
                raise ValueError(
                    "Replay requires increasing received measurement times"
                )
            velocity = (q - np.asarray(self.previous.qpos)) / dt
        error = np.asarray(packet.previous_target) - q
        features = np.r_[q, velocity, error]
        if self.variant == "Q":
            features = features[:28]
        scores, emissions, states, predecessor, unfiltered, smoothed = (
            [],
            [],
            [],
            [],
            [],
            [],
        )
        unresolved = 0
        with torch.no_grad():
            for i, (fit, model) in enumerate(
                zip(self.fits, self.networks, strict=True)
            ):
                value = torch.as_tensor(
                    scaled(features[None], fit["scaler"]), dtype=torch.float32
                )[None]
                raw, phase, failure, self.hidden[i] = model(value, self.hidden[i])
                if phase is None:
                    scores.append(float(raw[0, 0]))
                    continue
                e = torch.softmax(phase[0, 0], dim=0).numpy()
                heads = torch.sigmoid(failure[0, 0]).numpy()
                predecessor.append(self.alpha[i] @ self.grammar["matrix"])
                self.alpha[i], fallback = filter_step(
                    e, self.alpha[i], self.grammar["matrix"]
                )
                unresolved += int(fallback)
                amount = (
                    1
                    if self.previous is None
                    else 1 - np.exp(-(packet.time - self.previous.time) / 0.3)
                )
                self.smooth[i] = (
                    e.copy()
                    if self.smooth[i] is None
                    else amount * e + (1 - amount) * self.smooth[i]
                )
                weights = e if self.method == "P0" or fallback else self.alpha[i]
                if self.method == "P2":
                    weights = self.smooth[i]
                scores.append(float(weights @ heads))
                unfiltered.append(float(e @ heads))
                smoothed.append(float(self.smooth[i] @ heads))
                emissions.append(e)
                states.append(weights)
        risk = float(np.mean(scores))
        if risk >= self.threshold:
            if self.beginning is None:
                self.beginning = packet.time
        else:
            self.beginning = None
        duration = 0 if self.beginning is None else packet.time - self.beginning
        first = (
            not self.alarmed and self.beginning is not None and duration >= 0.1 - 2e-6
        )
        self.alarmed |= first
        phase = np.mean(states, axis=0) if states else None
        trace = {
            "motion_norm": float(np.linalg.norm(velocity)),
            "prior_target_error_norm": float(np.linalg.norm(error)),
            "phase_probabilities": phase.tolist() if phase is not None else None,
            "predicted_phase": int(phase.argmax()) + 1 if phase is not None else None,
            "emission_probabilities": np.mean(emissions, axis=0).tolist()
            if emissions
            else None,
            "allowed_predecessor_mass": np.mean(predecessor, axis=0).tolist()
            if predecessor
            else None,
            "unfiltered_score": float(np.mean(unfiltered)) if unfiltered else risk,
            "ordinary_smoothed_score": float(np.mean(smoothed)) if smoothed else None,
            "filter_score_change": risk - float(np.mean(unfiltered))
            if unfiltered
            else 0,
            "phase_unresolved_seed_count": unresolved,
            "phase_training_support_frames": self.grammar["support"].tolist()
            if self.grammar
            else None,
            "predicted_phase_has_training_support": bool(
                self.grammar["support"][phase.argmax()] > 0
            )
            if phase is not None
            else None,
            "persistence_seconds": duration,
            "threshold": self.threshold,
        }
        self.previous = packet
        return {
            "timestamp": packet.time,
            "source_timestamp": packet.source_time,
            "risk": risk,
            "first_alarm": bool(first),
            "alarm_latched": bool(self.alarmed),
            "explanation": trace,
            "inference_seconds": time.perf_counter() - started,
        }


def replay(root, group, *, variant="Q", method="P1"):
    registry = json.loads((root / "registry.json").read_text())
    row = next(r for r in registry if r["group"] == group and r["eligible"])
    fold = row["fold"]
    seal = json.loads((root / "main_prediction_seal.json").read_text())
    for name, value in seal["sha256"].items():
        if (
            name.startswith("models/")
            and name.startswith(f"models/fold{fold}_")
            and sha(root / name) != value
        ):
            raise ValueError("Frozen checkpoint changed")
    threshold = json.loads((root / "thresholds.json").read_text())[
        f"{fold}:{variant}:{method}"
    ]["threshold"]
    bundle = models_for(root, fold, variant)
    detector = StreamingDetector(bundle, threshold, method=method, variant=variant)
    arrays = arrays_for([row])[group]
    horizon = json.loads((root / "registration.json").read_text())["folds"][fold][
        "horizon"
    ]
    for frame in range(0, len(arrays["timestamp"]), 3):
        now = float(arrays["timestamp"][frame])
        if now >= horizon:
            break
        q = arrays["qpos"][frame].tolist()
        target = arrays["actions"][frame - 1].tolist() if frame else q
        yield detector.update(
            SensorPacket(time=now, source_time=now, qpos=q, previous_target=target)
        )


def examples(root, variant="Q"):
    rows = [
        r
        for r in json.loads((root / "outcomes.json").read_text())
        if r["variant"] == variant
        and r["method"] == "P1"
        and r["stress"] == "clean"
        and r["boundary_delta"] == 0
    ]
    categories = {
        "timely": lambda r: r["timely"],
        "premature": lambda r: r["premature"],
        "missed": lambda r: (
            r["role"] == "recovery" and r["evaluable"] and not r["timely"]
        ),
        "reference_alarm": lambda r: r["reference_alarm"],
    }
    destination = root / "streaming" / variant
    destination.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, predicate in categories.items():
        candidates = sorted(
            [r for r in rows if predicate(r)],
            key=lambda r: (
                r["alarm_time"] if r["alarm_time"] is not None else float("inf"),
                r["group"],
            ),
        )
        if not candidates:
            result[name] = {"available": False}
            continue
        selected = candidates[0]
        traces = list(replay(root, selected["group"], variant=variant))
        with (destination / (name + ".jsonl")).open("w") as stream:
            for trace in traces:
                stream.write(json.dumps(trace) + "\n")
        path = (
            root
            / "predictions"
            / f"fold{selected['fold']}"
            / variant
            / "clean/evaluation"
            / (selected["group"].split(":")[1] + ".npz")
        )
        batch = dict(np.load(path))
        error = float(
            np.max(np.abs(np.array([r["risk"] for r in traces]) - batch["P1"]))
        )
        first = next((r["timestamp"] for r in traces if r["first_alarm"]), None)
        result[name] = {
            "available": True,
            "group": selected["group"],
            "fold": selected["fold"],
            "offline_status": selected["status"],
            "batch_alarm": selected["alarm_time"],
            "stream_alarm": first,
            "maximum_stream_batch_score_difference": error,
            "mean_inference_ms_per_packet": 1000
            * float(np.mean([r["inference_seconds"] for r in traces])),
            "p95_inference_ms_per_packet": 1000
            * float(np.percentile([r["inference_seconds"] for r in traces], 95)),
            "evaluation_overlay": {
                k: selected[k] for k in ("role", "timely", "premature", "delay", "lead")
            },
            "example_trace": next((r for r in traces if r["first_alarm"]), traces[-1]),
        }
    save_json(root / f"streaming/examples_{variant}.json", result)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--group")
    parser.add_argument("--method", choices=("B3", "P0", "P1", "P2"), default="P1")
    parser.add_argument("--variant", choices=("Q", "QC"), default="Q")
    parser.add_argument("--examples", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    if args.examples:
        if (args.root / "completion_manifest.json").exists():
            raise SystemExit("Evidence sealed; use read-only --group replay")
        for variant in ("Q", "QC"):
            examples(args.root, variant)
    else:
        for trace in replay(
            args.root, args.group, variant=args.variant, method=args.method
        ):
            print(json.dumps(trace))


if __name__ == "__main__":
    main()
