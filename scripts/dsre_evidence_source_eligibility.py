"""Reproduce the named source failure without changing the executable worker."""

import hashlib
import importlib.metadata
import json
import math
import subprocess
import time
from pathlib import Path

from dsre_evidence_campaign import child
from dsre_evidence_prospective import read

OLD = Path("results/dsre-evidence-aware/20261117-prospective")
ROOT = Path("results/dsre-evidence-aware/20261118-source-eligibility")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprints():
    result = {}
    for package in ("mani-skill", "mplib", "sapien"):
        distribution = importlib.metadata.distribution(package)
        for file in distribution.files or []:
            name = str(file)
            if name.endswith(".so") or (
                name.endswith(".py")
                and any(
                    s in name for s in ("peg_insertion", "motionplanner", "controllers")
                )
            ):
                path = Path(distribution.locate_file(file))
                if path.is_file():
                    result[str(path)] = sha(path)
    result["scripts/dsre_evidence_tasks.py"] = sha(
        Path("scripts/dsre_evidence_tasks.py")
    )
    return result


def differences(a, b, path="state"):
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            return [path + ": keys differ"]
        return [d for key in a for d in differences(a[key], b[key], path + "." + key)]
    if isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            return [path + ": length differs"]
        return [
            d
            for i, (x, y) in enumerate(zip(a, b))
            for d in differences(x, y, f"{path}[{i}]")
        ]
    if isinstance(a, (int, float)):
        if (
            not isinstance(b, (int, float))
            or not math.isfinite(a)
            or not math.isfinite(b)
            or abs(a - b) > 1e-10
        ):
            return [path + ": numeric difference or nonfinite value"]
        return []
    return [] if a == b else [path + ": value differs"]


def main():
    registration = read(ROOT / "resource_amendment_registration.json")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert head == registration["commit"]
    assert not list(
        (OLD / "prospective/PegInsertionSide-v1/calibration").glob("*.json")
    )
    before = fingerprints()
    versions = {
        name: importlib.metadata.version(name)
        for name in read(OLD / "runtime_versions.json")["main_versions"]
    }
    assert versions == read(OLD / "runtime_versions.json")["main_versions"]
    originalpath = (
        OLD / "physics/PegInsertionSide-v1/calibration/259/acquisition_screen.json.gz"
    )
    original = read(originalpath)
    spec = original["spec"]
    assert spec["seed"] == 180937078 and spec["offset"] == -0.003
    records = []
    for repeat in (1, 2):
        branch = child(ROOT, spec, "screen", f"independent_reproduction_{repeat}")
        path = (
            ROOT
            / "physics/PegInsertionSide-v1/calibration/259"
            / f"independent_reproduction_{repeat}.json.gz"
        )
        comparable = bool(branch.get("prefix")) and bool(original.get("prefix"))
        diff = (
            differences(original["prefix"][0], branch["prefix"][0])
            if comparable
            else ["initial state unavailable"]
        )
        passed = (
            branch["status"] == "FAILED_PREREQUISITE_OR_PREFIX"
            and branch.get("error") == "UPSTREAM_SCREW_PLANNING_FAILED"
            and branch.get("phase") == "prefix"
            and len(branch.get("prefix", [])) == 1
            and len(branch.get("prefix_controls", [])) == 0
            and not branch.get("post_controls")
            and branch.get("checkpoint") is None
            and branch.get("success") is None
            and branch.get("features") is None
            and not diff
            and branch["spec"] == spec
        )
        records.append(
            {
                "repeat": repeat,
                "passed": passed,
                "status": branch["status"],
                "error": branch.get("error"),
                "initial_state_differences": diff[:20],
                "prefix_controls": len(branch.get("prefix_controls", [])),
                "raw_path": str(path),
                "raw_sha256": sha(path),
                "receipt": read(
                    path.with_name(path.name.replace(".json.gz", ".execution.json"))
                ),
            }
        )
    assert fingerprints() == before
    worker = Path("scripts/dsre_evidence_tasks.py").read_text()
    stage = "move(grasp * sapien.Pose([0, 0, -0.05]))"
    assert stage in worker and "if isinstance(result, int) and result == -1:" in worker
    result = {
        "epoch": time.time(),
        "commit_before_physics": head,
        "source_fingerprints": before,
        "versions": versions,
        "source_eligibility_conditions_passed": all(r["passed"] for r in records),
        "reproductions": records,
        "original_raw_sha256": sha(originalpath),
        "failure_stage": "First pregrasp approach; dry-run screw planning before follow_path or env.step",
        "assignment_and_selection": "screen executes before any action branch; seeded initial source state/RNG checked against original; no calibration or test action outcomes exist",
        "amendment_required_before_any_new_action_outcome": True,
    }
    with (ROOT / "independent_source_reproductions.json").open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(
        json.dumps(
            {
                "source_eligibility_conditions_passed": result[
                    "source_eligibility_conditions_passed"
                ],
                "reproductions": records,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
