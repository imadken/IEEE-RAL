"""Render the fixed FailTime evidence and compact local supervisor review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

METHODS = (
    "B0_time",
    "B0_prior",
    "B1",
    "B2",
    "B3",
    "B4",
    "MCSFA",
    "MCSFA_no_mode",
    "MCSFA_no_accum",
)
STRESSES = ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")


def read(root: Path, name: str) -> Any:
    return json.loads((root / name).read_text())


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def table(headers, rows) -> str:
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    return "\n".join(
        [
            "| " + " | ".join(map(cell, headers)) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *["| " + " | ".join(map(cell, row)) + " |" for row in rows],
        ]
    )


def number(value, digits=3) -> str:
    return "not estimable" if value is None else f"{value:.{digits}f}"


def primary(row) -> bool:
    return (
        row["stress"] == "clean"
        and row["alpha"] == 0.1
        and row["persistence"] == 0.1
        and row.get("split", "evaluation") == "evaluation"
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {
                key: json.dumps(value) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            }
            for row in rows
        )


def command_evidence(root: Path) -> list[dict]:
    rows = [
        json.loads(line) for line in (root / "commands.jsonl").read_text().splitlines()
    ]
    result = []
    for row in rows:
        command = " ".join(map(str, row["command"]))
        if not any(token in command for token in ("pytest", "ruff", "audit", "parity")):
            continue
        log = root / (row["name"] + ".log")
        text = log.read_text() if log.exists() else ""
        tests = re.findall(r"\d+ passed(?:, \d+ skipped)?(?: in [^\n]+)?", text)
        last = (
            tests[-1]
            if tests
            else next(
                (line for line in reversed(text.splitlines()) if line.strip()),
                "no log text",
            )
        )
        result.append(
            {
                "name": row["name"],
                "exit_status": row["exit_status"],
                "result": last[-400:],
                "log": str(log.relative_to(root)),
                "cpu_seconds": row["cpu_seconds"],
            }
        )
    return result


def report_examples(root: Path, rows: list[dict], cohort: dict) -> list[dict]:
    results = []
    preferred = (
        "MCSFA",
        "B2",
        "B3",
        "B4",
        "B1",
        "MCSFA_no_accum",
        "MCSFA_no_mode",
        "B0_time",
        "B0_prior",
    )
    for category in ("timely", "premature", "late", "missed", "clean_alarm"):
        choices = sorted(
            [r for r in rows if primary(r) and r["status"] == category],
            key=lambda r: (
                preferred.index(r["method"]),
                hashlib.sha256(r["sample"].encode()).hexdigest(),
            ),
        )
        if not choices:
            results.append(
                {
                    "category": category,
                    "available": False,
                    "reason": "No evaluated method has this primary outcome",
                }
            )
            continue
        row = choices[0]
        results.append(
            {
                "category": category,
                "available": True,
                "sample": row["sample"],
                "method": row["method"],
                "split": "evaluation",
                "risk_path": f"risks/evaluation/clean/{row['sample']}.npz",
                "threshold": row["threshold"],
                "alarm_time": row["alarm_time"],
                "raw_annotation": cohort[row["sample"]],
            }
        )
    uncertain = sorted(
        [
            r
            for r in cohort.values()
            if r["verdict"] == "fail" and not r.get("onset_within_observed", True)
        ],
        key=lambda r: hashlib.sha256(r["sample"].encode()).hexdigest(),
    )
    if uncertain:
        row = uncertain[0]
        registration = read(root, "registration.json")
        split = next(
            name for name, ids in registration["splits"].items() if row["sample"] in ids
        )
        threshold = next(
            r["threshold"]
            for r in read(root, "thresholds.json")
            if r["method"] == "MCSFA" and r["alpha"] == 0.1
        )
        alarm = None
        if threshold is not None:
            with np.load(
                root / f"risks/{split}/clean/{row['sample']}.npz", allow_pickle=False
            ) as stream:
                beginning = None
                for now, value in zip(stream["time"], stream["MCSFA"], strict=True):
                    if not np.isfinite(value) or value < threshold:
                        beginning = None
                    else:
                        beginning = now if beginning is None else beginning
                        if now - beginning >= 0.1 - 1e-7:
                            alarm = float(now)
                            break
        results.append(
            {
                "category": "annotation_observability_uncertain",
                "available": True,
                "sample": row["sample"],
                "method": "MCSFA",
                "split": split,
                "risk_path": f"risks/{split}/clean/{row['sample']}.npz",
                "threshold": threshold,
                "alarm_time": alarm,
                "alarm_scope": "No retrospective correction or fabricated physical adjudication",
                "raw_annotation": row,
            }
        )
    else:
        results.append(
            {
                "category": "annotation_observability_uncertain",
                "available": False,
                "reason": "No annotated onset outside observed history",
            }
        )
    save(
        root / "report_examples.json",
        {
            "selection": "First SHA256(sample) per primary outcome, preferring MCSFA then fixed comparator order; first uncertain annotation by hash",
            "examples": results,
        },
    )
    return results


def figures(
    root: Path,
    summary: list[dict],
    strata: list[dict],
    cohort: dict,
    examples: list[dict],
) -> None:
    destination = root / "figures"
    destination.mkdir(exist_ok=True)
    main = {r["method"]: r for r in summary if primary(r)}
    x = np.arange(len(METHODS))
    fig, axis = plt.subplots(figsize=(12, 5))
    for shift, key, label in (
        (-0.25, "timely", "Timely / failures"),
        (0, "premature", "Premature / failures"),
        (0.25, "clean_alarm", "Clean alarms / successes"),
    ):
        values = [main[m]["rates"][key] for m in METHODS]
        axis.bar(
            x + shift, [np.nan if v is None else v for v in values], 0.25, label=label
        )
    axis.set(
        xticks=x,
        xticklabels=METHODS,
        ylabel="Recording rate",
        ylim=(0, 1.08),
        title="First alarms from recording start; alpha .10, persistence .1s",
    )
    axis.tick_params(axis="x", labelrotation=22)
    axis.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(destination / "first_alarm_tradeoffs.png", dpi=150)
    plt.close(fig)
    tasks = sorted({r["task_id"] for r in cohort.values()})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    task_x = np.arange(len(tasks))
    for shift, verdict, label in (
        (-0.18, "fail", "Failures"),
        (0.18, "success", "Success references"),
    ):
        axes[0].bar(
            task_x + shift,
            [
                sum(
                    r["task_id"] == task and r["verdict"] == verdict
                    for r in cohort.values()
                )
                for task in tasks
            ],
            0.36,
            label=label,
        )
    axes[0].set(
        xticks=task_x,
        xticklabels=tasks,
        ylabel="All qualified recordings",
        title="Full-cohort composition",
    )
    axes[0].tick_params(axis="x", labelrotation=90, labelsize=7)
    axes[0].legend(fontsize=8)
    held = [r for r in strata if r["stratum_type"] == "task_id" and primary(r)]
    eval_tasks = sorted({r["stratum"] for r in held})
    for method in ("B2", "B3", "B4", "MCSFA"):
        ys = [
            next(
                (
                    r["rates"]["timely"]
                    for r in held
                    if r["method"] == method and r["stratum"] == task
                ),
                None,
            )
            for task in eval_tasks
        ]
        axes[1].plot(
            np.arange(len(eval_tasks)),
            [np.nan if v is None else v for v in ys],
            "o-",
            label=method,
        )
    axes[1].set(
        xticks=np.arange(len(eval_tasks)),
        xticklabels=eval_tasks,
        ylabel="Timely / task failures",
        ylim=(-0.04, 1.04),
        title="Fixed held-out tasks; no SO-101 evaluation",
    )
    axes[1].tick_params(axis="x", labelrotation=25, labelsize=8)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(destination / "task_strata.png", dpi=150)
    plt.close(fig)
    shown = [r for r in examples if r["available"]]
    fig, axes = plt.subplots(
        max(1, len(shown)), 1, figsize=(11, max(3, 2.2 * len(shown))), squeeze=False
    )
    for axis, example in zip(axes[:, 0], shown, strict=True):
        with np.load(root / example["risk_path"], allow_pickle=False) as saved:
            t, risk = saved["time"], saved[example["method"]]
        axis.plot(t, risk, label=example["method"], linewidth=1)
        if example["threshold"] is not None:
            axis.axhline(
                example["threshold"],
                color="black",
                linestyle=":",
                label="Frozen threshold",
            )
        annotation = example["raw_annotation"]
        if annotation["verdict"] == "fail":
            axis.axvspan(
                annotation["onset"],
                annotation["onset"] + 1,
                color="green",
                alpha=0.12,
                label="Offline released target window",
            )
        if example["alarm_time"] is not None:
            axis.axvline(example["alarm_time"], color="red", label="First alarm")
        axis.set(
            title=f"{example['category']}: {example['sample']} ({example['split']})",
            ylabel="Risk",
        )
        axis.legend(fontsize=6, loc="upper left", ncol=4)
    axes[-1, 0].set_xlabel(
        "Decision time (seconds); annotation overlays are offline only"
    )
    fig.tight_layout()
    fig.savefig(destination / "example_timelines.png", dpi=150)
    plt.close(fig)


def report(root: Path) -> None:
    required = (
        "independent_data_audit.json",
        "independent_numerical_audit.json",
        "streaming_parity.json",
    )
    audits = {name: read(root, name) for name in required}
    if any(value.get("status") != "PASS" for value in audits.values()):
        raise ValueError(
            "Final reporting requires passing independent audits and streaming parity"
        )
    summary = read(root, "summary.json")
    strata = read(root, "stratified.json")
    effects = read(root, "paired_effects.json")
    seeds = read(root, "seed_sensitivity.json")
    short_access = read(root, "short_access.json")
    role = read(root, "source_role_summary.json")
    gates = read(root, "gates.json")
    worktree_observation = read(root, "concurrent_worktree_observation.json")
    registration = read(root, "registration.json")
    rows = read(root, "cohort_qualification.json")
    cohort = {r["sample"]: r for r in rows}
    outcomes = read(root, "outcomes.json")
    thresholds = read(root, "thresholds.json")
    main = {r["method"]: r for r in summary if primary(r)}
    if set(main) != set(METHODS):
        raise ValueError("The report requires every fixed primary comparator")
    examples = report_examples(root, outcomes, cohort)
    tables = root / "tables"
    tables.mkdir(exist_ok=True)
    write_csv(tables / "all_comparisons.csv", summary)
    write_csv(tables / "all_strata.csv", strata)
    grouped = defaultdict(Counter)
    for split, names in registration["splits"].items():
        for name in names:
            r = cohort[name]
            grouped[(split, r["robot"], r["task_id"])][r["verdict"]] += 1
    composition = [
        {
            "split": split,
            "robot": robot,
            "task_id": task,
            "failures": counts["fail"],
            "successes": counts["success"],
        }
        for (split, robot, task), counts in sorted(grouped.items())
    ]
    save(root / "report_composition.json", composition)
    write_csv(tables / "cohort_composition.csv", composition)
    index = read(root, "models_index.json")
    fits = []
    for name, row in index.items():
        checkpoint = torch.load(
            root / row["path"], map_location="cpu", weights_only=False
        )
        fit = checkpoint["fit"]
        fits.append(
            {
                "name": name,
                "sha256": row["sha256"],
                "training_recordings": len(row["training_ids"]),
                "kind": fit["kind"],
                "seed": fit.get("seed"),
                "epochs": fit.get("epochs"),
                "converged": fit.get("converged"),
                "iterations": fit.get("iterations"),
                "objective": fit.get("objective"),
            }
        )
    save(root / "report_fits.json", fits)
    nominal = torch.load(
        root / index["nominal"]["path"], map_location="cpu", weights_only=False
    )["fit"]
    coverage = []
    for robot, value in nominal["robots"].items():
        coverage.append(
            {
                "robot": robot,
                "success_recordings": value["global"]["recordings"],
                "nominal_frames": value["global"]["frames"],
                "supported_modes": len(value["modes"]),
                "possible_modes": 36,
            }
        )
    for r in read(root, "risk_registry.json"):
        if r["split"] != "evaluation" or r["stress"] != "clean":
            continue
        with np.load(root / r["path"], allow_pickle=False) as saved:
            valid = np.isfinite(saved["MCSFA"])
            coverage.append(
                {
                    "sample": r["sample"],
                    "robot": cohort[r["sample"]]["robot"],
                    "finite_scored_frames": int(valid.sum()),
                    "global_backoff_frames": int(saved["mode_backoff"][valid].sum()),
                    "total_decision_frames": len(valid),
                }
            )
    save(root / "report_nominal_coverage.json", coverage)
    figures(root, summary, strata, cohort, examples)
    verification = command_evidence(root)
    save(root / "report_verification.json", verification)
    initial = read(root, "initial.json")
    commands = [
        json.loads(line) for line in (root / "commands.jsonl").read_text().splitlines()
    ]
    preseal = {
        "session_wall_seconds": time.time() - initial["started_epoch"],
        "measured_completed_worker_cpu_seconds": sum(
            r["cpu_seconds"] for r in commands
        ),
        "scope": "Pre-report/archive/seal; final resources.json adds closing costs. Interactive editing and browser-tool overhead are not part of measured worker CPU.",
    }
    save(root / "report_preseal_resources.json", preseal)
    failures = sum(r["verdict"] == "fail" for r in rows)
    successes = len(rows) - failures
    observable_onsets = sum(
        r["verdict"] == "fail" and r.get("onset_within_observed", True) for r in rows
    )
    summary_main = [main[m] for m in METHODS]
    no_timely_cells = sum(r["timely"] == 0 for r in summary)
    removed_paths = worktree_observation["observed_changes_to_initial_user_paths"]
    preservation_note = (
        "`.gitignore`, uv.lock and sealed historical scientific evidence are preserved. "
        "One initial untracked duplicate, root `supervisor_review.tar.gz`, disappeared during this session without a campaign write to that path. "
        "Its recorded initial SHA-256 matches the intact authoritative onset archive under `results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz`. "
        "The root duplicate is not recreated because that would reverse concurrent user/external state. "
        "The exact exception is recorded in concurrent_worktree_observation.json and the final preservation manifest; a blanket unchanged-user-state claim is not made."
        if removed_paths
        else "Initial user state, `.gitignore`, uv.lock and sealed historical scientific evidence were checked by the final preservation audit."
    )
    text = [
        "# FailTime causal online-trigger study",
        "",
        "2026-11-12. Exploratory internally held-out pilot on the fixed principal-researcher plan. This report records the completed scientific calculations and passing audits; final branch/commit, archive hash and closing resource accounting are bound by the completion manifest. It does not itself certify that finalization has finished.",
        "",
        "## Result and scientific gates",
        "",
        "```json",
        json.dumps(gates, indent=2),
        "```",
        "",
        "Gates are screening criteria, not acceptance or novelty decisions. The fixed comparisons, negative controls and perturbations were completed independently of gate direction. The principal researcher decides subsequent claims.",
        "",
        f"The evaluated causal scores yield zero timely detections in {no_timely_cells}/{len(summary)} fixed main comparison cells. These are repeated operating points on the same eight held-out recordings, not {len(summary)} independent studies. No cell is selected as a favorable result. The primary method disposition is `{gates['G2']}`; this is a result for these fixed scores, calibration and split, not an information-theoretic limit on proprioception.",
        "",
        "## Qualified cohort, split and annotation boundary",
        "",
        f"Evidence root: `{root}`. Source Git revision `{registration['github_revision']}`; HF revision `{registration['hf_revision']}`. All {len(rows)} declared Long signals are retained: {failures} failures and {successes} success references across {len({r['task_id'] for r in rows})} task groups. {observable_onsets} failures have released onsets within observed history and support DATA_GO. Whole original HDF5 objects were hashed against pinned HF identities; only numerical signals/indexing and camera schemas were inspected, with no video decoding.",
        "",
        "The unchanged `handover_episode_10` onset is 45.233333s while its last observed timestamp is 45.20000076293945s. Its history and denominator are retained, its target window is unobservable, and no label is repaired. This is an observability discrepancy, not physical adjudication.",
        "",
        "FailTime-Long supplies only an official test annotation file. The internal SHA256(robot/task) modulo-five rule was frozen before model/performance comparisons; all episodes of a robot/task stay together. Qualification metadata and three fixed fixture signals had already been inspected. Consequently held-out fitting/calibration separation is meaningful, but these data are not untouched confirmation or an official Long leaderboard training split.",
        "",
    ]
    text.append(
        table(
            ["Split", "Robot", "Task", "Failures", "Successes"],
            [
                (r["split"], r["robot"], r["task_id"], r["failures"], r["successes"])
                for r in composition
            ],
        )
    )
    text += [
        "",
        "The fixed split has 74 training, 18 calibration and eight evaluation recordings. Evaluation contains five failures and three successes from two ALOHA tasks; no SO-101 episode is held out for evaluation. Do not reroll the split or claim platform transfer. A one-record change can move timely sensitivity by 20 points or clean-alarm rate by 33.3 points.",
        "",
        "Task/recording grouping and numerical signal deduplication were checked, but released task/episode identifiers do not certify independent collection sessions or operators. Session/operator identities and their dependence are not independently established. Task grouping is therefore not proof of collection-level independence.",
        "",
        "Official Short annotations were preserved separately. Its calibration file has 50 episodes, all overlapping its 1,084-episode train file; future Short training would have to remove those IDs. The original raw source is public, rather than absent or globally DATA_BLOCKED. Three fixed annotation IDs were matched by metadata; no Short HDF5 was downloaded. Their complete task folders exceed this run's full transfer cap, so a complete official Short comparison was not qualified. No partial favorable comparison, alternative conversion, official Short confirmation or REBOOT-label transfer was performed.",
        "",
        f"Original Short raw repository `{short_access['repository']}`, revision `{short_access['revision']}`; bounded path/size evidence in short_access.json:",
        "",
        table(
            [
                "Official split",
                "Matched sample",
                "Object bytes",
                "Complete task bytes",
                "Raw downloaded",
            ],
            [
                (
                    r["split"],
                    r["sample"],
                    r["entry"]["size"],
                    r["matching_task_bytes"],
                    r["raw_downloaded"],
                )
                for r in short_access["results"]
            ],
        ),
        "",
        "## Runtime inputs, frozen methods and actual fits",
        "",
        "All monitors receive the same 10Hz causal sample-and-hold EEF16 stream plus backward differences on the decision grid, and a robot stratum known before execution. These increments divided by .1s are not certified native physical velocities. No onset, verdict, reason, future command, task-completion result, episode identity or eventual duration enters the monitor. Static task XML does not supply time-aligned phase labels. Runtime state starts only at recording start and never resets at the released onset.",
        "",
        "B0_time is elapsed time and B0_prior is training failure prevalence. B1 preserves pinned modal-Hamming Sign-CPD costs, penalty and pruning, using available-prefix processing, a training-success motion floor and arrival-time cut-count decisions. It is an explicit causal adaptation of a retrospective component. B2 is the global nominal CUSUM; B3 is the fixed one-second logistic comparator; B4 is the GRU32 probability ensemble. MCSFA uses the same derivative evidence/CUSUM with 36 mechanically defined gripper/motion modes. Insufficient mode support backs off to the robot-global nominal distribution; unknown robot coverage abstains. No-mode is exactly B2. No-accumulation uses the instantaneous evidence increment.",
        "",
    ]
    text.append(
        table(
            ["Checkpoint", "Kind", "Training records", "Seed", "Epochs", "Converged"],
            [
                (
                    r["name"],
                    r["kind"],
                    r["training_recordings"],
                    r["seed"],
                    r["epochs"],
                    r["converged"],
                )
                for r in fits
            ],
        )
    )
    text += [
        "",
        "Actual per-fit hashes and optimizer metadata are in report_fits.json and models_index.json. No architecture/hyperparameter search or favorable seed selection was performed. The GRU has one 32-unit causal recurrent layer; its three declared seeds train for 30 epochs each. The nominal fit and early-prefix classifier are separate lightweight fits, not additional neural architectures.",
        "",
        "Nominal training coverage:",
        "",
    ]
    text.append(
        table(
            ["Robot", "Success recordings", "Frames", "Supported modes / 36"],
            [
                (
                    r["robot"],
                    r["success_recordings"],
                    r["nominal_frames"],
                    r["supported_modes"],
                )
                for r in coverage
                if "success_recordings" in r
            ],
        )
    )
    text += [
        "",
        "report_nominal_coverage.json retains per-evaluation recording fallback counts. Mode support requires 50 frames from two success recordings. Scaling, evidence drift and motion floors use development successes only. No released phase boundaries are invented.",
        "",
        "## Matched calibration and primary first alarms",
        "",
        "Each method receives one constant threshold: the maximum of separately fitted calibration-success and strictly pre-onset failure-prefix thresholds. The conservative order statistic permits floor(alpha*n_valid) empirical alarms and uses nextafter above tied scores. Invalid prefixes are explicit and excluded from that population's valid-capacity denominator, never fabricated. Alpha .10 and persistence .1s are primary. The seal binds input arrays, weights, score source, calibration streams and thresholds before evaluation performance scoring. No hindsight threshold is deployed.",
        "",
    ]
    text.append(
        table(
            [
                "Method",
                "Threshold",
                "Success valid/invalid; allowed; realized",
                "Prefix valid/invalid; allowed; realized",
            ],
            [
                (
                    r["method"],
                    number(r["threshold"], 6),
                    *[
                        f"{r['fits'][p]['valid']}/{r['fits'][p]['invalid']}; {r['fits'][p]['allowed']}; {r['fits'][p]['realized_alarms']}"
                        for p in ("success", "prefix")
                    ],
                )
                for r in thresholds
                if r["alpha"] == 0.1
            ],
        )
    )
    text += [
        "",
        "Calibration is empirical with small task-dependent populations; it is not a conformal or physical-safety guarantee. Success episodes are reference recordings, not certified physically fault-free executions. Pre-annotation periods are permitted background labels, not proof of physical normality.",
        "",
        "At the primary operating point, the seven calibration successes permit zero empirical alarms, and the eleven failure prefixes permit one. These coarse integer constraints and cross-task distribution shifts do not guarantee a 10% held-out alarm rate. Realized calibration counts and all invalid-prefix counts are shown above rather than replacing uncertainty with a safety claim.",
        "",
        "Timely means onset ≤ first persistent alarm ≤ onset+1s; premature alarms remain false stops and cannot later become timely detections. Late and no-alarm failures remain in denominators. Clean alarms are any first alarm on a success reference. All methods use the same last 10Hz decision time as exposure.",
        "",
    ]
    text.append(
        table(
            [
                "Method",
                "Timely / fail",
                "Premature / fail",
                "Late",
                "Missed",
                "Clean / success",
                "Clean alarms/hour",
                "Median timely delay s",
                "Abstentions",
            ],
            [
                (
                    r["method"],
                    f"{r['timely']}/{r['failures']}",
                    f"{r['premature']}/{r['failures']}",
                    r["late"],
                    r["missed"],
                    f"{r['clean_alarms']}/{r['successes']}",
                    number(r["false_alarms_per_hour"]),
                    number(r["median_delay"]),
                    r["abstentions"],
                )
                for r in summary_main
            ],
        )
    )
    text += [
        "",
        f"Primary clean exposure is {summary_main[0]['clean_exposure_seconds']:.6f}s per method, with {summary_main[0]['observable_failures']} fully observable failure target windows. Conditional delays are shown alongside all misses. A no-alarm policy cannot establish useful recognition merely by eliminating both alarm populations.",
        "",
        "## Paired comparison and method disposition",
        "",
        "MCSFA minus each fixed alternative; differences are percentage points with 2,000 task-cluster bootstrap intervals:",
        "",
    ]
    contrasts = effects["contrasts"]
    text.append(
        table(
            [
                "Baseline",
                "Timely pp [95%]",
                "Premature pp [95%]",
                "Clean pp [95%]",
                "Burden pp [95%]",
            ],
            [
                (
                    r["baseline"],
                    *[
                        f"{100 * r['metrics'][k]['difference']:.1f} [{100 * r['metrics'][k]['ci95'][0]:.1f}, {100 * r['metrics'][k]['ci95'][1]:.1f}]"
                        if r["metrics"][k]["ci95"] is not None
                        else "not estimable"
                        for k in ("timely", "premature", "clean_alarm", "burden")
                    ],
                )
                for r in contrasts
            ],
        )
    )
    text += [
        "",
        "paired_effects.json includes valid resample counts and the exact seed/unit. With only two evaluation tasks, uncertainty is coarse and role-absent draws are invalid rather than silently imputed. Identical indicators yielding [0,0] do not imply population equivalence. Descriptive task-cluster intervals do not remove shared source, annotation, operator or embodiment limitations. G2 uses actual alarm rates and directional intervals; no score or task condition was changed after seeing outcomes.",
        "",
        f"All three GRU seeds are reported descriptively without selection. Each seed has its own matched threshold fitted from the same two calibration populations. seed_sensitivity.json retains {len(seeds['summary'])} fixed seed/alpha/persistence/stress cells; the primary seed counts are:",
        "",
        table(
            [
                "Seed comparator",
                "Timely/fail",
                "Premature/fail",
                "Late",
                "Missed",
                "Clean/success",
            ],
            [
                (
                    r["method"],
                    f"{r['timely']}/{r['failures']}",
                    f"{r['premature']}/{r['failures']}",
                    r["late"],
                    r["missed"],
                    f"{r['clean_alarms']}/{r['successes']}",
                )
                for r in seeds["summary"]
                if primary(r)
            ],
        ),
        "",
        "Primary held-out task/platform cells:",
        "",
    ]
    text.append(
        table(
            [
                "Stratum type",
                "Stratum",
                "Method",
                "Timely/fail",
                "Premature/fail",
                "Clean/success",
            ],
            [
                (
                    r["stratum_type"],
                    r["stratum"],
                    r["method"],
                    f"{r['timely']}/{r['failures']}",
                    f"{r['premature']}/{r['failures']}",
                    f"{r['clean_alarms']}/{r['successes']}",
                )
                for r in strata
                if primary(r)
            ],
        )
    )
    text += [
        "",
        "## Development controls and robustness",
        "",
        "Development-only equal-length pre/early-target contrasts, including the clock, are retained in development_contrasts.json and the G1 assessment. These annotation-delimited windows are diagnostics, not online success rates. A rising clock or eventual-verdict classifier can explain context/progress trends without identifying an event-specific alarm.",
        "",
    ]
    development = read(root, "development_contrast_summary.json")
    text.append(
        table(
            [
                "Method",
                "Included development failures",
                "Positive mean changes",
                "Median mean change",
            ],
            [
                (
                    r["method"],
                    r["included"],
                    r["positive_changes"],
                    number(r["median_change"], 6),
                )
                for r in development
            ],
        )
    )
    text += [
        "",
        "The early-prefix source-role control actually targets the eventual failure/success verdict, not an independently annotated collection source. It uses only the first complete second and excludes failures with onset≤1s from this diagnostic only. Fixed .5 decisions and train-only scaling are used; no failure denominator is removed. Results:",
        "",
        "The training row is resubstitution on the fitted recordings, not an out-of-fold or held-out score. Its high AUROC cannot establish generalization; calibration and eight-record evaluation rows are the separate held-out diagnostics. Neither the near-chance held-out scores nor their small sample sizes establish absence of a context shortcut.",
        "",
    ]
    text.append(
        table(
            [
                "Split",
                "Records",
                "Failures",
                "Successes",
                "Excluded",
                "AUROC",
                "Balanced accuracy",
            ],
            [
                (
                    r["split"],
                    r["recordings"],
                    r["failures"],
                    r["successes"],
                    r["excluded"],
                    number(r["auroc"]),
                    number(r["balanced_accuracy"]),
                )
                for r in role
            ],
        )
    )
    text += [
        "",
        "Strong early-prefix classification does not establish fraud, annotation error, causal confounding, or absence of later event signal. Small or one-class subsets cannot support an AUROC, which remains not estimable rather than fabricated.",
        "",
        "Fixed alpha sensitivities .05/.20 and persistence 0/.2s are fully tabulated in tables/all_comparisons.csv and summary.json. Primary-persistence clean alpha sensitivity counts (timely/premature/clean):",
        "",
    ]

    def cell(method, alpha, persistence, stress):
        r = next(
            r
            for r in summary
            if r["method"] == method
            and r["alpha"] == alpha
            and r["persistence"] == persistence
            and r["stress"] == stress
            and r.get("split", "evaluation") == "evaluation"
        )
        return f"{r['timely']}/{r['premature']}/{r['clean_alarms']}"

    text.append(
        table(
            [
                "Method",
                "alpha .05",
                "alpha .10",
                "alpha .20",
                "persistence 0s",
                "persistence .2s",
            ],
            [
                (
                    m,
                    cell(m, 0.05, 0.1, "clean"),
                    cell(m, 0.1, 0.1, "clean"),
                    cell(m, 0.2, 0.1, "clean"),
                    cell(m, 0.1, 0.0, "clean"),
                    cell(m, 0.1, 0.2, "clean"),
                )
                for m in METHODS
            ],
        )
    )
    text += [
        "",
        "Frozen primary operating points under sensor stress, timely/premature/clean counts:",
        "",
    ]
    text.append(
        table(
            ["Method", *STRESSES],
            [(m, *[cell(m, 0.1, 0.1, s) for s in STRESSES]) for m in METHODS],
        )
    )
    text += [
        "",
        "Native-packet dropout uses deterministic sample-derived draws; delayed streams expose only observations already available. Holding and missing initial packets are causal. Thresholds are unchanged across perturbations and persistence sensitivities. A delay that moves a premature alarm into the label window is not improved sensing. Multiple perturbations are repeated analyses of the same recordings, not new independent samples.",
        "",
        "## Streaming, examples and independent audit",
        "",
        "streaming_parity.json records the actual deterministic replay checks. Runtime sees only current/past packets, learned weights and static robot context; annotation overlays in figures/examples are offline review aids. Model-level mode, fallback, risk, source time and threshold traces explain computation, not physical root causes.",
        "",
    ]
    parity = audits["streaming_parity.json"]
    checks = parity["checks"]
    maximum = max(r["maximum_absolute_batch_stream_score_difference"] for r in checks)
    text += [
        f"All {len(checks)} streaming comparisons passed with exact first-alarm agreement and maximum batch/stream risk discrepancy {maximum:.3g}. The replay evidence additionally retains {len(parity.get('uncertain_annotation_examples', []))} unchanged uncertain-annotation example(s).",
        "",
    ]
    text.append(
        table(
            ["Category", "Available", "Method", "Recording", "Split"],
            [
                (
                    r["category"],
                    r["available"],
                    r.get("method", "—"),
                    r.get("sample", "—"),
                    r.get("split", "—"),
                )
                for r in examples
            ],
        )
    )
    text += [
        "",
        "Unavailable categories remain explicit. The uncertain example retains its raw released bounds/provenance and is not relabeled. report_examples.json and local risk streams reproduce the figure selection. A successful offline alarm is not evidence a recovery action would have succeeded.",
        "",
        "Independent audit status:",
        "",
    ]
    text.append(
        table(
            ["Artifact", "Status", "SHA-256"],
            [
                (name, value["status"], sha(root / name))
                for name, value in audits.items()
            ],
        )
    )
    text += [
        "",
        "The data auditor independently checks pinned raw hashes, aliases, schemas, timestamps, onset observability and split identities. The numerical auditor imports neither model nor primary scorer and reconstructs first alarms, calibration masks/IDs, both alarm populations, outcomes, source-role predictions and paired inference from saved values. Exact counts, tolerances and hashes remain in those audit JSON files.",
        "",
        f"The numerical audit records {audits['independent_numerical_audit.json']['native_array_hashes_checked']} native-array hashes, {audits['independent_numerical_audit.json']['threshold_cells']} main calibration cells and {audits['independent_numerical_audit.json']['outcome_rows']} main outcome rows. Separate packet and fixed-seed audit details, including all checked risk histories and seed operating points, remain in the same audit artifact rather than being inferred from test counts.",
        "",
        "Completed verification commands (failed earlier attempts remain visible rather than being erased):",
        "",
    ]
    text.append(
        table(
            ["Command record", "Exit", "Result"],
            [(r["name"], r["exit_status"], r["result"]) for r in verification],
        )
    )
    text += [
        "",
        "## Positioning and limits",
        "",
        "[ProTracer v2](https://arxiv.org/html/2609.21369v2) is a retrospective full-rollout diagnosis framework. Its runtime comparison already includes an onset-supervised GRU on visual features; our proprioception-only GRU is a separate baseline. First-alarm deployment agreement cannot be ranked directly against its retrospective MAE. [FAIL-Detect](https://www.roboticsproceedings.org/rss21/p073.html) already establishes nominal sequential failure monitoring/calibration, and [ProTAS](https://openaccess.thecvf.com/content/CVPR2024/html/Shen_Progress-Aware_Online_Action_Segmentation_for_Egocentric_Procedural_Task_Videos_CVPR_2024_paper.html) already combines causal segmentation, progress and task graphs. Generic mode conditioning, CUSUM and threshold calibration are not new formal guarantees.",
        "",
        "The historical [REBOOT report](docs/REBOOT_PHASE_REPORT.md) remains unchanged: primary Q-only phase-filter benefit failed; matched calibration improved Q/B2 to 14/55 while leaving 41 misses; early source-role AUROC was .982. Those exposed records are development history, not fresh confirmation. The bounded upstream source review and exact source hazards are retained at provenance/upstream_review.md.",
        "",
        "This pilot cannot establish cross-platform generality, independent physical onset precision, causal attribution, actual recovery improvement or IROS/RA-L readiness. Neither a negative MCSFA comparison nor a small positive cell authorizes another architecture, grammar, dataset or threshold search. All scientific conclusions remain limited to the fixed internal split, released annotation agreement and measured operating points.",
        "",
        "## Resource and local review handoff",
        "",
        f"Before report/archive/seal: conservative wall {preseal['session_wall_seconds']:.3f}s; completed bounded-worker CPU {preseal['measured_completed_worker_cpu_seconds']:.3f}s. The final resources.json adds closing costs, actual GPU, downloads and artifact bytes, with accounting scope. No GPU or paid inference was needed for the fixed CPU pipeline. Upper limits are eight wall hours, ten measured CPU core-hours, 8GB downloads and 10GB new artifacts; no hours are consumed artificially.",
        "",
        f"Compact review archive: `{root}/supervisor_review.tar.gz`; archive.json stores its exact size and SHA-256. completion_manifest.json binds the final local branch/commit, resource accounting, preservation check and every artifact. Detailed logs, original HDF5, extracted arrays, environments and detector checkpoints stay local/untracked. The archive contains compact risk predictions and decisive examples, not the 6.1GB raw cohort. Local publication remains manual.",
        "",
        preservation_note,
        "",
        "This report does not certify that finalization workers have already stopped. The final completion seal is written only after all foreground workers have returned and the worker lock is free. No push, credentials, author contact, paid inference or physical robot intervention is authorized.",
        "",
    ]
    for name in ("first_alarm_tradeoffs", "task_strata", "example_timelines"):
        text.append(f"![{name}]({root}/figures/{name}.png)\n")
    content = "\n".join(text)
    target = Path("FAILTIME_ONLINE_REPORT.md")
    if (
        target.exists()
        and target.read_text() != content
        and not (root / "report.md").exists()
    ):
        raise ValueError("Refuse to overwrite an unrelated existing report")
    target.write_text(content)
    (root / "report.md").write_text(content)
    print(
        json.dumps(
            {
                "report": str(target),
                "summary_cells": len(summary),
                "stratified_cells": len(strata),
                "models": len(fits),
                "figures": 3,
                "status": "REPORT_WRITTEN_FINAL_SEAL_PENDING",
            }
        )
    )


def archive(root: Path) -> None:
    target = root / "supervisor_review.tar.gz"
    if target.exists():
        raise ValueError("Review archive already exists; preserve the prior archive")
    files = {p for p in root.glob("*.json") if p.name != "archive.json"}
    files.update(
        root / name
        for name in (
            "authority.txt",
            "commands.jsonl",
            "downloads.jsonl",
            "report.md",
            "source_role_model.npz",
        )
    )
    files.update(
        Path(name)
        for name in ("FAILTIME_ONLINE_PROTOCOL.md", "FAILTIME_ONLINE_REPORT.md")
    )
    files.update(Path("config").glob("failtime*.json"))
    for folder in (
        "risks",
        "figures",
        "tables",
        "provenance",
        "streaming",
        "examples",
        "short_access",
    ):
        files.update(
            p for p in (root / folder).rglob("*") if p.is_file() and not p.is_symlink()
        )
    files.update(Path("src/dual_rec/failtime").glob("*.py"))
    files.update(Path("scripts").glob("*failtime*.py"))
    files.update(Path("tests").glob("test_failtime*.py"))
    for record in command_evidence(root):
        files.add(root / record["log"])
    files = sorted(p for p in files if p.is_file())
    if any(p.suffix in (".hdf5", ".pt") or "/env/" in str(p) for p in files):
        raise ValueError(
            "Raw trajectories, model checkpoints and environments do not belong in the review archive"
        )
    inventory = {str(path): sha(path) for path in files}
    with tarfile.open(target, "w:gz") as tar:
        for path in files:
            tar.add(path, arcname=str(path), recursive=False)
        blob = json.dumps(inventory, indent=2).encode()
        entry = tarfile.TarInfo("ARCHIVE_SHA256.json")
        entry.size = len(blob)
        tar.addfile(entry, io.BytesIO(blob))
    result = {
        "path": str(target),
        "sha256": sha(target),
        "bytes": target.stat().st_size,
        "entries": len(files) + 1,
        "scope": "Protocol, report, configurations, small tables/audits, compact resampled risk predictions and traces; no raw HDF5, extracted native arrays, environments or detector checkpoints",
    }
    save(root / "archive.json", result)
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("report", "archive"), required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Completed campaign is sealed")
    {"report": report, "archive": archive}[args.stage](args.root)


if __name__ == "__main__":
    main()
