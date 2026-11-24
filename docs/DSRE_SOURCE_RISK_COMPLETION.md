# DSRE: frozen independent source-risk study results

Status: **RUNTIME_QUALIFIED_AND_DATA_COMPLETE**.

Evidence root: `results/dsre-operational/20261116T130334Z-runtime-recovery`. The runtime/source qualification passes; calibration completes 256/256 independent parents, 1,280 checkpoints and 2,560 continuations. Testing completes 128/128 parents, 640 checkpoints and 1280 continuations. Missing planned test parents: 0. No parent or condition was replaced.

The sealed DSRE risk gate completes 340/640 test checkpoints, issues 0 inadequate actions and defers 300; it selects 0/229 necessary recoveries. CART2 completes 340/640 with 0 inadequate actions and 300 deferrals under the same independent calibration. The paired completion difference is 0.00 pp [0.00, 0.00]. Recovery is disabled by calibration, so this study does not establish a qualified physical-recovery improvement. Raw intervention proposals and their actual gains/errors remain separate below.

The sole execution correction selects the already installed Lavapipe ICD in dedicated children. DSRE, the original skills, seven-fact interface, condition offsets, thresholds, router, action tie, controller and terminal-success endpoint remain unchanged. No model training or manuscript edit occurred.

## Independent action-specific calibration

Each n/k is a count of independent assigned/error parents, not checkpoints: assignment is any of five conditions; error is any failed assigned condition. Complete 256-parent calibration is mandatory. The target remains 10%, delta=.05/68 per claim, preserving the conservative family allocation. Upper=1 at n=0 is uninformative, not a measured 100% failure rate. No old-data pooling, enrichment or noise transfer occurs.

| Method | Action | Assigned parents | Error parents | Exact upper | Enabled |
|---|---|---:|---:|---:|---|
| DSRE_strict | continue | 256 | 3 | 5.148% | True |
| DSRE_strict | recover | 66 | 10 | 33.337% | False |
| B7 | continue | 256 | 3 | 5.148% | True |
| B7 | recover | 66 | 10 | 33.337% | False |
| DSRE_risk | continue | 256 | 3 | 5.148% | True |
| DSRE_risk | recover | 66 | 10 | 33.337% | False |
| B7_risk | continue | 256 | 3 | 5.148% | True |
| B7_risk | recover | 66 | 10 | 33.337% | False |
| B1_one_strict | continue | 195 | 0 | 3.633% | True |
| B1_one_strict | recover | 0 | 0 | 100.000% | False |
| B1_two_strict | continue | 256 | 3 | 5.148% | True |
| B1_two_strict | recover | 24 | 0 | 25.965% | False |
| CART1_strict | continue | 0 | 0 | 100.000% | False |
| CART1_strict | recover | 0 | 0 | 100.000% | False |
| CART2_strict | continue | 256 | 3 | 5.148% | True |
| CART2_strict | recover | 24 | 0 | 25.965% | False |
| CART2_pruned_strict | continue | 256 | 3 | 5.148% | True |
| CART2_pruned_strict | recover | 24 | 0 | 25.965% | False |
| CART1_beta10 | continue | 256 | 3 | 5.148% | True |
| CART1_beta10 | recover | 0 | 0 | 100.000% | False |
| CART2_beta10 | continue | 256 | 3 | 5.148% | True |
| CART2_beta10 | recover | 24 | 0 | 25.965% | False |
| B5_beta10 | continue | 256 | 69 | 36.528% | False |
| B5_beta10 | recover | 0 | 0 | 100.000% | False |
| B0_continue | continue | 256 | 256 | 100.000% | False |
| B0_continue | recover | 0 | 0 | 100.000% | False |
| B0_recover | continue | 0 | 0 | 100.000% | False |
| B0_recover | recover | 256 | 73 | 38.198% | False |
| full_signature_strict | continue | 256 | 0 | 2.779% | True |
| full_signature_strict | recover | 48 | 6 | 33.805% | False |
| greedy_pure_rule | continue | 256 | 3 | 5.148% | True |
| greedy_pure_rule | recover | 66 | 10 | 33.337% | False |
| policy_faithful | continue | 256 | 3 | 5.148% | True |
| policy_faithful | recover | 24 | 0 | 25.965% | False |

## Untouched test populations and physical outcomes

| Condition | Checkpoints | C-only | R-only | Both | Neither | Initially unsuccessful | Required recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL | 640 | 89 | 229 | 251 | 71 | 316 | 229 |
| nominal | 128 | 36 | 0 | 92 | 0 | 6 | 0 |
| offset001 | 128 | 33 | 5 | 87 | 3 | 15 | 5 |
| offset002 | 128 | 10 | 62 | 36 | 20 | 84 | 62 |
| offset003 | 128 | 0 | 100 | 0 | 28 | 128 | 100 |
| offset_minus002 | 128 | 10 | 62 | 36 | 20 | 83 | 62 |

Required recovery means initially unsuccessful, continue unsuccessful, recover successful. Initially successful R-only cases are preventive, and both-success cases do not establish necessity. All alternatives were physically executed from the same fully reconstructed predecision state for 70 controls. STOP gets zero selective completion credit; no STOP outcome is imputed.

## Frozen selective execution and strongest baselines

| Uncalibrated clean proposal | C / R / STOP | Adequate / inadequate | Required selected / eligible |
|---|---:|---:|---:|
| DSRE_strict | 296 / 50 / 294 | 336 / 10 | 40 / 229 |
| DSRE_risk | 340 / 50 / 250 | 380 / 10 | 40 / 229 |
| B7_risk | 340 / 50 / 250 | 380 / 10 | 40 / 229 |
| CART2_beta10 | 340 / 32 / 268 | 372 / 0 | 32 / 229 |
| B5_beta10 | 390 / 0 / 250 | 340 / 50 | 0 / 229 |
| B1_two_strict | 296 / 32 / 312 | 328 / 0 | 32 / 229 |
| B0_continue | 640 / 0 / 0 | 340 / 300 | 0 / 229 |
| B0_recover | 0 / 640 / 0 | 480 / 160 | 229 / 229 |

The proposal table is descriptive and unqualified. It retains raw strict/provisional differences and the actual always-continue/recover alternatives. The following gate table applies the independently sealed action eligibility without rerouting.

| Clean gated method | C / R / STOP | Adequate / inadequate | Required selected / eligible | Coverage, 95% CI | Completion, 95% CI |
|---|---:|---:|---:|---|---|
| DSRE_strict | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| B7 | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| DSRE_risk | 340 / 0 / 300 | 340 / 0 | 0 / 229 | 53.12% [49.69, 56.72] | 53.12% [49.69, 56.72] |
| B7_risk | 340 / 0 / 300 | 340 / 0 | 0 / 229 | 53.12% [49.69, 56.72] | 53.12% [49.69, 56.72] |
| B1_one_strict | 176 / 0 / 464 | 176 / 0 | 0 / 229 | 27.50% [24.38, 30.47] | 27.50% [24.38, 30.47] |
| B1_two_strict | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| CART1_strict | 0 / 0 / 640 | 0 / 0 | 0 / 229 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |
| CART2_strict | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| CART2_pruned_strict | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| CART1_beta10 | 340 / 0 / 300 | 340 / 0 | 0 / 229 | 53.12% [49.69, 56.72] | 53.12% [49.69, 56.72] |
| CART2_beta10 | 340 / 0 / 300 | 340 / 0 | 0 / 229 | 53.12% [49.69, 56.72] | 53.12% [49.69, 56.72] |
| B5_beta10 | 0 / 0 / 640 | 0 / 0 | 0 / 229 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |
| B0_continue | 0 / 0 / 640 | 0 / 0 | 0 / 229 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |
| B0_recover | 0 / 0 / 640 | 0 / 0 | 0 / 229 | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] |
| full_signature_strict | 253 / 0 / 387 | 253 / 0 | 0 / 229 | 39.53% [38.44, 40.62] | 39.53% [38.44, 40.62] |
| greedy_pure_rule | 296 / 0 / 344 | 296 / 0 | 0 / 229 | 46.25% [44.22, 48.44] | 46.25% [44.22, 48.44] |
| policy_faithful | 340 / 0 / 300 | 340 / 0 | 0 / 229 | 53.12% [49.69, 56.72] | 53.12% [49.69, 56.72] |

| Clean gated method | Conditional success, 95% CI | Selected R harm | Both-success completions | Initially successful maintenance |
|---|---|---:|---:|---:|
| DSRE_strict | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| B7 | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| DSRE_risk | 100.00% [100.00, 100.00] | 0 | 251 | 324 |
| B7_risk | 100.00% [100.00, 100.00] | 0 | 251 | 324 |
| B1_one_strict | 100.00% [100.00, 100.00] | 0 | 120 | 165 |
| B1_two_strict | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| CART1_strict | undefined | 0 | 0 | 0 |
| CART2_strict | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| CART2_pruned_strict | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| CART1_beta10 | 100.00% [100.00, 100.00] | 0 | 251 | 324 |
| CART2_beta10 | 100.00% [100.00, 100.00] | 0 | 251 | 324 |
| B5_beta10 | undefined | 0 | 0 | 0 |
| B0_continue | undefined | 0 | 0 | 0 |
| B0_recover | undefined | 0 | 0 | 0 |
| full_signature_strict | 100.00% [100.00, 100.00] | 0 | 182 | 240 |
| greedy_pure_rule | 100.00% [100.00, 100.00] | 0 | 215 | 282 |
| policy_faithful | 100.00% [100.00, 100.00] | 0 | 251 | 324 |

| Clean gated method | Action | Assigned parents | Error parents | Test exact upper (descriptive) |
|---|---|---:|---:|---:|
| DSRE_risk | continue | 128 | 0 | 5.481% |
| DSRE_risk | recover | 0 | 0 | 100.000% |
| CART2_beta10 | continue | 128 | 0 | 5.481% |
| CART2_beta10 | recover | 0 | 0 | 100.000% |
| B7_risk | continue | 128 | 0 | 5.481% |
| B7_risk | recover | 0 | 0 | 100.000% |
| B1_two_strict | continue | 128 | 0 | 5.481% |
| B1_two_strict | recover | 0 | 0 | 100.000% |

Test bounds use the registered parent-any-assignment unit and conservative allocation, but never revise calibration eligibility. Zero assignments have an uninformative upper bound of one. The complete calibration and test populations remain disjoint.

A zero observed error count yields a degenerate empirical bootstrap band, not proof of zero population risk. The exact parent-action bounds retain nonzero uncertainty; checkpoint bootstrap intervals do not replace those simultaneous risk limits.

| Uncalibrated proposal | Recoveries | Matched net successful recoveries versus continue | Effect per selected recovery, 95% CI | Harmful recoveries |
|---|---:|---:|---|---:|
| DSRE_risk | 50 | 40 | 80.00% [65.00, 90.91] | 0 |
| CART2_beta10 | 32 | 32 | 100.00% [100.00, 100.00] | 0 |
| B5_beta10 | 0 | 0 | undefined | 0 |
| B0_recover | 640 | 140 | 21.88% [13.91, 29.53] | 89 |

These matched recovery effects describe uncalibrated proposals, not qualified deployment. A disabled recovery gate yields no selected recovery and an undefined effect per selected recovery. Positive raw net effects cannot establish that the risk-gated policy successfully recovered failures.

The same 256 calibration parents and per-action risk standard are available to all 17 methods. CART2_beta10 is the frozen depth-two risk tree; B5_beta10 and B1_two_strict retain their original rule semantics. Full_signature_strict uses the labeled extra-information 12-fact interface and is not a matched-seven-fact superiority comparator. Fixed controls are descriptive proposals unless their own action gate qualifies. A gated table includes STOP policies with no enabled action; it does not imply all methods qualified.

## Paired uncertainty and condition-specific results

| Paired DSRE risk minus comparator | Completion difference, 95% CI | Required-recovery recall difference, 95% CI |
|---|---|---|
| CART2_beta10 | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] |
| B7_risk | 0.00 pp [0.00, 0.00] | 0.00 pp [0.00, 0.00] |
| B5_beta10 | 53.12 pp [49.69, 56.72] | 0.00 pp [0.00, 0.00] |
| B1_two_strict | 6.88 pp [5.31, 8.44] | 0.00 pp [0.00, 0.00] |
| DSRE_strict | 6.88 pp [5.31, 8.44] | 0.00 pp [0.00, 0.00] |

| Condition and gated method | Adequate / inadequate / STOP | Required selected / eligible |
|---|---:|---:|
| nominal, DSRE_risk | 128 / 0 / 0 | 0 / 0 |
| nominal, CART2_beta10 | 128 / 0 / 0 | 0 / 0 |
| offset001, DSRE_risk | 120 / 0 / 8 | 0 / 5 |
| offset001, CART2_beta10 | 120 / 0 / 8 | 0 / 5 |
| offset002, DSRE_risk | 46 / 0 / 82 | 0 / 62 |
| offset002, CART2_beta10 | 46 / 0 / 82 | 0 / 62 |
| offset003, DSRE_risk | 0 / 0 / 128 | 0 / 100 |
| offset003, CART2_beta10 | 0 / 0 / 128 | 0 / 100 |
| offset_minus002, DSRE_risk | 46 / 0 / 82 | 0 / 62 |
| offset_minus002, CART2_beta10 | 46 / 0 / 82 | 0 / 62 |

Intervals use 4,000 paired parent resamples, PCG64 seed 2026111602. All five conditions and sensor replicates remain with their parent. These descriptive percentile 95% intervals do not assert a multiplicity-adjusted superiority test. B7 exactly agrees with DSRE under both strict and risk routing, including clean gates. Negative differences and equivalences are retained.

## Observation support and skills

The frozen reference contains 422 rows, with physical action-feasible mass 399 and seven-fact common-action signature mass 235. This is a finite-reference partition statement, not a population risk guarantee or a test ceiling.

Test-outcome hindsight ceilings, reported only diagnostically: 6 facts: 372/640 common-action mass versus 569/640 action-feasible mass; 7 facts: 372/640 common-action mass versus 569/640 action-feasible mass; 12 facts: 407/640 common-action mass versus 569/640 action-feasible mass. These do not deploy hindsight actions or thresholds.

Frozen-reference strict certificates and typed witnesses are retained for all 640 test checkpoints in `test_certificate_witnesses.json`; obstruction counts may overlap: `{"REPERTOIRE_INADEQUATE": 294}`. Independent enumeration verifies minimum evidence and necessity/insufficiency witnesses on every distinct observed query. Missing support never becomes a positive certificate.

A REPERTOIRE_INADEQUATE witness identifies a qualified neither-success reference row compatible with the observed signature. It does not assert that the current test checkpoint itself has no adequate skill. The actual neither-success test population is reported separately above; reference insufficiency and physical infeasibility must not be conflated.

## Measurement diagnostic: NOT QUALIFIED

| Offline 5-mm DSRE risk proposal | Mode | Adequate / inadequate / STOP | False / asserted literals | Required selected / eligible |
|---|---|---:|---:|---:|
| bound005 | proposal | 380 / 10 / 250 | 0 / 578 | 40 / 229 |
| bound005 | robust_proposal | 362 / 3 / 275 | 0 / 520 | 22 / 229 |
| uniform0.005_r0 | proposal | 386 / 11 / 243 | 35 / 622 | 46 / 229 |
| uniform0.005_r0 | robust_proposal | 360 / 3 / 277 | 0 / 496 | 20 / 229 |
| uniform0.005_r1 | proposal | 390 / 13 / 237 | 34 / 633 | 50 / 229 |
| uniform0.005_r1 | robust_proposal | 362 / 3 / 275 | 0 / 501 | 22 / 229 |
| uniform0.005_r2 | proposal | 385 / 13 / 242 | 34 / 622 | 45 / 229 |
| uniform0.005_r2 | robust_proposal | 364 / 1 / 275 | 0 / 498 | 24 / 229 |

These are offline proposals reusing the same physical pairs. Uniform replicates are correlated measurement repetitions, not new independent robot parents. Bound005 is the clean-centered declared 5-mm uncertainty box. No clean risk certificate covers altered inputs, and factual-literal correctness alone does not establish action risk. All 1/5-mm methods remain in the full machine-readable tables.

## Mechanism, cost and limitations

Every policy is evaluated on identical saved input packets and the same physically paired fixed interventions. Both branches reconstruct the same complete prefix and canonical controller/RNG state; no policy receives an additional helpful prefix. Any difference is action selection/abstention under this source, not an improved controller or a new recovery skill. Selected-recovery gain versus matched continue, maintenance and unnecessary harm are separately retained in the metric tables.

Source-specific bounds assume independent seed-parent resets, the fixed five-condition distribution, clean telemetry and continued source fidelity. They are not real-world safety or individual-checkpoint guarantees. A wide held-out bound never changes the sealed calibration gate. Necessary-recovery coverage and risk refusal remain separate scientific findings.

Computational cost is in `resource_accounting.json`, per-parent progress and chunk meters. Raw `route_ms` measures the full frozen nine-scenario point/robust routing bundle; it must not be presented as single-method online latency. No GPU model training, paid API or model download is used.

## Audit, preservation and reproduction

The physical auditor independently recomputes action equations, all branch labels and complete source replay. The separate numerical auditor imports no production selector or simulator: it rebuilds all metric records from raw outcomes/sealed decisions, verifies exact risk limits independently, checks minimum certificates/witnesses, and reproduces grouped intervals by direct indexed resampling. Its report explicitly identifies frozen controls without a separate route reimplementation; all 17 numerical outcomes and counts are audited.

Old source/evidence seals, user changes, `.gitignore`, `uv.lock` and manuscripts are preserved. Raw traces/logs remain local. The completion manifest gives exact source hashes, archive paths, tests, failed checks, resource debit, branch/commit and worker-exit verification. No public push, issue, submission or manuscript revision occurs.

```bash
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache
export PYTHONPATH=src:scripts:/home/imad/Desktop/IEEE-RAL/results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
mkdir /tmp/dsre-runtime-portable-review-20261116
tar -xzf docs/dsre_runtime_source_risk_review.tar.gz -C /tmp/dsre-runtime-portable-review-20261116
uv run --no-sync python /tmp/dsre-runtime-portable-review-20261116/source/scripts/dsre_source_risk_verify_packet.py /tmp/dsre-runtime-portable-review-20261116
uv run --no-sync pytest -q tests
```

Use a fresh empty extraction directory. The portable check is read-only. Full trajectory-audit and analysis entrypoints are `dsre_source_risk_audit.py --stage test`, `dsre_source_risk_terminal_audit.py --stage test`, `dsre_source_risk_analysis.py`, and `dsre_source_risk_numerical.py`, each taking the run root before options. They write audit outputs, so reproduce them only on a disposable copy of the full local raw evidence with the original frozen source available; do not overwrite sealed evidence. Exact executed commands and resource meters are retained under R/metered.

Do not rerun started physics parents or unseal the old failed root. The runtime correction is independently qualified; statistical qualification is action-specific and reported above without a favorable-result requirement.
