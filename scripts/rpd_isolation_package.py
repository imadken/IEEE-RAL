"""Scoped source preservation, provenance and compact microprotocol evidence seal."""

import argparse
import io
import json
import subprocess
import tarfile
import time
from pathlib import Path

from rpd_isolation_common import BASE, sha, verify_registration, write_json
from rpd_pilot_reproduce import check_archive

DOC = Path("docs/RPD_SOURCE_ISOLATION_AND_STAGE1_HANDOFF_20261119.md")


def additions():
    files = list(Path("scripts").glob("rpd_isolation_*.py")) + [
        Path("tests/test_rpd_source_isolation.py"),
        Path("tests/test_rpd_isolation_handoff.py"),
        DOC,
    ]
    files += [
        p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    return sorted(set(files))


def preservation():
    before = json.loads((BASE / "preservation_before.json").read_text())
    changed = []
    for name, expected in before["files"].items():
        actual = sha(name) if Path(name).is_file() else None
        if actual != expected:
            changed.append(name)
    metadata_changed = []
    for name, expected in before["historical_metadata"].items():
        path = Path(name)
        stat = path.stat() if path.is_file() else None
        if stat is None or [stat.st_size, stat.st_mtime_ns] != expected:
            metadata_changed.append(name)
    assert not changed and not metadata_changed, (changed, metadata_changed)
    old_status = before["original_user_status"].splitlines()
    current = subprocess.check_output(
        ["git", "status", "--short"], text=True
    ).splitlines()
    allowed = {str(p) for p in additions()}
    assert all(line in current for line in old_status)
    unexpected = [
        line
        for line in current
        if line not in old_status
        and line[3:] not in allowed
        and not line[3:].startswith(str(BASE))
    ]
    assert not unexpected, unexpected
    verify_registration()
    return {
        "passed": True,
        "source_parent_commit": before["head"],
        "original_path_hashes_preserved": len(before["files"]),
        "historical_metadata_entries_preserved": len(before["historical_metadata"]),
        "unchanged_user_status_entries": len(old_status),
        "manuscript_or_old_source_edits": 0,
        "changed_original_paths": [],
    }


def seal():
    write_json(BASE / "preservation_after.json", preservation())
    summary = json.loads((BASE / "final_audit/summary.json").read_text())
    write_json(
        BASE / "resource_ledger.json",
        {
            "phase": "AUTHORIZED_SOURCE_ONLY_NO_FURTHER_PHYSICS",
            "tasks": {
                t: {
                    k: r[k]
                    for k in [
                        "attempted",
                        "returned_complete",
                        "worker_wall_seconds",
                        "output_bytes",
                        "not_run",
                    ]
                }
                for t, r in summary["tasks"].items()
            },
            "worker_cap_seconds_per_task": 1200,
            "output_cap_bytes_per_task": 100 * 1024**2,
            "new_independent_parents": 0,
            "new_discovery_calibration_test_parents": 0,
            "new_dependencies": 0,
            "elapsed_calendar_seconds": time.time()
            - json.loads((BASE / "preservation_before.json").read_text())[
                "started_epoch"
            ],
        },
    )
    claim_sources = [
        BASE / "registration.json",
        BASE / "environment_and_inputs.json",
        BASE / "four_row_gate.json",
        BASE / "final_audit/summary.json",
        BASE / "technical_matches.json",
        BASE / "execution_complete.json",
        DOC,
    ]
    write_json(
        BASE / "claims_to_sources.json",
        {
            "claims": [
                {
                    "claim": "Limited isolated source completion of fixed rows; no global stability or crash cause",
                    "sources": [
                        str(BASE / "four_row_gate.json"),
                        str(BASE / "final_audit/summary.json"),
                    ],
                },
                {
                    "claim": "Actual terminal/matched technical parent0 outcomes, not independent H1 confirmation",
                    "sources": [
                        str(BASE / "technical_matches.json"),
                        str(BASE / "final_audit/summary.json"),
                    ],
                },
                {
                    "claim": "H1/H2 untested; locked matched-joint-event methodology and inactive Stage2 charter",
                    "sources": [
                        str(DOC),
                        str(
                            BASE
                            / "supervisor/RPD_RSS2027_STAGE1_METHOD_CHARTER_LOCK_20261119.md"
                        ),
                    ],
                },
            ],
            "sha256": {str(p): sha(p) for p in claim_sources},
            "raw_per_job_records": "All process receipts, native traces and logs individually covered by final integrity manifest",
        },
    )
    files = [
        p
        for p in additions()
        if p.name
        not in {
            "compact_evidence.tar.xz",
            "compact_manifest.json",
            "integrity_manifest.json",
        }
    ]
    files += [
        Path("scripts/rpd_pilot_common.py"),
        Path("scripts/rpd_pilot_audit.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    members = {}
    path = BASE / "compact_evidence.tar.xz"
    with tarfile.open(path, "x:xz", preset=3) as archive:
        for p in sorted(set(files)):
            data = p.read_bytes()
            entry = tarfile.TarInfo(str(p))
            entry.size = len(data)
            entry.mode = 0o644
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(data))
            members[str(p)] = sha(p)
    check_archive(path, members)
    write_json(
        BASE / "compact_manifest.json",
        {
            "archive_sha256": sha(path),
            "bytes": path.stat().st_size,
            "members": members,
            "dependencies": "Original canonical traces and frozen source remain in parent commit121faf7; all new diagnostic raw/log/source/registration/handoff artifacts included. No manuscripts or native binaries redistributed.",
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
            "anchor": "Scoped local Git commit",
            "scope": "Source-only diagnostic; no population H1/H2 conclusion",
        },
    )
    print(
        json.dumps(
            {
                "new_files": len(additions()),
                "archive_members": len(members),
                "archive_bytes": path.stat().st_size,
                "new_bytes": sum(p.stat().st_size for p in additions()),
                "preservation_passed": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check-preservation", "seal"])
    args = parser.parse_args()
    print(json.dumps(preservation())) if args.mode == "check-preservation" else seal()
