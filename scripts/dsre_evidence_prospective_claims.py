"""Bind scientific claims and explicit limitations to sealed current evidence."""

import json

from dsre_evidence_prospective import ROOT, TASKS, read

from dual_rec.evidence_aware.views import save, sha


def main():
    summary = read(ROOT / "prospective_summary.json")
    claims = []
    census = {}
    claims.append(
        {
            "claim": "Original cohort IDs, conditions and original manifests preserved; no overlap with checked historical identities",
            "status": "VERIFIED",
            "evidence": str(ROOT / "independent_manifest_audit.json"),
            "sha256": sha(ROOT / "independent_manifest_audit.json"),
        }
    )
    claims.append(
        {
            "claim": "Five supported insertion features; aperture remains UNKNOWN; fresh independent source-v2 qualification",
            "status": "TECHNICAL_PILOT_ONLY",
            "evidence": str(ROOT / "G1_source_v2_qualification.json"),
            "sha256": sha(ROOT / "G1_source_v2_qualification.json"),
        }
    )
    extended = read(ROOT / "independent_extended_audit.json")
    assert extended["passed"] and not extended["production_inference_imported"]
    claims.append(
        {
            "claim": "Every stored extremum/optimizer and constructive world pair; frozen acquisition membership, within-leaf hash prefixes and pre-outcome timing",
            "status": "INDEPENDENTLY_VERIFIED",
            "evidence": str(ROOT / "independent_extended_audit.json"),
            "sha256": sha(ROOT / "independent_extended_audit.json"),
            "counts": extended["counts"],
            "limitation": extended["limitation"],
        }
    )
    for task in TASKS:
        out = ROOT / "prospective" / task
        d = summary["domains"][task]
        records = [read(p) for p in (out / "test").glob("*.json")]
        census[task] = {
            "registered_test": 256,
            "test_parents_attempted": len(records),
            "actual_completed_selected_future_macros": sum(
                r["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT") for r in records
            ),
            "observed_absorbing_prefixes_without_recovery_decision": sum(
                bool(r.get("precheckpoint_absorption")) for r in records
            ),
            "observed_test_endpoint_parents": sum(
                r.get("y") is not None for r in records
            ),
            "clarification": "Legacy evaluation field n_selected_executions counts observed endpoint parents; this census distinguishes actual selected futures and preterminal source success. No policy training record is created from test endpoints.",
        }
        modelpath = out / "models/logged.json"
        if modelpath.exists():
            model = read(modelpath)
            assert model["counts"]["calibration_pairs"] == 0
            assert not any(
                "/paired_refinement/" in p or "/evaluator/" in p
                for p in model["successful_data_reads"]
            )
            claims.append(
                {
                    "claim": f"{task}: primary learner sees assigned-arm discovery/calibration only",
                    "status": "SOURCE_ACCESS_VERIFIED",
                    "evidence": str(modelpath),
                    "sha256": sha(modelpath),
                    "data_counts": model["counts"],
                    "confidence": "Per-task fixed leaf .025 logged + .025 reserved paired; no simultaneous cross-strategy or cross-budget guarantee.",
                }
            )
        if d["scientific_result"]:
            claims.append(
                {
                    "claim": f"{task}: useful recovery and policy completion on independent parent test",
                    "status": "ACTUAL_RESULTS_WITH_ATTRITION_DISCLOSED",
                    "result": d["scientific_result"],
                    "baseline_equal_actions": d["baseline_equivalence"],
                    "scope": "Deterministic qualified simulator model only; regional guarantees under declared assumptions, no individual or hardware safety claim.",
                }
            )
        else:
            claims.append(
                {
                    "claim": f"{task}: prospective useful-recovery evidence",
                    "status": "NOT_ESTABLISHED",
                    "source_guard": d["source_guard"],
                    "outstanding_valid_checkpoint_targets": d[
                        "outstanding_parent_counts"
                    ],
                    "unattempted_original_parents": d["unattempted_parent_counts"],
                    "note": "No missing endpoint is imputed and no failed parent replaced.",
                }
            )
    frontier = read(ROOT / "prospective_acquisition_frontiers.json")["curves"]
    acquisition = {}
    for task in TASKS:
        rows = [
            r
            for r in frontier
            if r["task"] == task and r["requested_additional_units"] == 512
        ]
        if not rows:
            acquisition[task] = {"status": "NO_INDEPENDENT_PROSPECTIVE_TEST_RESULT"}
            continue
        witness = next(r for r in rows if r["strategy"] == "witness")
        matched = all(r["actual_additional_units"] == 512 for r in rows)
        others = [r for r in rows if r["strategy"] != "witness"]
        better = witness["qualified_coverage"] > max(
            r["qualified_coverage"] for r in others
        ) and witness["whole_policy_gain"] > max(r["whole_policy_gain"] for r in others)
        acquisition[task] = {
            "status": "PRIMARY512_COST_SHORTFALL_NO_SUPERIORITY_CLAIM"
            if not matched
            else "DESCRIPTIVE_NUMERICAL_DIFFERENCE_ONLY"
            if better
            else "NO_UNIQUE_WITNESS_ADVANTAGE_OBSERVED",
            "primary_rows": rows,
            "formal_between_strategy_significance_claim": False,
        }
    save(ROOT / "acquisition_claim_audit.json", acquisition)
    claims += [
        {
            "claim": "DSRE action superiority over exact ordinary rules/direct matched bounds",
            "status": "NOT_CLAIMED",
            "reason": "Identical gate and support can implement exactly the same action map; report observed equalities.",
        },
        {
            "claim": "Witness acquisition improves useful recovery at equal budget",
            "status": "NO_GENERAL_ADVANTAGE_CLAIM",
            "per_domain_results": acquisition,
            "reason": "Historical witness/all-log/all-pair curves tie at512. Prospective requested512 cost shortfalls and all strategy results are disclosed; no superiority from unequal costs or test-selected budgets.",
        },
        {
            "claim": "New partial-identification mathematics or original Kallus/Li/DISCRET reproductions",
            "status": "NOT_CLAIMED",
            "reason": "Established bounds and explicitly named finite-cell adaptations; nearest-work matrix source-bound.",
        },
        {
            "claim": "Science lock and manuscript readiness",
            "status": summary["G1_G6"]["G6"],
            "scientific_decision": summary["scientific_decision"],
            "criteria": summary["G1_G6"],
        },
    ]
    save(
        ROOT / "scientific_claim_ledger.json",
        {
            "claims": claims,
            "provenance": "Actual frozen outputs and independent audits; no acceptance or hardware claim.",
        },
    )
    save(ROOT / "policy_execution_census.json", census)
    print(json.dumps({"claims": len(claims), "census": census}), flush=True)


if __name__ == "__main__":
    main()
