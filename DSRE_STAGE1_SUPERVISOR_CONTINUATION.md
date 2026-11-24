# DSRE Stage 1: Scientific Supervisor Continuation, Version 1.1

**Research target:** RSS 2027 Stage 1 scientific-method and preliminary-evidence package. IROS 2027 or IEEE RA-L remains a possible later venue. **No manuscript or submission action is authorized in this session.**

**Repository:** `/home/imad/Desktop/IEEE-RAL`

**Reviewed local starting commit:** `c5d354f648946a6945b07897f1c5a82961370835`

**Branch:** `research/dsre-stage1-risk-and-observability`

**Existing research:** DSRE Stage 1, registered run `results/dsre-stage1/20261113T144253Z/`; source documents in `docs/` or their original locations. Inspect `AGENTS.md`, `DSRE_STAGE1_RESULTS.md`, `DSRE_STAGE1_GATE.md`, `DSRE_NOVELTY_MATRIX.md`, `DSRE_STAGE1_PROTOCOL.md`, and all sealed input hashes. Do not assume the separate blueprint v1.0 exists: the formal requirements below are self-contained and authoritative for this new bounded follow-up. Preserve the earlier missing-blueprint disclosure rather than fabricating its content.

## 0. Authority and core research question

The principal scientific researcher has fixed this question:

> **What is the smallest observable evidence sufficient to justify a robot recovery action relative to actual outcomes of the available interventions, and how can a robot distinguish insufficient evidence from insufficient recovery capability?**

This question does not change. We are refining the operational meaning of *sufficient* under finite physical evidence, not selecting a new project.

You are Codex. Implement the precisely defined follow-up, run bounded existing-data analysis, audit independently, and hand the decision back to the supervisor. You may not invent another algorithm, vary the simulator fault severities, select a new domain, add a learned controller, train an LLM, write a manuscript, or authorize a fresh physics run. Do not ask for intermediate approval; complete the conditional paths below.

### Already established; do not overwrite or rebrand

1. Paired-outcome prevalence, 422 observations per task: PickCube continue-only 75, recover-only 120, both 204, neither 23; PushCube continue-only 2, recover-only 211, both 204, neither 5.
2. DSRE exact universal-rule decisions equal B7 exact rules and B5 when its rule purity threshold is 1. This is a mathematical equivalence, not an experimental coincidence.
3. Primary cross-fit: PickCube DSRE 203 recommendations/422 with one unacceptable action; PushCube DSRE 0/422. The stump covers more PickCube checkpoints at the same observed unacceptable count. Do not claim model superiority.
4. The six-predicate PushCube representation produces two full observable patterns. Both include states where neither action succeeds. Under the strict universal, absolute-adequacy requirement, no action can be certified on either signature.
5. The saved prospective 200 calibration parents per task predict only approximately 8.53 PickCube recovery assignments and zero PushCube assignments with the frozen strict router. At alpha=.10 and the previously registered four-stratum allocation, 42 *independently assigned* zero-error parents per enabled stratum are required. Do not present the frozen 800-parent plan as sufficient, or run it automatically.
6. Earlier 17 PickCube recovery-only certificates, their literal-removal witnesses, and every negative case must remain intact.

## 1. Fixed formal problem, in executable terms

For observation vector `x` with `d <= 8` declared observable Boolean/UNKNOWN predicates, fixed interventions `A = {continue, recover}`, and paired physical outcomes `V_i(a)`, define the acceptable action set at reference state `i`:

`Good_i = {a in A : V_i(a) >= v and max_b V_i(b) - V_i(a) <= epsilon}`.

For the primary historical experiment, `V_i(a)` is binary terminal success, `v=1`, `0 <= epsilon < 1`. Do not quietly substitute first-hit success, controller identity, fault label, future outcome or inferred physical root cause. Missing physical outcomes are UNKNOWN, not failures.

For a query observation `x`, any evidence conjunction `E` may use only literal-value pairs actually observed in `x`. Conservative UNKNOWN matching remains fixed from v1.0. `Match(E)` includes all reference rows compatible with those literals. Require nonzero support and the frozen minimum support.

**Strict finite-reference sufficiency** holds for action `a` iff `a in intersection_{i in Match(E)} Good_i`. A minimum certificate minimizes literal count, then applies the existing canonical tie-break.

**Crucial equivalence:** in this binary setting the strict procedure is exactly minimum-pure outcome-rule synthesis. It must be described that way. Witnesses and a three-way semantic result are useful interfaces but are not new hitting-set theory.

### Formal observability ceiling

For each **complete observable signature** `z` with `N_z` reference rows, compute

`G(z) = intersection_{i: x_i == z} Good_i`.

If `G(z)` is empty, no fixed deterministic action rule receiving only this exact signature can satisfy universal adequacy on every associated reference row. The finite-reference maximum possible coverage under a deterministic universal-adequacy policy is

`C_max = sum_{z : G(z) != empty} N_z / N`.

Provide a short independent mathematical argument, a direct exhaustive checker, and exact per-task breakdown. Treat this as an elementary characterization, not a claimed new theorem or population ceiling. Extend the code to conservative UNKNOWN compatibility where appropriate; label the distinction between exactly equal observed patterns and compatible incomplete patterns.

Decompose blocked signatures with actual witness records:

- **Repertoire inadequacy:** at least one compatible reference row has `Good_i = empty`. No available action is adequate in that row.
- **Action ambiguity:** two compatible rows have nonempty but disjoint `Good_i`. A common decision is impossible under that signature.
- **Evidence/support insufficiency:** the candidate explanation is missing, its reference support is below the registered minimum, or the query signature is unseen. This is not automatically a physical incompatibility.
- These classes may overlap. Report overlap rather than forcing a misleading exclusive cause.

Also compute a best-case *non-universal* accuracy/coverage diagnostic for each full signature, with its true number of unacceptable actions. Never call it a certificate or deployment guarantee.

## 2. The ONE permitted methodological refinement: risk-bounded sufficiency

The deterministic strict definition is appropriate for exhaustive symbolic models, but it makes a single empirical `neither` row invalidate an entire observation class. Physical results are statistical observations, not complete descriptions of all future worlds.

Implement a **two-tier DSRE output**, preserving the original strict tier:

**Tier S: STRICT_FINITE_REFERENCE**

Return the original minimum-evidence certificate and literal necessity witnesses only when the universal finite-table condition holds.

**Tier R: PROVISIONAL_RISK_RULE**

Only when Tier S cannot issue a recommendation, select a minimum-length outcome-grounded rule *on training/reference data only*, using the already available B5 rule grammar, identical features and minimum support. Its empirical unacceptable-action rate must be at most a **predeclared development target beta=.10**. Use fixed ties: cardinality, estimated unacceptable rate, higher support, default continue on action ties, canonical predicate order. Also report beta=.05 as a frozen descriptive sensitivity. Never claim the training rule is calibrated or statistically safe.

Freeze the whole Tier S + Tier R **router** before calibration. A future independent calibration cohort, if authorized, could test the entire routed decision policy and separately constrain its action-specific unacceptable rate using exact one-sided binomial confidence bounds. At this stage, only implement and unit-test the calibration module against independent synthetic arithmetic cases; no genuine calibration occurred.

If the result is a provisional rule, output status `PROVISIONAL_UNCALIBRATED`, not `CERTIFIED`, `SAFE` or `DEPLOYABLE`. No simulator actions may be commanded using an uncalibrated recommendation.

**Tier U: INSUFFICIENT**

When neither previous tier qualifies, return the relevant inadequacy, ambiguity, missing-evidence and support witnesses. For the planned deployed interface, if a future calibration gate rejects an action-specific stratum, it becomes `CALIBRATION_INSUFFICIENT`; do not reroute it to a different action after examining calibration outcomes.

This is ONE mechanism: intervention-grounded minimum explanations with strict-vs-statistical claim strength and explicit insufficiency. Do not invent alternative risk scores, sequential monitors, active tactile probes, new source data, additional recovery skills, or complex learned state models.

### Fair baselines

All baselines must receive the same reference rows, six primary observable predicates, intervention outcomes, action choices and support rules:

- B7 exact pure rule, including its known equivalence to Tier S.
- B5 same-grammar outcome-aware minimum rule at beta=.10, same canonical ties and reference size; this is the crucial competitor for Tier R. If Tier R is exactly B5, disclose the equivalence in results and novelty conclusions, not just in footnotes.
- CART stump, depth2 and depth3; include action acceptability and abstention output, with same threshold training only.
- Full-signature empirical action selector, without claiming a certificate.
- Always continue and always recover.

Separate the three questions: **(a) empirical decision quality, (b) certificate status, and (c) explanatory length/witnesses.** Never compare a strict method at zero tolerated reference errors to a 10% empirical-risk rule and call the latter better or worse without showing the different validity criteria.

All calibration wrappers shared by comparable methods. The joint coverage/error frontier, rather than only raw acceptance count, is the primary plot.

## 3. Exact bounded work packages, in order

### A. Scientific reconciliation and frozen specification

Read the uploaded v1.0 contract stored in the repository; identify differences between the prior frozen statement and the present follow-up. Do not invent the absent separate blueprint. Write `docs/DSRE_V11_METHOD_SPEC.md` containing the precise mathematics, limitations, pseudocode, data schema, output statuses, counterexamples, baseline equivalences and the fixed metrics below. Preserve all original stage-1 files.

Audit data qualification and the prior 844-pair table without refitting new models. Verify the full-signature collision counts from raw qualified pairs and independent implementation. Acknowledge that feature definitions are simulator-provided pose-estimate interfaces, not validated real sensors.

### B. Observatory/identifiability profile

For PickCube and PushCube, and for the existing feature, privileged and coarse observation variants (diagnostic only), produce:

- Exact number of full-signature groups.
- Count and mass of universally adequate signatures.
- Count and mass of inadequate and action-ambiguous signatures; identify overlaps.
- The finite-reference ceiling `C_max` for strict deterministic decisions.
- Explicit paired physical counterexample IDs and two-short-line witnesses.
- False impressions from naive label majority and from ignoring `neither` cases.

Compute robustly using a separate reference implementation and test tables where (i) both actions succeed, (ii) no action succeeds, (iii) identical observations require opposing actions, (iv) no reference matches, and (v) conservative UNKNOWN values prevent spurious certification. Distinguish finite model facts from claims about all deployment states.

### C. Two-tier router development evaluation

Implement the minimal Tier R extension without mutating the Tier S source behavior. Reuse original five parent-group folds and the original data. Add **new development-only** out-of-fold evaluations for beta=.10 with beta=.05 sensitivity, comparing to B5@beta and CART with the same outcome labels and rule support.

Report per task, per action and combined: recommended/abstained, adequate/unacceptable, absolute task success, mean number of literals on recommended decisions, evidence support, strict versus provisional route fraction, false-certification count (a provisional recommendation must never be labeled certified), and mean runtime.

Include error/coverage frontiers with **matched achieved unacceptable rates**. Do not post hoc choose thresholds for a favorable primary result. If no equal-risk point exists, say so. The old pure-rule results remain the registered historical reference, not a model to be relabeled as calibrated.

### D. Calibration and prospective feasibility, no new physics

Implement an independent exact binomial-bound verifier for the frozen router, with zero-assignment, missing-outcome, dependent-parent and rare-action tests. If several task/action strata are checked, allocate and document the confidence error budget explicitly. Only future fresh, independent parent assignments can enable deployment.

Calculate **before** any authorization the new assignment frequencies of the Tier S + Tier R router on the existing parent-group folds, plus sample sizes required at alpha=.10, total delta=.05, four strata; report expected calibration counts under 200 new parents/task and what cannot qualify. Never represent expectation as a guarantee. Do not silently pool four strata or rare actions to make a certification pass.

Do not execute the archived 800-parent seed plan or change its seed manifest. Preserve it as a proposal, not a commitment.

### E. Paper-level distinctiveness assessment

Prepare a **one-page scientific novelty challenge** comparing the precise v1.1 functionality to:

- ICAPS 2009 minimum sufficient explanations of MDP decisions.
- Anchors AAAI 2018 and probabilistic sufficient explanations IJCAI 2021.
- IJCAI 2023 formal explanations of neural/planning policies.
- DISCRET ICML 2024 outcome/treatment-effect rule explanations.
- Learn-then-Test risk calibration, published Annals of Applied Statistics 2025.
- Explainable decision-tree recovery (Peddi/Bezzo 2023), CAPE ICRA 2024 and RESCUE 2026.

State the strongest identity/equivalence and the precise non-equivalent capability, if any. Do not describe known ideas under a renamed title as a theoretical novelty. If all differences are mere output labels/witness formatting, report `METHOD_DISTINCTIVENESS_UNRESOLVED` and give the exact experiments necessary, without starting another topic.

### F. Independent audit and handoff

Produce `docs/DSRE_V11_RESULTS.md`, `docs/DSRE_V11_GATE.md`, and a fresh sealed run under `results/dsre-v11/<run-id>/`.

An audit implemented without importing the main certificate solver must independently reproduce signature ceilings, output classes, all first-rule matches, data splits, group denominators, empirical errors, calibrated/un-calibrated status, and all uncertainties. Include both failed and successful unit fixtures and sample witness verification.

Run relevant tests, complete maintained `pytest -q tests`, Ruff lint and formatting checks. Preserve all negative results and earlier immutable evidence. No manuscript, abstract, latex, PDF, upload, author contact or GitHub push.

## 4. Research gates fixed now

**G0 correctness:** independent exact checks and audit agree; no test leakage. If not, mark BLOCKED; repair implementation defects only without changing definitions.

**G1 observability:** publishable scientific characterization of what the six-predicate observation interface can and cannot justify, with actual witnesses. A simple known characterization is not claimed as a novel theorem.

**G2 selective decision:** risk-tier results improve *useful coverage* compared with strict DSRE on development, with known unavoidable unacceptable-action tradeoffs, but may tie B5. If matched to B5, record exact equality or tradeoff, and do not claim a stronger algorithm.

**G3 practical significance:** exactly compare to two-literal rule and CART. Report where DSRE's claim-strength/status and explanatory witnesses provide functionality unavailable from those vanilla outputs, and where wrappers give the same outputs at the same cost. A convenience interface alone is not enough for a strong RSS claim.

**G4 Stage 1 scientific-readiness judgment:** the supervisor, not Codex, decides whether the method/novelty/motivation/preliminary results can carry a five-content-page RSS 2027 Stage 1 argument. Codex reports `STAGE1_METHOD_CANDIDATE`, `PRELIMINARY_ONLY`, or `BLOCKED` with assumptions and direct competitors. It does not declare acceptance likely.

Do not respond to a failed gate by swapping tasks, making a new recovery policy, changing beta on held-out outcomes, adding arbitrary sensors, training a new architecture or undertaking a new simulator campaign.

## 5. Budget, hygiene and execution policy

Maximum 4 hours wall, 5 measured CPU core-hours, 0 GPU, 0 new physical rollouts, at most 500 MB new outputs and 100 MB network transfer. Use pinned local sealed data and existing Python environment. No paid APIs. Do not spend the full budget if work is complete earlier. Use bounded foreground workers, checkpoint analyses and a final shutdown check.

Respect in-progress user documentation relocations and unrelated changes. Do not reset, overwrite, amend, or stage them. Preserve existing `.gitignore`, `uv.lock`, historical evidence and output seals. Use `.git/info/exclude` for new raw evidence as needed and `git add` only scoped paths. Create scoped local commits; never attempt authentication or pushing.

The final response must contain verified counts, exact feature-signature ceilings, Tier S and Tier R versus strongest baselines, explicit calibration limitations, novelty status, new docs/evidence paths, tests/independent audit, full resource accounting, branch, local SHA and zero remaining workers.

**Begin immediately with scientific reconciliation and exact observability analysis. Complete all authorized phases.**
