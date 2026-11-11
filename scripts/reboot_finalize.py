"""Verify historical preservation, account resources and seal the Case D audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular_files(root):
    return [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]


def require_unsealed(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence is sealed")


def verify_inventory(root, expected):
    for name, value in expected.items():
        if digest(root / name) != value:
            raise ValueError(f"Historical file changed: {root / name}")


def verify_downloads(root, rows):
    verified = 0
    for row in rows:
        if "sha256" not in row:
            if "error" not in row or row.get("bytes", 0) != 0:
                raise ValueError("Saved download body lacks an integrity hash")
            continue
        if digest(root / row["path"]) != row["sha256"]:
            raise ValueError(f"Downloaded body changed: {row['path']}")
        verified += 1
    return verified


def verify_sealed_tree(root, expected):
    verify_inventory(root, expected)
    # Preserve each prior seal's convention: one includes interpreter symlinks;
    # the later regular-file-only seal excludes temporary pytest aliases.
    actual = {str(p.relative_to(root)) for p in regular_files(root)}
    actual.update(name for name in expected if (root / name).is_file())
    if actual != set(expected) | {"completion_manifest.json"}:
        raise ValueError(f"Historical evidence inventory changed: {root}")


def verify_prior(root):
    initial = json.loads((root / "initial.json").read_text())
    verify_inventory(Path.cwd(), initial["prior_sha256"])
    sealed = 0
    for name, value in initial["prior_seals"].items():
        path = Path(name)
        if digest(path) != value:
            raise ValueError(f"Historical seal changed: {name}")
        seal = json.loads(path.read_text())
        verify_sealed_tree(path.parent, seal["evidence_sha256"])
        sealed += len(seal["evidence_sha256"])
    old_inventory = Path(
        "results/recoverbench-transfer/20261111T172759Z/historical_inventory.json"
    )
    historical = json.loads(old_inventory.read_text())["sha256"]
    verify_inventory(Path.cwd(), historical)
    return {
        "reviewed_tracked_files": len(initial["prior_sha256"]),
        "previous_sealed_files": sealed,
        "earlier_historical_files": len(historical),
        "all_preserved": True,
    }


def resource_limits(resources):
    for name, limit in (
        ("elapsed_campaign_wall_seconds", 28800),
        ("measured_cpu_seconds_with_closing", 36000),
        ("charged_cpu_seconds_upper_bound", 36000),
        ("gpu_wall_seconds", 7200),
        ("download_bytes_conservative_bound", 6_000_000_000),
        ("new_storage_conservative_bound_bytes", 10_000_000_000),
    ):
        if not 0 <= resources[name] < limit:
            raise ValueError(f"Campaign resource limit: {name}")


def active_workers():
    active = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = process.info["cmdline"] or []
            if any(
                arg in {"dual_rec.reboot.acquisition", "dual_rec.reboot.audit"}
                or arg.endswith(("/reboot_command.py", "/reboot_independent_audit.py"))
                or arg
                in {"scripts/reboot_command.py", "scripts/reboot_independent_audit.py"}
                for arg in argv
            ):
                active.append(process.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return active


def verify(root):
    preserved = verify_prior(root)
    registration = root / "repository_registration.json"
    if digest(registration) != digest(Path("config/reboot_20261111.json")):
        raise ValueError("Frozen registration changed")
    if (
        digest(registration)
        != "2edcbb3655e74f6890e14dd83c387d8422d1cace9556015af073024252931c11"
    ):
        raise ValueError("Registration differs from preregistration")
    qualification = json.loads((root / "qualification.json").read_text())
    independent = json.loads((root / "independent_audit.json").read_text())
    assert qualification["status"] == "DATA_BLOCKED"
    assert qualification["models_trained"] == []
    assert qualification["B0_B7_results"] is None
    assert qualification["method_comparison_intervals"] is None
    assert qualification["alarm_delay_frontier"] is None
    assert qualification["all_metadata_hashes_match_release"]
    assert independent["status"] == "PASS" and not independent["failures"]
    assert independent["qualification_sha256"] == digest(root / "qualification.json")
    assert independent["projection_tables_checked"] == 793
    assert independent["frame_rows_checked"] == 546854
    assert independent["range_hashes_checked"] == 6344
    assert independent["metadata_hashes_checked"] == 82
    assert independent["annotation_joins_checked"] == 58
    assert len(independent["schema_invalid_annotations_checked"]) == 2
    assert independent["pilot_annotation_files"] == 0
    assert independent["duplicate_groups_checked"] == 60
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    by_name = {row["name"]: row for row in commands}
    for archive, job, path in (
        (
            "executed_acquisition_v1.py",
            "pinned-state-action-projections",
            "src/dual_rec/reboot/acquisition.py",
        ),
        (
            "executed_audit_v1.py",
            "corpus-annotation-and-causality-audit",
            "src/dual_rec/reboot/audit.py",
        ),
        (
            "executed_command_v1.py",
            "full-maintained-tests",
            "scripts/reboot_command.py",
        ),
    ):
        assert (
            digest(root / "provenance" / archive) == by_name[job]["source_sha256"][path]
        )
    for job, path in (
        ("final-corpus-annotation-audit", "src/dual_rec/reboot/audit.py"),
        (
            "independent-raw-range-and-label-audit",
            "scripts/reboot_independent_audit.py",
        ),
    ):
        assert digest(Path(path)) == by_name[job]["source_sha256"][path]
    downloads = [
        json.loads(s) for s in (root / "downloads.jsonl").read_text().splitlines()
    ]
    download_count = verify_downloads(root, downloads)
    projections = list((root / "ranges").rglob("manifest.json"))
    for path in projections:
        record = json.loads(path.read_text())
        assert digest(root / record["projection"]) == record["projection_sha256"]
    assert len(projections) == 793
    preserved["current_download_bodies_verified"] = download_count
    preserved["current_projection_hashes_verified"] = len(projections)
    for row in commands:
        assert digest(root / (row["name"] + ".log")) == row["log_sha256"]
    for row in map(
        json.loads, (root / "unmetered_commands.jsonl").read_text().splitlines()
    ):
        assert digest(root / (row["name"] + ".log")) == row["log_sha256"]
    required = {
        "final-corpus-annotation-audit",
        "independent-raw-range-and-label-audit",
        "reboot-regression-tests",
        "full-maintained-tests",
        "isolated-reboot-tests",
        "maintained-ruff-check",
        "maintained-format-check",
        "verified-maintained-suite",
        "meter-and-finalizer-regressions",
        "final-quality-suite",
        "final-quality-regressions",
        "final-quality-lint",
        "final-quality-format",
    }
    passed = {r["name"] for r in commands if r["exit_status"] == 0}
    assert required <= passed, f"Missing checks: {required - passed}"
    allowed_failures = {
        "primary-bootstrap",
        "pinned-state-action-projections",
        "closing-lint",
    }
    assert all(r["exit_status"] == 0 or r["name"] in allowed_failures for r in commands)
    assert not active_workers(), "Campaign workers still running"
    return preserved, commands


def main():
    cpu_start, wall_start = time.process_time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    root = args.root
    require_unsealed(root)
    preservation, commands = verify(root)
    initial = json.loads((root / "initial.json").read_text())
    downloads = [
        json.loads(s) for s in (root / "downloads.jsonl").read_text().splitlines()
    ]
    unmetered = [
        json.loads(s)
        for s in (root / "unmetered_commands.jsonl").read_text().splitlines()
    ]
    files = regular_files(root)
    # Count logical hard links twice: this is conservative for both disk and wheels.
    cache_bytes = sum(p.stat().st_size for p in regular_files(root / "cache/uv"))
    resources = {
        "preservation": preservation,
        "active_campaign_workers": [],
        "aggregate_worker_wall_seconds": sum(r["wall_seconds"] for r in commands),
        "measured_worker_and_driver_cpu_seconds": sum(
            r["cpu_seconds"] for r in commands
        ),
        "maximum_child_rss_kib": max(r["max_child_rss_kib"] for r in commands),
        "gpu_wall_seconds": 0,
        "paid_api_calls": 0,
        "models_trained": [],
        "unmetered_worker_cpu_upper_bound_seconds": sum(
            r["cpu_upper_bound_seconds"] for r in unmetered
        ),
        "download_successful_body_bytes": sum(r.get("bytes", 0) for r in downloads),
        "dependency_cache_logical_bytes_upper_bound": cache_bytes,
        "failed_request_and_interactive_download_allowance_bytes": 300_000_000,
        "new_logical_bytes_before_seal": sum(p.stat().st_size for p in files),
        "outside_run_git_cache_and_seal_allowance_bytes": 50_000_000,
        "measurement_scope": (
            "Foreground workers and their drivers plus this closing process; "
            "interactive tooling/editor/web/initial closing-probe overhead and host "
            "background CPU unmetered. One completed test lost process metering after "
            "a temporary-file race; its whole-host CPU-over-time upper bound is "
            "charged separately in unmetered_commands.jsonl. "
            "No host-wide exact CPU claim. Downloads count saved response bodies, "
            "the entire new uv cache bounds dependency transfers; a further 300 MB "
            "allowance covers failed bounded reads, linked-source/web requests and "
            "small bootstrap/tool traffic. No videos or model weights downloaded. "
            "GPU is zero by execution scope: only CPU data/tests/plots, no model or simulator."
        ),
    }
    resources["download_bytes_conservative_bound"] = (
        resources["download_successful_body_bytes"] + cache_bytes + 300_000_000
    )
    resources["new_storage_conservative_bound_bytes"] = (
        resources["new_logical_bytes_before_seal"] + 50_000_000
    )
    evidence = {}
    if args.seal:
        assert not subprocess.check_output(["git", "status", "--porcelain"], text=True)
        evidence = {str(p.relative_to(root)): digest(p) for p in files}
    resources["closing_process_cpu_seconds"] = time.process_time() - cpu_start
    resources["closing_wall_seconds"] = time.monotonic() - wall_start
    earlier = root / "preseal_resources.json"
    previous = json.loads(earlier.read_text()) if earlier.exists() else {}
    resources["earlier_closing_cpu_seconds"] = previous.get(
        "earlier_closing_cpu_seconds", 0
    ) + previous.get("closing_process_cpu_seconds", 0)
    resources["measured_cpu_seconds_with_closing"] = (
        resources["measured_worker_and_driver_cpu_seconds"]
        + resources["closing_process_cpu_seconds"]
        + resources["earlier_closing_cpu_seconds"]
    )
    resources["elapsed_campaign_wall_seconds"] = time.time() - initial["started_epoch"]
    resources["charged_cpu_seconds_upper_bound"] = (
        resources["measured_cpu_seconds_with_closing"]
        + resources["unmetered_worker_cpu_upper_bound_seconds"]
    )
    resource_limits(resources)
    if args.seal:
        (root / "resources.json").write_text(json.dumps(resources, indent=2) + "\n")
        evidence["resources.json"] = digest(root / "resources.json")
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", initial["reviewed_base"], "HEAD"], text=True
        ).splitlines()
        result = {
            "status": "COMPLETE_AUTHORIZED_CASE_D_AUDIT",
            "gate": "DATA_BLOCKED",
            "completed_utc": datetime.now(UTC).isoformat(),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "resources": resources,
            "evidence_sha256": evidence,
            "maintained_sha256": {name: digest(Path(name)) for name in changed},
            "symlink_targets": {
                str(p.relative_to(root)): os.readlink(p)
                for p in root.rglob("*")
                if p.is_symlink()
            },
            "seal_scope": "All new regular files, including original partial ranges, projections, environment/cache, failed attempts and command logs. External interpreter symlinks recorded separately; no whole-file integrity claim for range-only upstream Parquets.",
        }
        (root / "completion_manifest.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    else:
        (root / "preseal_resources.json").write_text(
            json.dumps(resources, indent=2) + "\n"
        )
    print(json.dumps(resources, indent=2))


if __name__ == "__main__":
    main()
