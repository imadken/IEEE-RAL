"""Parent-supported strict rules and counterexample-guided insufficiency interface."""

from fractions import Fraction
from itertools import combinations
from typing import Literal

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence

from .baselines import OutcomeRules
from .risk import RiskRule
from .schemas import (
    ACTIONS,
    Action,
    Certificate,
    LiteralFact,
    Query,
    ReferenceTable,
    Scope,
)
from .solver import FiniteIndex


class RepairScope(Scope):
    features: tuple[str, ...] = Field(max_length=14)


class RepairTable(ReferenceTable):
    scope: RepairScope


class RepairQuery(Query):
    scope: RepairScope


class Obstruction(Evidence):
    kind: Literal[
        "REPERTOIRE_INADEQUATE", "OBSERVATIONAL_AMBIGUITY", "REFERENCE_INSUFFICIENT"
    ]
    ids: tuple[str, ...] = ()
    reason: str


class RepairOutput(Evidence):
    status: Literal["STRICT_FINITE_REFERENCE", "INSUFFICIENT", "REFERENCE_INSUFFICIENT"]
    action: Action | None
    evidence: tuple[LiteralFact, ...] = ()
    support: int
    independent_parents: int
    certificate: Certificate
    obstructions: tuple[Obstruction, ...] = ()
    deployable_action: None = None
    calibration: Literal["UNASSESSED"] = "UNASSESSED"

    @model_validator(mode="after")
    def consistency(self):
        strict = self.status == "STRICT_FINITE_REFERENCE"
        if strict != (self.action is not None):
            raise ValueError("Strict output must name an action")
        if (self.action, self.evidence, self.support) != (
            self.certificate.action,
            self.certificate.evidence,
            self.certificate.support,
        ):
            raise ValueError("Output must agree with its original certificate")
        if strict and (self.independent_parents < 2 or self.obstructions):
            raise ValueError(
                "Strict output needs two independent parents and no obstruction"
            )
        reference = any(o.kind == "REFERENCE_INSUFFICIENT" for o in self.obstructions)
        if not strict and (self.status == "REFERENCE_INSUFFICIENT") != reference:
            raise ValueError("Reference status must agree with obstructions")
        return self


class ParentIndex(FiniteIndex):
    def __init__(self, table, parent_groups, minimum_parents=2):
        if set(parent_groups) != {r.id for r in table.rows}:
            raise ValueError(
                "Every reference row needs one declared independent parent"
            )
        super().__init__(table, minimum_parents)
        self.parent_groups = dict(parent_groups)
        self._parent_count = {}

    def parents(self, mask):
        if mask not in self._parent_count:
            self._parent_count[mask] = len(
                {self.parent_groups[id] for id in self.ids(mask)}
            )
        return self._parent_count[mask]

    def valid(self, action, mask):
        return (
            self.parents(mask) >= self.minimum_support
            and mask & ~self.acceptable[action] == 0
        )

    def diagnose(self, query):
        cert = self.solve(query)
        mask = (
            self.match(query, self.known(query))
            if query.scope == self.table.scope
            else 0
        )
        selected_ids = set(self.ids(mask))
        selected = [r for r in self.rows if r.id in selected_ids]
        obstructions = []
        if cert.action is None:
            inadequate = next(
                (
                    r
                    for r in selected
                    if r.qualified
                    and r.outcomes.continue_value is False
                    and r.outcomes.recover_value is False
                ),
                None,
            )
            if inadequate:
                obstructions.append(
                    Obstruction(
                        kind="REPERTOIRE_INADEQUATE",
                        ids=(inadequate.id,),
                        reason="Both measured fixed interventions fail in a compatible row",
                    )
                )
            left = next(
                (
                    r
                    for r in selected
                    if r.qualified and r.outcomes.acceptable() == ("continue",)
                ),
                None,
            )
            right = next(
                (
                    r
                    for r in selected
                    if r.qualified and r.outcomes.acceptable() == ("recover",)
                ),
                None,
            )
            if left and right:
                obstructions.append(
                    Obstruction(
                        kind="OBSERVATIONAL_AMBIGUITY",
                        ids=(left.id, right.id),
                        reason="Compatible rows require disjoint adequate actions",
                    )
                )
            missing = [
                r.id
                for r in selected
                if not r.qualified
                or None in (r.outcomes.continue_value, r.outcomes.recover_value)
            ]
            if (
                query.scope != self.table.scope
                or self.parents(mask) < self.minimum_support
                or missing
            ):
                obstructions.append(
                    Obstruction(
                        kind="REFERENCE_INSUFFICIENT",
                        ids=tuple(missing[:1]),
                        reason="Wrong scope, incomplete outcomes or fewer than two independent compatible parents; no supported broader pure rule exists",
                    )
                )
        status = (
            "STRICT_FINITE_REFERENCE"
            if cert.action
            else "REFERENCE_INSUFFICIENT"
            if any(o.kind == "REFERENCE_INSUFFICIENT" for o in obstructions)
            else "INSUFFICIENT"
        )
        matched = (
            mask
            if cert.action is None
            else self.match(
                query,
                [self.table.scope.features.index(f.feature) for f in cert.evidence],
            )
        )
        return RepairOutput(
            status=status,
            action=cert.action,
            evidence=cert.evidence,
            support=cert.support,
            independent_parents=self.parents(matched),
            certificate=cert,
            obstructions=tuple(obstructions),
        )


class ParentRules(OutcomeRules):
    def __init__(self, table, parent_groups, minimum_parents=2):
        super().__init__(table, minimum_parents)
        if set(parent_groups) != {r.id for r in table.rows}:
            raise ValueError("Missing independent parent assignment")
        self.parent_groups = dict(parent_groups)

    def parent_count(self, matched):
        return len({self.parent_groups[r.id] for r in matched})

    def select(self, query, beta=0.1, maximum_length=None):
        if not 0 <= beta <= 1:
            raise ValueError("Empirical target must lie in [0,1]")
        if query.scope != self.table.scope:
            return RiskRule(
                action=None, beta=beta, status="INSUFFICIENT", reason="SCOPE_MISMATCH"
            )
        known = self.known(query)
        maximum = (
            len(known) if maximum_length is None else min(maximum_length, len(known))
        )
        for count in range(maximum + 1):
            candidates = []
            for subset in combinations(known, count):
                matched = self.match(query, subset)
                if self.parent_count(matched) < self.minimum_support or any(
                    not r.qualified
                    or None in (r.outcomes.continue_value, r.outcomes.recover_value)
                    for r in matched
                ):
                    continue
                for order, action in enumerate(ACTIONS):
                    errors = sum(action not in r.outcomes.acceptable() for r in matched)
                    risk = Fraction(errors, len(matched))
                    if risk <= Fraction(str(beta)):
                        candidates.append(
                            (
                                (
                                    risk,
                                    -len(matched),
                                    order,
                                    tuple(self.table.scope.features[i] for i in subset),
                                ),
                                action,
                                subset,
                                matched,
                                errors,
                            )
                        )
            if candidates:
                _, action, subset, matched, errors = min(candidates, key=lambda p: p[0])
                return RiskRule(
                    action=action,
                    evidence=self.facts(query, subset),
                    support=len(matched),
                    matched_ids=tuple(sorted(r.id for r in matched)),
                    unacceptable=errors,
                    beta=beta,
                    status="PROVISIONAL_UNCALIBRATED",
                    reason="PARENT_SUPPORTED_EMPIRICAL_RULE",
                )
        return RiskRule(
            action=None,
            beta=beta,
            status="INSUFFICIENT",
            reason="NO_PARENT_SUPPORTED_RULE",
        )
