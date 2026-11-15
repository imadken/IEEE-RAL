"""Fixed grouped estimates for v1.2; no fitting or outcome-selected settings."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_recovery_audit import gz
from dsre_science_offline import ceiling, row_scores


def ratio_interval(nums, dens, weights):
    num = np.asarray(nums, dtype=float)
    den = np.asarray(dens, dtype=float)
    point = float(num.sum() / den.sum()) if den.sum() else None
    totals = weights @ den
    numerators = weights @ num
    valid = totals > 0
    interval = (
        np.quantile(numerators[valid] / totals[valid], [0.025, 0.975]).tolist()
        if valid.any()
        else [None, None]
    )
    return {
        "estimate": point,
        "lower": interval[0],
        "upper": interval[1],
        "numerator": int(num.sum()),
        "denominator": int(den.sum()),
        "bootstrap_defined_draws": int(valid.sum()),
    }


def weights_for(n):
    rng = np.random.default_rng(2026111504)
    indices = rng.integers(0, n, (4000, n))
    return np.asarray([np.bincount(row, minlength=n) for row in indices], dtype=float)


def aggregate(records, extra_condition=False):
    fields = (
        "adequate",
        "inadequate",
        "stop",
        "required_total",
        "required_selected",
        "recover_only_selected",
        "harmful_recover",
        "correct_continue",
        "maintenance",
        "neither_deferred",
        "literals",
        "false_assertions",
        "noninvariant_assertions",
    )
    counts = defaultdict(Counter)
    parents = defaultdict(lambda: defaultdict(Counter))
    for rec in records:
        key = "|".join(
            rec[k] for k in ("population", "task", "scenario", "mode", "method")
        )
        keys = [key] + ([key + "|" + rec["condition"]] if extra_condition else [])
        for k in keys:
            value = {f: rec[f] for f in fields}
            value["rows"] = 1
            counts[k].update(value)
            parents[k][rec["group"]].update(value)
    results = {}
    draw_cache = {}
    for key, count in counts.items():
        groups = sorted(parents[key])
        n = len(groups)
        if n not in draw_cache:
            draw_cache[n] = weights_for(n)
        w = draw_cache[n]
        arrays = {
            f: np.asarray([parents[key][g][f] for g in groups], dtype=float)
            for f in (*fields, "rows")
        }
        intervals = {}
        for name, num, den in (
            ("adequacy", "adequate", "rows"),
            ("inadequacy", "inadequate", "rows"),
            ("abstention", "stop", "rows"),
            ("necessary_recovery_recall", "required_selected", "required_total"),
            ("conditional_inadequacy", "inadequate", None),
            ("average_explanation_length_selected", "literals", None),
            ("factual_assertion_error", "false_assertions", "literals"),
        ):
            denominator = (
                arrays[den] if den is not None else arrays["rows"] - arrays["stop"]
            )
            intervals[name] = ratio_interval(arrays[num], denominator, w)
        results[key] = {**count, "parents": n, "intervals": intervals}
    return results, parents


def paired_difference(parents, key_a, key_b, field="adequate"):
    a, b = parents[key_a], parents[key_b]
    groups = sorted(a)
    assert set(groups) == set(b)
    assert all(a[g]["rows"] == b[g]["rows"] for g in groups)
    nums = [a[g][field] - b[g][field] for g in groups]
    dens = [a[g]["rows"] for g in groups]
    return ratio_interval(nums, dens, weights_for(len(groups)))


def compatible_profiles(rows):
    from dual_rec.dsre.features import ObservationHistory
    from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence

    result = {}
    for population, task in sorted({(r["population"], r["task"]) for r in rows}):
        selected = [
            r for r in rows if (r["population"], r["task"]) == (population, task)
        ]
        for rho in (0, 0.001, 0.005):
            values = []
            for row in selected:
                h = ObservationHistory.model_validate(row["runtime_history"])
                e = bounded_evidence(
                    h,
                    MeasurementScope(
                        coordinate_error_m=rho,
                        decision_time=h.current.time,
                        reference_scope_identity="descriptive",
                        source_regime=population,
                    ),
                )
                values.append(tuple(f.invariant for f in e.facts))
            for n in (6, 7, 12):
                signatures = [v[:n] for v in values]
                counts = []
                examples = []
                for i, query in enumerate(signatures):
                    compatible = [
                        j
                        for j, x in enumerate(signatures)
                        if all(
                            a is None or b is None or a == b
                            for a, b in zip(query, x, strict=True)
                        )
                    ]
                    common = [
                        a
                        for a in ("continue", "recover")
                        if all(
                            selected[j]["outcomes"][a + "_value"] is True
                            for j in compatible
                        )
                    ]
                    counts.append(bool(common))
                    if not common and len(examples) < 4:
                        examples.append(
                            {
                                "query": selected[i]["id"],
                                "compatible_ids": [
                                    selected[j]["id"] for j in compatible
                                ],
                                "signature": query,
                            }
                        )
                # Independent all-known-difference bitsets, no pairwise list reuse.
                all_mask = (1 << len(selected)) - 1
                literal_masks = {
                    (i, v): sum(
                        1 << j
                        for j, x in enumerate(signatures)
                        if x[i] is None or x[i] == v
                    )
                    for i in range(n)
                    for v in (False, True)
                }
                bad = {
                    a: sum(
                        1 << j
                        for j, r in enumerate(selected)
                        if not r["outcomes"][a + "_value"]
                    )
                    for a in ("continue", "recover")
                }
                mass = 0
                for query in signatures:
                    mask = all_mask
                    for i, v in enumerate(query):
                        if v is not None:
                            mask &= literal_masks[i, v]
                    mass += any(mask & bad[a] == 0 for a in bad)
                assert mass == sum(counts)
                result[f"{population}|{task}|rho{rho}|facts{n}"] = {
                    "rows": len(selected),
                    "parents": len({r["group"] for r in selected}),
                    "literal_compatible_common_action_mass": mass,
                    "fraction": mass / len(selected),
                    "support": "Same-table hindsight; ignores minimum2-parent requirement. Not a deployed policy or population guarantee.",
                    "examples": examples,
                }
    return result


def offline_uncertainty(root):
    with gzip.open(root / "offline_decisions.jsonl.gz", "rt") as f:
        records = [json.loads(s) for s in f]
    tables, parents = aggregate(records)
    comparisons = {}
    for population, task in sorted({(r["population"], r["task"]) for r in records}):
        for scenario in (
            "clean",
            "bound001",
            "bound005",
            "uniform0.005_r0",
            "uniform0.005_r1",
            "uniform0.005_r2",
            "delay5_equal_250ms",
        ):
            base = f"{population}|{task}|{scenario}"
            comparisons[base + "|robustDSRE_vs_point"] = paired_difference(
                parents,
                base + "|robust_proposal|DSRE_risk",
                base + "|point_proposal|DSRE_risk",
            )
            comparisons[base + "|robustDSRE_vs_CART2"] = paired_difference(
                parents,
                base + "|robust_proposal|DSRE_risk",
                base + "|robust_proposal|CART2_beta10",
            )
            comparisons[base + "|robust_strict_vs_margin"] = paired_difference(
                parents,
                base + "|robust_proposal|DSRE_strict",
                base + "|margin_all_inputs|margin_DSRE_strict",
            )
    atomic(
        root / "offline_uncertainty.json",
        {
            "tables": tables,
            "paired_comparisons": comparisons,
            "bootstrap_draws": 4000,
            "seed": 2026111504,
            "epoch": time.time(),
        },
    )
    with gzip.open(root / "offline_rows.jsonl.gz", "rt") as f:
        rows = [json.loads(s) for s in f]
    atomic(
        root / "mechanism_compatibility.json",
        {
            "analysis": "Secondary literal-compatibility diagnostic, distinguishes exact ternary-pattern partitions from missing-literal semantics; no policies or thresholds changed",
            "profiles": compatible_profiles(rows),
            "independent_bitset_check": True,
            "epoch": time.time(),
        },
    )


def prospective(root):
    if (root / "prospective_results.json").exists():
        raise ValueError("Prospective results already written")
    plan = read(root / "study_plan.json")
    qualification = read(root / "pilot_qualification_seal.json")
    seal = read(root / "prospective_recommendation_seal.json")
    rows = []
    records = []
    funnel = []
    route_ms = []
    for index, seed in enumerate(plan["primary_seeds"]):
        progress = root / "progress" / f"outcome-{index:04d}.json"
        if not progress.exists() or read(progress)["status"] != "COMPLETE":
            funnel.append(
                {
                    "seed": seed,
                    "index": index,
                    "status": "INCOMPLETE_OR_UNEXECUTED",
                    "split": "development" if index < 64 else "confirmation",
                }
            )
            continue
        d = root / "prospective" / str(seed)
        rec = read(d / "recommendations.json")
        assert sha(d / "recommendations.json") == seal["parents"][str(seed)]
        for cell in rec["cells"]:
            c = cell["condition"]
            raw = gz(d / c / "screen.json.gz")
            row = {
                **raw["summary"],
                "id": f"PickCube-v1/{seed}/{c}",
                "group": f"PickCube-v1/{seed}",
                "population": "new_development" if index < 64 else "new_confirmation",
                "outcomes": {
                    a + "_value": gz(d / c / (a + ".json.gz"))["terminal_success"]
                    for a in ("continue", "recover")
                },
                "source": str(d / c / "screen.json.gz"),
                "source_sha256": sha(d / c / "screen.json.gz"),
                "offset_x_m": raw["offset_x_m"],
            }
            rows.append(row)
            route_ms.append(raw["route_ms"])
            true = tuple(
                raw["summary"]["features"] + raw["summary"]["optional_features"]
            )
            for scenario, data in raw["scenarios"].items():
                invariant = tuple(f["invariant"] for f in data["measurement"]["facts"])
                for mode in ("point_proposal", "robust_proposal", "margin_all_inputs"):
                    scored = row_scores(
                        row, scenario, mode, data[mode], true, invariant
                    )
                    records += scored
                    if mode == "robust_proposal":
                        assert all(
                            r["false_assertions"] == 0
                            and r["noninvariant_assertions"] == 0
                            for r in scored
                        )
            funnel.append(
                {
                    "seed": seed,
                    "condition": c,
                    "status": "QUALIFIED_PAIRED_COMPLETE",
                    "split": row["population"],
                }
            )
    with gzip.open(root / "prospective_rows.jsonl.gz", "wt") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    with gzip.open(root / "prospective_decisions.jsonl.gz", "wt") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    tables, parents = aggregate(records, True)
    comparisons = {}
    for population in ("new_development", "new_confirmation"):
        for scenario in (
            "clean",
            "bound001",
            "bound005",
            "uniform0.005_r0",
            "uniform0.005_r1",
            "uniform0.005_r2",
        ):
            base = f"{population}|PickCube-v1|{scenario}"
            if base + "|robust_proposal|DSRE_risk" not in parents:
                continue
            for name, left, right in (
                ("DSRE_vs_B7", "robust_proposal|DSRE_risk", "robust_proposal|B7_risk"),
                (
                    "DSRE_vs_CART2",
                    "robust_proposal|DSRE_risk",
                    "robust_proposal|CART2_beta10",
                ),
                (
                    "strict_vs_margin",
                    "robust_proposal|DSRE_strict",
                    "margin_all_inputs|margin_DSRE_strict",
                ),
                (
                    "robust_vs_point",
                    "robust_proposal|DSRE_risk",
                    "point_proposal|DSRE_risk",
                ),
                (
                    "strict_vs_CART2",
                    "robust_proposal|DSRE_strict",
                    "robust_proposal|CART2_strict",
                ),
            ):
                comparisons[base + "|" + name] = paired_difference(
                    parents, base + "|" + left, base + "|" + right
                )
    classes = {}
    for population in ("new_development", "new_confirmation"):
        for condition in [*qualification["qualified_conditions"], "ALL"]:
            selected = [
                r
                for r in rows
                if r["population"] == population
                and (condition == "ALL" or r["condition"] == condition)
            ]
            if not selected:
                continue
            count = Counter(
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
            for row in selected:
                c, r = row["outcomes"].values()
                count[
                    "both"
                    if c and r
                    else "continue_only"
                    if c
                    else "recover_only"
                    if r
                    else "neither"
                ] += 1
                count["required_recovery"] += int(
                    not row["initial_success"] and not c and r
                )
                count["initial_failed"] += int(not row["initial_success"])
            classes[population + "|" + condition] = {
                **count,
                "rows": len(selected),
                "parents": len({r["group"] for r in selected}),
            }
    mechanism = {}
    for pop in ("new_development", "new_confirmation"):
        selected = [r for r in rows if r["population"] == pop]
        if not selected:
            continue
        for n in (6, 7, 12):
            mechanism[pop + "|point" + str(n)] = ceiling(
                selected,
                [(r["features"] + r["optional_features"])[:n] for r in selected],
            )
        for c in qualification["qualified_conditions"]:
            arm = [r for r in selected if r["condition"] == c]
            if arm:
                mechanism[pop + "|" + c + "|point7"] = ceiling(
                    arm, [(r["features"] + r["optional_features"])[:7] for r in arm]
                )
    atomic(
        root / "prospective_results.json",
        {
            "qualified_conditions": qualification["qualified_conditions"],
            "unqualified_conditions": qualification["unqualified_conditions"],
            "registered_development_parents": 64,
            "registered_confirmation_parents": 128,
            "completed_parent_groups": len({r["group"] for r in rows}),
            "qualified_checkpoints": len(rows),
            "outcome_classes": classes,
            "tables": tables,
            "paired_comparisons": comparisons,
            "mechanism": mechanism,
            "funnel": funnel,
            "all_altered_source_policies": "UNQUALIFIED_PROPOSALS: no original calibration transfer",
            "routing_all_scenarios_ms": {
                "median": float(np.median(route_ms)),
                "p95": float(np.quantile(route_ms, 0.95)),
                "total": sum(route_ms),
            },
            "epoch": time.time(),
        },
    )
    atomic(
        root / "prospective_compatibility.json",
        {
            "profiles": compatible_profiles(rows),
            "independent_bitset_check": True,
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {
                "rows": len(rows),
                "parents": len({r["group"] for r in rows}),
                "records": len(records),
                "tables": len(tables),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["offline", "prospective"])
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.command == "offline":
        offline_uncertainty(a.root)
    else:
        prospective(a.root)
