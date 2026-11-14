"""Synchronize the full master and compressed Stage 1 from audited measurements."""

import argparse
from pathlib import Path

from dsre_followup_batch import read


def ci(value):
    if value is None:
        return "not estimable"
    lo, hi = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} percentage points (paired 95\\% interval $[{100 * lo:.2f},{100 * hi:.2f}]$)"


def write(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Sealed evidence")
    results = read(root / "operational_results.json")
    halted = results["complete_parents"] == 0
    view = read(root / "exploratory_operational_results.json") if halted else results
    tab = view["tables"]
    calibration = (
        read(root / "calibration_decision.json")
        if (root / "calibration_decision.json").exists()
        else {"strata": {}}
    )
    robust = read(root / "observation_robustness.json")
    audit = read(root / "independent_audit.json")
    assert audit["status"] == "PASS"

    def row(task, method="DSRE_risk", mode="calibrated", pop="all"):
        return tab.get(
            f"{task}|{method}|{mode}|clean|{pop}",
            {
                "checkpoints": 0,
                "parents": 0,
                "recommended": 0,
                "successful": 0,
                "unacceptable": 0,
                "deferred": 0,
                "maintained_success": 0,
                "required_recovery_success": 0,
                "failed_start_success": 0,
            },
        )

    p, q = row("PickCube-v1"), row("PushCube-v1")
    ps, qs = row("PickCube-v1", "DSRE_strict"), row("PushCube-v1", "DSRE_strict")
    contrasts = view["paired_intervals"]
    test_parents = results["complete_parents"]
    cal_parents = results["calibration_parents"]

    def effect(task, other="DSRE_strict"):
        return ci(contrasts.get(f"{task}|DSRE_risk-{other}|all", {}).get("successful"))

    selected = audit["selected_execution"]
    abstract = f"""\\begin{{abstract}}
An effective recovery skill need not be justifiable from available observations, and a finite pure rule need not be statistically deployable. We formulate Decision-Sufficient Recovery Explanations (DSRE) as minimum observable action facts or constructive observation, repertoire and reference insufficiency witnesses. Established sufficient-rule and selective-risk principles provide the mathematical core; our contribution is a robot-intervention contract and its operational consequences. A preserved 333-parent prospective cohort confirmed a PickCube justification-coverage gain, mostly on already-successful starts, while strict PushCube routing always abstained. A separately preregistered study completed {cal_parents}/360 independent calibration and {test_parents}/160 disjoint test parents. All methods share a simultaneous task/action risk gate and an explicit stop on abstention. Gated PickCube completions are {ps["successful"]} versus {p["successful"]}/{p["checkpoints"]} for strict versus risk-tier routing; PushCube completions are {qs["successful"]} versus {q["successful"]}/{q["checkpoints"]}. Ordinary equal-information rules remain equivalent. Recorded observation-corruption tests expose the limits of factual certificates, while selected reset executions check the deterministic counterfactual estimator. Rare-action qualification, blocked third-task breadth and idealized poses limit the result; no new controller, algorithmic superiority or hardware recovery claim follows.
\\end{{abstract}}"""
    if halted:
        abstract = r"""\begin{abstract}
An effective recovery skill need not be justifiable from available observations, and a finite pure rule need not be statistically deployable. Decision-Sufficient Recovery Explanations (DSRE) provide minimum observable action facts or constructive observation, repertoire and reference-insufficiency witnesses. Established sufficient-rule and selective-risk principles supply the mathematical core. A preserved 333-parent prospective cohort confirmed a PickCube justification-coverage gain, mostly on already-successful starts, while strict PushCube routing always abstained. A separately preregistered operational study completed 360/360 independent calibration parents. Pick continue and Push recover each incurred one erroneous assigned parent in180; simultaneous upper error bounds are5.19\%, below the10\% target. Rare Pick recovery remains unqualified. The first selected-execution prefix check halted the new test at0/160 complete parents, so held-out operational effects are not estimable. We preserve that failure and report matched retrospective comparisons and a fixed offline corruption study separately. Ordinary rules remain equivalent; meaningful third-task recovery validation is blocked. The result characterizes intervention justification and its limits, without a new controller, algorithmic superiority or a completed operational validation claim.
\end{abstract}"""
    methods = r"""\section{Operational Protocol and Assurance}
We test four fixed hypotheses: H1, more observations can increase strict justification selectively; H2, increased justified coverage need not mean more required recoveries; H3, finite-reference purity differs from independently qualified statistical eligibility; H4, imperfect observations can change certificates, adequacy and deferral. These are tested propositions, not promised positive results.

\subsection{Unchanged reference and independent allocations}
The development reference contains844qualified paired checkpoints,422/task and211seed parents/task. Both conditions of each parent stay together. Frozen scripted continue/recover skills run70controls/3.5s, with terminal task success; no controller or model is trained here. Pick nominal/2-cm offset and Push nominal/misaligned conditions are unchanged. The primary predicates, in table order, are object--goal distance at most .03m, hand--object distance at most .04m, goal-distance reduction and object displacement each at least .005m, summed absolute finger positions at most .04m, and hand height above object greater than .03m; the development-selected extra Pick predicate tests object.x$-$goal.x$<-.02$ m. Push selects no extra predicate. All are summaries of simulator-supplied poses/proprioception, not validated visual perception or new physical sensors.

After inspecting the earlier interrupted33parents/task and completed333-parent follow-up, we separately preregistered180calibration and80disjoint test parents per task, with fixed unused chronological seeds and both conditions. The original development, preliminary and follow-up parents never enter new calibration. Models, support/ties, vocabulary, thresholds, actions and analysis are fixed before outcomes. No seeds are replaced or sampled until significance. Atomic completion requires both qualified conditions; missing/partial parents are enumerated rather than imputed.

\subsection{Finite justification versus statistical eligibility}
Abstention means defer/stop, contributing zero to autonomous completion. We separately measure success among actions, unacceptable choices, all-start completion, initially successful maintenance and initially unsuccessful recover-only completion. Initially unsuccessful means not yet task-successful at the checkpoint, not an independently annotated failure event. Regret relative to the best available action differs from inadequacy in neither-success states.

The risk candidate is the existing strict-then-provisional router: use strict DSRE if available, otherwise the ordinary two-literal rule with empirical error at most $.10$. Its B7-then-risk equivalent has the same decisions. Provisional evidence is not a strict universal certificate. Ordinary B5, four-outcome CART depths1/2 at purity1/.9, a fixed10-parent support pruning gate, pure one-/two-literal rules, greedy rules, constants and policy-faithful tree explanations are frozen controls. Only the full-signature upper-information comparison uses all12predicates; all common-budget methods use the same6/7facts.

For each method, task and assigned action, calibration counts independent seed parents. Any unacceptable assigned condition marks that parent erroneous. Exact one-sided Clopper--Pearson bounds~\cite{clopper1934} target assigned-parent any-error probability at most10\%, under the two registered conditions. All17methods and four task/action strata share Bonferroni $\delta=.05/(4\cdot17)$:69zero-error assignments are required, versus42for the four-stratum diagnostic at$.0125$. Only the stricter global gate enables actions. Empty/underpowered strata remain NOT CERTIFIED. This is not a checkpoint-weighted, arbitrary-time, noisy-input or hardware safety bound. Calibration is sealed before test and never updated from test labels.

\subsection{Qualified execution and observation stress}
Each paired branch starts from a seeded reset and full canonical action prefix. Every prefix state, model edit and controller custom memory must match; native snapshots are unused. On test, each enabled primary selected action receives an additional reset/prefix execution. The outcome-free input schema fixes its decision before that execution. This is a new repeat of a paired parent, not a new independent sample or falsely claimed separate closed-loop campaign. Source/replay or selected-future disagreement halts physics without repeated measurements.

The inspected333-parent follow-up supplies an offline twelve-scenario observation study: unavailable selected predicate, history or pose; Gaussian pose noise at1/5mm with three fixed replicates; and actual50/250ms prefix-pose delay, plus clean input. Common corrupted packets are shared across methods; original outcomes remain unchanged. UNKNOWN is never negation. The clean1-mm boundary-proximity subgroup, actual serialized bytes/scalars and computation time are recorded. Clean calibration does not transfer to corrupted observations; retrospective factual contradictions are not an online sensor-fault detector.

Primary test effects compare gated risk-tier versus gated strict completion, with4000paired seed-parent bootstrap draws, both conditions together. Subgroup ratios resample all task parents. All four outcome categories, initially successful/unsuccessful starts and strong comparator intervals are reported. Zero-variation intervals and zero observed errors do not establish zero population risk.

"""
    predictions = read(
        root
        / ("historical_operational_records.json" if halted else "test_records.json")
    )
    decomposition = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        selected_rows = [
            r
            for r in predictions
            if r["task"] == task
            and r["method"] == "DSRE_risk"
            and r["mode"] == "calibrated"
        ]
        cm = sum(
            r["successful"] and r["action"] == "continue" and r["initial_success"]
            for r in selected_rows
        )
        rr = sum(r["required_recovery_success"] for r in selected_rows)
        other = sum(r["successful"] for r in selected_rows) - cm - rr
        decomposition[task] = (cm, rr, other)
    new = f"""\\section{{Independent Operational Results}}
The study completed {cal_parents}/360 calibration and {test_parents}/160 test parents, with {p["checkpoints"]} Pick and {q["checkpoints"]} Push test checkpoints. Inclusion uses atomic complete parents only. The new estimator never pools inspected history into calibration or untouched test.

\\begin{{table}}[t]
\\caption{{Primary router calibration: assigned/error parents and simultaneous upper error bound. NC means NOT CERTIFIED. Scope is parent-action any-error across the two registered conditions.}}
\\label{{tab:calibration}}\\centering
\\begin{{tabular}}{{llrrl}}\\toprule
Task & Action & Parents/errors & Upper & Gate\\\\\\midrule
"""
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for action, short in (("continue", "C"), ("recover", "R")):
            b = calibration["strata"].get(
                f"DSRE_risk|{task}|{action}",
                {
                    "assigned_parents": 0,
                    "error_parents": 0,
                    "upper": 1.0,
                    "enabled": False,
                },
            )
            new += (
                f"{label} & {short} & {b['assigned_parents']}/{b['error_parents']} & {100 * b['upper']:.2f}\\% & {'on' if b['enabled'] else 'NC'}"
                + r"\\"
                + "\n"
            )
    new += r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    primary_table = r"""\begin{table}[t]
\caption{Primary gated completions: C-maint is successful continue from an initially successful start; R-req is successful required recover from an initially unsuccessful recover-only start. Other is remaining successful choices.}
\label{tab:primarydecomp}\centering
\begin{tabular}{lrrrr}\toprule
Task & C-maint & R-req & Other & Defer/bad\\\midrule
"""
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        a = row(task)
        cm, rr, other = decomposition[task]
        primary_table += (
            f"{label} & {cm} & {rr} & {other} & {a['deferred']}/{a['unacceptable']}"
            + r"\\"
            + "\n"
        )
    new += primary_table + r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    new += f"""Pick risk-tier minus strict autonomous completion is {effect("PickCube-v1")}; Push is {effect("PushCube-v1")}. Both are evaluated with the same global risk standard and stop semantics. Candidate purity and calibrated eligibility are different: a finite reference may contain an adverse compatible state while a sufficiently sampled distributional action stratum can pass its statistical target.

\\begin{{table}}[t]
\\caption{{Disjoint test under the identical global gate: successful / inadequate / deferred checkpoints.}}
\\label{{tab:operational}}\\centering
\\begin{{tabular}}{{lrr}}\\toprule
Method & Pick & Push\\\\\\midrule
"""
    for method, label in (
        ("DSRE_strict", "Strict"),
        ("DSRE_risk", "Risk tier"),
        ("B7_risk", "Ordinary risk"),
        ("CART2_beta10", "CART .9"),
        ("B5_beta10", "B5 .10"),
        ("B0_recover", "Always recover"),
    ):
        a, b = row("PickCube-v1", method), row("PushCube-v1", method)
        new += (
            f"{label} & {a['successful']}/{a['unacceptable']}/{a['deferred']} & {b['successful']}/{b['unacceptable']}/{b['deferred']}"
            + r"\\"
            + "\n"
        )
    new += r"\bottomrule\end{tabular}\end{table}" + "\n\n"
    new += f"""Of the primary Pick completions, {p["maintained_success"]} maintain an already-successful state and {p["failed_start_success"]} begin initially unsuccessful; {p["required_recovery_success"]} require recovery relative to the two skills. Push has {q["maintained_success"]} maintenance completions and {q["required_recovery_success"]} required recoveries. These counts must accompany all-start coverage. A statistical gate may defer a finite-certified but rarely assigned recovery. No rare stratum inherits qualification from the frequent action.

The ordinary risk wrapper remains identical to DSRE's risk mode. Strong CART and B5 results in Table~\\ref{{tab:operational}} are equally important; all methods receive identical calibration information and error budgets. A match or superiority of an ordinary comparator constrains method novelty. Policy-faithful explanations concern their frozen tree label, while the separate adequacy measurement can still reject that action. All condition/category and proposed-versus-gated comparisons remain distinct.

\\begin{{figure*}}[t]
\\centering\\includegraphics[width=\\textwidth]{{figures/operational.png}}
\\caption{{New disjoint test under globally matched statistical gates. Deferral is explicit zero autonomous completion. Maintained success, required recovery and other initially unsuccessful completion are different outcomes; initially unsuccessful does not imply an annotated failure event. Ordinary B7 risk is equivalent. No gain is attributed to a new controller.}}
\\label{{fig:operational}}
\\end{{figure*}}

New selected executions number {selected["new_selected_action_continuations"]}, with {selected["deferred_checkpoints"]} stopped checkpoints and {selected["future_trajectory_disagreements"]} selected-future disagreements. Independent action equations have maximum discrepancy {selected["maximum_action_error"]}. These repeats validate the deterministic outcome estimator within scope; they do not increase independent parent counts. Finite-reference, statistical and execution proof obligations are reported separately.

\\subsection{{Imperfect observation and external validity}}
The complete fixed corruption grid is an offline reanalysis of inspected inputs, not independent confirmation or an actual sensor deployment. Figure~\\ref{{fig:robustness}} reports proposed successful and inadequate actions; all three noise replicates are averaged without changing the independent parent count. Factual contradictions, action/certificate stability, unavailable observations and the boundary-proximity subgroup delimit what the explanation assumes. A supplied fact can be wrong or stale even when the exact rule is correct. Clean risk eligibility is not transferred to corrupted packets, and retrospective telemetry checks are not an online fault detector.

\\begin{{figure*}}[t]
\\centering\\includegraphics[width=\\textwidth]{{figures/observation_robustness.png}}
\\caption{{Fixed offline observation sensitivity on the inspected666-checkpoint follow-up. Marked curves show successful recommendations; dotted curves show inadequate actions. Noise points average three predeclared replicates; no additional independent parents or sensor hardware are claimed. Clean calibration is inapplicable under corruption. Full replicate and boundary results are reported separately.}}
\\label{{fig:robustness}}
\\end{{figure*}}

The preselected Lift/Panda arm failed a source-semantic prerequisite before new physics: its existing alternative only clips nominal lift speed, and the retained210starts have no failure or varying-adequacy contrast. No new controller, fault or favorable replacement task was developed. Consequently distinct third-task recovery validation remains absent. This is a material breadth limitation, not a positive transfer finding.

"""
    if halted:
        opening_end = new.index(r"\begin{table}")
        new = r"""\section{Calibration, Test Halt and Exploratory Comparisons}
The new study completed360/360 independent calibration parents but0/160 complete held-out test parents. Both primary enabled actions have one erroneous assigned parent among180; the simultaneous parent-any-error upper bound is5.194\%, versus3.492\% for the four-stratum diagnostic. Pick recovery has0/13 erroneous parents, upper42.594\%, and is NOT CERTIFIED; Push continue has no assignments. With no additional errors, Pick recovery would require at least56more independent assignments to reach the global zero-error minimum, not merely more nominal trials. No replenishment is performed.

The first Pick test parent fails the separate selected-prefix/controller/model guard. One qualified paired checkpoint is retained as secondary; its second condition is absent and159test parents remain untouched. No selected continuation executes. Held-out completion, action risk and paired effects are NOT ESTIMABLE, rather than zero. The frozen failure rule prohibits further physics, repeats or favorable seed replacement.

An offline software witness shows a sufficient guard defect: recorded JSON contact pairs are lists, whereas live pairs are tuples and the unchanged comparator uses direct equality. Reconstructing tuple contacts on the retained paired prefix falsely rejects90/91states despite identical other fields; JSON normalization passes. The failed live selected-prefix diagnostics were not persisted, so no claim that its other checks passed or physical parity held is possible. A normalization patch is retained for future qualification; no frozen source or measurement is amended here.

The following operational tables, decomposition and paired intervals apply the new frozen calibration gates retrospectively to the previously inspected333-parent follow-up (332Pick and334Push checkpoints). They are exploratory analysis of measured paired outcomes, not the missing new test, new policy rollouts or a replacement confirmation cohort. Calibration-cohort counts are separately descriptive because its errors selected the gates.

On the calibration cohort itself, gated Pick strict/risk-tier/CART$.9$ produce183/254/255successful choices out of360, with0/1/1inadequate actions; the ordinary tree thus exceeds the risk tier by one success in this descriptive comparison. Push risk, CART and always recover each give359/360successes and one inadequate action. These same-cohort counts do not supply an independent effect estimate.

""" + new[opening_end:]
        new = new.replace(
            "Primary gated completions:", "Exploratory historical gated completions:"
        )
        new = new.replace(
            "Pick risk-tier minus strict autonomous completion is",
            "On that inspected historical cohort, Pick risk-tier minus strict autonomous completion is",
        )
        new = new.replace(
            "Disjoint test under the identical global gate:",
            "Inspected historical follow-up under the new global gate (exploratory):",
        )
        new = new.replace(
            "New disjoint test under globally matched statistical gates.",
            "Inspected historical follow-up under newly calibrated gates; exploratory, not new test.",
        )
        start = new.index("New selected executions number")
        end = new.index(r"\subsection{Imperfect observation", start)
        new = (
            new[:start]
            + "No selected action was executed, so execution parity and its trajectory-error statistic are not assessable. The guard failure is retained as an engineering limitation, not evidence of physical nondeterminism.\n\n"
            + new[end:]
        )
    full = Path("rss2027/dsre_full_paper_master.tex").read_text()
    a = full.index(r"\begin{abstract}")
    b = full.index(r"\end{abstract}", a) + len(r"\end{abstract}")
    full = full[:a] + abstract + full[b:]
    a = min(
        full.index(h)
        for h in (
            r"\section{Independent Operational Study: Registered Status}",
            r"\section{Independent Operational Results}",
            r"\section{Calibration, Test Halt and Exploratory Comparisons}",
        )
        if h in full
    )
    b = full.index(r"\section{Discussion", a)
    import numpy as np

    times = {r["id"]: r["route_all_methods_ms"] for r in predictions}
    measured = np.asarray(list(times.values()))
    extra = ""
    if len(measured):
        extra = f"Recorded clean observation histories contain24scalar fields, averaging638.7bytes for Pick and620.2for Push in compact JSON. All17methods together take mean{measured.mean():.2f}ms, median{np.median(measured):.4f}ms, p95{np.percentile(measured, 95):.4f}ms and maximum{measured.max():.2f}ms per inspected checkpoint. Identical-query memoization makes these mixed cold/cached-call costs, not isolated method benchmarks or sensing/actuation latency. Boolean counts are representation cost, not sensor energy.\n\n"
    extra += (
        r"On the inspected Pick inputs, strict proposals have187good/0inadequate choices clean, mean218.3/1.7under5-mm noise and187/6under250-ms delay; CART$.9$ has mean239.3/1.0under that noise and224/16under delay. Strict noise certificates assert a clean-telemetry-contradicted fact in mean36.3proposals, versus34.0for CART. These are fixed-replicate averages, not additional independent samples or a superiority guarantee. Pose-corrupted inputs can increase apparent coverage while invalidating factual evidence; retrospective contradictions are not online detection."
        + "\n\n"
    )
    full = full[:a] + new + extra + full[b:]
    full = full.replace(
        "Anonymous Stage 1 research paper", "Anonymous full research manuscript"
    )
    a = full.index(r"\section{Discussion")
    b = full.index(r"\clearpage", a)
    full_discussion = r"""\section{Discussion and Remaining Scientific Boundaries}
Finite reference justification, measured action adequacy and independent statistical eligibility are different claims. Deferral has an explicit autonomy cost, and an adequate action need not be uniquely required. The operational comparison tests those consequences under identical information and error budgets. It does not create a new controller or make strict finite purity a population guarantee.

Exact B7 and the ordinary risk wrapper retain identical decisions and minimum facts. Selective classification and exact binomial risk control are established. Strong trees and constant policies may match or exceed a proposed operating point; all such comparisons remain in the same results. The candidate contribution is a robotics information contract and empirical characterization, not new pure-rule mathematics or calibration theory.

The parent-action confidence statement assumes independent seed-parent draws from the declared simulator distribution, two registered conditions, unchanged skills/horizon and a trustworthy clean observation interface. Grouping conditions prevents pseudoreplication; it does not prove distributional independence or transfer. Rare or absent actions remain unqualified; extra nominal continues cannot supply independent recovery assignments. The offline corruption experiment does not alter controller perception and cannot establish closed-loop sensor robustness. Retrospective factual diagnostics are not an online pose-health detector. No clean confidence bound transfers to noise, staleness or arbitrary checkpoints.

Two simple scripted tasks, idealized poses, deterministic branches, binary horizon-specific utility and the blocked Lift recovery contrast limit breadth. No real-hardware, human-interpretability or new sensor-cost claim is made. Remaining work requires a meaningful independently qualified third intervention, fixed independent rare-action cohorts and realistic observation validation, without inventing an algorithmic advantage. Formal manuscript completeness is separate from the significance judgment of RSS reviewers.

"""
    if halted:
        full_discussion = full_discussion.replace(
            "Finite reference justification,",
            "The new held-out operational study is incomplete and cannot establish an independently tested completion gain. The risk bounds are independent calibration results; retrospective operational estimates cannot repair the missing test. Finite reference justification,",
        )
    full = full[:a] + full_discussion + full[b:]
    # Current H4 concerns epistemic robustness; old held-out errors illustrate H3.
    full = full.replace(
        "\\textbf{H4}, held-out states can falsify extrapolation of finite-table sufficiency",
        "\\textbf{H4}, imperfect observations can change certificate validity and action adequacy",
    )
    full = full.replace("illustrating H4:", "illustrating the generalization boundary:")
    old = full.index("We test four fixed propositions:")
    end = full.index("\n\n", old)
    full = (
        full[:old]
        + r"We test four fixed propositions: \textbf{H1}, observation refinement increases strict justification selectively; \textbf{H2}, increased justified coverage need not increase required recoveries; \textbf{H3}, finite-reference purity differs from independent statistical risk eligibility; \textbf{H4}, imperfect observations can change factual certificates, adequacy and deferral. These are tested hypotheses, not promises of positive findings. No hypothesis requires beating the equivalent B7 rule."
        + full[end:]
    )
    full = full.replace("and repertoire boundary (H2)", "and the repertoire boundary")
    Path("rss2027/dsre_full_paper_master.tex").write_text(clean(full))
    # Compress the same scientific story; preserve the exact core and physical
    # cases, then replace the old evaluation narrative with current verified data.
    stage = Path(root / "starting_files/rss2027/dsre_stage1.tex").read_text()
    a = stage.index(r"\begin{abstract}")
    b = stage.index(r"\end{abstract}", a) + len(r"\end{abstract}")
    stage = stage[:a] + abstract + stage[b:]
    a = stage.index(r"\section{Hypotheses and Evaluation}")
    b = stage.index(r"\section{Discussion", a)
    history = r"""\subsection{Preserved independent evidence}
On844development checkpoints, Pick finite actionable mass rises183 to235/422with one optional predicate; all six yield248. Push remains zero, despite415/422successful fixed recoveries. Reused grouped Pick cross-fitting changes successful strict choices202 to242/422, but unacceptable choices1 to2; initially unsuccessful successes19 to18/145. B7 matches16,880registered views. These are inspected development results, not untouched calibration.

The preserved333-parent follow-up gives Pick145 to187/332strict successes, +12.65percentage points, paired95\% interval[9.33,16.27], with zero observed unacceptable choices. Initially unsuccessful starts improve16 to18/109, one extra required recovery; their interval includes zero. Forty of42additions maintain initially successful states. Strict CART2/cap2 differ once, while B7 is exact; provisional CART succeeds240/332. Push strict0/334versus recovery334/334 exposes justification versus skill success. The earlier interrupted33parents/task and orphan stay separate; SIGTERM cause is unknown. None of these inspected outcomes is used as new calibration.

"""
    # No sensitivity figure is dropped from the full master; the six-page version
    # states its measured limits and reserves space for the operational estimand.
    compressed_new = new[
        : new.index(r"\subsection{Imperfect observation and external validity}")
    ]
    obs = []
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for scenario, name in (
            ("clean", "clean"),
            ("noise005_r0", "5-mm noise"),
            ("delay5", "250-ms delay"),
            ("missing_pose", "unavailable pose"),
        ):
            names = (
                [scenario.replace("r0", f"r{i}") for i in range(3)]
                if scenario.startswith("noise")
                else [scenario]
            )
            rs = [
                robust["tables"][f"{task}|DSRE_strict|proposal|{s}|all"] for s in names
            ]
            good = sum(r["successful"] for r in rs) / len(rs)
            bad = sum(r["unacceptable"] for r in rs) / len(rs)
            obs.append(f"{label} {name}: {good:.1f}/{bad:.1f}")
    sensitivity = (
        "\\subsection{Observation limits and breadth}\nStrict good/inadequate counts under the fixed offline grid (noise averages three replicates) are "
        + "; ".join(obs)
        + ". These are inspected historical inputs, not sensor deployment or calibration transfer. Factual contradictions are retrospective telemetry diagnostics; the frozen router does not independently detect pose noise or staleness. UNKNOWN inputs follow the conservative unavailable-information path. Input bytes/scalars and Boolean counts are interface costs, not physical sensing latency or energy. The preselected Lift arm failed the distinct-recovery/varying-outcome source gate, so no third-task validation is claimed.\n\n"
    )
    stage = stage[:a] + methods + history + compressed_new + sensitivity + stage[b:]
    a = stage.index(r"\section{Discussion")
    b = stage.index(r"\clearpage", a)
    discussion = r"""\section{Discussion and Limits}
The contribution is an intervention-grounded information contract connecting minimum observable facts, explicit insufficiency and the cost of abstention, not new rule enumeration or calibration theory. Exact B7 equivalence and strong ordinary trees delimit any superiority claim. Statistical eligibility can differ from finite-reference purity, while rare actions can remain unsupported despite high all-start completion. Initial success maintenance and required recovery must be separated.

Limits are two scripted simulator tasks, deterministic horizon-specific outcomes, idealized pose observations and a blocked distinct third task. Parent-action confidence does not imply arbitrary checkpoint or hardware safety; corrupted inputs invalidate the clean calibration scope. No controller, human-interpretability benefit or physical recovery improvement is established. Strong RSS readiness depends on the significance of this bounded operational characterization, not formal page compliance.

"""
    stage = stage[:a] + discussion + stage[b:]
    # Exact method counts remain in the master table; Stage 1's plot and text
    # retain its matched comparators while avoiding a second redundant display.
    label = stage.index(r"\label{tab:operational}")
    start = stage.rfind(r"\begin{table}", 0, label)
    end = stage.index(r"\end{table}", label) + len(r"\end{table}")
    stage = stage[:start] + stage[end:]
    stage = stage.replace(
        r"Table~\ref{tab:operational}", r"Figure~\ref{fig:operational}"
    )
    stage = stage.replace(
        "The ordinary risk wrapper remains identical to DSRE's risk mode.",
        "On the inspected cohort, CART and the ordinary risk wrapper match the risk tier:224/332 Pick and334/334 Push successes, no inadequate choices; B5 and always recover defer all Pick and match Push. The ordinary risk wrapper remains identical to DSRE's risk mode.",
    )
    start = stage.index(r"\section{Introduction}")
    end = stage.index(r"\section{Decision-Sufficient Recovery Evidence}", start)
    stage = (
        stage[:start]
        + r"""\section{Introduction}
A manipulation action can succeed without being required, and a successful skill can lack observable justification. Explaining a policy label does not establish intervention adequacy. Table~\ref{tab:physical} illustrates these distinctions: Pick checkpoints share six facts but differ between recover-only and neither-success; Push checkpoints have opposing adequate actions despite identical declared signatures.

We ask what observable evidence suffices to justify a fixed recovery intervention relative to paired outcomes, and why justification fails. DSRE joins minimum action facts, constructive observation/repertoire/reference witnesses and explicit deferral. We evaluate downstream consequences against equally informed rules and trees. The contribution is this robotics contract and characterization, not a new sufficient-rule algorithm. Independent calibration, retrospective adequacy and the incomplete new test remain separate.

\section{Related Work and Scope}
Minimal sufficient MDP explanations already use reward/occupancy structure~\cite{khan2009}. Anchors and probabilistic sufficient explanations preserve model decisions~\cite{anchors,pse}; DSRE instead targets measured intervention adequacy. DISCRET synthesizes treatment-effect explanations~\cite{discret}; B5 is an adaptation, not its reproduction. Robust action intersections under partial observability already cover strict feasibility~\cite{partial}. We claim no new pure-rule, hitting-set or partial-observability theorem.

Robot recovery includes CAPE's precondition corrections~\cite{cape}, tree monitoring/recovery~\cite{peddi} and observed decision context~\cite{ernst}. DA-GRD uses physical sensing~\cite{dagrd}; our optional facts summarize existing simulated poses. RESCUE already evaluates counterfactual interventions~\cite{rescue}. The latter two are preprints. Selective classification establishes rejection and statistically controlled risk--coverage~\cite{selective2017}; our binomial gate uses that principle. The distinction is an executable intervention contract linking adequacy, insufficiency witnesses, statistical eligibility and measured completion loss, with exact ordinary-rule equivalence exposed.

"""
        + stage[end:]
    )
    # Introduce the full-width operational float early enough to share content
    # pages naturally; no template dimensions or negative spacing are changed.
    label = stage.index(r"\label{fig:operational}")
    start = stage.rfind(r"\begin{figure*}", 0, label)
    end = stage.index(r"\end{figure*}", label) + len(r"\end{figure*}")
    figure = stage[start:end]
    stage = stage[:start] + stage[end:]
    position = stage.index(r"\section{Operational Protocol and Assurance}")
    stage = stage[:position] + figure + "\n\n" + stage[position:]
    # The full master retains the historical frontier plot. Its measured counts
    # remain in the compressed history, while Stage 1 prioritizes the new
    # operational plot and the required calibration/necessity tables.
    label = stage.index(r"\label{fig:frontier}")
    start = stage.rfind(r"\begin{figure*}", 0, label)
    end = stage.index(r"\end{figure*}", label) + len(r"\end{figure*}")
    stage = stage[:start] + stage[end:]
    stage = stage.replace(
        r"\bibliography{references}", r"\bibliography{operational_references}"
    )
    Path("rss2027/dsre_stage1.tex").write_text(clean(stage))
    print(
        {
            "papers_updated": True,
            "new_calibration_parents": cal_parents,
            "new_test_parents": test_parents,
        },
        flush=True,
    )


def clean(text):
    import re

    parts = re.split(r"(\\(?:cite|ref|label)\{[^}]*\})", text)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", parts[i])
        parts[i] = re.sub(r"(?<=\d)(?=[a-zA-Z])", " ", parts[i])
        parts[i] = re.sub(r"\b([BbFH]) ([0-9])\b", r"\1\2", parts[i])
        parts[i] = parts[i].replace("CART 2", "CART2")
        parts[i] = parts[i].replace(
            r"\usepackage[T 1]{fontenc}", r"\usepackage[T1]{fontenc}"
        )
    return "\n".join(line.rstrip() for line in "".join(parts).splitlines()) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    write(parser.parse_args().root)
