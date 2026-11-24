# Explanation repair: Week 2 mechanism-validation results

**The current method lacks evidence for a distinct contribution over strong
evidence-only regeneration.** All six fixed comparisons completed. The public
adapter now recognizes useful command-order subclaims, but natural-language repair
quality remains unassessed without independently adjudicated labels. No simulator
campaign, model training, large-language-model calls, manuscript or Week 3 work ran.

Reviewed base: `b46679401fdcc33f362bbf53a032d1b368c88181`; branch:
`research/explanation-repair-week2`. This is exploratory development and reanalysis,
not held-out confirmation. Evidence root:
`results/explanation-repair-week2/20261113T130926Z` (abbreviated W2 below).
The final local source commit and resource totals are in W2's
`completion_manifest.json`; publication remains manual. Logs, full results and the
review archive stay local and are excluded using `.git/info/exclude`; `.gitignore`
and `uv.lock` are unchanged. The historical first-session report is retained below.

## Why the strongest baseline dominates

A separate recomputation read the 85 sealed raw simulator cells, rather than the
editor's support labels. On all 595 structured inputs, B3's true-information set is
a **strict superset** of B4's. It emits 3,465 independently checked factual
assertions, retains all 1,185 supported original facts, and produces 595 informative
outputs. B4 emits 1,315 factual assertions and 425 informative outputs. B3 reads the
same complete first/current observation history and declared transport-precondition
model; it enumerates visible facts and supported applicability values without
consulting future outcomes. B4 restricts its output to original claim slots and
locally supported replacements. When the explanation contains only an unsupported
battery story or unparseable prose, B4 falls back despite useful facts in the ledger.

For `PickCube-v1/103343/nominal/unsupported`, B4 says the evidence does not establish
a specific explanation. B3 reports the observed initial ungrasped/not-near-goal/no-
contact state, the current grasped/near-goal/contact state and conditional transport
eligibility. All seven facts are raw-oracle checked; none establishes the battery
cause or a recovery guarantee. For the same cell's `action_model` variant, B4 keeps
four current/model facts and B3 additionally retains the three historical facts.
Full examples and their extra fact sets are in `strongest_baseline_investigation.json`.

B3 does not use a hidden oracle, a larger evidence ledger, or an artificially narrow
last-snapshot baseline. All methods share the same primitive inference access and
4,096 candidate-evaluation ceiling; all observed runs meet it. B3 is a finite
ledger/model pass; B4 enumerates at most four options per claim in groups of four.
Runtime is measured rather than equalized by restricting B3's outputs. Cosmetic
rewriting alone is not damage: B3 changes all 295 initially correct texts while
losing no supported fact and adding no unsupported factual assertion.

## Actual natural-language coverage and its boundary

All original 750 rows at public revision
`730ba3200e84b6f1c140a4d7a6569f3a42fe1928` were reused unchanged. Extraction splits
clauses, grounds literal arguments to observation vocabulary, and matches identifiable
commands. Historical states without an observed time anchor remain UNKNOWN.
Dropped objects, blockage, perception mistakes and failed actions are recognized as
unestablished hypotheses, not turned into observed causes. Commands never prove
physical effects; repeated ambiguous command occurrences abstain. No action physics
for the public tasks or missing timestamp was invented. Original context and all
unparsed residue remain in the input/review artifacts.

| Source | Rows | Complete syntactic recognition | Partial recognition | No claims | Any factual subclaim | Hypothesis-only extraction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RoboFail/expert | 91 | 14 | 2 | 75 | 0 | 16 |
| RoboFail/GPT-3.5/REFLECT | 39 | 7 | 22 | 10 | 0 | 29 |
| CounterFactual/template | 620 | 536 | 32 | 52 | 174 | 394 |
| Total | 750 | 557 | 56 | 137 | 174 | 439 |

The 557/750 complete and 56/750 partial values are **syntax coverage, not successful
repairs or complete semantic understanding**. Only 174/750 (23.2%) have a factual
subclaim, all command-order statements in the template corpus. No factual explanation
claim was extracted from the 130 RoboFail examples. Hypothesis-only recognition does
not license a factual explanation. Relative to the old zero-coverage whitelist,
this is a working narrow interface with a substantial real-example limitation.

A 2,000-draw grouped bootstrap over 68 conservative episode/template/exact-input
alias components gives complete syntax coverage 74.27% [28.75%, 88.51%], partial
7.47% [1.66%, 23.97%], factual-subclaim coverage 23.20% [0.00%, 39.21%]. These wide
intervals expose template concentration; components can cross tasks and original
counterfactual episode linkage is unavailable. They are coverage intervals only.

| Method | Emitted factual slots | No factual output / 750 | Replacements | Rows with unresolved content |
| --- | ---: | ---: | ---: | ---: |
| B0 original | 174 | 576 | 0 | 193 |
| B1 generic fallback | 121 | 629 | 0 | 246 |
| B2 deletion | 76 | 674 | 0 | 728 |
| B3 regeneration | 3,574 | 0 | 0 | 0 |
| B4 selective repair | 129 | 621 | 53 | 707 |
| B5 both constraints disabled | 0 | 750 | 0 | 750 |

These are mechanical output counts, **not correctness, supported-retention or utility
scores**. B0/B1 may retain unparsed original prose; their low unresolved count cannot
mean it was checked. B3's zero unresolved fields describe regenerated ledger output,
not resolution of the original cause. Its complete supplied command sequence has
all original command-log order/presence information; no output-length cap or
E0-dependent evidence privilege is used. A true complete sequence receives semantic
credit for an original order fact in controlled evaluations. Do not mistake B5's
public abstention for proof that robot-action reasoning improves actual explanations:
its disabled model includes the simple literal command-log rule, and the public
adapter extracted no physical action-precondition claims.

For `CounterFactual/boilWater-8r5j2taz-autogen_wrong_order_c`, the original says
“put pot on fourth stove burner after turn on second stove burner.” B4 renders the
recorded opposite order: pot placement before burner toggle, explicitly without
claiming effects. For `heatPotato-qx972cwr-autogen_wrong_order_c`, B4 similarly reverses
the order subclaim and leaves the causal failure assertion unresolved. These are
**plausible ledger repairs awaiting independent semantic review**, not graded
natural-language successes. In `RoboFail/warmWater-6_gt_step_59_gt_exp`, “Wrong
perception: glass and mug” becomes a recognized hypothesis plus unparsed residue;
B4 abstains. A long explanation about a missing warm-water step also remains
unresolved. `representative_public_examples.json` preserves all contexts, extracted
clauses and exact outputs, including these failures. No grammar or weight was tuned
after these results to improve the numbers.

## Frozen blind annotation package

`review_subset_freeze.json` selects 55 examples before the Week 2 method evaluation:
first two salted-SHA rows per RoboFail task/origin and first one per counterfactual
task/template stratum, without coherence-label or outcome selection. Some strata are
sparse. The 76 source clauses appear in `review_blind.jsonl`, with complete original
observations, command prefix, source E/C/N labels/comments and candidate dependencies.
Independent reviewers must correct extraction before labeling each claim supported,
contradicted or undetermined, specify time/model dependencies and information worth
preserving. All adjudicated-label, reviewer and preservation fields are blank.

`review_provisional_not_gold.jsonl` contains machine suggestions and evidence links
separately, prominently marked unadjudicated. Existing public coherence labels and
comments help review but do not establish gold repairs. There were **no independent
human labels available**, no same-model judge and no scored NLP unsupported-assertion,
retention, damage, repair-accuracy or useful-diagnostic-content endpoint. Numerical
independence does not supply missing semantic annotation. These examples already
informed development; even later adjudication would not make them untouched tests.

## Matched simulator-oracle comparison

The same 595 frozen inputs cover 45 old task-parent seeds, 85 cells and seven
controlled explanation variants. There are 20 PickCube parents, 20 PushCube parents
and five privileged Lift preservation controls. Both conditions/variants remain in
each parent cluster. No new physical rollout or new recovery comparison occurred.
Truth is recomputed from raw physical positions, observed goals, recorded grasp
measurements and contact body names, plus the explicitly declared transport model.
These assumptions do not prove general robot physics or unique failure causes.

| Method | Unsupported / asserted factual atoms | Supported original retained / 1,185 | Informative / 595 | Damaged correct / 295 | No factual output |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 original | 215/1,400 | 1,185 | 415 | 0 | 85 |
| B1 generic fallback | 85/1,058 | 973 | 295 | 0 | 215 |
| B2 deletion | 0/1,185 | 1,185 | 415 | 0 | 180 |
| B3 regeneration | 0/3,465 | 1,185 | 595 | 0 | 0 |
| B4 selective repair | 0/1,315 | 1,185 | 425 | 0 | 170 |
| B5 both constraints disabled | 129/1,230 | 983 | 425 | 146 | 170 |

Unsupported means contradicted **or not established**, not merely contradicted.
B0's 215 comprise 130 false and 85 undetermined factual atoms; B1's 85 are
undetermined. B5's 129 are contradicted, occurring on 73 inputs. Hypotheses do not
inflate the factual-accuracy denominator. A correct input requires all parsed
factual claims true, no hypothesis and no unparsed residue. Damage means losing
supported original information or adding an unsupported assertion; exact wording
changes are reported separately. Informative means at least one oracle-established
fact, not a human judgment that the explanation is useful. No post hoc saliency or
utility score was invented.

Paired 95% percentile intervals use 2,000 fixed-seed task-stratified parent draws:

| B4 difference | Unsupported-input fraction | Original-fact retention | Informative-output fraction | Correct-input damage |
| --- | ---: | ---: | ---: | ---: |
| vs B2 | 0 [0,0] pp | 0 [0,0] pp | +1.68 [1.68,1.68] pp | 0 [0,0] pp |
| vs B3 | 0 [0,0] pp | 0 [0,0] pp | -28.57 [-28.57,-28.57] pp | 0 [0,0] pp |
| vs B5 | -12.27 [-12.94,-11.60] pp | +17.05 [15.70,18.40] pp | 0 [0,0] pp | -49.49 [-52.20,-46.78] pp |

B4 adds 130 true atoms versus deletion and ten informative outputs, but no retained-
original-fact advantage. B3 adds 2,150 true atoms beyond B4 with no extra factual
errors. Several intervals collapse because the same deterministic variants produce
identical within-task counts, not because generalization is certain. Full paired
comparisons with B0/B1, per-task counts and facts-per-input are in
`trace_paired_uncertainty.json` and `trace_metrics.json`. Sample size is not 595
independent robot trials. Nothing here changes the prior finding that the fixed
recovery selector ignores explanations; offline factual editing is not physical
recovery improvement.

## Mechanism controls and computational cost

Thirteen separately authored logical controls were frozen before outputs. Their
positive truth tables are inspectable in `controls_frozen.jsonl`; facts outside those
tables are unqualified, not separately classified as physical false versus unknown.
They are not released-language gold or additional robot trials. They cover correct
historical facts, stale facts at the wrong time, missing evidence, multiple plausible
causes, conflicting observations, correct no-repair input, commands without effects,
unanchored history, valid/blocked declared applicability, correct/incorrect command
order and ambiguous repeated commands.

B4 produces seven established factual outputs, no unqualified assertions, retains
all four supported original facts and damages 0/4 correct inputs. B2 has four
informative outputs; B3 has eleven, zero unqualified assertions and complete
retention (including sequence-to-order entailment). B5 has two informative outputs,
one unqualified assertion and damages 3/4 correct inputs. It wrongly rewrites a
correct historical open-fridge fact using the current closed-fridge observation,
and discards valid action applicability and correct command order. B4 abstains on
missing/conflicting evidence, ambiguous causes, unanchored history and repeated
command ambiguity. Shared constraints work on these designed logical cases;
regeneration uses them too, so they do not isolate a new selective-editing contribution.

| Method | Mean public method ms/input | Mean structured method ms/input |
| --- | ---: | ---: |
| B0 | 0.03075 | 0.06201 |
| B1 | 0.02795 | 0.05321 |
| B2 | 0.02656 | 0.05585 |
| B3 | 0.23731 | 0.23524 |
| B4 | 0.07030 | 0.21453 |
| B5 | 0.04420 | 0.19440 |

Single-pass `perf_counter_ns` timings exclude parsing, serialization and raw-source
I/O. They include method support bookkeeping; no warmup/repeat-based performance
claim is made. B4's smaller output is cheaper than full public regeneration in this
run, but it has no factual output on 621/750 rows. The shared comparison worker took
3.03 s wall / 2.85 CPU seconds including all populations and output I/O. Runtime
alone is not a scientific diagnostic-content advantage. The whole bounded ledger,
including raw-source audits and tests, is in `commands.jsonl`; peak RSS, exact wall,
CPU, bytes, conservative small-orchestration reserve and final commit are recorded
in `resources.json` / `completion_manifest.json`. No GPU training or new simulation
resource was used; the 4 h / 6 CPU h / 1 GB ceilings were respected.

## Independent verification and reproducibility

A second implementation imports no editor/support code. It independently reconstructs
raw-state facts, verifies every per-input numerical score, checks 2,975 B0–B4 outputs
against the sealed prior run, and recomputes all 25 paired intervals using bootstrap
multiplicity weights rather than concatenated rows. It also verifies source/frozen
hashes, all public originals, the blind package's empty adjudication fields, coverage
intervals and named negative controls. `independent_audit.json` records the result.
This is independent code-path numerical verification by the same unattended session,
not a separate human scientific review. The entire Week 1 sealed inventory and all
13 historical seal files are rechecked at finalization. Unrelated document moves,
`.gitignore`, `uv.lock` and previous evidence remain intact.

Validation passed: the focused adapter/core subset had 33 passing tests; the
complete suite had **382 passed, 4 skipped**. Ruff checking passed and all 191 Python
files passed format checking; `git diff --check` passed. Exact outputs are in
`validation.json` and bounded job logs. No workers are detached; finalization checks
the exclusive worker lock and confirms no campaign workers remain.

The compact local supervisor archive is W2/`supervisor_review.tar.gz`: source,
protocol/report, frozen review membership/clauses, provisional annotations, measured
tables, representative examples, audit, hashes and validation. Complete inputs and
all 8,148 six-method outputs remain in W2 (4,500 public + 3,570 structured + 78
controls); no raw logs/results are committed.

Reproduce into a **fresh** root from the final local commit and existing sealed
sources, never into W2:

```bash
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1
REPLAY_ROOT="results/explanation-repair-week2/replay-$(date -u +%Y%m%dT%H%M%SZ)"
uv run --no-sync python scripts/explanation_repair_week2_finish.py --root "$REPLAY_ROOT" --stage initialize
for stage in prepare run analyze audit; do
  uv run --no-sync python scripts/reboot_overnight_worker.py \
    --root "$REPLAY_ROOT" --name "$stage" --timeout 300 -- \
    uv run --no-sync python "scripts/explanation_repair_week2_${stage}.py" --root "$REPLAY_ROOT"
done
uv run --no-sync python scripts/reboot_overnight_worker.py \
  --root "$REPLAY_ROOT" --name validation --timeout 900 -- \
  uv run --no-sync python scripts/explanation_repair_finish.py --root "$REPLAY_ROOT" --stage validate
```

Read-only seal verification of this completed run:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python \
  scripts/explanation_repair_week2_finish.py \
  --root results/explanation-repair-week2/20261113T130926Z --stage verify
```

## Five scientific decisions

1. **Actual natural-language repair:** a narrow command-order interface now runs and
   proposes 53 replacements on released templates. General repair quality and even
   these repairs' semantic fidelity remain unvalidated. RoboFail factual extraction
   is still zero; parse/hypothesis recognition is not a correct repair.
2. **Advantage over deletion/regeneration:** the structured editor adds a small
   factual-completion benefit over deletion. No information/fidelity advantage over
   strong regeneration exists on these data; regeneration is strictly more
   informative on every structured input. Wording preservation is not diagnostic
   benefit. Human focus/usefulness was not measured.
3. **Action/time-specific advantage:** temporal/applicability constraints prevent
   errors versus the unconstrained ablation and on authored controls, but B3 shares
   those constraints. Public order checks are document reasoning, not validated
   robot-action physics. No distinct robot-reasoning contribution is isolated.
4. **Trustworthy labels:** raw-state truth is independently reproducible under stated
   sensor/model assumptions; authored controls have explicit limited truth tables.
   Public coherence labels are insufficient for repair evaluation. The 55-example
   annotation package has no independent adjudication, so NLP quality is unassessed.
5. **Feasible without a large LM:** bounded extraction/editing is computationally
   feasible with existing dependencies and no language model. Broad language
   competence and a distinct publishable contribution do not follow. The current
   approach lacks evidence for that distinction. Stop at this scientific boundary;
   do not add a heuristic, architecture, dataset, simulation campaign or manuscript.

---

## Historical Week 1 report (preserved)

# Explanation repair: first-session measured results

The authorized first session is complete: a working typed ledger, finite-menu editor,
renderer, deterministic baselines, public adapter and development-only outcome-linked
demonstration. **No advantage over the strongest evidence-only controls is established.**
The natural-language comparisons and downstream hypothesis remain incomplete. This is
a research prototype, not a manuscript or a publication-readiness decision.

Reviewed base: `c17d5a7e9a08626f6c7e63f73e6d94cbf6c5e71d`. Branch:
`research/evidence-preserving-explanation-repair`. Final committed source SHA and
resource accounting are recorded in `results/explanation-repair/20261113T091510Z/completion_manifest.json` and
`resources.json` after the scoped local commit. No push is authorized or attempted.

## What actually ran

All 750 pinned public rows were processed: 130 RoboFail (91 expert, 39 GPT/REFLECT)
and 620 CounterFactual templates. E/C/N and both original pair labels are unchanged.
There are 68 conservative alias groups; all rows are descriptive
development/interface data, with no train/test split. Counterfactual episode linkage
is unavailable, so shared template families are grouped across tasks. Imperfect SRL
was not used as truth. The four upstream Git blobs are byte-verified at revision
`730ba3200e84b6f1c140a4d7a6569f3a42fe1928` in `upstream_manifest.json`.

The simulator smoke used 20 old PickCube parents and 20 old PushCube parents, both
registered conditions, plus five nominal Lift parents: **45 task-parent seeds,
85 cells, 170 existing paired reference continuations**. All were used in the old
campaign and are DEVELOPMENT ONLY here. Seven fixed explanation variants yield
595 structured inputs. These repetitions are not independent physical trials.
There were **zero new physics rollouts, trained models, paid language calls or
GPU training jobs**. The exact same selected actions/outcomes were verified across
all preserved computational attempts; repeats never increase the sample size.

The declared privileged simulator state-observation projection is shared by every
method. It uses first/current state observations, the exposed contact flag and a
fixed 3 cm proximity predicate. This predicate is not task success; continuation
outcomes retain the old environment's unchanged success definition. Raw state,
fault conditions, caches and future outcomes are evaluator-only. Lift is a privileged
preservation control, not a third invented failure/recovery family. Grasp sensor and
recorder correctness remain trusted assumptions. The small transport precondition
model is an engineering abstraction, not proven necessary/sufficient robot physics.

## Public extraction and actual interface limits

| Source | Rows | Fully extracted explanations | Covered / total clauses | Extracted claims | Observation strings converted / supplied |
| --- | --- | --- | --- | --- | --- |
| RoboFail/expert | 91 | 0 | 0/103 | 0 | 307/314 |
| RoboFail/GPT-3.5/REFLECT | 39 | 0 | 0/67 | 0 | 141/143 |
| CounterFactual/template | 620 | 0 | 0/620 | 0 | 2249/2490 |

The final whitelist extracts **zero complete public explanations** and zero atomic
explanation clauses from these released rows. All unparsed spans are retained.
Earlier lexical matching falsely reported four full rows and six clauses because
it swallowed causal/temporal prose into object-name slots. Inspection rejected all
six; the erroneous parses and parser fix remain preserved. This is an explicit
parser failure boundary, not successful end-to-end language coverage or a
successful natural-language repair evaluation. Regeneration can still emit observed
facts from the public snapshot, but they are not gold repairs or established causes.
Observation conversion is also incomplete: unsupported observation strings remain
verbatim in the original public inputs and `public_observation_coverage.json`, and
are not silently treated as grounded facts. Any generated public explanation is
conditional on this partial projection; semantic repair quality is unassessed.
There are no gold repair labels, complete historical observations/action models or
independent natural-language semantic judge here. Editor support labels are not
used as gold quality labels. Original coherence labels cannot validate new repairs.

The initial cache search missed existing weights. A deeper hidden/symlink-aware
search found Pythia-160M; its offline CPU runtime was qualified and a bounded
language diagnostic was executed. The earlier absence-of-weights statements are
preserved and superseded by `language_backend_discovery.json` and `language/`.
The generic comparator remains an adapted parent fallback using our deterministic
checker, not the parent's trained NLI classifier.

## Bounded cached-model language diagnostic

The same cached Pythia-160M checkpoint, one-shot formatting example, greedy candidate,
full visible evidence and 96-new-token cap were shared across four conditions.
Inputs were frozen before generation: four current authored examples, one first-SHA
current trace case, and three first-SHA public examples per source (11 total).
The historical worked case remains in the structured study; this limited language
interface only accepts current observational facts, leaving other claims unresolved.
No input was truncated or skipped. There was no model or prompt search after outputs.

| Frozen language condition | Inputs | Valid complete JSON | Parse failures / token-cap reached |
| --- | --- | --- | --- |
| proposed_language_adapter | 11 | 0 | 11 |
| contradiction_reprompt | 11 | 0 | 11 |
| RARR_inspired_supplied_evidence | 11 | 0 | 11 |
| language_evidence_regeneration | 11 | 0 | 11 |

All 44 canonical outputs failed strict JSON parsing at the token cap. No complete
language repair was obtained; factual repair accuracy is **unassessed**, not 100%.
This does not demonstrate superiority of the structured editor over a competent
language editor. The [model card](https://huggingface.co/EleutherAI/pythia-160m)
describes Pythia as a research model not fine-tuned for instruction-following use.
The single-pass supplied-evidence RARR-inspired prompt is an explicitly limited
adaptation, not the original RARR retrieval/agreement/revision system.
Full Week2 language comparisons remain NOT_RUN; this 11-input diagnostic was run.

An input-contract review found fault-condition names in one trace case's source
paths. That first attempt is preserved in `language_attempt01_source_provenance/`.
The four tainted outputs were excluded, not hidden or replaced with another case.
Only source paths were removed for the same case; observation IDs/facts/times,
action model, initial text and all generation settings stayed fixed. Forty other
byte-identical valid-input outputs were reused, and only four calls were repeated.
There were 48 diagnostic generation calls plus one backend qualification call in
total, with all CPU/artifacts counted. Independent checks verify exact reuse, all
raw JSON classifications and unchanged model-file hashes. Raw outputs and input/
source/config hashes are retained; no cap or prompt was tuned to obtain a success.

## Independent structured factual-error / retention tradeoff

Counts below aggregate the declared development mixture, including controlled
corruptions and unedited deterministic templates. They are software/grounded-data
diagnostics, not an IID population error estimate. Unique entity/predicate/value/time
facts are counted rather than repeated words. Declared causal hypotheses are counted
separately from asserted factual errors. Zero factual outputs have undefined accuracy,
not perfect performance. Informative coverage and retention are separate endpoints.

| Method | Unsupported / emitted unique factual assertions | Supported original facts retained | Informative / inputs | Temporal errors | Correct-input exact text preserved |
| --- | --- | --- | --- | --- | --- |
| original | 215/1400 | 1185/1185 | 415/595 | 66 | 295/295 |
| generic | 85/1058 | 973/1185 | 295/595 | 0 | 295/295 |
| delete | 0/1185 | 1185/1185 | 415/595 | 0 | 295/295 |
| regenerate | 0/3465 | 1185/1185 | 595/595 | 0 | 0/295 |
| proposed | 0/1315 | 1185/1185 | 425/595 | 0 | 295/295 |
| no_temporal | 129/1315 | 1056/1185 | 425/595 | 129 | 222/295 |
| no_action_model | 0/1230 | 1112/1185 | 425/595 | 0 | 222/295 |

Task-stratified key controls (full variant/method rows remain in `independent_claim_metrics.json`):

| Task | Method | Unsupported / factual assertions | Supported original facts retained | Informative / inputs |
| --- | --- | --- | --- | --- |
| Lift | delete | 0/25 | 25/25 | 15/35 |
| Lift | no_action_model | 0/30 | 20/25 | 25/35 |
| Lift | no_temporal | 5/35 | 20/25 | 25/35 |
| Lift | proposed | 0/35 | 25/25 | 25/35 |
| Lift | regenerate | 0/105 | 25/25 | 35/35 |
| PickCube-v1 | delete | 0/680 | 680/680 | 200/280 |
| PickCube-v1 | no_action_model | 0/720 | 652/680 | 200/280 |
| PickCube-v1 | no_temporal | 84/760 | 596/680 | 200/280 |
| PickCube-v1 | proposed | 0/760 | 680/680 | 200/280 |
| PickCube-v1 | regenerate | 0/1960 | 680/680 | 280/280 |
| PushCube-v1 | delete | 0/480 | 480/480 | 200/280 |
| PushCube-v1 | no_action_model | 0/480 | 440/480 | 200/280 |
| PushCube-v1 | no_temporal | 40/520 | 440/480 | 200/280 |
| PushCube-v1 | proposed | 0/520 | 480/480 | 200/280 |
| PushCube-v1 | regenerate | 0/1400 | 480/480 | 280/280 |

The proposed editor matches deletion's supported-fact retention; regeneration also
retains those facts and has stronger coverage when the original explanation is
wholly unsupported or unparseable. Improvements over generic fallback do not
establish a new method advantage over these stronger equal-information controls.
Temporal ablation errors concern the explicitly different historical/current
intervals. Removing the action model loses valid declared-model deductions; this is
conditional applicability reasoning, not a unique cause or guaranteed recovery.

All 2380 sensitivity comparisons at loss weights 0/1/3/10 gave
0 operation changes.
The preservation penalty did no observed selection work in these independent menus;
its contribution is not established. No weights were tuned on evaluation outcomes.
All seven deterministic methods together took 0.5712
seconds across 595 structured bundles, excluding serialization/I/O,
source checks and audit. `runtime.json` contains each measurement. This aggregate
is not a measured per-method speedup or a language-model inference comparison.

## Five worked cases and comparator outputs

These are authored examples, separate from the raw-trace evaluation and natural
public explanations. Unknown does not mean failed; a command does not prove an
effect. Model deductions and observations carry separate proof bases/IDs.

| Authored case | Actual proposed text | Unresolved items |
| --- | --- | --- |
| correct-preserved | cube is grasped. | none |
| selective-replacement | cube is grasped. cube is not near goal. | none |
| unknown-battery-cause | The available evidence does not establish a specific failure explanation. | battery: No visible observation covers the claim interval; commands do not prove effects; cause: The supplied observations/model do not establish a unique physical cause |
| command-is-not-effect | cube is not grasped. Action 'transport' is blocked under the declared preconditions; this does not establish a unique physical cause. | none |
| temporal-and-conflicting | At t=0 s, cube is grasped. cube is not grasped. Some claims remain unresolved. | contact: Conflicting observations remain unresolved |

Actual baseline outputs on the same partially incorrect input:

| Method | Output |
| --- | --- |
| original | cube is not grasped. cube is not near goal. |
| generic | The available evidence does not establish a specific failure explanation. |
| delete | cube is not near goal. Some claims remain unresolved. |
| regenerate | cube is grasped. cube is not near goal. |
| proposed | cube is grasped. cube is not near goal. |
| no_temporal | cube is grasped. cube is not near goal. |
| no_action_model | cube is grasped. cube is not near goal. |

All 5,250 public method outputs, original labels and unparsed text are retained in
`public_outputs.jsonl` / `public_inputs.jsonl`; these are outputs, not certified gold
repairs. `repair_examples.json` gives actual source-linked simulator repairs,
support identifiers, unresolved items and their reused selected-action outcomes.

## Fixed-selector downstream demonstration

All conditions get the complete same projection, history, model, selector and exact
70-control candidate actions. The selector prioritizes the current shared sensor
slot. In this prototype it is fully determined without using explanation content.
Thus no explanation effect is identifiable: this is an interface/outcome-link
control, not evidence that repair improves recovery. Direct evidence and full
evidence/no-explanation controls are included; no sensor is hidden to create a gain.

| Task | Condition | Cells | Chosen recover | Selected successes | Continue successes | Harm / benefit vs continue |
| --- | --- | --- | --- | --- | --- | --- |
| Lift | nominal | 5 | 0 | 5 | 5 | 0/0 |
| PickCube-v1 | nominal | 20 | 0 | 20 | 20 | 0/0 |
| PickCube-v1 | offset002 | 20 | 12 | 17 | 8 | 0/9 |
| PushCube-v1 | misaligned | 20 | 0 | 0 | 0 | 0/0 |
| PushCube-v1 | nominal | 20 | 0 | 20 | 20 | 0/0 |

Proposed minus original/generic/deletion/regeneration/full-evidence/direct-evidence
success difference is exactly zero on every reused cell; there are no action
disagreements. This follows from the observation-dominant rule, not a confirmation
equivalence test. Any selected-vs-continue benefit belongs to the same existing
selector/action library for every condition. It cannot be credited to explanation
repair. No abstention occurred on these fully observed selected cells; separate
tests cover absent, conflicting and non-Boolean sensor values. Executed library
cost is 70 controls / 3.5 simulated seconds, not time to completion or new wall-time
physics execution. See `paired_recovery_comparisons.json` for the exact comparisons.

## Independent verification, corrections and limits

The separate raw-state/contact/time/outcome interpreter passed 85 cells, 170 actual old continuations, 595 structured variants, 4335 result rows and 10968 unique emitted factual assertions. It checked 2665 historical text qualifiers and 427 sealed historical members. Proposed soundness violations observed: 0. It does not call the editor's support checker to label assertions. This is independent numerical software, not an independent human annotation study or unrestricted causal truth.

Development01's structured numerical checks passed, but readable historical
statements initially lacked time qualifiers. That defect and its source snapshot
are preserved. Later refinements mark persistence-based inference explicitly,
retain conflict support IDs, separate qualified causal hypotheses from factual
error denominators, and abstain on non-Boolean sensor slots. All earlier attempts
remain local. `development_refinements.json` records them. No projection value,
seed, objective, precondition, action tape, selector choice or physical outcome was
changed to obtain a favorable result. The public grammar was tightened to reject
false positives, reducing coverage to zero; it was not broadened to manufacture a
linguistic success. An additional regression covers those parser failures.

Validation summaries (complete stdout/stderr remain in local `validation.json`
and bounded-worker logs):

- `uv run --no-sync pytest -q tests/test_explanation_repair.py`: 26 passed in 1.44s.

- `uv run --no-sync pytest -q tests`: 375 passed, 4 skipped in 25.73s.

- `uv run --no-sync ruff check src scripts tests`: All checks passed!.

- `uv run --no-sync ruff format --check src scripts tests`: 183 files already formatted.

- `git diff --check`: exit 0.

The four maintained optional physics tests are skipped in the main environment;
no physics code changed in this session. Tests are not scientific sample counts.
Historical evidence, `.gitignore`, `uv.lock`, and the initial unrelated documentation
moves are preserved. Large raw inputs, repeated outputs and logs remain excluded
locally and are not committed.

## Evidence, resource accounting and reproduction

Evidence root: `results/explanation-repair/20261113T091510Z`. Final development: `results/explanation-repair/20261113T091510Z/development05`. The exact source/config
freeze is `frozen_specification.json`; upstream pin/hashes, historical inputs,
independent metrics, paired choices, sensitivity and all job logs are retained.
`commands.jsonl` meters substantive jobs using the existing bounded worker.
`resources.json` and `completion_manifest.json` provide final wall/CPU/bytes/peak
RAM, commit, source hashes, preservation and zero-worker accounting after closing.
Unmetered interactive inspection/tool overhead is disclosed with a conservative
600 CPU-second allowance; remote tool/host reasoning CPU is not locally measured.
No model weights were downloaded. The public JSON/code and small isolated language
runtime dependencies were downloaded and are counted in the artifact footprint;
web/package transfer bytes are not individually metered. There was no GPU training
or inference and no paid language call. The four-hour / six CPU-hour / two GB
ceilings are enforced; no unused ceiling is treated as a reason to continue.

Actual development commands, run before sealing:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python scripts/reboot_overnight_worker.py --root results/explanation-repair/20261113T091510Z \
 --name final-development-comparison05 --timeout 600 -- uv run --no-sync python \
 scripts/explanation_repair_run.py --root results/explanation-repair/20261113T091510Z --attempt development05
uv run --no-sync python scripts/explanation_repair_audit.py --root results/explanation-repair/20261113T091510Z
uv run --no-sync python scripts/explanation_repair_language_audit.py --root results/explanation-repair/20261113T091510Z
```

The language generation/resume commands are recorded exactly in `commands.jsonl`.
They use `scripts/explanation_repair_language.py`, `--offline --no-project`, the
qualified supplementary Transformers4.57.6/tokenizers0.22.2/Hub0.36.2 runtime,
unchanged project CPU Torch, and `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.
`language/frozen_language_inputs.json` pins the cases, instructions, one-shot format
example, cap and runner/config hashes; `language/backend.json` pins model assets
and every supplementary dependency version. Reuse is verified in
`language/independent_audit.json`; source-path correction is in
`language_input_correction.json`. `post_batch_source_amendments.json` preserves the
original structured protocol and runner: only an appended language scope and an
incorrect output-manifest availability statement changed, with exact replacements
verified. Structured editor/selector logic and results did not change.

Sealed evidence refuses mutation. Repeating a batch requires a separately authorized
fresh unsealed root/clock and the pinned inputs; it must not overwrite an attempt.
The core CLI can read a saved worked bundle and write to a new temporary output:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python scripts/explanation_repair_run.py \
 --input results/explanation-repair/20261113T091510Z/development05/worked_inputs/selective-replacement.json \
 --output /tmp/explanation-repair-example-new.json
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python scripts/explanation_repair_finish.py --root results/explanation-repair/20261113T091510Z --stage verify
```

The fixed question remains unresolved as a substantive research contribution.
Parser/gold-repair limitations, unsuccessful bounded language outputs, missing full
language comparisons, and the uninformative
downstream contrast prevent a complete claim. [RARR](https://aclanthology.org/2023.acl-long.910/)
already edits for attribution while preserving content; the parent and HEXAR
overlap limits are recorded in the protocol. There is no proven literature gap.
The full Weeks 2–4 campaign, fresh independent seeds, held-out confirmation and
model-misspecification experiments were not authorized for this first session and
were not run; the bounded language diagnostic above was part of this first session. No new
topic, simulator, controller, architecture, detector or manuscript was substituted.
The supervisor retains continuation and publication decisions; simulation-only
evaluation is the target and no real robot is imposed as a later requirement.
