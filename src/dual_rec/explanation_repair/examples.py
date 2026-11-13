"""Five authored development cases, distinct from empirical trace evaluation."""

from .core import render_claim
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


def worked_cases() -> list[RepairInput]:
    now = Window(start=1, end=1)
    old = Window(start=0, end=0)
    grasp = Fact(entity="cube", predicate="grasped", value=True)
    near = Fact(entity="cube", predicate="near_goal", value=False)
    model = ActionModel(
        rules=[
            ActionRule(
                id="transport-grasp",
                action="transport",
                preconditions=[grasp],
                may_change=[Predicate(entity="cube", predicate="grasped")],
            )
        ]
    )

    def record(name, fact, window=now, **kwargs):
        return Record(
            id=name,
            fact=fact,
            window=window,
            source="authored-development-case",
            **kwargs,
        )

    def claim(name, fact, window=now, **kwargs):
        return Claim(
            id=name,
            fact=fact,
            window=window,
            kind=kwargs.pop("kind", "observation"),
            **kwargs,
        )

    cases = [
        RepairInput(
            id="correct-preserved",
            records=[record("g", grasp)],
            claims=[claim("g", grasp)],
            query=now,
        ),
        RepairInput(
            id="selective-replacement",
            records=[record("g", grasp), record("goal", near)],
            claims=[
                claim("g", grasp.model_copy(update={"value": False})),
                claim("goal", near),
            ],
            query=now,
        ),
        RepairInput(
            id="unknown-battery-cause",
            records=[],
            claims=[
                claim(
                    "battery", Fact(entity="battery", predicate="failed", value=True)
                ),
                Claim(id="cause", kind="hypothesis", window=now),
            ],
            query=now,
        ),
        RepairInput(
            id="command-is-not-effect",
            model=model,
            records=[
                record("observed-ungrasped", grasp.model_copy(update={"value": False})),
                record(
                    "transport-command",
                    Fact(entity="robot", predicate="command", value="transport"),
                    kind="command",
                    action="transport",
                ),
            ],
            claims=[
                claim("g", grasp),
                claim(
                    "blocked",
                    Fact(entity="transport", predicate="applicable", value=False),
                    kind="implication",
                    action="transport",
                ),
            ],
            query=now,
        ),
        RepairInput(
            id="temporal-and-conflicting",
            model=model,
            records=[
                record("old-grasp", grasp, old),
                record("now-ungrasped", grasp.model_copy(update={"value": False})),
                record(
                    "contact-yes", Fact(entity="robot", predicate="contact", value=True)
                ),
                record(
                    "contact-no", Fact(entity="robot", predicate="contact", value=False)
                ),
            ],
            claims=[
                claim("past", grasp, old),
                claim("present", grasp.model_copy(update={"value": False})),
                claim("contact", Fact(entity="robot", predicate="contact", value=True)),
            ],
            query=now,
        ),
    ]
    return [
        b.model_copy(
            update={
                "original_text": " ".join(render_claim(c, b.query) for c in b.claims)
            }
        )
        for b in cases
    ]
