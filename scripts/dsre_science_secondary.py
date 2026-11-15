"""Pre-outcome seal for registered historical2cm coarsening and actual delay stress."""

import argparse
import gzip
import json
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_recovery_audit import gz

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.measurement import MeasurementScope, RobustRouter, bounded_evidence
from dual_rec.dsre.operational import OperationalRouter, PolicyInput
from dual_rec.dsre.repair_selection import optional_values


def coarsen(h):
    frames = []
    for frame in (h.first, h.current):
        if frame is None:
            frames.append(None)
            continue
        update = {}
        for name in ("object_position", "tcp_position", "goal_position"):
            xyz = getattr(frame, name)
            update[name] = (
                None if xyz is None else tuple(round(v / 0.02) * 0.02 for v in xyz)
            )
        frames.append(frame.model_copy(update=update))
    return h.model_copy(update={"first": frames[0], "current": frames[1]})


def seal(root):
    if (root / "secondary_recommendation_seal.json").exists():
        raise ValueError("Already sealed")
    assert (root / "prospective_recommendation_seal.json").exists()
    assert not list((root / "prospective").glob("*/execution_started.json"))
    frozen = read(root / "frozen_routers.json")
    point = OperationalRouter(frozen)
    robust = RobustRouter(frozen)
    records = []
    unavailable = []
    for path in sorted((root / "prospective").glob("*/*/screen.json.gz")):
        raw = gz(path)
        h = ObservationHistory.model_validate(raw["summary"]["runtime_history"])
        ch = coarsen(h)
        values = feature_values(ch) + optional_values(ch)
        assert values[:6] == feature_values(h, coarse=True)
        p = PolicyInput(task="PickCube-v1", values=values[:7], full_values=values)
        scenarios = {
            "coarse02_point": {
                "outputs": point.route(p),
                "measured_values": values,
                "risk": "UNQUALIFIED_COARSENED_INTERFACE; no interval guarantee inferred for quantization",
            }
        }
        if (
            len(raw["prefix"]) >= 6
            and abs(h.current.time - raw["prefix"][-6]["time"] - 0.25) < 1e-8
        ):
            old = raw["prefix"][-6]
            dh = h.model_copy(
                update={"current": observed_frame(old["time"], old["observation"])}
            )
            e = bounded_evidence(
                dh,
                MeasurementScope(
                    coordinate_error_m=0,
                    decision_time=h.current.time,
                    reference_scope_identity=sha(root / "frozen_routers.json"),
                    source_regime="OOD_V12_ACTUAL_DELAY_250MS",
                ),
            )
            measured = tuple(f.measured for f in e.facts)
            dp = PolicyInput(
                task="PickCube-v1", values=measured[:7], full_values=measured
            )
            scenarios["delay5_equal_250ms"] = {
                "point": point.route(dp),
                "robust": robust.route(e.packet("PickCube-v1")),
                "measurement": e.model_dump(mode="json"),
                "risk": "UNQUALIFIED_DELAY; no motion envelope",
            }
        else:
            unavailable.append(raw["cell"])
        records.append(
            {
                "cell": raw["cell"],
                "source": str(path),
                "source_sha256": sha(path),
                "scenarios": scenarios,
            }
        )
    with gzip.open(root / "secondary_recommendations.jsonl.gz", "wt") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    atomic(
        root / "secondary_recommendation_seal.json",
        {
            "sha256": sha(root / "secondary_recommendations.jsonl.gz"),
            "cells": len(records),
            "registered_source_sha256": sha(Path(__file__)),
            "epoch": time.time(),
            "primary_outcome_starts": 0,
            "delay_unavailable": unavailable,
            "coarsening": "Existing2cm coordinate quantization; secondary, not a new primary method/feature/threshold",
            "five_steps_equals_250ms": True,
        },
    )
    print(
        json.dumps(
            {
                "secondary_cells_sealed": len(records),
                "delay_unavailable": len(unavailable),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    seal(a.root)
