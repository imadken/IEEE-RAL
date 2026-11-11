# Theory-first research reassessment for IROS 2027 / RA-L

**Decision: NO-GO for starting a new 30-day research campaign. No contribution
survives both the originality and evidence requirements in this investigation.**

Date: 11 November 2026. Evidence base:
`9787ee059a47985cf94fa5c610906b14949d678c`. Review branch:
`research/theory-reassessment-20261111`.

The strongest concrete candidate was **certification of a recovery continuation
under contradictory symbolic evidence, with efficient local certificate updates**.
Its basic guarantee reduces to established preferred-repair query answering and
ordinary planning regression. The proposed additional locality guarantee is false
without stronger assumptions; the obvious separator-based repair is standard
variable elimination. I have not established a different, nonclassical theorem
and proof that would justify implementation. This is a rejection of the evaluated
formulations, not a claim that no original robotics theory problem exists.

No new method, robot rollout, simulator experiment, policy training, dependency
installation, lockfile edit, or GitHub push was performed. One unmodified upstream
module was imported solely to check artifact availability; no action or planner
was invoked. Implementation remains stopped pending independent review.

## 1. Scientific boundary and review method

DUAL-REC is terminated. Its negative record is evidence to preserve, not a task
generator for another favorable fault pair. The overnight PickCube qualification
failed its meaningful recovery-reversal and uncertainty gates. The fallback found
numerical/contact divergence but no sampled decision change; its small cohorts do
not establish population equivalence. Neither result licenses new physics tuning,
controller changes, probe experiments, or restoration work.

The preserved [PickCube qualification summary](results/overnight-20261111/20261110T235337Z/d7b/evaluation/report.json)
records six paired failed seeds: the friction recovery contrast was only
`0.01733` (95% interval `0.01341–0.02366`), below the registered `0.10` margin,
and no realistic-history uncertain seeds qualified. The
[overnight audit](results/overnight-20261111/20261110T235337Z/audit/final_verification.json)
records 294 complete replay pairs, seven independent seeds per task, zero success
disagreements and zero action-ranking reversals. These are existing results,
not new experiments or a proof of replay equivalence.

I read the current cumulative reports and protocol, the qualification and replay
summary records, and the repository instructions. At the start of this assignment,
the checkout was clean at the specified commit. A temporary SHA-256 inventory
covers 407 existing tracked/source/result files, including local ignored evidence.
The requested report is the only intended repository addition.

The search window is **2023 through 11 November 2026**, the actual access date;
later November publications cannot be assessed prospectively. Searches covered
robot recovery, executable explanations, uncertain/inconsistent knowledge,
epistemic planning, controller repair, runtime verification, and their classical
foundations. Named-paper searches were followed by primary full texts, cited
formulations, publisher metadata, and public artifacts. Venue-focused searches
included IROS, ICRA, RA-L, RSS, CoRL, IJRR, T-RO, AAAI, IJCAI, ICAPS, NeurIPS and
formal-methods proceedings. I did not treat a keyword hit in an unrelated venue
as a relevant competitor, or a workshop as a main-conference acceptance.

This is a bounded, targeted investigation, **not an exhaustive systematic review**.
Fourteen primary PDFs were retrieved for targeted full-text reading; proof depth
is distinguished below from bibliographic screening. No proof was mechanized or
externally reviewed. Search absence means “not located in this investigation,” not
“does not exist.” Full texts remain in temporary storage, not redistributed here.

Publication status uses primary proceedings or publisher-deposited DOI metadata
where obtainable. IEEE landing pages required bot verification; their public
Crossref records were retrieved separately. AAAI HTML pages were blocked, but the
publisher PDFs were obtainable. A DOI beginning `10.48550/arXiv` is not evidence
of conference acceptance. Author-page conference labels are reported as such.

## 2. Verified literature and positioning

### 2.1 The four specifically requested recent papers

| Paper/version inspected | Verified status and reading | Consequence for selection |
|---|---|---|
| [LOGIV, 2610.40016v3](https://arxiv.org/abs/2610.40016v3), 2 Nov 2026 | Primary PDF, §III, evaluation protocol and Appendix A inspected. Preprint; main-conference acceptance not established. An [ICML SCALE workshop listing](https://scale-icml-2026.github.io/accepted_papers.html) uses an earlier LOGIV title; that is not acceptance of this revision at ICRA/IROS. | A checked PDDL plan supplies a task graph; state assessment can stop as UNRESOLVED. Repair regresses through retained actions and validates the combined continuation. The paper disclaims minimality/completeness. It does not maintain a preferred-repair belief family. These are useful scope differences, not a new theorem. |
| [MAGMA-GEN, 2609.20056v1](https://arxiv.org/abs/2609.20056v1), 17 Sep 2026 | Primary PDF, §§3–4, §6 and baseline appendix inspected. arXiv's journal reference and [author page](https://loanbrnt.github.io/) report CoRL 2026; an independent main-proceedings entry was not located. | A privileged coach proposes localized changes; matched re-execution selects supervision. No general identification or recovery-completeness theorem is supplied. Its dependency on valid continuations and restorable states does not make another replay audit a fresh contribution. |
| [Audit Before You Commit, 2609.30608v1](https://arxiv.org/abs/2609.30608v1), 24 Sep 2026 | Primary PDF, §§III–VI inspected. arXiv says submitted to IEEE. The [project page](https://sites.google.com/view/auditbeforeyoucommit) says ICRA 2027, but acceptance is not independently established. | Separates belief coverage from execution-score optimism. Its history-gate inequality explicitly applies the definition of total variation; the indistinguishable-instance argument assumes a fixed probe policy and incompatible successful commitments. Recasting that bound as a new impossibility theorem is unjustified. |
| [DA-GRD, 2609.29065v1](https://arxiv.org/abs/2609.29065v1), 24 Sep 2026 | Primary PDF, §III and evaluation inspected. Preprint; no accepted venue verified. | Weighted SE(2) hypotheses induce candidate grasps. Probe ranking uses miss exclusion, surface novelty and grasp-support gain; commitment uses a coverage threshold. The evidence is task-specific, not a universal identification theorem. “Stop when an action is supported despite residual state uncertainty” is already explicit. |

### 2.2 Recent formal and robotics work

| Primary reference | Status / depth | Relevant substance and limitation |
|---|---|---|
| [Engesser, Herzig & Perrotin, Towards Epistemic-Doxastic Planning with Observation and Revision](https://ojs.aaai.org/index.php/AAAI/article/download/28919/29748) | AAAI 2024 publisher PDF; §§3–4 and 8–9 read, including proofs. | Theorem 1 constructs a canonical model to relate the REDA fragment to propositional satisfiability. Theorem 2 uses translations to/from classical conditional-effect planning for PSPACE-completeness. Dynamics have explicit observability/depth restrictions. False beliefs are not the same thing as an internally inconsistent sensor database. |
| [Hu, Miller & Lipovetzky, Planning with Multi-Agent Belief Using Justified Perspectives](https://ojs.aaai.org/index.php/ICAPS/article/download/27193/26966/31262) | ICAPS 2023 publisher PDF; semantics, complexity discussion and evaluation read. | History-based perspectives handle false beliefs. The paper distinguishes complete semantics from an efficient ternary evaluation that sacrifices completeness; its soundness statement is relative to KD45, not an arbitrary physical observation model. This prevents claiming a generic new “unknown versus believed” representation. |
| [INPROVF, Meng et al.](https://arxiv.org/abs/2503.13660) | Full preprint inspected, especially verification and limitations. Publisher-deposited metadata verifies [CASE 2025, DOI 11163953](https://doi.org/10.1109/CASE58245.2025.11163953); the version of record was not compared. | New skill candidates are syntax-checked and tested with Slugs after relaxing a violated assumption. Guarantees depend on the abstraction. Evaluation uses twelve violations, 3 versus 5 repetitions, and reports runtime on successful runs. A complete competing protocol must retain unsuccessful runs rather than inherit that conditioning. |
| [Caglar, Zahedi & Sreedharan, Excuse My Explanations](https://sarathsreedharan.com/files/papers/conference/HRI__Excuse_Explanation_ARE__Cam_Ready.pdf) | Author camera-ready, Definitions 1–4, Propositions 1–2, algorithm and evaluation inspected. Publisher metadata verifies [HRI 2025](https://doi.org/10.1109/HRI61500.2025.10973938). | Actionable reconciliation jointly constrains explanations and allowed model edits in robot/human models. Proposition 2's cost comparison follows from independent component lower bounds. It does not establish reachability of arbitrary physical edits; that remaining grounding problem cannot be relabeled as a new explanation-cost theorem. |
| [Carr, Bakirtzis & Topcu, Compositional Shield Synthesis for Safe RL in Partial Observability](https://arxiv.org/abs/2509.12085v1) | 2025 preprint; Theorem 1 and induction inspected. No later accepted venue verified. | The avoid-shield guarantee assumes admissible decomposition, valid local shields and support tracking in a specified POMDP. The proof tracks reachable belief supports. These assumptions do not validate an incorrect symbolic observation model. No RL training is needed merely to compare the shield semantics. |
| [REFLECT, Liu et al.](https://proceedings.mlr.press/v229/liu23g.html) | CoRL 2023 verified in PMLR 229:3468–3484; project/code/data interfaces inspected, not a new proof competitor. | Failure explanations and correction already have an established RoboFail setting. Public summaries or fluent prose alone would not test execution-faithfulness. |
| [VeriGraph](https://verigraph-agent.github.io/) | Author project identifies ICRA 2026; project-level methods inspected, no independent theorem audit or proceedings confirmation here. | Scene-graph action checking and feedback are relevant engineering baselines, not proof that all uncertainty models or physical realizations are certified. |
| [LIBERO](https://proceedings.neurips.cc/paper_files/paper/2023/hash/8c3c666820ea055a77726d66fc7d447f-Abstract-Datasets_and_Benchmarks.html) | NeurIPS 2023 Datasets and Benchmarks proceedings verified; task/requirements files inspected. | An established robotics benchmark, but goal predicates and regions are not automatically a sound symbolic action model. |

Additional recent screening found [EPDDL's official guideline, v3](https://arxiv.org/abs/2601.20969v3)
(2026) and [action-consistent decentralized belief-space planning, v3](https://arxiv.org/abs/2403.05962v3)
(revised 31 Oct 2026). Their primary records were checked; their complete proofs
were not audited, and no main-venue status is inferred. The latter concerns
different robots' information-conditioned beliefs, which must not be conflated
with explosion in a single inconsistent knowledge base. The
[DX 2024 hierarchical monitoring/diagnosis paper](https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.DX.2024.1)
and [RA-L 2026 SRMP-S record](https://ieeexplore.ieee.org/abstract/document/11673306/)
were screened for competing systems; they are not used as proof authorities.
RSS, IJRR and T-RO searches did not produce a more defensible short-path theory
candidate in this investigation. That is a coverage limitation, not a field-wide
negative assertion.

### 2.3 Foundations that rule out easy novelty claims

The following are substantive prior formulations, not optional background:

- **Diagnosis:** [Reiter, 1987](https://doi.org/10.1016/0004-3702(87)90062-2)
  supplies the classical framework. Its publisher record was checked, but a
  university full-text link required authorization; no original proof is claimed
  read. The accessible [Vasileiou, Previti & Yeoh, AAAI 2021](https://arxiv.org/abs/2012.09274)
  explicitly states the MUS/MCS hitting-set duality and its use in minimal
  reconciliation. Its Definitions 2–7 and Propositions 1–2 were inspected.
- **Repair-based reasoning:** [Arenas, Bertossi & Chomicki, PODS 1999](https://marceloarenas.cl/publications/pods99.pdf)
  defines consistent answers through repaired databases. Primary PDF and the
  soundness/completeness discussion were inspected. Query languages and repair
  choices matter; one cannot transfer every complexity result to arbitrary
  propositional weighted histories.
- **Preferred repairs:** [Bienvenu, Bourgaux & Goasdoué, AAAI 2014, extended proof version](https://www.labri.fr/perso/meghyn/papers/BieBouGoa-AAAI14-long.pdf)
  studies reliability preferences and AR versus IAR answers. Theorem 3 reduces a
  priority-repair query to propositional unsatisfiability. The encoding separately
  handles absence of query support, repair maximality and consistency. Its
  restricted DL/query complexity is not a new robotics complexity bound.
- **Actions and repair:** [Calvanese et al., IJCAI 2013](https://www.ijcai.org/Proceedings/13/Papers/126.pdf)
  already interleaves actions and repairs and quantifies over them. Theorem 4.3
  assumes run-boundedness; Theorem 6.1 provides weak acyclicity as a sufficient
  condition. [Calvanese, Montali & Santoso, IJCAI 2015](https://www.ijcai.org/Proceedings/15/Papers/403.pdf)
  adds generalized execution semantics and Golog-style programs. Theorems 2–5
  compile verification into standard KAB verification. I traced the repair-step
  translation and boundedness argument, not a mechanized validation of every
  compilation detail. Exact maximal-repair semantics is an essential premise;
  consistency alone is not a substitute (§5.4).
- **Belief change:** [AGM, 1985](https://doi.org/10.2307/2274239) and
  [Katsuno–Mendelzon's revision/update distinction](https://www.cambridge.org/core/books/abs/belief-revision/on-the-difference-between-updating-a-knowledge-base-and-revising-it/8ADFFF65FA776C21E8646D6F4D2434AB)
  predate the proposed separation of new information from a changed world.
  Publisher metadata/summaries were checked; these full foundational proofs were
  not retrieved. They are not claimed as original results here.
- **Argumentation:** [Dung, 1995](https://doi.org/10.1016/0004-3702(94)00041-X)
  is the foundational acceptance/extension formulation. Choosing skeptical versus
  credulous or preferred versus stable semantics is part of a specification, not
  an innovation by itself. Publisher record checked; full proof not audited.
- **Explanations and verification:** [Chakraborti et al., IJCAI 2017](https://ijcai.org/proceedings/2017/23)
  already makes model reconciliation an optimization problem. The
  [three-valued runtime-verification formulation](https://doi.org/10.1145/2000799.2000800)
  distinguishes an inconclusive prefix from satisfaction/violation; this differs
  from certifying every branch of a future recovery policy. Neither adding
  provenance nor returning UNKNOWN proves physical soundness.
- **Local computation and grounding:** [Dechter's bucket elimination](https://doi.org/10.1016/S0004-3702(99)00059-4)
  is an established reasoning framework. [PDDLStream, ICAPS 2020](https://www.icaps-conference.org/recording/pddlstream-integrating-symbolic-planners-and-blackbox-samplers-via-optimistic-adaptive-planning/)
  is a relevant prior interface for symbolic plans and black-box geometric
  samplers. New guarantees cannot consist solely of composing these interfaces.

## 3. Serious candidates and rejection decisions

These are separate candidate questions, not modules of a proposed architecture.
Effort figures are planning estimates, not measured runtimes or acceptance odds.

### C1. Recovery certificates with local updates under contradictory evidence

1. **Question:** Can an exact certificate for a fixed recovery-plus-retained-suffix
   be updated using only the plan conditions affected by new evidence?
2. **Closest formulations:** preferred-repair answers, inconsistency-aware KABs,
   and LOGIV's retained-continuation check (§6).
3. **Desired new result:** a precise locality characterization permitting exact
   incremental certification without global repair reasoning.
4. **Proof analysis:** basic certification has the standard reduction in §5. The
   stronger plan-local invariance statement is refuted by §5.3. A sufficient
   separator condition leads to ordinary max-sum elimination (§5.5), not a new
   result. No new parameterized boundary or algorithmic theorem is established.
5. **Without empirical gain:** a genuinely new exact characterization would still
   matter; the currently available statements are classical or false.
6. **Robotics application:** checking that a kitchen manipulation continuation is
   executable despite disagreeing support/containment observations.
7. **Benchmarks/dependencies:** LIBERO tasks and LOGIV core are public; a sound
   observation/action abstraction and competing exact repair solver are not
   supplied by that combination. MaxSAT/SAT and a plan validator would be needed.
8. **30-day cost:** approximately 10–15 days for grounding/solver integration and
   10–15 for a serious evaluation, leaving little proof-discovery margin.
9. **Reviewer objection / decision:** “CQA plus regression with a robotics wrapper.”
   Currently correct and fatal. **Reject; focal analysis below is not a GO.**

### C2. Physically executable explanations of recovery decisions

1. **Question:** Which explanatory changes to an operator's world model can the
   robot actually realize while preserving the rest of its task?
2. **Closest formulation:** actionable reconciliation explanations (ARE), with
   model reconciliation and task-and-motion planning as necessary comparisons.
3. **Desired new result:** necessary/sufficient conditions connecting an allowed
   explanatory model edit to an executable, task-preserving action sequence.
4. **Proof analysis:** a proof by induction over sound grounded actions is ordinary
   plan/refinement soundness. Treating an edit as reachable by definition is
   circular. A new structural result beyond planning/TAMP has not been found.
5. **Without empirical gain:** such a new characterization could matter; mere
   model-edit reachability or a sum-of-component-cost bound does not suffice.
6. **Robotics application:** explain a failed placement and realize a permissible
   support/clearance change, without falsely suggesting impossible recourse.
7. **Artifacts:** ARE code/IPC examples and RoboFail are relevant. IPC problems alone
   are not robotics validation. Realized-recourse ground truth is not already
   established by a prose explanation or a goal predicate.
8. **30-day cost:** likely 15–20 days of grounding and baseline adaptation, then
   validation; a human-interpretability claim would also require a proper study.
9. **Reviewer objection / decision:** “ARE plus an existing motion planner; where
   is the new theorem?” Not answered. **Reject.** Do not promise a human study or
   create a favorable explanation benchmark to rescue it.

### C3. A decision-identifiability boundary for recovery

1. **Question:** When do available observations distinguish states requiring
   incompatible commitments?
2. **Closest formulations:** classical partially observed decision problems, Audit
   Before You Commit's fixed-history argument, and DA-GRD's action-support criterion.
3. **Proposed result:** an observation-equivalence/action-compatibility condition.
4. **Proof analysis:** indistinguishable histories and incompatible successful
   actions give a standard indistinguishability argument. A total-variation bound
   is not a new result; changing the probe policy changes the experiment.
5. **Without empirical gain:** only a new nonclassical characterization would
   survive. None is established here.
6. **Robotics application:** irreversible assembly commitment under occlusion.
7. **Artifacts:** the named grasp/insertion papers are relevant, but exact code,
   assets and executable reproduction were not verified for both systems.
8. **30-day cost:** credible physical grounding would require another qualification
   campaign. The terminated project's recovery-pair search cannot be restarted.
9. **Reviewer objection / decision:** “A classical information bound supported by
   a hand-selected example.” Correct for the current formulation. **Reject.**

### C4. Certifying recovery after an assumption violation

1. **Question:** Can a controller recover while current symbolic evidence is
   uncertain, rather than silently trusting a single state estimate?
2. **Closest formulations:** INPROVF, partial-observation shields and epistemic
   planning with revision.
3. **Desired new result:** an exact recovery-permission characterization for a
   specified uncertainty model and a meaningful restricted class of controllers.
4. **Proof analysis:** “safe for every state in the belief support” and an induction
   under a correct model are existing proof patterns. They do not certify the
   observation model that generated that support. No distinct new fragment,
   completeness theorem or complexity separation has been established.
5. **Without empirical gain:** a new characterization would matter; composing a
   verifier with an uncertain state estimator is insufficient by itself.
6. **Robotics application:** mobile manipulation after an unexpected object-state
   transition, with safety constraints that remain mandatory.
7. **Artifacts/dependencies:** Slugs/GR(1), epistemic planners and exact belief-state
   checking are relevant; a directly executable common robotics benchmark is not
   supplied by simply placing their outputs in one interface.
8. **30-day cost:** at least a week for synthesis integration plus a substantial
   abstraction/uncertainty-validation effort; a fair campaign is not yet scoped.
9. **Reviewer objection / decision:** “Existing shielding with assumptions that
   exclude the hard cases.” Not answered. **Reject.**

No candidate is retained merely because its implementation appears convenient
on the existing simulators. No positive empirical improvement is presumed.

## 4. Full formal problem for the rejected focal candidate C1

This specification makes the novelty test checkable independently of robotics.
It is **not a proposal to implement it as a new method**.

### 4.1 Inputs and semantics

Let `F` be a finite set of Boolean fluents and `V = {0,1}^F` its valuations. Let
`T` be a propositional theory of hard constraints with `Mod(T) != empty`.
An inconsistent `T` is an invalid input requiring abstention, not a license to use
classical explosion.

At the decision time, observations are indexed records

`H = ((id_i, source_i, time_i, o_i, w_i))_(i=1..m)`,

where `o_i` is a formula about that decision state and `w_i` is a strictly positive
integer priority weight. The weights are an explicitly chosen preference policy,
**not probabilities or calibrated sensor reliabilities**. A temporal grounding
model must justify projecting a historical measurement to the decision state;
old measurements cannot simply be treated as current facts after a world change.

Define the preferred repair family

`R*(H) = argmax_(R subseteq {1,..,m}, SAT(T AND AND_(i in R) o_i)) SUM_(i in R) w_i`.

The corresponding uncertainty set is

`B(H) = UNION_(R in R*(H)) Mod(T AND AND_(i in R) o_i)`.

All optimal repairs and all their model completions are included. A single
most-preferred repair with arbitrary tie-breaking is not an equivalent semantics.
With finite inputs and consistent `T`, the family is nonempty, even if the empty
set of observation records is the only feasible subset.

Let `A` be a finite fixed library of deterministic partial symbolic actions. Each
action `a` has precondition `pre_a` and successor function `delta_a` where enabled.
Let `I` be the required safety invariant and `g` the task goal. Let `kappa` be a
fixed retained suffix and `C` a finite declared library of repair fragments. A
candidate continuation is `pi = r . kappa`, for `r in C`.

For a fixed sequence `pi`, define its weakest precondition recursively:

`WP_epsilon(g)(s) = I(s) AND g(s)`;

`WP_(a.pi)(g)(s) = I(s) AND pre_a(s) AND WP_pi(g)(delta_a(s))`.

The second expression is false if `a` is undefined. Certification requires

`Licensed(H,pi) iff B(H) != empty AND FOR ALL s in B(H): WP_pi(g)(s)`.

The decision problem is to return all licensed continuations, or abstain. Optional
selection minimizes a fixed declared cost over **this finite library**; it does
not establish optimality over every physically possible recovery. A safe stop can
be represented separately and must not be counted as task completion.

Nondeterministic actions require universal quantification over every permitted
successor and an explicit nonempty-enabledness guard. That extension is ordinary
strong planning; it is not justified by checking a single sampled execution.
Higher-order beliefs, learned observation likelihoods and continuous geometry are
not covertly included in this finite propositional formulation.

### 4.2 What an independently checkable certificate would contain

The input history, its provenance and preference rule remain fixed. A certificate
must identify `T`, the action model, `I`, `g`, `kappa`, the candidate and the exact
repair-selection objective. It must support both the optimal preference score
and the absence of a violating preferred-model completion. Showing one feasible
repair or one successful trajectory is insufficient.

Physical validity requires an additional justified relation between real states
and symbolic states: the current real state must be covered by `B(H)`, predicate
groundings must be correct, and real executions must refine permitted abstract
transitions while preserving the physical meaning of `I`. These obligations are
not discharged by a SAT/plan proof. Contradiction handling does not automatically
repair an inaccurate hard theory or an incomplete hypothesis catalogue.

## 5. Candidate theorem statements, proofs and boundary checks

### 5.1 P1: weighted-repair characterization — true, not original

For `s in Mod(T)`, let `score_H(s) = SUM_i w_i * 1[s satisfies o_i]` and
`beta = max_(s in Mod(T)) score_H(s)`. Then

`B(H) = {s in Mod(T) : score_H(s) = beta}`.

**Proof.** Any feasible repair is satisfied by some valuation, whose score is at
least the repair weight. Conversely, a valuation satisfies a feasible repair
containing all records true there, with exactly its score. Hence the optimal
repair weight equals `beta`. A model of an optimal repair cannot satisfy extra
positive-weight records that would make its score exceed `beta`. A maximum-score
valuation satisfies an optimal repair. These establish both inclusions.

Consequently, for an exactly encoded deterministic continuation,

`Licensed(H,pi) iff UNSAT(T AND (score_H = beta) AND NOT WP_pi(g))`,

with the nonempty/valid-input conditions retained.

This is a weighted MaxSAT/preferred-model query characterization, not a new
theoretical contribution. Preference semantics cannot be silently changed from
weighted optimum to inclusion-maximal repairs: they need not select the same
models. The previous query-answering literature is directly relevant.

### 5.2 P2: continuation soundness — true under explicit assumptions, classical

For every finite sequence `pi` and valuation `s`, `WP_pi(g)(s)` holds exactly when
`pi` is executable from `s`, every visited state satisfies `I`, and its terminal
state satisfies `g`.

**Proof.** Induct on sequence length. The empty case is `I AND g`. For `a.pi`, the
recurrence requires safety now, an enabled first action, and the inductive
property at its successor. Necessity follows by taking the first transition of
any safe successful sequence; sufficiency follows by concatenating it with the
inductively safe suffix.

Combined with P1, this proves symbolic validity across the chosen uncertainty
set. With the physical coverage/refinement obligations in §4.2, an ordinary
refinement induction transfers the result to the represented physical executions.
**It proves no unconditional real-robot guarantee.** Regression, universal belief
checking and this induction pattern are established; a robotics instantiation
alone does not satisfy the requested theory novelty.

### 5.3 Proposed new locality claim — false as stated

**Candidate claim:** an observation change outside the preconditions/effects and
producer–consumer graph of a retained plan cannot alter its certification result.

**Counterexample.** Take fluents `p,q`, hard constraint `T = (p iff q)`, and a
one-action continuation with `pre_a=p`, identity successor, `I=true` and `g=p`.
Initially `H` contains just `(p, weight 1)`. The only preferred valuation
is `(p,q)=(1,1)`, so the continuation is licensed. Add `(NOT q, weight 2)`. The
two models of `T` now have scores:

| Valuation | Initial score | Score after new evidence |
|---|---:|---:|
| `p=1,q=1` | 1 | 1 |
| `p=0,q=0` | 0 | 2 |

The continuation loses certification, although `q` is absent from its plan's
preconditions/effects. The omitted link is in the background constraints and
preference problem. This refutes **our candidate extension**, not a locality
guarantee claimed by LOGIV. The example is a logical counterexample, not a new
robot benchmark or an empirical result.

### 5.4 Other essential boundary cases

**A consistent remainder need not be a maximal repair.** Let
`T = NOT(p AND q) AND NOT(p AND r)` and observations be `{p,q,r}`. Delete `q`
to resolve the first conflict, then `p` to resolve the second. The result `{r}`
is consistent but is not maximal: `{q,r}` is a consistent strict superset.
The inclusion-maximal repairs are `{p}` and `{q,r}`; with equal positive weights,
only the latter is maximum-weight. An implementation must establish the intended
maximality/preference condition, not just iterate conflict deletion. This is a
sanity check on a possible implementation, not a verified new error/correction
of a published KAB compiler.

**Repair entailment differs from intersecting repaired facts.** With the same
constraints, observations `{p,q}` have inclusion-maximal repairs `{p}` and `{q}`.
Each entails `p OR q`; their intersection does not. This is the established
AR/IAR distinction, not evidence for a new robot-specific logic.

**Symbolic confidence does not supply truth coverage.** Let `T=true` and records
be `(p,2)` and `(NOT p,1)`. Preferred models satisfy `p`. If the real state has
`NOT p`, an action requiring `p` can be symbolically licensed but physically
invalid. This violates the coverage assumption, not P2. Arbitrary trust weights
cannot serve as a distribution-free physical guarantee.

**Weak and strong recovery quantifiers differ.** Two indistinguishable worlds may
each admit a recovery, but require different actions. `FOR ALL s EXISTS r` does
not imply `EXISTS r FOR ALL s`. Observation-dependent policies require an
explicit sensing model. This is a classical planning distinction, not an original
impossibility theorem or a reason to restart the terminated probe project.

### 5.5 Why a separator-based rescue is not yet a contribution

Suppose the *complete reasoning model*, not merely the plan graph, factorizes as
`T_Q(x,z) AND T_R(y,z)`, the score as `f_Q(x,z)+f_R(y,z)`, and the continuation
query depends only on `(x,z)`. Define

`m_R(z) = max_(y satisfying T_R(y,z)) f_R(y,z)`

(value `-infinity` for infeasible boundary assignments). Global preferred models
can be checked through `max_(x,z satisfying T_Q) [f_Q(x,z)+m_R(z)]` and the
corresponding maximizing `(x,z)` assignments.

The proof is exchanging two finite maximizations and using that the query cannot
inspect `y`. The boundary must include every hard-constraint, preference and
query interaction. Ignoring one recreates §5.3. This is standard variable
elimination/message passing. A new tractable robotics fragment, nontrivial
succinctness result or strict algorithmic improvement would require a separate
statement and proof. None has been established in this review. No fresh
complexity class or lower bound is claimed.

## 6. Exact differences from the five closest focal competitors

These differences define a problem specification, not five proofs of novelty.

| Closest formulation | What is already supplied | Difference of C1, and why it does not yet justify a paper |
|---|---|---|
| Preferred-repair query answering, AAAI 2014 | Reliability-sensitive repair semantics; AR/IAR distinction; consistency/maximality/query encodings and restricted complexity results. | C1 uses a continuation weakest-precondition query with finite weighted observations. Substituting that query is a routine semantic composition. It does not establish a new query class or complexity boundary. |
| Inconsistency-aware KAB/GKAB verification, IJCAI 2013/2015 | Evolving knowledge, explicit repair strategies and temporal verification; reductions under stated boundedness conditions. | C1 has a finite fixed action library and retained suffix, rather than general data-generating programs. It does not inherit physical grounding or repair-cost optimality for free. Those omissions leave engineering work, not a proven new verification principle. |
| Epistemic-doxastic observation/revision, AAAI 2024 | A precise restricted action formalism handling knowledge, belief and observations, with satisfiability and planning results. | C1 concerns contradictory reports inside one observation base, not only false beliefs across agents. The semantics differs, but combining known repair reasoning with a different belief language does not establish a new theorem. |
| INPROVF, CASE 2025 | Verification-guided repair of a known assumption violation through proposed new abstract skills, checked for syntax/realizability. | C1 keeps the skill library fixed and certifies a continuation across uncertain initial models. This changes the problem and makes raw runtime comparison unfair. Exact conformant reasoning, not an unmodified single-state LLM baseline, is the necessary strong comparator. |
| LOGIV, 2026 v3 | Unknown/UNRESOLVED handling around a current symbolic estimate; retained-plan regression and combined-plan validation. | C1 preserves multiple preferred repaired models and asks for exact incremental certification. A public `State` with unknown markers is not that model family. Nevertheless, global certification is classical and the desired plan-local update theorem fails. |

The hypothetical advantage over a single guessed state or an intersection-only
baseline is not evidence against the exact existing formulation. Likewise,
correcting an adaptation's missing uncertainty handling is not a theoretical
advance over its source paper.

## 7. Reference method and algorithm — not a recommended new method

For auditability, the finite deterministic version could be solved as follows:

```text
Input: fixed H, T, action model, invariant I, goal g, suffix kappa, library C
1. If T has no model, return INVALID_MODEL.
2. Compute and certify beta = max score_H(s) over s satisfying T.
3. For every declared fragment r in C:
     pi := r followed by kappa
     Phi := exact weakest precondition for pi, I and g
     Check T AND (score_H = beta) AND NOT Phi.
     If UNSAT, retain pi with its objective/query proof artifacts.
4. Return all retained continuations, or abstain if none.
5. If selecting one, use only the predeclared cost and tie rule.
```

An optimality proof is needed for step 2, not merely a feasible optimizer output.
Step 3 must preserve *all* optimal models; proof certificates and a checker must
match the chosen backend. Exhaustive finite enumeration is an independent small-
instance reference, not a scalable method claim. The nondeterministic case needs
an appropriate universal-transition encoding, not the same SAT check unchanged.

This algorithm is a specification of an existing-reasoning baseline. Implementing
it faster, adding a language-model front end, or demonstrating wins against a
single-repair heuristic would not by itself satisfy the research objective.

## 8. Public artifacts and actual feasibility checks

### 8.1 What was obtained or checked

| Artifact | Evidence obtained | Execution status / dependency consequence |
|---|---|---|
| [LOGIV core at `0ea7a7ff765016a33409c54572d733bed4503d4d`](https://github.com/Enqiao-Lu/LOGIV/tree/0ea7a7ff765016a33409c54572d733bed4503d4d) | README, `pyproject.toml`, `core/symbolic.py`, `core/repair.py` inspected. Symbolic state/update/regression definitions are available; package declares Python >=3.11 and no mandatory dependencies. | Unmodified symbolic definitions imported under existing Python 3.12.12. No planner/action was called. Full execution additionally requires planner/validator, perception and benchmark/policy integration. README warns that linked weights are not the full paper-specific checkpoint set. **Not an end-to-end reproduction.** |
| [LIBERO at `8f1084e3132a39270c3a13ebe37270a43ece2a01`](https://github.com/Lifelong-Robot-Learning/LIBERO/tree/8f1084e3132a39270c3a13ebe37270a43ece2a01) | Public LIBERO-10 task listing and stove/moka-pot BDDL file read. Objects, regions, initial predicates and goal are available. | Requirements include robosuite 1.4.0 and NumPy 1.22.4; this repo pins 1.5.2 and 1.26.4. Neither LIBERO nor its dependencies were installed. BDDL goal files do not supply a verified symbolic skill-transition model. A future isolated environment and physical abstraction validation are required. |
| [MAGMA-GEN at `b84cccb14dccde43eeff375b7b1317aeb8037213`](https://github.com/MAGMA-rob/magma-gen/tree/b84cccb14dccde43eeff375b7b1317aeb8037213) | Current public README and [official workflow](https://magma-rob.github.io/docs/use-magma-gen/overview) inspected. | Current software is v2 while paper software is v0.1; docs state model checkpoints are not released. Agent/planner services and an appropriate model are additional requirements. Full paper training is not an admissible cheap baseline for this assignment. No service/model launched. |
| [REFLECT at `c2f9db993e372250321ca74e56ae27519716c934`](https://github.com/real-stanford/reflect/tree/c2f9db993e372250321ca74e56ae27519716c934) | Original Columbia URL redirects to real-stanford. README and dataset links found; [RoboFail project](https://robot-reflect.github.io/) is public. | Authors tested Python 3.9.13/Ubuntu 20.04; AI2-THOR and vision/audio dependencies need isolation. The original Columbia data URL returned 403; README provides a Drive alternative whose archive/labels were not downloaded or verified. Dataset recoverability remains an open check, not a claim of nonexistence. |
| [Justified-perspective model at `808c10bc9ea2968b0adbc35c2fbb73f38e13e7b9`](https://github.com/guanghuhappysf128/justified_perspective_model/tree/808c10bc9ea2968b0adbc35c2fbb73f38e13e7b9) | Paper's `bpwp` repository points here. Benchmarks, current tree and project metadata inspected. | Current metadata requires NumPy >=2.4.4 and pytz >=2026.1.post1, unlike older README instructions. Those are not the pinned local environment. No installation or planner execution performed; current code is not assumed identical to the 2023 evaluated revision. |
| [ARE at `7e5e746d0ea2fb914328e51c63d795b5f961df99`](https://github.com/cglrtrgy/ActionableExplanations/tree/7e5e746d0ea2fb914328e51c63d795b5f961df99) | Code, notebooks, user-study directory and `Code/3_ARE/src` listing inspected. | Shell scripts call grounding/planning/validation components. End-to-end dependency compatibility was not established. No human-study claims can be reproduced by inspecting the directory alone. |
| [AAAI 2021 reconciliation at `879615205f779021f16263691b7612eccf4c1fd3`](https://github.com/vstylianos/aaai21/tree/879615205f779021f16263691b7612eccf4c1fd3) | Primary paper identifies repository and PySAT use; repository README is obtainable on `main`, not `master`. | PySAT is absent locally. No solver installed or run. This is a relevant exact explanation baseline, not evidence that a new optimization objective is solved already. |

The import-only LOGIV source copy has SHA-256
`20955c2119b22cbe637eb2c02ed6ad869f77956a4ecdffe6e1155a9f9d5f0100`.
Its definitions were the only third-party code executed. Local read-only module
checks found no `pysat`, `z3`, `clingo`, `pytz`, `alfworld`, or `libero`. Their
absence is often readily repairable in a **future isolated environment**; it is
not a scientific impossibility. No existing package or lockfile was altered.

The requirement to establish full baseline execution is therefore **not passed**.
Available source files, an import smoke check, and a working older simulator
stack are not equivalent to an executable comparative robotics campaign. The
originality rejection is independent of this open feasibility gate.

### 8.2 Benchmarks that would genuinely exercise the theory

LIBERO is a credible physical task source because successful action sequences
depend on object/support/container state, not just text fluency. Its Spatial,
Object and Goal suites offer different task regimes without inventing a favorable
fault pair. However, no corrupted-observation model, priority policy or sound skill
abstraction should be assumed supplied by the benchmark.

RoboFail could test explanation and evidence provenance with established robot
experience records. It does not automatically supply preferred-repair ground
truth or executable counterfactual explanations. A small, independently annotated
subset might suffice for a reviewed future project; it is not a validated dataset
in this assignment.

[ALFWorld](https://github.com/alfworld/alfworld) provides aligned textual/embodied
household environments, public PDDL/game assets and documented CPU text mode.
It is a possible symbolic sanity benchmark; text-only success alone would not
establish the physical grounding required here. IPC tasks and epistemic planning
benchmarks can test algorithms, but cannot be the sole robotics evidence.

No custom large dataset, foundation-model training, new robot hardware or physical
failure-pair campaign is recommended. A hypothetical project must use exact CQA/
MaxSAT plus conformant reasoning as the principal semantic comparator. Single-
repair, intersection-only and guessed-state variants are ablations, not sufficient
strong baselines. Robot execution baselines must use the same fixed skills,
observations, costs and timeouts; adapted versions must be labelled as adaptations.

## 9. Statistical protocol if a genuinely new result were independently approved

This is a feasibility specification, **not authorization or a scheduled campaign**.

1. **Separate formal and empirical obligations.** A complete counterexample
   falsifies an advertised soundness theorem or its implementation. Positive
   task success cannot prove the theorem. Separately test whether physical state
   coverage and transition refinement actually hold.
2. **Freeze the model before test data.** Fix the fragment, hard constraints,
   uncertainty semantics, source priorities, candidate skill library and endpoint
   definitions. Use development tasks for engineering; hold out task templates/
   layouts for evaluation. No qualification case should select its own logic or
   corruption severity.
3. **Use multiple regimes.** Include complete consistent observations, missing
   observations, contradictory reports, and explicitly timestamped stale reports.
   Establish their relevance from benchmark traces or independent annotation;
   if only synthetic corruptions designed around the theorem work, stop. Do not
   fabricate a new physical benchmark to guarantee an advantage.
4. **Keep units independent.** Pair methods/regimes by the same task/initial-state
   group. Repeated frames, repairs and continuations are not independent samples.
   Report task-wise results; use a hierarchical bootstrap over tasks and initial
   states where tasks are sampled, or state clearly when inference is conditional
   on a fixed task set.
5. **Report the actual obligations.** Certificate soundness/completeness relative
   to an exact small-instance oracle; physically invalid permissions; abstention
   and goal completion; plan preservation; proof-checking time/size; and end-to-end
   wall/CPU cost. No explanation-faithfulness score based only on fluent text.
6. **Use direct tests and uncertainty.** Paired binary comparisons can use exact
   McNemar tests on independent paired groups, supplemented by paired effect CIs;
   task dependence needs stratified/clustered analysis. Use paired bootstrap CIs
   for cost differences and include censored timeouts in bounded-budget outcomes.
   Preregister a primary endpoint and adjust multiple confirmatory comparisons.
   Choose sample size from a blinded development estimate of discordance and a
   declared minimum relevant effect; no power is asserted from the present data.
7. **Do not hide rare errors.** Zero violations in `n` independent groups still has
   one-sided exact 95% upper probability bound `1 - 0.05^(1/n)`. Approximately
   299 independent groups are needed for a sub-1% bound after zero violations.
   This is a standard binomial calculation, not a new guarantee; correlated frames
   cannot be counted as those groups.
8. **Preserve negative outcomes.** Retain all attempted cases, invalid models,
   solver failures, abstentions and unreachable goals. Predeclare termination
   gates. A formal gain with no task-success gain could still be scientifically
   useful **if the formal gain were new**; current P1/P2 do not meet that condition.

## 10. Strongest reviewer objections

| Objection | Evidence needed for a satisfactory answer | Present disposition |
|---|---|---|
| “This is classical CQA plus regression.” | A precise result not implied by that composition, with proof and exact comparator. | Fatal; not supplied. |
| “The locality theorem ignores ontology/preference dependencies.” | Correct dependency model and nontrivial valid theorem. | Counterexample refutes the current statement. |
| “The proof assumes away physical uncertainty.” | Independent coverage/refinement validation and honest limits. | Not available; simulator access does not establish it. |
| “Your baseline lacks the uncertainty semantics you added.” | Exact existing solver under the same semantics and budget. | Required; heuristic wins would be insufficient. |
| “The benchmark was constructed to favor the method.” | Established tasks, independently justified uncertainty and locked test distributions. | Not established; do not manufacture it. |
| “This is an explanation interface, not executable reasoning.” | A checked link from explanation to real admissible actions and task consequences. | No new characterization found. |
| “The system papers were not reproduced.” | Immutable versions, assets, working dependency isolation and executed comparisons. | Source availability partially verified; full reproduction remains open. |
| “Thirty days is too short for theory discovery plus grounding.” | A nearly complete novel proof and an already demonstrated evaluation path. | Neither is ready. |

The current submissions would face a substantive novelty objection even if an
engineering prototype improved task success. That makes a 30-day IROS/RA-L
campaign a poor scientific commitment. No acceptance probability is estimated.

## 11. Thirty-day critical path and early termination gates

**The day-zero gate is closed. This report recommends stopping now, not executing
the following hypothetical schedule.** A new, independently reviewed theorem
would require a new authorization before any implementation.

| Days | Deliverable if that new authorization existed | Hard termination gate |
|---|---|---|
| 0–2 | Independent review of the exact novelty claim against CQA/GKAB, epistemic planning and shielding; full proof and counterexamples. | Stop if it is P1/P2, ordinary elimination, an unproved locality assertion, or an already known boundary. **Current outcome: stop.** |
| 3–5 | Obtain exact baseline versions/assets in an isolated environment; demonstrate a public robotics task and an independently checked abstraction. | Stop if only text examples, unavailable checkpoints, or a favorable custom domain support the claim. |
| 6–10 | Minimal implementation of only the reviewed result; exact small-instance checker and certificate verification. | Stop on an unresolved soundness counterexample or inability to compare against the exact semantics. |
| 11–14 | Blinded development feasibility/power study; finalize tasks, uncertainty regimes and resource throughput. | Stop if the uncertainty is artificial, physical abstraction fails, or a credible held-out campaign does not fit the remaining time. |
| 15–22 | Locked evaluation on established multiple task regimes, common baselines and independent groups. | Stop for an invalid model or preservation failure; retain scientific negative results. No parameter hunt. |
| 23–26 | Independent result recomputation, proof review, complete denominators and robustness checks already registered. | Stop any publication claim that relies on excluded failures or unsupported physical guarantees. |
| 27–30 | Reproducibility package and scientific reassessment. | Proceed toward submission only with both a new defensible formal contribution and meaningful robotics evidence, regardless of whether mean performance improves. |

This leaves little slack for discovering the theory after implementation starts.
Without an independently verified replacement for the rejected theorem claim,
the schedule is not a recommendation to spend thirty days exploring until a
positive result appears.

## 12. Reproducibility of this investigation and handoff

The following are SHA-256 fingerprints of the public full texts actually
retrieved. Stable source links are given above. These hashes identify the reading
copies, not conference acceptance or mathematical correctness.

| Reading copy | SHA-256 |
|---|---|
| LOGIV v3 | `2c13b0e20959a1cb0236db607d4cc424fb60c307b0175f9d66989c9ac481670f` |
| MAGMA-GEN v1 | `c797638ab3a0de937ede2ca701c1a6fb8a60b8f3f76dff31e4bd8b98fdc54345` |
| Audit Before You Commit v1 | `a1b73f4641b3fd0d6fed156b9fa9505fcec0a21d24140b5ade05386f714ae3c0` |
| DA-GRD v1 | `d4385d27496f0a57764e216fd61726b191bdee61b94425fcf0dc8074cbb06378` |
| AAAI 2024 epistemic-doxastic planning | `3ed7ce8b197d3b02526137376ce8d6d1603921747a661aafe2aeb7b9bfc242d6` |
| ICAPS 2023 justified perspectives | `35d6872e1e024ebb429a35cfa88c6401da3dcf942b452f0a6b056ce86682a7cc` |
| INPROVF preprint | `09aeb42ba895b87c40ad89e030edc56eb04ba01b84f5f8cd8d3137f98b1f5140` |
| ARE author camera-ready | `6245ef368d0daebdde3339b8f207a8b33dcf1952616558622033632cb843a91a` |
| PODS 1999 consistent answers | `eb9cd5be17339466d8e99f3c7a0da6aa26da3e71150a2424bf7efebe465e6b82` |
| IJCAI 2013 inconsistency-aware KABs | `63b6f3984c22d1670cb23f0c9848761a1d5d46297d86893edaeadee0efe81dc8` |
| IJCAI 2015 generalized KABs | `17fa8b3b0819c4441287a783d0236ab4db1ff3d28be10bf390819a7f9ed592dd` |
| AAAI 2014 preferred repairs, extended | `63e679f2737990f7704138af2ef6b2430fe3c53fab5c625e3403de68ebe7ea24` |
| AAAI 2021 hitting-set reconciliation | `2f21d863e0883d1ddef9493b272e345c3a157cc20a2d910a715c31808eb3a45a` |
| Compositional shields 2025 v1 | `06a77ec7ceb138473d25f1c9437e4f60237134dfe364f1a262649c8843061105` |

Access limitations are retained: Reiter university PDF 401; initial ARE OpenReview
PDF 403 but author camera-ready accessible; AAAI HTML blocked but PDFs accessible;
IEEE HTML bot checks but publisher-deposited metadata accessible; old RoboFail
data URL 403 with an alternate link not verified. No private access or credentials
were requested. No result depends on an inaccessible full text being assumed read.

Only document-level validation and preservation checks are appropriate to this
report-only change. The previous 29-test result belongs to the terminated
experimental session; it is not presented as a new research validation result.

The initial inventory was recorded at **07:37:17 UTC on 11 November 2026**.
At **08:19:45 UTC**, SHA-256 rechecking verified **407/407 unchanged files**,
42.47 minutes after that start. This is within the three-hour ceiling; no
additional research time is reserved or consumed to fill the budget. Resources
were literature retrieval, targeted reading, metadata/source inspection, and the
single import-only artifact check described above. No experimental GPU work,
training or simulator execution was launched.

The preserved overnight seal at
`results/overnight-20261111/20261110T235337Z/completion_manifest.json` retains
SHA-256 `942341dc6273dc31ac84bf8771aabc01ee17f6dea81b465e7961467b6c72b5ce`.
Only this report is added to the research branch. Final validation checks its
required sections, links, code fences and whitespace, and repeats preservation
verification before the local commit. Publication is left to the user.

**Final recommendation: NO-GO.** Preserve the terminated project's evidence and
this rejection analysis. Independent review may identify a different precise
question or a genuinely new theorem; it must do so before a new method or
experimental campaign starts. There is no surviving recommended contribution,
no implementation authorization, and no claim of publication-level novelty.
