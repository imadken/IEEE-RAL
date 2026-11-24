# Recovery evidence contracts: fixed consolidation protocol

2026-11-12. Principal-researcher-selected question: **From Failure Labels to
Executable Recovery: A Contract-Based Audit of Robot Failure Benchmarks.**
Reviewed base901165216752ff656fef7de93491d617540839a7. Branch
research/recovery-evidence-contracts. Local evidence root
results/recovery-contracts/20261112T124115Z/. The full supplied authority is stored
there verbatim. No new detector, architecture search, dataset or physical robot
experiment is authorized. Previous negative results and user documentation moves
remain untouched. Local commits only; no push or credentials.

## Fixed evidence and claim scope

Parse and review the existing DUAL-REC, LOGIV monitoring, SVR, RecoverBench, REBOOT
and FailTime reports, protocols and manifests. Preserve source-inspection claims
separately from numerical reproduction and newly repeated physical simulator
execution. The primary cases are the pinned RecoverBench release-interface
qualification, REBOOT annotation/recording/first-alarm audit, and all100 existing
FailTime-Long recordings. Reuse original environments; no simulator reinstall.

C1 is retrospective localization, C2 causal online detection, C3 physically
executable recovery, C4 intervention effectiveness. These are evidence
obligations, not a theorem that every metric or dataset forms a nested set.
Formalize observations, annotations, score functions, stopping times, environment
state/controller memory, executed interventions, and potential outcomes/costs.
Elementary causal/non-identification counterexamples are illustrations, not
novel theorems. The prospective contribution is a concrete cross-benchmark
executable evidence audit and validated scientific findings.

RESCUE already evaluates alarm intervention value with counterfactual branches;
FIPER and time-aware online metrics already address runtime alarms; STREAM-FAIL
addresses streaming localization/descriptions; FailBench also audits score
validity. A generic claim that detection does not imply useful recovery is not
new. Exact coverage by all seven required works must be assessed and any
substantive overlap stated plainly, including inaccessible full-text limits.

## Reusable executable checks

Use dataset-independent typed evidence inputs and explicit PASS/FAIL/UNKNOWN
statuses for: causal timestamps/features; alarm persistence from record start;
forbidden label/future inputs and bounded prefix perturbation; independent
success-reference calibration; numeric duplicate aliases; recording/source/task
partition separation; event bounds/semantics; model/controller compatibility;
action execution versus state forwarding; denominators/abstentions/exclusions;
and grouping/uncertainty. Supply known-valid and known-invalid fixtures for every
check. Missing evidence is UNKNOWN, not a silent pass or dataset-specific waiver.
Finite tests and provenance checks are not a proof of universal noninterference.

## RecoverBench

Freeze the12 source tapes and exact conditions of the prior interface rescue
config. Re-run identity/compiled-model and24 source-checker/raw-injection
diagnostics in the existing isolatedPython3.10/MuJoCo2.3.2 stack, writing only
new outputs. Preserve expected fingerprints, constructor errors and fallback.
Independently compare new numerical results with the sealed recorded artifacts.
If runtime reproduction is blocked, retain the failure and independently
recompute the stored evidence; do not silently replace a live reproduction with
source inspection. Keep canonical XML, compiled physical parameters, controller
memory, source validation and actual task-success events distinct. The recorded
raw-tape adaptation is not the benchmark's MimicGen object-relative transfer
evaluation. No invalidation of authors' original evaluation is implied.

## REBOOT

Reuse the pinned annotation inventory, projected signals, canonical recording
hashes, folds and score predictions. Independently recheck available event-label
coverage and aliases. Reproduce the original ensemble first alarms with its
original thresholds, including all exclusions/censoring. On the identical risk
streams recompute the explicitly invalid post-onset persistence reset, retaining
the strict original target intervals. Report Q/B3's historical1/55 versus51/55
as a controlled hidden-event protocol sensitivity, not an allegation about
REBOOT authors or a valid intervention outcome. Preserve phase-filter negatives
and all matched-background reanalysis evidence.

## FailTime full-cohort cross-fitting

Use all100 verified existing Long signals:57 failure labels/43 success references,
13 task groups,2 platforms. The unchanged handover_episode_10 onset is beyond
the last observation; retain it with an unobservable target window and report
both all57 and observable-window failure denominators. Do not clamp annotations.

Assign groups by robot/task. Within each robot separately, sort tasks by
SHA256("recovery-contracts-v1|robot/task_id") and assign round-robin to folds0–4.
This guarantees platform representation without selecting from model outcomes.
For evaluation foldk, calibration is(k+1)%5 and the other three folds train.
Every recording is evaluated once, no same-task recording crosses a partition,
and success/prefix calibration populations remain separate. Register exact IDs
before fitting. Data are development-exposed; grouped cross-fitting does not
create untouched confirmation or remove shared training/session dependence.

Reuse the previous FailTime definitions verbatim:10Hz causal held EEF16 plus
backward increments; B0_time/B0_prior, causal prefix Sign-CPD, global CUSUM,
one-second logistic, GRU32 probability ensemble seeds11/23/37×30epochs, MCSFA,
no-mode and no-accumulation ablations. Refit only where training IDs differ;
reuse only exact-ID-compatible checkpoints. There is no architecture, optimizer,
feature or threshold selection. Existing primaryalpha.10/persistence.1s/window1s,
alpha.05/.20, persistence0/.2s and10/30% dropout/.2/.5s delay stay fixed.
Freeze each fold's model/input/source/calibration seal before its evaluation.

Pool canonical OOF outcomes, retain fold/task/platform cells and compare against
the earlier eight-recording pilot without treating the two evaluations as
independent. Primary uncertainty is2,000 task-cluster paired resamples, seed
20261112; platform-stratified task resampling and robot-specific summaries are
fixed sensitivity analyses. Include Wilson sparse-rate intervals, explicit
population denominators, false alarms/hour and detected delays alongside misses.
Bootstrap[0,0] is not population equivalence. No broad generality follows from
one public collection or two platforms with uncertain session/operator linkage.

## Fixed contract sensitivity and hypotheses

For H1, compare continuous first alarms with the hidden-onset reset diagnostic.
Also calculate a fixed retrospective readout—earliest global maximum of each
existing complete score stream—and absolute localization error/±1s agreement.
This readout is an offline diagnostic, not a proposed detector, author-method
reproduction or deployed threshold. No label selects its peak. Keep contradictory
results if the peak is uninformative. Toy counterexamples illustrate the logical
non-implications but never contribute experimental sample counts.

H2 concerns purpose-specific missing provenance/annotations; H3 separates state
compatibility from executable recovery; H4 asks what contract checks add beyond
headline metrics. For every hypothesis record supportive, contradictory and
unresolved evidence, with exact case-level scope. No universal hypothesis claim.

## Verification and bounds

Independently recompute calibration capacities, first alarms, temporal readouts,
denominators, duplicates/groups, simulator findings and paired uncertainty without
using the compared scorer as the sole verification. Run focused fixtures, relevant
maintained tests, Ruff and formatting. Preserve failed attempts and hashes.
Produce the requested scientific report and paper outline with genuine results,
precise prior-work overlap, a defensible narrow contribution, formalism, figures,
limitations, official RSSStage1 requirements and ranked missing work. Do not
declare publication readiness or acceptance probabilities.

Caps:8h elapsed,12 measured CPUcore-hours,2GPUwall-hours only if necessary
(zero by default),2GB extra downloads,4GB extra artifacts. One existing locked
bounded foreground worker, at most2 numerical threads, reusable checkpointed
folds,30min/.5CPUhour closing reserve. Symlink immutable old inputs rather than
duplicate raw data. No paid APIs or large models. Stop after all justified work
or a defined boundary, with no workers left running.
