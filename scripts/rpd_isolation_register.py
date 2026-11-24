"""Prephysics source/executable/environment/failed-input registration, no simulator."""

import argparse
import importlib.metadata
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rpd_isolation_common import BASE, PRIOR, START, planned_jobs, sha, write_json


def snapshot():
    assert not BASE.exists()
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        == START
    )
    BASE.mkdir(parents=True)
    prior = json.loads((PRIOR / "preservation_before.json").read_text())
    for name, expected in prior["files"].items():
        assert (sha(name) if Path(name).is_file() else None) == expected, name
    files = set(prior["files"])
    files.update(
        subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    )
    metadata = dict(prior["historical_file_metadata"])
    for path in PRIOR.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            stat = path.stat()
            metadata[str(path)] = [stat.st_size, stat.st_mtime_ns]
    write_json(
        BASE / "preservation_before.json",
        {
            "head": START,
            "files": {
                p: sha(p) if Path(p).is_file() else None for p in sorted(files) if p
            },
            "historical_metadata": metadata,
            "started_epoch": time.time(),
            "original_user_status": json.loads(
                Path(
                    "research/rpd_method_challenge/preservation_before.json"
                ).read_text()
            )["status"],
        },
    )


def register():
    assert not (BASE / "prephysics_seal.json").exists()
    old = json.loads((PRIOR / "source_preflight.json").read_text())
    for name, expected in old["hashes"].items():
        assert sha(name) == expected, name
    for name, expected in old["versions"].items():
        assert importlib.metadata.version(name) == expected, name
    selected = planned_jobs()
    with (BASE / "jobs.jsonl").open("x") as stream:
        for job in selected:
            stream.write(job.model_dump_json() + "\n")
    (BASE / "debugger.gdb").write_text("""set pagination off
set confirm off
set print thread-events off
set disable-randomization off
set startup-with-shell off
run
python
import gdb
if gdb.selected_inferior().threads():
    for command in ("thread apply all bt", "py-bt"):
        try:
            gdb.execute(command)
        except gdb.error as error:
            gdb.write("Backtrace command unavailable: " + str(error) + "\\n")
end
quit
""")
    executable_paths = [
        Path(sys.executable),
        Path(sys.executable).resolve(),
        Path(shutil.which("gdb")),
        Path(shutil.which("uv")),
    ]
    environment = {
        key: os.environ.get(key)
        for key in (
            "PYTHONPATH",
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "UV_CACHE_DIR",
        )
    }
    assert environment["OPENBLAS_NUM_THREADS"] == environment["OMP_NUM_THREADS"] == "1"
    packet = {
        "registered_epoch": time.time(),
        "source_commit": START,
        "source_versions": old["versions"],
        "source_hashes": old["hashes"],
        "executables_sha256": {str(p): sha(p) for p in executable_paths},
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment": environment,
        "child_environment_additions": {
            "PYTHONFAULTHANDLER": "1",
            "XDG_CACHE_HOME": "/tmp/rpd-source-isolation-cache/{task}",
            "MPLCONFIGDIR": "/tmp/rpd-source-isolation-mpl/{task}",
        },
        "physics_configuration": "Unchanged PilotWorld/execute and all native source bytes. 20Hz,CPU,state_dict,pd_ee_delta_pos,max200,prefix65/53,registered10/20probe ticks,70macro ticks,90common deadline. No new env/controller/sensor/seed.",
        "process_change": "One original row per fresh Python OS process, under fresh GDB with ASLR unchanged. GDB traceback and Python faulthandler diagnostic only, no dynamics/step/reset/restore modifications.",
        "core_limit_inherited": list(resource.getrlimit(resource.RLIMIT_CORE)),
        "core_pattern": Path("/proc/sys/kernel/core_pattern").read_text().strip(),
        "gdb_preflight": "Sandbox ptrace denied; approved own-child debugger preflight outside sandbox exited0 with /bin/true. No physics used for that check.",
        "original_exits_and_pause": json.loads(
            (PRIOR / "native_process_exit_receipt.json").read_text()
        ),
        "pause_reason": "Native workers both stopped after38complete branches on39th start; no returned failed-row trace/backtrace. Cause unknown. Old guard/source status remains SOURCE_NOT_QUALIFIED.",
        "source_episodes": 4,
        "conditional_neutral_episodes": 24,
        "all_four_gate": "ALL four workers must exit0, return COMPLETE actual outcomes (not necessarily success), match original prefix/controller and original probe prefix, and match independent full-path cross-process repeats. Only then permit24controls.",
        "worker_seconds_per_task": 1200,
        "new_output_bytes_per_task": 100 * 1024**2,
        "reserve_output_bytes_before_each_row": 12 * 1024**2,
        "per_row_file_size_limit": 8 * 1024**2,
        "caps": "Count full debugger+Python startup/teardown wall per task. Forecast next row from max prior measured cost*1.5+2s; timeout remaining cap, kill whole worker process group on cap. Atomic row journals preserve interruption, never auto retry or replace.",
        "no_rerun": "Each job attempt once in this namespace; an interrupted started marker prohibits resuming that job. Original missing rows remain missing, with new linked technical evidence kept separately.",
        "scope": "Source engineering only, same already inspected parent0/task. Zero new independent parents, no10parent continuation, discovery, calibration or Stage2. No global source stability/H1/H2 finding from28episodes.",
        "full_input_hashes": [
            {
                "job_id": j.job_id,
                "row_id": j.row.row_id,
                "input": j.row.model_dump(mode="json"),
                "original_continue_path": j.original_continue_path,
                "original_continue_sha256": sha(j.original_continue_path),
            }
            for j in selected
        ],
    }
    write_json(BASE / "registration.json", packet)
    files = {str(p): sha(p) for p in Path("scripts").glob("rpd_isolation_*.py")}
    files.update(old["hashes"])
    files.update({str(p): sha(p) for p in executable_paths})
    for path in [
        *BASE.glob("supervisor/*"),
        BASE / "jobs.jsonl",
        BASE / "registration.json",
        BASE / "debugger.gdb",
        BASE / "prephysics_tests.txt",
        Path("tests/test_rpd_source_isolation.py"),
    ]:
        files[str(path)] = sha(path)
    for job in selected:
        files[job.original_continue_path] = sha(job.original_continue_path)
    # The entire existing pilot acquisition/audit source and original seal are immutable.
    for p in Path("scripts").glob("rpd_pilot_*.py"):
        files[str(p)] = sha(p)
    files[str(PRIOR / "prephysics_seal.json")] = sha(PRIOR / "prephysics_seal.json")
    write_json(
        BASE / "prephysics_seal.json",
        {"new_physics_so_far": 0, "files": files, "timestamp": time.time()},
    )
    print(
        json.dumps(
            {
                "registered_jobs": 28,
                "first_gate_jobs": 4,
                "conditional_jobs": 24,
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["snapshot", "register"])
    args = parser.parse_args()
    snapshot() if args.mode == "snapshot" else register()
