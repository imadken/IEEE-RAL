# ERR exact finite-world results

All rows below are **ANALYTICAL_ONLY**, not robot episodes. Costs are declared
experiment-type units, not a measured minimum noisy-trial budget. The registered
source menus, input probability vectors, verdicts, source metadata and costs are
stored in `research/err_method_challenge/final/finite_models/registered_cases_and_results.json`.

| Case | Status | Exact selected types | Cost | Opposing pairs | Independent exact oracle | Greedy | Reverse-deleted greedy |
|---|---|---|---|---|---|---|---|
| same_marginals_with_pair | MINIMUM_RESOLVING_MENU | paired_trial | 2 | 1 | ['2', ['paired_trial']] | ['2', ['paired_trial']] | ['2', ['paired_trial']] |
| same_marginals_unpaired_only | NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE | empty | None | 1 | None | None | None |
| same_marginals_absolute_refuted | MINIMUM_RESOLVING_MENU | empty | 0 | 0 | ['0', []] | ['0', []] | ['0', []] |
| obligation_shift_three_worlds_harm_only | MINIMUM_RESOLVING_MENU | paired_trial | 2 | 2 | ['2', ['paired_trial']] | ['3', ['c_log', 'paired_trial']] | ['2', ['paired_trial']] |
| obligation_shift_three_worlds_completion | MINIMUM_RESOLVING_MENU | c_log | 1 | 2 | ['1', ['c_log']] | ['1', ['c_log']] | ['1', ['c_log']] |
| obligation_shift_three_worlds_useful | MINIMUM_RESOLVING_MENU | paired_trial | 2 | 2 | ['2', ['paired_trial']] | ['3', ['c_log', 'paired_trial']] | ['2', ['paired_trial']] |
| reference_rounding_trap | MINIMUM_RESOLVING_MENU | paired_trial | 2 | 1 | ['2', ['paired_trial']] | ['2', ['paired_trial']] | ['2', ['paired_trial']] |
| greedy_cover_counterexample | MINIMUM_RESOLVING_MENU | B, C | 4 | 6 | ['4', ['B', 'C']] | ['6', ['A', 'B', 'C']] | ['4', ['B', 'C']] |
| supervisor_two_cheap_sources | MINIMUM_RESOLVING_MENU | x, y | 2 | 4 | ['2', ['x', 'y']] | ['2', ['x', 'y']] | ['2', ['x', 'y']] |
| zero_cost_required_and_redundant | MINIMUM_RESOLVING_MENU | A | 0 | 1 | ['0', ['A']] | ['0', ['A']] | ['0', ['A']] |
| cost_priority_before_cardinality | MINIMUM_RESOLVING_MENU | cheapA, cheapB | 2/3 | 2 | ['2/3', ['cheapA', 'cheapB']] | ['2/3', ['cheapA', 'cheapB']] | ['2/3', ['cheapA', 'cheapB']] |
| finite_sample_overlap | MINIMUM_RESOLVING_MENU | e0 | 1 | 1 | ['1', ['e0']] | ['1', ['e0']] | ['1', ['e0']] |
| fractional_cost_tolerance_trap | MINIMUM_RESOLVING_MENU | B | 999999999999999999999999999999/1000000000000000000000000000000 | 1 | ['999999999999999999999999999999/1000000000000000000000000000000', ['B']] | ['999999999999999999999999999999/1000000000000000000000000000000', ['B']] | ['999999999999999999999999999999/1000000000000000000000000000000', ['B']] |
| unanimous_true_is_not_population_certificate | MINIMUM_RESOLVING_MENU | empty | 0 | 0 | ['0', []] | ['0', []] | ['0', []] |
| opposing_empty_menu | NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE | empty | None | 1 | None | None | None |

## Independent checks and actual totals

- 15 named analytical cases, including same-marginal
  harm worlds, obligation switching, zero/duplicate costs, empty menu, overlapping
  noisy laws and probability/cost precision traps.
- 504 seeded cases: every combination of 2–8 worlds and 1–6 experiments has 12
  fixed-seed replications, seed 2026111901. All 504 agree with exact exhaustive
  enumeration, the independent integer program and the supplied checker.
- 42160 exhaustive deterministic-binary cases:
  all nonconstant verdict assignments, all outcome matrices and all 0/1 cost
  assignments for n=2,3 with m=1,2,3 and n=4 with m=1,2. This is the complete
  stated finite grid, not all possible rational models with eight worlds.
- 42679
  exact independent subset-oracle agreements overall. Pair coverage, every
  selected-type deletion witness and all-menu impossibility witnesses are
  checked against the full labelled likelihood vectors.
- The integer program agrees in 518 registered/seeded cases. One rational-cost
  trap exceeds its declared safe integer representation range; exact exhaustive
  arithmetic still verifies the result. It is explicitly unsupported for that
  numeric backend, not counted as an MILP pass.
- The supplied reference's original output exactly matches the supplied JSON.
  Two additional tiny-law cases disagree because it rounds signatures to 12
  decimal places. The original checker is preserved unchanged; production uses
  exact Fractions and does not merge distinct data laws.

The source-aware exact solver and oracle inputs are in `seeded_cases.jsonl` and
`seeded_results.jsonl`; every binary exhaustive case is compactly retained in
`exhaustive_binary_cases.jsonl`. No favorable cases are dropped.

## What the comparisons establish

Among 440 resolvable seeded instances, unpruned greedy ties exact COST in 377 and
costs more in 63. Reverse deletion ties cost in 431 and costs more in 9. Cost ties
do not assert identical canonical plans. The 64 impossible cases have an opposing
pair with identical laws for every declared source. The simple seven-world
example gives greedy 6, exact 4, and reverse-deleted greedy 4; a stronger greedy
control removes that headline gap. These are standard finite-cover diagnostics,
not evidence of robot action-execution efficiency or a new optimization theorem.

The three-world obligation contrast is nonempty: absolute success selects a
one-arm source at cost 1, while useful recovery requires the paired source at
cost 2. In the two-world example both absolute-success verdicts are already
false, so the minimum resolving menu is empty with cost 0. A zero-cost empty
menu may mean a known NEGATIVE catalogue verdict, not authorization.

Different laws do not mean finite observations reveal truth. The overlapping
Bernoulli example gives positive probability to the same observation in both
worlds. All plans carry `finite_sample_resolution_guaranteed=false` and
`physical_authorization=false`. A discretized/incomplete continuous world list
cannot inherit the finite-catalogue theorem.

## Precision, source and scope negative checks

The new adapter checks serialized certificate bounds against exact 1/10 and 1/20.
Synthetic probes expose the old 1e-12 comparison tolerance; the adapter refuses
tolerance-only authorization without changing old source or sealed decisions.
Negative tests reject malformed probabilities, missing likelihoods, false
couplings, unknown propensity, world-class-dependent participant selection,
new-skill menu items and attempts to claim continuous-population completeness.
Unmodelled correlations between individually equal experiment laws require a
declared JOINT menu item; they cannot justify a stronger impossibility claim.

The frozen full run passed all 5 phases in 94.02s,
with 80.36 child CPU seconds and zero new physics,
training or robot outcomes. Exact-world auditing alone took
20.53s. The full maintained log is
`research/err_method_challenge/final/logs/maintained_tests.txt`; the focused log is `focused_tests.txt`.
The final source/archive/reproduction receipts add total resource accounting.
