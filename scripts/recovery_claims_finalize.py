"""Preserve historical evidence, package compact review files and seal this campaign."""

import argparse
import fcntl
import hashlib
import io
import json
import subprocess
import tarfile
import time
from pathlib import Path

from recovery_contracts_finalize import sha


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def maintained():
    return sorted(
        [
            *Path(".").glob("RECOVERY_CLAIMS_*.md"),
            Path("config/recovery_claims.json"),
            Path("src/dual_rec/contracts/claims.py"),
            *Path("scripts").glob("recovery_claims_*.py"),
            Path("tests/test_recovery_claims.py"),
        ]
    )


def preserve(root):
    initial = read(root / "initial.json")
    for name, expected in initial["prior_files"].items():
        p = Path(name)
        assert (sha(p) if p.is_file() else None) == expected, name
    for name, expected in read(root / "historical_seal_hashes.json").items():
        assert sha(Path(name)) == expected, name
    amendments = (
        read(root / "source_amendments.json")
        if (root / "source_amendments.json").exists()
        else {}
    )
    for name, expected in read(root / "confirmation_freeze.json")[
        "source_sha256"
    ].items():
        if name in amendments:
            fix = amendments[name]
            allowed = {
                "scripts/recovery_claims_review.py": "serialization_only",
                "src/dual_rec/contracts/claims.py": "cli_reporting_only",
            }
            assert name in allowed and fix["kind"] == allowed[name]
            original = root / fix["preserved_original"]
            assert sha(original) == expected == fix["original_sha256"]
            text = original.read_text()
            for change in fix["exact_replacements"]:
                assert text.count(change["old"]) == 1
                text = text.replace(change["old"], change["new"], 1)
            assert (
                Path(name).read_text() == text
                and sha(Path(name)) == fix["amended_sha256"]
            )
        else:
            assert sha(Path(name)) == expected, name
    for name, expected in read(root / "secondary_source_hashes.json").items():
        assert sha(Path(name)) == expected, name
    return {
        "status": "PASS",
        "initial_paths": len(initial["prior_files"]),
        "historical_seals": len(read(root / "historical_seal_hashes.json")),
        "frozen_sources_unchanged": not bool(amendments),
        "serialization_only_amended_sources": list(amendments),
        "scientific_parameters_recording_and_method_unchanged": True,
        "secondary_sources_unchanged": True,
        "user_document_moves_gitignore_lockfile": "Preserved exactly from initial snapshot",
    }


def archive(root):
    assert read(root / "independent_audit.json")["status"] == "PASS"
    save(root / "preservation.json", preserve(root))
    entries = {"maintained/" + str(p): p for p in maintained()}
    for p in root.iterdir():
        if (
            p.is_file()
            and p.suffix in (".json", ".jsonl", ".csv")
            and p.stat().st_size < 25_000_000
        ):
            entries["evidence/" + p.name] = p
    for folder in ("figures", "external_evaluator", "frozen_source_copies"):
        for p in (root / folder).rglob("*"):
            if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts:
                entries["evidence/" + str(p.relative_to(root))] = p
    inventory = {name: sha(p) for name, p in entries.items()}
    target = root / "supervisor_review.tar.gz"
    assert not target.exists()
    with tarfile.open(target, "w:gz", compresslevel=5) as stream:
        for name, p in sorted(entries.items()):
            stream.add(p, arcname=name, recursive=False)
        payload = (json.dumps(inventory, indent=2) + "\n").encode()
        header = tarfile.TarInfo("ARCHIVE_SHA256.json")
        header.size = len(payload)
        stream.addfile(header, io.BytesIO(payload))
    save(
        root / "archive.json",
        {
            "path": str(target),
            "sha256": sha(target),
            "bytes": target.stat().st_size,
            "entries": len(entries),
            "scope": "Research docs, implementation, tables, audits, registered seeds, frozen verifier and selected raw traces. Full raw cohort remains outside compact archive. Final resource ledger and seal follow packaging and are authoritative outside archive. No old dataset, environment, model weights or manuscript.",
        },
    )
    with tarfile.open(target) as stream:
        supplied = json.load(stream.extractfile("ARCHIVE_SHA256.json"))
        for name, expected in sorted(supplied.items()):
            assert (
                hashlib.sha256(stream.extractfile(name).read()).hexdigest() == expected
            ), name
    save(
        root / "archive_verification.json",
        {
            "status": "PASS",
            "entries_verified": len(inventory),
            "archive_sha256": sha(target),
        },
    )
    print(read(root / "archive.json"))


def seal(root):
    started_cpu = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert read(root / "archive_verification.json")["status"] == "PASS"
        audit = read(root / "independent_audit.json")
        assert audit["status"] == "PASS" and audit["invalid_acceptance_bounds_verified"]
        assert read(root / "external_evaluator_smoke.json")["status"] == "PASS"
        assert preserve(root)["status"] == "PASS"
        initial = read(root / "initial.json")
        commands = [
            json.loads(line)
            for line in (root / "commands.jsonl").read_text().splitlines()
        ]
        resolutions = read(root / "resolved_worker_failures.json")
        assert all(c["exit_status"] == 0 or c["name"] in resolutions for c in commands)
        archive_info = read(root / "archive.json")
        assert sha(Path(archive_info["path"])) == archive_info["sha256"]
        inventory = {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and not p.is_symlink()
        }
        complete = list((root / "parents").glob("*/*/*/checkpoint.json"))
        historical_versions = list(
            (root / "development_record_versions").glob("*/checkpoint.json")
        )
        continuation_count = sum(
            read(p)["physical_continuations"] for p in complete + historical_versions
        )
        cpu = (
            sum(c["cpu_seconds"] for c in commands) + time.process_time() - started_cpu
        )
        cpu += read(root / "preconfirmation_engine_verification.json")["cpu_seconds"]
        usage = {
            "session_wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": initial["start_scope"],
            "measured_worker_and_seal_cpu_seconds": cpu,
            "interactive_cpu_allowance_seconds": 600,
            "cpu_scope": "All substantive jobs metered by bounded worker; sealing and engine hash check measured. Interactive inspection, lint, focused tests and final read-only verification covered by conservative 600 CPU-second allowance. Reasoning/browser infrastructure CPU not locally measured.",
            "gpu_seconds": 0,
            "additional_dataset_download_bytes": 0,
            "public_source_transfer_allowance_bytes": 20_000_000,
            "download_scope": "No new dataset/weights; primary web reads not byte-metered and covered by this allowance",
            "new_logical_bytes_before_small_seal": sum(
                p.stat().st_size
                for p in root.rglob("*")
                if p.is_file() and not p.is_symlink()
            ),
            "maintained_change_allowance_bytes": 1_000_000,
            "completed_parent_condition_cells": len(complete),
            "preserved_development_repeat_cells": len(historical_versions),
            "persisted_completed_physical_continuations": continuation_count,
            "failed_attempt_rollout_count": "Partial non-checkpointed work unavailable; CPU and failed logs retained, not claimed as zero",
            "research_workers_remaining": 0,
            "worker_verification": "All foreground sessions completed; exclusive shared worker lock held through seal; no detached jobs or agents launched",
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "push_attempted": False,
            "neural_training_fits": 0,
            "preserved_nonzero_jobs": [
                c["name"] for c in commands if c["exit_status"] != 0
            ],
        }
        limits = initial["limits"]
        assert usage["session_wall_seconds"] < limits["wall_seconds"]
        assert cpu + 600 < limits["cpu_seconds"]
        assert (
            usage["new_logical_bytes_before_small_seal"] + 1_000_000
            < limits["new_bytes"]
        )
        save(root / "resources.json", usage)
        inventory["resources.json"] = sha(root / "resources.json")
        save(
            root / "completion_manifest.json",
            {
                "status": "COMPLETE_AUTHORIZED_FIXED_WORK"
                if len(
                    list((root / "parents/confirmation").glob("*/*/checkpoint.json"))
                )
                == 1050
                else "RESOURCE_BOUNDARY_CHECKPOINT",
                "scientific_disposition": read(root / "scientific_disposition.json"),
                "resources": usage,
                "archive": archive_info,
                "sha256": inventory,
                "source_sha256": {str(p): sha(p) for p in maintained()},
            },
        )
        print(json.dumps(usage, indent=2))
        print("completion_manifest_sha256", sha(root / "completion_manifest.json"))


def verify(root):
    manifest = read(root / "completion_manifest.json")
    for name, expected in manifest["sha256"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert sha(Path(name)) == expected, name
    assert preserve(root)["status"] == "PASS"
    print(
        {
            "status": "PASS",
            "sealed_files": len(manifest["sha256"]),
            "seal_sha256": sha(root / "completion_manifest.json"),
        }
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--stage", choices=["archive", "seal", "verify"], required=True)
    a = p.parse_args()
    if a.stage != "verify" and (a.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"archive": archive, "seal": seal, "verify": verify}[a.stage](a.root)
