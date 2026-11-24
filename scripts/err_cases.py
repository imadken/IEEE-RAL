"""Registered analytical fixtures and exact, source-explicit likelihoods."""

from fractions import Fraction
from itertools import product

from dual_rec.evidence_aware.experiment_schema import (
    ExperimentProblem,
    World,
    verdict,
)


def source(
    kind="abstract_known_law", population="ANALYTICAL_FINITE_WORLD_STUDY", **extra
):
    result = {
        "kind": kind,
        "population_id": population,
        "provenance": ("Declared exact finite model; no observed robot episodes",),
        "assumptions": (
            "Known exact likelihoods",
            "Complete declared finite catalogue",
            "Conditional product observation laws",
        ),
        "qualified": True,
        "participant_selection": "FIXED_BEFORE_OUTCOMES",
        "participant_sampling": "DECLARED_ANALYTICAL",
        "law_origin": "KNOWN_ANALYTICAL_MODEL",
        "context_operation": "FIXED_OUTCOME_TARGET",
    }
    result.update(extra)
    return result


def problem(
    worlds,
    experiments,
    obligation="declared_predicate",
    population="ANALYTICAL_FINITE_WORLD_STUDY",
    cost_unit="DECLARED_EXPERIMENT_TYPE_UNITS",
):
    return ExperimentProblem(
        population_id=population,
        obligation=obligation,
        predicate_description="Fixed registered finite predicate; no continuous-population extrapolation",
        catalogue_scope="DECLARED_FINITE_CATALOGUE",
        complete_for_declared_finite_catalogue=True,
        cross_experiment_law="CONDITIONAL_PRODUCT_LAWS",
        cost_unit=cost_unit,
        worlds=tuple(worlds),
        experiments=tuple(experiments),
    )


def from_signatures(labels, signatures, costs, *, names=None):
    """Each signature row is a normalized PMF, not a realized outcome."""
    names = names or [f"e{j}" for j in range(len(costs))]
    worlds = [
        {"world_id": f"w{i}", "obligation_verdict": bool(label)}
        for i, label in enumerate(labels)
    ]
    experiments = []
    for j, name in enumerate(names):
        experiments.append(
            {
                "experiment_id": name,
                "cost": costs[j],
                "alphabet": tuple(str(k) for k in range(len(signatures[j][0]))),
                "laws": tuple(
                    {"world_id": f"w{i}", "probabilities": tuple(p)}
                    for i, p in enumerate(signatures[j])
                ),
                "source": source(),
            }
        )
    return problem(worlds, experiments)


def causal_worlds(joints, obligation="useful", *, paired=True, conditional_arms=True):
    joints = [tuple(Fraction(v) for v in q) for q in joints]
    worlds = [
        World(world_id=name, obligation_verdict=verdict(q, obligation), joint=q)
        for name, q in zip((f"Q{i}" for i in range(len(joints))), joints, strict=True)
    ]
    experiments = []
    for action in ("c", "r") if conditional_arms else ():
        laws = []
        for world in worlds:
            q = world.joint
            p = q[2] + q[3] if action == "c" else q[1] + q[3]
            laws.append(
                {
                    "world_id": world.world_id,
                    "probabilities": (Fraction(1, 2), (1 - p) / 2, p / 2),
                }
            )
        experiments.append(
            {
                "experiment_id": f"{action}_log",
                "cost": 1,
                "alphabet": ("other_arm", "0", "1"),
                "laws": laws,
                "source": source("randomized_arm", action=action, propensity="1/2"),
            }
        )
    experiments.append(
        {
            "experiment_id": "randomized_log",
            "cost": 1,
            "alphabet": ("c0", "c1", "r0", "r1"),
            "laws": [
                {
                    "world_id": w.world_id,
                    "probabilities": tuple(
                        x / 2
                        for x in (
                            1 - w.joint[2] - w.joint[3],
                            w.joint[2] + w.joint[3],
                            1 - w.joint[1] - w.joint[3],
                            w.joint[1] + w.joint[3],
                        )
                    ),
                }
                for w in worlds
            ],
            "source": source("randomized_single_action", propensity="1/2"),
        }
    )
    if paired:
        experiments.append(
            {
                "experiment_id": "paired_trial",
                "cost": 2,
                "alphabet": ("00", "01", "10", "11"),
                "laws": [
                    {"world_id": w.world_id, "probabilities": w.joint} for w in worlds
                ],
                "source": source(
                    "qualified_simulator_pair",
                    coupling="Declared joint simulator-model coupling; not a hardware counterfactual",
                ),
            }
        )
    return problem(
        worlds,
        experiments,
        obligation=obligation,
        cost_unit="OUTCOMES_PER_EXPERIMENT_TYPE_NOT_TOTAL_REQUIRED_SAMPLES",
    )


def registered_cases():
    pair = [("2/5", "1/5", "0", "2/5"), ("0", "3/5", "2/5", "0")]
    cases = {
        "same_marginals_with_pair": causal_worlds(pair),
        "same_marginals_unpaired_only": causal_worlds(pair, paired=False),
        "same_marginals_absolute_refuted": causal_worlds(pair, obligation="completion"),
    }
    three = pair + [("0", "1/100", "0", "99/100")]
    for o in ("harm_only", "completion", "useful"):
        cases[f"obligation_shift_three_worlds_{o}"] = causal_worlds(three, obligation=o)
    epsilon = Fraction(1, 10**13)
    near = [
        (Fraction(2, 5) - h, Fraction(1, 5) + h, h, Fraction(2, 5) - h)
        for h in (Fraction(1, 10) - epsilon, Fraction(1, 10) + epsilon)
    ]
    cases["reference_rounding_trap"] = causal_worlds(near)
    one = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
    covers = [{1, 2, 3, 4}, {1, 2, 5}, {3, 4, 6}]
    signatures = [[one[int(i in cover)] for i in range(7)] for cover in covers]
    cases["greedy_cover_counterexample"] = from_signatures(
        [True] + [False] * 6, signatures, [2, 2, 2], names=["A", "B", "C"]
    )
    xor = [
        [one[int(i in covered)] for i in range(4)]
        for covered in ({1, 2}, {1, 3}, {2, 3})
    ]
    cases["supervisor_two_cheap_sources"] = from_signatures(
        [True, True, False, False], xor, [1, 1, 4], names=["x", "y", "oracle"]
    )
    cases["zero_cost_required_and_redundant"] = from_signatures(
        [True, False], [[one[0], one[1]]] * 3, [0, 0, 2], names=["A", "B", "C"]
    )
    cases["cost_priority_before_cardinality"] = from_signatures(
        [True, False, False],
        [[one[0], one[1], one[0]], [one[0], one[0], one[1]], [one[0], one[1], one[1]]],
        ["1/3", "1/3", 1],
        names=["cheapA", "cheapB", "single"],
    )
    cases["finite_sample_overlap"] = from_signatures(
        [True, False],
        [
            [
                (Fraction(1, 2), Fraction(1, 2)),
                (Fraction(1, 2) + epsilon, Fraction(1, 2) - epsilon),
            ]
        ],
        [1],
    )
    cases["fractional_cost_tolerance_trap"] = from_signatures(
        [True, False],
        [[one[0], one[1]], [one[0], one[1]]],
        [1, 1 - Fraction(1, 10**30)],
        names=["A", "B"],
    )
    cases["unanimous_true_is_not_population_certificate"] = from_signatures(
        [True, True], [[one[0], one[1]]], [1]
    )
    cases["opposing_empty_menu"] = from_signatures([True, False], [], [])
    return cases


def exhaustive_binary_cases():
    """All labelled deterministic binary models in the registered finite grids."""
    for n, menus in [(2, (1, 2, 3)), (3, (1, 2, 3)), (4, (1, 2))]:
        for m in menus:
            for labels in product((False, True), repeat=n):
                if len(set(labels)) < 2:
                    continue
                for bits in product((False, True), repeat=n * m):
                    signatures = [
                        [
                            (int(not bits[j * n + i]), int(bits[j * n + i]))
                            for i in range(n)
                        ]
                        for j in range(m)
                    ]
                    for costs in product((0, 1), repeat=m):
                        yield n, m, labels, bits, costs, signatures
