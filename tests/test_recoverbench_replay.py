"""Validate source array alignment and reject invalid executable controls."""

import sys
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.recoverbench.replay import SourceCase, validate_arrays
from dual_rec.recoverbench.transfer_audit import AuditPair


def test_pre_action_and_human_state_alignment_are_distinct():
    actions = np.zeros((3, 7))
    assert validate_arrays(actions, np.zeros((3, 45))) == "T_pre_action"
    assert validate_arrays(actions, np.zeros((4, 45))) == "T_plus_one"


@pytest.mark.parametrize("shape", [(0, 7), (3, 6), (3, 8), (7,)])
def test_action_space_is_not_silently_substituted(shape):
    with pytest.raises(ValueError, match="OSC"):
        validate_arrays(np.zeros(shape), np.zeros((4, 45)))


def test_nonfinite_control_and_ambiguous_state_alignment_are_rejected():
    actions = np.zeros((3, 7))
    with pytest.raises(ValueError, match="alignment"):
        validate_arrays(actions, np.zeros((5, 45)))
    actions[0, 1] = np.nan
    with pytest.raises(ValueError, match="Nonfinite"):
        validate_arrays(actions, np.zeros((3, 45)))


def test_missing_optional_metadata_is_not_a_runtime_success_label():
    case = SourceCase(
        archive_member="example.npz",
        task_name="stack",
        scene_id="source",
        error_name="drop_in_transit",
        degree="D0",
        success=True,
    )
    assert "success" not in case.model_dump()


@pytest.mark.parametrize(
    "member",
    ["/tmp/outside.npz", "../outside.npz", "a/../../outside.npz", "C:\\outside.npz"],
)
def test_archived_case_cannot_escape_local_data_root(member):
    with pytest.raises(ValidationError, match="relative NPZ"):
        SourceCase(
            archive_member=member,
            task_name="stack",
            scene_id="source",
            error_name="drop_in_transit",
            degree="D0",
        )


def test_target_pair_rejects_hidden_outcome_and_nonlocal_scene():
    fields = {
        "target_task": "stack",
        "target_scene": "target",
        "target_error": "drop_in_transit",
        "target_degree": "D0",
        "target_source_group": "parent",
        "source_member": "source.npz",
        "source_scene": "source",
        "source_degree": "D0",
    }
    with pytest.raises(ValidationError, match="Extra inputs"):
        AuditPair(**fields, future_success=True)
    with pytest.raises(ValidationError, match="local basename"):
        AuditPair(**(fields | {"target_scene": "../outside"}))
