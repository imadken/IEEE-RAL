import math

import pytest

from dual_rec.dsre.calibration import (
    CalibrationObservation,
    FrozenRouter,
    calibrate,
    gate,
    upper_bound,
    zero_error_required,
)


def router():
    return FrozenRouter(
        sha256="a" * 64,
        training_parent_ids=("old/parent",),
        strata=(
            "PickCube-v1/continue",
            "PickCube-v1/recover",
            "PushCube-v1/continue",
            "PushCube-v1/recover",
        ),
    )


def observations(n, action="continue", task="PickCube-v1", errors=0):
    return tuple(
        CalibrationObservation(
            parent_id=f"new/{task}/{action}/{i}",
            router_sha256="a" * 64,
            task=task,
            assigned_action=action,
            violated=i < errors,
        )
        for i in range(n)
    )


def test_zero_error_formula_and_required_sample():
    assert zero_error_required() == 42
    assert zero_error_required(0.05) == 86
    for n in [1, 10, 42, 200]:
        assert upper_bound(0, n, 0.0125) == pytest.approx(1 - 0.0125 ** (1 / n))
    assert upper_bound(0, 41, 0.0125) > 0.1
    assert upper_bound(0, 42, 0.0125) <= 0.1


def test_empty_all_error_and_general_binomial_root():
    assert upper_bound(0, 0, 0.0125) == upper_bound(10, 10, 0.0125) == 1
    upper = upper_bound(1, 10, 0.05)
    independent_cdf = (1 - upper) ** 10 + 10 * upper * (1 - upper) ** 9
    assert independent_cdf == pytest.approx(0.05)
    assert upper_bound(2, 10, 0.05) > upper
    with pytest.raises(ValueError):
        upper_bound(2, 1, 0.05)


def test_rare_action_multiple_testing_and_task_specific_gate_no_reroute():
    r = router()
    result = calibrate(r, observations(42))
    assert sum(s.delta for s in result.strata) == pytest.approx(0.05)
    assert [s.enabled for s in result.strata] == [True, False, False, False]
    assert gate("PickCube-v1", "continue", r.sha256, result).action == "continue"
    assert gate("PickCube-v1", "recover", r.sha256, result).action is None
    assert gate("PushCube-v1", "continue", r.sha256, result).action is None
    assert (
        gate("PickCube-v1", "continue", r.sha256, None).reason
        == "CALIBRATION_INSUFFICIENT"
    )
    assert not any(s.enabled for s in calibrate(r, observations(42, errors=42)).strata)
    assert not any(s.enabled for s in calibrate(r, ()).strata)
    rare = calibrate(r, observations(42) + observations(1, action="recover"))
    assert rare.strata[1].assigned == 1 and not rare.strata[1].enabled


def test_independent_parent_and_frozen_router_contracts():
    r = router()
    one = observations(1)[0]
    with pytest.raises(ValueError):
        calibrate(r, (one, one))
    with pytest.raises(ValueError):
        calibrate(r, (one.model_copy(update={"parent_id": "old/parent"}),))
    with pytest.raises(ValueError):
        calibrate(r, (one.model_copy(update={"router_sha256": "b" * 64}),))
    with pytest.raises(ValueError):
        calibrate(r, (one.model_copy(update={"task": "unregistered"}),))
    with pytest.raises(ValueError):
        gate("PickCube-v1", "continue", "b" * 64, calibrate(r, ()))


def test_missing_outcome_never_disappears_and_abstention_is_not_success():
    r = router()
    values = observations(42)
    result = calibrate(
        r, values[:-1] + (values[-1].model_copy(update={"violated": None}),)
    )
    assert result.strata[0].assigned == 42
    assert result.strata[0].unknown_outcomes == 1
    assert not result.strata[0].enabled
    abstained = values[0].model_copy(update={"assigned_action": None, "violated": None})
    assert sum(s.assigned for s in calibrate(r, (abstained,)).strata) == 0
    assert gate("PickCube-v1", None, r.sha256, None).action is None
    assert math.isfinite(result.strata[0].upper)
