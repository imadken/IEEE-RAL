"""Verify the rescue's bounded stop condition and preserve the earlier evidence."""

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


def require_original_prefix(current, original):
    if not current.startswith(original):
        raise ValueError("Original cumulative document was rewritten")


def require_unsealed(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence is sealed")


def verify_prior(root):
    initial = json.loads((root / "initial.json").read_text())
    old = Path(initial["previous_run"])
    assert digest(old / "completion_manifest.json") == initial["previous_seal_sha256"]
    seal = json.loads((old / "completion_manifest.json").read_text())
    for name, expected in seal["evidence_sha256"].items():
        assert digest(old / name) == expected, name
    actual = {str(p.relative_to(old)) for p in old.rglob("*") if p.is_file()}
    assert actual == set(seal["evidence_sha256"]) | {"completion_manifest.json"}, (
        "Files were added to sealed inputs"
    )
    historical = json.loads((old / "historical_inventory.json").read_text())["sha256"]
    for name, expected in historical.items():
        assert digest(Path(name)) == expected, name
    for name, expected in initial["prior_sha256"].items():
        if name in {
            "RECOVERBENCH_TRANSFER_PROTOCOL.md",
            "RECOVERBENCH_TRANSFER_REPORT.md",
        }:
            original = subprocess.check_output(
                ["git", "show", initial["reviewed_base"] + ":" + name]
            )
            assert hashlib.sha256(original).hexdigest() == expected
            require_original_prefix(Path(name).read_bytes(), original)
        else:
            assert digest(Path(name)) == expected, name
    return {
        "sealed_files": len(seal["evidence_sha256"]),
        "historical_files": len(historical),
        "reviewed_tracked_files": len(initial["prior_sha256"]),
        "all_preserved": True,
    }


def verify(root):
    preserved = verify_prior(root)
    assert digest(root / "registration.json") == digest(
        Path("config/recoverbench_qualification_20261111.json")
    )
    assert (
        digest(root / "registration.json")
        == "4c0f76578e0df4ae81ec98248dec6f8b3a59cfcf0ef064394b02b3f3160c31f7"
    )
    numerical = json.loads((root / "independent_numerical_audit.json").read_text())
    physics = json.loads((root / "independent_physics_audit.json").read_text())
    assert numerical["status"] == physics["status"] == "PASS"
    assert numerical["rows"] == 24 and numerical["counted_controls"] == 9862
    assert numerical["derived_feature_sources"] == 12 and not numerical["failures"]
    assert physics["predicate_snapshots"] == 56 and not physics["errors"]
    assert sum(f["samples"] for f in physics["feature_checks"]) == 4931
    assert (
        digest(root / "source-diagnostics/outcomes.jsonl")
        == numerical["outcomes_sha256"]
    )
    generation = json.loads((root / "generation_preflight.json").read_text())
    assert (
        generation["generation_attempts"]
        == generation["independent_generated_rollouts"]
        == 0
    )
    assert generation["status"] == "SOURCE_GENERATION_BLOCKED"
    analysis = json.loads((root / "analysis.json").read_text())
    assert (
        analysis["gate"] == "INCONCLUSIVE"
        and not analysis["conditional_pilot_executed"]
    )
    assert analysis["B1_B5"] is None and analysis["method_effect_intervals"] is None
    commands = [
        json.loads(line) for line in (root / "commands.jsonl").read_text().splitlines()
    ]
    for name in (
        "upstream-source-and-evaluation-tests-layout",
        "rescue-maintained-regression-final",
        "rescue-isolated-regressions-final",
        "rescue-lint-final",
        "rescue-format-final",
    ):
        assert any(r["name"] == name and r["exit_status"] == 0 for r in commands), name
    archived = {
        "scripts/recoverbench_qualification_command.py": root
        / "provenance/executed_command_before_cache_redirection.py",
        "scripts/recoverbench_qualification_audit.py": root
        / "provenance/qualification_audit_before_roundoff_fix.py",
    }
    for name, path in archived.items():
        assert any(r["source_sha256"].get(name) == digest(path) for r in commands), name
    worker = next(
        r for r in commands if r["name"] == "source-checker-controller-and-fk"
    )
    for name in (
        "src/dual_rec/recoverbench/qualification.py",
        "src/dual_rec/recoverbench/qualification_replay.py",
    ):
        assert digest(Path(name)) == worker["source_sha256"][name], (
            "Executed physics source changed"
        )
    ancestors = {os.getpid(), *(p.pid for p in psutil.Process().parents())}
    active = []
    for p in psutil.process_iter(["cmdline"]):
        try:
            if p.pid not in ancestors and any(
                str(root) in arg for arg in p.info["cmdline"] or []
            ):
                active.append(p.pid)
        except psutil.Error:
            continue
    assert not active, active
    return {
        "preservation": preserved,
        "active_campaign_workers": active,
        "aggregate_worker_wall_seconds": sum(r["wall_seconds"] for r in commands),
        "measured_worker_and_driver_cpu_seconds": sum(
            r["cpu_seconds"] for r in commands
        ),
        "gpu_wall_seconds": 0,
        "paid_api_calls": 0,
        "measurement_scope": "Foreground workers and their drivers. Initial metadata/tool/editor work is unmetered; closing checks are measured separately. No whole-host CPU claim.",
        "bootstrap_worker_allowance_seconds": 5,
    }


def main():
    closing_started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    root = args.root
    require_unsealed(root)
    resource = verify(root)
    files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
    resource["new_logical_bytes_before_seal"] = sum(p.stat().st_size for p in files)
    overhead_paths = [
        Path(p)
        for p in (
            ".git",
            ".pytest_cache",
            ".ruff_cache",
            "/tmp/dual-rec-uv-cache",
            "/tmp/pytest-of-imad",
        )
    ]
    overhead_paths += [
        p
        for folder in ("src", "scripts", "tests")
        for p in Path(folder).rglob("__pycache__")
    ]
    overhead = sum(
        p.stat().st_size
        for folder in overhead_paths
        for p in folder.rglob("*")
        if p.is_file()
    )
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "960ec091e1ff16d29fa89d5bf20c63847050886a"],
        text=True,
    ).splitlines()
    resource["outside_run_storage_conservative_bytes"] = overhead + sum(
        Path(p).stat().st_size for p in changed if Path(p).is_file()
    )
    assert resource["outside_run_storage_conservative_bytes"] < 50_000_000
    resource["new_storage_with_overhead_bound_bytes"] = (
        resource["new_logical_bytes_before_seal"] + 50_000_000
    )
    assert resource["new_storage_with_overhead_bound_bytes"] < 4_000_000_000
    assert resource["aggregate_worker_wall_seconds"] + 5 < 18000
    assert (
        resource["measured_worker_and_driver_cpu_seconds"] + time.process_time() + 5
        < 21600
    )
    if args.seal:
        assert not subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        assert not any(
            p.startswith("results/") or p in {".gitignore", "uv.lock", "pyproject.toml"}
            for p in changed
        )
        evidence = {str(p.relative_to(root)): digest(p) for p in files}
        resource["closing_process_cpu_seconds"] = time.process_time()
        resource["closing_wall_seconds"] = time.monotonic() - closing_started
        resource["aggregate_wall_with_closing_and_bootstrap_allowance_seconds"] = (
            resource["aggregate_worker_wall_seconds"]
            + resource["closing_wall_seconds"]
            + 5
        )
        resource["cpu_with_closing_and_bootstrap_allowance_seconds"] = (
            resource["measured_worker_and_driver_cpu_seconds"]
            + resource["closing_process_cpu_seconds"]
            + 5
        )
        assert (
            resource["aggregate_wall_with_closing_and_bootstrap_allowance_seconds"]
            < 18000
        )
        assert resource["cpu_with_closing_and_bootstrap_allowance_seconds"] < 21600
        initial = json.loads((root / "initial.json").read_text())
        resource["elapsed_session_wall_seconds_at_seal"] = (
            time.time() - initial["started_epoch"]
        )
        (root / "resources.json").write_text(json.dumps(resource, indent=2) + "\n")
        evidence["resources.json"] = digest(root / "resources.json")
        result = {
            "status": "COMPLETE_AUTHORIZED_ENGINEERING_DIAGNOSTICS",
            "gate": "INCONCLUSIVE",
            "blockers": [
                "BENCHMARK_COMPATIBILITY_BLOCKED",
                "SOURCE_GENERATION_BLOCKED",
            ],
            "completed_utc": datetime.now(UTC).isoformat(),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "resources": resource,
            "evidence_sha256": evidence,
            "maintained_sha256": {p: digest(Path(p)) for p in changed},
            "reused_inputs": {
                "data": str((root / "data").resolve()),
                "upstream": str((root / "upstream").resolve()),
                "previous_seal_sha256": initial["previous_seal_sha256"],
            },
            "seal_scope": "All regular new run files; input directory symlinks refer to byte-verified prior evidence. The nonrecursive completion manifest and final read-only verification follow this checkpoint.",
        }
        (root / "completion_manifest.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    print(json.dumps(resource, indent=2))


if __name__ == "__main__":
    main()
