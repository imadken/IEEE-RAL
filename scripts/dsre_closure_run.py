"""Execute the fixed offline closure in E0--E5 order; launch no simulator."""

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path


def run(output, *, reproduction=False):
    repository = Path.cwd()
    registration_path = (
        repository / "research/dsre_experimental_closure/registration.json"
    )
    registration = json.loads(registration_path.read_text())
    original_start = json.loads(
        (registration_path.parent / "preservation_before.json").read_text()
    )["started_epoch"]
    assert registration["new_physics_allowed"] is False
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / "analysis_code_freeze.json").exists(), (
        "Use a fresh output directory; sealed outputs are immutable"
    )
    (output / "registration.json").write_bytes(registration_path.read_bytes())
    environment = dict(
        os.environ,
        DSRE_CLOSURE_OUTPUT=str(output),
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )

    def digest(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    scripts = [
        *Path("scripts").glob("dsre_closure_*.py"),
        Path("tests/test_dsre_closure.py"),
    ]
    freeze = {
        "created_epoch": time.time(),
        "base_commit": registration["base_commit"],
        "code_sha256": {str(p): digest(p) for p in sorted(scripts)},
        "new_physics": 0,
        "new_controller_fits": 0,
    }
    (output / "analysis_code_freeze.json").write_text(
        json.dumps(freeze, indent=2) + "\n"
    )
    logs = output / "run_logs"
    logs.mkdir(exist_ok=True)
    steps = []
    start = time.time()
    budget_origin = start if reproduction else original_start

    def execute(label, args):
        remaining = 12 * 3600 - (time.time() - budget_origin)
        assert remaining > 0, "Original 12-hour wall-time ceiling reached"
        print("START", label, flush=True)
        began = time.time()
        with (logs / (label + ".txt")).open("w") as stream:
            result = subprocess.run(
                [sys.executable, *args],
                check=False,
                env=environment,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=remaining,
            )
        steps.append(
            {
                "phase": label,
                "args": args,
                "started_epoch": began,
                "completed_epoch": time.time(),
                "wall_seconds": time.time() - began,
                "returncode": result.returncode,
                "log_sha256": digest(logs / (label + ".txt")),
            }
        )
        (output / "execution_steps.json").write_text(json.dumps(steps, indent=2) + "\n")
        assert result.returncode == 0, f"{label}: inspect {logs / (label + '.txt')}"
        size = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        assert size <= registration["max_new_artifact_bytes"]
        print("PASS", label, flush=True)

    execute(
        "E0_native_final",
        [
            "scripts/dsre_last_audit.py",
            "--compact",
            "--output",
            str(output / "E0/final_native_source_audit.json"),
        ],
    )
    execute(
        "E0_grasp_original",
        [
            "scripts/dsre_evidence_prospective_audit.py",
            "results/dsre-evidence-aware/20261117-prospective",
            "--task",
            "PickCube-v1",
            "--output",
            str(output / "E0/grasp_original_physics_audit.json"),
        ],
    )
    execute(
        "E0_navigation_original",
        [
            "scripts/dsre_evidence_prospective_audit.py",
            "results/dsre-evidence-aware/20261117-prospective",
            "--task",
            "PointMaze_UMaze-v3",
            "--output",
            str(output / "E0/navigation_original_physics_audit.json"),
        ],
    )
    recount = "import dsre_stage1_verify_numbers as audit; from pathlib import Path; import os; audit.OUT=Path(os.environ['DSRE_CLOSURE_OUTPUT'])/'E0/recount'; audit.main()"
    execute("E0_independent_recount", ["-c", recount])
    execute("E0_math", ["scripts/dsre_closure_math.py"])
    execute("E0_original_integrity", ["scripts/dsre_closure_integrity.py"])
    execute(
        "E0_checkpoint_and_parent_identity", ["scripts/dsre_closure_checkpoints.py"]
    )
    execute("E1_calibration_only", ["scripts/dsre_closure_calibrate.py"])
    execute("E1_obligation_scores", ["scripts/dsre_closure_evaluate.py", "obligations"])
    execute(
        "E2_source_materialization", ["scripts/dsre_closure_sources.py", "materialize"]
    )
    execute("E2_isolated_source_fits", ["scripts/dsre_closure_sources.py", "learn"])
    execute(
        "E3_selection_materialization", ["scripts/dsre_closure_sample.py", "prepare"]
    )
    execute("E3_isolated_case_selection", ["scripts/dsre_closure_sample.py", "select"])
    execute(
        "E3_complete_certificates", ["scripts/dsre_closure_evaluate.py", "certificates"]
    )
    execute(
        "E4_mechanism_falsification", ["scripts/dsre_closure_evaluate.py", "mechanisms"]
    )
    execute(
        "E5_error_box_sensitivity", ["scripts/dsre_closure_evaluate.py", "sensitivity"]
    )
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {
        "passed": True,
        "steps": len(steps),
        "wall_seconds": time.time() - start,
        "cumulative_contract_wall_seconds": time.time() - original_start,
        "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "new_physics_processes": 0,
        "controller_training_runs": 0,
        "artifact_bytes": sum(
            p.stat().st_size for p in output.rglob("*") if p.is_file()
        ),
        "sampling_scope": "Audits and retrospective analyses only; no new prospective experiment",
        "execution_mode": "OFFLINE_REPRODUCTION"
        if reproduction
        else "CONTRACT_CLOSURE",
        "wall_budget_origin": budget_origin,
    }
    (output / "run_complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("research/dsre_experimental_closure/final")
    )
    parser.add_argument(
        "--reproduction",
        action="store_true",
        help="Offline verification only, with a new 12h invocation bound; never authorizes outcomes or physics",
    )
    args = parser.parse_args()
    run(args.output, reproduction=args.reproduction)
