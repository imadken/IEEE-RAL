"""Metered fixed campaign: atomic parents, no source repair or seed replacement."""

import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess
import sys
import time
from collections import Counter

from dsre_evidence_lossless import archive
from dsre_evidence_lossless import read as trace_read
from dsre_last_common import ROOT, pid, read, save, sha
from dsre_last_physical import native_abort, parity, peg, push

from dual_rec.evidence_aware.schema import OneAction, Scope


def scope():
    return Scope(
        task="PushCube-v1",
        controller_sha256=sha("scripts/overnight_replay.py"),
        horizon=70,
        outcome="native PushCube endpoint XYdistance<.1 AND cubeZ<.025 after70 fixed controls",
        population="independent registered parents; 50% nominal, 50% existing misaligned",
        observation_protocol="PRIMARY6 fixed53-control boundary",
    )


def used():
    return sum(
        read(p)["elapsed_seconds"] for p in (ROOT / "physics").rglob("*.execution.json")
    )


def worker(spec, label, action):
    d = ROOT / "physics" / spec["phase"] / str(spec["index"])
    d.mkdir(parents=True, exist_ok=True)
    specpath = d / "spec.json"
    save(specpath, spec)
    output = d / (label + ".json.gz")
    receipt = d / (label + ".execution.json")
    if receipt.exists():
        record = read(receipt)
        assert record["action"] == action and record["spec_sha256"] == sha(specpath)
        result = trace_read(output)
        return result
    assert not output.exists() and not output.with_suffix(".xz").exists(), (
        "UNCLEAN_ATTEMPT_REQUIRES_AUDIT_NO_RETRY"
    )
    started = time.time()
    save(
        d / (label + ".started.json"),
        {"epoch": started, "action": action, "spec_sha256": sha(specpath)},
    )
    script = (
        "scripts/dsre_last_push.py"
        if spec["task"] == "PushCube-v1"
        else "scripts/dsre_evidence_tasks.py"
    )
    environment = dict(
        os.environ,
        VK_ICD_FILENAMES="/usr/share/vulkan/icd.d/lvp_icd.x86_64.json",
        CUDA_VISIBLE_DEVICES="",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    with (d / (label + ".stdout")).open("xb") as log:
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    script,
                    str(specpath),
                    str(output),
                    "--action",
                    action,
                ],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=180,
                check=False,
            )
            code = completed.returncode
        except subprocess.TimeoutExpired:
            code = "TIMEOUT"
    elapsed = time.time() - started
    save(
        receipt,
        {
            "action": action,
            "started_epoch": started,
            "completed_epoch": time.time(),
            "elapsed_seconds": elapsed,
            "returncode": code,
            "spec_sha256": sha(specpath),
            "script_sha256": sha(script),
            "raw_sha256": sha(output) if output.exists() else None,
        },
    )
    if code != 0 or not output.exists():
        raise RuntimeError(f"NATIVE_SOURCE_PROCESS_FAILED:{code}:{d}:{label}")
    result = trace_read(output)
    archive(output)
    return result


def process(spec):
    phase = spec["phase"]
    target = ROOT / "records" / phase / (str(spec["index"]) + ".json")
    if target.exists():
        return read(target)
    if spec["task"] == "PushCube-v1":
        if phase == "native_pilot":
            branches = {
                f"{a}{repeat}": worker(spec, f"{a}{repeat}", a)
                for a in ("c", "r")
                for repeat in range(2)
            }
            for b in branches.values():
                push(b)
                parity(branches["c0"], b, spec["task"])
            from dsre_source_risk_audit import state_equal

            for a in ("c", "r"):
                for x, y in zip(
                    branches[a + "0"]["post"], branches[a + "1"]["post"], strict=True
                ):
                    state_equal(x, y)
            result = {
                "status": "QUALIFIED",
                "spec": spec,
                "outcomes": {a: branches[a + "0"]["success"] for a in ("c", "r")},
            }
        elif phase in ("discovery", "calibration"):
            b = worker(spec, "assigned", spec["assigned"])
            push(b)
            assert (
                b["executed_action"] == spec["assigned"]
                and b["action"] == spec["assigned"]
            )
            record = OneAction(
                parent_id=pid(spec),
                x=b["features"],
                action=spec["assigned"],
                propensity=0.5,
                y=b["success"],
                controls=70,
                wall_seconds=b["wall_seconds"],
                source_scope=scope(),
            )
            result = {
                "status": "COMPLETE",
                "spec": spec,
                "record": record.model_dump(mode="json"),
            }
        else:
            b = worker(spec, "selected", "policy")
            push(b)
            assert b["model_sha256"] == sha(ROOT / "model_frozen.json")
            other = "r" if b["executed_action"] == "c" else "c"
            # The selected outcome is immutable before launching the evaluator.
            save(
                ROOT / "selected_test" / f"{spec['index']}.json",
                {
                    "spec": spec,
                    "parent_id": pid(spec),
                    "x": b["features"],
                    "action": b["executed_action"],
                    "y": b["success"],
                    "decision": b["decision"],
                    "completed_epoch": b["completed_epoch"],
                    "model_sha256": b["model_sha256"],
                },
            )
            a = worker(spec, "evaluator", other)
            assert a["started_epoch"] > b["completed_epoch"]
            push(a)
            parity(b, a, spec["task"])
            outcomes = {b["executed_action"]: b["success"], other: a["success"]}
            result = {
                "status": "COMPLETE",
                "spec": spec,
                "parent_id": pid(spec),
                "x": b["features"],
                "yc": outcomes["c"],
                "yr": outcomes["r"],
                "decision": b["decision"],
            }
    else:
        b = worker(spec, "screen", "screen")
        if native_abort(b):
            result = {
                "status": "NO_DECISION_CHECKPOINT",
                "spec": spec,
                "executed_prefix_controls": len(b["prefix_controls"]),
                "reason": b["error"],
            }
        else:
            assert b["status"] == "CHECKPOINT_ONLY", (
                f"INVALID_INSERTION_SOURCE:{b.get('status')}:{b.get('error')}"
            )
            outcomes = {}
            missing = []
            for action in ("c", "r"):
                a = worker(spec, action, action)
                # A valid canonical checkpoint cannot be silently lost on replay.
                parity(b, a, spec["task"])
                if a["status"] == "MISSING_TERMINAL_OUTCOME":
                    outcomes[action] = None
                    missing.append(action)
                else:
                    peg(a)
                    outcomes[action] = a["success"]
            result = {
                "status": "MISSING" if missing else "QUALIFIED",
                "spec": spec,
                "x": b["features"],
                "yc": outcomes["c"],
                "yr": outcomes["r"],
                "missing": missing,
            }
    save(target, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=(
            "native_pilot",
            "discovery",
            "calibration",
            "test",
            "insertion_pilot",
            "insertion_confirmation",
        ),
    )
    args = parser.parse_args()
    reg = read(ROOT / "registration.json")
    assert not (ROOT / (args.phase + ".source_stop.json")).exists(), (
        "TASK_SOURCE_STOP_NO_RETRY"
    )
    for p, h in reg["source_sha256"].items():
        assert sha(p) == h, "REGISTERED_SOURCE_CHANGED:" + p
    if args.phase in ("discovery", "calibration", "test"):
        assert read(ROOT / "native_pilot.complete.json")["qualified"] == 4
    if args.phase == "calibration":
        assert (ROOT / "discovery_freeze.json").exists()
    if args.phase == "test":
        assert (ROOT / "model_frozen.json").exists()
    if args.phase == "insertion_confirmation":
        assert read(ROOT / "insertion_extension_decision.json")["extend"]
    specs = [s for s in reg["push"] + reg["peg"] if s["phase"] == args.phase]
    try:
        for start in range(0, len(specs), 4):
            batch = specs[start : start + 4]
            needed = [
                s
                for s in batch
                if not (
                    ROOT / "records" / args.phase / (str(s["index"]) + ".json")
                ).exists()
            ]
            size = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
            now = datetime.datetime.now(datetime.UTC)
            hard = datetime.datetime.fromisoformat(reg["resources"]["hard_stop_utc"])
            if (
                used() + len(needed) * 4 * 180 > 10 * 3600
                or size + len(needed) * 20_000_000 > 4 * 1024**3
                or now + datetime.timedelta(seconds=4 * 180 + 7200) > hard
            ):
                save(
                    ROOT / (args.phase + ".resource_stop.json"),
                    {
                        "epoch": time.time(),
                        "used_worker_seconds": used(),
                        "next_index": start,
                        "bytes": size,
                    },
                )
                return
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(process, s) for s in needed]
                for f in futures:
                    f.result()
            print(
                json.dumps(
                    {
                        "phase": args.phase,
                        "completed": min(start + 4, len(specs)),
                        "registered": len(specs),
                        "worker_hours": round(used() / 3600, 4),
                    }
                ),
                flush=True,
            )
    except Exception as error:
        save(
            ROOT / (args.phase + ".source_stop.json"),
            {"error": repr(error), "epoch": time.time(), "worker_seconds": used()},
        )
        raise
    rows = [
        read(ROOT / "records" / args.phase / (str(s["index"]) + ".json")) for s in specs
    ]
    if args.phase in ("discovery", "calibration"):
        save(ROOT / "learner" / (args.phase + ".json"), [r["record"] for r in rows])
    counts = Counter(r["status"] for r in rows)
    save(
        ROOT / (args.phase + ".complete.json"),
        {
            "registered": len(specs),
            "completed": len(rows),
            "qualified": counts["QUALIFIED"],
            "counts": dict(counts),
            "epoch": time.time(),
            "worker_seconds": used(),
        },
    )
    if args.phase == "insertion_pilot":
        categories = Counter(
            f"{int(r['yc'])}{int(r['yr'])}" for r in rows if r["status"] == "QUALIFIED"
        )
        qualified = sum(r["status"] in ("QUALIFIED", "MISSING") for r in rows)
        save(
            ROOT / "insertion_extension_decision.json",
            {
                "extend": qualified >= 32
                and categories["10"] >= 2
                and categories["01"] >= 2,
                "qualified_checkpoints": qualified,
                "outcomes": dict(categories),
                "raw_denominator": 48,
                "epoch": time.time(),
                "pilot_records_sha256": {
                    str(p): sha(p)
                    for p in (ROOT / "records/insertion_pilot").glob("*.json")
                },
                "decision": "Fixed source and action-diversity qualification; no controller or condition retuning. If false insertion permanently closed for Stage1.",
            },
        )


if __name__ == "__main__":
    main()
