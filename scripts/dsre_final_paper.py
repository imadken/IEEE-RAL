"""Synchronized measured full manuscript and concise RSS Stage1 derivative."""

import argparse
import re
from pathlib import Path

from dsre_final_report import row
from dsre_followup_batch import read


def interval(value):
    if value is None:
        return "not estimable"
    lo, hi = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} pp (paired95\\% CI $[{100 * lo:.2f},{100 * hi:.2f}]$)"


def section(text, start, end, replacement):
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + replacement + "\n\n" + text[b:]


def clean(text):
    # Insert ordinary prose spaces without touching TeX commands or identifiers.
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def write(root):
    assert not (root / "completion_manifest.json").exists()
    r = read(root / "operational_results.json")
    tab = r["tables"]
    audit = read(root / "independent_audit.json")
    assert audit["status"] == "PASS"
    p = row(tab, "PickCube-v1")
    q = row(tab, "PushCube-v1")
    ps = row(tab, "PickCube-v1", "DSRE_strict")
    qs = row(tab, "PushCube-v1", "DSRE_strict")
    selected = audit["heldout"]["selected_executions"]
    cal = read(root / "calibration_decision.json")
    effects = r["paired_intervals"]
    robust = read(root / "heldout_robustness.json")
    delta = lambda task, other="DSRE_strict": interval(
        effects[f"{task}|DSRE_risk-{other}|all"]["successful"]
    )
    abstract = f"""\\begin{{abstract}}
An effective robot recovery action need not be justifiable from available observations. We formulate Decision-Sufficient Recovery Explanations (DSRE): minimum observable action facts or explicit observation, repertoire and reference-insufficiency witnesses, linked to measured paired interventions and an independent selective-risk gate. Established sufficient-rule and risk-control techniques supply the mathematical core. On a fixed two-task simulator reference, extra observation increases PickCube strict justification mostly by maintaining already-successful execution; strict PushCube always abstains despite high recovery success. After separate calibration on360parents and an explicitly excluded failed test attempt, a preregistered continuation completes{r["complete_parents"]}/159untouched parents with full-prefix paired execution and{selected}selected-action repeats. Gated strict versus risk-tier completion is{ps["successful"]} versus{p["successful"]}/{p["checkpoints"]}Pick checkpoints and{qs["successful"]} versus{q["successful"]}/{q["checkpoints"]}Push checkpoints. All{p["maintained_success"] - ps["maintained_success"]}extra Pick successes maintain already-successful starts;{q["required_recovery_success"]}Push successes require recovery. Ordinary rules are equivalent and strong trees/constant policies delimit any advantage. Fixed observation-corruption tests expose factual fragility without transferring clean risk guarantees. The study separates action quality, observable justification, recovery necessity and statistical eligibility; it establishes neither a new controller nor hardware safety.
\\end{{abstract}}"""
    # Prose spacing is explicit below; generated numbers are never placeholders.
    abstract = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", abstract)
    intro = r"""\section{Introduction}
A robot deciding whether to continue or recover needs evidence about the consequences of both actions. A reliable recovery skill can still be unjustifiable from a particular observation: indistinguishable states may require opposing actions, neither action may work, or the reference may lack support. Conversely, a justified successful action need not represent a recovered failure when both skills work or the task is already successful.

We ask: \emph{When is an intervention justified by available observations, and what minimum evidence or insufficiency witness explains the decision?} DSRE's product is a scoped, checkable information contract: minimum action facts, distinct obstruction witnesses, independently qualified statistical eligibility, and explicit defer/stop. The mathematical tools are established sufficient rules and robust action intersection; the robotics question is their relationship to actual paired action adequacy and the downstream cost of abstention.

Table~\ref{tab:physical} grounds the problem in qualified manipulation states. We evaluate identical-information rules, decision trees and constants, with the same frozen risk standard. Independent calibration and a disclosed postmortem-qualified held-out continuation measure completion, maintained success and required recovery separately. Physical selected resets check the counterfactual estimator; input corruption tests its observation assumptions. The result is a systems characterization of intervention justification, not a claim that renaming an ordinary rule improves a controller.

"""
    design = r"""\section{Registered Design and Independent Execution}
We test H1 (selective strict information sufficiency), H2 (justified completion versus required recovery), H3 (finite purity versus independent risk eligibility) and H4 (epistemic fragility under imperfect observations). Negative or equal ordinary-baseline results are valid outcomes.
\subsection{Fixed reference and interventions}
The development reference has844qualified paired checkpoints (422/task,211seed parents/task) after76exclusions from920candidates. Both conditions of each parent stay together. Pick uses nominal/2-cm offset; Push nominal/misaligned. Unchanged scripted continue/recover skills run70controls/3.5s with terminal task success. Pick recovery performs staged regrasp; Push recovery lifts/repositions behind the object before pushing. No model, controller or threshold is trained here. The common runtime vocabulary has six facts and the fixed optional Pick left-of-goal predicate; all12facts are used only by the labeled upper-information control. Simulator poses/proprioception are idealized observations, not validated vision.

The six facts test object--goal distance$\le.03$m; hand--object distance$\le.04$m; goal-distance reduction and object displacement$\ge.005$m; summed absolute finger positions$\le.04$m; and hand height above object$>.03$m. Pick's added fact tests object.x$-$goal.x$<-.02$m. Earlier prefix observations supply progress/displacement. Privileged contact/grasp and future fields never enter routing.

\subsection{Qualification and disclosed exclusion}
Separate180-parent/task calibration was completed before the original test. The first Pick test parent failed a selected-prefix guard: JSON contacts are lists, live contacts tuples. That inspected parent is permanently excluded, never repeated or replaced. The new protocol freezes exactly79Pick and80Push untouched parents, both original conditions; it is a disclosed deviation from planned160, not160pristine trials.

Only three representation comparisons are normalized with existing JSON conversion; numeric/contact/time/success, model, source and memory guards remain strict. Before fresh test collection, four inspected calibration states replay both actions frame-by-frame against original branches and independently check the repaired selected executor. Mutation tests preserve rejection of real contact/state/memory/model/source/terminal errors. Native snapshots are unused.

Every new paired branch uses seeded reset plus full canonical action prefix. A sealed outcome-free packet fixes all17proposals and gates before an additional selected-primary reset execution, or records STOP without another continuation. Every selected prefix and future frame is independently checked, including controller/model identity and action equations. Repeated executions share their parent and do not create independent N or a standalone closed-loop deployment. Both conditions must complete for primary inclusion; partial cells remain secondary. No source/qualification failure is silently resumed.

\subsection{Frozen comparisons and estimands}
Strict DSRE/B7, pure one-/two-literal rules, greedy rules, four-outcome CART depths1/2 at strict/.9purity, fixed10-parent support-pruned CART2, B5 at empirical error$.10$, constants and policy-faithful tree-label explanations remain fixed. Risk-tier DSRE is strict first, otherwise the existing capped two-literal$.10$rule; its ordinary wrapper is identical. All formal gates retain the same original17-method/task/action confidence budget. No new calibration, fit or test-label tuning occurs.

Abstention scores zero autonomous-completion credit, even for already-successful checkpoints. This is an explicit autonomy metric, not a physical claim that stopping destroys task success. Conditional success among actions, inadequate choices and all-start completion are separate. Initially unsuccessful means task success false at the checkpoint, not an independently annotated failure event. Required recovery means successful recover from an initially unsuccessful recover-only state relative to these two skills/horizon. All four paired categories and both original conditions are reported.

The primary contrast is gated risk-tier minus gated strict completion; strong ordinary controls share the same information and gates. We use4000paired seed-parent percentile bootstrap draws, both conditions together, PCG64 seed2026111401 for Pick and2026111402 for Push. Subgroup ratios resample all task parents. Zero-variation intervals and zero observed errors are not population safety bounds. Calibration bounds are unchanged and assume independent seed parents in the declared scope.

"""
    history = r"""\section{Preserved Information-Sufficiency Evidence}
The full-reference finite ceiling and out-of-sample success are different estimands (Fig.~\ref{fig:frontier}). Pick actionable masses are183,235,237,238/422at budgets0--3and248with all six optional facts; Push stays zero. Grouped exploratory Pick cross-fitting changes strict successes202to242/422at one extra fact, but inadequate choices1to2and initially unsuccessful successes19to18/145. B7 matches16,880views. Extra observations do not guarantee better held-out decisions.

The separately preregistered333-parent follow-up remains intact: Pick strict145to187/332, +12.65pp, paired95\% interval$[9.33,16.27]$; zero observed strict errors. Initially unsuccessful successes16to18/109yield only one extra required recovery, with an interval including zero. Forty of42additions maintain already-successful execution. Strict CART2/capped rules differ once; B7 is exact. Provisional CART achieves240/332and exceeds strict187under a different purity standard. Push strict0/334versus fixed recover334/334shows skill success without strict justification. The earlier interrupted33parents/task and orphan remain separate; no inspected historical outcomes enter new calibration.

"""
    new = results_section(root, r, tab, audit, cal, delta)
    observation = observation_section(root, robust)
    discussion = r"""\section{Discussion and Scientific Boundaries}
Skill success, finite-reference justification, statistical eligibility and action necessity answer different questions. The measured primary operating points count STOP explicitly; maintenance cannot be interpreted as a newly recovered failure. An effectively constant Push recover policy is also an ordinary always-recover result. B7 and the capped-risk wrapper retain exact identity, while CART can match or exceed DSRE. The contribution is the executable robot-intervention contract and its measured consequences, not new pure-rule, hitting-set, partial-observability or calibration theory.

Our bounds assume the declared independent seed-parent distribution, two conditions, fixed skills/horizon and clean observations; grouping prevents condition pseudoreplication but does not prove distributional independence. Rare Pick recovery remains unqualified. Clean calibration cannot certify noisy/stale packets, arbitrary time points or hardware. The offline corruption study changes routing observations only, not controller feedback. Retrospective false facts are not an online sensor-health detector. Literal/byte costs are not physical sensing latency or energy.

Two simple scripted tasks, idealized poses, deterministic branching and horizon-specific binary utility limit generality. Source-qualified reset repeats do not establish real-hardware or stochastic closed-loop recovery benefit. The optional third-task gate supplies no favorable replacement benchmark. Remaining work is independently qualified task breadth, realistic observed predicates and fixed rare-action calibration cohorts, with equal-information ordinary controls. Formal paper completeness is separate from RSS significance and acceptance.

"""
    full = (root / "starting_files/rss2027/dsre_full_paper_master.tex").read_text()
    full = section(full, r"\begin{abstract}", r"\section{Introduction}", abstract)
    full = section(full, r"\section{Introduction}", r"\section{Related Work", intro)
    full = section(
        full,
        r"\section{Hypotheses and Evaluation}",
        r"\section{Results and Their Boundaries}",
        design,
    )
    full = section(
        full,
        r"\section{Results and Their Boundaries}",
        r"\section{Calibration, Test Halt and Exploratory Comparisons}",
        history,
    )
    full = section(
        full,
        r"\section{Calibration, Test Halt and Exploratory Comparisons}",
        r"\section{Discussion",
        new + observation,
    )
    full = section(full, r"\section{Discussion", r"\clearpage", discussion)
    full = readable(full)
    Path("rss2027/dsre_full_paper_master.tex").write_text(clean(full))
    stage = (root / "starting_files/rss2027/dsre_stage1.tex").read_text()
    stage = section(stage, r"\begin{abstract}", r"\section{Introduction}", abstract)
    stage = section(stage, r"\section{Introduction}", r"\section{Related Work", intro)
    a = stage.index(r"\begin{figure*}")
    b = stage.index(r"\section{Operational Protocol", a)
    stage = stage[:a] + stage[b:]
    stage = section(
        stage,
        r"\section{Operational Protocol",
        r"\section{Calibration, Test Halt",
        short_design(design) + history,
    )
    stage = stage.replace(r"Fig.~\ref{fig:frontier}", r"Table~\ref{tab:budget}")
    anchor = stage.index(r"\section{Registered Design and Independent Execution}")
    stage = stage[:anchor] + budget_table() + stage[anchor:]
    stage = section(
        stage,
        r"\section{Calibration, Test Halt",
        r"\section{Discussion",
        new + short_observation(robust),
    )
    stage = section(stage, r"\section{Discussion", r"\clearpage", short_discussion())
    label = stage.index(r"\label{tab:primarydecomp}")
    a = stage.rfind(r"\begin{table*}", 0, label)
    b = stage.index(r"\end{table*}", label) + len(r"\end{table*}")
    block = (
        stage[a:b]
        .replace(r"\begin{table*}", r"\begin{table}")
        .replace(r"\end{table*}", r"\end{table}")
        .replace("{lrrrrr}", "{lrrrr}")
    )
    counts = []
    for task, name in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        value = "/".join(
            str(row(tab, task, pop=pop)["checkpoints"])
            for pop in ("continue_only", "recover_only", "both", "neither")
        )
        counts.append(f"{name} {value}")
        block = block.replace(f"{name} & {value} &", f"{name} &")
    block = block.replace("Task & C-only/R-only/both/neither &", "Task &")
    cap_a = block.index(r"\caption{")
    cap_b = block.index("\n", cap_a)
    block = (
        block[:cap_a]
        + r"\caption{Primary gated completions: maintained continue (C-maint), required recover (R-req), other good, and bad/STOP. True C-only/R-only/both/neither counts: "
        + "; ".join(counts)
        + ".}"
        + block[cap_b:]
    )
    stage = stage[:a] + block + stage[b:]
    label = stage.index(r"\label{fig:final_operational}")
    a = stage.rfind(r"\begin{figure*}", 0, label)
    b = stage.index(r"\end{figure*}", label) + len(r"\end{figure*}")
    figure = stage[a:b]
    stage = stage[:a] + stage[b:]
    where = stage.index(r"\section{Registered Design and Independent Execution}")
    stage = stage[:where] + figure + "\n\n" + stage[where:]
    Path("rss2027/dsre_stage1.tex").write_text(clean(readable(stage)))
    print(
        {"manuscripts_updated": True, "new_untouched_parents": r["complete_parents"]},
        flush=True,
    )


def readable(text):
    parts = re.split(r"(\\(?:cite|ref|label)\{[^}]*\})", text)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", parts[i])
        parts[i] = re.sub(r"\b([BbFH]) ([0-9])\b", r"\1\2", parts[i])
        parts[i] = (
            parts[i]
            .replace(r"\usepackage[T 1]{fontenc}", r"\usepackage[T1]{fontenc}")
            .replace("CART 2", "CART2")
            .replace("CART 1", "CART1")
        )
    return "".join(parts)


def results_section(root, r, tab, audit, cal, delta):
    text = f"""\\section{{Independent Calibration and Held-out Outcomes}}
The continuation completed{r["complete_parents"]}/{r["planned_parents"]}untouched parents and{r["checkpoints"]}primary checkpoints after excluding the already attempted parent. The old0/160halt and its raw evidence are preserved; no contaminated observation becomes primary or is replaced. Table~\\ref{{tab:calibration}} retains the original independent calibration. Both enabled primary strata have one erroneous assigned parent among180, simultaneous upper5.194\\%; rare Pick recover remains NOT CERTIFIED. Empty Push continue is also unqualified.

\\begin{{table}}[t]
\\caption{{Unchanged primary calibration: assigned/error parents and simultaneous upper error bound. NC=NOT CERTIFIED; family delta=.05/68.}}
\\label{{tab:calibration}}\\centering
\\begin{{tabular}}{{llrrl}}\\toprule
Task & Action & Parents/errors & Upper & Gate\\\\\\midrule
"""
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for action, short in (("continue", "C"), ("recover", "R")):
            b = cal["strata"][f"DSRE_risk|{task}|{action}"]
            text += (
                f"{label} & {short} & {b['assigned_parents']}/{b['error_parents']} & {100 * b['upper']:.2f}\\% & {'on' if b['enabled'] else 'NC'}"
                + r"\\"
                + "\n"
            )
    text += r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    text += r"""\begin{table}[t]
\caption{New held-out outcomes under identical global gates: successful/inadequate/STOP checkpoints. Same information and calibration standard; unqualified constant proposals are reported separately.}
\label{tab:final_operational}\centering
\begin{tabular}{lrr}\toprule
Method & Pick & Push\\\midrule
"""
    for method, label in (
        ("DSRE_strict", "Strict DSRE"),
        ("DSRE_risk", "Risk tier"),
        ("B7_risk", "Ordinary risk"),
        ("CART1_beta10", "CART1 .9"),
        ("CART2_beta10", "CART2 .9"),
        ("B5_beta10", "B5 .10"),
        ("B0_continue", "Always continue"),
        ("B0_recover", "Always recover"),
    ):
        a, b = row(tab, "PickCube-v1", method), row(tab, "PushCube-v1", method)
        text += (
            f"{label} & {a['successful']}/{a['unacceptable']}/{a['deferred']} & {b['successful']}/{b['unacceptable']}/{b['deferred']}"
            + r"\\"
            + "\n"
        )
    text += r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    records = read(root / "test_records.json")
    text += r"""\begin{table*}[t]
\caption{Actual paired outcome classes C-only/R-only/both/neither and the primary gated completion partition. C-maint=successful continue from an initially successful start; R-req=successful recover from an initially unsuccessful recover-only start. Other=remaining successful choices.}
\label{tab:primarydecomp}\centering
\begin{tabular}{lrrrrr}\toprule
Task & C-only/R-only/both/neither & C-maint & R-req & Other good & Bad/STOP\\\midrule
"""
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        a = row(tab, task)
        rs = [
            v
            for v in records
            if v["task"] == task
            and v["method"] == "DSRE_risk"
            and v["mode"] == "calibrated"
        ]
        counts = "/".join(
            str(row(tab, task, pop=pop)["checkpoints"])
            for pop in ("continue_only", "recover_only", "both", "neither")
        )
        cm = sum(
            v["successful"] and v["initial_success"] and v["action"] == "continue"
            for v in rs
        )
        rr = a["required_recovery_success"]
        other = a["successful"] - cm - rr
        text += (
            f"{label} & {counts} & {cm} & {rr} & {other} & {a['unacceptable']}/{a['deferred']}"
            + r"\\"
            + "\n"
        )
    text += r"\bottomrule\end{tabular}\end{table*}" + "\n\n"
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        a = row(tab, task)
        s = row(tab, task, "DSRE_strict")
        tree = row(tab, task, "CART2_beta10")
        rec = a["recommended"]
        conditional = f"{a['successful']}/{rec}" if rec else "not estimable"
        text += f"{label} risk-tier minus strict autonomous completion is {delta(task)}; versus CART2$.9$ it is {delta(task, 'CART2_beta10')}. Conditional success among primary recommendations is {conditional}, distinct from {a['successful']}/{a['checkpoints']} all-start completion credit. The risk-minus-strict gain changes maintained successes by {a['maintained_success'] - s['maintained_success']:+d} and required recoveries by {a['required_recovery_success'] - s['required_recovery_success']:+d}. CART2$.9$ yields {tree['successful']} completions under the same gate.\n\n"
    text += (
        r"The ordinary risk wrapper is identical to DSRE's risk tier. Constant recover and ordinary controls on Push must accompany its result; a risk-qualified action need not require query-specific facts or improve a physical skill. Pick recovery is disabled by its original calibration even if held-out proposals happen to succeed. No test observation updates this decision. Ungated proposal counts, per-condition/category tables, assignment/error parent counts, regret and paired strong-control intervals remain separate."
        + "\n\n"
    )
    proof = audit["heldout"]
    text += f"New selected resets execute {proof['selected_executions']} continuations and record {proof['deferred_checkpoints']} STOP decisions, with {proof['selected_disagreements']} selected-future disagreements. The independent verifier checks {proof['selected_prefix_states']} selected prefix states and {proof['selected_future_states']} future states, plus all {proof['raw']['qualified_traces']} paired traces. Every original action equation, controller/model/source and contact-inclusive state remains checked. These repeats validate the within-scope deterministic estimator; they do not increase parent N.\n\n"
    text += r"""\begin{figure*}[t]
\centering\includegraphics[width=\textwidth]{figures/final_operational.png}
\caption{New untouched continuation under unchanged calibration, with STOP contributing zero autonomous credit. Colors distinguish maintained success, truly required recovery and other initially unsuccessful completions; inadequate actions remain visible. Ordinary rules, CART and constants receive the same information/risk standard. This is paired counterfactual evaluation with separately checked selected repeats, not a new controller or independent closed-loop deployment.}
\label{fig:final_operational}
\end{figure*}

"""
    return text


def observation_section(root, robust):
    cases = read(root / "physical_examples.json")["cases"]
    f = next(c for c in cases if c["case"] == "F")
    text = r"""\subsection{Reference witnesses and their limitations}
The qualified physical cases in Table~\ref{tab:physical} retain their source-verified coordinates, facts and paired outcomes. A/B share six facts but differ in the registered signed-x fact; A's minimum recovery rule has three facts and five reference parents, while B remains inadequate. C demonstrates both-success adequacy without necessity. D/E require opposing actions despite matching all twelve declared facts. Raw poses differ; this is a finite vocabulary limit, not a no-sensor theorem.

"""
    text += f"An additional full-twelve-fact reference case has only {f['diagnosis']['independent_parents']} compatible independent parent and both actions fail; the separate verifier confirms overlapping reference-support and repertoire obstructions. Another preserved cross-fit case has zero exact-signature support, yet a supported broader pure rule selects continue where measured continue fails and recover succeeds. That case is not mislabeled an emitted reference-insufficiency obstruction: finite support diagnostics do not detect every unrepresented adverse state.\n\n"
    text += r"""\subsection{Registered observation sensitivity}
The same twelve input scenarios are evaluated separately on the inspected333-parent cohort and new held-out continuation: missing selected facts/history/pose, Gaussian1/5mm noise with three fixed replicates each,50/250ms actual prefix-pose delays and clean input. Identical corrupted packets are shared by methods; actual paired physical labels never change. UNKNOWN cannot be asserted as a false literal. Noise repetitions are averaged within parent before4000bootstrap draws; conditions and repeats never inflate independent N. The fixed1-mm boundary-proximity subgroup and every grid point remain visible. These are offline shift-sensitivity estimates, not physical sensor deployment or transferred clean calibration.

"""
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for method, name in (
            ("DSRE_strict", "strict"),
            ("DSRE_risk", "risk proposal"),
            ("CART2_beta10", "CART2.9"),
        ):
            parts = []
            for scenario, title in (
                ("clean", "clean"),
                ("noise005", "5-mm noise"),
                ("delay5", "250-ms delay"),
            ):
                x = robust["parent_intervals"][
                    f"{task}|{method}|proposal|{scenario}|all"
                ]
                if "unacceptable" in x:
                    parts.append(f"{title} {100 * x['unacceptable']['value']:.2f}\\%")
            text += f"{label} {name} inadequate proposals: " + "; ".join(parts) + ". "
        text += "\n\n"
    fact_noise = robust["parent_intervals"][
        "PickCube-v1|DSRE_strict|proposal|noise005|all"
    ]["false_confidence"]["value"]
    fact_delay = robust["parent_intervals"][
        "PushCube-v1|CART2_beta10|proposal|delay5|all"
    ]["false_confidence"]["value"]
    text += f"Under 5-mm noise, {100 * fact_noise:.2f}\\% of Pick strict views propose an action using a fact contradicted by clean telemetry. Push CART's action stays unchanged under 250-ms delay even though {100 * fact_delay:.2f}\\% of its explanation views contain such a contradiction. Action stability therefore does not imply factual explanation fidelity.\n\n"
    text += r"""\begin{figure*}[t]
\centering\includegraphics[width=\textwidth]{figures/final_robustness.png}
\caption{Predeclared secondary input sensitivity on new held-out physical outcomes. Marked curves show successful proposals; dotted curves inadequate proposals. Noise averages all three registered replicates within each original parent. Parent uncertainty, factual contradictions, missingness and boundary subgroups are reported separately. Clean statistical eligibility does not certify corrupted observations.}
\label{fig:final_robustness}
\end{figure*}

Retrospective fact contradictions are not online pose-health detection. The unchanged router can accept a supplied stale/noisy Boolean fact while its finite rule remains mathematically correct. Actual input bytes/scalars and routing times are interface/computation costs, not sensor energy or acquisition latency. The read-only third-task source assessment does not turn Lift's nominal speed clip into a distinct recovery intervention; no new third-task recovery result is claimed.

"""
    return text


def short_design(design):
    return r"""\section{Registered Design and Independent Execution}
H1 tests selective information sufficiency; H2 completion versus required recovery; H3 finite purity versus independent risk eligibility; H4 imperfect-observation fragility. Negative/equal ordinary comparisons are valid.

The fixed844-checkpoint reference has422/task and211parents/task. Pick nominal/2-cm offset and Push nominal/misaligned conditions retain both70-control/3.5-s skills and terminal success. Pick recovery is staged regrasp; Push lifts/repositions before pushing. No controller, reference, model or threshold is learned here. Six pose/proprioception facts test object--goal$\le.03$m, hand--object$\le.04$m, progress/displacement$\ge.005$m, summed absolute finger positions$\le.04$m and hand height$>.03$m; the added Pick fact is object.x$-$goal.x$<-.02$m. These are idealized simulator observations, not validated perception.

Independent calibration uses180parents/task and parent-any-error over both conditions. The primary existing router is strict first, otherwise a two-literal empirical$.10$rule. All17fixed methods share global$\delta=.05/(4\cdot17)$and target$\le10\%$:69zero-error assignments are required, versus42in the nonenabling four-stratum diagnostic. Rare/empty actions remain NOT CERTIFIED. With $k$ erroneous assigned parents among $n$, use the one-sided exact binomial bound~\cite{clopper1934}:
\begin{equation}
 U=\begin{cases}1,&n=0\text{ or }k=n,\\
 B^{-1}_{k+1,n-k}(1-\delta),&\text{otherwise},\end{cases}
\end{equation}
where $B_{u,v}$ is the Beta CDF; enable the proposed action only when $U\le .10$. Models, support/ties, predicates, actions and tree nodes are fixed; test labels never update gates. All common methods see6/7facts; only full-signature uses12. Constants, pure/capped/greedy rules, CART1/2strict/.9, support-pruned CART2, B5$.10$and policy-label explanations remain controls.

The first original test parent failed a contact-list/tuple guard. It is preserved/excluded, never rerun or replaced. A separately frozen79Pick/80Push continuation is a disclosed deviation from planned160. Three JSON normalizations retain all physical/source checks. Before new outcomes, four inspected states replay both actions and the repaired selected executor independently checks every frame, memory/model, action equation and nonempty contact. Mutation tests still reject genuine changes; native snapshots are unused.

Each test checkpoint has two measured paired branches; its outcome-free packet seals all proposals/gates before an enabled selected-primary reset repeat, or STOP. Both conditions and selected checks must complete per parent. Selected repeats add no independent N and are not standalone closed-loop deployment. STOP scores zero autonomy credit even if initially successful; conditional action success is separate. Initial unsuccessful status is checkpoint task-success false, not annotated failure. Required recovery means initially unsuccessful, recover-only and successful recover. Primary/strong-control effects use4000paired parent draws, both conditions together, seed2026111401+taskindex; subgroup ratios retain all task parents. Bounds assume the declared independent seed distribution, not arbitrary-time or shifted-input safety.

"""


def budget_table():
    finite = read(
        Path("results/dsre-rss2027/20261113T193554Z/reused_finite_ceiling.json")
    )
    tables = read(
        Path("results/dsre-rss2027/20261113T193554Z/reused_stratified_tables.json")
    )
    text = r"""\begin{table}[t]
\caption{Preserved Pick observation-budget result (N=422). Full-reference finite actionable mass differs from exploratory cross-fit successful/inadequate choices. Push strict remains zero at every budget.}
\label{tab:budget}\centering
\begin{tabular}{lrr}\toprule
Extra facts & Finite mass & Cross-fit good/bad\\\midrule
"""
    for b in range(4):
        a = tables[f"PickCube-v1|{b}|DSRE|all"]
        mass = finite[f"PickCube-v1|{b}"]["mass"]
        text += f"{b} & {mass} & {a['successful']}/{a['unacceptable']}" + r"\\" + "\n"
    return text + r"\bottomrule\end{tabular}\end{table}" + "\n\n"


def short_observation(robust):
    text = r"\subsection{Observation and reference limits}" + "\n"
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        parts = []
        for scenario, title in (
            ("clean", "clean"),
            ("noise005", "5-mm noise"),
            ("delay5", "250-ms delay"),
        ):
            x = robust["parent_intervals"][
                f"{task}|DSRE_strict|proposal|{scenario}|all"
            ]
            if "unacceptable" in x:
                parts.append(f"{title}: {100 * x['unacceptable']['value']:.2f}\\%")
        text += f"{label} strict inadequate proposals: " + "; ".join(parts) + ". "
    contradicted = robust["parent_intervals"][
        "PickCube-v1|DSRE_strict|proposal|noise005|all"
    ]["false_confidence"]["value"]
    text += f"At 5-mm noise, {100 * contradicted:.2f}\\% of Pick strict views use a contradicted fact. "
    return (
        text
        + r"These are offline corruption of the same measured outcomes, not sensor deployment or clean-calibration transfer. UNKNOWN is not false; retrospective contradicted facts are not online fault detection. A verified full12-fact case has one compatible parent and neither action adequate; support/repertoire obstructions overlap. A preserved unseen cross-fit signature admits an inadequate broader pure rule, limiting finite support diagnostics. Source assessment yields no qualified distinct third recovery task."
        + "\n\n"
    )


def short_discussion():
    return r"""\section{Discussion and Limits}
DSRE connects minimum observable action evidence, explicit insufficiency, independent statistical eligibility and the autonomy cost of abstention. Exact B7/ordinary-risk identity and strong CART/constant controls delimit superiority. More completion credit can be maintenance rather than required recovery; STOP's zero credit is prescribed, not evidence it physically destroys success.

Limits are two simple scripted simulator tasks, idealized poses, deterministic horizon-specific adequacy, rare unqualified actions and absent third-task breadth. Paired/selected resets are not independent trials or standalone closed-loop deployment. Clean parent-action risk is not arbitrary-time, shifted-sensor or hardware safety. The robotics contract is an empirically checked formulation using established mathematics; formal page compliance does not establish RSS significance or acceptance.

"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    write(parser.parse_args().root)
