"""Scientific report and rebuttal preparation from verified follow-up estimators."""

import argparse
import json
from pathlib import Path

from dsre_followup_batch import atomic, read


def interval(value):
    if value is None:
        return "N/A (empty population)"
    low, high = value["parent_percentile95"]
    return f"{100 * value['value']:+.2f} [{100 * low:+.2f}, {100 * high:+.2f}] pp"


def triple(row):
    return (
        f"{row['recommended']} / {row['successful']} / {row['unacceptable']}"
        if row
        else "0 / 0 / 0 (empty)"
    )


def tables(result):
    output = []
    tab = result["tables"]
    for task in ("PickCube-v1", "PushCube-v1"):
        output += [
            f"### {task}",
            "",
            "| Budget | Method | All starts rec / good / bad | Initially failed rec / good / bad | Initially successful rec / good / bad |",
            "|---|---|---:|---:|---:|",
        ]
        for budget in (0, 1):
            for method in (
                "DSRE",
                "B7",
                "B1_two_strict",
                "CART1_strict",
                "CART2_strict",
                "B5_beta10",
                "CART2_beta10",
                "B0_continue",
                "B0_recover",
            ):
                output.append(
                    f"| {budget} | {method} | "
                    + " | ".join(
                        triple(tab.get(f"{task}|{budget}|{method}|{pop}"))
                        for pop in ("all", "initial_failure", "initial_success")
                    )
                    + " |"
                )
        output += [
            "",
            "| Budget | Outcome class | Checkpoints / parents | Strict DSRE rec / good / bad | Continue / recover assigned |",
            "|---|---|---:|---:|---:|",
        ]
        for budget in (0, 1):
            for category in ("continue_only", "recover_only", "both", "neither"):
                row = tab.get(f"{task}|{budget}|DSRE|{category}")
                if row:
                    output.append(
                        f"| {budget} | {category} | {row['checkpoints']} / {row['parents']} | {triple(row)} | {row['continue']} / {row['recover']} |"
                    )
                else:
                    output.append(
                        f"| {budget} | {category} | 0 / 0 | 0 / 0 / 0 | 0 / 0 |"
                    )
        output += [""]
    return output


def write_report(root):
    result = read(root / "suffix_results.json")
    pooled = read(root / "pooled_secondary_results.json")
    missing = read(root / "followup_missingness.json")
    audit = read(root / "independent_audit.json")
    chunks = [read(p) for p in sorted((root / "chunks").glob("*_complete.json"))]
    complete = missing["complete_parents"] == 333
    lines = [
        "# DSRE RSS2027: independent prospective follow-up",
        "",
        f"Primary status: **{'COMPLETE' if complete else 'INCOMPLETE'}**, {missing['complete_parents']}/333 new complete parents, {missing['primary_checkpoints']}/666 primary checkpoints, {missing['qualified_checkpoints']} qualified checkpoints. No seed replacement or retraining.",
        "",
        f"Evidence: `{root}`. Earlier interrupted evidence: `results/dsre-rss2027/20261113T193554Z/`, immutable. Reviewed base `45422ef455327db91e08752edb684181800971ed`. Branch `research/dsre-rss2027-independent-followup`; exact local commit and archive SHA appear in the new completion manifest.",
        "",
        "## Research claim and cohort separation",
        "",
        "The fixed question is what observable evidence suffices to justify a fixed recovery intervention relative to paired measured outcomes, and what obstructs justification. Minimum-literal DSRE, its witnesses, support/ties, two skills, observations and horizon remain unchanged. B7 is the same decision problem. A finite-reference certificate is not a deployment risk guarantee.",
        "",
        "The earlier 33 complete parents/task and positive preliminary results were inspected before this separately preregistered follow-up. The primary population is exclusively Pick 6000034..6000199 (166 parents), Push 7000033..7000199 (167 parents), both unchanged conditions. The original Pick 6000033 boundary parent is excluded; its orphan stays in the earlier study only. Frozen reference/routers and eight existing small CART trees are byte-identical; **zero new fits**. The old 844 development checkpoints never absorb prospective outcomes.",
        "",
        "`followup_preregistration.md`, sorted seed manifest and `confirmation_freeze.json` were frozen before outcomes. Execution retains the original schedule after filtering. The seed/archive/directory overlap audit passed before physics. `scientific_reuse_regression.json` proves the entire existing physics implementation hash is unchanged. New code only schedules chunks, accounts resources, analyzes and presents the fixed comparisons.",
        "",
        "## Orchestration and missingness",
        "",
        f"{len(chunks)} synchronous chunks consumed {sum(c['wall_seconds'] for c in chunks):.2f}seconds of the10800-second physics ceiling. Chunk resource rows are independently retained in `chunks/` and outer worker CPU/wall rows in `commands.jsonl`. At most 480 seconds/24 parents per chunk and 120 seconds per parent, with 120 seconds reserved before launch. Each complete parent has an fsync/atomic marker for two qualified cells. Source/prefix/controller/model inconsistencies halt; uncommitted interrupted parents are never repeated.",
        "",
        f"Partial/missing parents: {len(missing['missing_or_partial_parents'])}. Qualified secondary-only cells: {len(missing['secondary_qualified_cells'])}. Exact IDs/reasons are in `followup_missingness.json`. Cohort completeness is not inferred from a clean chunk exit. The previous SIGTERM cause remains unknown; this run does not retroactively diagnose it.",
        "",
        "## New suffix-only primary results",
        "",
        "Counts below are recommendations / selected-action terminal successes / unacceptable choices, with abstention outside the success numerator. Each pair has two separate full-prefix reset branches, 70 controls/3.5 seconds, unchanged terminal task success. Same-information provisional B5 (.10 error) and CART (.9 purity) change the empirical justification standard and are not strict certificates.",
        "",
    ]
    lines += tables(result)
    lines += [
        "## Paired uncertainty and decision necessity",
        "",
        "4000 paired parent-bootstrap draws, PCG64 seed 2026111322+taskindex, two-sided 2.5/97.5 percentiles. Both conditions resample together; all complete task parents remain the sampling frame for subgroup ratios. These are suffix-only estimates under fixed routers. Bootstrap [0,0] can reflect no observed variation and is not a population error bound or proof of equality.",
        "",
        "| Task | Population | b1-b0 successful/checkpoint [95%] | Coverage difference [95%] | Unacceptable/checkpoint difference [95%] |",
        "|---|---|---:|---:|---:|",
    ]
    for key, value in result["paired_intervals"].items():
        if "|b1-b0|" in key:
            task, _, population = key.split("|")
            lines.append(
                f"| {task} | {population} | {interval(value['success_difference'])} | {interval(value['coverage_difference'])} | {interval(value['unacceptable_difference'])} |"
            )
    lines += [
        "",
        "| Task | Outcome class | b0 good | b1 good | Difference | Failed-start difference |",
        "|---|---|---:|---:|---:|---:|",
    ]
    records = result["decision_necessity_records"]
    for task in ("PickCube-v1", "PushCube-v1"):
        for category in ("continue_only", "recover_only", "both", "neither"):
            rs = [r for r in records if r["task"] == task and r["category"] == category]
            lines.append(
                f"| {task} | {category} | {sum(r['b0_success'] for r in rs)} | {sum(r['b1_success'] for r in rs)} | {sum(r['success_difference'] for r in rs):+d} | {sum(r['success_difference'] for r in rs if not r['initial_success']):+d} |"
            )
    for task in ("PickCube-v1", "PushCube-v1"):
        rs = [r for r in records if r["task"] == task]
        failed = sum(r["success_difference"] for r in rs if not r["initial_success"])
        required = sum(r["required_recovery_success_difference"] for r in rs)
        lines += [
            "",
            f"**{task}:** added successful recommendations on initially unsuccessful starts = {failed:+d}; added required-recovery successes in recover-only states = {required:+d}. Both-success adequate choices do not establish that recovery was necessary. This decomposition uses the original binary outcomes, not a new utility or solver.",
        ]
    lines += [
        "",
        "## Strong controls, actions, support and explanations",
        "",
        "| Task/budget comparator | Actual action disagreements |",
        "|---|---:|",
    ]
    for key, value in result["equivalences"].items():
        if key.endswith(
            ("DSRE-B7", "DSRE-B1_two_strict", "DSRE-CART1_strict", "DSRE-CART2_strict")
        ):
            lines.append(
                f"| {key} | {value['action_disagreements']} / {value['checkpoints']} |"
            )
    lines += [
        "",
        "| Task/budget comparator | Population | DSRE success difference [95%] | DSRE unacceptable difference [95%] |",
        "|---|---|---:|---:|",
    ]
    for key, value in result["paired_intervals"].items():
        if any(
            "DSRE-" + m in key for m in ("CART2_strict", "CART2_beta10", "B5_beta10")
        ):
            head, pop = key.rsplit("|", 1)
            lines.append(
                f"| {head} | {pop} | {interval(value['success_difference'])} | {interval(value['unacceptable_difference'])} |"
            )
    lines += [
        "",
        "| Task | Budget | Strict action | Assigned checkpoints / parents | Error parents |",
        "|---|---|---|---:|---:|",
    ]
    for key, value in result["assignment_counts"].items():
        if "|DSRE|" in key:
            task, budget, _, action = key.split("|")
            lines.append(
                f"| {task} | {budget} | {action} | {value['checkpoints']} / {value['assigned_parents']} | {value['error_parents']} |"
            )
    lines += [
        "",
        "**NOT_CALIBRATED.** The previous 42 zero-error assigned independent parents/stratum requirement is not inferred from total cohort size. `suffix_results.json` reports every stratum including zero and actual assignment counts to compare with 42. Even larger strata are confirmation, not independent calibration. No deployment error bound or executable authorization is issued.",
        "",
        "| Task | Budget | Strict recommendations | Total literals | Support rows sum | Support parents sum |",
        "|---|---|---:|---:|---:|",
    ]
    for task in ("PickCube-v1", "PushCube-v1"):
        for b in (0, 1):
            row = result["tables"].get(f"{task}|{b}|DSRE|all")
            if row:
                lines.append(
                    f"| {task} | {b} | {row['recommended']} | {row['literals']} | {row['support_rows_sum']} | {row['support_parents_sum']} |"
                )
    lines += [
        "",
        "Reference/query scope, all minimum-fact certificates, necessary-literal and obstruction witnesses are in `suffix_decisions.json`. Actual channel costs are Pick b0=0, b1=1 and Push b0=b1=0 by fixed minimum-cost ties. These are abstract Boolean-predicate counts from the same simulator pose interface, not sensors or measured sensing latency.",
        "",
        "## Secondary pooled description",
        "",
        "The following pool includes only completed parents from both studies. It excludes the old orphan and new partial parents. It is **SECONDARY_DESCRIPTIVE_POOL**, not untouched independent confirmation: earlier positive results were inspected before follow-up authorization. Frozen routers are identical. A distinct 4000-draw bootstrap uses seed 2026111422+taskindex; suffix estimates remain primary.",
        "",
    ]
    lines += tables(pooled)
    lines += [
        "## Physical examples, historical errata and independent audit",
        "",
        "`physical_examples.json` ties anonymous cases A–E to recorded predecision geometry, timestamps, predicate bits, measured paired outcomes and source identifiers. A recover-only Pick case (dx=-.03401m) and neither-success case (dx=+.05460m) share F0 but differ in the left predicate. The first has a three-fact minimum recovery certificate (goal not near, progress, object left of goal) supported by five independent reference parents; its full-signature child has two parents. The second remains inadequate. A both-success case illustrates an adequate but interchangeable decision. A Push recover-only/continue-only pair shares all 12 predicates; this is observation ambiguity, whereas the neither-success Pick case is repertoire inadequacy. Raw poses differ, so this is not an impossibility theorem for all sensors.",
        "",
        "The old paper accidentally labeled CART recommendation counts as successes. Correct old strict CART2 successes are 201,224,224,217 with one unacceptable choice each (recommendations 202,225,225,218). Old provisional CART2 b0 has 296 successes/297 recommendations and one error. Sealed data/figures and the independent previous aggregation were correct. This revision corrects text/ledger and the malformed indicator command; `presentation_errata.json`, git history and `starting_files/` preserve original bytes. No outcomes or model settings change.",
        "",
        f"Independent audit **{audit['status']}**: {audit['new_qualified_traces']} new traces, {audit['prefix_states_checked']}prefix states, {audit['outcome_controls_checked']}actual intervention controls, maximum action discrepancy {audit['maximum_action_error']}; {audit['selected_outcomes_recomputed_from_raw']} prediction views independently checked against raw labels, including abstentions. Main solver/feature code is checked against separate integer-mask rules, raw-pose predicates, action equations and direct CART leaf evaluation. Necessary-literal and obstruction witnesses are verified. These are two same-session implementations, not external human replication. Full-prefix/controller fidelity is measured; future trajectories are not independently duplicated.",
        "",
        "## Reproduction, tests, resources and scientific gate",
        "",
        f"Use `uv run --no-sync python scripts/dsre_followup_finish.py --root {root} --stage verify` for immutable verification. To reproduce analysis without physics or modifying sealed evidence:",
        "",
        "```bash",
        f"SOURCE={root}",
        "R=$(mktemp -d /tmp/dsre-followup-review-XXXXXX)",
        'cp "$SOURCE"/confirmation_freeze.json "$SOURCE"/fresh_seed_manifest.json "$SOURCE"/frozen_routers.json "$R"/',
        'ln -s "$PWD/$SOURCE/parent_progress" "$R/parent_progress"',
        'ln -s "$PWD/$SOURCE/fresh" "$R/fresh"',
        "export PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache",
        'uv run --no-sync timeout 600 python scripts/dsre_followup_analysis.py --root "$R"',
        "uv run --no-sync pytest -q tests/test_dsre_followup.py tests/test_dsre_paper.py",
        "/tmp/tectonic-rss2027-bin/tectonic --only-cached --untrusted --keep-logs --outdir rss2027 rss2027/dsre_stage1.tex",
        "```",
        "",
        "The exact original chunk commands, per-chunk wall/CPU records, source/input hashes, initial unused manifest, all missingness and the final compact archive are in this evidence root. New physics cannot be replayed in this sealed root: attempts and atomic markers prohibit repeats; any later new campaign requires a separate preregistration. The previous SIGTERM and CPU gap remain unchanged in the old study. New total measured resource use, tests, preservation proof, exact branch/commit and zero-worker audit are attested in the new completion manifest. Nothing is submitted, pushed or uploaded.",
        "",
        "Method distinctiveness, recovery benefit, independent confirmation, calibration and submission-worthiness are assessed separately in `DSRE_RSS2027_REVIEWER_CRITIQUE.md`. Formal six-page compliance is separate from the scientific judgment. A positive all-start coverage result alone cannot establish an improved physical recovery method.",
    ]
    Path("docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md").write_text(
        "\n".join(lines) + "\n"
    )
    print(
        json.dumps(
            {
                "report": "updated",
                "complete_followup": complete,
                "primary_checkpoints": missing["primary_checkpoints"],
            }
        ),
        flush=True,
    )


def write_review(root):
    data = read(root / "suffix_results.json")
    missing = read(root / "followup_missingness.json")
    audit = read(root / "independent_audit.json")
    assert audit["status"] == "PASS", "Review requires verified evidence"
    tab = data["tables"]
    p0 = tab["PickCube-v1|0|DSRE|all"]
    p1 = tab["PickCube-v1|1|DSRE|all"]
    f0 = tab.get(
        "PickCube-v1|0|DSRE|initial_failure", {"successful": 0, "checkpoints": 0}
    )
    f1 = tab.get(
        "PickCube-v1|1|DSRE|initial_failure", {"successful": 0, "checkpoints": 0}
    )
    tree = tab["PickCube-v1|1|CART2_strict|all"]
    risk = tab["PickCube-v1|1|CART2_beta10|all"]
    rules = tab["PickCube-v1|1|B5_beta10|all"]
    necessity = [
        r for r in data["decision_necessity_records"] if r["task"] == "PickCube-v1"
    ]
    required = sum(r["required_recovery_success_difference"] for r in necessity)
    delta = {
        c: sum(r["success_difference"] for r in necessity if r["category"] == c)
        for c in ("continue_only", "recover_only", "both", "neither")
    }
    assignments = {k: v for k, v in data["assignment_counts"].items() if "|DSRE|" in k}
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
    n = missing["complete_parents"]
    complete = n == 333
    gate = {
        "PAPER_DRAFT_READY": "Subject to final page/font/anonymity audit",
        "preliminary_characterization": "SUPPORTED_WITH_MAJOR_SCOPE_LIMITATIONS",
        "submission_worthy_preliminary_characterization": "BORDERLINE: a reviewable operational characterization, not established strong RSS readiness; principal researcher decides",
        "method_distinctiveness": "NOT_ESTABLISHED: exact B7 equivalence is mathematical, and short rules remain strong controls",
        "independent_confirmation": "COMPLETE_PREREGISTERED_SUFFIX"
        if complete
        else "INCOMPLETE_SUFFIX_VALID_SUBSET_ONLY",
        "physical_recovery_benefit": "NO_END_TO_END_POLICY_IMPROVEMENT_ESTABLISHED",
        "suffix_only_primary_pick_success_effect": data["paired_intervals"][
            "PickCube-v1|b1-b0|all"
        ]["success_difference"],
        "suffix_only_failed_start_pick_success_effect": data["paired_intervals"][
            "PickCube-v1|b1-b0|initial_failure"
        ]["success_difference"],
        "justified_required_recovery_coverage_change": required,
        "justified_failed_start_success_change": f1["successful"] - f0["successful"],
        "calibration": "NOT_PERFORMED_NOT_CALIBRATED",
        "strict_CART2_action_disagreements": disagreements,
        "cap2_action_disagreements": cap2,
        "assigned_strata_below 42": {
            k: v["assigned_parents"] < 42 for k, v in assignments.items()
        },
        "new_fits": 0,
        "no_submission_or_push": True,
    }
    atomic(root / "scientific_gate.json", gate)
    lines = [
        "# DSRE RSS2027: scientific critique and rebuttal preparation",
        "",
        "This is a same-session adversarial review supported by separate raw-physics/rule/predicate and numerical implementations. It is not external human peer review or an acceptance prediction.",
        "",
        "## Separate scientific gates",
        "",
        f"- **Independent confirmation:** {gate['independent_confirmation']}; {n}/333 new complete parents and {missing['primary_checkpoints']}/666 primary checkpoints. The earlier 133 qualified checkpoints and unexplained SIGTERM remain sealed separately; one old orphan is excluded.",
        "- **Preliminary characterization:** supported within the two-task, fixed-skill, declared-vocabulary protocol. Submission-worthiness is **borderline**, requiring principal-researcher judgment about the operational insight; formal six-page compliance does not establish a strong RSS contribution.",
        f"- **Method distinctiveness:** not established. B7 is the same minimum pure-rule decision problem; pure cap2 rules disagree on {cap2} suffix actions. New data cannot turn an established enumeration/intersection principle into new theory.",
        f"- **Recovery benefit:** failed-start successful recommendations change {f0['successful']} to {f1['successful']}/{f1['checkpoints']}; required recover-only successes change {required:+d}. These are justified-decision coverage outcomes, not a new controller or an end-to-end physical-policy improvement.",
        "- **Calibration:** not performed. Distinct assigned/error parents are reported for every task/action/budget; confirmation is not an independent calibration population. Rare strata below 42 are identified in `scientific_gate.json`.",
        "",
        "## New suffix-specific qualification of the earlier non-gain",
        "",
        f"Failed-start coverage: {interval(data['paired_intervals']['PickCube-v1|b1-b0|initial_failure']['success_difference'])}. Recover-only coverage: {interval(data['paired_intervals']['PickCube-v1|b1-b0|recover_only']['success_difference'])}. Both intervals include zero. The suffix adds two failed-start successes (one required continue, one required recover); therefore the earlier zero-gain finding is not silently generalized to the new cohort. Forty of the 42 additional successes still occur on initially successful states. This does not establish an end-to-end recovery-policy improvement.",
        "",
        "The sole strict CART2/cap2 exception is a recover-only offset checkpoint requiring a three-fact certificate supported by five reference parents. B7 supplies exactly the same certificate. `fresh_control_exception.json` retains its raw source hash, decision and action-equation qualification; the observation is descriptive and introduces no new rule or controller.",
        "",
        "## Central scientific interpretation",
        "",
        f"Untouched Pick b1 versus b0 yields {interval(data['paired_intervals']['PickCube-v1|b1-b0|all']['success_difference'])} successful strict coverage, with unacceptable choices {p0['unacceptable']} to {p1['unacceptable']}. The gain decomposes as continue-only {delta['continue_only']:+d}, recover-only {delta['recover_only']:+d}, both-success {delta['both']:+d}, neither {delta['neither']:+d}. Both-success choices are adequate without being uniquely required. The gain cannot be described only by its all-start percentage.",
        "",
        f"Strict CART2 disagrees on {disagreements} suffix actions and at Pick b1 gives {tree['successful']} successes/{tree['unacceptable']} unacceptable choices; DSRE gives {p1['successful']}/{p1['unacceptable']}. Provisional .9 CART gives {risk['successful']}/{risk['unacceptable']}, and B5 gives {rules['successful']}/{rules['unacceptable']}, using the same observables and reference. Their empirical-purity standard differs from strict universality. Any favorable observed operating point remains uncalibrated. B7 supplies identical decisions and minimum facts, precluding an algorithmic superiority claim.",
        "",
        "The potentially useful insight is that evidence which increases finite and out-of-sample justification coverage need not resolve the states where recovery is required. Explicit paired outcomes and obstruction witnesses separate representation conflict, inadequate repertoire and missing reference support. The decision-necessity decomposition sharpens that characterization without changing the utility or solver. Its relevance beyond a careful known-rule application remains the main reviewer challenge.",
        "",
        "## Rebuttal preparation: hardest objections and evidence",
        "",
        "1. **“This is ordinary sufficient-rule enumeration.”** Agree on the mathematical core. The frozen same-grammar B7 identity and cap2 controls are retained. The claim is the operational robot-intervention formulation, constructive insufficiency distinctions and reproducible empirical characterization. Do not answer by inventing a new algorithm or claiming that witness formatting alone is novel. A stronger contribution needs evidence that this contract changes an actual robotics decision beyond a simple known-rule interface.",
        "",
        "2. **“The action-intersection and observation-refinement theory already exists.”** Agree. Zhu/Leonard's partial-observability framework subsumes the feasibility core; Khan/Poupart/Black established minimal MDP decision explanations; DISCRET already synthesizes outcome-grounded subgroup rules. Anchors and probabilistic sufficient explanations target predictor sufficiency. The paper distinguishes its outcome target without claiming priority for these principles. The source-checked bibliography/ledger remains unchanged except factual count corrections.",
        "",
        f"3. **“Does it recover failures or just maintain success?”** Use the full necessity table, not a headline alone. Failed-start change is {f1['successful'] - f0['successful']:+d}; required-recovery change is {required:+d}. Report any positive, zero or negative value exactly. Additional successful justification is not automatically an end-to-end recovery improvement because abstention execution semantics and calibrated routing were not physically evaluated.",
        "",
        "4. **“Why does Push abstain if recovery works?”** The frozen reference contains compatible neither-success and opposing-action cases. Universal finite justification is different from high measured skill success in new seeds. All optional predicates remain uninformative for old Push classes. The raw poses differ, so neither the result nor its six unseparable edges prove that every sensor or continuous observation model must fail. Fixed controllers already use continuous poses; the limitation is the declared routing vocabulary and reference contract.",
        "",
        "5. **“The stronger tree or empirical-risk rule is enough.”** Give the exact same-information counts and paired intervals, including adverse comparisons. A strict CART match is sample equality, not a theorem; B7 equality is mathematical. A provisional .9 leaf or .10 empirical-error rule changes the purity standard and has no deployment guarantee. Fewer literals than a tree path do not establish human interpretability or method superiority when ordinary exact rules match them.",
        "",
        f"6. **“The follow-up is selected after a positive preliminary result.”** Disclose the history. The prior 33 parents/task were inspected before authorization; the new {n} complete parents belong exclusively to the fixed untouched suffix and use the same pre-existing routers. Seed manifest, endpoint definitions, bootstrap seed and continuation policy preceded outcomes. Pooling is explicitly secondary descriptive and excludes the old orphan. No favorable replacement, threshold search or significance stopping occurred.",
        "",
        "7. **“Zero observed errors imply safety.”** They do not. Finite purity and a two-parent support gate are not out-of-sample risk control. Bootstrap resampling cannot invent unseen failures and can produce [0,0]. Report actual assigned-parent strata versus the historical 42 zero-error requirement, while retaining NOT_CALIBRATED even for larger strata. Independent calibration, stochastic repeatability and deployment execution remain unfinished.",
        "",
        "8. **“These are not real sensing costs or broad robotics evidence.”** Correct: all predicates summarize simulator pose interfaces; cost is Boolean-predicate count, not sensors, latency or energy. There are two tasks, two fixed skills and binary terminal utility. No hardware, real perception or human study was run. Do not generalize beyond the declared scope or relabel the offline observation design as physical active sensing.",
        "",
        "9. **“Can we trust the paired branches and restart handling?”** Use the new atomic parent markers, immutable attempt list, source hashes and independent per-chunk CPU/wall records. Canonical full prefixes, controller memory, model edits and actual action equations are audited. The new study has no native snapshot restore and no independently duplicated future trajectories. Successful chunking does not identify the old SIGTERM cause. Preserve incomplete traces and every earlier seal rather than repairing history.",
        "",
        "## Factual corrections and presentation",
        "",
        "The old manuscript confused CART recommendations with successes: strict CART2 good counts are 201,224,224,217 (one bad each), not202,225,225,218; provisional b0 CART2 has 296 good/297 recommendations, not 297 good. Raw/aggregated evidence was correct. `presentation_errata.json` preserves the correction, and original paper bytes survive in `starting_files/` and git history. The malformed indicator command and stale Introduction future tense are corrected. Anonymous physical cases A–E now ground recover-only, both-success, neither-success and opposing-action examples in observed coordinates and measured outcomes.",
        "",
        "## Priorities before manual Stage1 submission",
        "",
        "1. Review whether the empirical sufficiency/necessity insight merits a Stage1 characterization paper despite exact-rule equivalence. Do not manufacture an algorithmic superiority claim or pivot the research question.",
        "2. Use only the verified final suffix figures, both initial-state populations, strongest baseline/error counts and explicit missingness. Keep pooled estimates secondary. Final page/font/anonymity/citation/claim audit must pass, with no supplement or external paper links.",
        "3. Treat independent calibration, stochastic repeats, actual observation cost, hardware transfer and practical witness usefulness as remaining scientific work. They were not silently completed here and are not implied by confirmation sample size.",
        "4. The principal researcher owns authorship and manual submission before December4,2026 23:59AoE. Nothing is pushed, uploaded or submitted. If invited, retain the same question during rebuttal and the Extension Charter; Stage2 is not automatic.",
        "",
    ]
    Path("docs/DSRE_RSS2027_REVIEWER_CRITIQUE.md").write_text("\n".join(lines))
    summary = f"""# DSRE Stage1: contribution and limits after independent follow-up

The fixed question is what observable evidence suffices to justify a fixed recovery intervention relative to paired outcomes, and what prevents justification. DSRE supplies minimum finite-reference facts, explicit observation/repertoire/reference witnesses and a fixed observation-budget frontier.

The mathematical core is established: robust action intersections, pure-rule enumeration, minimum hitting sets and subset selection are not new. B7 is equivalent; short rules and trees remain strong same-information controls. The candidate contribution is an operational robot-intervention formulation and a reproducible characterization of sufficiency, necessity and insufficiency, not algorithmic superiority.

A separately preregistered untouched suffix completed {n}/333 new parents and {missing["primary_checkpoints"]}/666 primary checkpoints, using frozen old references/routers and zero new fits. Pick successful strict recommendations change {p0["successful"]} to {p1["successful"]}/{p1["checkpoints"]}: {interval(data["paired_intervals"]["PickCube-v1|b1-b0|all"]["success_difference"])}. Failed-start successes change {f0["successful"]} to {f1["successful"]}/{f1["checkpoints"]}; required-recovery successes change {required:+d}. The decision-necessity decomposition retains both-success adequate choices separately. Unacceptable choices change {p0["unacceptable"]} to {p1["unacceptable"]}. All class/action/support/literal results and adverse controls are preserved.

Strict CART2 action disagreements number {disagreements}; pure cap2 disagreements {cap2}. Provisional .9 CART2 and B5 use different empirical purity standards, with Pick b1 good/bad counts {risk["successful"]}/{risk["unacceptable"]} and {rules["successful"]}/{rules["unacceptable"]}. These are not calibrated operating points or evidence of a new controller.

The earlier interrupted study remains immutable: 133 qualified checkpoints, 132 primary, one orphan excluded. The SIGTERM cause is unknown. Completed-parent pooling is secondary descriptive because earlier positive results were inspected before follow-up. The incomplete boundary parent is never replaced or remeasured.

Independent raw-physics, predicate/rule/tree and numerical audits verify the declared data and endpoints. Confirmation strengthens the bounded characterization, while method distinctiveness, end-to-end recovery benefit and calibration remain unestablished. Two simulated tasks, fixed binary utility, idealized poses and abstract predicate costs limit external validity; no hardware, stochastic-repeatability or human study is claimed.

Scientific gate: **borderline preliminary characterization; strong RSS readiness not established**. The principal researcher retains the submission decision. No push, upload or submission is performed. Exact evidence, reproduction commands, resources and local commit are in the follow-up seal.
"""
    Path("rss2027/CONTRIBUTIONS_AND_LIMITATIONS.md").write_text(summary)
    ledger = Path("rss2027/CLAIM_EVIDENCE_LEDGER.md")
    heading = "\n## Untouched suffix: final verified results\n"
    previous = ledger.read_text().split(heading)[0]
    entries = [
        heading,
        f"Evidence root: `{root}`. Primary = new suffix only; old boundary and orphan excluded. Pooled results are secondary descriptive.\n",
        "| Claim | Evidence and scope |",
        "|---|---|",
    ]
    entries.append(
        f"| {n}/333 complete new parents; {missing['primary_checkpoints']}/666 primary checkpoints; {len(missing['missing_or_partial_parents'])} missing/partial parents | followup_missingness.json and atomic parent_progress; separate untouched suffix, never replacement seeds. |"
    )
    for task in ("PickCube-v1", "PushCube-v1"):
        for b in (0, 1):
            record = tab[f"{task}|{b}|DSRE|all"]
            entries.append(
                f"| {task}, b{b}: rec/good/bad={record['recommended']}/{record['successful']}/{record['unacceptable']}, N={record['checkpoints']}, parents={record['parents']} | suffix_results.json tables; minimum facts/support in suffix_decisions.json. |"
            )
    entries.append(
        f"| Pick b1-b0 successful strict coverage {interval(data['paired_intervals']['PickCube-v1|b1-b0|all']['success_difference'])} | suffix_results.json paired_intervals; 4000 paired parent draws, seed 2026111322. |"
    )
    entries.append(
        f"| Pick failed-start good {f0['successful']}->{f1['successful']}/{f1['checkpoints']}; required recover-only good difference {required:+d} | decision_necessity_records and outcome-category tables; same binary utility, not a new score. |"
    )
    entries.append(
        f"| Pick gain by category: C-only {delta['continue_only']:+d}, R-only {delta['recover_only']:+d}, both {delta['both']:+d}, neither {delta['neither']:+d} | Same paired records; interchangeable adequacy separated from required action. |"
    )
    entries.append(
        f"| Strict CART2 disagreements {disagreements}; cap2 disagreements {cap2}; B7 identity retained | suffix_results.json equivalences, independent Oracle/direct tree audit. CART sample equality is not a universal theorem. |"
    )
    entries.append(
        f"| Pick b1 provisional CART2 good/bad {risk['successful']}/{risk['unacceptable']}; B5 {rules['successful']}/{rules['unacceptable']} | Same observables/reference; empirical .9/.10 criterion differs from strict finite purity. |"
    )
    entries.append(
        f"| {audit['new_qualified_traces']} traces, {audit['prefix_states_checked']} prefix states, {audit['outcome_controls_checked']} controls; maximum action error {audit['maximum_action_error']} | independent_audit.json and replay_audit_records.json; no duplicated future trajectories or external human replication. |"
    )
    entries += [
        "| Zero new model fits; eight old frozen CART trees reused | Frozen router bytes/source pins and scientific_reuse_regression.json. |",
        "| Every task/budget/action assignment and NOT_CALIBRATED | suffix_results.json assignment_counts; 42-parent criterion is not automatically met and confirmation is not independent calibration. |",
        "| Secondary pooled complete-parent analysis | pooled_secondary_results.json; previously inspected cohort included, orphan excluded, no untouched-confirmation claim. |",
        "| Anonymous cases A-E | physical_examples.json records actual raw source SHA256, predecision coordinates, timestamps and paired outcomes; illustrative development cases only. |",
        "| Exact formal statement, no new pure-rule theory | Existing method/specifications and verified prior-work entries above; indicator typo corrected without changing solver. |",
        "",
        "Final PDF page/font/anonymity and every main table/interval/physical value are checked in paper_format_audit.json and final_audit.json. Historical CART recommendation/success corrections are retained in presentation_errata.json. No paper upload, push or submission.\n",
    ]
    ledger.write_text(previous + "\n".join(entries))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    write_report(args.root)
    write_review(args.root)
