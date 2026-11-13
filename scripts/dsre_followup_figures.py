"""Paper figures with explicit finite-reference, held-out and necessity estimands."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load(path):
    return json.loads(path.read_text())


def figures(root):
    out = Path("rss2027/figures")
    out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42})
    previous = Path("results/dsre-rss2027/20261113T193554Z")
    old = load(previous / "reused_stratified_tables.json")
    finite = load(previous / "reused_finite_ceiling.json")
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.5), sharey=True)
    styles = [
        ("DSRE", "#2563eb", "o-", "Cross-fit strict DSRE: successful"),
        ("B1_two_strict", "#d97706", "^:", "Cross-fit pure cap2: successful"),
        ("CART2_strict", "#059669", "v-.", "Cross-fit strict CART2: successful"),
        ("CART2_beta10", "#9333ea", "d--", "Cross-fit .9 CART2: provisional"),
    ]
    for ax, task, title in zip(
        axes, ("PickCube-v1", "PushCube-v1"), ("PickCube", "PushCube"), strict=True
    ):
        ax.plot(
            range(4),
            [finite[f"{task}|{b}"]["mass"] for b in range(4)],
            "s--",
            color="#64748b",
            label="Full-reference finite ceiling",
        )
        for method, color, style, label in styles:
            ax.plot(
                range(4),
                [old[f"{task}|{b}|{method}|all"]["successful"] for b in range(4)],
                style,
                color=color,
                label=label,
            )
        ax.plot(
            range(4),
            [old[f"{task}|{b}|DSRE|all"]["unacceptable"] for b in range(4)],
            "x-",
            color="#dc2626",
            label="Cross-fit strict DSRE: unacceptable",
        )
        ax.set(
            title=title,
            xlabel="Allowed extra Boolean predicates",
            xticks=range(4),
            ylim=(-10, 435),
        )
        ax.grid(alpha=0.2)
        if task == "PushCube-v1":
            ax.text(
                0.1,
                260,
                "Always recover: 415 / 422\nStrict methods: 0 / 422",
                fontsize=7,
            )
    axes[0].set_ylabel("Checkpoints / 422")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, -0.01)
    )
    fig.tight_layout(rect=(0, 0.30, 1, 1), pad=0.4)
    fig.savefig(out / "frontier.pdf")
    fig.savefig(out / "frontier.png", dpi=350)
    plt.close(fig)
    suffix = load(root / "suffix_results.json")["tables"]
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.3), sharey=True)
    categories = [
        ("continue_only", "Continue required", "#2563eb"),
        ("recover_only", "Recover required", "#d97706"),
        ("both", "Either action adequate", "#16a34a"),
    ]
    for ax, pop, title in zip(
        axes,
        ("all", "initial_failure"),
        ("All PickCube starts", "Initially unsuccessful PickCube"),
        strict=True,
    ):
        totals = [
            suffix.get(f"PickCube-v1|{b}|DSRE|{pop}", {}).get("checkpoints", 0)
            for b in (0, 1)
        ]
        bottoms = np.zeros(2)
        for category, label, color in categories:
            counts = []
            for b in (0, 1):
                records = load(root / "suffix_prediction_records.json")
                counts.append(
                    sum(
                        r["successful"]
                        for r in records
                        if r["task"] == "PickCube-v1"
                        and r["budget"] == b
                        and r["method"] == "DSRE"
                        and r["category"] == category
                        and (pop == "all" or not r["initial_success"])
                    )
                )
            heights = np.array(
                [100 * n / d if d else 0 for n, d in zip(counts, totals, strict=True)]
            )
            ax.bar([0, 1], heights, 0.55, bottom=bottoms, label=label, color=color)
            bottoms += heights
        bad = [
            suffix.get(f"PickCube-v1|{b}|DSRE|{pop}", {}).get("unacceptable", 0)
            for b in (0, 1)
        ]
        bad_heights = [
            100 * n / d if d else 0 for n, d in zip(bad, totals, strict=True)
        ]
        ax.bar(
            [0, 1],
            bad_heights,
            0.55,
            bottom=bottoms,
            label="Unacceptable choice",
            color="#dc2626",
            hatch="//",
        )
        for b in (0, 1):
            row = suffix.get(f"PickCube-v1|{b}|DSRE|{pop}", {})
            ax.text(
                b,
                bottoms[b] + bad_heights[b] + 3,
                f"{row.get('successful', 0)}/{totals[b]} good\n{bad[b]} bad",
                ha="center",
                fontsize=8,
            )
        ax.set(title=title, xticks=[0, 1], xticklabels=["b0", "b1"], ylim=(0, 106))
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Fraction of checkpoints (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(
        h, l, loc="lower center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, -0.01)
    )
    fig.tight_layout(rect=(0, 0.25, 1, 1), pad=0.4)
    fig.savefig(out / "necessity.pdf")
    fig.savefig(out / "necessity.png", dpi=350)
    plt.close(fig)
    print(
        "Finite-reference/cross-fit frontier and suffix-only decision-necessity figures rendered"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    figures(parser.parse_args().root)
