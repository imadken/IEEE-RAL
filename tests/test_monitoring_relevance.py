import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.methods import run_method
from dual_rec.monitoring.relevance_audit import _exact_partition, audit_queries
from dual_rec.monitoring.semantics import Action, Lit, Model, relevant_atoms


def _context(atoms, constraints=(), evidence=None):
    action = Action(name="identity", pre=(Lit(atom="p"),))
    return Context(
        model=Model(atoms=frozenset(atoms), constraints=constraints),
        evidence=evidence or {},
        plan=(action,),
        goal=(Lit(atom="p"),),
        queries=(),
        consequence={"p": 1.0},
    )


def test_background_proxy_is_relevant_and_can_resolve_the_decision():
    context = _context(
        {"p", "q", "unused"},
        constraints=(
            (Lit(atom="p", positive=False), Lit(atom="q")),
            (Lit(atom="q", positive=False), Lit(atom="p")),
        ),
    )
    assert relevant_atoms(context.model, {}, context.plan, context.goal) == frozenset(
        {"p", "q"}
    )
    result = _exact_partition(context, {}, frozenset({"q"}))
    assert not result["zero_immediate_resolution_value"]
    assert result["all_answers_resolve_previously_mixed_labels"]
    irrelevant = _exact_partition(context, {}, frozenset({"unused"}))
    assert irrelevant["zero_immediate_resolution_value"]


def test_zero_immediate_value_does_not_mean_zero_joint_information_value():
    # p iff x XOR y. Either one-bit observation preserves both validity labels;
    # observing both determines p. These are logical unit cases, not benchmarks.
    clauses = (
        (Lit(atom="x"), Lit(atom="y"), Lit(atom="p", positive=False)),
        (
            Lit(atom="x", positive=False),
            Lit(atom="y", positive=False),
            Lit(atom="p", positive=False),
        ),
        (Lit(atom="x"), Lit(atom="y", positive=False), Lit(atom="p")),
        (Lit(atom="x", positive=False), Lit(atom="y"), Lit(atom="p")),
    )
    context = _context({"p", "x", "y"}, clauses)
    first = _exact_partition(context, {}, frozenset({"x"}))
    assert first["zero_immediate_resolution_value"]
    second = _exact_partition(context, {"x": True}, frozenset({"y"}))
    assert second["all_answers_resolve_previously_mixed_labels"]
    joint = _exact_partition(context, {}, frozenset({"x", "y"}))
    assert joint["all_answers_resolve_previously_mixed_labels"]
    assert relevant_atoms(context.model, {}, context.plan, context.goal) == frozenset(
        {"p", "x", "y"}
    )


def test_known_reads_have_zero_conditional_value_but_may_expose_wrong_evidence():
    context = _context({"p"}, evidence={"p": True})
    result = _exact_partition(context, {"p": True}, frozenset({"p"}))
    assert result["zero_immediate_resolution_value"]
    assert result["prior_validity_labels"] == [True]


@pytest.mark.parametrize("method", ["M1", "M3"])
def test_truthful_conjunction_requires_every_unresolved_required_query_group(method):
    context = Context(
        model=Model(
            atoms=frozenset({"p", "q", "r", "fixed", "unused"}),
            constraints=((Lit(atom="fixed"),),),
        ),
        evidence={"p": None, "q": None, "r": None, "fixed": True, "unused": None},
        plan=(
            Action(name="identity", pre=tuple(Lit(atom=a) for a in ("p", "q", "r"))),
        ),
        goal=(Lit(atom="p"),),
        queries=(
            Query(name="a", atoms=frozenset({"p"})),
            Query(name="b", atoms=frozenset({"q", "r"})),
            Query(name="c", atoms=frozenset({"unused"})),
        ),
        consequence={"p": 9.0, "q": 1.0, "r": 1.0},
    )
    menu = {query.name: query for query in context.queries}
    for budget in range(4):
        decision = run_method(
            context,
            method,
            budget,
            lambda name: {atom: True for atom in menu[name].atoms},
        )
        assert (decision.status == "VALID") == (budget >= 2)
        assert len(decision.query_names) == min(2, budget)
        assert "c" not in decision.query_names


def test_audit_reconstructs_query_evidence_and_preserves_model_relative_scope(tmp_path):
    context = _context({"p", "unused"})
    context = context.model_copy(
        update={
            "queries": (
                Query(name="u", atoms=frozenset({"unused"})),
                Query(name="p", atoms=frozenset({"p"})),
            )
        }
    )
    episode = {
        "episode_id": "unit",
        "parent_id": "unit-parent",
        "regime": "unit",
        "context": context.model_dump(mode="json"),
    }
    decision = {
        "method": "M0",
        "episode_id": "unit",
        "budget": 2,
        "decision": {
            "query_names": ["u", "p"],
            "query_atoms": [["unused"], ["p"]],
            "query_answers": [{"unused": True}, {"p": True}],
            "evidence": {"unused": True, "p": True},
        },
    }
    for name, row in (("episodes", episode), ("decisions", decision)):
        with gzip.open(tmp_path / f"{name}.jsonl.gz", "wt") as stream:
            stream.write(json.dumps(row) + "\n")
    (tmp_path / "status.json").write_text(json.dumps({"episodes": 1, "decisions": 1}))
    out = tmp_path / "audit.json"
    result = audit_queries(tmp_path, out)
    method = result["methods"]["M0"]
    assert method["query_events"] == 2
    assert method["wholly_model_structurally_irrelevant_calls"] == 1
    assert method["zero_immediate_resolution_value_calls"] == 1
    assert method["all_answers_resolve_previously_mixed_labels_calls"] == 1
    assert result["exact_sampling"]["first_events_per_method"] == 256
    with pytest.raises(FileExistsError):
        audit_queries(tmp_path, out)


def test_prefix_sampling_does_not_replace_large_events_with_later_small_ones(tmp_path):
    large = _context({"p", *(f"z{i}" for i in range(12))})
    large = large.model_copy(
        update={"queries": (Query(name="z", atoms=frozenset({"z0"})),)}
    )
    small = _context({"p"})
    small = small.model_copy(
        update={"queries": (Query(name="p", atoms=frozenset({"p"})),)}
    )
    episodes = [
        {
            "episode_id": name,
            "parent_id": "unit",
            "regime": "unit",
            "context": ctx.model_dump(mode="json"),
        }
        for name, ctx in (("large", large), ("small", small))
    ]
    rows = []
    for index in range(257):
        large_event = index < 256
        atom = "z0" if large_event else "p"
        name = "z" if large_event else "p"
        rows.append(
            {
                "episode_id": "large" if large_event else "small",
                "method": "M1",
                "budget": 1,
                "decision": {
                    "query_names": [name],
                    "query_atoms": [[atom]],
                    "query_answers": [{atom: True}],
                    "evidence": {atom: True},
                },
            }
        )
    for name, records in (("episodes", episodes), ("decisions", rows)):
        with gzip.open(tmp_path / f"{name}.jsonl.gz", "wt") as stream:
            stream.writelines(json.dumps(record) + "\n" for record in records)
    (tmp_path / "status.json").write_text(json.dumps({"episodes": 2, "decisions": 257}))
    result = audit_queries(tmp_path, tmp_path / "audit.json")["methods"]["M1"]
    assert result["exact_prefix_selected_events"] == 256
    assert result["exact_unknown_limit_skips"] == 256
    assert result["exact_examined_events"] == 0
    assert result["exact_prefix_omitted_events"] == 1
    assert result["query_events"] == 257


def test_known_measurement_revising_evidence_is_flagged_despite_conditional_label(
    tmp_path,
):
    context = _context({"p"}, evidence={"p": True})
    context = context.model_copy(
        update={"queries": (Query(name="p", atoms=frozenset({"p"})),)}
    )
    episode = {
        "episode_id": "unit",
        "parent_id": "unit",
        "regime": "stale-unit",
        "context": context.model_dump(mode="json"),
    }
    decision = {
        "episode_id": "unit",
        "method": "M0",
        "budget": 1,
        "decision": {
            "query_names": ["p"],
            "query_atoms": [["p"]],
            "query_answers": [{"p": False}],
            "evidence": {"p": False},
        },
    }
    for name, row in (("episodes", episode), ("decisions", decision)):
        with gzip.open(tmp_path / f"{name}.jsonl.gz", "wt") as stream:
            stream.write(json.dumps(row) + "\n")
    (tmp_path / "status.json").write_text(json.dumps({"episodes": 1, "decisions": 1}))
    result = audit_queries(tmp_path, tmp_path / "audit.json")["methods"]["M0"]
    assert result["wholly_model_structurally_irrelevant_calls"] == 1
    assert result["zero_immediate_resolution_value_calls"] == 1
    assert result["observed_answer_outside_prior_model_events"] == 1
    # Thus the first two labels cannot establish physical measurement futility.
