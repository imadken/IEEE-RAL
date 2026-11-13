"""Literal supplied-prefix reasoning; never a model of physical action effects."""

import json

from .schemas import Claim, Fact, Support, Window


def commands(bundle):
    return sorted(
        [
            r
            for r in bundle.records
            if r.kind == "command" and r.window.clock == "plan_index"
        ],
        key=lambda r: r.window.start,
    )


def sequence_claim(bundle):
    records = commands(bundle)
    return Claim(
        id="regen/command-prefix",
        kind="implication",
        action="command_log",
        fact=Fact(
            entity="command_log",
            predicate="sequence",
            value=json.dumps([r.action for r in records]),
        ),
        window=Window(clock="plan_index", start=0, end=max(0, len(records) - 1)),
    )


def assess_log(bundle, claim, temporal, action_model):
    if not action_model or not bundle.model.command_log:
        return Support(
            status="unknown",
            reason="Literal command-log reasoning disabled or undeclared",
        )
    records = commands(bundle)
    if claim.window != sequence_claim(bundle).window:
        return Support(
            status="unknown",
            reason="Claim does not describe the complete supplied prefix",
        )
    actions = [r.action for r in records]
    fact = claim.fact
    expected = None
    try:
        if fact.predicate == "sequence":
            expected = json.loads(fact.value) == actions if temporal else None
        elif fact.predicate == "order" and temporal:
            pair = json.loads(fact.value)
            if (
                len(pair) == 2
                and all(actions.count(a) == 1 for a in pair)
                and pair[0] != pair[1]
            ):
                expected = actions.index(pair[0]) < actions.index(pair[1])
        elif fact.predicate in ("listed", "missing"):
            expected = (fact.value in actions) == (fact.predicate == "listed")
    except (ValueError, TypeError):
        pass
    if expected is None:
        return Support(
            status="unknown",
            reason="Ambiguous occurrences, time disabled, or unrecognized prefix query",
        )
    return Support(
        status="supported" if expected else "contradicted",
        basis="model_deduction",
        evidence=[r.id for r in records],
        rules=["literal-command-log"],
        reason="Literal supplied command prefix only; no physical effects, global-plan completeness or cause implied",
    )


def render_log(claim):
    fact = claim.fact
    if fact.predicate == "sequence":
        return (
            "Complete supplied command prefix: "
            + " -> ".join(json.loads(fact.value))
            + ". Effects are not implied."
        )
    if fact.predicate == "order":
        first, second = json.loads(fact.value)
        return f"The supplied command prefix lists '{first}' before '{second}'; effects are not implied."
    return f"The supplied command prefix {'does not list' if fact.predicate == 'missing' else 'lists'} '{fact.value}'; global plan completeness is unknown."
