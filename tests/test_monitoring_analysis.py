"""Analysis regressions for independent parents, gate integrity and rare events."""

import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.analysis import (
    PRIMARY_REGIMES,
    Measurement,
    _primary,
    analyze,
    zero_event_upper_95,
)


def record(parent, method, index=0, regime="missing10", budget=1, **changes):
    row = {
        "method": method,
        "parent_id": parent,
        "family": "blocks" if parent.startswith("b") else "logistics",
        "episode_id": f"{parent}/{index}/{regime}",
        "regime": regime,
        "budget": budget,
        "false_current_permission": 0,
        "invalid_continuation_permission": 0,
        "goal_completion": 1,
        "valid_continuation": 1,
        "abstention": 0,
        "unnecessary_abstention": 0,
        "justified_abstention": 0,
        "recovery_invoked": 0,
        "query_count": 1,
        "simulated_cost": 2,
        "decision_seconds": 0.001,
        "query_seconds": 0.0001,
        "classification_resolved": 1,
        "continuation_permitted": True,
    }
    return row | changes


def write_rows(path, rows):
    path.mkdir()
    with gzip.open(path / "decisions.jsonl.gz", "wt") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


def test_parent_clustering_not_frames_and_nonzero_rare_error_bound(tmp_path):
    rows = []
    for parent, repetitions, success in [
        ("b1", 20, 1),
        ("b2", 1, 0),
        ("l1", 20, 1),
        ("l2", 1, 0),
    ]:
        for index in range(repetitions):
            for method in ["M1", "M3", "M4"]:
                rows.append(record(parent, method, index, goal_completion=success))
    rows.append({"method": "M4", "skip_reason": "unknown limit"})
    split = tmp_path / "input"
    write_rows(split, rows)
    summary = analyze(split, tmp_path / "analysis")
    group = next(
        g for g in summary["groups"] if g["family"] == "pooled" and g["method"] == "M1"
    )
    goal = group["metrics"]["goal_completion"]
    assert goal["mean"] == 0.5  # Raw-frame average would be20/21.
    assert goal["n_parents"] == 4 and goal["n_decisions"] == 42
    assert goal["ci"][0] < goal["ci"][1]
    rare = group["metrics"]["false_current_permission"]
    assert rare["ci"] == [0, 0]  # Descriptive bootstrap only.
    assert rare["zero_event_parent_upper_95"] == pytest.approx(1 - 0.05**0.25)
    assert rare["zero_event_parent_upper_95"] > 0.5
    assert summary["skipped"] == {"M4:unknown limit": 1}
    assert not summary["primary"]["meaningful_advantage"]
    assert summary["primary"]["effect"]["metrics"]["goal_completion"] == {
        "mean": 0,
        "ci": [0, 0],
    }
    assert summary["oracle_comparisons"]
    assert all(
        list(row["metrics"]) == ["classification_resolved"]
        for row in summary["oracle_comparisons"]
    )
    for name in [
        "summary.json",
        "full_table.csv",
        "paired_effects.csv",
        "frontier_inputs.csv",
        "cost_validity_frontier.svg",
    ]:
        assert (tmp_path / "analysis" / name).stat().st_size > 0


def primary_records(improvement=0, false_permission=0):
    rows = []
    for parent in ["b1", "b2", "l1", "l2"]:
        for regime in sorted(PRIMARY_REGIMES):
            for budget in [1, 2, 3]:
                rows.append(
                    Measurement.model_validate(
                        record(
                            parent,
                            "M1",
                            regime=regime,
                            budget=budget,
                            goal_completion=1 - improvement,
                        )
                    )
                )
                rows.append(
                    Measurement.model_validate(
                        record(
                            parent,
                            "M3",
                            regime=regime,
                            budget=budget,
                            false_current_permission=false_permission,
                        )
                    )
                )
    return rows


def test_identical_methods_cannot_pass_frozen_meaningful_advantage_gate():
    result = _primary(primary_records())
    assert result["complete_pairing"] and result["both_families_represented"]
    assert not result["route_a"] and not result["route_b"]
    assert not result["meaningful_advantage"]


def test_frozen_advantage_gate_keeps_accurate_sensor_correctness_obligation():
    result = _primary(primary_records(improvement=1))
    assert result["route_a"] and result["meaningful_advantage"]
    unsafe = _primary(primary_records(improvement=1, false_permission=1))
    assert unsafe["route_a"] and not unsafe["meaningful_advantage"]
    assert unsafe["accurate_sensor_false_permission_by_method"]["M3"] == 48


def test_missing_pairs_cannot_support_a_positive_gate():
    rows = primary_records(improvement=1)
    result = _primary(rows[1:])
    assert not result["complete_pairing"]
    assert not result["meaningful_advantage"]


def test_omitting_a_primary_regime_for_both_methods_cannot_create_a_go():
    rows = [r for r in primary_records(improvement=1) if r.regime != "structured"]
    result = _primary(rows)
    assert result["complete_pairing"] and result["route_a"]
    assert not result["complete_primary_cell_grid"]
    assert not result["meaningful_advantage"]


def test_analysis_rejects_duplicate_or_nonfinite_measurements(tmp_path):
    split = tmp_path / "input"
    row = record("b1", "M1")
    write_rows(split, [row, row])
    with pytest.raises(ValueError, match="Duplicate"):
        analyze(split, tmp_path / "analysis")
    with pytest.raises(ValueError):
        Measurement.model_validate(row | {"decision_seconds": float("nan")})
    with pytest.raises(ValueError, match="positive"):
        zero_event_upper_95(0)


def test_failed_deployed_methods_cannot_be_silently_excluded(tmp_path):
    split = tmp_path / "input"
    write_rows(split, [record("b1", "M1"), {"method": "M3", "skip_reason": "failed"}])
    with pytest.raises(ValueError, match="Only bounded M4"):
        analyze(split, tmp_path / "analysis")
