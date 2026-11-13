"""Conservative public text and declared simulator observation projections."""

from __future__ import annotations

import hashlib
import json
import re

import numpy as np
from pydantic import Field

from dual_rec.contracts.checks import Evidence

from .schemas import (
    ActionModel,
    ActionRule,
    Claim,
    Fact,
    Predicate,
    Record,
    RepairInput,
    Window,
)


class PublicRecord(Evidence):
    task_id: str
    plan_until_failure: list[str]
    action: str
    observation: list[str]
    explanation: str
    label: str
    L_plan_exp: str
    L_obs_exp: str
    comment: str | None = None


class Extraction(Evidence):
    claims: list[Claim] = Field(default_factory=list)
    unparsed: list[str] = Field(default_factory=list)
    spans: int = 0
    covered_spans: int = 0


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().rstrip("."))


def entity(text: str) -> str:
    return re.sub(r"^(?:the|an|a) ", "", normalize(text))


def noun_phrase(text: str) -> bool:
    # Longer or clausal arguments are explicitly unsupported, never truncated.
    return re.fullmatch(r"[a-z0-9]+(?:[ -][a-z0-9]+){0,5}", entity(text)) is not None


STATES = {
    "open": ("open", True),
    "closed": ("open", False),
    "turned on": ("powered", True),
    "turned off": ("powered", False),
    "clean": ("clean", True),
    "dirty": ("clean", False),
    "empty": ("empty", True),
    "filled with water": ("filled_with_water", True),
    "sliced": ("sliced", True),
    "not sliced": ("sliced", False),
    "cracked": ("cracked", True),
    "not cracked": ("cracked", False),
    "grasped": ("grasped", True),
    "not grasped": ("grasped", False),
    "near goal": ("near_goal", True),
    "not near goal": ("near_goal", False),
    "contact": ("contact", True),
    "not contact": ("contact", False),
    "failed": ("failed", True),
    "not failed": ("failed", False),
}


def parse_facts(sentence: str) -> list[Fact]:
    """A whole-span whitelist, not an unrestricted semantic or causal parser."""
    text = normalize(sentence)
    if re.search(
        r"\b(because|if|might|maybe|could|would|caused|therefore|unless)\b", text
    ):
        return []
    parenthetical = re.fullmatch(r"(.+?) \(([^()]+)\)", text)
    if parenthetical:
        subject, properties = parenthetical.groups()
        slots = properties.split(" and ")
        if noun_phrase(subject) and all(p in STATES for p in slots):
            return [
                Fact(entity=entity(subject), predicate=STATES[p][0], value=STATES[p][1])
                for p in slots
            ]
        return []
    if re.search(
        r"\b(and|but|while|during|before|after|already|never|cannot|can|should|trying|doing|that|which|due|result|beginning|with)\b",
        text,
    ):
        return []
    relation = re.fullmatch(
        r"(.+?) is (on top of|inside|below|on the left of|on the right of) (.+)", text
    )
    if relation:
        subject, predicate, target = relation.groups()
        if not noun_phrase(subject) or not noun_phrase(target):
            return []
        # Occupancy is an observed categorical slot, not a command effect or alias.
        if predicate == "inside" and target == "robot gripper":
            return [
                Fact(
                    entity="robot gripper", predicate="occupant", value=entity(subject)
                )
            ]
        return [
            Fact(
                entity=entity(subject),
                predicate={
                    "on top of": "on_top",
                    "inside": "inside",
                    "below": "below",
                    "on the left of": "left_of",
                    "on the right of": "right_of",
                }[predicate],
                value=entity(target),
            )
        ]
    simple = re.fullmatch(r"(.+?) is (.+)", text)
    if simple and noun_phrase(simple[1]) and simple[2] in STATES:
        predicate, value = STATES[simple[2]]
        return [Fact(entity=entity(simple[1]), predicate=predicate, value=value)]
    return []


def extract(text: str, window: Window) -> Extraction:
    # No maximum sentence count; the editor later handles bounded groups.
    spans = [s.strip() for s in re.split(r"[.;](?:\s+|$)|\n+", text) if s.strip()]
    claims, unparsed, covered = [], [], 0
    for i, sentence in enumerate(spans):
        facts = parse_facts(sentence)
        if facts:
            covered += 1
            claims.extend(
                Claim(id=f"text/{i}/{j}", kind="observation", fact=f, window=window)
                for j, f in enumerate(facts)
            )
        else:
            unparsed.append(sentence)
    return Extraction(
        claims=claims, unparsed=unparsed, spans=len(spans), covered_spans=covered
    )


def public_bundle(row: PublicRecord, dataset: str) -> tuple[RepairInput, Extraction]:
    snapshot = Window(clock="snapshot", start=0, end=0)
    records = []
    for i, sentence in enumerate(row.observation):
        for j, fact in enumerate(parse_facts(sentence)):
            records.append(
                Record(
                    id=f"obs/{i}/{j}",
                    fact=fact,
                    window=snapshot,
                    source=f"{dataset}/{row.task_id}/observation/{i}",
                )
            )
    for i, action in enumerate(row.plan_until_failure):
        records.append(
            Record(
                id=f"command/{i}",
                fact=Fact(entity="robot", predicate="command", value=normalize(action)),
                window=Window(clock="plan_index", start=i, end=i),
                source=f"{dataset}/{row.task_id}/plan/{i}",
                kind="command",
                action=normalize(action),
            )
        )
    extraction = extract(row.explanation, snapshot)
    return RepairInput(
        id=f"{dataset}/{row.task_id}",
        records=records,
        claims=extraction.claims,
        original_text=row.explanation,
        unparsed=extraction.unparsed,
        query=snapshot,
    ), extraction


def public_groups(rows: list[tuple[str, PublicRecord]]) -> list[str]:
    """Conservative union of episode aliases, CF families and exact input aliases."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, (dataset, row) in enumerate(rows):
        if dataset == "RoboFail":
            key = "episode/" + re.split(r"_(?:gt|pred)_", row.task_id)[0]
        else:
            family = re.sub(r"_[ec]$", "", row.task_id.split("autogen_", 1)[-1])
            key = "shared_template/" + family
        signature = hashlib.sha256(
            json.dumps(
                [row.plan_until_failure, row.observation], sort_keys=True
            ).encode()
        ).hexdigest()
        for alias in [key, "input/" + signature]:
            if alias in seen:
                parent[find(i)] = find(seen[alias])
            else:
                seen[alias] = i
    members = {}
    for i, (_, row) in enumerate(rows):
        members.setdefault(find(i), []).append(row.task_id)
    names = {
        k: hashlib.sha256("\n".join(sorted(v)).encode()).hexdigest()[:16]
        for k, v in members.items()
    }
    return [names[find(i)] for i in range(len(rows))]


def projected_facts(state: dict, task: str) -> list[Fact]:
    if task == "Lift":
        return [
            Fact(entity="cube", predicate="grasped", value=bool(state["is_grasped"]))
        ]
    extra = state["observation"]["extra"]
    facts = []
    if task == "PickCube-v1":
        facts.append(
            Fact(entity="cube", predicate="grasped", value=bool(extra["is_grasped"][0]))
        )
    object_position = np.asarray(extra["obj_pose"], float).reshape(-1)[:3]
    goal_position = np.asarray(extra["goal_pos"], float).reshape(-1)[:3]
    facts.extend(
        [
            Fact(
                entity="cube",
                predicate="near_goal",
                value=bool(np.linalg.norm(object_position - goal_position) <= 0.03),
            ),
            Fact(
                entity="robot",
                predicate="contact",
                value=bool(state["robot_object_contact"]),
            ),
        ]
    )
    return facts


def trace_bundle(raw: dict, task: str, identifier: str) -> RepairInput:
    trace = raw["traces"]["continue/reference"]
    records = []
    for tag, state in [
        ("first", trace["prefix_history"][0]),
        ("checkpoint", trace["start"]),
    ]:
        for fact in projected_facts(state, task):
            records.append(
                Record(
                    id=f"{tag}/{fact.entity}/{fact.predicate}",
                    fact=fact,
                    window=Window(start=state["time"], end=state["time"]),
                    source=f"{identifier}/{tag}/observation"
                    if task != "Lift"
                    else f"{identifier}/{tag}/privileged-preservation-control",
                )
            )
    query = Window(start=trace["start"]["time"], end=trace["start"]["time"])
    transport = "transport"
    model = ActionModel(
        rules=[
            ActionRule(
                id="transport-requires-grasp"
                if task != "PushCube-v1"
                else "push-requires-contact",
                action=transport,
                preconditions=[Fact(entity="cube", predicate="grasped", value=True)]
                if task != "PushCube-v1"
                else [Fact(entity="robot", predicate="contact", value=True)],
                may_change=[
                    Predicate(entity=f.entity, predicate=f.predicate)
                    for f in projected_facts(trace["start"], task)
                ],
            )
        ]
    )
    if query.start > records[0].window.end:
        records.append(
            Record(
                id="prefix/commands",
                fact=Fact(entity="robot", predicate="command", value=transport),
                window=Window(start=records[0].window.end, end=query.end),
                source=f"{identifier}/actual-prefix-action-tape",
                kind="command",
                action=transport,
            )
        )
    claims = [
        Claim(id=f"generated/{i}", kind="observation", fact=r.fact, window=query)
        for i, r in enumerate(records)
        if r.id.startswith("checkpoint/")
    ]
    from .core import render_claim

    text = " ".join(render_claim(c, query) for c in claims)
    return RepairInput(
        id=identifier,
        records=records,
        model=model,
        claims=claims,
        original_text=text,
        query=query,
    )


def select_action(task: str, bundle: RepairInput, explanation=None) -> str:
    """Frozen observational selector; all conditions have the full same history."""
    if task == "Lift":
        return "continue"
    wanted = ("cube", "grasped") if task == "PickCube-v1" else ("robot", "contact")
    visible = [
        r.fact.value
        for r in bundle.records
        if r.kind == "observation"
        and r.visibility == "visible"
        and r.window == bundle.query
        and r.fact.key() == wanted
    ]
    if len(set(visible)) == 1 and all(isinstance(v, bool) for v in visible):
        return "continue" if visible[0] is True else "recover"
    # Explanations do not create a sensor measurement when the shared evidence is
    # absent or conflicting. They cannot license a new control or an unsafe guess.
    return "abstain"
