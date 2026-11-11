import itertools
import random
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.semantics import (
    Action,
    Lit,
    Model,
    apply_action,
    certify,
    consistent_completions,
    possible,
    regress,
    relevant_atoms,
)


def test_action_preconditions_effects_and_negative_literals():
    action = Action(
        name="move",
        pre=(Lit(atom="clear"), Lit(atom="blocked", positive=False)),
        add=frozenset({"done"}),
        delete=frozenset({"clear"}),
    )
    assert apply_action(action, frozenset({"clear"})) == frozenset({"done"})
    for state in (frozenset(), frozenset({"clear", "blocked"})):
        with pytest.raises(ValueError, match="precondition"):
            apply_action(action, state)


def test_regression_preserves_current_preconditions_and_retained_goal():
    first = Action(name="pick", pre=(Lit(atom="clear"),), add=frozenset({"held"}))
    second = Action(name="place", pre=(Lit(atom="held"),), add=frozenset({"goal"}))
    goal = (Lit(atom="goal"), Lit(atom="untouched"))
    assert set(regress((first, second), goal)) == {
        Lit(atom="clear"),
        Lit(atom="untouched"),
    }
    model = Model(atoms=frozenset({"clear", "held", "goal", "untouched", "unused"}))
    assert (
        certify(model, {"clear": True, "untouched": True}, (first, second), goal)
        == "VALID"
    )
    assert (
        certify(model, {"clear": False, "untouched": True}, (first, second), goal)
        == "INVALID"
    )
    assert certify(model, {"clear": True}, (first, second), goal) == "UNRESOLVED"


def test_unknown_irrelevant_atoms_do_not_prevent_certification():
    model = Model(atoms=frozenset({"p", "irrelevant"}))
    action = Action(name="identity", pre=(Lit(atom="p"),))
    assert certify(model, {"p": True}, (action,), (Lit(atom="p"),)) == "VALID"
    assert relevant_atoms(model, {}, (action,), (Lit(atom="p"),)) == frozenset({"p"})
    assert certify(model, {}, (action,), (Lit(atom="p"),)) == "UNRESOLVED"


def test_background_dependency_refutes_naive_plan_name_locality():
    model = Model(
        atoms=frozenset({"p", "q", "unrelated"}),
        constraints=(
            (Lit(atom="p", positive=False), Lit(atom="q")),
            (Lit(atom="q", positive=False), Lit(atom="p")),
        ),
    )
    action = Action(name="requires-p", pre=(Lit(atom="p"),))
    goal = (Lit(atom="p"),)
    assert relevant_atoms(model, {}, (action,), goal) == frozenset({"p", "q"})
    assert certify(model, {"q": True}, (action,), goal) == "VALID"
    assert certify(model, {"q": False}, (action,), goal) == "INVALID"
    # Old positive p evidence with a contradictory new q measurement is invalid
    # evidence, never a vacuous permission. Weighted repair is outside this study.
    assert certify(model, {"p": True, "q": False}, (action,), goal) == "INCONSISTENT"


def test_constraints_are_not_implicitly_post_action_invariants():
    model = Model(atoms=frozenset({"p"}), constraints=((Lit(atom="p"),),))
    action = Action(name="clear-p", delete=frozenset({"p"}))
    assert certify(model, {}, (action,), (Lit(atom="p", positive=False),)) == "VALID"


def test_empty_models_and_impossible_sequences_never_license_execution():
    impossible_model = Model(atoms=frozenset({"p"}), constraints=((),))
    assert certify(impossible_model, {}, (), ()) == "INCONSISTENT"
    assert consistent_completions(impossible_model, {}) == ()
    model = Model(atoms=frozenset({"p"}))
    action = Action(name="delete-p", delete=frozenset({"p"}))
    assert regress((action,), (Lit(atom="p"),)) is None
    assert certify(model, {}, (action,), (Lit(atom="p"),)) == "INVALID"
    assert (
        certify(model, {}, (), (Lit(atom="p"), Lit(atom="p", positive=False)))
        == "INVALID"
    )


def test_negative_goals_and_preconditions_are_checked_universally():
    model = Model(atoms=frozenset({"p", "q"}))
    action = Action(
        name="clear", pre=(Lit(atom="q", positive=False),), delete=frozenset({"p"})
    )
    assert (
        certify(model, {"q": False}, (action,), (Lit(atom="p", positive=False),))
        == "VALID"
    )
    assert (
        certify(model, {}, (action,), (Lit(atom="p", positive=False),)) == "UNRESOLVED"
    )
    assert (
        certify(model, {"q": True}, (action,), (Lit(atom="p", positive=False),))
        == "INVALID"
    )


def test_evidence_and_model_boundaries_reject_undeclared_or_nonboolean_values():
    model = Model(atoms=frozenset({"p"}))
    for evidence in ({"p": 1}, {"p": "true"}, {"missing": True}):
        with pytest.raises(ValueError):
            possible(model, evidence)
        with pytest.raises(ValueError):
            consistent_completions(model, evidence)
    with pytest.raises(ValueError):
        certify(model, {}, (), (Lit(atom="missing"),))
    with pytest.raises(ValidationError):
        Model(atoms=frozenset({"p"}), constraints=((Lit(atom="missing"),),))
    with pytest.raises(ValidationError):
        Action(name="contradiction", add=frozenset({"p"}), delete=frozenset({"p"}))
    with pytest.raises(ValidationError):
        Action(name="contradiction", pre=(Lit(atom="p"), Lit(atom="p", positive=False)))


def test_exhaustive_limit_fails_explicitly_without_truncation():
    model = Model(atoms=frozenset({"p", "q"}))
    assert len(consistent_completions(model, {})) == 4
    assert len(consistent_completions(model, {"p": False})) == 2
    assert len(consistent_completions(model, {"p": None})) == 4
    with pytest.raises(ValueError, match="limit"):
        consistent_completions(model, {}, max_unknown=1)


def test_exact_solver_matches_independent_world_and_transition_enumeration():
    rng = random.Random(9617)
    atoms = ("p", "q", "r", "s")
    for _ in range(160):
        constraints = tuple(
            tuple(
                Lit(atom=atom, positive=rng.choice((False, True)))
                for atom in rng.sample(atoms, rng.randrange(1, 4))
            )
            for _ in range(rng.randrange(5))
        )
        model = Model(atoms=frozenset(atoms), constraints=constraints)
        evidence = {atom: rng.choice((True, False, None)) for atom in atoms}
        actions = []
        for i in range(rng.randrange(4)):
            effects = rng.sample(atoms, rng.randrange(4))
            split = rng.randrange(len(effects) + 1)
            actions.append(
                Action(
                    name=f"a{i}",
                    pre=tuple(
                        Lit(atom=atom, positive=rng.choice((False, True)))
                        for atom in rng.sample(atoms, rng.randrange(4))
                    ),
                    add=frozenset(effects[:split]),
                    delete=frozenset(effects[split:]),
                )
            )
        goal = tuple(
            Lit(atom=atom, positive=rng.choice((False, True)))
            for atom in rng.sample(atoms, rng.randrange(4))
        )
        outcomes = []
        worlds = []
        # This reference does not call regress, apply_action, possible or DPLL.
        for values in itertools.product((False, True), repeat=len(atoms)):
            state = dict(zip(atoms, values))
            if any(v is not None and state[a] != v for a, v in evidence.items()):
                continue
            if not all(
                any(state[lit.atom] == lit.positive for lit in clause)
                for clause in constraints
            ):
                continue
            worlds.append(frozenset(a for a, value in state.items() if value))
            successful = True
            for action in actions:
                if not all(state[lit.atom] == lit.positive for lit in action.pre):
                    successful = False
                    break
                state.update({a: False for a in action.delete})
                state.update({a: True for a in action.add})
            outcomes.append(
                successful and all(state[lit.atom] == lit.positive for lit in goal)
            )
        expected = (
            "INCONSISTENT"
            if not outcomes
            else "VALID"
            if all(outcomes)
            else "INVALID"
            if not any(outcomes)
            else "UNRESOLVED"
        )
        assert certify(model, evidence, tuple(actions), goal) == expected
        assert set(consistent_completions(model, evidence)) == set(worlds)
        assert possible(model, evidence) == bool(worlds)
