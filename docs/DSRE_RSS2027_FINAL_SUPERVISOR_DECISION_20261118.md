# DSRE for RSS 2027: Final Scientific Decision and One Last Bounded Validation

**Decision date:** 18 November 2026. **Research supervisor:** ChatGPT. **Implementer:** Codex.
**Scientific status:** Coherent and technically testable, but not a high-confidence RSS acceptance case. This document is a scientific decision, not an empirical result or acceptance promise.
**Hard instruction:** This is the LAST experimental redesign. The RSS Stage 1 manuscript becomes the priority after the bounded run, regardless of its outcome. No change of topic after this decision.

## A. What I reviewed from the complete history

GitHub branches: DUAL-REC (`dual-rec/d5-d7`, `research/budget-aware-verification`), RecoverBench transfer (`research/affordance-recovery-recoverbench`), REBOOT (`research/reboot-onset-specificity`), RecoveryClaim (`research/recovery-claims-validated-results`), DSRE (`research/dsre-rss2027-science-first-20261115`, `research/dsre-rss2027-stage1-synthesis-20261116`), and evidence-aware design (`research/dsre-evidence-aware-design-20261117`). Also inspected the uploaded November 18 evidence-aware completion archive, its reports and last source guards. Public GitHub lacks several latest LOCAL commits; their hashes come from verified user/Codex records and are not falsely claimed as remote.

Historical research decisions:

| Direction | Proven contribution/evidence | Why it is not the final independent paper |
| --- | --- | --- |
| DUAL-REC, LOGIV | Qualified physical infrastructure, some recovering scripted interventions | Registered ambiguity and preference-reversal hypothesis failed its prerequisite |
| RecoverBench transfer | Source qualification and negative transfer evidence | Interface/source mismatch prevents trusted common comparison |
| REBOOT / FailTime | Timing and annotation sensitivity | Main timely-alarm hypothesis unsupported or labels blocked |
| RecoveryClaim | Real paired physical recovery successes on Pick/Push and audited replay | Matched qualified-prefix completion erases claimed novel certifier advantage |
| DSRE v1.2 | Exact minimum evidence, finite-reference witnesses, observation/action ceilings, robustness, five physical conditions | B7 exact-equivalent; newer conditions still within PickCube |
| DSRE dual obligation | Independently certified non-degradation, 38 necessary rescues, four futile tries; success obligation different | Distinction alone follows from ordinary risk/event inclusion |
| Evidence-aware DSRE | Source-aware partial identification, scoped certificates, actual single-action logged Pick recovery, 84 necessary rescues/256 | Matched rules, CART, direct bounds tie; navigation requires no rescue; insertion has predecision planner aborts |

**Selection:** Keep the core DSRE intervention-evidence problem, its smallest robust statistical certificate, and the *actual* logged-data interface. Abandon claims of novel rule search, always-superior policy control, unique witness-based sample efficiency, universal sensor robustness, or end-to-end real-robot safety.

## B. One scientific claim, not five contributions

**Central hypothesis:** Whether robot recovery can be justified is jointly limited by (i) available observable facts, (ii) available intervention evidence and its identifiability assumptions, (iii) available recovery actions, and (iv) the declared task-outcome obligation. These constraints can be distinguished constructively, and some useful interventions can be justified from randomized one-action execution logs without executing the alternative at decision time.

**One methodology:** An **obligation-specific recovery evidence certificate** `C=(E,R,D,O,B,W)`:
- `E`: a minimum subset of actual predecision facts.
- `R`: the full, independently calibrated decision region(s) the certificate covers, not a secret narrower subgroup.
- `D`: paired or randomized one-action intervention evidence, with assignment/causal assumptions.
- `O`: explicitly requested action obligation. Primary = harm at most 10% AND expected binary task-success gain at least 5%; separately report harm-only and absolute-success comparisons.
- `B`: simultaneous confidence or partial-identification bounds, with parent-level independent support and correct calibrated scope.
- `W`: a constructive obstruction/witness if qualification fails, such as opposing adequate actions, an identifiable source failure, inadequate repertoire, statistical uncertainty, or two indistinguishable joint distributions.

**Do NOT claim** the basic bounds, shortest-conjunction solver, risk calibration or causal policy bounds are invented here. The scientific object is the minimum observable *and* experimental evidence required for a named physical intervention obligation. The evaluation should test that object through equal-cost evidence regimes, physical intervention outcomes and genuine non-grasp corroboration.

## C. Exact mathematics, with a non-tautological testable contrast

For one independent target checkpoint, define binary potential completion outcomes `Yc` (continue) and `Yr` (recover). In a given frozen, supported, eligible context cell `L`:

`pc=P(Yc=1|L)`, `pr=P(Yr=1|L)`, `h=P(Yc=1,Yr=0|L)`, `g=pr-pc`.

With randomized one-arm logs and consistency/positivity, the marginals are identifiable; the harm joint event generally is not. Its **known sharp** bound is:

`max(0, pc-pr) <= h <= min(pc, 1-pr)`.

At the frozen target `alpha=.10, eta=.05` and **exact marginals**, the log-only useful-recovery claim is identifiable and satisfied iff:

`pr-pc>=.05 AND (pc<=.10 OR pr>=.90)`.

A key *experimental question* is how often physically meaningful recovery regions occupy this certifiable part of the marginal plane, and how often paired evidence is necessary. The equality is a classical consequence of the sharp bounds, not a novelty theorem.

**Non-identification witness:** `(q00,q01,q10,q11)=(.4,.2,0,.4)` and `(0,.6,.4,0)` have identical marginals `pc=.4, pr=.6` and gain `.2` but harm `0` versus `.4`. An infinite set of the same randomized one-arm logs cannot distinguish these worlds. Paired simulator data can resolve their joint outcomes within the declared simulator reference.

For finite calibration with simultaneous lower/upper intervals `(Lc,Uc)` for `pc`, `(Lr,Ur)` for `pr`, a conservative sufficient certificate uses `H_U=min(Uc,1-Lr)<=.10` AND `G_L=Lr-Uc>=.05`. These intervals must be valid for the exact frozen cell and cannot be retrofitted to an adaptively selected subregion.

**Simple scope-validity lemma:** Freeze a finite observable partition on discovery data. If every whole cell included by a reported conjunction `E` has independently and simultaneously valid `h_cell<=alpha` and `g_cell>=eta`, then any mixture over those cells also satisfies both bounds, because conditional harm/gain are weighted averages. Unknown/unqualified cells invalidate the purported certificate. This lemma is elementary; its role is to avoid a false guarantee on selected subgroups. Report uncertainty in cell support; do not use test labels for this process.

Use the exact existing source-aware four-cell LP as an independent implementation; it must match analytical bounds. Existing `DSRE_FINAL_THEORETICAL_CHECK.json` verifies 1681 LP instances, max absolute discrepancy `1.11e-16`. This is supervisor design verification, not robot science.

## D. Why the experiment must be finite and comprehensive

The largest current gap is independent task breadth. Do not spend the last weeks attempting to fix every planner failure or adding another chain of risk gates. We need a bounded, **decisive comparison** using a task whose physical source already qualified and one optional contact-specific pilot. The remaining work is *one* experimental campaign and a frozen, manuscript-focused handoff.

### E1. Cross-task evidence frontier, no new physics at first

Use existing qualified paired PickCube, PushCube, and independently trained logged PickCube and PointMaze cohorts. Keep every historical cohort tagged with its original role; an inspected outcome cannot be a novel untouched test. Recompute with an independent oracle:

1. action capacity: at least one action succeeds;
2. observable-action commonality: compatible observation signatures share a successful action;
3. evidence-type sufficiency: randomized one-arm marginals can certify the requested obligation, paired outcomes could certify it, or neither can;
4. calibrated action-coverage and useful recovery under the actual registered distributions.

Report these **as separate quantities**, not as an additive population decomposition or a new optimizer victory. Include physically grounded opposing-action and neither-success witnesses. Stratify by true task and condition; hidden source labels cannot be used as predictor features. Reproduce baseline exact equivalence. Provide cost per observed action, not merely sample count.

### Supervisor exploratory falsification check on the OLD PickCube calibration

I independently reanalyzed the already inspected five-condition, 1,280-checkpoint PickCube dual-obligation calibration table. Grouping by the first 6, 7 or 12 recorded Boolean predicates gives 10, 15 and 52 full signatures, respectively. Among groups with at least ten checkpoint rows, **zero** had all three *empirical point-estimate* properties: gain at least .05, paired observed harm at most .10, yet the sharp upper harm bound from single-arm marginals above .10. This is NOT a proof that physically paired-only cases do not exist; the observations are correlated within 256 parents, and these are neither statistical confidence claims nor untouched data. It is a warning that physical pairing may add NO certifiability for the current coarse Pick vocabulary. The final study must report this possibility and cannot claim the pairing/identification component beats ordinary rules when its actual target regions are already log-identifiable. The source and independently executable diagnostic are preserved as `DSRE_FINAL_EXISTING_DATA_CHECK.json` and `DSRE_FINAL_EXISTING_DATA_DIAGNOSTIC.py`.

### E2. ONE genuinely prospective new-source PushCube one-arm study

PushCube is not selected as a favorable new task: it is a historically qualified pushing contact mechanism and was present throughout DSRE development. Prespecify it as a **contrast to PickCube**, with no new controller or fault search. The point of this study is whether the *same* obligation-specific evidence method correctly handles a second source distribution, not whether DSRE wins over the obvious recovery baseline.

**Fixed independent seed parents, never used before (check collisions before outcome access; on collision STOP rather than replace):**
- discovery: `910000000..910000127` (128),
- randomized single-action calibration: `910001000..910002023` (1024),
- untouched selected-action test: `910003000..910003255` (256).

Exactly one predecided condition per parent: even original index = nominal; odd = the existing qualified `misaligned` condition. Do not expand/retune severity after looking at outcomes. Action assignment for discovery/calibration: `sha256("DSRE-FINAL-PUSH-ARM-v1:"+seed)` first bit, implementing registered P=.5 for recover. Save propensity, observations, executed fixed action and actual terminal outcome. The other branch MUST NOT be available to any learner, feature/partition optimizer or calibration routine. On frozen test parents, physically execute the chosen action first; only an isolated evaluator may produce the alternative outcome from qualified source replay for scoring.

Freeze partition on discovery (K<=4, only predecision measured predicates). Freeze every baseline and leaf before calibrating. Preserve registered `alpha=.10,eta=.05`, confidence/tail allocation `0.025/(4K)` and whole-leaf validity. Compare exact B7, direct partial-id, CART with the same gate, ordinary outcome regression, fixed continue and fixed recover. Match outcome access and action-execution cost. If the task proves almost always-recover, that is a valuable negative control but **not** evidence of selector superiority.

Report one-arm identifiable-versus-pair-required contexts, certificates, selected task completion, required rescues, harms, futile attempts, abstentions, rule lengths and sample/physics cost with parent-level uncertainty. Never report a hidden joint outcome as available to the deployed selector.

### E3. BOUNDED insertion mechanism pilot, NOT the source-blocked old prospective cohort

The earlier source-screening study found 363 usable predecision checkpoints and two genuine upstream failures before the chosen decision point (zero controls for one seed; 33 controls for another). These are not action outcomes. Its 1024 calibration / 256 test cohort remains incomplete and must not be retroactively relabeled as the final experiment.

Prespecify exactly 48 new independent development parent IDs `920000000..920000047`, disjoint from every known insertion cohort. Evaluate BOTH registered cached-insertion and correction-insertion macros **only at valid checkpoints**. A planner abort at ANY stage strictly before the preregistered decision checkpoint is uniformly classified `NO_DECISION_CHECKPOINT` with executed-prefix count and source trace; retain the original registered seed denominator. A source/model/controller/dynamics mismatch or an action failure after an eligible checkpoint is not silently excluded; it receives its actual observed terminal outcome, or `MISSING` with bounds if no endpoint is observable. Never invent grasp aperture.

Stage the pilot before any extension. If (a) >=32 qualified decision checkpoints and (b) both continue-only and recover-only physical outcomes appear on at least 2 distinct parent seeds EACH, freeze a SECOND, separate, exploratory 96-parent paired confirmation with seed IDs `920001000..920001095`. Report all 96 registered parents and attrition. These counts give preliminary diversity, **not formal calibration of an obligation**. Do NOT reuse them to fit a claim subsequently advertised as held-out. If the pilot fails either source or action-diversity gate, stop insertion permanently for Stage 1; report it as an unsuccessful optional pilot, no new replacement task. This is source qualification, not outcome-based optimization of the DSRE method.

**No requirement to finish the old 1024-parent insertion study.** A source guard does not justify repeated indefinite repair. Full insertion qualification can remain an optional Stage 2/Extension Charter item, not a Stage 1 central promise.

### E4. One controlled baseline and identifiability challenge, not a new strategy search

Combine the existing Pick logged/paired evidence with new Push results. At matched per-task observation availability, fixed risk/gain requirement and action-execution budget, report paired oracle, log-only partial ID, exact rule, CART, frozen outcome regression, and always-action baselines. Include two synthetic same-marginal/different-harm worlds as sanity tests, labeled analytical. Do not claim acquisition-guidance superiority: previous preregistered 512-action evidence budget found five strategies tied. Do not launch a second witness-optimization search. A *source-evidence diagnosis* can be tested by showing actual cases where log-only data are intrinsically nonidentifying, while more logs cannot resolve the ambiguity; paired trials can, given physical reference assumptions.

### E5. Independent scientific gate and manuscript handoff

Deliver three tightly connected claim tests:
H1: the method distinguishes when randomized one-arm evidence suffices and when the requested obligation remains nonidentified; **whether paired-only certifiable situations occur in each physical task is an empirical question, not a presupposed positive result.** (A methodological/measurement contrast, not novel Frechet theory.)
H2: obligation-specific minimum evidence constructs validity-limited certificates across both pick and push, with correct support/identifiability and counterexample witnesses.
H3: the same method identifies both recovery-beneficial and unnecessary/harmful intervention regimes, with an independently qualified operational tradeoff and no asserted algorithm dominance.

Compare hypotheses against actual results. A claim without evidence must be removed or framed as an explicit Stage 2 test, never implied proved. If ordinary rules reproduce every action, say so in scientific results once and focus on the intervention-evidence problem and soundness; do not claim optimization superiority.

**Hard stop:** Finish this LAST scientific run by November 21, 2026, or stop at a sealed atomic boundary with exact incomplete counts. There are no further changes to the experimental problem or new task search after this date. November 22 to December 3 are reserved for the RSS Stage 1 scientific manuscript, bibliography and adversarial review. The author decides whether to submit on December 4; no acceptance guarantee exists.

## E. Feasible Extension Charter, not an open promise

The proposed RSS 2027 Stage 2 extensions must follow the same evidence-certificate question, with no new research direction:
1. A further independently held-out physical manipulation family: qualify insertion checkpoints and both fixed actions under uniform no-checkpoint handling; if impossible, add a rigorously qualified alternative contact mechanism with a preregistered substitution rule reviewed by ACs.
2. A larger one-arm logged-data comparison under controlled missing observations/measurement uncertainty and matched action cost, with fresh calibration and independent test regions.
3. Richer finite recovery repertoires if source-qualified: add a pre-existing qualified alternative macro and evaluate obligation-specific certificates for each action versus the same baseline; this is optional and should not be a Stage 1 dependency.
4. Worst-case cost-benefit and evidence-identification frontiers with strong counterfactual/no-harm policy baselines, including the case when exact ordinary rules implement identical decisions.

No promise of real hardware without an actual accessible platform and verified protocol. An AC may alter the requested charter. Stage 1 must be independently sufficient in its method, hypothesis, feasibility and scientific motivation.

## F. Nearest-work and reviewer-risk test

**Known overlaps:** minimal sufficient decision explanations (Khan et al. ICAPS 2009); observation-common-feasible-action analysis (Zhu/Leonard 2026); partial identification and no-harm policy learning (Kallus NeurIPS 2022, Li et al. ICML 2023, Joshi et al. AAAI 2024); outcome-aware rules (DISCRET ICML 2024); intervention-aware recovery evaluation (RESCUE preprint 2026); explanation-based sensing (DA-GRD preprint 2026); and calibrated abstention (KnowNo CoRL 2023). Review exact venue/status in primary sources. No broad first-ever claims and no unverified comparison to uninspected work.

**Scientific distinction to test:** the resulting *robot recovery certificate* jointly describes minimum observable facts, the action-outcome evidence/identification assumptions, the named obligation, and a constructively illustrated insufficient-evidence case. The unified methodology's importance must be supported by task-grounded decision and evidence results, not by the labels attached to its modules.

**Top reviewer objections and answer obligations:**
- Tautology of non-degradation: lead with evidence-dependent certifiability and finite-sample validity, not nested error events.
- Simulator-only counterfactual: log-only learner sees one action; paired simulator experiments are offline oracle, never online input.
- Standard pure rules and CART: no invented optimizer victory; matched gate and identical information/cost comparison.
- Narrow tasks: new qualified Push one-arm + Pick one-arm + independent navigation negative-control + bounded insertion pilot, named as 2 core contact mechanisms and 1 navigation abstraction; no five-offsets-as-five-tasks claim.
- Acquisition witness uselessness: no claim of allocation advantage after observed 512-cost tie; nonidentification witness is correct on constructed and physical regions.
- Weak end-to-end completion: report always-recover and always-continue success and harm/cost; selective coverage and rescue gain are separate.
- Charters too ambitious: limit Stage 2 to named, feasible source-qualified tasks and defined distributional tests.

## G. Execution constraints

Codex implements, not redesigns science. Start from the latest LOCAL commit `e8efd0fddf70a5405b5e9bda07e206655aa05d8b`; preserve all local uncommitted changes, the original locked manuscripts, .gitignore, uv.lock, old seals and partial insertion archive. Create dedicated branch `research/dsre-rss2027-final-science-20261118` without resetting to a remote design branch. Do not push or submit. Import this document by verified GitHub URL or user-provided file.

BEFORE any physics:
- verify disjoint seed manifests against all historical logs; freeze action definitions, qualification rules, simulator source hashes, one-arm access, partition algorithm, baseline scope, LP and CI code;
- register complete primary estimands and decision gates; prevent test leakage; record exact renderer ICD and CPU physics environment;
- independent pilot for native/physics source start, no environment/source mutation to force qualification.

**Max new physics:** 12 cumulative worker-hours across all phases, 4 GiB conservative compressed artifacts, bounded batches of <=16 parents or <=15 minutes, automatic atomic restarts only after clean interruption, no repeated failed source attempts except diagnostic reproduction. Reserve final 2 hours for independent audits, figures, results and seal; if time fails, finish from existing validated datasets and seal partial evidence. No GPU model training, new foundation models, paid APIs or large datasets. A fixed absent-macro, invalid checkpoint or source mismatch halts that task, not the whole program.

**Must deliver:** `docs/DSRE_FINAL_SCIENTIFIC_REPORT.md`, `docs/DSRE_FINAL_METHOD_AND_PROOFS.md`, `docs/DSRE_FINAL_EXPERIMENTAL_AUDIT.md`, `docs/DSRE_FINAL_RSS_STAGE1_CHARTER_PLAN.md`, source-grounded three-to-five primary figures/tables, exact reproduction, frozen baseline identities, physical source trace logs, independent confidence/oracle checks, and sealed data. Commit locally. **Do not revise the manuscript in this final scientific run.**

**Then:** hand results to the supervisor for Stage 1 writing. No further expansion, new theory direction, or new experimental campaign regardless of result. Manuscript after November 21 must present the strongest falsifiable thesis the evidence supports.