"""Exact bounded strong planning with physical transitions and explicit STOP.

The Bellman/AND-OR recursion is standard; no novel planning algorithm is claimed.
Only declared deterministic analytical truth tables are accepted.
"""

from fractions import Fraction
from functools import cache

from .schema import (
    FiniteProbeProblem,
    Obstruction,
    PolicyBranch,
    PolicyNode,
    ProbeObstruction,
    ProbePlan,
    RecoveryCounterexample,
)


def plan_probes(problem: FiniteProbeProblem) -> ProbePlan:
    states = {s.state_id: s for s in problem.states}
    recoveries = {
        s.state_id: {r.action_id: r for r in s.recoveries} for s in problem.states
    }
    probes = sorted(problem.probes, key=lambda p: p.probe_id)
    transitions = {p.probe_id: {t.state_id: t for t in p.transitions} for p in probes}
    safe = problem.require_physical_safety

    @cache
    def solve(belief, h, remaining):
        unsafe = tuple(s for s in belief if not states[s].physically_allowed)
        if safe and unsafe:
            return None, Obstruction(
                belief=belief,
                remaining_horizon=h,
                remaining_cost=remaining,
                reason="INITIAL_STATE_UNSAFE",
                unsafe_states=unsafe,
            )
        counterexamples = []
        for action in sorted(problem.recovery_actions):
            bad = next(
                (
                    s
                    for s in belief
                    if not recoveries[s][action].task_success
                    or (safe and not recoveries[s][action].path_safe)
                ),
                None,
            )
            if bad is None:
                return (
                    Fraction(0),
                    PolicyNode(belief=belief, decision="RECOVER", action_id=action),
                ), None
            reason = (
                "TASK_FAILURE"
                if not recoveries[bad][action].task_success
                else "PHYSICAL_PATH_UNSAFE"
            )
            counterexamples.append(
                RecoveryCounterexample(action_id=action, state_id=bad, reason=reason)
            )
        blocked, candidates = [], []
        if h:
            for probe in probes:
                rows = transitions[probe.probe_id]
                bad = next((s for s in belief if not rows[s].enabled), None)
                if bad is not None:
                    blocked.append(
                        ProbeObstruction(
                            probe_id=probe.probe_id, reason="DISABLED", state_id=bad
                        )
                    )
                    continue
                bad = next(
                    (
                        s
                        for s in belief
                        if safe
                        and (
                            not rows[s].path_safe
                            or not states[rows[s].successor].physically_allowed
                        )
                    ),
                    None,
                )
                if bad is not None:
                    blocked.append(
                        ProbeObstruction(
                            probe_id=probe.probe_id,
                            reason="PHYSICAL_PATH_UNSAFE",
                            state_id=bad,
                        )
                    )
                    continue
                if remaining is not None and probe.cost > remaining:
                    blocked.append(
                        ProbeObstruction(probe_id=probe.probe_id, reason="COST_BUDGET")
                    )
                    continue
                groups = {}
                for s in belief:
                    row = rows[s]
                    groups.setdefault(row.observation, set()).add(row.successor)
                children, costs, failed = [], [], None
                for observation, successors in sorted(groups.items()):
                    child, failure = solve(
                        tuple(sorted(successors)),
                        h - 1,
                        None if remaining is None else remaining - probe.cost,
                    )
                    if child is None:
                        failed = ProbeObstruction(
                            probe_id=probe.probe_id,
                            reason="LOSING_BRANCH",
                            observation=observation,
                            child=failure,
                        )
                        break
                    cost, policy = child
                    costs.append(cost)
                    children.append(PolicyBranch(observation=observation, child=policy))
                if failed is not None:
                    blocked.append(failed)
                else:
                    candidates.append(
                        (
                            probe.cost + max(costs),
                            probe.probe_id,
                            PolicyNode(
                                belief=belief,
                                decision="PROBE",
                                action_id=probe.probe_id,
                                branches=tuple(children),
                            ),
                        )
                    )
        if candidates:
            cost, _, policy = min(candidates, key=lambda row: row[:2])
            return (cost, policy), None
        return None, Obstruction(
            belief=belief,
            remaining_horizon=h,
            remaining_cost=remaining,
            reason="ALL_PROBES_BLOCKED" if h else "NO_COMMON_RECOVERY_AT_HORIZON",
            recoveries=tuple(counterexamples),
            probes=tuple(blocked),
        )

    belief = tuple(sorted(problem.initial_support))
    solution, failure = solve(belief, problem.horizon, problem.max_probe_cost)
    if solution is None:
        return ProbePlan(
            status="STOP_NO_ROBUST_POLICY",
            policy=PolicyNode(belief=belief, decision="STOP"),
            worst_probe_cost=None,
            obstruction=failure,
            dynamic_programming_states=solve.cache_info().currsize,
        )
    cost, policy = solution
    return ProbePlan(
        status="ROBUST_FINITE_MODEL_RECOVERY",
        policy=policy,
        worst_probe_cost=cost,
        dynamic_programming_states=solve.cache_info().currsize,
    )


def observed_branch(policy: PolicyNode, observation: str) -> PolicyNode:
    """Follow a known observation; a model miss never restores the root belief."""
    if policy.decision != "PROBE":
        raise ValueError("No observation branch exists after a terminal decision")
    for branch in policy.branches:
        if branch.observation == observation:
            return branch.child
    raise ValueError(
        "SOURCE_UNSUPPORTED_UNKNOWN_OBSERVATION: stop and report the model miss"
    )
