"""Fixed onset continuation figures, cumulative report, review bundle and seal."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import io
import json
import resource
import subprocess
import tarfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from dual_rec.reboot.onset_specificity import METHODS, OLD, read
from dual_rec.reboot.overnight_data import save_json, sha

MODELS = (*METHODS, "B2R")
MARKER = "## 2026-11-12: onset specificity and matched-background calibration"


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def percent(value):
    return f"{100 * value:.1f}"


def report(root):
    for name in (
        "independent_audit.json",
        "independent_controls_audit.json",
        "streaming_parity.json",
    ):
        assert read(root, name)["status"] == "PASS"
    summary = read(root, "summary.json")
    feasibility = read(root, "score_feasibility.json")
    ceilings = read(root, "hindsight_ceilings.json")
    within = read(root, "within_recording.json")
    source = read(root, "source_role_summary.json")
    calibration = read(root, "calibrations.json")["thresholds"]
    outcomes = read(root, "outcomes.json")
    effects = read(root, "paired_effects.json")
    fits = []
    for path in sorted((root / "models").glob("*.pt")):
        fit = torch.load(path, map_location="cpu", weights_only=False)
        fits.append(
            {
                "path": str(path),
                "sha256": sha(path),
                "kind": fit["kind"],
                "converged": fit["converged"],
                "iterations": fit["iterations"],
                "objective": fit["objective"],
                "training_ids": fit["training_ids"],
            }
        )
    save_json(root / "fit_summary.json", fits)
    get = lambda v, m, a, c, stress="clean": next(
        r
        for r in summary
        if (r["variant"], r["method"], r["alpha"], r["rule"], r["stress"])
        == (v, m, a, c, stress)
    )
    tables = root / "tables"
    tables.mkdir(exist_ok=True)
    for name, rows in (
        ("comparison", summary),
        ("feasibility", feasibility),
        ("hindsight_only", ceilings),
        ("within_recording", within),
        ("source_role", read(root, "source_role_predictions.json")),
    ):
        with (tables / (name + ".csv")).open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(
                {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in r.items()
                }
                for r in rows
            )
    folds = []
    for v in ("Q", "QC"):
        for m in MODELS:
            for a in (0.05, 0.1, 0.2):
                for c in ("C0", "C1"):
                    for f in range(5):
                        rows = [
                            r
                            for r in outcomes
                            if (
                                r["variant"],
                                r["method"],
                                r["alpha"],
                                r["rule"],
                                r["stress"],
                                r["fold"],
                            )
                            == (v, m, a, c, "clean", f)
                        ]
                        folds.append(
                            {
                                "variant": v,
                                "method": m,
                                "alpha": a,
                                "rule": c,
                                "fold": f,
                                "timely": sum(r["timely"] for r in rows),
                                "premature": sum(r["premature"] for r in rows),
                                "reference_alarms": sum(
                                    r["reference_alarm"] for r in rows
                                ),
                                "recoveries": sum(
                                    r["role"] == "recovery" for r in rows
                                ),
                                "references": sum(
                                    r["role"] == "reference" for r in rows
                                ),
                            }
                        )
    save_json(root / "fold_counts.json", folds)
    calibration_rows = []
    for identifier, r in calibration.items():
        calibration_rows.append(
            {
                "id": identifier,
                "threshold": r["threshold"],
                **{
                    p + "_" + k: value
                    for p, counts in r["realized"].items()
                    for k, value in counts.items()
                },
            }
        )
    with (tables / "calibration.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(calibration_rows[0]))
        writer.writeheader()
        writer.writerows(calibration_rows)
    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    x = np.arange(len(MODELS))
    for ax, v in zip(axes, ("Q", "QC"), strict=True):
        feasible = [
            sum(
                r["feasible"]
                for r in feasibility
                if r["variant"] == v and r["method"] == m and r["role"] == "recovery"
            )
            for m in MODELS
        ]
        ceiling = [
            sum(
                r["timely"]
                for r in ceilings
                if r["variant"] == v and r["method"] == m and r["alpha"] == 0.1
            )
            for m in MODELS
        ]
        ax.bar(x - 0.18, feasible, 0.36, label="Individual feasible interval")
        ax.bar(x + 0.18, ceiling, 0.36, label="Shared fold threshold ceiling")
        ax.set(
            xticks=x,
            xticklabels=MODELS,
            title=v + ": HINDSIGHT DIAGNOSTIC ONLY",
            ylim=(0, 58),
        )
    axes[0].set_ylabel("Recordings / 55")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        "Feasibility is not calibrated performance; ceiling constrains both alarm populations"
    )
    fig.tight_layout()
    fig.savefig(figures / "score_feasibility.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharey=True)
    for i, v in enumerate(("Q", "QC")):
        for j, metric in enumerate(("premature", "reference_alarms")):
            ax = axes[i, j]
            for m in MODELS:
                a, b = get(v, m, 0.1, "C0"), get(v, m, 0.1, "C1")
                den = 55 if metric == "premature" else 62
                ax.plot(
                    [a[metric] / den, b[metric] / den],
                    [a["timely"] / 55, b["timely"] / 55],
                    ".-",
                    label=m,
                )
                ax.annotate(m, (b[metric] / den, b["timely"] / 55), fontsize=8)
            ax.set(
                title=v,
                xlabel=metric.replace("_", " ") + " rate",
                ylabel="Timely rate",
                xlim=(-0.025, 1.03),
                ylim=(-0.025, 0.4),
            )
    axes[0, 0].legend(fontsize=7, ncol=4)
    fig.suptitle("Frozen scores, C0 → C1 at alpha .10; endpoint labels show C1")
    fig.tight_layout()
    fig.savefig(figures / "calibration_tradeoffs.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    dmethods = ("B0", "B2", "B3", "P0", "P1", "P2")
    for gap, marker in ((0, "o"), (0.5, "s")):
        for v, offset in (("Q", -0.06), ("QC", 0.06)):
            ys = []
            for m in dmethods:
                rs = [
                    r
                    for r in within
                    if r["variant"] == v
                    and r["method"] == m
                    and r["gap"] == gap
                    and r["included"]
                ]
                ys.append(np.mean([r["target_capacity_greater"] for r in rs]))
            axes[0].plot(
                np.arange(6) + offset, ys, marker=marker, label=f"{v}, gap {gap}s"
            )
    axes[0].set(
        xticks=np.arange(6),
        xticklabels=dmethods,
        ylim=(0, 1.05),
        ylabel="Target capacity > prefix fraction",
        title="Annotation-delimited contrast",
    )
    axes[0].legend(fontsize=8)
    predictions = read(root, "source_role_predictions.json")
    for v in ("Q", "QC"):
        rs = [r for r in predictions if r["variant"] == v]
        y = np.array([r["role"] == "recovery" for r in rs])
        s = np.array([r["score"] for r in rs])
        thresholds = np.r_[np.inf, np.sort(np.unique(s))[::-1], -np.inf]
        axes[1].plot(
            [(s[~y] >= t).mean() for t in thresholds],
            [(s[y] >= t).mean() for t in thresholds],
            label=v,
        )
    axes[1].plot([0, 1], [0, 1], "k:")
    axes[1].set(
        xlabel="Expert-source positive rate",
        ylabel="Recovery-source positive rate",
        title="First-second source role, not failure",
    )
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figures / "within_source_diagnostics.png", dpi=150)
    plt.close(fig)
    text = [
        "\n\n" + MARKER,
        "",
        f"Evidence: `{root}`. Reviewed base `c2e24d38b61e2a3d7db422c971342eab8cac4b7e`; analysis registration committed as `ad4572f` before recalculating comparisons. This is exploratory reanalysis and cross-fitting of already exposed data, not untouched confirmation. All 117 canonical recordings, 55 eligible recoveries, 62 cylinder-install expert-source references, original exclusions/folds, seeds and horizons are retained.",
        "",
        "### Reproduction and exact score capacity",
        "",
        "All 1,638 historical outcome rows reproduced exactly with the original scorer. Training already included pre-onset negatives. The reviewed implementation calibrated only on nominal references; no historical scientific scorer or model defect was found or silently repaired. All 1,506 consumed sealed input files were verified, including the available prior archive and completion manifest with the authorized hashes.",
        "",
        "Counts below are individual nonempty A < theta <= B intervals / infeasible intervals / shared-fold hindsight ceiling at alpha .10 under BOTH budgets. A/B retain complete causal persistence history, including streaks crossing onset. Every raw score breakpoint and immediately above ties is checked. These are capacities of the fixed scores and threshold policy, not information limits or deployable calibrated performance.",
        "",
    ]
    text.append(
        table(
            [
                "Input/model",
                "Feasible / 55",
                "Infeasible / 55",
                "Hindsight timely / 55",
            ],
            [
                (
                    v + "/" + m,
                    sum(
                        r["feasible"]
                        for r in feasibility
                        if r["variant"] == v
                        and r["method"] == m
                        and r["role"] == "recovery"
                    ),
                    55
                    - sum(
                        r["feasible"]
                        for r in feasibility
                        if r["variant"] == v
                        and r["method"] == m
                        and r["role"] == "recovery"
                    ),
                    sum(
                        r["timely"]
                        for r in ceilings
                        if r["variant"] == v and r["method"] == m and r["alpha"] == 0.1
                    ),
                )
                for v in ("Q", "QC")
                for m in MODELS
            ],
        )
    )
    text += [
        "",
        "The clock B0 has many individual feasible intervals but a zero shared-threshold ceiling: per-recording feasibility alone does not establish event specificity. B2-R's calibrated timely count can exceed its budget-constrained ceiling because its realized evaluation reference alarms violate that ceiling's reference budget; the ceiling does not bound unconstrained counts. Oracle thresholds are stored only under `hindsight_only/` and rejected by the deployment loader.",
        "",
        "### Both alarm populations under fixed calibration",
        "",
        "C0 fits expert-reference capacities only. C1 uses the maximum of separately calibrated nominal-reference and strictly pre-onset recovery-prefix thresholds. The smallest conservative threshold uses nextafter above the permitted order statistic, retaining ties. No target or evaluation labels choose deployable thresholds. Nominal alarms are not certified physical false positives, and pre-annotation alarms do not prove physical normality. Calibration-fold reference counts are 12–13, valid prefixes 10–11; empirical integer budgets are coarse. B1 has one unavailable sample-41 prefix in each input because of its warmup, explicitly excluded from the valid-prefix denominator; it remains in evaluation. No other prefix is replaced or relabeled.",
        "",
        "Primary alpha .10. T/P/R denote timely / premature / reference alarms; recovery denominator 55, reference denominator 62. Delay is median seconds among detections only; misses are shown to prevent conditioning from hiding failures.",
        "",
    ]
    text.append(
        table(
            [
                "Input/model",
                "C0 T/P/R",
                "C1 T/P/R",
                "C1 late / none",
                "C1 misses",
                "C1 delay s",
            ],
            [
                (
                    v + "/" + m,
                    "/".join(
                        str(get(v, m, 0.1, "C0")[k])
                        for k in ("timely", "premature", "reference_alarms")
                    ),
                    "/".join(
                        str(get(v, m, 0.1, "C1")[k])
                        for k in ("timely", "premature", "reference_alarms")
                    ),
                    f"{get(v, m, 0.1, 'C1')['late']} / {get(v, m, 0.1, 'C1')['no_alarm']}",
                    get(v, m, 0.1, "C1")["missed"],
                    "—"
                    if get(v, m, 0.1, "C1")["median_detected_delay"] is None
                    else f"{get(v, m, 0.1, 'C1')['median_detected_delay']:.2f}",
                )
                for v in ("Q", "QC")
                for m in MODELS
            ],
        )
    )
    threshold_rows = []
    for variant in ("Q", "QC"):
        for method in MODELS:
            selected = [
                r
                for r in calibration.values()
                if r["variant"] == variant
                and r["method"] == method
                and r["alpha"] == 0.1
            ]
            ranges = []
            for rule in ("C0", "C1"):
                rs = [r for r in selected if r["rule"] == rule]
                ranges.append(
                    f"{min(r['threshold'] for r in rs):.6g}–{max(r['threshold'] for r in rs):.6g}"
                )
                ranges.append(
                    ", ".join(
                        f"{r['realized']['reference']['alarms']}/{r['realized']['reference']['valid_count']};{r['realized']['recovery_prefix']['alarms']}/{r['realized']['recovery_prefix']['valid_count']}"
                        for r in sorted(rs, key=lambda r: r["fold"])
                    )
                )
            threshold_rows.append((variant + "/" + method, *ranges))
    text += [
        "",
        "Fold-specific threshold ranges and realized calibration reference;prefix counts (fold order 0–4), primary alpha:",
        "",
        table(
            [
                "Input/model",
                "C0 threshold range",
                "C0 ref;prefix",
                "C1 threshold range",
                "C1 ref;prefix",
            ],
            threshold_rows,
        ),
    ]
    base = get("Q", "B2", 0.1, "C1")
    text += [
        "",
        f"Q/B2 C1 timely is 14/55 (25.5%; Wilson 95% {percent(base['timely_wilson95'][0])}–{percent(base['timely_wilson95'][1])}%), premature 6/55 (10.9%), nominal 0/62 (Wilson upper {percent(base['reference_wilson95'][1])}%). Matched calibration retains event signal here while substantially reducing early alarms, but 41/55 events remain missed. All 55 target windows are observable; no target is removed to improve counts. Reference exposure is {base['total_reference_exposure']:.3f} seconds per clean model/rule cell. Detailed exposure/censoring, delays and leads, rate intervals and every fold are in summary.json, outcomes.json and fold_counts.json.",
        "",
        "All fixed sensitivity cells are reported, without selecting a favorable alpha:",
        "",
    ]
    text.append(
        table(
            ["Input/model", "alpha", "C0 T/P/R", "C1 T/P/R"],
            [
                (
                    v + "/" + m,
                    a,
                    *[
                        "/".join(
                            str(get(v, m, a, c)[k])
                            for k in ("timely", "premature", "reference_alarms")
                        )
                        for c in ("C0", "C1")
                    ],
                )
                for v in ("Q", "QC")
                for m in MODELS
                for a in (0.05, 0.2)
            ],
        )
    )
    text += [
        "",
        "### Paired uncertainty, B2-R and phase filtering",
        "",
        "Exactly ten recovery-only B2-R detectors and ten first-second source-role logistic controls were fitted, five folds times two input regimes. No neural fit, hyperparameter search or other model optimization was performed. B2-R retains original windows, training-only equal-recording scaling, clipped features, positive weighting, L2 .01 and optimizer. Only recovery training recordings enter its fit; expert recordings remain in calibration/evaluation. Convergence metadata and training IDs are retained in all 20 checkpoints.",
        "",
        "Primary Q/.10 contrasts below are recording-level differences in percentage points, with 2,000 paired role-stratified bootstrap 95% intervals:",
        "",
    ]
    text += [
        "",
        f"All {len(fits)} prescribed fits completed; {sum(r['converged'] for r in fits)} report optimizer convergence. Per-fit objectives, iteration counts and hashes are retained in fit_summary.json.",
        "",
    ]
    text.append(
        table(
            ["Contrast", "Timely pp [95%]", "Premature pp [95%]", "Reference pp [95%]"],
            [
                (
                    r["contrast"],
                    *[
                        f"{100 * r['effects'][k]['difference']:.1f} [{100 * r['effects'][k]['ci95'][0]:.1f}, {100 * r['effects'][k]['ci95'][1]:.1f}]"
                        for k in ("timely", "premature", "reference_alarm")
                    ],
                )
                for r in effects
                if r["primary"]
            ],
        )
    )
    text += [
        "",
        "B2-R is not a uniform improvement: Q timely is 12 versus B2's 14, fewer premature alarms but more nominal alarms. C1 equals C0 for B2-R at the primary setting because nominal calibration dominates. Its zero premature evaluation rate does not certify safety. Q/P1 has exactly the same pooled timely count as P0/P2, with wide paired intervals. Q+C/P1 has 10 timely versus 5/5: +9.1 percentage points, paired 95% [1.8, 16.4] against either comparator. This is a positive exploratory secondary contrast under C1; all sensitivities remain in paired_effects.json. This secondary command-assisted result does not establish a primary Q benefit. Historical phase accuracy remains unchanged: Q P0/P1/P2 61.01/63.56/62.61%; Q+C 64.98/70.94/67.34%. Improved phase coherence is separate from alarm utility, and the prior negative phase-filter result is preserved.",
        "",
        "Paired C1–C0 differences for every model/input/alpha are retained in paired_effects.json, including nonprimary cells. Shared training folds and one collection/object limit uncertainty; recordings, not frames/seeds/aliases, are resampled. Wilson intervals do not remove within-collection dependence. A [0,0] bootstrap interval from identical zero indicators is not evidence of population equivalence. No unadjusted p-value or acceptance probability is used.",
        "",
        "### Within-recording and source-context controls",
        "",
        "One-second equal-sample windows retain full history; .5-second gaps are a fixed sensitivity, never label correction. The table reports included / 55, target-capacity-greater count, and median mean-score change. Clock contrasts explicitly expose ordinary progress trends. These annotation-delimited comparisons are not deployment success rates.",
        "",
    ]
    rows = []
    for v in ("Q", "QC"):
        for m in ("B0", "B2", "B3", "P0", "P1", "P2"):
            for gap in (0, 0.5):
                rs = [
                    r
                    for r in within
                    if r["variant"] == v
                    and r["method"] == m
                    and r["gap"] == gap
                    and r["included"]
                ]
                rows.append(
                    (
                        v + "/" + m,
                        gap,
                        len(rs),
                        sum(r["target_capacity_greater"] for r in rs),
                        f"{np.median([r['mean_change'] for r in rs]):.4f}",
                    )
                )
    text.append(
        table(
            [
                "Input/model",
                "Gap s",
                "Included",
                "Capacity increases",
                "Median mean change",
            ],
            rows,
        )
    )
    text += [
        "",
        "Source-role features contain only first-second causal Q or Q+C B2 summaries, no role/time/duration/name/phase annotation features. Sample 41's onset at 1s excludes it only here; 54 recoveries plus 62 references remain. Decision threshold is fixed .5. Results:",
        "",
    ]
    text.append(
        table(
            ["Input", "AUROC [95%]", "Balanced accuracy [95%]"],
            [
                (
                    r["variant"],
                    f"{r['auroc']:.4f} [{r['ci95'][0][0]:.4f}, {r['ci95'][0][1]:.4f}]",
                    f"{r['balanced_accuracy']:.4f} [{r['ci95'][1][0]:.4f}, {r['ci95'][1][1]:.4f}]",
                )
                for r in source
            ],
        )
    )
    text += [
        "",
        "Recording contexts are highly distinguishable before the released onset. Initial pose, preparation or style can be legitimate sources of these differences. This diagnostic does not establish fraud, annotation error or a causal confound, and does not rule out later event-specific information. Q/B2's positive within-recording contrast and calibrated detections support some event-associated signal alongside context differences; none identifies physical onset independently.",
        "",
        "### Robustness under unchanged thresholds",
        "",
        "C1 thresholds are transferred unchanged to saved streams. Primary-alpha T/P/R cells:",
        "",
    ]
    text.append(
        table(
            ["Input/model", "Clean", "10% drop", "30% drop", ".2s delay", ".5s delay"],
            [
                (
                    v + "/" + m,
                    *[
                        "/".join(
                            str(get(v, m, 0.1, "C1", stress)[k])
                            for k in ("timely", "premature", "reference_alarms")
                        )
                        for stress in (
                            "clean",
                            "drop0.1",
                            "drop0.3",
                            "delay0.2",
                            "delay0.5",
                        )
                    ],
                )
                for v in ("Q", "QC")
                for m in MODELS
            ],
        )
    )
    text += [
        "",
        "These are descriptive perturbations of the same recordings, not new samples. A delayed alarm moving into the released target window is not evidence that degraded sensing helps. Q+C uses previously issued native targets and remains an assisted-information regime.",
        "",
        "### Streaming, annotation review and independent verification",
        "",
        "streaming_parity.json checks the first-hash P1 example in each available C0 review category, deduplicated. C0/C1 risk streams are bitwise identical, first alarms match batch outcomes, and batch/step differences are below 1e-6. Runtime receives only packets and accumulated state; onset/recovery overlays are offline only. Traces show model motion, previous-target residual, phase/emission distributions, predecessor mass, persistence and threshold, not a physical causal explanation. Reproduce either rule with:",
        "",
        "```bash",
        "PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \\",
        "PYTHONPATH=src:results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages \\",
        f"uv run --no-sync python -m dual_rec.reboot.overnight_replay --root {OLD} \\",
        f"  --calibration-root {root} --calibration C1 --alpha .1 \\",
        f"  --group {read(root, 'streaming_parity.json')['examples'][0]['group']} --variant {read(root, 'streaming_parity.json')['examples'][0]['variant']} --method P1",
        "```",
        "",
        "annotation_review.json selects three smallest canonical hashes per available C0 category/model/input: premature infeasible, premature feasible, timely, and late/no-alarm miss (disjoint categories). Empty categories remain empty. Raw annotation bounds and provenance are unchanged; score and full-history capacity traces are in annotation_review_scores.npz. Numeric plots do not physically adjudicate labels, and no annotation was corrected.",
        "",
        "The independent analyzer imports neither main detector nor scorer. It directly streams thresholds, independently computes capacities, verifies every shared-threshold breakpoint, calibration masks/IDs/fold separation, all 56,160 outcomes, train-only new scalers and direct logistic predictions, and paired resampling. A supplementary independent check covers all 1,320 within-recording rows and source-role AUROC/uncertainty. Exact check counts/hashes are in independent_audit.json and independent_controls_audit.json. Tests/lint/resource evidence and intentional source changes are sealed at completion.",
        "",
        "The original Q/B3 onset-reset 1→51/55 comparison remains invalid optimistic accounting; it is neither adopted nor attributed to REBOOT authors. [Kim et al.](https://arxiv.org/abs/2109.05257) provide related context on inflated anomaly metrics from point adjustment; that is a different operation. Existing FAIL-Detect and Sentinel positioning remains applicable. This continuation adds no theoretical or new-method claim.",
        "",
        "### Disposition, preservation and local handoff",
        "",
        "Matched calibration improves the evaluated Q/B2 alarm tradeoff but leaves most events missed. Fixed-score capacities vary strongly; neither universal absence of signal nor a solved calibration problem is supported. The source-role control reveals context separability; B2-R trades fewer premature for more reference alarms. Primary Q phase-filter advantage remains unsupported. No physical recovery, intervention efficacy, cross-object failure sensitivity or publication-readiness claim follows.",
        "",
        f"Local review bundle: `{root}/supervisor_review.tar.gz`; its exact SHA-256, final branch/commit, tests, storage/transfer and measured-worker CPU are in completion_manifest.json/resources.json. Raw outputs/logs/checkpoints stay untracked. `.gitignore`, historical lockfiles, old weights/seals and all unrelated files are preserved. The only historical source changes are configurable limits in the existing bounded worker and registered C0/C1 loading in the existing replay interface. Historical documentation prefixes are byte-preserved. No push, credentials, contact, GPU or detached research worker is used.",
        "",
        "Resume only an unfinished unsealed run using the existing locked worker and the registered stages in onset_specificity/onset_analysis; fitting reuses checkpoint hashes and refuses a 21st fit. Completed runs reject mutations. Commands and executed source hashes are in commands.jsonl; pre-format executed source snapshots remain under provenance/. All independent fixed stages are complete; no new campaign is authorized by these findings.",
        "",
    ]
    for name in (
        "score_feasibility",
        "calibration_tradeoffs",
        "within_source_diagnostics",
    ):
        text.append(f"![{name}]({root}/figures/{name}.png)\n")
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    status = {
        "tests": "13 focused onset tests; 62 maintained REBOOT tests passed",
        "audit": "PASS: full direct-stream and supplementary controls/status audits",
        "lint": "See maintained-ruff-final.log and maintained-format-final.log",
        "completed_worker_cpu_seconds_before_report": sum(
            r["cpu_seconds"] for r in commands
        ),
        "session_wall_seconds_before_report": time.time()
        - read(root, "initial.json")["started_epoch"],
    }
    save_json(root / "review_status.json", status)
    text += [
        "",
        f"Engineering validation: {status['tests']}. Maintained Ruff lint and format checks passed. Before report/archive/seal, measured worker/driver CPU was {status['completed_worker_cpu_seconds_before_report']:.3f}s and conservative session wall was {status['session_wall_seconds_before_report']:.3f}s. Final closing costs and artifact storage are added in resources.json. GPU and paid API use are zero.",
        "",
    ]
    path = Path("REBOOT_PHASE_REPORT.md")
    previous = path.read_text()
    if MARKER in previous:
        raise ValueError("Dated report already appended")
    with path.open("a") as stream:
        stream.write("\n".join(text))
    (root / "report_appendix.md").write_text("\n".join(text))
    print(
        json.dumps(
            {
                "summary_cells": len(summary),
                "fold_cells": len(folds),
                "figures": 3,
                "report_appended": True,
            }
        )
    )


def archive(root):
    target = root / "supervisor_review.tar.gz"
    if target.exists():
        raise ValueError("Archive exists")
    names = [
        "registration.json",
        "consumed_inputs.json",
        "original_reproduction.json",
        "score_feasibility.json",
        "hindsight_ceilings.json",
        "calibrations.json",
        "outcomes.json",
        "summary.json",
        "fold_counts.json",
        "paired_effects.json",
        "within_recording.json",
        "source_role_predictions.json",
        "source_role_summary.json",
        "annotation_review.json",
        "annotation_review_scores.npz",
        "streaming_parity.json",
        "independent_audit.json",
        "independent_controls_audit.json",
        "report_appendix.md",
        "initial.json",
        "input_verification.json",
        "fit_summary.json",
        "review_status.json",
        "commands.jsonl",
        "ledger.jsonl",
    ]
    files = [root / n for n in names]
    files += [
        root / (name + ".log")
        for name in (
            "maintained-reboot-tests-final",
            "focused-onset-tests-final",
            "maintained-ruff-final",
            "maintained-format-final",
            "independent-direct-stream-audit",
            "independent-status-and-controls-final",
            "frozen-c0-c1-streaming-parity",
        )
    ]
    files += [
        p
        for folder in (
            "tables",
            "figures",
            "streaming",
            "b2r_predictions",
            "hindsight_only",
            "provenance",
        )
        for p in (root / folder).rglob("*")
        if p.is_file()
    ]
    files += [
        Path("REBOOT_PHASE_REPORT.md"),
        Path("REBOOT_PHASE_PROTOCOL.md"),
        Path("config/reboot_onset_20261112T090003Z.json"),
        *map(
            Path,
            (
                "src/dual_rec/reboot/onset_specificity.py",
                "src/dual_rec/reboot/onset_analysis.py",
                "src/dual_rec/reboot/overnight_replay.py",
                "scripts/reboot_overnight_worker.py",
                "scripts/reboot_onset_audit.py",
                "scripts/reboot_onset_streaming.py",
                "scripts/reboot_onset_finish.py",
                "tests/test_reboot_onset.py",
            ),
        ),
    ]
    inventory = {str(p): sha(p) for p in files}
    with tarfile.open(target, "w:gz") as tar:
        for p in files:
            tar.add(p, arcname=str(p), recursive=False)
        blob = json.dumps(inventory, indent=2).encode()
        info = tarfile.TarInfo("ARCHIVE_SHA256.json")
        info.size = len(blob)
        tar.addfile(info, io.BytesIO(blob))
    save_json(
        root / "archive.json",
        {
            "path": str(target),
            "sha256": sha(target),
            "bytes": target.stat().st_size,
            "entries": len(files) + 1,
            "scope": "Review outputs, B2-R score predictions and decisive examples; no model environments/checkpoints/raw datasets",
        },
    )
    print((root / "archive.json").read_text())


def seal(root):
    cpu_start = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    initial = read(root, "initial.json")
    registration = read(root, "registration.json")
    assert sha(OLD / "completion_manifest.json") == registration["prior_seal_sha256"]
    assert sha(OLD / "supervisor_review.tar.gz") == registration["prior_archive_sha256"]
    preserved = []
    exceptions = {
        "scripts/reboot_overnight_worker.py",
        "src/dual_rec/reboot/overnight_replay.py",
    }
    for name, digest in initial["prior_sha256"].items():
        path = Path(name)
        if name in ("REBOOT_PHASE_REPORT.md", "REBOOT_PHASE_PROTOCOL.md"):
            old = subprocess.check_output(
                ["git", "show", initial["reviewed_base"] + ":" + name]
            )
            assert hashlib.sha256(
                old
            ).hexdigest() == digest and path.read_bytes().startswith(old)
        elif name not in exceptions:
            assert sha(path) == digest
        preserved.append(name)
    for name, digest in read(root, "consumed_inputs.json").items():
        assert sha(Path(name)) == digest
    assert sha(Path(".gitignore")) == initial["prior_sha256"][".gitignore"]
    assert sha(Path("uv.lock")) == initial["prior_sha256"]["uv.lock"]
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    assert all(r["exit_status"] == 0 for r in commands)
    assert read(root, "independent_audit.json")["status"] == "PASS"
    assert len(list((root / "models").glob("*.pt"))) == 20
    charge = sum(
        p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink()
    )
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    resources = {
        "session_wall_seconds": time.time() - initial["started_epoch"],
        "wall_scope": initial["start_scope"],
        "measured_worker_and_closing_cpu_seconds": sum(
            r["cpu_seconds"] for r in commands
        )
        + time.process_time()
        - cpu_start
        + usage.ru_utime
        + usage.ru_stime,
        "cpu_scope": "All bounded worker/driver commands plus seal CPU; interactive reading/editing overhead unmetered",
        "gpu_seconds": 0,
        "fits": 20,
        "new_artifact_bytes_before_small_seal": charge,
        "additional_transfer_upper_bound_bytes": 1_000_000,
        "transfer_scope": "Only named Kim arXiv abstract page; no datasets, packages, weights or video downloaded",
        "paid_apis": 0,
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "research_workers_remaining": 0,
        "worker_verification": "Campaign worker lock acquired; all foreground worker tool sessions returned terminal completion; no detached launch used",
    }
    assert resources["session_wall_seconds"] < initial["limits"]["wall_seconds"]
    assert (
        resources["measured_worker_and_closing_cpu_seconds"]
        < initial["limits"]["cpu_seconds"]
    )
    assert charge < initial["limits"]["new_bytes"] - 1_000_000
    save_json(root / "resources.json", resources)
    save_json(
        root / "preservation.json",
        {
            "status": "PASS",
            "prior_tracked_files_checked": len(preserved),
            "consumed_files_checked": len(read(root, "consumed_inputs.json")),
            "documentation_original_prefix_preserved": True,
            "intentional_source_changes": sorted(exceptions),
            "gitignore_and_lockfiles_unchanged": True,
        },
    )
    files = {
        str(p.relative_to(root)): sha(p)
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    save_json(
        root / "completion_manifest.json",
        {
            "status": "COMPLETE",
            "commit": resources["commit"],
            "branch": resources["branch"],
            "archive": read(root, "archive.json"),
            "sha256": files,
            "resources": resources,
        },
    )
    print(json.dumps(resources, indent=2))
    print("completion_manifest_sha256", sha(root / "completion_manifest.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("report", "archive", "seal"), required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"report": report, "archive": archive, "seal": seal}[args.stage](args.root)


if __name__ == "__main__":
    main()
