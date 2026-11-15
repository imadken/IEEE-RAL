"""Admission must depend on each frozen policy and its own parent quota."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
from dsre_recovery_evidence import admit

from dual_rec.dsre.operational import METHODS


def decisions(**actions):
    return {m: {"action": actions.get(m)} for m in METHODS}


def test_admission_counts_parent_once_despite_two_assigned_conditions():
    proposals = [decisions(DSRE_risk="recover")] * 2
    counts = dict.fromkeys(METHODS, 0)
    assert admit(proposals, counts) == ["DSRE_risk"]
    assert counts["DSRE_risk"] == 0


def test_other_method_stopping_does_not_select_baseline_sample_size():
    proposals = [decisions(DSRE_risk="recover", CART2_beta10="recover")]
    counts = dict.fromkeys(METHODS, 0)
    counts["DSRE_risk"] = 112
    counts["CART2_beta10"] = 111
    assert admit(proposals, counts) == ["CART2_beta10"]


def test_neither_continue_nor_abstention_qualifies_recovery_parent():
    assert admit([decisions(DSRE_risk="continue")], dict.fromkeys(METHODS, 0)) == []


def test_independent_binomial_inversion_and_family_size():
    from dsre_recovery_audit import exact_upper

    from dual_rec.dsre.calibration import upper_bound

    for n, k in [(0, 0), (13, 0), (69, 0), (92, 1), (112, 2), (125, 3), (180, 1)]:
        assert abs(exact_upper(k, n) - upper_bound(k, n, 0.05 / 68)) < 1e-10
    assert exact_upper(0, 68) > 0.1
    assert exact_upper(0, 69) <= 0.1
    assert exact_upper(1, 91) > 0.1
    assert exact_upper(1, 92) <= 0.1
    assert exact_upper(2, 111) > 0.1
    assert exact_upper(2, 112) <= 0.1


def test_parent_bootstrap_keeps_correlated_condition_denominators():
    import numpy as np
    from dsre_recovery_analysis import ratio_interval

    groups = ["a", "a", "b", "b"]
    indices = np.array([[0, 0], [0, 1], [1, 1]])
    result = ratio_interval([1, 1, 0, 0], [1, 1, 1, 1], groups, indices)
    assert result["estimate"] == 0.5
    assert result["numerator"] == 2 and result["denominator"] == 4
    assert result["lower"] == 0.025 and result["upper"] == 0.975
    empty = ratio_interval([0] * 4, [0] * 4, groups, indices)
    assert empty["estimate"] is None


def test_entire_test_cohort_must_be_decided_before_any_outcome(tmp_path, monkeypatch):
    import json

    import dsre_recovery_test as cohort
    import pytest

    monkeypatch.setattr(cohort, "verify", lambda root: None)
    (tmp_path / "test_screen_progress").mkdir()
    seeds = list(range(12000000, 12000160))
    (tmp_path / "test_registration.json").write_text(json.dumps({"test_seeds": seeds}))
    for i, seed in enumerate(seeds):
        d = tmp_path / "test" / str(seed)
        d.mkdir(parents=True)
        (d / "decision.json").write_text("{}")
        (tmp_path / "test_screen_progress" / f"{i:04d}.json").write_text(
            json.dumps({"seed": seed, "status": "COMPLETE"})
        )
    first = tmp_path / "test" / str(seeds[0])
    (first / "execution_started.json").write_text("{}")
    with pytest.raises(AssertionError):
        cohort.seal(tmp_path)
    (first / "execution_started.json").unlink()
    cohort.seal(tmp_path)
    sealed = json.loads((tmp_path / "test_recommendation_seal.json").read_text())
    assert sealed["parents"] == 160 and len(sealed["decisions"]) == 160
    assert sealed["method_decisions"] == 5440


def test_successful_start_with_recover_only_future_is_prevention_not_required_recovery():
    from dsre_recovery_analysis import recovery_populations

    rows = [
        {
            "initial_success": True,
            "outcomes": {"continue_value": False, "recover_value": True},
        },
        {
            "initial_success": False,
            "outcomes": {"continue_value": False, "recover_value": True},
        },
        {
            "initial_success": False,
            "outcomes": {"continue_value": True, "recover_value": True},
        },
        {
            "initial_success": False,
            "outcomes": {"continue_value": False, "recover_value": False},
        },
    ]
    recover_only, required = recovery_populations(rows)
    assert recover_only == [1, 1, 0, 0]
    assert required == [0, 1, 0, 0]
