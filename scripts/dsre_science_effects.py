"""Preregistered paired physical effects, secondary controls and witness examples."""

import argparse
import gzip
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_science_analysis import aggregate, ratio_interval, weights_for
from dsre_science_offline import row_scores


def physical_effects(rows):
    output = {}
    for population in sorted({r["population"] for r in rows}):
        source = [r for r in rows if r["population"] == population]
        parents = sorted({r["group"] for r in source})
        w = weights_for(len(parents))
        conditions = sorted({r["condition"] for r in source})
        for condition in ["ALL", *conditions]:
            selected = [
                r for r in source if condition == "ALL" or r["condition"] == condition
            ]
            groups = defaultdict(list)
            for row in selected:
                groups[row["group"]].append(row)
            den = [len(groups[g]) for g in parents]
            num = {
                a: [
                    sum(r["outcomes"][a + "_value"] for r in groups[g]) for g in parents
                ]
                for a in ("continue", "recover")
            }
            output[population + "|" + condition] = {
                "rows": len(selected),
                "parents": len(parents),
                "continue": ratio_interval(num["continue"], den, w),
                "recover": ratio_interval(num["recover"], den, w),
                "recover_minus_continue": ratio_interval(
                    np.asarray(num["recover"]) - np.asarray(num["continue"]), den, w
                ),
            }
        by_key = {(r["group"], r["condition"]): r for r in source}
        for condition in conditions:
            if condition == "nominal":
                continue
            for action in ("continue", "recover"):
                diffs = [
                    int(by_key[g, condition]["outcomes"][action + "_value"])
                    - int(by_key[g, "nominal"]["outcomes"][action + "_value"])
                    for g in parents
                ]
                output[f"{population}|{condition}_minus_nominal|{action}"] = (
                    ratio_interval(diffs, [1] * len(parents), w)
                )
    return output


def run(root):
    with gzip.open(root / "prospective_rows.jsonl.gz", "rt") as f:
        rows = [json.loads(s) for s in f]
    by_id = {r["id"]: r for r in rows}
    with gzip.open(root / "prospective_decisions.jsonl.gz", "rt") as f:
        records = [json.loads(s) for s in f]
    selected_effects = {}
    for population in ("new_development", "new_confirmation"):
        parent_ids = sorted({r["group"] for r in rows if r["population"] == population})
        if not parent_ids:
            continue
        weight = weights_for(len(parent_ids))
        for scenario in ("clean", "bound001", "bound005"):
            for method in (
                "DSRE_strict",
                "DSRE_risk",
                "B7_risk",
                "CART2_strict",
                "CART2_beta10",
                "B1_two_strict",
                "B0_continue",
                "B0_recover",
            ):
                selected = [
                    r
                    for r in records
                    if r["population"] == population
                    and r["scenario"] == scenario
                    and r["mode"] == "robust_proposal"
                    and r["method"] == method
                    and r["action"] == "recover"
                ]
                nums = Counter()
                dens = Counter()
                types = Counter()
                for rec in selected:
                    row = by_id[rec["id"]]
                    c, r = row["outcomes"].values()
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
                selected_effects[f"{population}|{scenario}|{method}"] = {
                    "selected_R": len(selected),
                    "composition": types,
                    "matched_R_minus_C": ratio_interval(
                        [nums[g] for g in parent_ids],
                        [dens[g] for g in parent_ids],
                        weight,
                    ),
                    "interpretation": "Conditional on the frozen proposed action, not population certification or a controller-improvement claim.",
                }
    secondary = []
    seal = read(root / "secondary_recommendation_seal.json")
    assert sha(root / "secondary_recommendations.jsonl.gz") == seal["sha256"]
    with gzip.open(root / "secondary_recommendations.jsonl.gz", "rt") as f:
        for line in f:
            item = json.loads(line)
            cell = item["cell"]
            id = f"PickCube-v1/{cell['seed']}/{cell['condition']}"
            if id not in by_id:
                continue
            row = by_id[id]
            truth = tuple(row["features"] + row["optional_features"])
            coarse = item["scenarios"]["coarse02_point"]
            secondary += row_scores(
                row,
                "coarse02_point",
                "point_proposal",
                coarse["outputs"],
                truth,
                tuple(coarse["measured_values"]),
            )
            if "delay5_equal_250ms" in item["scenarios"]:
                data = item["scenarios"]["delay5_equal_250ms"]
                invariant = tuple(f["invariant"] for f in data["measurement"]["facts"])
                for mode, name in (
                    ("point_proposal", "point"),
                    ("robust_proposal", "robust"),
                ):
                    secondary += row_scores(
                        row, "delay5_equal_250ms", mode, data[name], truth, invariant
                    )
    with gzip.open(root / "secondary_decisions.jsonl.gz", "wt") as f:
        for rec in secondary:
            f.write(json.dumps(rec) + "\n")
    tables, _ = aggregate(secondary, True)
    examples = []
    result = read(root / "prospective_results.json")
    # Deterministic first IDs, not a favorable-seed search or changed population.
    for key, profile in result["mechanism"].items():
        if not key.startswith("new_confirmation|point"):
            continue
        for kind in ("ambiguity_pair", "neither_witness"):
            candidates = [g for g in profile["groups"] if g[kind]]
            if candidates:
                group = min(candidates, key=lambda g: str(g[kind]))
                ids = group[kind] if isinstance(group[kind], list) else [group[kind]]
                examples.append(
                    {
                        "profile": key,
                        "kind": kind,
                        "signature": group["signature"],
                        "rows": [by_id[i] for i in ids],
                        "overlapping_insufficiency": bool(
                            group["ambiguity_pair"] and group["neither_witness"]
                        ),
                    }
                )
    zero_error64 = -math.expm1(math.log(0.05 / 68) / 64)
    minimum_zero_error = math.ceil(math.log(0.05 / 68) / math.log(0.9))
    atomic(
        root / "physical_effects_and_secondary.json",
        {
            "physical_effects": physical_effects(rows),
            "selected_recovery_effects": selected_effects,
            "secondary_tables": tables,
            "witness_examples": examples,
            "calibration_design_feasibility": {
                "characterization_parents": 64,
                "new_calibration_fit": False,
                "alpha_reserved_old_standard": 0.05 / 68,
                "hypothetical_zero_error64_upper": zero_error64,
                "minimum_zero_error_parents": minimum_zero_error,
                "interpretation": "Design-only support diagnostic under the reserved old68-stratum standard; no gate fitted or enabled, no held-out outcomes used for threshold selection.",
            },
            "secondary_recommendation_seal_sha256": sha(
                root / "secondary_recommendation_seal.json"
            ),
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {
                "physical_pairs": len(rows),
                "secondary_records": len(secondary),
                "examples": len(examples),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    run(a.root)
