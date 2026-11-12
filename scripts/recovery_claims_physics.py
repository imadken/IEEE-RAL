"""New bounded parent-checkpoint executions using existing frozen robot controllers."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.metadata
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overnight_pick import initial
from overnight_replay import World, prefix_to_stage

from dual_rec.overnight_pick import PickFault, PickFrame, pick_recovery, sensors
from dual_rec.replay import jsonable, snapshot_data, snapshot_mismatches
from dual_rec.validation import array, compare, passes

PHYSICS_STEPS = 0
_BaseWorld = World


class World(_BaseWorld):
    def step(self, action):
        global PHYSICS_STEPS
        PHYSICS_STEPS += 1
        return super().step(action)

    def exposed(self):
        packet = super().exposed()
        custom = self.adapter.capture().custom
        packet["controller_memory"] = jsonable(
            {
                k: v
                for k, v in custom.items()
                if k.startswith(("controller", "gripper", "drive"))
            }
        )
        return packet


LOADED_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha(value):
    return hashlib.sha256(
        json.dumps(jsonable(value), sort_keys=True).encode()
    ).hexdigest()


def run_parent(task, seed, condition, root, split, negative=False):
    started = time.monotonic()
    start_steps = PHYSICS_STEPS
    w = World(task, seed, "misaligned" if condition == "misaligned" else "nominal")
    w.wrapped._max_episode_steps = 200
    traces = {}
    results = []
    worlds = [w]
    try:
        if task == "PickCube-v1":
            case, prefix_records = initial(
                seed,
                PickFault(
                    name=condition, offset_x=0.02 if condition == "offset002" else 0
                ),
            )
            prefix = case["prefix_actions"]
            for a in prefix:
                w.step(a)
            triggered = case["failed"]
        else:
            prefix, prefix_records, triggered, _ = prefix_to_stage(w, "transport")
        if task == "PushCube-v1":
            from dual_rec.scenarios import failure_trigger

            triggered = failure_trigger(prefix_records)["failed"]
        elif task == "Lift":
            triggered = False  # No registered Lift failure-event detector.
        start = w.state()
        snap = w.adapter.capture()
        model = {
            "task": task,
            "versions": {
                k: importlib.metadata.version(k)
                for k in ["mani-skill", "sapien", "robosuite", "mujoco"]
            },
            "edit": w.edit,
            "controller": "frozen existing source",
            "condition": condition,
        }
        model_id = sha(model)
        history_id = sha(prefix)
        start_id = sha(start)
        modes = ["continue", "recover"]
        horizon = 70
        for mode in modes:
            fresh = World(
                task, seed, "misaligned" if condition == "misaligned" else "nominal"
            )
            fresh.wrapped._max_episode_steps = 200
            worlds.append(fresh)
            reset_memory = fresh.adapter.capture()
            fresh_prefix = [fresh.state()]
            for a in prefix:
                fresh_prefix.append(fresh.step(a))
            prefix_ok = (
                fresh.edit == w.edit
                and len(fresh_prefix) == len(prefix_records)
                and all(
                    passes(compare(a, b))
                    for a, b in zip(prefix_records, fresh_prefix, strict=True)
                )
            )
            reference_controller = jsonable(fresh.adapter.capture().custom)
            actions = []
            ref = []
            frames = []
            tcp = (
                fresh.env.sim.data.site_xpos[
                    fresh.env.robots[0].eef_site_id["right"]
                ].copy()
                if task == "Lift"
                else array(fresh.env.agent.tcp.pose.p).reshape(3)
            )
            for j in range(horizon):
                if task == "PickCube-v1":
                    obs = fresh.obs
                    state = fresh.state()
                    frame = PickFrame(
                        step=j,
                        action=[0] * 4,
                        sensors=sensors(fresh.env, fresh.cube, obs, state),
                    )
                    a = pick_recovery(
                        frame, "nominal" if mode == "continue" else "regrasp", j, tcp
                    )
                else:
                    a = fresh.continuation(
                        "nominal" if mode == "continue" else "alternative", j, tcp
                    )
                actions.append(a.copy())
                ref.append(fresh.step(a))
                frames.append(
                    {
                        "state": ref[-1],
                        "control": fresh.exposed(),
                        "integration": jsonable(fresh.adapter.capture().physics),
                    }
                )
            key = f"{mode}/reference"
            traces[key] = {
                "start": jsonable(fresh_prefix[-1]),
                "prefix_history": jsonable(fresh_prefix),
                "controller_memory": reference_controller,
                "frames": jsonable(frames),
                "actions": jsonable(actions),
                "prefix_ok": prefix_ok,
            }
            routes = ["native_snapshot", "fresh_prefix"]
            if negative:
                routes += [
                    "controller_memory",
                    "physics",
                    "action_order",
                    "midrollout_injection",
                ]
            for route in routes:
                route_started = time.monotonic()
                if route in ("fresh_prefix", "physics"):
                    candidate = World(
                        task,
                        seed,
                        "misaligned" if condition == "misaligned" else "nominal",
                    )
                    candidate.wrapped._max_episode_steps = 200
                    worlds.append(candidate)
                    candidate_prefix = [candidate.state()]
                    for a in prefix:
                        candidate_prefix.append(candidate.step(a))
                else:
                    candidate_prefix = []
                    candidate = w
                    candidate.adapter.restore(snap)
                violation = None
                missing = []
                readback = None
                if route == "controller_memory":
                    if task == "Lift":
                        partial = copy.deepcopy(snap)
                        for name in partial.custom:
                            if name.startswith(("controller", "gripper")):
                                partial.custom[name] = copy.deepcopy(
                                    reset_memory.custom[name]
                                )
                        candidate.adapter.restore(partial)
                        violation = "controller/gripper memory replaced by reset memory"
                    else:
                        candidate.env.agent.reset()
                        violation = "controller reset after checkpoint"
                if route == "physics":
                    if task == "Lift":
                        old = candidate.adapter.model.geom_friction.copy()
                        candidate.adapter.model.geom_friction[:, :2] *= 0.5
                        readback = {
                            "before": old.tolist(),
                            "after": candidate.adapter.model.geom_friction.tolist(),
                        }
                    else:
                        from sapien.physx import PhysxRigidDynamicComponent

                        from dual_rec.physical_faults import apply_fault
                        from dual_rec.scenarios import Fault

                        body = candidate.cube._objs[0].find_component_by_type(
                            PhysxRigidDynamicComponent
                        )
                        readback = apply_fault(
                            body, Fault(name="negative", mass_scale=1, friction=0.01)
                        ).model_dump()
                    violation = "physical friction changed across branches"
                actual = [a.copy() for a in actions]
                if route == "action_order":
                    actual = list(reversed(actual))
                    violation = (
                        "action order reversed"
                        if any(
                            not np.array_equal(a, b)
                            for a, b in zip(actual, actions, strict=True)
                        )
                        else None
                    )
                exposed_mismatches = (
                    snapshot_mismatches(snap, candidate.adapter.capture())
                    if candidate is w
                    else []
                )
                input_memory_mismatches = [
                    field
                    for field in exposed_mismatches
                    if field.startswith("custom/")
                    or field in ("python_rng", "numpy_rng")
                ]
                if input_memory_mismatches and violation is None:
                    violation = "controller/RNG restoration mismatch: " + ", ".join(
                        input_memory_mismatches
                    )
                candidate_start = candidate.state(refresh=True)
                start_custom = jsonable(candidate.adapter.capture().custom)
                tested = []
                recorded = []
                for j, a in enumerate(actual):
                    tested.append(candidate.step(a))
                    recorded.append(
                        {
                            "state": tested[-1],
                            "control": candidate.exposed(),
                            "integration": jsonable(
                                candidate.adapter.capture().physics
                            ),
                        }
                    )
                    if route == "midrollout_injection" and j == 0:
                        candidate.adapter.restore(snap)
                        violation = "state reinjected after first action"
                errors = [compare(a, b) for a, b in zip(ref, tested, strict=True)]
                normalized = []
                for e in errors:
                    normalized.append(
                        max(
                            e["position"] / 1e-5,
                            e["angle"] / 1e-4,
                            e["velocity"] / 1e-4,
                            e["qpos"] / 1e-4,
                            e["observation"] / 1e-4,
                            e["time"] / 1e-9,
                            0 if e["contacts"] else 2,
                            0 if e["success"] else 2,
                        )
                    )
                if candidate is w and task != "Lift":
                    missing = ["hidden PhysX solver state"]
                row = {
                    "task": task,
                    "seed": seed,
                    "split": split,
                    "condition": condition,
                    "action": mode,
                    "route": route,
                    "prefix_ok": prefix_ok,
                    "initial_success": bool(start["success"]),
                    "triggered": bool(triggered),
                    "model_hash": model_id,
                    "history_hash": history_id,
                    "start_hash": start_id,
                    "model": model,
                    "violation": violation,
                    "missing": missing,
                    "exposed_snapshot_mismatches": exposed_mismatches,
                    "first_divergence": next(
                        (i for i, e in enumerate(normalized) if e > 1), None
                    ),
                    "state_errors": normalized,
                    "success": bool(tested[-1]["success"]),
                    "first_hit": next(
                        (j + 1 for j, s in enumerate(tested) if s["success"]), None
                    ),
                    "reference_success": bool(ref[-1]["success"]),
                    "reference_first_hit": next(
                        (j + 1 for j, s in enumerate(ref) if s["success"]), None
                    ),
                    "actions": jsonable(actual),
                    "expected_actions": jsonable(actions),
                    "times": [s["time"] for s in tested],
                    "reference_times": [s["time"] for s in ref],
                    "readback": readback,
                    "cost_seconds": horizon * 0.05,
                    "reference_cost_seconds": horizon * 0.05,
                    "continuations_executed": 1,
                    "route_wall_seconds": time.monotonic() - route_started,
                    "prefix_controls_executed": len(prefix)
                    if route in ("fresh_prefix", "physics")
                    else 0,
                }
                traces[f"{mode}/{route}"] = {
                    "start": jsonable(candidate_start),
                    "controller_memory": start_custom,
                    "prefix_history": jsonable(candidate_prefix),
                    "frames": jsonable(recorded),
                    "row": row,
                }
                results.append(row)
                if route == "physics":
                    if task == "Lift":
                        candidate.adapter.model.geom_friction[:] = old
                    else:
                        # No later branches reuse edited material: stop this world's
                        # negative suite after collecting all other variants first.
                        pass
                if route in ("fresh_prefix", "physics"):
                    candidate.close()
                    worlds.remove(candidate)
            fresh.close()
            worlds.remove(fresh)
        # Mechanical record-level controls use executed records, never outcome edits.
        if negative:
            for name in ["missing_provenance"]:
                row = copy.deepcopy(
                    next(
                        r
                        for r in results
                        if r["route"] == "fresh_prefix" and r["action"] == "recover"
                    )
                )
                row["route"] = name
                row["continuations_executed"] = 0
                if name == "parent_rng":
                    row["violation"] = "paired history hash deliberately mismatched"
                    row["paired_history_hash"] = "another-parent-required"
                else:
                    row["model_hash"] = None
                    row["missing"] = ["model/controller provenance removed"]
                results.append(row)
        directory = root / "parents" / split / task / f"{seed}-{condition}"
        directory.mkdir(parents=True, exist_ok=False)
        with gzip.open(directory / "traces.json.gz", "wt") as f:
            json.dump(
                jsonable(
                    {
                        "prefix": prefix_records,
                        "prefix_actions": prefix,
                        "snapshot": snapshot_data(snap),
                        "traces": traces,
                    }
                ),
                f,
            )
        (directory / "outcomes.json").write_text(
            json.dumps(jsonable(results), indent=2)
        )
        (directory / "checkpoint.json").write_text(
            json.dumps(
                {
                    "wall_seconds": time.monotonic() - started,
                    "physics_control_steps": PHYSICS_STEPS
                    - start_steps
                    + (len(prefix) if task == "PickCube-v1" else 0),
                    "physical_continuations": sum(
                        r["continuations_executed"] for r in results
                    )
                    + 2,
                    "source_sha256": LOADED_SOURCE_HASH,
                    "outcomes_sha256": hashlib.sha256(
                        (directory / "outcomes.json").read_bytes()
                    ).hexdigest(),
                },
                indent=2,
            )
        )
        print(
            json.dumps(
                {
                    "task": task,
                    "seed": seed,
                    "condition": condition,
                    "rows": len(results),
                    "prefix_ok": all(r["prefix_ok"] for r in results),
                }
            ),
            flush=True,
        )
    finally:
        for world in worlds:
            world.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--split", choices=["development", "confirmation"], required=True)
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--seed", type=int)
    p.add_argument("--condition")
    a = p.parse_args()
    cfg = json.loads((a.root / "registration.json").read_text())
    assert not (a.root / "completion_manifest.json").exists()
    for seed in (
        [a.seed] if a.seed is not None else cfg["seeds"][a.task][a.split][: a.count]
    ):
        for condition in [a.condition] if a.condition else cfg["conditions"][a.task]:
            assert (
                seed in cfg["seeds"][a.task][a.split]
                and condition in cfg["conditions"][a.task]
            )
            if (
                a.root
                / "parents"
                / a.split
                / a.task
                / f"{seed}-{condition}"
                / "checkpoint.json"
            ).exists():
                continue
            run_parent(a.task, seed, condition, a.root, a.split, negative=True)


if __name__ == "__main__":
    main()
