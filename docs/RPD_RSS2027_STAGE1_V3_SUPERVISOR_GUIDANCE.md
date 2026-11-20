# RSS 2027 Stage 1: final local authoring and scientific consistency instructions

**Date:** 2026-11-20. This document is an authoring handoff, NOT the anonymous manuscript source or its submission PDF.

## Central scientific question
Physical diagnosis changes what a robot learns and which fixed feedback corrections remain executable before a deadline. The methodology measures recovery-option loss after a physical diagnostic probe against an equal-duration commanded hold from the same checkpoint and compares information-only versus task-aware probe decisions.

## Required paper structure
1. Page 1: Problem illustration in right column, single consequential scientific question, recent closest-work positioning, explicit quantitative H1/H2.
2. Page 2: Formal state/belief definition, K_tau(s), Common_tau(B), post-probe belief update and exact nominal contingent feasibility criterion.
3. Page 3: Full-width method figure, clear ONLINE versus OFFLINE distinction, physical erasure versus elapsed-time contrast, diagnostic information and paired policy effects.
4. Page 4: Source-specified assembly, two 0.5-second probes and neutral hold, two fixed recovery policies, online/evaluator information partition, stable-goal/constraint and source qualification protocol, frozen common-model comparisons.
5. Page 5: Parent-level statistical tests, meaningful null/positive interpretations, analytical example and feasible Stage 2 validation.
6. Page 6: References only.

## One methodology, precise assumptions
- K_tau(s) = {a in A: G(s,a,tau)=1}. Both the finite recovery repertoire A and remaining time tau are fixed and declared. K empty does not establish universal irreversibility.
- A diagnostic probe changes physical state and produces observation y. For each reachable y, a robust one-probe recovery exists in the complete reference model exactly if the intersection of K over compatible POST-probe states is nonempty.
- Offline from the same checkpoint, compare a physical probe against an equal-duration hold, followed by both fixed feedback corrections. Never show a hold->probe sequential arrow. These matched outcomes are evaluator-only, not available online.
- H1: more than 10% compliant full-repertoire erasure relative to holding under frozen probe-only information seeking, with positive discovery-frozen diagnostic log-score signal on average in erasure cases. Primary contrasts: q_IG > .10, E[J D0] > 0, E[J DH] > 0.
- H2: completion gain above .05 versus same-model constrained information seeking, while whole-path violation rate increase stays below .02. Strong same-objective task-consensus/planning baselines are allowed and expected to tie.
- No claims of a new POMDP/contingent-planning solver, empirical hardware safety or demonstrated physical H1/H2 population effects.
- Parent is the independent sampling unit. Qualification of a physical checkpoint must precede learning/test access; source failure/attrition cannot be converted to zero terminal success. Exact CP/binomial and bounded-score inference uses frozen hypotheses and independent held-out parents.

## Figures
**Figure 1, top-right page 1:** a conceptual three-panel peg-in-hole illustration: hold, axial preload, lateral dither. Captions must say the pictured outcomes are possibilities, NOT robot data. Use the same peg, fixture and gripper across panels.

**Figure 2, full width at top page 3:** Online lane history/belief -> choose probe/direct/STOP -> physical response -> one recovery. Offline lane one checkpoint -> PARALLEL hold and probe of equal duration -> both fixed corrections on each branch -> compare recovery sets, constraints and diagnostic signal. Explicitly separate online sensing from offline counterfactual evaluation.

## Prior work
Position against active fault diagnosis (s-FEAST), decision-aware tactile probing (DA-GRD), reversibility-aware control, task-compatible active calibration and standard contingent/reach-avoid planning. The novelty is recovery-specific physical measurement and the empirical hypothesis, not the generic planning mechanics.

## Current source boundary and safe reporting
The earlier assembly development run screened 12 roots, found 7 contact-eligible and 5 ineligible, and saw 0 stable task completions across 49 distinct terminal branches. It did NOT test H1 or H2. Do not turn it into a positive preliminary or state that assembly is qualified. The academic manuscript may focus on the methodology and analytical result without narrating unrelated source debugging, provided it does not imply completed physical validation. New empirical claims require a disjoint registered study with complete denominators.

## Reviewer-proof clarity
Uniform notation and capitalization from first mention; clear conceptual rather than process-oriented story; references for external introduction facts; references only on page 6; no external project URLs, anonymous identities, supplementary data or invented quantitative outcomes. Preserve the same task and algorithm across figure, caption, main text and claims. Ask a blinded reviewer to explain the question, causal contrast, source of evidence and falsifiable outcomes after reading only title/abstract/figures/conclusion.

**Status:** methodology-first manuscript can be completed without further physics. Originality and physical source feasibility remain scientific review questions, not typography problems.