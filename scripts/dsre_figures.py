"""Export scientific development figures and preregistered descriptive length caps."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    return json.loads(path.read_text())


def run(root):
    folder = root / "figures"
    folder.mkdir(exist_ok=True)
    config = load(Path("config/dsre_stage1.json"))
    metrics = load(root / "metrics.json")
    frontier = list(csv.DictReader((root / "frontier.csv").open()))
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    scatter = None
    for ax, task in zip(axes, config["tasks"], strict=True):
        points = [
            r
            for r in frontier
            if r["task"] == task
            and r["variant"] == "pose_proprioception"
            and r["mean_literals"] not in ("", "None")
        ]
        scatter = ax.scatter(
            [float(p["mean_literals"]) for p in points],
            [100 * float(p["coverage"]) for p in points],
            c=[100 * float(p["unacceptable_frequency"]) for p in points],
            vmin=0,
            vmax=100,
            cmap="viridis_r",
            s=34,
            alpha=0.7,
        )
        for method, offset in [
            ("DSRE", (5, -12)),
            ("B2_depth1", (6, 7)),
            ("B5_mean", (6, -17)),
            ("B3_full", (-70, 7)),
        ]:
            info = metrics[f"pose_proprioception/{task}/{method}/primary"]
            x, y = (
                info["rates"]["mean_literals_given_recommendation"]["value"],
                info["rates"]["coverage"]["value"],
            )
            if x is not None:
                ax.scatter([x], [100 * y], c="black", marker="x", s=35)
                ax.annotate(
                    method,
                    (x, 100 * y),
                    textcoords="offset points",
                    xytext=offset,
                    fontsize=8,
                )
            elif method == "DSRE":
                ax.text(
                    0.03,
                    0.08,
                    "DSRE: no recommendations",
                    transform=ax.transAxes,
                    fontsize=9,
                )
        ax.set(
            title=task,
            xlabel="Mean evidence literals among recommendations",
            ylabel="Checkpoint recommendation coverage (%)",
            xlim=(-0.2, 6.5),
            ylim=(-3, 105),
        )
        ax.grid(alpha=0.2)
    figure.colorbar(
        scatter, ax=axes, label="Unacceptable recommendations (%)", shrink=0.85
    )
    figure.suptitle(
        "Exploratory grouped cross-fitting: all frozen operating points\nZero independent deployment calibration; abstention is not success",
        fontsize=11,
    )
    figure.savefig(folder / "joint_frontier.png", dpi=160)
    plt.close(figure)
    prevalence = load(root / "paired_outcome_prevalence.json")
    figure, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    bottom = [0, 0]
    for category in ("continue_only", "recover_only", "both", "neither"):
        values = [prevalence[t].get(category, 0) for t in config["tasks"]]
        ax.bar(config["tasks"], values, bottom=bottom, label=category)
        for i, n in enumerate(values):
            if n:
                ax.text(
                    i, bottom[i] + n / 2, str(n), ha="center", va="center", fontsize=9
                )
        bottom = [a + b for a, b in zip(bottom, values, strict=True)]
    ax.set(
        ylabel="Qualified paired checkpoints",
        title="Measured terminal paired outcomes; reused development data",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, fontsize=8)
    figure.savefig(folder / "paired_outcomes.png", dpi=160)
    plt.close(figure)
    calibration = load(root / "calibration_feasibility.json")
    figure, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    strata = calibration["strata"]
    ax.bar(
        [f"{s['task']}\n{s['action']}" for s in strata],
        [s["expected_assigned_from200"] for s in strata],
    )
    ax.axhline(
        42, color="red", linestyle="--", label="42 assigned with zero errors needed"
    )
    ax.set(
        ylabel="Expected assigned parents from 200 (planning only)",
        title="Frozen full-table DSRE router; no independent calibration ran",
    )
    ax.legend(fontsize=9)
    figure.savefig(folder / "calibration_accrual.png", dpi=160)
    plt.close(figure)
    # These caps were declared before method numbers. They are descriptive
    # filtering of existing predictions, not newly calibrated or deployed routers.
    counts = defaultdict(lambda: [0, 0, 0, 0])
    with (root / "scored_primary.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            m = row["metrics"]
            for cap in range(9):
                key = row["variant"], row["task"], row["method"], cap
                c = counts[key]
                c[0] += 1
                if m["emitted"] and m["literal_sum"] <= cap:
                    c[1] += 1
                    c[2] += m["unacceptable"]
                    c[3] += m["literal_sum"]
    with (root / "descriptive_evidence_caps.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "variant",
                "task",
                "method",
                "cap",
                "episodes",
                "emitted",
                "unacceptable",
                "literal_sum",
                "status",
            ]
        )
        for key, values in sorted(counts.items()):
            writer.writerow([*key, *values, "DESCRIPTIVE_ONLY_NOT_CALIBRATED"])
    print({"figures": 3, "descriptive_cap_cells": len(counts)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    run(args.root)
