"""Untouched suffix-only inference and separately labeled pooled description."""

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_paper_confirmation import audit_trace, independent_tree_action, predicates
from dsre_paper_reanalysis import cluster_interval, summarize
from dsre_repair_experiment import predict

from dual_rec.dsre.baselines import OutcomeTree
from dual_rec.dsre.repair import ParentIndex, ParentRules, RepairQuery, RepairTable
from dual_rec.dsre.repair_oracle import Oracle

METHODS = (
    "DSRE",
    "B7",
    "B1_two_strict",
    "CART1_strict",
    "CART2_strict",
    "B5_beta10",
    "CART1_beta10",
    "CART2_beta10",
    "B0_continue",
    "B0_recover",
)


def collect(root):
    manifest = read(root / "fresh_seed_manifest.json")["parents"]
    qualified = []
    complete = []
    missing = []
    for parent in manifest:
        progress = root / "parent_progress" / f"{parent['index']:04d}.json"
        primary = progress.exists() and read(progress)["status"] == "COMPLETE"
        cells = []
        for condition in parent["conditions"]:
            path = (
                root
                / "fresh"
                / parent["task"]
                / f"{parent['seed']}-{condition}"
                / "summary.json"
            )
            if path.exists():
                summary = read(path)
                assert summary["group"] == parent["group"]
                assert sha(Path(summary["source"])) == summary["source_sha256"]
                qualified.append(summary)
                cells.append(summary)
        if primary:
            assert len(cells) == 2
            marked = read(progress)
            assert {x["id"] for x in marked["checkpoints"]} == {r["id"] for r in cells}
            complete.extend(cells)
        else:
            missing.append(
                {
                    "group": parent["group"],
                    "status": read(progress)["status"]
                    if progress.exists()
                    else "UNTOUCHED_NOT_EXECUTED",
                    "qualified_secondary_cells": [r["id"] for r in cells],
                }
            )
    return qualified, complete, missing


def score(rows, frozen):
    """Main implementation receives no query outcomes; audit uses integer-mask rules."""
    records = []
    decisions = {}
    queries_checked = 0
    for task, settings in frozen["tasks"].items():
        for budget, setting in settings.items():
            table = RepairTable.model_validate(setting["table"])
            index = ParentIndex(table, setting["parent_groups"], 2)
            rules = ParentRules(table, setting["parent_groups"], 2)
            oracle = Oracle(setting["table"], setting["parent_groups"])
            trees = {}
            for depth, nodes in setting["trees"].items():
                tree = OutcomeTree.__new__(OutcomeTree)
                tree.rules = rules
                tree.nodes = nodes
                tree.root = 0
                trees[depth] = tree
            cache = {}
            for row in [r for r in rows if r["task"] == task]:
                x = tuple(row["features"]) + tuple(
                    row["optional_features"][i] for i in setting["selected"]
                )
                if x not in cache:
                    query = RepairQuery(scope=table.scope, features=x)
                    strict = predict("DSRE", query, index, rules, trees)
                    oracle.verify(query.model_dump(mode="json"), strict["diagnosis"])
                    output = {}
                    for method in METHODS:
                        result = (
                            strict
                            if method == "DSRE"
                            else predict(method, query, index, rules, trees, strict)
                        )
                        if method in ("B7", "B5_beta10", "B1_two_strict"):
                            independent = oracle.rule(
                                query.model_dump(mode="json"),
                                0.1 if method == "B5_beta10" else 0,
                                2 if method == "B1_two_strict" else None,
                            )
                            assert result["action"] == (
                                independent["action"] if independent else None
                            )
                            if independent:
                                assert result["evidence"] == independent["evidence"]
                        if method.startswith("CART"):
                            assert result["action"] == independent_tree_action(
                                setting["trees"][method[4]],
                                setting["table"],
                                setting["parent_groups"],
                                x,
                                0.9 if method.endswith("beta10") else 1,
                            )
                        output[method] = result
                        decisions[f"{task}|{budget}|{method}|{x}"] = {
                            "query": query.model_dump(mode="json"),
                            "result": result,
                        }
                        queries_checked += 1
                    assert (
                        output["B7"]["action"] == strict["action"]
                        and output["B7"]["evidence"] == strict["evidence"]
                    )
                    cache[x] = output
                for method, result in cache[x].items():
                    action = result["action"]
                    success = bool(action and row["outcomes"][action + "_value"])
                    c, r = (
                        row["outcomes"]["continue_value"],
                        row["outcomes"]["recover_value"],
                    )
                    category = (
                        "both"
                        if c and r
                        else "continue_only"
                        if c
                        else "recover_only"
                        if r
                        else "neither"
                    )
                    records.append(
                        {
                            "id": row["id"],
                            "group": row["group"],
                            "task": task,
                            "budget": int(budget),
                            "method": method,
                            "initial_success": row["initial_success"],
                            "category": category,
                            "action": action,
                            "recommended": int(action is not None),
                            "successful": int(success),
                            "unacceptable": int(action is not None and not success),
                            "literals": len(result["evidence"]),
                            "support_rows": result["support"],
                            "support_parents": result["independent_parents"],
                            "necessary_adequate_action": int(
                                success
                                and category in ("continue_only", "recover_only")
                            ),
                            "adequate_either_action": int(
                                success and category == "both"
                            ),
                            "added_channels": len(setting["selected"]),
                            "decision_key": f"{task}|{budget}|{method}|{x}",
                        }
                    )
    return records, decisions, queries_checked


def statistics(records, seed):
    grouped = defaultdict(list)
    for row in records:
        key = f"{row['task']}|{row['budget']}|{row['method']}"
        for population in (
            "all",
            "initial_success" if row["initial_success"] else "initial_failure",
            row["category"],
            "action_" + (row["action"] or "abstain"),
        ):
            grouped[key + "|" + population].append(row)
    tables = {}
    for key, rs in grouped.items():
        tables[key] = summarize(rs) | {
            "abstained": sum(not r["recommended"] for r in rs),
            "support_rows_sum": sum(r["support_rows"] for r in rs if r["recommended"]),
            "support_parents_sum": sum(
                r["support_parents"] for r in rs if r["recommended"]
            ),
            "necessary_action_successes": sum(
                r["necessary_adequate_action"] for r in rs
            ),
            "both_success_adequate_choices": sum(
                r["adequate_either_action"] for r in rs
            ),
        }
    contrasts = {}
    equivalences = {}
    assignments = {}
    decomposition = []
    for tindex, task in enumerate(("PickCube-v1", "PushCube-v1")):
        parents = {r["group"] for r in records if r["task"] == task}
        ds = {
            b: {
                r["id"]: r
                for r in records
                if r["task"] == task and r["budget"] == b and r["method"] == "DSRE"
            }
            for b in (0, 1)
        }
        for population in (
            "all",
            "initial_failure",
            "initial_success",
            "recover_only",
            "continue_only",
            "both",
            "neither",
        ):
            pairs = []
            for rid, base in ds[0].items():
                if population not in (
                    "all",
                    base["category"],
                    "initial_success" if base["initial_success"] else "initial_failure",
                ):
                    continue
                later = ds[1][rid]
                pairs.append(
                    {
                        "group": base["group"],
                        "success_difference": later["successful"] - base["successful"],
                        "coverage_difference": later["recommended"]
                        - base["recommended"],
                        "unacceptable_difference": later["unacceptable"]
                        - base["unacceptable"],
                    }
                )
            contrasts[f"{task}|b1-b0|{population}"] = {
                f: cluster_interval(pairs, f, seed + tindex, parent_groups=parents)
                for f in (
                    "success_difference",
                    "coverage_difference",
                    "unacceptable_difference",
                )
            }
        for rid, base in ds[0].items():
            later = ds[1][rid]
            decomposition.append(
                {
                    "id": rid,
                    "group": base["group"],
                    "task": task,
                    "category": base["category"],
                    "initial_success": base["initial_success"],
                    "b0_action": base["action"],
                    "b1_action": later["action"],
                    "b0_success": base["successful"],
                    "b1_success": later["successful"],
                    "success_difference": later["successful"] - base["successful"],
                    "required_recovery_success_difference": int(
                        later["successful"]
                        and later["action"] == "recover"
                        and later["category"] == "recover_only"
                    )
                    - int(
                        base["successful"]
                        and base["action"] == "recover"
                        and base["category"] == "recover_only"
                    ),
                }
            )
        for budget in (0, 1):
            for method in METHODS:
                selected = {
                    r["id"]: r
                    for r in records
                    if r["task"] == task
                    and r["budget"] == budget
                    and r["method"] == method
                }
                equivalences[f"{task}|{budget}|DSRE-{method}"] = {
                    "checkpoints": len(selected),
                    "action_disagreements": sum(
                        ds[budget][rid]["action"] != r["action"]
                        for rid, r in selected.items()
                    ),
                }
                for action in ("continue", "recover"):
                    assigned = [r for r in selected.values() if r["action"] == action]
                    assignments[f"{task}|{budget}|{method}|{action}"] = {
                        "checkpoints": len(assigned),
                        "assigned_parents": len({r["group"] for r in assigned}),
                        "error_parents": len(
                            {r["group"] for r in assigned if r["unacceptable"]}
                        ),
                        "status": "NOT_CALIBRATED",
                        "previous_zero_error_parent_requirement": 42,
                    }
                if method in ("DSRE", "B7", "B0_continue", "B0_recover"):
                    continue
                for population in ("all", "initial_failure"):
                    pairs = [
                        {
                            "group": r["group"],
                            "success_difference": ds[budget][rid]["successful"]
                            - r["successful"],
                            "unacceptable_difference": ds[budget][rid]["unacceptable"]
                            - r["unacceptable"],
                        }
                        for rid, r in selected.items()
                        if population == "all" or not r["initial_success"]
                    ]
                    contrasts[f"{task}|b{budget}|DSRE-{method}|{population}"] = {
                        f: cluster_interval(
                            pairs, f, seed + tindex, parent_groups=parents
                        )
                        for f in ("success_difference", "unacceptable_difference")
                    }
    return {
        "tables": tables,
        "paired_intervals": contrasts,
        "equivalences": equivalences,
        "assignment_counts": assignments,
        "decision_necessity_records": decomposition,
        "bootstrap_seed": seed,
        "draws": 4000,
        "calibration": "NOT_CALIBRATED",
    }


def analyze(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence sealed")
    verify_freeze(root)
    started = time.process_time()
    qualified, primary, missing = collect(root)
    atomic(
        root / "followup_missingness.json",
        {
            "registered_parents": 333,
            "registered_checkpoints": 666,
            "qualified_checkpoints": len(qualified),
            "primary_checkpoints": len(primary),
            "complete_parents": len(primary) // 2,
            "missing_or_partial_parents": missing,
            "secondary_qualified_cells": [
                r["id"] for r in qualified if r["id"] not in {s["id"] for s in primary}
            ],
        },
    )
    audits = [audit_trace(row, root) for row in qualified]
    # Outcomes are read twice: main scoring uses summaries; independent scoring reads raw terminal states.
    independent_rows = []
    for row in primary:
        with gzip.open(row["source"], "rt") as stream:
            raw = json.load(stream)
        features, optional = predicates(
            raw["prefix"][0]["observation"], raw["canonical_start"]["observation"]
        )
        independent_rows.append(
            row
            | {
                "features": features,
                "optional_features": optional,
                "outcomes": {
                    a + "_value": bool(
                        raw["traces"][a]["frames"][-1]["state"]["success"]
                    )
                    for a in ("continue", "recover")
                },
                "initial_success": bool(raw["canonical_start"]["success"]),
            }
        )
    frozen = read(root / "frozen_routers.json")
    records, decisions, checks = score(primary, frozen)
    # Full independent rule/predicate calculation is checked by Oracle inside score and audit_trace.
    independent_lookup = {r["id"]: r for r in independent_rows}
    for row in records:
        raw = independent_lookup[row["id"]]
        expected = int(
            row["action"] is not None and raw["outcomes"][row["action"] + "_value"]
        )
        assert (
            row["successful"] == expected
            and row["initial_success"] == raw["initial_success"]
        )
    config = read(Path("config/dsre_followup.json"))
    result = statistics(records, config["bootstrap_seed"])
    atomic(root / "suffix_results.json", result)
    atomic(root / "suffix_prediction_records.json", records)
    atomic(root / "suffix_decisions.json", decisions)
    old = Path(config["previous_root"])
    old_complete = set(
        read(old / "physics_completed.json")["fully_completed_seed_parents"]
    )
    earlier = [
        json.loads(s)
        for s in (old / "fresh_qualified.jsonl").read_text().splitlines()
        if json.loads(s)["group"] in old_complete
    ]
    assert not {r["group"] for r in earlier} & {r["group"] for r in primary}
    earlier_records, _, _ = score(earlier, frozen)
    pooled = statistics(earlier_records + records, config["pooled_bootstrap_seed"])
    pooled["interpretation"] = (
        "SECONDARY_DESCRIPTIVE_POOL: earlier interrupted cohort inspected before follow-up design; not untouched independent confirmation; orphan excluded."
    )
    atomic(root / "pooled_secondary_results.json", pooled)
    atomic(
        root / "independent_audit.json",
        {
            "status": "PASS",
            "new_qualified_traces": len(audits),
            "new_primary_checkpoints": len(primary),
            "outcome_controls_checked": sum(
                r["outcome_controls_checked"] for r in audits
            ),
            "prefix_states_checked": sum(r["prefix_states_checked"] for r in audits),
            "maximum_action_error": max(
                (r["maximum_action_error"] for r in audits), default=0
            ),
            "unique_rule_tree_queries_checked": checks,
            "prediction_views": len(records),
            "selected_outcomes_recomputed_from_raw": len(records),
            "implementations": "Main finite-reference solver/feature extractor versus independent integer-mask rule, raw predicate and action-equation audit; same session, not external human replication.",
            "cpu_seconds": time.process_time() - started,
            "new_model_fits": 0,
        },
    )
    atomic(root / "replay_audit_records.json", audits)
    print(
        json.dumps(
            {
                "status": "PASS",
                "suffix_primary_checkpoints": len(primary),
                "complete_parents": len(primary) // 2,
                "missing_parents": len(missing),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    analyze(parser.parse_args().root)
