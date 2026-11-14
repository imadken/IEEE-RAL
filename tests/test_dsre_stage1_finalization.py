"""STOP accounting cannot invent hold outcomes or change frozen action choices."""

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def example(group, action, initial, continuing, recovering):
    return {
        "group": group,
        "action": action,
        "initial_success": initial,
        "truth": {"continue": continuing, "recover": recovering},
    }


def test_defer_state_is_not_a_measured_hold_outcome():
    from dsre_stage1_analysis import counts

    rows = [example("a", None, True, False, False)]
    result = counts(rows)
    assert result["success_at_defer"] == 1
    assert result["good"] == 0 and result["bad"] == 0 and result["stop"] == 1
    assert counts(rows, "fallback_continue")["bad"] == 1
    assert counts(rows, "fallback_recover")["bad"] == 1


def test_fixed_fallback_changes_only_stop_actions_and_recounts_parent_errors():
    from dsre_stage1_analysis import counts

    rows = [
        example("a", "continue", False, False, True),
        example("a", None, False, False, True),
        example("b", None, True, True, False),
    ]
    r = counts(rows, "fallback_recover")
    assert (r["good"], r["bad"], r["stop"]) == (1, 2, 0)
    assert r["parent_any_error"] == 2 and r["required_recovery"] == 1
    assert r["assignment_errors"]["continue"] == {
        "assigned_parents": 1,
        "error_parents": 1,
    }


def test_empty_subgroup_reports_zero_counts_without_inventing_trials():
    from dsre_stage1_analysis import counts, parent_interval

    assert counts([])["N"] == 0 and counts([])["parents"] == 0
    assert counts([])["status"] == "EMPTY_NO_TRIALS"
    assert parent_interval([], [], 4) == {
        "value": 0.0,
        "ci95": [0.0, 0.0],
        "parents": 0,
        "N": 0,
        "status": "EMPTY_NO_TRIALS",
    }


def test_parent_bootstrap_keeps_the_two_conditions_together():
    from dsre_stage1_analysis import parent_interval

    rows = [example(g, None, False, False, False) for g in ("a", "a", "b", "b")]
    v = parent_interval(rows, [1, 0, 0, 0], 7)
    rng = np.random.Generator(np.random.PCG64(7))
    manual = np.asarray([0.5, 0])[rng.integers(2, size=(4000, 2))].mean(axis=1)
    assert v["parents"] == 2 and v["N"] == 4 and v["value"] == 0.25
    assert v["ci95"] == np.percentile(manual, [2.5, 97.5]).tolist()


def test_neither_success_state_cannot_be_repaired_by_observation_refinement():
    from dsre_stage1_analysis import finite_ceiling

    reference = [
        {
            "features": [False],
            "optional_features": [False],
            "outcomes": {"continue_value": False, "recover_value": True},
        },
        {
            "features": [False],
            "optional_features": [True],
            "outcomes": {"continue_value": False, "recover_value": False},
        },
    ]
    assert finite_ceiling(reference, []) == 0
    assert finite_ceiling(reference, [0]) == 1


def test_reference_heading_distinguishes_body_prose_and_two_column_extraction():
    from dsre_stage1_audit import has_reference_heading

    assert not has_reference_heading(
        "The references, predicates and tree nodes are frozen."
    )
    assert not has_reference_heading(
        "References are finite evidence, not world knowledge."
    )
    assert has_reference_heading(
        "  R EFERENCES        A continued title in the other column\n[1] A citation"
    )
