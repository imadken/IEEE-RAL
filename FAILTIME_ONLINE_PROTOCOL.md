# FailTime online-trigger protocol

Registered 2026-11-12 on reviewed base
`ec42c27c1a266cd1f2321de56f9b11490cbf95a4` before model fitting or evaluation
performance analysis. Authority is the principal researcher's supplied
FAILTIME_ONLINE_TRIGGER_CODEX contract, preserved verbatim in the local run.
This is the same early robot-failure research question; no architecture search,
new dataset search, VLM, physical recovery experiment or novelty claim is allowed.

Evidence root: `results/failtime-online/20261112T101800Z/`.
The complete compact specification is
`config/failtime_online_20261112T101800Z.json`, copied to registration.json.

## Source and qualification

ProTracer source: `63dafa9b703be0347d80f63d049304269f8d000f`.
FailTime HF revision: `07aea9142616cf1f8047512bd53a4d9fcd5e7cee`.
The 100 Long HDF5 objects total 6,116,046,222 bytes. Acquire the complete cohort,
first qualifying three fixtures in sorted (robot,verdict) classes using the
smallest SHA256(task_id/sample) per class; no signal-based selection. Hash whole
files against HF LFS identities. Read actual timestamps, EEF16 and indexing;
inspect camera schemas without decoding video. At least40 failures with in-range
onsets,25 successes and2 task groups must qualify before fitting.

Retain censored records. `handover_episode_10` has onset45.233333,1357 samples at
30Hz, last timestamp45.20000076293945. It is one frame beyond observed history:
keep its unchanged annotation and observed calibration prefix, mark target
unobservable, and do not count it among the56 in-range onsets supporting DATA_GO.
All100 signals remain in the study (57 failures/43 successes).

Short official annotation files and original ViFailback raw availability are
audited separately. Its named calibration50 overlaps training1084 completely;
any future Short fitting must exclude those IDs from training. Do not claim the
released files are disjoint. Prioritize the full Long cohort under8GB; any Short
subset needs independently verified matching raw paths and a justified complete
comparison, not selective favorable cases. Long has only an official test file;
it supplies no official train/calibration split.

## Internal split and exposure

Assign every robot/task group by integer SHA256("failtime-online-v1|robot/task_id")
modulo5:0 evaluation,1 calibration,2/3/4 training. All original IDs in each group
remain together. The fixed result is74 train,18 calibration,8 evaluation. Both
evaluation tasks are ALOHA; no held-out SO-101 claim is possible. Do not reroll the
split. Qualification metadata and the three fixture signals were examined before
fitting. Consequently this is exploratory internally held-out model/calibration
evaluation, not untouched confirmation or an official leaderboard split.

Use a10Hz decision grid from0 through the last supported native timestamp,
choosing the last native measurement at or before each time (tolerance1e-7).
All methods receive the same EEF16, plus past backward difference16 computed
on this held decision grid. These are discrete resampled pose increments divided
by.1s, not certified exact physical velocities. Keep released gripper/quaternion
coordinate conventions. No runtime verdict, onset, reason, phase label, future
command, episode identity or duration enters scoring. Robot platform is a known
static deployment stratum. No command-assisted regime is added.

Primary first alarm persists.1s from recording start, never reset at onset.
Timely is onset<=first alarm<=onset+1s, with1e-7 numerical tolerance. Premature,
late, missed and success alarms retain all recording denominators. Exposure ends
at the last10Hz decision time; native duration and observability are recorded.

## Frozen methods and calibration

B0_time is elapsed time; B0_prior is training failure prevalence. B1 uses pinned
upstream modal-Hamming PELT with penalty2,jump2,.2s minimum segment, available-prefix
snap±.2s,.5s spacing and two-pass pruning, fixed15-phase budget. Replace whole-run
motion normalization with the training-success20th-percentile floor, run on the
available prefix only, and timestamp cut-count decisions on arrival. This is an
explicit causal adaptation of a retrospective component, not a published online
failure detector reproduction. Test incremental PELT against exact pinned-prefix
recomputation; do not backdate alarms to discovered cuts.

B2 uses robot-global training-success velocity residuals and fixed CUSUM. B3 is
the original1s logistic last/mean/std/slope model, L2.01, equal-record train-only
normalization, positive weight capped10 and unchanged L-BFGS optimizer. B4 is one
GRU32 layer with scalar failure head, Adam.001, weight decay.01, gradient clip1,
30epochs and seeds11/23/37 probability ensemble. No early stopping on held-out
labels, architecture selection or threshold search is authorized.

MCSFA uses the same16 derivative evidence channels and CUSUM. Each arm's mode
combines gripper-delta sign and xyz squared displacement above the training-only
20th percentile:36 combined modes. Mode distributions need50 frames from2 nominal
training recordings; otherwise use that robot's global distribution. Unknown
robot nominal coverage abstains. Equal-record means/stds, std floor1e-6, clipped
z±10, training nominal evidence90th percentile define increment
mean(z²)/max(q90,1e-6)-1, with state=max(0,previous+increment). No-mode is exactly
B2; no-accumulation uses the instantaneous increment.

Calibrate one constant threshold per method on calibration success whole-run
capacities and failure capacities strictly before onset. Separately permit
floor(alpha*n_valid) alarms and use nextafter above the conservative order
statistic; deploy the larger threshold. Invalid prefixes are explicit, never
fabricated. Primary alpha.10; .05/.20 are fixed descriptive sensitivities. Freeze
models, source, calibration predictions and thresholds before evaluation scoring.
No hindsight threshold is executable. Budgets are empirical, not safety guarantees.

## Controls, robustness and gates

Complete development-only within-recording onset contrasts, including the clock,
and a first-second source-role logistic diagnostic with fixed.5 threshold.
Exclude failures with onset<=1s only from that diagnostic, never from alarm counts.
Context distinguishability is not fraud, causal confounding or proof of no signal.

Apply10/30% deterministic native-packet dropout and.2/.5s observation delay,
sample/holding available measurements. Keep frozen thresholds and common exposure.
Evaluate persistence0/.2s with the primary.1s-calibrated thresholds unchanged.
Report robot/task strata and individual GRU seeds descriptively, never selecting
a favorable seed. Event movement under sensing delay is not improved sensing.

Use2,000 task-cluster bootstrap draws, seed20261112 reset per contrast, in order
MCSFA minus B2/B3/B4/no-accumulation and metric order timely,premature,clean_alarm,
combined burden. Retain role-absent draws as invalid and state effective counts.
With only2 held-out tasks, intervals are coarse and [0,0] does not imply population
equivalence. G1 requires competent development event contrast beyond clock/context;
G2 requires the contract's5-point timely gain or20% burden reduction at constrained
other rates, supported by paired intervals. G3 cannot establish platform
generality from this split. Complete fixed analyses even after a failed gate.

## Audit, resources and completion

Independent data and numerical analyzers import neither main loader nor compared
model/scorer. Verify hashes, aliases, timestamps, labels/censoring, task split,
actual calibration IDs/masks, first alarms from0, denominators, source-role
predictions and paired inference. Save raw risk streams and examples of every
available outcome category, including the uncertain annotation example. Run
targeted tests, relevant REBOOT regressions, Ruff and format checks. Keep local
raw files, predictions, checkpoints and logs untracked; compact source/tests,
configuration and this protocol/report are the only new Git content.

Reuse the existing locked foreground worker, at most2 numerical threads, no GPU
by default. Limits:8h elapsed,10 measured CPU core-hours,8GB downloads,10GB new
artifacts, at most2 workers; reserve30min/0.5core-hour for closing. Retain failed
attempt logs and resumable hashed checkpoints. Preserve all prior evidence,
user working-tree changes, .gitignore and uv.lock. Local commits only; no push,
credentials, author contact or paid inference. Stop at completion of the fixed
authorized work or a defined scientific/resource boundary, with no workers left.
