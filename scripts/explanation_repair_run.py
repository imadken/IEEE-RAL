"""CLI for the explicitly bounded explanation-repair development session."""

import argparse
from pathlib import Path

from dual_rec.explanation_repair.core import edit
from dual_rec.explanation_repair.experiment import run
from dual_rec.explanation_repair.schemas import RepairInput


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--attempt", default="development01")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.input is not None:
        if args.output is None or args.output.exists():
            parser.error("Provide a new output path for the edited bundle")
        bundle = RepairInput.model_validate_json(args.input.read_text())
        result = edit(bundle)
        args.output.write_text(result.model_dump_json(indent=2) + "\n")
        print(result.text)
    else:
        if args.root is None:
            parser.error("Provide --root or --input/--output")
        if (args.root / "completion_manifest.json").exists():
            raise SystemExit("Evidence sealed")
        run(args.root, args.attempt)


if __name__ == "__main__":
    main()
