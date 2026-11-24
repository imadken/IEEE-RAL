"""Exact minimum experiment-type cover for a declared finite world catalogue.

No simulator, observed outcome, statistical confidence fit or reference solver
is imported. Unequal likelihoods are compared with exact rational arithmetic.
"""

from fractions import Fraction
from itertools import combinations

from .experiment_schema import (
    EqualLaw,
    ExperimentPlan,
    ExperimentProblem,
    ImpossibilityWitness,
    PairCoverage,
    RemovalWitness,
)


def minimum_resolving_experiments(problem: ExperimentProblem) -> ExperimentPlan:
    worlds = sorted(problem.worlds, key=lambda w: w.world_id)
    experiments = sorted(problem.experiments, key=lambda e: e.experiment_id)
    pairs = tuple(
        (a, b)
        for a, b in combinations(worlds, 2)
        if a.obligation_verdict != b.obligation_verdict
    )
    laws = {
        e.experiment_id: {row.world_id: row.probabilities for row in e.laws}
        for e in experiments
    }
    masks = {
        e.experiment_id: sum(
            1 << j
            for j, (a, b) in enumerate(pairs)
            if laws[e.experiment_id][a.world_id] != laws[e.experiment_id][b.world_id]
        )
        for e in experiments
    }
    target = (1 << len(pairs)) - 1
    available = 0
    for mask in masks.values():
        available |= mask
    if available != target:
        a, b = next(pair for j, pair in enumerate(pairs) if not available & (1 << j))
        witness = ImpossibilityWitness(
            worlds=(a.world_id, b.world_id),
            verdicts=(a.obligation_verdict, b.obligation_verdict),
            identical_laws=tuple(
                EqualLaw(
                    experiment_id=e.experiment_id,
                    alphabet=e.alphabet,
                    probabilities=laws[e.experiment_id][a.world_id],
                )
                for e in experiments
            ),
        )
        return ExperimentPlan(
            status="NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE",
            cost_unit=problem.cost_unit,
            opposite_verdict_pairs=len(pairs),
            impossibility=witness,
        )

    # A state retains the best 0/1 subset achieving EXACTLY this coverage.
    best: dict[int, tuple[Fraction, int, tuple[str, ...]]] = {0: (Fraction(0), 0, ())}
    for experiment in experiments:
        for covered, (cost, count, selected) in tuple(best.items()):
            extended = covered | masks[experiment.experiment_id]
            proposal = (
                cost + experiment.cost,
                count + 1,
                selected + (experiment.experiment_id,),
            )
            if extended not in best or proposal < best[extended]:
                best[extended] = proposal
    cost, _, selected = best[target]
    coverage = tuple(
        PairCoverage(
            worlds=(a.world_id, b.world_id),
            experiments=tuple(e for e in selected if masks[e] & (1 << j)),
        )
        for j, (a, b) in enumerate(pairs)
    )
    removals = []
    for removed in selected:
        remaining = 0
        for e in selected:
            if e != removed:
                remaining |= masks[e]
        index = next(j for j in range(len(pairs)) if not remaining & (1 << j))
        a, b = pairs[index]
        removals.append(
            RemovalWitness(
                removed_experiment=removed,
                unseparated_opposing_worlds=(a.world_id, b.world_id),
            )
        )
    return ExperimentPlan(
        status="MINIMUM_RESOLVING_MENU",
        selected_experiments=selected,
        total_cost=cost,
        cost_unit=problem.cost_unit,
        opposite_verdict_pairs=len(pairs),
        coverage=coverage,
        removal_witnesses=tuple(removals),
        dynamic_programming_states=len(best),
        unanimous_catalogue_verdict=worlds[0].obligation_verdict if not pairs else None,
    )
