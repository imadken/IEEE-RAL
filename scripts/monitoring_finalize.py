"""Seal completed monitoring evidence after integrity, resource and job checks."""

import argparse
import hashlib
import json
import os
import stat
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_hashes(expected: dict[str, str]) -> int:
    for name, value in expected.items():
        if not Path(name).is_file() or digest(Path(name)) != value:
            raise ValueError(f"Preserved or sealed file changed: {name}")
    return len(expected)


def unique_bytes(roots: list[Path]) -> dict[str, int]:
    seen = set()
    logical = allocated = 0
    for root in roots:
        paths = root.rglob("*") if root.is_dir() else (root,)
        for path in paths:
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                continue
            identity = info.st_dev, info.st_ino
            if identity in seen:
                continue
            seen.add(identity)
            logical += info.st_size
            allocated += info.st_blocks * 512
    return {
        "unique_logical_bytes_before_seal": logical,
        "unique_allocated_bytes_before_seal": allocated,
        "unique_file_inodes": len(seen),
    }


def active_workers(root: Path) -> list[int]:
    active = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = process.info["cmdline"] or []
            if process.pid == os.getpid():
                continue
            command = any(Path(arg).name == "monitoring_command.py" for arg in argv)
            experiment = "dual_rec.monitoring.experiment" in argv
            if (command or experiment) and str(root) in argv:
                active.append(process.pid)
        except psutil.Error:
            continue
    return active


def finalize(root: Path, report: Path) -> dict:
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence is already sealed")
    initial = json.loads((root / "initial.json").read_text())
    seal = json.loads((root / "qualification_seal.json").read_text())
    jobs = active_workers(root)
    if jobs:
        raise ValueError(f"Research workers are still running: {jobs}")
    preserved = verify_hashes(initial["prior_sha256"])
    frozen = verify_hashes(seal["source_sha256"])
    audits = {}
    for split in ("baseline_development", "development", "qualification", "smoke"):
        value = json.loads((root / split / "audit.json").read_text())
        if value["status"] != "PASS" or value["mismatches"]:
            raise ValueError(f"Independent audit failed: {split}")
        audits[split] = value["checked_counts"]
    for log, token in (
        ("final-complete-tests.log", "passed"),
        ("final-lint-complete.log", "All checks passed"),
        ("final-format-complete.log", "files already formatted"),
    ):
        if token not in (root / log).read_text():
            raise ValueError(f"Final validation missing: {log}")
    rows = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    external = json.loads(
        (root / "compatibility/monitoring-benchmark-resources.json").read_text()
    )
    elapsed = time.time() - initial["started_epoch"]
    cpu = sum(r["cpu_seconds"] for r in rows) + external["recorded_process_cpu_seconds"]
    roots = [
        root,
        Path(".cache/monitoring-upstream"),
        *Path("/tmp").glob("monitoring*"),
    ]
    roots += [
        *Path("src/dual_rec/monitoring").glob("*.py"),
        *Path("scripts").glob("monitoring_*.py"),
        *Path("tests").glob("test_monitoring_*.py"),
        report,
        Path("MONITORING_STUDY_PROTOCOL.md"),
    ]
    sizes = unique_bytes(roots)
    # Four simultaneous agent slots bound aggregate active worker wall time even
    # if every slot is conservatively charged for all idle and tool-wait time.
    resources = {
        "captured_utc": datetime.now(UTC).isoformat(),
        "campaign_elapsed_seconds": elapsed,
        "aggregate_agent_wall_upper_bound_seconds": elapsed * 4,
        "recorded_subprocess_wall_seconds": sum(r["wall_seconds"] for r in rows)
        + external["recorded_process_wall_seconds"],
        "recorded_subprocess_cpu_seconds": cpu,
        "recorded_cpu_core_hours": cpu / 3600,
        "cpu_scope": "Substantive commands plus isolated compatibility/install workers; nested planner CPU already included. Read-only bootstrap/editor/tool-service overhead is not CPU-metered.",
        "gpu_physics_training_seconds": 0,
        **sizes,
        "manifest_metadata_reserve_bytes": 2_000_000,
        "artifact_upper_bound_bytes": max(
            sizes["unique_logical_bytes_before_seal"],
            sizes["unique_allocated_bytes_before_seal"],
        )
        + 2_000_000,
        "command_rows": len(rows),
        "compatibility_command_rows": external["commands"],
        "nonzero_command_rows": [
            {"name": r["name"], "exit_status": r["exit_status"]}
            for r in rows
            if r["exit_status"]
        ],
        "no_active_research_workers": True,
    }
    if (
        resources["aggregate_agent_wall_upper_bound_seconds"] >= 21600
        or cpu >= 28800
        or resources["artifact_upper_bound_bytes"] >= 4_000_000_000
    ):
        raise ValueError("Resource ceiling exceeded")
    marker = "<!-- MONITORING_RESOURCE_ACCOUNTING -->"
    text = report.read_text()
    if marker not in text:
        raise ValueError("Report accounting placeholder missing")
    paragraph = (
        f"Resource capture: **{resources['captured_utc']}**. Elapsed campaign wall time "
        f"**{elapsed / 60:.2f} minutes**; aggregate agent-wall conservative upper bound "
        f"**{elapsed * 4 / 3600:.3f} hours** (six-hour cap, including idle/wait time). "
        f"Recorded substantive subprocess wall time **{resources['recorded_subprocess_wall_seconds']:.3f} s**, "
        f"CPU **{cpu:.3f} s = {cpu / 3600:.5f} core-hours** (eight-core-hour cap). "
        f"GPU physics/training **0 s**. Unique allocated artifacts before the seal "
        f"**{sizes['unique_allocated_bytes_before_seal']:,} bytes**; conservative artifact upper bound "
        f"including manifest metadata **{resources['artifact_upper_bound_bytes']:,} bytes** "
        f"(four-GB cap). Dependencies/cache hardlinks are counted once. "
        "Read-only bootstrap/editor/tool-service CPU is not metered; no measurements are invented for it. "
        "No detached research workers remain. Exact scopes, commands and exit statuses are in "
        "`resources.json`, `commands.jsonl` and the compatibility ledger."
    )
    report.write_text(text.replace(marker, paragraph))
    (root / "resources.json").write_text(json.dumps(resources, indent=2))
    (root / "integrity.json").write_text(
        json.dumps(
            {
                "prior_files_preserved": preserved,
                "sealed_files_unchanged": frozen,
                "independent_audits": audits,
                "active_workers": jobs,
                "qualification_source_commit": seal["implementation_commit"],
            },
            indent=2,
        )
    )
    sources = {
        str(p): digest(p)
        for p in sorted(set(roots[1:]))
        if p.is_file() and p.suffix in {".py", ".md"}
    }
    source_paths = [
        *Path("src/dual_rec/monitoring").glob("*.py"),
        *Path("scripts").glob("monitoring_*.py"),
        *Path("tests").glob("test_monitoring_*.py"),
        report,
        Path("MONITORING_STUDY_PROTOCOL.md"),
    ]
    sources.update({str(p): digest(p) for p in source_paths})
    manifest = {
        "status": "COMPLETE_CASE_B_NO_GO",
        "manual_publication_only": True,
        "qualification_implementation_commit": seal["implementation_commit"],
        "source_sha256": sources,
        "artifacts": {
            str(p.relative_to(root)): {"sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(root.rglob("*"))
            if p.is_file()
        },
        "resources": resources,
    }
    (root / "completion_manifest.json").write_text(json.dumps(manifest, indent=2))
    return resources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--report", type=Path, default=Path("MONITORING_GATE_REPORT.md")
    )
    args = parser.parse_args()
    print(json.dumps(finalize(args.root, args.report), indent=2))


if __name__ == "__main__":
    main()
