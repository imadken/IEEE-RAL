"""Recording-level joins and causal sensor packets for the overnight pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from dual_rec.reboot.audit import episode_arrays, physical_hash
from dual_rec.reboot.contracts import PhaseEpisode, event_integrity

OLD = Path("results/reboot-phase/20261111T204459Z")
CORE = (
    "sample_recovery-demonstration",
    "16mm-cylinder_recovery_install",
    "16mm-cylinder_install",
)
EXTERNAL = (
    "16mm-cylinder_remove",
    "usb-c_install",
    "usb-c_remove",
    "rj45-install",
    "rj45_remove",
)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class SensorPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)
    time: float
    source_time: float
    qpos: list[float] = Field(min_length=14, max_length=14)
    previous_target: list[float] = Field(min_length=14, max_length=14)


def verified_inputs(root, *, external=False):
    """Check only consumed files against the earlier seal, never rewrite them."""
    seal = json.loads((OLD / "completion_manifest.json").read_text())
    names = CORE + (EXTERNAL if external else ())
    paths = [OLD / "data/sample_recovery-demonstration/meta/phase.json"]
    for name in names:
        paths.append(OLD / "data" / name / "meta/info.json")
        paths.extend(sorted((OLD / "projected" / name / "data").rglob("*.parquet")))
    values = {}
    for path in paths:
        value = sha(path)
        if value != seal["evidence_sha256"][str(path.relative_to(OLD))]:
            raise ValueError(f"Consumed input changed: {path}")
        values[str(path)] = value
    destination = root / (
        "external_inputs.json" if external else "consumed_inputs.json"
    )
    save_json(destination, values)
    return values


def make_registry(root):
    verified_inputs(root)
    sample, recovery, reference = [episode_arrays(OLD, name) for name in CORE]
    by_hash = {}
    for episode, arrays in recovery.items():
        by_hash.setdefault(physical_hash(arrays), []).append(episode)
    raw_labels = json.loads((OLD / "data" / CORE[0] / "meta/phase.json").read_text())[
        "episodes"
    ]
    entries, eligible = [], []
    for raw in raw_labels:
        episode = int(raw["episode_index"])
        arrays = sample[episode]
        value = physical_hash(arrays)
        candidates = by_hash.get(value, [])
        if len(candidates) != 1:
            raise ValueError("CORE_LABEL_IDENTITY_BLOCKED: ambiguous exact join")
        other = recovery[candidates[0]]
        for key in ("qpos", "actions", "timestamp", "frame_index"):
            if not np.array_equal(arrays[key], other[key]):
                raise ValueError(
                    "CORE_LABEL_IDENTITY_BLOCKED: exact array join differs"
                )
        reasons = []
        try:
            parsed = PhaseEpisode.model_validate(raw)
            integrity = event_integrity(parsed, arrays["frame_index"])
            if not integrity["event_frames_in_bounds"]:
                reasons.append("nonpositive_or_out_of_bounds_event_window")
        except ValueError:
            reasons.append("original_schema_rejected")
        if not all(
            np.isfinite(arrays[k]).all() for k in ("qpos", "actions", "timestamp")
        ):
            reasons.append("nonfinite_observations")
        group = "recording:" + value
        event = raw["failure"]
        row = {
            "group": group,
            "role": "recovery",
            "episode": candidates[0],
            "repository": CORE[1],
            "sample_episode": episode,
            "aliases": [f"{CORE[0]}:{episode}", f"{CORE[1]}:{candidates[0]}"],
            "equality_channels": ["qpos", "actions", "timestamp", "frame_index"],
            "raw_annotation": raw,
            "annotation_revision": "0633573d0438be1185bddebdf1a2c8f5505f7b2a",
            "eligible": not reasons,
            "exclusion_reasons": reasons,
            "frames": len(arrays["timestamp"]),
            "onset_frame": event["induced_at_frame"],
            "recovery_frame": event["recovery_started_at_frame"],
        }
        if row["eligible"]:
            row["onset"] = float(arrays["timestamp"][row["onset_frame"]])
            row["recovery"] = float(arrays["timestamp"][row["recovery_frame"]])
            eligible.append(row)
        entries.append(row)
    for episode, arrays in reference.items():
        row = {
            "group": "recording:" + physical_hash(arrays),
            "role": "reference",
            "repository": CORE[2],
            "episode": episode,
            "aliases": [f"{CORE[2]}:{episode}"],
            "eligible": True,
            "exclusion_reasons": [],
            "raw_annotation": None,
            "frames": len(arrays["timestamp"]),
        }
        entries.append(row)
        eligible.append(row)
    if len({r["group"] for r in eligible}) != len(eligible):
        raise ValueError("Duplicate canonical cohort entry; do not count aliases twice")
    for role in ("recovery", "reference"):
        ordered = sorted(
            [r for r in eligible if r["role"] == role],
            key=lambda r: hashlib.sha256(
                ("reboot-overnight-v1:" + r["group"]).encode()
            ).hexdigest(),
        )
        for index, row in enumerate(ordered):
            row["fold"] = index % 5
        if min(sum(r["fold"] == k for r in ordered) for k in range(5)) < 2:
            raise ValueError("Insufficient independent recordings for five folds")
    save_json(root / "registry.json", entries)
    return entries


def arrays_for(rows):
    repositories = {r["repository"] for r in rows}
    loaded = {name: episode_arrays(OLD, name) for name in repositories}
    return {r["group"]: loaded[r["repository"]][r["episode"]] for r in rows}


def sensor_features(arrays, group, *, variant="QC", stress="clean"):
    """10 Hz packets; differences use the last received scored observation."""
    indexes = np.arange(0, len(arrays["timestamp"]), 3)
    clock = arrays["timestamp"][indexes].astype(float)
    packet_q = arrays["qpos"][indexes].astype(float)
    previous_target = arrays["actions"][np.maximum(indexes - 1, 0)].astype(float)
    previous_target[0] = packet_q[0]
    drop = float(stress[4:]) if stress.startswith("drop") else 0
    ticks = round(float(stress[5:]) * 10) if stress.startswith("delay") else 0
    rng = np.random.default_rng(
        int(hashlib.sha256(("sensor-v1:" + group).encode()).hexdigest()[:16], 16)
    )
    unavailable = rng.random(len(clock)) < drop
    output = np.full((len(clock), 42), np.nan)
    sources = np.full(len(clock), -1, dtype=int)
    last = None
    held = None
    for decision in range(len(clock)):
        packet = decision - ticks
        if packet >= 0 and not unavailable[packet]:
            velocity = (
                np.zeros(14)
                if last is None
                else (packet_q[packet] - packet_q[last]) / (clock[packet] - clock[last])
            )
            held = np.concatenate(
                [packet_q[packet], velocity, previous_target[packet] - packet_q[packet]]
            )
            last = packet
        if held is not None:
            output[decision] = held
            sources[decision] = indexes[last]
    return {
        "time": clock,
        "features": output[:, :28] if variant == "Q" else output,
        "native_frame": indexes,
        "source_frame": sources,
    }


def targets(row, series, horizon):
    time = series["time"]
    mask = (time < horizon) & np.isfinite(series["features"]).all(axis=1)
    y = np.zeros(len(time), dtype=float)
    phase = np.full(len(time), -1, dtype=int)
    if row["role"] == "recovery":
        mask &= time < row["recovery"]
        y[time >= row["onset"]] = 1
        bounds = row["raw_annotation"]["phase_boundaries"]
        ordered = all(bounds[f"tau_{i}"] < bounds[f"tau_{i + 1}"] for i in range(5))
        if ordered:
            for i in range(5):
                selected = (
                    (series["native_frame"] >= bounds[f"tau_{i}"])
                    & (series["native_frame"] < bounds[f"tau_{i + 1}"])
                    & mask
                )
                phase[selected] = i
    return y, mask, phase


def fold_spec(rows, arrays, k):
    train = [r for r in rows if r["fold"] not in (k, (k + 1) % 5)]
    calibration = [r for r in rows if r["fold"] == (k + 1) % 5]
    evaluation = [r for r in rows if r["fold"] == k]
    horizon = min(
        30.0,
        *[
            float(
                np.percentile(
                    [
                        arrays[r["group"]]["timestamp"][-1]
                        for r in train
                        if r["role"] == role
                    ],
                    5,
                )
            )
            for role in ("reference", "recovery")
        ],
    )
    return train, calibration, evaluation, horizon
