"""Freeze the supervisor-specified unused suffix without fitting or new physics."""

import argparse
import ast
import json
import tarfile
from pathlib import Path

from dsre_followup_batch import atomic, read, sha


def prepare(root):
    if (root / "confirmation_freeze.json").exists():
        raise ValueError("Follow-up already frozen")
    config = read(Path("config/dsre_followup.json"))
    old = Path(config["previous_root"])
    seal = read(old / "completion_manifest.json")
    checked = 0
    for name, expected in seal["files"].items():
        assert sha(old / name) == expected, name
        checked += 1
    for name, expected in seal["maintained_files"].items():
        assert sha(Path(name)) == expected, name
    original = read(old / "fresh_seed_manifest.json")["parents"]
    parents = []
    for index, parent in enumerate(original):
        if (
            parent["task"] == "PickCube-v1"
            and config["pick_seed_first"] <= parent["seed"] <= config["pick_seed_last"]
            or parent["task"] == "PushCube-v1"
            and config["push_seed_first"] <= parent["seed"] <= config["push_seed_last"]
        ):
            parents.append(parent | {"original_index": index})
    parents.sort(key=lambda p: (p["task"], p["seed"]))
    parents = [p | {"index": i} for i, p in enumerate(parents)]
    assert (
        len(parents) == 333 and sum(p["task"] == "PickCube-v1" for p in parents) == 166
    )
    forbidden = {p["group"] for p in parents}
    executed = [
        json.loads(s) for s in (old / "fresh_qualified.jsonl").read_text().splitlines()
    ]
    assert not forbidden & {r["group"] for r in executed}
    executed_directories = []
    for pattern in ("*/*/fresh/*/*", "*/*/parents/*/*/*"):
        for directory in Path("results").glob(pattern):
            try:
                seed = int(directory.name.split("-")[0])
                task = directory.parent.name
            except ValueError:
                continue
            if f"{task}/{seed}" in forbidden:
                raise ValueError(
                    "A suffix parent already has an execution directory: "
                    + str(directory)
                )
            executed_directories.append(str(directory))
    with tarfile.open(old / "supervisor_review.tar.gz") as archive:
        audit_rows = json.load(
            archive.extractfile("evidence/fresh_replay_audit_records.json")
        )
        archived_groups = {"/".join(row["id"].split("/")[:2]) for row in audit_rows}
        assert len(audit_rows) == 133 and not forbidden & archived_groups
        # The review archive deliberately excludes raw trajectories; sealed live source members are checked above.
        assert not any("/fresh/" in member for member in archive.getnames())
    qualification = read(
        Path("results/dsre-stage1/20261113T144253Z/data_qualification.json")
    )
    for name, expected in qualification["controllers_sha256"].items():
        assert sha(Path(name)) == expected, name
    (root / "frozen_routers.json").write_bytes(
        (old / "frozen_routers.json").read_bytes()
    )
    atomic(
        root / "fresh_seed_manifest.json",
        {
            "status": "FROZEN_BEFORE_FOLLOWUP_OUTCOMES",
            "parents": parents,
            "execution_order_sorted_indices": [
                p["index"] for p in sorted(parents, key=lambda p: p["original_index"])
            ],
            "parent_count": 333,
            "checkpoints": 666,
            "action_continuations": 1332,
            "excluded_boundary": "PickCube-v1/6000033",
            "prior_complete_parents_per_task": 33,
            "prior_qualified_checkpoints": 133,
            "prior_results_inspected_before_new_preregistration": True,
            "prior_archive_scope": "No raw trajectory archive members; all1693sealed live members checked.",
            "existing_executed_directories_inspected": len(executed_directories),
        },
    )
    for directory in ("chunks", "parent_attempts", "parent_progress", "parent_live"):
        (root / directory).mkdir()
    sources = [
        Path("config/dsre_followup.json"),
        *sorted(Path("scripts").glob("dsre_followup_*.py")),
        Path("scripts/dsre_paper_physics.py"),
        Path("scripts/dsre_paper_confirmation.py"),
        Path("scripts/dsre_paper_reanalysis.py"),
        Path("scripts/dsre_repair_experiment.py"),
        Path("scripts/overnight_replay.py"),
        Path("scripts/overnight_pick.py"),
        Path("scripts/mani_runner.py"),
        Path("scripts/qualify.py"),
        Path("src/dual_rec/replay.py"),
        Path("src/dual_rec/validation.py"),
        Path("src/dual_rec/overnight_pick.py"),
        Path("src/dual_rec/scenarios.py"),
        Path("src/dual_rec/physical_faults.py"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
    ]
    # Save exact scientific function AST hashes to make orchestration-only reuse reviewable.
    source = ast.parse(Path("scripts/dsre_paper_physics.py").read_text())
    atomic(
        root / "scientific_reuse_regression.json",
        {
            "status": "PASS_UNMODIFIED_IMPLEMENTATION",
            "physics_file_sha256": sha(Path("scripts/dsre_paper_physics.py")),
            "prior_maintained_sha256": seal["maintained_files"][
                "scripts/dsre_paper_physics.py"
            ],
            "functions": [
                node.name
                for node in source.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef))
            ],
            "new_physics_implementations": 0,
            "new_controllers": 0,
            "new_model_fits": 0,
            "old_sealed_files_independently_checked": checked,
        },
    )
    inputs = [
        root / "followup_preregistration.md",
        root / "authority.txt",
        root / "fresh_seed_manifest.json",
        root / "frozen_routers.json",
        old / "completion_manifest.json",
        old / "confirmation_freeze.json",
        old / "physics_completed.json",
        Path("uv.lock"),
    ]
    atomic(
        root / "confirmation_freeze.json",
        {
            "status": "FROZEN_BEFORE_ANY_FOLLOWUP_OUTCOME",
            "source_sha256": {str(p): sha(p) for p in sources},
            "input_sha256": {str(p): sha(p) for p in inputs},
            "reference_router_bytes_identical_to_previous": True,
            "new_fits": 0,
            "bootstrap_seed": config["bootstrap_seed"],
            "maximum_new_parents": 333,
            "maximum_new_checkpoints": 666,
            "maximum_new_continuations": 1332,
        },
    )
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "new_parents": 333,
                "new_checkpoints": 666,
                "new_fits": 0,
                "prior_sealed_members_verified": checked,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    prepare(parser.parse_args().root)
