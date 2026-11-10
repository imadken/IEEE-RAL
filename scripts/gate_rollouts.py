"""Execute preregistered D5-D7 direct recovery trials with fresh prefix branches."""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import importlib.metadata
import json
import random
import sys
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mani_runner import make_env, record, scripted_action

from dual_rec.physical_faults import apply_fault
from dual_rec.replay import jsonable
from dual_rec.scenarios import (
    FailureScenario,
    Fault,
    HistoryFrame,
    ReplayRecipe,
    RobotObservation,
    failure_trigger,
    history_features,
    normalized_utility,
    recovery_action,
    split_seeds,
)
from dual_rec.validation import array, compare, max_difference, passes


def robot_observation(env, cube, obs, state) -> RobotObservation:
    robot = env.agent.robot
    return RobotObservation(
        task_state=jsonable(obs),
        cube_velocity=np.r_[
            array(cube.linear_velocity).ravel(), array(cube.angular_velocity).ravel()
        ].tolist(),
        drive_targets=array(robot.drive_targets).ravel().tolist(),
        drive_velocities=array(robot.drive_velocities).ravel().tolist(),
        joint_forces=array(robot.get_qf()).ravel().tolist(),
        link_wrenches=array(robot.get_link_incoming_joint_forces())[0].tolist(),
        robot_cube_contact=state["robot_object_contact"],
        time=state["time"],
    )


def fresh_environment(seed: int, fault: Fault):
    import torch
    from sapien.physx import PhysxRigidDynamicComponent

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    wrapped = make_env("PushCube-v1")
    try:
        obs, _ = wrapped.reset(seed=seed)
        env = wrapped.unwrapped
        if env.gpu_sim_enabled:
            raise RuntimeError("D5-D7 requires CPU physics")
        cube = env.obj
        body = cube._objs[0].find_component_by_type(PhysxRigidDynamicComponent)
        edit = apply_fault(body, fault)
        return wrapped, env, cube, obs, edit
    except Exception:
        wrapped.close()
        raise


def initial_execution(seed: int, fault: Fault, config: dict):
    wrapped, env, cube, obs, edit = fresh_environment(seed, fault)
    try:
        initial, goal = (
            array(cube.pose.p).reshape(3).copy(),
            array(env.goal_region.pose.p).reshape(3).copy(),
        )
        initial[1] += fault.alignment_y
        goal[1] += fault.alignment_y
        state = record(env, cube, obs)
        frames = [
            HistoryFrame(
                step=0,
                observation=robot_observation(env, cube, obs, state),
                action=[0.0] * 4,
            )
        ]
        records, actions = [state], []
        for phase, count in config["normal_schedule"]:
            for _ in range(count):
                action = scripted_action(
                    "PushCube-v1", initial, goal, env.agent.tcp.pose.p, phase
                )
                obs, _, _, _, _ = wrapped.step(action)
                actions.append(action.tolist())
                state = record(env, cube, obs)
                records.append(state)
                frames.append(
                    HistoryFrame(
                        step=len(actions),
                        observation=robot_observation(env, cube, obs, state),
                        action=action.tolist(),
                    )
                )
        return edit, frames, records, actions
    finally:
        wrapped.close()


def recovery_branch(
    scenario: FailureScenario,
    reference_records: list,
    recovery: str,
    config: dict,
    checks,
):
    recipe = scenario.recipe
    wrapped, env, cube, obs, edit = fresh_environment(
        recipe.seed, recipe.evaluation_only_fault
    )
    try:
        if edit.model_dump() != recipe.physical_edits[0].model_dump():
            raise RuntimeError("Physical edit reconstruction differs")
        errors, sensor_errors = [], []
        state = record(env, cube, obs)
        packet = robot_observation(env, cube, obs, state)
        errors.append(compare(reference_records[0], state))
        sensor_errors.append(
            max_difference(
                scenario.history[0].observation.model_dump(), packet.model_dump()
            )
        )
        for index, action in enumerate(recipe.prefix_actions, 1):
            obs, _, _, _, _ = wrapped.step(np.asarray(action, dtype=np.float32))
            state = record(env, cube, obs)
            packet = robot_observation(env, cube, obs, state)
            errors.append(compare(reference_records[index], state))
            sensor_errors.append(
                max_difference(
                    scenario.history[index].observation.model_dump(),
                    packet.model_dump(),
                )
            )
        parity = all(passes(e) for e in errors) and max(sensor_errors) <= 1e-4
        check = {
            "scenario_id": scenario.scenario_id,
            "seed": recipe.seed,
            "condition": recipe.evaluation_only_fault.name,
            "recovery": recovery,
            "passed": parity,
            "physical_edits_match": True,
            "independent_reconstruction": "new_environment_reset_full_prefix",
            "prefix_steps_compared": len(errors),
            "maxima": {
                k: max(e[k] for e in errors)
                for k in [
                    "position",
                    "angle",
                    "velocity",
                    "qpos",
                    "observation",
                    "time",
                ]
            },
            "sensor_max": max(sensor_errors),
            "contacts_agree": all(e["contacts"] for e in errors),
            "outcomes_agree": all(e["success"] for e in errors),
            "designated_replay_audit": recipe.seed in config["replay_seeds"],
        }
        checks.write(json.dumps(check, allow_nan=False) + "\n")
        checks.flush()
        if not parity:
            raise RuntimeError("Prefix branch mismatch: stop the D5-D7 gate")
        initial_tcp = np.asarray(packet.task_state.extra.tcp_pose[0][:3])
        actions, trace = [], []
        for step in range(config["recovery_horizon"]):
            action = recovery_action(packet, recovery, step, initial_tcp)
            obs, _, _, _, _ = wrapped.step(action)
            state = record(env, cube, obs)
            packet = robot_observation(env, cube, obs, state)
            actions.append(action.tolist())
            trace.append(
                {
                    "state": state,
                    "robot_observation": packet.model_dump(),
                    "action": action.tolist(),
                    "control_step": 79 + step,
                }
            )
        success = bool(trace[-1]["state"]["success"])
        outcome = {
            "scenario_id": scenario.scenario_id,
            "seed": recipe.seed,
            "split": scenario.split,
            "condition": recipe.evaluation_only_fault.name,
            "recovery": recovery,
            "failure_trigger": scenario.failure_trigger,
            "success": success,
            "utility": normalized_utility(success, actions, config["recovery_horizon"]),
            "steps": len(actions),
            "robot_contact_steps": sum(
                r["state"]["robot_object_contact"] for r in trace
            ),
            "final_position": trace[-1]["state"]["position"],
            "final_goal_distance_m": float(
                np.linalg.norm(
                    array(trace[-1]["state"]["position"])[:2]
                    - array(packet.task_state.extra.goal_pos[0])[:2]
                )
            ),
            "branch_check": check,
        }
        return outcome, trace
    finally:
        wrapped.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/gate_d5_d7.json"))
    parser.add_argument(
        "--split", choices=["development", "qualification"], required=True
    )
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes)
    split_seeds(config)
    seeds = config[args.split + "_seeds"][args.offset : args.offset + args.count]
    if not seeds or args.offset < 0 or not 1 <= args.count <= 40:
        parser.error("Invalid bounded seed selection")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "config.json").write_bytes(config_bytes)
    source = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ["src", "scripts"]
        for p in Path(folder).rglob("*.py")
    }
    versions = {
        n: importlib.metadata.version(n)
        for n in ["mani-skill", "sapien", "numpy", "torch"]
    }
    try:
        with (
            gzip.open(
                args.output / "scenarios.jsonl.gz", "xt", encoding="utf8"
            ) as scenarios,
            gzip.open(
                args.output / "recoveries.jsonl.gz", "xt", encoding="utf8"
            ) as recoveries,
            (args.output / "outcomes.jsonl").open("x") as outcomes,
            (args.output / "branch_checks.jsonl").open("x") as checks,
        ):
            for seed in seeds:
                for condition in config["conditions"]:
                    fault = Fault.model_validate(condition)
                    edit, history, records, actions = initial_execution(
                        seed, fault, config
                    )
                    scenario = FailureScenario(
                        scenario_id=f"{args.split}-{seed}-{fault.name}",
                        split=args.split,
                        recipe=ReplayRecipe(
                            seed=seed,
                            environment_versions=versions,
                            evaluation_only_fault=fault,
                            physical_edits=[edit],
                            prefix_actions=actions,
                            source_sha256=source,
                            config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                        ),
                        permitted_channels=list(RobotObservation.model_fields),
                        failure_trigger=failure_trigger(
                            records,
                            config["failure_window"],
                            config["failure_progress_m"],
                        ),
                        history=history,
                        branch_record=jsonable(records[-1]),
                    )
                    history_features(history)
                    scenarios.write(scenario.model_dump_json() + "\n")
                    scenarios.flush()
                    for recovery in config["recoveries"]:
                        outcome, trace = recovery_branch(
                            scenario, records, recovery, config, checks
                        )
                        outcomes.write(
                            json.dumps(jsonable(outcome), allow_nan=False) + "\n"
                        )
                        outcomes.flush()
                        recoveries.write(
                            json.dumps(
                                jsonable(
                                    {
                                        "scenario_id": scenario.scenario_id,
                                        "recovery": recovery,
                                        "trace": trace,
                                    }
                                ),
                                allow_nan=False,
                            )
                            + "\n"
                        )
                        recoveries.flush()
                    print(
                        f"{scenario.scenario_id}: failure={scenario.failure_trigger['failed']}",
                        flush=True,
                    )
                gc.collect()
        (args.output / "status.json").write_text(
            json.dumps(
                {
                    "status": "completed",
                    "split": args.split,
                    "seeds": seeds,
                    "conditions": len(config["conditions"]),
                    "recoveries": config["recoveries"],
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - retain failure evidence, then exit nonzero
        (args.output / "status.json").write_text(
            json.dumps(
                {
                    "status": "blocked_or_failed",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        )
        print(traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
