"""Shared fail-closed checks for recorded branch trajectories."""

from collections.abc import Mapping

import numpy as np

from dual_rec.replay import Tolerances, quat_error


def array(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    result = np.asarray(value, dtype=float)
    if result.size == 0 or not np.isfinite(result).all():
        raise ValueError("Missing or nonfinite measurement")
    return result


def max_difference(a, b):
    if isinstance(a, Mapping) or isinstance(b, Mapping):
        if (
            not isinstance(a, Mapping)
            or not isinstance(b, Mapping)
            or a.keys() != b.keys()
        ):
            raise ValueError("Observation schemas differ")
        return max((max_difference(a[k], b[k]) for k in a), default=0.0)
    x, y = array(a), array(b)
    if x.shape != y.shape:
        raise ValueError("Measurement shapes differ")
    return float(np.max(np.abs(x - y)))


def compare(a, b):
    return {
        "position": float(np.linalg.norm(array(a["position"]) - array(b["position"]))),
        "angle": quat_error(
            array(a["quaternion"]).reshape(4), array(b["quaternion"]).reshape(4)
        ),
        "velocity": max_difference(a["velocity"], b["velocity"]),
        "qpos": max_difference(a["qpos"], b["qpos"]),
        "observation": max_difference(a["observation"], b["observation"]),
        "time": abs(float(a["time"]) - float(b["time"])),
        "success": bool(a["success"]) == bool(b["success"]),
        "contacts": a["contacts"] == b["contacts"],
    }


def passes(error, tol=None):
    tol = tol or Tolerances()
    limits = {
        "position": tol.position,
        "angle": tol.angle,
        "velocity": tol.velocity,
        "qpos": tol.angle,
        "observation": tol.observation,
        "time": 1e-9,
    }
    return (
        all(
            np.isfinite(error[k]) and 0 <= error[k] <= bound
            for k, bound in limits.items()
        )
        and bool(error["success"])
        and bool(error["contacts"])
    )
