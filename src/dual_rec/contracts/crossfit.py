"""Fixed grouped cross-fitting of the existing FailTime implementations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from dual_rec.failtime import experiment

OLD = Path("results/failtime-online/20261112T101800Z")


def prepare(root):
    registration = experiment.read(root, "registration.json")
    old_config = experiment.read(OLD, "registration.json")
    cohort = experiment.read(OLD, "cohort_qualification.json")
    for fold in range(5):
        directory = root / "failtime" / f"fold{fold}"
        directory.mkdir(parents=True, exist_ok=True)
        for name in ("arrays", "upstream"):
            target = directory / name
            if not target.exists():
                target.symlink_to((OLD / name).resolve(), target_is_directory=True)
        for name in ("cohort_qualification.json", "data_gate.json"):
            target = directory / name
            if not target.exists():
                target.write_bytes((OLD / name).read_bytes())
        partitions = {"train": [], "calibration": [], "evaluation": []}
        for row in cohort:
            group = row["robot"] + "/" + row["task_id"]
            k = registration["failtime"]["group_folds"][group]
            partition = (
                "evaluation"
                if k == fold
                else "calibration"
                if k == (fold + 1) % 5
                else "train"
            )
            partitions[partition].append(row["sample"])
        config = {
            **old_config,
            "scope": "Exploratory task-grouped cross-fitting of all previously exposed Long records; no untouched confirmation",
            "splits": partitions,
            "crossfit_fold": fold,
            "parent_registration_sha256": experiment.digest(root / "registration.json"),
            "group_folds": registration["failtime"]["group_folds"],
        }
        path = directory / "registration.json"
        if path.exists():
            assert json.loads(path.read_text()) == config
        else:
            experiment.save(path, config)
    experiment.save(
        root / "crossfit_partitions.json",
        [
            {
                "fold": k,
                "splits": experiment.read(
                    root / "failtime" / f"fold{k}", "registration.json"
                )["splits"],
            }
            for k in range(5)
        ],
    )


def run(root, stage, fold):
    directory = root / "failtime" / f"fold{fold}"
    if stage == "train":
        experiment.train(directory)
    elif stage == "calibrate":
        experiment.calibrate(directory)
    elif stage == "evaluate":
        experiment.evaluate(directory)
    with (root / "crossfit_progress.jsonl").open("a") as stream:
        stream.write(
            json.dumps(
                {
                    "fold": fold,
                    "stage": stage,
                    "registration_sha256": hashlib.sha256(
                        (directory / "registration.json").read_bytes()
                    ).hexdigest(),
                }
            )
            + "\n"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("prepare", "train", "calibrate", "evaluate"), required=True
    )
    parser.add_argument("--fold", type=int, choices=range(5))
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.stage == "prepare":
        prepare(args.root)
    else:
        import torch

        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        if args.fold is None:
            for fold in range(5):
                run(args.root, args.stage, fold)
        else:
            run(args.root, args.stage, args.fold)


if __name__ == "__main__":
    main()
