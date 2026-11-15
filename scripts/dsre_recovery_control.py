"""Sequential foreground orchestration of bounded checkpointed physics chunks."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from dsre_followup_batch import atomic, read


def run(root, stage):
    plan = read(root / "plan.json")
    assert read(root / "qualification_audit.json")["passed"]
    started = time.time()
    while True:
        completed = list((root / "progress").glob(stage + "-*.json"))
        total = sum(
            read(p)["wall_seconds"] for p in (root / "chunks").glob("chunk-*.json")
        )
        if (root / "study_halt.json").exists() or (
            root / "resource_boundary.json"
        ).exists():
            reason = "PHYSICS_OR_RESOURCE_HALT"
            break
        if stage == "calibration":
            counts = (
                read(root / "counts.json") if (root / "counts.json").exists() else {}
            )
            if all(
                counts.get(m, 0) >= 112 or not reachable
                for m, reachable in plan["reachable_recover"].items()
            ):
                reason = "ALL_FIXED_ASSIGNMENT_QUOTAS"
                break
            if len(completed) >= len(plan["calibration_seeds"]):
                reason = "FIXED_SCREEN_LIMIT"
                break
            if total >= 14 * 3600 - 900:
                reason = "RESERVED_TEST_SIMULATION_BUDGET"
                break
        elif len(completed) >= len(plan["test_seeds"]):
            reason = "FIXED_TEST_COMPLETE"
            break
        before = len(completed)
        status = subprocess.run(
            [
                sys.executable,
                "scripts/dsre_recovery_evidence.py",
                "chunk",
                str(root),
                "--stage",
                stage,
            ],
            check=False,
        ).returncode
        after = len(list((root / "progress").glob(stage + "-*.json")))
        atomic(
            root / (stage + "_controller_checkpoint.json"),
            {
                "stage": stage,
                "complete_progress_records": after,
                "last_chunk_status": status,
                "epoch": time.time(),
            },
        )
        if status or after == before:
            reason = "CHUNK_STOP"
            break
    atomic(
        root / (stage + "_boundary.json"),
        {
            "reason": reason,
            "stage": stage,
            "wall_seconds": time.time() - started,
            "epoch": time.time(),
        },
    )
    print(reason, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--stage", choices=["calibration", "test"], required=True)
    a = p.parse_args()
    run(a.root, a.stage)
