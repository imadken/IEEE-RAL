"""Three-way finite/support/cross-fit reporting and fixed parent-bootstrap comparisons."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

FIELDS = (
    "episodes",
    "recommended",
    "adequate",
    "unacceptable",
    "strict_recommended",
    "strict_success",
    "strict_error",
    "provisional_recommended",
    "literals",
    "support_rows",
    "parent_support",
    "channel_sum",
    "abstained",
    "reference_insufficient",
    "ambiguity",
    "inadequacy",
    "overlap",
)
RATIOS = {
    "coverage": ("recommended", "episodes"),
    "successful_strict_coverage": ("strict_success", "episodes"),
    "unacceptable_rate": ("unacceptable", "recommended"),
    "unsuccessful_action_per_checkpoint": ("unacceptable", "episodes"),
    "success_per_checkpoint": ("adequate", "episodes"),
    "mean_literals": ("literals", "recommended"),
    "mean_support_rows": ("support_rows", "recommended"),
    "mean_parent_support": ("parent_support", "recommended"),
    "mean_added_channels": ("channel_sum", "episodes"),
}


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def score(result, row, channels, action="all"):
    chosen = result["action"]
    emitted = chosen is not None and action in ("all", chosen)
    success = int(row["outcomes"][chosen + "_value"]) if emitted else 0
    strict = result["status"] == "STRICT_FINITE_REFERENCE"
    kinds = {o["kind"] for o in result.get("diagnosis", {}).get("obstructions", [])}
    return [
        1,
        int(emitted),
        success,
        int(emitted) - success,
        int(emitted and strict),
        int(strict) * success,
        int(strict) * (int(emitted) - success),
        int(emitted and result["status"] == "PROVISIONAL_UNCALIBRATED"),
        len(result["evidence"]) if emitted else 0,
        result["support"] if emitted else 0,
        result["independent_parents"] if emitted else 0,
        channels,
        int(chosen is None),
        int("REFERENCE_INSUFFICIENT" in kinds),
        int("OBSERVATIONAL_AMBIGUITY" in kinds),
        int("REPERTOIRE_INADEQUATE" in kinds),
        int({"OBSERVATIONAL_AMBIGUITY", "REPERTOIRE_INADEQUATE"} <= kinds),
    ]


def summarize(array, weights):
    counts = array.sum(axis=0)
    samples = weights @ array
    groups = int((array[:, FIELDS.index("recommended")] > 0).sum())
    rates = {}
    for name, (num, den) in RATIOS.items():
        n, d = FIELDS.index(num), FIELDS.index(den)
        valid = samples[:, d] > 0
        sparse = den == "recommended" and groups < 10
        rates[name] = {
            "value": float(counts[n] / counts[d]) if counts[d] else None,
            "parent_percentile95": np.quantile(
                samples[valid, n] / samples[valid, d], [0.025, 0.975]
            ).tolist()
            if valid.any() and not sparse
            else None,
            "sparse_stratum": sparse,
        }
    return {
        "counts": dict(zip(FIELDS, map(int, counts), strict=True)),
        "rates": rates,
        "seed_groups": int((array[:, 0] > 0).sum()),
        "recommending_seed_groups": groups,
    }


def model_outputs(root):
    parts = {p.stem: load(p) for p in (root / "models").glob("*.json")}
    for designpath in sorted((root / "designs").glob("*.json")):
        design = load(designpath)
        for d in design["selected_designs"]:
            model = parts[d["model"]]
            for p in model["predictions"]:
                result = model["decisions"][p["decision_id"]]["result"]
                yield design, d, p, result


def analyze(root):
    config = load(Path("config/dsre_evidence_repair.json"))
    data = [
        json.loads(s) for s in (root / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    by_id = {r["id"]: r for r in data}
    tasks = ("PickCube-v1", "PushCube-v1")
    groups = {t: sorted({r["group"] for r in data if r["task"] == t}) for t in tasks}
    gindex = {t: {g: i for i, g in enumerate(groups[t])} for t in tasks}
    weights = {}
    draws_info = {}
    for i, t in enumerate(tasks):
        draws = np.random.default_rng(config["bootstrap_seed"] + i).integers(
            0, len(groups[t]), (config["bootstrap_draws"], len(groups[t]))
        )
        weights[t] = np.stack([np.bincount(d, minlength=len(groups[t])) for d in draws])
        draws_info[t] = {
            "groups": groups[t],
            "seed": config["bootstrap_seed"] + i,
            "draws_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
        }
    save(
        root / "uncertainty_plan.json",
        {
            "draws": 2000,
            "unit": "task/seed, both conditions together",
            "tasks": draws_info,
        },
    )
    arrays = defaultdict(lambda: np.zeros((211, len(FIELDS)), dtype=np.int64))
    per_input = defaultdict(dict)
    errors = []
    expanded = 0
    for design, d, p, result in model_outputs(root):
        row = by_id[p["id"]]
        task = row["task"]
        expanded += 1
        operating = f"{d['selector']}|{d['budget']}|{p['method']}"
        per_input[row["id"]][operating] = result
        if (
            p["method"] == "DSRE"
            and result["action"]
            and not row["outcomes"][result["action"] + "_value"]
        ):
            errors.append(
                {
                    "id": row["id"],
                    "selector": d["selector"],
                    "budget": d["budget"],
                    "model": d["model"],
                    "action": result["action"],
                    "outcomes": row["outcomes"],
                    "initial_success": row["initial_success"],
                    "evidence": result["evidence"],
                    "support": result["support"],
                    "independent_parents": result["independent_parents"],
                    "source": row["source"],
                    "source_sha256": row["source_sha256"],
                }
            )
        for population in ("all_starts", "failed_starts"):
            if population == "failed_starts" and row["initial_success"]:
                continue
            for action in (
                ("all", "continue", "recover") if p["method"] == "DSRE" else ("all",)
            ):
                key = f"{task}|{operating}|{population}|{action}"
                arrays[key][gindex[task][row["group"]]] += score(
                    result, row, len(d["channels"]), action
                )
    metrics = {}
    memo = {}
    for key, array in sorted(arrays.items()):
        task = key.split("|")[0]
        cachekey = (task, hashlib.sha256(array.tobytes()).hexdigest())
        if cachekey not in memo:
            memo[cachekey] = summarize(array, weights[task])
        metrics[key] = memo[cachekey]
    save(root / "metrics.json", metrics)
    save(
        root / "strict_errors.json",
        {
            "errors": errors,
            "unique_checkpoint_ids": sorted({r["id"] for r in errors}),
            "interpretation": "Every observed error prevents a zero-error held-out strict-success claim for that operating point. Repeated selector/budget views are not independent failures.",
        },
    )
    np.savez_compressed(
        root / "group_counts.npz", **{f"a{i}": a for i, a in enumerate(arrays.values())}
    )
    save(root / "group_count_index.json", {"fields": FIELDS, "keys": list(arrays)})
    paired = {}
    for task in tasks:
        comparisons = set()
        for b in range(4):
            target = f"exact_coverage|{b}|DSRE"
            comparisons |= {
                (target, f"{s}|{b}|DSRE")
                for s in config["selectors"]
                if s != "exact_coverage"
            }
            comparisons |= {
                (target, f"exact_coverage|{b}|{m}")
                for m in (
                    "B7",
                    "B1_two_strict",
                    "S_then_B1_two",
                    "CART1_strict",
                    "CART2_strict",
                    "CART3_strict",
                    "CART2_beta10",
                )
            }
            if b:
                comparisons.add((target, "exact_coverage|0|DSRE"))
        for left, right in sorted(comparisons):
            a = arrays[f"{task}|{left}|all_starts|all"]
            b = arrays[f"{task}|{right}|all_starts|all"]
            sa, sb = weights[task] @ a, weights[task] @ b
            ca, cb = a.sum(axis=0), b.sum(axis=0)
            differences = {}
            for name in (
                "successful_strict_coverage",
                "coverage",
                "unacceptable_rate",
                "success_per_checkpoint",
                "mean_literals",
                "mean_added_channels",
            ):
                num, den = RATIOS[name]
                i, j = FIELDS.index(num), FIELDS.index(den)
                valid = (sa[:, j] > 0) & (sb[:, j] > 0)
                sparse = (
                    den == "recommended"
                    and min(int((a[:, 1] > 0).sum()), int((b[:, 1] > 0).sum())) < 10
                )
                distribution = sa[valid, i] / sa[valid, j] - sb[valid, i] / sb[valid, j]
                differences[name] = {
                    "value": float(ca[i] / ca[j] - cb[i] / cb[j])
                    if ca[j] and cb[j]
                    else None,
                    "parent_percentile95": np.quantile(
                        distribution, [0.025, 0.975]
                    ).tolist()
                    if valid.any() and not sparse
                    else None,
                }
            common = np.zeros((211, 3), dtype=np.int64)
            equal = 0
            for row in data:
                if row["task"] != task:
                    continue
                r, s = per_input[row["id"]][left], per_input[row["id"]][right]
                equal += r["action"] == s["action"] and r["evidence"] == s["evidence"]
                if r["action"] and s["action"]:
                    common[gindex[task][row["group"]]] += [
                        1,
                        len(r["evidence"]) - len(s["evidence"]),
                        int(r["action"] == s["action"]),
                    ]
            samples = weights[task] @ common
            valid = samples[:, 0] > 0
            count = int(common[:, 0].sum())
            paired[f"{task}|{left} minus {right}"] = {
                "differences": differences,
                "equal_action_evidence": int(equal),
                "common_recommended": count,
                "common_action_agreement": int(common[:, 2].sum()),
                "common_mean_literal_difference": float(common[:, 1].sum() / count)
                if count
                else None,
                "common_literal_parent95": np.quantile(
                    samples[valid, 1] / samples[valid, 0], [0.025, 0.975]
                ).tolist()
                if valid.any() and (common[:, 0] > 0).sum() >= 10
                else None,
            }
    save(root / "paired_comparisons.json", paired)
    stability = defaultdict(Counter)
    runtime = defaultdict(list)
    training = []
    for path in (root / "designs").glob("*.json"):
        d = load(path)
        for selected in d["selected_designs"]:
            stability[f"{d['task']}|{selected['selector']}|{selected['budget']}"][
                ",".join(map(str, selected["channels"]))
            ] += 1
    for path in (root / "models").glob("*.json"):
        m = load(path)
        training.append(
            {
                k: m[k]
                for k in (
                    "task",
                    "fold",
                    "selected",
                    "new_tree_fits",
                    "reused_trees",
                    "training_seconds",
                )
            }
        )
        for d in m["decisions"].values():
            runtime[f"{m['task']}|{d['method']}"].append(d["cold_ms"])
    save(root / "selection_stability.json", {k: dict(v) for k, v in stability.items()})
    save(
        root / "runtime.json",
        {
            "cold_queries": {
                k: {
                    "n": len(v),
                    "mean_ms": float(np.mean(v)),
                    "median_ms": float(np.median(v)),
                    "max_ms": max(v),
                }
                for k, v in runtime.items()
            },
            "training": training,
            "total_training_seconds": sum(r["training_seconds"] for r in training),
        },
    )
    save(
        root / "analysis_completed.json",
        {
            "status": "COMPLETE",
            "expanded_prediction_rows": expanded,
            "metric_cells": len(metrics),
            "paired_cells": len(paired),
            "unique_uncertainty_cells": len(memo),
            "strict_error_views": len(errors),
            "unique_strict_error_checkpoints": len({r["id"] for r in errors}),
        },
    )
    print(json.dumps(load(root / "analysis_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    analyze(args.root)
