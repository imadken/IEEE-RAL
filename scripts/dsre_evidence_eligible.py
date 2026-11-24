"""Execute the original insertion cohort under the sealed source-eligibility ruling."""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dsre_evidence_campaign import child
from dsre_evidence_lossless import archive, read
from dsre_evidence_prospective import BUDGETS, STRATEGIES, identity, scope, specs
from dsre_evidence_source_eligibility import OLD, ROOT, differences, fingerprints

from dual_rec.evidence_aware.schema import OneAction, Pair
from dual_rec.evidence_aware.views import arm, save, sha

TASK = "PegInsertionSide-v1"
OUT = ROOT / "prospective" / TASK
NO_CHECKPOINT = "NO_DECISION_CHECKPOINT_SOURCE_PLANNER_FAILURE"


def eligible_scope():
    return scope(TASK).model_copy(
        update={
            "population": "Original independent registered seeds CONDITIONAL ON source checkpoint eligibility under the sealed20261118 rule, and on the entire frozen routed leaf; no all-seed risk guarantee"
        }
    )


def resources():
    amendment = read(ROOT / "resource_amendment_registration.json")
    receipts = [
        p
        for p in (ROOT / "physics").glob("*/*/*/*.execution.json")
        if not p.is_symlink() and p.resolve().is_relative_to(ROOT.resolve())
    ]
    wall = amendment["previous_physics_debit_seconds"] + sum(
        read(p)["wall_seconds"] for p in receipts
    )
    size = sum(
        p.stat().st_size
        for base in (OLD, ROOT)
        for p in base.rglob("*")
        if p.is_file() and not p.is_symlink()
    )
    size += sum(
        p.stat().st_size
        for p in Path("research/dsre_evidence_design").glob(
            "evidence_aware_prospective_review*.tar.gz"
        )
    )
    return wall, size


def blocked():
    return (OUT / "SOURCE_GUARD_FAILURE.json").exists()


def guard(spec, stage, reason):
    path = OUT / "guard_witnesses" / f"{spec['phase']}-{spec['index']}-{stage}.json"
    value = {
        "epoch": time.time(),
        "spec": spec,
        "stage": stage,
        "reason": str(reason),
        "status": "HARD_QUALIFICATION_FAILURE",
    }
    save(path, value)
    try:
        os.link(path, OUT / "SOURCE_GUARD_FAILURE.json")
    except FileExistsError:
        pass


def verify_method():
    registration = read(ROOT / "eligibility_amendment.json")
    for name, checksum in registration["method_sha256"].items():
        assert sha(Path(name)) == checksum, f"Frozen method changed: {name}"


def execute(spec, action, label):
    verify_method()
    wall, size = resources()
    if wall >= 26 * 3600 - 720 or size >= 5 * 1024**3 - 256 * 1024**2:
        raise RuntimeError("REGISTERED_RESOURCE_BOUNDARY")
    directory = ROOT / "physics" / TASK / spec["phase"] / str(spec["index"])
    path = directory / f"{label}.json.gz"
    receipt = directory / f"{label}.execution.json"
    if receipt.exists():
        assert read(receipt)["source_sha256"] == sha(
            Path("scripts/dsre_evidence_tasks.py")
        )
        result = read(path)
        assert result["spec"] == spec and result["action"] == action
        return result
    result = child(ROOT, spec, action, label)
    assert result["spec"] == spec and result["action"] == action
    archive(path)
    return result


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, (float, int)) or math.isfinite(value)


def source_failure(record):
    return (
        record.get("status") == "FAILED_PREREQUISITE_OR_PREFIX"
        and record.get("error") == "UPSTREAM_SCREW_PLANNING_FAILED"
        and record.get("phase") == "prefix"
        and "line 443, in insertion" in record.get("traceback", "")
        and len(record.get("prefix", [])) == 1
        and not record.get("prefix_controls")
        and not record.get("post_controls")
        and record.get("checkpoint") is None
        and record.get("success") is None
        and record.get("features") is None
        and finite(record["prefix"][0])
    )


def classify(spec, record):
    if record["status"] == "CHECKPOINT_ONLY":
        assert len(record["features"]) == 5 and all(
            isinstance(v, bool) for v in record["features"]
        )
        assert record["feature_telemetry"][4] is None
        return "CHECKPOINT_ONLY"
    if not source_failure(record):
        raise RuntimeError("Unqualified prefix failure; no automatic exclusion")
    proofpath = OUT / "eligibility" / f"{identity(spec)}.json"
    if not proofpath.exists():
        before = fingerprints()
        proofs = []
        for repeat in (1, 2):
            other = execute(spec, "screen", f"eligibility_repeat_{repeat}")
            assert source_failure(other), "Failure was not deterministic"
            assert not differences(record["prefix"][0], other["prefix"][0]), (
                "Initial source/controller/RNG mismatch"
            )
            proofs.append(f"eligibility_repeat_{repeat}")
        assert fingerprints() == before
        save(
            proofpath,
            {
                "epoch": time.time(),
                "spec": spec,
                "status": NO_CHECKPOINT,
                "repetitions": proofs,
                "source_fingerprints": before,
                "stage": "first pregrasp dry-run screw planning, zero controls",
                "action_outcome_observed": False,
            },
        )
    return NO_CHECKPOINT


def physical(record, spec, label):
    from dsre_evidence_prospective_audit import physical as independent_physical

    assert record["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT")
    independent_physical(record, TASK)
    if record["status"] == "OBSERVED_ABORT_ENDPOINT":
        assert record.get("error") == "UPSTREAM_SCREW_PLANNING_FAILED", (
            "Controller or other exception is a hard qualification failure"
        )
        directory = ROOT / "physics" / TASK / spec["phase"] / str(spec["index"])
        review = directory / f"endpoint_review_{label}.json"
        if not review.exists():
            subprocess.run(
                [
                    sys.executable,
                    "scripts/dsre_evidence_endpoint_audit.py",
                    str(directory / f"{label}.json.gz"),
                    str(review),
                ],
                check=True,
            )
        assert read(review)["passed"]


def parity(a, b):
    from dsre_evidence_audit import equal

    for name in ("prefix", "prefix_controls", "checkpoint", "features"):
        equal(a[name], b[name])


def no_decision(spec, status, path):
    save(
        path,
        {
            "epoch": time.time(),
            "spec": spec,
            "parent_id": identity(spec),
            "status": status,
            "x": None,
            "y": None,
            "action": None,
            "selected_future_executed": False,
            "checkpoint_eligible": False,
        },
    )


def collect_one(stage, index):
    assert not blocked()
    phase = "calibration" if stage == "screen" else stage
    spec = specs(ROOT, TASK, phase)[index]
    pid = identity(spec)
    target = OUT / ("screens" if stage == "screen" else stage) / f"{pid}.json"
    if target.exists() and (
        stage != "test" or (OUT / "evaluator" / f"{pid}.json").exists()
    ):
        return
    try:
        if stage == "screen":
            record = execute(spec, "screen", "acquisition_screen")
            status = classify(spec, record)
            save(
                target,
                {
                    "epoch": time.time(),
                    "spec": spec,
                    "parent_id": pid,
                    "status": status,
                    "x": record.get("features"),
                    "raw_status": record["status"],
                },
            )
            if status == "CHECKPOINT_ONLY":
                save(
                    OUT / "learner_observations/calibration" / f"{pid}.json",
                    {
                        "parent_id": pid,
                        "x": record["features"],
                        "source_scope": eligible_scope().model_dump(mode="json"),
                    },
                )
        elif stage == "calibration":
            assert (OUT / "acquisition_schedule.json").exists()
            screening = read(OUT / "screens" / f"{pid}.json")
            if screening["status"] == NO_CHECKPOINT:
                no_decision(spec, NO_CHECKPOINT, target)
                return
            assert screening["status"] == "CHECKPOINT_ONLY"
            action = arm(TASK, str(spec["seed"]))
            record = execute(spec, action, "randomized_assigned")
            physical(record, spec, "randomized_assigned")
            parity(
                read(
                    ROOT
                    / "physics"
                    / TASK
                    / phase
                    / str(index)
                    / "acquisition_screen.json.gz"
                ),
                record,
            )
            log = OneAction(
                parent_id=pid,
                x=record["features"],
                action=action,
                propensity=0.5,
                y=record["success"],
                controls=len(record["post_controls"]),
                wall_seconds=record["wall_seconds"],
                source_scope=eligible_scope(),
            )
            save(
                target,
                {
                    "epoch": time.time(),
                    "spec": spec,
                    "parent_id": pid,
                    "status": record["status"],
                    "x": record["features"],
                    "y": record["success"],
                    "action": action,
                    "record": log.model_dump(mode="json"),
                },
            )
            save(
                OUT / "learner_records/calibration" / f"{pid}.json",
                log.model_dump(mode="json"),
            )
        elif stage == "test":
            assert (OUT / "all_models_frozen.json").exists()
            screen = execute(spec, "screen", "policy_screen")
            status = classify(spec, screen)
            if status == NO_CHECKPOINT:
                no_decision(spec, status, target)
                save(
                    OUT / "evaluator" / f"{pid}.json",
                    {
                        "parent_id": pid,
                        "status": status,
                        "yc": None,
                        "yr": None,
                        "oracle_type": "no intervention checkpoint, not an oracle action pair",
                    },
                )
                return
            observation = OUT / "online_observations" / f"{pid}.json"
            decision = OUT / "online_decisions" / f"{pid}.json"
            if not observation.exists():
                save(
                    observation,
                    {
                        "parent_id": pid,
                        "x": screen["features"],
                        "source_scope": eligible_scope().model_dump(mode="json"),
                    },
                )
            if not decision.exists():
                subprocess.run(
                    [
                        sys.executable,
                        "scripts/dsre_evidence_online.py",
                        str(OUT / "models/logged.json"),
                        str(observation),
                        str(decision),
                    ],
                    check=True,
                )
            action = read(decision)["action"]
            record = execute(spec, action, "selected_policy")
            physical(record, spec, "selected_policy")
            parity(screen, record)
            if not target.exists():
                save(
                    target,
                    {
                        "epoch": time.time(),
                        "spec": spec,
                        "parent_id": pid,
                        "status": record["status"],
                        "x": record["features"],
                        "y": record["success"],
                        "action": action,
                        "model_sha256": sha(OUT / "models/logged.json"),
                    },
                )
            other = execute(
                spec, "r" if action == "c" else "c", "evaluator_counterpart"
            )
            physical(other, spec, "evaluator_counterpart")
            parity(record, other)
            save(
                OUT / "evaluator" / f"{pid}.json",
                {
                    "parent_id": pid,
                    "status": other["status"],
                    "first_seal_sha256": sha(target),
                    "first_sealed_epoch": read(target)["epoch"],
                    "yc": record["success"] if action == "c" else other["success"],
                    "yr": record["success"] if action == "r" else other["success"],
                },
            )
        print(
            json.dumps(
                {"stage": stage, "index": index, "status": read(target)["status"]}
            ),
            flush=True,
        )
    except Exception as error:
        if "REGISTERED_RESOURCE_BOUNDARY" not in str(error):
            guard(spec, stage, error)
        raise


def paired_one(index):
    spec = specs(ROOT, TASK, "calibration")[index]
    pid = identity(spec)
    target = OUT / "acquisition_pairs" / f"{pid}.json"
    if target.exists():
        return
    try:
        first = read(OUT / "calibration" / f"{pid}.json")
        other = execute(
            spec, "r" if first["action"] == "c" else "c", "acquisition_counterpart"
        )
        physical(other, spec, "acquisition_counterpart")
        parity(
            read(
                ROOT
                / "physics"
                / TASK
                / "calibration"
                / str(index)
                / "randomized_assigned.json.gz"
            ),
            other,
        )
        pair = Pair(
            parent_id=pid,
            x=first["x"],
            yc=first["y"] if first["action"] == "c" else other["success"],
            yr=first["y"] if first["action"] == "r" else other["success"],
            source_scope=eligible_scope(),
        )
        save(OUT / "paired_refinement" / f"{pid}.json", pair.model_dump(mode="json"))
        save(
            target,
            {
                "pair": pair.model_dump(mode="json"),
                "status": other["status"],
                "schedule_sha256": sha(OUT / "acquisition_schedule.json"),
                "first_log_sha256": sha(OUT / "calibration" / f"{pid}.json"),
                "epoch": time.time(),
            },
        )
        print(
            json.dumps({"stage": "pairs", "index": index, "status": other["status"]}),
            flush=True,
        )
    except Exception as error:
        if "REGISTERED_RESOURCE_BOUNDARY" not in str(error):
            guard(spec, "pairs", error)
        raise


def fit_one(name):
    from dsre_evidence_prospective_fit import freeze_one

    verify_method()

    freeze_one(ROOT, TASK, name, outcome_scope=eligible_scope())


def chunks(stage, indices):
    for start in range(0, len(indices), 16):
        for groupstart in range(start, min(start + 16, len(indices)), 4):
            assert not blocked(), "Hard source guard retained"
            group = indices[groupstart : min(groupstart + 4, start + 16)]

            def call(index):
                return subprocess.run(
                    [sys.executable, __file__, stage, "--index", str(index)],
                    check=False,
                ).returncode

            with ThreadPoolExecutor(max_workers=4) as pool:
                codes = list(pool.map(call, group))
            assert not any(codes), "Atomic group stopped; preserve receipts and guard"
        print(
            json.dumps(
                {
                    "chunk": stage,
                    "finished_indices": indices[start : start + 16],
                    "resources": resources(),
                }
            ),
            flush=True,
        )


def run():
    for stage, count, folder in (
        ("screen", 1024, "screens"),
        ("calibration", 1024, "calibration"),
    ):
        pending = [
            i
            for i in range(count)
            if not (
                OUT / folder / f"{identity(specs(ROOT, TASK, 'calibration')[i])}.json"
            ).exists()
        ]
        if stage == "calibration" and not (OUT / "acquisition_schedule.json").exists():
            subprocess.run(
                [
                    sys.executable,
                    "scripts/dsre_evidence_prospective_fit.py",
                    "plan",
                    "--root",
                    str(ROOT),
                    "--task",
                    TASK,
                ],
                check=True,
            )
        chunks(stage, pending)
    if not (OUT / "all_models_frozen.json").exists():
        if not (OUT / "models/logged.json").exists():
            subprocess.run(
                [sys.executable, __file__, "fit", "--model", "logged"], check=True
            )
        save(
            OUT / "all_models_frozen.json",
            {
                "epoch": time.time(),
                "models": {"logged": sha(OUT / "models/logged.json")},
                "discovery_sha256": sha(OUT / "discovery_freeze.json"),
                "acquisition_schedule_sha256": sha(OUT / "acquisition_schedule.json"),
                "test_outcomes_accessed": False,
                "scope": "Primary router before test; fixed G4 lists/code frozen before calibration; acquisition physics follows G3 per20261118 priority",
            },
        )
    pending = [
        i
        for i in range(256)
        if not (
            OUT / "evaluator" / f"{identity(specs(ROOT, TASK, 'test')[i])}.json"
        ).exists()
    ]
    chunks("test", pending)
    subprocess.run([sys.executable, __file__, "evaluate"], check=True)
    schedule = read(OUT / "acquisition_schedule.json")
    ids = {
        r["parent_id"]
        for budgets in schedule["schedules"].values()
        for r in budgets["512"]
        if r["kind"] == "pair"
    }
    pending = [
        i
        for i, spec in enumerate(specs(ROOT, TASK, "calibration"))
        if identity(spec) in ids
        and not (OUT / "acquisition_pairs" / f"{identity(spec)}.json").exists()
    ]
    chunks("pairs", pending)
    hashes = {}
    for strategy in STRATEGIES:
        for budget in BUDGETS:
            name = f"{strategy}_{budget}"
            if not (OUT / "models" / f"{name}.json").exists():
                subprocess.run(
                    [sys.executable, __file__, "fit", "--model", name], check=True
                )
            hashes[name] = sha(OUT / "models" / f"{name}.json")
    if (OUT / "acquisition_models_frozen.json").exists():
        return
    save(
        OUT / "acquisition_models_frozen.json",
        {
            "epoch": time.time(),
            "models": hashes,
            "schedule_sha256": sha(OUT / "acquisition_schedule.json"),
            "test_read_by_fitting": False,
            "scope": "Descriptive fixed strategy/budget curves; calibration independent of discovery; code/lists frozen before calibration and test; isolated fit never reads test",
        },
    )
    subprocess.run([sys.executable, __file__, "evaluate", "--acquisition"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("run", "screen", "calibration", "test", "pairs", "fit", "evaluate"),
    )
    parser.add_argument("--index", type=int)
    parser.add_argument("--model")
    parser.add_argument("--acquisition", action="store_true")
    args = parser.parse_args()
    if args.stage == "run":
        run()
    elif args.stage == "fit":
        fit_one(args.model)
    elif args.stage == "evaluate":
        from dsre_evidence_prospective_evaluate import evaluate

        evaluate(
            ROOT,
            TASK,
            frozen_path=OUT / "acquisition_models_frozen.json"
            if args.acquisition
            else None,
        )
    elif args.stage == "pairs":
        paired_one(args.index)
    else:
        collect_one(args.stage, args.index)
