"""Bounded evidence-repair initialization, preservation, compact archive and seal."""

import argparse
import fcntl
import hashlib
import json
import subprocess
import tarfile
import time
from pathlib import Path

import psutil
from dsre_repair_audit import frozen_sources


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def initialize(root, authority):
    if authority is None or not authority.is_file():
        raise ValueError(
            "Initialize requires --authority pointing to the complete supervisor contract"
        )
    root.mkdir(parents=True, exist_ok=False)
    config = load(Path("config/dsre_evidence_repair.json"))
    names = set(git("ls-files", "-z").split("\0")) | {
        str(p) for p in Path("docs").rglob("*") if p.is_file()
    }
    save(
        root / "initial.json",
        {
            "started_epoch": time.time(),
            "base": git("rev-parse", "HEAD"),
            "initial_status": git("status", "--short"),
            "limits": {
                "wall_seconds": 14400,
                "cpu_seconds": 18000,
                "new_bytes": 500000000,
            },
            "reserve": {
                "wall_seconds": 3600,
                "cpu_seconds": 1800,
                "new_bytes": 50000000,
            },
            "prior_files": {
                n: sha(Path(n)) if Path(n).is_file() else None for n in names if n
            },
            "historical_seals": {
                str(p): sha(p)
                for p in Path("results").glob("**/completion_manifest.json")
            },
            "prior_run_members": {
                str(p): sha(p)
                for old in (Path(config["input_root"]), Path(config["prior_v11_root"]))
                for p in old.rglob("*")
                if p.is_file()
            },
        },
    )
    (root / "authority.txt").write_bytes(authority.read_bytes())
    (root / "commands.jsonl").write_text("")


def preservation(root):
    initial = load(root / "initial.json")
    for category in ("prior_files", "historical_seals", "prior_run_members"):
        for name, expected in initial[category].items():
            path = Path(name)
            assert (sha(path) if path.is_file() else None) == expected, name
    pins = frozen_sources(root)
    return {
        category: len(initial[category])
        for category in ("prior_files", "historical_seals", "prior_run_members")
    } | {"frozen_inputs_and_sources": pins}


def workers(root):
    p = psutil.Process()
    excluded = {p.pid, *[a.pid for a in p.parents()]}
    found = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if (
                process.pid not in excluded
                and str(root) in args
                and any(
                    Path(a).name.startswith("dsre_repair_")
                    or Path(a).name == "reboot_overnight_worker.py"
                    for a in args
                )
            ):
                found.append(process.pid)
        except psutil.Error:
            pass
    return found


def maintained():
    return [
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        *sorted(Path("scripts").glob("dsre_repair_*.py")),
        Path("scripts/dsre_audit.py"),
        Path("scripts/dsre_v11_audit.py"),
        Path("scripts/dsre_experiment.py"),
        Path("scripts/reboot_overnight_worker.py"),
        Path("scripts/explanation_repair_finish.py"),
        *sorted(Path("tests").glob("test_dsre_*.py")),
        Path("config/dsre_evidence_repair.json"),
        Path("config/dsre_stage1.json"),
        *sorted(Path("docs").glob("DSRE_STAGE1_EVIDENCE_REPAIR_*.md")),
    ]


def seal(root):
    started = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in (
            "input_audit.json",
            "feature_qualification.json",
            "independent_audit.json",
            "validation.json",
            "review_audit.json",
        ):
            assert load(root / name)["status"] == "PASS", name
        for name in (
            "experiment_completed.json",
            "analysis_completed.json",
            "frontier_completed.json",
            "review_completed.json",
        ):
            assert load(root / name)["status"] == "COMPLETE", name
        preserved = preservation(root)
        assert not workers(root)
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        failed = {j["name"] for j in jobs if j["exit_status"]}
        resolved = (
            load(root / "resolved_failures.json")
            if (root / "resolved_failures.json").exists()
            else {"failed_worker_jobs": []}
        )
        assert failed == set(resolved["failed_worker_jobs"])
        initial = load(root / "initial.json")
        exp = load(root / "experiment_completed.json")
        resources = {
            "wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": "from first preflight timestamp including orchestration",
            "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
            "measured_seal_cpu_seconds_before_archive": time.process_time() - started,
            "unmetered_orchestration_cpu_allowance_seconds": 600,
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "worker_jobs": len(jobs),
            "preserved_resolved_worker_failures": sorted(failed),
            "gpu_seconds": 0,
            "new_physical_rollouts": 0,
            "new_Cart_tree_fits": exp["new_tree_fits"],
            "reused_trees": exp["reused_trees"],
            "paid_api_calls": 0,
            "local_public_download_bytes": 0,
            "unmetered_primary_web_traffic_allowance_bytes": 20000000,
            "branch": git("branch", "--show-current"),
            "commit": git("rev-parse", "HEAD"),
            "push_attempted": False,
            "workers_remaining": workers(root),
            "preservation": preserved,
            "limits": initial["limits"],
            "scientific_gate": "PRELIMINARY_ONLY; METHOD_DISTINCTIVENESS_NOT_ESTABLISHED; no zero-error primary Pick claim",
        }
        assert (
            resources["wall_seconds"] < 14400
            and resources["measured_worker_cpu_seconds"] + 600 < 18000
        )
        save(root / "resources.json", resources)
        archive = root / "supervisor_review.tar.gz"
        selected = [
            p
            for p in root.rglob("*")
            if p.is_file()
            and "cache" not in p.relative_to(root).parts
            and p.suffix in (".json", ".jsonl", ".csv", ".md", ".txt", ".png", ".py")
            and p.name != "commands.jsonl"
        ]
        with tarfile.open(archive, "w:gz") as stream:
            for p in sorted(selected):
                stream.add(p, arcname="evidence/" + str(p.relative_to(root)))
            for p in maintained():
                stream.add(p, arcname="source/" + str(p))
        files = {
            str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()
        }
        size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        resources.update(
            artifact_bytes_before_seal=size,
            wall_seconds_at_seal=time.time() - initial["started_epoch"],
            measured_seal_cpu_seconds_total=time.process_time() - started,
        )
        assert size + 1000000 < 500000000 and resources["wall_seconds_at_seal"] < 14400
        assert (
            resources["measured_worker_cpu_seconds"]
            + resources["measured_seal_cpu_seconds_total"]
            + 600
            < 18000
        )
        save(
            root / "completion_manifest.json",
            {
                "status": "COMPLETE_PRELIMINARY_ONLY",
                "resources": resources,
                "sha256": files,
                "source_sha256": {str(p): sha(p) for p in maintained()},
                "archive_sha256": sha(archive),
                "archive_bytes": archive.stat().st_size,
                "no_authorization": "No new physics, manuscript, deployment calibration or push",
            },
        )
        print(
            json.dumps(
                {
                    "seal": str(root / "completion_manifest.json"),
                    "seal_sha256": sha(root / "completion_manifest.json"),
                    "resources": resources,
                }
            ),
            flush=True,
        )


def verify(root):
    manifest = load(root / "completion_manifest.json")
    for name, expected in manifest["sha256"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert sha(Path(name)) == expected, name
    preserved = preservation(root)
    assert not workers(root)
    print(
        json.dumps(
            {
                "status": "PASS_READ_ONLY_SEAL",
                "members": len(manifest["sha256"]),
                "preservation": preserved,
                "workers": [],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--authority", type=Path)
    parser.add_argument(
        "--stage", choices=("initialize", "seal", "verify"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists() and args.stage != "verify":
        raise SystemExit("Evidence sealed")
    if args.stage == "initialize":
        initialize(args.root, args.authority)
    elif args.stage == "seal":
        seal(args.root)
    else:
        verify(args.root)
