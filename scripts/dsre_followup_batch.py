"""Short synchronous chunks; fixed suffix, unchanged paired physics, atomic parents."""

import argparse
import fcntl
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def verify_freeze(root):
    freeze = read(root / "confirmation_freeze.json")
    for kind in ("source_sha256", "input_sha256"):
        for name, expected in freeze[kind].items():
            if sha(Path(name)) != expected:
                raise ValueError("Frozen source/input changed: " + name)


def next_parent(parents, attempts):
    untouched = [p for p in parents if p["group"] not in attempts]
    return min(untouched, key=lambda p: p["original_index"]) if untouched else None


def parent_child(root, index, duration):
    # Import and invoke the original scientific implementation unchanged.
    from dsre_paper_physics import Cell, World, run_cell

    parent = read(root / "fresh_seed_manifest.json")["parents"][index]
    if index < 0 or not (root / "parent_attempts" / f"{index:04d}.json").exists():
        raise ValueError("Parent requires a registered attempt")
    if (root / "parent_progress" / f"{index:04d}.json").exists():
        raise ValueError("Parent already finalized; never repeat")
    started = time.monotonic()
    before = time.process_time()
    summaries = []
    try:
        for condition in parent["conditions"]:
            summaries.append(
                run_cell(
                    Cell(task=parent["task"], seed=parent["seed"], condition=condition),
                    root,
                    started + duration,
                )
            )
            atomic(
                root / "parent_live" / f"{index:04d}.json",
                {
                    "group": parent["group"],
                    "completed_cells": [r["id"] for r in summaries],
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - before,
                },
            )
        atomic(
            root / "parent_progress" / f"{index:04d}.json",
            {
                "status": "COMPLETE",
                "group": parent["group"],
                "index": index,
                "checkpoints": [
                    {
                        "id": s["id"],
                        "source": s["source"],
                        "source_sha256": s["source_sha256"],
                    }
                    for s in summaries
                ],
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - before,
                "physics_control_steps": World.controls,
            },
        )
    except Exception as error:
        atomic(
            root / "parent_progress" / f"{index:04d}.json",
            {
                "status": "QUALIFICATION_OR_RUNTIME_FAILURE",
                "group": parent["group"],
                "index": index,
                "completed_cells": [r["id"] for r in summaries],
                "error_type": type(error).__name__,
                "error": str(error),
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - before,
            },
        )
        raise


def attempts(root):
    return {
        read(p)["group"]: read(p) for p in (root / "parent_attempts").glob("*.json")
    }


def recover_interrupted(root):
    """No physics: retain all files and permanently exclude uncommitted parents."""
    for attempt in attempts(root).values():
        path = root / "parent_progress" / f"{attempt['index']:04d}.json"
        if not path.exists():
            atomic(
                path,
                {
                    "status": "INTERRUPTED_UNCOMMITTED_PARENT",
                    "group": attempt["group"],
                    "index": attempt["index"],
                    "reason": "Previous chunk ended without atomic parent completion; no measurements repeated.",
                    "known_outcomes": "Only persisted qualified cell summaries may be used as secondary diagnostics.",
                },
            )
    for start in sorted((root / "chunks").glob("*_started.json")):
        target = start.with_name(start.name.replace("_started", "_complete"))
        if not target.exists():
            metadata = read(start)
            live = start.with_name(start.name.replace("_started", "_live"))
            observed = time.time() - metadata["epoch"]
            atomic(
                target,
                {
                    "status": "UNEXPECTED_CHUNK_INTERRUPTION",
                    "sequence": metadata["sequence"],
                    "wall_seconds": observed,
                    "wall_is_observed_upper_bound": True,
                    "cpu_seconds": read(live)["cpu_seconds"] if live.exists() else None,
                    "cpu_is_last_checkpoint_lower_bound": True,
                    "cause": "Unknown; no timeout/OOM/source failure inferred.",
                    "last_completed_parent": read(live).get("last_completed_parent")
                    if live.exists()
                    else None,
                },
            )


def chunk(root):
    if (root / "completion_manifest.json").exists() or (
        root / "study_halt.json"
    ).exists():
        raise ValueError("Sealed or halted study")
    verify_freeze(root)
    config = read(Path("config/dsre_followup.json"))
    with (root / "chunk.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        recover_interrupted(root)
        chunks = [read(p) for p in (root / "chunks").glob("*_complete.json")]
        consumed = sum(c["wall_seconds"] for c in chunks)
        unexpected = sum(c["status"] == "UNEXPECTED_CHUNK_INTERRUPTION" for c in chunks)
        if unexpected >= config["unexpected_sigterm_limit"]:
            atomic(
                root / "study_halt.json",
                {"reason": "Unexpected interruption limit reached"},
            )
            return
        remaining = config["physics_wall_seconds"] - consumed
        if remaining < config["parent_wall_seconds"]:
            atomic(
                root / "physics_boundary.json",
                {
                    "reason": "CUMULATIVE_PHYSICS_WALL_LIMIT",
                    "consumed_wall_seconds": consumed,
                },
            )
            return
        sequence = len(chunks)
        stem = root / "chunks" / f"{sequence:04d}"
        started = time.monotonic()
        cpu_started = time.process_time()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        deadline = started + min(config["chunk_wall_seconds"], remaining)
        atomic(
            stem.with_name(stem.name + "_started.json"),
            {
                "sequence": sequence,
                "epoch": time.time(),
                "duration_limit_seconds": deadline - started,
                "source_sha256": sha(Path(__file__)),
            },
        )
        parents = read(root / "fresh_seed_manifest.json")["parents"]
        completed = []
        status = "CLEAN_CHUNK_BOUNDARY"
        failure = None
        for _ in range(config["maximum_parents_per_chunk"]):
            if time.monotonic() > deadline - config["parent_wall_seconds"]:
                break
            if (
                sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                > config["new_artifact_bytes"]
                - config["physics_artifact_reserve_bytes"]
            ):
                status = "ARTIFACT_RESERVE"
                atomic(root / "physics_boundary.json", {"reason": status})
                break
            parent = next_parent(parents, attempts(root))
            if parent is None:
                status = "COHORT_EXHAUSTED"
                break
            verify_freeze(root)
            index = parent["index"]
            atomic(
                root / "parent_attempts" / f"{index:04d}.json",
                {
                    "group": parent["group"],
                    "index": index,
                    "chunk": sequence,
                    "epoch": time.time(),
                },
            )
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        "--root",
                        str(root),
                        "--parent-index",
                        str(index),
                        "--duration",
                        str(config["parent_wall_seconds"]),
                    ],
                    timeout=config["parent_wall_seconds"] + 3,
                    check=False,
                )
                if result.returncode:
                    if result.returncode == -signal.SIGTERM:
                        status = "UNEXPECTED_CHUNK_INTERRUPTION"
                        recover_interrupted_parent(
                            root, parent, "Child SIGTERM15; cause unknown"
                        )
                        break
                    raise RuntimeError(
                        f"Parent {parent['group']} returned {result.returncode}"
                    )
                record = read(root / "parent_progress" / f"{index:04d}.json")
                if record["status"] != "COMPLETE":
                    raise ValueError("Missing atomic completion")
                completed.append(parent["group"])
            except (subprocess.TimeoutExpired, RuntimeError, ValueError) as error:
                status = "QUALIFICATION_OR_RUNTIME_BLOCKER"
                failure = {"type": type(error).__name__, "reason": str(error)}
                atomic(
                    root / "study_halt.json",
                    {"reason": status, "failure": failure, "parent": parent},
                )
                break
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            atomic(
                stem.with_name(stem.name + "_live.json"),
                {
                    "completed_parents": completed,
                    "last_completed_parent": parent["group"],
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": after.ru_utime
                    + after.ru_stime
                    - usage.ru_utime
                    - usage.ru_stime
                    + time.process_time()
                    - cpu_started,
                },
            )
            print(
                json.dumps(
                    {
                        "chunk": sequence,
                        "completed_parent": parent["group"],
                        "completed_in_chunk": len(completed),
                    }
                ),
                flush=True,
            )
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        result = {
            "sequence": sequence,
            "status": status,
            "completed_parents": completed,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": after.ru_utime
            + after.ru_stime
            - usage.ru_utime
            - usage.ru_stime
            + time.process_time()
            - cpu_started,
            "peak_child_rss_kib": after.ru_maxrss,
            "failure": failure,
        }
        atomic(stem.with_name(stem.name + "_complete.json"), result)
        print(json.dumps(result), flush=True)


def recover_interrupted_parent(root, parent, reason):
    path = root / "parent_progress" / f"{parent['index']:04d}.json"
    if not path.exists():
        atomic(
            path,
            {
                "status": "INTERRUPTED_UNCOMMITTED_PARENT",
                "group": parent["group"],
                "index": parent["index"],
                "reason": reason,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--parent-index", type=int)
    parser.add_argument("--duration", type=int, default=120)
    args = parser.parse_args()
    if args.parent_index is None:
        chunk(args.root)
    else:
        verify_freeze(args.root)
        parent_child(args.root, args.parent_index, args.duration)
