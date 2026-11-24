"""Render audited frozen-source results, scoped tables and figures, without paper edits."""

import argparse
import csv
import json
from pathlib import Path

from dsre_followup_batch import read, sha


def estimate(row, unit="%"):
    if row["estimate"] is None:
        return "undefined"
    return f"{100 * row['estimate']:.2f}{unit} [{100 * row['lower']:.2f}, {100 * row['upper']:.2f}]"


def render(root):
    assert read(root / "independent_numerical_audit.json")["passed"]
    result = read(root / "test_analysis.json")
    cal = read(root / "calibration_decision.json")
    plan = read(root / "study_plan.json")
    assert cal["complete_cohort"] and cal["calibration_parents"] == 256
    assert read(root / "calibration_decision_audit.json")["passed"]
    methods = plan["methods"]
    tables = result["tables"]
    proposals = [
        "| Uncalibrated clean proposal | C / R / STOP | Adequate / inadequate | Required selected / eligible |",
        "|---|---:|---:|---:|",
    ]
    for method in (
        "DSRE_strict",
        "DSRE_risk",
        "B7_risk",
        "CART2_beta10",
        "B5_beta10",
        "B1_two_strict",
        "B0_continue",
        "B0_recover",
    ):
        c = tables[f"clean|proposal|{method}|ALL"]["counts"]
        proposals.append(
            f"| {method} | {c['continue']} / {c['recover']} / {c['stop']} | {c['adequate']} / {c['inadequate']} | {c['required_selected']} / {c['required_total']} |"
        )
    status = (
        "RUNTIME_QUALIFIED_AND_DATA_COMPLETE"
        if result["complete_cohort"]
        else "RUNTIME_QUALIFIED_COHORT_INCOMPLETE"
    )
    cal_lines = [
        "| Method | Action | Assigned parents | Error parents | Exact upper | Enabled |",
        "|---|---|---:|---:|---:|---|",
    ]
    for method in methods:
        for action in ("continue", "recover"):
            s = cal["strata"][method + "|" + action]
            cal_lines.append(
                f"| {method} | {action} | {s['assigned_parents']} | {s['error_parents']} | {100 * s['upper']:.3f}% | {s['enabled']} |"
            )
    count_lines = [
        "| Clean gated method | C / R / STOP | Adequate / inadequate | Required selected / eligible | Coverage, 95% CI | Completion, 95% CI |",
        "|---|---:|---:|---:|---|---|",
    ]
    conditional = [
        "| Clean gated method | Conditional success, 95% CI | Selected R harm | Both-success completions | Initially successful maintenance |",
        "|---|---|---:|---:|---:|",
    ]
    for method in methods:
        entry = tables[f"clean|gated|{method}|ALL"]
        c, ci = entry["counts"], entry["intervals"]
        count_lines.append(
            f"| {method} | {c['continue']} / {c['recover']} / {c['stop']} | {c['adequate']} / {c['inadequate']} | {c['required_selected']} / {c['required_total']} | {estimate(ci['coverage'])} | {estimate(ci['unconditional_completion'])} |"
        )
        conditional.append(
            f"| {method} | {estimate(ci['conditional_success'])} | {c['harmful_recover']} | {c['both_success_maintained']} | {c['initial_success_maintained']} |"
        )
    held_out_bounds = [
        "| Clean gated method | Action | Assigned parents | Error parents | Test exact upper (descriptive) |",
        "|---|---|---:|---:|---:|",
    ]
    for method in ("DSRE_risk", "CART2_beta10", "B7_risk", "B1_two_strict"):
        for action in ("continue", "recover"):
            row = result["test_parent_action_bounds"]["gated"][method + "|" + action]
            held_out_bounds.append(
                f"| {method} | {action} | {row['assigned_parents']} | {row['error_parents']} | {100 * row['upper']:.3f}% |"
            )
    matched = [
        "| Uncalibrated proposal | Recoveries | Matched net successful recoveries versus continue | Effect per selected recovery, 95% CI | Harmful recoveries |",
        "|---|---:|---:|---|---:|",
    ]
    for method in ("DSRE_risk", "CART2_beta10", "B5_beta10", "B0_recover"):
        row = tables[f"clean|proposal|{method}|ALL"]
        c = row["counts"]
        matched.append(
            f"| {method} | {c['recover']} | {c['matched_recovery_gain']} | {estimate(row['intervals']['matched_recovery_effect'])} | {c['harmful_recover']} |"
        )
    populations = [
        "| Condition | Checkpoints | C-only | R-only | Both | Neither | Initially unsuccessful | Required recovery |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("ALL", *(p[0] for p in plan["profiles"])):
        c = result["paired_outcome_categories"][name]
        populations.append(
            "| "
            + name
            + " | "
            + " | ".join(
                str(c.get(k, 0))
                for k in (
                    "rows",
                    "continue_only",
                    "recover_only",
                    "both_success",
                    "neither_success",
                    "initially_unsuccessful",
                    "required_recovery",
                )
            )
            + " |"
        )
    effects = [
        "| Paired DSRE risk minus comparator | Completion difference, 95% CI | Required-recovery recall difference, 95% CI |",
        "|---|---|---|",
    ]
    for method in (
        "CART2_beta10",
        "B7_risk",
        "B5_beta10",
        "B1_two_strict",
        "DSRE_strict",
    ):
        comparisons = result["paired_contrasts"]
        effects.append(
            f"| {method} | {estimate(comparisons[f'DSRE_risk_minus_{method}|ALL|completion'], ' pp')} | {estimate(comparisons[f'DSRE_risk_minus_{method}|ALL|required_recovery_recall'], ' pp')} |"
        )
    condition_lines = [
        "| Condition and gated method | Adequate / inadequate / STOP | Required selected / eligible |",
        "|---|---:|---:|",
    ]
    for condition, _ in plan["profiles"]:
        for method in ("DSRE_risk", "CART2_beta10"):
            c = tables[f"clean|gated|{method}|{condition}"]["counts"]
            condition_lines.append(
                f"| {condition}, {method} | {c['adequate']} / {c['inadequate']} / {c['stop']} | {c['required_selected']} / {c['required_total']} |"
            )
    noise = [
        "| Offline 5-mm DSRE risk proposal | Mode | Adequate / inadequate / STOP | False / asserted literals | Required selected / eligible |",
        "|---|---|---:|---:|---:|",
    ]
    for scenario in (
        "bound005",
        "uniform0.005_r0",
        "uniform0.005_r1",
        "uniform0.005_r2",
    ):
        for mode in ("proposal", "robust_proposal"):
            c = tables[f"{scenario}|{mode}|DSRE_risk|ALL"]["counts"]
            noise.append(
                f"| {scenario} | {mode} | {c['adequate']} / {c['inadequate']} / {c['stop']} | {c['false_assertions']} / {c['literals']} | {c['required_selected']} / {c['required_total']} |"
            )
    ceilings = result["hindsight"]
    reference = result["frozen_reference"]
    certs = read(root / "test_certificate_witnesses.json")
    witness_types = {}
    for packet in certs:
        if packet["diagnosis"]:
            for obstruction in packet["diagnosis"].get("obstructions", []):
                kind = obstruction["kind"]
                witness_types[kind] = witness_types.get(kind, 0) + 1
    main = tables["clean|gated|DSRE_risk|ALL"]["counts"]
    cart = tables["clean|gated|CART2_beta10|ALL"]["counts"]
    lines = [
        "# DSRE: frozen independent source-risk study results",
        "",
        f"Status: **{status}**.",
        "",
        f"Evidence root: `{root}`. The runtime/source qualification passes; calibration completes 256/256 independent parents, 1,280 checkpoints and 2,560 continuations. Testing completes {result['parents']}/128 parents, {result['checkpoints']} checkpoints and {2 * result['checkpoints']} continuations. Missing planned test parents: {128 - result['parents']}. No parent or condition was replaced.",
        "",
        f"The sealed DSRE risk gate completes {main['adequate']}/{main['rows']} test checkpoints, issues {main['inadequate']} inadequate actions and defers {main['stop']}; it selects {main['required_selected']}/{main['required_total']} necessary recoveries. CART2 completes {cart['adequate']}/{cart['rows']} with {cart['inadequate']} inadequate actions and {cart['stop']} deferrals under the same independent calibration. The paired completion difference is {estimate(result['paired_contrasts']['DSRE_risk_minus_CART2_beta10|ALL|completion'], ' pp')}. Recovery is disabled by calibration, so this study does not establish a qualified physical-recovery improvement. Raw intervention proposals and their actual gains/errors remain separate below.",
        "",
        "The sole execution correction selects the already installed Lavapipe ICD in dedicated children. DSRE, the original skills, seven-fact interface, condition offsets, thresholds, router, action tie, controller and terminal-success endpoint remain unchanged. No model training or manuscript edit occurred.",
        "",
        "## Independent action-specific calibration",
        "",
        "Each n/k is a count of independent assigned/error parents, not checkpoints: assignment is any of five conditions; error is any failed assigned condition. Complete 256-parent calibration is mandatory. The target remains 10%, delta=.05/68 per claim, preserving the conservative family allocation. Upper=1 at n=0 is uninformative, not a measured 100% failure rate. No old-data pooling, enrichment or noise transfer occurs.",
        "",
        *cal_lines,
        "",
        "## Untouched test populations and physical outcomes",
        "",
        *populations,
        "",
        "Required recovery means initially unsuccessful, continue unsuccessful, recover successful. Initially successful R-only cases are preventive, and both-success cases do not establish necessity. All alternatives were physically executed from the same fully reconstructed predecision state for 70 controls. STOP gets zero selective completion credit; no STOP outcome is imputed.",
        "",
        "## Frozen selective execution and strongest baselines",
        "",
        *proposals,
        "",
        "The proposal table is descriptive and unqualified. It retains raw strict/provisional differences and the actual always-continue/recover alternatives. The following gate table applies the independently sealed action eligibility without rerouting.",
        "",
        *count_lines,
        "",
        *conditional,
        "",
        *held_out_bounds,
        "",
        "Test bounds use the registered parent-any-assignment unit and conservative allocation, but never revise calibration eligibility. Zero assignments have an uninformative upper bound of one. The complete calibration and test populations remain disjoint.",
        "",
        "A zero observed error count yields a degenerate empirical bootstrap band, not proof of zero population risk. The exact parent-action bounds retain nonzero uncertainty; checkpoint bootstrap intervals do not replace those simultaneous risk limits.",
        "",
        *matched,
        "",
        "These matched recovery effects describe uncalibrated proposals, not qualified deployment. A disabled recovery gate yields no selected recovery and an undefined effect per selected recovery. Positive raw net effects cannot establish that the risk-gated policy successfully recovered failures.",
        "",
        "The same 256 calibration parents and per-action risk standard are available to all 17 methods. CART2_beta10 is the frozen depth-two risk tree; B5_beta10 and B1_two_strict retain their original rule semantics. Full_signature_strict uses the labeled extra-information 12-fact interface and is not a matched-seven-fact superiority comparator. Fixed controls are descriptive proposals unless their own action gate qualifies. A gated table includes STOP policies with no enabled action; it does not imply all methods qualified.",
        "",
        "## Paired uncertainty and condition-specific results",
        "",
        *effects,
        "",
        *condition_lines,
        "",
        "Intervals use 4,000 paired parent resamples, PCG64 seed 2026111602. All five conditions and sensor replicates remain with their parent. These descriptive percentile 95% intervals do not assert a multiplicity-adjusted superiority test. B7 exactly agrees with DSRE under both strict and risk routing, including clean gates. Negative differences and equivalences are retained.",
        "",
        "## Observation support and skills",
        "",
        f"The frozen reference contains {reference['reference_rows']} rows, with physical action-feasible mass {reference['reference_action_feasible_mass']} and seven-fact common-action signature mass {reference['reference_common_action_signature_mass']}. This is a finite-reference partition statement, not a population risk guarantee or a test ceiling.",
        "",
        "Test-outcome hindsight ceilings, reported only diagnostically: "
        + "; ".join(
            f"{n} facts: {p['common_action_signature_mass']}/{p['rows']} common-action mass versus {p['action_mass']}/{p['rows']} action-feasible mass"
            for n, p in ceilings.items()
        )
        + ". These do not deploy hindsight actions or thresholds.",
        "",
        f"Frozen-reference strict certificates and typed witnesses are retained for all {len(certs)} test checkpoints in `test_certificate_witnesses.json`; obstruction counts may overlap: `{json.dumps(witness_types, sort_keys=True)}`. Independent enumeration verifies minimum evidence and necessity/insufficiency witnesses on every distinct observed query. Missing support never becomes a positive certificate.",
        "",
        "A REPERTOIRE_INADEQUATE witness identifies a qualified neither-success reference row compatible with the observed signature. It does not assert that the current test checkpoint itself has no adequate skill. The actual neither-success test population is reported separately above; reference insufficiency and physical infeasibility must not be conflated.",
        "",
        "## Measurement diagnostic: NOT QUALIFIED",
        "",
        *noise,
        "",
        "These are offline proposals reusing the same physical pairs. Uniform replicates are correlated measurement repetitions, not new independent robot parents. Bound005 is the clean-centered declared 5-mm uncertainty box. No clean risk certificate covers altered inputs, and factual-literal correctness alone does not establish action risk. All 1/5-mm methods remain in the full machine-readable tables.",
        "",
        "## Mechanism, cost and limitations",
        "",
        "Every policy is evaluated on identical saved input packets and the same physically paired fixed interventions. Both branches reconstruct the same complete prefix and canonical controller/RNG state; no policy receives an additional helpful prefix. Any difference is action selection/abstention under this source, not an improved controller or a new recovery skill. Selected-recovery gain versus matched continue, maintenance and unnecessary harm are separately retained in the metric tables.",
        "",
        "Source-specific bounds assume independent seed-parent resets, the fixed five-condition distribution, clean telemetry and continued source fidelity. They are not real-world safety or individual-checkpoint guarantees. A wide held-out bound never changes the sealed calibration gate. Necessary-recovery coverage and risk refusal remain separate scientific findings.",
        "",
        "Computational cost is in `resource_accounting.json`, per-parent progress and chunk meters. Raw `route_ms` measures the full frozen nine-scenario point/robust routing bundle; it must not be presented as single-method online latency. No GPU model training, paid API or model download is used.",
        "",
        "## Audit, preservation and reproduction",
        "",
        "The physical auditor independently recomputes action equations, all branch labels and complete source replay. The separate numerical auditor imports no production selector or simulator: it rebuilds all metric records from raw outcomes/sealed decisions, verifies exact risk limits independently, checks minimum certificates/witnesses, and reproduces grouped intervals by direct indexed resampling. Its report explicitly identifies frozen controls without a separate route reimplementation; all 17 numerical outcomes and counts are audited.",
        "",
        "Old source/evidence seals, user changes, `.gitignore`, `uv.lock` and manuscripts are preserved. Raw traces/logs remain local. The completion manifest gives exact source hashes, archive paths, tests, failed checks, resource debit, branch/commit and worker-exit verification. No public push, issue, submission or manuscript revision occurs.",
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dual-rec-uv-cache",
        "export PYTHONPATH=src:scripts:/home/imad/Desktop/IEEE-RAL/results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages",
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1",
        "mkdir /tmp/dsre-runtime-portable-review-20261116",
        "tar -xzf docs/dsre_runtime_source_risk_review.tar.gz -C /tmp/dsre-runtime-portable-review-20261116",
        "uv run --no-sync python /tmp/dsre-runtime-portable-review-20261116/source/scripts/dsre_source_risk_verify_packet.py /tmp/dsre-runtime-portable-review-20261116",
        "uv run --no-sync pytest -q tests",
        "```",
        "",
        "Use a fresh empty extraction directory. The portable check is read-only. Full trajectory-audit and analysis entrypoints are `dsre_source_risk_audit.py --stage test`, `dsre_source_risk_terminal_audit.py --stage test`, `dsre_source_risk_analysis.py`, and `dsre_source_risk_numerical.py`, each taking the run root before options. They write audit outputs, so reproduce them only on a disposable copy of the full local raw evidence with the original frozen source available; do not overwrite sealed evidence. Exact executed commands and resource meters are retained under R/metered.",
        "",
        "Do not rerun started physics parents or unseal the old failed root. The runtime correction is independently qualified; statistical qualification is action-specific and reported above without a favorable-result requirement.",
    ]
    Path("docs/DSRE_SOURCE_RISK_COMPLETION.md").write_text("\n".join(lines) + "\n")
    with (root / "calibration_table.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["method_action", "assigned_parents", "error_parents", "upper", "enabled"]
        )
        for key, row in cal["strata"].items():
            writer.writerow(
                [
                    key,
                    row["assigned_parents"],
                    row["error_parents"],
                    row["upper"],
                    row["enabled"],
                ]
            )
    (root / "report_source_binding.json").write_text(
        json.dumps(
            {
                "analysis_sha256": sha(root / "test_analysis.json"),
                "numerical_audit_sha256": sha(
                    root / "independent_numerical_audit.json"
                ),
                "report_sha256": sha(Path("docs/DSRE_SOURCE_RISK_COMPLETION.md")),
                "status": status,
            },
            indent=2,
        )
        + "\n"
    )
    return result, cal


def figures(root, result, cal):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 9})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    ax = axes[0]
    for action, color in (("continue", "#3677a5"), ("recover", "#bd673d")):
        for method in read(root / "study_plan.json")["methods"]:
            row = cal["strata"][method + "|" + action]
            ax.scatter(
                row["assigned_parents"],
                100 * row["upper"],
                s=24,
                color=color,
                marker="o" if row["enabled"] else "x",
                alpha=0.7,
            )
            if method == "DSRE_risk":
                ax.annotate(
                    "DSRE " + action,
                    (row["assigned_parents"], 100 * row["upper"]),
                    xytext=(
                        -3 if action == "continue" else 3,
                        8 if action == "continue" else -13,
                    ),
                    ha="right" if action == "continue" else "left",
                    textcoords="offset points",
                    fontsize=7,
                )
    ax.axhline(10, color="#a34a45", linestyle="--", linewidth=1)
    ax.set(
        xlim=(-8, 270),
        ylim=(-3, 107),
        xlabel="Independent assigned calibration parents",
        ylabel="Exact parent-action upper bound (%)",
        title="Clean calibration: ○ enabled; × disabled",
    )
    ax.text(
        0.08,
        0.96,
        "n=0 upper=100% is uninformative",
        transform=ax.transAxes,
        va="top",
        fontsize=7,
    )
    ax = axes[1]
    table = result["tables"]
    no_actions, risks = 0, []
    for method in read(root / "study_plan.json")["methods"]:
        row = table[f"clean|gated|{method}|ALL"]
        ci = row["intervals"]["conditional_success"]
        if ci["estimate"] is None:
            no_actions += 1
            continue
        x = row["intervals"]["coverage"]["estimate"] * 100
        y = (1 - ci["estimate"]) * 100
        risks.append(y)
        ax.scatter(x, y, s=25, color="#3677a5", alpha=0.6)
        if method in ("DSRE_risk", "CART2_beta10"):
            risks.append(100 * (1 - ci["lower"]))
            ax.errorbar(
                x,
                y,
                yerr=[
                    [100 * (ci["upper"] - ci["estimate"])],
                    [100 * (ci["estimate"] - ci["lower"])],
                ],
                color="#3677a5",
                linewidth=0.6,
                capsize=2,
            )
            ax.annotate(
                method.replace("_beta10", " risk").replace("_risk", " risk"),
                (x, y),
                xytext=(-3 if method == "DSRE_risk" else 3, -12),
                ha="right" if method == "DSRE_risk" else "left",
                textcoords="offset points",
                fontsize=7,
            )
    for i in range(3):
        row = table[f"uniform0.005_r{i}|robust_proposal|DSRE_risk|ALL"]
        if row["intervals"]["conditional_success"]["estimate"] is None:
            continue
        x = row["intervals"]["coverage"]["estimate"] * 100
        y = (1 - row["intervals"]["conditional_success"]["estimate"]) * 100
        risks.append(y)
        ax.scatter(
            x,
            y,
            facecolors="none",
            edgecolors="#888888",
            marker="s",
            s=30,
            label="5-mm offline, NOT QUALIFIED" if i == 0 else None,
        )
    ax.set(
        xlim=(-3, 103),
        ylim=(-1.5, max(10, 1.3 * max(risks, default=0))),
        xlabel="Held-out accepted coverage (%)",
        ylabel="Checkpoint error among selected (%)",
        title="Held-out descriptive risk–coverage",
    )
    ax.text(
        0.03,
        0.96,
        f"{no_actions} all-STOP policies: error undefined",
        transform=ax.transAxes,
        va="top",
        fontsize=7,
    )
    ax.legend(fontsize=6, loc="upper right", bbox_to_anchor=(1, 0.84))
    fig.tight_layout()
    dest = Path("docs/figures")
    for ext in ("png", "pdf"):
        fig.savefig(
            dest / ("dsre_recovered_source_risk." + ext), dpi=300, bbox_inches="tight"
        )
    plt.close(fig)
    (root / "figure_source_data.json").write_text(
        json.dumps(
            {
                "analysis_sha256": sha(root / "test_analysis.json"),
                "calibration_sha256": sha(root / "calibration_decision.json"),
                "left": "All17 clean method/action calibration strata; n=0 convention explicit",
                "right": "Descriptive checkpoint-conditional inadequacy versus accepted coverage; clean gated policies and all3 fixed5mm robust DSRE replicates. Distinct from left-hand parent-action risk bound. Noisy proposals unqualified, all-STOP errors undefined, all methods share physical pairs. Vertical bars: marginal95% parent-bootstrap uncertainty for DSRE/CART2.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    results, calibration = render(args.root)
    figures(args.root, results, calibration)
