# Evidence freshness and action permission: registered supervised qualification

Run: `20261111T132101Z`; base `31f4ba82f7ef55df35834a23d140aa6438964265`;
branch `research/support-validity-revalidation`. Authority is the user's supplied
11 November 2026 supervised execution contract. Earlier M3 and DUAL-REC NO-GO
conclusions are preserved; this is one separate freshness extension.

## Questions, primary comparison and decision boundary

RQ1 concerns stale cached permissions under executable hidden transitions; RQ2
revalidation without excessive refusal; RQ3 comparison against periodic/age/
current-condition and dynamic-belief baselines; RQ4 disturbance/sensor/task shifts.
The primary endpoint is **safe task completion per attempted checkpoint episode**.
A granted action with false true-state preconditions permanently makes safe
completion false, even if an environment guard blocks the transition. Goal
completion, grants, refusals, actual transitions and error denominators remain
separate.

Primary qualification condition is `hidden_nominal`, budget **2**. Before opening
qualification results choose B* from B2–B5 using development utility at this same
condition/budget. Ties prefer greater safe completion, fewer unsafe episodes,
fewer queries, then baseline name. This prevents selecting an easy comparator
after seeing qualification. The complete per-budget frontier and all B2–B5
comparisons must also be reported.

Screening for a positive pilot requires either (a) safe-completion difference at
least 0.05, paired 95% interval lower bound >0, no increase in both per-attempt
and per-grant error rates, and no material additional sensing; or (b) at least
20% relative error reduction with a paired error-difference interval excluding
zero, execution coverage within five percentage points, and comparable sensing.
Mean extra query difference must be <=0.05 calls for either claim; budget equality
alone is not realized-cost equality. Report intervals and sparse-error limits;
these are screening rules, not publication-level statistical validation. Effects
must not conceal an adverse domain result. Otherwise use the contract's NO-GO/
INCONCLUSIVE branches, with no new score or topic.

## Prior work and source boundary

Targeted primary inspection completed within approximately eight minutes, below
the 45-minute ceiling. Detailed references and access limitations are preserved
in `results/evidence-revalidation/20261111T132101Z/provenance/revalidation-positioning.txt`.

- [LOGIV v3](https://arxiv.org/abs/2610.40016v3), source
  `0ea7a7ff765016a33409c54572d733bed4503d4d`: original Boolean/unknown state,
  graph checking and local repair already exist. Its code is imported unchanged.
- [Ferrando–Malvone, TOSEM, DOI 10.1145/3735130](https://doi.org/10.1145/3735130):
  inspected accessible [author preprint](https://arxiv.org/abs/2408.11627v1), with
  journal-version access blocked. Additive relevance/payoff and budgeted
  observation selection already exist. Public RationalMonitor revision
  `0a335a3553300aee905b906c65ed2f7d74a338c7` was inspected, not installed.
- [Ernst et al., Frontiers 2026](https://doi.org/10.3389/frobt.2026.1847701):
  timestamps, relevant observers and observer dependencies already exist;
  dynamics-based validity durations/external disturbances are deferred there.
- [Catta et al., ECAI 2025](https://doi.org/10.3233/FAIA250983): rational
  proposition sharing/windowed monitors assume faithful trace projections.
- Bayesian belief updates, runtime assumption monitoring, survival decay, active
  sensing and risk-weighted observation are established. No new theorem or
  deterministic guarantee under unrestricted hidden events is claimed.

The potential distinction is empirical performance of support-validity weighting
against strong same-model policies, not invention of any component above.

## Formal state, history and generative model

Reuse the finite grounded public STRIPS model and exact symbolic transition
checks. T has the declared static/equality units; no physical mutex constraints
are invented. Runtime receives an earlier trusted anchor observation, a cache
measurement with time/source, available successful robot-action history, elapsed
opportunities for unknown change, and declared query channels. True current state,
actual event identities, actual test rates, regime labels, seeds and outcomes are
excluded from the runtime schema.

The finite event kernel permits **at most one** applicable, state-changing public
grounded action in a declared interval. Its occurrence probability for g elapsed
opportunities is `1-(1-lambda)^g`; conditional on occurrence choose uniformly among
applicable nonidentity transitions. If no such transition exists, retain state.
This models an event occurrence, not every proposition flipping. Proposition
wrong-value risk is derived from the actual action effects and posterior state
distribution. The kernel does not claim to model arbitrary repeated physical events.

General history: trusted nominal anchor; pre-cache interval of one opportunity;
cache measurement; any supplied observed successful robot actions; post-cache
interval of age 1, 2 or 4; pending task continuation. Known action effects update
values/status by the symbolic model, not by increasing age. The special known-
action control uses cache timestamp -1, observed robot action at 0, current time
0 and no hidden post-interval. Distinct phases avoid confusing an old reading
with a current one. Other cache timestamps are 0 and current time equals age.

Sensor corruption is a persistent per-atom latent bit within an episode, shared
by cache and repeated channel responses. A cached observation may be missing;
then its latest prior observation and time remain available. No data is silently
converted from missing to false. Query each atom at most once, so no method can
pretend repeated readings from the same faulty channel are independent.
Missing/conflicting reports do not create a Boolean assertion. Delayed responses
carry their actual measurement time and cannot overwrite a later known effect.

The shared dynamic Bayesian reference retains hypotheses `(cache_world,current_world)`.
The cache likelihood accounts for persistent corruption; for an observed cached
atom its latent bias is determined within each hypothesis. Missing-cache atoms
have the declared fault prior. Successful known actions condition and transform
the hypotheses. No hypothesis mass is silently truncated; exceeding 100,000
hypotheses is an explicit computational failure. Static conditions remain fixed.

## Observation actions and legacy adapters

All methods have the same individual dynamic-ground-atom inspection menu, unit
simulated cost, history, model and budget B in {0,1,2,3}. This is a new explicit
per-condition interface, not the earlier whole-predicate batch interface or a
measured robot camera/API. The original gate's pre-action behavior remains
unmodified behind its cumulative sensing adapter. Query latency and solver/
decision overhead are measured separately from simulated cost.

Each checkpoint is a fresh paired episode. Events occur before monitoring and
remain fixed during sensing/committed execution. Different methods do not receive
different disturbances after diverging decisions. A selected continuation is
executed with explicit per-action grants and domain precondition guards. A false
grant ends the attempted continuation; it is counted unsafe, not erased by the
guard. One common established recovery opportunity may precede commitment.
No new physical failure controller or sensing action is developed.

## Candidate methods and terminal decisions

**B0:** actual original LOGIV pre-action `state_gate`, all dynamic atoms tracked,
preserving global unknown resolution and current-precondition semantics.
**B1:** qualified M1 exact required-obligation/retained-plan verifier, with its
original cache-trusting semantics and query ordering. Both are diagnostic
comparators, not sufficient evidence for novelty.

**B2:** periodic refreshing of relevant conditions at interval d, with fixed
runtime-clock/canonical ordering and identical available budget.
**B3:** age-expiration refreshing: conditions older than tau lose their hard-cache
certificate and are prioritized by age, current conditions, then lexical order.
Historical observations remain probabilistic history; they are not discarded
from the Bayesian estimator. **B4:** refresh current action preconditions, bounded
by B, including previously known values.

B2/B3/B4 execute their eligible proactive schedule before applying the terminal
gate; their refresh work must not silently disappear merely because the prior
belief is confident. B5/SVR use the same adaptive early-stop rule. Actual queries
are recorded, and advancement is subject to the realized-cost guard above.

All B2–B5 and SVR variants share the **same** joint event/sensor model and final
posterior permission gate: continue if posterior probability of the full nominal
continuation succeeding is at least theta; invoke common recovery if that
probability is at most `1-theta`; otherwise use remaining permitted queries or
abstain. This is conditional empirical risk management, not universal soundness.
Their recovery candidates face this same posterior gate. B0/B1 retain their
original hard-evidence checks; differences in decision contracts are explicit.

**B5:** dynamic Bayesian belief plus a standard myopic value-of-information
selector across all available informative atom queries, including off-plan
proxies. Expected terminal value is `6*p-5` when permission is allowed and
`-0.05*p` for abstention, minus 0.01 per query; missing outcomes retain the prior
and consume a call. Zero-gain informative ties use entropy then lexical order.
This is an adaptation of established rational observation/belief reasoning.

**SVR:** use the same posterior for the probability a latest cached claim is
wrong now. Candidates close regressed continuation obligations through the full
declared T, and include the current action. Score is
`sum stale_risk(f)*impact(f)/query_cost`. Individual-atom impact is
`1 + remaining causal descendants of matching signed START support + (L+1 if f
is a current precondition)`. Future re-established supports are not charged as
initial supports. All coefficients are fixed at 1. Recompute risk after each
reading; exclude a model-uninformative query. No learned score or new formula is
introduced after results. Prespecified ablations set impact=1 or stale_risk=1.

**B6:** exact reduced belief/query-tree decision reference on at most 32 joint
hypotheses, eight candidate observations and B<=3. Optimize the declared nominal
continue/abstain utility with persistent sensor/missing models, not old M4's
resolved-classification objective. Ordinary recovery remains available after the
query decision, but the reduced tree is not a ceiling for the full replanning
problem. Bounds/exclusions are explicit. Exhaustive small controls check posterior,
action permissions, persistent faults and hidden-state isolation.

Common recovery uses the existing bounded LOGIV Repairer and action library.
Identical knowledge inputs share an identical cached candidate; no oracle state
or event label selects it. Cache/cold planning time is recorded. Returned symbolic
certification is separate from actual safe goal completion. No favorable new
recovery action is introduced.

## Public parents, calibration and allowed parameter selection

Source corpus remains `potassco/pddl-instances` at
`cf19edf7c53d1540ddbb396c642595e0926ee552`. Development reuses only old instances
1–4 in each family. Qualification selects previously unused public instances
**13–24 in both Blocks and Logistics**, before method outcomes. Pyperplan 2.1
GBFS+hFF is a fixed source-preparation choice after a retained native-FD probe
timed out. All 24 were attempted; unchanged Logistics19 is unsolvable because its
airplane has no initial location. It is retained without replacement. The other
**23 new parents** span both domains and have independently checked plans.

Per parent take distinct plan indices floor(L/3) and floor(2L/3), eight paired
schedules, ages cycling 1,2,4. The public model/action subset, plans and histories
are identical across methods. Parent IDs, not schedules, are inference units.

Development calibration uses two checkpoints, 64 fixed schedules, actual lambda
0.10 and sensor error 0.02. Observed complete state-change indicators identify
the single-event frequency; `(changes+1)/(opportunities+10)` estimates lambda.
Sensor errors are estimated against independently validated development cache-
epoch state with Beta(1,49) smoothing. These are offline supervised development
labels, not deployment features. Estimated per-proposition risks subsequently
use public action transitions. Qualification frequencies never fit the models.
The assumed missing probability is 0.10; the missing30 test is a declared shift.

Select theta from {0.85,0.90,0.95,0.99} using development B5 utility only, then
share it across all freshness methods. Select d in {1,2,4} and tau in {0,1,2,4}
using development B2/B3 respectively. Utility is safe goal success minus five
times any unsafe permission, minus 0.01 queries and minus 0.05 unnecessary
abstention. Use only hidden_nominal and no_external for these selections; do not
merge transition and sensor stress into an opaque score. No other parameter
search is authorized. Freeze selected parameters and B* in a local commit/seal
before qualification outcomes are opened.

Numerical utility ties within 1e-12 prefer the larger theta (conservative), then
the smaller interval/expiration threshold. Development selection has completed
without qualification data: lambda=0.097678916827853, sensor error=
0.019872056621750376, theta=0.85, periodic interval=1, expiration=0. The frozen
primary comparator is **B2**, the strongest development utility among B2–B5.
Full selection rows and alternatives are retained in `selection/` and
`selection.json`; these outcomes do not change SVR's scoring definition.

### B6 computational representation clarification before qualification

The reference uses one fixed menu of at most eight queries: current preconditions,
then regressed/T-connected obligations, then remaining canonical atoms. It never
refills this menu after a query. For this menu only, push the full joint belief
through its selected cache/current bits and an unqueryable full-continuation-
validity label, merging identical images by exact mass summation. This preserves
the declared query likelihoods and nominal decision utility; no hypothesis mass
is dropped. The 32-state bound applies to that quotient. Cases still too large
remain explicit reference exclusions. B6 is exact for this reduced query/action
problem and may query after practical policies' confidence stopping; it is not a
full-menu, full-replanning ceiling. This representation correction was made for
tractability before qualification, with no B0–B5/SVR algorithm or weight change.

## Locked regimes, shifts and negative controls

Regimes: no_external(lambda0,eta0); hidden_nominal(.10,0); hidden_low(.03,0);
hidden_high(.30,0); missing30(.10,0,cache/query missing0.30); noise02(0,.02);
noise10(0,.10); delayed(.10,0,old cache-epoch query); recent(.10,0,age0);
known_action(0,0,age0/known update); and unrelated_event.

The unrelated_event control forces one uniformly selected applicable changing
action whose changed atoms are disjoint from the full continuation/T relevance
closure; no eligible action is recorded as such, never replaced. All other events
are sampled by the declared kernel, not selected because they defeat a method.
Separately stratify actual hidden transitions that invalidate relevant cached
conditions versus those that leave them valid. These evaluator labels are not
runtime input. Source transitions are symbolic execution, not physical evidence.

Controls include no external change, unrelated change, recently verified evidence,
same-value replies, a false cached condition not queried, and a known robot action
that updates the belief correctly. Preserve the original holding(b)/put-down(b)
witness and new held-out failures. Hazard and sensor shifts explicitly include
low estimated risk being wrong. No method is promised to win.

## Evaluation, audit, resources and stop

Primary inference averages schedules/checkpoints within each independent parent,
then uses paired family-stratified bootstrap intervals with 2,000 resamples and
analysis seed 71603. Report both domains and all methods/budgets. Per-grant error
ratios have selection denominators; also report per-attempt unsafe episodes,
conditional coverage, paired outcomes and sparse zero-event parent bounds. Do
not infer causal safety from differing granted subsets or zero-width bootstraps.
Risk-versus-coverage figures retain query costs and full counts.

Record actual goal, safe goal, granted/refused/rechecked/executed actions, false
current permissions per grant/per attempt, abstention, observations, recovery
success/failure, invalidation-detection delay and solver/wall overhead. Preserve
undetected cases and all unsupported oracle/preparation cases. Brier/reliability
diagnostics compare initial risk estimates with evaluator truth without fitting
test frequencies. A standalone audit must recompute principal outcomes without
importing scheduler code.

Six-hour campaign/worker-wall ceiling, eight measured CPU core-hours, four GB new
artifacts, no paid API, GPU training or detached/unbounded jobs. Current embodiment
work is read-only/bounded interface feasibility, not a simulator campaign. Preserve
all 673 prior file hashes, the old locks/environment and old result seals. Record
source/command/exit/wall/CPU/artifact evidence, including source-preparation failures
and read-only bootstrap CPU measurement limits. Finalize only after all workers
finish, full regression tests/Ruff, independent audit, figures, report and evidence
sealing. Commit locally; no authentication attempt or GitHub push.

## Publication packaging: user steering during this session

The user explicitly requires leaving their `.gitignore` rules alone and excluding
logs and unnecessary generated results from GitHub. Their exact ignore-file bytes
are restored and retained; this is the sole approved exception to the initial
673-file inventory. The other 672 historical files and all prior scientific
records remain immutable. No further ignore-file edit is authorized.

Raw logs, observations, prepared-state dumps, detailed tables and local seals stay
under the ignored run directory. Publication commits contain code/tests, this
protocol, the final report and one compact configuration of source hashes, exact
input plans and selected parameters. The initial unpublished preregistration
commit remains locally at `refs/local-evidence/support-validity-registration-20261111`
(`e95ef0fdbd3593d300c65fe0deb5259805613f08`), outside normal branch/tag publication.
The public research branch is rebuilt from the unchanged reviewed base so this
session's generated data is absent from its publication ancestry. Prior reviewed
research commits are not rewritten. No GitHub push is attempted.
