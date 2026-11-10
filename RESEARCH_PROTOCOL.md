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
