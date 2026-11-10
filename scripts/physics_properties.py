"""Verify documented SAPIEN CPU mass/friction API without renderer.

This is a low-level sanity check, not a substitute for blocked Panda tasks.
No condition metadata is inserted into the returned physical observation.
"""

import json
from pathlib import Path

import numpy as np
import sapien
from sapien.physx import PhysxCpuSystem, PhysxRigidDynamicComponent


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


if __name__ == "__main__":
    # 4 cm cube: nominal 1000 kg/m^3 density, then twice the payload.
    rows = [run(0.064, 0.2), run(0.128, 0.2), run(0.064, 0.8)]
    assert (
        rows[0]["observation"]["displacement"][0]
        > rows[1]["observation"]["displacement"][0]
    )
    assert (
        rows[0]["observation"]["displacement"][0]
        > rows[2]["observation"]["displacement"][0]
    )
    Path("results/physical_properties.json").write_text(
        json.dumps({"status": "passed", "runs": rows}, indent=2)
    )
    print(json.dumps(rows, indent=2))
