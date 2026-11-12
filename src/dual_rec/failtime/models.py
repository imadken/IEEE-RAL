"""Fixed causal features, nominal evidence, logistic and GRU32 comparators.

Runtime functions accept robot observations and a known robot stratum only.
Released onsets and verdicts enter supervised targets outside this module.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from dual_rec.reboot.overnight_models import (
    fit_logistic,
    predict_logistic,
    scale_fit,
    scaled,
    windows,
)

Checkpoint = dict[str, Any]
VELOCITY_CHANNELS = np.arange(16, 32)


def _observations(times: np.ndarray, eef: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    t = np.asarray(times, dtype=np.float64)
    x = np.asarray(eef, dtype=np.float64)
    if t.ndim != 1 or x.shape != (len(t), 16):
        raise ValueError("Expected one timestamp and 16 end-effector values per frame")
    if not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
        raise ValueError(
            "Observation timestamps must be finite and strictly increasing"
        )
    return t, x


def causal_features(times: np.ndarray, eef: np.ndarray) -> np.ndarray:
    """EEF16 and backward differences; invalid packets leave state unchanged.

    Quaternion coordinates retain their released representation: no whole-run
    normalization or sign correction is applied. A valid initial derivative is
    zero; later derivatives use the latest valid earlier measurement and its
    actual timestamp. No later sample affects an earlier feature.
    """
    t, x = _observations(times, eef)
    result = np.full((len(t), 32), np.nan)
    previous = None
    for i, now in enumerate(t):
        if not np.isfinite(x[i]).all():
            continue
        derivative = (
            np.zeros(16)
            if previous is None
            else (x[i] - x[previous]) / (now - t[previous])
        )
        result[i] = np.r_[x[i], derivative]
        previous = i
    return result


def _motion_steps(eef: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-arm displacement squared and gripper sign using earlier packets."""
    steps = np.full((len(eef), 2), np.nan)
    signs = np.full((len(eef), 2), np.nan)
    previous = None
    for i, row in enumerate(eef):
        if not np.isfinite(row).all():
            continue
        if previous is None:
            steps[i], signs[i] = 0, 0
        else:
            for arm, start in enumerate((0, 8)):
                steps[i, arm] = np.sum(
                    (row[start : start + 3] - eef[previous, start : start + 3]) ** 2
                )
                signs[i, arm] = np.sign(row[start + 7] - eef[previous, start + 7])
        previous = i
    return steps, signs


def observable_modes(eef: np.ndarray, motion_floor: np.ndarray) -> np.ndarray:
    """36 combinations of opening/still/closing and moving/stopped per arm."""
    steps, signs = _motion_steps(np.asarray(eef, dtype=np.float64))
    mode = np.full(len(steps), -1, dtype=np.int64)
    valid = np.isfinite(steps).all(axis=1)
    arm = ((signs[valid] + 1) * 2 + (steps[valid] > motion_floor)).astype(int)
    mode[valid] = arm[:, 0] * 6 + arm[:, 1]
    return mode


def _distribution(blocks: list[np.ndarray]) -> Checkpoint:
    blocks = [b for b in blocks if len(b)]
    if not blocks:
        raise ValueError("No finite nominal evidence")
    means = np.asarray([b.mean(axis=0) for b in blocks])
    seconds = np.asarray([(b * b).mean(axis=0) for b in blocks])
    mean = means.mean(axis=0)
    std = np.maximum(np.sqrt(np.maximum(seconds.mean(axis=0) - mean * mean, 0)), 1e-6)
    evidence = np.concatenate(
        [np.mean(np.clip((b - mean) / std, -10, 10) ** 2, axis=1) for b in blocks]
    )
    return {
        "mean": mean,
        "std": std,
        "drift": float(np.quantile(evidence, 0.9)),
        "frames": sum(map(len, blocks)),
        "recordings": len(blocks),
    }


def fit_nominal(records: Sequence[dict[str, Any]]) -> Checkpoint:
    """Fit only caller-supplied development-success recordings, by robot.

    A mode requires 50 finite frames drawn from at least two recordings. All
    unsupported modes back off to that robot's global nominal distribution.
    The pooled 20th-percentile motion floor and 90th-percentile evidence drift
    are learned from these same training-success observations only.
    """
    robots = {}
    for robot in sorted({str(r["robot"]) for r in records}):
        population = [r for r in records if str(r["robot"]) == robot]
        arrays = [_observations(r["time"], r["eef"]) for r in population]
        steps = [_motion_steps(x)[0] for _, x in arrays]
        finite_steps = [s[np.isfinite(s).all(axis=1)] for s in steps]
        finite_steps = [s for s in finite_steps if len(s)]
        if not finite_steps:
            continue
        floor = np.quantile(np.concatenate(finite_steps), 0.2, axis=0)
        velocities = [causal_features(t, x)[:, VELOCITY_CHANNELS] for t, x in arrays]
        modes = [observable_modes(x, floor) for _, x in arrays]
        global_blocks = [v[np.isfinite(v).all(axis=1)] for v in velocities]
        conditioned = {}
        for mode in range(36):
            blocks = [
                v[(m == mode) & np.isfinite(v).all(axis=1)]
                for v, m in zip(velocities, modes, strict=True)
            ]
            blocks = [b for b in blocks if len(b)]
            if len(blocks) >= 2 and sum(map(len, blocks)) >= 50:
                conditioned[mode] = _distribution(blocks)
        robots[robot] = {
            "motion_floor": floor,
            "global": _distribution(global_blocks),
            "modes": conditioned,
        }
    return {
        "kind": "nominal_velocity",
        "robots": robots,
        "channels": VELOCITY_CHANNELS.tolist(),
        "minimum_mode_frames": 50,
        "minimum_mode_recordings": 2,
        "std_floor": 1e-6,
        "clip": 10.0,
        "drift_quantile": 0.9,
    }


def score_nominal(
    fit: Checkpoint,
    robot: str,
    times: np.ndarray,
    eef: np.ndarray,
    *,
    conditioned: bool = True,
    accumulate: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One fixed CUSUM or its no-accumulation ablation from recording start."""
    t, x = _observations(times, eef)
    risk = np.full(len(t), np.nan)
    backoff = np.ones(len(t), dtype=bool)
    if robot not in fit["robots"]:
        return risk, np.full(len(t), -1, dtype=np.int64), backoff
    nominal = fit["robots"][robot]
    mode = observable_modes(x, nominal["motion_floor"])
    velocities = causal_features(t, x)[:, VELOCITY_CHANNELS]
    state = 0.0
    for i, value in enumerate(velocities):
        if not np.isfinite(value).all():
            state = 0.0
            continue
        use_mode = conditioned and int(mode[i]) in nominal["modes"]
        distribution = nominal["modes"][int(mode[i])] if use_mode else nominal["global"]
        backoff[i] = not use_mode
        evidence = float(
            np.mean(
                np.clip((value - distribution["mean"]) / distribution["std"], -10, 10)
                ** 2
            )
        )
        increment = evidence / max(distribution["drift"], 1e-6) - 1.0
        state = max(0.0, state + increment) if accumulate else increment
        risk[i] = state
    return risk, mode, backoff


def prior_scores(times: np.ndarray, failure_prior: float) -> dict[str, np.ndarray]:
    """Controls use elapsed time and a fixed development prevalence only."""
    t = np.asarray(times, dtype=float)
    return {
        "B0_time": t - t[0] if len(t) else t.copy(),
        "B0_prior": np.full(len(t), failure_prior, dtype=float),
    }


def fit_logistic_detector(
    xs: Sequence[np.ndarray],
    times: Sequence[np.ndarray],
    ys: Sequence[np.ndarray],
    masks: Sequence[np.ndarray],
) -> Checkpoint:
    design = [windows(x, t) for x, t in zip(xs, times, strict=True)]
    usable = [
        np.asarray(m, bool) & np.isfinite(x).all(axis=1)
        for x, m in zip(design, masks, strict=True)
    ]
    if not all(m.any() for m in usable):
        raise ValueError("Each training recording requires finite supervised support")
    return fit_logistic(design, list(ys), usable, regularization=0.01)


def predict_logistic_detector(
    fit: Checkpoint, x: np.ndarray, times: np.ndarray
) -> np.ndarray:
    return predict_logistic(fit, windows(x, times))


class GRU32(nn.Module):
    """One causal recurrent layer and one scalar failure head."""

    def __init__(self, channels: int = 32):
        super().__init__()
        self.gru = nn.GRU(channels, 32, batch_first=True)
        self.failure = nn.Linear(32, 1)

    def forward(self, x, lengths=None):
        if lengths is None:
            hidden, _ = self.gru(x)
        else:
            packed = pack_padded_sequence(
                x, lengths, batch_first=True, enforce_sorted=False
            )
            hidden, _ = self.gru(packed)
            hidden, _ = pad_packed_sequence(
                hidden, batch_first=True, total_length=x.shape[1]
            )
        return self.failure(hidden)[..., 0]


def fit_gru(
    xs: Sequence[np.ndarray],
    ys: Sequence[np.ndarray],
    masks: Sequence[np.ndarray],
    *,
    seed: int,
    epochs: int = 30,
) -> Checkpoint:
    """Fixed equal-recording BCE, training-only normalization and one declared seed."""
    if seed not in (11, 23, 37) or not 1 <= epochs <= 30:
        raise ValueError("Only declared seeds and at most 30 epochs are authorized")
    torch.manual_seed(seed)
    usable = [
        np.asarray(m, bool) & np.isfinite(x).all(axis=1)
        for x, m in zip(xs, masks, strict=True)
    ]
    if not len(xs) or not all(m.any() for m in usable):
        raise ValueError("Every training recording requires finite supervised support")
    scaler = scale_fit(list(xs), usable)
    valid = [np.isfinite(x).all(axis=1) for x in xs]
    lengths = [int(v.sum()) for v in valid]
    maximum = max(lengths)
    x = torch.zeros(len(xs), maximum, xs[0].shape[1])
    y = torch.zeros(len(xs), maximum)
    mask = torch.zeros_like(y)
    for i, (values, labels, supervised, keep) in enumerate(
        zip(xs, ys, usable, valid, strict=True)
    ):
        n = lengths[i]
        x[i, :n] = torch.as_tensor(scaled(values[keep], scaler), dtype=torch.float32)
        y[i, :n] = torch.as_tensor(np.asarray(labels)[keep], dtype=torch.float32)
        mask[i, :n] = torch.as_tensor(supervised[keep], dtype=torch.float32)
    positives = float((y * mask).sum())
    negatives = float(((1 - y) * mask).sum())
    if positives <= 0 or negatives <= 0:
        raise ValueError("Training split lacks positive or negative support")
    weight = min(10.0, negatives / positives)
    model = GRU32(xs[0].shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.01)
    history = []
    started = time.monotonic()
    for epoch in range(epochs):
        optimizer.zero_grad()
        logits = model(x, lengths)
        loss = nn.functional.binary_cross_entropy_with_logits(
            logits, y, pos_weight=torch.tensor(weight), reduction="none"
        )
        loss = ((loss * mask).sum(1) / mask.sum(1)).mean()
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite GRU loss")
        loss.backward()
        norm = nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        history.append(
            {
                "epoch": epoch + 1,
                "loss": float(loss.detach()),
                "gradient_norm_before_clip": float(norm),
            }
        )
    return {
        "kind": "gru32",
        "state_dict": model.state_dict(),
        "scaler": scaler,
        "channels": xs[0].shape[1],
        "seed": seed,
        "epochs": epochs,
        "history": history,
        "positive_weight": weight,
        "training_wall_seconds": time.monotonic() - started,
        "optimizer": {
            "name": "Adam",
            "lr": 0.001,
            "weight_decay": 0.01,
            "gradient_clip": 1.0,
        },
    }


def predict_gru(fit: Checkpoint, x: np.ndarray) -> np.ndarray:
    model = GRU32(fit["channels"])
    model.load_state_dict(fit["state_dict"])
    model.eval()
    result = np.full(len(x), np.nan)
    valid = np.isfinite(x).all(axis=1)
    if valid.any():
        with torch.no_grad():
            tensor = torch.as_tensor(
                scaled(x[valid], fit["scaler"]), dtype=torch.float32
            )[None]
            result[valid] = torch.sigmoid(model(tensor))[0].numpy()
    return result
