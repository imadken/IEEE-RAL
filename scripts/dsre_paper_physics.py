"""Bounded prospective paired outcomes using frozen CPU skills and full-prefix resets."""

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal

from overnight_pick import initial
from overnight_replay import World as BaseWorld
from overnight_replay import prefix_to_stage
from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence
from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.repair_selection import optional_values
from dual_rec.overnight_pick import PickFault, PickFrame, pick_recovery, sensors
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes


class Cell(Evidence):
    task: Literal["PickCube-v1", "PushCube-v1"]
    seed: int = Field(ge=0)
    condition: Literal["nominal", "offset002", "misaligned"]

    @model_validator(mode="after")
    def registered(self):
        if self.condition not in (
            {"nominal", "offset002"}
            if self.task == "PickCube-v1"
            else {"nominal", "misaligned"}
        ):
            raise ValueError("Condition is not registered for task")
        return self


def sha(value):
    return hashlib.sha256(
        json.dumps(jsonable(value), sort_keys=True).encode()
    ).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(jsonable(value), indent=2, allow_nan=False) + "\n")


class World(BaseWorld):
    """No controller/physics changes; only counts already registered control steps."""

    controls = 0

    def step(self, action):
        type(self).controls += 1
        return super().step(action)


def action_for(world, mode, j, initial_tcp):
    if world.task == "PickCube-v1":
        state = world.state()
        frame = PickFrame(
            step=j,
            action=[0] * 4,
            sensors=sensors(world.env, world.cube, world.obs, state),
        )
        return pick_recovery(
            frame, "nominal" if mode == "continue" else "regrasp", j, initial_tcp
        )
    return world.continuation(
        "nominal" if mode == "continue" else "alternative", j, initial_tcp
    )


def run_cell(cell, root, deadline):
    started = time.monotonic()
    condition = "misaligned" if cell.condition == "misaligned" else "nominal"
    canonical = World(cell.task, cell.seed, condition)
    canonical.wrapped._max_episode_steps = 200
    traces = {}
    outcomes = {}
    prefix = []
    prefix_records = []
    snap_custom = None
    directory = root / "fresh" / cell.task / f"{cell.seed}-{cell.condition}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        if cell.task == "PickCube-v1":
            case, prefix_records = initial(
                cell.seed,
                PickFault(
                    name=cell.condition,
                    offset_x=0.02 if cell.condition == "offset002" else 0,
                ),
            )
            prefix = case["prefix_actions"]
            World.controls += len(prefix)
            for a in prefix:
                canonical.step(a)
        else:
            prefix, prefix_records, _, _ = prefix_to_stage(canonical, "transport")
        canonical_start = canonical.state()
        snap_custom = jsonable(canonical.adapter.capture().custom)
        if not passes(compare(prefix_records[-1], canonical_start)):
            raise ValueError("Canonical prefix endpoint differs")
        for mode in ("continue", "recover"):
            if time.monotonic() >= deadline:
                raise TimeoutError("Physics wall ceiling")
            candidate = World(cell.task, cell.seed, condition)
            candidate.wrapped._max_episode_steps = 200
            try:
                history = [candidate.state()]
                for a in prefix:
                    history.append(candidate.step(a))
                memory = jsonable(candidate.adapter.capture().custom)
                prefix_errors = [
                    compare(a, b) for a, b in zip(prefix_records, history, strict=True)
                ]
                if (
                    candidate.edit != canonical.edit
                    or not all(passes(e) for e in prefix_errors)
                    or memory != snap_custom
                ):
                    raise ValueError(
                        "Full-prefix or controller-memory fidelity failure"
                    )
                start = candidate.state(refresh=True)
                if not passes(compare(canonical_start, start)):
                    raise ValueError("Fresh checkpoint differs from canonical parent")
                tcp = array(candidate.env.agent.tcp.pose.p).reshape(3).copy()
                frames = []
                for j in range(70):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Physics wall ceiling")
                    a = action_for(candidate, mode, j, tcp)
                    before = candidate.state()
                    state = candidate.step(a)
                    frames.append(
                        {
                            "before_observation": before["observation"],
                            "action": jsonable(a),
                            "state": jsonable(state),
                        }
                    )
                traces[mode] = {
                    "start": jsonable(start),
                    "prefix_history": jsonable(history),
                    "controller_memory": memory,
                    "prefix_errors": prefix_errors,
                    "initial_tcp": tcp.tolist(),
                    "frames": frames,
                    "model_edit": candidate.edit,
                }
                outcomes[mode + "_value"] = bool(frames[-1]["state"]["success"])
            finally:
                candidate.close()
        history = ObservationHistory(
            first=observed_frame(
                prefix_records[0]["time"], prefix_records[0]["observation"]
            ),
            current=observed_frame(
                canonical_start["time"], canonical_start["observation"]
            ),
        )
        model = {
            "task": cell.task,
            "condition": cell.condition,
            "edit": canonical.edit,
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("mani-skill", "sapien", "torch", "numpy")
            },
        }
        record = {
            "cell": cell.model_dump(),
            "prefix": jsonable(prefix_records),
            "prefix_actions": jsonable(prefix),
            "canonical_start": jsonable(canonical_start),
            "canonical_controller_memory": snap_custom,
            "traces": traces,
            "outcomes": outcomes,
            "model": model,
            "model_sha256": sha(model),
            "prefix_sha256": sha(prefix),
            "freeze_sha256": file_sha(root / "confirmation_freeze.json"),
            "qualification": "FULL_PREFIX_MATCHED_CONTROLLER_MEMORY_PAIRED_OUTCOMES",
            "future_trajectory_duplicate_executions": 0,
        }
        with gzip.open(directory / "trace.json.gz", "wt", compresslevel=6) as stream:
            json.dump(jsonable(record), stream, allow_nan=False)
        summary = {
            "id": f"{cell.task}/{cell.seed}/{cell.condition}",
            "group": f"{cell.task}/{cell.seed}",
            **cell.model_dump(),
            "outcomes": outcomes,
            "initial_success": bool(canonical_start["success"]),
            "features": feature_values(history),
            "optional_features": optional_values(history),
            "runtime_history": history.model_dump(mode="json"),
            "checkpoint_time": canonical_start["time"],
            "prefix_controls": len(prefix),
            "source": str(directory / "trace.json.gz"),
            "source_sha256": file_sha(directory / "trace.json.gz"),
            "wall_seconds": time.monotonic() - started,
            "candidate_outcome_continuations": 2,
            "status": "QUALIFIED",
        }
        save(directory / "summary.json", summary)
        return summary
    except Exception as error:
        with gzip.open(directory / "incomplete_trace.json.gz", "wt") as stream:
            json.dump(
                jsonable(
                    {
                        "cell": cell.model_dump(),
                        "prefix": prefix_records,
                        "prefix_actions": prefix,
                        "controller_memory": snap_custom,
                        "traces": traces,
                        "outcomes": outcomes,
                        "failure": str(error),
                    }
                ),
                stream,
            )
        save(
            directory / "failure.json",
            {
                "cell": cell.model_dump(),
                "reason": str(error),
                "type": type(error).__name__,
                "outcomes_complete": False,
            },
        )
        raise
    finally:
        canonical.close()


def run_parent_child(root, parent_index):
    parent = json.loads((root / "fresh_seed_manifest.json").read_text())["parents"][
        parent_index
    ]
    deadline = json.loads((root / "physics_started.json").read_text())[
        "deadline_monotonic"
    ]
    results = []
    try:
        for condition in parent["conditions"]:
            cell = Cell(task=parent["task"], seed=parent["seed"], condition=condition)
            summary = run_cell(cell, root, deadline)
            results.append(summary)
            with (root / "fresh_qualified.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(summary), allow_nan=False) + "\n")
        save(
            root / "parent_progress" / f"{parent_index:04d}.json",
            {
                "status": "COMPLETE",
                "group": parent["group"],
                "checkpoints": len(results),
                "physics_control_steps": World.controls,
            },
        )
    except Exception as error:
        save(
            root / "parent_progress" / f"{parent_index:04d}.json",
            {
                "status": "INCOMPLETE",
                "group": parent["group"],
                "checkpoints": len(results),
                "physics_control_steps": World.controls,
                "failure": {"type": type(error).__name__, "reason": str(error)},
            },
        )
        raise


def main(root):
    config = json.loads(Path("config/dsre_rss2027.json").read_text())
    freeze = json.loads((root / "confirmation_freeze.json").read_text())
    for kind in ("source_sha256", "input_sha256"):
        for name, expected in freeze[kind].items():
            if file_sha(Path(name)) != expected:
                raise ValueError("Frozen source/input changed: " + name)
    parents = json.loads((root / "fresh_seed_manifest.json").read_text())["parents"]
    started = time.monotonic()
    deadline = started + config["physics_wall_seconds"] - 2
    (root / "parent_progress").mkdir()
    save(
        root / "physics_started.json",
        {
            "epoch": time.time(),
            "deadline_monotonic": deadline,
            "limit_seconds": 10800,
            "maximum_outcome_continuations": 1600,
            "source_sha256": file_sha(Path(__file__)),
        },
    )
    summaries = []
    completed_parents = []
    stop = "COHORT_COMPLETE"
    failure = None
    try:
        for parent in parents:
            if time.monotonic() > deadline - 240:
                stop = "PHYSICS_WALL_RESERVE"
                break
            if (
                sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                > 850000000
            ):
                stop = "ARTIFACT_RESERVE"
                break
            index = len(completed_parents)
            result = subprocess.run(
                [
                    sys.executable,
                    __file__,
                    "--root",
                    str(root),
                    "--parent-index",
                    str(index),
                ],
                timeout=min(240, deadline - time.monotonic()),
                check=False,
            )
            summaries = (
                [
                    json.loads(s)
                    for s in (root / "fresh_qualified.jsonl").read_text().splitlines()
                ]
                if (root / "fresh_qualified.jsonl").exists()
                else []
            )
            if result.returncode:
                raise RuntimeError("Parent process failed: " + str(parent))
            completed_parents.append(parent["group"])
            save(
                root / "physics_progress.json",
                {
                    "qualified_checkpoints": len(summaries),
                    "completed_parents": len(completed_parents),
                    "candidate_outcome_continuations": 2 * len(summaries),
                    "elapsed_seconds": time.monotonic() - started,
                    "last_parent": parent,
                },
            )
            print(
                json.dumps(
                    {
                        "qualified_checkpoints": len(summaries),
                        "completed_parents": len(completed_parents),
                        "task": parent["task"],
                        "seed": parent["seed"],
                    }
                ),
                flush=True,
            )
    except Exception as error:
        logging.getLogger(__name__).exception(
            "Prospective physics stopped; preserve completed parents"
        )
        stop = "QUALIFICATION_OR_RUNTIME_BLOCKER"
        failure = {"type": type(error).__name__, "reason": str(error)}
    save(
        root / "physics_completed.json",
        {
            "status": "COMPLETE" if stop == "COHORT_COMPLETE" else "INCOMPLETE",
            "stop_reason": stop,
            "failure": failure,
            "qualified_checkpoints": len(summaries),
            "fully_completed_seed_parents": completed_parents,
            "candidate_outcome_continuations": 2 * len(summaries),
            "wall_seconds": time.monotonic() - started,
            "registered_parents": 400,
            "registered_checkpoints": 800,
            "no_replacement_seeds": True,
            "native_snapshot_restore_executions": 0,
            "physics_control_steps_counted": sum(
                json.loads(p.read_text())["physics_control_steps"]
                for p in (root / "parent_progress").glob("*.json")
            ),
            "note": "Includes Pick prefix generator steps. No duplicate future-outcome branches. A failed/missing parent is not replenished.",
        },
    )
    print(
        json.dumps(json.loads((root / "physics_completed.json").read_text())),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--parent-index", type=int)
    a = p.parse_args()
    if (a.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    if a.parent_index is not None:
        if (
            not (a.root / "physics_started.json").exists()
            or (a.root / "parent_progress" / f"{a.parent_index:04d}.json").exists()
        ):
            raise SystemExit("Invalid or already executed parent")
        run_parent_child(a.root, a.parent_index)
    else:
        if (a.root / "physics_started.json").exists():
            raise SystemExit("Already started; do not duplicate fresh outcomes")
        main(a.root)
