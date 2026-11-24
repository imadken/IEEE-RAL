# Codex execution: 48-hour ERR methodological novelty challenge

**Date:** 19 November 2026. **Execution order: mandatory.** **No new physics or manuscript rewrite in this session.** This is the final authorized technical-methodology challenge before the RSS Stage 1 six-page paper. The goal is not a positive performance gain; it is to implement and independently falsify a research question that offers an additional methodological object beyond the existing DSRE action certificate.

## Source and preservation

Local repository: `/home/imad/Desktop/IEEE-RAL`.
The newest LOCAL research history is authoritative, including closure commit `9f98797e587489b4a6f9c5139f8aec0d65912bb8` if present; it may be on a different local branch from the V5 manuscript. **Do not reset or cherry-pick stale code over user changes.** Preserve all manuscripts (V5), original physics, prior failures, original paper evidence and seals, and the 645-pass closure tests. Make a new scoped branch from current verified local HEAD. Report current HEAD and dirty file inventory before work. Do not push anonymous paper/source publicly.

Read, in order:
1. `docs/DSRE_STAGE1_FINAL_SCIENCE_CLOSURE.md` from latest local closure;
2. `docs/DSRE_STAGE1_CERTIFICATE_BASELINE_AUDIT.md`;
3. `docs/DSRE_STAGE1_IDENTIFICATION_SOURCE_AUDIT.md`;
4. existing `rss2027/dsre_stage1.tex` or latest V5 source, whichever is newer;
5. supervisor `SCIENCE_DECISION.md` in the attached v6 package;
6. `finite_world_experiment_planner.py` attached reference checker.

**Treat the v6 supervisor memo as the selected SCIENTIFIC research problem, not evidence that its proposed algorithm is validated.** Do not quietly change thresholds, action definitions, or conclude superiority from a different input representation.

## Program A: independent mathematics and evidence semantics, before coding

A1. Independently reconstruct the exact definitions of `Q_D(S)`, existing child/whole-leaf calibration and registered 10% harm, 5% gain obligations. Re-run the pinned source evidence validations and the finite-world reference checker. Check that opposite-verdict pairs use population joint-outcome distributions and that experiment signatures are data-generating distributions, not observed lucky test outcomes.

A2. Define a **finite** set `M_D` of possible joint outcome worlds and source experiments `e`, each with a known `L_e(z|Q)`. An experiment separates two worlds only if their WHOLE observable data laws differ; it does not magically reveal the hidden truth. When finite samples are drawn, separate ideal identifiability from statistical power. Outcome of an identifying experiment may be `REFUTED` not `CERTIFIED`.

A3. State and independently prove the exact weighted-hitting-set equivalence for the finite catalogue, plus the impossibility result for an unseparated opposite-verdict pair. State limits: finite world catalogue, known experiment likelihoods, no guarantee at finite sample size or under source shift. Exhibit counterexample where a single-arm-only menu cannot identify harm but an offline paired source can.

A4. Distinguish observational measurement refinement (changes target context and may require new conditional calibration), one-arm randomization (identifies marginals under causal assumptions), qualified paired simulator trials (identifies joint only under declared coupling), and repertoire enlargement (changes the action class, not a new observation about the old one). Never equate these operations or let one inherit another source guarantee.

## Program B: exact solver and independent oracle

B1. Implement `src/.../experiment_resolvability.py` using existing project architecture. APIs must accept immutable `world_id`, `obligation_verdict`, experiment result law/signature, and nonnegative integer/rational experiment costs. Return `MINIMUM_RESOLVING_MENU` or `NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE`. Return a pair of opposing worlds demonstrating every unresolved case. Missing or malformed experiment source metadata must raise or return `SOURCE_UNSUPPORTED`, not claim equivalence.

B2. Implement independent exhaustive enumeration and a separate integer program or brute-force oracle. Test all small cases with 2-8 worlds and 1-6 experiments, including exact ties, duplicate data laws, zero-cost experiments, opposite verdicts with identical signatures across all experiments, and floating-point tolerance traps. Check optimized output against the independent oracle for at least 500 seeded cases. Include negative tests for claims from discretized continuous models and class-dependent participant selection.

B3. Unit tests must verify the analytical worlds `(.4,.2,0,.4)` and `(0,.6,.4,0)`, marginal equality within exact rational arithmetic, harm values 0 and .4, no one-arm identifying source, paired possible. The attached reference script already demonstrates the idea but is not the production proof.

B4. Do NOT call a shortest explanatory rule a cheapest experiment. Return *both* the existing minimum-justification explanation when authorized and a separate minimum-cost **experiment-type** plan when the obligation's truth is unresolved.

## Program C: physically grounded witness and useful comparator

C1. Use sealed discovery and calibration evidence only. Extract actual predecision PickCube and PushCube source-grounded observation patterns, qualified leaves and literal deletion counterexamples from the closure. Candidate sensor facts can be used only if recorded at the relevant checkpoint. Do not insert future labels or hidden simulator faults as observable facts. The source record must support the claimed observation threshold and physical origin.

C2. Output at least one contextual *observation* case and one *counterfactual* case as distinct typed outputs. If the physical tables cannot instantiate a genuinely unidentifiable paired-only obligation, produce the analytic world pair and explicitly label it analytical. Do not claim a physical paired-only case.

C3. Compare against:
- existing DSRE certificate-only;
- B7 with ALL identical certificate postprocessing;
- B7 with IDENTICAL new experiment-plan postprocessing (fully instrumented control);
- direct tabular bounds plus source-explicit experiment menu;
- a simple source-cost greedy set-cover heuristic and exact minimum-cost menu.

**The fully instrumented B7+same experiment planner may match exactly.** This is a legitimate equivalence, not evidence of unique algorithm novelty. The experimental advance is the obligation-resolving information-design QUESTION; the exact solver is one implementation. Do not claim superior action selection, oracle physical ground truth, or sample efficiency on the 512-budget study, which was a tie.

C4. Record per case: selected intervention, shortest scope-valid observed explanation (if any), opposite-verdict worlds (if unresolved), available experiment menu, minimum cost/capability of resolution, source assumptions, which information is unavailable now, and a verified typed witness. If no world catalogue is soundly derived from physical data, use the physical data only for observation/capability witnesses and keep the causal joint-world examples analytical.

## Program D: Stage 1 and Stage 2 scientific challenge

D1. Answer with source evidence: Is the ERR research object genuinely different in function or output from a source-aware ordinary rule, and how does it compare to UPS (RSS 2026), targeted explanations (RSS 2026), counterfactual-harm policy learning (NeurIPS/ICML), RESCUE, and active treatment-effect learning (ICML 2025)? Cite exact paper sections or explicit primary-source abstracts and URLs. If primary text is inaccessible, say so rather than invent details.

D2. Propose one finite Stage 2 experiment on independent physically qualified contact/manipulation tasks and one source-cost / identification frontier experiment. Fix action macros, assignment propensity, parents and source-checkpoint qualification BEFORE observing outcomes, and predefine equal action-execution cost. The empirical hypothesis should be conditional: an identifiability-aware experiment planner can avoid acquiring evidence that is provably unable to distinguish opposed obligation worlds. On sources where the current marginals already justify the decision, a tie is expected.

D3. Provide a claim-evidence table with tags `PROVED_FOR_FINITE_MODELS`, `IMPLEMENTED`, `OBSERVED_IN_SIM`, `ANALYTICAL_ONLY`, `UNESTABLISHED`, `REFUTED_IN_TESTED_SCOPE`. If a claim fails, mark it honestly. Do not obscure the 512-budget tie or B7 exact equivalence.

D4. Provide a reviewer panel simulating **Value of Hypothesis** and **Feasibility of Conclusion**, addressing the closest accepted RSS 2026 papers, with concrete changes to a five-content-page submission. Include a page budget and a PowerPoint Figure 1 storyboard. This is not permission to claim high-confidence acceptance.

## Outputs and cutoffs

Mandatory files:
- `docs/ERR_METHOD_AND_ASSUMPTIONS.md` full model and proof with limitations;
- `docs/ERR_FINITE_WORLD_EXPERIMENT_RESULTS.md` all exact tests, counterexamples, cost and minimality;
- `docs/ERR_SEALED_ROBOT_WITNESSES.md` only verified physical cases with provenance;
- `docs/ERR_MATCHED_METHOD_AND_PRIOR_ART.md` detailed matched B7 comparison and SOTA boundaries;
- `docs/ERR_RSS_STAGE1_METHOD_GATE.md` true current readiness, what can enter Stage 1, Stage 2 charter plan;
- verified raw/compact source archive, independent reproducibility and local commit.

Execution budget: at most 48 calendar hours of local work, no new physics, at most 3 additional wall-hours of experiments on sealed evidence and synthetic tests. Respect local current source/runtime/environment and an additional data cap of 500MB. Prevent accidental reuse of paired hidden evaluation as learner inputs. Never run unrelated model training, change action macros, import alternate robot tasks, or branch into a new hypothesis if this one performs poorly. Report actual resources, completeness and any failure.

**Definition of done:** finite-world experiment-resolution theorem and minimum-cost algorithm independently verified, actual source-grounded observation/capability witnesses, honest baseline/source positioning, and a five-page-usable hypothesis/methodology package. Do NOT edit existing manuscripts in this session, do not push or submit. At the end report one of:
`METHOD_READY_FOR_STAGE1_WITH_PROPOSED_STAGE2_EVALUATION`,
`THEORY_ONLY_NOT_YET_ROBOT_GROUNDED`,
`METHOD_EQUIVALENT_AND_NOT_DISTINCTLY_MOTIVATED`, or
`EVIDENCE_OR_IMPLEMENTATION_BLOCKED`.

After this one research session, return to paper preparation without another research pivot. The supervisor will integrate only verified statements and will not assert experiments not run.