"""Meter bounded qualification workers without changing the sealed campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def budget_reason(rows, *, wall, cpu, size):
    if sum(r["wall_seconds"] for r in rows) + wall >= 18000:
        return "aggregate_worker_wall_budget"
    if sum(r["cpu_seconds"] for r in rows) + cpu >= 21600:
        return "CPU_budget"
    if size >= 3_950_000_000:
        return "new_artifact_budget"
    return None


def new_files(root):
    # Path.rglob does not descend directory symlinks to the verified old inputs.
    return [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]


def worker_environment(root):
    (root / "cache/tmp").mkdir(parents=True, exist_ok=True)
    return os.environ | {
        "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMBA_NUM_THREADS": "1",
        "MUJOCO_GL": "egl",
        "NUMBA_CACHE_DIR": str(root.resolve() / "cache/numba"),
        "MPLCONFIGDIR": str(root.resolve() / "cache/matplotlib"),
        "TMPDIR": str(root.resolve() / "cache/tmp"),
        "PYTEST_ADDOPTS": (
            os.environ.get("PYTEST_ADDOPTS", "")
            + " -o cache_dir="
            + str(root.resolve() / "cache/pytest")
        ).strip(),
    }


def main():
    driver_started = time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    if not args.name or Path(args.name).name != args.name:
        parser.error("Command name must be a local basename")
    ledger = root / "commands.jsonl"
    rows = (
        [json.loads(s) for s in ledger.read_text().splitlines()]
        if ledger.exists()
        else []
    )
    reason = budget_reason(
        rows, wall=0, cpu=0, size=sum(p.stat().st_size for p in new_files(root))
    )
    if reason:
        raise SystemExit(reason)
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        parser.error("Missing command")
    sources = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("src", "scripts", "tests", "config")
        for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix in {".py", ".json", ".txt"}
    }
    for name in (
        "RECOVERBENCH_TRANSFER_PROTOCOL.md",
        "RECOVERBENCH_TRANSFER_REPORT.md",
        "uv.lock",
    ):
        sources[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    env = worker_environment(root)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    utc_start = datetime.now(UTC).isoformat()
    log = root / (args.name + ".log")
    reason = None
    with log.open("x") as stream:
        child = subprocess.Popen(
            argv,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        while child.poll() is None:
            wall = time.monotonic() - started
            try:
                process = psutil.Process(child.pid)
                cpu = sum(
                    sum(p.cpu_times()[:2])
                    for p in [process, *process.children(recursive=True)]
                )
            except psutil.Error:
                cpu = 0
            reason = budget_reason(
                rows,
                wall=wall,
                cpu=cpu + time.process_time() - driver_started,
                size=sum(p.stat().st_size for p in new_files(root)),
            )
            if wall >= args.timeout:
                reason = "command_timeout"
            if reason:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                break
            time.sleep(0.25)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    row = {
        "name": args.name,
        "command": argv,
        "utc_start": utc_start,
        "utc_end": datetime.now(UTC).isoformat(),
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime
        + time.process_time()
        - driver_started,
        "driver_cpu_seconds": time.process_time() - driver_started,
        "exit_status": 124 if reason else child.returncode,
        "termination_reason": reason,
        "source_sha256": sources,
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "max_child_rss_kib": after.ru_maxrss,
    }
    with ledger.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print(
        json.dumps(
            {k: row[k] for k in ("name", "exit_status", "wall_seconds", "cpu_seconds")}
        )
    )
    print(log.read_text()[-1500:])
    return row["exit_status"]


if __name__ == "__main__":
    raise SystemExit(main())
