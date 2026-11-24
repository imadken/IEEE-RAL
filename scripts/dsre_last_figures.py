"""Four reproducible scientific figures from sealed counts and calibration only."""

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/dsre-final-matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from dsre_evidence_statistical_audit import cp
from dsre_last_common import ROOT, read
from matplotlib.patches import Rectangle

OUT = Path("research/dsre_final_science/figures")
HIST = Path("results/dsre-evidence-aware/20261117-prospective/prospective")


def finish(fig, name):
    fig.savefig(
        OUT / (name + ".pdf"), bbox_inches="tight", metadata={"CreationDate": None}
    )
    fig.savefig(OUT / (name + ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def table(name, rows):
    with (OUT / (name + ".csv")).open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def marginal_plane():
    fig, (ax, world) = plt.subplots(
        1,
        2,
        figsize=(10, 4),
        gridspec_kw={"width_ratios": [1.4, 1]},
        layout="constrained",
    )
    pc, pr = np.meshgrid(np.linspace(0, 1, 401), np.linspace(0, 1, 401))
    approved = (pr - pc >= 0.05 - 1e-12) & ((pc <= 0.1 + 1e-12) | (pr >= 0.9 - 1e-12))
    ax.contourf(
        pc, pr, approved, levels=[-0.5, 0.5, 1.5], colors=["#f2f2f2", "#b8dcca"]
    )
    ax.plot([0, 0.95], [0.05, 1], color="#56616e", lw=1, label="gain = .05")
    data = []
    for task, path, color in [
        ("Pick", HIST / "PickCube-v1/models/logged.json", "#315ca8"),
        ("Push", ROOT / "model_frozen.json", "#c46b21"),
    ]:
        if not path.exists():
            continue
        model = read(path)
        for leaf, entry in model["leaves"].items():
            e = entry["evidence"]
            x = e["p0"]
            y = e["p1"]
            b = entry["bounds"]
            ax.add_patch(
                Rectangle(
                    (x["lo"], y["lo"]),
                    x["hi"] - x["lo"],
                    y["hi"] - y["lo"],
                    facecolor="none",
                    edgecolor=color,
                    lw=1.4,
                )
            )
            ax.plot(
                (x["lo"] + x["hi"]) / 2,
                (y["lo"] + y["hi"]) / 2,
                "o",
                color=color,
                ms=4,
                label=task + " calibration intervals" if leaf == "0" else None,
            )
            data.append(
                {
                    "task": task,
                    "leaf": leaf,
                    "Lc": x["lo"],
                    "Uc": x["hi"],
                    "Lr": y["lo"],
                    "Ur": y["hi"],
                    "harm_upper": b["harm_upper"] if b else None,
                    "gain_lower": b["gain_lower"] if b else None,
                }
            )
    ax.set(
        xlim=(-0.025, 1.025),
        ylim=(-0.025, 1.025),
        xlabel="continue marginal completion $p_c$",
        ylabel="recover marginal completion $p_r$",
        title="A. Exact-marginal certifiable region",
    )
    ax.legend(fontsize=8, loc="lower right")
    ax.text(
        0.48,
        0.08,
        r"Primary: $H\leq .10$, $G\geq .05$",
        transform=ax.transAxes,
        fontsize=9,
    )
    qs = np.array([[0.4, 0.2, 0, 0.4], [0, 0.6, 0.4, 0]])
    xx = np.arange(4)
    for i, color in enumerate(["#315ca8", "#c46b21"]):
        world.bar(
            xx + (i - 0.5) * 0.34,
            qs[i],
            width=0.32,
            color=color,
            label=f"World {i + 1}: harm={qs[i, 2]:.1f}",
        )
    world.set(
        xticks=xx,
        xticklabels=["00", "01", "10", "11"],
        xlabel="joint outcomes $(Y_c,Y_r)$",
        ylabel="probability",
        ylim=(0, 0.75),
        title="B. Same logs, different harm",
    )
    world.text(
        0.5,
        0.91,
        "Both: $p_c=.4, p_r=.6, g=.2$",
        transform=world.transAxes,
        ha="center",
        fontsize=9,
    )
    world.legend(
        fontsize=8,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
    )
    finish(fig, "01_source_identification")
    table("01_calibration_rectangles", data)


def availability(frontiers, audit):
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), layout="constrained", sharey=True)
    data = []
    for ax, task, title in zip(
        axes,
        ["PickCube-v1", "PushCube-v1", "PointMaze_UMaze-v3"],
        [
            "Pick: historical inspected T",
            "Push: final prospective T",
            "Navigation: eligible historical T",
        ],
        strict=True,
    ):
        entry = frontiers["tasks"].get(task)
        if not entry:
            ax.text(0.5, 0.5, "No qualified new test", ha="center")
            continue
        fs = entry["empirical_frontiers"]
        f = fs.get(task + "|ALL_CONDITIONS", fs.get("ALL_CONDITIONS"))
        n = f["n"]
        policy = (
            audit["policies"].get("DSRE", {})
            if task == "PushCube-v1"
            else entry["policies"]["DSRE"]
        )
        recover = policy.get("recover", 0)
        numerators = [
            f["action_capacity"],
            f["observable_common_action_rows"],
            f["empirical_log_certifiable"],
            recover,
        ]
        labels = [
            "any action\nsucceeds",
            "common action\nper full X",
            "log-identifiable\npoint estimates",
            "calibrated\nrecover coverage",
        ]
        ax.bar(
            np.arange(4),
            np.asarray(numerators) / n,
            color=["#5b7c8d", "#91adbf", "#d0a257", "#4a8b69"],
        )
        for j, v in enumerate(numerators):
            ax.text(j, v / n + 0.025, f"{v}/{n}", ha="center", fontsize=8, rotation=25)
        ax.set(xticks=np.arange(4), xticklabels=labels, title=title, ylim=(0, 1.16))
        ax.tick_params(axis="x", labelsize=8)
        for label, value in zip(labels, numerators, strict=True):
            data.append(
                {
                    "task": task,
                    "quantity": label.replace("\n", " "),
                    "numerator": value,
                    "denominator": n,
                    "scope": "Separate quantities, not additive gaps; third column empirical only",
                }
            )
    axes[0].set_ylabel("fraction of checkpoint parents")
    finish(fig, "02_evidence_availability")
    table("02_evidence_availability", data)


def policies(frontiers, audit):
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), layout="constrained", sharey=True)
    data = []
    for ax, task, title in zip(
        axes,
        ["PickCube-v1", "PushCube-v1", "PointMaze_UMaze-v3"],
        [
            "Pick: inspected historical T",
            "Push: prospective T",
            "Navigation: raw T includes1 prefix success",
        ],
        strict=True,
    ):
        if task == "PushCube-v1":
            ps = audit["policies"]
            names = [
                "always_continue",
                "always_recover",
                "DSRE",
                "CART_same_gate",
                "outcome_regression_same_gate",
            ]
            ceiling = audit["paired_hindsight_completion"]
        else:
            entry = frontiers["tasks"][task]
            ps = dict(
                read(ROOT / "legacy_policy_rescoring.json")["tasks"][task]["policies"]
            )
            names = ["always_continue", "always_recover", "DSRE", "CART2_matched"]
            ceiling = (
                entry["empirical_frontiers"][task + "|ALL_CONDITIONS"][
                    "action_capacity"
                ]
                + entry["absorbing_prefix"]
            )
            if task == "PickCube-v1":
                ps.update(read(ROOT / "legacy_regression/evaluation.json")["policies"])
                names += ["outcome_regression_same_gate"]
        if not ps:
            ax.text(0.5, 0.5, "No completed prospective test", ha="center")
            continue
        for i, name in enumerate(names):
            p = ps[name]
            n = p["n"]
            success = p["success"]
            harm = p.get("harm", 0)
            recover = p["recover"]
            low, high = cp(success, n, 0.025)
            ax.bar(i, success / n, color="#315ca8" if name == "DSRE" else "#94a6b8")
            ax.errorbar(
                i,
                success / n,
                yerr=[[success / n - low], [high - success / n]],
                color="#27313e",
                capsize=3,
                fmt="none",
                lw=1,
            )
            ax.text(
                i,
                0.025,
                f"{success}/{n}\nH={harm}, R={recover}",
                ha="center",
                va="bottom",
                fontsize=7,
                color="white",
                rotation=90,
            )
            data.append(
                {
                    "task": task,
                    "method": name,
                    "n": n,
                    "success": success,
                    "harm": harm,
                    "recover": recover,
                    "completion_lo": low,
                    "completion_hi": high,
                }
            )
        ax.axhline(
            ceiling / ps["DSRE"]["n"],
            color="#4a8b69",
            ls="--",
            lw=1,
            label="paired hindsight ceiling",
        )
        ax.set(
            xticks=np.arange(len(names)),
            xticklabels=["C", "R", "DSRE", "CART", "regression"][: len(names)],
            ylim=(0, 1.07),
            title=title,
        )
        ax.tick_params(axis="x", labelsize=8)
        ax.legend(fontsize=7, loc="upper center")
    axes[0].set_ylabel("completion fraction; descriptive parent CP95")
    finish(fig, "03_matched_policy_results")
    table("03_matched_policy_results", data)


def cost_curves(frontiers):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), layout="constrained")
    data = []
    markers = ["o", "s", "^", "D", "v"]
    for ax, task in zip(axes, ["PickCube-v1", "PointMaze_UMaze-v3"], strict=True):
        for i, (strategy, rows) in enumerate(
            frontiers["matched_historical_cost_curves"][task].items()
        ):
            xs = [r["actual_observed_calibration_actions"] for r in rows]
            ys = [r["DSRE"]["recover"] / r["DSRE"]["n"] for r in rows]
            ax.plot(
                xs,
                ys,
                marker=markers[i],
                label=strategy.replace("_", " "),
                alpha=0.8,
                ms=5,
            )
            for r in rows:
                data.append(
                    {
                        "task": task,
                        "strategy": strategy,
                        "additional_budget": r["registered_additional_action_budget"],
                        "actual_calibration_actions": r[
                            "actual_observed_calibration_actions"
                        ],
                        "logs": r["logs"],
                        "paired_second_outcomes": r["pairs"],
                        "recover": r["DSRE"]["recover"],
                        "success": r["DSRE"]["success"],
                        "n": r["DSRE"]["n"],
                    }
                )
        ax.set(
            xlabel="actual observed calibration actions (base included)",
            ylabel="qualified recover / raw256 test parents",
            title=task,
            ylim=(-0.025, 0.52),
        )
        ax.legend(fontsize=7)
    finish(fig, "04_matched_evidence_cost")
    table("04_matched_evidence_cost", data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )
    frontiers = read(ROOT / "evidence_frontier.json")
    audit = read(ROOT / "independent_final_audit.json")
    marginal_plane()
    availability(frontiers, audit)
    policies(frontiers, audit)
    cost_curves(frontiers)


if __name__ == "__main__":
    main()
