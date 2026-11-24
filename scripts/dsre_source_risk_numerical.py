"""Independent raw-decision/outcome recount and direct-index bootstrap audit.

Does not import the production selector, policy scorer or simulator.
"""

import argparse
import gzip
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_source_risk_audit import gz, predicates, read, sha
from dsre_source_risk_oracle import Oracle, RouteAudit, verify_minimum
from scipy.stats import beta


def isolated_imports():
    forbidden = (
        "dual_rec.dsre.operational",
        "dual_rec.dsre.solver",
        "dual_rec.dsre.measurement",
        "sapien",
        "mani_skill",
    )
    assert not any(name in sys.modules for name in forbidden)
    return {
        "production_selector_or_simulator_imported": False,
        "checked_modules": forbidden,
    }


def audit_routes(root):
    frozen = read(root / "frozen_routers.json")
    routing = RouteAudit(frozen)
    settings = frozen["tasks"]["PickCube-v1"]["1"]
    oracle = Oracle(settings["table"], settings["parent_groups"])
    cases, routes, minimum, unsupported = set(), 0, 0, Counter()
    earliest = read(root / "source_qualification_seal.json")["qualified_epoch"]
    for stage in ("calibration", "test"):
        prefix = "test_outcome" if stage == "test" else stage
        for path in sorted((root / "progress").glob(prefix + "-*.json")):
            progress = read(path)
            if progress["status"] != "COMPLETE":
                continue
            directory = root / stage / str(progress["seed"])
            decision = read(directory / "decision.json")
            assert sha(directory / "decision.json") == progress["decision_sha256"]
            for condition, _ in read(root / "study_plan.json")["profiles"]:
                source = directory / condition / "screen.json.gz"
                raw = gz(source)
                assert sha(source) == decision["screens"][condition]
                assert earliest <= raw["screened_epoch"] <= decision["sealed_epoch"]
                primary, optional = predicates(
                    raw["prefix"][0]["observation"],
                    raw["canonical_start"]["observation"],
                )
                assert (
                    primary == raw["summary"]["features"]
                    and optional == raw["summary"]["optional_features"]
                )
                for action in ("continue", "recover"):
                    branch = gz(source.parent / (action + ".json.gz"))
                    assert decision["sealed_epoch"] <= branch["completed_epoch"]
                    assert (
                        branch["terminal_success"]
                        == branch["frames"][-1]["state"]["success"]
                    )
                for data in raw["scenarios"].values():
                    for mode, kind in (
                        ("point_proposal", "measured"),
                        ("robust_proposal", "invariant"),
                    ):
                        values = [f[kind] for f in data["measurement"]["facts"]][:7]
                        for method, actual in data[mode].items():
                            expected = routing.expected(
                                "PickCube-v1", values, method, mode == "robust_proposal"
                            )
                            if expected == "UNASSESSED":
                                unsupported[method] += 1
                            else:
                                assert actual["action"] == expected, (
                                    progress["seed"],
                                    condition,
                                    method,
                                )
                                routes += 1
                        case = tuple(values)
                        if case not in cases:
                            verify_minimum(oracle, values, data[mode]["DSRE_strict"])
                            verify_minimum(
                                oracle, values, data[mode]["DSRE_risk"], True
                            )
                            minimum += 2
                            cases.add(case)
    return {
        "independent_route_actions": routes,
        "minimum_certificate_and_typed_witness_cases": minimum,
        "methods_with_counts_but_without_independent_route_reimplementation": dict(
            unsupported
        ),
    }


def recount(root):
    result = read(root / "test_analysis.json")
    rows = {}
    with gzip.open(root / "test_rows.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            rows[row["id"]] = row
    tables = defaultdict(lambda: defaultdict(Counter))
    action_errors = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    record_count, current_id, raw = 0, None, None
    cal = read(root / "calibration_decision.json")["strata"]
    with gzip.open(root / "test_metric_records.jsonl.gz", "rt") as stream:
        for line in stream:
            rec = json.loads(line)
            row = rows[rec["id"]]
            if current_id != rec["id"]:
                raw = gz(Path(row["source"]))
                assert sha(Path(row["source"])) == row["source_sha256"]
                for action in ("continue", "recover"):
                    branch = gz(Path(row["source"]).parent / (action + ".json.gz"))
                    assert (
                        row["outcomes"][action + "_value"]
                        == branch["frames"][-1]["state"]["success"]
                    )
                current_id = rec["id"]
            scenario, mode, method = (rec[k] for k in ("scenario", "mode", "method"))
            data = raw["scenarios"][scenario]
            proposed = data[
                "robust_proposal" if mode == "robust_proposal" else "point_proposal"
            ][method]
            action = proposed["action"]
            if (
                mode == "gated"
                and action is not None
                and not cal[method + "|" + action]["enabled"]
            ):
                action = None
            assert rec["action"] == action
            count = Counter(dict.fromkeys(rec["counts"], 0))
            count["rows"] = 1
            c, r = (row["outcomes"][a + "_value"] for a in ("continue", "recover"))
            if not row["initial_success"]:
                count["initially_unsuccessful"] = 1
            if c and r:
                count["both_success_total"] = 1
            elif not c and r:
                count["recover_only_total"] = 1
                if not row["initial_success"]:
                    count["required_total"] = 1
            elif not c and not r:
                count["neither_total"] = 1
            if action is None:
                count["stop"] = 1
                count["neither_deferred"] = count["neither_total"]
            else:
                count["acted"] = count[action] = 1
                adequate = row["outcomes"][action + "_value"]
                count["adequate" if adequate else "inadequate"] = 1
                count["both_success_maintained"] = int(c and r)
                count["initial_success_maintained"] = int(
                    row["initial_success"] and adequate
                )
                if action == "recover":
                    count["required_selected"] = count["required_total"]
                    count["recover_only_selected"] = count["recover_only_total"]
                    count["harmful_recover"] = int(c and not r)
                    count["matched_recovery_gain"] = int(r) - int(c)
                evidence = proposed.get("evidence", [])
                count["literals"] = len(evidence)
                names = [
                    f["feature"]
                    for f in raw["scenarios"]["clean"]["measurement"]["facts"]
                ]
                truth = dict(
                    zip(names, row["features"] + row["optional_features"], strict=True)
                )
                sensor = {
                    f["feature"]: f[
                        "invariant" if mode == "robust_proposal" else "measured"
                    ]
                    for f in data["measurement"]["facts"]
                }
                count["false_assertions"] = sum(
                    truth[f["feature"]] != f["value"] for f in evidence
                )
                count["noninvariant_assertions"] = sum(
                    sensor[f["feature"]] != f["value"] for f in evidence
                )
                if scenario == "clean":
                    action_errors[mode][method + "|" + action][row["group"]].append(
                        not adequate
                    )
            assert dict(count) == rec["counts"], (rec["id"], method, mode, scenario)
            base = f"{scenario}|{mode}|{method}"
            keys = [base + "|ALL"] + (
                [base + "|" + row["condition"]] if scenario == "clean" else []
            )
            for key in keys:
                tables[key][row["group"]].update(count)
            record_count += 1
    assert tables.keys() == result["tables"].keys()
    for key, parents in tables.items():
        total = Counter()
        for values in parents.values():
            total.update(values)
        assert {k: v for k, v in total.items() if v} == {
            k: v for k, v in result["tables"][key]["counts"].items() if v
        }
    for mode, strata in result["test_parent_action_bounds"].items():
        for key, row in strata.items():
            parent_errors = action_errors[mode][key]
            n = len(parent_errors)
            k = sum(any(v) for v in parent_errors.values())
            assert (row["assigned_parents"], row["error_parents"]) == (n, k)
            independent_upper = (
                float(beta.ppf(1 - 0.05 / 68, k + 1, n - k)) if n and k < n else 1.0
            )
            assert abs(row["upper"] - independent_upper) < 1e-12
    return tables, record_count, list(rows.values())


def intervals(root, tables, rows):
    result = read(root / "test_analysis.json")
    categories = defaultdict(Counter)
    for row in rows:
        c, r = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
        category = (
            "both_success"
            if c and r
            else "continue_only"
            if c
            else "recover_only"
            if r
            else "neither_success"
        )
        for condition in ("ALL", row["condition"]):
            categories[condition][category] += 1
            categories[condition]["rows"] += 1
            categories[condition]["initially_unsuccessful"] += int(
                not row["initial_success"]
            )
            categories[condition]["required_recovery"] += int(
                not row["initial_success"] and not c and r
            )
    assert categories.keys() == result["paired_outcome_categories"].keys()
    for condition, counts in categories.items():
        assert {k: v for k, v in counts.items() if v} == {
            k: v for k, v in result["paired_outcome_categories"][condition].items() if v
        }
    draws, checked = {}, 0
    for key, parents in tables.items():
        ids = sorted(parents)
        n = len(ids)
        if n not in draws:
            draws[n] = np.random.Generator(np.random.PCG64(2026111602)).integers(
                0, n, (4000, n)
            )
        assert result["tables"][key]["parents"] == n
        sample = draws[n]
        for name, numerator, denominator in (
            ("unconditional_completion", "adequate", "rows"),
            ("coverage", "acted", "rows"),
            ("unconditional_inadequacy", "inadequate", "rows"),
            ("abstention", "stop", "rows"),
            ("conditional_success", "adequate", "acted"),
            ("required_recovery_recall", "required_selected", "required_total"),
            ("recover_only_recall", "recover_only_selected", "recover_only_total"),
            ("matched_recovery_effect", "matched_recovery_gain", "recover"),
        ):
            nums = np.asarray([parents[g][numerator] for g in ids], dtype=float)
            dens = np.asarray([parents[g][denominator] for g in ids], dtype=float)
            num, den = nums[sample].sum(axis=1), dens[sample].sum(axis=1)
            valid = den > 0
            reported = result["tables"][key]["intervals"][name]
            expected = (
                np.quantile(num[valid] / den[valid], [0.025, 0.975]).tolist()
                if valid.any()
                else [None, None]
            )
            assert reported["estimate"] == (
                float(nums.sum() / dens.sum()) if dens.sum() else None
            )
            assert reported["defined_bootstrap_draws"] == int(valid.sum())
            assert all(
                a == b or (a is not None and b is not None and abs(a - b) < 1e-12)
                for a, b in zip(
                    expected, [reported["lower"], reported["upper"]], strict=True
                )
            ), (key, name)
            checked += 1
    paired_checks = 0
    for key, reported in result["paired_contrasts"].items():
        left, condition, name = key.split("|")
        other = left.removeprefix("DSRE_risk_minus_")
        a, b = (
            tables["clean|gated|DSRE_risk|" + condition],
            tables["clean|gated|" + other + "|" + condition],
        )
        ids = sorted(a)
        field = {
            "completion": "adequate",
            "coverage": "acted",
            "inadequacy": "inadequate",
            "required_recovery_recall": "required_selected",
        }[name]
        denominator = "required_total" if name == "required_recovery_recall" else "rows"
        nums = np.asarray([a[g][field] - b[g][field] for g in ids], dtype=float)
        dens = np.asarray([a[g][denominator] for g in ids], dtype=float)
        sample = draws[len(ids)]
        den, num = dens[sample].sum(axis=1), nums[sample].sum(axis=1)
        valid = den > 0
        expected = (
            np.quantile(num[valid] / den[valid], [0.025, 0.975]).tolist()
            if valid.any()
            else [None, None]
        )
        assert reported["numerator"] == int(nums.sum()) and reported[
            "denominator"
        ] == int(dens.sum())
        assert all(
            a == b or (a is not None and b is not None and abs(a - b) < 1e-12)
            for a, b in zip(
                expected, [reported["lower"], reported["upper"]], strict=True
            )
        )
        paired_checks += 1
    return {
        "independent_direct_index_intervals": checked,
        "independent_paired_intervals": paired_checks,
    }


def run(root):
    imports = isolated_imports()
    routing = audit_routes(root)
    tables, records, rows = recount(root)
    numeric = intervals(root, tables, rows)
    result = read(root / "test_analysis.json")
    for n, profile in result["hindsight"].items():
        n = int(n)
        signatures = [(r["features"] + r["optional_features"])[:n] for r in rows]
        mass = sum(
            any(
                all(
                    r["outcomes"][action + "_value"]
                    for j, r in enumerate(rows)
                    if signatures[j] == signature
                )
                for action in ("continue", "recover")
            )
            for signature in signatures
        )
        assert profile["common_action_signature_mass"] == mass
        assert profile["action_mass"] == sum(
            bool(r["outcomes"]["continue_value"] or r["outcomes"]["recover_value"])
            for r in rows
        )
    isolated_imports()
    report = {
        "passed": True,
        "metric_records_independently_rebuilt_from_raw": records,
        "all_table_counts_recounted": len(tables),
        **numeric,
        **routing,
        **imports,
        "analysis_sha256": sha(root / "test_analysis.json"),
        "audit_source_sha256": sha(Path(__file__)),
        "epoch": time.time(),
    }
    (root / "independent_numerical_audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)
