"""Analytical planning and synthetic schema tests; no simulator is instantiated."""

import copy
from fractions import Fraction

import pytest
from pydantic import ValidationError
from rpd_cases import chain, model, named_cases, three_world
from rpd_independent_oracle import (
    check_policy,
    exhaustive,
    pomdp_value,
    verify_obstruction,
)

from dual_rec.recoverability.adapters import (
    encode_response,
    mask_native_state,
    probe_commands,
)
from dual_rec.recoverability.planner import observed_branch, plan_probes
from dual_rec.recoverability.schema import FiniteProbeProblem


@pytest.mark.parametrize("name", sorted(named_cases()))
def test_named_models_match_independent_complete_tree_oracle_and_pomdp(name):
    p = named_cases()[name]
    raw = p.model_dump(mode="json")
    answer = plan_probes(p)
    expected, count = exhaustive(raw)
    probability, cost = pomdp_value(raw)
    assert count > 0
    assert (
        answer.worst_probe_cost == cost == (None if expected is None else expected[0])
    )
    if expected is None:
        assert answer.policy.decision == "STOP" and probability < 1
        verify_obstruction(raw, answer.obstruction.model_dump(mode="json"))
    else:
        assert probability == 1
        traces = check_policy(raw, answer.policy.model_dump(mode="json"))
        assert all(t[0] for t in traces)
        assert max(t[1] for t in traces) == cost
    assert answer.statistical_calibration is False
    assert answer.physical_deployment_authorized is False
    assert answer.implicit_resets is False


def test_supervisor_example_coarse_probe_and_observation_dependent_macros():
    r = plan_probes(three_world())
    assert r.worst_probe_cost == 2 and r.policy.action_id == "coarse_safe"
    assert observed_branch(r.policy, "left").action_id == "retry"
    assert observed_branch(r.policy, "right").action_id == "realign"


def test_destructive_probe_cannot_restore_the_original_world_on_next_step():
    raw = three_world(horizon=4).model_dump(mode="json")
    raw["probes"] = [p for p in raw["probes"] if p["probe_id"] == "full_diagnostic"]
    p = FiniteProbeProblem.model_validate(raw)
    r = plan_probes(p)
    assert r.policy.decision == "STOP"
    proof = r.obstruction.model_dump(mode="json")
    assert proof["probes"][0]["child"]["belief"] == ["dead_C"]
    verify_obstruction(raw, proof)


@pytest.mark.parametrize("depth", [2, 3])
def test_horizon_is_consumed_by_genuine_physical_steps(depth):
    raw = chain(depth).model_dump(mode="json")
    assert plan_probes(FiniteProbeProblem.model_validate(raw)).worst_probe_cost == depth
    raw["horizon"] = depth - 1
    r = plan_probes(FiniteProbeProblem.model_validate(raw))
    assert r.policy.decision == "STOP"
    verify_obstruction(raw, r.obstruction.model_dump(mode="json"))


def test_exact_cost_budget_and_zero_cost_cycles():
    assert plan_probes(three_world(budget=1)).worst_probe_cost is None
    assert plan_probes(three_world(budget=2)).worst_probe_cost == 2
    r = plan_probes(named_cases()["zero_cost_loop_cannot_reset"])
    assert r.policy.decision == "STOP" and r.dynamic_programming_states == 5
    r = plan_probes(named_cases()["exact_rational_cost_trap"])
    assert r.policy.action_id == "B_probe" and r.worst_probe_cost < Fraction(1)


def test_safety_set_and_common_task_macro_are_different_predicates():
    p = named_cases()["physically_allowed_but_irrecoverable"]
    assert all(s.physically_allowed for s in p.states)
    assert plan_probes(p).policy.decision == "STOP"
    p = named_cases()["individual_options_no_common_diagnosis"]
    assert all(any(r.task_success for r in s.recoveries) for s in p.states)
    assert plan_probes(p).policy.decision == "STOP"


def test_pure_observation_refinement_cannot_remove_an_existing_common_action():
    p = model(
        {"A": {"r": True}, "B": {"r": True}},
        {"sense": {"A": "A", "B": "B"}},
        {"sense": {"A": "a", "B": "b"}},
    )
    for support in (("A", "B"), ("A",), ("B",)):
        q = p.model_copy(update={"initial_support": support})
        assert plan_probes(q).policy.action_id == "r"


@pytest.mark.parametrize("bad", [-1, 0.5, True, "NaN", "1/0"])
def test_cost_boundary_rejects_inexact_or_invalid_inputs(bad):
    raw = three_world().model_dump(mode="json")
    raw["probes"][0]["cost"] = bad
    with pytest.raises(ValidationError):
        FiniteProbeProblem.model_validate(raw)


@pytest.mark.parametrize(
    "change",
    [
        "unknown_initial",
        "duplicate_state",
        "missing_transition",
        "unknown_successor",
        "inconsistent_post_observation",
        "disabled_with_successor",
        "missing_outcome",
        "unknown_success",
        "calibration_claim",
        "continuous_scope",
        "invalid_horizon",
        "world_class_selection",
        "missing_assumptions",
    ],
)
def test_incomplete_or_unsupported_source_contract_is_rejected(change):
    raw = three_world().model_dump(mode="json")
    if change == "unknown_initial":
        raw["initial_support"] = ["unrecorded"]
    elif change == "duplicate_state":
        raw["states"].append(copy.deepcopy(raw["states"][0]))
    elif change == "missing_transition":
        raw["probes"][0]["transitions"].pop()
    elif change == "unknown_successor":
        raw["probes"][0]["transitions"][0]["successor"] = "unrecorded"
    elif change == "inconsistent_post_observation":
        rows = raw["probes"][0]["transitions"]
        rows[1]["successor"] = rows[0]["successor"]
        rows[1]["observation"] = "contradictory"
    elif change == "disabled_with_successor":
        raw["probes"][0]["transitions"][0]["enabled"] = False
    elif change == "missing_outcome":
        raw["states"][0]["recoveries"].pop()
    elif change == "unknown_success":
        raw["states"][0]["recoveries"][0]["task_success"] = None
    elif change == "calibration_claim":
        raw["calibration_available"] = True
    elif change == "continuous_scope":
        raw["source_scope"] = "ALL_CONTINUOUS_PHYSICAL_STATES"
    elif change == "invalid_horizon":
        raw["horizon"] = 5
    elif change == "world_class_selection":
        raw["selection"] = "AFTER_TEST_OUTCOMES"
    elif change == "missing_assumptions":
        raw["assumptions"] = []
    with pytest.raises(ValidationError):
        FiniteProbeProblem.model_validate(raw)


def test_unknown_observation_stops_instead_of_resetting_or_guessing():
    r = plan_probes(three_world())
    with pytest.raises(ValueError, match="UNKNOWN_OBSERVATION"):
        observed_branch(r.policy, "out_of_model")
    with pytest.raises(ValidationError):
        r.policy.action_id = "full_diagnostic"


def synthetic_native_frame(index=0):
    return {
        "time": index * 0.05,
        "future_success": True,
        "fault_label": "hidden",
        "observation": {
            "agent": {
                "qpos": [[index * 0.01] * 7 + [0.03, 0.03]],
                "qvel": [[0.2] * 7 + [1, 1]],
            },
            "extra": {
                "tcp_pose": [[index * 0.001, 0, 0.1, 1, 0, 0, 0]],
                "obj_pose": [[1, 2, 3]],
                "is_grasped": [True],
            },
        },
    }


def test_synthetic_native_packet_mask_excludes_privileged_and_finger_fields():
    a = synthetic_native_frame()
    b = copy.deepcopy(a)
    b["fault_label"] = "different"
    b["future_success"] = False
    b["observation"]["agent"]["qpos"][0][7:] = [999, 999]
    b["observation"]["extra"]["obj_pose"] = [[100, 200, 300]]
    b["observation"]["extra"]["is_grasped"] = [False]
    assert mask_native_state(a) == mask_native_state(b)
    assert set(mask_native_state(a).model_dump()) == {
        "time_seconds",
        "arm_qpos",
        "arm_qvel",
        "tcp_xyz",
        "source",
    }


def test_synthetic_response_is_measured_kinematics_and_never_success_or_force():
    frames = tuple(mask_native_state(synthetic_native_frame(i)) for i in range(11))
    result = encode_response(frames)
    assert result.displacement_bins_5mm == (2, 0, 0)
    assert result.physical_effect_qualified is False
    with pytest.raises(ValueError, match="missing is not false"):
        encode_response(frames[:-1])


@pytest.mark.parametrize("field", ["time", "qpos", "tcp_pose"])
def test_missing_native_channels_are_not_imputed(field):
    raw = synthetic_native_frame()
    if field == "time":
        del raw[field]
    elif field == "qpos":
        del raw["observation"]["agent"][field]
    else:
        del raw["observation"]["extra"][field]
    with pytest.raises(ValueError):
        mask_native_state(raw)


@pytest.mark.parametrize(
    "task,probe",
    [
        ("PickCube-v1", "micro_lift"),
        ("PickCube-v1", "release_settle"),
        ("PushCube-v1", "forward_tap"),
        ("PushCube-v1", "lateral_sweep"),
    ],
)
def test_pure_probe_interfaces_have_equal_ten_control_cost(task, probe):
    commands = probe_commands(task, probe)
    assert len(commands) == 10 and all(len(c) == 4 for c in commands)
    assert all(-1 <= v <= 1 for c in commands for v in c)


def test_task_or_probe_substitution_is_rejected():
    with pytest.raises(ValueError):
        probe_commands("PegInsertionSide-v1", "anything")
    with pytest.raises(ValueError):
        probe_commands("PushCube-v1", "invent_force_probe")
