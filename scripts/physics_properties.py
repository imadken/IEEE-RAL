"""Bounded CPU mass/friction checks in standalone or actual ManiSkill scenes.

Condition metadata is kept in evaluation logs, outside physical observations.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import sapien
from sapien.physx import PhysxCpuSystem, PhysxRigidDynamicComponent

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def run(mass, friction):
    px = PhysxCpuSystem()
    scene = sapien.Scene([px])
    scene.set_timestep(1 / 240)
    material = sapien.physx.PhysxMaterial(friction, friction, 0)
    ground = scene.create_actor_builder()
    ground.add_box_collision(half_size=[1, 1, 0.01], material=material)
    ground.build_static("ground").set_pose(sapien.Pose(p=[0, 0, -0.01]))
    builder = scene.create_actor_builder()
    builder.add_box_collision(half_size=[0.02] * 3, material=material)
    actor = builder.build("cube")
    actor.set_pose(sapien.Pose(p=[0, 0, 0.02]))
    body = actor.find_component_by_type(PhysxRigidDynamicComponent)
    body.mass = mass
    for shape in body.collision_shapes:
        shape.physical_material.dynamic_friction = friction
        shape.physical_material.static_friction = friction
    for _ in range(60):
        scene.step()
    start = np.array(actor.pose.p)
    for _ in range(120):
        body.add_force_torque(
            np.array([0.3, 0, 0], dtype=np.float32), np.zeros(3, dtype=np.float32)
        )
        scene.step()
    observation = {
        "displacement": (np.array(actor.pose.p) - start).tolist(),
        "velocity": body.linear_velocity.tolist(),
    }
    return {
        "evaluation_only": {"mass_kg": body.mass, "friction": friction},
        "observation": observation,
    }


def run_task(task, mass_scale, friction):
    from mani_runner import make_env

    from dual_rec.replay import jsonable

    wrapped = make_env(task)
    try:
        wrapped.reset(seed=0)
        env = wrapped.unwrapped
        if env.gpu_sim_enabled:
            raise RuntimeError("Property qualification requires CPU physics")
        cube = env.obj if task == "PushCube-v1" else env.cube
        body = cube._objs[0].find_component_by_type(PhysxRigidDynamicComponent)
        nominal_mass = body.mass
        body.mass = nominal_mass * mass_scale
        # A fresh material avoids mutating a material shared with other actors.
        material = sapien.physx.PhysxMaterial(friction, friction, 0)
        for shape in body.collision_shapes:
            shape.physical_material = material
        for _ in range(round(0.25 / env.sim_timestep)):
            env.scene.step()
        start = np.array(cube._objs[0].pose.p)
        before = jsonable(env.get_obs())
        force = np.array([0.65, 0, 0], dtype=np.float32)
        for _ in range(round(0.25 / env.sim_timestep)):
            body.add_force_torque(force, np.zeros(3, dtype=np.float32))
            env.scene.step()
        return {
            "evaluation_only": {
                "task": task,
                "seed": 0,
                "sim_backend": "cpu",
                "nominal_mass_kg": nominal_mass,
                "mass_kg": body.mass,
                "inertia_kg_m2": body.inertia.tolist(),
                "shape_friction": [
                    {
                        "static": s.physical_material.static_friction,
                        "dynamic": s.physical_material.dynamic_friction,
                    }
                    for s in body.collision_shapes
                ],
                "force_newtons": force.tolist(),
                "force_seconds": 0.25,
                "timestep_seconds": env.sim_timestep,
                "protocol": "settle then force actual cube at each CPU physics step; no robot actions; robot remains dynamically simulated",
            },
            "observation": {
                "displacement": (np.array(cube._objs[0].pose.p) - start).tolist(),
                "velocity": body.linear_velocity.tolist(),
                "before": before,
                "after": jsonable(env.get_obs()),
            },
        }
    finally:
        wrapped.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=["PushCube-v1", "PickCube-v1"])
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # 4 cm cube: nominal 1000 kg/m^3 density, then twice the payload.
    rows = (
        [
            run_task(args.task, scale, friction)
            for scale, friction in [(1, 0.2), (2, 0.2), (1, 0.8)]
        ]
        if args.task
        else [run(0.064, 0.2), run(0.128, 0.2), run(0.064, 0.8)]
    )
    checks = {
        "mass_reduces_displacement": rows[0]["observation"]["displacement"][0]
        > rows[1]["observation"]["displacement"][0],
        "friction_reduces_displacement": rows[0]["observation"]["displacement"][0]
        > rows[2]["observation"]["displacement"][0],
        "finite_observations": all(
            np.isfinite(row["observation"]["displacement"]).all()
            and np.isfinite(row["observation"]["velocity"]).all()
            for row in rows
        ),
    }
    status = "passed" if all(checks.values()) else "failed"
    result = {"status": status, "checks": checks, "runs": rows}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if status == "passed" else 1)
