"""Descriptive fixed-seed sensitivity from already sealed GRU predictions."""

import argparse
from pathlib import Path

import numpy as np

from dual_rec.failtime.analysis import aggregate
from dual_rec.failtime.experiment import (
    ALPHAS,
    PERSISTENCES,
    STRESSES,
    read,
    save,
    verify_seal,
)
from dual_rec.failtime.metrics import calibrate, outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    verify_seal(root)
    registration = read(root, "registration.json")
    registry = {r["sample"]: r for r in read(root, "cohort_qualification.json")}
    thresholds = []
    outcomes = []
    summary = []
    for seed in (11, 23, 37):
        method = f"B4_seed{seed}"
        success = []
        prefix = []
        for sample in registration["splits"]["calibration"]:
            row = registry[sample]
            with np.load(root / "risks/calibration/clean" / (sample + ".npz")) as d:
                mask = (
                    np.ones(len(d["time"]), bool)
                    if row["verdict"] == "success"
                    else d["time"] < row["onset"]
                )
                record = {
                    "sample": sample,
                    "time": d["time"][mask],
                    "scores": d[method][mask],
                }
            (success if row["verdict"] == "success" else prefix).append(record)
        for alpha in ALPHAS:
            fitted = calibrate(success, prefix, alpha)
            thresholds.append({"method": method, **fitted})
            for stress in STRESSES:
                for persistence in PERSISTENCES:
                    population = []
                    for sample in registration["splits"]["evaluation"]:
                        row = registry[sample]
                        with np.load(
                            root / "risks/evaluation" / stress / (sample + ".npz")
                        ) as data:
                            result = outcome(
                                row,
                                data["time"],
                                data[method],
                                fitted["threshold"],
                                persistence,
                            )
                        result.update(
                            method=method,
                            alpha=alpha,
                            stress=stress,
                            split="evaluation",
                        )
                        population.append(result)
                        outcomes.append(result)
                    summary.append(
                        {
                            "method": method,
                            "alpha": alpha,
                            "stress": stress,
                            "persistence": persistence,
                            "split": "evaluation",
                            **aggregate(population),
                        }
                    )
    save(
        root / "seed_sensitivity.json",
        {
            "scope": "Descriptive fixed seeds; ensemble remains primary; no seed selected",
            "thresholds": thresholds,
            "summary": summary,
        },
    )
    save(root / "seed_outcomes.json", outcomes)
    verify_seal(root)
    print(
        {
            "seed_calibrations": len(thresholds),
            "cells": len(summary),
            "outcomes": len(outcomes),
        }
    )


if __name__ == "__main__":
    main()
