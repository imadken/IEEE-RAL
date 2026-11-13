"""Typed separation of runtime observations, offline outcomes and certificates."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, StrictBool, model_validator

from dual_rec.contracts.checks import Evidence

Action = Literal["continue", "recover"]
Value = StrictBool | None
Reason = Literal[
    "SCOPE_MISMATCH",
    "OUTCOME_UNCERTAINTY",
    "INSUFFICIENT_REFERENCE_SUPPORT",
    "OBSERVATION_AMBIGUITY",
    "INADEQUATE_REPERTOIRE",
    "MISSING_OBSERVATIONS",
    "CALIBRATION_INSUFFICIENT",
]
ACTIONS: tuple[Action, ...] = ("continue", "recover")


class Scope(Evidence):
    task: str
    controller_sha256: str
    horizon_steps: int = Field(default=70, gt=0)
    horizon_seconds: float = Field(default=3.5, gt=0)
    utility: Literal["terminal_task_success"] = "terminal_task_success"
    epsilon: float = Field(default=0, ge=0, lt=1)
    adequacy: Literal[1] = 1
    actions: tuple[Action, ...] = ACTIONS
    features: tuple[str, ...] = Field(max_length=8)
    channels: str

    @model_validator(mode="after")
    def unique(self):
        if self.actions != ACTIONS:
            raise ValueError("The fixed action repertoire/order is continue, recover")
        if len(set(self.features)) != len(self.features):
            raise ValueError("Duplicate feature names")
        return self


class LiteralFact(Evidence):
    feature: str
    value: StrictBool


class Outcomes(Evidence):
    continue_value: Value
    recover_value: Value

    def acceptable(self) -> tuple[Action, ...]:
        if self.continue_value is None or self.recover_value is None:
            return ()
        # Binary utility, adequacy=1 and epsilon<1: success implies zero regret.
        return tuple(
            a
            for a, v in zip(
                ACTIONS, (self.continue_value, self.recover_value), strict=True
            )
            if v
        )


class ReferenceRow(Evidence):
    id: str
    features: tuple[Value, ...]
    outcomes: Outcomes
    qualified: bool = True


class ReferenceTable(Evidence):
    scope: Scope
    rows: tuple[ReferenceRow, ...]

    @model_validator(mode="after")
    def dimensions(self):
        if len({r.id for r in self.rows}) != len(self.rows):
            raise ValueError("Duplicate reference checkpoint IDs")
        if any(len(r.features) != len(self.scope.features) for r in self.rows):
            raise ValueError("Reference feature dimensions differ from scope")
        return self


class Query(Evidence):
    scope: Scope
    features: tuple[Value, ...]

    @model_validator(mode="after")
    def dimensions(self):
        if len(self.features) != len(self.scope.features):
            raise ValueError("Query feature dimensions differ from scope")
        return self


class WitnessState(Evidence):
    id: str
    features: tuple[Value, ...]
    outcomes: Outcomes
    acceptable: tuple[Action, ...]


class Witness(Evidence):
    kind: Literal[
        "LITERAL_NECESSITY",
        "INCOMPATIBLE_ACTIONS",
        "INADEQUATE_ACTIONS",
        "UNKNOWN_OUTCOMES",
        "SUPPORT",
        "UNEXCLUDABLE_BAD_ROW",
    ]
    action: Action | None = None
    removed: LiteralFact | None = None
    states: tuple[WitnessState, ...] = ()
    reason: str


class Certificate(Evidence):
    status: Literal["SUFFICIENT", "INSUFFICIENT"]
    action: Action | None
    evidence: tuple[LiteralFact, ...] = ()
    support: int = Field(ge=0)
    matched_ids: tuple[str, ...] = ()
    scope: Scope
    reasons: tuple[Reason, ...] = ()
    witnesses: tuple[Witness, ...] = ()
    exactness: Literal["MINIMUM_CARDINALITY", "SUBSET_MINIMAL", "NONE"]
    calibration: Literal["UNASSESSED"] = "UNASSESSED"
    subsets_evaluated: int = 0

    @model_validator(mode="after")
    def consistency(self):
        if (self.status == "SUFFICIENT") != (self.action is not None):
            raise ValueError("A sufficient table certificate must name its action")
        if self.support != len(self.matched_ids):
            raise ValueError("Support must equal the matched ID count")
        return self


class Recommendation(Evidence):
    method: str
    action: Action | None
    evidence: tuple[LiteralFact, ...] = ()
    support: int = 0
    reason: str
    mean_utility: float | None = None
    treatment_effect: float | None = None
    category_probabilities: tuple[float, float, float, float] | None = None
