# RSS 2027 Stage 1: methodology-first alternative after the ERR originality result

**19 November 2026 | Research design candidate, NOT demonstrated novelty or a submitted paper**

## Decision

The evidence-resolving recovery (ERR) method should **not** be represented as a distinct new algorithm. The reported latest Codex gate is `METHOD_EQUIVALENT_AND_NOT_DISTINCTLY_MOTIVATED`: an equipped B7 and established active experiment-selection mechanisms reproduce it, and no physical evidence-acquisition gain was established. Its verified physical data remain useful as background and pilot evidence, but do not establish the new hypothesis below. That status is based on the Codex summary supplied in the conversation; the latest local-only detailed reports were not independently accessible here.

**Alternative scientific question:** *Can a robot acquire enough evidence to select a recovery action without destroying the remaining physical possibility of recovery?*

A diagnostic probe is an **action**, not a free measurement. It can perturb contacts, displace objects, consume a grasping opportunity, trigger a safety stop, or cross a task-irreversibility boundary. The inquiry should be designed around the **joint epistemic and physical effects** of that action.

We provisionally name this **Recoverability-Preserving Diagnosis (RPD)**. This name does not establish a first-ever claim. It is a direction to investigate seriously against safe active sensing, contingent planning, s-FEAST and DA-GRD.

## Core technical formulation

Let \(W\) be a finite family of physically possible robot/environment states (including uncertain dynamics parameters). Let \(B\subseteq W\) be the hypotheses consistent with current observations. The candidate **recovery macros** \(a\in\mathcal A\) have terminal task success predicate \(G(w,a)\in\{0,1\}\), or a robustly bounded success probability in a later stochastic extension.

A *physical probe* \(p\in\mathcal P\) has (i) a state transition \(T_p(w)\), (ii) an observation \(O_p(T_p(w))\), (iii) a measured cost \(c_p\), and (iv) declared physical feasibility constraints. There is an optional stop/no-probe decision. The same physical action may both reveal information and irreversibly change which recovery macros succeed.

For each possible probe observation \(y\), the set of possible successor states is

\[
B_{p,y}=\{T_p(w): w\in B,\ O_p(T_p(w))=y\}.
\]

Define the robust *post-probe recovery option* condition

\[
\operatorname{Viable}(B_{p,y}) \iff \exists a\in\mathcal A\ \forall w'\in B_{p,y}: G(w',a)=1.
\]

A probe \(p\) admits a one-step **recoverability-preserving diagnostic decision** iff

\[
\boxed{\forall y\text{ with }B_{p,y}\neq\emptyset,\quad \operatorname{Viable}(B_{p,y}).}
\]

The feasibility requirement extends to a depth-\(H\) contingent policy of probes followed by a recovery macro. For finite deterministic models, define recursively

\[
V_0(B)=\mathbf 1\{\operatorname{Viable}(B)\},\quad
V_{h+1}(B)=V_0(B)\lor\bigvee_{p\in\mathcal P_{\rm allowed}(B)}\bigwedge_{y:B_{p,y}\neq\emptyset}V_h(B_{p,y}).
\]

A minimum worst-case probe-cost solution can be computed by AND/OR search or dynamic programming with a bounded horizon. **These planning mechanisms are established**, and the simple recursion is not claimed as a new theorem. The proposed contribution must be established as a recovery-specific physical decision formulation, a systematic set of bounds/diagnostic counterexamples, and meaningful empirical consequences versus established active-diagnosis and contingent-planning controls.

Stochastic and learned-world-model extensions are explicitly optional Stage 2 work: replace universal success by an explicitly validated risk criterion and constrain model error. Do NOT claim probability, real-world safety or sim-to-real guarantees from this finite deterministic formulation.

## An exact synthetic counterexample, executed in the attached reference checker

There are three hidden cases \(A,B,C\) and two recovery macros `retry` (succeeds on A,B) and `realign` (succeeds on C). No single recovery macro succeeds on all three cases.

A cheaper probe `full_diagnostic` tells exactly which world applies, yielding \(\log_2 3=1.585\) bits, **but physically destroys the sole recovery option in C**. A more expensive `coarse_safe` probe only distinguishes \(\{A,B\}\) from \(\{C\}\), providing 0.918 bits, but preserves the viable macro in every possible world. A conventional static information-only selector prefers the first probe, yet only the second permits guaranteed recovery after diagnosis. The Python checker verifies this exact finite example.

This is a *constructed demonstration of the question*, not evidence that such a regime has been shown in ManiSkill or a novel theorem. A full POMDP planner with correctly modeled transitions can represent the phenomenon. The paper must compare against it.

## One central hypothesis and two derived predictions

**Central hypothesis (empirical, Stage 2):** in partially observed contact-rich recovery, physical diagnostic actions can trade information gain against the future feasibility of recovery. Explicitly accounting for that tradeoff changes which probes should be performed and, in identifiable regimes, enables better terminal task recovery at a fixed probe/action budget than information-only strategies.

**Prediction P1:** at least one independently qualified task family has meaningful incidence of states where higher information-gain probes eliminate a recovery that a lower-information probe preserves. Report zero incidence if absent. Predeclare the perturbations and physical probes, and use source-grounded outcome replay.

**Prediction P2:** at fixed opportunities and costs, the viability-aware contingent policy achieves a measurably different success, probe-cost and irrevocable-failure frontier than no-probe, entropy-maximizing, hindsight-oracle, and a general full-model POMDP/contingent planner. If the general planner ties exactly, attribute the planning capability to the standard algorithm and focus on the recovery-specific phenomenon, not solver superiority.

**Prediction P3:** finite belief-state certificates distinguish (a) insufficient information with a viable probe, (b) adequate information but no physically viable recovery, and (c) absence of a recovery-preserving diagnostic policy from the available menu. These are exactly verifiable in the finite simulator surrogate; they are not claims about a general unknown world.

## Nearest primary work and novelty warning

- Ragan et al., **Online tree-based planning for active spacecraft fault estimation and collision avoidance**, *Science Robotics* 2024: active fault diagnosis with belief-space search and probabilistic state-safety constraints. https://doi.org/10.1126/scirobotics.adn4722
- Wang et al., **DA-GRD**, 2026 preprint: tactile probes selected to make hypotheses agree on a feasible grasp; direct overlap with task-relevant stopping. https://arxiv.org/abs/2609.29065
- Strong planning under partial observability: established belief-state AND/OR contingent planning. https://www.sciencedirect.com/science/article/pii/S0004370206000075
- Hybrid conditional planning for robotic applications, *IJRR* 2020/2021: formal contingent plans with physical feasibility checks. https://doi.org/10.1177/0278364920963783
- Hu et al., **Active Uncertainty Reduction for Safe and Efficient Interaction Planning**, *IJRR* 2023: safe dual control and active uncertainty reduction. https://saferobotics.princeton.edu/research/aur
- RAYA, 2026 preprint: recoverability-aware optimal control and intervention timing; conceptually close to preservation of recovery opportunity. https://raya-control.github.io/

**Most important reviewer objection:** 'This is a special-case reach-avoid POMDP with information gathering.' The paper needs an actual, independently validated robotics phenomenon about *information that changes the recoverable set*, and a well-specified computational/evaluation method. Avoid claiming a new POMDP algorithm, new viability theory, or generic active sensing.

## Why this is a different methodology from abandoned ERR

ERR treated an evidence-acquisition operation as a static distinguishing observation with a cost, and solved a finite separating-experiment problem. With action-dependent \(T_p\), the data-collection operation changes the physical truth of the recovery condition it was intended to identify. A static set-cover optimizer cannot generally account for that. The next-state *recoverability* of all observation-contingent branches is therefore part of the decision problem.

This is a substantive scientific change, not a license to claim the proposed planner is already novel. The full-model POMDP and safe-active-diagnosis baselines remain essential.

## Stage 1 manuscript scope, with or without preliminaries

RSS 2027 Stage 1 is a **semi-complete technical paper**, not a position paper. The official FAQ permits preliminary or ongoing experiments and asks for a concrete technical formulation, explicit testable hypotheses, and actionable methods. A zero-new-experiment submission is possible in principle, but it gives reviewers less evidence of physical feasibility and novel effect; it is not automatically safer. The current DSRE numbers may be used as contextual motivation only, never as validation of the new probe method.

A five-content-page paper should contain: (1) a concrete physical vignette and close-prior contrast; (2) the state, probe, recovery and irreversibility formulation; (3) a checkable finite proof/algorithm and illustrative counterexample; (4) a fully specified Stage 2 empirical design with baseline controls; (5) predicted useful conclusions under both positive and negative outcomes. One references page follows. Figure 1 should depict **a high-information destructive probe versus a lower-information recovery-preserving probe**, followed by separate action choices.

## Feasible Stage 2 validation, not a promise of completed robotics data

By mid-February, implement two frozen probe/recovery interfaces in one controlled contact-manipulation domain and one distinct domain. Start from qualified native simulators, not the previously blocked insertion-prefix route. Pre-register a 10-parent technical pilot per domain with checkpoint replay, genuine physical contrast, available sensor measurements and failure accounting. If a domain fails qualification, disclose the source blocker and request an approved charter adjustment instead of silently substituting a favorable task.

For each qualified task, freeze a physical state/latent-parameter grid and probe menu, then separate model construction from held-out evaluation. Evaluate no probe, greedy information, static ERR, full-model POMDP/contingent planner, task-consensus probing, and the proposed viability-aware objective at **matched actual action-execution cost**. Run enough independent parent instances to estimate recoverability loss, useful intervention, task completion, and adverse probe events with parent-cluster uncertainty. Specify target parent counts only after a source-qualified throughput and power audit, and freeze them before reading test outcomes. Compare against the true task-feasibility oracle for diagnosis but do not give its privileged state to deployment methods.

A genuinely informative negative result would characterize a regime where diagnostic actions are effectively passive, where all probes preserve viability, or where full-model contingent planning is already sufficient. It must be established via controlled variation and uncertainty, not merely a failed integration.

## Adoption condition (before replacing V5)

Use the next 48 hours for a *novelty and feasibility challenge*, not more experiments or another full manuscript. Read s-FEAST and DA-GRD primary methods closely; verify that recovery-option preservation is not equivalent to the tested baseline's stated objective under the proposed observation/action interface. Independently verify the exact worked example and bounded planner; show with a source-supported task definition how the required physical probes can actually be executed and measured. If the only difference is a renamed safe POMDP objective, **do not call this new direction more submission-ready**. The current V5 remains the preserved fallback. There is no guaranteed RSS passage from a zero-experiment submission.

## Official RSS sources checked on 2026-11-19

https://roboticsconference.org/information/author-faq/
https://roboticsconference.org/information/reviewer-guidelines/
https://roboticsconference.org/information/cfp/
