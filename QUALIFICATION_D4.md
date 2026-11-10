# DUAL-REC day-4 qualification — 10 November 2026

**Local update: GO for day-4 review of CPU prefix reconstruction; NO-GO for
ManiSkill snapshot reconstruction or automatic research launch.** See the local
qualification addendum below. No research experiments are authorized or started.

**Original cloud decision (historical): NO-GO for subsequent scientific experiments.**
MuJoCo/robosuite replay passed. Both required ManiSkill tasks are blocked before
reset completes by unavailable rendering-device initialization. This is an
engineering/access limitation, not evidence for or against the research hypotheses.
Only the bounded section-15 handoff was undertaken; no method, training, paper,
large experiment or NeuroSym Agent changes were made.

## Frozen environment and reproducibility

Existing empty checkout: `/workspace/IEEE-RAL`; isolated branch `dual-rec/day4`.
Python 3.12.14, ManiSkill 3.0.1, SAPIEN 3.0.3 (bundled PhysX), robosuite 1.5.2,
MuJoCo 3.3.7, PyTorch 2.5.1+cpu, NumPy 1.26.4. `uv.lock` pins transitive artifacts
and hashes. `results/integrity.json` fingerprints source and bundled simulator
libraries and robot/model assets. No external model or controller assets were
downloaded. PhysX's separate upstream SDK revision is not exposed by the installed
Python API and is **not independently verified**; the exact SAPIEN wheel and its
binary hashes identify this build. No NVIDIA driver/GPU or `/dev/dri` was visible.

Install (tested twice, second time with frozen lock):

```sh
cd /workspace/IEEE-RAL
bash scripts/install.sh
source scripts/env.sh
uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
```

The initial dependency build selected an unavailable `clang`. `CC=gcc` fixed
`evdev` compilation without changing its source or bypassing verification.
Writable cache paths avoid read-only home directories. All TLS/artifact checks
remained enabled. No services or credentials are needed for the tested workflow.
PyPI, files.pythonhosted.org, download.pytorch.org and raw.githubusercontent.com
were sufficient for packages and official source inspection.

## Required task checks

| Check | Result | Evidence |
|---|---|---|
| robosuite Lift / Panda / BASIC OSC_POSE | PASS: 20 independent seeded resets; 20 successful reference grasps; 40 paired continuation rollouts | `results/Lift.metrics.json`, `results/Lift.raw.json` |
| ManiSkill PushCube-v1 / Panda / CPU | BLOCKED at cube RenderMaterial construction; zero replay states | `results/PushCube-v1.metrics.json` |
| ManiSkill PickCube-v1 / Panda / CPU | BLOCKED at cube RenderMaterial construction; zero replay states | `results/PickCube-v1.metrics.json` |
| Renderer-free SAPIEN physical-property sanity check | PASS: baseline, doubled mass, increased friction | `results/physical_properties.json` |
| Original metric and MuJoCo contact-state tests | PASS: 3 tests | `tests/test_replay.py` |
| Lint / formatting | PASS | commands above |
| GPU PhysX | UNRUN: CPU task gate not met; GPU not available | no GPU claims |

Commands (run separately so each nonzero exit remains visible):

```sh
uv run python scripts/qualify.py --task Lift --states 20
uv run python scripts/qualify.py --task PushCube-v1
uv run python scripts/qualify.py --task PickCube-v1
uv run python scripts/physics_properties.py --output results/local-properties/physical_properties.json
```

The original two ManiSkill commands returned nonzero at startup. A subsequent
cloud handoff now provides a full CPU contact runner in `scripts/mani_runner.py`,
including snapshot comparison and prefix fallback. Its physical behavior remains
**unvalidated** because startup is still blocked. Do not treat source inspection
or its action/recorder unit tests as day-4 success. Run one-state smoke checks
and then the 20-state checks on compatible local hardware.

## Replay protocol and measured limits

Lift uses seeded physical placement and robot initialization, scripted Cartesian
approach (20 steps), descent (25), gripper closure (15), and initial lift (5).
The snapshot is taken during lifting. A 25-step continuation is recorded, the
snapshot restored, and exactly the same action sequence repeated. Both entire
prefixes and continuations, observations, full generalized state, RNG states,
controller data, object pose, simulator time and contact geom pairs are retained.
Task location is privileged engineering input to this scripted controller; these
traces are **not** evidence of a deployable perception or recovery policy.

Predeclared tolerances: position 1e-5 m, orientation 1e-4 rad, generalized velocity
1e-4 (m/s or rad/s), observation max-component error 1e-4; exact success and contact
pair agreement. All 500 paired continuation steps passed. Position, qpos,
velocity and observation maxima were zero. Angular maximum was 4.2147e-8 rad
from quaternion normalization/acos rounding. Outcome and contact-pair agreement
were both 100%. Histograms, medians and 95th percentiles are in JSON; 500 paired
steps are repeated measures of **20 independent states**, not 500 independent samples.
All reference rollouts lifted the cube; this is actual grasp/contact coverage,
not merely stationary free-space replay. No failure-state or fault-ambiguity claim
is made. Contact summaries are pair identities, not force/impulse agreement.

### Snapshot omissions and scope

- ManiSkill's `get_state_dict()` returns registered nonstatic actor and
  articulation state plus nonempty controller state. Static state, physical
  materials/mass, task variables outside that registry, RNG streams, elapsed
  steps, and hidden PhysX contact/solver caches are not generally included.
  In 3.0.1, `set_state_dict()` restores scene state but does **not** call the
  controller setter. The adapter adds explicit controller, RNG and elapsed-step
  handling. There is no validated claim of restoring hidden contact caches.
- No claim can be made about whether prefix replay is required for **PhysX**:
  both tasks failed before meaningful contact execution. Source inspection is
  not a substitute for the numerical qualification.
- robosuite's basic `sim.get_state()` includes only time, qpos and qvel. Our Lift
  adapter uses `mjSTATE_INTEGRATION`, including control/applied forces, activation,
  user/plugin state and solver warmstart. `mj_forward` rebuilds derived contacts;
  integration fields are reapplied afterward. Explicit numeric controller,
  gripper, observable and robot/environment fields, RNG state and task timing
  supplement it. Fixed model/material properties are supplied by locked assets.
- Arbitrary Python object references, robot rolling-buffer objects, unrelated
  custom task internals, renderer state and interpolators are not serialized.
  The adapter rejects interpolated controllers and is qualified only for this
  exact Lift/Panda configuration. It is not a general full-simulator serializer.
  Prefix fallback is implemented on divergence but was not needed or exercised.
  Cross-process restart from stored JSON is not validated; observations and
  source/model fingerprints permit independent reruns from seeds and actions.

## Physical-property demonstration

Official ManiSkill domain-randomization documentation specifies rigid-body mass
and per-collision-shape physical-material friction changes. The separate CPU-only
SAPIEN scene exercises those exact APIs without visual construction: 4 cm cube,
0.064 kg nominal mass, friction 0.2; second condition doubles mass to 0.128 kg;
third raises friction to 0.8. Under the same 0.3 N horizontal force for 0.5 s,
measured x displacements were approximately 0.3435 m, 0.04782 m and -2.09e-6 m.
Parameter metadata resides in an evaluation-only dictionary, separate from
physical observations. These are engineering responses in a small scene, not
qualified fault pairs or results on PushCube/PickCube.

## Throughput, budget and next gate

The full 20-state Lift run took 38.51 wall seconds including setup/imports,
for 2,300 controller steps (1,800 unique-trajectory steps plus 500 replays).
This is about 59.7 end-to-end controller steps/s or 1.93 s per paired state.
Use this only for this configuration; it does not predict PhysX throughput.
Two BLAS/OpenMP threads, a 20-minute runner wall cap, 20-state CLI ceiling and
no GPU jobs constrain this qualification, well below the proposal's campaign
ceiling of 80 CPU core-hours / 12 GPU wall-hours. Actual process CPU core-hours
were not instrumented; no measured core-hour claim is made.

**Required next action:** supply an environment with a SAPIEN-compatible rendering
device, even for these CPU physics tasks. Re-run both startup gates without
patching simulator task code or faking RenderMaterial; then validate the prepared
scripted-contact replay runner and qualify 20 independent states per task. If
snapshot replay diverges, test deterministic reset plus full action-prefix replay
and matched RNG scheduling. Stop if that also fails. Day-4 review is still required
before any causal method or high-volume experiment. Novelty and publication
outcomes remain entirely untested.

## Official sources inspected

- ManiSkill release source: https://github.com/mani-skill/ManiSkill/tree/v3.0.1
  (`sapien_env.py`, `scene.py`, `base_agent.py`, PushCube and PickCube).
- Official mass/friction instructions:
  https://github.com/mani-skill/ManiSkill/blob/v3.0.1/docs/source/user_guide/tutorials/domain_randomization.md
- robosuite 1.5.2 source and local wheel `utils/binding_utils.py`, controller and
  environment implementations: https://github.com/ARISE-Initiative/robosuite/tree/v1.5.2
- Official publisher metadata and artifact hashes were obtained from PyPI for
  ManiSkill, SAPIEN, robosuite and MuJoCo. MuJoCo 3.3.7 was chosen as a pinned 3.x
  release satisfying robosuite's >=3.3.0 requirement, rather than assuming the
  current MuJoCo 4.x release has matching API behavior.

Use `git rev-parse HEAD` for this handoff's source commit. The branch is now pushed to GitHub as `dual-rec/day4`. Cloud environment
publication/restoration remains unverified; local Git transfer was validated separately.

Reusable configuration: saving install_script and start_skill was attempted, but
the onboarding backend returned INVALID_ARGUMENT and could not confirm persistence.
The tested instructions remain in scripts/install.sh, scripts/env.sh and this
report. This is separate from the rendering-device blocker; nothing was published.

## Cloud handoff extension — Ubuntu / RTX A4000

See `LOCAL_CODEX_HANDOFF.md` for the local Codex request and exact commands.
Installation and environment activation now resolve the actual checkout path;
no `/workspace` path is required. New qualification outputs default to unique
`results/local-*` directories, and existing metric/raw paths are rejected rather
than overwritten. Source/asset manifests and the physical-property demonstration
now require an explicit output path. Original evidence under `results/` is kept.

Shared comparisons now reject nonfinite values, schema and shape mismatches,
check simulation time, and distinguish one-state smoke from a 20-state run.
The ManiSkill adapter additionally records known controller transient fields,
drive position/velocity targets, and time-limit wrapper counters. The new runner
requires actual robot-object contact and at least one successful manipulation;
a repeatable all-failed trajectory is not enough. The Lift runner now checks
grasp contacts as well. CPU task mode and the original tolerances remain fixed.

Seven regression tests cover the numerical checks, actual MuJoCo contact replay,
fail-closed observations/outcomes, scripted action bounds/gripper convention,
and robot-cube versus cube-table contact detection. The latter uses a small API
fixture; it does not validate real ManiSkill contact dynamics.

New evidence lives in `results/cloud-handoff/` and `results/cloud-contact/`.
Both task startup errors were reproduced with the prepared ManiSkill runner.
A strengthened 20-state Lift rerun passed before adding explicit grasp coverage;
`results/cloud-contact/Lift.metrics.json` records the final grasp-coverage run.
No causal/model training or later-stage research was performed. Local success
still depends on actual NVIDIA/Vulkan task construction and contact replay.

### Transfer verification

A complete Git bundle was verified and cloned into a different directory with
no virtual environment. Frozen installation from the shared artifact cache,
all seven tests, lint and a one-state Lift grasp/replay smoke passed there.
`results/transfer-check/Lift.metrics.json` records that smoke (not a 20-state
qualification). This verifies checkout-path portability and isolated Python
installation on this cloud host; it does not prove Ubuntu/A4000 driver support.
The final grasp-aware full cloud rerun passed 20/20 independent states, with
20/20 successful reference grasps and 100% outcome/contact-pair agreement.
The repository branch was pushed without force and its remote SHA checked.

## Local qualification addendum — Ubuntu / RTX A4000, 10 November 2026

**Decision: the bounded engineering gate passes using deterministic reset plus
full-prefix reconstruction for ManiSkill, and snapshot replay for Lift. Stop for
day-4 review. ManiSkill snapshot replay fails and must not be used. Research
experiments remain NO-GO pending review and separate authorization.**

Evidence: [`results/local-20261110-d4/summary.json`](results/local-20261110-d4/summary.json),
per-task metric/raw files, and [`commands.jsonl`](results/local-20261110-d4/commands.jsonl).
The original 20 cloud evidence files and `uv.lock` have unchanged SHA-256 hashes;
`initial.json` retains those hashes. No original results were overwritten.

### Platform and scoped engineering fixes

Ubuntu 22.04.5, kernel 6.8.0-138-generic, NVIDIA RTX A4000 and driver 550.163.01;
Python 3.12.12 locally (the lock permits Python 3.12), with the same pinned
simulators, NumPy and CPU PyTorch as the cloud. Frozen installation passed with
TLS/hash verification enabled. No dependencies, drivers or third-party source
were changed. `vulkaninfo` was unavailable and was not installed. Actual
construction and stepping of both tasks passed with `sim_backend=cpu` and
`render_backend=none`; the A4000 provides the device support needed by visual
material construction, without enabling GPU physics.

The restricted command sandbox hides `/dev/nvidia*` and `/dev/dri`, causing
`nvidia-smi` exit 9; it also blocked package-download DNS. Approved host execution
resolved both access problems. Host preflight and hardware logs record the real
device/driver. These were access restrictions, not a broken driver. Diagnosis
followed the [official ManiSkill installation guidance](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html).

The initial one-state runs exposed an adapter error: `deepcopy(BatchedRNG)` routes
through ManiSkill's forwarded pickle hooks and raises a NumPy shape error. The
adapter now saves each underlying NumPy RandomState and restores its state in
place, retaining RNG aliases. Regression tests use the actual pinned BatchedRNG.
Explicit audits cover controller targets/transients, drive positions/velocities,
Python/NumPy/Torch CPU RNGs and seeds, and environment/wrapper elapsed steps.
`--replay-mode prefix` deliberately recreates the scene, resets the seed, replays
every stored prefix action, then compares the reconstructed state and identical
continuation. It never silently substitutes a passing fallback for a failed
snapshot result. The default remains `snapshot`.

Run metrics now include source commit, source SHA-256 hashes and process CPU
usage. `scripts/env.sh` fixes numerical-library threads at two even if larger
values are inherited. Ten tests, lint and formatting checks passed after the
final code edits. The final nullable-field audit fix was also checked against
the saved complete snapshots; those prefix snapshots have identical schemas and
values. No manipulation controller tuning or tolerance changes were needed.

### Required task results

| Check | Status | Scope / evidence directory |
|---|---|---|
| Real PushCube and PickCube construction | PASS | Initial one-state runs reach snapshot capture; hardware access resolved |
| Initial prepared snapshot adapter | FAIL, fixed | `push-smoke-01`, `pick-smoke-01`: BatchedRNG deepcopy exception |
| PushCube snapshot replay | FAIL | `push-snapshot-audit`: one state, numerical/contact divergence; no full snapshot run |
| PickCube snapshot replay | FAIL | `pick-snapshot-audit`: one state, numerical divergence; no full snapshot run |
| One-state prefix smokes | PASS | `push-prefix-smoke-01`, `pick-prefix-smoke-01` |
| PushCube prefix qualification | PASS: 20 independent seeds, 20 successful references, 20 robot-contact states | `push-prefix20` |
| PickCube prefix qualification | PASS: 20 independent seeds, 20 successful references, 20 robot-contact states | `pick-prefix20` |
| Lift snapshot qualification | PASS: 20 independent seeds, 20 successful references, 20 grasp-contact states | `lift20` |
| Actual task-cube mass/friction checks | PASS for both tasks | `preflight/task-properties-final` |
| Standalone property regression | PASS | `preflight/physical_properties.json` |
| Unit/integration regression tests | PASS: 10 tests | `complete-tests.log` |
| Lint and format check | PASS | `complete-lint.log`, `complete-format.log` |
| GPU physics, training, scientific gates | UNRUN | Outside authorization |
| Cross-process state-file restart / arbitrary task serialization | UNRUN | No claim |

All paths in this addendum are under `results/local-20261110-d4/` unless stated
otherwise. Each invocation has its own directory/log and retained exit status.
Initial failures, both snapshot diagnostic rounds, and all prefix fallback errors
remain available. Neither task ran a full 20-state snapshot test after failing its
smoke; the full tests explicitly selected prefix mode.

### Numerical distributions and snapshot limitation

For the qualified modes, each task has 20 reconstructed branch states and 500
paired continuation steps. PushCube additionally compares all 1,060 prefix steps;
PickCube compares all 1,300 prefix steps. These are repeated measures of 20
independent seeds per task, not thousands of independent samples. Immediate
reconstructed states and all exposed snapshot fields agree for both prefix tasks.
Outcome and contact-event agreement is 100% for all three tasks' continuations.
The contact record includes sorted body-pair entries, including multiplicity;
forces and impulses are not compared.

Position, velocity, qpos, observation and control-time errors have max, median and
p95 of zero in all three qualified continuations. Angular errors (radians) are:

| Task / mode | Median | p95 | Maximum |
|---|---:|---:|---:|
| PushCube / prefix | 0 | 4.2147e-8 | 5.9605e-8 |
| PickCube / prefix | 0 | 4.2147e-8 | 5.9605e-8 |
| Lift / snapshot | 0 | 2.9802e-8 | 4.2147e-8 |

Histograms and immediate/prefix/continuation distributions are in `summary.json`
and task metrics. Small nonzero angular errors arise when normalizing and taking
acos of identical floating-point quaternions. Frozen limits remain 1e-5 m,
1e-4 rad, 1e-4 generalized velocity/observation, 1e-9 s and exact outcome/contact
agreement.

Failed snapshot continuation maxima, seed 0:

| Task | Position (m) | Angle (rad) | Velocity | Observation | qpos |
|---|---:|---:|---:|---:|---:|
| PushCube | 7.9756e-4 | 1.1657e-2 | 4.1528e-1 | 1.3528e-2 | 1.2398e-5 |
| PickCube | 6.2174e-4 | 3.4977e-2 | 1.3453 | 4.7278e-2 | 8.4331e-4 |

All explicitly captured custom fields match immediately after snapshot restore.
Registered articulation state is not bit-identical: for example, PushCube root
position differs by up to 1.49e-8 m. PushCube's immediate contact list also remains
different after restoration; pose/velocity/observation readings alone would have
missed this failure. The exact source of subsequent divergence has not been
isolated. Inaccessible PhysX solver/contact caches and omitted integration state
are plausible contributors, not an established diagnosis. Snapshot replay is
therefore rejected. Both diagnostic prefix fallbacks pass at seed 0; qualification
of that alternative comes from the separate explicit 20-state runs.

Only the two built-in Panda tasks and `pd_ee_delta_pos` at control boundaries are
covered. Registered dynamic/kinematic actors include task goals. Static table and
robot/model configuration, collision materials/mass/inertia, drive gains, task
constants such as goal thresholds, solver internals and arbitrary custom Python
state are not generally serialized. They remain fixed during replay and are
rebuilt by the pinned task/asset code for prefix reconstruction. No inaccessible
solver cache is claimed restored. Time comparison uses elapsed control steps
and fixed control frequency; no independent hidden PhysX clock API was validated.
The protocol is within-process seeded scene reconstruction; cross-process restart
and other controller configurations remain unqualified.

### Actual task-cube property demonstration

Each condition creates and resets the real CPU task at seed 0, assigns a fresh
cube collision material, settles for 0.25 s, then applies the same 0.65 N force
in +x for 0.25 s at the scene physics timestep. The robot remains dynamically
simulated without actions; it is not held fixed. Earlier property artifacts with
"robot stays at reset" in their protocol text are superseded by the final files
with corrected metadata. No controller or task-success claim is derived from
these property checks.

Baseline mass is 0.064000003 kg and cube static/dynamic friction is 0.2. The second
condition doubles mass to 0.128000006 kg; the third sets cube friction to 0.8.
Inertia remains unchanged when mass alone is changed, and is logged explicitly.
The table retains its task-defined material. The measured x displacements are:

| Actual task cube | Baseline (m) | Doubled mass (m) | Increased friction (m) |
|---|---:|---:|---:|
| PushCube | 0.250441 | 0.085376 | 0.154825 |
| PickCube | 0.250275 | 0.085290 | 0.154636 |

Both perturbations reduce displacement, with finite observations and parameter
readback retained. These are single-seed engineering demonstrations in actual
task scenes, not fault-ambiguity or causal experiments. Condition parameters are
stored only in `evaluation_only`; physical observations have no added condition
labels. Direct scene stepping here does not advance Gym elapsed-step counters.

### Measured budget, integrity and review boundary

| Full task command | End-to-end wall (s) | CPU user + system (s) | Controller steps including reconstruction | Steps/wall s |
|---|---:|---:|---:|---:|
| PushCube prefix20 | 62.14 | 62.32 | 3,120 | 50.21 |
| PickCube prefix20 | 74.41 | 74.59 | 3,600 | 48.38 |
| Lift20 | 67.69 | 67.74 | 2,300 | 33.98 |

At evidence summarization, elapsed local work was 14.35 minutes and profiled
commands consumed approximately 0.107 CPU core-hours, including installation,
failed smokes, diagnostics, properties and checks. Command CPU totals cover
instrumented child processes, not every interactive inspection or editor process.
Each full command used a 20-minute timeout with TERM/KILL grace; smoke/property
commands used five minutes. The aggregate 90-minute cap was not approached.
No GPU physics or training jobs ran. GPU rendering-device initialization is not
charged or claimed as a GPU-physics experiment.

`preflight/integrity-final.json` hashes final source, locked simulator binaries and
bundled assets. The source base was `ee12762198644c6f56d03b2532489c2a8f8b5a6f`;
per-run source hashes identify the engineering working tree used at invocation,
including intermediate instrumentation revisions. `executor.py` and `summarize.py`
retain the command accounting and evidence-recalculation procedure. The final
schema-audit hardening does not change simulation or action generation; saved
prefix snapshot equality and continuations were independently recomputed.

**Review required now.** Prefix reconstruction is the sole qualified ManiSkill
mode and requires the entire seed/action history; it does not establish arbitrary
snapshot branching. A reviewer must decide whether this mode meets the next
phase's engineering needs. Physical ambiguity, recovery conflicts, information
versus physical effects, planning baselines, model error and novelty are still
untested. No causal method, paper, training, NeuroSym Agent change or research
campaign was started.
