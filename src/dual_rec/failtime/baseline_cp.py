"""Causal prefix use of pinned upstream Sign-CPD, with arrival-time decisions."""

from __future__ import annotations

import ast
import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np


@lru_cache(maxsize=2)
def upstream_functions(path):
    """Load only numeric functions/constants, excluding data/VLM imports."""
    path = Path(path) / "protracer/changepoint.py"
    if (
        hashlib.sha256(path.read_bytes()).hexdigest()
        != "88f599af3e78284b435544f535ef9ebf907ed83abe94d514f4044a5bf21d18cc"
    ):
        raise ValueError("Upstream Sign-CPD is not the reviewed pinned source")
    parsed = ast.parse(path.read_text(), filename=str(path))
    nodes = [
        n
        for n in parsed.body
        if isinstance(n, (ast.Assign, ast.FunctionDef, ast.ClassDef))
        or isinstance(n, ast.ImportFrom)
        and n.module == "__future__"
    ]
    namespace = {"np": np, "Episode": object}
    # Only the exact reviewed hash is loadable, and data/VLM imports are excluded.
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return namespace


def prefix_pelt_paths(symbols, cost, upstream, min_size):
    """Exact upstream PELT paths at each prefix, retaining its grid tie policy."""
    best = {0: (0.0, ())}
    starts = []
    last_grid = 0
    for n in range(1, len(symbols) + 1):
        # Only grid endpoints are reused. An odd terminal endpoint is transient.
        for end in range(last_grid + 2, n + 1, 2):
            last_grid = end
            if end < min_size:
                continue
            starts.append((end - min_size) // 2 * 2)
            options = [
                (best[s][0] + cost(s, end) + upstream["PENALTY"], s)
                for s in starts
                if s in best
            ]
            total, start = min(options, key=lambda o: o[0])
            best[end] = (total, best[start][1] + (end,))
            starts = [s for c, s in options if c <= total + upstream["PENALTY"]]
        if n < min_size:
            yield []
            continue
        if n % 2 == 0:
            yield list(best[n][1][:-1])
            continue
        candidates = starts + [(n - min_size) // 2 * 2]
        options = [
            (best[s][0] + cost(s, n) + upstream["PENALTY"], s)
            for s in candidates
            if s in best
        ]
        _, start = min(options, key=lambda o: o[0])
        yield list(best[start][1])


def score_sign_cpd(time, eef, robot, nominal_fit, upstream_path):
    """Cut count from the available prefix, never a backdated onset estimate.

    The only source changes are a train-success motion floor, common10Hz input,
    and prefix-only availability. Hamming cost, penalty, snapping, spacing and
    two-pass pruning remain pinned upstream functions/constants. Budget15 phases
    is fixed for all tasks; no released event determines a reset or schedule.
    """
    source = upstream_functions(str(upstream_path))
    if robot not in nominal_fit["robots"]:
        return np.full(len(time), np.nan)
    floor = nominal_fit["robots"][robot]["motion_floor"]
    eef = np.asarray(eef)
    valid = np.isfinite(eef).all(axis=1)
    # Initial unavailable delayed observations are not treated as real positions.
    indices = np.flatnonzero(valid)
    risk = np.full(len(time), np.nan)
    if not len(indices):
        return risk
    first = indices[0]
    x = eef[first:]
    if not np.isfinite(x).all():
        raise ValueError("Internal missing packets must be held causally")
    delta = np.vstack([np.zeros(16), np.diff(x, axis=0)])
    symbols = np.column_stack(
        [
            np.sign(delta[:, 7]),
            (delta[:, :3] ** 2).sum(1) > floor[0],
            np.sign(delta[:, 15]),
            (delta[:, 8:11] ** 2).sum(1) > floor[1],
        ]
    ).astype(int)
    cost = source["ModalHammingCost"](symbols)
    dt = 0.1
    frames = lambda seconds: max(1, round(seconds / dt))
    grip = np.max(np.abs(delta[:, [7, 15]]) / dt, axis=1)
    for index, cuts in enumerate(
        prefix_pelt_paths(
            symbols, cost, source, max(2, frames(source["MIN_SEGMENT_S"]))
        )
    ):
        n = index + 1
        snap = frames(source["SNAP_WINDOW_S"])
        snapped = set()
        for cut in cuts:
            c = min(cut - 1, n - 1)
            window = range(max(0, c - snap), min(n, c + snap + 1))
            snapped.add(min(window, key=lambda k: grip[k]))
        gap = frames(source["MIN_PHASE_S"])
        kept = []
        for c in sorted(snapped):
            if gap <= c <= n - gap and (not kept or c - kept[-1] >= gap):
                kept.append(c)
        kept = source["_prune"](kept, max(14, source["FIRST_PASS_CUTS"]), cost, n)
        kept = source["_prune"](kept, 14, cost, n, max_gap=frames(source["MAX_GAP_S"]))
        risk[first + index] = len(kept)
    return risk
