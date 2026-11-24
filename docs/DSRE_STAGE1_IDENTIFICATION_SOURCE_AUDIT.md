# Intervention evidence and identification audit

Scientific authority: the complete user-supplied closure contract (18 November 2026). Start commit `f551a6e546a55f59dc059747af6dfe8a3899c478`; branch `research/dsre-rss2027-experimental-closure`. All results are read-only audits or explicitly retrospective analyses. Zero new physics/controllers; no manuscript or final-figure edit. Final source artifacts: `research/dsre_experimental_closure/final`.

For q=(q00,q01,q10,q11), p0=q10+q11, p1=q01+q11, harm=q10 and gain=q01-q10. Nonnegativity gives the established sharp range max(0,p0-p1)<=h<=min(p0,1-p1). The code independently checks 1681 exact marginal pairs, 128 valid paired intersections, and binomial confidence containment regressions. Maximum numerical discrepancy is 2.22e-16. These are classical identification facts, not new DSRE theorems.

**ANALYTICAL WORLDS, not robot episodes:** (.4,.2,0,.4) and (0,.6,.4,0) both have p0=.4,p1=.6,g=.2, with h=0 and.4. A narrow confidence rectangle alone is not a structural nonidentification proof. The actual constructive witness fixes both marginals and has two admissible joints. At exact marginals O3 holds for all joints iff gain>=.05 and (p0<=.10 or p1>=.90). At finite marginals H_U=min(U0,1-L1), G_L=L1-U0. L0>.10 and U1<.90 means every allowed marginal pair still admits excessive harm; it does not by itself prove a favorable paired joint exists. Explicit favorable/unfavorable models are required when claiming unresolved verdicts.

## Equal visible-outcome cost, without fictitious new samples

| Task | Panel | Source | Logical action outcomes | Parents needed | Qualification |
|---|---|---|---|---|---|
| PickCube-v1 | shared_parents | L | 128 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | shared_parents | L | 256 | 256 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | shared_parents | L | 512 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | shared_parents | L | 1024 | 1024 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | shared_parents | P | 128 | 64 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | shared_parents | P | 256 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | shared_parents | P | 512 | 256 | O1 harm-only: [0], O2 absolute success: [], O3 useful recovery: [0] |
| PickCube-v1 | shared_parents | P | 1024 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | disjoint_parents | L | 128 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | disjoint_parents | L | 256 | 256 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | disjoint_parents | L | 512 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | disjoint_parents | L | 1024 | 1024 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | disjoint_parents | P | 128 | 64 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | disjoint_parents | P | 256 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PickCube-v1 | disjoint_parents | P | 512 | 256 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PickCube-v1 | disjoint_parents | P | 1024 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | shared_parents | L | 128 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PushCube-v1 | shared_parents | L | 256 | 256 | O1 harm-only: [0], O2 absolute success: [], O3 useful recovery: [0] |
| PushCube-v1 | shared_parents | L | 512 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | shared_parents | L | 1024 | 1024 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | shared_parents | P | 128 | 64 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PushCube-v1 | shared_parents | P | 256 | 128 | O1 harm-only: [0], O2 absolute success: [], O3 useful recovery: [0] |
| PushCube-v1 | shared_parents | P | 512 | 256 | O1 harm-only: [0, 1], O2 absolute success: [0], O3 useful recovery: [0] |
| PushCube-v1 | shared_parents | P | 1024 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | disjoint_parents | L | 128 | 128 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PushCube-v1 | disjoint_parents | L | 256 | 256 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | disjoint_parents | L | 512 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | disjoint_parents | L | 1024 | 1024 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | disjoint_parents | P | 128 | 64 | O1 harm-only: [], O2 absolute success: [], O3 useful recovery: [] |
| PushCube-v1 | disjoint_parents | P | 256 | 128 | O1 harm-only: [0], O2 absolute success: [], O3 useful recovery: [0] |
| PushCube-v1 | disjoint_parents | P | 512 | 256 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |
| PushCube-v1 | disjoint_parents | P | 1024 | 512 | UNSUPPORTED: insufficient distinct parents in this fixed source pool |

The predeclared parent order and virtual arm masks are in registration.json. Both task pools contain 256 fully qualified paired original-test parents (512 previously collected action outcomes). Each L view exposes one hash-selected label per parent; each P view exposes both labels, costs two, and uses the original marginal-plus-harm/rescue constraint engine. These L views are **masked retrospective development views**, not genuinely randomized newly executed logs. The actual prospective 1024-parent C logs are audited separately. No source-curve policy is scored on the same pool and called an independent test.

The shared-parent panel is a dependent paired comparison across methods. The disjoint panel assigns the first 128 hash-ordered parents to L and the rest to P, with no substitution. Both exclude discovery parents. Within a paired block, first-label marginals and joint constraints intentionally share parents; Bonferroni allows this event dependence. Paired outcomes are never counted as two independent parents. The per-view error allocation is fixed; curves are descriptive, without a simultaneous best-budget/source guarantee.

Every fit runs in a separate Python process with only its own partition and its L or P packet whitelisted. Source-scope, duplicate-parent and propensity checks fail closed. Original evaluator traces and other source-view files are inaccessible to the L estimator. The materializer is explicitly evaluator-authorized; it does not fit a rule. New physics=0. Logical exposed-outcome costs are not claims that only that many historical native branches were collected: the complete pool cost is512 per domain, plus its recorded prefix/source overhead.

At matched supported shared-pool costs, grasp has no qualification at 128 or 256 in either view; push qualifies the same useful cell at 256 in both. Paired 512 has no matched 512-log view in this fixed paired pool, and 1024 is unsupported here. This says nothing about global absence of genuine 1024-log evidence: that primary C cohort exists and qualifies the reported main rules. Do not promote an unmatched or masked point into an acquisition win.

The separately registered prospective grasp acquisition comparison remains an important stronger control: all-logs, all-pairs, uniform mixture, witness-guided and decision-uncertainty allocation tie at 512 base + 512 added visible outcomes. It is reconstructed in E0/recount. No physical confidence-qualified region requiring pairing was established. Sampling uncertainty can shrink with more labels; identical exact marginals can remain structurally ambiguous; missing observations and failed checkpoints are different failures. Confounded logs, unknown propensity or failed replay supply no positive causal certificate. Pairing describes a checked deterministic simulator coupling, not an observed hardware joint potential outcome.

The conditional causal estimands assume consistency, no interference, exchangeability/overlap, independent regional sampling and stationarity. Source code verifies outcome-blind hash assignments and disjoint IDs/fresh native histories, not a theorem that deterministic seed/hash sequences are iid random variables. The whole-cell statement is sufficient, not universal necessity. Actual source and guard hashes are in claims_to_sources.json.
