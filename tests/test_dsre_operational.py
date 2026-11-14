"""Operational abstention and conservative independent-parent risk contracts."""

import pytest
from pydantic import ValidationError

from dual_rec.dsre.calibration import zero_error_required
from dual_rec.dsre.operational import (
    METHODS,
    PolicyInput,
    calibrate_records,
    gated_action,
)


def test_json_contact_normalization_preserves_recorded_prefix_semantics():
    from dual_rec.replay import jsonable
    from dual_rec.validation import compare, passes

    recorded = {
        "position": [0, 0, 0],
        "quaternion": [1, 0, 0, 0],
        "velocity": [0],
        "qpos": [0],
        "observation": {"x": [0]},
        "time": 0,
        "success": False,
        "contacts": [["cube", "table"]],
    }
    live = recorded | {"contacts": [("cube", "table")]}
    # The frozen attempted runner omits normalization. This offline regression
    # records its sufficient software defect without repeating any physics.
    assert not passes(compare(recorded, live))
    assert passes(compare(recorded, jsonable(live)))
    changed = live | {"position": [0.1, 0, 0]}
    assert not passes(compare(recorded, jsonable(changed)))


def test_future_outcomes_are_not_runtime_inputs():
    packet = {"task": "PickCube-v1", "values": (True,) * 7, "full_values": (True,) * 12}
    with pytest.raises(ValidationError):
        PolicyInput(**packet, outcomes={"recover": True})
    with pytest.raises(ValidationError, match="Shared predecision"):
        PolicyInput(**(packet | {"values": (False,) * 7}))


def test_correlated_conditions_count_once_and_any_error_marks_parent():
    rows = [
        {
            "method": "DSRE_risk",
            "task": "PickCube-v1",
            "action": "continue",
            "group": "same",
            "unacceptable": error,
        }
        for error in (0, 1)
    ]
    bound = calibrate_records(rows)["DSRE_risk|PickCube-v1|continue"]
    assert bound["assigned_parents"] == 1 and bound["error_parents"] == 1
    assert not bound["enabled"] and bound["upper"] == 1
    assert (
        gated_action(
            "DSRE_risk",
            "PickCube-v1",
            "continue",
            {"DSRE_risk|PickCube-v1|continue": bound},
        )
        is None
    )


def test_exact_zero_error_gate_respects_simultaneous_method_budget():
    required = zero_error_required(0.1, 0.05 / (4 * len(METHODS)))
    assert zero_error_required() == 42 and required > 42
    rows = [
        {
            "method": "DSRE_risk",
            "task": "PushCube-v1",
            "action": "recover",
            "group": str(i),
            "unacceptable": 0,
        }
        for i in range(required)
    ]
    enabled = calibrate_records(rows)["DSRE_risk|PushCube-v1|recover"]
    disabled = calibrate_records(rows[:-1])["DSRE_risk|PushCube-v1|recover"]
    assert enabled["enabled"] and not disabled["enabled"]
    assert not calibrate_records(rows, planned_complete=False)[
        "DSRE_risk|PushCube-v1|recover"
    ]["enabled"]


def test_empty_and_unknown_actions_never_inherit_certification():
    bounds = calibrate_records([])
    assert all(
        v["status"] == "NOT_CERTIFIED" and v["assigned_parents"] == 0
        for v in bounds.values()
    )
    assert gated_action("DSRE_risk", "PushCube-v1", None, bounds) is None
    assert gated_action("DSRE_risk", "PushCube-v1", "recover", {}) is None


def test_acted_success_does_not_count_abstention_as_completion(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_operational_analysis import summarize

    row = {
        "id": "one",
        "group": "parent",
        "task": "PickCube-v1",
        "condition": "nominal",
        "method": "DSRE_risk",
        "mode": "calibrated",
        "scenario": "clean",
        "initial_success": True,
        "category": "both",
        "action": None,
        "recommended": 0,
        "successful": 0,
        "unacceptable": 0,
        "deferred": 1,
        "autonomous_completion": 0,
        "intervention_regret": 0,
        "autonomy_regret": 1,
        "unnecessary_recover_initial_success": 0,
        "unnecessary_recover_both": 0,
        "required_recovery_success": 0,
        "failed_start_success": 0,
        "maintained_success": 0,
        "literals": 0,
    }
    table = summarize([row])["PickCube-v1|DSRE_risk|calibrated|clean|all"]
    assert (
        table["autonomous_completion_rate"] == 0
        and table["conditional_success"] is None
    )


def router_fixture(outcomes):
    from dual_rec.dsre.operational import OperationalRouter
    from dual_rec.dsre.repair import RepairScope, RepairTable
    from dual_rec.dsre.schemas import Outcomes, ReferenceRow

    scope = RepairScope(
        task="PickCube-v1",
        controller_sha256="a" * 64,
        features=tuple(f"f{i}" for i in range(7)),
        channels="fixed",
    )
    rows = tuple(
        ReferenceRow(
            id=str(i),
            features=(True,) * 7,
            outcomes=Outcomes(continue_value=c, recover_value=r),
        )
        for i, (c, r) in enumerate(outcomes)
    )
    table = RepairTable(scope=scope, rows=rows)
    full = table.model_copy(
        update={
            "scope": scope.model_copy(
                update={"features": tuple(f"f{i}" for i in range(12))}
            ),
            "rows": tuple(
                r.model_copy(update={"features": (True,) * 12}) for r in rows
            ),
        }
    )
    setting = {
        "table": table.model_dump(mode="json"),
        "full_table": full.model_dump(mode="json"),
        "parent_groups": {r.id: r.id for r in rows},
        "selected": [0],
        "trees": {"1": [{"feature": None}], "2": [{"feature": None}]},
    }
    return OperationalRouter({"tasks": {"PickCube-v1": {"1": setting}}})


def test_unqueried_optional_information_does_not_change_common_budget_router():
    router = router_fixture([(False, True), (False, True)])
    a = PolicyInput(task="PickCube-v1", values=(True,) * 7, full_values=(True,) * 12)
    b = PolicyInput(
        task="PickCube-v1", values=(True,) * 7, full_values=(True,) * 7 + (False,) * 5
    )
    assert (
        router.route(a)["DSRE_risk"]["action"]
        == router.route(b)["DSRE_risk"]["action"]
        == "recover"
    )
    assert router.route(b)["full_signature_strict"]["action"] is None


@pytest.mark.parametrize(
    "outcomes,kind",
    [
        ([(True, False), (False, True)], "OBSERVATIONAL_AMBIGUITY"),
        ([(False, False), (False, True)], "REPERTOIRE_INADEQUATE"),
        ([], "REFERENCE_INSUFFICIENT"),
    ],
)
def test_operational_obstruction_survives_runtime_adapter(outcomes, kind):
    router = router_fixture(outcomes)
    packet = PolicyInput(
        task="PickCube-v1", values=(None,) * 7, full_values=(None,) * 12
    )
    result = router.route(packet)["DSRE_strict"]
    assert result["action"] is None
    assert kind in {x["kind"] for x in result["diagnosis"]["obstructions"]}


def test_deferred_primary_decision_executes_no_physics(monkeypatch, tmp_path):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from types import SimpleNamespace

    import dsre_operational_batch as batch

    batch.atomic(
        tmp_path / "frozen_routers.json",
        {"tasks": {"PickCube-v1": {"1": {"selected": [0]}}}},
    )
    batch.atomic(tmp_path / "calibration_decision.json", {})
    router = SimpleNamespace(
        route=lambda packet: {"DSRE_risk": {"action": "recover", "evidence": []}}
    )
    monkeypatch.setattr(
        batch,
        "World",
        lambda *args: pytest.fail("Deferred action instantiated physics"),
    )
    summary = {
        "task": "PickCube-v1",
        "features": [True] * 6,
        "optional_features": [True] * 6,
        "source": "must-not-open-future-outcomes.gz",
    }
    cell = batch.Cell(task="PickCube-v1", seed=99, condition="nominal")
    batch.selected_branch(cell, summary, tmp_path, router, {"strata": {}}, 0)
    saved = batch.read(tmp_path / "selected/PickCube-v1/99-nominal/execution.json")
    assert saved["status"] == "DEFER_STOP" and saved["new_continuations"] == 0
