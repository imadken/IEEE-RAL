"""Independent derived-analysis audit using already raw-verified physical labels."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def verify(root):
    assert load(root / "independent_audit.json")["status"].startswith("PASS_")
    source = {r["id"]: r for r in rows(root / "qualified_pairs.jsonl")}
    config = load(Path("config/dsre_stage1.json"))
    saved_scored = {
        (r["id"], r["variant"], r["method"]): r["metrics"]
        for r in rows(root / "scored_primary.jsonl")
    }
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
    by_scope = defaultdict(lambda: defaultdict(dict))
    failed = defaultdict(lambda: defaultdict(lambda: np.zeros(9)))
    for file in sorted((root / "crossfit").glob("*.jsonl")):
        for r in rows(file):
            if r["point"] != "primary":
                continue
            pair, rec = source[r["id"]], r["recommendation"]
            action = rec["action"]
            emitted = int(action is not None)
            successful = int(pair["outcomes"][action + "_value"]) if emitted else 0
            best = int(max(pair["outcomes"].values()))
            scored = np.array(
                [
                    1,
                    emitted,
                    successful,
                    successful,
                    emitted - successful,
                    best - successful if emitted else 0,
                    len(rec["evidence"]) if emitted else 0,
                    emitted - successful,
                    int(emitted and not best),
                ]
            )
            assert (
                dict(zip(fields, map(int, scored), strict=True))
                == saved_scored[(r["id"], r["variant"], r["method"])]
            )
            scope = r["variant"] + "/" + r["task"]
            by_scope[scope][r["id"]][r["method"]] = (scored, rec)
            if not pair["initial_success"]:
                failed[scope][r["method"]] += scored
    failed_saved = load(root / "failed_start_metrics.json")
    for scope, methods in failed.items():
        for method, score in methods.items():
            assert (
                dict(zip(fields, map(int, score), strict=True))
                == failed_saved[scope][method]
            )
    paired = load(root / "paired_comparisons.json")
    intervals = 0
    for scope, examples in by_scope.items():
        groups = sorted({source[i]["group"] for i in examples})
        where = {g: i for i, g in enumerate(groups)}
        methods = config["methods"]
        array = np.zeros((len(groups), len(methods), 9))
        for identifier, predictions in examples.items():
            for mi, method in enumerate(methods):
                array[where[source[identifier]["group"]], mi] += predictions[method][0]
        rng = np.random.default_rng(config["bootstrap_seed"])
        draws = rng.integers(len(groups), size=(config["bootstrap_draws"], len(groups)))
        weights = np.stack([np.bincount(draw, minlength=len(groups)) for draw in draws])
        sampled = np.einsum("bi,imf->bmf", weights, array, optimize=True)
        total = array.sum(axis=0)
        a = methods.index("DSRE")
        for b, method in enumerate(methods):
            if b == a:
                continue
            record = paired[scope + "/DSRE-minus-" + method]
            for metric, (n, d) in {
                "coverage": (1, 0),
                "unacceptable_frequency": (4, 1),
                "mean_literals_given_recommendation": (6, 1),
                "successful_recommendations_per_episode": (3, 0),
            }.items():
                point = (
                    total[a, n] / total[a, d] - total[b, n] / total[b, d]
                    if total[a, d] and total[b, d]
                    else None
                )
                expected = record["comparisons"][metric]
                assert point == expected["DSRE_minus_comparator"]
                valid = (sampled[:, a, d] > 0) & (sampled[:, b, d] > 0)
                enough = (
                    d == 0
                    or min((array[:, a, 1] > 0).sum(), (array[:, b, 1] > 0).sum()) >= 10
                )
                if valid.any() and enough:
                    values = (
                        sampled[valid, a, n] / sampled[valid, a, d]
                        - sampled[valid, b, n] / sampled[valid, b, d]
                    )
                    assert np.allclose(
                        np.quantile(values, [0.025, 0.975]),
                        expected["paired_parent_percentile95"],
                        atol=1e-12,
                        rtol=0,
                    )
                    intervals += 1
                else:
                    assert expected["paired_parent_percentile95"] is None
            common = np.zeros((len(groups), 2))
            for identifier, predictions in examples.items():
                left, right = predictions["DSRE"][1], predictions[method][1]
                if left["action"] and right["action"]:
                    common[where[source[identifier]["group"]]] += [
                        len(left["evidence"]) - len(right["evidence"]),
                        1,
                    ]
            assert int(common[:, 1].sum()) == record["common_recommendation_episodes"]
            sample = weights @ common
            valid = sample[:, 1] > 0
            if valid.any() and (common[:, 1] > 0).sum() >= 10:
                assert np.allclose(
                    np.quantile(sample[valid, 0] / sample[valid, 1], [0.025, 0.975]),
                    record["paired_parent_percentile95_common_length"],
                    atol=1e-12,
                    rtol=0,
                )
                intervals += 1
            else:
                assert record["paired_parent_percentile95_common_length"] is None
    examples = load(root / "witness_examples.json")
    useful = next(e for e in examples if e["category"] == "short_sound_certificate")
    matched = [source[i] for i in useful["certificate"]["matched_ids"]]
    assert len(matched) == 17 and all(
        not p["initial_success"]
        and not p["outcomes"]["continue_value"]
        and p["outcomes"]["recover_value"]
        for p in matched
    )
    output = {
        "status": "PASS_INDEPENDENT_DERIVED_ANALYSIS",
        "raw_label_basis": "independent_audit.json already verified source hashes and all physical outcomes",
        "primary_prediction_scores_recomputed": len(saved_scored),
        "failed_start_count_cells": sum(len(m) for m in failed.values()),
        "paired_and_common_cohort_intervals_checked": intervals,
        "useful_two_literal_recovery_only_reference_support": len(matched),
        "not_new_physics": True,
    }
    (root / "independent_derived_audit.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    print(json.dumps(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed; use the read-only finish verify stage")
    verify(args.root)
