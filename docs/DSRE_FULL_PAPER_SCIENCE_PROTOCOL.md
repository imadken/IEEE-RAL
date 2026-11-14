# DSRE operational research protocol: frozen before new outcomes

Authority: supervisor full-paper sprint contract, 14 November 2026. Base
`c2f77332f0a72b7f3930e846c1d4e0a8f82da67b`; branch
`research/dsre-operational-full-paper`. Exact source/input hashes and this document
are copied to the new result root before physics. The old 333-parent follow-up,
its 1332 continuations, previous interrupted cohort and all historical seals remain
immutable. All previously inspected data are development/reanalysis, never new
calibration. No manuscript is submitted or pushed.

## Fixed question, hypotheses and operational estimand

Keep minimum observable evidence for intervention adequacy, exact sufficient
rules, support of two independent parents, minimum literals/larger support/
continue-first/lexical ties, and observation/repertoire/reference witnesses.
H1 concerns information sufficiency; H2 separates required recovery from
interchangeable adequacy; H3 separates reference purity and independent statistical
risk; H4 concerns imperfect observations. Neither strict nor risk mode is a new
pure-rule solver. B7 identity is mathematical, including shared risk-tier grammar.

The primary router is the **existing** `S_then_B1_two`: strict DSRE first, otherwise
the existing two-literal outcome-aware rule at empirical error .10. No controller,
model, tree node, outcome definition or threshold is selected using new outcomes.
Runtime inputs contain only task and predecision Boolean facts derived from the
declared pose/proprioception packet. No outcome, condition ID, seed, grasp/contact
oracle or future observation enters routing. All common-budget comparators use
the same six primary and fixed budget-one optional facts; only the explicitly
labeled full-signature upper-information comparison uses all twelve predicates.

Abstention means **defer/stop**. It contributes zero to the primary autonomous
completion numerator, even if the initial state already satisfies task success.
Conditional success among actions, unconditional completion, inadequate actions,
defer fraction, regret relative to the available two actions, unnecessary recoveries
on initially successful/both-success states, and required recovery on initially
failed recover-only states are reported separately by task and condition.

Primary effect: calibrated risk-tier DSRE minus calibrated strict DSRE autonomous
completion on the new disjoint test cohort. All baseline comparisons are also
reported, including identical B7 and stronger ordinary tree/rule controls. Four
thousand paired seed-parent bootstrap draws (both conditions resampled together),
PCG64 seed `2026111401 + task_index`, two-sided percentile 95% intervals. Task index
is Pick=0, Push=1. Initially failed, initially successful and recover-only contrasts
retain all task parents in the resampling frame. These intervals are estimation,
not the statistical certification procedure; zero-variation intervals are not
population error bounds. With 80 test parents/task, a worst-case normal half-width
for parent differences in [-1,1] is about 21.91 percentage points; rare recovery
effects are expected to remain imprecise.

## Independent allocation, calibration and fairness

Fixed chronological seed allocation, both unchanged conditions:

| Task | Calibration (180 parents) | Test (80 parents) | Conditions |
|---|---|---|---|
| PickCube | 8000000..8000179 | 8000180..8000259 | nominal, offset002 |
| PushCube | 9000000..9000179 | 9000180..9000259 | nominal, misaligned |

Execute calibration in interleaved task/seed order before **any** test parent.
Maximum 520 new parents, 1040 paired checkpoints, 2080 paired continuations, plus
at most 320 independent reset executions of selected primary test actions. No
replacement, repetition, label-based allocation or sample-until-significance.
The unused manifest is checked against all prior manifests and actual execution
directories before outcomes. A seed overlap blocks physics rather than changing
the seed. Both conditions must qualify and receive an atomic COMPLETE parent
marker for primary inclusion; all partial cells remain secondary evidence.

For each fixed method, task and assigned action, count distinct seed parents.
A parent is erroneous if **any** assigned condition has an unacceptable action.
The formal target is this assigned-parent any-error probability <=.10, conditional
on at least one assignment of that action, under IID seeded simulator parents with
the two registered conditions. It is not a bound for arbitrary time points,
checkpoint-weighted samples, sensor shifts, hardware or a changed controller.
Checkpoint conditional risk and operational completion remain separately measured.

Compute exact one-sided Clopper-Pearson upper bounds. The four-stratum primary
diagnostic uses delta=.0125 and requires 42 zero-error assigned parents. For every
formal operating gate and fair cross-method comparison, use the **stricter global
family** delta=.05/(4*17), with the same risk target for all 17 frozen methods. This
requires 69 zero-error assigned parents. This protects simultaneous formal claims
over every fixed method/task/action stratum; the weaker primary diagnostic never
enables an action that fails the global gate. Missing or zero-assignment strata
are NOT CERTIFIED. Models receive no calibration outcomes as training data.

Seal the completed 360-parent calibration decision before test. Calibrated routing
retains a proposed action only if its exact task/action stratum passes the global
gate; otherwise it defers. No re-optimization or label-based threshold selection.
If the planned calibration is incomplete, no formal operating gate is enabled.
The complete fixed calibration cohort is collected even if an early bound would
already pass or fail. Test data never alter this decision.

Pre-outcome assignment forecast from the inspected old inputs: risk-tier Pick
continue 166/166 assigned parents; Pick recover 17/166; Push continue 0/167;
Push recover 167/167. Thus 180 calibration parents/task forecast approximately
180,18.4,0,180 assignments. Rare Pick recovery and absent Push continue are expected
to remain NOT CERTIFIED. No targeted replenishment is permitted. The prior run's
15.66 seconds/parent implies about 136 physics minutes for 520 paired parents;
selected test repeats add a conservatively reserved 25 minutes. Stop at the exact
180-minute cumulative cap rather than sacrificing analysis/reporting time.

## Fixed comparators and information standards

The 17 registered methods are strict DSRE; B7; existing strict-then-provisional
DSRE; its ordinary B7-then-capped-risk equivalent; pure one-/two-literal rules;
four-outcome CART depths 1/2 at purity 1 and .9; depth-2 strict CART with a fixed
10-parent support pruning gate; B5 at empirical error .10; always continue;
always recover; full-signature strict selector; ordinary greedy pure-rule search;
and policy-faithful sufficient explanations of the frozen .9 depth-2 tree's label.
The last comparator explains the selected policy label, not intervention adequacy.
The full-signature selector has more Boolean facts and is not a fair explanation-
length competitor. Exact old tree nodes are loaded without fits. All statistical
operating gates and proposed-action evaluation use the same original reference,
action set, terminal utility, grouping and global error budget. Empirical .9/.10
purity is explicitly distinct from certified statistical risk.

## Observation stress protocol (offline, no sensor deployment)

Use the inspected 333-parent follow-up's recorded predecision telemetry; outcomes
stay those of its original paired branches. This is exploratory offline reanalysis,
not another independent confirmation or calibration cohort. No grasp/contact
oracle, hidden outcome or new perception model is used. Input positions are metres;
the recorded control sampling cadence is 50 ms.

Twelve fixed input scenarios: clean; unavailable selected optional predicate
(Push has no selected optional predicate, so mask goal-near); unavailable earlier
history; unavailable pose fields; independent Gaussian object/TCP pose noise at
1 mm and 5 mm with three fixed replicates each; 50 ms and 250 ms pose delay.
Goal estimation noise is shared across the first/current packet; object/TCP errors
are independent across those packets. Fingers remain measured. Noise is seeded
by SHA256(cell,scenario) plus `2026111402`, common to every method. Delay uses the
actual prior prefix pose sample while retaining current finger readings. The
unavailable-history path makes temporal predicates UNKNOWN. UNKNOWN is never a
known negation. No grid point is selected after observing performance.

Threshold proximity is the predeclared clean-state subgroup within 1 mm of any
registered predicate boundary. Report stability of actions and fact certificates,
bad actions, defer rates, factual contradictions against clean telemetry, accepted
strict errors, proximity subsets, actual serialized observed-input bytes and
scalar counts, abstract predicate/literal counts and measured routing runtime.
Corruption replicates do not create new independent parents. Clean calibration
does **not** transfer to these corrupted inputs; all such apparent operating points
are labeled uncalibrated sensitivity analyses. No sensing latency/energy/cost is
inferred from a Boolean count or serialized bytes.

## Physics and third-task qualification

Use unchanged `dsre_paper_physics.run_cell`, CPU ManiSkill/SAPIEN, full canonical
prefix resets, exact controller memory/model checks, two fixed skills and terminal
success at 70 controls/3.5 seconds. No native snapshots. On test, a separate reset
and full prefix executes the calibrated primary selected action once, when enabled.
The selected action is computed through the outcome-free runtime schema and sealed
before that execution. Its parent already has paired measurements: this is an
explicit new selected-execution repeat, not a new independent parent or secretly
claimed standalone closed-loop campaign. Compare the entire selected future and
terminal outcome against the paired branch. A replay/source/controller or future-
parity disagreement halts physics, retaining the diagnostic rather than repeating.

Run one synchronous chunk at a time: at most 480 seconds/24 parents, 120-second
per-parent cap and launch reserve. Reserve at least 75 session minutes for final
papers/audits. Total new physics <=10800 seconds, session <=28800 seconds, new
artifacts <=1 GB with an 850 MB physics soft stop. Zero GPU training/paid APIs/new
datasets. Source pins are checked before each parent. Attempts are immutable and
never relaunched. Unexpected whole-chunk interruption halts new physics under this
protocol; source/qualification failure is never a routine resume boundary. No
campaign workers survive completion. Unrelated jobs are untouched.

Lift/Panda is the preselected third task. Source audit finds its existing alternative
only clips nominal lift speed, with retained 210/210 both-success starts, no failed
starts and no varying adequacy/recovery contract. Consequently the required
distinct-recovery/varying-outcomes prerequisite fails **before new physics**. Do not
develop a controller/fault or choose another task. No third-task cohort is authorized
after this failed gate; preserve the blocker as an external-validity limitation.

## Verification and outputs

Before physics: reproduce old strict b1 predictions, test outcome-free inputs,
unknown literals, empty support, opposing-action/neither cases, independent-parent
aggregation, exact CP thresholds and stop semantics; test frozen observation
transforms and source identity. Independently verify new action equations, all
prefix/model/controller fields, integer-mask rules, direct CART leaves, selected
execution labels and inverse-beta CP bounds. Recount every main table and primary
paired interval independently. Separate same-session implementations are not
external human replication. Preserve every negative comparison and prior seal.

Maintain `rss2027/dsre_full_paper_master.tex`/PDF and the anonymous six-page Stage 1
derivative, five content plus one references, using the unchanged official class.
The full master includes complete scope/math, operational assurance, all four
outcome categories, fixed control comparisons, sensitivity, physical examples,
reproducibility and limitations. No speculative empirical graph is drawn.
Update existing results/reviewer critique and claim ledger, with exact source
hashes, independent audits, archive and resource accounting. Readiness is split
into method correctness/distinctiveness, evidence including rare uncertified
actions/blocked breadth, and what the six-page paper establishes by itself. Commit
only scoped code/tests/papers/compact reports locally; exclude raw traces/logs.
