"""Fixed v1.2 existing-data ceilings, bounded sensor stress, and routing ledger."""

import argparse
import gzip
import hashlib
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_recovery_audit import gz

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.measurement import (
    MeasurementScope,
    RobustRouter,
    bounded_evidence,
    explain,
)
from dual_rec.dsre.measurement_oracle import check_invariance
from dual_rec.dsre.operational import OperationalRouter, PolicyInput, gated_action
from dual_rec.dsre.repair_selection import optional_values

OLD = Path("results/dsre-operational/20261114T180630Z")
LATEST = Path("results/dsre-operational/20261115T082827Z-recovery-evidence")
REFERENCE = Path("results/dsre-evidence-repair/20261113T180828Z/qualified_pairs.jsonl")


def paired_rows():
    rows = [
        dict(json.loads(s), population="development_reference")
        for s in REFERENCE.read_text().splitlines()
    ]
    for p in sorted(OLD.glob("fresh/*/*/summary.json")):
        rows.append(dict(read(p), population="historical_test_exploratory"))
    for p in sorted((LATEST / "test").glob("*/*/screen.json.gz")):
        raw = gz(p)
        history = ObservationHistory(
            first=observed_frame(
                raw["prefix"][0]["time"], raw["prefix"][0]["observation"]
            ),
            current=observed_frame(
                raw["canonical_start"]["time"], raw["canonical_start"]["observation"]
            ),
        )
        s = raw["summary"]
        rows.append(
            {
                **s,
                "id": f"PickCube-v1/{s['seed']}/{s['condition']}",
                "group": f"PickCube-v1/{s['seed']}",
                "population": "fresh160_reanalysis",
                "runtime_history": history.model_dump(mode="json"),
                "outcomes": {
                    a + "_value": gz(p.parent / (a + ".json.gz"))["terminal_success"]
                    for a in ("continue", "recover")
                },
                "source": str(p),
                "source_sha256": sha(p),
            }
        )
    return rows


def ceiling(rows, signatures):
    groups = defaultdict(list)
    for row, signature in zip(rows, signatures, strict=True):
        groups[tuple(signature)].append(row)
    adequate_mass = sum(any(r["outcomes"].values()) for r in rows)
    details = []
    for signature, group in sorted(groups.items(), key=lambda v: str(v[0])):
        common = [
            a
            for a in ("continue", "recover")
            if all(r["outcomes"][a + "_value"] is True for r in group)
        ]
        left = next(
            (
                r
                for r in group
                if r["outcomes"] == {"continue_value": True, "recover_value": False}
            ),
            None,
        )
        right = next(
            (
                r
                for r in group
                if r["outcomes"] == {"continue_value": False, "recover_value": True}
            ),
            None,
        )
        neither = next((r for r in group if not any(r["outcomes"].values())), None)
        details.append(
            {
                "signature": signature,
                "rows": len(group),
                "parents": len({r["group"] for r in group}),
                "ids": [r["id"] for r in group],
                "common_actions": common,
                "ambiguity_pair": [left["id"], right["id"]] if left and right else [],
                "neither_witness": neither["id"] if neither else None,
            }
        )
    mass = sum(d["rows"] for d in details if d["common_actions"])
    return {
        "rows": len(rows),
        "parents": len({r["group"] for r in rows}),
        "action_mass": adequate_mass,
        "observation_mass": mass,
        "action_ceiling": adequate_mass / len(rows),
        "observation_ceiling": mass / len(rows),
        "repertoire_insufficient": len(rows) - adequate_mass,
        "aliasing_gap": adequate_mass - mass,
        "ambiguity_class_mass": sum(d["rows"] for d in details if d["ambiguity_pair"]),
        "neither_containing_class_mass": sum(
            d["rows"] for d in details if d["neither_witness"]
        ),
        "overlap_class_mass": sum(
            d["rows"] for d in details if d["ambiguity_pair"] and d["neither_witness"]
        ),
        "singleton_classes": sum(d["rows"] == 1 for d in details),
        "groups": details,
    }


def mechanism(rows):
    out = {}
    for population, task in sorted({(r["population"], r["task"]) for r in rows}):
        selected = [
            r for r in rows if (r["population"], r["task"]) == (population, task)
        ]
        histories = [
            ObservationHistory.model_validate(r["runtime_history"]) for r in selected
        ]
        all_values = [feature_values(h) + optional_values(h) for h in histories]
        for n in (6, 7, 12):
            out[f"{population}|{task}|point{n}"] = ceiling(
                selected, [x[:n] for x in all_values]
            )
            for rho in (0.001, 0.005):
                signatures = [
                    tuple(
                        f.invariant
                        for f in bounded_evidence(
                            h,
                            MeasurementScope(
                                coordinate_error_m=rho,
                                decision_time=h.current.time,
                                reference_scope_identity="descriptive-same-table",
                                source_regime=population,
                            ),
                        ).facts[:n]
                    )
                    for h in histories
                ]
                out[f"{population}|{task}|robust{n}|rho{rho}"] = ceiling(
                    selected, signatures
                )
        poses = [
            tuple(
                v
                for frame in (h.first, h.current)
                if frame is not None
                for field in (
                    frame.object_position,
                    frame.tcp_position,
                    frame.goal_position,
                    frame.finger_positions,
                )
                for v in (field or (None,))
            )
            for h in histories
        ]
        out[f"{population}|{task}|exact_pose_unattainable"] = ceiling(selected, poses)
    return out


def corrupt(history, rho, row_id, replicate):
    seed = int.from_bytes(
        hashlib.sha256(f"{row_id}|{rho}|{replicate}|2026111503".encode()).digest()[:8],
        "little",
    )
    rng = random.Random(seed)
    frames = []
    for frame in (history.first, history.current):
        updates = {}
        for name in ("object_position", "tcp_position", "goal_position"):
            value = getattr(frame, name) if frame is not None else None
            updates[name] = (
                None
                if value is None
                else tuple(x + rng.uniform(-rho, rho) for x in value)
            )
        frames.append(None if frame is None else frame.model_copy(update=updates))
    return history.model_copy(update={"first": frames[0], "current": frames[1]})


def delayed(row, history):
    raw = gz(Path(row["source"]))
    prefix = raw.get("prefix", raw.get("prefix_history"))
    if not prefix or len(prefix) < 6:
        return None
    past = prefix[-6]
    if abs(history.current.time - past["time"] - 0.25) > 1e-8:
        return None
    return history.model_copy(
        update={"current": observed_frame(past["time"], past["observation"])}
    )


def row_scores(row, scenario, mode, outputs, original_values, sensor_values):
    c, r = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
    names = (
        "goal_near_03",
        "hand_object_near_04",
        "goal_progress_005",
        "object_moved_005",
        "gripper_closed_04",
        "hand_above_object_03",
        "object_left_of_goal_02",
        "object_right_of_goal_02",
        "object_behind_goal_02",
        "object_ahead_of_goal_02",
        "hand_left_of_object_02",
        "hand_right_of_object_02",
    )
    truth = dict(zip(names, original_values, strict=True))
    available = dict(zip(names, sensor_values, strict=True))
    records = []
    for method, d in outputs.items():
        action = d["action"]
        success = False if action is None else row["outcomes"][action + "_value"]
        evidence = d.get("evidence", [])
        records.append(
            {
                "id": row["id"],
                "group": row["group"],
                "population": row["population"],
                "task": row["task"],
                "condition": row.get("condition", row.get("condition_audit_only")),
                "scenario": scenario,
                "mode": mode,
                "method": method,
                "action": action,
                "evidence": evidence,
                "adequate": int(bool(action) and success),
                "inadequate": int(bool(action) and not success),
                "stop": int(action is None),
                "required_total": int(not row["initial_success"] and not c and r),
                "required_selected": int(
                    not row["initial_success"] and not c and r and action == "recover"
                ),
                "recover_only_selected": int(not c and r and action == "recover"),
                "harmful_recover": int(c and not r and action == "recover"),
                "correct_continue": int(c and action == "continue"),
                "maintenance": int(row["initial_success"] and bool(action) and success),
                "neither_deferred": int(not c and not r and action is None),
                "literals": len(evidence),
                "false_assertions": sum(
                    truth[f["feature"]] != f["value"] for f in evidence
                ),
                "noninvariant_assertions": sum(
                    available[f["feature"]] != f["value"] for f in evidence
                ),
            }
        )
    return records


def run(root):
    if (root / "offline_results.json").exists():
        raise ValueError("Offline evidence already written")
    rows = paired_rows()
    frozen = read(OLD / "frozen_routers.json")
    point = OperationalRouter(frozen)
    robust = RobustRouter(frozen)
    results = mechanism(rows)
    atomic(root / "mechanism_results.json", results)
    checks = 0
    factual_examples = []
    records = []
    unavailable = []
    calibration = read(LATEST / "calibration_decision.json")["strata"]
    for index, row in enumerate(rows):
        h = ObservationHistory.model_validate(row["runtime_history"])
        original = feature_values(h) + optional_values(h)
        scenarios = [("clean", h, 0.0), ("bound001", h, 0.001), ("bound005", h, 0.005)]
        for rho in (0.001, 0.005):
            scenarios += [
                (f"uniform{rho}_r{k}", corrupt(h, rho, row["id"], k), rho)
                for k in range(3)
            ]
        stale = delayed(row, h)
        if stale is not None:
            scenarios.append(("delay5_equal_250ms", stale, 0.0))
        else:
            unavailable.append(row["id"])
        previous = None
        for scenario, observed, rho in scenarios:
            scope = MeasurementScope(
                coordinate_error_m=rho,
                decision_time=h.current.time,
                reference_scope_identity=sha(OLD / "frozen_routers.json"),
                source_regime=row["population"],
                clean_risk_scope_eligible=scenario == "clean"
                and row["population"] != "development_reference",
            )
            e = bounded_evidence(observed, scope)
            if index % 11 == 0:
                checks += check_invariance(observed, rho, e, draws=32)
            fv = tuple(f.invariant for f in e.facts)
            measured = tuple(f.measured for f in e.facts)
            if scenario == "clean":
                assert fv == original
            if scenario in ("clean", "bound001", "bound005"):
                if previous is not None:
                    assert all(
                        b is None or a == b for a, b in zip(previous, fv, strict=True)
                    )
                previous = fv
            p = PolicyInput(
                task=row["task"],
                values=measured[:7] if row["task"] == "PickCube-v1" else measured[:6],
                full_values=measured,
            )
            point_output = point.route(p)
            robust_output = robust.route(e.packet(row["task"]))
            if scenario == "clean":
                assert point_output == robust_output
            for mode, output in (
                ("point_proposal", point_output),
                ("robust_proposal", robust_output),
            ):
                records += row_scores(row, scenario, mode, output, original, fv)
            # Per-predicate margin baseline: require every supplied primary input
            # invariant, then retain the frozen point DSRE; no learned score.
            width = len(p.values)
            margin = dict(point_output["DSRE_strict"])
            if any(v is None for v in fv[:width]):
                margin.update(action=None, evidence=[])
            records += row_scores(
                row,
                scenario,
                "margin_all_inputs",
                {"margin_DSRE_strict": margin},
                original,
                fv,
            )
            if scenario == "clean" and row["population"] != "development_reference":
                gated = {
                    m: {
                        **d,
                        "action": gated_action(
                            m, row["task"], d["action"], calibration
                        ),
                    }
                    for m, d in point_output.items()
                }
                for d in gated.values():
                    if d["action"] is None:
                        d["evidence"] = []
                records += row_scores(
                    row, scenario, "original_clean_gate", gated, original, fv
                )
            if (
                scenario == "bound005"
                and e.instability_witnesses
                and len(factual_examples) < 12
            ):
                nominal = point_output["DSRE_strict"]
                if any(
                    f["feature"] in e.undecidable_threshold_facts
                    for f in nominal.get("evidence", [])
                ):
                    factual_examples.append(
                        {
                            "id": row["id"],
                            "history": h.model_dump(mode="json"),
                            "paired_outcomes": row["outcomes"],
                            "nominal": nominal,
                            "robust": explain(e, robust, row["task"]),
                        }
                    )
        if index % 100 == 0:
            print(
                json.dumps({"offline_rows": index, "routing_records": len(records)}),
                flush=True,
            )
    with gzip.open(root / "offline_rows.jsonl.gz", "wt") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    with gzip.open(root / "offline_decisions.jsonl.gz", "wt") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    tables = defaultdict(Counter)
    for r in records:
        key = "|".join(
            r[k] for k in ("population", "task", "scenario", "mode", "method")
        )
        tables[key].update(
            {
                k: r[k]
                for k in (
                    "adequate",
                    "inadequate",
                    "stop",
                    "required_total",
                    "required_selected",
                    "recover_only_selected",
                    "harmful_recover",
                    "correct_continue",
                    "maintenance",
                    "neither_deferred",
                    "literals",
                    "false_assertions",
                    "noninvariant_assertions",
                )
            }
        )
        tables[key]["rows"] += 1
    atomic(
        root / "offline_results.json",
        {
            "tables": tables,
            "invariance_checks": checks,
            "explanation_examples": factual_examples,
            "delay_unavailable": unavailable,
            "delay_alias": "5 controls =250ms; one stress, not independent replications",
            "new_fits": 0,
            "epoch": time.time(),
        },
    )
    print(
        json.dumps(
            {
                "rows": len(rows),
                "decisions": len(records),
                "checks": checks,
                "delay_unavailable": len(unavailable),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    run(a.root)
