"""Bounded event-based PickCube calibration and independent recovery branches."""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import json
import random
import sys
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mani_runner import make_env, record, scripted_action

from dual_rec.overnight_pick import (
    PickFault,
    PickFrame,
    apply_pick_fault,
    event_trigger,
    pick_recovery,
    sensors,
)
from dual_rec.replay import jsonable
from dual_rec.scenarios import normalized_utility
from dual_rec.validation import array, compare, max_difference, passes


def fresh(seed, fault):
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    wrapped = make_env("PickCube-v1")
    # Permit the entire preregistered 90 + 70 step history without truncation.
    wrapped._max_episode_steps = 200
    try:
        obs, _ = wrapped.reset(seed=seed)
        env = wrapped.unwrapped
        edit = apply_pick_fault(env, fault)
        return wrapped, env, env.cube, obs, edit
    except Exception:
        wrapped.close()
        raise


def initial(seed, fault):
    wrapped, env, cube, obs, edit = fresh(seed, fault)
    try:
        p = array(cube.pose.p).reshape(3).copy()
        z = float(p[2])
        p[0] += fault.offset_x
        goal = array(env.goal_site.pose.p).reshape(3).copy()
        state = record(env, cube, obs)
        records = [state]
        frames = [
            PickFrame(step=0, action=[0] * 4, sensors=sensors(env, cube, obs, state))
        ]
        actions = []
        reason = None
        for phase, length in [(0, 20), (1, 25), (2, 15), (3, 30)]:
            for _ in range(length):
                action = scripted_action(
                    "PickCube-v1", p, goal, env.agent.tcp.pose.p, phase
                )
                obs, *_ = wrapped.step(action)
                actions.append(action.tolist())
                state = record(env, cube, obs)
                records.append(state)
                frames.append(
                    PickFrame(
                        step=len(actions),
                        action=action.tolist(),
                        sensors=sensors(env, cube, obs, state),
                    )
                )
                reason = None if state["success"] else event_trigger(frames, z)
                if reason:
                    break
            if reason:
                break
        row = {
            "seed": seed,
            "evaluation_only_fault": fault.model_dump(),
            "edit": edit,
            "prefix_actions": actions,
            "history": [f.model_dump() for f in frames],
            "branch_record": records[-1],
            "failure_event": reason,
            "failed": reason is not None,
            "initial_success": records[-1]["success"],
            "robot_contact_steps": sum(r["robot_object_contact"] for r in records),
            "decision_step": len(actions),
            "initial_cube_z": z,
        }
        return jsonable(row), records
    finally:
        wrapped.close()


def branch(case, reference, mode, horizon):
    fault = PickFault.model_validate(case["evaluation_only_fault"])
    wrapped, env, cube, obs, edit = fresh(case["seed"], fault)
    try:
        if edit != case["edit"]:
            raise RuntimeError("Physical replay readback mismatch")
        errors = []
        sensor_errors = []
        state = record(env, cube, obs)
        frame = PickFrame(
            step=0, action=[0] * 4, sensors=sensors(env, cube, obs, state)
        )
        errors.append(compare(reference[0], state))
        sensor_errors.append(
            max_difference(case["history"][0]["sensors"], frame.sensors.model_dump())
        )
        for index, action in enumerate(case["prefix_actions"], 1):
            obs, *_ = wrapped.step(np.asarray(action, dtype=np.float32))
            state = record(env, cube, obs)
            frame = PickFrame(
                step=index, action=action, sensors=sensors(env, cube, obs, state)
            )
            errors.append(compare(reference[index], state))
            sensor_errors.append(
                max_difference(
                    case["history"][index]["sensors"], frame.sensors.model_dump()
                )
            )
        check = {
            "passed": all(passes(e) for e in errors) and max(sensor_errors) <= 1e-4,
            "maxima": {
                key: max(e[key] for e in errors)
                for key in [
                    "position",
                    "angle",
                    "qpos",
                    "velocity",
                    "observation",
                    "time",
                ]
            },
            "sensor_max": max(sensor_errors),
            "contact_agreement": all(e["contacts"] for e in errors),
            "prefix_steps": len(errors),
        }
        if not check["passed"]:
            raise RuntimeError("GOLD_INTEGRITY_FAILURE " + json.dumps(check))
        tcp = np.asarray(frame.sensors.task_state.extra.tcp_pose[0][:3])
        actions = []
        trace = []
        for step in range(horizon):
            action = pick_recovery(frame, mode, step, tcp)
            obs, *_ = wrapped.step(action)
            state = record(env, cube, obs)
            frame = PickFrame(
                step=case["decision_step"] + step + 1,
                action=action.tolist(),
                sensors=sensors(env, cube, obs, state),
            )
            actions.append(action.tolist())
            trace.append(
                {
                    "state": state,
                    "sensors": frame.sensors.model_dump(),
                    "action": action,
                }
            )
        success = bool(state["success"])
        outcome = {
            "seed": case["seed"],
            "condition": fault.name,
            "recovery": mode,
            "initial_failed": case["failed"],
            "initial_success": case["initial_success"],
            "success": success,
            "utility": normalized_utility(success, actions, horizon),
            "horizon": horizon,
            "parity": check,
            "robot_contact_steps": sum(
                r["state"]["robot_object_contact"] for r in trace
            ),
            "final_position": state["position"],
        }
        return jsonable(outcome), jsonable(trace)
    finally:
        wrapped.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage", choices=["calibration", "development", "qualification"]
    )
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(Path("config/overnight_20261111.json").read_text())["d7b"]
    args.output.mkdir(parents=True, exist_ok=False)
    if args.stage == "calibration":
        seeds = cfg["calibration_seeds"]
        conditions = (
            [PickFault(name="nominal")]
            + [
                PickFault(name=f"friction-{mu}", friction=mu)
                for mu in cfg["friction_grid"]
            ]
            + [PickFault(name=f"offset-{d}", offset_x=d) for d in cfg["offset_grid_m"]]
        )
    else:
        if args.selection is None:
            parser.error("--selection required")
        selection = json.loads(args.selection.read_text())
        if selection["status"] != "SELECTED":
            raise RuntimeError("No credible calibrated fault pair")
        conditions = [
            PickFault(name="nominal"),
            PickFault(name="friction", friction=selection["friction"]),
            PickFault(name="offset", offset_x=selection["offset_x"]),
        ]
        seeds = cfg[args.stage + "_seeds"][args.offset : args.offset + args.count]
    if not seeds:
        parser.error("No selected seed groups")
    summary = []
    source = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ["src", "scripts", "config"]
        for p in Path(folder).rglob("*")
        if p.suffix in (".py", ".json")
    }
    try:
        with (
            gzip.open(
                args.output / "scenarios.jsonl.gz", "xt", encoding="utf8"
            ) as cases,
            gzip.open(args.output / "traces.jsonl.gz", "xt", encoding="utf8") as traces,
            (args.output / "outcomes.jsonl").open("x") as outcomes,
        ):
            for seed in seeds:
                for fault in conditions:
                    case, reference = initial(seed, fault)
                    case["source_sha256"] = source
                    cases.write(json.dumps(case, allow_nan=False) + "\n")
                    cases.flush()
                    compact = {
                        key: value
                        for key, value in case.items()
                        if key not in ["history", "prefix_actions", "source_sha256"]
                    }
                    summary.append(compact)
                    if args.stage != "calibration":
                        for recovery in cfg["recoveries"]:
                            result, trace = branch(
                                case, reference, recovery, cfg["horizon"]
                            )
                            outcomes.write(json.dumps(result, allow_nan=False) + "\n")
                            outcomes.flush()
                            traces.write(
                                json.dumps(
                                    {
                                        "seed": seed,
                                        "condition": fault.name,
                                        "recovery": recovery,
                                        "trace": trace,
                                    },
                                    allow_nan=False,
                                )
                                + "\n"
                            )
                            traces.flush()
                    print(
                        f"{args.stage} seed={seed} fault={fault.name} event={case['failure_event']} success={case['initial_success']}",
                        flush=True,
                    )
                gc.collect()
        (args.output / "initials.json").open("x").write(
            json.dumps(summary, indent=2, allow_nan=False)
        )
        (args.output / "status.json").open("x").write(
            json.dumps({"status": "completed", "seeds": seeds, "stage": args.stage})
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - preserve failed worker evidence, then stop
        (args.output / "status.json").open("x").write(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        )
        print(traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
