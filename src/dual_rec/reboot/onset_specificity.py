"""Fixed-score onset feasibility, matched calibration and two logistic controls."""

from __future__ import annotations

import argparse
import json
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch

from dual_rec.reboot.overnight_data import save_json, sha, targets
from dual_rec.reboot.overnight_metrics import first_alarm, outcome
from dual_rec.reboot.overnight_models import fit_logistic, predict_logistic, windows

OLD = Path("results/reboot-overnight/20261111T224622Z")
METHODS = ("B0", "B1", "B2", "B3", "P0", "P1", "P2")
ALPHAS = (0.05, 0.10, 0.20)
EXPECTED_SEAL = "f9d79bfc7df980a83e198ba33f1a0cfdf13a1222f53723a2deb80ffc12b7c07b"
EXPECTED_ARCHIVE = "9e3ba45e0478a239c839502590bff5747b82e2b367b586f7e886aadeb0b106db"


def read(root, name):
    return json.loads((root / name).read_text())


def progress(root, phase, **details):
    row = {"phase": phase, "epoch": time.time(), **details}
    with (root / "ledger.jsonl").open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    save_json(root / "progress.json", row)


def registry():
    return [r for r in read(OLD, "registry.json") if r["eligible"]]


@lru_cache(maxsize=1500)
def inherited(fold, variant, split, group, stress="clean"):
    path = (
        OLD
        / "predictions"
        / f"fold{fold}"
        / variant
        / stress
        / split
        / (group.split(":")[1] + ".npz")
    )
    with np.load(path, allow_pickle=False) as source:
        return {
            key: source[key]
            for key in (
                "time",
                "features",
                "native_frame",
                "source_frame",
                "horizon",
                *METHODS,
            )
        }


def load_scores(root, fold, variant, split, row, method, stress="clean"):
    data = inherited(fold, variant, split, row["group"], stress)
    if method != "B2R":
        return data, data[method]
    path = (
        root
        / "b2r_predictions"
        / f"fold{fold}"
        / variant
        / stress
        / split
        / (row["group"].split(":")[1] + ".npz")
    )
    with np.load(path) as saved:
        np.testing.assert_array_equal(saved["time"], data["time"])
        return data, saved["scores"]


def persistence_series(times, scores):
    """Largest finite threshold with a valid inherited streak ending at each t."""
    result = np.full(len(times), -np.inf)
    if len(times) and (not np.isfinite(times).all() or np.any(np.diff(times) <= 0)):
        raise ValueError("Strictly increasing finite decision timestamps required")
    for end, now in enumerate(times):
        start = np.searchsorted(times, now - 0.1 + 2e-6, side="right") - 1
        if 0 <= start < end and np.isfinite(scores[start : end + 1]).all():
            result[end] = np.min(scores[start : end + 1])
    return result


def maximum(values):
    return float(np.max(values)) if len(values) else -np.inf


def encoded(value):
    return float(value) if np.isfinite(value) else None


def capacities(row, data, scores):
    r = persistence_series(data["time"], scores)
    if row["role"] == "reference":
        return {"C": maximum(r), "A": -np.inf, "B": -np.inf, "observable": False}, r
    high = min(row["recovery"], float(data["horizon"]), row["frames"] / 30 - 1 / 30)
    a = maximum(r[data["time"] < row["onset"]])
    b = maximum(r[(data["time"] >= row["onset"]) & (data["time"] < high)])
    return {"A": a, "B": b, "C": -np.inf, "observable": bool(row["onset"] < high)}, r


def population_threshold(values, alpha):
    valid = [float(v) for v in values if np.isfinite(v)]
    if not valid:
        return {
            "available": False,
            "threshold": None,
            "count": 0,
            "invalid": len(values),
        }
    allowed = int(np.floor(alpha * len(valid)))
    boundary = sorted(valid, reverse=True)[allowed]
    threshold = float(np.nextafter(boundary, np.inf))
    return {
        "available": True,
        "threshold": threshold,
        "count": len(valid),
        "invalid": len(values) - len(valid),
        "allowed": allowed,
        "alarms": sum(v >= threshold for v in valid),
    }


def prepare(root):
    assert sha(OLD / "completion_manifest.json") == EXPECTED_SEAL
    seal = read(OLD, "completion_manifest.json")
    archive = OLD / "supervisor_review.tar.gz"
    archive_check = {"available": archive.exists()}
    if archive.exists():
        archive_check["sha256"] = sha(archive)
        assert archive_check["sha256"] == EXPECTED_ARCHIVE
    paths = [
        OLD / name
        for name in (
            "registry.json",
            "registration.json",
            "thresholds.json",
            "outcomes.json",
            "summary.json",
            "phase_results.json",
            "main_prediction_seal.json",
        )
    ]
    paths += sorted((OLD / "predictions").rglob("*.npz"))
    paths += sorted((OLD / "models").glob("*.pt"))
    consumed = {}
    for path in paths:
        digest = sha(path)
        assert digest == seal["evidence_sha256"][str(path.relative_to(OLD))], str(path)
        consumed[str(path)] = digest
    save_json(root / "consumed_inputs.json", consumed)
    rows = registry()
    assert len(rows) == len({r["group"] for r in rows}) == 117
    assert sum(r["role"] == "recovery" for r in rows) == 55
    save_json(
        root / "input_verification.json",
        {
            "seal_sha256": EXPECTED_SEAL,
            "archive": archive_check,
            "consumed_files": len(consumed),
        },
    )
    old_registration = read(OLD, "registration.json")
    new = {
        "run": str(root),
        "date": "2026-11-12",
        "scope": "Exploratory reanalysis/cross-fitting on exposed data; no untouched confirmation or physical recovery claim",
        "reviewed_base": "c2e24d38b61e2a3d7db422c971342eab8cac4b7e",
        "source_root": str(OLD),
        "consumed_inputs_sha256": sha(root / "consumed_inputs.json"),
        "prior_seal_sha256": EXPECTED_SEAL,
        "prior_archive_sha256": EXPECTED_ARCHIVE,
        "prior_registration_sha256": sha(OLD / "registration.json"),
        "prior_registry_sha256": sha(OLD / "registry.json"),
        "folds": old_registration["folds"],
        "seeds": [11, 23, 37],
        "models": list(METHODS) + ["B2R"],
        "primary_input": "Q",
        "secondary_input": "QC",
        "alphas": list(ALPHAS),
        "primary_alpha": 0.1,
        "calibration": {
            "C0": "Nominal-reference persistent capacities only; inherited conservative ties",
            "C1": "max(separate nominal-reference and strictly pre-onset recovery-prefix conservative thresholds), one constant threshold per fold/model/input",
            "invalid_prefix": "Report IDs/reasons; exclude recordings with no finite pre-onset persistent capacity from that population's denominator; never fabricate capacity",
        },
        "alarm": old_registration["alarm"],
        "horizon": old_registration["horizon_rule"],
        "feasibility": "Full-history ending-streak capacity; A<theta<=B. Candidate thresholds are all finite raw score breakpoints and their nextafter(+inf), plus +inf. Exact shared-threshold ceilings constrain BOTH evaluation recording alarm populations at each fixed alpha; tie chooses largest threshold. Hindsight only, never passed to deployment.",
        "contrasts": {
            "pre": "[tf-gap-1,tf-gap)",
            "post": "[tf+gap,min(tf+gap+1,tr,H))",
            "gaps": [0, 0.5],
            "equalization": "finite last n pre / first n target samples; n=min counts; persistent capacities retain full causal history",
            "models": ["B0", "B2", "B3", "P0", "P1", "P2"],
        },
        "source_role": "First full second [0,1] at original 10Hz, strictly before tf for recoveries. Original B2 summaries/L2/optimizer; three training folds, evaluate k, fixed .5 decision threshold. Diagnostic source role only; ten fits maximum.",
        "source_role_exclusions": [
            r["group"] for r in rows if r["role"] == "recovery" and r["onset"] <= 1
        ],
        "B2R": "Original B2 feature summaries, L2 .01, LBFGS maxiter200/ftol1e-9/gtol1e-6, equal recording loss, train-only scaler/std floor1e-6/clip10, unchanged positive-weight rule capped10; training recoveries only, pre-recovery masks. Ten fits maximum.",
        "primary_comparisons": ["B2R/C1-B2/C1", "P1/C1-P0/C1", "P1/C1-P2/C1"],
        "bootstrap": {
            "draws": 2000,
            "seed": 20261112,
            "unit": "canonical recording",
            "strata": "role",
        },
        "rate_intervals": "Wilson 95%; dependence within collection remains; zero bootstrap interval is not population equivalence",
        "annotation_review": "Three smallest canonical hashes in each available C0-alpha.1 category per model/input: premature infeasible, premature feasible, timely, miss; fixed released bounds, never adjudicated or repaired",
        "fit_cap": 20,
        "limits": read(root, "initial.json")["limits"],
    }
    save_json(root / "registration.json", new)
    (Path("config") / f"reboot_onset_{root.name}.json").write_bytes(
        (root / "registration.json").read_bytes()
    )
    progress(
        root,
        "REGISTERED",
        consumed_files=len(consumed),
        source_prefix_eligible=116,
        fits=0,
    )
    print(
        json.dumps(
            {
                "consumed_files": len(consumed),
                "cohort": 117,
                "archive": archive_check,
                "source_role_exclusions": new["source_role_exclusions"],
            }
        )
    )


def reproduce(root):
    thresholds = read(OLD, "thresholds.json")
    outcomes = []
    for row in registry():
        for variant in ("Q", "QC"):
            data = inherited(row["fold"], variant, "evaluation", row["group"])
            for method in METHODS:
                result = outcome(
                    row,
                    data["time"],
                    data[method],
                    thresholds[f"{row['fold']}:{variant}:{method}"]["threshold"],
                    float(data["horizon"]),
                )
                result.update(method=method, variant=variant)
                outcomes.append(result)
    original = [
        r
        for r in read(OLD, "outcomes.json")
        if r["stress"] == "clean" and r["boundary_delta"] == 0
    ]
    indexed = {(r["group"], r["variant"], r["method"]): r for r in original}
    failures = []
    for row in outcomes:
        before = indexed[(row["group"], row["variant"], row["method"])]
        for key in (
            "alarm_time",
            "timely",
            "premature",
            "reference_alarm",
            "status",
            "evaluable",
            "delay",
            "lead",
        ):
            if row[key] != before[key]:
                failures.append(
                    {
                        "group": row["group"],
                        "field": key,
                        "old": before[key],
                        "new": row[key],
                    }
                )
    save_json(
        root / "original_reproduction.json",
        {
            "status": "PASS" if not failures else "MISMATCH",
            "rows": outcomes,
            "failures": failures,
        },
    )
    if failures:
        raise ValueError("Original first-alarm reproduction mismatch")
    progress(root, "ORIGINAL_REPRODUCED", rows=len(outcomes))


def feasibility(root, *, additional=False):
    rows = registry()
    old_thresholds = read(OLD, "thresholds.json")
    methods = ("B2R",) if additional else METHODS
    recording_rows, ceilings = [], []
    directory = root / "hindsight_only"
    directory.mkdir(exist_ok=True)
    for fold in range(5):
        population = [r for r in rows if r["fold"] == fold]
        for variant in ("Q", "QC"):
            for method in methods:
                a, b, c, breakpoints = [], [], [], []
                for row in population:
                    data, scores = load_scores(
                        root, fold, variant, "evaluation", row, method
                    )
                    value, _ = capacities(row, data, scores)
                    threshold = old_thresholds.get(
                        f"{fold}:{variant}:{method}", {}
                    ).get("threshold")
                    margin = (
                        value["B"] - value["A"]
                        if np.isfinite(value["B"]) and np.isfinite(value["A"])
                        else None
                    )
                    recording_rows.append(
                        {
                            "group": row["group"],
                            "role": row["role"],
                            "fold": fold,
                            "variant": variant,
                            "method": method,
                            **{k: encoded(value[k]) for k in ("A", "B", "C")},
                            "minus_infinity_fields": [
                                k for k in ("A", "B", "C") if not np.isfinite(value[k])
                            ],
                            "margin": margin,
                            "margin_reason": None
                            if margin is not None
                            else "one_or_both_capacities_minus_infinity",
                            "observable": value["observable"],
                            "feasible": bool(
                                value["observable"] and value["B"] > value["A"]
                            ),
                            "original_threshold": threshold,
                            "original_first_alarm": first_alarm(
                                data["time"], scores, threshold
                            )
                            if threshold is not None
                            else None,
                        }
                    )
                    breakpoints.extend(scores[np.isfinite(scores)].tolist())
                    if row["role"] == "recovery":
                        a.append(value["A"])
                        b.append(value["B"])
                    else:
                        c.append(value["C"])
                points = np.unique(breakpoints)
                points = (
                    np.unique(np.r_[points, np.nextafter(points, np.inf), np.inf])
                    if len(points)
                    else np.array([0.0, np.inf])
                )
                a, b, c = np.array(a), np.array(b), np.array(c)
                timely = (
                    (a[None, :] < points[:, None]) & (points[:, None] <= b[None, :])
                ).sum(1)
                premature = (points[:, None] <= a[None, :]).sum(1)
                reference = (points[:, None] <= c[None, :]).sum(1)
                np.savez_compressed(
                    directory / f"fold{fold}_{variant}_{method}.npz",
                    threshold=points,
                    timely=timely,
                    premature=premature,
                    reference=reference,
                )
                for alpha in ALPHAS:
                    allowed = (premature <= np.floor(alpha * len(a))) & (
                        reference <= np.floor(alpha * len(c))
                    )
                    best = int(np.max(timely[allowed]))
                    index = np.flatnonzero(allowed & (timely == best))[-1]
                    ceilings.append(
                        {
                            "fold": fold,
                            "variant": variant,
                            "method": method,
                            "alpha": alpha,
                            "scope": "HINDSIGHT_ONLY_NOT_DEPLOYABLE",
                            "timely": best,
                            "recoveries": len(a),
                            "premature": int(premature[index]),
                            "references": len(c),
                            "reference_alarms": int(reference[index]),
                            "oracle_threshold": encoded(points[index]),
                            "threshold_kind": "finite"
                            if np.isfinite(points[index])
                            else "plus_infinity",
                            "breakpoints_checked": len(points),
                        }
                    )
    if additional:
        recording_rows = [
            r for r in read(root, "score_feasibility.json") if r["method"] != "B2R"
        ] + recording_rows
        ceilings = [
            r for r in read(root, "hindsight_ceilings.json") if r["method"] != "B2R"
        ] + ceilings
    save_json(root / "score_feasibility.json", recording_rows)
    save_json(root / "hindsight_ceilings.json", ceilings)
    progress(
        root,
        "FEASIBILITY_COMPLETE",
        additional=additional,
        recording_rows=len(recording_rows),
        ceilings=len(ceilings),
    )


def fit_controls(root):
    rows = registry()
    folds = read(OLD, "registration.json")["folds"]
    destination = root / "models"
    destination.mkdir(exist_ok=True)
    for fold in range(5):
        train = [r for r in rows if r["fold"] not in (fold, (fold + 1) % 5)]
        for variant in ("Q", "QC"):
            for kind in ("source_role", "B2R"):
                path = destination / f"fold{fold}_{variant}_{kind}.pt"
                if path.exists():
                    recorded = [
                        json.loads(line)
                        for line in (root / "ledger.jsonl").read_text().splitlines()
                    ]
                    expected = next(
                        r["sha256"]
                        for r in reversed(recorded)
                        if r["phase"] == "FIT_COMPLETE" and r["model"] == path.stem
                    )
                    if sha(path) != expected:
                        raise ValueError("Completed control checkpoint changed")
                    existing = torch.load(path, map_location="cpu", weights_only=False)
                    assert existing["registration_sha256"] == sha(
                        root / "registration.json"
                    )
                    continue
                if len(list(destination.glob("*.pt"))) >= 20:
                    raise ValueError("Twenty-fit cap reached")
                selected = [
                    r for r in train if kind == "source_role" or r["role"] == "recovery"
                ]
                if kind == "source_role":
                    selected = [
                        r
                        for r in selected
                        if r["role"] == "reference" or r["onset"] > 1
                    ]
                xs, ys, masks = [], [], []
                for row in selected:
                    data = inherited(row["fold"], variant, "evaluation", row["group"])
                    if kind == "source_role":
                        keep = data["time"] <= 1 + 2e-6
                        if data["time"][keep][-1] < 1 - 2e-6:
                            raise ValueError("Incomplete first second")
                        xs.append(
                            windows(data["features"][keep], data["time"][keep])[-1:]
                        )
                        ys.append(np.array([row["role"] == "recovery"], dtype=float))
                        masks.append(np.ones(1, dtype=bool))
                    else:
                        y, mask, _ = targets(
                            row,
                            {
                                "time": data["time"],
                                "features": data["features"],
                                "native_frame": data["native_frame"],
                            },
                            folds[fold]["horizon"],
                        )
                        if not np.any(y[mask]) or not np.any(1 - y[mask]):
                            raise ValueError("Missing within-recording label support")
                        xs.append(windows(data["features"], data["time"]))
                        ys.append(y)
                        masks.append(mask)
                fit = fit_logistic(xs, ys, masks)
                fit.update(
                    registration_sha256=sha(root / "registration.json"),
                    training_ids=[r["group"] for r in selected],
                    kind=kind,
                    deployable=kind == "B2R",
                )
                temporary = path.with_suffix(".partial")
                torch.save(fit, temporary)
                temporary.replace(path)
                progress(
                    root,
                    "FIT_COMPLETE",
                    model=path.stem,
                    sha256=sha(path),
                    fits=len(list(destination.glob("*.pt"))),
                )
            fit = torch.load(
                destination / f"fold{fold}_{variant}_B2R.pt",
                map_location="cpu",
                weights_only=False,
            )
            for split, population in (
                ("calibration", [r for r in rows if r["fold"] == (fold + 1) % 5]),
                ("evaluation", [r for r in rows if r["fold"] == fold]),
            ):
                for stress in (
                    ("clean",)
                    if split == "calibration"
                    else ("clean", "drop0.1", "drop0.3", "delay0.2", "delay0.5")
                ):
                    directory = (
                        root
                        / "b2r_predictions"
                        / f"fold{fold}"
                        / variant
                        / stress
                        / split
                    )
                    directory.mkdir(parents=True, exist_ok=True)
                    for row in population:
                        path = directory / (row["group"].split(":")[1] + ".npz")
                        if path.exists():
                            continue
                        data = inherited(fold, variant, split, row["group"], stress)
                        scores = predict_logistic(
                            fit, windows(data["features"], data["time"])
                        )
                        np.savez_compressed(path, time=data["time"], scores=scores)
    source_rows = []
    for fold in range(5):
        for variant in ("Q", "QC"):
            fit = torch.load(
                destination / f"fold{fold}_{variant}_source_role.pt",
                map_location="cpu",
                weights_only=False,
            )
            for row in rows:
                if (
                    row["fold"] != fold
                    or row["role"] == "recovery"
                    and row["onset"] <= 1
                ):
                    continue
                data = inherited(fold, variant, "evaluation", row["group"])
                keep = data["time"] <= 1 + 2e-6
                score = float(
                    predict_logistic(
                        fit, windows(data["features"][keep], data["time"][keep])[-1:]
                    )[0]
                )
                source_rows.append(
                    {
                        "group": row["group"],
                        "fold": fold,
                        "variant": variant,
                        "role": row["role"],
                        "score": score,
                        "prediction": score >= 0.5,
                    }
                )
    save_json(root / "source_role_predictions.json", source_rows)
    progress(root, "TWENTY_CONTROLS_COMPLETE", fits=len(list(destination.glob("*.pt"))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=(
            "prepare",
            "reproduce",
            "feasibility",
            "fit",
            "additional-feasibility",
        ),
        required=True,
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    if args.stage == "prepare":
        prepare(args.root)
    elif args.stage == "reproduce":
        reproduce(args.root)
    elif args.stage == "feasibility":
        feasibility(args.root)
    elif args.stage == "additional-feasibility":
        feasibility(args.root, additional=True)
    else:
        fit_controls(args.root)


if __name__ == "__main__":
    main()
