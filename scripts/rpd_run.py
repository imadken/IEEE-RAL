"""Freeze and execute the bounded offline RPD challenge checks, never physics."""

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("research/rpd_method_challenge")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output):
    before = json.loads((BASE / "preservation_before.json").read_text())
    registration = json.loads((BASE / "registration.json").read_text())
    assert (
        registration["no_new_physics"]
        and time.time() - before["started_epoch"] < 48 * 3600
    )
    assert not output.exists(), "Fresh output required"
    output.mkdir(parents=True)
    (output / "logs").mkdir()
    code = sorted(Path("src/dual_rec/recoverability").glob("*.py"))
    code += [
        Path("scripts") / n
        for n in (
            "rpd_cases.py",
            "rpd_baselines.py",
            "rpd_independent_oracle.py",
            "rpd_audit.py",
            "rpd_source_audit.py",
            "rpd_stage2_protocol.py",
            "rpd_run.py",
        )
    ]
    code.append(Path("tests/test_recoverability_planner.py"))
    freeze = {
        "code_sha256": {str(p): sha(p) for p in code},
        "registration_sha256": sha(BASE / "registration.json"),
        "base_commit": registration["base_commit"],
        "created_epoch": time.time(),
    }
    (output / "code_freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
    environment = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    start = time.perf_counter()
    steps = []
    commands = [
        (
            "finite_planner_and_independent_oracles",
            ["scripts/rpd_audit.py", "--output", str(output / "finite")],
        ),
        (
            "static_native_source_and_adapter_audit",
            ["scripts/rpd_source_audit.py", "--output", str(output / "source")],
        ),
        (
            "inactive_stage2_reservation",
            ["scripts/rpd_stage2_protocol.py", "--output", str(output / "stage2")],
        ),
        (
            "focused_tests",
            ["-m", "pytest", "-q", "tests/test_recoverability_planner.py"],
        ),
        ("maintained_tests", ["-m", "pytest", "-q", "tests"]),
    ]
    for label, args in commands:
        began = time.perf_counter()
        log = output / "logs" / (label + ".txt")
        print("START", label, flush=True)
        with log.open("w") as stream:
            result = subprocess.run(
                [sys.executable, *args],
                env=environment,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=1800,
                check=False,
            )
        steps.append(
            {
                "name": label,
                "args": args,
                "returncode": result.returncode,
                "wall_seconds": time.perf_counter() - began,
                "log_sha256": sha(log),
            }
        )
        (output / "execution_steps.json").write_text(json.dumps(steps, indent=2) + "\n")
        assert result.returncode == 0, f"See {log}"
        assert (
            time.perf_counter() - start < registration["max_offline_experiment_seconds"]
        )
        print("PASS", label, flush=True)
    assert all(sha(name) == digest for name, digest in freeze["code_sha256"].items())
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {
        "passed": True,
        "steps": steps,
        "wall_seconds": time.perf_counter() - start,
        "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "new_physics": 0,
        "new_robot_outcomes": 0,
        "new_calibrated_physical_predicates": 0,
        "manuscript_edits": 0,
        "output_bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),
        "scope": "Finite analytical checks, static source binding and inactive proposed protocol",
    }
    (output / "run_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=BASE / "final")
    run(parser.parse_args().output)
