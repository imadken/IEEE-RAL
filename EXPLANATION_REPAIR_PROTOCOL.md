# Evidence-preserving robot explanation repair: first local session

## Week 2 continuation authority and frozen mechanism study

The new authority is the Week 2 supervisor contract, preserved in the new evidence
root. Start: `b46679401fdcc33f362bbf53a032d1b368c88181`; branch:
`research/explanation-repair-week2`. Limits are four hours wall, six CPU core-hours,
one GB new artifacts and zero GPU training. No simulator campaign, manuscript,
language-model training, new dataset/controller or automatic Week 3 work is allowed.
The prior session below is historical context; its sealed evidence stays immutable.

First, independently recompute the original 595 results from raw simulator traces.
Inspect B3's entire evidence set and verify B4's supported information is a subset;
do not penalize a true regeneration merely because its wording differs. The public
review membership is frozen before Week 2 method evaluation by task/origin and
counterfactual template family using immutable SHA ordering, without selecting on
method outcomes or coherence labels. These previously used rows remain exploratory.

`config/explanation_repair_week2.json` freezes B0 original, B1 generic, B2 deletion,
B3 evidence regeneration, B4 selective repair, B5 repair with both temporal and
action-model constraints disabled. Original objective weights stay unchanged. All
methods receive the same ledger, declared model, full supplied command prefix and
permitted deterministic candidate ceiling; actual costs are measured, not equalized
by weakening B3. No model calls or Pythia dependency are needed. B3 retains access
to all history and emits a complete supplied command sequence independently of E0.

The smallest adapter extension splits factual candidates, anchors object/action
arguments to the released observations/command vocabulary, and recognizes common
state/spatial, temporal-order, action-failure and causal forms. Unparsed residue is
retained. Recognizing a hypothesis does not establish its truth. Historical statements
without observed times use an explicit unknown clock and cannot borrow current facts.
Command-log presence/order/sequence are literal document deductions, never proof of
physical effects or unique causes. Ambiguous repeated occurrences abstain. No complete
robot action physics, missing timestamp, gold repair or causal outcome is invented.

Complete/partial syntactic extraction, grounded factual coverage, unknown-only
outputs, and unparsed text are distinct. Public claim annotations are provisional,
with blank independently adjudicated fields. A blind review sheet exposes original
context, existing coherence labels/comments and dependencies, but no method outputs;
machine suggestions live separately. No repair-quality metric is graded against
the editor's own support labels or these unadjudicated suggestions. Missing gold
labels must be reported, not filled by a same-model judge.

The original independent raw-state interpreter scores the 595 simulator-derived
inputs; authored negative controls are separate, with explicit oracle tables for
temporal displacement, missing evidence, ambiguous causes, conflicts, unchanged
correct claims, command/effect separation and declared applicability. They supplement
all 750 released rows. Retention counts unique supported propositions; a correct
complete command sequence entails literal order/presence/absence, giving B3 full
credit. Damage means unsupported added assertions or lost supported information;
cosmetic rewriting is separate. Diagnostic content has no post hoc saliency score:
report original supported facts and content categories, with human utility unassessed.

Paired uncertainty uses fixed 2,000 bootstrap draws grouped by task-parent on the
simulator data, stratified by task; public coverage uses whole conservative episode/
template-alias components, with limited grouping provenance explicitly disclosed.
No public factual-quality confidence interval is fabricated without adjudicated
claim labels. All controls, source hashes, failures, budgets and method outputs are
preserved. After the fixed comparisons, answer the supervisor's five scientific
questions even if no distinct advantage exists. Stop without Week 3 simulation.

Authority is the supervisor's attached fixed scope, copied into the local evidence
root. Reviewed/current starting HEAD is
`c17d5a7e9a08626f6c7e63f73e6d94cbf6c5e71d`; the branch is
`research/evidence-preserving-explanation-repair`. This session implements Week 1,
the public interface, deterministic comparisons and a development demonstration.
The four-week roadmap is not authorization for a confirmation campaign now.
Limits: four hours wall (including a five-minute startup allowance), six measured
CPU core-hours, two GB new artifacts, no paid APIs or GPU training. No new physics,
model installation, controller, detector, manuscript, human study or hardware work.

## Scientific question and direct comparisons

Can correction preserve supported diagnostic content, and can that preservation
help a fixed recovery selector? The combination is a candidate contribution, not
an established novelty claim. Finite enumeration and conditional logical support
are ordinary tools. Our implementation does not discover actual physical causes.

[Pramanick and Rossi, IROS 2024](https://arxiv.org/html/2410.00659), III-B/III-E,
use coherence classification, historical graphic selection, and a generic textual
fallback on contradiction; IV-D explicitly discusses richer refinement and
re-prompting. We adapt its fallback using our deterministic support checker,
without reproducing the trained NLI classifier or inventing missing times.
[RARR](https://aclanthology.org/2023.acl-long.910.pdf), sections 2–3, already
balances attribution/preservation and uses question-guided agreement followed by
local editing and an attribution report. Our finite ledger editor is not a RARR
reproduction. [HEXAR](https://arxiv.org/html/2601.03070), III/IV-B/VII, already
combines specialized component explanations, event/context selection and model
or template reasoning; recovery is discussed as a possible extension. None of
minimal editing, grounding, temporal checking or content preservation alone is new.
No absence-of-prior-work or superiority claim follows from this focused reading.

## Typed method and frozen choices

`src/dual_rec/explanation_repair/` separates schemas, support/editing and adapters.
Input contains observations/commands with IDs, exact object identities, predicates,
values, visibility, source and explicit intervals/clocks. Snapshot and plan-index
clocks are not seconds. A command cannot establish an effect. Observation
persistence is off unless explicitly declared; an action that may change a
predicate, or an unknown action, blocks carry-forward. Conflicts remain UNKNOWN.
No closed-world negation or cup/mug alias is assumed.

Claims distinguish observations, model implications, causal hypotheses and
recommendations. A model supplies preconditions and possible writes, not guaranteed
effects. Violated known preconditions justify only blocked applicability. Applicable
actions and recommendations do not guarantee recovery. Causal hypotheses need
evidence absent from this prototype and remain unresolved.

Each claim has at most four options: supported keep, at most one directly supported
replacement, explicit unknown, remove. We minimize total operation cost plus loss
of unique supported original facts. Frozen costs are keep=0, replacement=.5,
unknown=.8, removal=1, supported-fact loss=3. Groups of four are exhaustively
enumerated, with cross-group dependencies ordered and retained. Changed, missing or
cyclic references abstain. There is no silent explanation truncation. A renderer
uses templates, explicit historical times and evidence/rule IDs. Proof basis marks
direct observations versus model deductions (including conditional persistence),
and unresolved conflicts retain their support identifiers. Empty factual content produces a generic
fallback and explicit unresolved reasons. An unknown battery is not a failed battery.
Sensitivity uses loss weights 0/1/3/10 without outcome-based retuning. This additive
objective may simply recover deletion's fact retention; that equivalence is a result.

Methods: unchanged original; contradiction-triggered generic fallback; delete
unsupported clauses; evidence-only regeneration from the entire same history/model;
proposed; temporal ablation; action-model ablation. A permitted fixed language
backend is required for contradiction-aware re-prompting and RARR-style editing.
Absent one, both are NOT_RUN, with no synthetic language-model results.

Five worked development cases are frozen before running: (1) correct observed
grasp preserved; (2) wrong grasp plus a correct goal fact repaired selectively;
(3) unknown battery/cause explicitly unresolved; (4) a transport command does not
prove a grasp, while an observed violated grasp precondition blocks applicability;
(5) historical/current grasp changes and simultaneous conflicting observations
remain temporally separated/unresolved. These are authored software examples,
not independent empirical evidence.

## Public-data interface

Parent [repository](https://github.com/pradippramanick/coexp-iros24) revision
`730ba3200e84b6f1c140a4d7a6569f3a42fe1928` is pinned. Raw Git blobs and hashes are
local only. RoboFail includes expert and GPT-generated explanations; CounterFactual
contains template examples. Preserve E/C/N and both original pair labels verbatim.
These are coherence labels, not gold repairs, actual causes or recovery outcomes.
Do not use the supplied SRL as truth. A fixed conservative pattern adapter handles
only supported atomic syntax, records every unparsed clause and processes all rows.
Conditional/causal prose is not converted into unconditional observed facts.
No historical timestamps or complete action model are inferred from prose.

RoboFail aliases are grouped by episode prefix before `_gt_`/`_pred_`. Shared
counterfactual template families are grouped conservatively across tasks; exact
duplicate original inputs also share a group. Episode linkage for CF remains
unavailable. All rows in this first session are descriptive development/interface
data; there is no sentence-random train/test or untouched confirmation claim.
Missing gold repair/historical annotations are reported as missing, not replaced by
an editor self-score or same-model judge.

## Existing-trace demonstration and independent endpoints

Use the first 20 registered old confirmation seeds per PickCube/PushCube, both
conditions, and the first five Lift seeds as a nominal preservation control.
All were used previously and are now DEVELOPMENT ONLY. No seed is selected on
recovery outcomes. The old full-prefix qualification and paired action library
are reused unchanged; references/raw files must match the old seal.

The projection in `config/explanation_repair.json` is frozen before running:
first and checkpoint robot-facing observations, fixed .03m near-goal predicate,
and exposed grasp/contact flags. This is an explicitly privileged simulator
state-observation projection shared by every method: task-provided object poses,
grasp flags and the physics contact flag are not claimed to be real-camera
perception. Lift's non-observation grasp readout is separately labeled as a
privileged preservation control. Full raw state, controller
caches, fault labels and continuation outcomes are evaluator-only.

A fixed template generator produces unedited structured explanations from visible
evidence; controlled mixtures separately include partially wrong, unsupported,
stale-time, model and unparseable cases. These are not outputs of a learned model.
Natural unedited public explanations supply a separate, imperfect language stream.
Independent code reads the sealed raw traces and recomputes projected truth and
fact-level metrics without calling the editor's support checker. Unique supported
original facts, not repeated words, form the retention denominator. Report factual
errors, retention, temporal errors, correct-fact preservation, coverage, unresolved
cases and runtime separately. Unparseable text is unassessed, not zero-error prose.

The frozen selector is in the compact config. All explanation conditions receive
the same complete projected history and current observations, model and 70-control
candidate library. Include full-evidence/no-explanation and direct structured-evidence
controls. Observations take priority; the current rule is fully determined by the
shared sensor slot, so the demonstration cannot identify a benefit from explanation
preservation. It checks the interface and reused-outcome link rather than the
complete downstream hypothesis. Do not hide sensors to induce a gain.
Reuse only actual paired fresh-prefix outcomes of the
exact selected actions; abstention has no invented success. Cost is 70 controls/
3.5 simulated seconds for executed library actions, not time to completion. Report
nominal harm and disagreements without pretending reused outcomes are new rollouts.

No positive result triggers new experiments in this session. Finish the bounded
prototype, deterministic/public comparisons, tests and independent development
recomputation; report missing language and confirmation stages. Maintain only this
protocol and `EXPLANATION_REPAIR_RESULTS.md` as research documents. Source/tests and
compact config are committed locally; raw inputs/logs/results stay excluded through
`.git/info/exclude`. Preserve historical evidence, user moves, `.gitignore`, `uv.lock`.

## Cached-model discovery and bounded first-session language diagnostic

A deeper hidden/symlink-aware cache search found already present Pythia-160M weights
(revision50f5173d932e8e61f858120bcb800b97af589f46). The initial absence-of-weights
statement was wrong; it is preserved and superseded in language_backend_discovery.json.
A supplementary uv runtime uses Transformers4.57.6/tokenizers0.22.2/Hub0.36.2 with
the unchanged project CPU Torch2.5.1. No model weights are installed or downloaded;
only small runtime dependencies are isolated inside the evidence root. Project
pyproject/uv.lock, simulator stacks and prior evidence remain unchanged.

The fixed config/explanation_repair_language.json declares one greedy96-token
candidate for each of four conditions: proposed extraction adapter followed by
the same deterministic repair, contradiction-aware revision, single-pass supplied-
evidence RARR-inspired revision, and evidence-only regeneration. The same small
base language model, one-shot format example, full visible evidence and output cap
are shared. This is an honestly limited prompt adaptation, not a faithful RARR
research/search reproduction or a complete Week2 language comparison.

Before outputs, select four current authored cases, the first-SHA current partial-
flip trace case, and three first-SHA public rows/source (11 inputs total). Labels and
physical outcomes do not select them. This text interface only accepts current
observational facts; causal, historical and action-model clauses must remain
unresolved. The historical authored case remains in the structured evaluation.
No input is truncated: if any condition would exceed context, all conditions on
that input are explicitly skipped. Raw output, token-cap limits, parse errors and
empty coverage are retained separately. No prompt or model search follows outputs.
Semantic gold repairs are still unavailable for public language. The budget and
original session clock continue unchanged; no new physics or confirmation follows.
