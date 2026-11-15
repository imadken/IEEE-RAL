"""Reproduce v1.2 compact routing/counts without simulator frames or new physics."""

import argparse
import gzip
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(path.read_text())


def main(root):
    seal = read(root / "packet_seal.json")
    for path, expected in seal["files"].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path
    sys.path.insert(0, str(root / "sources/src"))
    from dual_rec.dsre.features import PRIMARY, ObservationHistory, feature_values
    from dual_rec.dsre.measurement import (
        MeasurementScope,
        RobustRouter,
        bounded_evidence,
    )
    from dual_rec.dsre.operational import OperationalRouter, PolicyInput, gated_action
    from dual_rec.dsre.repair_oracle import Oracle
    from dual_rec.dsre.repair_selection import OPTIONAL, optional_values

    with gzip.open(root / "data/compact_rows.jsonl.gz", "rt") as f:
        rows = {r["id"]: r for r in map(json.loads, f)}
    frozen = read(root / "data/frozen_routers.json")
    calibration = read(root / "data/original_calibration_decision.json")["strata"]
    point = OperationalRouter(frozen)
    robust = RobustRouter(frozen)
    oracles = {
        t: Oracle(s["1"]["table"], s["1"]["parent_groups"])
        for t, s in frozen["tasks"].items()
    }
    minimum_cases = set()
    routing_checks = 0
    count_checks = 0
    minimum_checks = 0
    interval_checks = 0
    draw_cache = {}

    def corruption(history, rho, id, rep):
        seed = int.from_bytes(
            hashlib.sha256(f"{id}|{rho}|{rep}|2026111503".encode()).digest()[:8],
            "little",
        )
        rng = random.Random(seed)
        frames = []
        for frame in (history.first, history.current):
            update = {}
            for name in ("object_position", "tcp_position", "goal_position"):
                xyz = getattr(frame, name) if frame is not None else None
                update[name] = (
                    None
                    if xyz is None
                    else tuple(v + rng.uniform(-rho, rho) for v in xyz)
                )
            frames.append(None if frame is None else frame.model_copy(update=update))
        return history.model_copy(update={"first": frames[0], "current": frames[1]})

    def scenarios(row, scenario):
        h = ObservationHistory.model_validate(row["runtime_history"])
        rho = 0
        obs = h
        if scenario.startswith("uniform"):
            left, rep = scenario.split("_r")
            rho = float(left.removeprefix("uniform"))
            obs = corruption(h, rho, row["id"], int(rep))
        elif scenario.startswith("delay"):
            obs = ObservationHistory.model_validate(row["actual_delay_history"])
            assert abs(h.current.time - obs.current.time - 0.25) < 1e-8
        elif scenario == "coarse02_point":
            frames = []
            for frame in (h.first, h.current):
                updates = {
                    n: None
                    if getattr(frame, n) is None
                    else tuple(round(v / 0.02) * 0.02 for v in getattr(frame, n))
                    for n in ("object_position", "tcp_position", "goal_position")
                }
                frames.append(frame.model_copy(update=updates))
            obs = h.model_copy(update={"first": frames[0], "current": frames[1]})
        else:
            rho = {"clean": 0, "bound001": 0.001, "bound005": 0.005}[scenario]
        e = bounded_evidence(
            obs,
            MeasurementScope(
                coordinate_error_m=rho,
                decision_time=h.current.time,
                reference_scope_identity="compact",
                source_regime=row["population"],
            ),
        )
        values = tuple(f.measured for f in e.facts)
        invariant = tuple(f.invariant for f in e.facts)
        p = PolicyInput(
            task=row["task"],
            values=values[:7] if row["task"] == "PickCube-v1" else values[:6],
            full_values=values,
        )
        outputs = {
            "point_proposal": point.route(p),
            "robust_proposal": robust.route(e.packet(row["task"])),
        }
        margin = dict(outputs["point_proposal"]["DSRE_strict"])
        if any(v is None for v in invariant[: len(p.values)]):
            margin.update(action=None, evidence=[])
        outputs["margin_all_inputs"] = {"margin_DSRE_strict": margin}
        gate = {}
        for m, d in outputs["point_proposal"].items():
            action = gated_action(m, row["task"], d["action"], calibration)
            gate[m] = {
                **d,
                "action": action,
                "evidence": d["evidence"] if action else [],
            }
        outputs["original_clean_gate"] = gate
        if scenario == "coarse02_point":
            invariant = values
        return outputs, values, invariant

    for phase, filename, resultfile, tablefield in (
        ("offline", "offline_decisions.jsonl.gz", "offline_uncertainty.json", "tables"),
        (
            "prospective",
            "prospective_decisions.jsonl.gz",
            "prospective_results.json",
            "tables",
        ),
        (
            "secondary",
            "secondary_decisions.jsonl.gz",
            "physical_effects_and_secondary.json",
            "secondary_tables",
        ),
    ):
        counts = defaultdict(Counter)
        parent_counts = defaultdict(lambda: defaultdict(Counter))
        reported = read(root / "results" / resultfile)[tablefield]
        lastkey = None
        scen = None
        with gzip.open(root / "data" / filename, "rt") as f:
            for line in f:
                rec = json.loads(line)
                row = rows[rec["id"]]
                key = (rec["id"], rec["scenario"])
                if key != lastkey:
                    scen = scenarios(row, rec["scenario"])
                    lastkey = key
                outputs, values, invariant = scen
                expected = outputs[rec["mode"]][rec["method"]]
                assert (expected["action"], expected["evidence"]) == (
                    rec["action"],
                    rec["evidence"],
                ), (phase, key, rec["mode"], rec["method"])
                routing_checks += 1
                if rec["method"] in (
                    "DSRE_strict",
                    "DSRE_risk",
                    "B7",
                    "B7_risk",
                ) and rec["mode"] in ("point_proposal", "robust_proposal"):
                    x = values if rec["mode"] == "point_proposal" else invariant
                    x = x[: 7 if row["task"] == "PickCube-v1" else 6]
                    mkey = (row["task"], tuple(x), rec["method"])
                    if mkey not in minimum_cases:
                        o = oracles[row["task"]]
                        query = {"scope": o.table["scope"], "features": list(x)}
                        answer = o.rule(query)
                        if answer is None and rec["method"] in ("DSRE_risk", "B7_risk"):
                            answer = o.rule(query, 0.1, 2)
                        assert rec["action"] == (answer["action"] if answer else None)
                        if answer:
                            assert rec["evidence"] == answer["evidence"]
                        minimum_cases.add(mkey)
                        minimum_checks += 1
                h = ObservationHistory.model_validate(row["runtime_history"])
                truth = dict(
                    zip(
                        PRIMARY + OPTIONAL,
                        feature_values(h) + optional_values(h),
                        strict=True,
                    )
                )
                available = dict(zip(PRIMARY + OPTIONAL, invariant, strict=True))
                action = rec["action"]
                c, r = (
                    row["outcomes"]["continue_value"],
                    row["outcomes"]["recover_value"],
                )
                good = bool(action) and row["outcomes"][action + "_value"]
                exact = {
                    "adequate": int(good),
                    "inadequate": int(bool(action) and not good),
                    "stop": int(action is None),
                    "required_total": int(not row["initial_success"] and not c and r),
                    "required_selected": int(
                        not row["initial_success"]
                        and not c
                        and r
                        and action == "recover"
                    ),
                    "recover_only_selected": int(not c and r and action == "recover"),
                    "harmful_recover": int(c and not r and action == "recover"),
                    "correct_continue": int(c and action == "continue"),
                    "maintenance": int(row["initial_success"] and good),
                    "neither_deferred": int(not c and not r and action is None),
                    "literals": len(rec["evidence"]),
                    "false_assertions": sum(
                        truth[f["feature"]] != f["value"] for f in rec["evidence"]
                    ),
                    "noninvariant_assertions": sum(
                        available[f["feature"]] != f["value"] for f in rec["evidence"]
                    ),
                }
                assert all(rec[k] == v for k, v in exact.items())
                count_checks += len(exact)
                base = "|".join(
                    rec[k] for k in ("population", "task", "scenario", "mode", "method")
                )
                for tkey in (base, base + "|" + rec["condition"]):
                    if tkey in reported:
                        counts[tkey].update(exact)
                        counts[tkey]["rows"] += 1
                        parent_counts[tkey][rec["group"]].update(exact)
                        parent_counts[tkey][rec["group"]]["rows"] += 1
        assert set(counts) == set(reported)
        for key, values in counts.items():
            assert all(
                reported[key][field] == number for field, number in values.items()
            ), (phase, key)
            group_ids = sorted(parent_counts[key])
            n = len(group_ids)
            assert reported[key]["parents"] == n
            if key.count("|") > 4 and sum(key.encode()) % 5:
                continue
            if n not in draw_cache:
                draw_cache[n] = np.random.default_rng(2026111504).integers(
                    0, n, (4000, n)
                )
            indices = draw_cache[n]
            arrays = {
                field: np.array(
                    [parent_counts[key][g][field] for g in group_ids], dtype=float
                )
                for field in (
                    "rows",
                    "adequate",
                    "inadequate",
                    "stop",
                    "required_total",
                    "required_selected",
                    "literals",
                    "false_assertions",
                )
            }
            for name, num_field, den_field in (
                ("adequacy", "adequate", "rows"),
                ("inadequacy", "inadequate", "rows"),
                ("abstention", "stop", "rows"),
                ("necessary_recovery_recall", "required_selected", "required_total"),
                ("conditional_inadequacy", "inadequate", None),
                ("average_explanation_length_selected", "literals", None),
                ("factual_assertion_error", "false_assertions", "literals"),
            ):
                num = arrays[num_field]
                den = (
                    arrays[den_field] if den_field else arrays["rows"] - arrays["stop"]
                )
                estimate = float(num.sum() / den.sum()) if den.sum() else None
                den_draws = den[indices].sum(axis=1)
                num_draws = num[indices].sum(axis=1)
                valid = den_draws > 0
                interval = (
                    np.quantile(
                        num_draws[valid] / den_draws[valid], [0.025, 0.975]
                    ).tolist()
                    if valid.any()
                    else [None, None]
                )
                target = reported[key]["intervals"][name]
                assert target["estimate"] == estimate
                assert [target["lower"], target["upper"]] == interval
                assert target["bootstrap_defined_draws"] == int(valid.sum())
                interval_checks += 1
        print(json.dumps({"verified_phase": phase, "tables": len(counts)}), flush=True)
    print(
        json.dumps(
            {
                "verified": True,
                "routing_decisions": routing_checks,
                "raw_label_count_checks": count_checks,
                "minimum_certificate_cases": minimum_checks,
                "independent_bootstrap_intervals": interval_checks,
                "compact_rows": len(rows),
                "scope": "Numerical/routing reproduction. Full physics frames remain in the sealed workstation evidence root; no new simulation or population qualification.",
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    main(a.root)
