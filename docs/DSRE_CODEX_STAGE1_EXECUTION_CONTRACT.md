CODEX RESEARCH EXECUTION CONTRACT
DSRE: Decision-Sufficient Recovery Explanations
RSS 2027 Stage 1 readiness sprint; IROS 2027 / RA-L continuation
Research decision fixed by supervisor: 13 November 2026.

Repository: /home/imad/Desktop/IEEE-RAL
Expected most recent local research commit: 116dc45b33796b59df7ba6c0332bb120e60a3b9d on research/explanation-repair-week2. This may not be the currently checked-out branch or may not be published on GitHub. Inspect actual local Git state; do not assume a remote ref exists.
New branch: research/dsre-stage1-development
Primary specification: DSRE_STAGE1_RESEARCH_BLUEPRINT.md, supplied by supervisor; if not already in the local repository, locate the user-provided file or copy it into the new branch without modifying historical research. Preserve version 1.0 and explicitly record any discrepancy or amendment.
Current scientific target: RSS 2027 Stage 1 if the evidence merits submission, deadline 4 December 2026, 23:59 AoE. IROS 2027 / RA-L remain future routes, subject to submission rules.
Initial evidence checkpoint desired: 20 November 2026. RSS readiness recommendation desired: 23 November 2026. These are planning gates, not authorization to fabricate or alter results to meet a date.
0. Authority, task, and non-negotiable scope
The principal researcher, not Codex, selects the research question and scientific direction. You implement and empirically evaluate the one fixed problem described below. You may fix engineering defects and report scientific counterexamples, but you may not autonomously pivot to a new paper idea, dataset, architecture, action repertoire, or hypothesis after seeing results.

Fixed research problem: Given a robot's available observation history and a short, fixed set of existing recovery actions, find the smallest set of actual observable facts that suffices to justify an adequately good intervention relative to a declared, finite paired-intervention outcome model. When such evidence does not exist, report why, with verifiable witnesses. Calibrate the actual deployed action-selection procedure separately on independent parent states.

Proposed methodological contribution: (1) intervention-outcome-grounded sufficient evidence, including ties and absolute adequacy; (2) exact minimum evidence or explicit insufficiency witnesses; (3) separate routing-level error calibration. These are a synthesis of established ideas; no general new theory of minimal explanations, hitting sets, active sensing, risk control, or causal inference is claimed.

We are NOT developing a new failure detector, causal discovery system, LLM, language explanation editor, robot controller, physical fault search, simulator, human study, or benchmark-auditing framework. No real robot is required.

The immediate priority is running a credible preliminary experiment with the data and tools we already have. Do not write an RSS manuscript, LaTeX, abstract, slide deck, or PDF in this first session. The supervisor will authorize actual Stage 1 writing only after reviewing the first scientific results. Build the complete methodology and evidence package needed for that decision.

No permission-seeking between the steps already defined here. Finish the fixed first-session work, including negative findings, before returning. Do not promise to keep working after the session ends; make all work resumable.
1. Git and preservation preflight
1. Inspect AGENTS.md, git status, active branch, local commits, uncommitted user changes, existing workers, and existing sealed evidence. Do not reset, stash, overwrite, or include unrelated user edits in your commits. If a clean branch cannot be created without affecting them, use a separate Git worktree at a safe local location from an existing local parent commit.
2. Read the full blueprint and the final portions of RECOVERY_CLAIMS_EXPERIMENTAL_REPORT.md, RECOVERY_CLAIMS_SUPERVISOR_GATE.md, RECOVERY_CONTRACTS_SCIENTIFIC_REPORT.md, and EXPLANATION_REPAIR_RESULTS.md. The latter are background and development evidence, not independent DSRE confirmation.
3. Preserve .gitignore, uv.lock, historical sealed manifests, source data, and prior negative conclusions. Save the initial working-tree inventory and relevant SHA-256 hashes. Keep new raw analysis under a fresh ignored run directory, not inside an existing seal. No push or credentials.
4. Pin the provenance of every prior paired-outcome file. Audit the actual file contents. Never infer a local path solely from the report text. If raw paired outcomes cannot be accessed, record the exact missing dependency and complete the independent E0 algorithm/tests first rather than constructing imagined simulator outcomes.
5. New run root: results/dsre-stage1/<unique-UTC-run-id>/; repo files DSRE_STAGE1_PROTOCOL.md, DSRE_STAGE1_RESULTS.md, DSRE_NOVELTY_MATRIX.md and DSRE_STAGE1_GATE.md.
2. Freeze the scientific problem and formulas before evaluating results
Let physical checkpoint s include robot, object, controller and relevant execution history; let h be the observation history legitimately available to the robot. A frozen feature map x = phi(h) yields at most eight interpretable Boolean predicates with UNKNOWN for unavailable values. Fault-generator labels, physical hidden state, simulator-only future events, paired outcomes, candidate actions' future success, and oracle policy choices are forbidden runtime inputs.

The initial actions are A = {continue, recover} using existing frozen controllers on PickCube and PushCube with a fixed documented horizon and a qualified reset-plus-complete-prefix replay path. No native-snapshot fallback when it fails fidelity checks. No search for new faults or controller improvements.

The initial observed utility is binary task success from each executed continuation, V_i(a) in {0,1}. Do not interpret one deterministic outcome as an expected probability under stochastic execution. For fixed 0 <= epsilon < 1 and v=1, define

regret_i(a) = max_b V_i(b) - V_i(a);

Accept_i = {a : regret_i(a) <= epsilon AND V_i(a) >= v}.

The four distinct cases are: continue-only success, recover-only success, both succeed, neither succeeds. Do not equate ties at failure with adequate actions. Report the occurrence of all four categories before method comparisons.

For reference set D_ref and a conjunction E of observed, available literals consistent with current x, define M(E) as reference states compatible with E. A reference row whose relevant predicate is UNKNOWN cannot be excluded by pretending it disagrees: it is conservatively compatible unless a separate, stated data contract establishes otherwise.

E is sufficient for action a iff |M(E)| >= m_min and every row in M(E) has a in Accept_i. The algorithm chooses globally smallest cardinality evidence; then larger support; then frozen continue-first action tie-break when both acceptable; then deterministic lexical order. An empty explanation is valid when one action is acceptable throughout the declared model; do not force nontrivial examples. Zero-match evidence is invalid.

Scope includes task, fixed recovery repertoire, controller/horizon, and available feature channels. Return INSUFFICIENT when no action is justified or scope/calibration fails. Its reason must distinguish:
- observation-equivalent states with incompatible acceptable actions;
- inadequate action repertoire (neither succeeds in compatible states);
- outcome uncertainty or absent qualified outcomes;
- insufficient reference support / missing observations / scope mismatch;
- insufficient independent calibration support.
An explanation is a decision justification relative to a finite reference intervention model, not a statement of physical root cause or a physical safety guarantee. Do not claim lower sensor acquisition cost merely because fewer facts appear in an explanation.
3. Core algorithm and exact tests, E0
Implement the smallest sufficient-evidence solver using exhaustive subset enumeration or bitset-backed search for d <= 8. Do not add a SAT/MaxSAT service or novel neural architecture. Output a typed certificate:
- action or explicit insufficiency;
- evidence predicates and observed values;
- reference support count and matched reference identifiers (for audits only, not deployed explanation);
- task, action, horizon, utility/epsilon/v, feature scope;
- witness for each necessary literal; incompatible-state or inadequate-action witnesses on insufficiency;
- declared table-relative exactness versus independent deployment-calibration status.
Verify the hitting-set characterization independently: each reference row where candidate action is unacceptable contributes a set of known-opposite observable predicates; choosing evidence must exclude every such bad row while preserving support. An empty difference set implies that action cannot be justified from the current observations. A row with unknown feature values is not allowed to disappear as a conveniently known negative.

Create an independent exhaustive oracle and at least the following exact unit cases:
1. One predicate suffices and a decision stump matches DSRE.
2. Two literals are genuinely required; deleting either has a concrete bad-state witness.
3. Both actions adequate in a state; exact policy-label reproduction is unnecessarily restrictive.
4. Two states observationally indistinguishable but requiring disjoint adequate actions.
5. Both actions inadequate, so regret-only criterion would be misleading.
6. Unknown feature and unknown reference value remain conservative.
7. No reference support, scope mismatch, or insufficient outcome observations.
8. A greedy deletion order returns a longer subset-minimal explanation than exact search on some constructed finite model, only if a genuine counterexample exists.
9. Multiple bad reference rows and ties, with stable canonical selection and no leakage.
10. Removing a literal from a valid minimum must produce a witness or a specified failure, not a fabricated explanation.
Proofs are conditional finite-model facts, not novel general theorems. Record proof assumptions, counterexamples, and comparator equivalences in the research protocol.
4. Direct literature challenge, fixed and bounded
Before evaluating new method numbers, read the primary method sections, not only abstracts, for this short fixed competitor set:
- Khan, Poupart, Black, Minimal Sufficient Explanations for Factored Markov Decision Processes, ICAPS 2009;
- Ribeiro et al., Anchors, AAAI 2018;
- Wu et al., DISCRET: Synthesizing Faithful Explanations for Treatment Effect Estimation, ICML 2024;
- Wang et al., Probabilistic Sufficient Explanations, IJCAI 2021;
- Selvey et al., Formal Explanations of Neural Network Policies for Planning, IJCAI 2023;
- Peddi and Bezzo, IROS 2023, decision-tree recovery;
- RESCUE (2026 preprint), matched recovery interventions;
- DA-GRD (2026 preprint), decision-relevant physical ambiguity;
- Yaacov et al., 2026, sufficient and necessary causal explanations for autonomous systems.
Sources and URLs are already in the blueprint. Inspect accepted robotics work CAPE (ICRA 2024), Pramanick and Rossi (IROS 2024), and relevant CASE/RA-L works only insofar as needed for precise positioning. Do not request another topic search, build a 100-paper survey, or claim that a preprint was accepted without evidence.

Write DSRE_NOVELTY_MATRIX.md with columns: competing claim, exact prior mechanism, overlap, our conditional distinct element, baseline implementation, and evidence still needed. If outcome-aware minimum rules fully subsume DSRE, disclose it. Do not rename the same algorithm to manufacture novelty. Literature review consumes at most 90 minutes of this first session.
5. Qualified development table from previous simulator evidence, E1
Use the existing full paired continue/recover outcomes from RecoveryClaim and earlier replay-qualified development work. The parent units are physical seed and checkpoint, not trajectory frames or multiple certificate variants. Maintain task/condition grouping and canonical state identifiers. Conditions like offset002 and misaligned may be offline strata but must never be runtime features if they are hidden fault labels.

For each paired parent, verify:
- truly the same registered preintervention physical history, condition, action budget, model and controller setup;
- both frozen actions have measured outcomes;
- no already-successful start counted as a newly successful recovery;
- no native snapshot used in place of qualified fresh-prefix outcome;
- distinction between first-hit and terminal success frozen before scoring;
- complete output value labels and raw evidence hashes;
- observation features measured at or before the decision point, not evaluator-only fault or goal outcome labels.
Freeze at most eight candidate observable predicates before looking at DSRE comparisons. Prefer signals actually present in robot observations or declared pose/progress estimates: object near target, grasp/hold state where observable, gripper object-relative placement, recent task progress, goal-distance threshold, gripper closure, relevant contact/proximity. No invented force measurements. The is_grasped simulator boolean is a privileged channel unless independently available through a declared realistic estimate. Put privileged and estimated/observable variants in separate analyses. If any predicate is inaccessible, mark UNKNOWN; do not infer it from future branches.

A short per-task feature dictionary must include: definition, timestamp, physical units, threshold selection origin, availability, whether privileged, and source file. If existing records are insufficient for a feature, select another from already-recorded legitimate channels using physical semantics only, not outcome performance. If fewer than eight exist, use fewer.

Treat all already inspected historical seeds as development-only. Use deterministic parent-group internal splits/cross-fitting only for exploratory tradeoffs. Do not relabel them as a new independent holdout. Do not execute new simulator continuations in this first session.

Report per-task four-way paired-outcome prevalence and feature-pattern collisions. A trivial one-bit rule or all-tie domain is a legitimate negative result. Show how often no adequate action exists, and how often the same observable signature contains incompatible acceptable action sets. The latter limits explanation validity independent of optimizer sophistication.
6. Strong baselines with identical information
Implement these simple methods on the same D_ref, exact feature vocabulary, development groups, fixed actions, and all outcome information that the method is legitimately allowed to use:

B0: Always continue and always recover (boundary controls; no novelty comparison).

B1: Best single-literal rule and best two-literal rule, chosen on development data with a declared support/abstention policy.

B2: CART-style supervised outcome-trained decision tree, depth 1/2/3, with tree-path explanation and a pruning option. It must learn to distinguish {continue only, recover only, both, neither} or equivalent regret/adequacy targets. Do not collapse both-success/none-success into a forced binary label.

B3: Full-evidence outcome selector (small tree ensemble or an equally simple model). It is an information-rich action-quality reference; DSRE is not required to beat it in raw success. Its training and calibration use only the same allowed information.

B4: Policy-faithful minimum evidence for preserving the B3 label, with exact small-vocabulary enumeration or a documented Anchors-style method. This baseline targets model agreement, not actual intervention value. Do not quietly compare its label fidelity to DSRE outcome utility as though they were the same target.

B5: Outcome-aware rule comparator using the same rule grammar and paired outcomes, a minimum support requirement, and average treatment effect / conditional expected utility with abstention. This is a DISCRET-inspired adaptation, not a claimed reproduction of full DISCRET. It is a critical competitor and can match DSRE.

B6: Greedy deletion for DSRE's exact adequacy criterion, using the same reference data and support policy.

B7: Plain outcome-conditioned exact sufficient rule without explicit insufficiency-witness rendering. If mathematically equivalent to DSRE decisions and evidence lengths, report equivalence rather than calling it a weaker distinct comparator. Witnesses alone are an interface difference, not evidence of decision superiority.

Add tests for every baseline's evidence budget, support use, outcome visibility, group separation, and deterministic ties.
7. Metrics and the preliminary science package
Primary joint evaluation: evidence length versus accepted-decision coverage versus unacceptable-action frequency/utility regret, per task. Do not optimize only one axis. An abstention is not a successful task. A method that selects a one-literal explanation but abstains almost always has not established superiority.

Report at least:
- parent/sample count and four-way intervention outcome distribution;
- decision/action accuracy relative to the acceptable-action set, plus absolute success;
- regret/adequacy violation among emitted recommendations, with numerator and denominator;
- episode-level coverage and explanation cardinality conditional on recommendation;
- explanation cardinality at matched coverage and error bands, with infeasible comparisons flagged;
- outcome-aware versus policy-faithful disagreement and instances where their correct answers genuinely differ;
- frequency and correctness of each insufficiency type with witness examples;
- exact-versus-greedy solver length and latency (measured); simple-rule and CART results;
- calibration sample-size feasibility for the whole routed decision rule, by task/action stratum;
- sensitivity to missing/coarsened existing predicate channels, preserving the same observation contract across methods.
Use parent-level paired bootstrap for descriptive comparisons with uncertainty. When a stratum has only a handful of independently qualified parents, state it rather than giving a misleading degenerate confidence interval. No per-frame bootstrap or treatment of multiple rule variants as independent trials.

The Stage 1 empirical goal is not a mandatory positive gain. Produce at least one reproducible simulator-derived example of a truly useful short certificate, one ambiguity/inadequacy witness, and a complete strongest-baseline frontier if the data support these cases. If cases are absent, give counts and the exact observational reason, never create them by selecting convenient fault labels or adding hidden sensors.

The report should say whether the core proposed contribution is scientifically identifiable within the available paired outcome distribution. If a simple stump or outcome-aware rule exactly matches it, label this as a key boundary; do not add a new algorithm.
8. Calibration interface, without fresh physics yet
Implement a frozen-router calibration module as a function with tested contracts, not a claim of held-out deployment validity from reused data:
1. Freeze the full DSRE router and tie-break before calibration.
2. Partition independent new parent states by declared task/action stratum.
3. Count N assigned action and K regret/adequacy violations.
4. Compute a one-sided exact binomial upper bound, with the confidence budget allocated across the predeclared finite strata.
5. Enable the action only if its bound <= alpha; otherwise abstain for calibration insufficiency.
6. Do not reroute a disabled recommendation to a different action after observing calibration outcomes.
7. Separate the finite model's row-wise certificate from the distributional bound.
For zero errors, verify 1 - delta_a**(1/n). Freeze the single primary target alpha=0.10, total delta=0.05, with delta_a allocated across task/action strata; optional alpha=.05 is a planning sensitivity, not a post hoc replacement. Test 0 successes, 0 accepted parents, one rare-action stratum, multiple testing, and task-specific behavior. Do not assert any confidence guarantee unless an independent calibration cohort was actually evaluated.

Compute, from existing development routing frequencies, the expected number of new physical parents needed to obtain adequate accepted parent counts. The blueprint's initial planning candidate is 200 calibration and 200 confirmation parents per task. If routing favors only one action, show honestly why a minority action cannot qualify. No hidden stratification or outcome-conditioned sample selection to manufacture balanced accepted cases.

No new paired physics runs are authorized in the first session. Deliver a prospective fixed seed plan, resource estimate, and readiness decision. Physics execution requires the supervisor's review of this development report. The later campaign, if approved, will use a completely separate new seed pool and preserve the same intervention repertoire and observation contract.
9. Scientific gates and fixed conditional paths
Gate G0: correctness and provenance
Exact solver matches independent enumerator, certificates and witnesses are correct, paired outcome table qualified, and all leaky or privileged fields are flagged. If G0 fails, fix engineering defects, preserve evidence, and finish the parts that remain sound; do not train downstream baselines on corrupted labels.
Gate G1: evaluability
There are enough distinct physical parent states and nontrivial action-outcome categories to analyze the proposed decision sufficiency. If not, report LIMITED_IDENTIFIABILITY with counts and witnesses. Continue the finite-model comparison and source-quality audit. Do not invent or tune new failure scenarios.
Gate G2: simple-baseline challenge
Compare DSRE against B1/B2/B5/B6/B7 at matched information, risk and coverage. If there is a tie, retain it. Do not switch the task or change epsilon/adequacy/vocabulary to force a win. Explain the exact mathematical reason for any equivalence.
Gate G3: Stage 1 scientific contribution
The scientific package may be ready for RSS Stage 1 writing only if the primary methodological gap versus ICAPS 2009, outcome-aware rules/DISCRET and robotic recovery work can be expressed precisely, the formal algorithm/witnesses are independently verified, and preliminary simulator tradeoffs demonstrate a substantive result or a generalizable characterization beyond restating a known theorem.

If G3 fails, report why within the same DSRE question and preserve the negative findings. Do not invent a new project. A negative result can still be a useful paper finding; it does not automatically satisfy RSS novelty requirements.
Gate G4: later IROS/RA-L-scale confirmation
Only after supervisor authorization: use fresh parent seeds, paired physically qualified continue/recover outcomes, independent risk calibration and held-out test, missing-evidence/shift evaluation, and full baseline comparisons. No real robot required. Do not use prospective results to reselect the feature vocabulary or claim guaranteed safety.
10. First-session execution sequence and resource ceiling
This is an autonomous first-session assignment, not an instruction to work asynchronously after tool access ends. Execute in order:
1. Repo preflight, data inventory, read full blueprint, verify previous raw paired outcome access.
2. Freeze a short DSRE-specific protocol and feature vocabulary before scoring method outcomes.
3. Complete the bounded primary-method literature comparison and novelty ledger.
4. Implement exact solver, typed certificates, witness system, and independent finite oracle.
5. Implement and test all listed strong baselines with equal-information checks.
6. Construct development-only table from existing matched physical outcomes.
7. Produce first actual per-task joint length/error/coverage results, feature collision table and witnesses.
8. Implement calibration interface, compute accepted-parent feasibility and register future fresh-seed/resource plan, without running it.
9. Independently recompute the principal outcomes from raw outcomes and source manifests, run tests/Ruff/formatting and preserve failed attempts.
10. Write the methodology/novelty/evidence reports and scientific gate, seal the new run, commit scoped changes locally, no push. Stop with zero workers.
Hard first-session resource ceilings: eight hours campaign wall; ten measured CPU core-hours; zero GPU; no paid API calls; at most 250 MB new public downloads; at most 1 GB new artifacts; no new simulator continuations; no training of foundation models. Read-only access to existing large historical evidence does not count as new artifacts. Preserve the previously agreed orchestration and sealing practices and disclose unmetered overhead. Reserve the final 60 minutes of the session for analyses, independent audit, report, tests and sealing. Stop launching new analytic tasks at hour 7.

No manuscript of any kind in this session. The RSS venue is a planning target, not permission to draft or submit without research supervisor review. No external messages, issues, pushes, downloads of model checkpoints or author contact.
11. Deliverables, scientific acceptance, and handoff
Commit and preserve:
- DSRE_STAGE1_RESEARCH_BLUEPRINT.md if absent in this branch, as supervisor-provided fixed specification;
- DSRE_STAGE1_PROTOCOL.md with observed feature dictionary, exact data and method contracts, frozen E0/E1 protocol and provenance;
- DSRE_NOVELTY_MATRIX.md with primary-paper grounded overlaps;
- DSRE_STAGE1_RESULTS.md with all completed counts, tables, negative outcomes and properly scoped intervals;
- DSRE_STAGE1_GATE.md with STAGE1_READY_TO_DRAFT, PRELIMINARY_ONLY, or BLOCKED, explained against the named G0–G4 gates;
- src/dual_rec/dsre/ (or equivalent narrow independent module): finite solver, certificates, baselines, calibration utility, data adapters;
- tests/test_dsre_*.py with exact finite oracle, unknown observations, witness, baseline fairness, calibration, and provenance tests;
- results/dsre-stage1/<run-id>/ with hashed untracked raw analysis and charts, independent audits, a concise supervisor review archive and source/version manifests;
- one short DSRE_STAGE1_NEXT_7_DAYS.md mapping 19–23 November to the remaining experimental gates, fixed research question, and estimated code/simulator costs, including prerequisites before any fresh seeds are launched.
Scientific correctness rules: A conditional finite-table proof is not a novel theorem; reused results are not untouched confirmation; an all-zero sample difference is not population equivalence; a shorter explanation is not lower sensing cost; an unknown simulator field is not a real sensor; action success is not necessarily physical safety; a simulation study is not a real-robot claim. Do not recommend RSS submission automatically on a green software test suite.

The final message to supervisor must report: branch and local HEAD; E0 independent solver agreement; number of qualified physical parent pairs; paired-outcome category counts and feature collisions; all method metrics and comparisons; whether a stump/B5/B7 matched DSRE; examples of sound witnesses; calibration feasibility and fresh-seed budget; closest-paper overlap and any fatal novelty issue; all experimental limitations; checks/audit status; elapsed time, CPU, artifacts; exact report and evidence paths; no running workers and no push.

Begin implementation now and complete every scientifically justified stage of this fixed first-session protocol. Do not ask for intermediate approval and do not select another topic.