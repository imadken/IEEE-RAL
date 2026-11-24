"""Verify the stopped pilot or independently recount it, without new physics."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

from rpd_pilot_common import BASE, sha, verify_registration, write_json


def check_archive(path, expected):
    seen = {}
    with tarfile.open(path, "r:xz") as archive:
        for member in archive:
            name = Path(member.name)
            assert member.isfile() and not name.is_absolute() and ".." not in name.parts
            assert member.name not in seen
            content = archive.extractfile(member)
            digest = hashlib.file_digest(content, "sha256").hexdigest()
            assert expected[member.name] == digest, member.name
            seen[member.name] = digest
    assert seen == expected
    return len(seen)


def verify():
    manifest = json.loads((BASE / "integrity_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert sha(name) == expected, name
    verify_registration()
    archive = json.loads((BASE / "compact_manifest.json").read_text())
    path = BASE / "compact_evidence.tar.xz"
    assert sha(path) == archive["archive_sha256"]
    count = check_archive(path, archive["members"])
    print(
        json.dumps(
            {
                "passed": True,
                "integrity_files": len(manifest["files"]),
                "archive_members": count,
                "physics_restarted": False,
                "physical_decision": "SOURCE_NOT_QUALIFIED",
            }
        )
    )


def audit(output):
    assert not output.exists(), "Fresh offline output required"
    output.mkdir(parents=True)
    env = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    steps = []
    for script, reference in [
        ("scripts/rpd_pilot_audit.py", "independent_trace_audit"),
        ("scripts/rpd_pilot_closure.py", "final_audit"),
        ("scripts/rpd_pilot_source_review.py", "source_review"),
    ]:
        destination = output / reference
        log = output / (reference + ".txt")
        with log.open("x") as stream:
            result = subprocess.run(
                [sys.executable, script, "--output", str(destination)],
                env=env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=300,
            )
        assert result.returncode == 0, str(log)
        matched = []
        for expected in sorted((BASE / reference).glob("*")):
            assert expected.is_file()
            assert sha(expected) == sha(destination / expected.name), expected.name
            matched.append(expected.name)
        steps.append(
            {
                "script": script,
                "matched_outputs": matched,
                "returncode": result.returncode,
            }
        )
    write_json(
        output / "reproduction_receipt.json",
        {
            "passed": True,
            "steps": steps,
            "new_physics": 0,
            "no_native_worker_launched": True,
            "scope": "Byte-exact independent source trace and forensic accounting, same sealed native evidence",
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "scientific_outputs_matched": sum(
                    len(s["matched_outputs"]) for s in steps
                ),
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    assert args.verify != args.audit
    if args.verify:
        verify()
    else:
        assert args.output is not None
        audit(args.output)
