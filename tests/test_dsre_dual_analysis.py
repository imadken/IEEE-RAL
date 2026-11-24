"""Behavioral accounting and independent paired interval checks."""

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


@pytest.mark.parametrize(
    "c,r", [(False, False), (False, True), (True, False), (True, True)]
)
@pytest.mark.parametrize("initial", [False, True])
@pytest.mark.parametrize("action", [None, "continue", "recover"])
def test_physical_outcome_classes_and_independent_accounting(c, r, initial, action):
    from dsre_dual_analysis import metrics
    from dsre_dual_numerical import independently_count

    row = {"c": c, "r": r, "initial_success": initial}
    result = metrics(row, action)
    assert result == independently_count(row, action)
    assert result["harm_R"] == int(action == "recover" and c and not r)
    assert result["futile_R"] == int(action == "recover" and not c and not r)
    assert result["required_selected"] == int(
        action == "recover" and not initial and not c and r
    )
    assert result["preventive_R_only"] == int(
        action == "recover" and initial and not c and r
    )
    assert result["futile_recovery_controls"] == 70 * result["futile_R"]
    assert result["failure"] + result["success"] + result["stop"] == 1


@pytest.mark.parametrize("dens", [[1, 2, 1], [0, 0, 0]])
def test_negative_paired_effect_and_undefined_rate_have_independent_intervals(dens):
    from dsre_dual_analysis import bootstrap, bounds
    from dsre_dual_numerical import check_interval

    nums = [-1, 0, 1] if any(dens) else [0, 0, 0]
    result = bounds(nums, dens, bootstrap(3))
    sample = np.random.Generator(np.random.PCG64(2026111603)).integers(0, 3, (4000, 3))
    check_interval(nums, dens, sample, result)
    if any(dens):
        assert result["lower"] < 0 < result["upper"]
    else:
        assert result["estimate"] is result["lower"] is result["upper"] is None
