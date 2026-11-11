"""Freshness policies share observations, history and the declared belief gate."""

from collections.abc import Callable
from math import log
from time import perf_counter

from dual_rec.monitoring.semantics import certify, regress, relevant_atoms
from dual_rec.monitoring.upstream import load_upstream

from .belief import (
    Belief,
    BeliefLimit,
    InconsistentBelief,
    build_belief,
    select_exact_query,
)
from .contracts import FreshDecision, Reading, RevalidationContext

METHODS = frozenset(
    {"B0", "B1", "B2", "B3", "B4", "B5", "B6", "SVR", "SVR_no_impact", "SVR_no_risk"}
)
Sensing = Callable[[str], Reading]


def project_cache(ctx: RevalidationContext) -> dict[str, bool | None]:
    """Apply observed deterministic effects; hidden events are never read here."""
    evidence = dict(ctx.base.evidence)
    evidence.update(
        {
            atom: value
            for atom, value in ctx.cache_observations.items()
            if value is not None
        }
    )
    for action in ctx.known_after_cache:
        evidence.update({atom: False for atom in action.delete})
        evidence.update({atom: True for atom in action.add})
    return evidence


def _known_effect(ctx: RevalidationContext, atom: str) -> bool | None:
    value = None
    for action in ctx.known_after_cache:
        if atom in action.delete:
            value = False
        if atom in action.add:
            value = True
    return value


def _relevant(ctx: RevalidationContext) -> frozenset[str]:
    if regress(ctx.base.plan, ctx.base.goal) is None:
        return frozenset(
            lit.atom for action in ctx.base.plan for lit in action.pre
        ) | frozenset(lit.atom for lit in ctx.base.goal)
    unknown = dict.fromkeys(ctx.base.model.atoms)
    return relevant_atoms(ctx.base.model, unknown, ctx.base.plan, ctx.base.goal)


def _gate(probability: float, threshold: float) -> tuple[str, str]:
    if probability >= threshold:
        return "CONTINUE", "BELIEF_PERMISSION"
    if probability <= 1 - threshold:
        return "RECOVER", "BELIEF_INVALID"
    return "ABSTAIN", "BELIEF_UNRESOLVED"


def run_policy(
    ctx: RevalidationContext,
    method: str,
    budget: int,
    sense: Sensing,
    initial_belief: Belief | None = None,
) -> FreshDecision:
    """Choose queries and permission without evaluator state, labels or seeds.

    B2/B3/B4 execute their proactive schedule before the common posterior gate.
    B5/SVR stop at that gate. B6 may query beyond it when its exact nominal
    decision utility prefers another observation; it is a separate reference.
    Probability metadata is unavailable when belief_failure is non-null. Legacy
    B0/B1 still retain their diagnostic hard-evidence behavior in that case.
    """
    if method not in METHODS:
        raise ValueError("Unknown revalidation policy")
    if type(budget) is not int or not 0 <= budget <= 3:
        raise ValueError("Observation budget must be 0..3")
    if any(len(query.atoms) != 1 or query.cost != 1 for query in ctx.base.queries):
        raise ValueError("The registered interface uses unit-cost single-atom queries")
    atoms = tuple(sorted(next(iter(query.atoms)) for query in ctx.base.queries))
    if len(set(atoms)) != len(atoms) or any(
        atom not in ctx.base.model.atoms for atom in atoms
    ):
        raise ValueError("Query atoms must be unique declared propositions")
    started = perf_counter()
    evidence = project_cache(ctx)
    cached_claims = dict(evidence)
    stamps = dict(ctx.observed_at) | dict(ctx.updated_at)
    readings = []
    sensor_seconds = 0.0
    failure = None
    belief = initial_belief
    if belief is None:
        try:
            belief = build_belief(ctx)
        except (BeliefLimit, InconsistentBelief) as error:
            if method == "B6" and isinstance(error, BeliefLimit):
                raise
            failure = str(error)
    relevant = _relevant(ctx)
    current = frozenset(
        lit.atom for lit in (ctx.base.plan[0].pre if ctx.base.plan else ctx.base.goal)
    )
    initial_probability = (
        belief.probability(ctx.base.plan, ctx.base.goal) if belief is not None else 0.0
    )
    stale_risks = (
        {
            atom: belief.stale_risk(atom, cached_claims.get(atom))
            for atom in sorted(relevant)
        }
        if belief is not None
        else {}
    )

    def age(atom):
        return max(0, ctx.age - stamps.get(atom, ctx.cache_time))

    def acquire(atom):
        nonlocal belief, sensor_seconds, failure
        if (
            len(readings) >= budget
            or atom in {r.atom for r in readings}
            or atom not in atoms
        ):
            raise ValueError("Observation budget or common query menu violated")
        before = perf_counter()
        reading = Reading.model_validate(sense(atom))
        sensor_seconds += perf_counter() - before
        if reading.atom != atom or reading.measured_at not in {ctx.cache_time, ctx.age}:
            raise ValueError(
                "Sensing response violates the declared query/timestamp contract"
            )
        readings.append(reading)
        known_value = _known_effect(ctx, atom)
        if reading.measured_at <= ctx.cache_time and known_value is not None:
            evidence[atom] = known_value
        elif reading.conflict:
            evidence[atom] = None
            stamps[atom] = reading.measured_at
        elif reading.value is not None or method in {"B0", "B1"}:
            evidence[atom] = reading.value
            stamps[atom] = reading.measured_at
        # Missing freshness readings retain the last claim, but not a renewed age.
        if method == "B3" and age(atom) > ctx.parameters.expiry_steps:
            evidence[atom] = None
        if belief is not None:
            try:
                belief = belief.condition(reading)
            except InconsistentBelief as error:
                failure = str(error)
                belief = None

    if method == "B0":
        upstream = load_upstream()
        from logiv.core.verification import Observation, Verifier

        offset = ctx.age % len(atoms) if atoms else 0
        periodic = atoms[offset:] + atoms[:offset]

        class Runtime:
            index = 0

            def observe(self, active=False):
                if active and self.index < len(periodic):
                    acquire(periodic[self.index])
                    self.index += 1
                return Observation(
                    raw={tuple(atom.split()): value for atom, value in evidence.items()}
                )

        class Perception:
            def assess(self, observation, requested):
                return {atom: observation.raw.get(atom) for atom in requested}

        fixed = {
            clause[0].atom for clause in ctx.base.model.constraints if len(clause) == 1
        }
        state = upstream.State(
            frozenset(
                tuple(atom.split()) for atom, value in evidence.items() if value is True
            ),
            frozenset(
                tuple(atom.split())
                for atom in ctx.base.model.atoms
                if evidence.get(atom) is None
            ),
        )
        required = frozenset(
            upstream.Literal(tuple(lit.atom.split()), lit.positive)
            for lit in (ctx.base.plan[0].pre if ctx.base.plan else ctx.base.goal)
        )
        runtime = Runtime()
        verifier = Verifier(
            runtime,
            Perception(),
            additional_observations=min(budget, len(atoms)),
            tracked_atoms=frozenset(
                tuple(atom.split()) for atom in ctx.base.model.atoms - fixed
            ),
            static_predicates=frozenset(atom.split()[0] for atom in fixed),
        )
        state, _, resolved = verifier.state_gate(state, required, runtime.observe())
        choice, status = (
            ("ABSTAIN", "UNRESOLVED")
            if not resolved
            else ("CONTINUE", "CURRENT_VALID")
            if state.holds(required)
            else ("RECOVER", "CURRENT_INVALID")
        )
    elif method == "B1":
        status = certify(ctx.base.model, evidence, ctx.base.plan, ctx.base.goal)
        while status == "UNRESOLVED" and len(readings) < budget:
            needed = relevant_atoms(
                ctx.base.model, evidence, ctx.base.plan, ctx.base.goal
            )
            candidates = [
                a for a in atoms if a in needed and a not in {r.atom for r in readings}
            ]
            if not candidates:
                break
            acquire(candidates[0])
            status = certify(ctx.base.model, evidence, ctx.base.plan, ctx.base.goal)
        choice = (
            "CONTINUE"
            if status == "VALID"
            else "RECOVER"
            if status == "INVALID"
            else "ABSTAIN"
        )
    elif belief is None:
        choice, status = "ABSTAIN", "MODEL_INCONSISTENT"
    elif method in {"B2", "B3", "B4"}:
        if method == "B2":
            offset = ctx.age % len(atoms) if atoms else 0
            periodic = atoms[offset:] + atoms[:offset]
            candidates = [
                a
                for a in periodic
                if a in relevant and age(a) >= ctx.parameters.periodic_interval
            ]
        elif method == "B3":
            candidates = sorted(
                (
                    a
                    for a in atoms
                    if a in relevant and age(a) > ctx.parameters.expiry_steps
                ),
                key=lambda a: (-age(a), a not in current, a),
            )
            for atom in candidates:
                evidence[atom] = None
        else:
            candidates = [a for a in atoms if a in current]
        for atom in candidates[:budget]:
            acquire(atom)
            if belief is None:
                break
        choice, status = (
            _gate(
                belief.probability(ctx.base.plan, ctx.base.goal),
                ctx.parameters.permission_threshold,
            )
            if belief is not None
            else ("ABSTAIN", "MODEL_INCONSISTENT")
        )
    else:
        theta = ctx.parameters.permission_threshold
        # Enforce the reduced reference limits even if its initial gate resolves.
        if method == "B6":
            oracle_atoms = tuple(a for a in atoms if a in current)
            oracle_atoms += tuple(
                a for a in atoms if a in relevant and a not in current
            )
            oracle_atoms += tuple(
                a for a in atoms if a not in current and a not in relevant
            )
            oracle_atoms = oracle_atoms[:8]
            oracle_pending = select_exact_query(belief, oracle_atoms, budget, theta)
            oracle_first = True
        while True:
            probability = belief.probability(ctx.base.plan, ctx.base.goal)
            choice, status = _gate(probability, theta)
            if (method != "B6" and choice != "ABSTAIN") or len(readings) >= budget:
                break
            predictive = {
                a: belief.predict_reading(a, belief.query_time)
                for a in (oracle_atoms if method == "B6" else atoms)
                if a not in belief.queried_atoms
                and (method in {"B5", "B6"} or a in relevant)
            }
            candidates = [
                a
                for a, probability_true in predictive.items()
                if 0 < probability_true < 1
            ]
            if not candidates:
                break
            if method == "B6":
                if oracle_first:
                    selected = oracle_pending
                    oracle_first = False
                else:
                    available = tuple(
                        a for a in oracle_atoms if a not in belief.queried_atoms
                    )
                    selected = select_exact_query(
                        belief, available, budget - len(readings), theta
                    )
                if selected is None:
                    break
            elif method == "B5":
                values = belief.one_step_values(candidates, theta)

                def b5_key(atom, predictive=predictive, values=values):
                    p = predictive[atom]
                    entropy = -p * log(p) - (1 - p) * log(1 - p)
                    return -values[atom], -entropy, atom

                selected = min(candidates, key=b5_key)
            else:

                def svr_key(atom):
                    risk = (
                        1.0
                        if method == "SVR_no_risk"
                        else belief.stale_risk(atom, evidence.get(atom))
                    )
                    impact = (
                        1.0
                        if method == "SVR_no_impact"
                        else ctx.base.consequence.get(atom, 1.0)
                        + (len(ctx.base.plan) + 1 if atom in current else 0)
                    )
                    return -risk * impact, atom

                selected = min(candidates, key=svr_key)
            acquire(selected)
            if belief is None:
                choice, status = "ABSTAIN", "MODEL_INCONSISTENT"
                break
    final_probability = (
        belief.probability(ctx.base.plan, ctx.base.goal) if belief is not None else 0.0
    )
    final_current = (
        belief.probability((), ctx.base.plan[0].pre if ctx.base.plan else ctx.base.goal)
        if belief is not None
        else 0.0
    )
    return FreshDecision(
        method=method,
        choice=choice,
        status=status,
        evidence=evidence,
        readings=tuple(readings),
        initial_plan_probability=initial_probability,
        final_plan_probability=final_probability,
        final_current_probability=final_current,
        stale_risks=stale_risks,
        decision_seconds=perf_counter() - started,
        sensor_seconds=sensor_seconds,
        belief_hypotheses=len(belief.hypotheses) if belief is not None else 0,
        belief_failure=failure,
    )
