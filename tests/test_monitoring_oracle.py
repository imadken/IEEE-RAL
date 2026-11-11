import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.oracle import OracleLimit, evaluate_exact, select_exact
from dual_rec.monitoring.semantics import Action, Lit, Model

DEFAULT_GOAL = (Lit(atom="p"),)


def context_for(atoms, queries, *, constraints=(), plan=(), goal=DEFAULT_GOAL):
    return Context(
        model=Model(atoms=frozenset(atoms), constraints=constraints),
        evidence={},
        plan=plan,
        goal=goal,
        queries=tuple(queries),
        consequence={},
    )


def test_hand_enumerated_conjunction_and_lexical_ties():
    context = context_for(
        {"p", "q"},
        [Query(name="q", atoms={"q"}), Query(name="p", atoms={"p"})],
        goal=(Lit(atom="p"), Lit(atom="q")),
    )
    assert select_exact(context, {}, 0) is None
    one = evaluate_exact(context, {}, 1)
    assert one.first_query == "p"
    assert one.resolved_probability == 0.5
    assert one.expected_calls == 1
    two = evaluate_exact(context, {}, 2)
    assert two.first_query == "p"
    assert two.resolved_probability == 1
    assert two.expected_calls == 1.5
    assert select_exact(context, {"p": False}, 3) is None
    assert select_exact(context, {"p": True, "q": True}, 3) is None


def test_uniform_allowed_worlds_favor_early_conjunction_falsification():
    # p -> r leaves six equally likely worlds: P(p)=1/3, P(q)=1/2.
    # For p AND q, p first costs 1 + 1/3 calls; q first costs 1 + 1/2.
    context = context_for(
        {"p", "q", "r"},
        [Query(name="z-p", atoms={"p"}), Query(name="a-q", atoms={"q"})],
        constraints=((Lit(atom="p", positive=False), Lit(atom="r")),),
        goal=(Lit(atom="p"), Lit(atom="q")),
    )
    one = evaluate_exact(context, {}, 1)
    assert one.world_count == 6
    assert one.first_query == "z-p"
    assert one.resolved_probability == pytest.approx(2 / 3)
    two = evaluate_exact(context, {}, 2)
    assert two.first_query == "z-p"
    assert two.resolved_probability == 1
    assert two.expected_calls == pytest.approx(4 / 3)


def test_correlated_proxy_outside_plan_can_resolve_the_decision():
    context = context_for(
        {"p", "q", "irrelevant"},
        [
            Query(name="a-irrelevant", atoms={"irrelevant"}),
            Query(name="b-proxy", atoms={"q"}),
        ],
        constraints=(
            (Lit(atom="p", positive=False), Lit(atom="q")),
            (Lit(atom="q", positive=False), Lit(atom="p")),
        ),
        plan=(Action(name="requires-p", pre=(Lit(atom="p"),)),),
    )
    result = evaluate_exact(context, {}, 1)
    assert result.first_query == "b-proxy"
    assert result.resolved_probability == 1
    assert result.expected_calls == 1
    assert select_exact(context, {"q": True}, 1) is None


def test_two_step_tree_can_help_when_no_one_step_query_resolves_any_world():
    # p = q XOR r. Each of q and r alone leaves both p outcomes possible.
    context = context_for(
        {"p", "q", "r"},
        [Query(name="q", atoms={"q"}), Query(name="r", atoms={"r"})],
        constraints=(
            (Lit(atom="p"), Lit(atom="q"), Lit(atom="r", positive=False)),
            (Lit(atom="p"), Lit(atom="q", positive=False), Lit(atom="r")),
            (Lit(atom="p", positive=False), Lit(atom="q"), Lit(atom="r")),
            (
                Lit(atom="p", positive=False),
                Lit(atom="q", positive=False),
                Lit(atom="r", positive=False),
            ),
        ),
    )
    assert select_exact(context, {}, 1) is None
    result = evaluate_exact(context, {}, 2)
    assert result.first_query == "q"
    assert result.resolved_probability == 1
    assert result.expected_calls == 2


def test_batch_cost_budget_and_expected_call_tie_break():
    context = context_for(
        {"p", "q"},
        [
            Query(name="a-p", atoms={"p"}),
            Query(name="b-q", atoms={"q"}),
            Query(name="z-batch", atoms={"p", "q"}, cost=2),
        ],
        goal=(Lit(atom="p"), Lit(atom="q")),
    )
    assert select_exact(context, {}, 1) == "a-p"
    result = evaluate_exact(context, {}, 2)
    assert result.first_query == "z-batch"
    assert result.resolved_probability == 1
    assert result.expected_calls == 1


def test_reference_labels_execute_actions_and_check_terminal_goal():
    context = context_for(
        {"p", "q"},
        [Query(name="p", atoms={"p"}), Query(name="q", atoms={"q"})],
        plan=(
            Action(name="clear", pre=(Lit(atom="q"),), delete={"p"}),
            Action(name="restore", add={"p"}),
        ),
    )
    assert select_exact(context, {}, 1) == "q"
    assert evaluate_exact(context, {"q": True}, 0).resolved_probability == 1
    assert evaluate_exact(context, {"q": False}, 0).resolved_probability == 1
    impossible = context.model_copy(
        update={"plan": (Action(name="clear", delete={"p"}),)}
    )
    assert select_exact(impossible, {}, 3) is None
    assert evaluate_exact(impossible, {}, 3).resolved_probability == 1


def test_no_useful_or_informative_query_returns_none_without_spending_calls():
    context = context_for(
        {"p", "q"}, [Query(name="q", atoms={"q"}), Query(name="empty", atoms=set())]
    )
    result = evaluate_exact(context, {"q": True}, 3)
    assert result.first_query is None
    assert result.resolved_probability == 0
    assert result.expected_calls == 0


def test_inconsistent_evidence_and_undeclared_atoms_are_rejected():
    context = context_for(
        {"p"}, [Query(name="p", atoms={"p"})], constraints=((Lit(atom="p"),),)
    )
    with pytest.raises(ValueError, match="No consistent completion"):
        select_exact(context, {"p": False}, 1)
    with pytest.raises(ValueError, match="undeclared"):
        select_exact(context, {"missing": True}, 1)
    with pytest.raises(ValueError, match="undeclared"):
        select_exact(
            context.model_copy(update={"queries": (Query(name="bad", atoms={"x"}),)}),
            {},
            1,
        )
    with pytest.raises(ValueError, match="undeclared"):
        select_exact(context.model_copy(update={"goal": (Lit(atom="x"),)}), {}, 1)
    with pytest.raises(ValueError, match="unique"):
        select_exact(context.model_copy(update={"queries": context.queries * 2}), {}, 1)


@pytest.mark.parametrize("budget", [-1, 1.5, True])
def test_budget_type_and_sign_are_validated(budget):
    context = context_for({"p"}, [])
    with pytest.raises(ValueError, match="nonnegative integer"):
        select_exact(context, {}, budget)


def test_exact_resource_caps_raise_without_truncating():
    context = context_for({"p"}, [])
    with pytest.raises(OracleLimit, match="budget"):
        select_exact(context, {}, 4)
    large = context_for({"p"} | {f"x{i}" for i in range(12)}, [])
    with pytest.raises(OracleLimit, match="unknown"):
        select_exact(large, {}, 0)
    assert evaluate_exact(large, {"p": True}, 0).world_count == 4096
    many = context.model_copy(
        update={"queries": tuple(Query(name=str(i), atoms={"p"}) for i in range(7))}
    )
    with pytest.raises(OracleLimit, match="query-menu"):
        select_exact(many, {}, 0)


def test_selector_has_no_actual_state_input_and_does_not_mutate_evidence():
    context = context_for({"p"}, [Query(name="p", atoms={"p"})])
    evidence = {"p": None}
    before = context.model_dump(mode="json")
    assert select_exact(context, evidence, 1) == "p"
    assert evidence == {"p": None}
    assert context.model_dump(mode="json") == before
    with pytest.raises(TypeError):
        select_exact(context, evidence, 1, actual_state=frozenset({"p"}))
    with pytest.raises(ValidationError):
        Context(**context.model_dump(), actual_state=frozenset({"p"}))
