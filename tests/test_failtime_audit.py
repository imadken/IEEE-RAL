"""Independent FailTime audit rejects fabricated, duplicated or censored support."""

import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "failtime_independent_audit",
    Path(__file__).resolve().parents[1] / "scripts/failtime_independent_audit.py",
)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


def annotation(**changes):
    row = {
        "sample": "task_episode_1",
        "task_id": "task",
        "episode": "episode_1",
        "robot": "so101",
        "hdf5": "episodes/task_episode_1.hdf5",
        "verdict": "fail",
        "onset": 0.5,
    }
    return {**row, **changes}


@pytest.mark.parametrize(
    "changes",
    [
        {"onset": None},
        {"onset": float("nan")},
        {"onset": -1.0},
        {"hdf5": "../escaped.hdf5"},
        {"verdict": "probably_failed"},
    ],
)
def test_released_schema_rejects_missing_or_invalid_annotations(changes):
    records, problems = audit.validate_rows([annotation(**changes)])
    assert not records and len(problems) == 1


def test_source_alias_is_not_an_independent_recording():
    records, problems = audit.validate_rows(
        [annotation(), annotation(sample="renamed")]
    )
    assert len(records) == 2
    assert "Duplicated" in problems[0]["error"]


@pytest.mark.parametrize(
    "times",
    [
        np.array([0.0, 0.1, 0.1, 0.3]),
        np.array([0.0, 0.1, 0.3, 0.4]),
        np.array([0.0, 0.1, np.nan, 0.3]),
    ],
)
def test_bad_timestamp_sequences_are_not_repaired(times):
    result = audit.check_arrays(times, np.zeros((len(times), 16)), 0.1)
    assert result["valid"] is False


def test_onset_boundary_and_followup_censoring_are_separate():
    times = np.arange(11) / 10
    result = audit.check_arrays(times, np.zeros((11, 16)), 1.0)
    assert result["valid"] and result["onset_in_bounds"]
    assert result["full_delay_window_observable"] is False
    assert not audit.check_arrays(times, np.zeros((11, 16)), 1.001)["valid"]


def test_missing_raw_file_never_becomes_verified_support(tmp_path):
    result = audit.inspect_hdf5(
        tmp_path / "missing.hdf5", audit.ReleasedAnnotation.model_validate(annotation())
    )
    assert not result["available"] and not result["valid"]


def test_reader_ignores_embedded_video_and_uses_actual_timestamps(tmp_path):
    path = tmp_path / "episode.hdf5"
    with h5py.File(path, "w") as stream:
        stream.create_dataset("timestamp", data=np.arange(21) / 10)
        stream.create_dataset("observation.state_eef", data=np.zeros((21, 16)))
        stream.create_group("observation.images.head").create_dataset(
            "mp4_bytes", data=np.arange(5, dtype=np.uint8)
        )
    result = audit.inspect_hdf5(
        path, audit.ReleasedAnnotation.model_validate(annotation())
    )
    assert result["valid"] and result["median_hz"] == pytest.approx(10.0)
    assert result["camera_groups_unread"] == ["observation.images.head"]
    assert result["time_source"] == "Actual timestamp dataset, not inferred fps"


def test_release_comparison_preserves_changed_labels():
    result = audit.compare_releases([annotation()], [annotation(onset=0.6)])
    assert result["changed_records"] == ["task_episode_1"]
