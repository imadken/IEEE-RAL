import random
from itertools import pairwise

import pytest

from dual_rec.dsre.features import ObservationHistory, ObservedFrame, feature_values
from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence
from dual_rec.dsre.measurement_oracle import check_invariance
from dual_rec.dsre.repair_selection import optional_values


def history(x=0.0, hand=0.1):
    return ObservationHistory(
        first=ObservedFrame(
            time=0,
            object_position=(x, 0, 0),
            tcp_position=(hand, 0, 0.1),
            goal_position=(0, 0, 0),
            finger_positions=(0.01, 0.01),
        ),
        current=ObservedFrame(
            time=1,
            object_position=(x, 0, 0),
            tcp_position=(hand, 0, 0.1),
            goal_position=(0, 0, 0),
            finger_positions=(0.01, 0.01),
        ),
    )


def scope(rho, time=1, eligible=False):
    return MeasurementScope(
        coordinate_error_m=rho,
        decision_time=time,
        reference_scope_identity="test",
        source_regime="test",
        clean_risk_scope_eligible=eligible,
    )


def test_signed_operand_error_is_twice_coordinate_radius():
    e = bounded_evidence(history(x=-0.025), scope(0.005))
    f = e.facts[6]
    assert f.measured is True
    assert f.lower == pytest.approx(-0.035)
    assert f.upper == pytest.approx(-0.015)
    assert f.invariant is None
    assert f.reason == "OBSERVATION_INSTABILITY"


def test_missing_is_unknown_and_stale_has_no_motion_envelope():
    h = history()
    h = h.model_copy(
        update={"current": h.current.model_copy(update={"object_position": None})}
    )
    e = bounded_evidence(h, scope(0))
    assert e.facts[0].invariant is None
    assert e.facts[4].invariant is True
    stale = bounded_evidence(history(), scope(0, time=1.25, eligible=True))
    assert all(f.invariant is None for f in stale.facts)
    assert not stale.risk_qualification_covers_sensor_regime


def test_zero_radius_exact_and_nested_unknown_monotonicity():
    rng = random.Random(37)
    for _ in range(100):
        h = history(x=rng.uniform(-0.1, 0.1), hand=rng.uniform(-0.1, 0.1))
        values = []
        for rho in (0, 0.001, 0.005):
            e = bounded_evidence(h, scope(rho))
            values.append(tuple(f.invariant for f in e.facts))
            check_invariance(h, rho, e, draws=8)
        assert values[0] == feature_values(h) + optional_values(h)
        for small, large in pairwise(values):
            for a, b in zip(small, large):
                assert b is None or a == b


def test_exact_threshold_strictness():
    h = history(x=-0.02)
    assert bounded_evidence(h, scope(0)).facts[6].invariant is False
    h = history(x=0.03)
    assert bounded_evidence(h, scope(0)).facts[0].invariant is True


def test_risk_scope_does_not_transfer():
    h = history()
    assert bounded_evidence(
        h, scope(0, eligible=True)
    ).risk_qualification_covers_sensor_regime
    assert not bounded_evidence(
        h, scope(0.001, eligible=True)
    ).risk_qualification_covers_sensor_regime
    assert not bounded_evidence(h, scope(0)).risk_qualification_covers_sensor_regime


def test_future_input_rejected():
    with pytest.raises(ValueError, match="Future observation"):
        bounded_evidence(history(), scope(0, time=0.5))
