"""Synchronous bounded batches reusing unchanged paired physics and controllers."""

import argparse
import gzip
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_observations import packet_from_summary
from dsre_paper_physics import Cell, World, action_for, run_cell

from dual_rec.dsre.operational import OperationalRouter, gated_action
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes


def selected_branch(cell, summary, root, router, calibration, deadline):
    # The typed packet exposes only frozen predecision predicates. Paired labels
    # are never arguments to routing, and calibration was sealed before test.
    packet = packet_from_summary(summary, read(root / "frozen_routers.json"))
    decision = router.route(packet)["DSRE_risk"]
    action = gated_action(
        "DSRE_risk", cell.task, decision["action"], calibration["strata"]
    )
    directory = root / "selected" / cell.task / f"{cell.seed}-{cell.condition}"
    directory.mkdir(parents=True, exist_ok=False)
    selected = {
        "cell": cell.model_dump(),
        "predecision_input": packet.model_dump(mode="json"),
        "proposed_action": decision["action"],
        "action": action,
        "decision": decision,
        "calibration_sha256": sha(root / "calibration_decision.json"),
        "decision_frozen_epoch": time.time(),
        "scope": "Independent selected-branch reset execution, after paired measurement; route accepts no outcome labels and was frozen before outcomes. This is an execution repeat, not another independent seed.",
    }
    atomic(directory / "decision.json", selected)
    if action is None:
        atomic(
            directory / "execution.json",
            {
                "status": "DEFER_STOP",
                "action": None,
                "autonomous_completion": False,
                "new_continuations": 0,
            },
        )
        return
    with gzip.open(summary["source"], "rt") as stream:
        raw = json.load(stream)
    condition = "misaligned" if cell.condition == "misaligned" else "nominal"
    world = World(cell.task, cell.seed, condition)
    world.wrapped._max_episode_steps = 200
    try:
        states = [world.state()]
        for command in raw["prefix_actions"]:
            states.append(world.step(command))
        errors = [compare(a, b) for a, b in zip(raw["prefix"], states, strict=True)]
        memory = jsonable(world.adapter.capture().custom)
        start = world.state(refresh=True)
        if (
            not all(passes(e) for e in errors)
            or not passes(compare(raw["canonical_start"], start))
            or memory != raw["canonical_controller_memory"]
            or world.edit != raw["model"]["edit"]
        ):
            raise ValueError(
                "Selected-branch prefix/controller/model qualification failed"
            )
        tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
        frames = []
        for j in range(70):
            if time.monotonic() >= deadline:
                raise TimeoutError("Parent selected execution exceeded reserve")
            command = action_for(world, action, j, tcp)
            before = world.state()
            state = world.step(command)
            frames.append(
                {
                    "before_observation": before["observation"],
                    "action": jsonable(command),
                    "state": jsonable(state),
                }
            )
        paired = raw["traces"][action]
        future_errors = [
            compare(a["state"], b["state"])
            for a, b in zip(paired["frames"], frames, strict=True)
        ]
        result = {
            "status": "QUALIFIED_SELECTED_EXECUTION",
            "action": action,
            "new_continuations": 1,
            "initial_tcp": tcp.tolist(),
            "start": jsonable(start),
            "prefix_errors": errors,
            "controller_memory": memory,
            "model_edit": world.edit,
            "frames": frames,
            "paired_terminal_success": summary["outcomes"][action + "_value"],
            "terminal_success": bool(frames[-1]["state"]["success"]),
            "selected_future_parity": all(passes(e) for e in future_errors),
            "future_errors": future_errors,
        }
        with gzip.open(directory / "execution.json.gz", "wt") as stream:
            json.dump(jsonable(result), stream, allow_nan=False)
        atomic(
            directory / "execution.json",
            {
                k: v
                for k, v in result.items()
                if k
                not in ("frames", "future_errors", "prefix_errors", "controller_memory")
            }
            | {
                "source": str(directory / "execution.json.gz"),
                "source_sha256": sha(directory / "execution.json.gz"),
            },
        )
        if (
            not result["selected_future_parity"]
            or result["terminal_success"] != result["paired_terminal_success"]
        ):
            raise ValueError("Selected execution disagrees with measured paired branch")
    finally:
        world.close()


def parent_child(root, index):
    verify_freeze(root)
    config = read(Path("config/dsre_operational.json"))
    parent = read(root / "fresh_seed_manifest.json")["parents"][index]
    if (
        not (root / "parent_attempts" / f"{index:04d}.json").exists()
        or (root / "parent_progress" / f"{index:04d}.json").exists()
    ):
        raise ValueError("Unregistered or repeated parent")
    started, cpu = time.monotonic(), time.process_time()
    deadline = started + config["parent_wall_seconds"]
    router = (
        OperationalRouter(read(root / "frozen_routers.json"))
        if parent["split"] == "test"
        else None
    )
    calibration = read(root / "calibration_decision.json") if router else None
    if router:
        assert (
            sha(root / "calibration_decision.json")
            == read(root / "calibration_seal.json")["sha256"]
        )
    cells = []
    try:
        for condition in parent["conditions"]:
            cell = Cell(task=parent["task"], seed=parent["seed"], condition=condition)
            summary = run_cell(cell, root, deadline)
            if router:
                selected_branch(cell, summary, root, router, calibration, deadline)
            cells.append(
                {
                    "id": summary["id"],
                    "source": summary["source"],
                    "source_sha256": summary["source_sha256"],
                }
            )
            atomic(
                root / "parent_live" / f"{index:04d}.json",
                {
                    "group": parent["group"],
                    "completed_cells": cells,
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                },
            )
        atomic(
            root / "parent_progress" / f"{index:04d}.json",
            {
                "status": "COMPLETE",
                **parent,
                "checkpoints": cells,
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu,
            },
        )
    except Exception as error:
        atomic(
            root / "parent_progress" / f"{index:04d}.json",
            {
                "status": "QUALIFICATION_OR_RUNTIME_FAILURE",
                **parent,
                "completed_cells": cells,
                "reason": str(error),
            },
        )
        raise


def chunk(root):
    import fcntl

    verify_freeze(root)
    if (root / "completion_manifest.json").exists() or (
        root / "study_halt.json"
    ).exists():
        raise ValueError("Sealed or halted")
    read(Path("config/dsre_operational.json"))
    with (root / "chunk.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        starts = sorted((root / "chunks").glob("*_started.json"))
        if any(
            not p.with_name(p.name.replace("_started", "_complete")).exists()
            for p in starts
        ):
            atomic(
                root / "study_halt.json",
                {
                    "reason": "UNEXPECTED_INTERRUPTION_NO_REPEATS",
                    "partial_attempts_retained": True,
                },
            )
            return
        chunks = [read(p) for p in (root / "chunks").glob("*_complete.json")]
        remaining = 10800 - sum(c["wall_seconds"] for c in chunks)
        if remaining < 120:
            atomic(
                root / "physics_boundary.json",
                {"reason": "PHYSICS_WALL_CEILING", "remaining": remaining},
            )
            return
        parents = read(root / "fresh_seed_manifest.json")["parents"]
        sequence = len(chunks)
        started, cpu = time.monotonic(), time.process_time()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        deadline = started + min(480, remaining)
        atomic(
            root / "chunks" / f"{sequence:04d}_started.json",
            {
                "sequence": sequence,
                "epoch": time.time(),
                "remaining_physics_seconds": remaining,
            },
        )
        complete, status = [], "CLEAN_CHUNK_BOUNDARY"
        for _ in range(24):
            if time.monotonic() > deadline - 120:
                break
            if (
                sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                > 850000000
            ):
                status = "ARTIFACT_SOFT_STOP"
                atomic(root / "physics_boundary.json", {"reason": status})
                break
            attempted = {
                read(p)["group"] for p in (root / "parent_attempts").glob("*.json")
            }
            parent = next((p for p in parents if p["group"] not in attempted), None)
            if parent is None:
                status = "COHORT_EXHAUSTED"
                break
            if (
                parent["split"] == "test"
                and not (root / "calibration_seal.json").exists()
            ):
                status = "CALIBRATION_BOUNDARY"
                break
            verify_freeze(root)
            atomic(
                root / "parent_attempts" / f"{parent['index']:04d}.json",
                {**parent, "chunk": sequence, "epoch": time.time()},
            )
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        "--root",
                        str(root),
                        "--parent-index",
                        str(parent["index"]),
                    ],
                    timeout=123,
                    check=False,
                )
                if result.returncode:
                    raise RuntimeError(f"Parent returned {result.returncode}")
                assert (
                    read(root / "parent_progress" / f"{parent['index']:04d}.json")[
                        "status"
                    ]
                    == "COMPLETE"
                )
                complete.append(parent["group"])
            except (subprocess.TimeoutExpired, RuntimeError, AssertionError) as error:
                status = "QUALIFICATION_OR_RUNTIME_HALT"
                atomic(
                    root / "study_halt.json", {"reason": str(error), "parent": parent}
                )
                break
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            atomic(
                root / "chunks" / f"{sequence:04d}_live.json",
                {
                    "last_completed_parent": parent["group"],
                    "completed_parents": complete,
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": after.ru_utime
                    + after.ru_stime
                    - usage.ru_utime
                    - usage.ru_stime
                    + time.process_time()
                    - cpu,
                },
            )
            print(
                json.dumps(
                    {
                        "chunk": sequence,
                        "completed_parent": parent["group"],
                        "count": len(complete),
                    }
                ),
                flush=True,
            )
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        final = {
            "sequence": sequence,
            "status": status,
            "completed_parents": complete,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": after.ru_utime
            + after.ru_stime
            - usage.ru_utime
            - usage.ru_stime
            + time.process_time()
            - cpu,
            "peak_rss_kib": after.ru_maxrss,
        }
        atomic(root / "chunks" / f"{sequence:04d}_complete.json", final)
        print(json.dumps(final), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--parent-index", type=int)
    args = parser.parse_args()
    parent_child(
        args.root, args.parent_index
    ) if args.parent_index is not None else chunk(args.root)
