"""Outcome-neutral scientific handoff from the sealed native pilot and audit."""

import json
from pathlib import Path

from rpd_pilot_common import BASE, sha, write_json


def reports():
    summary = json.loads((BASE / "final_audit/summary.json").read_text())
    source_review = json.loads((BASE / "source_review/source_review.json").read_text())
    assert summary["audit_passed"] and summary["decision"] == "SOURCE_NOT_QUALIFIED"
    lines = [
        "# RPD fixed physical feasibility pilot: actual outcomes",
        "",
        "19 November 2026. **Verdict: SOURCE_NOT_QUALIFIED.** Both native workers",
        "terminated with exit139 (SIGSEGV convention) on the39th planned branch of",
        "parent0. Each returned38 complete native traces; neither reached a neutral",
        "hold. The source-failure stop rule was applied to both families. The original",
        "ten-parent lists remain unchanged; these are incomplete pilots, not smaller",
        "completed cohorts. No source repair, resumed physics or seed replacement followed.",
        "",
        "## Exact attempted, returned and missing counts",
        "",
        "| Task | Registered parents | Attempted parents | Complete qualified parents | Planned episodes | Started | Returned complete | Interrupted, outcome unknown | Unattempted | Missing terminal labels |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for task, r in summary["tasks"].items():
        c = r["counts"]
        lines.append(
            f"| {task} |10|{r['attempted_parents']}|{r['complete_qualified_parents']}|540|{c['attempted']}|{c['complete']}|{c['interrupted_missing_outcome']}|{c['unattempted']}|{c['missing_terminal_labels']}|"
        )
    lines += [
        "",
        "Across tasks:78 started episodes,76 returned complete traces,2 interrupted",
        "unknown outcomes,1,002 unattempted episodes. All1,004 missing terminal labels",
        "remain missing. Independent parent exposure is one per family, not38; zero",
        "complete qualified parents and zero eligible matched-hold contrasts exist.",
        "",
        "The authoritative ledger is `final_audit/summary.json` and its complete",
        "1,080-row `all_registered_rows.jsonl`. The frozen preliminary trace auditor",
        "counts only38 returned files/task and has no worker finalizer after SIGSEGV.",
        "Its `attempted=38`, `failed=0`, `worker_wall_seconds=0` fields are NOT the",
        "campaign counts or resource measurements. The journal-based forensic audit",
        "explicitly supersedes those fields; there was one interrupted attempt/task.",
        "All76 returned complete paths passed the separate sampled geometric allowed-set",
        "checks at all11,400 recorded boundaries. This supplies no contact-force or",
        "continuous-time safety guarantee and does not establish option preservation.",
        "",
    ]
    for task, r in summary["tasks"].items():
        lines += [
            f"## {task}: all ten fixed parent slots",
            "",
            "| Index | Seed | Parent ID prefix | Started | Complete | Interrupted unknown | Unattempted | Source disposition |",
            "|---:|---:|---|---:|---:|---:|---:|---|",
        ]
        for p in r["parents"]:
            c = p["counts"]
            disposition = (
                "Native worker failure; parent incomplete"
                if c["attempted"]
                else "Not attempted after family source guard"
            )
            lines.append(
                f"|{p['parent']['index']}|{p['parent']['seed']}|`{p['parent']['parent_id'][:16]}`|{c['attempted']}|{c['complete']}|{c['interrupted_missing_outcome']}|{c['unattempted']}|{disposition}|"
            )
        lines += [
            "",
            "The manifest and canonical row ledger retain the full parent IDs. Returned",
            f"prefix, native clock, controller memory and full repeated paths passed for {r['successful_repeat_checks']} pairs.",
            "This validates those returned traces; it does not qualify the unfinished family.",
            "",
            "### Actual terminal outcomes of exposed parent0",
            "",
            "Each cell is actual macro-end/common-deadline success for repeat0. Its",
            "paired repeat1 agrees on every returned path. STOP has no macro endpoint.",
            "MISSING means no returned outcome; it does not mean task failure.",
            "",
            "| History | Continue @70/@90 | Recover @70/@90 | STOP @90 |",
            "|---|---|---|---|",
        ]
        for h in r["history_endpoint_counts_repeat0"]:
            cells = []
            for e in ("continue", "recover", "STOP"):
                c = h["endpoints"][e]
                if not c["returned_repeat0_parents"]:
                    cells.append("MISSING")
                elif e == "STOP":
                    cells.append(str(c["native_deadline_successes"]))
                else:
                    cells.append(
                        f"{c['native_macro_end_successes']}/{c['native_deadline_successes']}"
                    )
            lines.append(
                "|"
                + (" → ".join(h["history"]) or "empty")
                + "|"
                + "|".join(cells)
                + "|"
            )
        lines += [
            "",
            "@70 denotes70 macro controls after history; absolute post-checkpoint time is",
            "history_delay+70. @90 is the common post-checkpoint deadline. All returned",
            "macro success labels happened to agree at both endpoints; no absorbing",
            "success assumption or early success stop was used.",
            "",
            "### Native contact, motion and allowed observations",
            "",
            "These are actual evaluator measurements from the continue/repeat0 branch",
            "of the sole exposed parent. They are descriptive and are not matched-time",
            "causal effects or independent population samples. Contact counts refer to",
            "native robot/object manifold points at20Hz; object motion is evaluator-only.",
            "The stricter active-contact audit separately requires native nonpositive point",
            "separation or nonzero solver impulse. Positive-gap zero-impulse manifolds are",
            "proximity-only, despite the legacy robot_object_contact boolean being true.",
            "",
            "| History | Manifold ticks | Active-contact ticks | Root active contact | Object displacement (mm) | TCP displacement (mm) | Sampled probe path allowed |",
            "|---|---:|---:|---|---:|---:|---|",
        ]
        for e in sorted(
            r["known_probe_effects"], key=lambda e: (len(e["history"]), e["history"])
        ):
            active = next(
                h
                for h in source_review["tasks"][task]["histories"]
                if list(h["history"]) == list(e["history"])
            )
            lines.append(
                f"|{' → '.join(e['history'])}|{e['contact_tick_count']}/{e['probe_delay_ticks']}|{active['active_contact_tick_count']}/{e['probe_delay_ticks']}|{active['root_active_contact_evidence']}|{e['object_displacement_m'] * 1000:.6f}|{e['tcp_displacement_m'] * 1000:.6f}|{e['sampled_probe_allowed']}|"
            )
        lines += [
            "",
            "Active contact occurs in some recorded histories; the source-review table",
            "distinguishes active contact, release of existing contact and proximity-only",
            "motion. A nonzero command or object displacement alone does not establish",
            "a diagnostic contact mechanism. No-contact/zero-impulse cases remain visible.",
            "They are neither synthetic truth labels nor a purely analytical example.",
            "However, their difference from neutral waiting is UNKNOWN. All sampled",
            "geometry, including full prefix/suffix and adverse-frame lists, is available",
            "in `independent_trace_audit/case_checks.json`. There is no force/damage,",
            "hardware or continuous-time safety guarantee.",
            "",
            "### Option preservation, erasure, creation and sensor information",
            "",
            "**K_hold=UNKNOWN; matched K_probe/K_hold contrasts=0 eligible.** Erasure,",
            "creation, loss/preservation of one successful macro, and their frequencies",
            "relative to equal-duration waiting are **NOT ESTIMABLE**, not zero.",
            "Immediate no-probe completion is not a valid substitute for neutral10/20.",
            "All60 planned parent/history matched contrasts per family remain unqualified.",
            "",
            "Actual native arm qpos/qvel, FK TCP response and clock were recorded for",
            "every returned probe tick. Their frozen response bins are stored per raw",
            "trace and independently reproduced. Only one root parent was exposed, so",
            "variation of the evaluator-only hidden pose label at fixed root observations",
            "cannot be assessed across parents. No decoder, held-out predictive gain,",
            "information ranking or Shannon-information claim was fitted to this pilot.",
            "",
        ]
    lines += [
        "## Unfavorable and unresolved findings",
        "",
        "PickCube's release-containing histories can fail fixed continue while the",
        "observed recover branch succeeds. This is an actual *history-conditional*",
        "terminal distinction for one parent, not full option erasure; the uncollected",
        "matched holds prevent attributing it to contact beyond elapsed time. PushCube",
        "returned continue/recover branches succeed for the same exposed parent.",
        "Repeated release/lateral-sweep recover and STOP, all neutral controls, and",
        "all nine later parents per task are unobserved. Missing labels are not filled.",
        "",
        "Both native processes failed after38 complete episodes on their39th start.",
        "No final trace, native backtrace or exact intra-episode stage was returned.",
        "The failed planned row is recover/repeat0 after two release_settle probes",
        "(Pick) or two lateral_sweep probes (Push). It is not known whether its",
        "checkpoint, probes or macro were reached. The repeated episode/environment",
        "lifetime topology is a possible engineering contributor, not an established",
        "root cause. The raw worker callsgc.collect only after a full parent; no",
        "process-isolation repair or extra diagnostic physics was authorized by the",
        "sealed failure path and none was run.",
        "",
        "## Resource accounting",
        "",
        "| Task | Returned native controls | Sum measured completed episode wall(s) | Conservative whole-worker upper bound(s) | Raw/journal bytes |",
        "|---|---:|---:|---:|---:|",
    ]
    for task, r in summary["tasks"].items():
        lines.append(
            f"|{task}|{r['known_native_controls']}|{r['measured_completed_episode_wall_seconds']:.6f}|{r['conservative_total_worker_wall_upper_seconds']:.6f}|{r['raw_compressed_bytes']}|"
        )
    lines += [
        "",
        "The hard cap was10,800worker seconds/task and3GiB compressed/task. Bounds",
        "start at the console's filesystem birth before worker launch and end at a",
        "post-exit observation; they conservatively include time after process death.",
        "They are NOT precise runtime measurements. Native finalizers did not run,",
        "so exact total worker CPU/wall time and peak memory are unavailable. The",
        "completed-episode wall sums are measured. The unreturned39th episode has",
        "unknown native control count between0 and155(Pick)/143(Push). Source failure,",
        "rather than a budget ceiling, stopped collection. No full Stage2 parent was",
        "collected; every original discovery/calibration/test reservation is untouched.",
        "",
        "## Reproduction and evidence",
        "",
        "The SHA-256 raw/canonical manifests, original prephysics source/seed seal,",
        "both native-exit receipts, all1,080 canonical planned rows, source review,",
        "test receipts and compact archive are in `research/rpd_physical_pilot_20261119/`.",
        "Reproduction is offline only; do not restart a native worker after this guard.",
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.",
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1",
        "uv run --no-sync python scripts/rpd_pilot_reproduce.py --verify",
        "uv run --no-sync python scripts/rpd_pilot_reproduce.py --audit --output /tmp/rpd-pilot-review",
        "uv run --no-sync pytest -q tests",
        "```",
        "",
        "Use a fresh audit directory. The local Git commit anchors the package.",
        "No manuscript, historical seal, native source or user change is modified.",
        "",
    ]
    Path("docs/RPD_PHYSICAL_PILOT_OUTCOMES.md").write_text("\n".join(lines))
    gate = """# RPD Stage 1 empirical hypothesis gate

19 November 2026. **Physical feasibility verdict: SOURCE_NOT_QUALIFIED.**
The two fixed ten-parent pilots were attempted under the prephysics neutral-hold
amendment and stopped after native SIGSEGV source failures. Each task has one
partially exposed parent,38 returned complete branches, one interrupted branch,
zero complete qualified parents, and no neutral-hold outcomes. The independent
trace audit passes for the returned evidence. A passing evidence audit does not
turn an unfinished source into a qualified physical experiment.

## Scientific disposition and exact claim boundary

| Question | Status | Evidence and admissible wording |
|---|---|---|
| Do the registered commands physically contact/move the nominated object? | LIMITED actual physical support | Active contact is observed for the exposed Pick lift/Push forward-tap histories; other histories contain proximity-only manifolds or release existing root contact. Native object/TCP motion alone is not proof of contact-mediated effect beyond waiting |
| H1: does a diagnostic contact probe erase recovery options beyond matched waiting while sampled geometry remains allowed? | OPEN / SOURCE-BLOCKED | No neutral10/20 outcomes returned; no eligible paired contrast. Neither a positive finding nor a null-frequency claim is justified |
| H2: does probe response improve held-out hidden-state prediction, possibly changing intervention selection? | OPEN / UNTESTED | One exposed parent/task cannot supply an independent discovery/test comparison. No decoder trained; original64 discovery slots untouched |
| H3: can transition, observation, repertoire and checkpoint limits explain model failures? | LIMITED engineering finding | Native collection fails on39th start in both workers, exact intra-episode stage/root cause unknown. No finite-model mismatch/impossibility theorem follows |
| Is RPD a distinct strong/POMDP planner? | VALID_KNOWN_FORMULATION, unchanged | Prior6,688 same-input value agreements and toy consensus equality remain preserved. No new planner comparison or novelty follows from these partial robot traces |

Physical allowed-set adherence and recovery feasibility remain distinct. Native
sampled20Hz geometry is separately audited and does not establish force, damage,
continuous-time or hardware safety. No calibrated post-probe success predicate,
population risk guarantee, physical impossibility or prevalence estimate exists.

The separate active-contact source review corrects the naive interpretation of
legacy `robot_object_contact`: native cached points can have positive separation
and zero impulse. The strict evaluator review records nonpositive separation or
nonzero solver impulse, without inventing a force sensor or changing eligibility.
In the exposed parent both tasks have active root contact. Single release_settle
and lateral_sweep have zero active-contact probe ticks after the root; this is
contact release/proximity evidence, not proof of a continued contact mechanism.
The initial unsealed handoff and the correction are preserved in a development
archive; all raw traces, frozen acquisition code and original seals are unchanged.

The complete raw terminal rows support narrow simulator descriptions. For example,
fixed continue after release can fail for the exposed Pick parent while recorded
recover succeeds. Comparing this with immediate continuation confounds probe
mechanics with elapsed time; missing neutral holds prohibit the primary inference.
No analytical world is relabelled a robot episode. No missing native outcome is
reconstructed from the finite truth table or a favorable matched baseline.

## Methodology and novelty boundary

The audited prior methods already include safe active diagnosis(s-FEAST),
decision-aware contact probing with physical object motion(DA-GRD), conditional
planning, reach-avoid belief planning and recoverability-aware control. See the
full source-qualified nearest-work matrix in the preserved
`RPD_METHODOLOGY_ORIGINALITY_CHALLENGE.md`. This pilot neither reproduces their
published experiments nor establishes superiority over them.

Same-input full-model strong/POMDP planning is an equivalent positive control;
task consensus is a strong comparator. Standard entropy and a transition-blind
ablation may test consequences of ignoring a physical model, but the latter is
deliberately misspecified. No algorithm novelty is claimed. The candidate robotics
contribution would be an empirical estimand and carefully matched experiment for
contact-associated loss of a previously successful fixed terminal macro repertoire.
This pilot has **not** established that matched phenomenon.

## Remaining precise work, without authorization to execute it

The campaign stops here. Author/supervisor must choose between the empirical RPD
hypothesis manuscript and the preserved DSRE V5. No current manuscript is changed.
The empirical route has a source qualification blocker; returning to a stronger
solver, favorable task/seed, sensor or fault distribution would not resolve it.

If the supervisor later chooses a separately authorized source qualification,
first register a process-isolation hypothesis, preserving the exact native
versions, controls and failed seeds. A minimal diagnostic micro-protocol is the
same interrupted recover row in two fresh OS processes per task(4episodes), then
neutral10/20 ×continue/recover/STOP ×two repeats at the same already-inspected
parent0(24episodes). Total28 existing-parent technical episodes, no new independent
parents, no confirmation claim. Cap20worker minutes/task and100MiB/task, count all
starts and failures. Prove source/controller/clock/prefix equivalence, no
within-history reset, and repeat parity. Native crashes fail this micro-protocol;
do not repair or switch tasks again within it. A process boundary change is a
future engineering hypothesis, not a root cause established by today's evidence.
Even a successful micro-protocol would not complete the original10-parent pilot.

Before any main study, full original technical source qualification must then be
completed under a new explicit source charter. The original remaining counts
are501 unattempted episodes plus one interrupted unknown/task, with nine untouched
parents each. No full campaign is launched by this document. Existing native
startup/episode costs do not measure fresh-process overhead, so the diagnostic
budget is a bounded feasibility gate, not a throughput guarantee.

## Conditional feasible paired Stage 2 measurement design

This design is inactive and supersedes none of the old frozen protocol files.
It follows the supervisor's new empirical disposition, rather than the old
six-policy-by-four-region calibration plan. Once source-qualified, freeze two
registered10-tick probes, the10-tick hold, unchanged70-tick macros and common90
deadline. Retain the same task/checkpoint; do not select more favorable parents.

Use64 independent discovery parents and a disjoint, untouched256-parent eligible
test cohort/task, with a predeclared original-seed list and maximum attempts.
Report original-seed and eligible-checkpoint denominators, all failures/missingness,
and incomplete-cohort counts. Baseline/history branches share a parent cluster.
Preregister eligibility before probing; post-probe failures/geometry violations
are retained as adverse results. Prove seed disjointness and source fingerprints.

Primary data: each parent has three histories(probe1,probe2,hold10) ×two fixed
macros, six evaluator-only fresh-prefix episodes.64+256 parents require1,920
episodes/task. A fixed16-test-parent replay audit adds96episodes/task, total2,016.
No physical-state restore occurs within an episode; all alternatives are isolated
evaluation counterfactuals, never learner observations. Identical macro endpoint,
deadline, sensors and action budgets apply. Prespecify optional STOP/no-probe
controls with their extra costs before opening test; none is silently included
in this base cost.16 technical repeats are correlated checks, not independent N.

For each test parent/probe record erasure, creation, lost/gained macro membership,
sampled geometry, contacts, object motion and terminal completion. The primary
estimand is the independent-parent probability of matched option erasure, with
per-task and prespecified pooled estimates. A candidate minimum relevant effect
is the preserved.05 threshold; finalize discovery-only precision/power and the
multiplicity rule BEFORE test outcomes, retaining the fixed testN or explicitly
declaring insufficient power. A four-way family(probe ×task) could allocate.05/4
to one-sided exact parent-binomial bounds. Secondary paired differences and H2/H3
need their own preregistered multiplicity allocation; do not recycle the old
eight-endpoint confidence claim or assert simultaneous scope without allocation.
Report conservative missing-outcome bounds before any complete-case inference.

H2 requires a decoder trained only on discovery, a root-only comparator, fixed
allowed root/probe channels and evaluator-only diagnostic labels. Compare
untouched-parent prediction accuracy, labelled a predictive proxy, not automatic
Shannon information or causal information gain. If the root signature/label does
not vary or generalize, retain that observability limitation instead of choosing
a new sensor or label after test. No predictive claim is supported by today'sN1.

An optional contingent execution demonstration needs a discovery-frozen empirical
model, source-miss criteria and identical observations/data/action budgets for
full-model strong/POMDP, one-step consensus, entropy and the labelled misspecified
transition-blind control. Share identical policies' executions and retain equality.
No new planner advantage or universal calibratedG follows from the paired terminal
measurement study. Any fresh statistical success authorization needs its own
independent fixed-policy calibration and may legitimately fail.

Conditional cost illustration only:2,016 times the observed completed-episode
average gives about84minutes(Pick) and56minutes(Push), excluding new-process
startup, storage, repeats of failures and model/audit work. **These are not feasible
source throughput promises:** today's process fails after38 episodes. The future
source gate must measure isolation throughput before setting a new bounded charter;
no58-hour or842-parent campaign is authorized. Unknown/negative/null outcomes are
valid: time explains the effect, probes lack predictive value, erasure is absent
or too rare to resolve, both macros fail, methods tie, or source remains blocked.

## Immediate handoff decision

Use the current result as a documented technical source blocker and narrowly
grounded contact/actuation observation. Do not put a matched contact-erasure result,
population frequency, calibrated success, or novel planning theorem into Stage1.
The RPD empirical question can remain an explicitly unverified, falsifiable
hypothesis. DSRE V5 and all its positive results and baseline equivalences remain
untouched for author choice. No RSS acceptance/invitation or submission is implied.
"""
    Path("docs/RPD_STAGE1_EMPIRICAL_HYPOTHESIS_GATE.md").write_text(gate)
    # Every manuscript-bearing statement is typed as actual, missing, or hypothetical.
    write_json(
        BASE / "claims_to_sources.json",
        {
            "source_commit": "b00c441ffa88924c157dda51b8e4deff3934566b",
            "decision": "SOURCE_NOT_QUALIFIED",
            "claims": [
                {
                    "id": "C1",
                    "kind": "ACTUAL_REGISTERED_PROTOCOL",
                    "claim": "20fixed parents,1080rows,90common deadline",
                    "sources": [
                        str(BASE / "prephysics_amendment.json"),
                        str(BASE / "replay_manifest.jsonl"),
                        str(BASE / "prephysics_seal.json"),
                    ],
                },
                {
                    "id": "C2",
                    "kind": "ACTUAL_MISSINGNESS",
                    "claim": "39starts38complete1interrupted501unattempted per family",
                    "sources": [
                        str(BASE / "final_audit/summary.json"),
                        str(BASE / "final_audit/all_registered_rows.jsonl"),
                        str(BASE / "native_process_exit_receipt.json"),
                    ],
                },
                {
                    "id": "C3",
                    "kind": "ACTUAL_TRACE_ONLY",
                    "claim": "76complete traces,38repeat pairs; native contacts/motion, known endpoints",
                    "sources": [
                        str(BASE / "independent_trace_audit/raw_manifest.json"),
                        str(BASE / "independent_trace_audit/case_checks.json"),
                        str(BASE / "final_audit/summary.json"),
                    ],
                },
                {
                    "id": "C4",
                    "kind": "UNKNOWN_NOT_ZERO",
                    "claim": "Matched erasure/creation and population/statistical claims unavailable: no neutral outcomes",
                    "sources": [
                        str(BASE / "final_audit/summary.json"),
                        str(BASE / "final_audit/all_registered_rows.jsonl"),
                    ],
                },
                {
                    "id": "C5",
                    "kind": "PRESERVED_PRIOR_ANALYTICAL_RESULT",
                    "claim": "Known strong/POMDP formulation; no new method originality",
                    "sources": [
                        "docs/RPD_METHODOLOGY_ORIGINALITY_CHALLENGE.md",
                        "research/rpd_method_challenge/final/finite/audit_summary.json",
                    ],
                },
                {
                    "id": "C6",
                    "kind": "INACTIVE_FUTURE_PROTOCOL_NOT_OBSERVED_RESULT",
                    "claim": "Stage2paired measurement and source-isolation micro-protocol require new authorization",
                    "sources": ["docs/RPD_STAGE1_EMPIRICAL_HYPOTHESIS_GATE.md"],
                },
                {
                    "id": "C7",
                    "kind": "RETROSPECTIVE_NATIVE_CONTACT_SEMANTICS_REVIEW",
                    "claim": "Proximity-only cached manifolds are not active contact; native separation/impulse evidence is reported separately, root contact included",
                    "sources": [str(BASE / "source_review/source_review.json")],
                },
            ],
            "sha256": {
                str(p): sha(p)
                for p in [
                    BASE / "prephysics_amendment.json",
                    BASE / "replay_manifest.jsonl",
                    BASE / "prephysics_seal.json",
                    BASE / "final_audit/summary.json",
                    BASE / "final_audit/all_registered_rows.jsonl",
                    BASE / "native_process_exit_receipt.json",
                    BASE / "independent_trace_audit/raw_manifest.json",
                    BASE / "independent_trace_audit/case_checks.json",
                    BASE / "source_review/source_review.json",
                    Path("docs/RPD_METHODOLOGY_ORIGINALITY_CHALLENGE.md"),
                    Path(
                        "research/rpd_method_challenge/final/finite/audit_summary.json"
                    ),
                    Path("docs/RPD_STAGE1_EMPIRICAL_HYPOTHESIS_GATE.md"),
                ]
            },
        },
    )


if __name__ == "__main__":
    reports()
