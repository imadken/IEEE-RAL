"""Bounded CPU contact qualification with explicit reconstruction modes."""

import json
import random
import time

import numpy as np

from dual_rec.replay import (
    ManiSkillReplay,
    Tolerances,
    distribution,
    jsonable,
    snapshot_data,
    snapshot_mismatches,
)
from dual_rec.validation import array, compare, passes


def scripted_action(task, cube_initial, goal, tcp, phase):
    cube, goal, tcp = (
        array(cube_initial).reshape(3),
        array(goal).reshape(3),
        array(tcp).reshape(3),
    )
    if task == "PushCube-v1":
        target = cube + [-0.055, 0, 0.12 if phase == 0 else 0]
        if phase >= 2:
            target = goal.copy()
            target[2] = cube[2]
        gripper = -1.0  # ManiSkill normalized gripper: -1 closes, +1 opens.
    else:
        target = cube + [0, 0, 0.12 if phase == 0 else 0]
        if phase >= 3:
            target = goal.copy()
        gripper = 1.0 if phase < 2 else -1.0
    # Panda pd_ee_delta_pos maps normalized +/-1 to +/-0.1 m.
    delta = np.clip((target - tcp) / 0.1, -0.25, 0.25)
    return np.r_[delta, gripper].astype(np.float32)


def record(env, cube, obs):
    contacts = []
    robot_contact = False
    robot_entities = {
        x.entity.name for link in env.agent.robot.links for x in link._objs
    }
    cube_entities = {x.name for x in cube._objs}
    for contact in env.scene.get_contacts():
        a, b = contact.bodies
        contacts.append(tuple(sorted((a.entity.name, b.entity.name))))
        ids = {a.entity.name, b.entity.name}
        robot_contact |= bool(ids & robot_entities and ids & cube_entities)
    pose = cube.pose.raw_pose.detach().cpu().numpy().reshape(7)
    return {
        "position": pose[:3],
        "quaternion": pose[3:],
        "qpos": env.agent.robot.get_qpos().detach().cpu().numpy(),
        "velocity": np.r_[
            array(cube.linear_velocity).ravel(),
            array(cube.angular_velocity).ravel(),
            array(env.agent.robot.get_qvel()).ravel(),
        ],
        "observation": jsonable(obs),
        "time": float(env.elapsed_steps[0]) / env.control_freq,
        "success": bool(env.evaluate()["success"][0]),
        "contacts": sorted(contacts),
        "robot_object_contact": bool(robot_contact),
    }


def make_env(task):
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401

    return gym.make(
        task,
        robot_uids="panda",
        num_envs=1,
        sim_backend="cpu",
        render_backend="none",
        obs_mode="state_dict",
        control_mode="pd_ee_delta_pos",
        max_episode_steps=150,
    )


def qualify(task, output, states, replay_mode="snapshot"):
    import torch

    tol = Tolerances()
    if replay_mode not in ("snapshot", "prefix"):
        raise ValueError("Unknown reconstruction mode")
    rows = []
    started = time.monotonic()
    for seed in range(states):
        if time.monotonic() - started > 1200:
            raise RuntimeError("20 minute qualification cap reached")
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        wrapped = make_env(task)
        try:
            obs, _ = wrapped.reset(seed=seed)
            env = wrapped.unwrapped
            cube = env.obj if task == "PushCube-v1" else env.cube
            goal_actor = env.goal_region if task == "PushCube-v1" else env.goal_site
            initial = array(cube.pose.p).reshape(3).copy()
            goal = array(goal_actor.pose.p).reshape(3).copy()
            adapter = ManiSkillReplay(wrapped)
            prefix, trace = [], []
            schedule = (
                [(0, 20), (1, 25), (2, 8)]
                if task == "PushCube-v1"
                else [(0, 20), (1, 25), (2, 15), (3, 5)]
            )
            for phase, steps in schedule:
                for _ in range(steps):
                    action = scripted_action(
                        task, initial, goal, env.agent.tcp.pose.p, phase
                    )
                    obs, _, _, _, _ = wrapped.step(action)
                    prefix.append(action.copy())
                    trace.append(record(env, cube, obs))
            snapshot = adapter.capture()
            before = record(env, cube, obs)
            actions, reference = [], []
            for _ in range(25):
                action = scripted_action(task, initial, goal, env.agent.tcp.pose.p, 3)
                obs, _, _, _, _ = wrapped.step(action)
                actions.append(action.copy())
                reference.append(record(env, cube, obs))
            if replay_mode == "snapshot":
                adapter.restore(snapshot)
                prefix_errors = []
            else:
                # Deliberate reconstruction mode: recreate the scene, reset the
                # seeded task, then execute every original action in order.
                random.seed(seed)
                np.random.seed(seed)
                torch.manual_seed(seed)
                obs, _ = wrapped.reset(seed=seed, options={"reconfigure": True})
                env = wrapped.unwrapped
                cube = env.obj if task == "PushCube-v1" else env.cube
                prefix_errors = []
                for action, ref in zip(prefix, trace, strict=True):
                    obs, _, _, _, _ = wrapped.step(action)
                    prefix_errors.append(compare(ref, record(env, cube, obs)))
            reconstructed_snapshot = adapter.capture()
            exposed_mismatches = snapshot_mismatches(snapshot, reconstructed_snapshot)
            restored_start = record(env, cube, env.get_obs())
            start_error = compare(before, restored_start)
            replay = []
            for action in actions:
                obs, _, _, _, _ = wrapped.step(action)
                replay.append(record(env, cube, obs))
            errors = [compare(a, b) for a, b in zip(reference, replay, strict=True)]
            replay_ok = (
                not exposed_mismatches
                and passes(start_error, tol)
                and all(passes(e, tol) for e in prefix_errors + errors)
            )
            contact_ok = any(r["robot_object_contact"] for r in trace + reference)
            row = {
                "seed": seed,
                "replay_mode": replay_mode,
                "snapshot": snapshot_data(snapshot),
                "reconstructed_snapshot": snapshot_data(reconstructed_snapshot),
                "exposed_state_mismatches": exposed_mismatches,
                "snapshot_state": jsonable(snapshot.physics),
                "snapshot_elapsed": jsonable(snapshot.custom["_elapsed_steps"]),
                "snapshot_torch_rng": jsonable(snapshot.custom["torch"]),
                "snapshot_numpy_rng": jsonable(snapshot.numpy),
                "snapshot_python_rng": jsonable(snapshot.python),
                "actions": {"prefix": prefix, "continuation": actions},
                "prefix": trace,
                "start": before,
                "restored_start": restored_start,
                "start_error": start_error,
                "reference": reference,
                "restored": replay,
                "errors": errors,
                "prefix_errors": prefix_errors,
                "replay_passed": replay_ok,
                "robot_object_contact": contact_ok,
            }
            rows.append(row)
            (output / f"{task}.raw.json").write_text(
                json.dumps(jsonable(rows), allow_nan=False)
            )
            print(
                f"{task} seed {seed}: replay={replay_ok}, robot contact={contact_ok}",
                flush=True,
            )
            if not replay_ok and replay_mode == "snapshot":
                # Source-informed fallback remains an engineering diagnostic.
                obs, _ = wrapped.reset(seed=seed, options={"reconfigure": True})
                env = wrapped.unwrapped
                cube = env.obj if task == "PushCube-v1" else env.cube
                for action in prefix:
                    obs, _, _, _, _ = wrapped.step(action)
                fallback = [compare(before, record(env, cube, obs))]
                for action, ref in zip(actions, reference, strict=True):
                    obs, _, _, _, _ = wrapped.step(action)
                    fallback.append(compare(ref, record(env, cube, obs)))
                (output / f"{task}.prefix_fallback.json").write_text(
                    json.dumps(jsonable(fallback))
                )
                raise RuntimeError(
                    "Snapshot mismatch; inspect prefix fallback and stop before experiments"
                )
            if not replay_ok:
                raise RuntimeError("Prefix reconstruction mismatch; stop qualification")
            if not contact_ok:
                raise RuntimeError(
                    "No robot/object contact: controller needs engineering adjustment; no qualification claim"
                )
        finally:
            wrapped.close()
    successes = sum(r["reference"][-1]["success"] for r in rows)
    return {
        "status": ("passed" if states == 20 else "smoke_passed")
        if successes > 0
        else "failed_task_behavior",
        "independent_states": len(rows),
        "replay_mode": replay_mode,
        "robot_contact_states": sum(r["robot_object_contact"] for r in rows),
        "successful_reference_rollouts": sum(
            r["reference"][-1]["success"] for r in rows
        ),
        "tolerances": tol.model_dump(),
        "errors": {
            k: distribution([e[k] for r in rows for e in r["errors"]])
            for k in ["position", "angle", "velocity", "observation", "qpos", "time"]
        },
        "immediate_errors": {
            k: distribution([r["start_error"][k] for r in rows])
            for k in ["position", "angle", "velocity", "observation", "qpos", "time"]
        },
        "outcome_agreement": sum(e["success"] for r in rows for e in r["errors"])
        / (25 * len(rows)),
        "contact_event_agreement": sum(e["contacts"] for r in rows for e in r["errors"])
        / (25 * len(rows)),
        "exposed_state_agreement": all(not r["exposed_state_mismatches"] for r in rows),
    }
