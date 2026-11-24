"""Recompute the frozen PickCube success predicate from saved physical fields.

No simulator or production selector import. This checks the existing endpoint;
it does not replace labels, thresholds, task conditions or intervention outcomes.
"""

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np


def load(path):
    with gzip.open(path, "rt") as stream:
        return json.load(stream)


def terminal_success(state):
    position = np.asarray(state["position"], dtype=np.float32).reshape(-1)
    goal = np.asarray(
        state["observation"]["extra"]["goal_pos"], dtype=np.float32
    ).reshape(-1)
    qpos = np.asarray(state["qpos"]).reshape(-1)
    velocity = np.asarray(state["velocity"], dtype=np.float32).reshape(-1)
    assert position.shape == goal.shape == (3,)
    assert qpos.size == 9 and velocity.size == 15
    assert (
        np.isfinite(position).all()
        and np.isfinite(goal).all()
        and np.isfinite(velocity).all()
    )
    # Panda's existing is_static excludes the two finger joints.
    arm_velocity = velocity[6:13]
    distance = np.sqrt(np.sum((goal - position) ** 2, dtype=np.float32))
    return bool(
        distance <= np.float32(0.025)
        and np.max(np.abs(arm_velocity)) <= np.float32(0.2)
    )


def audit(root, stage):
    namespace = root / stage
    screens = sorted(namespace.glob("*/*/screen.json.gz"))
    if stage == "qualification":
        screens += sorted(
            (root / "stability").glob("repeat*/qualification/*/*/screen.json.gz")
        )
    checked, initial, success, failure = 0, 0, 0, 0
    for path in screens:
        raw = load(path)
        derived = terminal_success(raw["canonical_start"])
        assert (
            derived
            == raw["canonical_start"]["success"]
            == raw["summary"]["initial_success"]
        ), str(path)
        initial += 1
        for action in ("continue", "recover"):
            source = path.parent / (action + ".json.gz")
            branch = load(source)
            final = branch["frames"][-1]["state"]
            expected = terminal_success(final)
            assert expected == final["success"] == branch["terminal_success"], str(
                source
            )
            checked += 1
            success += expected
            failure += not expected
    report = {
        "passed": True,
        "stage": stage,
        "initial_success_flags_independently_recomputed": initial,
        "terminal_labels_independently_recomputed": checked,
        "true_terminals": success,
        "false_terminals": failure,
        "predicate": "Float32 Euclidean cube-goal distance<=.025m AND maxabs Panda arm(qvel excluding2fingers)<=.2; unchanged pinned task endpoint",
        "no_labels_replaced": True,
        "no_selector_or_simulator_imported": True,
        "epoch": time.time(),
    }
    target = root / (stage + "_terminal_predicate_audit.json")
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--stage", choices=("qualification", "calibration", "test"), required=True
    )
    args = parser.parse_args()
    audit(args.root, args.stage)
