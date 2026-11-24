# Budget-aware causal dependency verification: qualification report

**Decision: Case B / NO-GO for escalating the present incremental method to a
full research campaign. Publication-level novelty has not been established.**

The original LOGIV gate has a reproducible global-unknown blocking condition.
Simple relevance filtering substantially improves the declared symbolic
checkpoint comparison. The recovery-consequence scheduler **M3 adds no primary
benefit over M1**: goal-completion difference **0.00 percentage points**, paired
95% interval **[0.00, 0.00]**; query-count difference **0.000 [0.000, 0.000]**.
There are 2,016 paired primary decisions from **14 held-out parent instances**.
These intervals describe exact agreement in this sample, not population
equivalence or a physical safety guarantee.

All authorized stages A–F and the Case B exact comparison are complete. No
30-day campaign, manuscript, new physics scenario, paid model call, GPU physics/
training, GitHub authentication or push was performed. Publication is manual.

## 1. Registration, source versions and scope

Run directory: `results/monitoring-study/20261111T121002Z/` (abbreviated **RUN**
below). Branch: `research/budget-aware-verification`.

| Record | Immutable identifier |
|---|---|
| Reviewed base | `036b3b073543ff43816f29726d82b924a31cbbc8` |
| Initial registration and exact reference | `b5c28a9d228fa919e3e86ad7127e62fc62a71f5b` |
| Experimental implementation | `a7786cbe4f87ec7be28f2d501f2b4650c4aa9dd7` |
| Qualification seal commit | `fb8a4ed3ef4de69554f1a5a44d19c7363594ee36` |
| LOGIV source | `0ea7a7ff765016a33409c54572d733bed4503d4d` |
| LOGIV Git tree | `492bacf310612d007b2ecf926f7d1779c90cc018` |
| Public IPC corpus | `potassco/pddl-instances`, `cf19edf7c53d1540ddbb396c642595e0926ee552` |
| ALFWorld inspected source | `aaba6870f86c5be6a08a491f32a50b906227bc3e` |

[Protocol](MONITORING_STUDY_PROTOCOL.md) fixes RQ1–RQ4, splits, observation
regimes, methods, scoring, budgets, endpoints and stopping gates. No weights
were learned or tuned. The 27 files/data inputs in
[qualification_seal.json](results/monitoring-study/20261111T121002Z/qualification_seal.json)
remain byte-identical after qualification. Fourteen original LOGIV text/PDDL
blobs were independently size/Git-object checked before import; SHA-256 values
are in `RUN/logiv_source_sha256.json`. Upstream code was never patched.

Historical DUAL-REC evidence, its failed gates, the theory reassessment, original
adapters, dependencies and lockfile are preserved. The initial inventory covers
**408 prior files**, including ignored local raw evidence. This study is separate
from the terminated physical probing and preferred-repair projects.

## 2. Targeted prior-work check

This was a direct-equivalence/implementation check, not another topic search.

| Primary source | Verified positioning and consequence |
|---|---|
| [LOGIV v3, 2 Nov 2026](https://arxiv.org/abs/2610.40016v3) and [pinned verifier](https://github.com/Enqiao-Lu/LOGIV/blob/0ea7a7ff765016a33409c54572d733bed4503d4d/logiv/core/verification.py) | Preprint; main-conference acceptance not verified. Already supplies graph-supported verification, additional observations, UNRESOLVED and retained-plan repair. The study tests resource allocation around that existing machinery. Source-level unknown blocking does not establish its frequency in the published VLA benchmarks. |
| [GAVEL, 2609.19315v1](https://arxiv.org/abs/2609.19315v1) | Preprint; accepted venue not verified. Inspected methods validate graph rollouts, repair failures and maintain object-location beliefs. Its explicit generation budget is not this study's predicate-observation budget. Full trained-model reproduction was not attempted; no exact equivalence of the inspected scheduler was found. |
| [Predictive Vision-Language Monitoring, Frontiers 2026](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1870024/full) | Published 3 Aug 2026. Predicts condition risk and invokes fallback/replanning. Public code at `3a344025ff2984ca94fa4a04def4bf02e0dab672` requires ROS2/Gazebo/model services. It was inspected, not locally reproduced. Relevant-condition monitoring is already prior work. |
| [Stochastic Boolean function evaluation](https://www.cs.cmu.edu/afs/cs/user/srallen/www/papers/dnfeval.pdf) and established selective monitoring/active sensing | Paid adaptive tests to determine a Boolean decision are classical. Conformant checking, information gain, value of information and conjunction-test ordering are not new theoretical contributions. M4 and the Case B characterization remain reference reasoning. |

Full primary references, reading limits and the CONCUR/active-observation
comparators are retained in `RUN/compatibility/monitoring-positioning.txt`.
No fatal exact equivalence of every recovery-aware operational detail was
established; broad “budget-aware monitoring” novelty is nevertheless untenable.
The empirical gate is therefore M3 versus the strong M1 baseline.

## 3. Formal model and implemented methods

Let T be the finite declared CNF decision-state theory and K the timestamp-valid
partial Boolean evidence. Let W be **all** valuations satisfying T and K. For a
fixed deterministic continuation pi and goal g, forward execution defines
`f(s)=1` iff every action is enabled and the terminal goal holds. Certification
is VALID when W is nonempty and every f is 1; INVALID when W is nonempty and
every f is 0; UNRESOLVED when both labels occur; INCONSISTENT when W is empty.
An inconsistent model never licenses execution.

Exact conjunctive regression and complete DPLL implement that established
semantics. Independent exhaustive worlds and forward transitions check it.
T restricts decision states; it is not silently made a post-action invariant.
The public PDDL adaptation fixes static/equality truth but invents no physical
mutex constraints. Background-dependency closure includes the previous
`p iff q` counterexample: a proxy outside the plan's names can affect its validity.

| Method | Implemented behavior |
|---|---|
| M0 | Actual unmodified LOGIV **pre-action state gate**. Tracks all dynamic atoms; active observations use the common periodic view schedule. Current-action permission, global unknown resolution, failure and abstention semantics are preserved. This checkpoint projection is not a full published LOGIV execution reproduction. |
| M1 | Exact current-plus-retained-continuation certification; query the group covering the most unresolved full-model relevance-closure atoms per cost, with lexical ties. This is the required-obligation baseline. |
| M2 | Same fixed periodic view schedule and budget; nonadaptive allocation, then exact certification. Realized query count can exceed an early-stopping method's count. |
| M3 | Same semantics and recovery as M1; prioritize sums of `1 + remaining causal action descendants` of matching signed START supports, divided by cost. Future re-established supports are not counted as current supports. Constraint-connected proxies receive baseline weight 1. |
| M3 without consequence | Every weight is 1. It is deliberately the same algorithm as M1; query/decision equivalence was tested and audited. |
| M4 | Exact uniform-completion adaptive query-tree reference: maximize resolved VALID/INVALID classification, then minimize expected calls. Bounds: 12 unknown atoms, six groups, budgets 0–3. This is not a goal-completion/recovery-cost ceiling. |

All methods receive identical context, query menu, initial plan, budget and
recovery library. Hidden state occurs only in evaluator records and the sensing
callback; source review found no oracle-state access in scheduling. Strict
runtime schemas reject evaluator fields; input fingerprints and query budgets
were independently checked for every evaluated decision.

Queries are predicate-kind batches at simulated cost 1, revealing ideal symbolic
readings. A common cumulative evidence adapter retains still-valid unqueried
facts. Without it, upstream missing-value overwrites could create an artificial
batching disadvantage. This adaptation is explicit and identical for all methods.
No query count is presented as measured VLM/API latency.

Recovery uses the original LOGIV `Repairer`, a common conservative knowledge-state
BFS planner, and an exact universal validator. Limits are depth 8, 2,000 expanded
belief nodes **across repair rounds**, and 0.10 CPU seconds per planner attempt;
upstream repair retains its three-round limit. Candidate repair certification is
distinct from actual goal success under corrupted/stale evidence.

## 4. Original behavior established by execution

`RUN/phase_a_smoke.json` contains actual upstream calls, not a rewritten verifier:

| Case | Original output |
|---|---|
| Required true and no unknowns | Resolved, zero additional calls |
| Required false and no unknowns | Resolved false; execution reports PRECONDITION_FAILURE |
| Required unknown | Three additional calls, UNRESOLVED |
| Required true, unrelated tracked unknown | Three additional calls, UNRESOLVED |
| Required true, unrelated untracked unknown | Three additional calls, UNRESOLVED |
| Missing assessment overwrites a known tracked value | Unknown, unresolved after the allowed calls |
| Boolean visual/sensor conflict | Unknown, unresolved |
| Action-effect and terminal-goal branches | PASS, effect UNRESOLVED, and goal failure exercised |

Both source PDDL examples were parsed and transition-conversion checked before
comparisons. The later full common-method smoke on those examples has 192
episodes/4,608 rows. All its M4 rows are explicitly excluded: 576 by the six-group
limit and 192 by the two misspecification regimes. Exact comparisons instead use
eligible IPC instances; these exclusions must not disappear from denominators.

## 5. Public tasks, observation regimes and attempts

The registered IPC2000 Blocks and Logistics instances 1–4 per family are
development; 5–12 are qualification. Source selection was numerical, not based
on gains. All 26 IPC files are pinned and independently Git-blob checked. Two
Logistics qualification instances, 11 and 12, reached the fixed 30-second planning
timeout; both failures/logs remain in `RUN/benchmarks/`. No substitute was added.
Inference is restricted to that solved subset; timeout exclusions limit coverage.
The other 24 prepared tasks are 8 development, 14 qualification and 2 LOGIV smoke.

Native PDDL degeneracies such as stack(x,x) and drive(l,l) contradict LOGIV's
Operator effect checks. Every excluded grounding is listed; the shared action
library is the same accepted subset for all methods. No reference plan uses an
excluded grounding. Every retained nominal plan agrees stepwise between two
transition implementations and reaches the public goal.

Regimes: complete; random missingness 0.10/0.30/0.50; one missing predicate channel;
timestamped delayed evidence with known action writes invalidated; 0.05 persistent
bit corruption; and an unannounced existing applicable source-domain action with
0.30 missing pre-disturbance evidence. The latter is a **synthetic exogenous
selection using actual declared symbolic transitions**, not physical execution.
Noise and unannounced stale evidence are model-misspecification stress tests.
Structured channel loss is not a calibrated physical occlusion distribution.

Each nominal plan supplies first/middle/last checkpoints, four schedules, eight
regimes and budgets 0–3. One checkpoint episode receives a total budget B and
executes its selected continuation without further monitoring. Repeated schedules
and checkpoints are grouped by their parent instance.

| Stage | Episodes | Decision rows | Evaluated rows | Explicit M4 exclusions | Parent instances |
|---|---:|---:|---:|---:|---:|
| M0/M1/M2 development before M3 | 768 | 9,216 | 9,216 | 0 | 8 |
| All-method development | 768 | 18,432 | 16,916 | 1,516 | 8 |
| Held-out qualification | 1,344 | 32,256 | 29,364 | 2,892 | 14 |
| Two public example method smokes | 192 | 4,608 | 3,840 | 768 | 2 |

Qualification excludes 1,548 M4 rows above twelve unknown atoms and 1,344
misspecification rows. No deployed-method attempt was skipped or replaced.

## 6. Held-out results and confidence intervals

Primary subset: budgets 1–3 crossed with missing10/missing30/missing50/structured.
Each method has 2,016 decisions and 14 parent instances. Estimates average within
parent first; 2,000 bootstrap resamples preserve the two family sample sizes.
Goal/valid-continuation success is not awarded to abstention. Incorrect current
permission is separate from a safe current action followed by an invalid suffix.

| Method | Goal completion % [95% interval] | Queries [95% interval] | Abstention % | Incorrect current permissions |
|---|---:|---:|---:|---:|
| M0 gate adaptation | 38.99 [37.90, 39.98] | 1.767 [1.756, 1.779] | 61.01 | 0 / 786 grants |
| M1 required obligations | 85.96 [84.57, 87.45] | 1.041 [0.994, 1.083] | 14.04 | 0 / 1,733 grants |
| M2 periodic | 57.49 [55.65, 59.33] | 1.857 [1.857, 1.857] | 42.51 | 0 / 1,159 grants |
| M3 recovery consequence | 85.96 [84.57, 87.40] | 1.041 [0.994, 1.083] | 14.04 | 0 / 1,733 grants |
| M3 without consequence | 85.96 [84.57, 87.40] | 1.041 [0.993, 1.081] | 14.04 | 0 / 1,733 grants |

M1 minus M0: **+46.97 pp [44.74, 48.96]** goal completion and
**-0.727 [-0.773, -0.685]** queries per decision. These are improvements of the
simple relevance baseline under the common checkpoint adapter. They are not M3
novelty or a reproduction of the paper's robot scores. The independent bootstrap
uses a separate random stream and agrees within Monte Carlo variation.

M3 minus M1: goal, query count, abstention and simulated cost differences are
exactly zero on every primary pair. The registered meaningful-advantage gate
fails in both families. Neither the 0.05 success improvement nor the 0.5-query
reduction criterion is met. Zero-width sample error intervals are descriptive:
with zero event-bearing parents, the one-sided exact 95% bound is about 19.3%
for fourteen independent parents, not a 1% per-action safety guarantee.

The complete evaluation, including all metrics/denominators and per-family,
regime and budget intervals, is in
[full_table.csv](results/monitoring-study/20261111T121002Z/qualification/analysis/full_table.csv)
(536 method/stratum cells). The 96 paired strata are in
[paired_effects.csv](results/monitoring-study/20261111T121002Z/qualification/analysis/paired_effects.csv).
Machine summaries: `qualification/analysis/summary.json` and
`qualification/report_metrics.json`.

### Observation cost and total cost are different

The [SVG frontier](results/monitoring-study/20261111T121002Z/qualification/analysis/cost_validity_frontier.svg)
and [standalone PDF](results/monitoring-study/20261111T121002Z/qualification/analysis/cost_validity_frontier.pdf)
plot each regime's actual mean extra symbolic queries against valid continuation.
Plot inputs are retained. M1/M3/ablation curves overlap in accurate regimes.
Their per-query dictionary measurements are not physical sensing latency.

The simulated cost is queries plus executed symbolic actions. M1 exceeds M0 by
**3.303 [2.711, 3.853] units** on the primary subset because more task actions
actually execute. Thus the result is fewer observations and fewer abstentions,
**not lower overall execution cost**. Mean measured scheduler time is about
1.93 ms for M0, 2.33 ms for M1 and 2.32 ms for M3 there, including their Python
adapter/checking overhead. These values are hardware/session-specific.

## 7. RQ1 and Case B: why filtering was sufficient here

Across accurate qualification regimes, M0 spent **2,615/4,163 calls (62.8%)** on
groups with no unresolved atom in the full-model relevance closure. M1 and M3
spent **0/2,498** calls each on wholly irrelevant groups. Batched readings still
include unrelated or already known atoms: 70,839/73,944 M0 atom readings lie
outside the unresolved closure. These are model-relative conservative relevance
counts. Stress queries can expose false prior facts, so they are not included in
that “cannot change a justified decision” interpretation.

The bounded independent query audit examines the first 256 events per method,
then applies the twelve-unknown cap. It distinguishes zero immediate resolution
value from global irrelevance; XOR shows how two individually unhelpful queries
can jointly matter. Full-background proxy tests and that boundary case pass.

**Primary-scope limitation:** the accurate/missing/delayed regimes preserve a
nominally valid checkpoint state. They test certificate acquisition and
abstention efficiency, not successful detection of genuinely broken supports.
With only unit static constraints, conjunctive regressed obligations and disjoint
truthful query groups, every unresolved necessary group must be measured before
certifying a valid suffix. M1/M3 take `min(B,k)` calls and certify iff `B >= k`.
Changing their order cannot improve this endpoint. This is established Boolean
conjunction reasoning, not a new theorem or proof that recovery-aware ordering
never helps elsewhere.

The authorized Case B exact comparison additionally considers **all allowed
completions**, including invalid continuations, under the existing M4 uniform
prior. Its source-order first-64 selection was registered before that calculation.
It covers two existing Blocks development parents, 33 mixed-validity contexts
and 256 context/budget cases; it is not a broader benchmark sample.

| Budget | Expected resolved classification, M1 = M3 = M4 | Expected queries, M1 = M3 = M4 |
|---:|---:|---:|
| 0 | 0.484375 | 0 |
| 1 | 0.904297 | 0.515625 |
| 2 | 0.992188 | 0.611328 |
| 3 | 1.000000 | 0.619141 |

There is no strict classification or expected-query gap to the exact reference
on these cases. Four bounded contexts were checked by **228 complete frozen-policy
executions** over every allowed world. These are exact conditional calculations,
not success probabilities on physical robots. Evidence:
`RUN/exact_comparison.json`, `exact_comparison_audit.json`, registration and logs.

## 8. Robustness, positive secondary effects and negative cases

The following aggregates include all four budgets, 672 attempted decisions per
method/regime. False permissions use **granted decisions** as the denominator;
the full files also retain attempted-decision rates and separate invalid suffixes.

| Regime / method | Goal % | Mean queries | False current permissions / grants | Invalid suffix permissions |
|---|---:|---:|---:|---:|
| Delayed / M1 | 77.38 | 0.595 | 0 / 520 | 0 |
| Delayed / M3 | 77.38 | 0.595 | 0 / 520 | 0 |
| Noise05 / M0 | 92.86 | 0.000 | 4 / 628 | 4 |
| Noise05 / M1 | 67.86 | 0.000 | 24 / 480 | 24 |
| Noise05 / M3 | 67.86 | 0.000 | 24 / 480 | 24 |
| Invalidated / M0 | 8.48 | 1.390 | 4 / 149 | 92 |
| Invalidated / M1 | 19.35 | 0.771 | 90 / 231 | 101 |
| Invalidated / M2 | 26.19 | 1.393 | 37 / 217 | 41 |
| Invalidated / M3 | 20.24 | 0.783 | 90 / 237 | 101 |

Do not hide the descriptive positive: at invalidation budgets **2 and 3**, M3's
goal difference over M1 is **+1.79 pp [0.60, 2.98]** for each budget, 168 pairs/
14 parents. At budget 3 it also uses **+0.030 [0.006, 0.054]** queries. These are
secondary, unadjusted comparisons, below the registered success margin and in a
regime with substantial false permissions. They do not pass the primary gate.

The concrete witness
`blocks-strips-typed-05/5/0/invalidated`, budget 0, has an actual source-domain
`put-down b` transition while cached evidence retains `holding b=True`. M3
licenses `stack b a` as VALID, but its actual precondition is false.
[The complete witness](results/monitoring-study/20261111T121002Z/qualification/stale_support_counterexample.json)
is preserved. This is a failed truth-coverage assumption, not a soundness failure
of SAT relative to its input K. Prior certainty can stop M1/M3 before requesting
any fresh evidence; selective unresolved-only monitoring does not solve that.

All 516 actually invalid, initially UNRESOLVED invalidation decisions per deployed method remain
in the detection denominator. M1 detects 318, M3 313; their detected-case query
totals are 340 and 341, respectively. Undetected cases are retained. The stored
generic `detection_delay_queries` column by itself is not this filtered endpoint;
the stricter recomputation is in `report_metrics.json`.

M3 invokes recovery 313 times in invalidation and obtains 66 symbolically
certified repairs; actual task goal success is separately measured. Search limits,
unsuccessful attempts and corrupted-state failures remain in the records. No
correctness specification was weakened and no fault was redesigned after results.

## 9. ALFWorld and embodied feasibility

An isolated Python 3.12 environment executes released ALFWorld 0.4.2/TextWorld
1.7.0 without changing the repository environment. The pinned public archive is
36,507,267 bytes, SHA-256
`5df77ea759f2211a4106082839ddbbb790f1ba4e7d097ed732cf453f72aa36cf`.
Only the lexicographically first native game per train/valid_seen/valid_unseen
split was extracted. All three walkthroughs completed, and ten actual
look/inventory/examine calls were recorded. This is compatibility evidence,
not a diverse ALFWorld comparative qualification.

Full integration remains incomplete. Sensing changes `checked` facts; source
tasks contain ADL/conditional effects, and feedback wording need not identify
the intuitive Boolean predicate. The retained toggle example disproves a naive
“turn on” text-to-isOn parser. Runtime-visible records whitelist feedback; hidden
facts/admissible actions are reserved to the offline audit. No exposed-oracle
PDDL comparison is mislabeled as native ALFWorld sensing.

Native environment-step latencies of about 65–126 ms in these smokes are separate
from the ideal symbolic callbacks. No paid API latency was measured. Generic
ALFWorld download was avoided because it fetches a checkpoint; direct bounded
task assets and the exact isolated package freeze are retained in compatibility
evidence. The expanded dependency footprint exceeded an initial subtask estimate
but remained well below the global four-GB limit, with hardlinks deduplicated.

The qualified ManiSkill CPU/full-prefix infrastructure could support a future
limited monitoring demonstration without new failure physics. It currently lacks
a checked long-horizon symbolic skill/observation abstraction and measured query
costs; privileged pose/contact channels are not a perception guarantee. Snapshot
limitations remain. No new ManiSkill rollout was executed here; existing CPU
physics unit fixtures were run as regression tests. Embodied robotics validation
is still absent and blocks a publication-level claim.

## 10. Independent audit, engineering corrections and tests

The independent standard-library interpreter imports no scheduler or semantic
implementation. It recomputes transitions, goals, false permissions, final
abstentions including failed recovery, action counts/costs, sensing answers,
input fingerprints, denominators, ablation equivalence and oracle exclusions.
All four stage audits PASS with **zero mismatches**. Principal qualification
effects also agree with a separate parent-wise metric/bootstrap calculation.
Final scientific review is in `RUN/compatibility/monitoring-final-review.txt`.

Preserved engineering corrections include a pre-comparison consequence-count
formula fix, with the original prepared metadata retained and all plans/states
unchanged; a smoke-fixture post-action frame correction; explicitly excluded
degenerate groundings; and initial lint/format failures followed by passing
checks. The two planning timeouts remain failures. Original upstream, historical
science, the final scoring rule and qualification files were not adjusted to
obtain gains.

The complete final suite includes the historical 29 tests, exact-enumeration
cross-checks, dependency counterexamples, interface fairness, source-tamper
rejection, oracle limits, parent clustering, stale/noisy negative cases and
finalization/integrity checks. **91 tests pass; Ruff lint and formatting pass.**
Exact pass logs are retained at
`RUN/final-complete-tests.log`, `final-lint-complete.log` and
`final-format-complete.log`. Ruff covers active `src`, `scripts` and `tests`;
byte-preserved source/evidence snapshots under results are not reformatted.

## 11. Resource accounting and integrity

Resource capture: **2026-11-11T13:05:51.183270+00:00**. Elapsed campaign wall time **55.82 minutes**; aggregate agent-wall conservative upper bound **3.721 hours** (six-hour cap, including idle/wait time). Recorded substantive subprocess wall time **835.514 s**, CPU **1011.418 s = 0.28095 core-hours** (eight-core-hour cap). GPU physics/training **0 s**. Unique allocated artifacts before the seal **772,595,712 bytes**; conservative artifact upper bound including manifest metadata **774,595,712 bytes** (four-GB cap). Dependencies/cache hardlinks are counted once. Read-only bootstrap/editor/tool-service CPU is not metered; no measurements are invented for it. No detached research workers remain. Exact scopes, commands and exit statuses are in `resources.json`, `commands.jsonl` and the compatibility ledger.

`RUN/integrity.json` verifies all 408 historical hashes and all 27 qualification
seal hashes, plus completed independent audits and no active research worker.
`RUN/completion_manifest.json` seals every evidence file and current source/report
hash. Nested FastDownward timing is already included in its preparation worker;
it is not counted twice. A publication copy of a public HTTP log removes transient
signed download parameters, retaining the original hash and canonical URL.

## 12. Reproduction and handoff

No new repository dependencies are required for the monitoring evaluator. Restore
the small exact LOGIV source cache when absent:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync python scripts/monitoring_fetch_reference.py \
  --manifest results/monitoring-study/20261111T121002Z/logiv_source.json
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync pytest -q
```

Stored prepared tasks, plans, schedules and raw decisions permit independent
recalculation without reinstalling ALFWorld. For example, a fresh audit can use
`scripts/monitoring_audit.py --root RUN --split qualification --output NEW_PATH`;
existing evidence is never overwritten. Full reproduction commands/versions are
in the two command ledgers; no GitHub credentials or model checkpoints are needed.

Principal evidence paths under RUN:

- `qualification/{episodes,decisions}.jsonl.gz`, `status.json`, `audit.json`.
- `qualification/analysis/{summary.json,full_table.csv,paired_effects.csv}` and frontier plots.
- `qualification/{report_metrics.json,query_relevance.json,stale_support_counterexample.json}`.
- `benchmarks/{task_preparation.jsonl,planning_commands.jsonl,prepared_tasks.json,public_pddl_manifest.json}`.
- `phase_a_smoke.json`, `development/`, `baseline_development/`, `smoke/`.
- `exact_comparison_registration.json`, `exact_comparison.json`, `exact_comparison_audit.json`.
- `compatibility/` for primary-source positioning, native ALFWorld evidence,
  package freeze, public artifact hashes and independent final review.
- `commands.jsonl`, validation logs, `qualification_seal.json`, `integrity.json`,
  `resources.json`, `completion_manifest.json`.

**Final recommendation:** preserve the implementation and complete positive and
negative evidence for the principal researcher's review. The operational
inefficiency premise is supported; the simple M1 correction is useful in this
declared symbolic setting. A distinct M3 algorithmic contribution, robustness to
incorrect certainty, and embodied reliability are not established. This campaign
does not justify claiming IROS/RA-L readiness or continuing research autonomously.
