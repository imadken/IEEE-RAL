"""Independent integer-mask routing, raw-label recount and weighted-bootstrap audit."""

import argparse
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read
from dsre_paper_confirmation import independent_tree_action
from dsre_recovery_audit import exact_upper, gz
from dsre_recovery_evidence import METHODS, PRIOR, TASK

from dual_rec.dsre.repair_oracle import Oracle


def route_audit(root):
    setting = read(root / "frozen_routers.json")["tasks"][TASK]["1"]
    oracle = Oracle(setting["table"], setting["parent_groups"])
    full = Oracle(setting["full_table"], setting["parent_groups"])
    cache = {}
    checks = 0
    for stage in ("calibration", "test"):
        for path in sorted((root / stage).glob("*/*/screen.json.gz")):
            raw = gz(path)
            x = tuple(raw["packet"]["values"])
            fx = tuple(raw["packet"]["full_values"])
            actual = raw["proposals"]
            if x not in cache:
                query = {"scope": setting["table"]["scope"], "features": list(x)}
                strict = oracle.rule(query)
                risk = strict or oracle.rule(query, 0.1, 2)
                expected = {
                    "DSRE_strict": strict,
                    "B7": strict,
                    "DSRE_risk": risk,
                    "B7_risk": risk,
                }
                for m, b, c in (
                    ("B1_one_strict", 0, 1),
                    ("B1_two_strict", 0, 2),
                    ("B5_beta10", 0.1, None),
                ):
                    expected[m] = oracle.rule(query, b, c)
                trees = {
                    m: independent_tree_action(
                        setting["trees"][m[4]],
                        setting["table"],
                        setting["parent_groups"],
                        x,
                        0.9 if m.endswith("beta10") else 1,
                    )
                    for m in (
                        "CART1_strict",
                        "CART2_strict",
                        "CART1_beta10",
                        "CART2_beta10",
                    )
                }
                cache[x] = (expected, trees)
            expected, trees = cache[x]
            for m, r in expected.items():
                assert actual[m]["action"] == (r["action"] if r else None), (path, m)
                if r:
                    assert actual[m]["evidence"] == r["evidence"], (
                        path,
                        m,
                        "minimum evidence",
                    )
                checks += 1
            for m, a in trees.items():
                assert actual[m]["action"] == a
                checks += 1
            assert (
                actual["B0_continue"]["action"] == "continue"
                and actual["B0_recover"]["action"] == "recover"
            )
            checks += 2
            mask = full.match(fx, list(range(12)))
            a = next(
                (
                    a
                    for a in ("continue", "recover")
                    if full.parents(mask) >= 2 and not (mask & full.bad[a])
                ),
                None,
            )
            assert actual["full_signature_strict"]["action"] == a
            checks += 1
            greedy = actual["greedy_pure_rule"]
            if greedy["action"]:
                ix = [
                    setting["table"]["scope"]["features"].index(f["feature"])
                    for f in greedy["evidence"]
                ]
                mask = oracle.match(x, ix)
                assert oracle.parents(mask) >= 2 and not (
                    mask & oracle.bad[greedy["action"]]
                )
            assert actual["policy_faithful"]["action"] in (
                None,
                actual["CART2_beta10"]["action"],
            )
            checks += 2
    return {
        "integer_mask_decision_checks": checks,
        "distinct_common_signatures": len(cache),
        "scope": "Exact core/risk rules and trees independently derived; greedy universal adequacy checked; policy-faithfulness label consistency checked. No claim of a new optimizer.",
    }


def numerical(root):
    # Rebuild assigned parent errors from raw terminal frames and sealed admissions.
    old = read(PRIOR / "calibration_records.json")
    oldgroups = defaultdict(dict)
    newgroups = defaultdict(dict)
    for r in old:
        key = f"{r['method']}|{r['task']}|{r['action']}"
        oldgroups[key][r["group"]] = oldgroups[key].get(r["group"], False) or bool(
            r["unacceptable"]
        )
    admitted_counts = dict.fromkeys(METHODS, 0)
    decision_checks = 0
    for path in sorted((root / "progress").glob("calibration-*.json")):
        p = read(path)
        if p["status"] != "COMPLETE":
            continue
        directory = root / "calibration" / str(p["seed"])
        d = read(directory / "decision.json")
        for m in METHODS:
            assigned = any(x[m]["proposal"] == "recover" for x in d["all_actions"])
            assert (m in d["admitted_methods"]) == (
                assigned and admitted_counts[m] < 112
            )
        for m in d["admitted_methods"]:
            error = False
            for i, c in enumerate(p["cells"]):
                if d["all_actions"][i][m]["proposal"] == "recover":
                    out = gz(directory / c["condition"] / "recover.json.gz")
                    error |= not bool(out["frames"][-1]["state"]["success"])
            newgroups[f"{m}|{TASK}|recover"][f"{TASK}/{p['seed']}"] = error
            admitted_counts[m] += 1
    cal = read(root / "calibration_decision.json")["strata"]
    for key, v in cal.items():
        oldg = oldgroups[key]
        fresh = newgroups[key]
        combined = oldg | fresh
        assert (
            len(combined) == v["assigned_parents"]
            and sum(combined.values()) == v["error_parents"]
        )
        assert (
            abs(exact_upper(sum(combined.values()), len(combined)) - v["upper"]) < 1e-10
        )
        if key.endswith("|PickCube-v1|recover"):
            assert (
                len(fresh) == v["new_assigned_parents"]
                and sum(fresh.values()) == v["new_error_parents"]
            )
            assert (
                abs(exact_upper(sum(fresh.values()), len(fresh)) - v["new_upper"])
                < 1e-10
            )
            expected = (
                len(fresh) == 112
                and v["upper"] <= 0.1
                and v["new_upper"] <= 0.1
                and not (root / "study_halt.json").exists()
            )
            assert bool(v["enabled"]) == expected
        else:
            assert v == read(PRIOR / "calibration_decision.json")["strata"][key]
        decision_checks += 1
    result = {
        "calibration_strata_rebuilt_from_raw": decision_checks,
        "own_fixed_quota_verified": admitted_counts,
    }
    if not (root / "test_analysis.json").exists():
        return result
    analysis = read(root / "test_analysis.json")
    if analysis["status"] == "NO_QUALIFIED_TEST_PARENTS":
        return result | {"test": "NONE; no imputation"}
    records = read(root / "test_records.json")
    truth = {}
    initial = {}
    sealed = {}
    for path in sorted((root / "progress").glob("test-*.json")):
        p = read(path)
        if p["status"] != "COMPLETE":
            continue
        directory = root / "test" / str(p["seed"])
        d = read(directory / "decision.json")
        for i, c in enumerate(p["cells"]):
            name = f"{TASK}/{p['seed']}/{c['condition']}"
            truth[name] = [
                bool(
                    gz(directory / c["condition"] / (a + ".json.gz"))["frames"][-1][
                        "state"
                    ]["success"]
                )
                for a in ("continue", "recover")
            ]
            initial[name] = bool(
                gz(directory / c["condition"] / "screen.json.gz")["canonical_start"][
                    "success"
                ]
            )
            sealed[name] = d["all_actions"][i]
    ids = list(truth)
    parents = sorted({i.rsplit("/", 1)[0] for i in ids})
    pindex = np.array([parents.index(i.rsplit("/", 1)[0]) for i in ids])
    n = len(parents)
    rng = np.random.Generator(np.random.PCG64(2026111501))
    draws = rng.integers(n, size=(4000, n))
    weights = np.array([np.bincount(d, minlength=n) for d in draws])
    fields = {}
    checks = 0
    for mode in ("proposal", "calibrated"):
        for m in METHODS:
            rows = {
                r["id"]: r for r in records if r["method"] == m and r["mode"] == mode
            }
            action = np.array(
                [
                    {None: -1, "continue": 0, "recover": 1}[
                        sealed[i][m]["gated" if mode == "calibrated" else "proposal"]
                    ]
                    for i in ids
                ]
            )
            acted = action >= 0
            good = acted & np.array(
                [truth[i][max(a, 0)] for i, a in zip(ids, action, strict=True)]
            )
            bad = acted & ~good
            required = (action == 1) & np.array(
                [not initial[i] and not truth[i][0] and truth[i][1] for i in ids]
            )
            values = {
                "successful": good.astype(int),
                "unacceptable": bad.astype(int),
                "recommended": acted.astype(int),
                "required_recovery_success": required.astype(int),
            }
            fields[m, mode] = values
            for j, i in enumerate(ids):
                for f, v in values.items():
                    assert rows[i][f] == v[j]
                    checks += 1
                assert rows[i]["deferred"] == int(not acted[j])
                checks += 1
            table = analysis["tables"][f"{TASK}|{m}|{mode}|clean|all"]
            for f, v in values.items():
                assert table[f] == int(v.sum())
                checks += 1
    interval_checks = 0
    for m in METHODS:
        for mode in ("proposal", "calibrated"):
            for field in (
                "successful",
                "unacceptable",
                "recommended",
                "required_recovery_success",
            ):
                v = fields["DSRE_risk", mode][field] - fields[m, mode][field]
                grouped = np.bincount(pindex, weights=v, minlength=n)
                den = np.bincount(pindex, minlength=n)
                samples = (weights @ grouped) / (weights @ den)
                low, high = np.percentile(samples, [2.5, 97.5])
                reported = analysis["paired_risk_minus_baselines"][m + "|" + mode][
                    field
                ]
                assert abs(reported["estimate"] - v.mean()) < 1e-12
                assert np.allclose(
                    [low, high],
                    [reported["lower"], reported["upper"]],
                    atol=1e-12,
                    rtol=0,
                )
                interval_checks += 1
    result.update(
        raw_label_count_checks=checks,
        independent_weighted_paired_intervals=interval_checks,
        test_parents=n,
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    value = {
        "passed": True,
        "routing": route_audit(a.root),
        "numerical": numerical(a.root),
        "epoch": time.time(),
    }
    atomic(a.root / "numerical_audit.json", value)
    print(value, flush=True)
