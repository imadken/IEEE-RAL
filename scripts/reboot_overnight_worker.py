"""One locked, foreground, bounded overnight worker with resource accounting."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

import psutil


def size(root):
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except FileNotFoundError:
            continue
    return total


def stop(child):
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()


def main():
    started_cpu = time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        initial = json.loads((root / "initial.json").read_text())
        limits = initial["limits"]
        reserve = initial.get(
            "reserve",
            {"wall_seconds": 2700, "cpu_seconds": 1800, "new_bytes": 100_000_000},
        )
        wall_ceiling = limits["wall_seconds"] - reserve["wall_seconds"]
        cpu_ceiling = limits["cpu_seconds"] - reserve["cpu_seconds"]
        disk_ceiling = limits["new_bytes"] - reserve["new_bytes"]
        rows = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        prior_cpu = sum(r["cpu_seconds"] for r in rows)
        argv = args.command[1:] if args.command[:1] == ["--"] else args.command
        if Path(args.name).name != args.name or not argv:
            parser.error("Local basename and a command required")
        env = os.environ | {
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "2",
            "OMP_WAIT_POLICY": "PASSIVE",
            "KMP_BLOCKTIME": "0",
            "NUMEXPR_NUM_THREADS": "1",
            "CUDA_VISIBLE_DEVICES": "",
            "UV_CACHE_DIR": str(root.resolve() / "cache/uv"),
            "TMPDIR": str(root.resolve() / "cache/tmp"),
            "MPLCONFIGDIR": str(root.resolve() / "cache/matplotlib"),
            "PYTEST_ADDOPTS": "-o cache_dir=" + str(root.resolve() / "cache/pytest"),
            "PYTHONPATH": "src:"
            + str(
                Path(
                    "results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages"
                ).resolve()
            ),
        }
        (root / "cache/tmp").mkdir(parents=True, exist_ok=True)
        source = {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("src", "scripts", "tests", "config")
            for p in Path(folder).rglob("*")
            if p.is_file() and p.suffix in (".py", ".json", ".txt")
        }
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        reason = None
        child = None
        try:
            with (root / (args.name + ".log")).open("x") as log:
                if (
                    prior_cpu >= cpu_ceiling
                    or time.time() - initial["started_epoch"] >= wall_ceiling
                    or size(root) >= disk_ceiling
                ):
                    raise ValueError("Reserved finalization resource boundary reached")
                child = subprocess.Popen(
                    argv,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                disk, next_check = 0, 0
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
                    if wall >= next_check:
                        disk = size(root)
                        next_check = wall + 10
                    if (
                        wall >= args.timeout
                        or cpu + prior_cpu >= cpu_ceiling
                        or time.time() - initial["started_epoch"] >= wall_ceiling
                        or disk >= disk_ceiling
                    ):
                        reason = "bounded_stop"
                        stop(child)
                        break
                    time.sleep(0.25)
        finally:
            if child is not None and child.poll() is None:
                stop(child)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = {
            "name": args.name,
            "command": argv,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime
            + time.process_time()
            - started_cpu,
            "max_rss_kib": after.ru_maxrss,
            "exit_status": 124 if reason else child.returncode,
            "reason": reason,
            "source_sha256": source,
            "log_sha256": hashlib.sha256(
                (root / (args.name + ".log")).read_bytes()
            ).hexdigest(),
        }
        with (root / "commands.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps({k: v for k, v in row.items() if k != "source_sha256"}))
        print((root / (args.name + ".log")).read_text()[-2000:])
        return row["exit_status"]


if __name__ == "__main__":
    raise SystemExit(main())
