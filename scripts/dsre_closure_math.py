"""E0/E4 mathematical obligations, independent LPs and constructive falsifiers."""

import itertools

import numpy as np
from dsre_closure_common import ROOT, b7_certificate, cp, lp, passed, save
from dsre_closure_evaluate import independent_extrema
from scipy.stats import binom

from dual_rec.evidence_aware.bounds import solve
from dual_rec.evidence_aware.schema import Evidence


def exact(p0, p1):
    return {
        "p0": {"lo": p0, "hi": p0},
        "p1": {"lo": p1, "hi": p1},
        "source_type": "randomized_single_action",
        "scope": "ANALYTICAL",
    }


def admissible(q, e):
    q = np.asarray(q)
    assert q.min() >= -1e-9 and abs(sum(q) - 1) < 1e-9
    for name, value in [
        ("p0", q[2] + q[3]),
        ("p1", q[1] + q[3]),
        ("harm", q[2]),
        ("rescue", q[1]),
    ]:
        if e.get(name) is not None:
            assert e[name]["lo"] - 1e-9 <= value <= e[name]["hi"] + 1e-9


def main():
    max_error = 0.0
    cases = 0
    for p0, p1 in itertools.product(np.linspace(0, 1, 41), repeat=2):
        e = exact(float(p0), float(p1))
        independent = lp(e)
        production = solve(Evidence.model_validate(e))
        target = {
            "harm_lower": max(0, p0 - p1),
            "harm_upper": min(p0, 1 - p1),
            "gain_lower": p1 - p0,
            "gain_upper": p1 - p0,
            "failure_upper": 1 - p1,
        }
        for field, value in target.items():
            max_error = max(
                max_error,
                abs(independent[field] - value),
                abs(getattr(production, field) - value),
            )
            admissible(independent["optimizers"][field], e)
        assert passed(independent, "useful") == bool(
            p1 - p0 >= 0.05 - 1e-12 and (p0 <= 0.1 + 1e-12 or p1 >= 0.9 - 1e-12)
        )
        cases += 1
    rng = np.random.default_rng(2026111807)
    refinements = 0
    for _ in range(128):
        q = rng.dirichlet(np.ones(4))
        p0, p1 = q[2] + q[3], q[1] + q[3]
        e = {
            "p0": {"lo": max(0, p0 - 0.12), "hi": min(1, p0 + 0.12)},
            "p1": {"lo": max(0, p1 - 0.12), "hi": min(1, p1 + 0.12)},
            "scope": "ANALYTICAL",
            "source_type": "randomized_single_action",
        }
        a = lp(e)
        e2 = dict(
            e,
            source_type="qualified_simulator_pair",
            harm={"lo": max(0, q[2] - 0.02), "hi": min(1, q[2] + 0.02)},
            rescue={"lo": max(0, q[1] - 0.02), "hi": min(1, q[1] + 0.02)},
        )
        b = lp(e2)
        for name in (
            "harm_lower",
            "harm_upper",
            "gain_lower",
            "gain_upper",
            "failure_upper",
        ):
            max_error = max(
                max_error,
                abs(b[name] - getattr(solve(Evidence.model_validate(e2)), name)),
            )
            admissible(b["optimizers"][name], e2)
        assert (
            b["harm_upper"] <= a["harm_upper"] + 1e-10
            and b["gain_lower"] >= a["gain_lower"] - 1e-10
        )
        assert abs(a["harm_upper"] - min(e["p0"]["hi"], 1 - e["p1"]["lo"])) < 1e-10
        assert abs(a["gain_lower"] - (e["p1"]["lo"] - e["p0"]["hi"])) < 1e-10
        refinements += 1
    cp_checks = 0
    for k_leaves in (1, 2, 4):
        tail = 0.025 / (4 * k_leaves)
        for n in range(1, 13):
            intervals = [cp(k, n, tail) for k in range(n + 1)]
            for p in np.linspace(0, 1, 41):
                coverage = sum(
                    binom.pmf(k, n, p)
                    for k, band in enumerate(intervals)
                    if band["lo"] - 1e-12 <= p <= band["hi"] + 1e-12
                )
                assert coverage >= 1 - 2 * tail - 1e-10
                cp_checks += 1
    worlds = [[0.4, 0.2, 0, 0.4], [0, 0.6, 0.4, 0]]
    for q in worlds:
        admissible(q, exact(0.4, 0.6))
    assert worlds[0][2] <= 0.1 < worlds[1][2]
    _low, high = independent_extrema((0.2, 0.6))
    assert 0.2 * (1 - 0.6) <= 0.1 and high[2] > 0.1
    # A union may meet an AVERAGE obligation even when one component lacks
    # benefit. Whole-leaf uniform qualification is sufficient, not necessary.
    partition = {
        "vocabulary": ["fact"],
        "cells": [0, 1],
        "tree": [0, -1, -1],
        "discovery_parents": [],
    }
    leaves = {
        str(i): {"bounds": lp(exact(*p)), "evidence": exact(*p)}
        for i, p in enumerate([(0, 1), (1, 1)])
    }
    model = {"partition": partition, "source_scope": {}, "leaves": leaves}
    certificate = b7_certificate(model, (False,), "useful")
    assert len(certificate["evidence"]) == 1
    pooled = lp(exact(0.5, 1))
    assert passed(pooled, "useful") and not passed(leaves["1"]["bounds"], "useful")
    subgroup = np.array([0.2, 0, 0.8, 0])
    complement = np.array([0.7, 0.3, 0, 0])
    whole = 0.1 * subgroup + 0.9 * complement
    for q in (subgroup, complement, whole):
        admissible(q, exact(q[2] + q[3], q[1] + q[3]))
    assert passed(lp(exact(whole[2] + whole[3], whole[1] + whole[3])), "useful")
    assert subgroup[2] > 0.1 and subgroup[1] - subgroup[2] < 0.05
    guards = {}
    for label, e in [
        (
            "confounded_observational",
            dict(exact(0.2, 0.8), source_type="uncontrolled_observational"),
        ),
        ("no_overlap", dict(exact(0.2, 0.8), overlap=False)),
        ("unqualified_pair", dict(exact(0.2, 0.8), harm={"lo": 0.0, "hi": 0.1})),
        (
            "inconsistent",
            dict(
                exact(0, 1),
                source_type="qualified_simulator_pair",
                harm={"lo": 0.5, "hi": 0.6},
            ),
        ),
    ]:
        try:
            lp(e)
        except ValueError as error:
            guards[label] = str(error)
        else:
            raise AssertionError(label)
    assert max_error < 1e-10
    save(
        ROOT / "E0/math_audit.json",
        {
            "passed": True,
            "exact_marginal_cases": cases,
            "paired_refinement_cases": refinements,
            "binomial_coverage_regressions": cp_checks,
            "maximum_error": max_error,
            "analytical_same_marginal_worlds": {
                "type": "ANALYTICAL_NOT_ROBOT_EPISODES",
                "q": worlds,
                "p0": 0.4,
                "p1": 0.6,
                "gain": 0.2,
                "harms": [0, 0.4],
            },
            "naive_independence_false_certificate": {
                "type": "ANALYTICAL",
                "p0": 0.2,
                "p1": 0.6,
                "assumed_harm": 0.08,
                "admissible_harm": high[2],
                "world": high,
            },
            "cellwise_sufficiency_not_necessity": {
                "type": "ANALYTICAL",
                "component_marginals": [[0, 1], [1, 1]],
                "component_q": [[0, 1, 0, 0], [0, 0, 0, 1]],
                "mixture_q": [0, 0.5, 0, 0.5],
                "fixed_mixture": [0.5, 0.5],
                "pooled_gain": 0.5,
                "pooled_harm": 0,
                "component_1_gain": 0,
                "conclusion": "The frozen all-leaf criterion rejects an empty conjunction despite a qualifying fixed-weight union. Minimum means minimum in the registered cellwise grammar, not universal population-average necessity.",
            },
            "scope_subgroup_counterexample": {
                "type": "ANALYTICAL",
                "subgroup_mass": 0.1,
                "subgroup_harm": 0.8,
                "remaining_harm": 0,
                "parent_harm": 0.08,
                "subgroup_q": subgroup.tolist(),
                "remaining_q": complement.tolist(),
                "parent_q": whole.tolist(),
                "parent_useful_log_qualified": True,
                "scope": "An entirely admissible whole-cell population passes both primary constraints while its selected subgroup violates both",
            },
            "expected_fail_closed_guards": guards,
        },
    )
    print(
        "Mathematical audit passed",
        cases,
        "exact marginals; max error",
        max_error,
        flush=True,
    )


if __name__ == "__main__":
    main()
