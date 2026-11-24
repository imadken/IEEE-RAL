"""Outcome-isolated discovery schedules and independent calibration freezes."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from dsre_evidence_prospective import (
    BUDGETS,
    ROOT,
    STRATEGIES,
    TASKS,
    bounded_child,
    identity,
    is_blocked,
    persist,
    read,
    scope,
    specs,
    vocabulary,
)

from dual_rec.evidence_aware.acquisition import decision_information_scores
from dual_rec.evidence_aware.baselines import DESCRIPTIONS, proposals
from dual_rec.evidence_aware.bounds import calibrate, solve
from dual_rec.evidence_aware.diagnosis import plugin_diagnosis
from dual_rec.evidence_aware.partition import fit, route
from dual_rec.evidence_aware.schema import OneAction, Pair, Partition, Source
from dual_rec.evidence_aware.views import guard_data_access, hashed, save, sha


def discovery(root, task):
    out = root / "prospective" / task
    rows = specs(root, task, "discovery")
    paths = [
        out / "learner_records/discovery" / f"{identity(s)}.json"
        for s in rows
        if (out / "learner_records/discovery" / f"{identity(s)}.json").exists()
    ]
    accesses = guard_data_access(Path("results"), paths, additional_roots=(root,))
    results = [read(p) for p in paths]
    assert len(results) <= 128 and results
    records = [OneAction.model_validate(r) for r in results]
    partition = fit(records, vocabulary(task))
    prop = proposals(partition, records)
    persist(
        out / "learner/discovery.json", [r.model_dump(mode="json") for r in records]
    )
    persist(out / "learner/vocabulary.json", list(vocabulary(task)))
    persist(
        out / "discovery_freeze.json",
        {
            "epoch": time.time(),
            "partition": partition.model_dump(mode="json"),
            "proposals": prop,
            "n_discovery_records": len(records),
            "input_whitelist_sha256": {str(p): sha(p) for p in paths},
            "successful_data_reads": list(accesses),
        },
    )
    print(
        json.dumps(
            {
                "discovery_frozen": task,
                "n": len(records),
                "leaves": len(set(partition.cells)),
            }
        ),
        flush=True,
    )


def plan(root, task):
    out = root / "prospective" / task
    registered = specs(root, task, "calibration")
    screenpaths = [
        out / "learner_observations/calibration" / f"{identity(s)}.json"
        for s in registered
        if (out / "learner_observations/calibration" / f"{identity(s)}.json").exists()
    ]
    base_ids = {identity(s) for s in registered[:512]}
    candidate_ids = {identity(s) for s in registered[512:]}
    allowed = [
        out / "learner/discovery.json",
        out / "discovery_freeze.json",
        *screenpaths,
    ]
    accesses = guard_data_access(Path("results"), allowed, additional_roots=(root,))
    partition = Partition.model_validate(
        read(out / "discovery_freeze.json")["partition"]
    )
    records = [
        OneAction.model_validate(r) for r in read(out / "learner/discovery.json")
    ]
    screens = [read(p) for p in screenpaths]
    assert all(route(partition, r["x"]) is not None for r in screens)
    candidates = [r for r in screens if r["parent_id"] in candidate_ids]
    masses = Counter(route(partition, r.x) for r in records)
    masses = {c: masses.get(c, 0) for c in sorted(set(partition.cells))}
    diagnostic = {}
    planning_marginals = {}
    for c in masses:
        rows = [r for r in records if route(partition, r.x) == c]
        e, _ = calibrate(rows, [], f"discovery-only-diagnostic:{c}", len(masses))
        b = solve(e)
        arms = [[int(r.y) for r in rows if r.action == a] for a in ("c", "r")]
        w = plugin_diagnosis(e, *[sum(v) / len(v) if v else 0 for v in arms])
        planning_marginals[c] = (
            *[(sum(v) + 0.5) / (len(v) + 1) for v in arms],
            *[len(v) for v in arms],
        )
        diagnostic[c] = (
            w.status,
            b.harm_upper - b.harm_lower,
            b.gain_upper - b.gain_lower,
        )
    schedules = {}
    for strategy in STRATEGIES:
        byleaf = {
            c: sorted(
                [r for r in candidates if route(partition, r["x"]) == c],
                key=lambda r: hashed("prospective-acquire:" + r["parent_id"]),
            )
            for c in masses
        }
        # Fixed context-only schedule, with exact nested budget boundaries.
        leaves = sorted(masses, key=lambda c: (-masses[c], c))
        positions = Counter()
        planned_logs, planned_pairs = Counter(), Counter()
        chosen, spent, turn = [], 0, 0
        while spent < 512:
            available = [c for c in leaves if positions[c] < len(byleaf[c])]
            if not available:
                break
            c = available[turn % len(available)]
            information = {}
            if strategy == "decision_uncertainty":
                information = {
                    leaf: decision_information_scores(
                        *planning_marginals[leaf],
                        planned_logs[leaf],
                        planned_pairs[leaf],
                    )
                    for leaf in available
                }
                c = min(
                    available,
                    key=lambda leaf: (-masses[leaf] * max(information[leaf]), leaf),
                )
            status, _width_h, _width_g = diagnostic[c]
            pair = (
                strategy == "all_pairs"
                or (
                    strategy == "witness"
                    and status == "MARGINAL_IDENTIFICATION_BARRIER"
                )
                or (
                    strategy == "uniform_mix"
                    and hashed(f"prospective-mixed:{task}:{turn}") % 2 == 0
                )
                or (
                    strategy == "decision_uncertainty"
                    and information[c][1] > information[c][0]
                )
            )
            boundary = next(b for b in BUDGETS if b > spent)
            if spent + (2 if pair else 1) > boundary:
                pair = False
            kind, cost = ("pair", 2) if pair else ("log", 1)
            r = byleaf[c][positions[c]]
            positions[c] += 1
            if pair:
                planned_pairs[c] += 1
            else:
                planned_logs[c] += 1
            chosen.append(
                {
                    "parent_id": r["parent_id"],
                    "leaf": c,
                    "kind": kind,
                    "cost": cost,
                    "cumulative_cost": spent + cost,
                }
            )
            spent += cost
            turn += 1
        schedules[strategy] = {
            str(b): [r for r in chosen if r["cumulative_cost"] <= b] for b in BUDGETS
        }
    persist(
        out / "acquisition_schedule.json",
        {
            "epoch": time.time(),
            "partition_sha256": sha(out / "discovery_freeze.json"),
            "diagnostic": diagnostic,
            "planning_marginals": planning_marginals,
            "masses": masses,
            "base_ids": [r["parent_id"] for r in screens if r["parent_id"] in base_ids],
            "candidate_ids": [r["parent_id"] for r in candidates],
            "schedules": schedules,
            "method_source_sha256": {
                str(p): sha(p)
                for p in [
                    *Path("src/dual_rec/evidence_aware").glob("*.py"),
                    Path("scripts/dsre_evidence_prospective_fit.py"),
                    Path("scripts/dsre_evidence_prospective.py"),
                    Path("scripts/dsre_evidence_online.py"),
                    Path("scripts/dsre_evidence_prospective_evaluate.py"),
                    Path("scripts/dsre_evidence_tasks.py"),
                    Path("scripts/dsre_evidence_grasp.py"),
                ]
            },
            "selection_information": "independent discovery labels and predecision calibration observations ONLY; no calibration outcomes or evaluator branches",
            "input_whitelist_sha256": {str(p): sha(p) for p in allowed},
            "successful_data_reads": list(accesses),
            "confidence": "individual fixed allocation .95 per task; curves and between-strategy differences descriptive",
        },
    )
    print(
        json.dumps(
            {
                "acquisition_schedule_frozen": task,
                "logical_cost": {
                    s: {b: sum(r["cost"] for r in v) for b, v in bs.items()}
                    for s, bs in schedules.items()
                },
            }
        ),
        flush=True,
    )


def refine(root, task, limit=16, only_index=None):
    out = root / "prospective" / task
    schedule = read(out / "acquisition_schedule.json")
    ids = {
        r["parent_id"]
        for bs in schedule["schedules"].values()
        for r in bs["512"]
        if r["kind"] == "pair"
    }
    rows = [s for s in specs(root, task, "calibration") if identity(s) in ids]
    pending = [
        s
        for s in rows
        if not (out / "acquisition_pairs" / f"{identity(s)}.json").exists()
    ]
    if only_index is None:
        import subprocess
        import sys
        from concurrent.futures import ThreadPoolExecutor

        for start in range(0, min(limit, len(pending)), 4):
            if is_blocked(out):
                break
            group = pending[start : min(start + 4, limit)]

            def execute_one(spec):
                return subprocess.run(
                    [
                        sys.executable,
                        __file__,
                        "refine",
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
                raise RuntimeError("Bounded paired acquisition chunk failed")
        return
    pending = [s for s in pending if s["index"] == only_index]
    for spec in pending[:limit]:
        pid = identity(spec)
        first = read(out / "calibration" / f"{pid}.json")
        assert "record" in first
        # This is budgeted paired refinement, not an evaluator calibration leak.
        other = bounded_child(
            root,
            spec,
            "r" if first["action"] == "c" else "c",
            "acquisition_counterpart",
        )
        from dsre_evidence_audit import equal
        from dsre_evidence_prospective import read as rawread

        raw = rawread(
            root
            / "physics"
            / task
            / "calibration"
            / str(spec["index"])
            / "randomized_assigned.json.gz"
        )
        if other["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
            for key in ("prefix", "prefix_controls", "checkpoint", "features"):
                equal(raw[key], other[key])
            pair = Pair(
                parent_id=pid,
                x=first["x"],
                yc=first["y"] if first["action"] == "c" else other["success"],
                yr=first["y"] if first["action"] == "r" else other["success"],
                source_scope=scope(task),
            )
            persist(
                out / "paired_refinement" / f"{pid}.json", pair.model_dump(mode="json")
            )
            persist(
                out / "acquisition_pairs" / f"{pid}.json",
                {
                    "pair": pair.model_dump(mode="json"),
                    "status": other["status"],
                    "schedule_sha256": sha(out / "acquisition_schedule.json"),
                    "first_log_sha256": sha(out / "calibration" / f"{pid}.json"),
                    "epoch": time.time(),
                },
            )
        else:
            persist(
                out / "SOURCE_GUARD_FAILURE.json",
                {
                    "stage": "acquisition",
                    "spec": spec,
                    "status": other["status"],
                    "reason": "Missing paired label; no complete-case PAC claim",
                },
            )
            break
        print(
            json.dumps(
                {"acquisition": task, "index": spec["index"], "status": other["status"]}
            ),
            flush=True,
        )


def freeze_one(root, task, name, *, outcome_scope=None):
    out = root / "prospective" / task
    schedule = read(out / "acquisition_schedule.json")
    assert all(
        sha(Path(path)) == checksum
        for path, checksum in schedule.get("method_source_sha256", {}).items()
    ), "Frozen calibration method source changed"
    if name == "logged":
        logids = [
            identity(s)
            for s in specs(root, task, "calibration")
            if (out / "learner_records/calibration" / f"{identity(s)}.json").exists()
        ]
        pairids = []
    else:
        strategy, budget = name.rsplit("_", 1)
        requests = schedule["schedules"][strategy][budget]
        logids = schedule["base_ids"] + [r["parent_id"] for r in requests]
        pairids = [r["parent_id"] for r in requests if r["kind"] == "pair"]
    cp = [out / "learner_records/calibration" / f"{pid}.json" for pid in logids]
    ap = [out / "paired_refinement" / f"{pid}.json" for pid in pairids]
    path = out / "models" / f"{name}.json"
    allowed = [
        out / "discovery_freeze.json",
        out / "acquisition_schedule.json",
        *cp,
        *ap,
    ]
    accessed = guard_data_access(Path("results"), allowed, additional_roots=(root,))
    frozen = read(out / "discovery_freeze.json")
    partition = Partition.model_validate(frozen["partition"])
    logs = [OneAction.model_validate(read(p)) for p in cp]
    pairs = [Pair.model_validate(read(p)) for p in ap]
    k = len(set(partition.cells))
    leaves = {}
    for c in sorted(set(partition.cells)):
        ls = [r for r in logs if route(partition, r.x) == c]
        ps = [r for r in pairs if route(partition, r.x) == c]
        e, ledger = calibrate(ls, ps, f"frozen_leaf:{c}", k)
        b = solve(e)
        arms = [[int(r.y) for r in ls if r.action == a] for a in ("c", "r")]
        w = plugin_diagnosis(e, *[sum(v) / len(v) if v else 0 for v in arms])
        leaves[c] = {
            "evidence": e.model_dump(mode="json"),
            "bounds": b.model_dump(mode="json"),
            "ledger": ledger,
            "diagnosis": w.model_dump(mode="json"),
        }
    save(
        path,
        {
            "regime": name,
            "development_only": False,
            "epoch": time.time(),
            "partition": partition.model_dump(mode="json"),
            "source_scope": (outcome_scope or scope(task)).model_dump(mode="json"),
            "source_type": Source.PAIRED.value if pairs else Source.LOGGED.value,
            "leaves": leaves,
            "proposals": frozen["proposals"],
            "decisions": [],
            "baseline_descriptions": DESCRIPTIONS,
            "counts": {
                "discovery": frozen.get("n_discovery_records", 128),
                "calibration_logs": len(logs),
                "calibration_pairs": len(pairs),
            },
            "logical_calibration_executions": len(logs) + len(pairs),
            "log_parent_ids": logids,
            "pair_parent_ids": pairids,
            "input_whitelist_sha256": {str(p): sha(p) for p in allowed},
            "successful_data_reads": list(accessed),
            "method_source_sha256": schedule.get("method_source_sha256", {}),
            "confidence_note": "95percent per task for this fixed model; curves descriptive; test untouched during fitting",
        },
    )


def freeze(root, task):
    from dsre_evidence_prospective import run_command

    out = root / "prospective" / task
    names = ["logged"] + [f"{s}_{b}" for s in STRATEGIES for b in BUDGETS]
    hashes = {}
    for name in names:
        path = out / "models" / f"{name}.json"
        if not path.exists():
            run_command(
                [
                    __file__,
                    "freeze_one",
                    "--root",
                    str(root),
                    "--task",
                    task,
                    "--model",
                    name,
                ]
            )
        hashes[name] = sha(path)
    persist(
        out / "all_models_frozen.json",
        {
            "epoch": time.time(),
            "models": hashes,
            "discovery_sha256": sha(out / "discovery_freeze.json"),
            "acquisition_schedule_sha256": sha(out / "acquisition_schedule.json"),
            "test_outcomes_accessed": False,
        },
    )
    model = read(out / "models/logged.json")
    print(
        json.dumps(
            {
                "models_frozen": task,
                "count": len(hashes),
                "qualified_logged_leaves": [
                    c
                    for c, v in model["leaves"].items()
                    if v["bounds"]["harm_upper"] <= 0.1
                    and v["bounds"]["gain_lower"] >= 0.05
                ],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "stage", choices=["discovery", "plan", "refine", "freeze", "freeze_one"]
    )
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--task", choices=TASKS, default=TASKS[0])
    p.add_argument("--limit", type=int, default=16)
    p.add_argument("--model")
    p.add_argument("--only-index", type=int)
    a = p.parse_args()
    if a.stage == "refine":
        refine(a.root, a.task, min(a.limit, 16), a.only_index)
    elif a.stage == "freeze_one":
        freeze_one(a.root, a.task, a.model)
    else:
        globals()[a.stage](a.root, a.task)
