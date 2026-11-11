"""Scientific boundary regressions for the unattended conditional gate."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.overnight_pick import (
    PickFrame,
    PickSensors,
    event_trigger,
    passive_features,
    pick_recovery,
    select_severity,
)


def frame(step, z=0.02, grasp=False):
    return PickFrame(
        step=step,
        action=[0, 0, 0, -1],
        sensors=PickSensors(
            task_state={
                "agent": {"qpos": [[0] * 9], "qvel": [[0] * 9]},
                "extra": {
                    "is_grasped": [grasp],
                    "tcp_pose": [[0, 0, 0.15, 1, 0, 0, 0]],
                    "goal_pos": [[0.05, 0, 0.2]],
                    "obj_pose": [[0, 0, z, 1, 0, 0, 0]],
                    "tcp_to_obj_pos": [[0, 0, z - 0.15]],
                    "obj_to_goal_pos": [[0.05, 0, 0.2 - z]],
                },
            },
            object_velocity=[0] * 6,
            drive_targets=[0] * 9,
            drive_velocities=[0] * 9,
            applied_qf=[0] * 9,
            link_wrenches=[[0] * 6 for _ in range(15)],
            robot_contact=True,
            time=step / 20,
        ),
    )


def test_event_trigger_uses_past_executed_lift_and_drop():
    history = [frame(i) for i in range(71)]
    assert event_trigger(history, 0.02) == "missed_lift"
    assert event_trigger(history[:69], 0.02) is None
    lifted = [frame(i, 0.12, True) for i in range(70)] + [frame(70, 0.04, False)]
    assert event_trigger(lifted, 0.02) == "drop"
    assert event_trigger([frame(i, 0.12, True) for i in range(71)], 0.02) is None


def test_sensor_schema_rejects_oracle_and_padding_never_reads_future():
    history = [frame(i) for i in range(71)]
    for regime in ["full", "realistic"]:
        values = passive_features(history, regime)
        assert np.isfinite(values).all()
    altered = history[0].model_dump()
    altered["sensors"]["fault"] = 1
    with pytest.raises(ValidationError):
        PickFrame.model_validate(altered)
    with pytest.raises(ValueError):
        passive_features(history + [frame(91)], "full")
    a = passive_features(history, "realistic")
    history[-1].sensors.task_state.extra.obj_pose[0][0] = 0.50
    # The camera has a fixed delay; direct exact object pose is not leaked.
    np.testing.assert_array_equal(a, passive_features(history, "realistic"))
    assert not np.array_equal(
        passive_features(history, "full"),
        passive_features([frame(i) for i in range(71)], "full"),
    )


def test_severity_choice_is_incidence_only_and_preserves_finite_grid():
    config = json.loads(Path("config/overnight_20261111.json").read_text())["d7b"]
    rows = []
    for seed in config["calibration_seeds"]:
        rows.append(
            {
                "evaluation_only_fault": {"name": "nominal"},
                "seed": seed,
                "initial_success": True,
                "failed": False,
            }
        )
        for mechanism, values in [
            ("friction", config["friction_grid"]),
            ("offset", config["offset_grid_m"]),
        ]:
            for index, value in enumerate(values):
                rows.append(
                    {
                        "evaluation_only_fault": {"name": f"{mechanism}-{value}"},
                        "seed": seed,
                        "initial_success": False,
                        "failed": index >= 1,
                        "unread_recovery_score": 999,
                    }
                )
    result = select_severity(rows, config)
    assert (
        result["status"] == "SELECTED"
        and result["friction"] == 0.03
        and result["offset_x"] == 0.02
    )
    changed = copy.deepcopy(rows)
    for row in changed:
        row["unread_recovery_score"] = -999
    assert select_severity(changed, config) == result
    for row in rows:
        if row["evaluation_only_fault"]["name"].startswith("friction"):
            row["failed"] = False
    assert select_severity(rows, config)["status"] == "NO-GO"


def test_recovery_actions_are_sensor_only_and_budget_bounded():
    for mode in ["nominal", "regrasp", "conservative"]:
        actions = np.asarray(
            [
                pick_recovery(frame(70), mode, i, np.array([0, 0, 0.15]))
                for i in range(70)
            ]
        )
        assert actions.shape == (70, 4) and np.isfinite(actions).all()
        assert np.abs(actions[:, :3]).max() <= 0.25
        if mode == "conservative":
            assert np.abs(actions[:, :3]).max() <= 0.08


def test_replay_audit_retains_failed_test_branches_and_rejects_invalid_gold():
    from dual_rec.replay_audit import summarize_replay

    error = {
        "position": 0.0,
        "angle": 0.0,
        "qpos": 0.0,
        "velocity": 0.0,
        "observation": 0.0,
        "time": 0.0,
        "contacts": True,
        "success": True,
    }
    rows = []
    for seed in range(3):
        for policy in ["nominal", "alternative"]:
            gold = 0.8 if policy == "nominal" else 0.2
            test = 0.1 if policy == "nominal" else 0.9
            rows.append(
                {
                    "task": "fixture",
                    "seed": seed,
                    "condition": "nominal",
                    "stage": "contact",
                    "policy": policy,
                    "stage_reached": True,
                    "gold_prefix": {"passed": True},
                    "gold_continuation": {"passed": True},
                    "gold": {"success": True, "utility": gold},
                    "test": {"success": False, "utility": test},
                    "test_immediate_error": error,
                    "test_continuation": {
                        "passed": False,
                        "contact_agreement": 0.0,
                        "maxima": {
                            k: error[k]
                            for k in [
                                "position",
                                "angle",
                                "qpos",
                                "velocity",
                                "observation",
                                "time",
                            ]
                        },
                    },
                }
            )
    summary = summarize_replay(rows, 20)
    cell = summary["groups"]["fixture/nominal/contact"]
    assert summary["stage_reached_rows"] == 6 and summary["success_disagreements"] == 6
    assert cell["ranking_reversal_001"]["mean"] == 1
    divergence_only = copy.deepcopy(rows)
    for row in divergence_only:
        row["test"] = copy.deepcopy(row["gold"])
    negative = summarize_replay(divergence_only, 20)
    assert negative["snapshot_continuation_parity_passes"] == 0
    assert negative["success_disagreements"] == 0
    assert (
        negative["groups"]["fixture/nominal/contact"]["ranking_reversal_001"]["mean"]
        == 0
    )
    rows[0]["test"] = None
    summary = summarize_replay(rows, 20)
    assert (
        summary["stage_reached_rows"] == 6
        and summary["complete_pairs"] == 5
        and summary["test_restore_failures"] == 1
    )
    rows[1]["gold_continuation"]["passed"] = False
    with pytest.raises(ValueError):
        summarize_replay(rows, 20)


def test_pick_material_scope_changes_both_grasp_surfaces_without_density_edit():
    from types import SimpleNamespace as NS

    import sapien
    from sapien.physx import PhysxCpuSystem, PhysxRigidDynamicComponent

    from dual_rec.overnight_pick import PickFault, apply_pick_fault

    scene = sapien.Scene([PhysxCpuSystem()])
    actors = []
    for index in range(3):
        b = scene.create_actor_builder()
        b.add_box_collision(half_size=[0.02] * 3)
        actors.append(b.build(f"body-{index}"))
    bodies = [a.find_component_by_type(PhysxRigidDynamicComponent) for a in actors]
    env = NS(
        cube=NS(_objs=[actors[0]]),
        agent=NS(
            robot=NS(
                links=[
                    NS(name=f"finger-{i}", _objs=[body])
                    for i, body in enumerate(bodies[1:])
                ]
            )
        ),
    )
    result = apply_pick_fault(env, PickFault(name="lubricated", friction=0.01))
    assert result["cube_before"]["mass_kg"] == result["cube_after"]["mass_kg"]
    assert (
        result["cube_before"]["inertia_kg_m2"] == result["cube_after"]["inertia_kg_m2"]
    )
    assert all(x["dynamic"] == pytest.approx(0.01) for x in result["finger_after"])
    assert result["cube_after"]["shape_materials"][0][
        "dynamic_friction"
    ] == pytest.approx(0.01)


def test_preregistered_splits_and_branch_budget_are_disjoint():
    cfg = json.loads(Path("config/overnight_20261111.json").read_text())
    cohorts = [
        set(cfg["d7b"]["development_seeds"]),
        set(cfg["d7b"]["qualification_seeds"]),
        set(range(5100, 5124)),
        set(range(6100, 6116)),
        *[set(seeds) for seeds in cfg["b"]["seed_ranges"].values()],
    ]
    assert sum(map(len, cohorts)) == len(set.union(*cohorts))
    planned = (
        sum(
            len(cfg["b"]["seed_ranges"][t]) * len(c)
            for t, c in cfg["b"]["conditions"].items()
        )
        * 3
        * 2
        * 3
    )
    assert planned == cfg["b"]["planned_physical_continuations"] == 882
    assert planned < cfg["b"]["physical_continuation_cap"]


def test_overnight_supervisor_kills_timed_out_worker_and_seals_finalization(tmp_path):
    import subprocess
    import time

    (tmp_path / "initial.json").write_text(json.dumps({"started_epoch": time.time()}))
    command = [sys.executable, "scripts/overnight_command.py", "--root", str(tmp_path)]
    timed = subprocess.run(
        command
        + [
            "--name",
            "timeout",
            "--stage",
            "TEST",
            "--timeout",
            "11",
            "--",
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert timed.returncode == 124, timed.stdout + timed.stderr
    rows = [
        json.loads(line)
        for line in (tmp_path / "commands.jsonl").read_text().splitlines()
    ]
    assert rows[0]["termination_reason"] == "wall_or_stage_timeout"
    assert json.loads((tmp_path / "STATUS.json").read_text())["running"] is False
    done = subprocess.run(
        command
        + [
            "--name",
            "finish",
            "--stage",
            "FINAL",
            "--finalize",
            "--",
            sys.executable,
            "-c",
            "print('finished')",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    status = json.loads((tmp_path / "STATUS.json").read_text())
    assert status["STOPPED_WITHIN_AUTHORIZED_BOUNDARY"] and not status["running"]
    manifest = json.loads((tmp_path / "completion_manifest.json").read_text())
    assert (
        "timeout.log" in manifest["artifacts"] and "finish.log" in manifest["artifacts"]
    )
    rows = [
        json.loads(line)
        for line in (tmp_path / "commands.jsonl").read_text().splitlines()
    ]
    assert status["total_cpu_seconds"] == sum(r["cpu_seconds"] for r in rows)
