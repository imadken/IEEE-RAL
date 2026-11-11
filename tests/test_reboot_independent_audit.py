"""Independent verification rejects tampered evidence and absent source bytes."""

import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "reboot_independent_audit",
    Path(__file__).resolve().parents[1] / "scripts/reboot_independent_audit.py",
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_archived_ranges_refuse_gaps_and_tampering(tmp_path):
    path = tmp_path / "range.bin"
    path.write_bytes(b"abc")
    manifest = {
        "original_size": 10,
        "ranges": [
            {
                "path": "range.bin",
                "start": 2,
                "end": 4,
                "sha256": hashlib.sha256(b"abc").hexdigest(),
            }
        ],
    }
    source = audit.ArchivedRangeFile(tmp_path, manifest)
    with pytest.raises(ValueError, match="gap"):
        source.read(1)
    source.seek(2)
    assert source.read(3) == b"abc"
    with pytest.raises(ValueError, match="gap"):
        source.read(1)
    path.write_bytes(b"abd")
    with pytest.raises(ValueError, match="hash"):
        audit.ArchivedRangeFile(tmp_path, manifest)


@pytest.mark.parametrize("recovery", [3, 2])
def test_independent_event_check_never_credits_empty_or_reversed_window(recovery):
    raw = {
        "phase_boundaries": {f"tau_{i}": i * 2 for i in range(6)},
        "failure": {"originating_phase": 2, "t_f": 3, "t_r": recovery},
    }
    result = audit.independently_check_annotation(raw, np.arange(10))
    assert result["event_frames_in_bounds"] is False
    assert result["pre_recovery_frames"] is None
