"""Independent ordering, controller and outcome recount of the one-arm demonstration."""

import argparse
import hashlib
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_evidence_audit import check_nav, check_peg, equal, read, save


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def audit(root, task):
    out = root / "development" / task
    result = read(out / "collection_results.json")
    classes = Counter()
    counts = Counter()
    checks = 0
    deployed = []
    for attempt in result["attempts"]:
        if attempt["status"] != "COMPLETE":
            continue
        pid = attempt["parent_id"]
        i = attempt["spec"]["index"]
        phase = attempt["phase"]
        d = root / "physics" / task / "development" / str(i)
        first = read(d / "assigned.json.gz")
        other = read(d / "evaluator_counterpart.json.gz")
        assert first["status"] == "COMPLETE"
        paired = other["status"] == "COMPLETE"
        if paired:
            equal(first["prefix"], other["prefix"])
            equal(first["prefix_controls"], other["prefix_controls"])
            equal(first["checkpoint"], other["checkpoint"])
            equal(first["features"], other["features"])
        else:
            counts["counterpart_unavailable"] += 1
        for branch in [first, other] if paired else [first]:
            if task == "PointMaze_UMaze-v3":
                check_nav(branch)
            elif task == "PegInsertionSide-v1":
                assert len(branch["post"]) == 400
                geometry = read(
                    root
                    / "geometry/development"
                    / (str(attempt["spec"]["seed"]) + ".json")
                )
                check_peg(branch, geometry)
            else:
                from dsre_source_risk_audit import difference, expected_action, vec

                assert len(branch["post"]) == 70
                previous = branch["checkpoint"]
                for j, (command, state) in enumerate(
                    zip(branch["post_controls"], branch["post"], strict=True)
                ):
                    expected = expected_action(
                        "PickCube-v1",
                        "continue" if branch["action"] == "c" else "recover",
                        j,
                        previous["observation"],
                        branch["initial_tcp"],
                    )
                    assert difference(command, expected) < 2e-6
                    assert abs(state["time"] - previous["time"] - 0.05) < 1e-8
                    previous = state
                obs = previous["observation"]
                distance = np.linalg.norm(vec(obs, "obj_pose") - vec(obs, "goal_pos"))
                qvel = np.asarray(obs["agent"]["qvel"]).reshape(-1)[:-2]
                assert branch["success"] == bool(
                    distance <= 0.025 and np.max(abs(qvel)) <= 0.2
                )
        seal = read(out / "assigned_log_seals" / (pid + ".json"))
        logged = read(out / "assigned_logs" / (pid + ".json"))
        assert seal["sha256"] == sha(out / "assigned_logs" / (pid + ".json"))
        execution = read(d / "evaluator_counterpart.execution.json")
        # start is reconstructed from recorded wall time and absolute invocation end metadata below.
        # File mtimes alone are not used as an experimental timestamp.
        start_epoch = execution.get(
            "started_epoch",
            (d / "evaluator_counterpart.execution.json").stat().st_mtime
            - execution["wall_seconds"],
        )
        assert seal["sealed_epoch"] <= start_epoch
        if phase == "evaluation":
            first_execution = read(d / "assigned.execution.json")
            first_start = first_execution.get(
                "started_epoch",
                (d / "assigned.execution.json").stat().st_mtime
                - first_execution["wall_seconds"],
            )
            assert (
                read(out / "online_decisions" / (pid + ".json"))[
                    "selected_before_execution_epoch"
                ]
                <= first_start
            )
        evaluator = read(out / "evaluator" / (pid + ".json"))
        assert logged["y"] == first["success"] and logged["action"] == first["action"]
        assert not logged["counterpart_exposed"]
        yc = first["success"] if first["action"] == "c" else other.get("success")
        yr = first["success"] if first["action"] == "r" else other.get("success")
        assert evaluator["yc"] == yc and evaluator["yr"] == yr
        if paired:
            classes[f"{int(yc)}{int(yr)}"] += 1
        counts[phase] += 1
        checks += int(paired)
        if phase == "evaluation":
            decision = read(out / "online_decisions" / (pid + ".json"))
            library = read(out / "library_seal.json")
            assert (
                library["sha256"]
                == decision["model_sha256"]
                == sha(out / "models/logged.json")
            )
            assert (
                library["epoch"]
                <= decision["selected_before_execution_epoch"]
                <= seal["sealed_epoch"]
            )
            assert decision["action"] == first["action"]
            assert all(
                "/evaluator/" not in name for name in decision["successful_data_reads"]
            )
            # Canonical policy view distinguishes deterministic deployment from randomized training.
            canonical = dict(
                logged, propensity=1.0, source_type="deterministic_frozen_policy"
            )
            save(
                out / "policy_executions" / (pid + ".json"),
                {
                    "execution": canonical,
                    "original_sealed_record_sha256": seal["sha256"],
                    "metadata_note": "Randomized calibration never uses these records. Legacy navigation export used placeholder .5; corrected policy view has actual assignment probability1."
                    if logged["propensity"] != 1
                    else "Deterministic execution, excluded from randomized calibration.",
                },
            )
            deployed.append(
                {
                    "parent_id": pid,
                    "recover": first["action"] == "r",
                    "certified": decision["certificate"] is not None,
                    "success": first["success"],
                    "yc": yc,
                    "yr": yr,
                }
            )
    model = read(out / "models/logged.json")
    train_ids = {
        r["parent_id"]
        for r in read(out / "learner/discovery.json")
        + read(out / "learner/calibration.json")
    }
    assert not train_ids & {r["parent_id"] for r in deployed}
    recovers = sum(r["recover"] for r in deployed)
    save(
        out / "independent_development_audit.json",
        {
            "passed": True,
            "counts": dict(counts),
            "paired_checkpoints_checked": checks,
            "classes_all_development": dict(classes),
            "deployed_parents": len(deployed),
            "certified_recover": sum(r["certified"] for r in deployed),
            "default_continue": len(deployed) - recovers,
            "policy_success": sum(r["success"] for r in deployed),
            "continue_success": sum(r["yc"] for r in deployed),
            "paired_recover_success": sum(r["yr"] is True for r in deployed),
            "paired_recover_known": sum(r["yr"] is not None for r in deployed),
            "failed_first_or_screen_attempts": len(result["attempts"])
            - sum(counts.get(k, 0) for k in ("discovery", "calibration", "evaluation")),
            "harmful_recoveries": sum(
                r["recover"] and r["yc"] is True and r["yr"] is False for r in deployed
            ),
            "gain_total": sum(
                int(r["success"]) - int(r["yc"])
                for r in deployed
                if r["yc"] is not None
            ),
            "gain_known_parents": sum(r["yc"] is not None for r in deployed),
            "attrition_note": "Missing assigned outcomes and unavailable counterparts are retained, never imputed; attrition can block population inference.",
            "randomized_training_source": "one action only, counterpart_exposed=False; sealed before evaluator",
            "deployed_source": "deterministic frozen policy, propensity1, never used for randomized CP",
            "future_outcomes_seen_by_learner": False,
            "intervals": "Small development demonstration; no confirmation claim",
            "training_counts": model["counts"],
        },
    )
    print(task, dict(counts), dict(classes), len(deployed), recovers, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--task", required=True)
    a = p.parse_args()
    audit(a.root, a.task)
