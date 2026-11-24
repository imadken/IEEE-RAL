"""Minimum literal count with exact whole-leaf population scope."""

from itertools import combinations

from .bounds import qualifies
from .partition import assignments, route
from .schema import Bounds, Certificate, Partition, Scope, Source


def selected_scope(partition: Partition, query, subset):
    by_cell = {}
    for x, leaf in zip(assignments(len(query)), partition.cells, strict=True):
        selected = all(x[j] == query[j] for j in subset)
        by_cell.setdefault(leaf, set()).add(selected)
    if any(len(v) != 1 for v in by_cell.values()):
        return None
    return tuple(sorted(c for c, flags in by_cell.items() if True in flags))


def minimum(
    partition: Partition,
    query,
    bounds: dict[int, Bounds],
    source: Source,
    obligation="useful",
    toll=0.0,
    *,
    outcome_scope: Scope,
) -> Certificate | None:
    current = route(partition, query)
    approved = {c for c, b in bounds.items() if qualifies(b, obligation, toll)}
    if current is None or current not in approved:
        return None
    for size in range(len(query) + 1):
        for subset in combinations(range(len(query)), size):
            scope = selected_scope(partition, query, subset)
            if not scope or current not in scope or not set(scope) <= approved:
                continue
            removals = {}
            for literal in subset:
                reduced = tuple(j for j in subset if j != literal)
                other = selected_scope(partition, query, reduced)
                removals[partition.vocabulary[literal]] = (
                    "conjunction splits a calibrated leaf"
                    if other is None
                    else "unqualified leaves admitted: "
                    + str(sorted(set(other) - approved))
                )
            return Certificate(
                obligation=obligation,
                evidence=tuple(
                    (partition.vocabulary[j], bool(query[j])) for j in subset
                ),
                selected_leaf_scope=scope,
                harm_upper=max(bounds[c].harm_upper for c in scope),
                gain_lower=min(bounds[c].gain_lower for c in scope),
                failure_upper=max(bounds[c].failure_upper for c in scope),
                source_type=source,
                outcome_scope=outcome_scope,
                confidence_family="per-task .025 logged + .025 paired, simultaneous frozen leaves",
                assumptions=(
                    "independent parents",
                    "stationary observation protocol",
                    "fixed macros",
                    "randomized assignment and overlap",
                    "discovery independent of calibration",
                ),
                removal_witnesses=removals,
            )
    return None
