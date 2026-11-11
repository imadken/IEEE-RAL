"""Run one bounded RecoverBench campaign command and retain exact resource evidence."""

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


def main() -> int:
    driver_cpu_started = time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    if Path(args.name).name != args.name:
        parser.error("Command name must be a filename")
    initial = json.loads((root / "initial.json").read_text())
    journal = root / "commands.jsonl"
    rows = (
        [json.loads(s) for s in journal.read_text().splitlines()]
        if journal.exists()
        else []
    )
    cpu_used = sum(r["cpu_seconds"] for r in rows)
    if time.time() - initial["started_epoch"] >= 28800 or cpu_used >= 43100:
        raise SystemExit("Campaign resource boundary")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Missing command")
    source = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("src/dual_rec", "scripts", "tests", "config")
        for p in sorted(Path(folder).rglob("*"))
        if p.is_file() and p.suffix in {".py", ".json"}
    }
    for p in (
        Path("RECOVERBENCH_TRANSFER_PROTOCOL.md"),
        Path("uv.lock"),
        Path("pyproject.toml"),
    ):
        if p.exists():
            source[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    started = time.monotonic()
    utc = datetime.now(UTC).isoformat()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    env = os.environ | {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    timeout = min(
        args.timeout, max(1, 28800 - (time.time() - initial["started_epoch"]))
    )
    log = root / (args.name + ".log")
    with log.open("x") as stream:
        process = subprocess.Popen(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        reason = None
        before_disk_check = 0.0
        while process.poll() is None:
            now = time.monotonic()
            if now - started >= timeout:
                reason = "timeout"
            try:
                worker = psutil.Process(process.pid)
                workers = [worker, *worker.children(recursive=True)]
                active_cpu = sum(
                    sum(p.cpu_times()[:4]) for p in workers if p.is_running()
                )
                if cpu_used + active_cpu >= 43100:
                    reason = "CPU_budget"
            except psutil.Error:
                pass
            if now - before_disk_check >= 2:
                # Include the isolated environment and download cache in the run.
                # Counting logical hardlinks twice is conservative during workers.
                disk = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                if disk >= 11_800_000_000:
                    reason = "artifact_budget"
                before_disk_check = now
            if reason:
                break
            time.sleep(0.2)
        if reason:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
        else:
            code = process.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    row = {
        "name": args.name,
        "command": command,
        "utc_start": utc,
        "utc_end": datetime.now(UTC).isoformat(),
        "exit_status": code,
        "termination_reason": reason,
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime
        + time.process_time()
        - driver_cpu_started,
        "driver_cpu_seconds": time.process_time() - driver_cpu_started,
        "max_rss_kib": after.ru_maxrss,
        "source_sha256": source,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    }
    with journal.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print(
        json.dumps(
            {k: row[k] for k in ("name", "exit_status", "wall_seconds", "cpu_seconds")}
        )
    )
    print(log.read_text()[-3000:])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
