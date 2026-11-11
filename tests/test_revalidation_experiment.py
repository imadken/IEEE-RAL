"""Unsafe action grants remain unsafe even when the transition guard blocks them."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.semantics import Action, Lit
from dual_rec.revalidation.experiment import action_library_digest, forward


def test_guarded_false_permission_is_counted_without_executing_action():
    action = Action(name="stack", pre=(Lit(atom="holding"),), add=frozenset({"goal"}))
    row = forward((action,), frozenset(), (Lit(atom="goal"),))
    assert row["granted_actions"] == 1
    assert row["actually_executed_actions"] == 0
    assert row["false_permissions"] == 1
    assert row["safe_task_completion"] == 0


def test_an_already_true_goal_cannot_erase_an_incorrect_permission():
    action = Action(name="unsafe", pre=(Lit(atom="p"),))
    row = forward((action,), frozenset({"goal"}), (Lit(atom="goal"),))
    assert row["actual_goal_at_end"] == 1
    assert row["false_permissions"] == 1
    assert row["actual_task_completion"] == row["safe_task_completion"] == 0


def test_later_false_precondition_keeps_full_denominators():
    first = Action(name="first", add=frozenset({"step"}))
    later = Action(name="later", pre=(Lit(atom="absent"),))
    row = forward((first, later), frozenset(), (Lit(atom="step"),))
    assert row["granted_actions"] == 2
    assert row["actually_executed_actions"] == 1
    assert row["false_permissions"] == 1
    assert row["safe_task_completion"] == 0


def test_library_digest_binds_effects_and_ignores_only_action_order():
    a = Action(name="a", add=frozenset({"p"}))
    b = Action(name="b", delete=frozenset({"p"}))
    assert action_library_digest((a, b)) == action_library_digest((b, a))
    changed = Action(name="a", add=frozenset({"q"}))
    assert action_library_digest((changed, b)) != action_library_digest((a, b))
