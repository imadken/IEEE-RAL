"""Bound and monitor one overnight worker; no detached or remote work."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def write_status(root: Path, payload: dict) -> None:
    temporary = root / "STATUS.tmp"
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False))
    temporary.replace(root / "STATUS.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or Path(args.name).name != args.name:
        parser.error("Invalid name or command")
    root = args.root
    initial = json.loads((root / "initial.json").read_text())
    journal = root / "commands.jsonl"
    rows = (
        [json.loads(line) for line in journal.read_text().splitlines()]
        if journal.exists()
        else []
    )
    used_cpu = sum(row["cpu_seconds"] for row in rows)
    status = (
        json.loads((root / "STATUS.json").read_text())
        if (root / "STATUS.json").exists()
        else {}
    )
    starts = status.get("stage_starts", {})
    family = (
        "D7B"
        if args.stage.startswith(("D7B", "PREREG_D7B"))
        else (
            "A"
            if args.stage.startswith("A_")
            else ("B" if args.stage.startswith("B_") else args.stage)
        )
    )
    starts.setdefault(family, time.time())
    stage_limit = (
        8100 if family == "D7B" else (14400 if family in ("A", "B") else 28800)
    )
    elapsed = time.time() - initial["started_epoch"]
    remaining = min(
        28800 - elapsed, stage_limit - (time.time() - starts[family]), args.timeout
    )
    if (
        remaining < 10
        or used_cpu >= 43200 - 30
        or artifact_bytes(root) >= 7_500_000_000
    ):
        raise SystemExit("Overnight budget boundary reached before worker launch")
    versions = {}
    hardware = root / "preflight/hardware.json"
    if hardware.exists():
        versions = json.loads(hardware.read_text()).get("versions", {})
    source = {
        str(p): digest(p)
        for directory in ("src", "scripts", "tests", "config")
        for p in sorted(Path(directory).rglob("*"))
        if p.suffix in (".py", ".sh", ".json")
    }
    for name in (
        "uv.lock",
        "pyproject.toml",
        "DUAL_REC_OVERNIGHT_CODEX_PROMPT.md",
        "RESEARCH_PROTOCOL.md",
        "GATE_REPORTS.md",
    ):
        if Path(name).exists():
            source[name] = digest(Path(name))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    cpu_cap = math.floor(43200 - used_cpu)
    _, hard = resource.getrlimit(resource.RLIMIT_CPU)
    if hard != resource.RLIM_INFINITY:
        cpu_cap = min(cpu_cap, hard)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_cap - 1, cpu_cap))
    utc_start = datetime.now(UTC).isoformat()
    started = time.monotonic()
    log = root / (args.name + ".log")
    env = os.environ | dict.fromkeys(
        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"), "2"
    )
    # env.sh has only trusted repository configuration; command argv stays argv.
    import shlex

    with log.open("x") as stream:
        process = subprocess.Popen(
            ["bash", "-c", "source scripts/env.sh\nexec " + shlex.join(command)],
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        reason = None
        last_disk_check = 0.0
        disk = artifact_bytes(root)
        while process.poll() is None:
            active_cpu = 0.0
            try:
                processes = [psutil.Process(process.pid)] + psutil.Process(
                    process.pid
                ).children(recursive=True)
                active_cpu = sum(
                    sum(p.cpu_times()[:2]) for p in processes if p.is_running()
                )
            except psutil.Error:
                pass
            now = time.monotonic()
            if now - last_disk_check > 5:
                disk = artifact_bytes(root)
                last_disk_check = now
            if now - started >= remaining:
                reason = "wall_or_stage_timeout"
            if used_cpu + active_cpu >= 43170:
                reason = "CPU_budget"
            if disk >= 7_500_000_000:
                reason = "artifact_budget"
            heartbeat = {
                "utc": datetime.now(UTC).isoformat(),
                "stage": args.stage,
                "run_id": root.name,
                "active_pid": process.pid,
                "running": True,
                "stage_starts": starts,
                "total_wall_seconds": time.time() - initial["started_epoch"],
                "total_cpu_seconds": used_cpu + active_cpu,
                "new_artifact_bytes": disk,
                "provisional_gate_status": "RUNNING",
                "pending_work": "Finish current bounded worker and follow preregistered decision graph",
            }
            write_status(root, heartbeat)
            if reason:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(0.5)
        status_code = 124 if reason else process.wait()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    row = {
        "name": args.name,
        "stage": args.stage,
        "command": command,
        "utc_start": utc_start,
        "utc_end": datetime.now(UTC).isoformat(),
        "exit_status": status_code,
        "termination_reason": reason,
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": usage.ru_utime + usage.ru_stime,
        "max_rss_kib": usage.ru_maxrss,
        "git_commit": commit,
        "source_sha256": source,
        "log_sha256": digest(log),
        "versions": versions,
        "numerical_threads": 2,
    }
    with journal.open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")
    completed_now = [json.loads(line) for line in journal.read_text().splitlines()]
    other_workers = []
    own_processes = {os.getpid()} | {
        parent.pid for parent in psutil.Process(os.getpid()).parents()
    }
    for candidate in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = candidate.info["cmdline"] or []
            if (
                candidate.pid not in own_processes
                and "scripts/overnight_command.py" in argv
                and str(root) in argv
            ):
                other_workers.append(candidate.pid)
        except psutil.Error:
            continue
    final_status = {
        "utc": row["utc_end"],
        "stage": args.stage,
        "run_id": root.name,
        "active_pid": other_workers[0] if other_workers else None,
        "active_worker_pids": other_workers,
        "running": bool(other_workers),
        "stage_starts": starts,
        "total_wall_seconds": time.time() - initial["started_epoch"],
        "worker_wall_seconds": sum(r["wall_seconds"] for r in completed_now),
        "total_cpu_seconds": sum(r["cpu_seconds"] for r in completed_now),
        "new_artifact_bytes": artifact_bytes(root),
        "provisional_gate_status": "WORKER_PASSED"
        if status_code == 0
        else "WORKER_FAILED",
        "pending_work": "Follow the saved stage gate; never infer scientific success from process exit alone",
    }
    write_status(root, final_status)
    with (root / "progress.jsonl").open("a") as stream:
        stream.write(json.dumps(final_status) + "\n")
    if args.finalize:
        if other_workers:
            raise RuntimeError(
                "Cannot finalize while another bounded worker is running"
            )
        final_status.update(
            stage="COMPLETE",
            provisional_gate_status="SEE_SCIENTIFIC_REPORT",
            pending_work="Manual publication only",
            STOPPED_WITHIN_AUTHORIZED_BOUNDARY=True,
        )
        write_status(root, final_status)
        manifest = {
            "artifacts": {
                str(p.relative_to(root)): {
                    "sha256": digest(p),
                    "bytes": p.stat().st_size,
                }
                for p in sorted(root.rglob("*"))
                if p.is_file() and p.name != "completion_manifest.json"
            },
            "source_sha256": source,
            "source_commit": commit,
            "resources": final_status,
        }
        (root / "completion_manifest.json").open("x").write(
            json.dumps(manifest, indent=2, allow_nan=False)
        )
    print(
        json.dumps(
            {
                k: row[k]
                for k in ("name", "stage", "exit_status", "wall_seconds", "cpu_seconds")
            }
        ),
        flush=True,
    )
    print(log.read_text()[-1800:], flush=True)
    return status_code


if __name__ == "__main__":
    raise SystemExit(main())
