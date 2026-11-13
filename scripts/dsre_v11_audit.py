"""Independent v1.1 checks; never imports the main certificate solver or router."""

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_audit import independently_project, verify_sources

from dual_rec.dsre.oracle import verify_certificate
from dual_rec.dsre.risk_oracle import ceiling, exact_binomial_upper, good, matches, rule


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def audit_data(root):
    config = load(Path("config/dsre_v11.json"))
    old = Path(config["input_root"])
    assert (
        sha(old / "completion_manifest.json")
        == "ed602f486794e7e500eaa4311df901a972c5b7f9e69263b3f01f1b87ae88e5ff"
    )
    seal = load(old / "completion_manifest.json")
    for name, expected in seal["sha256"].items():
        assert sha(old / name) == expected, name
    for name, expected in seal["source_sha256"].items():
        assert sha(Path(name)) == expected, name
    verify_sources(old)
    members = load(old / "source_members.json")
    for name, expected in members.items():
        assert sha(Path(name)) == expected, name
    data = [
        json.loads(line)
        for line in (old / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    assert sha(old / "qualified_pairs.jsonl") == config["table_sha256"]
    counts, source_outcomes = {}, 0
    for task in ("PickCube-v1", "PushCube-v1"):
        population = [r for r in data if r["task"] == task]
        category = Counter()
        for row in population:
            with gzip.open(row["source"], "rt") as stream:
                raw = json.load(stream)
            assert independently_project(raw["prefix"]) == row["features"]
            assert independently_project(raw["prefix"], True) == row["coarse_features"]
            extra = raw["prefix"][-1]["observation"]["extra"]
            assert row["privileged_features"] == row["features"] + [
                extra.get("is_grasped", [None])[0],
                raw["prefix"][-1]["robot_object_contact"],
            ]
            assert bool(raw["prefix"][-1]["success"]) == row["initial_success"]
            for action in ("continue", "recover"):
                route = raw["traces"][action + "/fresh_prefix"]
                reference = raw["traces"][action + "/reference"]
                assert (
                    route["controller_memory"]
                    == reference["controller_memory"]
                    == raw["snapshot"]["custom"]
                )
                assert len(route["frames"]) == len(reference["frames"]) == 70
                outcome = bool(route["frames"][-1]["state"]["success"])
                assert row["outcomes"][action + "_value"] == outcome
                source_outcomes += 1
            c, r = row["outcomes"].values()
            category.update(
                [
                    "both"
                    if c and r
                    else "continue_only"
                    if c
                    else "recover_only"
                    if r
                    else "neither"
                ]
            )
        counts[task] = {
            "rows": len(population),
            "seed_groups": len({r["group"] for r in population}),
            "outcomes": dict(category),
        }
    result = {
        "status": "PASS",
        "sealed_input_members": len(seal["sha256"]),
        "source_members": len(members),
        "qualified_pairs": len(data),
        "raw_action_outcomes": source_outcomes,
        "task_counts": counts,
        "raw_scope": "Recheck features, full branch presence, memory and terminal outcomes; prior sealed full-history fidelity audit preserved, not refitted",
    }
    save(root / "input_audit.json", result)
    print(json.dumps(result), flush=True)


def expected_baseline(method, beta, table, query, trees):
    """Independent stored-tree traversal and dictionary-only rule enumeration."""
    if method in ("S_strict", "B7_exact"):
        return rule(table, query, 0, strict=True)
    if method in ("B5_v11", "B1_two_v11"):
        return rule(
            table, query, beta, maximum_length=2 if method == "B1_two_v11" else None
        )
    if method.startswith("always_"):
        return {
            "action": method.removeprefix("always_"),
            "evidence": [],
            "support": len(table["rows"]),
        }
    x, names = query["features"], table["scope"]["features"]
    if method == "full_signature":
        selected = [i for i, v in enumerate(x) if v is not None]
    else:
        nodes = trees["B2_" + method.removeprefix("CART_")]
        node, selected = nodes[0], []
        while node["feature"] is not None:
            index = node["feature"]
            if x[index] is None:
                return None
            selected.append(index)
            node = nodes[node["right"] if x[index] else node["left"]]
    matched = [r for r in table["rows"] if matches(r, x, selected)]
    if len(matched) < 2:
        return None
    successes = [
        sum(action in good(r) for r in matched) for action in ("continue", "recover")
    ]
    choice = int(successes[1] > successes[0])
    if successes[choice] / len(matched) < 1 - beta:
        return None
    return {
        "action": ("continue", "recover")[choice],
        "evidence": [
            {"feature": names[i], "value": x[i]}
            for i in sorted(selected, key=lambda i: names[i])
        ],
        "support": len(matched),
    }


def verify_decision(table, decision, trees=None):
    method, beta, query, result = (
        decision[n] for n in ("method", "beta", "query", "result")
    )
    assert query["scope"] == table["scope"]
    if method == "DSRE_v11":
        strict = rule(table, query, 0, strict=True)
        risk = rule(table, query, beta) if strict is None else None
        expected = strict or risk
        tier = (
            "STRICT_FINITE_REFERENCE"
            if strict
            else "PROVISIONAL_RISK_RULE"
            if risk
            else "INSUFFICIENT"
        )
        status = "PROVISIONAL_UNCALIBRATED" if risk else tier
        assert result["tier"] == tier and result["status"] == status
        verify_certificate(table, query, result["strict"], 2)
        if risk:
            for field in (
                "action",
                "evidence",
                "support",
                "matched_ids",
                "unacceptable",
            ):
                assert result["provisional"][field] == risk[field], field
        if not strict:
            validate_insufficiency(table, query, result["strict"])
    else:
        expected = expected_baseline(method, beta, table, query, trees)
        if method == "S_strict":
            verify_certificate(table, query, result["certificate"], 2)
        if method in ("B5_v11", "B1_two_v11") and expected:
            for field in (
                "action",
                "evidence",
                "support",
                "matched_ids",
                "unacceptable",
            ):
                assert result["risk_rule"][field] == expected[field], field
    assert result["action"] == (expected["action"] if expected else None)
    if expected:
        for field in ("evidence", "support"):
            assert result[field] == expected[field], field
    else:
        assert not result["evidence"]
    assert result["calibration"] == "UNASSESSED" and result["deployable_action"] is None
    assert result["status"] not in ("CERTIFIED", "SAFE", "DEPLOYABLE")
    return True


def validate_insufficiency(table, query, certificate):
    x = query["features"]
    rows = [
        r
        for r in table["rows"]
        if matches(r, x, [i for i, v in enumerate(x) if v is not None])
    ]
    reasons = set()
    if len(rows) < 2:
        reasons.add("INSUFFICIENT_REFERENCE_SUPPORT")
    if any(None in r["outcomes"].values() or not r["qualified"] for r in rows):
        reasons.add("OUTCOME_UNCERTAINTY")
    if any(
        all(v is False for v in r["outcomes"].values()) and r["qualified"] for r in rows
    ):
        reasons.add("INADEQUATE_REPERTOIRE")
    if any(good(r) == {"continue"} for r in rows) and any(
        good(r) == {"recover"} for r in rows
    ):
        reasons.add("OBSERVATION_AMBIGUITY")
    if None in x:
        reasons.add("MISSING_OBSERVATIONS")
    assert set(certificate["reasons"]) == (
        reasons or {"INSUFFICIENT_REFERENCE_SUPPORT"}
    )


def independent_score(result, row, action):
    emitted = result["action"] is not None and action in ("all", result["action"])
    value = int(row["outcomes"][result["action"] + "_value"]) if emitted else 0
    return {
        "episodes": 1,
        "recommended": int(emitted),
        "abstained": int(result["action"] is None),
        "other_action": int(result["action"] is not None and not emitted),
        "adequate": value,
        "unacceptable": int(emitted and not value),
        "regret": int(emitted and not value and any(row["outcomes"].values())),
        "literals": len(result["evidence"]) if emitted else 0,
        "support": result["support"] if emitted else 0,
        "strict": int(emitted and result.get("tier") == "STRICT_FINITE_REFERENCE"),
        "provisional": int(emitted and result.get("tier") == "PROVISIONAL_RISK_RULE"),
        "status_errors": 0,
    }


def interval_equal(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert np.allclose(actual, expected, atol=1e-12, rtol=1e-12), (actual, expected)


def numerical_audit(root):
    assert "dual_rec.dsre.solver" not in sys.modules
    assert "dual_rec.dsre.risk" not in sys.modules
    config = load(Path("config/dsre_v11.json"))
    old = Path(config["input_root"])
    source = [
        json.loads(s) for s in (old / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    by_id = {r["id"]: r for r in source}
    mapping = load(old / "group_splits.json")
    tasks = ("PickCube-v1", "PushCube-v1")
    for task in tasks:
        ranked = sorted(
            {r["group"] for r in source if r["task"] == task},
            key=lambda g: hashlib.sha256(
                ("dsre-parent-fold-v1/" + g).encode()
            ).hexdigest(),
        )
        for index, group in enumerate(ranked):
            assert mapping[group] == index % 5
    observations = load(root / "observability.json")
    signature_checks = 0
    for name, p in observations.items():
        task, variant = name.split("/")
        field = {
            "pose_proprioception": "features",
            "plus_privileged": "privileged_features",
            "coarse_geometry": "coarse_features",
        }[variant]
        assert {r["id"] for r in p["table"]["rows"]} == {
            r["id"] for r in source if r["task"] == task
        }
        for r in p["table"]["rows"]:
            assert (
                r["features"] == by_id[r["id"]][field]
                and r["outcomes"] == by_id[r["id"]]["outcomes"]
            )
        independent = ceiling(p["table"])
        assert len(independent) == p["summary"]["groups"]
        for g in independent:
            measured = next(
                c for c in p["signatures"] if c["signature"] == g["signature"]
            )
            assert g["mass"] == measured["mass"]
            for kind in ("equal", "compatible"):
                assert g[kind]["good"] == measured[kind + "_good"]
                for cause in ("inadequate", "action_ambiguous", "unknown_outcomes"):
                    assert g[kind][cause] == measured[kind + "_causes"][cause]
                for label in (
                    "adequate",
                    "inadequate",
                    "action_ambiguous",
                    "overlap",
                    "unknown_outcomes",
                ):
                    relevant = [
                        c
                        for c in independent
                        if (
                            bool(c[kind]["good"])
                            if label == "adequate"
                            else c[kind][label]
                        )
                    ]
                    assert p["summary"][kind + "_" + label] == {
                        "groups": len(relevant),
                        "mass": sum(c["mass"] for c in relevant),
                    }
            expected_rule = rule(
                p["table"],
                {"scope": p["table"]["scope"], "features": g["signature"]},
                0,
                strict=True,
            )
            assert measured["strict_supported_rule_exists"] == bool(expected_rule)
            rows = [by_id[i] for i in measured["ids"]]
            scores = {
                a: sum(r["outcomes"][a + "_value"] for r in rows)
                for a in ("continue", "recover")
            }
            best = max(scores, key=scores.get)
            assert (
                measured["best_nonuniversal"]["unacceptable"]
                == len(rows) - scores[best]
            )
            witnesses = measured["compatible_causes"]
            if witnesses["inadequate_witness"]:
                assert not any(
                    by_id[witnesses["inadequate_witness"][0]]["outcomes"].values()
                )
            if witnesses["ambiguity_witness"]:
                a, b = [by_id[i] for i in witnesses["ambiguity_witness"]]
                assert good(a) and good(b) and not good(a) & good(b)
            signature_checks += 1
    outputs = []
    unique = 0
    historical_matches = 0
    certificate_checks = 0
    for path in sorted((root / "crossfit").glob("*.json")):
        part = load(path)
        task, fold = part["task"], part["fold"]
        model = load(
            old / "crossfit" / f"pose_proprioception__{task}__fold{fold}.model.json"
        )
        assert (
            sha(
                old / "crossfit" / f"pose_proprioception__{task}__fold{fold}.model.json"
            )
            == part["model_sha256"]
        )
        assert part["new_model_fits"] == 0
        expected_train = {
            r["id"] for r in source if r["task"] == task and mapping[r["group"]] != fold
        }
        assert (
            {r["id"] for r in part["table"]["rows"]}
            == expected_train
            == set(model["reference_ids"])
        )
        assert not set(part["reference_groups"]) & set(part["evaluation_groups"])
        for row in part["table"]["rows"]:
            assert (
                row["features"] == by_id[row["id"]]["features"]
                and row["outcomes"] == by_id[row["id"]]["outcomes"]
            )
        for d in part["decisions"].values():
            verify_decision(part["table"], d, model["trees"])
            unique += 1
            certificate_checks += int(d["method"] in ("DSRE_v11", "S_strict"))
        old_predictions = [
            json.loads(line)
            for line in (
                old / "crossfit" / f"pose_proprioception__{task}__fold{fold}.jsonl"
            )
            .read_text()
            .splitlines()
        ]
        old_map = {
            (p["id"], p["method"], p["point"]): p["recommendation"]
            for p in old_predictions
        }
        for p in part["predictions"]:
            pair = by_id[p["id"]]
            assert (
                p["id"] in model["evaluation_ids"]
                and p["group"] == pair["group"]
                and mapping[p["group"]] == fold
            )
            d = part["decisions"][p["decision_id"]]
            assert d["query"]["features"] == pair["features"]
            assert (p["method"], p["beta"]) == (d["method"], d["beta"])
            r = d["result"]
            method = p["method"]
            old_method = (
                "DSRE"
                if method == "S_strict"
                else "B7_exact_rule"
                if method == "B7_exact"
                else "B2_" + method.removeprefix("CART_")
                if method.startswith("CART_")
                else None
            )
            if old_method:
                point = (
                    "primary"
                    if method in ("S_strict", "B7_exact")
                    else "mean_" + f"{1 - p['beta']:g}"
                )
                prior = old_map[(p["id"], old_method, point)]
                assert all(r[f] == prior[f] for f in ("action", "evidence", "support"))
                historical_matches += 1
            outputs.append(p | {"result": r})
    expected_jobs = {
        ("S_strict", 0.0),
        ("B7_exact", 0.0),
        ("always_continue", None),
        ("always_recover", None),
        ("DSRE_v11", 0.1),
        ("DSRE_v11", 0.05),
    }
    expected_jobs |= {
        (m, b)
        for b in config["descriptive_frontier_betas"]
        for m in (
            "B5_v11",
            "B1_two_v11",
            "full_signature",
            "CART_depth1",
            "CART_depth2",
            "CART_depth3",
        )
    }
    seen = Counter((p["id"], p["method"], p["beta"]) for p in outputs)
    assert len(outputs) == len(source) * len(expected_jobs)
    assert all(seen[(r["id"], m, b)] == 1 for r in source for m, b in expected_jobs)
    for task, full in load(root / "full_table_router.json").items():
        table = observations[task + "/pose_proprioception"]["table"]
        for output in full["outputs"]:
            verify_decision(
                table,
                {
                    "method": "DSRE_v11",
                    "beta": 0.1,
                    "query": {"scope": table["scope"], "features": output["signature"]},
                    "result": output["result"],
                },
            )
            certificate_checks += 1
    uncertainty_checks, paired_checks = audit_uncertainty(root, source, outputs)
    feasibility = load(root / "calibration_feasibility.json")
    for name, entry in feasibility["strata_by_method"].items():
        task, method, action = name.split("|")
        selected = (
            [
                p
                for p in outputs
                if p["task"] == task
                and p["beta"] is not None
                and p["method"] + "/" + f"{p['beta']:g}" == method
                and p["result"]["action"] == action
            ]
            if not method.startswith("always_")
            else []
        )
        assert len(selected) == entry["assigned_checkpoints"]
        assert entry["assignment_frequency"] == len(selected) / 422
        assert entry["expected_from_200"] == 200 * len(selected) / 422
        assert entry["deployment_enabled"] is False
    for k, n in ((0, 0), (0, 1), (0, 41), (0, 42), (1, 42), (7, 200), (10, 10)):
        upper = exact_binomial_upper(k, n, 0.0125)
        if k == 0 and n:
            assert abs(upper - (1 - 0.0125 ** (1 / n))) < 1e-12
    assert (
        exact_binomial_upper(0, 41, 0.0125) > 0.1 >= exact_binomial_upper(0, 42, 0.0125)
    )
    review_checks = audit_review(root, source, outputs)
    result = {
        "status": "PASS",
        "signature_groups": signature_checks,
        "unique_first_rule_outputs": unique,
        "certificate_checks": certificate_checks,
        "prediction_rows": len(outputs),
        "historical_strict_B7_and_tree_matches": historical_matches,
        "uncertainty_intervals": uncertainty_checks,
        "paired_checks": paired_checks,
        "independent_calibration": "NONE; Decimal synthetic checks only",
        "independence": "Separate code paths in one session, not external human review",
        "main_solver_imported": False,
        "derived_review_checks": review_checks,
    }
    save(root / "independent_audit.json", result)
    print(json.dumps(result), flush=True)


def audit_review(root, source, outputs):
    """Verify post-analysis wrapper identities, exact-risk matches and witnesses."""
    import csv

    by_id = {r["id"]: r for r in source}
    per_input = defaultdict(dict)
    for p in outputs:
        point = (
            p["method"]
            + "/"
            + (f"{p['beta']:g}" if p["beta"] is not None else "boundary")
        )
        per_input[p["id"]][point] = p["result"]
    checks = 0
    splits = load(Path("results/dsre-stage1/20261113T144253Z/group_splits.json"))
    diagnostics = load(root / "query_support_diagnostics.json")
    assert len(diagnostics["records"]) == len(source)
    for r in diagnostics["records"]:
        x = by_id[r["id"]]["features"]
        train = [
            p
            for p in source
            if p["task"] == r["task"] and splits[p["group"]] != r["fold"]
        ]
        assert r["unseen_exact_signature"] == all(p["features"] != x for p in train)
        support = sum(
            matches(p, x, [i for i, v in enumerate(x) if v is not None]) for p in train
        )
        assert r["conservative_full_support"] == support
        assert r["full_support_below_two"] == (support < 2)
        checks += 1
    for name, measured in load(root / "wrapper_equivalence.json").items():
        task, beta = name.split("/beta=")
        equal = provisional = peq = total = 0
        for id, methods in per_input.items():
            if by_id[id]["task"] != task:
                continue
            total += 1
            s, b, r = (
                methods[k]
                for k in ("S_strict/0", "B1_two_v11/" + beta, "DSRE_v11/" + beta)
            )
            selected = s if s["action"] or b["action"] is None else b
            equal += all(selected[f] == r[f] for f in ("action", "evidence", "support"))
            if r["tier"] == "PROVISIONAL_RISK_RULE":
                provisional += 1
                peq += all(
                    methods["B5_v11/" + beta][f] == r[f]
                    for f in ("action", "evidence", "support")
                )
        assert (total, equal, provisional, peq) == (
            measured["checkpoints"],
            measured["strict_then_two_literal_equal_decisions"],
            measured["risk_tier_cases"],
            measured["risk_tier_exact_B5_matches"],
        )
        checks += total
    metrics = load(root / "metrics.json")
    with (root / "frontier.csv").open() as stream:
        frontier = list(csv.DictReader(stream))
    for point in frontier:
        cell = metrics[point["task"] + "|" + point["method_point"] + "|all|all_starts"]
        assert int(point["recommended"]) == cell["counts"]["recommended"]
        assert int(point["unacceptable"]) == cell["counts"]["unacceptable"]
        for field in ("coverage", "unacceptable_rate", "mean_literals"):
            interval_equal(
                float(point[field]) if point[field] else None,
                cell["rates"][field]["value"],
            )
        checks += 1
    for name, result in load(root / "matched_risk_frontier.json").items():
        task, target = name.split("|")
        count = metrics[f"{task}|{target}|all|all_starts"]["counts"]
        expected = []
        for point in frontier:
            n, k = int(point["recommended"]), int(point["unacceptable"])
            if (
                point["task"] == task
                and point["method_point"] != target
                and n
                and count["recommended"]
                and k * count["recommended"] == count["unacceptable"] * n
            ):
                expected.append(point["method_point"])
        assert sorted(expected) == sorted(
            p["method_point"] for p in result["exact_risk_matches"]
        )
        checks += 1
    witness_file = load(root / "witness_examples.json")
    for w in witness_file["signature_witnesses"]:
        for record in w["records"]:
            assert record["outcomes"] == by_id[record["id"]]["outcomes"]
            assert all(
                a is None or b is None or a == b
                for a, b in zip(record["features"], w["signature"], strict=True)
            )
        sets = [good(by_id[r["id"]]) for r in w["records"]]
        if w["kind"] == "INADEQUATE_REPERTOIRE":
            assert not sets[0]
        else:
            assert sets[0] and sets[1] and not sets[0] & sets[1]
        checks += 1
    frozen = load(root / "frozen_router.json")
    assert (
        frozen["router"]["sha256"]
        == hashlib.sha256(
            json.dumps(frozen["definition"], sort_keys=True).encode()
        ).hexdigest()
    )
    assert set(frozen["router"]["training_parent_ids"]) == {r["group"] for r in source}
    assert frozen["definition"]["full_table_outputs_sha256"] == sha(
        root / "full_table_router.json"
    )
    assert all(
        g["action"] is None and g["reason"] == "CALIBRATION_INSUFFICIENT"
        for g in frozen["current_gates"]
    )
    return checks + 4


def audit_uncertainty(root, source, outputs):
    """Rebuild every numerator, group matrix and registered percentile calculation."""
    tasks = ("PickCube-v1", "PushCube-v1")
    config = load(Path("config/dsre_v11.json"))
    names = [
        g for t in tasks for g in sorted({r["group"] for r in source if r["task"] == t})
    ]
    gindex = {g: i for i, g in enumerate(names)}
    by_id = {r["id"]: r for r in source}
    matrices = defaultdict(
        lambda: defaultdict(lambda: np.zeros(len(names), dtype=np.int64))
    )
    per_input = defaultdict(dict)
    for p in outputs:
        row = by_id[p["id"]]
        point = (
            p["method"]
            + "/"
            + (f"{p['beta']:g}" if p["beta"] is not None else "boundary")
        )
        per_input[row["id"]][point] = p["result"]
        for task in (row["task"], "combined"):
            for action in ("all", "continue", "recover"):
                for pop in ("all_starts", "failed_starts"):
                    if pop == "failed_starts" and row["initial_success"]:
                        continue
                    cell = f"{task}|{point}|{action}|{pop}"
                    for field, value in independent_score(
                        p["result"], row, action
                    ).items():
                        matrices[cell][field][gindex[row["group"]]] += value
    blocks = []
    plan = load(root / "uncertainty_plan.json")
    for index, task in enumerate(tasks):
        ng = len([g for g in names if g.startswith(task + "/")])
        draws = np.random.default_rng(config["bootstrap_seed"] + index).integers(
            0, ng, (config["bootstrap_draws"], ng)
        )
        assert (
            hashlib.sha256(draws.tobytes()).hexdigest()
            == plan["indices"][task]["draws_sha256"]
        )
        blocks.append(np.stack([np.bincount(d, minlength=ng) for d in draws]))
    weights = np.concatenate(blocks, axis=1)
    metrics = load(root / "metrics.json")
    checks = 0
    ratio_fields = {
        "coverage": ("recommended", "episodes"),
        "unacceptable_rate": ("unacceptable", "recommended"),
        "absolute_success_given_recommendation": ("adequate", "recommended"),
        "successful_recommendations_per_checkpoint": ("adequate", "episodes"),
        "mean_literals": ("literals", "recommended"),
        "mean_support": ("support", "recommended"),
        "mean_regret": ("regret", "recommended"),
        "strict_fraction_recommended": ("strict", "recommended"),
        "provisional_fraction_recommended": ("provisional", "recommended"),
    }
    assert set(metrics) == set(matrices)
    for cell, fields in matrices.items():
        actual = metrics[cell]
        assert actual["counts"] == {f: int(v.sum()) for f, v in fields.items()}
        assert actual["seed_groups"] == int((fields["episodes"] > 0).sum())
        assigned = int((fields["recommended"] > 0).sum())
        assert actual["recommending_seed_groups"] == assigned
        for name, (num, den) in ratio_fields.items():
            n, d = fields[num], fields[den]
            ns, ds = weights @ n, weights @ d
            valid = ds > 0
            sparse = den == "recommended" and assigned < 10
            expected = (
                np.percentile(ns[valid] / ds[valid], [2.5, 97.5]).tolist()
                if valid.any() and not sparse
                else None
            )
            interval_equal(actual["rates"][name]["parent_percentile95"], expected)
            interval_equal(
                actual["rates"][name]["value"],
                float(n.sum() / d.sum()) if d.sum() else None,
            )
            assert actual["rates"][name]["sparse_stratum"] == sparse
            checks += 1
    paired = load(root / "paired_comparisons.json")
    paired_checks = 0
    for label, actual in paired.items():
        task, contrast = label.split("|")
        left, right = contrast.split(" minus ")
        a = matrices[f"{task}|{left}|all|all_starts"]
        b = matrices[f"{task}|{right}|all|all_starts"]
        for name, difference in actual["differences"].items():
            num, den = ratio_fields[name]
            an, ad, bn, bd = (weights @ x for x in (a[num], a[den], b[num], b[den]))
            valid = (ad > 0) & (bd > 0)
            sparse = (
                den == "recommended"
                and min(int((a[den] > 0).sum()), int((b[den] > 0).sum())) < 10
            )
            expected = (
                np.percentile(
                    an[valid] / ad[valid] - bn[valid] / bd[valid], [2.5, 97.5]
                ).tolist()
                if valid.any() and not sparse
                else None
            )
            interval_equal(difference["parent_percentile95"], expected)
            point = (
                float(a[num].sum() / a[den].sum() - b[num].sum() / b[den].sum())
                if a[den].sum() and b[den].sum()
                else None
            )
            interval_equal(difference["value"], point)
            paired_checks += 1
        common = np.zeros((len(names), 3), dtype=int)
        equal = provisional = peq = 0
        for row in source:
            if task != "combined" and row["task"] != task:
                continue
            r, s = per_input[row["id"]][left], per_input[row["id"]][right]
            same = all(r[f] == s[f] for f in ("action", "evidence", "support"))
            equal += same
            if r.get("tier") == "PROVISIONAL_RISK_RULE":
                provisional += 1
                peq += same
            if r["action"] and s["action"]:
                common[gindex[row["group"]]] += [
                    1,
                    len(r["evidence"]) - len(s["evidence"]),
                    int(r["action"] == s["action"]),
                ]
        assert (
            actual["equal_action_evidence_support"],
            actual["provisional_cases"],
            actual["provisional_equal"],
        ) == (equal, provisional, peq)
        assert actual["common_recommendations"] == int(common[:, 0].sum())
        assert actual["common_action_agreement"] == int(common[:, 2].sum())
        bs = weights @ common
        valid = bs[:, 0] > 0
        expected = (
            np.percentile(bs[valid, 1] / bs[valid, 0], [2.5, 97.5]).tolist()
            if valid.any() and (common[:, 0] > 0).sum() >= 10
            else None
        )
        interval_equal(actual["common_literal_parent95"], expected)
        paired_checks += 1
    return checks, paired_checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-only", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.data_only:
        audit_data(args.root)
    else:
        numerical_audit(args.root)
