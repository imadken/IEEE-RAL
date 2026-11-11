"""Separate evaluation annotations from permitted causal robot observations."""

from __future__ import annotations

from itertools import pairwise
from typing import Literal

import numpy as np
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)


class FailureEvent(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    originating_phase: StrictInt = Field(ge=1, le=5)
    failure_mode: str
    onset_frame: StrictInt = Field(
        validation_alias=AliasChoices("t_f", "induced_at_frame")
    )
    recovery_frame: StrictInt = Field(
        validation_alias=AliasChoices("t_r", "recovery_started_at_frame")
    )

    @model_validator(mode="before")
    @classmethod
    def reject_conflicting_aliases(cls, values):
        for left, right in (
            ("t_f", "induced_at_frame"),
            ("t_r", "recovery_started_at_frame"),
        ):
            if left in values and right in values and values[left] != values[right]:
                raise ValueError(
                    "Conflicting event annotations; refusing to select an alias"
                )
        return values


class PhaseEpisode(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    episode_index: int = Field(ge=0)
    episode_type: str
    duration_frames: StrictInt = Field(gt=0)
    fps: StrictInt = Field(gt=0)
    phase_boundaries: dict[str, StrictInt]
    failure: FailureEvent | None = None

    @field_validator("episode_index", mode="before")
    @classmethod
    def exact_episode_index(cls, value):
        if isinstance(value, bool) or not (
            isinstance(value, int) or isinstance(value, str) and value.isdigit()
        ):
            raise ValueError("Episode index must be an integer or digit string")
        return int(value)


class RuntimeObservation(BaseModel):
    """No event/phase/outcome/repository identifiers may enter this boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    qpos: list[float] = Field(min_length=14, max_length=14)
    previously_issued_action: list[float] = Field(min_length=14, max_length=14)
    symmetry: Literal["continuous", "C1", "C2"]
    operation: Literal["install", "remove"]
    clearance_mm: float = Field(ge=0)


def event_integrity(annotation: PhaseEpisode, actual_frames: np.ndarray):
    """Report defects; never clip/relabel events using future corrective actions."""
    frames = np.asarray(actual_frames)
    errors, warnings = [], []
    if frames.ndim != 1 or len(frames) == 0 or len(np.unique(frames)) != len(frames):
        raise ValueError("Episode-local frame indices must be nonempty and unique")
    if not np.array_equal(frames, np.arange(len(frames))):
        errors.append("frame_indices_not_zero_based_contiguous")
    bounds = [annotation.phase_boundaries.get(f"tau_{i}") for i in range(6)]
    ordered = all(v is not None for v in bounds) and all(
        a < b for a, b in pairwise(bounds)
    )
    if not ordered:
        errors.append("phase_boundaries_missing_or_nonmonotonic")
    if ordered and (bounds[0] != 0 or bounds[-1] > len(frames)):
        errors.append("phase_boundaries_outside_recording")
    if annotation.duration_frames != len(frames):
        warnings.append("annotation_duration_differs_from_actual_frames")
    if ordered and bounds[-1] < len(frames):
        warnings.append("phase_annotations_leave_uncovered_tail")
    event = annotation.failure
    result = {
        "errors": errors,
        "warnings": warnings,
        "event_frames_in_bounds": False,
        "pre_recovery_frames": None,
        "origin_phase_at_onset": None,
        "origin_matches_half_open_phase": None,
        "onset_on_phase_boundary": None,
    }
    if event is None:
        result["errors"].append("missing_failure_events")
        return result
    valid = (
        event.onset_frame in frames
        and event.recovery_frame in frames
        and event.onset_frame < event.recovery_frame
    )
    result["event_frames_in_bounds"] = bool(valid)
    if not valid:
        result["errors"].append("failure_recovery_event_bounds_or_order_invalid")
    else:
        result["pre_recovery_frames"] = int(
            np.sum((frames >= event.onset_frame) & (frames < event.recovery_frame))
        )
    if ordered:
        phase = next(
            (
                i + 1
                for i, (start, end) in enumerate(pairwise(bounds))
                if start <= event.onset_frame < end
            ),
            None,
        )
        result["origin_phase_at_onset"] = phase
        result["origin_matches_half_open_phase"] = phase == event.originating_phase
        result["onset_on_phase_boundary"] = event.onset_frame in bounds[1:-1]
        if phase != event.originating_phase:
            result["warnings"].append(
                "origin_phase_disagrees_with_half_open_boundary_labels"
            )
    return result


def causal_signals(qpos, actions, timestamps):
    """Backward-only velocities and previously issued target errors; no labels."""
    qpos, actions, timestamps = (
        np.asarray(qpos),
        np.asarray(actions),
        np.asarray(timestamps),
    )
    if (
        qpos.ndim != 2
        or qpos.shape[1] != 14
        or actions.shape != qpos.shape
        or timestamps.shape != (len(qpos),)
    ):
        raise ValueError(
            "Expected aligned N by 14 state/action arrays and N timestamps"
        )
    if (
        not np.isfinite(qpos).all()
        or not np.isfinite(actions).all()
        or not np.isfinite(timestamps).all()
        or np.any(np.diff(timestamps) <= 0)
    ):
        raise ValueError("Nonfinite or nonmonotonic causal observations")
    velocity = np.zeros_like(qpos, dtype=float)
    velocity[1:] = np.diff(qpos, axis=0) / np.diff(timestamps)[:, None]
    lagged = np.concatenate([qpos[:1], actions[:-1]])
    return np.concatenate([qpos, velocity, lagged - qpos], axis=1)
