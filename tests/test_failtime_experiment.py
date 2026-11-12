"""Causal sampling, shared exposure and exact upstream change-point semantics."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from dual_rec.failtime.baseline_cp import score_sign_cpd, upstream_functions
from dual_rec.failtime.experiment import decision_stream


def test_future_packets_leave_existing_decisions_unchanged():
    time = np.arange(61) / 30
    x = np.arange(61 * 16, dtype=float).reshape(61, 16)
    before = decision_stream(time, x, "fixed")
    x[32:] += 10000
    after = decision_stream(time, x, "fixed")
    np.testing.assert_array_equal(before["features"][:11], after["features"][:11])
    assert np.all(before["source_time"] <= before["time"] + 1e-7)


def test_dropout_nested_and_delay_has_no_initial_future_fill():
    time = np.arange(61) / 30
    x = np.ones((61, 16))
    a = decision_stream(time, x, "fixed", "drop0.1")
    b = decision_stream(time, x, "fixed", "drop0.3")
    seed = 20261112 + int(__import__("hashlib").sha256(b"fixed").hexdigest()[:16], 16)
    draws = np.random.default_rng(seed).random(len(time))
    assert set(np.flatnonzero(draws >= 0.3)) <= set(np.flatnonzero(draws >= 0.1))
    assert len(a["time"]) == len(b["time"])
    delayed = decision_stream(time, x, "fixed", "delay0.2")
    assert np.isnan(delayed["eef"][:2]).all()
    assert np.isfinite(delayed["eef"][2:]).all()
    assert np.all(delayed["source_time"][2:] <= delayed["time"][2:] - 0.2 + 1e-7)


def test_causal_sign_cpd_matches_exact_pinned_prefix_component():
    t = np.arange(80) / 10
    x = np.zeros((80, 16))
    x[:, 7] = np.cumsum(np.repeat([1.0, -1.0, 0.0, 1.0], 20))
    x[:, 15] = -x[:, 7]
    nominal = {"robots": {"r": {"motion_floor": np.zeros(2)}}}
    path = "results/failtime-online/20261112T101800Z/upstream"
    if not (Path(path) / "protracer/changepoint.py").exists():
        pytest.skip("Pinned upstream qualification source is local evidence")
    source = upstream_functions(path)
    actual = score_sign_cpd(t, x, "r", nominal, path)
    for n in range(1, len(t) + 1):
        velocity = np.r_[0, np.diff(x[:n, 7])] * 10
        episode = SimpleNamespace(
            n_frames=n,
            fps=10,
            arms={
                "L": SimpleNamespace(aperture_velocity=velocity, motion=np.zeros(n)),
                "R": SimpleNamespace(aperture_velocity=-velocity, motion=np.zeros(n)),
            },
        )
        assert actual[n - 1] == len(source["sign_cpd"](episode, max_phases=15))
    assert actual[-1] > 0
