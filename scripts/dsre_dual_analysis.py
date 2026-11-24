"""Fixed paired policy accounting from sealed decisions; no policy refitting."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_dual_adjudication import (
    gz,
    outcome_class,
    partition,
    read,
    sha,
    summarize,
    write_once,
)

POLICIES = tuple(
    f"{m}_{mode}"
    for m in ("DSRE", "B7", "CART2")
    for mode in ("historical", "absolute", "nondegradation")
) + ("DSRE_raw", "CART2_raw", "always_continue", "always_recover")
FIELDS = (
    "rows",
    "acted",
    "continue",
    "recover",
    "success",
    "failure",
    "stop",
    "required",
    "required_selected",
    "initially_unsuccessful",
    "initial_failure_R",
    "preventive_R_only",
    "R_only",
    "harm_R",
    "futile_R",
    "both_success",
    "both_success_maintained",
    "both_success_R",
    "initial_success_maintained",
    "physical_recovery_gain",
    "completion_minus_continue",
    "recovery_controls",
    "futile_recovery_controls",
)
RATIOS = (
    ("completion", "success", "rows"),
    ("coverage", "acted", "rows"),
    ("conditional_success", "success", "acted"),
    ("required_recovery_recall", "required_selected", "required"),
    ("useful_recoveries_per_R", "required_selected", "recover"),
    ("recovery_per_failed_start", "required_selected", "initially_unsuccessful"),
    ("harm_per_R", "harm_R", "recover"),
    ("futile_per_R", "futile_R", "recover"),
    ("matched_recovery_effect", "physical_recovery_gain", "recover"),
    ("completion_effect_vs_continue", "completion_minus_continue", "rows"),
)
CONTRASTS = (
    ("DSRE_nondegradation", "DSRE_absolute"),
    ("CART2_nondegradation", "CART2_absolute"),
    ("DSRE_nondegradation", "CART2_nondegradation"),
    ("DSRE_absolute", "CART2_absolute"),
    ("DSRE_nondegradation", "B7_nondegradation"),
    ("DSRE_nondegradation", "always_continue"),
    ("DSRE_nondegradation", "always_recover"),
    ("DSRE_nondegradation", "DSRE_historical"),
)


def metrics(row, action):
    c, r, initial = row["c"], row["r"], row["initial_success"]
    acted = action is not None
    success = (r if action == "recover" else c) if acted else False
    required = not initial and not c and r
    return dict(
        zip(
            FIELDS,
            map(
                int,
                (
                    1,
                    acted,
                    action == "continue",
                    action == "recover",
                    success,
                    acted and not success,
                    not acted,
                    required,
                    required and action == "recover",
                    not initial,
                    not initial and action == "recover",
                    initial and not c and r and action == "recover",
                    not c and r and action == "recover",
                    c and not r and action == "recover",
                    not c and not r and action == "recover",
                    c and r,
                    c and r and acted,
                    c and r and action == "recover",
                    initial and success,
                    (int(r) - int(c)) if action == "recover" else 0,
                    int(success) - int(c),
                    70 if action == "recover" else 0,
                    70 if action == "recover" and not c and not r else 0,
                ),
            ),
            strict=True,
        )
    )


def actions(root, row, sidecar, original):
    condition = row["condition"]
    output = {
        "always_continue": "continue",
        "always_recover": "recover",
        "DSRE_raw": row["proposals"]["DSRE_risk"],
        "CART2_raw": row["proposals"]["CART2_beta10"],
    }
    for name, method in (
        ("DSRE", "DSRE_risk"),
        ("B7", "B7_risk"),
        ("CART2", "CART2_beta10"),
    ):
        output[name + "_historical"] = original["clean_gated_actions"][condition][
            method
        ]
        for mode in ("absolute", "nondegradation"):
            output[name + "_" + mode] = sidecar["decisions"][condition][method][mode][
                "action"
            ]
    assert set(output) == set(POLICIES)
    for mode in ("historical", "absolute", "nondegradation"):
        assert output["DSRE_" + mode] == output["B7_" + mode]
    return output


def bootstrap(n):
    sample = np.random.Generator(np.random.PCG64(2026111603)).integers(0, n, (4000, n))
    return np.asarray([np.bincount(row, minlength=n) for row in sample], dtype=float)


def bounds(nums, dens, weights):
    nums, dens = np.asarray(nums, dtype=float), np.asarray(dens, dtype=float)
    n, d = weights @ nums, weights @ dens
    valid = d > 0
    lo, hi = (
        np.quantile(n[valid] / d[valid], [0.025, 0.975])
        if valid.any()
        else (None, None)
    )
    return {
        "estimate": float(nums.sum() / dens.sum()) if dens.sum() else None,
        "lower": None if lo is None else float(lo),
        "upper": None if hi is None else float(hi),
        "numerator": int(nums.sum()),
        "denominator": int(dens.sum()),
        "defined_draws": int(valid.sum()),
    }


def run(root):
    assert read(root / "test_physics_audit.json")["complete_cohort"]
    assert read(root / "dual_calibration_audit.json")["passed"]
    rows = gz(root / "test_rows.json.gz")
    assert len(rows) == 640 and len({r["seed"] for r in rows}) == 128
    grouped = defaultdict(lambda: defaultdict(Counter))
    categories, records, witnesses = defaultdict(Counter), [], {}
    sidecars, originals = {}, {}
    seal = read(root / "dual_test_seal.json")
    for row in rows:
        seed = row["seed"]
        directory = root / "test" / str(seed)
        if seed not in sidecars:
            assert seal["parents"][str(seed)] == sha(directory / "dual_decision.json")
            sidecars[seed], originals[seed] = (
                read(directory / "dual_decision.json"),
                read(directory / "decision.json"),
            )
        cls = outcome_class(row["c"], row["r"])
        for population in ("ALL", row["condition"]):
            categories[population][cls] += 1
            categories[population]["rows"] += 1
            categories[population]["initially_unsuccessful"] += not row[
                "initial_success"
            ]
            categories[population]["required"] += (
                not row["initial_success"] and cls == "R_ONLY"
            )
        for policy, action in actions(
            root, row, sidecars[seed], originals[seed]
        ).items():
            count = metrics(row, action)
            rec = {
                "seed": seed,
                "condition": row["condition"],
                "policy": policy,
                "action": action,
                "counts": count,
            }
            records.append(rec)
            for population in ("ALL", row["condition"]):
                grouped[policy + "|" + population][seed].update(count)
            label = policy + "|" + cls
            if (
                action == "recover"
                and cls in ("R_ONLY", "NEITHER", "C_ONLY")
                and label not in witnesses
            ):
                raw = gz(Path(row["source"]))
                witnesses[label] = {
                    **row,
                    "policy": policy,
                    "selected_action": action,
                    "evidence": raw["scenarios"]["clean"]["point_proposal"][
                        "DSRE_risk"
                    ]["evidence"]
                    if policy.startswith(("DSRE", "B7"))
                    else [],
                    "initial_position": raw["canonical_start"]["position"],
                    "initial_goal": raw["canonical_start"]["observation"]["extra"][
                        "goal_pos"
                    ],
                    "C_terminal": gz(Path(row["source"]).parent / "continue.json.gz")[
                        "frames"
                    ][-1]["state"],
                    "R_terminal": gz(Path(row["source"]).parent / "recover.json.gz")[
                        "frames"
                    ][-1]["state"],
                }
    tables, weights = {}, bootstrap(128)
    for key, parent_counts in grouped.items():
        parents = sorted(parent_counts)
        assert len(parents) == 128
        arrays = {
            field: np.asarray([parent_counts[p][field] for p in parents])
            for field in FIELDS
        }
        tables[key] = {
            "parents": 128,
            "counts": {field: int(value.sum()) for field, value in arrays.items()},
            "intervals": {
                name: bounds(arrays[num], arrays[den], weights)
                for name, num, den in RATIOS
            },
        }
    comparisons = {}
    populations = ["ALL"] + [
        name for name, _ in read(root / "study_plan.json")["profiles"]
    ]
    for a, b in CONTRASTS:
        for pop in populations:
            left, right = grouped[a + "|" + pop], grouped[b + "|" + pop]
            parents = sorted(left)
            for name, field, den in (
                ("completion", "success", "rows"),
                ("coverage", "acted", "rows"),
                ("required_recovery_recall", "required_selected", "required"),
                ("harm", "harm_R", "rows"),
                ("futile_recovery_burden", "futile_R", "rows"),
                ("recovery_attempt_rate", "recover", "rows"),
            ):
                assert all(left[p][den] == right[p][den] for p in parents)
                comparisons[f"{a}_minus_{b}|{pop}|{name}"] = bounds(
                    [left[p][field] - right[p][field] for p in parents],
                    [left[p][den] for p in parents],
                    weights,
                )
    cal = read(root / "dual_calibration.json")
    qualified = [key for key, value in cal["bounds"].items() if value["qualified"]]
    main = tables["DSRE_nondegradation|ALL"]["counts"]
    contrast = comparisons["DSRE_nondegradation_minus_DSRE_absolute|ALL|completion"]
    confirmed = (
        cal["bounds"]["DSRE_risk|recover|nondegradation"]["qualified"]
        and not cal["bounds"]["DSRE_risk|recover|absolute"]["qualified"]
        and main["required_selected"] > 0
        and contrast["lower"] is not None
        and contrast["lower"] > 0
    )
    status = (
        "DUAL_OBLIGATION_CONFIRMED"
        if confirmed
        else "NO_ACTION_QUALIFICATION"
        if not qualified
        else "DECOMPOSITION_ONLY"
    )
    for stage in ("calibration", "test"):
        data = gz(root / (stage + "_rows.json.gz"))
        write_once(
            root / (stage + "_decomposition.json"),
            {
                "DSRE": summarize(data, "DSRE_risk"),
                "CART2": summarize(data, "CART2_beta10"),
                "fixed_recover": summarize(data, "B0_recover"),
                "partitions": {str(width): partition(data, width) for width in (7, 12)},
            },
        )
    with gzip.open(root / "policy_records.jsonl.gz", "wt") as stream:
        for rec in records:
            stream.write(json.dumps(rec) + "\n")
    write_once(root / "physical_witnesses.json", witnesses)
    result = {
        "status": status,
        "parents": 128,
        "checkpoints": 640,
        "tables": tables,
        "comparisons": comparisons,
        "paired_outcomes": {key: dict(value) for key, value in categories.items()},
        "qualified_calibration_claims": qualified,
        "B7_identity": True,
        "no_new_controller_or_prefix_advantage": True,
        "calibration_sha256": sha(root / "dual_calibration.json"),
        "test_sidecar_seal_sha256": sha(root / "dual_test_seal.json"),
        "bootstrap": read(root / "study_plan.json")["bootstrap"],
        "epoch": time.time(),
    }
    write_once(root / "dual_results.json", result)
    print(
        json.dumps(
            {
                "status": status,
                "tables": len(tables),
                "comparisons": len(comparisons),
                "policy_records": len(records),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    run(parser.parse_args().root)
