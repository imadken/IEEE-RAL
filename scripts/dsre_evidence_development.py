"""Genuine one-action logging, frozen ingestion, then execution on new parents."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dsre_evidence_campaign import child
from dsre_evidence_tasks import NAV_VOCAB, PEG_VOCAB

from dual_rec.dsre.features import PRIMARY
from dual_rec.evidence_aware.schema import OneAction, PolicyExecution, Scope
from dual_rec.evidence_aware.views import arm, hashed, save, sha


def persist(path, value):
    """A resumed collector reuses verified records and never overwrites them."""
    if path.exists():
        previous = json.loads(path.read_text())
        if isinstance(value, dict):
            ignored = {"epoch", "sealed_epoch"}
            assert {k: v for k, v in previous.items() if k not in ignored} == {
                k: v for k, v in value.items() if k not in ignored
            }
        else:
            assert previous == value
    else:
        save(path, value)


def collect(root, task):
    completed = root / "development" / task / "collection_results.json"
    if completed.exists():
        print(
            json.dumps(
                {
                    "status": "REUSED_COMPLETE_IMMUTABLE_COLLECTION",
                    "task": task,
                    "counts": json.loads(completed.read_text())["counts"],
                }
            ),
            flush=True,
        )
        return
    qualification = root / (
        task
        + (
            "-qualification-interface2.json"
            if task == "PointMaze_UMaze-v3"
            else "-qualification-interface3.json"
        )
    )
    if task == "PickCube-v1":
        qualification = root / "PickCube-v1-qualification-existing.json"
    assert json.loads(qualification.read_text())["technical_pass"]
    specs = json.loads((root / "prospective_manifest.json").read_text())["cohorts"][
        task
    ]["development"]
    out = root / "development" / task
    scope = Scope(
        task=task,
        controller_sha256=sha(
            Path(
                "scripts/dsre_evidence_grasp.py"
                if task == "PickCube-v1"
                else "scripts/dsre_evidence_tasks.py"
            )
        ),
        horizon=70
        if task == "PickCube-v1"
        else 200
        if task == "PointMaze_UMaze-v3"
        else 400,
        outcome="official episodic success, absorbing termination"
        if task == "PointMaze_UMaze-v3"
        else "official terminal success after70 controls"
        if task == "PickCube-v1"
        else "official terminal success after400 controls",
        population="fixed namespace independent DEVELOPMENT parents and five-condition mixture",
        observation_protocol="six contract predecision predicates; missing means unknown",
    )
    freeze_path = out / "collection_freeze.json"
    if freeze_path.exists():
        frozen = json.loads(freeze_path.read_text())
        assert frozen["seeds"] == specs and frozen["scope"] == scope.model_dump(
            mode="json"
        ), "Frozen collection changed"
    else:
        persist(
            out / "collection_freeze.json",
            {
                "split": "indices0..31 discovery,32..47 calibration,48..63 deployed development evaluation",
                "seeds": specs,
                "scope": scope.model_dump(mode="json"),
                "source_sha256": {
                    str(p): sha(p)
                    for p in (Path(__file__), Path("scripts/dsre_evidence_tasks.py"))
                },
                "logged_first": True,
                "learner": "only assigned y; counterparts confined to evaluator files",
                "epoch": time.time(),
            },
        )
    collected = {"discovery": [], "calibration": [], "evaluation": []}
    attempts = []
    vocab = (
        PRIMARY
        if task == "PickCube-v1"
        else NAV_VOCAB
        if task == "PointMaze_UMaze-v3"
        else PEG_VOCAB
    )
    for spec in specs:
        i = spec["index"]
        pid = f"{hashed('development-parent:' + task + ':' + str(spec['seed'])):064x}"
        phase = "discovery" if i < 32 else "calibration" if i < 48 else "evaluation"
        if i == 48:
            for phase0 in ("discovery", "calibration"):
                persist(out / "learner" / (phase0 + ".json"), collected[phase0])
            persist(out / "learner/queries.json", [])
            persist(out / "learner/vocabulary.json", list(vocab))
            if not (out / "models/logged.json").exists():
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "dual_rec.evidence_aware.cli",
                        "learn",
                        str(out),
                        "--regime",
                        "logged",
                    ],
                    check=True,
                    env=os.environ.copy(),
                )
            else:
                model = json.loads((out / "models/logged.json").read_text())
                assert all(
                    sha(Path(p)) == h
                    for p, h in model["input_whitelist_sha256"].items()
                )
            persist(
                out / "library_seal.json",
                {"sha256": sha(out / "models/logged.json"), "epoch": time.time()},
            )
        if phase == "evaluation":
            screen = child(root, spec, "screen", "screen")
            if screen["status"] != "CHECKPOINT_ONLY":
                attempts.append({"spec": spec, "status": screen["status"]})
                continue
            observation = out / "online_observations" / (pid + ".json")
            persist(
                observation,
                {
                    "parent_id": pid,
                    "x": screen["features"],
                    "source_scope": scope.model_dump(mode="json"),
                },
            )
            decision = out / "online_decisions" / (pid + ".json")
            if not decision.exists():
                subprocess.run(
                    [
                        sys.executable,
                        "scripts/dsre_evidence_online.py",
                        str(out / "models/logged.json"),
                        str(observation),
                        str(decision),
                    ],
                    check=True,
                    env=os.environ.copy(),
                )
            else:
                assert json.loads(decision.read_text())["model_sha256"] == sha(
                    out / "models/logged.json"
                )
            assigned = json.loads(decision.read_text())["action"]
        else:
            assigned = arm(task, str(spec["seed"]))
        first = child(root, spec, assigned, "assigned")
        if first["status"] != "COMPLETE":
            attempts.append({"spec": spec, "status": first["status"]})
            continue
        record_type = OneAction if phase != "evaluation" else PolicyExecution
        record = record_type(
            parent_id=pid,
            x=first["features"],
            action=assigned,
            propensity=0.5 if phase != "evaluation" else 1.0,
            y=first["success"],
            controls=len(first["post_controls"]),
            wall_seconds=first["wall_seconds"],
            source_scope=scope,
        )
        # Evaluation policy records are not randomized training logs and never enter fitting.
        logpath = out / "assigned_logs" / (pid + ".json")
        persist(logpath, record.model_dump(mode="json"))
        persist(
            out / "assigned_log_seals" / (pid + ".json"),
            {
                "sha256": sha(logpath),
                "sealed_epoch": time.time(),
                "assignment": "fair randomized behavior"
                if phase != "evaluation"
                else "frozen qualified router with continue fallback; not a randomized training record",
            },
        )
        collected[phase].append(record.model_dump(mode="json"))
        # This separate fresh process starts only after the learner record is sealed.
        other = child(
            root, spec, "r" if assigned == "c" else "c", "evaluator_counterpart"
        )
        persist(
            out / "evaluator" / (pid + ".json"),
            {
                "parent_id": pid,
                "first_action": assigned,
                "first_success": first["success"],
                "counterpart_success": other.get("success"),
                "counterpart_status": other["status"],
                "learner_log_sha256": sha(logpath),
                "first_sealed_before_counterpart": True,
                "yc": first["success"] if assigned == "c" else other.get("success"),
                "yr": first["success"] if assigned == "r" else other.get("success"),
                "spec": spec,
                "phase": phase,
            },
        )
        attempts.append(
            {
                "spec": spec,
                "status": "COMPLETE",
                "phase": phase,
                "assigned_action": assigned,
                "parent_id": pid,
            }
        )
        print(
            json.dumps(
                {"task": task, "index": i, "phase": phase, "status": "COMPLETE"}
            ),
            flush=True,
        )
    save(
        out / "collection_results.json",
        {
            "attempts": attempts,
            "counts": {k: len(v) for k, v in collected.items()},
            "source_type": "genuinely executed single-action records; separately sealed evaluator counterparts",
            "evaluation_note": "Deployed policy records never used as randomized calibration data",
            "stage": "DEVELOPMENT ONLY; full128/1024/256 cohort unexecuted",
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--task", required=True)
    a = p.parse_args()
    collect(a.root, a.task)
