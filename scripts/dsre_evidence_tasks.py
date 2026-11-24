"""Frozen task adapters, executed one branch per fresh foreground process.

This harness contains scripted controllers only. It imports no recovery learner.
"""

import argparse
import gzip
import hashlib
import heapq
import importlib.metadata
import json
import logging
import random
import time
from itertools import pairwise
from pathlib import Path

import numpy as np

NAV_VOCAB = (
    "goal_distance_le_1",
    "speed_le_point2",
    "waypoint_segment_free",
    "progress5_ge_point1",
    "route_distance_le_point35",
    "route_goal_consistent",
)
PEG_VOCAB = (
    "transverse_le_3mm",
    "axis_angle_le_5deg",
    "depth_progress5_ge_1mm",
    "tip_entrance_le_2cm",
    "aperture_below_source_threshold",
    "tcp_tracking_le_5mm",
)
PEG_V2_VOCAB = tuple(name for i, name in enumerate(PEG_VOCAB) if i != 4)


def peg_observation_v2(telemetry):
    """Exclude unsupported aperture from the grammar; preserve UNKNOWN telemetry."""
    if len(telemetry) != 6 or telemetry[4] is not None:
        raise ValueError("Peg aperture must remain UNKNOWN")
    return [value for i, value in enumerate(telemetry) if i != 4]


def plain(x):
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [plain(v) for v in x]
    if hasattr(x, "raw_pose"):
        return plain(x.raw_pose)
    if hasattr(x, "detach"):
        return plain(x.detach().cpu().numpy())
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    return x


def hashfile(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "xt", compresslevel=6) as f:
        json.dump(plain(value), f, allow_nan=False)


def grid_route(maze, start, goal):
    free = sorted(
        (i, j)
        for i, row in enumerate(maze.maze_map)
        for j, value in enumerate(row)
        if value != 1
    )
    positions = {ij: maze.cell_rowcol_to_xy(np.asarray(ij)) for ij in free}
    # Nearest free center; lexicographic row/column tie-breaking is fixed.
    snap = lambda x: min(
        free, key=lambda ij: (float(np.sum((positions[ij] - x) ** 2)), ij)
    )
    first, last = snap(start), snap(goal)
    queue = [(0, 0, first, (first,))]
    seen = set()
    while queue:
        _, cost, node, path = heapq.heappop(queue)
        if node in seen:
            continue
        seen.add(node)
        if node == last:
            return [positions[ij].copy() for ij in path] + [np.asarray(goal).copy()]
        for nxt in sorted(
            (node[0] + di, node[1] + dj)
            for di, dj in ((-1, 0), (0, -1), (0, 1), (1, 0))
        ):
            if nxt in positions and nxt not in seen:
                h = abs(nxt[0] - last[0]) + abs(nxt[1] - last[1])
                heapq.heappush(queue, (cost + 1 + h, cost + 1, nxt, path + (nxt,)))
    raise RuntimeError("No static-map path")


def tracker(obs, route, index):
    pos, vel = obs["observation"][:2], obs["observation"][2:4]
    while index < len(route) - 1 and np.linalg.norm(route[index] - pos) <= 0.20:
        index += 1
    return np.clip(2 * (route[index] - pos) - 0.8 * vel, -1, 1), index


def segment_distance(p, a, b):
    delta = b - a
    t = np.clip(np.dot(p - a, delta) / max(np.dot(delta, delta), 1e-15), 0, 1)
    return float(np.linalg.norm(p - a - t * delta))


def navigate(spec, action):
    import gymnasium as gym
    import gymnasium_robotics
    from gymnasium_robotics.envs.maze import maze_v4, point, point_maze

    gym.register_envs(gymnasium_robotics)
    env = gym.make(
        "PointMaze_UMaze-v3",
        continuing_task=False,
        reset_target=False,
        max_episode_steps=220,
    )
    e = env.unwrapped
    obs, _ = env.reset(seed=spec["seed"])
    maze = e.maze
    assert maze.maze_map == [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    for ij in ((1, 1), (1, 3), (3, 1), (3, 3)):
        xy = maze.cell_rowcol_to_xy(np.asarray(ij))
        assert tuple(maze.cell_xy_to_rowcol(xy)) == ij
    started = time.perf_counter()
    route = grid_route(
        maze, obs["observation"][:2] + np.asarray(spec["offset"]), obs["desired_goal"]
    )
    planning = time.perf_counter() - started
    index, frames, controls = 0, [], []

    def state():
        d = e.point_env.data
        return plain(
            {
                "qpos": d.qpos.copy(),
                "qvel": d.qvel.copy(),
                "qacc": d.qacc.copy(),
                "warmstart": d.qacc_warmstart.copy(),
                "ctrl": d.ctrl.copy(),
                "time": float(d.time),
                "contacts": [
                    (
                        int(c.geom1),
                        int(c.geom2),
                        float(c.dist),
                        c.pos.copy(),
                        c.frame.copy(),
                    )
                    for c in d.contact
                ],
                "obs": obs,
                "rng": e.np_random.bit_generator.state,
                "point_rng": e.point_env.np_random.bit_generator.state,
                "goal": e.goal.copy(),
                "route": route,
                "index": index,
            }
        )

    frames.append(state())
    try:
        for _ in range(20):
            command, index = tracker(obs, route, index)
            obs, _, terminated, truncated, info = env.step(command.astype(np.float32))
            controls.append(plain(command.astype(np.float32)))
            frames.append(state())
            if terminated or truncated:
                return {
                    "status": "ALREADY_SOLVED_PREFIX"
                    if info["success"]
                    else "FAILED_PREFIX",
                    "prefix": frames,
                    "prefix_controls": controls,
                    "post": [],
                    "success": bool(info["success"]),
                    "features": None,
                    "planning_seconds": planning,
                }
        pos, vel = obs["observation"][:2], obs["observation"][2:4]
        remaining = route[index:]
        route_dist = min(
            [float(np.linalg.norm(p - pos)) for p in remaining]
            + [segment_distance(pos, a, b) for a, b in pairwise(remaining)]
        )
        # Check segment against the exact static cell geometry (sample spacing < .01).
        segment = np.linspace(
            pos,
            route[index],
            max(2, int(np.linalg.norm(pos - route[index]) / 0.005) + 1),
        )

        def free(p):
            i, j = maze.cell_xy_to_rowcol(p)
            return (
                0 <= i < len(maze.maze_map)
                and 0 <= j < len(maze.maze_map[0])
                and maze.maze_map[i][j] != 1
            )

        before5 = np.asarray(frames[-6]["obs"]["observation"][:2])

        # Geometric progress along the remaining fixed route, over the last five controls.
        def remaining_length(p, idx):
            return float(np.linalg.norm(p - route[idx])) + sum(
                float(np.linalg.norm(b - a))
                for a, b in zip(route[idx:], route[idx + 1 :])
            )

        progress = remaining_length(before5, frames[-6]["index"]) - remaining_length(
            pos, index
        )
        features = [
            np.linalg.norm(pos - obs["desired_goal"]) <= 1,
            np.linalg.norm(vel) <= 0.2,
            all(free(p) for p in segment),
            progress >= 0.1,
            route_dist <= 0.35,
            np.array_equal(route[-1], obs["desired_goal"]),
        ]
        checkpoint = state()
        if action == "screen":
            return {
                "status": "CHECKPOINT_ONLY",
                "prefix": frames,
                "prefix_controls": controls,
                "checkpoint": checkpoint,
                "features": plain(features),
                "planning_seconds": planning,
            }
        if action == "r":
            then = time.perf_counter()
            route = grid_route(maze, pos, obs["desired_goal"])
            index = 0
            planning += time.perf_counter() - then
        post = []
        post_controls = []
        effort = 0.0
        for _ in range(200):
            command, index = tracker(obs, route, index)
            command = command.astype(np.float32)
            obs, _, terminated, truncated, info = env.step(command)
            post_controls.append(plain(command))
            effort += float(np.sum(command**2))
            post.append(state())
            if terminated or truncated:
                break
        source = {
            str(Path(m.__file__).resolve()): hashfile(m.__file__)
            for m in (maze_v4, point, point_maze)
        }
        return {
            "status": "COMPLETE",
            "prefix": frames,
            "prefix_controls": controls,
            "checkpoint": checkpoint,
            "features": plain(features),
            "post": post,
            "post_controls": post_controls,
            "success": bool(info["success"]),
            "effort": effort,
            "planning_seconds": planning,
            "source_sha256": source,
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("gymnasium-robotics", "gymnasium", "mujoco", "numpy")
            },
            "model_sha256": hashfile(e.point_env.fullpath),
            "episodic": True,
            "horizon": 200,
            "terminated_absorbing": bool(terminated),
        }
    finally:
        env.close()


class HorizonReached(Exception):
    pass


def insertion(spec, action):
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401
    import mplib
    import sapien
    import torch
    from mani_skill.examples.motionplanning.base_motionplanner.utils import (
        compute_grasp_info_by_obb,
        get_actor_obb,
    )
    from mani_skill.examples.motionplanning.panda.motionplanner import (
        PandaArmMotionPlanningSolver,
    )
    from mani_skill.examples.motionplanning.panda.solutions import peg_insertion_side
    from mani_skill.utils.structs.pose import to_sapien_pose

    random.seed(spec["seed"])
    np.random.seed(spec["seed"])
    torch.manual_seed(spec["seed"])
    if hasattr(mplib, "set_global_seed"):
        mplib.set_global_seed(spec["seed"])
    # TimeLimit is declared before any trial: prefix <=2000, future exactly400.
    env = gym.make(
        "PegInsertionSide-v1",
        num_envs=1,
        sim_backend="cpu",
        render_backend="none",
        obs_mode="state_dict",
        control_mode="pd_joint_pos",
        max_episode_steps=2400,
    )
    e = env.unwrapped
    env.reset(seed=spec["seed"])
    planner = PandaArmMotionPlanningSolver(
        env,
        debug=False,
        vis=False,
        base_pose=e.agent.robot.pose,
        visualize_target_grasp_pose=False,
        print_env_info=False,
        joint_vel_limits=0.75,
        joint_acc_limits=0.75,
    )
    prefix = []
    prefix_controls = []
    post = []
    post_controls = []
    phase = "prefix"
    tracking_target = None
    planning = 0.0
    original_step = env.step

    def state():
        return plain(
            {
                "physical": e.get_state_dict(),
                "controller": e.agent.controller.get_state(),
                "qpos": e.agent.robot.get_qpos(),
                "qvel": e.agent.robot.get_qvel(),
                "contacts": [
                    (
                        a.bodies[0].entity.name,
                        a.bodies[1].entity.name,
                        a.points[0].position if a.points else [],
                    )
                    for a in e.scene.get_contacts()
                ],
                "elapsed": e.elapsed_steps,
                "peg": e.peg.pose.raw_pose,
                "hole": e.box_hole_pose.raw_pose,
                "tcp": e.agent.tcp.pose.raw_pose,
                "gripper": planner.gripper_state,
                "planner_elapsed": planner.elapsed_steps,
                "planner_limits": planner.planner.joint_vel_limits,
                "planner_acc_limits": planner.planner.joint_acc_limits,
                "base_pose": np.r_[planner.base_pose.p, planner.base_pose.q],
                "drive_targets": e.agent.robot.drive_targets,
                "drive_velocities": e.agent.robot.drive_velocities,
                "controller_transient": {
                    n: {
                        k: getattr(c, k)
                        for k in (
                            "_step",
                            "_start_qpos",
                            "_target_qpos",
                            "_step_size",
                            "_target_pose",
                        )
                        if hasattr(c, k)
                    }
                    for n, c in e.agent.controller.controllers.items()
                },
                "torch_rng": torch.get_rng_state(),
                "numpy_rng": np.random.get_state(),
                "python_rng": random.getstate(),
                "batched_rng": [r.get_state() for r in e._batched_episode_rng.rngs],
            }
        )

    def step(command):
        if phase == "post" and len(post) >= 400:
            raise HorizonReached()
        if phase == "prefix" and len(prefix_controls) >= 2000:
            raise RuntimeError("Fixed prefix cap reached")
        output = original_step(command)
        if phase == "prefix":
            prefix_controls.append(plain(command))
            prefix.append(state())
        else:
            post_controls.append(plain(command))
            post.append(state())
        return output

    env.step = step

    def move(pose):
        nonlocal planning, tracking_target
        tracking_target = to_sapien_pose(pose)
        then = time.perf_counter()
        result = planner.move_to_pose_with_screw(pose, dry_run=True)
        planning += time.perf_counter() - then
        if isinstance(result, int) and result == -1:
            raise RuntimeError("UPSTREAM_SCREW_PLANNING_FAILED")
        planner.follow_path(result)

    try:
        prefix.append(state())
        obb = get_actor_obb(e.peg)
        closing_target = (
            e.agent.tcp.pose.to_transformation_matrix()[0, :3, 1].cpu().numpy()
        )
        peg_init = e.peg.pose
        grasp_info = compute_grasp_info_by_obb(
            obb,
            approaching=np.array([0, 0, -1]),
            target_closing=closing_target,
            depth=0.025,
        )
        grasp = e.agent.build_grasp_pose(
            np.array([0, 0, -1]), grasp_info["closing"], grasp_info["center"]
        )
        grasp = grasp * sapien.Pose(
            [-max(0.05, e.peg_half_sizes[0, 0].item() / 2 + 0.01), 0, 0]
        )
        move(grasp * sapien.Pose([0, 0, -0.05]))
        move(grasp)
        planner.close_gripper()
        cached = e.goal_pose * peg_init.inv() * grasp
        hole = to_sapien_pose(e.box_hole_pose)
        displacement = hole.to_transformation_matrix()[:3, :3] @ np.array(
            [0, spec["offset"], 0]
        )
        cached = to_sapien_pose(cached)
        cached = sapien.Pose(cached.p + displacement, cached.q)
        offset = sapien.Pose([-0.01 - e.peg_half_sizes[0, 0].item(), 0, 0])
        pre = cached * offset
        move(pre)
        checkpoint = state()

        # No physical aperture threshold is provided in this source: unknown.
        def geometry(packet):
            peg = packet["peg"][0]
            hole_raw = packet["hole"][0]
            hp = sapien.Pose(hole_raw[:3], hole_raw[3:])
            pp = sapien.Pose(peg[:3], peg[3:])
            local = hp.inv() * pp
            tip = (
                local.p
                + local.to_transformation_matrix()[:3, 0]
                * e.peg_half_sizes[0, 0].item()
            )
            angle = float(
                np.arccos(np.clip(local.to_transformation_matrix()[0, 0], -1, 1))
            )
            return tip, angle

        tip, angle = geometry(checkpoint)
        oldtip, _ = geometry(prefix[-6] if len(prefix) >= 6 else prefix[0])
        tcp = to_sapien_pose(e.agent.tcp.pose)
        features = [
            float(np.linalg.norm(tip[1:])) <= 0.003,
            angle <= np.deg2rad(5),
            float(tip[0] - oldtip[0]) >= 0.001,
            float(
                np.linalg.norm(tip - np.array([-e.peg_half_sizes[0, 0].item(), 0, 0]))
            )
            <= 0.02,
            None,
            float(np.linalg.norm(tcp.p - tracking_target.p)) <= 0.005,
        ]
        telemetry = features.copy()
        if spec.get("observation_protocol") == "Peg-observation-v2":
            features = peg_observation_v2(telemetry)
        source_geometry = {
            "peg_half_sizes": plain(e.peg_half_sizes),
            "hole_radii": plain(e.box_hole_radii),
            "initial_physical": prefix[0]["physical"],
        }
        if action == "screen":
            return {
                "status": "CHECKPOINT_ONLY",
                "prefix": prefix,
                "prefix_controls": prefix_controls,
                "checkpoint": checkpoint,
                "features": features,
                "feature_telemetry": telemetry,
                "geometry": source_geometry,
                "planning_seconds": planning,
            }
        phase = "post"
        try:
            if action == "r":
                for _ in range(3):
                    delta = e.goal_pose * offset * e.peg.pose.inv()
                    pre = to_sapien_pose(delta) * pre
                    move(pre)
                # Declared adapter: recompute current-geometry insertion target.
                target = e.goal_pose * e.peg.pose.inv() * e.agent.tcp.pose
                move(to_sapien_pose(target) * sapien.Pose([0.05, 0, 0]))
            else:
                move(cached * sapien.Pose([0.05, 0, 0]))
        except HorizonReached:
            pass
        hold = np.r_[
            e.agent.robot.get_qpos()[0, :7].cpu().numpy(), planner.gripper_state
        ]
        while len(post) < 400:
            env.step(hold)
        return {
            "status": "COMPLETE",
            "prefix": prefix,
            "prefix_controls": prefix_controls,
            "checkpoint": checkpoint,
            "post": post,
            "post_controls": post_controls,
            "features": features,
            "feature_telemetry": telemetry,
            "geometry": source_geometry,
            "success": bool(e.evaluate()["success"][0]),
            "planning_seconds": planning,
            "horizon": 400,
            "source_sha256": {
                peg_insertion_side.__file__: hashfile(peg_insertion_side.__file__)
            },
            "unknown_reason": "No aperture threshold defined by installed source; normalized CLOSED=-1 is not a measured aperture.",
        }
    except Exception as error:
        logging.getLogger(__name__).exception(
            "Task adapter failed; retain complete attempt"
        )
        import traceback

        failure = {
            "status": "FAILED_PREREQUISITE_OR_PREFIX"
            if phase == "prefix"
            else "MISSING_TERMINAL_OUTCOME",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "prefix": prefix,
            "prefix_controls": prefix_controls,
            "post": post,
            "post_controls": post_controls,
            "phase": phase,
        }
        if phase == "post":
            failure.update(
                checkpoint=checkpoint,
                features=features,
                feature_telemetry=telemetry,
                geometry=source_geometry,
                horizon=400,
                action_stopped=True,
                executed_controls=len(post_controls),
            )
            # An abort stops this macro. Read its actual endpoint, never infer 0
            # from a planner return code or execute compensating controls.
            try:
                terminal = state()
                success = bool(e.evaluate()["success"][0])
                failure.update(
                    status="OBSERVED_ABORT_ENDPOINT",
                    terminal=terminal,
                    success=success,
                    terminal_observed=True,
                )
            except Exception as endpoint_error:  # noqa: BLE001 - unreadable endpoints remain MISSING
                failure["endpoint_error"] = str(endpoint_error)
        return failure
    finally:
        planner.close()
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--action", choices=("c", "r", "screen"), required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    start = time.perf_counter()
    try:
        result = (navigate if spec["task"] == "PointMaze_UMaze-v3" else insertion)(
            spec, args.action
        )
    except Exception as error:
        logging.getLogger(__name__).exception(
            "Task adapter failed; retain complete attempt"
        )
        import traceback

        result = {
            "status": "FAILED_PREREQUISITE_OR_PREFIX",
            "error_type": type(error).__name__,
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
    result.update(
        spec=spec, action=args.action, wall_seconds=time.perf_counter() - start
    )
    write(args.output, result)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k in ("status", "success", "error", "wall_seconds")
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
