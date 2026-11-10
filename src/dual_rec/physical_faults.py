"""Explicit CPU rigid-body edits; no force, observation or vendor-code patching."""

from __future__ import annotations

import numpy as np

from dual_rec.scenarios import Fault, PhysicalEdit


def body_parameters(body) -> dict:
    return {
        "mass_kg": float(body.mass),
        "inertia_kg_m2": np.asarray(body.inertia).tolist(),
        "center_of_mass_pose": np.r_[
            body.cmass_local_pose.p, body.cmass_local_pose.q
        ].tolist(),
        "shape_materials": [
            {
                "static_friction": float(s.physical_material.static_friction),
                "dynamic_friction": float(s.physical_material.dynamic_friction),
                "restitution": float(s.physical_material.restitution),
            }
            for s in body.collision_shapes
        ],
    }


def apply_fault(body, fault: Fault) -> PhysicalEdit:
    import sapien

    before = body_parameters(body)
    if fault.mass_scale != 1:
        body.set_mass(before["mass_kg"] * fault.mass_scale)
        body.set_inertia(
            np.asarray(before["inertia_kg_m2"], dtype=np.float32) * fault.mass_scale
        )
    if fault.friction is not None:
        for shape in body.collision_shapes:
            shape.physical_material = sapien.physx.PhysxMaterial(
                fault.friction, fault.friction, shape.physical_material.restitution
            )
    after = body_parameters(body)
    if not np.isclose(
        after["mass_kg"], before["mass_kg"] * fault.mass_scale, rtol=1e-6
    ):
        raise RuntimeError("Mass parameter readback mismatch")
    if not np.allclose(
        after["inertia_kg_m2"],
        np.asarray(before["inertia_kg_m2"]) * fault.mass_scale,
        rtol=1e-6,
        atol=0,
    ):
        raise RuntimeError("Inertia parameter readback mismatch")
    if before["center_of_mass_pose"] != after["center_of_mass_pose"]:
        raise RuntimeError("Density change moved center of mass/axes")
    if fault.friction is not None and any(
        not np.isclose(m[key], fault.friction, rtol=1e-6)
        for m in after["shape_materials"]
        for key in ("static_friction", "dynamic_friction")
    ):
        raise RuntimeError("Material readback mismatch")
    return PhysicalEdit(control_step=0, before=before, after=after)
