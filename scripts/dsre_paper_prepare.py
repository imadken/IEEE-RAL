"""Freeze development-only routers and a fixed unused prospective parent cohort."""

import argparse
import hashlib
import json
from pathlib import Path

from dsre_repair_experiment import table_for

from dual_rec.dsre.baselines import OutcomeTree
from dual_rec.dsre.repair import ParentRules
from dual_rec.dsre.repair_selection import select_channels


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(root):
    config = load(Path("config/dsre_rss2027.json"))
    old = Path(config["original_root"])
    development = Path(config["development_root"])
    qualification = load(old / "data_qualification.json")
    for name, expected in qualification["controllers_sha256"].items():
        if sha(Path(name)) != expected:
            raise ValueError("Qualified controller source changed: " + name)
    source = [
        json.loads(s)
        for s in (development / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    observed = {r["seed"] for r in source}
    # Inspect existing executed parent directories without traversing unrelated datasets.
    paths = list(Path("results").glob("*/*/parents/*/*/*/checkpoint.json"))
    for p in paths:
        try:
            observed.add(int(p.parent.name.split("-")[0]))
        except ValueError:
            pass
    parents = []
    for index in range(config["parents_per_task"]):
        for task in config["tasks"]:
            seed = config["seed_bases"][task] + index
            if seed in observed:
                raise ValueError("Prospective seed already used: " + str(seed))
            parents.append(
                {
                    "task": task,
                    "seed": seed,
                    "group": task + "/" + str(seed),
                    "conditions": config["conditions"][task],
                }
            )
    save(
        root / "fresh_seed_manifest.json",
        {
            "status": "FROZEN_BEFORE_ANY_FRESH_OUTCOME",
            "parents": parents,
            "parents_per_task": 200,
            "total_parents": 400,
            "checkpoints": 800,
            "maximum_candidate_outcome_continuations": 1600,
            "previous_execution_directories_inspected": len(paths),
            "no_seed_replacement": True,
        },
    )
    fitted = {}
    tree_fits = 0
    for task in config["tasks"]:
        population = [r for r in source if r["task"] == task]
        template = load(
            old / "crossfit" / f"pose_proprioception__{task}__fold0.model.json"
        )["scope"]
        fitted[task] = {}
        for budget in config["primary_budgets"]:
            selected = select_channels(population, budget)
            table, groups = table_for(population, selected, template)
            rules = ParentRules(table, groups, 2)
            trees = {
                str(d): OutcomeTree(rules, d, 0).nodes for d in config["tree_depths"]
            }
            tree_fits += 2
            fitted[task][str(budget)] = {
                "selected": selected,
                "table": table.model_dump(mode="json"),
                "parent_groups": groups,
                "trees": trees,
                "tree_targets": ["strict1", "empirical.9"],
                "reference_sha256": hashlib.sha256(
                    table.model_dump_json().encode()
                ).hexdigest(),
            }
    save(
        root / "frozen_routers.json",
        {
            "status": "FROZEN_BEFORE_FRESH_OUTCOMES",
            "tasks": fitted,
            "new_small_tree_fits": tree_fits,
            "selection_data_only": str(development / "qualified_pairs.jsonl"),
            "deployment": "DISABLED_NOT_CALIBRATED",
        },
    )
    sources = [
        Path("config/dsre_rss2027.json"),
        Path("scripts/dsre_paper_prepare.py"),
        Path("scripts/dsre_paper_physics.py"),
        Path("scripts/recovery_claims_physics.py"),
        Path("scripts/overnight_replay.py"),
        Path("scripts/overnight_pick.py"),
        Path("scripts/mani_runner.py"),
        Path("src/dual_rec/replay.py"),
        Path("src/dual_rec/validation.py"),
        Path("src/dual_rec/overnight_pick.py"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
    ]
    inputs = [
        root / "fresh_seed_manifest.json",
        root / "frozen_routers.json",
        root / "preregistration.md",
        root / "authority.txt",
        development / "qualified_pairs.jsonl",
        development / "completion_manifest.json",
        old / "data_qualification.json",
        Path("uv.lock"),
    ]
    save(
        root / "confirmation_freeze.json",
        {
            "status": "FROZEN_BEFORE_ANY_FRESH_OUTCOME",
            "source_sha256": {str(p): sha(p) for p in sources},
            "input_sha256": {str(p): sha(p) for p in inputs},
            "small_tree_fits": tree_fits,
            "first_fresh_outcome_not_yet_generated": True,
        },
    )
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "parents": 400,
                "checkpoints": 800,
                "small_tree_fits": tree_fits,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    args = p.parse_args()
    if (args.root / "confirmation_freeze.json").exists() or (
        args.root / "completion_manifest.json"
    ).exists():
        raise SystemExit("Already frozen or sealed")
    prepare(args.root)
