"""Source-qualified complete pose signatures, independent of outcome routing."""

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

from dsre_followup_batch import atomic, sha
from dsre_recovery_audit import gz

from dual_rec.dsre.features import ObservationHistory, observed_frame


def vector(value):
    while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
        value = value[0]
    return tuple(float(v) for v in value)


def full_pose(frame):
    extra = frame["observation"]["extra"]
    obj, tcp, goal = (vector(extra[k]) for k in ("obj_pose", "tcp_pose", "goal_pos"))
    assert len(obj) == 7 and len(tcp) == 7 and len(goal) == 3
    fingers = vector(frame["observation"]["agent"]["qpos"])[-2:]
    return obj + tcp + goal + fingers


def audit(root, prospective=False):
    source = root / (
        "prospective_rows.jsonl.gz" if prospective else "offline_rows.jsonl.gz"
    )
    with gzip.open(source, "rt") as f:
        rows = [json.loads(s) for s in f]
    profiles = defaultdict(list)
    checks = 0
    for row in rows:
        path = Path(row["source"])
        assert sha(path) == row["source_sha256"]
        raw = gz(path)
        prefix = raw["prefix"]
        first = prefix[0]
        current = raw.get("canonical_start", prefix[-1])
        history = ObservationHistory.model_validate(row["runtime_history"])
        assert observed_frame(first["time"], first["observation"]) == history.first
        assert (
            observed_frame(current["time"], current["observation"]) == history.current
        )
        signature = full_pose(first) + full_pose(current)
        profiles[row["population"] + "|" + row["task"]].append((row, signature))
        checks += 2
    results = {}
    for key, items in profiles.items():
        groups = defaultdict(list)
        for row, signature in items:
            groups[signature].append(row)
        mass = sum(
            len(g)
            for g in groups.values()
            if all(r["outcomes"]["continue_value"] for r in g)
            or all(r["outcomes"]["recover_value"] for r in g)
        )
        action = sum(any(r["outcomes"].values()) for r, _ in items)
        results[key] = {
            "rows": len(items),
            "parents": len({r["group"] for r, _ in items}),
            "complete_pose_signature_classes": len(groups),
            "singleton_classes": sum(len(g) == 1 for g in groups.values()),
            "observation_mass": mass,
            "action_mass": action,
            "variables": "Both source frames: full object xyz+quaternion7, TCP xyz+quaternion7, goal xyz3, fingers2; no future/fault label",
            "scope": "Hindsight unattainable-information diagnostic; continuous singleton signatures overfit. No minimum support or deployment guarantee.",
        }
        assert mass <= action
    out = {
        "passed": True,
        "raw_source_frames_verified": checks,
        "profiles": results,
        "epoch": time.time(),
    }
    atomic(
        root
        / (
            "prospective_full_pose_audit.json"
            if prospective
            else "full_pose_audit.json"
        ),
        out,
    )
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--prospective", action="store_true")
    a = p.parse_args()
    audit(a.root, a.prospective)
