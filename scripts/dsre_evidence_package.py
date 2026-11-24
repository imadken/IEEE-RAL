"""Build a compact source/evidence archive without overwriting earlier outputs."""

import argparse
import hashlib
import json
import tarfile
import time
from pathlib import Path


def build(root, target):
    files = set()
    for directory in ("src", "scripts"):
        files.update(
            p for p in Path(directory).rglob("*.py") if "__pycache__" not in p.parts
        )
    files.update(
        Path(p)
        for p in (
            "pyproject.toml",
            "uv.lock",
            "AGENTS.md",
            "tests/test_evidence_aware.py",
            "docs/DSRE_EVIDENCE_AWARE_RESEARCH_PLAN_20261117.md",
            "docs/DSRE_EVIDENCE_SPEC_V2.md",
            "docs/DSRE_TASK_AND_EXECUTION_CONTRACT.md",
        )
    )
    files.update(
        p
        for p in Path("research/dsre_evidence_design").iterdir()
        if p.is_file() and p.suffix in (".py", ".md", ".json")
    )
    files.update(p for p in root.glob("*.json") if not p.name.startswith("compact_"))
    files.update(p for p in (root / "executed_source").glob("*.py"))
    for sub in ("learner", "paired_refinement", "evaluator", "models", "evaluations"):
        files.update((root / "historical" / sub).glob("*.json"))
    files.update(
        p
        for p in (root / "historical").glob("*.json")
        if "initial" not in p.name and "schedule" not in p.name
    )
    for strategy in (
        "witness",
        "all_logs",
        "all_pairs",
        "uniform_mix",
        "decision_uncertainty",
    ):
        base = root / "historical/acquisition" / strategy
        for sub in ("learner", "paired_refinement", "models", "evaluations"):
            files.update((base / sub).glob("*.json"))
        files.add(base / "acquisition_result.json")
    files.update((root / "historical/acquisition").glob("*.json"))
    for task in ("PickCube-v1", "PegInsertionSide-v1", "PointMaze_UMaze-v3"):
        base = root / "development" / task
        files.update(base.glob("*.json"))
        for sub in (
            "learner",
            "models",
            "online_observations",
            "online_decisions",
            "evaluator",
            "assigned_logs",
            "assigned_log_seals",
            "policy_executions",
        ):
            files.update((base / sub).glob("*.json"))
        phase = (
            "pilot-interface2" if task != "PegInsertionSide-v1" else "pilot-interface3"
        )
        sample = root / "physics" / task / phase / "0"
        files.update(p for p in sample.glob("*") if p.suffix in (".json", ".gz"))
    files.update((root / "geometry/pilot").glob("*.json"))
    files.update(root.glob("*.txt"))
    source_files = [p for p in files if not str(p).startswith("results/")]
    source_hashes = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_files)
    }
    (root / "source_seal.json").write_text(json.dumps(source_hashes, indent=2) + "\n")
    files.add(root / "source_seal.json")
    manifest = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)
    }
    index = root / "compact_inventory.json"
    index.write_text(json.dumps(manifest, indent=2) + "\n")
    assert not target.exists()
    with tarfile.open(target, "w:gz", compresslevel=6) as archive:
        for p in sorted(files):
            archive.add(p, arcname=str(p), recursive=False)
        archive.add(index, arcname="compact_inventory.json")
    with target.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    receipt = {
        "archive": str(target),
        "sha256": sha,
        "bytes": target.stat().st_size,
        "members": len(files) + 1,
        "scope": "Source, all canonical numerical/statistical views and audit receipts, sampled raw physics; full raw every-parent evidence remains local.",
        "created_epoch": time.time(),
    }
    (root / "compact_archive_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(receipt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    build(args.root, args.target)


if __name__ == "__main__":
    main()
