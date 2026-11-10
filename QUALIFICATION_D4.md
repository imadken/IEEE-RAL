# DUAL-REC day-4 qualification — 10 November 2026

**Decision: NO-GO for subsequent scientific experiments on this machine.**
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
