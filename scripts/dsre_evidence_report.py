"""Consolidate verified evidence without changing any manuscript or old seal."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from dsre_evidence_audit import read, save

TASKS = ("PickCube-v1", "PegInsertionSide-v1", "PointMaze_UMaze-v3")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    a = p.parse_args()
    root = a.root
    historical = root / "historical"
    regimes = {
        r: read(historical / "evaluations" / (r + ".json"))
        for r in (
            "logged",
            "paired_equal_parent",
            "paired_equal_execution",
            "observational",
        )
    }
    models = {r: read(historical / "models" / (r + ".json")) for r in regimes}
    demonstrations = {
        t: read(root / "development" / t / "independent_development_audit.json")
        for t in TASKS
    }
    acquisition = {
        s: read(historical / "acquisition" / s / "acquisition_result.json")
        for s in (
            "witness",
            "all_logs",
            "all_pairs",
            "uniform_mix",
            "decision_uncertainty",
        )
    }
    physics = [read(p) for p in (root / "physics").rglob("*.execution.json")]
    task_costs = {}
    for t in TASKS:
        entries = []
        for d in (root / "physics" / t / "development").glob("*"):
            if not d.is_dir():
                continue
            for name in ("assigned", "evaluator_counterpart", "screen"):
                path = d / (name + ".json.gz")
                receipt = d / (name + ".execution.json")
                if path.exists() and receipt.exists():
                    b = read(path)
                    r = read(receipt)
                    entries.append(
                        {
                            "status": b["status"],
                            "wall_seconds": r["wall_seconds"],
                            "cpu_seconds": r["cpu_seconds"],
                            "planning_seconds": b.get("planning_seconds"),
                            "controls": len(b.get("post_controls", [])),
                            "prefix_controls": len(b.get("prefix_controls", [])),
                        }
                    )
        paired = [e for e in entries if e["status"] == "COMPLETE"]
        average = (
            sum(e["wall_seconds"] for e in paired) / len(paired) if paired else None
        )
        task_costs[t] = {
            "worker_invocations": len(entries),
            "post_controls": sum(e["controls"] for e in entries),
            "prefix_replay_controls": sum(e["prefix_controls"] for e in entries),
            "prefix_generation_controls": sum(e["prefix_controls"] for e in entries)
            if t == "PickCube-v1"
            else 0,
            "total_physical_controls": sum(
                e["controls"] + e["prefix_controls"] * (2 if t == "PickCube-v1" else 1)
                for e in entries
            ),
            "worker_wall_seconds": sum(e["wall_seconds"] for e in entries),
            "worker_cpu_seconds": sum(e["cpu_seconds"] for e in entries),
            "total_planning_seconds_including_prefix": sum(
                e["planning_seconds"] or 0 for e in entries
            ),
            "complete_branch_mean_wall_seconds": average,
            "forecast_full1408_single_arm_worker_seconds": average * 1408
            if average
            else None,
            "forecast_full1408_with_counterparts_worker_seconds": average * 2816
            if average
            else None,
            "planning_note": "Total recorded planning includes prefix; no artificial delay or selected conversion to gain.",
        }
    known = read(root / "historical/historical_physical_audit.json")
    future = read(root / "prospective_manifest.json")
    for name in models:
        assert all(
            v == 314
            for k, v in models[name]["equal_action_counts_vs_DSRE"].items()
            if k
            in (
                "ordinary_rules",
                "tabular_Kallus_adaptation",
                "Li_no_harm_adaptation",
                "CART2_matched",
                "ensemble_matched",
                "DISCRET_style_adaptation",
            )
        )
    for t in TASKS:
        assert demonstrations[t]["passed"]
    initial = read(root / "initial.json")
    changed = []
    for name, wanted in initial["tracked_hashes"].items():
        path = Path(name)
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != wanted
        ):
            changed.append(name)
    assert not changed, changed
    preservation = {
        "tracked_files_checked": len(initial["tracked_hashes"]),
        "changed": changed,
        "manuscripts_unchanged": True,
        "gitignore_and_uv_lock_unchanged": True,
    }
    bytes_now = sum(
        p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink()
    )
    resources = {
        "wall_seconds_since_research_start": time.time()
        - initial["research_start_epoch"],
        "measured_physics_worker_wall_seconds": sum(p["wall_seconds"] for p in physics),
        "measured_physics_worker_cpu_seconds": sum(p["cpu_seconds"] for p in physics),
        "offline_geometry_and_unmetered_tool_CPU_reserve_seconds": 3600,
        "charged_cpu_seconds_conservative": sum(p["cpu_seconds"] for p in physics)
        + 3600,
        "new_logical_bytes_including_isolated_navigation_environment": bytes_now,
        "new_download_payload_upper_bound_bytes": 256 * 1024**2,
        "download_note": "Five large wheel payloads reported58.4MiB total, remaining wheels/metadata small; conservative256MiB envelope. No existing environment upgrade.",
        "new_paid_APIs": 0,
        "GPU_training": False,
        "large_confirmation_cohort_launched": False,
    }
    assert resources["wall_seconds_since_research_start"] < 43200
    assert resources["charged_cpu_seconds_conservative"] < 43200
    assert resources["measured_physics_worker_wall_seconds"] + 600 < 21600
    assert (
        resources["new_logical_bytes_including_isolated_navigation_environment"]
        < 2 * 1024**3
    )
    summary = {
        "status": "BOUNDED_DEVELOPMENT_IMPLEMENTED; C3_ADVANTAGE_NOT_ESTABLISHED",
        "local_base": initial["head"],
        "design_commit": "607a149524ebd0a31db298299d4973f97005bec7",
        "historical": known,
        "regimes": regimes,
        "models": {
            r: {
                k: v
                for k, v in m.items()
                if k
                in (
                    "counts",
                    "execution_budget",
                    "common_discovery_execution_budget",
                    "partition",
                    "leaves",
                    "equal_action_counts_vs_DSRE",
                )
            }
            for r, m in models.items()
        },
        "demonstrations": demonstrations,
        "acquisition": acquisition,
        "costs_and_forecasts": task_costs,
        "resources": resources,
        "preservation": preservation,
        "supervisor": read(root / "supervisor_reproduced.json"),
        "numerical_audit": read(historical / "independent_numerical_audit.json"),
        "statistical_audit": read(historical / "independent_statistical_audit.json"),
        "initial_state_composition": read(
            historical / "initial_state_outcome_composition.json"
        ),
        "controls": read(root / "production_controls.json"),
        "remaining_fixed_work": [
            "128 discovery /1024 calibration /256 evaluation fresh parents per eligible domain; not launched",
            "resolve source-defined insertion aperture predicate and prospective handling of planner/recording failures before any qualified full study",
            "full-budget witness utility comparison; current64-outcome experiment has zero qualified coverage for every strategy",
            "supervisor review of scoped soundness assumptions and incremental novelty; no new theorem claim",
            "no sim-to-real or real-hardware claim",
        ],
    }
    save(root / "implementation_results.json", summary)
    ready = dict(future)
    ready.update(
        source_registry={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in list(Path("src/dual_rec/evidence_aware").glob("*.py"))
            + list(Path("scripts").glob("dsre_evidence*.py"))
        },
        task_qualification={
            "PegInsertionSide-v1": read(
                root / "PegInsertionSide-v1-qualification-interface3.json"
            ),
            "PointMaze_UMaze-v3": read(
                root / "PointMaze_UMaze-v3-qualification-interface2.json"
            ),
        },
        full_study_first_session_authorized=False,
        forecast=task_costs,
        insertion_qualification_for_inference="BLOCKED: unknown aperture predicate; complete logging/selection assumptions require review",
        confidence="95percent per task at one frozen allocation; not simultaneous across regimes, budgets or publication iterations",
    )
    save(root / "prospective_ready_manifest.json", ready)
    save(root / "preservation_audit.json", preservation)
    save(root / "resources.json", resources)
    print(
        json.dumps(
            {
                "resources": resources,
                "development": {t: demonstrations[t]["counts"] for t in TASKS},
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
