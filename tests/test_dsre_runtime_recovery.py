"""Fail-closed native subprocess and physical-memory qualification guards."""

import copy
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def test_runtime_override_is_process_local_and_keeps_registered_source(monkeypatch):
    from dsre_runtime_recovery import configured_environment

    monkeypatch.delenv("VK_ICD_FILENAMES", raising=False)
    before = configured_environment()
    after = configured_environment(
        {"VK_ICD_FILENAMES": "/usr/share/vulkan/icd.d/lvp_icd.x86_64.json"}
    )
    assert {
        k for k in before.keys() | after.keys() if before.get(k) != after.get(k)
    } == {"VK_ICD_FILENAMES"}
    import os

    assert "VK_ICD_FILENAMES" not in os.environ
    assert after["CUDA_VISIBLE_DEVICES"] == "" and "reboot-phase" in after["PYTHONPATH"]


def test_unknown_runtime_override_and_unbounded_probe_rejected(tmp_path):
    from dsre_runtime_recovery import configured_environment, probe

    with pytest.raises(ValueError):
        configured_environment({"UNRELATED_SECRET": "value"})
    with pytest.raises(ValueError):
        probe(tmp_path, "invalid", ["python"], timeout=1000)


@pytest.mark.parametrize(
    "channel", ["rng_states", "torch", "controller_transient", "drive_targets"]
)
def test_controller_and_rng_drift_blocks_parity(channel):
    from dsre_runtime_parity import exact_memory_and_model

    keys = [
        "rng_states",
        "rng_aliases",
        "torch",
        "controller",
        "controller_transient",
        "drive_targets",
        "drive_velocities",
        "_episode_seed",
        "_main_seed",
        "_elapsed_steps",
    ]
    original = {
        "model": {"source": "fixed"},
        "canonical_controller_memory": {key: [1] for key in keys},
    }
    current = copy.deepcopy(original)
    exact_memory_and_model(original, current)
    current["canonical_controller_memory"][channel] = [2]
    with pytest.raises(AssertionError, match="memory drift"):
        exact_memory_and_model(original, current)


def test_missing_historical_channel_and_model_drift_block():
    from dsre_runtime_parity import exact_memory_and_model

    with pytest.raises(AssertionError, match="provenance"):
        exact_memory_and_model({"model": 1}, {"model": 2})
    with pytest.raises(AssertionError, match="channel absent"):
        exact_memory_and_model(
            {"model": 1, "canonical_controller_memory": {}},
            {"model": 1, "canonical_controller_memory": {}},
        )
