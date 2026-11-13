# DSRE Stage1: evidence-sufficiency repair specification

Fixed question: **What is the smallest observable evidence sufficient to justify
choosing an adequate robot recovery action, and when existing observations cannot
justify a choice, what information or recovery capability is missing?**
Authority is the complete supervisor attachment, copied verbatim to each new run's
`authority.txt`. Reviewed base `f3d74ec4271742f26a491276903230bdec9a69b2`;
branch `research/dsre-evidence-repair-stage1`. No absent external blueprint or
supervisor analysis is invented. Prior v1.0/v1.1 specifications, outcomes, seals,
equivalences and negative findings remain unchanged. This specification and config
are frozen before new method comparisons.

## Data, observation and support contracts

Reuse844 measured paired checkpoints,422/task,211 task/seed groups/task, two
conditions kept together in original five folds. Primary outcome is terminal
binary task success for the fixed continue/recover policies at70 controls/3.5s.
Good(i) contains successful actions, both if both succeed, empty if neither does.
Missing outcomes are UNKNOWN and prevent a universal certificate, not imputed
failures. The table hash remains
`46f13e374fd5d319e5987e12352074309163956db83b1f0ce9b3991a43d653e2`.
All old seeds are development; evaluation is exploratory grouped cross-fit.

F0 is the six frozen primary predicates. Exactly six optional unit-cost predicates
are authorized, in this canonical order, from the **current predecision observed
pose packet**, never future/hidden physical state:

| Channel | Signed coordinate test in metres |
| --- | --- |
| object_left_of_goal_02 | object.x-goal.x < -.02 |
| object_right_of_goal_02 | object.x-goal.x > .02 |
| object_behind_goal_02 | object.y-goal.y < -.02 |
| object_ahead_of_goal_02 | object.y-goal.y > .02 |
| hand_left_of_object_02 | tcp.x-object.x < -.02 |
| hand_right_of_object_02 | tcp.x-object.x > .02 |

Exact boundary equality is false. Missing/nonfinite vectors yield UNKNOWN for their
channels, not future-derived substitutes. Match stored packet timestamp to the
checkpoint and independently check raw prefix observations. These pose estimates
are simulator-supplied interfaces, not validated real perception. Grasp/contact
oracles are privileged diagnostics only. Channel cost counts abstract predicates,
not distinct sensors, processing time, energy or sensing accuracy; several derive
from the same raw pose. Every plot states that limitation.

Runtime input is only scope plus F0 and the **already selected** optional channels.
No unqueried channel, row ID, hidden condition or paired outcome is exposed to the
query. Design-time reference rows include qualified outcomes and independent parent
group IDs for support. Minimum support is **two distinct task/seed parents**, rather
than the prior two-checkpoint rule. This is an explicitly authorized support change;
historical row-support results are not overwritten. Canonical evidence ties remain
minimum cardinality, higher checkpoint support, continue-first, lexical facts.
Original8-feature schemas remain unchanged; a scoped repair schema admits up to14
features only for six primary+six optional+two privileged diagnostics.

## Exact offline repair objective and obstructions

For any fixed observation set F, group rows by exactly equal observed signature,
including UNKNOWN as a distinct observed symbol for the finite ceiling. Let
`G(Z)=intersection Good(i)` over a group. Then
`C_R(F)=sum |Z|*1[G(Z) nonempty]/|R|`. Its absolute upper bound is the fraction of
rows with nonempty Good: neither-success rows are never repaired by observation.

For each budget b=0..3, enumerate every available J subset of six channels with
|J|<=b on **training parents only**. Choose maximum training ceiling, then smaller
|J|, then the declared canonical channel order. Freeze J and its training/reference
hash before producing held-out predictions. This is an exact instrumentation-design
objective, not online adaptive sensing or a new search algorithm. It does not
choose channels using a held-out query's optional values or labels.

At runtime, a row conservatively matches evidence unless a known opposite fact
excludes it. UNKNOWN reference values cannot be discarded. Search every needed
known-literal subset for the minimum universally adequate rule with two independent
parents. The finite exact ceiling, achievable conservative-rule coverage/support,
and actual cross-fit success/acceptance are three separate quantities.

If strict search abstains, return **all applicable** obstructions with scoped raw
IDs and outcomes for audit only:

- `REPERTOIRE_INADEQUATE`: a compatible qualified row has neither successful action.
- `OBSERVATIONAL_AMBIGUITY`: compatible rows have nonempty disjoint Good sets.
- `REFERENCE_INSUFFICIENT`: wrong scope, missing/unqualified outcomes or insufficient
  independent-parent support. Support shortage is not physical impossibility.

Output status is STRICT_FINITE_REFERENCE, INSUFFICIENT, or REFERENCE_INSUFFICIENT;
descriptive empirical rules use PROVISIONAL_UNCALIBRATED. Obstructions can coexist,
and a reference problem may coexist with physical obstructions. Expose a why-not
witness for each available action, plus necessary-literal witnesses for strict
minimum explanations. An offline upgrade record contains J, cost, pre-upgrade and
post-upgrade training ceilings, scope/hash and `OFFLINE_DEVELOPMENT_SELECTED` status;
it never promises that every blocked query becomes actionable. Independently verify
which actual collisions each added predicate splits. When all declared observations
leave an incompatibility, explicitly report no observation repair in this vocabulary.

Pseudocode: qualify -> partition training -> enumerate J -> freeze J for each
budget -> project queries to F0+J -> exact strict search -> action+minimal facts or
all obstruction witnesses+frozen offline upgrade -> independent numerical audit.
No action is executable without future independent calibration, even if finite-
reference strict. Do not reroute a calibration-disabled action.

## Precommitted comparisons, sensitivity and uncertainty

Each selector receives the same training outcomes and optional menu. Greedy coverage
adds the canonical channel with largest positive ceiling gain, stopping if gain is
zero. Greedy entropy minimizes checkpoint-weighted four-category conditional entropy
H(Y|F0+J), canonical ties at1e-12, stopping at no positive gain. Canonical order and
one global `random.Random(20261113)` permutation use prefixes of length b. Exact
search can find multi-channel synergy missed by zero-gain greedy stopping; this is
known discrete optimization, not novelty. Controls may use fewer than b channels;
report actual count, not merely allowed budget.

For identical J/reference/held-out queries compare DSRE, B7, B5 beta=.10,
historical full-strict-first then two-literal B5, pure one-/two-literal rules, and
CART depth1/2/3 at strict leaf target1 and descriptive target.9, plus always-continue
and always-recover boundary controls. B7 and zero-risk
B5 are mathematically identical to DSRE with matching support/ties. The historical
S-first two-literal wrapper may match again; report it. A cap2 strict rule is also
shown separately, avoiding ambiguity about the wrapper's strict tier. B5 .10 is
provisional even if its measured error happens to be zero. CART retains original
four-category Gini settings, row-based split support2, deterministic lexical splits,
no pruning, and a shared **inference** independent-parent gate2. Only feature-changed
training folds may train new trees; reuse original nodes at J=empty. Deduplicate
identical selected J within task/fold; fit counts and training time are measured.

Primary cross-fit outcome is successful strict recommendations/all checkpoints,
alongside actual unacceptable actions/recommendations and/all checkpoints. A
zero-error strict-reference descriptive success claim requires zero held-out
unacceptable choices; list every error individually. Refusals are not successes.
Also report coverage, literals, support in rows/parents, statuses, overlap witnesses,
S/R fractions for wrappers, channel stability, cold timings and trained tree counts.
Failed-start rows are a separate population;277 maintained-success Pick starts are
not new recoveries. Partial information masks the first selected optional query
channel (or primary goal-near if J empty), reference unchanged, strict DSRE only.
Full F0+all optional and F0+privileged/all optional+privileged are offline diagnostics,
not primary deployed feature maps or evidence of real-sensor performance.

Use2,000 paired bootstrap draws of211 seed groups/task, both conditions together,
PCG64 seed2026111301+task index, same fixed v1.1 parent bootstrap. Report intervals
for counts/rates, common-cohort explanation differences and selector contrasts.
Withhold conditional intervals with fewer than10 recommending groups. Zero sample
difference is not population equivalence. Selected J is fit within each original
fold; no new untouched holdout is claimed.

## Known proof obligations and counterexamples

Deterministic nested exact-signature refinement splits old groups; any old common
adequate action remains common in every child. Thus finite oracle actionable mass
cannot decrease. A neither row stays empty-Good after any refinement. Identical
full-vocabulary signatures with disjoint Good cannot be separated by these channels.
These are established principles. Conservative compatible sets and independent
support must be checked separately: fine full signatures can lose support, although
an exhaustive reasoner can retain broader old evidence. In a fixed same table,
adding optional predicates cannot remove an old supported pure conjunction, so the
**exact supported rule optimum** also cannot lose coverage; a full-signature-only
selector can. UNKNOWN prevents excluding a bad row; UNKNOWN distinctions in exact
partitions need not be executable Boolean literals. Across folds or newly selected
non-nested J, neither empirical performance nor selected support need be monotone.
Test all of these, scope/data problems, opposing actions, neither, and strict/pure
rule equivalences using a separate dictionary-only implementation.

## Prior-work challenge recorded before new experiments

**METHOD_DISTINCTIVENESS_NOT_ESTABLISHED is the default challenge**, not a requirement
to obtain a positive result. Primary method sections were inspected directly.

| Primary work | Exact overlap and remaining scope distinction |
| --- | --- |
| [Khan/Poupart/Black, ICAPS2009](https://cs.uwaterloo.ca/~ppoupart/publications/explaining-mdps/ICAPS09OKhan.pdf), MSE equations/workflow | Minimal action-value justification already exists; reward/occupancy templates differ from finite paired robot-outcome conjunctions. Minimality and hitting sets are not new. |
| [DISCRET, ICML2024](https://proceedings.mlr.press/v235/wu24n.html), [author method §§2–3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11350397/) | Outcome-grounded subgroup rules and treatment means already exist. B5 is a small exact same-grammar adaptation, not a reproduction of its learned synthesis. |
| [DA-GRD2026 preprint](https://arxiv.org/html/2609.29065), §§III-D/E | Decision-aware probe scoring targets common grasp coverage rather than complete localization. Our selection is fixed offline telemetry design, not physical tactile sensing or the first decision-aware ambiguity resolution. |
| [Applied Sciences2026 16(10):4917](https://www.mdpi.com/2076-3417/16/10/4917), Definitions1–3 and Remark9 | Its robust feasible-action intersection on observation classes directly subsumes our strict feasibility criterion; refinement can split conflicting classes. We instantiate finite measured robot outcomes, abstention coverage and witness/upgrade enumeration. These do not establish new feasibility theory. |
| [Ernst et al., Frontiers2026](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1847701/full), §3, Algorithms1–2 | Explicit timestamped context variables, observability conditions and passive observers already support decision context. Our fixed budget optimization over recorded Boolean channels is not a new observer architecture or validated runtime sensing system. |
| [RESCUE2026 preprint](https://arxiv.org/html/2610.13516), §III | Matched intervention values and policy-state replay are prior mechanisms; our outcome-grounded explanation/repair does not invent recoverability estimation or fresh branching. |

The feasibility core is directly covered by prior theory, and the optimizer is
ordinary exhaustive subset selection. A finite executable package could still be
useful; witness labels/formatting alone are insufficient novelty. No universal
claim of full-package subsumption by one paper is inferred without evidence. The
scientific gate must consider actual held-out utility versus greedy selectors,
two-literal rules and CART, and whether a simple known wrapper reproduces the new
operational outputs. Complete the characterization even if novelty fails.

## Bounded execution and Stage1 argument

Four-hour wall/five measured CPU-hour ceiling,0GPU/new physics/paid APIs,
500MB new artifacts,100MB downloads. Preserve all historical members, seals,
`.gitignore`, `uv.lock` and user moves. Use bounded checkpointed workers and reserve
the final hour,1,800CPU seconds and50MB for tests/audit/report/seal. No manuscript,
push or credentials. Exact results, two physical worked examples, falsifiable
hypothesis assessment and prospective validation judgment will be appended after
the frozen computations without altering these preregistered choices.

## Two worked physical examples after the frozen study

**Resolvable finite class, fragile reference support.** PickCube records
`PickCube-v1/102571/offset002` and `PickCube-v1/102892/offset002` share the same six
primary predicates. At3.5s, the first has object.x=-.046608731, goal.x=-.012600221,
so object_left_of_goal_02=True; continue fails and recover succeeds. The second
has object.x=.039204050, goal.x=-.015400097, so that predicate is False; both
actions fail. With the one-channel upgrade, the first belongs to a full-table
pure recovery child supported by **two independent parents**. That class is
finite-reference actionable; the neither-success state remains inadequate.
The complete observed poses, both measured outcomes, child certificate and literal
witnesses are in `worked_examples.json`. The small supporting cohort also explains
why splitting a finite class does not guarantee cross-fit reference support.

**Unresolvable ambiguity under the fixed menu.** At2.65s,
`PushCube-v1/103984/nominal` is recover-only and
`PushCube-v1/105544/nominal` is continue-only. Their observed object/TCP/goal
positions differ, but their primary predicates and all six optional predicates
are identical. Both optional vectors are `[True,False,False,False,True,False]`.
Every declared upgrade leaves them indistinguishable; the full ambiguity graph
has six such opposing-action edges and zero separable edges. This is a limitation
of the declared Boolean vocabulary, not a theorem that raw poses or every possible
sensor are incapable of distinguishing the states. No new sensor or controller
was introduced to escape this result.

These examples were selected for explanation after evaluation; they never selected
the feature thresholds, channel sets or operating points. The initial inadequacy
example is also retained in the raw evidence. The useful local upgrade and the
unrepairable case coexist with the adverse grouped evaluation below.

The optional channels are extra Boolean summaries of poses already recorded.
Their gains demonstrate representation refinement, not acquisition of a new
physical measurement or installation of new sensing hardware.

## One-page Stage1 scientific argument and falsification outcome

**Precise methodological claim for supervisor assessment:** an executable finite-
reference recovery-sufficiency interface can return a minimum adequate-action
conjunction or verifiable observation/repertoire/reference obstructions, together
with a minimum-cost, training-selected instrumentation upgrade under a fixed menu.
This is a scoped implementation/empirical claim, not new feasible-action theory,
active sensing, hitting-set search or a guarantee on future physical actions.

The prior limitation is operational: an ordinary B5/CART prediction does not by
itself provide all three obstruction types or a frozen minimum-cost instrumentation
design. However, established partition feasibility plus exhaustive feature-subset
selection can wrap those models and supply the same additional outputs. The proposed
combination has no established exclusive capability or novel optimizer.

The falsifiable empirical question was whether the sufficiency objective yields
better held-out successful finite-reference action coverage than entropy/greedy/
simple-rule alternatives at comparable abstract channel cost, while exposing rather
than concealing unacceptable actions. At one channel, Pick finite coverage rises
183->235/422 and cross-fit successes202->242/422, but errors rise1->2; exact
selection equals greedy coverage and canonical order. On145 failed starts, successes
fall19->18. Most of the apparent gain concerns maintained success. At two channels,
exact versus entropy adds only one success with a paired interval crossing zero.
At three channels, exact gives250 successes/6 errors, versus greedy242/2, using one
more mean channel. No primary Pick setting satisfies a zero-held-out-error claim.

Push has zero strict recommendations and zero finite improvement even with all six
channels or privileged diagnostics. B7 reproduces all16,880 registered DSRE
decision/evidence views. Two-literal pure rules match exact-selection DSRE through
budget2. At budget3, full minimum rules add eight recommendations over cap2, five
successful and three unacceptable. Small CART comparisons remain strong, and their
descriptive .9-risk outputs cannot be compared to strict rules as if claim strength
were identical. These are completed adverse findings, not a reason to change topics.

The contribution therefore remains **METHOD_DISTINCTIVENESS_NOT_ESTABLISHED** and
the readiness advice is **PRELIMINARY_ONLY / NOT_READY**. New confirmation would
first need supervisor justification of a substantive non-equivalent capability,
adequate observable intervention variation and rare-action calibration feasibility.
Exactly one dormant conditional validation plan is frozen in `prospective_plan.json`:
the lowest nonzero registered budget1 router, fresh calibration1400 Pick/200 Push
parents and disjoint confirmation1400 Pick/200 Push parents, fixed original
conditions/controllers, no seed manifest or execution. Its roughly10.14h simulation
cost and zero strict Push accrual make immediate execution unjustified. It is a
costed handoff, not a commitment or permission to launch physics or a manuscript.
