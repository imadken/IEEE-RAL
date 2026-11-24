"""Exact finite-catalogue experiment contracts; no population extrapolation."""

from fractions import Fraction
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, StrictBool, model_validator
from pydantic_core import PydanticCustomError

from .schema import Frozen


def rational(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        raise PydanticCustomError(
            "source_unsupported",
            "SOURCE_UNSUPPORTED: use exact integer/rational strings, not floats",
        )
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("SOURCE_UNSUPPORTED: malformed rational") from error


Exact = Annotated[Fraction, BeforeValidator(rational)]
Name = Annotated[str, Field(strict=True, min_length=1, pattern=r".*\S.*")]
Obligation = Literal["useful", "harm_only", "completion", "declared_predicate"]


class World(Frozen):
    world_id: Name
    obligation_verdict: StrictBool
    joint: tuple[Exact, Exact, Exact, Exact] | None = None

    @model_validator(mode="after")
    def joint_law(self):
        if self.joint is not None and (min(self.joint) < 0 or sum(self.joint) != 1):
            raise ValueError(
                "SOURCE_UNSUPPORTED: joint law is not a probability vector"
            )
        return self


def verdict(q: tuple[Fraction, ...], obligation: Obligation) -> bool:
    harm, gain, recovery = q[2], q[1] - q[2], q[1] + q[3]
    if obligation == "harm_only":
        return harm <= Fraction(1, 10)
    if obligation == "completion":
        return recovery >= Fraction(9, 10)
    if obligation != "useful":
        raise ValueError("A declared predicate has caller-supplied finite-world labels")
    return harm <= Fraction(1, 10) and gain >= Fraction(1, 20)


class ExperimentSource(Frozen):
    kind: Literal[
        "randomized_single_action",
        "randomized_arm",
        "qualified_simulator_pair",
        "predecision_observation",
        "abstract_known_law",
    ]
    population_id: Name
    provenance: tuple[Name, ...] = Field(min_length=1)
    assumptions: tuple[Name, ...] = Field(min_length=1)
    qualified: Literal[True]
    participant_selection: Literal["FIXED_BEFORE_OUTCOMES"]
    participant_sampling: Literal[
        "FRESH_CLASS_INDEPENDENT", "DECLARED_ANALYTICAL", "FIXED_CONTEXT_READ"
    ]
    law_origin: Literal["KNOWN_ANALYTICAL_MODEL", "RECORDED_PREDECISION_FACTS"]
    context_operation: Literal["FIXED_OUTCOME_TARGET", "CONTEXT_REFINEMENT"]
    action: Literal["c", "r"] | None = None
    propensity: Exact | None = None
    coupling: Name | None = None
    recorded_channels: tuple[Name, ...] = ()
    observation_timing: Literal["PREDECISION", "NOT_OBSERVATION"] = "NOT_OBSERVATION"

    @model_validator(mode="after")
    def source_semantics(self):
        if (
            self.kind != "predecision_observation"
            and self.law_origin != "KNOWN_ANALYTICAL_MODEL"
        ):
            raise ValueError(
                "SOURCE_UNSUPPORTED: predecision telemetry does not supply causal joint laws"
            )
        if self.kind in ("randomized_arm", "randomized_single_action"):
            if self.propensity != Fraction(1, 2):
                raise ValueError(
                    "SOURCE_UNSUPPORTED: randomized source needs registered e=1/2"
                )
            if self.kind == "randomized_arm" and self.action is None:
                raise ValueError("SOURCE_UNSUPPORTED: conditional arm must be named")
        if self.kind == "qualified_simulator_pair" and self.coupling is None:
            raise ValueError(
                "SOURCE_UNSUPPORTED: paired source needs an explicit coupling"
            )
        if self.kind == "predecision_observation":
            if not self.recorded_channels or self.observation_timing != "PREDECISION":
                raise ValueError(
                    "SOURCE_UNSUPPORTED: observation needs recorded predecision channels"
                )
            if self.context_operation != "CONTEXT_REFINEMENT":
                raise ValueError(
                    "SOURCE_UNSUPPORTED: a new fact changes conditioning context"
                )
        elif self.context_operation != "FIXED_OUTCOME_TARGET":
            raise ValueError(
                "SOURCE_UNSUPPORTED: outcome experiment changed its target"
            )
        if self.participant_sampling == "FIXED_CONTEXT_READ" and (
            self.kind != "predecision_observation"
            or self.law_origin != "RECORDED_PREDECISION_FACTS"
        ):
            raise ValueError("SOURCE_UNSUPPORTED: context reads are not outcome trials")
        return self


class WorldLaw(Frozen):
    world_id: Name
    probabilities: tuple[Exact, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalized(self):
        if min(self.probabilities) < 0 or sum(self.probabilities) != 1:
            raise ValueError("SOURCE_UNSUPPORTED: experiment law is not normalized")
        return self


class Experiment(Frozen):
    experiment_id: Name
    cost: Exact = Field(ge=0)
    alphabet: tuple[Name, ...] = Field(min_length=1)
    laws: tuple[WorldLaw, ...] = Field(min_length=1)
    source: ExperimentSource

    @model_validator(mode="after")
    def common_alphabet(self):
        if len(set(self.alphabet)) != len(self.alphabet):
            raise ValueError("SOURCE_UNSUPPORTED: duplicate outcome labels")
        if len({r.world_id for r in self.laws}) != len(self.laws):
            raise ValueError("SOURCE_UNSUPPORTED: duplicate world laws")
        if any(len(r.probabilities) != len(self.alphabet) for r in self.laws):
            raise ValueError("SOURCE_UNSUPPORTED: inconsistent observable alphabet")
        if self.source.participant_sampling == "FIXED_CONTEXT_READ" and any(
            any(p not in (0, 1) for p in row.probabilities) for row in self.laws
        ):
            raise ValueError(
                "SOURCE_UNSUPPORTED: a recorded context read must be deterministic"
            )
        return self


class ExperimentProblem(Frozen):
    population_id: Name
    obligation: Obligation
    predicate_description: Name
    catalogue_scope: Literal["DECLARED_FINITE_CATALOGUE"]
    complete_for_declared_finite_catalogue: Literal[True]
    cross_experiment_law: Literal["CONDITIONAL_PRODUCT_LAWS"]
    cost_unit: Name
    worlds: tuple[World, ...] = Field(min_length=1)
    experiments: tuple[Experiment, ...]

    @model_validator(mode="after")
    def complete_source_laws(self):
        ids = {w.world_id for w in self.worlds}
        if len(ids) != len(self.worlds):
            raise ValueError("SOURCE_UNSUPPORTED: duplicate world identifiers")
        if len({e.experiment_id for e in self.experiments}) != len(self.experiments):
            raise ValueError("SOURCE_UNSUPPORTED: duplicate experiment identifiers")
        for w in self.worlds:
            if self.obligation != "declared_predicate" and (
                w.joint is None
                or verdict(w.joint, self.obligation) != w.obligation_verdict
            ):
                raise ValueError(
                    "SOURCE_UNSUPPORTED: verdict disagrees with named joint obligation"
                )
        worlds = {w.world_id: w for w in self.worlds}
        for e in self.experiments:
            if {row.world_id for row in e.laws} != ids:
                raise ValueError(
                    "SOURCE_UNSUPPORTED: missing or extra world likelihood"
                )
            if e.source.population_id != self.population_id:
                raise ValueError(
                    "SOURCE_UNSUPPORTED: experiment source population mismatch"
                )
            if e.source.kind in (
                "randomized_arm",
                "randomized_single_action",
                "qualified_simulator_pair",
            ):
                self.check_joint_signatures(e, worlds)
        return self

    @staticmethod
    def check_joint_signatures(e: Experiment, worlds: dict[str, World]) -> None:
        for row in e.laws:
            q = worlds[row.world_id].joint
            if q is None:
                raise ValueError(
                    "SOURCE_UNSUPPORTED: causal likelihood needs a declared joint world"
                )
            p0, p1 = q[2] + q[3], q[1] + q[3]
            if e.source.kind == "qualified_simulator_pair":
                alphabet, expected = ("00", "01", "10", "11"), q
            elif e.source.kind == "randomized_arm":
                p = p0 if e.source.action == "c" else p1
                # Pay for every randomized action, including the other arm.
                # Its observed outcome is withheld, rather than conditioning
                # away the cost/probability of receiving that arm.
                alphabet = ("other_arm", "0", "1")
                expected = (Fraction(1, 2), (1 - p) / 2, p / 2)
            else:
                alphabet = ("c0", "c1", "r0", "r1")
                expected = tuple(v / 2 for v in (1 - p0, p0, 1 - p1, p1))
            if e.alphabet != alphabet or row.probabilities != expected:
                raise ValueError(
                    "SOURCE_UNSUPPORTED: law disagrees with declared outcome source"
                )


class PairCoverage(Frozen):
    worlds: tuple[str, str]
    experiments: tuple[str, ...]


class EqualLaw(Frozen):
    experiment_id: str
    alphabet: tuple[str, ...]
    probabilities: tuple[Exact, ...]


class ImpossibilityWitness(Frozen):
    worlds: tuple[str, str]
    verdicts: tuple[StrictBool, StrictBool]
    identical_laws: tuple[EqualLaw, ...]


class RemovalWitness(Frozen):
    removed_experiment: str
    unseparated_opposing_worlds: tuple[str, str]


class ExperimentPlan(Frozen):
    status: Literal["MINIMUM_RESOLVING_MENU", "NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE"]
    selected_experiments: tuple[str, ...] = ()
    total_cost: Exact | None = None
    cost_unit: str
    opposite_verdict_pairs: int
    coverage: tuple[PairCoverage, ...] = ()
    removal_witnesses: tuple[RemovalWitness, ...] = ()
    impossibility: ImpossibilityWitness | None = None
    unanimous_catalogue_verdict: StrictBool | None = None
    scope: Literal["DECLARED_FINITE_CATALOGUE_ONLY"] = "DECLARED_FINITE_CATALOGUE_ONLY"
    finite_sample_resolution_guaranteed: Literal[False] = False
    physical_authorization: Literal[False] = False
    dynamic_programming_states: int = 0
