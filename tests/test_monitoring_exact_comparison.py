"""Exact tree expectations must match independent complete policy execution."""

import gzip
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.exact_comparison import (
    compare_context,
    expected_frozen,
    run_comparison,
)
from dual_rec.monitoring.semantics import Lit, Model


def context():
    return Context(
        model=Model(
            atoms={"p", "q", "r"},
            constraints=((Lit(atom="p", positive=False), Lit(atom="r")),),
        ),
        evidence={},
        plan=(),
        goal=(Lit(atom="p"), Lit(atom="q")),
        queries=(Query(name="a-q", atoms={"q"}), Query(name="z-p", atoms={"p"})),
        consequence={"p": 2, "q": 1},
    )


def test_hand_computed_uniform_expected_resolution_and_calls():
    case = context()
    first = expected_frozen(case, "M1")
    third = expected_frozen(case, "M3")
    assert first[0] == (Fraction(0), Fraction(0))
    assert first[1] == (Fraction(1, 2), Fraction(1))
    assert third[1] == (Fraction(2, 3), Fraction(1))
    assert first[2] == (Fraction(1), Fraction(3, 2))
    assert third[2] == (Fraction(1), Fraction(4, 3))
    result = compare_context(case, crosscheck=True)
    assert result["world_count"] == 6
    assert result["full_execution_crosscheck"]
    oracle = next(
        row for row in result["records"] if row["budget"] == 1 and row["method"] == "M4"
    )
    assert oracle["expected_resolved_classification"]["numerator"] == 2
    assert oracle["expected_resolved_classification"]["denominator"] == 3


def test_already_resolved_context_does_not_invent_observation_cost():
    case = context().model_copy(update={"evidence": {"p": False}})
    result = compare_context(case, crosscheck=True)
    assert all(
        row["expected_resolved_classification"]["value"] == 1
        for row in result["records"]
    )
    assert all(row["expected_queries"]["value"] == 0 for row in result["records"])


def test_selection_uses_record_order_and_runtime_context_not_oracle_state(tmp_path):
    development = tmp_path / "development"
    development.mkdir()
    source = development / "episodes.jsonl.gz"
    with gzip.open(source, "wt") as stream:
        for index in range(65):
            stream.write(
                json.dumps(
                    {
                        "episode_id": f"episode-{index}",
                        "parent_id": "parent",
                        "family": "blocks",
                        "regime": "complete",
                        "context": context()
                        .model_copy(update={"evidence": {"p": False}})
                        .model_dump(mode="json"),
                        "oracle_state": ["not used", index],
                    }
                )
                + "\n"
            )
    destination = tmp_path / "comparison.json"
    result = run_comparison(source, destination)
    assert result["selected_episodes"] == 64
    assert result["records"][-1]["episode_id"] == "episode-63"
    assert result["independent_complete_execution_crosschecks"] == 4
    assert not result["context_budget_cases_with_strict_gap_to_M4"]
    assert all(
        row["tied_contexts"] == 64 for row in result["M3_M1_comparison_by_budget"]
    )
    with pytest.raises(FileExistsError):
        run_comparison(source, destination)
    with pytest.raises(ValueError, match="development"):
        run_comparison(
            tmp_path / "qualification" / "episodes.jsonl.gz", tmp_path / "blocked.json"
        )
