"""Revise the same anonymous paper from audited suffix-only and secondary tables."""

import argparse
from pathlib import Path

from dsre_followup_batch import read


def ci(value):
    if value is None:
        return "not estimable"
    low, high = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} percentage points, paired 95\\% interval $[{100 * low:.2f},{100 * high:.2f}]$"


def write_paper(root):
    data = read(root / "suffix_results.json")
    tab = data["tables"]
    miss = read(root / "followup_missingness.json")
    audit = read(root / "independent_audit.json")
    pool = read(root / "pooled_secondary_results.json")
    pooled_pick0 = pool["tables"].get("PickCube-v1|0|DSRE|all", {})
    pooled_pick1 = pool["tables"].get("PickCube-v1|1|DSRE|all", {})

    def row(task, b, pop="all", method="DSRE"):
        return tab.get(
            f"{task}|{b}|{method}|{pop}",
            {
                "checkpoints": 0,
                "parents": 0,
                "recommended": 0,
                "successful": 0,
                "unacceptable": 0,
                "recover": 0,
                "continue": 0,
                "literals": 0,
            },
        )

    p0, p1 = row("PickCube-v1", 0), row("PickCube-v1", 1)
    f0, f1 = (
        row("PickCube-v1", 0, "initial_failure"),
        row("PickCube-v1", 1, "initial_failure"),
    )
    q0, q1 = row("PushCube-v1", 0), row("PushCube-v1", 1)
    pick_ci = data["paired_intervals"]["PickCube-v1|b1-b0|all"]["success_difference"]
    tree = row("PickCube-v1", 1, method="CART2_beta10")
    strict_tree = row("PickCube-v1", 1, method="CART2_strict")
    rules = row("PickCube-v1", 1, method="B5_beta10")
    failed_ci = (
        data["paired_intervals"]
        .get("PickCube-v1|b1-b0|initial_failure", {})
        .get("success_difference")
    )
    required_ci = (
        data["paired_intervals"]
        .get("PickCube-v1|b1-b0|recover_only", {})
        .get("success_difference")
    )
    strict_ci = (
        data["paired_intervals"]
        .get("PickCube-v1|b1|DSRE-CART2_strict|all", {})
        .get("success_difference")
    )
    provisional_ci = (
        data["paired_intervals"]
        .get("PickCube-v1|b1|DSRE-CART2_beta10|all", {})
        .get("success_difference")
    )
    uncertainty_note = (
        "Both intervals include zero in this cohort."
        if all(
            v is not None
            and v["parent_percentile95"][0] <= 0 <= v["parent_percentile95"][1]
            for v in (failed_ci, required_ci)
        )
        else ""
    )
    exception_note = (
        "The single differing recovery requires three facts supported by five reference parents, beyond the cap2 grammar."
        if (root / "fresh_control_exception.json").exists()
        else ""
    )
    counts = miss["complete_parents"]
    complete = counts == 333
    text = Path("rss2027/dsre_stage1.tex").read_text()
    start = text.index("\\begin{abstract}")
    end = text.index("\\end{abstract}", start) + len("\\end{abstract}")
    abstract = f"""\\begin{{abstract}}
A robot recovery action needs an intervention-grounded justification, not only a prediction of what its policy would do. We formulate a finite-reference contract connecting predecision predicates to paired continue/recover outcomes. Decision-Sufficient Recovery Explanations (DSRE) return minimum sufficient facts or constructive witnesses distinguishing observation conflict, inadequate recovery repertoire, and missing reference support. The solver uses established pure-rule semantics; the contribution is the operational formulation and empirical characterization of when observable evidence can justify an intervention. On844qualified development checkpoints, one extra Boolean pose predicate raises PickCube finite actionable mass183$\\to$235/422. We separately preregistered an untouched suffix after inspecting an interrupted preliminary cohort. The follow-up completed{counts}/333new parents. PickCube successful strict recommendations change{p0["successful"]}$\\to${p1["successful"]}/{p1["checkpoints"]} ({ci(pick_ci)}). Initially unsuccessful starts yield{f0["successful"]}$\\to${f1["successful"]}/{f1["checkpoints"]}. Outcome-necessity analysis separates interchangeable both-success choices from required recovery decisions. Strong exact-rule, tree and provisional-risk controls constrain the interpretation. The results characterize observable justification without establishing an improved recovery controller, algorithmic superiority, or deployment calibration.
\\end{{abstract}}"""
    abstract = abstract.replace(r"$\to$", " to ")
    text = text[:start] + abstract + text[end:]
    start = text.index("\\section{Introduction}")
    end = text.index("\\section{Related", start)
    introduction = r"""\section{Introduction}
A robot choosing between continuing a manipulation and invoking recovery faces three different situations: either skill may succeed, recovery alone may succeed, or neither skill may succeed. The same declared observations can describe all three. Explaining a policy's prediction does not establish that its selected intervention is adequate, and a high average recovery success rate does not resolve an ambiguous individual decision.

Table~\ref{tab:physical} makes the problem concrete. Two PickCube checkpoints share six primary predicates, but one is recover-only and the other neither-success. A signed geometric predicate separates them without making the inadequate state recoverable. A PushCube pair has opposing adequate actions yet identical values under the entire declared vocabulary. A both-success checkpoint, by contrast, can support an adequate action without establishing that recovery was necessary.

We ask: \emph{What observable evidence suffices to justify a fixed robot recovery intervention relative to measured paired outcomes, and what explains insufficiency?} The operational contribution joins minimum observable action facts, constructive observation/repertoire/reference witnesses, and a finite development-time instrumentation frontier under one explicit intervention contract. Established sufficient-rule and robust-intersection principles supply the reasoning. We evaluate their robotics consequences against equally informed rules and trees, rather than claiming a new enumeration algorithm.

Our evidence separates exact finite-reference statements, exploratory grouped cross-fitting, an interrupted preliminary cohort, and a separately preregistered untouched suffix. The key distinction is between increased successful justification coverage and increased justified recovery where recovery is required. The same measured four-category outcomes support this decomposition without changing the solver, utility, or hypothesis after seeing results.

"""
    text = text[:start] + introduction + text[end:]
    # Self-contained exact observation thresholds, without changing the feature dictionary.
    old = "Six primary predicates summarize goal distance, hand--object distance, progress, object displacement, gripper closure and relative height. Six optional predicates test signed object--goal x/y offsets and hand--object x offsets against fixed $\\pm.02$ m thresholds. All derive from simulator-supplied poses. They are observable interfaces in the experiment, not evidence for real visual perception or new sensing hardware. Privileged contact/grasp fields are diagnostic only and absent from primary queries."
    new = r"""The primary predicates are object--goal distance at most0.03m; hand--object distance at most0.04m; goal-distance reduction and object displacement from the first prefix packet each at least0.005m; summed absolute finger positions at most0.04m; and hand height above the object greater than0.03m. Optional predicates test object--goal x/y and hand--object x offsets below $-0.02$ m or above $0.02$ m. They summarize simulator-supplied poses, not validated real perception or newly acquired measurements. Privileged contact/grasp fields are excluded from primary queries."""
    text = text.replace(old, new)
    text = text.replace(
        "Both unchanged skills run for 70 controls, or 3.5 s, and adequacy uses terminal task success.",
        "Both unchanged skills run for 70 controls, or 3.5 s, and adequacy uses terminal task success. Pick recovery is a frozen staged regrasp (open/lift, approach, close, goal); Push recovery lifts and repositions behind the object before pushing. Continuations retain goal-directed Cartesian control.",
    )
    start = text.index("\\subsection{Frozen prospective check}")
    end = text.index("\\section{Results", start)
    protocol = r"""\subsection{Independent prospective follow-up}
The original400-parent schedule was interrupted by an unexplained SIGTERM after133qualified checkpoints; 132from66complete parents (33/task) form its primary analysis, with one orphan excluded. Pick successful recommendations rose29$\to$38/66, but failed-start successes stayed6/20; strict CART2 matched all264preliminary decisions. These positive preliminary findings were inspected before authorizing a separate follow-up, so its primary estimator uses only the previously untouched suffix: 166Pick and167Push parents, both original conditions. The incomplete Pick boundary parent is never remeasured. References, b0/b1 channels, support/ties, skills and tree nodes remain frozen; no models are retrained.

Each candidate action starts from a separate seeded reset followed by the full canonical action prefix. Every prefix state, endpoint, model edit and controller custom memory must match before intervention. Native snapshots are not used. Qualification checks restoration and recorded action equations; future trajectories are not independently duplicated. New physics is bounded to three cumulative hours in synchronous5--8minute chunks, with atomic completion after both conditions. Preregistered interrupted-parent exclusion and untouched-parent continuation prevent replacement or repeated measurements; qualification failures halt the study.

Primary suffix-only effects compare b1--b0 with4000paired seed-parent bootstrap draws, retaining both conditions together. Resampling all complete task parents also defines the initial-state and outcome-category contrasts. A separate completed-parent pool is descriptive only because the preliminary cohort was inspected. Neither study supplies independent deployment calibration.

\begin{figure*}[t]
\centering\includegraphics[width=\textwidth]{figures/necessity.png}
\caption{Untouched suffix-only PickCube outcomes under frozen strict-reference routing. Colors separate successful choices required relative to the two fixed skills from interchangeable choices when both succeed; red marks unacceptable choices. Denominators and failed-start outcomes are explicit. These are measured out-of-sample outcomes, not finite-reference ceilings or risk guarantees. Provisional empirical-risk controls use a different standard and are reported separately.}
\label{fig:necessity}
\end{figure*}

"""
    text = text[:start] + protocol + text[end:]
    start = text.index("\\section{Results")
    end = text.index("\\section{Discussion", start)
    result_text = r"""\section{Results and Their Boundaries}
\subsection{Finite reference and exploratory cross-fitting}
On the422development Pick checkpoints, finite actionable masses at budgets0--3 are183,235,237,238; all six optional predicates yield248. Push remains zero throughout. These exact same-table statements support the selective observation effect (H1) and repertoire boundary (H2), not deployment ceilings. Figure~\ref{fig:frontier} distinguishes them from outcomes against smaller cross-fit training references.

Grouped Pick cross-fitting gives202$\to$242successful strict recommendations/422 at b1: +9.48percentage points, paired95\% interval[6.64,12.32], with unacceptable choices1$\to$2. Among145failed starts, successes fall19$\to$18. B7 matches all16,880registered decision/explanation views; pure two-literal rules match throughb2. Strict CART2 gives201,224,224,217successful recommendations with one unacceptable choice each; provisional $.9$CART2 gives296/422successes and one error at b0.

For Push, always recover succeeds415/422while strict coverage stays zero. Compatible reference classes include neither-success cases and opposing adequate actions; six conflict edges remain unseparated by all six optional predicates. This supports H3 without suggesting the recovery skill is ineffective. Held-out Pick errors include unseen neither-success outcomes and an absent b1 signature, illustrating H4: training-pure rules can fail beyond their reference.

"""
    result_text += f"""\\subsection{{Untouched suffix-only outcomes}}
The follow-up completed{counts}/333parents and{miss["primary_checkpoints"]}/666primary checkpoints; {len(miss["missing_or_partial_parents"])}parents are missing or partial. Its status is explicitly {"complete" if complete else "incomplete"}. The earlier133qualified checkpoints, including the orphan, remain unchanged and outside the suffix-only estimator. No seeds were substituted, no thresholds or models changed, and no significance criterion stopped sampling.

\\begin{{table}}[t]
\\caption{{Suffix-only strict DSRE recommendations / successful / unacceptable. Denominators: Pick{p1["checkpoints"]}checkpoints/{p1["parents"]}parents; Push{q1["checkpoints"]}/{q1["parents"]}. Initially unsuccessful starts are separate.}}
\\label{{tab:fresh}}\\centering
\\begin{{tabular}}{{lcrr}}\\toprule
Task & Budget & All starts & Failed-start good / starts\\\\\\midrule
"""
    for task, name in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for budget in (0, 1):
            a = row(task, budget)
            f = row(task, budget, "initial_failure")
            result_text += (
                f"{name} & {budget} & {a['recommended']} / {a['successful']} / {a['unacceptable']} & {f['successful']} / {f['checkpoints']}"
                + r"\\"
                + "\n"
            )
    result_text += r"""\bottomrule\end{tabular}
\end{table}

"""
    result_text += f"""Pick b1--b0 successful strict coverage changes by {ci(pick_ci)}. Unacceptable choices are{p0["unacceptable"]}$\\to${p1["unacceptable"]}; abstentions are{p0["checkpoints"] - p0["recommended"]}$\\to${p1["checkpoints"] - p1["recommended"]}. Zero observed errors or a degenerate bootstrap interval would not establish zero population risk. Push strict successes are{q0["successful"]}$\\to${q1["successful"]}/{q1["checkpoints"]}, while always recovering succeeds{row("PushCube-v1", 1, method="B0_recover")["successful"]}/{q1["checkpoints"]}.

"""
    for task, name in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        vals = [
            row(task, 1, c)["checkpoints"]
            for c in ("continue_only", "recover_only", "both", "neither")
        ]
        result_text += (
            f"{name} outcome classes (continue-only/recover-only/both/neither) contain"
            + "/".join(map(str, vals))
            + "checkpoints. "
        )
    result_text += "\n\n\\subsection{Decision necessity and strongest controls}\n"
    necessity = [
        r for r in data["decision_necessity_records"] if r["task"] == "PickCube-v1"
    ]
    changes = {
        c: sum(r["success_difference"] for r in necessity if r["category"] == c)
        for c in ("continue_only", "recover_only", "both", "neither")
    }
    required = sum(r["required_recovery_success_difference"] for r in necessity)
    result_text += f"""The Pick gain decomposes into{changes["continue_only"]:+d}continue-only, {changes["recover_only"]:+d}recover-only, {changes["both"]:+d}both-success and {changes["neither"]:+d}neither-success choices (Fig.~\\ref{{fig:necessity}}). Initially unsuccessful successes change{f0["successful"]}$\\to${f1["successful"]}/{f1["checkpoints"]}; additional successful required-recovery recommendations number{required:+d}. Failed-start coverage changes by {ci(failed_ci)}; recover-only coverage by{ci(required_ci)}. {uncertainty_note} This is a decomposition of the same outcomes, not a changed utility. A larger numerator dominated by both-success or already-successful states does not demonstrate improved failure recovery.

"""
    b7 = sum(
        v["checkpoints"]
        for k, v in data["equivalences"].items()
        if k.endswith("DSRE-B7")
    )
    disagreements = sum(
        v["action_disagreements"]
        for k, v in data["equivalences"].items()
        if k.endswith("DSRE-CART2_strict")
    )
    cap2 = sum(
        v["action_disagreements"]
        for k, v in data["equivalences"].items()
        if k.endswith("DSRE-B1_two_strict")
    )
    result_text += f"""B7 matches{b7}suffix decisions and minimum facts. Strict CART2 differs on{disagreements}/{b7}actions; the pure two-literal control differs on{cap2}/{b7}. At b1 the strict tree gives{strict_tree["successful"]}successes and{strict_tree["unacceptable"]}unacceptable choices. The strict-tree contrast is {ci(strict_ci)}. {exception_note} These are equally informed comparators. A tree match on a cohort is empirical; B7 identity follows from shared grammar and ties. At b1, provisional $.9$CART2 succeeds{tree["successful"]}/{tree["checkpoints"]}with{tree["unacceptable"]}unacceptable choices; ordinary B5 succeeds{rules["successful"]}/{rules["checkpoints"]}with{rules["unacceptable"]}. DSRE minus provisional CART2 is {ci(provisional_ci)}. Their empirical-purity criterion differs from strict reference universality, and none is calibrated for deployment.

"""
    assigned = data["assignment_counts"]["PickCube-v1|1|DSRE|recover"][
        "assigned_parents"
    ]
    result_text += f"""Only{assigned}independent suffix parents receive strict Pick recovery at b1. This is below the earlier42zero-error assigned-parent requirement, a separate calibration criterion; this confirmation cohort is not independent calibration even where assignment counts exceed42. Certificates and all applicable obstruction witnesses are checked against the frozen reference.

The independent audit verifies{audit["new_qualified_traces"]}traces, {audit["prefix_states_checked"]}prefix states and{audit["outcome_controls_checked"]}intervention controls, with maximum recorded-action discrepancy{audit["maximum_action_error"]}. Separate raw predicates/terminal labels, integer-mask rules and direct tree-leaf calculations reproduce{audit["selected_outcomes_recomputed_from_raw"]}prediction views, including abstentions. This is two same-session implementations, not external human replication. Pooling completed parents gives{pooled_pick0.get("successful", 0)}$\\to${pooled_pick1.get("successful", 0)}/{pooled_pick1.get("checkpoints", 0)}Pick successes, secondary descriptive only: the earlier cohort was inspected, the old orphan is excluded, and the pool never replaces suffix inference.

"""
    text = text[:start] + result_text + text[end:]
    start = text.index("\\section{Discussion")
    end = text.index("\\clearpage", start)
    discussion = r"""\section{Discussion and Stage 2 Questions}
The operational distinction is consequential: skill success, observable finite-reference justification, and out-of-sample adequacy answer different questions. Forty of the 42 additional successful recommendations occur on already-successful starts; only one extra required recovery is justified, with its paired interval including zero. Explicit obstruction witnesses distinguish a representation collision from inadequate skills and missing reference support. They explain the declared reference, not the physical root cause of a failure.

The strongest controls delimit the contribution. Exact ordinary rules have the same decisions and minimal facts; trees can match the operating point, and provisional rules can recommend more actions under a different standard. The methodological contribution is the robot-intervention contract and measured sufficiency/necessity characterization, rather than new pure-rule mathematics. Independent confirmation can strengthen that characterization without creating an algorithmic advantage.

Limits remain two simulated tasks, fixed skills, deterministic branches, binary horizon-specific utility and idealized pose interfaces. Predicate count is abstract representation cost, not sensor acquisition, latency or energy. No hardware, stochastic-repeatability, real-perception or human-interpretability study is claimed. Prospective outcomes do not enter training, and confirmation is not deployment calibration. Stage2, only if invited, should test independent risk calibration, practical observation cost and transfer while retaining the same intervention-justification question. No improved physical recovery controller or population safety guarantee follows from these experiments.

"""
    text = text[:start] + discussion + text[end:]
    # Numeric adjacency in generated prose is normalized for readable typography.
    import re

    parts = re.split(r"(\\(?:cite|ref|label)\{[^}]*\})", text)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", parts[i])
        parts[i] = re.sub(r"(?<=\d)(?=[a-zA-Z])", " ", parts[i])
        parts[i] = re.sub(r"\b([BbFH]) ([0-9])\b", r"\1\2", parts[i])
        parts[i] = parts[i].replace("CART 2", "CART2")
    text = "".join(parts)
    Path("rss2027/dsre_stage1.tex").write_text(
        "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    )
    print({"paper_updated": True, "new_parents": counts, "complete_followup": complete})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    write_paper(parser.parse_args().root)
