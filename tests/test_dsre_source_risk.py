"""Fixed cohort, per-action parent errors, and strict test-outcome sealing."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def assigned(c, r, outcomes):
    return {
        "cells": [
            {
                "proposals": {"m": a},
                "outcomes": {"continue_value": x, "recover_value": y},
            }
            for a, (x, y) in zip((c, r), outcomes, strict=True)
        ]
    }


def test_action_error_is_any_assigned_condition_once_per_parent():
    from dsre_source_risk_audit import stratum_bounds

    parents = [
        assigned("recover", "recover", [(True, True), (True, False)]),
        assigned("continue", "recover", [(True, False), (False, True)]),
    ]
    b = stratum_bounds(parents, ["m"], True)
    assert (b["m|recover"]["assigned_parents"], b["m|recover"]["error_parents"]) == (
        2,
        1,
    )
    assert (b["m|continue"]["assigned_parents"], b["m|continue"]["error_parents"]) == (
        1,
        0,
    )


def test_empty_and_incomplete_cohort_never_qualifies_even_zero_errors():
    from dsre_source_risk_audit import stratum_bounds

    assert not any(x["enabled"] for x in stratum_bounds([], ["m"], True).values())
    parents = [assigned("recover", "recover", [(False, True), (False, True)])] * 112
    assert stratum_bounds(parents, ["m"], True)["m|recover"]["enabled"]
    assert not stratum_bounds(parents, ["m"], False)["m|recover"]["enabled"]


def test_independent_exact_bound_and_unchanged_multiplicity():
    from dsre_source_risk_audit import exact_upper

    from dual_rec.dsre.calibration import upper_bound

    for n, k in (
        (0, 0),
        (13, 0),
        (68, 0),
        (69, 0),
        (92, 1),
        (112, 2),
        (256, 0),
        (256, 12),
        (5, 5),
    ):
        assert exact_upper(k, n) == pytest.approx(
            upper_bound(k, n, 0.05 / 68), abs=1e-11
        )
    assert exact_upper(0, 68) > 0.1 >= exact_upper(0, 69)


def test_failed_final_parent_does_not_mark_cohort_complete(tmp_path, monkeypatch):
    import json

    import dsre_source_risk as runner

    monkeypatch.setattr(runner, "verify", lambda root: None)
    (tmp_path / "study_plan.json").write_text(json.dumps({"calibration_seeds": [1, 2]}))
    (tmp_path / "progress").mkdir()
    for i, status in enumerate(("COMPLETE", "INCOMPLETE")):
        (tmp_path / "progress" / f"calibration-{i:04d}.json").write_text(
            json.dumps({"status": status})
        )
    runner.control(tmp_path, "calibration")
    assert not (tmp_path / "calibration_boundary.json").exists()


def test_partial_calibration_cannot_seal_a_gate(tmp_path, monkeypatch):
    import json

    import dsre_source_risk as runner

    monkeypatch.setattr(runner, "verify", lambda root: None)
    (tmp_path / "study_plan.json").write_text(
        json.dumps({"calibration_seeds": list(range(256))})
    )
    (tmp_path / "calibration_physics_audit.json").write_text(
        json.dumps({"passed": True, "parents": 255})
    )
    with pytest.raises(AssertionError):
        runner.seal_calibration(tmp_path)
    assert not (tmp_path / "calibration_decision.json").exists()


def test_all_test_recommendations_precede_every_test_outcome(tmp_path, monkeypatch):
    import json

    import dsre_source_risk as runner

    monkeypatch.setattr(runner, "verify", lambda root: None)
    (tmp_path / "study_plan.json").write_text(
        json.dumps({"test_seeds": list(range(128))})
    )
    cal = tmp_path / "calibration_decision.json"
    cal.write_text(json.dumps({"complete_cohort": True, "calibration_parents": 256}))
    digest = runner.sha(cal)
    (tmp_path / "calibration_decision_audit.json").write_text(
        json.dumps({"passed": True, "calibration_sha256": digest})
    )
    for seed in range(128):
        d = tmp_path / "test" / str(seed)
        d.mkdir(parents=True)
        (d / "decision.json").write_text(json.dumps({"calibration_sha256": digest}))
    early = tmp_path / "test/0/nominal/continue.json.gz"
    early.parent.mkdir()
    early.write_text("preserved early outcome sentinel")
    with pytest.raises(AssertionError):
        runner.seal_test(tmp_path)
    early.unlink()
    runner.seal_test(tmp_path)
    assert (
        json.loads((tmp_path / "test_recommendation_seal.json").read_text())[
            "parent_count"
        ]
        == 128
    )
