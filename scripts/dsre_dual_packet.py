"""Package bounded numerical review; raw state/contact logs remain local."""

import argparse
import json
import shutil
import tarfile
from pathlib import Path

from dsre_dual_adjudication import read, sha


def build(root):
    assert read(root / "independent_dual_numerical_audit.json")["passed"]
    packet = root / "review_packet"
    packet.mkdir(exist_ok=False)
    names = (
        "study_plan.json",
        "seed_manifest.json",
        "seed_disjointness_audit.json",
        "source_freeze.json",
        "analysis_registration.json",
        "transitive_source_integrity.json",
        "portable_packaging_correction.json",
        "preregistration_commit.json",
        "execution_configuration.json",
        "runtime_candidate_fingerprint.json",
        "qualification_registration.json",
        "qualification_audit.json",
        "source_qualification_seal.json",
        "prior_replication.json",
        "nearest_work_registered.md",
        "engineering_preflight_failures.json",
        "calibration_rows.json.gz",
        "test_rows.json.gz",
        "calibration_physics_audit.json",
        "test_physics_audit.json",
        "dual_calibration.json",
        "dual_calibration_seal.json",
        "dual_calibration_audit.json",
        "calibration_decision.json",
        "calibration_seal.json",
        "calibration_decision_audit.json",
        "legacy_gate_provenance.json",
        "test_recommendation_seal.json",
        "dual_test_seal.json",
        "dual_results.json",
        "policy_records.jsonl.gz",
        "calibration_decomposition.json",
        "test_decomposition.json",
        "independent_dual_numerical_audit.json",
        "physical_witnesses.json",
        "report_source_binding.json",
        "figure_sources.json",
        "figure_visual_review.json",
        "calibration_table.csv",
        "policy_table.csv",
        "final_preservation_audit.json",
    )
    for name in names:
        shutil.copyfile(root / name, packet / name)
    for index in range(3):
        shutil.copyfile(
            root / f"parity-{index:04d}.json", packet / f"parity-{index:04d}.json"
        )
    for seed in read(root / "study_plan.json")["test_seeds"]:
        destination = packet / "test" / str(seed)
        destination.mkdir(parents=True)
        for name in ("decision.json", "dual_decision.json", "execution_started.json"):
            shutil.copyfile(root / "test" / str(seed) / name, destination / name)
    sources = set(read(root / "source_freeze.json")["source_sha256"])
    sources.update(read(root / "analysis_registration.json")["source_sha256"])
    sources.update(
        name
        for name in read(root / "transitive_source_integrity.json")["source_sha256"]
        if name.startswith(("scripts/", "tests/"))
    )
    sources.update(
        (
            "scripts/dsre_dual_report.py",
            "scripts/dsre_dual_packet.py",
            "scripts/dsre_dual_verify_packet.py",
            "src/dual_rec/__init__.py",
        )
    )
    for name in sources:
        target = packet / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, target)
    for name in (
        "docs/DSRE_DUAL_OBLIGATION_METHOD.md",
        "docs/DSRE_DUAL_OBLIGATION_PREREGISTRATION.md",
        "docs/DSRE_DUAL_OBLIGATION_RESULTS.md",
        "docs/DSRE_DUAL_OBLIGATION_NOVELTY_AND_GATE.md",
        "docs/figures/dsre_dual_obligation.png",
        "docs/figures/dsre_dual_obligation.pdf",
    ):
        target = packet / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, target)
    manifest = {
        "scope": "Portable numerical/decision-seal review only. Binary outcome rows were independently linked to raw matched physics in the full local archive. Compact data do not replace state/contact/source qualification.",
        "contains_manuscript_or_raw_log": False,
        "files": {
            p.relative_to(packet).as_posix(): sha(p)
            for p in sorted(packet.rglob("*"))
            if p.is_file()
        },
    }
    (packet / "packet_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    target = Path("docs/dsre_dual_obligation_review.tar.gz")
    assert not target.exists()
    with tarfile.open(target, "w:gz") as archive:
        for path in sorted(packet.rglob("*")):
            if path.is_file():
                archive.add(
                    path, arcname=path.relative_to(packet).as_posix(), recursive=False
                )
    print(
        json.dumps(
            {
                "archive": str(target),
                "bytes": target.stat().st_size,
                "sha256": sha(target),
                "members": len(manifest["files"]) + 1,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    build(parser.parse_args().root)
