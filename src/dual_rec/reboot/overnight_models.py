"""Fixed small evidence models and three inference layers on shared weights."""

from __future__ import annotations

import time
from itertools import pairwise

import numpy as np
import torch
from scipy.optimize import minimize
from scipy.special import expit
from torch import nn


def scale_fit(xs, masks):
    selected = [x[m] for x, m in zip(xs, masks, strict=True) if m.any()]
    mean = np.mean([x.mean(axis=0) for x in selected], axis=0)
    second = np.mean([(x * x).mean(axis=0) for x in selected], axis=0)
    return {
        "mean": mean,
        "std": np.maximum(np.sqrt(np.maximum(second - mean * mean, 0)), 1e-6),
    }


def scaled(x, scaler):
    return np.clip((x - scaler["mean"]) / scaler["std"], -10, 10)


def windows(x, times):
    result = []
    for i, now in enumerate(times):
        start = np.searchsorted(times, now - 1 - 2e-6)
        block, t = x[start : i + 1], times[start : i + 1]
        finite = np.isfinite(block).all(axis=1)
        block, t = block[finite], t[finite]
        if not len(block):
            result.append(np.full(x.shape[1] * 4, np.nan))
            continue
        t = t - t.mean()
        slope = t @ block / (t @ t) if len(t) > 1 else np.zeros(x.shape[1])
        result.append(np.concatenate([block[-1], block.mean(0), block.std(0), slope]))
    return np.asarray(result)


def clock_features(times):
    return np.eye(31)[np.minimum(np.floor(times + 2e-6).astype(int), 30)]


def fit_logistic(xs, ys, masks, *, regularization=0.01):
    scaler = scale_fit(xs, masks)
    weight_positive = min(
        10.0,
        sum(np.sum((1 - y)[m]) for y, m in zip(ys, masks, strict=True))
        / max(1, sum(y[m].sum() for y, m in zip(ys, masks, strict=True))),
    )
    x = np.concatenate(
        [
            np.c_[np.ones(m.sum()), scaled(a[m], scaler)]
            for a, m in zip(xs, masks, strict=True)
        ]
    )
    y = np.concatenate([a[m] for a, m in zip(ys, masks, strict=True)])
    weight = np.concatenate([np.full(m.sum(), 1 / m.sum() / len(xs)) for m in masks])
    weight *= np.where(y > 0, weight_positive, 1)

    def objective(beta):
        logits = x @ beta
        loss = np.sum(
            weight * (np.logaddexp(0, logits) - y * logits)
        ) + 0.5 * regularization * (beta[1:] @ beta[1:])
        gradient = x.T @ (weight * (expit(logits) - y))
        gradient[1:] += regularization * beta[1:]
        return loss, gradient

    fit = minimize(
        objective,
        np.zeros(x.shape[1]),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 200, "ftol": 1e-9, "gtol": 1e-6},
    )
    return {
        "kind": "logistic",
        "scaler": scaler,
        "beta": fit.x,
        "converged": bool(fit.success),
        "iterations": int(fit.nit),
        "positive_weight": weight_positive,
        "objective": float(fit.fun),
    }


def predict_logistic(fit, x):
    return expit(np.c_[np.ones(len(x)), scaled(x, fit["scaler"])] @ fit["beta"])


def ar_design(x):
    width = 140 + (14 if x.shape[1] == 42 else 0)
    result = np.full((len(x), width), np.nan)
    for i in range(10, len(x)):
        past = x[i - 10 : i, :14].reshape(-1)
        # Current discrepancy itself contains the response; recover the target
        # issued before this observation instead, so AR cannot copy its target.
        result[i] = np.r_[past, x[i, 28:42] + x[i, :14]] if width > 140 else past
    return result


def fit_anomaly(xs):
    design = [ar_design(x) for x in xs]
    masks = [np.isfinite(x).all(axis=1) for x in design]
    scaler = scale_fit(design, masks)
    x = np.concatenate(
        [
            np.c_[np.ones(m.sum()), scaled(a[m], scaler)]
            for a, m in zip(design, masks, strict=True)
        ]
    )
    y = np.concatenate([a[m, :14] for a, m in zip(xs, masks, strict=True)])
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0
    beta = np.linalg.solve(x.T @ x + penalty, x.T @ y)
    residual = y - x @ beta
    center = np.median(residual, axis=0)
    spread = np.maximum(1.4826 * np.median(np.abs(residual - center), axis=0), 1e-6)
    return {
        "kind": "anomaly",
        "scaler": scaler,
        "beta": beta,
        "center": center,
        "spread": spread,
    }


def predict_anomaly(fit, x):
    design = ar_design(x)
    predicted = np.c_[np.ones(len(x)), scaled(design, fit["scaler"])] @ fit["beta"]
    return np.abs((x[:, :14] - predicted - fit["center"]) / fit["spread"]).mean(axis=1)


def phase_matrix(phases):
    counts, initial, support = np.zeros((5, 5)), np.ones(5), np.zeros(5, dtype=int)
    for p in phases:
        valid = p >= 0
        if valid.any():
            initial[p[np.flatnonzero(valid)[0]]] += 1
        for state in p[valid]:
            support[state] += 1
        for a, b in pairwise(p):
            if a >= 0 and b >= 0:
                counts[a, b] += 1
    allowed = (counts > 0) | np.eye(5, dtype=bool)
    matrix = np.where(allowed, counts + 1, 0)
    matrix /= matrix.sum(axis=1, keepdims=True)
    return {
        "matrix": matrix,
        "initial": initial / initial.sum(),
        "counts": counts,
        "allowed": allowed,
        "support": support,
    }


def filter_step(emission, previous, matrix):
    value = emission * (previous @ matrix)
    total = value.sum()
    if not np.isfinite(value).all() or np.any(value < 0) or total <= 0:
        return previous.copy(), True
    return value / total, False


def phase_layers(emissions, heads, times, grammar):
    alpha, smooth = grammar["initial"].copy(), None
    scores, states, unresolved = [[], [], []], [[], [], []], []
    previous_time = None
    for emission, head, now in zip(emissions, heads, times, strict=True):
        alpha, fallback = filter_step(emission, alpha, grammar["matrix"])
        amount = (
            1 if previous_time is None else 1 - np.exp(-(now - previous_time) / 0.3)
        )
        smooth = (
            emission.copy()
            if smooth is None
            else amount * emission + (1 - amount) * smooth
        )
        mixtures = [emission, emission if fallback else alpha, smooth]
        for i, weights in enumerate(mixtures):
            scores[i].append(float(weights @ head))
            states[i].append(weights.copy())
        unresolved.append(fallback)
        previous_time = now
    return np.asarray(scores), np.asarray(states), np.asarray(unresolved)


class SmallGRU(nn.Module):
    def __init__(self, channels, *, phase=False):
        super().__init__()
        self.phase = phase
        self.gru = nn.GRU(channels, 32, batch_first=True)
        self.failure = nn.Linear(32, 5 if phase else 1)
        if phase:
            self.phase_head = nn.Linear(32, 5)

    def forward(self, x, hidden=None):
        evidence, hidden = self.gru(x, hidden)
        logits = self.failure(evidence)
        if self.phase:
            phase = self.phase_head(evidence)
            probabilities = torch.softmax(phase, dim=-1)
            risk = (probabilities * torch.sigmoid(logits)).sum(dim=-1)
            return risk, phase, logits, hidden
        return torch.sigmoid(logits[..., 0]), None, logits, hidden


def failure_loss(probabilities, labels, mask, positive_weight):
    loss = nn.functional.binary_cross_entropy(
        probabilities.clamp(1e-6, 1 - 1e-6), labels, reduction="none"
    )
    loss *= torch.where(labels > 0, positive_weight, 1.0)
    return ((loss * mask).sum(1) / mask.sum(1).clamp_min(1)).mean()


def phase_loss(logits, phases):
    mask = phases >= 0
    loss = nn.functional.cross_entropy(
        logits.transpose(1, 2), phases.clamp_min(0), reduction="none"
    )
    per_record = (loss * mask).sum(1) / mask.sum(1).clamp_min(1)
    return per_record[mask.any(1)].mean() if mask.any() else logits.sum() * 0


def fit_neural(xs, ys, masks, phases, *, seed, epochs, phase=False):
    torch.manual_seed(seed)
    scaler = scale_fit(xs, masks)
    maximum = max(map(len, xs))
    x = torch.zeros(len(xs), maximum, xs[0].shape[1])
    y, mask = torch.zeros(len(xs), maximum), torch.zeros(len(xs), maximum)
    p = torch.full((len(xs), maximum), -1, dtype=torch.long)
    for i, values in enumerate(xs):
        n = len(values)
        x[i, :n] = torch.as_tensor(scaled(values, scaler), dtype=torch.float32)
        y[i, :n] = torch.as_tensor(ys[i], dtype=torch.float32)
        mask[i, :n] = torch.as_tensor(masks[i], dtype=torch.float32)
        p[i, :n] = torch.as_tensor(phases[i])
    positive_weight = min(
        10.0, float(((1 - y) * mask).sum() / (y * mask).sum().clamp_min(1))
    )
    model = SmallGRU(xs[0].shape[1], phase=phase)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    history = []
    started = time.monotonic()
    for _ in range(epochs):
        optimizer.zero_grad()
        probabilities, phase_logits, _, _ = model(x)
        loss = failure_loss(probabilities, y, mask, positive_weight)
        if phase:
            loss = loss + 0.2 * phase_loss(phase_logits, p)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        history.append(float(loss.detach()))
    return {
        "kind": "neural",
        "state_dict": model.state_dict(),
        "scaler": scaler,
        "phase": phase,
        "channels": xs[0].shape[1],
        "seed": seed,
        "epochs": epochs,
        "loss": history,
        "positive_weight": positive_weight,
        "training_wall_seconds": time.monotonic() - started,
    }


def predict_neural(fit, x):
    model = SmallGRU(fit["channels"], phase=fit["phase"])
    model.load_state_dict(fit["state_dict"])
    model.eval()
    output = np.full(len(x), np.nan)
    emissions = np.full((len(x), 5), np.nan)
    heads = emissions.copy()
    valid = np.isfinite(x).all(axis=1)
    if not valid.any():
        return output, emissions, heads
    start = np.flatnonzero(valid)[0]
    if not valid[start:].all():
        raise ValueError(
            "Unavailable sensor packets must be causally held after startup"
        )
    with torch.no_grad():
        risk, phase, failure, _ = model(
            torch.as_tensor(scaled(x[start:], fit["scaler"]), dtype=torch.float32)[None]
        )
    output[start:] = risk[0].numpy()
    if phase is not None:
        emissions[start:] = torch.softmax(phase[0], dim=-1).numpy()
        heads[start:] = torch.sigmoid(failure[0]).numpy()
    return output, emissions, heads
