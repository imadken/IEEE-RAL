"""Checkpointed five-fold execution of the fixed recording-level pilot."""

from __future__ import annotations

import argparse
import json
import time
from functools import partial
from pathlib import Path

import numpy as np
import torch

from dual_rec.reboot.overnight_data import (
    OLD,
    arrays_for,
    fold_spec,
    make_registry,
    save_json,
    sensor_features,
    sha,
    targets,
)
from dual_rec.reboot.overnight_models import (
    clock_features,
    fit_anomaly,
    fit_logistic,
    fit_neural,
    phase_layers,
    phase_matrix,
    predict_anomaly,
    predict_logistic,
    predict_neural,
    windows,
)

SEEDS = (11, 23, 37)
STRESSES = ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")


def ledger(root, **row):
    with (root / "ledger.jsonl").open("a") as stream:
        stream.write(json.dumps(row | {"epoch": time.time()}) + "\n")
    save_json(root / "progress.json", row)


def prepare(root):
    rows = make_registry(root)
    eligible = [r for r in rows if r["eligible"]]
    arrays = arrays_for(eligible)
    folds = []
    for k in range(5):
        train, calibration, evaluation, horizon = fold_spec(eligible, arrays, k)
        phases = [
            targets(r, sensor_features(arrays[r["group"]], r["group"]), horizon)[2]
            for r in train
        ]
        grammar = phase_matrix(phases)
        folds.append(
            {
                "fold": k,
                "horizon": horizon,
                "train": [r["group"] for r in train],
                "calibration": [r["group"] for r in calibration],
                "evaluation": [r["group"] for r in evaluation],
                "phase_support": grammar["support"].tolist(),
                "phase_eligible": int(np.sum(grammar["support"] > 0)) >= 4,
            }
        )
    rng = np.random.default_rng(999)
    x = [rng.normal(size=(300, 42)) for _ in range(70)]
    y = [np.r_[np.zeros(150), np.ones(150)] for _ in x]
    mask = [np.ones(300, dtype=bool) for _ in x]
    p = [np.repeat(np.arange(5), 60) for _ in x]
    smoke = fit_neural(x, y, mask, p, seed=999, epochs=3, phase=True)
    estimate = smoke["training_wall_seconds"] * 10 * 60 * 2
    save_json(
        root / "throughput.json",
        {
            "scope": "Synthetic tensors only, no comparative evaluation",
            "epochs": 3,
            "wall_seconds": smoke["training_wall_seconds"],
            "projected_neural_matrix_seconds_with_factor_two": estimate,
        },
    )
    if estimate > 18000:
        raise ValueError(
            "Freeze a documented smaller epoch count before any comparison"
        )
    registration = {
        "run": str(root),
        "reviewed_base": "24f84001aff2c975c25f7f820ae6d8a901a58758",
        "source_inputs": str(OLD),
        "registry_sha256": sha(root / "registry.json"),
        "folds": folds,
        "seeds": list(SEEDS),
        "epochs": 30,
        "hidden": 32,
        "scoring_hz": 10,
        "score_native_stride": 3,
        "horizon_rule": "min(30, training-role 5th percentiles of final timestamp); stream t < H",
        "inputs": [
            "Q: 14 current positions, 14 differences between received 10-Hz positions / actual dt",
            "QC: Q plus 14 previous-native-frame issued targets minus current state",
        ],
        "feature_boundary": "first derivative/discrepancy zero; no annotation resets; train-only equal-recording standardization, std floor 1e-6, clip +/-10",
        "models": {
            "B0": "1-second elapsed bins, L2 logistic lambda .01",
            "B1": "ridge alpha 1; 10 preceding qpos packets, plus prior-issued target for QC; mean absolute MAD-scaled residual, 1.4826 and floor 1e-6; no scores before ten lags",
            "B2": "1-second last/mean/std/OLS slope, logistic lambda .01, LBFGS 200 iterations",
            "B3": "GRU32 one layer, Adam .001, 30 epochs, complete recording batch, clip gradient norm 1",
            "P": "same GRU32, five phase and five failure heads; predicted-phase risk mixture plus .2 phase CE; phase masked where absent",
        },
        "loss": "equal recording masked BCE; train-only negative/positive frame ratio capped at 10; same neural budget and weights policy",
        "phase": "pre-recovery chronological labels only; observed adjacent edges and all self loops, pseudocount 1 only on allowed edges; initial observed counts plus 1 per state",
        "inference": {
            "P0": "unfiltered phase mixture",
            "P1": "causal forward phase filtering",
            "P2": "phase-probability EMA time constant .3s",
        },
        "ensemble": "mean of three final seed risk probabilities per inference layer before calibration",
        "alarm": "first >= threshold streak spanning .1 seconds, timestamp tolerance 2e-6; from recording start",
        "calibration": "lowest float64 threshold above disallowed reference persistent capacity; <=floor(.1*N) alarms, conservative ties",
        "primary_contrasts": [["B3", "B2"], ["P1", "P0"], ["P1", "P2"]],
        "bootstrap": {
            "resamples": 2000,
            "seed": 20261111,
            "unit": "canonical recording",
            "strata": "source role",
        },
        "stress": list(STRESSES),
        "boundary_seconds": [0, 0.5, 1],
        "permutation": "training recoveries SHA256 order rotated once, donor native-frame event endpoints; B2 development/calibration evaluation only",
        "external": [
            "16mm-cylinder_remove",
            "usb-c_install",
            "usb-c_remove",
            "rj45-install",
            "rj45_remove",
        ],
        "limits": json.loads((root / "initial.json").read_text())["limits"],
        "threads": 2,
        "device": "cpu",
        "scope": "exploratory single-object released-annotation agreement; not physical recovery or confirmed false positives",
    }
    save_json(root / "registration.json", registration)
    config = Path("config") / f"reboot_overnight_{root.name}.json"
    config.write_bytes((root / "registration.json").read_bytes())
    ledger(
        root,
        phase="REGISTERED",
        eligible=len(eligible),
        recovery=sum(r["role"] == "recovery" for r in eligible),
        reference=sum(r["role"] == "reference" for r in eligible),
        phase_folds=sum(f["phase_eligible"] for f in folds),
    )
    print(
        json.dumps(
            {
                "eligible": len(eligible),
                "excluded": [r["sample_episode"] for r in rows if not r["eligible"]],
                "folds": [
                    {
                        k: f[k]
                        for k in ("fold", "horizon", "phase_support", "phase_eligible")
                    }
                    for f in folds
                ],
                "projected_neural_wall_seconds": estimate,
            }
        )
    )


def checkpoint(root, name, producer):
    path = root / "models" / (name + ".pt")
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        value = torch.load(path, map_location="cpu", weights_only=False)
        if value["registration_sha256"] != sha(root / "registration.json"):
            raise ValueError("Existing checkpoint registration mismatch")
        return value
    started = time.monotonic()
    value = producer()
    value["registration_sha256"] = sha(root / "registration.json")
    temporary = path.with_suffix(".partial")
    torch.save(value, temporary)
    temporary.replace(path)
    ledger(
        root,
        phase="FIT_COMPLETE",
        model=name,
        checkpoint_sha256=sha(path),
        wall_seconds=time.monotonic() - started,
    )
    return value


def fit_fold(root, k):
    rows = [
        r for r in json.loads((root / "registry.json").read_text()) if r["eligible"]
    ]
    arrays = arrays_for(rows)
    train, calibration, evaluation, horizon = fold_spec(rows, arrays, k)
    for variant in ("Q", "QC"):
        series = {
            r["group"]: sensor_features(arrays[r["group"]], r["group"], variant=variant)
            for r in rows
        }
        train_series = [series[r["group"]] for r in train]
        xs = [s["features"][s["time"] < horizon] for s in train_series]
        labels = [
            targets(r, s, horizon) for r, s in zip(train, train_series, strict=True)
        ]
        ys, masks, phases = [
            [v[i][: len(x)] for v, x in zip(labels, xs, strict=True)] for i in range(3)
        ]
        grammar = phase_matrix(phases)
        if variant == "Q":
            checkpoint(
                root,
                f"fold{k}_B0",
                partial(
                    fit_logistic,
                    [
                        clock_features(s["time"][: len(x)])
                        for s, x in zip(train_series, xs, strict=True)
                    ],
                    ys,
                    masks,
                ),
            )
        checkpoint(
            root,
            f"fold{k}_{variant}_B1",
            partial(
                fit_anomaly,
                [x for r, x in zip(train, xs, strict=True) if r["role"] == "reference"],
            ),
        )
        summaries = [
            windows(x, s["time"][: len(x)])
            for x, s in zip(xs, train_series, strict=True)
        ]
        checkpoint(
            root, f"fold{k}_{variant}_B2", partial(fit_logistic, summaries, ys, masks)
        )
        recoveries = sorted(
            [r for r in train if r["role"] == "recovery"], key=lambda r: r["group"]
        )
        donor = {
            r["group"]: recoveries[(i + 1) % len(recoveries)]
            for i, r in enumerate(recoveries)
        }
        permuted = []
        for r, s, x in zip(train, train_series, xs, strict=True):
            changed = r.copy()
            if r["role"] == "recovery":
                other = donor[r["group"]]
                changed["onset"] = float(
                    arrays[r["group"]]["timestamp"][other["onset_frame"]]
                )
                changed["recovery"] = float(
                    arrays[r["group"]]["timestamp"][other["recovery_frame"]]
                )
            permuted.append(targets(changed, s, horizon))
        permutation = checkpoint(
            root,
            f"fold{k}_{variant}_B2_permuted",
            partial(
                fit_logistic,
                summaries,
                [v[0][: len(x)] for v, x in zip(permuted, xs, strict=True)],
                [v[1][: len(x)] for v, x in zip(permuted, xs, strict=True)],
            ),
        )
        for phase in (False, True):
            if phase and np.sum(grammar["support"] > 0) < 4:
                continue
            family = "P" if phase else "B3"
            for seed in SEEDS:
                checkpoint(
                    root,
                    f"fold{k}_{variant}_{family}_seed{seed}",
                    partial(
                        fit_neural,
                        xs,
                        ys,
                        masks,
                        phases,
                        seed=seed,
                        epochs=30,
                        phase=phase,
                    ),
                )
        save_json(
            root / f"fold{k}_{variant}_grammar.json",
            {key: value.tolist() for key, value in grammar.items()},
        )
        # Development-only permutation predictions: these are never called OOF.
        destination = root / "development"
        destination.mkdir(exist_ok=True)
        for r in calibration:
            s = series[r["group"]]
            keep = s["time"] < horizon
            np.savez_compressed(
                destination / f"fold{k}_{variant}_{r['group'].split(':')[1]}.npz",
                time=s["time"][keep],
                scores=predict_logistic(permutation, windows(s["features"], s["time"]))[
                    keep
                ],
            )
    ledger(
        root,
        phase="FOLD_TRAINED",
        fold=k,
        training=len(train),
        calibration=len(calibration),
        evaluation=len(evaluation),
    )


def models_for(root, k, variant):
    def load(name):
        return torch.load(
            root / "models" / (name + ".pt"), map_location="cpu", weights_only=False
        )

    prefix = f"fold{k}_{variant}_"
    result = {
        "B0": load(f"fold{k}_B0"),
        "B1": load(prefix + "B1"),
        "B2": load(prefix + "B2"),
        "B3": [load(prefix + f"B3_seed{s}") for s in SEEDS],
    }
    if (root / "models" / (prefix + f"P_seed{SEEDS[0]}.pt")).exists():
        result["P"] = [load(prefix + f"P_seed{s}") for s in SEEDS]
        result["grammar"] = {
            key: np.asarray(value)
            for key, value in json.loads(
                (root / f"fold{k}_{variant}_grammar.json").read_text()
            ).items()
        }
    return result


def predict_bundle(bundle, series):
    x, t = series["features"], series["time"]
    result = {
        "B0": predict_logistic(bundle["B0"], clock_features(t)),
        "B1": predict_anomaly(bundle["B1"], x),
        "B2": predict_logistic(bundle["B2"], windows(x, t)),
    }
    result["B3_seeds"] = np.asarray([predict_neural(fit, x)[0] for fit in bundle["B3"]])
    result["B3"] = result["B3_seeds"].mean(axis=0)
    if "P" in bundle:
        seed_scores, seed_phases, fallbacks = [], [], []
        for fit in bundle["P"]:
            _, emission, heads = predict_neural(fit, x)
            valid = np.isfinite(emission).all(axis=1)
            scores = np.full((3, len(x)), np.nan)
            states = np.full((3, len(x), 5), np.nan)
            fallback = np.zeros(len(x), dtype=bool)
            if valid.any():
                scores[:, valid], states[:, valid], fallback[valid] = phase_layers(
                    emission[valid], heads[valid], t[valid], bundle["grammar"]
                )
            seed_scores.append(scores)
            seed_phases.append(states)
            fallbacks.append(fallback)
        scores, phases = np.asarray(seed_scores), np.asarray(seed_phases)
        for i in range(3):
            result[f"P{i}_seeds"] = scores[:, i]
            result[f"P{i}"] = scores[:, i].mean(axis=0)
            result[f"phase_P{i}"] = phases[:, i].mean(axis=0)
        result["phase_unresolved"] = np.asarray(fallbacks).sum(axis=0)
    return result


def predict_fold(root, k, *, stresses=STRESSES):
    rows = [
        r for r in json.loads((root / "registry.json").read_text()) if r["eligible"]
    ]
    arrays = arrays_for(rows)
    _, calibration, evaluation, horizon = fold_spec(rows, arrays, k)
    for variant in ("Q", "QC"):
        bundle = models_for(root, k, variant)
        for stress in stresses:
            for split, population in (
                ("calibration", calibration),
                ("evaluation", evaluation),
            ):
                if split == "calibration" and stress != "clean":
                    continue
                directory = root / "predictions" / f"fold{k}" / variant / stress / split
                directory.mkdir(parents=True, exist_ok=True)
                for r in population:
                    path = directory / (r["group"].split(":")[1] + ".npz")
                    if path.exists():
                        continue
                    series = sensor_features(
                        arrays[r["group"]], r["group"], variant=variant, stress=stress
                    )
                    keep = series["time"] < horizon
                    series = {key: value[keep] for key, value in series.items()}
                    started = time.monotonic()
                    result = predict_bundle(bundle, series)
                    latency = time.monotonic() - started
                    np.savez_compressed(
                        path,
                        **series,
                        **result,
                        inference_seconds=np.array(latency),
                        horizon=np.array(horizon),
                    )
            ledger(
                root,
                phase="PREDICTIONS_COMPLETE",
                fold=k,
                variant=variant,
                stress=stress,
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("prepare", "train", "predict"), required=True
    )
    parser.add_argument("--fold", type=int, choices=range(5))
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    if args.stage == "prepare":
        prepare(args.root)
    elif args.stage == "train":
        for fold in range(5) if args.fold is None else [args.fold]:
            fit_fold(args.root, fold)
    else:
        for fold in range(5) if args.fold is None else [args.fold]:
            predict_fold(args.root, fold)


if __name__ == "__main__":
    main()
