"""Final evidence sealing requires intact completed stages and measured budgets."""

import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "revalidation_finalize",
    Path(__file__).resolve().parents[1] / "scripts/revalidation_finalize.py",
)
finalizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalizer)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalizer, "HISTORICAL_FILE_COUNT", 2)
    monkeypatch.setattr(finalizer, "SEALED_FILE_COUNT", 1)
    monkeypatch.setattr(finalizer, "active_workers", lambda root: [])
    root = Path("run")
    root.mkdir()
    prior = Path("old-science.json")
    prior.write_text("preserved negative result")
    ignore = Path(".gitignore")
    ignore.write_text("old bytes")
    original_ignore = finalizer.digest(ignore)
    core = Path("core.py")
    core.write_text("pass\n")
    report = Path("report.md")
    report.write_text(
        "Bounded negative study; exact resources are in run/resources.json."
    )
    write_json(
        root / "initial.json",
        {
            "started_epoch": time.time() - 30,
            "prior_sha256": {
                str(prior): finalizer.digest(prior),
                ".gitignore": original_ignore,
            },
        },
    )
    ignore.write_text("user's explicitly approved new ignore rules")
    approved = finalizer.digest(ignore)
    write_json(
        root / "provenance/gitignore_integrity_event.json",
        {"user_steering_sha256": approved},
    )
    write_json(
        root / "qualification_seal.json",
        {
            "source_sha256": {str(core): finalizer.digest(core)},
            "qualification_parent_ids": ["held-out-13"],
            "implementation_commit": "abc123",
        },
    )
    write_json(root / "selection.json", {"primary_baseline": "B2"})
    for split in ("development", "qualification"):
        directory = root / split
        directory.mkdir()
        for name in ("episodes.jsonl.gz", "decisions.jsonl.gz"):
            (directory / name).write_text("retained raw evidence")
        status = {
            "episodes": 1,
            "rows": 2,
            "evaluated": 1,
            "reference_skips": {"cap": 1},
            "parents": ["held-out-13" if split == "qualification" else "dev-01"],
            "split": split,
        }
        write_json(directory / "status.json", status)
        write_json(
            directory / "audit.json",
            {
                "status": "PASS",
                "split": split,
                "mismatches": [],
                "parents": status["parents"],
                "checked_counts": {
                    "episodes": 1,
                    "rows": 2,
                    "recomputed_rows": 1,
                    "reference_skips": 1,
                    "parent_instances": 1,
                },
                "source_sha256": {
                    str(directory / name): finalizer.digest(directory / name)
                    for name in (
                        "episodes.jsonl.gz",
                        "decisions.jsonl.gz",
                        "status.json",
                    )
                },
            },
        )
        figure = directory / "analysis/figure.svg"
        figure.parent.mkdir()
        figure.write_text("<svg/>")
        write_json(
            directory / "analysis/summary.json",
            {
                "episodes": 1,
                "evaluated_rows": 1,
                "reference_skip_rows": 1,
                "primary_baseline": "B2",
                "selection_sha256": finalizer.digest(root / "selection.json"),
                "source_sha256": {
                    name: finalizer.digest(directory / name)
                    for name in ("episodes.jsonl.gz", "decisions.jsonl.gz")
                },
                "plots": {"files": ["figure.svg"]},
            },
        )
    rows = []
    for kind, command, text in (
        ("tests", ["uv", "run", "--no-sync", "pytest"], "8 passed in 0.1s"),
        ("lint", ["uv", "run", "--no-sync", "ruff", "check"], "All checks passed!"),
        (
            "format",
            ["uv", "run", "--no-sync", "ruff", "format", "--check"],
            "3 files already formatted",
        ),
    ):
        log = root / (kind + ".log")
        log.write_text(text)
        rows.append(
            {
                "name": kind,
                "command": command,
                "exit_status": 0,
                "cpu_seconds": 1.0,
                "wall_seconds": 1.5,
                "source_sha256": {str(core): finalizer.digest(core)},
                "log_sha256": finalizer.digest(log),
            }
        )
    (root / "commands.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    (root / "benchmarks").mkdir()
    (root / "benchmarks/commands.jsonl").write_text("")
    write_json(
        root / "benchmarks/resources.json",
        {
            "commands": 0,
            "cpu_seconds": 0,
            "wall_seconds": 0,
            "all_planning_and_install_jobs_finished": True,
        },
    )
    write_json(
        root / "benchmarks/planning_status.json", {"driver_self_cpu_seconds": 0.2}
    )
    monkeypatch.setattr(finalizer, "validation_sources", lambda: [core])
    monkeypatch.setattr(
        finalizer, "artifact_roots", lambda root, report: [root, core, report]
    )
    return root, report, approved, {kind: kind for kind in ("tests", "lint", "format")}


def finish(campaign):
    return finalizer.finalize(*campaign, workers_finished=True)


def test_completed_seal_preserves_report_and_never_overwrites(campaign):
    root, report, _, _ = campaign
    before = report.read_bytes()
    resources = finish(campaign)
    integrity = json.loads((root / "integrity.json").read_text())
    manifest = json.loads((root / "completion_manifest.json").read_text())
    assert integrity["historical_files_preserved"] == 1
    assert integrity["sealed_files_unchanged"] == 1
    assert resources["recorded_subprocess_cpu_seconds"] >= 3.2
    assert report.read_bytes() == before
    assert manifest["source_sha256"][str(report)] == hashlib.sha256(before).hexdigest()
    for name in ("resources.json", "integrity.json"):
        assert manifest["artifacts"][name]["sha256"] == finalizer.digest(root / name)
    with pytest.raises(ValueError, match="already"):
        finish(campaign)


@pytest.mark.parametrize(
    "mutation",
    [
        "historical",
        "sealed",
        "approved_ignore",
        "raw",
        "audit",
        "status",
        "missing_qualification",
        "validation",
        "figures",
    ],
)
def test_rejects_missing_or_tampered_evidence_before_writing(campaign, mutation):
    root, _, _, _ = campaign
    if mutation == "historical":
        Path("old-science.json").write_text("tampered")
    elif mutation == "sealed":
        Path("core.py").write_text("tampered")
    elif mutation == "approved_ignore":
        Path(".gitignore").write_text("unapproved change")
    elif mutation == "raw":
        (root / "qualification/decisions.jsonl.gz").write_text("tampered")
    elif mutation == "audit":
        value = finalizer.read_json(root / "qualification/audit.json")
        value["mismatches"] = ["wrong safe-goal label"]
        write_json(root / "qualification/audit.json", value)
    elif mutation == "status":
        value = finalizer.read_json(root / "qualification/status.json")
        value["evaluated"] = 2
        write_json(root / "qualification/status.json", value)
    elif mutation == "missing_qualification":
        (root / "qualification/status.json").unlink()
    elif mutation == "validation":
        (root / "tests.log").write_text("1 failed")
    else:
        (root / "qualification/analysis/figure.svg").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        finish(campaign)
    assert not any((root / name).exists() for name in finalizer.OUTPUTS)


@pytest.mark.parametrize("resource", ["wall", "cpu", "disk"])
def test_rejects_resource_overage(campaign, monkeypatch, resource):
    if resource == "wall":
        monkeypatch.setattr(finalizer, "WALL_LIMIT", 0)
    elif resource == "cpu":
        monkeypatch.setattr(finalizer, "CPU_LIMIT", 0)
    else:
        monkeypatch.setattr(finalizer, "ARTIFACT_LIMIT", 0)
    with pytest.raises(ValueError, match="Resource ceiling"):
        finish(campaign)


def test_requires_known_session_completion_and_visible_worker_exit(
    campaign, monkeypatch
):
    with pytest.raises(ValueError, match="known worker"):
        finalizer.finalize(*campaign)
    monkeypatch.setattr(finalizer, "active_workers", lambda root: [{"pid": 123}])
    with pytest.raises(ValueError, match="still running"):
        finish(campaign)


def test_artifact_usage_deduplicates_overlapping_roots_hardlinks_and_symlinks(tmp_path):
    a = tmp_path / "artifact"
    a.write_bytes(b"x" * 100)
    hardlink = tmp_path / "hardlink"
    hardlink.hardlink_to(a)
    symlink = tmp_path / "symlink"
    symlink.symlink_to(a)
    usage = finalizer.unique_bytes([tmp_path, a])
    assert usage["unique_file_inodes"] == 2
    assert usage["unique_logical_bytes_before_seal"] == 100 + os.lstat(symlink).st_size


def test_rejects_validation_after_admin_source_change(campaign, monkeypatch):
    admin = Path("new-finalizer.py")
    admin.write_text("new admin source absent from final checks")
    monkeypatch.setattr(
        finalizer, "validation_sources", lambda: [Path("core.py"), admin]
    )
    with pytest.raises(ValueError, match="Source changed since final validation"):
        finish(campaign)
