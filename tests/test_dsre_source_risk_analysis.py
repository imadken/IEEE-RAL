"""Registered recovery populations, STOP credit and parent-clustered inference."""

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def row(c, r, initial):
    return {
        "outcomes": {"continue_value": c, "recover_value": r},
        "initial_success": initial,
        "features": [True] * 6,
        "optional_features": [True] * 6,
    }


def test_stop_has_no_completion_credit_or_conditional_success():
    from dsre_source_risk_analysis import interval, metrics

    counts = metrics(row(True, True, True), None)
    assert counts["adequate"] == counts["inadequate"] == counts["acted"] == 0
    assert counts["stop"] == 1
    estimate = interval([0, 0], [0, 0], np.eye(2))
    assert estimate["estimate"] is estimate["lower"] is estimate["upper"] is None


def test_required_recovery_excludes_initially_successful_prevention_and_maintenance():
    from dsre_source_risk_analysis import metrics

    required = metrics(row(False, True, False), "recover")
    preventive = metrics(row(False, True, True), "recover")
    maintenance = metrics(row(True, True, True), "recover")
    assert required["required_selected"] == required["matched_recovery_gain"] == 1
    assert (
        preventive["required_selected"] == 0
        and preventive["recover_only_selected"] == 1
    )
    assert maintenance["required_selected"] == maintenance["matched_recovery_gain"] == 0
    assert (
        maintenance["both_success_maintained"]
        == maintenance["initial_success_maintained"]
        == 1
    )


def test_harm_and_confident_errors_remain_visible():
    from dsre_source_risk_analysis import metrics

    harm = metrics(
        row(True, False, True), "recover", [{"feature": "goal_near_03", "value": False}]
    )
    assert (
        harm["harmful_recover"] == harm["inadequate"] == harm["false_assertions"] == 1
    )
    assert harm["matched_recovery_gain"] == -1
    unknown = metrics(row(False, False, False), None)
    assert unknown["neither_deferred"] == 1 and unknown["adequate"] == 0


def test_five_conditions_stay_in_two_parent_clusters():
    from dsre_source_risk_analysis import bootstrap_indices, metrics, summarize

    records = []
    for parent, action in (("parent1", "continue"), ("parent2", None)):
        for condition in range(5):
            records.append(
                {
                    "group": parent,
                    "scenario": "clean",
                    "mode": "gated",
                    "method": "m",
                    "condition": str(condition),
                    "counts": metrics(row(True, False, True), action),
                }
            )
    tables, _ = summarize(records)
    result = tables["clean|gated|m|ALL"]
    assert result["parents"] == 2 and result["counts"]["rows"] == 10
    assert result["intervals"]["coverage"]["estimate"] == 0.5
    assert bootstrap_indices(2).shape == (4000, 2)


def test_hindsight_gap_keeps_neither_outcomes_and_is_not_a_risk_gate():
    from dsre_source_risk_analysis import hindsight

    rows = [row(True, False, False), row(False, True, False), row(False, False, False)]
    profile = hindsight(rows, 7)
    assert profile["action_mass"] == 2 and profile["common_action_signature_mass"] == 0
    assert "not calibrated" in profile["scope"]
