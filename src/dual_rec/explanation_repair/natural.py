"""Bounded public-language adapter, retaining residue and uncertain time anchors.

This is an inspectable template adapter, not a semantic gold-label generator.
"""

from __future__ import annotations

import json
import re

from pydantic import Field

from dual_rec.contracts.checks import Evidence

from .adapters import PublicRecord, entity, normalize, parse_facts, public_bundle
from .schemas import ActionModel, Claim, Fact, Window


class Clause(Evidence):
    text: str
    claim_ids: list[str] = Field(default_factory=list)
    recognized: bool
    form: str
    note: str


class LanguageExtraction(Evidence):
    clauses: list[Clause]
    complete: bool
    partial: bool
    recognized_clauses: int
    factual_claims: int
    hypotheses: int


def canonical_action(text: str) -> str:
    text = normalize(text).replace("_", " ")
    text = re.sub(r"[(),]", " ", text)
    text = re.sub(r"\bturn(?:ed)? (on|off)\b", r"toggle \1", text)
    return re.sub(r"\s+", " ", text).strip(" -:)")


def grounded_fact(fact: Fact, records) -> bool:
    """Require observed argument identities; no cup/mug or inferred object aliases."""
    names = {r.fact.entity for r in records if r.kind == "observation"}
    names.update(
        entity(r.fact.value)
        for r in records
        if r.kind == "observation" and isinstance(r.fact.value, str)
    )
    return fact.entity in names and (
        isinstance(fact.value, bool) or entity(fact.value) in names
    )


def language_bundle(row: PublicRecord, dataset: str):
    bundle, _ = public_bundle(row, dataset)
    records = [
        r.model_copy(
            update={
                "action": canonical_action(r.action),
                "fact": r.fact.model_copy(update={"value": canonical_action(r.action)}),
            }
        )
        if r.kind == "command"
        else r
        for r in bundle.records
    ]
    actions = list(dict.fromkeys(r.action for r in records if r.kind == "command"))
    prefix_window = Window(
        clock="plan_index", start=0, end=max(0, len(row.plan_until_failure) - 1)
    )
    unknown = Window(clock="unknown", start=0, end=0)
    # Each original span is retained verbatim; no silently discarded suffix.
    spans = [
        s.strip()
        for s in re.split(r"[.;](?:\s+|$)|\n+|\s+and\s+|\s+but\s+", row.explanation)
        if s.strip()
    ]
    claims, clauses, residue = [], [], []
    for i, raw in enumerate(spans):
        text = normalize(raw)
        identifier = f"language/{i}"
        historical = bool(
            re.search(r"\b(was|were|earlier|beginning|previously|initially)\b", text)
        )
        candidate = re.sub(
            r"^(?:the )?robot fails? (?:because|since) (?:it )?", "", text
        )
        candidate = re.sub(r"^wrong plan\s*[-:]\s*", "", candidate)
        canonical = canonical_action(candidate)
        found = []
        form = "unparsed"
        note = "No complete grounded clause template; residue retained"
        relation = re.search(r"\b(before|after)\b", canonical)
        if (
            relation
            and not historical
            and not re.search(r"\b(not|never|if|might|could|should|would)\b", canonical)
        ):
            left, right = canonical[: relation.start()], canonical[relation.end() :]
            first = [a for a in actions if a in left]
            second = [a for a in actions if a in right]
            # Exact matching is conservative; nested or repeated matches abstain.
            if len(first) == len(second) == 1 and first != second:
                pair = [first[0], second[0]]
                if relation[1] == "after":
                    pair.reverse()
                found = [
                    Claim(
                        id=identifier,
                        kind="implication",
                        action="command_log",
                        fact=Fact(
                            entity="command_log",
                            predicate="order",
                            value=json.dumps(pair),
                        ),
                        window=prefix_window,
                    )
                ]
                form = "literal_command_order"
                note = "Only the recorded order subclaim is parsed; physical cause is unresolved"
                # Extra words outside command names/template markers are residue.
                remainder = (
                    left.replace(first[0], "") + " " + right.replace(second[0], "")
                )
                remainder = re.sub(
                    r"\b(doing|do|it|the|robot|executing|execute|trying|to|did|not)\b|[-:()]",
                    " ",
                    remainder,
                )
                complete_order = not remainder.strip()
                if not complete_order:
                    residue.append(raw)
        if not found:
            literal = re.sub(r"\b(?:was|were)\b", "is", candidate)
            facts = [f for f in parse_facts(literal) if grounded_fact(f, records)]
            if facts:
                found = [
                    Claim(
                        id=f"{identifier}/{j}",
                        kind="observation",
                        fact=f,
                        window=unknown if historical else bundle.query,
                    )
                    for j, f in enumerate(facts)
                ]
                form = "historical_unanchored" if historical else "literal_observation"
                note = (
                    "Historical time is unobserved"
                    if historical
                    else "Arguments grounded to supplied observation vocabulary; truth not assumed"
                )
            elif re.fullmatch(
                r"(?:wrong perception\s*[-:]?.+|.+(?:was |is |being )?(?:dropped|blocking|blocked).+|(?:failed to|robot failed|the robot failed|missing step|missing action|robot mis.identified).+)",
                text,
            ):
                # These recognizable failure/cause forms are hypotheses, not facts.
                found = [
                    Claim(
                        id=identifier,
                        kind="hypothesis",
                        window=unknown if historical else bundle.query,
                    )
                ]
                form = "unestablished_failure_hypothesis"
                note = "Recognized failure/cause syntax only; no physical event or unique cause established"
        if (
            found
            and candidate != text
            and text.startswith(("robot fail", "the robot fail"))
        ):
            found.append(
                Claim(id=identifier + "/cause", kind="hypothesis", window=bundle.query)
            )
        if not found:
            residue.append(raw)
        claims.extend(found)
        clauses.append(
            Clause(
                text=raw,
                claim_ids=[c.id for c in found],
                recognized=bool(found) and raw not in residue,
                form=form,
                note=note,
            )
        )
    recognized = sum(c.recognized for c in clauses)
    extraction = LanguageExtraction(
        clauses=clauses,
        complete=bool(clauses) and not residue,
        partial=bool(claims) and bool(residue),
        recognized_clauses=recognized,
        factual_claims=sum(c.kind != "hypothesis" for c in claims),
        hypotheses=sum(c.kind == "hypothesis" for c in claims),
    )
    return bundle.model_copy(
        update={
            "records": records,
            "claims": claims,
            "unparsed": residue,
            "model": ActionModel(command_log=True),
        }
    ), extraction
