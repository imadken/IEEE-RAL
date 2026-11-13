"""Independent paper tables from sealed predictions, including parent uncertainty."""

import argparse
import hashlib
import json
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from dual_rec.dsre.repair_oracle import Oracle, finite_mass


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def cluster_interval(records, field, seed=2026111319, draws=4000, parent_groups=None):
    contributing = {r["group"] for r in records}
    groups = sorted(contributing if parent_groups is None else set(parent_groups))
    if not records or not groups:
        return None
    values = np.array(
        [
            [
                sum(r[field] for r in records if r["group"] == g),
                sum(1 for r in records if r["group"] == g),
            ]
            for g in groups
        ],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    samples = values[rng.integers(0, len(groups), size=(draws, len(groups)))].sum(
        axis=1
    )
    samples = samples[samples[:, 1] > 0]
    rates = samples[:, 0] / samples[:, 1]
    return {
        "value": float(values[:, 0].sum() / values[:, 1].sum()),
        "parent_percentile95": np.quantile(rates, [0.025, 0.975]).tolist(),
        "independent_parents": len(groups),
        "contributing_parents": len(contributing),
        "draws": draws,
    }


def summarize(records):
    return {
        "checkpoints": len(records),
        "parents": len({r["group"] for r in records}),
        "recommended": sum(r["recommended"] for r in records),
        "successful": sum(r["successful"] for r in records),
        "unacceptable": sum(r["unacceptable"] for r in records),
        "continue": sum(r["action"] == "continue" for r in records),
        "recover": sum(r["action"] == "recover" for r in records),
        "literals": sum(r["literals"] for r in records),
    }


def reanalyze(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence sealed; reproduce in a separate scratch root")
    cpu_started = time.process_time()
    old = Path("results/dsre-evidence-repair/20261113T180828Z")
    rows = {
        r["id"]: r
        for r in map(
            json.loads, (old / "qualified_pairs.jsonl").read_text().splitlines()
        )
    }
    expanded, errors, equivalence, audited = [], [], 0, 0
    # Audit each unique saved model decision independently of the implementation solver.
    for path in sorted((old / "models").glob("*.json")):
        model = load(path)
        oracle = Oracle(model["table"], model["parent_groups"])
        cache = {}
        for decision in model["decisions"].values():
            if decision["method"] != "DSRE":
                continue
            query, actual = decision["query"], decision["result"]
            key = tuple(query["features"])
            expected = cache.setdefault(key, oracle.rule(query))
            assert actual["action"] == (
                None if expected is None else expected["action"]
            )
            if expected:
                for field in ("evidence", "support", "independent_parents"):
                    assert actual[field] == expected[field], (path, field)
            audited += 1
    for path in sorted((old / "designs").glob("*.json")):
        design = load(path)
        for setting in design["selected_designs"]:
            model = load(old / "models" / (setting["model"] + ".json"))
            predictions = {
                (p["id"], p["method"]): model["decisions"][p["decision_id"]]["result"]
                for p in model["predictions"]
            }
            for rid in design["evaluation_ids"]:
                ds, b7 = predictions[rid, "DSRE"], predictions[rid, "B7"]
                for field in ("action", "evidence"):
                    assert ds[field] == b7[field], (rid, field)
                if ds["action"]:
                    assert ds["support"] == b7["support"]
                equivalence += 1
            if setting["selector"] != "exact_coverage":
                continue
            for (rid, method), result in predictions.items():
                source = rows[rid]
                action = result["action"]
                category = (
                    "both"
                    if all(source["outcomes"].values())
                    else "neither"
                    if not any(source["outcomes"].values())
                    else "continue_only"
                    if source["outcomes"]["continue_value"]
                    else "recover_only"
                )
                success = bool(action and source["outcomes"][action + "_value"])
                record = {
                    "id": rid,
                    "group": source["group"],
                    "task": source["task"],
                    "fold": design["fold"],
                    "budget": setting["budget"],
                    "method": method,
                    "initial_success": source["initial_success"],
                    "category": category,
                    "action": action,
                    "recommended": int(action is not None),
                    "successful": int(success),
                    "unacceptable": int(action is not None and not success),
                    "literals": len(result["evidence"]),
                }
                expanded.append(record)
                if method == "DSRE" and record["unacceptable"]:
                    reference = model["table"]["rows"]
                    signature = tuple(source["features"]) + tuple(
                        source["optional_features"][i] for i in setting["channels"]
                    )
                    exact = [r for r in reference if tuple(r["features"]) == signature]
                    errors.append(
                        record
                        | {
                            "selected": setting["channels"],
                            "observed_outcomes": source["outcomes"],
                            "training_exact_signature_rows": len(exact),
                            "training_exact_signature_neither": sum(
                                not any(r["outcomes"].values()) for r in exact
                            ),
                            "training_exact_signature_opposite": sum(
                                not r["outcomes"][action + "_value"] for r in exact
                            ),
                            "explanation": result["evidence"],
                            "reference": str(
                                old / "models" / (setting["model"] + ".json")
                            ),
                            "reason": "Training rule is pure but excludes the held-out unfavorable outcome; a finite-reference guarantee does not transfer.",
                        }
                    )
    grouped = defaultdict(list)
    for r in expanded:
        base = f"{r['task']}|{r['budget']}|{r['method']}"
        for slice_name in (
            "all",
            "initial_success" if r["initial_success"] else "initial_failure",
            r["category"],
            "fold" + str(r["fold"]),
        ):
            grouped[base + "|" + slice_name].append(r)
    tables = {key: summarize(rs) for key, rs in grouped.items()}
    contrasts = {}
    for tindex, task in enumerate(("PickCube-v1", "PushCube-v1")):
        parent_groups = {r["group"] for r in rows.values() if r["task"] == task}
        for budget in (1, 2, 3):
            first = {
                r["id"]: r
                for r in expanded
                if r["task"] == task and r["budget"] == 0 and r["method"] == "DSRE"
            }
            last = {
                r["id"]: r
                for r in expanded
                if r["task"] == task and r["budget"] == budget and r["method"] == "DSRE"
            }
            for population in ("all", "initial_failure", "initial_success"):
                rs = [
                    {
                        "group": r["group"],
                        "difference": last[rid]["successful"] - r["successful"],
                    }
                    for rid, r in first.items()
                    if population == "all"
                    or r["initial_success"] == (population == "initial_success")
                ]
                contrasts[f"{task}|b{budget}-b0|{population}"] = cluster_interval(
                    rs, "difference", 2026111319 + tindex, parent_groups=parent_groups
                )
        for budget in range(4):
            for comparator in (
                "B1_two_strict",
                "CART2_strict",
                "B5_beta10",
                "CART2_beta10",
            ):
                reference = {
                    r["id"]: r
                    for r in expanded
                    if r["task"] == task
                    and r["budget"] == budget
                    and r["method"] == comparator
                }
                dsre = {
                    r["id"]: r
                    for r in expanded
                    if r["task"] == task
                    and r["budget"] == budget
                    and r["method"] == "DSRE"
                }
                for population in ("all", "initial_failure", "initial_success"):
                    rs = [
                        {
                            "group": r["group"],
                            "difference": r["successful"]
                            - reference[rid]["successful"],
                            "error_difference": r["unacceptable"]
                            - reference[rid]["unacceptable"],
                        }
                        for rid, r in dsre.items()
                        if population == "all"
                        or r["initial_success"] == (population == "initial_success")
                    ]
                    contrasts[f"{task}|b{budget}|DSRE-{comparator}|{population}"] = {
                        f: cluster_interval(
                            rs, f, 2026111319 + tindex, parent_groups=parent_groups
                        )
                        for f in ("difference", "error_difference")
                    }
    intervals = {}
    for key, rs in grouped.items():
        if "|DSRE|" in key:
            task = key.split("|")[0]
            parents = {r["group"] for r in rows.values() if r["task"] == task}
            if "|fold" in key:
                parents = {r["group"] for r in rs}
            intervals[key] = {
                field: cluster_interval(rs, field, parent_groups=parents)
                for field in ("successful", "recommended", "unacceptable")
            }
    finite = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        population = [r for r in rows.values() if r["task"] == task]
        for budget in (0, 1, 2, 3, 6):
            candidates = [
                j for k in range(budget + 1) for j in combinations(range(6), k)
            ]
            chosen = min(
                candidates, key=lambda j: (-finite_mass(population, j), len(j), j)
            )
            finite[f"{task}|{budget}"] = {
                "selected": chosen,
                "mass": finite_mass(population, chosen),
                "total": len(population),
            }
    save(root / "reused_stratified_tables.json", tables)
    save(root / "reused_paired_intervals.json", contrasts)
    save(root / "reused_stratified_intervals.json", intervals)
    save(root / "reused_error_inspection.json", errors)
    save(root / "reused_finite_ceiling.json", finite)
    save(root / "reused_prediction_records.json", expanded)
    save(
        root / "reused_independent_audit.json",
        {
            "status": "PASS",
            "unique_DSRE_decisions_audited": audited,
            "B7_equal_views": equivalence,
            "expanded_exact_selector_views": len(expanded),
            "stratified_cells": len(tables),
            "source_table_sha256": hashlib.sha256(
                (old / "qualified_pairs.jsonl").read_bytes()
            ).hexdigest(),
            "new_physics": 0,
            "new_fits": 0,
            "cpu_seconds": time.process_time() - cpu_started,
            "independence": "Separate integer-mask rule oracle and record aggregation; same session, no external human replication.",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "B7_equal_views": equivalence,
                "strict_errors": len(errors),
                "tables": len(tables),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    reanalyze(parser.parse_args().root)
