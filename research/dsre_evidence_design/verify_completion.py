"""Verify the final extracted study bundle without running physics."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)
    inventory = json.loads(Path("COMPLETION_MANIFEST.json").read_text())
    for name, checksum in inventory["sha256"].items():
        with Path(name).open("rb") as handle:
            assert hashlib.file_digest(handle, "sha256").hexdigest() == checksum, name
    scratch = Path(tempfile.mkdtemp(prefix="dsre-completion-verify."))
    legacy = scratch / "legacy"
    legacy.mkdir()
    archive = Path(
        "research/dsre_evidence_design/evidence_aware_prospective_review.tar.gz"
    )
    with tarfile.open(archive, "r:gz") as handle:
        handle.extractall(legacy, filter="data")
    subprocess.run(
        [
            sys.executable,
            str(legacy / "research/dsre_evidence_design/verify_prospective.py"),
        ],
        check=True,
    )
    env = os.environ.copy()
    env.update(
        PYTHONPATH="src:scripts:.", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_evidence_aware.py",
            "tests/test_evidence_aware_prospective.py",
            "tests/test_evidence_lossless.py",
            "tests/test_evidence_source_eligibility.py",
        ],
        check=True,
        env=env,
    )
    evidence = Path("results/dsre-evidence-aware/20261118-source-eligibility")
    subprocess.run(
        [
            sys.executable,
            "scripts/dsre_evidence_eligible_audit.py",
            str(evidence),
            "--compact",
            "--output",
            str(scratch / "source_audit.json"),
            "--numerical-output",
            str(scratch / "numerical_audit.json"),
        ],
        check=True,
        env=env,
    )
    report = json.loads((evidence / "completion_scientific_report.json").read_text())
    for task, phases in report["grouped_denominators"].items():
        for phase, group in phases.items():
            assert (
                sum(group["mutually_exclusive_parent_categories"].values())
                == group["original_registered_parents"]
            )
            assert (
                group["original_registered_parents"]
                == {"discovery": 128, "calibration": 1024, "test": 256}[phase]
            )
    legacy_data = (
        legacy / "results/dsre-evidence-aware/20261117-prospective/prospective"
    )
    for task in ("PointMaze_UMaze-v3", "PickCube-v1"):
        out = legacy_data / task
        tests = {
            p.stem: json.loads(p.read_text()) for p in (out / "test").glob("*.json")
        }
        pairs = {
            p.stem: json.loads(p.read_text())
            for p in (out / "evaluator").glob("*.json")
        }
        decisions = {
            r["parent_id"]: r
            for r in json.loads((out / "evaluations/logged.json").read_text())[
                "decisions"
            ]
        }
        eligible = {
            p: r
            for p, r in tests.items()
            if r["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT")
        }
        for method, metrics in report["conditional_performance"][task][
            "policies"
        ].items():
            totals = Counter()
            for p in eligible:
                c, r = int(pairs[p]["yc"]), int(pairs[p]["yr"])
                recover = decisions[p]["actions"][method] == "r"
                y = r if recover else c
                totals.update(
                    recover=int(recover),
                    success=y,
                    gain=y - c,
                    harm=int(recover and c and not r),
                    rescues=int(recover and not c and r),
                    futile=int(recover and not c and not r),
                )
            assert metrics["eligible_n"] == len(eligible)
            assert all(metrics[k] == v for k, v in totals.items())
    assert report["scientific_decision"] == "INCOMPLETE_SOURCE_EVIDENCE"
    assert report["new_guard_independent_review"]["prefix_controls"] == 33
    print(
        json.dumps(
            {
                "passed": True,
                "verified_bundle_files": len(inventory["sha256"]),
                "legacy_reproduction": "PASS",
                "new_focused_tests": 24,
                "new_source_and_guard_review": "PASS",
                "canonical_eligible_denominators": "PASS",
                "physics_executed": False,
                "scope": inventory["scope"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
