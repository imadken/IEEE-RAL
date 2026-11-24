"""Immutable boundaries: observations never carry unexecuted outcomes."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Source(StrEnum):
    LOGGED = "randomized_single_action"
    PAIRED = "qualified_simulator_pair"
    OBSERVATIONAL = "uncontrolled_observational"


class Scope(Frozen):
    task: str
    controller_sha256: str
    horizon: int = Field(gt=0)
    outcome: str
    population: str
    observation_protocol: str
    coupling: str = "deterministic experimental model; no real-world transfer claim"


class OneAction(Frozen):
    parent_id: str
    x: tuple[bool | None, ...] = Field(min_length=1, max_length=6)
    action: Literal["c", "r"]
    propensity: float = Field(gt=0, lt=1)
    y: bool
    controls: int = Field(ge=0)
    wall_seconds: float = Field(ge=0)
    source_scope: Scope
    source_type: Source = Source.LOGGED
    counterpart_exposed: Literal[False] = False


class Observation(Frozen):
    parent_id: str
    x: tuple[bool | None, ...] = Field(min_length=1, max_length=6)
    source_scope: Scope


class Pair(Frozen):
    parent_id: str
    x: tuple[bool | None, ...]
    yc: bool
    yr: bool
    source_scope: Scope
    counterpart_exposed: Literal[True] = True
    selection: Literal["uniform_before_outcomes"] = "uniform_before_outcomes"


class PolicyExecution(Frozen):
    parent_id: str
    x: tuple[bool | None, ...]
    action: Literal["c", "r"]
    propensity: Literal[1.0] = 1.0
    y: bool
    controls: int = Field(ge=0)
    wall_seconds: float = Field(ge=0)
    source_scope: Scope
    source_type: Literal["deterministic_frozen_policy"] = "deterministic_frozen_policy"
    counterpart_exposed: Literal[False] = False


class Band(Frozen):
    lo: float = Field(ge=0, le=1)
    hi: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.lo > self.hi:
            raise ValueError("INCONSISTENT_BOUNDS")
        return self


class Evidence(Frozen):
    p0: Band
    p1: Band
    harm: Band | None = None
    rescue: Band | None = None
    source_type: Source = Source.LOGGED
    scope: str
    assumptions_supported: bool = True
    overlap: bool = True


class Bounds(Frozen):
    harm_lower: float
    harm_upper: float
    gain_lower: float
    gain_upper: float
    failure_upper: float
    optimizers: dict[str, tuple[float, float, float, float]]


class Partition(Frozen):
    vocabulary: tuple[str, ...] = Field(min_length=1, max_length=6)
    cells: tuple[int, ...]
    tree: tuple[int, int, int]  # -1 is an unsplit branch
    discovery_parents: tuple[str, ...]

    @model_validator(mode="after")
    def complete(self):
        if len(self.cells) != 2 ** len(self.vocabulary) or len(set(self.cells)) > 4:
            raise ValueError("Partition must cover the complete Boolean space")
        return self


class Certificate(Frozen):
    action: Literal["r"] = "r"
    obligation: Literal["useful", "harm_only", "completion"]
    evidence: tuple[tuple[str, bool], ...]
    selected_leaf_scope: tuple[int, ...]
    harm_upper: float
    gain_lower: float
    failure_upper: float
    source_type: Source
    outcome_scope: Scope
    confidence_family: str
    assumptions: tuple[str, ...]
    removal_witnesses: dict[str, str]


class Witness(Frozen):
    status: str
    detail: str
    favorable: tuple[float, float, float, float] | None = None
    unfavorable: tuple[float, float, float, float] | None = None
    parent_ids: tuple[str, ...] = ()
