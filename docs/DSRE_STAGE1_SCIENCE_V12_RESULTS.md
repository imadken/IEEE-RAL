# DSRE v 1.2: verified scientific results

Scientific base: `ae63512bade0a10c43514a81743243f157d287a0`. This report concerns implementation and experimental evidence. Neither manuscript is revised. Existing data below are exploratory reanalysis; only the separately sealed prospective 128-parent confirmation cohort is untouched for the new source.

## Measurement semantics and existing-data mechanisms

The interval adapter asserts only facts invariant under its declared bounds. Missing/stale facts remain UNKNOWN. The bounds are sound but conservative: UNKNOWN need not mean an attainable truth flip. Four constructive examples retain actual bounded corruptions and false point-certificate assertions. Finite-table validity, factual measurement invariance and population risk remain separate.

The independent existing-data pass used 1482 paired checkpoints: 844 development-reference rows (422 per task), 318 earlier held-out rows now used exploratorily, and 320 prior Pick test rows (160 parents). It evaluated 529546 decision records and preserves all prior scientific evidence.

| Declared table | Checkpoints | Action feasible | Exact6-fact common-action mass | Exact7-fact mass | Exact12-fact mass | 5mm invariant-literal compatible mass (7 facts) |
|---|---:|---:|---:|---:|---:|---:|
| development_reference / PickCube-v1 | 422 | 399 | 183 | 235 | 248 | 165 |
| development_reference / PushCube-v1 | 422 | 417 | 0 | 0 | 0 | 0 |
| fresh160_reanalysis / PickCube-v1 | 320 | 300 | 128 | 174 | 191 | 124 |

The exact-signature metric follows the supervisor definition. The wildcard-compatible statistic is a separate pessimistic diagnostic for overlapping UNKNOWN interfaces, independently cross-checked with bitsets. It is not the same partition metric. These descriptors are not deployment guarantees or an additive decomposition of test generalization error. Frozen policies use a different reference/risk criterion and can exceed a strict same-table mass. Push 7 facts are an extra-channel diagnostic; its operational router remains at 6.

All complete-pose signatures were singletons. Independent source checks verified 2964 supporting frames, including full object/TCP quaternions. Full-pose common-action mass therefore equals the action ceiling (Pick 399/422, Push 417/422, prior Pick 300/320), illustrating hindsight singleton overfitting. The neither-success states—23 reference Pick, 5 reference Push and 20 prior Pick test—cannot be repaired by extra sensing under these two fixed skills/horizons. Aliasing and repertoire witnesses can overlap.

## Original clean Pick baseline, preserved

The previous 112 newly assigned recovery-parent calibration has 0 errors and 6.239% simultaneous upper bound. Its scope remains the original two-condition clean distribution; it does not transfer to bounded noise, delay or the new five-condition source.

| Frozen method | Adequate | Inadequate | STOP | Selected necessary recoveries /81 |
|---|---:|---:|---:|---:|
| DSRE_strict | 174 | 0 | 146 | 11 |
| B7 | 174 | 0 | 146 | 11 |
| DSRE_risk | 229 | 1 | 90 | 11 |
| B7_risk | 229 | 1 | 90 | 11 |
| B1_one_strict | 119 | 0 | 201 | 0 |
| B1_two_strict | 172 | 0 | 148 | 9 |
| CART1_strict | 0 | 0 | 320 | 0 |
| CART2_strict | 172 | 0 | 148 | 9 |
| CART2_pruned_strict | 172 | 0 | 148 | 9 |
| CART1_beta10 | 218 | 1 | 101 | 0 |
| CART2_beta10 | 227 | 1 | 92 | 9 |
| B5_beta10 | 0 | 0 | 320 | 0 |
| B0_continue | 0 | 0 | 320 | 0 |
| B0_recover | 0 | 0 | 320 | 0 |
| full_signature_strict | 164 | 0 | 156 | 0 |
| greedy_pure_rule | 174 | 0 | 146 | 11 |
| policy_faithful | 227 | 1 | 92 | 9 |

Full-signature strict is explicitly a 12-fact extra-information control. Ordinary B7 and its risk wrapper match DSRE exactly; they are not independent algorithmic wins. Raw fixed recovery succeeds 247/320 times but has 73 inadequate interventions and fails the matched calibration, so the clean gated table above shows its abstentions. STOP credit is zero; no physical terminal-hold outcome is imputed.

## Measurement tradeoffs on the prior 160-parent Pick cohort

Centers held at original telemetry; these are bounded-error scenarios, not Gaussian noise or draws from an actual camera. Every row below remains a proposal diagnostic except unchanged zero-radius policies under their separate original gate.

| Coordinate radius | Method / interface | Adequate | Inadequate | STOP | Necessary recoveries /81 | False asserted literals |
|---|---|---:|---:|---:|---:|---:|
| 0mm | DSRE_strict | 174 | 0 | 146 | 11 | 0 |
| 0mm | DSRE_risk | 229 | 1 | 90 | 11 | 0 |
| 0mm | B7_risk | 229 | 1 | 90 | 11 | 0 |
| 0mm | CART2_beta10 | 227 | 1 | 92 | 9 | 0 |
| 0mm | margin_DSRE_strict | 174 | 0 | 146 | 11 | 0 |
| 1mm | DSRE_strict | 168 | 0 | 152 | 8 | 0 |
| 1mm | DSRE_risk | 226 | 1 | 93 | 8 | 0 |
| 1mm | B7_risk | 226 | 1 | 93 | 8 | 0 |
| 1mm | CART2_beta10 | 226 | 1 | 93 | 8 | 0 |
| 1mm | margin_DSRE_strict | 166 | 0 | 154 | 6 | 0 |
| 5mm | DSRE_strict | 165 | 0 | 155 | 5 | 0 |
| 5mm | DSRE_risk | 223 | 2 | 95 | 5 | 0 |
| 5mm | B7_risk | 223 | 2 | 95 | 5 | 0 |
| 5mm | CART2_beta10 | 165 | 0 | 155 | 5 | 0 |
| 5mm | margin_DSRE_strict | 160 | 0 | 160 | 1 | 0 |

At 5 mm, strict DSRE retains 5 more adequate decisions than the all-input margin rule: +1.5625 percentage points, parent-group 95% CI [0.3125, 3.125]. This isolates the benefit of using a sufficient invariant subset; robust B7 is identical and strong CART retains the same adequate count. No unique optimizer benefit follows.

Measurement robustness does not imply intervention safety: risk-tier inadequacy rises from 1 at zero radius to 2 at 5 mm despite zero false invariant assertions. Necessary recovery selection falls from 11 to 5. These unfavorable findings are retained.

Actual bounded uniform corruptions use three fixed replicates; all corruptions/conditions remain grouped under the same 160 parents.

| 5mm replicate | Interface (DSRE risk) | Adequate | Inadequate | STOP | Necessary recoveries /81 | False / asserted literals |
|---|---|---:|---:|---:|---:|---:|
| 0 | point_proposal | 230 | 2 | 88 | 12 | 29/314 |
| 0 | robust_proposal | 223 | 2 | 95 | 5 | 0/272 |
| 1 | point_proposal | 230 | 5 | 85 | 12 | 25/321 |
| 1 | robust_proposal | 223 | 2 | 95 | 5 | 0/271 |
| 2 | point_proposal | 233 | 2 | 85 | 15 | 31/323 |
| 2 | robust_proposal | 223 | 2 | 95 | 5 | 0/272 |

The actual five-control delay equals 250 ms at 50 ms/control; it is one experiment. All 1482 historical rows support the actual packet. On prior Pick, stale point risk selects 223 adequate/7 inadequate/90 STOP with 11 false literal assertions. Without a motion envelope, the robust interface declines all 320 current-state-dependent decisions. This is factual restraint, not improved physical completion.

## Qualified prospective protocol and pilot

The five offsets are nominal 0, +.01, +.02, +.03, −.02m in the existing scripted grasp-approach target. They do not translate the object or change materials. The whole joint distribution is explicitly OOD. Pilot seeds 13000000..13000004 were fixed before outcomes and disjoint from all prior plans/attempts. All five arms passed on all five parents: 25 cells, 100 continuations (two executions per action), 8060 checked prefix states and 7000 future states; no qualification failure.

Registered primary seeds 14000000..14000191 have 64 development/characterization and 128 confirmation parents, with every qualified condition retained. All primary recommendations and the secondary 2 cm coarsening/actual-delay controls must be sealed before any primary continuation. No fitting or new population-risk gate is performed. All 17 policies use the same declared input/risk standards; the 12-fact control is labeled separately.

All 192 primary parents completed all five arms: 960 paired checkpoints and 1920 continuations, with no failed qualification, replacement seed or incomplete cohort. All 302400 primary and 48960 secondary method/scenario decisions were sealed before the first primary future. The independent raw-physics audit and numerical/effect audits passed. The prospective findings below concern the untouched 128-parent confirmation cohort; 64-parent development results are retained separately in the sealed tables.


## Untouched prospective physical results

Every confirmation arm has 128 checkpoints from the same 128 independent parents. All five conditions remain in the pooled 640-checkpoint denominator. Offset is in the scripted approach target, not an object translation.

| Offset (m) | Continue only | Recover only | Both | Neither | Required failed-start recovery | Initially unsuccessful |
|---|---:|---:|---:|---:|---:|---:|
| +0.00 | 27 | 0 | 101 | 0 | 0 | 3 |
| +0.01 | 24 | 10 | 92 | 2 | 10 | 16 |
| +0.02 | 9 | 60 | 46 | 13 | 60 | 74 |
| +0.03 | 0 | 108 | 0 | 20 | 108 | 128 |
| -0.02 | 9 | 61 | 45 | 13 | 60 | 74 |
| ALL | 69 | 239 | 284 | 48 | 238 | 295 |

Thus 239 states are recover-only, of which 238 were initially unsuccessful; one is a preventive opportunity. These are distinct alarm/action populations. At +3 cm all 128 continuations fail, while recovery succeeds 108 times and both skills fail 20 times. The nominal arm instead has no recover-only state and 27 harmful fixed recoveries. The grid produces meaningful action-regime differences; it was not balanced or filtered using these outcomes.

Across all 640 paired states, fixed continuation succeeds 353/640 and fixed recovery 523/640. The matched recovery-minus-continuation effect is **+26.5625 percentage points, parent-group 95% CI [18.90625, 33.59375]**. These are effects of the existing fixed actions, not a new controller or DSRE advantage.

## Frozen proposals under the new source

All new-source policies are **UNQUALIFIED PROPOSALS** under the common standard. Strict finite-reference purity, the frozen 10%-reference-error tier and population risk are distinct. Clean calibration is not transferred to this joint five-arm distribution. No new model or risk gate is fitted.

| Frozen method, zero error radius | Adequate | Inadequate | STOP | Selected required recoveries /238 | Harmful recoveries on continue-only states | Mean asserted length when selected |
|---|---:|---:|---:|---:|---:|---:|
| DSRE_strict | 351 | 2 | 287 | 48 | 0 | 1.561 |
| B7 | 351 | 2 | 287 | 48 | 0 | 1.561 |
| DSRE_risk | 401 | 2 | 237 | 48 | 0 | 1.491 |
| B7_risk | 401 | 2 | 237 | 48 | 0 | 1.491 |
| B1_one_strict | 169 | 0 | 471 | 0 | 0 | 1.000 |
| B1_two_strict | 338 | 1 | 301 | 35 | 0 | 1.501 |
| CART1_strict | 0 | 0 | 640 | 0 | 0 | unavailable |
| CART2_strict | 337 | 1 | 302 | 35 | 0 | 2.000 |
| CART2_pruned_strict | 337 | 1 | 302 | 35 | 0 | 2.000 |
| CART1_beta10 | 353 | 1 | 286 | 0 | 0 | 1.000 |
| CART2_beta10 | 388 | 1 | 251 | 35 | 0 | 2.000 |
| B5_beta10 | 353 | 50 | 237 | 0 | 0 | 1.035 |
| B0_continue | 353 | 287 | 0 | 0 | 0 | 0.000 |
| B0_recover | 523 | 117 | 0 | 238 | 69 | 0.000 |
| full_signature_strict | 296 | 1 | 343 | 47 | 0 | 12.000 |
| greedy_pure_rule | 351 | 2 | 287 | 48 | 0 | 1.561 |
| policy_faithful | 388 | 1 | 251 | 35 | 0 | 1.090 |

DSRE risk proposes 353 continue, 50 recover and 237 STOP. Of its 50 recoveries, 48 are genuinely necessary, one preserves both-success and one fails where both actions fail. No selected recovery harms a continue-only state. Its other inadequate decision is a continue on the initially successful preventive recover-only state. The 190 unselected failed-start recovery opportunities are deferred.

Necessary-recovery recall is **48/238=20.1681%, 95% CI [13.4198, 27.4784]**. CART2 risk selects 35/238=14.7059%, CI [8.2642, 22.0931]. DSRE risk supplies 13 more adequate decisions than CART2 risk: **+2.03125 pp, paired 95% CI [0.9375, 3.28125]**, with **one additional inadequate decision**. This is a descriptive coverage/error tradeoff under an unqualified source, not dominance at a certified risk level. Strong ordinary B7 risk is identical to DSRE risk.

Risk versus strict DSRE adds 50 adequate decisions, all maintenance of existing success; it adds zero necessary recoveries and no additional inadequacy. The same ordinary wrapper reproduces it exactly. Fixed recovery attains more raw successes than DSRE risk (523 versus 401), but incurs 117 inadequate interventions, including 69 harms where continuation succeeds. No scalar score hides these tradeoffs.

## Physical feasibility and observation insufficiency on confirmation

| Interface, same640-row table | Action-feasible mass | Common-action signature mass | Feasible mass lost to observational grouping | Neither-success states |
|---|---:|---:|---:|---:|
| 6 predicates | 592 | 206 | 386 | 48 |
| 7 predicates | 592 | 256 | 336 | 48 |
| 12 predicates | 592 | 365 | 227 | 48 |
| Full recorded pose diagnostic | 592 | 592 | 0 | 48 |

All 640 complete-pose signatures are singletons. This is an unattainable-information hindsight diagnostic, not a learned or deployable model. With seven predicates, 48/640 failures are repertoire-limited and 336/640 action-feasible rows lie in classes without a common successful action. This within-table accounting does not decompose cross-population generalization error or bound the independently frozen policy.

At +2 cm and −2 cm, action feasibility is equal 115/128, while the same-condition seven-predicate common-action masses are 65/128 and 14/128. This separates representational/source asymmetry from fixed-skill feasibility in this table. Per-arm slicing is diagnostic; the policies never receive the hidden fault identity. The pooled 12-fact mass 365/640 remains far below the physical 592/640 ceiling.

Concrete, deterministically selected ambiguity and repertoire witnesses are in `physical_effects_and_secondary.json`. In particular:

- ambiguity_pair: `PickCube-v1/14000066/nominal`, `PickCube-v1/14000083/offset_minus002`; signature `[True, True, True, True, True, False, False]`; paired outcomes `[{'continue_value': True, 'recover_value': False}, {'continue_value': False, 'recover_value': True}]`. Overlapping obstruction types: `False`.
- neither_witness: `PickCube-v1/14000066/offset003`; signature `[False, False, True, True, True, True, False]`; paired outcomes `[{'continue_value': False, 'recover_value': False}]`. Overlapping obstruction types: `False`.

## Observation-uncertainty and mechanism-separating controls

The following radii bound each pose coordinate in every supporting frame. The centers are held at source telemetry; actual corruption replicates follow separately. Finger encoders are assumed exact.

| Radius | Method / interface | Adequate | Inadequate | STOP | Required recoveries /238 | False assertions |
|---|---|---:|---:|---:|---:|---:|
| 0mm | DSRE_strict | 351 | 2 | 287 | 48 | 0 |
| 0mm | DSRE_risk | 401 | 2 | 237 | 48 | 0 |
| 0mm | B7_risk | 401 | 2 | 237 | 48 | 0 |
| 0mm | CART2_beta10 | 388 | 1 | 251 | 35 | 0 |
| 0mm | margin_DSRE_strict | 351 | 2 | 287 | 48 | 0 |
| 1mm | DSRE_strict | 344 | 1 | 295 | 45 | 0 |
| 1mm | DSRE_risk | 398 | 1 | 241 | 45 | 0 |
| 1mm | B7_risk | 398 | 1 | 241 | 45 | 0 |
| 1mm | CART2_beta10 | 386 | 1 | 253 | 33 | 0 |
| 1mm | margin_DSRE_strict | 326 | 1 | 313 | 30 | 0 |
| 5mm | DSRE_strict | 280 | 1 | 359 | 15 | 0 |
| 5mm | DSRE_risk | 368 | 5 | 267 | 15 | 0 |
| 5mm | B7_risk | 368 | 5 | 267 | 15 | 0 |
| 5mm | CART2_beta10 | 256 | 0 | 384 | 14 | 0 |
| 5mm | margin_DSRE_strict | 148 | 0 | 492 | 1 | 0 |

At 5 mm, strict DSRE retains 132 more adequate decisions than the all-input margin rule: **+20.625 pp, paired 95% CI [18.28125, 23.125]**, while adding one inadequate decision. It selects 15 necessary recoveries rather than one. This discriminates subset sufficiency from requiring every input stable; B7 exactly reproduces the result. The robust tree comparison uses all reachable Boolean completions, with 11664 ternary masks exhaustively checked against common eligible actions.

Risk-tier recall falls from 48/238 to **15/238=6.3025%, 95% CI [2.1004, 11.4179]** at 5 mm. Adequate credit decreases by 33/640, **−5.15625 pp, CI [−7.34375, −3.28125]**; inadequate actions increase from 2 to 5 even though all asserted invariant facts remain valid. The five errors are continued recover-only states: four initially unsuccessful and one preventive. All 15 selected recoveries are necessary and succeed. Measurement robustness is not a physical-risk calibration.

Robust CART2 risk gives 256 adequate/0 inadequate/384 STOP at 5 mm versus DSRE risk 368/5/267. The+17.5 pp adequate-credit difference, CI [14.21875, 20.9375], comes with five additional inadequate decisions. Most of the extra good decisions preserve success; required recovery differs by only one. This is not an algorithmic win over ordinary risk rules or a certified superiority claim.

Actual bounded uniform corruptions (three fixed replicates, 128 parents each):

| Radius / replicate | Interface, DSRE risk | Adequate | Inadequate | STOP | Required recoveries /238 | False / asserted literals |
|---|---|---:|---:|---:|---:|---:|
| 1mm / 0 | point_proposal | 400 | 2 | 238 | 47 | 5/604 |
| 1mm / 0 | robust_proposal | 397 | 1 | 242 | 44 | 0/583 |
| 1mm / 1 | point_proposal | 400 | 2 | 238 | 47 | 6/602 |
| 1mm / 1 | robust_proposal | 397 | 2 | 241 | 44 | 0/585 |
| 1mm / 2 | point_proposal | 402 | 2 | 236 | 49 | 10/608 |
| 1mm / 2 | robust_proposal | 397 | 2 | 241 | 44 | 0/585 |
| 5mm / 0 | point_proposal | 408 | 8 | 224 | 55 | 42/658 |
| 5mm / 0 | robust_proposal | 367 | 4 | 269 | 14 | 0/487 |
| 5mm / 1 | point_proposal | 408 | 3 | 229 | 55 | 37/647 |
| 5mm / 1 | robust_proposal | 375 | 4 | 261 | 22 | 0/528 |
| 5mm / 2 | point_proposal | 408 | 3 | 229 | 55 | 44/648 |
| 5mm / 2 | robust_proposal | 369 | 4 | 267 | 16 | 0/492 |

At 5 mm the point risk policy asserts 123 false literals among 1953 asserted literals across the three replicates; the robust interface asserts 0 among 1507. These are descriptive replicate totals, not 384 independent parents. Robust policies lose recovery coverage and retain 4 inadequate decisions per replicate; factual stability does not guarantee intervention adequacy. All conditions and corruptions are grouped by source parent in reported CIs. Noise modifies decision evidence only; feedback inside the fixed skills remains unchanged, so this is not end-to-end noisy-controller validation.

Secondary controls were also sealed before any primary outcome:

| Control | Method / interface | Adequate | Inadequate | STOP | Required recoveries /238 | False assertions |
|---|---|---:|---:|---:|---:|---:|
| coarse02_point | DSRE_strict / point_proposal | 372 | 5 | 263 | 47 | 47 |
| coarse02_point | DSRE_risk / point_proposal | 398 | 5 | 237 | 47 | 47 |
| coarse02_point | CART2_beta10 / point_proposal | 384 | 5 | 251 | 34 | 69 |
| delay5_equal_250ms | DSRE_strict / point_proposal | 338 | 16 | 286 | 48 | 15 |
| delay5_equal_250ms | DSRE_risk / point_proposal | 387 | 16 | 237 | 48 | 15 |
| delay5_equal_250ms | CART2_beta10 / point_proposal | 360 | 29 | 251 | 35 | 30 |
| delay5_equal_250ms | DSRE_risk / robust_proposal | 0 | 0 | 640 | 0 | 0 |
| delay5_equal_250ms | CART2_beta10 / robust_proposal | 0 | 0 | 640 | 0 | 0 |

The 2 cm quantization can increase strict proposal coverage while creating false assertions and inadequate actions; it is not declared measurement-certified. The actual five-step/250 ms delayed point evidence increases DSRE risk inadequacy to 16 and CART2 risk to 29. Without a motion envelope, robust Pick policies defer all 640 states. This is abstention, not physical completion or controller improvement. Fixed actions remain 353/287 and 523/117 adequate/inadequate respectively under these observation-only controls.

## Calibration feasibility, verification and interpretation

No new calibration gate is learned. Under the reserved original `.05/68` standard, even 64 error-free characterization parents have a 10.6615% upper bound, above the 10% target; at least 69 zero-error assigned parents are needed. This is a design-only support calculation. The 128 confirmation labels are never used to choose gates, thresholds, features or conditions.

The scientific outcome is **BOUNDED_STAGE1_SCIENCE**: the adapter is sound for its declared bounds, the physical grid distinguishes action regimes, and action/observation/repertoire limits are verified. Unique algorithmic superiority, general robotics breadth and noisy/OOD population certification remain unestablished. Ordinary-rule identities and all unfavorable comparisons are retained. The companion GATE document contains the adversarial reviewer assessment.

Independent verification is by separate internal implementations, not external peer review. It checks 960 main cells, 160640 replayed prefix states, 134400 future states and 1920 primary continuations; all source/contact/controller/condition guards pass. Numerical checks independently recount 3780 main tables, 8897 primary/condition intervals, 224640 proposal routes, 184 minimum-certificate cases, 52 paired physical-effect intervals and 48 selected-recovery compositions/effects. The secondary audit recounts 612 tables and 1400 intervals. Existing-data audits verify 1801 tables and 12607 intervals.

Maintained tests: 539 passed, 4 skipped. Ruff passes; 305 files meet formatting. Unscoped test/lint discovery initially entered archived third-party research environments and failed; those attempts are preserved locally. Validation uses the complete maintained `tests/`, `src/` and `scripts/` trees and does not edit archived evidence. All three scientific figures were visually inspected.

Measured new simulation: 2.870346451 h of 10 h. Measured bounded physics-child CPU: 2.884900379 core-hours (audit/plot/package/model/tool CPU is not measured or asserted zero).470780 control steps correspond to 23539.0 simulated seconds; simulated time is not wall time. There are 0 new model fits. Artifact/session totals and final publication are in `release_receipt.json`; the source budget is 4 GiB newly compressed artifacts and 16 h session wall with a 1 h analysis reserve.

Both manuscripts, `.gitignore`, `uv.lock`, all 55 initial user-status entries and 12955 members of the previous sealed scientific root are preserved. No conference submission, author contact, new controller, training run or additional seed campaign occurs.

## Evidence and reproduction

Evidence root: `/home/imad/Desktop/IEEE-RAL/results/dsre-operational/20261115T195007Z-science-v12`. Key inputs are `study_plan.json`, `science_freeze.json`, `frozen_routers.json`, `pilot_qualification_seal.json`, `prospective_recommendation_seal.json` and `secondary_recommendation_seal.json`; outputs are `prospective_results.json`, `physical_effects_and_secondary.json`, `mechanism_compatibility.json`, the independent audit JSON files and `figure_data.json`. Full raw per-seed/condition traces stay under `pilot/` and `prospective/`, with SHA256 coverage in the completion manifest.

The compact review archive is `docs/dsre_science_v12_review.tar.gz` (local duplicate: evidence-root `supervisor_review.tar.gz`). It contains source snapshots, compact predecision telemetry and actual paired labels, the decision ledgers, verified reports, figures and independent audit outputs; it excludes execution logs, raw frames, caches and both manuscripts. The standalone verifier reproduces routing, counts, minimum rules and parent-group intervals without new physics:

```bash
DSRE_REVIEW=$(mktemp -d /tmp/dsre-v12-review.XXXXXX)
tar -xzf docs/dsre_science_v12_review.tar.gz -C "$DSRE_REVIEW"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python "$DSRE_REVIEW/verify_compact.py" "$DSRE_REVIEW"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts \
  uv run --no-sync pytest -q tests
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff check src scripts tests
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff format --check src scripts tests
```

To independently re-audit full physical evidence on this workstation, create a scratch audit directory; do not overwrite sealed outputs:

```bash
DSRE_RAW=/home/imad/Desktop/IEEE-RAL/results/dsre-operational/20261115T195007Z-science-v12
DSRE_AUDIT=$(mktemp -d /tmp/dsre-v12-raw-audit.XXXXXX)
cp "$DSRE_RAW"/{study_plan.json,frozen_routers.json,prospective_recommendation_seal.json,prospective_rows.jsonl.gz,prospective_decisions.jsonl.gz,prospective_results.json} "$DSRE_AUDIT/"
ln -s "$DSRE_RAW/prospective" "$DSRE_AUDIT/prospective"
ln -s "$DSRE_RAW/progress" "$DSRE_AUDIT/progress"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python scripts/dsre_science_audit.py physics "$DSRE_AUDIT"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python scripts/dsre_science_numerical.py "$DSRE_AUDIT" --prospective
```

The executed physics sequence is the fixed runner `dsre_science_physics.py control ROOT --stage pilot`, independent `dsre_science_audit.py pilot ROOT`, `control ... --stage screen`, secondary sealing, then `control ... --stage outcome`. Its immutable attempt/progress ledgers forbid duplicate or replacement parents. Do not point fresh simulation at the sealed root. Reproduction above rechecks evidence rather than collecting new outcomes.
