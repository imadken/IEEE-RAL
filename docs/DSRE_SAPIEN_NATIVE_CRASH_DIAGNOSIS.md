# DSRE: native SAPIEN crash diagnosis and process correction

Run root: `results/dsre-operational/20261116T130334Z-runtime-recovery` (R).
Starting commit: `9a6ddb40ea7b347744090de2191cc6bda70f9260`.
Branch: `research/dsre-runtime-qualification-recovery-20261116`.
The previous sealed failure root is preserved byte-for-byte. Its SIGSEGV is
historical evidence, not an unsuccessful physical intervention.

## Observed cause and controlled comparison

The fault is localized to the **host NVIDIA native driver initialization path**.
An unchanged host prefix reproducibly exits with signal 11. GDB catches SIGSEGV
in `libcuda.so.1`, with callers in `libnvidia-eglcore.so.550.163.01` and the
system Vulkan loader. The Python fault site remains SAPIEN `RenderMaterial`
creation during PickCube scene construction. This identifies the failing
native path, not a precise proprietary-driver defect or evidence of an update.

The original source already uses `sim_backend="cpu"`,
`render_backend="none"`, state observations and the unchanged Panda controller.
Nevertheless, creating task visual materials reaches Vulkan discovery. Disabling
rendering at the task interface therefore did not prevent this initialization.

| Independent bounded subprocess | Observed result |
|---|---|
| Frozen mixed-path imports, restricted process | Success; actual imported paths recorded |
| Direct SAPIEN material, restricted process | Success |
| Original scene/reset and old prefix, restricted process | Success |
| Exact historical prefix command, restricted process | Success |
| Host original prefix, no ICD override | SIGSEGV (-11) |
| Restricted GDB | ptrace denied; no inferior execution, despite GDB status 0 |
| Host GDB, original prefix | Inferior SIGSEGV in NVIDIA CUDA/EGL/Vulkan path, despite GDB status 0 |
| Host direct material and original prefix, existing Lavapipe ICD selected | Success |

`nvidia-smi` fails in the restricted process but reports an RTX A4000 and driver
550.163.01 on the host. The restriction is not proof that the workstation driver
is absent. The successful restricted launches also are not proof of host
runtime stability. The counterfactual host trials retain the same Python,
packages, source, seed and process settings, changing only
`VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json`.

This is the one adopted correction. It selects an already installed Vulkan
ICD in each dedicated worker. It does not change PhysX CPU simulation, task
render settings, observations, dynamics, material parameters, controller,
actions, outcome predicate or seeds. No package, driver, system ICD, kernel or
global environment is modified. Material/scene construction is never bypassed.
The original writable Matplotlib cache location is retained as metadata setup.

## Source, libraries and causal limits

All ten packaged build/metadata fingerprints in the successful November 15
record match. Actual imports resolve SAPIEN, ManiSkill and Torch in `.venv`,
while the original mixed path resolves NumPy 1.26.4 and Pydantic 2.12.3 in the
REBOOT environment. Loaded native paths, system loader dependencies, ICD JSON
and native ELF hashes are recorded in R. Current user-space and kernel NVIDIA
version strings are 550.163.01. The historical package fingerprint did not seal
a complete driver inventory; no driver update is inferred.

Removing the optional REBOOT path also permits imports and scene creation but
selects Pydantic **2.14.3**. That diagnostic alternative is rejected for scientific
execution. The repaired worker retains the original mixed path and all original
package provenance. No result is used to select another physics implementation.

`vulkaninfo` is unavailable; it was not installed. The existing Lavapipe manifest
and library are inspected and hashed, and their viability is established by
actual host material/prefix execution. The loader documents process-local ICD
selection for avoiding a problematic driver:
[Vulkan loader driver discovery](https://vulkan.lunarg.com/doc/view/latest/linux/LoaderDriverInterface.html).
ManiSkill's installation guidance motivates graphics-driver checks but does not
establish the cause of this particular fault:
[ManiSkill installation and troubleshooting](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html).

Each trial is foreground, timeout-bounded and protected by the existing PhysX
lock. Core dumps are disabled in the diagnostic process and inherited children.
No configuration has more than two diagnostic trials. Raw logs and GDB frames
remain local under `R/diagnostics`; no raw logs are committed. Diagnostic phases
finish within the 30-minute inventory and 75-minute isolation limits.

## Scientific gate

A working material constructor or prefix alone is insufficient. The candidate
must match three preselected old parents, every five-condition prefix, controller
and saved RNG state, both 70-control branches, complete recorded trajectories,
contacts and terminal labels, plus two fresh-process repetitions. See
[the physical qualification record](DSRE_RUNTIME_PHYSICAL_QUALIFICATION.md).
Fresh cohorts remain forbidden until its independent seal passes.

The full source and process hashes are frozen in R before qualification.
Native fault logs, including GDB's misleading wrapper exit status, remain part
of the evidence. The original failed seal is never edited or reclassified.
