"""Verify the compact package with an existing compatible Python environment."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    os.chdir(bundle)
    inventory = json.loads((bundle / "compact_inventory.json").read_text())
    for name, wanted in inventory.items():
        with (bundle / name).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == wanted, name
    data = Path("results/dsre-evidence-aware/20261117-first-session/historical")
    scratch = Path(tempfile.mkdtemp(prefix="dsre-compact-verified-"))
    for name in ("models", "evaluations", "evaluator"):
        shutil.copytree(data / name, scratch / name)
    env = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    commands = [
        [
            sys.executable,
            "research/dsre_evidence_design/supervisor_reference.py",
            "--output",
            str(scratch / "supervisor.json"),
        ],
        [
            sys.executable,
            "scripts/dsre_evidence_audit.py",
            "numerical",
            str(scratch),
            "--relocated",
        ],
        [sys.executable, "scripts/dsre_evidence_statistical_audit.py", str(scratch)],
        [sys.executable, "-m", "pytest", "-q", "tests/test_evidence_aware.py"],
    ]
    for command in commands:
        subprocess.run(command, check=True, env=env)
    print(
        json.dumps(
            {
                "status": "PASS",
                "checked_members": len(inventory),
                "scratch": str(scratch),
                "scope": "Full numerical/statistical checks and source-boundary tests; physical raw sample and full-audit receipts included. Every-parent physical verification needs the full local evidence root.",
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
