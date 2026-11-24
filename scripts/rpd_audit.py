"""Reproducible offline finite planner/oracle audit, with bounded output."""

import argparse
import hashlib
import json
import lzma
import time
from collections import Counter
from pathlib import Path

from rpd_baselines import named_comparison
from rpd_cases import exhaustive_cases, named_cases, random_cases
from rpd_independent_oracle import (
    check_policy,
    exhaustive,
    pomdp_value,
    verify_obstruction,
)

from dual_rec.recoverability.planner import plan_probes

BASE = Path("research/rpd_method_challenge")


def run(output):
    assert not output.exists(), "Fresh output directory required"
    output.mkdir(parents=True)
    registration = json.loads((BASE / "registration.json").read_text())
    assert registration["no_new_physics"] is True
    start = time.perf_counter()
    counts = Counter()
    named = {}

    def check(p):
        raw = p.model_dump(mode="json")
        answer = plan_probes(p)
        truth, trees = exhaustive(raw)
        p_goal, pomdp_cost = pomdp_value(raw)
        exact_cost = None if truth is None else truth[0]
        assert answer.worst_probe_cost == exact_cost == pomdp_cost
        assert (p_goal == 1) == (truth is not None)
        if truth is not None:
            outcomes = check_policy(raw, answer.policy.model_dump(mode="json"))
            assert all(row[0] for row in outcomes)
            assert max(row[1] for row in outcomes) == exact_cost
            counts["winning_policies_independently_replayed"] += 1
        else:
            assert answer.status == "STOP_NO_ROBUST_POLICY"
            verify_obstruction(raw, answer.obstruction.model_dump(mode="json"))
            counts["complete_obstructions_independently_verified"] += 1
        counts["exact_brute_policy_tree_agreements"] += 1
        counts["same_input_probability_one_POMDP_cost_agreements"] += 1
        counts["policy_trees_enumerated"] += trees
        return {
            "problem": raw,
            "production": answer.model_dump(mode="json"),
            "oracle_cost": None if exact_cost is None else str(exact_cost),
            "POMDP_max_goal_probability": str(p_goal),
            "POMDP_probability_one_min_worst_cost": None
            if pomdp_cost is None
            else str(pomdp_cost),
            "policy_trees_enumerated": trees,
        }

    for name, p in named_cases().items():
        named[name] = check(p)
    toy = named["three_world"]
    exact, _ = exhaustive(toy["problem"])
    toy["matched_control_comparison"] = named_comparison(toy["problem"], exact[1])
    assert toy["matched_control_comparison"]["one_step_consensus"]["metrics"][
        "all_worlds_success"
    ]
    assert (
        toy["matched_control_comparison"]["physical_entropy"]["metrics"][
            "uniform_initial_completion"
        ]
        == "2/3"
    )
    assert (
        toy["matched_control_comparison"]["static_ERR_transition_ignored_ABLATION"][
            "metrics"
        ]["uniform_initial_completion"]
        == "2/3"
    )
    (output / "named_cases.json").write_text(json.dumps(named, indent=2) + "\n")
    for label, iterator in [
        ("seeded", ((index, p) for index, p in random_cases(registration))),
        ("exhaustive", enumerate(exhaustive_cases())),
    ]:
        number = 0
        with lzma.open(output / (label + "_cases.jsonl.xz"), "wt") as stream:
            for index, p in iterator:
                result = check(p)
                stream.write(
                    json.dumps(
                        {"index": index, **result},
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                number += 1
                assert (
                    time.perf_counter() - start
                    < registration["max_offline_experiment_seconds"]
                )
        counts[label + "_cases"] = number
    assert counts["seeded_cases"] == 528 and counts["exhaustive_cases"] == 6144
    assert counts["exact_brute_policy_tree_agreements"] == 6688
    summary = {
        "passed": True,
        "named_cases": len(named),
        "counts": dict(counts),
        "full_model_baseline": "VALUE_EQUIVALENCE_TO_BOUNDED_STRONG_PLANNING_AND_PROBABILITY_ONE_REACH_AVOID_POMDP",
        "calibrated_new_physical_predicates": 0,
        "new_robot_outcomes": 0,
        "new_physics": 0,
        "scope": "Known deterministic finite analytical models, stated horizon, budget and path-safety constraints only",
        "wall_seconds": time.perf_counter() - start,
        "output_sha256": {
            str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.iterdir())
            if p.is_file()
        },
    }
    (output / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
