# DSRE: operational recovery justification, calibration and observation robustness

Evidence: `results/dsre-operational/20261114T140659Z`. Base `c2f77332f0a72b7f3930e846c1d4e0a8f82da67b`; branch `research/dsre-operational-full-paper`. Exact local commit, archive and resource accounting are in completion_manifest.json.

Registered 520 new parents: 360 calibration plus 160 disjoint test. Completed 360/520; new test 0/160 parents, 0/320 checkpoints. Missing/partial IDs and all secondary qualified cells are explicit in missingness.json. Prior 333-parent follow-up and earlier interrupted cohort remain sealed and unchanged.

## Scientific and operational contract

The fixed question is which observable facts suffice to justify a fixed robot intervention relative to paired outcomes, and why justification fails. Exact sufficient rules, support/ties, two skills, horizon, utility and witnesses remain unchanged. B7 and the equally wrapped ordinary risk rule are mathematically equivalent; no new pure-rule algorithm or controller is claimed. Runtime schemas forbid outcome labels and require common facts to agree across comparators. No new model fits were performed. Four existing depth-1/2 trees at budget one are loaded without training; full-reference outcomes remain development only.

Abstention is defer/stop and contributes zero to unconditional autonomous completion. Conditional success among actions is separate. Initially unsuccessful means terminal task success is false at the decision checkpoint; it does not assert a separately annotated failure event or that a normal unfinished prefix is a failure. Required recovery means recover-only adequacy relative to the two fixed skills and horizon. Neither-success actions are inadequate even if intervention regret relative to the best available action is zero.

All new paired measurements use unchanged CPU physics, complete reset/action-prefix reconstruction and controller/model checks. The registered test planned an additional calibrated selected branch after a fresh reset/prefix. Its first guard failed before a continuation, so no selected repeat was completed. Paired outcome lookup remains deterministic counterfactual estimation and is not misrepresented as a standalone online campaign.

## Independent calibration and exact bounds

Actual calibration: 360/360 parents. Primary target: assigned-parent any-error probability <=10% for task/action strata, under the two registered conditions and fixed seed distribution. Any bad assigned condition marks that parent erroneous. All 17 methods use global delta=.05/(4*17), requiring 69 zero-error assigned parents; primary four-stratum diagnostic delta=.0125 requires 42. Only the stricter global gate enables actions. The bound is not for arbitrary time points, shifted observations, hardware or checkpoint-weighted sampling.

| Method | Task/action | Assigned parents | Erroneous parents | Primary diagnostic upper | Global-family upper | Operational status |
|---|---|---:|---:|---:|---:|---|
| DSRE_strict | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| DSRE_strict | PickCube-v1/recover | 13 | 0 | 28.615% | 42.594% | NOT_CERTIFIED |
| DSRE_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| DSRE_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B7 | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| B7 | PickCube-v1/recover | 13 | 0 | 28.615% | 42.594% | NOT_CERTIFIED |
| B7 | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B7 | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| DSRE_risk | PickCube-v1/continue | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| DSRE_risk | PickCube-v1/recover | 13 | 0 | 28.615% | 42.594% | NOT_CERTIFIED |
| DSRE_risk | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| DSRE_risk | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| B7_risk | PickCube-v1/continue | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| B7_risk | PickCube-v1/recover | 13 | 0 | 28.615% | 42.594% | NOT_CERTIFIED |
| B7_risk | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B7_risk | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| B1_one_strict | PickCube-v1/continue | 134 | 0 | 3.217% | 5.242% | CERTIFIED_PARENT_ACTION_SCOPE |
| B1_one_strict | PickCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B1_one_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B1_one_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B1_two_strict | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| B1_two_strict | PickCube-v1/recover | 12 | 0 | 30.592% | 45.188% | NOT_CERTIFIED |
| B1_two_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B1_two_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_strict | PickCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_strict | PickCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART2_strict | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| CART2_strict | PickCube-v1/recover | 11 | 0 | 32.858% | 48.104% | NOT_CERTIFIED |
| CART2_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART2_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART2_pruned_strict | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| CART2_pruned_strict | PickCube-v1/recover | 11 | 0 | 32.858% | 48.104% | NOT_CERTIFIED |
| CART2_pruned_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART2_pruned_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_beta10 | PickCube-v1/continue | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| CART1_beta10 | PickCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_beta10 | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART1_beta10 | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| CART2_beta10 | PickCube-v1/continue | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| CART2_beta10 | PickCube-v1/recover | 11 | 0 | 32.858% | 48.104% | NOT_CERTIFIED |
| CART2_beta10 | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| CART2_beta10 | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| B5_beta10 | PickCube-v1/continue | 180 | 13 | 12.770% | 15.396% | NOT_CERTIFIED |
| B5_beta10 | PickCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B5_beta10 | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B5_beta10 | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| B0_continue | PickCube-v1/continue | 180 | 105 | 66.598% | 69.780% | NOT_CERTIFIED |
| B0_continue | PickCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B0_continue | PushCube-v1/continue | 180 | 180 | 100.000% | 100.000% | NOT_CERTIFIED |
| B0_continue | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B0_recover | PickCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B0_recover | PickCube-v1/recover | 180 | 51 | 36.539% | 40.003% | NOT_CERTIFIED |
| B0_recover | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| B0_recover | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| full_signature_strict | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| full_signature_strict | PickCube-v1/recover | 16 | 2 | 41.954% | 54.044% | NOT_CERTIFIED |
| full_signature_strict | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| full_signature_strict | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| greedy_pure_rule | PickCube-v1/continue | 180 | 0 | 2.405% | 3.929% | CERTIFIED_PARENT_ACTION_SCOPE |
| greedy_pure_rule | PickCube-v1/recover | 13 | 0 | 28.615% | 42.594% | NOT_CERTIFIED |
| greedy_pure_rule | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| greedy_pure_rule | PushCube-v1/recover | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| policy_faithful | PickCube-v1/continue | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |
| policy_faithful | PickCube-v1/recover | 11 | 0 | 32.858% | 48.104% | NOT_CERTIFIED |
| policy_faithful | PushCube-v1/continue | 0 | 0 | 100.000% | 100.000% | NOT_CERTIFIED |
| policy_faithful | PushCube-v1/recover | 180 | 1 | 3.492% | 5.194% | CERTIFIED_PARENT_ACTION_SCOPE |

Primary unqualified strata and remaining sample limitations:

- DSRE_risk|PickCube-v1|recover: 13 assigned, 0 erroneous. At least 56 additional independent assigned parents with no additional errors would be needed to reach the global zero-error minimum. More unassigned nominal trials do not directly qualify this action. A future independently fixed cohort must preserve the assignment distribution or state its changed estimand; this is a sample limitation, not authorization for replenishment.
- DSRE_risk|PushCube-v1|continue: 0 assigned, 0 erroneous. At least 69 additional independent assigned parents with no additional errors would be needed to reach the global zero-error minimum. More unassigned nominal trials do not directly qualify this action. A future independently fixed cohort must preserve the assignment distribution or state its changed estimand; this is a sample limitation, not authorization for replenishment.

Calibration selection is outcome-independent; the immutable decision/seal precedes every test parent. No threshold, allocation, rule, action or reference is updated from test labels. Empty/underpowered strata stay NOT CERTIFIED. No targeted replenishment was performed. Conditional certification is limited to enabled strata and stated simulator/observation scope.

## Disjoint held-out operational results

Counts are recommendations / successful / unacceptable. All denominators include deferral; reported autonomous completion counts are exactly successful selected actions. Proposed and globally gated modes are separated. Full-signature is upper-information, not a fair minimum-explanation length competitor; policy-faithful explains a tree label rather than action adequacy.

### PickCube-v1: proposal

| Method | N | Rec/good/bad | Deferred | Conditional good | Autonomous completion | Initially unsuccessful good/N | Required recovery good | Unnecessary recovery, initially successful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DSRE_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| DSRE_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_one_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_two_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_pruned_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B5_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_continue | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_recover | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| full_signature_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| greedy_pure_rule | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| policy_faithful | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
### PickCube-v1: calibrated

| Method | N | Rec/good/bad | Deferred | Conditional good | Autonomous completion | Initially unsuccessful good/N | Required recovery good | Unnecessary recovery, initially successful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DSRE_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| DSRE_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_one_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_two_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_pruned_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B5_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_continue | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_recover | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| full_signature_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| greedy_pure_rule | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| policy_faithful | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
### PushCube-v1: proposal

| Method | N | Rec/good/bad | Deferred | Conditional good | Autonomous completion | Initially unsuccessful good/N | Required recovery good | Unnecessary recovery, initially successful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DSRE_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| DSRE_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_one_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_two_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_pruned_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B5_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_continue | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_recover | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| full_signature_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| greedy_pure_rule | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| policy_faithful | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
### PushCube-v1: calibrated

| Method | N | Rec/good/bad | Deferred | Conditional good | Autonomous completion | Initially unsuccessful good/N | Required recovery good | Unnecessary recovery, initially successful |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DSRE_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| DSRE_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B7_risk | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_one_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B1_two_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_pruned_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART1_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| CART2_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B5_beta10 | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_continue | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| B0_recover | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| full_signature_strict | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| greedy_pure_rule | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |
| policy_faithful | 0 | 0/0/0 | 0 | N/A | NOT ESTIMABLE | 0/0 | 0 | 0 |

**No complete held-out test parent exists. All test rates and effects are NOT ESTIMABLE; zero counts are empty populations, not measured zero success or error.** The first test parent failed the selected reset qualification before any selected continuation. One independently qualified paired checkpoint is retained as secondary evidence; it is never promoted to a completed parent. The remaining 159 parents are untouched. See study_halt.json and selected_qualification_failure_diagnosis.json. No physics was resumed, no seeds replaced and no frozen source amended.

## Calibration cohort: descriptive, gates fitted on these errors

| Task | Method | N | Gated good/bad/defer | Initially unsuccessful good/N | Required recoveries | Maintained success |
|---|---|---:|---:|---:|---:|---:|
| PickCube-v1 | DSRE_strict | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | B7 | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | DSRE_risk | 360 | 254/1/105 | 4/109 | 0 | 250 |
| PickCube-v1 | B7_risk | 360 | 254/1/105 | 4/109 | 0 | 250 |
| PickCube-v1 | B1_one_strict | 360 | 134/0/226 | 2/109 | 0 | 132 |
| PickCube-v1 | B1_two_strict | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | CART1_strict | 360 | 0/0/360 | 0/109 | 0 | 0 |
| PickCube-v1 | CART2_strict | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | CART2_pruned_strict | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | CART1_beta10 | 360 | 255/1/104 | 4/109 | 0 | 251 |
| PickCube-v1 | CART2_beta10 | 360 | 255/1/104 | 4/109 | 0 | 251 |
| PickCube-v1 | B5_beta10 | 360 | 0/0/360 | 0/109 | 0 | 0 |
| PickCube-v1 | B0_continue | 360 | 0/0/360 | 0/109 | 0 | 0 |
| PickCube-v1 | B0_recover | 360 | 0/0/360 | 0/109 | 0 | 0 |
| PickCube-v1 | full_signature_strict | 360 | 185/0/175 | 2/109 | 0 | 183 |
| PickCube-v1 | greedy_pure_rule | 360 | 183/0/177 | 2/109 | 0 | 181 |
| PickCube-v1 | policy_faithful | 360 | 255/1/104 | 4/109 | 0 | 251 |
| PushCube-v1 | DSRE_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | B7 | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | DSRE_risk | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | B7_risk | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | B1_one_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | B1_two_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | CART1_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | CART2_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | CART2_pruned_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | CART1_beta10 | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | CART2_beta10 | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | B5_beta10 | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | B0_continue | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | B0_recover | 360 | 359/1/0 | 359/360 | 183 | 0 |
| PushCube-v1 | full_signature_strict | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | greedy_pure_rule | 360 | 0/0/360 | 0/360 | 0 | 0 |
| PushCube-v1 | policy_faithful | 360 | 359/1/0 | 359/360 | 183 | 0 |

Primary gated outcome decomposition for this same labeled population:

| Task | Outcome/start subgroup | N | Good/bad/defer | Required recovery | Maintained success |
|---|---|---:|---:|---:|---:|
| PickCube-v1 | continue_only | 70 | 70/0/0 | 0 | 66 |
| PickCube-v1 | recover_only | 83 | 0/1/82 | 0 | 0 |
| PickCube-v1 | both | 185 | 184/0/1 | 0 | 184 |
| PickCube-v1 | neither | 22 | 0/0/22 | 0 | 0 |
| PickCube-v1 | initial_success | 251 | 250/0/1 | 0 | 250 |
| PickCube-v1 | initial_failure | 109 | 4/1/104 | 0 | 0 |
| PushCube-v1 | continue_only | 1 | 0/1/0 | 0 | 0 |
| PushCube-v1 | recover_only | 183 | 183/0/0 | 183 | 0 |
| PushCube-v1 | both | 176 | 176/0/0 | 0 | 0 |
| PushCube-v1 | neither | 0 | 0/0/0 | 0 | 0 |
| PushCube-v1 | initial_success | 0 | 0/0/0 | 0 | 0 |
| PushCube-v1 | initial_failure | 360 | 359/1/0 | 183 | 0 |
## Previously inspected 333-parent follow-up: exploratory application of new gates, not new held-out confirmation

| Task | Method | N | Gated good/bad/defer | Initially unsuccessful good/N | Required recoveries | Maintained success |
|---|---|---:|---:|---:|---:|---:|
| PickCube-v1 | DSRE_strict | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | B7 | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | DSRE_risk | 332 | 224/0/108 | 1/109 | 0 | 223 |
| PickCube-v1 | B7_risk | 332 | 224/0/108 | 1/109 | 0 | 223 |
| PickCube-v1 | B1_one_strict | 332 | 129/0/203 | 0/109 | 0 | 129 |
| PickCube-v1 | B1_two_strict | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | CART1_strict | 332 | 0/0/332 | 0/109 | 0 | 0 |
| PickCube-v1 | CART2_strict | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | CART2_pruned_strict | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | CART1_beta10 | 332 | 224/0/108 | 1/109 | 0 | 223 |
| PickCube-v1 | CART2_beta10 | 332 | 224/0/108 | 1/109 | 0 | 223 |
| PickCube-v1 | B5_beta10 | 332 | 0/0/332 | 0/109 | 0 | 0 |
| PickCube-v1 | B0_continue | 332 | 0/0/332 | 0/109 | 0 | 0 |
| PickCube-v1 | B0_recover | 332 | 0/0/332 | 0/109 | 0 | 0 |
| PickCube-v1 | full_signature_strict | 332 | 171/0/161 | 1/109 | 0 | 170 |
| PickCube-v1 | greedy_pure_rule | 332 | 170/0/162 | 1/109 | 0 | 169 |
| PickCube-v1 | policy_faithful | 332 | 224/0/108 | 1/109 | 0 | 223 |
| PushCube-v1 | DSRE_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | B7 | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | DSRE_risk | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | B7_risk | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | B1_one_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | B1_two_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | CART1_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | CART2_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | CART2_pruned_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | CART1_beta10 | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | CART2_beta10 | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | B5_beta10 | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | B0_continue | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | B0_recover | 334 | 334/0/0 | 334/334 | 167 | 0 |
| PushCube-v1 | full_signature_strict | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | greedy_pure_rule | 334 | 0/0/334 | 0/334 | 0 | 0 |
| PushCube-v1 | policy_faithful | 334 | 334/0/0 | 334/334 | 167 | 0 |

Primary gated outcome decomposition for this same labeled population:

| Task | Outcome/start subgroup | N | Good/bad/defer | Required recovery | Maintained success |
|---|---|---:|---:|---:|---:|
| PickCube-v1 | continue_only | 60 | 60/0/0 | 0 | 59 |
| PickCube-v1 | recover_only | 84 | 0/0/84 | 0 | 0 |
| PickCube-v1 | both | 164 | 164/0/0 | 0 | 164 |
| PickCube-v1 | neither | 24 | 0/0/24 | 0 | 0 |
| PickCube-v1 | initial_success | 223 | 223/0/0 | 0 | 223 |
| PickCube-v1 | initial_failure | 109 | 1/0/108 | 0 | 0 |
| PushCube-v1 | continue_only | 0 | 0/0/0 | 0 | 0 |
| PushCube-v1 | recover_only | 167 | 167/0/0 | 167 | 0 |
| PushCube-v1 | both | 167 | 167/0/0 | 0 | 0 |
| PushCube-v1 | neither | 0 | 0/0/0 | 0 | 0 |
| PushCube-v1 | initial_success | 0 | 0/0/0 | 0 | 0 |
| PushCube-v1 | initial_failure | 334 | 334/0/0 | 167 | 0 |

### Exploratory historical paired effects; not the missing primary estimate

| Task/contrast | Population | Completion difference [95%] |
|---|---|---:|
| PickCube-v1/DSRE_risk-DSRE_strict | all | +16.27 [+12.95, +19.88] pp |
| PickCube-v1/DSRE_risk-DSRE_strict | initial_failure | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-DSRE_strict | initial_success | +24.22 [+20.09, +28.09] pp |
| PickCube-v1/DSRE_risk-DSRE_strict | recover_only | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B7_risk | all | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B7_risk | initial_failure | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B7_risk | initial_success | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B7_risk | recover_only | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-CART2_beta10 | all | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-CART2_beta10 | initial_failure | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-CART2_beta10 | initial_success | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-CART2_beta10 | recover_only | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B5_beta10 | all | +67.47 [+63.86, +71.08] pp |
| PickCube-v1/DSRE_risk-B5_beta10 | initial_failure | +0.92 [+0.00, +2.91] pp |
| PickCube-v1/DSRE_risk-B5_beta10 | initial_success | +100.00 [+100.00, +100.00] pp |
| PickCube-v1/DSRE_risk-B5_beta10 | recover_only | +0.00 [+0.00, +0.00] pp |
| PickCube-v1/DSRE_risk-B0_recover | all | +67.47 [+63.86, +71.08] pp |
| PickCube-v1/DSRE_risk-B0_recover | initial_failure | +0.92 [+0.00, +2.91] pp |
| PickCube-v1/DSRE_risk-B0_recover | initial_success | +100.00 [+100.00, +100.00] pp |
| PickCube-v1/DSRE_risk-B0_recover | recover_only | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-DSRE_strict | all | +100.00 [+100.00, +100.00] pp |
| PushCube-v1/DSRE_risk-DSRE_strict | initial_failure | +100.00 [+100.00, +100.00] pp |
| PushCube-v1/DSRE_risk-DSRE_strict | initial_success | N/A |
| PushCube-v1/DSRE_risk-DSRE_strict | recover_only | +100.00 [+100.00, +100.00] pp |
| PushCube-v1/DSRE_risk-B7_risk | all | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B7_risk | initial_failure | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B7_risk | initial_success | N/A |
| PushCube-v1/DSRE_risk-B7_risk | recover_only | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-CART2_beta10 | all | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-CART2_beta10 | initial_failure | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-CART2_beta10 | initial_success | N/A |
| PushCube-v1/DSRE_risk-CART2_beta10 | recover_only | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B5_beta10 | all | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B5_beta10 | initial_failure | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B5_beta10 | initial_success | N/A |
| PushCube-v1/DSRE_risk-B5_beta10 | recover_only | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B0_recover | all | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B0_recover | initial_failure | +0.00 [+0.00, +0.00] pp |
| PushCube-v1/DSRE_risk-B0_recover | initial_success | N/A |
| PushCube-v1/DSRE_risk-B0_recover | recover_only | +0.00 [+0.00, +0.00] pp |

## Primary paired uncertainty and strong controls

4000 seed-parent paired draws, PCG64 seed2026111401+taskindex, both conditions kept together. All task parents remain the subgroup resampling frame. These effect intervals are distinct from the exact binomial calibration gate. Zero-variation intervals are not population safety bounds.

| Task, risk-tier minus comparator | Population | Completion difference [95%] | Unacceptable difference [95%] | Required-recovery difference [95%] |
|---|---|---:|---:|---:|
| PickCube-v1, DSRE_risk-DSRE_strict | all | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-DSRE_strict | initial_failure | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-DSRE_strict | initial_success | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-DSRE_strict | recover_only | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B7_risk | all | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B7_risk | initial_failure | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B7_risk | initial_success | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B7_risk | recover_only | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-CART2_beta10 | all | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-CART2_beta10 | initial_failure | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-CART2_beta10 | initial_success | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-CART2_beta10 | recover_only | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B5_beta10 | all | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B5_beta10 | initial_failure | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B5_beta10 | initial_success | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B5_beta10 | recover_only | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B0_recover | all | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B0_recover | initial_failure | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B0_recover | initial_success | N/A | N/A | N/A |
| PickCube-v1, DSRE_risk-B0_recover | recover_only | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-DSRE_strict | all | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-DSRE_strict | initial_failure | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-DSRE_strict | initial_success | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-DSRE_strict | recover_only | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B7_risk | all | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B7_risk | initial_failure | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B7_risk | initial_success | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B7_risk | recover_only | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-CART2_beta10 | all | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-CART2_beta10 | initial_failure | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-CART2_beta10 | initial_success | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-CART2_beta10 | recover_only | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B5_beta10 | all | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B5_beta10 | initial_failure | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B5_beta10 | initial_success | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B5_beta10 | recover_only | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B0_recover | all | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B0_recover | initial_failure | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B0_recover | initial_success | N/A | N/A | N/A |
| PushCube-v1, DSRE_risk-B0_recover | recover_only | N/A | N/A | N/A |

### Four outcome classes and initially successful versus unsuccessful starts

| Task | Primary gated population | N | Rec/good/bad | Continue/recover | Maintained-success completions | Initially unsuccessful completions | Required-recovery completions |
|---|---|---:|---:|---:|---:|---:|---:|
| PickCube-v1 | initial_success | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PickCube-v1 | initial_failure | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PickCube-v1 | continue_only | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PickCube-v1 | recover_only | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PickCube-v1 | both | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PickCube-v1 | neither | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | initial_success | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | initial_failure | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | continue_only | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | recover_only | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | both | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |
| PushCube-v1 | neither | 0 | 0/0/0 | 0/0 | 0 | 0 | 0 |

### Condition-level matched comparisons

| Task | Condition | Method | Globally gated rec/good/bad | Deferred |
|---|---|---|---:|---:|

## Qualified selected physical execution

New selected-action continuations: 0; stopped/deferred checkpoints: 0; future-trajectory disagreements: 0; independently rederived action discrepancy maximum: 0. Every executed branch has a separate reset/prefix, outcome-free decision payload and calibration hash. Repeated branches share their original parent and never inflate statistical N.

## Observation corruption: inspected historical cohort, offline only

Use the already inspected 333-parent/666-checkpoint suffix, not independent calibration. The same corrupted predecision packet is shared by methods; original branch outcomes are unchanged. Twelve scenarios are all reported. Gaussian replicates and two conditions never become independent parents. Applying the clean gate under corruption does not transfer certification. False-fact confidence means a proposed explanation asserts a fact contradicted by the original clean telemetry; it is distinct from actual bad actions and from statistical confidence.

| Task | Method | Input scenario | Proposed good/bad/deferred | Stable actions/N | Stable certificates/N | Contradicted-fact proposals | Payload bytes / scalar fields |
|---|---|---|---:|---:|---:|---:|---:|

**Selected physical execution parity is NOT ASSESSABLE.** Zero future disagreements and zero maximum action discrepancy above mean zero executed branches, not observed perfect agreement. The first guard failed before a selected continuation; its live diagnostics were not retained. The offline contact list/tuple regression demonstrates a sufficient software defect, not actual selected-trajectory parity. qualification_normalization_candidate.patch is unexecuted future engineering repair; the frozen attempted runner and evidence remain unchanged.

| PickCube-v1 | DSRE_strict | clean | 187/0/145 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PickCube-v1 | DSRE_risk | clean | 241/0/91 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PickCube-v1 | B7_risk | clean | 241/0/91 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PickCube-v1 | B5_beta10 | clean | 224/17/91 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PickCube-v1 | CART2_beta10 | clean | 240/0/92 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PickCube-v1 | policy_faithful | clean | 240/0/92 | 332/332 | 332/332 | 0 | 638.7/24.0 |
| PushCube-v1 | DSRE_strict | clean | 0/0/334 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | DSRE_risk | clean | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B7_risk | clean | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B5_beta10 | clean | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | CART2_beta10 | clean | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | policy_faithful | clean | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PickCube-v1 | DSRE_strict | missing_optional | 145/0/187 | 290/332 | 290/332 | 0 | 638.7/24.0 |
| PickCube-v1 | DSRE_risk | missing_optional | 240/0/92 | 331/332 | 290/332 | 0 | 638.7/24.0 |
| PickCube-v1 | B7_risk | missing_optional | 240/0/92 | 331/332 | 290/332 | 0 | 638.7/24.0 |
| PickCube-v1 | B5_beta10 | missing_optional | 224/16/92 | 331/332 | 331/332 | 0 | 638.7/24.0 |
| PickCube-v1 | CART2_beta10 | missing_optional | 16/0/316 | 108/332 | 108/332 | 0 | 638.7/24.0 |
| PickCube-v1 | policy_faithful | missing_optional | 16/0/316 | 108/332 | 108/332 | 0 | 638.7/24.0 |
| PushCube-v1 | DSRE_strict | missing_optional | 0/0/334 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | DSRE_risk | missing_optional | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B7_risk | missing_optional | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B5_beta10 | missing_optional | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | CART2_beta10 | missing_optional | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | policy_faithful | missing_optional | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PickCube-v1 | DSRE_strict | missing_history | 186/0/146 | 331/332 | 331/332 | 0 | 328.0/12.0 |
| PickCube-v1 | DSRE_risk | missing_history | 240/0/92 | 331/332 | 331/332 | 0 | 328.0/12.0 |
| PickCube-v1 | B7_risk | missing_history | 240/0/92 | 331/332 | 331/332 | 0 | 328.0/12.0 |
| PickCube-v1 | B5_beta10 | missing_history | 224/16/92 | 331/332 | 331/332 | 0 | 328.0/12.0 |
| PickCube-v1 | CART2_beta10 | missing_history | 240/0/92 | 332/332 | 332/332 | 0 | 328.0/12.0 |
| PickCube-v1 | policy_faithful | missing_history | 240/0/92 | 332/332 | 332/332 | 0 | 328.0/12.0 |
| PushCube-v1 | DSRE_strict | missing_history | 0/0/334 | 334/334 | 334/334 | 0 | 308.4/12.0 |
| PushCube-v1 | DSRE_risk | missing_history | 334/0/0 | 334/334 | 334/334 | 0 | 308.4/12.0 |
| PushCube-v1 | B7_risk | missing_history | 334/0/0 | 334/334 | 334/334 | 0 | 308.4/12.0 |
| PushCube-v1 | B5_beta10 | missing_history | 334/0/0 | 334/334 | 334/334 | 0 | 308.4/12.0 |
| PushCube-v1 | CART2_beta10 | missing_history | 0/0/334 | 0/334 | 0/334 | 0 | 308.4/12.0 |
| PushCube-v1 | policy_faithful | missing_history | 0/0/334 | 0/334 | 334/334 | 0 | 308.4/12.0 |
| PickCube-v1 | DSRE_strict | missing_pose | 129/0/203 | 274/332 | 274/332 | 0 | 285.5/6.0 |
| PickCube-v1 | DSRE_risk | missing_pose | 129/0/203 | 220/332 | 220/332 | 0 | 285.5/6.0 |
| PickCube-v1 | B7_risk | missing_pose | 129/0/203 | 220/332 | 220/332 | 0 | 285.5/6.0 |
| PickCube-v1 | B5_beta10 | missing_pose | 129/0/203 | 220/332 | 220/332 | 0 | 285.5/6.0 |
| PickCube-v1 | CART2_beta10 | missing_pose | 0/0/332 | 92/332 | 92/332 | 0 | 285.5/6.0 |
| PickCube-v1 | policy_faithful | missing_pose | 0/0/332 | 92/332 | 92/332 | 0 | 285.5/6.0 |
| PushCube-v1 | DSRE_strict | missing_pose | 0/0/334 | 334/334 | 334/334 | 0 | 264.0/6.0 |
| PushCube-v1 | DSRE_risk | missing_pose | 334/0/0 | 334/334 | 334/334 | 0 | 264.0/6.0 |
| PushCube-v1 | B7_risk | missing_pose | 334/0/0 | 334/334 | 334/334 | 0 | 264.0/6.0 |
| PushCube-v1 | B5_beta10 | missing_pose | 334/0/0 | 334/334 | 334/334 | 0 | 264.0/6.0 |
| PushCube-v1 | CART2_beta10 | missing_pose | 0/0/334 | 0/334 | 0/334 | 0 | 264.0/6.0 |
| PushCube-v1 | policy_faithful | missing_pose | 0/0/334 | 0/334 | 334/334 | 0 | 264.0/6.0 |
| PickCube-v1 | DSRE_strict | noise001_r0 | 195/0/137 | 318/332 | 317/332 | 11 | 638.4/24.0 |
| PickCube-v1 | DSRE_risk | noise001_r0 | 241/0/91 | 332/332 | 317/332 | 11 | 638.4/24.0 |
| PickCube-v1 | B7_risk | noise001_r0 | 241/0/91 | 332/332 | 317/332 | 11 | 638.4/24.0 |
| PickCube-v1 | B5_beta10 | noise001_r0 | 224/17/91 | 332/332 | 331/332 | 0 | 638.4/24.0 |
| PickCube-v1 | CART2_beta10 | noise001_r0 | 239/0/93 | 331/332 | 317/332 | 14 | 638.4/24.0 |
| PickCube-v1 | policy_faithful | noise001_r0 | 239/0/93 | 331/332 | 331/332 | 0 | 638.4/24.0 |
| PushCube-v1 | DSRE_strict | noise001_r0 | 0/0/334 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PushCube-v1 | DSRE_risk | noise001_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PushCube-v1 | B7_risk | noise001_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PushCube-v1 | B5_beta10 | noise001_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PushCube-v1 | CART2_beta10 | noise001_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PushCube-v1 | policy_faithful | noise001_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.9/24.0 |
| PickCube-v1 | DSRE_strict | noise001_r1 | 195/0/137 | 316/332 | 315/332 | 12 | 638.2/24.0 |
| PickCube-v1 | DSRE_risk | noise001_r1 | 241/0/91 | 330/332 | 315/332 | 12 | 638.2/24.0 |
| PickCube-v1 | B7_risk | noise001_r1 | 241/0/91 | 330/332 | 315/332 | 12 | 638.2/24.0 |
| PickCube-v1 | B5_beta10 | noise001_r1 | 224/17/91 | 330/332 | 329/332 | 1 | 638.2/24.0 |
| PickCube-v1 | CART2_beta10 | noise001_r1 | 238/0/94 | 330/332 | 316/332 | 14 | 638.2/24.0 |
| PickCube-v1 | policy_faithful | noise001_r1 | 238/0/94 | 330/332 | 330/332 | 0 | 638.2/24.0 |
| PushCube-v1 | DSRE_strict | noise001_r1 | 0/0/334 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PushCube-v1 | DSRE_risk | noise001_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PushCube-v1 | B7_risk | noise001_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PushCube-v1 | B5_beta10 | noise001_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PushCube-v1 | CART2_beta10 | noise001_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PushCube-v1 | policy_faithful | noise001_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.8/24.0 |
| PickCube-v1 | DSRE_strict | noise001_r2 | 201/0/131 | 314/332 | 313/332 | 16 | 638.6/24.0 |
| PickCube-v1 | DSRE_risk | noise001_r2 | 240/0/92 | 331/332 | 313/332 | 16 | 638.6/24.0 |
| PickCube-v1 | B7_risk | noise001_r2 | 240/0/92 | 331/332 | 313/332 | 16 | 638.6/24.0 |
| PickCube-v1 | B5_beta10 | noise001_r2 | 224/16/92 | 331/332 | 330/332 | 0 | 638.6/24.0 |
| PickCube-v1 | CART2_beta10 | noise001_r2 | 238/0/94 | 330/332 | 313/332 | 17 | 638.6/24.0 |
| PickCube-v1 | policy_faithful | noise001_r2 | 238/0/94 | 330/332 | 330/332 | 0 | 638.6/24.0 |
| PushCube-v1 | DSRE_strict | noise001_r2 | 0/0/334 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PushCube-v1 | DSRE_risk | noise001_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PushCube-v1 | B7_risk | noise001_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PushCube-v1 | B5_beta10 | noise001_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PushCube-v1 | CART2_beta10 | noise001_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PushCube-v1 | policy_faithful | noise001_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 620.0/24.0 |
| PickCube-v1 | DSRE_strict | noise005_r0 | 215/2/115 | 296/332 | 296/332 | 33 | 638.3/24.0 |
| PickCube-v1 | DSRE_risk | noise005_r0 | 243/2/87 | 323/332 | 296/332 | 33 | 638.3/24.0 |
| PickCube-v1 | B7_risk | noise005_r0 | 243/2/87 | 323/332 | 296/332 | 33 | 638.3/24.0 |
| PickCube-v1 | B5_beta10 | noise005_r0 | 224/21/87 | 328/332 | 322/332 | 5 | 638.3/24.0 |
| PickCube-v1 | CART2_beta10 | noise005_r0 | 239/2/91 | 326/332 | 299/332 | 33 | 638.3/24.0 |
| PickCube-v1 | policy_faithful | noise005_r0 | 239/2/91 | 326/332 | 326/332 | 6 | 638.3/24.0 |
| PushCube-v1 | DSRE_strict | noise005_r0 | 0/0/334 | 334/334 | 334/334 | 0 | 619.3/24.0 |
| PushCube-v1 | DSRE_risk | noise005_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.3/24.0 |
| PushCube-v1 | B7_risk | noise005_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.3/24.0 |
| PushCube-v1 | B5_beta10 | noise005_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.3/24.0 |
| PushCube-v1 | CART2_beta10 | noise005_r0 | 334/0/0 | 334/334 | 295/334 | 39 | 619.3/24.0 |
| PushCube-v1 | policy_faithful | noise005_r0 | 334/0/0 | 334/334 | 334/334 | 0 | 619.3/24.0 |
| PickCube-v1 | DSRE_strict | noise005_r1 | 225/3/104 | 289/332 | 289/332 | 42 | 638.3/24.0 |
| PickCube-v1 | DSRE_risk | noise005_r1 | 243/3/86 | 319/332 | 289/332 | 42 | 638.3/24.0 |
| PickCube-v1 | B7_risk | noise005_r1 | 243/3/86 | 319/332 | 289/332 | 42 | 638.3/24.0 |
| PickCube-v1 | B5_beta10 | noise005_r1 | 224/22/86 | 327/332 | 317/332 | 6 | 638.3/24.0 |
| PickCube-v1 | CART2_beta10 | noise005_r1 | 240/1/91 | 323/332 | 293/332 | 39 | 638.3/24.0 |
| PickCube-v1 | policy_faithful | noise005_r1 | 240/1/91 | 323/332 | 323/332 | 9 | 638.3/24.0 |
| PushCube-v1 | DSRE_strict | noise005_r1 | 0/0/334 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | DSRE_risk | noise005_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | B7_risk | noise005_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | B5_beta10 | noise005_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | CART2_beta10 | noise005_r1 | 334/0/0 | 334/334 | 288/334 | 46 | 619.6/24.0 |
| PushCube-v1 | policy_faithful | noise005_r1 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PickCube-v1 | DSRE_strict | noise005_r2 | 215/0/117 | 292/332 | 292/332 | 34 | 638.5/24.0 |
| PickCube-v1 | DSRE_risk | noise005_r2 | 246/0/86 | 317/332 | 292/332 | 34 | 638.5/24.0 |
| PickCube-v1 | B7_risk | noise005_r2 | 246/0/86 | 317/332 | 292/332 | 34 | 638.5/24.0 |
| PickCube-v1 | B5_beta10 | noise005_r2 | 224/22/86 | 321/332 | 316/332 | 9 | 638.5/24.0 |
| PickCube-v1 | CART2_beta10 | noise005_r2 | 239/0/93 | 325/332 | 300/332 | 30 | 638.5/24.0 |
| PickCube-v1 | policy_faithful | noise005_r2 | 239/0/93 | 325/332 | 325/332 | 5 | 638.5/24.0 |
| PushCube-v1 | DSRE_strict | noise005_r2 | 0/0/334 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | DSRE_risk | noise005_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | B7_risk | noise005_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | B5_beta10 | noise005_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PushCube-v1 | CART2_beta10 | noise005_r2 | 334/0/0 | 334/334 | 289/334 | 45 | 619.6/24.0 |
| PushCube-v1 | policy_faithful | noise005_r2 | 334/0/0 | 334/334 | 334/334 | 0 | 619.6/24.0 |
| PickCube-v1 | DSRE_strict | delay1 | 187/0/145 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PickCube-v1 | DSRE_risk | delay1 | 241/0/91 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PickCube-v1 | B7_risk | delay1 | 241/0/91 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PickCube-v1 | B5_beta10 | delay1 | 224/17/91 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PickCube-v1 | CART2_beta10 | delay1 | 240/0/92 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PickCube-v1 | policy_faithful | delay1 | 240/0/92 | 332/332 | 332/332 | 0 | 638.9/24.0 |
| PushCube-v1 | DSRE_strict | delay1 | 0/0/334 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | DSRE_risk | delay1 | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B7_risk | delay1 | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | B5_beta10 | delay1 | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | CART2_beta10 | delay1 | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PushCube-v1 | policy_faithful | delay1 | 334/0/0 | 334/334 | 334/334 | 0 | 620.2/24.0 |
| PickCube-v1 | DSRE_strict | delay5 | 187/6/139 | 321/332 | 321/332 | 11 | 638.8/24.0 |
| PickCube-v1 | DSRE_risk | delay5 | 235/6/91 | 326/332 | 321/332 | 11 | 638.8/24.0 |
| PickCube-v1 | B7_risk | delay5 | 235/6/91 | 326/332 | 321/332 | 11 | 638.8/24.0 |
| PickCube-v1 | B5_beta10 | delay5 | 224/17/91 | 332/332 | 326/332 | 0 | 638.8/24.0 |
| PickCube-v1 | CART2_beta10 | delay5 | 224/16/92 | 316/332 | 311/332 | 21 | 638.8/24.0 |
| PickCube-v1 | policy_faithful | delay5 | 224/16/92 | 316/332 | 316/332 | 16 | 638.8/24.0 |
| PushCube-v1 | DSRE_strict | delay5 | 0/0/334 | 334/334 | 334/334 | 0 | 620.6/24.0 |
| PushCube-v1 | DSRE_risk | delay5 | 334/0/0 | 334/334 | 334/334 | 0 | 620.6/24.0 |
| PushCube-v1 | B7_risk | delay5 | 334/0/0 | 334/334 | 334/334 | 0 | 620.6/24.0 |
| PushCube-v1 | B5_beta10 | delay5 | 334/0/0 | 334/334 | 334/334 | 0 | 620.6/24.0 |
| PushCube-v1 | CART2_beta10 | delay5 | 334/0/0 | 334/334 | 168/334 | 166 | 620.6/24.0 |
| PushCube-v1 | policy_faithful | delay5 | 334/0/0 | 334/334 | 334/334 | 0 | 620.6/24.0 |

Every method/scenario/mode/condition/category result is retained in observation_robustness.json and robustness_records.json. The fixed 1 mm boundary-proximity flag is retained per record. Serialized bytes/scalars describe the observed-history interface, not distinct physical sensors or acquisition cost. Abstract predicates and certificate lengths are separate; shared raw pose fields supply several predicates. Routing times include the documented all-method cached computation path, not physical sensing/actuation latency.

## Preserved history, physical cases and breadth blocker

The previous untouched suffix remains 333 parents/666 checkpoints/1332 continuations: Pick strict145->187/332, +12.65pp[9.33,16.27]; initially unsuccessful16->18/109, one extra required recovery; zero observed strict errors. Forty of42 additions were initially successful, B7 was exact, CART2/cap2 differed once, provisional CART240/332 exceeded strict187/332. Push strict0/334 versus recovery334/334 remains intact. Neither prior cohort nor the inspected preliminary33 parents/task is used as new calibration. Historical raw seals and the old unknown SIGTERM cause are unchanged.

Old physical cases and raw-source hashes remain in the previous physical_examples.json: three-fact/five-parent recovery evidence versus a neither-success collision, both-success adequacy without necessity, and Push opposing actions sharing all12 predicates. These are illustrative reference examples, not threshold tuning. The full manuscript retains these alongside new operational evidence.

Lift/Panda is blocked by the pre-outcome source-semantic gate: the old alternative is a nominal speed clip, with210/210 both-success starts and no registered failed-start recovery contrast. No new third-task physics, controller, fault or task selection occurred. This remains a material breadth limitation.

## Reproduction, tests and evidence integrity

Immutable verification: `PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_operational_finish.py --root results/dsre-operational/20261114T140659Z --stage verify`.
Recompute independent raw-action/rule, CP, paired-bootstrap, corruption and PDF audits without changing sealed evidence: `PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/dsre_operational_finish.py --root results/dsre-operational/20261114T140659Z --stage reproduce`. This creates only a scratch audit directory with read-only input links and prints its output path. It runs no physics, training or recalibration.
Regressions: `UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest`; maintained-source lint: `UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff check src scripts tests`. An additional root-wide `ruff check .` found eight pre-existing errors in immutable results/monitoring-study scripts; those historical files were preserved. The original physics is reproduced only as a separately preregistered campaign on an unused manifest, never by resuming or overwriting this sealed root.

Reproduce analysis in a scratch copy of the frozen metadata and read-only links, never in the sealed root. See commands.jsonl for the exact bounded worker commands and protocol/source hashes. The scientific scripts and config are pinned in confirmation_freeze.json. Calibration decision/seal predates all test attempts. Regression, independent raw physics/rule/direct-tree/CP and separate numerical audits are retained; these are separate same-session implementations, not external human replication. All tests, PDF font/anonymity/page checks, archive hashes, worker usage and the exact local commit appear in the final seal.

No GitHub push, conference submission, manuscript upload, new dataset, GPU training or paid API. .gitignore, uv.lock, historical evidence and unrelated changes are preserved. Calibration and corrupted-input risk must not be conflated with hardware safety or an improved recovery controller.

Measured clean inspected historical routing, all 17 methods together over 666 unique checkpoints: mean 8.8025 ms, median 0.0009 ms, p95 0.0029 ms, maximum 276.9906 ms. The frozen router memoizes identical queries; these are actual mixed cold/cached-call costs including common computations, not isolated per-method benchmarks or sensor/robot latency. Per-view times and literal/support counts are retained in the corresponding prediction records.

## Separately qualified final-evidence continuation

The historical operational campaign above remains unchanged. A newly preregistered postmortem continuation uses identical calibration and excludes the already attempted parent. It completed 159/159 untouched parents. See [DSRE_FINAL_OPERATIONAL_RESULTS.md](DSRE_FINAL_OPERATIONAL_RESULTS.md) and [DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md](DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md), with exact evidence `results/dsre-operational/20261114T180630Z`. No old result is silently replaced.
