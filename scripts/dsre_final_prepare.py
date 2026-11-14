"""Pin the exact postmortem exclusion and immutable calibration before collection."""

import argparse
import ast
import shutil
import subprocess
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha


def prepare(root, stage):
    config = read(Path("config/dsre_final_sprint.json"))
    old = Path(config["prior_root"])
    if stage == "qualification":
        assert not (root / "qualification_freeze.json").exists()
        old_manifest = read(old / "fresh_seed_manifest.json")["parents"]
        attempted = {read(p)["group"] for p in old.glob("parent_attempts/*.json")}
        candidates = [
            p
            for p in old_manifest
            if p["split"] == "test" and p["group"] != "PickCube-v1/8000180"
        ]
        parents, excluded = [], []
        for parent in candidates:
            directories = [
                p
                for p in Path("results").glob(
                    f"**/fresh/{parent['task']}/{parent['seed']}-*"
                )
                if p.is_dir()
            ]
            if parent["group"] in attempted or directories:
                excluded.append(
                    {
                        "group": parent["group"],
                        "reason": "PREVIOUSLY_TOUCHED",
                        "directories": [str(p) for p in directories],
                    }
                )
                continue
            parents.append(
                parent | {"index": len(parents), "original_index": parent["index"]}
            )
        atomic(
            root / "fresh_seed_manifest.json",
            {
                "status": "FROZEN_BEFORE_NEW_TEST_OUTCOMES",
                "parents": parents,
                "original_planned_test": 160,
                "postmortem_exclusion": "PickCube-v1/8000180",
                "further_touched_exclusions": excluded,
                "maximum_untouched": 159,
            },
        )
        shutil.copy2(old / "calibration_audit.json", root / "calibration_audit.json")
        for name in (
            "frozen_routers.json",
            "calibration_decision.json",
            "calibration_seal.json",
            "calibration_plan.json",
            "calibration_records.json",
            "calibration_audit.json",
        ):
            assert sha(root / name) == sha(old / name), name
        old_source = root / "starting_files/scripts/dsre_operational_batch.py"
        old_tree = ast.parse(old_source.read_text())
        new_tree = ast.parse(Path("scripts/dsre_operational_batch.py").read_text())
        for name in ("parent_child", "chunk"):
            node = lambda t, name=name: next(
                n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name
            )
            assert ast.dump(node(old_tree)) == ast.dump(node(new_tree)), name
        atomic(
            root / "source_repair.json",
            {
                "old_commit": config["base"],
                "old_source_sha256": sha(old_source),
                "new_source_sha256": sha(Path("scripts/dsre_operational_batch.py")),
                "scope": "Three jsonable normalizations; strict provenance checks, all-method preexecution decisions and retained failure/success prefix diagnostics. All controller/physics/threshold/router semantics unchanged.",
                "patch": subprocess.check_output(
                    ["git", "diff", "--", "scripts/dsre_operational_batch.py"],
                    text=True,
                ),
                "parent_and_original_batch_ast_unchanged": True,
            },
        )
        shutil.copy2(
            "docs/DSRE_FINAL_SPRINT_PREREGISTRATION.md", root / "preregistration.md"
        )
        atomic(
            root / "calibration_link.json",
            {
                "root": str(old),
                "old_completion_seal_sha256": sha(old / "completion_manifest.json"),
                "calibration_decision_sha256": sha(old / "calibration_decision.json"),
                "calibration_seal_sha256": sha(old / "calibration_seal.json"),
                "calibration_unchanged": True,
                "failed_parent_preserved": read(old / "study_halt.json"),
            },
        )
    else:
        assert read(root / "qualification_seal.json")["status"] == "PASS"
        assert (
            sha(root / "qualification_results.json")
            == read(root / "qualification_seal.json")["results_sha256"]
        )
        assert not list((root / "parent_attempts").glob("*.json"))
    science = [
        Path("config/dsre_operational.json"),
        Path("config/dsre_final_sprint.json"),
        Path("scripts/dsre_operational_batch.py"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        *[
            Path("scripts") / name
            for name in (
                "dsre_paper_physics.py",
                "dsre_paper_confirmation.py",
                "dsre_operational_analysis.py",
                "dsre_operational_audit.py",
                "dsre_operational_observations.py",
                "overnight_replay.py",
                "overnight_pick.py",
                "mani_runner.py",
                "dsre_final_qualification.py",
                "dsre_final_verify.py",
                "dsre_final_prepare.py",
            )
        ],
        Path("src/dual_rec/validation.py"),
        Path("src/dual_rec/replay.py"),
        Path("src/dual_rec/overnight_pick.py"),
        Path("src/dual_rec/physical_faults.py"),
    ]
    if stage == "test":
        science.extend(
            Path("scripts") / name
            for name in ("dsre_final_batch.py", "dsre_final_analysis.py")
        )
    inputs = [
        root / name
        for name in (
            "fresh_seed_manifest.json",
            "frozen_routers.json",
            "calibration_decision.json",
            "calibration_seal.json",
            "calibration_records.json",
            "calibration_audit.json",
            "preregistration.md",
            "calibration_link.json",
            "source_repair.json",
        )
    ]
    if stage == "test":
        inputs += [
            root / "qualification_seal.json",
            root / "qualification_freeze.json",
            root / "worker_environment.json",
        ]
    output = root / (
        "qualification_freeze.json"
        if stage == "qualification"
        else "confirmation_freeze.json"
    )
    assert not output.exists()
    atomic(
        output,
        {
            "epoch": time.time(),
            "stage": stage,
            "source_sha256": {str(p): sha(p) for p in science},
            "input_sha256": {str(p): sha(p) for p in inputs},
        },
    )
    print(
        {
            "stage": stage,
            "frozen": str(output),
            "untouched_parents": len(
                read(root / "fresh_seed_manifest.json")["parents"]
            ),
        },
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("qualification", "test"), required=True)
    args = parser.parse_args()
    prepare(args.root, args.stage)
