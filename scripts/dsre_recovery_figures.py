"""Render verified paired recovery outcomes without mixing abstention and physics."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_followup_batch import atomic, read


def draw(root):
    result = read(root / "test_analysis.json")
    if result["status"] == "NO_QUALIFIED_TEST_PARENTS":
        return
    names = [
        "DSRE_strict",
        "DSRE_risk",
        "B7_risk",
        "CART2_beta10",
        "B0_continue",
        "B0_recover",
    ]
    labels = ["Strict", "Risk", "Ordinary", "CART2", "Fixed C", "Fixed R"]
    n = result["checkpoints"]
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 9})
    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.4))
    classes = ["continue_only", "recover_only", "both", "neither"]
    colors = ["#4477aa", "#228833", "#66ccee", "#cc6677"]
    count = [result["paired_classes"].get(c, 0) for c in classes]
    axes[0].bar(np.arange(4), count, color=colors)
    axes[0].set_xticks(range(4), ["C only", "R only", "Both", "Neither"])
    axes[0].set_title("Actual paired outcomes")
    axes[0].set_ylabel("Checkpoints")
    for x, v in enumerate(count):
        axes[0].text(x, v + 1, str(v), ha="center", fontsize=9)
    bottom = np.zeros(len(names))
    data = {}
    for field, color, label in [
        ("successful", "#228833", "Good"),
        ("unacceptable", "#cc6677", "Bad"),
        ("deferred", "#bbbbbb", "STOP"),
    ]:
        values = np.array(
            [
                result["tables"][f"PickCube-v1|{m}|calibrated|clean|all"][field]
                for m in names
            ]
        )
        axes[1].bar(
            np.arange(len(names)), values, bottom=bottom, color=color, label=label
        )
        bottom += values
        data[field] = values.tolist()
    axes[1].set_xticks(range(len(names)), labels, rotation=35, ha="right")
    axes[1].set_title("Own calibrated decisions\nSTOP=0 selective credit")
    axes[1].set_ylim(0, n * 1.18)
    axes[1].legend(frameon=False, ncol=3, fontsize=7, loc="upper center")
    required = [
        result["tables"][f"PickCube-v1|{m}|calibrated|clean|all"][
            "required_recovery_success"
        ]
        for m in names
    ]
    axes[2].bar(range(len(names)), required, color="#228833")
    axes[2].axhline(
        result["paired_classes"].get("recover_only", 0),
        ls="--",
        color="#333333",
        lw=0.8,
        label="All recover-only states",
    )
    axes[2].set_xticks(range(len(names)), labels, rotation=35, ha="right")
    axes[2].set_title("Selected necessary recoveries")
    axes[2].legend(frameon=False, fontsize=7)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.tight_layout(pad=0.7)
    destination = Path("rss2027/figures/stage1_recovery_confirmation")
    fig.savefig(destination.with_suffix(".png"), dpi=240, bbox_inches="tight")
    fig.savefig(destination.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    atomic(
        root / "recovery_figure_data.json",
        {
            "paired_classes": dict(zip(classes, count, strict=True)),
            "methods": names,
            "decisions": data,
            "required_recovery": required,
            "source": "test_analysis.json",
            "confidence_intervals": "Reported in tables/text; repeated conditions are not independent samples.",
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    draw(a.root)
