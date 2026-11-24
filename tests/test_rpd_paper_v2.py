"""Independent checks for the proposed paper's analytical and statistical claims."""

import math

import numpy as np
import pytest
import rpd_paper_v2_checks as checks
from rpd_independent_oracle import all_policy_trees, rollout
from scipy.optimize import minimize_scalar
from scipy.special import xlogy
from scipy.stats import chi2


def test_equal_duration_model_exposes_partial_and_full_loss_without_reset():
    raw = checks.illustration().model_dump(mode="json")
    states = {s["state_id"]: s for s in raw["states"]}
    options = {
        s: {r["action_id"] for r in v["recoveries"] if r["task_success"]}
        for s, v in states.items()
    }
    assert options["BH"] == {"a0", "a1"} and options["BF"] == {"a1"}
    assert options["CH"] == {"a1"} and not options["CF"]
    assert all(s["physically_allowed"] for s in states.values())
    assert {p["cost"] for p in raw["probes"]} == {"1/2"}
    by_probe = {}
    for tree in all_policy_trees(raw):
        if tree[0] != "PROBE":
            continue
        score = sum(rollout(raw, tree, s)[0] for s in raw["initial_support"]) / 3
        by_probe[tree[1]] = max(score, by_probe.get(tree[1], 0))
    assert by_probe == {"hold": 2 / 3, "p1_fine": 2 / 3, "p2_coarse": 1}


@pytest.mark.parametrize(
    "plus,minus", [(76, 26), (60, 30), (110, 12), (0, 0), (512, 0), (270, 242), (40, 0)]
)
def test_profile_boundary_against_independent_numerical_likelihood(plus, minus):
    n, margin = 512, 0.05
    ties = n - plus - minus

    def negative_ll(q):
        return -float(
            xlogy(plus, q + margin) + xlogy(minus, q) + xlogy(ties, 1 - 2 * q - margin)
        )

    fit = minimize_scalar(
        negative_ll,
        bounds=(0, (1 - margin) / 2),
        method="bounded",
        options={"xatol": 1e-13},
    )
    best = min(fit.fun, negative_ll(0), negative_ll((1 - margin) / 2))
    unconstrained = sum(float(xlogy(k, k / n)) for k in (plus, minus, ties))
    if plus + minus >= 30:
        expected = (plus - minus) / n > margin and 2 * (
            unconstrained + best
        ) > chi2.ppf(0.95, 1)
    else:
        expected = (
            checks.lower(plus, n, 0.0125) - checks.upper(minus, n, 0.0125) > margin
        )
    assert bool(checks.paired_profile_test(plus, minus, n)[0]) == expected


def test_rare_discordance_does_not_imply_equality():
    assert checks.upper(0, 512, 0.0125) > 0
    assert not checks.paired_profile_test(0, 0, 512)[0]


def test_exact_binomial_supporting_and_excluding_counts():
    assert checks.lower(65, 512, 0.025) < 0.10 < checks.lower(66, 512, 0.025)
    assert checks.upper(0, 512, 0.025) == pytest.approx(1 - math.pow(0.025, 1 / 512))


def test_reproduction_refuses_existing_outputs(tmp_path):
    with pytest.raises(AssertionError, match="Fresh offline output"):
        checks.run(tmp_path)


def test_no_simulator_construction_in_paper_checks():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(checks.__file__).read_text())
    imports = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert all(
        not (name or "").startswith(("mani_skill", "sapien", "gymnasium"))
        for name in imports
    )
    assert np.isclose(math.log(3), 1.0986122886681098)


def test_preservation_keeps_user_deleted_paths_absent(tmp_path):
    from rpd_paper_v2_receipt import matches_snapshot, sha

    path = tmp_path / "user_moved_document.md"
    assert matches_snapshot(path, None)
    path.write_text("user content")
    assert not matches_snapshot(path, None)
    expected = sha(path)
    assert matches_snapshot(path, expected)
    path.write_text("different content")
    assert not matches_snapshot(path, expected)
    path.unlink()
    assert not matches_snapshot(path, expected)
