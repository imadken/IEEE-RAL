"""Restore pinned public inputs and frozen plans without searching or experiments.

Install nothing and leave publication policy/.gitignore untouched. LOGIV's small
reference cache must already be restored with monitoring_fetch_reference.py.
Generated tasks, states and preparation evidence belong in a local ignored run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
from dual_rec.monitoring.benchmarks import _model, _normalized_state
from dual_rec.monitoring.semantics import Action, Model, apply_action
from dual_rec.monitoring.upstream import (
    PINNED_COMMIT,
    as_action,
    as_lit,
    ground_actions,
    load_public_task,
    load_upstream,
)
from dual_rec.revalidation.contracts import Parameters

SOURCE_REPOSITORY = "https://github.com/potassco/pddl-instances"
SOURCE_REVISION = "cf19edf7c53d1540ddbb396c642595e0926ee552"
MAX_SOURCE_BYTES = 100_000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_source(name: str) -> Path:
    path = Path(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError("Source paths must stay relative to the public repository")
    return path


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    parent_id: str
    family: str
    split: Literal["development", "qualification"]
    paths: dict[str, str]
    sha256: dict[str, str]
    plan: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self):
        if set(self.paths) != {"domain", "problem"} or set(self.sha256) != set(
            self.paths
        ):
            raise ValueError("Each input requires domain/problem paths and hashes")
        for name in self.paths:
            relative_source(self.paths[name])
            value = self.sha256[name]
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("Invalid source SHA-256")
        return self


class StudyInput(BaseModel):
    """Ignore documentary metadata; only these frozen inputs affect restoration."""

    model_config = ConfigDict(extra="ignore", frozen=True)
    schema_version: Literal[1]
    run_id: str
    reviewed_base: str
    source_repository: Literal["https://github.com/potassco/pddl-instances"]
    source_revision: Literal["cf19edf7c53d1540ddbb396c642595e0926ee552"]
    logiv_revision: Literal["0ea7a7ff765016a33409c54572d733bed4503d4d"]
    parameters: Parameters
    primary_baseline: Literal["B2", "B3", "B4", "B5"]
    input_tasks: tuple[TaskInput, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_parents(self):
        if len({task.parent_id for task in self.input_tasks}) != len(self.input_tasks):
            raise ValueError("Duplicate public parent identifier")
        return self


def _fetch_source(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read(MAX_SOURCE_BYTES + 1)


def _source(
    root: Path, relative: Path, expected: str, caches: list[Path]
) -> tuple[Path, dict]:
    target = root / "public-pddl" / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Source cache escapes the local run")
    candidates = [target]
    for cache in caches:
        candidates.extend(
            (
                cache / relative,
                cache / "public-pddl" / relative,
                cache / "benchmarks/public-pddl" / relative,
            )
        )
    present = next((p for p in candidates if p.is_file()), None)
    url = f"https://raw.githubusercontent.com/potassco/pddl-instances/{SOURCE_REVISION}/{relative.as_posix()}"
    if present is not None and present.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError(f"Source size exceeds bound: {relative}")
    data = present.read_bytes() if present is not None else _fetch_source(url)
    actual = hashlib.sha256(data).hexdigest()
    if len(data) > MAX_SOURCE_BYTES or actual != expected:
        raise ValueError(f"Source SHA-256/size mismatch: {relative}")
    data.decode("utf-8")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return target, {
        "path": relative.as_posix(),
        "url": url,
        "sha256": actual,
        "bytes": len(data),
        "source_used": str(present) if present else "public_https_fetch",
    }


def semantic_fingerprint(record: dict) -> str:
    """Hash mathematical inputs while ignoring set iteration and source paths."""
    model = Model.model_validate(record["model"])

    def action(value):
        item = Action.model_validate(value)
        return {
            "name": item.name,
            "pre": sorted((lit.atom, lit.positive) for lit in item.pre),
            "add": sorted(item.add),
            "delete": sorted(item.delete),
        }

    payload = {
        "model": {
            "atoms": sorted(model.atoms),
            "constraints": sorted(
                tuple(sorted((lit.atom, lit.positive) for lit in clause))
                for clause in model.constraints
            ),
        },
        "initial": sorted(record["initial"]),
        "goal": sorted(
            (lit["atom"], lit.get("positive", True)) for lit in record["goal"]
        ),
        "actions": sorted(
            (action(a) for a in record["actions"]), key=lambda a: a["name"]
        ),
        "plan": [action(a) for a in record["plan"]],
        "nominal_states": [sorted(state) for state in record["nominal_states"]],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _repository_inventory() -> tuple[dict, list[dict]]:
    commands, inventory = [], {}
    try:
        for argv in (["git", "rev-parse", "HEAD"], ["git", "ls-files", "-z"]):
            result = subprocess.run(
                argv, cwd=REPOSITORY, capture_output=True, check=False
            )
            commands.append({"command": argv, "exit_status": result.returncode})
            if not result.returncode and argv[1] == "ls-files":
                for name in result.stdout.decode().split("\0"):
                    path = REPOSITORY / name
                    if name and path.is_file():
                        inventory[str(path)] = digest(path)
    except FileNotFoundError:
        commands.append(
            {
                "command": ["git"],
                "exit_status": None,
                "reason": "Git unavailable; source-archive restoration",
            }
        )
    return inventory, commands


def restore_inputs(
    config: Path, root: Path, source_root: Path | list[Path] | None = None
) -> dict:
    """Materialize only pinned inputs; never overwrite an existing run or search."""
    config, root = Path(config), Path(root)
    for name in (
        "completion_manifest.json",
        "tasks.json",
        "selection.json",
        "initial.json",
        "preparation_status.json",
    ):
        if (root / name).exists():
            raise FileExistsError(f"Preserve existing run: {root / name}")
    settings = StudyInput.model_validate_json(config.read_text())
    if settings.logiv_revision != PINNED_COMMIT:
        raise ValueError("Unexpected LOGIV revision")
    try:
        load_upstream()
    except FileNotFoundError as error:
        raise RuntimeError(
            "Restore LOGIV first with scripts/monitoring_fetch_reference.py and the pinned monitoring logiv_source.json manifest"
        ) from error
    started = time.time()
    before_cpu = time.process_time()
    inventory, commands = _repository_inventory()
    caches = (
        []
        if source_root is None
        else [Path(source_root)]
        if isinstance(source_root, (str, Path))
        else [Path(p) for p in source_root]
    )
    root.mkdir(parents=True, exist_ok=True)
    sources, tasks, status = {}, [], []
    try:
        for entry in settings.input_tasks:
            paths = {}
            for kind in ("domain", "problem"):
                relative = relative_source(entry.paths[kind])
                path, metadata = _source(root, relative, entry.sha256[kind], caches)
                previous = sources.setdefault(relative.as_posix(), metadata)
                if previous["sha256"] != metadata["sha256"]:
                    raise ValueError("Conflicting hashes for one public source path")
                paths[kind] = path
            task = load_public_task(paths["domain"], paths["problem"])
            rejected = []
            operators = ground_actions(task, skip_invalid=True, rejected=rejected)
            allowed = {action.signature: action for action in operators}
            signatures = tuple(
                tuple(step.strip().strip("()").lower().split()) for step in entry.plan
            )
            if any(signature not in allowed for signature in signatures):
                raise ValueError(
                    f"Frozen plan uses an unsupported grounding: {entry.parent_id}"
                )
            plan = tuple(allowed[signature] for signature in signatures)
            model = _model(task, operators)
            native = task.initial_state
            own = _normalized_state(native, model)
            states = [sorted(own)]
            for index, action in enumerate(plan):
                if not native.holds(action.preconditions):
                    raise ValueError(
                        f"Frozen plan precondition fails: {entry.parent_id} step {index}"
                    )
                native = action.apply(native)
                own = apply_action(as_action(action), own)
                if own != _normalized_state(native, model):
                    raise ValueError(
                        f"Transition implementations disagree: {entry.parent_id} step {index}"
                    )
                states.append(sorted(own))
            if not native.holds(task.goal):
                raise ValueError(
                    f"Frozen plan misses its public goal: {entry.parent_id}"
                )
            record = {
                "task_id": entry.parent_id,
                "family": entry.family,
                "split": entry.split,
                "source_files": {kind: str(path) for kind, path in paths.items()},
                "source_hashes": entry.sha256,
                "model": model.model_dump(mode="json"),
                "dynamic_atoms": sorted(" ".join(atom) for atom in task.dynamic_atoms),
                "initial": states[0],
                "goal": [
                    as_lit(lit).model_dump(mode="json") for lit in sorted(task.goal)
                ],
                "actions": [
                    as_action(action).model_dump(mode="json") for action in operators
                ],
                "plan": [as_action(action).model_dump(mode="json") for action in plan],
                "plan_signatures": signatures,
                "nominal_states": states,
                "excluded_groundings": rejected,
                "transition_validation": "Frozen plan; native/independent equality at every step and public goal",
            }
            tasks.append(record)
            status.append(
                {
                    "parent_id": entry.parent_id,
                    "status": "PASS",
                    "plan_actions": len(plan),
                    "semantic_sha256": semantic_fingerprint(record),
                }
            )
    except Exception as error:
        (root / "preparation_status.json").write_text(
            json.dumps(
                {"status": "FAILED", "error": repr(error), "completed_tasks": status},
                indent=2,
            )
        )
        raise
    selection = {
        "parameters": settings.parameters.model_dump(mode="json"),
        "primary_baseline": settings.primary_baseline,
        "selection_split": "development",
        "restored_from_config_sha256": digest(config),
        "source_config": str(config),
    }
    outputs = {
        "tasks.json": tasks,
        "selection.json": selection,
        "source_manifest.json": {
            "repository": SOURCE_REPOSITORY,
            "revision": SOURCE_REVISION,
            "files": list(sources.values()),
        },
        "initial.json": {
            "started_epoch": started,
            "started_utc": datetime.fromtimestamp(started, UTC).isoformat(),
            "base": settings.reviewed_base,
            "run_id": settings.run_id,
            "prior_sha256": inventory,
            "inventory_scope": "Existing tracked repository files; no old ignored raw files required for input restoration",
            "git_read_commands": commands,
            "caps": {
                "wall_seconds": 21600,
                "cpu_seconds": 28800,
                "artifact_bytes": 4000000000,
            },
        },
    }
    for name, value in outputs.items():
        with (root / name).open("x") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
    result = {
        "status": "INPUTS_RESTORED_NO_EXPERIMENTS",
        "tasks": len(tasks),
        "development_parents": sum(task["split"] == "development" for task in tasks),
        "qualification_parents": sum(
            task["split"] == "qualification" for task in tasks
        ),
        "source_files": len(sources),
        "config_sha256": digest(config),
        "task_semantic_sha256": {
            item["parent_id"]: item["semantic_sha256"] for item in status
        },
        "validation": status,
        "worker_cpu_seconds": time.process_time() - before_cpu,
        "wall_seconds": time.time() - started,
        "no_plan_search": True,
        "no_experiments": True,
    }
    with (root / "preparation_status.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/evidence_revalidation_20261111.json"),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        action="append",
        type=Path,
        help="Optional read-only public-source cache; repeat for multiple roots",
    )
    args = parser.parse_args()
    restored = restore_inputs(args.config, args.root, args.source_root)
    print(
        json.dumps(
            {
                key: value
                for key, value in restored.items()
                if key not in {"validation", "task_semantic_sha256"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
