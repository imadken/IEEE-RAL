"""Initialize and seal bounded v1.1 evidence without changing historical runs."""

import argparse
import fcntl
import hashlib
import json
import subprocess
import tarfile
import time
from pathlib import Path

import psutil


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def maintained():
    return [
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        *sorted(Path("scripts").glob("dsre_v11_*.py")),
        Path("scripts/dsre_experiment.py"),
        Path("scripts/dsre_audit.py"),
        Path("scripts/reboot_overnight_worker.py"),
        Path("scripts/explanation_repair_finish.py"),
        *sorted(Path("tests").glob("test_dsre_*.py")),
        Path("config/dsre_v11.json"),
        Path("config/dsre_stage1.json"),
        *sorted(Path("docs").glob("DSRE_V11_*.md")),
    ]


def initialize(root):
    root.mkdir(parents=True, exist_ok=False)
    config = load(Path("config/dsre_v11.json"))
    prior = Path(config["input_root"])
    names = (
        set(git("ls-files", "-z").split("\0"))
        | {str(p) for p in Path("docs").rglob("*") if p.is_file()}
        | {"DSRE_STAGE1_SUPERVISOR_CONTINUATION.md"}
    )
    save(
        root / "initial.json",
        {
            "started_epoch": time.time(),
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
            "base": git("rev-parse", "HEAD"),
            "initial_status": git("status", "--short"),
            "prior_files": {
                n: sha(Path(n)) if Path(n).is_file() else None
                for n in sorted(names)
                if n
            },
            "historical_seals": {
                str(p): sha(p)
                for p in Path("results").glob("**/completion_manifest.json")
            },
            "prior_run_members": {
                str(p): sha(p) for p in prior.rglob("*") if p.is_file()
            },
            "authority_sha256": sha(Path("DSRE_STAGE1_SUPERVISOR_CONTINUATION.md")),
        },
    )
    (root / "authority.md").write_bytes(
        Path("DSRE_STAGE1_SUPERVISOR_CONTINUATION.md").read_bytes()
    )
    (root / "commands.jsonl").write_text("")


def workers(root):
    current = psutil.Process()
    excluded = {current.pid, *[p.pid for p in current.parents()]}
    result = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = p.info["cmdline"] or []
            if (
                p.pid not in excluded
                and str(root) in argv
                and any(
                    Path(a).name.startswith("dsre_v11_")
                    or Path(a).name == "reboot_overnight_worker.py"
                    for a in argv
                )
            ):
                result.append(p.pid)
        except psutil.Error:
            pass
    return result


def preservation(root):
    initial = load(root / "initial.json")
    for category in ("prior_files", "historical_seals", "prior_run_members"):
        for name, expected in initial[category].items():
            path = Path(name)
            assert (sha(path) if path.is_file() else None) == expected, name
    freeze = load(root / "experiment_freeze.json")
    for category in ("source_sha256", "input_sha256"):
        for name, expected in freeze[category].items():
            assert sha(Path(name)) == expected, name
    return {
        k: len(initial[k])
        for k in ("prior_files", "historical_seals", "prior_run_members")
    }


def seal(root):
    started = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ("input_audit.json", "independent_audit.json", "validation.json"):
            assert load(root / name)["status"] == "PASS", name
        for name in (
            "experiment_completed.json",
            "analysis_completed.json",
            "review_completed.json",
        ):
            assert load(root / name)["status"] == "COMPLETE", name
        preserved = preservation(root)
        assert not workers(root)
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        failures = [j["name"] for j in jobs if j["exit_status"]]
        resolved = load(root / "resolved_failures.json")
        assert set(failures) == set(resolved["failed_worker_jobs"])
        initial = load(root / "initial.json")
        resources = {
            "wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": "from first preflight timestamp, including orchestration",
            "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
            "measured_seal_cpu_seconds_before_archive": time.process_time() - started,
            "unmetered_orchestration_cpu_allowance_seconds": 600,
            "unmeasured_interrupted_worker_cpu_allowance_seconds": 600,
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "gpu_seconds": 0,
            "new_physical_rollouts": 0,
            "new_model_fits": 0,
            "reused_saved_trees": 30,
            "paid_api_calls": 0,
            "local_public_download_bytes": 0,
            "unmetered_web_source_transfer_allowance_bytes": 20000000,
            "network_limit_bytes": 100000000,
            "worker_jobs": len(jobs),
            "resolved_worker_failures": failures,
            "workers_remaining": workers(root),
            "branch": git("branch", "--show-current"),
            "commit": git("rev-parse", "HEAD"),
            "push_attempted": False,
            "preservation": preserved,
            "limits": initial["limits"],
        }
        assert resources["wall_seconds"] < 14400
        assert (
            resources["measured_worker_cpu_seconds"]
            + resources["measured_seal_cpu_seconds_before_archive"]
            + 1200
            < 18000
        )
        save(root / "resources.json", resources)
        archive = root / "supervisor_review.tar.gz"
        selected = [
            p
            for p in root.rglob("*")
            if p.is_file()
            and "cache" not in p.relative_to(root).parts
            and p != archive
            and p.suffix in (".json", ".csv", ".md", ".png")
        ]
        with tarfile.open(archive, "w:gz") as stream:
            for p in sorted(selected):
                stream.add(p, arcname="evidence/" + str(p.relative_to(root)))
            for p in maintained():
                stream.add(p, arcname="source/" + str(p))
        files = {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and p.name != "completion_manifest.json"
        }
        total = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        assert total + 1000000 < 500000000
        resources.update(
            artifact_bytes_before_seal=total,
            measured_seal_cpu_seconds_total=time.process_time() - started,
            wall_seconds_at_seal=time.time() - initial["started_epoch"],
        )
        assert resources["wall_seconds_at_seal"] < 14400
        assert (
            resources["measured_worker_cpu_seconds"]
            + resources["measured_seal_cpu_seconds_total"]
            + 1200
            < 18000
        )
        save(
            root / "completion_manifest.json",
            {
                "status": "COMPLETE_PRELIMINARY_ONLY",
                "scientific_gate": "PRELIMINARY_ONLY; METHOD_DISTINCTIVENESS_UNRESOLVED",
                "resources": resources,
                "sha256": files,
                "source_sha256": {str(p): sha(p) for p in maintained()},
                "archive_sha256": sha(archive),
                "archive_bytes": archive.stat().st_size,
                "no_authorization": "No independent calibration, physics, model training, manuscript or push",
            },
        )
        print(
            json.dumps(
                {
                    "seal": str(root / "completion_manifest.json"),
                    "sha256": sha(root / "completion_manifest.json"),
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
    parser.add_argument(
        "--stage", choices=("initialize", "seal", "verify"), required=True
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists() and args.stage != "verify":
        raise SystemExit("Evidence sealed")
    {"initialize": initialize, "seal": seal, "verify": verify}[args.stage](args.root)
