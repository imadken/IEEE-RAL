"""Integrity verification and isolated offline reproduction of the RPD package."""

import argparse
import hashlib
import json
import lzma
import os
import resource
import subprocess
import sys
import tarfile
import time
from pathlib import Path

BASE = Path("research/rpd_method_challenge")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def archive_check(path, members, destination=None):
    found = {}
    with tarfile.open(path, "r:xz") as stream:
        for member in stream:
            p = Path(member.name)
            assert member.isfile() and not p.is_absolute() and ".." not in p.parts
            assert member.name not in found
            content = stream.extractfile(member).read()
            digest = hashlib.sha256(content).hexdigest()
            assert members.get(member.name) == digest, member.name
            found[member.name] = digest
            if destination is not None:
                target = destination / p
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output:
                    output.write(content)
    assert found == members
    return len(found)


def verify():
    manifest = json.loads((BASE / "integrity_manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha(name) == digest, name
    source = json.loads((BASE / "source_bundle_manifest.json").read_text())
    compact = json.loads((BASE / "compact_manifest.json").read_text())
    counts = [
        archive_check(BASE / "source_bundle.tar.xz", source["members"]),
        archive_check(BASE / "compact_package.tar.xz", compact["members"]),
    ]
    print(
        json.dumps(
            {
                "passed": True,
                "verified_files": len(manifest["files"]),
                "archive_members": counts,
                "new_physics": 0,
            }
        )
    )


def projection(value):
    if isinstance(value, dict):
        return {
            k: projection(v)
            for k, v in value.items()
            if k not in {"wall_seconds", "historical_source_input_sha256"}
        }
    if isinstance(value, list):
        return [projection(v) for v in value]
    return value


def reproduce(output, portable):
    assert not output.exists(), "Fresh output required"
    output.mkdir(parents=True)
    output = output.resolve()
    source = Path.cwd()
    source_members = None
    if portable:
        source = output / "source"
        source.mkdir()
        manifest = json.loads((BASE / "source_bundle_manifest.json").read_text())
        source_members = archive_check(
            BASE / "source_bundle.tar.xz", manifest["members"], source
        )
    result = output / "results"
    result.mkdir()
    env = dict(
        os.environ,
        PYTHONPATH=f"{source / 'src'}:{source / 'scripts'}:{source}",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    start = time.perf_counter()
    steps = []
    commands = [
        ("supplied_reference", [str(BASE / "supervisor/finite_world_probe_check.py")]),
        ("finite", ["scripts/rpd_audit.py", "--output", str(result / "finite")]),
        ("source", ["scripts/rpd_source_audit.py", "--output", str(result / "source")]),
        (
            "stage2",
            ["scripts/rpd_stage2_protocol.py", "--output", str(result / "stage2")],
        ),
        ("tests", ["-m", "pytest", "-q", "tests/test_recoverability_planner.py"]),
    ]
    for name, args in commands:
        begin = time.perf_counter()
        log = output / (name + ".txt")
        with log.open("w") as stream:
            completed = subprocess.run(
                [sys.executable, *args],
                cwd=source,
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=1800,
                check=False,
            )
        assert completed.returncode == 0, f"See {log}"
        steps.append(
            {
                "name": name,
                "returncode": completed.returncode,
                "wall_seconds": time.perf_counter() - begin,
                "log_sha256": sha(log),
            }
        )
        assert time.perf_counter() - start < 3600
        print("REPRODUCED", name, flush=True)
    expected = json.loads((BASE / "reference_check_actual.json").read_text())
    assert json.loads((output / "supplied_reference.txt").read_text()) == expected
    matches = []
    for p in sorted((BASE / "final").rglob("*")):
        relative = p.relative_to(BASE / "final")
        if relative.parts[0] not in {"finite", "source", "stage2"} or not p.is_file():
            continue
        candidate = result / relative
        if p.suffix == ".xz":
            with lzma.open(p, "rt") as a, lzma.open(candidate, "rt") as b:
                from itertools import zip_longest

                for old, new in zip_longest(a, b):
                    assert old is not None and new is not None
                    assert projection(json.loads(old)) == projection(json.loads(new)), (
                        str(relative)
                    )
        elif p.suffix == ".json":
            assert projection(json.loads(p.read_text())) == projection(
                json.loads(candidate.read_text())
            ), str(relative)
        elif p.suffix == ".jsonl":
            assert p.read_bytes() == candidate.read_bytes(), str(relative)
        else:
            continue
        matches.append(str(relative))
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt = {
        "passed": True,
        "mode": "PORTABLE_ISOLATED" if portable else "REPOSITORY_ISOLATED",
        "steps": steps,
        "matched_scientific_outputs": matches,
        "source_members_verified": source_members,
        "source_bundle_sha256": sha(BASE / "source_bundle.tar.xz")
        if portable
        else None,
        "excluded_projection_fields": [
            "wall_seconds",
            "historical_source_input_sha256",
        ],
        "wall_seconds": time.perf_counter() - start,
        "child_cpu_seconds": usage.ru_utime + usage.ru_stime,
        "new_physics": 0,
        "new_robot_outcomes": 0,
        "output_bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),
    }
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
    assert args.verify or args.full
    if args.verify:
        verify()
    if args.full:
        assert args.output is not None
        reproduce(args.output, args.portable)
