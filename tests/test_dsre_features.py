import pytest
from pydantic import ValidationError

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame


def observation(x, goal=0.1):
    return {
        "extra": {
            "obj_pose": [[x, 0, 0]],
            "tcp_pose": [[x, 0, 0.02]],
            "goal_pos": [[goal, 0, 0]],
            "is_grasped": [True],
        },
        "agent": {"qpos": [[0] * 7 + [0.01, 0.01]]},
    }


def test_only_predecision_observation_fields_enter_features():
    start = observed_frame(0, observation(0))
    current = observed_frame(1, observation(0.09))
    history = ObservationHistory(first=start, current=current)
    assert feature_values(history) == (True, True, True, True, True, False)
    obs = observation(0.09) | {"future_success": False, "condition": "misaligned"}
    obs["extra"]["is_grasped"] = [False]
    assert observed_frame(1, obs) == current
    with pytest.raises(ValidationError):
        ObservationHistory(first=current, current=start)
    with pytest.raises(ValidationError):
        ObservationHistory.model_validate(
            history.model_dump() | {"future_outcome": True}
        )


def test_missing_nonfinite_and_insufficient_joint_channels_are_unknown():
    frame = observed_frame(1, {"extra": {"obj_pose": [[float("nan"), 0, 0]]}})
    assert feature_values(ObservationHistory(first=None, current=frame)) == (None,) * 6
    current = observed_frame(1, observation(0.09))
    assert feature_values(ObservationHistory(first=None, current=current))[2:4] == (
        None,
        None,
    )


def test_coarsening_is_geometry_not_outcome_tuning():
    history = ObservationHistory(
        first=observed_frame(0, observation(0.001, 0.034)),
        current=observed_frame(1, observation(0.001, 0.034)),
    )
    assert not feature_values(history)[0]
    assert not feature_values(history, coarse=True)[0]
