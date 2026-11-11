"""Exact finite conformant checks for deterministic propositional continuations.

This module supplies established reasoning semantics, not a new logical result.
CNF constraints restrict possible *decision states*. They are not implicitly
inserted as post-action invariants. Action abstractions must declare any such
obligations separately. Omitted evidence is unknown rather than false.
"""

from collections.abc import Mapping
from itertools import product
from typing import Literal as StatusLiteral

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Lit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    atom: str = Field(min_length=1)
    positive: bool = True

    def negate(self) -> "Lit":
        return Lit(atom=self.atom, positive=not self.positive)


class Action(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    pre: tuple[Lit, ...] = ()
    add: frozenset[str] = frozenset()
    delete: frozenset[str] = frozenset()

    @model_validator(mode="after")
    def validate_action(self) -> "Action":
        if self.add & self.delete:
            raise ValueError("An action cannot add and delete the same atom")
        if any(literal.negate() in self.pre for literal in self.pre):
            raise ValueError("Action preconditions contradict each other")
        if any(not atom for atom in self.add | self.delete):
            raise ValueError("Empty action atom")
        return self


class Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    atoms: frozenset[str]
    constraints: tuple[tuple[Lit, ...], ...] = ()

    @model_validator(mode="after")
    def validate_model(self) -> "Model":
        if any(not atom for atom in self.atoms):
            raise ValueError("Empty model atom")
        if any(
            literal.atom not in self.atoms
            for clause in self.constraints
            for literal in clause
        ):
            raise ValueError("Constraint refers to an undeclared atom")
        return self


Evidence = Mapping[str, bool | None]
Certification = StatusLiteral["VALID", "INVALID", "UNRESOLVED", "INCONSISTENT"]
SignedAtom = tuple[str, bool]
Clause = frozenset[SignedAtom]
CNF = tuple[Clause, ...]


def _check_evidence(model: Model, evidence: Evidence) -> dict[str, bool]:
    if set(evidence) - model.atoms:
        raise ValueError("Evidence refers to an undeclared atom")
    if any(
        value is not None and type(value) is not bool for value in evidence.values()
    ):
        raise ValueError("Evidence must contain only bool or None")
    return {atom: value for atom, value in evidence.items() if value is not None}


def _check_literals(model: Model, literals: tuple[Lit, ...]) -> None:
    if any(literal.atom not in model.atoms for literal in literals):
        raise ValueError("Query refers to an undeclared atom")


def _base_cnf(model: Model, evidence: Evidence) -> CNF:
    known = _check_evidence(model, evidence)
    clauses = [
        frozenset((literal.atom, literal.positive) for literal in clause)
        for clause in model.constraints
    ]
    clauses.extend(frozenset(((atom, value),)) for atom, value in known.items())
    # Tautologies do not constrain a completion. Empty clauses remain false.
    return tuple(
        clause
        for clause in clauses
        if not any((atom, not value) in clause for atom, value in clause)
    )


def _units(literals: tuple[Lit, ...]) -> CNF:
    return tuple(frozenset(((literal.atom, literal.positive),)) for literal in literals)


def _satisfiable(clauses: CNF) -> bool:
    """Complete DPLL with unit propagation; no external solver or sampling."""
    while True:
        if not clauses:
            return True
        if any(not clause for clause in clauses):
            return False
        units = {next(iter(clause)) for clause in clauses if len(clause) == 1}
        if not units:
            break
        if any((atom, not value) in units for atom, value in units):
            return False
        clauses = tuple(
            frozenset(
                (atom, value)
                for atom, value in clause
                if (atom, not value) not in units
            )
            for clause in clauses
            if not (clause & units)
        )
    shortest = min(clauses, key=lambda clause: (len(clause), tuple(sorted(clause))))
    atom, value = min(shortest)
    return _satisfiable(clauses + (frozenset(((atom, value),)),)) or _satisfiable(
        clauses + (frozenset(((atom, not value),)),)
    )


def possible(model: Model, evidence: Evidence, extra: tuple[Lit, ...] = ()) -> bool:
    """Whether some model completion satisfies evidence and extra literals."""
    _check_literals(model, extra)
    return _satisfiable(_base_cnf(model, evidence) + _units(extra))


def apply_action(action: Action, state: frozenset[str]) -> frozenset[str]:
    """Apply a deterministic STRIPS action, rejecting false preconditions."""
    if any((literal.atom in state) != literal.positive for literal in action.pre):
        raise ValueError(f"Action precondition is false: {action.name}")
    return (state - action.delete) | action.add


def regress(plan: tuple[Action, ...], goal: tuple[Lit, ...]) -> tuple[Lit, ...] | None:
    """Exact conjunctive weakest precondition, or None for an impossible plan."""
    required = set(goal)
    if any(literal.negate() in required for literal in required):
        return None
    for action in reversed(plan):
        effects = {Lit(atom=atom) for atom in action.add} | {
            Lit(atom=atom, positive=False) for atom in action.delete
        }
        if any(literal.negate() in effects for literal in required):
            return None
        required = (required - effects) | set(action.pre)
        if any(literal.negate() in required for literal in required):
            return None
    return tuple(sorted(required, key=lambda literal: (literal.atom, literal.positive)))


def _check_plan(model: Model, plan: tuple[Action, ...], goal: tuple[Lit, ...]) -> None:
    _check_literals(model, goal)
    for action in plan:
        _check_literals(model, action.pre)
        if (action.add | action.delete) - model.atoms:
            raise ValueError("Action effect refers to an undeclared atom")


def certify(
    model: Model,
    evidence: Evidence,
    plan: tuple[Action, ...],
    goal: tuple[Lit, ...],
) -> Certification:
    """Classify validity over every evidence-consistent initial completion.

    INVALID means every completion fails the sequence or goal, UNRESOLVED means
    both outcomes remain possible, and INCONSISTENT means no completion exists.
    Empty completion sets never produce a vacuous execution permission.
    """
    _check_plan(model, plan, goal)
    base = _base_cnf(model, evidence)
    if not _satisfiable(base):
        return "INCONSISTENT"
    required = regress(plan, goal)
    if required is None or not _satisfiable(base + _units(required)):
        return "INVALID"
    if any(_satisfiable(base + _units((literal.negate(),))) for literal in required):
        return "UNRESOLVED"
    return "VALID"


def consistent_completions(
    model: Model, evidence: Evidence, max_unknown: int = 18
) -> tuple[frozenset[str], ...]:
    """Independent bounded exhaustive reference; never truncate the state set."""
    known = _check_evidence(model, evidence)
    unknown = sorted(model.atoms - known.keys())
    if type(max_unknown) is not int or max_unknown < 0:
        raise ValueError("max_unknown must be a nonnegative integer")
    if len(unknown) > max_unknown:
        raise ValueError("Exhaustive completion limit exceeded")
    true_known = {atom for atom, value in known.items() if value}
    worlds = []
    for values in product((False, True), repeat=len(unknown)):
        state = frozenset(
            true_known | {atom for atom, value in zip(unknown, values) if value}
        )
        if all(
            any((literal.atom in state) == literal.positive for literal in clause)
            for clause in model.constraints
        ):
            worlds.append(state)
    return tuple(worlds)


def relevant_atoms(
    model: Model,
    evidence: Evidence,
    plan: tuple[Action, ...],
    goal: tuple[Lit, ...],
) -> frozenset[str]:
    """Conservative unknown-variable closure, not exact minimal query relevance.

    Start at the full continuation's regressed obligations and close over every
    CNF dependency. Thus a correlated atom outside a plan's names is retained.
    The closure may include observations that cannot change today's decision;
    it must not be described as a proof that each returned query has value.
    """
    _check_plan(model, plan, goal)
    known = _check_evidence(model, evidence)
    required = regress(plan, goal)
    if required is None:
        return frozenset()
    reached = {literal.atom for literal in required}
    changed = True
    while changed:
        changed = False
        for clause in model.constraints:
            atoms = {literal.atom for literal in clause}
            if reached & atoms and not atoms <= reached:
                reached.update(atoms)
                changed = True
    return frozenset(reached - known.keys())
