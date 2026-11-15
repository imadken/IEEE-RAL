"""Seal the entire untouched cohort's recommendations before any test outcome."""

import argparse
import fcntl
import resource
import subprocess
import sys
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_recovery_audit import gz
from dsre_recovery_evidence import CONDITIONS, TASK, execute, screen

from dual_rec.dsre.operational import METHODS, OperationalRouter, gated_action


def verify(root):
    verify_freeze(root)
    registration = read(root / "test_registration.json")
    assert (
        sha(root / "calibration_decision.json")
        == registration["calibration_sha256"]
        == read(root / "calibration_seal.json")["sha256"]
    )
    for name, value in registration["source_sha256"].items():
        assert sha(Path(name)) == value


def register(root):
    assert (root / "calibration_seal.json").exists()
    assert not (root / "test_registration.json").exists()
    assert not (root / "study_halt.json").exists()
    value = {
        "epoch": time.time(),
        "plan_sha256": sha(root / "plan.json"),
        "calibration_sha256": sha(root / "calibration_decision.json"),
        "source_sha256": {
            p: sha(Path(p))
            for p in (
                "scripts/dsre_recovery_test.py",
                "scripts/dsre_recovery_evidence.py",
            )
        },
        "strengthened_order": "Seal BOTH conditions, ALL17 methods and ALL160 test parents before ANY test continuation outcome. Frozen policies, thresholds, seeds and action equations unchanged. Screening produces predecision packets only, never future labels.",
        "test_seeds": read(root / "plan.json")["test_seeds"],
    }
    atomic(root / "test_registration.json", value)
    for folder in ("test_screen_progress", "test_screen_attempts"):
        (root / folder).mkdir()


def parent(root, phase, index):
    verify(root)
    seed = read(root / "plan.json")["test_seeds"][index]
    directory = root / "test" / str(seed)
    started = time.monotonic()
    cpu = time.process_time()
    deadline = started + 120
    try:
        if phase == "screen":
            frozen = read(root / "frozen_routers.json")
            router = OperationalRouter(frozen)
            raws = [
                screen(seed, c, directory / c, frozen, router, deadline)
                for c in CONDITIONS
            ]
            cal = read(root / "calibration_decision.json")["strata"]
            decision = {
                "seed": seed,
                "stage": "test",
                "index": index,
                "screens": {
                    c: sha(directory / c / "screen.json.gz") for c in CONDITIONS
                },
                "all_actions": [
                    {
                        m: {
                            "proposal": r["proposals"][m]["action"],
                            "gated": gated_action(
                                m, TASK, r["proposals"][m]["action"], cal
                            ),
                        }
                        for m in METHODS
                    }
                    for r in raws
                ],
                "calibration_sha256": sha(root / "calibration_decision.json"),
                "sealed_epoch": time.time(),
            }
            atomic(directory / "decision.json", decision)
            result = {
                "seed": seed,
                "index": index,
                "status": "COMPLETE",
                "decision_sha256": sha(directory / "decision.json"),
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu,
            }
            atomic(root / "test_screen_progress" / f"{index:04d}.json", result)
        else:
            cohort = read(root / "test_recommendation_seal.json")
            decision = read(directory / "decision.json")
            assert cohort["decisions"][str(seed)] == sha(directory / "decision.json")
            assert cohort["parents"] == 160
            assert (
                sha(root / "test_recommendation_manifest.json")
                == cohort["manifest_sha256"]
            )
            atomic(
                directory / "execution_started.json",
                {
                    "epoch": time.time(),
                    "cohort_seal_sha256": sha(root / "test_recommendation_seal.json"),
                    "decision_sha256": sha(directory / "decision.json"),
                },
            )
            cells = []
            for c in CONDITIONS:
                assert sha(directory / c / "screen.json.gz") == decision["screens"][c]
                raw = gz(directory / c / "screen.json.gz")
                outcomes = [
                    execute(raw, m, directory / c, deadline)
                    for m in ("continue", "recover")
                ]
                cells.append({"condition": c, "outcomes": outcomes})
            result = {
                "seed": seed,
                "index": index,
                "stage": "test",
                "status": "COMPLETE",
                "cells": cells,
                "decision_sha256": sha(directory / "decision.json"),
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu,
            }
            atomic(root / "progress" / f"test-{index:04d}.json", result)
    except Exception as error:
        atomic(
            root / "study_halt.json",
            {
                "phase": "test_" + phase,
                "seed": seed,
                "index": index,
                "reason": str(error),
                "type": type(error).__name__,
                "epoch": time.time(),
            },
        )
        raise


def seal(root):
    verify(root)
    seeds = read(root / "test_registration.json")["test_seeds"]
    progress = [read(p) for p in sorted((root / "test_screen_progress").glob("*.json"))]
    assert len(progress) == 160 and all(p["status"] == "COMPLETE" for p in progress)
    assert {p["seed"] for p in progress} == set(seeds)
    decisions = {}
    for seed in seeds:
        d = root / "test" / str(seed)
        assert not (d / "execution_started.json").exists()
        for c in CONDITIONS:
            assert (
                not (d / c / "continue.json.gz").exists()
                and not (d / c / "recover.json.gz").exists()
            )
        decisions[str(seed)] = sha(d / "decision.json")
    atomic(
        root / "test_recommendation_manifest.json",
        {
            "decisions": decisions,
            "registration_sha256": sha(root / "test_registration.json"),
            "epoch": time.time(),
        },
    )
    atomic(
        root / "test_recommendation_seal.json",
        {
            "parents": 160,
            "conditions": 320,
            "method_decisions": 5440,
            "decisions": decisions,
            "manifest_sha256": sha(root / "test_recommendation_manifest.json"),
            "epoch": time.time(),
        },
    )


def chunk(root, phase):
    verify(root)
    if (root / "study_halt.json").exists():
        raise ValueError("Scientific halt")
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = [read(p) for p in (root / "chunks").glob("chunk-*.json")]
        used = sum(p["wall_seconds"] for p in previous)
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        count = 0
        if (
            used > 57600 - 150
            or sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
            > 4 * 1024**3 - 100_000_000
        ):
            atomic(
                root / "resource_boundary.json",
                {"simulation_wall_seconds": used, "epoch": time.time()},
            )
            return
        for index, seed in enumerate(
            read(root / "test_registration.json")["test_seeds"]
        ):
            progress = (
                (root / "test_screen_progress" / f"{index:04d}.json")
                if phase == "screen"
                else (root / "progress" / f"test-{index:04d}.json")
            )
            attempt = (
                (root / "test_screen_attempts" / f"{index:04d}.json")
                if phase == "screen"
                else (root / "attempts" / f"test-{index:04d}.json")
            )
            if progress.exists():
                continue
            if attempt.exists():
                atomic(
                    root / "study_halt.json",
                    {
                        "reason": "Interrupted test parent; never replaced",
                        "phase": phase,
                        "seed": seed,
                    },
                )
                break
            if count >= 20 or time.monotonic() - started >= min(
                840, 57600 - used - 150
            ):
                break
            atomic(
                attempt,
                {"phase": phase, "index": index, "seed": seed, "epoch": time.time()},
            )
            with (root / "chunks" / f"test-{phase}-{index:04d}.log").open(
                "x"
            ) as stream:
                child = subprocess.Popen(
                    [
                        sys.executable,
                        __file__,
                        "parent",
                        str(root),
                        "--phase",
                        phase,
                        "--index",
                        str(index),
                    ],
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                )
                try:
                    status = child.wait(timeout=150)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child.wait(timeout=10)
                    status = -15
            if status:
                if not (root / "study_halt.json").exists():
                    atomic(
                        root / "study_halt.json",
                        {
                            "reason": "Test child runtime failure",
                            "phase": phase,
                            "seed": seed,
                            "status": status,
                        },
                    )
                break
            count += 1
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        atomic(
            root / "chunks" / f"chunk-{len(previous):04d}.json",
            {
                "stage": "test_" + phase,
                "completed_parents": count,
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": after.ru_utime
                + after.ru_stime
                - before.ru_utime
                - before.ru_stime,
                "epoch": time.time(),
            },
        )
        print({"phase": phase, "parents": count}, flush=True)


def control(root):
    verify(root)
    for phase in ("screen", "outcome"):
        while True:
            progress = (
                list((root / "test_screen_progress").glob("*.json"))
                if phase == "screen"
                else list((root / "progress").glob("test-*.json"))
            )
            if len(progress) == 160:
                break
            if (root / "study_halt.json").exists() or (
                root / "resource_boundary.json"
            ).exists():
                return
            before = len(progress)
            subprocess.run(
                [sys.executable, __file__, "chunk", str(root), "--phase", phase],
                check=True,
            )
            after = (
                len(list((root / "test_screen_progress").glob("*.json")))
                if phase == "screen"
                else len(list((root / "progress").glob("test-*.json")))
            )
            if after == before:
                raise ValueError("No progress")
        if phase == "screen":
            seal(root)
    atomic(
        root / "test_boundary.json",
        {"status": "COMPLETE", "parents": 160, "epoch": time.time()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["register", "parent", "chunk", "control"])
    p.add_argument("root", type=Path)
    p.add_argument("--phase", choices=["screen", "outcome"], default="screen")
    p.add_argument("--index", type=int, default=0)
    a = p.parse_args()
    if a.command == "register":
        register(a.root)
    elif a.command == "parent":
        parent(a.root, a.phase, a.index)
    elif a.command == "chunk":
        chunk(a.root, a.phase)
    else:
        control(a.root)
