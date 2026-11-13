"""Frozen existing-data observability and risk routing; reuse saved trees only."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from dsre_experiment import folds, reference_table, scope_for

from dual_rec.dsre.baselines import OutcomeRules, OutcomeTree
from dual_rec.dsre.calibration import zero_error_required
from dual_rec.dsre.observability import profile
from dual_rec.dsre.risk import RiskRules, TwoTierRouter
from dual_rec.dsre.schemas import Query


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def code_paths():
    return [
        Path("docs/DSRE_V11_METHOD_SPEC.md"),
        Path("config/dsre_v11.json"),
        Path("config/dsre_stage1.json"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        Path("scripts/dsre_v11_experiment.py"),
        Path("scripts/dsre_experiment.py"),
    ]


def freeze(root):
    config = load(Path("config/dsre_v11.json"))
    source = Path(config["input_root"])
    assert sha(source / "qualified_pairs.jsonl") == config["table_sha256"]
    manifest = {
        "status": "FROZEN_BEFORE_NEW_METHOD_NUMBERS",
        "source_sha256": {str(p): sha(p) for p in code_paths()},
        "input_sha256": {
            str(p): sha(p)
            for p in [
                source / "qualified_pairs.jsonl",
                source / "group_splits.json",
                source / "completion_manifest.json",
                source / "prospective_fresh_seed_plan.json",
                *sorted((source / "crossfit").glob("pose_proprioception*.model.json")),
            ]
        },
        "authority_sha256": sha(root / "authority.md"),
        "calibration": "NO_INDEPENDENT_COHORT_NOT_RUN",
    }
    save(root / "experiment_freeze.json", manifest)


def baseline_result(value, status="EMPIRICAL_BASELINE_UNCALIBRATED"):
    return {
        "action": value.action,
        "evidence": [f.model_dump(mode="json") for f in value.evidence],
        "support": value.support,
        "status": status if value.action else "INSUFFICIENT",
        "tier": None,
        "calibration": "UNASSESSED",
        "deployable_action": None,
    }


def run(root):
    config, old_config = (
        load(Path("config/dsre_v11.json")),
        load(Path("config/dsre_stage1.json")),
    )
    frozen = load(root / "experiment_freeze.json")
    for name, expected in (frozen["source_sha256"] | frozen["input_sha256"]).items():
        assert sha(Path(name)) == expected, name
    source = Path(config["input_root"])
    data, qualification = (
        jsonl(source / "qualified_pairs.jsonl"),
        load(source / "data_qualification.json"),
    )
    mapping = load(source / "group_splits.json")
    assert folds(data, old_config) == mapping
    variants = {
        "pose_proprioception": "features",
        "plus_privileged": "privileged_features",
        "coarse_geometry": "coarse_features",
    }
    observability = {}
    for variant in variants:
        for task in old_config["tasks"]:
            selected = [r for r in data if r["task"] == task]
            scope = scope_for(task, variant, qualification, old_config)
            table = reference_table(selected, scope, variant)
            observability[task + "/" + variant] = {
                "table": table.model_dump(mode="json"),
                **profile(table, config["minimum_support"]),
            }
    save(root / "observability.json", observability)
    directory = root / "crossfit"
    directory.mkdir(exist_ok=True)
    for task in old_config["tasks"]:
        for fold in range(5):
            name = task + "__fold" + str(fold)
            checkpoint = directory / (name + ".json")
            if checkpoint.exists():
                assert load(checkpoint)["freeze_sha256"] == sha(
                    root / "experiment_freeze.json"
                )
                continue
            model_path = (
                source / "crossfit" / ("pose_proprioception__" + name + ".model.json")
            )
            meta = load(model_path)
            train = [
                r for r in data if r["task"] == task and mapping[r["group"]] != fold
            ]
            evaluation = [
                r for r in data if r["task"] == task and mapping[r["group"]] == fold
            ]
            assert set(meta["reference_ids"]) == {r["id"] for r in train}
            assert set(meta["evaluation_ids"]) == {r["id"] for r in evaluation}
            assert not {r["group"] for r in train} & {r["group"] for r in evaluation}
            scope = scope_for(task, "pose_proprioception", qualification, old_config)
            table = reference_table(train, scope, "pose_proprioception")
            rules, risk = OutcomeRules(table, 2), RiskRules(table, 2)
            routers = {beta: TwoTierRouter(table, 2, beta) for beta in (0.1, 0.05)}
            trees = {}
            for depth in (1, 2, 3):
                tree = OutcomeTree.__new__(OutcomeTree)
                tree.rules, tree.root, tree.nodes = (
                    rules,
                    0,
                    meta["trees"]["B2_depth" + str(depth)],
                )
                trees["CART_depth" + str(depth)] = tree
            decisions, predictions = {}, []
            jobs = [
                ("S_strict", 0.0),
                ("B7_exact", 0.0),
                ("always_continue", None),
                ("always_recover", None),
            ]
            jobs += [("DSRE_v11", b) for b in (0.1, 0.05)]
            jobs += [
                (m, b)
                for b in config["descriptive_frontier_betas"]
                for m in ("B5_v11", "B1_two_v11", "full_signature", *trees)
            ]
            for row in evaluation:
                query = Query(scope=scope, features=tuple(row["features"]))
                for method, beta in jobs:
                    decision_id = hashlib.sha256(
                        json.dumps([method, beta, row["features"]]).encode()
                    ).hexdigest()[:24]
                    cached = decision_id in decisions
                    if not cached:
                        started = time.perf_counter_ns()
                        if method == "DSRE_v11":
                            result = (
                                routers[beta].predict(query).model_dump(mode="json")
                            )
                        elif method == "S_strict":
                            cert = routers[0.1].strict.solve(query)
                            result = baseline_result(
                                cert, "STRICT_FINITE_REFERENCE"
                            ) | {"certificate": cert.model_dump(mode="json")}
                        elif method == "B7_exact":
                            result = baseline_result(
                                rules.minimum(query, 1, exact=True),
                                "STRICT_FINITE_REFERENCE",
                            )
                        elif method in ("B5_v11", "B1_two_v11"):
                            decision = risk.select(
                                query, beta, 2 if method == "B1_two_v11" else None
                            )
                            result = baseline_result(decision) | {
                                "risk_rule": decision.model_dump(mode="json")
                            }
                        elif method == "full_signature":
                            result = baseline_result(rules.full(query, 1 - beta))
                        elif method in trees:
                            result = baseline_result(
                                trees[method].predict(query, 1 - beta)
                            )
                        else:
                            result = {
                                "action": method.removeprefix("always_"),
                                "evidence": [],
                                "support": len(train),
                                "tier": None,
                                "status": "BOUNDARY_CONTROL_UNCALIBRATED",
                                "calibration": "UNASSESSED",
                                "deployable_action": None,
                            }
                        latency = (time.perf_counter_ns() - started) / 1e6
                        decisions[decision_id] = {
                            "method": method,
                            "beta": beta,
                            "query": query.model_dump(mode="json"),
                            "result": result,
                            "cold_latency_ms": latency,
                        }
                    predictions.append(
                        {
                            "id": row["id"],
                            "group": row["group"],
                            "task": task,
                            "fold": fold,
                            "method": method,
                            "beta": beta,
                            "decision_id": decision_id,
                            "cache_hit": cached,
                        }
                    )
            save(
                checkpoint,
                {
                    "freeze_sha256": sha(root / "experiment_freeze.json"),
                    "model_sha256": sha(model_path),
                    "task": task,
                    "fold": fold,
                    "table": table.model_dump(mode="json"),
                    "reference_groups": sorted({r["group"] for r in train}),
                    "evaluation_groups": sorted({r["group"] for r in evaluation}),
                    "decisions": decisions,
                    "predictions": predictions,
                    "router_definition_sha256": hashlib.sha256(
                        json.dumps(
                            {"table": table.model_dump(mode="json"), "freeze": frozen},
                            sort_keys=True,
                        ).encode()
                    ).hexdigest(),
                    "new_model_fits": 0,
                },
            )
            save(
                root / "progress.json",
                {
                    "completed_folds": [p.name for p in directory.glob("*.json")],
                    "expected_folds": 10,
                },
            )
            print(
                json.dumps(
                    {
                        "completed": name,
                        "prediction_rows": len(predictions),
                        "cold_queries": len(decisions),
                    }
                ),
                flush=True,
            )
    full = {}
    for task in old_config["tasks"]:
        table = reference_table(
            [r for r in data if r["task"] == task],
            scope_for(task, "pose_proprioception", qualification, old_config),
            "pose_proprioception",
        )
        router = TwoTierRouter(table, 2, 0.1)
        signatures = sorted({r.features for r in table.rows}, key=str)
        full[task] = {
            "table_sha256": hashlib.sha256(
                table.model_dump_json().encode()
            ).hexdigest(),
            "beta": 0.1,
            "outputs": [
                {
                    "signature": x,
                    "result": router.predict(
                        Query(scope=table.scope, features=x)
                    ).model_dump(mode="json"),
                }
                for x in signatures
            ],
            "calibration": "PROPOSED_FROZEN_ROUTER_NO_INDEPENDENT_CALIBRATION",
            "deployment_enabled": False,
        }
    save(root / "full_table_router.json", full)
    save(
        root / "experiment_completed.json",
        {
            "status": "COMPLETE",
            "folds": 10,
            "new_model_fits": 0,
            "reused_trees": 30,
            "observability_profiles": len(observability),
            "pairs": len(data),
            "zero_error_required": zero_error_required(0.1, 0.05 / 4),
            "physics": 0,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.freeze:
        if (args.root / "experiment_freeze.json").exists():
            raise SystemExit("Freeze exists; do not overwrite")
        freeze(args.root)
    else:
        run(args.root)
