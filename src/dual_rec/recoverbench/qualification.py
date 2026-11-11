"""Audit released environment identity without waiving benchmark fingerprints."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .replay import load_original

_LOGGER = logging.getLogger(__name__)


class EngineeringEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    qualified_model: bool
    source_semantics_identified: bool
    official_generation_works: bool
    independently_successful_scenes: int = Field(ge=0, le=8)
    distinct_recovery_trajectories: int = Field(ge=0)
    leakage_or_hidden_reset: bool
    diagnostic_execution_works: bool


def engineering_decision(evidence: EngineeringEvidence) -> str:
    if (
        evidence.qualified_model
        and evidence.source_semantics_identified
        and evidence.official_generation_works
        and evidence.independently_successful_scenes >= 4
        and evidence.distinct_recovery_trajectories >= 2
        and not evidence.leakage_or_hidden_reset
    ):
        return "ENGINEERING_GO"
    if evidence.diagnostic_execution_works and (
        not evidence.qualified_model or not evidence.source_semantics_identified
    ):
        return "INCONCLUSIVE"
    return "ENGINEERING_NO_GO"


def canonical_xml(xml: str) -> str:
    """Normalize only known package path prefixes; preserve physical attributes."""
    tree = ET.fromstring(xml)
    for element in tree.iter():
        if "file" not in element.attrib:
            continue
        parts = element.attrib["file"].split("/")
        indexes = [
            i
            for i, v in enumerate(parts)
            if v in {"robosuite", "mimicgen", "robosuite_task_zoo"}
        ]
        if indexes:
            element.attrib["file"] = "/".join(parts[max(indexes) :])
    return ET.canonicalize(ET.tostring(tree, encoding="unicode"), strip_text=True)


def array_differences(left, right, *, atol=1e-12):
    """Compare named compiled fields, retaining missing fields and shape changes."""
    differences = {}
    for name in sorted(left.keys() | right.keys()):
        if name not in left or name not in right:
            differences[name] = {"reason": "missing_field"}
            continue
        a, b = np.asarray(left[name]), np.asarray(right[name])
        if a.shape != b.shape:
            differences[name] = {
                "reason": "shape",
                "left": list(a.shape),
                "right": list(b.shape),
            }
            continue
        if not np.allclose(a, b, atol=atol, rtol=0):
            delta = np.abs(a.astype(float) - b.astype(float))
            differences[name] = {
                "reason": "values",
                "max_abs_difference": float(delta.max()),
                "differing_entries": int(np.sum(delta > atol)),
            }
            if a.size <= 16:
                differences[name].update(left=a.tolist(), right=b.tolist())
    return differences


def compiled_arrays(model):
    prefixes = (
        "body_",
        "jnt_",
        "dof_",
        "geom_",
        "site_",
        "actuator_",
        "tendon_",
        "eq_",
        "pair_",
        "exclude_",
        "sensor_",
        "mesh_",
        "hfield_",
        "qpos0",
        "qpos_spring",
    )
    values = {}
    for name in dir(model):
        if name.startswith(prefixes):
            value = getattr(model, name)
            if isinstance(value, np.ndarray) and value.dtype.kind in "biuf":
                values[name] = value.copy()
    for name in dir(model.opt):
        if name.startswith("_"):
            continue
        value = getattr(model.opt, name)
        if isinstance(value, (int, float, np.ndarray)):
            values["option_" + name] = np.array(value)
    return values


def model_identities(model):
    import mujoco

    return {
        name: [mujoco.mj_id2name(model, kind, i) for i in range(getattr(model, count))]
        for name, kind, count in (
            ("bodies", mujoco.mjtObj.mjOBJ_BODY, "nbody"),
            ("joints", mujoco.mjtObj.mjOBJ_JOINT, "njnt"),
            ("geometries", mujoco.mjtObj.mjOBJ_GEOM, "ngeom"),
            ("actuators", mujoco.mjtObj.mjOBJ_ACTUATOR, "nu"),
            ("sites", mujoco.mjtObj.mjOBJ_SITE, "nsite"),
        )
    }


def controller_metadata(env):
    controller = env.robots[0].controller
    names = (
        "kp",
        "kd",
        "input_min",
        "input_max",
        "output_min",
        "output_max",
        "impedance_mode",
        "use_delta",
        "initial_joint",
        "interpolator_pos",
        "interpolator_ori",
    )
    result = {"class": type(controller).__name__, "action_dimension": env.action_dim}
    for name in names:
        value = getattr(controller, name, None)
        result[name] = value.tolist() if isinstance(value, np.ndarray) else value
    return result


def make_pickplace_adapter():
    """Restore the documented D0 yaw sampler only; class remains explicitly adapted."""
    from robosuite.environments.manipulation.pick_place import PickPlace

    class QualificationPickPlaceYawAdapter(PickPlace):
        def _get_placement_initializer(self):
            super()._get_placement_initializer()
            self.placement_initializer.samplers["CollisionObjectSampler"].rotation = (
                0.0,
                np.pi / 2,
            )

    return QualificationPickPlaceYawAdapter


def source_tree(root):
    return next((root / "upstream/source").iterdir())


def identity_audit(root):
    import h5py
    import mujoco
    import robosuite

    output = root / "identity"
    output.mkdir()
    registration = json.loads((root / "registration.json").read_text())
    results = []
    for task in ("stack", "pick_place"):
        calls = []
        original_make = robosuite.make

        def traced_make(name, *args, _calls=calls, _make=original_make, **kwargs):
            entry = {"requested": name, "kwargs": kwargs}
            _calls.append(entry)
            try:
                created = _make(name, *args, **kwargs)
                entry["actual_class"] = type(created).__name__
                return created
            except Exception as exc:
                entry["exception"] = repr(exc)
                entry["traceback"] = traceback.format_exc()
                raise

        np.random.seed(3101)
        with patch.object(robosuite, "make", traced_make):
            env, wrapper = load_original(root, task)
        env.reset()
        with h5py.File(root / "data/seed_demos" / f"{task}.hdf5", "r") as seed:
            meta = json.loads(seed["data"].attrs["env_args"])
            seed_xml = str(seed["data/demo_0"].attrs["model_file"])
        case = next(s for s in registration["sources"] if s["task"] == task)
        scene = json.loads(
            (
                root
                / "data/training_scenes"
                / task
                / "scenes"
                / (case["scene_id"] + ".json")
            ).read_text()
        )
        expected = scene["env_fingerprint"]
        current = wrapper.get_fingerprint()
        try:
            wrapper.verify_fingerprint(current, expected)
            fingerprint_error = None
        except Exception as exc:
            _LOGGER.exception("Preserving original fingerprint rejection")
            fingerprint_error = str(exc)
        xml = env.sim.model.get_xml()
        (output / f"{task}-factory.xml").write_text(xml)
        (output / f"{task}-seed.xml").write_text(seed_xml)
        arrays = compiled_arrays(env.sim.model._model)
        np.savez_compressed(output / f"{task}-factory-compiled.npz", **arrays)
        item = {
            "task": task,
            "factory_calls": calls,
            "seed_environment_metadata": meta,
            "actual_class": type(env).__name__,
            "robot": type(env.robots[0].robot_model).__name__,
            "gripper": type(env.robots[0].gripper).__name__,
            "controller": controller_metadata(env),
            "expected_fingerprint": expected,
            "actual_fingerprint": current,
            "fingerprint_error": fingerprint_error,
            "compiled_identities": model_identities(env.sim.model._model),
            "compiled_field_count": len(arrays),
            "seed_xml_sha1": hashlib.sha1(seed_xml.encode()).hexdigest(),
            "canonical_factory_sha256": hashlib.sha256(
                canonical_xml(xml).encode()
            ).hexdigest(),
            "canonical_seed_sha256": hashlib.sha256(
                canonical_xml(seed_xml).encode()
            ).hexdigest(),
            "versions": {
                "mujoco": mujoco.__version__,
                "robosuite": robosuite.__version__,
            },
        }
        # Compile a separate reference model; never replace the executing environment.
        try:
            relocated = env.edit_model_xml(seed_xml)
            (output / f"{task}-seed-relocated.xml").write_text(relocated)
            seed_model = mujoco.MjModel.from_xml_string(relocated)
            seed_arrays = compiled_arrays(seed_model)
            np.savez_compressed(output / f"{task}-seed-compiled.npz", **seed_arrays)
            item["seed_reference"] = {
                "compiled_identities": model_identities(seed_model),
                "identities_equal": model_identities(seed_model)
                == item["compiled_identities"],
                "compiled_differences": array_differences(arrays, seed_arrays),
                "asset_hashes": {
                    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for el in ET.fromstring(relocated).findall("asset/*")
                    if (name := el.get("file")) and (p := Path(name)).is_file()
                },
            }
        except Exception as exc:
            _LOGGER.exception("Seed reference compilation failed")
            item["seed_reference"] = {
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
        kwargs = dict(meta["env_kwargs"])
        kwargs.update(
            has_renderer=False, has_offscreen_renderer=False, use_camera_obs=False
        )
        try:
            strict = original_make(meta["env_name"], **kwargs)
            item["strict_constructor"] = {"actual_class": type(strict).__name__}
            strict.close()
        except Exception as exc:
            _LOGGER.exception("Strict registered constructor failed")
            item["strict_constructor"] = {
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
        if task == "pick_place":
            try:
                adapted = make_pickplace_adapter()(**kwargs)
                item["adapted_diagnostic"] = {
                    "class": type(adapted).__name__,
                    "official_qualified": False,
                    "yaw_rotation": adapted.placement_initializer.samplers[
                        "CollisionObjectSampler"
                    ].rotation,
                    "compiled_differences_from_base": array_differences(
                        arrays, compiled_arrays(adapted.sim.model._model)
                    ),
                    "semantic_difference": "Base factory samples full yaw; adapter samples 0..pi/2 as documented by pinned PickPlace_D0",
                }
                adapted.close()
            except Exception as exc:
                _LOGGER.exception("Adapted diagnostic constructor failed")
                item["adapted_diagnostic"] = {
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
        item["official_qualified"] = (
            fingerprint_error is None and item["actual_class"] == meta["env_name"]
        )
        item["unresolved_obligations"] = [
            "No source failure-scene XML or compiled parameter snapshot binds the recorded fingerprint to this model",
            "Seed XML is a clean-demo reference, not the missing failure-scene model",
            "Textual canonicalization alone cannot establish physical equivalence",
        ]
        results.append(item)
        env.close()
        print(
            json.dumps(
                {
                    "task": task,
                    "qualified": item["official_qualified"],
                    "seed_reference_error": item["seed_reference"].get("error"),
                    "compiled_difference_fields": len(
                        item["seed_reference"].get("compiled_differences", {})
                    ),
                }
            ),
            flush=True,
        )
    (root / "identity.json").write_text(json.dumps({"tasks": results}, indent=2) + "\n")


def generation_preflight(root):
    import h5py

    upstream = source_tree(root)
    sys.path.insert(0, str(upstream))
    paths = [
        upstream / "data/mimicgen_prepared/stack_d0_prepared.hdf5",
        root / "data/mimicgen_prepared/stack_d0_prepared.hdf5",
    ]
    result = {
        "prepared_source_paths": {str(p): p.exists() for p in paths},
        "generator_scenes_registered": json.loads(
            (root / "registration.json").read_text()
        )["generator_scenes"],
        "generation_attempts": 0,
        "independent_generated_rollouts": 0,
    }
    with h5py.File(root / "data/seed_demos/stack.hdf5", "r") as seed:
        keys = list(seed["data"])
        result["raw_seed_demos"] = len(keys)
        result["raw_seed_prepared_datagen_info"] = sum(
            "datagen_info" in seed["data"][k] for k in keys
        )
    try:
        from mimicgen.datagen.data_generator import DataGenerator

        result["DataGenerator_import"] = DataGenerator.__module__
    except Exception as exc:
        _LOGGER.exception("Official generator import unavailable")
        result["DataGenerator_import_error"] = repr(exc)
        result["DataGenerator_import_traceback"] = traceback.format_exc()
    result["robomimic_available"] = importlib.util.find_spec("robomimic") is not None
    result["torch_available"] = importlib.util.find_spec("torch") is not None
    result["status"] = "SOURCE_GENERATION_BLOCKED"
    result["reason"] = (
        "Released generator requires prepared source HDF5 with datagen_info and interface attributes; acquired raw seed has none. Contract directs stopping Stage C if prepared sources/interfaces are unavailable."
    )
    (root / "generation_preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("identity", "generation-preflight"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    if args.stage == "identity":
        identity_audit(args.root)
    else:
        generation_preflight(args.root)


if __name__ == "__main__":
    main()
