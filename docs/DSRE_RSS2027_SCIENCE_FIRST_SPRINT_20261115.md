# DSRE RSS 2027: Science-First Strengthening Sprint

**Supervisor contract | 2026-11-15 | Version 1.0 | Research work, not manuscript work**

Repository: `/home/imad/Desktop/IEEE-RAL`  
Remote: `imadken/IEEE-RAL`  
Verified published starting branch: `research/dsre-rss2027-recovery-evidence-20261115`  
Verified starting commit: `ae63512bade0a10c43514a81743243f157d287a0`

## 0. Scientific mandate and fixed boundaries

**Central problem (unchanged):** What is the smallest observable evidence sufficient to justify a recovery intervention under measured alternative-action outcomes, and what prevents justification when it is unavailable?

Retain the DSRE core: two fixed actions `continue` and `recover`, finite-reference minimum-literal certificates, typed observation/repertoire/reference insufficiency witnesses, and separate population-level risk qualification. Exact B7 is mathematically equivalent to the existing strict solver and ordinary strict-then-B5 rules are equivalent to its risk tier. DO NOT try to manufacture an optimizer win. No new controller, detector, causal model, neural policy, learned perception model, simulation environment, or change to existing outcomes, seeds, calibrations, thresholds or manuscript claims.

**Starting evidence, independently inspected in the 2026-11-15 compact packet:** fresh PickCube test has 160 independent parents, 320 checkpoints, 53 continue-only / 82 recover-only / 165 both / 20 neither; 81 recover-only states were failed starts. DSRE risk provides 229 adequate, one inadequate, 90 STOP, and 11/81 necessary recoveries. B7 risk matches exactly, CART2 risk produces 227 adequate, one inadequate, 92 STOP and nine necessary recoveries. Fresh recovery calibration has 112 independently assigned parents, zero errors, with a 6.239% simultaneous assigned-parent upper bound. Fixed recovery obtains 247/320 successes with 73 inadequate interventions; it does not qualify at the same risk standard. These facts are the immutable baseline. The 112-parent calibration does not transfer to altered observation or fault distributions.

**Deliverable:** a stronger *scientific core*, not merely more data. We need mechanism-separating experiments: physical-action feasibility, observation distinguishability, evidence stability, and independent statistical coverage. The researcher will decide later when to resume editing `rss2027/dsre_stage1.tex`. Do not edit either Stage 1 or full-length LaTeX/PDF in this sprint. Prepare ready-to-insert results and figures instead.

RSS 2027 official Stage 1 deadline: **December 4, 2026, 11:59 p.m. AoE**. The official author FAQ emphasizes rigorous, discriminating hypotheses and technical methodology, even when performance improvements are not universal: https://roboticsconference.org/information/author-faq/ . No supplementary evidence may be relied on for Stage 1.

## 1. Scientific v1.2 extension: measurement-robust decision sufficiency

The existing Boolean evidence interface can assert a threshold predicate even when a 5-mm position error changes its truth value. Build the **smallest possible observation-uncertainty adapter** around existing DSRE; do not replace the solver.

Let `z_hat` be the observed predecision telemetry and `Z(z_hat, rho, tau)` a *declared*, bounded error/timestamp set. For each existing predicate `f_i`, define an invariant value `TRUE` if `f_i(z)` is true for every `z` in `Z`; `FALSE` if false for every `z`; otherwise `UNKNOWN`. Feed only invariant literals to the unchanged DSRE certificate search. An explanation may assert a literal only when invariant under the declared measurement uncertainty. If the set admits both truth values, do not silently pick the nominal truth; return an observation-instability witness and/or abstain.

Implementation must be mathematically sound for **supported** bounds. For a signed x difference with each operand bounded in absolute coordinate error by `rho`, propagate a difference interval of width `2*rho` on each side. For Euclidean distance and cross-frame displacement, use conservative triangle/Lipschitz bounds; document which sensor variables are independently corrupted and which are shared. Distinguish absolute coordinate-wise error bounds from Gaussian standard deviations. Bound joint observation errors across each supporting frame. No simulated sensor error guarantee can be inferred for an actual camera.

Delay/staleness is a different experiment. A timestamped past pose does NOT establish its current value unless there is a justified motion envelope; when none is declared, mark current-state-dependent facts unknown, rather than inventing such an envelope. One can report descriptive delay stress without calling it certified robustness.

**New explanation output (minor schema extension):** measured literals, invariant literals, undecidable threshold facts, minimum certificate if one exists, reason for abstention, source timestamps, measurement-error scope, reference-scope identity, and whether risk qualification covers that sensor regime. Never label an uncalibrated noisy input as population-certified.

**Proof obligations and unit tests:**
- Every asserted robust literal is invariant over its declared measurement set (prove algebraically for provided interval bounds, then independent exhaustive/Monte Carlo checks as regression, not substitute proof).
- `rho = 0` with current fresh telemetry reduces to original v1.1 decisions.
- Increasing a nested error radius cannot turn an UNKNOWN predicate into a newly invariant predicate, given fixed telemetry and timing.
- Missing/ambiguous evidence never masquerades as `False`.
- A reference sufficiency certificate is still only finite-table validity. Measurement robustness is a separate property; population risk is a third property.

Run `rho in {0, 0.001, 0.005}` metres as *bounded-error scenarios*, plus a clearly separate descriptive `5-step` and `250-ms` delay stress. If the raw historical frames do not support those delay cases accurately, report unavailable. Reuse the existing actual paired outcomes when only observations change. Group all corruptions from a parent together.

**Fair comparators:** original DSRE with nominal/perturbed point predicates; a robust B7 using exactly the same invariant/UNKNOWN interface; a robust CART2 that considers all reachable branch completions rather than being given fewer unknown inputs; outcome-aware two-literal rules given the same interface; a simple conservative per-predicate margin rule; fixed continue/recover. If robust B7 matches robust DSRE, report the exact equivalence. Compare jointly on factual assertion validity, adequacy/inadequacy, selective coverage, required-recovery recall, abstentions and average explanation length. Never describe higher STOP as higher physical completion or claim measurement uncertainty has been statistically calibrated on clean data.

## 2. Mechanism analysis: action ceiling, observation ceiling, and selected coverage

For the same qualified paired outcome table `R`, calculate:

`C_action = count of rows with at least one successful action / |R|`.

`C_observation(F) = sum over exact observation-signature classes Z of |Z| if every row in Z has a common successful action, divided by |R|`.

`C_policy = observed adequate selected actions / |R|`, reported with STOP separately.

The first gap `C_action - C_observation` quantifies the finite-reference cost of observational aliasing; `1 - C_action` quantifies repertoire insufficiency; the remaining deployment coverage gap additionally reflects reference support, rule restrictions, and statistical qualification. **Do not interpret these as an additive decomposition of generalization error on different populations.** These quantities are descriptive for a declared table and feature interface; `C_policy` on independent test data is not automatically bounded by a development-table ceiling.

Recompute for PickCube and PushCube at 6 primary predicates, registered +1 Pick predicate, 12 total declared predicates, and sound robust/UNKNOWN versions. Include the source-qualified full-pose diagnostic as an unattainable-information upper bound, explicitly explaining why exact continuous signatures can overfit to singletons. Publish both: (i) genuine witness pairs with conflicting actions, (ii) states where BOTH available actions fail, which no extra sensing can repair. Preserve overlaps among insufficiency types.

Produce one strong, self-contained figure: **intervention feasibility, observation sufficiency, and calibrated selective coverage**, with denominators, task conditions, and support status visible. Cross-check by a second independently written enumerator. Never call an offline hindsight ceiling a deployed policy result.

## 3. Controlled, source-qualified PickCube perturbation study

The source already defines `PickFault(offset_x: float)` and a physically replayed `initial(seed, PickFault(...))` path; the current paper uses only `offset_x = 0` and `+0.02 m`. This gives a low-complexity way to study physically distinct intervention requirements while retaining the exact same robot, task, action prefix, action horizon, skill library and DSRE question.

**Freeze this prospective five-condition matrix BEFORE simulating new outcomes:** nominal `0`, `+0.01`, `+0.02`, `+0.03`, and `-0.02` metres. Keep all existing source names and historical manifests unchanged; implement these as a new *separate, explicitly out-of-distribution* study version, not edits to old definitions. Negative offset has not yet been qualified. The new conditions are not asserted physically valid until the strict tests below pass.

- **Qualification pilot:** 5 fixed independent pilot seed parents per new condition, selected before seeing outcomes. Verify full-prefix replay, contact, controller memory, exact condition application, paired-branch trajectory parity, and no feature leakage. A profile failing qualification remains explicitly unqualified and is not silently repaired by relaxing guards. A source-semantic bug may receive an isolated correction and new immutable pilot attempt, clearly disclosed. No outcome-dependent replacement.
- **Frozen primary population:** 192 *new* seed parents disjoint from every historical, qualification and calibration parent. Split deterministically BEFORE observing any continuation: 64 development/characterization parents and 128 untouched confirmation parents. For each qualified condition, perform both continue and recover from the same predecision state. Maximum if all five qualify: 960 paired checkpoints and 1,920 qualified continuations. All conditions of a seed remain a single statistical parent.
- **No cherry picking:** all qualified conditions and all seeds remain in the denominator. No sampling or retention based on future success. If the negative-offset arm cannot be qualified, preserve the frozen plan and report that arm unavailable; do not replace it with a more favorable perturbation. Do not select severity thresholds after inspecting recover-only incidence.
- **Frozen methods:** original DSRE/B7/B5, CART1/CART2, fixed continue/recover and the new interval-evidence adapter; all receive the same permitted predecision features. Original clean risk gates **do not transfer** to this new source distribution. Report frozen-policy *proposals* and inadequacy descriptively; if a separate risk gate is evaluated, learn and test it using disjoint parents from this new distribution, with a new preregistration, and call it unqualified if assigned support is inadequate.
- **Metrics:** four paired outcome classes; initial failures; recover-only selection/recall; harmful recovery on continue-only states; correct continue selections; both-success maintenance; neither-success deferral; finite observation/action ceilings; selective coverage and STOP; minimally sufficient explanation size; effect of coarsening and sensor noise. Parent-group bootstrap CIs and exact denominators.

The purpose is to test whether the *same* evidence-sufficiency method diagnoses physically different intervention regimes and exposes when information is helpful versus when the fixed recovery repertoire is insufficient. Do **not** present post hoc balancing of outcome classes or a hand-selected set of favorable seeds as representative deployment performance. If the registered conditions remain observationally trivial or nearly all one-action, report the consequence and restrict the claim.

**Resource controls:** maximum 10 hours new qualified-simulation wall time, 4 GiB newly compressed artifacts, 16 hours total session accounting. Checkpoint <=12 parents or <=15 minutes; reserve at least 1 hour for sealing, independent analysis and scientific reporting. GPU use is permitted if it faithfully reproduces qualified physics, but do not introduce model training merely to use a GPU. A corrupted or incomplete physics campaign is worse than a smaller qualified one. Do not change experiment definitions when a result is unfavorable.

## 4. Literature challenge and scientifically honest attribution

Before presenting this as a methodologically distinct contribution, construct a one-page comparison matrix using actual primary sources, not generic claims. At minimum compare:

- ICAPS 2009 *Minimal Sufficient Explanations for Factored MDPs*: minimality of decision explanations is established.
- ICML 2024 *DISCRET*: outcome-aware treatment-effect rules are established.
- IROS 2023 decision-tree monitoring/recovery: interpretability and recovery decision trees are established.
- 2026 DA-GRD, arXiv:2609.29065: task-relevant sensing until executable actions agree is established.
- 2026 RESCUE, arXiv:2610.13516: paired intervention evaluation, including cost and unnecessary recovery, is established.
- 2024 *Interval abstractions for robust counterfactual explanations*, Artificial Intelligence: interval robustness machinery is established.

The potential DSRE contribution is not these individual tools. The scientifically testable combination is **minimum observable justification for physical recovery with counterexample-typed insufficiency and explicit measurement-robustness and risk scopes**. If a paper already solves this complete problem with the same outputs and evidence assumptions, state the overlap precisely. Do not declare unverified first-ever novelty or model advantage.

## 5. Stage 1 science-readiness gates

The end of this sprint should answer, not evade, each of the following:

1. Are original minimum certificates and the new invariant-evidence semantics implemented and independently verified? Can we show examples where a nominal certificate becomes uncertain under plausible sensor error, while robust DSRE does not assert a false literal?
2. Does the new, outcome-blind physical-condition grid produce meaningful differences among continue-only, recover-only, both and neither? If not, what component of the physical task or skill repertoire makes the test uninformative? Include fixed-action competitors.
3. Can we distinguish action-repertoire insufficiency from observation aliasing on real matched simulator continuations? Are the witnesses and finite ceilings correct on untouched parents?
4. Is the tradeoff between justified coverage, required recovery, harmful intervention, sensor uncertainty, and deferral clear and reproducible? Are ordinary robust B7, strong CART, and fixed actions compared without information advantages?
5. What is new at the *problem/methodology* level compared with the closest prior work? What remains an application of established optimization/inference machinery?

The outcome of the sprint is `STRONGER_STAGE1_SCIENCE`, `BOUNDED_STAGE1_SCIENCE`, or `INSUFFICIENT_BREADTH`, with evidence attached. These are internal scientific assessments, **not** predictions or guarantees of RSS acceptance. A negative ablation is valuable only when it discriminates a proposed reason for failure, consistent with RSS 2027's author FAQ.

**Do not produce a manuscript revision in this session.** Save ready-to-insert figures/tables and a clean experimental narrative. After the research gate, the supervisor will authorize the final five-content-plus-one-references-page scientific writing pass. The paper should lead with scientific findings; candid limits belong in methods/results/discussion, not repetitive self-deprecation in the abstract.

## 6. Engineering and reproducibility contract

1. Inspect Git status, origin, exact parent commit, existing worktrees and sealed results; never overwrite or stage unrelated tracked/untracked user changes. Work on a new branch, e.g. `research/dsre-rss2027-science-first-20261115`. Preserve the published branch and its history. No force-push.
2. Publish a frozen preregistration file with target populations, settings, feature thresholds, sensor error bounds, fixed method list, primary/secondary metrics, stop conditions, and source hashes BEFORE producing any new outcome. Record environment and simulator build fingerprints.
3. Implement the small robust observation adapter and independent test/oracle in separate modules; do not mutate old DSRE decisions, calibration seals, or history. A zero-noise backwards-compatibility test is mandatory.
4. Run offline mechanism decomposition and sensor robustness first. Run qualified pilot and prospective physics only after their guards pass. Keep all interrupted/failed attempts.
5. Use complete grouped denominators and independent recomputation of action classes, certification claims, intervals, evidence invariance and witness validity. Do not use corrupted sensor replicates or multiple conditions as independent parents.
6. Run tests, Ruff, formatting, source-hash checks and sealed manifest verification. No fabricated results or manual paper table edits. Do not train another unrelated model, add a controller, or work on the full-length/Stage 2 paper.
7. Commit locally. Push the *new dedicated research branch* non-destructively only if the verified remote ancestry and credentials permit it; do not publish the blind paper or author-identifying submission links. If push is blocked, preserve the local branch and state the blocker. No conference submission.
8. Deliver `docs/DSRE_STAGE1_SCIENCE_V12_METHOD.md`, `docs/DSRE_STAGE1_SCIENCE_V12_RESULTS.md`, `docs/DSRE_STAGE1_SCIENCE_V12_NOVELTY.md`, `docs/DSRE_STAGE1_SCIENCE_V12_GATE.md`, figure source assets, raw/compact evidence manifests, tests and audit report, exact reproduction commands, resource ledger, branch and commit SHA.

**Priority order if time or simulation budget runs short:** (i) robust evidence semantics and independent verifier; (ii) existing-data action/observation feasibility decomposition; (iii) qualified, prospective physically varied PickCube paired interventions; (iv) source-grounded novelty review and paper-ready evidence; (v) optional richer visualizations. Never sacrifice correctness or independent baselines for breadth.