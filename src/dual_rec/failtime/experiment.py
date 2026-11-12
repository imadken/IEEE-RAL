"""Fixed train, matched calibration and sealed first-alarm evaluation stages.

All runtime prediction functions receive observations and the known robot
stratum only. Released labels enter supervised fitting or offline scoring in
separate orchestration steps; no onset event can reset a prediction stream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from dual_rec.failtime import models
from dual_rec.reboot.overnight_models import fit_logistic, predict_logistic, windows

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
SEEDS = (11, 23, 37)
ALPHAS = (0.05, 0.10, 0.20)
PERSISTENCES = (0.0, 0.1, 0.2)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(root: Path, name: str) -> Any:
    return json.loads((root / name).read_text())


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def save_npz(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    temporary.replace(path)


def progress(root: Path, stage: str, **details: Any) -> None:
    result = {"stage": stage, "epoch": time.time(), **details}
    with (root / "experiment_progress.jsonl").open("a") as stream:
        stream.write(json.dumps(result, allow_nan=False) + "\n")
    save(root / "experiment_progress.json", result)


def registration(root: Path) -> dict[str, Any]:
    if read(root, "data_gate.json")["status"] != "DATA_GO":
        raise ValueError("No model comparisons are authorized before DATA_GO")
    value = read(root, "registration.json")
    splits = value["splits"]
    names = [
        name
        for split in ("train", "calibration", "evaluation")
        for name in splits[split]
    ]
    if len(set(names)) != len(names):
        raise ValueError("Recording IDs overlap across fitting/calibration/evaluation")
    return value


def population(root: Path, split: str) -> list[dict[str, Any]]:
    # Qualification has already inspected annotation metadata. Only IDs in this
    # declared split are returned to fitting/calibration/performance analysis.
    names = registration(root)["splits"][split]
    by_name = {r["sample"]: r for r in read(root, "cohort_qualification.json")}
    if len(by_name) != len(read(root, "cohort_qualification.json")):
        raise ValueError("Canonical recording aliases must not duplicate episodes")
    return [by_name[name] for name in names]


def decision_stream(
    native_time: np.ndarray, native_eef: np.ndarray, sample: str, stress: str = "clean"
) -> dict[str, np.ndarray]:
    """Past-only 10-Hz sample/hold under fixed native-packet perturbations.

    A measurement with timestamp <= decision_time-delay+1e-7 is available.
    The same deterministic uniform packet draws define nested 10/30% dropout.
    EEF backward differences downstream use decision-grid times: held poses
    produce zero increments, not an estimate of exact native physical velocity.
    """
    if stress not in STRESSES:
        raise ValueError("Only registered sensor perturbations are authorized")
    t = np.asarray(native_time, dtype=np.float64)
    x = np.asarray(native_eef, dtype=np.float64)
    if t.ndim != 1 or x.shape != (len(t), 16) or not len(t):
        raise ValueError("Expected a nonempty time vector and EEF16 packets")
    if not np.isfinite(t).all() or np.any(np.diff(t) <= 0) or t[0] < 0:
        raise ValueError("Native timestamps must be finite and strictly increasing")
    grid = np.arange(int(np.floor((t[-1] + 1e-7) / 0.1)) + 1, dtype=float) / 10
    keep = np.ones(len(t), dtype=bool)
    delay = 0.0
    if stress.startswith("drop"):
        seed = 20261112 + int(hashlib.sha256(sample.encode()).hexdigest()[:16], 16)
        keep = np.random.default_rng(seed).random(len(t)) >= float(stress[4:])
    elif stress.startswith("delay"):
        delay = float(stress[5:])
    kept = np.flatnonzero(keep)
    received = np.searchsorted(t[keep], grid - delay + 1e-7, side="right") - 1
    available = received >= 0
    source_index = np.full(len(grid), -1, dtype=int)
    source_index[available] = kept[received[available]]
    held = np.full((len(grid), 16), np.nan)
    source_time = np.full(len(grid), np.nan)
    held[available] = x[source_index[available]]
    source_time[available] = t[source_index[available]]
    if np.any(source_time[available] > grid[available] - delay + 1e-7):
        raise AssertionError("A future measurement entered the runtime stream")
    return {
        "time": grid,
        "eef": held,
        "source_time": source_time,
        "source_index": source_index,
        "features": models.causal_features(grid, held),
    }


def load_stream(
    root: Path, row: dict[str, Any], stress: str = "clean"
) -> dict[str, np.ndarray]:
    if Path(row["sample"]).name != row["sample"] or row["sample"] in (".", ".."):
        raise ValueError("Recording identifier must be a local basename")
    path = root / row["arrays"]
    with np.load(path, allow_pickle=False) as data:
        return decision_stream(data["time"], data["eef"], row["sample"], stress)


def source_hashes() -> dict[str, str]:
    paths = set(Path("src/dual_rec/failtime").glob("*.py"))
    # Verification/packaging tools are versioned separately; they cannot change
    # the frozen score generator, input arrays or calibration artifacts.
    paths.add(Path("src/dual_rec/reboot/overnight_models.py"))
    return {str(path): digest(path) for path in sorted(paths)}


def checkpoint(
    root: Path, name: str, fit: Any = None, training_ids: list[str] | None = None
) -> Any:
    path = root / "models" / (name + ".pt")
    index = (
        read(root, "models_index.json") if (root / "models_index.json").exists() else {}
    )
    if path.exists():
        if name not in index or digest(path) != index[name]["sha256"]:
            raise ValueError("Completed checkpoint lacks a matching integrity record")
        value = torch.load(path, map_location="cpu", weights_only=False)
        if value["registration_sha256"] != digest(root / "registration.json"):
            raise ValueError("Checkpoint belongs to a different registration")
        return value["fit"]
    if fit is None:
        raise FileNotFoundError(path)
    path.parent.mkdir(exist_ok=True)
    value = {
        "fit": fit,
        "training_ids": training_ids,
        "registration_sha256": digest(root / "registration.json"),
        "source_sha256": source_hashes(),
    }
    temporary = path.with_suffix(".partial")
    torch.save(value, temporary)
    temporary.replace(path)
    index[name] = {
        "path": str(path.relative_to(root)),
        "sha256": digest(path),
        "training_ids": training_ids,
        "registration_sha256": value["registration_sha256"],
    }
    save(root / "models_index.json", index)
    progress(root, "MODEL_COMPLETE", model=name, sha256=index[name]["sha256"])
    return fit


def train(root: Path) -> None:
    registration(root)
    if (root / "models_source_seal.json").exists():
        raise ValueError("Training is frozen by the pre-evaluation model seal")
    rows = population(root, "train")
    streams = [load_stream(root, row) for row in rows]
    success = [
        {"robot": r["robot"], "time": s["time"], "eef": s["eef"]}
        for r, s in zip(rows, streams, strict=True)
        if r["verdict"] == "success"
    ]
    successes = [r["sample"] for r in rows if r["verdict"] == "success"]
    if not (root / "models/nominal.pt").exists():
        checkpoint(root, "nominal", models.fit_nominal(success), successes)
    else:
        checkpoint(root, "nominal")
    xs = [s["features"] for s in streams]
    times = [s["time"] for s in streams]
    labels = [
        (
            (s["time"] >= float(r["onset"]))
            if r["verdict"] == "fail"
            else np.zeros(len(s["time"]), bool)
        ).astype(float)
        for r, s in zip(rows, streams, strict=True)
    ]
    masks = [np.isfinite(x).all(axis=1) for x in xs]
    ids = [r["sample"] for r in rows]
    if not (root / "models/B3.pt").exists():
        checkpoint(
            root, "B3", models.fit_logistic_detector(xs, times, labels, masks), ids
        )
    else:
        checkpoint(root, "B3")
    for seed in SEEDS:
        name = f"B4_seed{seed}"
        if not (root / "models" / (name + ".pt")).exists():
            checkpoint(
                root, name, models.fit_gru(xs, labels, masks, seed=seed, epochs=30), ids
            )
        else:
            checkpoint(root, name)
    selected = [
        (r, s)
        for r, s in zip(rows, streams, strict=True)
        if s["time"][-1] >= 1 and (r["verdict"] == "success" or float(r["onset"]) > 1)
    ]
    role_ids = [r["sample"] for r, _ in selected]
    if not (root / "models/source_role.pt").exists():
        design = [
            windows(s["features"][s["time"] <= 1], s["time"][s["time"] <= 1])[-1:]
            for _, s in selected
        ]
        ys = [np.array([r["verdict"] == "fail"], float) for r, _ in selected]
        if not ys or not 0 < sum(y[0] for y in ys) < len(ys):
            raise ValueError(
                "Early-prefix role diagnostic lacks two-class training support"
            )
        fit = fit_logistic(
            design, ys, [np.ones(1, bool) for _ in ys], regularization=0.01
        )
        checkpoint(root, "source_role", fit, role_ids)
    else:
        fit = checkpoint(root, "source_role")
    save_npz(
        root / "source_role_model.npz",
        beta=fit["beta"],
        mean=fit["scaler"]["mean"],
        std=fit["scaler"]["std"],
    )
    save(root / "source_role_training_ids.json", role_ids)
    save(
        root / "training_summary.json",
        {
            "training_ids": ids,
            "success_nominal_ids": successes,
            "failure_prior": sum(r["verdict"] == "fail" for r in rows) / len(rows),
            "seeds": list(SEEDS),
            "epochs": 30,
            "checkpoint_count": len(read(root, "models_index.json")),
            "source_role_training_ids": role_ids,
            "input_contract": "10Hz held causal EEF16 and decision-grid backward differences; robot stratum only",
        },
    )
    progress(
        root, "TRAINING_COMPLETE", checkpoints=len(read(root, "models_index.json"))
    )


def risk_stream(
    root: Path, row: dict[str, Any], stress: str = "clean"
) -> dict[str, np.ndarray]:
    from dual_rec.failtime.baseline_cp import score_sign_cpd

    stream = load_stream(root, row, stress)
    t, eef, x = stream["time"], stream["eef"], stream["features"]
    nominal = checkpoint(root, "nominal")
    risks = models.prior_scores(t, read(root, "training_summary.json")["failure_prior"])
    risks["B1"] = score_sign_cpd(t, eef, row["robot"], nominal, root / "upstream")
    risks["B2"], _, _ = models.score_nominal(
        nominal, row["robot"], t, eef, conditioned=False
    )
    risks["B3"] = models.predict_logistic_detector(checkpoint(root, "B3"), x, t)
    seed_scores = [
        models.predict_gru(checkpoint(root, f"B4_seed{seed}"), x) for seed in SEEDS
    ]
    risks["B4"] = np.mean(seed_scores, axis=0)
    risks["MCSFA"], mode, backoff = models.score_nominal(nominal, row["robot"], t, eef)
    risks["MCSFA_no_mode"] = risks["B2"].copy()
    risks["MCSFA_no_accum"], _, _ = models.score_nominal(
        nominal, row["robot"], t, eef, accumulate=False
    )
    available = np.isfinite(eef).all(axis=1)
    for value in risks.values():
        value[~available] = np.nan
    return {
        **stream,
        **risks,
        **{
            f"B4_seed{seed}": values
            for seed, values in zip(SEEDS, seed_scores, strict=True)
        },
        "mode": mode,
        "mode_backoff": backoff,
    }


def save_risks(
    root: Path, row: dict[str, Any], split: str, stress: str = "clean"
) -> dict[str, np.ndarray]:
    path = root / "risks" / split / stress / (row["sample"] + ".npz")
    index = (
        read(root, "risk_registry.json")
        if (root / "risk_registry.json").exists()
        else []
    )
    existing = next(
        (
            r
            for r in index
            if (r["sample"], r["split"], r["stress"]) == (row["sample"], split, stress)
        ),
        None,
    )
    if path.exists():
        if existing is None or digest(path) != existing["sha256"]:
            raise ValueError("Saved risk stream lacks its matching integrity record")
        with np.load(path, allow_pickle=False) as data:
            return {k: data[k] for k in data.files}
    stream = risk_stream(root, row, stress)
    save_npz(path, **stream)
    index.append(
        {
            "sample": row["sample"],
            "split": split,
            "stress": stress,
            "path": str(path.relative_to(root)),
            "sha256": digest(path),
        }
    )
    save(root / "risk_registry.json", index)
    return stream


def source_role(
    root: Path, rows: list[dict[str, Any]], split: str
) -> list[dict[str, Any]]:
    fit = checkpoint(root, "source_role")
    result = []
    for row in rows:
        stream = load_stream(root, row)
        eligible = bool(
            stream["time"][-1] >= 1
            and (row["verdict"] == "success" or float(row["onset"]) > 1)
        )
        score = None
        if eligible:
            keep = stream["time"] <= 1
            vector = windows(stream["features"][keep], stream["time"][keep])[-1:]
            score = float(predict_logistic(fit, vector)[0])
        result.append(
            {
                "sample": row["sample"],
                "split": split,
                "score": score,
                "label": row["verdict"] == "fail",
                "eligible": eligible,
                "exclusion": None
                if eligible
                else "first_second_not_complete_strictly_before_onset",
            }
        )
    return result


def calibrate(root: Path) -> None:
    from dual_rec.failtime.metrics import calibrate as fit_threshold

    registration(root)
    if (root / "models_source_seal.json").exists():
        verify_seal(root)
        return
    calibration = population(root, "calibration")
    streams = {r["sample"]: save_risks(root, r, "calibration") for r in calibration}
    thresholds = []
    for method in METHODS:
        success, prefix = [], []
        for row in calibration:
            data = streams[row["sample"]]
            keep = (
                np.ones(len(data["time"]), bool)
                if row["verdict"] == "success"
                else data["time"] < float(row["onset"])
            )
            entry = {
                "sample": row["sample"],
                "time": data["time"][keep],
                "scores": data[method][keep],
            }
            (success if row["verdict"] == "success" else prefix).append(entry)
        for alpha in ALPHAS:
            thresholds.append(
                {
                    "method": method,
                    "alpha": alpha,
                    **fit_threshold(success, prefix, alpha),
                }
            )
    save(root / "thresholds.json", thresholds)
    training = population(root, "train")
    contrasts = []
    for row in training:
        data = save_risks(root, row, "train")
        if row["verdict"] != "fail":
            continue
        onset = float(row["onset"])
        for method in METHODS:
            before = np.flatnonzero(
                (data["time"] >= onset - 1)
                & (data["time"] < onset)
                & np.isfinite(data[method])
            )
            after = np.flatnonzero(
                (data["time"] >= onset)
                & (data["time"] <= onset + 1)
                & np.isfinite(data[method])
            )
            n = min(len(before), len(after))
            contrasts.append(
                {
                    "sample": row["sample"],
                    "method": method,
                    "samples": n,
                    "mean_change": float(
                        data[method][after[:n]].mean()
                        - data[method][before[-n:]].mean()
                    )
                    if n
                    else None,
                }
            )
    save(root / "development_contrasts.json", contrasts)
    save(
        root / "source_role_predictions.json",
        source_role(root, training, "train")
        + source_role(root, calibration, "calibration"),
    )
    paths = [
        root / "registration.json",
        root / "thresholds.json",
        root / "models_index.json",
        root / "training_summary.json",
        root / "cohort_qualification.json",
        root / "data_gate.json",
        root / "source_role_model.npz",
        root / "source_role_training_ids.json",
    ]
    paths += [
        root / row["arrays"]
        for row in read(root, "cohort_qualification.json")
        if row.get("status") == "verified"
    ]
    paths += sorted((root / "upstream/protracer").glob("*.py"))
    paths += [
        root / r["path"]
        for r in read(root, "risk_registry.json")
        if r["split"] in ("train", "calibration")
    ]
    paths += list((root / "models").glob("*.pt"))
    save(
        root / "models_source_seal.json",
        {
            "scope": "Frozen development models and matched calibration before held-out performance scoring; qualification metadata already inspected",
            "sha256": {str(p.relative_to(root)): digest(p) for p in sorted(paths)},
            "source_sha256": source_hashes(),
            "methods": list(METHODS),
            "seeds": list(SEEDS),
            "calibration_ids": [r["sample"] for r in calibration],
            "training_ids": [r["sample"] for r in training],
        },
    )
    progress(root, "CALIBRATION_AND_MODEL_SEAL_COMPLETE", thresholds=len(thresholds))


def verify_seal(root: Path) -> None:
    seal = read(root, "models_source_seal.json")
    for name, expected in seal["sha256"].items():
        if digest(root / name) != expected:
            raise ValueError(f"Frozen scientific input changed: {name}")
    for name, expected in seal["source_sha256"].items():
        if digest(Path(name)) != expected:
            raise ValueError(f"Frozen scientific source changed: {name}")


def evaluate(root: Path) -> None:
    from dual_rec.failtime.metrics import outcome

    verify_seal(root)
    thresholds = read(root, "thresholds.json")
    outcomes = []
    rows = population(root, "evaluation")
    for row in rows:
        for stress in STRESSES:
            data = save_risks(root, row, "evaluation", stress)
            for setting in thresholds:
                for persistence in PERSISTENCES:
                    result = outcome(
                        row,
                        data["time"],
                        data[setting["method"]],
                        setting["threshold"],
                        persistence,
                    )
                    result.update(
                        split="evaluation",
                        stress=stress,
                        method=setting["method"],
                        alpha=setting["alpha"],
                        persistence=persistence,
                    )
                    outcomes.append(result)
        progress(root, "EVALUATION_RECORDING_COMPLETE", sample=row["sample"])
    save(root / "outcomes.json", outcomes)
    role = read(root, "source_role_predictions.json")
    role = [r for r in role if r["split"] != "evaluation"] + source_role(
        root, rows, "evaluation"
    )
    save(root / "source_role_predictions.json", role)
    verify_seal(root)
    progress(
        root,
        "FIXED_EVALUATION_MATRIX_COMPLETE",
        outcomes=len(outcomes),
        evaluation_recordings=len(rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("train", "calibrate", "evaluate"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Completed campaign is sealed")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    {"train": train, "calibrate": calibrate, "evaluate": evaluate}[args.stage](
        args.root
    )


if __name__ == "__main__":
    main()
