"""Discovery-frozen conventional baselines and unchanged certificate inference."""

import argparse
import json
from pathlib import Path

import numpy as np
from dsre_last_common import ROOT, read, save, sha

from dual_rec.dsre.features import PRIMARY
from dual_rec.evidence_aware.baselines import proposals
from dual_rec.evidence_aware.bounds import calibrate, qualifies, solve
from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.partition import assignments, fit, route
from dual_rec.evidence_aware.schema import Bounds, OneAction, Partition, Scope, Source
from dual_rec.evidence_aware.views import guard_data_access


def regression_partition(logs):
    """Fixed ridge per-arm regression, two whole prediction regions; D only."""
    predictions = []
    coefficients = []
    grid = np.c_[np.ones(64), np.asarray(assignments(6), float)]
    for action in ("c", "r"):
        rows = [r for r in logs if r.action == action]
        x = np.asarray([[1.0, *r.x] for r in rows], float)
        y = np.asarray([r.y for r in rows], float)
        penalty = np.diag([0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        beta = np.linalg.solve(x.T @ x + penalty, x.T @ y)
        coefficients.append(beta.tolist())
        predictions.append(np.clip(grid @ beta, 0, 1))
    cells = tuple(int(v >= 0.05) for v in predictions[1] - predictions[0])
    ids = {c: i for i, c in enumerate(sorted(set(cells)))}
    cells = tuple(ids[c] for c in cells)
    p = Partition(
        vocabulary=PRIMARY,
        cells=cells,
        tree=(-1, -1, -1),
        discovery_parents=tuple(sorted(r.parent_id for r in logs)),
    )
    counts = {
        (c, a): sum(route(p, r.x) == c and r.action == a for r in logs)
        for c in set(cells)
        for a in ("c", "r")
    }
    if any(n < 8 for n in counts.values()):
        p = p.model_copy(update={"cells": (0,) * 64})
        decision = float(np.mean(predictions[1] - predictions[0])) >= 0.05
        proposed = {0: decision}
    else:
        proposed = {
            c: bool(
                next(
                    predictions[1][i] - predictions[0][i] >= 0.05
                    for i, leaf in enumerate(cells)
                    if leaf == c
                )
            )
            for c in set(cells)
        }
    return p, coefficients, proposed


def select(model, x):
    p = Partition.model_validate(model["partition"])
    bs = {
        int(c): Bounds.model_validate(v["bounds"])
        for c, v in model["leaves"].items()
        if v["bounds"]
    }
    leaf = route(p, x)
    passed = leaf in bs and qualifies(bs[leaf])
    utility = model["proposals"].get(str(leaf), {}).get("utility", False)
    actions = {
        "DSRE": "r" if passed else "c",
        "exact_B7": "r" if passed else "c",
        "direct_partial_ID": "r" if passed else "c",
        "CART_same_gate": "r" if passed and utility else "c",
        "always_continue": "c",
        "always_recover": "r",
    }
    rp = Partition.model_validate(model["regression"]["partition"])
    rc = route(rp, x)
    rb = model["regression"]["leaves"].get(str(rc), {}).get("bounds")
    actions["outcome_regression_same_gate"] = (
        "r"
        if rb
        and qualifies(Bounds.model_validate(rb))
        and model["regression"]["proposed"].get(str(rc), False)
        else "c"
    )
    cert = minimum(
        p,
        x,
        bs,
        Source.LOGGED,
        outcome_scope=Scope.model_validate(model["source_scope"]),
    )
    assert (cert is not None) == passed
    return {
        "actions": actions,
        "certificate": cert.model_dump(mode="json") if cert else None,
        "leaf": leaf,
    }


def calibrate_partition(p, logs):
    leaves = {}
    for c in sorted(set(p.cells)):
        rows = [r for r in logs if route(p, r.x) == c]
        evidence, ledger = calibrate(rows, [], f"frozen_leaf:{c}", len(set(p.cells)))
        try:
            bounds = solve(evidence).model_dump(mode="json")
        except ValueError:
            bounds = None
        leaves[c] = {
            "evidence": evidence.model_dump(mode="json"),
            "ledger": ledger,
            "bounds": bounds,
        }
    return leaves


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("discovery", "calibration"))
    args = parser.parse_args()
    dpath = ROOT / "learner/discovery.json"
    cpath = ROOT / "learner/calibration.json"
    freeze = ROOT / "discovery_freeze.json"
    allowed = [dpath] if args.stage == "discovery" else [dpath, cpath, freeze]
    reads = guard_data_access(Path("results"), allowed)
    discovery = [OneAction.model_validate(r) for r in read(dpath)]
    if args.stage == "discovery":
        p = fit(discovery, PRIMARY)
        rp, coefficients, prop = regression_partition(discovery)
        result = {
            "partition": p.model_dump(mode="json"),
            "proposals": proposals(p, discovery),
            "regression": {
                "partition": rp.model_dump(mode="json"),
                "coefficients": coefficients,
                "proposed": prop,
            },
            "source_scope": discovery[0].source_scope.model_dump(mode="json"),
        }
        destination = freeze
    else:
        result = read(freeze)
        calibration = [OneAction.model_validate(r) for r in read(cpath)]
        assert not {r.parent_id for r in discovery} & {r.parent_id for r in calibration}
        p = Partition.model_validate(result["partition"])
        rp = Partition.model_validate(result["regression"]["partition"])
        result["leaves"] = calibrate_partition(p, calibration)
        result["regression"]["leaves"] = calibrate_partition(rp, calibration)
        destination = ROOT / "model_frozen.json"
    result.update(
        input_sha256={str(p): sha(p) for p in allowed},
        successful_reads=list(reads),
        family="Individual per-method frozen-cell guarantee; no across-method/task joint95 claim",
    )
    save(destination, result)
    print(
        json.dumps(
            {
                "stage": args.stage,
                "partition": result["partition"]["tree"],
                "cells": len(set(result["partition"]["cells"])),
            }
        )
    )


if __name__ == "__main__":
    main()
