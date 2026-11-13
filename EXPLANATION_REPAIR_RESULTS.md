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
