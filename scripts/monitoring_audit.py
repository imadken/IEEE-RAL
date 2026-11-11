"""Independently audit stored monitoring decisions using only the standard library.

No study scheduler, certifier, recovery implementation or simulator is imported.
Noisy/stale false permissions remain measured outcomes, not audit failures.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

REGIMES = (
    "complete",
    "missing10",
    "missing30",
    "missing50",
    "structured",
    "delayed",
    "noise05",
    "invalidated",
)
PRIMARY_REGIMES = frozenset({"missing10", "missing30", "missing50", "structured"})
METRICS = (
    "false_current_permission",
    "invalid_continuation_permission",
    "valid_continuation",
    "goal_completion",
    "abstention",
    "unnecessary_abstention",
    "justified_abstention",
    "recovery_invoked",
    "recovery_success",
    "query_count",
    "executed_actions",
    "simulated_cost",
)


def fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def canonical_action(action: dict) -> tuple:
    return (
        action["name"],
        tuple(
            sorted((lit["atom"], lit.get("positive", True)) for lit in action["pre"])
        ),
        tuple(sorted(action["add"])),
        tuple(sorted(action["delete"])),
    )


def canonical_model(model: dict) -> tuple:
    return (
        tuple(sorted(model["atoms"])),
        tuple(
            sorted(
                tuple(
                    sorted((lit["atom"], lit.get("positive", True)) for lit in clause)
                )
                for clause in model["constraints"]
            )
        ),
    )


def preconditions_hold(action: dict, state: set[str]) -> bool:
    return all(
        (lit["atom"] in state) == lit.get("positive", True) for lit in action["pre"]
    )


def forward(plan: list[dict], initial: set[str], goal: list[dict]) -> tuple[bool, int]:
    """Plain set interpreter: reject a false precondition before any state edit."""
    state = set(initial)
    executed = 0
    for action in plan:
        if not preconditions_hold(action, state):
            return False, executed
        state.difference_update(action["delete"])
        state.update(action["add"])
        executed += 1
    return all(
        (lit["atom"] in state) == lit.get("positive", True) for lit in goal
    ), executed


def recompute_row(
    row: dict, episode: dict, library: dict[str, tuple]
) -> tuple[dict, list[dict]]:
    """Reconstruct point metrics from raw state, plan, queries and chosen repair."""
    mismatches = []

    def check(field: str, actual: object, expected: object) -> None:
        if actual != expected:
            mismatches.append(
                {"field": field, "stored": actual, "recomputed": expected}
            )

    context, decision = episode["context"], row["decision"]
    state, nominal = set(episode["oracle_state"]), context["plan"]
    goal, evidence = context["goal"], dict(context["evidence"])
    menu = {query["name"]: query for query in context["queries"]}
    for field in ("parent_id", "family", "regime", "checkpoint", "schedule"):
        check(field, row.get(field), episode[field])
    check("context_sha256", row.get("context_sha256"), fingerprint(context))
    check("decision.method", decision["method"], row["method"])
    names, atoms, answers = (
        decision["query_names"],
        decision["query_atoms"],
        decision["query_answers"],
    )
    check("query_record_lengths", [len(atoms), len(answers)], [len(names), len(names)])
    check("unique_queries", len(set(names)), len(names))
    spent = 0
    for index, name in enumerate(names):
        if name not in menu:
            mismatches.append({"field": "unknown_query", "stored": name})
            continue
        query = menu[name]
        spent += query["cost"]
        expected_answer = {
            atom: episode["sensor_answers"][atom] for atom in query["atoms"]
        }
        if index < len(atoms):
            check(f"query_atoms[{index}]", sorted(atoms[index]), sorted(query["atoms"]))
        if index < len(answers):
            check(f"query_answers[{index}]", answers[index], expected_answer)
            check(
                f"query_boolean[{index}]",
                all(type(v) is bool for v in answers[index].values()),
                True,
            )
            evidence.update(answers[index])
    check("within_call_budget", len(names) <= row["budget"], True)
    check("within_cost_budget", spent <= row["budget"], True)
    check("decision.evidence", decision["evidence"], evidence)
    nominal_valid, _ = forward(nominal, state, goal)
    current_valid = not nominal or preconditions_hold(nominal[0], state)
    repair = row["recovery"]
    choice = decision["choice"]
    if choice not in {"CONTINUE", "RECOVER", "ABSTAIN"}:
        raise ValueError(f"Unknown decision choice: {choice}")
    selected = (
        nominal
        if choice == "CONTINUE"
        else (repair["plan"] if choice == "RECOVER" and repair["success"] else None)
    )
    if choice != "RECOVER":
        check("uninvoked_recovery_success", repair["success"], False)
    for action in selected or []:
        check(
            f"action_library:{action['name']}",
            canonical_action(action),
            library.get(action["name"]),
        )
    permitted = selected is not None
    selected_valid, executed = (
        forward(selected, state, goal) if permitted else (False, 0)
    )
    first_valid = not selected or preconditions_hold(selected[0], state)
    covers_initial = all(
        v is None or ((atom in state) == v) for atom, v in context["evidence"].items()
    )
    covers_final = all(
        v is None or ((atom in state) == v) for atom, v in evidence.items()
    )
    metrics = {
        "oracle_current_valid": current_valid,
        "oracle_plan_valid": nominal_valid,
        "evidence_covers_truth": covers_initial,
        "continuation_permitted": permitted,
        "false_current_permission": int(permitted and not first_valid),
        "invalid_continuation_permission": int(permitted and not selected_valid),
        "valid_continuation": int(permitted and selected_valid),
        "goal_completion": int(permitted and selected_valid),
        "abstention": int(not permitted),
        "unnecessary_abstention": int(not permitted and nominal_valid),
        "justified_abstention": int(not permitted and not nominal_valid),
        "recovery_invoked": int(choice == "RECOVER"),
        "recovery_success": int(repair["success"]),
        "query_count": len(names),
        "executed_actions": executed,
        "simulated_cost": len(names) + executed,
    }
    for field, expected in metrics.items():
        check(field, row.get(field), expected)
    return metrics | {"final_evidence_covers_truth": covers_final}, mismatches


def grouped_means(records: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for record in records:
        groups[
            (record["family"], record["regime"], record["budget"], record["method"])
        ].append(record)
    output = []
    for (family, regime, budget, method), group in sorted(groups.items()):
        parents = defaultdict(list)
        for record in group:
            parents[record["parent_id"]].append(record)
        parent_means = {
            parent: {metric: fmean(row[metric] for row in rows) for metric in METRICS}
            for parent, rows in sorted(parents.items())
        }
        output.append(
            {
                "family": family,
                "regime": regime,
                "budget": budget,
                "method": method,
                "rows": len(group),
                "independent_parents": len(parents),
                "row_means": {
                    metric: fmean(row[metric] for row in group) for metric in METRICS
                },
                "parent_weighted_means": {
                    metric: fmean(row[metric] for row in parent_means.values())
                    for metric in METRICS
                },
                "parent_means": parent_means,
            }
        )
    return output


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower, upper = math.floor(index), math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def paired_effects(
    records: list[dict], *, primary: bool, repetitions: int
) -> list[dict]:
    """M3 minus M1, averaging repeats before parent-stratified inference."""
    by_pair = defaultdict(dict)
    for row in records:
        if row["method"] in {"M1", "M3"}:
            if primary and not (
                row["budget"] in {1, 2, 3} and row["regime"] in PRIMARY_REGIMES
            ):
                continue
            by_pair[(row["episode_id"], row["budget"])][row["method"]] = row
    groups = defaultdict(list)
    for methods in by_pair.values():
        if methods.keys() != {"M1", "M3"}:
            continue
        base, proposal = methods["M1"], methods["M3"]
        difference = {
            "parent_id": base["parent_id"],
            "family": base["family"],
            **{metric: proposal[metric] - base[metric] for metric in METRICS},
        }
        if primary:
            groups[("ALL", "PRIMARY", -1)].append(difference)
            groups[(base["family"], "PRIMARY", -1)].append(difference)
        else:
            groups[("ALL", base["regime"], base["budget"])].append(difference)
            groups[(base["family"], base["regime"], base["budget"])].append(difference)
    output = []
    for (family, regime, budget), group in sorted(groups.items()):
        parents = defaultdict(list)
        for row in group:
            parents[row["parent_id"]].append(row)
        deltas = {
            parent: {metric: fmean(row[metric] for row in rows) for metric in METRICS}
            for parent, rows in sorted(parents.items())
        }
        result = {
            "family": family,
            "regime": regime,
            "budget": budget,
            "paired_rows": len(group),
            "independent_parents": len(parents),
            "parent_differences": deltas,
            "mean": {
                metric: fmean(row[metric] for row in deltas.values())
                for metric in METRICS
            },
        }
        if repetitions:
            strata = defaultdict(list)
            for parent, rows in parents.items():
                strata[rows[0]["family"]].append(parent)
            rng = random.Random(71603)
            samples = {metric: [] for metric in METRICS}
            for _ in range(repetitions):
                drawn = [
                    rng.choice(sorted(pool))
                    for _, pool in sorted(strata.items())
                    for _ in pool
                ]
                for metric in METRICS:
                    samples[metric].append(
                        fmean(deltas[parent][metric] for parent in drawn)
                    )
            result["independent_bootstrap_95"] = {
                metric: [quantile(values, 0.025), quantile(values, 0.975)]
                for metric, values in samples.items()
            }
            result["bootstrap"] = {
                "repetitions": repetitions,
                "seed": 71603,
                "rng": "stdlib.Random",
                "stratified_by": "family",
            }
        output.append(result)
    return output


def audit(root: Path, split: str, repetitions: int = 2000) -> dict:
    folder = root / split
    episode_path, decision_path = (
        folder / "episodes.jsonl.gz",
        folder / "decisions.jsonl.gz",
    )
    episodes_list, rows = read_jsonl(episode_path), read_jsonl(decision_path)
    prepared_path = root / "benchmarks/prepared_tasks.json"
    tasks = {task["task_id"]: task for task in json.loads(prepared_path.read_text())}
    status_path = folder / "status.json"
    status = json.loads(status_path.read_text())
    methods = set(status["methods"])
    episodes = {episode["episode_id"]: episode for episode in episodes_list}
    mismatches = []
    if len(episodes) != len(episodes_list):
        mismatches.append({"field": "duplicate_episode_ids"})
    expected_ids = {
        f"{task['task_id']}/{checkpoint}/{schedule}/{regime}"
        for task in tasks.values()
        if task["split"] == status["split"]
        for checkpoint in sorted({0, len(task["plan"]) // 2, len(task["plan"]) - 1})
        for schedule in range(4)
        for regime in REGIMES
    }
    if expected_ids != episodes.keys():
        mismatches.append(
            {
                "field": "episode_denominator",
                "missing": sorted(expected_ids - episodes.keys()),
                "extra": sorted(episodes.keys() - expected_ids),
            }
        )
    libraries = {
        task_id: {
            action["name"]: canonical_action(action) for action in task["actions"]
        }
        for task_id, task in tasks.items()
    }
    for episode_id, episode in episodes.items():
        task = tasks[episode["parent_id"]]
        context = episode["context"]
        actual = [canonical_action(a) for a in context["plan"]]
        expected = [canonical_action(a) for a in task["plan"][episode["checkpoint"] :]]
        if actual != expected:
            mismatches.append(
                {
                    "episode_id": episode_id,
                    "field": "nominal_plan_differs_from_prepared_task",
                }
            )
        if (
            canonical_model(context["model"]) != canonical_model(task["model"])
            or context["goal"] != task["goal"]
        ):
            mismatches.append(
                {
                    "episode_id": episode_id,
                    "field": "model_or_goal_differs_from_prepared_task",
                }
            )
        if episode["source_hashes"] != task["source_hashes"]:
            mismatches.append(
                {"episode_id": episode_id, "field": "public_source_hashes"}
            )
        if any(
            key in context
            for key in ("oracle_state", "actual_state", "regime", "sensor_answers")
        ):
            mismatches.append(
                {
                    "episode_id": episode_id,
                    "field": "evaluation_truth_leaked_into_context",
                }
            )
    expected_keys = {
        (episode_id, budget, method)
        for episode_id in episodes
        for budget in range(4)
        for method in methods
    }
    seen, records, skipped, comparison = set(), [], Counter(), {}
    for row in rows:
        key = row["episode_id"], row["budget"], row["method"]
        if key in seen:
            mismatches.append({"key": key, "field": "duplicate_decision"})
        seen.add(key)
        if "skip_reason" in row:
            skipped[row["skip_reason"]] += 1
            if row["method"] != "M4":
                mismatches.append({"key": key, "field": "non_oracle_skipped"})
            else:
                episode = episodes[row["episode_id"]]
                context = episode["context"]
                unknown = sum(
                    context["evidence"].get(atom) is None
                    for atom in context["model"]["atoms"]
                )
                legitimate = (
                    (
                        row["skip_reason"] == "MODEL_MISSPECIFICATION_REGIME"
                        and episode["regime"] in {"noise05", "invalidated"}
                    )
                    or ("unknown-atom limit" in row["skip_reason"] and unknown > 12)
                    or (
                        "query-menu limit" in row["skip_reason"]
                        and len(context["queries"]) > 6
                    )
                )
                if not legitimate:
                    mismatches.append(
                        {
                            "key": key,
                            "field": "unjustified_oracle_skip",
                            "reason": row["skip_reason"],
                        }
                    )
            continue
        episode = episodes[row["episode_id"]]
        metrics, failures = recompute_row(row, episode, libraries[episode["parent_id"]])
        mismatches.extend({"key": key, **failure} for failure in failures)
        records.append(
            {
                **{
                    field: row[field]
                    for field in (
                        "episode_id",
                        "parent_id",
                        "family",
                        "regime",
                        "budget",
                        "method",
                    )
                },
                **metrics,
            }
        )
        comparison[key] = row["decision"]
    if expected_keys != seen:
        mismatches.append(
            {
                "field": "decision_denominator",
                "missing": sorted(expected_keys - seen),
                "extra": sorted(seen - expected_keys),
            }
        )
    for episode_id, budget, method in sorted(seen):
        if method not in {"M3A", "M3_ablation", "M3_no_consequence"}:
            continue
        base = comparison.get((episode_id, budget, "M1"))
        ablation = comparison.get((episode_id, budget, method))
        if base is not None and ablation is not None:
            for field in (
                "choice",
                "status",
                "query_names",
                "query_answers",
                "evidence",
            ):
                if base[field] != ablation[field]:
                    mismatches.append(
                        {
                            "key": (episode_id, budget, method),
                            "field": f"ablation_vs_M1:{field}",
                        }
                    )
    for field, expected in (("episodes", len(episodes_list)), ("decisions", len(rows))):
        if status.get(field) != expected:
            mismatches.append(
                {
                    "field": f"status.{field}",
                    "stored": status.get(field),
                    "recomputed": expected,
                }
            )
    source_paths = [
        Path(__file__),
        Path("MONITORING_STUDY_PROTOCOL.md"),
        prepared_path,
        episode_path,
        decision_path,
        status_path,
    ]
    source_paths.extend(sorted(Path("src/dual_rec/monitoring").glob("*.py")))
    zero_bounds = []
    for method in sorted(methods):
        subset = [
            row
            for row in records
            if row["method"] == method
            and row["regime"] in PRIMARY_REGIMES
            and row["budget"] in {1, 2, 3}
        ]
        parents = {row["parent_id"] for row in subset}
        event_parents = {
            row["parent_id"] for row in subset if row["false_current_permission"]
        }
        if parents:
            zero_bounds.append(
                {
                    "method": method,
                    "independent_parents": len(parents),
                    "parents_with_false_current_permission": len(event_parents),
                    "one_sided_95_upper_if_zero": 1 - 0.05 ** (1 / len(parents))
                    if not event_parents
                    else None,
                }
            )
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "split": split,
        "checked_counts": {
            "episodes": len(episodes_list),
            "decision_rows": len(rows),
            "recomputed_decisions": len(records),
            "skipped_rows": sum(skipped.values()),
            "independent_parents": len({row["parent_id"] for row in records}),
        },
        "methods": sorted(methods),
        "mismatches": mismatches,
        "skip_reasons": dict(skipped),
        "audited_means": grouped_means(records),
        "paired_M3_minus_M1": paired_effects(records, primary=False, repetitions=0),
        "primary_M3_minus_M1": paired_effects(
            records, primary=True, repetitions=repetitions
        ),
        "zero_event_parent_bounds": zero_bounds,
        "truth_coverage": {
            "initial_rows_not_covered": sum(
                not row["evidence_covers_truth"] for row in records
            ),
            "final_rows_not_covered": sum(
                not row["final_evidence_covers_truth"] for row in records
            ),
        },
        "source_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_paths
            if path.is_file()
        },
        "limitations": [
            "Symbolic forward-execution audit; no physical safety inference",
            "Noisy and stale errors remain outcomes, not audit mismatches",
            "Uniform oracle ceiling is only its declared classification objective",
            "Independent stdlib bootstrap need not numerically match a NumPy bootstrap stream",
        ],
    }


def self_test() -> None:
    p = {"atom": "p", "positive": True}
    action = {"name": "make-q", "pre": [p], "add": ["q"], "delete": ["p"]}
    assert forward([action], {"p"}, [{"atom": "q", "positive": True}]) == (True, 1)
    assert forward([action], set(), []) == (False, 0)
    assert forward([], set(), [{"atom": "p", "positive": False}]) == (True, 0)
    context = {
        "plan": [action],
        "goal": [{"atom": "q", "positive": True}],
        "evidence": {"p": None},
        "queries": [{"name": "view", "atoms": ["p"], "cost": 1}],
    }
    episode = {
        "context": context,
        "oracle_state": ["p"],
        "sensor_answers": {"p": True},
        "parent_id": "parent",
        "family": "unit",
        "regime": "complete",
        "checkpoint": 0,
        "schedule": 0,
    }
    row = {
        **{
            field: episode[field]
            for field in ("parent_id", "family", "regime", "checkpoint", "schedule")
        },
        "method": "M1",
        "budget": 1,
        "context_sha256": fingerprint(context),
        "decision": {
            "method": "M1",
            "choice": "CONTINUE",
            "evidence": {"p": True},
            "query_names": ["view"],
            "query_atoms": [["p"]],
            "query_answers": [{"p": True}],
        },
        "recovery": {"success": False, "plan": []},
    }
    library = {action["name"]: canonical_action(action)}
    metrics, _ = recompute_row(row, episode, library)
    row.update(
        {
            key: value
            for key, value in metrics.items()
            if key != "final_evidence_covers_truth"
        }
    )
    assert recompute_row(row, episode, library)[1] == []
    failed_repair = json.loads(json.dumps(row))
    failed_repair["decision"]["choice"] = "RECOVER"
    failed_metrics, _ = recompute_row(failed_repair, episode, library)
    assert failed_metrics["abstention"] == 1
    assert failed_metrics["unnecessary_abstention"] == 1
    assert failed_metrics["recovery_invoked"] == 1
    noisy_episode = episode | {"oracle_state": []}
    noisy_metrics, _ = recompute_row(row, noisy_episode, library)
    assert noisy_metrics["false_current_permission"] == 1
    assert noisy_metrics["invalid_continuation_permission"] == 1
    assert noisy_metrics["goal_completion"] == 0
    row["goal_completion"] = 0
    assert any(
        failure["field"] == "goal_completion"
        for failure in recompute_row(row, episode, library)[1]
    )
    row["goal_completion"] = 1
    row["decision"]["query_answers"][0]["p"] = False
    assert any(
        failure["field"] == "query_answers[0]"
        for failure in recompute_row(row, episode, library)[1]
    )
    assert quantile([0, 1, 2, 3], 0.5) == 1.5
    pairs = []
    for parent in ("a", "b"):
        for method in ("M1", "M3"):
            pairs.append(
                {
                    **dict.fromkeys(METRICS, 0),
                    "parent_id": parent,
                    "episode_id": parent,
                    "family": "unit",
                    "regime": "missing10",
                    "budget": 1,
                    "method": method,
                    "goal_completion": int(parent == "a" and method == "M3"),
                }
            )
    pooled = next(
        group
        for group in paired_effects(pairs, primary=True, repetitions=20)
        if group["family"] == "ALL"
    )
    assert pooled["mean"]["goal_completion"] == 0.5
    assert pooled["parent_differences"]["a"]["goal_completion"] == 1
    assert len(grouped_means(pairs)) == 2
    print(
        "Independent audit self-tests passed: transitions, goals, metrics, tampering and sensor pairing"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument(
        "--split",
        choices=("baseline_development", "development", "qualification", "smoke"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.root is None or args.split is None:
        parser.error("--root and --split are required for a stored-data audit")
    output = args.output or args.root / args.split / "audit.json"
    if output.exists():
        raise FileExistsError("Preserve existing audit; choose a distinct --output")
    result = audit(args.root, args.split)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                **result["checked_counts"],
                "mismatches": len(result["mismatches"]),
                "output": str(output),
            }
        )
    )
    return int(bool(result["mismatches"]))


if __name__ == "__main__":
    raise SystemExit(main())
