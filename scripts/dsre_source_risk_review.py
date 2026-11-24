"""Independent integrity checks for the halted source-risk study and its packet.

Uses saved records and exact binomial arithmetic, without a policy or simulator
import. An integrity pass cannot establish physical source qualification.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_report(report, plan):
    assert report["scientific_gate"] == "PHYSICS_OR_DATA_BLOCKED"
    assert not report["experimental_campaign_complete"]
    assert plan["calibration_seeds"] == list(range(15000000, 15000256))
    assert plan["test_seeds"] == list(range(16000000, 16000128))
    assert not set(plan["calibration_seeds"]) & set(plan["test_seeds"])
    assert plan["risk"]["per_stratum_delta"] == 0.05 / 68
    assert plan["risk"]["target"] == 0.1
    delta = plan["risk"]["per_stratum_delta"]
    assert 1 - delta ** (1 / 68) > 0.1
    assert 1 - delta ** (1 / 69) <= 0.1
    # Exact zero-error binomial CDF, independent of the production CP scorer.
    assert (1 - 0.1) ** 68 > delta >= (1 - 0.1) ** 69
    assert math.ceil(math.log(delta) / math.log(0.9)) == 69
    for stage, expected in (("calibration", 256), ("test", 128)):
        row = report[stage]
        assert row["planned_parents"] == expected
        assert row["started_parents"] == row["completed_parents"] == 0
        assert not row["complete_cohort"]
    for field in (
        "coverage",
        "conditional_success",
        "required_recovery_recall",
        "paired_effects",
        "paired_outcome_classes",
        "inadequate",
        "stop",
    ):
        assert report["test"][field] is None
    assert len(report["strata"]) == 34
    for row in report["strata"].values():
        assert row["assigned_parents"] == row["observed_error_parents"] == 0
        assert row["risk_point_estimate"] is None
        assert row["upper"] == 1 and not row["enabled"]
        assert row["status"] == "NOT_QUALIFIED_INCOMPLETE_COHORT"
    assert report["native_failure"]["first_attempt_returncode"] == -11
    assert report["native_failure"]["independent_prefix_probe_status"] == 139
    return {"claims_disabled": 34, "zero_error_support_needed": 69}


def audit(root):
    plan = read(root / "study_plan.json")
    report = read(root / "blocked_scientific_results.json")
    checks = validate_report(report, plan)
    freeze = read(root / "source_freeze.json")
    for key in ("source_sha256", "input_sha256"):
        for name, digest in freeze[key].items():
            assert sha(Path(name)) == digest, name
    for name, digest in read(root / "initial.json")["protected_sha256"].items():
        assert sha(Path(name)) == digest, name
    attempts = list((root / "attempts").glob("*.json"))
    assert len(attempts) == 1
    attempt = read(attempts[0])
    halt = read(root / "study_halt.json")
    assert halt["stage"] == "qualification" and halt["returncode"] == -11
    assert freeze["registered_epoch"] <= attempt["epoch"] <= halt["epoch"]
    assert attempt["seed"] == plan["qualification_seeds"][0] == 13000000
    for name in ("qualification", "calibration", "test"):
        assert not list((root / name).rglob("*.json.gz"))
    for name in (
        "calibration_decision.json",
        "calibration_seal.json",
        "test_recommendation_seal.json",
        "qualification_audit.json",
    ):
        assert not (root / name).exists()
    registry = read(root / "seed_disjointness_audit.json")
    assert registry["passed"] and not registry["collisions"]
    historical_members = 0
    latest_deliverables = {}
    superseded_deliverables = []
    for previous in read(root / "input_seal_verification.json")["roots"]:
        base = Path(previous["root"])
        seal = base / "completion_manifest.json"
        assert sha(seal) == previous["manifest_sha256"]
        content = read(seal)
        for name, entry in content["files"].items():
            assert sha(base / name) == entry["sha256"], name
            historical_members += 1
        for name, digest in content["maintained_deliverables"].items():
            if name in latest_deliverables and latest_deliverables[name] != digest:
                superseded_deliverables.append(name)
            latest_deliverables[name] = digest
    # A later sealed synthesis intentionally supersedes some v1.2 paper files.
    # Both old raw roots must match, and current deliverables match the latest seal.
    for name, digest in latest_deliverables.items():
        assert sha(Path(name)) == digest, name
    result = {
        "integrity_passed": True,
        "physical_qualification_passed": False,
        "new_empirical_results_available": False,
        "registered_source_and_inputs_unchanged": True,
        "protected_files_unchanged": True,
        "fresh_parents_started": 0,
        "old_manifest_members_verified": historical_members,
        "historically_superseded_deliverables": sorted(set(superseded_deliverables)),
        **checks,
    }
    (root / "final_independent_integrity_audit.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    return result


def verify(packet):
    manifest = read(packet / "packet_manifest.json")
    files = {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()}
    assert files == set(manifest["files"]) | {"packet_manifest.json"}
    assert not any(name.endswith(".log") for name in files)
    assert not any(name.startswith("rss2027/") for name in files)
    for name, digest in manifest["files"].items():
        assert sha(packet / name) == digest, name
    plan = read(packet / "study_plan.json")
    checks = validate_report(read(packet / "blocked_scientific_results.json"), plan)
    audit_result = read(packet / "final_independent_integrity_audit.json")
    assert audit_result["integrity_passed"]
    assert not audit_result["physical_qualification_passed"]
    freeze = read(packet / "source_freeze.json")
    assert (
        sha(packet / "docs/DSRE_V12_SOURCE_RISK_PREREGISTRATION.md")
        == freeze["input_sha256"]["docs/DSRE_V12_SOURCE_RISK_PREREGISTRATION.md"]
    )
    assert (
        sha(packet / "study_plan.json")
        == freeze["input_sha256"][plan["root"] + "/study_plan.json"]
    )
    for name, digest in freeze["source_sha256"].items():
        assert sha(packet / "source_snapshot" / name) == digest, name
    return {"packet_verified": True, "files": len(manifest["files"]), **checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("audit", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            audit(args.directory) if args.mode == "audit" else verify(args.directory)
        )
    )
