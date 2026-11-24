"""Independent final audit: raw physics, binomial inversion, LP and minimum scope.

No production inference/collector/simulator imports are permitted in this process.
"""

import argparse
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_evidence_lossless import read as trace_read
from dsre_evidence_statistical_audit import cp
from dsre_last_common import ROOT, read, save, sha
from dsre_last_physical import native_abort, parity, peg, push


def load_oracle():
    path = Path("research/dsre_evidence_design/supervisor_reference.py")
    spec = importlib.util.spec_from_file_location("final_independent_oracle", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def leaf(partition, x):
    return (
        None
        if any(v is None for v in x)
        else partition["cells"][
            sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))
        ]
    )


def certificate_scope(cert, query, partition, good, expected):
    indices = tuple(
        partition["vocabulary"].index(name) for name, value in cert["evidence"]
    )
    assert indices == expected
    assert all(
        bool(query[i]) == value
        for i, (name, value) in zip(indices, cert["evidence"], strict=True)
    )
    space = list(itertools.product((False, True), repeat=len(query)))
    mask = [all(x[i] == query[i] for i in indices) for x in space]
    assert oracle_scope(mask, partition["cells"])
    selected = {c for c, chosen in zip(partition["cells"], mask, strict=True) if chosen}
    assert selected == set(cert["selected_leaf_scope"]) and selected <= good
    assert set(cert["removal_witnesses"]) == {name for name, value in cert["evidence"]}


def oracle_scope(mask, cells):
    return all(
        len({flag for flag, c in zip(mask, cells, strict=True) if c == leaf_id}) == 1
        for leaf_id in set(cells)
    )


def numerical(model, logs, oracle):
    error = 0.0
    counts = Counter()
    for m in [model] + ([model["regression"]] if "regression" in model else []):
        p = m["partition"]
        k = len(set(p["cells"]))
        assert k <= 4
        for c, entry in m["leaves"].items():
            rs = [r for r in logs if leaf(p, r["x"]) == int(c)]
            counts_c = []
            for a, name in [("c", "p0"), ("r", "p1")]:
                ys = [r["y"] for r in rs if r["action"] == a]
                counts_c.append(len(ys))
                low, high = cp(sum(ys), len(ys), 0.025 / (4 * k))
                actual = entry["evidence"][name]
                error = max(error, abs(low - actual["lo"]), abs(high - actual["hi"]))
                counts["CP_endpoints"] += 2
            assert entry["ledger"]["counts_c_r_pair"] == counts_c + [0]
            assert entry["ledger"]["per_tail"] == 0.025 / (4 * k)
            assert (
                entry["evidence"]["harm"] is None
                and entry["evidence"]["rescue"] is None
            )
            if not entry["bounds"]:
                assert not all(counts_c)
                continue
            e = entry["evidence"]
            b = entry["bounds"]
            for field, vector, maximize in [
                ("harm_lower", oracle.HARM, False),
                ("harm_upper", oracle.HARM, True),
                ("gain_lower", oracle.GAIN, False),
                ("gain_upper", oracle.GAIN, True),
                ("failure_upper", np.array([1, 0, 1, 0]), True),
            ]:
                expected, _ = oracle.joint_extreme(
                    oracle.Band(**e["p0"]),
                    oracle.Band(**e["p1"]),
                    vector,
                    maximize=maximize,
                )
                error = max(error, abs(expected - b[field]))
                q = np.asarray(b["optimizers"][field])
                assert q.min() >= -1e-9 and abs(q.sum() - 1) < 1e-9
                assert e["p0"]["lo"] - 1e-9 <= q[2] + q[3] <= e["p0"]["hi"] + 1e-9
                assert e["p1"]["lo"] - 1e-9 <= q[1] + q[3] <= e["p1"]["hi"] + 1e-9
                assert abs(q @ vector - b[field]) < 1e-8
                counts["LP_extrema"] += 1
    assert error < 1e-8
    return counts, error


def expected_decision(model, x, oracle):
    def approved(m, c):
        b = m["leaves"].get(str(c), {}).get("bounds")
        return bool(
            b and b["harm_upper"] <= 0.1 + 1e-12 and b["gain_lower"] >= 0.05 - 1e-12
        )

    c = leaf(model["partition"], x)
    passed = approved(model, c)
    rc = leaf(model["regression"]["partition"], x)
    actions = {
        "DSRE": "r" if passed else "c",
        "exact_B7": "r" if passed else "c",
        "direct_partial_ID": "r" if passed else "c",
        "CART_same_gate": "r"
        if passed and model["proposals"][str(c)]["utility"]
        else "c",
        "outcome_regression_same_gate": "r"
        if approved(model["regression"], rc)
        and model["regression"]["proposed"][str(rc)]
        else "c",
        "always_continue": "c",
        "always_recover": "r",
    }
    good = {int(c) for c in model["leaves"] if approved(model, c)}
    minimal = oracle.minimal_certificate(tuple(x), model["partition"]["cells"], good)
    assert (minimal is not None) == passed
    return actions, minimal


def metrics(rows):
    methods = next(iter(rows), {}).get("decision", {}).get("actions", {})
    output = {}
    n = len(rows)
    draws = np.random.default_rng(2026111801).integers(0, n, (4000, n)) if n else None
    for method in methods:
        gains = []
        h = rescue = futile = redundant = recover = success = 0
        lengths = []
        for r in rows:
            use = r["decision"]["actions"][method] == "r"
            yc, yr = int(r["yc"]), int(r["yr"])
            y = yr if use else yc
            success += y
            recover += use
            h += use * yc * (1 - yr)
            rescue += use * (1 - yc) * yr
            futile += use * (1 - yc) * (1 - yr)
            redundant += use * yc * yr
            gains.append(y - yc)
            if method == "DSRE" and r["decision"]["certificate"]:
                lengths.append(len(r["decision"]["certificate"]["evidence"]))
        ci = cp(h, recover, 0.025)
        output[method] = {
            "n": n,
            "success": success,
            "recover": recover,
            "default_continue": n - recover,
            "harm": h,
            "required_rescues": rescue,
            "futile": futile,
            "redundant": redundant,
            "completion_CP95": cp(success, n, 0.025),
            "harm_per_recover_CP95": ci,
            "gain": sum(gains) / n if n else None,
            "gain_parent_bootstrap95": np.quantile(
                np.asarray(gains)[draws].mean(axis=1), [0.025, 0.975]
            ).tolist()
            if n
            else None,
            "certificate_literal_mean": float(np.mean(lengths)) if lengths else None,
        }
    return output


def insertion_metrics(rows):
    eligible = [r for r in rows if r["status"] in ("QUALIFIED", "MISSING")]
    n = len(eligible)
    counts = {
        "raw_completed": len(rows),
        "eligible_checkpoints": n,
        "no_decision_checkpoint": sum(
            r["status"] == "NO_DECISION_CHECKPOINT" for r in rows
        ),
        "four_cells_observed": dict(
            Counter(
                f"{int(r['yc'])}{int(r['yr'])}"
                for r in eligible
                if r["yc"] is not None and r["yr"] is not None
            )
        ),
        "missing_continue": sum(r["yc"] is None for r in eligible),
        "missing_recover": sum(r["yr"] is None for r in eligible),
        "known_continue_successes": sum(r["yc"] is True for r in eligible),
        "known_recover_successes": sum(r["yr"] is True for r in eligible),
        "known_any_action_success": sum(
            r["yc"] is True or r["yr"] is True for r in eligible
        ),
        "scope": "Exploratory eligible-checkpoint empirical bounds only, not calibrated population guarantees; no-checkpoint parents retain their separate raw denominator and receive no invented action outcomes",
    }
    if n:
        counts["continue_empirical_completion_bounds"] = [
            sum(r["yc"] is True for r in eligible) / n,
            sum(r["yc"] is not False for r in eligible) / n,
        ]
        counts["recover_empirical_completion_bounds"] = [
            sum(r["yr"] is True for r in eligible) / n,
            sum(r["yr"] is not False for r in eligible) / n,
        ]
        counts["recover_harm_empirical_bounds"] = [
            sum(r["yc"] is True and r["yr"] is False for r in eligible) / n,
            sum(r["yc"] is not False and r["yr"] is not True for r in eligible) / n,
        ]
        counts["recover_gain_empirical_bounds"] = [
            sum(int(r["yr"] is True) - int(r["yc"] is not False) for r in eligible) / n,
            sum(int(r["yr"] is not False) - int(r["yc"] is True) for r in eligible) / n,
        ]
    return counts


def run(output, compact=False):
    reg = read(ROOT / "registration.json")
    counts = Counter()
    maxerror = 0.0
    for p, h in reg["source_sha256"].items():
        assert sha(p) == h, f"SOURCE_CHANGED:{p}"
        counts["source_hashes"] += 1
    continuity = read(ROOT / "native_environment_continuity.json")
    for p, h in continuity["source_fingerprints"].items():
        assert sha(p) == h, "NATIVE_BINARY_OR_CONTROLLER_CHANGED:" + p
        counts["native_continuity_hashes"] += 1
    if not compact:
        old = read(ROOT / "preservation_start.json")
        for p, h in old["tracked_sha256"].items():
            assert (sha(p) if Path(p).is_file() else None) == h, (
                "TRACKED_HISTORY_CHANGED:" + p
            )
            counts["preserved_tracked_files"] += 1
        for p, h in old["historical_seals"].items():
            assert sha(p) == h
            counts["preserved_historical_seals"] += 1
        # Every historical raw seal entry must still reproduce its historical bytes.
        oldseal = read(
            "results/dsre-evidence-aware/20261117-prospective/raw_evidence_seal.json"
        )
        for p, h in oldseal["sha256"].items():
            if Path(p).exists():
                assert sha(p) == h, p
            else:
                metadata = read(p + ".archive.json")
                assert metadata["original_gzip_sha256"] == h, p
                trace_read(p)
            counts["preserved_historical_raw_files"] += 1
    oracle = load_oracle()
    legacy_path = ROOT / "legacy_regression/model_frozen.json"
    if legacy_path.exists():
        legacy = read(legacy_path)
        legacy_logs = read(ROOT / "legacy_regression/learner/calibration.json")
        legacy_counts, legacy_error = numerical(legacy, legacy_logs, oracle)
        counts.update(
            {"historical_regression_" + k: v for k, v in legacy_counts.items()}
        )
        maxerror = max(maxerror, legacy_error)
    model = (
        read(ROOT / "model_frozen.json")
        if (ROOT / "model_frozen.json").exists()
        else None
    )
    logs = (
        read(ROOT / "learner/calibration.json")
        if (ROOT / "learner/calibration.json").exists()
        else []
    )
    if model:
        nc, error = numerical(model, logs, oracle)
        maxerror = max(maxerror, error)
        counts.update(nc)
        discovery = read(ROOT / "discovery_freeze.json")
        for key in ("partition", "proposals", "source_scope"):
            assert model[key] == discovery[key]
        for key in ("partition", "coefficients", "proposed"):
            assert model["regression"][key] == discovery["regression"][key]
        freeze = read(ROOT / "discovery_freeze.json")
        for m in (freeze, model):
            for p, h in m["input_sha256"].items():
                assert sha(p) == h
            whitelist = {str(Path(p).resolve()) for p in m["input_sha256"]}
            assert all(
                p in whitelist
                or (
                    compact
                    and any(p.endswith("/" + name) for name in m["input_sha256"])
                )
                for p in m["successful_reads"]
            )
            counts["whitelisted_model_reads"] += len(m["successful_reads"])
        witness_path = ROOT / "source_obligation_witnesses.json"
        if witness_path.exists():
            witnesses = read(witness_path)
            assert witnesses["model_sha256"] == sha(ROOT / "model_frozen.json")
            for query in witnesses["queries"]:
                for obligation, cert in query["certificates"].items():
                    good = set()
                    for c, entry in model["leaves"].items():
                        b = entry["bounds"]
                        if not b:
                            continue
                        valid = (
                            b["failure_upper"] <= 0.1 + 1e-12
                            if obligation == "completion"
                            else b["harm_upper"] <= 0.1 + 1e-12
                            and (
                                obligation == "harm_only"
                                or b["gain_lower"] >= 0.05 - 1e-12
                            )
                        )
                        if valid:
                            good.add(int(c))
                    expected = oracle.minimal_certificate(
                        query["x"], model["partition"]["cells"], good
                    )
                    if cert:
                        certificate_scope(
                            cert, query["x"], model["partition"], good, expected
                        )
                    else:
                        assert expected is None
                    counts["all_cube_obligation_minimum_queries"] += 1
            for c, item in witnesses["leaves"].items():
                diagnosis = item["diagnosis"]
                if diagnosis["favorable"] is not None:
                    q, r = (
                        np.asarray(diagnosis[name])
                        for name in ("favorable", "unfavorable")
                    )
                    for p in (q, r):
                        assert p.min() >= -1e-9 and abs(p.sum() - 1) < 1e-8
                    assert abs(q @ oracle.P0 - r @ oracle.P0) < 1e-8
                    assert abs(q @ oracle.P1 - r @ oracle.P1) < 1e-8
                    assert q[2] <= 0.1 + 1e-8 and q[1] - q[2] >= 0.05 - 1e-8
                    assert r[2] > 0.1
                    counts["constructive_equal_marginal_witnesses"] += 1
    phases = {}
    allrows = []
    specs = {(s["phase"], s["index"]): s for s in reg["push"] + reg["peg"]}
    for phase in (
        "native_pilot",
        "discovery",
        "calibration",
        "test",
        "insertion_pilot",
        "insertion_confirmation",
    ):
        rows = [read(p) for p in sorted((ROOT / "records" / phase).glob("*.json"))]
        registered = sum(s["phase"] == phase for s in reg["push"] + reg["peg"])
        phases[phase] = {
            "registered": registered,
            "completed": len(rows),
            "remaining": registered - len(rows),
            "status_counts": dict(Counter(r["status"] for r in rows)),
        }
        attempted = [p for p in (ROOT / "physics" / phase).glob("*/spec.json")]
        phases[phase]["attempted_parents"] = len(attempted)
        phases[phase]["unopened_parents"] = registered - len(attempted)
        completed_indices = {r["spec"]["index"] for r in rows}
        unrecorded = []
        for specpath in attempted:
            s = read(specpath)
            if s["index"] in completed_indices:
                continue
            attempts = []
            for receipt in sorted(specpath.parent.glob("*.execution.json")):
                entry = read(receipt)
                rawpath = receipt.with_name(
                    receipt.name.removesuffix(".execution.json") + ".json.gz"
                )
                if entry["raw_sha256"] is not None:
                    branch = trace_read(rawpath)
                    assert (
                        read(str(rawpath) + ".archive.json")["original_gzip_sha256"]
                        == entry["raw_sha256"]
                    )
                    attempts.append(
                        {
                            "receipt": str(receipt),
                            "returncode": entry["returncode"],
                            "status": branch.get("status"),
                            "phase": branch.get("phase"),
                            "error": branch.get("error"),
                            "observed_y": branch.get("success"),
                        }
                    )
                else:
                    attempts.append(
                        {
                            "receipt": str(receipt),
                            "returncode": entry["returncode"],
                            "observed_y": None,
                        }
                    )
            unrecorded.append(
                {
                    "spec": s,
                    "attempts": attempts,
                    "classification": "Attempt retained at source/task stop; no imputed outcome and no replacement",
                }
            )
        phases[phase]["attempted_incomplete_parents"] = unrecorded
        for r in rows:
            s = r["spec"]
            assert s == specs[phase, s["index"]]
            d = ROOT / "physics" / phase / str(s["index"])
            branches = {}
            for receipt in sorted(d.glob("*.execution.json")):
                rec = read(receipt)
                label = receipt.name.removesuffix(".execution.json")
                path = d / (label + ".json.gz")
                b = trace_read(path)
                branches[label] = b
                assert b["spec"] == s and rec["spec_sha256"] == sha(d / "spec.json")
                assert (
                    read(str(path) + ".archive.json")["original_gzip_sha256"]
                    == rec["raw_sha256"]
                )
                if s["task"] == "PushCube-v1":
                    push(b)
                elif b["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                    peg(b)
                elif b["status"] == "FAILED_PREREQUISITE_OR_PREFIX":
                    assert native_abort(b)
                elif b["status"] == "MISSING_TERMINAL_OUTCOME":
                    assert "success" not in b
                else:
                    assert b["status"] == "CHECKPOINT_ONLY"
                counts["physical_branches"] += 1
                counts["prefix_controls"] += len(b.get("prefix_controls", []))
                counts["future_controls"] += len(b.get("post_controls", []))
            if s["task"] == "PushCube-v1":
                if phase in ("discovery", "calibration"):
                    assert set(branches) == {"assigned"}
                    assert {p.name for p in d.glob("*.json.xz")} == {"assigned.json.xz"}
                    # Independent textual first-bit convention.
                    import hashlib

                    wanted = (
                        "r"
                        if int(
                            hashlib.sha256(
                                f"DSRE-FINAL-PUSH-ARM-v1:{s['seed']}".encode()
                            ).hexdigest()[0],
                            16,
                        )
                        >= 8
                        else "c"
                    )
                    assert r["record"]["action"] == s["assigned"] == wanted
                    assert r["record"]["y"] == branches["assigned"]["success"]
                    assert r["record"]["x"] == branches["assigned"]["features"]
                    assert r["record"]["propensity"] == 0.5
                    assert r["record"]["source_type"] == "randomized_single_action"
                    assert not r["record"]["counterpart_exposed"]
                    assert "seed" not in r["record"] and "condition" not in r["record"]
                    if phase == "calibration":
                        assert (
                            read(ROOT / "discovery.complete.json")["epoch"]
                            <= read(d / "assigned.execution.json")["started_epoch"]
                        )
                        assert (ROOT / "discovery_freeze.json").stat().st_mtime <= read(
                            d / "assigned.execution.json"
                        )["started_epoch"]
                elif phase == "test":
                    assert set(branches) == {"selected", "evaluator"}
                    b, a = branches["selected"], branches["evaluator"]
                    assert (
                        read(d / "selected.execution.json")["completed_epoch"]
                        < read(d / "evaluator.execution.json")["started_epoch"]
                    )
                    assert (
                        ROOT / "selected_test" / f"{s['index']}.json"
                    ).stat().st_mtime < read(d / "evaluator.execution.json")[
                        "started_epoch"
                    ]
                    assert (
                        read(d / "evaluator.execution.json")["started_epoch"]
                        > b["completed_epoch"]
                    )
                    assert (ROOT / "model_frozen.json").stat().st_mtime < read(
                        d / "selected.execution.json"
                    )["started_epoch"]
                    parity(b, a, s["task"])
                    actions, minimal = expected_decision(model, r["x"], oracle)
                    assert actions == r["decision"]["actions"]
                    assert b["executed_action"] == actions["DSRE"]
                    cert = r["decision"]["certificate"]
                    if cert:
                        good = {
                            int(c)
                            for c, entry in model["leaves"].items()
                            if entry["bounds"]
                            and entry["bounds"]["harm_upper"] <= 0.1 + 1e-12
                            and entry["bounds"]["gain_lower"] >= 0.05 - 1e-12
                        }
                        certificate_scope(
                            cert, r["x"], model["partition"], good, minimal
                        )
                        counts["minimum_scope_certificates"] += 1
                    assert all(
                        Path(p).name == "model_frozen.json"
                        for p in b.get("successful_reads", [])
                    )
                    assert r["yc"] == (
                        b["success"] if b["executed_action"] == "c" else a["success"]
                    )
                    assert r["yr"] == (
                        b["success"] if b["executed_action"] == "r" else a["success"]
                    )
                    allrows.append(r)
                else:
                    for b in branches.values():
                        parity(branches["c0"], b, s["task"])
                    from dsre_source_risk_audit import state_equal

                    for action in ("c", "r"):
                        for first, repeat in zip(
                            branches[action + "0"]["post"],
                            branches[action + "1"]["post"],
                            strict=True,
                        ):
                            state_equal(first, repeat)
                            counts["native_repeat_future_states"] += 1
            elif r["status"] != "NO_DECISION_CHECKPOINT":
                for label in ("c", "r"):
                    parity(branches["screen"], branches[label], s["task"])
            else:
                assert set(branches) == {"screen"} and native_abort(branches["screen"])
    receipts = [read(p) for p in (ROOT / "physics").rglob("*.execution.json")]
    seconds = sum(r["elapsed_seconds"] for r in receipts)
    assert seconds <= 12 * 3600
    size = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    assert size < 4 * 1024**3
    assert not any(n.startswith("dual_rec.evidence_aware") for n in sys.modules)
    result = {
        "passed": True,
        "phases": phases,
        "counts": dict(counts),
        "maximum_numerical_discrepancy": maxerror,
        "policies": metrics(allrows),
        "equal_action_counts_vs_DSRE": {
            method: sum(
                r["decision"]["actions"][method] == r["decision"]["actions"]["DSRE"]
                for r in allrows
            )
            for method in next(iter(allrows), {}).get("decision", {}).get("actions", {})
        },
        "four_cells": dict(Counter(f"{int(r['yc'])}{int(r['yr'])}" for r in allrows)),
        "paired_hindsight_completion": sum(r["yc"] or r["yr"] for r in allrows),
        "unselected_rescue_opportunities": sum(
            not r["yc"] and r["yr"] and r["decision"]["actions"]["DSRE"] == "c"
            for r in allrows
        ),
        "source_qualified_test": len(allrows),
        "registered_test": 256,
        "statistical_scope": "Exact per-method frozen-cell C family. T intervals descriptive independent-parent; no across-method/task joint95, no optional-pilot PAC claim.",
        "physics_worker_seconds": seconds,
        "physics_processes": len(receipts),
        "compressed_campaign_bytes": size,
        "production_inference_imported": False,
        "historical_preservation_rechecked": not compact,
        "auditor_sha256": sha(__file__),
        "insertion": {
            phase: insertion_metrics(
                [read(p) for p in (ROOT / "records" / phase).glob("*.json")]
            )
            for phase in ("insertion_pilot", "insertion_confirmation")
        },
    }
    if allrows:
        differences = np.asarray(
            [
                int(r["yr"] if r["decision"]["actions"]["DSRE"] == "r" else r["yc"])
                - int(r["yr"])
                for r in allrows
            ]
        )
        draws = np.random.default_rng(2026111801).integers(
            0, len(allrows), (4000, len(allrows))
        )
        result["DSRE_minus_always_R_completion"] = {
            "net_parents": int(differences.sum()),
            "mean": float(differences.mean()),
            "paired_parent_bootstrap95": np.quantile(
                differences[draws].mean(axis=1), [0.025, 0.975]
            ).tolist(),
            "interpretation": "Descriptive comparison; no across-method significance or algorithm dominance claim",
        }
    save(output, result)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k
                in (
                    "passed",
                    "phases",
                    "counts",
                    "physics_worker_seconds",
                    "physics_processes",
                    "four_cells",
                )
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=ROOT / "independent_final_audit.json")
    p.add_argument("--compact", action="store_true")
    args = p.parse_args()
    run(args.output, args.compact)
