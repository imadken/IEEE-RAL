"""Checkpointed same-information development cross-fitting and fixed frontiers."""

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from dual_rec.dsre.baselines import OutcomeRules, OutcomeTree
from dual_rec.dsre.data import digest
from dual_rec.dsre.features import PRIMARY, PRIVILEGED
from dual_rec.dsre.schemas import (
    Outcomes,
    Query,
    Recommendation,
    ReferenceRow,
    ReferenceTable,
    Scope,
)
from dual_rec.dsre.solver import FiniteIndex


def load(path):
    return json.loads(path.read_text())


def protocol_path():
    original = Path("DSRE_STAGE1_PROTOCOL.md")
    return original if original.is_file() else Path("docs") / original.name


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def values(row, variant, query=False):
    if variant == "plus_privileged":
        return tuple(row["privileged_features"])
    if variant == "coarse_geometry":
        return tuple(row["coarse_features"])
    result = list(row["features"])
    for i in {"without_history": (2, 3), "without_goal_channel": (0, 2)}.get(
        variant, ()
    ):
        result[i] = None
    if variant == "query_channel_missing" and query:
        result[int(hashlib.sha256(row["id"].encode()).hexdigest(), 16) % 6] = None
    return tuple(result)


def scope_for(task, variant, manifest, config):
    return Scope(
        task=task,
        controller_sha256=manifest["controller_identity"],
        horizon_steps=config["horizon_steps"],
        horizon_seconds=config["horizon_seconds"],
        epsilon=config["epsilon"],
        features=PRIMARY + PRIVILEGED if variant == "plus_privileged" else PRIMARY,
        channels=variant,
    )


def reference_table(source, scope, variant):
    return ReferenceTable(
        scope=scope,
        rows=tuple(
            ReferenceRow(
                id=r["id"],
                features=values(r, variant),
                outcomes=Outcomes.model_validate(r["outcomes"]),
            )
            for r in source
        ),
    )


def folds(source, config):
    mapping = {}
    for task in config["tasks"]:
        groups = sorted(
            {r["group"] for r in source if r["task"] == task},
            key=lambda group: hashlib.sha256(
                (config["fold_salt"] + group).encode()
            ).hexdigest(),
        )
        for index, group in enumerate(groups):
            mapping[group] = index % config["folds"]
    return mapping


class FittedMethods:
    def __init__(self, table, minimum_support):
        self.exact = FiniteIndex(table, minimum_support)
        self.rules = OutcomeRules(table, minimum_support)
        self.trees = {
            "B2_depth" + str(d): OutcomeTree(self.rules, d) for d in (1, 2, 3)
        }
        self.trees["B2_pruned"] = OutcomeTree(self.rules, 3, 0.01)
        self.cache = {}
        self.certificates = {}
        self.times = []

    def predict(self, method, query, target=None):
        key = (method, query.features, target)
        if key in self.cache:
            return self.cache[key], True
        started = time.perf_counter_ns()
        if method in {"DSRE", "B6_greedy"}:
            certificate = (
                self.exact.solve(query)
                if method == "DSRE"
                else self.exact.greedy(query)
            )
            result = Recommendation(
                method=method,
                action=certificate.action,
                evidence=certificate.evidence,
                support=certificate.support,
                reason="TABLE_SUFFICIENT_UNCALIBRATED"
                if certificate.action
                else "+".join(certificate.reasons),
            )
            cert_id = hashlib.sha256(
                json.dumps([method, query.features]).encode()
            ).hexdigest()[:20]
            self.certificates[cert_id] = {
                "query": query.model_dump(mode="json"),
                "certificate": certificate.model_dump(mode="json"),
                "method": method,
            }
        elif method.startswith("B0_"):
            result = Recommendation(
                method=method,
                action=method.removeprefix("B0_"),
                evidence=(),
                support=len(self.rules.rows),
                reason="UNCONDITIONAL_BOUNDARY_CONTROL",
            )
        elif method in {"B1_one", "B1_two"}:
            result = self.rules.minimum(
                query, target, 1 if method == "B1_one" else 2, method
            )
        elif method.startswith("B2_"):
            result = self.trees[method].predict(query, target, method)
        elif method == "B3_full":
            result = self.rules.full(query, target)
        elif method == "B4_policy":
            result = self.rules.policy(query, 0.5)
        elif method == "B5_mean":
            result = self.rules.minimum(query, target, method=method)
        elif method == "B7_exact_rule":
            result = self.rules.minimum(query, 1, method=method, exact=True)
        else:
            raise ValueError("Unregistered method: " + method)
        elapsed = (time.perf_counter_ns() - started) / 1e6
        self.times.append(
            {
                "method": method,
                "target": target,
                "latency_ms": elapsed,
                "query_features": query.features,
            }
        )
        self.cache[key] = result.model_dump(mode="json")
        return self.cache[key], False


def run(root):
    config = load(Path("config/dsre_stage1.json"))
    manifest = load(root / "data_qualification.json")
    assert manifest["status"] == "PASS"
    source = rows(root / "qualified_pairs.jsonl")
    assert digest(root / "qualified_pairs.jsonl") == manifest["table_sha256"]
    grouping = folds(source, config)
    split_path = root / "group_splits.json"
    if split_path.exists():
        assert load(split_path) == grouping
    else:
        save(split_path, grouping)
    frozen_paths = [
        Path("config/dsre_stage1.json"),
        protocol_path(),
        Path("scripts/dsre_analyze.py"),
        root / "analysis_plan.json",
        Path(__file__),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
    ]
    freeze = {
        "source_sha256": {str(p): digest(p) for p in frozen_paths},
        "table_sha256": digest(root / "qualified_pairs.jsonl"),
        "split_sha256": digest(split_path),
        "status": "FROZEN_BEFORE_METHOD_NUMBERS",
        "calibration": "UNASSESSED_REUSED_DEVELOPMENT_ONLY",
    }
    freeze_path = root / "experiment_freeze.json"
    if freeze_path.exists():
        assert load(freeze_path) == freeze, (
            "Method code/specification changed; preserve the old attempt before rerunning"
        )
    else:
        save(freeze_path, freeze)
    target_methods = [
        "B1_one",
        "B1_two",
        "B2_depth1",
        "B2_depth2",
        "B2_depth3",
        "B2_pruned",
        "B3_full",
        "B5_mean",
    ]
    completed, fit_count, emitted = [], 0, Counter()
    directory = root / "crossfit"
    directory.mkdir(exist_ok=True)
    for variant in config["feature_variants"]:
        for task in config["tasks"]:
            scope = scope_for(task, variant, manifest, config)
            for fold in range(config["folds"]):
                name = f"{variant}__{task}__fold{fold}"
                output, meta = (
                    directory / (name + ".jsonl"),
                    directory / (name + ".model.json"),
                )
                if output.exists() and meta.exists():
                    info = load(meta)
                    assert digest(output) == info["prediction_sha256"]
                    assert info["experiment_freeze"] == digest(freeze_path)
                    completed.append(name)
                    continue
                training = [
                    r
                    for r in source
                    if r["task"] == task and grouping[r["group"]] != fold
                ]
                evaluation = [
                    r
                    for r in source
                    if r["task"] == task and grouping[r["group"]] == fold
                ]
                assert not {r["group"] for r in training} & {
                    r["group"] for r in evaluation
                }
                table = reference_table(training, scope, variant)
                started = time.perf_counter()
                fitted = FittedMethods(table, config["minimum_support"])
                fit_ms = (time.perf_counter() - started) * 1000
                fit_count += 4
                temporary = output.with_suffix(".partial")
                if temporary.exists():
                    temporary.rename(
                        temporary.with_suffix(f".interrupted-{time.time_ns()}")
                    )
                with temporary.open("x") as stream:
                    for row in evaluation:
                        query = Query(scope=scope, features=values(row, variant, True))
                        jobs = [
                            (
                                method,
                                "primary",
                                0.5
                                if method == "B3_full"
                                else 0.9
                                if method in target_methods
                                else None,
                            )
                            for method in config["methods"]
                        ]
                        jobs += [
                            (method, f"mean_{target:g}", target)
                            for method in target_methods
                            for target in config["mean_utility_targets"]
                        ]
                        for method, point, target in jobs:
                            result, cached = fitted.predict(method, query, target)
                            stream.write(
                                json.dumps(
                                    {
                                        "id": row["id"],
                                        "group": row["group"],
                                        "task": task,
                                        "fold": fold,
                                        "variant": variant,
                                        "point": point,
                                        "target": target,
                                        "method": method,
                                        "query_features": query.features,
                                        "recommendation": result,
                                        "prediction_cache_hit": cached,
                                    },
                                    allow_nan=False,
                                )
                                + "\n"
                            )
                            emitted[variant + "/" + point] += 1
                temporary.rename(output)
                certificates_path = directory / (name + ".certificates.json")
                save(certificates_path, fitted.certificates)
                save(
                    meta,
                    {
                        "scope": scope.model_dump(mode="json"),
                        "minimum_support": config["minimum_support"],
                        "reference_ids": [r["id"] for r in training],
                        "evaluation_ids": [r["id"] for r in evaluation],
                        "reference_groups": sorted({r["group"] for r in training}),
                        "evaluation_groups": sorted({r["group"] for r in evaluation}),
                        "trees": {m: t.nodes for m, t in fitted.trees.items()},
                        "fit_ms": fit_ms,
                        "uncached_prediction_latencies": fitted.times,
                        "prediction_sha256": digest(output),
                        "certificates_sha256": digest(certificates_path),
                        "experiment_freeze": digest(freeze_path),
                        "tree_training_targets": "four-category paired outcome distribution",
                    },
                )
                completed.append(name)
                save(
                    root / "experiment_progress.json",
                    {
                        "completed_folds": completed,
                        "expected_folds": len(config["feature_variants"])
                        * len(config["tasks"])
                        * config["folds"],
                        "tree_fits_this_invocation": fit_count,
                        "emitted_this_invocation": dict(emitted),
                    },
                )
                print(
                    json.dumps(
                        {
                            "completed_folds": len(completed),
                            "name": name,
                            "fit_ms": fit_ms,
                        }
                    ),
                    flush=True,
                )
    full = []
    for variant in ("pose_proprioception", "plus_privileged"):
        for task in config["tasks"]:
            population = [r for r in source if r["task"] == task]
            scope = scope_for(task, variant, manifest, config)
            table = reference_table(population, scope, variant)
            unique = sorted({values(r, variant) for r in population}, key=str)
            for minimum in [config["minimum_support"], *config["support_sensitivity"]]:
                solver = FiniteIndex(table, minimum)
                for x in unique:
                    query = Query(scope=scope, features=x)
                    exact, greedy = solver.solve(query), solver.greedy(query)
                    full.append(
                        {
                            "task": task,
                            "variant": variant,
                            "minimum_support": minimum,
                            "query": query.model_dump(mode="json"),
                            "matching_input_ids": [
                                r["id"] for r in population if values(r, variant) == x
                            ],
                            "certificate": exact.model_dump(mode="json"),
                            "greedy": greedy.model_dump(mode="json"),
                            "calibration": "UNASSESSED_DEVELOPMENT_FULL_TABLE",
                        }
                    )
    save(root / "full_table_certificates.json", full)
    save(
        root / "experiment_completed.json",
        {
            "status": "COMPLETE",
            "fold_models": len(completed),
            "trained_four_category_trees": 4 * len(completed),
            "source_pairs": len(source),
            "new_physical_rollouts": 0,
            "calibration": "NOT_RUN_INDEPENDENT_COHORT_ABSENT",
            "full_table_certificates": len(full),
        },
    )
    print(json.dumps(load(root / "experiment_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    run(args.root)
