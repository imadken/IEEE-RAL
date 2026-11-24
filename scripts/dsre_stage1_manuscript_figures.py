"""Draw the manuscript argument and tables from its independent audit output."""

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/dsre-stage1-mpl")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path("rss2027/stage1_evidence")
SOURCE = Path("research/dsre_stage1_manuscript/independent_numbers.json")
BLUE, ORANGE, INK, GREEN = "#32618b", "#a65624", "#263844", "#23705b"


def save(fig, name):
    for ext in ("pdf", "png", "svg"):
        fig.savefig(
            OUT / f"{name}.{ext}",
            dpi=450,
            metadata={"Creator": "", "Date": None}
            if ext == "svg"
            else {"Author": "", "Creator": "", "CreationDate": None}
            if ext == "pdf"
            else {},
        )
    plt.close(fig)
    svg = OUT / f"{name}.svg"
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n"
    )


def thesis():
    fig = plt.figure(figsize=(3.49, 3.75))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    def text(x, y, s, size=7.6, **kw):
        ax.text(x, y, s, fontsize=size, ha="center", va="center", color=INK, **kw)

    def box(x, y, w, h, s, fc="#f0f4f7", color=BLUE):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=.007,rounding_size=.012",
                linewidth=0.8,
                edgecolor=color,
                facecolor=fc,
            )
        )
        text(x + w / 2, y + h / 2, s)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.8,
                color=INK,
            )
        )

    text(0.50, 0.970, "OFFLINE: what can the evidence justify?", size=9, weight="bold")
    box(
        0.025, 0.850, 0.44, 0.080, "Paired checkpoint trials\n(simulator coupling only)"
    )
    box(
        0.535,
        0.850,
        0.44,
        0.080,
        "Randomized one-action logs\nknown propensity, one label",
    )
    text(0.50, 0.890, "or", size=7.3)
    arrow(0.245, 0.843, 0.38, 0.808)
    arrow(0.755, 0.843, 0.62, 0.808)
    box(
        0.11,
        0.740,
        0.78,
        0.066,
        "Compatible outcome models\nfor source D and whole region S",
    )
    arrow(0.50, 0.733, 0.50, 0.714)
    box(
        0.11,
        0.643,
        0.78,
        0.068,
        "Named obligation $o$: harm $h\\leq .10$, gain $g\\geq .05$\nminimum certificate $(E,S,D,o,B,W)$ or witness",
    )
    arrow(0.50, 0.636, 0.50, 0.615)
    text(
        0.50,
        0.597,
        "Freeze the qualified rule before test execution",
        size=7.7,
        weight="bold",
    )
    ax.plot([0.025, 0.975], [0.570, 0.570], color="#a8b4bc", lw=0.7)
    text(
        0.50,
        0.546,
        "ONLINE: one action, no counterfactual input",
        size=8.3,
        weight="bold",
    )
    box(0.025, 0.464, 0.25, 0.051, "Current facts $X$")
    box(0.365, 0.464, 0.29, 0.051, "Exact supported $S$", fc="#eaf3ef", color=GREEN)
    box(
        0.750,
        0.454,
        0.225,
        0.071,
        "Continue/recover\nor defer",
        fc="#eaf3ef",
        color=GREEN,
    )
    arrow(0.286, 0.490, 0.353, 0.490)
    arrow(0.665, 0.490, 0.738, 0.490)
    text(
        0.50,
        0.413,
        "Same marginals do not identify binary harm",
        size=8.0,
        weight="bold",
    )
    # Rows Y^0=0,1; columns Y^1=0,1. Both worlds are analytical.
    for center, matrix, h, color in [
        (0.255, [[0.4, 0.2], [0, 0.4]], 0, BLUE),
        (0.755, [[0, 0.6], [0.4, 0]], 0.4, ORANGE),
    ]:
        text(center, 0.379, "recover:  0       1", size=7.3)
        for i in range(2):
            text(center - 0.16, 0.340 - i * 0.041, str(i), size=7.3)
            for j in range(2):
                x = center - 0.08 + j * 0.105
                y = 0.321 - i * 0.041
                ax.add_patch(
                    Rectangle((x, y), 0.105, 0.041, fc="#f6f7f8", ec="#b9c2c8", lw=0.5)
                )
                text(
                    x + 0.0525,
                    y + 0.0205,
                    f"{matrix[i][j]:.1f}",
                    size=8,
                    weight="bold" if i == 1 and j == 0 else "normal",
                )
        text(center, 0.253, f"$h={h:.1f}$", size=8.1)
    text(0.50, 0.215, "Analytical: continue .4, recover .6, gain .2", size=7.6)
    ax.plot([0.025, 0.975], [0.188, 0.188], color="#a8b4bc", lw=0.7)
    # Schematic mechanisms; not fabricated robot imagery or measurements.
    for center, label in [
        (0.25, "Grasp: reapproach / regrasp"),
        (0.75, "Push: lift / reapproach"),
    ]:
        ax.add_patch(
            Rectangle(
                (center - 0.025, 0.108), 0.05, 0.046, ec=INK, fc="#c2d4e0", lw=0.8
            )
        )
        ax.plot(
            [center - 0.09, center - 0.09, center + 0.09, center + 0.09],
            [0.11, 0.164, 0.164, 0.11],
            color=INK,
            lw=1.5,
        )
        if center > 0.5:
            arrow(center + 0.04, 0.128, center + 0.15, 0.128)
        text(center, 0.081, label, size=7.2)
        text(center, 0.042, "256/256 qualified test parents", size=7.2)
    save(fig, "figure1_evidence")


def plane(data):
    fig, ax = plt.subplots(figsize=(3.49, 2.55))
    fig.subplots_adjust(left=0.15, right=0.97, bottom=0.19, top=0.96)
    p0, p1 = np.meshgrid(np.linspace(0, 1, 501), np.linspace(0, 1, 501))
    approved = (p1 - p0 >= 0.05) & ((p0 <= 0.10) | (p1 >= 0.90))
    ax.contourf(
        p0, p1, approved, levels=[-0.5, 0.5, 1.5], colors=["#f1f3f4", "#c2dfd2"]
    )
    ax.plot([0, 0.95], [0.05, 1], color="#8798a3", lw=0.7)
    for task, color, prefix in [
        ("PickCube-v1", BLUE, "G"),
        ("PushCube-v1", ORANGE, "P"),
    ]:
        for leaf, b in data[task]["calibration"].items():
            (lc, uc), (lr, ur) = b["intervals"]["c"], b["intervals"]["r"]
            ax.add_patch(
                Rectangle((lc, lr), uc - lc, ur - lr, fc="none", ec=color, lw=1.25)
            )
            if prefix == "G":
                ax.text(
                    max(0.07, uc + 0.018) if lc < 0.1 else lc - 0.07,
                    (lr + ur) / 2 + (0.035 if leaf in ("0", "3") else -0.035),
                    f"{prefix}{leaf}",
                    color=color,
                    fontsize=7.5,
                )
            else:
                ax.text(
                    0.10 if lc < 0.1 else lc - 0.055,
                    0.94 if lc < 0.1 else 0.93,
                    f"{prefix}{leaf}",
                    color=color,
                    fontsize=7.5,
                )
    ax.text(
        0.36,
        0.35,
        "Marginal-only\nprimary obligation\nunsupported",
        ha="center",
        fontsize=8,
        color=INK,
    )
    ax.set(
        xlim=(-0.02, 1.02),
        ylim=(-0.02, 1.02),
        xlabel="Continue success $p_0$",
        ylabel="Recover success $p_1$",
    )
    ax.xaxis.label.set_size(10.5)
    ax.yaxis.label.set_size(10.5)
    ax.tick_params(labelsize=7.5)
    ax.grid(alpha=0.12)
    save(fig, "figure2_identification")


def tables(data):
    names = [
        ("DSRE", "DSRE"),
        ("B7 exact rules", "exact_B7"),
        ("Direct partial ID", "direct_partial_ID"),
        ("CART + same gate", "CART_same_gate"),
        ("Regression + same gate", "outcome_regression_same_gate"),
        ("Always continue", "always_continue"),
        ("Always recover", "always_recover"),
    ]
    old = {
        "exact_B7": "ordinary_rules",
        "direct_partial_ID": "tabular_Kallus_adaptation",
        "CART_same_gate": "CART2_matched",
    }
    lines = [
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"Policy & R & Rescue & Harm & Futile & Done\\",
        r"\midrule",
    ]
    for task, label in [("PickCube-v1", "Grasp"), ("PushCube-v1", "Push")]:
        lines.append(
            r"\multicolumn{6}{l}{\textit{"
            + label
            + r"; 256 independent test parents}}\\"
        )
        for display, key in names:
            if task == "PickCube-v1":
                key = old.get(key, key)
            if task == "PickCube-v1" and key == "outcome_regression_same_gate":
                display += r"$^\dagger$"
            m = data[task]["methods"][key]
            lines.append(
                display
                + " & "
                + " & ".join(
                    str(m[k])
                    for k in ["recover", "rescue", "harm", "futile", "completion"]
                )
                + r"\\"
            )
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines.append(r"\end{tabular}")
    (OUT / "main_results.tex").write_text("\n".join(lines) + "\n")
    lines = [
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"Cell & $n_0$ & $n_1$ & $H_U$ & $G_L$ & Pass\\",
        r"\midrule",
    ]
    for task, prefix in [("PickCube-v1", "G"), ("PushCube-v1", "P")]:
        for leaf, b in data[task]["calibration"].items():
            passed = int(leaf) in data[task]["passed_leaves"]
            lines.append(
                f"{prefix}{leaf} & {b['n_c']} & {b['n_r']} & {b['harm_upper']:.3f} & {b['gain_lower']:.3f} & {'yes' if passed else 'no'}"
                + r"\\"
            )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (OUT / "calibration.tex").write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "dsre-stage1-evidence",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    data = json.loads(SOURCE.read_text())["results"]
    (OUT / "figure_data.json").write_text(
        json.dumps(
            {
                "results": {
                    task: {
                        k: value[k] for k in ("calibration", "passed_leaves", "methods")
                    }
                    for task, value in data.items()
                }
            },
            indent=2,
        )
        + "\n"
    )
    thesis()
    plane(data)
    tables(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    SOURCE, OUT = args.data, args.output
    main()
