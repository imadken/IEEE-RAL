"""Recount actual attempts, unresolved parents, scientific gates and resources."""

import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path

from dsre_evidence_prospective import OLD, ROOT, TASKS, identity, read, specs

from dual_rec.evidence_aware.views import save, sha


def report(root):
    prior = read(OLD / "prospective_ready_manifest.json")
    domains = {}
    resources = {}
    allreceipts = []
    for task in TASKS:
        out = root / "prospective" / task
        phases = {}
        outstanding = {}
        unattempted = {}
        for phase, target in [("discovery", 128), ("calibration", 1024), ("test", 256)]:
            rows = [read(p) for p in (out / phase).glob("*.json")]
            good = sum(
                r["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT")
                and r.get("y") is not None
                for r in rows
            )
            phases[phase] = {
                "registered": target,
                "attempted": len(rows),
                "completed": good,
                "observed_absorbing_prefix": sum(
                    r["status"] == "ALREADY_SOLVED_PREFIX" for r in rows
                ),
                "observed_endpoint_parents": sum(r.get("y") is not None for r in rows),
                "attempt_statuses": dict(Counter(r["status"] for r in rows)),
            }
            outstanding[phase] = target - good
            unattempted[phase] = target - len(rows)
        screens = [read(p) for p in (out / "screens").glob("*.json")]
        pairs = [read(p) for p in (out / "evaluator").glob("*.json")]
        completepairs = sum(
            r.get("yc") is not None and r.get("yr") is not None for r in pairs
        )
        receipts = [
            read(p) for p in (root / "physics" / task).glob("*/*/*.execution.json")
        ]
        allreceipts.extend(receipts)
        future = [r["wall_seconds"] for r in receipts if r["command"][-1] in ("c", "r")]
        screen = [r["wall_seconds"] for r in receipts if r["command"][-1] == "screen"]
        seconds = sum(r["wall_seconds"] for r in receipts)
        future_mean = (
            sum(future) / len(future)
            if future
            else prior["forecast"][task]["complete_branch_mean_wall_seconds"]
        )
        screen_mean = sum(screen) / len(screen) if screen else None
        remaining_futures = sum(unattempted.values()) + (256 - completepairs)
        remaining_screens = max(0, 1024 - len(screens)) + unattempted["test"]
        schedule_path = out / "acquisition_schedule.json"
        remaining_pairs = None
        if schedule_path.exists():
            schedules = read(schedule_path)["schedules"]
            planned_ids = {
                r["parent_id"]
                for budgets in schedules.values()
                for r in budgets["512"]
                if r["kind"] == "pair"
            }
            remaining_pairs = sum(
                not (out / "acquisition_pairs" / f"{pid}.json").exists()
                for pid in planned_ids
            )
        resources[task] = {
            "worker_invocations": len(receipts),
            "requested_macro_invocations": len(future),
            "prefix_only_invocations": len(screen),
            "worker_wall_seconds": seconds,
            "worker_cpu_seconds": sum(r["cpu_seconds"] for r in receipts),
            "mean_future_invocation_wall_seconds": future_mean,
            "mean_prefix_only_invocation_wall_seconds": screen_mean,
            "remaining_registered_future_invocations_excluding_G4": remaining_futures,
            "remaining_future_worker_seconds_forecast_excluding_G4": remaining_futures
            * future_mean,
            "remaining_predecision_screen_requests": remaining_screens,
            "remaining_selected_G4_counterpart_requests": remaining_pairs,
            "G4_counterpart_upper_bound_if_unplanned": 512
            if remaining_pairs is None
            else remaining_pairs,
            "remaining_screen_worker_seconds_forecast": remaining_screens * screen_mean
            if screen_mean is not None
            else None,
            "remaining_G4_worker_seconds_forecast": remaining_pairs * future_mean
            if remaining_pairs is not None
            else None,
            "forecast_limit": "Engineering extrapolation only; qualification blockers require resolution; additional screening and G4 listed separately.",
        }
        evaluation = out / "evaluations/logged.json"
        scored = read(evaluation) if evaluation.exists() else None
        testrecords = [read(p) for p in (out / "test").glob("*.json")]
        testactions = {r["parent_id"]: r["action"] for r in testrecords}
        known_success = sum(r.get("y") is True for r in testrecords)
        known_endpoints = sum(r.get("y") is not None for r in testrecords)
        known_gain = sum(
            (r["yr"] if testactions[r["parent_id"]] == "r" else r["yc"]) - r["yc"]
            for r in pairs
            if r.get("yc") is not None and r.get("yr") is not None
        )
        known_harm = sum(
            testactions[r["parent_id"]] == "r" and r["yc"] and not r["yr"]
            for r in pairs
            if r.get("yc") is not None and r.get("yr") is not None
        )
        unknown_pairs = 256 - completepairs
        guardpaths = list((out / "guard_witnesses").glob("*.json"))
        if (out / "SOURCE_GUARD_FAILURE.json").exists():
            guardpaths.append(out / "SOURCE_GUARD_FAILURE.json")
        activeguards = [
            read(p) for p in guardpaths if read(p)["status"] != "ALREADY_SOLVED_PREFIX"
        ]
        guard = activeguards[0] if activeguards else None
        absorbed_pairs = sum(bool(r.get("precheckpoint_absorption")) for r in pairs)
        domains[task] = {
            "phases": phases,
            "outstanding_parent_counts": outstanding,
            "unattempted_parent_counts": unattempted,
            "calibration_screens": len(screens),
            "screen_statuses": dict(Counter(r["status"] for r in screens)),
            "paired_test_checks": completepairs - absorbed_pairs,
            "observed_absorbing_test_prefix_pairs": absorbed_pairs,
            "oracle_complete_parents": completepairs,
            "actual_selected_future_executions": phases["test"]["completed"],
            "observed_test_endpoint_parents": phases["test"][
                "observed_endpoint_parents"
            ],
            "acquisition_counterparts_completed": len(
                list((out / "acquisition_pairs").glob("*.json"))
            ),
            "source_guard": guard,
            "scientific_result": scored["policies"].get("DSRE") if scored else None,
            "baseline_equivalence": scored.get("equivalence_vs_DSRE")
            if scored
            else None,
            "complete_cohort": all(v == 0 for v in unattempted.values())
            and completepairs == 256
            and guard is None,
            "all_valid_checkpoint_targets_met": all(
                v == 0 for v in outstanding.values()
            ),
            "untouched_test_parents": 256 - phases["test"]["attempted"],
            "missing_terminal_labels_after_assigned_action": sum(
                sum(
                    v
                    for k, v in p["attempt_statuses"].items()
                    if k == "MISSING_TERMINAL_OUTCOME"
                )
                for p in phases.values()
            ),
            "registered_test_identification_sensitivity": {
                "known_selected_successes": known_success,
                "unknown_selected_endpoints": 256 - known_endpoints,
                "completion": [
                    known_success / 256,
                    (known_success + 256 - known_endpoints) / 256,
                ],
                "whole_policy_gain": [
                    (known_gain - unknown_pairs) / 256,
                    (known_gain + unknown_pairs) / 256,
                ],
                "parent_harm": [
                    known_harm / 256,
                    (known_harm + unknown_pairs) / 256,
                ],
                "scope": "Worst/best unknown-parent identification bounds, not statistical confidence intervals; no missing endpoint is imputed.",
            },
            "note": "Outstanding includes unavailable attempted parents, which are never replaced. A source-successful already-solved prefix has no recovery checkpoint; it is not a missing terminal success label.",
        }
    g1 = read(root / "G1_source_v2_qualification.json")
    completed = sum(d["complete_cohort"] for d in domains.values())
    new_non_grasp = any(
        d["complete_cohort"]
        and task != "PickCube-v1"
        and d["scientific_result"]
        and d["scientific_result"]["recover"] > 0
        for task, d in domains.items()
    )
    scientific = (
        "VALID_BUT_UNDISTINGUISHED"
        if completed == len(TASKS)
        and not any(d["source_guard"] for d in domains.values())
        else "INCOMPLETE_SOURCE_EVIDENCE"
    )
    acquisition_frozen = []
    acquisition_exact512 = []
    for task, domain in domains.items():
        schedulepath = root / "prospective" / task / "acquisition_schedule.json"
        if schedulepath.exists():
            acquisition_frozen.append(task)
            schedules = read(schedulepath)["schedules"]
            if domain["complete_cohort"] and all(
                sum(r["cost"] for r in budgets["512"]) == 512
                for budgets in schedules.values()
            ):
                acquisition_exact512.append(task)
    extended = read(root / "independent_extended_audit.json")
    assert extended["passed"]
    for task, domain in domains.items():
        domain["independent_source_failure_witnesses"] = extended["tasks"][task][
            "source_failures"
        ]
    gates = {
        "G1": "PASS" if g1["technical_pass"] else "BLOCKED",
        "G2": "FROZEN; independently audited original cohorts",
        "G3": f"{completed}/3 registered cohorts fully attempted and oracle-covered; valid-checkpoint attrition and unfinished counts explicit",
        "G4": f"{'COMPLETE' if len(acquisition_exact512) == len(TASKS) else 'PARTIAL'}: historical64/128/256/512 curves executed; {len(acquisition_frozen)}/3 prospective schedule sets frozen; full equal512-cost test comparisons for {acquisition_exact512}. All shortfalls and untouched domains retained; no superiority inferred from equality",
        "G5": "Source-bound nearest-work and independent reviewer-style assessment delivered; empirical breadth limits retained",
        "G6": "NOT LOCKED; supervisor gate pending; no manuscript work authorized",
        "non_grasp_qualified_live_recovery_gate_met": new_non_grasp,
        "original_science_gate": "SCIENTIFIC_ADVANCE_NOT_ESTABLISHED",
    }
    totalwall = sum(r["wall_seconds"] for r in allreceipts)
    result = {
        "scientific_decision": scientific,
        "G1_G6": gates,
        "domains": domains,
        "resources_by_task": resources,
        "resources": {
            "measured_new_physics_worker_wall_seconds": totalwall,
            "measured_new_physics_worker_cpu_seconds": sum(
                r["cpu_seconds"] for r in allreceipts
            ),
            "physics_wall_cap_seconds": 64800,
            "physics_worker_wall_remaining_seconds": 64800 - totalwall,
            "audit_reserve_seconds": 7200,
            "elapsed_since_preservation_start_seconds": time.time()
            - read(root / "preservation_start.json")["epoch"],
            "artifact_bytes_before_final_seals_and_compact": sum(
                p.stat().st_size
                for p in root.rglob("*")
                if p.is_file() and not p.is_relative_to(root / "navigation_env")
            ),
            "artifact_cap_bytes": 5 * 1024**3,
            "new_dependencies": 0,
            "paid_APIs": 0,
            "neural_training_runs": 0,
            "discovery_partition_fits": sum(
                (root / "prospective" / task / "discovery_freeze.json").exists()
                for task in TASKS
            ),
            "calibrated_model_files": sum(
                len(list((root / "prospective" / task / "models").glob("*.json")))
                for task in TASKS
            ),
            "offline_CPU_note": "Worker CPU measured; offline verifier/test CPU not separately metered.",
        },
        "original_manifests_unchanged": all(
            sha(OLD / name) == read(root / "registration.json")[key]
            for name, key in [
                ("prospective_manifest.json", "original_manifest_sha256"),
                ("prospective_ready_manifest.json", "ready_manifest_sha256"),
            ]
        ),
        "independent_extended_audit_counts": extended["counts"],
        "primary": "harm<=.10 AND gain>=.05; per-tail .025/(4K); no retuning, seed replacement or alternate task",
        "source_types": "L assigned outcomes only; P only preselected budgeted acquisition; evaluator counterparts isolated; policy test executions excluded from randomized calibration",
        "next_action": "Resolve the recorded source/checkpoint qualification blockers under supervisor review without changing frozen outcomes or replacing parents; resume the exact registered unattempted parent only after a valid source contract is qualified. No held-out tuning or manuscript work.",
    }
    active = [
        (task, d["source_guard"]) for task, d in domains.items() if d["source_guard"]
    ]
    if active:
        detail = "; ".join(
            f"{task}, phase {g['spec']['phase']}, index {g['spec']['index']}, seed {g['spec']['seed']}, status {g['status']}"
            for task, g in active
        )
        result["next_action"] = (
            "Inspect and independently qualify the preserved source failure(s): "
            + detail
            + ". Repair only an interface error if justified; never change the frozen controllers, thresholds or outcomes, or replace parents. Resume original unattempted IDs only after source qualification; otherwise retain the domain qualification failure. Review G6 before any manuscript work."
        )
    elif completed != len(TASKS):
        task = next(t for t, d in domains.items() if not d["complete_cohort"])
        out = root / "prospective" / task
        pending = None
        for stage, phase, folder in (
            ("discovery", "discovery", "discovery"),
            ("screen", "calibration", "screens"),
            ("calibration", "calibration", "calibration"),
            ("test", "test", "test"),
        ):
            for spec in specs(root, task, phase):
                if not (out / folder / f"{identity(spec)}.json").exists():
                    pending = (stage, spec)
                    break
            if pending:
                break
        if pending:
            stage, spec = pending
            result["next_action"] = (
                f"At the sealed resource boundary, next unattempted original operation is {task}, stage {stage}, index {spec['index']}, seed {spec['seed']}. "
                "The cumulative registered cap is not reset by a new session. Obtain a supervisor-approved resource amendment if the cap prevents that operation; then use the deterministic resume command without changing frozen source, cohorts or outcomes. No manuscript work."
            )
        else:
            result["next_action"] = (
                f"Inspect the preserved atomic boundary for {task}; outstanding G4 counterparts or evaluator checks remain. Resume only under the original guards and cumulative resource cap, or a supervisor-approved resource amendment; no cohort replacement or test-driven tuning."
            )
    else:
        result["next_action"] = (
            "Supervisor G6 science review of the frozen per-task results and equal-budget source comparisons. Do not tune on these test outcomes or begin manuscript work. Any incomplete512 acquisition comparison needs a separately preregistered independent eligible pool, without replacing original parents or borrowing test labels."
        )
    save(root / "prospective_summary.json", result)
    docs = Path("docs")
    lines = [
        "# Evidence-aware DSRE prospective results",
        "",
        f"Scientific disposition: **{scientific}**. Original science gate: **SCIENTIFIC_ADVANCE_NOT_ESTABLISHED**. These are actual bounded results, not a declaration of full three-domain completion.",
        "",
        "## G1–G6",
        "",
    ]
    lines += [f"- **{g}:** {v}" for g, v in gates.items() if g.startswith("G")]
    lines += [
        "",
        "## Actual independent parent counts",
        "",
        "| Domain | Valid discovery | Valid calibration | Valid test checkpoints | Test checkpoint pairs | Unfilled valid-checkpoint targets D/C/T |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for task, d in domains.items():
        p = d["phases"]
        o = d["outstanding_parent_counts"]
        lines.append(
            f"| {task} | {p['discovery']['completed']}/128 | {p['calibration']['completed']}/1024 | {p['test']['completed']}/256 | {d['paired_test_checks']}/256 | {o['discovery']}/{o['calibration']}/{o['test']} |"
        )
    lines += [
        "",
        "Each entry is one original registered parent and one condition. The table reports valid-checkpoint counts against unchanged targets; already-solved prefix parents remain explicit attrition and are never replaced. A fully attempted cohort is not relabelled as1024 valid recovery logs. Screening is prefix-only source work, not another randomized action-outcome sample. Earlier development and historical data remain inspected development.",
        "",
        "## Source qualification and scientific results",
        "",
        f"Fresh insertion source-v2 pilot: {g1['usable_parents']}/10 usable, five supported measured predicates; aperture explicitly UNKNOWN in telemetry. Complete macro/repeat parity and independent physical terminal geometry checks precede G3.",
        "",
        "The primary logged router physically selects each test action before the isolated evaluator runs its alternative. Other frozen policies and acquisition models are scored using those same audited deterministic macro outcomes. This is a matched parent comparison, not a separate physical deployment or an additional independent test for every method. Evaluator labels never enter fitting or calibration.",
    ]
    for task, d in domains.items():
        lines += ["", f"**{task}:**"]
        if d["source_guard"]:
            w = d["source_guard"]
            lines.append(
                f"Source/checkpoint guard halted at {w['stage']}, registered index {w['spec']['index']}, seed {w['spec']['seed']}: `{w['status']}`. The complete raw first-difference witness is retained. No failed success label is fabricated."
            )
            for failure in d["independent_source_failure_witnesses"]:
                lines.append(
                    f"Independent source witness: error `{failure['error']}`, checkpoint present={failure['checkpoint_present']}, raw SHA256 `{failure['raw_sha256']}`. This is an unavailable decision checkpoint, not an observed failed recovery."
                )
        if d["scientific_result"]:
            m = d["scientific_result"]
            lines.append(
                f"Frozen logged policy: {m['recover']}/{m['n']} qualified recoveries, {m['success']}/{m['n']} completion, {m['required_rescues']} required rescues, {m['harm']} harmful attempts, {m['futile']} both-failure recoveries, signed gain {m['whole_policy_gain']:.6f}; descriptive parent-bootstrap95 {m['gain_parent_bootstrap95']}. Baseline decision equalities: `{d['baseline_equivalence']}`."
            )
            scored = read(root / "prospective" / task / "evaluations/logged.json")
            lines += [
                "",
                f"Oracle cells (continue,recover): `{scored['four_cells']}`. Observed harm per selected recovery CP95: `{m['harm_per_recover_CP95']}`. This descriptive test interval is distinct from the simultaneous calibration certificate; no recoveries gives [0,1], not a zero-risk guarantee.",
                "",
                "| Frozen method | R | Completion | Required rescues | Harm | Futile | Signed gain |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for method, metrics in scored["policies"].items():
                lines.append(
                    f"| {method} | {metrics['recover']} | {metrics['success']}/{metrics['n']} | {metrics['required_rescues']} | {metrics['harm']} | {metrics['futile']} | {metrics['whole_policy_gain']:.6f} |"
                )
            model = read(root / "prospective" / task / "models/logged.json")
            lines += [
                "",
                "Whole-leaf primary calibration bounds (each leaf frozen independently of calibration):",
                "",
                "| Leaf | Harm lower | Harm upper | Gain lower | Gain upper | Diagnosis |",
                "|---|---:|---:|---:|---:|---|",
            ]
            for leaf, record in model["leaves"].items():
                b = record["bounds"]
                lines.append(
                    f"| {leaf} | {b['harm_lower']:.6f} | {b['harm_upper']:.6f} | {b['gain_lower']:.6f} | {b['gain_upper']:.6f} | {record['diagnosis']['status']} |"
                )
        else:
            lines.append(
                "No completed independent test or fitted recovery result is claimed. Selected recoveries, rescues and harms on an unexecuted test are **unmeasured**, rather than reported as a zero-risk result."
            )
        lines.append(
            f"Calibration screens: {d['screen_statuses']}. Absorbing-prefix D/C/T: {[d['phases'][p]['observed_absorbing_prefix'] for p in ('discovery', 'calibration', 'test')]}. Unattempted D/C/T: {list(d['unattempted_parent_counts'].values())}. Untouched test parents: {d['untouched_test_parents']}. Missing terminal labels after assigned actions: {d['missing_terminal_labels_after_assigned_action']}."
        )
        sensitivity = d["registered_test_identification_sensitivity"]
        lines.append(
            f"Full registered-test identification sensitivity: completion {sensitivity['completion']}, signed gain {sensitivity['whole_policy_gain']}, parent harm {sensitivity['parent_harm']}. These are worst/best unknown-parent bounds, not confidence intervals."
        )
        auditpath = (
            root / "prospective" / task / "independent_prospective_audit_full.json"
        )
        if auditpath.exists():
            audit = read(auditpath)
            lines.append(
                f"Independent recorded-data audit: passed={audit['passed']}; CP bands {audit['CP_bands']}, LP extrema {audit['LP_extrema']}, minimum certificates {audit['minimum_certificates']}, maximum numerical discrepancy {audit['max_numerical_error']:.3g}. Qualification failures remain disclosed separately: `{audit['qualification_failures']}`. A passing audit does not repair a failed source."
            )
    lines += [
        "",
        "Navigation calibration seed1078846034 reaches the absorbing goal after18 of the20 prefix controls. Its source success is observed TRUE; there is no valid recovery checkpoint. The original contract preserves it as `ALREADY_SOLVED_PREFIX`, rather than creating a recovery observation, a failure label, or a replacement seed. An initial overly broad guard was corrected before any calibration/test outcomes; the first stop remains sealed. Bounded Pick discovery/screening occurred during that stop, then navigation resumed before Pick calibration/test and insertion. The separately sealed independent audit distinguishes successful-prefix attrition from a missing terminal label. All parent-level policy comparisons retain observed preterminal successes with zero intervention gain.",
        "",
        "## Resources and remaining experimental cost",
        "",
        f"Measured new physics worker wall {totalwall / 3600:.4f}h and worker CPU {result['resources']['measured_new_physics_worker_cpu_seconds'] / 3600:.4f}h. Four independent process chains can run concurrently; elapsed wall and summed worker wall are distinct. The cap is18h summed new physics with2h reserved for audits; artifact cap5GiB. No new dependencies, paid experimental APIs or neural training runs. Actual fitted discovery partitions: {result['resources']['discovery_partition_fits']}; calibrated model files: {result['resources']['calibrated_model_files']}.",
        "",
        "| Domain | Mean future branch seconds | Remaining future invocations excluding G4 | Forecast worker hours excluding screening/G4 |",
        "|---|---:|---:|---:|",
    ]
    for task, r in resources.items():
        lines.append(
            f"| {task} | {r['mean_future_invocation_wall_seconds']:.3f} | {r['remaining_registered_future_invocations_excluding_G4']} | {r['remaining_future_worker_seconds_forecast_excluding_G4'] / 3600:.3f} |"
        )
    lines += [
        "",
        "Additional remaining source work beyond the future-invocation table:",
        "",
    ]
    for task, r in resources.items():
        pair_work = (
            f"{r['remaining_selected_G4_counterpart_requests']} frozen G4 counterparts"
            if r["remaining_selected_G4_counterpart_requests"] is not None
            else "G4 list not yet eligible to freeze; at most512 additional counterpart requests"
        )
        lines.append(
            f"- {task}: {r['remaining_predecision_screen_requests']} prefix-only screens; {pair_work}. Prefix-only mean seconds: {r['mean_prefix_only_invocation_wall_seconds']}."
        )
    lines += [
        "",
        "These forecasts cannot override a qualification blocker. Prefix-only screening, already-executed unsuccessful attempts and preselected G4 counterparts are charged separately in execution receipts. Exact remaining cohort counts remain fixed; no smaller subset is called the original full study. Missing/unexecuted outcomes give worst/best success bounds [known successes/registered N, (known successes+unknown)/registered N] and signed-gain bounds allowing each unknown parent[-1,+1]. With no test executions those are completion[0,1], gain[-1,1], harm[0,1].",
        "",
        "## Audits, preservation and reproduction",
        "",
        "Independent manifest, physical/source-access, binomial-CDF confidence and LP/certificate audits are in the evidence root. The maintained suite passed628 tests with6 skips (`maintained_tests_final.log`). One initial unscoped pytest invocation entered vendored upstream examples; the scoped maintained-suite run is the validation result. Original manuscripts, approved plan, source packages, user changes and first-session seals are preserved. All new raw physics and parent receipts remain local, with compact sampled review material and full hash inventories. `task_diagnostics_and_witnesses.json` records actual both-failure, harmful-action, rescue and observation-alias witnesses without feeding evaluator labels back to any model.",
        "",
        f"The additional independent audit checks every stored extremum/optimizer, constructive same-marginal world pair, exact acquired model membership, outcome-blind within-leaf hash prefix and source/method timing. Actual counts: `{extended['counts']}`; maximum discrepancy {extended['max_numerical_error']:.3g}. It imports no production inference.",
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.",
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1",
        "R=results/dsre-evidence-aware/20261117-prospective",
        "uv run --no-sync pytest -q tests",
        "uv run --no-sync ruff check src scripts tests",
        "uv run --no-sync ruff format --check src scripts tests",
        "# Deterministic resume respects every existing source guard and never replaces parents:",
        'uv run --no-sync python scripts/dsre_evidence_prospective_run.py --root "$R"',
        "# Repeat a full raw audit into fresh storage, preserving the sealed outputs:",
        "T=$(mktemp -d /tmp/dsre-prospective-reproduce.XXXXXX)",
        'uv run --no-sync python scripts/dsre_evidence_prospective_audit.py "$R" --task PickCube-v1 --output "$T/pick_audit.json"',
        "# Compact review from a separate extracted tree:",
        'tar -xzf research/dsre_evidence_design/evidence_aware_prospective_review.tar.gz -C "$T"',
        'uv run --no-sync python "$T/research/dsre_evidence_design/verify_prospective.py"',
        "```",
        "",
        "The raw collector resumes exact-source completed branches; immutable outputs are not overwritten. Independent audits/evaluations are final sealed outputs; reproductions use a fresh extracted review root. Local commit and compact SHA are recorded in the closure receipt. No push, manuscript edit or RSS submission occurred.",
        "",
        "## Exact next action",
        "",
        result["next_action"],
    ]
    (docs / "DSRE_EVIDENCE_AWARE_PROSPECTIVE_RESULTS.md").write_text(
        "\n".join(lines) + "\n"
    )
    historical = read(root / "historical_acquisition_v3/results.json")["curves"]
    lines = [
        "# DSRE evidence-acquisition results",
        "",
        "The primary endpoint is the fixed additional budget512. Lower budgets are descriptive. No best-budget significance or simultaneous cross-strategy guarantee is claimed.",
        "",
        "## Inspected historical mechanism curve",
        "",
        "Same392 discovery parents;568 previously inspected candidate parents; no fresh held-out performance endpoint. Numbers below are qualified-region discovery mass under the stated development calculation, not deployed or confirmation coverage. Each pair costs two outcome reveals, each log one. Historical baseline allocator is the original heuristic; the prospective comparator uses discovery-only decision information.",
        "",
        "| Strategy |64|128|256|512|",
        "|---|---:|---:|---:|---:|",
    ]
    for strategy in (
        "witness",
        "all_logs",
        "all_pairs",
        "uniform_mix",
        "decision_uncertainty",
    ):
        rows = [r for r in historical if r["strategy"] == strategy]
        assert all(r["budget"] == r["logical_cost"] for r in rows)
        lines.append(
            "| "
            + strategy
            + " | "
            + " | ".join(f"{r['qualified_discovery_mass']:.6f}" for r in rows)
            + " |"
        )
    lines += [
        "",
        "Witness, all-logs and all-pairs agree at budget512; no witness advantage is established. Earlier accounting versions are retained: budget prefixes initially left one unit unused. The final version spends every exact budget; thresholds, outcomes and qualification rules were unchanged.",
        "",
        "## Prospective independent-calibration safeguard",
        "",
        "First512 registered calibration parents form the common base. Remaining512 are the candidate pool. Discovery-only diagnoses and candidate predecision observations freeze every list before any calibration outcomes. Every source assignment and within-leaf hash order is outcome-blind. Each strategy runs in a separate whitelisted fitting process. Only its chosen counterpart labels can enter its bounds. Base and candidate records are independent of discovery fitting; whole-leaf CP multiplicity is unchanged.",
        "",
        "Actual collection shares cached physical actions; logical costs charge each strategy separately. A pair from zero costs2; adding an alternative to an already logged parent physically costs1 more. Unselected candidate labels stay hidden from that strategy. All routers and acquisition models freeze before any prospective test.",
        "",
        "| Domain | Schedule frozen | Acquisition counterparts | Complete prospective test |",
        "|---|---|---:|---|",
    ]
    for task, d in domains.items():
        lines.append(
            f"| {task} | {(root / 'prospective' / task / 'acquisition_schedule.json').exists()} | {d['acquisition_counterparts_completed']} | {d['complete_cohort']} |"
        )
    for task in TASKS:
        schedulepath = root / "prospective" / task / "acquisition_schedule.json"
        if schedulepath.exists():
            schedule = read(schedulepath)
            lines += [
                "",
                f"**{task} requested512:** base valid logs {len(schedule['base_ids'])}; eligible independent candidates {len(schedule['candidate_ids'])}.",
            ]
            for strategy, budgets in schedule["schedules"].items():
                cost = sum(r["cost"] for r in budgets["512"])
                lines.append(
                    f"- {strategy}: additional logical cost {cost}/512; unspent {512 - cost}."
                )
    lines += [
        "",
        "Prospective curves and baseline counts are retained in each domain’s frozen models and evaluations. If a source guard prevents collection, no prospective allocation benefit or statistical infeasibility is invented. That is a source-evidence blocker, not proof that512 cannot statistically qualify. The original budget64 experiment alone remains insufficient. At any prospective budget512 with fewer than512 eligible log candidates, the exact logical-cost shortfall is disclosed; no primary512 superiority claim is made from unequal costs.",
        "",
        "## Frozen prospective curves",
        "",
        "Rows disclose all registered budgets, including actual cost and uncertainty width. Widths are unweighted means across frozen leaves, not performance confidence intervals. Reusing the common untouched test is descriptive; no best-budget significance is claimed.",
        "",
        "| Domain | Strategy | Requested | Actual additional | Total calibration | Test R | Gain | Mean harm width | Mean gain width |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    frontiers = read(root / "prospective_acquisition_frontiers.json")["curves"]
    for r in frontiers:
        lines.append(
            f"| {r['task']} | {r['strategy']} | {r['requested_additional_units']} | {r['actual_additional_units']} | {r['total_calibration_units']} | {r['qualified_recoveries']}/{r['test_n']} | {r['whole_policy_gain']:.6f} | {r['mean_leaf_harm_width']:.6f} | {r['mean_leaf_gain_width']:.6f} |"
        )
    lines += [
        "",
        "## Verifiable plot",
        "",
        "`results/dsre-evidence-aware/20261117-prospective/figures/acquisition_development.csv` and `prospective_acquisition.csv` are the plotted numeric sources; corresponding PNG/PDF files are generated from those exact rows. The historical plot is labelled development; the prospective plot is labelled descriptive and uses actual execution costs.",
    ]
    (docs / "DSRE_EVIDENCE_AWARE_ACQUISITION_RESULTS.md").write_text(
        "\n".join(lines) + "\n"
    )
    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    with (figures / "acquisition_development.csv").open("x", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "budget",
                "logical_cost",
                "qualified_discovery_mass",
            ],
        )
        writer.writeheader()
        writer.writerows({k: r[k] for k in writer.fieldnames} for r in historical)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    for i, strategy in enumerate(
        ("witness", "all_logs", "all_pairs", "uniform_mix", "decision_uncertainty")
    ):
        rows = [r for r in historical if r["strategy"] == strategy]
        ax.plot(
            [r["budget"] for r in rows],
            [r["qualified_discovery_mass"] for r in rows],
            label=strategy,
            linestyle=["-", "--", ":", "-.", "--"][i],
            marker=["o", "s", "^", "v", "x"][i],
        )
    ax.set(
        xlabel="Logical action-outcome reveals",
        ylabel="Qualified region mass on discovery",
        title="Historical DEVELOPMENT; no independent performance test",
        ylim=(-0.02, 0.6),
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(figures / "acquisition_development.png", dpi=180)
    fig.savefig(figures / "acquisition_development.pdf")
    plt.close(fig)
    print(
        json.dumps(
            {
                "scientific_decision": scientific,
                "G1_G6": gates,
                "domains": {
                    t: d["outstanding_parent_counts"] for t, d in domains.items()
                },
                "physics_wall_hours": totalwall / 3600,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args()
    report(a.root)
