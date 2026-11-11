"""Freshness selection, temporal updates and actual observation fairness."""

import copy
import inspect
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import dual_rec.revalidation.methods as policies
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.semantics import Action, Lit, Model
from dual_rec.revalidation.belief import build_belief
from dual_rec.revalidation.contracts import Parameters, Reading, RevalidationContext
from dual_rec.revalidation.methods import METHODS, project_cache, run_policy


def context(
    hazard=0.30, age=1, evidence=None, known=(), cache_time=0, expiry=0, period=1
):
    pending = Action(
        name="finish", pre=(Lit(atom="p"), Lit(atom="q")), add=frozenset({"g"})
    )
    actions = (
        pending,
        Action(name="drop-p", pre=(Lit(atom="p"),), delete=frozenset({"p"})),
        Action(name="drop-q", pre=(Lit(atom="q"),), delete=frozenset({"q"})),
    )
    values = (
        {"p": True, "q": True, "g": False, "u": True} if evidence is None else evidence
    )
    return RevalidationContext(
        base=Context(
            model=Model(atoms=frozenset(values)),
            evidence=dict(values),
            plan=(pending,),
            goal=(Lit(atom="g"),),
            queries=tuple(Query(name=a, atoms=frozenset({a})) for a in sorted(values)),
            consequence={"p": 1.0, "q": 9.0},
        ),
        actions=actions,
        trusted_anchor=frozenset({"p", "q", "u"}),
        cache_observations=dict(values),
        observed_at=dict.fromkeys(values, cache_time),
        updated_at={a: 0 for action in known for a in action.add | action.delete},
        known_after_cache=known,
        pre_gap=0,
        age=age,
        cache_time=cache_time,
        parameters=Parameters(
            event_hazard=hazard,
            sensor_error=0.0,
            missing_probability=0.0,
            permission_threshold=0.95,
            periodic_interval=period,
            expiry_steps=expiry,
        ),
    )


def truthful(ctx, world):
    return lambda atom: Reading(atom=atom, value=atom in world, measured_at=ctx.age)


def test_every_method_has_same_budget_menu_and_no_oracle_context():
    ctx = context()
    initial = build_belief(ctx)
    before = copy.deepcopy(ctx.model_dump())
    for method in sorted(METHODS):
        for budget in range(4):
            result = run_policy(
                ctx, method, budget, truthful(ctx, {"p", "q", "u"}), initial
            )
            assert len(result.readings) <= budget
            assert len({r.atom for r in result.readings}) == len(result.readings)
            assert {r.atom for r in result.readings} <= {
                next(iter(q.atoms)) for q in ctx.base.queries
            }
            assert ctx.model_dump() == before
            assert initial.readings == ()
    assert list(inspect.signature(run_policy).parameters) == [
        "ctx",
        "method",
        "budget",
        "sense",
        "initial_belief",
    ]
    with pytest.raises(ValidationError):
        RevalidationContext.model_validate(ctx.model_dump() | {"oracle_state": ["p"]})


def test_consequence_changes_order_without_changing_terminal_contract():
    ctx = context()
    world = {"p", "q", "u"}
    weighted = run_policy(ctx, "SVR", 1, truthful(ctx, world))
    ablated = run_policy(ctx, "SVR_no_impact", 1, truthful(ctx, world))
    assert weighted.readings[0].atom == "q"
    assert ablated.readings[0].atom == "p"
    for method in ("B5", "SVR", "SVR_no_impact", "SVR_no_risk"):
        for budget in range(4):
            result = run_policy(ctx, method, budget, truthful(ctx, world))
            p = result.final_plan_probability
            expected = (
                "CONTINUE" if p >= 0.95 else "RECOVER" if p <= 0.05 else "ABSTAIN"
            )
            assert result.choice == expected


def test_proactive_baselines_recheck_known_facts_even_when_prior_is_certain():
    ctx = context(hazard=0.0)
    sensor = truthful(ctx, {"p", "q", "u"})
    assert not run_policy(ctx, "SVR", 3, sensor).readings
    assert not run_policy(ctx, "B5", 3, sensor).readings
    assert len(run_policy(ctx, "B4", 2, sensor).readings) == 2
    assert len(run_policy(ctx, "B2", 2, sensor).readings) == 2
    assert len(run_policy(ctx, "B3", 2, sensor).readings) == 2


def test_period_and_expiry_boundaries_are_different():
    recent = context(hazard=0.0, age=0, period=1, expiry=0)
    assert not run_policy(recent, "B2", 3, truthful(recent, {"p", "q", "u"})).readings
    assert not run_policy(recent, "B3", 3, truthful(recent, {"p", "q", "u"})).readings
    at_threshold = context(hazard=0.0, age=1, period=1, expiry=1)
    assert (
        len(
            run_policy(
                at_threshold, "B2", 3, truthful(at_threshold, {"p", "q", "u"})
            ).readings
        )
        == 2
    )
    assert not run_policy(
        at_threshold, "B3", 3, truthful(at_threshold, {"p", "q", "u"})
    ).readings


def test_known_action_update_cannot_be_overwritten_by_delayed_old_measurement():
    action = Action(name="observed-drop", pre=(Lit(atom="p"),), delete=frozenset({"p"}))
    ctx = context(hazard=0.0, age=0, known=(action,), cache_time=-1)
    assert project_cache(ctx)["p"] is False
    stale = lambda atom: Reading(atom=atom, value=True, measured_at=-1)
    result = run_policy(ctx, "B4", 1, stale)
    assert result.evidence["p"] is False
    assert result.final_plan_probability == 0.0
    assert result.choice == "RECOVER"
    assert run_policy(ctx, "B1", 0, stale).choice == "RECOVER"


def test_missing_freshness_reading_retains_old_value_without_renewing_it():
    ctx = context()
    result = run_policy(
        ctx, "B4", 1, lambda atom: Reading(atom=atom, value=None, measured_at=ctx.age)
    )
    assert result.evidence["p"] is True
    assert result.initial_plan_probability == result.final_plan_probability
    unknown = context(
        hazard=0.0, evidence={"p": None, "q": True, "g": False, "u": True}
    )
    original = run_policy(
        unknown,
        "B1",
        1,
        lambda atom: Reading(atom=atom, value=None, measured_at=unknown.age),
    )
    assert original.evidence["p"] is None
    assert original.choice == "ABSTAIN"


def test_missing_history_frame_retains_older_observed_fallback_and_timestamp():
    ctx = context(hazard=0.0, age=1)
    fallback = ctx.model_copy(
        update={
            "cache_observations": dict(ctx.cache_observations) | {"p": None},
            "observed_at": dict(ctx.observed_at) | {"p": -1},
        }
    )
    assert project_cache(fallback)["p"] is True
    assert fallback.observed_at["p"] == -1
    result = run_policy(fallback, "B1", 0, lambda _: pytest.fail("No budget"))
    assert result.choice == "CONTINUE"
    expired = run_policy(fallback, "B3", 0, lambda _: pytest.fail("No budget"))
    assert expired.evidence["p"] is None


def test_conflict_is_unknown_not_a_boolean_assertion():
    ctx = context()
    result = run_policy(
        ctx,
        "B4",
        1,
        lambda atom: Reading(atom=atom, value=True, measured_at=ctx.age, conflict=True),
    )
    assert result.evidence["p"] is None
    assert result.initial_plan_probability == result.final_plan_probability


def test_scheduler_does_not_see_hidden_state_before_first_query():
    ctx = context()
    initial = build_belief(ctx)
    first = set()
    for hypothesis in initial.hypotheses:
        world = {
            a for i, a in enumerate(initial.atoms) if hypothesis.current & (1 << i)
        }
        result = run_policy(ctx, "SVR", 1, truthful(ctx, world), initial)
        first.add(result.readings[0].atom)
    assert first == {"q"}


def test_wrong_query_atom_and_timestamp_are_rejected():
    ctx = context()
    with pytest.raises(ValueError, match="contract"):
        run_policy(
            ctx,
            "B4",
            1,
            lambda atom: Reading(atom="other", value=True, measured_at=ctx.age),
        )
    with pytest.raises(ValueError, match="contract"):
        run_policy(
            ctx, "B4", 1, lambda atom: Reading(atom=atom, value=True, measured_at=17)
        )


def large_context():
    ctx = context()
    extras = {f"f{i:02d}" for i in range(40)}
    values = dict(ctx.base.evidence) | dict.fromkeys(extras, False)
    actions = ctx.actions + tuple(
        Action(name="external-" + atom, add=frozenset({atom}))
        for atom in sorted(extras)
    )
    base = ctx.base.model_copy(
        update={
            "model": Model(atoms=frozenset(values)),
            "evidence": values,
            "queries": tuple(
                Query(name=a, atoms=frozenset({a})) for a in sorted(values)
            ),
        }
    )
    return ctx.model_copy(
        update={
            "base": base,
            "actions": actions,
            "cache_observations": values,
            "observed_at": dict.fromkeys(values, 0),
        }
    )


def test_reduced_oracle_accepts_large_irrelevant_universe_without_pruning_states():
    ctx = large_context()
    initial = build_belief(ctx)
    assert len(initial.hypotheses) > 32
    assert len(ctx.base.queries) > 8
    decision = run_policy(ctx, "B6", 1, truthful(ctx, {"p", "q", "u"}), initial)
    assert len(decision.readings) <= 1
    assert {r.atom for r in decision.readings} <= {
        "p",
        "q",
        *(f"f{i:02d}" for i in range(6)),
    }
    assert initial.readings == ()


def test_oracle_query_subset_is_fixed_and_not_refilled_after_a_read(monkeypatch):
    ctx = large_context()
    calls = []

    def choose(belief, queryatoms, budget, threshold):
        calls.append(tuple(queryatoms))
        return next((a for a in ("p", "q") if a in queryatoms), None)

    monkeypatch.setattr(policies, "select_exact_query", choose)
    decision = run_policy(ctx, "B6", 2, truthful(ctx, {"p", "q", "u"}))
    fixed = ("p", "q", *(f"f{i:02d}" for i in range(6)))
    assert calls[0] == fixed
    assert calls[1] == tuple(a for a in fixed if a != "p")
    assert "f06" not in {a for call in calls for a in call}
    assert tuple(r.atom for r in decision.readings) == ("p", "q")
