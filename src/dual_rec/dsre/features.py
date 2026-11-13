"""Explicit predecision observation interface; no outcome/fault arguments."""

import math

from pydantic import model_validator

from dual_rec.contracts.checks import Evidence

PRIMARY = (
    "goal_near_03",
    "hand_object_near_04",
    "goal_progress_005",
    "object_moved_005",
    "gripper_closed_04",
    "hand_above_object_03",
)
PRIVILEGED = ("simulator_grasped", "simulator_contact")


class ObservedFrame(Evidence):
    time: float
    object_position: tuple[float, float, float] | None
    tcp_position: tuple[float, float, float] | None
    goal_position: tuple[float, float, float] | None
    finger_positions: tuple[float, float] | None


class ObservationHistory(Evidence):
    first: ObservedFrame | None
    current: ObservedFrame

    @model_validator(mode="after")
    def ordering(self):
        if self.first is not None and self.first.time > self.current.time:
            raise ValueError("Observation history extends past the decision time")
        return self


def vector(value, count=3):
    try:
        while (
            isinstance(value, list) and len(value) == 1 and isinstance(value[0], list)
        ):
            value = value[0]
        result = tuple(float(v) for v in value[:count])
        return (
            result
            if len(result) == count and all(math.isfinite(v) for v in result)
            else None
        )
    except (TypeError, ValueError):
        return None


def observed_frame(time, observation):
    extra = observation.get("extra", {})
    qpos = vector(observation.get("agent", {}).get("qpos"), 9)
    return ObservedFrame(
        time=time,
        object_position=vector(extra.get("obj_pose")),
        tcp_position=vector(extra.get("tcp_pose")),
        goal_position=vector(extra.get("goal_pos")),
        finger_positions=None if qpos is None else qpos[-2:],
    )


def distance(a, b):
    return None if a is None or b is None else math.dist(a, b)


def feature_values(history: ObservationHistory, *, coarse=False):
    current, first = history.current, history.first

    def pose(value):
        return (
            tuple(round(v / 0.02) * 0.02 for v in value)
            if coarse and value is not None
            else value
        )

    obj, hand, goal = (
        pose(current.object_position),
        pose(current.tcp_position),
        pose(current.goal_position),
    )
    near, proximity = distance(obj, goal), distance(hand, obj)
    old_goal = (
        distance(pose(first.object_position), pose(first.goal_position))
        if first is not None and first.time < current.time
        else None
    )
    displacement = (
        distance(obj, pose(first.object_position))
        if first is not None and first.time < current.time
        else None
    )
    return (
        None if near is None else near <= 0.03,
        None if proximity is None else proximity <= 0.04,
        None if old_goal is None or near is None else old_goal - near >= 0.005,
        None if displacement is None else displacement >= 0.005,
        None
        if current.finger_positions is None
        else sum(abs(v) for v in current.finger_positions) <= 0.04,
        None if hand is None or obj is None else hand[2] - obj[2] > 0.03,
    )
