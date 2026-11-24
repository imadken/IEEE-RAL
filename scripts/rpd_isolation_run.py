"""Bounded parent-side launcher: four isolated cases, then24 controls only on parity."""

import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

from rpd_isolation_audit import first_gate
from rpd_isolation_common import BASE, jobs, sha, verify_registration, write_json


def affordable(spent, previous, output_bytes):
    reserve = max(previous, default=0) * 1.5 + 2
    return spent + reserve < 1200 and output_bytes + 12 * 1024**2 <= 100 * 1024**2


def kill_tree(process):
    descendants = []

    def collect(pid):
        path = Path(f"/proc/{pid}/task/{pid}/children")
        try:
            children = [int(v) for v in path.read_text().split()]
        except FileNotFoundError:
            return
        for child in children:
            collect(child)
            descendants.append(child)

    collect(process.pid)
    for pid in [*descendants, process.pid]:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def run_one(job):
    task = job.row.parent.task
    directory = BASE / "physics" / task / job.job_id
    assert not directory.exists(), (
        "Each source attempt once; never auto-retry an interrupted job"
    )
    directory.mkdir(parents=True)
    previous = [
        json.loads(p.read_text())
        for p in (BASE / "physics" / task).glob("*/process.json")
    ]
    spent = sum(p["wall_seconds"] for p in previous)
    byte_count = sum(
        p.stat().st_size for p in (BASE / "physics" / task).rglob("*") if p.is_file()
    )
    if not affordable(spent, [p["wall_seconds"] for p in previous], byte_count):
        write_json(
            directory / "not_run.json",
            {
                "reason": "CAP_FORECAST_AT_ATOMIC_BOUNDARY",
                "spent_seconds": spent,
                "bytes": byte_count,
            },
        )
        return False
    env = dict(
        os.environ,
        PYTHONFAULTHANDLER="1",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
        XDG_CACHE_HOME=f"/tmp/rpd-source-isolation-cache/{task}",
        MPLCONFIGDIR=f"/tmp/rpd-source-isolation-mpl/{task}",
    )
    command = [
        "/usr/bin/gdb",
        "--batch",
        "--nx",
        "--quiet",
        "--return-child-result",
        "-x",
        str(BASE / "debugger.gdb"),
        "--args",
        sys.executable,
        "-X",
        "faulthandler",
        "scripts/rpd_isolation_worker.py",
        "--job-id",
        job.job_id,
    ]
    write_json(
        directory / "started.json",
        {
            "job": job.model_dump(mode="json"),
            "command": command,
            "epoch": time.time(),
            "row_input_sha256": sha(BASE / "jobs.jsonl"),
            "one_row_per_process": True,
        },
    )
    started = time.monotonic()
    timed_out = False
    with (directory / "debugger_and_worker.txt").open("x") as log:
        old_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024**2, old_limit[1]))
        try:
            process = subprocess.Popen(
                command,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            resource.setrlimit(resource.RLIMIT_FSIZE, old_limit)
        try:
            process.wait(timeout=max(0.001, 1200 - spent - 1))
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(process)
    wall = time.monotonic() - started
    text = (directory / "debugger_and_worker.txt").read_text(errors="replace")
    receipt = {
        "job_id": job.job_id,
        "returncode": process.returncode,
        "timed_out": timed_out,
        "wall_seconds": wall,
        "native_SIGSEGV_observed": "SIGSEGV" in text,
        "debugger_log_sha256": sha(directory / "debugger_and_worker.txt"),
        "gdb_pid": process.pid,
        "remaining_task_seconds": 1200 - spent - wall,
        "backtrace_status": "Captured in debugger log if inferior stopped; no failure replay to collect a backtrace",
        "new_independent_parents": 0,
    }
    write_json(directory / "process.json", receipt)
    print(
        json.dumps(
            {
                "task": task,
                "phase": job.phase,
                "replica": job.isolation_replica,
                "history": job.row.history,
                "endpoint": job.row.endpoint,
                "returncode": process.returncode,
                "wall_seconds": round(wall, 3),
            }
        ),
        flush=True,
    )
    assert spent + wall <= 1200, "Hard task worker cap exceeded; preserve actual cost"
    assert (
        sum(
            p.stat().st_size
            for p in (BASE / "physics" / task).rglob("*")
            if p.is_file()
        )
        <= 100 * 1024**2
    )
    return not timed_out


def run():
    verify_registration()
    planned = jobs()
    for job in [j for j in planned if j.phase == "failed_row_replay"]:
        run_one(job)
    gate = first_gate()
    write_json(BASE / "four_row_gate.json", gate)
    print("GLOBAL_GATE", gate["passed"], flush=True)
    if gate["passed"]:
        stopped = set()
        for job in [j for j in planned if j.phase == "neutral_control"]:
            if job.row.parent.task in stopped:
                continue
            if not run_one(job):
                stopped.add(job.row.parent.task)
    write_json(
        BASE / "execution_complete.json",
        {
            "four_row_gate": gate["passed"],
            "full_pilot_or_stage2_resumed": False,
            "stop": "End of authorized microprotocol; no further physics",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()
