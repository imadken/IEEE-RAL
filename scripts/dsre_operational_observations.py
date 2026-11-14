"""Frozen offline observation corruptions in metres and 50 ms control packets."""

import copy
import hashlib
import json
import math

import numpy as np

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.operational import PolicyInput
from dual_rec.dsre.repair_selection import optional_values

SCENARIOS = (
    "clean",
    "missing_optional",
    "missing_history",
    "missing_pose",
    "noise001_r0",
    "noise001_r1",
    "noise001_r2",
    "noise005_r0",
    "noise005_r1",
    "noise005_r2",
    "delay1",
    "delay5",
)


def packet_from_summary(summary, frozen):
    selected = frozen["tasks"][summary["task"]]["1"]["selected"]
    primary, optional = summary["features"], summary["optional_features"]
    return PolicyInput(
        task=summary["task"],
        values=tuple(primary) + tuple(optional[i] for i in selected),
        full_values=tuple(primary) + tuple(optional),
    )


def observation_packet(raw, task, scenario, frozen, seed=2026111402):
    first = observed_frame(raw["prefix"][0]["time"], raw["prefix"][0]["observation"])
    current = observed_frame(
        raw["canonical_start"]["time"], raw["canonical_start"]["observation"]
    )
    original = ObservationHistory(first=first, current=current)
    if scenario.startswith("delay"):
        steps = int(scenario.removeprefix("delay"))
        old = raw["prefix"][-1 - steps]
        stale = observed_frame(old["time"], old["observation"])
        current = current.model_copy(
            update={
                n: getattr(stale, n)
                for n in ("object_position", "tcp_position", "goal_position")
            }
        )
    if scenario.startswith("noise"):
        sigma = 0.001 if scenario.startswith("noise001") else 0.005
        digest = hashlib.sha256(
            (json.dumps(raw["cell"], sort_keys=True) + scenario).encode()
        ).digest()
        rng = np.random.default_rng(seed + int.from_bytes(digest[:4], "little"))
        goal_error = rng.normal(0, sigma, 3)
        altered = []
        for frame in (first, current):
            update = {}
            for name in ("object_position", "tcp_position", "goal_position"):
                value = getattr(frame, name)
                error = (
                    goal_error if name == "goal_position" else rng.normal(0, sigma, 3)
                )
                update[name] = (
                    None if value is None else tuple(np.asarray(value) + error)
                )
            altered.append(frame.model_copy(update=update))
        first, current = altered
    if scenario == "missing_pose":
        first = first.model_copy(
            update={
                n: None for n in ("object_position", "tcp_position", "goal_position")
            }
        )
        current = current.model_copy(
            update={
                n: None for n in ("object_position", "tcp_position", "goal_position")
            }
        )
    if scenario == "missing_history":
        first = None
    history = ObservationHistory(first=first, current=current)
    primary, optional = list(feature_values(history)), list(optional_values(history))
    if scenario == "missing_optional":
        if task == "PickCube-v1":
            optional[0] = None
        else:
            primary[0] = None
    selected = frozen["tasks"][task]["1"]["selected"]
    packet = PolicyInput(
        task=task,
        values=tuple(primary) + tuple(optional[i] for i in selected),
        full_values=tuple(primary + optional),
    )
    payload = history.model_dump(mode="json")
    return packet, {
        "pose_source_delay_seconds": int(scenario.removeprefix("delay")) * 0.05
        if scenario.startswith("delay")
        else 0,
        "observed_payload_json_bytes": len(
            json.dumps(payload, separators=(",", ":")).encode()
        ),
        "scalar_input_fields": sum(
            len(v) if isinstance(v, list) else int(v is not None)
            for f in payload.values()
            if f
            for v in f.values()
        ),
        "payload": copy.deepcopy(payload),
        "threshold_proximal": near_threshold(original),
    }


def near_threshold(history):
    first, current = history.first, history.current
    if first is None or any(
        getattr(current, n) is None
        for n in ("object_position", "tcp_position", "goal_position")
    ):
        return None
    obj, hand, goal = (
        current.object_position,
        current.tcp_position,
        current.goal_position,
    )
    distances = [
        abs(math.dist(obj, goal) - 0.03),
        abs(math.dist(hand, obj) - 0.04),
        abs(hand[2] - obj[2] - 0.03),
    ]
    if first.object_position is not None and first.goal_position is not None:
        distances += [
            abs(
                math.dist(first.object_position, first.goal_position)
                - math.dist(obj, goal)
                - 0.005
            ),
            abs(math.dist(first.object_position, obj) - 0.005),
        ]
    if current.finger_positions is not None:
        distances.append(abs(sum(abs(v) for v in current.finger_positions) - 0.04))
    offsets = (obj[0] - goal[0], obj[1] - goal[1], hand[0] - obj[0])
    distances += [abs(v - bound) for v in offsets for bound in (-0.02, 0.02)]
    return min(distances) <= 0.001
