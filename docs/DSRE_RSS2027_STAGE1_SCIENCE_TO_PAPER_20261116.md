# DSRE RSS 2027: Science-to-Stage-1 Integration Contract

**Research supervisor's fixed instruction, 2026-11-16.**
**Repository:** `/home/imad/Desktop/IEEE-RAL`
**Scientific starting commit:** `e63848e2487ca59e7c66bdd4430614748ae1ece0`
**Source:** `results/dsre-operational/20261115T195007Z-science-v12`
**Research target:** RSS 2027 Stage 1 submission, December 4, 2026, 23:59 AoE.
**Submission format:** up to five pages of content and exactly one page of references; no supplementary material considered.

## Decision and objective

DSRE v1.2 has completed the essential physical-regime and measurement-robustness study. **Do not initiate another large physics or method-development campaign.** We now have sufficient evidence to build a serious, self-contained Stage 1 scientific argument. Update **only** the Stage 1 manuscript. The prior eight-page master is not a deliverable and must remain unchanged.

The fixed problem remains: *what is the minimum observable evidence sufficient to justify a recovery intervention with respect to physically measured alternative-action outcomes, and what prevents such justification when it is unavailable?*

We do not claim a novel hitting-set algorithm, superior recovery controller, distributed safety guarantee, or universally optimal sensing policy. The proposed scientific contribution is the **operational intervention-evidence methodology**: minimum justifications, counterexample-backed distinctions between action repertoire and observational limits, measurement-invariant evidence under bounded sensor error, and prospectively measured adequacy/abstention/recovery tradeoffs. Explain this positively as a research contribution, not as defensive disclaimers in the abstract.

## Evidence pins and numerical facts to verify from primary files

The independent untouched confirmation cohort contains **128 seed parents**, with five registered approach-target offsets per parent and **640 paired checkpoints**. All five conditions have physical replay/branch qualification. The 64 development parents and earlier studies remain separate. The five settings alter the scripted approach target, **not** the object pose or contact material.

The outcome classes are **69 continue-only, 239 recover-only, 284 both-success, and 48 neither-success**. **238** recover-only states are failed-start required recoveries; the remaining one is preventive. Every main rate must use the correct denominator and parent-group resampling.

* Nominal: 27 continue-only, 0 recover-only, 101 both-success, 0 neither-success.
* +3 cm: 0 continue-only, 108 recover-only, 0 both-success, 20 neither-success.
* Fixed recover: 523 successful, 117 inadequate; 69 harms on continue-only states. Fixed continue: 353 successful.
* Physical action feasibility: 592/640. Finite-table exact-feature common-action mass: six facts 206/640, seven facts 256/640, twelve facts 365/640. Full exact pose produces one-instance signatures and is a **hindsight overfitting diagnostic**, not an attainable generalization result.
* Frozen zero-radius **DSRE risk proposal**: 401 adequate, 2 inadequate, 237 STOP, 48/238 required recoveries selected. Ordinary B7 risk matches **exactly**. CART2 risk: 388 adequate, 1 inadequate, 251 STOP, 35/238 required recoveries. The +13 adequate difference is **2.03125 percentage points**; it comes with one additional inadequate action. No dominance or risk-certified advantage is established.
* Under a declared 5 mm absolute coordinate-wise input error box: robust DSRE risk proposal 368 adequate, 5 inadequate, 267 STOP, 15/238 selected required recoveries; all asserted invariant facts correct. Robust B7 remains exactly equivalent. An all-six/all-seven margin comparator or conservative tree can abstain more. Robust factual validity **does not** establish action safety.
* Under three fixed 5 mm corrupted-telemetry replicates, the point-based risk proposal asserts a total of **123 false facts among 1,953 asserted literals**; robust evidence asserts **0 false facts among 1,507 literals**, but incurs substantial recovery deferral and some inadequate decisions. These are **replicate totals, not independent parents**.
* Previously calibrated clean two-condition parent/action bounds **do not transfer** to the new five-condition or noisy source. Label every result on that source an **unqualified proposal**. No new risk gates were trained or transferred.

Primary sources to reopen and reproduce:
`docs/DSRE_STAGE1_SCIENCE_V12_METHOD.md`, `docs/DSRE_STAGE1_SCIENCE_V12_RESULTS.md`, `docs/DSRE_STAGE1_SCIENCE_V12_NOVELTY.md`, `docs/DSRE_STAGE1_SCIENCE_V12_GATE.md`, the sealed JSON/JSONL evidence under the v1.2 root, `docs/dsre_science_v12_review.tar.gz`, and the earlier `docs/DSRE_RSS2027_STAGE1_ADVERSARIAL_REVIEW.md` and RSS manuscript source. **Never copy a numerical claim without verifying its definition and provenance.**

## Workstream A: consolidate the actual scientific mechanism

1. Independent scrutiny of the five-arm paired-outcome and decision tables. Audit category totals, parent IDs, action adequacy, false-literal denominators, confidence intervals, and exact B7 equivalence. Recompute from the compact archive and refer to raw evidence where necessary. Keep the original results read-only.
2. Formalize three propositions under explicitly delimited assumptions:
   * A neither-success physical state cannot be made adequate by additional observations alone under a fixed action repertoire and horizon.
   * With a **fixed finite table**, refining the observed feature partition cannot decrease the number of rows whose signature class has a common adequate action; it can still leave a gap to physical action feasibility. Do not assert this for differently trained policies or wildcard query semantics.
   * An invariant measurement literal is correct across the declared input-error box; this does **not** imply the chosen action is adequate in the true state or outside the reference distribution.
   Include explicit short proofs or counterexamples. Identify all three as elementary properties used to clarify the scientific formulation, not first-ever mathematical discoveries.
3. Select **two deterministic real paired-state witness examples**: one set of observation-aliased states requiring conflicting actions; one state where both actions fail. Trace the examples to the physical source and confirm that the displayed feature values are genuinely predecision observable. Include a minimal certificate and its literal-removal witness from the existing solver where available.
4. Prepare an **action-feasibility vs observation-sufficiency vs proposal-coverage** schematic that never mixes same-table ceilings with deployed cross-fit recommendations.

## Workstream B: sharpen the novelty comparison without moving the target

Directly contrast DSRE's stated objective and evidence scope with:
* Khan et al., ICAPS 2009, minimal sufficient MDP explanations;
* DISCRET, ICML 2024, outcome-aware explanatory rules;
* Peddi and Bezzo, IROS 2023, decision-tree-based recovery;
* DA-GRD, 2026 preprint, decision-aware sensory disambiguation;
* RESCUE, 2026 preprint, matched intervention evaluation;
* Zhu and Leonard, Applied Sciences 2026, feasibility under partial observability;
* Ceder et al., 2026 preprint, counterfactually labeled recovery-tree distillation;
* Jiang et al., Artificial Intelligence 2024, interval robustness of counterfactual explanations.

Cite only directly necessary primary sources in the tight Stage 1 paper. Separate established prior techniques from our **robotic evidence contract and empirical mechanism separation**. Do not manufacture novelty, but also do not lead the paper with self-deprecating claims. Explicitly acknowledge mathematical identity to B7 and matched empirical performance when reporting results.

## Workstream C: revise only RSS Stage 1, based on completed science

Maintain `rss2027/dsre_stage1.tex`, its bibliography, and necessary figures; preserve current PDF/source as a dated archive first. Do not edit `dsre_full_paper_master.tex` or PDF.

Required five-page content flow (adapt layout as needed):
1. **Introduction / scientific phenomenon / hypotheses**: recover can be beneficial, harmful, or ineffective; observation sufficiency and intervention feasibility are different. State exactly what DSRE explains and evaluates.
2. **Formal problem**: paired-action adequacy; minimum observed evidence relative to the finite intervention model; typed insufficiency; confidence and measurement scopes. One formula for action-set intersection, one for bounded evidence.
3. **Method**: small exact certificate search, counterexample witnesses, measurement invariance, calibrated risk interface. Provide a legible minimal figure. State all scope limits mathematically once, not repeatedly in prose.
4. **Experiments**: preregistered 5-condition PickCube source, 128 untouched parents, paired outcomes, strong rules, CART, fixed controls, no hidden condition labels, parent grouping. Use outcome-class table and enough measurement detail to establish credibility without external appendix.
5. **Mechanism findings**: one compact diagram/figure for task regimes and information gap; one panel/table for robust literal validity vs decision adequacy and deferral; precise comparison including B7 equivalence and qualified/unqualified distinction. End with concise analysis and a realistic hypothesis-driven extension plan, not a second manuscript.
6. **References page**: exactly one page, verified real primary records, no hallucinated citations.

The RSS 2027 submission must be anonymously typeset using the official author kit, with no identifying URLs or metadata. Use only the provided official class without changing font size, margins or spacing. Review citation bibliographic accuracy and check final embedding, table legibility, and any copyright concerns. Stage 1 has no considered supplementary materials. **The abstract must focus on what the method formalizes and establishes.** Empirical qualifications belong with the relevant results, with no hiding of negative findings.

Avoid overclaiming the +2.03 percentage-point CART contrast as method superiority because it increases inadequate actions and lacks new-source risk certification. The strongest headline is the *separation of skill feasibility, observation-based justifiability and measurement truth*, backed by physically paired recoveries and harmful interventions.

## Workstream D: pre-submission hard-science review

Write one adversarial reviewer report evaluating:
A. Novelty relative to exact B7 and partial-observability feasibility;
B. Whether the five-arm source variation is meaningfully physical and ecologically bounded;
C. Whether the evidence demonstrates required recovery rather than only maintenance;
D. Whether measurement invariance is wrongly sold as action safety;
E. Whether all numerical comparisons are apples-to-apples and confidence intervals group parents;
F. Whether the scientific question and main mechanism are understandable without supplemental material;
G. RSS 2027 5+1 paper, anonymity, and citation requirements.

Fix text, figures and mistaken claims. Do not suppress a valid objection. Any material unresolved issue receives a precisely worded limitation or a targeted **next-experiment proposal**, not automatic authorization to run physics. Do not launch another architecture, controller, task family, calibration search, large seed campaign, or open-ended literature exploration. If the paper requires a new experiment that is genuinely indispensable before Stage 1, document its exact hypothesis, sample-size rationale and expected information value, and stop for supervisor review.

## Engineering and delivery contract

Starting head: `e63848e2487ca59e7c66bdd4430614748ae1ece0` on `research/dsre-rss2027-science-first-20261115`. Work on new local branch `research/dsre-rss2027-stage1-scientific-synthesis`. Inspect `git status` first; preserve every pre-existing user change, old evidence seal, `.gitignore`, `uv.lock` and old manuscript. Never rewrite raw historical observations.

Authorized: source/file review, offline recomputation, formal checks, manuscript/figure edits, TeX compilation and tests. **Zero new physics** and **zero new controller or model training**. Use independent verification scripts where possible. Write reproducible commands and a figure-source ledger. All numerical paper claims must link to audited source fields.

Deliver:
* Complete revised anonymous 5+1 RSS 2027 Stage 1 PDF and LaTeX sources;
* concise mathematical-method section with checked proofs and physical witnesses;
* scientific comparisons and figure-source ledger;
* full numerical/citation/formatting/anonymity checks;
* adversarial scientific-review report and remaining risks;
* local commit and source hash manifest.

Do not submit. Do not force-push. Do **not** publicly push the blinded manuscript without a separate anonymization and release-risk review; the public GitHub repository identifies its owner. Finish the complete authorized assignment without asking for intermediate approval. The researcher decides whether the Stage 1 submission has sufficient scientific strength.
