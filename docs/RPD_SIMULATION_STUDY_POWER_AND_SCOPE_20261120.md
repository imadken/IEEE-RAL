# RPD simulation-only prospective study design amendment
Date: 2026-11-20. Research-side study design note. Not anonymous submission source. No H1/H2 confirmation outcomes have been collected.

The physical question and tests are unchanged:
- H1: full fixed-repertoire recovery erasure relative to an equal-duration hold exceeds 10% of predecision-eligible simulator checkpoints, and more than half of erasure cases exceed a 20% true-original-mode likelihood improvement relative to both root-only and hold-response predictors. Define the information margin as gamma=ln(1.2). Count all predecision-eligible parents, including direct-recovery or STOP decisions, in unconditional q. J=0 on a no-probe decision; report no-probe rate separately.
- H2: paired terminal completion improvement over the same-model constrained information-gain policy exceeds five percentage points while added whole-path measured constraint violation remains below two percentage points.

Before opening any confirmation outcomes, increase the proposed primary sample from 512 to **640 independent eligible parent checkpoints**. A fixed matched-hold and two-probe, two-recovery design gives **3840 matched terminal continuations** plus direct-recovery controls. Screen up to 1280 source candidates with eligibility fixed using only predecision data; report all exclusions, failures and missing outcomes. Source qualification still requires a separate 12-parent pilot with >=8 source-eligible roots and >=6 post-hold recoverable roots and independent replay parity. No evaluation conclusion is possible if source qualification fails. A previously inspected development adaptation did not qualify; it cannot be recast as an H1/H2 result.

Verified prospective statistical design, exact one-sided Clopper-Pearson binomial-mixture calculations:
| Eligible independent parents | Erasure count threshold for q>.10 at one-sided alpha=.025 | H1 joint power at hypothetical q=.15, eta=.80 | H2 completion-only power at hypothetical 20% discordance and +12 percentage-point gain | One-sided 97.5% upper q at zero erasure |
| --- | --- | --- | --- | --- |
| 512 | 66 | 0.9211560775 | 0.7956416399 | 0.0071789500 |
| **640** | **80** | **0.9685351570** | **0.9021811599** | **0.0057472949** |

These are theoretical planning assumptions, not measured outcomes. H2's full joint power is NOT identified without a specified paired violation outcome distribution. Hypothesis margins and controllers remain fixed. The source may be adapted using a new, separately identified development cohort; freeze source and statistical registration before the untouched confirmation population. Preserve prior development evidence and report whole cohorts, including negative outcomes, when making empirical claims.

Closely related established methods include task-compatible calibration (Kobayashi RA-L 2026), task-aware tactile disambiguation (DA-GRD 2026 arXiv) and constrained active diagnosis (s-FEAST 2024). The scientific distinction is the matched probe-versus-hold post-failure recovery-option measurement and its possible consequence for diagnostic choice, not a new general contingent-planning optimizer. All studies are physics **simulation only**, with no physical hardware, deployment or safety claims.

This note does not include or link the anonymous five-content-page manuscript. Do not place draft PDFs, TeX or figure files in the public repository while RSS double-blind submission is pending.