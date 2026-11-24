"""Fixed conventional regression on inspected Pick history; never a new test."""

import argparse
from pathlib import Path

from dsre_last_common import ROOT, read, save, sha
from dsre_last_model import calibrate_partition, regression_partition

from dual_rec.evidence_aware.bounds import qualifies
from dual_rec.evidence_aware.partition import route
from dual_rec.evidence_aware.schema import Bounds, OneAction, Partition
from dual_rec.evidence_aware.views import guard_data_access


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("discovery", "calibration", "evaluate"))
    args = parser.parse_args()
    d = ROOT / "legacy_regression/learner/discovery.json"
    c = ROOT / "legacy_regression/learner/calibration.json"
    frozen = ROOT / "legacy_regression/discovery_freeze.json"
    modelpath = ROOT / "legacy_regression/model_frozen.json"
    if args.stage == "discovery":
        accessed = guard_data_access(Path("results"), [d])
        rows = [OneAction.model_validate(r) for r in read(d)]
        p, beta, proposed = regression_partition(rows)
        save(
            frozen,
            {
                "partition": p.model_dump(mode="json"),
                "coefficients": beta,
                "proposed": proposed,
                "input_sha256": {str(d): sha(d)},
                "successful_reads": list(accessed),
                "role": "Inspected historical Pick development reanalysis, no new held-out status",
                "algorithm_sha256": sha("scripts/dsre_last_model.py"),
            },
        )
    elif args.stage == "calibration":
        accessed = guard_data_access(Path("results"), [c, frozen])
        frozenmodel = read(frozen)
        rows = [OneAction.model_validate(r) for r in read(c)]
        assert not set(frozenmodel["partition"]["discovery_parents"]) & {
            r.parent_id for r in rows
        }
        p = Partition.model_validate(frozenmodel["partition"])
        frozenmodel.update(
            leaves=calibrate_partition(p, rows),
            calibration_sha256=sha(c),
            discovery_freeze_sha256=sha(frozen),
            successful_calibration_reads=list(accessed),
        )
        save(modelpath, frozenmodel)
    else:
        # Evaluator is isolated from training/calibration; these outcomes were
        # historically inspected and are explicitly retrospective in this analysis.
        model = read(modelpath)
        p = Partition.model_validate(model["partition"])
        base = Path(
            "results/dsre-evidence-aware/20261117-prospective/prospective/PickCube-v1"
        )
        rows = []
        for path in sorted((base / "test").glob("*.json")):
            query = read(path)
            pair = read(base / "evaluator" / path.name)
            leaf = route(p, query["x"])
            entry = model["leaves"][str(leaf)]
            use = bool(
                entry["bounds"]
                and qualifies(Bounds.model_validate(entry["bounds"]))
                and model["proposed"][str(leaf)]
            )
            rows.append(
                {
                    "parent_id": query["parent_id"],
                    "x": query["x"],
                    "yc": pair["yc"],
                    "yr": pair["yr"],
                    "decision": {
                        "actions": {
                            "outcome_regression_same_gate": "r" if use else "c"
                        },
                        "certificate": None,
                    },
                }
            )
        from dsre_last_audit import metrics

        save(
            ROOT / "legacy_regression/evaluation.json",
            {
                "role": model["role"],
                "model_sha256": sha(modelpath),
                "policies": metrics(rows),
                "rows": rows,
                "budgets": {
                    "discovery": 128,
                    "calibration": 1024,
                    "test_selected_policy": 256,
                    "common_offline_evaluator_extra_actions": 256,
                },
                "limitation": "Algorithm fixed in final registration before new outcomes; this Pick comparison uses already inspected historical T and is a retrospective comparison, not independent prospective confirmation of a new regression baseline.",
            },
        )


if __name__ == "__main__":
    main()
