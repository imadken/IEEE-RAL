"""Claim-specific qualification of finite, physically executed evidence bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field

from dual_rec.contracts.checks import AuditBundle, Evidence


class Claim(Evidence):
    version: str = "recoveryclaim-v1"
    intended: Literal[
        "ONLINE_ALARM", "EXECUTABLE_RECOVERY", "MATCHED_INTERVENTION_EFFECT"
    ] = "EXECUTABLE_RECOVERY"
    task: str
    parent: str
    action: str
    model_hash: str | None
    history_hash: str | None
    unobserved_state_fields: list[str] = Field(default_factory=list)
    controller_hash: str | None
    reference_controller_hash: str | None = None
    reference_parent: str | None = None
    reference_model_hash: str | None = None
    reference_history_hash: str | None = None
    expected_actions: list[list[float]] | None = None
    state_injections: int = 0
    budget: int = Field(gt=0)
    dt: float = Field(default=0.05, gt=0)
    actions: list[list[float]]
    times: list[float]
    success: list[bool]
    initial_success: bool = False
    checkpoint_error: float = Field(default=0, ge=0)
    state_errors: list[float]
    contract_violation: str | None = None
    trace_hash: str | None = None
    raw_trace_path: str | None = None
    raw_trace_key: str | None = None
    source_path: str | None = None
    discordances: int = Field(default=0, ge=0)
    qualification_parents: int = Field(default=0, ge=0)
    alpha: float = Field(default=0.005, gt=0, lt=1)
    epsilon: float = Field(default=0.025, gt=0, lt=1)
    completion_qualified: bool = False
    completion_success: list[bool] | None = None
    cost_error: float = 0
    cost_tolerance: float = 0.1


@lru_cache(maxsize=2048)
def discordance_upper(k, n, alpha=0.005):
    if not 0 <= k <= n or not 0 < alpha < 1:
        raise ValueError("Invalid binomial counts or alpha")
    if n == 0:
        return 1.0
    # Invert the binomial CDF without scipy; assumes independent sampled parents.
    if k == n:
        return 1.0
    import math

    def cdf(p):
        return sum(
            math.exp(
                math.lgamma(n + 1)
                - math.lgamma(j + 1)
                - math.lgamma(n - j + 1)
                + j * math.log(max(p, 1e-300))
                + (n - j) * math.log(max(1 - p, 1e-300))
            )
            for j in range(k + 1)
        )

    lo, hi = 0.0, 1.0
    for _ in range(70):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def certify(c: Claim, method="M"):
    if c.intended != "EXECUTABLE_RECOVERY":
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "intended": c.intended,
            "missing": ["Use paired evidence or causal alarm evidence API"],
            "witness": None,
        }
    witness = None
    if (
        len(c.actions) != c.budget
        or len(c.success) != c.budget
        or len(c.times) != c.budget
    ):
        witness = {
            "obligation": "budget",
            "observed": len(c.actions),
            "expected": c.budget,
        }
    elif c.reference_parent is not None and c.reference_parent != c.parent:
        witness = {
            "obligation": "parent_identity",
            "expected": c.reference_parent,
            "observed": c.parent,
        }
    elif (
        c.reference_model_hash is not None
        and c.model_hash is not None
        and c.reference_model_hash != c.model_hash
    ):
        witness = {
            "obligation": "model_identity",
            "expected": c.reference_model_hash,
            "observed": c.model_hash,
        }
    elif (
        c.reference_history_hash is not None
        and c.history_hash != c.reference_history_hash
    ):
        witness = {
            "obligation": "history_identity",
            "expected": c.reference_history_hash,
            "observed": c.history_hash,
        }
    elif c.expected_actions is not None and c.actions != c.expected_actions:
        i = next(
            (
                i
                for i, (a, b) in enumerate(zip(c.actions, c.expected_actions))
                if a != b
            ),
            min(len(c.actions), len(c.expected_actions)),
        )
        witness = {"obligation": "first_wrong_control", "index": i}
    elif (
        method != "no_memory"
        and c.reference_controller_hash is not None
        and c.controller_hash is not None
        and c.controller_hash != c.reference_controller_hash
    ):
        witness = {
            "obligation": "controller_identity",
            "expected": c.reference_controller_hash,
            "observed": c.controller_hash,
        }
    elif c.state_injections:
        witness = {"obligation": "state_injection", "index": 1}
    elif c.contract_violation and not (
        method == "no_memory" and c.contract_violation.startswith("controller")
    ):
        witness = {"obligation": "execution_contract", "observed": c.contract_violation}
    elif len(c.times) > 1 and not np.allclose(
        np.diff(c.times), c.dt, atol=1e-7, rtol=0
    ):
        witness = {"obligation": "time", "observed": c.times}
    missing = [
        k
        for k in [
            "model_hash",
            "history_hash",
            "controller_hash",
            "reference_controller_hash",
        ]
        if getattr(c, k) is None
    ]
    completable = bool(missing) and not any(
        field in missing for field in ["model_hash", "history_hash"]
    )
    f2 = (
        c.checkpoint_error <= 1
        and bool(c.state_errors)
        and len(c.state_errors) == c.budget
        and max(c.state_errors) <= 1
    )
    upper = discordance_upper(c.discordances, c.qualification_parents, c.alpha)
    decision = upper <= c.epsilon and c.cost_error <= c.cost_tolerance
    completion = False
    if method == "no_F3":
        decision = False
    if method == "B0":
        status = "SUPPORTED"
    elif witness:
        status = "REFUTED_CONTRACT"
    elif method == "B3":
        status = "SUPPORTED"
    elif (
        completable
        and c.completion_qualified
        and method in ("M", "B4", "no_F3", "no_unknown")
    ):
        status = "SUPPORTED"
        completion = True
    elif missing and not (
        method == "no_memory"
        and all(k in ["controller_hash", "reference_controller_hash"] for k in missing)
    ):
        status = "INSUFFICIENT_EVIDENCE"
    elif method in ["B1", "B2"]:
        status = "SUPPORTED" if f2 else "INSUFFICIENT_EVIDENCE"
    elif method == "B4" or f2 or decision:
        status = "SUPPORTED"
    elif c.completion_qualified and method != "no_completion":
        status = "SUPPORTED"
        completion = True
    else:
        status = "INSUFFICIENT_EVIDENCE"
    if method == "no_unknown" and status == "INSUFFICIENT_EVIDENCE":
        status = "SUPPORTED"
    if completion and (
        c.completion_success is None or len(c.completion_success) != c.budget
    ):
        status = "INSUFFICIENT_EVIDENCE"
        completion = False
    selected = c.completion_success if completion else c.success
    return {
        "version": c.version,
        "task": c.task,
        "parent": c.parent,
        "action": c.action,
        "intended": c.intended,
        "method": method,
        "status": status,
        "witness": witness,
        "missing": missing,
        "F1": "FAIL" if witness else "UNKNOWN" if missing else "PASS",
        "F2": f2,
        "F2_unobserved": c.unobserved_state_fields,
        "F3": {
            "discordance_upper": upper,
            "n": c.qualification_parents,
            "passed": decision,
        },
        "completed_with_prefix": completion,
        "new_success": not c.initial_success and any(selected),
        "candidate_terminal_success": c.success[-1] if c.success else None,
        "terminal_success": selected[-1] if selected else None,
        "scope": "Finite recorded execution; not safety, universal replay equivalence, or an identified positive intervention effect",
        "dependencies": {
            "decision": [
                "model",
                "controller",
                "history",
                "budget",
                "outcome_predicate",
            ],
            "effect": ["qualified_start", "matched_actions", "uncertainty"],
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    payload = json.loads(a.bundle.read_text())
    if "branches" in payload:
        c = None
        result = matched_effect(MatchedEvidence.model_validate(payload))
    elif payload.get("intended", "EXECUTABLE_RECOVERY") == "ONLINE_ALARM":
        c = None
        result = certify_alarm(AlarmEvidence.model_validate(payload))
    else:
        c = Claim.model_validate(payload)
        result = certify(c)
    result["bundle_sha256"] = hashlib.sha256(a.bundle.read_bytes()).hexdigest()
    if a.verify:
        import gzip

        raw_claims = (
            [Claim.model_validate(b) for b in payload["branches"]]
            if "branches" in payload
            else [c]
            if c is not None
            else []
        )
        for c in raw_claims:
            if c.raw_trace_path is None:
                continue
            base = a.bundle.parent.parent.resolve()
            raw_path = (base / c.raw_trace_path).resolve()
            assert raw_path.is_relative_to(base), "Trace path escapes evidence root"
            assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == c.trace_hash
            with gzip.open(raw_path, "rt") as stream:
                raw = json.load(stream)["traces"][c.raw_trace_key]
            assert [bool(f["state"]["success"]) for f in raw["frames"]] == c.success
            assert [f["state"]["time"] for f in raw["frames"]] == c.times
            assert raw["row"]["actions"] == c.actions
            assert raw["row"]["task"] == c.task and str(raw["row"]["seed"]) == c.parent
            assert raw["row"]["history_hash"] == c.history_hash
            if c.controller_hash is not None:
                assert (
                    hashlib.sha256(
                        json.dumps(raw["controller_memory"], sort_keys=True).encode()
                    ).hexdigest()
                    == c.controller_hash
                )
            if c.reference_controller_hash is not None:
                with gzip.open(raw_path, "rt") as stream:
                    reference = json.load(stream)["traces"][c.action + "/reference"]
                assert (
                    hashlib.sha256(
                        json.dumps(
                            reference["controller_memory"], sort_keys=True
                        ).encode()
                    ).hexdigest()
                    == c.reference_controller_hash
                )
            if c.completion_success is not None:
                with gzip.open(raw_path, "rt") as stream:
                    full = json.load(stream)
                fresh = full["traces"][c.action + "/fresh_prefix"]["frames"]
                assert [
                    bool(f["state"]["success"]) for f in fresh
                ] == c.completion_success
        assert json.loads(a.output.read_text()) == result
        print("VERIFIED")
        return
    with a.output.open("x") as f:
        json.dump(result, f, indent=2)
    print(result["status"], result["witness"])


class MatchedEvidence(Evidence):
    branches: list[Claim] = Field(min_length=2)


def matched_effect(evidence: MatchedEvidence):
    branches = evidence.branches
    for field in [
        "parent",
        "task",
        "model_hash",
        "history_hash",
        "controller_hash",
        "budget",
        "dt",
    ]:
        if len({getattr(b, field) for b in branches}) != 1:
            return {
                "status": "REFUTED_CONTRACT",
                "witness": {"obligation": "matched_" + field},
            }
    if len({b.action for b in branches}) != len(branches):
        return {
            "status": "REFUTED_CONTRACT",
            "witness": {"obligation": "distinct_alternatives"},
        }
    if any(
        b.model_hash is None or b.history_hash is None or b.controller_hash is None
        for b in branches
    ):
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "witness": None,
            "missing": ["matched model/history/controller provenance"],
        }
    statuses = [certify(b)["status"] for b in branches]
    return {
        "status": "REFUTED_CONTRACT"
        if "REFUTED_CONTRACT" in statuses
        else "INSUFFICIENT_EVIDENCE"
        if "INSUFFICIENT_EVIDENCE" in statuses
        else "SUPPORTED",
        "intended": "MATCHED_INTERVENTION_EFFECT",
        "scope": "Matched finite executed alternatives only; population effects and effect sign require separate parent-level inference",
        "actions": [b.action for b in branches],
    }


class AlarmEvidence(Evidence):
    intended: Literal["ONLINE_ALARM"] = "ONLINE_ALARM"
    task: str
    parent: str
    evidence: AuditBundle


def certify_alarm(claim: AlarmEvidence):
    from dual_rec.contracts.checks import AuditBundle, audit

    checks = audit(AuditBundle.model_validate(claim.evidence))
    relevant = [
        r
        for r in checks
        if r.check
        not in ["simulator_identity", "physical_execution", "intervention_effect"]
    ]
    bad = next((r for r in relevant if r.status == "FAIL"), None)
    witness = bad.model_dump() if bad else None
    if bad and bad.check == "continuous_alarm" and claim.evidence.alarm is not None:
        from dual_rec.contracts.checks import first_alarm

        a = claim.evidence.alarm
        witness.update(
            observed_alarm=a.reported_alarm,
            expected_continuous_alarm=first_alarm(
                a.time, a.scores, a.threshold, a.persistence, a.tolerance
            ),
            reset_times=a.reset_times,
        )
    return {
        "version": "recoveryclaim-v1",
        "intended": "ONLINE_ALARM",
        "task": claim.task,
        "parent": claim.parent,
        "status": "REFUTED_CONTRACT"
        if bad
        else "INSUFFICIENT_EVIDENCE"
        if any(r.status == "UNKNOWN" for r in relevant)
        else "SUPPORTED",
        "witness": witness,
        "obligations": [r.model_dump() for r in relevant],
        "scope": "Protocol support, not detector performance or physical recovery improvement",
    }


if __name__ == "__main__":
    main()
