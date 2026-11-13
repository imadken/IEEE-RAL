"""Assemble compact scientific tables without changing frozen decisions."""

import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def line(row):
    return f"{row['recommended']} / {row['successful']} / {row['unacceptable']}"


def pct(interval):
    if interval is None:
        return "not estimable"
    lo, hi = interval["parent_percentile95"]
    return f"{100 * interval['value']:+.2f} [{100 * lo:+.2f}, {100 * hi:+.2f}] pp"


def render_tables(tables, fresh=False):
    text = []
    budgets = (0, 1) if fresh else range(4)
    methods = (
        "DSRE",
        "B7",
        "B1_two_strict",
        "CART1_strict",
        "CART2_strict",
        "B5_beta10",
        "CART2_beta10",
        "B0_recover",
    )
    for task in ("PickCube-v1", "PushCube-v1"):
        text += [
            f"### {task}",
            "",
            "| Budget | Method | All starts R / good / bad | Initially failed R / good / bad | Initially successful R / good / bad |",
            "|---|---|---:|---:|---:|",
        ]
        for budget in budgets:
            for method in methods:
                values = [
                    tables.get(f"{task}|{budget}|{method}|{population}")
                    for population in ("all", "initial_failure", "initial_success")
                ]
                if values[0] is None:
                    continue
                text.append(
                    f"| {budget} | {method} | "
                    + " | ".join(line(v) if v else "0 / 0 / 0 (empty)" for v in values)
                    + " |"
                )
        text += [
            "",
            "| Budget | Strict DSRE outcome class | Checkpoints / parents | Recommended / good / bad |",
            "|---|---|---:|---:|",
        ]
        for budget in budgets:
            for category in ("continue_only", "recover_only", "both", "neither"):
                v = tables.get(f"{task}|{budget}|DSRE|{category}")
                if v:
                    text.append(
                        f"| {budget} | {category} | {v['checkpoints']} / {v['parents']} | {line(v)} |"
                    )
        text += [""]
    return text


def report(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence sealed; reproduce in a separate scratch root")
    reused = load(root / "reused_stratified_tables.json")
    contrasts = load(root / "reused_paired_intervals.json")
    finite = load(root / "reused_finite_ceiling.json")
    fresh_done = (root / "fresh_independent_audit.json").exists()
    text = [
        "# DSRE RSS2027: strengthened scientific evidence",
        "",
        "The DSRE question, controllers, feature thresholds and original negative evidence are preserved. This campaign combines a complete anonymous draft with independently regenerated development results and one preregistered prospective study. It is not a new algorithm or a physical recovery improvement claim.",
        "",
        f"Evidence root: `{root}`. Reviewed base: `186af4931ce4926fc699282ac2394730c7368c79`. Branch: `research/dsre-rss2027-stage1-paper-and-evidence`. Final local SHA is attested in the completion manifest. Raw evidence is local and excluded through `.git/info/exclude`; `.gitignore`, `uv.lock`, historical seals, user document moves and other jobs are preserved.",
        "",
        "## Qualified evidence and availability",
        "",
        "The self-contained execution contract is preserved as `authority.txt`. Method/protocol/results/novelty files for DSRE v1.0, v1.1 and evidence repair were read. The original separate v1.0 blueprint remains absent as documented historically; no replacement or missing evidence is invented. The latest repair seal was verified before work: 1543 sealed members, 875 prior files, 144 historical manifests, 1646 prior run members and 33 frozen pins. This session additionally inventories 3190 earlier DSRE run members for final preservation.",
        "",
        "There are 844 qualified old checkpoints, 422/task and 211 independent seed groups/task; 76 of the original 920 candidates remain excluded. All old parents informed development. Both conditions stay in their original five grouped folds. Each outcome is terminal success after the fixed 70 controls / 3.5 seconds, not first-hit success. A single deterministic branch is a measured value, not an estimated stochastic success probability. Optional predicates derive from the same simulator-supplied poses; one predicate is one abstract representation cost, not a sensor or measured acquisition latency.",
        "",
        "## Independent reused-data results",
        "",
        "The independent integer-mask oracle recomputes every unique saved DSRE decision. Manifests expand them into registered views without retraining. B7 action and minimum explanation agree in all 16,880 views; diagnostic support metadata on abstentions is not asserted identical. All errors and source references are preserved in `reused_error_inspection.json`.",
        "",
        "| Task | Budget | Selected optional indices | Finite actionable mass |",
        "|---|---:|---|---:|",
    ]
    for key, value in finite.items():
        task, budget = key.split("|")
        text.append(
            f"| {task} | {budget} | {value['selected']} | {value['mass']} / {value['total']} |"
        )
    text += [
        "",
        "Finite mass is exact on the full table, without claiming that its reference is the same as each cross-fit training table. Cross-fit successful recommendations can exceed that mass because conflicting held-out rows are absent from training. Neither result is a deployment ceiling.",
        "",
        "In the following tables R means recommended, good means selected action succeeds, and bad means selected action fails, including neither-success cases. Abstention is neither a success nor an executed error. B5 and `.9` CART are provisional empirical-risk methods and are not directly interchangeable with strict purity.",
        "",
    ]
    text += render_tables(reused)
    text += [
        "## Grouped uncertainty and strongest same-information comparisons",
        "",
        "All intervals below are paired 4000-draw percentile bootstrap intervals over independent seed parents, with both conditions resampled together, PCG64 seed2026111319 (+task index). The previous 2000-draw interval [6.6351,12.5592]pp is preserved in the old run; the independently regenerated interval below differs slightly by Monte Carlo draws. No row-level pseudo-replication is used. These are exploratory intervals for reused data, not untouched confirmation.",
        "",
        "| Task | Budget contrast | Population | Successful recommendations / checkpoints difference [95%] |",
        "|---|---|---|---:|",
    ]
    for key, v in contrasts.items():
        if "b0|" not in key or "DSRE-" in key:
            continue
        task, budget, pop = key.split("|")
        text.append(f"| {task} | {budget} | {pop} | {pct(v)} |")
    text += [
        "",
        "| Task | Budget | DSRE minus comparator | Population | Successful difference [95%] | Unacceptable difference [95%] |",
        "|---|---|---|---|---:|---:|",
    ]
    for key, v in contrasts.items():
        if "|DSRE-" not in key:
            continue
        task, budget, comp, pop = key.split("|")
        if pop == "initial_success":
            continue
        text.append(
            f"| {task} | {budget} | {comp} | {pop} | {pct(v['difference'])} | {pct(v['error_difference'])} |"
        )
    text += [
        "",
        "Full task/budget/method/outcome-class/initial-state/fold counts are in `reused_stratified_tables.json` (1380 cells). Strict DSRE stratum intervals, including all five folds, are in `reused_stratified_intervals.json`. Conditional ratios from fewer than ten assigned parents must remain descriptive. The all-checkpoint intervals above estimate success coverage, not a calibrated conditional failure risk.",
        "",
        "## Error mechanisms, physical examples and novelty",
        "",
        "The exact selector has eleven unacceptable cross-fit views from seven unique PickCube checkpoints: ten neither-success views and one recover-only state assigned continue. No training exact-signature class for these views contains an adverse matching outcome. For the extra b1 error the full held-out signature is absent altogether; its broader training-pure continue rule extrapolates incorrectly. For b3, extra sparse recovery classes admit previously unseen neither-success states. Thus finite purity is not population validity.",
        "",
        "Two verified physical examples are retained in the sealed `worked_examples.json` under `results/dsre-evidence-repair/20261113T180828Z/`. A Pick recover-only checkpoint (object.x=-.046608731m, goal.x=-.012600221m) and neither-success checkpoint (object.x=.039204050m, goal.x=-.015400097m) share F0 but differ in object-left-of-goal. The first obtains a two-parent pure recovery child; the second remains inadequate. A Push recover-only/continue-only pair shares all twelve predicates although its raw poses differ. Its opposing edge is one of six, none separable by this menu. Exact internal source IDs and hashes remain in evidence, outside the anonymous PDF.",
        "",
        "B7 equality and two-literal equality through b2 preclude an algorithmic-superiority claim. At b1 greedy coverage and canonical selection also match exact selection. At b3 eight extra successes over greedy accompany four extra unacceptable recommendations and one extra predicate. The feasibility core is already subsumed by robust action-intersection theory; minimum rule enumeration and subset search are established. The useful empirical question is when this explicit finite contract exposes observation/repertoire/reference limitations. Its distinct robotics contribution remains unresolved.",
        "",
        "## Preregistered prospective simulation",
        "",
        "Read `preregistration.md`, `fresh_seed_manifest.json`, `frozen_routers.json` and `confirmation_freeze.json` for the exact pre-outcome freeze. Seeds6000000..6000199 (Pick) and7000000..7000199 (Push) are fixed, interleaved, two unchanged conditions per parent. All844 old checkpoints train/reference b0/b1; exact selection uses development outcomes only. Only eight prescribed small depth1/2 outcome trees were fit. No fresh outcome chooses channels, thresholds, ties or a model. Maximum400 parents,800 checkpoints,1600 action continuations,3h physics,8h session,1GB new artifacts,0GPU training/paid APIs.",
        "",
        "Each action branch uses a new seeded reset and the complete canonical prefix. Every prefix state, model edit and exact controller memory is checked; native snapshots are never restored. The new two-action study does not include extra duplicate future-trajectory branches, so its qualification is checkpoint restoration plus offline audit of actual actions/outcomes. It does not claim new-seed duplicated future-trajectory fidelity from the old reference qualification. A fidelity/source/runtime failure stops the entire study, with no replacements. Primary inference uses only complete seed parents; qualified orphan conditions remain a separately identified secondary population.",
        "",
    ]
    if fresh_done:
        fresh = load(root / "fresh_stratified_tables.json")
        missing = load(root / "fresh_missingness.json")
        ci = load(root / "fresh_paired_intervals.json")
        audit = load(root / "fresh_independent_audit.json")
        text += [
            f"Fresh status: **{missing['physics']['status']}**; {missing['fully_completed_parents']}/400 complete parents, {missing['qualified_checkpoints']}/800 qualified checkpoints, {missing['primary_complete_parent_checkpoints']} primary checkpoints. Qualified orphan conditions: {len(missing['qualified_orphan_conditions'])}. Missing checkpoints: {len(missing['missing_checkpoints'])}. Stop reason: `{missing['physics']['stop_reason']}`. Wall physics {missing['physics']['wall_seconds']:.2f}s. Missingness lists are exact, not imputed failures or a full-cohort claim.",
            "",
        ]
        text += render_tables(fresh, True)
        text += [
            "| Task | Population | b1-b0 success coverage [95%] | Coverage difference [95%] | Unacceptable/checkpoint difference [95%] |",
            "|---|---|---:|---:|---:|",
        ]
        for key, v in ci.items():
            task, pop = key.split("|")
            text.append(
                f"| {task} | {pop} | {pct(v['difference'])} | {pct(v['coverage_difference'])} | {pct(v['bad_difference'])} |"
            )
        text += [
            "",
            f"Independent replay audit: **{audit['status']}**, {audit['qualified_checkpoint_traces_audited']} raw traces, {audit['prefix_states_audited']} prefix states, {audit['outcome_actions_audited']} actual outcome controls, maximum controller-action discrepancy {audit['maximum_action_error']}. Separate integer-mask rules and direct CART leaf recomputation verify {audit['numerical_prediction_views_checked']} scored views, with necessary-literal/obstruction witnesses checked. This is independent implementation within one session, not external human replication.",
            "",
            "**NOT_CALIBRATED.** `fresh_assignment_counts.json` reports distinct assigned/error parents for every task/action/method/budget. No bound is reported from confirmation as if it were independent calibration. The earlier42 zero-error assigned parents criterion does not authorize a deployment claim here, and rare recovery strata may be much smaller.",
            "",
        ]
        strong = load(root / "fresh_strong_baseline_intervals.json")
        text += [
            "### Fresh strong-baseline effects",
            "",
            "| Task | Budget | DSRE minus comparator | Population | Success/checkpoint difference [95%] | Unacceptable/checkpoint difference [95%] |",
            "|---|---|---|---|---:|---:|",
        ]
        for key, value in strong.items():
            if not any(
                "DSRE-" + method + "|" in key
                for method in ("CART2_strict", "CART2_beta10", "B5_beta10")
            ) or key.endswith("|initial_success"):
                continue
            task, budget, method, population = key.split("|")
            text.append(
                f"| {task} | {budget} | {method} | {population} | {pct(value['difference'])} | {pct(value['error_difference'])} |"
            )
        text += [
            "",
            "The fresh Pick b1-vs-b0 gain is nine maintained successes among46 already-successful starts (+19.57pp, paired interval[9.52,28.30]pp), with no failed-start gain (6/20 at either budget). Strict CART2 makes the same264 task/checkpoint/budget decisions as DSRE. DSRE uses52 literals across38 b1 Pick recommendations, CART2 uses76; the ordinary exact rule matches DSRE's brevity. Provisional .9 CART succeeds53/66 with no observed error versus DSRE38/66; its standard is empirical leaf purity rather than strict reference universality. This adverse comparison remains explicit.",
            "",
            "Empirical zero-error bootstrap intervals can collapse to[0,0] because resampling cannot invent unseen failures. They are not population error bounds or proof of equivalence. Only five independent fresh parents receive strict recovery under either budget; b1 continue assignments number33, and Push strict assignments are zero. Both fall short of interpreting this as the earlier independent42-parent calibration stratum requirement.",
            "",
            "### Computational cost",
            "",
            "| Task | Budget | Method | Prebuilt-reference call median ms | Maximum ms |",
            "|---|---:|---|---:|---:|",
        ]
        for key, value in load(root / "fresh_query_runtime.json").items():
            if not key.endswith(("|DSRE", "|B7", "|CART2_strict")):
                continue
            task, budget, method = key.split("|")
            text.append(
                f"| {task} | {budget} | {method} | {value['median_ms']:.3f} | {value['max_ms']:.3f} |"
            )
        text += [
            "",
            "These are measured Python call wall times on the local CPU with already built reference/index and repeated signatures; they include witness generation for DSRE, and are not sensor latency, hardware real-time guarantees, or a controlled speed superiority experiment. The old sealed cold-query measurements remain in the earlier `runtime.json`. There are8 new small frozen CART fits, no neural/controller training. Primary cost is actual selected predicate count: Pick b0=0,b1=1; Push b0=b1=0 by minimum-cost ties.",
            "",
            "The wrapper exited143 (SIGTERM15) without finalizing its resource row. The cause is unknown; no qualification failure, OOM or timeout is invented. Completed data are retained, the sole incomplete parent is not replenished, and no physics is relaunched. Exactly266 completed action continuations are retained, of which264 belong to complete primary parents. At most two additional action attempts could have begun in the single incomplete cell, but their unwritten progress is unknown. Exact interrupted-physics CPU usage is unavailable. Its wall interval and the accounting gap are recorded in `physics_interruption.json`; resource completeness is qualified, not silently imputed.",
            "",
        ]
    else:
        text += [
            "Physics and the prospective audit are still pending. This intermediate report makes no fresh result claim and is not a completion deliverable.",
            "",
        ]
    text += [
        "## Reproduction and artifacts",
        "",
        "Historical evidence is read-only. Use a **new empty evidence root** and non-overlapping preregistered seeds for any new physics campaign; do not rerun this completed root or replace seeds. Preparation refuses an existing freeze, physics refuses an existing start marker, and sealed roots are immutable. The commands below replay analysis only, not physics.",
        "",
        "```bash",
        f"SOURCE={root}",
        "R=$(mktemp -d /tmp/dsre-review-XXXXXX)",
        'cp "$SOURCE"/physics_completed.json "$SOURCE"/fresh_qualified.jsonl "$SOURCE"/fresh_seed_manifest.json "$SOURCE"/frozen_routers.json "$SOURCE"/confirmation_freeze.json "$R"/',
        "export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1",
        'uv run --no-sync python scripts/dsre_paper_reanalysis.py --root "$R"',
        'uv run --no-sync python scripts/dsre_paper_confirmation.py --root "$R"',
        "uv run --no-sync python scripts/dsre_paper_figures.py",
        'uv run --no-sync python scripts/dsre_paper_report.py --root "$R"',
        "tectonic --untrusted --keep-logs --outdir rss2027 rss2027/dsre_stage1.tex",
        "uv run --no-sync pytest -q tests/test_dsre_paper.py",
        "```",
        "",
        "For an immutable completed run, copy the sealed analysis inputs to a separate scratch root and use the verification command in the final manifest; do not overwrite sealed outputs. The exact actual worker commands and CPU/RSS accounting are in `commands.jsonl`; compiler/download provenance is in `template/` and the final resources file. The compact supervisor archive excludes raw trajectories, caches and logs; they remain in this local evidence root. The archive contains scientific tables, provenance, audit, source and paper for review.",
        "",
        "## Interpretation, readiness and remaining work",
        "",
        "H1 is supported only as finite representation refinement on Pick; H2 is structural; H3 is directly illustrated by Push; H4 is evidenced by held-out strict errors. New prospective results must be interpreted separately from the reused folds. There is no evidence that explanation generation itself improves a physical recovery policy, installs a sensor, estimates causal root causes, establishes safety, or improves human understanding.",
        "",
        "The complete anonymous Stage1 draft is a reviewable artifact. Formal page/template compliance is not research readiness. Remaining scientific weaknesses include identity with exact ordinary rules, modest/negative failed-start gains, menu-dependent Push collapse, two idealized simulated tasks, horizon-specific binary utility, rare recovery assignment, and absent independent deployment calibration. The principal researcher retains the submission decision. No manuscript is submitted, pushed or sent to an external service.",
        "",
    ]
    Path("docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md").write_text("\n".join(text))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    report(parser.parse_args().root)
