"""Seal completed local freshness evidence without editing reports or prior files.

Run directly after the metered validation/audit workers have exited. The caller's
worker-completion assertion complements the visible-process check: a sandbox's
process list cannot establish that other process namespaces contain no workers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil

HISTORICAL_FILE_COUNT = 673
SEALED_FILE_COUNT = 21
WALL_LIMIT = 21_600
CPU_LIMIT = 28_800
ARTIFACT_LIMIT = 4_000_000_000
METADATA_RESERVE = 2_000_000
OUTPUTS = ("resources.json", "integrity.json", "completion_manifest.json")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


def verify_hashes(expected: dict[str, str]) -> int:
    for name, value in expected.items():
        path = Path(name)
        if not path.is_file() or digest(path) != value:
            raise ValueError(f"Preserved or sealed file changed: {name}")
    return len(expected)


def unique_bytes(roots: list[Path]) -> dict[str, int]:
    """Count hardlinked files once; count symlink storage without following it."""
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


def active_workers(root: Path) -> list[dict]:
    found = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            if process.pid == os.getpid():
                continue
            argv = process.info["cmdline"] or []
            worker = any(
                Path(arg).name.startswith("revalidation_") and Path(arg).suffix == ".py"
                for arg in argv
            ) or any(arg.startswith("dual_rec.revalidation.") for arg in argv)
            refers_to_run = any(
                Path(arg).resolve() == root.resolve()
                for arg in argv
                if not arg.startswith("-")
            )
            if worker and refers_to_run:
                found.append({"pid": process.pid, "command": argv})
        except (psutil.Error, OSError, ValueError):
            continue
    return found


def validation_sources() -> list[Path]:
    paths = [
        p
        for folder in ("src/dual_rec", "scripts", "tests", "config")
        for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix in {".py", ".json"}
    ]
    return sorted(
        {
            *paths,
            Path("pyproject.toml"),
            Path("uv.lock"),
            Path("EVIDENCE_REVALIDATION_PROTOCOL.md"),
        }
    )


def read_commands(path: Path, *, verify_logs: bool = True) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    names = set()
    for row in rows:
        for key in ("cpu_seconds", "wall_seconds"):
            value = row[key]
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"Invalid resource measurement in {path}: {key}")
        if "name" in row:
            if row["name"] in names:
                raise ValueError(f"Duplicate command name in {path}: {row['name']}")
            names.add(row["name"])
        if verify_logs and row.get("log_sha256"):
            log = path.parent / (row["name"] + ".log")
            if not log.is_file() or digest(log) != row["log_sha256"]:
                raise ValueError(f"Command log changed: {log}")
    return rows


def verify_validations(root: Path, rows: list[dict], selected: dict[str, str]) -> dict:
    if set(selected) != {"tests", "lint", "format"}:
        raise ValueError("Final tests, lint and format commands are required")
    by_name = {row["name"]: row for row in rows}
    sources = {str(path): digest(path) for path in validation_sources()}
    checks = {}
    for kind, name in selected.items():
        if name not in by_name:
            raise ValueError(f"Final validation command missing: {name}")
        row = by_name[name]
        command = row["command"]
        log = root / (name + ".log")
        if row["exit_status"] != 0 or row.get("termination_reason"):
            raise ValueError(f"Final validation failed: {name}")
        if not log.is_file() or digest(log) != row.get("log_sha256"):
            raise ValueError(f"Final validation log changed: {name}")
        if kind == "tests":
            valid = "pytest" in command and re.search(
                r"\b[1-9]\d* passed\b", log.read_text()
            )
        elif kind == "lint":
            valid = (
                "ruff" in command
                and "check" in command
                and "All checks passed" in log.read_text()
            )
        else:
            valid = (
                "ruff" in command
                and "format" in command
                and "--check" in command
                and "already formatted" in log.read_text()
            )
        if not valid:
            raise ValueError(f"Final validation evidence missing: {kind}")
        if any(
            row.get("source_sha256", {}).get(p) != value for p, value in sources.items()
        ):
            raise ValueError(f"Source changed since final validation: {name}")
        checks[kind] = {"command_name": name, "log_sha256": digest(log)}
    return checks


def verify_split(
    root: Path, split: str, expected_parents: list[str] | None = None
) -> dict:
    directory = root / split
    status = read_json(directory / "status.json")
    audit = read_json(directory / "audit.json")
    if audit.get("status") != "PASS" or audit.get("mismatches") != []:
        raise ValueError(f"Independent audit failed: {split}")
    if status.get("split") != split or audit.get("split") != split:
        raise ValueError(f"Split label mismatch: {split}")
    counts = audit["checked_counts"]
    expected = {
        "episodes": status["episodes"],
        "rows": status["rows"],
        "recomputed_rows": status["evaluated"],
        "reference_skips": sum(status["reference_skips"].values()),
        "parent_instances": len(status["parents"]),
    }
    if (
        counts != expected
        or expected["rows"] != expected["recomputed_rows"] + expected["reference_skips"]
    ):
        raise ValueError(f"Completed status/audit count mismatch: {split}")
    if expected["episodes"] <= 0 or expected["recomputed_rows"] <= 0:
        raise ValueError(f"Empty completed stage: {split}")
    if sorted(audit["parents"]) != sorted(status["parents"]):
        raise ValueError(f"Audit parent mismatch: {split}")
    if expected_parents is not None and sorted(status["parents"]) != sorted(
        expected_parents
    ):
        raise ValueError(f"Registered qualification parent mismatch: {split}")
    fingerprints = audit["source_sha256"]
    required = [
        directory / name
        for name in ("episodes.jsonl.gz", "decisions.jsonl.gz", "status.json")
    ]
    fingerprint_paths = {Path(name).resolve() for name in fingerprints}
    if any(path.resolve() not in fingerprint_paths for path in required):
        raise ValueError(f"Audit input fingerprint missing: {split}")
    verify_hashes(fingerprints)
    return {"checked_counts": counts, "audit_sha256": digest(directory / "audit.json")}


def verify_analysis(root: Path, split: str) -> dict:
    directory = root / split
    summary = read_json(directory / "analysis/summary.json")
    status = read_json(directory / "status.json")
    selection = read_json(root / "selection.json")
    if any(
        summary[key] != status[other]
        for key, other in (
            ("episodes", "episodes"),
            ("evaluated_rows", "evaluated"),
        )
    ) or summary["reference_skip_rows"] != sum(status["reference_skips"].values()):
        raise ValueError(f"Analysis count mismatch: {split}")
    if (
        summary["selection_sha256"] != digest(root / "selection.json")
        or summary["primary_baseline"] != selection["primary_baseline"]
    ):
        raise ValueError(f"Analysis frozen selection mismatch: {split}")
    expected = summary["source_sha256"]
    if set(expected) != {"episodes.jsonl.gz", "decisions.jsonl.gz"}:
        raise ValueError(f"Analysis input fingerprint missing: {split}")
    verify_hashes({str(directory / name): value for name, value in expected.items()})
    plots = summary["plots"]["files"]
    if not plots or any(
        not (directory / "analysis" / name).is_file()
        or (directory / "analysis" / name).stat().st_size == 0
        for name in plots
    ):
        raise ValueError(f"Analysis figures missing: {split}")
    return {
        "summary_sha256": digest(directory / "analysis/summary.json"),
        "figure_files": plots,
    }


def artifact_roots(root: Path, report: Path) -> list[Path]:
    return [
        root,
        *Path("/tmp").glob("revalidation*"),
        *Path("/tmp").glob("pytest-of-*"),
        Path(".git"),
        Path("/tmp/dual-rec-uv-cache"),
        Path("src/dual_rec/revalidation"),
        *Path("scripts").glob("revalidation_*.py"),
        *Path("tests").glob("test_revalidation_*.py"),
        Path("config/evidence_revalidation_20261111.json"),
        Path("EVIDENCE_REVALIDATION_PROTOCOL.md"),
        report,
    ]


def finalize(
    root: Path,
    report: Path,
    approved_gitignore_sha256: str,
    validations: dict[str, str],
    *,
    workers_finished: bool = False,
) -> dict:
    started_cpu = time.process_time()
    if any((root / name).exists() for name in OUTPUTS):
        raise ValueError("Evidence already sealed or final outputs already exist")
    if not workers_finished:
        raise ValueError("Caller must confirm all known worker sessions finished")
    jobs = active_workers(root)
    if jobs:
        raise ValueError(f"Visible research workers still running: {jobs}")
    initial = read_json(root / "initial.json")
    seal = read_json(root / "qualification_seal.json")
    previous = initial["prior_sha256"]
    frozen = seal["source_sha256"]
    if len(previous) != HISTORICAL_FILE_COUNT or len(frozen) != SEALED_FILE_COUNT:
        raise ValueError("Historical/sealed inventory count mismatch")
    if ".gitignore" not in previous:
        raise ValueError("Historical .gitignore inventory entry missing")
    provenance = read_json(root / "provenance/gitignore_integrity_event.json")
    if provenance.get("user_steering_sha256") != approved_gitignore_sha256:
        raise ValueError("Approved .gitignore hash differs from retained user steering")
    preserved = verify_hashes(
        {p: value for p, value in previous.items() if p != ".gitignore"}
    )
    verify_hashes({".gitignore": approved_gitignore_sha256})
    sealed = verify_hashes(frozen)
    if not report.is_file() or not report.read_text().strip():
        raise ValueError("Final report missing")
    audits = {
        split: verify_split(
            root,
            split,
            seal["qualification_parent_ids"] if split == "qualification" else None,
        )
        for split in ("development", "qualification")
    }
    analyses = {
        split: verify_analysis(root, split)
        for split in ("development", "qualification")
    }
    ledgers = [root / "commands.jsonl", root / "benchmarks/commands.jsonl"]
    command_rows = read_commands(ledgers[0])
    benchmark_rows = read_commands(ledgers[1])
    checks = verify_validations(root, command_rows, validations)
    benchmark = read_json(root / "benchmarks/resources.json")
    if not benchmark.get("all_planning_and_install_jobs_finished"):
        raise ValueError("Source preparation workers not completed")
    for key in ("cpu_seconds", "wall_seconds"):
        if not math.isclose(
            sum(row[key] for row in benchmark_rows), benchmark[key], abs_tol=1e-7
        ):
            raise ValueError(f"Source preparation ledger summary mismatch: {key}")
    if len(benchmark_rows) != benchmark["commands"]:
        raise ValueError("Source preparation command count mismatch")
    reproduction_ledgers = sorted(
        {
            *root.glob("provenance/revalidation*commands*.jsonl"),
            *Path("/tmp").glob("revalidation*commands*.jsonl"),
        }
    )
    # Copies of the same measured command may exist in /tmp and provenance.
    # Deduplicate full records, never merely equal command strings or names.
    extra = {}
    for path in reproduction_ledgers:
        for row in read_commands(path, verify_logs=False):
            extra[json.dumps(row, sort_keys=True)] = row
    records = command_rows + benchmark_rows + list(extra.values())
    driver = read_json(root / "benchmarks/planning_status.json")[
        "driver_self_cpu_seconds"
    ]
    if not math.isfinite(driver) or driver < 0:
        raise ValueError("Invalid source-preparation driver CPU")
    sources = {str(p): digest(p) for p in validation_sources()}
    sources[str(report)] = digest(report)
    sources[".gitignore"] = approved_gitignore_sha256
    roots = artifact_roots(root, report)
    sizes = unique_bytes(roots)
    artifacts = {
        str(path.relative_to(root)): {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    elapsed = time.time() - initial["started_epoch"]
    own_cpu = time.process_time() - started_cpu
    cpu = sum(row["cpu_seconds"] for row in records) + driver + own_cpu
    resources = {
        "captured_utc": datetime.now(UTC).isoformat(),
        "campaign_elapsed_seconds": elapsed,
        "recorded_subprocess_wall_seconds": sum(row["wall_seconds"] for row in records),
        "recorded_subprocess_cpu_seconds": cpu - own_cpu,
        "finalizer_cpu_seconds_through_capture": own_cpu,
        "recorded_cpu_seconds_through_capture": cpu,
        "recorded_cpu_core_hours_through_capture": cpu / 3600,
        "cpu_scope": "Metered main commands, source-preparation commands, preparation driver self CPU, deduplicated reproduction commands, and this finalizer through capture. Read-only editor/tool-service/bootstrap CPU is unmetered; final JSON writes occur after capture.",
        "wall_scope": "Campaign elapsed wall is limited to six hours; overlapping command wall is summed separately and is not CPU time.",
        "gpu_training_seconds": 0,
        "paid_calls": 0,
        "command_rows": len(command_rows),
        "source_preparation_command_rows": len(benchmark_rows),
        "deduplicated_reproduction_command_rows": len(extra),
        "source_preparation_driver_self_cpu_seconds": driver,
        "nonzero_commands": [
            {"name": row.get("name"), "exit_status": row["exit_status"]}
            for row in records
            if row["exit_status"]
        ],
        **sizes,
        "metadata_reserve_bytes": METADATA_RESERVE,
        "artifact_upper_bound_bytes": max(
            sizes["unique_logical_bytes_before_seal"],
            sizes["unique_allocated_bytes_before_seal"],
        )
        + METADATA_RESERVE,
        "artifact_roots": [str(p) for p in roots],
        "artifact_scope": "Includes entire Git storage and matching /tmp/revalidation* and /tmp/pytest-of-* trees, conservatively counting preexisting allocations too. Reused historical environments/evidence are excluded. Overlapping roots and hardlinks are counted once; the metadata reserve covers final small report/admin commit growth.",
        "caller_asserts_all_known_worker_sessions_finished": True,
        "visible_workers": jobs,
        "worker_check_scope": "Caller session-completion assertion, completed stage/audit/preparation records, and process list visible in this namespace; no claim of global process visibility.",
        "limits": {
            "wall_seconds": WALL_LIMIT,
            "cpu_seconds": CPU_LIMIT,
            "artifact_bytes": ARTIFACT_LIMIT,
        },
    }
    if (
        elapsed < 0
        or elapsed > WALL_LIMIT
        or cpu > CPU_LIMIT
        or resources["artifact_upper_bound_bytes"] >= ARTIFACT_LIMIT
    ):
        raise ValueError("Resource ceiling exceeded")
    if active_workers(root):
        raise ValueError("Research worker appeared during finalization")
    integrity = {
        "historical_inventory_entries": len(previous),
        "historical_files_preserved": preserved,
        "sealed_files_unchanged": sealed,
        "independent_audits": audits,
        "completed_analyses": analyses,
        "approved_historical_exception": {
            "path": ".gitignore",
            "original_sha256": previous[".gitignore"],
            "approved_sha256": approved_gitignore_sha256,
        },
        "final_validation": checks,
        "qualification_implementation_commit": seal["implementation_commit"],
    }
    resources_body = json.dumps(resources, indent=2, allow_nan=False) + "\n"
    integrity_body = json.dumps(integrity, indent=2, allow_nan=False) + "\n"
    for name, body in (
        ("resources.json", resources_body),
        ("integrity.json", integrity_body),
    ):
        artifacts[name] = {
            "sha256": hashlib.sha256(body.encode()).hexdigest(),
            "bytes": len(body.encode()),
        }
    manifest = {
        "status": "COMPLETE_AUDITED_STUDY",
        "manual_publication_only": True,
        "raw_evidence_local_only": True,
        "qualification_implementation_commit": seal["implementation_commit"],
        "source_sha256": sources,
        "artifacts": artifacts,
        "resource_record": "resources.json",
        "integrity_record": "integrity.json",
        "manifest_scope": "All pre-seal files under the local run plus resources/integrity; this manifest excludes its own recursive hash.",
    }
    bodies = {
        "resources.json": resources_body,
        "integrity.json": integrity_body,
        "completion_manifest.json": json.dumps(manifest, indent=2, allow_nan=False)
        + "\n",
    }
    if sum(len(body.encode()) + 4096 for body in bodies.values()) > METADATA_RESERVE:
        raise ValueError("Final metadata exceeds artifact reserve")
    created = []
    try:
        for name, body in bodies.items():
            path = root / name
            with path.open("x") as stream:
                created.append(path)
                stream.write(body)
    except BaseException:
        for path in created:
            path.unlink()
        raise
    return resources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--approved-gitignore-sha256", required=True)
    parser.add_argument(
        "--validation", action="append", default=[], metavar="KIND=COMMAND"
    )
    parser.add_argument("--workers-finished", action="store_true")
    args = parser.parse_args()
    validations = {}
    for item in args.validation:
        key, separator, value = item.partition("=")
        if not separator or key in validations or not value:
            parser.error("Use each --validation KIND=COMMAND once")
        validations[key] = value
    print(
        json.dumps(
            finalize(
                args.root,
                args.report,
                args.approved_gitignore_sha256,
                validations,
                workers_finished=args.workers_finished,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
