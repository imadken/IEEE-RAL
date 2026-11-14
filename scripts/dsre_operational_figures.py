"""Measured operational abstention and fixed-grid observation sensitivity figures."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_followup_batch import read


def figures(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Sealed evidence")
    primary = read(root / "operational_results.json")
    exploratory = not primary["complete_parents"]
    tables = (
        read(root / "exploratory_operational_results.json")["tables"]
        if exploratory
        else primary["tables"]
    )
    robustness = read(root / "observation_robustness.json")
    out = Path("rss2027/figures")
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42})
    methods = (
        "DSRE_strict",
        "DSRE_risk",
        "B7_risk",
        "CART2_beta10",
        "B5_beta10",
        "B0_recover",
    )
    labels = ("Strict", "Risk tier", "Ord. risk", "CART .9", "B5 .10", "Always R")
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.5), sharey=True)
    for ax, task, title in zip(
        axes, ("PickCube-v1", "PushCube-v1"), ("PickCube", "PushCube"), strict=True
    ):
        bottoms = np.zeros(len(methods))
        x = np.arange(len(methods))
        for field, label, color in (
            ("maintained_success", "Initially successful completion", "#16a34a"),
            (
                "required_recovery_success",
                "Required recover on unsuccessful start",
                "#d97706",
            ),
            ("other", "Other unsuccessful-start completion", "#2563eb"),
            ("unacceptable", "Inadequate acted-on checkpoint", "#dc2626"),
            ("deferred", "Defer / stop", "#d1d5db"),
        ):
            counts = []
            n = 0
            for method in methods:
                row = tables.get(f"{task}|{method}|calibrated|clean|all", {})
                n = row.get("checkpoints", 0)
                value = (
                    (
                        row.get("failed_start_success", 0)
                        - row.get("required_recovery_success", 0)
                    )
                    if field == "other"
                    else row.get(field, 0)
                )
                counts.append(100 * value / n if n else 0)
            ax.bar(x, counts, 0.73, bottom=bottoms, label=label, color=color)
            bottoms += counts
        ax.set(
            title=f"{title}: {n} {'inspected' if exploratory else 'test'} checkpoints",
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
        h, l, loc="lower center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, -0.01)
    )
    fig.tight_layout(rect=(0, 0.3, 1, 1), pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"operational.{ext}", dpi=350)
    plt.close(fig)
    scenarios = (
        "clean",
        "missing_optional",
        "missing_history",
        "missing_pose",
        "noise001_r0",
        "noise005_r0",
        "delay1",
        "delay5",
    )
    labels = (
        "Clean",
        "No extra",
        "No history",
        "No pose",
        "1 mm",
        "5 mm",
        "50 ms",
        "250 ms",
    )
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.5), sharey=True)
    styles = (
        ("DSRE_strict", "#2563eb", "o-", "Strict DSRE"),
        ("DSRE_risk", "#d97706", "s-", "Risk-tier proposal"),
        ("CART2_beta10", "#059669", "^--", "CART .9 proposal"),
    )
    for ax, task, title in zip(
        axes, ("PickCube-v1", "PushCube-v1"), ("PickCube", "PushCube"), strict=True
    ):
        for method, color, style, label in styles:
            good = []
            bad = []
            for scenario in scenarios:
                # Noise points average all three predeclared replicates; parent N
                # is unchanged and independent-replicate confidence is not claimed.
                names = (
                    [scenario.replace("r0", f"r{i}") for i in range(3)]
                    if scenario.startswith("noise")
                    else [scenario]
                )
                rows = [
                    robustness["tables"][f"{task}|{method}|proposal|{s}|all"]
                    for s in names
                ]
                good.append(
                    np.mean([100 * r["successful"] / r["checkpoints"] for r in rows])
                )
                bad.append(
                    np.mean([100 * r["unacceptable"] / r["checkpoints"] for r in rows])
                )
            ax.plot(range(len(scenarios)), good, style, color=color, label=label)
            ax.plot(range(len(scenarios)), bad, ":", color=color, alpha=0.8)
        ax.set(
            title=title,
            ylim=(-3, 105),
            xticks=range(len(scenarios)),
            xticklabels=labels,
        )
        ax.tick_params(axis="x", rotation=35, labelsize=7)
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Checkpoints (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, -0.01)
    )
    fig.text(
        0.51,
        0.17,
        "Solid/marked: good; dotted: inadequate. Offline; no calibration transfer.",
        ha="center",
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.31, 1, 1), pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"observation_robustness.{ext}", dpi=350)
    plt.close(fig)
    print(
        "Operational defer/completion and offline observation sensitivity figures rendered",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    figures(parser.parse_args().root)
