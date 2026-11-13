"""Fixed-suffix order, atomic completion and interruption handling without physics."""

import importlib
import json
import time
from pathlib import Path

import pytest


@pytest.fixture
def batch(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    return importlib.import_module("dsre_followup_batch")


def test_next_parent_follows_original_schedule_and_never_repeats_attempts(batch):
    parents = [
        {"group": "pick34", "original_index": 68},
        {"group": "push33", "original_index": 67},
        {"group": "push34", "original_index": 69},
    ]
    assert batch.next_parent(parents, {})["group"] == "push33"
    assert (
        batch.next_parent(parents, {"push33": {"status": "INTERRUPTED"}})["group"]
        == "pick34"
    )
    assert batch.next_parent(parents, {p["group"]: {} for p in parents}) is None


def test_atomic_record_is_complete_json_and_no_temporary_file(batch, tmp_path):
    path = tmp_path / "parent.json"
    batch.atomic(path, {"status": "COMPLETE", "checkpoints": ["a", "b"]})
    assert json.loads(path.read_text())["checkpoints"] == ["a", "b"]
    assert list(tmp_path.iterdir()) == [path]


def test_interruption_preserves_committed_parent_and_excludes_uncommitted(
    batch, tmp_path
):
    for name in ("chunks", "parent_attempts", "parent_progress"):
        (tmp_path / name).mkdir()
    for i in (0, 1):
        batch.atomic(
            tmp_path / "parent_attempts" / f"{i:04d}.json",
            {"group": f"parent{i}", "index": i},
        )
    complete = tmp_path / "parent_progress/0000.json"
    batch.atomic(complete, {"status": "COMPLETE", "group": "parent0"})
    previous = complete.read_bytes()
    batch.atomic(
        tmp_path / "chunks/0000_started.json",
        {"sequence": 0, "epoch": time.time() - 10},
    )
    batch.recover_interrupted(tmp_path)
    assert complete.read_bytes() == previous
    assert (
        batch.read(tmp_path / "parent_progress/0001.json")["status"]
        == "INTERRUPTED_UNCOMMITTED_PARENT"
    )
    record = batch.read(tmp_path / "chunks/0000_complete.json")
    assert (
        record["status"] == "UNEXPECTED_CHUNK_INTERRUPTION"
        and record["cpu_seconds"] is None
    )
    frozen = (tmp_path / "chunks/0000_complete.json").read_bytes()
    batch.recover_interrupted(tmp_path)
    assert (tmp_path / "chunks/0000_complete.json").read_bytes() == frozen


def test_source_change_prevents_any_resume(batch, tmp_path):
    source = tmp_path / "controller.py"
    source.write_text("original")
    batch.atomic(
        tmp_path / "confirmation_freeze.json",
        {"source_sha256": {str(source): batch.sha(source)}, "input_sha256": {}},
    )
    batch.verify_freeze(tmp_path)
    source.write_text("changed")
    with pytest.raises(ValueError, match="Frozen source"):
        batch.verify_freeze(tmp_path)


def test_decision_necessity_does_not_redefine_success(batch, monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    analysis = importlib.import_module("dsre_followup_analysis")
    record = {
        "id": "same",
        "group": "parent",
        "task": "PickCube-v1",
        "method": "DSRE",
        "initial_success": True,
        "category": "both",
        "action": "continue",
        "recommended": 1,
        "successful": 1,
        "unacceptable": 0,
        "literals": 1,
        "support_rows": 2,
        "support_parents": 2,
        "necessary_adequate_action": 0,
        "adequate_either_action": 1,
    }
    records = [record | {"budget": b} for b in (0, 1)]
    result = analysis.statistics(records, 2026111322)
    assert result["tables"]["PickCube-v1|1|DSRE|all"]["successful"] == 1
    assert result["tables"]["PickCube-v1|1|DSRE|all"]["necessary_action_successes"] == 0
    assert (
        result["decision_necessity_records"][0]["required_recovery_success_difference"]
        == 0
    )


def test_paper_rewrite_preserves_citation_keys_and_incomplete_population(
    batch, monkeypatch, tmp_path
):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    paper = importlib.import_module("dsre_followup_paper")
    root = tmp_path / "evidence"
    root.mkdir()
    batch.atomic(
        root / "suffix_results.json",
        {
            "tables": {},
            "paired_intervals": {"PickCube-v1|b1-b0|all": {"success_difference": None}},
            "decision_necessity_records": [],
            "equivalences": {},
            "assignment_counts": {
                "PickCube-v1|1|DSRE|recover": {"assigned_parents": 0}
            },
        },
    )
    batch.atomic(root / "pooled_secondary_results.json", {"tables": {}})
    batch.atomic(
        root / "followup_missingness.json",
        {
            "complete_parents": 0,
            "primary_checkpoints": 0,
            "missing_or_partial_parents": ["missing"],
        },
    )
    batch.atomic(
        root / "independent_audit.json",
        {
            "new_qualified_traces": 0,
            "prefix_states_checked": 0,
            "outcome_controls_checked": 0,
            "maximum_action_error": 0,
            "selected_outcomes_recomputed_from_raw": 0,
        },
    )
    target = tmp_path / "rss2027"
    target.mkdir()
    source = r"""\documentclass{IEEEtran}
\begin{abstract}old\end{abstract}
\section{Introduction}old
\section{Related Work}A verified citation \cite{khan2009} and label \ref{case2}.
\subsection{Frozen prospective check}old
\section{Results and Their Boundaries}old
\section{Discussion and Stage 2 Questions}old
\clearpage
\bibliography{references}
"""
    (target / "dsre_stage1.tex").write_text(source)
    monkeypatch.chdir(tmp_path)
    paper.write_paper(root)
    rendered = (target / "dsre_stage1.tex").read_text()
    assert r"\cite{khan2009}" in rendered and r"\ref{case2}" in rendered
    assert "0/333" in rendered and "incomplete" in rendered
    assert "suffix-only" in rendered and "secondary descriptive" in rendered
    assert all(line == line.rstrip() for line in rendered.splitlines())
