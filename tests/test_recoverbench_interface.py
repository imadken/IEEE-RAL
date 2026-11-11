"""Regression checks for exact split hashing without rounded state comparisons."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.recoverbench.interface_audit import state_digest


def test_state_hash_is_task_and_subtype_specific():
    state = np.array([0.0, 0.1, 0.2])
    assert state_digest("stack", "drop_D0", state) != state_digest(
        "pick_place", "drop_D0", state
    )
    assert state_digest("stack", "drop_D0", state) != state_digest(
        "stack", "drop_D1", state
    )


def test_state_hash_preserves_small_changes_and_endianness():
    state = np.array([0.0, 0.1, 0.2], dtype="<f8")
    assert state_digest("stack", "drop_D0", state) == state_digest(
        "stack", "drop_D0", state.astype(">f8")
    )
    changed = state.copy()
    changed[1] = np.nextafter(changed[1], 1.0)
    assert state_digest("stack", "drop_D0", state) != state_digest(
        "stack", "drop_D0", changed
    )
