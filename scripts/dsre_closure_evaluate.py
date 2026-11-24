"""E1/E3/E4/E5: offline scoring and source-grounded witness checks only."""

import argparse
import itertools
from collections import Counter

from dsre_closure_common import (
    INPUTS,
    OBLIGATIONS,
    ROOT,
    TASKS,
    calibrated,
    canonical,
    hashed,
    matching_scope,
    metrics,
    output,
    passed,
    paths,
    read,
    route,
    save,
)


def independent_extrema(e):
    """Explicit analytical couplings at fixed marginals, not robot episodes."""
    p0, p1 = e
    low, high = max(0, p0 - p1), min(p0, 1 - p1)

    def world(h):
        return [1 - p1 - h, p1 - p0 + h, h, p0 - h]

    return world(low), world(high)


def select_sample(task, rows, query_table, registration):
    """Select using X/qualification/reason codes; do not inspect certificate text."""
    buckets = {}
    for row in rows:
        result = query_table["useful", tuple(row["x"])]["output"]
        key = (
            "qualified"
            if result["action"] == "r"
            else "+".join(result["withholding"]["reasons"])
        )
        buckets.setdefault(key, []).append(row)
    for bucket in buckets.values():
        bucket.sort(
            key=lambda r: hashed(registration["sample_namespace"], task, r["parent_id"])
        )
    selected = buckets.get("qualified", [])[:24]
    withheld = sorted(k for k in buckets if k != "qualified")
    position = Counter()
    for _ in range(24):
        eligible = [k for k in withheld if position[k] < len(buckets[k])]
        if not eligible:
            break
        key = min(eligible, key=lambda k: (position[k], k))
        selected.append(buckets[key][position[key]])
        position[key] += 1
    return selected, {
        "qualified_requested": 24,
        "qualified_available": len(buckets.get("qualified", [])),
        "qualified_selected": min(24, len(buckets.get("qualified", []))),
        "withheld_requested": 24,
        "withheld_selected": sum(position.values()),
        "withheld_strata": {
            k: {"available": len(buckets[k]), "selected": position[k]} for k in withheld
        },
        "selected_parent_ids": [r["parent_id"] for r in selected],
        "selection_inputs": "Only predecision X, original C bounds and reason codes, then fixed parent hash; no certificate text or test outcome selects cases",
    }


def original_branches(task, row):
    p = paths(task)
    if task == "PushCube-v1":
        candidate = next(
            r
            for r in p["test"].glob("*.json")
            if read(r)["parent_id"] == row["parent_id"]
        )
    else:
        candidate = p["test"] / (row["parent_id"] + ".json")
    record = read(candidate)
    directory = p["physics"] / "test" / str(record["spec"]["index"])
    first, other = (
        ("selected", "evaluator")
        if task == "PushCube-v1"
        else ("selected_policy", "evaluator_counterpart")
    )
    branch_paths = [directory / (label + ".json.gz") for label in (first, other)]
    branches = [read(path) for path in branch_paths]
    assert branches[0]["prefix"] == branches[1]["prefix"]
    assert branches[0]["controller_memory"] == branches[1]["controller_memory"]
    a0 = row["actions"]["DSRE"]
    assert branches[0]["success"] == row["yr" if a0 == "r" else "yc"]
    assert branches[1]["success"] == row["yc" if a0 == "r" else "yr"]
    return record, branch_paths, branches


def mechanisms(task, rows, model, registration):
    ordered = sorted(
        rows, key=lambda r: hashed("DSRE-CLOSURE-E4-PHYSICAL-v1", task, r["parent_id"])
    )
    groups = {}
    for r in ordered:
        groups.setdefault(tuple(r["x"]), {}).setdefault((r["yc"], r["yr"]), r)
    alias = []
    for x, classes in groups.items():
        if (True, False) in classes and (False, True) in classes:
            selected = [classes[True, False], classes[False, True]]
            proof = []
            for r in selected:
                spec, rawpaths, _ = original_branches(task, r)
                proof.append(
                    {
                        "parent_id": r["parent_id"],
                        "spec": spec["spec"],
                        "x": r["x"],
                        "yc": r["yc"],
                        "yr": r["yr"],
                        "native_sources": [str(p) for p in rawpaths],
                    }
                )
            alias.append(
                {
                    "type": "PHYSICAL_OBSERVATION_ALIASING",
                    "x": x,
                    "parents": proof,
                    "scope": "Finite-reference pointwise common-action obstruction, not a regional average-risk impossibility",
                }
            )
    neither = next(r for r in ordered if not r["yc"] and not r["yr"])
    record, rawpaths, _ = original_branches(task, neither)
    repertoire = {
        "type": "PHYSICAL_FIXED_REPERTOIRE_INADEQUACY",
        "parent_id": neither["parent_id"],
        "spec": record["spec"],
        "x": neither["x"],
        "yc": False,
        "yr": False,
        "native_sources": [str(p) for p in rawpaths],
        "scope": "Both executed fixed macros fail this checkpoint and horizon only",
    }
    calibration = paths(task)["calibration"]
    logs = (
        [read(p) for p in sorted(calibration.glob("*.json"))]
        if calibration.is_dir()
        else read(calibration)
    )
    finite = []
    for cell in sorted(set(model["partition"]["cells"])):
        available = sorted(
            [r for r in logs if route(model["partition"], r["x"]) == cell],
            key=lambda r: hashed(
                registration["finite_sample_namespace"], task, r["parent_id"]
            ),
        )
        for n in (8, 16, 32, 64):
            selected = available[:n]
            e = calibrated(selected, [], len(model["leaves"]), cell)
            if all(e["counts"][:2]):
                p0, p1 = [
                    k / n for k, n in zip(e["successes"], e["counts"][:2], strict=True)
                ]
                if (
                    min(p0, 1 - p1) <= 0.1
                    and p1 - p0 >= 0.05
                    and not passed(e["bounds"], "useful")
                ):
                    finite.append(
                        {
                            "type": "PHYSICAL_RECORDED_OUTCOMES_RETROSPECTIVELY_DOWNSAMPLED",
                            "cell": cell,
                            "requested_parent_budget": n,
                            "actual_parents": len(selected),
                            "point_marginals": [p0, p1],
                            "evidence": e,
                            "scope": "Fixed outcome-blind parent-hash subset; plugin adequacy is a diagnostic, not the population truth",
                        }
                    )
    return {
        "observation_ambiguity": alias,
        "repertoire": repertoire,
        "sample_limited_cases": finite,
    }


def sensitivity(task, rows, model, query_table):
    from dual_rec.dsre.features import ObservationHistory, observed_frame
    from dual_rec.dsre.measurement import MeasurementScope, bounded_evidence
    from dual_rec.dsre.measurement_oracle import check_invariance

    native = {r["parent_id"]: original_branches(task, r)[2][0] for r in rows}
    result = []
    for rho in (0.0, 0.005, 0.010):
        known, ambiguous, counts, actions, observations = 0, 0, Counter(), [], []
        oracle_checks = 0
        for row in rows:
            raw = native[row["parent_id"]]
            first, current = raw["prefix"][0], raw["checkpoint"]
            history = ObservationHistory(
                first=observed_frame(first["time"], first["observation"]),
                current=observed_frame(current["time"], current["observation"]),
            )
            evidence = bounded_evidence(
                history,
                MeasurementScope(
                    coordinate_error_m=rho,
                    decision_time=current["time"],
                    reference_scope_identity=task + ":original-primary-C",
                    source_regime="RETROSPECTIVE_DECLARED_ERROR_BOX",
                    clean_risk_scope_eligible=rho == 0,
                ),
            )
            robust = tuple(f.invariant for f in evidence.facts[:6])
            if rho == 0:
                assert list(robust) == row["x"]
            oracle_checks += check_invariance(history, rho, evidence, draws=8)
            known += sum(v is not None for v in robust)
            for i, v in enumerate(robust):
                counts[str(i)] += v is None
            completions = [
                x
                for x in itertools.product((False, True), repeat=6)
                if all(v is None or v == x[i] for i, v in enumerate(robust))
            ]
            cells = {route(model["partition"], x) for x in completions}
            ambiguous += len(cells) > 1
            action = (
                "c"
                if any(v is None for v in robust)
                else query_table["useful", robust]["output"]["action"]
            )
            actions.append(action)
            observations.append(
                {
                    "parent_id": row["parent_id"],
                    "robust_x": robust,
                    "compatible_cells": sorted(cells),
                    "action": action,
                    "source_time": current["time"],
                    "original_calibration_guarantee_transfers": rho == 0,
                }
            )
        result.append(
            {
                "radius_mm": int(rho * 1000),
                "invariant_literals": known,
                "possible_literals": 6 * len(rows),
                "UNKNOWN_by_channel": dict(counts),
                "ambiguous_whole_leaf_memberships": ambiguous,
                "independent_interval_and_invariance_checks": oracle_checks,
                "metrics": metrics(rows, actions),
                "observations": observations,
                "qualification_scope": "Original guarantee only at rho=0; altered-radius consequences are descriptive and require fresh calibration",
            }
        )
    return result


def deletion_proofs(model, certificate, obligation):
    if certificate is None:
        return []
    indices = [
        (model["partition"]["vocabulary"].index(name), value)
        for name, value in certificate["evidence"]
    ]
    proofs = []
    for removed, value in indices:
        reduced = tuple((i, v) for i, v in indices if i != removed)
        scope = matching_scope(model["partition"], reduced)
        bad = (
            []
            if scope is None
            else [
                c
                for c in scope
                if not passed(model["leaves"][str(c)]["bounds"], obligation)
            ]
        )
        assert scope is None or bad
        countermodels = {}
        for cell in bad:
            leaf = model["leaves"][str(cell)]
            b = leaf["bounds"]
            field = (
                "failure_upper"
                if obligation == "completion"
                else "harm_upper"
                if b["harm_upper"] > 0.1 + 1e-12
                else "gain_lower"
            )
            q = b["optimizers"][field]
            violation = (
                q[0] + q[2] > 0.1
                if field == "failure_upper"
                else (q[2] > 0.1 if field == "harm_upper" else q[1] - q[2] < 0.05)
            )
            assert violation
            countermodels[str(cell)] = {
                "violated_bound": field,
                "q": q,
                "type": "ANALYTICAL_CALIBRATION_COMPATIBLE_NOT_ROBOT_EPISODE",
            }
        proofs.append(
            {
                "removed": [model["partition"]["vocabulary"][removed], value],
                "reduced_whole_leaf_scope": scope,
                "forbidden_leaf_split": scope is None,
                "disallowed_calibrated_cells": {
                    str(c): model["leaves"][str(c)] for c in bad
                },
                "constructive_models": countermodels,
                "witness_type": "LOGICAL_SCOPE_OR_CALIBRATION_COMPATIBLE_MODEL; not a fabricated robot episode",
            }
        )
    return proofs


def main(stage="all"):
    registration = read(ROOT / "registration.json")
    frozen = read(ROOT / "E1/calibration_freeze.json")
    original = read(ROOT / "E0/recount/independent_numbers.json")
    policies, baselines, witnesses, noise, selection = {}, {}, {}, {}, {}
    for task in TASKS:
        rows = original["results"][task]["paired_test"]
        data = frozen["tasks"][task]
        model = data["model"]
        table = {(r["obligation"], tuple(r["x"])): r for r in data["queries"]}
        sampled = []
        if stage in ("all", "certificates"):
            selection[task] = read(ROOT / "E3" / (task + "_sample_selection.json"))
            by_parent = {r["parent_id"]: r for r in rows}
            sampled = [by_parent[p] for p in selection[task]["selected_parent_ids"]]
        policy_rows = {}
        for o in OBLIGATIONS:
            selected = [table[o, tuple(r["x"])]["output"] for r in rows]
            cart = [
                "c"
                if not model["proposals"][str(route(model["partition"], r["x"]))][
                    "utility"
                ]
                else s["action"]
                for r, s in zip(rows, selected, strict=True)
            ]
            summary = metrics(rows, [s["action"] for s in selected])
            summary["certificate_lengths"] = dict(
                Counter(
                    len(s["certificate"]["evidence"])
                    for s in selected
                    if s["certificate"]
                )
            )
            summary["policy_scope"] = (
                "Retrospective obligation contrast on the original sealed paired oracle; thresholds and regions unchanged, no refit"
            )
            summary["CART_frozen_gain_prefilter"] = metrics(rows, cart)
            summary["CART_obligation_gate_only"] = metrics(
                rows, [s["action"] for s in selected]
            )
            policy_rows[o] = summary
        policy_rows["always_continue"] = metrics(rows, ["c"] * len(rows))
        policy_rows["always_recover"] = metrics(rows, ["r"] * len(rows))
        policies[task] = policy_rows
        cases = []
        for row in sampled:
            for o in OBLIGATIONS:
                q = table[o, tuple(row["x"])]
                d = q["output"]
                ordinary = q["B7_output"]
                assert canonical(d) == canonical(ordinary)
                direct_action = (
                    "r" if passed(model["leaves"][str(q["leaf"])]["bounds"], o) else "c"
                )
                assert direct_action == ordinary["action"]
                cert = d["certificate"]
                if cert is not None:
                    indices = tuple(
                        (model["partition"]["vocabulary"].index(name), value)
                        for name, value in cert["evidence"]
                    )
                    assert all(row["x"][i] is value for i, value in indices)
                    assert (
                        matching_scope(model["partition"], indices)
                        == cert["selected_leaf_scope"]
                    )
                    assert cert["outcome_scope"] == model["source_scope"]
                    assert all(
                        passed(model["leaves"][str(c)]["bounds"], o)
                        for c in cert["selected_leaf_scope"]
                    )
                # E1 compared independent B7 with production DSRE for ALL cube
                # queries. Here expose complete, identical postprocessed tuples.
                cart = output(
                    model,
                    row["x"],
                    o,
                    d["certificate"],
                    prefilter=not model["proposals"][str(q["leaf"])]["utility"],
                )
                cases.append(
                    {
                        "parent_id": row["parent_id"],
                        "x": row["x"],
                        "obligation": o,
                        "DSRE": d,
                        "B7_same_processor": ordinary,
                        "direct_ID_same_processor": ordinary,
                        "CART_obligation_gate_only_same_processor": ordinary,
                        "CART_frozen_gain_prefilter": cart,
                        "independent_B7_comparison": "Verified by exhaustive ternary library vs production subset search in C-only E1",
                        "DSRE_B7_full_equivalence": True,
                        "DSRE_frozen_CART_full_equivalence": canonical(d)
                        == canonical(cart),
                        "extra_evidence_units": 0,
                        "validity": {
                            "observed_literals": True,
                            "whole_region_scope": True,
                            "source_obligation_bounds": True,
                            "exact_minimum": True,
                            "confidence_support": "Original independently calibrated whole cells",
                            "withheld_is_not_a_certificate": cert is None,
                        },
                        "literal_removal_audit": deletion_proofs(
                            model, d["certificate"], o
                        ),
                    }
                )
        baselines[task] = {
            "cases": cases,
            "sampling": selection.get(task, {}),
            "timing": data["timing"],
            "status": "CERTIFICATE_EQUIVALENCE",
            "note": "Full witness instrumentation is deliberately shared; it is not a unique DSRE invention. Uninstrumented historical baselines originally emitted actions only.",
        }
        if stage in ("all", "mechanisms"):
            witnesses[task] = mechanisms(task, rows, model, registration)
            ablations = {}
            for feature in range(6):
                # Current source protocol refuses any UNKNOWN route, including
                # irrelevant missing channels; this is conservative, not necessity.
                masked_actions = []
                for row in rows:
                    masked = list(row["x"])
                    masked[feature] = None
                    assert route(model["partition"], masked) is None
                    masked_actions.append(
                        output(model, masked, "useful", None)["action"]
                    )
                ablations[f"UNKNOWN_feature_{feature}"] = metrics(rows, masked_actions)
            calibration = paths(task)["calibration"]
            logs = (
                [read(p) for p in sorted(calibration.glob("*.json"))]
                if calibration.is_dir()
                else read(calibration)
            )
            without_r = {
                str(c): calibrated(
                    [
                        r
                        for r in logs
                        if r["action"] == "c" and route(model["partition"], r["x"]) == c
                    ],
                    [],
                    len(model["leaves"]),
                    c,
                )
                for c in sorted(set(model["partition"]["cells"]))
            }
            assert all(
                v["failure"] == "NO_OVERLAP" and v["counts"][1] == 0
                for v in without_r.values()
            )
            ablations["missing_action_evidence"] = metrics(
                rows,
                [
                    "r"
                    if passed(
                        without_r[str(route(model["partition"], r["x"]))]["bounds"],
                        "useful",
                    )
                    else "c"
                    for r in rows
                ],
            )
            witnesses[task]["missing_arm_support_evidence"] = without_r
            naive = []
            for row in rows:
                e = model["leaves"][str(route(model["partition"], row["x"]))][
                    "evidence"
                ]
                naive.append(
                    "r"
                    if e["p0"]["hi"] * (1 - e["p1"]["lo"]) <= 0.1
                    and e["p1"]["lo"] - e["p0"]["hi"] >= 0.05
                    else "c"
                )
            ablations["naive_independence_INVALID_CAUSAL_ASSUMPTION"] = metrics(
                rows, naive
            )
            witnesses[task]["mechanism_ablations"] = ablations
        if stage in ("all", "sensitivity"):
            noise[task] = sensitivity(task, rows, model, table)
        print(
            task,
            {
                o: (v["recover"], v["completion"])
                for o, v in policy_rows.items()
                if o in OBLIGATIONS
            },
            flush=True,
        )
    if stage in ("all", "obligations"):
        save(
            ROOT / "E1/obligation_results.json",
            {"tasks": policies, "input_sha256": INPUTS},
        )
    if stage in ("all", "certificates"):
        save(
            ROOT / "E3/full_certificate_audit.json",
            {
                "tasks": baselines,
                "input_sha256": INPUTS,
                "method_originality": "FUNCTIONAL_EQUIVALENCE_TO_INSTRUMENTED_RULES",
            },
        )
    if stage in ("all", "mechanisms"):
        save(
            ROOT / "E4/physical_witnesses_and_ablations.json",
            {
                "tasks": witnesses,
                "input_sha256": INPUTS,
                "physical_vs_analytical": "All task rows are original sealed physical simulator executions. Mathematical worlds are stored separately in E0/math_audit.json.",
            },
        )
    if stage in ("all", "sensitivity"):
        save(
            ROOT / "E5/observation_error_sensitivity.json",
            {
                "status": "SUPPORTED_DECLARED_BOX_SENSITIVITY_ONLY",
                "tasks": noise,
                "assumptions": "Absolute per-coordinate error in each supporting pose/frame; exact finger encoders; fresh packets. No claim this is a measured physical noise distribution.",
                "input_sha256": INPUTS,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("all", "obligations", "certificates", "mechanisms", "sensitivity"),
        nargs="?",
        default="all",
    )
    main(parser.parse_args().stage)
