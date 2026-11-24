"""Paired binary endpoints and correlated-parent decomposition checks."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def test_four_classes_and_missing_labels():
    from dsre_dual_adjudication import outcome_class

    assert [
        outcome_class(c, r)
        for c, r in ((True, False), (False, True), (True, True), (False, False))
    ] == ["C_ONLY", "R_ONLY", "BOTH", "NEITHER"]
    with pytest.raises(ValueError):
        outcome_class(None, False)


def test_neither_is_failure_without_degradation_and_conditions_are_clustered():
    from dsre_dual_adjudication import summarize

    rows = [
        {
            "seed": seed,
            "condition": str(i),
            "initial_success": False,
            "c": False,
            "r": i == 0,
            "proposals": {"DSRE_risk": "recover"},
        }
        for seed in (1, 2)
        for i in range(5)
    ]
    result = summarize(rows, "DSRE_risk")
    assert result["assigned_parents"] == result["absolute_error_parents"] == 2
    assert result["harm_error_parents"] == 0
    assert result["classes"] == {"R_ONLY": 2, "NEITHER": 8}
    assert result["intervals"]["parent_failure_minus_harm"]["estimate"] == 1


def test_observation_ambiguity_and_physical_infeasibility_are_separate():
    from dsre_dual_adjudication import partition

    rows = [
        {"features": [False], "c": True, "r": False},
        {"features": [False], "c": False, "r": True},
        {"features": [True], "c": False, "r": False},
        {"features": [True], "c": True, "r": True},
    ]
    result = partition(rows, 1)
    assert result["physically_infeasible_rows"] == 1
    assert result["pure_observational_ambiguity_mass"] == 2
    assert result["feasible_rows_in_signatures_containing_infeasible_reference"] == 1
    assert result["common_action_signature_mass"] == 0


def test_adjudicator_does_not_import_the_selector():
    # Whole-suite collection can already import selectors; use a fresh interpreter.
    import os
    import subprocess
    import sys

    from dsre_dual_adjudication import assert_isolated

    env = dict(os.environ, PYTHONPATH="src:scripts:" + os.environ.get("PYTHONPATH", ""))
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from dsre_dual_adjudication import assert_isolated; assert_isolated()",
        ],
        env=env,
        check=True,
    )
    assert callable(assert_isolated)
