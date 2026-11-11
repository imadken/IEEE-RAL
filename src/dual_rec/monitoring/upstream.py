"""Hash-verified access to the unmodified pinned LOGIV reference source."""

import hashlib
import importlib
import json
import sys
from itertools import product
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from .semantics import Action, Lit, Model

if TYPE_CHECKING:
    from logiv.core.symbolic import Literal, Operator
    from logiv.planning.pddl import Task


REPOSITORY = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY / ".cache/monitoring-upstream"
MANIFEST = REPOSITORY / "results/monitoring-study/20261111T121002Z/logiv_source.json"
PINNED_COMMIT = "0ea7a7ff765016a33409c54572d733bed4503d4d"


def load_upstream(
    source_root: Path = SOURCE_ROOT, manifest: Path = MANIFEST
) -> ModuleType:
    """Verify every cached file's Git blob hash and size before importing LOGIV."""
    metadata = json.loads(manifest.read_text())
    if metadata["commit"] != PINNED_COMMIT:
        raise ValueError("Unexpected LOGIV revision")
    for item in metadata["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid upstream source path")
        content = (source_root / relative).read_bytes()
        header = f"blob {len(content)}\0".encode()
        digest = hashlib.sha1(header + content).hexdigest()
        if len(content) != item["size"] or digest != item["sha"]:
            raise ValueError(f"Upstream source integrity failure: {relative}")
    expected = (source_root / "logiv/__init__.py").resolve()
    existing = sys.modules.get("logiv")
    if existing is not None and Path(existing.__file__).resolve() != expected:
        raise ValueError("Another LOGIV installation is already imported")
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    module = importlib.import_module("logiv")
    if Path(module.__file__).resolve() != expected:
        raise ValueError("Imported LOGIV source differs from verified source")
    return module


def load_public_task(domain: Path, problem: Path) -> "Task":
    """Load supported PDDL with neutral instruction/resource metadata.

    Resource annotations do not exist in generic PDDL examples. Empty resources
    are an explicit experiment-interface adaptation, not upstream benchmark
    execution metadata.
    """
    load_upstream()
    from logiv.planning.pddl import load_task, parse

    schemas = [
        section[1]
        for section in parse(domain.read_text())[2:]
        if section[0] == ":action"
    ]
    return load_task(
        domain,
        problem,
        instructions={name: name for name in schemas},
        resources={name: () for name in schemas},
    )


def as_lit(literal: "Literal") -> Lit:
    return Lit(atom=" ".join(literal.atom), positive=literal.positive)


def as_action(operator: "Operator") -> Action:
    return Action(
        name=" ".join(operator.signature),
        pre=tuple(as_lit(literal) for literal in sorted(operator.preconditions)),
        add=frozenset(" ".join(lit.atom) for lit in operator.effects if lit.positive),
        delete=frozenset(
            " ".join(lit.atom) for lit in operator.effects if not lit.positive
        ),
    )


def ground_actions(
    task: "Task",
    max_actions: int = 50_000,
    *,
    skip_invalid: bool = False,
    rejected: list[dict] | None = None,
) -> tuple["Operator", ...]:
    """Enumerate typed groundings, strict unless exclusion is explicitly opted in.

    The optional common-library adaptation omits only inconsistent grounded
    literals rejected by upstream's Operator. Every omission can be retained in
    ``rejected``. This is not a claim to implement every native PDDL grounding.
    """
    objects = task.constants | task.objects
    actions = []
    attempted = 0
    for name, schema in sorted(task.actions.items()):
        arguments = [
            sorted(
                value for value, actual in objects.items() if task.is_type(actual, kind)
            )
            for kind in schema.parameters.values()
        ]
        for values in product(*arguments):
            attempted += 1
            if attempted > max_actions:
                raise ValueError("Ground action limit exceeded")
            if skip_invalid:
                bindings = dict(zip(schema.parameters, values))
                conditions = [
                    {
                        (
                            tuple(bindings.get(part, part) for part in literal.atom),
                            literal.positive,
                        )
                        for literal in literals
                    }
                    for literals in (schema.preconditions, schema.effects)
                ]
                if any(
                    any((atom, not positive) in literals for atom, positive in literals)
                    for literals in conditions
                ):
                    if rejected is not None:
                        rejected.append(
                            {
                                "signature": [name, *values],
                                "reason": "upstream_rejects_inconsistent_grounded_literals",
                            }
                        )
                    continue
            actions.append(task.ground((name, *values)))
    return tuple(actions)


def as_model(task: "Task", *, skip_invalid: bool = False) -> Model:
    """Declare all grounded variables and fixed static/equality facts.

    Static truth follows the public PDDL initial model and closed-world static
    semantics; dynamic omitted runtime observations remain unknown. This does
    not invent physical mutex constraints absent from the public task model.
    """
    upstream = load_upstream()
    atoms = set(task.dynamic_atoms) | set(task.initial_state.facts)
    atoms.update(literal.atom for literal in task.goal)
    for action in ground_actions(task, skip_invalid=skip_invalid):
        atoms.update(literal.atom for literal in action.preconditions | action.effects)
    fixed = tuple(
        (
            Lit(
                atom=" ".join(atom),
                positive=bool(task.initial_state.truth(upstream.Literal(atom))),
            ),
        )
        for atom in sorted(atoms)
        if atom[0] == "=" or atom[0] in task.static_predicates
    )
    return Model(atoms=frozenset(" ".join(atom) for atom in atoms), constraints=fixed)


def original_smoke() -> dict:
    """Execute actual upstream verifier branches without robot or planner calls."""
    upstream = load_upstream()
    from logiv.core.graph import build_graph
    from logiv.core.verification import Observation, Verifier

    p, q, g = ("p",), ("unrelated",), ("goal",)

    class Runtime:
        def __init__(self, initial, after=None):
            self.initial = initial
            self.after = after if after is not None else initial
            self.current = initial
            self.active_calls = 0
            self.executions = 0

        def observe(self, active=False):
            self.active_calls += int(active)
            return self.current

        def execute(self, action, observation):
            self.executions += 1
            self.current = self.after
            return self.after

    class Perception:
        def assess(self, observation, atoms):
            return {atom: observation.raw.get(atom) for atom in atoms}

    outputs = {}
    cases = {
        "known_true": ({p: True}, {}, frozenset({p}), frozenset(), frozenset({p})),
        "known_false": ({p: False}, {}, frozenset(), frozenset(), frozenset({p})),
        "required_unknown": (
            {p: None},
            {},
            frozenset(),
            frozenset({p}),
            frozenset({p}),
        ),
        "irrelevant_tracked_unknown": (
            {p: True, q: None},
            {},
            frozenset({p}),
            frozenset({q}),
            frozenset({p, q}),
        ),
        "irrelevant_untracked_unknown": (
            {p: True},
            {},
            frozenset({p}),
            frozenset({q}),
            frozenset({p}),
        ),
        "missing_overwrites_known": (
            {},
            {},
            frozenset({p}),
            frozenset(),
            frozenset({p}),
        ),
        "conflicting_sensor_visual": (
            {p: True},
            {p: False},
            frozenset({p}),
            frozenset(),
            frozenset({p}),
        ),
    }
    for name, (visual, feedback, facts, unknown, tracked) in cases.items():
        observation = Observation(raw=visual, feedback=feedback)
        runtime = Runtime(observation)
        verifier = Verifier(runtime, Perception(), tracked_atoms=tracked)
        state, _, resolved = verifier.state_gate(
            upstream.State(facts, unknown),
            frozenset({upstream.Literal(p)}),
            observation,
        )
        outputs[name] = {
            "resolved": resolved,
            "required_truth": state.truth(upstream.Literal(p)),
            "unknown": [" ".join(atom) for atom in sorted(state.unknown)],
            "additional_calls": runtime.active_calls,
            "executions": runtime.executions,
        }
    action = upstream.Operator(
        "achieve",
        (),
        frozenset({upstream.Literal(p)}),
        frozenset({upstream.Literal(g)}),
    )
    initial = upstream.State(frozenset({p}))
    for name, before, after, node in (
        ("precondition_false", {p: False, g: False}, {p: False, g: False}, 0),
        ("effect_unknown", {p: True, g: False}, {p: True, g: None}, 0),
        ("effect_pass", {p: True, g: False}, {p: True, g: True}, 0),
        ("goal_false", {p: True, g: False}, {p: True, g: False}, 1),
        ("goal_pass", {p: True, g: True}, {p: True, g: True}, 1),
    ):
        graph = build_graph(initial, (action,), frozenset({upstream.Literal(g)}))
        runtime = Runtime(Observation(raw=before), Observation(raw=after))
        verifier = Verifier(runtime, Perception(), tracked_atoms=frozenset({p, g}))
        check = verifier.verify_and_execute(node, graph, initial)
        outputs[name] = {
            "status": check.status.value,
            "failure": check.failure.kind.value if check.failure else None,
            "additional_calls": runtime.active_calls,
            "executions": runtime.executions,
            "completed": sorted(graph.completed),
        }
    return outputs
