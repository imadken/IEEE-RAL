"""Integrity and clean-workspace offline reproduction; never launches physics."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from rpd_isolation_common import BASE, PRIOR, sha, verify_registration, write_json
from rpd_pilot_reproduce import check_archive


def verify():
    manifest = json.loads((BASE / "integrity_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert sha(name) == expected, name
    verify_registration()
    supplementary = json.loads((BASE / "environment_input_seal.json").read_text())
    for name, expected in supplementary["files"].items():
        assert sha(name) == expected
    archive = json.loads((BASE / "compact_manifest.json").read_text())
    path = BASE / "compact_evidence.tar.xz"
    assert sha(path) == archive["archive_sha256"]
    members = check_archive(path, archive["members"])
    print(
        json.dumps(
            {
                "passed": True,
                "integrity_files": len(manifest["files"]),
                "archive_members": members,
                "new_physics": 0,
            }
        )
    )


def clean(output):
    assert not output.exists(), "Fresh workspace required"
    root = output.resolve() / "source"
    root.mkdir(parents=True)
    source_files = list(Path("scripts").glob("rpd_isolation_*.py"))
    source_files += [
        Path("scripts/rpd_pilot_common.py"),
        Path("scripts/rpd_pilot_audit.py"),
    ]
    data_files = [BASE / "jobs.jsonl"]
    data_files += [p for p in (BASE / "physics").rglob("*") if p.is_file()]
    for task in ("PickCube-v1", "PushCube-v1"):
        data_files += list((PRIOR / "physics" / task / "parent_00").glob("*.json.xz"))
    copied = {}
    for path in sorted(set(source_files + data_files)):
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        assert sha(path) == sha(destination)
        copied[str(path)] = sha(path)
    env = dict(
        os.environ,
        PYTHONPATH=str(root / "scripts"),
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    steps = []
    commands = [
        (
            "audit",
            ["scripts/rpd_isolation_audit.py", "--output", str(BASE / "final_audit")],
        ),
        ("technical_view", ["scripts/rpd_isolation_handoff.py", "--json-only"]),
    ]
    for name, args in commands:
        with (output / (name + ".txt")).open("x") as log:
            result = subprocess.run(
                [sys.executable, *args],
                cwd=root,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=300,
            )
        assert result.returncode == 0, str(output / (name + ".txt"))
        steps.append({"name": name, "returncode": 0})
    matches = []
    for path in [BASE / "final_audit/summary.json", BASE / "technical_matches.json"]:
        assert sha(path) == sha(root / path), str(path)
        matches.append(str(path))
    write_json(
        output / "reproduction_receipt.json",
        {
            "passed": True,
            "copied_files": copied,
            "matched_outputs": matches,
            "steps": steps,
            "new_physics": 0,
            "scope": "Independent offline audit and retrospective technical option accounting in a clean source/data directory, using existing locked Python dependencies. No native worker launched.",
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "clean_copied_files": len(copied),
                "matched_outputs": matches,
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    assert args.verify != args.clean
    if args.verify:
        verify()
    else:
        assert args.output is not None
        clean(args.output)
