"""Verify sealed closure artifacts, or repeat all offline scientific analyses."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

BASE = Path("research/dsre_experimental_closure")
FINAL = BASE / "final"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify():
    manifest = json.loads((BASE / "closure_manifest.json").read_text())
    for path, expected in manifest["files"].items():
        assert digest(path) == expected, path
    package = json.loads((BASE / "compact_archive_receipt.json").read_text())
    assert digest(package["archive"]) == package["archive_sha256"]
    with tarfile.open(package["archive"], "r:xz") as archive:
        members = {m.name: m for m in archive.getmembers() if m.isfile()}
        assert set(members) == set(package["members"])
        for name, expected in package["members"].items():
            assert (
                hashlib.sha256(archive.extractfile(members[name]).read()).hexdigest()
                == expected
            )
    print(
        json.dumps(
            {
                "passed": True,
                "sealed_files": len(manifest["files"]),
                "compact_archive_members": len(package["members"]),
            }
        )
    )


def normalized(value, roots):
    """Exclude runtime metadata; retain numerical, source and decision content."""
    excluded = {
        "input_sha256",
        "successful_reads",
        "created_epoch",
        "timing",
        "audit_source_sha256",
        "timing_note",
    }
    if isinstance(value, dict):
        return {k: normalized(v, roots) for k, v in value.items() if k not in excluded}
    if isinstance(value, list):
        return [normalized(v, roots) for v in value]
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, str):
        for root in roots:
            value = value.replace(str(root.resolve()), "<CLOSURE>").replace(
                str(root), "<CLOSURE>"
            )
    return value


def full(output):
    assert not output.exists(), "Reproduction must use a fresh output directory"
    start = time.time()
    environment = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/dsre_closure_run.py",
            "--reproduction",
            "--output",
            str(output),
        ],
        check=True,
        env=environment,
    )
    compared = []
    files = [
        "E0/math_audit.json",
        "E0/checkpoint_and_parent_identity_audit.json",
        "E0/raw_integrity_and_insertion_boundary.json",
        "E0/recount/independent_numbers.json",
        "E1/calibration_freeze.json",
        "E1/obligation_results.json",
        "E2/source_curves.json",
        "E3/full_certificate_audit.json",
        "E4/physical_witnesses_and_ablations.json",
        "E5/observation_error_sensitivity.json",
    ]
    for path in files:
        original = json.loads((FINAL / path).read_text())
        repeated = json.loads((output / path).read_text())
        a = normalized(original, [FINAL, output])
        b = normalized(repeated, [FINAL, output])
        assert a == b, f"Scientific reproduction differs: {path}"
        projection = json.dumps(a, sort_keys=True, separators=(",", ":"))
        compared.append(
            {
                "artifact": path,
                "scientific_projection_sha256": hashlib.sha256(
                    projection.encode()
                ).hexdigest(),
            }
        )
    receipt = {
        "passed": True,
        "compared": compared,
        "wall_seconds": time.time() - start,
        "fresh_output": str(output),
        "new_physics": 0,
        "comparison_scope": "All scientific values/decisions/sources in ten artifacts; exclude timings, timestamps and relocation-dependent input-file digests",
    }
    (output / "independent_reproduction_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/dsre-closure-independent-reproduction"),
    )
    args = parser.parse_args()
    assert args.verify or args.full
    if args.verify:
        verify()
    if args.full:
        full(args.output)
