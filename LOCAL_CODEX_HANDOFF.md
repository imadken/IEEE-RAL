# Local Codex handoff — Ubuntu / NVIDIA RTX A4000

Continue the bounded **DUAL-REC day-4 engineering qualification only**.
The Ubuntu/A4000 continuation has now completed; see the local addendum in
`QUALIFICATION_D4.md` and `results/local-20261110-d4/summary.json`. Both ManiSkill
tasks qualified in explicit prefix mode, while snapshot replay failed. Lift
snapshot replay and actual task-cube property checks passed. Stop for review;
the original sequence below remains the reproduction and authorization boundary.
Read `QUALIFICATION_D4.md` for the original evidence and limitations. No experiment,
causal method, training, paper writing, GPU physics or NeuroSym Agent changes are
authorized by this handoff. No scientific result or publication claim exists.

## What is already done

- Hash-locked Python environment: Python 3.12, ManiSkill 3.0.1, SAPIEN 3.0.3,
  robosuite 1.5.2, MuJoCo 3.3.7, CPU PyTorch 2.5.1.
- Original 20-state Lift/Panda replay passed; strengthened comparisons were rerun
  on all 20 states in cloud. Seven tests cover numerical checks, actual MuJoCo
  contact-state replay, fail-closed observation comparisons and action conventions.
- Renderer-free SAPIEN mass/friction perturbations behaved as expected.
- Both real ManiSkill tasks still fail before reset finishes because this cloud
  machine exposes no rendering device. No ManiSkill contact trajectory was tested.
- `scripts/mani_runner.py` now implements scripted contact qualification and prefix
  fallback using pinned API inspection. It is **prepared, physically unvalidated
  code**. Local Codex must diagnose controller/API errors, not assume it works.
- Snapshot adapter now includes drive targets, known interpolation/target fields,
  controller state, CPU RNGs, simulation clock and Gym time-limit elapsed steps.
  PhysX solver contact caches remain inaccessible. Check numerical replay rather
  than asserting full restoration based on these fields.

## Prepare your checkout

The branch `dual-rec/day4` is available on GitHub; clone it:

```sh
git clone --branch dual-rec/day4 https://github.com/imadken/IEEE-RAL.git
cd IEEE-RAL
```

If GitHub publication is unavailable, download the supplied `dual-rec-day4.bundle`
and clone the bundle instead (it includes commit history; `.venv` is excluded):

```sh
git clone --branch dual-rec/day4 /path/to/dual-rec-day4.bundle IEEE-RAL
cd IEEE-RAL
```

For an existing clone, use `git fetch origin` and switch to the branch while
preserving local work. Never reset or overwrite user changes. Confirm
`git log -1 --oneline` and `git status --short` before editing. The bundle clone's
origin is a local file; use `git remote add github https://github.com/imadken/IEEE-RAL.git`
if a separate GitHub remote is later needed. Do not push to the bundle file.

Install `uv` from its official instructions if absent:
https://docs.astral.sh/uv/getting-started/installation/

## Paste this request into local Codex

> Continue DUAL-REC day-4 qualification in this checkout. Read
> LOCAL_CODEX_HANDOFF.md and QUALIFICATION_D4.md first, inspect git status, then
> execute the local sequence below. This is Ubuntu with an NVIDIA RTX A4000.
> Preserve the uv lock and CPU physics configuration. First verify actual SAPIEN
> task construction; CPU PyTorch lacking CUDA is expected and is not a reason to
> replace dependencies. Diagnose Vulkan/NVIDIA runtime issues using official
> documentation. Do not change drivers blindly, disable TLS verification, fake
> render materials, or patch third-party task code to make the gate pass.
> Run one state per task before the full 20; debug scripted approach/grasp/push
> motion and explicit snapshot coverage as needed. Treat the prepared ManiSkill
> runner as unvalidated. Keep hidden physical conditions in evaluation logs only.
> Preserve all original cloud results; put each run in a new output directory.
> Stop on unexplained divergence, contact-free rollouts, inaccessible critical APIs,
> or the time budget. Record failures and the tested prefix-replay fallback rather
> than relaxing tolerances. Produce numerical distributions and a reasoned go/no-go
> report, then stop for day-4 review. Do not begin later research phases.

## Local execution sequence

Run commands individually and preserve each exit status. No simulator service needs
to stay running. CPU physics comes first; RTX A4000 supplies rendering-device
support for task initialization, **not authorization for GPU physics or training**.

```sh
bash scripts/install.sh
source scripts/env.sh
uv run python scripts/preflight.py --output results/local-preflight/hardware.json
uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
```

`nvidia-smi` should recognize the A4000 and its installed driver. `vulkaninfo
--summary`, if available, should recognize the NVIDIA device. The decisive check is
real task construction, not the presence of an ICD filename or a successful
`nvidia-smi`. The stack needs no external model downloads, credentials or RL training.
If compilation fails, check `gcc` and Python build prerequisites. If SAPIEN cannot
initialize, diagnose the installed NVIDIA/Vulkan libraries and supported driver
before installing or updating system packages. Keep physics on `sim_backend=cpu`.

Smoke runs (exit zero with `smoke_passed` is **not** a 20-state qualification):

```sh
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/qualify.py --task PushCube-v1 --states 1 --output results/local-push-smoke
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/qualify.py --task PickCube-v1 --states 1 --output results/local-pick-smoke
```

If these fail due to API/controller errors, make scoped fixes, add meaningful
regression checks, and retry into a **new** directory. If the scripted task never
succeeds or lacks robot/object contact, do not qualify it based solely on stable
replay. The current scripts deliberately refuse to overwrite prior metrics.

After each task's smoke passes:

```sh
timeout --signal=TERM --kill-after=15s 20m uv run python scripts/qualify.py --task PushCube-v1 --states 20 --output results/local-push20
timeout --signal=TERM --kill-after=15s 20m uv run python scripts/qualify.py --task PickCube-v1 --states 20 --output results/local-pick20
timeout --signal=TERM --kill-after=15s 20m uv run python scripts/qualify.py --task Lift --states 20 --output results/local-lift20
uv run python scripts/physics_properties.py --output results/local-preflight/physical_properties.json
uv run python scripts/manifest.py --output results/local-preflight/integrity.json
```

Controller tuning is allowed for engineering, but never choose tolerances after
looking at divergence. Current frozen limits: 1e-5 m position, 1e-4 rad orientation,
1e-4 generalized velocity/observation, 1e-9 s time, exact outcome/contact agreement.
No-contact or all-failed manipulation is a failed smoke, even if replay matches.
Log robot-object contact explicitly, not merely cube-table contact.

## Remaining engineering checks before a go decision

1. Immediate restored state AND identical continuation agree across 20 independent
   states per ManiSkill task; include contact trajectories and per-state outcomes.
2. Validate drive targets, interpolation counters, RNG and elapsed steps in the
   restored task. Document custom task state or static/model parameters omitted.
3. If snapshots diverge, inspect deterministic reset+full-prefix replay. The
   implementation writes fallback errors but conservatively stops; a passing
   fallback requires a deliberate 20-state qualification and documented mode,
   not changing one status flag. Stop if neither reconstruction mode qualifies.
4. Extend the SAPIEN property demonstration into actual ManiSkill cube actors:
   demonstrate doubled payload and increased friction in CPU scenes without
   observation labels. Do not treat the standalone scene as task validation.
5. Profile measured wall/CPU usage and save versions, driver metadata, asset hashes,
   source commit and command exit statuses. These are qualification runs only.
6. Update the qualification report with passed/failed/skipped/unrun results and
   limitations, commit scoped changes, and stop for day-4 review.

Local cap: at most 20 minutes per full task run, 90 minutes aggregate including
diagnosis, two configured numerical-library threads, no GPU jobs. If critical
replay is unreliable or support unavailable, retain the evidence and issue no-go.
The research campaign ceiling (80 CPU core-hours / 12 GPU wall-hours) is not a
budget to spend during this handoff.

**Outstanding scientific gates remain completely untested:** physical ambiguity,
recovery-choice conflicts, information versus physical-effect separation, robust
planning baselines, model-error experiments and novelty. Passing D4 authorizes
review of the next phase, not a paper claim or automatic campaign launch.

## Reproducing the qualified local alternative

The default `--replay-mode snapshot` intentionally retains the failed ManiSkill
snapshot gate. After examining retained snapshot/fallback evidence, select
`--replay-mode prefix` explicitly for each ManiSkill smoke and full run. Run
commands separately with new output directories, for example:

```sh
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/qualify.py --task PushCube-v1 --states 1 --replay-mode prefix --output results/local-push-prefix-smoke-new
timeout --signal=TERM --kill-after=15s 20m uv run python scripts/qualify.py --task PushCube-v1 --states 20 --replay-mode prefix --output results/local-push-prefix20-new
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/qualify.py --task PickCube-v1 --states 1 --replay-mode prefix --output results/local-pick-prefix-smoke-new
timeout --signal=TERM --kill-after=15s 20m uv run python scripts/qualify.py --task PickCube-v1 --states 20 --replay-mode prefix --output results/local-pick-prefix20-new
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/physics_properties.py --task PushCube-v1 --output results/local-properties-new/PushCube-v1.json
timeout --signal=TERM --kill-after=15s 5m uv run python scripts/physics_properties.py --task PickCube-v1 --output results/local-properties-new/PickCube-v1.json
```

Each full run still depends on its task's passing smoke. Prefix mode rebuilds the
scene and replays the full action history; it does not validate snapshot restore.
`scripts/env.sh` now enforces two numerical-library threads. A restricted tool
sandbox can hide otherwise functional GPU device nodes; test host visibility
before diagnosing a driver failure or changing system packages.

Transfer has been tested: a fresh bundle clone installed the frozen environment,
passed all seven tests and lint, and completed a one-state Lift grasp/replay smoke.
This used the cloud CPU host; the local NVIDIA/Vulkan checks remain outstanding.
