"""Independent frozen-rule, raw-action and exact-binomial numerical checks."""

import argparse
import gzip
import json
import math
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_observations import packet_from_summary
from dsre_paper_confirmation import (
    audit_trace,
    difference,
    expected_action,
    independent_tree_action,
)
from scipy.stats import beta

from dual_rec.dsre.operational import METHODS, OperationalRouter, gated_action
from dual_rec.dsre.repair_oracle import Oracle


def audit_observation_values(packet, metadata, scenario):
    """Recompute predicates from the deliberately limited observed payload."""
    first, current = metadata["payload"]["first"], metadata["payload"]["current"]
    obj, tcp, goal = (
        current[k] for k in ("object_position", "tcp_position", "goal_position")
    )
    distance = lambda a, b: (
        None
        if a is None or b is None
        else math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))
    )
    near, hand = distance(obj, goal), distance(tcp, obj)
    old = distance(first["object_position"], first["goal_position"]) if first else None
    moved = distance(obj, first["object_position"]) if first else None
    q = current["finger_positions"]
    primary = [
        None if near is None else near <= 0.03,
        None if hand is None else hand <= 0.04,
        None if old is None or near is None else old - near >= 0.005,
        None if moved is None else moved >= 0.005,
        None if q is None else sum(abs(v) for v in q) <= 0.04,
        None if obj is None or tcp is None else tcp[2] - obj[2] > 0.03,
    ]
    optional = []
    for a, b, index in ((obj, goal, 0), (obj, goal, 1), (tcp, obj, 0)):
        optional.extend(
            (None, None)
            if a is None or b is None
            else (a[index] - b[index] < -0.02, a[index] - b[index] > 0.02)
        )
    if scenario == "missing_optional":
        if packet.task == "PickCube-v1":
            optional[0] = None
        else:
            primary[0] = None
    assert tuple(primary + optional) == packet.full_values
    assert not any(
        k in metadata["payload"] for k in ("success", "outcomes", "grasped", "contacts")
    )
    return True


def audit_calibration(records, strata):
    checked = 0
    for key, value in strata.items():
        method, task, action = key.split("|")
        selected = [
            r
            for r in records
            if (r["method"], r["task"], r["action"]) == (method, task, action)
        ]
        parent_errors = {}
        for row in selected:
            parent_errors[row["group"]] = parent_errors.get(
                row["group"], False
            ) or bool(row["unacceptable"])
        n, k = len(parent_errors), sum(parent_errors.values())
        assert (n, k) == (value["assigned_parents"], value["error_parents"])
        for delta, field in (
            (0.0125, "primary_four_stratum_upper"),
            (0.05 / (4 * len(METHODS)), "upper"),
        ):
            expected = (
                1.0 if n == 0 or k == n else float(beta.ppf(1 - delta, k + 1, n - k))
            )
            assert abs(value[field] - expected) < 3e-12, (
                key,
                field,
                value[field],
                expected,
            )
            checked += 1
        assert value["enabled"] == bool(n and value["upper"] <= 0.1)
    return {
        "status": "PASS",
        "bounds_independently_recomputed": checked,
        "implementation": "Existing log-binomial inversion versus SciPy inverse-beta; grouping independently rebuilt as parent any-error",
    }


def audit_rules(router, rows, records):
    lookup = {r["id"]: r for r in rows}
    observed = {
        (r["id"], r["method"]): r
        for r in records
        if r["mode"] == "proposal" and r["scenario"] == "clean"
    }
    checks = 0
    outcomes = 0
    for task, (setting, _, rules, _) in router.settings.items():
        cache = {}
        oracle = Oracle(setting["table"], setting["parent_groups"])
        full = Oracle(setting["full_table"], setting["parent_groups"])
        for row in rows:
            if row["task"] != task:
                continue
            packet = packet_from_summary(row, {"tasks": {task: {"1": setting}}})
            query = {
                "scope": setting["table"]["scope"],
                "features": list(packet.values),
            }
            if packet.values not in cache:
                strict = oracle.rule(query)
                risk = strict or oracle.rule(query, 0.1, 2)
                expected = {
                    "DSRE_strict": strict["action"] if strict else None,
                    "B7": strict["action"] if strict else None,
                    "DSRE_risk": risk["action"] if risk else None,
                    "B7_risk": risk["action"] if risk else None,
                }
                for method, b, c in (
                    ("B1_one_strict", 0, 1),
                    ("B1_two_strict", 0, 2),
                    ("B5_beta10", 0.1, None),
                ):
                    rule = oracle.rule(query, b, c)
                    expected[method] = rule["action"] if rule else None
                for name in (
                    "CART1_strict",
                    "CART2_strict",
                    "CART1_beta10",
                    "CART2_beta10",
                ):
                    expected[name] = independent_tree_action(
                        setting["trees"][name[4]],
                        setting["table"],
                        setting["parent_groups"],
                        packet.values,
                        0.9 if name.endswith("beta10") else 1,
                    )
                cache[packet.values] = (expected, strict, risk)
            expected, strict, risk = cache[packet.values]
            actual = router.route(packet)
            for method, action in expected.items():
                assert actual[method]["action"] == action, (
                    task,
                    row["id"],
                    method,
                    actual[method],
                    action,
                )
                if method in ("B7", "DSRE_strict") and strict:
                    assert actual[method]["evidence"] == strict["evidence"]
                if method in ("B7_risk", "DSRE_risk") and risk:
                    assert actual[method]["evidence"] == risk["evidence"]
                checks += 1
            known = [i for i, x in enumerate(packet.full_values) if x is not None]
            mask = full.match(packet.full_values, known)
            full_action = next(
                (
                    a
                    for a in ("continue", "recover")
                    if full.parents(mask) >= 2 and not (mask & full.bad[a])
                ),
                None,
            )
            assert actual["full_signature_strict"]["action"] == full_action
            # Greedy is not claimed minimum: independently verify its universal
            # adequacy and independent support against the integer-mask reference.
            greedy = actual["greedy_pure_rule"]
            if greedy["action"]:
                ix = [
                    setting["table"]["scope"]["features"].index(f["feature"])
                    for f in greedy["evidence"]
                ]
                gm = oracle.match(packet.values, ix)
                assert oracle.parents(gm) >= 2 and not (
                    gm & oracle.bad[greedy["action"]]
                )
            assert actual["policy_faithful"]["action"] in (
                None,
                actual["CART2_beta10"]["action"],
            )
            with gzip.open(lookup[row["id"]]["source"], "rt") as stream:
                raw = json.load(stream)
            for method in METHODS:
                saved = observed[row["id"], method]
                action = actual[method]["action"]
                # Read the terminal measurement independently of scoring records.
                expected_good = int(
                    action is not None
                    and raw["traces"][action]["frames"][-1]["state"]["success"]
                )
                assert saved["successful"] == expected_good
                assert saved["initial_success"] == bool(
                    raw["canonical_start"]["success"]
                )
                outcomes += 1
    return {
        "status": "PASS",
        "rule_tree_action_checks": checks,
        "prediction_outcome_views_checked_from_raw": outcomes,
        "B7_and_risk_wrapper_equivalence": True,
    }


def audit_physics(root, rows):
    audits = [audit_trace(row, root) for row in rows]
    return {
        "status": "PASS",
        "qualified_traces": len(audits),
        "prefix_states": sum(r["prefix_states_checked"] for r in audits),
        "intervention_controls": sum(r["outcome_controls_checked"] for r in audits),
        "maximum_action_error": max(
            (r["maximum_action_error"] for r in audits), default=0
        ),
    }


def audit_selected(root, rows, calibration):
    executed = deferred = 0
    max_action_error = 0
    future_disagreements = 0
    router = OperationalRouter(read(root / "frozen_routers.json"))
    frozen = read(root / "frozen_routers.json")
    for row in rows:
        directory = (
            root / "selected" / row["task"] / f"{row['seed']}-{row['condition']}"
        )
        decision = read(directory / "decision.json")
        packet = packet_from_summary(row, frozen)
        proposed = router.route(packet)["DSRE_risk"]["action"]
        expected = gated_action("DSRE_risk", row["task"], proposed, calibration)
        assert decision["action"] == expected and decision[
            "predecision_input"
        ] == packet.model_dump(mode="json")
        result = read(directory / "execution.json")
        if expected is None:
            assert result["status"] == "DEFER_STOP" and result["new_continuations"] == 0
            deferred += 1
            continue
        assert sha(Path(result["source"])) == result["source_sha256"]
        with gzip.open(result["source"], "rt") as stream:
            trace = json.load(stream)
        for j, frame in enumerate(trace["frames"]):
            action = expected_action(
                row["task"],
                expected,
                j,
                frame["before_observation"],
                trace["initial_tcp"],
            )
            error = difference(action, frame["action"])
            assert error <= 2e-6
            max_action_error = max(max_action_error, error)
        assert len(trace["frames"]) == 70
        measured = bool(trace["frames"][-1]["state"]["success"])
        assert (
            measured
            == result["terminal_success"]
            == row["outcomes"][expected + "_value"]
        )
        future_disagreements += not result["selected_future_parity"]
        executed += 1
    assert future_disagreements == 0
    return {
        "status": "PASS",
        "new_selected_action_continuations": executed,
        "deferred_checkpoints": deferred,
        "future_trajectory_disagreements": future_disagreements,
        "maximum_action_error": max_action_error,
        "scope": "New repeated selected execution on the same registered parent; not additional independent samples",
    }


def chunk_audit(root):
    from dsre_operational_analysis import qualified

    verify_freeze(root)
    _, rows, _ = qualified(root)
    for path in sorted((root / "chunks").glob("*_complete.json")):
        target = path.with_name(path.name.replace("_complete", "_audit"))
        if target.exists():
            continue
        chunk = read(path)
        groups = set(chunk["completed_parents"])
        selected = [r for r in rows if r["group"] in groups]
        result = audit_physics(root, selected)
        if selected and selected[0]["split"] == "test":
            result["selected"] = audit_selected(
                root, selected, read(root / "calibration_decision.json")["strata"]
            )
        atomic(target, {"status": "PASS", "sequence": chunk["sequence"], **result})
    print("All completed chunk traces independently audited", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    chunk_audit(parser.parse_args().root)
