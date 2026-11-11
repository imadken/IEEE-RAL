# REBOOT phase-constrained recovery recognition: supervised campaign report

**Decision: DATA_BLOCKED, authorized Case D completed.** The pinned release
does not provide the fixed pilot's event/phase coverage required to evaluate
recognition after failure onset and before human recovery. This is a data
qualification outcome, not a negative experiment on PCRR. No model was trained;
H1–H4 and RQ1–RQ5 remain untested. No alternative research project was started.

Reviewed base: `65965c96216748f0d930ef1546dd9aa70361b48d`. Branch:
`research/reboot-phase-recovery`. Preregistration commit: `a15401d`.
Evidence root (RUN): `results/reboot-phase/20261111T204459Z/`.
The local final commit, completion time, complete file checksums and final
resource totals are recorded in RUN/completion_manifest.json. Publication and
the next scientific decision remain with the principal researcher.

## 1. Scientific problem and positioning

The fixed question is whether task phases plus mechanical metadata improve
causal recognition of an emerging precision-assembly failure, especially on
previously unseen objects, over strong unconstrained temporal models. The
target interval is [t_f,t_r), not prediction of an arbitrary external injection
before it occurs. Offline alarms would not establish physical recovery success.

The complete [REBOOT v1 paper](https://arxiv.org/abs/2609.22591v1), including
appendices, was read. REBOOT already supplies shared phases and analyzes
failure/phase distributions, symmetry, clearance, operation direction and
recovery demonstrations. Those descriptive analyses are prior work. Its
single-collector, fixed-laboratory setting and standardized recording durations
limit independence and external validity; force/audio are unavailable. The
candidate contribution would require an incremental held-out-object benefit
from mechanical metadata and causal temporal constraints. None is established
by this audit.

The focused primary-source comparison was:

| Work | Established component and consequence for PCRR |
| --- | --- |
| [ProTAS, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Shen_Progress-Aware_Online_Action_Segmentation_for_Egocentric_Procedural_Task_Videos_CVPR_2024_paper.pdf) | Causal segmentation, GRU progress estimation and training-derived task graphs already combine progression with procedural constraints. This is the closest component overlap; PCRR cannot claim to invent it. |
| [Online temporal action segmentation, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/6c6c5fccf3c8661fcae219be7ca226f7-Paper-Conference.pdf) | Causal TCN, recurrent context and online refinement support a strong temporal comparator. Offline future-context segmentation is an unfair online baseline. |
| [FAIL-Detect, RSS 2025](https://www.roboticsproceedings.org/rss21/p073.html) | Sequential OOD signals and conformal calibration from successful rollouts establish failure detection without failure examples. Publisher abstract inspected; the acquired PDF has no extractable text. No reproduction claimed. |
| [Sentinel, CoRL 2024 proceedings](https://proceedings.mlr.press/v270/agia25a.html) | Temporal action-distribution consistency detects erratic behavior; VLM monitoring addresses task progression. A recorded human target vector does not provide a policy's sampled action distribution. |
| [SAFE v2](https://arxiv.org/abs/2506.09937v2) | Multi-task failure scoring from VLA internals and calibrated thresholds establishes transfer-oriented failure monitoring. Those policy embeddings are absent from these teleoperation records. |
| [Foresight v1](https://arxiv.org/abs/2606.23085v1) | Action-conditioned world-model representations, causal sequence scoring and conformal thresholds are prior failure-monitoring components. Its trajectory-label setup does not validate REBOOT onset-to-recovery labels. |

Targeted method sections were inspected for the latter papers; this was not an
open-ended novelty search. All PDFs, extracted text and immutable download
hashes are in RUN/literature and RUN/downloads.jsonl. No foundation models or
paid APIs were used. Standard filtering/grammar correctness is not a new theorem.

## 2. Dataset provenance and immutable versions

The [official project](https://nanayawoa.github.io/REBOOT/) and
[REBOOT26 dataset listing](https://huggingface.co/REBOOT26/datasets) identify the
sources. The 38-repository listing was saved before selecting the fixed cylinder,
USB-C and RJ45 families. Exact names/revisions and the mechanical mapping were
committed before trajectory analysis in [the registration](config/reboot_20261111.json).
Its SHA-256 is
`2edcbb3655e74f6890e14dd83c387d8422d1cace9556015af073024252931c11`.
RUN/repository_registration.json is identical.

| REBOOT26 repository suffix | Immutable revision | Actual episodes |
| --- | --- | ---: |
| sample_recovery-demonstration | 0633573d0438be1185bddebdf1a2c8f5505f7b2a | 60 |
| 16mm-cylinder_install | 77385af9a9acf3da3c76e8a8031e67623ff401e2 | 62 |
| 16mm-cylinder_remove | 76aad32aa7aea67cadedd32c3ee57b21dfffd0ce | 60 |
| 16mm-cylinder_recovery_install | f1aec3a47371e2f5c0841e0fadd2021ecb60bb5f | 60 |
| 16mm-cylinder_recovery_remove | 365c9bea6a0ba9628aeb81c4838725a19bebd131 | 60 |
| usb-c_install | 1f223f63cb070b95dadf2fedfe4e6a4bb914cccf | 60 |
| usb-c_remove | 0aa5c24fcc2e2cdb87b6bc3b1ba6ed5a5b0014a5 | 60 |
| usbc_recovery_install | 0ef0b37f0601fbafcc3bab07195a1fb5e756c6b4 | 33 |
| usbc_recovery_install2 | 83709ed9d1d7f733781e582d2e36702de4dd9685 | 30 |
| USBC_recovery_remove | beba0e619331a54bb04d1349de07cf4064410725 | 61 |
| rj45-install | 1b5f443c62c70677610d06d7d223b830d090b884 | 63 |
| rj45_remove | d61344baccbb93497d6b4b1d02f72ba13a422bc2 | 63 |
| rj45_recovery_install | f6acd5b69394ffd4d2d8bd30079306c9e2061bbe | 60 |
| RJ45_recovery_remove | 245c045b104eedbb85e0216d8a6a0a8c86375788 | 61 |

The 13 pilot repositories contain **733 episodes, 492,968 frames**:
368 expert-source and 365 recovery-source episodes. Cylinder has 242 episodes,
USB-C 244 and RJ45 247. The engineering sample adds 60 records/53,886 frames
to the acquisition, but all 60 state/action/time trajectories exactly duplicate
cylinder recovery-install trajectories. They are not independent training data.
Including those copies, 793 projected tables contain 546,854 rows.

The official linked source fork `anon-robo-account/REBOOT` was pinned to
`269d53958caf32913104c5a93f8ee4ed84704a0f`, tree
`7dbfbc94c27bb0478f97598fc59f9fbea6b56061`. Four inspected source files match
their Git blob hashes (RUN/upstream/source_manifest.json); none was executed
to trim/repair data. The trimming tool's existence is not evidence that it
caused the observed defects.

All 82 acquired metadata files match their published Git/LFS hashes. Large
depth-embedded Parquets were accessed with strict HTTP ranges: only footer,
state, action, timestamps and indexing columns. Range offsets/Content-Range,
bytes and SHA-256 plus separate projected-table hashes are retained. This
certifies the saved ranges, not the complete large upstream Parquets' LFS hashes.
No video archive, depth stream or model weights were downloaded.

## 3. Failure and recovery event-label audit

**No pilot repository has a phase/event annotation file.** Actual trajectory
schemas and info metadata contain no event/phase/operator/session label fields.
The sample alone has meta/phase.json. It labels all 60 episodes as recovery,
with no annotated clean controls. Identical cylinder trajectories establish
duplication, not labels for USB-C/RJ45 or clean phase windows.

Every raw sample entry was retained. Counts below distinguish schema acceptance
from a physically meaningful event target:

| Check | Result |
| --- | --- |
| Raw annotation entries | 60 |
| Strict schema accepted | 58; episode 16 has originating_phase=0, episode 26 has 21 |
| Positive, actual-frame-bounded raw [t_f,t_r) intervals | 57/60 |
| Positive bounded intervals among schema-accepted records | 55/58 |
| Empty intervals | Episode 35: 390→390; episode 48: 270→270 |
| Reversed interval | Episode 37: 360→51; also tau_4=tau_5=897 |
| Raw annotated duration versus actual frame count | All 60 say 897, actual 898/899; 1–2 uncovered tail frames |
| Originating phase differs from current half-open phase at onset | 35/58 accepted entries; 19 away from a boundary, 16 on one |
| Quantization | All 60 raw onsets and 59/60 recovery starts are whole seconds at 30 Hz |

Phase disagreements are semantic/convention warnings: an originating phase
may refer to an earlier cause rather than the current phase. They were not
silently relabeled or all declared false. The nonmonotonic episode has no
well-defined current phase under the declared bounds. Likewise, the duration
discrepancy alone does not prove the positive event windows invalid. These
distinctions do not resolve the absent multi-object annotations.

The raw sample has 11 mode strings (28 misalignment, 9 slip, 6 premature_release,
5 excessive_force, 3 each retention_failure/sub_mm_misalignment, 2 jamming,
and one each poor_engagement/premature_grasp/delayed_start/freeze). Among the
58 schema-accepted records misalignment/slip counts are 27/8. Raw operator IDs
are op-00:2 and op-01:58; sessions are 2026-04-15:59 and initial:1. Those strings
do not establish independent operators, particularly given the paper's
single-collector statement. The plural annotation repo_id namespace differs
from the actual singular sample repository; no automatic rebinding was applied.

One complete metadata Parquet is published corrupt:
usbc_recovery_install/meta/episodes/chunk-000/file-000.parquet, 196,608 bytes,
SHA-256 `c2edd7790273c14ba3ff63d7dbb1d0368d8ca3086503e66277c0edd3de2af160`.
Its LFS hash matches the saved full file; its footer is absent. No rows were
invented to repair it. All 33 declared episode trajectories remain readable.
An extra listed data/chunk-000/file-033.parquet also lacks a readable footer;
only its footer ranges were fetched. Its listed whole-file LFS hash
`4a14e0662e32208e022c8b409e55b22988218b756cc8afde80caed79df6ddebd`
was **not** verified by a full download. This extra object is not a missing
declared episode: IDs 0–32 were all acquired from other files.

## 4. Causal observations and leakage rules

All acquired trajectories have aligned finite 14-dimensional state and action
arrays, contiguous zero-based episode frames and 30 Hz timestamps within float
precision. These are bimanual joint positions/targets including grippers, not
normalized OSC actions. Array/time alignment does not independently establish
the physical actuator delay or camera content synchronization. Four camera
streams and spans are declared in metadata; no video was decoded, so actual
RGB/proprioception or depth alignment remains unverified. Sample metadata still
mentions depth statistics while its actual schema omits depth.

The implemented audit feature contract uses current qpos, backward finite
differences and previous-frame issued target minus current state (42 channels).
First-frame derivative/error are zero. Prefix-invariance tests show no future
frame/current human corrective action enters these features. Only static
symmetry, direction and clearance can accompany them. Runtime schema rejects
event times, true phase/mode, outcome, repository and future actions. No feature
was fitted, normalized across held-out data or used to generate an alarm.

## 5. Temporal/phase model specification

PCRR remains a conditional registered method, not an implemented/trained
recognizer. A training-derived finite-state phase/recovery grammar would allow
documented recovery backtracking. It cannot be extracted or qualified from
absent pilot phase labels. No HMM, GRU, transition mask, learned grammar,
explanation generator or theorem was substituted for this missing prerequisite.
Phase B's matched physical-signal assessment was not qualified; audit feature
alignment is not evidence of detectable physical failure onset.

## 6. Strong baseline specifications

| Baseline | Registered comparison | Actual execution |
| --- | --- | --- |
| B0 | Time/phase-duration prior | Not fitted |
| B1 | Causal stall/deviation detector | Not fitted/calibrated |
| B2 | Regularized causal-window classifier | Not fitted |
| B3 | Small unconstrained causal TCN/GRU | Not fitted |
| B4 | Phase-aware temporal model without metadata | Not fitted |
| B5 | Phase-aware model with metadata, no constraints | Not fitted |
| B6 | PCRR with metadata and training-derived grammar | Not fitted |
| B7 | Annotated-phase oracle, nondeployable | Not evaluated |

No random predictions, source-role classifier or oracle output is presented as
a baseline run. The decisive B6 versus B3/B4/B5 comparisons remain unavailable.

## 7. Training, qualification and test grouping

The object set, source pins, gate and mechanical map were frozen before data
analysis. The cylinder/USB-C/RJ45 mappings are continuous/C2/C1 and
0.20/0.09/0.13 mm; both operations are included. No object was replaced.
No train/development/test partitions were activated because the label gate
failed. No overlapping windows were split across datasets. Sample duplicates
would need one grouping if training became authorized. Operator/session
holdouts cannot be established from absent pilot identifiers. Three objects
would support only exploratory per-object holdouts, not precise population
generalization. No qualification labels were used to tune a threshold or grammar.

## 8. Episode-level failure recognition results

No recognition experiment ran. Sensitivity, clean false alarms, before-recovery
detection fraction, phase accuracy, mode macro-F1, calibration/log loss and
inference latency are **N/A**, not zero. Paired comparison confidence intervals
are N/A. Counts in this report describe the acquired immutable release rather
than statistical estimates from a trained recognizer. Expert-source identity
was not treated as verified absence of every physical deviation.

## 9. False-alarm versus detection-delay curves

No predicted scores or alarms exist; detection-delay distributions and
false-alarm frontiers cannot be computed. RUN/figures/annotation_integrity.pdf
and .png plot annotation timing and missing pilot coverage only. The diagonal
compares released onset/recovery timestamps, not alarm predictions. No fabricated
performance curves or arbitrary confidence intervals were generated.

## 10. Held-out-object and mechanical-metadata comparisons

All three fixed families were inspected, but there is no held-out-object model
evaluation. Metadata benefit, B6–B3/B4/B5 effects and their uncertainty are N/A.
Distinct static attributes do not demonstrate a transferable causal mechanism;
with one object per attribute combination, object identity and attributes are
also confounded. Annotation availability must be resolved before that hypothesis
can be tested.

## 11. Ablations and robustness

No model ablations, sensor missingness/delay controls, latency benchmarks or
conditional vision extension ran. Those paths require valid labels and a
working proprioceptive pilot. No observed result establishes Case E (vision-only
evidence). Engineering checks did exercise causal prefix invariance, forbidden
inputs, malformed events, range enforcement, rate-limit deferral, archive
tampering/gaps, preservation, budgets and sealed-evidence rejection.

## 12. Negative findings and shortcut risks

The main negative finding is **release/task incompatibility at these pins**,
not failure of temporal reasoning. The sample is all recovery and duplicates
one object. Repository identity reveals expert/recovery source role by dataset
construction and is forbidden as a runtime feature. Whole-release
object/operation/final-duration bucket majority purity is **57.8445%**, independently
recomputed. This uses future recording length and source role; it is a
descriptive identifiability check, not B0, a causal classifier, held-out accuracy
or evidence that a failure detector solves the task. Standardized lengths,
rounded labels, short exceptions and standby/padding are audit concerns.
No hypothesis or model was rejected from this number.

Initial DNS failure, a first Sentinel PDF URL returning 404 and the immutable
bad footer were retained. The main range batch encountered 82 HTTP 429s and
one TLS timeout. After a five-minute cooldown, a two-worker retry recovered
all 83 transient failures. The immutable footer was not repeatedly fetched.
Final acquisition covers every declared episode; no engineering failure is
being confused with absent annotation coverage. The downloader now shares
rate-limit cooldown across workers and refuses ignored/misaligned ranges.

## 13. Independent audit and tests

The separate scripts/reboot_independent_audit.py imports no main auditor or
experiment executor. Offline it reconstructed original Parquet access from
saved ranges and compared all 793 tables, 6,344 acquired range hashes and
546,854 rows with projections. It independently recomputed 58 accepted label
joins, both schema-invalid records, all 60 duplicate groups, duration purity,
82 metadata hashes, the published corrupt metadata and zero pilot annotations.
Result: **PASS**, no mismatches (RUN/independent_audit.json).

RUN/qualification.json SHA-256:
`bfe2991b918ddbef9a7ad3ab5859243ab5511141469a4d6da62465503d7d9e98`.
The independent audit binds that exact hash. commands.jsonl preserves executed
argv, source hashes, exit status, wall/CPU, memory and log hashes. Earlier
acquisition/auditor versions and failed evidence remain in RUN/provenance.

Validation: **34 focused tests passed**; **21 REBOOT tests passed in the new
isolated environment**; **246 maintained tests passed, 4 skipped**. The four
historical physics checks require their original MuJoCo environment and were
not activated. Ruff check passed; all 114 maintained Python files passed the
format check. Closing verification rechecks all 691 initially tracked
files, 32,600 files in both preceding seals and the earlier 1,015-file inventory.
No historical simulator work is restarted by these checks.

The audit is independent by implementation, not a second human annotator or
separate research team. Its agreement establishes reproducible byte/label
checks, not that the annotations describe the true physical onset.

## 14. Resource accounting and reproducibility

Campaign start: 2026-11-11 20:44:59 UTC. Limits: 8 wall hours, 10 measured CPU
core-hours, 2 GPU hours, 6 GB initial transfers, 10 GB new artifacts.
All scientific jobs are foreground and finished. **Zero GPU work, models,
simulator workers, robot executions or paid API calls.**

The saved response-body journal totals **179,142,993 bytes**. Unsuccessful
bounded requests and interactive/source fetches are conservatively charged an
additional 300 MB; the entire new uv cache is charged as an upper bound for
dependency downloads: **704,539,133 bytes** total conservative transfer charge.
New artifacts, environment, duplicated logical hard
links and caches are counted inside RUN, with another 50 MB for Git/cache/seal
overhead. Resources are well below the limits. RUN/resources.json and
completion_manifest.json contain exact final worker CPU, closing CPU, campaign
wall, aggregate worker wall, maximum child RSS, disk and transfer bounds.
Interactive editor/tool/web/initial closing probes and host background CPU are
unmetered; no whole-host exact CPU claim is made. Resource accounting includes
failed attempts and retries.

Verified preseal checkpoint (RUN/preseal_resources.json; the final seal adds
its own closing cost):

| Resource | Recorded value |
| --- | ---: |
| Campaign wall | 3,600.084 s |
| Measured workers/drivers plus successful closing checks | 443.089 CPU s |
| CPU charged including the lost-metering upper bound | 2,564.646 s (0.7124 core-hours) |
| GPU / paid API usage | 0 / 0 |
| Maximum child RSS | 487,452 KiB |
| New logical artifacts, environment and caches | 658,728,362 bytes |
| Storage including external/seal allowance | 708,728,362 bytes |
| Transfers including dependency/cache and failure allowance | 704,539,133 bytes |

A final test rerun passed 241 tests but its driver encountered a disappearing
pytest lock file during disk enumeration, losing per-process CPU metering.
The child finished; no worker remained. Its preserved log creation-to-final-write
interval, plus ten seconds, charged across all 64 logical CPUs gives an additional
**2,121.558 CPU-second upper bound**, not a measured duration. It is included
in the final CPU budget and every later driver's gate (unmetered_commands.jsonl).
Disk scans now tolerate vanished transient files; unexpected driver exceptions
terminate and reap the child. New regressions and the final maintained suite
passed after this fix. Early closing inventory checks also required distinguishing
older interpreter-symlink hashes from the later regular-file-only seal's omitted
pytest alias; no historical bytes changed. Both diagnostic outcomes are retained.

The preregistration, report and small source/test/dependency files are committed.
All raw data, original ranges, projections, papers, examples, figures,
environment, caches and logs remain local. `.gitignore`, historical uv.lock,
simulator environments, prior seals, source and reports remain unchanged.
Only the local Git exclusion was extended for this new evidence directory.
No GitHub push or authentication setup was attempted.

Create a fresh isolated environment for inspecting the audit interfaces (choose
an unused path; the original environment/evidence must remain read-only):

```bash
REBOOT_ENV=/tmp/reboot-phase-audit-env
uv venv --python .venv/bin/python "$REBOOT_ENV"
uv pip sync --python "$REBOOT_ENV/bin/python" config/reboot_python312.txt
PYTHONPATH=src uv run --no-project --python "$REBOOT_ENV/bin/python" \
  python -m dual_rec.reboot.audit --help
PYTHONPATH=src uv run --no-project --python "$REBOOT_ENV/bin/python" \
  python scripts/reboot_independent_audit.py --help
uv run --no-sync pytest -q tests
uv run --no-sync ruff check src scripts tests
uv run --no-sync ruff format --check src scripts tests
```

Full executed acquisition/audit commands and immutable input URLs are in
commands.jsonl/downloads.jsonl. Do not recreate the environment or write outputs
inside the sealed original run. The commands above illustrate a fresh-run
workflow and inspection interfaces, not permission to mutate sealed evidence.

## 15. Scientific recommendation and completed boundary

**DATA_BLOCKED / Case D.** Phase A and the independent Phase G data-integrity
fallback are complete. Phase B did not qualify; Phases C–F, B0–B7 training,
conditional vision and recognition metrics were not activated. No detached
research workers remain. This satisfies the authorized conditional stopping
boundary; it does not establish a PCRR contribution or a manuscript result.

A small, separate **annotation-release requalification** is justified after
authoritative phase/event files cover the fixed clean and recovery episodes,
invalid sample records and conventions are clarified, and published corrupt
metadata is corrected. Require a documented annotation-to-trajectory join,
event semantics and genuine session/operator information before proposing a
full method campaign. Automatic relabeling from future human actions, another
object selection, or a new model campaign is not justified by this evidence.
The principal researcher should review the preserved audit before further work.
