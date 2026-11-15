"""Sound bounded telemetry adapter; finite validity and population risk stay separate.

Position errors are absolute, coordinate-wise bounds for EACH object, hand and
goal reading in EACH supporting frame. Shared errors are allowed but not assumed:
the product set is a conservative superset. Finger encoders are assumed exact.
No motion envelope is declared: a stale current frame supplies no current facts.
"""

import math
from itertools import product
from typing import Literal

from pydantic import Field

from dual_rec.contracts.checks import Evidence

from .features import PRIMARY, ObservationHistory, feature_values
from .operational import OperationalRouter, PolicyInput
from .repair_selection import OPTIONAL, optional_values
from .schemas import LiteralFact


class MeasurementScope(Evidence):
    coordinate_error_m: float = Field(ge=0)
    decision_time: float
    reference_scope_identity: str
    source_regime: str
    clean_risk_scope_eligible: bool = False
    error_set: Literal["ABSOLUTE_COORDINATE_BOX_EACH_POSE_EACH_FRAME"] = (
        "ABSOLUTE_COORDINATE_BOX_EACH_POSE_EACH_FRAME"
    )
    finger_error_scope: Literal["EXACT_ENCODERS_ASSUMED"] = "EXACT_ENCODERS_ASSUMED"


class ThresholdFact(Evidence):
    feature: str
    measured: bool | None
    invariant: bool | None
    lower: float | None
    upper: float | None
    reason: str


class MeasurementEvidence(Evidence):
    scope: MeasurementScope
    source_times: tuple[float | None, float]
    facts: tuple[ThresholdFact, ...]
    measured_literals: tuple[LiteralFact, ...]
    invariant_literals: tuple[LiteralFact, ...]
    undecidable_threshold_facts: tuple[str, ...]
    instability_witnesses: tuple[ThresholdFact, ...]
    risk_qualification_covers_sensor_regime: bool
    risk_scope_reason: str

    def packet(self, task: str) -> PolicyInput:
        full = tuple(f.invariant for f in self.facts)
        return PolicyInput(
            task=task,
            values=full[:7] if task == "PickCube-v1" else full[:6],
            full_values=full,
        )


def invariant_value(lower, upper, threshold, relation):
    if lower is None or upper is None:
        return None
    if relation == "le":
        return True if upper <= threshold else False if lower > threshold else None
    if relation == "ge":
        return True if lower >= threshold else False if upper < threshold else None
    if relation == "gt":
        return True if lower > threshold else False if upper <= threshold else None
    if relation == "lt":
        return True if upper < threshold else False if lower >= threshold else None
    raise ValueError("Unknown inequality")


def bounded_evidence(history: ObservationHistory, scope: MeasurementScope):
    if history.current.time > scope.decision_time:
        raise ValueError("Future observation")
    rho = scope.coordinate_error_m
    first, current = history.first, history.current
    measured = feature_values(history) + optional_values(history)
    stale = current.time < scope.decision_time - 1e-9
    radius = 2 * math.sqrt(3) * rho

    def dist(a, b):
        if a is None or b is None:
            return None
        d = math.dist(a, b)
        return max(0.0, d - radius), d + radius

    def delta(a, b, i):
        if a is None or b is None:
            return None
        d = a[i] - b[i]
        return d - 2 * rho, d + 2 * rho

    obj, hand, goal = (
        current.object_position,
        current.tcp_position,
        current.goal_position,
    )
    near, proximity = dist(obj, goal), dist(hand, obj)
    before = (
        dist(first.object_position, first.goal_position)
        if first is not None and first.time < current.time
        else None
    )
    progress = (
        (before[0] - near[1], before[1] - near[0])
        if before is not None and near is not None
        else None
    )
    moved = (
        dist(first.object_position, obj)
        if first is not None and first.time < current.time
        else None
    )
    fingers = (
        None
        if current.finger_positions is None
        else (sum(abs(v) for v in current.finger_positions),) * 2
    )
    dx, dy, hx = delta(obj, goal, 0), delta(obj, goal, 1), delta(hand, obj, 0)
    intervals = (near, proximity, progress, moved, fingers, delta(hand, obj, 2))
    intervals += (dx, dx, dy, dy, hx, hx)
    relations = ("le", "le", "ge", "ge", "le", "gt") + ("lt", "gt") * 3
    thresholds = (0.03, 0.04, 0.005, 0.005, 0.04, 0.03) + (-0.02, 0.02) * 3
    facts = []
    for name, value, bounds, relation, threshold in zip(
        PRIMARY + OPTIONAL, measured, intervals, relations, thresholds, strict=True
    ):
        lower, upper = bounds if bounds is not None else (None, None)
        robust = None if stale else invariant_value(lower, upper, threshold, relation)
        facts.append(
            ThresholdFact(
                feature=name,
                measured=value,
                invariant=robust,
                lower=lower,
                upper=upper,
                reason="STALE_WITHOUT_MOTION_ENVELOPE"
                if stale
                else "MISSING_MEASUREMENT"
                if bounds is None
                else "OBSERVATION_INSTABILITY"
                if robust is None
                else "INVARIANT_OVER_DECLARED_SET",
            )
        )
    eligible = scope.clean_risk_scope_eligible and rho == 0 and not stale
    return MeasurementEvidence(
        scope=scope,
        source_times=(None if first is None else first.time, current.time),
        facts=tuple(facts),
        measured_literals=tuple(
            LiteralFact(feature=f.feature, value=f.measured)
            for f in facts
            if f.measured is not None
        ),
        invariant_literals=tuple(
            LiteralFact(feature=f.feature, value=f.invariant)
            for f in facts
            if f.invariant is not None
        ),
        undecidable_threshold_facts=tuple(
            f.feature for f in facts if f.invariant is None
        ),
        instability_witnesses=tuple(
            f for f in facts if f.reason == "OBSERVATION_INSTABILITY"
        ),
        risk_qualification_covers_sensor_regime=eligible,
        risk_scope_reason="ELIGIBLE_FOR_SEPARATE_ORIGINAL_METHOD_ACTION_GATE"
        if eligible
        else "NO_TRANSFER_TO_ALTERED_SENSOR_OR_SOURCE_REGIME",
    )


class RobustRouter:
    """Unchanged DSRE; trees use unanimous actions over all Boolean completions.

    Boolean completions overapproximate jointly reachable predicate patterns. This
    may abstain excessively but never hides a reachable conflicting tree decision.
    Completion-only path literals are never asserted as measured facts.
    """

    def __init__(self, frozen):
        self.point = OperationalRouter(frozen)
        self.cache = {}

    def route(self, packet: PolicyInput):
        key = (packet.task, packet.values, packet.full_values)
        if key in self.cache:
            return self.cache[key]
        original = self.point.route(packet)
        output = {name: dict(value) for name, value in original.items()}
        unknown = [i for i, v in enumerate(packet.values) if v is None]
        if unknown:
            completion_results = []
            for choice in product((False, True), repeat=len(unknown)):
                full = list(packet.full_values)
                for i, v in zip(unknown, choice, strict=True):
                    full[i] = v
                completed = PolicyInput(
                    task=packet.task,
                    values=tuple(full[: len(packet.values)]),
                    full_values=tuple(full),
                )
                completion_results.append(self.point.route(completed))
            for name in (
                "CART1_strict",
                "CART2_strict",
                "CART1_beta10",
                "CART2_beta10",
                "CART2_pruned_strict",
            ):
                actions = {d[name]["action"] for d in completion_results}
                action = next(iter(actions)) if len(actions) == 1 else None
                known = {
                    self.point.settings[packet.task][2].table.scope.features[i]: v
                    for i, v in enumerate(packet.values)
                    if v is not None
                }
                output[name] = {
                    "action": action,
                    "evidence": [
                        {"feature": name, "value": value}
                        for name, value in sorted(known.items())
                    ]
                    if action
                    else [],
                    "support": min(d[name]["support"] for d in completion_results),
                    "independent_parents": min(
                        d[name]["independent_parents"] for d in completion_results
                    ),
                    "status": "UNANIMOUS_FROZEN_TREE_COMPLETIONS"
                    if action
                    else "AMBIGUOUS_OR_UNSUPPORTED_TREE_COMPLETIONS",
                    "completion_count": len(completion_results),
                }
        assert output["DSRE_strict"]["action"] == output["B7"]["action"]
        assert output["DSRE_risk"]["action"] == output["B7_risk"]["action"]
        self.cache[key] = output
        return output


def explain(evidence: MeasurementEvidence, router: RobustRouter, task: str):
    decisions = router.route(evidence.packet(task))
    strict = decisions["DSRE_strict"]
    return {
        **evidence.model_dump(mode="json"),
        "minimum_certificate": strict.get("diagnosis"),
        "reason_for_abstention": None
        if strict["action"]
        else {
            "observation": [f.reason for f in evidence.facts if f.invariant is None],
            "finite_reference": strict.get("diagnosis", {}).get("obstructions", []),
        },
        "decisions": decisions,
    }
