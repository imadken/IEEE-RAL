"""Bounded D4 qualification. Exit nonzero on blocked or failed engineering gates."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np

from dual_rec.replay import (
    RobosuiteReplay,
    Tolerances,
    distribution,
    jsonable,
    quat_error,
)


def make_lift(seed):
    import robosuite as suite
    from robosuite.controllers import load_composite_controller_config

    cfg = load_composite_controller_config(controller="BASIC")
    return suite.make(
        "Lift",
        robots="Panda",
        has_renderer=False,
        has_offscreen_renderer=False,
        use_camera_obs=False,
        controller_configs=cfg,
        hard_reset=False,
        seed=seed,
        horizon=200,
        reward_shaping=False,
    )


def action(env, phase):
    """Scripted OSC approach, descend, close, lift. Privileged task location
    is used only for engineering qualification, never a deployed policy input.
    """
    pos = env.sim.data.body_xpos[env.cube_body_id].copy()
    target = pos + [0, 0, 0.12 if phase == 0 else 0.005]
    if phase >= 3:
        target = np.array([env._qual_target[0], env._qual_target[1], 0.98])
    current = env.sim.data.site_xpos[env.robots[0].eef_site_id["right"]]
    a = np.zeros(env.action_dim)
    a[:3] = np.clip((target - current) / 0.05, -0.6, 0.6)
    a[-1] = -1 if phase < 2 else 1
    return a


def compare(a, b):
    obs_error = max(
        float(
            np.max(
                np.abs(
                    np.asarray(a["observation"][k]) - np.asarray(b["observation"][k])
                )
            )
        )
        for k in a["observation"]
    )
    return {
        "position": float(np.linalg.norm(a["position"] - b["position"])),
        "angle": quat_error(a["quaternion"], b["quaternion"]),
        "velocity": float(np.max(np.abs(a["velocity"] - b["velocity"]))),
        "qpos": float(np.max(np.abs(a["qpos"] - b["qpos"]))),
        "observation": obs_error,
        "success": a["success"] == b["success"],
        "contacts": a["contacts"] == b["contacts"],
    }


def lift(output, states):
    tol = Tolerances()
    results = []
    started = time.monotonic()
    for seed in range(states):
        if time.monotonic() - started > 1200:
            raise RuntimeError("Qualification exceeded its 20-minute wall cap")
        random.seed(seed)
        np.random.seed(seed)
        env = make_lift(seed)
        try:
            obs = env.reset()
            env._qual_target = env.sim.data.body_xpos[env.cube_body_id].copy()
            adapter = RobosuiteReplay(env)
            prefix, prefix_records = [], []
            # Branch during closed-gripper lift, not at a trivial reset state.
            for phase, length in [(0, 20), (1, 25), (2, 15), (3, 5)]:
                for _ in range(length):
                    a = action(env, phase)
                    obs, _, _, _ = env.step(a)
                    prefix.append(a.copy())
                    prefix_records.append(adapter.record(obs))
            snapshot = adapter.capture()
            start_record = adapter.record(obs)
            suffix, reference = [], []
            for _ in range(25):
                a = action(env, 3)
                obs, _, _, _ = env.step(a)
                suffix.append(a.copy())
                reference.append(adapter.record(obs))
            adapter.restore(snapshot)
            replay = []
            for a in suffix:
                obs, _, _, _ = env.step(a)
                replay.append(adapter.record(obs))
            errors = [compare(a, b) for a, b in zip(reference, replay, strict=True)]
            passed = all(
                e["position"] <= tol.position
                and e["angle"] <= tol.angle
                and e["velocity"] <= tol.velocity
                and e["observation"] <= tol.observation
                and e["qpos"] <= tol.angle
                and e["success"]
                and e["contacts"]
                for e in errors
            )
            contacts = sum(bool(r["contacts"]) for r in prefix_records + reference)
            row = {
                "seed": seed,
                "passed": passed,
                "errors": errors,
                "contact_steps": contacts,
                "start": start_record,
                "reference": reference,
                "restored": replay,
                "prefix_records": prefix_records,
                "actions": {"prefix": prefix, "suffix": suffix},
                "snapshot": {
                    "integration": snapshot.physics,
                    "custom": snapshot.custom,
                    "python_rng": snapshot.python,
                    "numpy_rng": snapshot.numpy,
                },
            }
            results.append(row)
            print(
                f"Lift seed {seed}: replay={passed}, contact_steps={contacts}",
                flush=True,
            )
            # Persist partial evidence even on a failed gate. No unchanged retries.
            (output / "Lift.raw.json").write_text(
                json.dumps(jsonable(results), allow_nan=False)
            )
            if not passed:
                # Approved deterministic-from-seed fallback, including action prefix.
                other = make_lift(seed)
                try:
                    obs = other.reset()
                    alt = RobosuiteReplay(other)
                    for a in prefix:
                        obs, _, _, _ = other.step(a)
                    fallback = [compare(start_record, alt.record(obs))]
                    for a, ref in zip(suffix, reference, strict=True):
                        obs, _, _, _ = other.step(a)
                        fallback.append(compare(ref, alt.record(obs)))
                    (output / "Lift.prefix_fallback.json").write_text(
                        json.dumps(jsonable(fallback))
                    )
                finally:
                    other.close()
                raise RuntimeError(
                    "Snapshot replay diverged; stopped qualification. See prefix fallback."
                )
        finally:
            env.close()
    metrics = {
        k: distribution([e[k] for row in results for e in row["errors"]])
        for k in ["position", "angle", "velocity", "qpos", "observation"]
    }
    qualified = all(r["contact_steps"] > 0 for r in results)
    return {
        "status": "passed" if qualified else "failed_contact_coverage",
        "independent_states": len(results),
        "paired_rollouts": 2 * len(results),
        "outcome_agreement": sum(e["success"] for r in results for e in r["errors"])
        / (25 * len(results)),
        "contact_event_agreement": sum(
            e["contacts"] for r in results for e in r["errors"]
        )
        / (25 * len(results)),
        "successful_reference_rollouts": sum(
            r["reference"][-1]["success"] for r in results
        ),
        "tolerances": tol.model_dump(),
        "errors": metrics,
        "wall_seconds": time.monotonic() - started,
    }


def mani(task, output):
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401

    env = None
    try:
        env = gym.make(
            task,
            robot_uids="panda",
            sim_backend="cpu",
            render_backend="none",
            obs_mode="state_dict",
            control_mode="pd_ee_delta_pos",
        )
        env.reset(seed=0)
        return {
            "status": "startup_only",
            "replay_states": 0,
            "reason": "CPU startup succeeded; full contact qualification remains required",
        }
    finally:
        if env is not None:
            env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task", choices=["Lift", "PushCube-v1", "PickCube-v1"], required=True
    )
    parser.add_argument("--states", type=int, default=20, choices=range(1, 21))
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        result = (
            lift(args.output, args.states)
            if args.task == "Lift"
            else mani(args.task, args.output)
        )
    except Exception as exc:  # noqa: BLE001 - record startup failures before exiting nonzero
        import traceback

        result = {
            "status": "blocked_or_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    result.update(
        task=args.task,
        requested_states=args.states,
        wall_seconds=time.monotonic() - started,
        versions={
            n: importlib.metadata.version(n)
            for n in ["mani-skill", "sapien", "robosuite", "mujoco", "torch", "numpy"]
        },
        platform={
            "python": sys.version,
            "cpu_count": os.cpu_count(),
            "gpu_tested": False,
        },
    )
    (args.output / f"{args.task}.metrics.json").write_text(
        json.dumps(result, indent=2, allow_nan=False)
    )
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
