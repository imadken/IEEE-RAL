"""Independent audit distinguishes physical rollout from visualization and labels."""

import copy
import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "rescue_audit",
    Path(__file__).parents[1] / "scripts/recoverbench_qualification_audit.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def traces():
    states = np.array([[0.0, 0.1], [0.05, 0.2]])
    actions = np.zeros((2, 7))
    rows = [
        {
            "step": 1,
            "action": actions[0].tolist(),
            "before": {"state": states[0].tolist(), "success": True},
            "after": {"state": states[1].tolist(), "success": False},
        },
        {
            "step": 2,
            "action": actions[1].tolist(),
            "before": {"state": states[1].tolist(), "success": False},
            "after": {"state": [0.1, 0.3], "success": True},
        },
    ]
    return rows, actions, states


def test_initial_success_is_separate_from_first_counted_success():
    rows, actions, states = traces()
    result = MODULE.audit_trace(rows, actions, states)
    assert result["initial_success"]
    assert result["first_success_step"] == 2
    assert not result["mismatches"]
    rows[1]["after"]["success"] = False
    assert MODULE.audit_trace(rows, actions, states)["first_success_step"] is None


def test_state_by_state_playback_is_not_accepted_as_control_rollout():
    rows, actions, states = traces()
    altered = copy.deepcopy(rows)
    altered[1]["before"]["state"][1] += 0.5
    result = MODULE.audit_trace(altered, actions, states)
    assert "intermediate state reset at 2" in result["mismatches"]
    assert result["first_recorded_pre_state_divergence_after_actions"] == 1


def test_wrong_action_and_time_alignment_are_rejected():
    rows, actions, states = traces()
    rows[0]["action"][0] = 1.0
    rows[0]["after"]["state"][0] = 0.1
    result = MODULE.audit_trace(rows, actions, states)
    assert "control mismatch at 1" in result["mismatches"]
    assert "physics time at 1" in result["mismatches"]


def test_initial_roundoff_is_retained_below_frozen_divergence_tolerance():
    rows, actions, states = traces()
    rows[0]["before"]["state"][1] += 2.2e-16
    result = MODULE.audit_trace(rows, actions, states)
    assert result["initial_state_residual"] > 0
    assert not result["mismatches"]
