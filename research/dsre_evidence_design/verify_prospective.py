"""Verify an extracted compact bundle using the unchanged compatible environment."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)
    manifest = json.loads((root / "COMPACT_MANIFEST.json").read_text())
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        assert actual == expected, name
    env = os.environ.copy()
    env.update(
        PYTHONPATH="src:scripts:.", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"
    )
    scratch = Path(tempfile.mkdtemp(prefix="dsre-prospective-verify."))
    commands = [
        [
            "research/dsre_evidence_design/supervisor_reference.py",
            "--output",
            str(scratch / "oracle.json"),
        ],
        [
            "-m",
            "pytest",
            "-q",
            "tests/test_evidence_aware.py",
            "tests/test_evidence_aware_prospective.py",
        ],
    ]
    evidence = Path("results/dsre-evidence-aware/20261117-prospective")
    for task in ("PointMaze_UMaze-v3", "PickCube-v1", "PegInsertionSide-v1"):
        if (evidence / "prospective" / task / "models").exists():
            commands.append(
                [
                    "scripts/dsre_evidence_prospective_audit.py",
                    str(evidence),
                    "--task",
                    task,
                    "--numerical-only",
                    "--relocated",
                ]
            )
    commands.append(
        [
            "scripts/dsre_evidence_prospective_extended_audit.py",
            str(evidence),
            "--output",
            str(scratch / "extended_audit.json"),
        ]
    )
    for command in commands:
        subprocess.run([sys.executable, *command], check=True, env=env)
    print(
        json.dumps(
            {
                "verified_compact_files": len(manifest["sha256"]),
                "commands_completed": len(commands),
                "physics_scope": "sampled trajectories only in compact; every-parent raw physical audit remains local and hash-sealed",
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
