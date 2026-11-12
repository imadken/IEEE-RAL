"""Small reproducible scientific figures from verified case-study tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from dual_rec.failtime.experiment import read, save


def figures(root):
    output = root / "figures"
    output.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "savefig.dpi": 180,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    inventory = []

    def finish(fig, name, caption):
        fig.tight_layout()
        for extension in ("png", "pdf"):
            fig.savefig(output / (name + "." + extension), bbox_inches="tight")
        plt.close(fig)
        inventory.append({"name": name, "caption": caption})

    reboot = read(root, "reboot_reproduction.json")["summary"]
    rows = [r for r in reboot if r["variant"] == "Q"]
    names = [r["method"] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(8, 3.7))
    ax.bar(
        x - 0.19,
        [r["timely"] for r in rows],
        width=0.38,
        label="Continuous first alarm",
        color="#28739d",
    )
    ax.bar(
        x + 0.19,
        [r["INVALID_onset_reset_timely"] for r in rows],
        width=0.38,
        label="INVALID onset reset",
        color="#d58336",
    )
    ax.set(
        xticks=x,
        xticklabels=names,
        ylabel="Timely alarms / 55 failure records",
        ylim=(0, 59),
        title="REBOOT: same scores, different alarm protocol (Q)",
    )
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.01), ncol=2)
    ax.set_title("REBOOT: same scores, different alarm protocol (Q)", pad=38)
    finish(
        fig,
        "reboot_reset",
        "Controlled invalid diagnostic on the same stored scores; not a reproduction of an alleged author error. Original thresholds, strict target windows and persistence retained.",
    )
    rows = [
        r
        for r in read(root, "failtime_summary.json")
        if r["alpha"] == 0.1 and r["persistence"] == 0.1 and r["stress"] == "clean"
    ]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]}
    )
    bottom = np.zeros(len(rows))
    for metric, color in (
        ("timely", "#328a70"),
        ("premature", "#d58336"),
        ("late", "#6b87ba"),
        ("missed", "#c9c9c9"),
    ):
        count = np.array([r[metric] for r in rows])
        axes[0].bar(x, count, bottom=bottom, label=metric, color=color)
        bottom += count
    axes[0].set(
        ylabel="Failure records / 57",
        ylim=(0, 64),
        title="FailTime-Long: grouped out-of-fold first alarms",
    )
    axes[0].legend(ncol=4, frameon=False, loc="upper center")
    y = np.array([r["rates"]["clean_alarm"] for r in rows])
    bounds = np.array([r["wilson95"]["clean_alarm"] for r in rows])
    axes[1].bar(x, 100 * y, color="#28739d")
    axes[1].errorbar(
        x,
        100 * y,
        yerr=100 * np.stack([y - bounds[:, 0], bounds[:, 1] - y]),
        fmt="none",
        color="black",
        capsize=3,
    )
    axes[1].set(
        xticks=x,
        xticklabels=[r["method"] for r in rows],
        ylabel="Success alarms (%)",
        ylim=(0, 100),
    )
    axes[1].tick_params(axis="x", rotation=30)
    finish(
        fig,
        "failtime_oof",
        "All 100 previously exposed recordings; 57 failures and 43 successful references, 13 tasks and two robots. Primary alpha .10 and persistence .1s. Success-rate whiskers are descriptive recording-level Wilson intervals, not cluster-adjusted confirmation.",
    )
    recovery = read(root, "recoverbench_reproduction.json")["summary"]
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(recovery))
    ax.bar(
        x,
        [r["initial_success"] for r in recovery],
        label="Already successful starts",
        color="#c9c9c9",
    )
    ax.bar(
        x,
        [r["new_success"] for r in recovery],
        bottom=[r["initial_success"] for r in recovery],
        label="New first-hit successes",
        color="#328a70",
    )
    ax.set(
        xticks=x,
        xticklabels=[
            r["task"]
            + "\n"
            + ("checker" if "checker" in r["variant"] else "raw / fresh")
            for r in recovery
        ],
        ylabel="Source tapes / 6 per condition",
        ylim=(0, 6.6),
        title="RecoverBench pinned interface diagnostics",
    )
    ax.legend(frameon=False)
    for i, row in enumerate(recovery):
        if row["task"] == "pick_place" and "direct" in row["variant"]:
            ax.text(i, 1.15, "714 steps\n>500-step budget", ha="center", fontsize=9)
    finish(
        fig,
        "recoverbench_execution",
        "Two workflows jointly change reset/cache/goal-update conditions, so this is not a one-factor causal fix. PickPlace raw first success occurs at step 714, beyond the original 500-step target budget. These are local source-interface diagnostics, not official policy recovery rates.",
    )
    with (root / "primary_failtime.csv").open("w") as stream:
        fields = [
            "method",
            "failures",
            "successes",
            "timely",
            "premature",
            "late",
            "missed",
            "clean_alarms",
            "false_alarms_per_hour",
            "observable_failures",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    save(output / "captions.json", inventory)
    print({"scientific_figures": len(inventory)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    figures(args.root)


if __name__ == "__main__":
    main()
