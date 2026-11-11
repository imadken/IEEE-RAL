"""Fair sensing, sound decisions and paired schedules for monitoring methods."""

import copy
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.methods import run_method
from dual_rec.monitoring.recovery import recover
from dual_rec.monitoring.semantics import Action, Lit, Model, certify


def context(evidence=None, plan=None, constraints=()):
    return Context(
        model=Model(atoms=frozenset({"p", "q", "g"}), constraints=constraints),
        evidence=evidence or {"p": True, "q": None, "g": False},
        plan=plan
        or (Action(name="achieve", pre=(Lit(atom="p"),), add=frozenset({"g"})),),
        goal=(Lit(atom="g"),),
        queries=(
            Query(name="p", atoms=frozenset({"p"})),
            Query(name="q", atoms=frozenset({"q"})),
        ),
        consequence={"p": 2.0},
        schedule_offset=1,
    )


def test_original_gate_irrelevant_unknown_and_cumulative_adapter():
    ctx = context()
    no_budget = run_method(ctx, "M0", 0, lambda _: pytest.fail("No budget"))
    assert no_budget.choice == "ABSTAIN"
    required = run_method(ctx, "M1", 0, lambda _: pytest.fail("Irrelevant reading"))
    assert required.choice == "CONTINUE"
    cumulative = run_method(ctx, "M0", 1, lambda name: {name: True})
    assert cumulative.query_names == ("q",)
    assert cumulative.choice == "CONTINUE"
    assert cumulative.evidence["p"] is True


def test_same_inputs_budgets_and_available_queries():
    ctx = context({"p": None, "q": None, "g": False})
    original = copy.deepcopy(ctx.model_dump())
    for method in ("M0", "M1", "M2", "M3", "M3_no_consequence", "M4"):
        for budget in range(4):
            calls = []

            def sensor(name, calls=calls):
                calls.append(name)
                return {name: True}

            result = run_method(ctx, method, budget, sensor)
            assert len(calls) <= budget
            assert len(set(calls)) == len(calls)
            assert set(calls) <= {q.name for q in ctx.queries}
            assert result.query_names == tuple(calls)
            assert ctx.model_dump() == original
    with pytest.raises(ValidationError):
        Context.model_validate(ctx.model_dump() | {"oracle_state": ["p"]})


def test_full_suffix_and_current_action_are_distinct_contracts():
    first = Action(name="first", pre=(Lit(atom="p"),))
    later = Action(name="later", pre=(Lit(atom="q"),), add=frozenset({"g"}))
    ctx = context({"p": True, "q": False, "g": False}, (first, later))
    baseline = run_method(ctx, "M0", 0, lambda _: {})
    exact = run_method(ctx, "M1", 0, lambda _: {})
    assert baseline.choice == "CONTINUE"
    assert baseline.status == "CURRENT_VALID"
    assert exact.choice == "RECOVER"
    assert exact.status == "INVALID"


def test_constraint_proxy_and_invalid_evidence():
    p, q = Lit(atom="p"), Lit(atom="q")
    constraints = ((p.negate(), q), (p, q.negate()))
    ctx = context({"p": None, "q": None, "g": False}, constraints=constraints)
    ctx = ctx.model_copy(update={"queries": (Query(name="q", atoms=frozenset({"q"})),)})
    result = run_method(ctx, "M1", 1, lambda _: {"q": True})
    assert result.choice == "CONTINUE"
    inconsistent = ctx.model_copy(
        update={"evidence": {"p": True, "q": False, "g": False}}
    )
    assert run_method(inconsistent, "M1", 0, lambda _: {}).status == "INCONSISTENT"


def test_common_recovery_uses_evidence_not_oracle():
    achieve = Action(name="achieve", pre=(Lit(atom="p"),), add=frozenset({"g"}))
    restore = Action(name="restore", add=frozenset({"p"}))
    ctx = context({"p": False, "q": None, "g": False}, (achieve,))
    result = recover(ctx, dict(ctx.evidence), (achieve, restore))
    assert result["success"]
    repaired = tuple(Action.model_validate(action) for action in result["plan"])
    assert certify(ctx.model, ctx.evidence, repaired, ctx.goal) == "VALID"
    blocked = recover(ctx, dict(ctx.evidence), (achieve,))
    assert not blocked["success"]


def test_sensor_cannot_change_query_contract_or_exceed_budget():
    ctx = context({"p": None, "q": None, "g": False})
    with pytest.raises(ValueError, match="response"):
        run_method(ctx, "M1", 1, lambda _: {"oracle_state": True})
    with pytest.raises(ValueError, match="Budget"):
        run_method(ctx, "M1", 4, lambda _: {})


def test_consequence_changes_only_order_and_ablation_equals_required_baseline():
    plan = (
        Action(
            name="achieve", pre=(Lit(atom="p"), Lit(atom="q")), add=frozenset({"g"})
        ),
    )
    ctx = context({"p": None, "q": None, "g": False}, plan).model_copy(
        update={"consequence": {"p": 1.0, "q": 4.0}}
    )
    sensor = lambda name: {name: False}
    simple = run_method(ctx, "M1", 1, sensor)
    selective = run_method(ctx, "M3", 1, sensor)
    ablation = run_method(ctx, "M3_no_consequence", 1, sensor)
    assert simple.query_names == ("p",)
    assert selective.query_names == ("q",)
    assert simple.query_names == ablation.query_names
    assert simple.choice == ablation.choice
    assert selective.status == "INVALID"


def test_truthful_conjunctive_valid_certification_needs_every_unknown_group():
    plan = (
        Action(
            name="achieve", pre=(Lit(atom="p"), Lit(atom="q")), add=frozenset({"g"})
        ),
    )
    ctx = context({"p": None, "q": None, "g": False}, plan).model_copy(
        update={"consequence": {"q": 4.0}}
    )
    for method in ("M1", "M3", "M3_no_consequence", "M4"):
        assert run_method(ctx, method, 1, lambda name: {name: True}).choice == "ABSTAIN"
        assert (
            run_method(ctx, method, 2, lambda name: {name: True}).choice == "CONTINUE"
        )
