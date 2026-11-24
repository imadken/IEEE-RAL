# From Failure Labels to Executable Recovery

## Research disposition and scope

The fixed campaign completed five FailTime folds (30 checkpoints; 40,500 OOF
outcomes), 24 repeated RecoverBench action rollouts, and exact reproduction of
the REBOOT alarm/alias findings. The full-cohort primary result remains negative:
MCSFA has 0/57 timely alarms versus B3’s 1/57, with no conditioning advantage
over global CUSUM. The strongest protocol sensitivity is REBOOT’s invalid reset,
1/55 versus 51/55 on unchanged B3 scores. Neither result estimates physical
recovery improvement.

This is a bounded, exploratory consolidation of the existing DUAL-REC project,
not a new detector study. The selected contribution is a **claim-to-evidence
audit**, implemented as typed executable obligations and evaluated on three
versioned cases. The elementary distinctions between temporal causality,
prediction and intervention are established principles, not new theorems.

**Novelty warning:** the broad detection-to-useful-intervention argument is
already substantially addressed by RESCUE, and score-validity auditing appears
in FailBench. A four-contract vocabulary alone is insufficient novelty. The
remaining candidate contribution is narrower: a reusable, purpose-specific
audit that connects temporal annotation semantics, continuous alarms, calibration,
recording identity, simulator/controller provenance and intervention claims,
together with measured consequences in three existing benchmark releases.
Distinctiveness remains provisional until this framework shows useful coverage
beyond those works and can be applied independently by another evaluator.

Evidence root: `results/recovery-contracts/20261112T124115Z/`. Registration was
committed before fitting (`eff69fde4ef0284ba3a21b0ff8d6a5376d9156bf`).
Reviewed base: `901165216752ff656fef7de93491d617540839a7`. Branch:
`research/recovery-evidence-contracts`. No previous evidence, `.gitignore`,
`uv.lock`, or initial user documentation moves are part of these changes.

## 1. Claims and evidence contracts

Let a recording contain packets \(p_j=(x_j,s_j,a_j)\): a measured value, its
source timestamp and its arrival time. Labels \(Y_i,L_i\) specify an episode
outcome and annotated events, with their declared semantics and provenance.
They are different objects from observations \(x_j\), predicted scores
\(r_i(t)\), executed controls \(u_i(t)\), and measured execution outcomes.
The permitted runtime history is

\[
\mathcal F_t=\sigma\{p_j:a_j\le t,\ s_j\le a_j;\ c,\theta_{\rm train}\},
\]

where static context \(c\) must be available at deployment and trained
parameters are frozen before evaluating that recording. Annotation-defined
onsets, task completion, future commands and whole-record normalization are
not runtime inputs merely because they appear in the same offline file.
An annotation can enter a calibration procedure on a disjoint calibration
population; that does not make it a permitted runtime feature.

These contracts organize increasing *claim obligations*, not mathematically
nested sets of tasks. An online warning can predict final failure without
estimating an onset; a human can execute a recovery without an online detector.
Each manuscript claim must identify the obligations it actually needs.

| Contract | Inputs and permitted information | Fidelity and observable outcomes | Valid metrics | Unsupported inference |
|---|---|---|---|---|
| C1: retrospective localization | Complete recorded observations; released outcome/event labels for scoring; any use of labels in training declared and partitioned | Identity/time alignment of the recording; annotation bounds and meaning; predicted event positions or intervals | All-failure tolerance accuracy, conditional MAE with denominator, interval overlap, exclusions and annotation uncertainty | A retrospective estimate is not a runtime emission time, executable action or measured recovery gain |
| C2: causal online detection | Only \(\mathcal F_t\); separate training/calibration/evaluation groups; independently labeled success references and explicitly defined background prefixes | Packet availability, causal features/model state, continuous alarm state from recording start; observed alarm time and full exposure | Joint timely/premature/late/missed counts, success alarms per recording and hour, conditional delay plus misses, recording/task uncertainty | Offline localization, onset resets, or evaluation-selected thresholds do not establish a deployable online alarm; nominal calibration targets do not guarantee held-out false-alarm rates |
| C3: physically executable recovery | A declared start state, action interface, policy/controller state, environment model, success predicate and remaining budget | Actual action stepping or real execution; initialization fidelity and no intervening state injection; initial/terminal success, first success, time and action logs | Newly successful executions among initially unsuccessful starts, first-hit and terminal success separately, budget compliance, replay residuals and parent-group uncertainty | Joint-state agreement, forward kinematics, stored demonstration success or an already successful start does not establish that the proposed recovery executes successfully |
| C4: intervention effectiveness | Declared alternatives, alarm rule, policy, workload, budget and costs; matched valid branches or an identified randomized comparison | Restored robot **and policy/controller** state and declared stochastic execution model, or valid randomized physical trials; measured alternative outcomes/costs | Paired success/cost differences, harm on nominally successful episodes, cost to completion under stated retry assumptions, uncertainty at the assignment/parent unit | Recognition accuracy or one executed recovery cannot identify the benefit of acting on an alarm |

### Continuous alarms and denominators

For a fixed threshold \(\eta\) and persistence \(p\), define

\[
\tau_i=\inf\{t:r_i(v)\ge\eta\text{ at all observed decision samples in a
continuous run from }b\text{ through }t,\ t-b\ge p\}.
\]

Missing/below-threshold samples break a run. The search begins at recording
start, not at a supplied onset. With target interval \([\ell_i,h_i]\), the
first alarm is premature, timely, late or absent; these categories exhaust the
failure population. REBOOT instead preserves its original strict upper bound
\([\ell_i,h_i)\) and original numerical tolerance. Do not silently unify these
different historical semantics. For successful episodes, report the fraction
with an alarm and alarms per observed reference hour. Abstentions stay in the
population; valid lack of observable target time is reported explicitly, with
both the original failure denominator and an observable-window counterpart.

The target interval is an annotation-defined evaluation convention. A
retrospective deviation label is not an experimentally identified latest
recoverable instant. Calling an alarm “premature” here is a metric definition,
not evidence that early prediction or intervention would be harmful.

### Execution and intervention

Write the restorable execution state as
\(S_t=(q,\dot q,o,\text{contacts},\text{actuators},m_c,m_\pi,\text{RNG};M)\),
where \(m_c,m_\pi\) include controller memory and policy queues and \(M\)
specifies the model and time/action conventions. Equal visible poses do not
imply equal continuations when these omitted quantities differ. An XML hash
inequality is a provenance discrepancy, not a proof of changed physical
dynamics: visual-only changes can alter hashes. A passing interface check also
does not prove equivalence of two models.

For action \(a\), an effectiveness estimand might be
\(\Delta_Y=E[Y(a)-Y(\mathrm{continue})]\) or
\(\Delta_C=E[C(a)-C(\mathrm{continue})]\), conditional on the declared
workload, policy, execution model and budget. Valid branching must preserve
the experiment being compared; observational failure labels do not identify
these counterfactual quantities. We do not claim a new identification result
or estimate such a physical recovery benefit in this campaign.

### Illustrative counterexamples, not theorems or experimental samples

1. A full-video procedure can return the correct historical event position
   after completion while emitting no runtime alarm. Exact C1 localization
   therefore need not satisfy C2.
2. A score high before and after onset triggers a premature first alarm.
   Restarting its persistence clock at the known onset can credit a timely
   alarm without changing any score. This invalid rule depends on a label
   unavailable to a deployed detector.
3. Two simulators can share \(q,\dot q\) but have different controller goals,
   model parameters or policy queues, yielding different next states for the
   same control. Conversely, distinct visual XML hashes can leave physical
   transition parameters unchanged.
4. A correct warning followed by an expensive reset can cost more than
   continuing; a successful stored recovery can fail when its controls are
   executed from a different scene. Neither label accuracy nor a tape’s
   existence identifies intervention value.

## 2. Exact prior-work positioning

The comparisons below concern the inspected versions and accessible materials.
They do not claim that unpublished appendices or inaccessible full papers lack
particular details. No listed detector was retrained as an external baseline.

| Work | Already addresses | Remaining distinction and inspection limit |
|---|---|---|
| [ProTracer / FailTime, 2026](https://arxiv.org/html/2609.21369v2) | Full-rollout failure diagnosis/localization and annotated real-robot data; also runtime baselines | Our EEF-only first-alarm cross-fit is a different, exploratory task, not a reproduction or ranking of its visual/VLM methods. Full HTML, metrics and pinned source inspected. |
| [Ma, Fan and Liu, RTCSA 2026](https://ieeexplore.ieee.org/abstract/document/11662154/) | Online robot-manipulation failure detection and AUTC timing-aware evaluation | We do not invent online timing metrics. Abstract/metadata verified; full IEEE PDF inaccessible, so exact reset, censoring and calibration equivalence remains unverified. |
| [STREAM-FAIL, CoRL 2026](https://omron-sinicx.github.io/Online_Robot_Error_Detection/) | Chunk-causal detection, temporal localization and description, with early triggers and later committed intervals | Runtime emission and retrospectively predicted interval positions remain distinct observables. Author project’s methodology inspected; full-paper review incomplete. |
| [RESCUE, 2026](https://arxiv.org/html/2610.13516) | Action-conditioned recoverability, replay fidelity, robot-policy branching, decision costs and break-even false-alarm rates | Strong substantive overlap with C3/C4 and their non-implication from prediction. Our candidate addition is cross-release evidence validation, not intervention-value theory. Full HTML methods/results inspected. |
| [FailBench, 2026](https://arxiv.org/html/2609.03611) | Episode-level success judgments, heterogeneous sources and reproductions that expose prevalence-dependent score comparisons | Reproducibility and metric-validity auditing are prior art. Our temporal/runtime/execution obligations and measured cross-contract cases are narrower proposed additions. Full HTML and reproduction appendix inspected. |
| [RecoverBench, NeurIPS 2026 release](https://github.com/ErrorRecoveryBenchmark/ErrorRecoveryBenchmark/tree/88f6fedab46dd130a617e058f8d0d05a42c2ea3d) | Failure scenarios, simulator fingerprints, source checks, object-relative recovery generation and execution-based recovery evaluation | Our pinned interface/source-replay qualification is not the authors’ policy evaluation. Release code/docs inspected and run; OpenReview paper access blocked. |
| [FIPER, NeurIPS 2025](https://arxiv.org/html/2510.09459) | Causal runtime uncertainty, successful-reference calibration and first detection timing; states assumptions for false-alarm control | Independent calibration and temporal alarms are established. Its formal success-distribution assumptions must not be transferred to our task-shifted cross-fit. Full HTML method/calibration/metrics inspected. |

**Remaining contribution paragraph.** We propose a versioned claim-to-evidence
audit that identifies which temporal, population, execution and intervention
claims a particular benchmark use can support, implements portable checks with
explicit unknowns, and measures the consequences on three existing releases.
This does not invent retrospective localization, online metrics, recovery-value
evaluation or reproducibility auditing. To be scientifically distinctive, it
must show cross-contract failure modes not already captured by RESCUE’s
execution/value checks or FailBench’s score audit, quantify their practical
consequences with independent verification, and demonstrate that another
evaluator can apply the checks without dataset-specific silent exceptions.
The present convenience cases and incomplete access to two papers leave that
last distinctiveness claim open.

## 3. Reproduction and analysis design

The protocol and exact fold map were registered before fitting. Raw inputs are
symlinked to immutable previous evidence, not copied or relabeled. Historical
JSON manifests and scientific documents are indexed with hashes under the new
root. Background review includes prior DUAL-REC replay qualification, LOGIV
query-cost monitoring and SVR freshness studies. These are context, not new
robot-performance experiments in this campaign.

FailTime uses all 100 verified Long recordings (57 failure labels, 43 success
references; 13 tasks; ALOHA and SO101). Within each robot, tasks sorted by the
registered hash are assigned round-robin to five folds. Evaluation fold \(k\)
uses fold \((k+1)\bmod5\) for calibration and the remaining three for training.
Both robots occur in every evaluation and calibration fold; task groups never
cross a partition. Each recording receives one out-of-fold evaluation. The
original handover episode with onset beyond its last timestamp is retained.

The nine previous implementations and all hyperparameters remain fixed:
elapsed-time/prior controls, causal Sign-CPD, global CUSUM, logistic classifier,
GRU32 ensemble (seeds 11/23/37, 30 epochs), MCSFA and its no-mode/no-accumulation
ablations. Inputs are 10 Hz causal held EEF16 with backward decision-grid
differences. B3 uses its original one-second feature window. The GRUs average
probabilities across all three seeds. New training is necessary because the
registered training IDs differ from the old pilot; no old checkpoint has an
identical fitting population. There is no seed or architecture selection.

Calibration separately constrains the empirical persistent-score capacities of
successful records and strictly pre-onset failure prefixes, then uses the more
conservative threshold. Primary alpha is .10, persistence .1 s and timely width
1 s; .05/.20 alpha, 0/.2 s persistence, 10/30% packet dropout and .2/.5 s delay
are fixed sensitivities. Models/calibration/source seals precede evaluation.
Calibration targets are empirical constraints on small task-shifted samples,
not guaranteed held-out false-alarm rates.

Primary paired uncertainty uses 2,000 task-cluster resamples, seed 20261112;
robot-stratified task resampling is a fixed sensitivity. Sparse rates also have
95% Wilson intervals. All intervals are descriptive: Wilson intervals do not
account for clustering, and the task bootstrap conditions on fitted predictions,
does not refit models, and does not remove dependence caused by overlapping
training folds. An all-zero bootstrap interval is not evidence of equivalence.
All data informed prior development: this is exploratory cross-fitting, not
untouched confirmation or a causal comparison with the old eight-record pilot.

For H1, the separately registered offline readout is the earliest finite global
score maximum, evaluated by MAE and ±1 s agreement on the complete record. It
uses no onset to choose the peak but uses future scores, so it is never deployed
as an alarm. This fixed diagnostic may be poor; no alternative localization
readout is selected to improve its result. The deliberately invalid reset is a
separate diagnostic and is never described as legitimate C1 performance.

## 4. RecoverBench: actual repeated execution, limited inference

Source revision `88f6fedab46dd130a617e058f8d0d05a42c2ea3d`, dataset revision
`f2f9cfe9ad2135f40c0b47a70269cc806541b58d`, existing robosuite 1.4.1 /
MuJoCo 2.3.2 / Python 3.10 environment. The exact 12 selected tapes and two
workflows were repeated: **24 actual rollouts, 9,862 executed controls**.
All recorded initial-success, first-hit, terminal-success and length outcomes
matched the historical ledger. Requested/actual classes and fingerprints also
matched the historical identity audit. A successful reproduction of a rejection
is not a successful qualification of the rejected environment.

| Task / workflow | Tapes | Initially successful | First-hit after action | Newly successful / initially unsuccessful | Terminal success |
|---|---:|---:|---:|---:|---:|
| Stack / released checker, shared environment | 6 | 2 | 2 | 0/4 | 2 |
| Stack / raw controls, fresh reset | 6 | 2 | 5 | 3/4 | 4 |
| PickPlace / released checker, shared environment | 6 | 0 | 0 | 0/6 | 0 |
| PickPlace / raw controls, fresh reset | 6 | 0 | 1 | 1/6 | 1 |

PickPlace’s raw-workflow success occurs at control 714, exceeding the original
500-step target budget. Thus the displayed first hit is not a budget-compliant
benchmark recovery. The two workflows jointly change reset, controller cache
and goal handling; the comparison does not identify the causal effect of one
cache fix. Selected tapes also share clean parent trajectories. Previously
reported paired first-hit differences (.50 for Stack, .1667 for PickPlace) had
four-parent bootstrap intervals [0, .75] and [0, .60], respectively; those are
reused exploratory workflow intervals, not intervention-effect estimates.

The original factory attempts PickPlace_D0; its constructor rejects
`z_rotation`, and the released broad fallback constructs PickPlace. This is
directly reproduced in the pinned public stack and is separate from our
explicit yaw adapter. The adapter is an engineering diagnostic and is never
used to score a recovery. Stack_D0 constructs as requested. Both task-level
fingerprint checks reject the requested stored scene identity.

All 24 action traces agree with their stored initial state within
2.22e-16 but diverge from the reference pre-action trajectory after one control
at the fixed 1e-8 tolerance. The numerical auditor checks every control and
state-to-state continuity, with no intermediate state injections. The physics
auditor independently checks the original success predicate at 56 selected
snapshots and forward kinematics at all **4,931 source states**, with zero
position/rotation residual in that local model. Accurate kinematic reconstruction
therefore coexists with different action-driven continuations.

Physical equivalence to the original failure scenes remains **unknown**.
Original failure-scene XML and complete controller/gripper memory were not
available in the selected material. Clean-seed compiled comparisons include
visual site changes; XML hash differences alone do not prove altered dynamics.
The earlier 668-small-tape inspection found constant released EEF fields despite
moving reconstructed end effectors; the generator reads a cached controller
position after forwarding states. That bounded released-feature observation is
preserved as prior source/feature evidence, not newly re-inventoried here.

Crucially, the benchmark’s original generator performs object-relative MimicGen
waypoint adaptation. Our earlier identity-transfer adapter and the present
raw-tape/source-checker diagnostics do not reproduce the authors’ full
generation/policy evaluation. Missing prepared `datagen_info` in the selected
small library blocked that old preflight; the large original training corpus was
not downloaded. We cannot conclude that every generation path fails or that
the published evaluation is invalid. Counterevidence is material: five Stack
tapes do reach first success under the raw workflow, and local kinematics pass.

Evidence: `recoverbench_reproduction.json`, `recoverbench/identity.json`,
`recoverbench/source-diagnostics/outcomes.jsonl`, all new compressed step traces,
`recoverbench/independent_numerical_audit.json` and
`recoverbench/independent_physics_audit.json` under the new root.

## 5. REBOOT: purpose-specific labels and continuous alarms

The previous pinned inventory contains 14 repositories and 793 declared episodes,
including 60 sample aliases; alias collapse leaves 733 distinct physical
recordings. This campaign does not repeat a whole-release download/inventory.
It re-decodes the existing raw projected cylinder/sample signals, verifies all
60 sample/canonical numerical alias pairs, and rechecks the downloaded label
files against the pinned repository registry. Only the sample repository has
its own downloaded `phase.json`; verified numerical alias transfer supplies
the corresponding canonical cylinder-install labels. Absence of native files
does not erase those valid transferred labels.

Of the 60 raw sample annotations, 58 satisfy the phase schema. Samples 16 and
26 fail the phase-label schema; samples 35, 37 and 48 have invalid event bounds.
All raw annotations and original invalid windows remain unchanged. The original
55 eligible recovery recordings and 62 expert references give the bounded
117-recording pilot. Missing temporal annotations for the intended broader
object/operation target leave that evaluation unsupported; they do not invalidate
demonstration learning, episode-level analyses or this labeled cylinder subset.

All **1,638 original clean, unperturbed ensemble outcome cells** match exactly
under the original stored thresholds. Original persistence is .1 s, tolerance
2e-6, and the target is `[onset, min(recovery, exposure, horizon))`. This
strict upper bound differs from FailTime’s inclusive one-second convention.

| Q method | Timely / 55 | Premature / 55 | Reference alarms / 62 | INVALID reset timely / 55 | Offline peak ±1 s / 55 |
|---|---:|---:|---:|---:|---:|
| B0 | 0 | 0 | 0 | 0 | 15 |
| B1 | 1 | 54 | 10 | 55 | 1 |
| B2 | 5 | 46 | 16 | 48 | 1 |
| B3 | 1 | 53 | 6 | 51 | 1 |
| P0 unfiltered | 1 | 54 | 9 | 51 | 1 |
| P1 phase filter | 0 | 54 | 4 | 51 | 7 |
| P2 ordinary smoothing | 1 | 54 | 12 | 51 | 1 |

For B3, hiding the early alarm by resetting at known onset changes timely
detection from **1.82% to 92.73%**, a paired increase of 50/55 = **90.91 percentage
points** without altering any prediction. This is an intentionally invalid
protocol sensitivity in our own experiment. It is not attributed to the original
REBOOT paper, used as calibrated performance or deployed in streaming code.

The legitimate offline peak readout gives B3 only 1/55 within one second and
MAE 13.273 s; P1 gives 7/55 and MAE 7.458 s. Thus the strong reset result does
not establish good legitimate retrospective localization. B0’s 15/55 peak
agreement also cautions that coarse timing can look localized without useful
online alarms. Both variants and all methods are retained in
`reboot_reproduction.json`; no favorable readout was substituted.

Historical matched-background reanalysis remains part of the evidence, not a
new result of this run: primary Q/P1 reached 2/55 timely with six premature
alarms and zero reference alarms, versus Q/B2 14/55 with six premature and zero
reference alarms. The command-augmented QC secondary analysis gave P1 10/55
versus P0/P2 5/55 under that calibration; this is a useful contrary secondary
result and does not reverse the primary negative phase-filter finding.
Early-prefix source-role separability (historical AUROC .982) and command access
limit an event-specific interpretation. Phase filtering is not established as
better than ordinary smoothing or the stronger primary baseline.

Evidence: `reboot_reproduction.json` includes raw labels, coverage, aliases and
all method summaries; `reboot_outcomes.json` retains the paired recording-level
outcomes. Original phase/filter reanalysis and its immutable seal remain in
`results/reboot-onset-specificity/20261112T090003Z/`.

## 6. Background evidence retained without restarting old campaigns

`historical_document_review_index.json` and `historical_manifest_review.json`
record the previous reports/protocols and 26 reviewed manifests with hashes and
scientific dispositions. The review concentrates on the three primary cases;
it does not claim independent re-execution of every older experiment.

- DUAL-REC’s previous qualification separated snapshot restoration from full
  prefix replay. In 294 paired replay comparisons, numerical divergence did
  **not** change success outcomes or action rankings. This contradicts a
  universal claim that any fidelity discrepancy changes decisions. Earlier
  Lift qualification also passed its bounded 20-state/500-continuation checks.
- LOGIV monitoring reproduced a global-unknown blocking behavior and measured
  symbolic query costs, but did not establish a method advantage over the
  stronger comparator or reproduce physical sensing/recovery costs.
- SVR freshness conclusions are relative to their declared model and evidence
  semantics; they do not certify unobserved physical truth. Its negative
  qualification against the strong baseline is retained.

These results motivate claim discipline and supply contrary evidence. They
are not additional benchmark sample counts or new physical findings of this
consolidation. Original cloud evidence, lockfiles and all prior negative reports
remain preserved.

## 7. FailTime: completed full-cohort exploratory cross-fitting

All five folds completed training, sealing and evaluation. There are **30 actual
saved checkpoints**: five nominal-distribution fits, five B3 logistic fits,
15 GRU fits (all three seeds in every fold) and five early-prefix source-role
classifier fits. Every GRU completed the fixed 30-epoch recipe. No best seed was
selected. Checkpoints and indices are in `failtime/fold{0..4}/models/` and
`models_index.json`; the separate portable source-role coefficients are also
saved. The nonparametric/control methods reuse those fixed components.

| Fold | Training F/S | Calibration F/S | Evaluation F/S | Evaluation task groups |
|---|---:|---:|---:|---:|
| 0 | 37/24 | 13/13 | 7/6 | 3 |
| 1 | 26/21 | 18/9 | 13/13 | 3 |
| 2 | 28/27 | 11/7 | 18/9 | 3 |
| 3 | 38/28 | 8/8 | 11/7 | 2 |
| 4 | 42/29 | 7/6 | 8/8 | 2 |
| OOF evaluation total | — | — | **57/43** | **13 distinct** |

Each calibration/evaluation fold contains both robots. Across OOF recordings,
ALOHA contributes 21 failures/9 references and SO101 36/34. The exact per-task
and per-fold records remain in `fold_coverage.json` and `failtime_stratified.json`.
There are **40,500 distinct recording × method × operating-setting outcomes**
(100 × 9 × 3 alpha × 3 persistence × 5 packet conditions), with no OOF omission
or repeated evaluation ID. All primary target windows except
`handover_episode_10` are fully observable. Its unchanged onset is 45.233333 s
versus last timestamp 45.20000076293945 s; all 57 failures remain in the main
denominator, and the fully observable counterpart uses 56.

### Primary continuous first alarms

Alpha .10, persistence .1 s, clean packets. “Missed” here means **no first
alarm**, distinct from premature or late alarms. Success exposure is 2,285 s
for every method; zero primary abstentions. These are recognition outcomes,
not physical rescue outcomes.

| Method | Timely / 57 | Premature / 57 | Late / 57 | No alarm / 57 | Success alarms / 43 | Success alarms/hour |
|---|---:|---:|---:|---:|---:|---:|
| B0 prior | 0 | 0 | 0 | 57 | 0 | 0.000 |
| B0 elapsed time | 0 | 3 | 7 | 47 | 6 | 9.453 |
| B1 causal Sign-CPD | 0 | 0 | 0 | 57 | 0 | 0.000 |
| B2 global CUSUM | 0 | 1 | 5 | 51 | 5 | 7.877 |
| B3 logistic | **1** | 9 | 11 | 36 | 12 | 18.906 |
| B4 GRU ensemble | 0 | 3 | 4 | 50 | 2 | 3.151 |
| MCSFA | 0 | 7 | 5 | 45 | 5 | 7.877 |
| MCSFA no mode | 0 | 1 | 5 | 51 | 5 | 7.877 |
| MCSFA no accumulation | 0 | 5 | 0 | 52 | 3 | 4.726 |

The no-mode implementation equals B2 by design; it is not another independently
trained comparator. B3’s single timely delay is .874569 s; a conditional delay
from one hit must not hide its other 56 failure outcomes. Timely rates are 1.75%
for B3 and zero otherwise. Descriptive 95% Wilson intervals are [.31%, 9.29%]
for 1/57 and [0, 6.31%] for 0/57. MCSFA’s success-alarm rate is 11.63%
([5.07%, 24.48%]); B3’s is 27.91% ([16.75%, 42.69%]). These recording-level
intervals are not cluster-adjusted guarantees. The all-failure and observable
counterparts retain the same hit counts, with denominators 57 and 56.

Robot-specific primary counts further restrict interpretation:

| Robot / method | Timely | Premature | Late | No alarm | Success alarms |
|---|---:|---:|---:|---:|---:|
| ALOHA / B2 (21 F, 9 S) | 0 | 0 | 2 | 19 | 2 |
| ALOHA / B3 | 0 | 4 | 8 | 9 | 5 |
| ALOHA / B4 | 0 | 3 | 4 | 14 | 2 |
| ALOHA / MCSFA | 0 | 1 | 3 | 17 | 1 |
| SO101 / B2 (36 F, 34 S) | 0 | 1 | 3 | 32 | 3 |
| SO101 / B3 | 1 | 5 | 3 | 27 | 7 |
| SO101 / B4 | 0 | 0 | 0 | 36 | 0 |
| SO101 / MCSFA | 0 | 6 | 2 | 28 | 4 |

### Paired uncertainty and method conclusion

Differences below are MCSFA minus comparator, in percentage points, on the same
OOF recordings. Burden is `(premature failure alarms + success alarms) / 100`;
it is an alert-count summary, not an identified physical cost. Intervals are
the registered 2,000 task-cluster resamples, conditional on the fitted models.

| Comparator | Timely difference [95% interval] | Premature difference [95% interval] | Success-alarm difference [95% interval] | Burden difference [95% interval] |
|---|---|---|---|---|
| B2 | 0 [0, 0]* | +10.53 [2.00, 18.67] | 0 [−19.23, 24.32] | +6.00 [−6.09, 19.51] |
| B3 | −1.75 [−6.53, 0] | −3.51 [−28.21, 16.18] | −16.28 [−56.53, 13.22] | −9.00 [−36.49, 11.48] |
| B4 | 0 [0, 0]* | +7.02 [−10.26, 20.34] | +6.98 [−9.09, 25.01] | +7.00 [−7.87, 20.34] |
| No accumulation | 0 [0, 0]* | +3.51 [−5.88, 12.77] | +4.65 [−8.62, 22.58] | +4.00 [−4.85, 14.46] |

*All-zero empirical hit differences produce degenerate bootstrap intervals;
these do **not** establish population equivalence. Resampling task groups within
robot gives the same qualitative assessment: MCSFA versus B2 premature
difference +10.53 points [3.39, 18.75], burden +6.00 [−5.77, 20.00]. Equal
aggregate success-alarm counts do not mean the methods alarm on the same records.
No mode-conditioning advantage over the global sequential baseline is supported.
The observed premature-alarm contrast is unfavorable to conditioning, subject
to the limited 13-task, overlapping-fit, exploratory design.

### Fixed robustness and operating-setting sensitivity

At primary alpha/persistence, ordered as `clean / drop10% / drop30% / delay.2s /
delay.5s`:

| Method | Timely counts / 57 | Premature counts / 57 | Success alarms / 43 |
|---|---|---|---|
| B2 | 0/0/0/0/0 | 1/1/1/1/1 | 5/5/5/5/5 |
| B3 | 1/1/1/0/1 | 9/9/9/9/8 | 12/11/11/12/12 |
| B4 | 0/0/0/0/0 | 3/3/3/3/3 | 2/2/1/2/2 |
| MCSFA | 0/0/0/0/0 | 7/7/7/7/7 | 5/5/6/5/5 |
| No accumulation | 0/0/0/0/0 | 5/5/4/5/5 | 3/4/4/3/3 |

An unchanged zero hit count is not evidence of robust useful detection. B3’s
single hit disappears at .2 s delay; packet effects on other alarm populations
remain in the complete tables. Across the nine fixed clean alpha/persistence
cells, B3 timely counts are 1–2, MCSFA 0–1, B2/B4 zero. The MCSFA .05-alpha
one-hit sensitivity does not replace the registered primary setting. Persistence
matters especially without accumulation: at alpha .10, zero persistence gives
one hit but 22 premature and 20 success alarms; .2 s gives zero hits, one
premature and zero success alarms. No evaluation outcome selects a new threshold.

### Retrospective readout, role control and the old pilot

The legitimate offline peak diagnostic is poor on these streams:

| Method | Offline peak MAE (s), all 57 | Offline ±1 s hits / 57 | ±1 s hits / 56 observable | Primary online timely / 57 |
|---|---:|---:|---:|---:|
| B0 prior | 34.825 | 1 | 1 | 0 |
| B0 time | 19.863 | 1 | 0 | 0 |
| B1 | 18.946 | 2 | 2 | 0 |
| B2 | 18.408 | 1 | 1 | 0 |
| B3 | 16.189 | 0 | 0 | 1 |
| B4 | 17.673 | 1 | 0 | 0 |
| MCSFA | 18.207 | 0 | 0 | 0 |
| No mode | 18.408 | 1 | 1 | 0 |
| No accumulation | 19.273 | 2 | 2 | 0 |

The all-record B0-time/B4 peak agreement includes the censored record, which
explains its disappearance in the observable counterpart. We preserve both,
not claim an observed event where none was recorded. This study does **not**
demonstrate a good legitimate retrospective localizer paired with a bad online
detector. Changing estimands can change counts/rankings, but both valid readouts
are generally weak here. The strong REBOOT reset effect is a different, invalid
label-access demonstration.

The fixed early-prefix source-role classifier has OOF AUROC **.3592** and
balanced accuracy **.4217** on 99 eligible controls (56 failures/43 references).
`empty_bowl_insert_block_episode_27` lacks a complete first second strictly
before onset, so it is excluded only from this control and retained in all
primary evaluations. Fold AUROCs range .2564–.4877. No orientation is flipped
using these outcomes. Pooled scores come from different fitted models; this
weak control neither establishes onset specificity nor rules out other source
confounds. It contrasts with the strong role separation in the REBOOT study.

The original eight-record evaluation had only two ALOHA tasks, five failures
and three references. Zero timely hits there has Wilson upper bound **43.45%**;
zero alarms among three references has upper bound **56.15%**. The expanded
cross-fit gives much better coverage and narrower descriptive bounds, but is
not a causal effect of sample size or untouched confirmation. Refitting
populations changed, records overlap prior development, and uncertainty does
not include the entire model-training procedure. The larger evaluation retains
the negative method conclusion without claiming that useful online detection
is impossible with other modalities or independently sampled tasks.

Evidence: `failtime_summary.json`, `failtime_outcomes.json`,
`failtime_stratified.json`, both `paired_effects*.json`,
`retrospective_summary.json`, `source_role_oof.json`, `pilot_informativeness.json`
and per-fold model/calibration/source seals. All 405 operating-setting summaries
are retained, including negative and non-primary results.

## 8. Executable checks, independent audit and engineering findings

`src/dual_rec/contracts/checks.py` provides Pydantic boundary validation and 13
named obligations, plus a bounded future-suffix perturbation check. There are
known-valid and known-invalid fixtures for every obligation, including an
explicit leaking whole-record normalizer for the perturbation test. Runtime
declarations, timestamps, source/task partitions, success-reference calibration,
event semantics, simulator/controller identity, action stepping, denominators,
uncertainty units and branch evidence are separate checks.

The grouping requirement is explicit and claim-dependent. This task uses
source-and-task separation; a declared within-task generalization claim can
require source separation alone. The checker does not declare ordinary
within-task calibration universally invalid. Empty grouping requirements are
rejected. Missing evidence returns UNKNOWN; known violations return FAIL.
PASS means the supplied necessary checks passed, not that a dataset, causal
claim, provenance declaration or statistical independence is universally proved.

The final applications cover **136 claim contexts** with stored typed inputs
and verdicts. All 100 primary clean MCSFA streams satisfy continuous-alarm and
packet-time checks. The 100 fixed EEF future-suffix perturbations preserve prior
features. Source/task/calibration designs pass for all five folds. Controlled
misinterpretations of FailTime’s retrospective labels fail semantic checks;
uncollapsed REBOOT aliases fail numerical-duplicate checks. Missing targets
remain unknown. Stack’s original-scene physical equivalence is unknown;
PickPlace’s requested-class mismatch fails. All 24 actual rollouts pass the
execution-mode obligation, while state forwarding alone fails that obligation.
No context supplies an identified intervention effect: **C4 remains UNKNOWN**.

Independent implementations verify:

- Five complete numerical fold audits: all 40,500 outcomes, 135 threshold cells,
  scalar first alarms from recording start, calibration capacities, causal
  packet/feature construction, GRU probability-ensemble arithmetic, model and
  input seals, and early-prefix source-role coefficients/predictions. Relevant
  tests separately compare causal prefix-CPD against the pinned upstream source
  and check nominal/GRU prefix invariance.
- Exact once-only OOF coverage, the registered hash-to-fold assignment, 100
  recomputed numerical signal signatures, pooled and stratified counts, Wilson
  arithmetic, 32 pooled paired-bootstrap cells and all offline peak readouts.
- Independent aggregation of role-control and peak summaries, expected
  purpose-specific contract verdicts, REBOOT’s 1/55 versus 51/55 sensitivity,
  and every newly executed RecoverBench action trace; independent local-model
  predicate/FK checks have the limited scope specified in §4.

“Independent” here means separate implementations, including the earlier
standalone numerical auditors; it is **not independent human replication**.
The numerical auditor imports no compared scorer/model or new contract kernel.

One new adapter bug was exposed and corrected: indexing the last pre-onset
sample assumed nonempty history. `empty_bowl_insert_block_episode_27` has no
strictly pre-onset decision sample. The adapter now records its unavailable
calibration prefix explicitly and retains the recording, with a regression
test. Original calibration already retains invalid capacities explicitly;
no model, threshold, label, fold or prediction was changed. The failed command,
traceback, fix and successful recheck remain in `commands.jsonl`, the original
log and `resolved_worker_failures.json`. No dataset-specific identity is used
to suppress this condition.

Initial archive inspection also exposed an extension-filter omission of
compressed action traces. The filter and archive regression test were corrected;
the provisional unsealed archive is preserved locally, and
`archive_packaging_revision.json` records the change. Final archive verification
includes the compressed traces. This packaging correction changes no experiment.
The first full archive verifier reached its 300-second bound because member
access order repeatedly restarted gzip decompression. Verification now follows
the stored member order; a regression also rejects maintained files changed
after packaging. The bounded stop and successful corrected verification are
retained separately. These corrections change neither hash criteria nor results.

Final validation: **98 relevant contract/benchmark tests passed**, including
24 contract tests; **4 additional actual pinned-stack physics tests passed**.
The old simulator emits three existing deprecation warnings, retained in its
test log. Ruff lint and formatting pass for all maintained Python changes.
Three scientific figures were generated as PNG/PDF and visually inspected;
their captions preserve the invalid-reset and over-budget-success caveats.

## 9. Hypotheses: support, contrary evidence and unresolved claims

| Hypothesis | Supported finding | Contrary or limiting evidence | Disposition |
|---|---|---|---|
| H1: retrospective and continuous-alarm evaluations can differ | Same-stream readouts produce different counts; the controlled invalid reset changes B3 by 90.91 points on REBOOT | Reset is not legitimate retrospective localization. The registered legitimate peaks are mostly poor on both datasets, so this campaign does not demonstrate a strong legitimate C1 system with weak C2 | Limited empirical support for readout/estimand dependence; no broad positive localization claim |
| H2: missing temporal evidence can block a purpose without invalidating a dataset | Broader REBOOT temporal target lacks labels; a zero-length FailTime background prefix is unavailable and one final target is censored | Verified alias transfer supplies 55 valid REBOOT recovery episodes; 100 FailTime recordings and 56 complete target windows support the bounded analyses | Supported purpose-specifically; blanket invalidation contradicted |
| H3: state compatibility differs from executable recovery | Initial-state roundoff agreement and exact local FK coexist with divergence after one executed control and workflow-dependent successes | Five Stack tapes reach first success; missing failure-scene XML prevents identifying physical model mismatch as the cause. Older DUAL-REC divergence changed no decisions | Supported distinction in these interfaces; no universal replay failure or causal cache-fix claim |
| H4: contracts reveal limitations hidden by headline metrics | Initial-success versus new-success denominators, budget overrun, invalid resets, grouping and weak eight-record uncertainty change what can be claimed | These are selected previously investigated cases; no prevalence estimate, independent operator replication or demonstrated C4 benefit | Supported case-study utility; general portability and incremental novelty remain open |

## 10. Explicit principal-researcher review

1. **Distinct contribution?** A narrow methodological contribution is plausible
   but **not established merely by this consolidation**. The broad conceptual
   argument is substantially covered by prior work. Scientific distinctiveness
   depends on the portable cross-contract specification and independently
   replicated, consequential findings beyond RESCUE/FailBench. Incomplete primary
   paper access further limits a definitive novelty conclusion.
2. **Experimentally supported claims?** The exact pinned RecoverBench
   interface/source-execution findings and their local-model limits; REBOOT’s
   aliases, purpose-specific annotation coverage and controlled invalid-reset
   effect; all-100-record exploratory FailTime cross-fitting and the negative
   conditioning result; small-cohort uncertainty; executable check behavior.
   No physical intervention advantage, universal benchmark defect or useful
   detector improvement is supported.
3. **Essential missing results?** Independent human application of the checks;
   a demonstrated positive control under a fully matched original simulator /
   controller / policy state; original RecoverBench generation/policy-evaluation
   reproduction if claims about that evaluation are desired; stronger sampling
   and uncertainty; complete positioning against inaccessible papers. Valid
   intervention comparisons are missing if a later paper claims C4 benefit.
4. **RSS Stage 1 suitability?** The question, falsifiable hypotheses, specified
   methods and preliminary negative results fit a semi-complete methodological
   paper in form. The scientific novelty/portability case remains a gate, so an
   unqualified submission-readiness recommendation is premature. The outline
   gives a five-content-page plan and the official Stage 1 constraints; an
   archive cannot substitute for central evidence in those pages.
5. **Ranked remaining work:** (i) resolve primary-paper access/overlap and write
   an explicit non-redundant claim; (ii) have another evaluator apply frozen
   checks, including independently chosen positive and negative controls;
   (iii) qualify a complete original-scene execution/policy-state positive
   control before interpreting recovery transfer; (iv) plan stronger prospective
   sampling and training-aware uncertainty; (v) execute identified benefit/harm
   comparisons only if the paper expands to intervention-effect claims. These
   are future researcher decisions, not additional experiments silently begun
   in this assignment.
6. **Methodological science or software debugging?** Presently this is a
   methodological case-study prototype with substantial engineering evidence.
   The measured protocol consequences and claim-specific controls make it more
   than a bug list, but version-specific debugging is not by itself a paper-level
   contribution. A portable, independently useful audit methodology is the
   necessary scientific addition. No detector architecture or causality theorem
   is contributed, and no publication-readiness claim is made.

## 11. Evidence, commands, accounting and preservation

The three maintained deliverables are this report,
`RECOVERY_CONTRACTS_RESEARCH_PROTOCOL.md`, and
`RECOVERY_CONTRACTS_PAPER_OUTLINE.md`. The exact registration is
`config/recovery_contracts_20261112T124115Z.json`.

All local run paths below are relative to
`results/recovery-contracts/20261112T124115Z/`:

| Material | Exact location |
|---|---|
| Trained models, splits, thresholds, source/input seals | `failtime/fold0/` through `failtime/fold4/` |
| OOF recording-level outcomes, full summaries and uncertainty | `failtime_outcomes.json`, `failtime_summary.json`, `failtime_stratified.json`, `paired_effects.json`, `paired_effects_robot_stratified.json` |
| Original-score REBOOT reproduction | `reboot_reproduction.json`, `reboot_outcomes.json` |
| Actual simulator traces and original factory outcomes | `recoverbench/source-diagnostics/`, `recoverbench/identity.json` |
| Independent numerical/derived verification | `independent_numerical_audit.json`, `independent_derived_audit.json`, per-fold and `recoverbench/independent_*_audit.json` |
| Typed case inputs/verdicts and bounded future checks | `contract_applications/`, `contract_applications.json`, `prefix_noninterference.json` |
| Scientific figures and primary CSV | `figures/`, `primary_failtime.csv` |
| Primary-source positioning scope | `literature/inspection_manifest.json` |
| Exact executed commands, resource logs and preserved failed attempt | `commands.jsonl`, named `.log` files, `resolved_worker_failures.json` |
| Compact local review archive | `supervisor_review.tar.gz`, with `archive.json` and `archive_verification.json` |
| Closing preservation, resources, final commit and hashes | `preservation.json`, `resources.json`, `completion_manifest.json` |

The review archive contains maintained sources/docs, new prediction streams,
calibration/model metadata, figures, audits and decisive action traces. Raw old
datasets, environments and neural weights stay outside it. Full reproduction
uses the existing immutable input roots and the new model checkpoints; this is
not a standalone redistribution of all benchmark data. No logs, raw data,
weights or local review archives are committed to Git.

The reusable fixture audit can be run without any benchmark download:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache \
uv run --no-sync python -m dual_rec.contracts.checks \
  --input tests/fixtures/recovery_contracts/valid.json \
  --output /tmp/recovery-contracts-fixture-audit.json
```

The CLI refuses an existing output file. `commands.jsonl` records exact live
reproduction, cross-fit, audit, test and packaging commands. Scientific workers
refuse sealed roots; reproduce into a fresh registered root with a fresh clock,
not by editing completed evidence. Generic check inputs state their intended
grouping and claim; there is no hidden dataset-name waiver.

The session uses one bounded foreground research worker at a time, at most two
numerical threads, and no GPU, paid API, new dataset download or simulator
reinstallation. Before initial packaging, measured worker CPU was below one core-hour
and new run artifacts were about 193 MB. Final exact elapsed/CPU/byte accounting,
including packaging and closing, is recorded in `resources.json`; it separately
discloses a 300-CPU-second interactive allowance and a conservative 20 MB public
source-tool-transfer allowance. Limits are eight elapsed hours, twelve CPU
core-hours, two GB downloads and four GB artifacts. There are no background
research workers or agents launched by this campaign.

Closing checks compare every initial tracked/user-document path, all 26
registered prior manifests and the three canonical earlier review archives with
their original hashes. The user’s 14 root-document deletions and untracked
`docs/` moves remain outside these commits. `.gitignore`, `uv.lock`, cloud
evidence and prior scientific outputs are preserved. The final branch and exact
local commit SHA are recorded in `resources.json`. Publication remains manual;
no push, credential request, author contact or issue posting is performed.
