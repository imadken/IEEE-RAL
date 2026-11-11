"""Actual pinned-stack checks; run explicitly in the isolated Python 3.10 env."""

import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pytest

from dual_rec.recoverbench.qualification import make_pickplace_adapter
from dual_rec.recoverbench.qualification_replay import independently_reconstruct
from dual_rec.recoverbench.replay import load_original

pytestmark = pytest.mark.skipif(
    importlib.metadata.version("mujoco") != "2.3.2",
    reason="Requires unchanged isolated RecoverBench stack",
)
ROOT = Path("results/recoverbench-qualification-rescue/20261111T195432Z")


@pytest.fixture(scope="module")
def stack():
    env, wrapper = load_original(ROOT, "stack")
    yield env, wrapper
    env.close()


def test_actual_constructor_and_controller_conventions(stack):
    env, _ = stack
    assert type(env).__name__ == "Stack_D0"
    controller = env.robots[0].controller
    assert env.action_dim == 7 and controller.use_delta
    np.testing.assert_allclose(
        controller.scale_action(np.ones(6)), [0.05] * 3 + [0.5] * 3
    )
    gripper = env.robots[0].gripper
    gripper.current_action[:] = 0
    np.testing.assert_allclose(gripper.format_action(np.array([1.0])), [-0.01, 0.01])


def test_direct_state_injection_and_documented_wrapper_refresh_differ(stack):
    env, wrapper = stack
    registration = json.loads((ROOT / "registration.json").read_text())
    case = next(c for c in registration["sources"] if c["task"] == "stack")
    with np.load(ROOT / "data" / case["archive_member"], allow_pickle=False) as source:
        state = source["states"][0]
    env.reset()
    cached = env.robots[0].controller.ee_pos.copy()
    env.sim.set_state_from_flattened(state)
    env.sim.forward()
    np.testing.assert_array_equal(env.robots[0].controller.ee_pos, cached)
    wrapper.set_sim_state_flat(state)
    np.testing.assert_allclose(
        env.robots[0].controller.ee_pos, wrapper.get_eef_pos(), atol=1e-12
    )
    np.testing.assert_allclose(
        env.robots[0].controller.goal_pos, wrapper.get_eef_pos(), atol=1e-12
    )


def test_independent_fk_and_original_success_are_offline_checks(stack):
    env, wrapper = stack
    before = env.sim.get_state().flatten().copy()
    result = independently_reconstruct(env, before)
    assert result["site_body_position_error"] < 1e-12
    assert result["site_body_rotation_error"] < 1e-12
    np.testing.assert_allclose(result["eef"], wrapper.get_eef_pos(), atol=1e-12)
    np.testing.assert_array_equal(before, env.sim.get_state().flatten())
    assert wrapper.check_success() == bool(env._check_success())


def test_pickplace_original_failure_and_explicit_adapted_identity():
    import robosuite

    kwargs = {
        "robots": ["Sawyer"],
        "has_renderer": False,
        "has_offscreen_renderer": False,
        "use_camera_obs": False,
    }
    with pytest.raises(TypeError, match="z_rotation"):
        robosuite.make("PickPlace_D0", **kwargs)
    env = make_pickplace_adapter()(**kwargs)
    try:
        assert type(env).__name__ == "QualificationPickPlaceYawAdapter"
        np.testing.assert_allclose(
            env.placement_initializer.samplers["CollisionObjectSampler"].rotation,
            [0, np.pi / 2],
        )
    finally:
        env.close()
