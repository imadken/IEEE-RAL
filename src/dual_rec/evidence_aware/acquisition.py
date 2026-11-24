"""Freeze evidence-type allocations from an independent diagnostic pool."""

from .schema import Frozen


def decision_information_scores(p0, p1, n0, n1, requested_logs, requested_pairs):
    """Discovery-only gate uncertainty per next execution, for a fixed schedule.

    Singles reduce marginal standard errors. Pairs reduce the unresolved joint
    range, relevant only when the empirical useful-gain requirement is possible.
    Requested counts are planned counts, never subsequently revealed outcomes.
    This is a deterministic information heuristic, not a confidence statement.
    """
    marginal = (max(p0 * (1 - p0), 0.01) / (n0 + 1 + requested_logs / 2)) ** 0.5 + (
        max(p1 * (1 - p1), 0.01) / (n1 + 1 + requested_logs / 2)
    ) ** 0.5
    coupling = min(p0, 1 - p1) - max(0.0, p0 - p1)
    pair = coupling / (2 * (requested_pairs + 1)) if p1 - p0 >= 0.05 else 0.0
    return marginal, pair


class Allocation(Frozen):
    strategy: str
    executions: int
    requests: tuple[tuple[int, str], ...]
    unspent: int


def allocate(strategy, diagnostic, masses, budget):
    """Every request is one pair (cost 2) or one fair randomized log (cost 1).

    Leaves are visited by discovery mass, then round robin. Type choices use
    diagnostic evidence only; final calibration outcomes are never consulted.
    The uncertainty comparator is a declared heuristic, not an optimal design.
    """
    if budget < 0 or strategy not in (
        "witness",
        "all_logs",
        "all_pairs",
        "uniform_mix",
        "decision_uncertainty",
    ):
        raise ValueError("Unknown strategy or budget")
    leaves = sorted(masses, key=lambda c: (-masses[c], c))
    requests, spent, turn = [], 0, 0
    while leaves and spent < budget:
        c = leaves[turn % len(leaves)]
        status, width_h, width_g = diagnostic[c]
        pair = (
            strategy == "all_pairs"
            or (strategy == "witness" and status == "MARGINAL_IDENTIFICATION_BARRIER")
            or (strategy == "uniform_mix" and turn % 2 == 0)
            or (strategy == "decision_uncertainty" and width_h > width_g / 2)
        )
        cost = 2 if pair else 1
        if spent + cost > budget:
            pair, cost = False, 1
        requests.append((c, "pair" if pair else "log"))
        spent += cost
        turn += 1
    return Allocation(
        strategy=strategy,
        executions=spent,
        requests=tuple(requests),
        unspent=budget - spent,
    )
