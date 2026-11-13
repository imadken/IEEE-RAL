"""Training-only fixed instrumentation selection and grouped recovery evaluation."""

import argparse
import hashlib
import json
import time
from itertools import combinations
from pathlib import Path

from dual_rec.dsre.baselines import OutcomeTree
from dual_rec.dsre.features import PRIMARY, PRIVILEGED
from dual_rec.dsre.repair import (
    ParentIndex,
    ParentRules,
    RepairQuery,
    RepairScope,
    RepairTable,
)
from dual_rec.dsre.repair_selection import (
    OPTIONAL,
    ceiling_mass,
    profile,
    select_channels,
    values,
)
from dual_rec.dsre.schemas import Outcomes, ReferenceRow


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def table_for(source, selected, scope_template, privileged=False):
    scope = RepairScope.model_validate(
        scope_template
        | {
            "features": PRIMARY
            + tuple(OPTIONAL[i] for i in selected)
            + (PRIVILEGED if privileged else ()),
            "channels": "repair:"
            + ",".join(map(str, selected))
            + ("/privileged" if privileged else ""),
        }
    )
    table = RepairTable(
        scope=scope,
        rows=tuple(
            ReferenceRow(
                id=r["id"],
                features=values(r, selected, privileged),
                outcomes=Outcomes.model_validate(r["outcomes"]),
            )
            for r in source
        ),
    )
    return table, {r["id"]: r["group"] for r in source}


def freeze(root):
    assert load(root / "feature_qualification.json")["status"] == "PASS"
    config = load(Path("config/dsre_evidence_repair.json"))
    old = Path(config["input_root"])
    method = Path("docs/DSRE_STAGE1_EVIDENCE_REPAIR_METHOD.md")
    (root / "registered_method.md").write_bytes(method.read_bytes())
    paths = [
        Path("config/dsre_evidence_repair.json"),
        Path("scripts/dsre_repair_experiment.py"),
        Path("scripts/dsre_repair_prepare.py"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
    ]
    inputs = [
        root / "qualified_pairs.jsonl",
        root / "registered_method.md",
        root / "authority.txt",
        old / "group_splits.json",
        old / "completion_manifest.json",
        Path(config["prior_v11_root"]) / "completion_manifest.json",
    ]
    inputs += sorted((old / "crossfit").glob("pose_proprioception*.model.json"))
    save(
        root / "experiment_freeze.json",
        {
            "status": "FROZEN_BEFORE_NEW_METHOD_COMPARISONS",
            "source_sha256": {str(p): sha(p) for p in paths},
            "input_sha256": {str(p): sha(p) for p in inputs},
            "evaluation": "exploratory grouped development cross-fit",
        },
    )


def compact(result, status=None, independent_parents=None):
    if hasattr(result, "model_dump"):
        result = result.model_dump(mode="json")
    return {
        "action": result["action"],
        "evidence": result["evidence"],
        "support": result["support"],
        "independent_parents": independent_parents
        if independent_parents is not None
        else result.get("independent_parents", 0),
        "status": status or result["status"],
        "deployable_action": None,
        "calibration": "UNASSESSED",
    }


def predict(method, query, index, rules, trees, strict=None):
    if method.startswith("B0_"):
        return {
            "action": method.removeprefix("B0_"),
            "evidence": [],
            "support": len(rules.rows),
            "independent_parents": rules.parent_count(rules.rows),
            "status": "PROVISIONAL_UNCALIBRATED",
            "deployable_action": None,
            "calibration": "UNASSESSED",
        }
    if method == "DSRE":
        output = index.diagnose(query)
        return compact(output) | {"diagnosis": output.model_dump(mode="json")}
    if method == "S_then_B1_two":
        if strict["action"]:
            return {k: v for k, v in strict.items() if k != "diagnosis"}
        r = rules.select(query, 0.1, 2)
    elif method in ("B7", "B1_one_strict", "B1_two_strict", "B5_beta10"):
        r = rules.select(
            query,
            0.1 if method == "B5_beta10" else 0,
            1
            if method == "B1_one_strict"
            else 2
            if method == "B1_two_strict"
            else None,
        )
    else:
        tree = trees[method[4]]
        r = tree.predict(query, 0.9 if method.endswith("beta10") else 1)
        selected = [table_feature.feature for table_feature in r.evidence]
        indices = [rules.table.scope.features.index(f) for f in selected]
        matched = rules.match(query, indices) if r.action else []
        parent_count = rules.parent_count(matched)
        if r.action and parent_count < 2:
            return {
                "action": None,
                "evidence": [],
                "support": 0,
                "independent_parents": parent_count,
                "status": "REFERENCE_INSUFFICIENT",
                "deployable_action": None,
                "calibration": "UNASSESSED",
            }
        return compact(
            r,
            status=(
                "PROVISIONAL_UNCALIBRATED"
                if method.endswith("beta10")
                else "STRICT_FINITE_REFERENCE"
            )
            if r.action
            else "INSUFFICIENT",
            independent_parents=parent_count,
        )
    matched_ids = set(r.matched_ids)
    matched = [row for row in rules.rows if row.id in matched_ids]
    return compact(
        r,
        status=(
            "PROVISIONAL_UNCALIBRATED"
            if method in ("B5_beta10", "S_then_B1_two")
            else "STRICT_FINITE_REFERENCE"
        )
        if r.action
        else "INSUFFICIENT",
        independent_parents=rules.parent_count(matched),
    ) | {"rule": r.model_dump(mode="json")}


def model_name(task, fold, selected):
    return (
        task
        + f"__fold{fold}__"
        + ("none" if not selected else "-".join(map(str, selected)))
    )


def evaluate_model(root, task, fold, selected, train, evaluation, template, config):
    name = model_name(task, fold, selected)
    target = root / "models" / (name + ".json")
    if target.exists():
        assert load(target)["freeze_sha256"] == sha(root / "experiment_freeze.json")
        return name
    table, groups = table_for(train, selected, template)
    index, rules = ParentIndex(table, groups), ParentRules(table, groups)
    started = time.perf_counter()
    trees = {}
    reused = not selected
    if reused:
        original = load(
            Path(config["input_root"])
            / "crossfit"
            / f"pose_proprioception__{task}__fold{fold}.model.json"
        )
        for depth in (1, 2, 3):
            tree = OutcomeTree.__new__(OutcomeTree)
            tree.rules = rules
            tree.nodes = original["trees"][f"B2_depth{depth}"]
            tree.root = 0
            trees[str(depth)] = tree
    else:
        trees = {str(d): OutcomeTree(rules, d, 0) for d in (1, 2, 3)}
    training_seconds = time.perf_counter() - started
    decisions, predictions = {}, []
    for row in evaluation:
        features = values(row, selected)
        query = RepairQuery(scope=table.scope, features=features)
        for method in config["methods"]:
            key = hashlib.sha256(json.dumps([method, features]).encode()).hexdigest()[
                :24
            ]
            if key not in decisions:
                started = time.perf_counter_ns()
                strict_key = hashlib.sha256(
                    json.dumps(["DSRE", features]).encode()
                ).hexdigest()[:24]
                strict = (
                    decisions[strict_key]["result"]
                    if method == "S_then_B1_two"
                    else None
                )
                result = predict(method, query, index, rules, trees, strict)
                decisions[key] = {
                    "method": method,
                    "query": query.model_dump(mode="json"),
                    "result": result,
                    "cold_ms": (time.perf_counter_ns() - started) / 1e6,
                }
            predictions.append(
                {
                    "id": row["id"],
                    "group": row["group"],
                    "method": method,
                    "decision_id": key,
                }
            )
        masked = list(features)
        masked[6 if selected else 0] = None
        key = hashlib.sha256(json.dumps(["DSRE_partial", masked]).encode()).hexdigest()[
            :24
        ]
        if key not in decisions:
            started = time.perf_counter_ns()
            result = index.diagnose(
                RepairQuery(scope=table.scope, features=tuple(masked))
            )
            decisions[key] = {
                "method": "DSRE_partial",
                "query": RepairQuery(
                    scope=table.scope, features=tuple(masked)
                ).model_dump(mode="json"),
                "result": compact(result)
                | {"diagnosis": result.model_dump(mode="json")},
                "cold_ms": (time.perf_counter_ns() - started) / 1e6,
            }
        predictions.append(
            {
                "id": row["id"],
                "group": row["group"],
                "method": "DSRE_partial",
                "decision_id": key,
            }
        )
    save(
        target,
        {
            "task": task,
            "fold": fold,
            "selected": selected,
            "table": table.model_dump(mode="json"),
            "parent_groups": groups,
            "trees": {d: t.nodes for d, t in trees.items()},
            "new_tree_fits": 0 if reused else 3,
            "reused_trees": 3 if reused else 0,
            "training_seconds": training_seconds,
            "decisions": decisions,
            "predictions": predictions,
            "freeze_sha256": sha(root / "experiment_freeze.json"),
        },
    )
    print(
        json.dumps(
            {
                "model": name,
                "predictions": len(predictions),
                "new_trees": 0 if reused else 3,
            }
        ),
        flush=True,
    )
    return name


def experiment(root):
    config = load(Path("config/dsre_evidence_repair.json"))
    old = Path(config["input_root"])
    frozen = load(root / "experiment_freeze.json")
    for key in ("source_sha256", "input_sha256"):
        for name, expected in frozen[key].items():
            assert sha(Path(name)) == expected, name
    data = rows(root / "qualified_pairs.jsonl")
    splits = load(old / "group_splits.json")
    (root / "models").mkdir(exist_ok=True)
    (root / "designs").mkdir(exist_ok=True)
    designs = []
    for task in ("PickCube-v1", "PushCube-v1"):
        for fold in range(5):
            train = [
                r for r in data if r["task"] == task and splits[r["group"]] != fold
            ]
            evaluation = [
                r for r in data if r["task"] == task and splits[r["group"]] == fold
            ]
            assert not {r["group"] for r in train} & {r["group"] for r in evaluation}
            template = load(
                old / "crossfit" / f"pose_proprioception__{task}__fold{fold}.model.json"
            )["scope"]
            available = tuple(
                i
                for i in range(6)
                if any(r["optional_features"][i] is not None for r in train)
            )
            subset_scores = [
                {"channels": j, "ceiling_mass": ceiling_mass(train, j)}
                for count in range(len(available) + 1)
                for j in combinations(available, count)
            ]
            full_best = min(
                subset_scores,
                key=lambda s: (-s["ceiling_mass"], len(s["channels"]), s["channels"]),
            )
            selected_designs = []
            for selector in config["selectors"]:
                for budget in config["budgets"]:
                    selected = select_channels(
                        train, budget, selector, available, config["random_order_seed"]
                    )
                    selected_designs.append(
                        {
                            "selector": selector,
                            "budget": budget,
                            "channels": selected,
                            "model": model_name(task, fold, selected),
                            "training_ceiling_mass": ceiling_mass(train, selected),
                            "training_rows": len(train),
                            "status": "OFFLINE_DEVELOPMENT_SELECTED",
                            "reference_sha256": hashlib.sha256(
                                json.dumps(train, sort_keys=True).encode()
                            ).hexdigest(),
                        }
                    )
            design = {
                "task": task,
                "fold": fold,
                "reference_ids": [r["id"] for r in train],
                "evaluation_ids": [r["id"] for r in evaluation],
                "available": available,
                "subset_scores": subset_scores,
                "minimum_cost_full_ceiling_upgrade": full_best,
                "selected_designs": selected_designs,
                "freeze_sha256": sha(root / "experiment_freeze.json"),
            }
            design_path = root / "designs" / f"{task}__fold{fold}.json"
            if design_path.exists():
                assert load(design_path) == json.loads(json.dumps(design))
            else:
                save(design_path, design)
            # All selections are on disk before any query projection/prediction for this fold.
            for d in selected_designs:
                d["model"] = evaluate_model(
                    root,
                    task,
                    fold,
                    tuple(d["channels"]),
                    train,
                    evaluation,
                    template,
                    config,
                )
            designs.extend(selected_designs)
            save(
                root / "progress.json",
                {
                    "completed_task_folds": len(
                        list((root / "designs").glob("*.json"))
                    ),
                    "models": len(list((root / "models").glob("*.json"))),
                    "expected_task_folds": 10,
                },
            )
    finite = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        population = [r for r in data if r["task"] == task]
        template = load(
            old / "crossfit" / f"pose_proprioception__{task}__fold0.model.json"
        )["scope"]
        scores = [
            {"channels": j, "ceiling_mass": ceiling_mass(population, j)}
            for count in range(7)
            for j in combinations(range(6), count)
        ]
        diagnostic = {}
        for j, privileged in [
            ((), False),
            (tuple(range(6)), False),
            ((), True),
            (tuple(range(6)), True),
        ]:
            table, groups = table_for(population, j, template, privileged)
            index = ParentIndex(table, groups)
            p = profile(population, j, privileged)
            certificates = []
            for signature in sorted({r.features for r in table.rows}, key=str):
                output = index.diagnose(
                    RepairQuery(scope=table.scope, features=signature)
                )
                certificates.append(
                    {"signature": signature, "output": output.model_dump(mode="json")}
                )
            mass = sum(
                g["mass"]
                for g in p["signatures"]
                if next(
                    c["output"]["action"]
                    for c in certificates
                    if tuple(c["signature"]) == tuple(g["signature"])
                )
                is not None
            )
            diagnostic[
                ("all" if j else "primary") + ("/privileged" if privileged else "")
            ] = {
                "profile": p,
                "supported_grammar_mass": mass,
                "certificates": certificates,
                "table": table.model_dump(mode="json"),
                "parent_groups": groups,
            }
        finite[task] = {
            "all_subsets": scores,
            "diagnostics": diagnostic,
            "full_table_best_by_budget": [
                {
                    "budget": b,
                    "channels": select_channels(population, b),
                    "mass": ceiling_mass(population, select_channels(population, b)),
                }
                for b in config["budgets"]
            ],
        }
    save(root / "finite_profiles.json", finite)
    models = [load(p) for p in (root / "models").glob("*.json")]
    save(
        root / "experiment_completed.json",
        {
            "status": "COMPLETE",
            "task_folds": 10,
            "selected_designs": len(designs),
            "distinct_models": len(models),
            "new_tree_fits": sum(m["new_tree_fits"] for m in models),
            "reused_trees": sum(m["reused_trees"] for m in models),
            "checkpoint_method_predictions": sum(len(m["predictions"]) for m in models),
            "physics": 0,
        },
    )
    print(json.dumps(load(root / "experiment_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.freeze:
        if (args.root / "experiment_freeze.json").exists():
            raise SystemExit("Freeze exists")
        freeze(args.root)
    else:
        experiment(args.root)
