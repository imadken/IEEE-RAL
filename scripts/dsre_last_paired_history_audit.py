"""Recheck historical paired Pick/Push trajectories without executing physics."""

import gzip
import json
from collections import Counter
from pathlib import Path

from dsre_evidence_prospective_audit import check_grasp
from dsre_last_common import ROOT, save, sha
from dsre_last_physical import push
from dsre_source_risk_audit import predicates, state_equal, vec


def main():
    catalog = Path("results/dsre-rss2027/20261113T193554Z/fresh_qualified.jsonl")
    counts = Counter()
    sources = {}
    for line in catalog.read_text().splitlines():
        row = json.loads(line)
        path = Path(row["source"])
        assert sha(path) == row["source_sha256"]
        sources[str(path)] = sha(path)
        with gzip.open(path, "rt") as f:
            raw = json.load(f)
        assert raw["cell"] == {k: row[k] for k in ("task", "seed", "condition")}
        for action, name in [("c", "continue"), ("r", "recover")]:
            t = raw["traces"][name]
            assert t["controller_memory"] == raw["canonical_controller_memory"]
            assert t["model_edit"] == raw["model"]["edit"]
            for a, b in zip(raw["prefix"], t["prefix_history"], strict=True):
                state_equal(a, b)
                counts["prefix_states"] += 1
            state_equal(raw["canonical_start"], t["start"])
            b = {
                "spec": {"condition": row["condition"]},
                "status": "COMPLETE",
                "features": row["features"],
                "prefix": raw["prefix"],
                "prefix_controls": raw["prefix_actions"],
                "checkpoint": t["start"],
                "post": [f["state"] for f in t["frames"]],
                "post_controls": [f["action"] for f in t["frames"]],
                "action": action,
                "executed_action": action,
                "initial_tcp": t["initial_tcp"],
                "success": raw["outcomes"][name + "_value"],
            }
            primary, optional = predicates(
                raw["prefix"][0]["observation"], t["start"]["observation"]
            )
            assert primary == row["features"] and optional == row["optional_features"]
            assert b["success"] == row["outcomes"][name + "_value"]
            if row["task"] == "PushCube-v1":
                cube = vec(raw["prefix"][0]["observation"], "obj_pose").copy()
                goal = vec(raw["prefix"][0]["observation"], "goal_pos").copy()
                if row["condition"] == "misaligned":
                    cube[1] += 0.07
                    goal[1] += 0.07
                b.update(cached_initial=cube.tolist(), cached_goal=goal.tolist())
                push(b)
            else:
                check_grasp(b)
            counts[row["task"] + "_outcome_actions"] += 1
            counts["future_controls"] += len(t["frames"])
        counts["paired_checkpoints"] += 1
    save(
        ROOT / "independent_historical_paired_audit.json",
        {
            "passed": True,
            "counts": dict(counts),
            "source_sha256": sources,
            "source_scope": "Historical inspected development data, original task/condition and parent roles retained",
            "physics_executed": False,
        },
    )
    print(json.dumps({"passed": True, "counts": dict(counts)}))


if __name__ == "__main__":
    main()
