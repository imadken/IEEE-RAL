"""Guard the qualified process configuration around the unchanged frozen runner."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from dsre_runtime_recovery import ENV_FIELDS, configured_environment, sha


def read(path):
    return json.loads(path.read_text())


def write_once(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def forensic_audit(root):
    folder = root / "diagnostics"
    baseline = read(folder / "prefix_host_baseline.json")
    corrected = read(folder / "prefix_host_lvp.json")
    assert baseline["returncode"] == -11 and corrected["returncode"] == 0
    before, after = (
        baseline["process_configuration"],
        corrected["process_configuration"],
    )
    assert {
        k for k in before.keys() | after.keys() if before.get(k) != after.get(k)
    } == {"VK_ICD_FILENAMES"}
    trace = (folder / "gdb_host_prefix.log").read_text()
    assert "received signal SIGSEGV" in trace
    assert all(
        name in trace
        for name in (
            "libcuda.so.1",
            "libnvidia-eglcore.so.550.163.01",
            "libvulkan.so.1",
        )
    )
    assert (
        "ptrace: Operation not permitted"
        in (folder / "gdb_exact_prefix.log").read_text()
    )
    comparison = read(root / "historical_source_comparison.json")
    assert comparison["historical_build_bytes_identical"]
    assert all(p["equal"] for p in comparison["files"])
    return {
        "passed": True,
        "native_fault_path": "NVIDIA CUDA/EGL via Vulkan discovery",
        "gdb_wrapper_status_does_not_equal_inferior_status": True,
        "one_factor_process_correction": "VK_ICD_FILENAMES=existing Lavapipe ICD",
        "precise_proprietary_driver_defect_or_update": "Not established",
        "diagnostic_sources": {
            str(p): sha(p) for p in sorted(folder.glob("*")) if p.is_file()
        },
        "epoch": time.time(),
    }


def register(root):
    qualification = read(root / "qualification_audit.json")
    assert qualification["passed"] and qualification["parents"] == 3
    assert qualification["additional_fresh_process_repetitions"] == 2
    assert qualification["counts"]["continuations"] == 50
    assert not (root / "first_parity_disagreement.json").exists()
    original = Path(read(root / "initial.json")["old_failed_root"])
    plan, old = read(root / "study_plan.json"), read(original / "study_plan.json")
    assert {k for k in plan if plan[k] != old[k]} == {
        "root",
        "qualification_seeds",
        "session_start_epoch",
    }
    assert not any((root / stage).iterdir() for stage in ())
    for stage in ("calibration", "test"):
        assert not list((root / stage).rglob("*.json*"))
    audit = forensic_audit(root)
    write_once(root / "native_forensic_audit.json", audit)
    config = read(root / "execution_configuration.json")
    env = configured_environment(config["overrides"])
    fixed = {
        str(root / name): sha(root / name)
        for name in (
            "qualification_audit.json",
            "source_freeze.json",
            "execution_configuration.json",
            "qualification_registration.json",
            "runtime_candidate_fingerprint.json",
            "study_plan.json",
            "frozen_routers.json",
            "seed_manifest.json",
            "native_forensic_audit.json",
        )
    }
    fixed[str(original / "completion_manifest.json")] = sha(
        original / "completion_manifest.json"
    )
    fixed[str(Path(__file__))] = sha(Path(__file__))
    seal = {
        "passed": True,
        "registered_before_fresh_parent_outcomes": True,
        "source_file_sha256": fixed,
        "process_configuration": {k: env.get(k) for k in ENV_FIELDS},
        "qualified_epoch": time.time(),
        "original_scientific_registration_preserved": True,
    }
    write_once(root / "source_qualification_seal.json", seal)
    probes = [read(p) for p in (root / "diagnostics").glob("*.json")]
    write_once(
        root / "metered/p0_native_and_parity.json",
        {
            "command": [
                "aggregate",
                "all bounded diagnostic/P0 children; individual records in diagnostics",
            ],
            "status": 0,
            "wall_seconds": sum(p["wall_seconds"] for p in probes),
            "cpu_seconds": sum(p["cpu_seconds"] for p in probes),
            "peak_child_rss_kib": max(p["peak_child_rss_kib"] for p in probes),
            "scope": "Child CPU included once; expected failed diagnostic configurations retained separately",
            "epoch": time.time(),
        },
    )
    return seal


def verify(root):
    seal = read(root / "source_qualification_seal.json")
    assert seal["passed"] and seal["registered_before_fresh_parent_outcomes"]
    for name, digest in seal["source_file_sha256"].items():
        assert sha(Path(name)) == digest, name
    config = read(root / "execution_configuration.json")
    env = configured_environment(config["overrides"])
    assert {k: env.get(k) for k in ENV_FIELDS} == seal["process_configuration"]
    from dsre_source_risk import verify as original_verify

    original_verify(root)
    return env


def run(root, stage):
    env = verify(root)
    assert not (root / "study_halt.json").exists()
    with (root / (stage + "_control.log")).open("a") as log:
        subprocess.run(
            [
                sys.executable,
                "scripts/dsre_source_risk.py",
                "control",
                str(root),
                "--stage",
                stage,
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    return {
        "stage": stage,
        "boundary": read(root / (stage + "_boundary.json"))
        if (root / (stage + "_boundary.json")).exists()
        else "INCOMPLETE",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "mode",
        choices=("register", "verify", "calibration", "test_screen", "test_outcome"),
    )
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.mode == "register":
        result = register(a.root)
    elif a.mode == "verify":
        verify(a.root)
        result = {"passed": True}
    else:
        result = run(a.root, a.mode)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("source_file_sha256", "process_configuration")
            }
        )
    )
