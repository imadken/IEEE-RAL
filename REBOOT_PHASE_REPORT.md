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


## Overnight research extension: 20261111T224622Z

The new supervised scope authorizes this single-object recording-level study; the original multi-object DATA_BLOCKED report above remains unchanged. All values below are measured out of fold, relative to released annotations.

| Model | Input | Timely / evaluable | Premature / 55 | Reference alarms / 62 | Median detected delay; misses | Phase inference | Fit wall (s) |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| B0 | clock | 0/55 | 0/55 | 0/62 | N/A; 55 misses | — | 0.19 |
| B1 | Q | 1/55 | 54/55 | 10/62 | 0.10s; 54 misses | — | 0.47 |
| B2 | Q | 5/55 | 46/55 | 16/62 | 2.50s; 50 misses | — | 0.90 |
| B3 | Q | 1/55 | 53/55 | 6/62 | 2.00s; 54 misses | — | 63.25 |
| P0 | Q | 1/55 | 54/55 | 9/62 | 2.00s; 54 misses | unfiltered | 62.63 shared |
| P1 | Q | 0/55 | 54/55 | 4/62 | N/A; 55 misses | forward filter | 62.63 shared |
| P2 | Q | 1/55 | 54/55 | 12/62 | 2.00s; 54 misses | EMA .3s | 62.63 shared |
| B1 | Q+C | 1/55 | 54/55 | 11/62 | 0.10s; 54 misses | — | 0.83 |
| B2 | Q+C | 9/55 | 44/55 | 8/62 | 2.30s; 46 misses | — | 1.22 |
| B3 | Q+C | 3/55 | 50/55 | 12/62 | 1.80s; 52 misses | — | 60.43 |
| P0 | Q+C | 2/55 | 50/55 | 10/62 | 1.40s; 53 misses | unfiltered | 63.92 shared |
| P1 | Q+C | 1/55 | 50/55 | 10/62 | 1.00s; 54 misses | forward filter | 63.92 shared |
| P2 | Q+C | 2/55 | 50/55 | 11/62 | 1.40s; 53 misses | EMA .3s | 63.92 shared |

P0/P1/P2 share one fit per fold/input/seed: their fit time is repeated for transparency, not three independent trainings. These detected-only medians exclude the stated misses. Reference alarms are not certified physical false positives.

### What completed and what the data supports

All five folds completed: five shared clock fits, ten ridge dynamics fits, ten ordinary window classifiers, thirty phase-free GRUs and thirty shared phase-head GRUs (seeds 11/23/37, 30 epochs), plus ten development-only permuted-label window fits. There are 95 checkpoints, 85 in the main comparison. All models, preprocessing and continuous OOF predictions remain local.

The 60 sample aliases match cylinder-recovery state/action/timestamps and frame order exactly. They contribute 55 unique eligible recovery recordings, not 115; 62 unique cylinder-install expert-source references bring the cohort to 117. Original sample entries 16,26,35,37,48 remain excluded. Neither malformed phase IDs nor event times were repaired. Five deterministic role-balanced folds use k for evaluation, (k+1)%5 for calibration and three other folds for fitting. Shared collection conditions and overlapping training folds make this exploratory cross-fitting, not untouched confirmation.

All training folds support chronological phases 1–4 before recovery, with no phase-5 supervision. Expert phase loss is masked. Originating failure phase is never substituted for chronological phase. Constant single-object symmetry/clearance cannot establish a mechanical-metadata benefit. No operator/session or cross-object failure-generalization claim is supported.

### Primary paired effects

Differences below are percentage points with 95% exploratory paired intervals from 2,000 recording-level, source-role-stratified resamples. Seeds, aliases and windows are not resampling units.

| Input | Contrast | Timely difference [CI] | Premature difference [CI] | Reference-alarm difference [CI] |
| --- | --- | --- | --- | --- |
| Q | B3-B2 | -7.27 [-14.55, -1.82] | +12.73 [+3.64, +23.64] | -16.13 [-29.03, -4.84] |
| Q | P1-P0 | -1.82 [-5.45, +0.00] | +0.00 [-5.45, +5.45] | -8.06 [-16.13, +0.00] |
| Q | P1-P2 | -1.82 [-5.45, +0.00] | +0.00 [-5.45, +5.45] | -12.90 [-22.58, -4.84] |
| QC | B3-B2 | -10.91 [-20.00, -1.82] | +10.91 [+1.82, +20.00] | +6.45 [-6.45, +19.35] |
| QC | P1-P0 | -1.82 [-5.45, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [-6.45, +6.45] |
| QC | P1-P2 | -1.82 [-5.45, +0.00] | +0.00 [+0.00, +0.00] | -1.61 [-8.06, +3.23] |

B3 has fewer timely detections than B2 in both regimes; the Q comparison also spends fewer reference alarms, so it is not uniform domination. P1 provides no timely benefit over either P0 or ordinary smoothing. Lower reference alarms without timely recognition are not recovery success. No favorable architecture, seed, threshold or scoring rule was substituted.

### Timing, commands, uncertainty and robustness

Only B0 receives elapsed time. It makes no alarms at its common-exposure calibrated point and detects no events. Human targets are lagged one native frame; Q-only remains essential because teleoperator commands can reveal reaction or collection procedure rather than an autonomous policy's evidence. Q+C improves B2 from 5 to 9 timely detections, but 44/55 first alarms remain premature; it does not rescue the GRU/phase hypothesis. Physical onset remains unvalidated and annotations are rounded.

| Input/model | Clean timely | Drop 10% | Drop 30% | Delay .2s | Delay .5s | Optimistic onset reset |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Q/B1 | 1/55 | 1/55 | 1/55 | 1/55 | 1/55 | 55/55 |
| Q/B2 | 5/55 | 7/55 | 6/55 | 6/55 | 8/55 | 48/55 |
| Q/B3 | 1/55 | 1/55 | 1/55 | 1/55 | 1/55 | 51/55 |
| Q/P0 | 1/55 | 0/55 | 0/55 | 1/55 | 1/55 | 51/55 |
| Q/P1 | 0/55 | 0/55 | 0/55 | 0/55 | 1/55 | 51/55 |
| Q/P2 | 1/55 | 0/55 | 0/55 | 1/55 | 1/55 | 51/55 |
| QC/B1 | 1/55 | 1/55 | 1/55 | 1/55 | 1/55 | 55/55 |
| QC/B2 | 9/55 | 10/55 | 7/55 | 10/55 | 11/55 | 52/55 |
| QC/B3 | 3/55 | 3/55 | 1/55 | 3/55 | 3/55 | 51/55 |
| QC/P0 | 2/55 | 2/55 | 2/55 | 2/55 | 2/55 | 51/55 |
| QC/P1 | 1/55 | 1/55 | 1/55 | 1/55 | 1/55 | 50/55 |
| QC/P2 | 2/55 | 2/55 | 2/55 | 2/55 | 2/55 | 51/55 |

Thresholds are unchanged under synthetic packet loss/delay. Every condition's premature/reference alarms, exposure and censoring are in tables/summary.csv, not hidden behind timely counts. The onset-reset column deliberately erases the first premature alarm and restarts persistence; it is an invalid optimistic diagnostic, never the main result. For Q/B3 it changes 1/55 valid timely detections to 51/55. The first-alarm rule prevents that inflation.

The .5/1-second interior analyses retain the original first alarm and report emptied interiors/timing ambiguity. They are stress offsets, not validated onset confidence bounds; paired comparisons use common eligible recording subsets. Full results and changed denominators are in summary.json/paired_effects.json. Missingness holds only received packets; derivatives use source timestamps. Delays hide both observations and commands initially. Prefix tests and independent reconstruction check that future data never fills a past score.

All seed-specific calibrated recording outcomes are in tables/seed_results.csv, and all five fold numerators in tables/fold_results.csv. The fixed interval permutation uses only training donors and evaluates B2 on calibration-fold development recordings, not on main evaluation folds. It reduces development timely counts from 8 to 2 (Q) and 9 to 3 (Q+C), while 51/55 premature alarms persist. This does not validate the physical labels or eliminate collection-role shortcuts.

### Boundary interiors and initialization variation

| Input/model | Original timely/support | .5s interior | 1s interior |
| --- | ---: | ---: | ---: |
| Q/B2 | 5/55 | 5/53 | 5/51 |
| Q/B3 | 1/55 | 1/53 | 1/51 |
| Q/P1 | 0/55 | 0/53 | 0/51 |
| QC/B2 | 9/55 | 8/53 | 6/51 |
| QC/B3 | 3/55 | 3/53 | 2/51 |
| QC/P1 | 1/55 | 1/53 | 1/51 |

Two/four interiors become empty at .5/1s. Shrinking denominators are not new detections. Sensor-delay increases can simply move early alarms into the released window, rather than improve sensing. No offset is promoted to corrected ground truth.

| Input/model | Seed 11 timely/premature/reference | Seed 23 | Seed 37 |
| --- | --- | --- | --- |
| Q/B3 | 2/48/9 | 1/51/9 | 8/45/8 |
| Q/P0 | 1/54/5 | 0/52/9 | 0/55/12 |
| Q/P1 | 1/50/8 | 0/52/4 | 1/54/6 |
| Q/P2 | 1/54/5 | 0/52/9 | 1/54/10 |
| QC/B3 | 3/50/7 | 2/51/5 | 2/49/17 |
| QC/P0 | 4/49/6 | 2/51/12 | 2/51/7 |
| QC/P1 | 4/48/7 | 2/51/10 | 2/48/10 |
| QC/P2 | 4/49/7 | 3/51/12 | 2/51/10 |

Each seed is calibrated on the same nominal-reference calibration group; denominators are 55 recovery and 62 reference recordings. The primary ensemble averages probabilities before calibration and is not an average of these counts. Initialization sensitivity is material: Q/B3 varies from 1 to 8 timely events; the favorable seed was not selected as the main result. Thus the negative primary contrast concerns the frozen ensemble, not every possible initialization.

### What the phase layer changes

Q: P0: 61.01% phase accuracy; 678 marginal-argmax edge violations; P1: 63.56% phase accuracy; 84 marginal-argmax edge violations; P2: 62.61% phase accuracy; 283 marginal-argmax edge violations.

QC: P0: 64.98% phase accuracy; 582 marginal-argmax edge violations; P1: 70.94% phase accuracy; 116 marginal-argmax edge violations; P2: 67.34% phase accuracy; 265 marginal-argmax edge violations.

Accuracy is restricted to annotated pre-recovery intervals; violation counts span the full scored replay and are not physical-recovery labels. Filtering improves this secondary phase measure but not the primary timely-recognition contrast. Observed edges/self loops, train-only counts and Laplace pseudocount 1 define the matrix. Initial counts receive fixed smoothing. Neural emissions are potentials, not calibrated generative likelihoods. Impossible normalization retains the prior state and emits a flagged unfiltered fallback. No such fallback is concealed.

Positive latent paths use allowed edges; marginal-argmax labels need not. The regression counterexample has previous mass (.4,.6,0), transitions 0→{0,2}, 1→1, 2→2 and emissions (.01,.01,1): the marginal label switches 1→2 despite that edge being forbidden. Standard causal GRUs, forward filtering, EMA, task graphs and this distinction are not new theory. REBOOT already supplies the phase framework; ProTAS is the closest structured online segmentation component (references in the original report).

### Limited external reference shift

After the main prediction/model seal, frozen cylinder models were applied without refitting or threshold changes to 306 unique expert-source recordings. Identical named joint/gripper channels, order, dtype, robot/export and 30-Hz timing were checked; no mapping was chosen from performance. This is a native-export distribution diagnostic. Physical SI calibration is not independently certified, and the official source tree did not supply the custom robot driver. It is not cross-object failure detection.

| Reference source | Q B3 alarm counts across five frozen folds | Q P1 counts | Q+C B3 counts | Q+C P1 counts | Unique recordings |
| --- | --- | --- | --- | --- | ---: |
| 16mm-cylinder_remove | 38,43,51,38,25 | 23,47,9,12,8 | 59,57,57,51,52 | 36,14,18,21,26 | 60 |
| usb-c_install | 60,60,60,60,60 | 57,60,22,59,57 | 60,60,60,60,60 | 60,43,50,60,60 | 60 |
| usb-c_remove | 60,60,60,60,60 | 60,60,52,60,60 | 60,60,60,60,60 | 58,11,26,54,57 | 60 |
| rj45-install | 62,62,62,62,62 | 62,62,43,62,62 | 62,62,62,62,62 | 62,54,42,62,62 | 63 |
| rj45_remove | 61,62,62,62,62 | 53,55,42,49,52 | 62,62,62,62,62 | 62,61,61,62,62 | 63 |

These are five repeated analyses of each external recording, not 1,530 independent recordings. Alarm/exposure counts, score distributions and full-bundle latency are retained per recording/fold in external_outcomes.json. Very short recordings remain censored, with exposure availability explicit. High alarms are distribution sensitivity, not new failure labels. Unannotated recovery sources are excluded. Missing target events prohibit target sensitivity/delay or metadata-transfer claims.

### Streaming replay and explanation examples

The runtime accepts only timestamped current observations and previously issued targets. It carries recurrent and filtered state from recording start; labels, future duration and true phase are evaluator-only overlays. All four deterministic categories are attempted under both Q and Q+C, choosing earliest first-alarm time then canonical ID (non-alarming misses sort last). Absent categories remain explicit; Q/P1 has no timely example. Trace fields show actual motion/target residual, phase/emission distributions, allowed predecessor mass, filter score change, persistence and threshold. They explain model computation, not friction/misalignment or another physical cause.

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 \
PYTHONPATH=src:results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages \
uv run --no-sync python -m dual_rec.reboot.overnight_replay --root results/reboot-overnight/20261111T224622Z \
  --group recording:d7ab759bd690a02afba335860c4f44d4b794d86d60606e2794a67bc6cbc76651 --variant QC --method P1
```

Q: 3/4 categories present; maximum streaming/batch risk discrepancy 8.37e-08; packet mean inference 1.31–1.35 ms across examples. Per-category first-alarm agreement and traces are in streaming/examples_Q.json.

QC: 4/4 categories present; maximum streaming/batch risk discrepancy 9.93e-08; packet mean inference 1.30–1.35 ms across examples. Per-category first-alarm agreement and traces are in streaming/examples_QC.json.

The earliest missed-target example also has a premature first alarm, so those two categories share a recording in each input regime; they are not additional independent demonstrations. Full non-alarming/late cases remain in the outcome and prediction files.

### Claims and next evidence

| Established in this run | Unsupported here | Required next evidence |
| --- | --- | --- |
| Completed single-object trained OOF baseline/phase comparison and causal replay | Improved physical recovery, safety or causal root-cause identification | Prospective robot/policy evaluation, independently verified outcomes |
| Phase filtering improves chronological phase accuracy/coherence in this sample | Improved timely recognition beyond ordinary smoothing | Frozen-model test on a new, counterbalanced collection session |
| First-alarm accounting reveals heavy premature alarms; onset-reset evaluation inflates apparent success | Robust recognition of true physical onset or useful deployment performance | Independently adjudicated physical onset/recovery boundaries and nominal references |
| Native external references expose distribution sensitivity | Cross-object failure sensitivity, mechanical-metadata benefit or operator generalization | Attributable target-object events, multiple objects per mechanical attribute and independent operators |

The smallest useful next confirmation is an independently collected, counterbalanced cylinder session: matched start conditions/recording exposure across roles, externally annotated onset and human-recovery times, and a frozen comparison of B2/B3/P0/P1/P2 with Q and Q+C. Choose the number of independent calibration/evaluation recordings prospectively for alarm-rate resolution and paired uncertainty, not by recycling windows. A broader assembly claim additionally needs real event annotations on the other objects. No such collection or new campaign was launched. This package is not publication-ready and does not demonstrate the proposed recognition contribution.

### Provisional positioning (not a manuscript)

This exploratory REBOOT study separates causal motion evidence, command-assisted evidence, extra phase supervision, graph filtering and ordinary smoothing under identical recording-level folds. The measured result is a useful negative boundary: better phase coherence does not imply a better recovery-needed alarm. A superficially strong onset-reset evaluation largely disappears when first alarms are counted from recording start. This supports retaining the functioning baseline/replay package and correcting the evidence target before pursuing a stronger method claim. It does not establish novel temporal logic, task graphs, physical recovery improvement or a publishable positive PCRR result.

### Verification, preservation, resources and resume

The independent scorer imports neither detector nor main scorer. It independently joins raw aliases, checks train-only folds/grammar, reconstructs missingness/delay features, recomputes 190 threshold calibrations, first-alarm/boundary/seed outcomes, external alarms and 2,000-resample paired effects. See independent_audit.json for exact counts and hashes. Engineering tests are separate from scientific evidence. The final maintained test/lint/format outcomes and metering are in commands.jsonl; completion_manifest.json binds the final commit and every artifact.

Existing CPU Torch and the earlier PyArrow installation were reused read-only, with new caches and no package/model/video downloads. Known-source housekeeping fetched one immutable official Git tree, found no attributable additional event files, and saved one unsent request draft. No authors were contacted. Initial per-backend two-thread pools incurred spin overlap; remaining workers use passive OpenMP and one-thread BLAS to keep the CPU worker bounded. GPU/paid APIs/simulators/robot executions are zero. Initial bootstrap/editor/tool overhead is unmetered; foreground worker/driver and closing CPU are measured. Final resources.json states wall/CPU, transfers and storage with scope.

Historical report/protocol prefixes, all other maintained historical files, old completion seal and every consumed source file are verified at start/end. The historical lockfile and .gitignore are unchanged. No whole-release inventory or old physical study was repeated. Checkpointed workers use a process lock; resume an **unfinished, unsealed** run with the same worker and `python -m dual_rec.reboot.overnight_experiment --root RUN --stage train` then `--stage predict`. Existing complete fits are reused; completed sealed runs reject writing commands. All authorized analyses are complete, without detached workers. Local commits only; publication is manual.

![alarm_frontier](results/reboot-overnight/20261111T224622Z/figures/alarm_frontier.png)

![phase_comparison](results/reboot-overnight/20261111T224622Z/figures/phase_comparison.png)

![streaming_timeline](results/reboot-overnight/20261111T224622Z/figures/streaming_timeline.png)

Engineering validation: 15 focused tests passed; 261 maintained tests passed and four original environment-gated physics checks skipped. Lint and format checks passed (125 maintained Python files). These counts are not scientific sample sizes.

Verified preseal checkpoint: campaign wall 3508.714s (conservative five-minute startup allowance), measured worker/driver/closing CPU 2394.010s; GPU 0; additional transfers <=1,000,000 bytes; logical artifacts 195,306,405 bytes and storage charge 245,306,405 bytes. Final reporting/archive/seal costs are added in resources.json. All limits passed.


## 2026-11-12: onset specificity and matched-background calibration

Evidence: `results/reboot-onset-specificity/20261112T090003Z`. Reviewed base `c2e24d38b61e2a3d7db422c971342eab8cac4b7e`; analysis registration committed as `ad4572f` before recalculating comparisons. This is exploratory reanalysis and cross-fitting of already exposed data, not untouched confirmation. All 117 canonical recordings, 55 eligible recoveries, 62 cylinder-install expert-source references, original exclusions/folds, seeds and horizons are retained.

### Reproduction and exact score capacity

All 1,638 historical outcome rows reproduced exactly with the original scorer. Training already included pre-onset negatives. The reviewed implementation calibrated only on nominal references; no historical scientific scorer or model defect was found or silently repaired. All 1,506 consumed sealed input files were verified, including the available prior archive and completion manifest with the authorized hashes.

Counts below are individual nonempty A < theta <= B intervals / infeasible intervals / shared-fold hindsight ceiling at alpha .10 under BOTH budgets. A/B retain complete causal persistence history, including streaks crossing onset. Every raw score breakpoint and immediately above ties is checked. These are capacities of the fixed scores and threshold policy, not information limits or deployable calibrated performance.

| Input/model | Feasible / 55 | Infeasible / 55 | Hindsight timely / 55 |
| --- | --- | --- | --- |
| Q/B0 | 54 | 1 | 0 |
| Q/B1 | 19 | 36 | 2 |
| Q/B2 | 46 | 9 | 17 |
| Q/B3 | 25 | 30 | 6 |
| Q/P0 | 25 | 30 | 7 |
| Q/P1 | 20 | 35 | 4 |
| Q/P2 | 25 | 30 | 6 |
| Q/B2R | 50 | 5 | 9 |
| QC/B0 | 54 | 1 | 0 |
| QC/B1 | 21 | 34 | 3 |
| QC/B2 | 50 | 5 | 24 |
| QC/B3 | 30 | 25 | 9 |
| QC/P0 | 30 | 25 | 8 |
| QC/P1 | 41 | 14 | 16 |
| QC/P2 | 31 | 24 | 8 |
| QC/B2R | 52 | 3 | 11 |

The clock B0 has many individual feasible intervals but a zero shared-threshold ceiling: per-recording feasibility alone does not establish event specificity. B2-R's calibrated timely count can exceed its budget-constrained ceiling because its realized evaluation reference alarms violate that ceiling's reference budget; the ceiling does not bound unconstrained counts. Oracle thresholds are stored only under `hindsight_only/` and rejected by the deployment loader.

### Both alarm populations under fixed calibration

C0 fits expert-reference capacities only. C1 uses the maximum of separately calibrated nominal-reference and strictly pre-onset recovery-prefix thresholds. The smallest conservative threshold uses nextafter above the permitted order statistic, retaining ties. No target or evaluation labels choose deployable thresholds. Nominal alarms are not certified physical false positives, and pre-annotation alarms do not prove physical normality. Calibration-fold reference counts are 12–13, valid prefixes 10–11; empirical integer budgets are coarse. B1 has one unavailable sample-41 prefix in each input because of its warmup, explicitly excluded from the valid-prefix denominator; it remains in evaluation. No other prefix is replaced or relabeled.

Primary alpha .10. T/P/R denote timely / premature / reference alarms; recovery denominator 55, reference denominator 62. Delay is median seconds among detections only; misses are shown to prevent conditioning from hiding failures.

| Input/model | C0 T/P/R | C1 T/P/R | C1 late / none | C1 misses | C1 delay s |
| --- | --- | --- | --- | --- | --- |
| Q/B0 | 0/0/0 | 0/0/0 | 0 / 55 | 55 | — |
| Q/B1 | 1/54/10 | 0/7/0 | 7 / 41 | 55 | — |
| Q/B2 | 5/46/16 | 14/6/0 | 30 / 5 | 41 | 3.20 |
| Q/B3 | 1/53/6 | 3/9/0 | 19 / 24 | 52 | 2.30 |
| Q/P0 | 1/54/9 | 2/8/0 | 13 / 32 | 53 | 0.20 |
| Q/P1 | 0/54/4 | 2/6/0 | 1 / 46 | 53 | 1.80 |
| Q/P2 | 1/54/12 | 2/8/0 | 13 / 32 | 53 | 0.20 |
| Q/B2R | 12/0/11 | 12/0/11 | 41 / 2 | 43 | 3.35 |
| QC/B0 | 0/0/0 | 0/0/0 | 0 / 55 | 55 | — |
| QC/B1 | 1/54/11 | 0/7/0 | 7 / 41 | 55 | — |
| QC/B2 | 9/44/8 | 16/16/0 | 23 / 0 | 39 | 1.90 |
| QC/B3 | 3/50/12 | 8/9/0 | 35 / 3 | 47 | 2.80 |
| QC/P0 | 2/50/10 | 5/9/0 | 18 / 23 | 50 | 2.70 |
| QC/P1 | 1/50/10 | 10/8/0 | 18 / 19 | 45 | 2.35 |
| QC/P2 | 2/50/11 | 5/9/0 | 17 / 24 | 50 | 2.70 |
| QC/B2R | 10/0/11 | 10/0/11 | 40 / 5 | 45 | 2.85 |

Fold-specific threshold ranges and realized calibration reference;prefix counts (fold order 0–4), primary alpha:

| Input/model | C0 threshold range | C0 ref;prefix | C1 threshold range | C1 ref;prefix |
| --- | --- | --- | --- | --- |
| Q/B0 | 0.857891–0.874818 | 0/13;0/11, 0/12;0/11, 0/12;0/11, 0/12;0/11, 0/13;0/11 | 0.857891–0.874818 | 0/13;0/11, 0/12;0/11, 0/12;0/11, 0/12;0/11, 0/13;0/11 |
| Q/B1 | 4.58651–11.5412 | 1/13;10/11, 1/12;10/10, 1/12;11/11, 1/12;11/11, 1/13;11/11 | 1645.78–2982.8 | 0/13;1/11, 0/12;1/10, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/B2 | 0.461184–0.865855 | 1/13;10/11, 1/12;8/11, 1/12;8/11, 1/12;9/11, 1/13;11/11 | 0.974699–0.996705 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/B3 | 0.537482–0.563227 | 1/13;10/11, 1/12;11/11, 1/12;11/11, 1/12;10/11, 1/13;11/11 | 0.79423–0.845289 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/P0 | 0.513097–0.527279 | 1/13;10/11, 1/12;11/11, 1/12;11/11, 1/12;11/11, 1/13;11/11 | 0.679684–0.716195 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/P1 | 0.515811–0.569534 | 1/13;10/11, 1/12;11/11, 1/12;11/11, 1/12;11/11, 1/13;11/11 | 0.734841–0.768731 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/P2 | 0.509552–0.523142 | 1/13;11/11, 1/12;11/11, 1/12;11/11, 1/12;11/11, 1/13;11/11 | 0.679897–0.717088 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| Q/B2R | 0.995236–0.998346 | 1/13;0/11, 1/12;0/11, 1/12;0/11, 1/12;0/11, 1/13;0/11 | 0.995236–0.998346 | 1/13;0/11, 1/12;0/11, 1/12;0/11, 1/12;0/11, 1/13;0/11 |
| QC/B0 | 0.857891–0.874818 | 0/13;0/11, 0/12;0/11, 0/12;0/11, 0/12;0/11, 0/13;0/11 | 0.857891–0.874818 | 0/13;0/11, 0/12;0/11, 0/12;0/11, 0/12;0/11, 0/13;0/11 |
| QC/B1 | 3.26359–12.2221 | 1/13;10/11, 1/12;10/10, 1/12;11/11, 1/12;11/11, 1/13;11/11 | 1537.06–2913.63 | 0/13;1/11, 0/12;1/10, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/B2 | 0.43596–0.815166 | 1/13;9/11, 1/12;8/11, 1/12;8/11, 1/12;10/11, 1/13;11/11 | 0.946623–0.996413 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/B3 | 0.594262–0.69547 | 1/13;9/11, 1/12;9/11, 1/12;11/11, 1/12;10/11, 1/13;11/11 | 0.838441–0.868235 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/P0 | 0.567866–0.632063 | 1/13;10/11, 1/12;9/11, 1/12;11/11, 1/12;10/11, 1/13;11/11 | 0.734046–0.763465 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/P1 | 0.589278–0.66331 | 1/13;9/11, 1/12;9/11, 1/12;11/11, 1/12;10/11, 1/13;11/11 | 0.767892–0.804431 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/P2 | 0.565425–0.631401 | 1/13;10/11, 1/12;9/11, 1/12;11/11, 1/12;10/11, 1/13;11/11 | 0.732298–0.763011 | 0/13;1/11, 0/12;1/11, 0/12;1/11, 0/12;1/11, 0/13;1/11 |
| QC/B2R | 0.998388–0.999782 | 1/13;0/11, 1/12;0/11, 1/12;0/11, 1/12;0/11, 1/13;0/11 | 0.998388–0.999782 | 1/13;0/11, 1/12;0/11, 1/12;0/11, 1/12;0/11, 1/13;0/11 |

Q/B2 C1 timely is 14/55 (25.5%; Wilson 95% 15.8–38.3%), premature 6/55 (10.9%), nominal 0/62 (Wilson upper 5.8%). Matched calibration retains event signal here while substantially reducing early alarms, but 41/55 events remain missed. All 55 target windows are observable; no target is removed to improve counts. Reference exposure is 1853.152 seconds per clean model/rule cell. Detailed exposure/censoring, delays and leads, rate intervals and every fold are in summary.json, outcomes.json and fold_counts.json.

All fixed sensitivity cells are reported, without selecting a favorable alpha:

| Input/model | alpha | C0 T/P/R | C1 T/P/R |
| --- | --- | --- | --- |
| Q/B0 | 0.05 | 0/0/0 | 0/0/0 |
| Q/B0 | 0.2 | 0/0/0 | 0/0/0 |
| Q/B1 | 0.05 | 1/54/8 | 0/5/0 |
| Q/B1 | 0.2 | 1/54/11 | 0/13/0 |
| Q/B2 | 0.05 | 7/41/7 | 12/2/0 |
| Q/B2 | 0.2 | 4/47/18 | 14/14/0 |
| Q/B3 | 0.05 | 1/50/3 | 5/4/0 |
| Q/B3 | 0.2 | 1/53/9 | 3/14/0 |
| Q/P0 | 0.05 | 1/54/5 | 2/4/0 |
| Q/P0 | 0.2 | 0/55/21 | 2/15/0 |
| Q/P1 | 0.05 | 1/53/1 | 1/3/0 |
| Q/P1 | 0.2 | 0/54/10 | 2/16/0 |
| Q/P2 | 0.05 | 1/54/3 | 3/4/0 |
| Q/P2 | 0.2 | 1/54/17 | 1/16/0 |
| Q/B2R | 0.05 | 10/0/5 | 10/0/5 |
| Q/B2R | 0.2 | 12/2/19 | 12/2/19 |
| QC/B0 | 0.05 | 0/0/0 | 0/0/0 |
| QC/B0 | 0.2 | 0/0/0 | 0/0/0 |
| QC/B1 | 0.05 | 1/54/6 | 0/5/0 |
| QC/B1 | 0.2 | 1/54/13 | 0/13/0 |
| QC/B2 | 0.05 | 9/41/4 | 14/7/0 |
| QC/B2 | 0.2 | 8/46/17 | 19/20/1 |
| QC/B3 | 0.05 | 3/48/4 | 4/6/0 |
| QC/B3 | 0.2 | 3/50/13 | 9/13/0 |
| QC/P0 | 0.05 | 2/49/2 | 5/4/0 |
| QC/P0 | 0.2 | 3/51/15 | 5/14/0 |
| QC/P1 | 0.05 | 3/47/4 | 6/2/0 |
| QC/P1 | 0.2 | 2/50/14 | 12/11/0 |
| QC/P2 | 0.05 | 2/49/2 | 7/3/0 |
| QC/P2 | 0.2 | 3/50/15 | 5/14/0 |
| QC/B2R | 0.05 | 8/0/7 | 8/0/7 |
| QC/B2R | 0.2 | 13/0/18 | 13/0/18 |

### Paired uncertainty, B2-R and phase filtering

Exactly ten recovery-only B2-R detectors and ten first-second source-role logistic controls were fitted, five folds times two input regimes. No neural fit, hyperparameter search or other model optimization was performed. B2-R retains original windows, training-only equal-recording scaling, clipped features, positive weighting, L2 .01 and optimizer. Only recovery training recordings enter its fit; expert recordings remain in calibration/evaluation. Convergence metadata and training IDs are retained in all 20 checkpoints.

Primary Q/.10 contrasts below are recording-level differences in percentage points, with 2,000 paired role-stratified bootstrap 95% intervals:


All 20 prescribed fits completed; 20 report optimizer convergence. Per-fit objectives, iteration counts and hashes are retained in fit_summary.json.

| Contrast | Timely pp [95%] | Premature pp [95%] | Reference pp [95%] |
| --- | --- | --- | --- |
| B2R/C1-B2/C1 | -3.6 [-16.4, 9.1] | -10.9 [-20.0, -3.6] | 17.7 [8.1, 27.4] |
| P1/C1-P0/C1 | 0.0 [-7.3, 7.3] | -3.6 [-10.9, 3.6] | 0.0 [0.0, 0.0] |
| P1/C1-P2/C1 | 0.0 [-7.3, 7.3] | -3.6 [-10.9, 3.6] | 0.0 [0.0, 0.0] |

B2-R is not a uniform improvement: Q timely is 12 versus B2's 14, fewer premature alarms but more nominal alarms. C1 equals C0 for B2-R at the primary setting because nominal calibration dominates. Its zero premature evaluation rate does not certify safety. Q/P1 has exactly the same pooled timely count as P0/P2, with wide paired intervals. Q+C/P1 has 10 timely versus 5/5: +9.1 percentage points, paired 95% [1.8, 16.4] against either comparator. This is a positive exploratory secondary contrast under C1; all sensitivities remain in paired_effects.json. This secondary command-assisted result does not establish a primary Q benefit. Historical phase accuracy remains unchanged: Q P0/P1/P2 61.01/63.56/62.61%; Q+C 64.98/70.94/67.34%. Improved phase coherence is separate from alarm utility, and the prior negative phase-filter result is preserved.

Paired C1–C0 differences for every model/input/alpha are retained in paired_effects.json, including nonprimary cells. Shared training folds and one collection/object limit uncertainty; recordings, not frames/seeds/aliases, are resampled. Wilson intervals do not remove within-collection dependence. A [0,0] bootstrap interval from identical zero indicators is not evidence of population equivalence. No unadjusted p-value or acceptance probability is used.

### Within-recording and source-context controls

One-second equal-sample windows retain full history; .5-second gaps are a fixed sensitivity, never label correction. The table reports included / 55, target-capacity-greater count, and median mean-score change. Clock contrasts explicitly expose ordinary progress trends. These annotation-delimited comparisons are not deployment success rates.

| Input/model | Gap s | Included | Capacity increases | Median mean change |
| --- | --- | --- | --- | --- |
| Q/B0 | 0 | 55 | 48 | 0.0288 |
| Q/B0 | 0.5 | 55 | 53 | 0.0497 |
| Q/B2 | 0 | 55 | 42 | 0.0429 |
| Q/B2 | 0.5 | 55 | 43 | 0.1137 |
| Q/B3 | 0 | 55 | 34 | 0.0081 |
| Q/B3 | 0.5 | 55 | 39 | 0.0220 |
| Q/P0 | 0 | 55 | 30 | 0.0021 |
| Q/P0 | 0.5 | 55 | 37 | 0.0061 |
| Q/P1 | 0 | 55 | 31 | 0.0008 |
| Q/P1 | 0.5 | 55 | 33 | 0.0040 |
| Q/P2 | 0 | 55 | 30 | 0.0027 |
| Q/P2 | 0.5 | 55 | 37 | 0.0066 |
| QC/B0 | 0 | 55 | 48 | 0.0288 |
| QC/B0 | 0.5 | 55 | 53 | 0.0497 |
| QC/B2 | 0 | 55 | 40 | 0.0475 |
| QC/B2 | 0.5 | 55 | 45 | 0.1458 |
| QC/B3 | 0 | 55 | 35 | 0.0112 |
| QC/B3 | 0.5 | 55 | 37 | 0.0232 |
| QC/P0 | 0 | 55 | 37 | 0.0086 |
| QC/P0 | 0.5 | 55 | 38 | 0.0179 |
| QC/P1 | 0 | 55 | 36 | 0.0118 |
| QC/P1 | 0.5 | 55 | 42 | 0.0203 |
| QC/P2 | 0 | 55 | 37 | 0.0088 |
| QC/P2 | 0.5 | 55 | 39 | 0.0193 |

Source-role features contain only first-second causal Q or Q+C B2 summaries, no role/time/duration/name/phase annotation features. Sample 41's onset at 1s excludes it only here; 54 recoveries plus 62 references remain. Decision threshold is fixed .5. Results:

| Input | AUROC [95%] | Balanced accuracy [95%] |
| --- | --- | --- |
| Q | 0.9818 [0.9459, 1.0000] | 0.9549 [0.9110, 0.9907] |
| QC | 0.9907 [0.9725, 1.0000] | 0.9549 [0.9122, 0.9907] |

Recording contexts are highly distinguishable before the released onset. Initial pose, preparation or style can be legitimate sources of these differences. This diagnostic does not establish fraud, annotation error or a causal confound, and does not rule out later event-specific information. Q/B2's positive within-recording contrast and calibrated detections support some event-associated signal alongside context differences; none identifies physical onset independently.

### Robustness under unchanged thresholds

C1 thresholds are transferred unchanged to saved streams. Primary-alpha T/P/R cells:

| Input/model | Clean | 10% drop | 30% drop | .2s delay | .5s delay |
| --- | --- | --- | --- | --- | --- |
| Q/B0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| Q/B1 | 0/7/0 | 0/7/0 | 0/7/0 | 0/7/0 | 0/7/0 |
| Q/B2 | 14/6/0 | 14/6/0 | 12/9/0 | 14/6/0 | 13/6/0 |
| Q/B3 | 3/9/0 | 3/9/0 | 3/9/0 | 3/9/0 | 3/9/0 |
| Q/P0 | 2/8/0 | 2/8/0 | 2/8/0 | 2/8/0 | 2/8/0 |
| Q/P1 | 2/6/0 | 2/7/0 | 2/7/0 | 2/6/0 | 2/6/0 |
| Q/P2 | 2/8/0 | 2/8/0 | 2/8/0 | 2/8/0 | 2/8/0 |
| Q/B2R | 12/0/11 | 12/0/12 | 12/0/13 | 12/0/11 | 12/0/11 |
| QC/B0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| QC/B1 | 0/7/0 | 0/7/0 | 0/7/0 | 0/7/0 | 0/7/0 |
| QC/B2 | 16/16/0 | 18/14/0 | 17/15/0 | 18/14/0 | 17/14/0 |
| QC/B3 | 8/9/0 | 7/11/0 | 9/9/0 | 8/9/0 | 8/9/0 |
| QC/P0 | 5/9/0 | 6/9/0 | 4/11/0 | 5/9/0 | 4/9/0 |
| QC/P1 | 10/8/0 | 8/9/0 | 8/9/0 | 10/8/0 | 10/8/0 |
| QC/P2 | 5/9/0 | 6/9/0 | 4/11/0 | 5/9/0 | 4/9/0 |
| QC/B2R | 10/0/11 | 11/0/12 | 8/0/13 | 9/0/11 | 7/0/11 |

These are descriptive perturbations of the same recordings, not new samples. A delayed alarm moving into the released target window is not evidence that degraded sensing helps. Q+C uses previously issued native targets and remains an assisted-information regime.

### Streaming, annotation review and independent verification

streaming_parity.json checks the first-hash P1 example in each available C0 review category, deduplicated. C0/C1 risk streams are bitwise identical, first alarms match batch outcomes, and batch/step differences are below 1e-6. Runtime receives only packets and accumulated state; onset/recovery overlays are offline only. Traces show model motion, previous-target residual, phase/emission distributions, predecessor mass, persistence and threshold, not a physical causal explanation. Reproduce either rule with:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=src:results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages \
uv run --no-sync python -m dual_rec.reboot.overnight_replay --root results/reboot-overnight/20261111T224622Z \
  --calibration-root results/reboot-onset-specificity/20261112T090003Z --calibration C1 --alpha .1 \
  --group recording:042d41db25e25b6a7c61d6f6a387097e6247d33d034071a794d354889d8513ee --variant Q --method P1
```

annotation_review.json selects three smallest canonical hashes per available C0 category/model/input: premature infeasible, premature feasible, timely, and late/no-alarm miss (disjoint categories). Empty categories remain empty. Raw annotation bounds and provenance are unchanged; score and full-history capacity traces are in annotation_review_scores.npz. Numeric plots do not physically adjudicate labels, and no annotation was corrected.

The independent analyzer imports neither main detector nor scorer. It directly streams thresholds, independently computes capacities, verifies every shared-threshold breakpoint, calibration masks/IDs/fold separation, all 56,160 outcomes, train-only new scalers and direct logistic predictions, and paired resampling. A supplementary independent check covers all 1,320 within-recording rows and source-role AUROC/uncertainty. Exact check counts/hashes are in independent_audit.json and independent_controls_audit.json. Tests/lint/resource evidence and intentional source changes are sealed at completion.

The original Q/B3 onset-reset 1→51/55 comparison remains invalid optimistic accounting; it is neither adopted nor attributed to REBOOT authors. [Kim et al.](https://arxiv.org/abs/2109.05257) provide related context on inflated anomaly metrics from point adjustment; that is a different operation. Existing FAIL-Detect and Sentinel positioning remains applicable. This continuation adds no theoretical or new-method claim.

### Disposition, preservation and local handoff

Matched calibration improves the evaluated Q/B2 alarm tradeoff but leaves most events missed. Fixed-score capacities vary strongly; neither universal absence of signal nor a solved calibration problem is supported. The source-role control reveals context separability; B2-R trades fewer premature for more reference alarms. Primary Q phase-filter advantage remains unsupported. No physical recovery, intervention efficacy, cross-object failure sensitivity or publication-readiness claim follows.

Local review bundle: `results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz`; its exact SHA-256, final branch/commit, tests, storage/transfer and measured-worker CPU are in completion_manifest.json/resources.json. Raw outputs/logs/checkpoints stay untracked. `.gitignore`, historical lockfiles, old weights/seals and all unrelated files are preserved. The only historical source changes are configurable limits in the existing bounded worker and registered C0/C1 loading in the existing replay interface. Historical documentation prefixes are byte-preserved. No push, credentials, contact, GPU or detached research worker is used.

Resume only an unfinished unsealed run using the existing locked worker and the registered stages in onset_specificity/onset_analysis; fitting reuses checkpoint hashes and refuses a 21st fit. Completed runs reject mutations. Commands and executed source hashes are in commands.jsonl; pre-format executed source snapshots remain under provenance/. All independent fixed stages are complete; no new campaign is authorized by these findings.

![score_feasibility](results/reboot-onset-specificity/20261112T090003Z/figures/score_feasibility.png)

![calibration_tradeoffs](results/reboot-onset-specificity/20261112T090003Z/figures/calibration_tradeoffs.png)

![within_source_diagnostics](results/reboot-onset-specificity/20261112T090003Z/figures/within_source_diagnostics.png)


Engineering validation: 13 focused onset tests; 62 maintained REBOOT tests passed. Maintained Ruff lint and format checks passed. Before report/archive/seal, measured worker/driver CPU was 397.804s and conservative session wall was 2922.357s. Final closing costs and artifact storage are added in resources.json. GPU and paid API use are zero.
