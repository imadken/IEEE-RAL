"""Independent count, binomial inversion and grouped-resampling audit.

Reads frozen outputs only; imports neither production inference nor physics.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import binom


def read(p):
    return json.loads(p.read_text())


def cp(k, n, tail):
    low = (
        0.0
        if k == 0
        else float(brentq(lambda p: binom.sf(k - 1, n, p) - tail, 0, 1, xtol=1e-14))
    )
    high = (
        1.0
        if k == n
        else float(brentq(lambda p: binom.cdf(k, n, p) - tail, 0, 1, xtol=1e-14))
    )
    return low, high


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    a = p.parse_args()
    root = a.root
    rows = {r["parent_id"]: r for r in read(root / "evaluator/evaluation_pairs.json")}
    counts = 0
    intervals = 0
    bands = 0
    error = 0.0
    for regime in (
        "logged",
        "paired_equal_parent",
        "paired_equal_execution",
        "observational",
    ):
        m = read(root / "models" / (regime + ".json"))
        evaluated = read(root / "evaluations" / (regime + ".json"))
        ids = [r["parent_id"] for r in m["decisions"]]
        n = len(ids)
        assert n == len(rows) == 314 and len(set(ids)) == n
        resamples = np.random.Generator(np.random.PCG64(2026111702)).integers(
            0, n, size=(2000, n)
        )
        weights = np.asarray([np.bincount(draw, minlength=n) for draw in resamples])
        for policy, reported in evaluated["policies"].items():
            matrix = []
            for decision in m["decisions"]:
                raw = rows[decision["parent_id"]]
                c = int(raw["yc"])
                r = int(raw["yr"])
                recover = decision["actions"][policy] == "r"
                y = r if recover else c
                matrix.append(
                    [
                        recover,
                        y,
                        y - c,
                        recover * c * (1 - r),
                        recover * (1 - c) * r,
                        recover * (1 - c) * (1 - r),
                    ]
                )
            array = np.asarray(matrix, dtype=int)
            totals = array.sum(axis=0)
            for field, index in (
                ("recover", 0),
                ("success", 1),
                ("harmful_authorizations", 3),
                ("rescues_selected", 4),
                ("futile_recoveries", 5),
            ):
                assert reported[field] == int(totals[index])
                counts += 1
            assert abs(reported["whole_policy_gain"] - totals[2] / n) < 1e-14
            boot = (weights @ array[:, 2]) / n
            expected = np.percentile(boot, [2.5, 97.5])
            actual = reported["gain_parent_bootstrap95"]
            assert np.max(np.abs(expected - actual)) < 1e-12
            intervals += 2
            lo, hi = cp(int(totals[3]), int(totals[0]), 0.025)
            error = max(
                error,
                abs(lo - reported["harm_parent_CP95"]["lo"]),
                abs(hi - reported["harm_parent_CP95"]["hi"]),
            )
            assert error < 1e-10
            intervals += 2
        for c, leaf in m["leaves"].items():
            ledger = leaf["ledger"]
            assert ledger["per_tail"] == 0.025 / (4 * ledger["K"])
            source = m["input_whitelist_sha256"]
            logs = read(next(Path(p) for p in source if "/learner/calibration" in p))

            def cell(x, cells=m["partition"]["cells"]):
                return cells[sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))]

            logs = [r for r in logs if cell(r["x"]) == int(c)]
            assert all(
                not r["counterpart_exposed"] and r["propensity"] == 0.5 for r in logs
            )
            assert all(
                not {"yc", "yr", "seed", "condition", "fault", "unassigned_outcome"}
                & set(r)
                for r in logs
            )
            for action, name in (("c", "p0"), ("r", "p1")):
                values = [r["y"] for r in logs if r["action"] == action]
                lo, hi = cp(sum(values), len(values), ledger["per_tail"])
                actual = leaf["evidence"][name]
                assert max(abs(lo - actual["lo"]), abs(hi - actual["hi"])) < 1e-10
                bands += 1
            pair_paths = [Path(p) for p in source if "/paired_refinement/" in p]
            if pair_paths:
                pairs = [r for r in read(pair_paths[0]) if cell(r["x"]) == int(c)]
                assert len(pairs) == ledger["counts_c_r_pair"][2]
                for name in ("harm", "rescue"):
                    successes = sum(
                        (r["yc"] and not r["yr"])
                        if name == "harm"
                        else (not r["yc"] and r["yr"])
                        for r in pairs
                    )
                    lo, hi = cp(successes, len(pairs), ledger["per_tail"])
                    actual = leaf["evidence"][name]
                    assert max(abs(lo - actual["lo"]), abs(hi - actual["hi"])) < 1e-10
                    bands += 1
    report = {
        "passed": True,
        "independent_integer_totals_checked": counts,
        "parent_interval_endpoints_checked": intervals,
        "marginal_CP_bands_checked": bands,
        "maximum_binomial_inversion_error": error,
        "production_inference_or_simulator_imported": False,
    }
    target = root / "independent_statistical_audit.json"
    with target.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
