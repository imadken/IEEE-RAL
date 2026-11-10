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
