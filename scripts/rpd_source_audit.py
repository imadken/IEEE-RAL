"""Native-interface audit and inactive two-task adapter specification.

Reads source, package metadata and sealed historical D/C sensor fields.
Never imports or constructs a simulator; no old outcome enters the planner.
"""

import argparse
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path

from dsre_closure_common import INPUTS, read

from dual_rec.recoverability.adapters import mask_native_state, probe_commands

BASE = Path("research/rpd_method_challenge")
PACKAGE = Path(".venv/lib/python3.12/site-packages/mani_skill")


def run(output):
    assert not output.exists(), "Use a fresh output directory"
    output.mkdir(parents=True)
    files = [
        Path(p)
        for p in (
            "scripts/mani_runner.py",
            "scripts/overnight_replay.py",
            "scripts/dsre_paper_physics.py",
            "src/dual_rec/overnight_pick.py",
            "src/dual_rec/replay.py",
            "src/dual_rec/validation.py",
        )
    ]
    files += [
        PACKAGE / p
        for p in (
            "envs/tasks/tabletop/pick_cube.py",
            "envs/tasks/tabletop/push_cube.py",
            "agents/robots/panda/panda.py",
            "agents/base_agent.py",
            "envs/sapien_env.py",
            "utils/structs/types.py",
            "agents/controllers/pd_ee_pose.py",
            "assets/robots/panda/panda_v3.urdf",
        )
    ]
    missing = [str(p) for p in files if not p.exists()]
    assert not missing, missing
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    runner = Path("scripts/mani_runner.py").read_text()
    native = (PACKAGE / "envs/sapien_env.py").read_text()
    assert 'obs_mode="state_dict"' in runner and 'render_backend="none"' in runner
    assert 'control_mode="pd_ee_delta_pos"' in runner
    assert (
        "qpos=self.robot.get_qpos(), qvel=self.robot.get_qvel()"
        in (PACKAGE / "agents/base_agent.py").read_text()
    )
    assert "control_freq: int = 20" in (PACKAGE / "utils/structs/types.py").read_text()
    assert '"Get (ground-truth) state-based observations.' in native
    for p in Path("src/dual_rec/recoverability").glob("*.py"):
        tree = ast.parse(p.read_text())
        imported = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imported += [
            a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
        ]
        assert not any(
            name
            and name.split(".")[0]
            in {"mani_skill", "sapien", "gymnasium", "mujoco", "subprocess"}
            for name in imported
        )
        forbidden = [
            n.func.attr
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr
            in {"reset", "step", "set_state", "set_state_dict", "set_pose"}
        ]
        assert not forbidden, (p, forbidden)
    # The old D/C records prove channel availability only. They do not supply
    # post-probe outcomes, new qualification or a calibrated success predicate.
    previous = read(
        Path("research/err_method_challenge/final/robot/robot_context_witnesses.json")
    )
    sensor_examples = []
    for task, index in (("PickCube-v1", 65), ("PushCube-v1", 53)):
        anchor = previous["tasks"][task]["actual_predecision_anchors"][0]
        assert anchor["phase"] in ("discovery", "calibration")
        native = read(Path(anchor["native"]))
        assert INPUTS[anchor["native"]] == anchor["original_gzip_sha256"]
        frame = mask_native_state(native["prefix"][index])
        assert abs(frame.time_seconds - index / 20) < 1e-9
        sensor_examples.append(
            {
                "task": task,
                "historical_parent_id": anchor["parent_id"],
                "original_phase": anchor["phase"],
                "prefix_control_index": index,
                "source": anchor["native"],
                "original_sha256": anchor["original_gzip_sha256"],
                "masked_real_frame": frame.model_dump(mode="json"),
                "scope": "ORIGINAL_SEALED_D_C_SENSOR_FIELDS_ONLY; not new probe effects, new checkpoint replay qualification or calibration",
            }
        )
    specs = []
    for task, prefix, probes in [
        ("PickCube-v1", 65, ("micro_lift", "release_settle")),
        ("PushCube-v1", 53, ("forward_tap", "lateral_sweep")),
    ]:
        specs.append(
            {
                "task_id": task,
                "robot": "panda",
                "status": "DESIGNED_NOT_EXECUTED",
                "sim_backend": "cpu",
                "render_backend": "none",
                "obs_mode": "state_dict",
                "control_mode": "pd_ee_delta_pos",
                "control_hz": 20,
                "max_episode_steps": 200,
                "checkpoint": {
                    "function": "scripts/overnight_replay.py:prefix_to_stage(world,'transport')",
                    "exact_controls": prefix,
                    "schedule": [[0, 20], [1, 25], [2, 15], [3, 5]]
                    if prefix == 65
                    else [[0, 20], [1, 25], [2, 8]],
                    "requires_native_task_success_false": True,
                    "condition": "nominal; cached source targets and natural reset distribution frozen",
                    "new_checkpoint_requires_independent_qualification": True,
                },
                "measured_channels": [
                    "observation.agent.qpos[0][0:7]",
                    "observation.agent.qvel[0][0:7]",
                    "observation.extra.tcp_pose[0][0:3]",
                    "time",
                ],
                "sensor_interpretation": "Ideal native arm proprioception and FK TCP estimate; not force, aperture, tactile contact or real robot sensing",
                "excluded_planner_channels": [
                    "finger joints",
                    "obj_pose",
                    "is_grasped",
                    "contacts",
                    "wrenches",
                    "applied_qf",
                    "fault label",
                    "future success",
                ],
                "controller_privilege": "Original fixed macro functions use native object/goal state internally; identical for every method, simulation-only. Never disclosed to the planner.",
                "probes": {
                    name: {
                        "native_commands": probe_commands(task, name),
                        "controls": 10,
                        "predicted_effect": "Real actuator/PD commands can change hand-object motion or release contact; actual object effect and information benefit are UNMEASURED",
                    }
                    for name in probes
                },
                "recovery_binding": {
                    "c": "scripts/dsre_paper_physics.py:action_for(world,'continue',j,post_probe_tcp)",
                    "r": "scripts/dsre_paper_physics.py:action_for(world,'recover',j,post_probe_tcp)",
                },
                "recovery_controls": 70,
                "max_probes": 2,
                "post_checkpoint_deadline_controls": 90,
                "padding": "Native zero-EE delta with last gripper command until the common90-control deadline; separately record macro-end and deadline native success",
                "STOP": "No further diagnostic/recovery attempt; native hold through deadline is measured and charged. Never impute its terminal outcome.",
                "reset_rule": "Fresh full-prefix reconstruction only BETWEEN evaluator/source episodes; never reset, restore, teleport or rewind within a probe/recovery history",
                "G_after_probe": "NOT_CALIBRATED_NOT_OBSERVED; no inherited DSRE calibration",
                "pilot": {
                    "independent_parent_slots": 10,
                    "complete_history_macro_paths": 14,
                    "complete_history_STOP_paths": 7,
                    "repeat_executions_per_path": 2,
                    "maximum_native_episodes": 420,
                    "wall_cap_worker_hours": 2,
                    "completed_parents": 0,
                    "replacement": "NONE; failures retained with exact stage and missing labels",
                },
                "new_physics_authorized": False,
            }
        )
    record = {
        "static_interface_check_passed": True,
        "source_sha256": hashes,
        "versions": {
            p: importlib.metadata.version(p)
            for p in ("mani-skill", "sapien", "torch", "numpy", "pydantic")
        },
        "adapters": specs,
        "insertion_prefix_dependency": False,
        "new_physics": 0,
        "historical_sensor_field_examples": sensor_examples,
        "historical_source_input_sha256": dict(INPUTS),
        "actual_qualification_pilots_completed": 0,
        "new_calibrated_predicates": 0,
        "full_physical_state_recoverability_table": "UNAVAILABLE_UNTIL_A_NEW_QUALIFIED_SOURCE_AND_INDEPENDENT_COHORT_EXIST",
        "source_feasibility": "STATIC_BINDINGS_PRESENT; DYNAMICS_OBSERVABILITY_AND_TASK_EFFECTS_UNVERIFIED",
    }
    (output / "source_and_adapters.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(
        json.dumps(
            {k: v for k, v in record.items() if k not in {"source_sha256", "adapters"}}
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
