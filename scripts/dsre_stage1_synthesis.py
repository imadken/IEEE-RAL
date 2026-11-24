"""Recount sealed DSRE science and export paper facts; never run physics or fit."""

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

import numpy as np

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence
from dual_rec.dsre.repair_oracle import Oracle
from dual_rec.dsre.repair_selection import optional_values

SCIENCE = Path("results/dsre-operational/20261115T195007Z-science-v12")
OLD = Path("results/dsre-operational/20261114T180630Z")
ARMS = ("nominal", "offset001", "offset002", "offset003", "offset_minus002")


def read(path):
    return json.loads(path.read_text())


def gz(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


def lines(path):
    with gzip.open(path, "rt") as f:
        yield from map(json.loads, f)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def mass(rows, n):
    """Independent set intersections, without importing the ceiling routine."""
    groups = defaultdict(list)
    for r in rows:
        groups[tuple((r["features"] + r["optional_features"])[:n])].append(r)
    return sum(
        len(g)
        for g in groups.values()
        if set.intersection(
            *[{a for a, success in r["outcomes"].items() if success} for r in g]
        )
    )


def interval(rows, numerator, denominator):
    """Resample parents, carrying all five conditions together."""
    groups = sorted({r["group"] for r in rows})
    nums = np.array(
        [sum(numerator(r) for r in rows if r["group"] == g) for g in groups],
        dtype=float,
    )
    dens = np.array(
        [sum(denominator(r) for r in rows if r["group"] == g) for g in groups],
        dtype=float,
    )
    draws = np.random.default_rng(2026111504).integers(
        0, len(groups), (4000, len(groups))
    )
    nd, dd = nums[draws].sum(1), dens[draws].sum(1)
    defined = dd > 0
    return {
        "estimate": float(nums.sum() / dens.sum()) if dens.sum() else None,
        "ci95": np.quantile(nd[defined] / dd[defined], [0.025, 0.975]).tolist()
        if defined.any()
        else [None, None],
        "parents": len(groups),
        "numerator": int(nums.sum()),
        "denominator": int(dens.sum()),
    }


def classes(rows):
    c = Counter(
        (r["outcomes"]["continue_value"], r["outcomes"]["recover_value"]) for r in rows
    )
    return [c[True, False], c[False, True], c[True, True], c[False, False]]


def required(r):
    return (
        not r["initial_success"]
        and not r["outcomes"]["continue_value"]
        and r["outcomes"]["recover_value"]
    )


def formal_regression():
    checked = 0
    for outcomes in product(
        ((False, False), (False, True), (True, False), (True, True)), repeat=4
    ):
        rows = [
            {
                "features": [bool(i // 2), bool(i % 2)],
                "optional_features": [],
                "outcomes": dict(
                    zip(("continue_value", "recover_value"), o, strict=True)
                ),
            }
            for i, o in enumerate(outcomes)
        ]
        action = sum(any(r["outcomes"].values()) for r in rows)
        assert 0 <= mass(rows, 1) <= mass(rows, 2) <= action
        for r in rows:
            if not any(r["outcomes"].values()):
                assert mass([r], 2) == 0
        checked += 1
    return {
        "exhaustive_two_action_four_state_tables": checked,
        "scope": "Regression for elementary finite-table propositions, not a replacement for their proofs.",
    }


def main(root):
    extracted = root / "review-extracted"
    all_rows = {r["id"]: r for r in lines(extracted / "data/compact_rows.jsonl.gz")}
    rows = sorted(
        (r for r in all_rows.values() if r["population"] == "new_confirmation"),
        key=lambda r: r["id"],
    )
    assert len(rows) == 640
    assert {r["seed"] for r in rows} == set(range(14000064, 14000192))
    assert all(
        Counter(r["condition"] for r in rows if r["seed"] == s) == Counter(ARMS)
        for s in range(14000064, 14000192)
    )
    by_id = {r["id"]: r for r in rows}
    records = defaultdict(dict)
    direct_checks = 0
    for d in lines(extracted / "data/prospective_decisions.jsonl.gz"):
        if d["id"] not in by_id:
            continue
        r = by_id[d["id"]]
        action = d["action"]
        good = bool(action) and r["outcomes"][action + "_value"]
        assert d["adequate"] == int(good)
        assert d["inadequate"] == int(bool(action) and not good)
        assert d["stop"] == int(action is None)
        assert d["required_total"] == int(required(r))
        assert d["required_selected"] == int(required(r) and action == "recover")
        records[d["scenario"], d["mode"], d["method"]][d["id"]] = d
        direct_checks += 1
    tables = {}
    for key, ds in records.items():
        assert set(ds) == set(by_id)
        tables["|".join(key)] = {
            f: sum(d[f] for d in ds.values())
            for f in (
                "adequate",
                "inadequate",
                "stop",
                "required_selected",
                "harmful_recover",
                "maintenance",
                "literals",
                "false_assertions",
                "noninvariant_assertions",
            )
        }
        if key[2] in ("DSRE_strict", "DSRE_risk"):
            other = "B7" if key[2] == "DSRE_strict" else "B7_risk"
            peer = records[key[0], key[1], other]
            assert all(
                (d["action"], d["evidence"]) == (peer[i]["action"], peer[i]["evidence"])
                for i, d in ds.items()
            )
    published = read(SCIENCE / "prospective_results.json")["tables"]
    for key, v in tables.items():
        p = published["new_confirmation|PickCube-v1|" + key]
        assert all(p[f] == x for f, x in v.items())
    clean = records["clean", "point_proposal", "DSRE_risk"]
    cart = records["clean", "point_proposal", "CART2_beta10"]
    rho5 = records["bound005", "robust_proposal", "DSRE_risk"]
    ci = {
        "required_recall": interval(
            rows, lambda r: clean[r["id"]]["required_selected"], required
        ),
        "cart_required_recall": interval(
            rows, lambda r: cart[r["id"]]["required_selected"], required
        ),
        "rho5_required_recall": interval(
            rows, lambda r: rho5[r["id"]]["required_selected"], required
        ),
        "adequate_dsre_minus_cart": interval(
            rows,
            lambda r: clean[r["id"]]["adequate"] - cart[r["id"]]["adequate"],
            lambda r: 1,
        ),
        "fixed_r_minus_c": interval(
            rows,
            lambda r: (
                int(r["outcomes"]["recover_value"])
                - int(r["outcomes"]["continue_value"])
            ),
            lambda r: 1,
        ),
    }
    for key, scenario, method in (
        ("required_recall", "clean", "DSRE_risk"),
        ("cart_required_recall", "clean", "CART2_beta10"),
        ("rho5_required_recall", "bound005", "DSRE_risk"),
    ):
        mode = "point_proposal" if scenario == "clean" else "robust_proposal"
        target = published[f"new_confirmation|PickCube-v1|{scenario}|{mode}|{method}"][
            "intervals"
        ]["necessary_recovery_recall"]
        assert ci[key]["estimate"] == target["estimate"]
        assert np.allclose(ci[key]["ci95"], [target["lower"], target["upper"]])
    effects = read(SCIENCE / "physical_effects_and_secondary.json")
    witnesses = [
        w
        for w in effects["witness_examples"]
        if w["profile"] == "new_confirmation|point7"
    ]
    physical = []
    for w in witnesses:
        for r in w["rows"]:
            assert feature_values(
                ObservationHistory.model_validate(r["runtime_history"])
            ) == tuple(r["features"])
            p = Path(r["source"])
            assert sha(p) == r["source_sha256"]
            raw = gz(p)
            h = ObservationHistory(
                first=observed_frame(
                    raw["prefix"][0]["time"], raw["prefix"][0]["observation"]
                ),
                current=observed_frame(
                    raw["canonical_start"]["time"],
                    raw["canonical_start"]["observation"],
                ),
            )
            assert h.model_dump(mode="json") == r["runtime_history"]
            futures = {}
            for a in ("continue", "recover"):
                future = gz(p.parent / (a + ".json.gz"))
                assert len(future["frames"]) == 70
                assert (
                    future["terminal_success"]
                    == r["outcomes"][a + "_value"]
                    == future["frames"][-1]["state"]["success"]
                )
                terminal = future["frames"][-1]["state"]
                futures[a] = {
                    "object_position": observed_frame(
                        terminal["time"], terminal["observation"]
                    ).object_position,
                    "success": future["terminal_success"],
                    "sha256": sha(p.parent / (a + ".json.gz")),
                }
            physical.append({"kind": w["kind"], "row": r, "futures": futures})
    assert len(physical) == 3
    old_cases = read(OLD / "physical_examples.json")["cases"]
    historical_conflicts = []
    for case in old_cases[3:5]:
        raw = gz(Path(case["source"]))
        assert sha(Path(case["source"])) == case["source_sha256"]
        start = raw["traces"]["continue/reference"]["start"]
        h = ObservationHistory(
            first=observed_frame(
                raw["prefix"][0]["time"], raw["prefix"][0]["observation"]
            ),
            current=observed_frame(start["time"], start["observation"]),
        )
        assert h.current.model_dump(mode="json") == case["observed"]
        assert list(feature_values(h)) == case["features"]
        assert list(optional_values(h)) == case["optional_features"]
        futures = {}
        for a in ("continue", "recover"):
            tr = raw["traces"][a + "/reference"]
            assert tr["prefix_ok"] and len(tr["frames"]) == 70
            state = tr["frames"][-1]["state"]
            assert state["success"] == case["outcomes"][a + "_value"]
            futures[a] = {
                "success": state["success"],
                "object_position": observed_frame(
                    state["time"], state["observation"]
                ).object_position,
            }
        historical_conflicts.append(
            {"case": case, "history": h.model_dump(mode="json"), "futures": futures}
        )
    assert (
        historical_conflicts[0]["case"]["features"]
        + historical_conflicts[0]["case"]["optional_features"]
        == historical_conflicts[1]["case"]["features"]
        + historical_conflicts[1]["case"]["optional_features"]
    )
    old_case = old_cases[0]
    measurement_example = read(SCIENCE / "constructive_measurement_examples.json")[
        "examples"
    ][0]
    assert (
        sha(Path(measurement_example["source"])) == measurement_example["source_sha256"]
    )
    actual = ObservationHistory.model_validate(measurement_example["actual_history"])
    observed = ObservationHistory.model_validate(
        measurement_example["corrupted_observed_history"]
    )
    error = max(
        abs(a - b)
        for f, g in ((actual.first, observed.first), (actual.current, observed.current))
        for name in ("object_position", "tcp_position", "goal_position")
        for a, b in zip(getattr(f, name), getattr(g, name), strict=True)
    )
    assert error <= 0.005
    bounded = bounded_evidence(
        observed,
        MeasurementScope(
            coordinate_error_m=0.005,
            decision_time=actual.current.time,
            reference_scope_identity="illustration",
            source_regime="historical_development",
        ),
    )
    fact = next(f for f in bounded.facts if f.feature == "object_left_of_goal_02")
    assert fact.measured is False and fact.invariant is None
    true_dx = actual.current.object_position[0] - actual.current.goal_position[0]
    assert true_dx < -0.02
    measurement_detail = {
        "source": measurement_example["source"],
        "source_sha256": measurement_example["source_sha256"],
        "id": measurement_example["id"],
        "true_dx_m": true_dx,
        "observed_dx_m": observed.current.object_position[0]
        - observed.current.goal_position[0],
        "interval_m": [fact.lower, fact.upper],
        "maximum_coordinate_error_m": error,
        "point_certificate": measurement_example["point_certificate"]["evidence"],
        "action_outcomes": measurement_example["actual_paired_outcomes_unchanged"],
    }
    frozen = read(SCIENCE / "frozen_routers.json")["tasks"]["PickCube-v1"]["1"]
    oracle = Oracle(frozen["table"], frozen["parent_groups"])
    x = old_case["features"] + [old_case["optional_features"][0]]
    certificate = oracle.rule({"scope": oracle.table["scope"], "features": x})
    assert certificate["action"] == "recover" and len(certificate["evidence"]) == 3
    names = oracle.table["scope"]["features"]
    indices = [names.index(f["feature"]) for f in certificate["evidence"]]
    removals = []
    for i in indices:
        bad = oracle.match(x, [j for j in indices if j != i]) & oracle.bad["recover"]
        assert bad
        state = min(
            (oracle.rows[j] for j in oracle.indices(bad)), key=lambda z: z["id"]
        )
        removals.append({"removed": names[i], "state": state})
    assert sha(Path(old_case["source"])) == old_case["source_sha256"]
    assert (
        len(
            {
                tuple((r["features"] + r["optional_features"])[:7])
                for r in witnesses[0]["rows"]
            }
        )
        == 1
    )
    output = {
        "passed": True,
        "population": "128 untouched confirmation parents; all five arms; unqualified proposals",
        "parents": 128,
        "checkpoints": 640,
        "classes": classes(rows),
        "per_arm_classes": {
            a: classes([r for r in rows if r["condition"] == a]) for a in ARMS
        },
        "per_arm_required": {
            a: sum(required(r) for r in rows if r["condition"] == a) for a in ARMS
        },
        "required": sum(required(r) for r in rows),
        "action_feasible": sum(any(r["outcomes"].values()) for r in rows),
        "observation_mass": {str(n): mass(rows, n) for n in (6, 7, 12)},
        "tables": tables,
        "intervals": ci,
        "physical_witnesses": physical,
        "historical_conflict_examples": historical_conflicts,
        "measurement_example": measurement_detail,
        "confirmation_failed_start_conflict_pairs_exist": any(
            a["features"] + a["optional_features"][:1]
            == b["features"] + b["optional_features"][:1]
            for a in rows
            if a["outcomes"]["continue_value"] and not a["outcomes"]["recover_value"]
            for b in rows
            if required(b)
        ),
        "minimum_certificate_example": {
            "case": old_case,
            "independent_oracle": certificate,
            "literal_removals": removals,
        },
        "formal_regression": formal_regression(),
        "direct_decision_label_checks": direct_checks,
        "provenance": {
            str(p): sha(p)
            for p in (
                SCIENCE / "prospective_rows.jsonl.gz",
                SCIENCE / "prospective_decisions.jsonl.gz",
                SCIENCE / "frozen_routers.json",
                SCIENCE / "physical_effects_and_secondary.json",
            )
        },
    }
    write(root / "scientific_consolidation.json", output)
    exports(output, root)
    print(
        json.dumps(
            {
                "passed": True,
                "direct_decision_label_checks": direct_checks,
                "classes": output["classes"],
                "required": output["required"],
                "physical_witness_states": len(physical),
            }
        ),
        flush=True,
    )


def exports(data, root):
    macros, ledger = [], {}

    def add(name, value, source):
        macros.append("\\newcommand{\\" + name + "}{" + str(value) + "}")
        ledger[name] = {
            "value": value,
            "source": "scientific_consolidation.json",
            "field": source,
        }

    add("StudyParents", data["parents"], "parents")
    add("StudyStates", data["checkpoints"], "checkpoints")
    add("StudyRequired", data["required"], "required")
    add("ActionMass", data["action_feasible"], "action_feasible")
    for n in (6, 7, 12):
        add(
            {6: "SixMass", 7: "SevenMass", 12: "TwelveMass"}[n],
            data["observation_mass"][str(n)],
            "observation_mass." + str(n),
        )
    for name, key in (
        ("Recall", "required_recall"),
        ("CartRecall", "cart_required_recall"),
        ("RobustRecall", "rho5_required_recall"),
        ("CartEffect", "adequate_dsre_minus_cart"),
        ("PhysicalEffect", "fixed_r_minus_c"),
    ):
        v = data["intervals"][key]
        add(
            name + "Percent",
            f"{100 * v['estimate']:.2f}",
            "intervals." + key + ".estimate",
        )
        add(
            name + "CI",
            f"[{100 * v['ci95'][0]:.2f},{100 * v['ci95'][1]:.2f}]",
            "intervals." + key + ".ci95",
        )
    add(
        "CleanRecoveryBound",
        f"{100 * (1 - (0.05 / 68) ** (1 / 112)):.3f}",
        "Clopper-Pearson zero-error .05/68, n=112; previous clean calibration only",
    )
    ex = data["measurement_example"]
    add(
        "ExampleTrueDx",
        f"{1000 * ex['true_dx_m']:.2f}",
        "measurement_example.true_dx_m",
    )
    add(
        "ExampleObservedDx",
        f"{1000 * ex['observed_dx_m']:.2f}",
        "measurement_example.observed_dx_m",
    )
    add(
        "ExampleInterval",
        f"[{1000 * ex['interval_m'][0]:.2f},{1000 * ex['interval_m'][1]:.2f}]",
        "measurement_example.interval_m",
    )
    for name, method in (
        ("PointMeanLength", "DSRE_risk"),
        ("CartMeanLength", "CART2_beta10"),
    ):
        key = "clean|point_proposal|" + method
        t = data["tables"][key]
        add(
            name,
            f"{t['literals'] / (t['adequate'] + t['inadequate']):.2f}",
            "tables." + key + ".literals / selected",
        )
    outcome = [
        r"\begin{tabular}{lrrrrr}\toprule",
        r"Offset & C only & R only & Both & Neither & Required R\\\midrule",
    ]
    for a, label in zip(ARMS, ("0", "+1 cm", "+2 cm", "+3 cm", "$-2$ cm"), strict=True):
        cs = data["per_arm_classes"][a]
        req = data["per_arm_required"][a]
        outcome.append(label + " & " + " & ".join(map(str, cs + [req])) + r"\\")
    outcome += [
        "All & "
        + " & ".join(map(str, data["classes"] + [data["required"]]))
        + r"\\\bottomrule\end{tabular}"
    ]
    (Path("rss2027") / "stage1_synthesis_outcomes.tex").write_text(
        "\n".join(outcome) + "\n"
    )
    table = [
        r"\begin{tabular}{llrrrr}\toprule",
        r"$\rho$ & Proposal & Good & Bad & STOP & Req. R\\\midrule",
    ]
    settings = [
        ("0", "clean", "point_proposal", m, label)
        for m, label in (
            ("DSRE_strict", "Strict DSRE/B7"),
            ("DSRE_risk", "Risk DSRE/B7"),
            ("CART2_beta10", "CART2 risk"),
            ("B1_two_strict", "Pure two-literal"),
            ("B0_continue", "Fixed C"),
            ("B0_recover", "Fixed R"),
        )
    ]
    settings += [
        ("5 mm", "bound005", "robust_proposal", m, label)
        for m, label in (
            ("DSRE_strict", "Strict DSRE/B7"),
            ("DSRE_risk", "Risk DSRE/B7"),
            ("CART2_beta10", "CART2 risk"),
        )
    ]
    settings += [
        (
            "5 mm",
            "bound005",
            "margin_all_inputs",
            "margin_DSRE_strict",
            "All-input margin",
        )
    ]
    for rho, scenario, mode, method, label in settings:
        key = f"{scenario}|{mode}|{method}"
        t = data["tables"][key]
        table.append(
            rho
            + " & "
            + label
            + " & "
            + " & ".join(
                str(t[k])
                for k in ("adequate", "inadequate", "stop", "required_selected")
            )
            + r"\\"
        )
        ledger["table:" + key] = {
            "source": "scientific_consolidation.json",
            "field": "tables." + key,
            "value": t,
        }
    table += [r"\bottomrule\end{tabular}"]
    Path("rss2027/stage1_synthesis_decisions.tex").write_text("\n".join(table) + "\n")
    Path("rss2027/stage1_synthesis_numbers.tex").write_text(
        "% Generated from independently recounted sealed evidence.\n"
        + "\n".join(macros)
        + "\n"
    )
    ledger["outcome_table"] = {
        "source": "scientific_consolidation.json",
        "fields": ["per_arm_classes", "classes", "required"],
        "definition": "C/R terminal success; required excludes initially successful preventive case",
    }
    write(root / "claim_source_ledger.json", ledger)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    main(parser.parse_args().root)
