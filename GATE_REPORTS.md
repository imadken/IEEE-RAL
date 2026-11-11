# DUAL-REC cumulative gate reports

## D5–D7 — NO-GO; stopped after qualification

The registered candidates do **not** establish recovery-relevant passive ambiguity.
High-friction and consistent-payload conditions completed the initial task in
24/24 setups each. Alignment error produced 24/24 executed failures, but its
history is passively distinguishable and neither primary family contains a matched
pair of failed qualification states. Recontact helps this observable failure;
that is not evidence of ambiguous causes requiring conflicting recoveries.
H1 remains unestablished, not disproved for all physical regimes. No H2/H3,
probing, counterfactual diagnosis method, POMDP, planner, later gate or paper work
was implemented. **STOPPED_AT_D7 = true.**

### Source, registration and independence

- Branch: `dual-rec/d5-d7`; verified base `e4d73714eaac240a626ccece2eae34f6cfd8b4c8`.
- Audited D4: `f9d43f438d48ad818ef8974edfad39c8d97c9d7c`; D4 results and pinned environment are preserved.
- Preregistration: `f9e158bbcce648cff03abfe952b6b5d3feb7d90f`, before comparative recovery execution.
- Rollout source: `5e8382290af2c951b702450fb1a07250a7dd2116`; recovery/fault definitions stayed unchanged.
- Passive analysis: `7b8b6224f48ec6845c8e0da1595583f56b1d9176`; model-selection seal `091002f9678b19ec1ca2d7cfdfb90d1ffc6c6cc5`
  precedes creation of any qualification data. Later commits contain administrative
  checks and this report; the final pushed HEAD is supplied in the review handoff.
- D5 task: PushCube-v1/Panda/CPU only. PickCube prefix and Lift snapshot were each
  checked by one D4 smoke; the full D4 qualification was not rerun.
- 16 development and 8 reserved qualification base seeds; six conditions per seed,
  144 initial executions and 432 independent fresh-environment recovery branches.
  The 24 matched base seeds, not 432 branches or trajectory frames, define the
  independent nuisance groups. No ManiSkill snapshot restoration was used.

[Protocol](RESEARCH_PROTOCOL.md) is the cumulative scientific specification;
[contract](RESEARCH_EXECUTION_CONTRACT.md) is the supplied authorization. Immutable
machine evidence is under `results/gate-d5-d7/20261110T222449Z`. Final branch/HEAD/cleanliness and remote
verification are provided with the final handoff; no other branch is pushed.

### Measured failure mechanisms and physical consistency

All changes occur before control action 0; normal execution has 78 actual robot
steps. The fixed decision trigger uses non-success plus last-ten-step stall
(<0.01 m goal-distance improvement) or missed/lost robot–cube contact. It never
reads the condition label. All cube pose, velocity, robot state/action and contact
histories are retained. Parameter changes were applied by verified pinned CPU APIs,
with fresh cube materials and no vendor/task-code edits or external recovery forces.

| Condition | Mass kg | Principal inertia kg m² (each axis) | Cube static/dynamic friction | Initial failures dev / qualification |
|---|---:|---:|---:|---|
| native | 0.064000003 | 1.7066666e-5 | 0.3 / 0.3 | 0/16; 0/8 |
| high_friction | 0.064000003 | 1.7066666e-5 | 1.2 / 1.2 | 0/16; 0/8 |
| heavy_cube | 0.512000024 | 1.3653333e-4 | 0.3 / 0.3 | 0/16; 0/8 |
| misaligned | 0.064000003 | 1.7066666e-5 | 0.3 / 0.3 | 16/16; 8/8 |
| control_mu03 | 0.064000003 | 1.7066666e-5 | 0.3 / 0.3 | 0/16; 0/8 |
| control_mu05 | 0.064000003 | 1.7066666e-5 | 0.5 / 0.5 | 0/16; 0/8 |

Mass and inertia scale together by eight, with center of mass and axes unchanged.
Nominal material is 0.3: native and control_mu03 are deliberately physically
identical negative controls, not independent different mechanisms. The mild
surface pair is physically distinct. Alignment is a +0.07 m programmed pusher
waypoint error, enacted through robot actions, with no object teleportation or
sensor corruption. Earlier contacts can occur before contact is lost; this is
not a wholly contact-free fabricated rollout. That alignment error is observable
from actions/TCP/object tracking is a limitation, not information to conceal.

Qualification paired change in final initial-execution goal distance versus native
(metres, mean [95% seed-cluster bootstrap CI]):

| Condition | Effect on goal distance | Mean initial x displacement |
|---|---|---|
| high_friction | 0.004700 [0.001846, 0.007223] | 0.185672 [0.158035, 0.214627] |
| heavy_cube | 0.000642 [-0.000342, 0.001809] | 0.190073 [0.163572, 0.216346] |
| misaligned | 0.168562 [0.153663, 0.183569] | -0.000001 [-0.000001, -0.000001] |
| control_mu05 | 0.002087 [0.000688, 0.003459] | 0.188441 [0.161064, 0.216035] |

The high-friction response is measurably different but still successful. The
payload goal-distance effect is small/uncertain and does not cause the registered
failure. Misalignment leaves about 0.20 m goal error with no final-window progress.
Contact histories and full per-condition readback are in the audit registry and
physical-parameter artifact. These are manipulation-policy executions; the D4
external-force material checks were not reused as recovery evidence.

### Executed recovery matrix

Every action starts from a new reset, the same seed, physical edits and exact full
prefix. Each recovery executes 50 steps with the same observations and horizon.
Cells below are **final successes / 8; normalized utility mean [95% CI]** on all
qualification setups. Rows with zero initial failures are successful-task controls,
not evidence of successful failure recovery. Failure-conditioned rows and the
16-seed development matrix are separately available in `evaluation/report.json`.

| Condition | continue | recontact | slow |
|---|---|---|---|
| native | 8/8; 0.937989 [0.931430, 0.947812] | 8/8; 0.935625 [0.933100, 0.939361] | 8/8; 0.949147 [0.947053, 0.952275] |
| high_friction | 8/8; 0.937975 [0.931412, 0.947768] | 8/8; 0.935449 [0.932884, 0.939267] | 8/8; 0.949145 [0.947053, 0.952234] |
| heavy_cube | 8/8; 0.937913 [0.931328, 0.947731] | 8/8; 0.935606 [0.933077, 0.939324] | 8/8; 0.949070 [0.946906, 0.952196] |
| misaligned | 0/8; 0.020747 [0.012417, 0.033225] | 5/8; 0.583531 [0.243423, 0.811806] | 0/8; 0.036548 [0.034510, 0.039597] |
| control_mu03 | 8/8; 0.937989 [0.931430, 0.947812] | 8/8; 0.935625 [0.933100, 0.939361] | 8/8; 0.949147 [0.947053, 0.952275] |
| control_mu05 | 8/8; 0.937982 [0.931428, 0.947794] | 8/8; 0.935522 [0.932976, 0.939316] | 8/8; 0.949132 [0.947035, 0.952254] |

Success-rate uncertainty: Wilson 95% intervals are [0.676,1.000] for 8/8,
[0.000,0.324] for 0/8, and [0.306,0.863] for 5/8. Bootstrap intervals are clustered
by base seed (2,000 draws, fixed analysis seed 7321). They are screening estimates.
Recontact improves alignment success by 0.625 [0.250,0.875] versus continue and
utility by 0.562783 [0.210197,0.799382]. Three held-out alignment cases still fail
under recontact; all eight fail under continue/slow. The first development case
also failed recontact and remains in the data. No failed cases were removed.

For high friction, recontact-minus-continue utility is -0.002527
[-0.008490,0.001486], far short of a meaningful opposite preference. This is an
**unconditional descriptive contrast**, not a valid matched-failure reversal test.
The mild-surface pair admits all three common successful actions, with `slow`
having the highest mean utility in both because of lower effort. The same controller
succeeds for distinct physical conditions. A same-recovery example spanning two
actual failed causes is N/A because only alignment caused failures. Cause
identification alone is not recovery
relevance. `descriptive_contrasts.json` preserves all paired unconditional effects.

### Passive diagnosis, overlap and held-out separation

The classifier sees all original state_dict channels and all predecision history,
plus cube velocity, drive targets, applied generalized force, incoming link joint
spatial forces, robot–cube contact flag, time and issued actions. No fault value,
condition ID, base seed, scene/contact body name, success label, recovery action or
future outcome enters a feature. A strict nested observation schema rejects such
extras and future frames. Recoveries also receive only the robot observation
contract. Source-level and behavioral leakage tests passed.

L2 logistic and RBF-kernel logistic models use training-only scaling. Fourfold
cross-validation groups by development base seed; all paired fault rows stay in
one fold. Fit on 16 development groups (32 histories per family), then evaluate
on 8 entirely separate base seeds (16 histories per family). No physical-parameter
OOD claim: each split uses the same preregistered values. Full predictions, exact
splits, candidate CV scores and model hashes are published; large fitted arrays
are local and reproducible. Qualification data never select hyperparameters.

| Family / passive model | AUROC [95% CI] | Balanced accuracy [95% CI] | Brier | Log loss | 5-bin ECE |
|---|---|---|---:|---:|---:|
| surface_vs_alignment / logistic | 1.0000 [1.0000,1.0000] | 1.0000 [1.0000,1.0000] | 0.0171 | 0.1053 | 0.0952 |
| surface_vs_alignment / rbf_kernel_logistic | 1.0000 [1.0000,1.0000] | 1.0000 [1.0000,1.0000] | 0.1286 | 0.4361 | 0.2317 |
| surface_vs_payload / logistic | 1.0000 [1.0000,1.0000] | 1.0000 [1.0000,1.0000] | 0.0206 | 0.0882 | 0.0745 |
| surface_vs_payload / rbf_kernel_logistic | 1.0000 [1.0000,1.0000] | 0.8750 [0.6875,1.0000] | 0.2083 | 0.6092 | 0.0075 |
| mild_surface_control / logistic | 1.0000 [1.0000,1.0000] | 1.0000 [1.0000,1.0000] | 0.0103 | 0.0583 | 0.0516 |
| mild_surface_control / rbf_kernel_logistic | 0.9844 [0.9375,1.0000] | 0.8750 [0.6875,1.0000] | 0.2250 | 0.6431 | 0.0046 |

These are **full-setup** diagnostics. Failure-specific classifier metrics are N/A:
there are zero matched failed development or qualification seed pairs in either
primary family. High classification accuracy on successful/failed mixtures is not
reported as proof about a nonexistent matched-failure population. Bootstrap
AUROC/accuracy intervals can degenerate at perfect observed ranking; eight
held-out groups do not establish population-perfect diagnosis. Calibration
intervals for Brier/log loss/ECE are in the machine report. A small ECE from
near-0.5 predictions is not evidence of useful individual confidence.

The preregistered physical/history overlap assessment is:

| Pair | Within-class development nearest-history RMS p95 | Matched qualification history RMS range | Neighborhood-overlap pairs / 8 | Both-model uncertain pairs / 8 |
|---|---:|---|---:|---:|
| surface_vs_alignment | 1.0055 | 0.6654–1.5707 | 6/8 | 0/8 |
| surface_vs_payload | 0.9990 | 0.3081–0.6149 | 8/8 | 0/8 |
| mild_surface_control | 1.0077 | 0.2419–0.4736 | 8/8 | 0/8 |

Friction/payload terminal cube positions differ by only approximately 0.00069–0.00977 m,
yet full passive histories separate them. Neighborhood distance overlap does not
establish observational non-identifiability. No matched failed seed passes the
registered ambiguity subgroup rule; its fraction is N/A rather than inventing a
zero-population denominator. Named simulator contacts are kept only for parity;
the passive baseline was not weakened by withholding available force/state data.

### Gate decision by family

| Family | Matched failed qualification pairs | Meaningful preference reversal | Decision |
|---|---:|---|---|
| surface_vs_alignment | 0 | N/A; not supported | NO-GO: friction never induces the registered failure; alignment also strongly distinguishable |
| surface_vs_payload | 0 | N/A; not supported | NO-GO: neither physical condition induces the registered failure |
| mild_surface_control | 0 | Not a candidate GO test | Negative control behaves as intended: common successful actions, despite passive separability |

The formal primary continue-minus-recontact contrast, simultaneous 98.75%
intervals, failure-state optimum-disagreement fraction and wrong-recovery regret
are N/A because the required matched failed population does not exist. No optimum
was assigned from the fault label. No 10-point reversal claim can be made from
opposite signs of tiny effort costs. The preregistered 25% mechanism-failure,
minimum four matched failed test seeds, passive subgroup and reversal conditions
are not met. Overall D7 recommendation is **NO-GO for these candidates and for
progression to D8–D10**. This is not a general falsification of H1.

### Replay, contacts, tests and resources

All 432 new-environment prefix branches pass, each comparing reset plus 78 actual
steps against its reference. Ten designated independent development base seeds
cover all six conditions and three actions (180 designated branches). These ten
seeds mechanically validate the entire physical-edit/action schedule, but are not
misrepresented as ten ambiguous failure pairs. Across all branches:

- position, generalized velocity, qpos, original observation and time maxima: 0;
- angular maximum: 6.664001874625056e-8 rad (normalization/acos rounding);
- expanded sensor-history maximum error: 0; contacts/outcomes agree exactly;
- physical edits/readback consistent; no ManiSkill snapshot restore or hidden-cache
  restoration claim; no prefix parity failure or stopped scientific worker.

Twenty tests pass, including real CPU mass/inertia/material isolation, complete
history/future/oracle masking, grouped partitions, utility/action budgets, nonlinear
baseline behavior, initial contacts from the existing suite and bounded-worker
termination/final manifest. Ruff lint and formatting checks pass. The scientific
cohort contains 66,528 actual D5–D7 controller steps, including independent prefix
executions; frames/branches are not independent statistical samples.

Environment: Python 3.12.12, ManiSkill 3.0.1, SAPIEN 3.0.3, MuJoCo 3.3.7,
robosuite 1.5.2, PyTorch 2.5.1+cpu, NumPy 1.26.4, SciPy 1.17.1. Full versions,
A4000 driver 550.163.01, source and bundled-asset hashes are retained in preflight.
No dependency, driver, vendor-code or uv.lock changes were made. Two numerical
threads, CPU physics only, no GPU training/physics and no surviving worker/service.

Before final audit the completed instrumented workers used approximately
17.820 worker wall minutes and 0.302673 CPU core-hours. 
The final exact totals including audit are in `completion_manifest.json`; both
are far below the 180-minute / 6-core-hour ceilings. Wall accounting sums worker
durations; it does not claim that interactive editing or Git administration was
CPU-profiled. Every scientific worker has a process-group timeout, retained exit
status, UTC start/end, sources and CPU/wall metadata. No worker was detached
without a termination bound. All original D4 and cloud artifacts are hash-checked.

### Deviations, negative cases and reviewer vulnerabilities

No scientific preregistration values or gate criteria changed. The following
engineering facts and limitations remain visible rather than being converted to
positive evidence:

1. Two initial lint failures were fixed; their logs remain. A new nested-worker
   regression caught an inherited RLIMIT_CPU hard-limit error; the executor now
   respects the smaller inherited limit. The failed test and passing regression
   remain. These are not discarded failed scientific trials.
2. Early command metadata read the Git SHA at completion. Start-time per-file
   hashes and scenario source hashes remain authoritative for those workers; the
   executor now records the start-time commit. Later packaging changes do not
   alter physics, controllers, faults, split, utility, models or thresholds.
3. The alignment mechanism is a visible waypoint error rather than a hidden
   physical parameter. This directly blocks an H1 GO for that pair. Every
   legitimate action/state reading was retained; no sensor was hidden to force
   ambiguity.
4. Physically plausible friction/payload magnitudes did not defeat this Panda
   controller. No values were increased after looking at performance. A different
   failure regime would require separate supervised preregistration, not a silent
   retry or a task switch.
5. Recontact has only 22 pushing steps after fixed repositioning and does not
   recover every alignment case. The fixed success/effort utility gives failed
   low-effort actions a small positive baseline and does not credit partial
   geometric progress. Those action/utility limitations preclude a broad claim
   about all possible recoveries; they were not retuned after outcomes.
6. The eight held-out nuisance groups give wide success intervals; only two
   lightweight diagnostic families and fixed parameter values were screened.
   Perfect simulated-state classification is neither real-sensor validation nor
   a proof of identifiability. There is no OOD/second-task/scientific confirmation.
7. Counterfactual branching compares exposed physics/robot state, parameters,
   histories and contacts under the full prefix. Opaque solver caches are not
   serialized or claimed inspected. This is the approved reconstruction mode,
   not a general simulator snapshot guarantee.
8. Coarse history-neighborhood overlap coexists with strong passive separation.
   Calling that distance overlap "ambiguous failure" would manufacture the claim.
   Likewise, diagnostic separation of the mild-surface control is not recovery
   choice value when the same controllers succeed for both.

These vulnerabilities and absent matched failures block GO. They are not evidence
for a new method, information/physical-effect decomposition or publication claim.

### Evidence and independent review

All paths below are relative to the run directory:

- `initial.json`: preserved prior SHA-256 hashes and verified D4 base.
- `commands.jsonl`, corresponding logs: exact invocations, failures/fixes and resource accounting.
- `development-*/` and `qualification-*/outcomes.jsonl`, `branch_checks.jsonl`, `config.json`, `status.json`: complete setup/action outcomes and fresh-branch checks.
- `fitted/fit_plan.json`: development-only split/hyperparameter seal and local model hash.
- `evaluation/report.json`, `predictions.jsonl`, `descriptive_contrasts.json`: matrices, intervals, all held-out predictions and explicitly descriptive effects.
- `audit/scenario_registry.jsonl`, `physical_parameters.json`, `development_cv.json`, `examples.jsonl.gz`, `replay_and_integrity.json`: compact recipes, readback, CV evidence, predetermined complete examples and parity audit.
- `preflight/hardware.json`, `environment.json`, `integrity-final.json`: hardware, complete versions, final source/assets.
- `completion_manifest.json`: final SHA-256 inventory including local compressed trajectories/models and exact resource totals. `audit/evidence_sha256.json` is the data inventory before command-ledger finalization.

Large local `scenarios.jsonl.gz`, `recoveries.jsonl.gz` and `models.json.gz` are
intentionally not committed. They are preserved locally and listed with hashes;
compact complete recipes and small balanced examples are published. Use the
sequential, bounded reproduction sequence in `RESEARCH_PROTOCOL.md` to regenerate
them on the qualified machine in under the authorized limits. The same scientific
configuration is mandatory; gzip headers may differ while numerical fingerprints
and replay checks provide the substantive audit. Source/HEAD and exact GitHub
URLs are provided in the final pushed-branch handoff.

**STOPPED_AT_D7 = true. No self-authorization for D8–D10.**

## 2026-11-11 overnight authorization: D7B PickCube qualification

The separately supplied `DUAL_REC_OVERNIGHT_CODEX_PROMPT.md` authorizes this
bounded session after the preceding D7 stop. Earlier outcomes and artifacts are
preserved. Run: `results/overnight-20261111/20261110T235337Z`, base
`66b464e64561ee18757b63e69e03b1b5b0abe5ab`, research branch
`dual-rec/overnight-20261111`. Preregistration was committed at `68798cd`;
incidence-selected severities at `5aeab8d`; development-only model seal at
`00ec371`, before qualification. The sensor availability clarification v1.1 at
`ec41846` preceded fitting and qualification. No reserved outcomes were used to
choose severities, sensor degradation, controllers or hyperparameters.

**D7B = NO-GO; automatic route = B_COUNTERFACTUAL_REPLAY_AUDIT. A was not run.**
Both perturbations produced genuine event-triggered failures, but the friction
contrast was an effort-only advantage far below the preregistered 0.10 utility
margin. The declared realistic passive regime also had zero qualifying uncertain
paired seeds. There is no qualified pair of mechanisms requiring meaningfully
opposite recoveries under these fixed candidates. Information-versus-physical
probe effects are **N/A**, because the intervention prerequisite did not pass.

### Calibration and physical scope

Four calibration seeds (3100–3103) are included in the twelve development seeds
(3100–3111); qualification uses eight independent untouched seeds (4100–4107).
All finite-grid levels were executed: nominal 4/4 initial successes; friction
coefficients .10/.03/.01 produced 0/0/2 event failures out of four; grasp target
x-offsets .01/.02/.03 m produced 0/2/2 event failures out of four. The least severe
incidence-eligible choices were therefore .01 friction and .02 m offset, frozen
without consulting recovery rankings. A .02 m offset is half the .04 m cube width.
Offset affects executed grasp commands, not object placement or success labels.

The friction edit changes the cube and both finger collision materials together;
it also changes cube/table contact. Nominal cube friction is .3, finger friction
2.0. This is a severe slick-contact stress test, not an isolated gripper-friction
or real-hardware calibration. All mass, principal inertia and center-of-mass/axis
readbacks are retained. The pinned binding did not expose a friction-combination
getter. PhysX documents an average default, but the effective mode in the pinned
wheel was not independently verified; changing both surfaces avoids relying on
a one-sided material edit. See `preflight/contact_apis.json` and
`preflight/official_sources.json`.

Qualification initial outcomes retain all setups, including ordinary nonsuccess:

| Condition | Initial success / 8 | Triggered failure / 8 | Nonsuccess without trigger / 8 |
|---|---:|---:|---:|
| Nominal | 8 | 0 | 0 |
| Friction .01 | 1 | 7 | 0 |
| Grasp offset .02 m | 1 | 6 | 1 |

The trigger uses only past observations: a missed lift after step 70 sustained for
three frames, or a previously observed lift followed by loss/drop; current task
success suppresses triggering. The nontriggered offset nonsuccess is retained
and excluded only from the explicitly defined triggered-failure estimand. No
future recovery outcome determines membership. Comparisons of two fault classes
condition on failure and are descriptive for these triggered states, not causal
effects of changing fault class in a common state population.

### Executed recovery and passive evidence

All 60 selected development/qualification setups received all three 70-step
continuations, including initially successful controls: **180/180 fresh-prefix
reconstructions passed numerical, sensor-history and contact parity**. ManiSkill
snapshots were never used for D7B. TimeLimit was fixed at 200 before collection,
covering the full maximum 90+70 steps. Qualified recovery evidence is:

| Triggered qualification population | Nominal success | Regrasp success | Conservative success |
|---|---:|---:|---:|
| Friction, n=7 base seeds | 0/7 | 0/7 | 0/7 |
| Offset, n=6 base seeds | 0/6 | 5/6 | 0/6 |

Wilson 95% intervals are [0,.3543] for 0/7, [0,.3903] for 0/6 and
[.4365,.9699] for 5/6. Initially successful nominal controls are not counted as
recovered failures. The six matched failed seed pairs are
4101, 4102, 4104, 4105, 4106, 4107. Primary nominal-minus-regrasp utility:

| Mechanism | Paired mean | Seed bootstrap 95% CI | Absolute mean >= .10 |
|---|---:|---:|---|
| Friction | +.0173315019 | [.0134126479, .0236643056] | No |
| Offset | −.7425448914 | [−.8948553178, −.4395570910] | Yes |

Intervals use 2,000 resamples of six independent base seeds, RNG 11817. All
three recovery actions fail the triggered friction states; nominal's tiny
advantage is lower action effort, not successful friction recovery. Fixed utility
is `(success - .05*mean_normalized_effort - .05 + .10)/1.10`; all actions consume
the same 70-step budget. Complete success/utility matrices and uncertainty are in
`d7b/evaluation/report.json`, with all outcome rows and action tapes retained.

The passive models train only on twelve development seed groups with grouped CV,
then evaluate sixteen fault setups from eight qualification seed groups. The full
regime includes ideal simulated state/action/wrench history; the realistic regime
uses rounded encoders and drive signals, a controller-model effort estimate and
a 5 mm, 10 Hz, one-step-delayed position camera. It is a sensor hypothesis, not a
validated hardware model. No fault parameter, seed, contact-ID label or future
recovery outcome enters deployed features.

| Passive regime/model | AUROC [seed-clustered 95% CI] | Balanced accuracy [95% CI] | Brier | Log loss | ECE, 5 bins |
|---|---|---|---:|---:|---:|
| Full / linear logistic | 1.0000 [1,1] | .9375 [.8125,1] | .0438161 | .1174862 | .0523770 |
| Full / RBF logistic | .890625 [.640625,1] | .8125 [.625,.9375] | .1949109 | .5800918 | .0876613 |
| Realistic / linear logistic | 1.0000 [1,1] | .9375 [.8125,1] | .0359754 | .1472288 | .1198676 |
| Realistic / RBF logistic | .609375 [.3125,.859375] | .625 [.375,.875] | .2386194 | .6702156 | .0651945 |

The linear baseline ranks the causes perfectly but does not classify every setup
correctly at threshold .5. The weaker realistic nonlinear baseline is not evidence
of unavoidable ambiguity when the competent linear baseline separates the labels.
Zero of six matched failed seeds has both fault setups in [.25,.75] for both
realistic models, failing the declared uncertainty requirement. Complete
predictions, calibration intervals, matched-failure metrics, CV scores and model
hashes remain available; none is hidden by reporting only the strongest model.
