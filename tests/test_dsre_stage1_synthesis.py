"""Scientific synthesis keeps parent units and physical meanings intact."""

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def test_preventive_opportunity_is_not_a_failed_start_recovery():
    from dsre_stage1_synthesis import required

    r = {
        "initial_success": True,
        "outcomes": {"continue_value": False, "recover_value": True},
    }
    assert not required(r)
    assert required({**r, "initial_success": False})


def test_bibliographic_case_protection_preserves_punctuation():
    from dsre_stage1_synthesis_audit import normalize_bib_title

    assert normalize_bib_title(
        "{DISCRET}: Synthesizing Faithful Explanations"
    ) == normalize_bib_title("DISCRET: Synthesizing Faithful Explanations")
    assert normalize_bib_title("{AI}  with {ManiSkill3}") == "ai with maniskill3"


def test_information_refinement_does_not_repair_a_both_fail_state():
    from dsre_stage1_synthesis import mass

    rows = [
        {
            "features": [False, False],
            "optional_features": [],
            "outcomes": {"continue_value": True, "recover_value": False},
        },
        {
            "features": [False, True],
            "optional_features": [],
            "outcomes": {"continue_value": False, "recover_value": False},
        },
    ]
    assert mass(rows, 1) == 0
    assert mass(rows, 2) == 1


def test_all_conditions_travel_with_parent_in_ratio_uncertainty():
    from dsre_stage1_synthesis import interval

    rows = [{"group": g, "good": int(g == "a")} for g in ("a", "b") for _ in range(5)]
    answer = interval(rows, lambda r: r["good"], lambda r: 1)
    draws = np.random.default_rng(2026111504).integers(0, 2, (4000, 2))
    expected = np.array([1.0, 0.0])[draws].mean(1)
    assert answer["parents"] == 2
    assert answer["estimate"] == 0.5
    assert answer["ci95"] == np.quantile(expected, [0.025, 0.975]).tolist()
    empty = interval(rows, lambda r: 0, lambda r: 0)
    assert empty["estimate"] is None and empty["ci95"] == [None, None]
