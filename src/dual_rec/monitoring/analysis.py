"""Parent-clustered descriptive analysis independent of monitoring method code."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

SEED = 71603
RESAMPLES = 2000
PRIMARY_REGIMES = frozenset({"missing10", "missing30", "missing50", "structured"})
ACCURATE_REGIMES = PRIMARY_REGIMES | {"complete", "delayed"}
METRICS = (
    "false_current_permission",
    "invalid_continuation_permission",
    "goal_completion",
    "valid_continuation",
    "abstention",
    "unnecessary_abstention",
    "justified_abstention",
    "recovery_invoked",
    "query_count",
    "simulated_cost",
    "decision_seconds",
    "query_seconds",
)
ERROR_METRICS = frozenset(
    {"false_current_permission", "invalid_continuation_permission"}
)


class Measurement(BaseModel):
    """Validate numeric records without retaining large evaluator trace payloads."""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    method: str
    parent_id: str
    episode_id: str
    family: str
    regime: str
    budget: int = Field(ge=0, le=3)
    false_current_permission: float = Field(ge=0, le=1)
    invalid_continuation_permission: float = Field(ge=0, le=1)
    goal_completion: float = Field(ge=0, le=1)
    valid_continuation: float = Field(ge=0, le=1)
    abstention: float = Field(ge=0, le=1)
    unnecessary_abstention: float = Field(ge=0, le=1)
    justified_abstention: float = Field(ge=0, le=1)
    recovery_invoked: float = Field(ge=0, le=1)
    query_count: float = Field(ge=0)
    simulated_cost: float = Field(ge=0)
    decision_seconds: float = Field(ge=0)
    query_seconds: float = Field(ge=0)
    classification_resolved: float | None = Field(default=None, ge=0, le=1)
    continuation_permitted: bool = False


def _load(path: Path) -> tuple[list[Measurement], dict[str, int]]:
    rows = []
    skipped: Counter[str] = Counter()
    seen = set()
    family_by_parent = {}
    with gzip.open(path, "rt") as stream:
        for line in stream:
            raw = json.loads(line)
            if raw.get("skip_reason"):
                if raw.get("method") != "M4":
                    raise ValueError("Only bounded M4 reference cases may be skipped")
                skipped[f"{raw.get('method', 'unknown')}:{raw['skip_reason']}"] += 1
                continue
            row = Measurement.model_validate(raw)
            key = (row.method, row.episode_id, row.regime, row.budget)
            if key in seen:
                raise ValueError(f"Duplicate method/episode/budget record: {key}")
            seen.add(key)
            previous_family = family_by_parent.setdefault(row.parent_id, row.family)
            if previous_family != row.family:
                raise ValueError("Parent identifier occurs in multiple domain families")
            rows.append(row)
    if not rows:
        raise ValueError("No evaluated decision records")
    return rows, dict(sorted(skipped.items()))


def _bootstrap(
    values: np.ndarray, families: list[str], key: str
) -> tuple[np.ndarray, np.ndarray]:
    """Resample parents within each family, preserving family sample sizes."""
    digest = hashlib.sha256(f"{SEED}:{key}".encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    sums = np.zeros((RESAMPLES, values.shape[1]))
    labels = np.asarray(families)
    for family in sorted(set(families)):
        indices = np.flatnonzero(labels == family)
        sampled = indices[rng.integers(0, len(indices), size=(RESAMPLES, len(indices)))]
        sums += values[sampled].sum(axis=1)
    return tuple(np.quantile(sums / len(values), [0.025, 0.975], axis=0))


def zero_event_upper_95(n_parents: int) -> float:
    """Exact one-sided bound for zero event-bearing independent parent groups."""
    if n_parents <= 0:
        raise ValueError("A positive independent-parent denominator is required")
    return 1 - 0.05 ** (1 / n_parents)


def _stats(rows: list[Measurement], key: str) -> dict:
    metrics = list(METRICS)
    if all(row.classification_resolved is not None for row in rows):
        metrics.append("classification_resolved")
    parent_rows: dict[str, list[Measurement]] = defaultdict(list)
    for row in rows:
        parent_rows[row.parent_id].append(row)
    parents = sorted(parent_rows)
    values = np.asarray(
        [
            [
                np.mean([getattr(row, metric) for row in parent_rows[parent]])
                for metric in metrics
            ]
            for parent in parents
        ]
    )
    lower, upper = _bootstrap(values, [parent_rows[p][0].family for p in parents], key)
    result = {}
    for index, metric in enumerate(metrics):
        estimate = {
            "mean": float(values[:, index].mean()),
            "ci": [float(lower[index]), float(upper[index])],
            "n_parents": len(parents),
            "n_decisions": len(rows),
        }
        if metric in ERROR_METRICS:
            event_parents = sum(
                any(getattr(r, metric) > 0 for r in parent_rows[p]) for p in parents
            )
            estimate["event_parents"] = event_parents
            estimate["zero_event_parent_upper_95"] = (
                zero_event_upper_95(len(parents)) if event_parents == 0 else None
            )
            estimate["bound_scope"] = (
                "Probability a parent has any observed event under this tested schedule; not per-action physical safety"
            )
        result[metric] = estimate
    return {
        "metrics": result,
        "parent_ids": parents,
        "n_permissions": sum(row.continuation_permitted for row in rows),
        "raw_false_current_permissions": sum(
            row.false_current_permission for row in rows
        ),
        "n_decisions": len(rows),
        "n_parents": len(parents),
    }


def _paired(
    rows: list[Measurement],
    left: str,
    right: str,
    key: str,
    metrics: tuple[str, ...] = METRICS,
) -> dict | None:
    sides = {
        method: {
            (r.episode_id, r.regime, r.budget): r for r in rows if r.method == method
        }
        for method in (left, right)
    }
    common = sorted(sides[left].keys() & sides[right].keys())
    if not common:
        return None
    differences: dict[str, list[list[float]]] = defaultdict(list)
    families = {}
    for item in common:
        a, b = sides[left][item], sides[right][item]
        if (a.parent_id, a.family) != (b.parent_id, b.family):
            raise ValueError("Paired episode identifiers disagree on parent/family")
        differences[a.parent_id].append(
            [getattr(a, m) - getattr(b, m) for m in metrics]
        )
        families[a.parent_id] = a.family
    parents = sorted(differences)
    values = np.asarray([np.mean(differences[p], axis=0) for p in parents])
    lower, upper = _bootstrap(values, [families[p] for p in parents], key)
    return {
        "left": left,
        "right": right,
        "n_parents": len(parents),
        "n_paired_decisions": len(common),
        "complete_pairing": len(common) == len(sides[left]) == len(sides[right]),
        "left_only_decisions": len(sides[left]) - len(common),
        "right_only_decisions": len(sides[right]) - len(common),
        "parent_ids": parents,
        "metrics": {
            metric: {
                "mean": float(values[:, i].mean()),
                "ci": [float(lower[i]), float(upper[i])],
            }
            for i, metric in enumerate(metrics)
        },
    }


def _primary(rows: list[Measurement]) -> dict:
    selected = [
        r for r in rows if r.regime in PRIMARY_REGIMES and r.budget in (1, 2, 3)
    ]
    effect = _paired(selected, "M3", "M1", "primary")
    unsafe = [
        r
        for r in rows
        if r.regime in ACCURATE_REGIMES and r.false_current_permission > 0
    ]
    if effect is None:
        return {
            "meaningful_advantage": False,
            "reason": "No paired M3/M1 primary cases",
            "accurate_sensor_false_permission_decisions": len(unsafe),
        }
    goal = effect["metrics"]["goal_completion"]
    queries = effect["metrics"]["query_count"]
    route_a = goal["mean"] >= 0.05 and goal["ci"][0] > 0 and queries["mean"] <= 0
    route_b = (
        queries["mean"] <= -0.5 and queries["ci"][1] < 0 and goal["ci"][0] >= -0.01
    )
    families = sorted({r.family for r in selected})
    family_effects = {
        family: _paired(
            [r for r in selected if r.family == family], "M3", "M1", f"primary:{family}"
        )
        for family in families
    }
    expected_cells = {
        (regime, budget) for regime in PRIMARY_REGIMES for budget in (1, 2, 3)
    }
    coverage = defaultdict(set)
    for row in selected:
        if row.method in {"M1", "M3"}:
            coverage[(row.parent_id, row.method)].add((row.regime, row.budget))
    complete_grid = bool(coverage) and all(
        cells == expected_cells for cells in coverage.values()
    )
    represented_families = sum(value is not None for value in family_effects.values())
    eligible = (
        effect["complete_pairing"]
        and complete_grid
        and represented_families >= 2
        and not unsafe
    )
    return {
        "effect": effect,
        "family_effects": family_effects,
        "accurate_sensor_false_permission_decisions": len(unsafe),
        "accurate_sensor_false_permission_by_method": dict(
            Counter(r.method for r in unsafe)
        ),
        "route_a": route_a,
        "route_b": route_b,
        "complete_pairing": effect["complete_pairing"],
        "complete_primary_cell_grid": complete_grid,
        "both_families_represented": represented_families >= 2,
        "meaningful_advantage": bool(eligible and (route_a or route_b)),
        "interpretation": "Pilot decision gate; no publication novelty or powered safety noninferiority claim",
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plots(output: Path, groups: list[dict]) -> dict:
    points = []
    for group in groups:
        if group["family"] != "pooled" or group["method"] == "M4":
            continue
        metrics = group["metrics"]
        points.append(
            {key: group[key] for key in ("method", "regime", "budget")}
            | {
                "mean_queries": metrics["query_count"]["mean"],
                "valid_continuation": metrics["valid_continuation"]["mean"],
                "goal_completion": metrics["goal_completion"]["mean"],
                "incorrect_permission": metrics["false_current_permission"]["mean"],
                "simulated_cost": metrics["simulated_cost"]["mean"],
            }
        )
    _write_csv(output / "frontier_inputs.csv", points)
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except ImportError:
        # Retain a standalone vector artifact even when the historical environment
        # lacks plotting dependencies; no installation is justified for a figure.
        circles = "".join(
            f'<circle cx="{50 + 125 * p["mean_queries"]:.2f}" cy="{350 - 300 * p["valid_continuation"]:.2f}" r="3"><title>{escape(p["method"])} {escape(p["regime"])} B={p["budget"]}</title></circle>'
            for p in points
        )
        (output / "cost_validity_frontier.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="410"><rect width="100%" height="100%" fill="white"/><path d="M50 50V350H470" fill="none" stroke="black"/><text x="140" y="390">Additional symbolic queries (0–3)</text><text x="55" y="25">Valid continuation rate (0–1)</text>'
            + circles
            + "</svg>"
        )
        return {"backend": "standalone SVG fallback", "pdf": False}
    regimes = sorted({p["regime"] for p in points})
    figure, axes = plt.subplots(
        max(1, math.ceil(len(regimes) / 4)), 4, squeeze=False, figsize=(15, 7)
    )
    for axis, regime in zip(axes.flat, regimes, strict=False):
        for method in sorted({p["method"] for p in points}):
            data = sorted(
                (p for p in points if p["method"] == method and p["regime"] == regime),
                key=lambda p: p["budget"],
            )
            axis.plot(
                [p["mean_queries"] for p in data],
                [p["valid_continuation"] for p in data],
                marker="o",
                label=method,
            )
        axis.set(
            title=regime,
            xlabel="Mean extra symbolic queries",
            ylabel="Valid continuation rate",
            ylim=(-0.02, 1.02),
        )
        axis.grid(alpha=0.2)
    for axis in axes.flat[len(regimes) :]:
        axis.set_visible(False)
    if regimes:
        axes.flat[0].legend(fontsize=7)
    figure.suptitle(
        "Descriptive cost/validity points; no physical sensing latency claim"
    )
    figure.tight_layout()
    figure.savefig(output / "cost_validity_frontier.svg")
    figure.savefig(output / "cost_validity_frontier.pdf")
    plt.close(figure)
    return {"backend": "matplotlib", "pdf": True}


def analyze(split_dir: Path, output: Path) -> dict:
    """Write complete denominators, paired cluster intervals and the locked gate."""
    source = split_dir / "decisions.jsonl.gz"
    rows, skipped = _load(source)
    output.mkdir(parents=True, exist_ok=True)
    cells = sorted({(r.regime, r.budget) for r in rows})
    families = ["pooled"] + sorted({r.family for r in rows})
    groups, effects, oracle = [], [], []
    for regime, budget in cells:
        for family in families:
            selected = [
                r
                for r in rows
                if r.regime == regime
                and r.budget == budget
                and (family == "pooled" or r.family == family)
            ]
            for method in sorted({r.method for r in selected}):
                key = f"group:{family}:{regime}:{budget}:{method}"
                groups.append(
                    {
                        "family": family,
                        "regime": regime,
                        "budget": budget,
                        "method": method,
                    }
                    | _stats([r for r in selected if r.method == method], key)
                )
            pair = _paired(selected, "M3", "M1", f"effect:{family}:{regime}:{budget}")
            if pair:
                effects.append(
                    {"family": family, "regime": regime, "budget": budget} | pair
                )
            oracle_episodes = {
                r.episode_id
                for r in selected
                if r.method == "M4" and r.classification_resolved is not None
            }
            matched = [
                r
                for r in selected
                if r.episode_id in oracle_episodes
                and r.classification_resolved is not None
            ]
            for method in ("M1", "M3"):
                pair = _paired(
                    matched,
                    method,
                    "M4",
                    f"oracle:{family}:{regime}:{budget}:{method}",
                    ("classification_resolved",),
                )
                if pair:
                    oracle.append(
                        {
                            "family": family,
                            "regime": regime,
                            "budget": budget,
                            "objective": "Resolved classification only; not task-success ceiling",
                        }
                        | pair
                    )
    table = []
    for group in groups:
        for metric, estimate in group["metrics"].items():
            table.append(
                {k: group[k] for k in ("family", "regime", "budget", "method")}
                | {
                    "metric": metric,
                    "mean": estimate["mean"],
                    "ci_low": estimate["ci"][0],
                    "ci_high": estimate["ci"][1],
                    "n_parents": estimate["n_parents"],
                    "n_decisions": estimate["n_decisions"],
                    "n_permissions": group["n_permissions"],
                    "zero_event_parent_upper_95": estimate.get(
                        "zero_event_parent_upper_95"
                    ),
                }
            )
    effect_table = []
    for effect in effects:
        for metric, estimate in effect["metrics"].items():
            effect_table.append(
                {k: effect[k] for k in ("family", "regime", "budget")}
                | {
                    "comparison": "M3-M1",
                    "metric": metric,
                    "mean": estimate["mean"],
                    "ci_low": estimate["ci"][0],
                    "ci_high": estimate["ci"][1],
                    "n_parents": effect["n_parents"],
                    "n_paired_decisions": effect["n_paired_decisions"],
                    "complete_pairing": effect["complete_pairing"],
                }
            )
    _write_csv(output / "full_table.csv", table)
    _write_csv(output / "paired_effects.csv", effect_table)
    summary = {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "n_evaluated_decisions": len(rows),
        "n_parents": len({r.parent_id for r in rows}),
        "skipped": skipped,
        "bootstrap": {
            "resamples": RESAMPLES,
            "seed": SEED,
            "unit": "Parent task instance; stratified by family; repeated schedules averaged first",
            "zero_width_error_intervals": "Descriptive only; exact parent zero-event bounds reported separately",
        },
        "groups": groups,
        "paired_effects": effects,
        "oracle_comparisons": oracle,
        "primary": _primary(rows),
        "plots": _plots(output, groups),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    return summary
