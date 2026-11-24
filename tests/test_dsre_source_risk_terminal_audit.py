"""Pinned endpoint checks: placement and arm stationarity, with exact boundaries."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


@pytest.mark.parametrize(
    "distance,arm,finger,expected",
    [
        (0, 0, 1, True),
        (0.025, 0.2, 0, True),
        (0.026, 0, 0, False),
        (0, 0.201, 0, False),
    ],
)
def test_existing_endpoint_uses_both_placement_and_panda_arm_velocity(
    distance, arm, finger, expected
):
    from dsre_source_risk_terminal_audit import terminal_success

    state = {
        "position": [0, 0, 0],
        "observation": {"extra": {"goal_pos": [distance, 0, 0]}},
        "qpos": [[0] * 9],
        "velocity": [0] * 6 + [arm] * 7 + [finger] * 2,
    }
    assert terminal_success(state) is expected


def test_missing_physical_channel_blocks_endpoint_audit():
    from dsre_source_risk_terminal_audit import terminal_success

    with pytest.raises(KeyError):
        terminal_success({"success": True})
