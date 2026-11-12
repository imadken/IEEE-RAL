"""Continuous first alarms and two-population empirical calibration."""

from __future__ import annotations

import numpy as np

TOLERANCE = 1e-7


def first_alarm(time, scores, threshold, persistence=0.1):
    beginning = None
    for now, value in zip(time, scores, strict=True):
        if not np.isfinite(value) or value < threshold:
            beginning = None
        else:
            if beginning is None:
                beginning = now
            if now - beginning >= persistence - TOLERANCE:
                return float(now)
    return None


def persistent_capacity(time, scores, persistence=0.1):
    time = np.asarray(time)
    scores = np.asarray(scores)
    if len(time) and (not np.isfinite(time).all() or np.any(np.diff(time) <= 0)):
        raise ValueError("Strictly increasing finite decision times required")
    capacity = -np.inf
    for end, now in enumerate(time):
        start = np.searchsorted(time, now - persistence + TOLERANCE, side="right") - 1
        if 0 <= start <= end and np.isfinite(scores[start : end + 1]).all():
            capacity = max(capacity, float(np.min(scores[start : end + 1])))
    return capacity


def calibrate(success, prefix, alpha):
    populations = {}
    fits = {}
    for name, streams in (("success", success), ("prefix", prefix)):
        capacities = [persistent_capacity(r["time"], r["scores"]) for r in streams]
        populations[name] = [
            {"sample": r["sample"], "capacity": float(c) if np.isfinite(c) else None}
            for r, c in zip(streams, capacities, strict=True)
        ]
        valid = sorted([c for c in capacities if np.isfinite(c)], reverse=True)
        if not valid:
            fits[name] = {
                "valid": 0,
                "invalid": len(streams),
                "allowed": 0,
                "threshold": None,
            }
            continue
        allowed = int(np.floor(alpha * len(valid)))
        theta = float(np.nextafter(valid[allowed], np.inf))
        fits[name] = {
            "valid": len(valid),
            "invalid": len(streams) - len(valid),
            "allowed": allowed,
            "threshold": theta,
        }
    available = all(r["threshold"] is not None for r in fits.values())
    threshold = max(r["threshold"] for r in fits.values()) if available else None
    for name, rows in populations.items():
        fits[name]["realized_alarms"] = (
            sum(r["capacity"] is not None and r["capacity"] >= threshold for r in rows)
            if available
            else None
        )
    return {
        "threshold": threshold,
        "available": available,
        "alpha": alpha,
        "populations": populations,
        "fits": fits,
        "scope": "calibration_only",
    }


def outcome(row, time, scores, threshold, persistence=0.1):
    alarm = (
        first_alarm(time, scores, threshold, persistence)
        if threshold is not None
        else None
    )
    exposure = float(min(row["duration"], time[-1])) if len(time) else 0.0
    failed = row["verdict"] == "fail"
    onset = row.get("onset")
    timely = bool(
        failed and alarm is not None and onset <= alarm <= onset + 1 + TOLERANCE
    )
    premature = bool(failed and alarm is not None and alarm < onset)
    late = bool(failed and alarm is not None and alarm > onset + 1 + TOLERANCE)
    missed = bool(failed and alarm is None)
    status = (
        "timely"
        if timely
        else "premature"
        if premature
        else "late"
        if late
        else "missed"
        if failed
        else "clean_alarm"
        if alarm is not None
        else "clean_quiet"
    )
    return {
        "sample": row["sample"],
        "robot": row["robot"],
        "task_id": row["task_id"],
        "alarm_time": alarm,
        "status": status,
        "timely": timely,
        "premature": premature,
        "clean_alarm": bool(not failed and alarm is not None),
        "late": late,
        "missed": missed,
        "observable_window": bool(not failed or onset + 1 <= exposure + TOLERANCE),
        "exposure": exposure,
        "delay": float(alarm - onset) if timely else None,
        "threshold": threshold,
        "persistence": persistence,
        "is_failure": failed,
        "abstention": threshold is None or not np.isfinite(scores).any(),
    }
