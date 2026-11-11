"""Finite event/observation posterior and exact decision-tree regression checks."""

import sys
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.contracts import Context, Query
from dual_rec.monitoring.semantics import Action, Lit, Model
from dual_rec.revalidation.belief import (
    BeliefLimit,
    Hypothesis,
    InconsistentBelief,
    OracleLimit,
    build_belief,
    reduce_belief,
    select_exact_query,
    terminal_utility,
)
from dual_rec.revalidation.contracts import Parameters, Reading, RevalidationContext


def context(
    *,
    atoms=("p", "q", "g"),
    anchor=("p",),
    actions=None,
    cache=None,
    hazard=0.2,
    error=0.0,
    pre_gap=0,
    age=1,
    cache_time=0,
    known=(),
    missing=0.1,
    delay=0,
    constraints=(),
):
    if actions is None:
        actions = (Action(name="drop-p", pre=(Lit(atom="p"),), delete={"p"}),)
    if cache is None:
        cache = {atom: atom in anchor for atom in atoms}
    plan = (Action(name="complete", pre=(Lit(atom="p"),), add={"g"}),)
    base = Context(
        model=Model(atoms=frozenset(atoms), constraints=constraints),
        evidence=dict(cache),
        plan=plan,
        goal=(Lit(atom="g"),),
        queries=tuple(Query(name=atom, atoms={atom}) for atom in atoms),
        consequence={},
    )
    return RevalidationContext(
        base=base,
        actions=tuple(actions),
        trusted_anchor=frozenset(anchor),
        cache_observations=cache,
        observed_at={atom: cache_time for atom in atoms},
        updated_at={atom: cache_time for atom in atoms},
        known_after_cache=known,
        pre_gap=pre_gap,
        age=age,
        cache_time=cache_time,
        query_delay=delay,
        parameters=Parameters(
            event_hazard=hazard,
            sensor_error=error,
            permission_threshold=0.9,
            periodic_interval=1,
            expiry_steps=1,
            missing_probability=missing,
        ),
    )


def test_event_hazard_elapsed_steps_and_reachable_source_actions():
    belief = build_belief(context(age=2))
    assert len(belief.hypotheses) == 2
    assert belief.marginal("p") == pytest.approx(0.8**2)
    assert belief.stale_risk("p", True) == pytest.approx(0.36)
    assert belief.probability(belief.plan, belief.goal) == pytest.approx(0.64)
    assert build_belief(context(hazard=0)).marginal("p") == 1
    assert build_belief(context(hazard=1)).marginal("p") == 0
    assert build_belief(context(hazard=1, age=0)).marginal("p") == 1
    assert (
        build_belief(context(anchor=(), cache={"p": False}, hazard=1)).marginal("p")
        == 0
    )


def test_uniform_operator_sampling_retains_duplicate_successor_multiplicity():
    actions = (
        Action(name="drop-one", pre=(Lit(atom="p"),), delete={"p"}),
        Action(name="drop-two", pre=(Lit(atom="p"),), delete={"p"}),
        Action(name="set-q", pre=(Lit(atom="p"),), add={"q"}),
    )
    belief = build_belief(context(actions=actions, hazard=1))
    assert len(belief.hypotheses) == 2
    assert belief.marginal("p") == pytest.approx(1 / 3)
    assert belief.marginal("q") == pytest.approx(1 / 3)


def test_known_action_updates_current_truth_and_negative_cache_timestamp():
    restore = Action(name="restore", pre=(Lit(atom="p", positive=False),), add={"p"})
    ctx = context(
        anchor=(),
        cache={"p": False},
        known=(restore,),
        actions=(restore,),
        hazard=0,
        age=0,
        cache_time=-1,
    )
    belief = build_belief(ctx)
    assert belief.marginal("p") == 1
    assert belief.stale_risk("p", True) == 0
    assert belief.predict_reading("p", -1) == 0
    assert belief.predict_reading("p", 0) == 1
    with pytest.raises(ValueError, match="distinct"):
        build_belief(ctx.model_copy(update={"cache_time": 0}))


def test_known_success_conditions_instead_of_silently_executing_false_precondition():
    drop = Action(name="drop", pre=(Lit(atom="p"),), delete={"p"})
    known = Action(name="known-success", pre=(Lit(atom="p"),), add={"q"})
    ctx = context(
        actions=(drop,),
        cache={},
        pre_gap=1,
        hazard=0.5,
        known=(known,),
        cache_time=-1,
        age=0,
    )
    belief = build_belief(ctx)
    assert len(belief.hypotheses) == 1
    assert belief.marginal("p") == belief.marginal("q") == 1


def test_cache_likelihood_and_persistent_corruption_are_jointly_tracked():
    ctx = context(pre_gap=1, hazard=0.5, error=0.1, cache={"p": True})
    belief = build_belief(ctx)
    # P(before=p | report=true)=.9; a later event removes p with chance .5.
    assert belief.marginal("p") == pytest.approx(0.45)
    assert belief.predict_reading("p", 0) == 1
    # A wrong-before report stays wrong; the resulting current-report mass is .55.
    assert belief.predict_reading("p", 1) == pytest.approx(0.55)
    reading = Reading(atom="p", value=True, measured_at=1)
    posterior = belief.condition(reading)
    assert posterior.marginal("p") == pytest.approx(9 / 11)
    assert posterior.condition(reading) is posterior
    assert belief.marginal("p") == pytest.approx(0.45)
    with pytest.raises(ValueError, match="Repeated"):
        posterior.condition(Reading(atom="p", value=False, measured_at=1))


def test_first_read_of_uncached_atom_infers_persistent_channel_bias():
    belief = build_belief(context(cache={}, hazard=0, error=0.2, age=0))
    assert belief.predict_reading("p", 0) == pytest.approx(0.8)
    wrong = Reading(atom="p", value=False, measured_at=0)
    posterior = belief.condition(wrong)
    assert posterior.marginal("p") == 1
    assert posterior.predict_reading("p", 0) == 0
    assert posterior.condition(wrong) is posterior


def test_missing_conflicting_and_delayed_observations_do_not_acquire_current_truth():
    ctx = context(age=1, delay=1)
    belief = build_belief(ctx)
    old = belief.condition(Reading(atom="p", value=True, measured_at=0))
    assert old.marginal("p") == pytest.approx(0.8)
    for reading in (
        Reading(atom="p", value=None, measured_at=1),
        Reading(atom="p", value=True, measured_at=1, conflict=True),
    ):
        unchanged = belief.condition(reading)
        assert unchanged.hypotheses == belief.hypotheses
        assert unchanged.queried_atoms == {"p"}
    with pytest.raises(ValueError, match="timestamp"):
        belief.condition(Reading(atom="p", value=True, measured_at=7))
    with pytest.raises(ValueError, match="intermediate"):
        build_belief(context(age=3, delay=1))


def test_zero_probability_evidence_and_model_mismatch_never_create_permission():
    with pytest.raises(InconsistentBelief, match="zero probability"):
        build_belief(context(hazard=0, cache={"p": False}))
    belief = build_belief(context(hazard=0))
    with pytest.raises(InconsistentBelief, match="zero probability"):
        belief.condition(Reading(atom="p", value=False, measured_at=1))
    with pytest.raises(InconsistentBelief, match="anchor"):
        build_belief(context(constraints=((Lit(atom="q"),),)))
    with pytest.raises(InconsistentBelief, match="fixed"):
        build_belief(context(hazard=1, constraints=((Lit(atom="p"),),)))


def test_log_likelihood_keeps_tiny_support_that_a_later_read_can_resurrect():
    atoms = tuple(f"p{i}" for i in range(1000)) + ("g",)
    flip_all = Action(name="all-true", add=frozenset(atoms[:-1]))
    force_first = Action(name="force-first", add={"p0"})
    ctx = context(
        atoms=atoms,
        anchor=(),
        actions=(flip_all, force_first),
        cache={atom: True for atom in atoms[:-1]},
        hazard=0.5,
        error=0.001,
        pre_gap=1,
        age=0,
        cache_time=-1,
        known=(force_first,),
    )
    # The generic helper's pending p is replaced with declared p0 here.
    base = ctx.base.model_copy(
        update={"plan": (Action(name="complete", pre=(Lit(atom="p0"),), add={"g"}),)}
    )
    ctx = ctx.model_copy(update={"base": base})
    belief = build_belief(ctx)
    assert len(belief.hypotheses) == 3
    assert any(
        h.weight == 0 and h.log_weight > float("-inf") for h in belief.hypotheses
    )
    revived = belief.condition(Reading(atom="p0", value=False, measured_at=0))
    assert len(revived.hypotheses) == 1
    assert revived.marginal("p0") == 1
    assert revived.marginal("p1") == 0
    projected = reduce_belief(belief, ("p0",))
    assert len(projected.hypotheses) == 2
    assert any(
        h.weight == 0 and h.log_weight > float("-inf") for h in projected.hypotheses
    )
    revived_projection = projected.condition(
        Reading(atom="p0", value=False, measured_at=0)
    )
    assert len(revived_projection.hypotheses) == 1
    assert revived_projection.plan_probability == revived.plan_probability == 1


def test_myopic_value_and_oracle_include_missing_outcome_and_query_cost():
    belief = build_belief(context(hazard=0.2, missing=0.25))
    assert terminal_utility(0.8, 0.9) == pytest.approx(-0.04)
    assert belief.expected_one_step_value("p", 0.9) == pytest.approx(0.58)
    assert select_exact_query(belief, ("p", "q"), 0, 0.9) is None
    assert (
        select_exact_query(belief, {"recheck": "p", "unrelated": "q"}, 1, 0.9)
        == "recheck"
    )
    missing = replace(belief, missing_probability=1)
    assert select_exact_query(missing, ("p", "q"), 3, 0.9) is None


def test_exact_two_query_decision_can_help_when_each_myopic_query_does_not():
    drop_p = Action(name="drop-p", delete={"p"})
    drop_q = Action(name="drop-q", delete={"q"})
    ctx = context(anchor=("p", "q"), actions=(drop_p, drop_q), hazard=0.8, missing=0)
    plan = (Action(name="complete", pre=(Lit(atom="p"), Lit(atom="q")), add={"g"}),)
    ctx = ctx.model_copy(update={"base": ctx.base.model_copy(update={"plan": plan})})
    belief = build_belief(ctx)
    stop = terminal_utility(belief.probability(plan, ctx.base.goal), 0.9)
    assert belief.expected_one_step_value("p", 0.9) < stop
    assert select_exact_query(belief, ("p", "q"), 1, 0.9) is None
    assert select_exact_query(belief, ("p", "q"), 2, 0.9) == "p"


def test_fast_joint_mass_values_equal_explicit_posterior_enumeration():
    actions = (
        Action(name="drop-p", pre=(Lit(atom="p"),), delete={"p"}),
        Action(name="set-p", pre=(Lit(atom="p", positive=False),), add={"p"}),
        Action(name="set-q", pre=(Lit(atom="p"),), add={"q"}),
        Action(name="drop-q", pre=(Lit(atom="q"),), delete={"q"}),
    )
    for hazard in (0, 0.2, 0.7):
        for error in (0, 0.1, 0.3):
            for cache in ({"p": True, "q": False}, {}):
                belief = build_belief(
                    context(
                        actions=actions,
                        pre_gap=1,
                        age=2,
                        hazard=hazard,
                        error=error,
                        cache=cache,
                        missing=0.25,
                    )
                )
                for threshold in (0.9, 1.0):
                    fast = belief.one_step_values(("p", "q", "g"), threshold)
                    for atom in ("p", "q", "g"):
                        true_chance = belief.predict_reading(atom, belief.query_time)
                        expected = belief.missing_probability * terminal_utility(
                            belief.probability(belief.plan, belief.goal), threshold
                        )
                        for value, chance in (
                            (True, true_chance),
                            (False, 1 - true_chance),
                        ):
                            if chance:
                                after = belief.condition(
                                    Reading(
                                        atom=atom,
                                        value=value,
                                        measured_at=belief.query_time,
                                    )
                                )
                                expected += (
                                    (1 - belief.missing_probability)
                                    * chance
                                    * terminal_utility(
                                        after.probability(after.plan, after.goal),
                                        threshold,
                                    )
                                )
                        assert fast[atom] == pytest.approx(expected - 0.01, abs=1e-12)


def test_oracle_can_improve_utility_after_crossing_practical_permission_gate():
    # The exact reference may query beyond the practical policies' confidence
    # stopping gate; it optimizes the declared utility rather than that gate.
    belief = build_belief(context(hazard=0.05, missing=0))
    assert belief.probability(belief.plan, belief.goal) > 0.9
    assert select_exact_query(belief, ("p",), 1, 0.9) == "p"


def test_certain_observation_endpoint_never_creates_a_roundoff_branch():
    belief = build_belief(context(pre_gap=1, error=0.1, age=2))
    assert belief.predict_reading("q", 2) == 0.0
    assert belief.expected_one_step_value("q", 0.9) == pytest.approx(
        terminal_utility(belief.plan_probability, 0.9) - 0.01
    )


def test_exact_caps_and_query_boundaries_are_explicit(monkeypatch):
    belief = build_belief(context())
    with pytest.raises(OracleLimit):
        select_exact_query(belief, ("p",), 4, 0.9)
    with pytest.raises(OracleLimit):
        select_exact_query(belief, {f"q{i}": "p" for i in range(9)}, 1, 0.9)
    wide = replace(
        belief,
        atoms=tuple(f"x{i}" for i in range(6)) + ("g",),
        cache=(),
        plan=(),
        goal=(Lit(atom="g"),),
        hypotheses=tuple(Hypothesis(0, state, 1 / 64) for state in range(64)),
    )
    with pytest.raises(OracleLimit, match="projected"):
        select_exact_query(wide, tuple(f"x{i}" for i in range(6)), 1, 0.9)
    with pytest.raises(ValueError, match="undeclared"):
        belief.marginal("secret")
    with pytest.raises(ValueError, match="nonnegative"):
        select_exact_query(belief, ("p",), True, 0.9)
    monkeypatch.setattr("dual_rec.revalidation.belief.MAX_HYPOTHESES", 1)
    with pytest.raises(BeliefLimit, match="truncated"):
        build_belief(context())


def test_runtime_contract_and_belief_api_have_no_evaluator_state_input():
    ctx = context()
    with pytest.raises(ValidationError):
        RevalidationContext.model_validate(ctx.model_dump() | {"oracle_state": ["p"]})
    with pytest.raises(TypeError):
        build_belief(ctx, oracle_state={"p"})
    before = ctx.model_dump()
    a, b = build_belief(ctx), build_belief(ctx)
    assert select_exact_query(a, ("p", "q"), 1, 0.9) == select_exact_query(
        b, ("p", "q"), 1, 0.9
    )
    assert ctx.model_dump() == before


def test_exact_projection_preserves_goal_probability_query_likelihood_and_posteriors():
    actions = (
        Action(name="drop-p", pre=(Lit(atom="p"),), delete={"p"}),
        Action(name="set-q", pre=(Lit(atom="p"),), add={"q"}),
        Action(name="drop-q", pre=(Lit(atom="q"),), delete={"q"}),
    )
    full = build_belief(
        context(
            actions=actions, pre_gap=1, age=2, cache={"p": True, "q": False}, error=0.15
        )
    )
    projected = reduce_belief(full, ("p", "q"))
    assert len(projected.atoms) == 3
    assert projected.plan == ()
    assert projected.plan_probability == pytest.approx(full.plan_probability)
    assert sum(h.weight for h in projected.hypotheses) == pytest.approx(1)
    for atom in ("p", "q"):
        for timestamp in (0, 2):
            assert projected.predict_reading(atom, timestamp) == pytest.approx(
                full.predict_reading(atom, timestamp)
            )
            chance = full.predict_reading(atom, timestamp)
            for value, mass in ((True, chance), (False, 1 - chance)):
                if mass:
                    reading = Reading(atom=atom, value=value, measured_at=timestamp)
                    a, b = full.condition(reading), projected.condition(reading)
                    assert b.plan_probability == pytest.approx(a.plan_probability)
                    for remaining in ("p", "q"):
                        assert b.marginal(remaining) == pytest.approx(
                            a.marginal(remaining)
                        )
    for budget in range(4):
        assert select_exact_query(
            projected, ("p", "q"), budget, 0.9
        ) == select_exact_query(full, ("p", "q"), budget, 0.9)


def test_large_full_state_is_merged_exactly_for_a_fixed_small_query_menu():
    atoms = ("p", "g") + tuple(f"x{i}" for i in range(43))
    actions = (Action(name="drop-p", delete={"p"}),) + tuple(
        Action(name=f"set-{atom}", add={atom}) for atom in atoms[2:]
    )
    full = build_belief(context(atoms=atoms, actions=actions, hazard=0.5, missing=0))
    assert len(full.hypotheses) == 45
    reduced = reduce_belief(full, ("p",))
    assert len(reduced.hypotheses) == 2
    assert reduced.plan_probability == pytest.approx(full.plan_probability)
    assert select_exact_query(full, {"inspect": "p"}, 1, 0.9) == "inspect"
    assert select_exact_query(reduced, {"inspect": "p"}, 1, 0.9) == "inspect"


def test_projected_virtual_goal_is_never_a_free_observation_channel():
    reduced = reduce_belief(build_belief(context()), ("p",))
    virtual = reduced.goal[0].atom
    assert virtual not in reduced.queryable_atoms
    with pytest.raises(ValueError, match="virtual"):
        reduced.predict_reading(virtual, reduced.age)
    with pytest.raises(ValueError, match="virtual"):
        reduced.condition(Reading(atom=virtual, value=True, measured_at=reduced.age))
    with pytest.raises(ValueError, match="virtual"):
        select_exact_query(reduced, (virtual,), 1, 0.9)
    with pytest.raises(ValueError, match="virtual"):
        reduced.expected_one_step_value(virtual, 0.9)


def test_projected_history_retains_persistent_bias_for_previously_uncached_fact():
    full = build_belief(context(cache={}, hazard=0, error=0.2, age=0))
    reading = Reading(atom="p", value=False, measured_at=0)
    left = reduce_belief(full.condition(reading), ("p",))
    right = reduce_belief(full, ("p",)).condition(reading)
    assert left.predict_reading("p", 0) == right.predict_reading("p", 0) == 0
    assert left.plan_probability == right.plan_probability == 1
    assert left.queried_atoms == right.queried_atoms == {"p"}
