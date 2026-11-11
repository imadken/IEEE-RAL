"""Parent-paired freshness analysis with explicit action/decision denominators."""

import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

SEED = 71603
RESAMPLES = 2000
METHODS = frozenset(
    {"B0", "B1", "B2", "B3", "B4", "B5", "B6", "SVR", "SVR_no_impact", "SVR_no_risk"}
)
METRICS = (
    "safe_task_completion",
    "actual_task_completion",
    "actual_goal_at_end",
    "unsafe_episode",
    "decision_granted",
    "execution_coverage",
    "actual_execution_coverage",
    "authorized_empty_completion",
    "false_permissions",
    "error_per_granted_action",
    "abstention",
    "unnecessary_abstention",
    "query_count",
    "granted_actions",
    "refused_actions",
    "rechecked_actions",
    "actually_executed_actions",
    "recovery_invoked",
    "recovery_certified",
    "recovery_accepted",
    "recovery_actual_success",
    "recovery_candidate_failure",
    "recovery_execution_failure",
    "decision_seconds",
    "sensor_seconds",
    "common_belief_build_seconds",
    "recovery_lookup_seconds",
    "recovery_cold_cpu_seconds",
    "utility",
    "direct_detected",
    "direct_undetected",
    "same_value_replies",
    "unrevalidated_false_claims",
    "invalidated_relevant_claims",
)
COUNTS = (
    "safe_task_completion",
    "actual_task_completion",
    "actual_goal_at_end",
    "unsafe_episode",
    "decision_granted",
    "execution_coverage",
    "authorized_empty_completion",
    "false_permissions",
    "abstention",
    "unnecessary_abstention",
    "query_count",
    "granted_actions",
    "refused_actions",
    "rechecked_actions",
    "actually_executed_actions",
    "recovery_invoked",
    "recovery_certified",
    "recovery_accepted",
    "recovery_actual_success",
    "direct_detected",
    "direct_undetected",
    "same_value_replies",
    "unrevalidated_false_claims",
    "invalidated_relevant_claims",
)


class Measurement(BaseModel):
    """Strip large trace payloads while validating every reported denominator."""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    episode_id: str
    parent_id: str
    family: str
    regime: str
    method: str
    budget: int = Field(ge=0, le=3)
    safe_task_completion: int = Field(ge=0, le=1)
    actual_task_completion: int = Field(ge=0, le=1)
    actual_goal_at_end: int = Field(ge=0, le=1)
    unsafe_episode: int = Field(ge=0, le=1)
    decision_granted: int = Field(ge=0, le=1)
    execution_coverage: int = Field(ge=0, le=1)
    authorized_empty_completion: int = Field(ge=0, le=1)
    false_permissions: int = Field(ge=0)
    abstention: int = Field(ge=0, le=1)
    unnecessary_abstention: int = Field(ge=0, le=1)
    query_count: int = Field(ge=0)
    granted_actions: int = Field(ge=0)
    refused_actions: int = Field(ge=0, le=1)
    rechecked_actions: int = Field(ge=0, le=1)
    actually_executed_actions: int = Field(ge=0)
    recovery_invoked: int = Field(ge=0, le=1)
    recovery_certified: int = Field(ge=0, le=1)
    recovery_accepted: int = Field(ge=0, le=1)
    recovery_actual_success: int = Field(ge=0, le=1)
    decision_seconds: float = Field(ge=0)
    sensor_seconds: float = Field(ge=0)
    common_belief_build_seconds: float = Field(default=0, ge=0)
    recovery_lookup_seconds: float = Field(default=0, ge=0)
    recovery_cold_cpu_seconds: float = Field(default=0, ge=0)
    utility: float
    direct_detected: int = Field(ge=0, le=1)
    direct_undetected: int = Field(ge=0, le=1)
    direct_detection_queries: int | None = Field(default=None, ge=1)
    same_value_replies: int = Field(ge=0)
    unrevalidated_false_claims: int = Field(ge=0)
    invalidated_relevant_claims: int = Field(ge=0)

    @model_validator(mode="after")
    def coherent_counts(self):
        if self.method not in METHODS:
            raise ValueError("Unregistered method")
        if self.query_count > self.budget or self.same_value_replies > self.query_count:
            raise ValueError("Observation denominator exceeds the budget")
        if (
            self.false_permissions > self.granted_actions
            or self.actually_executed_actions > self.granted_actions
        ):
            raise ValueError("Action outcome exceeds granted-action denominator")
        if self.unsafe_episode != int(self.false_permissions > 0):
            raise ValueError("Unsafe episode and incorrect permissions disagree")
        if (
            self.abstention != 1 - self.decision_granted
            or self.refused_actions != self.abstention
        ):
            raise ValueError("Grant/refusal/abstention disagree")
        if self.execution_coverage != int(self.granted_actions > 0):
            raise ValueError("Execution coverage is not granted-action coverage")
        if self.authorized_empty_completion != int(
            self.decision_granted
            and not self.granted_actions
            and self.safe_task_completion
        ):
            raise ValueError("Empty-certificate denominator disagrees")
        if not self.decision_granted and (
            self.granted_actions
            or self.actually_executed_actions
            or self.safe_task_completion
        ):
            raise ValueError("An abstention cannot execute or safely complete the task")
        if (
            self.safe_task_completion > self.actual_task_completion
            or self.safe_task_completion + self.unsafe_episode > 1
        ):
            raise ValueError("Unsafe or incomplete task reported as safe completion")
        if not (
            self.recovery_actual_success
            <= self.recovery_accepted
            <= self.recovery_certified
            <= self.recovery_invoked
        ):
            raise ValueError("Recovery success chain is inconsistent")
        if self.direct_detected + self.direct_undetected != int(
            self.invalidated_relevant_claims > 0
        ):
            raise ValueError("Detected/undetected invalidation denominator disagrees")
        if (self.direct_detection_queries is not None) != bool(self.direct_detected):
            raise ValueError("Detection delay is missing or present for the wrong case")
        if (
            self.direct_detection_queries is not None
            and self.direct_detection_queries > self.query_count
        ):
            raise ValueError("Detection delay exceeds issued queries")
        return self


def _number(row: Measurement, metric: str) -> float:
    if metric == "actual_execution_coverage":
        return float(row.actually_executed_actions > 0)
    if metric == "recovery_candidate_failure":
        return float(row.recovery_invoked - row.recovery_certified)
    if metric == "recovery_execution_failure":
        return float(row.recovery_accepted - row.recovery_actual_success)
    return float(getattr(row, metric))


def _parent_values(rows: list[Measurement]) -> tuple[list[str], list[str], np.ndarray]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.parent_id].append(row)
    parents = sorted(grouped)
    values = []
    families = []
    for parent in parents:
        cohort = grouped[parent]
        families.append(cohort[0].family)
        counts = sum(r.granted_actions for r in cohort)
        values.append(
            [
                (
                    sum(r.false_permissions for r in cohort) / counts
                    if counts
                    else math.nan
                )
                if metric == "error_per_granted_action"
                else sum(_number(r, metric) for r in cohort) / len(cohort)
                for metric in METRICS
            ]
        )
    return parents, families, np.asarray(values, dtype=float)


def _estimates(values: np.ndarray, families: list[str], key: str) -> dict:
    """Resample all parents; undefined conditional risks are never made zero."""
    seed = int.from_bytes(hashlib.sha256(f"{SEED}:{key}".encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    sums = np.zeros((RESAMPLES, len(METRICS)))
    counts = np.zeros_like(sums)
    family_array = np.asarray(families)
    for family in sorted(set(families)):
        indices = np.flatnonzero(family_array == family)
        selected = indices[
            rng.integers(0, len(indices), size=(RESAMPLES, len(indices)))
        ]
        draw = values[selected]
        sums += np.nansum(draw, axis=1)
        counts += np.isfinite(draw).sum(axis=1)
    draws = np.divide(sums, counts, out=np.full_like(sums, np.nan), where=counts > 0)
    result = {}
    for index, metric in enumerate(METRICS):
        observed = values[:, index]
        observed = observed[np.isfinite(observed)]
        resampled = draws[:, index]
        resampled = resampled[np.isfinite(resampled)]
        result[metric] = {
            "mean": float(observed.mean()) if len(observed) else None,
            "ci": [float(v) for v in np.quantile(resampled, [0.025, 0.975])]
            if len(resampled)
            else [None, None],
            "n_defined_parents": len(observed),
            "defined_bootstrap_resamples": len(resampled),
        }
    return result


def summarize(rows: list[Measurement], key: str) -> dict:
    if not rows:
        return {
            "n_parents": 0,
            "n_decisions": 0,
            "counts": {},
            "metrics": {},
            "undefined_risk_parents": [],
        }
    parents, families, values = _parent_values(rows)
    totals = {name: sum(getattr(row, name) for row in rows) for name in COUNTS}
    totals["recovery_candidate_failure"] = (
        totals["recovery_invoked"] - totals["recovery_certified"]
    )
    totals["recovery_execution_failure"] = (
        totals["recovery_accepted"] - totals["recovery_actual_success"]
    )
    totals["direct_detection_query_sum"] = sum(
        r.direct_detection_queries or 0 for r in rows
    )
    event_parents = sum(
        any(r.unsafe_episode for r in rows if r.parent_id == parent)
        for parent in parents
    )
    return {
        "n_parents": len(parents),
        "n_decisions": len(rows),
        "parent_ids": parents,
        "counts": totals,
        "metrics": _estimates(values, families, key),
        "undefined_risk_parents": [
            parent
            for parent, v in zip(
                parents, values[:, METRICS.index("error_per_granted_action")]
            )
            if not math.isfinite(v)
        ],
        "pooled_error_per_granted_action": totals["false_permissions"]
        / totals["granted_actions"]
        if totals["granted_actions"]
        else None,
        "detected_case_mean_query_delay": totals["direct_detection_query_sum"]
        / totals["direct_detected"]
        if totals["direct_detected"]
        else None,
        "unsafe_event_parents": event_parents,
        "zero_event_parent_upper_95": 1 - 0.05 ** (1 / len(parents))
        if event_parents == 0
        else None,
        "risk_scope": "Mean parent conditional action-error ratio; zero-grant parents undefined. Pooled ratio also shown. Zero-width error bootstraps are descriptive, not powered safety noninferiority.",
    }


def paired(rows: list[Measurement], left: str, right: str, key: str) -> dict | None:
    sides = {
        method: {(r.episode_id, r.budget): r for r in rows if r.method == method}
        for method in (left, right)
    }
    common = sorted(sides[left].keys() & sides[right].keys())
    if not common:
        return None
    cohorts = [[sides[method][item] for item in common] for method in (left, right)]
    for a, b in zip(*cohorts):
        if (a.parent_id, a.family, a.regime) != (b.parent_id, b.family, b.regime):
            raise ValueError("Paired episode metadata disagree")
    parents, families, a = _parent_values(cohorts[0])
    b_parents, b_families, b = _parent_values(cohorts[1])
    if (parents, families) != (b_parents, b_families):
        raise ValueError("Paired parent metadata disagree")
    return {
        "left": left,
        "right": right,
        "n_parents": len(parents),
        "n_pairs": len(common),
        "complete_pairing": len(common) == len(sides[left]) == len(sides[right]),
        "left_only": len(sides[left]) - len(common),
        "right_only": len(sides[right]) - len(common),
        "parent_ids": parents,
        "metrics": _estimates(a - b, families, key),
        "left_counts": {
            name: sum(getattr(r, name) for r in cohorts[0]) for name in COUNTS
        },
        "right_counts": {
            name: sum(getattr(r, name) for r in cohorts[1]) for name in COUNTS
        },
        "baseline_error_per_attempt": float(
            np.mean(b[:, METRICS.index("unsafe_episode")])
        ),
        "baseline_coverage": float(np.mean(b[:, METRICS.index("execution_coverage")])),
    }


def _nonpositive(estimate: dict) -> bool:
    return estimate["mean"] is not None and estimate["mean"] <= 1e-12


def _screen(effect: dict | None, domains: dict, complete_grid: bool) -> dict:
    if effect is None:
        return {
            "meaningful_advantage": False,
            "reason": "No paired primary outcomes",
            "exploratory": True,
        }
    metrics = effect["metrics"]
    goal, error, risk, coverage, query = (
        metrics[k]
        for k in (
            "safe_task_completion",
            "unsafe_episode",
            "error_per_granted_action",
            "execution_coverage",
            "query_count",
        )
    )
    n = effect["n_parents"]
    defined = risk["n_defined_parents"] == n
    common_guards = (
        complete_grid
        and effect["complete_pairing"]
        and n >= 20
        and len(domains) >= 2
        and defined
    )
    cost_guard = query["mean"] <= 0.05 + 1e-12
    risk_guard = _nonpositive(error) and _nonpositive(risk)
    direction_ok = all(
        d is not None
        and _nonpositive(d["metrics"]["unsafe_episode"])
        and _nonpositive(d["metrics"]["error_per_granted_action"])
        and d["metrics"]["safe_task_completion"]["mean"] >= -1e-12
        and d["metrics"]["query_count"]["mean"] <= 0.05 + 1e-12
        for d in domains.values()
    )
    route_a = (
        goal["mean"] >= 0.05 - 1e-12 and goal["ci"][0] > 0 and cost_guard and risk_guard
    )
    baseline = effect["baseline_error_per_attempt"]
    relative = -error["mean"] / baseline if baseline > 0 else None
    route_b = (
        relative is not None
        and relative >= 0.20 - 1e-12
        and error["ci"][1] < 0
        and abs(coverage["mean"]) <= 0.05 + 1e-12
        and cost_guard
        and risk_guard
    )
    return {
        "meaningful_advantage": bool(
            common_guards and direction_ok and (route_a or route_b)
        ),
        "route_a_observed": bool(route_a),
        "route_b_observed": bool(route_b),
        "complete_primary_grid": complete_grid,
        "complete_pairing": effect["complete_pairing"],
        "both_domains_consistent": direction_ok,
        "all_parent_risks_defined": defined,
        "relative_per_attempt_error_reduction": relative,
        "exploratory": n < 20,
        "powered_safety_noninferiority_established": False,
        "unsafe_difference_interval_allows_increase": error["ci"][1] > 0,
        "grant_risk_difference_interval_allows_increase": risk["ci"][1] is None
        or risk["ci"][1] > 0,
        "interpretation": "Preregistered pilot screening only; selection-conditioned grant risks and sparse errors do not establish publication-level safety.",
    }


def _calibration_update(store: dict, raw: dict) -> None:
    if raw["method"] != "SVR" or raw["budget"] != 0:
        return
    pairs = raw.get("calibration_pairs", [])
    if len(pairs) != raw.get("calibration_n", len(pairs)):
        raise ValueError("Calibration denominator mismatch")
    sse = 0.0
    for probability, outcome in pairs:
        if (
            not math.isfinite(probability)
            or not 0 <= probability <= 1
            or outcome not in (0, 1)
        ):
            raise ValueError("Invalid calibration pair")
        sse += (probability - outcome) ** 2
        index = min(9, int(probability * 10))
        cell = store[raw["regime"]]["bins"][index]
        cell["count"] += 1
        cell["prediction_sum"] += probability
        cell["outcome_sum"] += outcome
    if not math.isclose(
        sse, raw.get("calibration_squared_error_sum", sse), rel_tol=1e-9, abs_tol=1e-9
    ):
        raise ValueError("Calibration squared-error sum mismatch")
    group = store[raw["regime"]]
    group["n"] += len(pairs)
    group["squared_error_sum"] += sse
    group["episodes"] += 1


def _load(split_dir: Path):
    episodes = {}
    with gzip.open(split_dir / "episodes.jsonl.gz", "rt") as stream:
        for line in stream:
            episode = json.loads(line)
            key = episode["episode_id"]
            if key in episodes:
                raise ValueError("Duplicate episode")
            episodes[key] = {
                name: episode[name]
                for name in ("episode_id", "parent_id", "family", "regime")
            }
            episodes[key]["split"] = episode.get("split")
    rows, skips, seen = [], [], set()
    calibration = defaultdict(
        lambda: {
            "n": 0,
            "squared_error_sum": 0.0,
            "episodes": 0,
            "bins": [
                {"count": 0, "prediction_sum": 0.0, "outcome_sum": 0} for _ in range(10)
            ],
        }
    )
    with gzip.open(split_dir / "decisions.jsonl.gz", "rt") as stream:
        for line in stream:
            raw = json.loads(line)
            key = raw["episode_id"], raw["method"], raw["budget"]
            if key in seen:
                raise ValueError("Duplicate decision")
            seen.add(key)
            meta = episodes.get(raw["episode_id"])
            if meta is None or any(
                raw[k] != meta[k] for k in ("parent_id", "family", "regime")
            ):
                raise ValueError("Decision/episode metadata disagree")
            if raw.get("skip_reason"):
                if raw["method"] != "B6":
                    raise ValueError("Only bounded B6 reference exclusions are allowed")
                skips.append(
                    {
                        k: raw[k]
                        for k in (
                            "episode_id",
                            "parent_id",
                            "family",
                            "regime",
                            "method",
                            "budget",
                            "skip_reason",
                        )
                    }
                )
                continue
            repair = raw.get("recovery", {})
            raw["recovery_lookup_seconds"] = repair.get("lookup_seconds", 0)
            raw["recovery_cold_cpu_seconds"] = (
                repair.get("cpu_seconds", 0) if not repair.get("cache_hit", True) else 0
            )
            rows.append(Measurement.model_validate(raw))
            _calibration_update(calibration, raw)
    family_by_parent = {}
    for row in rows:
        if family_by_parent.setdefault(row.parent_id, row.family) != row.family:
            raise ValueError("Parent occurs in multiple domain families")
    for group in calibration.values():
        group["brier"] = group["squared_error_sum"] / group["n"] if group["n"] else None
        for cell in group["bins"]:
            count = cell["count"]
            cell["mean_prediction"] = cell["prediction_sum"] / count if count else None
            cell["observed_error_frequency"] = (
                cell["outcome_sum"] / count if count else None
            )
    return rows, skips, episodes, dict(calibration)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plots(output: Path, groups: list[dict]) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pooled = [g for g in groups if g["family"] == "pooled" and g["n_decisions"]]
    regimes = sorted({g["regime"] for g in pooled})
    methods = sorted({g["method"] for g in pooled})
    colors = {method: f"C{index % 10}" for index, method in enumerate(methods)}
    if not regimes:
        return {}
    inputs = []
    for group in pooled:
        metrics = group["metrics"]
        inputs.append(
            {
                k: group[k]
                for k in ("regime", "budget", "method", "n_parents", "n_decisions")
            }
            | {
                "coverage": metrics["execution_coverage"]["mean"],
                "risk_per_granted_action": metrics["error_per_granted_action"]["mean"],
                "safe_completion": metrics["safe_task_completion"]["mean"],
                "queries": metrics["query_count"]["mean"],
            }
        )
    _write_csv(output / "frontier_inputs.csv", inputs)
    files = []
    for kind, xmetric, ymetric, xlabel, ylabel in (
        (
            "risk_coverage_frontier",
            "execution_coverage",
            "error_per_granted_action",
            "Execution coverage (at least one action granted)",
            "Incorrect permissions / granted action",
        ),
        (
            "safe_completion_query_frontier",
            "query_count",
            "safe_task_completion",
            "Mean additional symbolic queries",
            "Safe task completion / attempted episode",
        ),
    ):
        columns = min(4, len(regimes))
        lines = math.ceil(len(regimes) / columns)
        figure, axes = plt.subplots(
            lines, columns, figsize=(4 * columns, 3.5 * lines), squeeze=False
        )
        for axis, regime in zip(axes.flat, regimes):
            for method in methods:
                cells = sorted(
                    [
                        g
                        for g in pooled
                        if g["regime"] == regime and g["method"] == method
                    ],
                    key=lambda g: g["budget"],
                )
                points = [
                    (g["metrics"][xmetric]["mean"], g["metrics"][ymetric]["mean"])
                    for g in cells
                ]
                points = [(x, y) for x, y in points if x is not None and y is not None]
                if points:
                    axis.plot(
                        [p[0] for p in points],
                        [p[1] for p in points],
                        marker="o",
                        markersize=3,
                        label=method,
                        color=colors[method],
                    )
            axis.set(title=regime, xlabel=xlabel, ylabel=ylabel)
            axis.grid(alpha=0.25)
            if xmetric == "execution_coverage":
                axis.set_xlim(-0.02, 1.02)
            axis.set_ylim(bottom=-0.005)
        for axis in list(axes.flat)[len(regimes) :]:
            axis.set_visible(False)
        legend = {}
        for axis in axes.flat:
            handles, labels = axis.get_legend_handles_labels()
            legend.update(zip(labels, handles))
        labels = sorted(legend)
        if labels:
            figure.legend(
                [legend[label] for label in labels],
                labels,
                loc="upper center",
                ncol=min(10, len(labels)),
                fontsize=8,
            )
        figure.suptitle(
            "Paired task-instance means; points are budgets 0–3; symbolic sensing cost",
            y=1.01,
        )
        figure.tight_layout(rect=(0, 0, 1, 0.94))
        for extension in ("svg", "pdf"):
            name = kind + "." + extension
            figure.savefig(output / name, bbox_inches="tight")
            files.append(name)
        plt.close(figure)
    return {
        "files": files,
        "undefined_risk": "Zero-grant parent ratios are not plotted as zero; see full table and counts",
        "cost_inputs": "frontier_inputs.csv",
    }


def analyze(split_dir: Path, output: Path, primary_baseline: str) -> dict:
    if primary_baseline not in {"B2", "B3", "B4", "B5"}:
        raise ValueError("Primary baseline must be a practical B2–B5 comparator")
    if output.exists():
        raise FileExistsError("Never overwrite an analysis attempt")
    output.mkdir(parents=True)
    rows, skips, episodes, calibration = _load(split_dir)
    if not rows:
        raise ValueError("No evaluated records")
    selection_file = split_dir.parent / "selection.json"
    if selection_file.exists():
        selection = json.loads(selection_file.read_text())
        if selection.get("primary_baseline") != primary_baseline:
            raise ValueError(
                "Primary comparator differs from frozen development selection"
            )
    elif any(meta.get("split") == "qualification" for meta in episodes.values()):
        raise ValueError("Qualification analysis requires the frozen selection file")
    status_path = split_dir / "status.json"
    if not status_path.is_file():
        raise ValueError("Completed split status is missing")
    if status_path.exists():
        status = json.loads(status_path.read_text())
        if status.get("rows", len(rows) + len(skips)) != len(rows) + len(skips):
            raise ValueError("Completed row denominator mismatch")
        if status.get("episodes", len(episodes)) != len(episodes):
            raise ValueError("Completed episode denominator mismatch")
        if status.get("evaluated", len(rows)) != len(rows):
            raise ValueError("Evaluated-row denominator mismatch")
        if status.get("methods") and status.get("budgets"):
            methods, budgets = status["methods"], status["budgets"]
            if len(set(methods)) != len(methods) or len(set(budgets)) != len(budgets):
                raise ValueError("Duplicate completed method/budget declaration")
            if len(rows) + len(skips) != len(episodes) * len(methods) * len(budgets):
                raise ValueError("Incomplete completed decision grid")
            if any(
                row.method not in methods or row.budget not in budgets for row in rows
            ) or any(
                row["method"] not in methods or row["budget"] not in budgets
                for row in skips
            ):
                raise ValueError("Decision outside completed method/budget declaration")
    grouped = defaultdict(list)
    for row in rows:
        for family in ("pooled", row.family):
            grouped[family, row.regime, row.budget, row.method].append(row)
    groups = []
    for (family, regime, budget, method), cohort in sorted(grouped.items()):
        groups.append(
            {"family": family, "regime": regime, "budget": budget, "method": method}
            | summarize(cohort, f"group:{family}:{regime}:{budget}:{method}")
        )
    primary_rows = [r for r in rows if r.regime == "hidden_nominal" and r.budget == 2]
    effect = paired(primary_rows, "SVR", primary_baseline, "primary")
    families = sorted({r.family for r in primary_rows})
    domains = {
        family: paired(
            [r for r in primary_rows if r.family == family],
            "SVR",
            primary_baseline,
            "primary:" + family,
        )
        for family in families
    }
    expected = {eid for eid, e in episodes.items() if e["regime"] == "hidden_nominal"}
    present = {
        method: {r.episode_id for r in primary_rows if r.method == method}
        for method in ("SVR", primary_baseline)
    }
    complete = all(present[method] == expected for method in present) and bool(expected)
    comparisons = []
    for family in ["pooled", *sorted({r.family for r in rows})]:
        for regime in sorted({r.regime for r in rows}):
            for budget in sorted({r.budget for r in rows}):
                subset = [
                    r
                    for r in rows
                    if r.regime == regime
                    and r.budget == budget
                    and (family == "pooled" or r.family == family)
                ]
                for baseline in (
                    "B0",
                    "B1",
                    "B2",
                    "B3",
                    "B4",
                    "B5",
                    "SVR_no_impact",
                    "SVR_no_risk",
                ):
                    comparison = paired(
                        subset,
                        "SVR",
                        baseline,
                        f"paired:{family}:{regime}:{budget}:{baseline}",
                    )
                    if comparison:
                        comparisons.append(
                            {
                                "family": family,
                                "regime": regime,
                                "budget": budget,
                                "baseline": baseline,
                            }
                            | comparison
                        )
    table = []
    for group in groups:
        for metric, estimate in group["metrics"].items():
            table.append(
                {
                    k: group[k]
                    for k in (
                        "family",
                        "regime",
                        "budget",
                        "method",
                        "n_parents",
                        "n_decisions",
                    )
                }
                | {
                    "metric": metric,
                    "mean": estimate["mean"],
                    "ci_low": estimate["ci"][0],
                    "ci_high": estimate["ci"][1],
                    "defined_parents": estimate["n_defined_parents"],
                    "granted_actions_total": group["counts"]["granted_actions"],
                    "incorrect_permissions_total": group["counts"]["false_permissions"],
                }
            )
    effects_table = []
    for comparison in comparisons:
        for metric, estimate in comparison["metrics"].items():
            effects_table.append(
                {
                    k: comparison[k]
                    for k in (
                        "family",
                        "regime",
                        "budget",
                        "baseline",
                        "n_parents",
                        "n_pairs",
                    )
                }
                | {
                    "metric": metric,
                    "difference": estimate["mean"],
                    "ci_low": estimate["ci"][0],
                    "ci_high": estimate["ci"][1],
                    "defined_parents": estimate["n_defined_parents"],
                    "complete_pairing": comparison["complete_pairing"],
                }
            )
    _write_csv(output / "full_table.csv", table)
    _write_csv(output / "paired_effects.csv", effects_table)
    _write_csv(
        output / "denominators.csv",
        [
            {
                k: group[k]
                for k in (
                    "family",
                    "regime",
                    "budget",
                    "method",
                    "n_parents",
                    "n_decisions",
                )
            }
            | group["counts"]
            | {
                "risk_defined_parents": group["metrics"]["error_per_granted_action"][
                    "n_defined_parents"
                ],
                "pooled_error_per_granted_action": group[
                    "pooled_error_per_granted_action"
                ],
                "detected_case_mean_query_delay": group[
                    "detected_case_mean_query_delay"
                ],
            }
            for group in groups
        ],
    )
    exclusion_counts = Counter(
        (family, row["regime"], row["budget"], row["skip_reason"])
        for row in skips
        for family in ("pooled", row["family"])
    )
    exclusions = [
        {
            "family": family,
            "regime": regime,
            "budget": budget,
            "method": "B6",
            "reason": reason,
            "excluded_rows": count,
        }
        for (family, regime, budget, reason), count in sorted(exclusion_counts.items())
    ]
    _write_csv(output / "reference_exclusions.csv", exclusions)
    result = {
        "primary_baseline": primary_baseline,
        "evaluated_rows": len(rows),
        "reference_skip_rows": len(skips),
        "reference_skip_reasons": dict(Counter(r["skip_reason"] for r in skips)),
        "reference_exclusions": exclusions,
        "episodes": len(episodes),
        "parents": len({r.parent_id for r in rows}),
        "exploratory": len({r.parent_id for r in rows}) < 20,
        "primary": {
            "effect": effect,
            "domains": domains,
            **_screen(effect, domains, complete),
        },
        "groups": groups,
        "comparisons": comparisons,
        "calibration": calibration,
        "calibration_scope": "One shared initial-risk vector per episode, from SVR budget0; no fitting or duplicate method/budget counts",
        "detection_scope": "Fresh correct re-observation of an evaluator-identified wrong cached relevant claim; undetected cases retained. A nonmissing but biased reading may leave a claim wrong even after querying it.",
        "selection_sha256": hashlib.sha256(selection_file.read_bytes()).hexdigest()
        if selection_file.exists()
        else None,
        "bootstrap": {
            "seed": SEED,
            "resamples": RESAMPLES,
            "unit": "Parent task; family-stratified; repeated histories averaged before inference",
        },
        "plots": _plots(output, groups),
        "source_sha256": {
            name: hashlib.sha256((split_dir / name).read_bytes()).hexdigest()
            for name in ("episodes.jsonl.gz", "decisions.jsonl.gz")
        },
        "limitations": [
            "Grant-conditional ratios use selected outcomes, not causal comparisons",
            "Zero event bounds concern independent event-bearing parents, not physical per-action safety",
            "Descriptive strata beyond the frozen primary comparison are not multiplicity-adjusted",
        ],
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    return result
