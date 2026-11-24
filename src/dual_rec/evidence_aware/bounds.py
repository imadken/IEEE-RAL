"""Four-cell linear optimization by active-set vertex enumeration.

This production algorithm does not import the supervisor's HiGHS solver.
The simplex equality eliminates q00; every vertex intersects three planes.
"""

from itertools import combinations

import numpy as np
from scipy.special import betaincinv

from .schema import Band, Bounds, Evidence, OneAction, Pair, Source

P0 = (0.0, 0.0, 1.0, 1.0)
P1 = (0.0, 1.0, 0.0, 1.0)
H = (0.0, 0.0, 1.0, 0.0)
R = (0.0, 1.0, 0.0, 0.0)
G = (0.0, 1.0, -1.0, 0.0)


def cp(k: int, n: int, tail: float) -> Band:
    if not 0 <= k <= n or not 0 < tail < 0.5:
        raise ValueError("Invalid count or confidence allocation")
    return Band(
        lo=0 if not k else float(betaincinv(k, n - k + 1, tail)),
        hi=1 if k == n else float(betaincinv(k + 1, n - k, 1 - tail)),
    )


def vertices(e: Evidence, extra=()) -> np.ndarray:
    if not e.assumptions_supported or e.source_type == Source.OBSERVATIONAL:
        raise ValueError("IDENTIFICATION_ASSUMPTION_UNSUPPORTED")
    if not e.overlap:
        raise ValueError("NO_OVERLAP")
    if (e.harm is not None or e.rescue is not None) and e.source_type != Source.PAIRED:
        raise ValueError("COUNTERPART_SOURCE_MISMATCH")
    rows = [-np.eye(3)[j] for j in range(3)] + [np.ones(3)]
    rhs = [0.0, 0.0, 0.0, 1.0]
    bands = [(P0, e.p0), (P1, e.p1), (H, e.harm), (R, e.rescue)]
    for vector, band in bands:
        if band is None:
            continue
        a = np.asarray(vector)
        reduced = a[1:] - a[0]
        rows.extend((reduced, -reduced))
        rhs.extend((band.hi - a[0], a[0] - band.lo))
    for vector, limit in extra:
        a = np.asarray(vector)
        rows.append(a[1:] - a[0])
        rhs.append(limit - a[0])
    a, b = np.asarray(rows), np.asarray(rhs)
    choices = np.asarray(list(combinations(range(len(rows)), 3)))
    mats = a[choices]
    good = abs(np.linalg.det(mats)) > 1e-12
    solutions = np.linalg.solve(mats[good], b[choices[good]])
    solutions = solutions[np.all(solutions @ a.T <= b + 1e-10, axis=1)]
    if not len(solutions):
        raise ValueError("INCONSISTENT_BOUNDS")
    return np.column_stack((1 - solutions.sum(axis=1), solutions))


def solve(e: Evidence) -> Bounds:
    qs = vertices(e)
    specs = {
        "harm_lower": (H, False),
        "harm_upper": (H, True),
        "gain_lower": (G, False),
        "gain_upper": (G, True),
        "failure_upper": ((1, 0, 1, 0), True),
    }
    values, optimizers = {}, {}
    for key, (coefficient, maximum) in specs.items():
        objective = qs @ coefficient
        index = np.argmax(objective) if maximum else np.argmin(objective)
        values[key] = float(objective[index])
        optimizers[key] = tuple(float(x) for x in qs[index])
    return Bounds(**values, optimizers=optimizers)


def qualifies(b: Bounds, obligation="useful", toll=0.0) -> bool:
    if obligation == "completion":
        return b.failure_upper <= 0.1 + 1e-12
    if obligation == "harm_only":
        return b.harm_upper <= 0.1 + 1e-12
    if obligation != "useful":
        raise ValueError("Unknown obligation")
    return b.harm_upper <= 0.1 + 1e-12 and b.gain_lower - toll >= 0.05 - 1e-12


def calibrate(logs: list[OneAction], pairs: list[Pair], scope: str, leaves: int):
    """One look on a fixed leaf; callers enforce disjoint discovery/calibration."""
    if not 1 <= leaves <= 4:
        raise ValueError("Invalid frozen family size")
    scopes = {r.source_scope.model_dump_json() for r in logs + pairs}
    if len(scopes) > 1:
        raise ValueError("SCOPE_MISMATCH")
    if len({r.parent_id for r in logs}) != len(logs) or len(
        {r.parent_id for r in pairs}
    ) != len(pairs):
        raise ValueError("Duplicate parent in evidence block")
    if any(r.propensity != 0.5 for r in logs):
        raise ValueError("Assignment differs from frozen fair behavior rule")
    tail = 0.025 / (4 * leaves)
    arms = [[r.y for r in logs if r.action == arm] for arm in ("c", "r")]
    marginals = [cp(sum(ys), len(ys), tail) for ys in arms]
    e = Evidence(
        p0=marginals[0],
        p1=marginals[1],
        harm=cp(sum(r.yc and not r.yr for r in pairs), len(pairs), tail)
        if pairs
        else None,
        rescue=cp(sum(not r.yc and r.yr for r in pairs), len(pairs), tail)
        if pairs
        else None,
        source_type=Source.PAIRED
        if pairs
        else (
            Source.OBSERVATIONAL
            if any(r.source_type == Source.OBSERVATIONAL for r in logs)
            else Source.LOGGED
        ),
        scope=scope,
        overlap=bool(pairs) or all(arms),
    )
    ledger = {
        "K": leaves,
        "delta_L": 0.025,
        "delta_P": 0.025,
        "per_tail": tail,
        "counts_c_r_pair": [len(arms[0]), len(arms[1]), len(pairs)],
        "confidence_scope": "95 percent per task at one fixed allocation and one look",
    }
    return e, ledger
