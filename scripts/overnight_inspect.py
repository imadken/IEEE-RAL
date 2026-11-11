"""Read pinned contact APIs and nominal PickCube execution without research faults."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mani_runner import make_env, record, scripted_action

from dual_rec.physical_faults import body_parameters
from dual_rec.replay import jsonable
from dual_rec.validation import array

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
wrapped = make_env("PickCube-v1")
try:
    obs, _ = wrapped.reset(seed=0)
    env = wrapped.unwrapped
    cube = env.cube
    from sapien.physx import PhysxRigidDynamicComponent

    body = cube._objs[0].find_component_by_type(PhysxRigidDynamicComponent)
    fingers = {}
    for link in env.agent.robot.links:
        if "finger" in link.name:
            fingers[link.name] = [
                {
                    "static": s.physical_material.static_friction,
                    "dynamic": s.physical_material.dynamic_friction,
                    "restitution": s.physical_material.restitution,
                }
                for physical in link._objs
                for s in physical.collision_shapes
            ]
    initial = array(cube.pose.p).reshape(3)
    goal = array(env.goal_site.pose.p).reshape(3)
    trace = []
    for phase, length in [(0, 20), (1, 25), (2, 15), (3, 30)]:
        for _ in range(length):
            obs, *_ = wrapped.step(
                scripted_action(
                    "PickCube-v1", initial, goal, env.agent.tcp.pose.p, phase
                )
            )
            r = record(env, cube, obs)
            trace.append(
                {
                    "step": len(trace) + 1,
                    "phase": phase,
                    "position": r["position"],
                    "tcp": array(env.agent.tcp.pose.raw_pose),
                    "contact": r["robot_object_contact"],
                    "grasped": bool(env.agent.is_grasping(cube)[0]),
                    "success": r["success"],
                    "contacts": r["contacts"],
                }
            )
    result = {
        "cube_parameters": body_parameters(body),
        "finger_materials": fingers,
        "task_obs_keys": {
            k: list(v) if isinstance(v, dict) else type(v).__name__
            for k, v in obs.items()
        },
        "joint_wrench_shape": list(
            array(env.agent.robot.get_link_incoming_joint_forces()).shape
        ),
        "combine_rule_exposed": any(
            "combin" in name.lower()
            for name in dir(body.collision_shapes[0].physical_material)
        ),
        "nominal_trace": trace,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.open("x").write(json.dumps(jsonable(result), indent=2, allow_nan=False))
    print(
        json.dumps(
            jsonable({k: v for k, v in result.items() if k != "nominal_trace"}),
            indent=2,
        )
    )
finally:
    wrapped.close()
