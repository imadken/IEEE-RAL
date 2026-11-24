"""Reconstruct the frozen manuscript claims; never import inference or physics.

This audit reads the native recorded outcomes, not report totals. Binomial
endpoints are inverted from the CDF independently of production beta quantiles.
"""

import csv
import gzip
import hashlib
import itertools
import json
import lzma
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, linprog
from scipy.stats import binom

BASE = Path("results/dsre-evidence-aware")
OLD = BASE / "20261117-prospective"
NEW = BASE / "20261118-final-science"
OUT = Path("research/dsre_stage1_manuscript")
INPUTS = {}
SEALS = {}
for root in (OLD, NEW):
    seal = root / "raw_evidence_seal.json"
    SEALS.update(json.loads(seal.read_text())["sha256"])
    INPUTS[str(seal)] = hashlib.sha256(seal.read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    if path.exists():
        encoded = path.read_bytes()
        checksum = hashlib.sha256(encoded).hexdigest()
        decoded = gzip.decompress(encoded) if path.suffix == ".gz" else encoded
    else:
        sidecar = json.loads(Path(str(path) + ".archive.json").read_text())
        encoded = path.with_suffix(".xz").read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == sidecar["xz_sha256"]
        decoded = lzma.decompress(encoded)
        assert hashlib.sha256(decoded).hexdigest() == sidecar["decoded_sha256"]
        checksum = sidecar["original_gzip_sha256"]
        INPUTS[str(path.with_suffix(".xz"))] = sidecar["xz_sha256"]
        INPUTS[str(path) + ".archive.json"] = hashlib.sha256(
            Path(str(path) + ".archive.json").read_bytes()
        ).hexdigest()
    if str(path) in SEALS:
        assert checksum == SEALS[str(path)], f"seal mismatch: {path}"
    INPUTS[str(path)] = checksum
    return json.loads(decoded)


def cp(k, n, tail):
    if not n:
        return 0.0, 1.0
    lo = (
        0.0
        if not k
        else brentq(lambda p: binom.sf(k - 1, n, p) - tail, 0, 1, xtol=1e-14)
    )
    hi = (
        1.0 if k == n else brentq(lambda p: binom.cdf(k, n, p) - tail, 0, 1, xtol=1e-14)
    )
    return lo, hi


def route(model, x):
    assert len(x) == 6 and all(isinstance(v, bool) for v in x)
    return model["partition"]["cells"][int("".join(str(int(v)) for v in x), 2)]


def terminal(raw, push):
    state = raw["post"][-1]
    extra = state["observation"]["extra"]
    obj = np.asarray(extra["obj_pose"], float).reshape(-1)[:3]
    goal = np.asarray(extra["goal_pos"], float).reshape(-1)[:3]
    if push:
        success = np.linalg.norm(obj[:2] - goal[:2]) < 0.10 and obj[2] < 0.025
    else:
        qvel = np.asarray(state["observation"]["agent"]["qvel"], float).reshape(-1)
        success = np.linalg.norm(obj - goal) <= 0.025 and max(abs(qvel[:-2])) <= 0.2
    assert bool(success) == raw["success"] == state["success"]


def minimum(model, x, passed):
    cube = list(itertools.product((False, True), repeat=6))
    cells = model["partition"]["cells"]
    for size in range(7):
        for indices in itertools.combinations(range(6), size):
            hit = [all(z[i] == x[i] for i in indices) for z in cube]
            scope = {c for c, h in zip(cells, hit, strict=True) if h}
            if not scope <= passed:
                continue
            if all(
                len({h for c, h in zip(cells, hit, strict=True) if c == leaf}) == 1
                for leaf in set(cells)
            ):
                return [
                    (model["partition"]["vocabulary"][i], x[i]) for i in indices
                ], sorted(scope)
    return None


def counts(rows, name):
    selected = [r for r in rows if r["actions"][name] == "r"]
    harm = sum(r["yc"] and not r["yr"] for r in selected)
    return {
        "n": len(rows),
        "recover": len(selected),
        "completion": sum(
            r["yr"] if r["actions"][name] == "r" else r["yc"] for r in rows
        ),
        "rescue": sum(not r["yc"] and r["yr"] for r in selected),
        "harm": harm,
        "futile": sum(not r["yc"] and not r["yr"] for r in selected),
        "redundant": sum(r["yc"] and r["yr"] for r in selected),
        "default_continue": len(rows) - len(selected),
        "observed_harm_two_sided_CP95": cp(harm, len(selected), 0.025),
    }


def verify(task):
    push = task == "PushCube-v1"
    root = NEW if push else OLD / "prospective" / task
    # The historical native traces sit outside the prospective aggregate tree.
    phys = OLD / "physics" / task
    model = read(root / ("model_frozen.json" if push else "models/logged.json"))
    if push:
        manifest = read(NEW / "registration.json")["push"]
        access = model["successful_reads"]
        expected_access = model["input_sha256"]
    else:
        original = read(BASE / "20261117-first-session/prospective_manifest.json")
        ready = read(BASE / "20261117-first-session/prospective_ready_manifest.json")
        assert original["cohorts"] == ready["cohorts"]
        manifest = [r for phase in ready["cohorts"][task].values() for r in phase]
        access = model["successful_data_reads"]
        expected_access = model["input_whitelist_sha256"]
        assert model["pair_parent_ids"] == []
    assert all(
        str(Path(p).resolve()) in {str(Path(v).resolve()) for v in expected_access}
        for p in access
    )
    assert not any(
        "/test/" in p or "/evaluator/" in p or "counterpart" in p for p in access
    )
    for name, checksum in expected_access.items():
        path = Path(name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
        INPUTS[str(path)] = checksum
    registry = {(r["phase"], r["index"]): r for r in manifest}
    k = len(model["leaves"])
    support, parents = {}, {}
    arm_counts = Counter()
    for phase, n in (("discovery", 128), ("calibration", 1024)):
        directory = root / ("records/" + phase if push else phase)
        wrappers = [read(p) for p in sorted(directory.glob("*.json"))]
        assert len(wrappers) == n
        parents[phase] = {w["record"]["parent_id"] for w in wrappers}
        assert len(parents[phase]) == n
        for w in wrappers:
            spec, r = w["spec"], w["record"]
            assert spec == registry[phase, spec["index"]]
            assert r["propensity"] == 0.5 and not r["counterpart_exposed"]
            assert not {"yc", "yr", "seed", "condition"} & set(r)
            expected = (
                ("c", "r")[
                    hashlib.sha256(
                        f"DSRE-FINAL-PUSH-ARM-v1:{spec['seed']}".encode()
                    ).digest()[0]
                    >> 7
                ]
                if push
                else ("c", "r")[
                    int(
                        hashlib.sha256(
                            f"dsre-evidence-v2:arm:{task}:{spec['seed']}".encode()
                        ).hexdigest(),
                        16,
                    )
                    % 2
                ]
            )
            assert expected == r["action"]
            label = "assigned" if push else "randomized_assigned"
            directory_native = (
                NEW / "physics" / phase / str(spec["index"])
                if push
                else phys / phase / str(spec["index"])
            )
            raw = read(directory_native / (label + ".json.gz"))
            assert raw["status"] == "COMPLETE" and raw["success"] == r["y"]
            terminal(raw, push)
            assert len(raw["post_controls"]) == len(raw["post"]) == 70
            assert raw["success"] == raw["post"][-1]["success"]
            # Historical acquisition arms collected separately budgeted counterparts.
            # They are not inputs to the primary single-action learner.
            observed_labels = {
                p.name.removesuffix(".gz").removesuffix(".xz").removesuffix(".json")
                for p in [
                    *directory_native.glob("*.json.gz"),
                    *directory_native.glob("*.json.xz"),
                ]
            }
            allowed = (
                {label}
                if push
                else {
                    label,
                    "screen",
                    "policy_screen",
                    "acquisition_screen",
                    "acquisition_counterpart",
                }
            )
            assert observed_labels <= allowed, observed_labels
            arm_counts[phase, r["action"]] += 1
            if phase == "calibration":
                support.setdefault(route(model, r["x"]), {"c": [], "r": []})[
                    r["action"]
                ].append(r["y"])
    assert parents["discovery"].isdisjoint(parents["calibration"])
    bands, passed, max_error = {}, set(), 0.0
    for leaf, arms in sorted(support.items()):
        intervals = {a: cp(sum(y), len(y), 0.025 / (4 * k)) for a, y in arms.items()}
        lc, uc = intervals["c"]
        lr, ur = intervals["r"]
        bounds = {
            "harm_upper": min(uc, 1 - lr),
            "gain_lower": lr - uc,
            "gain_upper": ur - lc,
            "harm_lower": max(0, lc - ur),
        }
        # A second calculation solves the four-variable outcome polytope.
        A = [[0, 0, 1, 1], [0, 0, -1, -1], [0, 1, 0, 1], [0, -1, 0, -1]]
        b = [uc, -lc, ur, -lr]
        for objective, field, sign in [
            ([0, 0, -1, 0], "harm_upper", -1),
            ([0, 1, -1, 0], "gain_lower", 1),
        ]:
            lp = linprog(
                objective,
                A_ub=A,
                b_ub=b,
                A_eq=[[1] * 4],
                b_eq=[1],
                bounds=(0, None),
                method="highs",
            )
            assert lp.success and abs(sign * lp.fun - bounds[field]) < 1e-10
        saved = model["leaves"][str(leaf)]
        for a, key in [("c", "p0"), ("r", "p1")]:
            for j, end in enumerate(("lo", "hi")):
                max_error = max(
                    max_error, abs(intervals[a][j] - saved["evidence"][key][end])
                )
        for field, value in bounds.items():
            max_error = max(max_error, abs(value - saved["bounds"][field]))
        if bounds["harm_upper"] <= 0.10 and bounds["gain_lower"] >= 0.05:
            passed.add(leaf)
        bands[leaf] = dict(
            n_c=len(arms["c"]), n_r=len(arms["r"]), intervals=intervals, **bounds
        )
    assert max_error < 1e-10
    decisions = (
        {}
        if push
        else {
            r["parent_id"]: r
            for r in read(root / "evaluations/logged.json")["decisions"]
        }
    )
    regression = (
        {}
        if push
        else {
            r["parent_id"]: r
            for r in read(NEW / "legacy_regression/evaluation.json")["rows"]
        }
    )
    rows, certs, literals = [], 0, Counter()
    directory = root / ("records/test" if push else "test")
    for path in sorted(directory.glob("*.json")):
        w = read(path)
        spec, parent = w["spec"], w["parent_id"]
        assert spec == registry["test", spec["index"]]
        decision = w["decision"] if push else decisions[parent]
        pair = w if push else read(root / "evaluator" / (parent + ".json"))
        actions = dict(decision["actions"])
        if not push:
            actions.update(regression[parent]["decision"]["actions"])
        labels = (
            ("selected", "evaluator")
            if push
            else ("selected_policy", "evaluator_counterpart")
        )
        directory_native = (
            NEW / "physics/test" / str(spec["index"])
            if push
            else phys / "test" / str(spec["index"])
        )
        selected = read(directory_native / (labels[0] + ".json.gz"))
        other = read(directory_native / (labels[1] + ".json.gz"))
        selected_execution = read(directory_native / (labels[0] + ".execution.json"))
        other_execution = read(directory_native / (labels[1] + ".execution.json"))
        assert (
            selected_execution.get(
                "completed_epoch", selected_execution.get("finished_epoch")
            )
            <= other_execution["started_epoch"]
        )
        first = actions["DSRE"]
        expected = {
            first: selected["success"],
            {"c": "r", "r": "c"}[first]: other["success"],
        }
        assert (pair["yc"], pair["yr"]) == (expected["c"], expected["r"])
        for raw in (selected, other):
            assert raw["status"] == "COMPLETE" and len(raw["post_controls"]) == 70
            assert raw["success"] == raw["post"][-1]["success"]
            terminal(raw, push)
        assert selected["prefix"] == other["prefix"]
        assert selected["controller_memory"] == other["controller_memory"]
        assert route(model, w["x"]) == decision["leaf"]
        assert first == ("r" if decision["leaf"] in passed else "c")
        cert = decision["certificate"]
        wanted = minimum(model, w["x"], passed)
        assert (cert is None) == (wanted is None)
        if cert:
            certs += 1
            assert [list(t) for t in wanted[0]] == cert["evidence"]
            assert wanted[1] == cert["selected_leaf_scope"]
            literals[json.dumps(cert["evidence"])] += 1
        rows.append(
            {
                "parent_id": parent,
                "x": w["x"],
                "yc": pair["yc"],
                "yr": pair["yr"],
                "actions": actions,
            }
        )
    parents["test"] = {r["parent_id"] for r in rows}
    assert len(rows) == len(parents["test"]) == 256
    assert parents["test"].isdisjoint(parents["discovery"] | parents["calibration"])
    metrics = {name: counts(rows, name) for name in rows[0]["actions"]}
    agreement = {
        name: sum(r["actions"][name] == r["actions"]["DSRE"] for r in rows)
        for name in metrics
    }
    signature_groups = {}
    for row in rows:
        signature_groups.setdefault(tuple(row["x"]), []).append(row)
    signature_diagnostics = []
    for x, group in sorted(signature_groups.items()):
        n = len(group)
        p0 = sum(r["yc"] for r in group) / n
        p1 = sum(r["yr"] for r in group) / n
        h = sum(r["yc"] and not r["yr"] for r in group) / n
        signature_diagnostics.append(
            {
                "x": x,
                "n": n,
                "p0": p0,
                "p1": p1,
                "h": h,
                "four_cells": dict(
                    Counter(str(int(r["yc"])) + str(int(r["yr"])) for r in group)
                ),
                "empirical_paired_only_n_ge_10": n >= 10
                and p1 - p0 >= 0.05
                and h <= 0.10
                and min(p0, 1 - p1) > 0.10,
            }
        )
    result = {
        "task": task,
        "calibration": bands,
        "passed_leaves": sorted(passed),
        "calibration_max_error": max_error,
        "methods": metrics,
        "action_agreement": agreement,
        "four_cells": dict(
            Counter(str(int(r["yc"])) + str(int(r["yr"])) for r in rows)
        ),
        "certificates": certs,
        "literal_frequencies": dict(literals),
        "paired_test": rows,
        "signature_diagnostics": signature_diagnostics,
        "learner_whitelist_files": len(expected_access),
        "support": {f"{p}/{a}": n for (p, a), n in sorted(arm_counts.items())},
        "budget": {
            "discovery": 128,
            "calibration": 1024,
            "selected_test": 256,
            "evaluator_only": 256,
            "controls_per_macro": 70,
        },
    }
    print(
        task,
        json.dumps(
            {
                "four_cells": result["four_cells"],
                "DSRE": metrics["DSRE"],
                "agreement": agreement,
            }
        ),
        flush=True,
    )
    return result


def boundaries(results):
    pick = OLD / "prospective/PickCube-v1"
    pairs = {r["parent_id"]: r for r in results["PickCube-v1"]["paired_test"]}
    acquisition = {}
    for strategy in (
        "all_logs",
        "all_pairs",
        "uniform_mix",
        "witness",
        "decision_uncertainty",
    ):
        m = read(pick / "models" / f"{strategy}_512.json")
        assert (
            m["logical_calibration_executions"]
            == len(m["log_parent_ids"]) + len(m["pair_parent_ids"])
            == 1024
        )
        ev = read(pick / "evaluations" / f"{strategy}_512.json")
        rows = [
            dict(pairs[d["parent_id"]], actions=d["actions"]) for d in ev["decisions"]
        ]
        acquisition[strategy] = counts(rows, "DSRE")
        assert all(
            d["actions"]["DSRE"] == pairs[d["parent_id"]]["actions"]["DSRE"]
            for d in ev["decisions"]
        )
    nav = OLD / "prospective/PointMaze_UMaze-v3"
    records = [read(p) for p in (nav / "test").glob("*.json")]
    eligible = [r for r in records if r["status"] == "COMPLETE"]
    absent = [r for r in records if r["status"] == "ALREADY_SOLVED_PREFIX"]
    assert len(records) == 256 and len(eligible) == 255 and len(absent) == 1
    assert all(r["y"] is True and all(v is None for v in r["x"]) for r in absent)
    nav_cells = Counter()
    for r in eligible:
        p = read(nav / "evaluator" / (r["parent_id"] + ".json"))
        nav_cells[str(int(p["yc"])) + str(int(p["yr"]))] += 1
    assert nav_cells.get("01", 0) == 0
    peg = [read(p) for p in (NEW / "records/insertion_pilot").glob("*.json")]
    assert len(peg) == 48 and all(
        r["status"] == "QUALIFIED" and not r["missing"] for r in peg
    )
    peg_cells = Counter(str(int(r["yc"])) + str(int(r["yr"])) for r in peg)
    decision = read(NEW / "insertion_extension_decision.json")
    assert dict(peg_cells) == decision["outcomes"] and not decision["extend"]
    assert not (NEW / "records/insertion_confirmation").exists()
    return {
        "acquisition_primary_cost": {"base": 512, "additional": 512},
        "acquisition": acquisition,
        "navigation": {
            "registered": 256,
            "eligible": 255,
            "absorbed": 1,
            "four_cells": dict(nav_cells),
        },
        "insertion": {
            "pilot": 48,
            "four_cells": dict(peg_cells),
            "confirmation": 0,
            "conditional_reserved": 96,
            "extend": False,
        },
    }


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    results = {t: verify(t) for t in ("PickCube-v1", "PushCube-v1")}
    secondary = boundaries(results)
    # Explicit analytical countermodels, not robot observations.
    worlds = [[0.4, 0.2, 0, 0.4], [0, 0.6, 0.4, 0]]
    assert all(
        abs(q[2] + q[3] - 0.4) < 1e-12 and abs(q[1] + q[3] - 0.6) < 1e-12
        for q in worlds
    )
    payload = {
        "science_base_commit": "d917a69d47f3102123030eaf565f4623dad86525",
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
        "analytical_worlds": worlds,
        "boundary_checks": secondary,
        "input_sha256": INPUTS,
        "new_physics": 0,
        "imports_production_inference": False,
    }
    (OUT / "independent_numbers.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (OUT / "main_results.csv").open("w") as f:
        writer = csv.DictWriter(
            f,
            lineterminator="\n",
            fieldnames=[
                "task",
                "method",
                "n",
                "recover",
                "rescue",
                "harm",
                "futile",
                "redundant",
                "completion",
                "default_continue",
            ],
        )
        writer.writeheader()
        for task, result in results.items():
            for method, values in result["methods"].items():
                writer.writerow(
                    dict(
                        task=task,
                        method=method,
                        **{k: values[k] for k in writer.fieldnames[2:]},
                    )
                )


if __name__ == "__main__":
    main()
