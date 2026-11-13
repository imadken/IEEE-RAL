"""Independent reference-only selection, rule, witness and parent-level statistics audit."""

import argparse
import ast
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from dual_rec.dsre.repair_oracle import (
    Oracle,
    action_set,
    features,
    finite_mass,
    select,
)


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def frozen_sources(root):
    freeze = load(root / "experiment_freeze.json")
    amendment = (
        load(root / "source_amendment.json")
        if (root / "source_amendment.json").exists()
        else None
    )
    for name, expected in freeze["source_sha256"].items():
        if amendment is None or name != amendment["source"]:
            assert sha(Path(name)) == expected, name
            continue
        original = Path(amendment["original_copy"]).read_text()
        assert (
            hashlib.sha256(original.encode()).hexdigest()
            == expected
            == amendment["original_sha256"]
        )
        for r in amendment["replacements"]:
            assert original.count(r["old"]) == 1
            original = original.replace(r["old"], r["new"], 1)
        assert ast.dump(ast.parse(original)) == ast.dump(
            ast.parse(Path(name).read_text())
        )
        assert sha(Path(name)) == amendment["final_sha256"]
    for name, expected in freeze["input_sha256"].items():
        assert sha(Path(name)) == expected, name
    assert (
        Path("docs/DSRE_STAGE1_EVIDENCE_REPAIR_METHOD.md")
        .read_text()
        .startswith((root / "registered_method.md").read_text())
    )
    return len(freeze["source_sha256"]) + len(freeze["input_sha256"])


def tree_expected(table, groups, query, nodes, target):
    node = nodes[0]
    indices = []
    names = table["scope"]["features"]
    x = query["features"]
    while node["feature"] is not None:
        feature = node["feature"]
        if x[feature] is None:
            return None
        indices.append(feature)
        node = nodes[node["right"] if x[feature] else node["left"]]
    matched = [
        r
        for r in table["rows"]
        if all(r["features"][i] in (None, x[i]) for i in indices)
    ]
    if len(matched) < 2:
        return None
    counts = {
        a: sum(a in action_set(r) for r in matched) for a in ("continue", "recover")
    }
    choice = max(counts, key=counts.get)
    if (
        counts[choice] / len(matched) < target
        or len({groups[r["id"]] for r in matched}) < 2
    ):
        return None
    return {
        "action": choice,
        "evidence": [
            {"feature": names[i], "value": x[i]}
            for i in sorted(indices, key=lambda i: names[i])
        ],
        "support": len(matched),
        "independent_parents": len({groups[r["id"]] for r in matched}),
    }


def check_tree_training(table, nodes, maximum_depth):
    """Independently verify Gini gains on the complete actual training vectors."""
    assert all(None not in r["features"] for r in table["rows"])
    names = table["scope"]["features"]

    def impurity(rows):
        counts = Counter(tuple(sorted(action_set(r))) for r in rows)
        return (
            len(rows) * (1 - sum((n / len(rows)) ** 2 for n in counts.values()))
            if rows
            else 0
        )

    def visit(index, rows, available, remaining):
        node = nodes[index]
        base = impurity(rows)
        assert abs(base - node["impurity"]) < 1e-9
        possibilities = []
        for i in available:
            left = [r for r in rows if not r["features"][i]]
            right = [r for r in rows if r["features"][i]]
            if min(len(left), len(right)) >= 2:
                possibilities.append(
                    (impurity(left) + impurity(right), names[i], i, left, right)
                )
        if (
            not remaining
            or base <= 1e-12
            or not possibilities
            or min(c[0] for c in possibilities) >= base - 1e-12
        ):
            assert node["feature"] is None
            return
        assert node["feature"] is not None
        chosen = next(c for c in possibilities if c[2] == node["feature"])
        assert chosen[0] <= min(c[0] for c in possibilities) + 1e-9
        available = [i for i in available if i != node["feature"]]
        visit(node["left"], chosen[3], available, remaining - 1)
        visit(node["right"], chosen[4], available, remaining - 1)

    visit(0, table["rows"], list(range(len(names))), maximum_depth)


def check_model(root, path, by_id, splits):
    m = load(path)
    table = m["table"]
    groups = m["parent_groups"]
    oracle = Oracle(table, groups)
    train = {
        r["id"]
        for r in by_id.values()
        if r["task"] == m["task"] and splits[r["group"]] != m["fold"]
    }
    assert {r["id"] for r in table["rows"]} == train
    assert groups == {id: by_id[id]["group"] for id in train}
    assert all(r["qualified"] for r in table["rows"])
    for row in table["rows"]:
        assert (
            row["features"] == features(by_id[row["id"]], m["selected"])
            and row["outcomes"] == by_id[row["id"]]["outcomes"]
        )
    for depth, nodes in m["trees"].items():
        check_tree_training(table, nodes, int(depth))
    checked = 0
    for decision in m["decisions"].values():
        query, result, method = (decision[k] for k in ("query", "result", "method"))
        if method in ("DSRE", "DSRE_partial"):
            assert oracle.verify(query, result["diagnosis"])
            assert all(
                result[k] == result["diagnosis"][k]
                for k in (
                    "action",
                    "evidence",
                    "support",
                    "independent_parents",
                    "status",
                )
            )
            references = {r["id"]: r for r in table["rows"]}
            for w in result["diagnosis"]["certificate"]["witnesses"]:
                for state in w["states"]:
                    assert state["features"] == references[state["id"]]["features"]
                    assert state["outcomes"] == references[state["id"]]["outcomes"]
            expected = oracle.rule(query)
        elif method == "S_then_B1_two":
            expected = oracle.rule(query) or oracle.rule(query, 0.1, 2)
        elif method in ("B7", "B1_one_strict", "B1_two_strict", "B5_beta10"):
            expected = oracle.rule(
                query,
                0.1 if method == "B5_beta10" else 0,
                1
                if method == "B1_one_strict"
                else 2
                if method == "B1_two_strict"
                else None,
            )
        elif method.startswith("B0_"):
            expected = {
                "action": method.removeprefix("B0_"),
                "evidence": [],
                "support": len(table["rows"]),
                "independent_parents": len(set(groups.values())),
            }
        else:
            expected = tree_expected(
                table,
                groups,
                query,
                m["trees"][method[4]],
                0.9 if method.endswith("beta10") else 1,
            )
        assert result["action"] == (expected["action"] if expected else None)
        if expected:
            for field in ("action", "evidence", "support", "independent_parents"):
                assert result[field] == expected[field], (path, method, field)
            if result["status"] == "STRICT_FINITE_REFERENCE":
                assert expected.get("unacceptable", 0) == 0
        assert (
            result["deployable_action"] is None
            and result["calibration"] == "UNASSESSED"
        )
        assert result["status"] in (
            "STRICT_FINITE_REFERENCE",
            "PROVISIONAL_UNCALIBRATED",
            "INSUFFICIENT",
            "REFERENCE_INSUFFICIENT",
        )
        checked += 1
    counts = Counter()
    for p in m["predictions"]:
        row = by_id[p["id"]]
        assert row["task"] == m["task"] and splits[row["group"]] == m["fold"]
        d = m["decisions"][p["decision_id"]]
        expected = features(row, m["selected"])
        if p["method"] == "DSRE_partial":
            expected[6 if m["selected"] else 0] = None
        assert d["query"]["features"] == expected and d["method"] == p["method"]
        assert d["query"]["scope"] == table["scope"]
        counts[(p["id"], p["method"])] += 1
    assert all(n == 1 for n in counts.values())
    return m, checked


def audit(root):
    assert (
        "dual_rec.dsre.solver" not in sys.modules
        and "dual_rec.dsre.repair" not in sys.modules
    )
    pins = frozen_sources(root)
    config = load(Path("config/dsre_evidence_repair.json"))
    source = [
        json.loads(s) for s in (root / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    by_id = {r["id"]: r for r in source}
    original = [
        json.loads(s)
        for s in (Path(config["input_root"]) / "qualified_pairs.jsonl")
        .read_text()
        .splitlines()
    ]
    for row in original:
        enriched = by_id[row["id"]]
        assert all(enriched[k] == v for k, v in row.items())
        c = row["runtime_history"]["current"]
        obj, goal, hand = (
            c[k] for k in ("object_position", "goal_position", "tcp_position")
        )
        deltas = [
            obj[0] - goal[0] if obj and goal else None,
            obj[1] - goal[1] if obj and goal else None,
            hand[0] - obj[0] if hand and obj else None,
        ]
        expected = [
            None if x is None else x < -0.02 if sign < 0 else x > 0.02
            for x in deltas
            for sign in (-1, 1)
        ]
        assert enriched["optional_features"] == expected
        assert enriched["optional_timestamp"] == row["checkpoint_time"] == c["time"]
    splits = load(Path(config["input_root"]) / "group_splits.json")
    for task in ("PickCube-v1", "PushCube-v1"):
        ordered = sorted(
            {r["group"] for r in source if r["task"] == task},
            key=lambda g: hashlib.sha256(
                ("dsre-parent-fold-v1/" + g).encode()
            ).hexdigest(),
        )
        assert all(splits[g] == i % 5 for i, g in enumerate(ordered))
    selected_checks = 0
    expanded = []
    models = {}
    rule_checks = 0
    for path in sorted((root / "models").glob("*.json")):
        m, n = check_model(root, path, by_id, splits)
        models[path.stem] = m
        rule_checks += n
        print(json.dumps({"audited_model": path.stem}), flush=True)
    for path in sorted((root / "designs").glob("*.json")):
        design = load(path)
        task, fold = design["task"], design["fold"]
        train = [r for r in source if r["task"] == task and splits[r["group"]] != fold]
        evaluation = [
            r for r in source if r["task"] == task and splits[r["group"]] == fold
        ]
        assert set(design["reference_ids"]) == {r["id"] for r in train}
        assert set(design["evaluation_ids"]) == {r["id"] for r in evaluation}
        for scored in design["subset_scores"]:
            assert scored["ceiling_mass"] == finite_mass(train, scored["channels"])
        for d in design["selected_designs"]:
            expected = select(
                train,
                d["budget"],
                d["selector"],
                design["available"],
                config["random_order_seed"],
            )
            assert list(expected) == d["channels"]
            assert finite_mass(train, d["channels"]) == d["training_ceiling_mass"]
            assert (
                d["reference_sha256"]
                == hashlib.sha256(
                    json.dumps(train, sort_keys=True).encode()
                ).hexdigest()
            )
            model = models[d["model"]]
            assert model["selected"] == d["channels"]
            assert len(model["predictions"]) == len(evaluation) * (
                len(config["methods"]) + 1
            )
            for p in model["predictions"]:
                expanded.append(
                    (task, d, p, model["decisions"][p["decision_id"]]["result"])
                )
            selected_checks += 1
    finite_checks = 0
    finite = load(root / "finite_profiles.json")
    for task, profile in finite.items():
        population = [r for r in source if r["task"] == task]
        scores = {
            tuple(r["channels"]): r["ceiling_mass"] for r in profile["all_subsets"]
        }
        assert len(scores) == 64
        for j, n in scores.items():
            assert n == finite_mass(population, j)
            for i in range(6):
                if i not in j:
                    assert n <= scores[tuple(sorted((*j, i)))]
            finite_checks += 1
        for p in profile["diagnostics"].values():
            oracle = Oracle(p["table"], p["parent_groups"])
            mass = 0
            for c in p["certificates"]:
                q = {"scope": p["table"]["scope"], "features": c["signature"]}
                assert oracle.verify(q, c["output"])
                if c["output"]["action"]:
                    mass += sum(
                        r["features"] == c["signature"] for r in p["table"]["rows"]
                    )
            assert mass == p["supported_grammar_mass"]
            assert p["profile"]["actionable_mass"] == finite_mass(
                population, p["profile"]["channels"], p["profile"]["privileged"]
            )
    for path in sorted((root / "supported_profiles").glob("*.json")):
        p = load(path)
        m = models[path.stem]
        oracle = Oracle(m["table"], m["parent_groups"])
        mass = 0
        for c in p["signature_outputs"]:
            q = {"scope": m["table"]["scope"], "features": c["signature"]}
            assert oracle.verify(q, c["output"])
            if c["output"]["action"]:
                mass += c["mass"]
        assert mass == p["supported_grammar_mass"]
        finite_checks += 1
    statistical_checks = audit_statistics(root, source, expanded)
    graph = load(root / "ambiguity_graph.json")
    graph_checks = 0
    for task, g in graph.items():
        for edge in g["ambiguity_edges"]:
            a, b = [by_id[id] for id in edge["ids"]]
            assert (
                a["features"] == b["features"]
                and action_set(a)
                and action_set(b)
                and not action_set(a) & action_set(b)
            )
            separated = [
                config["optional_channels"][i]
                for i, (x, y) in enumerate(
                    zip(a["optional_features"], b["optional_features"], strict=True)
                )
                if x is not None and y is not None and x != y
            ]
            assert separated == edge["separating_channels"]
            graph_checks += 1
    # Separate full-table frontier/support values from cross-fit counts.
    checked_full = set()
    for task, frontier in load(root / "full_reference_frontiers.json").items():
        pop = [r for r in source if r["task"] == task]
        for key, entry in frontier.items():
            selector, budget = key.split("|")
            assert entry["channels"] == list(
                select(
                    pop,
                    int(budget),
                    selector,
                    tuple(range(6)),
                    config["random_order_seed"],
                )
            )
            assert entry["profile"]["finite_profile"]["actionable_mass"] == finite_mass(
                pop, entry["channels"]
            )
            identity = (task, tuple(entry["channels"]))
            if identity in checked_full:
                continue
            checked_full.add(identity)
            p = entry["profile"]
            scope = p["signature_outputs"][0]["output"]["certificate"]["scope"]
            table = {
                "scope": scope,
                "rows": [
                    {
                        "id": r["id"],
                        "features": features(r, entry["channels"]),
                        "outcomes": r["outcomes"],
                        "qualified": True,
                    }
                    for r in pop
                ],
            }
            oracle = Oracle(table, {r["id"]: r["group"] for r in pop})
            mass = 0
            for c in p["signature_outputs"]:
                assert oracle.verify(
                    {"scope": scope, "features": c["signature"]}, c["output"]
                )
                if c["output"]["action"]:
                    mass += c["mass"]
            assert mass == p["supported_grammar_mass"]
    result = {
        "status": "PASS",
        "main_solver_imported": False,
        "source_input_pins": pins,
        "qualified_pairs": len(source),
        "training_selected_designs": selected_checks,
        "distinct_models": len(models),
        "unique_rule_and_output_checks": rule_checks,
        "expanded_prediction_rows": len(expanded),
        "finite_and_supported_checks": finite_checks,
        "statistical_checks": statistical_checks,
        "physical_ambiguity_edges": graph_checks,
        "new_tree_fits": sum(m["new_tree_fits"] for m in models.values()),
        "audit_independence": "Separate implementation in the same session, not independent human review",
    }
    save(root / "independent_audit.json", result)
    print(json.dumps(result), flush=True)


def audit_statistics(root, source, expanded):
    plan = load(root / "uncertainty_plan.json")
    by_id = {r["id"]: r for r in source}
    index = load(root / "group_count_index.json")
    fields = index["fields"]
    npz = np.load(root / "group_counts.npz")
    keys = index["keys"]
    stored = {k: npz[f"a{i}"] for i, k in enumerate(keys)}
    computed = {k: np.zeros_like(v) for k, v in stored.items()}
    tasks = ("PickCube-v1", "PushCube-v1")
    gindex = {
        t: {g: i for i, g in enumerate(plan["tasks"][t]["groups"])} for t in tasks
    }
    per_input = defaultdict(dict)
    for task, d, p, r in expanded:
        row = by_id[p["id"]]
        chosen = r["action"]
        strict = r["status"] == "STRICT_FINITE_REFERENCE"
        kinds = {o["kind"] for o in r.get("diagnosis", {}).get("obstructions", [])}
        label = f"{d['selector']}|{d['budget']}|{p['method']}"
        per_input[p["id"]][label] = r
        for population in ("all_starts", "failed_starts"):
            if population == "failed_starts" and row["initial_success"]:
                continue
            for action in (
                ("all", "continue", "recover") if p["method"] == "DSRE" else ("all",)
            ):
                emitted = chosen is not None and action in ("all", chosen)
                success = int(row["outcomes"][chosen + "_value"]) if emitted else 0
                score = {
                    "episodes": 1,
                    "recommended": int(emitted),
                    "adequate": success,
                    "unacceptable": int(emitted) - success,
                    "strict_recommended": int(strict and emitted),
                    "strict_success": success * strict,
                    "strict_error": strict * (int(emitted) - success),
                    "provisional_recommended": int(
                        emitted and r["status"] == "PROVISIONAL_UNCALIBRATED"
                    ),
                    "literals": len(r["evidence"]) if emitted else 0,
                    "support_rows": r["support"] if emitted else 0,
                    "parent_support": r["independent_parents"] if emitted else 0,
                    "channel_sum": len(d["channels"]),
                    "abstained": int(chosen is None),
                    "reference_insufficient": int("REFERENCE_INSUFFICIENT" in kinds),
                    "ambiguity": int("OBSERVATIONAL_AMBIGUITY" in kinds),
                    "inadequacy": int("REPERTOIRE_INADEQUATE" in kinds),
                    "overlap": int(
                        {"OBSERVATIONAL_AMBIGUITY", "REPERTOIRE_INADEQUATE"} <= kinds
                    ),
                }
                computed[f"{task}|{label}|{population}|{action}"][
                    gindex[task][row["group"]]
                ] += [score[f] for f in fields]
    assert all(np.array_equal(stored[k], v) for k, v in computed.items())
    weights = {}
    for t in tasks:
        ng = len(gindex[t])
        draws = np.random.default_rng(plan["tasks"][t]["seed"]).integers(
            0, ng, (plan["draws"], ng)
        )
        assert (
            hashlib.sha256(draws.tobytes()).hexdigest()
            == plan["tasks"][t]["draws_sha256"]
        )
        weights[t] = np.stack([np.bincount(row, minlength=ng) for row in draws])
    ratio = {
        "coverage": ("recommended", "episodes"),
        "successful_strict_coverage": ("strict_success", "episodes"),
        "unacceptable_rate": ("unacceptable", "recommended"),
        "unsuccessful_action_per_checkpoint": ("unacceptable", "episodes"),
        "success_per_checkpoint": ("adequate", "episodes"),
        "mean_literals": ("literals", "recommended"),
        "mean_support_rows": ("support_rows", "recommended"),
        "mean_parent_support": ("parent_support", "recommended"),
        "mean_added_channels": ("channel_sum", "episodes"),
    }
    metrics = load(root / "metrics.json")
    checks = 0
    memo = {}
    for key, a in computed.items():
        t = key.split("|")[0]
        ck = (t, hashlib.sha256(a.tobytes()).hexdigest())
        if ck not in memo:
            memo[ck] = weights[t] @ a
        samples = memo[ck]
        counts = a.sum(axis=0)
        m = metrics[key]
        assert m["counts"] == dict(zip(fields, map(int, counts), strict=True))
        groups = int((a[:, fields.index("recommended")] > 0).sum())
        assert m["recommending_seed_groups"] == groups
        for name, (num, den) in ratio.items():
            n, d = fields.index(num), fields.index(den)
            valid = samples[:, d] > 0
            sparse = den == "recommended" and groups < 10
            expected = (
                np.percentile(
                    samples[valid, n] / samples[valid, d], [2.5, 97.5]
                ).tolist()
                if valid.any() and not sparse
                else None
            )
            compare(m["rates"][name]["parent_percentile95"], expected)
            compare(
                m["rates"][name]["value"],
                float(counts[n] / counts[d]) if counts[d] else None,
            )
            checks += 1
    for key, p in load(root / "paired_comparisons.json").items():
        task, rest = key.split("|", 1)
        left, right = rest.split(" minus ")
        a = computed[f"{task}|{left}|all_starts|all"]
        b = computed[f"{task}|{right}|all_starts|all"]
        sa, sb = weights[task] @ a, weights[task] @ b
        ca, cb = a.sum(axis=0), b.sum(axis=0)
        for name, result in p["differences"].items():
            num, den = ratio[name]
            n, d = fields.index(num), fields.index(den)
            valid = (sa[:, d] > 0) & (sb[:, d] > 0)
            sparse = (
                den == "recommended"
                and min(int((a[:, 1] > 0).sum()), int((b[:, 1] > 0).sum())) < 10
            )
            expected = (
                np.percentile(
                    sa[valid, n] / sa[valid, d] - sb[valid, n] / sb[valid, d],
                    [2.5, 97.5],
                ).tolist()
                if valid.any() and not sparse
                else None
            )
            compare(result["parent_percentile95"], expected)
            compare(
                result["value"],
                float(ca[n] / ca[d] - cb[n] / cb[d]) if ca[d] and cb[d] else None,
            )
            checks += 1
        common = np.zeros((211, 3), dtype=int)
        equal = 0
        for row in source:
            if row["task"] != task:
                continue
            r, s = per_input[row["id"]][left], per_input[row["id"]][right]
            equal += r["action"] == s["action"] and r["evidence"] == s["evidence"]
            if r["action"] and s["action"]:
                common[gindex[task][row["group"]]] += [
                    1,
                    len(r["evidence"]) - len(s["evidence"]),
                    int(r["action"] == s["action"]),
                ]
        assert (
            p["equal_action_evidence"] == equal
            and p["common_recommended"] == int(common[:, 0].sum())
            and p["common_action_agreement"] == int(common[:, 2].sum())
        )
        sample = weights[task] @ common
        valid = sample[:, 0] > 0
        expected = (
            np.percentile(sample[valid, 1] / sample[valid, 0], [2.5, 97.5]).tolist()
            if valid.any() and (common[:, 0] > 0).sum() >= 10
            else None
        )
        compare(p["common_literal_parent95"], expected)
        checks += 1
    # Check the full enumerated error list without treating repeated views as new parents.
    expected_errors = {
        (p["id"], d["selector"], d["budget"])
        for t, d, p, r in expanded
        if p["method"] == "DSRE"
        and r["action"]
        and not by_id[p["id"]]["outcomes"][r["action"] + "_value"]
    }
    errors = load(root / "strict_errors.json")
    assert expected_errors == {
        (r["id"], r["selector"], r["budget"]) for r in errors["errors"]
    }
    return checks


def compare(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert np.allclose(actual, expected, atol=1e-12, rtol=1e-12), (actual, expected)


def audit_review(root):
    assert (
        "dual_rec.dsre.solver" not in sys.modules
        and "dual_rec.dsre.repair" not in sys.modules
    )
    identities = load(root / "baseline_identities.json")
    overlap = load(root / "obstruction_overlap.json")
    models = {p.stem: load(p) for p in (root / "models").glob("*.json")}
    computed = defaultdict(Counter)
    causes = defaultdict(Counter)
    checks = 0
    for path in (root / "designs").glob("*.json"):
        design = load(path)
        for d in design["selected_designs"]:
            model = models[d["model"]]
            methods = defaultdict(dict)
            for p in model["predictions"]:
                methods[p["id"]][p["method"]] = model["decisions"][p["decision_id"]][
                    "result"
                ]
            key = f"{design['task']}|{d['budget']}"
            causekey = f"{design['task']}|{d['selector']}|{d['budget']}"
            for row in methods.values():
                a, b, c = (row[m] for m in ("DSRE", "B7", "B1_two_strict"))
                computed[key]["views"] += 1
                computed[key]["DSRE_B7_equal"] += all(
                    a[f] == b[f] for f in ("action", "evidence")
                ) and (not a["action"] or a["support"] == b["support"])
                computed[key]["DSRE_pure_two_literal_equal"] += all(
                    a[f] == c[f] for f in ("action", "evidence")
                )
                kinds = sorted(o["kind"] for o in a["diagnosis"]["obstructions"])
                causes[causekey][
                    "+".join(kinds) if kinds else "STRICT_RECOMMENDATION"
                ] += 1
                checks += 1
    assert {k: dict(v) for k, v in computed.items()} == identities
    assert {k: dict(v) for k, v in causes.items()} == overlap
    plan = load(root / "prospective_plan.json")
    assert (
        plan["count"] == 1 and plan["status"] == "DORMANT_NOT_JUSTIFIED_FOR_EXECUTION"
    )
    assert plan["per_stratum_delta"] == plan["delta"] / plan["strata"] == 0.0125
    assert (
        math.ceil(math.log(0.0125) / math.log(0.9))
        == plan["zero_error_assigned_required"]
        == 42
    )
    metrics = load(root / "metrics.json")
    for stratum, p in plan["assignments"].items():
        task, action = stratum.split("/")
        expected = metrics[f"{task}|exact_coverage|1|DSRE|all_starts|{action}"][
            "counts"
        ]["recommended"]
        assert expected == p["crossfit_assigned"]
        assert p["frequency"] == expected / 422
        compare(p["expected_from_200"], 200 * expected / 422)
        checks += 1
    expected_cost = (2800 * 2 * 3.9696 + 400 * 2 * 2.6377) * 1.5 / 3600
    assert expected_cost == plan["serial_wall_estimate_hours_with_1_5_overhead"]
    for p in load(root / "interface_examples.json"):
        assert p["deployment_enabled"] is False
        u = p["offline_upgrade"]
        assert u["abstract_cost"] == len(u["channels"]) <= u["budget"]
        assert u["guarantees_current_query_repair"] is False
        assert u["training_before_mass"] <= u["training_after_mass"]
        assert p["result"]["status"] != "STRICT_FINITE_REFERENCE"
        checks += 1
    source = [
        json.loads(s) for s in (root / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    by_id = {r["id"]: r for r in source}
    for example in load(root / "worked_examples.json"):
        records = example["records"]
        assert all(record == by_id[record["id"]] for record in records)
        assert records[0]["features"] == records[1]["features"]
        if example["example"] == "opposing_good_sets":
            assert (
                action_set(records[0])
                and action_set(records[1])
                and not action_set(records[0]) & action_set(records[1])
            )
            assert records[0]["optional_features"] == records[1]["optional_features"]
        elif "refinement_certificate" in example:
            selected = example["added_channels"]
            assert any(
                records[0]["optional_features"][i] != records[1]["optional_features"][i]
                for i in selected
            )
            cert = example["refinement_certificate"]
            population = [r for r in source if r["task"] == example["task"]]
            scope = cert["certificate"]["scope"]
            table = {
                "scope": scope,
                "rows": [
                    {
                        "id": r["id"],
                        "features": features(r, selected),
                        "outcomes": r["outcomes"],
                        "qualified": True,
                    }
                    for r in population
                ],
            }
            oracle = Oracle(table, {r["id"]: r["group"] for r in population})
            assert oracle.verify(
                {"scope": scope, "features": features(records[0], selected)}, cert
            )
            assert not action_set(records[1]) and cert["action"] in action_set(
                records[0]
            )
        checks += 1
    save(
        root / "review_audit.json",
        {
            "status": "PASS",
            "independent_checks": checks,
            "new_physics": 0,
            "method_distinctiveness": "NOT_ESTABLISHED",
        },
    )
    print(json.dumps(load(root / "review_audit.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--review-only", action="store_true")
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if args.review_only:
        audit_review(args.root)
    else:
        audit(args.root)
