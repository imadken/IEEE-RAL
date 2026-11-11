"""Frozen D7B model selection/evaluation and independent compact B analysis."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.overnight_pick import passive_features
from dual_rec.passive import (
    clustered_metric_intervals,
    mean_interval,
    metrics,
    predict,
    select_model,
    wilson,
)
from dual_rec.replay_audit import summarize_replay


def pick_cases(root, split):
    result = {}
    outcomes = []
    for folder in sorted((root / "d7b").glob(split + "-*")):
        if not folder.is_dir():
            continue
        status = json.loads((folder / "status.json").read_text())
        if status["status"] != "completed":
            raise RuntimeError("Incomplete physical worker")
        with gzip.open(folder / "scenarios.jsonl.gz", "rt") as stream:
            for line in stream:
                row = json.loads(line)
                key = (row["seed"], row["evaluation_only_fault"]["name"])
                if key in result:
                    raise ValueError("Duplicate independent sample")
                result[key] = row
        outcomes += [
            json.loads(line)
            for line in (folder / "outcomes.jsonl").read_text().splitlines()
        ]
    return result, outcomes


def fit_pick(root, output, cfg):
    if any((root / "d7b").glob("qualification-*")):
        raise RuntimeError("Qualification already opened; no model refit")
    cases, _ = pick_cases(root, "development")
    seeds = cfg["d7b"]["development_seeds"]
    expected = {(s, c) for s in seeds for c in ["nominal", "friction", "offset"]}
    if set(cases) != expected:
        raise ValueError("Incomplete development population")
    output.mkdir(exist_ok=False)
    rows = [cases[s, c] for s in seeds for c in ["friction", "offset"]]
    y = np.tile([0, 1], len(seeds))
    groups = np.repeat(seeds, 2)
    payload = {
        "training_seeds": seeds,
        "qualification_seeds_unopened": cfg["d7b"]["qualification_seeds"],
        "models": {},
    }
    for regime in ["full", "realistic"]:
        x = np.stack([passive_features(r["history"], regime) for r in rows])
        payload["models"][regime] = {}
        for mode in ["logistic", "rbf_kernel_logistic"]:
            model, cv = select_model(x, y, groups, mode, [0.01, 0.1, 1, 10])
            payload["models"][regime][mode] = {"model": model, "cv": cv}
            print(
                f"fit {regime}/{mode} regularization={model['regularization']}",
                flush=True,
            )
    with gzip.open(output / "models.json.gz", "xt") as stream:
        json.dump(payload, stream, allow_nan=False)
    (output / "seal.json").open("x").write(
        json.dumps(
            {
                "training_seeds": seeds,
                "qualification_seeds_unopened": cfg["d7b"]["qualification_seeds"],
                "model_sha256": hashlib.sha256(
                    (output / "models.json.gz").read_bytes()
                ).hexdigest(),
                "hyperparameters": {
                    regime: {
                        mode: info["model"]["regularization"]
                        for mode, info in models.items()
                    }
                    for regime, models in payload["models"].items()
                },
            },
            indent=2,
        )
    )


def evaluate_pick(root, output, cfg):
    cases, outcomes = pick_cases(root, "qualification")
    seeds = cfg["d7b"]["qualification_seeds"]
    if set(cases) != {(s, c) for s in seeds for c in ["nominal", "friction", "offset"]}:
        raise ValueError("Incomplete qualification")
    if len(outcomes) != len(seeds) * 9:
        raise ValueError("Incomplete recovery matrix")
    with gzip.open(root / "d7b/fitted/models.json.gz", "rt") as stream:
        fitted = json.load(stream)
    if set(fitted["training_seeds"]) & set(seeds):
        raise ValueError("Split leakage")
    output.mkdir(exist_ok=False)
    matrix = {}
    lookup = {(r["seed"], r["condition"], r["recovery"]): r for r in outcomes}
    counts = {
        c: sum(cases[s, c]["failed"] for s in seeds)
        for c in ["nominal", "friction", "offset"]
    }
    for condition in counts:
        matrix[condition] = {}
        for recovery in cfg["d7b"]["recoveries"]:
            rows = [lookup[s, condition, recovery] for s in seeds]
            matrix[condition][recovery] = {}
            for name, selected in [
                ("all_setups", rows),
                ("triggered_failures", [r for r in rows if r["initial_failed"]]),
            ]:
                n = len(selected)
                success = sum(r["success"] for r in selected)
                matrix[condition][recovery][name] = {
                    "independent_seeds": n,
                    "successes": success,
                    "wilson_95": wilson(success, n),
                    "utility": mean_interval(
                        [r["utility"] for r in selected],
                        cfg["bootstrap_repetitions"],
                        cfg["analysis_seed"],
                    ),
                }
    paired = [
        s
        for s in seeds
        if cases[s, "friction"]["failed"] and cases[s, "offset"]["failed"]
    ]
    contrasts = {
        c: mean_interval(
            [
                lookup[s, c, "nominal"]["utility"] - lookup[s, c, "regrasp"]["utility"]
                for s in paired
            ],
            cfg["bootstrap_repetitions"],
            cfg["analysis_seed"],
        )
        for c in ["friction", "offset"]
    }
    diagnostic = {}
    predictions = []
    uncertain_sets = []
    rows = [cases[s, c] for s in seeds for c in ["friction", "offset"]]
    y = np.tile([0, 1], len(seeds))
    groups = np.repeat(seeds, 2)
    for regime in ["full", "realistic"]:
        x = np.stack([passive_features(r["history"], regime) for r in rows])
        diagnostic[regime] = {}
        probabilities = []
        for mode, info in fitted["models"][regime].items():
            p = predict(info["model"], x)
            probabilities.append(p)
            selected = np.array([r["seed"] in paired for r in rows])
            diagnostic[regime][mode] = {
                "all_setups": metrics(y, p),
                "all_setups_clustered_95": clustered_metric_intervals(
                    y, p, groups, cfg["bootstrap_repetitions"], cfg["analysis_seed"]
                ),
                "matched_failures": metrics(y[selected], p[selected])
                if selected.any()
                else None,
            }
            for index, row in enumerate(rows):
                predictions.append(
                    {
                        "seed": row["seed"],
                        "condition": row["evaluation_only_fault"]["name"],
                        "regime": regime,
                        "model": mode,
                        "probability_offset": float(p[index]),
                        "target": int(y[index]),
                        "matched_failed": row["seed"] in paired,
                    }
                )
        if regime == "realistic":
            uncertain_sets = [
                s
                for index, s in enumerate(seeds)
                if s in paired
                and all(
                    np.all(
                        (p[index * 2 : index * 2 + 2] >= 0.25)
                        & (p[index * 2 : index * 2 + 2] <= 0.75)
                    )
                    for p in probabilities
                )
            ]
    a, b = contrasts.values()
    opposite = (
        a is not None
        and b is not None
        and a["mean"] * b["mean"] < 0
        and min(abs(a["mean"]), abs(b["mean"])) >= 0.10
    )
    intervals = bool(
        opposite and a["ci"][0] * a["ci"][1] > 0 and b["ci"][0] * b["ci"][1] > 0
    )
    uncertainty = bool(
        len(paired) > 0
        and len(uncertain_sets) >= 2
        and len(uncertain_sets) / len(paired) >= 0.25
    )
    if min(counts["friction"], counts["offset"]) < 4:
        status, reason = (
            "NO-GO",
            "Both mechanisms did not reach four triggered qualification failures",
        )
    elif len(paired) < 4:
        status, reason = (
            "INCONCLUSIVE",
            "Fewer than four matched failed qualification seeds",
        )
    elif not opposite:
        status, reason = (
            "NO-GO",
            "Primary utility preference reversal did not meet opposite-sign and 0.10 criteria",
        )
    elif not intervals:
        status, reason = "INCONCLUSIVE", "Primary paired intervals include zero"
    elif not uncertainty:
        status, reason = (
            "NO-GO",
            "Declared realistic regime lacks required decision uncertainty",
        )
    else:
        status, reason = "PASS", "All preregistered D7B gates satisfied"
    result = {
        "status": status,
        "reason": reason,
        "route": "A_INTERVENTION_PILOT"
        if status == "PASS"
        else "B_COUNTERFACTUAL_REPLAY_AUDIT",
        "failure_counts": counts,
        "matched_failed_seeds": paired,
        "contrasts": contrasts,
        "matrix": matrix,
        "diagnostics": diagnostic,
        "uncertain_realistic_seeds": uncertain_sets,
        "training_seeds": fitted["training_seeds"],
        "qualification_seeds": seeds,
        "no_snapshot_restores": True,
        "sensor_availability_amendment": "v1.1 before fitting/qualification",
    }
    (output / "report.json").open("x").write(
        json.dumps(result, indent=2, allow_nan=False)
    )
    (output / "predictions.jsonl").open("x").write(
        "".join(json.dumps(r) + "\n" for r in predictions)
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "status",
                    "reason",
                    "route",
                    "failure_counts",
                    "matched_failed_seeds",
                    "contrasts",
                    "uncertain_realistic_seeds",
                ]
            },
            indent=2,
        )
    )


def analyze_b(root, output, cfg):
    rows = []
    for path in sorted((root / "b").glob("*/trials.jsonl")):
        state = json.loads((path.parent / "status.json").read_text())
        if state["status"] != "completed":
            raise ValueError("Failed B worker requires diagnosis, not exclusion")
        rows += [json.loads(line) for line in path.read_text().splitlines()]
    result = summarize_replay(rows, cfg["bootstrap_repetitions"], cfg["analysis_seed"])
    keys = [
        (r["task"], r["seed"], r["condition"], r["stage"], r["policy"]) for r in rows
    ]
    expected = {
        (task, seed, c, s, p)
        for task, seeds in cfg["b"]["seed_ranges"].items()
        for seed in seeds
        for c in cfg["b"]["conditions"][task]
        for s in cfg["b"]["stages"]
        for p in cfg["b"]["continuations"]
    }
    if set(keys) != expected or len(keys) != len(expected):
        raise ValueError("B denominator mismatch")
    output.mkdir(exist_ok=False)
    (output / "report.json").open("x").write(
        json.dumps(result, indent=2, allow_nan=False)
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "groups"}, indent=2
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fit-pick", "evaluate-pick", "analyze-b"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(Path("config/overnight_20261111.json").read_text())
    if args.stage == "fit-pick":
        fit_pick(args.root, args.output, cfg)
    elif args.stage == "evaluate-pick":
        evaluate_pick(args.root, args.output, cfg)
    else:
        analyze_b(args.root, args.output, cfg)


if __name__ == "__main__":
    main()
