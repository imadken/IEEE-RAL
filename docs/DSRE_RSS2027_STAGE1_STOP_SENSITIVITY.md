# Stage 1: post hoc STOP and fixed-fallback sensitivity

Evidence: `results/dsre-operational/20261114T210505Z-stage1`; immutable original physical evidence: `results/dsre-operational/20261114T180630Z`; starting commit `f008a109bdc0d4a1aad43d30629837af292d0db7`. Policies, reference, gates, parents and physical outcomes are unchanged. This reanalysis is **POST HOC SECONDARY**, not an additional untouched confirmation, new method or physical campaign.

## Three interpretations

- **A, original primary:** successful recommended actions; STOP receives zero autonomous-completion credit. The registered primary point estimates and original 4000-draw parent intervals are retained exactly.
- **B, observed defer state:** record task success at each original STOP, preserving the original decisions and defer count. A successful-at-STOP observation is not a measured terminal hold outcome, human success or new completion. No combined hold-performance score is invented.
- **C, fixed fallback:** replace only STOP by continue, and separately replace only STOP by recover. Both use the existing paired measured branch. Original non-STOP actions stay unchanged. Each composition is **UNQUALIFIED**, with descriptive errors recomputed; it inherits no risk gate or safety guarantee. No evaluation label chooses the fallback.

## Concise matched-control table

A = good/bad/STOP, B = already-successful/unsuccessful at the original STOP; C = good/bad after replacement. Calibrated here means the **original** precomposition gate only. Raw ungated constant-skill outcomes appear below.

| Task | Original frozen policy | A | B | C: STOP→continue (unqualified) | C: STOP→recover (unqualified) |
|---|---|---:|---:|---:|---:|
| PickCube-v1 | DSRE_strict | 80/0/78 | 30/48 | 110/48 | 133/25 |
| PickCube-v1 | B7 | 80/0/78 | 30/48 | 110/48 | 133/25 |
| PickCube-v1 | DSRE_risk | 110/0/48 | 0/48 | 110/48 | 141/17 |
| PickCube-v1 | B7_risk | 110/0/48 | 0/48 | 110/48 | 141/17 |
| PickCube-v1 | CART2_beta10 | 110/0/48 | 0/48 | 110/48 | 141/17 |
| PickCube-v1 | B0_continue | 0/0/158 | 108/50 | 110/48 | 104/54 |
| PickCube-v1 | B0_recover | 0/0/158 | 108/50 | 110/48 | 104/54 |
| PushCube-v1 | DSRE_strict | 0/0/160 | 0/160 | 79/81 | 159/1 |
| PushCube-v1 | B7 | 0/0/160 | 0/160 | 79/81 | 159/1 |
| PushCube-v1 | DSRE_risk | 159/1/0 | 0/0 | 159/1 | 159/1 |
| PushCube-v1 | B7_risk | 159/1/0 | 0/0 | 159/1 | 159/1 |
| PushCube-v1 | CART2_beta10 | 159/1/0 | 0/0 | 159/1 | 159/1 |
| PushCube-v1 | B0_continue | 0/0/160 | 0/160 | 79/81 | 159/1 |
| PushCube-v1 | B0_recover | 159/1/0 | 0/0 | 159/1 | 159/1 |

All 17 methods, both original proposal and gated modes, both fixed compositions and condition/category/initial-state slices are retained in `stop_sensitivity.json`. Empty strata have N=0, parents=0 and `EMPTY_NO_TRIALS`; zeros do not invent safety evidence.

## Primary versus secondary paired differences

| Task | Original STOP=0, primary | STOP→continue, post hoc/unqualified | STOP→recover, post hoc/unqualified |
|---|---:|---:|---:|
| PickCube-v1: Risk minus Strict | +18.99 [13.92,24.05] pp | +0.00 [0.00,0.00] pp | +5.06 [1.90,8.86] pp |
| PushCube-v1: Risk minus Strict | +99.38 [98.12,100.00] pp | +50.00 [48.12,51.88] pp | +0.00 [0.00,0.00] pp |

Intervals are seed-parent paired percentile intervals: 4000 draws, PCG64 2026111401 for Pick and 2026111402 for Push; both conditions move together. Original primary values and quantiles are checked against the sealed original intervals. New fallback intervals are exploratory descriptive estimates, not new qualification bounds.

## Interpretation and descriptive errors

Pick’s 30 extra primary credits are exactly the 30 already-successful strict deferrals. Their terminal hold outcome is unmeasured. Continue fallback removes the Pick risk-minus-strict completion gap, but introduces 48 inadequate actions for each composition. Recover fallback raises risk-tier completions to 141/158 with 17 inadequate actions, versus 133/158 and 25 for strict. These are completion/error trade-offs, not a newly qualified improvement. Push recover fallback removes the 99.38-pp primary gap entirely: both give 159/160 and one inadequate action, also matching the already separately calibrated always-recover baseline. Continue fallback leaves a 50.00-pp Push gap. These facts narrow the headline to abstention-dependent selective credit and preserve the action-justification distinction.

The raw fixed skills have Pick continue 110/158 (48 inadequate), recover 104/158 (54 inadequate); Push continue 79/160 (81 inadequate), recover 159/160 (one inadequate). Gate-disabled constants receiving zero primary credit never imply zero physical efficacy.

Parent-any-error counts after composition are recounted from actual outcomes, not inferred from checkpoint rates:

| Task | Composition | Any bad parent / total parents | Continue assigned/error parents | Recover assigned/error parents |
|---|---|---:|---:|---:|
| PickCube-v1 | DSRE_strict/primary | 0/79 | 79/0 | 0/0 |
| PickCube-v1 | DSRE_strict/fallback_continue | 48/79 | 79/48 | 0/0 |
| PickCube-v1 | DSRE_strict/fallback_recover | 25/79 | 79/0 | 78/25 |
| PickCube-v1 | DSRE_risk/primary | 0/79 | 79/0 | 0/0 |
| PickCube-v1 | DSRE_risk/fallback_continue | 48/79 | 79/48 | 0/0 |
| PickCube-v1 | DSRE_risk/fallback_recover | 17/79 | 79/0 | 48/17 |
| PushCube-v1 | DSRE_strict/primary | 0/80 | 0/0 | 0/0 |
| PushCube-v1 | DSRE_strict/fallback_continue | 80/80 | 80/80 | 0/0 |
| PushCube-v1 | DSRE_strict/fallback_recover | 1/80 | 0/0 | 80/1 |
| PushCube-v1 | DSRE_risk/primary | 1/80 | 0/0 | 80/1 |
| PushCube-v1 | DSRE_risk/fallback_continue | 1/80 | 0/0 | 80/1 |
| PushCube-v1 | DSRE_risk/fallback_recover | 1/80 | 0/0 | 80/1 |

No human escalation cost, unexecuted hold effect, physical sensing improvement, calibration update or deployment is inferred. The paper contains the key table and limits directly; this local report is verification evidence rather than an essential supplement.

Reproduction: the source/raw audit, secondary scoring and independent vector audit commands are in [DSRE_RSS2027_STAGE1_FINAL_AUDIT.md](DSRE_RSS2027_STAGE1_FINAL_AUDIT.md).
