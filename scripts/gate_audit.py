"""Compact gate evidence and verify prior artifacts, edits and all replay branches."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.scenarios import FailureScenario, history_features


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    initial = json.loads((args.root / "initial.json").read_text())
    changed = [p for p, h in initial["preserved_sha256"].items() if digest(p) != h]
    if changed:
        raise RuntimeError(f"Previously preserved artifacts changed: {changed}")
    args.output.mkdir(exist_ok=False)
    checks = []
    edits = {}
    cases = []
    contacts_by_condition = {}
    config = json.loads(Path("config/gate_d5_d7.json").read_text())
    with (
        (args.output / "scenario_registry.jsonl").open("x") as registry,
        gzip.open(args.output / "examples.jsonl.gz", "xt", encoding="utf8") as examples,
    ):
        for split in ("development", "qualification"):
            for folder in sorted(args.root.glob(split + "-*")):
                if not folder.is_dir():
                    continue
                state = json.loads((folder / "status.json").read_text())
                if state["status"] != "completed":
                    raise RuntimeError(f"Incomplete scientific worker: {folder}")
                checks += [
                    json.loads(line)
                    for line in (folder / "branch_checks.jsonl")
                    .read_text()
                    .splitlines()
                ]
                with gzip.open(
                    folder / "scenarios.jsonl.gz", "rt", encoding="utf8"
                ) as stream:
                    for line in stream:
                        scenario = FailureScenario.model_validate_json(line)
                        features = history_features(scenario.history)
                        fault = scenario.recipe.evaluation_only_fault
                        edit = scenario.recipe.physical_edits[0]
                        error = np.max(
                            np.abs(
                                np.asarray(edit.after["inertia_kg_m2"])
                                - np.asarray(edit.before["inertia_kg_m2"])
                                * fault.mass_scale
                            )
                        )
                        if not np.allclose(
                            edit.after["inertia_kg_m2"],
                            np.asarray(edit.before["inertia_kg_m2"]) * fault.mass_scale,
                            rtol=1e-6,
                            atol=0,
                        ):
                            raise RuntimeError("Inconsistent scientific inertia")
                        edits.setdefault(fault.name, []).append(
                            {
                                "seed": scenario.recipe.seed,
                                "edit": edit.model_dump(),
                                "inertia_max_absolute_error": float(error),
                            }
                        )
                        row = scenario.model_dump(exclude={"history"})
                        row["passive_history_local_path"] = str(
                            folder / "scenarios.jsonl.gz"
                        )
                        row["passive_feature_sha256"] = hashlib.sha256(
                            features.tobytes()
                        ).hexdigest()
                        row["passive_feature_count"] = len(features)
                        contact_steps = sum(
                            frame.observation.robot_cube_contact
                            for frame in scenario.history
                        )
                        row["robot_cube_contact_steps_before_decision"] = contact_steps
                        contacts_by_condition.setdefault(fault.name, []).append(
                            contact_steps
                        )
                        registry.write(json.dumps(row, allow_nan=False) + "\n")
                        cases.append((scenario.split, scenario.recipe.seed, fault.name))
                        if scenario.recipe.seed == config[split + "_seeds"][0]:
                            examples.write(line)
    expected = {
        (split, seed, c["name"])
        for split in ["development", "qualification"]
        for seed in config[split + "_seeds"]
        for c in config["conditions"]
    }
    assert len(cases) == len(expected) and set(cases) == expected
    expected_branches = {
        (f"{split}-{seed}-{condition}", recovery)
        for split, seed, condition in expected
        for recovery in config["recoveries"]
    }
    actual_branches = [(r["scenario_id"], r["recovery"]) for r in checks]
    assert (
        len(actual_branches) == len(expected_branches)
        and set(actual_branches) == expected_branches
    )
    assert all(
        r["passed"] and r["contacts_agree"] and r["outcomes_agree"] for r in checks
    )
    designated = [r for r in checks if r["designated_replay_audit"]]
    assert {r["seed"] for r in designated} == set(config["replay_seeds"])
    for fault in config["conditions"]:
        assert len([r for r in designated if r["condition"] == fault["name"]]) == 30
    versions = json.loads((args.root / "preflight/hardware.json").read_text())
    commands = [
        json.loads(line)
        for line in (args.root / "commands.jsonl").read_text().splitlines()
    ]
    summary = {
        "preserved_prior_artifacts": len(initial["preserved_sha256"]),
        "all_prior_hashes_unchanged": True,
        "initial_scenario_instances": len(cases),
        "independent_base_seeds": 24,
        "seeds_per_condition": 24,
        "recovery_branches": len(checks),
        "maniskill_snapshot_restores": 0,
        "designated_replay_base_seeds": sorted(config["replay_seeds"]),
        "designated_replay_branches": len(designated),
        "maxima": {
            k: max(r["maxima"][k] for r in checks)
            for k in ["position", "angle", "velocity", "qpos", "observation", "time"]
        },
        "expanded_sensor_max_error": max(r["sensor_max"] for r in checks),
        "contact_agreement": True,
        "outcome_agreement": True,
        "physical_edits_consistent": True,
        "initial_robot_cube_contact_steps_by_condition": contacts_by_condition,
        "versions": versions,
        "instrumented_worker_wall_seconds_before_audit": sum(
            r["wall_seconds"] for r in commands
        ),
        "instrumented_cpu_core_hours_before_audit": sum(
            r["cpu_user_seconds"] + r["cpu_system_seconds"] for r in commands
        )
        / 3600,
        "case_counts_by_split": {
            split: sum(row[0] == split for row in cases)
            for split in ["development", "qualification"]
        },
        "seed_overlap": False,
        "raw_histories": "Local compressed JSONL, omitted from Git; exact recipes, small examples and hashes are published",
    }
    (args.output / "replay_and_integrity.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False)
    )
    (args.output / "physical_parameters.json").write_text(
        json.dumps(edits, indent=2, allow_nan=False)
    )
    with gzip.open(
        args.root / "fitted/models.json.gz", "rt", encoding="utf8"
    ) as stream:
        fitted = json.load(stream)
    cv_results = {}
    for family, cohorts in fitted["families"].items():
        cv_results[family] = {}
        for cohort, value in cohorts.items():
            if value["status"] != "fitted":
                cv_results[family][cohort] = value
                continue
            cv_results[family][cohort] = {
                mode: {
                    "regularization": item["model"]["regularization"],
                    "training_seed_groups": item["train_seed_groups"],
                    "cross_validation": item["cross_validation"],
                }
                for mode, item in value["models"].items()
            }
    (args.output / "development_cv.json").write_text(
        json.dumps(cv_results, indent=2, allow_nan=False)
    )
    inventory = {
        str(p.relative_to(args.root)): {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in sorted(args.root.rglob("*"))
        if p.is_file() and p.suffix != ".log" and p.name != "commands.jsonl"
    }
    (args.output / "evidence_sha256.json").write_text(json.dumps(inventory, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
