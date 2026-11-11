"""Analyze completed freshness records under the frozen development comparator."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.revalidation.analysis import analyze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "qualification"), required=True
    )
    args = parser.parse_args()
    selection = json.loads((args.root / "selection.json").read_text())
    split = args.root / args.split
    result = analyze(split, split / "analysis", selection["primary_baseline"])
    print(json.dumps(result["primary"], indent=2))


if __name__ == "__main__":
    main()
