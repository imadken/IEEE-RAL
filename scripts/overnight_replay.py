"""Preregistered native/GOLD/unchanged-snapshot counterfactual validity audit."""

from __future__ import annotations

import argparse
import gc
import gzip
import json
import random
import sys
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mani_runner import make_env, record, scripted_action
from qualify import action as lift_action
from qualify import make_lift

from dual_rec.overnight_pick import PickFault, apply_pick_fault
from dual_rec.physical_faults import apply_fault
from dual_rec.replay import (
    ManiSkillReplay,
    RobosuiteReplay,
    jsonable,
    snapshot_mismatches,
)
from dual_rec.scenarios import Fault
from dual_rec.validation import array, compare, passes


class World:
    """Only wraps the existing pinned environments and unmodified replay adapters."""

    def __init__(self, task, seed, condition):
        import torch

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        self.task = task
        self.condition = condition
        if task == "Lift":
            import mujoco

            self.wrapped = make_lift(seed)
            self.env = self.wrapped
            self.obs = self.env.reset()
            self.adapter = RobosuiteReplay(self.env)
            self.env._qual_target = self.env.sim.data.body_xpos[
                self.env.cube_body_id
            ].copy()
            model, data = self.adapter.model, self.adapter.data
            body = self.env.cube_body_id
            self.edit = {
                "step": 0,
                "mass_before": float(model.body_mass[body]),
                "inertia_before": model.body_inertia[body].copy().tolist(),
                "com_before": model.body_ipos[body].copy().tolist(),
                "axes_before": model.body_iquat[body].copy().tolist(),
            }
            if condition == "mass8":
                integration = np.empty(mujoco.mj_stateSize(model, self.adapter.spec))
                mujoco.mj_getState(model, data, integration, self.adapter.spec)
                model.body_mass[body] *= 8
                model.body_inertia[body] *= 8
                mujoco.mj_setConst(model, data)
                mujoco.mj_setState(model, data, integration, self.adapter.spec)
                mujoco.mj_forward(model, data)
            self.edit.update(
                mass_after=float(model.body_mass[body]),
                inertia_after=model.body_inertia[body].copy().tolist(),
                com_after=model.body_ipos[body].copy().tolist(),
                axes_after=model.body_iquat[body].copy().tolist(),
            )
            scale = 8 if condition == "mass8" else 1
            if not np.isclose(
                self.edit["mass_after"], self.edit["mass_before"] * scale
            ) or not np.allclose(
                self.edit["inertia_after"],
                np.asarray(self.edit["inertia_before"]) * scale,
            ):
                raise RuntimeError("INVALID_PHYSICAL_EDIT")
            if (
                self.edit["com_before"] != self.edit["com_after"]
                or self.edit["axes_before"] != self.edit["axes_after"]
            ):
                raise RuntimeError("INVALID_PHYSICAL_EDIT_COM_AXES")
            robot = self.env.robots[0]
            names = list(robot.robot_model.contact_geoms) + [
                name
                for gripper in robot.gripper.values()
                for name in gripper.contact_geoms
            ]
            self.robot_ids = {self.env.sim.model.geom_name2id(name) for name in names}
            self.cube_ids = {
                self.env.sim.model.geom_name2id(name)
                for name in self.env.cube.contact_geoms
            }
        else:
            from sapien.physx import PhysxRigidDynamicComponent

            self.wrapped = make_env(task)
            self.obs, _ = self.wrapped.reset(seed=seed)
            self.env = self.wrapped.unwrapped
            self.cube = self.env.obj if task == "PushCube-v1" else self.env.cube
            if task == "PickCube-v1":
                self.edit = apply_pick_fault(
                    self.env,
                    PickFault(
                        name=condition,
                        friction=0.01 if condition == "low_friction_001" else None,
                    ),
                )
            else:
                body = self.cube._objs[0].find_component_by_type(
                    PhysxRigidDynamicComponent
                )
                self.edit = apply_fault(
                    body,
                    Fault(name=condition, mass_scale=8 if condition == "mass8" else 1),
                ).model_dump()
            self.initial = array(self.cube.pose.p).reshape(3).copy()
            goal_actor = (
                self.env.goal_region if task == "PushCube-v1" else self.env.goal_site
            )
            self.goal = array(goal_actor.pose.p).reshape(3).copy()
            if condition == "misaligned":
                self.initial[1] += 0.07
                self.goal[1] += 0.07
            self.adapter = ManiSkillReplay(self.wrapped)

    def close(self):
        self.wrapped.close()

    def state(self, refresh=False):
        if self.task == "Lift":
            if refresh:
                self.obs = self.env._get_observations()
            result = self.adapter.record(self.obs)
            result["robot_object_contact"] = any(
                (a in self.cube_ids and b in self.robot_ids)
                or (b in self.cube_ids and a in self.robot_ids)
                for a, b in result["contacts"]
            )
            return result
        if refresh:
            self.obs = self.env.get_obs()
        return record(self.env, self.cube, self.obs)

    def step(self, a):
        if self.task == "Lift":
            self.obs, *_ = self.wrapped.step(np.asarray(a, dtype=float))
        else:
            self.obs, *_ = self.wrapped.step(np.asarray(a, dtype=np.float32))
        return self.state()

    def normal(self, phase):
        if self.task == "Lift":
            return lift_action(self.env, phase)
        return scripted_action(
            self.task, self.initial, self.goal, self.env.agent.tcp.pose.p, phase
        )

    def exposed(self):
        if self.task == "Lift":
            return {
                "applied_qfrc": self.adapter.data.qfrc_applied.copy(),
                "ctrl": self.adapter.data.ctrl.copy(),
            }
        return {
            "applied_qf": array(self.env.agent.robot.get_qf()).copy(),
            "drive_targets": array(self.env.agent.robot.drive_targets).copy(),
            "drive_velocities": array(self.env.agent.robot.drive_velocities).copy(),
        }

    def continuation(self, mode, step, initial_tcp):
        if self.task == "Lift":
            a = self.normal(3)
            if mode == "alternative":
                a[:3] = np.clip(a[:3], -0.2, 0.2)
            return a
        if self.task == "PickCube-v1":
            cube = array(self.cube.pose.p).reshape(3)
            tcp = array(self.env.agent.tcp.pose.p).reshape(3)
            goal = array(self.env.goal_site.pose.p).reshape(3)
            bound = 0.25 if mode == "nominal" else 0.08
            target = (
                cube + [0, 0, 0.06] if mode == "alternative" and step < 15 else goal
            )
        else:
            cube = array(self.cube.pose.p).reshape(3)
            tcp = array(self.env.agent.tcp.pose.p).reshape(3)
            goal = array(self.env.goal_region.pose.p).reshape(3)
            target = np.r_[goal[:2], cube[2]]
            bound = 0.25
            if mode == "alternative":
                if step < 6:
                    target = initial_tcp + [0, 0, 0.08]
                elif step < 16:
                    target = cube + [-0.055, 0, 0.10]
                elif step < 26:
                    target = cube + [-0.055, 0, 0]
        return np.r_[np.clip((target - tcp) / 0.1, -bound, bound), -1].astype(
            np.float32
        )


def prefix_to_stage(world, stage):
    trace = [world.state()]
    actions = []
    seen = False
    schedule = (
        [(0, 20), (1, 25), (2, 8)]
        if world.task == "PushCube-v1"
        else [(0, 20), (1, 25), (2, 15), (3, 5)]
    )
    for phase, count in schedule:
        for _ in range(count):
            a = world.normal(phase)
            state = world.step(a)
            actions.append(a.copy())
            trace.append(state)
            seen |= state["robot_object_contact"]
            if stage == "free" and len(actions) == 20:
                return (
                    actions,
                    trace,
                    not state["robot_object_contact"],
                    "no-contact at approach boundary",
                )
            contact = (
                state.get("is_grasped", state["robot_object_contact"])
                if world.task == "Lift"
                else state["robot_object_contact"]
            )
            if stage == "contact" and len(actions) > 20 and contact:
                return (
                    actions,
                    trace,
                    True,
                    "observed established grasp"
                    if world.task == "Lift"
                    else "observed first robot-object contact",
                )
    return (
        actions,
        trace,
        stage == "transport" and seen,
        "fixed post-contact boundary" if seen else "contact stage not reached",
    )


def summary_errors(errors):
    return {
        "passed": all(passes(e) for e in errors),
        "steps": len(errors),
        "maxima": {
            key: max(e[key] for e in errors)
            for key in ["position", "angle", "velocity", "qpos", "observation", "time"]
        },
        "contact_agreement": sum(e["contacts"] for e in errors) / len(errors),
        "outcome_agreement": sum(e["success"] for e in errors) / len(errors),
    }


def outcome(trace, actions, task):
    success = bool(trace[-1]["success"])
    bound = 0.6 if task == "Lift" else 0.25
    effort = float(
        np.clip(
            np.linalg.norm(np.asarray(actions)[:, :3], axis=1) / (np.sqrt(3) * bound),
            0,
            1,
        ).mean()
    )
    return {
        "success": success,
        "utility": float((int(success) - 0.05 * effort - 0.05 + 0.10) / 1.10),
        "effort": effort,
        "steps": len(actions),
        "final_position": jsonable(trace[-1]["position"]),
    }


def trial(task, seed, condition, stage, policy, horizon):
    reference = World(task, seed, condition)
    gold = None
    try:
        prefix, records, reached, detection = prefix_to_stage(reference, stage)
        base = {
            "completed_continuations": 0,
            "task": task,
            "seed": seed,
            "condition": condition,
            "stage": stage,
            "policy": policy,
            "stage_reached": reached,
            "stage_detection": detection,
            "physical_edit": reference.edit,
            "prefix_actions": prefix,
            "branch_record": records[-1],
        }
        if not reached:
            return base, {}, 0
        snap = reference.adapter.capture()
        exposed_before = reference.exposed()
        if task == "Lift":
            tcp = reference.env.sim.data.site_xpos[
                reference.env.robots[0].eef_site_id["right"]
            ].copy()
        else:
            tcp = array(reference.env.agent.tcp.pose.p).reshape(3).copy()
        actions = []
        native = []
        for step in range(horizon):
            a = reference.continuation(policy, step, tcp)
            actions.append(a.copy())
            native.append(reference.step(a))
        gold = World(task, seed, condition)
        if gold.edit != reference.edit:
            raise RuntimeError("INVALID_PHYSICAL_EDIT_RECONSTRUCTION")
        gold_prefix = [gold.state()]
        for a in prefix:
            gold_prefix.append(gold.step(a))
        prefix_errors = [
            compare(a, b) for a, b in zip(records, gold_prefix, strict=True)
        ]
        gold_trace = [gold.step(a) for a in actions]
        base["completed_continuations"] = 2
        gold_errors = [compare(a, b) for a, b in zip(native, gold_trace, strict=True)]
        base["gold_prefix"] = summary_errors(prefix_errors)
        base["gold_continuation"] = summary_errors(gold_errors)
        if not base["gold_prefix"]["passed"] or not base["gold_continuation"]["passed"]:
            base["integrity_failure"] = True
            return (
                base,
                {
                    "prefix": records,
                    "gold_prefix": gold_prefix,
                    "native": native,
                    "gold": gold_trace,
                    "prefix_errors": prefix_errors,
                    "gold_errors": gold_errors,
                },
                2,
            )
        base["native"] = outcome(native, actions, task)
        base["gold"] = outcome(gold_trace, actions, task)
        tested = []
        try:
            reference.adapter.restore(snap)
            immediate = reference.state(refresh=True)
            base["test_immediate_error"] = compare(records[-1], immediate)
            base["test_exposed_mismatches"] = snapshot_mismatches(
                snap, reference.adapter.capture()
            )
            from dual_rec.validation import max_difference

            base["omitted_or_integration_fields_error"] = {
                key: max_difference(value, reference.exposed()[key])
                for key, value in exposed_before.items()
            }
            for a in actions:
                tested.append(reference.step(a))
            base["completed_continuations"] = 3
            errors = [compare(a, b) for a, b in zip(gold_trace, tested, strict=True)]
            base["test"] = outcome(tested, actions, task)
            base["test_continuation"] = summary_errors(errors)
            base["test_errors"] = errors
            base["test_restore_exception"] = None
            base["test_immediate_record"] = immediate
        except Exception as exc:  # noqa: BLE001 - unqualified TEST failures remain denominators
            base["test_restore_exception"] = {
                "type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            base["test"] = None
        base["continuation_actions"] = actions
        base["test_steps_completed"] = len(tested)
        return (
            base,
            {"prefix": records, "native": native, "gold": gold_trace, "test": tested},
            3,
        )
    finally:
        if gold is not None:
            gold.close()
        reference.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task", choices=["PushCube-v1", "PickCube-v1", "Lift"], required=True
    )
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(Path("config/overnight_20261111.json").read_text())["b"]
    seeds = cfg["seed_ranges"][args.task][args.offset : args.offset + args.count]
    planned = len(seeds) * len(cfg["conditions"][args.task]) * 3 * 2 * 3
    prior_reserved = 0
    for status_file in args.output.parent.glob("*/status.json"):
        previous = json.loads(status_file.read_text())
        prior_reserved += (
            previous.get("attempted_continuations", 0)
            if previous["status"] == "completed"
            else previous.get("planned_continuations", 0)
        )
    if prior_reserved + planned > cfg["physical_continuation_cap"]:
        raise RuntimeError("B physical continuation budget boundary")
    args.output.mkdir(parents=True, exist_ok=False)
    count = 0
    completed_count = 0
    try:
        with (
            (args.output / "trials.jsonl").open("x") as compact,
            gzip.open(args.output / "raw.jsonl.gz", "xt", encoding="utf8") as raw,
        ):
            for seed in seeds:
                for condition in cfg["conditions"][args.task]:
                    for stage in cfg["stages"]:
                        for policy in cfg["continuations"]:
                            result, trace, branches = trial(
                                args.task,
                                seed,
                                condition,
                                stage,
                                policy,
                                cfg["horizon"],
                            )
                            count += branches
                            completed_count += result["completed_continuations"]
                            compact.write(
                                json.dumps(jsonable(result), allow_nan=False) + "\n"
                            )
                            compact.flush()
                            raw.write(
                                json.dumps(
                                    jsonable(
                                        {
                                            "seed": seed,
                                            "condition": condition,
                                            "stage": stage,
                                            "policy": policy,
                                            "trace": trace,
                                        }
                                    ),
                                    allow_nan=False,
                                )
                                + "\n"
                            )
                            raw.flush()
                            if result.get("integrity_failure"):
                                raise RuntimeError(
                                    "GOLD_INTEGRITY_FAILURE: experimental execution must stop"
                                )
                            print(
                                f"{args.task} seed={seed} {condition}/{stage}/{policy}: reached={result['stage_reached']} test_parity={result.get('test_continuation', {}).get('passed')}",
                                flush=True,
                            )
                gc.collect()
        (args.output / "status.json").open("x").write(
            json.dumps(
                {
                    "status": "completed",
                    "task": args.task,
                    "seeds": seeds,
                    "attempted_continuations": count,
                    "physical_continuations": completed_count,
                    "planned_continuations": planned,
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - retain failures and stop, never route invalid GOLD
        (args.output / "status.json").open("x").write(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "task": args.task,
                    "seeds": seeds,
                    "attempted_continuations": count,
                    "physical_continuations": completed_count,
                    "planned_continuations": planned,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        )
        print(traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
