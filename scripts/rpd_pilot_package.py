"""Source-preserving receipts and a compact raw/canonical evidence archive."""

import argparse
import io
import json
import subprocess
import tarfile
import time
from pathlib import Path

from rpd_pilot_common import BASE, OLD, sha, verify_registration, write_json
from rpd_pilot_reproduce import check_archive

DOCS = [
    Path("docs/RPD_PHYSICAL_PILOT_METHOD_AND_AMENDMENT.md"),
    Path("docs/RPD_PHYSICAL_PILOT_OUTCOMES.md"),
    Path("docs/RPD_STAGE1_EMPIRICAL_HYPOTHESIS_GATE.md"),
]


def additions():
    paths = list(Path("scripts").glob("rpd_pilot_*.py"))
    paths += [
        Path("tests/test_rpd_physical_pilot.py"),
        Path("tests/test_rpd_pilot_forensics.py"),
        *DOCS,
    ]
    paths += [
        p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    return sorted(set(paths))


def preservation():
    before = json.loads((BASE / "preservation_before.json").read_text())
    changed = []
    for name, expected in before["files"].items():
        actual = sha(name) if Path(name).is_file() else None
        if actual != expected:
            changed.append(name)
    history_changed = []
    for name, expected in before["historical_file_metadata"].items():
        p = Path(name)
        actual = [p.stat().st_size, p.stat().st_mtime_ns] if p.is_file() else None
        if actual != expected:
            history_changed.append(name)
    verify_registration()
    original = json.loads((OLD / "preservation_before.json").read_text())
    current = subprocess.check_output(
        ["git", "status", "--short"], text=True
    ).splitlines()
    user_status = original["status"].splitlines()
    # New scoped additions are separate; every original user status line survives.
    assert all(line in current for line in user_status)
    allowed = {str(p) for p in additions()}
    unexpected = []
    for line in current:
        name = line[3:]
        if (
            line not in user_status
            and name not in allowed
            and not name.startswith(str(BASE))
        ):
            unexpected.append(line)
    assert not changed and not history_changed and not unexpected, (
        changed,
        history_changed,
        unexpected,
    )
    return {
        "passed": True,
        "source_parent_commit": before["head"],
        "original_path_hashes_preserved": len(before["files"]),
        "historical_file_size_mtime_entries_preserved": len(
            before["historical_file_metadata"]
        ),
        "original1444_inventory_rechecked_before_pilot": before[
            "original_inventory_verified"
        ],
        "original_user_status_entries_preserved": len(user_status),
        "changed_original_paths": [],
        "changed_historical_metadata": [],
        "unexpected_user_status_changes": [],
        "manuscript_edits": 0,
        "old_scientific_and_physics_sources_unchanged": True,
    }


def seal():
    write_json(BASE / "preservation_after.json", preservation())
    summary = json.loads((BASE / "final_audit/summary.json").read_text())
    write_json(
        BASE / "resource_ledger.json",
        {
            "physics_authority": "Only original10technical parent slots per task with neutral controls",
            "physics_stopped": True,
            "source_failure": True,
            "physics_not_resumed": True,
            "per_family": {
                task: {
                    key: r[key]
                    for key in [
                        "counts",
                        "known_native_controls",
                        "native_controls_unreturned_row_range",
                        "measured_completed_episode_wall_seconds",
                        "actual_total_worker_wall_seconds",
                        "conservative_total_worker_wall_upper_seconds",
                        "raw_compressed_bytes",
                    ]
                }
                for task, r in summary["tasks"].items()
            },
            "worker_seconds_cap_per_family": 10800,
            "new_compressed_bytes_cap_per_family": 3 * 1024**3,
            "total_new_parent_exposure": 2,
            "total_complete_qualified_parents": 0,
            "new_discovery_calibration_or_test_parents": 0,
            "new_controller_training": 0,
            "new_dependencies": 0,
            "paid_API_calls": 0,
            "new_hardware_experiments": 0,
            "peak_memory": "NOT_MEASURED",
            "wall_calendar_seconds_to_packaging": time.time()
            - json.loads((BASE / "preservation_before.json").read_text())[
                "started_epoch"
            ],
        },
    )
    source_paths = list(Path("scripts").glob("rpd_pilot_*.py")) + [
        Path("tests/test_rpd_physical_pilot.py"),
        Path("tests/test_rpd_pilot_forensics.py"),
    ]
    write_json(
        BASE / "final_code_manifest.json",
        {
            "files": {str(p): sha(p) for p in source_paths},
            "post_failure_additions": "Forensic missingness correction, scientific handoff and offline package/reproduction only; frozen physics/menu/source/test code not changed after collection.",
        },
    )
    paths = [
        p
        for p in additions()
        if p.name
        not in {
            "compact_evidence.tar.xz",
            "compact_manifest.json",
            "integrity_manifest.json",
        }
    ]
    # Include exact existing core native Python dependencies as context, no vendor binaries/manuscripts.
    dependencies = json.loads((BASE / "source_preflight.json").read_text())["hashes"]
    paths += [Path(p) for p in dependencies if p.endswith((".py", ".pyi", ".urdf"))]
    paths += [
        Path("src/dual_rec/recoverability/adapters.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    archive_path = BASE / "compact_evidence.tar.xz"
    members = {}
    with tarfile.open(archive_path, "x:xz", preset=3) as archive:
        for path in sorted(set(paths)):
            content = path.read_bytes()
            info = tarfile.TarInfo(str(path))
            info.size = len(content)
            info.mode = 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(content))
            members[str(path)] = sha(path)
    check_archive(archive_path, members)
    write_json(
        BASE / "compact_manifest.json",
        {
            "archive_sha256": sha(archive_path),
            "bytes": archive_path.stat().st_size,
            "members": members,
            "scope": "All new source, raw/native traces, canonical rows, registration, negative results, receipts and docs; existing Python/native source context, no manuscripts or simulator binary redistribution",
        },
    )
    write_json(
        BASE / "integrity_manifest.json",
        {
            "files": {
                str(p): sha(p)
                for p in additions()
                if p.name != "integrity_manifest.json"
            },
            "self_anchor": "Scoped local Git commit; no self-referential hash",
            "scientific_decision": "SOURCE_NOT_QUALIFIED",
        },
    )
    print(
        json.dumps(
            {
                "preservation": True,
                "new_files": len(additions()),
                "archive_members": len(members),
                "archive_bytes": archive_path.stat().st_size,
                "new_bytes": sum(p.stat().st_size for p in additions()),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check-preservation", "seal"])
    args = parser.parse_args()
    if args.mode == "seal":
        seal()
    else:
        print(json.dumps(preservation()))
