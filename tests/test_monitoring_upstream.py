import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.semantics import apply_action
from dual_rec.monitoring.upstream import (
    MANIFEST,
    SOURCE_ROOT,
    as_action,
    as_model,
    ground_actions,
    load_public_task,
    load_upstream,
    original_smoke,
)


def test_unmodified_upstream_source_and_integrity_failure(tmp_path):
    assert (
        Path(load_upstream().__file__).resolve()
        == (SOURCE_ROOT / "logiv/__init__.py").resolve()
    )
    metadata = json.loads(MANIFEST.read_text())
    for item in metadata["files"]:
        destination = tmp_path / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE_ROOT / item["path"], destination)
    target = tmp_path / "logiv/core/verification.py"
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="integrity"):
        load_upstream(tmp_path)


def test_actual_original_known_false_unknown_and_irrelevant_behavior():
    result = original_smoke()
    assert result["known_true"]["resolved"]
    assert result["known_true"]["additional_calls"] == 0
    assert result["known_false"]["resolved"]
    assert result["known_false"]["required_truth"] is False
    for name in (
        "required_unknown",
        "irrelevant_tracked_unknown",
        "irrelevant_untracked_unknown",
        "missing_overwrites_known",
        "conflicting_sensor_visual",
    ):
        assert not result[name]["resolved"], name
        assert result[name]["additional_calls"] == 3, name
        assert result[name]["executions"] == 0, name
    assert result["missing_overwrites_known"]["required_truth"] is None
    assert result["conflicting_sensor_visual"]["required_truth"] is None


def test_actual_original_action_effect_and_goal_checks():
    result = original_smoke()
    assert result["precondition_false"]["status"] == "FAIL"
    assert result["precondition_false"]["failure"] == "PRECONDITION_FAILURE"
    assert result["precondition_false"]["executions"] == 0
    assert result["effect_unknown"]["status"] == "UNRESOLVED"
    assert result["effect_unknown"]["executions"] == 1
    assert 0 not in result["effect_unknown"]["completed"]
    assert result["effect_pass"]["status"] == "PASS"
    assert result["effect_pass"]["executions"] == 1
    assert 0 in result["effect_pass"]["completed"]
    assert result["goal_false"]["status"] == "FAIL"
    assert result["goal_false"]["failure"] == "GOAL_FAILURE"
    assert result["goal_pass"]["status"] == "PASS"


@pytest.mark.parametrize("task_path", ["robotwin/move_can_pot", "bicoord/build_bridge"])
def test_public_pddl_tasks_and_conversion_preserve_transitions(task_path):
    directory = SOURCE_ROOT / "logiv/pddl" / task_path
    task = load_public_task(directory / "domain.pddl", directory / "problem.pddl")
    model = as_model(task)
    operators = ground_actions(task)
    assert task.actions
    assert operators
    assert model.atoms
    initial = frozenset(" ".join(atom) for atom in task.initial_state.facts)
    applicable = [op for op in operators if task.initial_state.holds(op.preconditions)]
    assert applicable
    for operator in applicable:
        result = frozenset(
            " ".join(atom) for atom in operator.apply(task.initial_state).facts
        )
        assert apply_action(as_action(operator), initial) == result
    with pytest.raises(ValueError, match="limit"):
        ground_actions(task, max_actions=0)
