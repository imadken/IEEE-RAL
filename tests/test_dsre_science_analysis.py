"""Grouped denominators and unavailable uncertainty must retain their meaning."""

from pathlib import Path

import numpy as np


def test_empty_conditional_denominator_is_unavailable(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_science_analysis import ratio_interval

    result = ratio_interval([0, 0], [0, 0], np.array([[2, 0], [1, 1], [0, 2]]))
    assert result["estimate"] is None
    assert result["lower"] is None and result["upper"] is None
    assert result["bootstrap_defined_draws"] == 0


def test_conditions_do_not_become_independent_bootstrap_parents(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_science_analysis import aggregate

    rows = []
    for parent, adequate in (("a", 1), ("b", 0)):
        for condition in range(16):
            rows.append(
                {
                    "population": "test",
                    "task": "PickCube-v1",
                    "scenario": "clean",
                    "mode": "point_proposal",
                    "method": "fixed",
                    "condition": str(condition),
                    "group": parent,
                    "adequate": adequate,
                    "inadequate": 1 - adequate,
                    "stop": 0,
                    "required_total": 0,
                    "required_selected": 0,
                    "recover_only_selected": 0,
                    "harmful_recover": 0,
                    "correct_continue": adequate,
                    "maintenance": 0,
                    "neither_deferred": 0,
                    "literals": 0,
                    "false_assertions": 0,
                    "noninvariant_assertions": 0,
                }
            )
    tables, _ = aggregate(rows)
    result = tables["test|PickCube-v1|clean|point_proposal|fixed"]
    assert result["rows"] == 32 and result["parents"] == 2
    interval = result["intervals"]["adequacy"]
    assert interval["estimate"] == 0.5
    assert interval["lower"] == 0 and interval["upper"] == 1
    assert result["intervals"]["necessary_recovery_recall"]["estimate"] is None
