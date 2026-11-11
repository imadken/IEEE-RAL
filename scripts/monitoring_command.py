"""Run one bounded monitoring-study command and retain exact resource evidence."""

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


def main() -> int:
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
    rows = [json.loads(s) for s in journal.read_text().splitlines()] if journal.exists() else []
    cpu_used = sum(r["cpu_seconds"] for r in rows)
    if time.time() - initial["started_epoch"] >= 21600 or cpu_used >= 28700:
        raise SystemExit("Campaign resource boundary")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Missing command")
    source = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ("src/dual_rec/monitoring", "scripts", "tests", "config")
        for p in sorted(Path(folder).rglob("*"))
        if p.is_file() and p.suffix in {".py", ".json"}
    }
    for p in (Path("MONITORING_STUDY_PROTOCOL.md"), Path("uv.lock"), Path("pyproject.toml")):
        if p.exists():
            source[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    started = time.monotonic()
    utc = datetime.now(UTC).isoformat()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    env = os.environ | {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    timeout = min(args.timeout, max(1, 21600 - (time.time() - initial["started_epoch"])))
    log = root / (args.name + ".log")
    with log.open("x") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        reason = None
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            reason = "timeout"
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    row = {
        "name": args.name, "command": command, "utc_start": utc,
        "utc_end": datetime.now(UTC).isoformat(), "exit_status": code,
        "termination_reason": reason, "wall_seconds": time.monotonic() - started,
        "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        "max_rss_kib": after.ru_maxrss, "source_sha256": source,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    }
    with journal.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print(json.dumps({k: row[k] for k in ("name", "exit_status", "wall_seconds", "cpu_seconds")}))
    print(log.read_text()[-3000:])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
