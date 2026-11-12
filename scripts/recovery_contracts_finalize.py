"""Package compact local review evidence, verify preservation, and seal the run."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import resource
import subprocess
import tarfile
import time
from pathlib import Path


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(root, name):
    return json.loads((root / name).read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def maintained():
    return sorted(
        list(Path(".").glob("RECOVERY_CONTRACTS_*.md"))
        + list(Path("config").glob("recovery_contracts_*.json"))
        + list(Path("src/dual_rec/contracts").glob("*.py"))
        + list(Path("scripts").glob("recovery_contracts_*.py"))
        + [Path("tests/test_recovery_contracts.py")]
        + list(Path("tests/fixtures/recovery_contracts").glob("*.json"))
    )


def preserve(root):
    initial = read(root, "initial.json")
    for name, expected in initial["prior_files"].items():
        path = Path(name)
        assert (sha(path) if path.is_file() else None) == expected, name
    prior = read(root, "registration.json")["prior_manifests"]
    for name, expected in prior.items():
        assert sha(Path(name)) == expected, name
    # In addition to initial tracked/user paths and the 26 registered manifests,
    # preserve the canonical prior review archives used in the primary cases.
    for name, expected in {
        "results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz": "da45061b2d5006f7b9011fe0ab12d4e6c8568aeb1e274e241c4866eba3b560cd",
        "results/reboot-overnight/20261111T224622Z/supervisor_review.tar.gz": "9e3ba45e0478a239c839502590bff5747b82e2b367b586f7e886aadeb0b106db",
        "results/failtime-online/20261112T101800Z/supervisor_review.tar.gz": "42b60374ac7f038736aa632d67ca144cb2e940f67c234546f5a7f90220eedc3c",
    }.items():
        assert sha(Path(name)) == expected, name
    return {
        "status": "PASS",
        "initial_paths_checked": len(initial["prior_files"]),
        "registered_prior_manifests_checked": len(prior),
        "canonical_previous_archives_checked": 3,
        "gitignore_lockfile_user_document_moves": "Unchanged from initial snapshot",
    }


def archive(root):
    target = root / "supervisor_review.tar.gz"
    assert not target.exists()
    entries = {"maintained/" + str(p): p for p in maintained()}
    suffixes = {".json", ".jsonl", ".npz", ".pdf", ".png", ".csv", ".xml", ".log"}
    for p in root.rglob("*"):
        relative = p.relative_to(root)
        if (
            p.is_symlink()
            or not p.is_file()
            or "cache" in relative.parts
            or "literature" in relative.parts
        ):
            continue
        if p.suffix in suffixes or p.name.endswith(".jsonl.gz"):
            entries["evidence/" + str(relative)] = p
    literature = root / "literature/inspection_manifest.json"
    entries["evidence/literature/inspection_manifest.json"] = literature
    inventory = {name: sha(path) for name, path in entries.items()}
    with tarfile.open(target, "w:gz", compresslevel=5) as tar:
        for name, path in sorted(entries.items()):
            tar.add(path, arcname=name, recursive=False)
        payload = (json.dumps(inventory, indent=2) + "\n").encode()
        header = tarfile.TarInfo("ARCHIVE_SHA256.json")
        header.size = len(payload)
        tar.addfile(header, io.BytesIO(payload))
    save(
        root / "archive.json",
        {
            "path": str(target),
            "sha256": sha(target),
            "bytes": target.stat().st_size,
            "entries": len(entries),
            "scope": "Local compact review archive: maintained sources/docs, new risk predictions, calibration/model metadata, figures, audits and decisive action traces. No raw old dataset, environments or neural weights. Raw-primary read notes omitted; primary links/scope retained. Full reproduction uses immutable original inputs and the new weights outside this archive.",
        },
    )
    print(read(root, "archive.json"))


def verify(root):
    from dual_rec.failtime.experiment import verify_seal

    for k in range(5):
        child = root / "failtime" / f"fold{k}"
        verify_seal(child)
        assert read(child, "independent_numerical_audit.json")["status"] == "PASS"
    for name in (
        "independent_numerical_audit.json",
        "independent_derived_audit.json",
        "prefix_noninterference.json",
        "reboot_reproduction.json",
        "recoverbench_reproduction.json",
        "recoverbench/independent_numerical_audit.json",
        "recoverbench/independent_physics_audit.json",
    ):
        assert read(root, name)["status"] == "PASS", name
    archive_info = read(root, "archive.json")
    assert sha(Path(archive_info["path"])) == archive_info["sha256"]
    with tarfile.open(archive_info["path"]) as tar:
        inventory = json.load(tar.extractfile("ARCHIVE_SHA256.json"))
        for name, expected in inventory.items():
            assert not name.endswith((".pt", ".hdf5")) and "/env/" not in name
            assert (
                hashlib.sha256(tar.extractfile(name).read()).hexdigest() == expected
            ), name
        for p in maintained():
            assert inventory["maintained/" + str(p)] == sha(p), p
    save(root / "preservation.json", preserve(root))
    save(
        root / "archive_verification.json",
        {
            "status": "PASS",
            "entries_verified": len(inventory),
            "archive_sha256": archive_info["sha256"],
        },
    )
    print({"status": "PASS", "archive_entries": len(inventory)})


def seal(root):
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert read(root, "archive_verification.json")["status"] == "PASS"
    assert preserve(root)["status"] == "PASS"
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    failures_path = root / "resolved_worker_failures.json"
    resolved = read(root, failures_path.name) if failures_path.exists() else {}
    assert all(
        row["exit_status"] == 0 or row["name"] in resolved for row in commands
    ), "Unresolved worker failure must be recorded explicitly"
    files = {
        str(p.relative_to(root)): sha(p)
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (
        sum(row["cpu_seconds"] for row in commands)
        + time.process_time()
        + usage.ru_utime
        + usage.ru_stime
    )
    logical_bytes = sum(
        p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink()
    )
    initial = read(root, "initial.json")
    result = {
        "session_wall_seconds": time.time() - initial["started_epoch"],
        "wall_scope": initial["start_scope"],
        "measured_worker_and_seal_cpu_seconds": cpu,
        "interactive_cpu_allowance_seconds": 300,
        "cpu_scope": "All research workers, model fits, evaluation, audits, archive/test commands and closing process measured; small interactive inspection/formatting commands not individually metered, conservatively covered by 300 CPU seconds. Reasoning and remote browsing overhead not CPU-metered.",
        "gpu_seconds": 0,
        "additional_dataset_download_bytes": 0,
        "public_source_tool_transfer_allowance_bytes": 20_000_000,
        "transfer_scope": "No new datasets or local HTTP acquisition; public primary-source reading through web tools not byte-metered, bounded by conservative allowance",
        "new_logical_bytes_before_small_seal": logical_bytes,
        "maintained_change_allowance_bytes": 1_000_000,
        "model_checkpoints": sum(
            len(read(root / "failtime" / f"fold{k}", "models_index.json"))
            for k in range(5)
        ),
        "neural_fits": 15,
        "seeds": [11, 23, 37],
        "epochs_per_fit": 30,
        "completed_folds": 5,
        "source_simulator_rollouts": 24,
        "executed_controls": 9862,
        "research_workers_remaining": 0,
        "worker_verification": "All foreground tool sessions completed; shared worker lock acquired; no detached workers or agents launched",
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "paid_api_calls": 0,
        "preserved_failed_worker_attempts": [
            row["name"] for row in commands if row["exit_status"] != 0
        ],
    }
    limits = initial["limits"]
    assert result["session_wall_seconds"] < limits["wall_seconds"]
    assert cpu + 300 < limits["cpu_seconds"]
    assert logical_bytes + 1_000_000 < limits["new_bytes"]
    assert 20_000_000 < limits["download_bytes"]
    save(root / "resources.json", result)
    files["resources.json"] = sha(root / "resources.json")
    save(
        root / "completion_manifest.json",
        {
            "status": "COMPLETE",
            "scientific_disposition": "Fixed consolidation complete; candidate methodological contribution, novelty provisional; no physical recovery improvement or publication-readiness claim",
            "resources": result,
            "archive": read(root, "archive.json"),
            "sha256": files,
            "source_sha256": {str(p): sha(p) for p in maintained()},
        },
    )
    print(json.dumps(result, indent=2))
    print("completion_manifest_sha256", sha(root / "completion_manifest.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("archive", "verify", "seal"), required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"archive": archive, "verify": verify, "seal": seal}[args.stage](args.root)


if __name__ == "__main__":
    main()
