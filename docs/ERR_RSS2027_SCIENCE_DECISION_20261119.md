# RSS 2027: scientific repositioning and definitive methodology test

**Supervisor decision, 19 November 2026**  
**Status:** A bounded, falsifiable **methodology extension proposed for validation**, not an established new robotics result or guaranteed RSS acceptance.  
**Parent project:** Decision-Sufficient Recovery Explanations (DSRE). No new controller, no new physics requirement for the first prototype. Preserve all sealed experiments, including exact baseline equivalences.

## 1. Research decision, not another exploration cycle

The current V5 manuscript, *When Does Evidence Justify Robot Recovery?*, is mathematically sound within its scope and has qualified grasp/push preliminaries. Its fatal potential review is that B7 rules equipped with the same outcome constraints, witness logic and calibrated scopes reproduce every certificate. One cannot make that risk disappear by prettier prose. The RSS 2027 semi-complete Stage 1 encourages important technical hypotheses and a complete prospective methodology, not a leaderboard win. It does **not** waive the obligation to explain a meaningful technical distinction from prior work.

**Decision:** Keep the proven DSRE authorization certificate as the foundation; extend its scientific *output* from a yes/no intervention certificate to **the minimum identifying experiment when authorization is undecidable**. Call the extended research question **Evidence-Resolving Recovery** (ERR), with DSRE the certificate subroutine. This is one question, not a bundle of unrelated methods:

> For a specified recovery requirement, what observations and intervention experiments are sufficient to decide whether recovery is justified, and what is the least additional evidence capable of settling an unsupported claim?

The word **decide** includes establishing that recovery is **not** justified. An identifying experiment does not promise to make an unsafe skill safe or to yield a positive certificate. The extension is justified only if Codex can implement it rigorously and demonstrate an output that is absent from the original baseline and not already solved unchanged by one of the closest papers. If no concrete distinction survives, do not conceal this outcome or silently relabel the original DSRE.

Why this is more substantial than adding more risk thresholds: the present DSRE takes an experiment design as given and decides an action. ERR takes a **declared menu of available evidence-generating experiments** and returns a checkable choice of experiment or a formal impossibility witness, with a minimum-cost criterion. The core technical idea is **obligation-aware experiment identifiability**.

## 2. Nearest method boundaries grounded in current literature

- **UPS, RSS 2026, Yuan et al., _When to Act, Ask, or Learn_**: Calibrated policy steering chooses among action, language clarification and retraining from semantic and action-feasibility uncertainty. OUR proposed additional target is distinguishing **causal joint-outcome identification** from missing sensing and statistical support, with explicit experiment-source provenance and a countermodel pair. Do **not** claim we invented act/ask/learn or abstention. https://arxiv.org/abs/2602.22474
- **Merker, Walker and Bobu, RSS 2026, _Robots That Know What to Ask_**: Detects underspecified reward features and requests targeted demonstrations. Our evidence object is a **joint intervention-harm obligation** rather than reward feature uncertainty. Do **not** claim we invented explanation-guided acquisition. https://roboticsproceedings.org/rss22/p116.html
- **AgentChord, RSS 2026**: Proactive recovery branches, task graphs and physical execution. Our object is what a fixed-action evaluation source can warrant, not recovery-controller design. https://arxiv.org/abs/2605.11951
- **RESCUE, October 2026 preprint**: Same-checkpoint action/continuation comparison and evaluation of alarm intervention value. We cannot claim counterfactual physical branching is new; ERR asks **which additional experiment could resolve a currently unidentifiable recovery obligation**, with explicit observational distinctions. https://arxiv.org/abs/2610.13516
- **Kallus, NeurIPS 2022** and **Li et al., ICML 2023**: Counterfactual harm bounds, no-harm policies. Identifiability maths is inherited. https://proceedings.neurips.cc/paper_files/paper/2022/hash/666cccc6376058e251315b4de7e085b9-Abstract-Conference.html ; https://proceedings.mlr.press/v202/li23ay.html
- **DISCRET, ICML 2024**: Rule-based causal outcome explanations. An instrumented rule with our identical experiment-synthesis procedure is a **fully matched implementation**, not a different result. https://proceedings.mlr.press/v235/wu24n.html
- **Wen et al., ICML 2025, _Enhancing Treatment Effect Estimation via Active Learning_**: Counterfactual-coverage-driven acquisition. ERR must distinguish *identifiability of a named obligation and experiment class* from generic treatment-effect estimation/sample efficiency. https://proceedings.mlr.press/v267/wen25b.html

**Claim of novelty to challenge:** conditional experiment-type resolvability for *robot recovery obligations* jointly over observable regions and intervention data, with minimal distinguishing experiment and proof/check of unresolvable claims. **Not** a new Frechet bound, set-cover solver, generic active learner, or uniquely better policy.

## 3. Formal object and two different mathematical levels

We retain fixed macros `continue` and `recover`, terminal outcomes `(Y0,Y1)` and predecision observations `X`. For a declared region `S`, a joint potential-outcome law `Q` induces the binary task harm `h(Q)=P(Y0=1,Y1=0|S)`, gain `g(Q)=E[Y1-Y0|S]`, and obligations such as

`phi(Q)=1{h(Q)<=0.10 and g(Q)>=0.05}`.

Existing outcome evidence `D` and declared source assumptions specify a candidate family `M_D`. With independent calibration, the existing DSRE certificate warrants recovery only when `phi(Q)=1` for **all** `Q` in its simultaneous valid confidence/identification set on the stated region. A proposed new evidence-design stage must NEVER remove that conservatism. If the true `Q` is unknown, the method can say `CERTIFIED`, `REFUTED`, or `UNRESOLVED` (for confidence/support or identification reasons). An empty or invalid model set is a source error, NOT authorization.

### 3A. Population identifiability, an idealized structural question

Fix a finite candidate-world set `M_D` for an analytical proposition. A possible experiment `e` has a **declared data-generating law** `L_e(.|Q)` for each candidate world `Q`. Examples are a new predecision observation channel, an independently randomized single-action trial, or a qualified paired simulator trial. An evidence plan `E` distinguishes worlds of opposite **obligation verdict** if

`forall Q,Q' in M_D with phi(Q) != phi(Q'), exists e in E with L_e(.|Q) != L_e(.|Q')`.

A minimum-cost *resolving experiment plan* is

`E* in argmin_{E subset E_menu} sum_{e in E} cost(e)`

subject to the preceding condition. The cost denotes experiment **types**, not a statistically verified minimum number of noisy real trials. When no plan in the declared menu separates an opposite-verdict pair, that pair is a **constructive impossibility witness** for the menu.

For a finite `M_D`, construct the bipartite opposite-verdict pair universe. Each available experiment covers exactly the pairs whose ideal data laws differ. The minimum plan is therefore a weighted set-cover instance. Exact enumeration/MILP can solve small menus. This algebraic reduction is basic combinatorial optimization and is NOT claimed as a new theorem. The scientific content is the recovery-obligation-specific world model, evidence-source semantics and task-relevant experiment contract.

**Population implication:** a paired trial can identify counterfactual harm when action marginals cannot. If the data remain unpaired, two worlds with `p0=.4`, `p1=.6` and respective harm `0` and `.4` are observationally indistinguishable for any number of ideal randomized single-arm trials. Their population joint distributions differ and can be distinguished in principle by properly coupled paired trials. The experiment may reveal recovery is unsafe rather than certify it.

### 3B. Finite-sample statistics, a separate implementable procedure

A statistical decision procedure must use independent discovery and calibration, source-correct outcome models, declared support, and simultaneously valid confidence sets over the actual routed regions. A structural signature difference does not imply enough information is available in `n=64` or `n=1024` samples. A learned plan must not use a held-out oracle or collect outcomes adaptively and reuse them as iid calibration data. The initial ERR theorem applies to a fixed finite world catalogue **only**; population deployment validity remains the existing conditional DSRE argument if its assumptions hold.

**No strong statistical claim about a continuous universe of worlds follows from discretizing it.** Analytic examples are proof-of-concept, while robotic pilots must use qualified traces and registered denominators. If fitted world lists are incomplete, the planner cannot assert that no other worlds remain.

### 3C. Observation acquisition is not simply extra data on the same estimand

Measuring a new fact changes the conditioning partition and can change the conditional intervention law. It is not merely intersecting two confidence sets on the original `S`. Sensors, log design and adding a new recovery skill are different operations. A new skill changes the action set and requires new matched evidence, so skill expansion is **not** treated as an identifying experiment for the old `(Y0,Y1)` law. Distinguish `NOT_IDENTIFIABLE_WITH_MENU` from `KNOWN_FIXED_REPERTOIRE_FAILURE` and from `SOURCE_OR_STATISTICAL_SUPPORT_MISSING`.

### 3D. Executable outputs

At each authorized predecision region, ERR emits exactly one of:
1. `CERTIFIED_RECOVER(visible_observation_subset, region, named_obligation, source, bounds)`;
2. `UNRESOLVED(experiment_plan, its declared cost, separated opposing worlds, assumptions)`;
3. `NOT_RESOLVABLE_WITH_MENU(opposing-world counterexample)`;
4. `REPERTOIRE_INADEQUATE(witnessed paired checkpoint, fixed skill family)` or `SOURCE_UNSUPPORTED`, without inventing a promise of action success.

Online, the robot performs only the selected fixed action; data collection and paired evaluation are offline plans, not simultaneous online futures.

## 4. Falsifiable RSS hypotheses and evidence

**H1, intervention evidence:** Identical action-success marginals can leave binary harm undecidable and, for some declared robot contexts, paired evidence can identify the obligation. The exact **general** non-identification result is established literature; the new research task is to characterize *when* this case arises in robot recovery regions and which source resolves it. Existing one-arm qualified Pick/Push is preliminary evidence of the contrasting log-sufficient regime; there is **no verified physical paired-only region yet**.

**H2, obligation-dependent experiment requirements:** Changing the named obligation can change the minimum observation and evidence design, even for identical fixed recovery macros. Existing retrospective PushCube contrasts provide the concrete observed fact requirement (0 literals for nondegradation / absolute success versus 1 literal for useful recovery); Stage 2 must check whether optimal experiment type also changes with obligation under equal budgets.

**H3, actionable insufficiency:** An identifiability-aware experiment planner can distinguish structural impossibility from ordinary sample scarcity, and identify the cheapest **capable** experiment within a registered finite menu. The exact finite-world oracle and concrete two-world counterexample establish mechanical feasibility; whether this saves actual action-execution cost is **unestablished**. The historical 512-unit acquisition test tied all strategies, so broad efficiency claims are prohibited. A Stage 2 experiment tests whether improvement arises specifically in genuinely nonidentified contexts; a tie would bound the benefit.

These are linked predictions of one problem, not three algorithms. No hypothesis is described as new solely because classical counterfactual theory supplies its algebra.

## 5. Three Stage 1 preliminaries, with truthful status

- **P1, intervention matters:** Independently qualified PickCube single-action learning: 227/256 test completions and 84 necessary rescues among 111 selected recoveries, zero observed selected terminal harms; 27 selected futile attempts. Same actions from fully matched B7, direct bound and CART. Fixed recover harms 32 otherwise-successful parents.
- **P2, a second mechanism and different obligation:** PushCube: 253/256 completions and 126 necessary rescues, zero observed selected binary harms; 128 recoveries with two futile. Same actions from matched rules/CART/direct bound. Retrospective change in obligation changes minimum displayed fact from 0 to 1; fixed recover is nearly as successful and its success comparison is not the headline.
- **P3, evidence can be structurally undecidable:** Analytical, not physical, two-world witness for equal single-action marginals and different counterfactual harm; the exact finite-world planning oracle selects paired evidence and proves an unpaired-only menu cannot decide. This is a method demonstration, NOT new physical generality.

Scientific preliminaries must keep the exact study provenance, sample independence and frozen measurement/trigger assumptions. Do not lead with unspecified average improvement over a strong baseline.

## 6. Feasible Stage 2 experiment, 7 weeks from charter to final paper

**Objective:** test the distribution of four evidence regimes and the cost/benefit of *resolving experiment selection* compared with fixed allocations and source-aware ordinary rules.

- Predeclare 2-3 task families including PickCube, PushCube and one **source-qualified** non-grasp/contact family; fixed macros, decision points, failure/source guards and task outcomes. The third task may be studied only after source and action-diversity qualification on a pilot frozen before outcome comparison. Unqualified insertion pilots are not a successful third-task result.
- Predeclare regions deliberately through task mechanisms or simulation design, **not by searching test outcomes for a favorable pair-only region**. Require regimes with identifiable marginals, potentially unidentifiable harm and observation aliasing; physical prevalences are measured and may be zero.
- Compare (a) DSRE certificate-only, (b) ERR resolving experiment selection, (c) fully instrumented B7 plus identical evidence-plan postprocessor, (d) matched CART+same bound and information, (e) random and cost-aware uncertainty acquisition, (f) fixed always-continue/recover. If (c) ties (b), report implementation equivalence; the method is the scientific experiment-identity problem, not software-source exclusivity.
- Separate a small *pilot/source qualification* from independent frozen discovery / calibration / untouched test. Use identical action-execution budgets and report structural **resolvability** separately from finite-sample certification and actual physical completion. Record harm, rescue, futility, unqualified actions, model-source failures and added information cost. Calibration must not reuse adaptively acquired outcomes without a justified design and uncertainty correction.
- Stage 2 Charter can require stronger alternate tasks, hardware or assumptions; do not guarantee hardware availability or invent a fallback task after seeing confirmation outcomes. The achievable charter should primarily require one independently qualified task, matched acquisition comparison, independent mathematical check and full source provenance.

## 7. Stage 1 page allocation and visual thesis

**Title candidate:** *What Evidence Would Justify Robot Recovery? Certificates and Resolving Experiments*.

**One-sentence thesis:** A robot's recovery decision depends not just on a recovery predictor but on the evidence source capable of answering its obligation; when that source is insufficient, the methodology identifies the cheapest admissible experiment capable of answering the question, or proves that none in the menu can.

Proposed Figure 1 (author-editable PowerPoint design):
- **Panel A: three inputs**: observed predecision facts (robot scene), outcome evidence (randomized one-arm logs / paired simulator trials), named outcome obligation (harm / success / useful gain).
- **Panel B: one inference object**: joint-outcome compatible worlds with two different evidence sources. The two analytically constructed worlds display the same `p_continue` and `p_recover` but different harm. Keep a visible **analytic illustration** label.
- **Panel C: exact output**: if claim holds on all admissible worlds, `RECOVER` + minimum visible facts; else `EXPAND EVIDENCE` + cheapest experiment that separates opposed verdicts; or `IMPOSSIBLE UNDER AVAILABLE MENU`. Dotted offline branch for paired rollout; a solid one-action-only online branch.
- **Thin bottom bar** with verified Pick/Push counts in different mechanisms. Do not imply hardware validation.

Five main pages: (1) scientific problem + thesis Figure 1; (2) outcomes/evidence and requirements; (3) scope-valid certification plus resolving-experiment synthesis; (4) two verified preliminary robot studies + analytical experiment example and strong equivalence; (5) hypotheses/charter protocol and implications. One references page.

### Proposed abstract, subject to implementation and independent review

> A robot may recover from an execution error and still be unable to justify that intervention from the evidence available at decision time. The missing information can concern the robot's observations, the outcomes of alternative actions, or the recovery skills themselves, and these deficits require different experiments. We formulate recovery justification as an obligation-specific evidence problem. Our method first checks whether current observations and logged intervention outcomes warrant a declared success, non-degradation or improvement requirement. When they do not, it constructs incompatible outcome explanations and finds a minimum-cost experiment capable of distinguishing them, or certifies that the available experiment menu cannot. The methodology separates population identifiability from finite-sample qualification and offline simulator pairing from online execution. Preliminary randomized single-action studies in simulated grasping and pushing yield 84 and 126 necessary recoveries, respectively; a constructive joint-outcome example exposes the identification limit of unpaired logs. This frames recovery as a question of both which action to execute and what evidence would warrant it.

The fourth sentence must not be published as an implemented empirical capability until Codex completes the finite-world synthesis and fair comparison in the actual research codebase. Until then this is a proposed technical methodology for Stage 1 with a clearly identified prototype status.

## 8. Hard, fast execution and falsification contract

**Time bound:** 48 hours for implementation/proof challenge and source-grounded dry runs; no new physics. Stop scientific redesign when this is done and produce the actual six-page Stage 1 manuscript. No open-ended dependence on gaining a new result. Use current local working branch; remote GitHub design branches may lag behind the newer local code.

**Must pass before the method enters the Stage 1 abstract as working:** independent implementation returns mathematically correct minimal experiment menus on all registered constructed-world tests, exact source signatures and opposite-verdict witnesses; explicit separation of population identifiability vs finite-sample risk; no model/evaluator leakage; a fully matched reference baseline; and at least one physically sourced observation witness where the method correctly says what additional measured fact would split the unsupported region (without claiming that it guarantees task success). If a physical case is unavailable, report an analytical witness and retain the experiment planner as **proposed Stage 2 methodology** in Stage 1, rather than an achieved robot result.

**Stop conditions:** no new controller, task shopping, stale/source-mismatched data relabels, or post hoc favorable result selection. A B7+identical planner tie is expected and is not hidden; no unique optimizer claim. No paper assertion of guaranteed RSS acceptance. The finished manuscript must be self-contained; RSS Stage 1 excludes supplementary material and all essential method details must fit 5+1 pages.

**Final supervisor judgment at present:** This is a more interesting research target than V5's certificate-only account, but its actual novelty is not yet demonstrated. It is a defensible high-value *hypothesis and test methodology candidate*; it is not a high-confidence submission decision until the 48-hour implementation challenge and independent robotics/causal review are complete.

## 9. Official venue and examples

RSS 2027 official FAQ: https://roboticsconference.org/information/author-faq/  
RSS 2027 reviewer rubric: https://roboticsconference.org/information/reviewer-guidelines/  
RSS 2027 CFP: https://roboticsconference.org/information/cfp/ (in some caches this still serves stale RSS 2026; check the year)  
RSS 2026 accepted paper list: https://roboticsconference.org/2026/program/papers/  

**No fabricated physical results and no suppression of relevant contradictory findings.** Discarding irrelevant research history is legitimate; making an already-tested claim appear untested is not a scientific improvement.