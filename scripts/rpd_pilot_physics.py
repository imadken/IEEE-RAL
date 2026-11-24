"""Only the registered ten-parent native probe/hold technical pilots.

Every branch constructs a fresh evaluator episode and replays the original prefix.
There is no checkpoint restore, within-history reset or learned controller.
"""

import argparse
import gc
import json
import lzma
import os
import time
import traceback

import numpy as np
from dsre_paper_physics import action_for
from overnight_replay import World, prefix_to_stage
from rpd_pilot_common import (
    BASE,
    HOLD,
    PREFIX,
    TASKS,
    read_rows,
    sha,
    verify_registration,
    write_json,
)

from dual_rec.recoverability.adapters import (
    encode_response,
    mask_native_state,
    probe_commands,
)
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes


def memory(world):
    controller = world.env.agent.controller
    return jsonable(
        {
            "state": world.env.agent.get_controller_state(),
            "transient": {
                name: {
                    key: getattr(ctrl, key)
                    for key in (
                        "_step",
                        "_start_qpos",
                        "_target_qpos",
                        "_step_size",
                        "_target_pose",
                    )
                    if hasattr(ctrl, key)
                }
                for name, ctrl in controller.controllers.items()
            },
            "drive_targets": world.env.agent.robot.drive_targets,
            "drive_velocities": world.env.agent.robot.drive_velocities,
        }
    )


class PilotWorld(World):
    def __init__(self, task, seed):
        super().__init__(task, seed, "nominal")
        self.wrapped._max_episode_steps = 200
        self.records = []
        self.actions = []
        self.flags = {"terminated": False, "truncated": False}
        self.capture()

    def capture(self):
        state = jsonable(self.state())
        state["controller_memory"] = memory(self)
        state["native_task_flags"] = jsonable(self.env.evaluate())
        state["wrapper_flags"] = dict(self.flags)
        # Contact points are native solver evidence for the evaluator, never sensors.
        robots = {
            x.entity.name for link in self.env.agent.robot.links for x in link._objs
        }
        cubes = {x.name for x in self.cube._objs}
        actual = []
        for contact in self.env.scene.get_contacts():
            names = [b.entity.name for b in contact.bodies]
            if set(names) & robots and set(names) & cubes:
                actual.append(
                    {
                        "bodies": sorted(names),
                        "points": [
                            {
                                "position": jsonable(p.position),
                                "separation": float(p.separation),
                                "impulse": jsonable(p.impulse),
                                "normal": jsonable(p.normal),
                            }
                            for p in contact.points
                        ],
                    }
                )
        state["evaluator_robot_object_contacts"] = actual
        state["planner_frame"] = mask_native_state(state).model_dump(mode="json")
        self.records.append(state)
        return state

    def step(self, action):
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (4,) or not np.isfinite(action).all():
            raise ValueError("Invalid native actuator command")
        self.obs, _, terminated, truncated, _ = self.wrapped.step(action)
        self.flags = {
            "terminated": bool(array(terminated).reshape(-1)[0]),
            "truncated": bool(array(truncated).reshape(-1)[0]),
        }
        self.actions.append(action.tolist())
        state = self.capture()
        if self.flags["truncated"]:
            raise ValueError("SOURCE_HORIZON_TRUNCATION")
        return state


def same_path(a, b):
    if len(a) != len(b):
        return {"passed": False, "reason": "length"}
    errors = [compare(x, y) for x, y in zip(a, b, strict=True)]
    memories = all(
        x["controller_memory"] == y["controller_memory"]
        for x, y in zip(a, b, strict=True)
    )
    flags = all(
        x["native_task_flags"] == y["native_task_flags"]
        and x["wrapper_flags"] == y["wrapper_flags"]
        for x, y in zip(a, b, strict=True)
    )
    return {
        "passed": all(passes(e) for e in errors) and memories and flags,
        "controller_memory_equal": memories,
        "task_and_wrapper_flags_equal": flags,
        "max_errors": {
            k: max(e[k] for e in errors)
            for k in ("position", "angle", "velocity", "qpos", "observation", "time")
        },
        "contacts_equal": all(e["contacts"] for e in errors),
        "frames": len(a),
    }


def execute(row, canonical, deadline):
    started = time.monotonic()
    world = None
    result = {
        "row": row.model_dump(mode="json"),
        "status": "FAILED",
        "failure": None,
        "runtime_seconds": None,
        "records": [],
        "actions": [],
        "probe_observations": [],
        "source_checkpoint_qualified": False,
        "macro_end_success": None,
        "deadline_success": None,
        "physics_wall_start_epoch": time.time(),
    }
    try:
        world = PilotWorld(row.parent.task, row.parent.seed)
        result["startup_seconds"] = time.monotonic() - started
        assert (
            world.env.control_freq == 20 and world.env.control_mode == "pd_ee_delta_pos"
        )
        assert not world.env.gpu_sim_enabled and world.wrapped._max_episode_steps == 200
        result["source_runtime"] = {
            "control_hz": world.env.control_freq,
            "control_mode": world.env.control_mode,
            "max_episode_steps": world.wrapped._max_episode_steps,
            "cube_half_size": float(world.env.cube_half_size),
            "joint_limits": jsonable(world.env.agent.robot.get_qlimits()),
            "physical_edit": jsonable(world.edit),
            "controller_config": {
                name: repr(c.config)
                for name, c in world.env.agent.controller.controllers.items()
            },
        }
        if canonical is None:
            _, _, reached, detail = prefix_to_stage(world, "transport")
            result["checkpoint_contact_reached"] = reached
            result["checkpoint_detail"] = detail
        else:
            for action in canonical["actions"][: PREFIX[row.parent.task]]:
                if time.monotonic() >= deadline:
                    raise TimeoutError("PHYSICS_CAP")
                world.step(action)
            result["checkpoint_contact_reached"] = any(
                s["robot_object_contact"] for s in world.records
            )
        assert len(world.actions) == PREFIX[row.parent.task], "SOURCE_CHECKPOINT_CLOCK"
        assert abs(world.records[-1]["time"] - PREFIX[row.parent.task] / 20) <= 1e-9
        root = world.records[-1]
        result["root_controller_custom"] = jsonable(world.adapter.capture().custom)
        if canonical is not None:
            result["prefix_replay"] = same_path(
                canonical["records"][: PREFIX[row.parent.task] + 1], world.records
            )
            assert result["prefix_replay"]["passed"], "SOURCE_PREFIX_REPLAY_FAILURE"
            assert (
                result["root_controller_custom"] == canonical["root_controller_custom"]
            ), "SOURCE_FULL_CONTROLLER_MEMORY_FAILURE"
            assert result["source_runtime"] == canonical["source_runtime"], (
                "SOURCE_CONTROLLER_TASK_CONFIGURATION_FAILURE"
            )
        if root["success"]:
            result["status"] = "INELIGIBLE_ALREADY_COMPLETE"
            return result
        assert result["checkpoint_contact_reached"], "SOURCE_PREFIX_CONTACT_NOT_REACHED"
        result["source_checkpoint_qualified"] = True
        suffix_start = len(world.records) - 1
        last_grip = -1.0
        for probe in row.history:
            commands = (
                (HOLD,) * (10 if probe == "neutral10" else 20)
                if probe.startswith("neutral")
                else probe_commands(row.parent.task, probe)
            )
            before = len(world.records) - 1
            for command in commands:
                if time.monotonic() >= deadline:
                    raise TimeoutError("PHYSICS_CAP")
                world.step(command)
                last_grip = command[-1]
            if not probe.startswith("neutral"):
                frames = tuple(mask_native_state(s) for s in world.records[before:])
                result["probe_observations"].append(
                    {
                        "probe": probe,
                        "response": encode_response(frames).model_dump(mode="json"),
                        "start_control": before,
                        "end_control": len(world.records) - 1,
                    }
                )
        result["post_history_control"] = len(world.actions)
        tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
        for j in range(row.macro_ticks):
            if time.monotonic() >= deadline:
                raise TimeoutError("PHYSICS_CAP")
            command = action_for(world, row.endpoint, j, tcp)
            world.step(command)
            last_grip = float(command[-1])
        if row.macro_ticks:
            result["macro_end_control"] = len(world.actions)
            result["macro_end_success"] = world.records[-1]["success"]
        while len(world.actions) - suffix_start < 90:
            if time.monotonic() >= deadline:
                raise TimeoutError("PHYSICS_CAP")
            world.step((0.0, 0.0, 0.0, last_grip))
        assert len(world.actions) == PREFIX[row.parent.task] + 90
        result["deadline_success"] = world.records[-1]["success"]
        result["status"] = "COMPLETE"
    except Exception as error:  # noqa: BLE001 - failed native attempts remain raw evidence and stop the family.
        result["failure"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
    finally:
        if world is not None:
            result["records"] = world.records
            result["actions"] = world.actions
            world.close()
        result["runtime_seconds"] = time.monotonic() - started
    return result


def save_raw(path, value):
    assert not path.exists() and not path.with_suffix(".partial").exists()
    temporary = path.with_suffix(".partial")
    with lzma.open(temporary, "xt", preset=3) as stream:
        json.dump(value, stream, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    os.rename(temporary, path)
    return sha(path)


def run(task):
    verify_registration()
    task_dir = BASE / "physics" / task
    task_dir.mkdir(parents=True, exist_ok=True)
    # A single family invocation; clean resume only from its immutable per-row files.
    rows = [r for r in read_rows() if r.parent.task == task]
    invocation_start = time.monotonic()
    logs = sorted(task_dir.glob("invocation_*.json"))
    prior_seconds = sum(json.loads(p.read_text())["worker_wall_seconds"] for p in logs)
    assert prior_seconds < 10800
    deadline = invocation_start + (10800 - prior_seconds)
    row_times = []
    attempted = 0
    stop = None
    run_id = len(logs)
    # An interrupted started row is never silently rerun: its missing outcome is retained.
    for marker in task_dir.glob("**/*.started.json"):
        if not marker.with_name(
            marker.name.replace(".started.json", ".json.xz")
        ).exists():
            stop = "INTERRUPTED_ATOMIC_ROW_REQUIRES_AUDIT_NO_RERUN"
    try:
        for index in range(10):
            if stop:
                break
            selected = [r for r in rows if r.parent.index == index]
            directory = task_dir / f"parent_{index:02d}"
            directory.mkdir(exist_ok=True)
            if (directory / "parent_seal.json").exists():
                seal = json.loads((directory / "parent_seal.json").read_text())
                for name, expected in seal["raw_sha256"].items():
                    assert sha(directory / name) == expected
                if seal["status"] != "COMPLETE":
                    stop = seal["status"]
                continue
            if (
                row_times
                and time.monotonic() + max(row_times) * 54 * 1.2 + 10 >= deadline
            ):
                stop = "CAP_FORECAST_AT_ATOMIC_PARENT_BOUNDARY"
                break
            if (
                sum(p.stat().st_size for p in task_dir.rglob("*") if p.is_file())
                + 100 * 1024**2
                >= 3 * 1024**3
            ):
                stop = "STORAGE_FORECAST_AT_ATOMIC_PARENT_BOUNDARY"
                break
            canonical = None
            repeated = {}
            raw_sha = {}
            parent_status = "COMPLETE"
            for row in selected:
                path = directory / (row.row_id + ".json.xz")
                if path.exists():
                    with lzma.open(path, "rt") as stream:
                        result = json.load(stream)
                else:
                    marker = directory / (row.row_id + ".started.json")
                    write_json(
                        marker,
                        {
                            "row_id": row.row_id,
                            "start_epoch": time.time(),
                            "invocation": run_id,
                            "resume_policy": "No repeat if started row lacks canonical result",
                        },
                    )
                    result = execute(row, canonical, deadline)
                    attempted += 1
                    row_times.append(result["runtime_seconds"])
                    if result["status"] == "COMPLETE" and row.repeat == 1:
                        first = repeated[(row.history, row.endpoint)]
                        result["repeat_replay"] = same_path(
                            first["records"], result["records"]
                        )
                        if not result["repeat_replay"]["passed"]:
                            result["status"] = "FAILED"
                            result["failure"] = {
                                "message": "SOURCE_FULL_HISTORY_REPEAT_FAILURE"
                            }
                    save_raw(path, result)
                    print(
                        json.dumps(
                            {
                                "task": task,
                                "parent": index,
                                "history": row.history,
                                "endpoint": row.endpoint,
                                "repeat": row.repeat,
                                "status": result["status"],
                                "wall_seconds": round(result["runtime_seconds"], 3),
                                "macro_end": result["macro_end_success"],
                                "deadline": result["deadline_success"],
                            }
                        ),
                        flush=True,
                    )
                raw_sha[path.name] = sha(path)
                if canonical is None:
                    canonical = result
                if result["status"] != "COMPLETE":
                    parent_status = result["status"]
                    stop = result["status"] + ":" + str(result.get("failure"))
                    break
                if row.repeat == 0:
                    repeated[(row.history, row.endpoint)] = result
            write_json(
                directory / "parent_seal.json",
                {
                    "parent": selected[0].parent.model_dump(),
                    "status": parent_status,
                    "raw_sha256": raw_sha,
                    "planned_rows": 54,
                    "available_rows": len(raw_sha),
                    "remaining_rows": 54 - len(raw_sha),
                    "seal_epoch": time.time(),
                },
            )
            print("ATOMIC_PARENT", task, index, parent_status, flush=True)
            gc.collect()
    finally:
        write_json(
            task_dir / f"invocation_{run_id:03d}.json",
            {
                "task": task,
                "worker_wall_seconds": time.monotonic() - invocation_start,
                "attempted_rows_this_invocation": attempted,
                "prior_worker_seconds": prior_seconds,
                "stop_reason": stop,
                "cap_seconds": 10800,
                "new_stage2_parents": 0,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=TASKS, required=True)
    run(parser.parse_args().task)
