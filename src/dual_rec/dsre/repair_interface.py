"""Attach a pre-frozen offline instrumentation plan without online feature selection."""

from typing import Literal

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence

from .repair import RepairOutput, RepairScope
from .repair_selection import OPTIONAL
from .schemas import Certificate


class OfflineUpgrade(Evidence):
    status: Literal["OFFLINE_DEVELOPMENT_SELECTED"] = "OFFLINE_DEVELOPMENT_SELECTED"
    channels: tuple[str, ...]
    abstract_cost: int = Field(ge=0, le=3)
    budget: int = Field(ge=0, le=3)
    training_rows: int = Field(gt=0)
    training_before_mass: int = Field(ge=0)
    training_after_mass: int = Field(ge=0)
    reference_sha256: str = Field(min_length=64, max_length=64)
    selector: str
    guarantees_current_query_repair: Literal[False] = False
    cost_units: Literal["abstract_predicate_channels_not_hardware_time_energy"] = (
        "abstract_predicate_channels_not_hardware_time_energy"
    )

    @model_validator(mode="after")
    def consistent(self):
        if len(set(self.channels)) != len(self.channels) or any(
            c not in OPTIONAL for c in self.channels
        ):
            raise ValueError("Only the fixed declared optional channels are allowed")
        if len(self.channels) != self.abstract_cost or self.abstract_cost > self.budget:
            raise ValueError("Upgrade must respect its actual unit channel budget")
        if (
            not 0
            <= self.training_before_mass
            <= self.training_after_mass
            <= self.training_rows
        ):
            raise ValueError("Nested finite training mass must not decrease")
        return self


class EvidenceRepairDecision(Evidence):
    result: RepairOutput
    offline_upgrade: OfflineUpgrade
    why_not_actions: dict[str, tuple[str, ...]]
    deployment_enabled: Literal[False] = False


def attach_plan(output: RepairOutput, frozen_design: dict, primary_training_mass: int):
    """Consumes only a completed diagnosis and training-frozen metadata, no optional query values."""
    upgrade = OfflineUpgrade(
        channels=tuple(OPTIONAL[i] for i in frozen_design["channels"]),
        abstract_cost=len(frozen_design["channels"]),
        budget=frozen_design["budget"],
        training_rows=frozen_design["training_rows"],
        training_before_mass=primary_training_mass,
        training_after_mass=frozen_design["training_ceiling_mass"],
        reference_sha256=frozen_design["reference_sha256"],
        selector=frozen_design["selector"],
    )
    why_not = {}
    if output.action is None:
        for action in ("continue", "recover"):
            ids = tuple(
                s.id
                for w in output.certificate.witnesses
                if w.kind == "UNEXCLUDABLE_BAD_ROW" and w.action == action
                for s in w.states
            )
            why_not[action] = ids
    return EvidenceRepairDecision(
        result=output, offline_upgrade=upgrade, why_not_actions=why_not
    )


def restore_output(value: dict):
    """Restore a refined scope without widening historical certificate schemas."""
    certificate = dict(value["certificate"])
    certificate["scope"] = RepairScope.model_validate(certificate["scope"])
    return RepairOutput.model_validate(
        value | {"certificate": Certificate.model_validate(certificate)}
    )
