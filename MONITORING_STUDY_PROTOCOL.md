# Budget-aware causal dependency verification: frozen qualification protocol

Authorized source: supervised research contract supplied 11 November 2026.
Base `036b3b073543ff43816f29726d82b924a31cbbc8`; branch
`research/budget-aware-verification`; run `20261111T121002Z`.
This study does not reopen DUAL-REC or the rejected preferred-repair proposal.

## Questions and decision gates

RQ1 measures verification spent on information that cannot alter the current
action or retained continuation. RQ2 asks whether relevance filtering improves
limited-budget decisions. RQ3 asks whether recovery-consequence prioritization
adds value beyond that filtering. RQ4 tests missing, delayed, noisy, and invalidated
support evidence. These questions and the methods below remain fixed after any
negative outcome.

The primary method comparison is **M3 versus M1**, not M3 versus original LOGIV.
A meaningful pilot advantage requires either (a) at least 0.05 greater goal
completion with a paired 95% interval excluding zero and no greater mean query
count, or (b) at least 0.5 fewer queries with a paired interval excluding zero
and a goal-completion difference interval lower bound at least -0.01. Assess this
on budgets 1–3 and missing10/missing30/missing50/structured, pooled with equal
parent-instance weight, and check both domain families. Any inaccurate current-
action permission in these accurate-sensor regimes is a correctness failure to
audit. This is a qualification criterion, not a powered 1% safety noninferiority
test. No absence-of-errors confidence claim follows from zero observed errors.
If M3 and M1 match, complete the exact comparison and report Case B. Source or
interface obstacles follow Case D; an unsound algorithm follows Case E. No pivot,
physics failure design, paid API call or model training is authorized.

## Source and targeted positioning

LOGIV is frozen at `0ea7a7ff765016a33409c54572d733bed4503d4d`, Git tree
`492bacf310612d007b2ecf926f7d1779c90cc018`.
`results/monitoring-study/20261111T121002Z/logiv_source.json` records the exact
14 source/PDDL blobs, sizes and object hashes. They are cached externally to
the study code under `.cache/monitoring-upstream`, verified before import, and
never edited. A later source revision cannot silently replace them.

The targeted positioning check covers [LOGIV v3](https://arxiv.org/abs/2610.40016v3),
[GAVEL](https://arxiv.org/abs/2609.19315), and
[Predictive Vision-Language Monitoring](https://doi.org/10.3389/frobt.2026.1870024).
Generic selective monitoring, value of information, Boolean-function evaluation,
conformant reasoning and graph repair are prior art. No new logical theorem is
claimed. The final report records direct equivalences and implementation limits.

## Formal semantics and obligations

A finite Boolean model supplies all atoms, CNF decision-state constraints T,
deterministic grounded STRIPS actions and a fixed nominal plan/goal. Static PDDL
predicates and equality are fixed by the public initial model. No undocumented
physical mutex or sensor calibration is assumed. Dynamic facts not observed are
unknown. T restricts decision-state completions; it is not automatically an
invariant after actions. Supplied action transitions define subsequent behavior.

For evidence K, consider **every** model of T consistent with its Boolean values.
A continuation is VALID if every completion executes it and reaches the goal,
INVALID if no completion can do so, UNRESOLVED if both outcomes remain possible,
and INCONSISTENT if no completion exists. The last case always abstains. Exact
conjunctive regression plus complete SAT reasoning implements this established
definition; independent exhaustive enumeration checks small cases.

Current-action precondition validity and full retained-continuation validity are
distinct endpoints. A safe current action followed by an invalid suffix is not
an incorrect current-action permission. The previous p-iff-q locality example
must reject reasoning that ignores background constraints. Relevance closes
regressed obligations through **all** declared CNF dependencies. This closure
is conservative; membership alone does not prove a query has decision value.

## Common sensing and method interface

All schedulers receive exactly the same immutable task, nominal plan, evidence,
query menu, budget, constraints, costs, recovery library and stopping rules.
Actual state, missingness labels and future outcomes are evaluation-only fields.
Method input schemas forbid those fields. The evaluator supplies a sensing
callback; selection logic cannot read the callback's hidden state.

For the finite PDDL assessment, one query measures all grounded dynamic atoms of
one predicate kind, at simulated cost 1 and at most once per decision episode.
Each method has the same menu. These are **ideal symbolic readings of a declared
simulator state**, not real robot/VLM measurements. Dictionary-read latency is
measured separately and never called API latency. Initial evidence is free and
identical. Cumulative, timestamp-valid readings persist across queries for every
method: a restricted camera/view adapter must not erase all other known facts
each time it is called. Source LOGIV is untouched; this cumulative perception
adapter is explicitly part of the common experiment interface.

Budget B in {0,1,2,3} is the total number of additional calls in one checkpoint
episode. Afterwards the selected continuation is executed without further
monitoring; each checkpoint is a fresh paired decision, not a claim of a full
end-to-end LOGIV reproduction. Repeated checkpoints/schedules share their parent
task-instance identifier and are not independent tasks.

### M0: original LOGIV gate, checkpoint adaptation

Run the actual unmodified `Verifier.state_gate` with current action preconditions
and incoming conditions, all declared dynamic atoms tracked, the common
cumulative perception, and B additional observations. Since upstream observe()
has no query selector, its active calls use the same deterministic periodic view
schedule as M2. Preserve global-unknown blocking, missing/conflict updates and
known-false versus UNRESOLVED behavior. A resolved gate permits only when current
requirements hold; otherwise invoke common recovery. An unresolved gate abstains.
This is the source gate at a pre-action checkpoint, not all of LOGIV execution,
post-action monitoring or the published VLA benchmark. Native full verifier
branches are separately exercised in Phase A smoke tests.

### M1: strong required-obligation baseline

Certify the current action **and full retained suffix/goal** over all allowed
completions. While UNRESOLVED and budget remains, query the group containing the
largest number of unknown relevance-closure atoms per unit cost, breaking ties
lexicographically. Recheck after each query. Stop when resolved; INVALID may
invoke common recovery, VALID continues, other unresolved/inconsistent cases
abstain. This batching/relevance heuristic is a baseline, not new work.

### M2: fixed-budget monitoring

Use the periodic lexicographic group schedule, rotated by checkpoint index plus
schedule identifier, without evidence- or outcome-dependent query choices. Spend
the B calls (or the entire smaller menu), then apply M1's exact decision rule.
This is budget matched, not necessarily matched to adaptive realized query count;
report the latter explicitly rather than hiding the difference.

### M3: frozen recovery-consequence prioritization

Use exactly M1's certification, candidates, recovery and stopping rules. The only
change is query order. Compile the nominal retained plan using LOGIV's graph.
For each unknown regressed signed obligation, identify matching causal-support
edges from START in that graph. Its consequence weight is

`1 + number of remaining action nodes in the union of their causal descendants`.

Only matching signed initial supports count. A support established later is not
charged again merely because the fluent name occurs later. Goal-only initial
supports have baseline weight 1. T-connected proxy atoms have weight 1 unless
they independently have such an initial-support role. Query priority is the sum
of these weights over its unknown relevance-closure atoms divided by query cost;
ties are lexicographic. All constants are fixed at 1, with **no learned weights,
no parameter search and no qualification-based changes**. This is an interpretable
heuristic, not an optimality or locality theorem. It is a proxy for the consequence
of detecting a broken support, not measured physical recovery cost.

M3-minus-consequence replaces every weight by 1, leaving everything else intact.
It must be exactly equivalent to M1; this is an intentional ablation/control.

### Shared recovery opportunity

Use the existing upstream `Repairer` with a bounded planner and validator under
the common action library. The planner searches only transitions justified by
the available evidence; candidates are accepted only after exact universal
validation of the combined repair and retained suffix. No actual-state planner
or guessed completion may be used at runtime. Search is capped at 2,000 belief
nodes, depth 8, 0.10 CPU seconds per attempt; failures/timeouts are retained and
abstain. Upstream repair is capped at its original three rounds. Report invocation
and success separately. All methods have this identical opportunity when their
declared gate detects invalidity. A different gate may detect it at a different
time; that is an outcome to measure, not an unequal supplied recovery library.

### M4: exact small-instance observation reference

For truthful static queries, enumerate all evidence-consistent completions when
at most 12 unknown dynamic atoms and at most 6 query groups remain. With a uniform
prior on those completions, enumerate adaptive query trees to depth B and maximize
the probability of obtaining a resolved VALID/INVALID classification, breaking
ties by expected calls then lexicographically. This is an exact ceiling only for
that classification objective/prior, **not** for task success or recovery cost.
INCONSISTENT is not a correct resolved classification. No actual state selects
the policy. Excluded/oversized/noisy cases are counted, not silently sampled.

## Sources, splits and engineering fallback

Start with upstream `move_can_pot` and `build_bridge`, exclusively semantic smoke
tasks. The preregistered lightweight public assessment uses **both** IPC2000
Blocks STRIPS typed and Logistics STRIPS typed, canonical instances 1–12 from
`potassco/pddl-instances` commit `cf19edf7c53d1540ddbb396c642595e0926ee552`.
Instances 1–4 per family are development; 5–12 are qualification. Selection is by
public numbering, never by gain. Plan generation is bounded at 30 seconds per
task with the existing isolated TextWorld FastDownward package, with nominal
plans checked by both transition implementations. Unsupported/unsolved instances
remain in the registry with reasons. No replacements are selected after results.
LOGIV's Operator rejects groundings whose add/delete effects contradict (for
example stack(x,x) and drive(l,l)). Those signatures are logged and excluded
identically from the common action library; a reference plan using one would
make that task unsupported. This is a subset adaptation, not full native PDDL
action equivalence. No upstream constructor or effect rule is changed.
Checkpoints are distinct indices {0, floor(L/2), L-1} of each nonempty plan.
Each has four paired schedules numbered 0–3.

ALFWorld is pinned at `aaba6870f86c5be6a08a491f32a50b906227bc3e`; the released
TextWorld games and isolated dependency environment are checked independently.
Native look/inventory/examine can change `checked` state. A faithful comparative
adapter must model those effects and derive evidence from visible feedback,
rather than handing hidden facts to the scheduler. If that bounded integration
cannot be established, preserve actual native execution evidence and report
that comparative ALFWorld integration remains incomplete. IPC ideal-sensor
results are never relabeled as ALFWorld or physical robotics validation.
The two IPC families are broader symbolic evidence, not the required later
embodied robotics campaign. Inspect existing ManiSkill for a future limited
monitoring demonstration; launch **zero GPU physics/training** in this assignment.

## Locked observation regimes

Run complete accurate evidence; independent missingness 0.10, 0.30 and 0.50;
structured missingness; delayed evidence; 0.05 persistent observation corruption;
and externally invalidated supports. Every regime crosses all four budgets and
all methods on paired schedules. A SHA-256-derived PRNG key from task, checkpoint,
schedule and regime creates the schedule independently of method outcomes.

Random masks cover declared dynamic ground atoms, never static facts. Structured
missingness hides one whole predicate group selected uniformly by the fixed key,
representing a semantic observation channel absent rather than favorable named
faults. Delayed evidence was measured immediately before the last known prefix
action and becomes available at the current checkpoint; values of atoms written
since measurement are invalidated to unknown. At checkpoint zero there is no
earlier action and this reduces to accurate evidence. Active reads are current.

Noise flips each atom's reported Boolean with probability 0.05, persistent within
an episode and identical across methods/repeats. This is an explicit
**model-misspecification stress**, not a calibrated safety guarantee. The external
invalidation regime executes one uniformly selected applicable existing grounded
action other than the nominal next action, where available; the history retains
pre-disturbance readings with 0.30 missingness. This uses the domain's actual
declared symbolic transitions, but the exogenous selection is synthetic and is
not physical disturbance evidence. Cases with no alternative action are recorded.
Fresh active reads are accurate there. Known stale facts may survive if no query
revisits them; that is a substantive expected limitation to measure, not repair
through hidden-state access. Noisy/stale evidence can exclude the true state,
so conditional symbolic certification alone cannot imply true-state correctness.

## Measurements and statistics

Retain every task/episode/method attempt, false current-action permission,
retained-continuation validity, goal completion, justified/unnecessary abstention,
recovery invocation/success, query names/answers/count/cost and actual sensor/
decision CPU/wall latency. Simulated decision/execution cost is query calls plus
executed symbolic action count; it is not physical time. Report denominators
including failed planning, model inconsistency and recovery budget failures.

For RQ1, distinguish irrelevant **atoms** in a batch from wholly irrelevant query
calls. Exact decision irrelevance on bounded cases means conditioning on every
possible query answer leaves the validity partition unchanged; outside that
reference, report only relevance-closure-external counts as a conservative proxy.
No graph-name-only assertion is allowed. Detection delay is additional query calls
until a previously unresolved invalid continuation is classified INVALID; known
but wrong stale evidence and never-detected cases are reported separately.

Average repeated checkpoints/schedules within a task before inference. Report
paired cluster bootstrap 95% intervals with 2,000 resamples of independent parent
instances stratified by domain; fix analysis seed 71603. Per-family and per-regime/
budget tables accompany pooled effects. Bootstrap zero-width intervals after zero
events are descriptive, not rare-error confidence bounds; additionally report
exact zero-event bounds based on parent-instance event indicators. With only
eight qualification parents per family, precision/generalization are limited.
Primary comparison is preregistered above; all other comparisons are descriptive.
No multiplicity-adjusted confirmatory publication claim is made in this pilot.
Save machine-readable frontier tables and standalone plots, and independently
recalculate principal metrics from raw records without importing method code.

## Resource, integrity and finalization

Caps: six aggregate worker wall hours, eight measured CPU core-hours, zero GPU
physics/training, four GB new artifacts, no paid calls/large checkpoints. Stop
before limits. Every substantive worker command records argv, exit, measured wall/
CPU, source hashes and logs. Earlier read-only bootstrap/tool inspection is listed
separately where CPU measurements are unavailable; do not invent usage values.
Track isolated dependencies/archive storage too, avoiding duplicate hardlink
counts. No detached jobs may remain. Stop bounded heavyweight integration rather
than repeatedly repairing it.

The initial inventory hashes 408 historical files including ignored raw evidence.
All must remain unchanged, including AGENTS.md, prior reports, pyproject.toml and
uv.lock. New work lives in `src/dual_rec/monitoring`, corresponding tests/scripts,
this protocol, `MONITORING_GATE_REPORT.md`, and the new results directory.
Record deviations and failed engineering attempts; distinguish bug fixes from
method changes. Commit this registration before method comparisons, and seal
implementation/parameters before opening qualification outcomes. Finalize only
after tests, Ruff, independent audit, source/evidence manifests and local commits.
Publication is manual; no GitHub push or authentication attempt is permitted.

## Pre-qualification implementation record

Registration commit: `b5c28a9`. Original gate behavior and M0/M1/M2 development
measurements precede M3 implementation. The final M3 design is exactly the fixed
rule above; no weights were tuned. Eight development parents were evaluated;
the primary M3–M1 goal and query differences were both zero. This negative result
does not cancel held-out qualification or authorize a scoring revision.

The independent development audit checks all 18,432 rows (including 1,516 explicit
M4 exclusions), with zero mismatches. The complete repository suite passed
85 tests before qualification. Lint/format fixture corrections and the earlier
consequence-metadata correction are retained; none used qualification outcomes.

For the secondary exact query-relevance audit, retain all structural-closure
counts, and inspect the first 256 query events per method subject to twelve
unknown atoms. Selection is record order, never outcome-based. Equal possible
validity-label sets after every answer establish only zero *immediate* resolution
value; XOR demonstrates why this is not global irrelevance. The full-model closure
external to a query gives the stronger conservative irrelevance diagnostic.

The source-code commit and a SHA-256 qualification seal are recorded immediately
before the held-out worker is launched. Qualification instances 11–12 in Logistics
hit the registered 30-second planning limit; all fourteen other held-out instances
remain. No replacement or further integration search follows that exclusion.
