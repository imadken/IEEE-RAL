"""Fixed operational scoring, independent calibration and disjoint test estimands."""

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

from dsre_followup_analysis import collect
from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_observations import (
    SCENARIOS,
    observation_packet,
    packet_from_summary,
)
from dsre_paper_reanalysis import cluster_interval

from dual_rec.dsre.operational import (
    METHODS,
    OperationalRouter,
    calibrate_records,
    gated_action,
)


def records_for(
    rows, router, frozen, calibration=None, scenario="clean", raw_root=None
):
    result = []
    for row in rows:
        if scenario == "clean":
            packet, metadata = packet_from_summary(row, frozen), {}
        else:
            with gzip.open(row["source"], "rt") as stream:
                raw = json.load(stream)
            packet, metadata = observation_packet(raw, row["task"], scenario, frozen)
        start = time.perf_counter_ns()
        decisions = router.route(packet)
        elapsed = (time.perf_counter_ns() - start) / 1e6
        c, r = (
            bool(row["outcomes"]["continue_value"]),
            bool(row["outcomes"]["recover_value"]),
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
        for method, decision in decisions.items():
            for mode in (
                ("proposal", "calibrated") if calibration is not None else ("proposal",)
            ):
                proposed = decision["action"]
                action = (
                    gated_action(method, row["task"], proposed, calibration)
                    if mode == "calibrated"
                    else proposed
                )
                good = int(bool(action) and (c if action == "continue" else r))
                initial = bool(row["initial_success"])
                result.append(
                    {
                        "id": row["id"],
                        "group": row["group"],
                        "task": row["task"],
                        "condition": row["condition"],
                        "method": method,
                        "mode": mode,
                        "scenario": scenario,
                        "initial_success": initial,
                        "category": category,
                        "proposed_action": proposed,
                        "action": action,
                        "recommended": int(action is not None),
                        "successful": good,
                        "unacceptable": int(action is not None) - good,
                        "deferred": int(action is None),
                        "autonomous_completion": good,
                        "intervention_regret": int(
                            action is not None and not good and (c or r)
                        ),
                        "autonomy_regret": int(bool(c or r)) - good,
                        "unnecessary_recover_initial_success": int(
                            action == "recover" and initial
                        ),
                        "unnecessary_recover_both": int(
                            action == "recover" and c and r
                        ),
                        "required_recovery_success": int(
                            action == "recover" and not initial and not c and r
                        ),
                        "failed_start_success": int(not initial and good),
                        "maintained_success": int(initial and good),
                        "literals": len(decision["evidence"]) if action else 0,
                        "support_parents": decision["independent_parents"]
                        if action
                        else 0,
                        "decision_status": decision["status"],
                        "evidence": decision["evidence"],
                        "route_all_methods_ms": elapsed,
                        **{k: v for k, v in metadata.items() if k != "payload"},
                    }
                )
    return result


SUM_FIELDS = (
    "recommended",
    "successful",
    "unacceptable",
    "deferred",
    "autonomous_completion",
    "intervention_regret",
    "autonomy_regret",
    "unnecessary_recover_initial_success",
    "unnecessary_recover_both",
    "required_recovery_success",
    "failed_start_success",
    "maintained_success",
    "literals",
)


def summarize(records):
    groups = defaultdict(list)
    for r in records:
        head = f"{r['task']}|{r['method']}|{r['mode']}|{r['scenario']}"
        for pop in (
            "all",
            r["condition"],
            "initial_success" if r["initial_success"] else "initial_failure",
            r["category"],
        ):
            groups[head + "|" + pop].append(r)
    tables = {}
    for key, rs in groups.items():
        n = len(rs)
        acted = sum(r["recommended"] for r in rs)
        good = sum(r["successful"] for r in rs)
        tables[key] = {
            "checkpoints": n,
            "parents": len({r["group"] for r in rs}),
            **{f: sum(r[f] for r in rs) for f in SUM_FIELDS},
            "coverage": acted / n,
            "conditional_success": good / acted if acted else None,
            "conditional_unacceptable": (acted - good) / acted if acted else None,
            "autonomous_completion_rate": good / n,
            "continue": sum(r["action"] == "continue" for r in rs),
            "recover": sum(r["action"] == "recover" for r in rs),
        }
    return tables


def paired(records):
    contrasts = {}
    for tindex, task in enumerate(("PickCube-v1", "PushCube-v1")):
        selected = {
            (r["id"], r["method"]): r
            for r in records
            if r["task"] == task
            and r["mode"] == "calibrated"
            and r["scenario"] == "clean"
        }
        parents = {r["group"] for r in selected.values()}
        ids = sorted({r["id"] for r in selected.values()})
        for comparator in METHODS:
            for population in (
                "all",
                "initial_failure",
                "initial_success",
                "recover_only",
            ):
                pairs = []
                for id_ in ids:
                    a, b = selected[id_, "DSRE_risk"], selected[id_, comparator]
                    if population not in (
                        "all",
                        a["category"],
                        "initial_success"
                        if a["initial_success"]
                        else "initial_failure",
                    ):
                        continue
                    pairs.append(
                        {
                            "group": a["group"],
                            **{
                                f: a[f] - b[f]
                                for f in (
                                    "successful",
                                    "unacceptable",
                                    "recommended",
                                    "required_recovery_success",
                                )
                            },
                        }
                    )
                contrasts[f"{task}|DSRE_risk-{comparator}|{population}"] = {
                    f: cluster_interval(
                        pairs, f, 2026111401 + tindex, parent_groups=parents
                    )
                    for f in (
                        "successful",
                        "unacceptable",
                        "recommended",
                        "required_recovery_success",
                    )
                }
    return contrasts


def qualified(root):
    all_, complete, missing = collect(root)
    parent_split = {
        p["group"]: p["split"]
        for p in read(root / "fresh_seed_manifest.json")["parents"]
    }
    for row in all_:
        row["split"] = parent_split[row["group"]]
    return all_, complete, missing


def calibration_stage(root):
    if (root / "calibration_seal.json").exists():
        raise ValueError("Calibration decision is already immutable")
    verify_freeze(root)
    _, rows, _missing = qualified(root)
    rows = [r for r in rows if r["split"] == "calibration"]
    assert len(rows) == 720 and not any(r["split"] == "test" for r in rows)
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    records = records_for(rows, router, frozen)
    from dsre_operational_audit import audit_calibration, audit_rules

    check = audit_rules(router, rows, records)
    strata = calibrate_records(records, planned_complete=True)
    cp = audit_calibration(records, strata)
    atomic(root / "calibration_records.json", records)
    atomic(
        root / "calibration_decision.json",
        {
            "status": "COMPLETE_FIXED_CALIBRATION",
            "primary_router": "DSRE_risk",
            "parents": 360,
            "checkpoints": 720,
            "strata": strata,
            "no_test_outcomes_used": True,
            "calibration_scope": "Independent seed-parent any-error risk; two registered conditions; clean observation model",
        },
    )
    planned_test = [
        p
        for p in read(root / "fresh_seed_manifest.json")["parents"]
        if p["split"] == "test"
    ]
    assert all(
        not (root / "fresh" / p["task"] / f"{p['seed']}-{c}").exists()
        for p in planned_test
        for c in p["conditions"]
    )
    atomic(
        root / "calibration_audit.json",
        {
            "status": "PASS",
            "rules": check,
            "bounds": cp,
            "planned_test_parents_still_untouched": len(planned_test),
            "untouched_test_check": True,
        },
    )
    # This immutable hash is required by every new test parent.
    atomic(
        root / "calibration_seal.json",
        {
            "status": "SEALED_BEFORE_TEST",
            "sha256": sha(root / "calibration_decision.json"),
            "records_sha256": sha(root / "calibration_records.json"),
            "audit_sha256": sha(root / "calibration_audit.json"),
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {
                "status": "CALIBRATION_SEALED",
                "parents": 360,
                "enabled_primary_strata": {
                    k: v["assigned_parents"]
                    for k, v in strata.items()
                    if k.startswith("DSRE_risk|") and v["enabled"]
                },
            }
        ),
        flush=True,
    )


def analyze(root):
    verify_freeze(root)
    if (root / "completion_manifest.json").exists():
        raise ValueError("Sealed evidence")
    all_, rows, missing = qualified(root)
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    calibration = (
        read(root / "calibration_decision.json")["strata"]
        if (root / "calibration_seal.json").exists()
        else {}
    )
    test = [r for r in rows if r["split"] == "test"]
    from dsre_operational_audit import (
        audit_observation_values,
        audit_physics,
        audit_rules,
        audit_selected,
    )

    raw_audit = audit_physics(root, all_)
    test_records = records_for(test, router, frozen, calibration)
    rules_audit = audit_rules(router, test, test_records)
    selected_audit = audit_selected(root, test, calibration)
    result = {
        "primary_population": "NEW_DISJOINT_TEST_ONLY",
        "complete_parents": len(test) // 2,
        "planned_parents": 160,
        "checkpoints": len(test),
        "calibration_parents": sum(r["split"] == "calibration" for r in rows) // 2,
        "tables": summarize(test_records),
        "paired_intervals": paired(test_records),
        "scope": "Defer/stop counts as zero completion; all methods use identical global family risk gate; parent-action risk scope only. Outcome lookup is paired deterministic estimation; selected primary executions counted separately.",
    }
    atomic(root / "test_records.json", test_records)
    atomic(root / "operational_results.json", result)
    atomic(
        root / "missingness.json",
        {
            "planned_parents": 520,
            "complete_parents": len(rows) // 2,
            "qualified_cells": len(all_),
            "missing_or_partial_parents": missing,
            "qualified_secondary_cells": len(all_) - len(rows),
        },
    )
    atomic(
        root / "independent_audit.json",
        {
            "status": "PASS",
            "raw_physics": raw_audit,
            "rules": rules_audit,
            "selected_execution": selected_audit,
            "scope": "Separate same-session raw-predicate/action/rule/CP calculations, not external human replication",
        },
    )
    # Reanalysis of previously inspected confirmation inputs is explicitly not
    # independent calibration; it supplies the larger offline corruption cohort.
    prior = Path("results/dsre-followup/20261113T205403Z")
    _, historical, _ = collect(prior)
    historical_records = records_for(historical, router, frozen, calibration)
    atomic(
        root / "historical_operational_results.json",
        {
            "population": "INSPECTED_FOLLOWUP_EXPLORATORY_REANALYSIS",
            "tables": summarize(historical_records),
            "not_independent_calibration": True,
        },
    )
    atomic(root / "historical_operational_records.json", historical_records)
    corrupt = []
    for scenario in SCENARIOS:
        for row in historical:
            with gzip.open(row["source"], "rt") as stream:
                raw = json.load(stream)
            packet, metadata = observation_packet(raw, row["task"], scenario, frozen)
            audit_observation_values(packet, metadata, scenario)
            # Obtain the clean metadata too; scalar/byte measurements are input
            # serialization costs, not physical sensing costs.
            changed = (
                records_for([row], router, frozen, calibration, scenario)
                if scenario != "clean"
                else records_for([row], router, frozen, calibration)
            )
            clean_packet = packet_from_summary(row, frozen)
            clean = router.route(clean_packet)
            output = router.route(packet)
            for record in changed:
                method = record["method"]
                decision = output[method]
                old = clean[method]
                names = (
                    router.full[row["task"]].table.scope.features
                    if method == "full_signature_strict"
                    else router.settings[row["task"]][2].table.scope.features
                )
                clean_values = (
                    clean_packet.full_values
                    if method == "full_signature_strict"
                    else clean_packet.values
                )
                fact_errors = sum(
                    clean_values[names.index(f["feature"])] is not None
                    and clean_values[names.index(f["feature"])] != f["value"]
                    for f in decision["evidence"]
                )
                record.update({k: v for k, v in metadata.items() if k != "payload"})
                record.update(
                    action_stable=record["proposed_action"] == old["action"],
                    certificate_stable=decision["evidence"] == old["evidence"],
                    contradicted_certificate_facts=fact_errors,
                    false_confidence=int(bool(decision["action"]) and fact_errors > 0),
                    strict_false_acceptance=int(
                        decision["status"] == "STRICT_FINITE_REFERENCE"
                        and record["unacceptable"] > 0
                    ),
                    calibration_status="NO_TRANSFERRED_CERTIFICATION_UNDER_CORRUPTION"
                    if scenario != "clean"
                    else "CLEAN_SCOPE_ONLY",
                )
                corrupt.append(record)
    atomic(root / "robustness_records.json", corrupt)
    by = defaultdict(list)
    for r in corrupt:
        by[f"{r['task']}|{r['method']}|{r['mode']}|{r['scenario']}"].append(r)
    stability = {
        k: {
            "checkpoints": len(rs),
            "parents": len({r["group"] for r in rs}),
            "action_stable": sum(r["action_stable"] for r in rs),
            "certificate_stable": sum(r["certificate_stable"] for r in rs),
            "false_fact_confidence": sum(r["false_confidence"] for r in rs),
            "strict_false_acceptance": sum(r["strict_false_acceptance"] for r in rs),
            "proximity_checkpoints": sum(r["threshold_proximal"] is True for r in rs),
            "mean_payload_json_bytes": sum(r["observed_payload_json_bytes"] for r in rs)
            / len(rs),
            "mean_scalar_input_fields": sum(r["scalar_input_fields"] for r in rs)
            / len(rs),
        }
        for k, rs in by.items()
    }
    atomic(
        root / "observation_robustness.json",
        {
            "population": "INSPECTED_333_PARENT_FOLLOWUP_OFFLINE_ONLY",
            "scenarios": SCENARIOS,
            "tables": summarize(corrupt),
            "stability": stability,
            "independent_observation_payload_checks": len(SCENARIOS) * len(historical),
            "no_physical_sensor_or_calibration_transfer_claim": True,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "new_test_parents": len(test) // 2,
                "robustness_prediction_views": len(corrupt),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("calibrate", "analyze"), required=True)
    args = parser.parse_args()
    calibration_stage(args.root) if args.stage == "calibrate" else analyze(args.root)
