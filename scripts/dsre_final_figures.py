"""Publication figures from audited fixed-scope operational and shift results."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_final_report import row
from dsre_followup_batch import atomic, read


def figures(root):
    assert not (root / "completion_manifest.json").exists()
    r = read(root / "operational_results.json")
    assert read(root / "independent_audit.json")["status"] == "PASS"
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42})
    out = Path("rss2027/figures")
    plot_data = {"operational": [], "sensitivity": []}
    methods = (
        "DSRE_strict",
        "DSRE_risk",
        "B7_risk",
        "CART2_beta10",
        "B5_beta10",
        "B0_continue",
        "B0_recover",
    )
    labels = (
        "Strict",
        "Risk tier",
        "Ord. risk",
        "CART .9",
        "B5 .10",
        "Always C",
        "Always R",
    )
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.7), sharey=True)
    for ax, task, title in zip(
        axes, ("PickCube-v1", "PushCube-v1"), ("PickCube", "PushCube"), strict=True
    ):
        bottom = np.zeros(len(methods))
        x = np.arange(len(methods))
        for field, name, color in (
            ("maintained_success", "Initially successful completion", "#16a34a"),
            (
                "required_recovery_success",
                "Required recovery on unsuccessful start",
                "#d97706",
            ),
            ("other", "Other unsuccessful-start completion", "#2563eb"),
            ("unacceptable", "Inadequate action", "#dc2626"),
            ("deferred", "STOP / defer", "#d1d5db"),
        ):
            heights = []
            for method in methods:
                a = row(r["tables"], task, method)
                n = a["checkpoints"]
                number = (
                    a["failed_start_success"] - a["required_recovery_success"]
                    if field == "other"
                    else a[field]
                )
                heights.append(100 * number / n if n else 0)
                plot_data["operational"].append(
                    {
                        "task": task,
                        "method": method,
                        "field": field,
                        "N": n,
                        "count": number,
                        "percent": 100 * number / n if n else 0,
                    }
                )
            ax.bar(x, heights, 0.74, bottom=bottom, label=name, color=color)
            bottom += heights
        a = row(r["tables"], task)
        ax.set(
            title=f"{title}: {a['parents']} parents / {a['checkpoints']} checkpoints",
            ylim=(0, 105),
            xticks=x,
            xticklabels=labels,
        )
        ax.tick_params(axis="x", rotation=35, labelsize=7)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Checkpoints (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, -0.005)
    )
    fig.tight_layout(rect=(0, 0.3, 1, 1), pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"final_operational.{ext}", dpi=350)
    plt.close(fig)
    robust = read(root / "heldout_robustness.json")["parent_intervals"]
    families = (
        "clean",
        "missing_optional",
        "missing_history",
        "missing_pose",
        "noise001",
        "noise005",
        "delay1",
        "delay5",
    )
    labels = (
        "Clean",
        "No selected",
        "No history",
        "No pose",
        "1 mm",
        "5 mm",
        "50 ms",
        "250 ms",
    )
    styles = (
        ("DSRE_strict", "#2563eb", "o-", "Strict DSRE"),
        ("DSRE_risk", "#d97706", "s-", "Risk proposal"),
        ("CART2_beta10", "#059669", "^--", "CART .9 proposal"),
    )
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.7), sharey=True)
    for ax, task, title in zip(
        axes, ("PickCube-v1", "PushCube-v1"), ("PickCube", "PushCube"), strict=True
    ):
        for method, color, style, label in styles:
            good = []
            bad = []
            low = []
            high = []
            for family in families:
                a = robust[f"{task}|{method}|proposal|{family}|all"]
                good.append(100 * a["successful"]["value"])
                bad.append(100 * a["unacceptable"]["value"])
                lo, hi = a["successful"]["parent_percentile95"]
                low.append(100 * lo)
                high.append(100 * hi)
                plot_data["sensitivity"].append(
                    {
                        "task": task,
                        "method": method,
                        "scenario": family,
                        "good": 100 * a["successful"]["value"],
                        "bad": 100 * a["unacceptable"]["value"],
                        "low": 100 * lo,
                        "high": 100 * hi,
                    }
                )
            ax.plot(range(len(families)), good, style, color=color, label=label)
            ax.fill_between(range(len(families)), low, high, color=color, alpha=0.10)
            ax.plot(range(len(families)), bad, ":", color=color, alpha=0.9)
        ax.set(
            title=title, ylim=(-3, 105), xticks=range(len(families)), xticklabels=labels
        )
        ax.tick_params(axis="x", rotation=35, labelsize=7)
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Checkpoints (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, -0.005)
    )
    fig.text(
        0.51,
        0.16,
        "Marked: good; dotted: inadequate; bands: parent 95% intervals. Offline shift only.",
        ha="center",
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.30, 1, 1), pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"final_robustness.{ext}", dpi=350)
    plt.close(fig)
    atomic(root / "figure_data.json", plot_data)
    print({"measured_figures": 4, "no_speculative_points": True}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    figures(parser.parse_args().root)
