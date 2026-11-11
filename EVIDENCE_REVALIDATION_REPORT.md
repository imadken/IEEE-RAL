# Evidence freshness and action permission: supervised qualification report

**Decision: Case B / NO-GO for advancing the current incremental SVR method.
The primary meaningful-improvement and safety evidence is inconclusive; the
registered advancement gate fails.**

SVR improves primary safe completion over the frozen periodic baseline B2 by
**1.63 percentage points [95% paired interval -1.63, +5.16]** and uses **1.288
fewer queries** per episode. The completion gain is below the five-point screen
and its interval crosses zero. The point reduction in unsafe permissions is
23.8%, but its per-attempt difference interval includes an increase and the
Logistics direction is adverse. Age-expiration B3 is more complete and safer at
the same available budget, while using more observations. Removing SVR's impact
weight slightly improves completion. These results do not establish the proposed
incremental contribution or statistical equivalence of methods.

Run directory: `results/evidence-revalidation/20261111T132101Z/` (**RUN** below).
Branch: `research/support-validity-revalidation`. The earlier M3 and DUAL-REC
NO-GO conclusions remain in force. This study evaluates only the authorized
support-validity revalidation extension; it authorizes no manuscript or subsequent
research campaign.

## Registration and reproducibility

The [frozen protocol](EVIDENCE_REVALIDATION_PROTOCOL.md) specifies the questions,
models, splits, methods, utility, primary endpoint and stopping rules.

| Record | Identifier |
|---|---|
| Reviewed base | `31f4ba82f7ef55df35834a23d140aa6438964265` |
| Initial local preregistration | `e95ef0fdbd3593d300c65fe0deb5259805613f08` |
| Frozen implementation | `3e210bc2a4e6e927e8c0ca1ba920f4820863020d` |
| Qualification seal | `RUN/qualification_seal.json`, 11 November 2026, 14:47:47 UTC |
| LOGIV source | `0ea7a7ff765016a33409c54572d733bed4503d4d` |
| Public IPC corpus | `potassco/pddl-instances`, `cf19edf7c53d1540ddbb396c642595e0926ee552` |

The seal fixes 21 source/input files before qualification outcomes are opened.
All selected parameters and the primary comparator are fixed using development
data. The preregistration commit is retained at the local-only ref
`refs/local-evidence/support-validity-registration-20261111`. Publication ancestry
starts from the unchanged reviewed base and excludes this session's generated
logs and raw results. Earlier reviewed commits are preserved.

The user's exact `.gitignore` bytes are retained without further edits. They are
the sole authorized exception to the initial historical inventory; all other
672 historical files, including prior results and lockfiles, must remain intact.
Raw evidence, detailed tables, figures and local seals remain under ignored RUN.
The committed [input configuration](config/evidence_revalidation_20261111.json)
contains source hashes, exact nominal input plans and frozen parameters rather
than generated outcomes. No GitHub authentication or push is attempted.

Input restoration was separately executed with
[revalidation_prepare.py](scripts/revalidation_prepare.py): all 31 parents and 33
public source files were restored and hash checked, and all model/library/initial/
goal/plan/nominal-state semantic fingerprints matched the actual experiment's
inputs. This restoration performs no plan search or parameter fitting. It uses
the existing pinned environment and small LOGIV reference cache:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync python scripts/monitoring_fetch_reference.py \
  --manifest results/monitoring-study/20261111T121002Z/logiv_source.json
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src uv run --no-sync python scripts/revalidation_prepare.py \
  --config config/evidence_revalidation_20261111.json \
  --root results/evidence-revalidation/reproduction
```

Source preparation originally attempted all public instances 13–24 in both
domains, before method outcomes. A native Fast Downward Logistics13 probe timed
out at 30 seconds and remains recorded. The fixed isolated Pyperplan 2.1 GBFS+hFF
preparation then solved 23 of 24 selected qualification parents. Public
Logistics19 has no initial airplane location and an unreachable cross-city goal;
it remains excluded without replacement. All retained plans agree stepwise
between the upstream and local STRIPS interpreters and reach their public goals.
Development uses only instances 1–4 per domain. Qualification has **23 new
independent parents: 12 Blocks and 11 Logistics**, exceeding the 20-parent target.

## Original failure and prior work

The preserved `holding(b)` witness was reproduced using the unchanged old M1
implementation. The external public action `put-down(b)` is applicable and
produces the recorded true state. M1 retains cached `holding(b)=true`, returns
VALID/CONTINUE at every budget 0–3 with zero queries, and grants `stack(b,a)`
although its true holding precondition is false. Re-observing holding changes the
verdict to INVALID/RECOVER. Independent recounting reproduces the old 90 false
current permissions / 231 grants / 672 attempts under invalidation and 24 / 480 /
672 under persistent corruption. These selection denominators are descriptive,
not causal comparisons against the original gate. Evidence is in
`RUN/provenance/revalidation-failure-reproduction.json` and its retained script.

The primary-method inspection took approximately eight minutes, below the
45-minute limit. Full access limits/source notes are local at
`RUN/provenance/revalidation-positioning.txt`.

| Primary work | Existing component and boundary |
|---|---|
| [LOGIV v3](https://arxiv.org/abs/2610.40016v3) | Boolean/unknown evidence, causal task graphs, observation requests and bounded repair already exist. Its upstream source is unchanged. |
| [Ferrando–Malvone, TOSEM, DOI 10.1145/3735130](https://doi.org/10.1145/3735130), accessible [author preprint](https://arxiv.org/abs/2408.11627v1) | Additive proposition relevance/payoff, knapsack observation selection and reactive residual monitoring already exist. Faithful visible projections do not establish correctness of stale/corrupt physical reports. ACM's journal text was access blocked; inspected methods are from the author preprint. RationalMonitor source `0a335a3553300aee905b906c65ed2f7d74a338c7` was inspected, not installed. |
| [Ernst et al., Frontiers 2026](https://doi.org/10.3389/frobt.2026.1847701) | Timestamped context, relevant observers and observer dependencies already exist. Dynamics-based validity duration and external-disturbance evaluation are deferred there. |
| [Catta–Ferrando–Malvone, ECAI 2025](https://doi.org/10.3233/FAIA250983) | Resource-bounded proposition sharing/windowed monitoring and conclusive-verdict results already exist under faithful trace projections. They do not give stale-report physical soundness. |
| Established belief-state planning and assumption monitoring | Bayesian history updates, known-action effects, survival-style uncertainty, value of information and risk-weighted sensing are standard. |

No novelty is claimed for these ingredients or for a risk-times-impact formula.
No directly equivalent complete implementation was established in the bounded
inspection. Any contribution therefore depends on a useful empirical distinction
against strong same-model freshness and belief baselines.

## Model, methods and fairness boundary

Runtime receives a trusted historical anchor, timestamped/source-tagged cached
readings, known successful robot actions, elapsed opportunities for hidden
change, the public action model and query menu. Current true state, event
identities, actual test rates, regime labels, seeds and outcomes belong only to
the evaluator. A finite joint Bayesian belief retains cache/current worlds and
persistent per-atom channel faults. Known actions transform beliefs and evidence
through their actual symbolic effects. Missing reports retain older information;
delayed reports carry measurement time. Repeated reports from one faulty channel
are never treated as independent confirmations.

Each pre-cache or post-cache interval permits at most one applicable state-
changing public action, with occurrence probability `1-(1-lambda)^gap`, uniformly
selected among applicable changing actions. This is a declared symbolic event
model, not arbitrary bit flipping or a physical disturbance experiment. No new
events occur during querying or the committed continuation. The complete joint
belief drops no mass and has an explicit 100,000-hypothesis computational bound.

Queries inspect individual dynamic ground atoms at unit simulated cost, at most
once per atom, under budgets 0–3. All methods share the same paired inputs, menus,
event tapes, channel faults and bounded established recovery. Recovery candidates
are cached by runtime knowledge rather than true state. Candidate certification,
acceptance and actual safe success are distinct outcomes.

| Method | Implemented decision/sensing policy |
|---|---|
| B0 | Actual unchanged original LOGIV pre-action state gate with cumulative sensing adapter. |
| B1 | Previously qualified M1 full-continuation verifier, retaining its cache-trusting semantics. |
| B2 | Periodic relevant refresh; development-selected interval 1. |
| B3 | Age-based expiration/refresh; development-selected expiry 0. History remains probabilistic evidence after hard-certificate expiration. |
| B4 | Refresh currently required predicates within the common budget. |
| B5 | Same joint dynamic belief, with standard myopic decision value of information over all informative queries, including off-plan proxies. |
| SVR | Same joint belief and terminal decision gate; query stale-value probability times fixed signed START-support causal impact, divided by cost. All impact coefficients are 1. |
| Ablations | `SVR_no_impact` sets impact to 1; `SVR_no_risk` sets risk to 1. |
| B6 | Exact nominal continue/abstain decision tree on a fixed menu of up to eight queries and an exact belief quotient of up to 32 states; larger cases are explicit exclusions. |

B2–B5 and SVR share posterior full-continuation permission threshold **0.85** and
the same recovery gate. B2/B3/B4 proactively refresh before this gate; B5/SVR
share adaptive confidence stopping. Realized query counts matter in addition to
budget equality. B6 may query beyond that practical confidence stopping rule;
its exact quotient preserves query likelihoods and nominal validity utility,
without dropping probability mass. It is neither a full-menu oracle nor a
ceiling for the full recovery/replanning problem.

B0 is the original *checkpoint pre-action gate*, not a reproduction of LOGIV's
full action-by-action monitoring/effect-checking execution loop. A chosen
continuation commits under one checkpoint budget; the evaluator audits every
granted action against true preconditions. One false grant permanently prevents
safe completion even if an environment guard blocks it. Claims about B0/B1 use
this explicit adaptation. The primary B2–SVR comparison uses matched full-suffix
decision contracts.

Development-only calibration estimates event hazard **0.097678916827853** from
100 changes in 1,024 opportunities with the registered smoothing; persistent
sensor-error prior **0.019872056621750376** from 875 errors in 44,032 bits. The
assumed missing probability is 0.10. Development chooses threshold 0.85,
period 1 and expiry 0 from the registered finite grids. At primary budget 2,
B2 has the highest development utility among B2–B5 and is frozen as **B\***.
Qualification never fits these quantities or changes the scoring rule.

Eleven separately reported regimes cross two checkpoints and eight schedules
per parent: no external change; hidden nominal/low/high event rates 0.10/0.03/
0.30; forced unrelated executable change; missing30; persistent sensor noise
0.02/0.10 without hidden events; delayed readings; recent revalidation; and a
known robot-action update. Transition and sensor stress remain separate.
Primary inference uses hidden_nominal, budget 2; schedules are averaged within
each parent before 2,000 family-stratified paired bootstrap resamples. Other
strata are descriptive and have no multiplicity adjustment.

Engineering corrections were made before qualification: exact endpoint
predictive probabilities, retaining fallback evidence when a cache reading is
missing, the legitimate anchor timestamp, and the exact B6 query quotient.
The timestamp correction was independently checked on 5,120 development paired
decisions; decisions/queries/counts were unchanged apart from timings. Old raw
development evidence and original source hashes remain local. Qualification
also records separate action-library and full-input fingerprints. No scientific
policy, parameter or sealed source is changed after qualification starts.

## Held-out results, controls and independent audit

The worker exited successfully after **4,048 episodes / 161,920 decision rows**.
All nine practical policies/ablations evaluated all 16,192 opportunities each.
B6 evaluated 8,768 rows and explicitly excluded 7,424 above its registered
32-state quotient bound; no mass was truncated. Thus **154,496 rows are
evaluated**. Development has 1,408 episodes / 56,320 rows, with 54,528 evaluated
and 1,792 B6 exclusions. No practical-method attempt was removed or replaced.

### Primary comparison and denominators

The primary subset contains **368 paired episodes, 23 parents**, at
hidden_nominal and available budget 2. Safe and actual completed tasks coincide
in this subset; both remain separate recorded fields. Coverage means at least
one task action granted, not successful execution or a safety guarantee.

| Method | Safe/actual completion / 368 | Unsafe episodes / 368 | Execution coverage % | Mean queries | False permissions / granted actions | Refused checkpoints | Rechecked current actions | Actually executed actions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 checkpoint gate | 284 | 75 | 100.00 | 0.000 | 75 / 7,905 | 0 | 0 | 7,830 |
| B1 cached obligations | 297 | 65 | 100.00 | 0.000 | 65 / 8,142 | 0 | 0 | 8,077 |
| B2 periodic, frozen B* | 243 | 21 | 72.01 | 2.000 | 21 / 6,445 | 103 | 134 | 6,424 |
| B3 expiration | 260 | 9 | 74.18 | 2.000 | 9 / 6,937 | 95 | 368 | 6,928 |
| B4 current conditions | 251 | 8 | 71.20 | 1.761 | 8 / 6,662 | 106 | 368 | 6,654 |
| B5 belief/VOI | 234 | 15 | 68.21 | 0.712 | 15 / 6,134 | 117 | 91 | 6,119 |
| SVR | 249 | 16 | 73.10 | 0.712 | 16 / 6,629 | 99 | 189 | 6,613 |
| SVR without impact | 251 | 16 | 73.64 | 0.701 | 16 / 6,717 | 97 | 163 | 6,701 |
| SVR without risk | 249 | 17 | 73.37 | 0.910 | 17 / 6,615 | 98 | 201 | 6,598 |

Permissions count each action in a committed continuation. A checkpoint refusal
counts one refused pending action, not every hypothetical future action.
`rechecked_actions` counts checkpoints querying a current precondition.
The difference between granted and actually executed actions is retained:
environment guards blocking a false permission do not make it safe. Four SVR
authorized continuations fail to complete without a false precondition grant;
coverage is therefore not interchangeable with completion plus unsafe episodes.

| Canonical primary SVR minus B2 endpoint | Difference [95% paired interval] |
|---|---:|
| Safe task completion | +1.63 pp [-1.63, +5.16] |
| Unsafe permissions per attempted episode | -1.36 pp [-2.99, +0.27] |
| Mean parent error / granted-action ratio | -0.136 pp [-0.258, -0.023] |
| Execution coverage | +1.09 pp [-2.72, +4.89] |
| Query count | -1.288 [-1.359, -1.217] |
| Registered realized utility | +0.1012 [+0.0140, +0.1910] |

SVR saves **474/736 B2 queries (64.4%)**. Its pooled false-action ratio is
16/6,629 = 0.241%, versus 21/6,445 = 0.326%; the inferential endpoint above
instead averages each parent's conditional ratio. Neither conditional ratio
is a causal safety comparison across different granted subsets. The per-attempt
error interval fails the required exclusion of zero even though the point
reduction is 23.8%. Utility improves under the registered reward, but utility
alone is not the advancement rule. Both registered screening routes are false.

The following per-domain effects use the canonical primary bootstrap; each
domain has 16 episodes per parent.

| Domain | Parents | SVR / B2 safe tasks | Safe difference pp [95% interval] | SVR / B2 unsafe episodes | Unsafe difference pp [95% interval] | Query difference |
|---|---:|---:|---:|---:|---:|---:|
| Blocks | 12 | 149 / 149 | 0.00 [-3.65, +4.17] | 5 / 12 | -3.65 [-6.25, -1.56] | -1.417 |
| Logistics | 11 | 100 / 94 | +3.41 [-2.27, +9.09] | 11 / 9 | +1.14 [-1.14, +3.41] | -1.148 |

Thus the aggregate risk reduction conceals an adverse Logistics direction; the
domain-consistency gate fails. Domain conditional-risk intervals also permit a
Logistics increase. This is not evidence that the population methods are equal.

### Other practical baselines and ablations

All comparisons were required before qualification; none replaces frozen B2 as
the primary comparator. The intervals below are descriptive paired intervals
without multiplicity adjustment.

| SVR minus comparator, primary stratum | Safe completion pp [95% interval] | Unsafe episodes pp [95% interval] | Mean extra queries |
|---|---:|---:|---:|
| B3 expiration | -2.99 [-5.16, -0.54] | +1.90 [+0.27, +3.53] | -1.288 |
| B4 current refresh | -0.54 [-2.99, +1.90] | +2.17 [+0.54, +3.80] | -1.049 |
| B5 belief/VOI | +4.08 [+1.90, +6.25] | +0.27 [0.00, +0.82] | 0.000 |
| Without impact | -0.54 [-1.63, 0.00] | 0.00 [0.00, 0.00] | +0.011 |
| Without risk | 0.00 [-2.45, +2.45] | -0.27 [-1.09, +0.54] | -0.198 |

The B5 completion improvement is a positive secondary result at equal realized
sensing, but is below the five-point screen and has one additional unsafe
episode. The impact ablation does not support the claimed dependency-weighting
increment. B3/B4 use more sensing, so their safety/completion advantage is a
tradeoff at matched available budget, not a claim of dominance at identical
realized cost. No threshold, hazard estimate, score or primary comparator was
retuned to qualification.

B6's primary eligibility is only **136/368 episodes from 11 parents**, with
107 safe completions, three unsafe episodes, 110 covered episodes, 26 refusals,
134 queries, 2,580 action grants and 2,577 executed actions. Its mean-parent
safe estimate is 78.98%, coverage 80.68% and queries 0.989 on this restricted
subset. These are not comparisons to the full 23-parent practical-method
cohort or a full recovery ceiling. Full exclusions by domain/regime/budget are
local in `qualification/analysis/reference_exclusions.csv`.

### Robustness, negative controls and calibration

Each row below has 368 attempted episodes per practical method at budget 2.
Cells are **safe completion % / unsafe episode count / mean queries**.
Transition and sensor regimes are separate; they are not averaged into a single
favorable score.

| Regime | B2 | B3 | B5 | SVR |
|---|---:|---:|---:|---:|
| No external changes | 73.91 / 0 / 2.000 | 84.78 / 0 / 2.000 | 81.52 / 0 / 0.793 | 87.23 / 0 / 0.802 |
| Hidden low, lambda .03 | 72.55 / 5 / 2.000 | 80.16 / 2 / 2.000 | 74.73 / 5 / 0.769 | 79.89 / 6 / 0.777 |
| Hidden nominal, lambda .10 | 66.03 / 21 / 2.000 | 70.65 / 9 / 2.000 | 63.59 / 15 / 0.712 | 67.66 / 16 / 0.712 |
| Hidden high, lambda .30 | 54.35 / 45 / 2.000 | 57.07 / 17 / 2.000 | 44.57 / 33 / 0.560 | 45.92 / 40 / 0.563 |
| Unrelated event control | 73.91 / 0 / 2.000 | 84.78 / 0 / 2.000 | 98.64 / 0 / 0.668 | 87.23 / 0 / 0.802 |
| Missing30 | 54.89 / 15 / 2.000 | 52.45 / 13 / 2.000 | 55.16 / 12 / 0.927 | 58.15 / 12 / 0.929 |
| Persistent noise .02, no events | 72.83 / 0 / 2.000 | 83.97 / 0 / 2.000 | 80.71 / 0 / 0.807 | 86.41 / 0 / 0.853 |
| Persistent noise .10, no events | 62.77 / 10 / 2.000 | 72.55 / 9 / 2.000 | 70.92 / 6 / 0.766 | 71.20 / 6 / 0.889 |
| Delayed cache-epoch readings | 34.78 / 9 / 2.000 | 34.78 / 9 / 2.000 | 34.78 / 9 / 0.000 | 34.78 / 9 / 0.000 |
| Recently revalidated | 100.00 / 0 / 0.000 | 100.00 / 0 / 0.000 | 100.00 / 0 / 0.000 | 100.00 / 0 / 0.000 |
| Known robot action | 100.00 / 0 / 2.000 | 100.00 / 0 / 2.000 | 100.00 / 0 / 0.000 | 100.00 / 0 / 0.000 |

No-change SVR still unnecessarily abstains on 47/368 episodes under the
conservative learned event model. Recently measured conditions avoid redundant
SVR sensing and all complete. Known-action beliefs update correctly with zero
SVR queries; successful outcomes are not obtained by merely aging old values.
The unrelated control contains **160 actual eligible unrelated transitions and
208 retained no-eligible cases**; it must not be described as 368 executed
disturbances. B5's 98.64% completion versus SVR's 87.23% here shows a strong
belief baseline can use informative observations outside SVR's relevant-support
menu. It is a further boundary of the targeted heuristic.

The primary 71 episodes with wrong relevant cached claims contain 129 such
claims. Direct fresh correction detects 34 episodes for SVR and leaves 37
undetected, versus 26/45 for B2 and 22/49 for B5. Conditional detected-case query
delay is 1.029 for SVR, 1.538 for B2 and 1.045 for B5; undetected episodes remain
in the denominator and have no invented finite delay. These are query counts,
not physical detection latency. All 90 noise02 and 274 noise10 episodes with a
wrong relevant cached claim lack a direct correct re-observation: the same
persistent bias survives querying. Posterior inference and direct detection are
different mechanisms.

An independent supplemental calculation stratifies nominal/low/high event data
by actual transitions and relevant-cache correctness. In the nominal regime,
265 episodes have no transition, 32 have an event with accurate relevant cached
claims, and 71 have an event with wrong relevant cached claims. The corresponding
low-rate counts are 332/15/21; high-rate counts 144/65/159. Accurate cached claims
do not imply a valid nominal plan. Method-dependent same-value/unqueried-false
controls retain their own selection denominators and are not causal contrasts.
All stratum/control parent means and counts are local at
`supplement-qualification/{summary.json,stratum_parent_means.csv,control_parent_means.csv}`.

| Nominal event stratum | Episodes | SVR / B2 safe completions | SVR / B2 unsafe episodes | SVR / B2 abstentions |
|---|---:|---:|---:|---:|
| No actual transition | 265 | 236 / 206 | 0 / 0 | 29 / 59 |
| Event, accurate relevant cached claims | 32 | 13 / 18 | 0 / 0 | 19 / 14 |
| Event, wrong relevant cached claims | 71 | 0 / 19 | 16 / 21 | 51 / 30 |

The pooled completion gain comes from fewer refusals in unchanged situations,
not improved safe completion once relevant cached claims actually became wrong.
The latter stratum's lower SVR error count accompanies substantially more
abstention. These evaluator-defined descriptive strata have varying parent
support and do not constitute new independent or randomized causal comparisons.
At high hazard the pooled SVR-minus-B2 safe-completion difference is
**-8.42 pp [-13.04, -3.80]**, an additional robustness failure.

Calibration diagnostics use exactly one initial risk vector per episode, not
duplicate method/budget rows. There are 5,000 dynamic cached-claim labels per
regime, clustered within the same 23 parents. These fact-level summaries are
descriptive and were not used to refit the model.

| Regime | Mean predicted wrong-value risk | Observed wrong-value frequency | Brier score |
|---|---:|---:|---:|
| Hidden low | 2.473% | 0.940% | 0.009899 |
| Hidden nominal | 2.480% | 2.580% | 0.023156 |
| Hidden high | 2.512% | 5.700% | 0.047690 |
| Noise .02 | 4.315% | 1.960% | 0.002490 |
| Noise .10 | 10.893% | 9.640% | 0.009197 |
| Known action | 0.000% | 0.000% | 0.000000 |

Under high hazard, the lowest predicted-risk bin averages 1.850% while its
observed wrong-value frequency is 4.126% (4,847 claims). This is concrete model
shift miscalibration, not a reason to fit qualification hazard rates.

Fixed-rule failure witnesses in the supplemental summary preserve both
mechanisms. For B2, `blocks-strips-typed-13/14/4/hidden_high` queries unchanged
clear(d)/clear(h), then falsely grants unstack(a,g); clear(a)/on(a,g) each had
estimated risk about 0.04645. For SVR,
`blocks-strips-typed-13/28/6/hidden_high` contains executable pick-up(c), then
stack(c,e). SVR invokes recovery with zero queries and accepts put-down(c), whose
holding(c) precondition is actually false. Wrong relevant claim risks include
0.09768/0.02442/0.09768. This is a belief/recovery-admission failure under model
shift, not proof that one selected atom or the query score alone caused it.
Same-value replies and false cached facts never rechecked also have retained
fixed-rule witnesses. The fallback witness search was unnecessary.

### Recovery, runtime and frontiers

| Primary method | Recovery invoked | Candidate certified | Candidate accepted | Actually successful | Accepted execution failures |
|---|---:|---:|---:|---:|---:|
| B0 | 21 | 21 | 21 | 14 | 7 |
| B1 | 36 | 36 | 36 | 27 | 9 |
| B2 | 58 | 51 | 36 | 33 | 3 |
| B3 | 71 | 42 | 27 | 26 | 1 |
| B4 | 69 | 39 | 24 | 23 | 1 |
| B5 | 68 | 28 | 11 | 9 | 2 |
| SVR | 70 | 28 | 11 | 9 | 2 |

Certification is relative to runtime evidence; it does not establish physical
truth. SVR's other 42 invoked repairs return no certified candidate under the
common bounded planner; 17 certified candidates fail its posterior acceptance
gate. Candidate reuse avoids different repairs for identical runtime knowledge.
Cold planning and lookup times remain separate: their observed values depend on
the fixed method order/cache reuse and should not be read as method-specific
planning speed rankings.

Mean primary scheduler overhead is 6.62 ms for SVR, 37.16 ms for B5 and 5.05 ms
for B2, plus a common 1.97 ms initial belief build. Mean synthetic sensing callback
time is about 0.007 ms for SVR and 0.015 ms for B2; these are dictionary operations,
not robot-camera latency. Per-method solver, sensor, cold-recovery and lookup
timings, counts and uncertainty are in the detailed local tables. Held-out worker
wall/CPU were **2,571.270 / 2,570.666 seconds**.

The full risk-versus-coverage frontier and safe-completion-versus-query frontier
are saved in `qualification/analysis/` as SVG and PDF with numeric inputs in
`frontier_inputs.csv`. Points are budgets 0–3, with separate panels for all eleven
regimes. B6 curves use only its eligible subset; conditional risks are selected
parent means, not causal or full-population safety estimates. Original generated
figures are preserved; presentation-only readable copies separate the title and
legend and use nonnegative risk axes without changing numeric inputs.

Local figure links: [risk/coverage SVG](results/evidence-revalidation/20261111T132101Z/qualification/analysis/risk_coverage_frontier_readable.svg),
[PDF](results/evidence-revalidation/20261111T132101Z/qualification/analysis/risk_coverage_frontier_readable.pdf),
[safe-completion/query SVG](results/evidence-revalidation/20261111T132101Z/qualification/analysis/safe_completion_query_frontier_readable.svg),
[PDF](results/evidence-revalidation/20261111T132101Z/qualification/analysis/safe_completion_query_frontier_readable.pdf).
These files remain intentionally local, so publication of this branch distributes
the report's essential tables and reproduction code rather than generated figures.

### Independent verification

The standalone stdlib auditor imports no scheduler/belief/experiment code. It
recalculates source event tapes, persistent/missing/delayed sensor responses,
input/action-library fingerprints, query budgets, actual forward transitions,
goal completion, grants/errors, calibration labels and detection denominators.
Both development and qualification audits **PASS with zero mismatches**.
Qualification verifies all 4,048 episodes and 154,496 evaluated rows while
retaining all 7,424 reference exclusions.

A further independent review re-executes forward checks on all **736 primary
method decisions / 368 matched pairs**, recomputes ten paired parent means and
matches audit/analysis point estimates within `1e-12`. All 21 sealed files and
raw/selection hashes match. The independent stdlib bootstrap uses a different
random stream from the analysis's key-derived NumPy generator: its per-attempt
error interval ends at zero while the canonical analysis ends at +0.27 pp. Both
fail strict error-reduction screening; no preferred stream is chosen afterward.
The canonical primary intervals above come from `summary.json:primary.effect`.
The all-comparisons table also uses separately keyed finite bootstrap streams,
so its repeated B2 interval can differ slightly in Monte Carlo endpoints.

The outcome audit does not independently prove every Bayesian posterior or
enumerate every public-task quotient-cap exclusion. Those numerical semantics
are checked separately by focused tests and the exhaustive finite study below.
Scientific review agrees with NO-GO and explicitly retains positive secondary
effects, adverse Logistics risk and the recovery/model-shift failure. Local review
memos and metered command records are retained with the run.

### Exact finite-model characterization

A separate local registration fixed 11 existing unit-test contexts and budgets
0–3 before the bounded calculation, without reading qualification outcomes.
Independent enumeration of latent event/fault worlds and query branches checked
1,368 positive-probability history/budget nodes and 2,736 B6 full/quotient choices.
Both maximum oracle utility gaps were zero; posterior/reading discrepancies were
at most `2.22e-16`. The 45-state full fixture merges exactly to two quotient
states. This verifies the declared reduced nominal decision problem rather than
a full recovery/replanning optimum or every public-task exclusion.

| Predefined fixture | Exact result and boundary |
|---|---|
| Already above permission threshold | At budget 1, B6 queries and attains nominal utility 0.94; B5/SVR stop with zero queries and utility 0.70. The 0.24 gap is a confidence-stopping limitation. |
| Two-query complementarity | At budget 1, stopping has utility -0.01 while B5/SVR spend one query and attain -0.02. At budget 2, B6/B5/SVR all attain 0.184 with 1.6 expected queries. |
| Fixed low-risk hazard shift | Declared hazard 0.05 gives posterior validity 0.95 and a budget-0 permission. With the same runtime input but actual hazard 0.30, the true false-permission probability is 0.30. All three policies fail here; low estimated risk is not a guarantee. |

This nominal utility uses the registered continue/abstain action values and query
cost, and is distinct from the campaign's realized recovery-inclusive utility.
The enumeration records 394 actual policy-tree nodes and 296 terminal histories;
there were no discrepancies. Local evidence is
`RUN/provenance/finite_characterization_{registration,results,summary}.json` and
the retained calculation script. Registration SHA-256 is
`3462a021337be72a7c3256d7876995597d130e8c6090d2689a748c72671710fa`;
results SHA-256 is
`7c21355beb0845c7b41778839008bc2fb4926bbec56aebe5802261ab72c6dc9d`.

## Embodied feasibility, limitations and final disposition

The bounded interface review inspected source and historical qualifications only;
it constructed or stepped no simulator. [mani_runner.py](scripts/mani_runner.py)
provides CPU Panda stepping, state/action recording and qualified prefix
reconstruction. Historical snapshot restoration failed and remains rejected.
[overnight_pick.py](src/dual_rec/overnight_pick.py) supplies typed pose/contact
history, and existing physics utilities can change materials or apply forces.
These are useful engineering interfaces, not an embodied SVR experiment.

Five integrations are missing:

1. Grounded, calibrated perception mapping pose/contact/visual observations to
   named predicates, uncertainty, sources and measurement timestamps. Existing
   privileged `state_dict`/pose readback is not deployable visual perception.
2. A multi-step physical skill library with validated symbolic initiation,
   effects, termination and evaluator-true preconditions. IPC Blocks/Logistics
   operators are not already ManiSkill robot skills.
3. A timed, reproducible mid-task physical transition after an earlier observation
   and before a dependent skill. Existing reset-time friction/mass changes do not
   demonstrate this chain. Policies need the same evaluated event history, using
   qualified prefix reconstruction rather than rejected snapshots.
4. An observation-delivery/cache layer that truly withholds unrequested updates,
   implements the timestamped `Reading` callback and preserves known-action
   history. Current physical loops fetch fresh privileged state each step.
5. Measured acquisition/delivery/processing latency and behavior while sensing,
   with matched physical time and cost. Control-step timestamps and Python
   dictionary-callback duration cannot substitute for camera/robot sensing time.

Exact interface paths and evidence limits are retained in
`RUN/provenance/revalidation-embodied-feasibility.txt`. No physical failure search,
new simulation campaign, GPU training or real-robot validation was performed.

The experiment assumes a complete trusted historical anchor, a correct finite
symbolic action model, at most one event per declared interval and no new events
while sensing/executing the selected suffix. Hazard calibration has supervised
development truth and ideal symbolic transition labels. These are strong
model-relative assumptions; test shifts do not establish unrestricted hidden-
event soundness. Persistent faults, missing data and delayed measurements are
specified synthetic channels rather than calibrated robot sensors. B6's bounded
menu/quotient and unoptimized recovery restrict its reference scope. Parent-level
uncertainty has only 23 independent tasks and remains limited for rare safety
errors; neither a zero-width bootstrap nor zero observed errors proves safety
noninferiority. No standard Bayesian, expiration, survival or active-observation
component is a new theorem.

The completed scientific disposition is **NO-GO for advancing this incremental
SVR contribution** under contract Case B. The primary meaningful effect/safety
question remains statistically inconclusive; the impact ablation and strong
freshness/control comparisons fail to establish a distinct useful contribution.
This authorizes no new score, parameter hunt, physical campaign, manuscript or
IROS/RA-L submission. The principal researcher retains all subsequent direction
and publication decisions.

## Local evidence and resource accounting

The final relevant regression suite passes: **181 tests**, including the old
monitoring/replay regressions, stale-cache permissions, contradictory/persistent
reports, known actions, delayed/missing evidence, model shifts, query-budget/menu
equality, rejected evaluator fields, exhaustive posterior/query-tree cases,
exact quotient preservation, reconstruction and finalization failure boundaries.
`uv run --no-sync ruff check src scripts tests` passes, and
`uv run --no-sync ruff format --check src scripts tests` reports 77 files already
formatted. The unrestricted `ruff check .` additionally finds eight pre-existing
issues in immutable historical archived scripts under old results; that failed
check is retained without modifying those records or ignore rules.

The local finalizer checks all 672 preserved historical files, the exact
user-approved ignore-file hash and all 21 qualification-sealed files. It also
requires completed independent audits, analyses, figures and fresh passing
validation records, plus completion of all known worker sessions. The final
records are `RUN/resources.json`, `RUN/integrity.json` and
`RUN/completion_manifest.json`; the manifest hashes all local run artifacts and
current source/report files, excluding only its own recursive hash.

The final pre-seal checkpoint records approximately **0.98 CPU core-hours** and
**362 MB allocated** across conservatively counted artifact roots. Held-out
evaluation alone uses 2,571.270 seconds wall and 2,570.666 CPU seconds; development
uses 341.075 / 340.865; public preparation uses 56.175 / 55.179. Final
qualification audit and analysis use 98.699 / 98.619 and 106.626 / 106.527 seconds
respectively. The campaign is about 2 hours 20 minutes at this checkpoint.
`resources.json` supplies the final exact capture of campaign elapsed wall,
summed subprocess wall, measured CPU, disk upper bound and all cap checks.

Caps remain six campaign/worker wall hours, eight CPU core-hours and four GB new
artifacts. There are **zero paid calls and zero GPU-training seconds**. Artifact
accounting deduplicates hardlinks and conservatively includes the complete Git
object storage and pytest temporary trees, including pre-existing allocations,
plus a metadata/final-commit reserve. Historical environments/evidence reused
without copying are excluded. CPU accounting includes metered main/source-
preparation/reproduction/review commands, preparation-driver self CPU and the
finalizer through capture. Read-only editor/tool-service/bootstrap overhead and
the final tiny JSON writes are not fully CPU-metered; this limitation is explicit
rather than an assertion of exact whole-machine CPU consumption.

Failed planning, first-pass tests/lint/format checks, the initial timestamp-audit
import-path error and corrected attempts all remain in the command ledgers.
No failure is deleted or substituted with a successful attempt. Full failed
command names, exit statuses and resource measurements are in the final resource
record and `commands.jsonl`; source-preparation commands have a separate ledger.

Principal local evidence paths:

- `qualification/{episodes,decisions}.jsonl.gz`, `status.json`, `audit.json`.
- `qualification/analysis/{summary.json,full_table.csv,paired_effects.csv,denominators.csv,reference_exclusions.csv,frontier_inputs.csv}` and both figure pairs.
- `supplement-qualification/` for all three event strata, controls and fixed witnesses.
- `calibration/`, `selection/`, `selection.json`, `qualification_seal.json`, `tasks.json` and `benchmarks/` for preparation, fitting, exclusions and frozen inputs.
- `provenance/` for failure reproduction, prior-work/source review, timestamp audit, finite enumeration, reconstruction equality, final independent reviews and presentation-only figure verification.
- `resources.json`, `integrity.json`, `completion_manifest.json` for final accounting and hashes.

These generated files remain local and are excluded from this session's
publication commits. The branch contains only scoped code/tests, the compact
input configuration, protocol and this report, with the user's ignore-file bytes
preserved. Commit publication is manual. No GitHub authentication or push occurs.
