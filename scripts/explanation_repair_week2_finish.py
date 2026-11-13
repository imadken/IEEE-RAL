"""Small Week 2 integrity seal and fresh-root reproduction initializer."""

import argparse
import fcntl
import hashlib
import json
import resource
import subprocess
import tarfile
import time
from pathlib import Path

import psutil


def load(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def maintained():
    return [
        Path("EXPLANATION_REPAIR_PROTOCOL.md"),
        Path("EXPLANATION_REPAIR_RESULTS.md"),
        Path("config/explanation_repair_week2.json"),
        Path("tests/test_explanation_repair_week2.py"),
        *sorted(Path("src/dual_rec/explanation_repair").glob("*.py")),
        *sorted(Path("scripts").glob("explanation_repair_week2*.py")),
    ]


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def initialize(root):
    root.mkdir(parents=True, exist_ok=False)
    names = git("ls-files", "-z").split("\0")
    allowed = [
        "EXPLANATION_REPAIR_PROTOCOL.md",
        "EXPLANATION_REPAIR_RESULTS.md",
        "config/explanation_repair.json",
        "src/dual_rec/explanation_repair/adapters.py",
        "src/dual_rec/explanation_repair/core.py",
        "src/dual_rec/explanation_repair/schemas.py",
        "tests/test_explanation_repair.py",
    ]
    save(
        root / "initial.json",
        {
            "started_epoch": time.time(),
            "limits": {
                "wall_seconds": 14400,
                "cpu_seconds": 21600,
                "new_bytes": 1000000000,
            },
            "reserve": {
                "wall_seconds": 1800,
                "cpu_seconds": 900,
                "new_bytes": 50000000,
            },
            "base": git("rev-parse", "HEAD"),
            "initial_status": git("status", "--short"),
            "prior_files": {
                name: digest(Path(name)) if Path(name).is_file() else None
                for name in names
                if name
            },
            "historical_seals": {
                str(p): digest(p)
                for p in Path("results").glob("**/completion_manifest.json")
            },
            "allowed_changes": allowed,
            "scope": "Week2 deterministic reproduction; no simulation, training or manuscript",
        },
    )
    (root / "commands.jsonl").write_text("")
    print("Fresh bounded reproduction root:", root)


def preserve(root):
    initial = load(root / "initial.json")
    for name, expected in initial["prior_files"].items():
        if name not in initial["allowed_changes"]:
            assert (digest(Path(name)) if Path(name).is_file() else None) == expected, (
                name
            )
    for name, expected in initial["historical_seals"].items():
        assert digest(Path(name)) == expected, name
    old = Path("results/explanation-repair/20261113T091510Z")
    old_members = load(old / "completion_manifest.json")["sha256"]
    for name, expected in old_members.items():
        assert digest(old / name) == expected, name
    for name, expected in load(root / "source_members.json").items():
        assert digest(Path(name)) == expected, name
    return {
        "status": "PASS",
        "initial_paths": len(initial["prior_files"]),
        "historical_seals": len(initial["historical_seals"]),
        "entire_week1_members": len(old_members),
        "used_sources": len(load(root / "source_members.json")),
        "gitignore_uv_lock_and_unrelated_document_moves": "UNCHANGED",
    }


def seal(root):
    assert not (root / "completion_manifest.json").exists()
    started_cpu = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        initial = load(root / "initial.json")
        checks = preserve(root)
        assert load(root / "validation.json")["status"] == "PASS"
        assert load(root / "independent_audit.json")["status"].startswith("PASS_")
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        assert all(j["exit_status"] == 0 for j in jobs)
        # Other sessions are observed only; never signal or stop an unrelated job.
        ancestors = {p.pid for p in psutil.Process().parents()} | {psutil.Process().pid}
        active = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                argv = process.info["cmdline"] or []
                if (
                    process.pid not in ancestors
                    and any(
                        "explanation_repair_week2" in a
                        or "reboot_overnight_worker.py" in a
                        for a in argv
                    )
                    and any(str(root) in a for a in argv)
                ):
                    active.append(process.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        assert not active, active
        resources = {
            "session_wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": initial.get("start_scope", "fresh reproduction start"),
            "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
            "measured_seal_cpu_seconds_before_archive": time.process_time()
            - started_cpu,
            "unmetered_small_orchestration_cpu_reserve_seconds": 600,
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "zero_gpu_training": True,
            "new_simulations": 0,
            "trained_models": 0,
            "language_model_calls": 0,
            "network_model_downloads": 0,
            "branch": git("branch", "--show-current"),
            "commit": git("rev-parse", "HEAD"),
            "workers_remaining": active,
            "push_attempted": False,
            "preservation": checks,
            "worker_jobs": len(jobs),
        }
        assert resources["session_wall_seconds"] < initial["limits"]["wall_seconds"]
        assert (
            resources["measured_worker_cpu_seconds"]
            + resources["measured_seal_cpu_seconds_before_archive"]
            + 600
            < initial["limits"]["cpu_seconds"]
        )
        save(root / "resources.json", resources)
        archive_names = [
            "authority.txt",
            "review_subset_freeze.json",
            "review_blind.jsonl",
            "review_provisional_not_gold.jsonl",
            "strongest_baseline_investigation.json",
            "control_metrics.json",
            "controls_frozen.jsonl",
            "public_coverage.json",
            "public_analysis.json",
            "trace_metrics.json",
            "trace_paired_uncertainty.json",
            "runtime.json",
            "representative_public_examples.json",
            "independent_audit.json",
            "source_members.json",
            "evaluation_input_freeze.json",
            "validation.json",
            "resources.json",
        ]
        with tarfile.open(root / "supervisor_review.tar.gz", "w:gz") as archive:
            for name in archive_names:
                if (root / name).exists():
                    archive.add(root / name, arcname="evidence/" + name)
            for path in maintained():
                archive.add(path, arcname="source/" + str(path))
        inventory = {
            str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()
        }
        logical_bytes = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        assert logical_bytes + 1000000 < initial["limits"]["new_bytes"]
        manifest = {
            "status": "COMPLETE_AUTHORIZED_WEEK2_NO_DISTINCT_ADVANTAGE_ESTABLISHED",
            "resources": resources
            | {
                "logical_bytes_before_small_manifest": logical_bytes,
                "seal_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            },
            "sha256": inventory,
            "source_sha256": {str(p): digest(p) for p in maintained()},
            "remaining_boundary": "Independent human adjudication unavailable; Week3 not authorized",
        }
        save(root / "completion_manifest.json", manifest)
        print(json.dumps(manifest["resources"], indent=2))
        print("completion_manifest_sha256", digest(root / "completion_manifest.json"))


def verify(root):
    manifest = load(root / "completion_manifest.json")
    for name, expected in manifest["sha256"].items():
        assert digest(root / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert digest(Path(name)) == expected, name
    checks = preserve(root)
    print(
        json.dumps(
            {
                "status": "PASS_SEALED_EVIDENCE_AND_PRESERVATION",
                "files": len(manifest["sha256"]),
                "preservation": checks,
                "manifest_sha256": digest(root / "completion_manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=["initialize", "seal", "verify"], required=True
    )
    args = parser.parse_args()
    {"initialize": initialize, "seal": seal, "verify": verify}[args.stage](args.root)
