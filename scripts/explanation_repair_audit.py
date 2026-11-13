"""Recompute development truth and metrics independently of the repair engine."""

import argparse
from pathlib import Path

from dual_rec.explanation_repair.audit import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed; use final read-only integrity verification")
    run(args.root)
