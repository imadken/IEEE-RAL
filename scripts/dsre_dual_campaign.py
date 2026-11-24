"""Frozen-source transport with separate dual-obligation decision sidecars."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from dsre_dual_adjudication import gz, read, sha, write_once
from dsre_runtime_recovery import ENV_FIELDS, configured_environment, probe


def environment(root):
    freeze = read(root / "source_freeze.json")
    for field in ("source_sha256", "input_sha256"):
        for path, expected in freeze[field].items():
            assert sha(Path(path)) == expected, path
    config = read(root / "execution_configuration.json")
    env = configured_environment(config["overrides"])
    assert {name: env.get(name) for name in ENV_FIELDS} == config[
        "process_configuration"
    ]
    fingerprint = read(root / "runtime_candidate_fingerprint.json")
    for path, fields in fingerprint["native_binaries"].items():
        assert sha(Path(path)) == fields["sha256"], path
    for fields in fingerprint["old_package_hash_comparison"]["files"]:
        assert sha(Path(fields["path"])) == fields["expected"]
    if (root / "source_qualification_seal.json").exists():
        seal = read(root / "source_qualification_seal.json")
        assert seal["passed"] and seal["source_freeze_sha256"] == sha(
            root / "source_freeze.json"
        )
        assert seal["qualification_audit_sha256"] == sha(
            root / "qualification_audit.json"
        )
        assert seal["process_configuration_sha256"] == sha(
            root / "execution_configuration.json"
        )
    assert not (root / "completion_manifest.json").exists()
    return env


def measured(root, label, script, *arguments):
    subprocess.run(
        [
            sys.executable,
            "scripts/dsre_source_risk_meter.py",
            str(root),
            label,
            "--",
            sys.executable,
            script,
            *map(str, arguments),
        ],
        env=environment(root),
        check=True,
    )


def qualify(root):
    assert read(root / "prior_replication.json")["passed"]
    plan = read(root / "study_plan.json")
    assert plan["qualification_seeds"] == [13000000, 13000001, 13000002]
    for index in range(3):
        result = probe(
            root,
            f"qualification_{index}",
            [
                sys.executable,
                "scripts/dsre_source_risk.py",
                "parent",
                str(root),
                "--stage",
                "qualification",
                "--index",
                str(index),
            ],
            timeout=360,
            overrides=read(root / "execution_configuration.json")["overrides"],
            domain="host",
        )
        if result.returncode or result.timed_out:
            write_once(
                root / "study_halt.json",
                {
                    "stage": "qualification",
                    "index": index,
                    "returncode": result.returncode,
                    "epoch": time.time(),
                },
            )
            raise RuntimeError(
                "Fresh-process qualification failed; no new cohort physics"
            )
        measured(
            root,
            f"qualification_parity_{index}",
            "scripts/dsre_runtime_parity.py",
            "parent",
            root,
            "--index",
            index,
        )
    counts = Counter()
    reports = {}
    for index in range(3):
        path = root / f"parity-{index:04d}.json"
        record = read(path)
        assert record["passed"]
        counts.update(record["counts"])
        reports[str(path)] = sha(path)
    assert counts["cells"] == 15 and counts["continuations"] == 30
    write_once(
        root / "qualification_audit.json",
        {
            "passed": True,
            "parents": 3,
            "counts": dict(counts),
            "reports_sha256": reports,
            "epoch": time.time(),
        },
    )
    write_once(
        root / "source_qualification_seal.json",
        {
            "passed": True,
            "source_freeze_sha256": sha(root / "source_freeze.json"),
            "qualification_audit_sha256": sha(root / "qualification_audit.json"),
            "process_configuration_sha256": sha(root / "execution_configuration.json"),
            "qualified_epoch": time.time(),
        },
    )
    print(json.dumps({"qualified": True, "counts": dict(counts)}))


def seal_calibration(root):
    from dual_rec.dsre.dual_obligation import calibrate

    environment(root)
    assert read(root / "calibration_physics_audit.json")["complete_cohort"]
    rows = gz(root / "calibration_rows.json.gz")
    plan = read(root / "study_plan.json")
    decision = {
        "complete_cohort": True,
        "parents": 256,
        "family_alpha": 0.05,
        "family_size": 6,
        "bounds": calibrate(rows, tuple(plan["calibration_seeds"])),
        "plan_sha256": sha(root / "study_plan.json"),
        "physical_audit_sha256": sha(root / "calibration_physics_audit.json"),
        "scope": "Separate absolute-success versus binary task-nondegradation annotation; original DSRE adequacy and solver unchanged; independent new-source parents only",
        "epoch": time.time(),
    }
    write_once(root / "dual_calibration.json", decision)
    write_once(
        root / "dual_calibration_seal.json",
        {"sha256": sha(root / "dual_calibration.json"), "epoch": time.time()},
    )
    measured(
        root, "six_claim_independent_audit", "scripts/dsre_dual_gate_audit.py", root
    )
    # Byte-identical historical gate for unchanged collector transport only.
    # It supplies no new-source qualification or additional alpha allocation.
    prior = Path(read(root / "initial.json")["prior_root"])
    (root / "calibration_decision.json").write_bytes(
        (prior / "calibration_decision.json").read_bytes()
    )
    write_once(
        root / "calibration_seal.json",
        {
            "sha256": sha(root / "calibration_decision.json"),
            "scope": "Preserved historical gate, descriptive legacy comparator only",
            "epoch": time.time(),
        },
    )
    write_once(
        root / "calibration_decision_audit.json",
        {
            "passed": True,
            "calibration_sha256": sha(root / "calibration_decision.json"),
            "scope": "Byte identity with historical gate only; new claims exist exclusively in dual_calibration_audit.json",
            "epoch": time.time(),
        },
    )
    write_once(
        root / "legacy_gate_provenance.json",
        {
            "prior_root": str(prior),
            "original_gate_sha256": sha(prior / "calibration_decision.json"),
            "new_source_guarantee_claimed": False,
            "new_claim_family": "Exactly six in dual_calibration.json; historical34 are not recalibrated or reallocated",
        },
    )
    print(json.dumps(decision))


def seal_test(root):
    from dsre_source_risk import seal_test as original_seal_test

    from dual_rec.dsre.dual_obligation import annotated_action

    original_seal_test(root)
    cal = read(root / "dual_calibration.json")
    assert read(root / "dual_calibration_audit.json")["calibration_sha256"] == sha(
        root / "dual_calibration.json"
    )
    parents = {}
    for seed in read(root / "study_plan.json")["test_seeds"]:
        directory = root / "test" / str(seed)
        assert not list(directory.glob("*/continue.json.gz")) and not list(
            directory.glob("*/recover.json.gz")
        )
        original = read(directory / "decision.json")
        decisions = {}
        for condition in original["screens"]:
            raw = gz(directory / condition / "screen.json.gz")
            assert (
                sha(directory / condition / "screen.json.gz")
                == original["screens"][condition]
            )
            proposals = raw["scenarios"]["clean"]["point_proposal"]
            decisions[condition] = {}
            for method in ("DSRE_risk", "B7_risk", "CART2_beta10"):
                key = "DSRE_risk" if method == "B7_risk" else method
                decisions[condition][method] = {
                    mode: annotated_action(
                        proposals[method]["action"], key, mode, cal["bounds"]
                    )
                    for mode in ("absolute", "nondegradation")
                }
        path = directory / "dual_decision.json"
        write_once(
            path,
            {
                "seed": seed,
                "decisions": decisions,
                "original_decision_sha256": sha(directory / "decision.json"),
                "dual_calibration_sha256": sha(root / "dual_calibration.json"),
                "sealed_epoch": time.time(),
            },
        )
        parents[str(seed)] = sha(path)
    write_once(
        root / "dual_test_seal.json",
        {
            "parents": parents,
            "parent_count": 128,
            "original_test_seal_sha256": sha(root / "test_recommendation_seal.json"),
            "dual_calibration_sha256": sha(root / "dual_calibration.json"),
            "epoch": time.time(),
        },
    )


def run(root, stage):
    assert read(root / "qualification_audit.json")["passed"]
    plan = read(root / "study_plan.json")
    target = len(
        plan["test_seeds" if stage.startswith("test") else "calibration_seeds"]
    )
    while len(list((root / "progress").glob(stage + "-*.json"))) < target:
        env = environment(root)
        if (root / "study_halt.json").exists() or (
            root / "resource_boundary.json"
        ).exists():
            break
        if stage.startswith("test"):
            assert read(root / "dual_calibration_audit.json")["passed"]
        if stage == "test_outcome":
            seal = read(root / "dual_test_seal.json")
            assert len(seal["parents"]) == 128
            for seed, expected in seal["parents"].items():
                assert sha(root / "test" / seed / "dual_decision.json") == expected
        physics = sum(
            read(p)["wall_seconds"] for p in (root / "chunks").glob("chunk-*.json")
        ) + sum(
            read(p)["wall_seconds"]
            for p in (root / "diagnostics").glob("qualification_*.json")
        )
        if physics + 840 > 25200:
            write_once(
                root / "resource_boundary.json",
                {
                    "physics_seconds_including_qualification": physics,
                    "epoch": time.time(),
                },
            )
            break
        before = len(list((root / "progress").glob(stage + "-*.json")))
        with (root / (stage + "_control.log")).open("a") as log:
            child = subprocess.Popen(
                [
                    sys.executable,
                    "scripts/dsre_source_risk.py",
                    "chunk",
                    str(root),
                    "--stage",
                    stage,
                ],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                status = child.wait(timeout=850)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                write_once(
                    root / "study_halt.json",
                    {
                        "stage": stage,
                        "reason": "Owned chunk process-group timeout; preserve all attempts",
                        "epoch": time.time(),
                    },
                )
                raise
            if status:
                raise subprocess.CalledProcessError(status, child.args)
        after = len(list((root / "progress").glob(stage + "-*.json")))
        if before == after:
            if (root / "study_halt.json").exists() or (
                root / "resource_boundary.json"
            ).exists():
                break
            raise RuntimeError("No progress; preserve attempted parents")
        if stage == "calibration" and after == 24:
            write_once(
                root / "pacing_24.json",
                {
                    "parents_complete": 24,
                    "unchanged_cohort_members": True,
                    "physics_wall_seconds_including_qualification": physics,
                    "no_outcome_based_adjustment": True,
                    "epoch": time.time(),
                },
            )
    progress = [read(p) for p in (root / "progress").glob(stage + "-*.json")]
    complete = len(progress) == target and all(
        p["status"] == "COMPLETE" for p in progress
    )
    if complete and stage == "test_screen":
        seal_test(root)
    write_once(
        root / (stage + "_boundary.json"),
        {"complete": complete, "parents": len(progress), "epoch": time.time()},
    )
    print(json.dumps({"stage": stage, "complete": complete, "parents": len(progress)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("qualify", "calibrate", "calibration", "test_screen", "test_outcome"),
    )
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.mode == "qualify":
        qualify(args.root)
    elif args.mode == "calibrate":
        seal_calibration(args.root)
    else:
        run(args.root, args.mode)
