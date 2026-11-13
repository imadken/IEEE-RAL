"""Strict-first routing with explicitly uncalibrated same-grammar risk rules."""

from fractions import Fraction
from itertools import combinations
from typing import Literal

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence

from .baselines import OutcomeRules, category
from .schemas import ACTIONS, Action, Certificate, LiteralFact, Query
from .solver import FiniteIndex


class RiskRule(Evidence):
    action: Action | None
    evidence: tuple[LiteralFact, ...] = ()
    matched_ids: tuple[str, ...] = ()
    support: int = Field(default=0, ge=0)
    unacceptable: int | None = Field(default=None, ge=0)
    beta: float = Field(ge=0, le=1)
    status: Literal["PROVISIONAL_UNCALIBRATED", "INSUFFICIENT"]
    reason: str

    @model_validator(mode="after")
    def consistency(self):
        if self.support != len(self.matched_ids):
            raise ValueError("Support must equal reference ID count")
        if (self.action is not None) != (self.status == "PROVISIONAL_UNCALIBRATED"):
            raise ValueError("Provisional rule must name its action")
        if self.action is not None and (
            not self.support
            or self.unacceptable is None
            or Fraction(self.unacceptable, self.support) > Fraction(str(self.beta))
        ):
            raise ValueError("Rule does not meet its declared empirical target")
        return self


class RoutedDecision(Evidence):
    tier: Literal["STRICT_FINITE_REFERENCE", "PROVISIONAL_RISK_RULE", "INSUFFICIENT"]
    status: Literal[
        "STRICT_FINITE_REFERENCE", "PROVISIONAL_UNCALIBRATED", "INSUFFICIENT"
    ]
    action: Action | None
    evidence: tuple[LiteralFact, ...] = ()
    support: int = Field(ge=0)
    strict: Certificate
    provisional: RiskRule | None = None
    calibration: Literal["UNASSESSED"] = "UNASSESSED"
    deployable_action: None = None

    @model_validator(mode="after")
    def consistency(self):
        if self.tier == "STRICT_FINITE_REFERENCE":
            if self.strict.action is None or self.provisional is not None:
                raise ValueError("Strict route requires its original certificate")
            origin = self.strict
            expected_status = "STRICT_FINITE_REFERENCE"
        elif self.tier == "PROVISIONAL_RISK_RULE":
            if self.strict.action is not None or self.provisional is None:
                raise ValueError("Risk tier is available only after strict abstention")
            origin = self.provisional
            if origin.action is None:
                raise ValueError("Risk route requires a provisional action")
            expected_status = "PROVISIONAL_UNCALIBRATED"
        else:
            origin = self.strict
            if self.action is not None or origin.action is not None:
                raise ValueError("Insufficient route must abstain")
            if self.provisional is not None and self.provisional.action is not None:
                raise ValueError("Cannot discard an eligible provisional rule")
            expected_status = "INSUFFICIENT"
        if self.status != expected_status or (
            self.action,
            self.evidence,
            self.support,
        ) != (origin.action, origin.evidence, origin.support):
            raise ValueError("Route does not agree with its source/status")
        return self


class RiskRules(OutcomeRules):
    """B5 grammar with v1.1 empirical-error-first canonical ties.

    Missing outcomes are not imputed as errors: such a candidate is unavailable.
    """

    def select(self, query: Query, beta=0.10, maximum_length=None):
        threshold = Fraction(str(beta))
        if not 0 <= threshold <= 1:
            raise ValueError("Empirical target must lie in [0,1]")
        if maximum_length is not None and maximum_length < 0:
            raise ValueError("Maximum evidence length must be nonnegative")

        def abstain(reason):
            return RiskRule(
                action=None, beta=beta, status="INSUFFICIENT", reason=reason
            )

        if query.scope != self.table.scope:
            return abstain("SCOPE_MISMATCH")
        known = self.known(query)
        maximum = (
            len(known) if maximum_length is None else min(maximum_length, len(known))
        )
        for length in range(maximum + 1):
            choices = []
            for indices in combinations(known, length):
                matched = self.match(query, indices)
                if len(matched) < self.minimum_support or any(
                    category(r) is None for r in matched
                ):
                    continue
                for order, action in enumerate(ACTIONS):
                    errors = sum(action not in r.outcomes.acceptable() for r in matched)
                    risk = Fraction(errors, len(matched))
                    if risk <= threshold:
                        choices.append(
                            (
                                (
                                    risk,
                                    -len(matched),
                                    order,
                                    tuple(
                                        self.table.scope.features[i] for i in indices
                                    ),
                                ),
                                action,
                                indices,
                                matched,
                                errors,
                            )
                        )
            if choices:
                _, action, indices, matched, errors = min(choices, key=lambda c: c[0])
                return RiskRule(
                    action=action,
                    evidence=self.facts(query, indices),
                    matched_ids=tuple(sorted(r.id for r in matched)),
                    support=len(matched),
                    unacceptable=errors,
                    beta=beta,
                    status="PROVISIONAL_UNCALIBRATED",
                    reason="EMPIRICAL_OUTCOME_RULE_NOT_A_UNIVERSAL_CERTIFICATE",
                )
        return abstain("NO_COMPLETE_SUPPORTED_RULE_WITHIN_EMPIRICAL_TARGET")


class TwoTierRouter:
    def __init__(self, table, minimum_support=2, beta=0.10):
        if not 0 <= beta <= 1:
            raise ValueError("Empirical target must lie in [0,1]")
        self.strict = FiniteIndex(table, minimum_support)
        self.risk = RiskRules(table, minimum_support)
        self.beta = beta

    def predict(self, query: Query):
        strict = self.strict.solve(query)
        if strict.action is not None:
            return RoutedDecision(
                tier="STRICT_FINITE_REFERENCE",
                status="STRICT_FINITE_REFERENCE",
                action=strict.action,
                evidence=strict.evidence,
                support=strict.support,
                strict=strict,
            )
        risk = self.risk.select(query, self.beta)
        if risk.action is not None:
            return RoutedDecision(
                tier="PROVISIONAL_RISK_RULE",
                status="PROVISIONAL_UNCALIBRATED",
                action=risk.action,
                evidence=risk.evidence,
                support=risk.support,
                strict=strict,
                provisional=risk,
            )
        return RoutedDecision(
            tier="INSUFFICIENT",
            status="INSUFFICIENT",
            action=None,
            support=strict.support,
            strict=strict,
            provisional=risk,
        )
