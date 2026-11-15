"""Build compact review evidence without logs, manuscripts, caches or raw frames."""

import argparse
import gzip
import hashlib
import json
import shutil
import tarfile
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_science_offline import LATEST, delayed

from dual_rec.dsre.features import ObservationHistory


def build(root):
    assert read(root / "prospective_numerical_audit.json")["passed"]
    payload = root / "review_payload"
    payload.mkdir(exist_ok=False)
    for name in ("data", "results", "reports"):
        (payload / name).mkdir()
    with gzip.open(payload / "data/compact_rows.jsonl.gz", "wt") as stream:
        for name in ("offline_rows.jsonl.gz", "prospective_rows.jsonl.gz"):
            with gzip.open(root / name, "rt") as f:
                for line in f:
                    row = json.loads(line)
                    h = ObservationHistory.model_validate(row["runtime_history"])
                    delay = delayed(row, h)
                    row["actual_delay_history"] = (
                        delay.model_dump(mode="json") if delay is not None else None
                    )
                    stream.write(json.dumps(row) + "\n")
    for name in (
        "offline_decisions.jsonl.gz",
        "prospective_decisions.jsonl.gz",
        "secondary_decisions.jsonl.gz",
    ):
        shutil.copyfile(root / name, payload / "data" / name)
    shutil.copyfile(root / "frozen_routers.json", payload / "data/frozen_routers.json")
    shutil.copyfile(
        LATEST / "calibration_decision.json",
        payload / "data/original_calibration_decision.json",
    )
    names = [
        "study_plan.json",
        "science_freeze.json",
        "initial.json",
        "prior_seal_verification.json",
        "expanded_seed_disjointness_audit.json",
        "environment_fingerprint.json",
        "preregistration_publication.json",
        "analysis_registration.json",
        "secondary_analysis_registration.json",
        "physical_contrast_registration.json",
        "pilot_gate.json",
        "pilot_qualification_seal.json",
        "prospective_recommendation_seal.json",
        "secondary_recommendation_seal.json",
        "offline_results.json",
        "offline_uncertainty.json",
        "mechanism_results.json",
        "mechanism_compatibility.json",
        "offline_audit.json",
        "offline_numerical_audit.json",
        "full_pose_audit.json",
        "robust_tree_fairness_audit.json",
        "constructive_measurement_examples.json",
        "prospective_results.json",
        "prospective_compatibility.json",
        "physical_effects_and_secondary.json",
        "prospective_physics_audit.json",
        "prospective_full_pose_audit.json",
        "prospective_numerical_audit.json",
        "figure_data.json",
        "scientific_readiness.json",
        "validation.json",
        "resources.json",
        "worker_exit_audit.json",
        "preservation_verification.json",
    ]
    for name in names:
        shutil.copyfile(root / name, payload / "results" / name)
    for path in Path("docs").glob("DSRE_STAGE1_SCIENCE_V12_*.md"):
        shutil.copyfile(path, payload / "reports" / path.name)
    for path in Path("docs/figures").glob("dsre_science_v12_*.*"):
        shutil.copyfile(path, payload / "reports" / path.name)
    sources = set(read(root / "science_freeze.json")["source_sha256"])
    sources.update(str(p) for p in Path("scripts").glob("dsre_science_*.py"))
    sources.update(
        [
            "src/dual_rec/__init__.py",
            "src/dual_rec/contracts/__init__.py",
            "src/dual_rec/contracts/checks.py",
            "config/dsre_science_v12.json",
            "pyproject.toml",
            "uv.lock",
            "tests/test_dsre_measurement.py",
            "tests/test_dsre_science_analysis.py",
        ]
    )
    for source in sorted(sources):
        p = Path(source)
        if p.is_file():
            d = payload / "sources" / source
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, d)
    shutil.copyfile(
        "scripts/dsre_science_verify_compact.py", payload / "verify_compact.py"
    )
    seal = {
        "schema": "dsre-science-v12-compact-seal-v1",
        "files": {
            str(p.relative_to(payload)): sha(p)
            for p in sorted(payload.rglob("*"))
            if p.is_file()
        },
        "registered_plan_sha256": sha(root / "study_plan.json"),
        "scope": "All quantitative routing inputs/labels plus compact ledgers, source snapshots and independent audits. Raw physical states retained locally under source hashes. No manuscript or log redistribution.",
        "epoch": time.time(),
    }
    atomic(payload / "packet_seal.json", seal)
    archive = root / "supervisor_review.tar.gz"
    with tarfile.open(archive, "w:gz", compresslevel=9) as tar:
        for p in sorted(payload.rglob("*")):
            if p.is_file():
                tar.add(p, arcname=str(p.relative_to(payload)), recursive=False)
    target = Path("docs/dsre_science_v12_review.tar.gz")
    shutil.copyfile(archive, target)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    atomic(
        root / "review_packet_validation.json",
        {
            "passed": True,
            "members": len(seal["files"]) + 1,
            "archive_sha256": digest,
            "archive_bytes": archive.stat().st_size,
            "no_logs_manuscripts_or_raw_frames": True,
            "packet_seal_sha256": sha(payload / "packet_seal.json"),
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {"archive": str(target), "sha256": digest, "bytes": archive.stat().st_size}
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    build(a.root)
