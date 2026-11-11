"""Paired public-task episodes; true states remain in this evaluator only."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter

from dual_rec.monitoring.recovery import recover
from dual_rec.monitoring.semantics import Action, apply_action, regress

from .belief import Belief, OracleLimit, build_belief
from .contracts import FreshEpisode, Parameters, Reading
from .episodes import generate_episodes
from .methods import project_cache, run_policy

METHODS = (
    "B0",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "SVR",
    "SVR_no_impact",
    "SVR_no_risk",
)


def action_library_digest(actions):
    body = [
        {
            "name": a.name,
            "pre": sorted((lit.atom, lit.positive) for lit in a.pre),
            "add": sorted(a.add),
            "delete": sorted(a.delete),
        }
        for a in sorted(actions, key=lambda item: item.name)
    ]
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def forward(plan, state, goal):
    grants = executed = errors = 0
    for action in plan:
        grants += 1
        try:
            state = apply_action(action, state)
        except ValueError:
            errors += 1
            break
        executed += 1
    goal_holds = all((lit.atom in state) == lit.positive for lit in goal)
    completed = executed == len(plan) and goal_holds
    return {
        "granted_actions": grants,
        "actually_executed_actions": executed,
        "false_permissions": errors,
        "actual_goal_at_end": int(goal_holds),
        "actual_task_completion": int(completed),
        "safe_task_completion": int(completed and errors == 0),
    }


class RecoveryCache:
    """Same declared knowledge/plan gets the same bounded recovery opportunity."""

    def __init__(self):
        self.cache = {}

    def candidate(self, episode: FreshEpisode, knowledge: dict):
        signature = json.dumps(
            {
                "parent": episode.parent_id,
                "plan": [a.name for a in episode.context.base.plan],
                "knowledge": knowledge,
            },
            sort_keys=True,
        )
        key = hashlib.sha256(signature.encode()).hexdigest()
        hit = key in self.cache
        before = perf_counter()
        if not hit:
            context = episode.context.base.model_copy(update={"evidence": knowledge})
            self.cache[key] = recover(context, knowledge, episode.context.actions)
        return self.cache[key] | {
            "cache_hit": hit,
            "lookup_seconds": perf_counter() - before,
            "knowledge_sha256": key,
        }


def evaluate(
    episode: FreshEpisode,
    method: str,
    budget: int,
    initial: Belief,
    recovery_cache: RecoveryCache,
    context_hash: str,
) -> dict:
    ctx = episode.context

    def sense(atom):
        measured = ctx.age - ctx.query_delay
        world = (
            episode.oracle_state if measured == ctx.age else episode.oracle_cache_state
        )
        value = (
            None
            if atom in episode.missing_queries
            else ((atom in world) != (atom in episode.persistent_bias))
        )
        return Reading(atom=atom, value=value, measured_at=measured)

    decision = run_policy(ctx, method, budget, sense, initial)
    posterior = initial
    for reading in decision.readings:
        posterior = posterior.condition(reading)
    selected = None
    repair = {"success": False, "reason": "NOT_INVOKED", "plan": []}
    repair_accepted = False
    if decision.choice == "CONTINUE":
        selected = ctx.base.plan
    elif decision.choice == "RECOVER":
        if method in {"B0", "B1"}:
            knowledge = dict(decision.evidence)
        else:
            theta = ctx.parameters.permission_threshold
            knowledge = {}
            for atom in sorted(ctx.base.model.atoms):
                probability = posterior.marginal(atom)
                knowledge[atom] = (
                    True
                    if probability >= theta
                    else False
                    if probability <= 1 - theta
                    else None
                )
        repair = recovery_cache.candidate(episode, knowledge)
        if repair["success"]:
            candidate = tuple(Action.model_validate(a) for a in repair["plan"])
            repair_accepted = (
                method in {"B0", "B1"}
                or posterior.probability(candidate, ctx.base.goal)
                >= ctx.parameters.permission_threshold
            )
            if repair_accepted:
                selected = candidate
    nominal = forward(ctx.base.plan, episode.oracle_state, ctx.base.goal)
    granted = selected is not None
    outcome = (
        forward(selected, episode.oracle_state, ctx.base.goal)
        if granted
        else {
            "granted_actions": 0,
            "actually_executed_actions": 0,
            "false_permissions": 0,
            "actual_goal_at_end": int(
                all(
                    (g.atom in episode.oracle_state) == g.positive
                    for g in ctx.base.goal
                )
            ),
            "actual_task_completion": 0,
            "safe_task_completion": 0,
        }
    )
    cached = project_cache(ctx)
    dynamic = {next(iter(query.atoms)) for query in ctx.base.queries}
    required = regress(ctx.base.plan, ctx.base.goal) or ()
    relevant = {lit.atom for lit in required} & dynamic
    wrong = {
        atom
        for atom in relevant
        if cached.get(atom) is not None
        and cached[atom] != (atom in episode.oracle_state)
    }
    detected = None
    for number, reading in enumerate(decision.readings, 1):
        if (
            reading.atom in wrong
            and reading.measured_at == ctx.age
            and reading.value is not None
            and not reading.conflict
            and reading.value == (reading.atom in episode.oracle_state)
        ):
            detected = number
            break
    calibration = [
        (risk, int(cached.get(atom) != (atom in episode.oracle_state)))
        for atom, risk in decision.stale_risks.items()
        if atom in dynamic and cached.get(atom) is not None
    ]
    q = len(decision.readings)
    abstention = not granted
    unnecessary = abstention and bool(nominal["safe_task_completion"])
    unsafe = outcome["false_permissions"] > 0
    queried_current = bool(
        {r.atom for r in decision.readings} & {p.atom for p in ctx.base.plan[0].pre}
    )
    return {
        "episode_id": episode.episode_id,
        "parent_id": episode.parent_id,
        "family": episode.family,
        "regime": episode.regime,
        "checkpoint": episode.checkpoint,
        "schedule": episode.schedule,
        "method": method,
        "budget": budget,
        "context_sha256": context_hash,
        **outcome,
        "decision_granted": int(granted),
        "refused_actions": int(abstention),
        "execution_coverage": int(outcome["granted_actions"] > 0),
        "authorized_empty_completion": int(
            granted and not selected and outcome["safe_task_completion"]
        ),
        "rechecked_actions": int(queried_current),
        "unsafe_episode": int(unsafe),
        "abstention": int(abstention),
        "unnecessary_abstention": int(unnecessary),
        "oracle_nominal_valid": nominal["safe_task_completion"],
        "query_count": q,
        "sensor_seconds": decision.sensor_seconds,
        "decision_seconds": decision.decision_seconds,
        "recovery_invoked": int(decision.choice == "RECOVER"),
        "recovery_certified": int(repair["success"]),
        "recovery_accepted": int(repair_accepted),
        "recovery_actual_success": int(
            repair_accepted and outcome["actual_task_completion"]
        ),
        "recovery": repair,
        "decision": decision.model_dump(mode="json"),
        "utility": outcome["safe_task_completion"]
        - 5 * int(unsafe)
        - 0.01 * q
        - 0.05 * int(unnecessary),
        "invalidated_relevant_claims": len(wrong),
        "direct_detected": int(detected is not None),
        "direct_detection_queries": detected,
        "direct_undetected": int(bool(wrong) and detected is None),
        "same_value_replies": sum(
            r.value is not None and r.value == cached.get(r.atom)
            for r in decision.readings
        ),
        "unrevalidated_false_claims": len(
            wrong
            - {
                r.atom
                for r in decision.readings
                if r.measured_at == ctx.age and r.value is not None
            }
        ),
        "calibration_n": len(calibration),
        "calibration_squared_error_sum": sum((p - y) ** 2 for p, y in calibration),
        "calibration_pairs": calibration,
        "external_event_count": sum(a is not None for a in episode.external_actions),
        "hidden_rate": episode.actual_event_hazard,
        "sensor_error_actual": episode.actual_sensor_error,
        "selected_plan": [a.model_dump(mode="json") for a in selected]
        if selected is not None
        else None,
    }


def run(
    root: Path,
    output: Path,
    split: str,
    parameters: Parameters,
    methods=METHODS,
    budgets=(0, 1, 2, 3),
    limit=None,
    regimes=None,
):
    if output.exists():
        raise FileExistsError("Never overwrite a research attempt")
    if split == "qualification" and limit is not None:
        raise ValueError("Qualification cannot silently limit its episode count")
    output.mkdir(parents=True)
    tasks = json.loads((root / "tasks.json").read_text())
    counts = {
        "episodes": 0,
        "rows": 0,
        "evaluated": 0,
        "reference_skips": {},
        "parents": set(),
    }
    started = perf_counter()
    cache = RecoveryCache()
    libraries = {}
    with (
        gzip.open(output / "episodes.jsonl.gz", "wt", compresslevel=1) as ep_stream,
        gzip.open(output / "decisions.jsonl.gz", "wt", compresslevel=1) as row_stream,
    ):
        for episode in generate_episodes(tasks, split, parameters):
            if regimes and episode.regime not in regimes:
                continue
            if limit is not None and counts["episodes"] >= limit:
                break
            payload = episode.model_dump(mode="json", exclude={"context": {"actions"}})
            serialized = json.dumps(
                payload["context"], sort_keys=True, separators=(",", ":")
            )
            fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
            if episode.parent_id not in libraries:
                libraries[episode.parent_id] = action_library_digest(
                    episode.context.actions
                )
            payload["actions_sha256"] = libraries[episode.parent_id]
            ep_stream.write(json.dumps(payload) + "\n")
            before = perf_counter()
            initial = build_belief(episode.context)
            cold_seconds = perf_counter() - before
            counts["episodes"] += 1
            counts["parents"].add(episode.parent_id)
            for budget in budgets:
                for method in methods:
                    try:
                        row = evaluate(
                            episode, method, budget, initial, cache, fingerprint
                        )
                        row["common_belief_build_seconds"] = cold_seconds
                        row["actions_sha256"] = libraries[episode.parent_id]
                        row["full_input_sha256"] = hashlib.sha256(
                            (fingerprint + libraries[episode.parent_id]).encode()
                        ).hexdigest()
                        counts["evaluated"] += 1
                    except OracleLimit as error:
                        if method != "B6":
                            raise
                        reason = str(error)
                        row = {
                            "episode_id": episode.episode_id,
                            "parent_id": episode.parent_id,
                            "family": episode.family,
                            "regime": episode.regime,
                            "budget": budget,
                            "method": method,
                            "skip_reason": reason,
                        }
                        counts["reference_skips"][reason] = (
                            counts["reference_skips"].get(reason, 0) + 1
                        )
                    row_stream.write(json.dumps(row, allow_nan=False) + "\n")
                    counts["rows"] += 1
            if counts["episodes"] % 32 == 0:
                print(
                    json.dumps(
                        {
                            "episodes": counts["episodes"],
                            "rows": counts["rows"],
                            "seconds": perf_counter() - started,
                        }
                    ),
                    flush=True,
                )
    counts["parents"] = sorted(counts["parents"])
    counts["wall_seconds"] = perf_counter() - started
    counts["methods"] = methods
    counts["budgets"] = budgets
    counts["split"] = split
    (output / "status.json").write_text(json.dumps(counts, indent=2))
    print(json.dumps(counts), flush=True)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "qualification"), required=True
    )
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--budgets", default="0,1,2,3")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--regimes")
    args = parser.parse_args()
    raw = json.loads(args.parameters.read_text())
    parameters = Parameters.model_validate(raw.get("parameters", raw))
    run(
        args.root,
        args.output,
        args.split,
        parameters,
        tuple(args.methods.split(",")),
        tuple(int(b) for b in args.budgets.split(",")),
        args.limit,
        tuple(args.regimes.split(",")) if args.regimes else None,
    )


if __name__ == "__main__":
    main()
