"""Paired checkpoint execution with evaluator truth isolated from scheduling."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter

from .contracts import Episode
from .methods import run_method
from .observations import generate_episodes
from .recovery import recover
from .semantics import Action, apply_action


def forward(plan: tuple[Action, ...], state: frozenset[str], goal) -> tuple[bool, int]:
    executed = 0
    for action in plan:
        try:
            state = apply_action(action, state)
        except ValueError:
            return False, executed
        executed += 1
    return all((lit.atom in state) == lit.positive for lit in goal), executed


def evaluate(episode: Episode, method: str, budget: int, context_sha256: str) -> dict:
    menu = {query.name: query for query in episode.context.queries}

    def sense(name):
        return {atom: episode.sensor_answers[atom] for atom in sorted(menu[name].atoms)}

    decision = run_method(episode.context, method, budget, sense)
    full_valid, _ = forward(
        episode.context.plan, episode.oracle_state, episode.context.goal
    )
    current_valid = all(
        (lit.atom in episode.oracle_state) == lit.positive
        for lit in episode.context.plan[0].pre
    )
    repair = {"success": False, "reason": "NOT_INVOKED", "plan": []}
    selected = None
    recovery_seconds = 0.0
    if decision.choice == "CONTINUE":
        selected = episode.context.plan
    elif decision.choice == "RECOVER":
        before = perf_counter()
        repair = recover(episode.context, dict(decision.evidence), episode.actions)
        recovery_seconds = perf_counter() - before
        if repair["success"]:
            selected = tuple(Action.model_validate(a) for a in repair["plan"])
    permitted = selected is not None
    selected_valid, executed = (
        forward(selected, episode.oracle_state, episode.context.goal)
        if permitted
        else (False, 0)
    )
    first_valid = (
        all(
            (lit.atom in episode.oracle_state) == lit.positive
            for lit in selected[0].pre
        )
        if selected
        else True
    )
    covers = all(
        value is None or ((atom in episode.oracle_state) == value)
        for atom, value in episode.context.evidence.items()
    )
    detected = decision.status in {"INVALID", "CURRENT_INVALID"}
    return {
        "episode_id": episode.episode_id,
        "parent_id": episode.parent_id,
        "family": episode.family,
        "regime": episode.regime,
        "checkpoint": episode.checkpoint,
        "schedule": episode.schedule,
        "method": method,
        "budget": budget,
        "context_sha256": context_sha256,
        "oracle_current_valid": current_valid,
        "oracle_plan_valid": full_valid,
        "evidence_covers_truth": covers,
        "continuation_permitted": permitted,
        "false_current_permission": int(permitted and not first_valid),
        "invalid_continuation_permission": int(permitted and not selected_valid),
        "valid_continuation": int(permitted and selected_valid),
        "goal_completion": int(permitted and selected_valid),
        "abstention": int(not permitted),
        "unnecessary_abstention": int(not permitted and full_valid),
        "justified_abstention": int(not permitted and not full_valid),
        "recovery_invoked": int(decision.choice == "RECOVER"),
        "recovery_success": int(repair["success"]),
        "query_count": len(decision.query_names),
        "query_seconds": decision.query_seconds,
        "decision_seconds": decision.decision_seconds,
        "recovery_seconds": recovery_seconds,
        "total_decision_seconds": decision.decision_seconds + recovery_seconds,
        "executed_actions": executed,
        "simulated_cost": len(decision.query_names) + executed,
        "irrelevant_atom_reads": decision.query_irrelevant_atoms,
        "total_atom_reads": decision.query_total_atoms,
        "detected_invalid": int(detected),
        "detection_delay_queries": len(decision.query_names) if detected else None,
        "classification_resolved": int(decision.status in {"VALID", "INVALID"}),
        "decision": decision.model_dump(mode="json"),
        "recovery": repair,
    }


def run(root: Path, output: Path, split: str, methods: tuple[str, ...]) -> dict:
    if output.exists():
        raise FileExistsError("Do not overwrite an experimental attempt")
    output.mkdir(parents=True)
    prepared = json.loads((root / "benchmarks/prepared_tasks.json").read_text())
    counts = {"episodes": 0, "decisions": 0, "parents": set(), "oracle_skips": {}}
    started = perf_counter()
    with (
        gzip.open(output / "episodes.jsonl.gz", "wt", compresslevel=1) as episodes_file,
        gzip.open(
            output / "decisions.jsonl.gz", "wt", compresslevel=1
        ) as decisions_file,
    ):
        for episode in generate_episodes(prepared, split):
            payload = episode.model_dump(mode="json", exclude={"actions"})
            context_json = json.dumps(
                payload["context"], sort_keys=True, separators=(",", ":")
            )
            context_hash = hashlib.sha256(context_json.encode()).hexdigest()
            episodes_file.write(json.dumps(payload) + "\n")
            counts["episodes"] += 1
            counts["parents"].add(episode.parent_id)
            for budget in range(4):
                for method in methods:
                    if method == "M4" and episode.regime in {"noise05", "invalidated"}:
                        row = {
                            "episode_id": episode.episode_id,
                            "parent_id": episode.parent_id,
                            "family": episode.family,
                            "regime": episode.regime,
                            "method": method,
                            "budget": budget,
                            "skip_reason": "MODEL_MISSPECIFICATION_REGIME",
                        }
                    else:
                        try:
                            row = evaluate(episode, method, budget, context_hash)
                        except Exception as error:
                            from .oracle import OracleLimit

                            if method != "M4" or not isinstance(error, OracleLimit):
                                (output / "FAILURE.json").write_text(
                                    json.dumps(
                                        {
                                            "episode_id": episode.episode_id,
                                            "method": method,
                                            "budget": budget,
                                            "error": repr(error),
                                        },
                                        indent=2,
                                    )
                                )
                                raise
                            row = {
                                "episode_id": episode.episode_id,
                                "parent_id": episode.parent_id,
                                "family": episode.family,
                                "regime": episode.regime,
                                "method": method,
                                "budget": budget,
                                "skip_reason": str(error),
                            }
                    if "skip_reason" in row:
                        reason = row["skip_reason"]
                        counts["oracle_skips"][reason] = (
                            counts["oracle_skips"].get(reason, 0) + 1
                        )
                    else:
                        assert len(row["decision"]["query_names"]) <= budget
                        after = json.dumps(
                            episode.context.model_dump(mode="json"),
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        assert (
                            hashlib.sha256(after.encode()).hexdigest() == context_hash
                        ), "Method changed shared inputs"
                    decisions_file.write(json.dumps(row) + "\n")
                    counts["decisions"] += 1
            if counts["episodes"] % 96 == 0:
                print(
                    json.dumps(
                        {
                            "episodes": counts["episodes"],
                            "decisions": counts["decisions"],
                            "wall_seconds": perf_counter() - started,
                        }
                    ),
                    flush=True,
                )
    counts["parents"] = sorted(counts["parents"])
    counts["wall_seconds"] = perf_counter() - started
    counts["methods"] = methods
    counts["split"] = split
    (output / "status.json").write_text(json.dumps(counts, indent=2))
    print(json.dumps(counts), flush=True)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "qualification", "smoke"), required=True
    )
    parser.add_argument("--methods", default="M0,M1,M2")
    args = parser.parse_args()
    run(args.root, args.output, args.split, tuple(args.methods.split(",")))


if __name__ == "__main__":
    main()
