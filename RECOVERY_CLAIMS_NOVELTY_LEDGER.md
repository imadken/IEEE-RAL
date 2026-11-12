# RecoveryClaim novelty freeze

H1 (unproven): For a fixed finite intervention family and outcome/cost tolerance,
claim-relative qualification separates sufficient decision evidence from contradicted
or missing evidence, potentially rejecting fewer harmless trajectory mismatches.
No novel causality theorem, witness principle, replay restoration or generic gate is claimed.

| Primary source | Established overlap / inspected scope | Distinguishable test / fair adapted baseline |
|---|---|---|
| [RESCUE](https://arxiv.org/html/2610.13516), method III-B | Robot-policy branching, budget-relative outcomes/costs, deterministic trunk replay prerequisite. Accessible HTML does not establish an equivalent statistical discordance acceptance test; absence of inspected evidence is not proof of absence | B2 fixed-horizon trajectory parity on identical continuations; not official implementation. Test F2 mismatch with bounded F3 discordance |
| [EvalSpec DOI](https://doi.org/10.1109/TASE.2026.3745671) | Primary DOI inaccessible; restricted primary searches yielded no accessible full text/code. No inference of novelty from secondary summaries | B3 explicitly limited interface/action/time conformance proxy. Cannot claim reproduction or superiority to full EvalSpec |
| [ROEP](https://www.mdpi.com/1424-8220/26/15/4757), sections 3.3–3.4 | Clean admission, runtime integrity, missing-evidence withholding and recovery-support scope already exist | B4 input/provenance/execution gating, same affordances. Statistical replay-relative decision fidelity is the candidate incremental component, not admission semantics |
| [Benchmark audit](https://arxiv.org/html/2606.04233) | Shortcut, significance, overfitting, source dependence and nondeterminism already audited | No first-audit claim; preserve null outcomes and small-cohort uncertainty |
| [FailBench](https://arxiv.org/html/2609.03611) | Episode-verdict and score-validity audit | Not a new success detector; no retraining |
| [FIPER](https://arxiv.org/html/2510.09459) | Runtime detection/calibration under stated assumptions | No new online detector or guarantee transferred to shifted tasks |

Existing contracts implement 13 metadata/temporal obligations and finite-prefix
perturbations; existing replay adapters implement CPU native and full-prefix restoration.
New code must consume actual continuations, emit first observed violation witnesses,
compute matched effects/discordance precision and account for prefix completion.
Fatal prior-work equivalence is NOT established; novelty remains unresolved, especially
against inaccessible EvalSpec. B3/B4 are component proxies, not whole-system dominance tests.
