"""Typed PickCube histories, explicit contact faults and frozen overnight controls."""

from __future__ import annotations

import numpy as np
from pydantic import Field

from dual_rec.physical_faults import body_parameters
from dual_rec.replay import jsonable
from dual_rec.scenarios import AgentObservation, StrictModel
from dual_rec.validation import array


class PickFault(StrictModel):
    name: str
    friction: float | None = Field(default=None, ge=0)
    offset_x: float = 0


class PickExtra(StrictModel):
    is_grasped: list[bool]
    tcp_pose: list[list[float]]
    goal_pos: list[list[float]]
    obj_pose: list[list[float]]
    tcp_to_obj_pos: list[list[float]]
    obj_to_goal_pos: list[list[float]]


class PickState(StrictModel):
    agent: AgentObservation
    extra: PickExtra


class PickSensors(StrictModel):
    task_state: PickState
    object_velocity: list[float]
    drive_targets: list[float]
    drive_velocities: list[float]
    applied_qf: list[float]
    link_wrenches: list[list[float]]
    robot_contact: bool
    time: float


class PickFrame(StrictModel):
    step: int
    action: list[float] = Field(min_length=4, max_length=4)
    sensors: PickSensors


def sensors(env, cube, obs, state):
    robot = env.agent.robot
    return PickSensors(
        task_state=jsonable(obs),
        object_velocity=np.r_[
            array(cube.linear_velocity).ravel(), array(cube.angular_velocity).ravel()
        ].tolist(),
        drive_targets=array(robot.drive_targets).ravel().tolist(),
        drive_velocities=array(robot.drive_velocities).ravel().tolist(),
        applied_qf=array(robot.get_qf()).ravel().tolist(),
        link_wrenches=array(robot.get_link_incoming_joint_forces())[0].tolist(),
        robot_contact=state["robot_object_contact"],
        time=state["time"],
    )


def apply_pick_fault(env, fault: PickFault):
    import sapien
    from sapien.physx import PhysxRigidDynamicComponent

    body = env.cube._objs[0].find_component_by_type(PhysxRigidDynamicComponent)
    before = body_parameters(body)
    finger_shapes = [
        s
        for link in env.agent.robot.links
        if "finger" in link.name
        for physical in link._objs
        for s in physical.collision_shapes
    ]
    before_fingers = [
        {
            "static": s.physical_material.static_friction,
            "dynamic": s.physical_material.dynamic_friction,
        }
        for s in finger_shapes
    ]
    if fault.friction is not None:
        for shape in list(body.collision_shapes) + finger_shapes:
            shape.physical_material = sapien.physx.PhysxMaterial(
                fault.friction, fault.friction, shape.physical_material.restitution
            )
        if any(
            not np.isclose(
                s.physical_material.dynamic_friction, fault.friction, rtol=1e-6
            )
            for s in list(body.collision_shapes) + finger_shapes
        ):
            raise RuntimeError("Invalid physical material readback")
    after = body_parameters(body)
    if any(
        before[key] != after[key]
        for key in ["mass_kg", "inertia_kg_m2", "center_of_mass_pose"]
    ):
        raise RuntimeError("Grasp-material edit changed mass/inertia/COM")
    return {
        "step": 0,
        "cube_before": before,
        "cube_after": after,
        "finger_before": before_fingers,
        "finger_after": [
            {
                "static": s.physical_material.static_friction,
                "dynamic": s.physical_material.dynamic_friction,
            }
            for s in finger_shapes
        ],
        "scope": "cube/table and cube/finger contact; not a contact-specific coefficient",
    }


def event_trigger(frames: list[PickFrame], initial_z: float):
    if frames[-1].step < 70 or len(frames) < 3:
        return None
    recent = frames[-3:]
    missed = all(
        not f.sensors.task_state.extra.is_grasped[0]
        and f.sensors.task_state.extra.obj_pose[0][2] < initial_z + 0.03
        and f.sensors.task_state.extra.tcp_pose[0][2] > initial_z + 0.06
        for f in recent
    )
    peak = max(f.sensors.task_state.extra.obj_pose[0][2] for f in frames)
    last = frames[-1].sensors.task_state.extra
    dropped = (
        peak > initial_z + 0.06
        and last.obj_pose[0][2] < peak - 0.03
        and not last.is_grasped[0]
    )
    return "missed_lift" if missed else ("drop" if dropped else None)


def pick_recovery(frame: PickFrame, mode: str, step: int, initial_tcp):
    extra = frame.sensors.task_state.extra
    cube = np.asarray(extra.obj_pose[0][:3])
    tcp = np.asarray(extra.tcp_pose[0][:3])
    goal = np.asarray(extra.goal_pos[0])
    target = goal.copy()
    gripper = -1.0
    bound = 0.25
    if mode == "regrasp":
        if step < 8:
            target = np.asarray(initial_tcp) + [0, 0, 0.10]
            gripper = 1.0
        elif step < 22:
            target = cube + [0, 0, 0.10]
            gripper = 1.0
        elif step < 34:
            target = cube
            gripper = 1.0
        elif step < 46:
            target = cube
    elif mode == "conservative":
        if step < 20:
            target = cube + [0, 0, 0.06]
        bound = 0.08
    elif mode != "nominal":
        raise ValueError("Unknown frozen recovery")
    return np.r_[np.clip((target - tcp) / 0.1, -bound, bound), gripper].astype(
        np.float32
    )


def passive_features(history: list[dict | PickFrame], regime: str, maximum_step=90):
    from dual_rec.scenarios import flatten_numeric

    frames = [PickFrame.model_validate(f) for f in history]
    if (
        not frames
        or [f.step for f in frames] != list(range(len(frames)))
        or frames[-1].step > maximum_step
    ):
        raise ValueError("Invalid or future history")
    rows = []
    for index in range(maximum_step + 1):
        observed = index < len(frames)
        last = min(index, len(frames) - 1)
        frame = frames[last]
        packet = frame.sensors
        if regime == "full":
            values = flatten_numeric(packet.model_dump())
        elif regime == "realistic":
            q = np.asarray(packet.task_state.agent.qpos).ravel()
            v = np.asarray(packet.task_state.agent.qvel).ravel()
            camera = max(0, ((last - 1) // 2) * 2)
            previous = max(0, camera - 2)
            obj = (
                np.round(
                    np.asarray(frames[camera].sensors.task_state.extra.obj_pose[0][:3])
                    / 0.005
                )
                * 0.005
            )
            old = (
                np.round(
                    np.asarray(
                        frames[previous].sensors.task_state.extra.obj_pose[0][:3]
                    )
                    / 0.005
                )
                * 0.005
            )
            velocity = (obj - old) / (max(1, camera - previous) / 20)
            goal = (
                np.round(np.asarray(packet.task_state.extra.goal_pos[0]) / 0.005)
                * 0.005
            )
            targets = np.asarray(packet.drive_targets)
            velocities = np.asarray(packet.drive_velocities)
            # Standard robot controller signals, not hypothetical 6D sensors on
            # every link. This is a commanded-effort estimate, not a measurement
            # of contact impulse or a calibrated motor-current sensor.
            efforts = []
            for past in frames[max(0, last - 2) : last + 1]:
                sensor = past.sensors
                position = np.asarray(sensor.task_state.agent.qpos).ravel()
                speed = np.asarray(sensor.task_state.agent.qvel).ravel()
                effort = np.clip(
                    1000 * (np.asarray(sensor.drive_targets) - position)
                    + 100 * (np.asarray(sensor.drive_velocities) - speed),
                    -100,
                    100,
                ) + np.asarray(sensor.applied_qf)
                efforts.append(effort)
            resolutions = np.r_[np.full(7, 0.05), np.full(2, 0.5)]
            force = np.round(np.mean(efforts, axis=0) / resolutions) * resolutions
            values = np.r_[
                np.round(q / 0.001) * 0.001,
                np.round(v / 0.01) * 0.01,
                targets,
                velocities,
                obj,
                velocity,
                goal,
                force.ravel(),
                packet.time,
            ].tolist()
        else:
            raise ValueError("Unknown sensor regime")
        rows.extend([float(observed)] + frame.action + values)
    result = np.asarray(rows, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite passive sensors")
    return result


def select_severity(rows: list[dict], config: dict) -> dict:
    nominal = [row for row in rows if row["evaluation_only_fault"]["name"] == "nominal"]
    expected = len(config["calibration_seeds"])
    if len(nominal) != expected:
        raise ValueError("Incomplete calibration negative control")
    result = {
        "status": "NO-GO",
        "nominal_successes": sum(row["initial_success"] for row in nominal),
        "independent_calibration_seeds": expected,
        "levels": {},
    }
    if result["nominal_successes"] < 3:
        result["reason"] = (
            "Nominal calibration control failed its preregistered incidence criterion"
        )
        return result
    chosen = {}
    for mechanism, key, values in [
        ("friction", "friction", config["friction_grid"]),
        ("offset", "offset_x", config["offset_grid_m"]),
    ]:
        result["levels"][mechanism] = []
        for value in values:
            selected = [
                row
                for row in rows
                if row["evaluation_only_fault"]["name"] == f"{mechanism}-{value}"
            ]
            if len(selected) != expected:
                raise ValueError("Incomplete registered severity grid")
            failures = sum(row["failed"] for row in selected)
            result["levels"][mechanism].append(
                {"value": value, "failures": failures, "total": expected}
            )
            if (
                mechanism not in chosen
                and failures >= config["severity_selection_minimum_failures"]
            ):
                chosen[mechanism] = value
        if mechanism in chosen:
            result[key] = chosen[mechanism]
    if len(chosen) == 2:
        result.update(
            status="SELECTED",
            reason="Least severity meeting the registered failure-incidence threshold; no recovery outcomes consulted",
        )
    else:
        result["reason"] = (
            "No credible registered severity for both mechanisms; route to B"
        )
    return result
