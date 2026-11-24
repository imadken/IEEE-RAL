"""Join bounded collection chunks in the supervisor's fixed task order."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from dsre_evidence_prospective import ROOT, TASKS, identity, is_blocked, read, specs


def command(script, stage, root, task):
    argv = [sys.executable, script, stage, "--root", str(root), "--task", task]
    started = time.time()
    result = subprocess.run(argv, check=False)
    print(
        json.dumps(
            {
                "chunk_finished": stage,
                "task": task,
                "returncode": result.returncode,
                "wall_seconds": time.time() - started,
            }
        ),
        flush=True,
    )
    if result.returncode:
        raise RuntimeError(
            f"Bounded stage failed: {stage}; preserve attempts before diagnosis"
        )


def remaining(root, task, stage):
    out = root / "prospective" / task
    phase = "calibration" if stage == "screen" else stage
    folder = "screens" if stage == "screen" else stage
    return sum(
        not (out / folder / f"{identity(s)}.json").exists()
        or (
            stage == "test" and not (out / "evaluator" / f"{identity(s)}.json").exists()
        )
        for s in specs(root, task, phase)
    )


def run(root, tasks):
    assert (root / "G2_execution_freeze.json").exists()
    for task in tasks:
        out = root / "prospective" / task
        if (
            task == TASKS[2]
            and not read(root / "G1_source_v2_qualification.json")["technical_pass"]
        ):
            print(json.dumps({"task": task, "status": "G1 BLOCKED"}), flush=True)
            continue
        blocked = False
        for stage in ("discovery", "screen", "calibration"):
            if stage == "screen" and not (out / "discovery_freeze.json").exists():
                command(
                    "scripts/dsre_evidence_prospective_fit.py", "discovery", root, task
                )
            if (
                stage == "calibration"
                and not (out / "acquisition_schedule.json").exists()
            ):
                command("scripts/dsre_evidence_prospective_fit.py", "plan", root, task)
            while remaining(root, task, stage):
                if is_blocked(out):
                    blocked = True
                    break
                command("scripts/dsre_evidence_prospective.py", stage, root, task)
            if is_blocked(out):
                blocked = True
                break
        if blocked:
            print(
                json.dumps(
                    {
                        "task": task,
                        "status": "SOURCE GUARD HALT",
                        "witness": read(out / "SOURCE_GUARD_FAILURE.json"),
                    }
                ),
                flush=True,
            )
            continue
        schedule = read(out / "acquisition_schedule.json")
        pairids = {
            r["parent_id"]
            for bs in schedule["schedules"].values()
            for r in bs["512"]
            if r["kind"] == "pair"
        }
        while any(
            not (out / "acquisition_pairs" / f"{pid}.json").exists() for pid in pairids
        ):
            command("scripts/dsre_evidence_prospective_fit.py", "refine", root, task)
            if is_blocked(out):
                blocked = True
                break
        if blocked:
            continue
        if not (out / "all_models_frozen.json").exists():
            command("scripts/dsre_evidence_prospective_fit.py", "freeze", root, task)
        while remaining(root, task, "test") and not is_blocked(out):
            command("scripts/dsre_evidence_prospective.py", "test", root, task)
        print(
            json.dumps({"task": task, "test_remaining": remaining(root, task, "test")}),
            flush=True,
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--task", choices=TASKS, action="append")
    a = p.parse_args()
    run(a.root, a.task or TASKS)
