# RPD: Quantitative hypotheses and methodology lock, version 2

**Date:** 19 November 2026. **Status:** supervisor-proposed scientific design, not a new empirical finding, completed task adapter, or acceptance prediction.

## 1. Decision

Keep one paper: **When Does Physical Diagnosis Compromise Robot Recovery?**

Keep its central question: **Under which post-failure contact conditions does informative diagnosis reduce the recovery capability remaining after the interaction, beyond the effect of elapsed time, and when does incorporating that effect improve subsequent task completion?**

The contribution is a recovery-specific measurement and decision methodology. Established belief-space/contingent planning supplies the inference machinery. The three linked components are: recovery-option formalization; matched physical probe-versus-hold evaluation; recovery-aware diagnostic decisions. Do not blend DSRE/ERR/RPD into a multi-module paper or restart a general optimizer search.

One primary validation family: contact-sensitive assembly. Cluttered target extraction is a prespecified replication extension, not a second prerequisite for writing. Existing cube executions are source-feasibility evidence only.

Start writing the Stage 1 paper now. This document sharpens its method and proposed validation; it does not authorize another unbounded simulator campaign.

## 2. What changes after the two critiques

- Replace an existence claim (some probe can be destructive) by a population-frequency hypothesis under a declared source distribution.
- Replace an unspecified tradeoff claim by a directional completion prediction with a prespecified meaningful margin.
- Use one remaining-time symbol throughout.
- Describe nominal deterministic models separately from stochastic/noisy evaluation.
- Distinguish loss of one skill from erasure of the entire declared repertoire.
- Include information, measured constraint compliance, and equal-duration control together.
- Make one domain fully specified before relying on a second.
- Do not require novel planning mechanics, perfect physical models, or real hardware to state the paper's simulation-scoped contribution.

These changes are a proposed amendment to the scientific plan. Previous source experiments are not retroactively preregistered tests of these hypotheses.

## 3. Uniform formal definitions

A checkpoint state s includes physical state, time, and relevant controller memory. h is its legitimate observation history. B(h) is a set of possible current states in the nominal model. A is a fixed catalogue of executable feedback recovery policies. tau is the remaining time at the decision checkpoint. Do not reuse T for both a deadline and a transition.

G(s,a,tau) is terminal task success of recovery policy a within tau; in the nominal deterministic model G is binary. Define

    K_tau(s) = {a in A : G(s,a,tau)=1}.

An empty set means no policy in A succeeds within tau. It does not prove physical impossibility under arbitrary controllers or deadlines. A nonempty K for each state also does not imply a common executable action across B:

    Common_tau(B) = intersection over s in B of K_tau(s).

Let probe p take time d_p, transition the physical state through T_p, and produce observation y. In the nominal deterministic case,

    B_{p,y} = {T_p(s) : s in B and O_p(s,T_p(s)) = y}.

Allow O to depend on the measured trajectory, not just terminal pose. It is often the trajectory of contact/proprioceptive response that is informative. For stochastic transitions and observations use a joint kernel P_p(ds',dy | s); update the belief with that kernel. A support-only version must include all transitions/observations permitted by declared uncertainty. A deterministic finite-model guarantee is not a population physical guarantee under model mismatch.

A one-probe robust recovery decision is feasible when

    for every reachable y, there exists a_y in A such that
    for every s' in B_{p,y}, G(s',a_y,tau-d_p)=1.

Multi-step diagnosis uses ordinary bounded contingent planning with explicit time/probe costs. A direct recovery ends the diagnostic search; STOP/DEFER is explicit and is not automatically a successful task. Full-state outcome oracles are offline evaluators, not online observations.

## 4. Matched physical estimand

For a matched neutral physical hold H_d of duration d=d_p, define

    L_p(s) = 1[ K_{tau-d}(H_d(s)) is nonempty
                and K_{tau-d}(T_p(s)) is empty ].

The hold continues feedback, contacts, gravity and time. It is not a frozen simulator state. Each recovery branch uses the same remaining budget tau-d, source parameters, policy definitions and outcome rule.

Let C_p and C_H indicate satisfaction of the preregistered sampled physical constraints along probe and hold respectively. These are measured constraints, not universal physical safety. Define

    J_p(s) = L_p(s) C_p(s) C_H(s).

Primary rate:

    q_IG = E_{s ~ D_eligible}[ J_{pi_IG(h(s))}(s) ].

D_eligible is a predecision source distribution fixed before confirmation. pi_IG is the frozen information-seeking diagnostic selector under the common modeled constraints. Do not choose whichever probe is most destructive after seeing outcomes. All physically qualified predecision parents remain in the denominator. Violations remain reported, not filtered away after treatment. Report erasure L, joint compliant erasure J, per-action loss, creation, and constraint violations separately.

The estimand compares the physical consequences of a specific probe policy with holding. It is not a universal claim about all diagnostic policies. Matched simulation identifies counterfactual branch effects only under the declared repeatability/dynamics coupling. Repeated noise/dynamics rollouts from one parent are clustered, not independent parents.

## 5. Quantitative hypotheses: proposed margins, not measured effects

### H1: diagnostically useful, constraint-compliant erasure is materially prevalent

On the registered contact-sensitive assembly distribution, the frozen information-seeking selector yields joint compliant recovery-option erasure on **at least 10%** of eligible independent checkpoints:

    q_IG >= .10.

Separately require evidence that the probe response is actually informative: frozen decoders for the prespecified evaluator-only diagnostic target Z must improve held-out log score using (X,Y_p) rather than X alone. Z is a predeclared latent alignment/contact hypothesis, not a task condition label handed to the deployed policy. The conditional predictive task, label extraction, decoder class, losses, and thresholds must be frozen from development. No test-label fitting or threshold selection. Log score improvement is reported in nats per parent; a lower confidence bound above zero supports informativeness. Also compare against the response observed during an equal-duration hold, using separately frozen decoders with identical information and fitting budgets, to distinguish contact-derived diagnostic benefit from information available merely by waiting. Neither empirical predictive-score contrast is automatically exact mutual information.

The 10% is a proposed materiality threshold: an effect affecting at least one in ten checkpoints would be operationally consequential. It is not a frequency estimate, tuned threshold, or success condition required by RSS. If the effect is positive but below 10%, report that narrower frequency; do not redefine H1 after observing it.

No held-out parents are dropped because the probe turns out unsafe, uninformative, or destructive. Report those outcomes. An uninformative-probe result concerns the intended sensing mechanism and does not establish H1 by mere perturbation.

### H2: accounting for physical recovery consequences improves decision quality

Under the same observations, learned/source models, constraints, probe menu and time budget, the recoverability-aware selector improves held-out task completion by **at least 5 percentage points** relative to constrained information-gain selection:

    Delta_U = E[U(pi_RPD)-U(pi_IG)] >= .05.

Report probe count/time, intervention effort and observed constraint violations alongside completion. A proposed noninferiority tolerance for measured constraint-violation probability is +.02; interpret any violation increase explicitly rather than attributing a gain entirely to better recovery reasoning. These margins are design targets, not promised results.

Primary comparison is RPD versus constrained information gain, NOT versus an identical full-objective solver. A task-consensus comparator is mandatory. If task-consensus or the matched general planner ties RPD, it is a meaningful explanation of the result; do not call the known decision problem a new optimizer.

H2 is evaluated on the fixed confirmation population even if H1 is not supported. Do not condition H2's denominator on post-treatment erasure or select an effect-rich subgroup from the same test. Prespecified baseline-geometry/contact strata may support descriptive heterogeneity analysis.

## 6. One primary family, with a concrete mechanism

**Primary mechanism: contact-sensitive peg alignment and insertion after a failed nominal approach.** This is a proposed validation adapter; the prior blocked insertion prefix is not represented as a completed RPD experiment. Reuse source-available geometry and fixed servo primitives, with a separate source qualification and provenance record; do not upgrade existing historical environments in place.

Define the fixture dimensions, radial clearance c, insertion axis and precontact alignment frame directly from the pinned source. The planned predecision distribution varies lateral alignment and angular error within declared mechanical tolerances, and optional fixed friction strata. State all parameter ranges before confirmation; do not choose them for a favorable DSRE/RPD score. The intended population is this declared contact-failure distribution, not arbitrary factory assembly.

**Two equal-duration diagnostic operations:**

- Axial preload: a bounded motion toward the hole along the insertion axis, holding within the registered displacement and sampled constraint envelope.
- Lateral dither: one bounded zero-net transverse cycle at the same axial depth and equal duration.

**Neutral control:** hold the current commanded equilibrium for exactly the same duration, with the same feedback controller.

**Two recovery policies:**

- Current-alignment insertion: continue a bounded insertion policy using the available pose/contact estimate.
- Withdraw, realign, and insert: retract to the registered clearance, update alignment from allowed observations, and reattempt insertion.

The same sensing inputs and source privileges must be provided to every policy. If simulated pose or force is privileged, say so. Do not invent an unavailable force sensor. The feedback primitive, amplitudes, gains, duration, endpoints and constraints must be explicitly bound in the adapter specification BEFORE fresh confirmation; their numerical values are not supplied by the already completed cube data. Development may calibrate safe engineering ranges, but not select on relative RPD performance.

Nominal illustrative design values to assess at development, not claims of executed settings: probe duration d=.5s; primary remaining task time tau=4s; second-deadline sensitivity 2tau. Normalize displacement limits to c rather than transferring cube-centimetre values blindly. The final numeric binding belongs in the paper once the source interface has been checked. If it cannot be established, state that exact feasibility dependency; do not write that the adapter is runnable.

Observation X comprises measured joint configuration/velocity, declared pose estimate and recent permitted execution history. Probe response Y includes only recorded predecision/during-probe telemetry actually available to the selector. The generator's latent alignment/mode Z and branch outcomes belong to the evaluator. Fit or supply one frozen transition/observation/recovery model shared across selectors. Report model errors on held-out trials.

**Secondary replication:** cluttered target extraction, with two predeclared physical probes and fixed extract/regrasp/reposition policies. It is a replication of the same estimands, not a second new methodology. No core Stage 1 claim depends on an unqualified new clutter dataset.

## 7. Baselines and mechanism controls

Use equal sensors, priors, allowable action catalogues, horizon, learned models and physical budget:

1. Direct recovery from current observations, without probing.
2. Information-gain selection under the same modeled path constraints.
3. Task-consensus selection that stops when hypotheses share an executable recovery. Explain whether it uses the same physical transition model; never silently make it physics-blind.
4. RPD recoverability-aware selection.
5. Full-model contingent/reach-avoid solver optimizing the same RPD objective, as an equivalence/correctness control rather than a method expected to lose.

Measured controls:
- Equal-duration hold: rules out elapsed time as the only explanation for branch differences.
- Common measured path constraints and violation reporting: distinguishes permitted probing effects from obvious constraint violations.
- Held-out probe informativeness: separates diagnosis from arbitrary harmful motion.
- Longer deadline: identifies timing-sensitive loss.
- One predeclared existing extra recovery skill: measures catalogue dependence without inventing a controller after a difficult failure.
- A probe-response-blind versus response-aware recovery selector on the same post-probe branches: separates information benefit from the physical intervention effect. It is an offline diagnostic, not a newly deployed success result.

Task-consensus and full-model planning can legitimately match RPD. The study's primary new evidence concerns when recovery-option measurements discriminate physically useful decisions, not invention of planning.

## 8. Sample design and interpretable outcomes

Proposed primary validation: **64 discovery parents and 512 independent confirmation parents in the assembly family**, each drawn before outcomes from the frozen checkpoint generator. The hypothesis margins are fixed before this new family's measurements. Pilot/source checks are development and never relabeled confirmation.

Two probes plus a hold, each followed by two fixed recoveries, require **3,072 terminal branch evaluations** for 512 confirmation parents. All six outcomes remain one independent parent. Additional selected-policy replays test execution parity, not sample size. The recovery-selector output must be frozen before evaluator outcomes are opened.

The repertoire/deadline sensitivity can use a fixed 64-parent subset selected by ID before outcomes. Record which extra branches it requires. No need to promise a large hardware campaign or three unqualified environments.

For q_IG, report exact binomial intervals when the assumptions justify independent binary parents; also report the full eligibility and missingness counts. For policy completion differences, use a prespecified paired parent-level interval and show discordant counts. Do not infer equality from a degenerate bootstrap. Primary hypothesis decisions and secondary mechanism intervals must have a declared multiplicity plan; no post hoc best-probe selection.

Illustrative power audit for the binomial part of H1 (mathematical calculation, not a robot result): with n=512 and a one-sided .025 test of q<=.10, rejection starts at 66 events. Power is about .921 if the true q is .15. For H2, power depends strongly on the number of discordant paired outcomes; under discordance .20 and true difference .10, an approximate two-sided 95% half-width is .0378. These calculations do not guarantee qualification or discovery of a positive effect. Check final sample precision from discovery-only nuisance estimates before confirmation, without changing the scientific margin.

With zero events, n=512 gives a one-sided 97.5% upper bound approximately .00718. This would be meaningful evidence against a claimed 10% prevalence in the declared population, provided the probes, source and measurements were qualified and informative.

Interpretation table:
- Informative probes, H1 supported, H2 supported: physical recovery loss matters and changes decisions under the declared scope.
- H1 supported, H2 unsupported: the physical effect exists, but ordinary task-aware selection, model error or cost may explain absent policy gains.
- H1 not supported with narrow interval: quantify the restricted prevalence; inspect prespecified deadline/catalogue strata rather than changing the population.
- Probe not informative: the diagnostic mechanism was not established; arbitrary motion damage is insufficient evidence.
- Source failure or broad missingness: inconclusive engineering/measurement result, not a physical null.
- Same-objective planners tie: expected consequence of representing the same decision problem, not evidence of a new optimizer.

## 9. What to say about the current evidence

The archive `compact_evidence.tar.xz`, inspected for this decision, contains the source-isolation handoff. It reports 28 source-valid episodes: 14 per task at one already-inspected parent per task, under GDB-supervised fresh processes. The matched technical table shows Pick release histories removing successful continuation while recovery remains possible; Push retains both options. No full-repertoire erasure was observed in these technical contrasts. These are correlated feasibility observations, not a prospective frequency estimate or a test of the amended assembly hypotheses.

Stage 1 can use a short source-feasibility paragraph and the explicitly analytical three-world example. Neither should be described as evidence establishing H1 or H2. Prior DSRE completion figures are not RPD probe-selection results.

The paper need not recount abandoned projects or debugging chronology. Report every fact necessary to interpret any experiment that is actually described, including its denominator, comparison and scope. Do not present a favorable subset as a complete prospective evaluation or an inspected contradiction as an unrun experiment.

## 10. Positioning and source verification

Primary sources inspected in this review:

- Official RSS 2027 CFP: https://roboticsconference.org/information/cfp/ (direct open intermittently returned RSS 2026 cache; current official indexed content clearly describes the 2027 5+1 format and two-stage process).
- Official author FAQ: https://roboticsconference.org/information/author-faq/
- Official reviewer guidelines: https://roboticsconference.org/information/reviewer-guidelines/
- Ragan et al., s-FEAST, Science Robotics 2024: https://doi.org/10.1126/scirobotics.adn4722 ; author dataset/source https://datadryad.org/dataset/doi%3A10.5061/dryad.xgxd254r1 . Inspected primary author/publication abstracts and data record, not an independently reproduced implementation.
- DA-GRD, arXiv:2609.29065: https://arxiv.org/abs/2609.29065 . Primary method text inspected, including SE(2) hypotheses, tactile filtering and common-grasp support. It explicitly discusses possible contact disturbance; do not say it ignores physical interaction. It remains a preprint in the inspected record.
- Leave No Trace, ICLR 2018: https://research.google/pubs/leave-no-trace-learning-to-reset-for-safe-and-autonomous-reinforcement-learning/ . Recoverability/reset-based intervention constraints predate this proposal.
- There Is No Turning Back, NeurIPS 2021: https://papers.neurips.cc/paper_files/paper/2021/hash/0e98aeeb54acf612b9eb4e48a269814c-Abstract.html . Reversibility-aware exploration/control are established.
- When Identifiability Is Not Enough: Terminal Controllability in Task-Compatible Active Calibration: https://www.biorxiv.org/content/10.64898/2026.06.11.731593v2.full . Primary preprint text inspected. This review does not independently verify its alleged RA-L publication, so do not assign a journal venue without a publisher record.
- IndustReal, RSS 2023: https://roboticsconference.org/2023/program/papers/039/ . Supports relevance of contact-rich assembly; not evidence that our diagnostic adapter is qualified.

Proposed positioning: **a time-controlled post-failure study of diagnosis-induced recovery-option loss and its consequences for contingent recovery decisions**. Do not claim invention of irreversibility, active diagnosis, terminal feasibility, sensing-induced disturbance, or POMDP planning. Compare recovery to return-to-start reversibility and generic safety using shared dimensions, not invented weaknesses of prior papers.

## 11. Five-page manuscript and thesis figure

Working title: **When Does Physical Diagnosis Compromise Robot Recovery?**

- Page 1: concrete assembly tension; scientific question; H1/H2 in clear prose; Figure 1.
- Page 2: K_tau(s), uncertain-state executable common action, the physical belief update and one-probe feasibility condition. A short conventional planner description, not a page of standard derivation.
- Page 3: equal-duration matching, joint event, information measurement, quantified hypotheses and preselection assumptions.
- Page 4: primary assembly operations, actual available observations, model provenance, baseline algorithms and independent data split.
- Page 5: analytical illustration, carefully scoped feasibility evidence, repertoire/deadline controls and concise interpretation of possible outcomes. No internal review logistics or unsupported feasibility claims.
- Page 6: directly relevant verified references only.

Figure 1: same ambiguous failed state -> three equal-time branches (hold, diagnostic probe 1, diagnostic probe 2) -> post-branch recovery-option cards -> observed response and one selected recovery. Mark every hypothetical loss as an analytical illustration unless trace-grounded. An offline-evaluation enclosure separates the matched branches from one online action. Losing one option and losing all options must look visibly different. All labels match the manuscript.

The figure is an explanatory scientific model, not a claimed architecture breakthrough. PowerPoint is suitable for a vector figure; no new visualization is generated by this document.

## 12. Completion rule

The next deliverable is the methodologically complete Stage 1 manuscript, not another originality search or general experimentation loop. Resolve exact task-binding and observation-interface details during a bounded source review, label anything unresolved, and do not fabricate a fully executable protocol. If new preliminary physics is explicitly authorized later, it may strengthen the submission but may not silently redefine these hypotheses.

A short positive result may be featured when it tests the stated mechanism. A well-controlled null can also be scientifically valuable. No outcome guarantees acceptance, and the final charter is determined by reviewers and the Area Chair rather than by this proposal alone.
