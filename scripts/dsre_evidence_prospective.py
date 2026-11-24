"""Fixed prospective cohorts, outcome-blind acquisition, and atomic bounded chunks."""

import argparse
import gzip
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from dsre_evidence_campaign import child
from dsre_evidence_development import persist as frozen_persist
from dsre_evidence_tasks import NAV_VOCAB, PEG_V2_VOCAB

from dual_rec.dsre.features import PRIMARY
from dual_rec.evidence_aware.schema import OneAction, Scope
from dual_rec.evidence_aware.views import arm, condition, hashed, seed, sha

OLD = Path("results/dsre-evidence-aware/20261117-first-session")
ROOT = Path("results/dsre-evidence-aware/20261117-prospective")
TASKS = ("PointMaze_UMaze-v3", "PickCube-v1", "PegInsertionSide-v1")
STRATEGIES = ("witness", "all_logs", "all_pairs", "uniform_mix", "decision_uncertainty")
BUDGETS = (64, 128, 256, 512)


def persist(path, value):
    if path.name != "SOURCE_GUARD_FAILURE.json":
        return frozen_persist(path, value)
    # Concurrent in-flight parents retain every witness; the first guard wins.
    witness = (
        path.parent
        / "guard_witnesses"
        / f"{value['spec']['seed']}-{value['stage']}.json"
    )
    frozen_persist(witness, value)
    try:
        os.link(witness, path)
    except FileExistsError:
        pass


def read(path):
    with gzip.open(path, "rt") if str(path).endswith(".gz") else path.open() as stream:
        return json.load(stream)


def identity(spec):
    return (
        f"{hashed('prospective-parent:' + spec['task'] + ':' + str(spec['seed'])):064x}"
    )


def vocabulary(task):
    return tuple(
        PRIMARY if task == TASKS[1] else NAV_VOCAB if task == TASKS[0] else PEG_V2_VOCAB
    )


def scope(task):
    return Scope(
        task=task,
        controller_sha256=sha(
            Path(
                "scripts/dsre_evidence_grasp.py"
                if task == TASKS[1]
                else "scripts/dsre_evidence_tasks.py"
            )
        ),
        horizon=70 if task == TASKS[1] else 200 if task == TASKS[0] else 400,
        outcome="source terminal success; absorbing navigation goal; observed stopped-macro endpoint on planner abort, otherwise MISSING",
        population="independent original sealed prospective seeds; one hash-assigned condition from the registered five-condition mixture",
        observation_protocol="Peg-observation-v2"
        if task == TASKS[2]
        else "original six measured predecision predicates",
    )


def register(root):
    """Inspect identifiers and file metadata only, never new cohort outcomes."""
    original = read(OLD / "prospective_manifest.json")
    ready = read(OLD / "prospective_ready_manifest.json")
    assert ready["cohorts"] == original["cohorts"]
    cohorts = ready["cohorts"]
    used, future, past = set(), set(), set()
    offsets = {
        TASKS[0]: [[0, 0], [0.35, 0], [-0.35, 0], [0, 0.35], [0, -0.35]],
        TASKS[1]: [0.0, 0.01, 0.02, 0.03, -0.02],
        TASKS[2]: [0.0, 0.003, -0.003, 0.006, -0.006],
    }
    for task, phases in cohorts.items():
        for phase, rows in phases.items():
            assert (
                len(rows)
                == {
                    "pilot": 10,
                    "development": 64,
                    "discovery": 128,
                    "calibration": 1024,
                    "test": 256,
                }[phase]
            )
            for index, row in enumerate(rows):
                number = row["seed"]
                assert number == seed(task, phase, index) and number not in used
                assert (
                    row["offset"]
                    == offsets[task][
                        index // 2 if phase == "pilot" else condition(task, str(number))
                    ]
                )
                used.add(number)
                (future if phase in ("discovery", "calibration", "test") else past).add(
                    number
                )
    historic = set()
    for current, dirs, files in os.walk("results"):
        dirs[:] = [
            d
            for d in dirs
            if d
            not in ("env", "navigation_env", "cache", "review_packet", "prior_packet")
        ]
        for name in dirs + files:
            match = re.match(r"^(\d{3,})(?:-|\.|$)", name)
            if match:
                historic.add(int(match[1]))
    # Cold inventories preserve path identities for files moved during cleanup.
    cold = []
    for path in Path("results/storage-cleanup/20261117").glob("*.json.gz"):
        with gzip.open(path, "rt") as stream:
            text = stream.read()
        historic.update(int(v) for v in re.findall(r"/(\d{3,})(?=[/.-])", text))
        cold.append({"path": str(path), "sha256": sha(path)})
    assert not future & historic and not future & past
    pilot = []
    for index in range(10):
        number = seed(TASKS[2], "source-v2-qualification", index)
        assert number not in used | historic
        used.add(number)
        pilot.append(
            {
                "task": TASKS[2],
                "phase": "source-v2-qualification",
                "index": index,
                "seed": number,
                "offset": offsets[TASKS[2]][index // 2],
                "observation_protocol": "Peg-observation-v2",
            }
        )
    persist(
        root / "registration.json",
        {
            "epoch": time.time(),
            "base_commit": "6525dc6bf79a96e798d2d94c6778eae81d7b8304",
            "design_commit": "f634207",
            "original_manifest_sha256": sha(OLD / "prospective_manifest.json"),
            "ready_manifest_sha256": sha(OLD / "prospective_ready_manifest.json"),
            "cohorts": cohorts,
            "source_v2_pilot": pilot,
            "historical_numeric_ids_checked": len(historic),
            "cold_inventories": cold,
            "overlaps": [],
            "task_order": list(TASKS),
            "primary": {
                "harm": 0.10,
                "gain": 0.05,
                "delta_L": 0.025,
                "delta_P": 0.025,
                "per_tail": ".025/(4K)",
                "K_max": 4,
            },
            "budgets": list(BUDGETS),
            "acquisition": {
                "base": "first512 calibration by registered index",
                "candidates": "remaining512 calibration; all predecision observations collected before any calibration outcomes",
                "ranking": "discovery-only diagnostics, mass descending then leaf index; round-robin nonempty leaves",
                "within_leaf": "SHA256 acquisition-parent ordering independent of outcomes and assigned action",
                "pair_cost": 2,
                "log_cost": 1,
                "primary_budget": 512,
                "curves": "descriptive; individual fixed leaf confidence families only, no simultaneous cross-strategy or budget claim",
                "final_rule": "all acquisition lists frozen before base or candidate outcomes; no adaptive updates; no replacement of failures",
            },
            "limits": {
                "physics_wall_seconds": 18 * 3600,
                "audit_reserve_seconds": 2 * 3600,
                "compressed_artifact_bytes": 5 * 1024**3,
                "chunk_parents": 16,
                "subprocess_seconds_max": 180,
            },
            "endpoint": "prefix failure has no checkpoint; stopped post-action abort uses source-evaluated observed endpoint only; missing not imputed",
            "missing_analysis": "No PAC qualification on complete-case-selected populations; any unavailable checkpoint/label halts domain inference and reports worst/best identification bounds.",
            "estimands": [
                "parent intervention harm",
                "conditional useful gain",
                "qualified coverage",
                "default-continue completion",
                "required rescues",
                "futile attempts",
                "harmful attempts",
                "execution cost",
                "literal count",
            ],
            "test_access": "test outcomes remain unopened until all discovery, calibration, acquisition and model freezes",
        },
    )
    nav = root / "navigation_env"
    if not nav.exists():
        nav.symlink_to((OLD / "navigation_env").absolute(), target_is_directory=True)
    print(
        json.dumps(
            {
                "registration": "FROZEN",
                "old_ids": len(historic),
                "future_parents": len(future),
                "source_v2_pilot": 10,
            }
        ),
        flush=True,
    )


def bounded_child(root, spec, action, label):
    receipts = list((root / "physics").glob("*/*/*/*.execution.json"))
    total = 0.0
    for receipt in receipts:
        try:
            total += read(receipt)["wall_seconds"]
        except json.JSONDecodeError:
            # Another isolated parent may be committing its receipt now.
            total += 180.0
    size = sum(
        p.stat().st_size
        for p in root.rglob("*")
        if p.is_file() and not p.is_relative_to(root / "navigation_env")
    )
    if total >= 16 * 3600 - 720 or size >= 5 * 1024**3 - 256 * 1024**2:
        raise RuntimeError(
            "REGISTERED_RESOURCE_BOUNDARY: preserve cohort and resume at exact parent"
        )
    return child(root, spec, action, label)


def qualify(root):
    from dsre_evidence_audit import check_peg, equal

    registration = read(root / "registration.json")
    attempts = []
    for spec in registration["source_v2_pilot"]:
        branches = {}
        for a in ("c", "r"):
            branches[a] = bounded_child(root, spec, a, a)
            if branches[a]["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                branches[a + "_repeat"] = bounded_child(root, spec, a, a + "_repeat")
        differences = []
        try:
            for a in ("c", "r"):
                b = branches[a]
                assert b["status"] == "COMPLETE", (
                    b["status"] + ": " + b.get("error", "")
                )
                assert b["feature_telemetry"][4] is None and len(b["features"]) == 5
                equal(
                    b["features"],
                    [v for i, v in enumerate(b["feature_telemetry"]) if i != 4],
                )
                check_peg(b, b["geometry"])
                assert len(b["post"]) == len(b["post_controls"]) == 400
                for key in (
                    "prefix",
                    "prefix_controls",
                    "checkpoint",
                    "features",
                    "post",
                    "post_controls",
                    "success",
                ):
                    try:
                        equal(b[key], branches[a + "_repeat"][key])
                    except AssertionError:
                        raise AssertionError(
                            a + ": repeat first differing channel " + key
                        ) from None
            for key in ("prefix", "prefix_controls", "checkpoint", "features"):
                try:
                    equal(branches["c"][key], branches["r"][key])
                except AssertionError:
                    raise AssertionError("C/R first differing channel " + key) from None
        except (AssertionError, KeyError) as error:
            differences.append(str(error))
        attempts.append(
            {
                "spec": spec,
                "qualified": not differences,
                "first_difference": differences[:1],
                "statuses": {k: b["status"] for k, b in branches.items()},
            }
        )
        print(
            json.dumps(
                {
                    "G1_index": spec["index"],
                    "qualified": not differences,
                    "first_difference": differences[:1],
                }
            ),
            flush=True,
        )
    usable = sum(a["qualified"] for a in attempts)
    # Any replay/measurement inconsistency is a hard guard even with >=8 checkpoints.
    failed_replay = any(
        a["first_difference"] and "differing channel" in a["first_difference"][0]
        for a in attempts
    )
    persist(
        root / "G1_source_v2_qualification.json",
        {
            "technical_pass": usable >= 8 and not failed_replay,
            "usable_parents": usable,
            "attempts": attempts,
            "minimum_usable": 8,
            "unsupported_aperture": "UNKNOWN telemetry only; five-feature grammar",
            "epoch": time.time(),
        },
    )


def specs(root, task, phase):
    rows = read(root / "registration.json")["cohorts"][task][phase]
    return (
        [dict(s, observation_protocol="Peg-observation-v2") for s in rows]
        if task == TASKS[2]
        else rows
    )


def run_command(args):
    subprocess.run([sys.executable, *args], check=True, env=os.environ.copy())


def parity_or_guard(out, spec, first, second, context):
    from dsre_evidence_audit import equal

    for key in ("prefix", "prefix_controls", "checkpoint", "features"):
        try:
            equal(first[key], second[key])
        except (AssertionError, KeyError) as error:
            persist(
                out / "SOURCE_GUARD_FAILURE.json",
                {
                    "stage": context,
                    "spec": spec,
                    "status": "REPLAY_PARITY_FAILURE",
                    "first_difference_channel": key,
                    "reason": str(error),
                    "first_difference_witness": "Raw compared branches retained at this parent; numerical equality is not relaxed.",
                },
            )
            return False
    return True


def is_blocked(out):
    guards = list((out / "guard_witnesses").glob("*.json"))
    if (out / "SOURCE_GUARD_FAILURE.json").exists():
        guards.append(out / "SOURCE_GUARD_FAILURE.json")
    amendment = out.parent.parent / "G2_absorbing_prefix_clarification.json"
    return any(
        read(p)["status"] != "ALREADY_SOLVED_PREFIX" or not amendment.exists()
        for p in guards
    )


def collect(root, task, stage, limit=16, only_index=None):
    if task == TASKS[2]:
        assert read(root / "G1_source_v2_qualification.json")["technical_pass"], (
            "G1 BLOCKED"
        )
    out = root / "prospective" / task
    if (root / "STOP_AT_CHUNK_BOUNDARY").exists():
        raise RuntimeError("Intentional joined chunk boundary for contract correction")
    if is_blocked(out):
        raise RuntimeError(
            "Affected task halted at frozen source guard; see SOURCE_GUARD_FAILURE.json"
        )
    phase = "calibration" if stage == "screen" else stage
    sc = scope(task)
    rows = specs(root, task, phase)
    pending = []
    for spec in rows:
        if only_index is not None and spec["index"] != only_index:
            continue
        pid = identity(spec)
        target = out / ("screens" if stage == "screen" else stage) / f"{pid}.json"
        if not target.exists() or (
            stage == "test" and not (out / "evaluator" / f"{pid}.json").exists()
        ):
            pending.append((spec, pid, target))
    if only_index is None:
        from concurrent.futures import ThreadPoolExecutor

        # Process isolation retains private RNG/native state and CPU receipts.
        for start in range(0, min(limit, len(pending)), 4):
            if is_blocked(out):
                break
            group = pending[start : min(start + 4, limit)]

            def execute_one(entry):
                spec = entry[0]
                return subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        stage,
                        "--root",
                        str(root),
                        "--task",
                        task,
                        "--limit",
                        "1",
                        "--only-index",
                        str(spec["index"]),
                    ],
                    check=False,
                ).returncode

            with ThreadPoolExecutor(max_workers=4) as pool:
                codes = list(pool.map(execute_one, group))
            if any(codes) and not is_blocked(out):
                raise RuntimeError(
                    "Bounded parallel chunk failed; preserve all receipts"
                )
        return len(pending[:limit])
    for spec, pid, target in pending[:limit]:
        if stage == "screen":
            first = bounded_child(root, spec, "screen", "acquisition_screen")
            result = {
                "spec": spec,
                "parent_id": pid,
                "status": first["status"],
                "x": first.get("features"),
                "observed_prefix_success": first.get("success"),
                "epoch": time.time(),
            }
        elif stage == "test":
            assert (out / "all_models_frozen.json").exists()
            screen = bounded_child(root, spec, "screen", "policy_screen")
            if screen["status"] == "ALREADY_SOLVED_PREFIX":
                assert task == TASKS[0] and screen["success"] is True
                observation = out / "online_observations" / f"{pid}.json"
                persist(
                    observation,
                    {
                        "parent_id": pid,
                        "x": [None] * len(vocabulary(task)),
                        "source_scope": sc.model_dump(mode="json"),
                    },
                )
                decision = out / "online_decisions" / f"{pid}.json"
                if not decision.exists():
                    run_command(
                        [
                            "scripts/dsre_evidence_online.py",
                            str(out / "models/logged.json"),
                            str(observation),
                            str(decision),
                        ]
                    )
                assert (
                    read(decision)["action"] == "c"
                    and read(decision)["certificate"] is None
                )
                persist(
                    target,
                    {
                        "spec": spec,
                        "parent_id": pid,
                        "status": screen["status"],
                        "x": [None] * len(vocabulary(task)),
                        "action": "c",
                        "y": screen["success"],
                        "precheckpoint_absorption": True,
                        "selected_future_executed": False,
                        "epoch": time.time(),
                        "model_sha256": sha(out / "models/logged.json"),
                    },
                )
                other = bounded_child(root, spec, "r", "evaluator_counterpart")
                from dsre_evidence_audit import equal

                assert (
                    other["status"] == "ALREADY_SOLVED_PREFIX"
                    and other["success"] is True
                )
                equal(screen["prefix"], other["prefix"])
                equal(screen["prefix_controls"], other["prefix_controls"])
                persist(
                    out / "evaluator" / f"{pid}.json",
                    {
                        "parent_id": pid,
                        "first_seal_sha256": sha(target),
                        "first_sealed_epoch": read(target)["epoch"],
                        "status": other["status"],
                        "yc": screen["success"],
                        "yr": other["success"],
                        "precheckpoint_absorption": True,
                        "oracle_type": "observed absorbing prefix endpoints; no recovery checkpoint pair",
                    },
                )
                print(
                    json.dumps(
                        {
                            "task": task,
                            "stage": stage,
                            "index": spec["index"],
                            "status": "ALREADY_SOLVED_PREFIX",
                            "recovery_checkpoint": False,
                        }
                    ),
                    flush=True,
                )
                continue
            if screen["status"] != "CHECKPOINT_ONLY":
                persist(
                    target,
                    {
                        "spec": spec,
                        "parent_id": pid,
                        "status": screen["status"],
                        "epoch": time.time(),
                    },
                )
                persist(
                    out / "SOURCE_GUARD_FAILURE.json",
                    {
                        "stage": stage,
                        "spec": spec,
                        "status": screen["status"],
                        "reason": "No qualified checkpoint; no replacement or complete-case inference",
                    },
                )
                break
            observation = out / "online_observations" / f"{pid}.json"
            persist(
                observation,
                {
                    "parent_id": pid,
                    "x": screen["features"],
                    "source_scope": sc.model_dump(mode="json"),
                },
            )
            decision = out / "online_decisions" / f"{pid}.json"
            if not decision.exists():
                run_command(
                    [
                        "scripts/dsre_evidence_online.py",
                        str(out / "models/logged.json"),
                        str(observation),
                        str(decision),
                    ]
                )
            selected = read(decision)["action"]
            first = bounded_child(root, spec, selected, "selected_policy")
            result = {
                "spec": spec,
                "parent_id": pid,
                "status": first["status"],
                "action": selected,
                "y": first.get("success"),
                "x": first.get("features"),
                "epoch": time.time(),
                "model_sha256": sha(out / "models/logged.json"),
            }
        else:
            if stage == "calibration":
                assert (out / "acquisition_schedule.json").exists()
            selected = arm(task, str(spec["seed"]))
            first = bounded_child(root, spec, selected, "randomized_assigned")
            result = {
                "spec": spec,
                "parent_id": pid,
                "status": first["status"],
                "action": selected,
                "y": first.get("success"),
                "x": first.get("features"),
                "epoch": time.time(),
            }
            if first["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                record = OneAction(
                    parent_id=pid,
                    x=first["features"],
                    action=selected,
                    propensity=0.5,
                    y=first["success"],
                    controls=len(first["post_controls"]),
                    wall_seconds=first["wall_seconds"],
                    source_scope=sc,
                )
                result["record"] = record.model_dump(mode="json")
        if first["status"] == "ALREADY_SOLVED_PREFIX":
            assert (
                task == TASKS[0]
                and first["success"] is True
                and first["features"] is None
            )
            result["observed_prefix_success"] = first["success"]
            result["valid_recovery_checkpoint"] = False
            result["selected_future_executed"] = False
        if stage == "calibration" and first["status"] in (
            "COMPLETE",
            "OBSERVED_ABORT_ENDPOINT",
        ):
            rawscreen = read(
                root
                / "physics"
                / task
                / "calibration"
                / str(spec["index"])
                / "acquisition_screen.json.gz"
            )
            if not parity_or_guard(out, spec, rawscreen, first, "calibration"):
                persist(target, result)
                break
        persist(target, result)
        result = read(target)
        if "record" in result:
            persist(out / "learner_records" / stage / f"{pid}.json", result["record"])
        if stage == "screen" and result["status"] == "CHECKPOINT_ONLY":
            persist(
                out / "learner_observations/calibration" / f"{pid}.json",
                {
                    "parent_id": pid,
                    "x": result["x"],
                    "source_scope": sc.model_dump(mode="json"),
                },
            )
        if first["status"] not in (
            "COMPLETE",
            "CHECKPOINT_ONLY",
            "OBSERVED_ABORT_ENDPOINT",
            "ALREADY_SOLVED_PREFIX",
        ):
            persist(
                out / "SOURCE_GUARD_FAILURE.json",
                {
                    "stage": stage,
                    "spec": spec,
                    "status": first["status"],
                    "reason": "Missing checkpoint/label; halt rather than certify a selected complete-case population",
                },
            )
            break
        if stage == "test":
            if not parity_or_guard(out, spec, screen, first, "test_selected"):
                break
            # Selected record has been sealed before starting isolated counterfactual.
            other = bounded_child(
                root, spec, "r" if selected == "c" else "c", "evaluator_counterpart"
            )
            counterpart = {
                "parent_id": pid,
                "first_seal_sha256": sha(target),
                "first_sealed_epoch": result["epoch"],
                "status": other["status"],
                "yc": first.get("success") if selected == "c" else other.get("success"),
                "yr": first.get("success") if selected == "r" else other.get("success"),
            }
            if other["status"] in (
                "COMPLETE",
                "OBSERVED_ABORT_ENDPOINT",
            ) and not parity_or_guard(out, spec, first, other, "test_counterpart"):
                persist(out / "evaluator" / f"{pid}.json", counterpart)
                break
            persist(out / "evaluator" / f"{pid}.json", counterpart)
            if other["status"] not in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                persist(
                    out / "SOURCE_GUARD_FAILURE.json",
                    {
                        "stage": "test_counterpart",
                        "spec": spec,
                        "status": other["status"],
                        "reason": "Unavailable isolated oracle branch; selected outcome preserved, no paired label imputation",
                    },
                )
                break
        print(
            json.dumps(
                {
                    "task": task,
                    "stage": stage,
                    "index": spec["index"],
                    "status": first["status"],
                }
            ),
            flush=True,
        )
    return len(pending[:limit])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "stage",
        choices=["register", "qualify", "discovery", "screen", "calibration", "test"],
    )
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--task", choices=TASKS, default=TASKS[0])
    p.add_argument("--limit", type=int, default=16)
    p.add_argument("--only-index", type=int)
    a = p.parse_args()
    if a.stage == "register":
        register(a.root)
    elif a.stage == "qualify":
        qualify(a.root)
    else:
        collect(a.root, a.task, a.stage, min(a.limit, 16), a.only_index)
