"""Fit on development only, then evaluate the sealed D5-D7 qualification cohort."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.passive import (
    clustered_metric_intervals,
    mean_interval,
    metrics,
    predict,
    select_model,
    squared_distances,
    wilson,
)
from dual_rec.scenarios import FailureScenario, history_features, split_seeds


def read_jsonl(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def load_cohort(root: Path, split: str, config: dict):
    cases, outcomes = {}, []
    for folder in sorted(root.glob(split + "-*")):
        if not folder.is_dir():
            continue
        status = json.loads((folder / "status.json").read_text())
        if status["status"] != "completed":
            raise RuntimeError(f"Incomplete worker: {folder}")
        with gzip.open(folder / "scenarios.jsonl.gz", "rt", encoding="utf8") as stream:
            for line in stream:
                scenario = FailureScenario.model_validate_json(line)
                key = scenario.scenario_id
                if key in cases:
                    raise ValueError("Duplicate independent scenario")
                cases[key] = {
                    "id": key,
                    "seed": scenario.recipe.seed,
                    "condition": scenario.recipe.evaluation_only_fault.name,
                    "failed": scenario.failure_trigger["failed"],
                    "trigger": scenario.failure_trigger,
                    "features": history_features(scenario.history),
                    "last": scenario.history[-1].observation.model_dump(),
                    "edit": scenario.recipe.physical_edits[0].model_dump(),
                }
        outcomes += read_jsonl(folder / "outcomes.jsonl")
    expected = {
        (seed, c["name"])
        for seed in config[split + "_seeds"]
        for c in config["conditions"]
    }
    if {(r["seed"], r["condition"]) for r in cases.values()} != expected or len(
        cases
    ) != len(expected):
        raise ValueError("Missing or substituted preregistered seed/condition")
    expected_outcomes = {
        (seed, condition, recovery)
        for seed, condition in expected
        for recovery in config["recoveries"]
    }
    keys = [(r["seed"], r["condition"], r["recovery"]) for r in outcomes]
    if set(keys) != expected_outcomes or len(keys) != len(set(keys)):
        raise ValueError("Incomplete/duplicate recovery matrix")
    return cases, outcomes


def family_arrays(cases, conditions, failed_only=False):
    by_key = {(row["seed"], row["condition"]): row for row in cases.values()}
    seeds = sorted({seed for seed, condition in by_key if condition in conditions})
    if failed_only:
        seeds = [
            seed for seed in seeds if all(by_key[seed, c]["failed"] for c in conditions)
        ]
    rows = [by_key[seed, c] for seed in seeds for c in conditions]
    if not rows:
        return rows, None, None, None
    return (
        rows,
        np.stack([r["features"] for r in rows]),
        np.tile([0, 1], len(seeds)),
        np.repeat(seeds, 2),
    )


def fit(root, output, config):
    if any(folder.is_dir() for folder in root.glob("qualification-*")):
        raise RuntimeError(
            "Qualification data already exists; refuse new development model selection"
        )
    cases, _ = load_cohort(root, "development", config)
    output.mkdir(exist_ok=False)
    payload = {
        "config_sha256": hashlib.sha256(
            Path("config/gate_d5_d7.json").read_bytes()
        ).hexdigest(),
        "families": {},
        "development_ids": sorted(cases),
        "qualification_seeds_unopened": config["qualification_seeds"],
    }
    for family in config["families"]:
        result = {}
        for cohort in ["full", "matched_failures"]:
            rows, x, y, groups = family_arrays(
                cases, family["conditions"], cohort == "matched_failures"
            )
            if not rows or len(np.unique(groups)) < 4:
                result[cohort] = {
                    "status": "not_fit",
                    "reason": "fewer than four matched failed development seeds",
                }
                continue
            models = {}
            for mode in config["classifier_models"]:
                model, cv = select_model(
                    x, y, groups, mode, config["classifier_regularization"]
                )
                models[mode] = {
                    "model": model,
                    "cross_validation": cv,
                    "train_seed_groups": sorted(set(groups.tolist())),
                }
                print(
                    f"fit {family['name']}/{cohort}/{mode}: lambda={model['regularization']}",
                    flush=True,
                )
            result[cohort] = {
                "status": "fitted",
                "models": models,
                "case_ids": [r["id"] for r in rows],
            }
        payload["families"][family["name"]] = result
    with gzip.open(output / "models.json.gz", "xt", encoding="utf8") as stream:
        json.dump(payload, stream, allow_nan=False)
    metadata = {
        name: {
            cohort: (
                {
                    "status": value["status"],
                    "regularization": {
                        mode: info["model"]["regularization"]
                        for mode, info in value["models"].items()
                    },
                }
                if value["status"] == "fitted"
                else value
            )
            for cohort, value in result.items()
        }
        for name, result in payload["families"].items()
    }
    (output / "fit_plan.json").write_text(
        json.dumps(
            {
                "config_sha256": payload["config_sha256"],
                "development_ids": payload["development_ids"],
                "qualification_seeds_unopened": payload["qualification_seeds_unopened"],
                "models_sha256": hashlib.sha256(
                    (output / "models.json.gz").read_bytes()
                ).hexdigest(),
                "selected": metadata,
            },
            indent=2,
        )
    )


def matrix(outcomes, cases, config):
    result = {}
    for condition in [c["name"] for c in config["conditions"]]:
        result[condition] = {}
        for recovery in config["recoveries"]:
            selected = sorted(
                [
                    r
                    for r in outcomes
                    if r["condition"] == condition and r["recovery"] == recovery
                ],
                key=lambda r: r["seed"],
            )
            stats = {}
            for cohort in ["all_setups", "registered_failures"]:
                rows = (
                    selected
                    if cohort == "all_setups"
                    else [r for r in selected if r["failure_trigger"]["failed"]]
                )
                stats[cohort] = {
                    "independent_seeds": len(rows),
                    "successes": sum(r["success"] for r in rows),
                    "success_rate": float(np.mean([r["success"] for r in rows]))
                    if rows
                    else None,
                    "success_wilson_95": wilson(
                        sum(r["success"] for r in rows), len(rows)
                    ),
                    "utility": mean_interval(
                        [r["utility"] for r in rows],
                        config["bootstrap_repetitions"],
                        config["analysis_seed"],
                    ),
                }
            result[condition][recovery] = stats
    return result


def evaluate(root, fitted, output, config):
    output.mkdir(exist_ok=False)
    development, dev_outcomes = load_cohort(root, "development", config)
    qualification, outcomes = load_cohort(root, "qualification", config)
    with gzip.open(fitted / "models.json.gz", "rt", encoding="utf8") as stream:
        payload = json.load(stream)
    assert (
        payload["config_sha256"]
        == hashlib.sha256(Path("config/gate_d5_d7.json").read_bytes()).hexdigest()
    )
    assert set(payload["development_ids"]) == set(development)
    assert not {r["seed"] for r in development.values()} & {
        r["seed"] for r in qualification.values()
    }
    report = {
        "development_matrix": matrix(dev_outcomes, development, config),
        "qualification_matrix": matrix(outcomes, qualification, config),
        "qualification_failure_counts": {
            c["name"]: sum(
                r["failed"]
                for r in qualification.values()
                if r["condition"] == c["name"]
            )
            for c in config["conditions"]
        },
        "families": {},
        "independent_seeds_per_condition": {"development": 16, "qualification": 8},
        "no_snapshot_branches": True,
    }
    predictions = []
    by_outcome = {(r["seed"], r["condition"], r["recovery"]): r for r in outcomes}
    for family in config["families"]:
        name, conditions = family["name"], family["conditions"]
        full_rows, test_x, _test_y, _test_groups = family_arrays(
            qualification, conditions
        )
        train_rows, train_x, _, _ = family_arrays(development, conditions)
        full_fit = payload["families"][name]["full"]["models"]
        diagnostic = {}
        probabilities = {}
        for cohort in ["full", "matched_failures"]:
            rows, x, y, groups = family_arrays(
                qualification, conditions, cohort == "matched_failures"
            )
            cohort_fit = payload["families"][name][cohort]
            if not rows or cohort_fit["status"] != "fitted":
                diagnostic[cohort] = {
                    "status": "not_evaluated",
                    "reason": "insufficient matched failed development/qualification groups",
                    "qualification_independent_groups": 0
                    if not rows
                    else len(np.unique(groups)),
                }
                continue
            results = {}
            for mode, info in cohort_fit["models"].items():
                p = predict(info["model"], x)
                results[mode] = {
                    "metrics": metrics(y, p),
                    "clustered_95_intervals": clustered_metric_intervals(
                        y,
                        p,
                        groups,
                        config["bootstrap_repetitions"],
                        config["analysis_seed"],
                    ),
                    "qualification_groups": len(np.unique(groups)),
                    "regularization": info["model"]["regularization"],
                    "training_groups": info["train_seed_groups"],
                }
                for row, label, probability in zip(rows, y, p, strict=True):
                    predictions.append(
                        {
                            "family": name,
                            "cohort": cohort,
                            "model": mode,
                            "scenario_id": row["id"],
                            "base_seed": row["seed"],
                            "condition": row["condition"],
                            "target_label": int(label),
                            "probability_second_condition": float(probability),
                            "feature_sha256": hashlib.sha256(
                                row["features"].tobytes()
                            ).hexdigest(),
                        }
                    )
                if cohort == "full":
                    probabilities[mode] = p
            diagnostic[cohort] = {"status": "evaluated", "models": results}
        scaler = full_fit["logistic"]["model"]
        mean, scale = np.asarray(scaler["mean"]), np.asarray(scaler["scale"])
        standardized = (train_x - mean) / scale
        within = squared_distances(standardized, standardized)
        # Interleaved rows have balanced labels. Restrict nearest neighbors to
        # the same condition and exclude each sample itself.
        labels = np.tile([0, 1], len(train_rows) // 2)
        within[labels[:, None] != labels[None, :]] = np.inf
        np.fill_diagonal(within, np.inf)
        within_nearest = np.sqrt(within.min(1) / standardized.shape[1])
        threshold = float(np.quantile(within_nearest, 0.95))
        test_standardized = (test_x - mean) / scale
        distances = np.sqrt(
            np.mean((test_standardized[::2] - test_standardized[1::2]) ** 2, axis=1)
        )
        matched_failed = [
            index
            for index in range(len(full_rows) // 2)
            if all(full_rows[2 * index + j]["failed"] for j in range(2))
        ]
        matched_seeds = [full_rows[2 * index]["seed"] for index in matched_failed]
        ambiguous = []
        physical = []
        for index in range(len(full_rows) // 2):
            row_a, row_b = full_rows[2 * index : 2 * index + 2]
            uncertain = all(
                np.all(
                    (p[2 * index : 2 * index + 2] >= 0.25)
                    & (p[2 * index : 2 * index + 2] <= 0.75)
                )
                for p in probabilities.values()
            )
            overlap = bool(distances[index] <= threshold)
            if index in matched_failed and uncertain and overlap:
                ambiguous.append(row_a["seed"])
            a, b = row_a["last"], row_b["last"]
            physical.append(
                {
                    "seed": row_a["seed"],
                    "both_failed": index in matched_failed,
                    "standardized_history_rms": float(distances[index]),
                    "neighborhood_overlap": overlap,
                    "both_models_uncertain": bool(uncertain),
                    "cube_position_difference_m": float(
                        np.linalg.norm(
                            np.asarray(a["task_state"]["extra"]["obj_pose"][0][:3])
                            - np.asarray(b["task_state"]["extra"]["obj_pose"][0][:3])
                        )
                    ),
                    "cube_velocity_max_difference": float(
                        np.max(
                            np.abs(
                                np.asarray(a["cube_velocity"])
                                - np.asarray(b["cube_velocity"])
                            )
                        )
                    ),
                    "joint_wrench_max_difference": float(
                        np.max(
                            np.abs(
                                np.asarray(a["link_wrenches"])
                                - np.asarray(b["link_wrenches"])
                            )
                        )
                    ),
                }
            )
        contrasts = {
            condition: [
                by_outcome[seed, condition, "continue"]["utility"]
                - by_outcome[seed, condition, "recontact"]["utility"]
                for seed in matched_seeds
            ]
            for condition in conditions
        }
        directional = {
            condition: mean_interval(
                values,
                config["bootstrap_repetitions"],
                config["analysis_seed"],
                confidence=0.9875,
            )
            for condition, values in contrasts.items()
        }
        disagreement, meaningful_disagreement, common_regret = [], [], []
        per_seed = []
        for seed in matched_seeds:
            values = np.array(
                [
                    [by_outcome[seed, c, r]["utility"] for r in config["recoveries"]]
                    for c in conditions
                ]
            )
            best = values.argmax(1)
            different = bool(best[0] != best[1])
            cross_regret = [
                float(values[0, best[0]] - values[0, best[1]]),
                float(values[1, best[1]] - values[1, best[0]]),
            ]
            meaningful = different and min(cross_regret) >= config["preference_margin"]
            disagreement.append(different)
            meaningful_disagreement.append(meaningful)
            regret = float(values.max(1).mean() - values.mean(0).max())
            common_regret.append(regret)
            per_seed.append(
                {
                    "seed": seed,
                    "best_recoveries": [config["recoveries"][i] for i in best],
                    "cross_regret": cross_regret,
                    "best_common_recovery_regret": regret,
                }
            )
        interval_values = list(directional.values())
        reversal = False
        if all(value is not None for value in interval_values):
            first, second = interval_values
            margin = config["preference_margin"]
            reversal = bool(
                (
                    first["mean"] >= margin
                    and second["mean"] <= -margin
                    and first["ci"][0] > 0
                    and second["ci"][1] < 0
                )
                or (
                    second["mean"] >= margin
                    and first["mean"] <= -margin
                    and second["ci"][0] > 0
                    and first["ci"][1] < 0
                )
            )
        ambiguous_fraction = (
            len(ambiguous) / len(matched_seeds) if matched_seeds else None
        )
        failure_counts = [report["qualification_failure_counts"][c] for c in conditions]
        overlap_pass = (
            bool(
                len(ambiguous) >= 4
                and ambiguous_fraction >= config["minimum_ambiguous_fraction"]
            )
            if matched_seeds
            else False
        )
        if family["negative_control"]:
            status = "CONTROL"
            reason = "Measured recovery equivalence control; no H1 claim"
        elif min(failure_counts) < len(config["qualification_seeds"]) * 0.25:
            status = "NO-GO"
            reason = "At least one registered mechanism did not produce qualifying failures in 25% of qualification setups"
        elif len(matched_seeds) < config["minimum_matched_failure_test_seeds"]:
            status = "INCONCLUSIVE"
            reason = "Too few matched failed qualification seed groups"
        elif reversal and overlap_pass:
            status = "GO"
            reason = "All preregistered H1 screening criteria passed"
        elif all(
            all(
                report["qualification_matrix"][c][r]["registered_failures"][
                    "success_rate"
                ]
                == 1
                for c in conditions
            )
            for r in ["continue"]
        ):
            status = "NO-GO"
            reason = "A common direct recovery succeeds across both failed mechanisms"
        else:
            status = "INCONCLUSIVE"
            reason = "Recovery conflict and nontrivial passive ambiguity not jointly established"
        effective = {
            c: [
                r
                for r in config["recoveries"]
                if report["qualification_matrix"][c][r]["all_setups"]["utility"]["mean"]
                >= max(
                    report["qualification_matrix"][c][other]["all_setups"]["utility"][
                        "mean"
                    ]
                    for other in config["recoveries"]
                )
                - config["preference_margin"]
            ]
            for c in conditions
        }
        report["families"][name] = {
            "status": status,
            "reason": reason,
            "conditions": conditions,
            "passive_diagnostics": diagnostic,
            "overlap": {
                "within_class_development_nearest_rms_p95": threshold,
                "qualification_pairs": physical,
                "ambiguous_failed_seeds": ambiguous,
                "ambiguous_failed_fraction": ambiguous_fraction,
            },
            "matched_failed_qualification_seeds": matched_seeds,
            "primary_continue_minus_recontact": directional,
            "preference_reversal_supported": reversal,
            "best_recovery_disagreement": mean_interval(
                disagreement, config["bootstrap_repetitions"], config["analysis_seed"]
            ),
            "meaningful_disagreement_fraction": mean_interval(
                meaningful_disagreement,
                config["bootstrap_repetitions"],
                config["analysis_seed"],
            ),
            "common_recovery_regret": mean_interval(
                common_regret, config["bootstrap_repetitions"], config["analysis_seed"]
            ),
            "per_matched_failure_seed": per_seed,
            "common_effective_recoveries_all_setups": sorted(
                set(effective[conditions[0]]) & set(effective[conditions[1]])
            ),
        }
    statuses = [
        report["families"][family["name"]]["status"]
        for family in config["families"]
        if not family["negative_control"]
    ]
    report["status"] = (
        "GO"
        if "GO" in statuses
        else ("INCONCLUSIVE" if "INCONCLUSIVE" in statuses else "NO-GO")
    )
    report["STOPPED_AT_D7"] = True
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    with (output / "predictions.jsonl").open("x") as stream:
        for row in predictions:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "qualification_failure_counts": report["qualification_failure_counts"],
                "families": {
                    k: {
                        "status": v["status"],
                        "matched_failures": len(
                            v["matched_failed_qualification_seeds"]
                        ),
                        "reversal": v["preference_reversal_supported"],
                    }
                    for k, v in report["families"].items()
                },
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fit", "evaluate"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fitted", type=Path)
    args = parser.parse_args()
    config = json.loads(Path("config/gate_d5_d7.json").read_text())
    split_seeds(config)
    if args.stage == "fit":
        fit(args.root, args.output, config)
    else:
        if args.fitted is None:
            parser.error("--fitted is required for evaluation")
        evaluate(args.root, args.fitted, args.output, config)


if __name__ == "__main__":
    main()
