"""Prepare immutable public PDDL tasks and validated nominal continuations."""

import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

from .semantics import Model, apply_action, regress
from .upstream import (
    PINNED_COMMIT,
    SOURCE_ROOT,
    as_action,
    as_lit,
    ground_actions,
    load_public_task,
    load_upstream,
)

IPC_ROOT = Path("/tmp/monitoring-public-pddl")
IPC_REVISION = "cf19edf7c53d1540ddbb396c642595e0926ee552"
FD_PYTHON = Path("/tmp/monitoring-alfworld/bin/python")
FD_HELPER = Path("/tmp/monitoring_fd_plan.py")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _append(path: Path, value: dict) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")


def _ground_library(task):
    """Use upstream-consistent groundings and expose every rejected signature.

    Public IPC schemas admit degenerate substitutions such as stack(x,x) or
    drive(l,l), whose effects contain both polarities. LOGIV's Operator rejects
    these. The common library is explicitly the accepted subset; no source is
    patched and the omitted groundings are never hidden as full equivalence.
    """
    rejected = []
    operators = ground_actions(task, skip_invalid=True, rejected=rejected)
    return operators, rejected


def _model(task, operators) -> Model:
    upstream = load_upstream()
    atoms = set(task.dynamic_atoms) | set(task.initial_state.facts)
    atoms.update(lit.atom for lit in task.goal)
    for operator in operators:
        atoms.update(lit.atom for lit in operator.preconditions | operator.effects)
    constraints = tuple(
        (
            as_lit(
                upstream.Literal(
                    atom, bool(task.initial_state.truth(upstream.Literal(atom)))
                )
            ),
        )
        for atom in sorted(atoms)
        if atom[0] in task.static_predicates or atom[0] == "="
    )
    return Model(
        atoms=frozenset(" ".join(atom) for atom in atoms), constraints=constraints
    )


def _normalized_state(state, model: Model) -> frozenset[str]:
    """Materialize public static/equality truth for our atom-based evaluator."""
    atoms = {" ".join(atom) for atom in state.facts}
    for clause in model.constraints:
        if len(clause) == 1:
            literal = clause[0]
            if literal.positive:
                atoms.add(literal.atom)
            else:
                atoms.discard(literal.atom)
    return frozenset(atoms)


def _bfs(task, operators, state_limit=20_000, seconds=30):
    started = time.monotonic()
    initial = task.initial_state
    frontier = deque([(initial, ())])
    visited = {initial.facts}
    while frontier:
        if time.monotonic() - started >= seconds:
            raise TimeoutError("BFS planning time limit")
        state, plan = frontier.popleft()
        if state.holds(task.goal):
            return plan, len(visited)
        for operator in operators:
            if not state.holds(operator.preconditions):
                continue
            successor = operator.apply(state)
            if successor.facts in visited:
                continue
            if len(visited) >= state_limit:
                raise ValueError("BFS planning state limit")
            visited.add(successor.facts)
            frontier.append((successor, plan + (operator,)))
    raise ValueError("No plan found in reachable states")


def _plan(task, operators, domain, problem, output_dir, task_id):
    started = time.monotonic()
    utc = datetime.now(UTC).isoformat()
    source = {"domain": _sha(domain), "problem": _sha(problem)}
    if not (FD_PYTHON.is_file() and FD_HELPER.is_file()):
        before = time.process_time()
        row = {"task_id": task_id, "planner": "bounded_bfs", "utc_start": utc}
        try:
            plan, states = _bfs(task, operators)
            row.update(exit_status=0, states=states)
            return plan
        except (ValueError, TimeoutError) as error:
            row.update(exit_status=1, error=str(error))
            raise
        finally:
            row.update(
                wall_seconds=time.monotonic() - started,
                cpu_seconds=time.process_time() - before,
                source_sha256=source,
            )
            _append(output_dir / "planning_commands.jsonl", row)
    result_path = output_dir / "planner" / f"{task_id}.json"
    log_path = output_dir / "planner" / f"{task_id}.log"
    result_path.parent.mkdir(exist_ok=True)
    helper = output_dir / "planner/driver.py"
    if not helper.is_file():
        helper = FD_HELPER
    command = [
        str(FD_PYTHON),
        str(helper),
        str(domain),
        str(problem),
        str(result_path),
    ]
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    reason = None
    with log_path.open("x") as stream:
        process = subprocess.Popen(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=os.environ | {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
        )
        try:
            code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            reason = "timeout"
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    _append(
        output_dir / "planning_commands.jsonl",
        {
            "task_id": task_id,
            "planner": "fast_downward_pddl2sas",
            "command": command,
            "utc_start": utc,
            "utc_end": datetime.now(UTC).isoformat(),
            "exit_status": code,
            "termination_reason": reason,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": after.ru_utime
            + after.ru_stime
            - before.ru_utime
            - before.ru_stime,
            "source_sha256": source | {"planner_helper": _sha(helper)},
            "log_sha256": _sha(log_path),
        },
    )
    if code:
        raise ValueError(f"Planner exited {code}")
    record = json.loads(result_path.read_text())
    if not record["solved"]:
        raise ValueError("Planner reported no solution")
    allowed = {operator.signature: operator for operator in operators}
    signatures = [
        tuple(step.replace("(", "").replace(")", "").split())
        for step in record["steps"]
    ]
    if any(signature not in allowed for signature in signatures):
        raise ValueError("Plan uses a grounding rejected by the pinned upstream model")
    return tuple(allowed[signature] for signature in signatures)


def _consequence(task, state, plan) -> dict[str, float]:
    """Count causal descendants of present-state supports, without future roots."""
    from logiv.core.graph import START, build_graph

    required = regress(
        tuple(as_action(action) for action in plan), tuple(as_lit(g) for g in task.goal)
    )
    if required is None:
        raise ValueError("Validated nominal continuation has impossible regression")
    required_set = set(required)
    graph = build_graph(state, plan, task.goal)
    roots = {}
    for edge in graph.edges:
        if (
            edge.source == START
            and edge.condition is not None
            and as_lit(edge.condition) in required_set
        ):
            roots.setdefault(edge.condition.atom, set()).add(edge.target)
    result = {}
    for atom, reached in roots.items():
        frontier = list(reached)
        while frontier:
            node = frontier.pop()
            for edge in graph.edges:
                if (
                    edge.source == node
                    and edge.condition is not None
                    and edge.target not in reached
                ):
                    reached.add(edge.target)
                    frontier.append(edge.target)
        result[" ".join(atom)] = float(
            1 + len({node for node in reached if 0 <= node < len(plan)})
        )
    # Regression is the semantic obligation. Every such atom receives a defined
    # score even if graph representation details omit a corresponding edge.
    return {literal.atom: result.get(literal.atom, 1.0) for literal in required}


def _copy_source(source: Path, destination: Path, entry: dict, manifest: list) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_bytes()
    if destination.exists() and destination.read_bytes() != content:
        raise ValueError("Existing public source differs")
    destination.write_bytes(content)
    manifest.append(
        entry
        | {"path": str(destination), "sha256": _sha(destination), "bytes": len(content)}
    )
    return destination


def _prepare_one(task_id, family, split, domain, problem, output_dir):
    task = load_public_task(domain, problem)
    operators, rejected = _ground_library(task)
    model = _model(task, operators)
    plan = _plan(task, operators, domain, problem, output_dir, task_id)
    upstream_state = task.initial_state
    own_state = _normalized_state(upstream_state, model)
    states = [sorted(own_state)]
    consequences = []
    for index, operator in enumerate(plan):
        consequences.append(_consequence(task, upstream_state, plan[index:]))
        upstream_state = operator.apply(upstream_state)
        own_state = apply_action(as_action(operator), own_state)
        if own_state != _normalized_state(upstream_state, model):
            raise ValueError("Independent transition conversion mismatch")
        states.append(sorted(own_state))
    if not upstream_state.holds(task.goal):
        raise ValueError("Nominal plan fails the declared public goal")
    consequences.append(_consequence(task, upstream_state, ()))
    return {
        "task_id": task_id,
        "family": family,
        "split": split,
        "source_hashes": {"domain": _sha(domain), "problem": _sha(problem)},
        "source_files": {"domain": str(domain), "problem": str(problem)},
        "model": model.model_dump(mode="json"),
        "dynamic_atoms": sorted(" ".join(atom) for atom in task.dynamic_atoms),
        "initial": states[0],
        "goal": [
            as_lit(literal).model_dump(mode="json") for literal in sorted(task.goal)
        ],
        "actions": [
            as_action(operator).model_dump(mode="json") for operator in operators
        ],
        "plan": [as_action(operator).model_dump(mode="json") for operator in plan],
        "plan_signatures": [operator.signature for operator in plan],
        "nominal_states": states,
        "consequence": consequences,
        "excluded_groundings": rejected,
        "transition_validation": "own_apply_equals_upstream_at_every_step_and_goal_holds",
    }


def prepare_tasks(output_dir: Path) -> list[dict]:
    """Prepare every locked canonical instance; preserve and report all failures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "prepared_tasks.json").exists():
        raise FileExistsError("Prepared task evidence already exists")
    source_manifest = json.loads((IPC_ROOT / "source_manifest.json").read_text())
    if source_manifest["revision"] != IPC_REVISION:
        raise ValueError("Unexpected IPC source revision")
    for entry in source_manifest["files"]:
        content = (IPC_ROOT / entry["path"]).read_bytes()
        header = f"blob {len(content)}\0".encode()
        if (
            hashlib.sha256(content).hexdigest() != entry["sha256"]
            or hashlib.sha1(header + content).hexdigest() != entry["git_blob_sha1"]
            or len(content) != entry["bytes"]
        ):
            raise ValueError(f"IPC source integrity failure: {entry['path']}")
    _write_json(output_dir / "ipc_source_verification.json", source_manifest)
    if FD_HELPER.is_file():
        (output_dir / "planner").mkdir(exist_ok=True)
        (output_dir / "planner/driver.py").write_bytes(FD_HELPER.read_bytes())
    tasks, manifest = [], []
    specifications = []
    for family in ("blocks-strips-typed", "logistics-strips-typed"):
        directory = IPC_ROOT / "ipc-2000/domains" / family
        domain = _copy_source(
            directory / "domain.pddl",
            output_dir / "public-pddl" / "ipc-2000/domains" / family / "domain.pddl",
            {
                "repository": "https://github.com/potassco/pddl-instances",
                "revision": IPC_REVISION,
            },
            manifest,
        )
        for number in range(1, 13):
            problem = _copy_source(
                directory / "instances" / f"instance-{number}.pddl",
                domain.parent / "instances" / f"instance-{number}.pddl",
                {
                    "repository": "https://github.com/potassco/pddl-instances",
                    "revision": IPC_REVISION,
                },
                manifest,
            )
            specifications.append(
                (
                    f"{family}-{number:02d}",
                    family,
                    "development" if number <= 4 else "qualification",
                    domain,
                    problem,
                )
            )
    for family in ("robotwin/move_can_pot", "bicoord/build_bridge"):
        source = SOURCE_ROOT / "logiv/pddl" / family
        destination = output_dir / "public-pddl/logiv" / family
        paths = [
            _copy_source(
                source / filename,
                destination / filename,
                {
                    "repository": "https://github.com/Enqiao-Lu/LOGIV",
                    "revision": PINNED_COMMIT,
                },
                manifest,
            )
            for filename in ("domain.pddl", "problem.pddl")
        ]
        specifications.append((family.replace("/", "-"), family, "smoke", *paths))
    _write_json(output_dir / "public_pddl_manifest.json", manifest)
    for task_id, family, split, domain, problem in specifications:
        started = time.monotonic()
        try:
            record = _prepare_one(task_id, family, split, domain, problem, output_dir)
            tasks.append(record)
            status = {
                "status": "prepared",
                "actions": len(record["actions"]),
                "plan_length": len(record["plan"]),
                "excluded_groundings": len(record["excluded_groundings"]),
            }
        except (ValueError, KeyError, OSError, TimeoutError) as error:
            status = {
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
            }
        _append(
            output_dir / "task_preparation.jsonl",
            {
                "task_id": task_id,
                "family": family,
                "split": split,
                "wall_seconds": time.monotonic() - started,
                **status,
            },
        )
    _write_json(output_dir / "prepared_tasks.json", tasks)
    return tasks


def refresh_consequence_metadata(output_dir: Path) -> None:
    """Retain pre-comparison metadata and correct only the declared score formula."""
    path = output_dir / "prepared_tasks.json"
    archived = output_dir / "prepared_tasks.pre_consequence_correction.json"
    if archived.exists():
        raise FileExistsError("Original consequence metadata already archived")
    original = path.read_bytes()
    archived.write_bytes(original)
    tasks = json.loads(original)
    changes = []
    for record in tasks:
        source = record["source_files"]
        task = load_public_task(Path(source["domain"]), Path(source["problem"]))
        plan = tuple(
            task.ground(tuple(signature)) for signature in record["plan_signatures"]
        )
        state = task.initial_state
        scores = []
        for checkpoint in range(len(plan) + 1):
            scores.append(_consequence(task, state, plan[checkpoint:]))
            if checkpoint < len(plan):
                state = plan[checkpoint].apply(state)
        changes.append(
            {"task_id": record["task_id"], "changed": record["consequence"] != scores}
        )
        record["consequence"] = scores
    old_tasks = json.loads(original)
    assert [
        {k: v for k, v in row.items() if k != "consequence"} for row in old_tasks
    ] == [{k: v for k, v in row.items() if k != "consequence"} for row in tasks]
    _write_json(path, tasks)
    _append(
        output_dir / "engineering_corrections.jsonl",
        {
            "utc": datetime.now(UTC).isoformat(),
            "reason": "Use protocol weight 1 + count of remaining ACTION descendants; goal-only weight 1; match signed regressed obligations",
            "stage": "source_preparation_before_any_method_comparison",
            "original_sha256": hashlib.sha256(original).hexdigest(),
            "corrected_sha256": _sha(path),
            "plans_sources_states_and_task_membership_unchanged": True,
            "tasks": changes,
        },
    )
