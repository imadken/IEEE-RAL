"""Ready-to-insert scientific figures; neither manuscript is edited."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_followup_batch import atomic, read

COLORS = ["#0072B2", "#009E73", "#E69F00", "#CC79A7", "#999999"]


def save(fig, path):
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def figures(root):
    assert read(root / "offline_numerical_audit.json")["passed"]
    assert read(root / "prospective_numerical_audit.json")["passed"]
    old = read(root / "mechanism_results.json")
    new = read(root / "prospective_results.json")
    compat = read(root / "mechanism_compatibility.json")["profiles"]
    nc = read(root / "prospective_compatibility.json")["profiles"]
    offline = read(root / "offline_uncertainty.json")
    effects = read(root / "physical_effects_and_secondary.json")
    out = Path("docs/figures")
    out.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )
    data = {}
    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(13.8, 6.7), gridspec_kw={"width_ratios": [1.1, 1]}
    )
    population_profiles = [
        (
            "Pick reference\n211 parents, 2 conditions",
            old,
            "development_reference|PickCube-v1",
            compat,
        ),
        (
            "Push reference\n211 parents, 2 conditions",
            old,
            "development_reference|PushCube-v1",
            compat,
        ),
        (
            "Pick prior test (reanalysis)\n160 parents, 2 conditions",
            old,
            "fresh160_reanalysis|PickCube-v1",
            compat,
        ),
        (
            "Pick new confirmation\n128 parents, 5 conditions",
            new["mechanism"],
            "new_confirmation",
            nc,
        ),
    ]
    measures = [
        "Physical action feasibility",
        "Exact signature: 6 facts",
        "Exact signature: 7 facts",
        "Exact signature: 12 facts",
        "Invariant-literal compatibility: 7 facts, 5mm",
    ]
    bars = []
    for label, source, prefix, comp in population_profiles:
        p = source[prefix + "|point7"]
        compkey = (
            prefix + "|rho0.005|facts7"
            if prefix != "new_confirmation"
            else "new_confirmation|PickCube-v1|rho0.005|facts7"
        )
        values = [
            p["action_mass"],
            source[prefix + "|point6"]["observation_mass"],
            p["observation_mass"],
            source[prefix + "|point12"]["observation_mass"],
            comp[compkey]["literal_compatible_common_action_mass"],
        ]
        bars.append({"population": label, "rows": p["rows"], "masses": values})
    for i, name in enumerate(measures):
        y = np.arange(4) + (i - 2) * 0.14
        values = [b["masses"][i] / b["rows"] for b in bars]
        ax.barh(y, values, height=0.13, color=COLORS[i], label=name)
        for yy, b, v in zip(y, bars, values, strict=True):
            ax.text(
                min(v + 0.01, 1.01),
                yy,
                f"{b['masses'][i]}/{b['rows']}",
                va="center",
                fontsize=7.5,
            )
    ax.set_yticks(range(4), [p[0] for p in population_profiles])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.2)
    ax.set_xlabel("Same-table hindsight mass / checkpoints")
    ax.set_title(
        "Intervention feasibility and observation sufficiency", fontweight="bold"
    )
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.45, -0.12),
        ncol=1,
        frameon=False,
        fontsize=8,
    )
    policies = []
    for label, pop, mode, method in [
        (
            "Prior Pick: strict",
            "fresh160_reanalysis",
            "original_clean_gate",
            "DSRE_strict",
        ),
        (
            "Prior Pick: risk = ordinary rules",
            "fresh160_reanalysis",
            "original_clean_gate",
            "DSRE_risk",
        ),
        (
            "Prior Pick: CART2 risk",
            "fresh160_reanalysis",
            "original_clean_gate",
            "CART2_beta10",
        ),
        ("New Pick: strict", "new_confirmation", "robust_proposal", "DSRE_strict"),
        (
            "New Pick: risk = ordinary rules",
            "new_confirmation",
            "robust_proposal",
            "DSRE_risk",
        ),
        ("New Pick: CART2 risk", "new_confirmation", "robust_proposal", "CART2_beta10"),
        (
            "New Pick: fixed continue",
            "new_confirmation",
            "robust_proposal",
            "B0_continue",
        ),
        (
            "New Pick: fixed recover",
            "new_confirmation",
            "robust_proposal",
            "B0_recover",
        ),
    ]:
        table = offline["tables"] if pop == "fresh160_reanalysis" else new["tables"]
        v = table[f"{pop}|PickCube-v1|clean|{mode}|{method}"]
        policies.append(
            {
                "label": label,
                **{k: v[k] for k in ("adequate", "inadequate", "stop", "rows")},
            }
        )
    for i, p in enumerate(policies):
        start = 0
        for field, color in (
            ("adequate", "#009E73"),
            ("inadequate", "#D55E00"),
            ("stop", "#D5D5D5"),
        ):
            width = p[field] / p["rows"]
            bx.barh(
                i,
                width,
                left=start,
                height=0.7,
                color=color,
                label=field if i == 0 else None,
            )
            start += width
        bx.text(
            1.015,
            i,
            f"{p['adequate']}/{p['inadequate']}/{p['stop']}\nn={p['rows']}",
            va="center",
            fontsize=8,
        )
    bx.set_yticks(range(len(policies)), [p["label"] for p in policies])
    bx.invert_yaxis()
    bx.set_xlim(0, 1.25)
    bx.set_xlabel("Adequate / inadequate / STOP; STOP is not completion")
    bx.set_title(
        "Selective decisions under distinct qualification scopes", fontweight="bold"
    )
    bx.axhline(2.5, color="black", linewidth=0.8)
    bx.legend(
        loc="upper center",
        bbox_to_anchor=(0.43, -0.12),
        ncol=3,
        frameon=False,
        fontsize=8,
    )
    fig.suptitle(
        "Fixed two-skill outcomes: feasibility, observable justification, and selected coverage",
        fontsize=13,
    )
    fig.text(
        0.04,
        -0.06,
        "Prior clean gates retain their original scope. ALL new-source proposals are unqualified. Exact-signature ceilings are not deployed policies; risk-tier decisions need not lie below a strict hindsight ceiling.\nMeasurement bound is coordinate-wise per pose/frame; finger encoders are assumed exact. Two registered historical conditions; five prespecified approach offsets in the new source.",
        fontsize=9,
    )
    fig.tight_layout()
    save(fig, out / "dsre_science_v12_feasibility")
    data["feasibility"] = {"ceilings": bars, "policies": policies}

    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1.5, 1]}
    )
    conditions = new["qualified_conditions"]
    names = {
        "nominal": "0",
        "offset001": "+1",
        "offset002": "+2",
        "offset003": "+3",
        "offset_minus002": "−2",
    }
    bottom = np.zeros(len(conditions))
    classes = []
    for field, color, label in (
        ("continue_only", "#0072B2", "Continue only"),
        ("recover_only", "#009E73", "Recover only"),
        ("both", "#E69F00", "Both succeed"),
        ("neither", "#CC79A7", "Neither succeeds"),
    ):
        counts = [
            new["outcome_classes"]["new_confirmation|" + c][field] for c in conditions
        ]
        totals = [
            new["outcome_classes"]["new_confirmation|" + c]["rows"] for c in conditions
        ]
        heights = np.asarray(counts) / np.asarray(totals)
        ax.bar(range(len(conditions)), heights, bottom=bottom, color=color, label=label)
        for i, (n, h, b) in enumerate(zip(counts, heights, bottom, strict=True)):
            if n:
                ax.text(i, b + h / 2, str(n), ha="center", va="center", fontsize=9)
        bottom += heights
        classes.append({"class": field, "counts": counts})
    ax.set_xticks(range(len(conditions)), [names[c] for c in conditions])
    ax.set_xlabel("Scripted approach-target x offset (cm)")
    ax.set_ylabel("Fraction of paired checkpoints")
    ax.set_title("Untouched confirmation: 128 shared seed parents per arm")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    estimates = [
        effects["physical_effects"]["new_confirmation|" + c]["recover_minus_continue"]
        for c in conditions
    ]
    xs = np.array([e["estimate"] for e in estimates])
    error = np.array(
        [
            [e["estimate"] - e["lower"] for e in estimates],
            [e["upper"] - e["estimate"] for e in estimates],
        ]
    )
    bx.errorbar(
        xs, range(len(conditions)), xerr=error, fmt="o", color="black", capsize=4
    )
    bx.axvline(0, color="#999999", linestyle="--")
    bx.set_yticks(range(len(conditions)), [names[c] + " cm" for c in conditions])
    bx.invert_yaxis()
    bx.set_xlabel("Matched recovery − continuation success")
    bx.set_title("Paired physical contrast; parent-group 95% CI")
    fig.text(
        0.02,
        -0.03,
        "Both70-control branches start from the same fully replayed state. All five arms/128 parents retained; no outcome balancing. These compare fixed actions, not a newly calibrated controller.",
        fontsize=9,
    )
    fig.tight_layout()
    save(fig, out / "dsre_science_v12_physical_grid")
    data["physical_grid"] = {
        "conditions": conditions,
        "classes": classes,
        "effects": estimates,
    }

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.7))
    curves = {}
    for column, (population, source, title) in enumerate(
        (
            ("fresh160_reanalysis", offline, "Prior160-parent Pick reanalysis"),
            ("new_confirmation", new, "Untouched128-parent / five-offset Pick"),
        )
    ):
        for method, mode, label, color in (
            ("DSRE_strict", "robust_proposal", "Strict DSRE = B7", COLORS[0]),
            (
                "DSRE_risk",
                "robust_proposal",
                "Risk DSRE = ordinary risk rules",
                COLORS[1],
            ),
            ("CART2_beta10", "robust_proposal", "Robust CART2 risk", COLORS[2]),
            (
                "margin_DSRE_strict",
                "margin_all_inputs",
                "All-input margin + strict",
                COLORS[3],
            ),
        ):
            values = [
                source["tables"][f"{population}|PickCube-v1|{scenario}|{mode}|{method}"]
                for scenario in ("clean", "bound001", "bound005")
            ]
            for row, metric in ((0, "adequacy"), (1, "necessary_recovery_recall")):
                y = [v["intervals"][metric]["estimate"] for v in values]
                lo = [v["intervals"][metric]["lower"] for v in values]
                hi = [v["intervals"][metric]["upper"] for v in values]
                if None in y:
                    continue
                axes[row, column].plot([0, 1, 5], y, "o-", label=label, color=color)
                axes[row, column].fill_between(
                    [0, 1, 5], lo, hi, color=color, alpha=0.10
                )
            curves[population + "|" + method] = [
                {
                    k: v[k]
                    for k in (
                        "adequate",
                        "inadequate",
                        "stop",
                        "required_selected",
                        "required_total",
                        "false_assertions",
                        "literals",
                    )
                }
                for v in values
            ]
        axes[0, column].set_title(title)
        axes[0, column].set_ylabel("Adequate selected actions / checkpoints")
        axes[1, column].set_ylabel("Selected necessary recoveries / opportunities")
        for row in (0, 1):
            axes[row, column].set_xlabel(
                "Declared coordinate error per pose/frame (mm)"
            )
            axes[row, column].set_xticks([0, 1, 5])
            axes[row, column].set_ylim(bottom=0)
            axes[row, column].grid(axis="y", alpha=0.2)
    axes[0, 0].legend(loc="best", frameon=False, fontsize=8)
    fig.suptitle(
        "Measurement invariance trades coverage for justified factual assertions",
        fontsize=13,
    )
    fig.text(
        0.03,
        0.005,
        "Centers held at source telemetry; these are bounded-error scenarios, separate from actual uniform corruption replicates. Shading: parent-group95% intervals.\nNo altered-sensor or new-source risk qualification. Zero false invariant assertions does not establish zero inadequate interventions. Strong ordinary-rule equivalences remain exact.",
        fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 0.96])
    save(fig, out / "dsre_science_v12_measurement_tradeoff")
    data["measurement_tradeoff"] = curves
    atomic(root / "figure_data.json", data)
    print(json.dumps({"figures": 3, "pdf_and_png_directory": str(out)}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    figures(a.root)
