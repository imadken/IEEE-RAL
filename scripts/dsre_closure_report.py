"""E6 claim-to-source ledger and the six requested scientific handoff reports."""

import argparse
import json
from pathlib import Path

from dsre_closure_common import ROOT, TASKS, read, sha

LABELS = {
    "harm_only": "O1 harm-only",
    "completion": "O2 absolute success",
    "useful": "O3 useful recovery",
}


def table(header, rows):
    return (
        "| "
        + " | ".join(header)
        + " |\n|"
        + "|".join("---" for _ in header)
        + "|\n"
        + "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in rows)
        + "\n"
    )


def main(docs):
    docs.mkdir(parents=True, exist_ok=True)
    frozen = read(ROOT / "E1/calibration_freeze.json")
    policies = read(ROOT / "E1/obligation_results.json")["tasks"]
    source = read(ROOT / "E2/source_curves.json")
    baseline = read(ROOT / "E3/full_certificate_audit.json")
    read(ROOT / "E4/physical_witnesses_and_ablations.json")
    noise = read(ROOT / "E5/observation_error_sensitivity.json")
    math = read(ROOT / "E0/math_audit.json")
    read(ROOT / "E0/raw_integrity_and_insertion_boundary.json")
    checkpoints = read(ROOT / "E0/checkpoint_and_parent_identity_audit.json")
    recount = read(ROOT / "E0/recount/independent_numbers.json")
    resources = read(ROOT / "run_complete.json")
    registration = read(ROOT / "registration.json")

    def write(name, text):
        p = docs / name
        p.write_text(text.rstrip() + "\n")

    def artifact(name):
        return str(ROOT / name)

    outcomes = []
    leaves = []
    examples = []
    certificate_rows = []
    for task in TASKS:
        t = frozen["tasks"][task]
        for obligation, label in LABELS.items():
            m = policies[task][obligation]
            length = (
                "none qualified"
                if not m["certificate_lengths"]
                else ", ".join(
                    f"{k} literals: {v} parents"
                    for k, v in m["certificate_lengths"].items()
                )
            )
            outcomes.append(
                [
                    task,
                    label,
                    m["recover"],
                    m["rescue"],
                    m["harm"],
                    m["futile"],
                    m["redundant"],
                    f"{m['completion']}/{m['parents']}",
                    length,
                ]
            )
            q = next(
                (
                    q
                    for q in t["queries"]
                    if q["obligation"] == obligation and q["output"]["certificate"]
                ),
                None,
            )
            examples.append(
                [
                    task,
                    label,
                    json.dumps(q["output"]["certificate"]["evidence"])
                    if q
                    else "NO CERTIFICATE (not an empty conjunction)",
                    q["output"]["certificate"]["selected_leaf_scope"] if q else "none",
                ]
            )
        for cell, e in t["model"]["leaves"].items():
            b = e["bounds"]
            leaves.append(
                [
                    task,
                    cell,
                    *e["counts"][:2],
                    f"{e['evidence']['p0']['lo']:.12f}",
                    f"{e['evidence']['p0']['hi']:.12f}",
                    f"{e['evidence']['p1']['lo']:.12f}",
                    f"{e['evidence']['p1']['hi']:.12f}",
                    f"{b['harm_upper']:.12f}",
                    f"{b['gain_lower']:.12f}",
                    *[
                        "pass"
                        if int(cell) in t["checks"][o]["approved_leaves"]
                        else "withhold"
                        for o in LABELS
                    ],
                ]
            )
        cases = baseline["tasks"][task]["cases"]
        certificate_rows.append(
            [
                task,
                len(baseline["tasks"][task]["sampling"]["selected_parent_ids"]),
                len(cases),
                sum(c["DSRE_B7_full_equivalence"] for c in cases),
                sum(c["DSRE_frozen_CART_full_equivalence"] for c in cases),
                sum(
                    c["DSRE"]["action"] == c["CART_frozen_gain_prefilter"]["action"]
                    for c in cases
                ),
            ]
        )
    outcomes_table = table(
        [
            "Task",
            "Obligation",
            "R",
            "Rescue",
            "Harm",
            "Futile",
            "Redundant",
            "Completion",
            "Minimum support on selected parents",
        ],
        outcomes,
    )
    leaf_table = table(
        [
            "Task",
            "Leaf",
            "n0",
            "n1",
            "L0",
            "U0",
            "L1",
            "U1",
            "H_U",
            "G_L",
            "O1",
            "O2",
            "O3",
        ],
        leaves,
    )
    root_note = f"Scientific authority: the complete user-supplied closure contract (18 November 2026). Start commit `{registration['base_commit']}`; branch `{registration['branch']}`. All results are read-only audits or explicitly retrospective analyses. Zero new physics/controllers; no manuscript or final-figure edit. Final source artifacts: `{ROOT}`.\n"
    write(
        "DSRE_STAGE1_OBLIGATION_CONTRAST_RESULTS.md",
        f"""# Obligation comparison: fixed facts, actions and calibration

{root_note}
The original 128 discovery / 1024 one-action calibration / 256 test parents are separate in each task. O1 requires H_U<=.10; O2 requires L1>=.90; O3 requires H_U<=.10 and G_L>=.05. The C-only process freezes all rules before this offline oracle scoring. All three obligations were already specified in the scientific contract; the completed secondary policy comparison is a **post hoc obligation contrast**, not a new prospective trial. Each secondary action is scored on an actually executed native branch from the same qualified checkpoint. It is not an additional deployment or an imputed counterfactual.

{outcomes_table}
{table(["Task", "Obligation", "Minimum E", "Whole-cell S"], examples)}
## Exact regional support

{leaf_table}
Full precision, all five four-cell extrema and parent support lists: `{artifact("E1/calibration_freeze.json")}`. The independent CDF inversion and four-variable LP agree with the original production bounds; no sample/threshold or discovery tree changes. Pick uses K=4 (tail .0015625); Push K=2 (tail .003125). Each tail is .025/(4K); the separate paired reserve remains .025. All three obligations are deterministic functions of the SAME simultaneous interval event, so they do not consume that family budget three times. No joint95 claim across tasks/methods/source budgets follows.

## Interpretation and nontriviality

Pick absolute success has **no qualified recovery**, not a zero-literal success certificate: the default continue macro is measured and is not certified successful. Harm-only and useful recovery require the same one literal under this grammar. Push O1/O2 permit the empty conjunction over both cells. Useful recovery needs `hand_object_near_04=False`, excluding cell 1 whose gain upper bound is below .05. The broader weak-obligation policy has recorded harms and redundant interventions; zero-literal support is not universal individual safety.

Deleting each retained grasp literal admits cells 2/3, whose harm/gain constraints fail; deleting the useful push literal admits cell 1. Per-case removal records include the exact admitted cells, parent support, bounds and feasible model witnesses at `{artifact("E3/full_certificate_audit.json")}`. Splitting any calibrated leaf is disallowed. UNKNOWN is never false.

Minimum means minimum **within the frozen, all-compatible-leaves-qualified grammar**. Whole-leaf componentwise qualification is sufficient, not universally necessary for an average obligation on a fixed-weight union. The checked analytical two-cell example has gains 1 and 0; its half-and-half union has gain .5 and harm 0 although one cell fails useful recovery. Thus the reported one-literal requirement is not a universal theorem that every valid pooled-region analysis needs that observation. No controller/optimizer novelty follows from the contrast.

All instrumented B7/direct-ID/obligation-gated trees have identical outputs. The original CART additionally vetoes discovery cells lacking empirical gain; this is retained as a distinct, stronger preference in the policy JSON. In particular a harm-only objective and a harm-plus-gain proposal filter need not recommend the same intervention. No comparison advantage is manufactured by hiding this distinction.
""",
    )
    curves = []
    for r in source["results"]:
        curves.append(
            [
                r["task"],
                r["panel"],
                r["source"],
                r["budget"],
                r["parents_required"],
                ", ".join(f"{LABELS[o]}: {r['qualified_leaves'][o]}" for o in LABELS)
                if r["supported"]
                else "UNSUPPORTED: insufficient distinct parents in this fixed source pool",
            ]
        )
    write(
        "DSRE_STAGE1_IDENTIFICATION_SOURCE_AUDIT.md",
        f"""# Intervention evidence and identification audit

{root_note}
For q=(q00,q01,q10,q11), p0=q10+q11, p1=q01+q11, harm=q10 and gain=q01-q10. Nonnegativity gives the established sharp range max(0,p0-p1)<=h<=min(p0,1-p1). The code independently checks {math["exact_marginal_cases"]} exact marginal pairs, {math["paired_refinement_cases"]} valid paired intersections, and binomial confidence containment regressions. Maximum numerical discrepancy is {math["maximum_error"]:.3g}. These are classical identification facts, not new DSRE theorems.

**ANALYTICAL WORLDS, not robot episodes:** (.4,.2,0,.4) and (0,.6,.4,0) both have p0=.4,p1=.6,g=.2, with h=0 and.4. A narrow confidence rectangle alone is not a structural nonidentification proof. The actual constructive witness fixes both marginals and has two admissible joints. At exact marginals O3 holds for all joints iff gain>=.05 and (p0<=.10 or p1>=.90). At finite marginals H_U=min(U0,1-L1), G_L=L1-U0. L0>.10 and U1<.90 means every allowed marginal pair still admits excessive harm; it does not by itself prove a favorable paired joint exists. Explicit favorable/unfavorable models are required when claiming unresolved verdicts.

## Equal visible-outcome cost, without fictitious new samples

{table(["Task", "Panel", "Source", "Logical action outcomes", "Parents needed", "Qualification"], curves)}
The predeclared parent order and virtual arm masks are in registration.json. Both task pools contain 256 fully qualified paired original-test parents (512 previously collected action outcomes). Each L view exposes one hash-selected label per parent; each P view exposes both labels, costs two, and uses the original marginal-plus-harm/rescue constraint engine. These L views are **masked retrospective development views**, not genuinely randomized newly executed logs. The actual prospective 1024-parent C logs are audited separately. No source-curve policy is scored on the same pool and called an independent test.

The shared-parent panel is a dependent paired comparison across methods. The disjoint panel assigns the first 128 hash-ordered parents to L and the rest to P, with no substitution. Both exclude discovery parents. Within a paired block, first-label marginals and joint constraints intentionally share parents; Bonferroni allows this event dependence. Paired outcomes are never counted as two independent parents. The per-view error allocation is fixed; curves are descriptive, without a simultaneous best-budget/source guarantee.

Every fit runs in a separate Python process with only its own partition and its L or P packet whitelisted. Source-scope, duplicate-parent and propensity checks fail closed. Original evaluator traces and other source-view files are inaccessible to the L estimator. The materializer is explicitly evaluator-authorized; it does not fit a rule. New physics=0. Logical exposed-outcome costs are not claims that only that many historical native branches were collected: the complete pool cost is512 per domain, plus its recorded prefix/source overhead.

At matched supported shared-pool costs, grasp has no qualification at 128 or 256 in either view; push qualifies the same useful cell at 256 in both. Paired 512 has no matched 512-log view in this fixed paired pool, and 1024 is unsupported here. This says nothing about global absence of genuine 1024-log evidence: that primary C cohort exists and qualifies the reported main rules. Do not promote an unmatched or masked point into an acquisition win.

The separately registered prospective grasp acquisition comparison remains an important stronger control: all-logs, all-pairs, uniform mixture, witness-guided and decision-uncertainty allocation tie at 512 base + 512 added visible outcomes. It is reconstructed in E0/recount. No physical confidence-qualified region requiring pairing was established. Sampling uncertainty can shrink with more labels; identical exact marginals can remain structurally ambiguous; missing observations and failed checkpoints are different failures. Confounded logs, unknown propensity or failed replay supply no positive causal certificate. Pairing describes a checked deterministic simulator coupling, not an observed hardware joint potential outcome.

The conditional causal estimands assume consistency, no interference, exchangeability/overlap, independent regional sampling and stationarity. Source code verifies outcome-blind hash assignments and disjoint IDs/fresh native histories, not a theorem that deterministic seed/hash sequences are iid random variables. The whole-cell statement is sufficient, not universal necessity. Actual source and guard hashes are in claims_to_sources.json.
""",
    )
    write(
        "DSRE_STAGE1_CERTIFICATE_BASELINE_AUDIT.md",
        f"""# Complete-certificate matched baseline audit

{root_note}
Decision: **CERTIFICATE_EQUIVALENCE** for DSRE versus B7 equipped with identical bounds, region definitions, tie breaks and witness postprocessing. Method originality decision: **FUNCTIONAL_EQUIVALENCE_TO_INSTRUMENTED_RULES**. The shared capability is source-/obligation-/scope-aware justification; no uniquely novel exact rule solver or witness algorithm is demonstrated.

{table(["Task", "Actual sampled parents", "Parent-obligation cases", "Full B7 equal", "Full original gain-prefilter CART equal", "Original CART actions equal"], certificate_rows)}
The C-only exhaustive check covers all 729 ternary queries per obligation/task (including every UNKNOWN pattern), or 4374 complete output comparisons. Production DSRE uses per-query subset enumeration; the independent B7 implementation enumerates the whole ternary rule library and checks its complete Boolean match set. Equality covers evidence literals, whole-cell S, D/source assumptions, o, confidence bounds, removal W and withholding reasons, with numerical agreement independently checked before canonical comparison. Direct-ID and the obligation-gated fixed tree receive exactly the same processor and produce the same complete outputs. These are accurately labeled augmentations: the historical uninstrumented baselines originally returned actions, not a unique explanation interface.

Selection is outcome-neutral: up to 24 actual primary-qualified and 24 primary-withheld parents/task, stratified across recorded reason codes, hash-selected without replacing unavailable strata. An isolated selector reads sanitized X/parent/qualification/reason packets with **no outcome or explanation fields**; only afterward are full tuples examined. Exact selection manifests and access whitelists are under E3. This is algorithmic separation, not a claim that an analyst had never seen these historically inspected experiments.

The original CART includes a discovery empirical-gain proposal filter in addition to the common risk gate. Its extra withholding reason can differ even when the final action matches. Under weaker O1/O2 it can also veto recoveries that the requested obligation allows. We preserve both that historical policy and an explicitly obligation-matched gate-only tree control; we do not rename the original policy or hide differences. Such differences reflect objectives/instrumentation, not a newly superior DSRE solver.

Every retained literal is checked by deleting it and reporting the admitted disallowed whole cells or forbidden split, their original independent C support and their bounds. Full source/evidence assumptions are linked through the unchanged source scope and the audit ledger. All baseline processors use zero extra evidence units. Measured C-only timing totals are in E1/calibration_freeze.json and per-task E3 output; B7 library-construction time is included separately. They are tiny-dictionary engineering measurements, not a runtime or sensing-efficiency claim.

Four insufficiency mechanisms remain distinct and may overlap: physical same-X opposing unique-success actions; actual neither-success fixed-macro executions; retrospectively hash-thinned physical C outcomes whose plugin passes while confidence fails; and explicit same-marginal analytical joint worlds. Bound optimizers with different marginals are not mislabeled a nonidentification witness. Withholding has no implication that the fallback continue action is successful or physically safe.
""",
    )
    noise_rows = []
    for task, rows in noise["tasks"].items():
        for r in rows:
            m = r["metrics"]
            noise_rows.append(
                [
                    task,
                    r["radius_mm"],
                    f"{r['invariant_literals']}/{r['possible_literals']}",
                    r["ambiguous_whole_leaf_memberships"],
                    m["recover"],
                    m["rescue"],
                    m["harm"],
                    m["futile"],
                    m["completion"],
                ]
            )
    formal = "SUPPORTED"
    write(
        "DSRE_STAGE1_FINAL_SCIENCE_CLOSURE.md",
        f"""# Final scientific-evidence closure

{root_note}
## Two separate decisions

**Formal/data integrity: {
            formal
        }, conditional on the explicitly declared sampling/causal/source assumptions.** Original parent identities, native endpoints, control equations, calibrated bounds, scopes and minimum rules reproduce. This is not an unconditional physical-safety or sim-to-real guarantee.

**Method originality: FUNCTIONAL_EQUIVALENCE_TO_INSTRUMENTED_RULES.** Complete B7 with the same bound/scope/witness processor is equivalent, not merely action-equivalent. No unique solver, witness algorithm, control-performance or acquisition-efficiency advantage is established. The evidence-sufficiency question and its physical obligation contrast are demonstrated as a shared methodological capability. External novelty/acceptance remains a reviewer judgment.

{
            table(
                ["Question", "Claim/evidence", "Scientific status"],
                [
                    [
                        "RQ1 obligations",
                        "Same C, fixed regions and macros; O1/O2/O3 change valid support and recorded intervention consequences",
                        "SUPPORTED within the registered cellwise grammar",
                    ],
                    [
                        "RQ2 evidence source",
                        "Sharp bounds and same-marginal analytical worlds; actual one-arm qualification; bounded masked and registered acquisition comparisons",
                        "Analytical limit SUPPORTED; necessary physical pairing advantage OPEN / NOT ESTABLISHED",
                    ],
                    [
                        "RQ3 unique certificate algorithm",
                        "Full independent B7 plus identical source/witness processing matches",
                        "Unique solver/witness advantage REFUTED in this matched setting; functional equivalence established",
                    ],
                    [
                        "RQ4 breadth / measurement",
                        "Two calibrated manipulation sources; navigation no-rescue boundary, insertion uncalibrated pilot, retrospective error-box sensitivity",
                        "LIMITED; broad task, measurement-shift and hardware transfer remain OPEN",
                    ],
                ],
            )
        }
## Recomputed intervention outcomes

{outcomes_table}
These are offline scores on actually recorded paired native branches. Primary deployed-policy counts and all other frozen baselines are independently reconstructed in E0; secondary contrasts remain post hoc. The strong fixed-action controls remain visible: pushing always-recover nearly matches the selected policy, while grasping fixed recovery harms successful continuations. Equivalent rules receive equal credit.

Zero observed primary harms are finite samples, not proof of zero risk. On selected recoveries, the separately reported descriptive two-sided CP95 harm intervals are {
            recount["results"]["PickCube-v1"]["methods"]["DSRE"][
                "observed_harm_two_sided_CP95"
            ]
        } for Pick and {
            recount["results"]["PushCube-v1"]["methods"]["DSRE"][
                "observed_harm_two_sided_CP95"
            ]
        } for Push. These are different estimands from the independently calibrated regional obligation and are not a joint confidence statement over all comparisons. Whole-region calibration support and exact endpoints are in the obligation report.

## What the guarantee and minimum actually say

Conditional on the independent discovery partition and the stated binomial/stationary source population, all marginal endpoints contain their targets on one simultaneous event. Max-H/min-G qualification of every complete routed leaf implies the same inequalities for any mixture preserving those within-leaf distributions. It does not authorize arbitrary feature-conditioned subcells, measurement-dependent sub-selection, or individual safety. Cardinality minimum is exact among conjunctions constant on whole cells whose every admitted leaf qualifies. The analytical fixed-weight pooled-union counterexample proves this restriction is sufficient, not universally necessary. No new identification theorem is claimed.

E0 independently checks source selection on 1408 parents/task: Pick's native missed-lift/drop trigger (including its privileged simulator grasp flag) or90-control cap, and Push's fixed53-control boundary; native source histories are distinct and replayed alternatives agree. IDs, seeds, process reconstruction and source hashes support the experimental protocol. Exchangeability, iid regional sampling and stationarity remain substantive assumptions; uniqueness does not prove them. Simulator pairing is an experimental model coupling, not a hardware counterfactual.

## Physical, analytical and missing-evidence witnesses

Physical observation-aliasing and both-failure witnesses have original native source paths, specs, parent IDs and original-gzip SHA links under E4. Analytical joint worlds and scope countermodels are separately labeled under E0/math_audit.json. Fixed-hash C downsampling demonstrates current finite confidence insufficiency without changing an outcome. UNKNOWN/missing-arm ablations fail closed; a missing label is never relabeled failure. Naive independence is an explicitly invalid causal assumption: equal observed physical actions in these populations do not validate its unobserved-joint premise.

{
            table(
                [
                    "Task",
                    "Radius mm",
                    "Invariant facts",
                    "Ambiguous memberships",
                    "R",
                    "Rescue",
                    "Harm",
                    "Futile",
                    "Done",
                ],
                noise_rows,
            )
        }
At radius 0 the original facts and main actions reproduce. Larger hypothetical coordinate boxes preserve asserted factual truth but can collapse intervention coverage. These are **retrospective sensitivity consequences**, not measured physical sensor-noise performance and not transferred risk certificates. Exact finger encoders and fresh supporting frames are assumptions. Recalibration under a fixed altered measurement protocol is required for a risk claim.

## Boundary and feasibility reconciliation

{
            table(
                ["Source", "Registered / actual", "Interpretation"],
                [
                    [
                        "PickCube",
                        "D128/C1024/T256 valid",
                        "Positive useful recovery with independent original calibration",
                    ],
                    [
                        "PushCube",
                        "D128/C1024/T256 valid",
                        "Positive useful recovery; nearly optimal fixed recovery",
                    ],
                    [
                        "Navigation",
                        "D128; C1013/1024; T255/256 eligible",
                        "11 C +1 T observed successful prefixes, not failures; zero recover-only eligible outcomes",
                    ],
                    [
                        "Old insertion",
                        "D128; C0/1024 outcomes; T0/256 decisions",
                        "Retired source-blocked cohort; no restart and no fabricated outcomes",
                    ],
                    [
                        "New insertion pilot",
                        "48/48 qualified; 0/96 conditional confirmation activated",
                        "25 recover-only,22 neither,1 both,0 continue-only; action-diversity failure; no risk-calibrated third task",
                    ],
                ],
            )
        }
The original zero-control planner failure and its two isolated historical reproductions remain source failures with no executable checkpoint/outcome. The later nonzero-prefix guard is retained, not broadened away. The pilot's post-checkpoint observed stopped endpoint is retained. No contact-task confirmation or three-domain success is manufactured.

## Stage 1 decision and exact limits

Publication-defensible now: conditional four-cell/source mathematics with classical attribution; frozen-cell scope soundness; exact grammar minimum; actual useful one-arm recovery in two simulated mechanisms; the obligation-support/intervention contrast; complete instrumented-rule equivalence; and explicit negative/boundary evidence. A claim of a uniquely novel optimizer/certificate/witness algorithm, a measured intrinsic pairing advantage, source-independent safety, or calibrated third-task generality would be unsupported and is a methodological blocker **to that stronger claim**.

No reproduced numerical or data-integrity blocker prevents presenting the narrower Stage1 question and evidence. The current artifact should next be revised by the supervisor to incorporate this closure and its restrictions; no manuscript is edited here. The V4 editorial zip/risk register/latest separate methodology-first blueprint were not present. They are UNVERIFIED editorial inputs, not silently replaced by an older manuscript. Thus this is not unconditional conformance approval of an unseen V4 package or a guarantee of RSS acceptance.

All execution details, exact code/source hashes, tests, preservation, compact reproduction and final local commit are in the closure receipts and the remaining handoff reports. The next phase is final manuscript revision, not another unbounded campaign.

## Reproduction and resources

The finalized ordered E0–E5 run passed {resources["steps"]} phases in {
            resources["wall_seconds"]:.2f} wall seconds and {
            resources[
                "child_cpu_seconds"
            ]:.2f} child CPU seconds. Its cumulative wall time from the initial preservation inventory was {
            resources[
                "cumulative_contract_wall_seconds"
            ]:.2f} seconds at completion, below 12h. Further report/test/reproduction costs are charged in the final preservation/resource receipt. New physics and controller training are both zero; output size is checked against 2GiB. New audit code failures (wrong historical C path and an overly broad prototype source whitelist) were corrected before the final run; superseded development outputs are preserved separately. No final scientific/source qualification check was made to pass by changing outcomes.

Run from the repository root with the original sealed local data present:

```bash
UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-sync python scripts/dsre_closure_reproduce.py --verify
UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-sync python scripts/dsre_closure_reproduce.py --full --output /tmp/dsre-closure-independent-reproduction
UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-sync pytest -q tests
UV_CACHE_DIR=/tmp/dsre-evidence-uv uv run --no-sync ruff check scripts/dsre_closure_*.py tests/test_dsre_closure.py
```

The full command requires a fresh output directory, repeats the offline audits in isolated processes and compares scientific outputs; timestamps, timings and relocation-dependent file hashes are excluded from deterministic equality. Compact archive validation alone checks transfer integrity and does not replace access to the original native source seals. Commands, exit codes, test totals and original-preservation hashes are sealed under research/dsre_experimental_closure; no public push or submission is authorized. Unrestricted repository-wide pytest collection failed because archived third-party suites under results/ parse unrelated CLI flags at import; its log is preserved separately. The maintained suite is tests/, as explicitly used above. This collection issue is not hidden as a successful scientific check.
""",
    )
    write("DSRE_STAGE1_RSS_REVIEWER_RISKS.md", risk_report(root_note))
    write("DSRE_STAGE2_FEASIBLE_EXPERIMENT_MATRIX.md", stage2_report(root_note))
    claims = {}
    source_sets = {}
    for task in TASKS:
        m = frozen["tasks"][task]["model"]
        checks = checkpoints["tasks"][task]["checks"]
        source_sets[task] = {
            "science_commit": "d917a69d47f3102123030eaf565f4623dad86525",
            "local_start": registration["base_commit"],
            "independent_parent_ids": {
                phase: [c["parent_id"] for c in checks if c["phase"] == phase]
                for phase in ("discovery", "calibration", "test")
            },
            "native_source_records": checks,
            "source_scope": m["source_scope"],
            "learner_visible_fields": [
                "parent_id (grouping only)",
                "X",
                "A",
                "propensity=.5",
                "Y_A",
                "controls",
                "cost",
                "source_scope",
            ],
            "forbidden_policy_features": [
                "seed",
                "condition identity",
                "native grasp/contact flag",
                "unexecuted future",
            ],
            "calibration_parent_ids_by_cell": {
                c: v["parent_ids"] for c, v in m["leaves"].items()
            },
            "original_evaluator_only_branches": [
                c["native"]
                .replace("selected_policy.json.gz", "evaluator_counterpart.json.gz")
                .replace("selected.json.gz", "evaluator.json.gz")
                for c in checks
                if c["phase"] == "test"
            ],
            "independence_assessment": {
                "verified": "Distinct IDs/seeds/fresh physical histories and disjoint splits",
                "declared": "iid conditional sampling, exchangeability, no interference, consistency and stationarity",
            },
        }
        for obligation, mets in policies[task].items():
            for field in (
                "parents",
                "recover",
                "rescue",
                "harm",
                "futile",
                "redundant",
                "completion",
            ):
                claims[f"{task}.{obligation}.{field}"] = {
                    "value": mets[field],
                    "source_set": task,
                    "original_native_seals": [
                        str(p)
                        for p in [
                            Path(
                                "results/dsre-evidence-aware/20261117-prospective/raw_evidence_seal.json"
                            ),
                            Path(
                                "results/dsre-evidence-aware/20261118-final-science/raw_evidence_seal.json"
                            ),
                        ]
                    ],
                    "recomputed_artifact": artifact("E1/obligation_results.json"),
                    "role": "Original-primary or post-hoc secondary scoring; never new prospective confirmation",
                }
        for c, v in m["leaves"].items():
            for field, value in v["bounds"].items():
                if field == "optimizers":
                    continue
                claims[f"{task}.cell{c}.{field}"] = {
                    "value": value,
                    "source_set": task,
                    "calibration_sample": v["parent_ids"],
                    "tail": v["tail"],
                    "recomputed_artifact": artifact("E1/calibration_freeze.json"),
                }
        original = recount["results"][task]
        rows = original["paired_test"]
        for field, value in {
            "four_cell_counts": original["four_cells"],
            "hindsight_completion_ceiling": sum(r["yc"] or r["yr"] for r in rows),
            "unselected_rescues": sum(
                not r["yc"] and r["yr"] and r["actions"]["DSRE"] != "r" for r in rows
            ),
            "all_frozen_baseline_metrics": original["methods"],
            "all_frozen_baseline_action_agreement": original["action_agreement"],
            "source_signature_diagnostics": original["signature_diagnostics"],
            "actual_learner_and_evaluator_budgets": original["budget"],
            "source_arm_support": original["support"],
        }.items():
            claims[f"{task}.{field}"] = {
                "value": value,
                "source_set": task,
                "recomputed_artifact": artifact("E0/recount/independent_numbers.json"),
                "primary_native_sources": "source_sets native_source_records and original_evaluator_only_branches",
            }
    original_hashes = {}
    for p in ROOT.rglob("*.json"):
        if p.name in ("claims_to_sources.json", "raw_output_seal.json"):
            continue
        obj = json.loads(p.read_text())
        if isinstance(obj, dict):
            original_hashes.update(obj.get("input_sha256", {}))
    methods = {
        "sharp_harm_bounds": {
            "basis": "Classical four-cell/Fréchet algebra; Kallus NeurIPS2022",
            "proof": artifact("E0/math_audit.json"),
        },
        "scoped_soundness": {
            "basis": "Simultaneous containment and whole-cell mixtures, with within-cell distributions preserved",
            "sufficient_not_universally_necessary": True,
        },
        "minimum": {
            "basis": "Exhaustive fixed grammar; independently enumerated B7 ternary rule library",
            "global_information_necessity": False,
        },
        "analytical_worlds": {
            "q": [[0.4, 0.2, 0, 0.4], [0, 0.6, 0.4, 0]],
            "robot_episodes": False,
        },
        "confidence": {
            "delta_L": 0.025,
            "delta_P": 0.025,
            "tail_formula": ".025/(4K)",
            "no_cross_task_method_budget_joint95": True,
        },
        "source_trigger": {
            "file": "scripts/overnight_pick.py",
            "native_grasp_flag_is_policy_input": False,
            "source_audit": artifact("E0/checkpoint_and_parent_identity_audit.json"),
        },
        "geometry_thresholds": {
            "source": "src/dual_rec/dsre/features.py",
            "macro_sources": [
                "src/dual_rec/overnight_pick.py",
                "scripts/overnight_replay.py",
            ],
            "horizon_controls": 70,
            "control_period_seconds": 0.05,
        },
        "boundary_counts": {
            "proof": artifact("E0/raw_integrity_and_insertion_boundary.json")
        },
        "full_B7_equivalence": {
            "proof": artifact("E3/full_certificate_audit.json"),
            "claim": "No unique minimum-rule or witness algorithm",
        },
        "V4_editorial_inputs": {
            "status": "UNVERIFIED_UNAVAILABLE",
            "items": registration["absent_editorial_inputs"],
        },
    }
    ledger = {
        "authority": registration,
        "claims": claims,
        "mathematical_and_source_claims": methods,
        "source_sets": source_sets,
        "original_input_sha256": original_hashes,
        "analysis_code_sha256": {
            str(p): sha(p) for p in sorted(Path("scripts").glob("dsre_closure_*.py"))
        },
        "formal_data_integrity": formal,
        "method_originality": "FUNCTIONAL_EQUIVALENCE_TO_INSTRUMENTED_RULES",
        "preservation_inventory": "research/dsre_experimental_closure/preservation_before.json",
    }
    manuscript = Path("rss2027/dsre_stage1.tex")
    ledger["frozen_manuscript_claim_provenance"] = {
        "file": str(manuscript),
        "sha256": sha(manuscript),
        "edited": False,
        "source_tables": {
            str(p): sha(p) for p in Path("rss2027/stage1_evidence").glob("*.tex")
        },
        "numerical_and_formal_line_index": [
            {
                "line": i,
                "text": line,
                "source_sets": list(TASKS),
                "numerical_claims": "claims entries; all_frozen_baseline_metrics, exact leaf bounds and source support",
                "mathematical_claims": "mathematical_and_source_claims; E0 math and E1 independent exhaustive oracle",
                "source_protocol": "Original input hashes, native traces and checkpoint/controller audits",
                "limits": "Citations/editorial numbers are not new experimental observations; historical full-paper manuscript remains separately preserved",
            }
            for i, line in enumerate(manuscript.read_text().splitlines(), 1)
            if any(c.isdigit() for c in line) and not line.startswith("%")
        ],
    }
    (ROOT / "claims_to_sources.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(
        "Wrote six scientific reports and claims_to_sources.json",
        len(claims),
        "quantitative claims",
    )


def risk_report(note):
    return f"""# Ranked scientific reviewer objections

{note}
These are evidence-based internal objections, not fabricated external reviews or acceptance scores. Ranking reflects threat to the current claim, not advice to hide unfavorable evidence.

| Rank | Hard objection | Evidence / unresolved limit | Correct claim and response |
|---|---|---|---|
| 1 | Ordinary fully instrumented rules do exactly this. | E1 exhaustive production/B7 match and E3 full tuples. | Report FUNCTIONAL_EQUIVALENCE_TO_INSTRUMENTED_RULES. The shared recovery-evidence question is operationalized; no unique rule/witness solver is established. |
| 2 | Minimum facts are being sold as a universal necessity theorem. | Whole-cell sufficiency proof plus the checked fixed-weight pooled-union counterexample. | Say minimum within the frozen all-leaves-qualified grammar. Broader valid pooled/subgroup inference would need its own justified target/confidence construction. |
| 3 | Hash-assigned simulator parents do not prove causal exchangeability or iid sampling. | Distinct native histories and source implementation verified; stochastic assumptions remain declared. | State conditional guarantees and the exact fixed source population. Do not assert source hashes prove independence or sim-to-real transfer. |
| 4 | Secondary obligations were evaluated after inspecting the test. | Deterministic C-only freezes and original predeclared targets; secondary analysis performed now. | Label post hoc obligation contrasts on measured paired endpoints. Do not call them new untouched confirmation or tune policies on T. |
| 5 | Pushing always-recover is already nearly optimal. | Full baseline/native counts retained. | No meaningful superiority claim; report harm, redundancy and equal70-control horizons without inventing energy savings. |
| 6 | The claimed physical identification gap is only a synthetic example. | Same-marginal analytical worlds are valid; no confidence-qualified physical pairing necessity established. | Separate analytical identifiability from robot-source findings. Leave physical pairing necessity open. |
| 7 | Masked source curves are not genuinely randomized new logs, and some budgets are missing. | E2 source packets, pool size, isolated process reads and unsupported endpoints. | Label retrospective masks and both logical/sunk costs. Keep the registered1024-cost acquisition tie; do not promote unmatched 512 P into a win. |
| 8 | Robust facts do not preserve calibrated risk under selection/shift. | E5 declared-box invariance plus large coverage loss. | Report descriptive consequences only; fresh protocol-specific calibration is required. UNKNOWN is not false, and unchanged continue is not certified safe. |
| 9 | The simulator checkpoint/controller uses privileged state. | Native grasp trigger and full-prefix/controller audits explicitly identify source information. | Simulator-qualified recovery evidence only. No claim that a physical robot has the same trigger or perfect pose inputs. |
| 10 | Insertion/navigation do not establish broad recovery generality. | Insertion diversity failure/retired C0-T0; navigation zero-rescue/absorbing prefixes. | Two positive simulated manipulation mechanisms; boundary/feasibility evidence remains negative and separately denominated. |
| 11 | Confidence is overclaimed across tasks, views or algorithms. | Registered .025/(4K) endpoints and paired reserve. | One fixed family; same-event obligations may share it, but source/budget/task/model comparisons are not a joint95 success guarantee. Test harm intervals are different estimands. |
| 12 | An unseen V4 methodology package might contain additional unsupported claims. | The requested V4 zip/risk register/separate blueprint are unavailable locally. | This audit covers visible frozen sources and the supplied closure contract; V4 editorial conformance is UNVERIFIED. Review that input before final manuscript signoff. |

Additional correctable implementation issues encountered in this closure were confined to new audit code: historical C records live in per-parent learner files, not an aggregate file; and an initial source-view prototype allowed multiple source packets in one process. Final source fits are isolated per view and tested against counterpart access. Development outputs are retained, marked superseded, and no original outcome, source, threshold or seal changed. An unrestricted pytest invocation also collected archived third-party tests and failed at import/CLI parsing; the explicit maintained tests/ suite is reported separately. Final tests and reproduction receipts distinguish corrected software checks from genuine historical source failures.

Next action: the supervisor revises the manuscript around this scientifically limited evidence package, complete baseline equivalence and conditional scope. No extra experiment or rhetorical deletion of adverse evidence is needed to complete this closure. Acceptance is not guaranteed.
"""


def stage2_report(note):
    return f"""# Feasible, falsifiable Stage2 experiment matrix

{note}
These are future, separately authorized protocols, not executed work or a Stage2 manuscript. No real-robot access is established. DSRE's actions, tolerances, source semantics and scientific question remain fixed; do not seek a new optimizer or alter an already failed task after outcomes. Estimates use recorded branch times, not promised throughput.

| Open hypothesis | Fixed design / estimand | Prerequisites and independent samples | Outcome budget and forecast | Null interpretation / honest fallback |
|---|---|---|---|---|
| RQ2: pairing helps at equal outcome cost, possibly through an identification rather than sample gap | Choose existing Pick or Push before data; compare genuine one-action L with uniformly paired P under the same discovery partition and O1/O2/O3. Estimands: qualified recovery mass, harm/gain bounds, completion and source-only coverage at equal1024-outcome calibration cost. To claim structural necessity, require both a qualified paired cell and a same-marginal obstruction, not merely a wider L interval. | Reverify4 source parents with two macros/two repeats (16 executions); common fresh D128. Independent C_L1024 one-arm parents, C_P512 paired parents, common untouched T256 paired evaluator; source/parent pools distinct and chosen before outcomes. Freeze all views/thresholds before C, and calibration before T. | 16+128+1024+1024+512=2704 macros. Grasp at8.148s about6.12 worker-hours; conservative10s pushing allowance about7.51h. Cap one chosen task at10 worker-hours and3GiB, charging prefixes/startup. | Equality/no paired-only cell is a valid result, not permission to change tasks or faults. Baseline instrumented B7 remains equivalent. Any observed gap must distinguish finite support from intrinsic nonidentification. |
| RQ4: measured support remains useful under a declared observation-error protocol | One primary5mm coordinate-box protocol on an existing manipulation source;10mm secondary descriptive only unless separately allocated. Estimands: invariant factual truth, UNKNOWN/unrouteable mass, actual whole-region qualification, rescue/harm/futility/completion. Controller inputs and macros unchanged; only the explanatory observation protocol is tested. | Fixed measurement/selection protocol and fresh D128/C1024/T256. Missingness must be represented in the target population before C; no borrowing clean bounds on a narrower all-known subgroup. Same parent perturbation replicas are dependent, not extra samples. Exact encoders/fresh supporting frames remain explicit assumptions. | 16 source checks+128+1024+512=1680 macros: about3.80h grasp or4.67h at10s push. Cap7 worker-hours/2GiB including startup and screening. Paired test outcomes can be shared across pre-frozen observation comparators. | Coverage collapse or zero qualification falsifies useful transfer under that protocol. Report no guarantee if scope support fails. Do not add a new sensor/controller or claim hardware-noise performance from hypothetical boxes. |
| RQ4: the existing contact source can support informative action diversity and independent calibration | One fresh96-parent paired Peg diagnostic under the unchanged source, with all native failures retained. Estimands: executable checkpoint probability, q00/q01/q10/q11 conditional on it, source attrition and action/planning cost. Only a separately fixed eligibility/diversity pass may activate a full cohort. | Original48 pilot and blocked1024/256 remain historical. No repeat-until-success. Reverify source; aperture UNKNOWN. Conditional new D128/C1024/T256 must be disjoint from the diagnostic and all history. No alternative task is selected after seeing the gate. | Diagnostic192+16=208 macros at20.723s about1.20h; cap2h. Conditional full study1664 more outcomes about9.58h, cap12h. Combined future cap14h, with a new explicit authorization. | Zero continue-only diversity is evidence of a source/repertoire boundary. No calibrated third-task claim follows. Stop at that negative result and retain two-task scope; do not reopen old IDs or substitute favorable seeds. |

Every future registry must collision-check fixed seeds against all original manifests before collection, record independent task draws and assignment/propensities before outcomes, preserve the exact confidence allocation, measure actual costs, and stop at whole-parent atomic boundaries. Each option is an alternative bounded scope, not additive authority under this session's12-hour/zero-physics ceiling.

RQ3's proposed unique-rule-solver advantage is already contradicted by complete instrumented B7 equivalence; no future experiment should be designed to manufacture a distinction by withholding equivalent postprocessing. The open question is how much the shared evidence-sufficiency capability warrants under new, fixed sources. Broad hardware transfer remains unpromised pending actual access and a separately qualified protocol.
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    main(parser.parse_args().docs_dir)
