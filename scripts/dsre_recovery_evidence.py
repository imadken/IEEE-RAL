"""Frozen rare-action calibration and disjoint paired confirmation orchestration.

Reuses registered physics, predicates, router and action equations unchanged.
"""

import argparse
import fcntl
import gzip
import importlib.metadata
import json
import resource
import subprocess
import sys
import time
from itertools import product
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_observations import packet_from_summary
from dsre_paper_physics import Cell, World, action_for, initial

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.dsre.operational import (
    METHODS,
    OperationalRouter,
    PolicyInput,
    gated_action,
)
from dual_rec.dsre.repair_selection import optional_values
from dual_rec.overnight_pick import PickFault
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes

PRIOR = Path("results/dsre-operational/20261114T180630Z")
TASK = "PickCube-v1"
CONDITIONS = ("nominal", "offset002")


def write_gzip(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", compresslevel=6) as stream:
        json.dump(jsonable(value), stream, allow_nan=False)


def admit(proposals, counts, target=112):
    """Stop each method at its OWN fixed assigned-parent quota, before outcomes."""
    return [
        m
        for m in METHODS
        if counts[m] < target and any(p[m]["action"] == "recover" for p in proposals)
    ]


def prepare(root):
    if (root / "plan.json").exists():
        raise ValueError("Already registered")
    frozen = read(PRIOR / "frozen_routers.json")
    (root / "frozen_routers.json").write_bytes(
        (PRIOR / "frozen_routers.json").read_bytes()
    )
    router = OperationalRouter(frozen)
    reachable = {m: False for m in METHODS}
    signatures = [list(x) + [False] * 5 for x in product((False, True), repeat=7)]
    signatures += [
        r["features"] for r in frozen["tasks"][TASK]["1"]["full_table"]["rows"]
    ]
    for x in signatures:
        decisions = router.route(
            PolicyInput(task=TASK, values=tuple(x[:7]), full_values=tuple(x))
        )
        for m in METHODS:
            reachable[m] |= decisions[m]["action"] == "recover"
    plan = {
        "base": "9f42bb8df9d0e9a695ae1c7eda3bb00c8af72de3",
        "task": TASK,
        "conditions": list(CONDITIONS),
        "additional_assigned_target": 112,
        "calibration_seeds": list(range(11000000, 11004000)),
        "test_seeds": list(range(12000000, 12000160)),
        "qualification_seed": 8000000,
        "reachable_recover": reachable,
        "stop": "First 112 assigned parents PER method, irrespective of error. No later parents enter that method. All reachable methods finish or 4000 screens / 16h simulation / 4GB boundary. No replacement. Any scientific replay/provenance failure halts new physics.",
        "calibration_sampling": "Common independent seed stream; selection exclusively frozen predecision assignment in either condition. Recover only in each assigned condition. Parent error is ANY failed assigned recover. Method-specific admission prevents stopping on another policy from selecting its sample size.",
        "risk": {
            "target": 0.1,
            "family_alpha": 0.05,
            "strata": 68,
            "per_stratum_alpha": 0.05 / 68,
        },
        "pooling": "Pool original compatible method-specific Pick recover parents with its new quota; report old/new/pooled separately. Also require independently fixed-size new-only bound <= .10 for enabling a previously disabled recovery gate. Historical continue and Push gates unchanged. Partial quotas do not qualify new gates.",
        "test": "160 disjoint independent seed parents, two registered conditions each; seal all17 proposals and calibrated decisions for BOTH conditions before either continuation outcome. Both 70-control continue/recover reset continuations. STOP zero selective completion, no physical completion imputation.",
        "analysis": "Parent bootstrap 4000 draws seed2026111501; exact parent-action bounds alpha .05/68; required recovery = C false R true; harm = C true R false; all four paired classes, coverage, errors, abstention and initial-success maintenance; all17 own gates. No outcome-selected thresholds, seeds or contrasts.",
        "limits": {
            "simulation_wall_seconds": 57600,
            "parent_seconds": 120,
            "chunk_parents": 20,
            "chunk_seconds": 840,
            "new_bytes": 4 * 1024**3,
        },
        "registered_epoch": time.time(),
    }
    atomic(root / "plan.json", plan)
    old = read(PRIOR / "confirmation_freeze.json")
    inputs = dict(old["input_sha256"])
    inputs.update(
        {str(root / p): sha(root / p) for p in ("plan.json", "frozen_routers.json")}
    )
    sources = dict(old["source_sha256"])
    sources["scripts/dsre_recovery_evidence.py"] = sha(Path(__file__))
    atomic(
        root / "confirmation_freeze.json",
        {
            "source_sha256": sources,
            "input_sha256": inputs,
            "registered_epoch": time.time(),
        },
    )
    for folder in (
        "attempts",
        "progress",
        "chunks",
        "calibration",
        "test",
        "qualification",
    ):
        (root / folder).mkdir(exist_ok=True)
    print(
        json.dumps(
            {"reachable_recover": reachable, "plan_sha256": sha(root / "plan.json")}
        ),
        flush=True,
    )


def screen(seed, condition, directory, frozen, router, deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("Predecision parent reserve")
    directory.mkdir(parents=True, exist_ok=False)
    case, prefix = initial(
        seed,
        PickFault(name=condition, offset_x=0.02 if condition == "offset002" else 0),
    )
    world = World(TASK, seed, "nominal")
    world.wrapped._max_episode_steps = 200
    try:
        states = [world.state()]
        for command in case["prefix_actions"]:
            states.append(world.step(command))
        errors = [
            compare(jsonable(a), jsonable(b))
            for a, b in zip(prefix, states, strict=True)
        ]
        if not all(passes(e) for e in errors):
            raise ValueError("Canonical screening prefix/contact mismatch")
        current = world.state(refresh=True)
        history = ObservationHistory(
            first=observed_frame(prefix[0]["time"], prefix[0]["observation"]),
            current=observed_frame(current["time"], current["observation"]),
        )
        summary = {
            "task": TASK,
            "seed": seed,
            "condition": condition,
            "features": feature_values(history),
            "optional_features": optional_values(history),
            "initial_success": bool(current["success"]),
        }
        packet = packet_from_summary(summary, frozen)
        started = time.perf_counter()
        proposals = router.route(packet)
        route_ms = (time.perf_counter() - started) * 1000
        raw = {
            "cell": Cell(task=TASK, seed=seed, condition=condition).model_dump(),
            "prefix": jsonable(prefix),
            "prefix_actions": case["prefix_actions"],
            "canonical_start": jsonable(current),
            "canonical_controller_memory": jsonable(world.adapter.capture().custom),
            "model": {
                "task": TASK,
                "condition": condition,
                "edit": jsonable(world.edit),
                "versions": {
                    p: importlib.metadata.version(p)
                    for p in ("mani-skill", "sapien", "torch", "numpy")
                },
            },
            "summary": summary,
            "packet": packet.model_dump(mode="json"),
            "proposals": proposals,
            "route_ms": route_ms,
            "screened_epoch": time.time(),
        }
        write_gzip(directory / "screen.json.gz", raw)
        return raw
    except Exception as error:
        write_gzip(
            directory / "screen_failure.json.gz",
            {"cell": case, "prefix": prefix, "error": str(error)},
        )
        raise
    finally:
        world.close()


def execute(raw, mode, directory, deadline):
    world = World(TASK, raw["cell"]["seed"], "nominal")
    world.wrapped._max_episode_steps = 200
    diagnostic = {"mode": mode, "phase": "prefix"}
    try:
        states = [world.state()]
        for command in raw["prefix_actions"]:
            states.append(world.step(command))
        memory = jsonable(world.adapter.capture().custom)
        start = world.state(refresh=True)
        errors = [
            compare(a, jsonable(b)) for a, b in zip(raw["prefix"], states, strict=True)
        ]
        diagnostic.update(
            prefix_states=jsonable(states),
            controller_memory=memory,
            start=jsonable(start),
            model_edit=jsonable(world.edit),
            prefix_errors=errors,
        )
        if (
            not all(passes(e) for e in errors)
            or memory != raw["canonical_controller_memory"]
            or jsonable(world.edit) != raw["model"]["edit"]
            or not passes(compare(raw["canonical_start"], jsonable(start)))
        ):
            raise ValueError("Continuation prefix/controller/model/contact mismatch")
        tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
        frames = []
        diagnostic.update(phase="future", frames=frames, initial_tcp=tcp.tolist())
        for j in range(70):
            if time.monotonic() >= deadline:
                raise TimeoutError("Parent continuation reserve")
            command = action_for(world, mode, j, tcp)
            before = world.state()
            state = world.step(command)
            frames.append(
                {
                    "before_observation": jsonable(before["observation"]),
                    "action": jsonable(command),
                    "state": jsonable(state),
                }
            )
        diagnostic.update(
            terminal_success=bool(frames[-1]["state"]["success"]),
            completed_epoch=time.time(),
            status="QUALIFIED",
        )
        write_gzip(directory / (mode + ".json.gz"), diagnostic)
        return {
            "action": mode,
            "success": diagnostic["terminal_success"],
            "source": str(directory / (mode + ".json.gz")),
            "sha256": sha(directory / (mode + ".json.gz")),
            "completed_epoch": diagnostic["completed_epoch"],
        }
    except Exception as error:
        diagnostic["error"] = str(error)
        write_gzip(directory / (mode + "_failure.json.gz"), diagnostic)
        raise
    finally:
        world.close()


def parent(root, stage, index):
    verify_freeze(root)
    plan = read(root / "plan.json")
    seed = (
        plan[stage + "_seeds"][index]
        if stage != "qualification"
        else plan["qualification_seed"]
    )
    destination = root / stage / str(seed)
    started = time.monotonic()
    cpu = time.process_time()
    deadline = started + plan["limits"]["parent_seconds"]
    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    try:
        raws = [
            screen(seed, c, destination / c, frozen, router, deadline)
            for c in CONDITIONS
        ]
        counts = (
            read(root / "counts.json")
            if (root / "counts.json").exists()
            else dict.fromkeys(METHODS, 0)
        )
        admitted = (
            admit([r["proposals"] for r in raws], counts)
            if stage == "calibration"
            else []
        )
        calibration = (
            read(root / "calibration_decision.json") if stage == "test" else None
        )
        if calibration:
            assert (
                sha(root / "calibration_decision.json")
                == read(root / "calibration_seal.json")["sha256"]
            )
        decision = {
            "seed": seed,
            "stage": stage,
            "index": index,
            "admitted_methods": admitted,
            "prior_counts": counts,
            "screens": {c: sha(destination / c / "screen.json.gz") for c in CONDITIONS},
            "all_actions": [
                {
                    m: {
                        "proposal": r["proposals"][m]["action"],
                        "gated": gated_action(
                            m, TASK, r["proposals"][m]["action"], calibration["strata"]
                        )
                        if calibration
                        else None,
                    }
                    for m in METHODS
                }
                for r in raws
            ],
            "sealed_epoch": time.time(),
            "calibration_sha256": sha(root / "calibration_decision.json")
            if calibration
            else None,
        }
        atomic(destination / "decision.json", decision)
        decision_sha = sha(destination / "decision.json")
        cells = []
        for condition, raw in zip(CONDITIONS, raws, strict=True):
            modes = (
                ["continue", "recover"]
                if stage in ("test", "qualification")
                else (
                    ["recover"]
                    if any(raw["proposals"][m]["action"] == "recover" for m in admitted)
                    else []
                )
            )
            outcomes = [
                execute(raw, mode, destination / condition, deadline) for mode in modes
            ]
            cells.append({"condition": condition, "outcomes": outcomes})
        if sha(destination / "decision.json") != decision_sha:
            raise ValueError("Decision changed after outcomes")
        result = {
            "stage": stage,
            "index": index,
            "seed": seed,
            "status": "COMPLETE",
            "admitted_methods": admitted,
            "cells": cells,
            "decision_sha256": decision_sha,
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": time.process_time() - cpu,
            "physics_control_steps": World.controls,
        }
        atomic(root / "progress" / f"{stage}-{index:04d}.json", result)
        if stage == "calibration":
            for m in admitted:
                counts[m] += 1
            atomic(root / "counts.json", counts)
        print(json.dumps(result), flush=True)
    except Exception as error:
        atomic(
            root / "progress" / f"{stage}-{index:04d}.json",
            {
                "status": "FAILURE",
                "stage": stage,
                "index": index,
                "seed": seed,
                "error_type": type(error).__name__,
                "error": str(error),
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": time.process_time() - cpu,
            },
        )
        atomic(
            root / "study_halt.json",
            {"stage": stage, "seed": seed, "reason": str(error), "epoch": time.time()},
        )
        raise


def chunk(root, stage):
    verify_freeze(root)
    if (root / "study_halt.json").exists():
        raise ValueError("Scientific halt; no new physics")
    plan = read(root / "plan.json")
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = [read(p) for p in (root / "chunks").glob("*.json")]
        remaining = 57600 - sum(p["wall_seconds"] for p in prior)
        if (
            remaining < 120
            or sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
            > 4 * 1024**3 - 100_000_000
        ):
            atomic(
                root / "resource_boundary.json",
                {"simulation_remaining": remaining, "epoch": time.time()},
            )
            return
        count = 0
        seeds = (
            plan[stage + "_seeds"]
            if stage != "qualification"
            else [plan["qualification_seed"]]
        )
        for index, seed in enumerate(seeds):
            if stage == "calibration":
                counts = (
                    read(root / "counts.json")
                    if (root / "counts.json").exists()
                    else dict.fromkeys(METHODS, 0)
                )
                if all(
                    counts[m] >= 112 or not plan["reachable_recover"][m]
                    for m in METHODS
                ):
                    break
            attempt = root / "attempts" / f"{stage}-{index:04d}.json"
            if attempt.exists():
                if not (root / "progress" / attempt.name).exists():
                    atomic(
                        root / "study_halt.json",
                        {
                            "reason": "Interrupted parent; preserved, never replaced",
                            "stage": stage,
                            "index": index,
                        },
                    )
                    break
                continue
            if count >= 20 or time.monotonic() - started >= min(840, remaining - 120):
                break
            atomic(
                attempt,
                {"stage": stage, "index": index, "seed": seed, "epoch": time.time()},
            )
            directory = root / "chunks"
            log = directory / f"{stage}-{index:04d}.log"
            with log.open("x") as stream:
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
                            "reason": "Parent process failure",
                            "stage": stage,
                            "index": index,
                            "status": status,
                        },
                    )
                break
            count += 1
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        atomic(
            root / "chunks" / f"chunk-{len(prior):04d}.json",
            {
                "stage": stage,
                "completed_parents": count,
                "wall_seconds": time.monotonic() - started,
                "cpu_seconds": after.ru_utime
                + after.ru_stime
                - before.ru_utime
                - before.ru_stime,
                "epoch": time.time(),
            },
        )
        print(
            json.dumps(
                {
                    "stage": stage,
                    "completed": count,
                    "counts": read(root / "counts.json")
                    if (root / "counts.json").exists()
                    else None,
                    "halted": (root / "study_halt.json").exists(),
                }
            ),
            flush=True,
        )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["prepare", "chunk", "parent"])
    p.add_argument("root", type=Path)
    p.add_argument(
        "--stage",
        choices=["calibration", "test", "qualification"],
        default="calibration",
    )
    p.add_argument("--index", type=int, default=0)
    a = p.parse_args()
    if a.command == "prepare":
        prepare(a.root)
    elif a.command == "chunk":
        chunk(a.root, a.stage)
    else:
        parent(a.root, a.stage, a.index)


if __name__ == "__main__":
    main()
