"""Registered clean-gate and paired-outcome estimates; no fitting or new policy."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_source_risk_audit import exact_upper, gz

FIELDS = (
    "rows",
    "acted",
    "continue",
    "recover",
    "adequate",
    "inadequate",
    "stop",
    "required_total",
    "required_selected",
    "recover_only_total",
    "recover_only_selected",
    "initially_unsuccessful",
    "harmful_recover",
    "both_success_total",
    "both_success_maintained",
    "initial_success_maintained",
    "neither_total",
    "neither_deferred",
    "literals",
    "false_assertions",
    "noninvariant_assertions",
    "matched_recovery_gain",
)
NAMES = (
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


def metrics(row, action, evidence=(), sensor_values=None):
    c, r = (row["outcomes"][a + "_value"] for a in ("continue", "recover"))
    acted = action is not None
    success = row["outcomes"][action + "_value"] if acted else False
    required = not row["initial_success"] and not c and r
    truth = dict(zip(NAMES, row["features"] + row["optional_features"], strict=True))
    sensor = (
        dict(zip(NAMES, sensor_values, strict=True))
        if sensor_values is not None
        else truth
    )
    evidence = evidence if acted else ()
    return dict(
        zip(
            FIELDS,
            map(
                int,
                (
                    1,
                    acted,
                    action == "continue",
                    action == "recover",
                    acted and success,
                    acted and not success,
                    not acted,
                    required,
                    required and action == "recover",
                    not c and r,
                    not c and r and action == "recover",
                    not row["initial_success"],
                    c and not r and action == "recover",
                    c and r,
                    c and r and acted,
                    row["initial_success"] and acted and success,
                    not c and not r,
                    not c and not r and not acted,
                    len(evidence),
                    sum(truth[f["feature"]] != f["value"] for f in evidence),
                    sum(sensor[f["feature"]] != f["value"] for f in evidence),
                    (int(r) - int(c)) if action == "recover" else 0,
                ),
            ),
            strict=True,
        )
    )


def bootstrap_indices(n, draws=4000, seed=2026111602):
    return np.random.Generator(np.random.PCG64(seed)).integers(0, n, (draws, n))


def interval(nums, dens, weights):
    nums, dens = np.asarray(nums, dtype=float), np.asarray(dens, dtype=float)
    den, num = weights @ dens, weights @ nums
    valid = den > 0
    lo, hi = (
        np.quantile(num[valid] / den[valid], [0.025, 0.975])
        if valid.any()
        else (None, None)
    )
    return {
        "estimate": float(nums.sum() / dens.sum()) if dens.sum() else None,
        "lower": None if lo is None else float(lo),
        "upper": None if hi is None else float(hi),
        "numerator": int(nums.sum()),
        "denominator": int(dens.sum()),
        "defined_bootstrap_draws": int(valid.sum()),
    }


def summarize(records):
    grouped = defaultdict(lambda: defaultdict(Counter))
    for rec in records:
        base = "|".join(rec[k] for k in ("scenario", "mode", "method"))
        keys = [base + "|ALL"]
        if rec["scenario"] == "clean":
            keys.append(base + "|" + rec["condition"])
        for key in keys:
            grouped[key][rec["group"]].update(rec["counts"])
    tables, cache = {}, {}
    for key, parents in grouped.items():
        groups = sorted(parents)
        n = len(groups)
        if n not in cache:
            cache[n] = np.asarray(
                [np.bincount(row, minlength=n) for row in bootstrap_indices(n)],
                dtype=float,
            )
        arrays = {
            field: np.asarray([parents[g][field] for g in groups], dtype=float)
            for field in FIELDS
        }
        bounds = {}
        for name, num, den in (
            ("unconditional_completion", "adequate", "rows"),
            ("coverage", "acted", "rows"),
            ("unconditional_inadequacy", "inadequate", "rows"),
            ("abstention", "stop", "rows"),
            ("conditional_success", "adequate", "acted"),
            ("required_recovery_recall", "required_selected", "required_total"),
            ("recover_only_recall", "recover_only_selected", "recover_only_total"),
            ("matched_recovery_effect", "matched_recovery_gain", "recover"),
        ):
            bounds[name] = interval(arrays[num], arrays[den], cache[n])
        tables[key] = {
            "counts": {field: int(arrays[field].sum()) for field in FIELDS},
            "parents": n,
            "intervals": bounds,
            "risk_scope": "INDEPENDENTLY_CALIBRATED_CLEAN_SOURCE_ACTIONS"
            if "|gated|" in key
            else "UNQUALIFIED_PROPOSALS",
        }
    return tables, grouped


def paired(grouped):
    result = {}
    for condition in (
        "ALL",
        "nominal",
        "offset001",
        "offset002",
        "offset003",
        "offset_minus002",
    ):
        a = "clean|gated|DSRE_risk|" + condition
        if a not in grouped:
            continue
        for other in (
            "CART2_beta10",
            "B7_risk",
            "B5_beta10",
            "B1_two_strict",
            "DSRE_strict",
        ):
            b = "clean|gated|" + other + "|" + condition
            groups = sorted(grouped[a])
            assert set(groups) == set(grouped[b])
            weights = np.asarray(
                [
                    np.bincount(row, minlength=len(groups))
                    for row in bootstrap_indices(len(groups))
                ],
                dtype=float,
            )
            for name, field, denominator in (
                ("completion", "adequate", "rows"),
                ("coverage", "acted", "rows"),
                ("inadequacy", "inadequate", "rows"),
                ("required_recovery_recall", "required_selected", "required_total"),
            ):
                assert all(
                    grouped[a][g][denominator] == grouped[b][g][denominator]
                    for g in groups
                )
                result[f"DSRE_risk_minus_{other}|{condition}|{name}"] = interval(
                    [grouped[a][g][field] - grouped[b][g][field] for g in groups],
                    [grouped[a][g][denominator] for g in groups],
                    weights,
                )
    return result


def hindsight(rows, n):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple((row["features"] + row["optional_features"])[:n])].append(row)
    action_mass = sum(any(r["outcomes"].values()) for r in rows)
    common_mass = sum(
        len(group)
        for group in buckets.values()
        if any(
            all(r["outcomes"][a + "_value"] for r in group)
            for a in ("continue", "recover")
        )
    )
    return {
        "rows": len(rows),
        "facts": n,
        "action_mass": action_mass,
        "common_action_signature_mass": common_mass,
        "scope": "Test-outcome hindsight only; not calibrated performance or a deployed reference certificate",
    }


def load_rows(root, stage):
    prefix = "test_outcome" if stage == "test" else stage
    rows, raw_by_id, packets = [], {}, {}
    for path in sorted((root / "progress").glob(prefix + "-*.json")):
        p = read(path)
        if p["status"] != "COMPLETE":
            continue
        directory = root / stage / str(p["seed"])
        decision = read(directory / "decision.json")
        assert sha(directory / "decision.json") == p["decision_sha256"]
        labels = read(directory / "outcome_labels.json")
        for cell in labels["cells"]:
            source = directory / cell["condition"] / "screen.json.gz"
            raw = gz(source)
            assert sha(source) == decision["screens"][cell["condition"]]
            row = raw["summary"] | {
                "id": f"PickCube-v1/{p['seed']}/{cell['condition']}",
                "group": str(p["seed"]),
                "outcomes": cell["outcomes"],
                "source": str(source),
                "source_sha256": sha(source),
            }
            rows.append(row)
            raw_by_id[row["id"]] = raw
            packets[row["id"]] = decision
    return rows, raw_by_id, packets


def frozen_reference_profile(frozen):
    table = frozen["tasks"]["PickCube-v1"]["1"]["table"]
    buckets = defaultdict(list)
    for row in table["rows"]:
        assert row.get("qualified", True)
        assert None not in row["features"]
        buckets[tuple(row["features"])].append(row)
    mass = sum(
        len(group)
        for group in buckets.values()
        if any(
            all(r["outcomes"][a + "_value"] is True for r in group)
            for a in ("continue", "recover")
        )
    )
    return {
        "scope": table["scope"],
        "reference_rows": len(table["rows"]),
        "reference_action_feasible_mass": sum(
            any(r["outcomes"].values()) for r in table["rows"]
        ),
        "reference_common_action_signature_mass": mass,
        "signature_classes": len(buckets),
        "interpretation": "Exact frozen-reference seven-fact partition ceiling; not test-outcome hindsight, not a new gate or population guarantee. Actual query certificates/witnesses retain registered support requirements.",
    }


def run(root):
    audit = read(root / "test_physics_audit.json")
    assert audit["passed"]
    assert read(root / "calibration_decision_audit.json")["passed"]
    assert read(root / "calibration_decision.json")["complete_cohort"]
    cal = read(root / "calibration_decision.json")["strata"]
    rows, raws, decisions = load_rows(root, "test")
    assert len(rows) == audit["parents"] * 5
    records, categories = [], defaultdict(Counter)
    inference_parents = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    witnesses = []
    for row in rows:
        raw, decision = raws[row["id"]], decisions[row["id"]]
        c, r = (row["outcomes"][a + "_value"] for a in ("continue", "recover"))
        kind = (
            "both_success"
            if c and r
            else "continue_only"
            if c
            else "recover_only"
            if r
            else "neither_success"
        )
        for condition in ("ALL", row["condition"]):
            categories[condition].update(
                {
                    kind: 1,
                    "rows": 1,
                    "initially_unsuccessful": int(not row["initial_success"]),
                    "required_recovery": int(
                        not row["initial_success"] and not c and r
                    ),
                }
            )
        for scenario, data in raw["scenarios"].items():
            variants = [
                ("proposal", data["point_proposal"], "measured"),
                ("robust_proposal", data["robust_proposal"], "invariant"),
            ]
            if scenario == "clean":
                outputs = {}
                for method, d in data["point_proposal"].items():
                    action = d["action"]
                    gated = (
                        action
                        if action is not None and cal[method + "|" + action]["enabled"]
                        else None
                    )
                    assert (
                        gated
                        == decision["clean_gated_actions"][row["condition"]][method]
                    )
                    outputs[method] = dict(d, action=gated)
                variants += [("gated", outputs, "measured")]
            for mode, outputs, sensor_key in variants:
                sensor = [f[sensor_key] for f in data["measurement"]["facts"]]
                for method, d in outputs.items():
                    action = d["action"]
                    record = {
                        "id": row["id"],
                        "group": row["group"],
                        "condition": row["condition"],
                        "scenario": scenario,
                        "mode": mode,
                        "method": method,
                        "action": action,
                        "counts": metrics(row, action, d.get("evidence", []), sensor),
                    }
                    records.append(record)
                    if scenario == "clean":
                        if action is not None:
                            inference_parents[mode][method + "|" + action][
                                row["group"]
                            ].append(not row["outcomes"][action + "_value"])
                        if method == "DSRE_strict" and mode == "proposal":
                            witnesses.append(
                                {
                                    "id": row["id"],
                                    "source_sha256": row["source_sha256"],
                                    "action": action,
                                    "diagnosis": d.get("diagnosis"),
                                }
                            )
        for data in raw["scenarios"].values():
            for mode in ("point_proposal", "robust_proposal"):
                for a, b in (("DSRE_strict", "B7"), ("DSRE_risk", "B7_risk")):
                    assert data[mode][a]["action"] == data[mode][b]["action"]
                    assert data[mode][a]["evidence"] == data[mode][b]["evidence"]
    tables, groups = summarize(records)
    contrasts = paired(groups)
    test_bounds = {}
    for mode in ("proposal", "robust_proposal", "gated"):
        strata = inference_parents[mode]
        test_bounds[mode] = {}
        for method in read(root / "study_plan.json")["methods"]:
            for action in ("continue", "recover"):
                key = method + "|" + action
                parents = strata[key]
                n, k = len(parents), sum(any(errors) for errors in parents.values())
                test_bounds[mode][key] = {
                    "assigned_parents": n,
                    "error_parents": k,
                    "upper": exact_upper(k, n),
                    "risk_point_estimate": k / n if n else None,
                    "scope": "Untouched test descriptive parent-any-assignment bound; never changes calibration eligibility",
                }
    with gzip.open(root / "test_rows.jsonl.gz", "wt") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    with gzip.open(root / "test_metric_records.jsonl.gz", "wt") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")
    atomic(root / "test_certificate_witnesses.json", witnesses)
    result = {
        "parents": audit["parents"],
        "checkpoints": len(rows),
        "complete_cohort": audit["complete_cohort"],
        "tables": tables,
        "paired_contrasts": contrasts,
        "paired_outcome_categories": dict(categories),
        "test_parent_action_bounds": test_bounds,
        "hindsight": {str(n): hindsight(rows, n) for n in (6, 7, 12)},
        "frozen_reference": frozen_reference_profile(
            read(root / "frozen_routers.json")
        ),
        "bootstrap": read(root / "study_plan.json")["bootstrap"],
        "B7_identity_exact": True,
        "all_noisy_proposals_risk_status": "NOT_QUALIFIED",
        "additional_controller_or_prefix_advantage": False,
        "calibration_sha256": sha(root / "calibration_decision.json"),
        "source_qualification_sha256": sha(root / "source_qualification_seal.json"),
        "analysis_source_sha256": sha(Path(__file__)),
        "epoch": time.time(),
    }
    atomic(root / "test_analysis.json", result)
    print(
        json.dumps(
            {
                "parents": result["parents"],
                "checkpoints": len(rows),
                "tables": len(tables),
                "records": len(records),
                "complete_cohort": result["complete_cohort"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)
