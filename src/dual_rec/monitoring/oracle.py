"""Bounded exact observation-tree reference for static, truthful symbolic queries.

The objective is resolved VALID/INVALID classification under a uniform prior on
allowed completions. This is standard finite decision-tree evaluation, not a
new theorem or an upper bound on task completion, recovery quality, or latency.
Actual environment states and noisy sensor answers are absent from this API.
"""

from fractions import Fraction
from functools import cache

from pydantic import Field

from .contracts import Context, StrictModel
from .semantics import apply_action, consistent_completions

MAX_UNKNOWN = 12
MAX_QUERIES = 6
MAX_BUDGET = 3


class OracleLimit(ValueError):
    """The requested instance exceeds the preregistered exact-reference bounds."""


class ExactEvaluation(StrictModel):
    first_query: str | None
    resolved_probability: float = Field(ge=0, le=1)
    expected_calls: float = Field(ge=0)
    world_count: int = Field(ge=1)
    search_states: int = Field(ge=1)


def evaluate_exact(
    context: Context, evidence: dict[str, bool | None], budget: int
) -> ExactEvaluation:
    """Enumerate adaptive query trees of total declared cost at most budget.

    Maximize classification probability, then minimize expected query calls and
    break remaining ties lexicographically. Probability arithmetic is exact.
    Queries reveal all their atoms truthfully without changing the state; each
    branch is weighted by its number of initially equiprobable completions.
    Inconsistent evidence is rejected rather than certified vacuously.
    """
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if budget > MAX_BUDGET:
        raise OracleLimit(f"Exact budget limit is {MAX_BUDGET}")
    if len(context.queries) > MAX_QUERIES:
        raise OracleLimit(f"Exact query-menu limit is {MAX_QUERIES}")
    if len({query.name for query in context.queries}) != len(context.queries):
        raise ValueError("Query names must be unique")
    if any(query.atoms - context.model.atoms for query in context.queries):
        raise ValueError("Query refers to an undeclared atom")
    plan_atoms = {literal.atom for literal in context.goal}
    for action in context.plan:
        plan_atoms.update(literal.atom for literal in action.pre)
        plan_atoms.update(action.add | action.delete)
    if plan_atoms - context.model.atoms:
        raise ValueError("Continuation refers to an undeclared atom")
    try:
        worlds = consistent_completions(context.model, evidence, MAX_UNKNOWN)
    except ValueError as error:
        if "limit exceeded" in str(error):
            raise OracleLimit(f"Exact unknown-atom limit is {MAX_UNKNOWN}") from error
        raise
    if not worlds:
        raise ValueError("No consistent completion; evidence cannot be certified")

    # Forward execution makes reference labels independent of weakest-precondition
    # regression and the deployed certifier's SAT implementation.
    labels = []
    for world in worlds:
        state = world
        try:
            for action in context.plan:
                state = apply_action(action, state)
        except ValueError:
            labels.append(False)
            continue
        labels.append(
            all((literal.atom in state) == literal.positive for literal in context.goal)
        )

    queries = tuple(sorted(context.queries, key=lambda query: query.name))
    query_atoms = tuple(tuple(sorted(query.atoms)) for query in queries)

    @cache
    def partition(
        indices: tuple[int, ...], query_index: int
    ) -> tuple[tuple[int, ...], ...]:
        groups: dict[tuple[bool, ...], list[int]] = {}
        for index in indices:
            answer = tuple(atom in worlds[index] for atom in query_atoms[query_index])
            groups.setdefault(answer, []).append(index)
        return tuple(tuple(group) for group in groups.values())

    @cache
    def solve(
        indices: tuple[int, ...], remaining: int
    ) -> tuple[Fraction, Fraction, str | None]:
        if all(labels[index] == labels[indices[0]] for index in indices):
            return Fraction(1), Fraction(0), None
        best_score, best_calls, best_query = Fraction(0), Fraction(0), None
        for query_index, query in enumerate(queries):
            if query.cost > remaining:
                continue
            groups = partition(indices, query_index)
            if len(groups) == 1:
                continue
            score, calls = Fraction(0), Fraction(1)
            for group in groups:
                child_score, child_calls, _ = solve(group, remaining - query.cost)
                probability = Fraction(len(group), len(indices))
                score += probability * child_score
                calls += probability * child_calls
            if score > best_score or (score == best_score and calls < best_calls):
                best_score, best_calls, best_query = score, calls, query.name
            # Queries are sorted, so equal score/call ties already keep the
            # lexicographically first query. Abstention wins a zero-gain tie.
        return best_score, best_calls, best_query

    score, calls, first_query = solve(tuple(range(len(worlds))), budget)
    return ExactEvaluation(
        first_query=first_query,
        resolved_probability=float(score),
        expected_calls=float(calls),
        world_count=len(worlds),
        search_states=solve.cache_info().currsize,
    )


def select_exact(
    context: Context, evidence: dict[str, bool | None], budget: int
) -> str | None:
    """Return the exact first query, or None if resolved/no useful tree exists."""
    return evaluate_exact(context, evidence, budget).first_query
