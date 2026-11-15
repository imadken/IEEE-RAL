"""Independent raw-label population and fixed-composition numerical audit."""

import argparse
import time
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read
from dsre_recovery_audit import gz
from scipy.stats import beta

from dual_rec.dsre.operational import METHODS


def audit(root):
    results = read(root / "test_analysis.json")
    secondary = read(root / "stop_sensitivity.json")
    records = read(root / "test_records.json")
    base = [
        r for r in records if r["method"] == "DSRE_risk" and r["mode"] == "calibrated"
    ]
    ids = [r["id"] for r in base]
    truth = []
    initial = []
    for key in ids:
        _, seed, condition = key.split("/")
        d = root / "test" / seed / condition
        truth.append(
            [
                bool(gz(d / (a + ".json.gz"))["frames"][-1]["state"]["success"])
                for a in ("continue", "recover")
            ]
        )
        initial.append(bool(gz(d / "screen.json.gz")["canonical_start"]["success"]))
    truth = np.asarray(truth)
    initial = np.asarray(initial)
    ronly = ~truth[:, 0] & truth[:, 1]
    required = ronly & ~initial
    groups = sorted({r["group"] for r in base})
    parent = np.asarray([groups.index(r["group"]) for r in base])
    n = len(groups)
    draws = np.random.Generator(np.random.PCG64(2026111501)).integers(n, size=(4000, n))
    weights = np.array([np.bincount(x, minlength=n) for x in draws])
    checks = 0

    def interval(values, denominator, reported):
        nonlocal checks
        v = np.bincount(parent, weights=values, minlength=n)
        d = np.bincount(parent, weights=denominator, minlength=n)
        assert reported["denominator"] == int(d.sum())
        if not d.sum():
            assert reported["estimate"] is None
            checks += 1
            return
        num = weights @ v
        den = weights @ d
        good = den > 0
        ci = np.percentile(num[good] / den[good], [2.5, 97.5])
        assert abs(reported["estimate"] - v.sum() / d.sum()) < 1e-12
        assert np.allclose(
            ci, [reported["lower"], reported["upper"]], atol=1e-12, rtol=0
        )
        checks += 1

    scores = {}
    assignment = read(root / "test_assignment_errors.json")
    strata = 0
    for mode in ("proposal", "calibrated"):
        for m in METHODS:
            rs = [r for r in records if r["method"] == m and r["mode"] == mode]
            assert [r["id"] for r in rs] == ids
            selected = np.array(
                [{None: -1, "continue": 0, "recover": 1}[r["action"]] for r in rs]
            )
            acted = selected >= 0
            good = acted & truth[np.arange(len(ids)), np.maximum(selected, 0)]
            bad = acted & ~good
            metrics = {
                "coverage": (acted, np.ones(len(ids))),
                "completion": (good, np.ones(len(ids))),
                "conditional_error": (bad, acted),
                "required_recovery": ((selected == 1) & required, required),
                "recover_only_coverage": ((selected == 1) & ronly, ronly),
                "harmful_recovery": (
                    (selected == 1) & truth[:, 0] & ~truth[:, 1],
                    truth[:, 0] & ~truth[:, 1],
                ),
                "deferred_physically_actionable": (
                    (~acted) & truth.any(axis=1),
                    truth.any(axis=1),
                ),
            }
            for field, (v, d) in metrics.items():
                interval(v, d, results["parent_bootstrap_95"][m + "|" + mode][field])
            for a, name in ((0, "continue"), (1, "recover")):
                mask = selected == a
                parents = set(parent[mask])
                errors = set(parent[mask & bad])
                reported = assignment[m + "|" + mode + "|" + name]
                assert (reported["assigned_parents"], reported["error_parents"]) == (
                    len(parents),
                    len(errors),
                )
                expected = (
                    1.0
                    if not parents or len(errors) == len(parents)
                    else float(
                        beta.ppf(
                            1 - 0.05 / 68, len(errors) + 1, len(parents) - len(errors)
                        )
                    )
                )
                assert abs(reported["upper"] - expected) < 1e-10
                strata += 1
            if mode != "calibrated":
                continue
            for name, fallback in (
                ("primary", -1),
                ("STOP_continue", 0),
                ("STOP_recover", 1),
            ):
                action = np.where(acted, selected, fallback)
                used = action >= 0
                success = used & truth[np.arange(len(ids)), np.maximum(action, 0)]
                table = secondary["tables"][m + "|" + name]
                assert (table["good"], table["bad"], table["stop"]) == (
                    int(success.sum()),
                    int((used & ~success).sum()),
                    int((~used).sum()),
                )
                assert table["required_recovery"] == int(
                    ((action == 1) & required).sum()
                )
                assert table["success_at_original_STOP"] == int(
                    (~acted & initial).sum()
                )
                interval(success, np.ones(len(ids)), table["completion_interval"])
                scores[m, name] = success.astype(int)
    for m in METHODS:
        for name in ("primary", "STOP_continue", "STOP_recover"):
            interval(
                scores["DSRE_risk", name] - scores[m, name],
                np.ones(len(ids)),
                secondary["paired_risk_minus_baselines"][m + "|" + name],
            )
    before = read(root / "test_analysis_before_population_fix.json")
    assert (
        before["tables"] == results["tables"]
        and before["paired_risk_minus_baselines"]
        == results["paired_risk_minus_baselines"]
    )
    return {
        "passed": True,
        "raw_recover_only_checkpoints": int(ronly.sum()),
        "raw_initially_failed_recover_only_checkpoints": int(required.sum()),
        "preventive_recover_only_checkpoints": int((ronly & initial).sum()),
        "population_and_composition_intervals_checked": checks,
        "heldout_assignment_bounds_independently_checked": strata,
        "all_main_tables_and_paired_contrasts_unchanged_by_label_fix": True,
        "epoch": time.time(),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    v = audit(a.root)
    atomic(a.root / "sensitivity_population_audit.json", v)
    print(v, flush=True)
