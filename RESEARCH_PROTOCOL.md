# DUAL-REC research protocol

## D5–D7 preregistration v1 — 10 November 2026

This gate tests **H1 only**: do realistic executed manipulation failures have
passively overlapping histories yet favor different direct recoveries? No
positive result is assumed. H2/H3, probing, information-effect interventions,
planners, training RL/LLMs and manuscript work are outside this authorization.
`RESEARCH_EXECUTION_CONTRACT.md` is the supplied supervisory contract.

Base: `e4d73714eaac240a626ccece2eae34f6cfd8b4c8`, containing audited D4 commit
`f9d43f438d48ad818ef8974edfad39c8d97c9d7c`. Dedicated branch `dual-rec/d5-d7`.
All prior evidence, simulator code and `uv.lock` stay unchanged. CPU physics,
Panda `pd_ee_delta_pos`, two numerical-library threads and the pinned uv environment
are required. The A4000 is used only to permit task material construction.

This version and `config/gate_d5_d7.json` are committed **before any comparative
recovery data**. Values will not be changed in response to performance. Engineering
API corrections must be logged, preserve failed trials and leave these definitions
unchanged. No replacement candidate is added after seeing results.

### Candidate registry and physical changes

Start and remain on PushCube. We register two primary families and one negative
control pair, six unique conditions in total. No automatic task expansion.

| Family | First condition | Second condition | Motivation / possible falsification |
|---|---|---|---|
| surface_vs_alignment | cube static/dynamic friction 1.2 | +0.07 m lateral pusher waypoint error | surface resistance versus missed/eccentric contact; alignment may be immediately observable |
| surface_vs_payload | cube friction 1.2 | cube mass **and inertia** multiplied by 8 | rubber-like high resistance versus a uniform steel-density payload; Panda may overcome both |
| mild_surface_control (negative) | cube friction 0.3 | cube friction 0.5 | distinct mild surfaces expected to admit a common good recovery; this expectation is measured, not a label |

An additional `native` condition is the unperturbed task negative control. Material
coefficients are hypotheses about plausible dry contact, not calibrated real
surfaces. The 4 cm nominal cube has about 0.064 kg mass; eightfold mass corresponds
to about 8000 kg/m³ without changing geometry. For a uniform density change, scale
all three principal inertia components by the same factor, retaining center of
mass and axes. Use the pinned SAPIEN `PhysxRigidBodyComponent.set_mass` and
`set_inertia` APIs; read both back. Assign fresh per-shape material objects to avoid
changing other actors' surfaces. Record every original and new value, including
unchanged properties. If this cannot be implemented consistently, exclude mass
and report the omission rather than running an inconsistent condition.

Parameter edits occur after reset and before control action 0. The alignment
condition is a programmed pusher waypoint error during the initial execution,
not a hidden sensor corruption: add +0.07 m to the cube and goal y waypoints used
by the normal controller. It changes physical contact through real robot actions,
not object teleportation. The actual actions and TCP/object histories remain
available to the classifier. Its obvious visibility would count **against** H1.
No material, mass, waypoint error, fault identifier or seed is passed to a recovery
controller or passive feature constructor.

### Executed failure definition and reconstruction

Use the existing D4 PushCube controller, with phase lengths 20 approach, 25 descend,
33 push, matching D4's complete successful reference path. At step 78, use a fixed
10-step window. A qualifying failure must be task-unsuccessful and either:

1. reduce planar cube-to-goal distance by less than 0.01 m over that window
   (no progress / stall), or
2. have no robot–cube contact in that window (missed/lost contact).

The normal manipulation and all histories must be actually executed. Merely
running out of time while still making progress with contact is not a qualifying
failure. Native success/failure rates and distance/contact traces distinguish
fault effects from ordinary random non-success. Record stalls and missed contact
separately, including overlaps. Never filter samples by later recovery outcome.

For **every** alternative recovery: create a new scene/environment, reset the same
seed, reapply parameter edits at step 0, execute the entire exact stored 78-action
prefix, verify the reconstructed branch against its independently generated
reference, then execute that recovery. No ManiSkill snapshot restoration, start
state substitution or manual pose matching. Store both numerical state comparison
and exact contact/outcome comparison at every prefix step and the branch point.
Use the D4 frozen limits: position 1e-5 m, angle/qpos 1e-4 rad, velocity and
observation 1e-4, time 1e-9 s; contacts/outcome exact. A mismatch stops the gate.

At the first meaningful candidate, inspect ten independent base seeds using the
complete perturbation schedule. The first ten development seeds are reserved for
this reproducibility audit (no extra independent samples). At minimum audit all
conditions mechanically, even if none meets the failure/ambiguity criterion;
do not call non-failure reconstructions a scientific failure-family validation.
All subsequent branches also undergo the same parity test. Store failed checks.

`FailureScenario` records simulator/task/version, seed, allowed channels,
evaluation-only fault, physical-edit step/readback, exact actions, trigger and
source hashes. Seeds/configuration travel with the recipe, never with policy inputs.

### Recovery controllers, common budget and utility

Three controllers, each 50 control steps (2.5 s at 20 Hz), no early stopping:

- `continue`: close gripper (-1) and target the observed goal xy at observed cube z;
  `delta = clip((target - tcp)/0.1, -0.25, 0.25)`.
- `slow`: same target and feedback, clip bounds +/-0.08 instead of +/-0.25.
- `recontact`: six steps lift toward current TCP +0.08 m z; twelve steps move above
  the **currently observed** cube at [-0.055, 0, +0.10] m; ten steps descend behind
  it at [-0.055, 0, 0]; twenty-two steps push as `continue`. Lifting is a fixed
  six-step segment; its first TCP target is frozen at recovery start to avoid an
  unintended continuously ascending target. All other targets use current sensors.

All conditions get the identical action set and budget; recovery functions take
only permitted observation packets and a recovery name, never scenario metadata.
They issue physical normalized Cartesian/gripper actions using the existing
controller. There are no direct external recovery forces or simulator-state edits.

Success S is the task's actual final success indicator. Effort E is the mean of
`norm(action_xyz)/(sqrt(3)*0.25)` over all 50 steps, clipped to [0,1]. Time fraction
T is executed steps/50. Raw utility is `S - 0.05 E - 0.05 T`, and normalized utility
is `(raw + 0.10)/1.10` in [0,1]. Fixed full horizon means equal time costs;
effort still differs. Neither friction nor fault labels determine utility or a
preferred recovery. Report success and utility separately. Report unconditional
outcomes for all setups and failure-conditioned outcomes; only actual failed
setups can support H1. No hindsight-dependent failure or utility changes.

### Permitted histories and passive diagnostics

No added observation noise, no quantization to force overlap, no masking obvious
state channels. The ideal state-based robot observes **all original state_dict
channels** (qpos, qvel, TCP pose, cube pose, goal pose), cube linear/angular
velocity, its current drive targets/velocities, applied generalized forces,
link incoming joint spatial forces if the pinned CPU API is accessible, robot–cube
contact flag, elapsed time and every actual issued action. Record reset plus all
78 control-step observations. Renderer images are not enabled in this state-based
task; the noiseless cube pose already provides ideal object tracking. Spatial
forces are described as robot joint-reaction measurements, not inferred contact
impulses. Verify API shapes/finite readings; an inaccessible critical sensor is
reported, not silently filled with zeros.

Feature constructor accepts a dedicated observation/action history schema only.
It rejects extra keys and includes every declared numeric channel at every time;
no latent parameters, condition/family strings, seeds, scenario IDs, solver state,
contact body names, success labels, recovery actions or future measurements enter
features. Oracle metadata remains evaluation-only. Full simulator contact pairs
are retained for engineering parity but not used as named classifier features.

Baselines: L2 logistic regression and nonlinear RBF-kernel logistic regression,
implemented with pinned NumPy/SciPy (no new packages). Standardize using development
training data only, flooring scale at 1e-6. RBF bandwidth is the median nonzero
squared training distance. Choose regularization from [0.01,0.1,1,10] by fourfold
**base-seed grouped** development cross-validation, minimizing log loss; tie by
larger regularization. Fit each family separately on the balanced full setup
cohort, and also on matched failure states if both classes have sufficient groups.
Qualification labels/outcomes never choose hyperparameters. The nonlinear baseline
is required to reduce reliance on linear separability; neither model proves
structural non-identifiability. Report AUROC, balanced accuracy, Brier score,
log loss, 5-bin ECE, per-seed predictions and calibration limitations.

### Splits, estimates, uncertainty and gate criteria

Development: base seeds 1000–1015 (16). Qualification: untouched seeds 2000–2007
(8), opened only after development model/hyperparameter freeze. All fault
conditions/recoveries for a base seed stay together. This is 24 initial independent
seeds per condition, below the cap of 40; replay checks reuse development seeds.
Physics parameter values are fixed configurations; no physical-configuration OOD
generalization is claimed. A seed split is not a substitute for OOD confirmation.

Use 2,000 bootstrap resamples clustered by base seed, preserving matched fault
conditions and action pairs, fixed analysis RNG seed 7321. Report 95% intervals
for success, utilities, differences, classifier metrics and disagreement fractions.
For the primary reversal decision, report simultaneous conservative 98.75%
percentile intervals (four directional assertions across two primary families).
Discrete small-cohort intervals may be degenerate; also give Wilson success
intervals and independent sample counts. These are screening intervals, not
publication-level confirmation or guarantees of coverage.

Primary recovery contrast is **continue minus recontact**. `slow` is a measured
alternative, not a post hoc way to choose a favorable primary contrast. A reversal
requires mean contrast >= +0.10 in one condition and <= -0.10 in the other, with
the corresponding simultaneous intervals excluding zero, on matched failures
in qualification. Report all three recovery optima, fraction of matched failure
seeds with disagreement (also disagreements with >=0.10 regret), and the utility
loss from a common recovery. Ties within 1e-8 use registry order; tiny effort-cost
ties are not meaningful conflict. Minimum four matched failed qualification seeds;
otherwise insufficient samples cannot support GO.

Physical overlap: report matched faults' differences in final pose, velocity,
robot/TCP signals and complete standardized history. Compare cross-fault nearest
history distances with the 95th percentile of within-class nearest distances in
development. Predeclared ambiguous subgroup requires this neighborhood overlap
AND held-out probabilities in [0.25,0.75] for **both** diagnostic models. At least
20% of matched failed qualification seeds and at least four independent seeds
must qualify. Apply this rule as written to all samples, not handpicked successes.
Classifier uncertainty alone is not physical overlap. Report perfect state/action
separators if present. Strong passive separation or a common successful recovery
is evidence against the candidate; low classifier accuracy alone is not GO.

GO requires a physically validated family, independent reconstruction, nontrivial
passive overlap and measured reversal meeting the above criteria. Both mechanisms
must produce failures in at least 25% of their qualification setups. If a mechanism
never induces the registered failure, or one recovery dominates, report NO-GO for
that candidate. If sample size/uncertainty prevents a decision, report INCONCLUSIVE.
Reconstruction failure or unavailable critical support means BLOCKED. The mild
surface pair must be reported even if its expected common optimum does not occur.

### Limits, immutable evidence and stopping

At most 180 minutes instrumented worker wall, 6 CPU core-hours, no GPU physics or
training, no more than 40 initial seeds per condition and three registered pairs.
`scripts/gate_command.py` enforces remaining budgets, process-group timeouts and
retains UTC start/end, exit/CPU/wall status, versions and source hashes. Run all
simulation workers serially, bounded per cohort batch. Every worker gets a unique
log/output. A crashed worker retains its partial JSONL; restart only into a new
path with the deviation recorded. No stale result substitution.

Use `results/gate-d5-d7/<run-id>/` for immutable configuration, scenarios, raw
histories, branch checks, outcomes, classifier splits/predictions and manifests.
Check in small evidence; compress large text trajectory logs, retain SHA-256 and
an exact reproduction recipe rather than caches or huge arrays. Preserve all
failures and negative controls. `GATE_REPORTS.md` is the sole cumulative gate
outcome document. Commit, push only `dual-rec/d5-d7`, and stop after D7 regardless
of outcome. No probe/counterfactual-diagnosis/planning implementation is authorized.

## Execution notes and reproduction (does not change v1)

The scientific preregistration is commit `f9e158b` (full SHA from `git rev-parse
f9e158b`). The initial rollout implementation is `5e83822`, grouped diagnostics
are `7b8b622`, and the development-only model seal is `091002f`. The full commit
IDs, per-command source hashes and exact worker arguments are retained in the
published command ledger. No fault values, recovery definitions, horizon, feature
channels, splits, utility or gate thresholds were changed after performance was
observed. Later code changes harden seed-budget validation, administrative source
commit timing, hashes and evidence packaging. Initial-effect summaries are
explicitly descriptive; they are not additional decision criteria.

The actual run is `results/gate-d5-d7/20261110T222449Z/`. Complete compressed
scenario histories, recovery trajectories and fitted model arrays stay locally
under that path. Compact complete recipes, outcomes, replay checks, all
qualification predictions, development CV scores, small prespecified examples,
and SHA-256 manifests are published. Reproduction regenerates the large files;
matching numerical results and feature fingerprints is the target, not identical
gzip headers (which include creation times). Nothing requires a model download,
credential, GPU physics/training, or a service left running.

A reviewer can reproduce on the qualified Ubuntu/A4000 setup in well under the
180-minute / 6-core-hour limits. All simulator commands require host rendering
device visibility; the restricted sandbox can hide a healthy device. Use a new
root and run the commands **sequentially**. The worker wrapper enforces the
aggregate budget and records every worker exit. Any failed prefix check stops the
gate; do not skip failures or reuse a prior result directory.

```bash
set -euo pipefail
bash scripts/install.sh
source scripts/env.sh
GATE_RUN="results/gate-d5-d7/replica-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$GATE_RUN"
# Create a new preservation inventory before any workers.
uv run python - "$GATE_RUN" <<'PY'
import hashlib, json, subprocess, sys
from datetime import UTC, datetime
from pathlib import Path
root = Path(sys.argv[1])
files = subprocess.check_output(['git', 'ls-files', 'results'], text=True).splitlines()
files += ['uv.lock', 'pyproject.toml', 'AGENTS.md']
record = {'utc_start': datetime.now(UTC).isoformat(),
          'base_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
          'preserved_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}}
(root / 'initial.json').write_text(json.dumps(record, indent=2))
PY
bounded() {
    local command_name="$1"
    shift
    uv run python scripts/gate_command.py --root "$GATE_RUN" \
        --name "$command_name" --timeout 900 -- "$@"
}
bounded preflight uv run python scripts/preflight.py --output "$GATE_RUN/preflight/hardware.json"
bounded push-smoke uv run python scripts/qualify.py --task PushCube-v1 --states 1 --replay-mode prefix --output "$GATE_RUN/smokes/push"
bounded pick-smoke uv run python scripts/qualify.py --task PickCube-v1 --states 1 --replay-mode prefix --output "$GATE_RUN/smokes/pick"
bounded lift-smoke uv run python scripts/qualify.py --task Lift --states 1 --output "$GATE_RUN/smokes/lift"
for offset in 0 4 8 12; do
    bounded "development-$offset" uv run python scripts/gate_rollouts.py \
        --split development --offset "$offset" --count 4 --output "$GATE_RUN/development-$offset"
done
bounded fit uv run python scripts/gate_analysis.py fit --root "$GATE_RUN" --output "$GATE_RUN/fitted"
# Keep fit_plan.json/models hash as the seal before opening qualification.
for offset in 0 4; do
    bounded "qualification-$offset" uv run python scripts/gate_rollouts.py \
        --split qualification --offset "$offset" --count 4 --output "$GATE_RUN/qualification-$offset"
done
bounded evaluate uv run python scripts/gate_analysis.py evaluate --root "$GATE_RUN" --fitted "$GATE_RUN/fitted" --output "$GATE_RUN/evaluation"
bounded tests uv run pytest -q
bounded lint uv run ruff check src scripts tests
bounded format uv run ruff format --check src scripts tests
bounded source-assets uv run python scripts/manifest.py --output "$GATE_RUN/preflight/integrity.json"
uv run python scripts/gate_command.py --root "$GATE_RUN" --name audit --timeout 900 --finalize -- \
    uv run python scripts/gate_audit.py --root "$GATE_RUN" --output "$GATE_RUN/audit"
```

Stop the shell sequence immediately on any nonzero worker; the full actual
invocations/statuses, including fixed lint failures, are in `commands.jsonl`.
The sequence enables `set -euo pipefail` so a failed worker ends execution.
The loop grouping differs from the original one-seed start plus five-seed batches;
the initial configuration, independent seeds, exact individual action schedules
and scientific sample counts remain unchanged. The audit checks 144 scenario
instances, 432 fresh recovery branches and the designated ten-seed subset.
After reproduction, stop at D7. A different fault regime or action budget needs
a new supervisor-approved preregistration, not edits to this evidence.

## Overnight preregistration — 11 November 2026, v1

The new supplied `DUAL_REC_OVERNIGHT_CODEX_PROMPT.md` supersedes the old stopping
boundary for this invocation only. The requested root file was absent; the complete
attached contract is preserved verbatim there. Base is audited D7 HEAD
`66b464e64561ee18757b63e69e03b1b5b0abe5ab`; branch is
`dual-rec/overnight-20261111`. No remote, authentication, push or PR is attempted.
Prior D4/D7 evidence remains immutable. This section does not rewrite its outcomes.

Decision graph: preflight -> D7B severity calibration -> freeze -> reserved D7B
qualification. Only a complete D7B PASS permits A. NO-GO/INCONCLUSIVE or unavailable
scientific support routes automatically to B. A prerequisite failure routes to B
if resources permit. Invalid physics, GOLD replay disagreement, leakage, failed
preservation, or exhausted global budget stops experimental work as BLOCKED.

Global limits: eight elapsed hours including editing, twelve measured child CPU
core-hours, eight billion new artifact bytes (worker stops at 7.5 billion for
margin), two numerical threads, serial bounded simulation batches. D7B subcap is
135 elapsed minutes; A/B study subcap 240 minutes. `overnight_command.py` owns
bounded child process groups, CPU limits, periodic heartbeat/STATUS.json and
append-only batch progress/exit/resource records. Ceilings are not time targets.

### D7B: finite PickCube grasp scan and recovery qualification

Initial robot execution is D4's controller: 20 approach, 25 descend, 15 close,
30 lift/transport steps. No object teleportation, external force, reward edit or
controller-limit manipulation. Calibration uses four new seeds 3100–3103. The
finite severity grid is cube **and** both finger collision-material friction
(static=dynamic) [0.1,0.03,0.01], or a grasp-center waypoint x offset
[0.01,0.02,0.03] m (quarter, half, three-quarter of the 4 cm cube width).
Nominal controls retain original materials and centered waypoints. Finger/cube
material edits are fresh objects, with complete before/after readback; mass,
inertia, COM and restitution remain unchanged. Changing cube material also changes
cube/table friction. No contact-specific coefficient is claimed.

PhysX documents average material combination as its default, but this pinned
SAPIEN Python API does not expose a combine-mode getter. Record that limitation,
not a verified effective coefficient. Setting both grasp surfaces avoids relying
on a low coefficient on only one surface. These are plausible lubricated-contact
hypotheses, not calibrated material measurements. Primary official reference:
https://nvidia-omniverse.github.io/PhysX/physx/5.1.0/_build/physx/latest/class_px_material.html

A failure is triggered causally during execution, after step 70, by three
consecutive observations of no grasp plus cube lift <0.03 m while TCP is >0.06 m
above the initial cube; or a previously lifted cube (>0.06 m above initial) drops
at least 0.03 m without grasp. Stop the initial prefix at the event; otherwise
observe through step 90. Mark ordinary non-success without that event separately.
No recovery outcome participates in trigger/severity selection.

Choose the least severe grid value causing at least two failures in four executed
calibration seeds, provided nominal succeeds in at least three of four. Select
only by this incidence/readback/plausibility rule. Preserve all 28 calibration
runs. If either mechanism has no credible level, mark D7B NO-GO and enter B
without inventing another value. Freeze chosen settings in a local commit before
comparative recovery measurements or reserved-seed execution.

The development cohort is at most twelve base seeds 3100–3111, reusing calibration
seeds at the selected values. Qualification is eight untouched seeds 4100–4107.
Each of three conditions (nominal, low friction, offset) is executed for every
seed. Every recovery starts in a fresh environment at the same seed, physical
edits and exact full action prefix; all prefix records, contact pairs and numeric
sensor readings must meet frozen D4 parity. Never use ManiSkill snapshots.

Three 70-step recoveries, identical per-step normalized action bounds +/-0.25 and
closed gripper -1 except the declared regrasp-open segment:

- nominal: target the observed task goal with the closed gripper throughout;
- regrasp: 8 open/lift steps toward recovery-start TCP +0.10 m z; 14 open approach
  steps toward current cube +0.10 m z; 12 open descend steps to current cube center;
  12 close steps at the observed cube; 24 closed goal-transport steps;
- conservative: closed gripper, first 20 steps target current cube +0.06 m z,
  then transport toward goal; action translation clip +/-0.08 throughout.

Utility is frozen as `(S - .05 E - .05 T + .10)/1.10`, S actual final task success,
E mean normalized translation action norm (divide sqrt(3)*.25, clipped [0,1]),
T executed steps/70. Report success separately; do not count initially successful
controls as recovery successes. All declared recoveries are retained.

Full sensors: complete original task state numeric channels, object velocities,
robot drive targets/velocities, applied qf, incoming link joint spatial forces,
current grasp/contact flags, time and full issued action history. No contact IDs,
parameter values, labels, seeds or future outcomes enter features. Strict typed
sensor frames isolate these from evaluation-only recipes. Histories stop at the
decision event, padded only by last observed state and an explicit observed mask
up to 90 steps; never by future measurements.

The one lower-fidelity regime is fixed now, before outcomes: encoder resolution
0.001 (rad or m per joint), velocity 0.01, link-force resolution 0.5 N / torque
0.05 Nm after a three-sample trailing mean, and 10 Hz object/goal position tracking
at 5 mm resolution with one control-step delay. Derive vision velocity from past
sampled positions; do not use exact object velocity, named contacts, or simulator
is_grasped in this regime (Panda has no added tactile hardware). Keep complete
commands, proprioception and force history. This is an explicitly hypothesized
sensor configuration, not a calibration claim or post hoc ambiguity mask.

Reuse grouped-CV L2 logistic and RBF kernel logistic, training-only scaling and
regularization grid [0.01,.1,1,10], four development seed folds. Freeze before
qualification. Report both regimes and both classifiers; full-state separation
must remain visible. Primary contrast is nominal minus regrasp on matched failed
qualification cases. PASS requires both causes fail >=4/8, >=4 matched failed
seeds, opposite utility means with magnitude >=.10 and paired 95% intervals
excluding zero, plus >=25% and at least two matched failed seeds uncertain
(probabilities .25–.75 for both models) in the realistic regime. Uncertainty alone
is not a proof of unidentifiability. Fewer matched states or intervals crossing
zero is INCONCLUSIVE/NO-GO as the failed criterion warrants; automatically run B.

### Conditional A boundary

Only if the above gate passes, preregister at most two brief physical probes and
blind/adaptive information sets before new measurements, using development seeds
5100–5123 and qualification seeds 6100–6115. Cap 1,600 continuations. Compare
direct, probe-blind, probe-adaptive, information-gain and nominal decision-aware
selection with common action/cost budgets. Blind high-level selection cannot see
probe observations; low-level safety feedback remains common. Test leakage and
paired component estimates. No favorable outcome or publication claim is presumed.
If prerequisites fail, enter B once; no third project is authorized.

### Conditional B matrix: restoration validity, registered before new measurements

B does not assume ambiguous failures. It compares fresh full-prefix GOLD with the
**unchanged existing** ManiSkillReplay/RobosuiteReplay adapters, never weakened to
force an effect. PushCube conditions: nominal, consistent mass/inertia x8, and
previously documented +0.07 m y pusher misalignment. PickCube: nominal and the
fixed low-friction 0.01 cube/finger condition above, independent of recovery ranks.
Lift/MuJoCo: nominal and consistent cube mass/inertia x8. Fixed task/models remain
within condition; parameter edits occur before the first prefix action.

Seven new independent seeds per task: PushCube 7100–7106, PickCube 7200–7206,
Lift 7300–7306. No seed is shared with D7B/D7. Three stages: free-space at end of
20-step approach (verify no robot-object contact), first observed robot-object
contact after approach (Lift may use established two-finger grasp as an observed
contact event), and the fixed post-contact phase boundary (PushCube after eight
push steps, PickCube/Lift after five initial lift steps). Require earlier contact
for post-contact sampling. Unreached stages are reported as such with denominators,
never replaced by outcome-selected states.

Two fixed 40-step continuation policies per task: nominal continuation and an
alternative. Push nominal pushes toward goal closed; alternative is recontact
(6 lift, 10 above/behind cube, 10 descend, 14 push). Pick nominal transports to
goal closed; alternative is the conservative low-speed lift/transport profile
(first 15 steps cube +0.06 m, then goal, clip .08). Lift nominal continues the
existing OSC lift, alternative lifts slowly with translation clips .2 instead of
.6 (same target/gripper). Freeze success/time/effort utility as above with horizon
40; Lift action norm divides sqrt(3)*.6, ManiSkill sqrt(3)*.25.

For each sampled condition/stage/action, generate one native reference continuation
and its exact action tape; independently reset/replay prefix for GOLD, compare all
prefix state/contact records and identical continuation tape, then restore the
existing snapshot in the reference environment after its own native continuation
and execute the **same tape** for TEST. This natural prior continuation is the
snapshot-branch use being audited, not an injected degradation. Each action gets
a new reference environment. Native/GOLD/TEST all count as physical branches:
7 seeds x (3+2+2 task-conditions) x 3 stages x 2 policies x 3 = **882**, below 1,000.
Log immediate TEST parity failure as invalid reconstruction, but retain its outcome
to measure the consequence of using it; never relabel it qualified. Native-GOLD
parity failure stops all experimental work for integrity diagnosis. TEST exceptions
remain failed branches in denominators. No claim of hidden solver cache access.

Outcomes: immediate and continuation numeric/contact errors and their distributions,
restoration failures, per-action success/utility differences, preference reversals
and sign changes in paired nominal-minus-alternative effects. Aggregate by task,
condition and stage; bootstrap 2,000 times grouped by independent task seed, RNG
11817. Include Wilson intervals. Distinguish physical divergence without decision
change, and implementation/API omissions from intrinsic engine claims. Pairwise
rank reversals count only when GOLD and TEST contrasts have opposite signs with
both magnitude >=.01 (also report raw signs and >=.10); no tiny effort-only flip
is called substantively important. Seven seeds give limited precision. MuJoCo is
a positive implementation comparison, not a controlled engine-superiority trial.

After D7B and the applicable study, independently recompute all summaries from
compact trial records without the fitter, validate preserved hashes, run tests,
lint/format and commit locally. Preserve negative evidence and unknown novelty.
NO_PAPER_CLAIM unless a separately verified future contribution exists; no paper
draft, later campaign, extra fault hunt or remote publication is authorized.

### Overnight sensor clarification v1.1 — before fitting or inspecting recovery matrices

The nominal inspection exposes incoming spatial wrenches on 15 simulated links;
that is not a standard Panda hardware sensor suite. The realistic regime therefore
uses available encoder/velocity, drive-target and commanded-effort signals instead
of pretending every link has an installed six-axis transducer. Before any passive
model is fit or qualification data are opened, replace the v1 realistic-force
projection with trailing-three-sample commanded-effort estimates:
`clip(1000*(drive_target-qpos)+100*(drive_velocity-qvel), -100,100)+applied_qf`,
using the pinned Panda's nominal stiffness/damping/force limits. Round the first
seven joint torques to .05 Nm and two gripper forces to .5 N; retain drive targets
and velocities. This is an observable controller-model estimate, not a calibrated
current sensor or contact impulse. Full ideal-state baselines still receive the
entire measured spatial-force history. Camera/encoder settings, fault grid,
recovery controls, utility and all decision thresholds stay unchanged. This
clarification is motivated solely by actual sensor availability, before any
classifier performance or recovery matrix inspection; original v1 text remains
above and in its preregistration commit. No claim of real-hardware calibration.
