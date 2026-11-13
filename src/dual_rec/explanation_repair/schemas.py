"""Explicit boundaries for observations, commands, deductions and text coverage."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence


class Window(Evidence):
    clock: Literal["seconds", "snapshot", "plan_index"] = "seconds"
    start: float
    end: float

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("Reversed time interval")
        return self


class Fact(Evidence):
    entity: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: bool | str

    def key(self) -> tuple[str, str]:
        return self.entity, self.predicate


class Predicate(Evidence):
    entity: str
    predicate: str

    def key(self) -> tuple[str, str]:
        return self.entity, self.predicate


class Record(Evidence):
    id: str
    fact: Fact
    window: Window
    source: str
    visibility: Literal["visible", "not_visible", "unknown"] = "visible"
    kind: Literal["observation", "command"] = "observation"
    action: str | None = None

    @model_validator(mode="after")
    def command_has_action(self):
        if self.kind == "command" and not self.action:
            raise ValueError("Commands require a declared action name")
        return self


class ActionRule(Evidence):
    id: str
    action: str
    preconditions: list[Fact] = Field(min_length=1)
    may_change: list[Predicate] = Field(default_factory=list)


class ActionModel(Evidence):
    rules: list[ActionRule] = Field(default_factory=list)
    persistent: list[Predicate] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_rules(self):
        if len({r.action for r in self.rules}) != len(self.rules):
            raise ValueError("One rule per action is required")
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("Duplicate model-rule identifiers")
        return self


class Claim(Evidence):
    id: str
    kind: Literal["observation", "implication", "hypothesis", "recommendation"]
    window: Window
    fact: Fact | None = None
    action: str | None = None
    depends_on: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def required_fields(self):
        if self.kind != "hypothesis" and self.fact is None:
            raise ValueError("A factual slot is required")
        if self.kind in ("implication", "recommendation") and self.action is None:
            raise ValueError("Action-model claims require an action")
        return self


class RepairInput(Evidence):
    id: str
    records: list[Record]
    model: ActionModel = Field(default_factory=ActionModel)
    claims: list[Claim]
    original_text: str = ""
    unparsed: list[str] = Field(default_factory=list)
    query: Window

    @model_validator(mode="after")
    def unique_ids(self):
        for values in (self.records, self.claims):
            if len({x.id for x in values}) != len(values):
                raise ValueError("Duplicate evidence or claim identifiers")
        return self


class Support(Evidence):
    status: Literal["supported", "contradicted", "unknown"]
    basis: Literal["observation", "model_deduction", "unresolved"] = "unresolved"
    evidence: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    reason: str


class Grounded(Evidence):
    origin: str
    claim: Claim
    support: Support


class Decision(Evidence):
    origin: str
    operation: Literal["keep", "replace", "unknown", "remove"]
    output: Grounded | None
    reason: str
    evaluation: Support | None = None


class RepairResult(Evidence):
    id: str
    method: str
    claims: list[Grounded]
    decisions: list[Decision]
    unresolved: list[str]
    text: str
    menus_evaluated: int = 0
    max_menu_size: int = 0


class Objective(Evidence):
    replacement: float = Field(default=0.5, ge=0)
    qualification: float = Field(default=0.8, ge=0)
    removal: float = Field(default=1.0, ge=0)
    supported_fact_loss: float = Field(default=3.0, ge=0)
    group_size: int = Field(default=4, ge=1, le=6)
