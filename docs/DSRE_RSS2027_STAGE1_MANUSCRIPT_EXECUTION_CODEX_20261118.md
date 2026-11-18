# Codex assignment: DSRE RSS 2027 Stage 1, final scientific manuscript

**Scientific direction fixed by supervisor, 18 November 2026. Codex implements; Codex does not choose research questions, change mathematical obligations, or decide venue novelty.**

Repo: `/home/imad/Desktop/IEEE-RAL`.
Latest LOCAL research result: `d917a69d47f3102123030eaf565f4623dad86525`.
Suggested local working branch: `research/dsre-rss2027-stage1-scientific-writing`.
Supervisor blueprint: `docs/DSRE_RSS2027_STAGE1_SCIENTIFIC_STORY_LOCK_20261118.md` from remote design branch `research/dsre-rss2027-stage1-story-20261118`.
Target paper: `rss2027/dsre_stage1.tex` and its compiled PDF. **Do not touch the full-length/Stage 2 manuscript.**

## 0. Absolute instruction: the science is locked

The prospective experiments are complete for Stage 1. NO new physics, datasets, controllers, model training, alternate recovery policies, new acquisition strategies or revised risk targets. Do not restart insertion or replace it with a fourth task. The previous manuscripts and all historical evidence must remain recoverable. The central research question is evidence sufficient to justify a specified recovery obligation from the facts and intervention data actually available. This is ONE methodological paper, not a collection of pipeline contributions.

### Research ownership

Treat the supervisor blueprint as the scientific design. Do not claim DSRE outperforms exact B7, matched CART, or direct partial-ID rules when identical decisions were recorded. Do not invent a theorem or causal guarantee beyond the source-specific assumptions. Never add favorable figures or omit material failed outcomes to create a win. You can tighten exposition and make source-grounded design diagrams; you may not alter the thesis or run new searches for a better algorithm.

## 1. Read the exact current local science before editing

In order:

1. `docs/DSRE_FINAL_METHOD_AND_PROOFS.md`
2. `docs/DSRE_FINAL_SCIENTIFIC_REPORT.md`
3. `docs/DSRE_FINAL_EXPERIMENTAL_AUDIT.md`
4. `docs/DSRE_FINAL_RSS_STAGE1_CHARTER_PLAN.md`
5. `docs/DSRE_EVIDENCE_SPEC_V2.md`
6. `docs/DSRE_EVIDENCE_AWARE_PROSPECTIVE_RESULTS.md`
7. `docs/DSRE_EVIDENCE_AWARE_REVIEWER_GATE.md`
8. `rss2027/dsre_stage1.tex`, its bibliography and figure sources
9. Every sealed local manifest referenced by the key numerical claims.

Verify local HEAD, branch, remote ancestry, source/provenance and outstanding user changes. Import supervisor blueprint without resetting to the older GitHub branch. Preserve `.gitignore`, `uv.lock`, historical seals, all unrelated changes, and the latest full paper byte-identically. Work only on Stage 1 artifacts, paper source figures, final claim ledger, citation audit and independent-review documents.

**Source rule:** the supervisor blueprint is a claim selection plan. It does not independently verify local `d917...` numbers. Recompute every selected count, interval, eligibility denominator, bound, action-cost unit, confidence allocation, baseline equivalence and condition from exact recorded results. If a report conflicts with raw data, show the disagreement and use independently verified numbers. Never copy a number based only on the handoff.

## 2. Author one paper using the locked hypothesis and proof obligations

Use the title and central one-sentence thesis from the blueprint. Define all variables exactly once and use same capitalization and naming from abstract through conclusion. Fixed concept terms:

- **predecision observation** X, chosen **observable evidence** E,
- **intervention evidence source** D (paired, randomized single-arm, or assumptions-limited observational),
- **region** S with whole calibrated membership,
- **outcome obligation** o: harm bound, positive benefit bound, or absolute success, explicitly named,
- **certificate** C=(E,S,D,o,B,W), with the bound set B and evidence/witness W,
- **binary task harm** h and expected task-success gain g (not physical safety guarantees),
- **abstention/defer** when evidence is insufficient.

Do not use `E` for both evidence and an error event; write loss events as `ell` if needed. Be mathematically precise about randomized one-arm assignment, propensity, consistency, identification, independent sample splitting, support and scope. Use the four-cell potential-outcome table, sharp Kallus/Fréchet bounds, and scoped worst-case obligation condition. Include one short checked proposition about calibrated-region soundness and a small counterexample showing nonidentification under identical marginals. Classical facts must be cited rather than relabeled as new theorems.

**Two specific objections the methodology MUST preempt within the five pages:**

1. A selected conjunction E may cover more than the independently calibrated scope S. A reported population guarantee cannot silently move from S to E; require a certificate to name exact scope S and restrict/qualify every E-compatible region. Include a concrete explanatory sentence or equation and ensure source proof is valid for actual router selection.
2. Single-action logs identify action-success marginals under the randomized protocol, not a factual individual joint counterfactual outcome. Paired branches are available only to isolated offline simulator evaluation; the online method never has both futures. An unrecoverable confounding/overlap situation returns insufficient evidence, not a falsely confident action.

## 3. Write as one scientific narrative, not as a tech report

Consult the uploaded `Universal_Top_Paper_Playbook_v7_Visual_Storytelling` when available locally and follow its central argument and reviewer reading-order principles. The first page must answer what the tension is, what evidence sufficiency changes, why this matters across robotics rather than one cube simulator, what DSRE computes, and what early evidence supports that conceptual change. Cite primary related work directly in the opening introduction; the last contribution paragraph is citation-free.

The work's novelty must be positioned against Kallus (NeurIPS 2022), Li et al. (ICML 2023), partial-ID policy learning (AAAI 2024), DISCRET (ICML 2024), KnowNo (CoRL 2023), the relevant recovery counterfactual work and minimal sufficient explanations. The novelty is NOT the underlying bound, pure-rule search, conditional action selection or causal assumptions. State the positive contribution through its recovery-evidence contract and qualification/diagnosis mechanics. Do not include defensive 'we did not invent...' prose in the abstract or contribution statement. Put important scope qualifications where a knowledgeable reader expects them, in Method and Results. Do not suppress exact B7/CART matches in the comparison.

**Abstract:** context -> unresolved evidence question -> obligation-specific, source-aware formulation -> certificate and witness mechanism -> two qualified physical source studies -> scientific implication. A draft exists in the blueprint; verify and rewrite it as needed.

**Section flow:** Introduction and Figure 1; Related Work (compact, integrated); Problem Formulation; Method; Experimental Protocol and Findings; Discussion and Conclusion. This is a five-page narrative, not a chronological history. Abstract/conclusion should express the same central result.

## 4. Figure 1 and results selection

Figure 1 must occupy the first page if formatting permits. It should show two evidence streams, paired simulator outcomes versus single-action logs, feeding an identified/partially identified outcome region, named obligation, minimum observed certificate or missing-evidence witness, then ONE online action or defer. A two-world analytical inset shows same action marginals but opposite harm verdicts. It must be clear the robot never executes both alternatives online. Use a professional source-controlled diagram, readable text, consistent notation, and a short scientific caption, not an engineering box inventory or invented visual claims.

**Main table:** use two distinct main simulated manipulation mechanisms as strong preliminary evidence. In separate registered frozen cohorts, PickCube has reported 227/256 selected completions and 84 necessary rescues, PushCube 253/256 and 126 necessary rescues, both with zero observed binary harms. The current latest local source must independently establish these values. Include fixed continuation and recovery, identical B7, matched CART/direct partial-ID controls with comparable information and confidence. Pick fixed recover has 32 harmful interventions in its reported test; Push fixed recover succeeds 252/256, making it a nearly optimal fixed-action comparator. Show that difference, not an unsupported ranking advantage. Include cost and futility counts where directly reported and comparably defined.

Do not pool historical dual-obligation cohorts with this newer logged-data test. A separate mechanism figure/table may use one earlier five-condition observation-versus-capability ceiling if it directly tests H2, marked as distinct. The 48-parent insertion pilot has no source-qualified full test and failed its action-diversity gate; do not represent it as an independent positive dataset. Navigation has no required recoveries on the tested distribution, so treat it as an informative boundary case if space allows, not the main physical-success result.

**Final figure/table audit:** each has a question in the preceding text; source, task, numerator/denominator, independent-parent grouping, outcome obligations, evidence regime, and caption meaning are clear. Use point effects and confidence intervals only for registered claims with available recalculated evidence. Source-qualification percentages and observed no-harm counts must never be called universal safety.

## 5. Stage 1 versus possible Stage 2 validation

Confirm the live RSS 2027 CFP and FAQ. Stage 1 is exactly five content pages and one references page, self-contained and anonymous, with no relied-on external supplements. It must have a fully developed hypothesis and method, even with incomplete final experiments. Do not turn it into a position paper or pretend all final evaluations are present.

The method MUST already make sense for a registered finite action pair and admissible offline evidence sources at Stage 1; later validation does not invent new core semantics. A brief future-evaluation paragraph may name independently qualified contact-sensitive tasks, source shift/measurement missingness, and sample-cost-sensitive logged-data comparisons. Do not mention 'Charter', 'RSS reviewers will ask', 'Codex', internal gate names, research pivot history, or GitHub/public author-identifying materials inside the paper. No real-robot commitment unless verified access and protocol exist.

Prepare a separate **reviewer/charter feasibility document** with the scope, exact estimands, source feasibility, sample budget and three realistic validation extensions. Make it easy to rebut potential objections without claiming future acceptance is guaranteed.

## 6. Mandatory adversarial three-reader review

Simulate distinct objections by a robotics reviewer, a causal-identification/statistical reviewer, and a research-novelty/methodology reviewer. For each state: the actual objection, the source/section that addresses it, whether it remains valid, and the narrowest amendment to the paper needed. No fictional paper acceptance scores. Explicitly test:

- Is this an algorithm or an integration of classical partial-ID and exact rule search? Does the paper explain why the integration is a new robotics reasoning capability?
- Are 'same observed marginals, different harm' only analytical constructed worlds? Does the paper avoid claiming they occur in every measured robot region?
- Are harm and gain guarantees valid for the **actual** selected/whole routed regions and confidence allocation, not post-hoc subgroups?
- How do randomized logs differ from simulator paired evaluation and arbitrary confounded observational logs?
- Is PushCube's near-optimal always-recover outcome acknowledged and not depicted as a method win?
- Why do matched B7/CART/direct-bound methods produce identical actions? What certificate outputs are tested beyond labels?
- Does the Section 2 method provide sufficient detail for an expert to verify primary claims without a supplement?
- Does the paper present distinct grasps and pushes as useful breadth without claiming general robotics deployment?
- Can the first-page illustration and abstract alone convey the question and precise methodological change?

Have an independent numerical script reconstruct the main table from sealed local data and an independent LaTeX/figure inspector verify the compiled PDF. Do not rely exclusively on existing Codex tests for source auditing.

## 7. Deliverables and stopping condition

Produce in a LOCAL scoped commit:

1. `rss2027/dsre_stage1.tex` and compiled `rss2027/dsre_stage1.pdf`, with exactly 5 content plus 1 references page, correct official 2027 template and embedded fonts.
2. The Figure 1 drawing source, PDF/raster media, and all figure/table data source scripts.
3. `docs/DSRE_RSS2027_STAGE1_CLAIM_EVIDENCE_LEDGER.md`, every numerical and methodological assertion traced to the frozen source.
4. `docs/DSRE_RSS2027_STAGE1_ADVERSARIAL_FINAL_REVIEW.md`, concrete issue-by-issue fixes and residual novelty risks.
5. `docs/DSRE_RSS2027_STAGE2_FEASIBLE_VALIDATION.md`, 3 task-level charter options with data and compute feasibility (not a full-length paper).
6. `docs/DSRE_RSS2027_STAGE1_SUBMISSION_AUDIT.md`: verified source, bibliography, numerical reproduction commands, anonymity, formatting, PDF visual pages, reviewer reading tests, and exact local git SHA.

Run maintained unit tests where relevant, independent numerical checks, LaTeX compilation, `pdfinfo`, `pdffonts`, and page renders. Avoid any external links to author identity in the anonymous PDF. Never fabricate a citation, result, image, sample size, statistical qualification or safety statement. Preserve all local user changes, `.gitignore`, `uv.lock`, historical seals and the full-length master unchanged. No GitHub push or RSS submission.

**Finish the paper now.** Do not return only a plan or propose another research cycle. A final weak-confidence scientific assessment should remain honest in the separate internal report; no optimistic acceptability guarantee should appear in the manuscript. If one claim is unsupported by the local source, drop or narrow THAT claim; do not redesign the science or run new physics.