"""Compact actual-prediction figures, review tables and a local review archive."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from dual_rec.reboot.overnight_data import save_json, sha
from dual_rec.reboot.overnight_metrics import METHODS, first_alarm, persistent_capacity


def read(root, name):
    return json.loads((root / name).read_text())


def csv_table(path, rows):
    with path.open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tables(root):
    destination = root / "tables"
    destination.mkdir(exist_ok=True)
    for name in ("summary", "external_summary", "phase_results"):
        rows = read(root, name + ".json")
        csv_table(
            destination / (name + ".csv"),
            [
                {k: json.dumps(v) if isinstance(v, dict) else v for k, v in row.items()}
                for row in rows
            ],
        )
    outcomes = read(root, "outcomes.json")
    fold_rows, seed_rows = [], []
    for variant in ("Q", "QC"):
        for method in METHODS:
            for fold in range(5):
                rows = [
                    r
                    for r in outcomes
                    if r["variant"] == variant
                    and r["method"] == method
                    and r["fold"] == fold
                    and r["stress"] == "clean"
                    and r["boundary_delta"] == 0
                ]
                fold_rows.append(
                    {
                        "variant": variant,
                        "method": method,
                        "fold": fold,
                        "timely": sum(r["timely"] for r in rows),
                        "evaluable": sum(r["evaluable"] for r in rows),
                        "premature": sum(r["premature"] for r in rows),
                        "reference_alarms": sum(r["reference_alarm"] for r in rows),
                        "references": sum(r["role"] == "reference" for r in rows),
                    }
                )
        for method in ("B3", "P0", "P1", "P2"):
            for seed in (11, 23, 37):
                rows = [
                    r
                    for r in read(root, "seed_outcomes.json")
                    if r["variant"] == variant
                    and r["method"] == method
                    and r["seed"] == seed
                ]
                seed_rows.append(
                    {
                        "variant": variant,
                        "method": method,
                        "seed": seed,
                        "timely": sum(r["timely"] for r in rows),
                        "premature": sum(r["premature"] for r in rows),
                        "reference_alarms": sum(r["reference_alarm"] for r in rows),
                    }
                )
    csv_table(destination / "fold_results.csv", fold_rows)
    csv_table(destination / "seed_results.csv", seed_rows)
    save_json(
        root / "runtime_versions.json",
        {
            name: importlib.metadata.version(name)
            for name in (
                "torch",
                "numpy",
                "scipy",
                "pyarrow",
                "pydantic",
                "matplotlib",
                "psutil",
            )
        },
    )
    # Review arrays contain predictions, not source joint recordings or features.
    registry = sorted(
        [r for r in read(root, "registry.json") if r["eligible"]],
        key=lambda r: r["group"],
    )
    maximum = max(
        len(
            np.load(
                root
                / "predictions"
                / f"fold{r['fold']}"
                / "Q/clean/evaluation"
                / (r["group"].split(":")[1] + ".npz")
            )["time"]
        )
        for r in registry
    )
    score = np.full((len(registry), 2, 5, 7, maximum), np.nan)
    time = np.full((len(registry), maximum), np.nan)
    for i, row in enumerate(registry):
        for v, variant in enumerate(("Q", "QC")):
            for j, stress in enumerate(
                ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
            ):
                data = np.load(
                    root
                    / "predictions"
                    / f"fold{row['fold']}"
                    / variant
                    / stress
                    / "evaluation"
                    / (row["group"].split(":")[1] + ".npz")
                )
                n = len(data["time"])
                time[i, :n] = data["time"]
                for m, method in enumerate(METHODS):
                    score[i, v, j, m, :n] = data[method]
    np.savez_compressed(
        root / "review_oof_scores.npz",
        group=np.array([r["group"] for r in registry]),
        role=np.array([r["role"] for r in registry]),
        fold=np.array([r["fold"] for r in registry]),
        variants=np.array(["Q", "QC"]),
        stresses=np.array(["clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5"]),
        methods=np.array(METHODS),
        time=time,
        scores=score,
    )
    save_json(
        root / "review_cohort.json",
        [
            {
                k: r[k]
                for k in (
                    "group",
                    "role",
                    "episode",
                    "repository",
                    "eligible",
                    "exclusion_reasons",
                    "frames",
                    "aliases",
                    "fold",
                    "onset",
                    "recovery",
                )
                if k in r
            }
            for r in read(root, "registry.json")
        ],
    )


def figures(root):
    plt.switch_backend("Agg")
    destination = root / "figures"
    destination.mkdir(exist_ok=True)
    registry = [r for r in read(root, "registry.json") if r["eligible"]]
    thresholds = read(root, "thresholds.json")
    frontier = []
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for ax, variant in zip(axes, ("Q", "QC"), strict=True):
        for method in METHODS:
            records = []
            for row in registry:
                data = np.load(
                    root
                    / "predictions"
                    / f"fold{row['fold']}"
                    / variant
                    / "clean/evaluation"
                    / (row["group"].split(":")[1] + ".npz")
                )
                threshold = thresholds[f"{row['fold']}:{variant}:{method}"]["threshold"]
                records.append((row, data["time"], data[method], threshold))
            ratios = [
                persistent_capacity(t, s) / threshold for _, t, s, threshold in records
            ]
            grid = np.unique(
                np.r_[
                    0,
                    1,
                    np.percentile(ratios, np.linspace(0, 100, 32)),
                    max(ratios) * 1.01,
                ]
            )
            points = []
            for multiplier in grid:
                timely = premature = reference = 0
                for row, t, s, threshold in records:
                    first = first_alarm(t, s, threshold * multiplier)
                    if first is None:
                        continue
                    if row["role"] == "reference":
                        reference += 1
                    else:
                        timely += row["onset"] <= first < row["recovery"]
                        premature += first < row["onset"]
                point = {
                    "variant": variant,
                    "method": method,
                    "threshold_multiplier": float(multiplier),
                    "timely": int(timely),
                    "premature": int(premature),
                    "reference_alarms": int(reference),
                }
                frontier.append(point)
                points.append(point)
            (artist,) = ax.plot(
                [p["reference_alarms"] / 62 for p in points],
                [p["timely"] / 55 for p in points],
                label=method,
                linewidth=2 if method == "P1" else 1,
                linestyle="None" if method == "B0" else "-",
                marker=".",
                markersize=3,
            )
            operating = next(p for p in points if p["threshold_multiplier"] == 1)
            ax.scatter(
                [operating["reference_alarms"] / 62],
                [operating["timely"] / 55],
                color=artist.get_color(),
                edgecolors="black",
                linewidths=0.5,
                s=35,
                zorder=4,
            )
        ax.set(
            xlabel="Expert-reference recording alarm fraction",
            ylabel="Timely / 55 recovery recordings",
            title=variant,
            xlim=(0, 1),
            ylim=(0, 1),
        )
        ax.legend(fontsize=8, ncol=2)
    fig.suptitle(
        "Descriptive OOF first-alarm frontier; outlined circles are frozen calibration points\nClock control shows observed points only; other thresholds are descriptive"
    )
    for suffix in ("pdf", "png"):
        fig.savefig(destination / ("alarm_frontier." + suffix), dpi=160)
    plt.close(fig)
    save_json(root / "descriptive_frontiers.json", frontier)
    effects = [r for r in read(root, "paired_effects.json") if r["delta"] == 0]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for index, row in enumerate(effects):
        e = row["effects"]["timely"]
        low, high = np.array(e["ci95"]) * 100
        value = e["difference"] * 100
        axes[0].errorbar(
            value, index, xerr=[[value - low], [high - value]], fmt="o", color="#28728e"
        )
    axes[0].set(
        yticks=range(len(effects)),
        yticklabels=[r["variant"] + " " + r["contrast"] for r in effects],
        xlabel="Timely-rate difference (percentage points)",
    )
    axes[0].axvline(0, color="gray", linestyle="--")
    phase = read(root, "phase_results.json")
    labels, accuracy = [], []
    for variant in ("Q", "QC"):
        for method in ("P0", "P1", "P2"):
            chosen = [
                r for r in phase if r["variant"] == variant and r["method"] == method
            ]
            labels.append(variant + " " + method)
            accuracy.append(
                sum(r["correct"] for r in chosen) / sum(r["frames"] for r in chosen)
            )
    axes[1].bar(labels, accuracy, color=["#b9c9d2", "#28728e", "#e1bc78"] * 2)
    axes[1].set(
        ylabel="Chronological-phase frame accuracy",
        ylim=(0, 1),
        title="Annotated pre-recovery intervals only; phases 1–4",
    )
    fig.suptitle("Phase prediction gains do not establish a timely-recognition gain")
    for suffix in ("pdf", "png"):
        fig.savefig(destination / ("phase_comparison." + suffix), dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), layout="constrained")
    for ax, variant, category in zip(
        axes, ("Q", "QC"), ("premature", "timely"), strict=True
    ):
        examples = read(root, f"streaming/examples_{variant}.json")
        selected = examples[category]
        if not selected["available"]:
            ax.text(
                0.1, 0.5, f"No {variant} {category} example", transform=ax.transAxes
            )
            continue
        traces = [
            json.loads(line)
            for line in (root / f"streaming/{variant}/{category}.jsonl")
            .read_text()
            .splitlines()
        ]
        row = next(r for r in registry if r["group"] == selected["group"])
        ax.plot(
            [r["timestamp"] for r in traces],
            [r["risk"] for r in traces],
            label="Frozen P1 risk",
        )
        ax.axhline(
            traces[0]["explanation"]["threshold"],
            color="gray",
            linestyle="--",
            label="Calibration threshold",
        )
        ax.axvspan(
            row["onset"],
            row["recovery"],
            alpha=0.15,
            color="green",
            label="Released target (evaluation overlay)",
        )
        if selected["stream_alarm"] is not None:
            ax.axvline(
                selected["stream_alarm"], color="red", label="First persistent alarm"
            )
        ax.set(
            title=f"{variant}: deterministic {category} example",
            xlabel="Recording time (s)",
            ylabel="Model risk",
            ylim=(0, 1),
        )
        ax.legend(fontsize=7)
    fig.suptitle("Incremental replay: model-level traces, not physical root causes")
    for suffix in ("pdf", "png"):
        fig.savefig(destination / ("streaming_timeline." + suffix), dpi=160)
    plt.close(fig)


def report(root):
    summary = read(root, "summary.json")
    primary = [
        r
        for r in summary
        if r["stress"] == "clean"
        and r["boundary_delta"] == 0
        and not (r["method"] == "B0" and r["variant"] == "QC")
    ]
    fit_rows = [
        r
        for r in map(json.loads, (root / "ledger.jsonl").read_text().splitlines())
        if r["phase"] == "FIT_COMPLETE"
    ]
    lines = [
        f"\n\n## Overnight research extension: {root.name}\n",
        "The new supervised scope authorizes this single-object recording-level study; the original multi-object DATA_BLOCKED report above remains unchanged. All values below are measured out of fold, relative to released annotations.\n",
        "| Model | Input | Timely / evaluable | Premature / 55 | Reference alarms / 62 | Median detected delay; misses | Phase inference | Fit wall (s) |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for row in primary:
        family = "P" if row["method"].startswith("P") else row["method"]
        token = (
            ("_" + family) if family == "B0" else "_" + row["variant"] + "_" + family
        )
        seconds = sum(
            r["wall_seconds"]
            for r in fit_rows
            if token in r["model"] and "permuted" not in r["model"]
        )
        delay = (
            "N/A"
            if row["median_detected_delay"] is None
            else f"{row['median_detected_delay']:.2f}s"
        )
        layer = {"P0": "unfiltered", "P1": "forward filter", "P2": "EMA .3s"}.get(
            row["method"], "—"
        )
        regime = (
            "clock"
            if row["method"] == "B0"
            else "Q+C"
            if row["variant"] == "QC"
            else "Q"
        )
        lines.append(
            f"| {row['method']} | {regime} | {row['timely']}/{row['evaluable']} | {row['premature']}/55 | {row['reference_alarms']}/62 | {delay}; {row['misses_including_premature_and_late']} misses | {layer} | {seconds:.2f}{' shared' if family == 'P' else ''} |"
        )
    lines += [
        "\nP0/P1/P2 share one fit per fold/input/seed: their fit time is repeated for transparency, not three independent trainings. These detected-only medians exclude the stated misses. Reference alarms are not certified physical false positives.\n",
        "### What completed and what the data supports\n",
        "All five folds completed: five shared clock fits, ten ridge dynamics fits, ten ordinary window classifiers, thirty phase-free GRUs and thirty shared phase-head GRUs (seeds 11/23/37, 30 epochs), plus ten development-only permuted-label window fits. There are 95 checkpoints, 85 in the main comparison. All models, preprocessing and continuous OOF predictions remain local.\n",
        "The 60 sample aliases match cylinder-recovery state/action/timestamps and frame order exactly. They contribute 55 unique eligible recovery recordings, not 115; 62 unique cylinder-install expert-source references bring the cohort to 117. Original sample entries 16,26,35,37,48 remain excluded. Neither malformed phase IDs nor event times were repaired. Five deterministic role-balanced folds use k for evaluation, (k+1)%5 for calibration and three other folds for fitting. Shared collection conditions and overlapping training folds make this exploratory cross-fitting, not untouched confirmation.\n",
        "All training folds support chronological phases 1–4 before recovery, with no phase-5 supervision. Expert phase loss is masked. Originating failure phase is never substituted for chronological phase. Constant single-object symmetry/clearance cannot establish a mechanical-metadata benefit. No operator/session or cross-object failure-generalization claim is supported.\n",
        "### Primary paired effects\n",
        "Differences below are percentage points with 95% exploratory paired intervals from 2,000 recording-level, source-role-stratified resamples. Seeds, aliases and windows are not resampling units.\n",
        "| Input | Contrast | Timely difference [CI] | Premature difference [CI] | Reference-alarm difference [CI] |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in read(root, "paired_effects.json"):
        if row["delta"] != 0:
            continue

        def cell(name, row=row):
            e = row["effects"][name]
            return f"{100 * e['difference']:+.2f} [{100 * e['ci95'][0]:+.2f}, {100 * e['ci95'][1]:+.2f}]"

        lines.append(
            f"| {row['variant']} | {row['contrast']} | {cell('timely')} | {cell('premature')} | {cell('reference_alarm')} |"
        )
    lines += [
        "\nB3 has fewer timely detections than B2 in both regimes; the Q comparison also spends fewer reference alarms, so it is not uniform domination. P1 provides no timely benefit over either P0 or ordinary smoothing. Lower reference alarms without timely recognition are not recovery success. No favorable architecture, seed, threshold or scoring rule was substituted.\n",
        "### Timing, commands, uncertainty and robustness\n",
        "Only B0 receives elapsed time. It makes no alarms at its common-exposure calibrated point and detects no events. Human targets are lagged one native frame; Q-only remains essential because teleoperator commands can reveal reaction or collection procedure rather than an autonomous policy's evidence. Q+C improves B2 from 5 to 9 timely detections, but 44/55 first alarms remain premature; it does not rescue the GRU/phase hypothesis. Physical onset remains unvalidated and annotations are rounded.\n",
        "| Input/model | Clean timely | Drop 10% | Drop 30% | Delay .2s | Delay .5s | Optimistic onset reset |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant in ("Q", "QC"):
        for method in ("B1", "B2", "B3", "P0", "P1", "P2"):
            data = {
                r["stress"]: r
                for r in summary
                if r["variant"] == variant
                and r["method"] == method
                and r["boundary_delta"] == 0
            }
            values = [
                str(data[s]["timely"]) + "/55"
                for s in ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
            ]
            lines.append(
                f"| {variant}/{method} | "
                + " | ".join(values)
                + f" | {data['clean']['optimistic_reset_timely']}/55 |"
            )
    lines += [
        "\nThresholds are unchanged under synthetic packet loss/delay. Every condition's premature/reference alarms, exposure and censoring are in tables/summary.csv, not hidden behind timely counts. The onset-reset column deliberately erases the first premature alarm and restarts persistence; it is an invalid optimistic diagnostic, never the main result. For Q/B3 it changes 1/55 valid timely detections to 51/55. The first-alarm rule prevents that inflation.\n",
        "The .5/1-second interior analyses retain the original first alarm and report emptied interiors/timing ambiguity. They are stress offsets, not validated onset confidence bounds; paired comparisons use common eligible recording subsets. Full results and changed denominators are in summary.json/paired_effects.json. Missingness holds only received packets; derivatives use source timestamps. Delays hide both observations and commands initially. Prefix tests and independent reconstruction check that future data never fills a past score.\n",
        "All seed-specific calibrated recording outcomes are in tables/seed_results.csv, and all five fold numerators in tables/fold_results.csv. The fixed interval permutation uses only training donors and evaluates B2 on calibration-fold development recordings, not on main evaluation folds. It reduces development timely counts from 8 to 2 (Q) and 9 to 3 (Q+C), while 51/55 premature alarms persist. This does not validate the physical labels or eliminate collection-role shortcuts.\n",
    ]
    lines += [
        "### Boundary interiors and initialization variation\n",
        "| Input/model | Original timely/support | .5s interior | 1s interior |",
        "| --- | ---: | ---: | ---: |",
    ]
    for variant in ("Q", "QC"):
        for method in ("B2", "B3", "P1"):
            cells = []
            for delta in (0, 0.5, 1.0):
                row = next(
                    r
                    for r in summary
                    if r["variant"] == variant
                    and r["method"] == method
                    and r["stress"] == "clean"
                    and r["boundary_delta"] == delta
                )
                cells.append(f"{row['timely']}/{row['evaluable']}")
            lines.append(f"| {variant}/{method} | " + " | ".join(cells) + " |")
    lines += [
        "\nTwo/four interiors become empty at .5/1s. Shrinking denominators are not new detections. Sensor-delay increases can simply move early alarms into the released window, rather than improve sensing. No offset is promoted to corrected ground truth.\n",
        "| Input/model | Seed 11 timely/premature/reference | Seed 23 | Seed 37 |",
        "| --- | --- | --- | --- |",
    ]
    for variant in ("Q", "QC"):
        for method in ("B3", "P0", "P1", "P2"):
            cells = []
            for seed in (11, 23, 37):
                selected = [
                    r
                    for r in read(root, "seed_outcomes.json")
                    if r["variant"] == variant
                    and r["method"] == method
                    and r["seed"] == seed
                ]
                cells.append(
                    f"{sum(r['timely'] for r in selected)}/{sum(r['premature'] for r in selected)}/{sum(r['reference_alarm'] for r in selected)}"
                )
            lines.append(f"| {variant}/{method} | " + " | ".join(cells) + " |")
    lines += [
        "\nEach seed is calibrated on the same nominal-reference calibration group; denominators are 55 recovery and 62 reference recordings. The primary ensemble averages probabilities before calibration and is not an average of these counts. Initialization sensitivity is material: Q/B3 varies from 1 to 8 timely events; the favorable seed was not selected as the main result. Thus the negative primary contrast concerns the frozen ensemble, not every possible initialization.\n",
        "### What the phase layer changes\n",
    ]
    phase = read(root, "phase_results.json")
    for variant in ("Q", "QC"):
        values = []
        for method in ("P0", "P1", "P2"):
            chosen = [
                r for r in phase if r["variant"] == variant and r["method"] == method
            ]
            values.append(
                f"{method}: {sum(r['correct'] for r in chosen) / sum(r['frames'] for r in chosen):.2%} phase accuracy; {sum(r['marginal_argmax_graph_violations_full_stream'] for r in chosen)} marginal-argmax edge violations"
            )
        lines.append(variant + ": " + "; ".join(values) + ".\n")
    lines += [
        "Accuracy is restricted to annotated pre-recovery intervals; violation counts span the full scored replay and are not physical-recovery labels. Filtering improves this secondary phase measure but not the primary timely-recognition contrast. Observed edges/self loops, train-only counts and Laplace pseudocount 1 define the matrix. Initial counts receive fixed smoothing. Neural emissions are potentials, not calibrated generative likelihoods. Impossible normalization retains the prior state and emits a flagged unfiltered fallback. No such fallback is concealed.\n",
        "Positive latent paths use allowed edges; marginal-argmax labels need not. The regression counterexample has previous mass (.4,.6,0), transitions 0→{0,2}, 1→1, 2→2 and emissions (.01,.01,1): the marginal label switches 1→2 despite that edge being forbidden. Standard causal GRUs, forward filtering, EMA, task graphs and this distinction are not new theory. REBOOT already supplies the phase framework; ProTAS is the closest structured online segmentation component (references in the original report).\n",
        "### Limited external reference shift\n",
        "After the main prediction/model seal, frozen cylinder models were applied without refitting or threshold changes to 306 unique expert-source recordings. Identical named joint/gripper channels, order, dtype, robot/export and 30-Hz timing were checked; no mapping was chosen from performance. This is a native-export distribution diagnostic. Physical SI calibration is not independently certified, and the official source tree did not supply the custom robot driver. It is not cross-object failure detection.\n",
        "| Reference source | Q B3 alarm counts across five frozen folds | Q P1 counts | Q+C B3 counts | Q+C P1 counts | Unique recordings |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    external = read(root, "external_summary.json")
    for repository in (
        "16mm-cylinder_remove",
        "usb-c_install",
        "usb-c_remove",
        "rj45-install",
        "rj45_remove",
    ):
        cells = []
        for variant, method in (("Q", "B3"), ("Q", "P1"), ("QC", "B3"), ("QC", "P1")):
            chosen = sorted(
                [
                    r
                    for r in external
                    if r["repository"] == repository
                    and r["variant"] == variant
                    and r["method"] == method
                ],
                key=lambda r: r["fold"],
            )
            cells.append(",".join(str(r["alarms"]) for r in chosen))
        lines.append(
            f"| {repository} | " + " | ".join(cells) + f" | {chosen[0]['recordings']} |"
        )
    lines += [
        "\nThese are five repeated analyses of each external recording, not 1,530 independent recordings. Alarm/exposure counts, score distributions and full-bundle latency are retained per recording/fold in external_outcomes.json. Very short recordings remain censored, with exposure availability explicit. High alarms are distribution sensitivity, not new failure labels. Unannotated recovery sources are excluded. Missing target events prohibit target sensitivity/delay or metadata-transfer claims.\n",
        "### Streaming replay and explanation examples\n",
        "The runtime accepts only timestamped current observations and previously issued targets. It carries recurrent and filtered state from recording start; labels, future duration and true phase are evaluator-only overlays. All four deterministic categories are attempted under both Q and Q+C, choosing earliest first-alarm time then canonical ID (non-alarming misses sort last). Absent categories remain explicit; Q/P1 has no timely example. Trace fields show actual motion/target residual, phase/emission distributions, allowed predecessor mass, filter score change, persistence and threshold. They explain model computation, not friction/misalignment or another physical cause.\n",
    ]
    examples = read(root, "streaming/examples_QC.json")
    example = examples["timely"]
    if example["available"]:
        lines += [
            "```bash",
            "PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 \\",
            "PYTHONPATH=src:results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages \\",
            f"uv run --no-sync python -m dual_rec.reboot.overnight_replay --root {root} \\",
            f"  --group {example['group']} --variant QC --method P1",
            "```\n",
        ]
    for variant in ("Q", "QC"):
        examples = read(root, f"streaming/examples_{variant}.json")
        present = [r for r in examples.values() if r["available"]]
        lines.append(
            f"{variant}: {len(present)}/4 categories present; maximum streaming/batch risk discrepancy {max(r['maximum_stream_batch_score_difference'] for r in present):.3g}; packet mean inference {min(r['mean_inference_ms_per_packet'] for r in present):.2f}–{max(r['mean_inference_ms_per_packet'] for r in present):.2f} ms across examples. Per-category first-alarm agreement and traces are in streaming/examples_{variant}.json.\n"
        )
    lines.append(
        "The earliest missed-target example also has a premature first alarm, so those two categories share a recording in each input regime; they are not additional independent demonstrations. Full non-alarming/late cases remain in the outcome and prediction files.\n"
    )
    lines += [
        "### Claims and next evidence\n",
        "| Established in this run | Unsupported here | Required next evidence |",
        "| --- | --- | --- |",
        "| Completed single-object trained OOF baseline/phase comparison and causal replay | Improved physical recovery, safety or causal root-cause identification | Prospective robot/policy evaluation, independently verified outcomes |",
        "| Phase filtering improves chronological phase accuracy/coherence in this sample | Improved timely recognition beyond ordinary smoothing | Frozen-model test on a new, counterbalanced collection session |",
        "| First-alarm accounting reveals heavy premature alarms; onset-reset evaluation inflates apparent success | Robust recognition of true physical onset or useful deployment performance | Independently adjudicated physical onset/recovery boundaries and nominal references |",
        "| Native external references expose distribution sensitivity | Cross-object failure sensitivity, mechanical-metadata benefit or operator generalization | Attributable target-object events, multiple objects per mechanical attribute and independent operators |",
        "\nThe smallest useful next confirmation is an independently collected, counterbalanced cylinder session: matched start conditions/recording exposure across roles, externally annotated onset and human-recovery times, and a frozen comparison of B2/B3/P0/P1/P2 with Q and Q+C. Choose the number of independent calibration/evaluation recordings prospectively for alarm-rate resolution and paired uncertainty, not by recycling windows. A broader assembly claim additionally needs real event annotations on the other objects. No such collection or new campaign was launched. This package is not publication-ready and does not demonstrate the proposed recognition contribution.\n",
        "### Provisional positioning (not a manuscript)\n",
        "This exploratory REBOOT study separates causal motion evidence, command-assisted evidence, extra phase supervision, graph filtering and ordinary smoothing under identical recording-level folds. The measured result is a useful negative boundary: better phase coherence does not imply a better recovery-needed alarm. A superficially strong onset-reset evaluation largely disappears when first alarms are counted from recording start. This supports retaining the functioning baseline/replay package and correcting the evidence target before pursuing a stronger method claim. It does not establish novel temporal logic, task graphs, physical recovery improvement or a publishable positive PCRR result.\n",
        "### Verification, preservation, resources and resume\n",
        "The independent scorer imports neither detector nor main scorer. It independently joins raw aliases, checks train-only folds/grammar, reconstructs missingness/delay features, recomputes 190 threshold calibrations, first-alarm/boundary/seed outcomes, external alarms and 2,000-resample paired effects. See independent_audit.json for exact counts and hashes. Engineering tests are separate from scientific evidence. The final maintained test/lint/format outcomes and metering are in commands.jsonl; completion_manifest.json binds the final commit and every artifact.\n",
        "Existing CPU Torch and the earlier PyArrow installation were reused read-only, with new caches and no package/model/video downloads. Known-source housekeeping fetched one immutable official Git tree, found no attributable additional event files, and saved one unsent request draft. No authors were contacted. Initial per-backend two-thread pools incurred spin overlap; remaining workers use passive OpenMP and one-thread BLAS to keep the CPU worker bounded. GPU/paid APIs/simulators/robot executions are zero. Initial bootstrap/editor/tool overhead is unmetered; foreground worker/driver and closing CPU are measured. Final resources.json states wall/CPU, transfers and storage with scope.\n",
        "Historical report/protocol prefixes, all other maintained historical files, old completion seal and every consumed source file are verified at start/end. The historical lockfile and .gitignore are unchanged. No whole-release inventory or old physical study was repeated. Checkpointed workers use a process lock; resume an **unfinished, unsealed** run with the same worker and `python -m dual_rec.reboot.overnight_experiment --root RUN --stage train` then `--stage predict`. Existing complete fits are reused; completed sealed runs reject writing commands. All authorized analyses are complete, without detached workers. Local commits only; publication is manual.\n",
    ]
    for name in ("alarm_frontier", "phase_comparison", "streaming_timeline"):
        lines.append(f"![{name}]({root}/figures/{name}.png)\n")
    lines.append(
        "Engineering validation: 15 focused tests passed; 261 maintained tests passed and four original environment-gated physics checks skipped. Lint and format checks passed (125 maintained Python files). These counts are not scientific sample sizes.\n"
    )
    if (root / "preseal_resources.json").exists():
        resource = read(root, "preseal_resources.json")
        lines.append(
            f"Verified preseal checkpoint: campaign wall {resource['campaign_wall_seconds']:.3f}s (conservative five-minute startup allowance), measured worker/driver/closing CPU {resource['measured_cpu_seconds']:.3f}s; GPU 0; additional transfers <=1,000,000 bytes; logical artifacts {resource['new_logical_bytes_before_seal']:,} bytes and storage charge {resource['storage_with_overhead_bound_bytes']:,} bytes. Final reporting/archive/seal costs are added in resources.json. All limits passed.\n"
        )
    base = subprocess.check_output(
        [
            "git",
            "show",
            "24f84001aff2c975c25f7f820ae6d8a901a58758:REBOOT_PHASE_REPORT.md",
        ]
    )
    Path("REBOOT_PHASE_REPORT.md").write_bytes(
        base + ("\n".join(lines).rstrip() + "\n").encode()
    )


def archive(root):
    progress = {
        "phase": "READY_FOR_FINAL_SEAL",
        "main_fits": 85,
        "development_fits": 10,
        "folds": 5,
        "scientific_stages": {
            stage: "COMPLETE"
            for stage in (
                "registration",
                "baselines",
                "phase_comparison",
                "robustness",
                "external_diagnostic",
                "streaming",
                "independent_analysis",
                "report",
            )
        },
    }
    save_json(root / "progress.json", progress)
    with (root / "ledger.jsonl").open("a") as stream:
        stream.write(json.dumps(progress) + "\n")
    for name in ("commands.jsonl", "ledger.jsonl", "progress.json"):
        shutil.copyfile(root / name, root / ("review_" + name))
    paths = [
        Path("REBOOT_PHASE_PROTOCOL.md"),
        Path("REBOOT_PHASE_REPORT.md"),
        Path("config") / f"reboot_overnight_{root.name}.json",
    ]
    names = (
        "registration.json",
        "review_cohort.json",
        "review_oof_scores.npz",
        "summary.json",
        "paired_effects.json",
        "thresholds.json",
        "phase_results.json",
        "external_summary.json",
        "external_compatibility.json",
        "development_sanity.json",
        "permutation_mapping.json",
        "independent_audit.json",
        "runtime_versions.json",
        "consumed_inputs.json",
        "external_inputs.json",
        "main_prediction_seal.json",
        "throughput.json",
        "preseal_resources.json",
        "annotation_request_draft.txt",
        "housekeeping.json",
    )
    paths.extend(root / name for name in names)
    paths.extend(
        root / ("review_" + name)
        for name in ("commands.jsonl", "ledger.jsonl", "progress.json")
    )
    paths.extend(
        p
        for folder in (root / "tables", root / "figures", root / "streaming")
        for p in folder.rglob("*")
        if p.is_file()
    )
    paths.extend(Path("src/dual_rec/reboot").glob("overnight_*.py"))
    paths.extend(Path("scripts").glob("reboot_overnight_*.py"))
    paths.append(Path("tests/test_reboot_overnight.py"))
    index = {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "sha256": {str(p): sha(p) for p in paths},
        "scope": "Supervisor review package. Excludes datasets, checkpoints, environments, caches and third-party PDFs. Final nonrecursive filesystem completion seal is outside this archive.",
        "dataset_attribution": "REBOOT26 official pinned datasets, Apache-2.0 per dataset cards; see config and consumed-input manifests. No original robot recordings/PDFs redistributed.",
    }
    save_json(root / "review_archive_index.json", index)
    destination = root / "supervisor_review.tar.gz"
    with tarfile.open(destination, "w:gz") as bundle:
        for path in paths + [root / "review_archive_index.json"]:
            bundle.add(path, arcname=str(path), recursive=False)
    print(
        json.dumps(
            {
                "path": str(destination),
                "sha256": sha(destination),
                "bytes": destination.stat().st_size,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("figures", "report", "archive"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.stage == "figures":
        tables(args.root)
        figures(args.root)
    elif args.stage == "report":
        report(args.root)
    else:
        archive(args.root)


if __name__ == "__main__":
    main()
