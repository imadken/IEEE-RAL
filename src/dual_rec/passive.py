"""Small passive diagnostic baselines using training-only history transforms."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata


def squared_distances(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.maximum(
        (x * x).sum(1)[:, None] + (y * y).sum(1)[None, :] - 2 * x @ y.T, 0
    )


def fit_model(x: np.ndarray, y: np.ndarray, mode: str, regularization: float) -> dict:
    if len(np.unique(y)) != 2 or not np.isfinite(x).all():
        raise ValueError("A diagnostic fit needs finite features and both classes")
    mean, scale = x.mean(0), np.maximum(x.std(0), 1e-6)
    standardized = (x - mean) / scale
    bandwidth = None
    centers = None
    if mode == "logistic":
        design = standardized
        penalty_matrix = None
    elif mode == "rbf_kernel_logistic":
        distance = squared_distances(standardized, standardized)
        nonzero = distance[np.triu_indices(len(x), 1)]
        nonzero = nonzero[nonzero > 1e-12]
        bandwidth = float(np.median(nonzero)) if len(nonzero) else 1.0
        design = np.exp(-distance / bandwidth)
        penalty_matrix = design + np.eye(len(x)) * 1e-8
        centers = standardized
    else:
        raise ValueError("Unknown passive baseline")

    def objective(parameters):
        weights, intercept = parameters[:-1], parameters[-1]
        score = design @ weights + intercept
        residual = (expit(score) - y) / len(y)
        penalty = weights if penalty_matrix is None else penalty_matrix @ weights
        loss = (
            np.mean(np.logaddexp(0, score) - y * score)
            + regularization * (weights @ penalty) / 2
        )
        gradient = np.r_[design.T @ residual + regularization * penalty, residual.sum()]
        return float(loss), gradient

    fitted = minimize(
        objective,
        np.zeros(design.shape[1] + 1),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 300, "ftol": 1e-10, "gtol": 1e-7},
    )
    if not fitted.success:
        raise RuntimeError(f"Passive fit failed: {fitted.message}")
    return {
        "mode": mode,
        "regularization": regularization,
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "weights": fitted.x[:-1].tolist(),
        "intercept": float(fitted.x[-1]),
        "bandwidth": bandwidth,
        "centers": centers.tolist() if centers is not None else None,
    }


def predict(model: dict, x: np.ndarray) -> np.ndarray:
    transformed = (x - np.asarray(model["mean"])) / np.asarray(model["scale"])
    if model["mode"] == "rbf_kernel_logistic":
        transformed = np.exp(
            -squared_distances(transformed, np.asarray(model["centers"]))
            / model["bandwidth"]
        )
    return expit(transformed @ np.asarray(model["weights"]) + model["intercept"])


def metrics(y: np.ndarray, probability: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    if len(np.unique(y)) != 2 or not np.isfinite(probability).all():
        raise ValueError("Metrics need both classes and finite predictions")
    clipped = np.clip(probability, 1e-12, 1 - 1e-12)
    positive = y == 1
    ranks = rankdata(probability)
    npositive = int(positive.sum())
    nnegative = len(y) - npositive
    auc = (ranks[positive].sum() - npositive * (npositive + 1) / 2) / (
        npositive * nnegative
    )
    hard = probability >= 0.5
    balanced = 0.5 * (hard[positive].mean() + (~hard[~positive]).mean())
    ece = 0.0
    bins = np.minimum((probability * 5).astype(int), 4)
    for index in range(5):
        selected = bins == index
        if selected.any():
            ece += selected.mean() * abs(
                y[selected].mean() - probability[selected].mean()
            )
    return {
        "auroc": float(auc),
        "balanced_accuracy": float(balanced),
        "brier": float(np.mean((probability - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))),
        "ece_5_bins": float(ece),
    }


def select_model(
    x: np.ndarray, y: np.ndarray, groups: np.ndarray, mode: str, candidates: list[float]
) -> tuple[dict, list]:
    unique = np.unique(groups)
    if len(unique) < 4:
        raise ValueError("Need four independent development seed groups")
    fold_by_group = {int(seed): index % 4 for index, seed in enumerate(unique)}
    folds = np.array([fold_by_group[int(seed)] for seed in groups])
    scores = []
    for value in candidates:
        predictions = np.zeros(len(y))
        for fold in range(4):
            train = folds != fold
            test = ~train
            assert not set(groups[train]) & set(groups[test])
            model = fit_model(x[train], y[train], mode, value)
            predictions[test] = predict(model, x[test])
        scores.append(
            {
                "regularization": value,
                "cross_validated_metrics": metrics(y, predictions),
                "probabilities": predictions.tolist(),
                "folds": folds.tolist(),
            }
        )
    chosen = min(
        scores,
        key=lambda row: (
            row["cross_validated_metrics"]["log_loss"],
            -row["regularization"],
        ),
    )
    return fit_model(x, y, mode, chosen["regularization"]), scores


def clustered_metric_intervals(y, probability, groups, repetitions=2000, seed=7321):
    y, probability, groups = np.asarray(y), np.asarray(probability), np.asarray(groups)
    unique = np.unique(groups)
    rng = np.random.default_rng(seed)
    samples = {name: [] for name in metrics(y, probability)}
    for _ in range(repetitions):
        indices = np.concatenate(
            [
                np.flatnonzero(groups == group)
                for group in rng.choice(unique, len(unique), replace=True)
            ]
        )
        if len(np.unique(y[indices])) < 2:
            continue
        values = metrics(y[indices], probability[indices])
        for name, value in values.items():
            samples[name].append(value)
    return {
        name: np.quantile(values, [0.025, 0.975]).tolist()
        for name, values in samples.items()
    }


def mean_interval(values, repetitions=2000, seed=7321, confidence=0.95):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return None
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(repetitions, len(values)))].mean(
        1
    )
    alpha = (1 - confidence) / 2
    return {
        "mean": float(values.mean()),
        "ci": np.quantile(means, [alpha, 1 - alpha]).tolist(),
        "independent_seeds": len(values),
        "confidence": confidence,
    }


def wilson(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = (
        z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    )
    return [float(max(0, center - radius)), float(min(1, center + radius))]
