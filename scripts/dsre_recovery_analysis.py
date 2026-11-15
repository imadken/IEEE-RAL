"""Seal the fixed recovery calibration, then score the independent paired test."""

import argparse
import time
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_analysis import records_for, summarize
from dsre_recovery_audit import exact_upper, gz
from dsre_recovery_evidence import PRIOR, TASK

from dual_rec.dsre.operational import METHODS, OperationalRouter, calibrate_records


def calibration_rows(root):
    records = []
    funnel = []
    counts = Counter()
    for p in sorted((root / "progress").glob("calibration-*.json")):
        progress = read(p)
        funnel.append({k: progress[k] for k in ("index", "seed", "status")})
        if progress["status"] != "COMPLETE":
            continue
        directory = root / "calibration" / str(progress["seed"])
        decision = read(directory / "decision.json")
        assert sha(directory / "decision.json") == progress["decision_sha256"]
        admitted = decision["admitted_methods"]
        for m in METHODS:
            assigned = any(
                x[m]["proposal"] == "recover" for x in decision["all_actions"]
            )
            assert (m in admitted) == (assigned and counts[m] < 112)
        for cell_index, cell in enumerate(progress["cells"]):
            outcomes = {o["action"]: o["success"] for o in cell["outcomes"]}
            for m in admitted:
                if decision["all_actions"][cell_index][m]["proposal"] == "recover":
                    assert "recover" in outcomes
                    records.append(
                        {
                            "method": m,
                            "task": TASK,
                            "action": "recover",
                            "group": f"{TASK}/{progress['seed']}",
                            "condition": cell["condition"],
                            "unacceptable": not outcomes["recover"],
                            "source_decision_sha256": progress["decision_sha256"],
                        }
                    )
        counts.update(admitted)
    if (root / "counts.json").exists():
        assert dict(counts) == {
            k: v for k, v in read(root / "counts.json").items() if v
        }
    return records, funnel, counts


def seal_calibration(root):
    verify_freeze(root)
    if (root / "calibration_seal.json").exists():
        raise ValueError("Calibration already sealed")
    assert (root / "calibration_boundary.json").exists(), (
        "Calibration workers must finish first"
    )
    new, funnel, counts = calibration_rows(root)
    old = read(PRIOR / "calibration_records.json")
    previous = read(PRIOR / "calibration_decision.json")["strata"]
    combined = calibrate_records(old + new)
    strata = dict(previous)
    comparison = {}
    for m in METHODS:
        key = f"{m}|{TASK}|recover"
        fresh = [r for r in new if r["method"] == m]
        groups = {r["group"] for r in fresh}
        errors = {r["group"] for r in fresh if r["unacceptable"]}
        fresh_bound = exact_upper(len(errors), len(groups))
        entry = combined[key]
        assert (
            abs(
                entry["upper"]
                - exact_upper(entry["error_parents"], entry["assigned_parents"])
            )
            < 1e-10
        )
        complete = counts[m] == 112
        qualified = (
            complete
            and not (root / "study_halt.json").exists()
            and read(root / "qualification_audit.json")["passed"]
        )
        entry["enabled"] = bool(
            entry["upper"] <= 0.1 and fresh_bound <= 0.1 and qualified
        )
        entry["status"] = (
            "CERTIFIED_PARENT_ACTION_SCOPE" if entry["enabled"] else "NOT_CERTIFIED"
        )
        entry.update(
            new_assigned_parents=len(groups),
            new_error_parents=len(errors),
            new_upper=fresh_bound,
            additional_quota_complete=complete,
        )
        strata[key] = entry
        comparison[m] = {
            "original": previous[key],
            "new_only": {
                "assigned_parents": len(groups),
                "error_parents": len(errors),
                "upper": fresh_bound,
            },
            "pooled": entry,
            "screened_parents": len([r for r in funnel if r["status"] == "COMPLETE"]),
            "stopping": "Own fixed112 assigned-parent quota, or frozen resource/screen boundary; never errors",
        }
    decision = {
        "strata": strata,
        "comparison": comparison,
        "plan_sha256": sha(root / "plan.json"),
        "qualification_sha256": sha(root / "qualification_audit.json"),
        "previous_calibration_sha256": sha(PRIOR / "calibration_decision.json"),
        "sealed_epoch": time.time(),
        "scope": "Pick recovery gate only; all historical continue and Push gates identical. Independently fixed-size fresh bounds plus compatible pooled diagnostics. No test outcome consulted.",
    }
    atomic(root / "new_calibration_records.json", new)
    atomic(root / "calibration_funnel.json", funnel)
    atomic(root / "calibration_decision.json", decision)
    atomic(
        root / "calibration_seal.json",
        {
            "sha256": sha(root / "calibration_decision.json"),
            "records_sha256": sha(root / "new_calibration_records.json"),
            "funnel_sha256": sha(root / "calibration_funnel.json"),
            "plan_sha256": sha(root / "plan.json"),
            "epoch": time.time(),
        },
    )
    (root / "calibration_decision.json").chmod(0o444)
    print(
        {
            m: (
                v["new_only"]["assigned_parents"],
                v["new_only"]["error_parents"],
                v["pooled"]["enabled"],
            )
            for m, v in comparison.items()
        },
        flush=True,
    )


def ratio_interval(numerator, denominator, groups, indices):
    nums = np.array(
        [
            sum(numerator[i] for i, g in enumerate(groups) if g == parent)
            for parent in sorted(set(groups))
        ],
        float,
    )
    dens = np.array(
        [
            sum(denominator[i] for i, g in enumerate(groups) if g == parent)
            for parent in sorted(set(groups))
        ],
        float,
    )
    if not dens.sum():
        return {"estimate": None, "lower": None, "upper": None, "denominator": 0}
    den = dens[indices].sum(axis=1)
    num = nums[indices].sum(axis=1)
    values = num[den > 0] / den[den > 0]
    lo, hi = np.quantile(values, [0.025, 0.975])
    return {
        "estimate": float(nums.sum() / dens.sum()),
        "lower": float(lo),
        "upper": float(hi),
        "denominator": int(dens.sum()),
        "numerator": int(nums.sum()),
        "bootstrap_draws_with_support": len(values),
    }


def recovery_populations(rows):
    """Separate counterfactual recovery need from recovery of a failed start."""
    recover_only = [
        int(not r["outcomes"]["continue_value"] and r["outcomes"]["recover_value"])
        for r in rows
    ]
    required = [
        int(only and not r["initial_success"])
        for only, r in zip(recover_only, rows, strict=True)
    ]
    return recover_only, required


def analyze(root):
    verify_freeze(root)
    assert (
        sha(root / "calibration_decision.json")
        == read(root / "calibration_seal.json")["sha256"]
    )
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    cal = read(root / "calibration_decision.json")["strata"]
    rows = []
    sealed = []
    funnel = []
    for path in sorted((root / "progress").glob("test-*.json")):
        p = read(path)
        funnel.append({k: p[k] for k in ("index", "seed", "status")})
        if p["status"] != "COMPLETE":
            continue
        directory = root / "test" / str(p["seed"])
        dec = read(directory / "decision.json")
        assert dec["calibration_sha256"] == sha(root / "calibration_decision.json")
        assert (
            dec["sealed_epoch"]
            >= read(root / "calibration_decision.json")["sealed_epoch"]
        )
        for i, cell in enumerate(p["cells"]):
            raw = gz(directory / cell["condition"] / "screen.json.gz")
            outcomes = {o["action"] + "_value": o["success"] for o in cell["outcomes"]}
            assert len(outcomes) == 2
            row = raw["summary"] | {
                "id": f"{TASK}/{p['seed']}/{cell['condition']}",
                "group": f"{TASK}/{p['seed']}",
                "outcomes": outcomes,
            }
            rows.append(row)
            sealed.append(dec["all_actions"][i])
    records = records_for(rows, router, frozen, cal)
    for i, row in enumerate(rows):
        for rec in records[i * 34 : (i + 1) * 34]:
            kind = "gated" if rec["mode"] == "calibrated" else "proposal"
            assert rec["action"] == sealed[i][rec["method"]][kind]
    atomic(root / "test_records.json", records)
    atomic(root / "test_funnel.json", funnel)
    tables = summarize(records)
    groups = [row["group"] for row in rows]
    n = len(set(groups))
    if not n:
        atomic(
            root / "test_analysis.json",
            {
                "status": "NO_QUALIFIED_TEST_PARENTS",
                "funnel": funnel,
                "tables": {},
                "no_results_imputed": True,
            },
        )
        return
    rng = np.random.default_rng(2026111501)
    indices = rng.integers(0, n, (4000, n))
    uncertainty = {}
    contrasts = {}
    ronly, required = recovery_populations(rows)
    both = [
        int(r["outcomes"]["continue_value"] and r["outcomes"]["recover_value"])
        for r in rows
    ]
    conly = [
        int(r["outcomes"]["continue_value"] and not r["outcomes"]["recover_value"])
        for r in rows
    ]
    for mode in ("proposal", "calibrated"):
        bymethod = {
            m: [r for r in records if r["mode"] == mode and r["method"] == m]
            for m in METHODS
        }
        for m, rs in bymethod.items():
            metrics = {
                "coverage": ([r["recommended"] for r in rs], [1] * len(rs)),
                "completion": ([r["successful"] for r in rs], [1] * len(rs)),
                "conditional_error": (
                    [r["unacceptable"] for r in rs],
                    [r["recommended"] for r in rs],
                ),
                "required_recovery": (
                    [
                        int(required[i] and r["action"] == "recover")
                        for i, r in enumerate(rs)
                    ],
                    required,
                ),
                "recover_only_coverage": (
                    [
                        int(ronly[i] and r["action"] == "recover")
                        for i, r in enumerate(rs)
                    ],
                    ronly,
                ),
                "harmful_recovery": (
                    [
                        int(conly[i] and r["action"] == "recover")
                        for i, r in enumerate(rs)
                    ],
                    conly,
                ),
                "deferred_physically_actionable": (
                    [
                        int(r["deferred"] and (ronly[i] or both[i] or conly[i]))
                        for i, r in enumerate(rs)
                    ],
                    [int(ronly[i] or both[i] or conly[i]) for i in range(len(rs))],
                ),
            }
            uncertainty[m + "|" + mode] = {
                name: ratio_interval(num, den, groups, indices)
                for name, (num, den) in metrics.items()
            }
        primary = bymethod["DSRE_risk"]
        for m, rs in bymethod.items():
            contrasts[m + "|" + mode] = {}
            for metric in (
                "successful",
                "unacceptable",
                "recommended",
                "required_recovery_success",
            ):
                delta = [
                    a[metric] - b[metric] for a, b in zip(primary, rs, strict=True)
                ]
                contrasts[m + "|" + mode][metric] = ratio_interval(
                    delta, [1] * len(delta), groups, indices
                )
    classes = Counter(
        "both"
        if a and b
        else "continue_only"
        if a
        else "recover_only"
        if b
        else "neither"
        for a, b in [
            (r["outcomes"]["continue_value"], r["outcomes"]["recover_value"])
            for r in rows
        ]
    )
    clean = [
        r for r in records if r["method"] == "DSRE_risk" and r["mode"] == "calibrated"
    ]
    physical = {
        "all_continue_success": sum(r["outcomes"]["continue_value"] for r in rows),
        "all_recover_success": sum(r["outcomes"]["recover_value"] for r in rows),
        "selected_recover_only_gains": sum(
            r["action"] == "recover" and ronly[i] for i, r in enumerate(clean)
        ),
        "selected_recover_harm": sum(
            r["action"] == "recover" and conly[i] for i, r in enumerate(clean)
        ),
        "selected_recover_maintenance_both": sum(
            r["action"] == "recover" and both[i] for i, r in enumerate(clean)
        ),
        "scope": "Matched reset outcomes of frozen skills. No new controller or improvement attributable to explanation algorithm; ordinary rules and trees compared at own calibrated gates.",
    }
    recover_mask = [int(r["action"] == "recover") for r in clean]
    outcome_delta = [
        int(r["outcomes"]["recover_value"]) - int(r["outcomes"]["continue_value"])
        for r in rows
    ]
    physical["paired_fixed_recover_minus_continue"] = ratio_interval(
        outcome_delta, [1] * len(rows), groups, indices
    )
    physical["selected_recover_minus_matched_continue"] = ratio_interval(
        [v * mask for v, mask in zip(outcome_delta, recover_mask, strict=True)],
        recover_mask,
        groups,
        indices,
    )
    physical["required_fraction_among_selected_recover"] = ratio_interval(
        [v * mask for v, mask in zip(required, recover_mask, strict=True)],
        recover_mask,
        groups,
        indices,
    )
    assignment_errors = {}
    for mode in ("proposal", "calibrated"):
        for method in METHODS:
            for action in ("continue", "recover"):
                selected = [
                    r
                    for r in records
                    if r["method"] == method
                    and r["mode"] == mode
                    and r["action"] == action
                ]
                assigned = {r["group"] for r in selected}
                failed = {r["group"] for r in selected if r["unacceptable"]}
                assignment_errors[f"{method}|{mode}|{action}"] = {
                    "assigned_parents": len(assigned),
                    "error_parents": len(failed),
                    "assigned_checkpoints": len(selected),
                    "upper": exact_upper(len(failed), len(assigned)),
                    "scope": "Held-out diagnostic only; any assigned-condition parent error; no calibration gate update.",
                }
    atomic(root / "test_assignment_errors.json", assignment_errors)
    result = {
        "status": "COMPLETE" if n == 160 else "INCOMPLETE_COHORT",
        "parents": n,
        "checkpoints": len(rows),
        "paired_classes": dict(classes),
        "tables": tables,
        "parent_bootstrap_95": uncertainty,
        "paired_risk_minus_baselines": contrasts,
        "physical_effects": physical,
        "calibration_sha256": sha(root / "calibration_decision.json"),
        "bootstrap": {
            "draws": 4000,
            "seed": 2026111501,
            "unit": "independent seed parent, retain both conditions",
            "intervals": "Descriptive percentile95%, no simultaneous coverage claim",
        },
        "epoch": time.time(),
    }
    atomic(root / "test_analysis.json", result)
    print(
        {"status": result["status"], "classes": classes, "physical": physical},
        flush=True,
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["calibrate", "analyze"])
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.command == "calibrate":
        seal_calibration(a.root)
    else:
        analyze(a.root)


if __name__ == "__main__":
    main()
