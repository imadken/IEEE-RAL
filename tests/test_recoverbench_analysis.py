"""Clustered uncertainty must not treat candidates as independent trials."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "recoverbench_analysis",
    Path(__file__).parents[1] / "scripts/recoverbench_analysis.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_clusters_preserve_within_parent_pairs():
    # Every parent has one zero and one one: cluster resampling preserves 0.5.
    assert MODULE.cluster_interval([0, 1, 0, 1], ["a", "a", "b", "b"]) == [0.5, 0.5]


def test_interval_validates_alignment_and_is_repeatable():
    with pytest.raises(ValueError):
        MODULE.cluster_interval([1], [])
    assert MODULE.cluster_interval([0, 1], ["a", "b"]) == MODULE.cluster_interval(
        [0, 1], ["a", "b"]
    )
