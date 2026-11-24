"""Source-blind paired-outcome adjudication; no selector or report imports."""

import argparse
import gzip
import hashlib
import json
import sys
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_source_risk_audit import audit_cell, predicates
from dsre_source_risk_terminal_audit import terminal_success


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def gz(path):
    with gzip.open(path, "rt") as stream:
        return json.load(stream)


def write_once(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def outcome_class(c, r):
    if type(c) is not bool or type(r) is not bool:
        raise ValueError("Paired labels must be actual binary terminal flags")
    return "BOTH" if c and r else "C_ONLY" if c else "R_ONLY" if r else "NEITHER"


def assert_isolated():
    assert not any(
        name in sys.modules
        for name in (
            "dual_rec.dsre.operational",
            "dual_rec.dsre.solver",
            "sapien",
            "mani_skill",
            "dsre_source_risk_report",
        )
    )


def raw_rows(root, stage, physical=False):
    plan = read(root / "study_plan.json")
    rows, counts, sources = [], Counter(), {}
    for seed in plan[stage + "_seeds"]:
        directory = root / stage / str(seed)
        decision = read(directory / "decision.json")
        assert decision["seed"] == seed
        assert decision["source_freeze_sha256"] == sha(root / "source_freeze.json")
        for condition, offset in plan["profiles"]:
            cell = directory / condition
            raw = gz(cell / "screen.json.gz")
            assert decision["screens"][condition] == sha(cell / "screen.json.gz")
            assert raw["cell"]["seed"] == seed and raw["cell"]["condition"] == condition
            assert raw["offset_x_m"] == offset
            initial = terminal_success(raw["canonical_start"])
            assert (
                initial
                == raw["summary"]["initial_success"]
                == raw["canonical_start"]["success"]
            )
            primary, optional = predicates(
                raw["prefix"][0]["observation"], raw["canonical_start"]["observation"]
            )
            assert (
                primary == raw["summary"]["features"]
                and optional == raw["summary"]["optional_features"]
            )
            actions = {}
            for action in ("continue", "recover"):
                path = cell / (action + ".json.gz")
                branch = gz(path)
                actual = terminal_success(branch["frames"][-1]["state"])
                assert (
                    actual
                    == branch["terminal_success"]
                    == branch["frames"][-1]["state"]["success"]
                )
                assert decision["sealed_epoch"] < branch["completed_epoch"]
                actions[action] = actual
                sources[str(path)] = sha(path)
            if physical:
                part, flags = audit_cell(raw, cell)
                counts.update(part)
                assert flags == {a + "_value": v for a, v in actions.items()}
            proposals = {
                m: d["action"]
                for m, d in raw["scenarios"]["clean"]["point_proposal"].items()
            }
            assert proposals["DSRE_risk"] == proposals["B7_risk"]
            assert proposals["DSRE_strict"] == proposals["B7"]
            sources[str(cell / "screen.json.gz")] = sha(cell / "screen.json.gz")
            rows.append(
                {
                    "seed": seed,
                    "condition": condition,
                    "initial_success": initial,
                    "c": actions["continue"],
                    "r": actions["recover"],
                    "features": primary + optional,
                    "proposals": proposals,
                    "source": str(cell / "screen.json.gz"),
                    "source_sha256": sha(cell / "screen.json.gz"),
                    "decision_sha256": sha(directory / "decision.json"),
                }
            )
    assert len(rows) == 5 * len(plan[stage + "_seeds"])
    assert_isolated()
    return rows, dict(counts), sources


def interval(numerators, denominators, sample):
    nums, dens = np.asarray(numerators), np.asarray(denominators)
    n, d = nums[sample].sum(axis=1), dens[sample].sum(axis=1)
    valid = d > 0
    lo, hi = (
        np.quantile(n[valid] / d[valid], [0.025, 0.975])
        if valid.any()
        else (None, None)
    )
    return {
        "estimate": float(nums.sum() / dens.sum()) if dens.sum() else None,
        "lower": None if lo is None else float(lo),
        "upper": None if hi is None else float(hi),
        "defined_draws": int(valid.sum()),
    }


def summarize(rows, method):
    groups = defaultdict(list)
    cells, conditions, initial = Counter(), defaultdict(Counter), Counter()
    for row in rows:
        groups[row["seed"]].append(row)
        action = (
            method.removeprefix("B0_")
            if method.startswith("B0_")
            else row["proposals"][method]
        )
        if action != "recover":
            continue
        name = outcome_class(row["c"], row["r"])
        cells[name] += 1
        conditions[row["condition"]][name] += 1
        if name == "R_ONLY":
            initial["required" if not row["initial_success"] else "preventive"] += 1
    records = []
    for seed in sorted(groups):
        selected = [
            r
            for r in groups[seed]
            if (
                method == "B0_recover"
                or (
                    not method.startswith("B0_") and r["proposals"][method] == "recover"
                )
            )
        ]
        fail = sum(not r["r"] for r in selected)
        harm = sum(r["c"] and not r["r"] for r in selected)
        gain = sum(int(r["r"]) - int(r["c"]) for r in selected)
        records.append(
            [bool(selected), bool(fail), bool(harm), len(selected), fail, harm, gain]
        )
    data = np.asarray(records, dtype=int)
    sample = np.random.Generator(np.random.PCG64(2026111603)).integers(
        0, len(data), (4000, len(data))
    )
    return {
        "classes": dict(cells),
        "proposed_recover_cells": sum(cells.values()),
        "assigned_parents": int(data[:, 0].sum()),
        "absolute_error_parents": int(data[:, 1].sum()),
        "harm_error_parents": int(data[:, 2].sum()),
        "initial_failure_rescues": initial["required"],
        "preventive_recoveries": initial["preventive"],
        "by_condition": {k: dict(v) for k, v in conditions.items()},
        "intervals": {
            "parent_absolute_failure": interval(data[:, 1], data[:, 0], sample),
            "parent_harm": interval(data[:, 2], data[:, 0], sample),
            "parent_failure_minus_harm": interval(
                data[:, 1] - data[:, 2], data[:, 0], sample
            ),
            "cell_absolute_failure": interval(data[:, 4], data[:, 3], sample),
            "cell_harm": interval(data[:, 5], data[:, 3], sample),
            "cell_failure_minus_harm": interval(
                data[:, 4] - data[:, 5], data[:, 3], sample
            ),
            "matched_recovery_gain": interval(data[:, 6], data[:, 3], sample),
        },
        "bootstrap": "4000 PCG64 seed2026111603, independent parent unit; cohorts never pooled",
    }


def partition(rows, width):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple(row["features"][:width])].append(row)
    counts = Counter(
        rows=len(rows),
        signature_classes=len(buckets),
        common_action_signature_mass=0,
        physically_infeasible_rows=0,
        action_feasible_rows=0,
        feasible_rows_in_signatures_containing_infeasible_reference=0,
        pure_observational_ambiguity_mass=0,
    )
    for group in buckets.values():
        classes = [outcome_class(r["c"], r["r"]) for r in group]
        infeasible = classes.count("NEITHER")
        counts["physically_infeasible_rows"] += infeasible
        counts["action_feasible_rows"] += len(group) - infeasible
        if all(r["c"] for r in group) or all(r["r"] for r in group):
            counts["common_action_signature_mass"] += len(group)
        if infeasible:
            counts["feasible_rows_in_signatures_containing_infeasible_reference"] += (
                len(group) - infeasible
            )
        elif "C_ONLY" in classes and "R_ONLY" in classes:
            counts["pure_observational_ambiguity_mass"] += len(group)
    return dict(counts)


def replicate(root, prior):
    packet = root / "prior_packet"
    if not packet.exists():
        packet.mkdir()
        with tarfile.open(
            "docs/dsre_runtime_source_risk_review.tar.gz", "r:gz"
        ) as archive:
            archive.extractall(packet, filter="data")
    manifest = read(packet / "packet_manifest.json")
    for name, expected in manifest["files"].items():
        assert sha(packet / name) == expected, name
    previous = read(prior / "completion_manifest.json")
    assert (
        sha(prior / "completion_manifest.json")
        == read(root / "initial.json")["prior_completion_manifest_sha256"]
    )
    for name, fields in previous["files"].items():
        assert sha(prior / name) == fields["sha256"], name
    reports, witnesses = {}, {}
    for stage in ("calibration", "test"):
        rows, _, sources = raw_rows(prior, stage)
        old_audit = read(prior / (stage + "_physics_audit.json"))
        assert old_audit["passed"] and old_audit["complete_cohort"]
        assert sources == old_audit["source_file_sha256"]
        with gzip.open(packet / (stage + "_parent_labels.jsonl.gz"), "rt") as stream:
            parents = [json.loads(line) for line in stream]
        compact = {(p["seed"], c["condition"]): c for p in parents for c in p["cells"]}
        assert len(compact) == len(rows)
        for row in rows:
            cell = compact[row["seed"], row["condition"]]
            assert cell["initial_success"] == row["initial_success"]
            assert cell["outcomes"] == {
                "continue_value": row["c"],
                "recover_value": row["r"],
            }
            assert cell["proposals"] == row["proposals"]
            category = outcome_class(row["c"], row["r"])
            if (
                stage == "test"
                and category in ("R_ONLY", "NEITHER", "C_ONLY")
                and category not in witnesses
                and (category == "C_ONLY" or row["proposals"]["DSRE_risk"] == "recover")
            ):
                witnesses[category] = row
        report = summarize(rows, "DSRE_risk")
        expected = (
            {"R_ONLY": 90, "NEITHER": 10, "C_ONLY": 0, "BOTH": 1}
            if stage == "calibration"
            else {"R_ONLY": 40, "NEITHER": 10, "C_ONLY": 0, "BOTH": 0}
        )
        assert all(report["classes"].get(k, 0) == v for k, v in expected.items()), (
            report
        )
        assert report["assigned_parents"] == (66 if stage == "calibration" else 32)
        if stage == "calibration":
            assert report["by_condition"]["offset_minus002"].get("NEITHER") == 10
        assert report["harm_error_parents"] == 0
        for row in rows:
            assert row["proposals"]["DSRE_risk"] == row["proposals"]["B7_risk"]
        reports[stage] = {
            "DSRE": report,
            "CART2": summarize(rows, "CART2_beta10"),
            "fixed_recover": summarize(rows, "B0_recover"),
            "partitions": {str(width): partition(rows, width) for width in (7, 12)},
            "rows": len(rows),
            "parents": len(parents),
        }
    assert set(witnesses) == {"R_ONLY", "NEITHER", "C_ONLY"}
    settings = read(prior / "frozen_routers.json")["tasks"]["PickCube-v1"]["1"]
    reference = {}
    for key, width in (("table", 7), ("full_table", 12)):
        rows = [
            {
                "features": r["features"],
                "c": r["outcomes"]["continue_value"],
                "r": r["outcomes"]["recover_value"],
            }
            for r in settings[key]["rows"]
        ]
        reference[str(width)] = partition(rows, width)
    assert_isolated()
    result = {
        "passed": True,
        "old_results_exploratory_only": True,
        "reports": reports,
        "frozen_reference": reference,
        "witnesses": witnesses,
        "old_zero_harm_66_parent_bound_at_original_delta": 1 - (0.05 / 68) ** (1 / 66),
        "prior_manifest_members_verified": len(previous["files"]),
        "packet_members_verified": len(manifest["files"]),
        "production_selector_imported": False,
        "epoch": time.time(),
    }
    write_once(root / "prior_replication.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "calibration": reports["calibration"]["DSRE"],
                "test": reports["test"]["DSRE"],
            }
        )
    )


def audit_fresh(root, stage):
    from dsre_source_risk_oracle import RouteAudit

    plan = read(root / "study_plan.json")
    prefix = "test_outcome" if stage == "test" else stage
    progress = [read(p) for p in sorted((root / "progress").glob(prefix + "-*.json"))]
    expected = plan[stage + "_seeds"]
    assert len(progress) == len(expected) and all(
        p["status"] == "COMPLETE" for p in progress
    )
    assert [p["seed"] for p in progress] == expected
    rows, counts, sources = raw_rows(root, stage, physical=True)
    oracle = RouteAudit(read(root / "frozen_routers.json"))
    checked = 0
    for row in rows:
        for method in ("DSRE_risk", "B7_risk", "CART2_beta10"):
            # Exactly seven observable facts, never condition, seed or labels.
            expected_action = oracle.expected(
                "PickCube-v1", row["features"][:7], method, False
            )
            assert row["proposals"][method] == expected_action
            checked += 1
        if stage == "test":
            directory = root / "test" / str(row["seed"])
            seal = read(root / "dual_test_seal.json")
            assert (
                sha(directory / "dual_decision.json")
                == seal["parents"][str(row["seed"])]
            )
            assert seal["epoch"] <= read(directory / "execution_started.json")["epoch"]
            assert seal["original_test_seal_sha256"] == sha(
                root / "test_recommendation_seal.json"
            )
    by_parent = defaultdict(list)
    for row in rows:
        by_parent[row["seed"]].append(
            {
                "condition": row["condition"],
                "initial_success": row["initial_success"],
                "outcomes": {"continue_value": row["c"], "recover_value": row["r"]},
                "proposals": row["proposals"],
            }
        )
    for seed, cells in by_parent.items():
        write_once(
            root / stage / str(seed) / "outcome_labels.json",
            {
                "seed": seed,
                "cells": cells,
                "decision_sha256": sha(root / stage / str(seed) / "decision.json"),
            },
        )
    with gzip.open(root / (stage + "_rows.json.gz"), "wt") as stream:
        json.dump(rows, stream)
    result = {
        "passed": True,
        "parents": len(expected),
        "registered_parents": len(expected),
        "complete_cohort": True,
        "counts": counts,
        "source_file_sha256": sources,
        "terminal_labels_independently_recomputed": 2 * len(rows),
        "initial_flags_independently_recomputed": len(rows),
        "independent_route_actions": checked,
        "no_condition_or_future_inputs_in_route_reconstruction": True,
        "no_extra_calibration_claims": True,
        "epoch": time.time(),
    }
    write_once(root / (stage + "_physics_audit.json"), result)
    assert_isolated()
    print(json.dumps({k: v for k, v in result.items() if k != "source_file_sha256"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("prior", type=Path, nargs="?")
    parser.add_argument("--stage", choices=("calibration", "test"))
    args = parser.parse_args()
    try:
        if args.stage:
            audit_fresh(args.root, args.stage)
        else:
            replicate(args.root, args.prior)
    except Exception as error:
        write_once(
            args.root
            / (
                (args.stage + "_audit_failure.json")
                if args.stage
                else "prior_replication_failure.json"
            ),
            {"error": str(error), "epoch": time.time()},
        )
        raise
