"""Packet isolation and incremental frozen-model parity without optimization."""

import hashlib
import json
import runpy

import numpy as np
import pytest
import torch
from pydantic import ValidationError

from dual_rec.failtime.models import GRU32, causal_features, predict_gru, score_nominal

SCRIPT = runpy.run_path("scripts/failtime_streaming.py")
Packet = SCRIPT["RuntimePacket"]
Monitor = SCRIPT["StreamingAlarm"]


def fit():
    torch.manual_seed(11)
    return {
        "channels": 32,
        "state_dict": GRU32(32).state_dict(),
        "scaler": {"mean": np.zeros(32), "std": np.ones(32)},
    }


def test_packet_boundary_excludes_oracle_and_provenance_fields():
    for field in ("onset", "verdict", "sample", "episode", "reason", "duration"):
        with pytest.raises(ValidationError):
            Packet(time=0, eef=[0.0] * 16, robot="r", **{field: 1})
    with pytest.raises(ValidationError):
        Packet(time=0, eef=[np.nan] * 16, robot="r")
    with pytest.raises(ValidationError):
        Packet(time=0, eef=[0.0] * 15, robot="r")


def test_recurrent_packet_stream_matches_batch_and_latches_only_once():
    checkpoint = fit()
    t = np.arange(8) / 10
    x = np.zeros((8, 16))
    x[:, 0] = t * 0.1
    expected = predict_gru(checkpoint, causal_features(t, x))
    detector = Monitor("B4", [checkpoint], 0.0)
    traces = [
        detector.update(Packet(time=float(now), eef=row.tolist(), robot="r"))
        for now, row in zip(t, x, strict=True)
    ]
    np.testing.assert_allclose([r["risk"] for r in traces], expected, atol=1e-7)
    assert [r["time"] for r in traces if r["first_alarm"]] == [0.1]
    assert all(r["alarm_latched"] for r in traces[1:])
    assert len(detector.hidden) == 1 and detector.hidden[0].shape == (1, 1, 32)


def test_runtime_rejects_time_reversal_or_robot_change():
    detector = Monitor("B4", [fit()], 0.5)
    detector.update(Packet(time=0, eef=[0.0] * 16, robot="r"))
    with pytest.raises(ValueError, match="strictly increase"):
        detector.update(Packet(time=0, eef=[0.0] * 16, robot="r"))
    with pytest.raises(ValueError, match="stratum"):
        detector.update(Packet(time=0.1, eef=[0.0] * 16, robot="other"))


def test_unavailable_calibration_abstains_without_alarming():
    detector = Monitor("B4", [fit()], None)
    traces = [
        detector.update(Packet(time=i / 10, eef=[0.0] * 16, robot="r"))
        for i in range(4)
    ]
    assert all(r["abstention"] and not r["first_alarm"] for r in traces)


def test_incremental_mode_evidence_and_cusum_match_batch():
    distribution = {"mean": np.zeros(16), "std": np.ones(16), "drift": 1.0}
    checkpoint = {
        "robots": {
            "r": {"motion_floor": np.zeros(2), "global": distribution, "modes": {}}
        }
    }
    t = np.arange(6) / 10
    x = np.zeros((6, 16))
    x[1:, 0] = 0.5
    expected, _, _ = score_nominal(checkpoint, "r", t, x)
    detector = Monitor("MCSFA", checkpoint, 0.1)
    traces = [
        detector.update(Packet(time=float(now), eef=row.tolist(), robot="r"))
        for now, row in zip(t, x, strict=True)
    ]
    np.testing.assert_array_equal([r["risk"] for r in traces], expected)
    assert traces[1]["explanation"]["global_backoff"]
    assert traces[1]["explanation"]["increment"] > 0


def test_hindsight_artifact_is_never_loadable_as_runtime_calibration(tmp_path):
    thresholds = tmp_path / "thresholds.json"
    thresholds.write_text(
        json.dumps([{"method": "B4", "alpha": 0.1, "scope": "hindsight_only"}])
    )
    (tmp_path / "models_source_seal.json").write_text(
        json.dumps(
            {
                "scope": "Frozen development models and matched calibration before held-out evaluation",
                "sha256": {
                    "thresholds.json": hashlib.sha256(
                        thresholds.read_bytes()
                    ).hexdigest()
                },
            }
        )
    )
    with pytest.raises(ValueError, match="Hindsight"):
        SCRIPT["load_runtime"](tmp_path, "B4")
