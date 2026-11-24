"""Draw original source-grounded Stage 1 figures from independently checked facts."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main(root):
    source = root / "scientific_consolidation.json"
    d = json.loads(source.read_text())
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "savefig.dpi": 350,
        }
    )
    out = Path("rss2027/figures")
    ledger = {}

    def save(fig, name, fields):
        files = []
        for ext in ("png", "pdf"):
            p = out / (name + "." + ext)
            fig.savefig(
                p,
                bbox_inches="tight",
                pad_inches=0.08,
                metadata={"Author": "", "Title": name}
                if ext == "pdf"
                else {"Software": "Scientific figure"},
            )
            files.append(
                {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            )
        ledger[name] = {
            "source": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "fields": fields,
            "files": files,
            "original_graphic": True,
            "third_party_figure_copies": False,
            "paper_uses_png": "Avoids plot font embedding changes to the official TeX fonts.",
        }
        plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.05))
    examples = [
        (x["case"], x["history"]["current"], x["futures"])
        for x in d["historical_conflict_examples"]
    ]
    new = next(x for x in d["physical_witnesses"] if x["kind"] == "neither_witness")
    examples.append(
        (new["row"], new["row"]["runtime_history"]["current"], new["futures"])
    )
    for i, (ax, (r, h, futures)) in enumerate(zip(axes, examples, strict=True)):
        goal = np.array(h["goal_position"])
        dims = [0, 1] if i < 2 else [0, 2]
        for name, marker, color in (
            ("object_position", "s", "#c37c1d"),
            ("tcp_position", "+", "#333333"),
        ):
            pos = 100 * (np.array(h[name]) - goal)
            ax.scatter(*pos[dims], marker=marker, color=color, s=40, zorder=5)
        ax.scatter(0, 0, marker="*", s=65, color="#389d77", zorder=6)
        for a, marker, color in (
            ("continue", "o", "#3976a8"),
            ("recover", "^", "#a14367"),
        ):
            p = 100 * (np.array(futures[a]["object_position"]) - goal)
            ax.scatter(*p[dims], marker=marker, s=34, color=color)
        good = r["outcomes"]
        title = "Push D" if i == 0 else "Push E" if i == 1 else "Pick F"
        ax.set_title(
            f"{title}: C={int(good['continue_value'])}, R={int(good['recover_value'])}",
            fontsize=10,
        )
        ax.set_xlabel("x relative to goal (cm)")
        ax.set_ylabel(("y" if i < 2 else "z") + " − goal (cm)")
        if i < 2:
            ax.set_xlim(-17, 1.8)
            ax.set_ylim(-6, 5)
            ax.text(
                0.04,
                0.05,
                f"dx={100 * (h['object_position'][0] - goal[0]):.3f} cm",
                transform=ax.transAxes,
                fontsize=8,
            )
        else:
            ax.set_xlim(-2.5, 2.5)
            ax.set_ylim(-31, 3)
        ax.grid(alpha=0.15)
    fig.legend(
        [
            plt.Line2D(
                [],
                [],
                marker=m,
                color="none",
                markeredgecolor=c,
                markerfacecolor=c,
                linestyle="none",
            )
            for m, c in (
                ("s", "#c37c1d"),
                ("+", "#333333"),
                ("*", "#389d77"),
                ("o", "#3976a8"),
                ("^", "#a14367"),
            )
        ],
        [
            "predecision object",
            "hand",
            "goal",
            "C terminal object",
            "R terminal object",
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=5,
        frameon=False,
        fontsize=8,
    )
    fig.tight_layout(w_pad=1.1)
    save(
        fig,
        "stage1_synthesis_witnesses",
        ["historical_conflict_examples", "physical_witnesses[kind=neither_witness]"],
    )

    fig, axes = plt.subplots(
        1, 2, figsize=(7.0, 2.4), gridspec_kw={"width_ratios": [1, 1.2]}
    )
    ax = axes[0]
    vals = [d["observation_mass"][str(n)] for n in (6, 7, 12)] + [d["action_feasible"]]
    ax.barh(
        range(4), vals, color=["#a9bfce", "#759bb4", "#47718f", "#389d77"], height=0.65
    )
    for i, v in enumerate(vals):
        ax.text(v + 8, i, str(v), va="center", fontsize=9)
    ax.set_yticks(range(4), ["6 facts", "7 facts", "12 facts*", "Action feasible"])
    ax.invert_yaxis()
    ax.set_xlim(0, 660)
    ax.set_title("Same-table common action", fontsize=10)
    ax.set_xlabel("Common-action mass / 640")
    fig.text(
        0.03,
        0.02,
        "*Extra-information diagnostic.\nNeither-success: 48 / 640.",
        fontsize=8,
    )
    ax = axes[1]
    keys = [
        "clean|point_proposal|DSRE_risk",
        "clean|point_proposal|CART2_beta10",
        "bound005|robust_proposal|DSRE_risk",
        "bound005|robust_proposal|CART2_beta10",
    ]
    labels = ["DSRE/B7, 0", "CART2, 0", "DSRE/B7, 5 mm", "CART2, 5 mm"]
    left = np.zeros(4)
    for field, color, label in (
        ("adequate", "#3976a8", "adequate"),
        ("inadequate", "#c15749", "inadequate"),
        ("stop", "#d6dade", "STOP"),
    ):
        counts = [d["tables"][k][field] for k in keys]
        ax.barh(range(4), counts, left=left, color=color, height=0.65, label=label)
        left += counts
    for i, k in enumerate(keys):
        t = d["tables"][k]
        ax.text(
            t["adequate"] / 2,
            i,
            str(t["adequate"]),
            va="center",
            ha="center",
            color="white",
        )
        ax.text(650, i, f"bad={t['inadequate']}", va="center", fontsize=8)
    ax.set_yticks(range(4), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 770)
    ax.set_title(
        "Frozen-reference proposals\nunqualified under new source", fontsize=10
    )
    ax.set_xlabel("Paired confirmation checkpoints")
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.73),
        ncol=3,
        frameon=False,
        fontsize=8,
    )
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.35, top=0.84, wspace=0.85)
    save(
        fig,
        "stage1_synthesis_scopes",
        ["observation_mass", "action_feasible", "tables[clean|bound005]"],
    )
    (root / "figure_source_ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps({"figures": list(ledger), "new_physics": 0}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    main(p.parse_args().root)
