RSS 2027 scientific disposition after the RPD originality audit
Date: November 19, 2026. Scientific status: valid standard planner; candidate empirical robotics hypothesis not yet physically tested.
Decision
Do not submit RPD as a novel strong planner or POMDP method. The independently checked same-input strong and reach-avoid POMDP controls match it on 6,688 cases, and a one-step task-consensus controller solves its illustrative three-world problem. A toy information-versus-recovery example is a logical example, not evidence of physical prevalence. No post-probe robotic success predicate has yet been measured or calibrated.

The only plausible RSS Stage 1 direction that uses RPD is a hypothesis-driven empirical and measurement methodology: establish whether contact-rich physical probes alter, and sometimes eliminate, future task-recovery opportunities even when they remain within ordinary physical allowed-state constraints. Standard belief-space planning may be used as a control/measurement instrument, without an algorithmic novelty claim. This is a candidate, not an accepted or confirmed novelty claim. V5 DSRE remains an independent preserved submission alternative with qualified robot results.
One scientific question
When do actions taken to diagnose a manipulation failure irreversibly reduce the set of still-feasible recovery options, and how does that change the value of information?

Hypothesis H1: For a fixed subset of physically qualified contact probes and robot failure checkpoints, measurable post-probe recovery-option loss occurs relative to an equal-duration neutral hold even when sampled geometric safety constraints remain satisfied.

Hypothesis H2: Probe responses can improve prediction of an evaluator-only hidden state property beyond the available pre-probe proprioceptive history while also reducing recovery-option coverage. In these regimes, raw information-gain selection can be a worse intervention choice than a task-recovery-aware selection rule. A direct task-consensus policy and a same-input full-model strong/POMDP planner must be included. Identical decisions are an expected honest result.

Hypothesis H3: When an empirical model fails to predict post-probe recovery options, the failure can be attributed to specified transition, observation, action-repertoire or checkpoint-eligibility limits, rather than being declared a physical impossibility result.

These are empirical hypotheses whose truth in the nominated robot tasks is UNKNOWN. RSS Stage 1 may legitimately submit them with the technical protocol fully specified, but cannot claim physical verification on the basis of a constructed finite example.
Scientific measurement to replace solver-centered novelty
At eligible matched checkpoint s, let A={continue,recover} be fixed 70-control macros. For probe p of d=10 native control ticks, let H_d be an equal-duration no-probe neutral hold. Use a common 90-control post-checkpoint deadline and fixed native success predicate evaluated on actual simulator rollouts; all policy-specific hold padding is explicit. No same-run reset, teleport or state injection occurs. Independent counterfactual branches are produced only by starting separate qualified replay episodes from the identical original checkpoint and are never available to the deployed policy.

Define K_h(s) = {a in A: U_90(H_d(s),a)=1} and K_p(s) = {a in A: U_90(T_p(s),a)=1}, where the horizon suffix and terminal padding are matched by source-level controls. Compare the two sets with actual simulator outcomes, not a learned universal truth table.

Primary probe-induced recovery-option erasure is
E_p(s) = 1[K_h(s) nonempty AND K_p(s) empty].
A secondary outcome is option creation
C_p(s) = 1[K_h(s) empty AND K_p(s) nonempty].
Report lost/gained action membership separately, since a probe may remove one successful macro while retaining another. The matched hold is indispensable: comparing probes to immediate continuation alone confounds their physical effects with a ten-tick delay and deadline. An optional equal-effort no-contact action can be registered as a further control before any data is opened, but must not be chosen based on effects.

Sampled geometric allowed-set adherence is recorded along whole paths, not substituted for recovery-option preservation. A safe-state outcome and a task-recovery outcome are distinct. No force/damage or continuous-time safety guarantee exists in the current source.

For information, freeze a pre-probe measurable history X, an evaluator-only diagnostic label Z (e.g. relative object/TCP pose cell), and the allowed observation Y_p. Use held-out prediction gain of Z from (X,Y_p) relative to X alone, with the decoder fit on discovery parents only. It is a predictive information proxy, not automatically Shannon mutual information or causal information gain.
Necessary methodological alternatives and prior art
Prior art already covers safe active fault estimation (s-FEAST, Science Robotics 2024), belief-space POMDP and strong planning, tactile decision-aware probing (DA-GRD, 2026), and recoverability-aware control. Do not claim that information/action coupling or physical irreversibility is new in general. Contrast the empirical estimand and matched physical test protocol: loss of previously adequate terminal recovery macros caused by a diagnostic probe, over and above an equal-duration hold, conditional on sampled geometric allowance.

A same-input POMDP planner is a positive control, not a baseline that the RPD finite solver should beat. Task-consensus is another strong comparator. Standard entropy and a transition-blind ablation test consequences of ignoring viability, but the latter is deliberately misspecified and must be labeled accordingly. The paper's scientific contribution must be the physical phenomenon and measurement methodology, not the standard planner implementation.
Exact limited physical qualification pilot, before choosing a paper
Use the already reserved new 10 technical parents for EACH of PickCube-v1 and PushCube-v1. Exact source hashes and original checkpoints at native prefix65 and prefix53. Freeze probe macros and allowed native response channels from the sealed protocol. No seed substitutions, simulator-mode shopping, new learned controller, or alteration to old DSRE evidence.

For each parent, run all source histories of lengths zero to two and the three existing endpoint options as independently replayed native trajectories. As a registered pre-outcome protocol addition, include equal-duration neutral holds of 10 and 20 control ticks with the same fixed endpoint options. Keep separate histories at 10 and 20 controls to isolate waiting from physical state alteration. Repeated trials from one parent are correlated; independent N per family is 10, not the count of rollout branches.

Audit native actuator and TCP effects, object motion and real contacts (evaluator only), source checkpoint reproducibility, observed joint/TCP channels, task terminal conditions, continuous path recording at 20Hz, and actual recovery eligibility. A no-contact or non-acting probe means the tested interface does not expose the intended contact mechanism; it is not evidence that recoverability-preserving diagnosis is unnecessary. Include all failures and null cases.

The prior protocol budgets 420 source episodes per family and two worker-hours per family. The two added neutral holds add up to 120 native episode branches per family if each endpoint is replayed twice for every parent. Before running, measure the actual time per native episode, and cap physics at THREE worker-hours per family inclusive of repeat/hold probes and no more than 3 GiB new compressed artifacts per family. If the registered histories cannot complete within this cap, stop on an atomic parent boundary, disclose unfinished counts, and do not convert partial tests into confirmation claims.

This is a technical feasibility and mechanism pilot, not a population hypothesis test or a new novelty proof. No calibration from old DSRE transfers to the probed checkpoint distribution. No Stage 1 headline performance number is required from this pilot.
Feasible Stage 2 plan, distinct from the superseded 58-hour gate
Stage 2 primary analysis is a paired, intervention-outcome measurement study, not six-policy-times-four-region independent PAC certifications. Freeze two probes, a ten-tick neutral hold, same fixed terminal macros, a fixed physical checkpoint and common 90-control deadline. Use separate 64-parent discovery and a new independent test cohort of 256 eligible parent seeds per task, with original-seed and qualified-checkpoint denominators both visible. Evaluate matched potential intervention outcomes for the same source checkpoint in separate replay episodes; cluster all histories within parent. Sample size and minimum scientifically relevant erasure effect must be finalized from discovery precision/power calculations BEFORE any test outcomes. Prespecify pooled and per-task estimates, grouped intervals, multiple-testing rule, missing data bounds and matched time/effort controls. Distinguish sources, action labels, and task-family mechanism; do not assume the two Panda tabletop tasks cover all robots.

An optional secondary contingent-planning demonstration can compare full-model strong planning, one-step task consensus, and information-gain; it is not a new optimizer claim. A different robotic family or hardware may be added only if an RSS Extension Charter requires it and the source qualifies. No hardware is promised without access. Avoid the original proposed 512 calibration samples split over 6 policies and 4 terminal regions: its own audit shows that 128 samples in a region pass a 90% success CP gate with only around 11% probability when true success is 95%, so it cannot be the primary feasibility argument.

Possible scientific conclusions: probe-related option erasure occurs at meaningful frequency; it is rare at the tested contacts; its apparent effect is explained by time delay rather than contact; information changes without physical option erosion; or model observability is inadequate. Each conclusion needs actual diagnostic/contact qualification and independent source-grounded evidence. A source failure or probe that never acts does not support a claim about absence of the underlying phenomenon.
Manuscript and timing disposition
Current RPD status: not manuscript-ready. V5 DSRE status: complete methodology and grounded positive preliminaries but material novelty risk. DO NOT merge the two methods into a giant architecture. One short physical source/phenomenon pilot determines whether the stronger empirical-science route is feasible; afterward choose ONE paper. Keep the old manuscripts/source/evidence untouched until that decision. Deadline December 4 2026 23:59 AoE; no more generic optimization-method searches. The official RSS FAQ explicitly allows empirical science hypotheses and preliminary/missing experiments, but requires precise methodological mechanics and the ability to obtain meaningful conclusions.

Immediate next action: complete the specified two-family ten-parent native probe/neutral-hold technical pilot with an independent evaluator audit and all adverse cases retained, then use the result to decide whether to write the empirical RPD Stage 1 paper or finalize the already-evidenced DSRE V5. No high-confidence acceptance prediction is supported for either choice now.

Official policy sources:
https://roboticsconference.org/information/cfp/
https://roboticsconference.org/information/reviewer-guidelines/
https://roboticsconference.org/information/author-faq/

Relevant primary source:
https://doi.org/10.1126/scirobotics.adn4722
https://arxiv.org/abs/2609.29065