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
