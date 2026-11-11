"""Analyze completed paired records and audit model-relative query relevance."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.analysis import analyze
from dual_rec.monitoring.relevance_audit import audit_queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "qualification"), required=True
    )
    args = parser.parse_args()
    directory = args.root / args.split
    summary = analyze(directory, directory / "analysis")
    relevance = audit_queries(directory, directory / "query_relevance.json")
    print(
        json.dumps(
            {"primary": summary["primary"], "query_methods": relevance["methods"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
