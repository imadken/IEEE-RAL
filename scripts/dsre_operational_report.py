"""Compact measured operational report, claim ledger and adversarial assessment."""

import argparse
from pathlib import Path

from dsre_followup_batch import atomic, read

from dual_rec.dsre.operational import METHODS


def completed_data_views(root):
    """Retain primary missingness; label every non-test comparison explicitly."""
    from dsre_operational_analysis import paired, qualified, records_for, summarize

    from dual_rec.dsre.operational import OperationalRouter

    historical = read(root / "historical_operational_records.json")
    exploratory = {
        "population": "INSPECTED_HISTORICAL_FOLLOWUP_EXPLORATORY_NOT_NEW_TEST",
        "complete_parents": 333,
        "checkpoints": 666,
        "tables": summarize(historical),
        "paired_intervals": paired(historical),
        "scope": "Frozen new calibration gate applied retrospectively to previously inspected follow-up. These intervals are exploratory and cannot replace the missing primary held-out result.",
    }
    atomic(root / "exploratory_operational_results.json", exploratory)
    _, rows, _ = qualified(root)
    frozen = read(root / "frozen_routers.json")
    calibration = read(root / "calibration_decision.json")["strata"]
    records = records_for(
        [r for r in rows if r["split"] == "calibration"],
        OperationalRouter(frozen),
        frozen,
        calibration,
    )
    atomic(
        root / "calibration_operational_results.json",
        {
            "population": "CALIBRATION_COHORT_DESCRIPTIVE_NOT_HELD_OUT",
            "parents": 360,
            "checkpoints": 720,
            "tables": summarize(records),
            "scope": "Risk gates were chosen using this cohort's action-error counts. Operational counts here describe calibration data, not independent test performance.",
        },
    )
    return exploratory


def interval(value):
    if value is None:
        return "N/A"
    low, high = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} [{100 * low:+.2f}, {100 * high:+.2f}] pp"


def triple(row):
    return (
        f"{row['recommended']}/{row['successful']}/{row['unacceptable']}"
        if row
        else "0/0/0"
    )


def write(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Sealed evidence")
    result = read(root / "operational_results.json")
    tables = result["tables"]
    missing = read(root / "missingness.json")
    calibration = (
        read(root / "calibration_decision.json")
        if (root / "calibration_decision.json").exists()
        else {"strata": {}, "parents": 0}
    )
    robustness = read(root / "observation_robustness.json")
    audit = read(root / "independent_audit.json")
    assert audit["status"] == "PASS"
    exploratory = completed_data_views(root)
    lines = [
        "# DSRE: operational recovery justification, calibration and observation robustness",
        "",
        f"Evidence: `{root}`. Base `c2f77332f0a72b7f3930e846c1d4e0a8f82da67b`; branch `research/dsre-operational-full-paper`. Exact local commit, archive and resource accounting are in completion_manifest.json.",
        "",
        f"Registered 520 new parents: 360 calibration plus 160 disjoint test. Completed {missing['complete_parents']}/520; new test {result['complete_parents']}/160 parents, {result['checkpoints']}/320 checkpoints. Missing/partial IDs and all secondary qualified cells are explicit in missingness.json. Prior 333-parent follow-up and earlier interrupted cohort remain sealed and unchanged.",
        "",
        "## Scientific and operational contract",
        "",
        "The fixed question is which observable facts suffice to justify a fixed robot intervention relative to paired outcomes, and why justification fails. Exact sufficient rules, support/ties, two skills, horizon, utility and witnesses remain unchanged. B7 and the equally wrapped ordinary risk rule are mathematically equivalent; no new pure-rule algorithm or controller is claimed. Runtime schemas forbid outcome labels and require common facts to agree across comparators. No new model fits were performed. Four existing depth-1/2 trees at budget one are loaded without training; full-reference outcomes remain development only.",
        "",
        "Abstention is defer/stop and contributes zero to unconditional autonomous completion. Conditional success among actions is separate. Initially unsuccessful means terminal task success is false at the decision checkpoint; it does not assert a separately annotated failure event or that a normal unfinished prefix is a failure. Required recovery means recover-only adequacy relative to the two fixed skills and horizon. Neither-success actions are inadequate even if intervention regret relative to the best available action is zero.",
        "",
        "All new paired measurements use unchanged CPU physics, complete reset/action-prefix reconstruction and controller/model checks. The registered test planned an additional calibrated selected branch after a fresh reset/prefix. Its first guard failed before a continuation, so no selected repeat was completed. Paired outcome lookup remains deterministic counterfactual estimation and is not misrepresented as a standalone online campaign.",
        "",
        "## Independent calibration and exact bounds",
        "",
        f"Actual calibration: {calibration['parents']}/360 parents. Primary target: assigned-parent any-error probability <=10% for task/action strata, under the two registered conditions and fixed seed distribution. Any bad assigned condition marks that parent erroneous. All 17 methods use global delta=.05/(4*17), requiring 69 zero-error assigned parents; primary four-stratum diagnostic delta=.0125 requires 42. Only the stricter global gate enables actions. The bound is not for arbitrary time points, shifted observations, hardware or checkpoint-weighted sampling.",
        "",
        "| Method | Task/action | Assigned parents | Erroneous parents | Primary diagnostic upper | Global-family upper | Operational status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for key, bound in calibration["strata"].items():
        method, task, action = key.split("|")
        lines.append(
            f"| {method} | {task}/{action} | {bound['assigned_parents']} | {bound['error_parents']} | {100 * bound['primary_four_stratum_upper']:.3f}% | {100 * bound['upper']:.3f}% | {bound['status']} |"
        )
    lines += ["", "Primary unqualified strata and remaining sample limitations:", ""]
    for key, bound in calibration["strata"].items():
        if not key.startswith("DSRE_risk|") or bound["enabled"]:
            continue
        n, k = bound["assigned_parents"], bound["error_parents"]
        need = (
            f"At least {max(0, 69 - n)} additional independent assigned parents with no additional errors would be needed to reach the global zero-error minimum."
            if k == 0
            else "Observed errors require more than the zero-error minimum; no new cohort or stopping rule is authorized here."
        )
        lines.append(
            f"- {key}: {n} assigned, {k} erroneous. {need} More unassigned nominal trials do not directly qualify this action. A future independently fixed cohort must preserve the assignment distribution or state its changed estimand; this is a sample limitation, not authorization for replenishment."
        )
    lines += [
        "",
        "Calibration selection is outcome-independent; the immutable decision/seal precedes every test parent. No threshold, allocation, rule, action or reference is updated from test labels. Empty/underpowered strata stay NOT CERTIFIED. No targeted replenishment was performed. Conditional certification is limited to enabled strata and stated simulator/observation scope.",
        "",
        "## Disjoint held-out operational results",
        "",
        "Counts are recommendations / successful / unacceptable. All denominators include deferral; reported autonomous completion counts are exactly successful selected actions. Proposed and globally gated modes are separated. Full-signature is upper-information, not a fair minimum-explanation length competitor; policy-faithful explains a tree label rather than action adequacy.",
        "",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        for mode in ("proposal", "calibrated"):
            lines += [
                f"### {task}: {mode}",
                "",
                "| Method | N | Rec/good/bad | Deferred | Conditional good | Autonomous completion | Initially unsuccessful good/N | Required recovery good | Unnecessary recovery, initially successful |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
            for method in METHODS:
                head = f"{task}|{method}|{mode}|clean|"
                row = tables.get(
                    head + "all",
                    {
                        "checkpoints": 0,
                        "recommended": 0,
                        "successful": 0,
                        "unacceptable": 0,
                        "deferred": 0,
                        "conditional_success": None,
                        "autonomous_completion_rate": 0,
                        "required_recovery_success": 0,
                        "unnecessary_recover_initial_success": 0,
                    },
                )
                failed = tables.get(
                    head + "initial_failure", {"successful": 0, "checkpoints": 0}
                )
                conditional = (
                    "N/A"
                    if row["conditional_success"] is None
                    else f"{100 * row['conditional_success']:.2f}%"
                )
                completion = (
                    f"{100 * row['autonomous_completion_rate']:.2f}%"
                    if row["checkpoints"]
                    else "NOT ESTIMABLE"
                )
                lines.append(
                    f"| {method} | {row['checkpoints']} | {triple(row)} | {row['deferred']} | {conditional} | {completion} | {failed['successful']}/{failed['checkpoints']} | {row['required_recovery_success']} | {row['unnecessary_recover_initial_success']} |"
                )
    if not result["complete_parents"]:
        lines += [
            "",
            "**No complete held-out test parent exists. All test rates and effects are NOT ESTIMABLE; zero counts are empty populations, not measured zero success or error.** The first test parent failed the selected reset qualification before any selected continuation. One independently qualified paired checkpoint is retained as secondary evidence; it is never promoted to a completed parent. The remaining 159 parents are untouched. See study_halt.json and selected_qualification_failure_diagnosis.json. No physics was resumed, no seeds replaced and no frozen source amended.",
            "",
        ]
    for name, view in (
        (
            "Calibration cohort: descriptive, gates fitted on these errors",
            read(root / "calibration_operational_results.json"),
        ),
        (
            "Previously inspected 333-parent follow-up: exploratory application of new gates, not new held-out confirmation",
            exploratory,
        ),
    ):
        lines += [
            f"## {name}",
            "",
            "| Task | Method | N | Gated good/bad/defer | Initially unsuccessful good/N | Required recoveries | Maintained success |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for task in ("PickCube-v1", "PushCube-v1"):
            for method in METHODS:
                head = f"{task}|{method}|calibrated|clean|"
                row = view["tables"][head + "all"]
                failed = view["tables"].get(
                    head + "initial_failure", {"successful": 0, "checkpoints": 0}
                )
                lines.append(
                    f"| {task} | {method} | {row['checkpoints']} | {row['successful']}/{row['unacceptable']}/{row['deferred']} | {failed['successful']}/{failed['checkpoints']} | {row['required_recovery_success']} | {row['maintained_success']} |"
                )
        lines += [
            "",
            "Primary gated outcome decomposition for this same labeled population:",
            "",
            "| Task | Outcome/start subgroup | N | Good/bad/defer | Required recovery | Maintained success |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for task in ("PickCube-v1", "PushCube-v1"):
            for pop in (
                "continue_only",
                "recover_only",
                "both",
                "neither",
                "initial_success",
                "initial_failure",
            ):
                row = view["tables"].get(f"{task}|DSRE_risk|calibrated|clean|{pop}", {})
                lines.append(
                    f"| {task} | {pop} | {row.get('checkpoints', 0)} | {row.get('successful', 0)}/{row.get('unacceptable', 0)}/{row.get('deferred', 0)} | {row.get('required_recovery_success', 0)} | {row.get('maintained_success', 0)} |"
                )
    lines += [
        "",
        "### Exploratory historical paired effects; not the missing primary estimate",
        "",
        "| Task/contrast | Population | Completion difference [95%] |",
        "|---|---|---:|",
    ]
    for key, effects in exploratory["paired_intervals"].items():
        if any(
            f"DSRE_risk-{m}|" in key
            for m in (
                "DSRE_strict",
                "B7_risk",
                "CART2_beta10",
                "B5_beta10",
                "B0_recover",
            )
        ):
            task, contrast, pop = key.split("|")
            lines.append(
                f"| {task}/{contrast} | {pop} | {interval(effects['successful'])} |"
            )
    lines += [
        "",
        "## Primary paired uncertainty and strong controls",
        "",
        "4000 seed-parent paired draws, PCG64 seed2026111401+taskindex, both conditions kept together. All task parents remain the subgroup resampling frame. These effect intervals are distinct from the exact binomial calibration gate. Zero-variation intervals are not population safety bounds.",
        "",
        "| Task, risk-tier minus comparator | Population | Completion difference [95%] | Unacceptable difference [95%] | Required-recovery difference [95%] |",
        "|---|---|---:|---:|---:|",
    ]
    for key, cell in result["paired_intervals"].items():
        if any(
            "DSRE_risk-" + m + "|" in key
            for m in (
                "DSRE_strict",
                "B7_risk",
                "CART2_beta10",
                "B5_beta10",
                "B0_recover",
            )
        ):
            task, contrast, pop = key.split("|")
            lines.append(
                f"| {task}, {contrast} | {pop} | {interval(cell['successful'])} | {interval(cell['unacceptable'])} | {interval(cell['required_recovery_success'])} |"
            )
    lines += [
        "",
        "### Four outcome classes and initially successful versus unsuccessful starts",
        "",
        "| Task | Primary gated population | N | Rec/good/bad | Continue/recover | Maintained-success completions | Initially unsuccessful completions | Required-recovery completions |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        for pop in (
            "initial_success",
            "initial_failure",
            "continue_only",
            "recover_only",
            "both",
            "neither",
        ):
            row = tables.get(
                f"{task}|DSRE_risk|calibrated|clean|{pop}",
                {
                    k: 0
                    for k in (
                        "checkpoints",
                        "recommended",
                        "successful",
                        "unacceptable",
                        "continue",
                        "recover",
                        "maintained_success",
                        "failed_start_success",
                        "required_recovery_success",
                    )
                },
            )
            lines.append(
                f"| {task} | {pop} | {row['checkpoints']} | {triple(row)} | {row['continue']}/{row['recover']} | {row['maintained_success']} | {row['failed_start_success']} | {row['required_recovery_success']} |"
            )
    lines += [
        "",
        "### Condition-level matched comparisons",
        "",
        "| Task | Condition | Method | Globally gated rec/good/bad | Deferred |",
        "|---|---|---|---:|---:|",
    ]
    for task, conditions in (
        ("PickCube-v1", ("nominal", "offset002")),
        ("PushCube-v1", ("nominal", "misaligned")),
    ):
        for condition in conditions:
            for method in METHODS:
                row = tables.get(f"{task}|{method}|calibrated|clean|{condition}")
                if row:
                    lines.append(
                        f"| {task} | {condition} | {method} | {triple(row)} | {row['deferred']} |"
                    )
    selected = audit["selected_execution"]
    lines += [
        "",
        "## Qualified selected physical execution",
        "",
        f"New selected-action continuations: {selected['new_selected_action_continuations']}; stopped/deferred checkpoints: {selected['deferred_checkpoints']}; future-trajectory disagreements: {selected['future_trajectory_disagreements']}; independently rederived action discrepancy maximum: {selected['maximum_action_error']}. Every executed branch has a separate reset/prefix, outcome-free decision payload and calibration hash. Repeated branches share their original parent and never inflate statistical N.",
        "",
        "## Observation corruption: inspected historical cohort, offline only",
        "",
        "Use the already inspected 333-parent/666-checkpoint suffix, not independent calibration. The same corrupted predecision packet is shared by methods; original branch outcomes are unchanged. Twelve scenarios are all reported. Gaussian replicates and two conditions never become independent parents. Applying the clean gate under corruption does not transfer certification. False-fact confidence means a proposed explanation asserts a fact contradicted by the original clean telemetry; it is distinct from actual bad actions and from statistical confidence.",
        "",
        "| Task | Method | Input scenario | Proposed good/bad/deferred | Stable actions/N | Stable certificates/N | Contradicted-fact proposals | Payload bytes / scalar fields |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    if not selected["new_selected_action_continuations"]:
        lines += [
            "",
            "**Selected physical execution parity is NOT ASSESSABLE.** Zero future disagreements and zero maximum action discrepancy above mean zero executed branches, not observed perfect agreement. The first guard failed before a selected continuation; its live diagnostics were not retained. The offline contact list/tuple regression demonstrates a sufficient software defect, not actual selected-trajectory parity. qualification_normalization_candidate.patch is unexecuted future engineering repair; the frozen attempted runner and evidence remain unchanged.",
            "",
        ]
    for key, stability in robustness["stability"].items():
        task, method, mode, scenario = key.split("|")
        if mode != "proposal" or method not in (
            "DSRE_strict",
            "DSRE_risk",
            "B7_risk",
            "CART2_beta10",
            "B5_beta10",
            "policy_faithful",
        ):
            continue
        row = robustness["tables"][key + "|all"]
        n = row["checkpoints"]
        lines.append(
            f"| {task} | {method} | {scenario} | {row['successful']}/{row['unacceptable']}/{row['deferred']} | {stability['action_stable']}/{n} | {stability['certificate_stable']}/{n} | {stability['false_fact_confidence']} | {stability['mean_payload_json_bytes']:.1f}/{stability['mean_scalar_input_fields']:.1f} |"
        )
    lines += [
        "",
        "Every method/scenario/mode/condition/category result is retained in observation_robustness.json and robustness_records.json. The fixed 1 mm boundary-proximity flag is retained per record. Serialized bytes/scalars describe the observed-history interface, not distinct physical sensors or acquisition cost. Abstract predicates and certificate lengths are separate; shared raw pose fields supply several predicates. Routing times include the documented all-method cached computation path, not physical sensing/actuation latency.",
        "",
        "## Preserved history, physical cases and breadth blocker",
        "",
        "The previous untouched suffix remains 333 parents/666 checkpoints/1332 continuations: Pick strict145->187/332, +12.65pp[9.33,16.27]; initially unsuccessful16->18/109, one extra required recovery; zero observed strict errors. Forty of42 additions were initially successful, B7 was exact, CART2/cap2 differed once, provisional CART240/332 exceeded strict187/332. Push strict0/334 versus recovery334/334 remains intact. Neither prior cohort nor the inspected preliminary33 parents/task is used as new calibration. Historical raw seals and the old unknown SIGTERM cause are unchanged.",
        "",
        "Old physical cases and raw-source hashes remain in the previous physical_examples.json: three-fact/five-parent recovery evidence versus a neither-success collision, both-success adequacy without necessity, and Push opposing actions sharing all12 predicates. These are illustrative reference examples, not threshold tuning. The full manuscript retains these alongside new operational evidence.",
        "",
        "Lift/Panda is blocked by the pre-outcome source-semantic gate: the old alternative is a nominal speed clip, with210/210 both-success starts and no registered failed-start recovery contrast. No new third-task physics, controller, fault or task selection occurred. This remains a material breadth limitation.",
        "",
        "## Reproduction, tests and evidence integrity",
        "",
        f"Immutable verification: `PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_operational_finish.py --root {root} --stage verify`.",
        f"Recompute independent raw-action/rule, CP, paired-bootstrap, corruption and PDF audits without changing sealed evidence: `PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_operational_finish.py --root {root} --stage reproduce`. This creates only a scratch audit directory with read-only input links and prints its output path. It runs no physics, training or recalibration.",
        "Regressions: `UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest`; maintained-source lint: `UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff check src scripts tests`. An additional root-wide `ruff check .` found eight pre-existing errors in immutable results/monitoring-study scripts; those historical files were preserved. The original physics is reproduced only as a separately preregistered campaign on an unused manifest, never by resuming or overwriting this sealed root.",
        "",
        "Reproduce analysis in a scratch copy of the frozen metadata and read-only links, never in the sealed root. See commands.jsonl for the exact bounded worker commands and protocol/source hashes. The scientific scripts and config are pinned in confirmation_freeze.json. Calibration decision/seal predates all test attempts. Regression, independent raw physics/rule/direct-tree/CP and separate numerical audits are retained; these are separate same-session implementations, not external human replication. All tests, PDF font/anonymity/page checks, archive hashes, worker usage and the exact local commit appear in the final seal.",
        "",
        "No GitHub push, conference submission, manuscript upload, new dataset, GPU training or paid API. .gitignore, uv.lock, historical evidence and unrelated changes are preserved. Calibration and corrupted-input risk must not be conflated with hardware safety or an improved recovery controller.",
    ]
    import numpy as np

    predictions = read(
        root
        / (
            "test_records.json"
            if result["complete_parents"]
            else "historical_operational_records.json"
        )
    )
    timed = {}
    for record in predictions:
        timed.setdefault(record["id"], record["route_all_methods_ms"])
    if timed:
        elapsed = np.asarray(list(timed.values()))
        lines += [
            "",
            f"Measured clean {'test' if result['complete_parents'] else 'inspected historical'} routing, all 17 methods together over {len(timed)} unique checkpoints: mean {elapsed.mean():.4f} ms, median {np.median(elapsed):.4f} ms, p95 {np.percentile(elapsed, 95):.4f} ms, maximum {elapsed.max():.4f} ms. The frozen router memoizes identical queries; these are actual mixed cold/cached-call costs including common computations, not isolated per-method benchmarks or sensor/robot latency. Per-view times and literal/support counts are retained in the corresponding prediction records.",
        ]
    Path("docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md").write_text(
        "\n".join(lines) + "\n"
    )
    gate = {
        "method": "CORRECT_SCOPED_CONTRACT; established exact rules/robust feasibility; no algorithmic novelty",
        "evidence": "CALIBRATION_ONLY_NO_COMPLETE_NEW_TEST; historical operational estimates exploratory; selected execution halted; rare/absent strata and third task blocked"
        if not result["complete_parents"]
        else "INDEPENDENT_TWO_TASK_OPERATIONAL_STUDY; rare/absent action strata and blocked third task limit scope",
        "paper": "Requires final master/Stage1 content, page, font, anonymity and claim audits; no acceptance prediction",
        "completed_calibration_parents": calibration["parents"],
        "completed_test_parents": result["complete_parents"],
        "planned_test_parents": 160,
        "primary_enabled_strata": {
            k: v for k, v in calibration["strata"].items() if k.startswith("DSRE_risk|")
        },
        "third_task": "BLOCKED_SOURCE_SEMANTICS",
        "end_to_end_controller_improvement_claim": False,
        "B7_risk_identity": True,
        "no_submission_or_push": True,
        "PAPER_DRAFT_READY": "Pending final PDF audit",
    }
    atomic(root / "scientific_gate.json", gate)
    critique = f"""# DSRE operational full-paper: adversarial scientific assessment

This is a same-session adversarial review, not external peer review. The complete
calibration/test allocation is preregistered and every estimate is sourced to the
new evidence root `{root}`. Prior inspected data are excluded from calibration.

## Method

The contract distinguishes factual observation, policy-label fidelity, measured
action adequacy, decision necessity and generalization. Exact minimum pure rules,
robust feasible-action intersections and Clopper-Pearson inference are established.
B7 and the ordinary strict-then-risk wrapper remain equivalent. The contribution
must be the intervention-grounded operational specification and measured
consequences of stopping, risk qualification and imperfect observations. A shorter
explanation than a tree path is not evidence of a new algorithm or human benefit.

## Evidence

Completed calibration: {calibration["parents"]}/360 parents. Disjoint test:
{result["complete_parents"]}/160 parents and {result["checkpoints"]}/320 checkpoints.
Global method/task/action multiplicity is accounted for. Certification concerns
parent-any-error under the fixed two-condition seeded simulator scope. It cannot
be generalized to checkpoint-weighted deployment or arbitrary future sensors.
Every primary action stratum, including zero assignments, appears in the report.
Rare Pick recovery is not made certifiable by collecting more nominal continues.
The fixed allocation was never replenished based on results.

Operational tables include deferral as zero completion, all four outcome categories,
initially unsuccessful/successful subsets, matched-condition baselines and paired
uncertainty. New selected-branch execution checks are explicitly repeated reset
executions of an already paired parent. They do not create additional independent
trials or justify calling the study a standalone closed-loop system evaluation.

The inspected 333-parent robustness cohort is offline observation corruption. Its
clean calibrated gate cannot retain a formal guarantee under shifted inputs.
Observation bytes and predicate counts are not physical sensing costs. Lift failed
the source-semantic prerequisite and supplies no distinct recovery breadth result.

## Two strongest remaining reviewer objections

1. **The same ordinary rules/tree with the same statistical gate may be sufficient.**
   The manuscript must show the exact operating tables and equivalences prominently.
   An operational distinction between finite justification, appropriate action and
   calibration can be scientifically informative without a new algorithm. If the
   strongest ordinary comparator matches, method superiority remains unestablished.

2. **The new held-out operational study is incomplete; two simple simulator tasks
   and sparse recovery assignments do not establish a broad trustworthy system.** The record must retain the failed selected-execution guard, actual {result["complete_parents"]}/160 test parents and blocked third
   task, idealized observed poses, horizon-specific utility, finite deterministic
   seed scope and all NOT CERTIFIED actions. A meaningful third intervention and
   independently assigned rare-action cohorts remain necessary before a broad
   deployment claim. No new controller or hand-selected fault is invented here.

## Rebuttal preparation

- Explain exact B7 identity directly; do not claim novel pure-rule or hitting-set
  mathematics. Cite Khan, Anchors, DISCRET and robust partial observability in their
  actual scopes. B5 is an adaptation, not a reproduction of DISCRET.
- Answer operational relevance using completion with defer/stop, not conditional
  precision alone. Separate initially successful maintenance, continue-only success,
  recover-only necessity and neither-success inadequacy.
- Answer risk questions with actual assigned/error parent counts, both diagnostic
  and global-family bounds and the immutable test-time gate. Zero observed errors
  are not zero risk. No calibration outcome changes the models or reference.
- Answer replay validity with full-prefix/controller/model/source checks, actual
  selected-repeat counts and every guard failure. No selected execution means
  parity is unassessed. Future duplicates share their parent and do not increase N.
- Answer robustness with the whole frozen grid, boundary cases, UNKNOWN handling,
  false-fact confidence and bad actions, including unfavorable ordinary baselines.
  No clean-scope guarantee transfers to a corrupted input model.

## Readiness in three dimensions

**Method:** scoped and mathematically checkable; algorithmic distinctiveness is not
established. **Evidence:** {calibration["parents"]}/360 calibration and {result["complete_parents"]}/160 test parents;
calibration and held-out confirmation are distinct. The new operational result is
incomplete if no full test parents exist. Retrospective comparisons remain exploratory;
broad recovery, sensor transfer and third-task validation remain limited.
**Paper:** the master has eight content pages plus references and Stage1 five plus one,
with anonymous embedded fonts and final claim/format evidence in final_audit.json. The principal
researcher must judge whether the operational insight is consequential enough for
RSS. This report does not claim publication readiness, guaranteed acceptance or
hardware recovery improvement. No push, upload or submission is performed.
"""
    if not result["complete_parents"]:
        critique += "\n## Actual failed operational gate\n\nThe new calibration is complete, but the primary held-out operational effect is NOT ESTIMABLE: 0/160 test parents, one secondary paired checkpoint, no selected continuation. An offline contact list/tuple defect is sufficient to trigger the guard; failed live diagnostics were not saved. No physical parity is established. The explicit frozen halt was honored without repeats, model changes or replacement seeds. The papers therefore use only prominently labeled retrospective operational comparisons on the inspected old cohort. This is not independent prospective operational confirmation. A future fixed study must first qualify the corrected selected executor, then collect an untouched test allocation and sufficient rare-action assignments. Pick recover needs at least 56 more zero-error assigned parents under the global standard; no targeted replenishment is performed here.\n\nThe method specification can pass its scoped mathematical gate, while the operational evidence gate remains INCOMPLETE. Formal paper compilation does not remove this scientific weakness or establish RSS readiness.\n"
    Path("docs/DSRE_RSS2027_REVIEWER_CRITIQUE.md").write_text(critique)
    Path("rss2027/CONTRIBUTIONS_AND_LIMITATIONS.md").write_text(
        "# DSRE operational research scope\n\n"
        + critique.split("## Method\n\n", 1)[1].split("## Evidence", 1)[0]
        + f"\nNew independent calibration/test: {calibration['parents']}/360 and {result['complete_parents']}/160 parents. Exact results, bounds and scope are in docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md.\n\n"
        + critique.split("## Readiness in three dimensions\n\n", 1)[1]
    )
    ledger = Path("rss2027/CLAIM_EVIDENCE_LEDGER.md")
    heading = "\n## Operational full-paper campaign\n"
    previous = ledger.read_text().split(heading)[0]
    entries = [
        heading,
        f"Evidence root: `{root}`. Protocol/source pins precede new physics; calibration seal precedes test.\n",
        "| Claim | Evidence and limitation |",
        "|---|---|",
        f"| {calibration['parents']}/360 calibration, {result['complete_parents']}/160 test parents | fresh_seed_manifest.json, atomic parent_progress, calibration_seal.json, missingness.json; no replacement or old-data calibration. |",
        "| Parent-action exact risk; global method family | calibration_plan.json, calibration_decision.json, independent SciPy bounds; 69 zero-error assignments globally versus42 diagnostic. |",
        f"| {selected['new_selected_action_continuations']} new selected executions, {selected['future_trajectory_disagreements']} future disagreements | selected raw sources; repeats are not new independent parents. |",
        "| All17 common-risk baseline comparisons and defer/stop | operational_results.json and test_records.json; full-signature is upper-information, policy-faithful targets labels. |",
        "| Twelve frozen observation scenarios on inspected old suffix | observation_robustness.json, robustness_records.json; no physical sensor deployment or calibration transfer. |",
        "| No qualified third recovery task | third_task_audit.json; Lift source-semantic prerequisite failed before new physics. |",
        "| Existing mathematical equivalences remain | Frozen ordinary rules/oracles and exact action comparisons; no algorithmic superiority. |",
        "| No new model fits/controllers; old333-parent study preserved | Source hashes, regression and final preservation audit. |",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        for method in (
            "DSRE_strict",
            "DSRE_risk",
            "B7_risk",
            "CART2_beta10",
            "B5_beta10",
            "B0_recover",
        ):
            row = tables.get(f"{task}|{method}|calibrated|clean|all")
            if row:
                entries.append(
                    f"| {task}, {method}: {triple(row)} of{row['checkpoints']} | New disjoint test only, global clean-scope gate; operational_results.json. |"
                )
    ledger.write_text(previous + "\n".join(entries) + "\n")
    print(
        {"report_updated": True, "test_parents": result["complete_parents"]}, flush=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    write(parser.parse_args().root)
