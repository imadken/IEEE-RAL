"""Independent minimum-certificate, raw-label and direct-index interval audit."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_recovery_audit import gz
from dsre_science_audit import RouteAudit

from dual_rec.dsre.repair_oracle import Oracle


def verify_minimum(oracle, values, decision, risk=False):
    query = {"scope": oracle.table["scope"], "features": list(values)}
    expected = oracle.rule(query)
    if risk and expected is None:
        expected = oracle.rule(query, 0.1, 2)
    assert decision["action"] == (expected["action"] if expected else None)
    if expected:
        assert decision["evidence"] == expected["evidence"]
        if not risk:
            diagnosis = decision.get("diagnosis")
            if diagnosis:
                certificate = diagnosis["certificate"]
                assert set(certificate["matched_ids"]) == set(expected["matched_ids"])
                rows = {r["id"]: r for r in oracle.rows}
                names = oracle.table["scope"]["features"]
                for witness in certificate["witnesses"]:
                    assert witness["kind"] == "LITERAL_NECESSITY"
                    bad = rows[witness["states"][0]["id"]]
                    assert bad["outcomes"][expected["action"] + "_value"] is not True
                    for fact in expected["evidence"]:
                        if fact != witness["removed"]:
                            value = bad["features"][names.index(fact["feature"])]
                            assert value is None or value == fact["value"]
    elif "diagnosis" in decision:
        actual = {o["kind"] for o in decision["diagnosis"]["obstructions"]}
        assert actual == oracle.obstruction_types(query)


def check_intervals(records, tables):
    # Rebuild independent parent counters directly from the ledger, then use
    # direct indexed bootstrap samples instead of analysis matrix multiplication.
    fields = (
        "adequate",
        "inadequate",
        "stop",
        "required_total",
        "required_selected",
        "literals",
        "false_assertions",
    )
    groups = defaultdict(lambda: defaultdict(Counter))
    totals = defaultdict(Counter)
    for r in records:
        base = "|".join(
            r[k] for k in ("population", "task", "scenario", "mode", "method")
        )
        for key in (base, base + "|" + r["condition"]):
            if key not in tables:
                continue
            counts = {k: r[k] for k in fields}
            counts["rows"] = 1
            totals[key].update(counts)
            groups[key][r["group"]].update(counts)
    checked = 0
    draws = {}
    for key, reported in tables.items():
        for field in (*fields, "rows"):
            assert reported[field] == totals[key][field], (key, field)
        parent_ids = sorted(groups[key])
        n = len(parent_ids)
        assert reported["parents"] == n
        if n not in draws:
            draws[n] = np.random.default_rng(2026111504).integers(0, n, (4000, n))
        sample = draws[n]
        arrays = {
            field: np.array([groups[key][p][field] for p in parent_ids], dtype=float)
            for field in (*fields, "rows")
        }
        for name, numerator, denominator in (
            ("adequacy", "adequate", "rows"),
            ("inadequacy", "inadequate", "rows"),
            ("abstention", "stop", "rows"),
            ("necessary_recovery_recall", "required_selected", "required_total"),
            ("conditional_inadequacy", "inadequate", None),
            ("average_explanation_length_selected", "literals", None),
            ("factual_assertion_error", "false_assertions", "literals"),
        ):
            num = arrays[numerator]
            den = (
                arrays[denominator] if denominator else arrays["rows"] - arrays["stop"]
            )
            result = reported["intervals"][name]
            point = num.sum() / den.sum() if den.sum() else None
            assert result["estimate"] == point
            # All pooled tables; deterministic one-in-five condition-specific
            # intervals, with all point counts still verified above.
            if key.count("|") > 4 and sum(key.encode()) % 5:
                continue
            sums = den[sample].sum(axis=1)
            snum = num[sample].sum(axis=1)
            valid = sums > 0
            interval = (
                np.quantile(snum[valid] / sums[valid], [0.025, 0.975]).tolist()
                if valid.any()
                else [None, None]
            )
            assert result["bootstrap_defined_draws"] == int(valid.sum())
            assert result["lower"] == interval[0] and result["upper"] == interval[1], (
                key,
                name,
                result,
                interval,
            )
            checked += 1
    return {"tables_recounted": len(tables), "independent_intervals": checked}


def run(root, prospective=False):
    from dsre_science_offline import corrupt, delayed

    from dual_rec.dsre.features import ObservationHistory
    from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence

    prefix = "prospective" if prospective else "offline"
    with gzip.open(root / (prefix + "_rows.jsonl.gz"), "rt") as f:
        rows = [json.loads(s) for s in f]
    by_id = {r["id"]: r for r in rows}
    with gzip.open(root / (prefix + "_decisions.jsonl.gz"), "rt") as f:
        records = [json.loads(s) for s in f]
    tables = read(
        root
        / ("prospective_results.json" if prospective else "offline_uncertainty.json")
    )["tables"]
    counts = check_intervals(records, tables)
    frozen = read(root / "frozen_routers.json")
    routing = RouteAudit(frozen)
    oracles = {
        t: Oracle(v["1"]["table"], v["1"]["parent_groups"])
        for t, v in frozen["tasks"].items()
    }
    cases = set()
    minimum_checks = 0
    actual_route_checks = 0
    true_counts = Counter()
    if prospective:
        seal = read(root / "prospective_recommendation_seal.json")
        for row in rows:
            raw = gz(Path(row["source"]))
            assert sha(Path(row["source"])) == row["source_sha256"]
            assert raw["screened_epoch"] <= seal["epoch"]
            for mode in ("continue", "recover"):
                out = gz(Path(row["source"]).parent / (mode + ".json.gz"))
                assert row["outcomes"][mode + "_value"] == bool(
                    out["frames"][-1]["state"]["success"]
                )
            for scenario, data in raw["scenarios"].items():
                assert (
                    data["measurement"]["risk_qualification_covers_sensor_regime"]
                    is False
                )
                for mode in ("point_proposal", "robust_proposal"):
                    key = "measured" if mode == "point_proposal" else "invariant"
                    values = [f[key] for f in data["measurement"]["facts"]][:7]
                    for method, d in data[mode].items():
                        expected = routing.expected(
                            row["task"], values, method, mode == "robust_proposal"
                        )
                        if expected != "UNASSESSED":
                            assert d["action"] == expected
                            actual_route_checks += 1
                    case = (row["task"], tuple(values))
                    if case not in cases:
                        oracle = oracles[row["task"]]
                        verify_minimum(oracle, values, data[mode]["DSRE_strict"])
                        verify_minimum(oracle, values, data[mode]["DSRE_risk"], True)
                        minimum_checks += 2
                        cases.add(case)
    else:
        values_cache = {}
        for rec in records:
            if rec["method"] not in (
                "DSRE_strict",
                "DSRE_risk",
                "B7",
                "B7_risk",
            ) or rec["mode"] not in ("point_proposal", "robust_proposal"):
                continue
            row = by_id[rec["id"]]
            key = (rec["id"], rec["scenario"])
            if key not in values_cache:
                h = ObservationHistory.model_validate(row["runtime_history"])
                scenario = rec["scenario"]
                if scenario.startswith("uniform"):
                    left, k = scenario.split("_r")
                    rho = float(left.removeprefix("uniform"))
                    obs = corrupt(h, rho, row["id"], int(k))
                elif scenario.startswith("delay"):
                    rho = 0
                    obs = delayed(row, h)
                else:
                    rho = {"clean": 0, "bound001": 0.001, "bound005": 0.005}[scenario]
                    obs = h
                e = bounded_evidence(
                    obs,
                    MeasurementScope(
                        coordinate_error_m=rho,
                        decision_time=h.current.time,
                        reference_scope_identity="audit",
                        source_regime="audit",
                    ),
                )
                values_cache[key] = {
                    "point_proposal": [f.measured for f in e.facts],
                    "robust_proposal": [f.invariant for f in e.facts],
                }
            values = values_cache[key][rec["mode"]][
                : 7 if row["task"] == "PickCube-v1" else 6
            ]
            case = (row["task"], tuple(values), rec["method"])
            if case not in cases:
                verify_minimum(
                    oracles[row["task"]],
                    values,
                    rec,
                    rec["method"] in ("DSRE_risk", "B7_risk"),
                )
                minimum_checks += 1
                cases.add(case)
    for rec in records:
        row = by_id[rec["id"]]
        c, r = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
        action = rec["action"]
        good = bool(action) and row["outcomes"][action + "_value"]
        assert rec["adequate"] == int(good)
        assert rec["inadequate"] == int(bool(action) and not good)
        assert rec["required_total"] == int(not row["initial_success"] and not c and r)
        assert rec["required_selected"] == int(
            not row["initial_success"] and not c and r and action == "recover"
        )
        assert rec["harmful_recover"] == int(c and not r and action == "recover")
        true_counts["decision_rows"] += 1
        if rec["mode"] == "robust_proposal":
            assert rec["false_assertions"] == rec["noninvariant_assertions"] == 0
    output = {
        "passed": True,
        **counts,
        **true_counts,
        "minimum_certificate_cases": minimum_checks,
        "raw_proposal_routing_checks": actual_route_checks,
        "all_robust_assertions_valid": True,
        "population_qualification": "No OOD or altered-sensor qualification inferred",
        "epoch": time.time(),
    }
    atomic(root / (prefix + "_numerical_audit.json"), output)
    print(json.dumps(output), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--prospective", action="store_true")
    a = p.parse_args()
    run(a.root, a.prospective)
