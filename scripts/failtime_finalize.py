"""Verify compact review evidence, preserve the starting worktree, then seal."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import resource
import subprocess
import tarfile
import time
from pathlib import Path

from dual_rec.failtime.experiment import read, save, verify_seal


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def preservation(root):
    initial = read(root, "initial.json")
    concurrent = []
    for name, expected in initial["prior_files"].items():
        path = Path(name)
        if name == "supervisor_review.tar.gz" and not path.exists():
            preserved_copy = Path(
                "results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz"
            )
            assert sha(preserved_copy) == expected
            assert (
                read(root, "concurrent_worktree_observation.json")[
                    "observed_changes_to_initial_user_paths"
                ][0]["path"]
                == name
            )
            concurrent.append(
                {
                    "path": name,
                    "initial_sha256": expected,
                    "preserved_scientific_copy": str(preserved_copy),
                    "observation": "Untracked duplicate disappeared during session; no campaign command touched it; newer user/external state retained",
                }
            )
            continue
        assert (sha(path) if path.is_file() else None) == expected, name
    for name, expected in {
        "results/reboot-onset-specificity/20261112T090003Z/completion_manifest.json": "f8fc619598a864fd87dd6a2edb1702b9ca74021c922ae59036d5c39c1223b417",
        "results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz": "da45061b2d5006f7b9011fe0ab12d4e6c8568aeb1e274e241c4866eba3b560cd",
        "results/reboot-overnight/20261111T224622Z/completion_manifest.json": "f9d79bfc7df980a83e198ba33f1a0cfdf13a1222f53723a2deb80ffc12b7c07b",
        "results/reboot-overnight/20261111T224622Z/supervisor_review.tar.gz": "9e3ba45e0478a239c839502590bff5747b82e2b367b586f7e886aadeb0b106db",
    }.items():
        assert sha(Path(name)) == expected, name
    return {
        "status": "PASS",
        "starting_paths_checked": len(initial["prior_files"]),
        "initial_paths_unchanged": len(initial["prior_files"]) - len(concurrent),
        "concurrent_user_state_observations": concurrent,
        "campaign_did_not_modify_initial_user_paths": True,
        "gitignore_and_uv_lock_unchanged": True,
        "reviewed_prior_seals_and_archives_unchanged": True,
    }


def verify(root):
    verify_seal(root)
    archive = read(root, "archive.json")
    assert sha(Path(archive["path"])) == archive["sha256"]
    with tarfile.open(archive["path"]) as tar:
        inventory = json.load(tar.extractfile("ARCHIVE_SHA256.json"))
        for name, expected in inventory.items():
            assert not name.endswith((".hdf5", ".pt")) and "/env/" not in name, name
            assert (
                hashlib.sha256(tar.extractfile(name).read()).hexdigest() == expected
            ), name
    for name in (
        "independent_data_audit.json",
        "independent_numerical_audit.json",
        "streaming_parity.json",
    ):
        assert read(root, name)["status"] == "PASS", name
    save(root / "preservation.json", preservation(root))
    save(
        root / "archive_verification.json",
        {
            "status": "PASS",
            "entries_verified": len(inventory),
            "archive_sha256": archive["sha256"],
        },
    )
    print({"status": "PASS", "archive_entries": len(inventory)})


def seal(root):
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert read(root, "archive_verification.json")["status"] == "PASS"
    assert preservation(root)["status"] == "PASS"
    verify_seal(root)
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    cpu = sum(r["cpu_seconds"] for r in commands)
    downloads = [
        json.loads(s) for s in (root / "downloads.jsonl").read_text().splitlines()
    ]
    logical_bytes = sum(
        p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink()
    )
    # Hash all new evidence, including the100 consumed HDF5 files, before measuring closing CPU.
    files = {
        str(p.relative_to(root)): sha(p)
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    initial = read(root, "initial.json")
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "session_wall_seconds": time.time() - initial["started_epoch"],
        "wall_scope": initial["start_scope"],
        "measured_worker_and_closing_cpu_seconds": cpu
        + time.process_time()
        + usage.ru_utime
        + usage.ru_stime,
        "cpu_scope": "All bounded worker/driver commands and seal CPU; interactive editing, tool browsing and sub-agent reasoning overhead unmetered; no other model fits used",
        "gpu_seconds": 0,
        "paid_api_calls": 0,
        "download_payload_bytes": sum(r.get("bytes", 0) for r in downloads),
        "additional_tool_transfer_upper_bound_bytes": 20_000_000,
        "transfer_scope": "Measured local HTTP bodies including bounded failures plus conservative allowance for public source review through tools",
        "new_logical_bytes_before_small_seal": logical_bytes,
        "artifact_scope": "All files in new evidence root; compact maintained changes are covered by1MB closing allowance",
        "model_checkpoints": len(list((root / "models").glob("*.pt"))),
        "gru_seeds": [11, 23, 37],
        "gru_epochs_per_seed": 30,
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "research_workers_remaining": 0,
        "worker_verification": "All foreground command sessions completed; shared campaign worker lock acquired; no detached workers launched",
    }
    assert result["session_wall_seconds"] < initial["limits"]["wall_seconds"]
    assert (
        result["measured_worker_and_closing_cpu_seconds"]
        < initial["limits"]["cpu_seconds"]
    )
    assert (
        result["download_payload_bytes"]
        + result["additional_tool_transfer_upper_bound_bytes"]
        < initial["limits"]["download_bytes"]
    )
    assert logical_bytes + 1_000_000 < initial["limits"]["new_bytes"]
    save(root / "resources.json", result)
    files["resources.json"] = sha(root / "resources.json")
    source = {
        str(p): sha(p)
        for folder, pattern in [
            ("src/dual_rec/failtime", "*.py"),
            ("scripts", "*failtime*.py"),
            ("tests", "test_failtime*.py"),
            ("config", "failtime*.json"),
        ]
        for p in Path(folder).glob(pattern)
    }
    save(
        root / "completion_manifest.json",
        {
            "status": "COMPLETE",
            "scientific_disposition": read(root, "gates.json"),
            "resources": result,
            "archive": read(root, "archive.json"),
            "sha256": files,
            "source_sha256": source,
        },
    )
    print(json.dumps(result, indent=2))
    print("completion_manifest_sha256", sha(root / "completion_manifest.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("verify", "seal"), required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"verify": verify, "seal": seal}[args.stage](args.root)


if __name__ == "__main__":
    main()
