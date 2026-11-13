# DSRE v1.1: strict and provisional minimum outcome rules

Authority: `DSRE_STAGE1_SUPERVISOR_CONTINUATION.md` v1.1. Starting commit
`c5d354f648946a6945b07897f1c5a82961370835`. This self-contained continuation
supersedes the v1.0 prohibition on introducing an average-outcome tier. The absent
v1.0 blueprint remains absent; its content is not reconstructed. All original
Stage 1 documents and sealed results remain historical, unchanged evidence.

## Fixed observations, outcomes and scope

Reuse exactly the 844 qualified paired checkpoints, 422 per task, two conditions
per seed, 211 independent seed groups per task, and the original five folds.
Source: `results/dsre-stage1/20261113T144253Z/qualified_pairs.jsonl`, SHA256
`46f13e374fd5d319e5987e12352074309163956db83b1f0ce9b3991a43d653e2`.
No new physical outcomes, tree fits, controllers, features or annotation decisions.
Six primary Boolean/UNKNOWN predicates, scope, thresholds, terminal utility and
70-control/3.5-second horizon are inherited from `DSRE_STAGE1_PROTOCOL.md`.
Simulator pose observations are a declared pose-estimate interface, not validated
real sensors. Privileged and 2cm pose-quantized variants are observability diagnostics
only. Coarse poses change the Boolean partition; this is not monotone bit coarsening.

Reference schema: scoped task/controller/horizon/features plus rows with audit ID,
Boolean/UNKNOWN vector, qualified flag and measured paired binary terminal outcomes.
Runtime query schema contains only scope and observed predicates. Outcomes, hidden
conditions, future frames and identifiers do not enter query selection. All data
have informed development; cross-fitting is exploratory, not untouched confirmation.
UNKNOWN physical outcomes remain unknown. Rules touching incomplete or unqualified
outcome rows cannot issue either a strict or empirical-risk recommendation.

For A={continue,recover}, v=1 and 0<=epsilon<1,
`Good_i={a: V_i(a)>=1 and max_b V_i(b)-V_i(a)<=epsilon}` equals the set of successful
measured actions. Both may qualify; neither may qualify. A single deterministic
branch per action is not an estimated stochastic success probability.
E contains only observed query literals. A row matches E unless it has a known
opposite literal. Reference UNKNOWN never excludes a row. Minimum support is two
checkpoint rows, not two independent seeds. Zero support never suffices.

## Observability characterization and executable proof

Group rows by exactly equal observed vector z, including explicit UNKNOWN symbols.
Let G(z) be the intersection of their Good sets. The exact-pattern finite-table
upper coverage is `sum_z N_z*1[G(z) nonempty]/N`. A deterministic action on z
must be in every Good set; if the intersection is empty it cannot succeed on all
rows. Conversely choose any common action on each nonempty class and abstain
elsewhere. This attains the bound for an unrestricted exact-pattern policy.
This elementary finite characterization is not new theory or a population bound.

The conservative rule grammar cannot test UNKNOWN as a literal. Its full known
query conjunction also matches incomplete compatible rows, even from other exact
groups. Report the intersection on that larger match separately, and enumerate
all subsets to check achievable strict coverage with minimum support two. A sparse
pure full signature may have a supported broader pure rule; full-pattern support
below two alone is not proof that every explanation is impossible. An unseen query
can similarly have supported broader evidence. Do not call lack of data a physical
incompatibility. Query support status and physical witnesses are separate.

For both exact and compatible groups report inadequate rows (empty Good), disjoint
nonempty Good witnesses, their overlap, unknown outcomes and support. Record actual
IDs and values. The diagnostic best fixed action maximizes measured successes on
each exact signature, continue on ties, acts on all rows and reports actual errors;
it is hindsight finite-table accuracy, never a certificate. Also report false pure
classes obtained by deleting neither rows, and the errors of the action suggested
by a majority four-way outcome label (both->continue, neither->abstain). No evaluated
label is used to choose a deployed threshold or primary feature map.

## Router and equivalences

Tier S calls the unchanged v1.0 exact solver. It minimizes cardinality, then larger
support, continue-first, canonical predicate names. Return
`STRICT_FINITE_REFERENCE`, its original certificate and literal-removal witnesses.
Calibration remains UNASSESSED and deployable action remains disabled.

Only if S abstains, Tier R enumerates the existing B5 conjunction grammar. On each
candidate/action let k be measured unacceptable outcomes in its n matched rows.
Require n>=2, complete qualified outcomes and k/n<=beta. Primary beta=.10;
descriptive sensitivity beta=.05. Choose cardinality, lower k/n, larger support,
continue on action ties, then canonical predicate names. Compare fractions exactly
to avoid floating tie errors. Status is `PROVISIONAL_UNCALIBRATED`, tier is
`PROVISIONAL_RISK_RULE`; it has no universal certificate or necessity assertion.
Emit matched IDs, k/n and scope for audit. No simulator action is commanded.

If neither qualifies, return `INSUFFICIENT` with original strict reasons/witnesses.
The strict-failure explanation is retained also for provisional recommendations.
Pseudocode: validate scope -> S.solve(x) -> if action return S -> else enumerate
R(x,beta) -> if action return R -> else return U. Freeze whole router before any
future independent calibration. A failed action stratum returns
`CALIBRATION_INSUFFICIENT`, with no rerouting after calibration outcomes.

Strict S equals minimum pure outcome-rule synthesis (B7 and B5@zero risk) under
identical ties. Tier R is exactly B5 v1.1 on the S-abstention subset. The entire
S-first router need not equal unconstrained B5: S may choose a longer zero-error
rule when B5 can choose a shorter impure rule. This is priority, not superior search.
The v1.0 mean-rule ties favored support before error; v1.1 changes only risk-tier
and B5 v1.1 ties, not the historical S solver or saved trees. Include B1 two-literal
B5 grammar under the same risk/ties. Reuse CART stump/depth2/depth3 nodes and same
reference-row leaf support; no refitting. Full-signature selector uses the same
risk threshold, plus always-continue/recover boundary controls. Shared calibration
wrappers do not confer any distinct guarantee on DSRE.

Counterexamples tested: both-success permits empty evidence; neither-success
invalidates adequacy despite zero regret; identical opposing single-success rows
block strict action; one neither row can block a high-accuracy class; incomplete
compatible rows cannot be discarded; missing outcomes do not become failures;
strict-first priority can yield a longer rule than B5; support and scope failures
are not evidence of physical inability. Provisional labels can never be certified.

## Frozen evaluation, uncertainty and calibration

Reuse the original five group folds and saved four-category CART nodes. Enumerate
only reference rules and then score held-out folds. Cache repeated signatures;
record cold per-signature runtime separately from cache hits, parsing and audit.
Primary fixed points beta .10 and sensitivity .05; strict point0 and inherited
.25/.50 targets are descriptive frontier diagnostics only. No evaluation-selected
threshold is deployed. Match achieved conditional unacceptable rates exactly using
integer cross products; show coverage/length tradeoffs and flag absent equal-risk
points. Equal risk at different coverage is not equality on the same population.

Report by task/action and combined: checkpoints and seed denominators, emitted,
abstained, adequate/absolute terminal successes, unacceptable count/rate, regret,
successful recommendations/all, mean literals/support, S/R fractions, status mistakes
and runtime. Repeat key counts on failed-start cohorts; maintained success is not
new recovery. Parent bootstrap: 2,000 shared draws of 211 seed groups/task,
NumPy PCG64 seed 2026111301+task index, both conditions together. Combined draws
are task-stratified; paired contrasts use identical weights. Report conditional
intervals only with >=10 recommending groups; no per-frame resampling. Conditional
risk comparisons may have different recommendation populations. No CI is a
deployment bound, and a degenerate CI is not population equivalence.

Freeze each fold router's definition/reference and the full table router (planning
only). Reuse exact one-sided Clopper-Pearson upper bounds from calibration.py and
verify independently with Decimal binomial arithmetic. Alpha=.10,total delta=.05,
four task/action strata, delta_a=.0125. Zero errors require42 independent assigned
parents, not42 correlated conditions or total sampled parents. Missing outcomes,
zero assignments, dependent/reused parents and stale routers cannot qualify.
Shared wrappers apply to each comparable method; simultaneous selection among
several calibrated methods would require additional multiplicity allocation.
No real calibration occurs. Fold assignment rates estimate expected counts per200
new task parents and expected parents for42 assignments, not guarantees. Preserve
the archived800-parent proposal without execution or mutation.

Budget:4h wall,5 measured CPU hours,0GPU/physics/model fits/paid APIs,
500MB outputs,100MB network. Bounded foreground workers; reserve final60min and
1,800CPU seconds for handoff, plus50MB. Preserve historical hashes and user moves.
All output claims are offline development results. G0 exact audit/test correctness;
G1 finite observability limits; G2 useful coverage/risk with B5 identities; G3 direct
two-literal/CART/wrapper challenge; G4 supervisor readiness decision. A novelty
shortfall leads to PRELIMINARY_ONLY, not a topic change or manuscript.

## One-page scientific novelty challenge

Status before numbers: **METHOD_DISTINCTIVENESS_UNRESOLVED**. The closest identity
is B7=S and B5=R on strict-abstention queries. The S-first composition is an explicit
priority wrapper over those known procedures, not a new rule optimizer. Original
primary-method reading evidence and precise mechanisms remain in
`DSRE_NOVELTY_MATRIX.md` and the sealed Stage 1 literature ledger.

| Prior method | Strongest overlap and precise remaining distinction |
| --- | --- |
| [ICAPS2009 MSE](https://cs.uwaterloo.ca/~ppoupart/publications/explaining-mdps/ICAPS09OKhan.pdf) | Minimum information justifying action value already exists. Here literals query finite paired outcomes instead of MDP reward/occupancy templates; this is representation/scope, not new minimality theory. |
| [Anchors AAAI2018](https://sameersingh.org/files/papers/anchors-aaai18.pdf), [PSE IJCAI2021](https://arxiv.org/html/2105.10118) | Short high-precision sufficient rules/partial observations are known. Our target is measured action adequacy, including both/none, rather than preserving a model prediction. Empirical rule accuracy is not future risk calibration. |
| [Formal policy explanations IJCAI2023](https://users.cecs.anu.edu.au/~thiebaux/papers/ijcai23.pdf) | Universal partial-state sufficiency and deletion witnesses are known. DSRE allows any adequate intervention rather than one policy label, with finite paired outcomes and exact cardinality at small d. |
| [DISCRET ICML2024](https://proceedings.mlr.press/v235/wu24n.html) | Outcome/treatment-grounded subgroup rules are direct competition. Exhaustive same-grammar B5 matches R by definition; omitting learned synthesis at d<=8 does not create a scientific novelty. |
| [Learn then Test, AOAS2025](https://www.gsb.stanford.edu/faculty-research/publications/learn-then-test-calibrating-predictive-algorithms-achieve-risk), [author method §§2–3.2](https://arxiv.org/html/2110.01052v5) | Post-fitting calibration with familywise error control is established. Our four action/task binomial checks are a simple fixed-router application, not a new calibration method. Independent assigned parents and identical future distributions remain assumptions; no such cohort exists here. |
| [Peddi/Bezzo2023](https://arxiv.org/html/2308.00944), [CAPE ICRA2024](https://www.cs.utexas.edu/~ml/papers/raman.icra24.pdf), [RESCUE2026 preprint](https://arxiv.org/html/2610.13516) | Explainable recovery trees, preconditions and matched intervention outcomes already exist. DSRE gives scoped minimal outcome rules plus insufficiency witnesses; it neither creates a controller nor demonstrates improved physical recovery. |

The non-equivalent target versus a policy explanation is accepting multiple adequate
actions and distinguishing neither-success from ambiguity. Plain outcome-aware rules
already receive this same target. S/R/U statuses and witnesses can be reproduced by
wrapping B5/B7/CART with the same table checker/calibration, so these interfaces alone
do not establish an RSS-strength method contribution. No novelty claim is rescued
by a favorable development subgroup or a changed discretization.

Evidence still necessary within this question, **not executed here**: supervisor
review of a substantive non-equivalent capability; a frozen-router, prospective
independent assigned-parent calibration cohort with adequate action accrual; paired
fresh confirmation comparing B5, two-literal rules and CART at common validity/risk
criteria; and a measured decision-relevant effect of the claimed evidence interface
beyond identical wrappers. Those require new scientific authorization, not an
automatic launch of the old800-parent proposal. The exact finite observability
characterization can be useful negative evidence without being a new theorem.
