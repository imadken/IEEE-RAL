"""First alarms, conservative populations and exact causal Sign-CPD paths."""

from pathlib import Path

import numpy as np
import pytest

from dual_rec.failtime.baseline_cp import prefix_pelt_paths, upstream_functions
from dual_rec.failtime.metrics import (
    calibrate,
    first_alarm,
    outcome,
    persistent_capacity,
)


@pytest.mark.parametrize(
    "scores", [[1, 1, 1], [np.nan, np.nan, np.nan], [0.5, np.nan, 0.5], [0.2, 0.8, 0.8]]
)
def test_capacity_matches_direct_alarm(scores):
    t = np.arange(3) / 10
    s = np.asarray(scores)
    for theta in (0, 0.5, 1, np.nextafter(1, np.inf)):
        assert (first_alarm(t, s, theta) is not None) == (
            theta <= persistent_capacity(t, s)
        )


def test_full_history_boundary_crossing_and_inclusive_end():
    row = {
        "sample": "x",
        "robot": "r",
        "task_id": "t",
        "verdict": "fail",
        "onset": 0.1,
        "duration": 2.0,
    }
    result = outcome(row, np.array([0, 0.1, 1.1]), np.ones(3), 1)
    assert result["alarm_time"] == 0.1 and result["timely"]
    row["onset"] = 0
    assert outcome(row, np.array([0, 1]), np.ones(2), 1)["timely"]
    assert outcome(row, np.array([0, 0.1, 1]), np.ones(3), 1)["timely"]


def test_separate_populations_saturation_and_invalid_prefix():
    stream = lambda key, value: {
        "sample": key,
        "time": np.array([0, 0.1]),
        "scores": np.array([value, value]),
    }
    result = calibrate(
        [stream("s", 0.2)], [stream("p", 1.0), stream("empty", np.nan)], 0.1
    )
    assert result["threshold"] > 1 and result["fits"]["prefix"]["valid"] == 1
    assert result["fits"]["prefix"]["invalid"] == 1
    assert (
        calibrate([stream("s", 0.2)], [stream("empty", np.nan)], 0.1)["threshold"]
        is None
    )


def test_incremental_pelt_equals_pinned_prefix_recomputation():
    path = "results/failtime-online/20261112T101800Z/upstream"
    if not (Path(path) / "protracer/changepoint.py").exists():
        pytest.skip("Pinned upstream qualification source is local evidence")
    source = upstream_functions(path)
    symbols = np.random.default_rng(3).integers(-1, 2, (70, 4))
    cost = source["ModalHammingCost"](symbols)
    for n, cuts in enumerate(prefix_pelt_paths(symbols, cost, source, 2), start=1):
        assert cuts == source["pelt"](cost, n, 2.0, min_size=2)
