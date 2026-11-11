"""Annotation validity is separate from runtime observations and temporal models."""

import numpy as np
import pytest

from dual_rec.reboot.audit import annotation_coverage_complete
from dual_rec.reboot.contracts import (
    PhaseEpisode,
    RuntimeObservation,
    causal_signals,
    event_integrity,
)


def annotation(**updates):
    values = {
        "episode_index": "00",
        "episode_type": "recovery",
        "duration_frames": 10,
        "fps": 30,
        "phase_boundaries": {f"tau_{i}": 2 * i for i in range(6)},
        "failure": {
            "originating_phase": 2,
            "failure_mode": "slip",
            "induced_at_frame": 3,
            "recovery_started_at_frame": 6,
        },
    }
    return PhaseEpisode.model_validate(values | updates)


def test_event_window_uses_only_actual_frames_without_clipping():
    result = event_integrity(annotation(), np.arange(10))
    assert result["event_frames_in_bounds"] and result["pre_recovery_frames"] == 3
    result = event_integrity(
        annotation(
            failure={
                "originating_phase": 2,
                "failure_mode": "slip",
                "t_f": 3,
                "t_r": 10,
            }
        ),
        np.arange(10),
    )
    assert (
        not result["event_frames_in_bounds"] and result["pre_recovery_frames"] is None
    )


def test_conflicting_event_aliases_and_noninteger_episode_ids_are_rejected():
    with pytest.raises(ValueError, match="Conflicting"):
        annotation(
            failure={
                "originating_phase": 2,
                "failure_mode": "slip",
                "t_f": 2,
                "induced_at_frame": 3,
                "t_r": 6,
            }
        )
    with pytest.raises(ValueError, match="Episode index"):
        annotation(episode_index=0.5)


def test_phase_disagreement_is_reported_without_relabeling():
    result = event_integrity(
        annotation(
            failure={"originating_phase": 5, "failure_mode": "slip", "t_f": 3, "t_r": 6}
        ),
        np.arange(10),
    )
    assert result["origin_phase_at_onset"] == 2
    assert result["origin_matches_half_open_phase"] is False
    assert result["event_frames_in_bounds"]


def test_causal_signals_are_prefix_invariant_and_lag_human_actions():
    qpos = np.arange(140, dtype=float).reshape(10, 14)
    actions = qpos + 0.5
    time = np.arange(10) / 30
    first = causal_signals(qpos, actions, time)
    altered_q, altered_a = qpos.copy(), actions.copy()
    altered_q[5:] += 1000
    altered_a[5:] -= 1000
    np.testing.assert_array_equal(
        first[:5], causal_signals(altered_q, altered_a, time)[:5]
    )
    np.testing.assert_array_equal(
        first[:5], causal_signals(qpos[:5], actions[:5], time[:5])
    )
    altered_a[4] += 1000
    np.testing.assert_array_equal(first[4], causal_signals(qpos, altered_a, time)[4])


@pytest.mark.parametrize(
    "forbidden",
    [
        "t_f",
        "recovery_started_at_frame",
        "true_phase",
        "failure_mode",
        "episode_outcome",
        "repository",
        "future_action",
    ],
)
def test_runtime_boundary_rejects_label_and_identity_leakage(forbidden):
    values = {
        "qpos": [0.0] * 14,
        "previously_issued_action": [0.0] * 14,
        "symmetry": "C2",
        "operation": "install",
        "clearance_mm": 0.09,
    }
    with pytest.raises(ValueError, match="Extra inputs"):
        RuntimeObservation.model_validate(values | {forbidden: 1})


def test_one_labeled_sample_never_qualifies_missing_object_annotations():
    sample = {
        "role": "sample_engineering_only",
        "object": "cylinder",
        "operation": "install",
        "phase_annotation_file": True,
        "annotation_entries": 60,
        "projected_episodes": 60,
        "annotation_parse_errors": [],
    }
    assert not annotation_coverage_complete([sample])
    complete = [
        sample | {"role": role, "object": obj, "operation": operation}
        for role in ("expert", "recovery")
        for obj in ("cylinder", "usb_c", "rj45")
        for operation in ("install", "remove")
    ]
    assert annotation_coverage_complete(complete)
    complete[0] = complete[0] | {"phase_annotation_file": False}
    assert not annotation_coverage_complete(complete)
