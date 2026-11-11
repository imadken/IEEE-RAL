"""Verify preservation and seal the completed RecoverBench fallback locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_hashes(expected):
    mismatches = [
        str(path)
        for name, value in expected.items()
        if not (path := Path(name)).is_file() or digest(path) != value
    ]
    if mismatches:
        raise ValueError(f"Preservation/hash failure: {mismatches}")


def verify(root):
    initial = json.loads((root / "initial.json").read_text())
    historical = json.loads((root / "historical_inventory.json").read_text())["sha256"]
    verify_hashes(historical)
    verify_hashes(initial["prior_sha256"])
    for split, rows, steps, snapshots in (
        ("source-replay", 56, 23182, 122),
        ("transfer-audit", 72, 22386, 146),
    ):
        control = json.loads(
            (
                root
                / split
                / ("audit-final.json" if split == "source-replay" else "audit.json")
            ).read_text()
        )
        physics = json.loads((root / split / "physics_audit.json").read_text())
        if not (
            control["status"] == physics["status"] == "PASS"
            and control["checked_rows"] == rows
            and control["checked_control_steps"] == steps
            and physics["checked_snapshots"] == snapshots
            and not control["mismatches"]
            and not physics["mismatches"]
        ):
            raise ValueError(f"Audit incomplete: {split}")
        verify_hashes(control["source_sha256"])
    registration = json.loads(
        Path("config/recoverbench_transfer_20261111.json").read_text()
    )
    verify_hashes(
        {
            str(root / "source_qualification_registration.json"): registration[
                "source_registration_sha256"
            ],
            str(root / "fallback_transfer_registration.json"): registration[
                "fallback_transfer_registration_sha256"
            ],
        }
    )
    archived = json.loads(
        (root / "provenance/executed_sources_before_hygiene.json").read_text()
    )
    verify_hashes(
        {v["archived_version"]: v["executed_sha256"] for v in archived.values()}
    )
    archives = {
        "data/eval_data.tar": "0c2e732286d623a4f437b55996a78f3e3c0d6260d093c839d2524dd65d2182b0",
        "data/training_scenes.tar": "ddac00ac207f02d6360fb8990ad9c22cc182c0d8b8e88f196859803c80b61740",
        "data/recovery_mimicgen_generated.tar": "9f212d9b4c846578050a46d8cbb0e9c3cb9c880487a5b928c71ed58317fc6268",
        "upstream/source-archive.tar.gz": "41894e650435bd2fb780e71ab05cf44e1c29f87b97043c0e0e1982a0d18dbe7a",
    }
    for v in json.loads((root / "upstream/dependencies.json").read_text()):
        archives["upstream/" + v["repository"].split("/")[-1] + ".tar.gz"] = v["sha256"]
    for v in json.loads((root / "upstream/minimal_seed_manifest.json").read_text()):
        archives["data/seed_demos/" + v["task"] + ".hdf5"] = v["sha256"]
    verify_hashes({str(root / p): h for p, h in archives.items()})
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    for name, version in archived.items():
        if not any(
            row["source_sha256"].get(name) == version["executed_sha256"]
            for row in commands
        ):
            raise ValueError(f"Archived code not present in execution journal: {name}")
    required = (
        "maintained-regression-final",
        "isolated-new-regressions",
        "final-lint",
        "final-format",
    )
    for name in required:
        if not any(v["name"] == name and v["exit_status"] == 0 for v in commands):
            raise ValueError(f"Required check not passed: {name}")
    ancestors = {os.getpid(), *(p.pid for p in psutil.Process().parents())}
    active = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = process.info["cmdline"] or []
            if process.pid not in ancestors and any(str(root) in arg for arg in argv):
                active.append({"pid": process.pid, "argv": argv})
        except psutil.Error:
            continue
    if active:
        raise ValueError(f"Campaign processes still active: {active}")
    old_driver_ceiling = sum(
        v["wall_seconds"] for v in commands if "driver_cpu_seconds" not in v
    )
    cpu = sum(v["cpu_seconds"] for v in commands)
    return {
        "historical_files_verified": len(historical),
        "initial_files_verified": len(initial["prior_sha256"]),
        "archives_verified": len(archives),
        "active_campaign_workers": active,
        "measured_command_cpu_seconds": cpu,
        "early_unmetered_driver_cpu_ceiling_seconds": old_driver_ceiling,
        "wall_seconds": time.time() - initial["started_epoch"],
        "gpu_wall_seconds": 0,
        "gpu_scope": "No rendering or model execution; renderer/offscreen/camera disabled",
        "paid_api_calls": 0,
        "cpu_scope": "Bounded workers; later wrapper includes driver. Early single-thread driver bounded by its wall time. Interactive tooling/editor/bootstrap and host-wide background CPU not metered; no host-wide exact CPU claim.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence already sealed")
    resource = verify(root)
    files = [p for p in root.rglob("*") if p.is_file()]
    resource["logical_bytes_before_seal"] = sum(p.stat().st_size for p in files)
    inode_sizes = {(p.stat().st_dev, p.stat().st_ino): p.stat().st_size for p in files}
    resource["unique_inode_bytes_before_seal"] = sum(inode_sizes.values())
    resource["finalizer_process_cpu_seconds"] = time.process_time()
    resource["conservative_command_and_driver_cpu_seconds"] = (
        resource["measured_command_cpu_seconds"]
        + resource["early_unmetered_driver_cpu_ceiling_seconds"]
        + resource["finalizer_process_cpu_seconds"]
    )
    if not (
        resource["wall_seconds"] < 28800
        and resource["conservative_command_and_driver_cpu_seconds"] < 43200
        and resource["logical_bytes_before_seal"] < 11_900_000_000
    ):
        raise SystemExit("Resource boundary exceeded")
    if args.seal:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        if status.strip():
            raise SystemExit("Commit maintained changes before sealing")
        (root / "resources.json").write_text(json.dumps(resource, indent=2) + "\n")
        evidence = {
            str(p.relative_to(root)): digest(p)
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }
        maintained = [
            Path(s)
            for s in subprocess.check_output(
                ["git", "ls-files"], text=True
            ).splitlines()
            if s.startswith(
                (
                    "scripts/recoverbench_",
                    "src/dual_rec/recoverbench/",
                    "tests/test_recoverbench_",
                    "config/recoverbench_",
                    "RECOVERBENCH_TRANSFER_",
                )
            )
        ]
        manifest = {
            "status": "COMPLETED_APPROVED_CASE_D_FALLBACK",
            "recommendation": "BLOCKED; tested identity-tape ACTION_COVERAGE_FAILURE; ACRR untested",
            "completed_utc": datetime.now(UTC).isoformat(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "resources": resource,
            "evidence_sha256": evidence,
            "maintained_sha256": {str(p): digest(p) for p in maintained},
            "seal_scope": "All local run files before this nonrecursive manifest; no detached workers. Seal creation/final read-only verification overhead follows resource checkpoint.",
        }
        (root / "completion_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
    print(json.dumps(resource, indent=2))


if __name__ == "__main__":
    main()
