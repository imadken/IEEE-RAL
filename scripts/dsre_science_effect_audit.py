"""Independent paired-effect and secondary-control recount from sealed data."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_science_numerical import check_intervals


def direct(nums, dens, n):
    num = np.asarray(nums, dtype=float)
    den = np.asarray(dens, dtype=float)
    indices = np.random.default_rng(2026111504).integers(0, n, (4000, n))
    sums = den[indices].sum(axis=1)
    values = num[indices].sum(axis=1)
    valid = sums > 0
    return (
        float(num.sum() / den.sum()) if den.sum() else None,
        np.quantile(values[valid] / sums[valid], [0.025, 0.975]).tolist()
        if valid.any()
        else [None, None],
        int(valid.sum()),
    )


def same(reported, nums, dens, n):
    point, interval, valid = direct(nums, dens, n)
    assert reported["estimate"] == point
    assert [reported["lower"], reported["upper"]] == interval
    assert reported["bootstrap_defined_draws"] == valid
    assert reported["numerator"] == sum(nums) and reported["denominator"] == sum(dens)


def audit(root):
    with gzip.open(root / "prospective_rows.jsonl.gz", "rt") as f:
        rows = [json.loads(s) for s in f]
    by_id = {r["id"]: r for r in rows}
    result = read(root / "prospective_results.json")
    effects = read(root / "physical_effects_and_secondary.json")
    checks = 0
    class_checks = 0
    selection_checks = 0
    for population in sorted({r["population"] for r in rows}):
        selected = [r for r in rows if r["population"] == population]
        groups = sorted({r["group"] for r in selected})
        n = len(groups)
        conditions = sorted({r["condition"] for r in selected})
        by_key = {(r["group"], r["condition"]): r for r in selected}
        for condition in ["ALL", *conditions]:
            arm = [
                r for r in selected if condition == "ALL" or r["condition"] == condition
            ]
            expected = Counter(
                {
                    k: 0
                    for k in (
                        "continue_only",
                        "recover_only",
                        "both",
                        "neither",
                        "required_recovery",
                        "initial_failed",
                    )
                }
            )
            for row in arm:
                c, r = (
                    row["outcomes"]["continue_value"],
                    row["outcomes"]["recover_value"],
                )
                expected[
                    "both"
                    if c and r
                    else "continue_only"
                    if c
                    else "recover_only"
                    if r
                    else "neither"
                ] += 1
                expected["required_recovery"] += int(
                    not row["initial_success"] and not c and r
                )
                expected["initial_failed"] += int(not row["initial_success"])
            reported = result["outcome_classes"][population + "|" + condition]
            assert all(reported[k] == v for k, v in expected.items())
            assert reported["parents"] == n and reported["rows"] == len(arm)
            class_checks += 1
            per = defaultdict(list)
            for row in arm:
                per[row["group"]].append(row)
            den = [len(per[g]) for g in groups]
            c = [sum(r["outcomes"]["continue_value"] for r in per[g]) for g in groups]
            r = [sum(r["outcomes"]["recover_value"] for r in per[g]) for g in groups]
            data = effects["physical_effects"][population + "|" + condition]
            for name, nums in (
                ("continue", c),
                ("recover", r),
                ("recover_minus_continue", np.asarray(r) - np.asarray(c)),
            ):
                same(data[name], nums, den, n)
                checks += 1
        for condition in conditions:
            if condition == "nominal":
                continue
            for action in ("continue", "recover"):
                nums = [
                    int(by_key[g, condition]["outcomes"][action + "_value"])
                    - int(by_key[g, "nominal"]["outcomes"][action + "_value"])
                    for g in groups
                ]
                same(
                    effects["physical_effects"][
                        f"{population}|{condition}_minus_nominal|{action}"
                    ],
                    nums,
                    [1] * n,
                    n,
                )
                checks += 1
    with gzip.open(root / "prospective_decisions.jsonl.gz", "rt") as f:
        records = [json.loads(s) for s in f]
    for key, data in effects["selected_recovery_effects"].items():
        pop, scenario, method = key.split("|")
        groups = sorted({r["group"] for r in rows if r["population"] == pop})
        chosen = [
            r
            for r in records
            if r["population"] == pop
            and r["scenario"] == scenario
            and r["method"] == method
            and r["mode"] == "robust_proposal"
            and r["action"] == "recover"
        ]
        nums = Counter()
        dens = Counter()
        types = Counter()
        for rec in chosen:
            row = by_id[rec["id"]]
            c, r = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
            nums[row["group"]] += int(r) - int(c)
            dens[row["group"]] += 1
            types[
                "harmful_continue_only"
                if c and not r
                else "both_success_maintenance"
                if c and r
                else "necessary_failed_start"
                if r and not row["initial_success"]
                else "preventive_recover_only"
                if r
                else "neither_success"
            ] += 1
        assert data["composition"] == dict(types) and data["selected_R"] == len(chosen)
        same(
            data["matched_R_minus_C"],
            [nums[g] for g in groups],
            [dens[g] for g in groups],
            len(groups),
        )
        selection_checks += 1
    with gzip.open(root / "secondary_decisions.jsonl.gz", "rt") as f:
        secondary = [json.loads(s) for s in f]
    secondary_checks = check_intervals(secondary, effects["secondary_tables"])
    seal = read(root / "secondary_recommendation_seal.json")
    assert sha(root / "secondary_recommendations.jsonl.gz") == seal["sha256"]
    earliest = min(
        read(p)["epoch"]
        for p in (root / "prospective").glob("*/execution_started.json")
    )
    assert (
        read(root / "prospective_recommendation_seal.json")["epoch"]
        <= seal["epoch"]
        < earliest
    )
    for p in (root / "prospective").glob("*/*/screen.json.gz"):
        # Version records use the same build-qualified simulator family; package
        # binary/metadata preservation is also checked at campaign closure.
        with gzip.open(p, "rt") as stream:
            raw = json.load(stream)
        expected = read(root / "environment_fingerprint.json")["packages"]
        assert all(
            raw["model"]["versions"][name] == expected[name]["version"]
            for name in raw["model"]["versions"]
        )
    output = {
        "passed": True,
        "outcome_class_profiles": class_checks,
        "independent_physical_effect_intervals": checks,
        "selected_recovery_compositions_and_intervals": selection_checks,
        "secondary": secondary_checks,
        "all_secondary_recommendations_sealed_before_primary_futures": True,
        "simulator_versions_unchanged": True,
        "epoch": time.time(),
    }
    atomic(root / "physical_effects_secondary_audit.json", output)
    print(json.dumps(output), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    audit(a.root)
