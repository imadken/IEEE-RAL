"""Case B: exact expected classification of frozen schedulers on their M4 prior.

This is classical finite Boolean-function evaluation, not a new uncertainty
regime, theorem, task corpus, or task-success ceiling. Qualification is untouched.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from fractions import Fraction
from functools import cache
from pathlib import Path

from .contracts import Context
from .methods import run_method
from .oracle import MAX_QUERIES, MAX_UNKNOWN, evaluate_exact
from .semantics import apply_action, consistent_completions

METHODS = ("M1", "M3", "M4")


class QueryRequested(Exception):
    """Interrupt immediately before sensing; preserve the deployed query choice."""

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


def _query_choice(
    context: Context, evidence: dict[str, bool | None], method: str
) -> str | None:
    def interrupt(name: str) -> dict[str, bool]:
        raise QueryRequested(name)

    try:
        decision = run_method(
            context.model_copy(update={"evidence": evidence}), method, 1, interrupt
        )
    except QueryRequested as requested:
        return requested.name
    if decision.status not in {"VALID", "INVALID", "UNRESOLVED"}:
        raise ValueError("The selected context has inconsistent evidence")
    return None


def _label(context: Context, world: frozenset[str]) -> bool:
    state = world
    try:
        for action in context.plan:
            state = apply_action(action, state)
    except ValueError:
        return False
    return all((literal.atom in state) == literal.positive for literal in context.goal)


def _fraction(value: Fraction) -> dict:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "value": float(value),
    }


def expected_frozen(
    context: Context, method: str
) -> dict[int, tuple[Fraction, Fraction]]:
    """Evaluate exactly the frozen M1/M3 choices, retaining observed evidence.

    Evidence keys are part of the memoized state: two histories can induce the
    same world subset while revealing different proxy atoms to a heuristic.
    Inferring extra keys from the subset would silently alter the scheduler.
    """
    if method not in {"M1", "M3"}:
        raise ValueError(
            "Only frozen heuristic schedulers M1 and M3 are evaluated here"
        )
    if any(query.cost != 1 for query in context.queries):
        raise ValueError("The existing campaign uses unit-cost query calls")
    worlds = consistent_completions(context.model, context.evidence, MAX_UNKNOWN)
    if not worlds:
        raise ValueError("No evidence-consistent worlds")
    labels = tuple(_label(context, world) for world in worlds)
    query_atoms = {query.name: tuple(sorted(query.atoms)) for query in context.queries}
    initial = tuple(
        sorted(
            (atom, value)
            for atom, value in context.evidence.items()
            if value is not None
        )
    )

    @cache
    def solve(
        indices: tuple[int, ...],
        evidence_items: tuple[tuple[str, bool], ...],
        remaining: int,
    ) -> tuple[Fraction, Fraction]:
        if all(labels[index] == labels[indices[0]] for index in indices):
            return Fraction(1), Fraction(0)
        if remaining == 0:
            return Fraction(0), Fraction(0)
        evidence = dict(evidence_items)
        name = _query_choice(context, evidence, method)
        if name is None:
            return Fraction(0), Fraction(0)
        atoms = query_atoms[name]
        if all(atom in evidence for atom in atoms):
            raise ValueError("Frozen scheduler repeated an entirely observed query")
        branches: dict[tuple[bool, ...], list[int]] = {}
        for index in indices:
            answer = tuple(atom in worlds[index] for atom in atoms)
            branches.setdefault(answer, []).append(index)
        score, calls = Fraction(0), Fraction(1)
        for answer, branch in branches.items():
            child_evidence = evidence | dict(zip(atoms, answer, strict=True))
            child_score, child_calls = solve(
                tuple(branch), tuple(sorted(child_evidence.items())), remaining - 1
            )
            probability = Fraction(len(branch), len(indices))
            score += probability * child_score
            calls += probability * child_calls
        return score, calls

    return {
        budget: solve(tuple(range(len(worlds))), initial, budget) for budget in range(4)
    }


def exhaustive_execution(
    context: Context,
) -> dict[str, dict[int, tuple[Fraction, Fraction]]]:
    """Independent policy-execution average over every allowed small-world state."""
    worlds = consistent_completions(context.model, context.evidence, 8)
    if not worlds:
        raise ValueError("No evidence-consistent worlds")
    results = {}
    for method in METHODS:
        by_budget = {}
        for budget in range(4):
            resolved = calls = 0
            for world in worlds:
                menu = {query.name: query.atoms for query in context.queries}

                def sense(name: str, world=world, menu=menu) -> dict[str, bool]:
                    return {atom: atom in world for atom in menu[name]}

                decision = run_method(context, method, budget, sense)
                resolved += decision.status in {"VALID", "INVALID"}
                calls += len(decision.query_names)
            by_budget[budget] = (
                Fraction(resolved, len(worlds)),
                Fraction(calls, len(worlds)),
            )
        results[method] = by_budget
    return results


def compare_context(context: Context, crosscheck: bool = False) -> dict:
    worlds = consistent_completions(context.model, context.evidence, MAX_UNKNOWN)
    if not worlds:
        raise ValueError("No evidence-consistent worlds")
    expected = {method: expected_frozen(context, method) for method in ("M1", "M3")}
    exact_records = {}
    for budget in range(4):
        exact = evaluate_exact(context, context.evidence, budget)
        # Uniform-world expectations are integer multiples of1/world_count.
        # Recover those rational numbers from the existing float-only API.
        score = Fraction(exact.resolved_probability).limit_denominator(len(worlds))
        calls = Fraction(exact.expected_calls).limit_denominator(len(worlds))
        exact_records[budget] = score, calls
    expected["M4"] = exact_records
    independently_checked = False
    if crosscheck:
        actual = exhaustive_execution(context)
        if actual != expected:
            raise AssertionError(
                f"Expected-tree versus full frozen-policy execution mismatch: {actual!r} != {expected!r}"
            )
        independently_checked = True
    records = []
    for budget in range(4):
        for method in METHODS:
            score, calls = expected[method][budget]
            oracle_score = expected["M4"][budget][0]
            if score > oracle_score:
                raise AssertionError(
                    "A frozen policy exceeds the exact classification optimum"
                )
            records.append(
                {
                    "budget": budget,
                    "method": method,
                    "expected_resolved_classification": _fraction(score),
                    "expected_queries": _fraction(calls),
                    "classification_gap_to_M4": _fraction(oracle_score - score),
                }
            )
    return {
        "world_count": len(worlds),
        "unknown_atoms": sum(
            context.evidence.get(atom) is None for atom in context.model.atoms
        ),
        "uniform_prior_valid_worlds": sum(_label(context, world) for world in worlds),
        "full_execution_crosscheck": independently_checked,
        "records": records,
    }


def run_comparison(episodes_path: Path, output: Path) -> dict:
    if "qualification" in episodes_path.parts:
        raise ValueError(
            "This diagnostic is restricted to existing development episodes"
        )
    if output.exists():
        raise FileExistsError(output)
    selected, skipped = [], Counter()
    crosschecks = 0
    with gzip.open(episodes_path, "rt") as stream:
        for source_index, line in enumerate(stream):
            raw = json.loads(line)
            if raw["regime"] in {"noise05", "invalidated"}:
                skipped["nontruthful_or_stale_disturbance_regime"] += 1
                continue
            context = Context.model_validate(raw["context"])
            unknown = sum(
                context.evidence.get(atom) is None for atom in context.model.atoms
            )
            if unknown > MAX_UNKNOWN or len(context.queries) > MAX_QUERIES:
                skipped["existing_M4_size_limit"] += 1
                continue
            if not consistent_completions(context.model, context.evidence, MAX_UNKNOWN):
                skipped["inconsistent_evidence_not_M4_eligible"] += 1
                continue
            crosscheck = crosschecks < 4 and unknown <= 8
            result = compare_context(context, crosscheck)
            crosschecks += crosscheck
            selected.append(
                {
                    "episode_id": raw["episode_id"],
                    "parent_id": raw["parent_id"],
                    "family": raw["family"],
                    "regime": raw["regime"],
                    "source_record_index": source_index,
                    "context_sha256": hashlib.sha256(
                        json.dumps(
                            raw["context"], sort_keys=True, separators=(",", ":")
                        ).encode()
                    ).hexdigest(),
                    **result,
                }
            )
            if len(selected) == 64:
                break
    gaps = Counter()
    for case in selected:
        for row in case["records"]:
            if row["classification_gap_to_M4"]["numerator"]:
                gaps[row["method"]] += 1
    comparisons = []
    for budget in range(4):
        values = []
        for case in selected:
            by_method = {
                row["method"]: row for row in case["records"] if row["budget"] == budget
            }
            values.append(
                by_method["M3"]["expected_resolved_classification"]["value"]
                - by_method["M1"]["expected_resolved_classification"]["value"]
            )
        comparisons.append(
            {
                "budget": budget,
                "M3_minus_M1_mean_expected_resolution": sum(values) / len(values)
                if values
                else None,
                "M3_better_contexts": sum(v > 0 for v in values),
                "M1_better_contexts": sum(v < 0 for v in values),
                "tied_contexts": sum(v == 0 for v in values),
            }
        )
    result = {
        "source_sha256": hashlib.sha256(episodes_path.read_bytes()).hexdigest(),
        "selection": "First64 existing-M4-eligible truthful development episodes in original record order; no outcome selection",
        "objective": "Expected resolved VALID/INVALID classification under existing M4 uniform-completion prior; not task-success ceiling",
        "selected_episodes": len(selected),
        "selected_parents": len({r["parent_id"] for r in selected}),
        "regime_counts": dict(Counter(r["regime"] for r in selected)),
        "skipped_while_selecting": dict(skipped),
        "independent_complete_execution_crosschecks": crosschecks,
        "context_budget_cases_with_strict_gap_to_M4": dict(gaps),
        "M3_M1_comparison_by_budget": comparisons,
        "records": selected,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_comparison(args.episodes, args.output)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "records"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
