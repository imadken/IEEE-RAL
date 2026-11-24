"""Bounded offline ERR verification in a fresh output directory; no physics."""

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path


def run(output, *, maintained_tests=True):
    base = Path("research/err_method_challenge")
    registration = json.loads((base / "registration.json").read_text())
    original = json.loads((base / "preservation_before.json").read_text())
    assert time.time() - original["started_epoch"] < 48 * 3600
    assert registration["physics"] is False
    assert not output.exists(), (
        "Use a fresh output directory; do not overwrite evidence"
    )
    output.mkdir(parents=True)
    logs = output / "logs"
    logs.mkdir()
    files = [
        Path("src/dual_rec/evidence_aware") / name
        for name in (
            "experiment_schema.py",
            "experiment_resolvability.py",
            "evidence_resolution.py",
        )
    ]
    files += [
        Path("scripts") / name
        for name in (
            "err_cases.py",
            "err_independent_oracle.py",
            "err_method_audit.py",
            "err_robot_witnesses.py",
            "err_stage2_manifest.py",
            "err_run.py",
        )
    ]
    files.append(Path("tests/test_experiment_resolvability.py"))

    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    freeze = {
        "base_commit": registration["base_commit"],
        "created_epoch": time.time(),
        "scientific_code_sha256": {str(p): sha(p) for p in files},
        "registration_sha256": sha(base / "registration.json"),
    }
    (output / "scientific_code_freeze.json").write_text(
        json.dumps(freeze, indent=2) + "\n"
    )
    environment = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    start = time.perf_counter()
    steps = []

    def execute(label, args):
        print("START", label, flush=True)
        began = time.perf_counter()
        with (logs / (label + ".txt")).open("w") as stream:
            result = subprocess.run(
                [sys.executable, *args],
                check=False,
                env=environment,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=7200,
            )
        steps.append(
            {
                "label": label,
                "args": args,
                "returncode": result.returncode,
                "wall_seconds": time.perf_counter() - began,
                "log_sha256": sha(logs / (label + ".txt")),
            }
        )
        (output / "execution_steps.json").write_text(json.dumps(steps, indent=2) + "\n")
        assert result.returncode == 0, label
        assert time.perf_counter() - start < 10800
        assert (
            sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) < 500000000
        )
        print("PASS", label, flush=True)

    execute(
        "exact_models_and_oracles",
        ["scripts/err_method_audit.py", "--output", str(output / "finite_models")],
    )
    execute(
        "D_C_only_robot_witnesses",
        ["scripts/err_robot_witnesses.py", "--output", str(output / "robot")],
    )
    execute(
        "inactive_future_parent_reservation",
        [
            "scripts/err_stage2_manifest.py",
            "--output",
            str(output / "stage2_reservation"),
        ],
    )
    execute(
        "focused_tests",
        ["-m", "pytest", "-q", "tests/test_experiment_resolvability.py"],
    )
    if maintained_tests:
        execute("maintained_tests", ["-m", "pytest", "-q", "tests"])
    for path, expected in freeze["scientific_code_sha256"].items():
        assert sha(path) == expected, f"Code changed during verification: {path}"
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {
        "passed": True,
        "steps": steps,
        "wall_seconds": time.perf_counter() - start,
        "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "new_physics": 0,
        "new_controller_training": 0,
        "new_robot_outcomes": 0,
        "output_bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),
        "source_guard": "Only the D/C robot-witness subprocess fits/queries source examples; source audits/evaluator views are isolated",
        "scope": "Finite-model method verification and retrospective source capabilities, not a new prospective physical experiment",
    }
    (output / "run_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("research/err_method_challenge/final")
    )
    parser.add_argument(
        "--focused-only",
        action="store_true",
        help="Reproduction may omit the already passed maintained suite",
    )
    args = parser.parse_args()
    run(args.output, maintained_tests=not args.focused_only)
