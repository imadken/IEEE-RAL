# DSRE: independent dual-obligation results

Scientific outcome: **DUAL_OBLIGATION_CONFIRMED**. Evidence: `results/dsre-operational/20261116T193049Z-dual-obligation`.

All 256 fresh calibration parents and 128 untouched test parents completed all five conditions and both fixed actions: 1,920 paired checkpoints and 3,840 continuations. Three historical parents separately passed fresh-process qualification (15 checkpoints, 30 continuations, 2,100 future states). No seed was replaced or method retuned.

The non-degradation DSRE composition completes 393/640 versus 355/640 under the new absolute composition; paired difference 5.94 pp [3.44, 8.91]. It selects 38 of 218 necessary recoveries, attempts 42 recoveries, incurs 0 binary-outcome harms and 4 neither-success attempts, and defers 240 checkpoints. CART2's non-degradation composition completes 355/640; paired DSRE-minus-CART2 difference 5.94 pp [3.44, 8.91]. B7 is exactly identical to DSRE.

## Exploratory source-blind replication of old evidence

| Old cohort | R-only | Neither | Harm | Both | Assigned parents | Parent failure-minus-harm,95% CI |
|---|---|---|---|---|---|---|
| calibration | 90 | 10 | 0 | 1 | 66 | 15.15% [7.04, 24.00] |
| test | 40 | 10 | 0 | 0 | 32 | 31.25% [16.00, 48.49] |

These old data motivated the question and do not support a new qualification. The old zero-harm 66-parent bound at .05/68 is 10.356%, above 10%. Compact labels agree with raw matched branches and independent geometry/velocity endpoint checks. The preserved audit correction concerned a calibration-only condition assertion: old test's ten neither-success proposals are nine at minus2cm and one at plus3cm. The zero-harm counts were correct.

## Fresh six-claim calibration

| Claim | Assigned parents | Error parents | Exact upper | Qualified |
|---|---|---|---|---|
| DSRE_risk\|recover\|absolute | 64 | 9 | 27.542% | False |
| DSRE_risk\|recover\|nondegradation | 64 | 0 | 7.208% | True |
| DSRE_risk\|continue\|absolute | 256 | 1 | 2.645% | True |
| CART2_beta10\|recover\|absolute | 32 | 0 | 13.896% | False |
| CART2_beta10\|recover\|nondegradation | 32 | 0 | 13.896% | False |
| CART2_beta10\|continue\|absolute | 256 | 1 | 2.645% | True |

All six claims share target 10% and delta=.05/6. The parent unit is any assignment/any error across five conditions; n=0 is uninformative and disabled. The new absolute and harm obligations have identical assigned support within each router and the same alpha allocation. Thus their within-router difference is an error-definition difference, not an alpha change. The old .05/68 gate remains unchanged and is descriptive on these new data. No new absolute guarantee is inherited from that file. B7 uses DSRE's existing verdict, and fixed actions have no new qualification.

| Fresh cohort | Router | R cells | Assigned parents | Absolute-error parents | Harm-error parents | Parent failure-minus-harm,95% CI | Checkpoint failure-minus-harm,95% CI |
|---|---|---|---|---|---|---|---|
| calibration | DSRE | 106 | 64 | 9 | 0 | 14.06% [6.35, 22.95] | 8.49% [3.57, 14.74] |
| calibration | CART2 | 73 | 32 | 0 | 0 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |
| test | DSRE | 42 | 27 | 4 | 0 | 14.81% [3.33, 30.01] | 9.52% [1.89, 20.93] |
| test | CART2 | 30 | 15 | 0 | 0 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |

At a checkpoint absolute failure is the disjoint union of harm and neither-success. At a parent their unions may overlap: the absolute-minus-harm parent gap counts futile-error parents without harm. Cohorts are never pooled. Test estimates are descriptive and never change gates.

## Untouched paired physical outcome populations

| Condition | Cells | C-only | R-only | Both | Neither | Initially failed | Required recovery |
|---|---|---|---|---|---|---|---|
| ALL | 640 | 95 | 220 | 260 | 65 | 299 | 218 |
| nominal | 128 | 35 | 0 | 93 | 0 | 6 | 0 |
| offset001 | 128 | 30 | 14 | 81 | 3 | 24 | 14 |
| offset002 | 128 | 15 | 54 | 43 | 16 | 74 | 54 |
| offset003 | 128 | 0 | 98 | 0 | 30 | 128 | 98 |
| offset_minus002 | 128 | 15 | 54 | 43 | 16 | 67 | 52 |

Required recovery is initially unsuccessful R-only; preventive R-only and both-success maintenance receive separate counts. The primary policies use saved prospective sidecar decisions sealed for all 128 parents before any test future. Both alternatives were physically executed from the same full reconstructed prefix, controller/RNG and model state. This is fixed single-intervention evaluation, not a newly trained controller or a full closed-loop recovery system.

## Selected actions, task completion and abstention

| Policy | C/R/STOP | Successful/unsuccessful | Completion,95% CI | Conditional success,95% CI |
|---|---|---|---|---|
| always_continue | 640 / 0 / 0 | 355 / 285 | 55.47% [51.41, 59.53] | 55.47% [51.41, 59.53] |
| always_recover | 0 / 640 / 0 | 480 / 160 | 75.00% [67.50, 82.34] | 75.00% [67.50, 82.34] |
| DSRE_raw | 358 / 42 / 240 | 393 / 7 | 61.41% [57.03, 65.94] | 98.25% [96.85, 99.48] |
| CART2_raw | 358 / 30 / 252 | 385 / 3 | 60.16% [55.62, 64.69] | 99.23% [98.21, 100.00] |
| DSRE_historical | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| DSRE_absolute | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| DSRE_nondegradation | 358 / 42 / 240 | 393 / 7 | 61.41% [57.03, 65.94] | 98.25% [96.85, 99.48] |
| B7_historical | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| B7_absolute | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| B7_nondegradation | 358 / 42 / 240 | 393 / 7 | 61.41% [57.03, 65.94] | 98.25% [96.85, 99.48] |
| CART2_historical | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| CART2_absolute | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |
| CART2_nondegradation | 358 / 0 / 282 | 355 / 3 | 55.47% [51.41, 59.53] | 99.16% [98.06, 100.00] |

Absolute and nondegradation use new six-claim calibration. Historical rows apply the unchanged old gate descriptively; raw and fixed rows are unqualified comparisons. STOP receives zero selective-completion credit with no invented hold, escalation or reset outcome. Zero observed errors can yield degenerate empirical bootstrap intervals; they do not prove zero population risk.

| Policy | Required selected/eligible | R on initial failure | Preventive R-only | Harmful R | Futile R | Both-success R | Both-success maintained C/R | Futile R controls |
|---|---|---|---|---|---|---|---|---|
| always_continue | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| always_recover | 218 / 218 | 299 | 2 | 95 | 65 | 260 | 260 | 4550 |
| DSRE_raw | 38 / 218 | 42 | 0 | 0 | 4 | 0 | 260 | 280 |
| CART2_raw | 30 / 218 | 30 | 0 | 0 | 0 | 0 | 260 | 0 |
| DSRE_historical | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| DSRE_absolute | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| DSRE_nondegradation | 38 / 218 | 42 | 0 | 0 | 4 | 0 | 260 | 280 |
| B7_historical | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| B7_absolute | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| B7_nondegradation | 38 / 218 | 42 | 0 | 0 | 4 | 0 | 260 | 280 |
| CART2_historical | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| CART2_absolute | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |
| CART2_nondegradation | 0 / 218 | 0 | 0 | 0 | 0 | 0 | 260 | 0 |

For non-degradation DSRE, useful required recoveries per attempted R are 90.48% [79.07, 98.11], required-recovery recall is 17.43% [10.18, 25.44], and useful recoveries per initially failed checkpoint are 12.71% [7.30, 19.05]. These separate useful interventions from maintaining an already-successful episode.

Futile recovery burden is 4/42 attempted recoveries, 9.52% [1.89, 20.93], corresponding to 280 fixed controls. Every R alternative uses 70 controls, as does C: this is recovery-work accounting, not an incremental energy/time, collision, damage or cost-to-completion model.

## Paired comparisons at matched information and risk

| Contrast | Completion difference,95% CI | Required-recovery recall difference,95% CI | Futile-attempt burden difference,95% CI |
|---|---|---|---|
| DSRE_nondegradation minus DSRE_absolute | 5.94 pp [3.44, 8.91] | 17.43 pp [10.18, 25.44] | 0.62 pp [0.16, 1.25] |
| CART2_nondegradation minus CART2_absolute | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] |
| DSRE_nondegradation minus CART2_nondegradation | 5.94 pp [3.44, 8.91] | 17.43 pp [10.18, 25.44] | 0.62 pp [0.16, 1.25] |
| DSRE_nondegradation minus B7_nondegradation | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] |
| DSRE_nondegradation minus always_continue | 5.94 pp [3.44, 8.91] | 17.43 pp [10.18, 25.44] | 0.62 pp [0.16, 1.25] |
| DSRE_nondegradation minus always_recover | -13.59 pp [-21.88, -5.31] | -82.57 pp [-89.82, -74.56] | -9.53 pp [-13.12, -6.25] |
| DSRE_nondegradation minus DSRE_historical | 5.94 pp [3.44, 8.91] | 17.43 pp [10.18, 25.44] | 0.62 pp [0.16, 1.25] |

All descriptive 95% intervals use 4,000 paired parent resamples, PCG64 seed 2026111603, retaining five conditions together. The six exact calibration bounds alone define the simultaneous qualification family. Test intervals add no certification, tuning or favorable superiority threshold. Both branches use the same prefix; no comparison gains an additional helpful prefix.

## Observation sufficiency versus action infeasibility

| Cohort | Facts | Rows | Action feasible | Neither | Common-action signature mass | Pure ambiguity mass | Feasible mass sharing a signature with neither |
|---|---|---|---|---|---|---|---|
| calibration | 7 | 1280 | 1141 | 139 | 534 | 211 | 396 |
| calibration | 12 | 1280 | 1141 | 139 | 662 | 87 | 392 |
| test | 7 | 640 | 575 | 65 | 243 | 0 | 332 |
| test | 12 | 640 | 575 | 65 | 349 | 0 | 226 |

These are descriptive hindsight partitions of saved 7/12-fact observations, not deployed rules, risk bounds or new feature selection. A frozen-reference repertoire witness identifies a compatible inadequate reference state and does not prove the actual test checkpoint is physically infeasible. The original finite-reference minimum certificates, necessity/insufficiency witnesses and strict/provisional B7 identities are independently checked without redefining adequacy. No new minimum non-degradation certificate is claimed.

## Literal physical episode witnesses

| Class | Parent | Condition | Initial success | C | R | Selected by | Screen SHA256 prefix |
|---|---|---|---|---|---|---|---|
| R_ONLY | 18000007 | offset003 | False | False | True | DSRE_nondegradation | 7120b73fb25eacde |
| NEITHER | 18000006 | offset_minus002 | False | False | False | DSRE_nondegradation | 0364c3972a4947a7 |
| C_ONLY | 18000000 | nominal | False | True | False | always_recover | 2d56eca4a0a55829 |

Full predecision evidence literals, object/goal positions and both terminal states are preserved in physical_witnesses.json; old witnesses are in prior_replication.json. Labels are independently recomputed from the unchanged 25-mm goal-distance and 0.2 arm-velocity endpoint. A neither-success recovery is unsuccessful even when its binary non-degradation error is zero; a C-only recovery harms task success even without any measured robot-safety outcome.

## Interpretation, limits and audit

TASK_NONDEGRADATION_QUALIFIED_ONLY bounds a specified binary degradation error at the registered 10% target, conditional on source and action assignment. It does not guarantee zero harm, absolute completion, nonnegative expected policy return, physical safety, arbitrary sensor robustness or real-robot transfer. Abstention and unmeasured intervention costs prevent interpreting it as a general safe-policy-improvement theorem. Clean calibration does not qualify the stored noisy-input variants.

Candidate support, observed errors and the same confidence allocation jointly determine DSRE/CART qualification. A support-frequency difference is not algorithmic or controller superiority. B7's exact identity is retained. The novelty assessment explicitly separates prospective operational evidence from the established binary identity, selective calibration, outcome-aware rules and counterfactual evaluation.

The strong-baseline limitations matter: unqualified raw CART selects 30 required recoveries with 0 harmful and 0 futile attempts, and completes 385/640. Its calibrated refusal is a support limitation, not evidence that its proposals are physically worse. Always-recover completes 480/640 versus DSRE non-degradation's 393/640, but causes 95 binary harms and 65 futile attempts. DSRE still misses 180 of 218 necessary recoveries and defers 240/640 checkpoints. These results establish neither maximal completion nor algorithmic superiority.

Independent checks reconstruct terminal labels, full physical prefix/action/contact/model/controller traces, six bounds with separate binomial inversion and beta quantiles, sidecar eligibility/annotations and whole-cohort timing isolation. The numerical recount imports no production selector or simulator and checks every count and interval through separate direct indexed resampling. Tests, Ruff, source/user/manuscript preservation, workers, failed development checks and resource accounting are sealed beside completion_manifest.json. No manuscript is edited or pushed.

```bash
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src:scripts:/home/imad/Desktop/IEEE-RAL/results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=1
mkdir /tmp/dsre-dual-portable-review-20261116
tar -xzf docs/dsre_dual_obligation_review.tar.gz -C /tmp/dsre-dual-portable-review-20261116
uv run --no-sync python /tmp/dsre-dual-portable-review-20261116/source/scripts/dsre_dual_verify_packet.py /tmp/dsre-dual-portable-review-20261116
uv run --no-sync pytest -q tests
```

Use a fresh empty extraction directory. Portable verification is read-only statistical review; full physical truth requires the local raw archive and the independently sealed source audits. Audit/analysis commands that write outputs must run only in a disposable copy, never over sealed evidence. Exact executed commands and meters are retained locally.
