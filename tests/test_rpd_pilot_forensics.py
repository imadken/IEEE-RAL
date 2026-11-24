"""A native interrupted attempt must never become a failure label or disappear."""

import pytest
from pydantic import ValidationError
from rpd_pilot_closure import Counts, count_status
from rpd_pilot_source_review import point_evidence


def test_native_crash_accounting_preserves_unknown_and_unattempted():
    result = count_status(
        ["COMPLETE"] * 38
        + ["INTERRUPTED_MISSING_OUTCOME"]
        + ["UNATTEMPTED_SOURCE_GUARD"] * 501
    )
    assert result.registered == 540
    assert result.attempted == 39
    assert result.complete == 38
    assert result.interrupted_missing_outcome == 1
    assert result.unattempted == 501
    assert result.missing_terminal_labels == 502


def test_cost_and_complete_trace_do_not_impute_missing_terminal_label():
    result = count_status(["INTERRUPTED_MISSING_OUTCOME"])
    assert result.complete == 0 and result.missing_terminal_labels == 1
    assert result.attempted == 1 and result.unattempted == 0


def test_counter_conservation_rejects_raw_only_attempt_count():
    with pytest.raises(ValidationError):
        Counts(
            registered=540,
            attempted=38,
            complete=38,
            interrupted_missing_outcome=1,
            unattempted=501,
            missing_terminal_labels=502,
        )


@pytest.mark.parametrize(
    "points,active",
    [
        ([], False),
        ([{"separation": 0.02, "impulse": [0, 0, 0]}], False),
        ([{"separation": 0.001, "impulse": [0, 0.01, 0]}], True),
        ([{"separation": -0.000001, "impulse": [0, 0, 0]}], True),
    ],
)
def test_contact_manifold_proximity_is_not_active_contact(points, active):
    assert point_evidence(points) == active
