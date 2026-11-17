# DSRE evidence-aware recovery: supervisor specification v2

Date: 17 November 2026. Research definition and execution design, not an empirical result or acceptance prediction.

The approved plan is preserved unchanged in GitHub commit `125199a9a773c764425d0007575a01db2e54105d`, branch `research/dsre-evidence-aware-design-20261117`. This specification resolves its remaining mathematical and implementation choices. It does not rewrite historical DSRE experiments. Latest local manuscript lineage: `5547450d66e7561d701afcddd29f0e29156fc55c`; last remotely verified scientific base: `e63848e2487ca59e7c66bdd4430614748ae1ece0`. The design branch is not a substitute for the user's newer local history.

## 1. One contribution and three claims

**Question:** What is the minimum observable and experimental evidence needed to justify a useful recovery intervention under a specified outcome obligation?

**Method:** DSRE constructs a small outcome-distribution ambiguity set from the type of intervention evidence available, qualifies useful recovery over frozen decision regions, compresses the resulting justification without changing its scope, and returns constructive witnesses of what evidence is missing.

**C1, evidence requirement:** randomized single-action logs can justify some recovery obligations but cannot resolve every counterfactual-harm claim, even with unlimited samples. The method must separate sampling uncertainty from this identification limit.

**C2, operational certificate:** explanations preserve the actual region for which the outcome claim is qualified. A short conjunction cannot silently inherit a larger region's guarantee after selecting a favorable or unfavorable subgroup.

**C3, practical consequence:** missing-evidence witnesses help allocate an equal acquisition budget between more single-action observations and paired evaluations. The benefit, if demonstrated, is useful qualified intervention coverage per evidence cost, not superiority over an equivalent rule solver.

Novelty is incremental and conditional: partial-identification bounds, safe policy improvement, rule minimization, interval propagation and simultaneous confidence control already exist. The candidate contribution is source-aware, obligation-specific certificate synthesis and operational missing-evidence diagnosis in robot recovery. A conventional rule with the same bound may make identical decisions. Report that identity, and test certificate faithfulness and evidence allocation directly.

## 2. Estimands and assumptions

Actions are fixed macros `c` (continue) and `r` (recover). A task record fixes controller versions, task objective, decision checkpoint, horizon and observation interface. Potential outcomes are terminal binary successes `(Yc,Yr)`. Their joint order is `(00,01,10,11)`.

For a declared region B of predecision observations:

- `p0 = P(Yc=1 | B)`;
- `p1 = P(Yr=1 | B)`;
- `h = P(Yc=1,Yr=0 | B)`, binary task-outcome harm;
- `g = E[Yr-Yc | B]`, mean success improvement;
- `r_plus = P(Yc=0,Yr=1 | B)`, rescue probability; hence `g = r_plus-h`.

Primary useful-recovery requirement is `h <= 0.10` AND `g >= 0.05`. Both constants are frozen before new results. Absolute-completion (`1-p1 <= 0.10`) and harm-only are separate secondary requests. Primary gain is binary success improvement, not physical safety or individual benefit. A descriptive intervention toll `tau in {0, .02, .05}` changes the secondary benefit requirement to `g-tau >= .05`; never select a favorable toll after testing. Report actual control count, elapsed execution and planning time independently.

A noncertified recovery defaults to the SAME `continue` macro for the main operational evaluation. This makes the primary comparison baseline-relative rather than dependent on assigning zero completion to STOP. An explicit defer output is retained and reported as a distinct secondary operating protocol. Continuing by default is not asserted safe or successful.

Assumptions: independent parent checkpoints from a declared task/condition distribution; one condition per parent for primary estimation; consistency of the fixed macros and outcome definitions; randomized action assignment with propensity 1/2 in logged data; no interference; discovery data independent from calibration and test; stationary calibration-to-test population. Arbitrary confounded logs get `IDENTIFICATION_ASSUMPTION_UNSUPPORTED`. These assumptions do not establish sim-to-real transfer.

For deterministic reproducible simulation, paired branches define a valid joint experimental outcome. In a stochastic system, fixing common random numbers is an experimental coupling, not automatically the real-world joint potential-outcome law. Retain this limitation in data metadata and guarantees.

## 3. Evidence types and an explicit learner boundary

**L, single-action:** `(parent_id, X, A, propensity=.5, Y, cost, source_scope)`. No hidden outcome, fault ID, eventual oracle action or postdecision feature is included.

**P, paired refinement:** the same checkpoint has qualified counterpart execution, making `(Yc,Yr)` observable under the experimental model.

**O, uncontrolled observational:** absent an independently justified exchangeability model, do not compute causal certification merely by predicting outcomes.

Masked historical experiments may use full paired archives only in a separate evaluator. Generate learner files in a distinct directory containing one assigned outcome. Hash the whitelist and instrument file access. Discovery, partition fitting, rule ordering, calibration and data acquisition must not read the hidden counterpart. All historical data already viewed are exploratory development, not new confirmation.

For prospective logs, execute the randomized assigned action first and seal the learner log. A counterpart may later be executed in an evaluator-only process. The learner sees it only in an explicitly budgeted paired-refinement arm. Online execution receives a frozen certificate library and current observations, never counterfactual outcomes.

## 4. Four-cell outcome solver

Represent `q=(q00,q01,q10,q11)`, with nonnegative entries summing to one. Marginals are `p0=q10+q11`, `p1=q01+q11`; harm `q10`; rescue `q01`; gain `q01-q10`.

For logged intervals `[L0,U0]` and `[L1,U1]`, form Q_L by those two marginal constraints. For paired refinement, intersect Q_L with independently valid intervals on harm and rescue. The paired sample must represent the SAME conditional population; selecting pairs using their revealed outcomes or a within-cell feature without changing the target scope is prohibited. Empty Q means inconsistent evidence and an abstention, never a successful certificate.

Compute `H=max_Q q10`, `G=min_Q(q01-q10)`, `F=max_Q(1-q01-q11)` with a four-variable LP. Return optimizing distributions as witnesses. Test analytical equivalents for the unpaired rectangular case:

`h_lower=max(0,L0-U1)`;
`H=min(U0,1-L1)`;
`G=L1-U0`;
`F=1-L1`.

### An operational identification boundary

For exact marginals, harm qualifies at alpha iff `p0 <= alpha OR p1 >= 1-alpha`. If absolute completion does NOT qualify, a marginal-only non-degradation certificate therefore requires a sufficiently low continuation-success probability. Paired evidence can qualify harm even when both marginals are moderate. This is a corollary of the established sharp bound, not a newly invented inequality.

A strong finite-sample data-type obstruction is `L0 > alpha AND U1 < 1-alpha`: every marginal pair inside the confidence rectangle still allows harmful couplings above alpha. More unpaired samples targeting the same region cannot establish harm qualification for any true marginals remaining inside that event. New observations change the conditioning region; paired evidence or structural assumptions change identification. Do not conflate these operations.

Construct an explicit non-identification witness by solving for two joint distributions with identical marginals, one satisfying the requested obligation and one violating it. Such a witness proves unresolved compatibility, not necessarily that every future marginal sample remains uninformative. Label the stronger obstruction separately.

## 5. Valid routing and genuine minimum explanations

This section refines the approved plan's initial routing choice. Use frozen, coarse routing regions and forbid statistical claims on arbitrary selected subgroups.

1. On discovery data only, construct a Boolean decision tree with depth <=2 and <=4 leaves. For the primary evidence-regime comparison, EVERY method receives the SAME partition. Use the same randomized single-action discovery view; paired outcomes may not secretly choose a better partition for P.
2. Partition fitting: enumerate candidate depth-two Boolean trees; minimize total within-arm Bernoulli squared error from observed labels. Require at least 8 discovered observations per arm in each nonempty leaf. Tie by fewer leaves, then canonical feature order. If no split qualifies, use one leaf. This is a standard partition constructor, not DSRE novelty.
3. Freeze the complete logical partition over all possible Boolean assignments, not just observed rows. Unknown/unseen outcomes remain unqualified. Primary route is a function of that partition only.
4. Independently estimate simultaneous confidence constraints for each leaf. Choose recover only when its H <=.10 and G >=.05. Otherwise continue baseline with an insufficiency report. Do not select a narrower favorable subregion using other observed facts after calibrating a leaf.
5. Enumerate subsets of the at-most-six declared predicates. A display conjunction is eligible ONLY if it is logically constant on every leaf: it selects a union of entire leaves, not part of a leaf. Require all selected leaves to qualify the same obligation. Include the current leaf. Choose minimum literal count then canonical order. Zero-literal explanations are valid if the whole scope qualifies.

The population statement assumes the calibrated observation protocol is unchanged. A missingness-dependent sub-selection can violate it: include missingness in the discovery partition before calibration, or mark the affected observations unqualified. The resulting certificate is `(action, obligation, evidence, selected_leaf_scope, confidence_bound, source_type, assumptions)`. It describes a regional population statement, not individual causal safety. Since each selected leaf passes the same inequality, any union or cell-constant policy composed from those leaves inherits it. The explanation can be calibration-dependent because the confidence event is simultaneous over the already fixed leaves; no fresh data-dependent subgroup is introduced.

A wider vocabulary or deeper tree is a predeclared secondary sensitivity, not a test-driven remedy for poor coverage. Explainability is measured as literal count, exact scope fidelity and witness validity, not assumed human understanding.

## 6. Finite-sample confidence allocation and proof

Primary confidence is 95% PER TASK, not simultaneously across every task, experimental budget and publication iteration. Keep the sampling population and confidence family visible.

Reserve delta_L=.025 for logged marginals and delta_P=.025 for paired refinement. For K<=4 frozen leaves and two Bernoulli quantities per evidence block, use a two-sided Clopper-Pearson interval with per-tail probability `delta_block/(4K)`. Logged quantities are p0 and p1, estimated from independent randomized assigned outcomes within each leaf. Paired quantities are h and rescue, estimated from a uniformly sampled paired subset within each leaf, selected before any paired outcome is observed. Correlation between constraints is allowed by the union bound.

Zero sample count gives [0,1], not zero error. Full finite-sample certification requires actual conditional counts and assumptions. For K=4, per-tail .0015625, a zero-error parameter upper bound is about .0960 at n=64 and .0492 at n=128. These are planning calculations, not promises of final sample qualification.

**Proposition, scoped soundness:** Conditional on the independent discovery partition, all true regional parameters lie in their constraints with probability at least 1-(delta_L+delta_P). On that event, every passed leaf has harm <=alpha and gain >=eta. The calibrated action map is leaf-constant, so the deployed recover set is a union of passing leaves; its conditional harm is a weighted average <=alpha and gain a weighted average >=eta. Each reported conjunction selects a union of whole passing leaves, so it has the same regional property. Proof uses simultaneous confidence containment and conditioning, not an unsupported claim of conditional-on-each-individual coverage.

**Counterexample requiring the restriction:** A leaf can have harm .08 while a 10%-mass subregion has harm .80. Routing to recover only in that subregion breaks a .10 bound despite valid calibration on the leaf.

**Minimum evidence:** Exhaustive search is globally cardinality-minimal among conjunctions respecting the frozen partition and requested obligation. This is a restricted, explicitly named grammar. It is not claimed minimal over every possible natural-language explanation or arbitrary subgroup.

**Refinement:** Intersecting valid additional constraints on the same Q cannot increase H or decrease G. Adding a sensor, changing a controller or conditioning on a different region is NOT automatically such a set intersection.

## 7. Evidence diagnosis and repair protocol

Return typed, inspectable outputs, not unexplained rejection:

- `CERTIFIED_USEFUL_RECOVERY`: both harm and benefit pass.
- `CERTIFIED_COMPLETION_ONLY` / `CERTIFIED_NONDEGRADATION_ONLY`: optional separate requests, never mislabeled useful.
- `MARGINAL_IDENTIFICATION_BARRIER`: the strict rectangle condition in Section 4 holds; compatible favorable and unfavorable couplings show what pairing could reveal.
- `COUPLING_UNRESOLVED`: two currently compatible worlds disagree, but future marginal evidence might resolve the interval.
- `SAMPLE_LIMITED_AT_PLUGIN`: exact empirical marginals pass but finite-confidence constraints do not. This is a planning diagnostic, not proof that more samples will eventually qualify.
- `BENEFIT_UNSUPPORTED` / `HARM_UNAVOIDABLE_WITHIN_MODEL`: report the corresponding feasible-set bounds.
- `OBSERVATION_ALIASING`, `SCOPE_MISMATCH`, `NO_OVERLAP`, `INCONSISTENT_BOUNDS`: include the violated contract/witness.

A first bounded data-acquisition test uses only TWO evidence actions, so it is implementable: acquire more randomized single-action outcomes or acquire paired outcomes. Sensor addition is evaluated offline as a separate existing-channel ablation, not an undeveloped third acquisition method.

Use a diagnostic pool disjoint from final calibration. With a fixed budget, serve initially unresolved leaves by discovered population mass, then round-robin. In a leaf with a marginal identification barrier, request pairs; otherwise request balanced single-arm logs. Do not claim this deterministic diagnostic policy is optimally efficient. Compare it to all-logs, all-pairs, uniform mixed acquisition, and a decision-aware uncertainty strategy with the same evidence. Each execution costs one action outcome; a pair costs two; also record wall and replay costs. Choose all final calibration evidence-type allocations before its outcomes. Never use an outcome-selected paired sample as if it were a random sample of the leaf.

If adaptive diagnostic collection is used, its intermediate bounds are exploratory. Final certificates use a disjoint, fixed-size calibration allocation and one look. No optional-stopping CP claim. Budget curves require distinct confidence allocation or must be labeled descriptive, not simultaneous guaranteed deployment points.

## 8. Experiments and baselines, frozen by claim

E0: independently check 441 exact marginal pairs, interval LP identities, paired-set nesting, incompatible couplings, unknown evidence, the routing counterexample, and minimum explanation scopes. The supervisor's executable oracle already passes these checks. They validate the design, not scientific novelty.

E1: historical DEVELOPMENT replay, with one prechosen condition per independent parent. Four equally specified views: paired refinement; randomized single-action logs; naive independence coupling; no-identification-assumption negative control. Keep train/selector/evaluator processes separated. Report both equal parent budgets and equal action-execution budgets. Previous inspected archives cannot be advertised as confirmation.

E2: new-task pilots, then prospective source-isolated data. Tasks are grasping (existing PickCube), insertion (PegInsertionSide-v1) and navigation (PointMaze). Five grasp offsets are not five tasks. Primary breadth goal: grasping plus one COMPLETE non-grasp experiment; second new task is a fixed, explicitly reported pilot if budget-limited.

E3: witness usefulness at equal evidence cost. The decisive endpoint is extra valid intervention coverage or useful recovery per acquired execution, not number of explanations emitted. All strategies use the same frozen partition, obligations and final calibration rule; uncertainty selection gets the same features and outcomes. A tree+the identical bounds may reproduce DSRE decisions; report identity and evaluate scope compression/witness value separately.

E4: physical operational assessment. Use default continue when useful recovery is unqualified, rather than manufacturing gains from STOP=0. Also report explicit deferral as a secondary mode. Evaluate full policy success versus fixed continue, required rescues, binary harm, futile attempts, coverage, control count and wall time. Simultaneous inequalities concern regional risk/benefit, not zero harms on every test episode.

Baselines: fixed continue/recover; outcome-trained CART2 and shallow ensemble with matched qualification; same-grammar ordinary rules; direct tabular sharp bounds following Kallus; a no-harm utility-constrained policy over the same cells following the Li et al. objective (explicit adaptation unless original method reproduced); DISCRET-style subgroup policy with common bound; naive independence coupling as a negative control; empirical/LTT-style qualification for observable paired losses only. CRC expectation guarantees and PAC confidence guarantees are different; do not pretend their targets or required labels coincide.

Primary metrics: harm/benefit-bound validity, useful qualified recovery coverage, whole-policy gain over continue, necessary-rescue recall, execution cost, explanation length, witness correctness and evidence-budget efficiency. Compute parent-level intervals. A lower-risk policy with more abstention must be plotted on the same risk/coverage/benefit frontier, not advertised as universally better.

## 9. Sampling and prospective allocation

All reused DSRE parents are DEVELOPMENT for this extension. Deduplicate by task, physical model, checkpoint history, controller/horizon and parent, not just archive path. One condition per parent is selected by a frozen seeded uniform draw before any continuation outcome is read. No condition identifier becomes a runtime feature.

After each new-task technical pilot, freeze task-specific six predicates, macros, horizon and source version. Primary proposed per-domain fresh design is 128 discovery, 1024 independent calibration and 256 independent evaluation parents. These are caps and planning targets, not an assumption of adequate support in rare leaves. With four roughly balanced leaves and fair logged assignment, 1024 gives about 128 observations per arm per leaf; actual counts determine certification.

Authorize only the pilot and first bounded discovery pass in the initial session. The full numeric design is already specified, but its runtime forecast and data contract must be inspected before expensive collection. If the simulator throughput makes it infeasible, preserve the planned test pool and report achievable precision; do not lower alpha, alter outcomes or pick a lucky subset. No hardware is required or claimed.

## 10. Supervisor evidence and limitations

`supervisor_reference.py` and `supervisor_validation.json` implement and record independent design checks: 441 marginal LP cases (maximum error 1.11e-16), 256 random interval rectangles, 256 paired-constraint nesting cases, and 64 exhaustive certificate-scope cases. They also expose a naive-independence false qualification and subgroup-routing counterexample. No robot experiment or discovery of a new theorem is claimed from these checks.

Known related work is attributed rather than rediscovered. Kallus (NeurIPS 2022) gives sharp counterfactual-harm bounds and robust estimation. Li et al. (ICML 2023) optimizes policies under counterfactual no-harm constraints. DISCRET (ICML 2024) synthesizes faithful treatment-effect rules. Learn-then-Test and Conformal Risk Control provide different forms of risk qualification, not identification of missing harm labels. The candidate DSRE distinction is evidence-source-aware minimum scoped justification plus constructive evidence-choice witnesses in diverse recovery mechanisms. It remains a hypothesis until tested against matched adaptations.

No manuscript edits, review-process gaming, fabricated benefits, favorable seed replacement, erased negative trials or retrospective preregistration are allowed. The intended advantage is stronger scientific capability, not a promised favorable number.
