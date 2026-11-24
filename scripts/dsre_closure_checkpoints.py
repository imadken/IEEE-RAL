"""Independent predecision source/trigger and physical-parent identity audit."""

import hashlib
import itertools
import json

import numpy as np
from dsre_closure_common import INPUTS, ROOT, TASKS, paths, read, save
from dsre_source_risk_audit import predicates, vec


def discovery_check(task, p):
    directory = p["base"] / "learner_records/discovery"
    logs = (
        [read(f) for f in sorted(directory.glob("*.json"))]
        if directory.is_dir()
        else read(p["base"] / "learner/discovery.json")
    )
    assert len(logs) == len({r["parent_id"] for r in logs}) == 128
    frozen = read(p["discovery"])
    partition = frozen["partition"]
    assert sorted(r["parent_id"] for r in logs) == partition["discovery_parents"]
    d = len(partition["vocabulary"])
    cube = list(itertools.product((False, True), repeat=d))
    trees = [(-1, -1, -1)]
    for root in range(d):
        children = [-1] + [i for i in range(d) if i != root]
        trees.extend(
            (root, left, right) for left, right in itertools.product(children, repeat=2)
        )
    ranked = []
    for tree in trees:

        def terminal(x, tree=tree):
            if tree[0] < 0:
                return 0
            side = int(x[tree[0]])
            child = tree[1 + side]
            return side * 2 + (int(x[child]) if child >= 0 else 0)

        raw = [terminal(x) for x in cube]
        groups = {(leaf, action): [] for leaf in set(raw) for action in ("c", "r")}
        for row in logs:
            assert row["propensity"] == 0.5 and row["counterpart_exposed"] is False
            groups[terminal(row["x"]), row["action"]].append(int(row["y"]))
        if tree[0] >= 0 and any(len(v) < 8 for v in groups.values()):
            continue
        sse = sum(sum(v) - sum(v) ** 2 / len(v) for v in groups.values() if v)
        ids = {leaf: i for i, leaf in enumerate(sorted(set(raw)))}
        ranked.append(((round(sse, 12), len(ids), tree), [ids[c] for c in raw]))
    score, cells = min(ranked, key=lambda r: r[0])
    assert list(score[2]) == partition["tree"] and cells == partition["cells"]
    return {
        "passed": True,
        "parents": len(logs),
        "candidate_trees": len(trees),
        "eligible_trees": len(ranked),
        "winning_score": score,
        "cells": cells,
        "method": "Independent exhaustive discovery-only SSE, per-arm n>=8, exact declared ties; no calibration/test-driven selection",
    }


def grasp_stop(raw):
    prefix = raw["prefix"]
    z0 = vec(prefix[0]["observation"], "obj_pose")[2]
    peak = z0
    stop = 90
    reason = "PREFIX_CAP"
    for j, state in enumerate(prefix):
        obs = state["observation"]
        z = vec(obs, "obj_pose")[2]
        peak = max(peak, z)
        if j < 70 or state["success"]:
            continue

        def ungrasped(frame):
            return not bool(
                np.asarray(frame["observation"]["extra"]["is_grasped"]).reshape(-1)[0]
            )

        missed = all(
            ungrasped(s)
            and vec(s["observation"], "obj_pose")[2] < z0 + 0.03
            and vec(s["observation"], "tcp_pose")[2] > z0 + 0.06
            for s in prefix[j - 2 : j + 1]
        )
        dropped = peak > z0 + 0.06 and z < peak - 0.03 and ungrasped(state)
        if missed or dropped:
            stop = j
            reason = "MISSED_LIFT" if missed else "DROP"
            break
    assert len(raw["prefix_controls"]) == stop
    assert len(prefix) == stop + 1
    return stop, reason


def main():
    result = {}
    for task in TASKS:
        p = paths(task)
        identities = set()
        parents = set()
        seeds = set()
        checks = []
        for phase, expected in [
            ("discovery", 128),
            ("calibration", 1024),
            ("test", 256),
        ]:
            directory = p["base"] / (
                "records/" + phase if task == "PushCube-v1" else phase
            )
            rows = [read(f) for f in sorted(directory.glob("*.json"))]
            assert len(rows) == expected
            for record in rows:
                spec = record["spec"]
                parent = record.get(
                    "parent_id", record.get("record", {}).get("parent_id")
                )
                assert parent not in parents and spec["seed"] not in seeds
                parents.add(parent)
                seeds.add(spec["seed"])
                label = (
                    ("selected" if phase == "test" else "assigned")
                    if task == "PushCube-v1"
                    else (
                        "selected_policy" if phase == "test" else "randomized_assigned"
                    )
                )
                rawpath = (
                    p["physics"] / phase / str(spec["index"]) / (label + ".json.gz")
                )
                raw = read(rawpath)
                if task == "PickCube-v1":
                    stop, reason = grasp_stop(raw)
                else:
                    assert (
                        len(raw["prefix_controls"]) == 53 and len(raw["prefix"]) == 54
                    )
                    stop, reason = 53, "FIXED_TRANSPORT_BOUNDARY"
                first, current = (
                    raw["prefix"][0]["observation"],
                    raw["checkpoint"]["observation"],
                )
                primary, _ = predicates(first, current)
                assert primary == raw["features"]
                identity = hashlib.sha256(
                    json.dumps(
                        [raw["prefix"], raw["controller_memory"]], sort_keys=True
                    ).encode()
                ).hexdigest()
                assert identity not in identities, (task, spec)
                identities.add(identity)
                checks.append(
                    {
                        "phase": phase,
                        "parent_id": parent,
                        "seed": spec["seed"],
                        "boundary_controls": stop,
                        "trigger": reason,
                        "native": str(rawpath),
                        "physical_history_identity": identity,
                    }
                )
        result[task] = {
            "discovery_partition_reproduction": discovery_check(task, p),
            "parents": len(parents),
            "unique_seeds": len(seeds),
            "unique_physical_histories": len(identities),
            "checks": checks,
            "privileged_trigger": "Native simulator grasp flag selects missed-lift/drop boundary; excluded from learner X"
            if task == "PickCube-v1"
            else "Fixed53-control boundary",
            "independence_scope": "Distinct registered IDs/seeds/fresh histories are verified. Exchangeability and iid regional sampling remain declared stochastic-model assumptions, not proven by uniqueness.",
        }
        print("Predecision source checks passed", task, len(checks), flush=True)
    save(
        ROOT / "E0/checkpoint_and_parent_identity_audit.json",
        {
            "passed": True,
            "tasks": result,
            "input_sha256": INPUTS,
            "source_assumptions": "Controller/source continuity and execution parity are source-supported. Population independence, exchangeability, stationarity and hardware joint-counterfactual transfer are not established merely by source hashes.",
        },
    )


if __name__ == "__main__":
    main()
