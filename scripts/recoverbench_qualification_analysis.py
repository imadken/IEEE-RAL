"""Summarize source-interface diagnostics and enforce the conditional pilot gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from recoverbench_analysis import cluster_interval

from dual_rec.recoverbench.qualification import (
    EngineeringEvidence,
    engineering_decision,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    audit = json.loads((root / "independent_numerical_audit.json").read_text())
    physics = json.loads((root / "independent_physics_audit.json").read_text())
    assert audit["status"] == physics["status"] == "PASS"
    registration = json.loads((root / "registration.json").read_text())
    identities = json.loads((root / "identity.json").read_text())["tasks"]
    stack = next(t for t in identities if t["task"] == "stack")
    fingerprint_fields = (
        "robosuite_version",
        "mujoco_version",
        "xml_hash",
        "control_freq",
        "timestep",
    )
    matches = all(
        stack["actual_fingerprint"][k] == stack["expected_fingerprint"][k]
        for k in fingerprint_fields
    )
    generation = json.loads((root / "generation_preflight.json").read_text())
    evidence = EngineeringEvidence(
        qualified_model=matches and stack["actual_class"] == "Stack_D0",
        source_semantics_identified=True,
        official_generation_works=generation["status"] != "SOURCE_GENERATION_BLOCKED"
        and generation["generation_attempts"] > 0,
        independently_successful_scenes=0,
        distinct_recovery_trajectories=0,
        leakage_or_hidden_reset=not audit["source_target_disjoint"]
        or bool(audit["failures"]),
        diagnostic_execution_works=any(r["new_success"] > 0 for r in audit["summary"]),
    )
    result = {
        "gate": engineering_decision(evidence),
        "evidence": evidence.model_dump(),
        "blockers": ["BENCHMARK_COMPATIBILITY_BLOCKED", "SOURCE_GENERATION_BLOCKED"],
        "source_summary": audit["summary"],
        "conditional_pilot_executed": False,
        "B1_B5": None,
        "false_acceptance_rejection": None,
        "method_effect_intervals": None,
        "workflow_comparisons": [],
        "per_error": [],
    }
    for task in ("stack", "pick_place"):
        cases = [s for s in registration["sources"] if s["task"] == task]
        pairs, groups = [], []
        for case in cases:
            matching = {
                r["variant"]: r
                for r in audit["records"]
                if r["case"]["archive_member"] == case["archive_member"]
            }
            a = matching["official_source_checker_shared_environment"]
            b = matching["direct_controls_fresh_reset"]
            pairs.append(
                int(b["first_success_step"] is not None)
                - int(a["first_success_step"] is not None)
            )
            metadata = json.loads(
                (
                    root
                    / "data/training_scenes"
                    / task
                    / "scenes"
                    / (case["scene_id"] + ".json")
                ).read_text()
            )
            groups.append(task + "/" + metadata["dataset"]["trajectory_id"])
        result["workflow_comparisons"].append(
            {
                "task": task,
                "recordings": len(cases),
                "source_scenes": len({c["scene_id"] for c in cases}),
                "clean_parent_groups": len(set(groups)),
                "paired_raw_minus_checker_first_hit_difference": float(np.mean(pairs)),
                "cluster_bootstrap_interval": cluster_interval(pairs, groups),
                "bootstrap_seed": 20261111,
                "bootstrap_repetitions": 2000,
                "scope": "Selected source workflow diagnostics, not ACRR effects; fresh reset and wrapper cache handling change together",
            }
        )
        for error in (
            "grasp_wrong_pose",
            "drop_at_wrong_place",
            "trajectory_regression",
        ):
            for variant in (
                "official_source_checker_shared_environment",
                "direct_controls_fresh_reset",
            ):
                rows = [
                    r
                    for r in audit["records"]
                    if r["case"]["task"] == task
                    and r["case"]["error"] == error
                    and r["variant"] == variant
                ]
                result["per_error"].append(
                    {
                        "task": task,
                        "error": error,
                        "variant": variant,
                        "attempts": len(rows),
                        "first_hit_success": sum(
                            r["first_success_step"] is not None for r in rows
                        ),
                        "initial_success": sum(r["initial_success"] for r in rows),
                    }
                )
    # Explicit feature provenance binds numerical artifacts to executed code and
    # reference model files without claiming the unavailable scene model identity.
    feature_manifest = root / "derived/manifest.json"
    worker = next(
        r
        for r in [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        if r["name"] == "source-checker-controller-and-fk"
    )
    provenance = {
        "feature_manifest_sha256": hashlib.sha256(
            feature_manifest.read_bytes()
        ).hexdigest(),
        "executed_source_sha256": worker["source_sha256"][
            "src/dual_rec/recoverbench/qualification_replay.py"
        ],
        "reference_model_files": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root / "identity").glob("*-factory*")
        },
        "reference_scope": "Factory-reference models; independent all-sample FK matches the generated features exactly. Failure-scene XML equivalence remains unverified.",
        "contains_deployed_selector": False,
        "array_metadata_leakage": "Derived arrays contain state/kinematics only; taxonomy/source labels are separate provenance, never a deployed policy input",
    }
    (root / "derived/provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    (root / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
