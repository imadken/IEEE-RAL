"""Second numerical/source audit, with no imports from the editing implementation."""

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(claim):
    w = claim["window"]
    f = claim["fact"]
    return (
        claim["kind"],
        None if f is None else (f["entity"], f["predicate"], f["value"]),
        w["clock"],
        float(w["start"]),
        float(w["end"]),
        claim["action"],
    )


def run(root):
    config = load(Path("config/explanation_repair_week2.json"))
    old = Path(config["week1_root"])
    target = old / config["week1_development"]
    freeze = load(root / "evaluation_input_freeze.json")
    for name, expected in freeze["hashes"].items():
        assert digest(root / name) == expected, name
    for name, expected in freeze["source_hashes"].items():
        assert digest(Path(name)) == expected, name
    assert (
        digest(Path("config/explanation_repair_week2.json")) == freeze["config_sha256"]
    )
    sources = load(root / "source_members.json")
    for name, expected in sources.items():
        assert digest(Path(name)) == expected, name
    seal = load(old / "completion_manifest.json")["sha256"]
    for name in ["data/RoboFail_generated.json", "data/CounterFactual_generated.json"]:
        path = old / "upstream" / name
        assert digest(path) == seal[str(path.relative_to(old))]
    original_public = {
        dataset + "/" + r["task_id"]: r
        for dataset, filename in [
            ("RoboFail", "RoboFail_generated.json"),
            ("CounterFactual", "CounterFactual_generated.json"),
        ]
        for r in load(old / "upstream/data" / filename)
    }
    public = rows(root / "public_inputs.jsonl")
    assert len(public) == len(original_public) == 750
    assert len({r["id"] for r in public}) == 750
    for row in public:
        original = original_public[row["id"]]
        assert row["original"] == original | (
            {"comment": None} if "comment" not in original else {}
        )
        for clause in row["extraction"]["clauses"]:
            if not clause["recognized"]:
                assert clause["text"] in row["input"]["unparsed"]
    review = rows(root / "review_blind.jsonl")
    wanted = {r["id"] for r in load(root / "review_subset_freeze.json")["rows"]}
    assert len(wanted) == 55 and {r["id"] for r in review} == wanted
    assert len(review) == 76
    for row in review:
        assert all(
            row[k] is None
            for k in [
                "adjudicated_status",
                "adjudicated_claims",
                "independent_reviewer",
                "information_to_preserve",
                "dependency_review",
            ]
        )
        assert not ({"result", "method", "code", "output"} & row.keys())
    assert all(
        v == "NOT_ASSESSED_WITHOUT_INDEPENDENT_ADJUDICATION"
        for v in load(root / "public_analysis.json")["quality"].values()
    )
    public_groups = defaultdict(Counter)
    for row in public:
        e = row["extraction"]
        public_groups[row["group"]].update(
            rows=1,
            complete=int(e["complete"]),
            partial=int(e["partial"]),
            factual=int(e["factual_claims"] > 0),
        )
    coverage_fields = ["rows", "complete", "partial", "factual"]
    public_matrix = np.array(
        [[public_groups[g][k] for k in coverage_fields] for g in sorted(public_groups)]
    )
    public_rng = np.random.default_rng(config["bootstrap_seed"])
    public_indices = public_rng.integers(
        0, len(public_groups), (config["bootstrap_draws"], len(public_groups))
    )
    public_samples = np.stack(
        [
            np.bincount(indices, minlength=len(public_groups)) @ public_matrix
            for indices in public_indices
        ]
    )
    public_analysis = load(root / "public_analysis.json")
    for i, name in enumerate(coverage_fields[1:], 1):
        expected = public_analysis["coverage"][name]
        assert int(public_matrix[:, i].sum()) == expected["count"]
        assert np.allclose(
            np.quantile(public_samples[:, i] / public_samples[:, 0], [0.025, 0.975]),
            expected["percentile95"],
            rtol=0,
            atol=1e-12,
        )
    controls = {r["id"]: r for r in rows(root / "controls_frozen.jsonl")}
    control_counts = defaultdict(Counter)
    for row in rows(root / "control_outputs.jsonl"):
        original = controls[row["id"]]
        truth = {key(c) for c in original["oracle_true"]}
        emitted = {
            key(g["claim"]): g["claim"]
            for g in row["result"]["claims"]
            if g["claim"]["kind"] != "hypothesis"
        }
        established = sum(k in truth for k in emitted)
        control_counts[row["code"]].update(
            asserted=len(emitted),
            established=established,
            unsupported=len(emitted) - established,
            informative=int(established > 0),
        )
        if row["id"] == "correct_historical" and row["code"] == "B5":
            assert len(emitted) == 1 and established == 0
        if (
            row["id"]
            in {
                "missing_evidence",
                "multiple_plausible_causes",
                "conflicting_observations",
                "command_not_effect",
                "unanchored_history",
                "ambiguous_repetition",
            }
            and row["code"] == "B4"
        ):
            assert not emitted
        if (
            row["id"]
            in {
                "correct_no_repair",
                "valid_model",
                "correct_historical",
                "correct_order",
                "wrong_order",
                "blocked_model",
                "temporally_misplaced",
            }
            and row["code"] == "B4"
        ):
            assert established == 1 and len(emitted) == 1
    saved_controls = load(root / "control_metrics.json")["totals"]
    for code, counts in control_counts.items():
        assert all(saved_controls[code][k] == v for k, v in counts.items())
    cells = load(target / "physical_sources.json")
    truth_by_cell = {}
    for cell in cells:
        assert digest(Path(cell["source"])) == cell["source_sha256"]
        with gzip.open(cell["source"], "rt") as stream:
            raw = json.load(stream)
        reference = raw["traces"]["continue/reference"]
        truth = {}
        for state in [reference["prefix_history"][0], reference["start"]]:
            time = state["time"]
            if cell["task"] == "Lift":
                truth[("cube", "grasped", time)] = bool(state["is_grasped"])
            else:
                extra = state["observation"]["extra"]
                if cell["task"] == "PickCube-v1":
                    truth[("cube", "grasped", time)] = bool(extra["is_grasped"][0])
                truth[("cube", "near_goal", time)] = (
                    math.sqrt(
                        sum(
                            (a - b) ** 2
                            for a, b in zip(
                                state["position"], extra["goal_pos"][0][:3], strict=True
                            )
                        )
                    )
                    <= 0.03
                )
                truth[("robot", "contact", time)] = any(
                    "cube" in str(pair[0])
                    and "panda" in str(pair[1])
                    or "panda" in str(pair[0])
                    and "cube" in str(pair[1])
                    for pair in state["contacts"]
                )
        truth_by_cell[cell["id"]] = truth
    inputs = {r["id"]: r for r in rows(target / "trace_inputs.jsonl")}
    old_outputs = {
        (r["input_id"], r["method"]): r["result"]
        for r in rows(target / "trace_outputs.jsonl")
    }
    per_input = {
        (r["id"], r["code"]): r for r in load(root / "trace_per_input_metrics.json")
    }
    recomputed = defaultdict(Counter)
    exact_matches = 0
    for row in rows(root / "trace_outputs.jsonl"):
        original = inputs[row["id"]]
        raw_truth = truth_by_cell[original["cell"]]

        def true(c, original=original, raw_truth=raw_truth):
            if (
                c["kind"] == "hypothesis"
                or c["fact"] is None
                or c["window"]["clock"] != "seconds"
                or c["window"]["start"] != c["window"]["end"]
            ):
                return None
            f, t = c["fact"], c["window"]["start"]
            if c["kind"] == "observation":
                k = (f["entity"], f["predicate"], t)
            elif (
                c["action"] == f["entity"] == "transport"
                and f["predicate"] == "applicable"
            ):
                k = (
                    ("robot", "contact", t)
                    if original["cell"].startswith("PushCube-v1/")
                    else ("cube", "grasped", t)
                )
                if c["kind"] == "recommendation" and raw_truth.get(k) is False:
                    return False
            else:
                return None
            return raw_truth[k] == f["value"] if k in raw_truth else None

        orig = {
            key(c): c for c in original["input"]["claims"] if c["kind"] != "hypothesis"
        }
        emitted = {
            key(g["claim"]): g["claim"]
            for g in row["result"]["claims"]
            if g["claim"]["kind"] != "hypothesis"
        }
        supported = {k for k, c in orig.items() if true(c) is True}
        correct = (
            bool(orig)
            and len(supported) == len(orig)
            and not original["input"]["unparsed"]
            and not any(c["kind"] == "hypothesis" for c in original["input"]["claims"])
        )
        established = sum(true(c) is True for c in emitted.values())
        bad = len(emitted) - established
        m = {
            "inputs": 1,
            "asserted": len(emitted),
            "established": established,
            "contradicted": sum(true(c) is False for c in emitted.values()),
            "undetermined": sum(true(c) is None for c in emitted.values()),
            "unsupported": bad,
            "any_unsupported": int(bad > 0),
            "supported_original": len(supported),
            "retained": len(supported & emitted.keys()),
            "informative": int(established > 0),
            "correct_inputs": int(correct),
            "damaged": int(correct and (bad > 0 or not supported <= emitted.keys())),
            "cosmetic_change": int(
                correct and row["result"]["text"] != original["input"]["original_text"]
            ),
            "abstained": int(not emitted),
            "unresolved": int(bool(row["result"]["unresolved"])),
        }
        assert m == per_input[(row["id"], row["code"])]["metrics"]
        recomputed[row["code"]].update(m)
        if row["code"] != "B5":
            assert row["result"] == old_outputs[(row["id"], row["method"])]
            exact_matches += 1
    assert {k: dict(v) for k, v in recomputed.items()} == load(
        root / "trace_metrics.json"
    )["totals"]
    # Independent resampling implementation: multiplicity weights instead of
    # concatenated sampled rows. Both conditions/variants remain in each parent.
    parent = defaultdict(lambda: defaultdict(Counter))
    for row in per_input.values():
        parent["/".join(row["cell"].split("/")[:2])][row["code"]].update(row["metrics"])
    names, codes = sorted(parent), list(config["methods"])
    tasks = sorted({g.split("/")[0] for g in names})
    strata = [
        [i for i, name in enumerate(names) if name.split("/")[0] == t] for t in tasks
    ]
    fields = sorted(next(iter(next(iter(parent.values())).values())))
    array = np.array(
        [[[parent[name][code][f] for f in fields] for code in codes] for name in names],
        float,
    )
    rng = np.random.default_rng(config["bootstrap_seed"])
    draws = []
    for _ in range(config["bootstrap_draws"]):
        weights = np.zeros(len(names))
        for s in strata:
            weights += np.bincount(
                rng.choice(s, len(s), replace=True), minlength=len(names)
            )
        draws.append(np.einsum("i,ijk->jk", weights, array))
    samples, totals = np.asarray(draws), array.sum(axis=0)
    ratios = {
        "unsupported_input_fraction": ("any_unsupported", "inputs"),
        "retention": ("retained", "supported_original"),
        "informative_fraction": ("informative", "inputs"),
        "damage_fraction": ("damaged", "correct_inputs"),
        "established_facts_per_input": ("established", "inputs"),
    }
    uncertainty = load(root / "trace_paired_uncertainty.json")
    checked_intervals = 0
    for code in codes:
        if code == "B4":
            continue
        a, b = codes.index("B4"), codes.index(code)
        for name, (n, d) in ratios.items():
            ni, di = fields.index(n), fields.index(d)
            delta = totals[a, ni] / totals[a, di] - totals[b, ni] / totals[b, di]
            distribution = (
                samples[:, a, ni] / samples[:, a, di]
                - samples[:, b, ni] / samples[:, b, di]
            )
            expected = uncertainty["comparisons"]["B4-minus-" + code][name]
            assert abs(delta - expected["difference"]) < 1e-12
            assert np.allclose(
                np.quantile(distribution, [0.025, 0.975]),
                expected["percentile95"],
                atol=1e-12,
                rtol=0,
            )
            checked_intervals += 1
    output_checks = {}
    for population, count in [("public", 750), ("trace", 595), ("control", 13)]:
        output = rows(root / f"{population}_outputs.jsonl")
        assert len(output) == count * 6
        assert len({(r["id"], r["code"]) for r in output}) == count * 6
        assert Counter(r["code"] for r in output) == {c: count for c in codes}
        assert all(
            r["result"]["menus_evaluated"] <= config["common_candidate_limit"]
            for r in output
        )
        output_checks[population] = len(output)
    audit = {
        "status": "PASS_INDEPENDENT_NUMERICAL_AND_SOURCE_AUDIT",
        "scope": "Second implementation of raw-state facts, per-input counts and parent-weight bootstrap; not independent human semantic adjudication",
        "raw_cells": len(cells),
        "source_hashes_checked": len(sources),
        "frozen_source_and_input_hashes": "PASS",
        "previous_method_exact_output_matches": exact_matches,
        "raw_oracle_method_input_rows": len(per_input),
        "paired_intervals_recomputed": checked_intervals,
        "public_coverage_intervals_recomputed": 3,
        "authored_control_factual_counts_and_named_negatives": "PASS_SEPARATE_STATIC_TRUTH_TABLES",
        "output_counts": output_checks,
        "review_examples": len(wanted),
        "review_clauses": len(review),
        "human_labels": "NONE; quality correctly withheld",
        "historical_and_unrelated_preservation": "Verified separately by finalizer",
    }
    (root / "independent_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
