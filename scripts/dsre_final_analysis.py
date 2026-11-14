"""Frozen held-out estimands and identical-grid observation shift sensitivity."""

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_final_verify import load_trace, verify_execution, verify_sources
from dsre_followup_batch import atomic, read, sha
from dsre_operational_analysis import paired, qualified, records_for, summarize
from dsre_operational_audit import (
    audit_calibration,
    audit_observation_values,
    audit_physics,
    audit_rules,
)
from dsre_operational_observations import (
    SCENARIOS,
    observation_packet,
    packet_from_summary,
)

from dual_rec.dsre.operational import METHODS, OperationalRouter, gated_action


def audit_rows(root, rows):
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    calibration = read(root / "calibration_decision.json")["strata"]
    predictions = records_for(rows, router, frozen, calibration)
    raw = audit_physics(root, rows)
    rules = audit_rules(router, rows, predictions)
    executed = deferred = prefix = future = 0
    for row in rows:
        directory = (
            root / "selected" / row["task"] / f"{row['seed']}-{row['condition']}"
        )
        decision = read(directory / "decision.json")
        result = read(directory / "execution.json")
        packet = packet_from_summary(row, frozen)
        expected = router.route(packet)
        assert decision["predecision_input"] == packet.model_dump(mode="json")
        assert decision["calibration_sha256"] == sha(root / "calibration_decision.json")
        assert set(decision["all_method_actions"]) == set(METHODS)
        for method, value in expected.items():
            assert decision["all_method_actions"][method] == {
                "proposal": value["action"],
                "gated": gated_action(
                    method, row["task"], value["action"], calibration
                ),
            }
        action = gated_action(
            "DSRE_risk", row["task"], expected["DSRE_risk"]["action"], calibration
        )
        assert decision["action"] == action
        if action is None:
            assert result["status"] == "DEFER_STOP" and result["new_continuations"] == 0
            deferred += 1
            continue
        assert sha(Path(result["source"])) == result["source_sha256"]
        with gzip.open(result["source"], "rt") as stream:
            actual = json.load(stream)
        proof = verify_execution(load_trace(row), actual, row["task"], action)
        prefix += proof["prefix_states"]
        future += proof["future_states"]
        executed += 1
    return {
        "status": "PASS",
        "raw": raw,
        "rules": rules,
        "selected_executions": executed,
        "deferred_checkpoints": deferred,
        "selected_prefix_states": prefix,
        "selected_future_states": future,
        "selected_disagreements": 0,
        "all_method_preexecution_decisions_checked": len(rows) * len(METHODS),
    }


def analyze(root):
    verify_sources(root)
    assert not (root / "completion_manifest.json").exists()
    all_rows, rows, missing = qualified(root)
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    calibration = read(root / "calibration_decision.json")
    predictions = records_for(rows, router, frozen, calibration["strata"])
    proof = audit_rows(root, rows)
    if len(all_rows) > len(rows):
        proof["secondary_raw"] = audit_physics(
            root, [r for r in all_rows if r["group"] not in {q["group"] for q in rows}]
        )
    cp = audit_calibration(
        read(root / "calibration_records.json"), calibration["strata"]
    )
    assert (
        calibration["strata"]
        == read(
            Path(read(Path("config/dsre_final_sprint.json"))["prior_root"])
            / "calibration_decision.json"
        )["strata"]
    )
    result = {
        "primary_population": "POSTMORTEM_EXCLUSION_UNTOUCHED_159_ONLY",
        "complete_parents": len(rows) // 2,
        "planned_parents": len(read(root / "fresh_seed_manifest.json")["parents"]),
        "original_planned_test": 160,
        "checkpoints": len(rows),
        "calibration_parents": 360,
        "tables": summarize(predictions),
        "paired_intervals": paired(predictions),
        "scope": "Frozen global family gate and explicit STOP; 8000180 excluded, no replacement. Selected repeats share original seed parents.",
    }
    atomic(root / "test_records.json", predictions)
    atomic(root / "operational_results.json", result)
    atomic(
        root / "missingness.json",
        {
            "planned_parents": result["planned_parents"],
            "complete_parents": len(rows) // 2,
            "qualified_cells": len(all_rows),
            "qualified_secondary_cells": len(all_rows) - len(rows),
            "missing_or_partial_parents": missing,
            "prior_excluded_parent": "PickCube-v1/8000180",
        },
    )
    atomic(
        root / "independent_audit.json",
        {
            "status": "PASS",
            "heldout": proof,
            "calibration": cp,
            "same_session_independent_implementations": True,
        },
    )
    assignment = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        for method in METHODS:
            for action in ("continue", "recover"):
                rs = [
                    r
                    for r in predictions
                    if r["task"] == task
                    and r["method"] == method
                    and r["mode"] == "proposal"
                    and r["action"] == action
                ]
                assignment[f"{method}|{task}|{action}"] = {
                    "assigned_parents": len({r["group"] for r in rs}),
                    "error_parents": len({r["group"] for r in rs if r["unacceptable"]}),
                    "checkpoints": len(rs),
                    "no_gate_update": True,
                }
    atomic(root / "test_assignment_errors.json", assignment)
    print(
        json.dumps(
            {
                "status": "PASS",
                "complete_parents": len(rows) // 2,
                "checkpoints": len(rows),
                "selected": proof["selected_executions"],
            }
        ),
        flush=True,
    )


def corrupt_records(root, rows):
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    calibration = read(root / "calibration_decision.json")["strata"]
    records = []
    for row in rows:
        raw = load_trace(row)
        clean_packet = packet_from_summary(row, frozen)
        clean = router.route(clean_packet)
        for scenario in SCENARIOS:
            packet, meta = observation_packet(raw, row["task"], scenario, frozen)
            audit_observation_values(packet, meta, scenario)
            # Score the identical fixed corrupted packet against physical labels.
            adapted = row | {
                "features": list(packet.full_values[:6]),
                "optional_features": list(packet.full_values[6:]),
            }
            changed = records_for([adapted], router, frozen, calibration)
            output = router.route(packet)
            for r in changed:
                method = r["method"]
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
                errors = sum(
                    clean_values[names.index(f["feature"])] is not None
                    and clean_values[names.index(f["feature"])] != f["value"]
                    for f in output[method]["evidence"]
                )
                r.update(
                    scenario=scenario,
                    **{k: v for k, v in meta.items() if k != "payload"},
                    action_stable=r["proposed_action"] == clean[method]["action"],
                    certificate_stable=output[method]["evidence"]
                    == clean[method]["evidence"],
                    false_confidence=int(bool(output[method]["action"]) and errors > 0),
                    contradicted_certificate_facts=errors,
                )
                records.append(r)
    return records


def sensitivity_intervals(records):
    """Resample parents; within each draw average noise repetitions per cell."""
    by = defaultdict(list)
    for r in records:
        family = (
            r["scenario"].rsplit("_r", 1)[0]
            if r["scenario"].startswith("noise")
            else r["scenario"]
        )
        by[(r["task"], r["method"], r["mode"], family)].append(r)
    results = {}
    for (task, method, mode, scenario), rs in by.items():
        for population in ("all", "threshold_proximal"):
            parents = sorted({r["group"] for r in rs})
            index = {p: i for i, p in enumerate(parents)}
            fields = (
                "successful",
                "unacceptable",
                "deferred",
                "action_unstable",
                "certificate_unstable",
                "false_confidence",
                "newly_unacceptable",
            )
            frame = np.zeros((len(parents), len(fields) + 1))
            clean = {r["id"]: r for r in by[(task, method, mode, "clean")]}
            repetitions = 3 if scenario.startswith("noise") else 1
            for r in rs:
                if population == "threshold_proximal" and not r["threshold_proximal"]:
                    continue
                values = [
                    r["successful"],
                    r["unacceptable"],
                    r["deferred"],
                    int(r["action"] != clean[r["id"]]["action"]),
                    int(not r["certificate_stable"]),
                    r["false_confidence"],
                    int(r["unacceptable"] and not clean[r["id"]]["unacceptable"]),
                ]
                frame[index[r["group"]], : len(fields)] += (
                    np.asarray(values) / repetitions
                )
                frame[index[r["group"]], -1] += 1 / repetitions
            entry = {
                "parents": len(parents),
                "effective_checkpoints": float(frame[:, -1].sum()),
                "noise_replicates_averaged_within_parent": repetitions,
                "population": population,
            }
            if frame[:, -1].sum():
                rng = np.random.default_rng(2026111401 + int(task == "PushCube-v1"))
                samples = frame[
                    rng.integers(len(parents), size=(4000, len(parents)))
                ].sum(axis=1)
                samples = samples[samples[:, -1] > 0]
                for i, field in enumerate(fields):
                    entry[field] = {
                        "value": float(frame[:, i].sum() / frame[:, -1].sum()),
                        "parent_percentile95": np.percentile(
                            samples[:, i] / samples[:, -1], [2.5, 97.5]
                        ).tolist(),
                    }
            else:
                entry["status"] = "NOT_ESTIMABLE_EMPTY_SUBGROUP"
            results[f"{task}|{method}|{mode}|{scenario}|{population}"] = entry
    return results


def robustness(root):
    verify_sources(root)
    old = Path(read(Path("config/dsre_final_sprint.json"))["prior_root"])
    historical = read(old / "robustness_records.json")
    for population, records in [
        ("INSPECTED_HISTORICAL_333", historical),
        (
            "NEW_159_SECONDARY_SHIFT_SENSITIVITY",
            corrupt_records(root, qualified(root)[1]),
        ),
    ]:
        name = "historical" if population.startswith("INSPECTED") else "heldout"
        if name == "heldout":
            atomic(root / "heldout_corruption_records.json", records)
        atomic(
            root / f"{name}_robustness.json",
            {
                "population": population,
                "scenarios": SCENARIOS,
                "tables": summarize(records),
                "parent_intervals": sensitivity_intervals(records),
                "clean_calibration_does_not_transfer": True,
                "source": str(old / "robustness_records.json")
                if name == "historical"
                else str(root / "heldout_corruption_records.json"),
            },
        )
        print(
            json.dumps(
                {"status": "PASS", "population": population, "views": len(records)}
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("analyze", "robustness"), required=True)
    args = parser.parse_args()
    analyze(args.root) if args.stage == "analyze" else robustness(args.root)
