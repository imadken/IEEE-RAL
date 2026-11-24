"""Independent pose-derived feature audit of the separately frozen G1 pilot."""

import gzip
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def main():
    r = Path("results/dsre-evidence-aware/20261117-prospective")
    folder = r / "physics/PegInsertionSide-v1/source-v2-qualification"
    classes = Counter()
    features = 0
    for i in range(10):
        branches = []
        for action in ("c", "r"):
            with gzip.open(folder / str(i) / (action + ".json.gz"), "rt") as f:
                b = json.load(f)
            length = b["geometry"]["peg_half_sizes"][0][0]

            def geometry(packet, length=length):
                p = np.asarray(packet["peg"][0])
                h = np.asarray(packet["hole"][0])
                rot = lambda q: Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
                relative = rot(h[3:]).T @ rot(p[3:])
                position = rot(h[3:]).T @ (p[:3] - h[:3])
                return position + relative[:, 0] * length, math.acos(
                    np.clip(relative[0, 0], -1, 1)
                )

            tip, angle = geometry(b["checkpoint"])
            previous, _ = geometry(b["prefix"][-6])
            expected = [
                np.linalg.norm(tip[1:]) <= 0.003,
                angle <= np.deg2rad(5),
                tip[0] - previous[0] >= 0.001,
                np.linalg.norm(tip - np.array([-length, 0, 0])) <= 0.02,
            ]
            assert expected == b["features"][:4], (i, action, expected, b["features"])
            assert b["feature_telemetry"][4] is None and len(b["features"]) == 5
            features += 4
            branches.append(b["success"])
        classes["".join(str(int(v)) for v in branches)] += 1
    result = {
        "passed": True,
        "fresh_parents": 10,
        "source_action_endpoints": 20,
        "source_endpoint_pairs": 10,
        "independently_recomputed_predecision_predicates": features,
        "four_cells": dict(classes),
        "unknown_aperture_telemetry_preserved": True,
        "fifth_TCP_tracking_predicate": "Source equation audited; no independent target-pose telemetry channel was added or claimed.",
    }
    with (r / "G1_independent_feature_audit_v2.json").open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
