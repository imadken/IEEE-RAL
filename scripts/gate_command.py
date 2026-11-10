"""Run one bounded D5-D7 worker command and retain its exit/resource evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import shlex
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or Path(args.name).name != args.name or args.timeout <= 0:
        parser.error("Provide a safe command name, positive timeout and command")
    args.root.mkdir(parents=True, exist_ok=True)
    journal = args.root / "commands.jsonl"
    completed = (
        [json.loads(line) for line in journal.read_text().splitlines()]
        if journal.exists()
        else []
    )
    used_wall = sum(row["wall_seconds"] for row in completed)
    used_cpu = sum(
        row["cpu_user_seconds"] + row["cpu_system_seconds"] for row in completed
    )
    remaining_wall, remaining_cpu = 10800 - used_wall, 21600 - used_cpu
    if min(remaining_wall, remaining_cpu) < 30:
        raise SystemExit("D5-D7 worker budget exhausted")
    timeout = min(args.timeout, remaining_wall - 5)
    source = {
        str(p): sha256(p)
        for folder in ("src", "scripts", "tests")
        for p in sorted(Path(folder).rglob("*"))
        if p.suffix in (".py", ".sh")
    }
    for name in (
        "uv.lock",
        "pyproject.toml",
        "RESEARCH_PROTOCOL.md",
        "RESEARCH_EXECUTION_CONTRACT.md",
    ):
        if Path(name).exists():
            source[name] = sha256(Path(name))
    for config_path in sorted(Path("config").glob("*.json")):
        source[str(config_path)] = sha256(config_path)
    log = args.root / f"{args.name}.log"
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    utc_start = datetime.now(UTC).isoformat()
    started = time.monotonic()
    env = os.environ | dict.fromkeys(
        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"), "2"
    )

    # This executor is a short-lived process. Set its limit before spawning so
    # children inherit it without a preexec hook.
    cap = math.floor(remaining_cpu)
    resource.setrlimit(resource.RLIMIT_CPU, (cap - 1, cap))

    with log.open("x") as stream:
        process = subprocess.Popen(
            ["bash", "-c", "source scripts/env.sh\nexec " + shlex.join(command)],
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        timed_out = False
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            status = 124
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    hardware = args.root / "preflight" / "hardware.json"
    row = {
        "name": args.name,
        "command": command,
        "utc_start": utc_start,
        "utc_end": datetime.now(UTC).isoformat(),
        "exit_status": status,
        "timed_out": timed_out,
        "wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": usage.ru_utime,
        "cpu_system_seconds": usage.ru_stime,
        "max_rss_kib": usage.ru_maxrss,
        "source_commit": source_commit,
        "source_sha256": source,
        "log_sha256": sha256(log),
        "numerical_threads": 2,
        "versions": json.loads(hardware.read_text()).get("versions", {})
        if hardware.exists()
        else {},
        "seeds": "Exact seeds in command arguments and preregistered configuration; none implicit in executor",
    }
    with journal.open("a") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")
    if args.finalize:
        inventory = {
            str(path.relative_to(args.root)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(args.root.rglob("*"))
            if path.is_file() and path.name != "completion_manifest.json"
        }
        ledger = [json.loads(line) for line in journal.read_text().splitlines()]
        final = {
            "artifacts": inventory,
            "source_sha256": source,
            "source_commit": source_commit,
            "worker_wall_seconds": sum(item["wall_seconds"] for item in ledger),
            "cpu_core_hours": sum(
                item["cpu_user_seconds"] + item["cpu_system_seconds"] for item in ledger
            )
            / 3600,
        }
        (args.root / "completion_manifest.json").write_text(
            json.dumps(final, indent=2, allow_nan=False)
        )
    print(
        json.dumps(
            {
                k: row[k]
                for k in (
                    "name",
                    "exit_status",
                    "wall_seconds",
                    "cpu_user_seconds",
                    "cpu_system_seconds",
                )
            }
        ),
        flush=True,
    )
    print(log.read_text()[-1500:], flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
