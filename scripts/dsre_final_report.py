"""Measured final-sprint tables, calibrated scope and adversarial interpretation."""

import argparse
from pathlib import Path

import numpy as np
from dsre_followup_batch import read

from dual_rec.dsre.operational import METHODS

LEAD = (
    "DSRE_strict",
    "DSRE_risk",
    "B7_risk",
    "CART1_beta10",
    "CART2_beta10",
    "B5_beta10",
    "B0_continue",
    "B0_recover",
)


def effect(value):
    if value is None:
        return "NOT ESTIMABLE"
    lo, hi = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}] pp"


def row(tables, task, method="DSRE_risk", mode="calibrated", pop="all"):
    return tables.get(
        f"{task}|{method}|{mode}|clean|{pop}",
        dict.fromkeys(
            (
                "checkpoints",
                "parents",
                "recommended",
                "successful",
                "unacceptable",
                "deferred",
                "maintained_success",
                "failed_start_success",
                "required_recovery_success",
                "intervention_regret",
                "autonomy_regret",
                "unnecessary_recover_initial_success",
                "literals",
            ),
            0,
        ),
    )


def write(root):
    assert not (root / "completion_manifest.json").exists()
    results = read(root / "operational_results.json")
    tables = results["tables"]
    missing = read(root / "missingness.json")
    cal = read(root / "calibration_decision.json")
    audit = read(root / "independent_audit.json")
    assert audit["status"] == "PASS"
    lines = [
        "# DSRE final operational results",
        "",
        f"Evidence: `{root}`. Starting commit 873556b54ce9f783326ee2c08bd0303447ed041d; branch `research/dsre-rss2027-final-evidence`. Exact final commit/archive/resources are recorded in completion_manifest.json.",
        "",
        f"Completed **{results['complete_parents']}/{results['planned_parents']} untouched continuation parents**, {results['checkpoints']} primary paired checkpoints. The original plan was 160; Pick8000180 remains contaminated, failed and excluded in the immutable old root. It is not rerun or replaced. The continuation allocation is 79 Pick and 80 Push parents, both original conditions. Missing/partial parents and {missing['qualified_secondary_cells']} secondary qualified cells appear in missingness.json.",
        "",
        "## Qualification and scope",
        "",
        "The representation repair normalizes live contact tuples through jsonable before three existing strict state comparisons. Tolerances, contacts, full prefixes, controller memory, model edits, source hashes and action equations remain checked. Four inspected calibration states pass both-action replay (eight complete action continuations), followed by the actual calibrated selected-executor checks. Original failed-parent evidence remains intact; no untouched test parent supplied preflight data. qualification_results.json and the source repair/split seals precede collection. A preparer-only closure binding change for lint is recorded with original qualified source bytes; it does not alter the qualified executor.",
        "",
        "Runtime PolicyInput contains only task and declared predecision Boolean observations, not condition IDs, seeds, outcomes or privileged future. All 17 methods retain identical original references, skills, support/ties, thresholds, four old CART trees, and the same global method/task/action risk gate. No model fits or new controllers. B7 and the ordinary strict-then-capped-risk wrapper are equivalent. Full-signature uses more information; policy-faithful targets a tree label rather than intervention adequacy.",
        "",
        "STOP/DEFER receives zero autonomous-completion credit, including already-successful checkpoints. This is the prescribed autonomy metric, not a physical measurement that stopping destroys task success. Conditional success among recommendations and physical paired outcomes are separate. Selected repeats validate deterministic execution on the same parent; they are not independent trials or a standalone closed-loop deployment. Initially unsuccessful means task success false at the checkpoint, not an independently annotated failure.",
        "",
        "## Frozen calibration: unchanged exact parent-action bounds",
        "",
        "Target<=10% parent-any-error risk under the two fixed conditions and assumed independent seed-parent distribution. Global delta=.05/(4*17) for all formal gates; four-stratum diagnostic delta=.0125 never overrides it. Bounds do not transfer to arbitrary checkpoints, shifted sensors or hardware. No test labels update eligibility.",
        "",
        "| Method | Task/action | Cal assigned/error parents | Global upper | Diagnostic upper | Gate | Test proposal assigned/error parents |",
        "|---|---|---:|---:|---:|---|---:|",
    ]
    assigned = read(root / "test_assignment_errors.json")
    for key, b in cal["strata"].items():
        method, task, action = key.split("|")
        a = assigned[key]
        lines.append(
            f"| {method} | {task}/{action} | {b['assigned_parents']}/{b['error_parents']} | {100 * b['upper']:.3f}% | {100 * b['primary_four_stratum_upper']:.3f}% | {b['status']} | {a['assigned_parents']}/{a['error_parents']} |"
        )
    lines += [
        "",
        "Pick recover remains NOT CERTIFIED (13/0; upper42.594%); Push continue has no assignments. At least56 additional independent error-free Pick-recover assignments would be needed to reach the global zero-error minimum 69. This is a sample limitation, not permission to replenish, pool old trials, reuse test outcomes or stop on favorable results.",
        "",
        "## Main matched operating points",
        "",
        "Counts are successful / inadequate / STOP. Every denominator includes STOP for autonomous credit. Ungated fixed-policy outcomes are a separate descriptive comparison, not certified deployment performance.",
        "",
        "| Task | Mode | Method | Parents / checkpoints | Good / bad / STOP | Conditional good | Autonomous good/N | Required recoveries | Maintained success |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        for mode in ("calibrated", "proposal"):
            for method in METHODS:
                r = row(tables, task, method, mode)
                n = r["checkpoints"]
                rec = r["recommended"]
                conditional = f"{r['successful']}/{rec}" if rec else "NOT ESTIMABLE"
                lines.append(
                    f"| {task} | {mode} | {method} | {r['parents']}/{n} | {r['successful']}/{r['unacceptable']}/{r['deferred']} | {conditional} | {r['successful']}/{n} | {r['required_recovery_success']} | {r['maintained_success']} |"
                )
    lines += [
        "",
        "## Paired parent uncertainty",
        "",
        "4000 draws, PCG64 seed2026111401+taskindex, both conditions kept together; subgroup ratios resample all task parents. Effect intervals are not CP eligibility bounds. Degenerate intervals are not zero population risk.",
        "",
        "| Task/contrast | Population | Completion difference [95%] | Inadequate difference [95%] | Required-recovery difference [95%] |",
        "|---|---|---:|---:|---:|",
    ]
    for key, values in results["paired_intervals"].items():
        task, contrast, pop = key.split("|")
        lines.append(
            f"| {task}/{contrast} | {pop} | {effect(values['successful'])} | {effect(values['unacceptable'])} | {effect(values['required_recovery_success'])} |"
        )
    lines += [
        "",
        "## Four outcome categories, necessity and condition slices",
        "",
        "| Task | Method | Population | N | Good/bad/STOP | Maintained | Initially unsuccessful good | Required recovery | Intervention/autonomy regret | Avoidable recover, initially successful |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        conditions = (
            ("nominal", "offset002")
            if task == "PickCube-v1"
            else ("nominal", "misaligned")
        )
        for method in LEAD:
            for pop in (
                *conditions,
                "continue_only",
                "recover_only",
                "both",
                "neither",
                "initial_success",
                "initial_failure",
            ):
                r = row(tables, task, method, "calibrated", pop)
                lines.append(
                    f"| {task} | {method} | {pop} | {r['checkpoints']} | {r['successful']}/{r['unacceptable']}/{r['deferred']} | {r['maintained_success']} | {r['failed_start_success']} | {r['required_recovery_success']} | {r['intervention_regret']}/{r['autonomy_regret']} | {r['unnecessary_recover_initial_success']} |"
                )
    p = audit["heldout"]
    lines += [
        "",
        "## Physical parity, cost and interpretation",
        "",
        f"Independent raw audit: {p['raw']['qualified_traces']} traces, {p['raw']['prefix_states']} paired prefix states, {p['raw']['intervention_controls']} controls, maximum action discrepancy{p['raw']['maximum_action_error']}. New selected executions{p['selected_executions']}; selected STOPs{p['deferred_checkpoints']}; selected prefix/future states{p['selected_prefix_states']}/{p['selected_future_states']}; disagreements{p['selected_disagreements']}. Every method's preexecution proposal/gate decision is checked ({p['all_method_preexecution_decisions_checked']} views). These counts are not additional independent parent N.",
        "",
    ]
    records = read(root / "test_records.json")
    timed = {r["id"]: r["route_all_methods_ms"] for r in records}

    if timed:
        a = np.asarray(list(timed.values()))
        lines.append(
            f"All 17-method routing over{len(timed)} clean checkpoints: mean{a.mean():.4f}ms, median{np.median(a):.4f}ms, p95{np.percentile(a, 95):.4f}ms, maximum{a.max():.4f}ms. Mixed cold/cached identical-query computation includes common work; this is not an isolated algorithm benchmark or physical sensor/actuator latency. Per-view literal/support counts are retained; predicates are not physical sensors."
        )
    for task in ("PickCube-v1", "PushCube-v1"):
        r = row(tables, task)
        s = row(tables, task, "DSRE_strict")
        tree = row(tables, task, "CART2_beta10")
        lines += [
            "",
            f"{task}: gated risk/strict/CART2.9 successful counts {r['successful']}/{s['successful']}/{tree['successful']} of{r['checkpoints']}. Risk mode includes{r['maintained_success']} initially successful completions and{r['required_recovery_success']} required recoveries. Risk minus CART: {effect(results['paired_intervals'][f'{task}|DSRE_risk-CART2_beta10|all']['successful'])}. Ordinary matches or superior outcomes constrain any superiority claim. More completion is not automatically more recovered failures.",
        ]
    lines += [
        "",
        "## Reproduction and preservation",
        "",
        "Protocol: docs/DSRE_FINAL_SPRINT_PREREGISTRATION.md; sources/inputs: confirmation_freeze.json; qualification: qualification_seal.json. Immutable prior calibration link and failed-parent exclusion are explicit. Source/data hashes and exact Git commit are in completion_manifest.json.",
        "",
        f"Read-only verification: `PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_final_finish.py --root {root} --stage verify`.",
        "",
        f"Recompute raw numerical and corruption audits in scratch space without physics or writes to sealed evidence: `PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_final_finish.py --root {root} --stage reproduce`.",
        "",
        "Tests: `PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -q tests`; maintained-source lint/format: `UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff check src scripts tests` and `ruff format --check src scripts tests`. Physics is never rerun in a sealed root. No push, publication or submission.",
    ]
    Path("docs/DSRE_FINAL_OPERATIONAL_RESULTS.md").write_text("\n".join(lines) + "\n")
    robustness_report(root)
    review(root, results)
    print(
        {"reports_updated": True, "complete_parents": results["complete_parents"]},
        flush=True,
    )


def robustness_report(root):
    lines = [
        "# DSRE: registered observation sensitivity, witnesses and breadth",
        "",
        f"Evidence: `{root}`. Same frozen observations and actual paired outcomes; no detector, new skill or sensor deployment.",
        "",
        "Noise repetitions are averaged within parent before 4000 parent-bootstrap draws. Conditions/repetitions are not independent parents. Every fixed grid point is retained. Clean statistical eligibility does not transfer to corrupted packets. UNKNOWN is never known false. Factual contradictions are retrospective comparisons with clean telemetry, not an online fault detector.",
        "",
        "| Population | Task/method | Scenario | Effective N / parents | Good% [95%] | Bad% [95%] | Defer% [95%] | Action instability% [95%] | Contradicted-fact proposal% [95%] |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    def ci(v):
        if v is None:
            return "NOT ESTIMABLE"
        lo, hi = v["parent_percentile95"]
        return f"{100 * v['value']:.2f} [{100 * lo:.2f},{100 * hi:.2f}]"

    for name in ("historical", "heldout"):
        v = read(root / f"{name}_robustness.json")
        for key, x in v["parent_intervals"].items():
            task, method, mode, scenario, pop = key.split("|")
            if (
                mode != "proposal"
                or pop != "all"
                or method
                not in (
                    "DSRE_strict",
                    "DSRE_risk",
                    "B7_risk",
                    "CART2_beta10",
                    "B5_beta10",
                    "B0_continue",
                    "B0_recover",
                )
            ):
                continue
            lines.append(
                f"| {v['population']} | {task}/{method} | {scenario} | {x['effective_checkpoints']:.1f}/{x['parents']} | {ci(x.get('successful'))} | {ci(x.get('unacceptable'))} | {ci(x.get('deferred'))} | {ci(x.get('action_unstable'))} | {ci(x.get('false_confidence'))} |"
            )
    lines += [
        "",
        "Full17-method, both-mode, threshold-proximity and separate replicate results are in historical_robustness.json/heldout_robustness.json and their referenced prediction records. Action instability uses the action appropriate to the mode; certificate instability concerns proposed facts. Noise families aggregate all three exact registered replicates, never a favorable one. Empty proximity subgroups are NOT ESTIMABLE. Proposals/gates do not change physical outcomes or controller input streams.",
        "",
        "## Grounded insufficiency and adequacy examples",
        "",
    ]
    for case in read(root / "physical_examples.json")["cases"]:
        lines += [
            f"- Case {case['case']}: `{case['id']}`, source `{case['source']}`, SHA256 `{case['source_sha256']}`; paired outcomes {case['outcomes']}. "
            + case.get("overlap", case.get("limit", ""))
        ]
    lines += [
        "",
        "A/B share six facts and differ in the registered left-of-goal predicate; B remains neither-success. C is both-success and initially successful. D/E share all 12 facts with opposing adequate actions: the existing Boolean menu cannot separate them, while raw poses differ. F has only one independent compatible parent under the registered full 12-fact scope and also neither-success: support and repertoire obstructions overlap. G has no exact signature in an original inspected cross-fit reference, yet a supported broader pure rule chooses inadequate continue. G is not mislabeled as an emitted reference-insufficiency obstruction. Finite diagnostics cannot discover every unrepresented adverse state. No extra controller, predicate, failure condition or hypothesis is introduced.",
        "",
        "The preserved finite frontier remains Pick183->235/422 at one added predicate, all six248/422; Push0through all budgets. These full-reference masses differ from held-out success. The old333-parent result remains145->187/332 strict Pick successes, mostly maintenance and only one extra required recovery. No historical result is overwritten.",
        "",
        "## Optional third task",
        "",
    ]
    breadth = read(root / "breadth_feasibility.json")
    lines += [
        breadth["conclusion"],
        "",
        f"Inventory time: {breadth['wall_seconds']:.2f}s (<=60min). New third-task physics: {breadth['new_physics_seconds']}s. Source inventory/hashes are in breadth_feasibility.json. No task selected for favorable DSRE performance, new controller or invented failure.",
    ]
    Path("docs/DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md").write_text(
        "\n".join(line.rstrip() for line in lines) + "\n"
    )


def review(root, results):
    pick = row(results["tables"], "PickCube-v1")
    push = row(results["tables"], "PushCube-v1")
    pick_effect = effect(
        results["paired_intervals"]["PickCube-v1|DSRE_risk-DSRE_strict|all"][
            "successful"
        ]
    )
    content = f"""# DSRE final evidence: adversarial scientific review

Evidence: `{root}`. This is an independent same-session numerical implementation
and adversarial review, not external human peer review. The registered 159-parent
postmortem continuation completed {results["complete_parents"]}/{results["planned_parents"]}.

## What the completed test actually establishes

Pick's gated risk tier completes {pick["successful"]}/{pick["checkpoints"]},
{pick_effect} relative to strict DSRE. All 30 additional successes maintain
already-successful starts; neither policy realizes a required Pick recovery.
Push completes {push["successful"]}/{push["checkpoints"]}, including
{push["required_recovery_success"]} required recoveries and one inadequate action.
The ordinary risk wrapper and calibrated CART1/CART2 match both operating points;
on Push, B5 and always-recover also match. These results support the distinction
between strict justification, risk eligibility and action quality, while providing
no evidence of controller or prediction superiority. The confidence intervals
describe the fixed seed-parent distribution, not general task diversity.

## Strongest scientific objections

1. **Established ordinary rules may fully explain the result.** B7 and the ordinary
strict-then-capped-risk wrapper are identical under shared grammar/ties. CART and
always-recover receive exactly the same calibration and information. If they match
or exceed DSRE, there is no algorithmic or physical-controller superiority. The
contribution is an executable robot-intervention information contract, checkable
obstructions and measured distinctions between skill success, observability,
statistical eligibility and completion credit. Pure rules, robust action intersection
and selective classification/risk control are established foundations.

2. **Operational scope and the recovery interpretation remain narrow.** Two simple
deterministic simulator tasks and idealized poses are not hardware safety or real
perception validation. Paired outcomes and selected resets are measured, but are
not independent repeats or a standalone end-to-end closed-loop deployment.
STOP scores zero even on already-successful checkpoints by the frozen contract;
that is autonomy credit, not evidence stopping physically destroys success.
Maintenance gains cannot be called new required recovery. A nearly constant Push
recover rule is an ordinary baseline result. Rare Pick recovery remains unqualified.

## Leakage, fairness and failure audit

The contaminated Pick8000180 is preserved/excluded, not replaced. The 159 remaining
parents were untouched at the new source/protocol freeze. This deviation is disclosed;
the study is not 160 pristine trials. P0 uses only inspected calibration states and
the original failed parent's offline witness. Both fixed actions and every frame,
model, memory, action equation and source identity are independently checked.
Calibration bytes, references, thresholds, tree nodes and all 17-family error budgets
are unchanged. Outcomes never enter PolicyInput. Tests do not update gates.

Parent-any-error CP eligibility is conditional on the fixed assignment process and
independent seed model; it is not checkpoint-weighted, arbitrary-time or shifted-sensor
safety. Test error counts are descriptive. Conditions and selected/noise repeats
cannot inflate N. Empty strata/subgroups are unestimated, not perfect safety.
All four actual outcome classes and strong baseline comparisons are in the main
results, including unfavorable comparisons. Full-signature has extra information;
policy-label fidelity is different from physical action adequacy.

The observation study preserves physical labels and the fixed grid. New-test shift
sensitivity is separate from inspected333-parent reanalysis. False facts against
clean telemetry are retrospective, not online detection; clean qualification does
not transfer. Reference support diagnostics do not detect all unseen adverse
outcomes: the preserved cross-fit caseG is explicitly an inadequate broad rule.

## Method, evidence and paper gates

**Method:** mathematically scoped and testable, with explicit established equivalences;
new solver/calibration theory is not claimed. **Evidence:** assess actual completion,
parity, baseline results, rare uncertified strata and breadth from the numerical
report. **Paper:** format and claim audit evidence is separate from significance.
The first page must present the intervention problem/product and the strongest
actual evidence, without implying human trust, hardware recovery or acceptance.
No publication readiness or guaranteed acceptance follows automatically.
"""
    Path("docs/DSRE_RSS2027_REVIEWER_CRITIQUE.md").write_text(content)
    Path("rss2027/CONTRIBUTIONS_AND_LIMITATIONS.md").write_text(
        "# DSRE contribution and boundaries\n\n"
        + content.split("## What the completed test actually establishes")[1].split(
            "## Strongest scientific objections"
        )[0]
        + content.split("## Method, evidence and paper gates")[1]
        + f"\nExact operational results: docs/DSRE_FINAL_OPERATIONAL_RESULTS.md; evidence `{root}`.\n"
    )
    ledger = Path("rss2027/CLAIM_EVIDENCE_LEDGER.md")
    heading = "\n## Final postmortem-qualified159-parent continuation\n"
    previous = ledger.read_text().split(heading)[0]
    entries = [
        heading,
        f"Evidence: `{root}`. Original873556b campaign remains sealed, including0/160test and failed8000180.\n",
        "| Claim | Exact source/scope |",
        "|---|---|",
        f"| {results['complete_parents']}/{results['planned_parents']} untouched parents, {results['checkpoints']} primary checkpoints | fresh_seed_manifest.json, atomic parent_progress, missingness.json;79Pick/80Push maximum, original contaminated parent excluded. |",
        "| Live preflight, unchanged controller/physics and repaired representation | qualification_results.json/seal, source_repair.json, independent full-frame verifier and mutation tests. |",
        "| Original calibration unchanged | calibration_link.json, identical decision/seal bytes,136 exact bounds; rare strata remain disabled. |",
        "| All 17 same-gate methods and primary paired uncertainty | operational_results.json, test_records.json, final_audit.json:numerical; parent resampling4000draws, original seeds. |",
        "| Selected repeats validate the same-parent estimator | independent_audit.json, selected decision/execution hashes and all-frame equality; no independent N added. |",
        "| Same twelve observation scenarios, old/new populations separate | historical_robustness.json, heldout_robustness.json; parent CI, no calibration transfer. |",
        "| Physical cases A--G and finite frontier | physical_examples.json raw source hashes; F support/repertoire overlap, G broad-rule generalization failure; historical frontier unchanged. |",
        "| Third-task status | breadth_feasibility.json, read-only source gate, no favorable task search or new controllers. |",
    ]
    ledger.write_text(previous + "\n".join(entries) + "\n")
    old = Path("docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md")
    heading = "\n## Separately qualified final-evidence continuation\n"
    prior = old.read_text().split(heading)[0]
    old.write_text(
        prior
        + heading
        + f"\nThe historical operational campaign above remains unchanged. A newly preregistered postmortem continuation uses identical calibration and excludes the already attempted parent. It completed {results['complete_parents']}/{results['planned_parents']} untouched parents. See [DSRE_FINAL_OPERATIONAL_RESULTS.md](DSRE_FINAL_OPERATIONAL_RESULTS.md) and [DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md](DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md), with exact evidence `{root}`. No old result is silently replaced.\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    write(parser.parse_args().root)
