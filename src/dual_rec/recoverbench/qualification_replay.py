"""Compare the released source checker, reset replay and offline kinematics."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

from .qualification import controller_metadata, source_tree
from .replay import load_original, validate_arrays


def snapshot(env):
    robot = env.robots[0]
    controller = robot.controller
    model, data = env.sim.model, env.sim.data
    fingers = [
        model.get_joint_qpos(name)
        if hasattr(model, "get_joint_qpos")
        else data.get_joint_qpos(name)
        for name in robot.gripper.joints
    ]
    memory = {}
    for name in (
        "ee_pos",
        "ee_ori_mat",
        "goal_pos",
        "goal_ori",
        "initial_joint",
        "joint_pos",
        "joint_vel",
        "new_update",
    ):
        value = getattr(controller, name, None)
        memory[name] = value.tolist() if isinstance(value, np.ndarray) else value
    contacts = [
        {
            "geom1": int(c.geom1),
            "geom2": int(c.geom2),
            "distance": float(c.dist),
            "position": c.pos.tolist(),
        }
        for c in data.contact[: data.ncon]
    ]
    return {
        "state": env.sim.get_state().flatten().tolist(),
        "eef": data.site_xpos[robot.eef_site_id].tolist(),
        "eef_rotation": data.site_xmat[robot.eef_site_id].reshape(3, 3).tolist(),
        "gripper_qpos": np.asarray(fingers).reshape(-1).tolist(),
        "gripper_current_action": robot.gripper.current_action.tolist(),
        "controller": memory,
        "contacts": contacts,
        "success": bool(env._check_success()),
    }


def independently_reconstruct(env, state):
    """Separate MuJoCo data; no writes to the executing environment or controller."""
    import mujoco

    model = env.sim.model._model
    data = mujoco.MjData(model)
    state = np.asarray(state)
    if len(state) != 1 + model.nq + model.nv:
        raise ValueError(
            "Expected time/qpos/qvel snapshot without hidden actuation state"
        )
    data.time = float(state[0])
    data.qpos[:] = state[1 : 1 + model.nq]
    data.qvel[:] = state[1 + model.nq :]
    mujoco.mj_forward(model, data)
    site = env.robots[0].eef_site_id
    body = model.site_bodyid[site]
    parent_rotation = data.xmat[body].reshape(3, 3)
    position_from_body = data.xpos[body] + parent_rotation @ model.site_pos[site]
    local_rotation = np.empty(9)
    mujoco.mju_quat2Mat(local_rotation, model.site_quat[site])
    rotation_from_body = parent_rotation @ local_rotation.reshape(3, 3)
    return {
        "eef": data.site_xpos[site].copy(),
        "rotation": data.site_xmat[site].reshape(3, 3).copy(),
        "body_eef": position_from_body,
        "body_rotation": rotation_from_body,
        "site_body_position_error": float(
            np.max(np.abs(position_from_body - data.site_xpos[site]))
        ),
        "site_body_rotation_error": float(
            np.max(np.abs(rotation_from_body - data.site_xmat[site].reshape(3, 3)))
        ),
        "contacts": int(data.ncon),
    }


def read_controls(root, case):
    path = root / "data" / case["archive_member"]
    with np.load(path, allow_pickle=False) as data:
        actions, states = data["actions"].copy(), data["states"].copy()
        stored_eef = data["eef_positions"].copy()
    validate_arrays(actions, states)
    if len(actions) > 1500:
        raise ValueError("Frozen source control cap exceeded")
    return actions, states, stored_eef


def derived_features(root, env, case, index):
    _, states, stale_eef = read_controls(root, case)
    references = [independently_reconstruct(env, state) for state in states]
    positions = np.array([r["eef"] for r in references])
    rotations = np.array([r["rotation"] for r in references])
    wrapper_errors = []
    # Exact-state visualization diagnostic only; never scored as a rollout.
    env.reset()
    cached_positions = []
    for state, reference in zip(states, references, strict=True):
        env.sim.set_state_from_flattened(state)
        env.sim.forward()
        cached_positions.append(env.robots[0].controller.ee_pos.copy())
        wrapper_errors.append(
            float(
                np.max(
                    np.abs(
                        env.sim.data.site_xpos[env.robots[0].eef_site_id]
                        - reference["eef"]
                    )
                )
            )
        )
    path = root / "derived" / f"source-{index:02d}-kinematics.npz"
    np.savez_compressed(
        path,
        states=states,
        eef_positions=positions,
        eef_rotations=rotations,
        body_positions=np.array([r["body_eef"] for r in references]),
        body_rotations=np.array([r["body_rotation"] for r in references]),
    )
    return {
        "source": case,
        "source_sha256": hashlib.sha256(
            (root / "data" / case["archive_member"]).read_bytes()
        ).hexdigest(),
        "feature_path": str(path.relative_to(root)),
        "feature_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "samples": len(states),
        "is_executable_recovery": False,
        "model_scope": "Local factory model; validates FK consistency, not original model identity",
        "max_independent_vs_sim_site_error": max(wrapper_errors),
        "max_site_body_position_error": max(
            r["site_body_position_error"] for r in references
        ),
        "max_site_body_rotation_error": max(
            r["site_body_rotation_error"] for r in references
        ),
        "stored_eef_axis_range": np.ptp(stale_eef, axis=0).tolist(),
        "cached_controller_axis_range_after_state_forwards": np.ptp(
            cached_positions, axis=0
        ).tolist(),
        "reconstructed_eef_axis_range": np.ptp(positions, axis=0).tolist(),
        "max_stored_eef_discrepancy_m": float(
            np.max(np.linalg.norm(stale_eef - positions, axis=1))
        ),
    }


def write_step(stream, env, action, step):
    before = snapshot(env)
    result = env.step(action)
    after = snapshot(env)
    stream.write(
        json.dumps(
            {
                "step": step,
                "action": np.asarray(action).tolist(),
                "before": before,
                "after": after,
            }
        )
        + "\n"
    )
    return result


def run_sources(root):
    import h5py

    sys.path.insert(0, str(source_tree(root)))
    import yaml
    from error_benchmark.framework.env_wrapper import EnvWrapper
    from error_benchmark.framework.mimicgen_source_validation import (
        build_demo_replay_success_checker,
    )

    registration = json.loads((root / "registration.json").read_text())
    output = root / "source-diagnostics"
    output.mkdir()
    (output / "traces").mkdir()
    (root / "derived").mkdir()
    outcomes, features = [], []
    for task in ("stack", "pick_place"):
        cases = [c for c in registration["sources"] if c["task"] == task]
        # Derived checker input preserves raw numerical arrays and seed env_args.
        # It is NOT a prepared DataGenerator source and has no invented datagen_info.
        dataset = root / "derived" / f"{task}-checker-input.hdf5"
        with (
            h5py.File(root / "data/seed_demos" / f"{task}.hdf5", "r") as seed,
            h5py.File(dataset, "x") as target,
        ):
            group = target.create_group("data")
            group.attrs["env_args"] = seed["data"].attrs["env_args"]
            for i, case in enumerate(cases):
                actions, states, _ = read_controls(root, case)
                demo = group.create_group(f"demo_{i}")
                demo.create_dataset("actions", data=actions)
                demo.create_dataset("states", data=states)
        config = yaml.safe_load(
            (
                source_tree(root) / "error_benchmark/configs/tasks" / f"{task}.yaml"
            ).read_text()
        )
        np.random.seed(3101)
        checker = build_demo_replay_success_checker(str(dataset), config)
        # Instrument the original wrapper step while retaining its original call.
        original_step = EnvWrapper.step
        context = {
            "stream": None,
            "step": 0,
            "initial": None,
            "env": None,
            "first_success": None,
        }

        def traced_step(wrapper, action, _context=context, _step=original_step):
            env = wrapper._env
            before = snapshot(env)
            if _context["initial"] is None:
                _context["initial"] = before
            _context["env"] = env
            result = _step(wrapper, action)
            _context["step"] += 1
            after = snapshot(env)
            if after["success"] and _context["first_success"] is None:
                _context["first_success"] = _context["step"]
            _context["stream"].write(
                json.dumps(
                    {
                        "step": _context["step"],
                        "action": np.asarray(action).tolist(),
                        "before": before,
                        "after": after,
                    }
                )
                + "\n"
            )
            return result

        for i, case in enumerate(cases):
            trace = output / "traces" / f"{task}-{i}-official-checker.jsonl.gz"
            context.update(step=0, initial=None, first_success=None)
            with (
                gzip.open(trace, "xt") as stream,
                patch.object(EnvWrapper, "step", traced_step),
            ):
                context["stream"] = stream
                terminal = checker(f"demo_{i}")
            env = context["env"]
            outcomes.append(
                {
                    "case": case,
                    "variant": "official_source_checker_shared_environment",
                    "initial_success": context["initial"]["success"],
                    "first_success_step": context["first_success"],
                    "terminal_success": terminal,
                    "executed_steps": context["step"],
                    "trace_path": str(trace.relative_to(root)),
                    "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                    "controller_metadata": controller_metadata(env),
                }
            )
        context["env"].close()
        del checker
        for i, case in enumerate(cases):
            np.random.seed(3101)
            env, _wrapper = load_original(root, task)
            env.reset()
            actions, states, _ = read_controls(root, case)
            env.sim.set_state_from_flattened(states[0])
            env.sim.forward()
            initial_success = bool(env._check_success())
            trace = output / "traces" / f"{task}-{i}-direct.jsonl.gz"
            first_success = None
            with gzip.open(trace, "xt") as stream:
                for step, action in enumerate(actions, 1):
                    write_step(stream, env, action, step)
                    if env._check_success() and first_success is None:
                        first_success = step
            outcomes.append(
                {
                    "case": case,
                    "variant": "direct_controls_fresh_reset",
                    "initial_success": initial_success,
                    "first_success_step": first_success,
                    "terminal_success": bool(env._check_success()),
                    "executed_steps": len(actions),
                    "trace_path": str(trace.relative_to(root)),
                    "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                    "controller_metadata": controller_metadata(env),
                }
            )
            print(
                json.dumps(
                    {
                        "task": task,
                        "source_index": i,
                        "steps": len(actions),
                        "first_success_step": first_success,
                        "initial_success": initial_success,
                    }
                ),
                flush=True,
            )
            features.append(derived_features(root, env, case, len(features)))
            env.close()
    (output / "outcomes.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in outcomes)
    )
    (root / "derived/manifest.json").write_text(json.dumps(features, indent=2) + "\n")
    (output / "status.json").write_text(
        json.dumps(
            {
                "status": "COMPLETE_DIAGNOSTIC_ONLY",
                "executed_rows": len(outcomes),
                "derived_sources": len(features),
                "counted_controls": sum(r["executed_steps"] for r in outcomes),
                "source_checker_is_not_official_generator": True,
            },
            indent=2,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    run_sources(args.root)


if __name__ == "__main__":
    main()
