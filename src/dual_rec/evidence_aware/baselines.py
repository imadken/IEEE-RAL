"""Matched finite-cell adaptations, with explicit equivalences and controls."""

import numpy as np

from .bounds import qualifies
from .partition import route

DESCRIPTIONS = {
    "DSRE": "minimum whole-leaf conjunction + common bound",
    "ordinary_rules": "same grammar and same bound; exact action equivalence expected",
    "tabular_Kallus_adaptation": "finite-cell sharp partial identification; no compression",
    "Li_no_harm_adaptation": "finite-cell utility-maximizing no-harm policy; not original estimator reproduction",
    "CART2_matched": "observed-arm SSE tree shared with every method; utility proposal + same gate",
    "ensemble_matched": "16 bootstrap within-cell arm means; same partition and gate",
    "DISCRET_style_adaptation": "outcome subgroup utility proposal, same scope gate; not a DISCRET reproduction",
    "empirical_utility": "unqualified positive observed marginal gain; descriptive comparator",
    "naive_independence": "unsupported independence coupling with matched marginal CP intervals; negative control",
    "LTT_paired_adaptation": "common simultaneous paired observable-loss constraints; requires exposed pairs",
    "always_continue": "fixed c",
    "always_recover": "fixed r",
}


def proposals(partition, discovery):
    rng = np.random.default_rng(2026111701)
    output = {}
    for c in set(partition.cells):
        arms = [
            [
                int(r.y)
                for r in discovery
                if route(partition, r.x) == c and r.action == a
            ]
            for a in ("c", "r")
        ]
        means = [float(np.mean(v)) if v else None for v in arms]
        empirical = all(v is not None for v in means) and means[1] - means[0] >= 0.05
        ensemble = False
        if all(arms):
            gains = [
                np.mean(rng.choice(arms[1], len(arms[1])))
                - np.mean(rng.choice(arms[0], len(arms[0])))
                for _ in range(16)
            ]
            ensemble = float(np.mean(gains)) >= 0.05
        output[c] = {
            "utility": bool(empirical),
            "ensemble": ensemble,
            "naive": bool(empirical and means[0] * (1 - means[1]) <= 0.1),
        }
    return output


def decisions(leaf, bounds, proposed, paired=False, independence_pass=False):
    passed = leaf in bounds and qualifies(bounds[leaf])
    prop = proposed.get(leaf, {"utility": False, "ensemble": False, "naive": False})
    selected = {
        "DSRE": passed,
        "ordinary_rules": passed,
        "tabular_Kallus_adaptation": passed,
        "Li_no_harm_adaptation": passed,
        "CART2_matched": passed and prop["utility"],
        "ensemble_matched": passed and prop["ensemble"],
        "DISCRET_style_adaptation": passed and prop["utility"],
        "empirical_utility": prop["utility"],
        "naive_independence": prop["utility"] and independence_pass,
        "always_continue": False,
        "always_recover": True,
    }
    if paired:
        selected["LTT_paired_adaptation"] = passed
    return {k: "r" if v else "c" for k, v in selected.items()}
