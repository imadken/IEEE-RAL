"""Exact first-alarm capacity, conservative populations and gradient contracts."""

import json
import runpy

import numpy as np
import pytest
import torch

from dual_rec.reboot.onset_analysis import deployment_threshold
from dual_rec.reboot.onset_specificity import (
    capacities,
    persistence_series,
    population_threshold,
)
from dual_rec.reboot.overnight_metrics import first_alarm
from dual_rec.reboot.overnight_models import failure_loss

BRUTE_STREAM = runpy.run_path("scripts/reboot_onset_audit.py")["brute_stream"]


@pytest.mark.parametrize(
    "times,scores",
    [
        ([0, 0.1, 0.2, 0.3], [1, 1, 1, 1]),
        ([0, 0.1, 0.2, 0.3], [np.nan, np.nan, np.nan, np.nan]),
        ([0, 0.03, 0.11, 0.4, 0.51], [0.2, 0.8, 0.8, 0.4, 0.4]),
        ([0, 0.1, 0.2, 0.3], [0.5, np.nan, 0.5, 0.5]),
        ([0, 0.1, 0.2, 0.3], [0.1, 0.5, 0.8, 0.8]),
        ([0, 0.1, 0.2, 0.3], [0, 0, 1, 1]),
    ],
)
def test_capacity_matches_direct_streaming_at_all_breakpoints(times, scores):
    times, scores = np.array(times), np.array(scores)
    r = persistence_series(times, scores)
    _, _, independent = BRUTE_STREAM(times, scores)
    np.testing.assert_array_equal(r, independent)
    values = np.unique(scores[np.isfinite(scores)])
    thresholds = np.unique(np.r_[values, np.nextafter(values, np.inf), 0.0, np.inf])
    for theta in thresholds:
        first = first_alarm(times, scores, theta)
        ends = times[r >= theta]
        assert first == (float(ends[0]) if len(ends) else None)


def test_boundary_crossing_streak_is_not_reset_at_onset():
    row = {"role": "recovery", "onset": 0.1, "recovery": 0.2, "frames": 30}
    data = {"time": np.array([0.0, 0.1, 0.2]), "horizon": np.array(0.3)}
    result, _ = capacities(row, data, np.array([0.8, 0.8, 0.2]))
    assert result["A"] == -np.inf and result["B"] == 0.8
    assert first_alarm(data["time"], np.array([0.8, 0.8, 0.2]), 0.8) == 0.1
    assert persistence_series(np.array([0.1]), np.array([0.8]))[0] == -np.inf


def test_tied_capacity_has_no_feasible_event_interval():
    row = {"role": "recovery", "onset": 0.2, "recovery": 0.4, "frames": 30}
    data = {"time": np.arange(5) / 10, "horizon": np.array(0.5)}
    result, _ = capacities(row, data, np.ones(5))
    assert result["A"] == result["B"] == 1
    for theta in (1.0, np.nextafter(1.0, np.inf)):
        assert not result["A"] < theta <= result["B"]


def test_population_calibration_retains_ties_and_invalid_prefixes():
    nominal = population_threshold([0.2] * 12, 0.1)
    prefixes = population_threshold([0.9] * 11 + [-np.inf], 0.1)
    theta = max(nominal["threshold"], prefixes["threshold"])
    assert theta > 0.9 and prefixes["count"] == 11 and prefixes["invalid"] == 1
    assert population_threshold([-np.inf], 0.1)["available"] is False
    assert population_threshold([1.0] * 11, 0.1)["threshold"] > 1


def test_pre_onset_negatives_have_gradients_and_post_recovery_is_masked():
    probabilities = torch.tensor([[0.6, 0.6, 0.6]], requires_grad=True)
    labels = torch.tensor([[0.0, 1.0, 0.0]])
    mask = torch.tensor([[1.0, 1.0, 0.0]])
    loss = failure_loss(probabilities, labels, mask, 1.0)
    loss.backward()
    assert probabilities.grad[0, 0] > 0
    assert probabilities.grad[0, 1] < 0
    assert probabilities.grad[0, 2] == 0


def test_future_values_never_change_existing_capacity():
    times = np.arange(10) / 10
    scores = np.arange(10) / 10
    result = persistence_series(times, scores)
    changed = scores.copy()
    changed[5:] = 1
    np.testing.assert_array_equal(result[:5], persistence_series(times, changed)[:5])


def test_invalid_timestamps_fail_instead_of_reordering():
    with pytest.raises(ValueError, match="increasing"):
        persistence_series(np.array([0.0, 0.1, 0.1]), np.ones(3))


def test_hindsight_artifact_cannot_supply_a_runtime_threshold(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    (tmp_path / "calibrations.json").write_text(
        json.dumps({"scope": "HINDSIGHT_ONLY_NOT_DEPLOYABLE"})
    )
    with pytest.raises(ValueError, match="hindsight"):
        deployment_threshold(tmp_path, 0, "Q", "P1", 0.1, "C1")
    with pytest.raises(ValueError, match="registered"):
        deployment_threshold(tmp_path, 0, "Q", "P1", 0.1, "oracle")
