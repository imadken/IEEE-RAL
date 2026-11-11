"""Meter one bounded REBOOT worker, with isolated caches and immutable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import resource
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil
from recoverbench_qualification_command import new_files, worker_environment

_LOGGER = logging.getLogger(__name__)


def logical_bytes(root):
    total = 0
    for path in new_files(root):
        try:
            total += path.stat().st_size
        except FileNotFoundError:
            # Live pytest/uv temporary files can disappear during enumeration.
            continue
    return total


def stop_child(child):
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()


def budget_reason(initial, rows, *, cpu=0, size=0):
    if time.time() - initial["started_epoch"] >= 28800:
        return "campaign_wall_budget"
    if sum(r["cpu_seconds"] for r in rows) + cpu >= 35900:
        return "CPU_budget"
    if size >= 9_900_000_000:
        return "new_artifact_budget"
    return None


def main():
    driver_start = time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    if not args.name or Path(args.name).name != args.name:
        parser.error("Command name must be a local basename")
    initial = json.loads((root / "initial.json").read_text())
    ledger = root / "commands.jsonl"
    rows = (
        [json.loads(s) for s in ledger.read_text().splitlines()]
        if ledger.exists()
        else []
    )
    unmetered = root / "unmetered_commands.jsonl"
    if unmetered.exists():
        rows += [
            {"cpu_seconds": json.loads(line)["cpu_upper_bound_seconds"]}
            for line in unmetered.read_text().splitlines()
        ]
    reason = budget_reason(initial, rows, size=logical_bytes(root))
    if reason:
        raise SystemExit(reason)
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        parser.error("Missing command")
    source = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("src", "scripts", "tests", "config")
        for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix in {".py", ".json", ".txt"}
    }
    for name in (
        "REBOOT_PHASE_PROTOCOL.md",
        "REBOOT_PHASE_REPORT.md",
        "uv.lock",
        "pyproject.toml",
    ):
        path = Path(name)
        if path.exists():
            source[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    env = worker_environment(root) | {
        "UV_CACHE_DIR": str(root.resolve() / "cache/uv"),
        "TOKENIZERS_PARALLELISM": "false",
    }
    started = time.monotonic()
    utc_start = datetime.now(UTC).isoformat()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    log = root / (args.name + ".log")
    reason = None
    last_disk_check = 0
    disk = 0
    with log.open("x") as stream:
        child = subprocess.Popen(
            argv,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        try:
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
                if wall - last_disk_check > 2:
                    disk = logical_bytes(root)
                    last_disk_check = wall
                reason = budget_reason(
                    initial,
                    rows,
                    cpu=cpu + time.process_time() - driver_start,
                    size=disk,
                )
                if wall >= args.timeout:
                    reason = "command_timeout"
                if reason:
                    stop_child(child)
                    break
                time.sleep(0.25)
        except Exception as exc:
            reason = f"driver_error:{type(exc).__name__}"
            stop_child(child)
            _LOGGER.exception("Worker driver failed; child terminated")
            stream.write(f"\nWorker terminated after driver exception: {exc!r}\n")
        finally:
            if child.poll() is None:
                stop_child(child)
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
        - driver_start,
        "driver_cpu_seconds": time.process_time() - driver_start,
        "exit_status": 124 if reason else child.returncode,
        "termination_reason": reason,
        "source_sha256": source,
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
    print(log.read_text()[-1800:])
    return row["exit_status"]


if __name__ == "__main__":
    raise SystemExit(main())
