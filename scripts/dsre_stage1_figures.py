"""Stage 1 figures separating measured action potential and selective credit."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_followup_batch import atomic, read
from dsre_stage1_analysis import PRIOR, TASKS, counts
from matplotlib.patches import FancyBboxPatch


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(Path("rss2027/figures") / f"stage1_{name}.{ext}", dpi=350)
    plt.close(fig)


def figures(root):
    assert read(root / "source_audit.json")["status"] == "PASS"
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42})
    cases = {c["case"]: c for c in read(PRIOR / "physical_examples.json")["cases"]}
    d, e = cases["D"], cases["E"]
    assert (
        d["features"] + d["optional_features"] == e["features"] + e["optional_features"]
    )
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(
        0.5,
        0.98,
        "Measured adequacy ≠ observable justification",
        ha="center",
        va="top",
        fontsize=8.7,
        weight="bold",
    )
    ax.text(
        0.5,
        0.84,
        "Push D/E: same 12 facts, opposing actions",
        ha="center",
        fontsize=8.5,
    )
    for x, case in ((0.05, d), (0.55, e)):
        ax.text(x, 0.69, f"{case['case']}: Δx={case['dx']:+.5f} m", fontsize=8)
        for j, action in enumerate(("continue", "recover")):
            good = int(case["outcomes"][action + "_value"])
            px = x + j * 0.21
            ax.add_patch(
                FancyBboxPatch(
                    (px, 0.48),
                    0.18,
                    0.15,
                    boxstyle="round,pad=0.01",
                    facecolor="#d1fae5" if good else "#fee2e2",
                    edgecolor="#222222",
                    linewidth=0.6,
                )
            )
            ax.text(
                px + 0.09,
                0.555,
                f"{action[0].upper()}: {good}",
                ha="center",
                va="center",
                fontsize=9,
            )
    ax.text(
        0.5,
        0.39,
        "Intersection empty → observation conflict",
        ha="center",
        fontsize=8.3,
        weight="bold",
    )
    ax.text(0.02, 0.26, "Pick A: 3 facts → recovery certificate", fontsize=8.3)
    ax.text(0.02, 0.14, "Pick B: C=0, R=0 → repertoire gap", fontsize=8.3)
    ax.text(0.02, 0.02, "Pick F: 1 parent → reference gap (also C=R=0)", fontsize=8)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.03, top=0.98)
    save(fig, "mechanism")
    data = {
        "mechanism": {
            k: {f: cases[k][f] for f in ("id", "source", "source_sha256", "outcomes")}
            for k in ("A", "B", "D", "E", "F")
        },
        "outcomes": [],
        "limits": [],
    }
    primary = read(root / "primary_rows.json")
    predictions = read(PRIOR / "test_records.json")
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.3), sharey=True)
    labels = ("Raw C", "Raw R", "Strict", "Risk", "Ord./CART", "Gated R")
    for ax, task in zip(axes, TASKS, strict=True):
        raw = [r for r in primary if r["task"] == task]
        rs = []
        for action in ("continue", "recover"):
            rs.append(counts([r | {"action": action} for r in raw]))
        for method in ("DSRE_strict", "DSRE_risk", "CART2_beta10", "B0_recover"):
            lookup = {
                r["id"]: r["action"]
                for r in predictions
                if r["task"] == task
                and r["mode"] == "calibrated"
                and r["method"] == method
            }
            rs.append(counts([r | {"action": lookup[r["id"]]} for r in raw]))
        bottom = np.zeros(len(rs))
        x = np.asarray([0, 1, 2.5, 3.5, 4.5, 5.5])
        for field, legend, color in (
            ("maintained", "Maintained success", "#15803d"),
            ("required_recovery", "Required recovery", "#d97706"),
            ("other", "Other completion", "#1d4ed8"),
            ("bad", "Inadequate action", "#b91c1c"),
            ("stop", "STOP: zero credit", "#d1d5db"),
        ):
            values = [
                r["good"] - r["maintained"] - r["required_recovery"]
                if field == "other"
                else r[field]
                for r in rs
            ]
            heights = 100 * np.asarray(values) / len(raw)
            ax.bar(
                x,
                heights,
                0.76,
                bottom=bottom,
                color=color,
                label=legend,
                hatch="//" if field == "stop" else None,
                edgecolor="white",
                linewidth=0.25,
            )
            bottom += heights
            for i, value in enumerate(values):
                data["outcomes"].append(
                    {
                        "task": task,
                        "label": labels[i],
                        "field": field,
                        "count": value,
                        "N": len(raw),
                    }
                )
        ax.axvline(1.8, color="#111827", linestyle=":", linewidth=0.8)
        ax.set(
            title=f"{task.split('-')[0]} (N={len(raw)})",
            ylim=(0, 116),
            xticks=x,
            xticklabels=labels,
        )
        ax.text(0.5, 108, "Paired potential", ha="center", fontsize=8)
        ax.text(4, 108, "Gated selective credit", ha="center", fontsize=8)
        ax.tick_params(axis="x", rotation=35, labelsize=8)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Checkpoints (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, -0.005)
    )
    fig.tight_layout(rect=(0, 0.24, 1, 1), pad=0.3)
    save(fig, "outcomes")
    fig, axes = plt.subplots(1, 2, figsize=(7, 1.9))
    ceilings = read(root / "source_audit.json")["finite_ceilings"]
    for task, color, marker in zip(
        TASKS, ("#1d4ed8", "#b45309"), ("o", "s"), strict=True
    ):
        values = [ceilings[f"{task}|{b}"] for b in (0, 1, 6)]
        axes[0].plot(
            range(3),
            100 * np.asarray(values) / 422,
            marker=marker,
            label=task.split("-")[0],
            color=color,
        )
        for x, y in enumerate(values):
            axes[0].annotate(
                str(y),
                (x, 100 * y / 422),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )
            data["limits"].append(
                {
                    "kind": "finite",
                    "task": task,
                    "budget": (0, 1, 6)[x],
                    "count": y,
                    "N": 422,
                }
            )
    axes[0].set(
        xticks=range(3),
        xticklabels=("0", "1", "all 6"),
        xlabel="Optional predicates",
        ylabel="Finite mass (%)",
        ylim=(-7, 78),
        title="Fixed reference, not test success",
    )
    axes[0].legend(fontsize=8, loc="center right")
    robust = read(PRIOR / "heldout_robustness.json")["parent_intervals"]
    for metric, name, color, marker in (
        ("unacceptable", "Inadequate action proposal", "#b91c1c", "o"),
        ("false_confidence", "Contradicted fact in proposal", "#7c3aed", "s"),
    ):
        vs = [
            robust[f"PickCube-v1|DSRE_strict|proposal|{s}|all"][metric]
            for s in ("clean", "noise005", "delay5")
        ]
        y = 100 * np.asarray([v["value"] for v in vs])
        ci = 100 * np.asarray([v["parent_percentile95"] for v in vs])
        axes[1].errorbar(
            range(3),
            y,
            yerr=np.asarray([y - ci[:, 0], ci[:, 1] - y]),
            marker=marker,
            color=color,
            label=name,
            capsize=2,
        )
        for scenario, value in zip(("clean", "noise005", "delay5"), vs, strict=True):
            data["limits"].append(
                {"kind": "sensitivity", "scenario": scenario, "metric": metric, **value}
            )
    axes[1].set(
        xticks=range(3),
        xticklabels=("Clean", "5 mm", "250 ms"),
        ylabel="Pick views (%)",
        ylim=(-1, 24),
        title="Fixed outcomes; perturbed inputs",
    )
    axes[1].legend(fontsize=7.3, loc="upper left")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.tight_layout(pad=0.45)
    save(fig, "limits")
    atomic(root / "stage1_figure_data.json", data)
    print({"stage1_figures": 3, "historical_assets_unchanged": True}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    figures(parser.parse_args().root)
