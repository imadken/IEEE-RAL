import sys
from pathlib import Path

import mujoco
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.replay import distribution, quat_error


def test_quaternion_sign_and_known_rotation():
    assert quat_error(np.array([1.0, 0, 0, 0]), np.array([-1.0, 0, 0, 0])) == 0
    assert quat_error(
        np.array([1.0, 0, 0, 0]), np.array([0.0, 1, 0, 0])
    ) == pytest.approx(np.pi)


def test_distribution_rejects_invalid_evidence():
    for values in ([], [np.nan], [np.inf]):
        with pytest.raises(ValueError):
            distribution(values)
    assert sum(distribution([0.0, 1.0, 2.0])["counts"]) == 3


def test_full_mujoco_integration_state_restores_contact_rollout():
    model = mujoco.MjModel.from_xml_string("""<mujoco><worldbody>
    <geom type="plane" size="1 1 .1"/><body pos="0 0 .025"><freejoint/>
    <geom type="box" size=".02 .02 .02" mass=".064"/></body>
    </worldbody></mujoco>""")
    data = mujoco.MjData(model)
    for _ in range(50):
        mujoco.mj_step(model, data)
    assert data.ncon > 0
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    snapshot = np.empty(mujoco.mj_stateSize(model, spec))
    mujoco.mj_getState(model, data, snapshot, spec)

    def rollout():
        for _ in range(30):
            data.xfrc_applied[1, 0] = 0.1
            mujoco.mj_step(model, data)
        return data.qpos.copy(), data.qvel.copy(), data.time

    expected = rollout()
    mujoco.mj_setState(model, data, snapshot, spec)
    mujoco.mj_forward(model, data)
    mujoco.mj_setState(model, data, snapshot, spec)
    observed = rollout()
    np.testing.assert_allclose(observed[0], expected[0], atol=1e-12, rtol=0)
    np.testing.assert_allclose(observed[1], expected[1], atol=1e-12, rtol=0)
    assert observed[2] == expected[2]


def test_nested_observation_comparison_fails_closed():
    from dual_rec.validation import max_difference

    assert max_difference(
        {"agent": {"q": [1.0, 2.0]}}, {"agent": {"q": [1.0, 2.1]}}
    ) == pytest.approx(0.1)
    for b in (
        {"missing": [1.0]},
        {"agent": {"q": [1.0]}},
        {"agent": {"q": [np.nan, 2.0]}},
    ):
        with pytest.raises(ValueError):
            max_difference({"agent": {"q": [1.0, 2.0]}}, b)


def test_trajectory_gate_detects_divergence_and_missing_metrics():
    from dual_rec.validation import compare, passes

    record = {
        "position": np.zeros(3),
        "quaternion": np.array([1.0, 0, 0, 0]),
        "qpos": np.zeros(9),
        "velocity": np.zeros(9),
        "observation": {"q": [0.0]},
        "time": 0.5,
        "success": False,
        "contacts": [("cube", "finger")],
    }
    assert passes(compare(record, record))
    import copy

    for field, value in [
        ("position", np.ones(3) * 0.01),
        ("success", True),
        ("time", 0.6),
        ("contacts", []),
    ]:
        other = copy.deepcopy(record)
        other[field] = value
        assert not passes(compare(record, other))


def test_maniskill_scripted_control_bounds_and_gripper_convention():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from mani_runner import scripted_action

    cube = np.array([0.0, 0.0, 0.02])
    goal = np.array([0.15, 0.0, 0.2])
    for task in ["PushCube-v1", "PickCube-v1"]:
        for phase in range(4):
            a = scripted_action(task, cube, goal, np.array([1.0, -1.0, 1.0]), phase)
            assert a.shape == (4,)
            assert np.isfinite(a).all()
            assert (np.abs(a[:3]) <= 0.25).all()
    assert scripted_action("PickCube-v1", cube, goal, cube, 0)[-1] == 1
    assert scripted_action("PickCube-v1", cube, goal, cube, 2)[-1] == -1
    assert scripted_action("PushCube-v1", cube, goal, cube, 1)[-1] == -1


def test_maniskill_recorder_distinguishes_cube_table_from_robot_contact():
    from types import SimpleNamespace as NS

    import torch

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from mani_runner import record

    finger, cube_entity, table = [NS(name=n) for n in ["finger", "cube", "table"]]
    cube = NS(
        _objs=[cube_entity],
        pose=NS(raw_pose=torch.tensor([[0.0, 0, 0.02, 1, 0, 0, 0]])),
        linear_velocity=torch.zeros(1, 3),
        angular_velocity=torch.zeros(1, 3),
    )
    robot = NS(
        links=[NS(_objs=[NS(entity=finger)])],
        get_qpos=lambda: torch.zeros(1, 9),
        get_qvel=lambda: torch.zeros(1, 9),
    )
    contacts = [NS(bodies=[NS(entity=cube_entity), NS(entity=table)])]
    env = NS(
        agent=NS(robot=robot),
        scene=NS(get_contacts=lambda: contacts),
        elapsed_steps=torch.tensor([1]),
        control_freq=20,
        evaluate=lambda: {"success": torch.tensor([False])},
    )
    assert not record(env, cube, {"q": [0.0]})["robot_object_contact"]
    contacts.append(NS(bodies=[NS(entity=cube_entity), NS(entity=finger)]))
    assert record(env, cube, {"q": [0.0]})["robot_object_contact"]


def test_maniskill_batched_rng_snapshot_restores_draws_and_aliases():
    from types import SimpleNamespace as NS

    import torch
    from mani_skill.envs.utils.randomization.batched_rng import BatchedRNG

    from dual_rec.replay import ManiSkillReplay

    main = BatchedRNG.from_seeds([7])
    episode = BatchedRNG.from_seeds([11])
    robot = NS(
        drive_targets=torch.zeros(1, 9),
        drive_velocities=torch.zeros(1, 9),
        active_joints=[],
        set_joint_drive_targets=lambda *args, **kwargs: None,
        set_joint_drive_velocity_targets=lambda *args, **kwargs: None,
    )
    env = NS(
        gpu_sim_enabled=False,
        _main_seed=[7],
        _episode_seed=np.array([11]),
        _elapsed_steps=torch.tensor([5]),
        _main_rng=np.random.RandomState(7),
        _episode_rng=episode[0],
        _batched_main_rng=main,
        _batched_episode_rng=episode,
        agent=NS(
            robot=robot,
            controller=NS(controllers={}),
            get_controller_state=dict,
            set_controller_state=lambda state: None,
        ),
        get_state_dict=dict,
        set_state_dict=lambda state: None,
    )
    env.unwrapped = env
    adapter = ManiSkillReplay(env)
    snapshot = adapter.capture()
    from dual_rec.replay import snapshot_mismatches

    def draws():
        return [rng.rand(3) for rng in adapter.rngs().values()] + [torch.rand(3)]

    expected = draws()
    adapter.restore(snapshot)
    assert snapshot_mismatches(snapshot, adapter.capture()) == []
    for actual, reference in zip(draws(), expected, strict=True):
        np.testing.assert_array_equal(actual, reference)
    assert env._episode_rng is env._batched_episode_rng[0]
    assert env._batched_main_rng is main
    env._elapsed_steps += 1
    assert "custom/_elapsed_steps" in snapshot_mismatches(snapshot, adapter.capture())


def test_snapshot_audit_covers_pose_targets_and_rng_state():
    import copy
    from types import SimpleNamespace as NS

    import torch

    from dual_rec.replay import Snapshot, snapshot_data, snapshot_mismatches

    snapshot = Snapshot(
        {"qpos": torch.zeros(1, 9)},
        (1, 2),
        np.random.get_state(),
        {
            "drive_targets": torch.zeros(1, 9),
            "controller_transient": {
                "arm": {"_target_pose": NS(raw_pose=torch.zeros(1, 7))}
            },
            "wrapper_elapsed": [None, 53],
        },
    )
    import json

    json.dumps(snapshot_data(snapshot), allow_nan=False)
    assert snapshot_mismatches(snapshot, copy.deepcopy(snapshot)) == []
    for key in ("drive_targets", "controller_transient", "wrapper_elapsed"):
        actual = copy.deepcopy(snapshot)
        actual.custom[key] = None
        assert snapshot_mismatches(snapshot, actual) == [f"custom/{key}"]
    actual = copy.deepcopy(snapshot)
    actual.custom["missing_nullable_field"] = None
    assert snapshot_mismatches(snapshot, actual) == ["custom/missing_nullable_field"]


def test_qualification_environment_enforces_two_numerical_threads():
    import os
    import subprocess

    names = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
    env = os.environ | dict.fromkeys(names, "64")
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source scripts/env.sh\nprintf "%s\\n" "$OMP_NUM_THREADS" "$OPENBLAS_NUM_THREADS" "$MKL_NUM_THREADS"',
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.splitlines() == ["2", "2", "2"]
