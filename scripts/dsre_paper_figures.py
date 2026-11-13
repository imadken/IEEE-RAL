"""Render anonymous DSRE methodology and finite-reference/cross-fit controls."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("rss2027/figures")
OLD = Path("results/dsre-evidence-repair/20261113T180828Z")


def figures():
    OUT.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(7, 2.35))
    ax.set(xlim=(0, 10), ylim=(0, 3))
    ax.axis("off")

    def box(x, y, w, h, label, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=0.05", fc=color, ec="#334155", lw=0.8
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8)

    def arrow(a, b):
        ax.add_patch(
            FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=10, color="#334155")
        )

    box(
        0.1,
        1.8,
        2.2,
        0.9,
        "Qualified reference\npaired continue/recover\nterminal outcomes",
        "#dbeafe",
    )
    box(
        3,
        1.8,
        2.6,
        0.9,
        "Offline channel enumeration\nmaximize finite strict mass\nfreeze channels + reference",
        "#dbeafe",
    )
    box(
        0.1,
        0.15,
        2.2,
        0.9,
        "Current observed facts\npredecision only\nunknowns retained",
        "#fef3c7",
    )
    box(
        3,
        0.15,
        2.6,
        0.9,
        "Minimum pure conjunction\n2 independent reference parents\nexact ordinary rule semantics",
        "#fef3c7",
    )
    box(
        6.4,
        1.65,
        3.4,
        1.05,
        "Action + minimum facts\n+ checkable literal witnesses\nFINITE REFERENCE ONLY",
        "#dcfce7",
    )
    box(
        6.4,
        0.1,
        3.4,
        1.15,
        "Abstain + all applicable witnesses\nobservation conflict / neither action\n/ missing or unsupported reference",
        "#fee2e2",
    )
    arrow((2.4, 2.25), (2.95, 2.25))
    arrow((4.3, 1.75), (4.3, 1.1))
    arrow((2.4, 0.6), (2.95, 0.6))
    arrow((5.65, 0.75), (6.35, 2.1))
    arrow((5.65, 0.55), (6.35, 0.65))
    fig.tight_layout(pad=0.3)
    fig.savefig(OUT / "method.pdf")
    fig.savefig(OUT / "method.png", dpi=180)
    plt.close(fig)
    met = json.loads((OLD / "metrics.json").read_text())

    def series(task, method, field="adequate"):
        return [
            met[f"{task}|exact_coverage|{b}|{method}|all_starts|all"]["counts"][field]
            for b in range(4)
        ]

    fig, axes = plt.subplots(1, 2, figsize=(7, 2.9))
    for ax, task, title, finite in zip(
        axes,
        ("PickCube-v1", "PushCube-v1"),
        ("PickCube", "PushCube"),
        ([183, 235, 237, 238], [0, 0, 0, 0]),
        strict=True,
    ):
        ax.plot(
            range(4), finite, "s--", label="Full-table finite ceiling", color="#64748b"
        )
        ax.plot(
            range(4),
            series(task, "DSRE"),
            "o-",
            label="Cross-fit DSRE successful",
            color="#2563eb",
        )
        ax.plot(
            range(4),
            series(task, "B1_two_strict"),
            "^:",
            label="Cross-fit 2-literal successful",
            color="#d97706",
        )
        ax.plot(
            range(4),
            series(task, "CART2_strict"),
            "v-.",
            label="Cross-fit CART2 successful",
            color="#059669",
        )
        ax.plot(
            range(4),
            series(task, "DSRE", "unacceptable"),
            "x-",
            label="Cross-fit DSRE unacceptable",
            color="#dc2626",
        )
        ax.set(
            title=title,
            xlabel="Allowed optional predicates (abstract cost)",
            xticks=range(4),
            ylim=(-7, 300),
        )
        ax.grid(alpha=0.2)
        if task == "PushCube-v1":
            ax.axhline(415, color="#9333ea", linestyle="--", linewidth=1)
            ax.set_ylim(-10, 440)
            ax.text(
                0.12,
                370,
                "Always recover: 415 / 422 successful\n(constant action, no strict justification)",
                fontsize=7,
                color="#6b21a8",
            )
    axes[0].set_ylabel("Checkpoint count (422 per task)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=2,
        fontsize=7,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.tight_layout(rect=(0, 0.22, 1, 1), pad=0.5)
    fig.savefig(OUT / "frontier.pdf")
    fig.savefig(OUT / "frontier.png", dpi=350)
    plt.close(fig)


if __name__ == "__main__":
    figures()
