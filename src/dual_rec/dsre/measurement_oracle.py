"""Independent box-corner enclosure and sampled-invariance regression oracle.

Does not import the production measurement adapter. Interval algebra plus the
triangle inequality is the proof; sampling is only an implementation regression.
"""

import math
import random
from itertools import product

from .features import feature_values
from .repair_selection import optional_values


def box_distance(a, b, rho):
    if a is None or b is None:
        return None
    low = [x - y - 2 * rho for x, y in zip(a, b, strict=True)]
    high = [x - y + 2 * rho for x, y in zip(a, b, strict=True)]
    nearest = [0 if l <= 0 <= h else min(abs(l), abs(h)) for l, h in zip(low, high)]
    minimum = math.sqrt(sum(x * x for x in nearest))
    maximum = max(
        math.sqrt(sum(x * x for x in corner))
        for corner in product(*zip(low, high, strict=True))
    )
    return minimum, maximum


def check_invariance(history, rho, evidence, draws=64, seed=2026111503):
    rng = random.Random(seed)
    expected = [f.invariant for f in evidence.facts]
    checks = 0
    if history.current.time < evidence.scope.decision_time - 1e-9:
        assert all(v is None for v in expected)
        return 12
    for _ in range(draws):
        frames = []
        for frame in (history.first, history.current):
            if frame is None:
                frames.append(None)
                continue
            update = {}
            for name in ("object_position", "tcp_position", "goal_position"):
                xyz = getattr(frame, name)
                update[name] = (
                    None
                    if xyz is None
                    else tuple(x + rng.uniform(-rho, rho) for x in xyz)
                )
            frames.append(frame.model_copy(update=update))
        sampled = history.model_copy(update={"first": frames[0], "current": frames[1]})
        point = feature_values(sampled) + optional_values(sampled)
        for robust, value in zip(expected, point, strict=True):
            if robust is not None:
                assert robust == value, (rho, expected, point)
                checks += 1
    # Production distance/progress enclosures must contain independently derived
    # coordinate-box extrema, even though the latter may be tighter.
    c, f = history.current, history.first
    distances = [
        box_distance(c.object_position, c.goal_position, rho),
        box_distance(c.tcp_position, c.object_position, rho),
    ]
    old = (
        box_distance(f.object_position, f.goal_position, rho)
        if f is not None and f.time < c.time
        else None
    )
    progress = (
        (old[0] - distances[0][1], old[1] - distances[0][0])
        if old is not None and distances[0] is not None
        else None
    )
    displacement = (
        box_distance(f.object_position, c.object_position, rho)
        if f is not None and f.time < c.time
        else None
    )
    for fact, interval in zip(
        evidence.facts[:4], [*distances, progress, displacement], strict=True
    ):
        if interval is not None:
            assert fact.lower <= interval[0] + 1e-12
            assert fact.upper >= interval[1] - 1e-12
            checks += 2
    return checks
