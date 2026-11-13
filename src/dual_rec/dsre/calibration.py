"""Frozen-router, independent-parent calibration; no rerouting or physics calls."""

import math

from pydantic import Field, StrictBool, model_validator

from dual_rec.contracts.checks import Evidence

from .schemas import Action


def binomial_cdf(k: int, n: int, p: float) -> float:
    if p == 0:
        return 1.0
    if p == 1:
        return float(k == n)
    terms = [
        math.lgamma(n + 1)
        - math.lgamma(j + 1)
        - math.lgamma(n - j + 1)
        + j * math.log(p)
        + (n - j) * math.log1p(-p)
        for j in range(k + 1)
    ]
    maximum = max(terms)
    return math.exp(maximum) * sum(math.exp(t - maximum) for t in terms)


def upper_bound(k: int, n: int, delta: float) -> float:
    """One-sided Clopper-Pearson error bound, including N=0 and all errors."""
    if not 0 < delta < 1 or not 0 <= k <= n:
        raise ValueError("Require 0<delta<1 and 0<=errors<=accepted")
    if not n or k == n:
        return 1.0
    if k == 0:
        return -math.expm1(math.log(delta) / n)
    low, high = 0.0, 1.0
    for _ in range(80):
        middle = (low + high) / 2
        if binomial_cdf(k, n, middle) > delta:
            low = middle
        else:
            high = middle
    return high


def zero_error_required(alpha=0.10, delta=0.0125) -> int:
    if not 0 < alpha < 1 or not 0 < delta < 1:
        raise ValueError("Require alpha, delta strictly between zero and one")
    return math.ceil(math.log(delta) / math.log1p(-alpha))


class FrozenRouter(Evidence):
    sha256: str = Field(min_length=64, max_length=64)
    training_parent_ids: tuple[str, ...]
    strata: tuple[str, ...]
    alpha: float = Field(default=0.10, gt=0, lt=1)
    delta: float = Field(default=0.05, gt=0, lt=1)

    @model_validator(mode="after")
    def uniqueness(self):
        if not self.strata or len(set(self.strata)) != len(self.strata):
            raise ValueError(
                "Declare unique nonempty task/action strata before calibration"
            )
        if len(set(self.training_parent_ids)) != len(self.training_parent_ids):
            raise ValueError("Training parents must be unique")
        if any(
            s.rsplit("/", 1)[-1] not in ("continue", "recover") for s in self.strata
        ):
            raise ValueError("Unknown action in calibration stratum")
        return self


class CalibrationObservation(Evidence):
    parent_id: str
    router_sha256: str
    task: str
    assigned_action: Action | None
    violated: StrictBool | None


class StratumBound(Evidence):
    stratum: str
    assigned: int
    violations: int
    unknown_outcomes: int
    delta: float
    upper: float
    enabled: bool


class CalibrationResult(Evidence):
    router_sha256: str
    independent_parents: int
    alpha: float
    total_delta: float
    strata: tuple[StratumBound, ...]


class DeploymentDecision(Evidence):
    proposed_action: Action | None
    action: Action | None
    reason: str


def calibrate(router: FrozenRouter, observations: tuple[CalibrationObservation, ...]):
    ids = [o.parent_id for o in observations]
    if len(set(ids)) != len(ids):
        raise ValueError(
            "Repeated physical parents cannot count as independent observations"
        )
    if set(ids) & set(router.training_parent_ids):
        raise ValueError(
            "Reused fitting/development parents are not independent calibration"
        )
    if any(o.router_sha256 != router.sha256 for o in observations):
        raise ValueError("Calibration does not belong to the frozen router")
    tasks = {s.rsplit("/", 1)[0] for s in router.strata}
    for o in observations:
        if o.task not in tasks or (
            o.assigned_action and o.task + "/" + o.assigned_action not in router.strata
        ):
            raise ValueError("Observation is outside predeclared calibration scope")
        if o.assigned_action is None and o.violated is not None:
            raise ValueError("An abstention has no executed recommendation error label")
    per_delta = router.delta / len(router.strata)
    bounds = []
    for stratum in router.strata:
        assigned = [
            o
            for o in observations
            if o.assigned_action and o.task + "/" + o.assigned_action == stratum
        ]
        k, missing = (
            sum(o.violated is True for o in assigned),
            sum(o.violated is None for o in assigned),
        )
        upper = 1.0 if missing else upper_bound(k, len(assigned), per_delta)
        bounds.append(
            StratumBound(
                stratum=stratum,
                assigned=len(assigned),
                violations=k,
                unknown_outcomes=missing,
                delta=per_delta,
                upper=upper,
                enabled=bool(assigned) and upper <= router.alpha,
            )
        )
    return CalibrationResult(
        router_sha256=router.sha256,
        independent_parents=len(observations),
        alpha=router.alpha,
        total_delta=router.delta,
        strata=tuple(bounds),
    )


def gate(
    task: str,
    action: Action | None,
    router_sha256: str,
    calibration: CalibrationResult | None,
):
    if action is None:
        return DeploymentDecision(
            proposed_action=None, action=None, reason="TABLE_INSUFFICIENT"
        )
    if calibration is None:
        return DeploymentDecision(
            proposed_action=action, action=None, reason="CALIBRATION_INSUFFICIENT"
        )
    if router_sha256 != calibration.router_sha256:
        raise ValueError("Calibration is stale for this router")
    bound = next(
        (s for s in calibration.strata if s.stratum == task + "/" + action), None
    )
    enabled = bound is not None and bound.enabled
    return DeploymentDecision(
        proposed_action=action,
        action=action if enabled else None,
        reason="CALIBRATED_ROUTER" if enabled else "CALIBRATION_INSUFFICIENT",
    )
