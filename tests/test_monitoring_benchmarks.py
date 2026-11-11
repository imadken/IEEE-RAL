import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.benchmarks import (
    IPC_ROOT,
    _consequence,
    _ground_library,
    _model,
    _normalized_state,
)
from dual_rec.monitoring.semantics import apply_action, possible
from dual_rec.monitoring.upstream import as_action, ground_actions, load_public_task


@pytest.mark.parametrize("family", ["blocks-strips-typed", "logistics-strips-typed"])
def test_canonical_domain_grounding_reports_upstream_rejected_degeneracies(family):
    directory = IPC_ROOT / "ipc-2000/domains" / family
    if not directory.is_dir():
        pytest.skip("Public IPC source cache not present; bootstrap the pinned source")
    task = load_public_task(
        directory / "domain.pddl", directory / "instances/instance-1.pddl"
    )
    operators, rejected = _ground_library(task)
    with pytest.raises(ValueError):
        ground_actions(task)
    assert operators
    assert rejected
    assert all(
        row["reason"] == "upstream_rejects_inconsistent_grounded_literals"
        for row in rejected
    )
    model = _model(task, operators)
    evidence = {
        atom: atom in {" ".join(a) for a in task.initial_state.facts}
        for atom in model.atoms
    }
    assert possible(model, evidence)
    assert all(not (as_action(op).add & as_action(op).delete) for op in operators)


def test_present_support_consequence_does_not_count_future_producers_as_roots():
    from dual_rec.monitoring.upstream import SOURCE_ROOT

    path = SOURCE_ROOT / "logiv/pddl/robotwin/move_can_pot"
    task = load_public_task(path / "domain.pddl", path / "problem.pddl")
    operators, _ = _ground_library(task)
    # A public initially applicable action establishes a predicate that becomes
    # an obligation of its successor. It is not an initial-state query target.
    first = next(
        op
        for op in operators
        if op.name == "grasp-can" and task.initial_state.holds(op.preconditions)
    )
    after = first.apply(task.initial_state)
    second = next(
        op
        for op in operators
        if op.name == "lift-can" and after.holds(op.preconditions)
    )
    goal = frozenset(second.effects)
    from dataclasses import replace

    partial_task = replace(task, goal=goal)
    scores = _consequence(partial_task, task.initial_state, (first, second))
    assert not any(atom.startswith("holding-can ") for atom in scores)
    assert any(atom.startswith("empty ") for atom in scores)
    assert all(value == 3 for value in scores.values())
    goal_only = _consequence(partial_task, second.apply(after), ())
    assert all(value == 1 for value in goal_only.values())


def test_public_equality_semantics_is_materialized_before_own_execution(tmp_path):
    domain = tmp_path / "domain.pddl"
    problem = tmp_path / "problem.pddl"
    domain.write_text("""(define (domain equality-check)
      (:requirements :strips :typing :equality) (:types item)
      (:predicates (done ?x - item))
      (:action mark :parameters (?x - item ?y - item)
       :precondition (= ?x ?y) :effect (done ?x)))""")
    problem.write_text("""(define (problem equality-test) (:domain equality-check)
      (:objects a b - item) (:init) (:goal (done a)))""")
    task = load_public_task(domain, problem)
    operators, rejected = _ground_library(task)
    assert not rejected
    model = _model(task, operators)
    state = _normalized_state(task.initial_state, model)
    assert "= a a" in state
    assert "= a b" not in state
    action = next(op for op in operators if op.signature == ("mark", "a", "a"))
    assert apply_action(as_action(action), state) == _normalized_state(
        action.apply(task.initial_state), model
    )
