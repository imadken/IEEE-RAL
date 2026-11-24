# RecoverBench recovery transfer campaign: completed Case D audit

**Recommendation: BLOCKED at the engineering gate.** The tested identity-action
library also has **ACTION_COVERAGE_FAILURE** on the selected training scenes.
This is not METHOD_NO_GO for ACRR: ACRR and the comparative selectors were not
activated. No methodological novelty, official leaderboard result, physical
robot validation or publication readiness is established.

Run: `results/recoverbench-transfer/20261111T172759Z/` (RUN). Reviewed base:
`86fcf8e59d526b5b81eb798b5deb379d19d3eae8`. Branch:
`research/affordance-recovery-recoverbench`. The preregistration commit is
`29e27e84cc3644594cf7028cb86923f94df738d2`. The final implementation commit and
resource checkpoint are recorded without a circular self-reference in
`RUN/completion_manifest.json`. Earlier DUAL-REC, LOGIV and SVR conclusions
remain unchanged. This report is an engineering and scientific audit, not a
manuscript.

## 1. Source and dataset versions

RecoverBench source is pinned to
`88f6fedab46dd130a617e058f8d0d05a42c2ea3d`, source tree
`16d7953d2b6cd4c6f13977eccf6dfd0a29dbaf81`, package version 1.2.0. Dataset
`v1.2.0` resolves to immutable
`f2f9cfe9ad2135f40c0b47a70269cc806541b58d`. The three official small archives
were SHA-256 checked against the release:

| Archive | Bytes | SHA-256 |
|---|---:|---|
| eval_data.tar | 26,173,440 | `0c2e732286d623a4f437b55996a78f3e3c0d6260d093c839d2524dd65d2182b0` |
| training_scenes.tar | 99,297,280 | `ddac00ac207f02d6360fb8990ad9c22cc182c0d8b8e88f196859803c80b61740` |
| recovery_mimicgen_generated.tar | 126,136,320 | `9f212d9b4c846578050a46d8cbb0e9c3cb9c880487a5b928c71ed58317fc6268` |

The 8,908,974,080-byte training_data.tar was not downloaded. Only two required
MimicGen seed HDF5 files were added: source/pick_place.hdf5 (92,016,062 bytes)
and core/stack_d0.hdf5 (1,138,107,058 bytes), at immutable seed revision
`33016f8a62c02334f929f2913af8fdd2a8a129e1`. Their LFS hashes, dependency archive
hashes and exact URLs are in `config/recoverbench_release_manifest.json`.

The isolated `RUN/env` uses system Python 3.10.12, MuJoCo 2.3.2 and robosuite
1.4.1, not the historical Python 3.12 environment. Source pins:

| Dependency | Commit | Modification |
|---|---|---|
| robosuite | `c848ca848020d0c4ccdd10c5056bd06f2a195ba2` | Released RecoverBench patch only |
| MimicGen | `72bd767c255545f462e7ccfb2731f2e5d4c1d9bb` | None |
| robosuite-task-zoo | `74eab7f88214c21ca1ae8617c2b2f8d19718a9ed` | Released setup-dependency patch only |

MimicGen reports module 1.0.1 versus setup/package 1.0.0; this discrepancy is
preserved. Patch before/after hashes are retained. The environment installs
physics and audit requirements, not every optional VLA training dependency.
`config/recoverbench_python310.txt` pins installed ordinary packages;
`RUN/environment-freeze.txt` also preserves the actual editable source paths.
Historical `uv.lock`, `pyproject.toml` and simulator installations are unchanged.

## 2. Nearest research and positioning

The release README, evaluation protocol, data format, datasheet, dataset card,
version locks and relevant source were read. The RecoverBench paper itself
could not be read: the official poster links OpenReview `dvg6FAMUK7`, whose PDF
and public API requests returned HTTP 403. No authentication/challenge bypass
was attempted. That missing paper is a positioning limitation, not a claimed
full-paper review. See `RUN/literature/openreview_api_fetch.json` and the failed
primary-paper command. Five other primary PDFs were downloaded, hashed and
their method text inspected; no model weights were downloaded.

| Work | Already addresses | Consequence for this proposal |
|---|---|---|
| [RecoverBench official release](https://github.com/ErrorRecoveryBenchmark/ErrorRecoveryBenchmark/tree/88f6fedab46dd130a617e058f8d0d05a42c2ea3d) | Error scenes, recovery groups/policies; MimicGen object-nearest-neighbor selection (`nn_k3`), object-centric subtask warping and source replay/grasp checks | Retrieval, object-relative transfer and source validation cannot be claimed as new. Full-paper equivalence review remains incomplete. |
| [FLARE, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_FLARE_A_Failure-Aware_Framework_for_Autonomous_Correction_and_Recovery_in_CVPR_2026_paper.pdf) | Retry perturbations/bridging; MLLM-guided object-centric Reset skill construction and online arbitration | Recovery reuse and task-aware skill arbitration are established components. |
| [MAGMA-GEN](https://arxiv.org/abs/2609.20056v1) | Privileged coaching of localized corrections and matched re-execution to validate recovery supervision | Geometric correction and outcome validation are prior work, not an ACRR distinction by themselves. |
| [REACH, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Ke_REACH_Explicit_Recovery_Behavior_for_Diffusion_Policies_CVPR_2026_paper.pdf) | Error representation, retreat/rollback and negative-action prompting for diffusion recovery | Explicit recovery behavior and failure-conditioned corrections are already studied. |
| [RoboRecover](https://arxiv.org/abs/2609.28952v1) | Prefix-replayed failures, scenario filtering, same-state policy evaluation and short correction followed by base-policy resumption | Outcome-based filtering and fair same-state recovery comparisons are not novel. |
| [VLA-FixBench author paper](https://bowen-yan-research.github.io/assets/pdf/vla-fixbench.pdf) | Fault diagnosis, spatiotemporal rollback and spatial correction in FaultEval | Task-aware rollback/correction is prior work. Its human upper reference is not an automated VLM gain. |

The proposed distinction remains an untested, explicitly observable applicability
layer compared with identical state retrieval and learned outcome selection.
This targeted inspection did not establish an exact equivalent of that complete
comparison; it also does not establish novelty. No competing foundation model
was trained or reproduced, and no method-level comparison is claimed.

## 3. Recovery library and transfer semantics

The small archive has 668 recordings: pick_place 223, stack 248, coffee 47,
stack_three 55, threading 7 and three_piece_assembly 88. All 668 contain finite
7D actions/states and T pre-action states for T controls; this alignment is
supported by the generator and is not automatically a defect. Total controls:
247,581. All source-scene references resolve. Every index success entry is
blank: missing outcomes, not synthetic failure/success labels. This subformat
contains no stored success, gripper-state, target-waypoint or orientation field.

The fallback operator is deliberately limited: T(d,s) copies the recorded
normalized OSC_POSE delta/gripper controls to another registered training scene.
It does not perform object-frame warping. Each target is initialized once,
advanced by the official uncounted neutral control and then executed for
min(T,500) controls, stopping at first original task success. There are no
synthetic tail actions, pose assignments during rollout, controller heuristics
or substituted success predicates. Offline forward kinematics and predicate
checks never earn a recovery outcome.

This operator audits one released control interface. Failure under identity
controls does not prove that properly calibrated object-centric transfer or
other recovery operators cannot work. The release's richer MimicGen warping
implementation was inspected, not replaced by an invented adaptation.

## 4. Simulator and source qualification

Startup used one predeclared evaluation fixture per task, three independent
resets and three neutral steps per repetition. State restoration residual and
repeated three-step-state differences were zero; physics time advanced 0.15 s,
action dimension was seven, OSC_POSE used delta controls, and reported versions,
20 Hz control frequency and 0.002 s simulator timestep matched. Rendering,
offscreen rendering and cameras were disabled.

Nevertheless, exact compatibility failed. Official creation silently falls back
from expected PickPlace_D0 to PickPlace. Direct PickPlace_D0 construction raises
`TypeError: PickPlace.__init__() got an unexpected keyword argument 'z_rotation'`
under the pinned release stack. Its inherited constructor does not support the
argument passed by MimicGen. Stack_D0 constructs. No argument stripping,
version substitution or custom simulator patch was used to force a pass.

All 56 source replay rows and all 72 target rows fail original XML fingerprint
verification. Raw XML hashing includes path-sensitive asset references, but
path relocation alone has not been established as the cause. Original scene
model XML is not provided for a complete equivalence proof. Fingerprints were
retained as failures; subsequent execution is explicitly diagnostic.

| Source task, original alignment | Recordings | Source scenes / clean parent groups | First-hit task success | Initially already successful | Newly reached success |
|---|---:|---:|---:|---:|---:|
| pick_place | 12 | 8 / 6 | 0/12 | 0/12 | 0/12 |
| stack | 12 | 9 / 6 | 5/12 | 4/12 | 1/8 initially unsuccessful |

The one-neutral source variant gives the same first-hit counts. Four Stack
drop-at-wrong-place recordings were already solved and remained successful at
counted action 1; they are retained and are not credited as four new recoveries.
The only initially unsolved successful Stack source first reaches the predicate
at action 3. Full source-tape terminal success is 0/12 and 3/12 respectively;
source diagnostics run the full tape to assess trajectory parity. The official
first-hit endpoint is distinct from terminal-state success.

Source lengths are 654–736 controls for PickPlace (median 713.5), 110–137 for
Stack (median 121), all below the registered 1,500 source diagnostic cap.
PickPlace failure therefore also occurs with the full tape, beyond the target
500-action horizon. Reconstructed physical EEF trajectories move for all 24
sampled sources; median maximum execution/reference EEF errors are 0.210282 m
and 0.085069 m respectively. Initialization matches the stored source state;
median source-state versus referenced post-error-scene discrepancy is
2.22e-16 and zero. This is not evidence of successful physical replay parity.
All four repeated source/variant sets (three resets each) have exactly zero
maximum numeric trace-state difference.

The registered GO required exact compatibility and at least 80% reliable replay
per task, followed by at least 20% target-scene coverage. Both task replay
thresholds and exact compatibility fail. The full selector pilot is blocked.

## 5. Frozen scope and actual phase completion

Coverage-only selection fixed grasp_wrong_pose (group A), drop_at_wrong_place
(B), trajectory_regression (E), tasks pick_place/stack and released D0/D1.
The first two archive members per task/category/degree gave 24 source tapes;
both source variants plus registered repetitions gave 56 rows. Exact membership
is in `config/recoverbench_transfer_20261111.json` and the immutable registration
whose SHA-256 is `74c121bee6c653293402f31910cf713231314f19c53dab62205c068fd431f178`.

After the gate failed, the fallback was frozen before its execution: first two
eligible lexicographic training target scenes per task/category/degree, excluding
source scene IDs and enforcing distinct clean parent trajectories within each
task/category. This gives 24 target scenes, four per task/category, not the
qualified pilot target of 12 independent scenes per task/category. First three
frozen source tapes per task/category give 72 attempts. These tapes represent
only two distinct source scenes for every PickPlace category and Stack
drop_at_wrong_place, three for the other Stack categories. They must not be
described as three independent recovery strategies. Fallback registration hash:
`66865d598e79f08dfbcc2c7767f5a2a94b376132e8b6d7a29f72cbb19b8d4d2d`.

| Phase | Actual completion |
|---|---|
| 1 | Pinned sources/data, isolated installation, startup and fixed compatibility diagnostics completed; qualification failed. |
| 2 | Source replay and candidate-interface qualification completed; failed. |
| 3 | Conditional protocol and source membership committed before evaluation; fallback targets/rule frozen before execution. Comparative feature/constraint/model tuning never activated. |
| 4–5 | B1/B2/B3 and ACRR implementation not activated because engineering GO failed. |
| 6 | Comparative development experiments blocked; no trained selector or method estimate. |
| 7 | Authorized Case D training-only release-interface fallback completed, including all 72 fixed transfers. Coffee and held-out confirmation not activated. |
| 8 | Independent arithmetic and original-predicate audits, regressions, integrity verification and local evidence sealing completed. |

## 6. All executed recovery outcomes

Every attempt, including fingerprint-invalid cases, remains in the raw ledgers.
No failed source or target was exchanged for a favorable replacement.

| Target task | Candidate attempts with first-hit success | Distinct targets with any tested success | Clean target parent groups | Qualified fingerprint rows |
|---|---:|---:|---:|---:|
| pick_place | 0/36 | 0/12 | 7 | 0/36 |
| stack | 2/36 | 2/12 | 11 | 0/36 |
| Total | 2/72 | 2/24 | 18 | 0/72 |

Every target is initially unsuccessful. All three attempts for each target start
from the exact same bitwise post-neutral simulator state. Best observed coverage
among the three fixed tapes is 8.33% overall, 16.67% Stack, zero PickPlace,
below the registered 20% screen. This is conditional diagnostic coverage,
not an official benchmark recovery score. Official Normal SR and six-task,
unweighted-mean RSR were not established.

Two positive diagnostic transfers are retained:

| Stack training target | Source tape basename | Source/target degree | First success |
|---|---|---|---:|
| `v5_train_backfill_grasp_wrong_pose_D0_0021_02b38df65b99` | `mg_v5_train_grasp_wrong_pose_D1_000_10ea9ba8_001.npz` | D1 → D0 | 99 |
| `v5_train_backfill_grasp_wrong_pose_D1_0021_03bacf2d0781` | `mg_v5_train_grasp_wrong_pose_D0_001_f0922b87_000.npz` | D0 → D1 | 119 |

These two source tapes fail their own-source execution. Thus a hypothetical
blanket self-replay-success filter would discard some useful diagnostic
cross-transfers. This is not an observed ACRR false-rejection rate; no ACRR rule
was implemented. The positive cases do not waive compatibility failures.

Source replay used 23,182 counted controls; targets used 22,386, total 45,568.
The 28 source neutral controls, 72 target neutrals and 18 startup controls add
118 uncounted diagnostic controls, for 45,686 explicit rollout controls overall.
Offline state forwarding/predicate checks are not additional control recoveries.

## 7. Strong baselines and applicability analysis

B0–B5 comparative outcomes are **N/A**, not zero. B1 labels are used only to
register cohorts, not as a deployed label-free selector. B2 and B3 were not
fitted; B4 was not implemented. The best-observed-three coverage above is an
offline coverage diagnostic, not a qualified B5 comparison against other methods.
No released large recovery policy was downloaded or trained.

Hard/soft applicability acceptance, incorrect acceptance, false rejection,
abstention, fallback frequency, applicability precision/recall and selector
runtime are **N/A**. A success-versus-rejection frontier cannot be measured
without a qualified selector/rejection rule. It is not replaced by fabricated
zero rejection or perfect abstention. The executed action-prefix coverage is
1/24 targets by action 100, 2/24 by 200 and 2/24 by 500; it is not a rejection
frontier and adds no synthetic tail after source controls end.

## 8. Paired statistics and uncertainty

`scripts/recoverbench_analysis.py` recomputes summaries from the raw records.
Repeated candidate attempts are not independent scenes: source sample sizes are
8/9 scenes, six clean parents per task; target sizes are 12 scenes per task,
7/11 clean parents. Same-task/category parents can recur across severity cells.

The paired one-neutral-minus-original first-hit difference is zero for all 24
source tapes; 2,000 whole-parent bootstrap resamples (seed 20261111) give
descriptive percentile intervals [0,0] in both tasks. This reflects exact sample
agreement, not proof of population equivalence or successful replay parity.
The conditional Stack best-of-three scene coverage estimate is 16.67%, with
parent-cluster percentile interval [0%,41.67%]; PickPlace's all-zero observed
sample produces a degenerate [0,0] bootstrap interval. Such a degenerate interval
does not rule out unobserved successes. Fixed scene selection, few clusters and
unresolved environment mismatch preclude a calibrated benchmark efficacy claim.
No paired B4–B2/B3 effect, confidence interval or significance test exists.

## 9. Per-task, per-error and severity diagnostics

| Task / error | Own-source first-hit successes / 4 tapes | Initially successful sources | Target successes / 12 attempts | Targets covered / 4 |
|---|---:|---:|---:|---:|
| pick_place / grasp_wrong_pose | 0 | 0 | 0 | 0 |
| pick_place / drop_at_wrong_place | 0 | 0 | 0 | 0 |
| pick_place / trajectory_regression | 0 | 0 | 0 | 0 |
| stack / grasp_wrong_pose | 0 | 0 | 2 | 2 |
| stack / drop_at_wrong_place | 4 | 4 | 0 | 0 |
| stack / trajectory_regression | 1 | 0 | 0 | 0 |

PickPlace D0 and D1 each have zero successes in 18 transfers to six scenes.
Stack D0 and D1 each have one success in 18 transfers to six scenes. Stack
source first-hit counts are 3/6 D0 and 2/6 D1; two sources in each degree are
initially solved. These are different, small scene cohorts, not paired severity
interventions or evidence of D0/D1 invariance. Both positive target transfers
cross degree. Held-out scene or task generalization and coffee remain untested.
All cell counts, groups and conditional intervals are in `RUN/analysis.json`.

The source-to-target initial EEF displacement spans 0.020435–0.554871 m over
the 72 pairs. This is a privileged physical diagnostic, not an object-relative
transfer feature or learned predictor. Maximum recorded target contact
penetration is 0.019486 m PickPlace and 0.007802 m Stack. Counts/penetrations
are contact diagnostics, not verified violations of a declared hard constraint,
collision safety certificates or a causal explanation of the success difference.

## 10. Negative evidence and engineering blockers

All 668 stored EEF trajectories are constant despite moving simulator states.
Physical forward kinematics on all 24 sampled source recordings is nonconstant.
The generator `error_benchmark/scripts/mimicgen/3c_generate_from_error_scene.py`
sets state and forwards the simulator, then reads cached `controller.ee_pos`
without updating the controller. The numerical discrepancy corroborates this
cache defect. Stored EEF fields are unsuitable for the proposed NN features or
waypoint transfer without independently justified reconstruction. No such field
repair was used to improve an execution outcome.

Flat snapshots also do not by themselves certify controller/gripper internal
memory parity. We did not tune restoration or inject controller-memory fixes.
The direct PickPlace_D0 constructor error, factory fallback, fingerprint mismatch,
low replay fidelity, missing outcome labels and correlated recordings jointly
prevent scientific qualification. Determinism and finite 7D controls alone do
not resolve these blockers. These findings concern the pinned small-release
interface, not every RecoverBench data format or the benchmark as a whole.

## 11. Independent numerical, split and leakage audits

The independent trace auditor imports neither the executor nor a selector. It
checks input/trace hashes, original control bytes and order, first-hit accounting,
finite states, 0.05 s control-time increments, caps and target-state pairing:
56 source rows / 23,182 controls and 72 target rows / 22,386 controls pass with
zero mismatches. A separate implementation loads the original simulator API
directly and independently recomputes `_check_success()` at initial, terminal
and first-success snapshots: 122 source and 146 target checks, zero mismatches.
This validates recorded predicate events at those snapshots, not all continuous
physics or model equivalence. Independent means separately implemented checks;
no separate human or agent reviewer is claimed.

Blind task/subtype/exact-state hashing audited 5,038 training and 1,360 evaluation
scenes: no shared IDs or task/subtype state hashes. Only the two registered
startup evaluation fixtures were opened for execution, and they are excluded
from any future confirmation. No evaluation outcome/features were used for
fitting or selection; no method was fitted. Source/target scene IDs are disjoint,
but parent correlation remains explicitly grouped. No taxonomy/future outcome
was used as a runtime selection feature. The oracle-leakage and rejected-candidate
checks for an implemented ACRR remain N/A, not silently passed.

The originally executed source versions were archived in
`RUN/provenance/executed_sources_before_hygiene.json` before import/logging/input
validation cleanup. Their hashes match execution journal entries. Cleanup does
not change controls or scoring; full physics was not rerun solely for formatting.
Final arithmetic/predicate audits remain attached to the actual executed traces.

## 12. Tests and preservation

The maintained repository test suite passes **201 tests**, including new action/state contract,
path validation, trace tampering, paired-state mismatch, cluster-resampling and
seal-tampering regressions. Final counts and exact commands are retained in
`RUN/maintained-regression-final.log` and `RUN/commands.jsonl`. The isolated
Python 3.10 replay/interface/analysis subset passes **19 tests**. Four upstream core,
success-criterion, step-budget and determinism test files pass **59 tests**;
this is not a claim that optional VLA/model tests ran. Ruff and formatting pass
for maintained `src scripts tests`, excluding downloaded upstream repositories.
An early lint failure was fixed and retained in the command history.

Finalization verifies all 1,015 files in the expanded historical inventory plus
the original captured inventory, all input archive/seed hashes, registration
hashes, actual executed-source snapshots and audit completion. Historical cloud
evidence remains byte-for-byte unchanged. `.gitignore` is unchanged, SHA-256
`253c45f9042946238de5798fd51803137b2e15b6bdb88f01d635ecc5bca2b31e`.
Only a local `.git/info/exclude` entry hides this campaign's raw evidence. No
generated logs, raw outcomes, downloaded data, environment, PDFs or plots enter
the commits. No GitHub push or authentication operation was attempted.

## 13. Resource accounting and stop boundary

The campaign began 11 November 2026 at 18:27:59 CET (17:27:59 UTC). Limits:
eight wall hours, twelve measured CPU core-hours, four GPU wall-hours if needed,
twelve GB new artifacts. The two substantive physics workers consumed
748.474799 / 676.367817 wall seconds and 748.123912 / 676.171777 measured CPU
seconds respectively. No detached scientific worker remains; unused resources
do not authorize another experiment after this Case D boundary.

`RUN/resources.json` and `completion_manifest.json` contain the final elapsed
wall time, summed command CPU, finalizer CPU, exact logical and deduplicated
inode bytes, worker check and bounds. At analysis closure measured command CPU
was approximately 0.44 core-hours, with 3.85 GB logical / 3.30 GB unique-inode
run data/environment/cache/assets before the final manifest. No GPU rendering/model work or paid API
calls occurred. Original environment and historical lockfile were not changed.

Early instrumentation measured child CPU; later instrumentation also meters
the single-thread driver. To avoid pretending this is whole-machine accounting,
the finalizer additionally charges each earlier driver its entire worker wall
time as a conservative CPU ceiling. Interactive tool/editor/bootstrap and
unrelated host CPU were not metered. Evidence hashing/seal and final read-only
verification add small closing overhead, explicitly scoped in the manifest.
All recorded command/driver bounds and artifact counts remain well below limits.
These are bounded-worker measurements, not a host-wide exact CPU utilization log.
`RUN/resource_scope.json` additionally charges full local Git metadata, relevant
repository caches, the temporary uv cache and maintained campaign files outside
RUN, including pre-existing bytes, as a conservative storage allowance. This
adds less than 0.04 GB; the combined storage bound is below twelve GB.

## 14. Reproduction and evidence locations

Public input hashes/URLs and pins are in
`config/recoverbench_release_manifest.json`; membership and thresholds are in
`config/recoverbench_transfer_20261111.json`. Set RUN to a fresh unsealed output
directory for new execution; do not overwrite this sealed run. Create the
isolated environment with `uv venv --python /usr/bin/python3.10 "$RUN/env"`, then
`uv pip install --python "$RUN/env/bin/python" -r config/recoverbench_python310.txt`.
Download/extract the pinned source/dependency archives and two seed HDF5 files
using manifest URLs; verify every hash. Apply only the two released patches
(`patch -p1 --dry-run`, then `patch -p1`) to their respective pinned trees.
Install the three trees with `uv pip install --python "$RUN/env/bin/python"
--no-deps -e <tree>`. The exact historical preparation, class probe and download
scripts are retained in `RUN/provenance/`; patch hashes are in the compact
manifest. Fresh acquisition remains dependent on those public services.

The exact small-data command, after extracting UP to the pinned source tree, is:

```sh
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync python "$UP/scripts/download_data.py" "$RUN/data" \
  --base-url https://huggingface.co/datasets/ErrorRecovery/ErrorRecoveryBenchmark/resolve/f2f9cfe9ad2135f40c0b47a70269cc806541b58d \
  --archives eval_data.tar training_scenes.tar recovery_mimicgen_generated.tar
```

The local registrations preserve the exact metadata-based source selection and
fallback target/pair list; compact config permits reconstructing membership.
Their hashes must match before reproducing the historical execution. After
preparation, use these bounded foreground commands (each executor creates a new
output directory; source and target run directories must not already exist):

```sh
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src MUJOCO_GL=egl NUMBA_NUM_THREADS=1
uv run --no-project --python "$RUN/env/bin/python" python -m dual_rec.recoverbench.replay --root "$RUN" --output "$RUN/source-replay"
uv run --no-project --python "$RUN/env/bin/python" python -m dual_rec.recoverbench.transfer_audit --root "$RUN" --output "$RUN/transfer-audit"
uv run --no-sync python scripts/recoverbench_audit.py --root "$RUN" --split source-replay
uv run --no-sync python scripts/recoverbench_audit.py --root "$RUN" --split transfer-audit
uv run --no-project --python "$RUN/env/bin/python" python scripts/recoverbench_physics_audit.py --root "$RUN" --split source-replay
uv run --no-project --python "$RUN/env/bin/python" python scripts/recoverbench_physics_audit.py --root "$RUN" --split transfer-audit
uv run --no-sync python scripts/recoverbench_analysis.py --root "$RUN"
uv run --no-sync pytest -q tests
uv run --no-sync ruff check src scripts tests
uv run --no-sync ruff format --check src scripts tests
```

During this campaign every substantive worker was wrapped by
`scripts/recoverbench_command.py --root RUN --name NAME --timeout SECONDS -- ...`;
the exact arguments, UTC timestamps, source hashes, exits and CPU/wall costs are
in `RUN/commands.jsonl`. The isolated environment does not install this root
project, whose Python constraint is 3.12; PYTHONPATH provides only our source.

| Local evidence | Meaning |
|---|---|
| `RUN/startup_probe.json`, `strict_factory_probe.json`, `engineering_gate.json` | Compatibility failures and frozen gate decision |
| `RUN/source-replay/outcomes.jsonl`, `traces/` | All 56 actual source executions |
| `RUN/transfer-audit/outcomes.jsonl`, `traces/` | All 72 actual target executions |
| `RUN/release_interface_audit.json` | All 668 array records and blind train/eval split audit |
| `RUN/analysis.json` | Recomputed counts, grouped intervals, geometry shifts and retained successes |
| `RUN/source-replay/audit-final.json`, `physics_audit.json` | Independent source arithmetic/predicate checks |
| `RUN/transfer-audit/audit.json`, `physics_audit.json` | Independent target arithmetic/predicate checks |
| `RUN/upstream/`, `data/`, `environment-freeze.txt` | Exact pinned inputs, patches and isolated stack |
| `RUN/literature/`, `provenance/` | Primary PDFs/access failures and actually executed source versions |
| `RUN/resources.json`, `completion_manifest.json` | Resource checkpoint, local commit and final SHA-256 evidence seal |

Source outcome ledger SHA-256:
`b2c945b25c9820b745d3b3b7ecf4fa6d88b8461af23debdefa08221955f39f66`.
Target outcome ledger SHA-256:
`bf2923460fefafef7ccda7812d8aa1e746a97c4d4ff4e97a8ab4d8da8be444de`.
Raw evidence stays local and is necessary to independently inspect these hashes;
publishing the compact branch alone does not distribute the full evidence set.

## 15. Scientific disposition

The source-library engineering GO is rejected for this pinned execution. Case D
is complete: compatibility, release-interface and bounded identity-transfer
limits have been independently audited. The two Stack transfers establish only
that a few raw controls reach the original predicate in the unqualified local
environment. H1/RQ1 receive conditional diagnostic examples, not a qualified
population result. RQ2 taxonomy sufficiency, H2/RQ3 applicability benefit,
H3/RQ4 generalization and H4 physical-invalidity mechanism remain untested.
They are not statistically rejected or supported by missing comparisons.

The principal researcher should review the class/constructor conflict, XML
equivalence, source replay and EEF cache issue before authorizing a qualified
ACRR experiment. No additional research project, full campaign or manuscript
was started. The branch is suitable for manual publication as a bounded
negative engineering audit, subject to that scientific review.

## 16. Supervised interface qualification rescue — 11 November 2026

This section records the subsequent supervised contract; sections 1–15 and the
previous sealed evidence are retained. Reviewed commit:
`960ec091e1ff16d29fa89d5bf20c63847050886a`. New branch:
`research/recoverbench-interface-qualification`. Evidence root:
`results/recoverbench-qualification-rescue/20261111T195432Z/` (RESCUE).
The new preregistration is committed before physical checks at `4d5c15a`;
membership/config SHA-256 is
`4c0f76578e0df4ae81ec98248dec6f8b3a59cfcf0ef064394b02b3f3160c31f7`.
The final commit is recorded in `RESCUE/completion_manifest.json`.

**Decision: INCONCLUSIVE, with BENCHMARK_COMPATIBILITY_BLOCKED and
SOURCE_GENERATION_BLOCKED.** Some raw controls execute successfully, but no
qualified official generator/candidate library has been established. Stage D
was not activated. This is not METHOD_NO_GO, an ACRR result or a benchmark RSR.

### 16.1 Scope, inputs and completed stages

The exact RecoverBench, dataset, MimicGen, robosuite and task-zoo revisions and
released patches remain those in section 1. No package, asset, vendored source,
historical lockfile or expected fingerprint was changed. The existing Python
3.10 environment and verified downloads are reused through local input-directory
symlinks; no additional dataset archive or model was downloaded.

Stage A constructor/model diagnosis and Stage B source/controller/FK audits
completed. Stage C completed its required dependency preflight and stopped at
the contract's explicit missing-prepared-source boundary; generation was not
performed. The eight frozen generation scenes were not replaced. Stage D and
its comparative/qualification runs were not authorized by the resulting gate.
Independent outcome, physics, preservation, regression and resource checks
completed. No evaluation scene was opened for new simulator execution or method
selection in this rescue, and no research job remains running at closure.

The exact source and scene memberships are in
`config/recoverbench_qualification_20261111.json`. Six source tapes per task were
selected as the first lexicographic member of each already fixed category/degree
cell, independent of earlier outcomes: six distinct source scenes and four clean
parent trajectories per task. The eight prospective Stack generation scenes
cover all six category/degree cells plus two lexicographic additions; they have
six clean parents. Their scene IDs are disjoint from the source-audit IDs, but
some clean parents overlap. This is engineering qualification, not a disjoint
training/confirmation split for a fitted selector.

### 16.2 Environment constructor identity and adaptation

The six constructor questions are resolved as follows:

1. The released `error_benchmark/scripts/utils/script_utils.py:create_env`
   reads PickPlace_D0 from the seed HDF5 metadata and calls `robosuite.make`.
2. Registration resolves to pinned MimicGen's `PickPlace_D0.__init__`, which
   calls the pinned robosuite `PickPlace.__init__` superclass.
3. MimicGen itself adds `z_rotation=(0, pi/2)`; it is not present in the seed
   kwargs used here. The superclass has no such constructor argument.
4. The class is registered, but no working supported D0 constructor path was
   found in this pinned pair or its released patch. The exact original TypeError
   and full call sequence remain in `RESCUE/identity.json` and its command log.
5. The factory catches **any** constructor exception, then tries PickPlace.
   Its comment describes fallback for unregistered classes, but the code also
   hides this registered-class constructor failure. Base PickPlace samples full
   object yaw, whereas D0's declared intent restricts yaw to 0–90 degrees.
   This changes reset-distribution semantics; matching state dimensions alone
   does not establish benchmark identity after injection.
6. Seed metadata specifies Sawyer/OSC_POSE for PickPlace_D0 and Panda/OSC_POSE
   for Stack_D0. Actual robot/controller conventions match those channels;
   PickPlace's class does not match. Stack_D0 constructs as registered. Both
   still fail the original XML fingerprint check.

A separate local `QualificationPickPlaceYawAdapter` calls the base implementation
and changes only `CollisionObjectSampler.rotation` to (0, pi/2). This preserves
the documented yaw intent without deleting an unsupported argument in vendored
code. Construction and sampler bounds are tested. It remains explicitly
**adapted**, is not substituted into the official factory and is not used for
any source recovery rollout. Its compiled comparison with the base differs
only in a visual site-color field in this diagnostic. This does not restore an
official class/fingerprint contract. The original D0 failure is preserved.

### 16.3 XML, compiled-model and physical-equivalence obligations

`RESCUE/identity/` retains factory XML, original seed XML, source-supported path
relocation of seed XML, and compressed compiled numeric parameter snapshots.
`identity.json` records literal expected/actual fingerprints, actual classes,
factory kwargs, robot/gripper names, controller gains/scales, body/joint/geometry/
actuator/site names, version and time-step settings, and asset content hashes.
Path canonicalization removes only known package-directory prefixes and retains
physical attributes; it does not manufacture the expected fingerprint.

Compiled seed-reference and factory models have matching named identities for
both tasks. They nevertheless differ in 15 retained numeric fields per task.
Large mass differences are specifically the **world-welded table/bins**:

| Body | Factory mass | Seed-reference mass | Welded to world |
|---|---:|---:|---|
| Stack table | 32.000000 | 70.086836 | Yes |
| PickPlace bin1 | 11.680000 | 24.365310 | Yes |
| PickPlace bin2 | 13.480000 | 27.965310 | Yes |

Those fixed-body masses are not evidence of a changed moving-object mass or the
cause of replay failure. Other differences include small serialized numeric
precision changes (maximum armature discrepancy 3.333333e-6), derived inertia
fields and visual site sizes. Contact friction, collision masks, actuator gains
and biases agree between these two references. See
`RESCUE/compiled_model_detail.json` and the full compiled snapshots, which retain
the differences rather than hiding them behind a chosen tolerance.

The original **failure-scene** XML/compiled parameter snapshot is not supplied;
seed clean-demo XML is available but its SHA-1 is not the recorded scene hash.
Consequently, source model binding, all dynamic/contact equivalence and exact
controller-initialization fidelity cannot be certified. Canonical XML differences
are not solely path text; nor do these reference differences prove a changed
failure-scene dynamics model. Both original strict fingerprint checks remain
failed, so the alternative references do not qualify an official benchmark run.

### 16.4 Source timing, controller memory and actual rollouts

The exact generator is
`error_benchmark/scripts/augmentation/3c_generate_from_error_scene.py` (the older
section's `scripts/mimicgen/...` path was an attribution error; the evidence and
source file inspected are retained). It resets normally, injects the post-error
state directly with `sim.set_state_from_flattened`/`sim.forward`, then calls the
pinned `DataGenerator.generate`. The latter selects source subtasks, applies
object-relative pose warping and interpolation, converts each waypoint into a
current-state normalized pose delta and executes it. It does not transplant an
unchanged action tape to another scene.

Pinned `WaypointTrajectory.execute` saves each state **before** executing its
corresponding action. The sampled records have T states and T actions, at 0.05 s
control intervals. The target evaluator's neutral action belongs to its initial
observation procedure, not this recorded source format; neither source condition
in this rescue inserts it. Controls have six normalized OSC pose components
(1 maps to 0.05 m / 0.5 rad) plus the gripper command. Positive gripper commands
close, negative commands open; the gripper's integrated `current_action` is not
contained in a flat time/qpos/qvel state.

The actual released source-validation checker restores via
`EnvWrapper.set_sim_state_flat`, which additionally force-updates controller EEF
caches and resets goal position/orientation. Raw generator-style injection does
not do those cache/goal updates. The checker also shares an environment across
source calls, while the frozen raw condition constructs and resets a fresh
environment per tape. These change multiple initialization details together;
the experiment is not a one-factor causal ablation of controller memory.
OSC means operational-space control; no separate oscillator was introduced.

A derived HDF5 input preserves the selected NPZ action/state arrays byte for
byte and copies original seed env_args solely to invoke the actual source
checker. It contains no invented datagen_info and is **not** a DataGenerator
prepared source. Every before/after state, EEF rotation/position, gripper qpos/
memory, controller caches/goals and contact record is saved in the 24 traces.

| Task / execution condition | First-hit successes | Initially successful | Newly reached success | Full-tape terminal success |
|---|---:|---:|---:|---:|
| Stack / released source checker | 2/6 | 2/6 | 0/4 initially unsolved | 2/6 |
| Stack / fresh raw injection and controls | 5/6 | 2/6 | 3/4 initially unsolved | 4/6 |
| PickPlace / released source checker | 0/6 | 0/6 | 0/6 | 0/6 |
| PickPlace / fresh raw injection and controls | 1/6 | 0/6 | 1/6 | 1/6 |

All 24 rollouts executed the full recorded tapes: **9,862 controls**, with no
neutral action or intermediate state assignment during a counted rollout.
All diverge from the recorded pre-action physical state by the first saved
post-action comparison (after action 1, registered 1e-8 coordinate threshold).
Initial differences are at most 2.220446e-16, consistent with normalization
roundoff. Controller/gripper state was not fully recorded in the released tapes,
so exact original memory reconstruction is not established.

Three initially unsolved raw Stack tapes reach success at actions 110, 119 and
133; the two initially solved Stack tapes first satisfy the counted predicate at
action 1. PickPlace's sole raw success occurs at **714**, beyond the target
500-action budget; it cannot qualify a benchmark recovery. Per-error first-hit
counts across D0/D1 are: Stack grasp 0→2, drop 2→2 (both initially solved),
regression 0→1; PickPlace grasp/drop 0→0 and regression 0→1. Arrows denote
checker→raw workflow, not ACRR improvement.

Paired raw-minus-checker first-hit differences are +50 percentage points for
Stack and +16.67 for PickPlace. Whole-clean-parent bootstrap intervals (2,000
resamples, seed 20261111; four parents/task) are [0,75] and [0,60] percentage
points. These wide, conditional diagnostic intervals include zero. Six tapes
are not six independent parent trajectories, and these are neither official RSR
intervals nor evidence that a particular cache fix improves a recovery policy.

### 16.5 Independent EEF reconstruction and missing generation inputs

For all 12 sampled tapes, **4,931 saved states** were independently reconstructed
in separate native MuJoCo data, without overwriting a counted rollout. World
site positions/rotations agree with parent-body plus local-site transforms and
the simulator wrapper; maximum observed discrepancy is zero at stored precision.
A separately implemented audit reproduces every derived EEF position/rotation.
All 12 cached controller/stored EEF series remain constant under state forwards,
while physical kinematics move. Maximum stored-versus-reconstructed displacement
per tape ranges from 0.153081 to 0.771274 m.

Separate `RESCUE/derived/source-*-kinematics.npz` files contain state and kinematic
arrays only, with raw-source/output hashes in `derived/manifest.json`, executed
code/reference-model hashes in `derived/provenance.json`, and explicit local-model
scope. Taxonomy and source IDs are separate provenance, never a deployed feature
array. This repairs feature extraction for the local model; it does **not**
repair stored controls or establish the original failure-scene model identity.

Stage C's exact preflight blocker is recorded in `generation_preflight.json`:

- `data/mimicgen_prepared/stack_d0_prepared.hdf5`, required by the released
  generator, is absent from the acquired source/data layouts.
- The acquired raw Stack seed has **0/1,000** demos with datagen_info; PickPlace
  has **0/10**. Missing prepared fields include EEF/target/object poses, gripper
  actions, subtask termination signals and interface attributes.
- Importing the actual pinned DataGenerator fails first with missing `gdown`.
  `robomimic` and `torch` are also absent from the reused physics-only environment.
- The official `mimicgen/scripts/prepare_src_dataset.py` preparation interface was
  inspected. It was not replaced by synthetic labels, guessed waypoints or the
  checker-only HDF5 conversion. The contract explicitly directs stopping Stage C
  when prepared files/interfaces are unavailable; no environment modification or
  full recovery-corpus download was used to bypass that boundary.

Generation attempts: **0**; independently executed generated candidates: **0**.
These are missing/unattempted outcomes, not 0/8 failures or a measured generation
success rate. Four-of-eight scene coverage and two distinct qualified generated
recoveries are not established. The source checker/raw-tape results above are
not substituted for this missing generator qualification.

### 16.6 Independent audits, errors and preservation

The numerical auditor imports no executor. It checks literal action bytes,
source alignment, finite states, 0.05 s steps, continuity between actions,
first/terminal success, input/trace hashes, scene separation and derived-array
fields. Final result: **PASS**, 24 rows / 9,862 controls, zero mismatches. A second
direct-simulator implementation independently verifies **56 predicate snapshots**
and all 4,931 feature positions/rotations: **PASS**, zero discrepancies. Agreement
in these local-model checks does not waive model-identity uncertainty.

An initial exact-equality initialization check flagged ten machine-roundoff
residuals, all <=2.220446e-16. The failed audit and residual table are retained.
The checker now retains the residual and uses 1e-12 initialization tolerance,
well below the frozen 1e-8 trajectory-divergence threshold; a regression covers
this case. No physical outcome, candidate, action, task predicate or divergence
threshold changed. The actually executed prior auditor/driver source versions
are archived and matched to their recorded hashes.

An initial isolated test failed because the host budget-driver dependency
`psutil` is absent from the frozen physics environment. That test is validated
in the root environment and explicitly skipped in isolated runs; no package was
installed into the sealed environment. A separate upstream test initially failed
because its expected `shared/mimicgen_workspace` layout was absent. A **separate
254-file byte-identical source copy** plus directory symlinks restores the
documented dependency layout for those tests, with zero source-code patches.
All 62 selected upstream tests then pass. The copy is for tests, not an adapted
physics result or substitute prepared generator source.

That first upstream invocation also wrote incidental pytest cache entries inside
the old source directory. The changed cache was archived locally; only cache
bytes whose reconstructed SHA-256 exactly matched the previous seal were
restored, and the newly created failure-cache file was archived then removed.
`RESCUE/cache_incident.json` records the incident. Subsequent pytest/TMPDIR/cache
output is redirected into RESCUE. Final verification checks every old sealed
file, absence of added files there, all 1,015 earlier historical files and all
680 reviewed tracked files; only append-only additions to these two cumulative
documents are allowed. This explicitly records the correction rather than
claiming the incidental write never occurred.

Constructor identity, sampler bounds, action scaling, controller refresh,
kinematics, original success predicate, XML/compiled comparison, T/action timing,
source/target separation, rollout continuity, qualification false acceptance,
budget enforcement, append-only preservation and sealed-run rejection have
regressions. The maintained suite passes **212 tests**, with four pinned-stack
physics tests skipped in the root environment; the isolated suite passes
**12 tests**, with the host-only budget test explicitly skipped. Those four
physics tests execute in the isolated suite. Exact outputs are in
`rescue-maintained-regression-final.log` / `rescue-isolated-regressions-final.log`.
Ruff and formatting pass for maintained source/tests/scripts. Tests for ACRR's
actual false rejection/acceptance or deployable feature leakage are **N/A**:
there is no deployed selector. Array/provenance and gate checks are not relabeled
as tests of an unimplemented method.

### 16.7 Resources and reproduction

The rescue began at **20:54:32 CET / 19:54:32 UTC**. New ceilings are five aggregate
worker wall hours, six measured CPU core-hours, one GPU wall-hour if necessary,
four GB new files excluding identical reused inputs. Main source diagnostics:
339.766179 worker wall seconds / 346.817918 measured worker-plus-driver CPU
seconds. Every substantive physics and test worker is bounded, foreground and
logged with source hashes and exits. There was no GPU rendering, model training,
paid API call, new dataset download or GitHub authentication/push.

`RESCUE/resources.json` and the final completion manifest provide aggregate
worker wall/CPU, closing-process CPU, session elapsed time, new artifact bytes
and conservative external Git/cache/temp storage charges. The new run is roughly
0.06 GB before sealing, including a conservative charge for the copied source
files; verified old data/environment are reused. Initial metadata/tool/editor
work is outside the worker meter; five seconds are additionally reserved for the
small bootstrap worker, and no host-wide exact CPU claim is made. The final
resource bounds include the measured closing checks and remain below all limits.

The committed config fixes membership and every pin; no historical source file
was edited. For reproduction, use a **fresh** RESCUE directory, reuse verified
inputs with `data`/`upstream` directory symlinks, and copy the compact config to
`registration.json`. Preserve the initial inventory before execution. The
original environment path below is the reused pinned Python 3.10 environment:

```sh
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
uv run --no-sync python scripts/recoverbench_qualification_command.py --root "$RESCUE" --name identity --timeout 180 -- \
  uv run --no-project --python "$ORIGINAL/env/bin/python" python -m dual_rec.recoverbench.qualification --root "$RESCUE" --stage identity
uv run --no-sync python scripts/recoverbench_qualification_command.py --root "$RESCUE" --name sources --timeout 1500 -- \
  uv run --no-project --python "$ORIGINAL/env/bin/python" python -m dual_rec.recoverbench.qualification_replay --root "$RESCUE"
uv run --no-sync python scripts/recoverbench_qualification_command.py --root "$RESCUE" --name generator-preflight --timeout 90 -- \
  uv run --no-project --python "$ORIGINAL/env/bin/python" python -m dual_rec.recoverbench.qualification --root "$RESCUE" --stage generation-preflight
uv run --no-sync python scripts/recoverbench_qualification_audit.py --root "$RESCUE"
uv run --no-project --python "$ORIGINAL/env/bin/python" python scripts/recoverbench_qualification_audit.py --root "$RESCUE" --physics
uv run --no-sync python scripts/recoverbench_qualification_analysis.py --root "$RESCUE"
```

Exact executed commands, preparation scripts, source versions and all failed
attempts remain in RESCUE, including `workspace_manifest.json` for the unmodified
upstream test layout. Raw data, logs, compiled arrays, derived NPZs and detailed
outcomes stay locally excluded. `.gitignore` remains unchanged. Final source and
evidence hashes and local commit are in `RESCUE/completion_manifest.json`.

### 16.8 Scientific implication and stopping boundary

This rescue establishes that source action semantics and initialization flow
matter: some tapes reach the original task predicate under raw injection while
the released source checker does not. It does not identify a unique causal
controller fix or certify exact original-state/action replay. FK extraction can
be made internally consistent for the local model; that is not a recovery-skill
selection contribution. The original campaign's results remain valid descriptions
of its own workflow, not universal failures of every recovery-generation path.

The Stage A equivalence obligation and Stage C prepared-source/interface
obligation remain unresolved. Hence **INCONCLUSIVE**, with the two explicit
compatibility/source-generation blockers. B1–B5 comparisons, applicability
acceptance/rejection, abstention, coverage frontier, B4–B2/B3 effects and their
intervals remain **N/A**, not zero. H2–H4, methodological novelty, official Normal
SR/RSR and physical robot generalization remain untested. No official held-out
evaluation, new research direction, additional recovery policy or manuscript
was started. This bounded audit is ready for the principal researcher's review
and manual publication; a method pilot needs new qualified inputs/evidence.
