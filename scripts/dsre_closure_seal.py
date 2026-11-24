"""Preservation, bounded-resource and compact-transfer seal for the closure."""

import argparse
import hashlib
import json
import tarfile
import time
from pathlib import Path

BASE = Path("research/dsre_experimental_closure")
DOCS = [
    "DSRE_STAGE1_FINAL_SCIENCE_CLOSURE.md",
    "DSRE_STAGE1_OBLIGATION_CONTRAST_RESULTS.md",
    "DSRE_STAGE1_IDENTIFICATION_SOURCE_AUDIT.md",
    "DSRE_STAGE1_CERTIFICATE_BASELINE_AUDIT.md",
    "DSRE_STAGE1_RSS_REVIEWER_RISKS.md",
    "DSRE_STAGE2_FEASIBLE_EXPERIMENT_MATRIX.md",
]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def seal():
    original = json.loads((BASE / "preservation_before.json").read_text())
    checked = {}
    for group in ("files", "seals", "manuscripts"):
        for path, expected in original[group].items():
            actual = digest(path) if Path(path).is_file() else None
            assert actual == expected, f"Original preservation differs: {path}"
        checked[group] = len(original[group])
    freeze = json.loads((BASE / "final/analysis_code_freeze.json").read_text())
    for path, expected in freeze["code_sha256"].items():
        assert digest(path) == expected, f"Analysis changed after final freeze: {path}"
    new_paths = sorted(
        [
            *Path("scripts").glob("dsre_closure_*.py"),
            Path("tests/test_dsre_closure.py"),
            *[Path("docs") / name for name in DOCS],
        ]
    )
    new_bytes = sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file())
    new_bytes += sum(p.stat().st_size for p in new_paths)
    elapsed = time.time() - original["started_epoch"]
    assert elapsed < 12 * 3600 and new_bytes < 2 * 1024**3
    dump(
        BASE / "preservation_and_resources.json",
        {
            "passed": True,
            "original_inventory_counts": checked,
            "original_head": original["head"],
            "original_user_status": original["status"],
            "original_data_code_manuscripts_and_seals": "UNCHANGED",
            "actual_contract_wall_seconds": elapsed,
            "max_wall_seconds": 43200,
            "new_artifact_bytes_before_pack": new_bytes,
            "max_new_artifact_bytes": 2147483648,
            "new_physics_processes": 0,
            "new_controller_training_runs": 0,
            "cpu_accounting": "Per-final-run and repeated-run child CPU measured in run_complete.json. Cumulative wall covers all development, reads, reports and testing; a complete per-prototype CPU sum is unavailable.",
            "checked_frozen_analysis_files": freeze["code_sha256"],
        },
    )
    members = sorted(
        {
            *new_paths,
            *[
                p
                for p in BASE.rglob("*")
                if p.is_file()
                and p.name
                not in (
                    "closure_manifest.json",
                    "compact_closure.tar.xz",
                    "compact_archive_receipt.json",
                    "local_commit_receipt.json",
                )
            ],
        }
    )
    manifest = {str(p): digest(p) for p in members}
    dump(
        BASE / "closure_manifest.json",
        {
            "files": manifest,
            "scope": "New closure outputs/source/tests/reports only. Original evidence remains in original sealed paths.",
            "original_preservation": str(BASE / "preservation_before.json"),
        },
    )
    archive_path = BASE / "compact_closure.tar.xz"
    assert not archive_path.exists(), "Do not overwrite a sealed package"
    with tarfile.open(archive_path, "w:xz", preset=6) as archive:
        for path in members:
            archive.add(path, arcname=str(path), recursive=False)
    with tarfile.open(archive_path, "r:xz") as archive:
        for member in archive.getmembers():
            assert (
                hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                == manifest[member.name]
            )
    total = sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file()) + sum(
        p.stat().st_size for p in new_paths
    )
    assert total < 2 * 1024**3
    dump(
        BASE / "compact_archive_receipt.json",
        {
            "passed": True,
            "archive": str(archive_path),
            "archive_sha256": digest(archive_path),
            "archive_bytes": archive_path.stat().st_size,
            "all_new_artifact_bytes": total,
            "members": manifest,
            "full_source_reproduction_requires": "Original sealed native evidence in this local repository; compact archive is an offline analysis handoff, not a substitute for original raw physics.",
        },
    )
    print(
        json.dumps(
            {
                "preservation": checked,
                "sealed_files": len(members),
                "archive_bytes": archive_path.stat().st_size,
                "new_bytes": total,
                "contract_wall_seconds": elapsed,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    seal()
