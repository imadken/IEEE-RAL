# DSRE Stage 1: measured development results

**Gate: PRELIMINARY_ONLY. No distinct method advantage or readiness to draft an RSS
submission is established.** The exact solver, witnesses, all strong baselines,
actual development cross-fitting, registered sensitivities and calibration interface
are implemented and evaluated. B7 and B5 at mean target1 are equivalent to DSRE;
a plain two-literal outcome rule at target1 matches the entire primary PickCube
result. The outcome-trained stump has a better primary empirical operating point.
No new simulator rollout, controller, failure condition, LM, manuscript or push ran.

The fixed question is: **What is the smallest observable evidence sufficient to
justify a robot recovery action relative to its actual intervention outcomes?**

Reviewed base: `116dc45b33796b59df7ba6c0332bb120e60a3b9d`. Branch:
`research/dsre-stage1-development`. Final exact local HEAD is attested in the evidence
seal after committing. Evidence root (R below):
`results/dsre-stage1/20261113T144253Z`. All source/control/utility choices were frozen
before method numbers in `DSRE_STAGE1_PROTOCOL.md`, `config/dsre_stage1.json`,
`pre_evaluation_freeze.json` and `experiment_freeze.json`.

## Specification availability and what was completed

The supplied execution contract was read in full and committed verbatim as
`DSRE_CODEX_STAGE1_EXECUTION_CONTRACT.md`. The named supervisor blueprint version 1.0
was **not found** in repository, all attachments, Desktop/Downloads/Documents, or a
home-wide hidden filename search. Its contents/URL list were not invented, and no
substitute `DSRE_STAGE1_RESEARCH_BLUEPRINT.md` was created. All self-contained stages
specified in the execution contract were completed. Blueprint consistency remains
unverifiable and must be resolved before a later scientific authorization.

The previous RecoveryClaim/RecoveryContract reports and Week2 explanation-repair
negative findings were inspected and preserved. This is a different decision object
within the supervisor-fixed recovery question, not another detector or language editor.
The direct eleven-paper method inspection is in `DSRE_NOVELTY_MATRIX.md` and
R/`literature_inspection.json`; no broad topic search or preprint-acceptance claim.

## Qualified physical outcome table and provenance

There were 920 recorded PickCube/PushCube checkpoint pairs. An initial pass accepted
metadata-level qualification but inspection identified incomplete retained histories/
reference memory in 76 older records. Before any model fitting, the full pass and
adapter were preserved in `qualification_attempt01_metadata_only/`, the correction
was documented in `qualification_correction.json`, and strict qualification was
rerun without changing seeds, features, actions, thresholds or utilities.

**844 checkpoint pairs remain, from 422 task/seed groups**: 422 checkpoints / 211
seed groups per task, both original conditions per seed. All 840 old confirmation
checkpoints plus four fully instrumented old development checkpoints qualify. The
76 exclusions are retained with exact reasons. Every historical seed is development
now, irrespective of its original split label. No frame/certificate variant adds a
physical sample. The two conditions within each seed stay together in all five folds
and bootstrap draws.

Both measured `continue/fresh_prefix` and `recover/fresh_prefix` branches have retained
complete histories, controller memory equal to the registered checkpoint, equal
physical model/history hashes, 70 recorded controls, 3.5-second horizon and raw
start/trajectory parity with their reference. Native snapshots are never substituted.
Terminal task-success is the primary binary utility. One deterministic branch per
action is an observed value, **not an estimated stochastic success probability**.
Initial success and new first-hit success remain distinct.

| Task | Pairs / seed groups | Continue only | Recover only | Both succeed | Neither succeeds | Already successful at checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PickCube-v1 | 422 / 211 | 75 | 120 | 204 | 23 | 277 |
| PushCube-v1 | 422 / 211 | 2 | 211 | 204 | 5 | 0 |

On the 145 failed-start PickCube checkpoints: 3 continue-only, 120 recover-only,
22 neither, no both. New first-hit successes are 3 continuation / 120 recovery.
All 422 PushCube starts fail the task predicate; new first-hit successes are 206 /
415. Terminal and first-hit counts happen to coincide in these failed-start cohorts;
this was checked, not used to reselect the endpoint. Maintaining one of the 277
initially successful PickCube states is not counted as new recovery.

The final table SHA-256 is
`46f13e374fd5d319e5987e12352074309163956db83b1f0ce9b3991a43d653e2`.
R/`source_members.json` pins 1,843 source members, including excluded records and
historical registration/freeze/seal files. `data_qualification.json` pins all five
controller/source files and their combined identity
`4d94f7e69d838fe4181e9719ae5c79c4381948bdf158d6f2ac45b0adf27fd3f5`.
The original installed-engine/runtime identities remain in the immutable source
root; current numerical versions are in R/`runtime_versions.json`.

## Exact finite-model methodology and E0

The primary vocabulary contains six predecision pose/proprioception predicates:
goal-near3cm, hand/object-near4cm, goal progress5mm, object displacement5mm,
gripper aperture<=4cm and hand>3cm above object. The precise source/time/units,
engineering threshold origins, availability and privileged variants are in the
protocol. Object/goal poses are simulator-supplied state observations behind a
**declared pose-estimate interface**, not a demonstrated real perception system.
Grasp/contact simulator booleans are privileged diagnostic additions, never silently
real sensors. Condition names, success flags and future branches are not runtime
query fields. Unavailable facts stay UNKNOWN and cannot exclude a reference row.

DSRE searches every needed subset of at most eight available predicates and returns
globally minimum cardinality, larger conservative support (minimum2), continue-first
action and lexical literal ties. Empty evidence is permitted; zero support is not.
Certificates state scope, matched reference IDs for audit only, necessary-literal
counterexamples and typed insufficiency. The deployed recommendation interface omits
reference IDs. A table-relative certificate is separate from independent calibration;
all current deployment actions are disabled for lack of that cohort.

The independent direct enumerator and difference-set/hitting-set oracle agreed on
**1,200 fixed E0 tables through d=8, with 3,431 witnesses checked**. Unit cases cover
one-bit stump equivalence, two necessary literals, adequate ties, indistinguishable
incompatible actions, failure ties, UNKNOWN query/reference values, absent outcomes/
support/scope, canonical ties, leakage boundaries and literal-deletion witnesses.
The genuine logical greedy counterexample has bad-row difference sets {a,b} and
{a,c}: exact {a}, lexical deletion {b,c}. These authored cases are not simulator trials
or a new theorem. Their success does not establish deployment accuracy.

## What actually trained and ran

All 60 variant/task/fold model sets completed: six fixed feature variants × two tasks
× five seed-group folds. **240 four-category CART-style trees actually trained**
(depth1/2/3 and fixed pruning). Full-pattern lookup selectors, outcome-trained bounded
rules, policy-faithful exact rules, greedy and minimum outcome rules use the same
reference outcomes/observations. Four outcome categories are retained; both/none are
not forced into a binary policy label. There is no foundation model or new controller.

Primary predictions plus all five registered mean-utility operating targets produced
273,456 stored prediction rows and 648 operating-point count tables. There are
70,896 primary prediction rows across variants/methods; these are repeated analyses
of 844 checkpoints, not independent physical trials. Predictions contain query
features only; query outcomes are evaluator-only. All fit/evaluation seed groups are
disjoint. The entire corpus already informed development: **exploratory cross-fitting,
not an untouched confirmation set**.

B0 is unconditional; B1 uses outcome-aware one/two-literal libraries; B2 uses CART
paths and fixed pruning; B3 is a saturated full-pattern conditional outcome model;
B4 targets agreement with that model; B5 is a DISCRET-inspired mean-utility/paired-ATE
rule adaptation; B6 is fixed lexical deletion; B7 is the plain exact adequate rule.
No weak language baseline is substituted. Primary mean targets are .9 for B1/B2/B5,
.5 for B3, and universal adequacy for DSRE/B6/B7. The full fixed 1/.95/.9/.75/.5
frontier is retained, so the primary table alone is not the strongest-baseline claim.

## Primary joint outcome, coverage and evidence tables

At v=1, successful selected actions equal acceptable-action accuracy. Mean regret
can be zero even for an unacceptable neither-success action; absolute adequacy is
therefore reported separately. An abstention contributes no successful recommendation;
it is neither a measured physical failure nor a successful task. Length is conditional
on recommendation. These predictions are uncalibrated offline recommendations.

### PickCube-v1

| Method | Recommended / checkpoints | Success / recommended | Unacceptable / recommended | Mean regret | Mean literals | Successful recommendations / all |
| --- | --- | --- | --- | --- | --- | --- |
| DSRE | 203/422 | 202/203 | 1/203 | 0.0000 | 1.0887 | 202/422 |
| B0_continue | 422/422 | 279/422 | 143/422 | 0.2844 | 0.0000 | 279/422 |
| B0_recover | 422/422 | 324/422 | 98/422 | 0.1777 | 0.0000 | 324/422 |
| B1_one | 298/422 | 279/298 | 19/298 | 0.0604 | 1.0000 | 279/422 |
| B1_two | 298/422 | 279/298 | 19/298 | 0.0604 | 1.0000 | 279/422 |
| B2_depth1 | 280/422 | 279/280 | 1/280 | 0.0000 | 1.0000 | 279/422 |
| B2_depth2 | 297/422 | 296/297 | 1/297 | 0.0000 | 2.0000 | 296/422 |
| B2_depth3 | 297/422 | 296/297 | 1/297 | 0.0000 | 2.0000 | 296/422 |
| B2_pruned | 280/422 | 279/280 | 1/280 | 0.0000 | 1.0000 | 279/422 |
| B3_full | 419/422 | 396/419 | 23/419 | 0.0000 | 6.0000 | 396/422 |
| B4_policy | 419/422 | 396/419 | 23/419 | 0.0000 | 1.0000 | 396/422 |
| B5_mean | 298/422 | 279/298 | 19/298 | 0.0604 | 1.0000 | 279/422 |
| B6_greedy | 200/422 | 199/200 | 1/200 | 0.0000 | 1.0750 | 199/422 |
| B7_exact_rule | 203/422 | 202/203 | 1/203 | 0.0000 | 1.0887 | 202/422 |

### PushCube-v1

| Method | Recommended / checkpoints | Success / recommended | Unacceptable / recommended | Mean regret | Mean literals | Successful recommendations / all |
| --- | --- | --- | --- | --- | --- | --- |
| DSRE | 0/422 | N/A (0 recommendations) | N/A | N/A | N/A | 0/422 |
| B0_continue | 422/422 | 206/422 | 216/422 | 0.5000 | 0.0000 | 206/422 |
| B0_recover | 422/422 | 415/422 | 7/422 | 0.0047 | 0.0000 | 415/422 |
| B1_one | 422/422 | 415/422 | 7/422 | 0.0047 | 0.0000 | 415/422 |
| B1_two | 422/422 | 415/422 | 7/422 | 0.0047 | 0.0000 | 415/422 |
| B2_depth1 | 422/422 | 414/422 | 8/422 | 0.0071 | 1.0000 | 414/422 |
| B2_depth2 | 422/422 | 414/422 | 8/422 | 0.0071 | 1.0000 | 414/422 |
| B2_depth3 | 422/422 | 414/422 | 8/422 | 0.0071 | 1.0000 | 414/422 |
| B2_pruned | 422/422 | 414/422 | 8/422 | 0.0071 | 1.0000 | 414/422 |
| B3_full | 422/422 | 414/422 | 8/422 | 0.0071 | 6.0000 | 414/422 |
| B4_policy | 422/422 | 414/422 | 8/422 | 0.0071 | 0.1991 | 414/422 |
| B5_mean | 422/422 | 415/422 | 7/422 | 0.0047 | 0.0000 | 415/422 |
| B6_greedy | 0/422 | N/A (0 recommendations) | N/A | N/A | N/A | 0/422 |
| B7_exact_rule | 0/422 | N/A (0 recommendations) | N/A | N/A | N/A | 0/422 |

The PickCube stump recommends on 66.35% versus DSRE's 48.10%, with the same one
unacceptable checkpoint and lower average evidence cardinality (1 versus 1.089).
The empirical stump point dominates DSRE on these three primary axes; this is a
descriptive development result, not population dominance. B3/B4 have greater
coverage with 23 unacceptable actions, illustrating a different risk/coverage point.
On PushCube, an empty B5 mean-success rule is simply always recover: 415/422 successes,
seven unacceptable outcomes (five inadequate ties, two action-regret errors). DSRE
cannot justify any action under its stricter universal criterion. Zero recommendations
must not be represented as zero conditional risk or a successful recovery policy.

### Failed-start population, without counting maintained success as recovery

On PickCube's 145 failed starts, DSRE recommends on 19 and succeeds on 19, with mean
1.947 literals. The stump recommends/succeeds on 3 with one literal; depth2/depth3
recommend/succeed on 20 with two literals. B3/B4 recommend on 142, succeed on 120 and
accept22 inadequate states; B5 recommends on 21, succeeds on 3, and has18 action-regret
errors. Always recover succeeds on 120/145 but has25 unacceptable choices. B7 exactly
matches DSRE's19/19. Thus a useful selective-recovery certificate exists, but neither
this subset nor the all-start table demonstrates a distinct DSRE algorithm advantage.
All PushCube checkpoints are already in the failed-start population. Full fourteen-
method subset counts are in `failed_start_metrics.json` and independently checked.

## Strongest frontier, mathematical equivalence and uncertainty

With binary V, epsilon<1 and v=1, Accept_i is exactly the set of successful measured
actions. DSRE is therefore an outcome-conditioned minimum pure conjunction. B7 is
mathematically the same finite problem; B5 at mean-success target1 is also identical
with the same grammar, support, UNKNOWN semantics and ties. All **5,064** variant/
checkpoint comparisons reproduce action, evidence and support, verified independently.
This is a formal equivalence under the assumptions, not population equivalence
inferred from zero sample differences. Witness rendering is an interface difference.

At the registered strict target1, **B1's plain two-literal rule also matches the full
primary PickCube result: 203 recommendations, one unacceptable, 1.089 literals**.
All observed primary DSRE certificates have one or two literals. Its match is an
empirical small-vocabulary boundary, distinct from B7's general formulation equivalence.
The strict single-literal rule gives 185 recommendations/one unacceptable; strict CART
stump gives 55/one. Full operating points and Pareto membership are in `frontier.csv`.

Exact matched coverage/error bands are zero-width, fixed before numbers. PickCube
has exact matches to B1-two@1, B5@1 and B7 with identical mean length. Other registered
points are explicitly infeasible matches; no held-out threshold is chosen to force
a favourable match. PushCube has no DSRE recommendation and hence no conditional
matched-performance comparison. Descriptive evidence caps0..8 are supplied separately;
none is a newly calibrated/deployed router.

Paired bootstrap uses2,000 fixed-seed draws over 211 task/seed groups per task, both
conditions together. Conditional intervals are withheld for fewer than10 recommending
seed groups. A constant interval is not proof of generalization or zero risk.

| Primary contrast | Coverage difference, pp | Paired95% pp | Mean-literal difference on common recommendation episodes |
| --- | ---: | --- | --- |
| Pick DSRE minus stump | -18.25 | [-24.41,-12.32] | 0 on 185 common checkpoints; [0,0] |
| Pick DSRE minus B5@.9 | -22.51 | [-28.20,-17.06] | +.0887; [.0532,.1244] on 203 |
| Pick DSRE minus greedy | +.71 | [0,1.66] | 0 on 200 common checkpoints; [0,0] |
| Pick DSRE minus B7 | 0 | [0,0] | 0 on 203; equivalence already known |
| Push DSRE minus B5@.9 | -100 | [-100,-100] | N/A: no common recommendations |

Pick DSRE's conditional unacceptable rate is1/203=0.493%, descriptive parent95%
[0%,1.563%]; stump1/280=0.357% [0%,1.103%]. These conditional populations differ.
DSRE coverage95% is[44.31%,51.90%] and conditional mean length95% is[1.053,1.124].
The lone error is a neither-success checkpoint: regret remains zero while adequacy
fails. No deployment confidence bound follows from this one-error development sample.

Exact-versus-greedy has **no observed length difference on their200 common primary
PickCube recommendations**. The three extra exact recommendations have zero support
for the full six-literal query conjunction in that fold; the frozen greedy routine
cannot initialize there, while a supported broader two-literal rule exists. This is
a support-initialization limitation, not an observed example of greedy returning a
longer rule. `greedy_difference_diagnostics.json` names all three. The length2-versus 1
greedy counterexample remains E0-only; it is not relabelled as a physical result.

## Collision limits, witnesses and sensitivity

| Task / channels | Exact feature patterns | Patterns with incompatible nonempty action sets | Patterns containing a neither-success row |
| --- | ---: | ---: | ---: |
| Pick primary | 9 | 0 | 3 |
| Pick plus privileged | 13 | 0 | 3 |
| Push primary | 2 | 1 | 2 |
| Push plus privileged | 2 | 1 | 2 |

Every primary PushCube pattern contains an inadequate state, and one also mixes
continue-only and recover-only states. No nonempty matching pure adequate rule exists
with this vocabulary/reference model, regardless of solver sophistication. Grasp is
UNKNOWN for PushCube; adding recorded contact creates no additional pattern there.
`feature_collisions.json` preserves both exact patterns and conservative UNKNOWN
compatibility, with all IDs/categories for checking.

A useful full-table example justifies **recover** from `goal_near_03=False` and
`hand_above_object_03=False`, with 17 reference checkpoints: all 17 initially fail,
all 17 continuation branches fail and all 17 recovery branches succeed. This is a
measured, outcome-relevant short certificate, not a root cause or an independent test.
Deleting the goal literal admits `PickCube-v1/100471/nominal`, where continue succeeds
and recovery fails. Deleting the hand-height literal admits
`PickCube-v1/100863/offset002`, where neither succeeds. B7/B5@1 generate the same rule.

An ambiguity witness pairs `PushCube-v1/103984/nominal` (recover-only) with
`PushCube-v1/105544/nominal` (continue-only) at the same primary signature; that class
also contains `PushCube-v1/101204/nominal`, where neither succeeds. Inadequacy is
separate from policy-label disagreement. In primary cross-fitting DSRE has219 Pick
insufficiencies containing an inadequate compatible state; all 422 Push cases have
that reason, and211 also have incompatible-action witnesses. Counts overlap by
design. Scope/outcome-uncertainty/missing-support mechanisms are tested in E0; no
missing outcome is fabricated for the complete qualified E1 pairs.

| Variant | Pick recommendations | Pick unacceptable | Pick literals | Push recommendations | Push unacceptable | Push literals |
| --- | --- | --- | --- | --- | --- | --- |
| pose_proprioception | 203/422 | 1 | 1.089 | 0/422 | 0 | N/A |
| plus_privileged | 208/422 | 1 | 1.111 | 0/422 | 0 | N/A |
| without_history | 203/422 | 1 | 1.089 | 0/422 | 0 | N/A |
| without_goal_channel | 180/422 | 0 | 1.083 | 0/422 | 0 | N/A |
| coarse_geometry | 184/422 | 0 | 1.103 | 183/422 | 0 | 1.000 |
| query_channel_missing | 177/422 | 1 | 1.085 | 0/422 | 0 | N/A |

Coarsening poses to2cm changes the Boolean threshold partition: PushCube goes from
two to three patterns and obtains183 recommendations with zero observed unacceptable
actions. This is a predeclared, exploratory discretization sensitivity, **not a
monotonic information-loss theorem or a reason to replace the primary vocabulary**.
The zero sample error is not a calibrated guarantee, and the plain exact outcome
rules remain equivalent. Dropping goal/history or adding privileged channels does
not establish a distinct method contribution. Full-table support sensitivities1/5/10
are preserved in `full_table_certificates.json`; none replaces primary minimum2.

Only three cross-fit policy-faithful/outcome-action disagreements occur, all in the
predeclared coarse PickCube analysis. All three measured pairs have both actions
succeeding: the differing actions are equally adequate, with no recovery gain.
There are zero such primary-channel disagreements. E0 separately demonstrates why
preserving a tied model label can require more evidence than choosing another adequate
action; that logical possibility is not promoted into an observed physical advantage.

## Calibration interface and prospective resource plan

The typed frozen-router utility rejects repeated/reused development parents, wrong
router hashes/tasks, absent outcomes and unregistered strata. It applies one-sided
exact binomial error bounds with total delta=.05 split over four declared task/action
strata (.0125 each), alpha=.10. A disabled recommendation is not rerouted. The finite
certificate remains separate. Unit tests and high-precision independent arithmetic
check zero/all errors, N=0, a rare action, multiplicity and task-specific behaviour.

With zero errors, upper=1-.0125**(1/N); **N>=42 assigned independent parents** is
required. Optional alpha=.05 requires 86, strictly a planning sensitivity. No independent
calibration cohort exists here. All deployment actions remain disabled, including
otherwise table-sufficient recommendations.

The frozen full-table primary router recommends on 183/422 Pick checkpoints:165
continue and18 recover. Push has0/422. These fitting-set frequencies are planning
inputs, not future assignment or error guarantees.

| Stratum | Development routing frequency | Expected assigned from 200 new parents | Expected parents to reach42 assigned, assuming zero errors |
| --- | ---: | ---: | ---: |
| Pick / continue | 39.10% | 78.20 | 108 |
| Pick / recover | 4.27% | 8.53 | 985 |
| Push / continue | 0% | 0 | unavailable at this frequency |
| Push / recover | 0% | 0 | unavailable at this frequency |

The candidate200 calibration/200 confirmation parents per task therefore does not
qualify all DSRE strata. Sampling noise, shifts and any errors can require more.
No minority-action quota, outcome-conditioned selection or confidence reallocation
is introduced. A fixed800-parent prospective list has separate new calibration/
confirmation seed pools, one existing registered condition per seed, balanced before
outcomes; every seed is disjoint from old pools. It is **not authorized or executed**.

Assuming the same host/controllers, 400 total parents/task with two reference plus
two fresh-prefix continuations each would require 3,200 continuations and224,000
post-checkpoint controls overall, plus complete prefixes. Existing median two-fresh-
route wall times are3.970s Pick /2.638s Push. Reference+fresh estimates are52.9min /
35.2min; a1.5x overhead factor gives 79.4min /52.8min, about 2.20h combined. These are
planning estimates, not measured future resource use; CPU would depend on host/thread
load. The985-parent rare-action estimate is **not an expanded registered campaign**.
The supervisor must review scientific identifiability, the missing blueprint and the
budget before authorizing any new physics.

## Computational cost, independent audit and tests

Cold primary unique-signature means (parsing/I/O and model fitting excluded):

| Method | Pick mean ms / median ms (31 signatures) | Push mean ms / median ms (10 signatures) |
| --- | --- | --- |
| DSRE with witnesses | 7.183 /1.034 | 87.346 /87.449 |
| Greedy with witnesses | 7.206 /.208 | 86.587 /87.086 |
| Plain exact outcome rule | 16.149 /9.822 | 37.388 /37.701 |
| CART stump | .584 /.371 | .889 /.805 |

These single-run cold costs include support/certificate bookkeeping. Repeated
signatures were cached in the experiment and are not counted as fresh latency
measurements. Insufficiency witness search adds cost; no real-time or sensing-cost
advantage is claimed. Whole-worker/model-fit timing and pooled variant/target
latencies are retained separately in `commands.jsonl`, model files,
`method_runtime.json` and `runtime_primary_comparison.json`.

The independent raw/finite/numerical audit passed 1,843 source hashes,844 pairs,
1,688 measured fresh action outcomes,235,728 full-history state comparisons,
273,456 prediction rows,648 operating-point count tables,383 exact cross-fit
certificates,104 full-table certificates,5,064 DSRE/B7/B5at1 equivalences and1,101
primary parent intervals. A second derived path rechecks70,896 primary per-input
scores,168 failed-start count cells and585 paired/common-cohort intervals. The17-
checkpoint useful recovery certificate is checked against actual outcome pairs.
Calibration bounds agree with 70-digit decimal arithmetic. These are independent
code paths in the **same unattended session**, not independent human scientific review.

The initial failing scope-reason unit test and wrong source-manifest lookup are
preserved and resolved before scientific fits. The weaker metadata-only qualification
attempt and first plot rendering are also preserved. No physical seed or adverse
outcome was replaced. Final validation passed **420 tests, with four optional-stack skips**. All 211
Python files passed Ruff format checking, Ruff lint passed, and `git diff --check`
passed. DSRE/source tests also ran separately; the latest provenance/relocation/seal
subset passed all ten tests. Exact outputs are in `validation.json` and bounded
job logs before sealing.

## Documentation relocation after computation

During the run, the user moved additional repository documents into `docs/`,
including the frozen DSRE protocol, contract and novelty ledger. All moved content
is byte-identical to its frozen/initial hash. Their locations are preserved; old
root-document deletions and unrelated `docs/` files remain outside this commit.
The remaining new DSRE reports are also stored in `docs/`. Reproduction now accepts
the protocol in either original location or `docs/`; this post-computation change
only affects document lookup. The original runner, exact two replacements and both
source hashes are preserved in `post_execution_path_amendment.json` and its source
copy. `post_relocation_source_audit.json` independently checks the restricted
amendment and unchanged scientific sources/choices. `user_document_relocations.json`
records all verified moves without altering the original initial inventory or
historical seals. The existing numerical results did not change or rerun.

## Evidence paths, reproduction and scientific boundary

| Material under R | Path |
| --- | --- |
| Authority/specification status and initial preservation inventory | `authority.txt`, `specification_status.json`, `initial.json` |
| Frozen protocol/config/source/data/splits | `pre_evaluation_freeze.json`, `experiment_freeze.json`, `analysis_plan.json`, `group_splits.json` |
| Qualified rows, source hashes and all exclusions | `qualified_pairs.jsonl`, `source_members.json`, `data_qualification.json`, `qualification_exclusions.json` |
| Exact E0 evidence | `e0_independent_agreement.json`, bounded unit-test logs |
| Actual trained models, fold outputs, timings and certificates | `crossfit/*.model.json`, `crossfit/*.jsonl`, `crossfit/*.certificates.json` |
| All metrics/frontiers and uncertainty | `metrics.json`, `frontier.csv`, `matched_frontier.json`, `paired_comparisons.json`, `descriptive_evidence_caps.csv`, `failed_start_metrics.json` |
| Witnesses, collisions and policy disagreements | `witness_examples.json`, `feature_collisions.json`, `full_table_certificates.json`, `policy_outcome_disagreements.json` |
| Calibration and prospective seeds/costs | `calibration_feasibility.json`, `frozen_router.json`, `prospective_fresh_seed_plan.json`, `*_prospective_cost.json` |
| Independent verification | `independent_audit.json`, `independent_derived_audit.json` |
| Standalone figures | `figures/paired_outcomes.png`, `figures/joint_frontier.png`, `figures/calibration_accrual.png` |
| Compact review package | `supervisor_review.tar.gz` |
| Final tests, accounting, preservation, commit and seal | `validation.json`, `resources.json`, `completion_manifest.json` |

No raw trajectories, logs, model outputs or review archives are committed. Historical
evidence, `.gitignore`, `uv.lock` and all unrelated user changes remain intact.
The final seal records measured worker CPU, wall including the preflight allowance,
artifact bytes, source versions, exact local HEAD and workers=0. The8h wall /10 CPUh /
1GB artifact /zero-GPU bounds were respected. Public source-tool traffic is not byte-
metered; no dataset/model/public file was downloaded locally, and a conservative40MB
source-traffic allowance is disclosed below the250MB budget. Small orchestration
CPU is not fully metered; a600 CPU-second allowance is explicit.

Reproduce the fixed computations from the final commit into a **fresh** root, keeping
all existing sealed input roots immutable. The original missing blueprint cannot be
reproduced or inferred by these commands.

```bash
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1
REPLAY_ROOT="results/dsre-stage1/replay-$(date -u +%Y%m%dT%H%M%SZ)"
uv run --no-sync python scripts/dsre_finish.py --root "$REPLAY_ROOT" --stage initialize
for stage in e0 qualify; do
  uv run --no-sync python scripts/reboot_overnight_worker.py \
    --root "$REPLAY_ROOT" --name "$stage" --timeout 1200 -- \
    uv run --no-sync python scripts/dsre_prepare.py --root "$REPLAY_ROOT" --stage "$stage"
done
for stage in experiment analyze audit verify_analysis figures; do
  uv run --no-sync python scripts/reboot_overnight_worker.py \
    --root "$REPLAY_ROOT" --name "$stage" --timeout 1800 -- \
    uv run --no-sync python "scripts/dsre_${stage}.py" --root "$REPLAY_ROOT"
done
uv run --no-sync python scripts/reboot_overnight_worker.py \
  --root "$REPLAY_ROOT" --name validation --timeout 900 -- \
  uv run --no-sync python scripts/explanation_repair_finish.py --root "$REPLAY_ROOT" --stage validate
```

The existing generic validation stage is reused; its first focused subset is the
historical explanation tests, followed by the complete maintained suite including
all DSRE tests. DSRE-specific tests were also run separately. Ensure the new run
path is locally excluded before staging any source; never `git add .`. Final seal
verification is read-only and runs outside the worker, which refuses sealed roots:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python \
  scripts/dsre_finish.py --root results/dsre-stage1/20261113T144253Z --stage verify
```

G0 is supported for the qualified subset, while blueprint consistency is unavailable.
G1 is LIMITED_IDENTIFIABILITY: inadequate/ambiguous observable classes constrain the
problem, especially PushCube. G2 retains exact minimum-rule equivalences and the
strong stump/two-literal challenge. G3 does not establish a distinct methodological
contribution; known pure-rule search and witnesses are insufficient novelty on their
own. G4 remains unauthorized. The useful result is an auditable finite development
characterization and a concrete calibration-feasibility limit within the fixed DSRE
question. Stop for supervisor review, with no manuscript or new simulator campaign.
