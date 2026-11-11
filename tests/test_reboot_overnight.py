"""Causality and reasoning properties, separate from scientific validation."""

import json

import numpy as np
import pytest
import torch

from dual_rec.reboot.overnight_data import SensorPacket, sensor_features, targets
from dual_rec.reboot.overnight_metrics import (
    calibrate,
    first_alarm,
    outcome,
    persistent_capacity,
)
from dual_rec.reboot.overnight_models import (
    SmallGRU,
    filter_step,
    phase_layers,
    phase_loss,
    phase_matrix,
    predict_neural,
    scale_fit,
    scaled,
    windows,
)


def arrays(n=90):
    q = np.arange(n * 14, dtype=float).reshape(n, 14) / 100
    return {"qpos": q, "actions": q + 1, "timestamp": np.arange(n) / 30}


def test_sensor_and_window_prefix_invariance():
    data = arrays()
    for stress in ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5"):
        full = sensor_features(data, "fixed", stress=stress)
        short = sensor_features(
            {k: v[:45] for k, v in data.items()}, "fixed", stress=stress
        )
        np.testing.assert_allclose(
            full["features"][:15], short["features"], equal_nan=True
        )
        np.testing.assert_allclose(
            windows(full["features"], full["time"])[:15],
            windows(short["features"], short["time"]),
            equal_nan=True,
        )


def test_delay_availability_and_previous_commands():
    data = arrays()
    delayed = sensor_features(data, "fixed", stress="delay0.2")
    assert np.isnan(delayed["features"][:2]).all()
    assert delayed["source_frame"][2] == 0
    assert delayed["source_frame"][3] == 3
    np.testing.assert_array_equal(
        delayed["features"][3, 28:], data["actions"][2] - data["qpos"][3]
    )
    missing = sensor_features(data, "fixed", stress="drop0.3")
    for j, native in enumerate(missing["source_frame"]):
        if native >= 0:
            assert native <= j * 3
            np.testing.assert_array_equal(
                missing["features"][j, :14], data["qpos"][native]
            )


def test_fixed_training_normalization_never_fits_test_recording():
    train = np.arange(56, dtype=float).reshape(2, 28)
    fit = scale_fit([train], [np.ones(2, bool)])
    first = scaled(train[:1], fit)
    np.testing.assert_array_equal(
        first, scaled(np.r_[train[:1], train[1:] + 10000], fit)[:1]
    )


def test_phase_loss_masks_unannotated_records():
    logits = torch.randn(2, 4, 5)
    phases = torch.tensor([[0, 1, 2, 3], [-1, -1, -1, -1]])
    original = phase_loss(logits, phases)
    logits[1, :, 0] += 1000
    torch.testing.assert_close(original, phase_loss(logits, phases))
    assert phase_loss(logits, torch.full_like(phases, -1)) == 0


def test_filter_allowed_edges_and_unresolved_fallback():
    grammar = phase_matrix([np.array([0, 0, 1, 1, 2, -1])])
    assert grammar["allowed"][0, 1] and not grammar["allowed"][0, 2]
    prior = np.array([1.0, 0, 0, 0, 0])
    state, unresolved = filter_step(np.ones(5), prior, grammar["matrix"])
    assert not unresolved and state[2] == 0
    held, unresolved = filter_step(np.zeros(5), state, grammar["matrix"])
    assert unresolved
    np.testing.assert_array_equal(held, state)
    scores, _, flags = phase_layers(np.zeros((1, 5)), np.ones((1, 5)), [0.0], grammar)
    assert flags[0] and scores[1, 0] == scores[0, 0]


def test_marginal_argmax_can_violate_graph_despite_valid_latent_paths():
    matrix = np.array([[0.1, 0, 0.9], [0, 1, 0], [0, 0, 1]])
    previous = np.array([0.4, 0.6, 0])
    current, bad = filter_step(np.array([0.01, 0.01, 1.0]), previous, matrix)
    assert not bad and previous.argmax() == 1 and current.argmax() == 2
    assert matrix[1, 2] == 0  # The supported path 0→2 wins after marginalization.


def test_neural_outputs_and_hidden_states_are_causal():
    torch.manual_seed(11)
    x = torch.randn(1, 12, 28)
    model = SmallGRU(28, phase=True).eval()
    with torch.no_grad():
        full = model(x)[0]
        short = model(x[:, :5])[0]
        _, h = model.gru(x[:, :5])
        continued, _ = model.gru(x[:, 5:], h)
        direct, _ = model.gru(x)
    torch.testing.assert_close(full[:, :5], short)
    torch.testing.assert_close(continued, direct[:, 5:])
    fit = {
        "channels": 28,
        "phase": True,
        "state_dict": model.state_dict(),
        "scaler": {"mean": np.zeros(28), "std": np.ones(28)},
    }
    np.testing.assert_allclose(
        predict_neural(fit, x[0].numpy())[0][:5],
        predict_neural(fit, x[0, :5].numpy())[0],
        atol=1e-6,
    )


def test_runtime_packets_reject_annotation_and_identity_fields():
    values = {
        "time": 0.0,
        "source_time": 0.0,
        "qpos": [0.0] * 14,
        "previous_target": [0.0] * 14,
    }
    for field in ("onset", "true_phase", "outcome", "episode_length", "repository"):
        with pytest.raises(ValueError):
            SensorPacket.model_validate(values | {field: 1})


def test_phase_origin_is_not_chronological_phase_and_post_recovery_is_masked():
    series = sensor_features(arrays(), "fixed")
    row = {
        "role": "recovery",
        "onset": 0.5,
        "recovery": 1.0,
        "raw_annotation": {
            "failure": {"originating_phase": 5},
            "phase_boundaries": {f"tau_{i}": i * 18 for i in range(6)},
        },
    }
    y, mask, phase = targets(row, series, 3.0)
    assert not mask[10:].any() and (phase[10:] == -1).all()
    assert phase[0] == 0 and y[5] == 1


def test_first_alarm_is_never_reset_at_onset():
    t = np.arange(20) / 10
    s = np.zeros(20)
    s[2:4] = 1
    s[8:10] = 1
    row = {
        "group": "one",
        "role": "recovery",
        "fold": 0,
        "frames": 90,
        "onset": 0.5,
        "recovery": 1.5,
    }
    result = outcome(row, t, s, 0.5, 2.0)
    assert result["premature"] and not result["timely"]
    assert result["optimistic_post_onset_reset"]
    assert first_alarm(t, s, 0.5) == pytest.approx(0.3)


def test_conservative_calibration_and_persistence_capacity_agree():
    t = np.arange(20) / 10
    records = [(t, np.full(len(t), 0.5)) for _ in range(12)]
    fit = calibrate(records)
    assert fit["threshold"] > 0.5 and fit["reference_alarms"] == 0
    rng = np.random.default_rng(19)
    for _ in range(20):
        scores = rng.random(len(t))
        capacity = persistent_capacity(t, scores)
        assert first_alarm(t, scores, capacity) is not None
        assert first_alarm(t, scores, np.nextafter(capacity, np.inf)) is None


def test_boundary_interiors_change_support_without_making_new_recordings():
    row = {
        "group": "one",
        "role": "recovery",
        "fold": 0,
        "frames": 90,
        "onset": 0.5,
        "recovery": 1.2,
    }
    t, scores = np.arange(20) / 10, np.zeros(20)
    a = outcome(row, t, scores, 0.5, 2.0)
    b = outcome(row, t, scores, 0.5, 2.0, delta=0.5)
    assert a["evaluable"] and not b["evaluable"]
    assert a["group"] == b["group"] and not a["timely"]


def test_alias_crosswalk_counts_recordings_once_and_rejects_duplicate_cohort(
    tmp_path, monkeypatch
):
    from dual_rec.reboot import overnight_data as data

    old = tmp_path / "old"
    phase_path = old / "data" / data.CORE[0] / "meta/phase.json"
    phase_path.parent.mkdir(parents=True)
    labels = [
        {
            "episode_index": str(i),
            "episode_type": "recovery",
            "duration_frames": 60,
            "fps": 30,
            "phase_boundaries": {f"tau_{j}": j * 12 for j in range(6)},
            "failure": {
                "originating_phase": 1,
                "failure_mode": "test",
                "induced_at_frame": 3,
                "recovery_started_at_frame": 15,
            },
        }
        for i in range(10)
    ]
    phase_path.write_text(json.dumps({"episodes": labels}))

    def recording(offset):
        result = arrays(60)
        result["qpos"] += offset
        result["actions"] += offset
        result["frame_index"] = np.arange(60)
        return result

    source = {i: recording(i) for i in range(10)}
    reference = {i: recording(i + 100) for i in range(10)}
    monkeypatch.setattr(data, "OLD", old)
    monkeypatch.setattr(data, "verified_inputs", lambda root: {})
    monkeypatch.setattr(
        data,
        "episode_arrays",
        lambda root, name: reference if name == data.CORE[2] else source,
    )
    rows = data.make_registry(tmp_path)
    assert len(rows) == len({r["group"] for r in rows}) == 20
    assert sum(len(r["aliases"]) for r in rows) == 30
    reference[1] = reference[0]
    with pytest.raises(ValueError, match="Duplicate canonical"):
        data.make_registry(tmp_path)


def test_incremental_replay_matches_batch_model_without_annotation_inputs():
    from dual_rec.reboot.overnight_replay import StreamingDetector

    torch.manual_seed(11)
    network = SmallGRU(28, phase=True)
    fit = {
        "channels": 28,
        "phase": True,
        "state_dict": network.state_dict(),
        "scaler": {"mean": np.zeros(28), "std": np.ones(28)},
    }
    grammar = phase_matrix([np.array([0, 0, 1, 1, 2, 3])])
    data = arrays()
    series = sensor_features(data, "one", variant="Q")
    _, e, h = predict_neural(fit, series["features"])
    expected, _, _ = phase_layers(e, h, series["time"], grammar)
    stream = StreamingDetector({"P": [fit], "grammar": grammar}, 0.5)
    observed = []
    for j, frame in enumerate(series["native_frame"]):
        packet = SensorPacket(
            time=float(series["time"][j]),
            source_time=float(series["time"][j]),
            qpos=data["qpos"][frame].tolist(),
            previous_target=(
                data["actions"][frame - 1] if frame else data["qpos"][0]
            ).tolist(),
        )
        observed.append(stream.update(packet)["risk"])
    np.testing.assert_allclose(observed, expected[1], atol=1e-6)


def test_finalization_requires_unchanged_historical_document_prefix():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/reboot_overnight_finalize.py"
    spec = importlib.util.spec_from_file_location("overnight_finalize", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.preserve_prefix(b"original\nnew authorized appendix\n", b"original\n")
    with pytest.raises(ValueError, match="prefix changed"):
        module.preserve_prefix(b"rewritten\nnew appendix\n", b"original\n")
