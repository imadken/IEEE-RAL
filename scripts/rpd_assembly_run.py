"""Bounded qualification gate then conditional24-parent study; no confirmation path."""

import argparse
import json
import logging
import lzma
import os
import signal
import subprocess
import sys
import time

import numpy as np
from rpd_assembly_audit import check_row, compare_roots
from rpd_assembly_contract import (
    BASE,
    Candidate,
    Job,
    active_registration_path,
    episode_directory,
    sha,
    verify_registration,
    write,
)

LOGGER = logging.getLogger(__name__)


def load_row(path):
    with lzma.open(path, "rt") as stream:
        return json.load(stream)


def launch(job, deadline):
    directory = episode_directory(job)
    assert time.monotonic() < deadline
    assert (
        sum(p.stat().st_size for p in BASE.rglob("*") if p.is_file()) < 2 * 1024**3
    ), "STOP_ARTIFACT_CEILING"
    if directory.exists():
        process = json.loads((directory / "process.json").read_text())
        assert process["returncode"] == 0 and not process["timed_out"], (
            "Previous failure retained; no automatic retry"
        )
        assert check_row(directory)["passed"]
        return load_row(directory / "result.json.xz"), process
    directory.mkdir(parents=True)
    write(directory / "job.json", job.model_dump())
    started = time.monotonic()
    env = dict(
        os.environ,
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        PYTHONPATH="src:scripts",
    )
    # The attempt and its exact immutable input exist before launching physics.
    command = [
        sys.executable,
        "scripts/rpd_assembly_worker.py",
        "--job",
        str(directory / "job.json"),
    ]
    timed_out = False
    with (directory / "console.log").open("x") as console:
        child = subprocess.Popen(
            command,
            stdout=console,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        write(
            directory / "attempt.json",
            {
                "candidate_id": job.candidate.candidate_id,
                "pid": child.pid,
                "command": command,
                "registration_sha256": sha(active_registration_path()),
            },
        )
        try:
            child.wait(timeout=min(60, max(0.01, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    process = {
        "candidate_id": job.candidate.candidate_id,
        "job_id": job.job_id,
        "returncode": child.returncode,
        "timed_out": timed_out,
        "wall_seconds": time.monotonic() - started,
        "registration_sha256": sha(active_registration_path()),
        "console_sha256": sha(directory / "console.log"),
    }
    write(directory / "process.json", process)
    assert child.returncode == 0 and not timed_out, f"STOP_SOURCE_FAILURE:{directory}"
    checked = check_row(directory)
    write(directory / "independent_check.json", checked)
    assert checked["passed"], f"STOP_INVALID_SOURCE_TRACE:{directory}"
    print(
        json.dumps(
            {
                "candidate_id": job.candidate.candidate_id,
                "intervention": job.intervention,
                "action": job.action,
                "repeat": job.repeat,
                "wall_seconds": process["wall_seconds"],
                "source_audit": True,
            }
        ),
        flush=True,
    )
    return load_row(directory / "result.json.xz"), process


def branches(candidate, repeat=0):
    result = [
        Job(candidate=candidate, intervention=p, action=a, repeat=repeat)
        for p in ("hold", "preload", "dither")
        for a in ("a0", "a1")
    ]
    if candidate.phase == "qual":
        result.append(
            Job(candidate=candidate, intervention="direct", action="a0", repeat=repeat)
        )
    return result


def execute(phase):
    registration = verify_registration()
    revision = registration.get("source_revision", 0)
    source_suffix = f"_sourcefix{revision:02d}" if revision else ""
    seconds = (
        registration["physics_qualification_cap_seconds"]
        if phase == "qual"
        else registration["exploratory_cap_seconds"]
    )
    previous = [
        json.loads(p.read_text()) for p in (BASE / "episodes").glob("*/process.json")
    ]
    prefix = "RPD-assembly-v1/qual/" if phase == "qual" else "RPD-assembly-prelim-v1/"
    spent = sum(
        p["wall_seconds"] for p in previous if p["candidate_id"].startswith(prefix)
    )
    deadline = time.monotonic() + max(0, seconds - spent)
    if phase == "exploratory":
        gate = json.loads(
            (BASE / ("qualification" + source_suffix + ".json")).read_text()
        )
        assert gate["passed"] and gate["registration_sha256"] == sha(
            active_registration_path()
        )
    candidates = [
        Candidate.model_validate(c)
        for c in registration["candidates"]
        if c["phase"] == phase
    ]
    eligible = []
    screens = {}
    timings = []
    try:
        for candidate in candidates:
            row, _ = launch(
                Job(candidate=candidate, intervention="screen", action="none"), deadline
            )
            screens[candidate.candidate_id] = row
            if row["eligibility"]["disposition"] == "KNOWN_ELIGIBLE":
                eligible.append(candidate)
        for candidate in eligible:
            for job in branches(candidate):
                row, process = launch(job, deadline)
                assert row["eligibility"]["disposition"] == "KNOWN_ELIGIBLE"
                assert compare_roots(
                    screens[candidate.candidate_id]["root"], row["root"]
                )["passed"], "STOP_INVALID_BRANCH_RECONSTRUCTION"
                timings.append(process["wall_seconds"])
        if phase == "qual":
            for candidate in eligible[:2]:
                for job in branches(candidate, repeat=1):
                    row, process = launch(job, deadline)
                    assert compare_roots(
                        screens[candidate.candidate_id]["root"], row["root"]
                    )["passed"]
                    original = Job(
                        candidate=candidate,
                        intervention=job.intervention,
                        action=job.action,
                    )
                    before = load_row(episode_directory(original) / "result.json.xz")
                    assert before["terminal"] == row["terminal"], (
                        "STOP_REPLAY_GOAL_OR_CONSTRAINT_MISMATCH"
                    )
                    # Full trace state parity, independent of success outcomes.
                    a = episode_directory(original) / "trace.jsonl"
                    b = episode_directory(job) / "trace.jsonl"
                    aa = [json.loads(line) for line in a.read_text().splitlines()]
                    bb = [json.loads(line) for line in b.read_text().splitlines()]
                    assert len(aa) == len(bb) == 550
                    assert all(
                        compare_roots({"frame": x}, {"frame": y})["passed"]
                        for x, y in zip(aa, bb)
                    ), "STOP_REPLAY_TRACE_MISMATCH"
                    timings.append(process["wall_seconds"])
        report = {
            "phase": phase,
            "passed": len(eligible) >= 8 if phase == "qual" else True,
            "fixed_candidates": len(candidates),
            "screened": len(screens),
            "eligible": len(eligible),
            "registered_branch_count": len(timings),
            "registration_sha256": sha(active_registration_path()),
            "median_branch_wall_seconds": float(np.median(timings))
            if timings
            else None,
            "p95_branch_wall_seconds": float(np.percentile(timings, 95))
            if timings
            else None,
            "reason": "COMPLETE"
            if phase != "qual" or len(eligible) >= 8
            else "FEWER_THAN_EIGHT_REGISTERED_ELIGIBLE_ROOTS",
            "source_result_is_not_population_H1_or_H2": True,
        }
    except Exception as exc:
        LOGGER.exception("Source qualification stopped at the exact failed row")
        report = {
            "phase": phase,
            "passed": False,
            "screened": len(screens),
            "eligible": len(eligible),
            "registration_sha256": sha(active_registration_path()),
            "reason": str(exc),
            "failure_type": type(exc).__name__,
            "preserved_all_attempts": True,
        }
    destination = BASE / (
        ("qualification" if phase == "qual" else "exploratory")
        + source_suffix
        + ".json"
    )
    write(destination, report)
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("qual", "exploratory"))
    raise SystemExit(execute(parser.parse_args().phase))
