"""Replay metrics and explicit adapters for the pinned simulator versions."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class Tolerances(BaseModel):
    """Frozen before replay collection; SI units except orientation (radians)."""

    position: float = Field(default=1e-5, gt=0)
    angle: float = Field(default=1e-4, gt=0)
    velocity: float = Field(default=1e-4, gt=0)
    observation: float = Field(default=1e-4, gt=0)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy().tolist()
    return value


def quat_error(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    return float(2 * np.arccos(np.clip(abs(a @ b), 0, 1)))


def distribution(values: list[float]) -> dict:
    a = np.asarray(values, dtype=float)
    if not len(a) or not np.isfinite(a).all():
        raise ValueError("Expected nonempty finite errors")
    counts, edges = np.histogram(a, bins=10)
    return {
        "max": float(a.max()),
        "median": float(np.median(a)),
        "p95": float(np.quantile(a, 0.95)),
        "counts": counts.tolist(),
        "edges": edges.tolist(),
    }


def simple(value: Any) -> bool:
    """Only copy data, never simulator/controller object references."""
    if value is None or isinstance(
        value, (str, int, float, bool, np.ndarray, np.generic)
    ):
        return True
    if isinstance(value, (tuple, list)):
        return all(simple(v) for v in value)
    if isinstance(value, dict):
        return all(simple(v) for v in value.values())
    return False


def fields(obj: Any) -> dict:
    return {k: copy.deepcopy(v) for k, v in vars(obj).items() if simple(v)}


def apply_fields(obj: Any, state: dict) -> None:
    for k, v in state.items():
        setattr(obj, k, copy.deepcopy(v))


@dataclass
class Snapshot:
    physics: Any
    python: Any
    numpy: Any
    custom: dict


class RobosuiteReplay:
    """Lift/Panda BASIC OSC_POSE only, with no interpolation or cameras.

    mjSTATE_INTEGRATION includes warmstart, controls and applied forces, unlike
    robosuite's get_state. Model properties remain fixed within each paired run.
    This is an explicitly scoped adapter, not serialization of arbitrary tasks.
    """

    def __init__(self, env):
        import mujoco

        self.env = env
        self.mj = mujoco
        self.model = env.sim.model._model
        self.data = env.sim.data._data
        self.spec = mujoco.mjtState.mjSTATE_INTEGRATION
        self.objects = {"env": env}
        for i, robot in enumerate(env.robots):
            self.objects[f"robot{i}"] = robot
            self.objects[f"composite{i}"] = robot.composite_controller
            for name, controller in robot.part_controllers.items():
                for k in ("interpolator_pos", "interpolator_ori"):
                    if getattr(controller, k, None) is not None:
                        raise RuntimeError(
                            "Interpolated controllers are outside adapter coverage"
                        )
                self.objects[f"controller{i}/{name}"] = controller
            for name, gripper in robot.gripper.items():
                self.objects[f"gripper{i}/{name}"] = gripper
        for name, observable in env._observables.items():
            self.objects[f"observable/{name}"] = observable

    def capture(self) -> Snapshot:
        state = np.empty(self.mj.mj_stateSize(self.model, self.spec))
        self.mj.mj_getState(self.model, self.data, state, self.spec)
        custom = {k: fields(v) for k, v in self.objects.items()}
        custom["rng"] = copy.deepcopy(self.env.rng.bit_generator.state)
        return Snapshot(state, random.getstate(), np.random.get_state(), custom)

    def restore(self, snap: Snapshot) -> None:
        # Forward rebuilds derived contact/kinematic data; restore integration
        # fields again afterward so warmstart is not changed by this operation.
        self.mj.mj_setState(self.model, self.data, snap.physics, self.spec)
        self.mj.mj_forward(self.model, self.data)
        self.mj.mj_setState(self.model, self.data, snap.physics, self.spec)
        for k, obj in self.objects.items():
            apply_fields(obj, snap.custom[k])
        self.env.rng.bit_generator.state = copy.deepcopy(snap.custom["rng"])
        random.setstate(snap.python)
        np.random.set_state(snap.numpy)

    def record(self, obs: dict) -> dict:
        d = self.data
        i = self.env.cube_body_id
        return {
            "position": d.xpos[i].copy(),
            "quaternion": d.xquat[i].copy(),
            "qpos": d.qpos.copy(),
            "velocity": d.qvel.copy(),
            "time": float(d.time),
            "contacts": sorted((int(c.geom1), int(c.geom2)) for c in d.contact),
            "is_grasped": bool(
                self.env._check_grasp(
                    gripper=self.env.robots[0].gripper, object_geoms=self.env.cube
                )
            ),
            "success": bool(self.env._check_success()),
            "observation": copy.deepcopy(obs),
        }


class ManiSkillReplay:
    """CPU adapter for built-in PushCube and PickCube; runtime qualification required.

    Contact solver caches and static/material/model data are not exposed by
    get_state_dict. Scene/model properties must be identical across branches.
    """

    def __init__(self, env):
        self.env = env.unwrapped
        self.wrappers = []
        wrapper = env
        while wrapper is not self.env:
            self.wrappers.append(wrapper)
            wrapper = wrapper.env
        if self.env.gpu_sim_enabled:
            raise RuntimeError("CPU qualification must precede GPU support")

    def capture(self) -> Snapshot:
        import torch

        env = self.env
        names = (
            "_elapsed_steps",
            "_main_seed",
            "_episode_seed",
            "_main_rng",
            "_episode_rng",
            "_batched_main_rng",
            "_batched_episode_rng",
        )
        custom = {k: getattr(env, k) for k in names}
        # Deep-copy together to preserve RNG aliases.
        custom = copy.deepcopy(custom)
        custom["torch"] = torch.get_rng_state().clone()
        custom["controller"] = copy.deepcopy(env.agent.get_controller_state())
        # Public controller snapshots omit interpolation counters/targets in
        # non-target modes. Capture these explicit fields at control boundaries.
        custom["controller_transient"] = {
            name: {
                key: copy.deepcopy(getattr(ctrl, key))
                for key in (
                    "_step",
                    "_start_qpos",
                    "_target_qpos",
                    "_step_size",
                    "_target_pose",
                )
                if hasattr(ctrl, key)
            }
            for name, ctrl in env.agent.controller.controllers.items()
        }
        custom["wrapper_elapsed"] = [
            getattr(w, "_elapsed_steps", None) for w in self.wrappers
        ]
        custom["drive_targets"] = env.agent.robot.drive_targets.clone()
        custom["drive_velocities"] = env.agent.robot.drive_velocities.clone()
        return Snapshot(
            copy.deepcopy(env.get_state_dict()),
            random.getstate(),
            np.random.get_state(),
            custom,
        )

    def restore(self, snap: Snapshot) -> None:
        import torch

        self.env.set_state_dict(copy.deepcopy(snap.physics))
        self.env.agent.set_controller_state(copy.deepcopy(snap.custom["controller"]))
        for name, state in snap.custom["controller_transient"].items():
            apply_fields(self.env.agent.controller.controllers[name], state)
        robot = self.env.agent.robot
        robot.set_joint_drive_targets(
            snap.custom["drive_targets"], joints=robot.active_joints
        )
        robot.set_joint_drive_velocity_targets(
            snap.custom["drive_velocities"], joints=robot.active_joints
        )
        custom = copy.deepcopy(snap.custom)
        for k, v in custom.items():
            if k.startswith("_"):
                setattr(self.env, k, v)
        for wrapper, elapsed in zip(
            self.wrappers, snap.custom["wrapper_elapsed"], strict=True
        ):
            if elapsed is not None:
                wrapper._elapsed_steps = elapsed
        torch.set_rng_state(snap.custom["torch"])
        random.setstate(snap.python)
        np.random.set_state(snap.numpy)
