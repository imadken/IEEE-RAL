# DSRE: Evidence-aware recovery justification
## Supervisor research decision and bounded expansion plan

**Date:** 17 November 2026
**Status:** Proposed methodological extension, not a validated replacement or a submission-readiness claim.
**Venue:** RSS 2027. Stage 1 deadline 4 December 2026; rebuttal 5-12 February 2027; Extension Charter decision 26 February; final submission 16 April, if invited. Verify the current official CFP and author FAQ before submission.
**Current local paper/source commit:** `5547450d66e7561d701afcddd29f0e29156fc55c`.
**Immutable experimental parent:** `748301df9e3ad22678077c718a5b44d84948d1cb`, with preceding v1.2 and dual-obligation evidence.
**Immediate scope:** scientific design, implementation, and discriminating preliminary experiments. Do not rewrite the paper or any historical results during the first implementation session. Do not modify the full-length manuscript.

## 1. Supervisor assessment

The existing DSRE has a defined intervention-evidence interface, qualified physics, strong bookkeeping, exact minimum rules and independent risk qualification. It has not yet established a high-confidence RSS contribution. The most serious scientific gaps are: reliance on paired simulator outcomes, a minimum certificate that targets action success rather than the subsequently qualified obligation, narrow physical task coverage, and insufficient comparison against counterfactual no-harm policy learning and partial-identification research.

The previous decision to stop all methodological work was premature. The correction is not to start another project or add many modules. It is to repair one specific limitation of the SAME question:

> What observable facts and what intervention evidence are sufficient to justify a useful recovery action under a declared outcome requirement?

**One core object:** an obligation-specific recovery certificate whose validity explicitly depends on both observable facts and the available type of action-outcome evidence.

The existing paired simulator experiments become an oracle/reference case of this formulation. They are not discarded or relabeled. The non-degradation versus completion result remains descriptive motivation and validation; it is not presented as a new mathematical discovery.

## 2. Verified closest work and novelty boundaries

Primary sources consulted for this plan:

1. Kallus, **What's the Harm? Sharp Bounds on the Fraction Negatively Affected by Treatment**, NeurIPS 2022. https://proceedings.neurips.cc/paper_files/paper/2022/hash/666cccc6376058e251315b4de7e085b9-Abstract-Conference.html
2. Li et al., **Trustworthy Policy Learning under the Counterfactual No-Harm Criterion**, ICML 2023. https://proceedings.mlr.press/v202/li23ay.html
3. Wu et al., **DISCRET: Synthesizing Faithful Explanations For Treatment Effect Estimation**, ICML 2024. https://proceedings.mlr.press/v235/wu24n.html
4. Straitouri et al., **Controlling Counterfactual Harm in Decision Support Systems Based on Prediction Sets**, NeurIPS 2024. https://proceedings.neurips.cc/paper_files/paper/2024/hash/e9e3e5bdb017bbc887271c6f6de5353f-Abstract-Conference.html
5. Ren et al., **Robots That Ask For Help**, CoRL 2023. https://proceedings.mlr.press/v229/ren23a.html
6. Angelopoulos et al., **Learn then Test**. https://arxiv.org/abs/2110.01052
7. Angelopoulos et al., **Conformal Risk Control**. https://arxiv.org/abs/2208.02814
8. Khan, Poupart and Black, **Minimal Sufficient Explanations for Factored MDPs**, ICAPS 2009. Retain the verified original citation from the existing manuscript.

Keep the current RESCUE and DA-GRD comparisons, but independently pin their author versions before making a claim about their full scope. In this review the primary arXiv full text was not retrievable, so their full methods are not newly certified as reviewed. Do not substitute an AI-generated summary for a primary text.

**Important correction:** no-harm policy learning and harm bounds from unpaired data already exist. This extension must NOT claim their invention. General minimum sufficient explanations, robust optimization, interval propagation and exact binomial tests are also established.

The proposed distinction to investigate is narrower:

> DSRE synthesizes compact, obligation-specific robot recovery certificates that distinguish which claims follow from paired trials, randomized single-action logs, or incomplete evidence, and returns concrete missing-information witnesses that guide the next useful evaluation or observation.

A generic outcome-aware rule plus the identical bound may reproduce its action choices. That equivalence must remain explicit. The additional scientific value must be demonstrated through correct source-dependent qualification, explanations, and a reduction in unnecessary evidence collection or uninformed repairs, not claimed from a new name.

## 3. Precisely address the deployment question

A deployed robot executes ONE selected action. It does not observe both counterfactual futures. Offline calibration can legitimately use paired simulation, but applying a simulator-derived bound to a physical robot requires a justified transfer model or external validation.

We therefore separate three evidence regimes:

**P: Paired execution evidence.** Both fixed actions are executed from a qualified reproducible simulator checkpoint. This identifies a joint binary outcome table under that deterministic experimental model. Shared simulator seeds in a stochastic model do not automatically identify a physical real-world coupling; state this limitation.

**L: Randomized single-action logs.** For each independent checkpoint, an action is assigned using a known randomized behavior rule and only its observed outcome enters training/calibration. This permits identification of conditional action-success marginals under consistency, overlap, and randomized assignment. No paired branch is needed by the estimator.

**O: Arbitrary observational logs.** Actions may depend on hidden variables. Unless conditional exchangeability or an explicit sensitivity model is justified, the estimator does not assume causal marginals are identified. Return insufficient evidence. A powerful predictor is not a substitute for this assumption.

The first deployable-evidence experiment covers L. O with hidden confounding is a negative/assumption stress test, not a claim that we solve unobserved confounding.

Simulator pairing is retained as an independent evaluation oracle. In a masked-log test, the learner, rule selector, calibration code, cost selection, and feature selection must never access the hidden branch. A separate evaluator can score actual harm, rescue and futility afterwards. Name this a simulated logged-data study, not real-robot validation.

## 4. Mathematical core

Let X be the declared observable predecision context; a0 the continuation baseline; a a recovery action; Y^a in {0,1} its potential terminal success. Fixed controllers, horizon and success semantics are part of the context.

For a fixed evidence region E, define:

- p0(E) = P(Y^a0=1 | E)
- pa(E) = P(Y^a=1 | E)
- h_a(E) = P(Y^a0=1, Y^a=0 | E), binary outcome degradation
- g_a(E) = E[Y^a - Y^a0 | E], expected success improvement
- k_a(E), measured or externally fixed incremental intervention cost in a declared unit.

**Known sharp bound, inherited from counterfactual partial identification:**

max(0,p0-pa) <= h_a <= min(p0,1-pa).

The mean gain g_a = pa-p0 is identified by the marginals. Harm generally is not. The interval for harm remains even with infinite unpaired data; it is not a confidence interval.

For example p0=.4, pa=.6 allows zero harm or .4 harm while preserving the same mean improvement of .2. Two compatible joint distributions are q=(.4,.2,0,.4) and q=(0,.6,.4,0) ordered as q00,q01,q10,q11. This is an analytical counterexample, not a robot result.

Conversely, p0=.05, pa=.70 implies h_a <= .05 from marginals alone. Paired replay is not necessary for every non-degradation certificate.

### Evidence ambiguity sets

Construct Q_D(E), the family of joint outcome distributions consistent with the explicitly available evidence D, assumptions, and simultaneous finite-sample bounds. With two binary outcomes this is a polytope in four nonnegative masses q00,q01,q10,q11 summing to one:

p0=q10+q11; pa=q01+q11; harm=q10; success gain=q01-q10.

Paired observations constrain joint probabilities. Unpaired randomized observations constrain marginals. Confidence intervals add sampling uncertainty; absent overlap or confounding assumptions add uncertainty or make the claim unsupported. These mechanisms must not be merged into a single undocumented confidence score.

The proposed certificate tests:

sup_{Q in Q_D(E)} h_a(Q) <= alpha,
inf_{Q in Q_D(E)} [g_a(Q) - lambda k_a(Q)] >= eta.

alpha is the declared harm-risk tolerance; eta is the minimum useful improvement; lambda is a prespecified cost conversion. Report measured time/action counts and the full cost sensitivity instead of choosing lambda to make DSRE look good. A harm-only certificate permits futile interventions; a useful-intervention certificate requires the additional benefit condition. Both can be reported with distinct names. The current manuscript's historical harm-only results stay unchanged.

A success-obligation certificate replaces the harm constraint by sup_Q P(Y^a=0) <= alpha. These are alternative requested obligations, not newly discovered error events.

Candidate evidence E is a conjunction of actual observed facts. Search a small fixed vocabulary for minimum |E|, subject to these obligation-specific constraints and adequate support. Task identity, hidden fault family and future outcomes are not selectable explanatory facts.

### Statistical validity of explanations and action routing

The desired claim is about a declared population/region, not a probability of safety for an individual episode. Reusing the calibration set to choose whichever of many rules happens to pass invalidates naive guarantees.

Implementation must choose ONE of two explicitly proved designs:

A. Freeze a complete router on discovery data, define its actual disjoint routed decision regions, and construct valid bounds on those regions using separate data. The explanatory certificate refers to its actual routed scope, including exclusions needed for membership. Do not claim a broad conjunction has a risk guarantee merely because a selected subset has one.

B. Freeze a finite atomic context partition. Obtain simultaneous confidence sets for each supported atom. Require the certificate bound to hold for every compatible atom. A deterministic policy depending only on that declared atom can then select among passing actions without changing the bound. This is stronger and potentially more conservative; unknown atoms cause abstention. Any finer side information used for routing must be included in the partition.

Use A as the initial low-complexity implementation, with exact scope represented explicitly and minimum explanatory subsets verified against the atomic partition; independently check its assumptions. Do not obscure the distinction between an economical display and the actual scope of its statistical claim. If the wording cannot honestly refer to E alone, use certificate=(E,scope,obligation,bound) and make scope visible.

Formal results must be checked by the supervisor before calling them proved. Statistical confidence sets and population model ambiguity are different. A union bound or Fréchet bound is not new theoretical work.

## 5. Theory deliverables that test substance

1. **Scoped soundness:** state conditions under which Q_D contains the true conditional joint law with probability at least 1-delta, and prove that passing the stated worst-case constraints yields the corresponding population bounds. Address the actual selected router, not hypothetical unselected rules.
2. **A sharp certifiability boundary:** show precisely when harm can be certified from marginals, when paired/structural information is necessary, and when no additional marginal samples can settle the claim. For exact two-arm marginals this is the known bound; the proposed contribution is its integration with evidence minimization and missing-evidence witnesses, not the inequality.
3. **Constructive non-identification witness:** return two admissible outcome tables with identical available observations/marginals but different obligation verdicts. A noisy estimate or empty cell is not such a witness.
4. **Minimum-evidence check:** exact search over a fixed predicate dictionary, with countermodels or feasibility failures when retained facts are removed. Minimum cardinality, minimum cost, and subset-minimality must be distinguished.
5. **Evidence refinement:** adding valid constraints on the same target distribution cannot enlarge Q_D. Changing sensors, behavior populations, or conditional regions is not automatically such a refinement; do not assert monotonicity across different estimands.

If all mathematics is an immediate restatement of known results, acknowledge it. The work can still have a methodological and robotics contribution, but should not be advertised as a new theory paper.

## 6. Experiments organized by the central claims

### E1: Paired versus unpaired identification, existing data first

Use the sealed existing paired datasets for DEVELOPMENT. They have already been inspected, so no new holdout claims.

For a fixed random schedule, hide one outcome per parent-checkpoint from all learner inputs. Primary episode analysis uses one preselected condition per independent parent to avoid pretending all five conditions are independent trials. A separate parent-cluster analysis may use all conditions, but must not silently reuse an episode risk bound for parent-any-condition risk.

Compare: paired oracle estimator; single-action estimator with partial-identification bounds; an explicitly labeled naive independence-coupling plug-in; outcome regression; same harm-bounding engine with all features instead of minimum evidence; and outcome-aware rules under identical gates. Compare equal independent-parent budgets AND equal executed-action budgets, since pairs contain more observations.

Measure harmful authorizations, valid recommendation coverage, required rescue, cost, certificate length and unresolved width. Include a setting where marginals alone suffice and another where compatible couplings prevent certification. Constructed tables are tests of logic; actual robot data test relevance.

### E2: Two genuinely different robotics domains, then a third

Target three mechanisms, not ten visually similar benchmarks:

1. Existing PickCube grasp recovery: retain all historical regimes as the anchor.
2. **PegInsertionSide-v1**: contact/alignment-sensitive assembly. Official ManiSkill has a task card and a released Panda motion-planning solution with approach, alignment refinement and insertion. Reuse the cached insertion macro versus the source's refinement-and-insertion macro, after independent qualification. No learned recovery controller. Controller source uses simulator poses; any modelled pose-estimate interface and privilege must be declared identically for all selectors. This action pair is a proposed adapter, not already validated.
3. **PointMaze navigation in Gymnasium-Robotics/MuJoCo**: progress/route-sensitive navigation with fixed path tracking versus fixed map-based replanning using the same declared information. This is a 2-DoF point-agent navigation abstraction, not a full mobile robot. It adds mechanism diversity, not hardware realism. Controller implementation is small and belongs only to the evaluation harness; it must be frozen before method comparison.

Official environment documentation:
https://maniskill.readthedocs.io/en/latest/tasks/table_top_gripper/index.html
https://robotics.farama.org/envs/maze/point_maze/
Verified source: mani-skill/ManiSkill, mani_skill/examples/motionplanning/panda/solutions/peg_insertion_side.py. Pin a commit; do not upgrade the existing qualified simulator environment in place.

For each new task: a bounded fixed 10-parent development pilot tests source availability, episode semantics, controller execution, sensor availability and action diversity. Do not rotate among tasks until finding a favorable DSRE score. All pilot outcomes remain development. Failed source qualification is reported and stops that task, not the method program.

First Stage 1 breadth goal: existing grasping plus at least one complete non-grasp task and a qualified small pilot in the other. All three full studies are preferred but not guaranteed feasible. A broad claim is not allowed if only cube perturbations succeed.

### E3: The actual one-action execution interface

Collect a separate small set in which the randomized behavior policy genuinely executes only one action per initial state, stores propensity, observation and that outcome, and never uses a cloned paired branch for learning. Fit certificates from those logs, freeze the router, then execute it on new states. Pairing can be done in an isolated evaluator to validate harm, but must be unavailable to the learner and not a runtime prerequisite.

Randomization or an explicit unconfoundedness assumption is necessary. On arbitrary confounded logs, return insufficient identification rather than silently output causal confidence. Simulation-only evidence does not prove sim-to-real transfer. We remove the paired-data requirement of the method, not the remaining external-validity gap.

### E4: Equal-standard baselines

The same frozen features, action repertoire, discovery/calibration/test splits, assignment propensities, interval construction and gate must be available to:
- CART or an ensemble outcome predictor with the exact same obligation test;
- same-grammar ordinary sufficient rules / B7;
- Li et al. ICML 2023 no-harm policy method or a precisely documented adaptation;
- DISCRET-style outcome explanation as a distinct baseline, never a claimed full reproduction without its method;
- a Learn-then-Test qualification layer matched to the same estimand, with multiplicity handling;
- a direct partial-identification estimator following Kallus (exact tabular version acceptable if declared);
- always-continue, always-recover, and cost-aware empirical outcome selection.

A standard conformal risk-control procedure cannot directly use unobserved harm labels. It needs the same valid bound/surrogate assumptions. Likewise LTT does not identify counterfactual events by itself. Do not stack incompatible confidence claims or rank methods using different target risks.

Matching gate does not force equal action assignment counts. Report natural proposals, balanced collected evidence, and shared-proposal controlled comparisons separately. CART must not lose solely because it receives fewer calibration assignments; show support-controlled sensitivity or disclose an underpowered comparison.

### E5: Witnesses that change a useful decision

Distinguish four actionable diagnoses: observation aliasing; finite sample uncertainty; missing joint/counterfactual information; inadequate action repertoire. The first three support different interventions in the DATA pipeline, not invented changes in the physical robot.

Predeclare a limited offline repair menu: add a recorded predecision channel; reveal more random single-arm logs; acquire paired simulator outcomes for a preselected subgroup. A fourth existing skill may be evaluated later only if already executable and properly recorded. Compare witness-guided allocation against uniform additional-data allocation, generic entropy and a strong decision-aware uncertainty heuristic at equal actual acquisition budgets.

The outcome is additional valid coverage/decision benefit per evidence unit, not number of diagnostic labels. The hidden evaluator may verify the diagnosed obstruction but cannot guide the selection. This is the most direct test that certificates are operationally useful rather than cosmetic explanations of the same decisions.

## 7. Reviewer objections that should be addressed before writing

**Tautology:** the primary experiment becomes what evidence can identify and certify an obligation, not the fact that harm is a subset of failure. The 38-rescue result remains supporting evidence, not the whole thesis.

**Deployment:** paired outcomes are optional training evidence, not a runtime oracle; randomized one-action logs and valid partial-identification bounds provide the initial route beyond replayable data. No unjustified transfer to real hardware.

**Known mathematics:** acknowledge classical bounds and rule synthesis. Demonstrate minimum obligation-specific facts, explicit identification witnesses, and experimentally useful evidence repair. Avoid novelty by vocabulary alone.

**Weak baselines:** give the same gates, risk target, feature access, data and baseline tuning budget. Report both natural assignment and matched-support comparisons.

**Narrow tasks:** task diversity must mean distinct physical decision mechanisms. Five offsets are not five tasks. PointMaze must not be dressed up as a realistic mobile robot.

**Unhelpful abstention or futile recovery:** report vector outcomes and measured costs. At least a prespecified positive benefit requirement must be available; report sensitivity to cost conversion instead of one favorable scalar weight.

**Finite-table certificates:** distinguish exact table support, statistical confidence, identification assumptions and distributional scope. Correct facts are not a physical safety proof.

**AI-assisted review:** the manuscript should be readable and internally consistent for any reviewer. Do not assume most reviewers use AI, attempt prompt injection, or hide adverse comparisons. No review system can be made rejection-proof.

## 8. Figure 1 specification

A single thesis-and-method figure, with two visually separated rows:

**Offline evidence row:** paired simulator trials OR single-action logs -> evidence/assumption model Q_D -> obligation-specific certificate synthesis -> frozen selector and calibration.

**Online robot row:** available observed facts -> matching qualified certificate -> execute ONE selected action OR defer with a concrete witness.

Right-hand inset: same action marginals, two admissible joint worlds, different harm. Show a certificate that is possible under one evidence regime and unresolved under another. This makes the conceptual change visible, rather than showing a bag of independent modules.

The caption must explicitly say that counterfactual outcome pairs, where used, are offline; no robot executes both actions at decision time. Baselines and evidence regimes use consistent symbols. A one-arm deployment trace and evidence-budget frontier should support the figure experimentally.

## 9. Stage 1 and Extension Charter plan

RSS's current reviewer rubric scores **Value of Hypothesis** and **Feasibility of Conclusion**, each from 1 to 4. Merely accumulating experiments does not raise the first score. A vague promise of real-robot experiments does not raise the second.

Minimum evidence before an ambitious Stage 1 claim:
- rigorously defined Q_D and obligation-specific certificate semantics;
- checked non-identification and validity arguments with assumptions;
- implemented paired/unpaired experiments with source isolation;
- at least one complete physically different additional task;
- a matched-gate strong baseline comparison;
- at least one witness-guided data or observation repair experiment;
- stated sample/support limits and achievable effect precision.

If these do not materialize, the assessment remains bounded. More optimistic prose cannot substitute.

Propose an Extension Charter menu, not an assumed negotiated contract:
- locked primary theorem and independently checked assumptions;
- three specified task families with frozen interface, controllers and failure distributions;
- complete single-action-logging validation and bounded shift sensitivity;
- equal-budget baselines and witness-usefulness ablation;
- prespecified supported/refuted interpretations and release of minimal reproducible artifacts.

The AC and reviewers set the charter and may request different experiments. We can make a feasible scientific plan legible, but cannot compel the charter or guarantee final acceptance. Do not make real hardware a prerequisite unless access and the actual experiment are secured. No manuscript should contain internal submission logistics.

## 10. Calendar and finite commitment

- **17-19 November:** finish the formulation, nearest-work matrix, four-cell bound solver, independent verification, and paired-to-unpaired existing-data study. Independently qualify the insertion and navigation adapters in parallel where infrastructure permits.
- **20-23 November:** complete one non-grasp pilot, prototype single-action logs and a matched-gate comparison. This is the substantive expansion checkpoint; no unrelated topic may be substituted.
- **24-27 November:** freeze methods; execute bounded independent confirmation and evidence-repair comparisons. Fix sample allocations from observed development variance and expected accepted support BEFORE outcomes, not from a target significance result.
- **28 November-2 December:** write the Stage 1 argument around verified claims and complete an adversarial review against the actual RSS rubric.
- **3 December:** final format, source, anonymity and numbers checks.
- **4 December:** manual submission decision by the author.

No guarantee is made that all proposed task adapters will qualify. If one fails, report it; never continue replacing tasks until a gain appears. The core problem does not change. Data already inspected become development for this extension and remain untouched as historical records.

## 11. First Codex session: bounded implementation, not delegation of research

Codex implements this supervisor-defined formulation; it does not select a new contribution, choose convenient assumptions or proclaim novelty.

Authorized first session, maximum 8 hours wall, no new large physics campaign:
1. Preserve exact branch and all user changes; create `research/dsre-evidence-regimes` from verified current history.
2. Implement a four-cell LP and analytical bounds with an independent enumerated oracle. Include explicit source-evidence and assumption metadata.
3. Test 441 marginal pairs on a 21x21 grid and both analytical indistinguishable worlds. These checks were already numerically verified in the supervisor environment to <=1.2e-16 absolute error; they are sanity tests, not experimental novelty.
4. Implement paired and randomized one-action data views from existing DEVELOPMENT archives with hard learner/evaluator separation and one preregistered condition per parent.
5. Run evidence-regime and equal-gate baselines, provide candidate explanation/obstruction examples, and identify which formal guarantee is actually proved versus pending.
6. Qualify at most the frozen 10-parent development pilot for each named new task, with isolated environments, full-prefix parity where applicable, no policy tuning against DSRE outcomes, and exact source hashes.
7. Produce research-only method/results/nearest-work/prospective protocol files and a compact independent audit.
8. Commit locally without editing either manuscript, publishing, or submitting. Git credentials never block completion.

Do not turn this into another broad search. Do not train a foundation model or learn a new recovery controller. If source assumptions fail, label the exact inference unsupported and complete all independent components. The supervisor owns the hypothesis and next scientific decision.

## 12. Independent numerical audit attached to this plan

The classical two-arm harm interval was checked against a four-variable linear program for all 441 pairs p0,pa on a uniform 21x21 unit grid; maximum absolute discrepancy was 1.11e-16. The two same-marginal worlds both have p0=.4,pa=.6,expected gain=.2, but harm 0 and .4 respectively.

In an exploratory reread of the OLD dual-obligation calibration archive, the 106 checkpoint-level DSRE recovery proposals have outcome counts (continue-only, recover-only, both, neither)=(0,96,1,9). Their empirical marginal-only sharp harm interval is [0,1/106]. This is a finite empirical distribution calculation, NOT a new calibrated risk bound, not an independent result, and not interchangeable with the registered 64-parent simultaneous bound. It suggests that a one-action-data question is testable in existing evidence; it does not establish successful learning from genuinely unpaired logs.

Official RSS sources:
https://roboticsconference.org/information/cfp/
https://roboticsconference.org/information/author-faq/
https://roboticsconference.org/information/reviewer-guidelines/

Retrieval note: the direct CFP endpoint sometimes returned an older cached RSS 2026 page, while current official indexed CFP, reviewer guidelines and FAQ clearly described RSS 2027. Apply the current year-specific rules, and recheck live content before submission. PDF screenshot calls for three relevant primary papers failed in this tool environment; no visual/table-dependent assertions were taken from those failed screenshots.
