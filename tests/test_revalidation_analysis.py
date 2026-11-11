"""Parent-level inference, sparse grant risk and locked comparator controls."""

import gzip
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.revalidation.analysis import (
    Measurement,
    _load,
    _screen,
    analyze,
    paired,
    summarize,
)


def record(
    parent="p",
    family="blocks",
    episode=None,
    method="SVR",
    budget=2,
    safe=1,
    grants=2,
    errors=0,
    decision=1,
    queries=0,
    **extras,
):
    return {
        "episode_id": episode or parent + "/0",
        "parent_id": parent,
        "family": family,
        "regime": "hidden_nominal",
        "method": method,
        "budget": budget,
        "safe_task_completion": safe,
        "actual_task_completion": safe,
        "actual_goal_at_end": safe,
        "unsafe_episode": int(errors > 0),
        "decision_granted": decision,
        "execution_coverage": int(grants > 0),
        "authorized_empty_completion": int(decision and not grants and safe),
        "false_permissions": errors,
        "abstention": 1 - decision,
        "unnecessary_abstention": 0,
        "query_count": queries,
        "granted_actions": grants,
        "refused_actions": 1 - decision,
        "rechecked_actions": int(queries > 0),
        "actually_executed_actions": grants - errors,
        "recovery_invoked": 0,
        "recovery_certified": 0,
        "recovery_accepted": 0,
        "recovery_actual_success": 0,
        "decision_seconds": 0.001,
        "sensor_seconds": 0.0001 * queries,
        "utility": safe - 5 * int(errors > 0) - 0.01 * queries,
        "direct_detected": 0,
        "direct_undetected": 0,
        "direct_detection_queries": None,
        "same_value_replies": 0,
        "unrevalidated_false_claims": 0,
        "invalidated_relevant_claims": 0,
        **extras,
    }


def write_data(tmp_path, rows, extra_episodes=()):
    split = tmp_path / "qualification"
    split.mkdir()
    episodes = {
        r["episode_id"]: {
            k: r[k] for k in ("episode_id", "parent_id", "family", "regime")
        }
        | {"split": "qualification"}
        for r in rows
    }
    episodes.update({e["episode_id"]: e for e in extra_episodes})
    with gzip.open(split / "episodes.jsonl.gz", "wt") as stream:
        stream.writelines(json.dumps(e) + "\n" for e in episodes.values())
    with gzip.open(split / "decisions.jsonl.gz", "wt") as stream:
        stream.writelines(json.dumps(r) + "\n" for r in rows)
    (split / "status.json").write_text(
        json.dumps(
            {
                "rows": len(rows),
                "episodes": len(episodes),
                "evaluated": sum(not r.get("skip_reason") for r in rows),
            }
        )
    )
    (tmp_path / "selection.json").write_text(json.dumps({"primary_baseline": "B2"}))
    return split


def test_parent_means_do_not_count_repeated_schedules_as_independent_tasks():
    rows = [
        Measurement.model_validate(record("a", episode=f"a/{i}", safe=1))
        for i in range(100)
    ]
    rows += [Measurement.model_validate(record("b", "logistics", safe=0))]
    result = summarize(rows, "unit-parent")
    assert result["n_parents"] == 2 and result["n_decisions"] == 101
    assert result["metrics"]["safe_task_completion"]["mean"] == 0.5
    assert result["zero_event_parent_upper_95"] == pytest.approx(1 - math.sqrt(0.05))


def test_action_risk_ratio_uses_parent_total_grants_and_zero_grants_are_undefined():
    rows = [
        record("a", episode="a/0", safe=0, grants=1, errors=1),
        record("a", episode="a/1", grants=9),
        record("b", "logistics", safe=0, grants=0, decision=0),
    ]
    result = summarize([Measurement.model_validate(r) for r in rows], "unit-risk")
    risk = result["metrics"]["error_per_granted_action"]
    assert risk["mean"] == 0.1
    assert risk["n_defined_parents"] == 1
    assert result["undefined_risk_parents"] == ["b"]
    assert result["counts"]["false_permissions"] == 1
    assert result["pooled_error_per_granted_action"] == 0.1


def test_zero_action_certificate_is_not_execution_coverage():
    row = Measurement.model_validate(record(safe=1, grants=0, decision=1))
    result = summarize([row], "unit-empty")
    assert result["counts"]["authorized_empty_completion"] == 1
    assert result["metrics"]["execution_coverage"]["mean"] == 0
    assert result["metrics"]["decision_granted"]["mean"] == 1
    assert result["metrics"]["error_per_granted_action"]["mean"] is None


def test_nonfinite_duplicate_and_deployed_method_exclusions_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        Measurement.model_validate(record(decision_seconds=float("nan")))
    split = write_data(tmp_path, [record(), record()])
    with pytest.raises(ValueError, match="Duplicate decision"):
        _load(split)
    with gzip.open(split / "decisions.jsonl.gz", "wt") as stream:
        stream.write(json.dumps(record() | {"skip_reason": "budget"}) + "\n")
    with pytest.raises(ValueError, match="Only bounded B6"):
        _load(split)


def test_calibration_uses_one_initial_vector_per_episode_and_does_not_fit(tmp_path):
    pairs = [[0.1, 1], [0.9, 0]]
    rows = [
        record(
            method=m,
            budget=b,
            calibration_pairs=pairs,
            calibration_n=2,
            calibration_squared_error_sum=1.62,
        )
        for m in ("SVR", "B2")
        for b in (0, 2)
    ]
    split = write_data(tmp_path, rows)
    _, _, _, calibration = _load(split)
    group = calibration["hidden_nominal"]
    assert group["n"] == 2 and group["episodes"] == 1
    assert group["brier"] == pytest.approx(0.81)
    assert sum(bin_["count"] for bin_ in group["bins"]) == 2


def test_direct_detection_retains_undetected_denominator_and_delay(tmp_path):
    rows = [
        record(
            "a",
            queries=2,
            direct_detected=1,
            direct_detection_queries=2,
            invalidated_relevant_claims=1,
            same_value_replies=1,
        ),
        record(
            "b",
            "logistics",
            direct_undetected=1,
            invalidated_relevant_claims=2,
            unrevalidated_false_claims=2,
        ),
    ]
    stats = summarize([Measurement.model_validate(r) for r in rows], "unit-detection")
    assert stats["counts"]["direct_detected"] == 1
    assert stats["counts"]["direct_undetected"] == 1
    assert stats["detected_case_mean_query_delay"] == 2


def primary_effects(harm_logistics=False):
    rows = []
    for p in range(24):
        family = "blocks" if p < 12 else "logistics"
        for schedule in range(2):
            baseline_safe = int(schedule == 0)
            proposed_safe = (
                int(schedule == 0) if harm_logistics and family == "logistics" else 1
            )
            rows += [
                Measurement.model_validate(
                    record(str(p), family, f"{p}/{schedule}", "B2", safe=baseline_safe)
                ),
                Measurement.model_validate(
                    record(str(p), family, f"{p}/{schedule}", "SVR", safe=proposed_safe)
                ),
            ]
    effect = paired(rows, "SVR", "B2", "primary-unit")
    domains = {
        f: paired([r for r in rows if r.family == f], "SVR", "B2", f)
        for f in ("blocks", "logistics")
    }
    return effect, domains


def test_pilot_screen_cost_risk_and_completeness_guards_without_safety_overclaim():
    effect, domains = primary_effects()
    decision = _screen(effect, domains, True)
    assert decision["meaningful_advantage"]
    assert not decision["powered_safety_noninferiority_established"]
    assert not _screen(effect, domains, False)["meaningful_advantage"]
    changed = dict(effect) | {"metrics": dict(effect["metrics"])}
    changed["metrics"]["query_count"] = {"mean": 0.06, "ci": [0.06, 0.06]}
    assert not _screen(changed, domains, True)["meaningful_advantage"]
    changed["metrics"]["query_count"] = effect["metrics"]["query_count"]
    changed["metrics"]["error_per_granted_action"] = {
        "mean": None,
        "ci": [None, None],
        "n_defined_parents": 0,
    }
    assert not _screen(changed, domains, True)["meaningful_advantage"]


def test_actual_domain_harm_blocks_pooled_positive_screen():
    effect, domains = primary_effects()
    domains["logistics"]["metrics"]["safe_task_completion"] = {
        "mean": -0.01,
        "ci": [-0.01, -0.01],
    }
    assert not _screen(effect, domains, True)["meaningful_advantage"]


def test_full_analysis_artifacts_counts_and_frozen_baseline(tmp_path):
    rows = [record("a", "blocks", method=m) for m in ("SVR", "B2")]
    rows += [
        record("b", "logistics", method=m, safe=0, grants=0, decision=0)
        for m in ("SVR", "B2")
    ]
    split = write_data(tmp_path, rows)
    result = analyze(split, split / "analysis", "B2")
    assert result["parents"] == 2 and result["primary"]["exploratory"]
    assert not result["primary"]["meaningful_advantage"]
    assert (split / "analysis/full_table.csv").is_file()
    assert (split / "analysis/denominators.csv").is_file()
    assert (split / "analysis/risk_coverage_frontier.svg").is_file()
    assert (split / "analysis/risk_coverage_frontier.pdf").is_file()
    with pytest.raises(ValueError, match="frozen development selection"):
        analyze(split, split / "wrong-baseline", "B5")


def test_qualification_cannot_choose_a_comparator_without_selection(tmp_path):
    split = write_data(tmp_path, [record()])
    (tmp_path / "selection.json").unlink()
    with pytest.raises(ValueError, match="frozen selection"):
        analyze(split, split / "analysis", "B2")


def test_analysis_never_treats_unfinished_or_incomplete_grid_as_completed(tmp_path):
    split = write_data(tmp_path, [record()])
    status = split / "status.json"
    status.unlink()
    with pytest.raises(ValueError, match="Completed split status"):
        analyze(split, split / "unfinished", "B2")
    status.write_text(
        json.dumps(
            {
                "rows": 1,
                "episodes": 1,
                "evaluated": 1,
                "methods": ["SVR", "B2"],
                "budgets": [2],
            }
        )
    )
    with pytest.raises(ValueError, match="Incomplete completed decision grid"):
        analyze(split, split / "partial-grid", "B2")
