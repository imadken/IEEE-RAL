# RSS 2027 Stage 1: DSRE scientific-story lock

Scientific supervisor decision, 18 November 2026. **The new experiment campaign is closed.** The user-provided final handoff reports local commit `d917a69d47f3102123030eaf565f4623dad86525`. This document is a research-to-manuscript specification, not a newly verified audit of that local commit. Codex must verify every result against its sealed records before inclusion.

## A. RSS Stage 1 decision criteria and deadline

Official RSS 2027: 5 main-content pages plus exactly one references page, no supplements considered. Stage 1 assesses the **value of the hypothesis** and **feasibility of a scientifically informative conclusion**. A proposal of future experiments alone is insufficient, but complete final hardware validation is not required. Stage 1 deadline: December 4, 2026, 23:59 Anywhere on Earth. Rebuttal: February 5-12, 2027. Extension Charter invitation decision: February 26, 2027. Final invited paper: April 16, 2027. The official source is https://roboticsconference.org/information/cfp/index.html and https://roboticsconference.org/information/author-faq/ .

**Internal judgment:** Our scientific question is consequential if stated broadly enough; the current empirical distinction is still limited by exact conventional-rule equivalence and two fully evaluated simple manipulation tasks. We cannot guarantee acceptance or assign a confidence margin from tests passing. We CAN submit a technically developed, hypothesis-driven, evidence-backed methodology and a feasible Stage 2 validation plan. No more physics is authorized before Stage 1; science is frozen.

## B. One thesis that unifies the work

> A robot's recovery decision is justified only relative to (i) the state facts it can observe, (ii) the action-outcome evidence it has, and (iii) the outcome obligation it promises; DSRE synthesizes the minimum factual support or identifies why the available evidence cannot justify that obligation.

Scientific contrast (for the first 100 words): recovery controllers can be effective, but observed historical success of a recovery skill does not automatically warrant executing it in the current uncertain situation. Nor does a good mean treatment effect identify the probability of harming an otherwise successful continuation. Standard rules can reproduce recommendations but need a declared evidence and validity scope to support the causal claim.

DSRE is not framed as a novel search algorithm or novel harm bound. Its methodological object is an **obligation-specific, source-aware, region-scoped recovery certificate**:

C = (E, S, D, o, B, W),

where E is the selected observable factual conjunction; S is the whole independently calibrated routing region(s), with exact membership; D is the source regime and evidence assumptions; o is the named recovery obligation; B contains simultaneous confidence/identification bounds; and W is a supporting or insufficiency witness. Certificate C either qualifies action recovery/continue for that claim or declares exactly why it cannot.

The paper has ONE contribution: **recovery-evidence sufficiency**. Minimum facts, statistical qualification, identifiability, and physical witnesses are aspects of that same object, not four independent contributions.

## C. Locked notation and mathematical claim

Let X be predecision observable facts and a0=continue, a1=recover. Let Y^0,Y^1 in {0,1} be terminal task-success potential outcomes under fixed actions and horizon. For a whole frozen conditional decision region S, define:

- p0(S)=P(Y^0=1 | X in S)
- p1(S)=P(Y^1=1 | X in S)
- h(S)=P(Y^0=1,Y^1=0 | X in S), binary task-outcome harm
- g(S)=p1(S)-p0(S), mean success gain.

For a randomized one-action log with consistency, exchangeability by assignment and overlap, p0,p1 are identifiable, but h need not be. Established sharp Fréchet bounds:

max(0,p0-p1) <= h <= min(p0,1-p1).

If q00,q01,q10,q11 are probabilities of (Y^0,Y^1)=(0,0),(0,1),(1,0),(1,1), then p0=q10+q11, p1=q01+q11, h=q10 and g=q01-q10. Paired simulator evidence can constrain the joint q within the simulator's declared deterministic replay scope. Arbitrary observational logs without a valid causal assumption do not identify potential-outcome marginals, so the correct output is an unsupported obligation.

For fixed tolerances alpha=.10, eta=.05, and simultaneous confidence/identification ambiguity set Q_D(S), a qualified **useful, non-degrading recovery** region satisfies:

sup_{Q in Q_D(S)} h(Q) <= alpha  AND  inf_{Q in Q_D(S)} g(Q) >= eta.

The 10% guarantee is a **regional population guarantee under the declared source and sampling assumptions**, not a pointwise guarantee or physical robot safety claim. Region membership is determined before calibration. Calibration outcomes may not choose or shrink the region. The rule must be frozen on discovery data; valid confidence and union-bound allocation are applied to disjoint independent calibration parents. A minimum displayed conjunction E must include all regions compatible with E, or name the narrower certified S explicitly; otherwise the claim is invalid. Parent-level dependence and predecision eligibility are part of the scope.

Candidate E is chosen among known predecision predicates in a fixed dictionary, minimising |E| while maintaining obligation and reference support across all claimed S. A missing counterfactual witness is a pair of admissible q tables with identical observable marginals but contrasting harm verdicts, not simply a confidence interval. Missing-action, incompatible-observation, insufficient-calibration, and unidentifiable-joint cases are distinct return types; avoid presenting them as unrelated modules.

**Internal theorem obligations for Codex to verify from final method:** 1) scoped soundness from a simultaneous confidence event and worst-case constraints; 2) exact minimality of E under the fixed grammar; 3) no certification from marginals when the upper sharp harm bound exceeds alpha without additional identifying assumptions. The last item is known mathematical groundwork, not our new theorem. A synthetic same-marginal two-world example establishes the need for source-aware identifiability, while physical results establish relevance.

## D. Three falsifiable hypotheses, not a module inventory

H1 (Source sufficiency): randomized one-action execution evidence can qualify a useful recovery under stated assumptions in some physical situations, while other causal obligations remain unidentifiable even with arbitrarily many unpaired observations. Evidence: same-marginal analytical counterexample; genuinely randomized one-arm physical experiments; pre-registered bounds; qualified and unsupported cases.

H2 (Observable sufficiency): the minimum facts required for a qualified claim depend on the calibrated decision region, and source-aware counterexamples identify whether more observation, joint intervention evidence, statistical samples, or another recovery skill would be needed. Evidence: exact certificate/witness audits, paired outcome classes, physical ambiguity examples, and B7 equality. No empirical claim that witness-guided acquisition beats strong uncertainty sampling, because the registered 512-action budget tied.

H3 (Robotics consequence): the same source-aware certificate interface supports physically useful decisions in distinct manipulation mechanisms while making explicit the tradeoff among completion, genuinely required rescues, harm, futility, and abstention. Evidence: fresh grasp and pushing cohorts, frozen ordinary-rule/CART/direct-bound controls. The thesis does not require outperforming equivalent implementations on action labels.

Do not expand into a claim of general sim-to-real safety, novel identification theory, universal policy superiority, or useful recovery from every source/task.

## E. Evidence selection for five pages

All numbers in this paragraph were **reported in the user's 18 Nov local final handoff and require exact raw-source audit before manuscript use**. They are not generated here. Parent/condition structure and independent splits must be read from the final results. Never pool separate historical cohorts into a single estimate.

**Primary direct evidence: genuinely one-action-trained, test-evaluated, two manipulation mechanisms.**

- PickCube grasp recovery: 128 discovery, 1024 calibration and 256 untouched test parents. Frozen selected policy completes 227/256; 111 recovery attempts include 84 required rescues, 27 futile attempts, no observed binary harm. Always continue completes 143/256; always recover 197/256 with 32 harmful interventions. Ordinary B7, matched CART and direct bound procedures choose the same actions. Report risk and utility constraints from final audit, not from assumed zero-harm confidence.
- PushCube pushing recovery: 128 discovery, 1024 calibration and 256 untouched test parents. Frozen selected policy completes 253/256, with 126 genuine rescues, zero observed binary harm, two futile attempts. Always recover completes 252/256, so NO meaningful outcome-superiority claim versus a nearly optimal fixed policy. Ordinary exact rules, direct bounds, CART and regression select all the same actions. Show that source-aware selection is feasible, not a new better controller.

**Mechanism validation from independently sealed older cohorts, not pooled:** controlled five-condition PickCube exhibits both harm and necessary recovery and a gap between physical action feasibility and observation sufficiency; earlier dual-obligation result demonstrates success versus non-degradation eligibility; interval evidence preserves factual truth but does not guarantee adequate actions. Include only ONE compact representative contrast if it supports the central hypothesis; do not overload the five pages with separate historic benchmark tables.

**Exploratory boundary cases:** PointMaze navigation: no recover-only successes in this frozen population; recovery cannot be declared necessary. PegInsertionSide: 48 qualified pilot checkpoints with 25 recover-only, 22 neither-success, one both-success, zero continue-only. The diversity criterion failed, so no 96-parent confirmation was run. These are useful scope/feasibility diagnostics, NOT full positive validation. Prefer a brief experimental-scope sentence or Stage 2 outline, not another large table suggesting comparable coverage.

**Experimental table must show:** domain, training evidence = one randomized action per parent, eligible test n, certified risk and gain criteria if actually qualified, selected recoveries, necessary rescues, harms, futile recoveries, total task completions, always-continue/recover, and best fair matched baseline. Clearly mark what is measured versus what is a conditional statistical upper/lower bound.

**No result should be claimed as an algorithmic advantage when matched methods make identical decisions.** The substantive result is evidence-source/obligation correctness with functional robot interventions and constructive insufficiency diagnostics. If this is not an interesting enough methodological contribution for a reviewer, polished prose cannot change the fact.

## F. Paper story and word allocation, five content pages plus one references

Working title: **When Does Evidence Justify Robot Recovery?**
Possible subtitle: **Minimum Recovery Certificates from Partial Intervention Outcomes**. Avoid jargon in the first sentence. Keep acronym Decision-Sufficient Recovery Explanations (DSRE) defined exactly once.

**Page 1:** Motivation close to recovery choices, source-identifiability gap, one high-value example, central thesis, concise contributions, FIGURE 1 (thesis figure). Cite nearby prior art with 3-5 direct references; do not defer all citations to Related Work.

**Page 2:** Rigorous problem formulation: the observation X, fixed intervention pair Y^0,Y^1, evidence source regimes P/L/O and identification assumptions; show four-outcome q and precise risk/benefit obligations; explain concept of minimum evidence certificate.

**Page 3:** Certificate synthesis, scoped validity theorem with proof sketch and assumptions, constructive non-identification witness, exact known method and computational cost, one worked physical fact/witness and matched conventional controls. A broad E does NOT automatically inherit narrow S's bound.

**Page 4:** Claim-first experiments with real dataset splits, fixed controllers/horizon/source, randomized one-arm learner boundary and sealed evaluator-only paired counterfactuals, strongest grasp and push results + same-risk/evidence baselines, no new methods. Include Figure 2 or one compact table.

**Page 5:** Observation/source sufficiency mechanism experiment, non-identification inset or independent witness, physical condition distinction, risk/coverage/abstention and source scope, sharp conclusion and credible 1-paragraph next validation path. No internal Gate, Codex, reviewer, Charter, source repair chronology, or acceptance speculation in submission.

**Page 6:** exactly one page of verified directly relevant references; prioritise NeurIPS 2022 Kallus, ICML 2023 Li et al., ICML 2024 DISCRET, AAAI 2024 safe partial-ID work, CoRL 2023 KnowNo, RSS robot-recovery literature, 2026 RESCUE/DA-GRD with correct preprint status, one classical sufficient-explanation reference, and simulator framework where appropriate. Do not invent venue acceptance or pad the bibliography. Use consistent notation, captions, topic terms and units throughout.

### Figure 1: required thesis diagram (not a generic software architecture)

Upper row marked **OFFLINE EVIDENCE**: paired checkpoint trials OR randomized single-action logs with propensities -> admissible outcome models Q_D(S) with source assumptions -> named obligation (gain and harm) -> minimum observable certificate or explicit missing-evidence witness -> frozen risk-qualified decision rule.

Lower row marked **ONE ONLINE ROBOT DECISION**: current observed predicates -> supported certificate & actual routed region -> continue/recover OR defer. Paired counterfactual branches belong to OFFLINE evaluation only, not online robot input.

Inset: same p0=.4 and p1=.6 but two compatible 2x2 joint tables with harm 0 and .4; this proves that mean success does not identify non-degradation. Inset is a known identification fact, not a new theorem. Bottom small physical examples: grasp/push, each with source-qualified cohort label, not both labelled generically 'robot recovery'. Font ≥7pt at final print scale; accessible legend, source-based labels, no user/public GitHub URLs in anonymous submission. Caption must state the conceptual contrast, not restate pipeline steps.

## G. Abstract draft, to be checked against actual validated results

Robot recovery decisions require more than an effective intervention: they require evidence that the intervention serves a specified objective in the current situation. This is difficult when the robot observes only part of the state and historical executions record the outcome of only one action. We formulate Decision-Sufficient Recovery Explanations (DSRE), which synthesize minimum observable facts supporting obligation-specific recovery decisions under explicitly declared intervention-evidence assumptions. The method combines source-dependent outcome uncertainty with independent region-level qualification and returns counterexamples when observations, causal identification, or statistical support cannot establish the claim. Controlled simulator studies using randomized single-action logs evaluate fixed recovery alternatives in grasping and pushing. On untouched test cohorts, the qualified selectors achieve [verify 227/256 and 253/256] completions and [verify 84 and 126] necessary rescues, while matched exact-rule and tree implementations reach the same operating points. Complementary analyses reveal when physical action feasibility exceeds what observations can justify and when identical action-success statistics conceal different harm. The resulting framework makes the evidence requirements for robot intervention explicit, and distinguishes informative abstention from unsupported action guarantees.

Do not submit this prose unedited: check it follows the final source semantics, does not claim a certificate on arbitrary observational logs, and is within RSS style. Do not imply a proved improvement over CART or exact ordinary B7. All source-specific numbers must be independently audited.

## H. The hardest reviewers, answered in the paper itself

1. **'Just Kallus/Fréchet + rules?'** Established bounds and rule synthesis are cited; DSRE contributes a scoped, obligation-specific observable robot-action certificate with source-specific validity requirements and constructive unavailable-evidence witnesses. Empirical tests must demonstrate source distinctions and robotics consequences, not claim new inequality.
2. **'No method advantage over CART or B7?'** They implement the same supported action decisions in tested conditions. Compare equal data and confidence access; the distinct evaluated output is source/obligation support and its countermodel, not ranking accuracy. No unsupported policy advantage.
3. **'Requires both counterfactual futures at run time?'** No: one-arm randomized execution logs are used offline, online input is only current observations and learned certificate. Paired simulator branch outcomes are an isolated evaluation oracle; graph and methods must make separation unmistakable.
4. **'How can non-degradation be verified without both outcomes?'** It is generally unidentifiable from marginals; the sharp valid upper bound plus finite-sample calibration can certify some regions and withhold others; display two compatible couplings with different harm. Do not claim direct observation of individual counterfactual harm in actual deployed robots.
5. **'Does calibration survive selecting a rule?'** Region partition and proposals frozen before independent calibration; simultaneous confidence sets, actual region membership and parent-level sampling scope preserved. Explain no guarantee for post-hoc subsets.
6. **'Push always-recover already solves it?'** Report 252/256 baseline openly; not a claim of task-success superiority. Together with grasping's harmful fixed recovery, it demonstrates when intervention choice is or is not consequential. Do not present two near-identical tasks as broad physical-world generalization.
7. **'Only simulation and hand-built facts?'** Precisely two successfully evaluated manipulation mechanisms, with source-assumption and predecision observation scope. Source transfer, noise and contact-rich tasks are Stage 2 candidate validation, not completed or guaranteed.
8. **'Witnesses do not improve acquisition at 512 units?'** Correct: do not make sample-efficiency or new active-sensing advantage a headline claim; present the witness's formal diagnostic correctness and available evidence-type distinction instead.
9. **'Reference-only, no real robot?'** Formal source regimes allow one-arm randomized logs under causal assumptions. Current empirical validation remains simulator-only; no sim-to-real or unobserved-confounder guarantee.

## I. Feasible Extension Charter path, not a promise or acceptance trick

One central continuation, not a new model: test the SAME obligation-specific certificate on (a) an independently qualified contact-sensitive manipulation task, with a source-eligibility/attrition protocol locked before outcomes; (b) randomized one-arm logs at multiple evidence budgets to map conditional identifiability and resource cost; and (c) bounded observation noise/shift with fresh qualification where required. The current insertion 48-parent pilot illustrates feasibility of diverse outcomes but also why checkpoint/source validity must be controlled; do not promise an effortless complete contact benchmark. A predeclared alternative source task may be listed only under an explicit fixed source-availability gate and before outcomes. No hardware promise.

This is a realistic menu reviewers and ACs may adapt. No paper claim should imply the Charter has already been negotiated or is guaranteed. We can satisfy constructive comments if invited, but final acceptance remains contingent on review.

## J. Pre-submission source and formatting gate

- Independently open the final LOCAL outcome report at commit d917... and cross-check every numerical value, denominator, calibration bound and source condition.
- Report source-driven eligibility/attrition (navigation's no-checkpoint records; insertion pilot only), and never combine independent cohorts.
- Show exact rule/CART ties with no suppression; all sentence-level results correspond to a figure or table.
- Verify primary papers and publication status; no leaked identifying link or authorship metadata in blinded PDF, no external supplements at Stage 1.
- Figure 1 and captions must communicate offline versus online evidence and physical consequence at legible print size.
- Have independent formal-method, causal-inference and robotics reviewers provide evidence-based critiques and rewrite the ambiguous passages, not the underlying outcomes.
- Lock science and method: no more new physics, controllers, task shopping, or revised theoretical obligations before Stage 1.
- The final claim should withstand a skeptical reader using only five content pages; test by reading title+abstract+Figure 1+conclusion, then by running an independent proof and number audit.