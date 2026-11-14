"""Short atomic untouched-parent batches, with no scientific-failure restart."""

import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

from dsre_final_verify import verify_sources
from dsre_followup_batch import atomic, read, sha
from dsre_operational_batch import parent_child


def resume_interruption(root):
    """Audit completed parents; retain partial attempts, then permit unused IDs."""
    unfinished = [
        p
        for p in (root / "chunks").glob("*_started.json")
        if not p.with_name(p.name.replace("_started", "_complete")).exists()
    ]
    if not unfinished:
        return
    from dsre_final_analysis import audit_rows
    from dsre_operational_analysis import qualified

    assert not (root / "study_halt.json").exists(), "Scientific halt cannot resume"
    for p in (root / "parent_progress").glob("*.json"):
        assert read(p)["status"] in ("COMPLETE", "PROCESS_INTERRUPTION_PARTIAL"), (
            "Failed scientific parent cannot resume"
        )
    assert not list((root / "selected").glob("*/*/failure.json")), (
        "Selected scientific failure cannot resume"
    )
    all_rows, complete, _ = qualified(root)
    proof = audit_rows(root, complete)
    partial = []
    for p in (root / "parent_attempts").glob("*.json"):
        target = root / "parent_progress" / p.name
        if not target.exists():
            parent = read(p)
            atomic(
                target,
                parent
                | {
                    "status": "PROCESS_INTERRUPTION_PARTIAL",
                    "reason": "Clean process interruption; no repeated parent",
                },
            )
            partial.append(parent["group"])
    for p in unfinished:
        atomic(
            p.with_name(p.name.replace("_started", "_complete")),
            {
                "sequence": read(p)["sequence"],
                "status": "PROCESS_INTERRUPTION_AUDITED",
                "completed_parents": sorted({r["group"] for r in complete}),
                "never_started_only_after_resume": True,
            },
        )
    atomic(
        root
        / f"interruption_audit_{len(list(root.glob('interruption_audit_*.json'))):04d}.json",
        {
            "status": "PASS",
            "epoch": time.time(),
            "qualified_secondary_cells": len(all_rows) - len(complete),
            "partial_parents_never_repeated": partial,
            "proof": proof,
        },
    )


def chunk(root):
    verify_sources(root)
    assert read(root / "qualification_seal.json")["status"] == "PASS"
    assert (
        sha(root / "calibration_decision.json")
        == read(root / "calibration_seal.json")["sha256"]
    )
    if (root / "study_halt.json").exists() or (
        root / "completion_manifest.json"
    ).exists():
        raise ValueError("Sealed or scientifically halted")
    config = read(Path("config/dsre_final_sprint.json"))
    with (root / "chunk.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        resume_interruption(root)
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        remaining = config["physics_wall_seconds"] - sum(
            j["wall_seconds"] for j in jobs if j["name"].startswith("physics_")
        )
        if remaining < 510:
            atomic(
                root / "physics_boundary.json",
                {"reason": "OUTER_PHYSICS_CEILING_RESERVE", "remaining": remaining},
            )
            return
        sequence = len(list((root / "chunks").glob("*_complete.json")))
        started = time.monotonic()
        deadline = started + min(config["chunk_wall_seconds"], remaining - 30)
        atomic(
            root / "chunks" / f"{sequence:04d}_started.json",
            {"sequence": sequence, "epoch": time.time()},
        )
        complete = []
        status = "CLEAN_CHUNK_BOUNDARY"
        for _ in range(config["maximum_parents_per_chunk"]):
            if time.monotonic() > deadline - config["parent_wall_seconds"]:
                break
            if (
                sum(
                    p.stat().st_size
                    for p in root.rglob("*")
                    if p.is_file() and not p.is_symlink()
                )
                > config["artifact_soft_stop_bytes"]
            ):
                status = "ARTIFACT_SOFT_STOP"
                atomic(root / "physics_boundary.json", {"reason": status})
                break
            attempted = {
                read(p)["group"] for p in (root / "parent_attempts").glob("*.json")
            }
            parent = next(
                (
                    p
                    for p in read(root / "fresh_seed_manifest.json")["parents"]
                    if p["group"] not in attempted
                ),
                None,
            )
            if parent is None:
                status = "COHORT_EXHAUSTED"
                break
            verify_sources(root)
            atomic(
                root / "parent_attempts" / f"{parent['index']:04d}.json",
                parent | {"epoch": time.time(), "chunk": sequence},
            )
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        "--root",
                        str(root),
                        "--parent-index",
                        str(parent["index"]),
                    ],
                    timeout=config["parent_wall_seconds"] + 3,
                    check=False,
                )
                if process.returncode:
                    raise RuntimeError(f"Parent exit {process.returncode}")
                assert (
                    read(root / "parent_progress" / f"{parent['index']:04d}.json")[
                        "status"
                    ]
                    == "COMPLETE"
                )
                complete.append(parent["group"])
            except (subprocess.TimeoutExpired, RuntimeError, AssertionError) as error:
                status = "SCIENTIFIC_OR_RUNTIME_HALT"
                atomic(
                    root / "study_halt.json", {"reason": str(error), "parent": parent}
                )
                break
            atomic(
                root / "chunks" / f"{sequence:04d}_live.json",
                {
                    "completed_parents": complete,
                    "wall_seconds": time.monotonic() - started,
                },
            )
            print(
                json.dumps(
                    {
                        "sequence": sequence,
                        "completed_parent": parent["group"],
                        "count": len(complete),
                    }
                ),
                flush=True,
            )
        result = {
            "sequence": sequence,
            "status": status,
            "completed_parents": complete,
            "wall_seconds": time.monotonic() - started,
        }
        atomic(root / "chunks" / f"{sequence:04d}_complete.json", result)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--parent-index", type=int)
    args = parser.parse_args()
    parent_child(
        args.root, args.parent_index
    ) if args.parent_index is not None else chunk(args.root)
