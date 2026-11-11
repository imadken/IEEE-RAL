# REBOOT phase-constrained recovery recognition: supervised protocol

Reviewed base: `65965c96216748f0d930ef1546dd9aa70361b48d`; branch
`research/reboot-phase-recovery`; evidence root
`results/reboot-phase/20261111T204459Z/` (RUN). Authority is the supplied
supervised REBOOT research campaign. RecoverBench/ACRR is closed; no simulator,
robotics-policy execution, source replay or environment repair is authorized.
All historical source, reports, data, environments and `uv.lock` are preserved.

## Fixed question and scientific boundary

Test whether jointly modeling task phases and mechanical metadata improves
causal recognition of an emerging failure before human recovery, especially on
unseen precision-assembly objects. Temporal filtering, phase annotations and
mechanical affordances are established ideas; no novelty/theorem claim follows
from their implementation. Recognition of a previously induced deviation is
distinct from anticipating an arbitrary future externally imposed event.

The primary target window is the episode-local interval [t_f,t_r). Failure onset,
recovery start, true phase/type, outcome and future corrective actions are labels
for evaluation only, never deployed model inputs. Clean controls require actual
expert episodes and equivalent phase windows/observation budgets. If annotations
cannot support that target, finish the authorized Case D validity/shortcut audit,
report DATA_BLOCKED and do not fit invented labels or an alternative classifier.

## Pinned sources and object selection

The complete REBOOT primary paper `2609.22591v1`, including limitations and
annotation appendices, is read before method implementation. Its downloaded
PDF SHA-256 is `1f5401dfe2a8209a83cb96780a43fbfa0938f8a743eb8285be793fbdd60cf6f5`.
The official project is `https://nanayawoa.github.io/REBOOT/`. The linked source
fork `anon-robo-account/REBOOT` is pinned to
`269d53958caf32913104c5a93f8ee4ed84704a0f`, tree
`7dbfbc94c27bb0478f97598fc59f9fbea6b56061`. No upstream code is executed to
change or trim the original datasets. Dataset licenses and per-file provenance
are retained; the paper's examples are not assumed to be real episode labels.

`config/reboot_20261111.json` freezes exact names and immutable revisions from
the official 38-repository REBOOT26 listing before trajectory analysis. The
three families are 16 mm cylinder (continuous symmetry, 0.20 mm clearance),
USB-C (C2, 0.09 mm) and RJ45 (C1, 0.13 mm), both install and remove. The two
released USB-C recovery-install parts are both included; no difficult part is
discarded. In total: 13 pilot repositories plus the 60-episode engineering
sample. The sample is not an independent scientific pilot or additional training
data. Never replace these objects based on modeling outcomes.

## Phase A qualification and acquisition

Inspect the sample first, then metadata and action/state data from the frozen
repositories. Enumerate actual episodes, phase/event annotations, mechanical
metadata, operators/sessions and camera alignment fields. Verify episode IDs,
timestamps/frame indices, observation/action schemas, phase-boundary ordering,
event bounds, positive [t_f,t_r) windows, missing fields, repeated/rounded labels,
duration/padding shortcuts, duplicates and object/session grouping. Report
inconsistencies without guessing offset corrections, converting absent events
to negatives or deriving onset from future corrective actions.

Video archives and embedded depth columns are not required for this initial
pilot. Download the small sample trajectory files directly; for large depth-
embedded Parquets use bounded HTTP range reads of only the footer and causal
state/action/index/timestamp columns. Preserve every fetched range with offsets,
HTTP Content-Range, byte count and SHA-256, and save separately hashed projected
tables. These are verified partial/projection artifacts, not falsely certified
whole-file LFS hashes. Stop rather than accept a server ignoring ranges on a
large object. All original metadata/annotations remain unchanged.

A data GO requires real failure and clean episodes with attributable, in-bounds
events and sufficient phase labels across the fixed object families. One sample's
annotations are not transferred to other episodes/objects merely by index or
similarity. A byte-identical state/action match may establish sample duplication,
not create missing labels for other objects. Missing multi-object event timing
blocks the transfer-recognition claim and invokes the independent data audit.

## Conditional models, features and evaluation

Only after data qualification, inspect development physical signals and commit
the exact episode splits, feature dimensions, training hyperparameters, grammar,
metadata mapping and operating point before qualification outcomes are opened.
Use current qpos, backward differences and previously issued actions; no centered
derivatives, future frames, episode length, annotation phase/time/type, outcome,
operator future commands or held-out normalization enter runtime features.
Scaling, grammar and learned metadata relationships use training episodes only.

B0 is a time/duration prior, B1 causal kinematic stall/deviation rules, B2 a
regularized window classifier, B3 a small causal TCN/GRU, B4 phase-aware without
mechanical metadata, B5 phase-aware with metadata but unconstrained, B6 PCRR
with the same evidence/metadata and an explicit training-derived transition
grammar, B7 annotated-phase oracle. B7 is never deployable. Recovery backtracking
is permitted where training demonstrations support it; monotonic nominal phases
are not imposed on observed recovery. No rule is chosen to remove a known test
mistake. HMM/finite-state filtering has no claimed new theoretical result.

Use episode-disjoint training/development/qualification sets within objects;
operator/session holdouts only where real identifiers permit; leave one of the
three entire objects out of fitting for each exploratory object-generalization
fold. Never split overlapping windows across sets. With only three independent
objects, report each fold and broad uncertainty rather than precise population
generalization. The primary development-selected operating point is at most
10% episode-level clean false alarms, also report 5% where resolvable. Thresholds
and all normalization/model choices freeze before qualification; report an
unattainable discrete budget instead of tuning to held-out labels.

Primary outputs are episode sensitivity, clean false alarms, post-onset detection
delay and the fraction detected before recovery. Preserve pre-onset alarms as
false/early alarms; they are not credited as anticipation of an injected event.
Report complete delay/false-alarm frontiers, frame curves and episode outcomes,
paired episode-level intervals for B6–B3/B4/B5, per-object/operation effects,
phase accuracy, failure macro-F1, calibration/log loss, temporal violations and
runtime. Missingness and observation-delay controls use identical episodes and
budgets. Offline recognition is not physical recovery success.

If trivial timing/task identity solves a valid target, preserve the shortcut and
report NO-GO for the method claim. If phase/metadata/constraints add no benefit,
finish the corresponding negative analysis without new rules. Vision is a small
development-only conditional check after valid labels and a working proprioceptive
pilot; invalid annotations do not authorize video or foundation-model work.

## Independent audit, resources and repository policy

An independently implemented audit recomputes annotation joins, ranges, episode
groups and any actual model metrics. Test causality, schema rejection, index/event
bounds, duplicate joins, missing labels, range/projection integrity, resource
limits and evidence sealing; if models execute, also test grammar and alarm
metrics. Nonexecuted model comparisons/intervals/frontiers remain N/A, not zero.
Run focused tests, maintained `pytest -q tests`, Ruff and formatting, with all
test/cache output redirected inside RUN. Preserve previous seals and every
historical byte; no incidental cache writes into prior evidence are permitted.

Limits: eight campaign wall hours, ten measured CPU core-hours, two GPU wall
hours, six GB initial downloads and ten GB new artifacts. No paid APIs, large
model training, robot/simulator execution or detached jobs. An isolated Python
3.12 environment contains only required REBOOT analysis dependencies. Meter
foreground workers/driver CPU, wall, memory, exit codes, versions and download
bytes; disclose unmetered interactive overhead rather than claim host-wide CPU.

Case D must finish the real public-data validity and shortcut-bias audit, not
stop at the first missing field. Finalize all independently executable checks,
record negative evidence, write the report and seal locally. Commit only scoped
source/tests, this protocol, report and small necessary reproducibility manifests.
Raw metadata, Parquets, ranges, videos, predictions, tensors, logs and checkpoints
stay locally excluded. `.gitignore` and historical lockfiles remain unchanged.
No GitHub authentication or push; the user publishes the final local branch.

## Overnight extension registered before fitting: 20261111T224622Z

Authority: the supplied REBOOT overnight campaign, reviewed base
`24f84001aff2c975c25f7f820ae6d8a901a58758`, branch
`research/reboot-overnight-evidence`. This authorizes a different, restricted
single-object annotation-agreement experiment; the original multi-object
DATA_BLOCKED finding above remains unchanged. No mechanical-metadata transfer,
physical recovery, certified false-positive or publication-readiness claim follows.

The full frozen settings and exact recording/fold IDs are in
`config/reboot_overnight_20261111T224622Z.json`; local outputs are
`results/reboot-overnight/20261111T224622Z/`. Exact equality of state, action,
timestamps and frame ordering joins all 60 sample aliases to cylinder recordings.
The cohort contains 55 original-schema accepted positive-window recoveries and
62 expert-source nominal references, each physical recording counted once.
Sample entries 16,26,35,37,48 remain excluded with their raw labels visible.
No compatible earlier signal pilot was present. Inputs are consumed read-only.

Five role-balanced SHA-256 folds use evaluation k, calibration (k+1)%5, and the
other three for fitting. All seeds 11/23/37 are used. B0 is shared; B1/B2/B3
and the shared phase model run under Q and Q+C. Fixed 30-epoch GRU32 models,
Adam .001, clipping 1 and equal-recording losses are retained after the
synthetic-only three-epoch throughput smoke projected approximately ten minutes
for the full neural matrix with a factor-two allowance. No comparative score
has been inspected. Model/scaler/transition learning uses training recordings
only; no test-based early stopping or architecture sweep is authorized.

10-Hz features use received scored observations, backward differences over
their actual source times, and the previously issued native-frame target.
Only B0 sees elapsed time. The first alarm is a threshold streak spanning .1 s
from recording start, with 2-microsecond timestamp tolerance. Calibration uses
the lowest float64 threshold attaining at most floor(.1*N) reference alarms,
with conservative ties. Score times satisfy t<H, where H is the registered
training-only role-duration quantile rule. Three seed risk probabilities are
averaged before main calibration; seed-specific calibration is descriptive.

All training folds contain chronological phases 1–4 before recovery; phase 5
has no pre-recovery support and will not receive an accuracy claim. Missing
expert phase labels are masked. P0/P1/P2 use identical trained phase weights,
with unfiltered, forward-filtered and .3-second EMA phase mixtures respectively.
Allowed edges are observed training adjacency plus self edges, pseudocount 1;
initial counts have fixed +1 smoothing. Originating phase is not current phase.
Filtering constrains latent paths, not necessarily marginal-argmax transitions.

Primary contrasts: B3–B2, P1–P0, P1–P2, each with timely, premature and
reference-alarm differences and 2,000 paired role-stratified recording bootstraps.
Always finish Q/Q+C, B0, .5/1-second interiors, onset-reset inflation,
10%/30% packet loss, .2/.5-second availability delays and fixed training-event
permutation B2 development checks. Thresholds remain fixed for sensor stress.
After main predictions are sealed, compatible already-downloaded expert sources
for the five other object/operation groups receive a nominal-shift diagnostic;
no event sensitivity is inferred there. A streaming replay exposes model-level
signals, not physical root causes. All negative results and absent categories stay.

One locked foreground CPU worker, at most two threads; no GPU is available.
Reuse CPU PyTorch and the earlier PyArrow installation read-only, with new caches.
Limits: 10 campaign hours, 12 measured CPU core-hours, 2 GPU hours, 2 GB additional
transfers and 4 GB new artifacts; reserve 45 minutes and .5 CPU hours for closing.
Workers checkpoint individual fits/folds, append progress/ledger entries and
can resume with the same commands. No extra topic, simulator, author contact,
new data collection, video/weight downloads, push or credentials are authorized.
