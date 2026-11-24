"""Verify or independently rerun the sealed offline ERR package; no physics."""

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import tarfile
import time
from pathlib import Path

BASE = Path("research/err_method_challenge")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_relative(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive member: {name}")
    return path


def verify_archive(archive, expected, destination=None):
    """Verify every member before permitting local, file-only extraction."""
    found = {}
    with tarfile.open(archive, "r:xz") as stream:
        for member in stream:
            relative = safe_relative(member.name)
            assert member.isfile() and member.name not in found, member.name
            content = stream.extractfile(member).read()
            digest = hashlib.sha256(content).hexdigest()
            assert expected.get(member.name) == digest, member.name
            found[member.name] = digest
            if destination is not None:
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output:
                    output.write(content)
    assert found == expected, "Archive member inventory differs"
    return len(found)


def verify():
    manifest = json.loads((BASE / "integrity_manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha(name) == digest, name
    raw = json.loads((BASE / "raw_source_manifest.json").read_text())
    count = verify_archive(BASE / "raw_source.tar.xz", raw["members"])
    compact = json.loads((BASE / "compact_manifest.json").read_text())
    second = verify_archive(BASE / "compact_package.tar.xz", compact["members"])
    print(
        json.dumps(
            {
                "verified_files": len(manifest["files"]),
                "raw_archive_members": count,
                "compact_archive_members": second,
                "new_physics": 0,
            }
        )
    )


def scientific(value):
    """Exclude only measured timing and location-dependent read inventories."""
    excluded = {
        "wall_seconds",
        "solver_wall_seconds",
        "input_sha256",
        "successful_reads",
    }
    if isinstance(value, dict):
        return {k: scientific(v) for k, v in value.items() if k not in excluded}
    if isinstance(value, list):
        return [scientific(v) for v in value]
    return value


def reproduce(output, *, portable=False):
    assert not output.exists(), "Choose a fresh output directory"
    output.mkdir(parents=True)
    output = output.resolve()
    repo = Path.cwd()
    receipt = {
        "mode": "ISOLATED_PORTABLE" if portable else "ISOLATED_REPOSITORY",
        "new_physics": 0,
        "new_robot_outcomes": 0,
        "steps": [],
    }
    if portable:
        source = output / "source"
        source.mkdir()
        raw = json.loads((BASE / "raw_source_manifest.json").read_text())
        receipt["source_archive_sha256"] = sha(BASE / "raw_source.tar.xz")
        receipt["source_members_verified"] = verify_archive(
            BASE / "raw_source.tar.xz", raw["members"], source
        )
    else:
        source = repo
    environment = dict(
        os.environ,
        PYTHONPATH=f"{source / 'src'}:{source / 'scripts'}:{source}",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    result = output / "results"
    result.mkdir()
    start = time.perf_counter()
    commands = [
        (
            "finite_models",
            ["scripts/err_method_audit.py", "--output", str(result / "finite_models")],
        ),
        (
            "robot",
            ["scripts/err_robot_witnesses.py", "--output", str(result / "robot")],
        ),
        (
            "stage2_reservation",
            [
                "scripts/err_stage2_manifest.py",
                "--output",
                str(result / "stage2_reservation"),
            ],
        ),
        (
            "focused_tests",
            ["-m", "pytest", "-q", "tests/test_experiment_resolvability.py"],
        ),
    ]
    for label, command in commands:
        began = time.perf_counter()
        log = output / (label + ".log")
        with log.open("w") as stream:
            completed = subprocess.run(
                [sys.executable, *command],
                cwd=source,
                env=environment,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=7200,
                check=False,
            )
        receipt["steps"].append(
            {
                "name": label,
                "returncode": completed.returncode,
                "wall_seconds": time.perf_counter() - began,
                "log_sha256": sha(log),
            }
        )
        assert completed.returncode == 0, f"Failed {label}; see {log}"
        assert time.perf_counter() - start < 10800, "3h reproduction bound"
        print("REPRODUCED", label, flush=True)
    comparisons = []
    for path in sorted((BASE / "final").rglob("*")):
        relative = path.relative_to(BASE / "final")
        if relative.parts[0] not in {"finite_models", "robot", "stage2_reservation"}:
            continue
        if path.suffix not in {".json", ".jsonl"}:
            continue
        candidate = result / relative
        if path.suffix == ".jsonl":
            with path.open() as old, candidate.open() as new:
                from itertools import zip_longest

                for a, b in zip_longest(old, new):
                    assert a is not None and b is not None, str(relative)
                    assert scientific(json.loads(a)) == scientific(json.loads(b)), str(
                        relative
                    )
        else:
            assert scientific(json.loads(path.read_text())) == scientific(
                json.loads(candidate.read_text())
            ), str(relative)
        comparisons.append(str(relative))
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt.update(
        passed=True,
        scientific_projection_matches=comparisons,
        excluded_comparison_fields=[
            "wall_seconds",
            "solver_wall_seconds",
            "input_sha256",
            "successful_reads",
        ],
        wall_seconds=time.perf_counter() - start,
        child_cpu_seconds=usage.ru_utime + usage.ru_stime,
        output_bytes=sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),
    )
    (output / "reproduction_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--portable", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    assert args.verify or args.full, "Specify --verify and/or --full"
    if args.verify:
        verify()
    if args.full:
        assert args.output is not None, "--full requires a fresh --output"
        reproduce(args.output, portable=args.portable)
