"""Frozen-router prospective scoring and independent recorded-physics audit."""

import argparse
import gzip
import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_paper_reanalysis import cluster_interval, summarize
from dsre_repair_experiment import predict

from dual_rec.dsre.baselines import OutcomeTree
from dual_rec.dsre.repair import ParentIndex, ParentRules, RepairQuery, RepairTable
from dual_rec.dsre.repair_oracle import Oracle


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def difference(left, right):
    if isinstance(left, dict) or isinstance(right, dict):
        assert isinstance(left, dict) and isinstance(right, dict)
        assert left.keys() == right.keys()
        return max((difference(left[k], right[k]) for k in left), default=0)
    x, y = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    assert x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    return float(np.max(np.abs(x - y))) if x.size else 0


def state_equal(a, b):
    assert np.linalg.norm(np.asarray(a["position"]) - b["position"]) <= 1e-5
    q, r = (
        np.asarray(a["quaternion"], dtype=float),
        np.asarray(b["quaternion"], dtype=float),
    )
    q, r = q / np.linalg.norm(q), r / np.linalg.norm(r)
    angle = 2 * math.acos(float(np.clip(abs(q @ r), 0, 1)))
    assert angle <= 1e-4
    for field in ("velocity", "qpos", "observation"):
        assert difference(a[field], b[field]) <= 1e-4
    assert abs(a["time"] - b["time"]) <= 1e-9
    assert a["success"] == b["success"] and a["contacts"] == b["contacts"]


def vec(observation, key):
    return np.asarray(observation["extra"][key], dtype=float).reshape(-1)[:3]


def expected_action(task, mode, step, observation, initial_tcp):
    """Independent transcription, using only each recorded pre-action packet."""
    cube, tcp, goal = (
        vec(observation, k) for k in ("obj_pose", "tcp_pose", "goal_pos")
    )
    gripper = -1
    if task == "PickCube-v1":
        target = goal
        if mode == "recover":
            if step < 8:
                target = np.asarray(initial_tcp) + [0, 0, 0.10]
                gripper = 1
            elif step < 22:
                target = cube + [0, 0, 0.10]
                gripper = 1
            elif step < 34:
                target = cube
                gripper = 1
            elif step < 46:
                target = cube
    else:
        target = np.array([goal[0], goal[1], cube[2]])
        if mode == "recover":
            if step < 6:
                target = np.asarray(initial_tcp) + [0, 0, 0.08]
            elif step < 16:
                target = cube + [-0.055, 0, 0.10]
            elif step < 26:
                target = cube + [-0.055, 0, 0]
    return np.r_[np.clip((target - tcp) / 0.1, -0.25, 0.25), gripper].astype(np.float32)


def predicates(first, current):
    obj, tcp, goal = (vec(current, k) for k in ("obj_pose", "tcp_pose", "goal_pos"))
    old_obj, old_goal = (vec(first, k) for k in ("obj_pose", "goal_pos"))
    fingers = np.asarray(current["agent"]["qpos"], dtype=float).reshape(-1)[-2:]
    near = np.linalg.norm(obj - goal)
    primary = [
        near <= 0.03,
        np.linalg.norm(obj - tcp) <= 0.04,
        np.linalg.norm(old_obj - old_goal) - near >= 0.005,
        np.linalg.norm(obj - old_obj) >= 0.005,
        np.abs(fingers).sum() <= 0.04,
        tcp[2] - obj[2] > 0.03,
    ]
    dx, dy, hx = obj[0] - goal[0], obj[1] - goal[1], tcp[0] - obj[0]
    optional = [dx < -0.02, dx > 0.02, dy < -0.02, dy > 0.02, hx < -0.02, hx > 0.02]
    return [bool(v) for v in primary], [bool(v) for v in optional]


def independent_tree_action(nodes, table, groups, x, target):
    """Read frozen splits, then recompute conservative leaf utility from raw rows."""
    node, path = 0, []
    while nodes[node]["feature"] is not None:
        feature = nodes[node]["feature"]
        if x[feature] is None:
            return None
        path.append(feature)
        node = nodes[node]["right"] if x[feature] else nodes[node]["left"]
    matched = [
        r for r in table["rows"] if all(r["features"][i] in (None, x[i]) for i in path)
    ]
    if len(matched) < 2 or len({groups[r["id"]] for r in matched}) < 2:
        return None
    means = [
        sum(r["outcomes"][a + "_value"] is True for r in matched) / len(matched)
        for a in ("continue", "recover")
    ]
    return (
        None
        if max(means) < target
        else ("recover" if means[1] > means[0] else "continue")
    )


def audit_trace(summary, root):
    path = Path(summary["source"])
    assert sha(path) == summary["source_sha256"]
    with gzip.open(path, "rt") as stream:
        record = json.load(stream)
    assert record["cell"] == {k: summary[k] for k in ("task", "seed", "condition")}
    assert record["freeze_sha256"] == sha(root / "confirmation_freeze.json")
    assert record["future_trajectory_duplicate_executions"] == 0
    prefix = record["prefix"]
    assert len(prefix) == len(record["prefix_actions"]) + 1
    state_equal(prefix[-1], record["canonical_start"])
    primary, optional = predicates(
        prefix[0]["observation"], record["canonical_start"]["observation"]
    )
    assert primary == summary["features"] and optional == summary["optional_features"]
    assert summary["initial_success"] == record["canonical_start"]["success"]
    controls = 0
    maximum_action_error = 0
    for mode in ("continue", "recover"):
        trace = record["traces"][mode]
        assert trace["controller_memory"] == record["canonical_controller_memory"]
        assert trace["model_edit"] == record["model"]["edit"]
        assert len(trace["prefix_history"]) == len(prefix)
        for a, b in zip(prefix, trace["prefix_history"], strict=True):
            state_equal(a, b)
        state_equal(trace["start"], record["canonical_start"])
        assert len(trace["frames"]) == 70
        previous = trace["start"]
        for j, frame in enumerate(trace["frames"]):
            assert (
                difference(previous["observation"], frame["before_observation"]) <= 1e-8
            )
            expected = expected_action(
                summary["task"],
                mode,
                j,
                frame["before_observation"],
                trace["initial_tcp"],
            )
            error = difference(expected, frame["action"])
            maximum_action_error = max(maximum_action_error, error)
            assert error <= 2e-6, (summary["id"], mode, j, error)
            assert abs(frame["state"]["time"] - previous["time"] - 0.05) < 1e-8
            previous = frame["state"]
            controls += 1
        assert (
            summary["outcomes"][mode + "_value"]
            == previous["success"]
            == record["outcomes"][mode + "_value"]
        )
    assert record["model"]["versions"] == {
        "mani-skill": "3.0.1",
        "sapien": "3.0.3",
        "torch": "2.5.1+cpu",
        "numpy": "1.26.4",
    }
    return {
        "id": summary["id"],
        "raw_sha256": sha(path),
        "prefix_states_checked": 2 * len(prefix),
        "outcome_controls_checked": controls,
        "maximum_action_error": maximum_action_error,
        "status": "PASS",
    }


def evaluate(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence sealed; reproduce in a separate scratch root")
    methods = (
        "DSRE",
        "B7",
        "B5_beta10",
        "B1_two_strict",
        "CART1_strict",
        "CART2_strict",
        "CART1_beta10",
        "CART2_beta10",
        "B0_continue",
        "B0_recover",
    )
    assert (root / "physics_completed.json").exists(), (
        "Do not score an ongoing campaign"
    )
    started = time.process_time()
    complete = load(root / "physics_completed.json")
    qualified = (
        [
            json.loads(s)
            for s in (root / "fresh_qualified.jsonl").read_text().splitlines()
        ]
        if (root / "fresh_qualified.jsonl").exists()
        else []
    )
    manifest = load(root / "fresh_seed_manifest.json")["parents"]
    allowed = {
        f"{p['task']}/{p['seed']}/{c}" for p in manifest for c in p["conditions"]
    }
    assert len({r["id"] for r in qualified}) == len(qualified)
    assert all(r["id"] in allowed for r in qualified)
    completed = set(complete["fully_completed_seed_parents"])
    by_group = defaultdict(list)
    for row in qualified:
        by_group[row["group"]].append(row)
    assert all(len(by_group[g]) == 2 for g in completed)
    primary = [r for r in qualified if r["group"] in completed]
    save(
        root / "fresh_missingness.json",
        {
            "registered_parents": len(manifest),
            "fully_completed_parents": len(completed),
            "qualified_checkpoints": len(qualified),
            "primary_complete_parent_checkpoints": len(primary),
            "qualified_orphan_conditions": [
                r["id"] for r in qualified if r["group"] not in completed
            ],
            "missing_checkpoints": sorted(allowed - {r["id"] for r in qualified}),
            "excluded_or_missing_parents": [
                p["group"] for p in manifest if p["group"] not in completed
            ],
            "physics": complete,
        },
    )
    audits = [audit_trace(row, root) for row in qualified]
    save(root / "fresh_replay_audit_records.json", audits)
    frozen = load(root / "frozen_routers.json")
    records = []
    decisions = {}
    numerical = 0
    for task, settings in frozen["tasks"].items():
        for budget, setting in settings.items():
            table = RepairTable.model_validate(setting["table"])
            index = ParentIndex(table, setting["parent_groups"], 2)
            rules = ParentRules(table, setting["parent_groups"], 2)
            oracle = Oracle(setting["table"], setting["parent_groups"])
            trees = {}
            for depth, nodes in setting["trees"].items():
                tree = OutcomeTree.__new__(OutcomeTree)
                tree.rules, tree.depth, tree.pruning_alpha = rules, int(depth), 0
                tree.nodes = nodes
                tree.root = 0
                trees[depth] = tree
            for row in [r for r in primary if r["task"] == task]:
                x = [
                    *row["features"],
                    *[row["optional_features"][i] for i in setting["selected"]],
                ]
                query = RepairQuery(scope=table.scope, features=tuple(x))
                strict_started = time.perf_counter()
                strict = predict("DSRE", query, index, rules, trees)
                strict_runtime = time.perf_counter() - strict_started
                expected = oracle.rule(query.model_dump(mode="json"))
                assert strict["action"] == (expected["action"] if expected else None)
                if expected:
                    for field in ("evidence", "support", "independent_parents"):
                        assert strict[field] == expected[field]
                diagnosis = strict["diagnosis"]
                oracle.verify(query.model_dump(mode="json"), diagnosis)
                assert (
                    {o["kind"] for o in diagnosis["obstructions"]}
                    == oracle.obstruction_types(query.model_dump(mode="json"))
                    if not strict["action"]
                    else not diagnosis["obstructions"]
                )
                for method in methods:
                    then = time.perf_counter()
                    result = (
                        strict
                        if method == "DSRE"
                        else predict(method, query, index, rules, trees, strict)
                    )
                    runtime = (
                        strict_runtime
                        if method == "DSRE"
                        else time.perf_counter() - then
                    )
                    if method.startswith("CART"):
                        independent = independent_tree_action(
                            setting["trees"][method[4]],
                            setting["table"],
                            setting["parent_groups"],
                            x,
                            0.9 if method.endswith("beta10") else 1,
                        )
                        assert result["action"] == independent
                    if method in ("B7", "B5_beta10", "B1_two_strict"):
                        independent = oracle.rule(
                            query.model_dump(mode="json"),
                            0.1 if method == "B5_beta10" else 0,
                            2 if method == "B1_two_strict" else None,
                        )
                        assert result["action"] == (
                            independent["action"] if independent else None
                        )
                        if method == "B7":
                            assert (
                                result["action"] == strict["action"]
                                and result["evidence"] == strict["evidence"]
                            )
                    category = (
                        "both"
                        if all(row["outcomes"].values())
                        else "neither"
                        if not any(row["outcomes"].values())
                        else "continue_only"
                        if row["outcomes"]["continue_value"]
                        else "recover_only"
                    )
                    action = result["action"]
                    success = bool(action and row["outcomes"][action + "_value"])
                    key = f"{task}|{budget}|{method}|{tuple(x)}"
                    decisions[key] = {
                        "query": query.model_dump(mode="json"),
                        "result": result,
                    }
                    records.append(
                        {
                            "id": row["id"],
                            "group": row["group"],
                            "task": task,
                            "budget": int(budget),
                            "method": method,
                            "initial_success": row["initial_success"],
                            "category": category,
                            "action": action,
                            "recommended": int(action is not None),
                            "successful": int(success),
                            "unacceptable": int(action is not None and not success),
                            "literals": len(result["evidence"]),
                            "channels": len(setting["selected"]),
                            "runtime_seconds": runtime,
                            "decision_key": key,
                        }
                    )
                    numerical += 1
    grouped = defaultdict(list)
    for row in records:
        key = f"{row['task']}|{row['budget']}|{row['method']}"
        for population in (
            "all",
            "initial_success" if row["initial_success"] else "initial_failure",
            row["category"],
            row["action"] if row["action"] else "abstain",
        ):
            grouped[key + "|" + population].append(row)
    tables = {key: summarize(rs) for key, rs in grouped.items()}
    contrasts = {}
    for tindex, task in enumerate(frozen["tasks"]):
        task_parents = {r["group"] for r in primary if r["task"] == task}
        base = {
            r["id"]: r
            for r in records
            if r["task"] == task and r["budget"] == 0 and r["method"] == "DSRE"
        }
        target = {
            r["id"]: r
            for r in records
            if r["task"] == task and r["budget"] == 1 and r["method"] == "DSRE"
        }
        for population in ("all", "initial_failure", "initial_success"):
            rs = [
                {
                    "group": r["group"],
                    "difference": target[rid]["successful"] - r["successful"],
                    "coverage_difference": target[rid]["recommended"]
                    - r["recommended"],
                    "bad_difference": target[rid]["unacceptable"] - r["unacceptable"],
                }
                for rid, r in base.items()
                if population == "all"
                or r["initial_success"] == (population == "initial_success")
            ]
            contrasts[task + "|" + population] = {
                f: cluster_interval(
                    rs, f, 2026111319 + tindex, parent_groups=task_parents
                )
                for f in ("difference", "coverage_difference", "bad_difference")
            }
    assignments = {}
    for task, settings in frozen["tasks"].items():
        for budget in settings:
            for method in methods:
                for action in ("continue", "recover"):
                    key = f"{task}|{budget}|{method}|{action}"
                    rs = grouped.get(key, [])
                    n = len({r["group"] for r in rs})
                    k = len({r["group"] for r in rs if r["unacceptable"]})
                    assignments[key] = {
                        "assigned_parents": n,
                        "error_parents": k,
                        "checkpoints": len(rs),
                        "status": "NOT_CALIBRATED",
                        "required_zero_error_parents_for_previous_bound": 42,
                        "bound_not_reported": "Prospective confirmation, not an independent calibration/authorization population.",
                    }
    strong_contrasts = {}
    runtimes = {}
    for tindex, task in enumerate(frozen["tasks"]):
        parents = {r["group"] for r in primary if r["task"] == task}
        for budget in (0, 1):
            dsre = {
                r["id"]: r
                for r in records
                if r["task"] == task and r["budget"] == budget and r["method"] == "DSRE"
            }
            for method in methods:
                selected = [
                    r
                    for r in records
                    if r["task"] == task
                    and r["budget"] == budget
                    and r["method"] == method
                ]
                times = [r["runtime_seconds"] * 1000 for r in selected]
                runtimes[f"{task}|{budget}|{method}"] = {
                    "queries": len(times),
                    "median_ms": float(np.median(times)) if times else None,
                    "max_ms": max(times) if times else None,
                    "scope": "Recorded call wall time with prebuilt reference/index, no hard-real-time guarantee; repeated signatures may use rule caches.",
                }
                if method == "DSRE":
                    continue
                comparator = {r["id"]: r for r in selected}
                for population in ("all", "initial_failure", "initial_success"):
                    pairs = [
                        {
                            "group": r["group"],
                            "difference": r["successful"]
                            - comparator[rid]["successful"],
                            "error_difference": r["unacceptable"]
                            - comparator[rid]["unacceptable"],
                        }
                        for rid, r in dsre.items()
                        if population == "all"
                        or r["initial_success"] == (population == "initial_success")
                    ]
                    strong_contrasts[f"{task}|{budget}|DSRE-{method}|{population}"] = {
                        f: cluster_interval(
                            pairs, f, 2026111319 + tindex, parent_groups=parents
                        )
                        for f in ("difference", "error_difference")
                    }
    save(root / "fresh_strong_baseline_intervals.json", strong_contrasts)
    save(root / "fresh_query_runtime.json", runtimes)
    save(root / "fresh_stratified_tables.json", tables)
    save(root / "fresh_paired_intervals.json", contrasts)
    save(root / "fresh_assignment_counts.json", assignments)
    save(root / "fresh_prediction_records.json", records)
    save(root / "fresh_decisions.json", decisions)
    save(
        root / "fresh_independent_audit.json",
        {
            "status": "PASS",
            "qualified_checkpoint_traces_audited": len(audits),
            "primary_complete_parent_checkpoints": len(primary),
            "outcome_actions_audited": sum(
                a["outcome_controls_checked"] for a in audits
            ),
            "prefix_states_audited": sum(a["prefix_states_checked"] for a in audits),
            "numerical_prediction_views_checked": numerical,
            "maximum_action_error": max(
                (a["maximum_action_error"] for a in audits), default=0
            ),
            "cpu_seconds": time.process_time() - started,
            "qualification_scope": "Full canonical prefix, controller memory and actual action equations. No new duplicate future-trajectory physics, no external human replication.",
            "deployment": "NOT_CALIBRATED",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "fresh_traces": len(audits),
                "primary_checkpoints": len(primary),
                "prediction_views": numerical,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    evaluate(parser.parse_args().root)
