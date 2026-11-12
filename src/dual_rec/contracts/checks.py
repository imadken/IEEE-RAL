"""Dataset-independent evidence obligations; missing evidence never earns PASS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Result(Evidence):
    check: str
    status: Literal["PASS", "FAIL", "UNKNOWN"]
    reason: str
    scope: str = "Supplied evidence only; not a universal proof or dataset verdict"


class PacketHistory(Evidence):
    decisions: list[float]
    source_times: list[float]
    arrivals: list[float]


class AlarmRecord(Evidence):
    time: list[float]
    scores: list[float | None]
    threshold: float
    persistence: float = Field(default=0.1, ge=0)
    tolerance: float = Field(default=1e-7, ge=0)
    reported_alarm: float | None
    reset_times: list[float] = []


class RuntimeInputs(Evidence):
    fields: dict[
        str, Literal["observation", "static", "annotation", "future", "outcome"]
    ]
    allowed_static: list[str] = []


class Recording(Evidence):
    record_id: str
    signal_hash: str
    task_group: str
    source_group: str
    partition: Literal["train", "calibration", "evaluation"]
    role: Literal["failure", "success"]


class Calibration(Evidence):
    reference_ids: list[str]
    prefix_ids: list[str]
    selection_label_ids: list[str]
    reference_verdicts: dict[str, str]
    prefix_stop: dict[str, float]
    onsets: dict[str, float]
    unavailable_prefixes: dict[str, str] = {}


class Event(Evidence):
    record_id: str
    start: float
    end: float
    onset: float | None
    event_required: bool = True
    semantics: Literal[
        "retrospective_deviation", "observable_event", "human_recovery", "unknown"
    ]
    claimed_semantics: Literal[
        "retrospective_deviation", "observable_event", "human_recovery", "unknown"
    ]
    censored: bool = False
    excluded: bool = False


class SimulatorIdentity(Evidence):
    expected_class: str
    actual_class: str
    expected_controller: str
    actual_controller: str
    expected_dimension: int = Field(gt=0)
    actual_dimension: int = Field(gt=0)
    expected_dt: float = Field(gt=0)
    actual_dt: float = Field(gt=0)
    expected_model_hash: str | None = None
    actual_model_hash: str | None = None
    reference_kind: Literal["recorded_scene", "clean_seed", "unknown"] = "unknown"
    controller_memory_recorded: bool | None = None


class Execution(Evidence):
    kind: Literal["actions_stepped", "states_forwarded", "unknown"]
    actions: int = Field(ge=0)
    state_injections_after_start: int = Field(ge=0)
    physics_time_advanced: float = Field(ge=0)
    initial_success: bool
    reported_new_recovery: bool
    observed_success: bool
    original_predicate_checked: bool


class Accounting(Evidence):
    eligible_ids: list[str]
    evaluated_ids: list[str]
    exclusion_reasons: dict[str, str]
    abstention_ids: list[str]
    denominator: int = Field(ge=0)
    uncertainty_unit: Literal["frame", "recording", "task", "robot", "none"]
    independent_groups: int = Field(ge=0)
    claims_population_equivalence_from_zero_bootstrap: bool = False


class BranchPair(Evidence):
    checkpoint_id: str
    state_hashes: list[str]
    policy_memory_hashes: list[str]
    actions: list[str]
    observed_outcomes: list[bool]
    costs: list[float]
    declared_budget: int = Field(gt=0)
    assignment: Literal[
        "matched_counterfactual", "randomized", "observational", "unknown"
    ]
    randomization_provenance: str | None = None


class AuditBundle(Evidence):
    separation_units: list[Literal["source", "task"]] = Field(
        default=["source", "task"], min_length=1
    )
    packets: PacketHistory | None = None
    alarm: AlarmRecord | None = None
    runtime: RuntimeInputs | None = None
    recordings: list[Recording] | None = None
    calibration: Calibration | None = None
    events: list[Event] | None = None
    simulator: SimulatorIdentity | None = None
    execution: Execution | None = None
    accounting: Accounting | None = None
    branches: list[BranchPair] | None = None


def first_alarm(times, scores, threshold, persistence, tolerance=1e-7):
    """Reference scalar state machine: no event annotation is an argument."""
    start = None
    for now, value in zip(times, scores, strict=True):
        if value is None or not np.isfinite(value) or value < threshold:
            start = None
        else:
            if start is None:
                start = now
            if now - start >= persistence - tolerance:
                return float(now)
    return None


def check_prefix(predictor, left, right, cutoff):
    """Bounded counterfactual test, not proof for every possible future suffix."""
    if cutoff < 1 or not np.array_equal(
        np.asarray(left)[:cutoff], np.asarray(right)[:cutoff], equal_nan=True
    ):
        return Result(
            check="prefix_noninterference",
            status="UNKNOWN",
            reason="Perturbation must preserve the supplied prefix",
        )
    a = np.asarray(predictor(left))
    b = np.asarray(predictor(right))
    if a.ndim == 0 or b.ndim == 0 or min(len(a), len(b)) < cutoff:
        return Result(
            check="prefix_noninterference",
            status="UNKNOWN",
            reason="Predictor did not expose enough prefix outputs",
        )
    same = np.allclose(a[:cutoff], b[:cutoff], rtol=0, atol=1e-12, equal_nan=True)
    return Result(
        check="prefix_noninterference",
        status="PASS" if same else "FAIL",
        reason="Fixed-prefix future perturbation agrees"
        if same
        else "Changing a future suffix changed earlier outputs",
        scope="Only the supplied perturbation and predictor execution",
    )


def audit(bundle: AuditBundle) -> list[Result]:
    result = []

    def add(name, ok, reason):
        result.append(
            Result(
                check=name,
                status="UNKNOWN" if ok is None else "PASS" if ok else "FAIL",
                reason=reason,
            )
        )

    p = bundle.packets
    if p is None:
        add("causal_time", None, "No packet provenance supplied")
    else:
        lengths = len(p.decisions) == len(p.source_times) == len(p.arrivals)
        valid = (
            lengths
            and bool(len(p.decisions))
            and np.all(np.diff(p.decisions) > 0)
            and all(
                s <= a + 1e-7 and a <= d + 1e-7
                for s, a, d in zip(p.source_times, p.arrivals, p.decisions, strict=True)
            )
        )
        add(
            "causal_time",
            valid,
            "Source <= arrival <= decision, with increasing decision indices required",
        )
    a = bundle.alarm
    if a is None:
        add("continuous_alarm", None, "No alarm/risk history supplied")
    else:
        valid = (
            len(a.time) == len(a.scores)
            and bool(a.time)
            and np.all(np.diff(a.time) > 0)
        )
        expected = (
            first_alarm(a.time, a.scores, a.threshold, a.persistence, a.tolerance)
            if valid
            else None
        )
        add(
            "continuous_alarm",
            bool(valid and not a.reset_times and expected == a.reported_alarm),
            "First persistent alarm must begin at recording start; annotations never reset it",
        )
    runtime = bundle.runtime
    add(
        "runtime_information",
        None
        if runtime is None or not runtime.fields
        else all(
            kind == "observation"
            or kind == "static"
            and field in runtime.allowed_static
            for field, kind in runtime.fields.items()
        ),
        "Only observations and explicitly declared static context are permitted",
    )
    rows = bundle.recordings
    if not rows:
        add("numeric_duplicates", None, "No recording identities/hashes supplied")
        add("group_separation", None, "No source/task partitions supplied")
    else:
        add(
            "numeric_duplicates",
            len({r.record_id for r in rows}) == len(rows)
            and len({r.signal_hash for r in rows}) == len(rows),
            "Canonical IDs and numerical signal hashes must be unique; aliases require explicit collapse",
        )
        groups = {}
        for row in rows:
            for unit in bundle.separation_units:
                group = unit + ":" + getattr(row, unit + "_group")
                groups.setdefault(group, set()).add(row.partition)
        add(
            "group_separation",
            all(len(v) == 1 for v in groups.values()),
            "Declared independent grouping units cannot cross partitions: "
            + ", ".join(bundle.separation_units),
        )
    c = bundle.calibration
    if c is None or rows is None:
        add(
            "independent_calibration",
            None,
            "Need calibration IDs and recording partitions",
        )
    else:
        by_id = {r.record_id: r for r in rows}
        ids = c.reference_ids + c.prefix_ids
        known = all(
            i in by_id and by_id[i].partition == "calibration"
            for i in ids + c.selection_label_ids
        )
        nominal = all(
            i in by_id
            and by_id[i].role == "success"
            and c.reference_verdicts.get(i) == "success"
            for i in c.reference_ids
        )
        prefixes = all(
            i in by_id
            and by_id[i].role == "failure"
            and i in c.prefix_stop
            and i in c.onsets
            and c.prefix_stop[i] < c.onsets[i]
            for i in c.prefix_ids
        )
        unavailable = all(
            i in by_id
            and by_id[i].partition == "calibration"
            and by_id[i].role == "failure"
            and i not in ids
            and bool(reason)
            for i, reason in c.unavailable_prefixes.items()
        )
        add(
            "independent_calibration",
            bool(
                ids
                and len(ids) == len(set(ids))
                and c.reference_ids
                and known
                and nominal
                and prefixes
                and unavailable
            ),
            "Calibration success references must be independently labeled; prefixes strictly precede onset; evaluation labels cannot select thresholds",
        )
    events = bundle.events
    if not events:
        add("event_bounds", None, "No released event bounds supplied")
        add("event_semantics", None, "No annotation semantic provenance supplied")
    else:
        bounds = all(
            e.start <= e.end
            and (
                e.onset is None
                or e.start <= e.onset <= e.end
                or e.censored
                and not e.excluded
            )
            for e in events
        )
        add(
            "event_bounds",
            False
            if not bounds
            else None
            if any(e.event_required and e.onset is None for e in events)
            else True,
            "Out-of-observation events require explicit retained censoring, never silent clamping or exclusion",
        )
        semantics = (
            False
            if any(
                e.semantics != "unknown"
                and e.claimed_semantics != "unknown"
                and e.semantics != e.claimed_semantics
                for e in events
            )
            else None
            if any(
                e.semantics == "unknown" or e.claimed_semantics == "unknown"
                for e in events
            )
            else True
        )
        add(
            "event_semantics",
            semantics,
            "Retrospective deviation, observable onset and human recovery labels are different semantics",
        )
    s = bundle.simulator
    if s is None:
        add("simulator_identity", None, "No simulator/controller evidence supplied")
    else:
        interface = (
            s.expected_class == s.actual_class
            and s.expected_controller == s.actual_controller
            and s.expected_dimension == s.actual_dimension
            and abs(s.expected_dt - s.actual_dt) < 1e-12
        )
        known = (
            s.reference_kind == "recorded_scene"
            and s.expected_model_hash is not None
            and s.actual_model_hash is not None
            and s.controller_memory_recorded is not None
        )
        same = (
            s.expected_model_hash == s.actual_model_hash
            and s.controller_memory_recorded
        )
        add(
            "simulator_identity",
            False if not interface else None if not known else bool(same),
            "Model class, controller, action/time conventions and recorded-scene identity/controller memory must be supported; clean-seed agreement alone is insufficient",
        )
    x = bundle.execution
    add(
        "physical_execution",
        None
        if x is None or x.kind == "unknown"
        else x.kind == "actions_stepped"
        and x.actions > 0
        and x.state_injections_after_start == 0
        and x.physics_time_advanced > 0
        and x.original_predicate_checked
        and (
            not x.reported_new_recovery or x.observed_success and not x.initial_success
        ),
        "State forwarding is kinematics, not an executed recovery; already-successful initial states are not new recoveries",
    )
    ac = bundle.accounting
    if ac is None:
        add("denominators", None, "No population/accounting supplied")
        add("uncertainty", None, "No uncertainty units supplied")
    else:
        eligible = set(ac.eligible_ids)
        evaluated = set(ac.evaluated_ids)
        excluded = set(ac.exclusion_reasons)
        valid = (
            len(eligible) == len(ac.eligible_ids)
            and len(evaluated) == len(ac.evaluated_ids)
            and not evaluated.intersection(excluded)
            and evaluated | excluded == eligible
            and all(ac.exclusion_reasons.values())
            and set(ac.abstention_ids) <= evaluated
            and ac.denominator == len(evaluated)
        )
        add(
            "denominators",
            valid,
            "Retain abstentions in the denominator; make all exclusions and aliases explicit",
        )
        add(
            "uncertainty",
            ac.uncertainty_unit in ("recording", "task", "robot")
            and ac.independent_groups >= 2
            and not ac.claims_population_equivalence_from_zero_bootstrap,
            "Frames are repeated measures; clustered intervals do not erase small-cohort/dependence limits",
        )
    branches = bundle.branches
    if branches is None:
        add(
            "intervention_effect",
            None,
            "No executed paired interventions/costs supplied",
        )
    else:
        valid = bool(branches) and all(
            len(b.actions) >= 2
            and len(b.actions)
            == len(b.observed_outcomes)
            == len(b.costs)
            == len(b.state_hashes)
            == len(b.policy_memory_hashes)
            and all(b.state_hashes)
            and all(b.policy_memory_hashes)
            and all(c >= 0 for c in b.costs)
            and len(set(b.actions)) >= 2
            and (
                b.assignment == "matched_counterfactual"
                and len(set(b.state_hashes)) == 1
                and len(set(b.policy_memory_hashes)) == 1
                or b.assignment == "randomized"
                and bool(b.randomization_provenance)
            )
            for b in branches
        )
        add(
            "intervention_effect",
            valid,
            "A claim of intervention effectiveness requires declared matched/randomized executed alternatives and outcome/cost evidence, not detection labels",
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refuse to overwrite an existing audit")
    results = audit(AuditBundle.model_validate_json(args.input.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([r.model_dump() for r in results], indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
