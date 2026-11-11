"""Model-relative query-relevance audit with a bounded independent cross-check.

The closure-based label is conservative and conditional on the declared model
and evidence being truthful. Zero immediate resolution value is a different
property: jointly useful observations can each have zero immediate value. Neither
label establishes that a measurement cannot expose stale or incorrect evidence.
"""

import gzip
import hashlib
import json
from itertools import product
from pathlib import Path

from .contracts import Context
from .semantics import Lit, possible, relevant_atoms

METHODS = ("M0", "M1", "M2", "M3")
EXACT_EVENT_LIMIT = 256
MAX_EXACT_UNKNOWN = 12


def _read(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as stream:
        for line in stream:
            yield json.loads(line)


def _input(split_dir: Path, name: str) -> Path:
    for suffix in (".jsonl.gz", ".jsonl"):
        path = split_dir / (name + suffix)
        if path.exists():
            return path
    raise FileNotFoundError(f"Missing {name} records")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_partition(
    context: Context, evidence: dict[str, bool | None], query_atoms: frozenset[str]
) -> dict:
    """Enumerate raw worlds and forward transitions without SAT or regression."""
    known = {atom: value for atom, value in evidence.items() if value is not None}
    unknown = sorted(context.model.atoms - known.keys())
    if len(unknown) > MAX_EXACT_UNKNOWN:
        return {"status": "UNKNOWN_LIMIT", "unknown_atoms": len(unknown)}
    partitions: dict[tuple[bool, ...], set[bool]] = {}
    labels = set()
    worlds = 0
    ordered_query = sorted(query_atoms)
    for values in product((False, True), repeat=len(unknown)):
        world = known | dict(zip(unknown, values))
        if not all(
            any(world[lit.atom] == lit.positive for lit in clause)
            for clause in context.model.constraints
        ):
            continue
        worlds += 1
        answer = tuple(world[atom] for atom in ordered_query)
        current = dict(world)
        valid = True
        for action in context.plan:
            if not all(current[lit.atom] == lit.positive for lit in action.pre):
                valid = False
                break
            current.update({atom: False for atom in action.delete})
            current.update({atom: True for atom in action.add})
        valid = valid and all(current[lit.atom] == lit.positive for lit in context.goal)
        labels.add(valid)
        partitions.setdefault(answer, set()).add(valid)
    if not worlds:
        return {"status": "INCONSISTENT", "unknown_atoms": len(unknown)}
    return {
        "status": "EXAMINED",
        "unknown_atoms": len(unknown),
        "worlds": worlds,
        "prior_validity_labels": sorted(labels),
        "answer_partitions": len(partitions),
        "zero_immediate_resolution_value": all(
            part == labels for part in partitions.values()
        ),
        "some_answer_resolves_previously_mixed_labels": len(labels) == 2
        and any(len(part) == 1 for part in partitions.values()),
        "all_answers_resolve_previously_mixed_labels": len(labels) == 2
        and all(len(part) == 1 for part in partitions.values()),
    }


def _counter() -> dict[str, int]:
    return dict.fromkeys(
        (
            "decisions",
            "query_events",
            "consistent_evidence_query_events",
            "inconsistent_evidence_query_events",
            "wholly_model_structurally_irrelevant_calls",
            "total_atom_reads",
            "atom_reads_outside_model_relevance_closure",
            "already_known_atom_reads",
            "observed_answer_outside_prior_model_events",
            "exact_prefix_selected_events",
            "exact_examined_events",
            "exact_unknown_limit_skips",
            "exact_inconsistent_skips",
            "exact_prefix_omitted_events",
            "zero_immediate_resolution_value_calls",
            "some_answer_resolves_previously_mixed_labels_calls",
            "all_answers_resolve_previously_mixed_labels_calls",
            "already_resolved_before_query_calls",
        ),
        0,
    )


def audit_queries(split_dir: Path, out: Path) -> dict:
    """Audit completed raw records, selecting the first 256 query events/method.

    Prefix selection is by source record order, before checking unknown counts
    or outcomes. It is a bounded diagnostic, not a representative population
    estimate. All events receive the conservative structural check.
    """
    status_path = split_dir / "status.json"
    if not status_path.exists():
        raise ValueError("Only completed splits may be audited")
    status = json.loads(status_path.read_text())
    episodes_path = _input(split_dir, "episodes")
    decisions_path = _input(split_dir, "decisions")
    contexts, metadata = {}, {}
    for row in _read(episodes_path):
        episode_id = row["episode_id"]
        if episode_id in contexts:
            raise ValueError("Duplicate episode identifier")
        contexts[episode_id] = Context.model_validate(row["context"])
        metadata[episode_id] = {"regime": row["regime"], "parent_id": row["parent_id"]}
    if status.get("episodes", len(contexts)) != len(contexts):
        raise ValueError("Episode denominator differs from completed split")
    events_path = out.with_name(out.stem + "_events.jsonl.gz")
    if out.exists() or events_path.exists():
        raise FileExistsError("Do not overwrite an existing query audit")
    out.parent.mkdir(parents=True, exist_ok=True)
    counters = {method: _counter() for method in METHODS}
    strata = {}
    record_count = 0
    with gzip.open(events_path, "xt", compresslevel=1) as events:
        for row in _read(decisions_path):
            record_count += 1
            method = row["method"]
            if method not in METHODS or "skip_reason" in row:
                continue
            context = contexts[row["episode_id"]]
            decision = row["decision"]
            evidence = dict(context.evidence)
            regime = metadata[row["episode_id"]]["regime"]
            stratum = strata.setdefault(regime, {}).setdefault(method, _counter())
            groups = (counters[method], stratum)
            for group in groups:
                group["decisions"] += 1
            names = decision["query_names"]
            atoms_trace = decision["query_atoms"]
            answers = decision["query_answers"]
            if not (len(names) == len(atoms_trace) == len(answers)) or len(
                set(names)
            ) != len(names):
                raise ValueError("Malformed query trace")
            menu = {query.name: query for query in context.queries}
            if sum(menu[name].cost for name in names) > row["budget"]:
                raise ValueError("Query trace exceeds declared budget")
            for index, (name, atoms, response) in enumerate(
                zip(names, atoms_trace, answers)
            ):
                queried = frozenset(atoms)
                if (
                    queried != menu[name].atoms
                    or set(response) != queried
                    or any(type(v) is not bool for v in response.values())
                ):
                    raise ValueError("Query trace differs from declared menu")
                closure = relevant_atoms(
                    context.model, evidence, context.plan, context.goal
                )
                consistent = possible(context.model, evidence)
                outside = queried - closure
                unknown_queried = {
                    atom for atom in queried if evidence.get(atom) is None
                }
                answer_possible = possible(
                    context.model,
                    evidence,
                    tuple(
                        Lit(atom=atom, positive=value)
                        for atom, value in response.items()
                    ),
                )
                event = {
                    "episode_id": row["episode_id"],
                    "parent_id": metadata[row["episode_id"]]["parent_id"],
                    "method": method,
                    "budget": row["budget"],
                    "regime": regime,
                    "query_index": index,
                    "query_name": name,
                    "query_atoms": sorted(queried),
                    "queried_unknown_atoms": sorted(unknown_queried),
                    "atoms_outside_model_relevance_closure": sorted(outside)
                    if consistent
                    else None,
                    "wholly_model_structurally_irrelevant": not bool(
                        unknown_queried & closure
                    )
                    if consistent
                    else None,
                    "evidence_consistent": consistent,
                    "observed_answer_possible_under_prior_model": answer_possible
                    if consistent
                    else None,
                    "prior_evidence_sha256": hashlib.sha256(
                        json.dumps(evidence, sort_keys=True).encode()
                    ).hexdigest(),
                }
                for group in groups:
                    group["query_events"] += 1
                    group["total_atom_reads"] += len(queried)
                    group["already_known_atom_reads"] += len(queried - unknown_queried)
                    group[
                        "consistent_evidence_query_events"
                        if consistent
                        else "inconsistent_evidence_query_events"
                    ] += 1
                    if consistent:
                        group["atom_reads_outside_model_relevance_closure"] += len(
                            outside
                        )
                        group["wholly_model_structurally_irrelevant_calls"] += int(
                            not (unknown_queried & closure)
                        )
                        group["observed_answer_outside_prior_model_events"] += int(
                            not answer_possible
                        )
                if counters[method]["query_events"] <= EXACT_EVENT_LIMIT:
                    exact = _exact_partition(context, evidence, queried)
                    event["exact"] = exact
                    for group in groups:
                        group["exact_prefix_selected_events"] += 1
                        if exact["status"] == "EXAMINED":
                            group["exact_examined_events"] += 1
                            group["zero_immediate_resolution_value_calls"] += int(
                                exact["zero_immediate_resolution_value"]
                            )
                            group[
                                "some_answer_resolves_previously_mixed_labels_calls"
                            ] += int(
                                exact["some_answer_resolves_previously_mixed_labels"]
                            )
                            group[
                                "all_answers_resolve_previously_mixed_labels_calls"
                            ] += int(
                                exact["all_answers_resolve_previously_mixed_labels"]
                            )
                            group["already_resolved_before_query_calls"] += int(
                                len(exact["prior_validity_labels"]) == 1
                            )
                        elif exact["status"] == "UNKNOWN_LIMIT":
                            group["exact_unknown_limit_skips"] += 1
                        else:
                            group["exact_inconsistent_skips"] += 1
                else:
                    event["exact"] = {"status": "PREFIX_LIMIT"}
                    for group in groups:
                        group["exact_prefix_omitted_events"] += 1
                events.write(json.dumps(event) + "\n")
                evidence.update(response)
            if evidence != decision["evidence"]:
                raise ValueError(
                    "Final evidence differs from reconstructed query trace"
                )
    if status.get("decisions", record_count) != record_count:
        raise ValueError("Decision denominator differs from completed split")
    result = {
        "scope": "Model-relative structural query audit; no physical irrelevance guarantee",
        "zero_immediate_resolution_value_scope": "Every possible answer retains the prior possible-validity-label set; this does not imply global irrelevance or zero multi-query value",
        "exact_sampling": {
            "first_events_per_method": EXACT_EVENT_LIMIT,
            "max_unknown_atoms": MAX_EXACT_UNKNOWN,
            "selection": "source record order, without outcome filtering",
        },
        "source_sha256": {
            str(path): _digest(path)
            for path in (episodes_path, decisions_path, status_path)
        },
        "events_sha256": _digest(events_path),
        "source_decision_records": record_count,
        "methods": counters,
        "by_regime": strata,
    }
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
