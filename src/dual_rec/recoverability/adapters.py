"""Pure, unexecuted probe interfaces for the two nominated native tasks.

No environment constructor, simulator import, step, reset or state setter exists
here. These command/packet designs require the separately specified future pilot.
"""

import itertools
import math
from typing import Literal

from pydantic import Field, model_validator

from .schema import Frozen

Task = Literal["PickCube-v1", "PushCube-v1"]
Command = tuple[float, float, float, float]


class PlannerFrame(Frozen):
    time_seconds: float = Field(ge=0)
    arm_qpos: tuple[float, float, float, float, float, float, float]
    arm_qvel: tuple[float, float, float, float, float, float, float]
    tcp_xyz: tuple[float, float, float]
    source: Literal["NATIVE_ARM_PROPRIOCEPTION_AND_FORWARD_KINEMATICS"] = (
        "NATIVE_ARM_PROPRIOCEPTION_AND_FORWARD_KINEMATICS"
    )

    @model_validator(mode="after")
    def no_missing_or_nonfinite_measurements(self):
        if not all(
            math.isfinite(v)
            for v in (self.time_seconds, *self.arm_qpos, *self.arm_qvel, *self.tcp_xyz)
        ):
            raise ValueError("SOURCE_UNAVAILABLE: nonfinite native measurement")
        return self


def mask_native_state(native: dict) -> PlannerFrame:
    """Accept a recorded native state; exclude object/fault/future/contact data.

    Finger joint positions are deliberately excluded, rather than named a new
    aperture sensor. Applied forces, wrenches and simulator grasp flags are absent.
    """
    try:
        obs = native["observation"]
        return PlannerFrame(
            time_seconds=native["time"],
            arm_qpos=tuple(obs["agent"]["qpos"][0][:7]),
            arm_qvel=tuple(obs["agent"]["qvel"][0][:7]),
            tcp_xyz=tuple(obs["extra"]["tcp_pose"][0][:3]),
        )
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(
            "SOURCE_UNAVAILABLE: no invented sensor or fallback label"
        ) from error


def probe_commands(task: Task, probe: str) -> tuple[Command, ...]:
    """Ten genuine Panda pd_ee_delta_pos control commands; no free observation.

    The source controller maps normalized Cartesian deltas through its own PD/IK
    dynamics. Commanded displacement is not asserted as observed object motion.
    """
    if task == "PickCube-v1":
        if probe == "micro_lift":
            return ((0.0, 0.0, 0.025, -1.0),) * 4 + ((0.0, 0.0, 0.0, -1.0),) * 6
        if probe == "release_settle":
            return ((0.0, 0.0, 0.0, 1.0),) * 10
    elif task == "PushCube-v1":
        if probe == "forward_tap":
            return ((0.05, 0.0, 0.0, -1.0),) * 4 + ((0.0, 0.0, 0.0, -1.0),) * 6
        if probe == "lateral_sweep":
            return ((0.0, 0.05, 0.0, -1.0),) * 4 + ((0.0, 0.0, 0.0, -1.0),) * 6
    raise ValueError("SOURCE_UNSUPPORTED: task/probe is outside the frozen menu")


class ProbeObservation(Frozen):
    displacement_bins_5mm: tuple[int, int, int]
    arm_motion_bin_0_01rad: int
    peak_arm_speed_bin_0_1rad_s: int
    timestamp: float
    physical_effect_qualified: Literal[False] = False
    interpretation: Literal[
        "OBSERVED_KINEMATIC_RESPONSE_NOT_A_CONTACT_FORCE_OR_SUCCESS_LABEL"
    ] = "OBSERVED_KINEMATIC_RESPONSE_NOT_A_CONTACT_FORCE_OR_SUCCESS_LABEL"


def encode_response(frames: tuple[PlannerFrame, ...]) -> ProbeObservation:
    if len(frames) != 11 or any(
        abs(b.time_seconds - a.time_seconds - 0.05) > 1e-9
        for a, b in itertools.pairwise(frames)
    ):
        raise ValueError(
            "SOURCE_UNAVAILABLE: require all ten20Hz source controls; missing is not false"
        )
    first, last = frames[0], frames[-1]
    return ProbeObservation(
        displacement_bins_5mm=tuple(
            math.floor((b - a) / 0.005)
            for a, b in zip(first.tcp_xyz, last.tcp_xyz, strict=True)
        ),
        arm_motion_bin_0_01rad=math.floor(
            math.sqrt(
                sum(
                    (b - a) ** 2
                    for a, b in zip(first.arm_qpos, last.arm_qpos, strict=True)
                )
            )
            / 0.01
        ),
        peak_arm_speed_bin_0_1rad_s=math.floor(
            max(abs(v) for f in frames for v in f.arm_qvel) / 0.1
        ),
        timestamp=last.time_seconds,
    )
