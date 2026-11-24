# V2 audit disposition and remaining scientific risks

The revised paper is a methodology-first author-review manuscript. It is not a
completed assembly study, an experimental feasibility certification, or an RSS
endorsement. Three separate computational assessments are preserved in
`REVIEW_ROBOTICS.md`, `REVIEW_METHODOLOGY.md`, and `REVIEW_STATISTICS.md`.
Each records scope and independent initial objections. Later appendices assess
corrections without deleting the original critique. The robotics reviewer recorded
the title/abstract stage before the figure/conclusion stage; its supplemental
Introduction read accidentally returned further text, which is disclosed. This
is not represented as a controlled human blind-review experiment.

## Completed corrections

| Audit issue | Correction in the main paper | Status |
|---|---|---|
| Official class assumed rather than checked | Fresh official archive; SHA256 and byte comparison; unmodified official class used | Closed by template receipt |
| Underspecified assembly setup | Explicit frames/perturbation pivot, native IK seed, public calibration, controller settings, trajectories, clock, sampling and goal | Proposed defaults complete; physical execution unqualified |
| H1 aggregate signal confused with same-case erasure | H1 states two population properties; full-parent JD secondary diagnostics test average co-occurrence without refitting or deleting parents | Mathematical distinction closed; effect untested |
| a1 changes its parameters after observing probe response | Estimate grasp transform from root X only, then store it unchanged across probe/hold/direct; responses select macros only | Removes identified recovery-initialization confound |
| G(i,p,a) invalid when recovery depends on codeword j | Response-independent calibrated macro parameters make the per-particle action table coherent | Nominal model contract closed; physical model errors remain testable |
| Native 100-tick limit truncates the experiment | Both wrappers200 ticks; setup30 plus primary80 or sensitivity160; no checkpoint clock reset | Source-visible requirement closed; execution must verify |
| Sine endpoint, dwell and observation timestamps ambiguous | k=1..10 endpoint-inclusive zero-order holds; literal final u0; Y after fifth substep; 26 inclusive goal samples | Closed in text/design recipe |
| Bootstrap pilot depends on an unavailable learned model | Nominal qualification-only recovery first; discovery root estimator then frozen labels;16 final-estimator parity episodes before test | Dependency order closed |
| H1 undefined for direct/STOP/no-safe-probe | Probe-only selector with explicit abstention and zero policy contributions; separate H2 deployment wrapper; no parent removal | Closed; contribution zeros are not invented robot outcomes |
| UNKNOWN eligibility silently treated as ineligibility | Distinct root dispositions; no unconditional eligible-population claim on unknown roots; all known-eligible missing labels retained | Identification scope closed |
| Missingness bounds depend on an outcome-selected prefix | Exact worst-case CP binary envelopes and a variance-aware bounded-score envelope over the fixed eligible cohort | Tested offline, no missing-at-random assumption |
| Direct-control budget incomplete | Both direct macros in discovery add128 terminal branches: base4096, screening576, parity16, qualification up to110 source episodes | Corrected accounting,4798 maximum base source episodes |
| Weak/identical task-aware baselines hidden | Shared-model Bayesian coverage adaptation equals RPD; exact response-wise control retained | Equality explicit, no new optimizer claim |
| Tiny cube table looks like population evidence | Replaced by a brief note with one-parent scope, no full erasure, prior crashes and original lost outcomes | Closed without deleting historical evidence |
| Closest-work DOI/title mismatch | Corrected to IEEE-deposited RA-L DOI10.1109/LRA.2026.3719194; wrong bioRxiv attribution documented | Closed, important prior art retained |
| Figure text/metadata/anonymity | Conceptual scene and constructed worlds; editable SVG text/shapes; minimum7.5pt labels at official column width; outlined PDF figure text; empty active PDF Info dictionary | Build/visual checks required and recorded |

## Ranked risks not resolved by manuscript editing

| Rank | Remaining risk / exact missing evidence | Fixed bounded resolution and honest interpretation |
|---|---|---|
|1|No qualified primary assembly source or H1/H2 outcomes|12 fixed qualification candidates, at most98 terminal branches plus12 screens/3worker-hours; fail without task/parameter search if roots/replay/telemetry do not qualify|
|2|No observed material, informative full-repertoire erasure|Fixed512 confirmation candidates, all six matched branches on eligible roots, q and score intervals; two positive population properties do not prove same-case informativeness|
|3|No demonstrated completion benefit over strong IG wrapper|Paired H2 with fixed5pp margin and2pp violation noninferiority; evaluate regardless of H1; report equality or negative outcomes|
|4|Small catalogue and deadline may explain every loss|Same six branches at8s on64 pre-hash-selected IDs; extra-skill sensitivity remains unavailable until one existing qualified skill is bound before data; no global irrecoverability claim|
|5|Source replay can fail outside two inspected parity parents|Fresh prefix every branch, root fingerprint for every confirmation parent, full flags/clock records; any invalid branch is missing, never a manufactured failure|
|6|Runtime/source attrition may prevent useful inference|28worker-hour proposed ceiling; primary4688 source episodes need about15.36sec each on average; screen eligibility first, retain unfinished IDs and use full-cohort bounds|
|7|H2 profile and exact intervals can disagree|Primary scope is asymptotic; report exact sensitivity always. Analytically,76 positive/26 negative discordances atn512 give profile lower about.0603 but exact lower about.0379: approximate support is not robust/exact confirmation|
|8|Rare-erasure score intervals can be very broad|Atn512 the secondary EB additive penalty is about.3202nats/parent before variance. Report unresolved co-occurrence if intervals span zero; do not lower the criterion after seeing data|
|9|A stronger stable goal may differ materially from stock head success|Measure both the registered stable mid-depth event and native head-only flag; never relabel old cube or insertion evidence; do not call the goal released/full assembly|
|10|Finite discovery model may be wrong or poorly supported|No calibrated recovery-probability or complete-support claim. Freeze shared model and report held-out prediction errors, absolute violations and policy outcomes|
|11|Sampled net forces, slip and limits are incomplete safety proxies|Record the exact native channels and all path violations; goal-only K and compliant K^C separately. No hardware-safety or physical impossibility claim|
|12|Scientific novelty/significance depends on physical findings|Prior work already represents information/state interaction and finite-horizon viability. Contribution remains proposed recovery-specific measurement; a working solver or six-page PDF proves no novelty or acceptance|

## Scientific decision for author handoff

Formal definitions, hypothesis logic, source-conditioned inference, baseline
equivalence and numerical bookkeeping are ready for scientific author review.
The paper is self-contained in its five content pages. Format and integrity
checks are executable, with exact results in the build/checklist receipts.

Physical feasibility, prevalence, diagnostic co-occurrence, completion benefit,
repertoire robustness and transfer remain unestablished. The precise proposed
simulation protocol can falsify or narrow those hypotheses without real robot
hardware. No issue is “resolved” by replacing missing measurements with analytical
worlds. No manuscript revision or citation correction changes historical data.
Submission and acceptance judgments remain with the author and conference.
