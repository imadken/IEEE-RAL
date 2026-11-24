"""One frozen assembly row per fresh OS process; no within-history reset."""

import argparse
import faulthandler
import json
import logging
import lzma
import time
import traceback
from pathlib import Path

import numpy as np
from rpd_assembly_contract import (
    SCHEMA,
    Job,
    fault,
    goal_components,
    pose_matrix,
    pose_raw,
    probe_target,
    recovery_segments,
    transform,
    verify_registration,
)

LOGGER = logging.getLogger(__name__)
from scipy.spatial.transform import Rotation, Slerp


def plain(value):
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy().tolist()
    if hasattr(value, "raw_pose"):
        return plain(value.raw_pose)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def vector(value):
    return np.asarray(plain(value), dtype=float).reshape(-1)


class AssemblyEpisode:
    def __init__(self, job, destination):
        self.job = job
        self.destination = destination
        self.started = time.monotonic()
        self.frames = []
        self.command_log = []
        self.wrapped = None
        self.substep = 0
        self.tick = 0
        self.dwell = 0
        self.completion = False
        self.root_e = None
        self.root = None
        self.configuration = {}
        self.trace = (destination / "trace.jsonl").open("x", buffering=1)

    def initialize(self):
        import gymnasium as gym
        import mani_skill.envs  # noqa: F401
        import sapien
        import torch
        from mani_skill.utils.structs import Pose

        torch.set_num_threads(1)
        seed = self.job.candidate.native_geometry_seed
        np.random.seed(seed)
        torch.manual_seed(seed)
        self.wrapped = gym.make(
            "PegInsertionSide-v1",
            robot_uids="panda_wristcam",
            num_envs=1,
            sim_backend="cpu",
            render_backend="none",
            obs_mode="none",
            control_mode="pd_ee_pose",
            max_episode_steps=200,
            sim_config={"sim_freq": 100, "control_freq": 20},
        )
        self.wrapped.reset(seed=seed)
        env = self.env = self.wrapped.unwrapped
        assert env.control_freq == 20 and env._sim_steps_per_control == 5
        assert abs(env.scene.px.timestep - 0.01) < 1e-8
        limits = []
        current = self.wrapped
        while hasattr(current, "env"):
            if "_max_episode_steps" in current.__dict__:
                limits.append(int(current.__dict__["_max_episode_steps"]))
            current = current.env
        assert limits and all(n == 200 for n in limits)
        self.length, self.radius, _ = vector(env.peg_half_sizes)
        self.hole = transform([0.05, 0.30, 0.15])
        self.nominal_tcp = transform(
            [-2 * self.length - 0.006 - 0.060, 0, 0],
            Rotation.from_euler("X", np.pi).as_matrix(),
        )
        disturbance = fault(self.job.candidate, self.length)
        peg_h = transform(
            [-2 * self.length - 0.006, disturbance["dy"], disturbance["dz"]],
            (
                Rotation.from_euler("Z", disturbance["yaw"])
                * Rotation.from_euler("Y", disturbance["pitch"])
            ).as_matrix(),
        )
        target_world = self.hole @ self.nominal_tcp
        self.command_h = self.nominal_tcp.copy()
        env.box.set_pose(
            Pose.create_from_pq(
                *self._pq(
                    self.hole
                    @ np.linalg.inv(pose_matrix(vector(env.box_hole_offsets.raw_pose)))
                )
            )
        )
        env.peg.set_pose(Pose.create_from_pq(*self._pq(self.hole @ peg_h)))
        env.peg.set_linear_velocity(torch.zeros((1, 3)))
        env.peg.set_angular_velocity(torch.zeros((1, 3)))
        q0 = np.array(
            [0, np.pi / 8, 0, -5 * np.pi / 8, 0, 3 * np.pi / 4, -np.pi / 4, 0.04, 0.04]
        )
        arm = env.agent.controller.controllers["arm"]
        gripper = env.agent.controller.controllers["gripper"]
        assert env.agent.control_mode == "pd_ee_pose"
        assert not arm.config.use_delta and not arm.config.normalize_action
        assert arm.config.frame == "root_translation:root_aligned_body_rotation"
        for controller in (arm, gripper):
            assert controller.config.stiffness == 1000
            assert controller.config.damping == 100
            assert controller.config.force_limit == 100
        kin = arm.kinematics
        base = pose_matrix(vector(arm.root_link.pose.raw_pose))
        goal_base = np.linalg.inv(base) @ target_world
        initial = q0[vector(kin.pmodel_active_joint_indices).astype(int)]
        result, success, error = kin.pmodel.compute_inverse_kinematics(
            kin.end_link_idx,
            sapien.Pose(pose_raw(goal_base)[:3], pose_raw(goal_base)[3:]),
            initial_qpos=initial,
            active_qmask=kin.qmask.cpu().numpy(),
            max_iterations=100,
        )
        self.configuration = {
            "length": float(self.length),
            "radius": float(self.radius),
            "fault_evaluator_only": disturbance,
            "wrapper_limits": limits,
            "control_mode": env.agent.control_mode,
            "physics_hz": 100,
            "control_hz": 20,
            "nominal_tcp_H": pose_raw(self.nominal_tcp),
            "initial_actual_peg_H": pose_raw(peg_h),
            "hole_world": pose_raw(self.hole),
            "native_IK_success": bool(success),
            "native_IK_error": plain(error),
            "arm_controller_config": {
                key: plain(getattr(arm.config, key))
                for key in (
                    "stiffness",
                    "damping",
                    "force_limit",
                    "frame",
                    "use_delta",
                    "use_target",
                    "normalize_action",
                    "interpolate",
                )
            },
            "method": "NOMINAL_SOURCE_EXPLORATORY_NOT_LEARNED_RPD",
            "native_hole_offset": vector(env.box_hole_offsets.raw_pose).tolist(),
            "native_peg_head_offset": vector(env.peg_head_offsets.raw_pose).tolist(),
            "gripper_controller_config": {
                key: plain(getattr(gripper.config, key))
                for key in ("stiffness", "damping", "force_limit", "normalize_action")
            },
        }
        if not success:
            return {
                "disposition": "KNOWN_INELIGIBLE",
                "reasons": ["INITIAL_IK_DID_NOT_CONVERGE"],
            }
        q0[vector(kin.pmodel_active_joint_indices).astype(int)] = np.asarray(result)
        q0[-2:] = 0.04
        env.agent.robot.set_qpos(torch.tensor(q0[None], dtype=torch.float32))
        env.agent.robot.set_qvel(torch.zeros((1, 9)))
        # Initialization only: all following controls proceed natively without reset.
        env.agent.controller.reset()
        actual = np.linalg.inv(base) @ pose_matrix(vector(env.agent.tcp.pose.raw_pose))
        residual_p = float(np.linalg.norm(actual[:3, 3] - goal_base[:3, 3]))
        residual_r = float(
            Rotation.from_matrix(goal_base[:3, :3].T @ actual[:3, :3]).magnitude()
        )
        self.configuration["initial_IK_checked_residual"] = [residual_p, residual_r]
        if residual_p > 0.0003 or residual_r > disturbance["theta_c"] / 10:
            return {
                "disposition": "KNOWN_INELIGIBLE",
                "reasons": ["INITIAL_IK_RESIDUAL_EXCEEDS_REGISTERED_BOUND"],
            }
        self.initial_e = np.linalg.inv(
            pose_matrix(vector(env.agent.tcp.pose.raw_pose))
        ) @ pose_matrix(vector(env.peg.pose.raw_pose))
        self.mass = float(vector(env.peg.mass)[0])
        self.configuration["peg_mass_kg"] = self.mass
        self.configuration["joint_limits"] = plain(env.agent.robot.get_qlimits())
        old_hook = env._after_simulation_step

        def hook():
            old_hook()
            self.substep += 1
            frame = self.measure()
            self.frames.append(frame)
            self.trace.write(json.dumps(frame, allow_nan=False) + "\n")

        env._after_simulation_step = hook
        self.record_initial = self.measure()
        for _ in range(10):
            self.step(self.nominal_tcp)
        for k in range(1, 21):
            target = self.nominal_tcp.copy()
            v = k / 20
            target[0, 3] += 0.009 * (3 * v**2 - 2 * v**3)
            self.step(target)
        self.root_e = np.linalg.inv(
            pose_matrix(vector(env.agent.tcp.pose.raw_pose))
        ) @ pose_matrix(vector(env.peg.pose.raw_pose))
        root_frame = self.measure(update_goal=False)
        self.root_command = self.command_h.copy()
        self.root = {
            "frame": root_frame,
            "controller": self.controller_memory(),
            "drive_targets": plain(env.agent.robot.get_drive_targets()),
            "native_elapsed_ticks": int(env.elapsed_steps[0]),
            "absolute_substep": self.substep,
            "goal_dwell": self.dwell,
            "completion_flag": self.completion,
            "command_H": pose_raw(self.command_h),
            "root_nominal_grasp_parameters": pose_raw(
                transform([0.060, 0, 0], Rotation.from_euler("X", np.pi).as_matrix())
            ),
        }
        recent = self.frames[-6:]
        reasons = []
        if self.completion:
            reasons.append("ALREADY_COMPLETED")
        if not root_frame["native_grasp"]:
            reasons.append("NO_NATIVE_TWO_FINGER_GRASP")
        if len(recent) != 6 or not all(f["peg_fixture_force_N"] >= 0.5 for f in recent):
            reasons.append("NO_PERSISTENT_REGISTERED_CONTACT")
        if not (0.00075 <= root_frame["tcp_residual_m"] <= 0.012):
            reasons.append("ROOT_TCP_RESIDUAL_OUTSIDE_REGISTERED_RANGE")
        reasons += [
            "ROOT_" + name
            for name, passed in root_frame["constraint_checks"].items()
            if not passed
        ]
        return {
            "disposition": "KNOWN_ELIGIBLE" if not reasons else "KNOWN_INELIGIBLE",
            "reasons": reasons,
        }

    @staticmethod
    def _pq(matrix):
        raw = pose_raw(matrix)
        return np.array(raw[:3], dtype=np.float32)[None], np.array(
            raw[3:], dtype=np.float32
        )[None]

    def controller_memory(self):
        return {
            name: {
                key: plain(getattr(controller, key))
                for key in (
                    "_step",
                    "_start_qpos",
                    "_target_qpos",
                    "_target_pose",
                    "_step_size",
                )
                if hasattr(controller, key)
            }
            for name, controller in self.env.agent.controller.controllers.items()
        }

    def measure(self, update_goal=True):
        env = self.env
        q, qv = vector(env.agent.robot.get_qpos()), vector(env.agent.robot.get_qvel())
        tcp = pose_matrix(vector(env.agent.tcp.pose.raw_pose))
        peg = pose_matrix(vector(env.peg.pose.raw_pose))
        hole = pose_matrix(vector(env.box_hole_pose.raw_pose))
        tcp_h = np.linalg.inv(hole) @ tcp
        relative = np.linalg.inv(self.nominal_tcp) @ tcp_h
        rotation_log = Rotation.from_matrix(relative[:3, :3]).as_rotvec()
        command_log = Rotation.from_matrix(
            self.nominal_tcp[:3, :3].T @ self.command_h[:3, :3]
        ).as_rotvec()
        residual = self.command_h[:3, 3] - tcp_h[:3, 3]
        force = vector(env.scene.get_pairwise_contact_forces(env.peg, env.box))
        fingers = (env.agent.finger1_link, env.agent.finger2_link)
        finger_forces = [
            vector(env.scene.get_pairwise_contact_forces(link, env.peg)).tolist()
            for link in fingers
        ]
        finger_directions = [
            pose_matrix(vector(link.pose.raw_pose))[:3, 1] * sign
            for link, sign in zip(fingers, (1, -1))
        ]
        nonfinger_contacts = []
        contacts = []
        robot_names = {
            obj.entity.name for link in env.agent.robot.links for obj in link._objs
        }
        finger_names = {
            obj.entity.name
            for link in (
                env.agent.finger1_link,
                env.agent.finger2_link,
                env.agent.finger1pad_link,
                env.agent.finger2pad_link,
            )
            if link is not None
            for obj in link._objs
        }
        object_names = {obj.name for actor in (env.peg, env.box) for obj in actor._objs}
        for contact in env.scene.get_contacts():
            names = [body.entity.name for body in contact.bodies]
            impulse = (
                np.sum([vector(p.impulse) for p in contact.points], axis=0)
                if contact.points
                else np.zeros(3)
            )
            norm = float(np.linalg.norm(impulse) / 0.01)
            contacts.append(
                {
                    "bodies": names,
                    "net_impulse_Ns": np.asarray(impulse).tolist(),
                    "net_force_N": norm,
                }
            )
            if set(names) & (robot_names - finger_names) and set(names) & object_names:
                nonfinger_contacts.append(norm)
        e = np.linalg.inv(tcp) @ peg
        reference = (
            self.root_e if self.root_e is not None else getattr(self, "initial_e", e)
        )
        slip = np.linalg.inv(reference) @ e
        limits = np.asarray(plain(env.agent.robot.get_qlimits())).reshape(9, 2)
        angle = float(Rotation.from_matrix(slip[:3, :3]).magnitude())
        frame = {
            "substep": self.substep,
            "time_seconds": self.substep / 100,
            "native_ticks_before_increment": int(env.elapsed_steps[0]),
            "qpos": q.tolist(),
            "qvel": qv.tolist(),
            "peg": pose_raw(peg),
            "fixture": vector(env.box.pose.raw_pose).tolist(),
            "hole": pose_raw(hole),
            "tcp": pose_raw(tcp),
            "peg_linear_velocity": vector(env.peg.linear_velocity).tolist(),
            "peg_angular_velocity": vector(env.peg.angular_velocity).tolist(),
            "peg_fixture_force_vector_N": force.tolist(),
            "peg_fixture_force_N": float(np.linalg.norm(force)),
            "native_grasp": bool(
                env.agent.is_grasping(env.peg, min_force=0.5, max_angle=85)[0]
            ),
            "finger_peg_forces_N": finger_forces,
            "finger_opening_directions": [v.tolist() for v in finger_directions],
            "contacts_evaluator_only": contacts,
            "tcp_residual_m": float(np.linalg.norm(residual)),
            "grasp_slip_translation_m": float(np.linalg.norm(slip[:3, 3])),
            "grasp_slip_rotation_rad": angle,
            "online_X": np.r_[
                q[:7],
                qv[:7],
                tcp_h[:3, 3],
                rotation_log,
                self.command_h[:3, 3],
                command_log,
                self.length,
                self.radius,
            ].tolist(),
            "online_Y_sample": np.r_[
                q[:7], qv[:7], tcp_h[:3, 3], rotation_log, residual
            ].tolist(),
            "command_H": pose_raw(self.command_h),
        }
        frame["constraint_checks"] = {
            "joint_limits": bool(
                np.all(q >= limits[:, 0] - 1e-7) and np.all(q <= limits[:, 1] + 1e-7)
            ),
            "joint_speed": bool(np.max(np.abs(qv[:7])) <= 2),
            "tcp_residual": frame["tcp_residual_m"] <= 0.012,
            "grasp_slip_translation": frame["grasp_slip_translation_m"] <= 0.003,
            "grasp_slip_rotation": angle <= 2 * np.arctan(0.003 / (2 * self.length)),
            "peg_fixture_force": frame["peg_fixture_force_N"] <= 10 * self.mass * 9.81,
            "nonfinger_robot_contact": max(nonfinger_contacts, default=0) <= 0.5,
        }
        frame["goal_components"] = goal_components(frame, self.length)
        if update_goal:
            self.dwell = self.dwell + 1 if all(frame["goal_components"].values()) else 0
            self.completion |= self.dwell >= 26
        frame["goal_dwell"] = self.dwell
        frame["completion_flag"] = self.completion
        frame["native_goal"] = bool(env.evaluate()["success"][0])
        assert len(frame["online_X"]) == 28 and len(frame["online_Y_sample"]) == 23
        # Serialization rejects all nonfinite records before any outcome is accepted.
        frame = plain(frame)
        json.dumps(frame, allow_nan=False)
        return frame

    def step(self, target_h):
        if time.monotonic() - self.started >= 60:
            raise TimeoutError("Registered60-second source-episode ceiling")
        self.command_h = np.asarray(target_h).copy()
        base = pose_matrix(vector(self.env.agent.robot.pose.raw_pose))
        target = np.linalg.inv(base) @ self.hole @ target_h
        angles = Rotation.from_matrix(target[:3, :3]).as_euler("XYZ")
        action = np.r_[target[:3, 3], angles, -1].astype(np.float32)
        before = self.substep
        _, _, terminated, truncated, _ = self.wrapped.step(action)
        self.tick += 1
        assert self.substep - before == 5
        assert int(self.env.elapsed_steps[0]) == self.tick
        assert not bool(truncated[0])
        self.command_log.append(
            {
                "control_tick": self.tick,
                "native_action": action.tolist(),
                "target_H": pose_raw(target_h),
                "native_terminated": bool(terminated[0]),
            }
        )

    def execute(self):
        eligibility = self.initialize()
        result = {
            "schema": SCHEMA,
            "job": self.job.model_dump(),
            "job_id": self.job.job_id,
            "status": "COMPLETE",
            "eligibility": eligibility,
            "configuration": self.configuration,
        }
        if (
            self.job.intervention == "screen"
            or eligibility["disposition"] != "KNOWN_ELIGIBLE"
        ):
            return result
        if self.job.intervention != "direct":
            for k in range(1, 11):
                self.step(probe_target(self.root_command, self.job.intervention, k))
        start = np.linalg.inv(self.hole) @ pose_matrix(
            vector(self.env.agent.tcp.pose.raw_pose)
        )
        previous = start
        for duration, endpoint in recovery_segments(
            start, self.length, self.job.action
        ):
            rotations = Rotation.from_matrix(
                np.stack([previous[:3, :3], endpoint[:3, :3]])
            )
            slerp = Slerp([0, 1], rotations)
            for k in range(1, duration + 1):
                v = k / duration
                target = transform(
                    previous[:3, 3]
                    + (endpoint[:3, 3] - previous[:3, 3]) * (3 * v**2 - 2 * v**3),
                    slerp(v).as_matrix(),
                )
                self.step(target)
            previous = endpoint
        while self.tick < 110:
            self.step(previous)
        assert self.tick == 110 and self.substep == 550
        result["terminal"] = {
            "completion": self.completion,
            "native_goal_at_deadline": self.frames[-1]["native_goal"],
            "diagnostic_path_compliant": all(
                all(f["constraint_checks"].values())
                for f in [self.root["frame"]] + self.frames[150:200]
            ),
            "whole_postroot_compliant": all(
                all(f["constraint_checks"].values())
                for f in [self.root["frame"]] + self.frames[150:]
            ),
        }
        return result

    def finish(self, result):
        self.trace.flush()
        self.trace.close()
        result.update(
            {
                "root": self.root,
                "configuration": self.configuration,
                "initial_record": getattr(self, "record_initial", None),
                "commands": self.command_log,
                "actual_physics_substeps": self.substep,
                "actual_control_ticks": self.tick,
                "elapsed_seconds": time.monotonic() - self.started,
                "root_reconstruction": "FRESH_INITIALIZATION_AND_FIXED_PREFIX_NO_STATE_RESTORE",
            }
        )
        with lzma.open(self.destination / "result.json.xz", "wt") as stream:
            json.dump(result, stream, allow_nan=False)
        if self.wrapped is not None:
            self.wrapped.close()


def main(path):
    faulthandler.enable(all_threads=True)
    verify_registration()
    job = Job.model_validate_json(Path(path).read_text())
    destination = Path(path).parent
    episode = AssemblyEpisode(job, destination)
    try:
        result = episode.execute()
    except Exception as exc:
        LOGGER.exception(
            "Frozen source row failed; preserve its trace and missing outcome"
        )
        result = {
            "schema": SCHEMA,
            "job": job.model_dump(),
            "job_id": job.job_id,
            "status": "SOURCE_ERROR",
            "eligibility": {"disposition": "UNKNOWN"},
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "traceback": traceback.format_exc(),
        }
    episode.finish(result)
    print(
        json.dumps(
            {
                "job_id": job.job_id,
                "status": result["status"],
                "eligibility": result["eligibility"],
            }
        ),
        flush=True,
    )
    return 0 if result["status"] == "COMPLETE" else 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True)
    raise SystemExit(main(parser.parse_args().job))
