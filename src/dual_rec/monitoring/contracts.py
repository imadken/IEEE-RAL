"""Strict public/runtime versus evaluation-only contracts for the study."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .semantics import Action, Lit, Model


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Query(StrictModel):
    name: str
    atoms: frozenset[str]
    cost: int = Field(default=1, ge=1)


class Context(StrictModel):
    """Everything a deployed scheduler may read; no actual state or outcome."""

    model: Model
    evidence: dict[str, bool | None]
    plan: tuple[Action, ...]
    goal: tuple[Lit, ...]
    queries: tuple[Query, ...]
    consequence: dict[str, float]
    schedule_offset: int = 0


class Episode(StrictModel):
    """Evaluator record. Only context is passed to method selection code."""

    episode_id: str
    parent_id: str
    family: str
    split: Literal["development", "qualification", "smoke"]
    checkpoint: int
    schedule: int
    regime: str
    context: Context
    oracle_state: frozenset[str]
    nominal_state: frozenset[str]
    sensor_answers: dict[str, bool]
    actions: tuple[Action, ...]
    source_hashes: dict[str, str]
    evidence_timing: dict
    disturbance_action: str | None = None


class Decision(StrictModel):
    method: str
    choice: Literal["CONTINUE", "RECOVER", "ABSTAIN"]
    evidence: dict[str, bool | None]
    status: str
    query_names: tuple[str, ...]
    query_atoms: tuple[tuple[str, ...], ...]
    query_answers: tuple[dict[str, bool], ...]
    query_seconds: float
    decision_seconds: float
    query_irrelevant_atoms: int
    query_total_atoms: int
