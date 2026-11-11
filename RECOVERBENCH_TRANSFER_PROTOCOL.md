# Affordance-constrained recovery transfer: supervised campaign protocol

Authority: the supplied 11 November 2026 RecoverBench campaign. Reviewed base
`86fcf8e59d526b5b81eb798b5deb379d19d3eae8`; branch
`research/affordance-recovery-recoverbench`; run
`results/recoverbench-transfer/20261111T172759Z/` (RUN).
Earlier DUAL-REC, monitoring and SVR negative conclusions remain unchanged.

## Fixed questions, stages and stop conditions

RQ1 concerns source-to-target recovery transfer; RQ2 taxonomy versus physical
state; RQ3 explicit applicability versus identical state retrieval and learned
selection; RQ4 task, configuration and original D0/D1 shifts. No alternative
research question, synthetic success label, new fault or task is authorized.

Execute compatibility and source-library qualification before claiming recovery
selection is meaningful. Only if those gates pass, freeze the candidate library,
transfer, features, splits, B0–B5 definitions and applicability checks in a local
commit before comparative evaluation. The main contrast is ACRR/B4 versus B2
and B3, not random retrieval. If source replay or dependencies fail, finish the
prespecified independent release-interface/transferability audit (Cases D/E),
preserve failed attempts, report BLOCKED or ACTION_COVERAGE_FAILURE and stop.
Do not manufacture recoveries or fit a selector to behavior-group labels.

Case A requires the registered robustness/constraint ablations; Case B a complete
negative transfer characterization; Case C quantifies useful recoveries rejected;
Case F reports any verified prior-method equivalence. No post-qualification
constraint tuning, new score or additional project follows a negative result.

## Pinned primary release and isolated stack

- RecoverBench source: `ErrorRecoveryBenchmark/ErrorRecoveryBenchmark`,
  `88f6fedab46dd130a617e058f8d0d05a42c2ea3d` (v1.2.0 release content).
- Dataset tag `v1.2.0` resolves to
  `f2f9cfe9ad2135f40c0b47a70269cc806541b58d`; use this immutable revision.
- robosuite 1.4.1: `c848ca848020d0c4ccdd10c5056bd06f2a195ba2` plus only its
  published RecoverBench patch.
- MimicGen: `72bd767c255545f462e7ccfb2731f2e5d4c1d9bb`, no patch. Its module
  reports 1.0.1 while the original package setup reports 1.0.0; preserve this fact.
- Task zoo: `74eab7f88214c21ca1ae8617c2b2f8d19718a9ed` plus only the released
  setup-dependency patch.
- New environment: Python 3.10.12, MuJoCo 2.3.2, NumPy 1.26.4. The repository's
  Python 3.12 environment, installed modern simulator and `uv.lock` are untouched.

Archive bytes and SHA-256 values are retained locally. Initial downloads are
the 26 MB evaluation scenes, 99 MB training scenes and 126 MB MimicGen recovery
archive, all checked against release SHA256SUMS. Do not initially fetch the
8.9 GB training-data archive. The two required upstream seed files use MimicGen
dataset revision `33016f8a62c02334f929f2913af8fdd2a8a129e1`, verified against its
LFS SHA-256 values. Coffee's large seed file is conditional on the pilot gates.

Read the actual code, dataset card, EVALUATION, DATA_FORMAT and DATASHEET.
Targeted primary positioning covers RecoverBench, FLARE, MAGMA-GEN, REACH,
RoboRecover and VLA-FixBench; record inaccessible papers precisely rather than
substituting abstracts for a claimed full-paper inspection. Recovery reuse,
object-centric correction, task selection, outcome learning and feasibility
checks are existing ideas. No general novelty or safety theorem is asserted.

## Official semantics and initial compatibility fixtures

Use the official `create_env` seed-HDF5 factory and `EnvWrapper` initially.
The original simulator's `_check_success()` is authoritative; no fallback
heuristic success definition. The official target protocol restores the stored
post-error state once, executes one uncounted neutral action, then allows at
most 500 control steps with first success after a counted action. Initial
`already_success` is diagnostic and does not alone earn recovery success.

The first lexicographic evaluation scene per pilot task is opened solely for
startup, three reset/three-neutral-step repetitions and fingerprint checks:

- pick_place: `v5_collision_eef_object_D0_0002d5b31c7e`.
- stack: `v5_collision_eef_object_D0_00731d8acf70`.

These preopened compatibility scenes are excluded from future held-out
confirmation. No other official evaluation scenes are used to fit or select
methods. Versions, robot/class, action dimension, controller convention,
fingerprint, restoration residual and physics time advancement are all recorded.
Observed startup XML mismatch is an unresolved blocker, not a silently waived
check. The official factory's PickPlace versus expected PickPlace_D0 class
difference is investigated using only documented release/controller interfaces.

## Source-library qualification registered before action replay

Use the small released MimicGen recovery archive first. Category selection
uses coverage alone: for each of groups A/B/E, maximize the minimum candidate
count across pick_place and stack, then total count, then lexical tie. This fixes
`grasp_wrong_pose`, `drop_at_wrong_place`, `trajectory_regression`. Per task,
category and degree, choose the first two archive members lexicographically:
**24 source candidates** in total. No failed source is replaced.

Exact candidates/rules are in compact config and local
`source_qualification_registration.json`, whose pre-replay SHA-256 is
`74c121bee6c653293402f31910cf713231314f19c53dab62205c068fd431f178`.
Use each recorded starting state and all recorded controls, capped at 1,500
for source diagnostics; disclose any cap exclusion. Record both original
no-neutral alignment and the official one-neutral interface. Original MimicGen
source stores T pre-action states and T actions, unlike human T+1 recordings.
Use source code to determine alignment; do not shift it to maximize success.

For the first registered source per task, repeat three times per variant from
independent resets. Measure official first-success, action/control counts,
contacts, finite states, initial/replayed physical poses and trajectory errors.
Offline state reconstruction can audit forward kinematics and stored features;
it is never counted as recovery execution or used to overwrite state during
a control rollout. Actual execution initializes once and thereafter only steps
the recorded/adapted actions. Preserve all failures and compatibility variants.

Engineering GO requires exact intended environment/controller compatibility,
including original fingerprint checks, at least 80% replay success per task
under the original recording alignment, and an executable library with at least
20% development-scene coverage using three source-distinct candidates where
available. These are engineering screens, not population-level guarantees.
If they fail, fixed compatibility diagnostics and the release-interface fallback
must finish; an unqualified library does not authorize method comparisons.

## Conditional comparative pilot requirements

If qualified, start with pick_place and stack; coffee is conditional. Keep the
three fixed categories and original D0/D1 definitions. Target 12 independent
development scenes per task/category, grouped by source trajectory/demo; retain
shortfalls without replacement. Source candidates and target scenes must be
disjoint. Freeze all features, scales, transfer frames, constraints and thresholds
using training data only before any held-out evaluation.

B0 is random eligible retrieval; B1 uses error/RBG labels and is explicitly an
oracle-label-assisted reference; B2 state nearest-neighbor and B4 ACRR share
feature channels, candidate count/library and transfer operator. B3 is a small
outcome/applicability predictor fitted only to executed development transfers;
B5 selects offline from the same executed candidate outcomes. No B5 outcome or
simulator fault metadata enters deployed B2/B3/B4 features. Uncertain physical
conditions remain uncertain. Separate proven hard necessities, learned soft
scores and unverified conditions; no small-sample correlation proves necessity.

Execute rejected candidates independently from exactly the same target states
to count false rejections, and retain a no-applicability ablation. Primary task
recovery uses the common 500-action horizon and official first-success predicate;
abstention is failure per attempted target, not successful avoidance. Record
incorrect acceptance/rejection, coverage/fallback, costs/control steps, selection
runtime, contact/feasibility diagnostics, task/error/RBG/degree and geometry shift.
Provide scene/source-cluster paired confidence intervals and full success versus
coverage/rejection frontier. Repeated candidates/frames are not independent.

The method screen is approximately five percentage points or greater recovery
improvement over the strongest comparable B2/B3, with paired interval excluding
zero and acceptable false rejection/action costs. Favorable but uncertain effects
are INCONCLUSIVE; equivalence/inferiority gives METHOD_NO_GO. Poor candidate
coverage gives ACTION_COVERAGE_FAILURE. Normal SR accompanies any reported RSR;
this bounded task subset is not the official six-task Table 2 leaderboard.

## Evidence, resource and repository boundaries

Maximum: eight campaign wall hours, twelve measured CPU core-hours, four GPU
wall-hours only for necessary rendering/small approved models, twelve GB new
data/artifacts, zero paid calls/large-model training. Bounded foreground workers
record commands, exits, source hashes, wall/CPU and artifact sizes. Prefer
headless privileged-state physics with equal observations across methods.
Source-preparation failures and partial/unsupported runs remain explicit.

The final audit independently recalculates raw outcomes, split/source integrity,
oracle leakage, rejected-candidate outcomes and action-budget equality where
those phases execute. Missing phases have no invented rates or confidence
intervals. Run the full relevant regressions, Ruff and formatting. Hash all
historical evidence and final local artifacts, report measured resource scope
and stop only at an authorized scientific/resource boundary with no jobs left.

Raw downloads, logs, NPZs, detailed results and plots stay in locally excluded
RUN. The user's `.gitignore` bytes remain unchanged. Commit only scoped
source/tests, protocol/report and compact necessary input configuration; never
attempt GitHub authentication or pushing. Publication remains manual.
