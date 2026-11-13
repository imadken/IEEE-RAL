# DSRE Stage 1: fixed development protocol

Question: **What is the smallest observable evidence sufficient to justify a robot
recovery action relative to its actual intervention outcomes?** Authority is the
supervisor's complete execution contract, copied byte-for-byte to
`DSRE_CODEX_STAGE1_EXECUTION_CONTRACT.md` and the fresh evidence root. Reviewed base
`116dc45b33796b59df7ba6c0332bb120e60a3b9d`; branch
`research/dsre-stage1-development`. All prior source files and user changes are
preserved. Raw outputs stay under a new `results/dsre-stage1/` root, excluded through
`.git/info/exclude`, with no change to `.gitignore` or `uv.lock`.

## Missing primary specification

The named `DSRE_STAGE1_RESEARCH_BLUEPRINT.md` version 1.0 was not supplied in the
attachment and was not found in repository, attachment contents, Desktop, Downloads,
Documents or a home-wide hidden filename search. No substitute blueprint or version
1.0 is invented. The execution contract itself specifies the following executable
work. Blueprint consistency and the supervisor's precise intended amendments cannot
be certified; the final gate must retain this missing dependency. This limitation
does not prevent the independent algorithm tests and contract-defined development
comparisons. No requests for intermediate permission are needed.

## Finite decision contract and proof assumptions

Scope fixes task, controller identity, action repertoire, 70-step/3.5-second horizon,
terminal binary task-success utility, epsilon=0 and adequacy v=1, feature dictionary
and available channels. Both successful actions are acceptable; neither-success is
inadequate despite zero regret. With these binary utilities and any epsilon in
[0,1), v=1 makes action acceptability exactly V(a)=1. This elementary equivalence is
retained, not promoted as a new theorem.

For query-known literals E, a reference row matches unless at least one E literal
has a **known opposite** value in that row. UNKNOWN is conservatively compatible.
Evidence is valid iff at least m_min=2 reference rows match and the chosen action
is acceptable on every matched row. Missing outcomes invalidate universal support;
unknown outcomes are not zero successes or invented measurements. Choose globally
minimum cardinality, then larger support, continue-first action, lexical literals.
Empty evidence is valid when justified over the full reference scope; zero-match
rules are invalid. Support counts checkpoint rows; independent seed groups are
reported separately and remain the uncertainty/resampling unit.

For every bad row and candidate action, collect known-opposite query predicates.
Evidence must hit every such difference set. A bad row with an empty difference
set cannot be excluded with the available query observations. This characterization
is tested independently by exhaustive enumeration, not asserted as novel theory.
For each necessary selected literal, deleting it must expose a concrete bad row.
Deleting a literal expands support, so cannot alone violate the minimum support.
Insufficiency reports scope mismatch, unqualified/missing outcomes, lack of support,
observation-equivalent incompatible acceptable actions, inadequate repertoire,
missing observations, or independent calibration insufficiency as appropriate.
Reasons may coexist; witnesses are explicit IDs, compatible observations and measured
outcome pairs, never an invented root cause. IDs/hidden condition names are audit-only.

The certificate's table-relative action is distinct from a deployable action.
Calibration is UNASSESSED in all reused-data experiments. A later failed calibration
gate abstains without rerouting to another action. No physical-safety guarantee,
causal discovery or reduced sensor-acquisition cost follows from evidence length.

## Frozen observable dictionary before method comparisons

`config/dsre_stage1.json` freezes all choices before DSRE scores. Use only the
registered complete-prefix history at or before the checkpoint; no continuation
frames enter phi. Current values use the last prefix observation; history uses the
first and last prefix observations. Distances/displacements/apertures are metres;
times retain the recorder's simulator seconds. Missing/nonfinite channels are UNKNOWN.

| Predicate | Definition | Input and availability | Origin/qualification |
| --- | --- | --- | --- |
| goal_near_03 | distance(object, goal) <= .03 | observed obj_pose and goal_pos | prior fixed 3 cm projection; goal proximity is not a success flag |
| hand_object_near_04 | distance(tcp, object) <= .04 | observed tcp_pose and obj_pose | frozen cube-width-scale geometry |
| goal_progress_005 | first goal-distance minus current >= .005 | first/current observed poses and goal | frozen 5 mm change; UNKNOWN if history missing |
| object_moved_005 | object displacement from first >= .005 | first/current obj_pose | frozen 5 mm change, not outcome progress labels |
| gripper_closed_04 | sum(abs(last two finger qpos)) <= .04 | robot agent.qpos, requires two finger joints | fixed aperture proxy, not proof of holding |
| hand_above_object_03 | tcp.z - object.z > .03 | observed tcp_pose and obj_pose | frozen vertical geometry |
| simulator_grasped | supplied is_grasped Boolean | PickCube simulator observation; PushCube missing -> UNKNOWN | privileged diagnostic addition only |
| simulator_contact | recorded robot_object_contact Boolean | simulator contact-derived field | privileged diagnostic addition only |

Primary analysis uses the first six. Simulator-supplied object/goal poses are treated
as a **declared pose-estimate interface**, not a demonstrated real perception system.
No realistic grasp/contact estimator is invented. Privileged analysis adds the last
two, never pooling its results with the primary observable-channel analysis. Source
file/hash, exact timestamps, measurements, thresholds and missingness are preserved
per row. Neither condition names (offset002/misaligned), task success, hidden physical
position/contact arrays nor future action outcomes are runtime feature values.

Sensitivity variants are fixed: remove both history predicates; remove goal_near and
goal_progress; quantize supplied pose coordinates to nearest 2 cm before applying the
same predicates; mask one query channel by id-SHA modulo six while leaving training
channels unchanged. All methods receive identical variant inputs. Additional support
sensitivity m_min=1/5/10 is descriptive, never used to replace the primary result.

## Qualified paired development table

Use actual registered development and old confirmation source directories from
`results/recovery-claims/20261112T152155Z`, PickCube/PushCube only. Every old seed is
now development. Verify each source against the historical seal, both fresh-prefix
branches against the same registered prefix/physical checkpoint and controller
memory, model identity, action count/time, prefix fidelity and raw terminal success.
No native-snapshot substitution. Preserve exclusions and exact failure reasons.
Audit same-parent/action start differences and per-step fidelity using existing
qualified tolerances. Missing qualifications are exclusions, not guessed outcomes.

Report four-way (continue-only/recover-only/both/neither) prevalence before method
tables. Primary utility is terminal success over the fixed horizon. Report already-
successful starts separately; a maintained successful state is not new recovery.
First-hit utility and failed-start results are separate diagnostics; never silently
replace terminal labels to improve a method. Parent is task/seed/condition/checkpoint;
both conditions for a seed remain grouped for all splits and uncertainty. Repeated
certificate variants and trajectory frames never increase physical sample size.

## Strong baseline definitions, frozen before outcomes are scored

All methods get the same reference rows, channel variant, minimum support and
available paired outcomes. Query objects contain no outcome labels. Model fit uses
reference groups only. Run five deterministic hash-ranked, balanced parent-seed
folds per task, with both conditions together. Separately illustrate full-table
certificates; these are not cross-fit or deployment results.

| Method | Fixed implementation and evidence contract |
| --- | --- |
| DSRE | exact d<=8 subset search, universal adequacy, canonical ties, all witnesses |
| B0 | always continue / always recover, empty evidence; boundary controls |
| B1 | strongest matching rule library with at most one / two literals; outcome-trained; mean utility >=.9; minimum length/support/action/lex ties |
| B2 | outcome-four-category CART-style Gini trees, depth1/2/3; mean utility >=.9 at leaf; path literals; depth3 cost-complexity pruning alpha=.01; unknown traversed feature -> abstain |
| B3 | saturated full-pattern conditional outcome table, a simple full-information predictor; conservative matching; choose larger conditional mean utility with minimum support and mean >=.5; output all query-known facts |
| B4 | exact smallest rule preserving B3's action label over reference signatures, including B3 abstentions as differing labels; not an outcome-adequacy certificate |
| B5 | exhaustive outcome-aware rules, conditional mean success/paired ATE, mean >=.9, same rule grammar/support/ties; DISCRET-inspired adaptation, no claim of reproducing its learned synthesizer |
| B6 | exact adequacy criterion, greedy lexical deletion for each action then canonical choice; subset-minimal, not necessarily minimum |
| B7 | plain exact universally adequate rule, independent implementation, no witness rendering; mathematically equivalent decisions/evidence to DSRE |

Unknown-reference values remain conservative in rule matching, including tree path
support. CART retains the full four-outcome histogram and marginal utility per
action; both/none are not forced into opposite binary labels. Unknowns in training
are fractionally passed to both children for split scoring; runtime cannot silently
interpret UNKNOWN as false. Pruning uses only reference data and fixed alpha.
No validation-outcome architecture or threshold search. The full B1/B2/B3/B5 mean-
utility frontier at fixed targets 1/.95/.9/.75/.5 is reported, with unavailable matched
coverage/error comparisons marked infeasible. At target 1, B5's binary mean purity
equals DSRE/B7 universal acceptability: disclose the exact equivalence.

## E0, E1, metrics and calibration

E0 includes all ten specified cases and a genuine greedy counterexample if found:
query 111; continue-bad rows have difference sets {a,b} and {a,c}; exact {a} beats
greedy deletion of a first, which leaves {b,c}. An independent enumeration and
independent difference-set oracle check exactness, tie selection and witnesses on
fixed random small tables, including UNKNOWN and absent outcomes. Authored E0
tables are logical tests, never simulator evidence.

E1 reports per-task coverage, emitted numerator/denominator, acceptable action
membership, absolute terminal success, regret, inadequacy, cardinality conditional
on recommendation, exact/greedy runtime, policy/outcome disagreement, collisions,
insufficiency types and examples. An abstention is not a successful task. Bootstrap
2,000 paired draws over task/seed groups, both conditions together. Sparse strata
and template-/category-induced constant differences are disclosed; degenerate
intervals are not population equivalence or a generalization guarantee. No per-frame
bootstrap or repeated-rule pseudoreplication. Matched frontiers use existing fixed
operating points, never selecting thresholds on held-out outcomes for deployment.

Frozen calibration interface: alpha=.10; delta=.05 divided across four task/action
strata (.0125 each). Count N/K for the complete pre-frozen router, not individual
certificates. One-sided exact binomial upper bound; enable iff bound<=alpha. Verify
zero-error bound 1-delta_a**(1/n); N=0 gives no qualification. Independent new parent
IDs must be disjoint from fitting/development IDs; repeated parents are rejected.
No rerouting after disabling a stratum. No calibration guarantee from reused data.
Report optional alpha=.05 only as planning sensitivity. Plan 200 calibration and
200 confirmation fresh parents per task in separate seed pools, exactly one fixed
registered condition per seed to avoid counting two dependent conditions as
independent calibration parents. Estimate routing/sample/cost feasibility; do not
execute physics. Later execution requires supervisor review.

## Budget, gates and evidence

Eight hours wall, ten measured CPU core-hours, zero GPU/paid APIs/new simulator
continuations; <=250 MB public source downloads and <=1 GB artifacts. Initial
preflight time allowance and small unmetered CPU overhead are disclosed. Existing
bounded foreground worker enforces a final 60-minute reserve; no new analytic job
after hour seven. No other jobs are stopped. All attempts, source hashes, qualification
exclusions, model/rule outputs and numerical audits are local. Tests/Ruff/format
checks precede sealing and a scoped local commit. No push, manuscript, new controller,
new failure condition, new research question or automatic continuation.

G0 correctness/provenance must pass for used rows; missing blueprint remains a
separate specification limitation. G1 may be LIMITED_IDENTIFIABILITY; continue valid
comparisons. G2 preserves stump/rule/B7 ties. G3 requires a substantive gap beyond
known minimal rules and paired recovery, not merely passing tests or witness UI.
G4 fresh-physics calibration/confirmation is NOT_AUTHORIZED. Final gate chooses
STAGE1_READY_TO_DRAFT / PRELIMINARY_ONLY / BLOCKED against actual evidence.
