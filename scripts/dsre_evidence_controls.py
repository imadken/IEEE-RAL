"""Record production controls and constructive examples; no physics or fitting."""

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from dual_rec.evidence_aware.bounds import cp, solve
from dual_rec.evidence_aware.diagnosis import (
    diagnose,
    observation_aliasing,
    repertoire_failure,
)
from dual_rec.evidence_aware.schema import Band, Evidence, Pair, Source
from dual_rec.evidence_aware.views import save


def exact(p0, p1, **kwargs):
    return Evidence(
        p0=Band(lo=p0, hi=p0), p1=Band(lo=p1, hi=p1), scope="finite control", **kwargs
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    a = p.parse_args()
    maximum = 0.0
    for p0, p1 in itertools.product(np.linspace(0, 1, 21), repeat=2):
        b = solve(exact(p0, p1))
        maximum = max(
            maximum,
            abs(b.harm_lower - max(0, p0 - p1)),
            abs(b.harm_upper - min(p0, 1 - p1)),
            abs(b.gain_lower - (p1 - p0)),
        )
    pairs = [
        Pair.model_validate(r)
        for phase in ("discovery", "calibration", "evaluation")
        for r in json.loads(
            (a.root / "historical/evaluator" / (phase + "_pairs.json")).read_text()
        )
    ]
    alias = observation_aliasing(pairs)
    neither = next(repertoire_failure(r) for r in pairs if not r.yc and not r.yr)
    worlds = diagnose(exact(0.4, 0.6))
    controls = {
        "grid_cases": 441,
        "maximum_analytic_error": maximum,
        "two_worlds": worlds.model_dump(mode="json"),
        "marginals_suffice": solve(exact(0.05, 0.7)).model_dump(mode="json"),
        "independence_counterexample": {
            "q": [0.2, 0.6, 0.2, 0],
            "independent_harm": 0.08,
            "actual_harm": 0.2,
            "gain": 0.4,
        },
        "subgroup_counterexample": {
            "whole_harm": 0.08,
            "subset_mass": 0.1,
            "subset_harm": 0.8,
        },
        "unsupported_source": diagnose(
            exact(0.4, 0.6, source_type=Source.OBSERVATIONAL)
        ).model_dump(mode="json"),
        "no_overlap": diagnose(exact(0, 1, overlap=False)).model_dump(mode="json"),
        "inconsistent": diagnose(
            exact(0, 1, source_type=Source.PAIRED, harm=Band(lo=0.5, hi=0.6))
        ).model_dump(mode="json"),
        "neither_action": neither.model_dump(mode="json"),
        "observation_aliasing": alias.model_dump(mode="json") if alias else None,
        "zero_error_upper_n64_K4": cp(0, 64, 0.025 / 16).hi,
        "scope_note": "Constructed probability controls are mathematical tests. Paired checkpoint witnesses are historical DEVELOPMENT examples, never hidden learner inputs.",
    }
    save(a.root / "production_controls.json", controls)


if __name__ == "__main__":
    main()
