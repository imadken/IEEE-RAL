"""Independent standard-library audit of recorded freshness-study outcomes.

No scheduler, belief or experiment implementation is imported. Predictions are
treated as policy outputs; their calibration labels and execution consequences
are independently calculated from the retained source actions and sensor tape.
"""

import argparse
import gzip
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

METRICS = (
    "safe_task_completion",
    "actual_task_completion",
    "unsafe_episode",
    "query_count",
    "execution_coverage",
    "abstention",
    "granted_actions",
    "false_permissions",
    "actually_executed_actions",
    "utility",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def action_signature(action):
    return (
        action["name"],
        tuple(sorted((p["atom"], p["positive"]) for p in action["pre"])),
        frozenset(action["add"]),
        frozenset(action["delete"]),
    )


def action_library_digest(actions):
    body = [
        {
            "name": a["name"],
            "pre": sorted((p["atom"], p["positive"]) for p in a["pre"]),
            "add": sorted(a["add"]),
            "delete": sorted(a["delete"]),
        }
        for a in sorted(actions, key=lambda action: action["name"])
    ]
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def apply_action(action, state):
    if not all((p["atom"] in state) == p["positive"] for p in action["pre"]):
        raise ValueError("False source action precondition: " + action["name"])
    return (state - set(action["delete"])) | set(action["add"])


def forward(plan, state, goal):
    state = set(state)
    grants = executed = errors = 0
    for action in plan:
        grants += 1
        try:
            state = apply_action(action, state)
        except ValueError:
            errors += 1
            break
        executed += 1
    holds = all((p["atom"] in state) == p["positive"] for p in goal)
    complete = executed == len(plan) and holds
    return {
        "granted_actions": grants,
        "actually_executed_actions": executed,
        "false_permissions": errors,
        "actual_goal_at_end": int(holds),
        "actual_task_completion": int(complete),
        "safe_task_completion": int(complete and errors == 0),
    }


def regressed(plan, goal):
    required = {(p["atom"], p["positive"]) for p in goal}
    for action in reversed(plan):
        effects = {(atom, True) for atom in action["add"]} | {
            (atom, False) for atom in action["delete"]
        }
        if any((atom, not value) in effects for atom, value in required):
            return None
        required = (required - effects) | {
            (p["atom"], p["positive"]) for p in action["pre"]
        }
        if any((atom, not value) in required for atom, value in required):
            return None
    return required


def relevant_atoms(context):
    base = context["base"]
    required = regressed(base["plan"], base["goal"])
    if required is None:
        return set()
    reached = {atom for atom, _ in required}
    changed = True
    while changed:
        changed = False
        for clause in base["model"]["constraints"]:
            names = {p["atom"] for p in clause}
            if names & reached and not names <= reached:
                reached.update(names)
                changed = True
    return reached


def project_cache(context):
    values = dict(context["base"]["evidence"])
    values.update(
        {a: v for a, v in context["cache_observations"].items() if v is not None}
    )
    for action in context["known_after_cache"]:
        values.update({a: False for a in action["delete"]})
        values.update({a: True for a in action["add"]})
    return values


def _close(a, b):
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return (
            math.isfinite(a)
            and math.isfinite(b)
            and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-10)
        )
    return a == b


def audit_episode(episode, task, source_digest=None):
    errors = []
    ctx = episode["context"]
    forbidden = {
        "oracle_state",
        "persistent_bias",
        "external_actions",
        "actual_event_hazard",
        "regime",
        "seed",
        "outcome",
    }
    if forbidden & ctx.keys() or forbidden & ctx["base"].keys():
        errors.append("Evaluator field entered runtime context")
    if episode["parent_id"] != task["task_id"] or episode["family"] != task["family"]:
        errors.append("Episode parent/family differs from public source task")
    if episode["source_hashes"] != task["source_hashes"]:
        errors.append("Public source fingerprint differs")
    library = {a["name"]: a for a in task["actions"]}
    if "actions_sha256" in episode and episode["actions_sha256"] != (
        source_digest or action_library_digest(task["actions"])
    ):
        errors.append("Actual source action-library fingerprint differs")
    nominal = task["plan"][episode["checkpoint"] :]
    if tuple(map(action_signature, nominal)) != tuple(
        map(action_signature, ctx["base"]["plan"])
    ):
        errors.append("Nominal plan differs from registered parent suffix")
    anchor_index = episode["checkpoint"] - int(episode["regime"] == "known_action")
    if set(ctx["trusted_anchor"]) != set(task["nominal_states"][anchor_index]):
        errors.append("Trusted anchor differs from the legitimate earlier public state")
    projected = {
        a: v if v is not None else a in ctx["trusted_anchor"]
        for a, v in ctx["cache_observations"].items()
    }
    for action in ctx["known_after_cache"]:
        projected.update({a: False for a in action["delete"]})
        projected.update({a: True for a in action["add"]})
    if projected != ctx["base"]["evidence"]:
        errors.append("Base evidence has an unlicensed current-state revelation")
    state = set(ctx["trusted_anchor"])
    events = episode["external_actions"]
    if len(events) != 2:
        return errors + ["Expected pre-cache and post-cache event records"]
    try:
        if events[0] is not None:
            state = apply_action(library[events[0]], state)
        if state != set(episode["oracle_cache_state"]):
            errors.append(
                "Pre-cache source transition does not produce retained cache world"
            )
        for action in ctx["known_after_cache"]:
            if action_signature(action) != action_signature(library[action["name"]]):
                errors.append("Known action differs from source library")
            state = apply_action(action, state)
        if events[1] is not None:
            state = apply_action(library[events[1]], state)
        if state != set(episode["oracle_state"]):
            errors.append(
                "Post-cache source transition does not produce retained current world"
            )
    except (ValueError, KeyError) as error:
        errors.append(str(error))
    for atom, value in ctx["cache_observations"].items():
        if value is not None:
            expected = (atom in episode["oracle_cache_state"]) != (
                atom in episode["persistent_bias"]
            )
            if type(value) is not bool or value != expected:
                errors.append(
                    "Cache observation does not match persistent sensor channel: "
                    + atom
                )
    return errors


def audit_row(episode, row, library, derived=None):
    """Return independently recalculated metrics plus discrepancies."""
    errors = []
    ctx = episode["context"]
    base = ctx["base"]
    decision = row["decision"]
    reads = decision["readings"]
    derived = derived or {}
    if "actions_sha256" in row:
        digest = derived.get("library_sha256") or action_library_digest(
            list(library.values())
        )
        if row["actions_sha256"] != digest:
            errors.append("Row action-library fingerprint differs")
        expected_full = hashlib.sha256(
            (row["context_sha256"] + digest).encode()
        ).hexdigest()
        if row.get("full_input_sha256") != expected_full:
            errors.append("Combined runtime-input fingerprint differs")
    query_atoms = derived.get("query_atoms")
    if query_atoms is None:
        query_atoms = set()
        for query in base["queries"]:
            if len(query["atoms"]) != 1 or query["cost"] != 1:
                errors.append("Common menu is not unit-cost single-atom sensing")
            query_atoms.update(query["atoms"])
    actual = set(episode["oracle_state"])
    cached = derived.get("cached") or project_cache(ctx)
    relevant = derived.get("relevant")
    if relevant is None:
        relevant = relevant_atoms(ctx) & query_atoms
    if row["method"] == "B6":
        current = {p["atom"] for p in base["plan"][0]["pre"]}
        oracle_menu = (
            sorted(query_atoms & current)
            + sorted((query_atoms & relevant) - current)
            + sorted(query_atoms - current - relevant)
        )[:8]
        if any(reading["atom"] not in oracle_menu for reading in reads):
            errors.append("B6 refilled or exceeded its fixed reduced query menu")
    wrong = {
        a for a in relevant if cached.get(a) is not None and cached[a] != (a in actual)
    }
    detected = None
    if len(reads) > row["budget"]:
        errors.append("Query budget exceeded")
    if len({r["atom"] for r in reads}) != len(reads):
        errors.append("Repeated atom query violates common channel contract")
    for index, reading in enumerate(reads, 1):
        atom = reading["atom"]
        if atom not in query_atoms:
            errors.append("Query absent from available menu: " + atom)
        stamp = ctx["age"] - ctx["query_delay"]
        if reading["measured_at"] != stamp or stamp not in {
            ctx["cache_time"],
            ctx["age"],
        }:
            errors.append("Measurement timestamp differs from declared sensor delay")
        world = (
            episode["oracle_state"]
            if stamp == ctx["age"]
            else episode["oracle_cache_state"]
        )
        response = (
            None
            if atom in episode["missing_queries"]
            else ((atom in world) != (atom in episode["persistent_bias"]))
        )
        if reading["value"] != response or reading.get("conflict", False):
            errors.append("Sensor response differs from shared tape: " + atom)
        if (
            detected is None
            and atom in wrong
            and reading["measured_at"] == ctx["age"]
            and reading["value"] is not None
            and not reading.get("conflict", False)
            and reading["value"] == (atom in actual)
        ):
            detected = index
    evidence = dict(cached)
    stamps = dict(ctx["observed_at"]) | dict(ctx["updated_at"])
    if row["method"] == "B3":
        for atom in relevant:
            if (
                max(0, ctx["age"] - stamps.get(atom, ctx["cache_time"]))
                > ctx["parameters"]["expiry_steps"]
            ):
                evidence[atom] = None
    for reading in reads:
        atom = reading["atom"]
        effect = None
        for action in ctx["known_after_cache"]:
            if atom in action["delete"]:
                effect = False
            if atom in action["add"]:
                effect = True
        if reading["measured_at"] <= ctx["cache_time"] and effect is not None:
            evidence[atom] = effect
        elif reading.get("conflict", False):
            evidence[atom] = None
            stamps[atom] = reading["measured_at"]
        elif reading["value"] is not None or row["method"] in {"B0", "B1"}:
            evidence[atom] = reading["value"]
            stamps[atom] = reading["measured_at"]
        if (
            row["method"] == "B3"
            and max(0, ctx["age"] - stamps.get(atom, ctx["cache_time"]))
            > ctx["parameters"]["expiry_steps"]
        ):
            evidence[atom] = None
    if decision["evidence"] != evidence:
        errors.append("Evidence does not reconstruct from cache/history/readings")
    expected_hash = derived.get("context_sha256")
    if expected_hash is None:
        serialized = json.dumps(ctx, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256(serialized.encode()).hexdigest()
    if row["context_sha256"] != expected_hash:
        errors.append("Runtime context fingerprint mismatch")
    choice = decision["choice"]
    selected = row["selected_plan"]
    repair = row["recovery"]
    accepted = choice == "RECOVER" and selected is not None
    if choice == "CONTINUE":
        if selected is None or tuple(map(action_signature, selected)) != tuple(
            map(action_signature, base["plan"])
        ):
            errors.append("CONTINUE does not select the unchanged nominal continuation")
    elif choice == "RECOVER":
        if selected is not None and (
            not repair["success"]
            or tuple(map(action_signature, selected))
            != tuple(map(action_signature, repair["plan"]))
        ):
            errors.append("RECOVER selected an uncertified or different repair plan")
    elif choice == "ABSTAIN":
        if selected is not None:
            errors.append("ABSTAIN improperly selected an executable plan")
    else:
        errors.append("Unknown permission choice")
    for action in selected or ():
        source = library.get(action["name"])
        if source is None or action_signature(action) != action_signature(source):
            errors.append("Selected action absent from common source library")
    granted = selected is not None
    initial_goal = int(
        all((lit["atom"] in actual) == lit["positive"] for lit in base["goal"])
    )
    outcome = (
        forward(selected, actual, base["goal"])
        if granted
        else {
            "granted_actions": 0,
            "actually_executed_actions": 0,
            "false_permissions": 0,
            "actual_goal_at_end": initial_goal,
            "actual_task_completion": 0,
            "safe_task_completion": 0,
        }
    )
    nominal = forward(base["plan"], actual, base["goal"])
    abstention = int(not granted)
    unnecessary = int(not granted and nominal["safe_task_completion"])
    unsafe = int(outcome["false_permissions"] > 0)
    current_atoms = {lit["atom"] for lit in base["plan"][0]["pre"]}
    queried_current = bool(current_atoms & {r["atom"] for r in reads})
    calibration = []
    for atom, risk in decision["stale_risks"].items():
        if (
            not isinstance(risk, (float, int))
            or not math.isfinite(risk)
            or not 0 <= risk <= 1
        ):
            errors.append("Nonprobabilistic stale-risk output")
        if atom in query_atoms and cached.get(atom) is not None:
            calibration.append([risk, int(cached[atom] != (atom in actual))])
    values = {
        **outcome,
        "decision_granted": int(granted),
        "refused_actions": abstention,
        "execution_coverage": int(outcome["granted_actions"] > 0),
        "authorized_empty_completion": int(
            granted and not selected and outcome["safe_task_completion"]
        ),
        "rechecked_actions": int(queried_current),
        "unsafe_episode": unsafe,
        "abstention": abstention,
        "unnecessary_abstention": unnecessary,
        "oracle_nominal_valid": nominal["safe_task_completion"],
        "query_count": len(reads),
        "recovery_invoked": int(choice == "RECOVER"),
        "recovery_certified": int(repair["success"]),
        "recovery_accepted": int(accepted),
        "recovery_actual_success": int(accepted and outcome["actual_task_completion"]),
        "utility": outcome["safe_task_completion"]
        - 5 * unsafe
        - 0.01 * len(reads)
        - 0.05 * unnecessary,
        "invalidated_relevant_claims": len(wrong),
        "direct_detected": int(detected is not None),
        "direct_detection_queries": detected,
        "direct_undetected": int(bool(wrong) and detected is None),
        "same_value_replies": sum(
            r["value"] is not None and r["value"] == cached.get(r["atom"])
            for r in reads
        ),
        "unrevalidated_false_claims": len(
            wrong
            - {
                r["atom"]
                for r in reads
                if r["measured_at"] == ctx["age"] and r["value"] is not None
            }
        ),
        "calibration_n": len(calibration),
        "calibration_squared_error_sum": sum((p - y) ** 2 for p, y in calibration),
        "external_event_count": sum(a is not None for a in episode["external_actions"]),
        "hidden_rate": episode["actual_event_hazard"],
        "sensor_error_actual": episode["actual_sensor_error"],
    }
    for key, value in values.items():
        if key not in row or not _close(value, row[key]):
            errors.append("Metric mismatch: " + key)
    stored = sorted(tuple(pair) for pair in row["calibration_pairs"])
    if stored != sorted(tuple(pair) for pair in calibration):
        errors.append(
            "Calibration truth labels differ from true-state/cache comparison"
        )
    if decision.get("belief_failure") is None and row["method"] not in {"B0", "B1"}:
        probability = decision["final_plan_probability"]
        theta = ctx["parameters"]["permission_threshold"]
        expected_choice = (
            "CONTINUE"
            if probability >= theta
            else "RECOVER"
            if probability <= 1 - theta
            else "ABSTAIN"
        )
        if choice != expected_choice:
            errors.append(
                "Terminal choice contradicts recorded posterior permission rule"
            )
    return values | {"initial_goal": initial_goal}, errors


def conditional_error_rate(rows):
    denominator = sum(row["granted_actions"] for row in rows)
    return (
        sum(row["false_permissions"] for row in rows) / denominator
        if denominator
        else None
    )


def parent_means(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["parent_id"]].append(row)
    return {
        parent: {
            metric: sum(r[metric] for r in group) / len(group) for metric in METRICS
        }
        for parent, group in sorted(grouped.items())
    }


def _quantile(values, probability):
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def paired_primary(rows, baseline, repetitions=2000):
    selected = [r for r in rows if r["regime"] == "hidden_nominal" and r["budget"] == 2]
    sides = {
        method: {r["episode_id"]: r for r in selected if r["method"] == method}
        for method in ("SVR", baseline)
    }
    common = sorted(sides["SVR"].keys() & sides[baseline].keys())
    if not common:
        return {"available": False}
    differences = defaultdict(list)
    families = {}
    for episode_id in common:
        a, b = sides["SVR"][episode_id], sides[baseline][episode_id]
        differences[a["parent_id"]].append({m: a[m] - b[m] for m in METRICS})
        families[a["parent_id"]] = a["family"]
    means = {
        p: {m: sum(r[m] for r in group) / len(group) for m in METRICS}
        for p, group in sorted(differences.items())
    }
    strata = defaultdict(list)
    for parent in means:
        strata[families[parent]].append(parent)
    rng = random.Random(71603)
    draws = {m: [] for m in METRICS}
    for _ in range(repetitions):
        sampled = [
            rng.choice(group) for _, group in sorted(strata.items()) for _ in group
        ]
        for metric in METRICS:
            draws[metric].append(sum(means[p][metric] for p in sampled) / len(sampled))
    return {
        "available": True,
        "left": "SVR",
        "right": baseline,
        "n_pairs": len(common),
        "n_parents": len(means),
        "complete_pairing": len(common) == len(sides["SVR"]) == len(sides[baseline]),
        "parent_differences": means,
        "metrics": {
            m: {
                "mean": sum(v[m] for v in means.values()) / len(means),
                "ci": [_quantile(draws[m], 0.025), _quantile(draws[m], 0.975)],
            }
            for m in METRICS
        },
    }


def audit(root, split):
    directory = root / split
    status_path = directory / "status.json"
    if not status_path.exists():
        raise ValueError(
            "Worker is incomplete; do not inspect an open qualification stream"
        )
    status = json.loads(status_path.read_text())
    tasks = {t["task_id"]: t for t in json.loads((root / "tasks.json").read_text())}
    selection = json.loads((root / "selection.json").read_text())
    libraries = {
        parent: {a["name"]: a for a in task["actions"]}
        for parent, task in tasks.items()
    }
    digests = {
        parent: action_library_digest(task["actions"]) for parent, task in tasks.items()
    }
    with gzip.open(directory / "episodes.jsonl.gz", "rt") as stream:
        episodes_list = [json.loads(line) for line in stream]
    episodes = {ep["episode_id"]: ep for ep in episodes_list}
    errors = []
    if len(episodes) != len(episodes_list):
        errors.append({"scope": "episodes", "error": "Duplicate episode identifiers"})
    for ep in episodes.values():
        parent = ep["parent_id"]
        if parent not in tasks:
            errors.append(
                {"episode": ep["episode_id"], "error": "Unknown public parent"}
            )
            continue
        if split == "qualification" and (
            int(parent.rsplit("-", 1)[1]) <= 12
            or tasks[parent]["split"] != "qualification"
        ):
            errors.append(
                {
                    "episode": ep["episode_id"],
                    "error": "Previously opened parent entered new qualification",
                }
            )
        if ep["context"]["parameters"] != selection["parameters"]:
            errors.append(
                {"episode": ep["episode_id"], "error": "Frozen parameters differ"}
            )
        for message in audit_episode(ep, tasks[parent], digests[parent]):
            errors.append({"episode": ep["episode_id"], "error": message})
    derived = {}
    for eid, ep in episodes.items():
        ctx = ep["context"]
        menu = {atom for q in ctx["base"]["queries"] for atom in q["atoms"]}
        if any(len(q["atoms"]) != 1 or q["cost"] != 1 for q in ctx["base"]["queries"]):
            errors.append(
                {"episode": eid, "error": "Non-unit singleton query in common menu"}
            )
        derived[eid] = {
            "query_atoms": menu,
            "cached": project_cache(ctx),
            "relevant": relevant_atoms(ctx) & menu,
            "library_sha256": digests[ep["parent_id"]],
            "context_sha256": hashlib.sha256(
                json.dumps(ctx, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
    seen = set()
    recomputed = []
    skipped = Counter()
    with gzip.open(directory / "decisions.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            key = row["episode_id"], row["method"], row["budget"]
            if key in seen:
                errors.append({"key": key, "error": "Duplicate method/budget decision"})
            seen.add(key)
            if row["episode_id"] not in episodes:
                errors.append({"key": key, "error": "Decision episode missing"})
                continue
            if row.get("skip_reason"):
                if row["method"] != "B6" or not re.search(
                    r"(32|8|3|100000|hypotheses|limit)", row["skip_reason"]
                ):
                    errors.append(
                        {"key": key, "error": "Unpermitted deployed-method exclusion"}
                    )
                skipped[row["skip_reason"]] += 1
                continue
            ep = episodes[row["episode_id"]]
            values, discrepancies = audit_row(
                ep, row, libraries[ep["parent_id"]], derived[ep["episode_id"]]
            )
            for message in discrepancies:
                errors.append({"key": key, "error": message})
            recomputed.append(
                {
                    k: row[k]
                    for k in (
                        "episode_id",
                        "parent_id",
                        "family",
                        "method",
                        "regime",
                        "budget",
                    )
                }
                | values
            )
    expected = {
        (eid, method, budget)
        for eid in episodes
        for method in status["methods"]
        for budget in status["budgets"]
    }
    if seen != expected:
        errors.append(
            {
                "scope": "denominators",
                "missing": len(expected - seen),
                "unexpected": len(seen - expected),
            }
        )
    if (
        len(episodes) != status["episodes"]
        or len(seen) != status["rows"]
        or len(recomputed) != status["evaluated"]
    ):
        errors.append(
            {
                "scope": "denominators",
                "error": "Completed status differs from audited counts",
            }
        )
    grouped = defaultdict(list)
    for row in recomputed:
        grouped[row["method"]].append(row)
    means = {}
    for method, records in sorted(grouped.items()):
        parents = parent_means(records)
        means[method] = {
            "n_decisions": len(records),
            "n_parents": len(parents),
            "metrics": {
                m: sum(v[m] for v in parents.values()) / len(parents) for m in METRICS
            },
            "false_per_granted_action": conditional_error_rate(records),
            "raw_granted_actions": sum(r["granted_actions"] for r in records),
            "raw_false_permissions": sum(r["false_permissions"] for r in records),
        }
    parents = sorted({ep["parent_id"] for ep in episodes.values()})
    return {
        "status": "PASS" if not errors else "FAIL",
        "split": split,
        "checked_counts": {
            "episodes": len(episodes),
            "rows": len(seen),
            "recomputed_rows": len(recomputed),
            "reference_skips": sum(skipped.values()),
            "parent_instances": len(parents),
        },
        "parents": parents,
        "mismatches": errors,
        "oracle_exclusions": dict(skipped),
        "oracle_cap_scope": "Exclusion types and complete denominators checked; exact 32-state quotient sizes not independently reconstructed",
        "audited_means": means,
        "primary_SVR_minus_baseline": paired_primary(
            recomputed, selection["primary_baseline"]
        ),
        "source_sha256": {
            str(p): sha(p)
            for p in (
                directory / "episodes.jsonl.gz",
                directory / "decisions.jsonl.gz",
                status_path,
                root / "tasks.json",
                root / "selection.json",
                Path(__file__),
            )
        },
        "limitations": "Probability estimates and posterior threshold admission of a certified repair are policy outputs; this audit independently verifies their recorded choices, sensors, calibration labels and actual execution outcomes, not the Bayesian implementation.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "qualification"), required=True
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.root / args.split / "audit.json"
    if output.exists():
        raise FileExistsError("Preserve previous audits; choose a different output")
    result = audit(args.root, args.split)
    output.write_text(json.dumps(result, indent=2, allow_nan=False))
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
