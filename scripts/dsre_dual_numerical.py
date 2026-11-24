"""Independent raw-outcome, sidecar, cost and direct-resampling verification."""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_dual_adjudication import assert_isolated, gz, read, sha, write_once
from dsre_dual_gate_audit import independent_bounds
from dsre_source_risk_oracle import Oracle, verify_minimum
from dsre_source_risk_terminal_audit import terminal_success


def raw_check(root, stage):
    rows = gz(root / (stage + "_rows.json.gz"))
    plan = read(root / "study_plan.json")
    assert len(rows) == len(plan[stage + "_seeds"]) * 5
    assert {r["seed"] for r in rows} == set(plan[stage + "_seeds"])
    settings = read(root / "frozen_routers.json")["tasks"]["PickCube-v1"]["1"]
    oracle = Oracle(settings["table"], settings["parent_groups"])
    checked = set()
    for row in rows:
        source = Path(row["source"])
        raw = gz(source)
        assert sha(source) == row["source_sha256"]
        assert terminal_success(raw["canonical_start"]) == row["initial_success"]
        for name, flag in (("continue", "c"), ("recover", "r")):
            branch = gz(source.parent / (name + ".json.gz"))
            assert (
                terminal_success(branch["frames"][-1]["state"])
                == row[flag]
                == branch["terminal_success"]
            )
        assert (
            raw["scenarios"]["clean"]["point_proposal"]["DSRE_risk"]["action"]
            == raw["scenarios"]["clean"]["point_proposal"]["B7_risk"]["action"]
        )
        query = tuple(row["features"][:7])
        if query not in checked:
            packet = raw["scenarios"]["clean"]["point_proposal"]
            verify_minimum(oracle, query, packet["DSRE_strict"])
            verify_minimum(oracle, query, packet["DSRE_risk"], True)
            checked.add(query)
        assert (
            raw["scenarios"]["clean"]["point_proposal"]["DSRE_risk"]["evidence"]
            == raw["scenarios"]["clean"]["point_proposal"]["B7_risk"]["evidence"]
        )
    return rows


def policy_actions(root, row):
    directory = root / "test" / str(row["seed"])
    sidecar, original = (
        read(directory / "dual_decision.json"),
        read(directory / "decision.json"),
    )
    calibration = read(root / "dual_calibration.json")
    legacy = read(root / "calibration_decision.json")
    original_seal, dual_seal = (
        read(root / "test_recommendation_seal.json"),
        read(root / "dual_test_seal.json"),
    )
    started = read(directory / "execution_started.json")
    assert sidecar["dual_calibration_sha256"] == sha(root / "dual_calibration.json")
    assert sidecar["original_decision_sha256"] == sha(directory / "decision.json")
    assert dual_seal["parents"][str(row["seed"])] == sha(
        directory / "dual_decision.json"
    )
    assert original_seal["parents"][str(row["seed"])] == sha(
        directory / "decision.json"
    )
    assert started["cohort_seal_sha256"] == sha(root / "test_recommendation_seal.json")
    assert (
        original["sealed_epoch"]
        <= original_seal["epoch"]
        <= sidecar["sealed_epoch"]
        <= dual_seal["epoch"]
        <= started["epoch"]
    )
    output = {
        "always_continue": "continue",
        "always_recover": "recover",
        "DSRE_raw": row["proposals"]["DSRE_risk"],
        "CART2_raw": row["proposals"]["CART2_beta10"],
    }
    for name, method in (
        ("DSRE", "DSRE_risk"),
        ("B7", "B7_risk"),
        ("CART2", "CART2_beta10"),
    ):
        key = "DSRE_risk" if method == "B7_risk" else method
        proposed = row["proposals"][method]
        old_allowed = (
            proposed is not None
            and legacy["strata"][method + "|" + proposed]["enabled"]
        )
        historical = proposed if old_allowed else None
        assert original["clean_gated_actions"][row["condition"]][method] == historical
        output[name + "_historical"] = historical
        for mode in ("absolute", "nondegradation"):
            absolute = (
                proposed is not None
                and calibration["bounds"][key + "|" + proposed + "|absolute"][
                    "qualified"
                ]
            )
            harm = (
                proposed == "recover"
                and calibration["bounds"][key + "|recover|nondegradation"]["qualified"]
            )
            allowed = absolute or (mode == "nondegradation" and harm)
            action = proposed if allowed else None
            annotation = (
                "ABSOLUTE_SUCCESS_QUALIFIED"
                if absolute
                else "TASK_NONDEGRADATION_QUALIFIED_ONLY"
                if allowed
                else "UNQUALIFIED"
            )
            actual = sidecar["decisions"][row["condition"]][method][mode]
            assert actual == {
                "action": action,
                "annotation": annotation,
                "task_adequacy_status_unchanged": True,
            }
            output[name + "_" + mode] = action
    return output


def independently_count(row, action):
    c, r, initial = row["c"], row["r"], row["initial_success"]
    count = {
        key: 0
        for key in (
            "rows",
            "acted",
            "continue",
            "recover",
            "success",
            "failure",
            "stop",
            "required",
            "required_selected",
            "initially_unsuccessful",
            "initial_failure_R",
            "preventive_R_only",
            "R_only",
            "harm_R",
            "futile_R",
            "both_success",
            "both_success_maintained",
            "both_success_R",
            "initial_success_maintained",
            "physical_recovery_gain",
            "completion_minus_continue",
            "recovery_controls",
            "futile_recovery_controls",
        )
    }
    count["rows"] = 1
    count["required"] = int(not initial and not c and r)
    count["initially_unsuccessful"] = int(not initial)
    count["both_success"] = int(c and r)
    selected_success = False
    if action is None:
        count["stop"] = 1
    else:
        count["acted"] = count[action] = 1
        selected_success = r if action == "recover" else c
        count["success"] = int(selected_success)
        count["failure"] = int(not selected_success)
        count["both_success_maintained"] = int(c and r)
        count["initial_success_maintained"] = int(initial and selected_success)
        if action == "recover":
            count["required_selected"] = count["required"]
            count["initial_failure_R"] = int(not initial)
            count["preventive_R_only"] = int(initial and not c and r)
            count["R_only"] = int(not c and r)
            count["harm_R"] = int(c and not r)
            count["futile_R"] = int(not c and not r)
            count["both_success_R"] = int(c and r)
            count["physical_recovery_gain"] = int(r) - int(c)
            count["recovery_controls"] = 70
            count["futile_recovery_controls"] = 70 * count["futile_R"]
    count["completion_minus_continue"] = int(selected_success) - int(c)
    return count


def check_interval(nums, dens, sample, reported):
    nums, dens = np.asarray(nums), np.asarray(dens)
    n, d = nums[sample].sum(axis=1), dens[sample].sum(axis=1)
    valid = d > 0
    limits = (
        np.quantile(n[valid] / d[valid], [0.025, 0.975])
        if valid.any()
        else [None, None]
    )
    assert reported["estimate"] == (
        float(nums.sum() / dens.sum()) if dens.sum() else None
    )
    assert reported["numerator"] == int(nums.sum()) and reported["denominator"] == int(
        dens.sum()
    )
    assert reported["defined_draws"] == int(valid.sum())
    for actual, expected in zip(
        limits, (reported["lower"], reported["upper"]), strict=True
    ):
        assert actual == expected or (
            actual is not None
            and expected is not None
            and abs(actual - expected) < 1e-12
        )


def verify(root):
    assert_isolated()
    calibration = raw_check(root, "calibration")
    expected = independent_bounds(calibration)
    cal = read(root / "dual_calibration.json")
    assert set(expected) == set(cal["bounds"]) and len(expected) == 6
    for key, row in expected.items():
        assert row["assigned_parents"] == cal["bounds"][key]["assigned_parents"]
        assert row["error_parents"] == cal["bounds"][key]["error_parents"]
        assert row["qualified"] == cal["bounds"][key]["qualified"]
        assert abs(row["upper"] - cal["bounds"][key]["upper"]) < 1e-12
    prior = Path(read(root / "initial.json")["prior_root"])
    assert sha(root / "calibration_decision.json") == sha(
        prior / "calibration_decision.json"
    )
    rows = raw_check(root, "test")
    lookup = {(r["seed"], r["condition"]): r for r in rows}
    result = read(root / "dual_results.json")
    grouped, action_cache = defaultdict(lambda: defaultdict(Counter)), {}
    records = 0
    with gzip.open(root / "policy_records.jsonl.gz", "rt") as stream:
        for line in stream:
            rec = json.loads(line)
            identity = (rec["seed"], rec["condition"])
            row = lookup[identity]
            if identity not in action_cache:
                action_cache[identity] = policy_actions(root, row)
            action = action_cache[identity][rec["policy"]]
            assert action == rec["action"]
            counts = independently_count(row, action)
            assert counts == rec["counts"]
            for population in ("ALL", rec["condition"]):
                grouped[rec["policy"] + "|" + population][rec["seed"]].update(counts)
            records += 1
    assert records == 640 * 13 and grouped.keys() == result["tables"].keys()
    sample = np.random.Generator(np.random.PCG64(2026111603)).integers(
        0, 128, (4000, 128)
    )
    ratios = {
        "completion": ("success", "rows"),
        "coverage": ("acted", "rows"),
        "conditional_success": ("success", "acted"),
        "required_recovery_recall": ("required_selected", "required"),
        "useful_recoveries_per_R": ("required_selected", "recover"),
        "recovery_per_failed_start": ("required_selected", "initially_unsuccessful"),
        "harm_per_R": ("harm_R", "recover"),
        "futile_per_R": ("futile_R", "recover"),
        "matched_recovery_effect": ("physical_recovery_gain", "recover"),
        "completion_effect_vs_continue": ("completion_minus_continue", "rows"),
    }
    intervals = 0
    for key, parents in grouped.items():
        counts = Counter()
        for row in parents.values():
            counts.update(row)
        assert dict(counts) == result["tables"][key]["counts"]
        ids = sorted(parents)
        assert len(ids) == 128
        for name, (num, den) in ratios.items():
            check_interval(
                [parents[p][num] for p in ids],
                [parents[p][den] for p in ids],
                sample,
                result["tables"][key]["intervals"][name],
            )
            intervals += 1
    mapping = {
        "completion": ("success", "rows"),
        "coverage": ("acted", "rows"),
        "required_recovery_recall": ("required_selected", "required"),
        "harm": ("harm_R", "rows"),
        "futile_recovery_burden": ("futile_R", "rows"),
        "recovery_attempt_rate": ("recover", "rows"),
    }
    for key, reported in result["comparisons"].items():
        pair, population, metric = key.split("|")
        a, b = pair.split("_minus_")
        left, right = grouped[a + "|" + population], grouped[b + "|" + population]
        num, den = mapping[metric]
        ids = sorted(left)
        assert all(left[p][den] == right[p][den] for p in ids)
        check_interval(
            [left[p][num] - right[p][num] for p in ids],
            [left[p][den] for p in ids],
            sample,
            reported,
        )
    for pop, reported in result["paired_outcomes"].items():
        counts = Counter()
        for row in rows:
            if pop != "ALL" and row["condition"] != pop:
                continue
            c, r = row["c"], row["r"]
            counts[
                "BOTH" if c and r else "C_ONLY" if c else "R_ONLY" if r else "NEITHER"
            ] += 1
            counts["rows"] += 1
            counts["initially_unsuccessful"] += not row["initial_success"]
            counts["required"] += not row["initial_success"] and not c and r
        assert dict(counts) == reported
    assert_isolated()
    report = {
        "passed": True,
        "raw_calibration_parents": 256,
        "raw_test_parents": 128,
        "independent_policy_records": records,
        "independent_tables": len(grouped),
        "independent_intervals": intervals,
        "independent_paired_intervals": len(result["comparisons"]),
        "six_calibration_bounds_independently_checked": True,
        "finite_reference_minimum_and_typed_witness_cases": 2
        * (
            len({tuple(r["features"][:7]) for r in calibration})
            + len({tuple(r["features"][:7]) for r in rows})
        ),
        "no_new_minimum_nondegradation_certificate_claimed": True,
        "historical_gate_byte_identity": True,
        "whole_test_cohort_predecision_isolation_verified": True,
        "no_production_selector_or_simulator_imported": True,
        "result_sha256": sha(root / "dual_results.json"),
        "epoch": time.time(),
    }
    write_once(root / "independent_dual_numerical_audit.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    verify(parser.parse_args().root)
