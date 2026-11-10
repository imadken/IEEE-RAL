"""Regression checks for D5-D7 physical, replay-recipe and information boundaries."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.physical_faults import apply_fault, body_parameters
from dual_rec.scenarios import (
    Fault,
    HistoryFrame,
    RobotObservation,
    failure_trigger,
    history_features,
    normalized_utility,
    recovery_action,
    split_seeds,
)


def packet(step=0):
    return RobotObservation(
        task_state={
            "agent": {"qpos": [[0.0] * 9], "qvel": [[0.0] * 9]},
            "extra": {
                "tcp_pose": [[0, 0, 0.02, 1, 0, 0, 0]],
                "obj_pose": [[0, 0, 0.02, 1, 0, 0, 0]],
                "goal_pos": [[0.2, 0, 0.001]],
            },
        },
        cube_velocity=[0.0] * 6,
        drive_targets=[0.0] * 9,
        drive_velocities=[0.0] * 9,
        joint_forces=[0.0] * 9,
        link_wrenches=[[0.0] * 6] * 12,
        robot_cube_contact=True,
        time=step / 20,
    )


def test_real_sapien_density_change_scales_mass_and_inertia_and_isolates_material():
    import sapien
    from sapien.physx import PhysxCpuSystem, PhysxRigidDynamicComponent

    scene = sapien.Scene([PhysxCpuSystem()])
    material = sapien.physx.PhysxMaterial(0.3, 0.3, 0)
    bodies = []
    for index in range(2):
        builder = scene.create_actor_builder()
        builder.add_box_collision(half_size=[0.02] * 3, material=material)
        actor = builder.build(f"cube-{index}")
        bodies.append(actor.find_component_by_type(PhysxRigidDynamicComponent))
    original = body_parameters(bodies[0])
    edit = apply_fault(bodies[0], Fault(name="steel", mass_scale=8, friction=1.2))
    assert edit.control_step == 0
    assert edit.after["mass_kg"] == pytest.approx(original["mass_kg"] * 8, rel=1e-6)
    np.testing.assert_allclose(
        edit.after["inertia_kg_m2"],
        np.asarray(original["inertia_kg_m2"]) * 8,
        rtol=1e-6,
        atol=0,
    )
    assert edit.after["center_of_mass_pose"] == original["center_of_mass_pose"]
    assert bodies[1].mass == pytest.approx(original["mass_kg"])
    assert bodies[1].collision_shapes[
        0
    ].physical_material.dynamic_friction == pytest.approx(0.3)


def test_fault_edit_repeats_from_fresh_physical_body():
    import sapien
    from sapien.physx import PhysxCpuSystem, PhysxRigidDynamicComponent

    edits = []
    for _ in range(2):
        scene = sapien.Scene([PhysxCpuSystem()])
        builder = scene.create_actor_builder()
        builder.add_box_collision(half_size=[0.02] * 3)
        body = builder.build("cube").find_component_by_type(PhysxRigidDynamicComponent)
        edits.append(apply_fault(body, Fault(name="mass", mass_scale=8)).model_dump())
    assert edits[0] == edits[1]


def test_history_schema_rejects_oracle_and_future_inputs_but_keeps_every_sensor():
    history = [
        HistoryFrame(step=s, observation=packet(s), action=[0] * 4) for s in range(79)
    ]
    before = history_features(history)
    for field in (
        "seed",
        "condition",
        "friction",
        "mass",
        "success",
        "recovery",
        "future_outcome",
    ):
        altered = history[0].model_dump()
        altered["observation"][field] = 1
        with pytest.raises(ValidationError):
            history_features([altered] + history[1:])
    for name in RobotObservation.model_fields:
        altered = copy.deepcopy(history)
        values = altered[-1].observation.model_dump()
        if name == "task_state":
            values[name]["agent"]["qpos"][0][0] = 2
        elif name == "robot_cube_contact":
            values[name] = False
        elif name == "time":
            continue
        elif isinstance(values[name][0], list):
            values[name][0][0] = 2
        else:
            values[name][0] = 2
        altered[-1].observation = RobotObservation.model_validate(values)
        assert not np.array_equal(before, history_features(altered)), name
    with pytest.raises(ValueError):
        history_features(
            history + [HistoryFrame(step=79, observation=packet(79), action=[0] * 4)]
        )
    with pytest.raises(ValueError):
        history_features(history[:-1])


def test_seed_partitions_are_grouped_and_replay_does_not_add_samples():
    config = json.loads(Path("config/gate_d5_d7.json").read_text())
    train, test = split_seeds(config)
    assert len(train | test) == 24
    config["qualification_seeds"] = [1000]
    with pytest.raises(ValueError):
        split_seeds(config)
    config["qualification_seeds"] = [2000]
    config["replay_seeds"] = [9000]
    with pytest.raises(ValueError):
        split_seeds(config)
    config["replay_seeds"] = [1000]
    config["qualification_seeds"] = list(range(2000, 2030))
    with pytest.raises(ValueError):
        split_seeds(config)


def test_recoveries_have_equal_horizon_costs_and_never_take_fault_metadata():
    import inspect

    assert list(inspect.signature(recovery_action).parameters) == [
        "observation",
        "recovery",
        "step",
        "initial_tcp",
    ]
    for mode in ("continue", "recontact", "slow"):
        actions = [
            recovery_action(packet(), mode, s, np.array([0, 0, 0.02]))
            for s in range(50)
        ]
        assert np.asarray(actions).shape == (50, 4)
        assert (np.abs(np.asarray(actions)[:, :3]) <= 0.25).all()
        assert (np.asarray(actions)[:, -1] == -1).all()
        assert (
            0
            <= normalized_utility(False, actions)
            < normalized_utility(True, actions)
            <= 1
        )
        assert normalized_utility(True, actions) - normalized_utility(
            False, actions
        ) == pytest.approx(1 / 1.1)
    with pytest.raises(ValueError):
        normalized_utility(True, [[0] * 4] * 49)


def test_failure_needs_executed_nonprogress_or_missed_contact_not_a_condition_tag():
    def state(x, contact, success=False):
        return {
            "position": [x, 0, 0.02],
            "robot_object_contact": contact,
            "success": success,
            "observation": {"extra": {"goal_pos": [[0.2, 0, 0.001]]}},
        }

    assert failure_trigger([state(0, True)] * 11)["failed"]
    assert failure_trigger([state(0, False)] * 11)["missed_contact"]
    assert not failure_trigger([state(0, True)] * 10 + [state(0.02, True)])["failed"]
    assert not failure_trigger([state(0, True, True)] * 11)["failed"]


def test_passive_models_use_training_scaling_and_handle_nonlinear_signal():
    from dual_rec.passive import fit_model, metrics, predict

    x = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]], dtype=float)
    y = np.array([0, 1, 1, 0])
    model = fit_model(x, y, "rbf_kernel_logistic", 0.01)
    assert metrics(y, predict(model, x))["balanced_accuracy"] == 1
    original = copy.deepcopy(model)
    predict(model, np.array([[1000, 2000]], dtype=float))
    assert model == original
    assert model["mean"] == [0, 0]
    assert model["scale"] == [1, 1]


def test_classifier_cv_keeps_fault_rows_of_each_base_seed_together():
    from dual_rec.passive import select_model

    groups = np.repeat(np.arange(8), 2)
    y = np.tile([0, 1], 8)
    x = np.column_stack([y, groups / 10])
    model, scores = select_model(x, y, groups, "logistic", [0.1, 1])
    assert model["mode"] == "logistic"
    for score in scores:
        for group in np.unique(groups):
            assert len(set(np.asarray(score["folds"])[groups == group])) == 1
        assert score["cross_validated_metrics"]["balanced_accuracy"] == 1


def test_statistical_controls_do_not_count_recoveries_as_independent_seeds():
    from dual_rec.passive import (
        clustered_metric_intervals,
        mean_interval,
        metrics,
        wilson,
    )

    y = np.tile([0, 1], 8)
    p = np.tile([0.1, 0.9], 8)
    groups = np.repeat(np.arange(8), 2)
    assert metrics(y, p)["auroc"] == 1
    assert metrics(y, np.ones(16) * 0.5)["auroc"] == 0.5
    assert clustered_metric_intervals(y, p, groups, repetitions=20)["auroc"] == [1, 1]
    assert mean_interval([0.2] * 8, repetitions=20)["independent_seeds"] == 8
    assert wilson(8, 8)[0] < 1
    assert mean_interval([]) is None
