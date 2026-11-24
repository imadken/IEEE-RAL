"""Independent raw-source, action-equation, label and exact-risk audit.

Pure physical equations retained from the prior independently transcribed auditor.
This module never imports the policy scorer, production router or simulator.
"""

import argparse
import gzip
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import binom


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gz(path):
    with gzip.open(path, "rt") as stream:
        return json.load(stream)


def write(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def exact_upper(k, n, delta=0.05 / 68):
    if not n or k == n:
        return 1.0
    if k == 0:
        return 1 - delta ** (1 / n)
    return float(brentq(lambda p: binom.cdf(k, n, p) - delta, k / n, 1, xtol=1e-14))


def difference(left, right):
    if isinstance(left, dict) or isinstance(right, dict):
        assert isinstance(left, dict) and isinstance(right, dict)
        assert left.keys() == right.keys()
        return max((difference(left[k], right[k]) for k in left), default=0)
    x, y = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    assert x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    return float(np.max(np.abs(x - y))) if x.size else 0


def state_equal(a, b):
    assert np.linalg.norm(np.asarray(a["position"]) - b["position"]) <= 1e-5
    q, r = (
        np.asarray(a["quaternion"], dtype=float),
        np.asarray(b["quaternion"], dtype=float),
    )
    q, r = q / np.linalg.norm(q), r / np.linalg.norm(r)
    angle = 2 * math.acos(float(np.clip(abs(q @ r), 0, 1)))
    assert angle <= 1e-4
    for field in ("velocity", "qpos", "observation"):
        assert difference(a[field], b[field]) <= 1e-4
    assert abs(a["time"] - b["time"]) <= 1e-9
    assert a["success"] == b["success"] and a["contacts"] == b["contacts"]


def vec(observation, key):
    return np.asarray(observation["extra"][key], dtype=float).reshape(-1)[:3]


def expected_action(task, mode, step, observation, initial_tcp):
    """Independent transcription, using only each recorded pre-action packet."""
    cube, tcp, goal = (
        vec(observation, k) for k in ("obj_pose", "tcp_pose", "goal_pos")
    )
    gripper = -1
    if task == "PickCube-v1":
        target = goal
        if mode == "recover":
            if step < 8:
                target = np.asarray(initial_tcp) + [0, 0, 0.10]
                gripper = 1
            elif step < 22:
                target = cube + [0, 0, 0.10]
                gripper = 1
            elif step < 34:
                target = cube
                gripper = 1
            elif step < 46:
                target = cube
    else:
        target = np.array([goal[0], goal[1], cube[2]])
        if mode == "recover":
            if step < 6:
                target = np.asarray(initial_tcp) + [0, 0, 0.08]
            elif step < 16:
                target = cube + [-0.055, 0, 0.10]
            elif step < 26:
                target = cube + [-0.055, 0, 0]
    return np.r_[np.clip((target - tcp) / 0.1, -0.25, 0.25), gripper].astype(np.float32)


def predicates(first, current):
    obj, tcp, goal = (vec(current, k) for k in ("obj_pose", "tcp_pose", "goal_pos"))
    old_obj, old_goal = (vec(first, k) for k in ("obj_pose", "goal_pos"))
    fingers = np.asarray(current["agent"]["qpos"], dtype=float).reshape(-1)[-2:]
    near = np.linalg.norm(obj - goal)
    primary = [
        near <= 0.03,
        np.linalg.norm(obj - tcp) <= 0.04,
        np.linalg.norm(old_obj - old_goal) - near >= 0.005,
        np.linalg.norm(obj - old_obj) >= 0.005,
        np.abs(fingers).sum() <= 0.04,
        tcp[2] - obj[2] > 0.03,
    ]
    dx, dy, hx = obj[0] - goal[0], obj[1] - goal[1], tcp[0] - obj[0]
    optional = [dx < -0.02, dx > 0.02, dy < -0.02, dy > 0.02, hx < -0.02, hx > 0.02]
    return [bool(v) for v in primary], [bool(v) for v in optional]


def independent_tree_action(nodes, table, groups, x, target):
    """Read frozen splits, then recompute conservative leaf utility from raw rows."""
    node, path = 0, []
    while nodes[node]["feature"] is not None:
        feature = nodes[node]["feature"]
        if x[feature] is None:
            return None
        path.append(feature)
        node = nodes[node]["right"] if x[feature] else nodes[node]["left"]
    matched = [
        r for r in table["rows"] if all(r["features"][i] in (None, x[i]) for i in path)
    ]
    if len(matched) < 2 or len({groups[r["id"]] for r in matched}) < 2:
        return None
    means = [
        sum(r["outcomes"][a + "_value"] is True for r in matched) / len(matched)
        for a in ("continue", "recover")
    ]
    return (
        None
        if max(means) < target
        else ("recover" if means[1] > means[0] else "continue")
    )


def audit_cell(raw, directory):
    first = raw["prefix"][0]["observation"]
    cube, goal = vec(first, "obj_pose").copy(), vec(first, "goal_pos")
    cube[0] += raw["offset_x_m"]
    assert raw["fault_spec"]["offset_x"] == raw["offset_x_m"]
    assert raw["model"]["edit"]["cube_before"] == raw["model"]["edit"]["cube_after"]
    for j, command in enumerate(raw["prefix_actions"]):
        phase = 0 if j < 20 else 1 if j < 45 else 2 if j < 60 else 3
        target = cube + [0, 0, 0.12 if phase == 0 else 0] if phase < 3 else goal
        expected = np.r_[
            np.clip(
                (target - vec(raw["prefix"][j]["observation"], "tcp_pose")) / 0.1,
                -0.25,
                0.25,
            ),
            1 if phase < 2 else -1,
        ].astype(np.float32)
        assert difference(command, expected) < 2e-6
    state_equal(raw["prefix"][-1], raw["canonical_start"])
    primary, optional = predicates(first, raw["canonical_start"]["observation"])
    assert (
        primary == raw["summary"]["features"]
        and optional == raw["summary"]["optional_features"]
    )
    assert len(raw["prefix"]) == len(raw["prefix_actions"]) + 1
    counts = Counter(cells=1)
    outcomes = {}
    for action in ("continue", "recover"):
        path = directory / (action + ".json.gz")
        future = gz(path)
        assert future["controller_memory"] == raw["canonical_controller_memory"]
        assert future["model_edit"] == raw["model"]["edit"]
        assert len(future["frames"]) == 70
        for a, b in zip(raw["prefix"], future["prefix_states"], strict=True):
            state_equal(a, b)
            counts["prefix_states"] += 1
        state_equal(raw["canonical_start"], future["start"])
        previous = future["start"]
        for j, frame in enumerate(future["frames"]):
            assert (
                difference(previous["observation"], frame["before_observation"]) <= 1e-8
            )
            assert (
                difference(
                    expected_action(
                        "PickCube-v1",
                        action,
                        j,
                        frame["before_observation"],
                        future["initial_tcp"],
                    ),
                    frame["action"],
                )
                < 2e-6
            )
            assert abs(frame["state"]["time"] - previous["time"] - 0.05) < 1e-8
            previous = frame["state"]
            counts["future_states"] += 1
            counts["contact_frames"] += bool(previous["contacts"])
        assert future["terminal_success"] == previous["success"]
        outcomes[action + "_value"] = bool(previous["success"])
        counts["continuations"] += 1
    return counts, outcomes


def stratum_bounds(parents, methods, complete):
    output = {}
    for method in methods:
        for action in ("continue", "recover"):
            n = k = 0
            for parent in parents:
                assigned = [
                    c for c in parent["cells"] if c["proposals"][method] == action
                ]
                if assigned:
                    n += 1
                    k += any(not c["outcomes"][action + "_value"] for c in assigned)
            upper = exact_upper(k, n)
            output[method + "|" + action] = {
                "assigned_parents": n,
                "error_parents": k,
                "upper": upper,
                "enabled": bool(complete and n and upper <= 0.1),
            }
    return output


def audit(root, stage):
    plan = read(root / "study_plan.json")
    folder = "test" if stage == "test" else stage
    prefix = "test_outcome" if stage == "test" else stage
    target = 1 if stage == "qualification" else 256 if stage == "calibration" else 128
    seeds = plan[
        "qualification_seeds" if stage == "qualification" else stage + "_seeds"
    ]
    total = Counter()
    parents = []
    source_files = {}
    for p in sorted((root / "progress").glob(prefix + "-*.json")):
        progress = read(p)
        if progress["status"] != "COMPLETE":
            continue
        seed = progress["seed"]
        assert seed == seeds[progress["index"]]
        d = root / folder / str(seed)
        decision = read(d / "decision.json")
        assert sha(d / "decision.json") == progress["decision_sha256"]
        assert decision["source_freeze_sha256"] == sha(root / "source_freeze.json")
        if stage == "test":
            seal = read(root / "test_recommendation_seal.json")
            started = read(d / "execution_started.json")
            assert seal["parents"][str(seed)] == progress["decision_sha256"]
            assert started["cohort_seal_sha256"] == sha(
                root / "test_recommendation_seal.json"
            )
            assert (
                read(root / "calibration_seal.json")["epoch"]
                <= decision["sealed_epoch"]
                <= seal["epoch"]
                <= started["epoch"]
            )
        cells = []
        for condition, offset in plan["profiles"]:
            cd = d / condition
            raw = gz(cd / "screen.json.gz")
            assert sha(cd / "screen.json.gz") == decision["screens"][condition]
            assert (
                raw["offset_x_m"] == offset
                and raw["screened_epoch"] <= decision["sealed_epoch"]
            )
            assert raw["model"]["versions"] == {
                "mani-skill": "3.0.1",
                "sapien": "3.0.3",
                "torch": "2.5.1+cpu",
                "numpy": "1.26.4",
            }
            checks, outcomes = audit_cell(raw, cd)
            total.update(checks)
            proposals = {
                m: x["action"]
                for m, x in raw["scenarios"]["clean"]["point_proposal"].items()
            }
            assert set(proposals) == set(plan["methods"])
            for a, b in (("DSRE_strict", "B7"), ("DSRE_risk", "B7_risk")):
                for scenario in raw["scenarios"].values():
                    for mode in ("point_proposal", "robust_proposal"):
                        assert (
                            scenario[mode][a]["action"] == scenario[mode][b]["action"]
                        )
                        assert (
                            scenario[mode][a]["evidence"]
                            == scenario[mode][b]["evidence"]
                        )
            for action in ("continue", "recover"):
                fp = cd / (action + ".json.gz")
                out = gz(fp)
                assert out["completed_epoch"] > decision["sealed_epoch"]
                source_files[str(fp)] = sha(fp)
            source_files[str(cd / "screen.json.gz")] = sha(cd / "screen.json.gz")
            if stage == "qualification":
                old = Path(plan["qualification_reference"]) / str(seed) / condition
                oldraw = gz(old / "screen.json.gz")
                assert oldraw["prefix_actions"] == raw["prefix_actions"]
                assert (
                    oldraw["canonical_controller_memory"]
                    == raw["canonical_controller_memory"]
                )
                assert oldraw["model"] == raw["model"]
                for a, b in zip(oldraw["prefix"], raw["prefix"], strict=True):
                    state_equal(a, b)
                for action in ("continue", "recover"):
                    oldf = gz(old / "repeat0" / (action + ".json.gz"))
                    newf = gz(cd / (action + ".json.gz"))
                    for a, b in zip(oldf["frames"], newf["frames"], strict=True):
                        state_equal(a["state"], b["state"])
            cells.append(
                {
                    "condition": condition,
                    "initial_success": raw["summary"]["initial_success"],
                    "outcomes": outcomes,
                    "proposals": proposals,
                }
            )
        labels = {
            "seed": seed,
            "cells": cells,
            "decision_sha256": progress["decision_sha256"],
        }
        write(d / "outcome_labels.json", labels)
        parents.append(labels)
    complete = len(parents) == target
    result = {
        "passed": True,
        "parents": len(parents),
        "registered_parents": target,
        "complete_cohort": complete,
        "counts": dict(total),
        "independent_implementation": "No policy scorer, production router, simulator or calibration-bound imports; recorded action equations, raw labels and scipy binomial inversion.",
        "source_file_sha256": source_files,
        "epoch": time.time(),
    }
    if stage == "qualification":
        assert complete and total["cells"] == 5 and total["continuations"] == 10
        write(root / "qualification_audit.json", result)
    else:
        result["independent_strata"] = (
            stratum_bounds(parents, plan["methods"], complete)
            if stage == "calibration"
            else None
        )
        write(root / (stage + "_physics_audit.json"), result)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("source_file_sha256", "independent_strata")
            }
        ),
        flush=True,
    )


def decision_audit(root):
    own = read(root / "calibration_physics_audit.json")
    decision = read(root / "calibration_decision.json")
    assert own["complete_cohort"] and decision["complete_cohort"]
    assert len(decision["strata"]) == 34
    for key, expected in own["independent_strata"].items():
        actual = decision["strata"][key]
        for field in ("assigned_parents", "error_parents", "enabled"):
            assert actual[field] == expected[field], (key, field)
        assert abs(actual["upper"] - expected["upper"]) < 1e-11
        assert actual["delta"] == 0.05 / 68 and actual["target"] == 0.1
    assert (
        sha(root / "calibration_decision.json")
        == read(root / "calibration_seal.json")["sha256"]
    )
    write(
        root / "calibration_decision_audit.json",
        {
            "passed": True,
            "method_action_strata": 34,
            "calibration_sha256": sha(root / "calibration_decision.json"),
            "epoch": time.time(),
        },
    )
    print(json.dumps({"passed": True, "strata": 34}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument(
        "--stage",
        choices=["qualification", "calibration", "test", "decision"],
        required=True,
    )
    a = p.parse_args()
    if a.stage == "decision":
        decision_audit(a.root)
    else:
        audit(a.root, a.stage)
