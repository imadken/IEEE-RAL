# Recoverability-preserving diagnosis: bounded originality challenge

19 November 2026. **Decision: VALID_KNOWN_FORMULATION.**

The supplied construction is correct, and the exact finite planner is independently
verified. The objective is representable by established bounded strong planning
and a time/resource-augmented reach-avoid POMDP. No distinct planning methodology
or physical benefit is established. V5 remains unchanged for the author's decision.

This is a separate hypothetical alternative, starting at local commit
`0d3b52b57a5914dee05530d15cc9ef26b95a921b`, on
`research/rpd-method-originality-challenge`. The explicit six-part user request is
the authority. The attached memo is a design to challenge, not evidence of novelty
or permission for its optional physics, stochastic extension or manuscript adoption.
All four package files were imported byte-for-byte under
`research/rpd_method_challenge/supervisor/`; the original ZIP remains untouched.

## 1. Formulation and scope

Let a finite state `s` include every physical variable, hidden parameter, controller
memory and clock needed for Markov transitions. `B` is the nonempty support of the
current uncertainty. Each registered terminal macro `a` has a declared binary task
predicate `G(s,a)`. In this execution **all such predicates are analytical truth
tables**. New calibrated physical success predicates available: **zero**.

A probe `p` has explicit deterministic transition `T_p(s)`, post-transition
observation `O_p(T_p(s))`, nonnegative rational cost, an enable condition and a
declared path-allowed flag. Its successor support after observation `y` is

    B[p,y] = { T_p(s) : s in B, O_p(T_p(s)) = y }.

The implementation replaces states with their actual successors. It never filters
the original support while silently keeping its old recovery labels. States with
the same successor must have the same observation for that probe; an omitted
hidden parameter must instead be retained in the state. Undefined transitions,
missing predicates, inconsistent source metadata and unknown observations raise
errors. Missing information never becomes a false physical outcome or a reset.

Define the immediate task option

    Common(B) = { a : every s in B satisfies G(s,a) }.

This differs from `every s has SOME successful macro`: the latter need not supply
one common executable decision under uncertainty. It also differs from physical
state constraints. A state can lie inside an allowed set `C` while both fixed
macros fail. Conversely, a task-successful macro can violate a separate physical
constraint. The optional physical gate checks the initial support, each whole
probe path and successor, and terminal macro paths. An allowed endpoint alone
does not prove an allowed intermediate path.

For horizon `h` and remaining probe-cost budget `b`, let `J_h(B,b)` be the minimum
worst-case accumulated probe cost of a policy guaranteed to finish with a
successful allowed macro. Immediate common recovery has value zero. Otherwise,

    J_h(B,b) = min_p [ c_p + max_y J_(h-1)(B[p,y], b-c_p) ],

over enabled, budget-admissible, path-allowed probes and all nonempty observation
branches. A missing feasible solution has value infinity. The policy then returns
**STOP**, with an obstruction proof; it does not execute a risky macro by default.
STOP terminates the attempt without a reset or a successful-macro certificate.
It is not a guarantee that an uncontrolled physical system remains safe forever.

The production API bounds `h` by four, states by 32 and probes by eight. Registered
exhaustive/seeded tests use the smaller grid below. Costs use exact `Fraction`
arithmetic. Equal-value choices use local deterministic action-ID tie breaks;
there is no claim of a globally shortest or unique policy tree. Runtime remains
exponential in the finite problem size.

### Standard correctness argument

At horizon zero the only successful policies terminate with a common allowed
macro, exactly the base case. At positive horizon, any successful nonterminal
policy must choose a legal first probe and have a successful continuation for
every possible observation. Induction gives the child optimum; adding the probe
cost and taking the maximum gives its worst branch cost. Minimizing over all legal
first probes gives the global minimum. Conversely, combining those child policies
constructs a successful policy. A decreasing horizon prevents zero-cost cycles
from creating an infinite plan.

For multiple probe steps this is bounded eventual recoverability. It does not
require an immediately executable common fallback macro at every intermediate
belief; the two/three-step cases explicitly exercise that distinction.

An unsuccessful search returns one counterexample state for every recovery macro.
For every probe it records an actual disable/constraint/budget violation, or a
nonempty observation branch with a recursively checked obstruction. Induction
therefore proves **no robust policy for this model, menu, horizon and budget**.
It does not prove impossibility with another sensor, controller or longer horizon.

These are standard Bellman/AND-OR arguments. No new theorem of POMDP planning,
viability theory or strong conditional planning is claimed.

### Exact same-input reach-avoid representation

Augment each state with the remaining horizon and resource budget. Probe actions
use the same transitions, observations and costs. A terminal macro enters GOAL on
success, FAIL on task failure, or AVOID on a physical violation. STOP enters HALT.
These terminal symbols are accounting states, not physical state restorations.
All initial support states receive positive probability, for example a uniform
prior. In this finite deterministic bounded model, reaching GOAL with probability
one is equivalent to succeeding from every initial support state. Feasibility
under each candidate resource budget, or equivalent minimax dynamic programming,
therefore recovers exactly the same minimum worst-case probe cost.

**EXACT REPRESENTATIONAL EQUIVALENCE** holds for this probability-one, bounded,
same-objective problem. It is not a claim that a generic expected-return objective,
an infinite-horizon almost-sure objective, or a finite-sampling POMCP implementation
must select the same policy. Where probability-one success is impossible, a
probability-maximizing policy may accept partial success while this robust interface
STOPs. The oracle preserves those partial-success probabilities rather than hiding
them. No sampled, continuous or learned robot model inherits this exact guarantee.

## 2. Independently verified counterexample and numerical results

**ANALYTICAL WORLDS, not robot episodes.** Initial states A and B admit `retry`;
C admits `realign`. No macro is common to all three. `full_diagnostic` costs one,
reveals the initial case, and maps C to an explicit absorbing `dead_C` with no
successful macro. `coarse_safe` costs two, leaves physical states intact and
observes either A/B or C. Every state, including `dead_C`, is physically allowed.

Under the uniform initial prior, observation information is 1.584962500721156 bits
for the full probe and 0.9182958340544896 for the coarse probe. The latter permits
`retry` on its left branch and `realign` on its right branch. The former's C branch
is irrecoverable within the fixed menu. The supplied output matches its provided
validation JSON, and a separately coded transition/group/intersection calculation
reproduces the result.

| Same supplied model, horizon 1, budget 2 | Chosen behavior | Worst spent probe cost | Successful analytical worlds |
|---|---|---:|---:|
| Exact viability planner | coarse probe, contingent macro | 2 | 3/3 |
| Independent strong-policy tree oracle | coarse probe, contingent macro | 2 | 3/3 |
| Full-model probability-one POMDP objective | same optimal value | 2 | 3/3 |
| One-step task-consensus control | coarse probe, contingent macro | 2 | 3/3 |
| Physical-safety-filtered uniform-support entropy | full probe; C branch STOPs | 1 | 2/3 |
| Static-transition ERR ablation | full probe; stale C macro fails | 1 | 2/3 |
| No-probe robust control | STOP | 0 | 0 certified macro completions |

The input budget is matched; actual spent type costs differ and are displayed.
These are not equal-cost physical performance results. The static ablation
deliberately violates the transition model and loses its model-based guarantee.
Independent empirical terminal calibration would be a different, source-scoped
claim. The one-step consensus tie is a strong adverse control, not omitted.

The complete numerical audit checks **6,688** declared problems: 16 named cases,
528 seeded cases and 6,144 exhaustive two-state cases. It enumerates **22,904**
legal policy trees, including unsuccessful recoveries and STOP. All values match
both independent exhaustive enumeration and the separate exact Bayesian POMDP
recursion. There are 1,237 independently replayed winning policies and 5,451
independently verified recursive obstruction proofs.

The exhaustive family covers every two-state one-macro success table, transition
map, binary observation map, allowed-state set and enable mask, at horizons 0/1/2,
with the physical gate on/off. Its fixed probe cost is one. The 528 seeded cases
span 2–5 states, 1–2 probes, horizons 0–2 and 22 replications per cell, seed
2026111903. They include rational/zero costs, disabled probes and cost budgets.
The named cases additionally check three required physical steps, intermediate
unsafe paths with allowed endpoints, unsafe successful macros, tiny rational
cost differences, and zero-cost loops. This is the stated finite grid, not every
possible model with eight probes or continuous dynamics.

The pure-information control is not a reproduction of s-FEAST. The task-consensus
control is not a reproduction of DA-GRD. The independently implemented generic
same-input control tests the mathematical objective; no published robotics
software was installed or benchmarked on a different task.

Two further falsifiers limit the interpretation. With identity transitions, pure
observation refinement cannot remove a previously common macro: that macro still
succeeds on every subset. Conversely, the explicit physical-restoration case
improves task feasibility without supplying any new information. The mechanism
is the physical action's effect, not information itself causing failure.

## 3. Full primary-method challenge and nearest-work matrix

Full methods were retrieved, rather than relying on titles or abstracts. The
retrieval receipt records URLs, exact file hashes and extracted-text hashes.
Publisher access to the s-FEAST article failed, so its first author's complete
2025 thesis method chapter is identified explicitly. The restricted 2021 HCPlan
journal text was not retrieved; the full HCP-ASP predecessor is audited instead,
without pretending it is the same version. The public HCPlan repository was empty.
No claim about the inaccessible extension's detailed algorithm is made.

| Primary method / exact checked location | Problem data and assumptions | Constraints and algorithm | Stated guarantee and measured quantities | Same-input baseline / limit |
|---|---|---|---|---|
| **s-FEAST**, Science Robotics 2024; [Ragan's full author thesis](https://thesis.caltech.edu/17024/1/_Thesis%20Final%20Final%20Draft.pdf), §3.2–3.3, pp32–43, Algorithm3, Theorem5; AppendixB pp158–162 | Joint physical-state/fault belief; fixed candidate fault modes, dynamics/observation models, motion-capture measurements and marginalized filtering | Information-seeking tree search with conservative probabilistic physical-state constraints | Claims asymptotic value convergence on the stated conservative safe-belief problem, under sampling/feasibility assumptions. Measures fault diagnosis, collision avoidance and computation, with spacecraft hardware and numerical studies | Its published objective is not fixed-macro terminal task recovery. A finite safety/entropy heuristic is only an adaptation. It already models action-dependent physical and epistemic effects; no new safe-active-sensing claim is justified here. |
| **DA-GRD**, [full v1](https://arxiv.org/html/2609.29065v1), §III-A–E, Eqs1–6; §IV-A–D | Remembered geometry/task grasp; weighted SE(2) pose hypotheses; hit/miss/contact and free-space evidence | Feasible horizontal/vertical probes, miss-exclusion/surface/coverage score, grasp-coverage stopping and refinement | Empirical grasp/probe evaluation in MuJoCo and hardware; posterior grasp coverage is not this prototype's universal robust truth | A task-consensus control is essential and ties the supplied toy. §III-B already includes small sliding, translation and pivot-like probe-induced motion. It cannot honestly be labelled passive sensing. No full DA-GRD port or ranking is claimed. |
| **Hybrid conditional planning**, [full HCP-ASP paper](https://arxiv.org/pdf/1707.05904), §3–5.4, Algorithm1, AppendixC; [2021 extension locator](https://doi.org/10.1177/0278364920963783) | Partial functional-fluent states; actuation/sensing models and external kinematic/geometric checks | Parallel conditional-branch construction, ASP, reuse of subtrees; goal-directed sensing and actuation | Branch correctness uses Markov/merging assumptions. §5.2 explicitly discusses whole-plan constraints and recomputing from the root. Measures plan size, makespan, sensing count and runtime | Encode physical effects and terminal goal; augment state with clock/resources for history constraints. No claim that its native optimization is our exact minimax cost or that the unavailable 2021 implementation was reproduced. |
| **Reach-avoid POMDP shielding**, [full ICRA2024 paper](https://www.cs.ox.ac.uk/David.Parker/papers/icra24shields.pdf), §III-B, V, VI-D | Finite POMDP T/Z, initial belief, REACH/AVOID sets; winning belief supports | Productive winning regions restrict actions, with centralized/factored POMCP shielding | Guarantees depend on the model/winning region; particle approximation can miss states. Reports unsafe behavior, return and runtime on navigation/refueling/rock domains | **Exact objective representation** after horizon/resource augmentation and terminal macro encoding. The paper's indefinite-horizon/expected-return settings are not identical to bounded worst-cost optimization. Our separate exact control verifies the probability-one specialization, not that approximate published code always returns the same tree. |
| **Shielding-aware safe dual control**, [full arXiv v2](https://arxiv.org/html/2302.00171v2), §4–6.4, Eq20, Theorems1–2 and Remark10 | Joint agent dynamics and behavioral belief; bounded disturbances/other-agent actions; initial robust controlled-invariant safe set | Scenario-tree approximate dual MPC with proactive shielding and a safe fallback | Dual-control effect and recursive safety under the stated invariant-set assumptions; global optimality is explicitly limited by approximation and nonconvex local optimization. Measures task cost, information/shielding and driving interaction, including hardware | Coupled action/information tradeoffs are established. Its published safety/performance problem is not a plug-in fixed-macro diagnosis benchmark; adaptation would require matched dynamics, belief and terminal-goal data. |
| **RAYA**, [full v1](https://arxiv.org/html/2609.21690v1), §III-A–D, Eqs3–11; §IV-A | Deployable history features, learned finite-horizon recovery margin, fixed predictive dynamics and hard constraints | Recovery margin enters MPC; a bounded scheduler reallocates task objectives | Structural bounds preserve existing hard constraints; empirical margin quality is distinct from universal recoverability. Reports simulation/hardware recovery and intervention effects | Preserving recovery opportunities during action choice is already a direct motivation. It does not supply this finite diagnosis tree, but the present candidate cannot claim that generic recovery-preserving control is new. |

The relevant distinction from a physical safe-set-only objective is real. The
conclusion that it constitutes a new general methodology does not follow.
Established goal-directed belief planning already represents the proposed
objective exactly; the numerical same-input equality supports that conclusion.
No superiority over published s-FEAST, DA-GRD, HCPlan, dual-control or RAYA results
is measured in this execution.

## 4. Two source-supported adapter designs, no new physics

The static audit binds ManiSkill **3.0.1**, SAPIEN **3.0.3**, Torch
**2.5.1+cpu**, NumPy **1.26.4**, Panda URDF/controller and native task source hashes.
The existing environment factory uses CPU simulation, `render_backend="none"`,
`state_dict` observations and `pd_ee_delta_pos`. No camera, tactile, force or
aperture sensor is invented. The packet contains only the first seven arm joint
positions/velocities, FK TCP xyz and the native clock. Finger joints, object pose,
grasp flags, contacts, wrenches, fault labels and future outcomes are excluded.

Actual historical sealed D/C traces verify the named fields at Pick prefix index
65, time3.25s, and Push index53, time2.65s. The source JSON records both parent IDs,
original native gzip hashes and masked numerical packets. They establish **channel
availability only**. In particular, the old Pick condition/prefix does not certify
the newly nominated nominal checkpoint/replay flow or any post-probe success.
The historical assigned outcomes are never supplied to the finite planner.

| Adapter | Concrete checkpoint | Physical probe commands | Fixed recovery/controller binding |
|---|---|---|---|
| PickCube-v1 | Nominal native `prefix_to_stage(world,'transport')`: 20 approach,25 descend,15 close,5 transport controls; checkpoint65 | `micro_lift`: four `(0,0,.025,-1)` controls, then six closed-gripper holds. `release_settle`: ten `(0,0,0,+1)` controls | Existing `action_for` continue/recover functions,70 controls from the actual post-probe state; Panda PD/IK remains unchanged |
| PushCube-v1 | Nominal native prefix:20 approach,25 descend,8 push controls; checkpoint53 | `forward_tap`: four `(.05,0,0,-1)` then six holds. `lateral_sweep`: four `(0,.05,0,-1)` then six holds | Same native binding,70 controls; no new robot controller, optimizer or insertion dependency |

Commands are normalized native actuator inputs, not measured object displacement.
They genuinely actuate the robot rather than merely relabel a measurement. Whether
they change object contacts, supply useful information or remove recovery options
is **unmeasured** and is the proposed pilot's question. The release command is an
actuator command, not an aperture measurement.

These are two task families on the same Panda/tabletop stack. They do not
establish cross-embodiment or independent-domain breadth. The memo's broader
domain aspiration is not represented as an achieved result or permission to
substitute another task.

Both menus use ten controls per probe at20Hz. The future physical horizon allows
at most two probes and a common90-control deadline. Original70-control macros are
followed by native holds where needed; record success at both macro-end and the
common deadline. STOP also holds to that deadline and its actual native outcome
must be recorded, not labelled failed by assumption. Set the existing episode
wrapper to200 controls, as in the prior native source, so65+90 does not truncate.
Future model state must retain the clock and controller memory; otherwise padding
would change the meaning of `G` without appearing in the model.

The fixed macro controllers internally use ideal native object/goal state. This
privilege remains identical across methods and is disclosed as simulation-only;
it is not exposed as a diagnostic sensor or represented as a real-robot policy.

### Exact qualification guards and bounded pilot

Each nominated family has ten new preregistered technical parents, zero currently
collected. Test all seven probe histories of length0–2 with two recovery macros
and a STOP/hold endpoint, twice:21 histories/endpoints ×2 ×10 =420 native
episodes per family, with a two-worker-hour pilot cap. There is no initial-success
or failed-seed replacement and no task substitution.

Require exact task/source/controller hashes,20Hz timing and the fixed checkpoint.
Record already-complete prefixes separately. Reconstruct a fresh full prefix
between evaluator episodes, including controller memory, and require repeated
lineage parity: position<=1e-5m, orientation/qpos<=1e-4rad, velocity/observations
<=1e-4, time<=1e-9s, and identical contacts/task flags. During any one actual
probe/recovery history, forbid reset, restoration, state injection and teleporting.
All ten measured probe frames must exist and be finite. Unknown observations
stop and mark a model miss, rather than restoring the original belief.

Verify nonzero native actuator/TCP effects against neutral hold. Log object motion
and contact changes separately as evaluator-only evidence. No positive recovery
effect, favorable probe ranking or action diversity is a qualification prerequisite.
A source/replay/telemetry failure blocks that family; zero information or zero
recoverability loss is retained as a scientific null. No repair campaign or
alternative task is authorized by this design.

The proposed engineering allowed set uses the Panda URDF arm-joint limits with
1e-6rad numerical allowance; TCP |x|,|y|<=.60m and z in[.015,.50]m; object
|x|,|y|<=.45m and z in[cube_half_size-.002,.50]m, in the native world frame.
Evaluate it at every recorded20Hz control boundary. Object bounds are evaluator-
only; the learner does not acquire a hidden object-state sensor. A legitimate
post-probe violation is retained as an adverse outcome, not silently excluded
as source attrition. A model-based filter cannot turn this into a physical guarantee.
This is sampled geometric evidence, not continuous-time, force, collision-damage
or hardware safety. No post-probe calibrated predicate or path-safety certificate
exists now. Existing DSRE marginal bounds cannot be transferred to these new
checkpoints, histories, sensors or deadline populations.

## 5. Fixed, falsifiable Stage 2 protocol — inactive

The generated manifest reserves **842 independent parents per family**:10 pilot,
64 discovery,512 independent calibration and256 untouched test, totaling1,684.
All qualification/outcome fields are null. Pick base seed is2004000000; Push base
is2004100000. Phase offsets are0,1000,10000,20000. Parent ID is
`SHA256("RPD-S2-20261119|task|phase|index|seed")`. Historical seed collision checking
against all source manifests is a mandatory pre-collection guard, not a check
claimed to have passed here. The128 evaluator-oracle test parents are selected
by a fixed parent hash before any new outcome.

Discovery freezes the finite surrogate, initial support construction, source
likelihoods/transition hypotheses, common observation encoding and all policies.
The prototype does not establish that a learned finite catalogue exhausts a
continuous simulator. Include clock/controller memory. Freeze one binary split
of one registered response feature using discovery only, with an integer
threshold grammar and deterministic ties. An uninformative feature is a null,
not permission to change sensors after test. At two binary probes each policy
has at most four terminal strata.

Respect the prototype's32-state limit: a candidate catalogue may contain at most
four surrogate roots with seven history-indexed nodes each, selected by the fixed
`RPD-SURROGATE-ROOT-v1` parent hash on discovery before reading their outcomes.
These28 model nodes are not28 independent parents or a complete physical law.
The remaining discovery parents test the surrogate, rather than being silently
discarded as new support. A future source-qualified catalogue bridge and its
coverage checks are prerequisites; they are not implemented or certified by
today's analytical-only input mode. Failure to construct a supported catalogue
blocks physical model-based claims without inventing transition or success labels.

Six behavior controls are fixed continue, fixed recover, physical-safety-filtered
entropy, one-step task consensus, the explicit static-transition ablation and
the exact contingent objective. Include an independent full-model strong/POMDP
control with identical data, transitions, observations, actions, horizon and
minimax cost. Share executions where it is the same policy. Do not market
different solvers for the same objective as different scientific capabilities.
No actual published robotics implementation is claimed to have been ported.

Every valid method has the same discovery information, source assumptions,
calibration budget and90-control physical deadline. All six policy executions
on a parent share a parent cluster, not six independent samples. Extra evaluator
oracle histories never enter policy selection. Report actual elapsed time,
native controls, probes, source failures and terminal outcomes as well as budget
caps. The transition-ignored ablation loses its model-based guarantee; a valid
independent empirical terminal gate would still have its own limited scope.

| Hypothesis | Frozen empirical test | Null/open interpretation |
|---|---|---|
| H1: more-disambiguating action can remove recovery options | Fix probe order by discovery decoder accuracy for16 root object-minus-TCP pose cells. Condition on the same predecision proprioceptive signature; compare probe-augmented predictions and report the root-only decoder. On untouched oracle parents require corrected lower bounds above.05 for both decoder-accuracy advantage and incidence of `K_low nonempty, K_high empty`, where K uses actual macro outcomes | Accuracy is a conditional information proxy, not measured Shannon information. Tied/uninformative probes, zero loss or wide intervals leave H1 unsupported/open; do not replace probes |
| H2: accounting for physical effects improves task completion over entropy at equal budget | On256 independent test parents compare actual common-deadline success. Require `L_CP(RPD-only success)-U_CP(entropy-only success)>.05`; split the endpoint error across tails | A tie with exact full-model control is expected. A small/wide or negative difference gives no advantage claim. Report cost, withholding, futility, rescue and lost options separately |
| H3: the finite classifications remain source-grounded | On128 hash-fixed oracle parents check actual source traces for every instantiated witness; require upperCP(model/source mismatch)<=.05 | Unknown/missing states or transitions are model/source failures, not proofs of physical impossibility. Zero observed mismatch is not universal validity |

H1 decoder labels are evaluator-only root geometry. Its decoder is fitted on
discovery, never on test. Predecision root signatures are quantized using the
fixed native telemetry units; unseen signatures use the discovery prior. This
prevents apparent new information from facts already visible before probing.
There are eight one-sided hypothesis endpoints across the two families; allocate
.05/8 to each, with further splitting for paired-difference bounds. All condition
variants and histories stay in their parent cluster.

Optional statistical terminal authorization requires **fresh calibration**, not
the analytical truth table. Use one-sided Clopper–Pearson tails .05/(2*6*4),
simultaneous over two tasks, six policies and four frozen whole terminal strata.
Only a selected terminal macro with lower bound>=.90 qualifies, in that frozen
policy-induced history/population and macro-with-padding scope. A failed gate
STOPs; it does not trigger upstream replanning or refitting on calibration.
This supplies neither universal state-wise `G` nor physical path safety. A
stochastic planner extension is **not implemented or claimed** in this challenge.

At least66 all-success independent parents are needed in a stratum even to pass
that proposed gate. A64-parent stratum cannot qualify at all. At128 parents,
125 successes qualify; analytical qualification power is about.960 at true
success.99 and.113 at.95. Thus512 total calibration parents do not promise
qualification of every leaf. The stored power table exposes this limitation.
Near-threshold or small task gains may remain statistically unresolved at the
fixed test size; do not claim power that has not been demonstrated.

Do not drop post-qualification missing endpoints into an unconditional complete-
case interval. Preserve missing labels, calculate worst-case completion ranges
and withhold unsupported guarantees unless a separate censoring argument exists.
Initial-prefix attrition, missing sensors, replay mismatch, model mismatch, both-
macro failure and statistical withholding must be reported with separate counts.

The bounded episode allocation per family is420 pilot +896 discovery +3,072
calibration +1,536 selected-policy test +1,792 evaluator-only oracle episodes =
**7,716**. The same selected branch may be reused by provenance rather than
executed twice, so this is a ceiling. Ten seconds/Pick episode and twelve/Push
give estimates21.43 and25.72 worker-hours. Proposed family caps are26 and32
worker-hours, including the two-hour pilots, with8GiB storage each. These are
future estimates requiring a separate resource charter; **zero of those hours
is authorized or spent here**. No claim of completed cohorts is made.

If a source guard fails, stop that family and preserve its precise missing
counts. If pilot throughput cannot fit the fixed cohorts within the proposed
ceiling, stop before the main study and report infeasibility, rather than shrinking
test N after seeing outcomes. At a ceiling close the current episode/parent and
seal incomplete counts without replacement. The timetable is technical source
qualification first, then frozen discovery/model, independent calibration,
untouched common test, independent audit and writing. A failed family does not
become a replacement task or another insertion repair campaign.

## 6. Brief Stage 1 narrative for author consideration

*Diagnostic actions can alter the task they are intended to diagnose. We study
when a robot can resolve uncertainty about a recovery decision while retaining
a feasible terminal recovery. We formulate the question as bounded strong
planning with explicit physical transitions and post-action observations, and
provide an exact finite-model implementation with auditable no-policy witnesses.
A constructed example separates physical state allowance from remaining task
options: the most informative action can leave an allowed state with no successful
macro. This is a known planning formulation, and an independent full-model control
is equivalent. The robotics hypothesis is whether such a tradeoff occurs under
qualified native probe interfaces and matters at a fixed execution budget. Two
unexecuted simulator adapter designs and a source-qualified, independent-cohort
protocol make that hypothesis falsifiable. Existing DSRE recovery results are
background only and do not validate the new probes or their success predicates.*

This paragraph is an internal alternative narrative, not an edit to V5 or an
assertion that the alternative is more submission-ready. A five-content-page
paper would need the question/closest-prior boundary, model/limits, finite
construction/control equality, concrete source feasibility and the falsifiable
protocol in its main text. The physical feasibility and benefit are currently
unverified. The general formulation and solver cannot carry a novelty claim.

## 7. Reviewer challenge and final scientific gate

| Hard objection | Evidence-based answer |
|---|---|
| This is goal-directed partially observed planning | Agree. The exact same-input strong/POMDP representation and all6,688 value checks support equivalence; do not rename it into a new algorithm |
| Safe active diagnosis and grasp-consensus probing already exist | Full methods, including physical effects and stopping rules, are audited above. No superiority over their published results is measured |
| Physical safety and recovery feasibility are being conflated | The finite counterexamples separate them; native sampled geometry is separately labelled and supplies no force/hardware guarantee |
| A learned success predicate is being treated as truth | Rejected. Current inputs are analytical only, current calibrated predicates number zero, and old DSRE calibration cannot transfer |
| The sensors or resets are imaginary | Actual sealed D/C packets and source bindings verify the named arm channels. The pure adapters have no simulator/reset API; future continuous histories and replay guards are explicit |
| The new task choice or baseline favors the proposal | The two families/menu were fixed before any new outcome. One-step consensus and generic planning ties are retained; no replacement follows a negative test |
| The physical study may have no useful regime or insufficient support | Both are valid nulls. Source qualification, attrition, calibration power and fixed costs are explicit; no new physics has been run |

**Formal/implementation decision:** supported within the declared deterministic
finite model, horizon, budget and source assumptions. **Originality decision:**
**VALID_KNOWN_FORMULATION**. **Physical decision:** source interfaces and old
sensor availability are checked; new probe qualification, calibrated outcomes
and useful physical effects are unestablished.

There is no unresolved numerical or implementation failure in the checked scope.
There is a disclosed literature-access gap for the final2021 HCPlan text, not a
claim reconstructed from its abstract. The broader hybrid method was read in
full in its identified primary version. This does not weaken the independent
known-formulation equivalence. The next action is author/supervisor paper choice
with V5 preserved, not another autonomous experimental campaign or manuscript
replacement. Nothing has been pushed or submitted, and no RSS invitation is claimed.

## 8. Reproduction and integrity

Core source is `src/dual_rec/recoverability/`; independent controls/verifier are
`scripts/rpd_independent_oracle.py`, `rpd_baselines.py` and `rpd_audit.py`.
The source/adapter audit, inactive parent protocol, original checker comparison,
all finite inputs/results, code freeze, test logs, source/provenance ledgers,
preservation inventory and resource/reproduction receipts are under
`research/rpd_method_challenge/`. No historical evidence file or manuscript is
replaced. The compact archive includes only the new package and the exact
consumed source dependency snapshot, not redistributed papers.

```bash
cd /home/imad/Desktop/IEEE-RAL
export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
uv run --no-sync python scripts/rpd_reproduce.py --verify
uv run --no-sync python scripts/rpd_reproduce.py --full --portable --output /tmp/rpd-independent-review
uv run --no-sync pytest -q tests
git log -1 --format=%H
```

Choose a fresh reproduction directory. The independently usable reproducer is
separate from the dated48-hour campaign driver. The Git commit anchors the final
integrity manifest without a self-referential commit hash in its contents.

The frozen final run passed52 new tests and the maintained suite of747 passed,
6 skipped. The six skips retain the existing two missing-public-IPC-cache cases
and four tests requiring the isolated RecoverBench stack. The run took56.10s
and42.59 child CPU seconds. Portable reproduction verified42 source members and
matched all seven scientific outputs in8.76s, including the supplied checker,
independent finite audit, actual historical sensor-field audit, inactive protocol
and focused tests. Timings and archive-format-dependent read inventories are the
only excluded comparison fields. Static checks and final preservation/archive
receipts accompany the sealed package.
