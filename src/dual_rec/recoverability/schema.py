"""Validated finite transition models, bounded policies and obstruction proofs."""

from __future__ import annotations

from fractions import Fraction
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    model_validator,
)
from pydantic_core import PydanticCustomError


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


def rational(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise PydanticCustomError(
            "exact_cost", "Exact nonnegative costs require integer/rational input"
        )
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("Malformed rational cost") from error


Exact = Annotated[Fraction, BeforeValidator(rational)]
Name = Annotated[str, Field(strict=True, min_length=1, pattern=r".*\S.*")]


class RecoveryOutcome(Frozen):
    action_id: Name
    task_success: StrictBool
    path_safe: StrictBool


class State(Frozen):
    state_id: Name
    physically_allowed: StrictBool
    recoveries: tuple[RecoveryOutcome, ...]


class ProbeTransition(Frozen):
    state_id: Name
    enabled: StrictBool
    successor: Name | None = None
    observation: Name | None = None
    path_safe: StrictBool | None = None

    @model_validator(mode="after")
    def explicit_transition(self):
        fields = (self.successor, self.observation, self.path_safe)
        if self.enabled and any(x is None for x in fields):
            raise ValueError(
                "Enabled probes need explicit successor/observation/path safety"
            )
        if not self.enabled and any(x is not None for x in fields):
            raise ValueError("Disabled probes have no implicit successor or reset")
        return self


class Probe(Frozen):
    probe_id: Name
    cost: Exact = Field(ge=0)
    transitions: tuple[ProbeTransition, ...] = Field(min_length=1)


class FiniteProbeProblem(Frozen):
    model_id: Name
    source_scope: Literal["DECLARED_DETERMINISTIC_FINITE_MODEL"]
    evidence_origin: Literal["ANALYTICAL_TRUTH_TABLE_NOT_ROBOT_OUTCOMES"]
    calibration_available: Literal[False]
    assumptions: tuple[Name, ...] = Field(min_length=1)
    states: tuple[State, ...] = Field(min_length=1, max_length=32)
    recovery_actions: tuple[Name, ...] = Field(min_length=1, max_length=8)
    probes: tuple[Probe, ...] = Field(max_length=8)
    initial_support: tuple[Name, ...] = Field(min_length=1)
    horizon: int = Field(strict=True, ge=0, le=4)
    max_probe_cost: Exact | None = Field(default=None, ge=0)
    cost_unit: Name
    require_physical_safety: StrictBool = True

    @model_validator(mode="after")
    def complete_markov_model(self):
        ids = {s.state_id for s in self.states}
        actions = set(self.recovery_actions)
        if len(ids) != len(self.states) or len(actions) != len(self.recovery_actions):
            raise ValueError("Duplicate state or recovery action")
        if (
            len(set(self.initial_support)) != len(self.initial_support)
            or not set(self.initial_support) <= ids
        ):
            raise ValueError(
                "Initial support is duplicated or references an unknown state"
            )
        if len({p.probe_id for p in self.probes}) != len(self.probes):
            raise ValueError("Duplicate probe")
        for state in self.states:
            if (
                len(state.recoveries) != len(actions)
                or {r.action_id for r in state.recoveries} != actions
            ):
                raise ValueError("Every state needs the complete recovery truth table")
        for probe in self.probes:
            if (
                len(probe.transitions) != len(ids)
                or {t.state_id for t in probe.transitions} != ids
            ):
                raise ValueError(
                    "Every probe needs a row for every state; no implicit resets"
                )
            observations = {}
            for t in probe.transitions:
                if t.enabled:
                    if t.successor not in ids:
                        raise ValueError("Unknown successor")
                    if (
                        t.successor in observations
                        and observations[t.successor] != t.observation
                    ):
                        raise ValueError(
                            "Observation must depend on the successor state and probe; retain hidden parameters in the state"
                        )
                    observations[t.successor] = t.observation
        return self


class PolicyBranch(Frozen):
    observation: str
    child: PolicyNode


class PolicyNode(Frozen):
    belief: tuple[str, ...]
    decision: Literal["RECOVER", "PROBE", "STOP"]
    action_id: str | None = None
    branches: tuple[PolicyBranch, ...] = ()

    @model_validator(mode="after")
    def decision_shape(self):
        if self.decision == "STOP" and (self.action_id is not None or self.branches):
            raise ValueError("STOP terminates without action or reset")
        if self.decision != "STOP" and self.action_id is None:
            raise ValueError("Action identifier required")
        if (self.decision == "PROBE") != bool(self.branches):
            raise ValueError("Only probes have nonempty observation branches")
        return self


class RecoveryCounterexample(Frozen):
    action_id: str
    state_id: str
    reason: Literal["TASK_FAILURE", "PHYSICAL_PATH_UNSAFE"]


class ProbeObstruction(Frozen):
    probe_id: str
    reason: Literal["DISABLED", "PHYSICAL_PATH_UNSAFE", "COST_BUDGET", "LOSING_BRANCH"]
    state_id: str | None = None
    observation: str | None = None
    child: Obstruction | None = None


class Obstruction(Frozen):
    belief: tuple[str, ...]
    remaining_horizon: int
    remaining_cost: Exact | None
    reason: Literal[
        "INITIAL_STATE_UNSAFE", "NO_COMMON_RECOVERY_AT_HORIZON", "ALL_PROBES_BLOCKED"
    ]
    unsafe_states: tuple[str, ...] = ()
    recoveries: tuple[RecoveryCounterexample, ...] = ()
    probes: tuple[ProbeObstruction, ...] = ()


class ProbePlan(Frozen):
    status: Literal["ROBUST_FINITE_MODEL_RECOVERY", "STOP_NO_ROBUST_POLICY"]
    policy: PolicyNode
    worst_probe_cost: Exact | None
    obstruction: Obstruction | None = None
    dynamic_programming_states: int
    scope: Literal["THIS_KNOWN_FINITE_MODEL_HORIZON_AND_BUDGET_ONLY"] = (
        "THIS_KNOWN_FINITE_MODEL_HORIZON_AND_BUDGET_ONLY"
    )
    statistical_calibration: Literal[False] = False
    physical_deployment_authorized: Literal[False] = False
    implicit_resets: Literal[False] = False


PolicyBranch.model_rebuild()
PolicyNode.model_rebuild()
ProbeObstruction.model_rebuild()
Obstruction.model_rebuild()
