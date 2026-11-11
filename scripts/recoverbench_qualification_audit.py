"""Independently recompute rescue diagnostics without importing the executor."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def audit_trace(rows, actions, states):
    mismatches = []
    first_success = None
    first_divergence = None
    max_state_error = 0.0
    max_cache_error = 0.0
    max_gripper_memory = 0.0
    for i, row in enumerate(rows):
        before = np.array(row["before"]["state"])
        after = np.array(row["after"]["state"])
        if row["step"] != i + 1 or not np.array_equal(row["action"], actions[i]):
            mismatches.append(f"control mismatch at {i + 1}")
        if not np.isfinite(before).all() or not np.isfinite(after).all():
            mismatches.append(f"nonfinite state at {i + 1}")
        if not np.isclose(after[0] - before[0], 0.05, atol=1e-10, rtol=0):
            mismatches.append(f"physics time at {i + 1}")
        if i and not np.array_equal(before, rows[i - 1]["after"]["state"]):
            mismatches.append(f"intermediate state reset at {i + 1}")
        if not i and not np.allclose(before, states[0], atol=1e-12, rtol=0):
            mismatches.append("source initialization")
        error = float(np.max(np.abs(before - states[i])))
        max_state_error = max(max_state_error, error)
        if first_divergence is None and error > 1e-8:
            first_divergence = i  # zero-based number of already executed actions
        controller = row["before"].get("controller", {})
        if controller.get("ee_pos") is not None:
            max_cache_error = max(
                max_cache_error,
                float(
                    np.linalg.norm(
                        np.array(controller["ee_pos"]) - row["before"]["eef"]
                    )
                ),
            )
        max_gripper_memory = max(
            max_gripper_memory,
            float(np.max(np.abs(row["before"].get("gripper_current_action", [0])))),
        )
        if row["after"]["success"] and first_success is None:
            first_success = i + 1
    if len(rows) != len(actions):
        mismatches.append("incomplete recorded tape")
    return {
        "mismatches": mismatches,
        "first_success_step": first_success,
        "initial_success": bool(rows[0]["before"]["success"]),
        "initial_state_residual": float(
            np.max(np.abs(np.array(rows[0]["before"]["state"]) - states[0]))
        ),
        "terminal_success": bool(rows[-1]["after"]["success"]),
        "first_recorded_pre_state_divergence_after_actions": first_divergence,
        "max_reference_state_error": max_state_error,
        "max_pre_action_controller_cache_error_m": max_cache_error,
        "max_abs_gripper_memory": max_gripper_memory,
    }


def physics_audit(root, outcomes, feature_manifest):
    import mujoco
    import yaml

    upstream = next((root / "upstream/source").iterdir())
    sys.path.insert(0, str(upstream))
    from error_benchmark.scripts.utils.script_utils import create_env

    checked, errors, features = 0, [], []
    for task in ("stack", "pick_place"):
        config = yaml.safe_load(
            (upstream / "error_benchmark/configs/tasks" / (task + ".yaml")).read_text()
        )
        env = create_env(
            config,
            str(root / "data/seed_demos" / (task + ".hdf5")),
            enable_camera=False,
            has_renderer=False,
        )
        for row in outcomes:
            if row["case"]["task"] != task:
                continue
            with gzip.open(root / row["trace_path"], "rt") as stream:
                records = [json.loads(line) for line in stream]
            snapshots = [records[0]["before"], records[-1]["after"]]
            if row["first_success_step"] is not None:
                snapshots.append(records[row["first_success_step"] - 1]["after"])
            for snapshot in snapshots:
                env.sim.set_state_from_flattened(np.array(snapshot["state"]))
                env.sim.forward()
                checked += 1
                if bool(env._check_success()) != snapshot["success"]:
                    errors.append(row["trace_path"])
        for feature in feature_manifest:
            if feature["source"]["task"] != task:
                continue
            with np.load(root / feature["feature_path"], allow_pickle=False) as payload:
                differences, body_errors, rotation_errors = [], [], []
                data = mujoco.MjData(env.sim.model._model)
                model = env.sim.model._model
                site = env.robots[0].eef_site_id
                body = model.site_bodyid[site]
                for i, state in enumerate(payload["states"]):
                    data.time = state[0]
                    data.qpos[:] = state[1 : 1 + model.nq]
                    data.qvel[:] = state[1 + model.nq :]
                    mujoco.mj_forward(model, data)
                    differences.append(
                        float(
                            np.max(
                                np.abs(
                                    data.site_xpos[site] - payload["eef_positions"][i]
                                )
                            )
                        )
                    )
                    rotation_errors.append(
                        float(
                            np.max(
                                np.abs(
                                    data.site_xmat[site].reshape(3, 3)
                                    - payload["eef_rotations"][i]
                                )
                            )
                        )
                    )
                    predicted = (
                        data.xpos[body]
                        + data.xmat[body].reshape(3, 3) @ model.site_pos[site]
                    )
                    body_errors.append(
                        float(np.max(np.abs(predicted - data.site_xpos[site])))
                    )
                features.append(
                    {
                        "feature": feature["feature_path"],
                        "samples": len(differences),
                        "max_independent_position_error": max(differences),
                        "max_site_body_error": max(body_errors),
                        "max_independent_rotation_error": max(rotation_errors),
                    }
                )
                if (
                    max(differences) > 1e-10
                    or max(body_errors) > 1e-10
                    or max(rotation_errors) > 1e-10
                ):
                    errors.append(feature["feature_path"])
        env.close()
    return {
        "status": "PASS" if not errors else "FAIL",
        "predicate_snapshots": checked,
        "feature_checks": features,
        "errors": errors,
        "scope": "Independent original predicate and local-model FK checks, not proof of original-scene model equivalence",
    }


def numerical_audit(root):
    registration = json.loads((root / "registration.json").read_text())
    outcomes_path = root / "source-diagnostics/outcomes.jsonl"
    outcomes = [json.loads(s) for s in outcomes_path.read_text().splitlines()]
    manifest = json.loads((root / "derived/manifest.json").read_text())
    expected = {s["archive_member"] for s in registration["sources"]}
    grouped = defaultdict(list)
    records = []
    failures = []
    for row in outcomes:
        member = row["case"]["archive_member"]
        assert member in expected
        assert digest(root / row["trace_path"]) == row["trace_sha256"]
        with np.load(root / "data" / member, allow_pickle=False) as source:
            actions, states = source["actions"], source["states"]
            assert len(actions) == len(states)
            with gzip.open(root / row["trace_path"], "rt") as stream:
                trace = [json.loads(s) for s in stream]
            recomputed = audit_trace(trace, actions, states)
        for name in ("initial_success", "terminal_success", "first_success_step"):
            if recomputed[name] != row[name]:
                failures.append(f"Outcome mismatch: {member}/{name}")
        failures.extend(recomputed["mismatches"])
        record = {
            "case": row["case"],
            "variant": row["variant"],
            "controls": len(trace),
            **recomputed,
        }
        records.append(record)
        grouped[(member, row["variant"])].append(trace)
    assert len(grouped) == 24 and all(len(v) == 1 for v in grouped.values())
    comparisons = []
    for member in sorted(expected):
        a = grouped[(member, "official_source_checker_shared_environment")][0]
        b = grouped[(member, "direct_controls_fresh_reset")][0]
        comparisons.append(
            {
                "source": member,
                "max_before_contact_count_difference": max(
                    abs(len(x["before"]["contacts"]) - len(y["before"]["contacts"]))
                    for x, y in zip(a, b, strict=True)
                ),
                "max_before_controller_eef_difference_m": max(
                    float(
                        np.linalg.norm(
                            np.array(x["before"]["controller"]["ee_pos"])
                            - y["before"]["controller"]["ee_pos"]
                        )
                    )
                    for x, y in zip(a, b, strict=True)
                ),
                "max_after_state_difference": max(
                    float(
                        np.max(
                            np.abs(np.array(x["after"]["state"]) - y["after"]["state"])
                        )
                    )
                    for x, y in zip(a, b, strict=True)
                ),
                "max_before_gripper_qpos_difference": max(
                    float(
                        np.max(
                            np.abs(
                                np.array(x["before"]["gripper_qpos"])
                                - y["before"]["gripper_qpos"]
                            )
                        )
                    )
                    for x, y in zip(a, b, strict=True)
                ),
                "max_before_gripper_memory_difference": max(
                    float(
                        np.max(
                            np.abs(
                                np.array(x["before"]["gripper_current_action"])
                                - y["before"]["gripper_current_action"]
                            )
                        )
                    )
                    for x, y in zip(a, b, strict=True)
                ),
                "first_hit_agrees": next(
                    (x["step"] for x in a if x["after"]["success"]), None
                )
                == next((x["step"] for x in b if x["after"]["success"]), None),
            }
        )
    for feature in manifest:
        assert (
            digest(root / "data" / feature["source"]["archive_member"])
            == feature["source_sha256"]
        )
        assert digest(root / feature["feature_path"]) == feature["feature_sha256"]
        with np.load(root / feature["feature_path"], allow_pickle=False) as payload:
            assert set(payload) == {
                "states",
                "eef_positions",
                "eef_rotations",
                "body_positions",
                "body_rotations",
            }
    source_ids = {s["scene_id"] for s in registration["sources"]}
    target_ids = {s["scene_id"] for s in registration["generator_scenes"]}
    assert not source_ids & target_ids and len(target_ids) == 8
    summary = []
    for task in ("stack", "pick_place"):
        for variant in (
            "official_source_checker_shared_environment",
            "direct_controls_fresh_reset",
        ):
            rows = [
                r
                for r in records
                if r["case"]["task"] == task and r["variant"] == variant
            ]
            summary.append(
                {
                    "task": task,
                    "variant": variant,
                    "sources": len(rows),
                    "initial_success": sum(r["initial_success"] for r in rows),
                    "first_hit_success": sum(
                        r["first_success_step"] is not None for r in rows
                    ),
                    "new_success": sum(
                        not r["initial_success"] and r["first_success_step"] is not None
                        for r in rows
                    ),
                    "terminal_success": sum(r["terminal_success"] for r in rows),
                }
            )
    return (
        {
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "outcomes_sha256": digest(outcomes_path),
            "rows": len(records),
            "counted_controls": sum(r["controls"] for r in records),
            "derived_feature_sources": len(manifest),
            "source_target_disjoint": True,
            "summary": summary,
            "records": records,
            "source_checker_vs_direct": comparisons,
            "ACRR_false_acceptance": None,
            "ACRR_false_rejection": None,
            "method_effect_intervals": None,
        },
        outcomes,
        manifest,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--physics", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    result, outcomes, features = numerical_audit(args.root)
    if args.physics:
        result = physics_audit(args.root, outcomes, features)
    (
        args.root
        / (
            "independent_physics_audit.json"
            if args.physics
            else "independent_numerical_audit.json"
        )
    ).write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"records", "source_checker_vs_direct", "feature_checks"}
            }
        )
    )
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
