"""Build a bounded supervisor packet; raw physical states/logs remain local."""

import argparse
import gzip
import json
import shutil
import tarfile
from pathlib import Path

from dsre_followup_batch import read, sha


def build(root):
    assert read(root / "independent_numerical_audit.json")["passed"]
    packet = root / "review_packet"
    packet.mkdir(exist_ok=False)
    for name in (
        "study_plan.json",
        "seed_manifest.json",
        "frozen_routers.json",
        "source_freeze.json",
        "analysis_registration.json",
        "execution_configuration.json",
        "source_qualification_seal.json",
        "qualification_audit.json",
        "qualification_registration.json",
        "runtime_candidate_fingerprint.json",
        "native_forensic_audit.json",
        "terminal_audit_registration.json",
        "qualification_terminal_predicate_audit.json",
        "calibration_terminal_predicate_audit.json",
        "test_terminal_predicate_audit.json",
        "calibration_decision.json",
        "calibration_seal.json",
        "calibration_decision_audit.json",
        "calibration_physics_audit.json",
        "test_physics_audit.json",
        "test_recommendation_seal.json",
        "test_analysis.json",
        "independent_numerical_audit.json",
        "test_certificate_witnesses.json",
        "test_rows.jsonl.gz",
        "test_metric_records.jsonl.gz",
        "figure_source_data.json",
        "report_source_binding.json",
        "final_preservation_audit.json",
        "figure_visual_review.json",
        "calibration_table.csv",
    ):
        shutil.copyfile(root / name, packet / name)
    for source in list(root.glob("parity-*.json")) + list(
        (root / "stability").glob("repeat*/parity-*.json")
    ):
        target = packet / "qualification_reports" / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for stage in ("calibration", "test"):
        with gzip.open(packet / (stage + "_parent_labels.jsonl.gz"), "wt") as stream:
            for path in sorted((root / stage).glob("*/outcome_labels.json")):
                stream.write(json.dumps(read(path)) + "\n")
    sources = set(read(root / "source_freeze.json")["source_sha256"])
    sources.update(read(root / "analysis_registration.json")["source_sha256"])
    sources.update(
        (
            "scripts/dsre_source_risk_report.py",
            "scripts/dsre_source_risk_packet.py",
            "scripts/dsre_source_risk_verify_packet.py",
            "scripts/dsre_runtime_campaign.py",
            "src/dual_rec/__init__.py",
            "scripts/dsre_source_risk_terminal_audit.py",
            "tests/test_dsre_source_risk_terminal_audit.py",
        )
    )
    for name in sources:
        target = packet / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, target)
    for name in (
        "docs/DSRE_SAPIEN_NATIVE_CRASH_DIAGNOSIS.md",
        "docs/DSRE_RUNTIME_PHYSICAL_QUALIFICATION.md",
        "docs/DSRE_SOURCE_RISK_COMPLETION.md",
        "docs/DSRE_V12_SOURCE_RISK_PREREGISTRATION.md",
        "docs/figures/dsre_recovered_source_risk.png",
        "docs/figures/dsre_recovered_source_risk.pdf",
    ):
        target = packet / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, target)
    manifest = {
        "scope": "Local supervisor numerical/hash review. Physical state fidelity requires the full local raw archive; its independent audit/source seals are linked, not replaced by compact labels.",
        "contains_manuscript_or_raw_log": False,
        "files": {
            p.relative_to(packet).as_posix(): sha(p)
            for p in sorted(packet.rglob("*"))
            if p.is_file()
        },
    }
    (packet / "packet_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    destination = Path("docs/dsre_runtime_source_risk_review.tar.gz")
    assert not destination.exists()
    with tarfile.open(destination, "w:gz") as archive:
        for path in sorted(packet.rglob("*")):
            if path.is_file():
                archive.add(
                    path, arcname=path.relative_to(packet).as_posix(), recursive=False
                )
    print(
        json.dumps(
            {
                "archive": str(destination),
                "bytes": destination.stat().st_size,
                "sha256": sha(destination),
                "members": len(manifest["files"]) + 1,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    build(parser.parse_args().root)
