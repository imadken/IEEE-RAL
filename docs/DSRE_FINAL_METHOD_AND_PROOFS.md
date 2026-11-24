# Final DSRE methodology and validity obligations

Authority: [final supervisor decision](DSRE_RSS2027_FINAL_SUPERVISOR_DECISION_20261118.md), design commit `eea75861cbf57013e3983dfbcf08e2a4252c2a54`. This document fixes the scientific interpretation; the machine-readable registration and source hashes are in `results/dsre-evidence-aware/20261118-final-science/registration.json`. No manuscript is revised.

## Scientific object

For a source-qualified predecision checkpoint, two **fixed** macros have binary terminal potential outcomes `(Yc,Yr)`. Define `qij=P(Yc=i,Yr=j | L)` on an independently calibrated, discovery-frozen observable cell `L`. Write `pc=q10+q11`, `pr=q01+q11`, harm `h=q10`, rescue `s=q01`, and expected binary completion gain `g=s-h=pr-pc`. The primary obligation is `h<=.10` **and** `g>=.05`. Harm-only `h<=.10` and absolute recover success `pr>=.90` are separate obligations. None implies useful recovery without the other primary constraint. These are population-average obligations within the declared region, not per-robot safety guarantees.

A certificate `C=(E,R,D,O,B,W)` records: minimum measured predecision facts `E`; the union of **whole** calibrated cells `R`; source evidence and assumptions `D`; the named obligation `O`; simultaneous uncertainty/identification bounds `B`; and deletion/insufficiency witnesses `W`. Abstention is default execution of unchanged continue, with a separately reportable deferral interpretation. A deferred checkpoint is not physically relabeled failure.

## Source semantics and sharp bounds

Randomized one-action logs expose `(X,A,Y_A,e=.5)` only. Independent parents, consistency of fixed macro execution, positivity, exchangeability supplied by assignment, stable observation/source population and supported predecision measurements are assumptions. A deterministic hash implements the registered assignment; its interpretation as fair randomization over independently generated simulator parents is explicit, not a theorem about arbitrary seeds. The learner never receives seed, condition, hidden contact/grasp labels or the unexecuted outcome as a feature.

Qualified paired simulator trials add a joint outcome under independently checked fresh-prefix/controller reconstruction. They are two outcome executions per parent; this model coupling is not a hardware counterfactual or a free deployed observation. An uncontrolled observational log cannot establish the registered causal claim without additional identification assumptions. Missing terminal outcomes stay missing; unsupported measurements stay UNKNOWN. A nonexistent decision checkpoint is source attrition, not `Y=0`.

**Classical binary sharp-bound derivation.** Nonnegativity gives `q11<=min(pc,pr)` and `q00=1-pc-pr+q11>=0`, hence `max(0,pc+pr-1)<=q11<=min(pc,pr)`. Since `h=pc-q11`,

`max(0,pc-pr)<=h<=min(pc,1-pr)`.

Every intermediate feasible `q11` constructs a compatible joint distribution, so the interval is sharp. Gain is point identified from randomized marginals even when harm is not. At exact marginals, the primary obligation is warranted for **all** compatible joints iff

`pr-pc>=.05 AND (pc<=.10 OR pr>=.90)`.

Necessity follows by taking the attainable maximal harm; sufficiency follows from the upper bound and the marginal gain identity. This is established partial-identification mathematics, not a new theorem.

**Constructive nonidentification.** `q=(.4,.2,0,.4)` and `(0,.6,.4,0)` both have `pc=.4,pr=.6,g=.2`; harm is respectively `0` and `.4`. Arbitrarily many identical randomized one-arm marginals cannot choose between them. Extra qualified joint trials can. The example is analytical; a physical empirical point estimate alone is not proof of a population paired-only region.

The source-aware production method independently enumerates vertices of the four-cell probability polytope. The supervisor HiGHS LP and analytical formulas are numerical oracles. With rectangular marginal intervals the exact conservative extrema are `H_U=min(Uc,1-Lr)`, `H_L=max(0,Lc-Ur)`, `G_L=Lr-Uc`, `G_U=Ur-Lc`, and recover failure `1-Lr`. Paired harm/rescue bands further intersect the feasible polytope. Inconsistent constraints or missing overlap fail closed.

## Finite-sample scope and confidence

Freeze a partition with `K<=4` on discovery parents before calibration. In each cell construct exact one-sided Clopper–Pearson marginal endpoints with tail `.025/(4K)`. A union bound over both endpoints of both arms and all K cells gives logged-family error at most `.025`. The existing paired evidence allowance is separately `.025`; do not spend it repeatedly across arbitrary alternatives. This campaign's regression comparator uses its own discovery-frozen two-region partition and the same per-method allocation. There is **no joint95 claim across methods, tasks, post hoc regimes, budgets or the exploratory insertion pilot**. Actual support and assignment counts are reported, including zero-support failure.

The primary action gate is `H_U<=.10 AND G_L>=.05`. Discovery structures/proposals are sealed before C; C bounds are sealed before any T execution. Untouched T supplies descriptive independent-parent outcome intervals and policy scoring, not policy tuning. Test harm intervals conditional on selected recoveries and whole-policy gain intervals have different denominators and meanings.

**Whole-cell scope lemma.** Let `R` be a union of whole frozen cells whose harm/gain constraints hold simultaneously. For any mixture over those complete cells, `h_R=sum(wL*hL)<=.10` and `g_R=sum(wL*gL)>=.05`. This requires preserving the within-cell distribution. It does not authorize selecting an arbitrary subcell, changing within-cell population, or conditioning on extra facts/test outcomes. Unsupported/unknown cells invalidate a certificate. The guarantee applies to the conditional population represented by `R`, not each individual.

**Why a subgroup claim is false.** A calibrated cell may contain a small subgroup with harm1 and a majority with harm0. Its average can satisfy `.10` while the selected subgroup violates it. The implementation rejects conjunctions that split any calibrated leaf; merely averaging the cell's bound over the selected subset would be unsound.

## Minimum facts and witnesses

Enumerate subsets of the actual measured query literals by increasing cardinality, then canonical vocabulary order. Retain only conjunctions matching the query and selecting nonempty unions of whole cells, all qualified. The first accepted set is cardinality minimal over this finite declared grammar because every smaller subset was examined. This is not minimum sensing cost, a globally shortest natural-language explanation, or a theorem beyond the grammar. Missing facts are not assigned Boolean values. Removing each selected literal produces either a leaf-splitting scope witness or newly admitted unqualified leaves. A witness of finite calibration uncertainty is distinguished from an intrinsic compatible-joint witness, source failure, opposing successful actions and both-action failure. Opposing unique-success outcomes within one measured signature obstruct a pointwise common-success requirement on that finite reference; they do not by themselves refute an average `.10/.05` obligation. Likewise, an individual both-failure parent is an action-capacity witness, not automatically a statistical impossibility result for its entire cell.

## Frozen comparisons and costs

Exact B7 rules use the same Boolean grammar, whole-cell scope and gate. Direct partial identification uses identical cells, evidence and thresholds. Their primary actions must coincide with DSRE; shorter representation is not a control-performance advantage. CART uses the same discovery tree with a discovery empirical-gain proposal and the same calibration gate. Ordinary outcome regression is per-arm ridge least squares (`lambda=1`, intercept unpenalized), clipped to `[0,1]`, trained on the same D records; its two prediction-gain regions are frozen on D and calibrated as whole regions, collapsing if a region has fewer than 8 discovery records in either arm. It does not inherit another leaf's guarantee on a narrower subset. Fixed C and R retain their actual benefit/harm without being advertised as qualified methods. Finite-cell literature adaptations are labeled adaptations, not faithful reproductions of published estimators.

Every learner has 128 discovery and1024 calibration one-action outcomes when complete; every deployed policy uses one selected test action. Alternate test outcomes are offline scoring with an additional256 actions, common to scoring all frozen policies. A hindsight paired oracle observes both outcomes and is only a completion ceiling at that extra cost. Historical paired-versus-log source budgets count actual observed actions, including independently acquired counterpart labels. Evidence frontier quantities—action capacity, signature commonality, source sufficiency, calibrated coverage—are separate, not an additive decomposition.

Insertion is exploratory source/action-diversity qualification only:48 registered parents, all native predecision planner aborts retained as no checkpoint; minimum32 checkpoints and two distinct parents for each opposing unique-success action before a separately registered96-parent confirmation. No aperture is invented, no failed seed replaced, no post-checkpoint failure excluded, and no formal risk/gain calibration claimed from this pilot. The old interrupted1024/256 cohort remains historical and incomplete.
