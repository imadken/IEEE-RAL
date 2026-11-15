"""Separate frozen five-offset PickCube study with bounded checkpointed workers.

offset_x offsets the scripted grasp approach target, NOT the object pose or a
material property. The exact historical source is reused, including its event
timing; only this new version's registered parameter values and seeds differ.
"""

import argparse
import fcntl
import importlib.metadata
import json
import logging
import resource
import subprocess
import sys
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_paper_physics import World, initial
from dsre_recovery_audit import gz
from dsre_recovery_evidence import execute, write_gzip
from dsre_science_offline import corrupt

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.measurement import MeasurementScope, RobustRouter, bounded_evidence
from dual_rec.dsre.operational import OperationalRouter, PolicyInput
from dual_rec.dsre.repair_selection import optional_values
from dual_rec.overnight_pick import PickFault
from dual_rec.replay import jsonable
from dual_rec.validation import compare, passes

TASK = "PickCube-v1"
PROFILES = (
    ("nominal", 0.0),
    ("offset001", 0.01),
    ("offset002", 0.02),
    ("offset003", 0.03),
    ("offset_minus002", -0.02),
)


def verify(root):
    freeze = read(root / "science_freeze.json")
    for family in ("source_sha256", "input_sha256"):
        for p, h in freeze[family].items():
            if sha(Path(p)) != h:
                raise ValueError("Frozen source/input changed: " + p)
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence already sealed")


def decisions(history, frozen, router, point, cell_id, reference_id):
    output = {}
    scenarios = [
        ("clean", history, 0),
        ("bound001", history, 0.001),
        ("bound005", history, 0.005),
    ]
    for rho in (0.001, 0.005):
        scenarios += [
            (f"uniform{rho}_r{k}", corrupt(history, rho, cell_id, k), rho)
            for k in range(3)
        ]
    for scenario, h, rho in scenarios:
        evidence = bounded_evidence(
            h,
            MeasurementScope(
                coordinate_error_m=rho,
                decision_time=history.current.time,
                reference_scope_identity=reference_id,
                source_regime="OOD_FIVE_APPROACH_OFFSETS_V12",
            ),
        )
        measured = tuple(f.measured for f in evidence.facts)
        packet = PolicyInput(task=TASK, values=measured[:7], full_values=measured)
        p = point.route(packet)
        r = router.route(evidence.packet(TASK))
        if rho == 0:
            assert p == r
        margin = dict(p["DSRE_strict"])
        if any(f.invariant is None for f in evidence.facts[:7]):
            margin.update(action=None, evidence=[])
        output[scenario] = {
            "measurement": evidence.model_dump(mode="json"),
            "point_proposal": p,
            "robust_proposal": r,
            "margin_all_inputs": {"margin_DSRE_strict": margin},
            "population_calibration": "UNQUALIFIED_OOD_NO_CLEAN_BOUND_TRANSFER",
        }
    return output


def screen(seed, condition, offset, directory, root, router, point, deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("Screen parent deadline")
    directory.mkdir(parents=True, exist_ok=False)
    case, prefix = initial(seed, PickFault(name=condition, offset_x=offset))
    World.controls += len(case["prefix_actions"])
    world = World(TASK, seed, "nominal")
    world.wrapped._max_episode_steps = 200
    try:
        states = [world.state()]
        for action in case["prefix_actions"]:
            states.append(world.step(action))
        assert len(states) == len(prefix)
        if not all(
            passes(compare(jsonable(a), jsonable(b)))
            for a, b in zip(prefix, states, strict=True)
        ):
            raise ValueError("Full canonical prefix/contact replay mismatch")
        current = world.state(refresh=True)
        history = ObservationHistory(
            first=observed_frame(prefix[0]["time"], prefix[0]["observation"]),
            current=observed_frame(current["time"], current["observation"]),
        )
        started = time.perf_counter()
        output = decisions(
            history,
            None,
            router,
            point,
            f"{TASK}/{seed}/{condition}",
            sha(root / "frozen_routers.json"),
        )
        raw = {
            "cell": {"task": TASK, "seed": seed, "condition": condition},
            "study_version": "SCIENCE_V12_FIVE_APPROACH_OFFSETS",
            "offset_x_m": offset,
            "fault_spec": case["evaluation_only_fault"],
            "offset_semantics": "Prefix approach target offset; no object translation/material edit",
            "prefix": jsonable(prefix),
            "prefix_actions": case["prefix_actions"],
            "canonical_start": jsonable(current),
            "canonical_controller_memory": jsonable(world.adapter.capture().custom),
            "model": {
                "task": TASK,
                "edit": jsonable(world.edit),
                "versions": {
                    p: importlib.metadata.version(p)
                    for p in ("mani-skill", "sapien", "torch", "numpy")
                },
            },
            "summary": {
                "task": TASK,
                "seed": seed,
                "condition": condition,
                "features": feature_values(history),
                "optional_features": optional_values(history),
                "runtime_history": history.model_dump(mode="json"),
                "initial_success": bool(current["success"]),
            },
            "scenarios": output,
            "route_ms": (time.perf_counter() - started) * 1000,
            "screened_epoch": time.time(),
        }
        write_gzip(directory / "screen.json.gz", raw)
        return raw
    except Exception as e:
        write_gzip(
            directory / "screen_failure.json.gz",
            {"case": case, "prefix": prefix, "error": str(e)},
        )
        raise
    finally:
        world.close()


def parent(root, stage, index):
    verify(root)
    plan = read(root / "study_plan.json")
    seed = (
        plan["pilot_seeds"][index] if stage == "pilot" else plan["primary_seeds"][index]
    )
    directory = root / ("pilot" if stage == "pilot" else "prospective") / str(seed)
    started = time.monotonic()
    cpu = time.process_time()
    deadline = started + 300
    router = RobustRouter(read(root / "frozen_routers.json"))
    point = OperationalRouter(read(root / "frozen_routers.json"))
    profiles = (
        PROFILES
        if stage == "pilot"
        else tuple(
            (c, o)
            for c, o in PROFILES
            if c in read(root / "pilot_qualification_seal.json")["qualified_conditions"]
        )
    )
    try:
        if stage in ("pilot", "screen"):
            cells = []
            for condition, offset in profiles:
                d = directory / condition
                if stage == "pilot":
                    try:
                        raw = screen(
                            seed, condition, offset, d, root, router, point, deadline
                        )
                        out = []
                        for repeat in (0, 1):
                            repeat_dir = d / f"repeat{repeat}"
                            repeat_dir.mkdir()
                            out.append(
                                [
                                    execute(raw, mode, repeat_dir, deadline)
                                    for mode in ("continue", "recover")
                                ]
                            )
                        cells.append(
                            {
                                "condition": condition,
                                "screen_sha256": sha(d / "screen.json.gz"),
                                "outcomes": out,
                                "status": "QUALIFICATION_ATTEMPT_COMPLETE",
                            }
                        )
                    except Exception as e:
                        logging.getLogger(__name__).exception(
                            "Pilot profile unqualified; preserve attempt"
                        )
                        atomic(
                            d / "failure.json",
                            {
                                "condition": condition,
                                "seed": seed,
                                "error": str(e),
                                "epoch": time.time(),
                            },
                        )
                        cells.append(
                            {
                                "condition": condition,
                                "status": "UNQUALIFIED",
                                "error": str(e),
                            }
                        )
                else:
                    raw = screen(
                        seed, condition, offset, d, root, router, point, deadline
                    )
                    cells.append(
                        {
                            "condition": condition,
                            "screen_sha256": sha(d / "screen.json.gz"),
                            "sealed_epoch": raw["screened_epoch"],
                        }
                    )
            if stage == "screen":
                atomic(
                    directory / "recommendations.json",
                    {
                        "seed": seed,
                        "split": "development" if index < 64 else "confirmation",
                        "cells": cells,
                        "source_freeze_sha256": sha(root / "science_freeze.json"),
                        "epoch": time.time(),
                    },
                )
        else:
            seal = read(root / "prospective_recommendation_seal.json")
            assert sha(directory / "recommendations.json") == seal["parents"][str(seed)]
            atomic(
                directory / "execution_started.json",
                {
                    "epoch": time.time(),
                    "cohort_seal_sha256": sha(
                        root / "prospective_recommendation_seal.json"
                    ),
                },
            )
            rec = read(directory / "recommendations.json")
            cells = []
            for cell in rec["cells"]:
                d = directory / cell["condition"]
                assert sha(d / "screen.json.gz") == cell["screen_sha256"]
                raw = gz(d / "screen.json.gz")
                out = [
                    execute(raw, mode, d, deadline) for mode in ("continue", "recover")
                ]
                cells.append({"condition": cell["condition"], "outcomes": out})
        result = {
            "stage": stage,
            "seed": seed,
            "index": index,
            "status": "COMPLETE",
            "cells": cells,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": time.process_time() - cpu,
            "controls": World.controls,
            "epoch": time.time(),
        }
        atomic(root / "progress" / f"{stage}-{index:04d}.json", result)
        print(json.dumps({k: v for k, v in result.items() if k != "cells"}), flush=True)
    except Exception as e:
        atomic(
            root / "progress" / f"{stage}-{index:04d}.json",
            {
                "stage": stage,
                "seed": seed,
                "index": index,
                "status": "INCOMPLETE",
                "error": str(e),
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu,
                "controls": World.controls,
            },
        )
        atomic(
            root / "study_halt.json",
            {
                "stage": stage,
                "index": index,
                "seed": seed,
                "reason": str(e),
                "epoch": time.time(),
            },
        )
        raise


def seal_cohort(root):
    plan = read(root / "study_plan.json")
    parents = {}
    for seed in plan["primary_seeds"]:
        d = root / "prospective" / str(seed)
        assert not (d / "execution_started.json").exists()
        assert not list(d.glob("*/continue.json.gz")) and not list(
            d.glob("*/recover.json.gz")
        )
        parents[str(seed)] = sha(d / "recommendations.json")
    atomic(
        root / "prospective_recommendation_seal.json",
        {
            "parents": parents,
            "count": 192,
            "split": {"development": 64, "confirmation": 128},
            "qualified_conditions": read(root / "pilot_qualification_seal.json")[
                "qualified_conditions"
            ],
            "scope": "ALL parents/conditions/scenarios/methods before ANY primary continuation",
            "epoch": time.time(),
        },
    )


def chunk(root, stage):
    verify(root)
    if (root / "study_halt.json").exists():
        raise ValueError("Scientific halt")
    plan = read(root / "study_plan.json")
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    seeds = plan["pilot_seeds"] if stage == "pilot" else plan["primary_seeds"]
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = [read(p) for p in (root / "chunks").glob("chunk-*.json")]
        used = sum(p["wall_seconds"] for p in prior)
        count = 0
        for index, seed in enumerate(seeds):
            p = root / "progress" / f"{stage}-{index:04d}.json"
            if p.exists():
                if read(p)["status"] != "COMPLETE":
                    raise ValueError("Incomplete preserved parent")
                continue
            attempt = root / "attempts" / f"{stage}-{index:04d}.json"
            if attempt.exists():
                atomic(
                    root / "study_halt.json",
                    {
                        "reason": "Interrupted attempt preserved, no replacement",
                        "stage": stage,
                        "index": index,
                        "seed": seed,
                        "epoch": time.time(),
                    },
                )
                break
            now = time.monotonic()
            elapsed = now - started
            from_start = (
                time.time() - read(root / "study_plan.json")["session_start_epoch"]
            )
            bytes_used = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
            if (
                used + elapsed > 36000 - 330
                or from_start > 57600 - 3600 - 330
                or bytes_used > 4 * 1024**3 - 150_000_000
            ):
                atomic(
                    root / "resource_boundary.json",
                    {
                        "used_simulation_seconds": used + elapsed,
                        "session_seconds": from_start,
                        "bytes": bytes_used,
                        "stage": stage,
                        "epoch": time.time(),
                    },
                )
                break
            if count >= 12 or elapsed >= 840 - 330:
                break
            atomic(
                attempt,
                {"stage": stage, "seed": seed, "index": index, "epoch": time.time()},
            )
            with (root / "chunks" / f"{stage}-{index:04d}.log").open("x") as stream:
                child = subprocess.Popen(
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
                    status = child.wait(timeout=330)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    status = -15
            if status:
                if not (root / "study_halt.json").exists():
                    atomic(
                        root / "study_halt.json",
                        {
                            "stage": stage,
                            "index": index,
                            "seed": seed,
                            "reason": "Worker runtime failure",
                            "returncode": status,
                            "epoch": time.time(),
                        },
                    )
                break
            count += 1
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        atomic(
            root / "chunks" / f"chunk-{len(prior):04d}.json",
            {
                "stage": stage,
                "parents": count,
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": after.ru_utime
                + after.ru_stime
                - before.ru_utime
                - before.ru_stime,
                "epoch": time.time(),
            },
        )
        print(
            json.dumps({"stage": stage, "parents": count, "used_before": used}),
            flush=True,
        )


def control(root, stage):
    verify(root)
    assert read(root / "offline_audit.json")["passed"]
    if stage != "pilot":
        assert read(root / "pilot_qualification_seal.json")["qualified_conditions"]
    if stage == "outcome":
        assert (root / "prospective_recommendation_seal.json").exists()
    n = 5 if stage == "pilot" else 192
    while len(list((root / "progress").glob(stage + "-*.json"))) < n:
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
            {"completed": after, "registered": n, "epoch": time.time()},
        )
        if after == before:
            raise ValueError("No progress")
    if stage == "screen":
        seal_cohort(root)
    atomic(
        root / (stage + "_boundary.json"),
        {"complete": True, "parents": n, "epoch": time.time()},
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["parent", "chunk", "control"])
    p.add_argument("root", type=Path)
    p.add_argument("--stage", choices=["pilot", "screen", "outcome"], required=True)
    p.add_argument("--index", type=int, default=0)
    a = p.parse_args()
    {
        "parent": lambda: parent(a.root, a.stage, a.index),
        "chunk": lambda: chunk(a.root, a.stage),
        "control": lambda: control(a.root, a.stage),
    }[a.command]()
