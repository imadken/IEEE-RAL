"""Independent source-ruling audit: no collector or inference imports."""

import ast
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path


def read(path):
    with gzip.open(path, "rt") if path.suffix == ".gz" else path.open() as handle:
        return json.load(handle)


def compare(a, b):
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys()
        for key in a:
            compare(a[key], b[key])
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b)
        for x, y in zip(a, b):
            compare(x, y)
    elif isinstance(a, (int, float)):
        assert math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-10
    else:
        assert a == b


def main():
    root = Path("results/dsre-evidence-aware/20261118-source-eligibility")
    old = Path("results/dsre-evidence-aware/20261117-prospective")
    proof = read(root / "independent_source_reproductions.json")
    original = read(
        old / "physics/PegInsertionSide-v1/calibration/259/acquisition_screen.json.gz"
    )
    worker = Path("scripts/dsre_evidence_tasks.py")
    data = worker.read_bytes()
    assert data == subprocess.check_output(
        [
            "git",
            "show",
            proof["commit_before_physics"] + ":scripts/dsre_evidence_tasks.py",
        ]
    )
    tree = ast.parse(data)
    insertion = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "insertion"
    )
    first_action_read = min(
        n.lineno
        for n in ast.walk(insertion)
        if isinstance(n, ast.Name) and n.id == "action" and isinstance(n.ctx, ast.Load)
    )
    stage = next(
        i
        for i, line in enumerate(data.decode().splitlines(), 1)
        if "move(grasp * sapien.Pose([0, 0, -0.05]))" in line
    )
    assert stage < first_action_read
    checks = []
    for repetition in proof["reproductions"]:
        branch = read(Path(repetition["raw_path"]))
        receipt = repetition["receipt"]
        assert (
            receipt["command"][-2:] == ["--action", "screen"]
            and receipt["returncode"] == 0
        )
        assert receipt["source_sha256"] == hashlib.sha256(data).hexdigest()
        assert branch["spec"] == original["spec"] and branch["action"] == "screen"
        assert (
            branch["spec"]["seed"] == 180937078 and branch["spec"]["offset"] == -0.003
        )
        assert branch["status"] == "FAILED_PREREQUISITE_OR_PREFIX"
        assert (
            branch["error"] == "UPSTREAM_SCREW_PLANNING_FAILED"
            and branch["phase"] == "prefix"
        )
        assert f"line {stage}, in insertion" in branch["traceback"]
        assert (
            len(branch["prefix"]) == 1
            and not branch["prefix_controls"]
            and not branch["post_controls"]
        )
        assert all(
            branch.get(key) is None for key in ("checkpoint", "features", "success")
        )
        compare(original["prefix"][0], branch["prefix"][0])
        assert branch["prefix"][0]["elapsed"] == [0]
        checks.append(
            {
                "repeat": repetition["repeat"],
                "stage_line": stage,
                "full_initial_physical_controller_rng_agreement": True,
                "controls": 0,
                "executable_checkpoint": False,
                "action_outcome": None,
            }
        )
    for name, checksum in proof["source_fingerprints"].items():
        with Path(name).open("rb") as handle:
            assert hashlib.file_digest(handle, "sha256").hexdigest() == checksum
    assert not list(
        (old / "prospective/PegInsertionSide-v1/calibration").glob("*.json")
    )
    assert not list((old / "prospective/PegInsertionSide-v1/test").glob("*.json"))
    assert len(checks) == 2
    result = {
        "passed": True,
        "checks": checks,
        "source_fingerprints_verified": len(proof["source_fingerprints"]),
        "action_read_occurs_after_failed_stage": True,
        "assigned_calibration_and_test_outcomes_before_amendment": 0,
        "interpretation": "Two exact isolated native-planner failures, finite initial state and identical controller/RNG/source; no evidence of corruption, mismatch, wrong fault, endpoint/parity error or missing import. This qualifies only the zero-control predecision event, never post-control failure.",
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with (root / "independent_source_eligibility_audit.json").open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
