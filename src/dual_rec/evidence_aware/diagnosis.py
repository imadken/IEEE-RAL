"""Construct admissible same-marginal worlds; never confuse width with proof."""

from .bounds import P0, P1, G, H, qualifies, solve, vertices
from .schema import Band, Evidence, Witness


def diagnose(e: Evidence) -> Witness:
    try:
        b = solve(e)
    except ValueError as error:
        return Witness(status=str(error), detail="No causal recovery certificate")
    if qualifies(b):
        return Witness(status="CERTIFIED_USEFUL_RECOVERY", detail="H<=.10 and G>=.05")
    if b.harm_lower > 0.1:
        return Witness(status="HARM_UNAVOIDABLE_WITHIN_MODEL", detail=str(b.harm_lower))
    if b.gain_upper < 0.05:
        return Witness(status="BENEFIT_UNSUPPORTED", detail=str(b.gain_upper))
    try:
        favorable = vertices(e, [(H, 0.1), (tuple(-v for v in G), -0.05)])
        for q in favorable:
            p0, p1 = (max(0.0, min(1.0, float(q @ v))) for v in (P0, P1))
            fixed = e.model_copy(
                update={"p0": Band(lo=p0, hi=p0), "p1": Band(lo=p1, hi=p1)}
            )
            worst = solve(fixed)
            if worst.harm_upper > 0.1 + 1e-9:
                barrier = e.p0.lo > 0.1 and e.p1.hi < 0.9
                return Witness(
                    status="MARGINAL_IDENTIFICATION_BARRIER"
                    if barrier
                    else "COUPLING_UNRESOLVED",
                    detail="Same available marginals; useful and harmful compatible joint laws",
                    favorable=tuple(float(v) for v in q),
                    unfavorable=worst.optimizers["harm_upper"],
                )
    except ValueError:
        pass
    return Witness(
        status="FINITE_CONFIDENCE_UNRESOLVED",
        detail="No constructive identification witness found; actual plugin check is separate",
    )


def plugin_diagnosis(e: Evidence, p0: float, p1: float) -> Witness:
    result = diagnose(e)
    if result.status not in ("FINITE_CONFIDENCE_UNRESOLVED", "COUPLING_UNRESOLVED"):
        return result
    exact = Evidence(p0=Band(lo=p0, hi=p0), p1=Band(lo=p1, hi=p1), scope=e.scope)
    if qualifies(solve(exact)):
        return result.model_copy(
            update={
                "status": "SAMPLE_LIMITED_AT_PLUGIN",
                "detail": "Empirical marginals pass; confidence set does not; compatible-world witnesses retained when available",
            }
        )
    return result


def observation_aliasing(pairs):
    """Evaluator-only paired obstruction; never called by a single-arm learner."""
    groups = {}
    for pair in pairs:
        if any(v is None for v in pair.x):
            continue
        key = (pair.source_scope.model_dump_json(), pair.x)
        by_class = groups.setdefault(key, {})
        by_class.setdefault((pair.yc, pair.yr), pair.parent_id)
        if (True, False) in by_class and (False, True) in by_class:
            return Witness(
                status="OBSERVATION_ALIASING",
                detail="Two distinct paired checkpoints share declared X and require opposite actions for individual completion; this does not refute a regional population bound.",
                parent_ids=(by_class[True, False], by_class[False, True]),
            )
    return None


def repertoire_failure(pair):
    if not pair.yc and not pair.yr:
        return Witness(
            status="BENEFIT_UNSUPPORTED",
            detail="Neither fixed macro completes this paired checkpoint; extra observations alone do not change these executed outcomes.",
            parent_ids=(pair.parent_id,),
        )
    return None
