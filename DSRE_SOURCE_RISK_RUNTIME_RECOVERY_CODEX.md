# CODEX EXECUTION CONTRACT
## DSRE: Restore Qualified PickCube Physics and Complete the Frozen Independent Risk Study

**Scientific supervision:** Continue the existing DSRE research. This is a runtime qualification and pre-registered experimental recovery assignment, not a new contribution, a publication-readiness review, or manuscript work.

**Workstation repository:** `/home/imad/Desktop/IEEE-RAL`.

**Reviewed local starting commit:** `9a6ddb40ea7b347744090de2191cc6bda70f9260` on `research/dsre-rss2027-independent-source-calibration`. This commit is reported local and may not exist on the remote. Inspect the actual local state; never reset a user's changes to match this string.

**Working branch:** `research/dsre-runtime-qualification-recovery-20261116` or an isolated worktree from the verified local parent.

**Frozen scientific problem:** Find minimum observable evidence that justifies the selection of a fixed recovery intervention relative to paired physical outcomes, or return a correctly scoped insufficiency witness. The strict solver, invariant-evidence adapter, binary terminal outcome, and clean parent-level statistical risk gate are unchanged.

**Do not work on the RSS or Stage 2 manuscript. Do not discuss submission readiness.** The aim is scientifically qualified data and a verifiable correction of the physical execution blockage.

---

## 1. Facts established by the sealed failure archive

Read `AGENTS.md` and these exact repo records before changing anything:

- `docs/DSRE_V12_SOURCE_RISK_PREREGISTRATION.md`
- `docs/DSRE_V12_INDEPENDENT_CALIBRATION_RESULTS.md`
- `docs/DSRE_V12_OPERATIONAL_EVIDENCE_GATE.md`
- `config/dsre_source_risk.json`
- `results/dsre-operational/20261116T102110Z-source-calibration/completion_manifest.json`
- The old failed-attempt logs under that root, including `metered/inspected_prefix_diagnostic.json`, `metered/import_diagnostic.json`, `study_halt.json`, and `independent_failure_audit.json`.
- The registered source snapshots for `scripts/overnight_pick.py`, `scripts/mani_runner.py`, `scripts/dsre_source_risk.py`, `scripts/dsre_science_physics.py` and DSRE source packages.

**The historical result is immutable:** first old qualification parent 13000000 failed with SIGSEGV/signal 11, before any scene, state, or physical outcome could be saved. A direct independent invocation of `overnight_pick.initial()` also terminated with shell exit 139 after approximately 5.8 seconds; imports alone succeeded. The Python-level fault site was reported in `mani_skill/utils/building/actors/common.py:87`, SAPIEN `RenderMaterial` construction inside `build_cube`. This is where the crash surfaced, NOT a proven root cause.

**Important:** the frozen `mani_runner.make_env` already uses `sim_backend="cpu"`, `render_backend="none"`, `obs_mode="state_dict"` and the original `pd_ee_delta_pos` controller. **Do not suggest toggling to render_backend="none" as though it had not been tried.** ManiSkill 3.0.1 documentation nevertheless identifies broken Vulkan/graphics drivers as one possible class of native crashes; this is a hypothesis to test and not an established explanation. See `https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html` and the corresponding simulator API documentation.

Environment recorded in the failure archive: Python 3.12.12, ManiSkill 3.0.1, SAPIEN 3.0.3, Torch 2.5.1+cpu, NumPy 1.26.4. The execution uses a mixed `PYTHONPATH` that may include a separate REBOOT environment; **inspect the actual import file paths** rather than assuming that package-version strings prove a single consistent environment. Source and packaged binary hashes matched before the failure.

**New study denominators are exactly zero:** calibration 0/256; test 0/128; no source-specific risk status is qualified and no new paired effect is estimable. Do not call these zero errors or negative scientific results. Previously sealed v1.2 results remain useful background but cannot be pooled with the unfinished source-specific experiment.

---

## 2. Engineering objective, and guard against research drift

**Objective P0:** Restore a *physically identical, independently qualified* deterministic execution route for the original PickCube fixed task, or establish the concrete native-runtime blocker and stop trying. A successful Python import or a single scene reset does not constitute physical parity.

**Objective P1 (conditional on P0):** Complete the existing immutable 256-parent calibration and 128-parent test with unchanged seeds, all five offsets, both registered interventions, strict replay qualification, the original 17 methods and the registered risk allocation. Use an entirely new output namespace and an explicit link to the failed old seal. Never change the old seal.

No new physical fault settings, no new seeds, no version-uncontrolled simulator upgrades, no controller or action model changes, no threshold/rule tuning, no novel uncertainty method, no LLM or GPU training, no benchmark migration.

The failure does not authorize Codex to claim the study's hypothesis is true or false. The supervisor decides how any qualified results contribute to the paper.

---

## 3. P0: Bounded, forensic native crash diagnosis

### Phase A: preservation and environmental comparison, maximum 30 minutes

1. Inspect git status, the last successful physical-run commit and environment fingerprint, source tree and immutable manifests. Protect uncommitted user edits, `.gitignore`, `uv.lock`, old data and all prior seals. Create a dedicated branch/worktree without rebasing or force-updating remote branches.
2. Record only diagnostic, nonsecret environment fields: `PATH` entries relevant to Python, actual `sys.path`, `sys.executable`, `PYTHONPATH`, `LD_LIBRARY_PATH`, selected Vulkan variables, `DISPLAY`, `CUDA_VISIBLE_DEVICES`, thread variables, `ulimit` resource bounds, and loaded native module locations. **Never dump all environment variables or tokens into evidence.**
3. Inspect dynamically loaded libraries with available nonprivileged tools (`ldd`, `ldconfig -p`, `vulkaninfo --summary`, `nvidia-smi`, existing `/usr/share/vulkan/icd.d/*.json`, `journalctl` if permitted, and file hashes). Record unavailable tools as unavailable, not a cause.
4. Compare current driver/ICD/library information, host changes, package/ELF hashes and imported paths with the last verified successful run (November 15, 2026). Separate *identical packaged bytes* from *different native runtime/graphics driver*. Do not assume a driver update actually occurred unless documented.

### Phase B: isolate the fault in new subprocesses, maximum 75 minutes

Run each diagnostic in a fresh **foreground, timeout-bounded child process**, holding the established PhysX lock where necessary. Never kill other users' processes. Capture exit code/signal, timestamped stdout/stderr and a Python faulthandler/native stack trace when available; avoid writing multi-GB core dumps.

Run in this order, stopping early if the native root cause is clear:

1. **Pure imports:** confirm known import-only success. Print the file paths of imported `sapien`, `mani_skill`, `numpy`, `torch` and the exact native `.so` used.
2. **Direct SAPIEN material construction:** on this pinned build, reproduce the smallest available `sapien.render.RenderMaterial()` or the documented factory that the failing line actually calls. This must not import DSRE policy code. Do not guess an API: inspect the installed source first. If it segfaults, report that material initialization alone is implicated.
3. **Gym scene initialization:** original `make_env('PickCube-v1')` with `render_backend='none'` and CPU simulation, then original `overnight_pick.initial(13000000, PickFault(...))`. Record whether the fault occurs before or after reset, actuator setup, material creation and scene registration.
4. **Native backtrace if available:** one isolated GDB or equivalent process under a timeout, requesting C/C++ frames at the fault. If GDB is missing or security policy prevents attach, note that and continue; do not install system tooling without permission.
5. **Minimal controlled environment comparison:** compare identical pinned source/binaries under supported, separately recorded *process-local* runtime configurations, e.g. removing duplicate optional `PYTHONPATH` entries only when all essential imports remain from the pinned installed packages, or selecting an existing valid Vulkan ICD if documented by `vulkaninfo`. Test a change in one factor at a time. Avoid speculative, undocumented environment switches.

At most **two repeat trials per unique diagnostic configuration**. No loop until the crash disappears. Stop early when the session's source material becomes inconsistent or further diagnosis would require privileged driver/OS modifications.

**Do not do these things:** reinstall/up/downgrade ManiSkill/SAPIEN/Torch or NVIDIA drivers in the preserved environment; modify `/usr/share/vulkan`, CUDA, Xorg or kernel settings; inject a fake RenderMaterial or bypass cube/material creation; change physics/render semantics just to avoid the crash; replace a failed seed; silently use GPU simulation instead of PhysX CPU.

### Phase C: one minimal repair, clearly versioned

If an evidence-supported configuration-level correction is found (e.g. a verified library-path or installed ICD selection), apply it **only to a dedicated child worker and document exactly what differs**. The original source/physics code and environment freeze remain immutable. An engineering patch to subprocess setup is acceptable only if it does not change observations, actions, dynamics, controller state, model parameters or sampled scenarios.

If native library code or actual engine packages must change, construct a **separate isolated environment candidate** with a new fingerprint. This is a distinct physical execution domain; it must pass all replay/trajectory parity checks below before being considered equivalent to the registered source. If parity fails, stop the scientific campaign and report an engineering comparison, not a new experimental result.

---

## 4. Physical fidelity gate after any apparent crash fix

A successful `RenderMaterial` constructor is not enough. Before collecting a single fresh parent, perform an independent qualification in **a new output root**, never the old failed root:

- Use the **already inspected** qualification seed 13000000 and at least two other **preselected, previously inspected** old-seed parents from the November 15 frozen v1.2 evidence. All qualification seeds must be named *before* running outcomes; choose examples spanning original and perturbed conditions, including nonempty contacts and both terminal success classes where available. Do not select seeds by favorable new-source output.
- For each selected parent, reconstruct the full old action prefix from reset and verify exact model/actor provenance, controller/RNG state, time, robot/object pose and qpos/qvel, observations, action ordering, contacts, and the task success predicate. Do not use an unreliable native snapshot. Replay both original fixed interventions for 70 controls at the registered horizon.
- Independently compare the **complete time series** against the saved historical qualified trajectories with the originally registered tolerances. Save the first disagreement, not just summary error. Preserve source ids/hashes, source runtime, both action branches, outputs and all failed attempts.
- Verify that the old deterministic reference and new source have identical action-outcome labels and controlled physical trajectories. If comparison is impossible because historical trace channels are missing, mark the equivalence gate **INSUFFICIENT_EVIDENCE**; do not infer equivalence from final success alone.
- Run a separate fresh-process replay repeated twice for one qualification parent to verify initialization stability. Native crashes recurring during this gate require stopping new-data physics, not repeated unbounded retries.

**Conditional outcomes:**
- **Fidelity qualified:** Freeze the corrected *process configuration*, its hashes and the full parity evidence, register a new source-qualification seal referencing the old failed root, then proceed to P1.
- **Scene construction works but trajectories differ:** preserve the difference and stop P1; do not pool or replace the immutable source assumptions.
- **Crash persists, native fix requires system privileges or strict parity cannot be demonstrated:** stop P1; complete offline audits and the root-cause report. Do not claim an unsuccessful experiment.

No changes to DSRE source, conditions, risk allocation or router are authorized at this gate.

---

## 5. P1: Complete the frozen independent statistical campaign only after fidelity passes

Use the **original registered plan** as the source of truth. Freeze and hash the new qualification certificate, execution code and environment before opening fresh labels. Do not alter or re-register the scientific questions.

**Calibration:** all **256** parent seeds `15000000..15000255`, five approach-offset conditions per parent, both actions per condition, totaling 1,280 qualified checkpoints and 2,560 action continuations if all complete.

**Untouched test:** all **128** parent seeds `16000000..16000127`, five conditions, both actions, totaling 640 checkpoints and 1,280 continuations if all complete. No test future may start before all calibration parents, the independent physical audit, complete calibration decisions and seal. No partial calibration gate.

Every condition of a parent is one statistical cluster. No resampling, skipped-seed replacement, result-driven early stopping, post hoc threshold change, source-changing controller tweak or collapsing of the five conditions into independent examples.

**Registered risk method:** for each of the 17 fixed methods and each `continue` or `recover` action, a parent is assigned when at least one of its five conditions receives that action proposal. The parent is an error if **any** such assigned condition yields an inadequate action. Count one assigned/error parent per action stratum, not five checkpoints. Preserve primary target 10% unacceptable action rate, one-sided familywise confidence 95%, delta=.05/68 per predeclared claim. `n=0` means NOT QUALIFIED; for zero errors at least 69 independent assigned parents are needed. Do not recycle unused familywise allocation. Keep rare-action outcomes and failed qualifications visible.

**Risk gate:** qualify each action-specific method only if all 256 calibration parents are physically complete, independently audited, and its exact Clopper-Pearson upper bound is at most 10%. Freeze qualified/disabled action strata. Disabled/unknown recommendations STOP, not rerouted. The test must proceed even if DSRE or all comparators remain unqualified, provided physical source passes.

**Order on test:** freeze all test-parent predecision packets, proposals and gated decisions for the entire 128-parent cohort before opening paired futures. Then execute both unchanged actions physically for all conditions. Independently audit the paired branches and selected-action parity where the frozen protocol requires it. Never count repeated selected continuation as a new independent parent.

**Report with actual denominators and uncertainty:** parent-assigned and erroneous counts, simultaneous exact risk bounds, all four outcome categories, conditional and unconditional completion (STOP separately), genuine required recoveries, continue-only harm, both-success maintenance, neither-success insufficiency, B7 mathematical identity, CART/B5 and fixed-action baselines with the same permitted evidence and calibration opportunity, grouped paired 4,000-draw bootstrap intervals with the original fixed seed and no independence inflation. Any reference-library finite ceiling is descriptive, not a deployed guarantee. Noise results remain UNQUALIFIED unless separately calibrated on noise data, which is not authorized here.

Use one physical child at a time, unchanged physics lock, per-parent atomic progress, at most eight parents per chunk, bounded timeouts and fixed source hashes. Save every crash/partial attempt. A recurrent postqualification source violation halts further physics and must be reported as such rather than suppressed.

**Resource budget:** up to 12 new physics worker-wall hours after passing P0; up to 14 hours total campaign wall across forensic diagnostics, physics and final verification; 20 measured CPU core-hours; maximum 6 GB new evidence. Reserve one hour and two CPU core-hours for final numerical audit, tests, reproduction and sealing. If a strict budget cannot be met because of time already spent diagnosing, finish the largest scientifically valid subset and report the exact incomplete-cohort status. No artificial waiting. Do not promise work after the host session ends; checkpoint for resume by a later authorized agent on untouched parents only.

---

## 6. Independent audit, deliverables, and final status

Run independent scientific/audit code that does not import the production selector to recompute source fidelity, selected interventions, model hashes, full state/contact agreement, risk bound computation, four-way outcome counts and parent-clustered errors. Running generic tests is not a substitute for live physical qualification.

Required tests: broken native environment preflight (reproducible diagnostic, not a pass); supported runtime comparison; contact serialization still detects actual contact divergence; model/controller/RNG drift blocks; same-seed replay; atomic resume rules; calibration n=0 and incomplete-cohort handling; exact CP inversion and multiple-testing budget; hidden fault labels excluded from runtime; confident errors and abstention accounting; test-label isolation; full negative/unknown cases.

Run maintained `pytest -q tests`, Ruff lint/format and standalone independent physical, numerical and evidence-seal checks. Preserve original user changes, previous research histories, old `completion_manifest.json`, `.gitignore`, and `uv.lock`. Keep raw traces/logs only in a new ignored run root. Commit source, tests, nonsecret diagnostics and bounded report files locally. Do not push, publish, file public issues, request credentials or modify papers.

Create:

1. `docs/DSRE_SAPIEN_NATIVE_CRASH_DIAGNOSIS.md`: observed fault, platform/ICD/loaded-library comparison, isolated tests, any native backtrace, repair and its constraints, causal uncertainty.
2. `docs/DSRE_RUNTIME_PHYSICAL_QUALIFICATION.md`: new runtime fingerprint, preselected old-seed parity results or exact blocker, separate pass/fail for model, contact, controller, observations, physics and terminal success.
3. `docs/DSRE_SOURCE_RISK_COMPLETION.md`: all 256/128 parent denominators or explicit incomplete status, risk gate, paired action outcomes, strong comparators, physically required recovery and harm.
4. A new sealed `results/dsre-operational/<fresh-run-id>-runtime-recovery/` with parent attempts, logs, environment registry, independent checks, source hashes, actual states/outcomes if any, resource meter and completion manifest.
5. One concise supervisor handoff: exact branch and SHA, root-cause evidence, whether fidelity holds, parents completed, action-specific risk bounds, held-out effects where measured, tests and failed checks, resource usage and zero running workers.

**Outcome labels:** `RUNTIME_QUALIFIED_AND_DATA_COMPLETE`, `RUNTIME_QUALIFIED_COHORT_INCOMPLETE`, `NATIVE_RUNTIME_BLOCKED`, or `SOURCE_EQUIVALENCE_FAILED`. These report engineering/scientific completeness only, **not paper or venue readiness**. Do not call source-qualification failure an experimental negative result.

**Begin with Phase A and work through the fixed conditional path. No questions and no new DSRE methodological extensions.**
