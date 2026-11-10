"""D5-D7 contracts: oracle recipes are separate from robot histories."""

from __future__ import annotations

from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

Vector3 = Annotated[list[float], Field(min_length=3, max_length=3)]
Action = Annotated[list[float], Field(min_length=4, max_length=4)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Fault(StrictModel):
    name: str
    mass_scale: float = Field(gt=0)
    friction: float | None = Field(default=None, ge=0)
    alignment_y: float = 0.0


class AgentObservation(StrictModel):
    qpos: list[list[float]]
    qvel: list[list[float]]


class TaskExtra(StrictModel):
    tcp_pose: list[list[float]]
    obj_pose: list[list[float]]
    goal_pos: list[list[float]]


class TaskObservation(StrictModel):
    agent: AgentObservation
    extra: TaskExtra


class RobotObservation(StrictModel):
    task_state: TaskObservation
    cube_velocity: list[float]
    drive_targets: list[float]
    drive_velocities: list[float]
    joint_forces: list[float]
    link_wrenches: list[list[float]]
    robot_cube_contact: bool
    time: float


class HistoryFrame(StrictModel):
    step: int = Field(ge=0)
    observation: RobotObservation
    action: Action


class PhysicalEdit(StrictModel):
    control_step: int = 0
    before: dict
    after: dict


class ReplayRecipe(StrictModel):
    simulator: Literal["ManiSkill 3.0.1 / SAPIEN 3.0.3 CPU"] = (
        "ManiSkill 3.0.1 / SAPIEN 3.0.3 CPU"
    )
    task: Literal["PushCube-v1"] = "PushCube-v1"
    seed: int
    environment_versions: dict[str, str]
    evaluation_only_fault: Fault
    physical_edits: list[PhysicalEdit]
    fault_injection_step: int = 0
    prefix_actions: list[Action]
    source_sha256: dict[str, str]
    config_sha256: str


class FailureScenario(StrictModel):
    scenario_id: str
    split: Literal["development", "qualification"]
    recipe: ReplayRecipe
    permitted_channels: list[str]
    failure_trigger: dict
    history: list[HistoryFrame]
    branch_record: dict


def flatten_numeric(value) -> list[float]:
    if isinstance(value, dict):
        return [x for key in sorted(value) for x in flatten_numeric(value[key])]
    if isinstance(value, list):
        return [x for item in value for x in flatten_numeric(item)]
    if isinstance(value, (int, float, bool)):
        return [float(value)]
    raise ValueError("Only declared numeric robot observations may enter features")


def history_features(
    history: list[HistoryFrame | dict], decision_step: int = 78
) -> np.ndarray:
    frames = [HistoryFrame.model_validate(frame) for frame in history]
    if [frame.step for frame in frames] != list(range(decision_step + 1)):
        raise ValueError(
            "History must end at decision time without missing/future frames"
        )
    if any(abs(frame.observation.time - frame.step / 20) > 1e-9 for frame in frames):
        raise ValueError("History time does not match declared control step")
    features = np.asarray(
        [
            x
            for frame in frames
            for x in flatten_numeric(
                {"observation": frame.observation.model_dump(), "action": frame.action}
            )
        ]
    )
    if not np.isfinite(features).all():
        raise ValueError("Nonfinite history features")
    return features


def recovery_action(
    observation: RobotObservation, recovery: str, step: int, initial_tcp: np.ndarray
) -> np.ndarray:
    """A physical controller receiving only declared robot measurements."""
    extra = observation.task_state.extra
    tcp = np.asarray(extra.tcp_pose[0][:3])
    cube = np.asarray(extra.obj_pose[0][:3])
    goal = np.asarray(extra.goal_pos[0])
    target = np.r_[goal[:2], cube[2]]
    bound = 0.08 if recovery == "slow" else 0.25
    if recovery == "recontact":
        if step < 6:
            target = initial_tcp + [0, 0, 0.08]
        elif step < 18:
            target = cube + [-0.055, 0, 0.10]
        elif step < 28:
            target = cube + [-0.055, 0, 0]
    elif recovery not in ("continue", "slow"):
        raise ValueError("Unknown recovery")
    return np.r_[np.clip((target - tcp) / 0.1, -bound, bound), -1].astype(np.float32)


def normalized_utility(success: bool, actions: list, horizon: int = 50) -> float:
    a = np.asarray(actions, dtype=float)
    if a.shape != (horizon, 4) or not np.isfinite(a).all():
        raise ValueError("Utility requires the complete fixed action horizon")
    effort = np.clip(
        np.linalg.norm(a[:, :3], axis=1) / (np.sqrt(3) * 0.25), 0, 1
    ).mean()
    return float((int(success) - 0.05 * effort - 0.05 + 0.10) / 1.10)


def failure_trigger(
    records: list[dict], window: int = 10, minimum_progress: float = 0.01
) -> dict:
    if len(records) < window + 1:
        raise ValueError("Failure requires a complete decision window")
    start, end = records[-window - 1], records[-1]

    def distance(record):
        goal = np.asarray(record["observation"]["extra"]["goal_pos"][0])[:2]
        return np.linalg.norm(np.asarray(record["position"])[:2] - goal)

    progress = float(distance(start) - distance(end))
    contact_steps = sum(bool(r["robot_object_contact"]) for r in records[-window:])
    stalled = progress < minimum_progress
    missed = contact_steps == 0
    return {
        "failed": bool(not end["success"] and (stalled or missed)),
        "stalled": bool(stalled),
        "missed_contact": missed,
        "window_progress_m": progress,
        "window_contact_steps": contact_steps,
        "task_success": bool(end["success"]),
        "goal_distance_m": float(distance(end)),
    }


def split_seeds(config: dict) -> tuple[set[int], set[int]]:
    development, qualification = (
        set(config["development_seeds"]),
        set(config["qualification_seeds"]),
    )
    if development & qualification or len(development | qualification) > 40:
        raise ValueError("Invalid or leaking seed partitions")
    if not set(config["replay_seeds"]) <= development:
        raise ValueError("Replay seeds must reuse development")
    return development, qualification
