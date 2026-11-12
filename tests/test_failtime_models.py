"""Causal feature, nominal coverage and fixed recurrent inference contracts."""

import numpy as np
import pytest
import torch

from dual_rec.failtime.models import (
    GRU32,
    causal_features,
    fit_nominal,
    observable_modes,
    predict_gru,
    prior_scores,
    score_nominal,
)


def observations(n=80, scale=1.0):
    time = np.arange(n, dtype=float) / 10
    eef = np.zeros((n, 16))
    eef[:, 0] = scale * time * 0.001
    eef[:, 8] = scale * time * 0.002
    eef[:, 7] = time * 0.01
    eef[:, 15] = time * 0.01
    return time, eef


def nominal():
    return fit_nominal(
        [
            {"robot": "r", "time": t, "eef": x}
            for t, x in (observations(scale=1.0), observations(scale=1.2))
        ]
    )


def test_causal_features_use_actual_backward_timestamps():
    t = np.array([0.0, 0.04, 0.14])
    eef = np.repeat((2 * t)[:, None], 16, axis=1)
    x = causal_features(t, eef)
    np.testing.assert_array_equal(x[0, 16:], np.zeros(16))
    np.testing.assert_allclose(x[1:, 16:], 2.0)
    changed = eef.copy()
    changed[2] += 100
    np.testing.assert_array_equal(causal_features(t, changed)[:2], x[:2])


def test_invalid_packets_do_not_contaminate_future_features():
    t, x = observations(5)
    x[1] = np.nan
    features = causal_features(t, x)
    assert np.isnan(features[1]).all()
    np.testing.assert_allclose(features[2, 16:], (x[2] - x[0]) / (t[2] - t[0]))


def test_nonincreasing_or_nonfinite_timestamps_rejected():
    with pytest.raises(ValueError, match="strictly increasing"):
        causal_features(np.array([0.0, 0.0]), np.zeros((2, 16)))
    with pytest.raises(ValueError, match="16 end-effector"):
        causal_features(np.array([0.0]), np.zeros((1, 15)))


def test_nominal_conditioning_requires_two_recordings_and_fifty_frames():
    t, x = observations()
    singleton = fit_nominal([{"robot": "r", "time": t, "eef": x}])
    assert not singleton["robots"]["r"]["modes"]
    trained = nominal()
    assert trained["robots"]["r"]["modes"]
    for fit in trained["robots"]["r"]["modes"].values():
        assert fit["frames"] >= 50 and fit["recordings"] >= 2


def test_unseen_mode_backs_off_and_missing_robot_abstains():
    trained = nominal()
    t, x = observations()
    x[:, 7] *= -1
    risk, mode, backoff = score_nominal(trained, "r", t, x)
    assert np.isfinite(risk).all()
    assert backoff[1:].all()
    risk, mode, backoff = score_nominal(trained, "unseen", t, x)
    assert np.isnan(risk).all() and np.all(mode == -1) and backoff.all()


def test_sequential_and_instantaneous_nominal_scores_are_prefix_invariant():
    trained = nominal()
    t, x = observations()
    for conditioned in (False, True):
        for accumulate in (False, True):
            all_risk, all_mode, all_backoff = score_nominal(
                trained, "r", t, x, conditioned=conditioned, accumulate=accumulate
            )
            risk, mode, backoff = score_nominal(
                trained,
                "r",
                t[:23],
                x[:23],
                conditioned=conditioned,
                accumulate=accumulate,
            )
            np.testing.assert_array_equal(risk, all_risk[:23])
            np.testing.assert_array_equal(mode, all_mode[:23])
            np.testing.assert_array_equal(backoff, all_backoff[:23])
    # The global ablation ignores the otherwise supported mode distributions.
    a = score_nominal(trained, "r", t, x, conditioned=False)[0]
    altered = {**trained, "robots": {"r": {**trained["robots"]["r"], "modes": {}}}}
    np.testing.assert_array_equal(
        a, score_nominal(altered, "r", t, x, conditioned=False)[0]
    )


def test_mode_ties_are_stationary_and_strict_motion_threshold():
    _, x = observations(2)
    floor = np.array([(x[1, 0] - x[0, 0]) ** 2, (x[1, 8] - x[0, 8]) ** 2])
    modes = observable_modes(x, floor)
    assert modes[0] == 14  # sign=0, stopped for both arms
    assert modes[1] == 28  # sign=+1, displacement equal to floor remains stopped
    _, x = observations(3)
    x[2, :3] += 1
    assert observable_modes(x, np.zeros(2))[2] != modes[1]


def test_gru_predictions_are_causal_without_any_optimization():
    torch.manual_seed(11)
    network = GRU32(32)
    fit = {
        "channels": 32,
        "state_dict": network.state_dict(),
        "scaler": {"mean": np.zeros(32), "std": np.ones(32)},
    }
    t, eef = observations(20)
    x = causal_features(t, eef)
    prediction = predict_gru(fit, x)
    changed = x.copy()
    changed[10:] += 2
    np.testing.assert_allclose(
        prediction[:10], predict_gru(fit, changed)[:10], atol=1e-7
    )
    np.testing.assert_allclose(prediction[:10], predict_gru(fit, x[:10]), atol=1e-7)


def test_runtime_functions_reject_oracle_arguments_and_prior_has_no_future_duration():
    trained = nominal()
    t, x = observations()
    with pytest.raises(TypeError):
        score_nominal(trained, "r", t, x, onset=1.0)
    early = prior_scores(t[:10], 0.4)
    full = prior_scores(t, 0.4)
    for key in early:
        np.testing.assert_array_equal(early[key], full[key][:10])
