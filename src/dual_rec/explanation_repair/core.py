"""Small enumerative editor; support is conditional on supplied grounding/model."""

from __future__ import annotations

from itertools import product

from .schemas import (
    Claim,
    Decision,
    Fact,
    Grounded,
    Objective,
    RepairInput,
    RepairResult,
    Support,
    Window,
)


def observe(
    bundle: RepairInput,
    fact: Fact,
    window: Window,
    temporal=True,
    allow_persistence=True,
) -> Support:
    records = [
        r
        for r in bundle.records
        if r.kind == "observation"
        and r.visibility == "visible"
        and r.fact.key() == fact.key()
        and r.window.clock == window.clock
    ]
    eligible = []
    for record in records:
        if not temporal:
            eligible.append(record)
            continue
        if record.window.start <= window.start and record.window.end >= window.end:
            eligible.append(record)
        elif (
            allow_persistence
            and record.window.end < window.start
            and fact.key() in {p.key() for p in bundle.model.persistent}
        ):
            # Unknown actions are conservative barriers, not assumed no-ops.
            barriers = [
                r
                for r in bundle.records
                if r.kind == "command"
                and r.window.clock == window.clock
                and record.window.end < r.window.end
                and r.window.start <= window.end
            ]
            rules = {r.action: r for r in bundle.model.rules}
            if not any(
                r.action not in rules
                or fact.key() in {p.key() for p in rules[r.action].may_change}
                for r in barriers
            ):
                eligible.append(record)
    if not temporal and eligible:
        latest = max(r.window.start for r in eligible)
        eligible = [r for r in eligible if r.window.start == latest]
    if not eligible:
        return Support(
            status="unknown",
            reason="No visible observation covers the claim interval; commands do not prove effects",
        )
    # A point observation that contradicts a longer supplied interval is a conflict.
    overlapping = [
        r
        for r in records
        if not temporal
        or (r.window.start <= window.end and r.window.end >= window.start)
    ]
    values = {r.fact.value for r in eligible + (overlapping if temporal else [])}
    identifiers = sorted({r.id for r in eligible + (overlapping if temporal else [])})
    if len(values) != 1:
        return Support(
            status="unknown",
            evidence=identifiers,
            reason="Conflicting observations remain unresolved",
        )
    inferred = temporal and any(r.window.end < window.start for r in eligible)
    return Support(
        status="supported" if eligible[0].fact.value == fact.value else "contradicted",
        basis="model_deduction" if inferred else "observation",
        evidence=identifiers,
        rules=[f"persistence/{fact.entity}/{fact.predicate}"] if inferred else [],
        reason="Inferred under declared persistence; no new observation at the query interval"
        if inferred
        else (
            "Visible observation at the declared interval"
            if temporal
            else "Temporal distinctions disabled (ablation)"
        ),
    )


def assess(
    bundle: RepairInput, claim: Claim, temporal=True, action_model=True
) -> Support:
    if claim.kind == "hypothesis":
        return Support(
            status="unknown",
            reason="The supplied observations/model do not establish a unique physical cause",
        )
    if claim.kind == "observation":
        return observe(
            bundle, claim.fact, claim.window, temporal, allow_persistence=action_model
        )
    rule = next((r for r in bundle.model.rules if r.action == claim.action), None)
    if not action_model or rule is None:
        return Support(status="unknown", reason="No applicable declared action model")
    requirements = [
        observe(bundle, f, claim.window, temporal) for f in rule.preconditions
    ]
    blocked = any(r.status == "contradicted" for r in requirements)
    applicable = all(r.status == "supported" for r in requirements)
    if not blocked and not applicable:
        return Support(status="unknown", reason="Unresolved action preconditions")
    expected = Fact(entity=rule.action, predicate="applicable", value=not blocked)
    if claim.fact != expected or (claim.kind == "recommendation" and blocked):
        return Support(
            status="contradicted",
            evidence=sorted({e for r in requirements for e in r.evidence}),
            rules=[rule.id],
            reason="Claim differs from declared model applicability; no recovery guarantee follows",
        )
    used = (
        [r for r in requirements if r.status == "contradicted"]
        if blocked
        else requirements
    )
    return Support(
        status="supported",
        basis="model_deduction",
        evidence=sorted({e for r in used for e in r.evidence}),
        rules=[rule.id],
        reason="Declared preconditions only; not unique causation or guaranteed recovery",
    )


def fact_identity(claim: Claim) -> tuple:
    return (claim.kind, claim.fact, claim.window, claim.action)


def render_claim(claim: Claim, query: Window | None = None) -> str:
    if query is not None and claim.window != query:
        interval = claim.window
        point = (
            f"{interval.start:g}"
            if interval.start == interval.end
            else f"[{interval.start:g}, {interval.end:g}]"
        )
        label = (
            f"t={point} s"
            if interval.clock == "seconds"
            else f"{interval.clock} {point}"
        )
        return f"At {label}, " + render_claim(claim)
    if claim.kind == "hypothesis":
        return "A causal hypothesis is present, but its cause is not established."
    if claim.kind in ("implication", "recommendation"):
        if claim.kind == "recommendation":
            return f"Action '{claim.action}' is eligible under the declared model; success is not guaranteed."
        state = "eligible" if claim.fact.value else "blocked"
        return f"Action '{claim.action}' is {state} under the declared preconditions; this does not establish a unique physical cause."
    fact = claim.fact
    if isinstance(fact.value, bool):
        name = fact.predicate.replace("_", " ")
        return f"{fact.entity} is {'' if fact.value else 'not '}{name}."
    relation = {
        "on_top": "on top of",
        "inside": "inside",
        "below": "below",
        "left_of": "on the left of",
        "right_of": "on the right of",
        "occupant": "occupied by",
    }.get(fact.predicate, fact.predicate.replace("_", " "))
    return f"{fact.entity} is {relation} {fact.value}."


def finish(bundle, method, choices, unresolved, evaluations=0, menu_size=0, text=None):
    grounded = [c.output for c in choices if c.output is not None]
    rendered = " ".join(
        dict.fromkeys(
            (
                "Under the declared persistence model, "
                if g.claim.kind == "observation"
                and g.support.basis == "model_deduction"
                else ""
            )
            + render_claim(g.claim, bundle.query)
            for g in grounded
        )
    )
    if not rendered:
        rendered = (
            "The available evidence does not establish a specific failure explanation."
        )
    elif unresolved:
        rendered += " Some claims remain unresolved."
    return RepairResult(
        id=bundle.id,
        method=method,
        claims=grounded,
        decisions=choices,
        unresolved=unresolved,
        text=rendered if text is None else text,
        menus_evaluated=evaluations,
        max_menu_size=menu_size,
    )


def menu(bundle, claim, temporal, action_model):
    support = assess(bundle, claim, temporal, action_model)
    choices = []
    if support.status == "supported":
        choices.append(
            Decision(
                origin=claim.id,
                operation="keep",
                output=Grounded(origin=claim.id, claim=claim, support=support),
                reason=support.reason,
            )
        )
    # Exactly one directly supported replacement is allowed, and no value guessing.
    replacements = []
    if claim.fact is not None and support.status != "supported":
        if claim.kind in ("observation", "hypothesis"):
            for record in bundle.records:
                if (
                    record.fact.key() == claim.fact.key()
                    and record.kind == "observation"
                ):
                    candidate = claim.model_copy(
                        update={
                            "kind": "observation",
                            "fact": record.fact,
                            "action": None,
                        }
                    )
                    proof = assess(bundle, candidate, temporal, action_model)
                    if proof.status == "supported" and not any(
                        fact_identity(c) == fact_identity(candidate)
                        for c, _ in replacements
                    ):
                        replacements.append((candidate, proof))
        elif action_model:
            for value in (False, True):
                candidate = claim.model_copy(
                    update={
                        "kind": "implication",
                        "fact": Fact(
                            entity=claim.action, predicate="applicable", value=value
                        ),
                    }
                )
                proof = assess(bundle, candidate, temporal, action_model)
                if proof.status == "supported":
                    replacements.append((candidate, proof))
    if len(replacements) == 1:
        candidate, proof = replacements[0]
        choices.append(
            Decision(
                origin=claim.id,
                operation="replace",
                output=Grounded(origin=claim.id, claim=candidate, support=proof),
                reason="Directly supported alternative, with observation and deduction types separated",
            )
        )
    choices.extend(
        [
            Decision(
                origin=claim.id,
                operation="unknown",
                output=None,
                reason=support.reason,
                evaluation=support,
            ),
            Decision(
                origin=claim.id,
                operation="remove",
                output=None,
                reason=support.reason,
                evaluation=support,
            ),
        ]
    )
    assert len(choices) <= 4
    return choices


def edit(
    bundle: RepairInput,
    objective: Objective | None = None,
    *,
    temporal=True,
    action_model=True,
) -> RepairResult:
    objective = objective or Objective()
    pending = list(bundle.claims)
    selected: dict[str, Decision] = {}
    evaluations = 0
    max_size = 0
    unresolved = [
        f"Unparsed span {i}: no grounded claim extracted"
        for i, _ in enumerate(bundle.unparsed)
    ]
    costs = {
        "keep": 0,
        "replace": objective.replacement,
        "unknown": objective.qualification,
        "remove": objective.removal,
    }
    while pending:
        ready = [c for c in pending if all(d in selected for d in c.depends_on)][
            : objective.group_size
        ]
        if not ready:
            # No silent truncation: cycles and missing/forward-unresolvable references
            # are explicitly retained as unresolved items.
            for claim in pending:
                selected[claim.id] = Decision(
                    origin=claim.id,
                    operation="unknown",
                    output=None,
                    reason="Missing or cyclic claim reference",
                )
            break
        menus = []
        for claim in ready:
            if any(selected[d].operation != "keep" for d in claim.depends_on):
                options = [
                    Decision(
                        origin=claim.id,
                        operation="unknown",
                        output=None,
                        reason="Referenced original claim was changed or not established",
                    )
                ]
            else:
                options = menu(bundle, claim, temporal, action_model)
            menus.append(options)
            max_size = max(max_size, len(options))
        original_supported = {
            fact_identity(c)
            for c in ready
            if assess(bundle, c, temporal, action_model).status == "supported"
        }

        def loss(choices, supported=original_supported):
            retained = {fact_identity(c.output.claim) for c in choices if c.output}
            return sum(
                costs[c.operation] for c in choices
            ) + objective.supported_fact_loss * len(supported - retained)

        possibilities = list(product(*menus))
        evaluations += len(possibilities)
        best = min(
            possibilities, key=lambda v: (loss(v), tuple(c.operation for c in v))
        )
        for claim, choice in zip(ready, best, strict=True):
            selected[claim.id] = choice
            pending.remove(claim)
    choices = [selected[c.id] for c in bundle.claims]
    unresolved.extend(f"{c.origin}: {c.reason}" for c in choices if c.output is None)
    return finish(
        bundle,
        "proposed"
        if temporal and action_model
        else "no_temporal"
        if not temporal
        else "no_action_model",
        choices,
        unresolved,
        evaluations,
        max_size,
    )


def baselines(bundle: RepairInput) -> dict[str, RepairResult]:
    original = [
        Decision(
            origin=c.id,
            operation="keep",
            output=Grounded(origin=c.id, claim=c, support=assess(bundle, c)),
            reason="Unchanged input",
        )
        for c in bundle.claims
    ]
    outputs = {
        "original": finish(
            bundle,
            "original",
            original,
            list(bundle.unparsed),
            text=bundle.original_text,
        )
    }
    contradiction = any(c.output.support.status == "contradicted" for c in original)
    outputs["generic"] = finish(
        bundle,
        "generic",
        [] if contradiction else original,
        ["Detected contradiction; adapted parent fallback omits unavailable timestamps"]
        if contradiction
        else list(bundle.unparsed),
        text=None if contradiction else bundle.original_text,
    )
    kept = [c for c in original if c.output.support.status == "supported"]
    outputs["delete"] = finish(
        bundle,
        "delete",
        kept,
        [
            f"Removed {len(original) - len(kept)} unsupported clauses; {len(bundle.unparsed)} unparsed spans"
        ]
        if len(kept) != len(original) or bundle.unparsed
        else [],
    )
    generated = []
    seen = set()
    # Strong regeneration sees the complete same visible history, not just the
    # original explanation's slots or the last observation.
    for record in bundle.records:
        candidate = Claim(
            id=f"regen/{record.id}",
            kind="observation",
            fact=record.fact,
            window=record.window,
        )
        identity = fact_identity(candidate)
        proof = assess(bundle, candidate)
        if (
            record.kind == "observation"
            and identity not in seen
            and proof.status == "supported"
        ):
            seen.add(identity)
            generated.append(
                Decision(
                    origin=candidate.id,
                    operation="keep",
                    output=Grounded(
                        origin=candidate.id, claim=candidate, support=proof
                    ),
                    reason="Evidence-only history regeneration",
                )
            )
    for rule in bundle.model.rules:
        for value in (False, True):
            candidate = Claim(
                id=f"regen/model/{rule.id}",
                kind="implication",
                action=rule.action,
                fact=Fact(entity=rule.action, predicate="applicable", value=value),
                window=bundle.query,
            )
            proof = assess(bundle, candidate)
            if proof.status == "supported":
                generated.append(
                    Decision(
                        origin=candidate.id,
                        operation="keep",
                        output=Grounded(
                            origin=candidate.id, claim=candidate, support=proof
                        ),
                        reason="Same declared action-model information",
                    )
                )
    outputs["regenerate"] = finish(
        bundle,
        "regenerate",
        generated,
        [] if generated else ["No informative evidence"],
    )
    outputs.update(
        proposed=edit(bundle),
        no_temporal=edit(bundle, temporal=False),
        no_action_model=edit(bundle, action_model=False),
    )
    return outputs
