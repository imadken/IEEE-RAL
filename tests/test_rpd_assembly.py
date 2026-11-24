"""Offline contract/mechanics tests; constructed arrays are not robot observations."""

import json
from unittest.mock import patch

import numpy as np
import pytest
import rpd_assembly_run as runner
from pydantic import ValidationError
from rpd_assembly_audit import compare_roots, independently_goal
from rpd_assembly_contract import (
    Job,
    candidates,
    fault,
    goal_components,
    pose_matrix,
    pose_raw,
    probe_target,
    recovery_segments,
    transform,
)
from scipy.spatial.transform import Rotation


def test_registered_source_ids_and_new_namespace_never_overlap():
    records = candidates()
    assert len(records) == 36
    assert sum(r.phase == "qual" for r in records) == 12
    assert len({r.native_geometry_seed for r in records}) == 36
    assert records[12].candidate_id == "RPD-assembly-prelim-v1/0"
    assert records[-1].candidate_id == "RPD-assembly-prelim-v1/23"


def test_monitor_serialization_preserves_numpy_truth_without_imputation():
    from rpd_assembly_worker import plain

    raw = {
        "pass": np.bool_(False),
        "value": np.float64(0.003),
        "array": np.array([1, 2]),
    }
    assert json.loads(json.dumps(plain(raw), allow_nan=False)) == {
        "pass": False,
        "value": 0.003,
        "array": [1, 2],
    }
    with pytest.raises(ValueError):
        json.dumps(plain({"unavailable": np.float64(np.nan)}), allow_nan=False)


def test_confirmation_cannot_be_smuggled_into_worker_contract():
    record = candidates()[0].model_dump()
    record["phase"] = "confirmation"
    with pytest.raises(ValidationError):
        Job(candidate=record, intervention="hold", action="a0")
    record = candidates()[12]
    with pytest.raises(ValidationError):
        Job(candidate=record, intervention="direct", action="a0")
    with pytest.raises(ValidationError):
        Job(candidate=record, intervention="hold", action="a0", repeat=1)


def test_probe_targets_preserve_clock_and_literal_dither_endpoint():
    root = transform([0.1, 0.2, 0.3])
    assert np.array_equal(probe_target(root, "dither", 10), root)
    assert np.array_equal(probe_target(root, "hold", 5), root)
    assert np.isclose(probe_target(root, "preload", 10)[0, 3] - root[0, 3], 0.0015)
    assert probe_target(root, "dither", 3)[1, 3] > root[1, 3]
    assert np.array_equal(root, transform([0.1, 0.2, 0.3]))


def test_two_nominal_policies_have_same_final_target_and_unequal_physical_paths():
    start = transform([-0.29, 0.003, 0], Rotation.from_euler("X", np.pi).as_matrix())
    a0, a1 = recovery_segments(start, 0.1, "a0"), recovery_segments(start, 0.1, "a1")
    assert sum(k for k, _ in a0) == 40
    assert sum(k for k, _ in a1) == 60
    assert np.array_equal(a0[-1][1], a1[-1][1])
    assert np.isclose(a1[0][1][0, 3], start[0, 3] - 0.012)


def test_fault_draw_is_fixed_and_geometry_scaled_without_resampling():
    record = candidates()[0]
    assert fault(record, 0.1) == fault(record, 0.1)
    assert fault(record, 0.1)["Z"] in (0, 1, 2)
    assert fault(record, 0.1)["theta_c"] == np.arctan(0.003 / 0.2)


def test_independent_goal_in_translated_rotated_hole_frame():
    hole = transform([0.05, 0.30, 0.15], Rotation.from_euler("Z", 0.4).as_matrix())
    peg = hole @ transform([-0.11, 0, 0])
    frame = {
        "hole": pose_raw(hole),
        "peg": pose_raw(peg),
        "peg_linear_velocity": [0, 0, 0],
        "peg_angular_velocity": [0, 0, 0],
    }
    assert independently_goal(frame, 0.1)
    assert all(goal_components(frame, 0.1).values())
    frame["peg_linear_velocity"] = [0.003001, 0, 0]
    assert not independently_goal(frame, 0.1)
    assert not all(goal_components(frame, 0.1).values())


def test_frame_round_trip_and_quaternion_sign_do_not_create_replay_failure():
    p = pose_raw(
        transform(
            [0.1, 0.2, 0.3], Rotation.from_euler("XYZ", [0.1, 0.2, 0.3]).as_matrix()
        )
    )
    q = p[:3] + [-x for x in p[3:]]
    a = {
        "frame": {k: p for k in ("peg", "fixture", "hole", "tcp")},
        "absolute_substep": 150,
    }
    b = {
        "frame": {k: q for k in ("peg", "fixture", "hole", "tcp")},
        "absolute_substep": 150,
    }
    assert compare_roots(a, b)["passed"]
    assert np.allclose(pose_matrix(p), pose_matrix(q))
    b["absolute_substep"] = 151
    assert not compare_roots(a, b)["passed"]


def test_replay_translation_tolerance_is_not_relaxed_by_success():
    p = pose_raw(np.eye(4))
    a = {"frame": {k: p for k in ("peg", "fixture", "hole", "tcp")}}
    b = json.loads(json.dumps(a))
    b["frame"]["peg"][0] += 2e-5
    assert not compare_roots(a, b)["passed"]


def test_fewer_than_eight_eligible_sources_cannot_open_exploration(tmp_path):
    records = [r.model_dump() for r in candidates() if r.phase == "qual"]
    packet = {
        "candidates": records,
        "physics_qualification_cap_seconds": 10800,
        "exploratory_cap_seconds": 10080,
    }
    tmp_path.joinpath("registration.json").write_text(json.dumps(packet))

    def source(job, deadline):
        assert job.intervention == "screen"
        return {"eligibility": {"disposition": "KNOWN_INELIGIBLE"}}, {"wall_seconds": 1}

    with (
        patch.object(runner, "BASE", tmp_path),
        patch.object(runner, "verify_registration", return_value=packet),
        patch.object(runner, "launch", side_effect=source),
    ):
        assert runner.execute("qual") == 2
        gate = json.loads((tmp_path / "qualification.json").read_text())
        assert not gate["passed"] and gate["screened"] == 12 and gate["eligible"] == 0
        with pytest.raises(AssertionError):
            runner.execute("exploratory")
