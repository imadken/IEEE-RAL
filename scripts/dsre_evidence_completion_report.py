"""Canonical grouped denominators and fixed-study completion report."""

import json
import time
from collections import Counter
from pathlib import Path

from dsre_evidence_lossless import read
from dsre_evidence_statistical_audit import cp

OLD = Path("results/dsre-evidence-aware/20261117-prospective")
ROOT = Path("results/dsre-evidence-aware/20261118-source-eligibility")
TASKS = ("PointMaze_UMaze-v3", "PickCube-v1", "PegInsertionSide-v1")
NO_CHECKPOINT = "NO_DECISION_CHECKPOINT_SOURCE_PLANNER_FAILURE"


def save(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main():
    registration = read(ROOT / "registration.json")
    groups = {}
    performance = {}
    for task in TASKS:
        source = ROOT if task == TASKS[2] else OLD
        out = source / "prospective" / task
        guard = (
            read(out / "SOURCE_GUARD_FAILURE.json")
            if task == TASKS[2] and (out / "SOURCE_GUARD_FAILURE.json").exists()
            else None
        )
        rows = {
            phase: {
                r["spec"]["index"]: r
                for r in [read(p) for p in (out / phase).glob("*.json")]
            }
            for phase in ("discovery", "calibration", "test")
        }
        screens = {
            r["spec"]["index"]: r
            for r in [read(p) for p in (out / "screens").glob("*.json")]
        }
        grouped = {}
        for phase, records in rows.items():
            target = len(registration["cohorts"][task][phase])
            counts = Counter()
            known_source_eligible = 0
            for index in range(target):
                row = records.get(index)
                screen = screens.get(index) if phase == "calibration" else None
                if row and row["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                    counts["eligible_checkpoint_with_qualified_action_outcome"] += 1
                    known_source_eligible += 1
                elif (row and row["status"] == "ALREADY_SOLVED_PREFIX") or (
                    screen and screen["status"] == "ALREADY_SOLVED_PREFIX"
                ):
                    counts["NO_DECISION_CHECKPOINT_PREFIX_COMPLETED"] += 1
                elif (row and row["status"] == NO_CHECKPOINT) or (
                    screen and screen["status"] == NO_CHECKPOINT
                ):
                    counts[NO_CHECKPOINT] += 1
                elif (
                    guard
                    and guard["spec"]["phase"] == phase
                    and guard["spec"]["index"] == index
                ):
                    counts["failed_qualification_hard_guard"] += 1
                else:
                    counts["pending_action_or_unattempted_parent"] += 1
                    if screen and screen["status"] == "CHECKPOINT_ONLY":
                        known_source_eligible += 1
            assert sum(counts.values()) == target
            no_decision = (
                counts[NO_CHECKPOINT]
                + counts["NO_DECISION_CHECKPOINT_PREFIX_COMPLETED"]
            )
            unknown_source = target - known_source_eligible - no_decision
            lower = cp(known_source_eligible, target, 0.025)[0]
            upper = cp(known_source_eligible + unknown_source, target, 0.025)[1]
            grouped[phase] = {
                "original_registered_parents": target,
                "mutually_exclusive_parent_categories": dict(counts),
                "observed_eligible_source_checkpoints": known_source_eligible,
                "known_no_decision_parents": no_decision,
                "source_eligibility_unknown_or_unqualified": unknown_source,
                "eligible_rate_identification_range": [
                    known_source_eligible / target,
                    (known_source_eligible + unknown_source) / target,
                ],
                "eligible_rate_pointwise95_CP_envelope": [lower, upper],
                "uncertainty_scope": "Per fixed raw cohort under iid seed sampling; conservative envelope over unknown source eligibility, no imputation and no simultaneous across-task/phase claim. Not an intervention-risk guarantee.",
            }
        groups[task] = grouped
        test = {r["parent_id"]: r for r in rows["test"].values()}
        pairs = {p.stem: read(p) for p in (out / "evaluator").glob("*.json")}
        qualified = {
            p: r
            for p, r in test.items()
            if r["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT")
            and p in pairs
            and pairs[p]["yc"] is not None
            and pairs[p]["yr"] is not None
        }
        known_prefix_successes = sum(
            r["status"] == "ALREADY_SOLVED_PREFIX" and r.get("y") is True
            for r in test.values()
        )
        selected_successes = sum(r["y"] for r in qualified.values())
        n = len(qualified)
        known = n + known_prefix_successes
        results = {
            "raw_registered_test_parents": 256,
            "eligible_decisions_with_oracle": n,
            "prefix_successes_without_action": known_prefix_successes,
            "raw_population_completion_sensitivity": [
                (selected_successes + known_prefix_successes) / 256,
                (selected_successes + known_prefix_successes + 256 - known) / 256,
            ],
            "raw_population_harm_or_regret": "Not assigned to no-decision parents. Intervention harm/gain are conditional on eligibility; no action outcome is invented.",
            "policies": {},
            "four_cells_among_eligible_only": dict(
                Counter(
                    f"{int(pairs[p]['yc'])}{int(pairs[p]['yr'])}" for p in qualified
                )
            ),
        }
        evaluation = out / "evaluations/logged.json"
        if evaluation.exists():
            scored = read(evaluation)
            decisions = {r["parent_id"]: r for r in scored["decisions"]}
            for method in scored["policies"]:
                totals = Counter()
                for parent, row in qualified.items():
                    c, r = int(pairs[parent]["yc"]), int(pairs[parent]["yr"])
                    recover = decisions[parent]["actions"][method] == "r"
                    y = r if recover else c
                    totals.update(
                        recover=int(recover),
                        success=y,
                        gain=y - c,
                        harm=int(recover and c and not r),
                        rescues=int(recover and not c and r),
                        futile=int(recover and not c and not r),
                    )
                lo, hi = cp(totals["harm"], totals["recover"], 0.025)
                results["policies"][method] = {
                    **dict(totals),
                    "eligible_n": n,
                    "gain_per_eligible_parent": totals["gain"] / n,
                    "harm_per_selected_R_CP95": [lo, hi],
                    "scope": "Frozen matched deterministic simulator macro outcomes; conditional on eligible checkpoints. Zero observed harm is not zero risk.",
                }
            results["calibration_support"] = {
                leaf: {
                    "c_r_pair": record["ledger"]["counts_c_r_pair"],
                    "per_tail": record["ledger"]["per_tail"],
                    "harm_upper": record["bounds"]["harm_upper"],
                    "gain_lower": record["bounds"]["gain_lower"],
                    "gain_upper": record["bounds"]["gain_upper"],
                    "diagnosis": record["diagnosis"]["status"],
                }
                for leaf, record in read(out / "models/logged.json")["leaves"].items()
            }
        else:
            results["status"] = (
                "UNMEASURED; no fitted calibration or held-out recovery result"
            )
        performance[task] = results
    receipts = [
        p
        for p in (ROOT / "physics").glob("*/*/*/*.execution.json")
        if not p.is_symlink() and p.resolve().is_relative_to(ROOT.resolve())
    ]
    debit = read(ROOT / "resource_amendment_registration.json")[
        "previous_physics_debit_seconds"
    ]
    newwall = sum(read(p)["wall_seconds"] for p in receipts)
    guard = read(ROOT / "independent_followup_audit.json")[
        "source_guard_independent_review"
    ]
    new_screen_receipts = [
        p for p in receipts if p.name == "acquisition_screen.execution.json"
    ]
    total_screens = 260 + len(new_screen_receipts)
    resource = {
        "cumulative_worker_wall_seconds": debit + newwall,
        "new_worker_wall_seconds": newwall,
        "cumulative_worker_hours": (debit + newwall) / 3600,
        "ceiling_worker_hours": 28,
        "remaining_ceiling_worker_hours": 28 - (debit + newwall) / 3600,
        "audit_buffer_worker_hours": 2,
        "new_physics_invocations": len(receipts),
        "prior_physics_invocations": 6964,
        "insertion_source_screen_attempts_total": total_screens,
        "unattempted_calibration_prefix_screens": 1024 - total_screens,
        "unattempted_test_prefix_screens": 256,
        "raw_calibration_parent_slots_without_an_action_outcome": 1024,
        "known_source_ineligible_calibration_parents_never_assigned_an_outcome": 1,
        "remaining_eligible_action_continuation_upper_bound": 1535,
        "current_stop": "Source qualification guard, not resource exhaustion",
        "source_requalification_cost": "Unmeasured; needs ruling on distinct post-control prefix failure",
        "physics_forecast_excluding_screening_G4_requalification_hours": 1535
        * 20.7232705993319
        / 3600,
        "new_dependencies": 0,
        "neural_training_runs": 0,
        "paid_experimental_APIs": 0,
    }
    stages = {
        "G1": "Original zero-control event independently qualified twice; uniform insertion source qualification BLOCKED by distinct second-move prefix failure after33 controls.",
        "G2": "PASS:4224 original IDs/cohorts unchanged; eligibility/resource/code/storage amendments sealed before any insertion calibration/test outcome.",
        "G3": "PARTIAL: navigation and PickCube fully attempted with explicit eligible denominators; insertion128 discovery,363 usable screens,1 approved no-decision source failure,1 hard source guard;0 calibration action outcomes and0 test decisions.",
        "G4": "PARTIAL: historical/PickCube comparisons complete and tied at primary512; navigation508/512 candidate shortfall retained; insertion not executed due source guard, not asserted statistically impossible.",
        "G5": "Independent three-domain record audits, grouped source denominators, support, missingness, baseline equalities, counterexamples and resource ledger delivered; final compact verification is recorded separately in its receipt.",
        "G6": "NOT PASSED: no additional qualified non-grasp recovery; original scientific advance not established; manuscripts untouched.",
    }
    result = {
        "epoch": time.time(),
        "scientific_decision": "INCOMPLETE_SOURCE_EVIDENCE",
        "original_science_gate": "SCIENTIFIC_ADVANCE_NOT_ESTABLISHED",
        "G1_G6": stages,
        "grouped_denominators": groups,
        "conditional_performance": performance,
        "resources": resource,
        "new_guard_independent_review": guard,
        "next_action": "Supervisor source ruling on original calibration screen364, seed85558356, offset-.006: native second move(grasp) failed after33 prefix controls. Retain the guard; do not apply the zero-control exclusion, replace the seed, invent a checkpoint/terminal label or resume under the current registered rule. Calibration1024 and test256 remain unexecuted.",
    }
    save(ROOT / "completion_scientific_report.json", result)
    lines = [
        "\n## 2026-11-18 executed source continuation and final grouped assessment",
        "",
        "**Scientific disposition: INCOMPLETE_SOURCE_EVIDENCE. Original gate: SCIENTIFIC_ADVANCE_NOT_ESTABLISHED.**",
        "",
    ]
    lines += [f"- **{k}:** {v}" for k, v in stages.items()]
    lines += [
        "",
        "The pre-physics durable commit is `a13aea090fcfe8b4ca0c9380a32f392b055b56ff`; the independently justified source-eligibility amendment is committed as `e566859`. Both were made in the prescribed order, with no push or manuscript edit.",
        "",
        "The two fresh replays of seed180937078 exactly reproduced the first screw-planner failure at worker line443 before any control, with matching full initial physical/controller/RNG state and27 verified source/native fingerprints. The eligibility and28-hour resource amendments were sealed before any insertion calibration or test intervention. New raw traces use independently verified lossless storage; original gzip bytes can be reconstructed exactly, and historical gzip files/seals remain unchanged.",
        "",
        "**New independent counterexample:** screen364, seed85558356, offset−0.006, fails at the second `move(grasp)` (worker line444) after33 prefix controls and34 recorded states. Independent review verified finite recorded physics and elapsed steps0–33, unchanged source, no executable decision checkpoint and no intervention outcome. This is outside the registered zero-control rule. The hard guard remains; it was not automatically excluded or turned into a zero outcome.",
        "",
        "| Task / phase | Original parents | Qualified action outcomes | Source-planner no-decision | Prefix completed without decision | Hard qualification guard | Pending action/unattempted |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for task, phases in groups.items():
        for phase, g in phases.items():
            c = g["mutually_exclusive_parent_categories"]
            lines.append(
                f"| {task} / {phase} | {g['original_registered_parents']} | {c.get('eligible_checkpoint_with_qualified_action_outcome', 0)} | {c.get(NO_CHECKPOINT, 0)} | {c.get('NO_DECISION_CHECKPOINT_PREFIX_COMPLETED', 0)} | {c.get('failed_qualification_hard_guard', 0)} | {c.get('pending_action_or_unattempted_parent', 0)} |"
            )
    lines += [
        "",
        "Insertion has365 attempted calibration source screens:363 usable checkpoints,1 independently qualified zero-control failure and1 distinct guarded failure. Its363 usable contexts have no assigned-action observation. The1022 pending calibration parents comprise363 with usable prefixes but unexecuted actions plus659 whose prefixes were never attempted. No parent was replaced. Test256 remains untouched. Source failures and source-prefix successes are not DSRE abstentions and do not enter intervention-at-risk or action-regret counts.",
        "",
        "| Task | Eligible test decisions | Raw test parents | DSRE R | Required rescues | Harm | Futile R | Eligible completion | Raw completion / sensitivity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for task, p in performance.items():
        m = p["policies"].get("DSRE")
        if m:
            lines.append(
                f"| {task} | {p['eligible_decisions_with_oracle']} |256|{m['recover']}|{m['rescues']}|{m['harm']}|{m['futile']}|{m['success']}/{m['eligible_n']}|{p['raw_population_completion_sensitivity']}|"
            )
        else:
            lines.append(
                f"| {task} |0|256|unmeasured|unmeasured|unmeasured|unmeasured|unmeasured|[0,1]|"
            )
    lines += [
        "",
        "Navigation excludes its one prefix-success test parent from decision/at-risk/regret counts: conditional eligible completion is183/255, with one separately observed prefix success making184/256 raw completion. PickCube completes227/256, rescues84 through111 qualified recoveries, observes0 harmful recoveries and27 futile recoveries. Its observed harm CP95 interval is[0,0.032687], rather than a zero-risk guarantee. All matched gated rules/CART/direct-bound adaptations retain identical decisions. Always-continue/recover complete143/197 of256 on PickCube; always-recover harms32. On navigation always-recover harms14 with no required rescues.",
        "",
        "Exact per-leaf C/R calibration support and bounds, per-task/per-phase eligibility-rate CP envelopes over all unknown completions, and canonical matched policy metrics are in `completion_scientific_report.json`. Eligibility intervals are pointwise by fixed raw cohort, not simultaneous across tasks/phases; risk/gain guarantees remain conditional on eligibility and the fixed whole leaf. No harm or action regret is assigned to no-decision parents. Raw-population completion uses conservative best/worst unknown-outcome bounds.",
        "",
        f"Measured physics is {resource['cumulative_worker_hours']:.6f} summed worker-hours ({len(receipts)} new invocations), below the 28h ceiling; {resource['remaining_ceiling_worker_hours']:.6f}h remains before reserving 2h for audits. The stop is scientific/source qualification. All 1024 calibration raw-parent slots lack action observations, but the known ineligible parent will never receive an imputed outcome. Remaining physical action continuations have upper bound 1023 calibration +256 selected test +256 evaluator =1535, subject to the unresolved source guard and further eligibility. Remaining unattempted source screens:659 calibration +256 test =915. At the prior measured branch mean, this upper-bound future workload forecasts {resource['physics_forecast_excluding_screening_G4_requalification_hours']:.3f}h, excluding screening, G4 and source requalification. No new dependencies, paid experimental APIs or neural training runs.",
        "",
        "Fresh independent full audits of navigation and PickCube were repeated. The insertion audit checks all preserved discovery/source traces, exact new gzip reconstruction, the qualified exclusion and the distinct post-control blocker. A passing record audit confirms the preserved blocker; it does not qualify the blocked insertion cohort.",
        "",
        result["next_action"],
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.",
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1",
        "uv run --no-sync pytest -q tests",
        "T=$(mktemp -d /tmp/dsre-completion-audit.XXXXXX)",
        'uv run --no-sync python scripts/dsre_evidence_eligible_audit.py results/dsre-evidence-aware/20261118-source-eligibility --output "$T/source_audit.json" --numerical-output "$T/numerical_audit.json"',
        "# The current guarded runner must not launch further affected-domain physics.",
        "```",
    ]
    with Path("docs/DSRE_EVIDENCE_AWARE_PROSPECTIVE_RESULTS.md").open("a") as handle:
        handle.write("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "scientific_decision": result["scientific_decision"],
                "resources": resource,
                "G1_G6": stages,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
