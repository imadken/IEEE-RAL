"""Score sealed models only after their independent test executions."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_evidence_development import persist
from dsre_evidence_prospective import ROOT, TASKS, read

from dual_rec.evidence_aware.baselines import decisions
from dual_rec.evidence_aware.bounds import cp
from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.partition import route
from dual_rec.evidence_aware.schema import Bounds, Partition, Scope, Source
from dual_rec.evidence_aware.views import sha


def evaluate(root, task, *, frozen_path=None):
    out = root / "prospective" / task
    if not (out / "all_models_frozen.json").exists():
        return
    frozen = read(frozen_path or out / "all_models_frozen.json")
    test = [read(p) for p in sorted((out / "test").glob("*.json"))]
    pairs = {
        r["parent_id"]: r for r in [read(p) for p in (out / "evaluator").glob("*.json")]
    }
    known = [
        r
        for r in test
        if r["parent_id"] in pairs
        and pairs[r["parent_id"]]["yc"] is not None
        and pairs[r["parent_id"]]["yr"] is not None
    ]
    n = len(known)
    rng = np.random.default_rng(2026111702)
    draws = rng.integers(0, n, (2000, n)) if n else None
    for name, checksum in frozen["models"].items():
        path = out / "models" / f"{name}.json"
        assert sha(path) == checksum
        model = read(path)
        partition = Partition.model_validate(model["partition"])
        bounds = {
            int(c): Bounds.model_validate(v["bounds"])
            for c, v in model["leaves"].items()
        }
        prop = {int(c): v for c, v in model["proposals"].items()}
        rows = []
        for record in known:
            pid = record["parent_id"]
            leaf = route(partition, record["x"])
            evidence = model["leaves"].get(str(leaf), {}).get("evidence")
            independence_pass = bool(
                evidence
                and evidence["overlap"]
                and evidence["p0"]["hi"] * (1 - evidence["p1"]["lo"]) <= 0.1
                and evidence["p1"]["lo"] - evidence["p0"]["hi"] >= 0.05
            )
            actions = decisions(
                leaf, bounds, prop, bool(model["pair_parent_ids"]), independence_pass
            )
            if record.get("precheckpoint_absorption"):
                actions = {method: "c" for method in actions}
            cert = minimum(
                partition,
                record["x"],
                bounds,
                Source(model["source_type"]),
                outcome_scope=Scope.model_validate(model["source_scope"]),
            )
            if cert and all(
                model["leaves"][str(c)]["evidence"]["source_type"]
                == Source.LOGGED.value
                for c in cert.selected_leaf_scope
            ):
                cert = cert.model_copy(update={"source_type": Source.LOGGED})
            assert (cert is not None) == (actions["DSRE"] == "r")
            rows.append(
                {
                    "parent_id": pid,
                    "leaf": leaf,
                    "actions": actions,
                    "certificate": cert.model_dump(mode="json") if cert else None,
                }
            )
        metrics = {}
        for method in next(iter(rows), {}).get("actions", {}):
            vectors = []
            literals = []
            for row in rows:
                pair = pairs[row["parent_id"]]
                recover = row["actions"][method] == "r"
                c, r = int(pair["yc"]), int(pair["yr"])
                y = r if recover else c
                vectors.append(
                    [
                        recover,
                        y,
                        y - c,
                        recover * c * (1 - r),
                        recover * (1 - c) * r,
                        recover * (1 - c) * (1 - r),
                    ]
                )
                if method == "DSRE" and row["certificate"]:
                    literals.append(len(row["certificate"]["evidence"]))
            a = np.asarray(vectors, dtype=int)
            totals = a.sum(axis=0)
            metrics[method] = {
                "n": n,
                "qualification_label": "unsupported independence negative control"
                if method == "naive_independence"
                else "unqualified descriptive comparator"
                if method in ("empirical_utility", "always_continue", "always_recover")
                else "matched useful-recovery gate",
                "recover": int(totals[0]),
                "success": int(totals[1]),
                "gain_total": int(totals[2]),
                "whole_policy_gain": float(totals[2] / n),
                "harm": int(totals[3]),
                "required_rescues": int(totals[4]),
                "futile": int(totals[5]),
                "redundant_recoveries": int(
                    totals[0] - totals[3] - totals[4] - totals[5]
                ),
                "rescue_opportunities": sum(
                    not p["yc"] and p["yr"]
                    for p in pairs.values()
                    if p["yc"] is not None and p["yr"] is not None
                ),
                "gain_parent_bootstrap95": np.quantile(
                    a[:, 2][draws].mean(axis=1), [0.025, 0.975]
                ).tolist(),
                "harm_per_recover_CP95": cp(
                    int(totals[3]), int(totals[0]), 0.025
                ).model_dump(),
                "coverage": float(totals[0] / n),
                "deferral_secondary": n - int(totals[0]),
                "literal_mean": float(np.mean(literals)) if literals else None,
                "completion_all256_sensitivity": [
                    int(totals[1]) / 256,
                    (int(totals[1]) + 256 - n) / 256,
                ],
            }
        classes = Counter(
            f"{int(pairs[r['parent_id']]['yc'])}{int(pairs[r['parent_id']]['yr'])}"
            for r in known
        )
        result = {
            "task": task,
            "model": name,
            "frozen_model_sha256": checksum,
            "n_registered_test": 256,
            "n_selected_executions": sum(r.get("y") is not None for r in test),
            "n_complete_oracle_pairs": n,
            "n_recovery_checkpoint_pairs": sum(
                not r.get("precheckpoint_absorption") for r in known
            ),
            "n_observed_absorbing_prefix_parents": sum(
                bool(r.get("precheckpoint_absorption")) for r in known
            ),
            "missing_or_unexecuted": 256 - n,
            "four_cells": dict(classes),
            "policies": metrics,
            "decisions": rows,
            "equivalence_vs_DSRE": {
                method: sum(r["actions"][method] == r["actions"]["DSRE"] for r in rows)
                for method in next(iter(rows), {}).get("actions", {})
            },
            "logical_calibration_cost": model["logical_calibration_executions"],
            "confidence": "fixed calibration family; test bootstrap intervals descriptive; no simultaneous best-budget significance claim",
        }
        persist(out / "evaluations" / f"{name}.json", result)
    print(
        json.dumps(
            {"evaluated": task, "test_pairs": n, "models": len(frozen["models"])}
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--task", choices=TASKS, required=True)
    a = p.parse_args()
    evaluate(a.root, a.task)
