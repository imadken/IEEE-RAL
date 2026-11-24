"""Fixed-cohort source-risk campaign; unchanged DSRE and paired physics."""

import argparse
import fcntl
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha


def verify(root):
    freeze = read(root / "source_freeze.json")
    for kind in ("source_sha256", "input_sha256"):
        for name, digest in freeze[kind].items():
            if sha(Path(name)) != digest:
                raise ValueError("Frozen input/source changed: " + name)
    for filename in ("calibration_seal.json", "test_recommendation_seal.json"):
        if (root / filename).exists():
            seal = read(root / filename)
            if filename == "calibration_seal.json":
                assert sha(root / "calibration_decision.json") == seal["sha256"]
    if (root / "completion_manifest.json").exists():
        raise ValueError("Completed evidence is read-only")


def seeds_for(plan, stage):
    return (
        plan["qualification_seeds"]
        if stage == "qualification"
        else plan["test_seeds" if stage.startswith("test") else "calibration_seeds"]
    )


def parent(root, stage, index):
    # Physics imports are confined to the bounded child process.
    from dsre_paper_physics import World
    from dsre_recovery_evidence import execute
    from dsre_science_physics import screen

    from dual_rec.dsre.measurement import RobustRouter
    from dual_rec.dsre.operational import OperationalRouter

    verify(root)
    plan = read(root / "study_plan.json")
    seed = seeds_for(plan, stage)[index]
    folder = "test" if stage.startswith("test") else stage
    directory = root / folder / str(seed)
    start, cpu = time.monotonic(), time.process_time()
    deadline = start + plan["limits"]["parent_seconds"]
    cells = []
    try:
        if stage != "qualification":
            assert read(root / "qualification_audit.json")["passed"]
        if stage.startswith("test"):
            assert read(root / "calibration_decision_audit.json")["passed"]
            assert read(root / "calibration_decision.json")["complete_cohort"]
        if stage != "test_outcome":
            if (directory / "decision.json").exists():
                raise ValueError("Parent already screened; no replacement")
            frozen = read(root / "frozen_routers.json")
            router, point = RobustRouter(frozen), OperationalRouter(frozen)
            raws = []
            for condition, offset in plan["profiles"]:
                raw = screen(
                    seed,
                    condition,
                    offset,
                    directory / condition,
                    root,
                    router,
                    point,
                    deadline,
                )
                raws.append(raw)
            dec = {
                "stage": stage,
                "seed": seed,
                "index": index,
                "screens": {
                    r["cell"]["condition"]: sha(
                        directory / r["cell"]["condition"] / "screen.json.gz"
                    )
                    for r in raws
                },
                "source_freeze_sha256": sha(root / "source_freeze.json"),
                "sealed_epoch": time.time(),
            }
            if stage == "test_screen":
                cal = read(root / "calibration_decision.json")
                dec["calibration_sha256"] = sha(root / "calibration_decision.json")
                dec["clean_gated_actions"] = {
                    r["cell"]["condition"]: {
                        m: d["action"]
                        if d["action"] is not None
                        and cal["strata"][m + "|" + d["action"]]["enabled"]
                        else None
                        for m, d in r["scenarios"]["clean"]["point_proposal"].items()
                    }
                    for r in raws
                }
            atomic(directory / "decision.json", dec)
        else:
            seal = read(root / "test_recommendation_seal.json")
            assert seal["parents"][str(seed)] == sha(directory / "decision.json")
            atomic(
                directory / "execution_started.json",
                {
                    "epoch": time.time(),
                    "cohort_seal_sha256": sha(root / "test_recommendation_seal.json"),
                },
            )
            dec = read(directory / "decision.json")
        decision_digest = sha(directory / "decision.json")
        if stage != "test_screen":
            import gzip

            for condition, _ in plan["profiles"]:
                d = directory / condition
                assert sha(d / "screen.json.gz") == dec["screens"][condition]
                with gzip.open(d / "screen.json.gz", "rt") as stream:
                    raw = json.load(stream)
                futures = [
                    execute(raw, mode, d, deadline) for mode in ("continue", "recover")
                ]
                cells.append({"condition": condition, "outcomes": futures})
        assert sha(directory / "decision.json") == decision_digest
        result = {
            "stage": stage,
            "seed": seed,
            "index": index,
            "status": "COMPLETE",
            "cells": cells,
            "decision_sha256": sha(directory / "decision.json"),
            "wall_seconds": time.monotonic() - start,
            "cpu_seconds": time.process_time() - cpu,
            "controls": World.controls,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "epoch": time.time(),
        }
        atomic(root / "progress" / f"{stage}-{index:04d}.json", result)
        print(json.dumps({k: v for k, v in result.items() if k != "cells"}), flush=True)
    except Exception as error:
        atomic(
            root / "progress" / f"{stage}-{index:04d}.json",
            {
                "stage": stage,
                "seed": seed,
                "index": index,
                "status": "INCOMPLETE",
                "error": str(error),
                "wall_seconds": time.monotonic() - start,
                "cpu_seconds": time.process_time() - cpu,
                "epoch": time.time(),
            },
        )
        atomic(
            root / "study_halt.json",
            {
                "stage": stage,
                "index": index,
                "seed": seed,
                "error": str(error),
                "epoch": time.time(),
            },
        )
        raise


def resource_totals(root):
    chunks = [read(p) for p in (root / "chunks").glob("chunk-*.json")]
    offline = [read(p) for p in (root / "metered").glob("*.json")]
    measured = sum(x["cpu_seconds"] for x in chunks + offline)
    reserve = read(root / "study_plan.json").get(
        "pre_registration_cpu_reserve_seconds", 600
    )
    return {
        "physics_wall_seconds": sum(x["wall_seconds"] for x in chunks),
        "cpu_seconds": measured,
        "cpu_cap_charge_seconds": measured + reserve,
    }


def chunk(root, stage):
    verify(root)
    plan = read(root / "study_plan.json")
    limits = plan["limits"]
    began, cpu = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN)
    count = 0
    prior = resource_totals(root)
    try:
        with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for index, seed in enumerate(seeds_for(plan, stage)):
                progress = root / "progress" / f"{stage}-{index:04d}.json"
                if progress.exists():
                    if read(progress)["status"] != "COMPLETE":
                        raise ValueError("Preserved incomplete parent; no replacement")
                    continue
                attempt = root / "attempts" / progress.name
                if attempt.exists():
                    atomic(
                        root / "study_halt.json",
                        {
                            "stage": stage,
                            "seed": seed,
                            "reason": "Interrupted attempt preserved; only never-started parents can resume",
                            "epoch": time.time(),
                        },
                    )
                    break
                elapsed = time.monotonic() - began
                wall = time.time() - plan["session_start_epoch"]
                if (
                    prior["physics_wall_seconds"] + elapsed + 360
                    > limits["physics_wall_seconds"]
                    or wall + 360
                    > limits["campaign_wall_seconds"]
                    - limits["analysis_reserve_seconds"]
                    or prior["cpu_cap_charge_seconds"] + elapsed * 2 + 720
                    > limits["cpu_seconds"] - limits["analysis_cpu_reserve_seconds"]
                    or sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                    > limits["artifact_bytes"] - 200_000_000
                ):
                    atomic(
                        root / "resource_boundary.json",
                        {
                            "stage": stage,
                            "prior": prior,
                            "current_chunk_seconds": elapsed,
                            "campaign_wall_seconds": wall,
                            "epoch": time.time(),
                        },
                    )
                    break
                if count >= 8 or elapsed + 360 > 840:
                    break
                atomic(
                    attempt,
                    {
                        "stage": stage,
                        "index": index,
                        "seed": seed,
                        "epoch": time.time(),
                    },
                )
                with (root / "chunks" / f"{stage}-{index:04d}.log").open("x") as stream:
                    proc = subprocess.Popen(
                        [
                            sys.executable,
                            __file__,
                            "parent",
                            str(root),
                            "--stage",
                            stage,
                            "--index",
                            str(index),
                        ],
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                    )
                    try:
                        status = proc.wait(timeout=360)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()
                        status = -15
                if status:
                    if not (root / "study_halt.json").exists():
                        atomic(
                            root / "study_halt.json",
                            {
                                "stage": stage,
                                "index": index,
                                "seed": seed,
                                "returncode": status,
                                "epoch": time.time(),
                            },
                        )
                    break
                count += 1
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        atomic(
            root / "chunks" / f"chunk-{time.time_ns()}.json",
            {
                "stage": stage,
                "parents": count,
                "wall_seconds": time.monotonic() - began,
                "cpu_seconds": after.ru_utime
                + after.ru_stime
                - cpu.ru_utime
                - cpu.ru_stime,
                "epoch": time.time(),
            },
        )
    print(
        json.dumps(
            {
                "stage": stage,
                "completed_in_chunk": count,
                "resources": resource_totals(root),
            }
        ),
        flush=True,
    )


def seal_calibration(root):
    from dual_rec.dsre.calibration import upper_bound

    verify(root)
    audit = read(root / "calibration_physics_audit.json")
    plan = read(root / "study_plan.json")
    assert audit["passed"] and audit["parents"] == len(plan["calibration_seeds"]) == 256
    if (root / "calibration_decision.json").exists():
        raise ValueError("Calibration decision already immutable")
    strata = {}
    for method in plan["methods"]:
        for action in ("continue", "recover"):
            assigned = errors = 0
            for seed in plan["calibration_seeds"]:
                decisions = read(
                    root / "calibration" / str(seed) / "outcome_labels.json"
                )
                selected = [
                    r for r in decisions["cells"] if r["proposals"][method] == action
                ]
                if selected:
                    assigned += 1
                    errors += any(
                        not r["outcomes"][action + "_value"] for r in selected
                    )
            bound = upper_bound(errors, assigned, 0.05 / 68)
            strata[method + "|" + action] = {
                "assigned_parents": assigned,
                "error_parents": errors,
                "upper": bound,
                "delta": 0.05 / 68,
                "target": 0.1,
                "enabled": bool(assigned) and bound <= 0.1,
                "status": "QUALIFIED_SOURCE_PARENT_ACTION"
                if assigned and bound <= 0.1
                else "NOT_QUALIFIED",
            }
    decision = {
        "complete_cohort": True,
        "calibration_parents": 256,
        "strata": strata,
        "scope": "Frozen new-source PickCube five-condition parent distribution, clean telemetry only. Parent-any-assigned-condition error conditional on assignment. No old-data pooling or noise transfer.",
        "plan_sha256": sha(root / "study_plan.json"),
        "physical_audit_sha256": sha(root / "calibration_physics_audit.json"),
        "epoch": time.time(),
    }
    atomic(root / "calibration_decision.json", decision)
    atomic(
        root / "calibration_seal.json",
        {"sha256": sha(root / "calibration_decision.json"), "epoch": time.time()},
    )
    print(
        json.dumps(
            {
                "calibration_sealed": True,
                "DSRE_risk": {
                    a: strata["DSRE_risk|" + a] for a in ("continue", "recover")
                },
            }
        ),
        flush=True,
    )


def seal_test(root):
    verify(root)
    plan = read(root / "study_plan.json")
    assert read(root / "calibration_decision_audit.json")["passed"]
    calibration = read(root / "calibration_decision.json")
    assert calibration["complete_cohort"] and calibration["calibration_parents"] == 256
    assert read(root / "calibration_decision_audit.json")["calibration_sha256"] == sha(
        root / "calibration_decision.json"
    )
    if (root / "test_recommendation_seal.json").exists():
        raise ValueError("Test already sealed")
    parents = {}
    for seed in plan["test_seeds"]:
        d = root / "test" / str(seed)
        assert not (d / "execution_started.json").exists()
        assert not list(d.glob("*/continue.json.gz")) and not list(
            d.glob("*/recover.json.gz")
        )
        assert read(d / "decision.json")["calibration_sha256"] == sha(
            root / "calibration_decision.json"
        )
        parents[str(seed)] = sha(d / "decision.json")
    assert len(parents) == 128
    atomic(
        root / "test_recommendation_seal.json",
        {
            "parents": parents,
            "parent_count": 128,
            "calibration_sha256": sha(root / "calibration_decision.json"),
            "scope": "All five-condition test recommendations before any test intervention outcome",
            "epoch": time.time(),
        },
    )


def control(root, stage):
    verify(root)
    target = len(seeds_for(read(root / "study_plan.json"), stage))
    while len(list((root / "progress").glob(stage + "-*.json"))) < target:
        if (root / "study_halt.json").exists() or (
            root / "resource_boundary.json"
        ).exists():
            return
        before = len(list((root / "progress").glob(stage + "-*.json")))
        subprocess.run(
            [sys.executable, __file__, "chunk", str(root), "--stage", stage], check=True
        )
        after = len(list((root / "progress").glob(stage + "-*.json")))
        atomic(
            root / (stage + "_checkpoint.json"),
            {"complete_parents": after, "registered": target, "epoch": time.time()},
        )
        if before == after:
            if (root / "study_halt.json").exists() or (
                root / "resource_boundary.json"
            ).exists():
                return
            raise ValueError(
                "No progress; lock or resource condition requires inspection"
            )
    if (root / "study_halt.json").exists() or any(
        read(p)["status"] != "COMPLETE"
        for p in (root / "progress").glob(stage + "-*.json")
    ):
        return
    if stage == "test_screen":
        seal_test(root)
    atomic(
        root / (stage + "_boundary.json"),
        {"complete": True, "parents": target, "epoch": time.time()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command", choices=["parent", "chunk", "control", "seal-calibration"]
    )
    p.add_argument("root", type=Path)
    p.add_argument(
        "--stage",
        choices=["qualification", "calibration", "test_screen", "test_outcome"],
    )
    p.add_argument("--index", type=int, default=0)
    a = p.parse_args()
    if a.command == "seal-calibration":
        seal_calibration(a.root)
    elif a.command == "parent":
        parent(a.root, a.stage, a.index)
    elif a.command == "chunk":
        chunk(a.root, a.stage)
    else:
        control(a.root, a.stage)
