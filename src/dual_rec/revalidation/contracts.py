"""Runtime history and evaluator truth occupy separate strict contracts."""

from typing import Literal

from pydantic import Field

from dual_rec.monitoring.contracts import Context, StrictModel
from dual_rec.monitoring.semantics import Action


class Parameters(StrictModel):
    event_hazard: float = Field(ge=0, le=1)
    sensor_error: float = Field(ge=0, le=0.5)
    missing_probability: float = Field(default=0.10, ge=0, le=1)
    permission_threshold: float = Field(ge=0.5, le=1)
    periodic_interval: int = Field(ge=1)
    expiry_steps: int = Field(ge=0)


class Reading(StrictModel):
    atom: str
    value: bool | None
    measured_at: int
    source: str = "symbolic_inspection"
    conflict: bool = False


class RevalidationContext(StrictModel):
    """No event identity, oracle state, test rate, seed or outcome is admitted."""

    base: Context
    actions: tuple[Action, ...]
    trusted_anchor: frozenset[str]
    cache_observations: dict[str, bool | None]
    observed_at: dict[str, int]
    updated_at: dict[str, int]
    observation_sources: dict[str, str] = Field(default_factory=dict)
    update_sources: dict[str, str] = Field(default_factory=dict)
    known_after_cache: tuple[Action, ...] = ()
    pre_gap: int = Field(default=1, ge=0, le=4)
    age: int = Field(ge=0, le=8)
    cache_time: int = 0
    query_delay: int = Field(default=0, ge=0, le=8)
    parameters: Parameters


class FreshEpisode(StrictModel):
    episode_id: str
    parent_id: str
    family: str
    split: Literal["development", "qualification", "control"]
    checkpoint: int
    schedule: int
    regime: str
    context: RevalidationContext
    oracle_cache_state: frozenset[str]
    oracle_state: frozenset[str]
    persistent_bias: frozenset[str]
    missing_queries: frozenset[str]
    external_actions: tuple[str | None, ...]
    actual_event_hazard: float
    actual_sensor_error: float
    source_hashes: dict[str, str]


class FreshDecision(StrictModel):
    method: str
    choice: Literal["CONTINUE", "RECOVER", "ABSTAIN"]
    status: str
    evidence: dict[str, bool | None]
    readings: tuple[Reading, ...]
    initial_plan_probability: float
    final_plan_probability: float
    final_current_probability: float
    stale_risks: dict[str, float]
    decision_seconds: float
    sensor_seconds: float
    belief_hypotheses: int
    belief_failure: str | None = None
