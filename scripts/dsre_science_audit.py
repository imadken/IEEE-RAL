"""Independent science-v1.2 routing, witness, invariant and raw-physics checks."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_paper_confirmation import (
    difference,
    expected_action,
    independent_tree_action,
    predicates,
    state_equal,
)
from dsre_recovery_audit import gz

from dual_rec.dsre.measurement_oracle import check_invariance
from dual_rec.dsre.repair_oracle import Oracle


def independent_ceiling(rows, signatures):
    # Independent pairwise equality masks; no production partition enumerator.
    actionable = 0
    checked = set()
    mass = 0
    for i, row in enumerate(rows):
        actionable += bool(
            row["outcomes"]["continue_value"] or row["outcomes"]["recover_value"]
        )
        key = tuple(signatures[i])
        if key in checked:
            continue
        checked.add(key)
        matches = [r for j, r in enumerate(rows) if tuple(signatures[j]) == key]
        can_continue = all(r["outcomes"]["continue_value"] is True for r in matches)
        can_recover = all(r["outcomes"]["recover_value"] is True for r in matches)
        if can_continue or can_recover:
            mass += len(matches)
    return actionable, mass


class RouteAudit:
    def __init__(self, frozen):
        self.settings = {t: v["1"] for t, v in frozen["tasks"].items()}
        self.oracles = {
            t: Oracle(s["table"], s["parent_groups"]) for t, s in self.settings.items()
        }
        self.cache = {}

    def expected(self, task, values, method, robust):
        key = (task, tuple(values), method, robust)
        if key in self.cache:
            return self.cache[key]
        s = self.settings[task]
        o = self.oracles[task]
        query = {"scope": s["table"]["scope"], "features": values}
        if method in (
            "DSRE_strict",
            "B7",
            "DSRE_risk",
            "B7_risk",
            "B1_one_strict",
            "B1_two_strict",
            "B5_beta10",
        ):
            if method in ("DSRE_risk", "B7_risk"):
                answer = o.rule(query) or o.rule(query, 0.1, 2)
            elif method == "B5_beta10":
                answer = o.rule(query, 0.1)
            else:
                answer = o.rule(
                    query,
                    0,
                    1
                    if method == "B1_one_strict"
                    else 2
                    if method == "B1_two_strict"
                    else None,
                )
            value = answer["action"] if answer else None
        elif method in ("CART1_strict", "CART2_strict", "CART1_beta10", "CART2_beta10"):
            unknown = [i for i, v in enumerate(values) if v is None]
            completions = []
            for bits in (
                product((False, True), repeat=len(unknown)) if robust else [None]
            ):
                x = list(values)
                if bits is not None:
                    for i, v in zip(unknown, bits, strict=True):
                        x[i] = v
                completions.append(
                    independent_tree_action(
                        s["trees"][method[4]],
                        s["table"],
                        s["parent_groups"],
                        x,
                        0.9 if method.endswith("beta10") else 1,
                    )
                )
            value = completions[0] if len(set(completions)) == 1 else None
        elif method.startswith("B0_"):
            value = method.removeprefix("B0_")
        else:
            return "UNASSESSED"
        self.cache[key] = value
        return value


def offline(root):
    # Imports below are adapters for constructing observations, not audit routing
    # or numeric tally implementations. Invariance oracle is a separate module.
    from dsre_science_offline import OLD, corrupt, delayed

    from dual_rec.dsre.features import ObservationHistory, feature_values
    from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence
    from dual_rec.dsre.repair_selection import optional_values

    with gzip.open(root / "offline_rows.jsonl.gz", "rt") as f:
        rows = [json.loads(s) for s in f]
    by_id = {r["id"]: r for r in rows}
    assert len(by_id) == len(rows)
    routing = RouteAudit(read(OLD / "frozen_routers.json"))
    scenarios = {}
    checks = 0
    tables = defaultdict(Counter)
    fields = (
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
    route_checks = 0
    count = 0
    with gzip.open(root / "offline_decisions.jsonl.gz", "rt") as f:
        for line in f:
            rec = json.loads(line)
            row = by_id[rec["id"]]
            key = (rec["id"], rec["scenario"])
            if key not in scenarios:
                h = ObservationHistory.model_validate(row["runtime_history"])
                scenario = rec["scenario"]
                if scenario.startswith("uniform"):
                    left, k = scenario.split("_r")
                    rho = float(left.removeprefix("uniform"))
                    observed = corrupt(h, rho, row["id"], int(k))
                elif scenario.startswith("delay"):
                    rho = 0
                    observed = delayed(row, h)
                else:
                    rho = {"clean": 0, "bound001": 0.001, "bound005": 0.005}[scenario]
                    observed = h
                e = bounded_evidence(
                    observed,
                    MeasurementScope(
                        coordinate_error_m=rho,
                        decision_time=h.current.time,
                        reference_scope_identity="audit",
                        source_regime="audit",
                    ),
                )
                true = feature_values(h) + optional_values(h)
                point = tuple(f.measured for f in e.facts)
                invariant = tuple(f.invariant for f in e.facts)
                if len(scenarios) % 13 == 0:
                    checks += check_invariance(observed, rho, e, draws=32)
                scenarios[key] = (true, point, invariant)
            true, point, invariant = scenarios[key]
            values = (
                point
                if rec["mode"]
                in ("point_proposal", "original_clean_gate", "margin_all_inputs")
                else invariant
            )
            n = 7 if row["task"] == "PickCube-v1" else 6
            if rec["mode"] != "original_clean_gate":
                if rec["mode"] == "margin_all_inputs":
                    expected = (
                        None
                        if any(v is None for v in invariant[:n])
                        else routing.expected(
                            row["task"], list(point[:n]), "DSRE_strict", False
                        )
                    )
                else:
                    expected = routing.expected(
                        row["task"],
                        list(values[:n]),
                        rec["method"],
                        rec["mode"] == "robust_proposal",
                    )
                if expected != "UNASSESSED":
                    assert rec["action"] == expected, (
                        key,
                        rec["mode"],
                        rec["method"],
                        rec["action"],
                        expected,
                    )
                    route_checks += 1
            action = rec["action"]
            c, r = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
            adequate = bool(action) and row["outcomes"][action + "_value"]
            assert rec["adequate"] == int(adequate)
            assert rec["inadequate"] == int(bool(action) and not adequate)
            assert rec["required_total"] == int(
                not row["initial_success"] and not c and r
            )
            assert rec["required_selected"] == int(
                not row["initial_success"] and not c and r and action == "recover"
            )
            tablekey = "|".join(
                rec[k] for k in ("population", "task", "scenario", "mode", "method")
            )
            tables[tablekey].update({k: rec[k] for k in fields})
            tables[tablekey]["rows"] += 1
            count += 1
            if rec["mode"] == "robust_proposal":
                assert rec["noninvariant_assertions"] == 0
    original = read(root / "offline_results.json")["tables"]
    assert dict(tables) == original
    ceilings = read(root / "mechanism_results.json")
    ceiling_checks = 0
    for key, record in ceilings.items():
        population, task, interface, *radius = key.split("|")
        selected = [
            r for r in rows if (r["population"], r["task"]) == (population, task)
        ]
        signatures = []
        for row in selected:
            h = ObservationHistory.model_validate(row["runtime_history"])
            if interface.startswith("point"):
                signatures.append(
                    (feature_values(h) + optional_values(h))[: int(interface[5:])]
                )
            elif interface.startswith("robust"):
                e = bounded_evidence(
                    h,
                    MeasurementScope(
                        coordinate_error_m=float(radius[0][3:]),
                        decision_time=h.current.time,
                        reference_scope_identity="audit",
                        source_regime="audit",
                    ),
                )
                signatures.append(
                    tuple(f.invariant for f in e.facts[: int(interface[6:])])
                )
            else:
                signatures.append(
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
                )
        action_mass, observation_mass = independent_ceiling(selected, signatures)
        assert (
            action_mass == record["action_mass"]
            and observation_mass == record["observation_mass"]
        )
        for group in record["groups"]:
            if group["ambiguity_pair"]:
                a, b = (by_id[i]["outcomes"] for i in group["ambiguity_pair"])
                assert a == {"continue_value": True, "recover_value": False} and b == {
                    "continue_value": False,
                    "recover_value": True,
                }
            if group["neither_witness"]:
                assert not any(by_id[group["neither_witness"]]["outcomes"].values())
        ceiling_checks += 1
    result = {
        "passed": True,
        "routing_checks": route_checks,
        "decision_rows": count,
        "invariance_checks": checks,
        "independent_ceiling_profiles": ceiling_checks,
        "tables_independently_recounted": len(tables),
        "unique_routing_cases": len(routing.cache),
        "equivalence": "Unchanged strict solver/B7 and strict-then-risk ordinary wrapper, including UNKNOWN inputs",
        "scope": "Independent integer-mask rule oracle, transcribed tree enumeration, raw outcome recount, and coordinate-box regression verifier; internal independent implementations, not external review",
        "epoch": time.time(),
    }
    atomic(root / "offline_audit.json", result)
    print(json.dumps(result), flush=True)


def audit_cell(raw, directory, repeats):
    # Independent exact approach-target semantics, not an object-position edit.
    initial = raw["prefix"][0]["observation"]
    obj = np.asarray(initial["extra"]["obj_pose"]).reshape(-1)[:3].copy()
    obj[0] += raw["offset_x_m"]
    goal = np.asarray(initial["extra"]["goal_pos"]).reshape(-1)[:3]
    assert raw["fault_spec"]["offset_x"] == raw["offset_x_m"]
    assert raw["model"]["edit"]["cube_before"] == raw["model"]["edit"]["cube_after"]
    for step, command in enumerate(raw["prefix_actions"]):
        before = raw["prefix"][step]["observation"]
        tcp = np.asarray(before["extra"]["tcp_pose"]).reshape(-1)[:3]
        phase = 0 if step < 20 else 1 if step < 45 else 2 if step < 60 else 3
        target = (
            obj + np.array([0, 0, 0.12 if phase == 0 else 0]) if phase < 3 else goal
        )
        expected = (
            np.r_[np.clip((target - tcp) / 0.1, -0.25, 0.25), 1 if phase < 2 else -1]
            .astype(np.float32)
            .tolist()
        )
        assert difference(expected, command) < 2e-6
    state_equal(raw["prefix"][-1], raw["canonical_start"])
    primary, optional = predicates(
        raw["prefix"][0]["observation"], raw["canonical_start"]["observation"]
    )
    assert (
        primary == raw["summary"]["features"]
        and optional == raw["summary"]["optional_features"]
    )
    checks = Counter(
        cells=1, prefix_states=0, future_states=0, continuations=0, contact_frames=0
    )
    gold = {}
    for repeat in range(repeats):
        d = directory / f"repeat{repeat}" if repeats > 1 else directory
        for mode in ("continue", "recover"):
            out = gz(d / (mode + ".json.gz"))
            assert out["controller_memory"] == raw["canonical_controller_memory"]
            assert out["model_edit"] == raw["model"]["edit"]
            for a, b in zip(raw["prefix"], out["prefix_states"], strict=True):
                state_equal(a, b)
                checks["prefix_states"] += 1
            state_equal(raw["canonical_start"], out["start"])
            previous = out["start"]
            assert len(out["frames"]) == 70
            for j, frame in enumerate(out["frames"]):
                assert (
                    difference(frame["before_observation"], previous["observation"])
                    <= 1e-8
                )
                assert (
                    difference(
                        expected_action(
                            "PickCube-v1",
                            mode,
                            j,
                            frame["before_observation"],
                            out["initial_tcp"],
                        ),
                        frame["action"],
                    )
                    < 2e-6
                )
                assert abs(frame["state"]["time"] - previous["time"] - 0.05) < 1e-8
                if repeat:
                    state_equal(gold[mode][j]["state"], frame["state"])
                previous = frame["state"]
                checks["future_states"] += 1
                checks["contact_frames"] += bool(previous["contacts"])
            assert bool(previous["success"]) == out["terminal_success"]
            if not repeat:
                gold[mode] = out["frames"]
            checks["continuations"] += 1
    return checks


def physics(root, pilot=False):
    plan = read(root / "study_plan.json")
    profiles = [p[0] for p in plan["profiles"]]
    total = Counter()
    qualified = []
    failures = []
    if pilot:
        for condition in profiles:
            ok = True
            for seed in plan["pilot_seeds"]:
                d = root / "pilot" / str(seed) / condition
                try:
                    assert not (d / "failure.json").exists()
                    checks = audit_cell(gz(d / "screen.json.gz"), d, 2)
                    total.update(checks)
                except (AssertionError, OSError, ValueError, KeyError) as error:
                    ok = False
                    failures.append(
                        {"condition": condition, "seed": seed, "reason": str(error)}
                    )
            if ok:
                qualified.append(condition)
        atomic(
            root / "pilot_qualification_seal.json",
            {
                "qualified_conditions": qualified,
                "unqualified_conditions": [c for c in profiles if c not in qualified],
                "all_attempts_retained": True,
                "checks": total,
                "failures": failures,
                "plan_sha256": sha(root / "study_plan.json"),
                "epoch": time.time(),
            },
        )
    else:
        seal = read(root / "prospective_recommendation_seal.json")
        for p in sorted((root / "progress").glob("outcome-*.json")):
            progress = read(p)
            if progress["status"] != "COMPLETE":
                continue
            seed = progress["seed"]
            d = root / "prospective" / str(seed)
            assert sha(d / "recommendations.json") == seal["parents"][str(seed)]
            begun = read(d / "execution_started.json")
            assert begun["epoch"] > seal["epoch"] and begun[
                "cohort_seal_sha256"
            ] == sha(root / "prospective_recommendation_seal.json")
            rec = read(d / "recommendations.json")
            for c in rec["cells"]:
                raw = gz(d / c["condition"] / "screen.json.gz")
                assert sha(d / c["condition"] / "screen.json.gz") == c["screen_sha256"]
                assert raw["screened_epoch"] <= seal["epoch"]
                total.update(audit_cell(raw, d / c["condition"], 1))
        atomic(
            root / "prospective_physics_audit.json",
            {
                "passed": True,
                "checks": total,
                "cohort_decisions_precede_every_primary_future": True,
                "epoch": time.time(),
            },
        )
    print(
        json.dumps(
            {
                "pilot": pilot,
                "checks": total,
                "qualified": qualified,
                "failures": failures,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["offline", "pilot", "physics"])
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.command == "offline":
        offline(a.root)
    else:
        physics(a.root, a.command == "pilot")
