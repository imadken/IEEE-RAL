"""The six-claim family, two distinct obligations and refusal invariants."""

import math

import pytest

from dual_rec.dsre.dual_obligation import CLAIMS, DELTA, annotated_action, calibrate


def rows(n, c=False, r=False):
    return [
        {
            "seed": seed,
            "condition": str(i),
            "c": c,
            "r": r,
            "proposals": {"DSRE_risk": "recover", "CART2_beta10": "recover"},
        }
        for seed in range(n)
        for i in range(5)
    ]


def test_exact_fixed_six_claim_family_and_zero_error_support():
    assert len(CLAIMS) == len(set(CLAIMS)) == 6
    assert DELTA == 0.05 / 6
    assert math.ceil(math.log(DELTA) / math.log(0.9)) == 46


def test_futile_recovery_can_only_qualify_for_nondegradation():
    bounds = calibrate(rows(256), tuple(range(256)))
    assert bounds["DSRE_risk|recover|absolute"]["error_parents"] == 256
    assert bounds["DSRE_risk|recover|nondegradation"]["error_parents"] == 0
    assert (
        annotated_action("recover", "DSRE_risk", "absolute", bounds)["action"] is None
    )
    decision = annotated_action("recover", "DSRE_risk", "nondegradation", bounds)
    assert (
        decision["action"] == "recover"
        and decision["annotation"] == "TASK_NONDEGRADATION_QUALIFIED_ONLY"
    )
    assert decision["task_adequacy_status_unchanged"]


def test_harm_disables_both_obligations_and_does_not_reroute():
    bounds = calibrate(rows(256, c=True), tuple(range(256)))
    assert not bounds["DSRE_risk|recover|nondegradation"]["qualified"]
    assert (
        annotated_action("recover", "DSRE_risk", "nondegradation", bounds)["action"]
        is None
    )


@pytest.mark.parametrize("count", [0, 45, 46, 255])
def test_missing_full_calibration_never_qualifies_even_with_zero_errors(count):
    bounds = calibrate(rows(count, r=True), tuple(range(256)))
    assert not any(b["qualified"] for b in bounds.values())


def test_correlated_conditions_count_one_error_parent():
    data = rows(256, r=True)
    for row in data[:5]:
        row["r"] = False
    bound = calibrate(data, tuple(range(256)))["DSRE_risk|recover|absolute"]
    assert bound["assigned_parents"] == 256 and bound["error_parents"] == 1
