"""Independent raw-record, finite-oracle, numerical and calibration verification."""

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np

from dual_rec.dsre.oracle import verify_certificate


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def value_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def flatten(value):
    if isinstance(value, list):
        return [n for v in value for n in flatten(v)]
    return [float(value)]


def numeric_difference(a, b):
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        return max((numeric_difference(a[k], b[k]) for k in a), default=0)
    x, y = flatten(a), flatten(b)
    assert len(x) == len(y)
    return max((abs(v - w) for v, w in zip(x, y, strict=True)), default=0)


def same_state(a, b):
    assert math.dist(a["position"], b["position"]) <= 1e-5
    qa, qb = flatten(a["quaternion"]), flatten(b["quaternion"])
    dot = abs(sum(x * y for x, y in zip(qa, qb, strict=True))) / math.sqrt(
        sum(x * x for x in qa) * sum(y * y for y in qb)
    )
    assert 2 * math.acos(min(1, dot)) <= 1e-4
    for key in ("velocity", "qpos", "observation"):
        assert numeric_difference(a[key], b[key]) <= 1e-4
    assert abs(a["time"] - b["time"]) <= 1e-9
    assert a["success"] == b["success"] and a["contacts"] == b["contacts"]


def observed_vector(obs, name, count=3):
    value = obs.get("extra", {}).get(name)
    if value is None:
        return None
    vector = flatten(value)[:count]
    return (
        vector
        if len(vector) == count and all(math.isfinite(v) for v in vector)
        else None
    )


def independently_project(prefix, coarse=False):
    first, current = prefix[0]["observation"], prefix[-1]["observation"]

    def vector(obs, name):
        v = observed_vector(obs, name)
        return [round(x / 0.02) * 0.02 for x in v] if coarse and v is not None else v

    obj, hand, goal = (
        vector(current, "obj_pose"),
        vector(current, "tcp_pose"),
        vector(current, "goal_pos"),
    )
    old_obj, old_goal = vector(first, "obj_pose"), vector(first, "goal_pos")

    def dist(a, b):
        return (
            math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))
            if a is not None and b is not None
            else None
        )

    near, prox = dist(obj, goal), dist(hand, obj)
    previous, movement = dist(old_obj, old_goal), dist(old_obj, obj)
    joints = flatten(current.get("agent", {}).get("qpos", []))
    return [
        None if near is None else near <= 0.03,
        None if prox is None else prox <= 0.04,
        None if previous is None or near is None else previous - near >= 0.005,
        None if movement is None else movement >= 0.005,
        sum(abs(x) for x in joints[-2:]) <= 0.04 if len(joints) == 9 else None,
        hand[2] - obj[2] > 0.03 if hand is not None and obj is not None else None,
    ]


def variant_features(pair, variant, query=False):
    if variant == "plus_privileged":
        return pair["privileged_features"]
    if variant == "coarse_geometry":
        return pair["coarse_features"]
    result = list(pair["features"])
    if variant == "without_history":
        result[2:4] = [None, None]
    if variant == "without_goal_channel":
        result[0] = result[2] = None
    if variant == "query_channel_missing" and query:
        result[int(hashlib.sha256(pair["id"].encode()).hexdigest(), 16) % 6] = None
    return result


def compatible(row, x, indices):
    return all(
        row["features"][i] is None or row["features"][i] == x[i] for i in indices
    )


def current_source(path):
    original = Path(path)
    if original.is_file() or original.suffix != ".md":
        return original
    return Path("docs") / original.name


def verify_sources(root):
    freeze = load(root / "experiment_freeze.json")
    amendments = (
        load(root / "post_execution_path_amendment.json")
        if (root / "post_execution_path_amendment.json").exists()
        else None
    )
    for path, expected in freeze["source_sha256"].items():
        if amendments and path == amendments["source"]:
            assert Path(path).resolve() == Path("scripts/dsre_experiment.py").resolve()
            assert amendments["kind"] == "DOCUMENT_LOCATION_ONLY_AFTER_USER_RELOCATION"
            original = Path(amendments["original_copy"])
            assert sha(original) == expected == amendments["original_sha256"]
            allowed = [
                (
                    "def rows(path):",
                    'def protocol_path():\n    original = Path("DSRE_STAGE1_PROTOCOL.md")\n    return original if original.is_file() else Path("docs") / original.name\n\n\ndef rows(path):',
                ),
                (
                    '        Path("DSRE_STAGE1_PROTOCOL.md"),',
                    "        protocol_path(),",
                ),
            ]
            assert amendments["replacements"] == [
                {"old": a, "new": b} for a, b in allowed
            ]
            text = original.read_text()
            for old, new in allowed:
                assert text.count(old) == 1
                text = text.replace(old, new, 1)
            assert Path(path).read_text() == text
            assert sha(Path(path)) == amendments["new_sha256"]
        else:
            assert sha(current_source(path)) == expected, path
    for path, expected in load(root / "pre_evaluation_freeze.json")["sha256"].items():
        assert sha(current_source(path)) == expected, path
    return {
        "status": "PASS_FROZEN_SOURCE_AND_DOCUMENT_LOCATIONS",
        "source_paths": len(freeze["source_sha256"]),
        "document_content": "UNCHANGED",
        "post_execution_amendment": "verified document-path fallback only"
        if amendments
        else None,
    }


def audit(root):
    config = load(Path("config/dsre_stage1.json"))
    verify_sources(root)
    freeze = load(root / "experiment_freeze.json")
    assert sha(root / "qualified_pairs.jsonl") == freeze["table_sha256"]
    assert sha(root / "group_splits.json") == freeze["split_sha256"]
    sources = load(root / "source_members.json")
    for path, expected in sources.items():
        assert sha(Path(path)) == expected, path
    data = list(rows(root / "qualified_pairs.jsonl"))
    by_id = {p["id"]: p for p in data}
    exclusions = load(root / "qualification_exclusions.json")
    old = Path(config["source_root"])
    registration = load(old / "registration.json")
    registered = {
        f"{task}/{seed}/{condition}"
        for task in config["tasks"]
        for split in ("development", "confirmation")
        for seed in registration["seeds"][task][split]
        for condition in registration["conditions"][task]
    }
    assert set(by_id).isdisjoint(r["id"] for r in exclusions)
    assert set(by_id) | {r["id"] for r in exclusions} == registered
    raw_actions = history_states = 0
    raw_counts = defaultdict(Counter)
    for index, pair in enumerate(data):
        with gzip.open(pair["source"], "rt") as stream:
            raw = json.load(stream)
        metadata = load(Path(pair["outcomes_source"]))
        initial = bool(raw["prefix"][-1]["success"])
        assert initial == pair["initial_success"]
        assert independently_project(raw["prefix"]) == pair["features"]
        assert independently_project(raw["prefix"], True) == pair["coarse_features"]
        extra = raw["prefix"][-1]["observation"]["extra"]
        grasp = extra.get("is_grasped", [None])[0]
        assert pair["privileged_features"] == pair["features"] + [
            grasp,
            raw["prefix"][-1]["robot_object_contact"],
        ]
        assert pair["checkpoint_time"] == raw["prefix"][-1]["time"]
        assert value_sha(raw["prefix_actions"]) == pair["history_hash"]
        assert len(raw["prefix_actions"]) + 1 == len(raw["prefix"])
        observed_outcomes = []
        for action in ("continue", "recover"):
            trace = raw["traces"][action + "/fresh_prefix"]
            reference = raw["traces"][action + "/reference"]
            row = next(
                r
                for r in metadata
                if r["route"] == "fresh_prefix" and r["action"] == action
            )
            assert (
                trace["controller_memory"]
                == reference["controller_memory"]
                == raw["snapshot"]["custom"]
            )
            assert row["prefix_ok"] and reference["prefix_ok"]
            assert row["model_hash"] == value_sha(row["model"])
            assert row["history_hash"] == pair["history_hash"]
            assert (
                row["actions"] == row["expected_actions"] and len(row["actions"]) == 70
            )
            assert len(trace["frames"]) == len(reference["frames"]) == 70
            for history in (trace["prefix_history"], reference["prefix_history"]):
                assert len(history) == len(raw["prefix"])
                for a, b in zip(history, raw["prefix"], strict=True):
                    same_state(a, b)
                    history_states += 1
            same_state(raw["prefix"][-1], trace["start"])
            for i, (a, b) in enumerate(
                zip(trace["frames"], reference["frames"], strict=True)
            ):
                same_state(a["state"], b["state"])
                assert (
                    abs(a["state"]["time"] - trace["start"]["time"] - (i + 1) * 0.05)
                    < 1e-8
                )
            terminal = bool(trace["frames"][-1]["state"]["success"])
            assert terminal == row["success"] == pair["outcomes"][action + "_value"]
            assert pair["new_first_hits"][action] == (
                not initial and any(f["state"]["success"] for f in trace["frames"])
            )
            assert row["first_hit"] == next(
                (j + 1 for j, f in enumerate(trace["frames"]) if f["state"]["success"]),
                None,
            )
            observed_outcomes.append(terminal)
            raw_actions += 1
        name = ["neither", "continue_only", "recover_only", "both"][
            int(observed_outcomes[0]) + 2 * int(observed_outcomes[1])
        ]
        raw_counts[pair["task"]].update(
            pairs=1, **{name: 1}, initially_successful=int(initial)
        )
        if index % 100 == 0:
            print(
                json.dumps({"independently_audited_raw_pairs": index + 1}), flush=True
            )
    for excluded in exclusions:
        path = Path(excluded["source"]) / "traces.json.gz"
        with gzip.open(path, "rt") as stream:
            raw = json.load(stream)
        assert any(
            raw["traces"][a + "/reference"].get("controller_memory") is None
            or raw["traces"][a + "/reference"].get("prefix_history") is None
            or raw["traces"][a + "/fresh_prefix"].get("prefix_history") is None
            for a in ("continue", "recover")
        )
    prevalence = load(root / "paired_outcome_prevalence.json")
    for task, counts in raw_counts.items():
        assert all(prevalence[task][k] == v for k, v in counts.items())
    totals = defaultdict(lambda: np.zeros(9))
    cluster = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: np.zeros(9))))
    exact_certificates = greedy_certificates = predictions_checked = equivalences = 0
    fields = [
        "episodes",
        "emitted",
        "acceptable",
        "success",
        "unacceptable",
        "regret",
        "literal_sum",
        "inadequacy",
        "neither_recommended",
    ]
    for model_path in sorted((root / "crossfit").glob("*.model.json")):
        model = load(model_path)
        assert (
            sha(model_path.with_name(model_path.name.replace(".model.json", ".jsonl")))
            == model["prediction_sha256"]
        )
        assert not set(model["reference_groups"]) & set(model["evaluation_groups"])
        assert not set(model["reference_ids"]) & set(model["evaluation_ids"])
        assert {by_id[i]["group"] for i in model["reference_ids"]} == set(
            model["reference_groups"]
        )
        assert {by_id[i]["group"] for i in model["evaluation_ids"]} == set(
            model["evaluation_groups"]
        )
        variant, task = model["scope"]["channels"], model["scope"]["task"]
        ref = [
            {
                "id": i,
                "features": variant_features(by_id[i], variant),
                "outcomes": by_id[i]["outcomes"],
                "qualified": True,
            }
            for i in model["reference_ids"]
        ]
        table = {"scope": model["scope"], "rows": ref}
        certificates_path = model_path.with_name(
            model_path.name.replace(".model.json", ".certificates.json")
        )
        assert sha(certificates_path) == model["certificates_sha256"]
        for entry in load(certificates_path).values():
            c, query = entry["certificate"], entry["query"]
            reference_by_id = {r["id"]: r for r in ref}
            for witness in c["witnesses"]:
                for state in witness["states"]:
                    actual = reference_by_id[state["id"]]
                    assert (
                        state["features"] == actual["features"]
                        and state["outcomes"] == actual["outcomes"]
                    )
                    assert state["acceptable"] == [
                        a
                        for a in ("continue", "recover")
                        if actual["outcomes"][a + "_value"]
                    ]
            if entry["method"] == "DSRE":
                verify_certificate(table, query, c, model["minimum_support"])
                exact_certificates += 1
            elif c["action"]:
                names = model["scope"]["features"]
                selected = [names.index(f["feature"]) for f in c["evidence"]]
                matched = [r for r in ref if compatible(r, query["features"], selected)]
                assert len(matched) == c["support"] >= model["minimum_support"]
                assert all(r["outcomes"][c["action"] + "_value"] for r in matched)
                assert len(c["witnesses"]) == len(selected)
                for w in c["witnesses"]:
                    bad = next(r for r in ref if r["id"] == w["states"][0]["id"])
                    remaining = [
                        i for i in selected if names[i] != w["removed"]["feature"]
                    ]
                    assert (
                        compatible(bad, query["features"], remaining)
                        and not bad["outcomes"][c["action"] + "_value"]
                    )
                greedy_certificates += 1
        path = model_path.with_name(model_path.name.replace(".model.json", ".jsonl"))
        comparison = defaultdict(dict)
        for prediction in rows(path):
            pair = by_id[prediction["id"]]
            assert prediction["id"] in model["evaluation_ids"]
            x = variant_features(pair, variant, True)
            assert prediction["query_features"] == x
            rec = prediction["recommendation"]
            action = rec["action"]
            selected = [
                model["scope"]["features"].index(f["feature"]) for f in rec["evidence"]
            ]
            assert len(set(selected)) == len(selected)
            assert all(
                x[i] is not None and x[i] == f["value"]
                for i, f in zip(selected, rec["evidence"], strict=True)
            )
            method, point = prediction["method"], prediction["point"]
            if action and not method.startswith("B0_"):
                matched = [r for r in ref if compatible(r, x, selected)]
                assert len(matched) == rec["support"] >= model["minimum_support"]
                if (
                    method in ("DSRE", "B6_greedy", "B7_exact_rule")
                    or method == "B5_mean"
                    and prediction["target"] == 1
                ):
                    assert all(r["outcomes"][action + "_value"] for r in matched)
                elif method != "B4_policy":
                    assert (
                        sum(r["outcomes"][action + "_value"] for r in matched)
                        / len(matched)
                        >= prediction["target"]
                    )
                if method == "B1_one":
                    assert len(selected) <= 1
                if method == "B1_two":
                    assert len(selected) <= 2
                if method.startswith("B2_depth"):
                    assert len(selected) <= int(method[-1])
                if method == "B2_pruned":
                    assert len(selected) <= 3
            emitted = int(action is not None)
            successful = int(pair["outcomes"][action + "_value"]) if emitted else 0
            best = max(pair["outcomes"].values())
            score = np.array(
                [
                    1,
                    emitted,
                    successful,
                    successful,
                    emitted - successful,
                    int(best) - successful if emitted else 0,
                    len(selected) if emitted else 0,
                    emitted - successful,
                    int(emitted and not best),
                ]
            )
            key = variant + "/" + task + "/" + method + "/" + point
            totals[key] += score
            cluster[variant + "/" + task][method + "/" + point][pair["group"]] += score
            predictions_checked += 1
            if (method, point) in [
                ("DSRE", "primary"),
                ("B7_exact_rule", "primary"),
                ("B5_mean", "mean_1"),
            ]:
                comparison[pair["id"]][method] = (
                    action,
                    rec["evidence"],
                    rec["support"] if action else 0,
                )
        for items in comparison.values():
            assert items["DSRE"] == items["B7_exact_rule"] == items["B5_mean"]
            equivalences += 1
    saved = load(root / "metrics.json")
    full_checked = 0
    for record in load(root / "full_table_certificates.json"):
        query = record["query"]
        reference = [
            {
                "id": p["id"],
                "features": variant_features(p, record["variant"]),
                "outcomes": p["outcomes"],
                "qualified": True,
            }
            for p in data
            if p["task"] == record["task"]
        ]
        verify_certificate(
            {"scope": query["scope"], "rows": reference},
            query,
            record["certificate"],
            record["minimum_support"],
        )
        full_checked += 1
    for key, counts in totals.items():
        assert dict(zip(fields, map(int, counts), strict=True)) == saved[key]["counts"]
    ratios = {
        "coverage": (1, 0),
        "acceptable_accuracy": (2, 1),
        "absolute_success_given_recommendation": (3, 1),
        "unacceptable_frequency": (4, 1),
        "mean_regret_given_recommendation": (5, 1),
        "mean_literals_given_recommendation": (6, 1),
        "successful_recommendations_per_episode": (3, 0),
    }
    intervals = 0
    for scope, methods in cluster.items():
        names = sorted(methods)
        groups = sorted({g for m in methods.values() for g in m})
        array = np.asarray([[methods[name][g] for name in names] for g in groups])
        rng = np.random.default_rng(config["bootstrap_seed"])
        chosen = rng.integers(
            len(groups), size=(config["bootstrap_draws"], len(groups))
        )
        weight = np.zeros((len(chosen), len(groups)), dtype=int)
        for i, draw in enumerate(chosen):
            np.add.at(weight[i], draw, 1)
        samples = np.einsum("bi,imf->bmf", weight, array, optimize=True)
        for j, name in enumerate(names):
            if not name.endswith("/primary"):
                continue
            key = scope + "/" + name
            for metric, (n, d) in ratios.items():
                denominator = totals[key][d]
                expected = saved[key]["rates"][metric]
                point = float(totals[key][n] / denominator) if denominator else None
                assert point == expected["value"]
                valid = samples[:, j, d] > 0
                enough = d == 0 or (array[:, j, 1] > 0).sum() >= 10
                if valid.any() and enough:
                    interval = np.quantile(
                        samples[valid, j, n] / samples[valid, j, d], [0.025, 0.975]
                    )
                    assert np.allclose(
                        interval, expected["parent_percentile95"], rtol=0, atol=1e-12
                    )
                    intervals += 1
                else:
                    assert expected["parent_percentile95"] is None
    # Independent high-precision arithmetic checks of the calibration utility.
    from dual_rec.dsre.calibration import upper_bound

    with localcontext() as ctx:
        ctx.prec = 70
        for n, k in [(10, 1), (42, 2), (200, 10)]:
            low, high = Decimal(0), Decimal(1)
            delta = Decimal(".0125")
            for _ in range(160):
                p = (low + high) / 2
                cdf = sum(
                    Decimal(math.comb(n, j)) * p**j * (1 - p) ** (n - j)
                    for j in range(k + 1)
                )
                if cdf > delta:
                    low = p
                else:
                    high = p
            assert abs(float(high) - upper_bound(k, n, 0.0125)) < 1e-12
    assert upper_bound(0, 42, 0.0125) <= 0.1 < upper_bound(0, 41, 0.0125)
    plan = load(root / "prospective_fresh_seed_plan.json")
    ids = [r["parent_id"] for r in plan["parents"]]
    assert len(ids) == len(set(ids)) == 800
    assert not set(ids) & {r["group"] for r in data}
    assert Counter((p["task"], p["split"]) for p in plan["parents"]) == {
        (t, s): 200 for t in config["tasks"] for s in ("calibration", "confirmation")
    }
    feasibility = load(root / "calibration_feasibility.json")
    assert (
        feasibility["all_deployment_actions_disabled"]
        and feasibility["zero_error_assigned_n"] == 42
    )
    report = {
        "status": "PASS_INDEPENDENT_RAW_FINITE_AND_NUMERICAL_AUDIT",
        "scope": "Independent code paths in the same session; no independent human review",
        "source_hashes": len(sources),
        "qualified_raw_pairs": len(data),
        "excluded_incomplete_retained_history_pairs": len(exclusions),
        "raw_fresh_action_outcomes": raw_actions,
        "full_history_state_comparisons": history_states,
        "independent_feature_projection": "PASS_PRIMARY_PRIVILEGED_COARSE",
        "fold_prediction_rows_verified": predictions_checked,
        "all_operating_point_count_tables": len(totals),
        "exact_crossfit_certificates_verified_by_exhaustive_and_hitting_oracles": exact_certificates,
        "full_table_certificates_independently_verified": full_checked,
        "valid_greedy_certificates_with_witnesses": greedy_certificates,
        "DSRE_B7_B5at1_exact_prediction_equivalences": equivalences,
        "primary_parent_intervals_recomputed": intervals,
        "calibration_bound_high_precision_checks": "PASS",
        "prospective_only_fresh_parent_plan": len(ids),
        "independent_calibration": "NOT_RUN_NO_DISTRIBUTIONAL_CLAIM",
        "blueprint": "MISSING_CONSISTENCY_NOT_VERIFIABLE",
    }
    (root / "independent_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--sources-only", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed; use the read-only finish verify stage")
    if args.sources_only:
        result = verify_sources(args.root)
        (args.root / "post_relocation_source_audit.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        print(json.dumps(result))
    else:
        audit(args.root)
