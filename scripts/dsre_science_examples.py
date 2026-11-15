"""Constructive false-assertion examples from fixed bounded sensor corruptions."""

import argparse
import gzip
import json
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_science_offline import corrupt

from dual_rec.dsre.features import PRIMARY, ObservationHistory, feature_values
from dual_rec.dsre.measurement import (
    MeasurementScope,
    RobustRouter,
    bounded_evidence,
    explain,
)
from dual_rec.dsre.operational import OperationalRouter, PolicyInput
from dual_rec.dsre.repair_selection import OPTIONAL, optional_values


def examples(root):
    with gzip.open(root / "offline_rows.jsonl.gz", "rt") as f:
        rows = [json.loads(s) for s in f]
    frozen = read(root / "frozen_routers.json")
    point = OperationalRouter(frozen)
    robust = RobustRouter(frozen)
    output = []
    for row in sorted(rows, key=lambda r: r["id"]):
        h = ObservationHistory.model_validate(row["runtime_history"])
        truth = feature_values(h) + optional_values(h)
        observed = corrupt(h, 0.005, row["id"], 0)
        measured = feature_values(observed) + optional_values(observed)
        p = PolicyInput(
            task=row["task"],
            values=measured[:7] if row["task"] == "PickCube-v1" else measured[:6],
            full_values=measured,
        )
        decision = point.route(p)["DSRE_strict"]
        actual = dict(zip(PRIMARY + OPTIONAL, truth, strict=True))
        wrong = [f for f in decision["evidence"] if actual[f["feature"]] != f["value"]]
        if not wrong:
            continue
        deltas = []
        for a, b in ((h.first, observed.first), (h.current, observed.current)):
            for name in ("object_position", "tcp_position", "goal_position"):
                left, right = getattr(a, name), getattr(b, name)
                if left is not None:
                    deltas += [abs(x - y) for x, y in zip(left, right, strict=True)]
        assert max(deltas) <= 0.005 + 1e-15
        e = bounded_evidence(
            observed,
            MeasurementScope(
                coordinate_error_m=0.005,
                decision_time=h.current.time,
                reference_scope_identity=sha(root / "frozen_routers.json"),
                source_regime=row["population"],
            ),
        )
        unstable = {f.feature for f in e.facts if f.invariant is None}
        assert all(f["feature"] in unstable for f in wrong)
        output.append(
            {
                "selection": "First lexicographic source rows with a false strict point-certificate assertion in registered5mm uniform replicate0; illustration only, not an added statistical population",
                "id": row["id"],
                "source": row["source"],
                "source_sha256": row["source_sha256"],
                "actual_history": h.model_dump(mode="json"),
                "corrupted_observed_history": observed.model_dump(mode="json"),
                "maximum_coordinate_error_m": max(deltas),
                "actual_paired_outcomes_unchanged": row["outcomes"],
                "point_certificate": decision,
                "false_asserted_literals": wrong,
                "true_values": {f["feature"]: actual[f["feature"]] for f in wrong},
                "robust_output": explain(e, robust, row["task"]),
                "interpretation": "Actual sensor corruption is inside the declared box; source physical futures are unchanged. Conservative UNKNOWN enclosures elsewhere are not automatically constructive truth-flip witnesses.",
            }
        )
        if len(output) == 4:
            break
    assert output, (
        "Expected actual false-assertion evidence from fixed corruption ledger"
    )
    atomic(
        root / "constructive_measurement_examples.json",
        {
            "examples": output,
            "joint_coordinate_bounds_checked": True,
            "new_physics": 0,
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {"constructive_examples": len(output), "ids": [e["id"] for e in output]}
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    examples(a.root)
