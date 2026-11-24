"""Render independently verified dual-obligation results without manuscript edits."""

import argparse
import csv
import gzip
import json
from pathlib import Path

from dsre_dual_adjudication import read, sha, write_once


def estimate(value, unit="%"):
    if value["estimate"] is None:
        return "undefined"
    return f"{100 * value['estimate']:.2f}{unit} [{100 * value['lower']:.2f}, {100 * value['upper']:.2f}]"


def table(headers, rows):
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "---|" * len(headers),
        *(
            "| " + " | ".join(str(cell).replace("|", r"\|") for cell in row) + " |"
            for row in rows
        ),
    ]


def render(root):
    assert read(root / "independent_dual_numerical_audit.json")["passed"]
    result = read(root / "dual_results.json")
    cal = read(root / "dual_calibration.json")
    old = read(root / "prior_replication.json")
    main = result["tables"]["DSRE_nondegradation|ALL"]
    absolute = result["tables"]["DSRE_absolute|ALL"]
    cart = result["tables"]["CART2_nondegradation|ALL"]
    raw_cart = result["tables"]["CART2_raw|ALL"]["counts"]
    fixed_recover = result["tables"]["always_recover|ALL"]["counts"]
    primary = result["comparisons"][
        "DSRE_nondegradation_minus_DSRE_absolute|ALL|completion"
    ]
    versus_cart = result["comparisons"][
        "DSRE_nondegradation_minus_CART2_nondegradation|ALL|completion"
    ]
    rows = []
    for key, bound in cal["bounds"].items():
        rows.append(
            [
                key,
                bound["assigned_parents"],
                bound["error_parents"],
                f"{100 * bound['upper']:.3f}%",
                bound["qualified"],
            ]
        )
    populations = []
    for condition, c in result["paired_outcomes"].items():
        populations.append(
            [
                condition,
                c["rows"],
                c.get("C_ONLY", 0),
                c.get("R_ONLY", 0),
                c.get("BOTH", 0),
                c.get("NEITHER", 0),
                c["initially_unsuccessful"],
                c["required"],
            ]
        )
    actions, interventions, effects = [], [], []
    for key, entry in result["tables"].items():
        if not key.endswith("|ALL"):
            continue
        name, c, ci = key.removesuffix("|ALL"), entry["counts"], entry["intervals"]
        actions.append(
            [
                name,
                f"{c['continue']} / {c['recover']} / {c['stop']}",
                f"{c['success']} / {c['failure']}",
                estimate(ci["completion"]),
                estimate(ci["conditional_success"]),
            ]
        )
        interventions.append(
            [
                name,
                f"{c['required_selected']} / {c['required']}",
                c["initial_failure_R"],
                c["preventive_R_only"],
                c["harm_R"],
                c["futile_R"],
                c["both_success_R"],
                c["both_success_maintained"],
                c["futile_recovery_controls"],
            ]
        )
    for a, b in (
        ("DSRE_nondegradation", "DSRE_absolute"),
        ("CART2_nondegradation", "CART2_absolute"),
        ("DSRE_nondegradation", "CART2_nondegradation"),
        ("DSRE_nondegradation", "B7_nondegradation"),
        ("DSRE_nondegradation", "always_continue"),
        ("DSRE_nondegradation", "always_recover"),
        ("DSRE_nondegradation", "DSRE_historical"),
    ):
        base = a + "_minus_" + b + "|ALL|"
        effects.append(
            [
                a + " minus " + b,
                estimate(result["comparisons"][base + "completion"], " pp"),
                estimate(
                    result["comparisons"][base + "required_recovery_recall"], " pp"
                ),
                estimate(result["comparisons"][base + "futile_recovery_burden"], " pp"),
            ]
        )
    exploratory, decompositions, partitions = [], [], []
    for stage in ("calibration", "test"):
        old_data = old["reports"][stage]["DSRE"]
        exploratory.append(
            [
                stage,
                old_data["classes"].get("R_ONLY", 0),
                old_data["classes"].get("NEITHER", 0),
                old_data["classes"].get("C_ONLY", 0),
                old_data["classes"].get("BOTH", 0),
                old_data["assigned_parents"],
                estimate(old_data["intervals"]["parent_failure_minus_harm"]),
            ]
        )
        fresh = read(root / (stage + "_decomposition.json"))
        for method in ("DSRE", "CART2"):
            d = fresh[method]
            decompositions.append(
                [
                    stage,
                    method,
                    d["proposed_recover_cells"],
                    d["assigned_parents"],
                    d["absolute_error_parents"],
                    d["harm_error_parents"],
                    estimate(d["intervals"]["parent_failure_minus_harm"]),
                    estimate(d["intervals"]["cell_failure_minus_harm"]),
                ]
            )
        for width, part in fresh["partitions"].items():
            partitions.append(
                [
                    stage,
                    width,
                    part["rows"],
                    part["action_feasible_rows"],
                    part["physically_infeasible_rows"],
                    part["common_action_signature_mass"],
                    part["pure_observational_ambiguity_mass"],
                    part["feasible_rows_in_signatures_containing_infeasible_reference"],
                ]
            )
    selected = main["counts"]
    witness_rows = []
    for category in ("R_ONLY", "NEITHER", "C_ONLY"):
        witness = next(
            (
                w
                for w in sorted(
                    read(root / "physical_witnesses.json").values(),
                    key=lambda item: item["policy"] != "DSRE_nondegradation",
                )
                if (w["c"], w["r"])
                == {
                    "R_ONLY": (False, True),
                    "NEITHER": (False, False),
                    "C_ONLY": (True, False),
                }[category]
            ),
            None,
        )
        if witness:
            witness_rows.append(
                [
                    category,
                    witness["seed"],
                    witness["condition"],
                    witness["initial_success"],
                    witness["c"],
                    witness["r"],
                    witness["policy"],
                    witness["source_sha256"][:16],
                ]
            )
    lines = [
        "# DSRE: independent dual-obligation results",
        "",
        f"Scientific outcome: **{result['status']}**. Evidence: `{root}`.",
        "",
        "All 256 fresh calibration parents and 128 untouched test parents completed all five conditions and both fixed actions: 1,920 paired checkpoints and 3,840 continuations. Three historical parents separately passed fresh-process qualification (15 checkpoints, 30 continuations, 2,100 future states). No seed was replaced or method retuned.",
        "",
        f"The non-degradation DSRE composition completes {selected['success']}/640 versus {absolute['counts']['success']}/640 under the new absolute composition; paired difference {estimate(primary, ' pp')}. It selects {selected['required_selected']} of {selected['required']} necessary recoveries, attempts {selected['recover']} recoveries, incurs {selected['harm_R']} binary-outcome harms and {selected['futile_R']} neither-success attempts, and defers {selected['stop']} checkpoints. CART2's non-degradation composition completes {cart['counts']['success']}/640; paired DSRE-minus-CART2 difference {estimate(versus_cart, ' pp')}. B7 is exactly identical to DSRE.",
        "",
        "## Exploratory source-blind replication of old evidence",
        "",
        *table(
            [
                "Old cohort",
                "R-only",
                "Neither",
                "Harm",
                "Both",
                "Assigned parents",
                "Parent failure-minus-harm,95% CI",
            ],
            exploratory,
        ),
        "",
        f"These old data motivated the question and do not support a new qualification. The old zero-harm 66-parent bound at .05/68 is {100 * old['old_zero_harm_66_parent_bound_at_original_delta']:.3f}%, above 10%. Compact labels agree with raw matched branches and independent geometry/velocity endpoint checks. The preserved audit correction concerned a calibration-only condition assertion: old test's ten neither-success proposals are nine at minus2cm and one at plus3cm. The zero-harm counts were correct.",
        "",
        "## Fresh six-claim calibration",
        "",
        *table(
            ["Claim", "Assigned parents", "Error parents", "Exact upper", "Qualified"],
            rows,
        ),
        "",
        "All six claims share target 10% and delta=.05/6. The parent unit is any assignment/any error across five conditions; n=0 is uninformative and disabled. The new absolute and harm obligations have identical assigned support within each router and the same alpha allocation. Thus their within-router difference is an error-definition difference, not an alpha change. The old .05/68 gate remains unchanged and is descriptive on these new data. No new absolute guarantee is inherited from that file. B7 uses DSRE's existing verdict, and fixed actions have no new qualification.",
        "",
        *table(
            [
                "Fresh cohort",
                "Router",
                "R cells",
                "Assigned parents",
                "Absolute-error parents",
                "Harm-error parents",
                "Parent failure-minus-harm,95% CI",
                "Checkpoint failure-minus-harm,95% CI",
            ],
            decompositions,
        ),
        "",
        "At a checkpoint absolute failure is the disjoint union of harm and neither-success. At a parent their unions may overlap: the absolute-minus-harm parent gap counts futile-error parents without harm. Cohorts are never pooled. Test estimates are descriptive and never change gates.",
        "",
        "## Untouched paired physical outcome populations",
        "",
        *table(
            [
                "Condition",
                "Cells",
                "C-only",
                "R-only",
                "Both",
                "Neither",
                "Initially failed",
                "Required recovery",
            ],
            populations,
        ),
        "",
        "Required recovery is initially unsuccessful R-only; preventive R-only and both-success maintenance receive separate counts. The primary policies use saved prospective sidecar decisions sealed for all 128 parents before any test future. Both alternatives were physically executed from the same full reconstructed prefix, controller/RNG and model state. This is fixed single-intervention evaluation, not a newly trained controller or a full closed-loop recovery system.",
        "",
        "## Selected actions, task completion and abstention",
        "",
        *table(
            [
                "Policy",
                "C/R/STOP",
                "Successful/unsuccessful",
                "Completion,95% CI",
                "Conditional success,95% CI",
            ],
            actions,
        ),
        "",
        "Absolute and nondegradation use new six-claim calibration. Historical rows apply the unchanged old gate descriptively; raw and fixed rows are unqualified comparisons. STOP receives zero selective-completion credit with no invented hold, escalation or reset outcome. Zero observed errors can yield degenerate empirical bootstrap intervals; they do not prove zero population risk.",
        "",
        *table(
            [
                "Policy",
                "Required selected/eligible",
                "R on initial failure",
                "Preventive R-only",
                "Harmful R",
                "Futile R",
                "Both-success R",
                "Both-success maintained C/R",
                "Futile R controls",
            ],
            interventions,
        ),
        "",
        f"For non-degradation DSRE, useful required recoveries per attempted R are {estimate(main['intervals']['useful_recoveries_per_R'])}, required-recovery recall is {estimate(main['intervals']['required_recovery_recall'])}, and useful recoveries per initially failed checkpoint are {estimate(main['intervals']['recovery_per_failed_start'])}. These separate useful interventions from maintaining an already-successful episode.",
        "",
        f"Futile recovery burden is {selected['futile_R']}/{selected['recover']} attempted recoveries, {estimate(main['intervals']['futile_per_R'])}, corresponding to {selected['futile_recovery_controls']} fixed controls. Every R alternative uses 70 controls, as does C: this is recovery-work accounting, not an incremental energy/time, collision, damage or cost-to-completion model.",
        "",
        "## Paired comparisons at matched information and risk",
        "",
        *table(
            [
                "Contrast",
                "Completion difference,95% CI",
                "Required-recovery recall difference,95% CI",
                "Futile-attempt burden difference,95% CI",
            ],
            effects,
        ),
        "",
        "All descriptive 95% intervals use 4,000 paired parent resamples, PCG64 seed 2026111603, retaining five conditions together. The six exact calibration bounds alone define the simultaneous qualification family. Test intervals add no certification, tuning or favorable superiority threshold. Both branches use the same prefix; no comparison gains an additional helpful prefix.",
        "",
        "## Observation sufficiency versus action infeasibility",
        "",
        *table(
            [
                "Cohort",
                "Facts",
                "Rows",
                "Action feasible",
                "Neither",
                "Common-action signature mass",
                "Pure ambiguity mass",
                "Feasible mass sharing a signature with neither",
            ],
            partitions,
        ),
        "",
        "These are descriptive hindsight partitions of saved 7/12-fact observations, not deployed rules, risk bounds or new feature selection. A frozen-reference repertoire witness identifies a compatible inadequate reference state and does not prove the actual test checkpoint is physically infeasible. The original finite-reference minimum certificates, necessity/insufficiency witnesses and strict/provisional B7 identities are independently checked without redefining adequacy. No new minimum non-degradation certificate is claimed.",
        "",
        "## Literal physical episode witnesses",
        "",
        *table(
            [
                "Class",
                "Parent",
                "Condition",
                "Initial success",
                "C",
                "R",
                "Selected by",
                "Screen SHA256 prefix",
            ],
            witness_rows,
        ),
        "",
        "Full predecision evidence literals, object/goal positions and both terminal states are preserved in physical_witnesses.json; old witnesses are in prior_replication.json. Labels are independently recomputed from the unchanged 25-mm goal-distance and 0.2 arm-velocity endpoint. A neither-success recovery is unsuccessful even when its binary non-degradation error is zero; a C-only recovery harms task success even without any measured robot-safety outcome.",
        "",
        "## Interpretation, limits and audit",
        "",
        "TASK_NONDEGRADATION_QUALIFIED_ONLY bounds a specified binary degradation error at the registered 10% target, conditional on source and action assignment. It does not guarantee zero harm, absolute completion, nonnegative expected policy return, physical safety, arbitrary sensor robustness or real-robot transfer. Abstention and unmeasured intervention costs prevent interpreting it as a general safe-policy-improvement theorem. Clean calibration does not qualify the stored noisy-input variants.",
        "",
        "Candidate support, observed errors and the same confidence allocation jointly determine DSRE/CART qualification. A support-frequency difference is not algorithmic or controller superiority. B7's exact identity is retained. The novelty assessment explicitly separates prospective operational evidence from the established binary identity, selective calibration, outcome-aware rules and counterfactual evaluation.",
        "",
        f"The strong-baseline limitations matter: unqualified raw CART selects {raw_cart['required_selected']} required recoveries with {raw_cart['harm_R']} harmful and {raw_cart['futile_R']} futile attempts, and completes {raw_cart['success']}/640. Its calibrated refusal is a support limitation, not evidence that its proposals are physically worse. Always-recover completes {fixed_recover['success']}/640 versus DSRE non-degradation's {selected['success']}/640, but causes {fixed_recover['harm_R']} binary harms and {fixed_recover['futile_R']} futile attempts. DSRE still misses {selected['required'] - selected['required_selected']} of {selected['required']} necessary recoveries and defers {selected['stop']}/640 checkpoints. These results establish neither maximal completion nor algorithmic superiority.",
        "",
        "Independent checks reconstruct terminal labels, full physical prefix/action/contact/model/controller traces, six bounds with separate binomial inversion and beta quantiles, sidecar eligibility/annotations and whole-cohort timing isolation. The numerical recount imports no production selector or simulator and checks every count and interval through separate direct indexed resampling. Tests, Ruff, source/user/manuscript preservation, workers, failed development checks and resource accounting are sealed beside completion_manifest.json. No manuscript is edited or pushed.",
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1",
        "export PYTHONPATH=src:scripts:/home/imad/Desktop/IEEE-RAL/results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages",
        "export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=1",
        "mkdir /tmp/dsre-dual-portable-review-20261116",
        "tar -xzf docs/dsre_dual_obligation_review.tar.gz -C /tmp/dsre-dual-portable-review-20261116",
        "uv run --no-sync python /tmp/dsre-dual-portable-review-20261116/source/scripts/dsre_dual_verify_packet.py /tmp/dsre-dual-portable-review-20261116",
        "uv run --no-sync pytest -q tests",
        "```",
        "",
        "Use a fresh empty extraction directory. Portable verification is read-only statistical review; full physical truth requires the local raw archive and the independently sealed source audits. Audit/analysis commands that write outputs must run only in a disposable copy, never over sealed evidence. Exact executed commands and meters are retained locally.",
    ]
    Path("docs/DSRE_DUAL_OBLIGATION_RESULTS.md").write_text("\n".join(lines) + "\n")
    agreement = {}
    with gzip.open(root / "policy_records.jsonl.gz", "rt") as stream:
        for line in stream:
            rec = json.loads(line)
            if rec["policy"] in ("DSRE_nondegradation", "CART2_nondegradation"):
                agreement.setdefault((rec["seed"], rec["condition"]), {})[
                    rec["policy"]
                ] = rec["action"]
    different = sum(
        p["DSRE_nondegradation"] != p["CART2_nondegradation"]
        for p in agreement.values()
    )
    registered = (root / "nearest_work_registered.md").read_text()
    judgment = f"\n\n## Independently verified scientific outcome\n\n**{result['status']}**. DSRE's non-degradation composition completes {selected['success']}/640 versus {absolute['counts']['success']}/640 under absolute-success qualification; difference {estimate(primary, ' pp')}. It selects {selected['required_selected']}/{selected['required']} necessary recoveries with {selected['harm_R']} binary harms and {selected['futile_R']} futile attempts. The original adequate-action interpretation and gate are not relabeled.\n\nDSRE and CART2 non-degradation decisions differ at {different}/640 checkpoints; paired completion difference is {estimate(versus_cart, ' pp')}. Their recovery-assigned calibration supports are {cal['bounds']['DSRE_risk|recover|nondegradation']['assigned_parents']} and {cal['bounds']['CART2_beta10|recover|nondegradation']['assigned_parents']}. Candidate sets, error rates and statistical support must explain this comparison; it is not evidence of a better controller. B7 exactly reproduces DSRE.\n\nOur assessment: this experiment establishes the measured operational distinction only to the extent stated by its preregistered outcome label. It does **not establish a distinct new optimizer, a substantive algorithmic advantage over equivalent ordinary rules, or a general policy-improvement theorem**. The elementary error decomposition and statistical tools are established, and the new evaluator does not minimize a new harm certificate. The defensible additional contribution is source-specific evidence about which named obligation the existing observable contract can support, including its unsuccessful-attempt burden. Standalone methodological distinctiveness remains limited; a positive qualification alone does not resolve it.\n\nNo acceptance/readiness claim follows. This finite contract is complete; no further objective, optimizer, fault family, feature, controller or simulation expansion is authorized without supervisor review.\n"
    judgment += f"\n## Scientific reviewer critique\n\nThe empirical obligation distinction survives, but the method claim remains constrained. (1) B7 is exactly identical; no new rule optimizer or minimum non-degradation certificate was introduced. (2) Raw CART achieves {raw_cart['required_selected']} required recoveries, {raw_cart['harm_R']} harms and {raw_cart['futile_R']} futile attempts; its calibrated recovery strata fail from insufficient parent support. This is not an adverse physical comparison against CART. (3) Always-recover obtains {fixed_recover['success']}/640 completions with {fixed_recover['harm_R']} harms, while DSRE obtains {selected['success']}/640 and leaves {selected['required'] - selected['required_selected']}/{selected['required']} necessary recoveries unselected. The tradeoff must be visible. (4) Zero observed selected harm and a 10% parent-conditional bound do not establish zero harm, absolute success, sensor robustness, long-horizon return or physical safety. (5) The finite reference supports scoped observable witnesses; the two counterfactual futures remain simulator/source dependent, and neither-success attempts still fail. These concerns limit standalone methodological distinctiveness even though the preregistered operational result is positive.\n"
    Path("docs/DSRE_DUAL_OBLIGATION_NOVELTY_AND_GATE.md").write_text(
        registered + judgment
    )
    with (root / "calibration_table.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["claim", "assigned_parents", "error_parents", "exact_upper", "qualified"]
        )
        for key, value in cal["bounds"].items():
            writer.writerow(
                [
                    key,
                    value["assigned_parents"],
                    value["error_parents"],
                    value["upper"],
                    value["qualified"],
                ]
            )
    with (root / "policy_table.csv").open("w") as stream:
        writer = csv.writer(stream)
        fields = list(main["counts"])
        writer.writerow(
            [
                "policy",
                *fields,
                "completion",
                "completion_lower95",
                "completion_upper95",
                "required_recovery_recall",
            ]
        )
        for key, value in result["tables"].items():
            if key.endswith("|ALL"):
                ci = value["intervals"]
                writer.writerow(
                    [
                        key.removesuffix("|ALL"),
                        *[value["counts"][field] for field in fields],
                        ci["completion"]["estimate"],
                        ci["completion"]["lower"],
                        ci["completion"]["upper"],
                        ci["required_recovery_recall"]["estimate"],
                    ]
                )
    write_once(
        root / "report_source_binding.json",
        {
            "results_sha256": sha(root / "dual_results.json"),
            "independent_audit_sha256": sha(
                root / "independent_dual_numerical_audit.json"
            ),
            "report_sha256": sha(Path("docs/DSRE_DUAL_OBLIGATION_RESULTS.md")),
            "novelty_gate_sha256": sha(
                Path("docs/DSRE_DUAL_OBLIGATION_NOVELTY_AND_GATE.md")
            ),
            "status": result["status"],
        },
    )
    return result, cal


def figure(root, result, cal):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 8})
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.3))
    keys = list(cal["bounds"])
    upper = [100 * cal["bounds"][key]["upper"] for key in keys]
    labels = []
    for index, key in enumerate(keys):
        method, action, endpoint = key.split("|")
        row = cal["bounds"][key]
        axes[0].bar(
            index,
            upper[index],
            color="#3d8069" if row["qualified"] else "#c7c7c7",
            edgecolor="#555555",
            linewidth=0.5,
        )
        axes[0].annotate(
            f"{row['error_parents']}/{row['assigned_parents']}",
            (index, upper[index]),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=6,
        )
        labels.append(
            ("DSRE" if method == "DSRE_risk" else "CART2")
            + "\n"
            + ("R " if action == "recover" else "C ")
            + ("abs" if endpoint == "absolute" else "harm")
        )
    axes[0].axhline(10, color="#a84b48", linestyle="--", linewidth=0.8)
    axes[0].set(
        xticks=range(6),
        xticklabels=labels,
        ylabel="Exact parent-error upper bound (%)",
        ylim=(0, min(107, max(15, 1.25 * max(upper)))),
        title="Calibration: fixed six-claim family",
    )
    axes[0].text(
        0.98,
        0.95,
        "labels: error/assigned parents\ngreen: qualified, target 10%",
        transform=axes[0].transAxes,
        ha="right",
        va="top",
        fontsize=6,
    )
    policies = (
        "DSRE_absolute",
        "DSRE_nondegradation",
        "CART2_absolute",
        "CART2_nondegradation",
    )
    names = ("DSRE abs", "DSRE harm", "CART2 abs", "CART2 harm")
    left = [0] * 4
    for field, label, color in (
        ("R_only", "R-only successes", "#3d8069"),
        ("both_success_R", "Both succeed", "#537aa4"),
        ("futile_R", "Both fail", "#b3b3b3"),
        ("harm_R", "Harm to C success", "#b95550"),
    ):
        counts = [result["tables"][p + "|ALL"]["counts"][field] for p in policies]
        axes[1].barh(range(4), counts, left=left, label=label, color=color)
        left = [a + b for a, b in zip(left, counts, strict=True)]
    for i, total in enumerate(left):
        axes[1].text(total + 0.6, i, str(total), va="center", fontsize=7)
    axes[1].set(
        yticks=range(4),
        yticklabels=names,
        xlabel="Test recovery attempts (checkpoint count)",
        xlim=(0, max(10, 1.2 * max(left))),
        title="Selected recovery outcomes",
    )
    axes[1].invert_yaxis()
    axes[1].legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(
            Path("docs/figures") / ("dsre_dual_obligation." + ext),
            dpi=300,
            bbox_inches="tight",
        )
    plt.close(fig)
    write_once(
        root / "figure_sources.json",
        {
            "calibration_sha256": sha(root / "dual_calibration.json"),
            "results_sha256": sha(root / "dual_results.json"),
            "scope": "All six CP calibration bounds with parent denominators, and selected test recoveries classified from physical pairs. Harm is binary task-outcome degradation, not physical safety. Zero attempts are visible. No outcome filtering or deployed noisy guarantee.",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result, calibration = render(args.root)
    figure(args.root, result, calibration)
