"""Audit released array contracts and blind scene disjointness without success labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np


def state_digest(task: str, subtype: str, state: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(task.encode())
    digest.update(b"\0")
    digest.update(subtype.encode())
    digest.update(b"\0")
    digest.update(np.asarray(state, dtype="<f8").tobytes())
    return digest.hexdigest()


def audit_release(root: Path, output: Path):
    if output.exists():
        raise FileExistsError("Never overwrite a release audit")
    source = next((root / "upstream/source").iterdir())
    rows = list(csv.DictReader((source / "metadata/mimicgen_generated.csv").open()))
    counts = Counter()
    tasks = Counter()
    alignment = Counter()
    failures = []
    members = []
    for row in rows:
        path = root / "data" / row["archive_member"]
        with np.load(path, allow_pickle=False) as arrays:
            actions, states = arrays["actions"], arrays["states"]
            eef = arrays["eef_positions"]
            counts["files"] += 1
            tasks[row["task_name"]] += 1
            counts["actions"] += len(actions)
            counts["seven_action_dimensions"] += int(
                actions.ndim == 2 and actions.shape[1] == 7
            )
            alignment[str(len(states) - len(actions))] += 1
            finite = bool(np.isfinite(actions).all() and np.isfinite(states).all())
            counts["finite_actions_and_states"] += int(finite)
            moving = bool(np.any(np.ptp(states[:, 1:], axis=0) > 1e-8))
            constant_eef = bool(np.all(np.ptp(eef, axis=0) <= 1e-10))
            counts["moving_state_trajectory"] += int(moving)
            counts["constant_recorded_eef"] += int(constant_eef)
            counts["moving_state_with_constant_eef"] += int(moving and constant_eef)
            counts["missing_success_label_in_index"] += int(
                row.get("success", "") == ""
            )
            counts["stored_success_field"] += int("success" in arrays.files)
            counts["stored_gripper_field"] += int("gripper_states" in arrays.files)
            counts["stored_target_waypoints"] += int("target_poses" in arrays.files)
            counts["stored_orientation_field"] += int(
                "eef_orientations" in arrays.files
            )
            if row.get("scene_id"):
                target = (
                    root
                    / "data/training_scenes"
                    / row["task_name"]
                    / "scenes"
                    / (row["scene_id"] + ".npz")
                )
                counts["source_scene_exists"] += int(target.exists())
            if not finite:
                failures.append(
                    {"member": row["archive_member"], "reason": "NONFINITE"}
                )
            members.append(
                {
                    "member": row["archive_member"],
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "task": row["task_name"],
                    "steps": len(actions),
                    "constant_eef": constant_eef,
                    "moving_state": moving,
                }
            )
    ids, states_by_split = {}, {}
    for split, directory in (
        ("training", "training_scenes"),
        ("evaluation", "error_scenes"),
    ):
        scene_ids, hashes = set(), set()
        for task_dir in sorted((root / "data" / directory).iterdir()):
            for path in sorted((task_dir / "scenes").glob("*.npz")):
                metadata = json.loads(path.with_suffix(".json").read_text())
                labels = metadata.get("labels", {})
                spec = metadata["error_spec"]
                subtype = (
                    labels.get("subtype_id") or f"{spec['error_name']}_{spec['degree']}"
                )
                with np.load(path, allow_pickle=False) as arrays:
                    hashes.add(
                        state_digest(task_dir.name, subtype, arrays["post_sim_state"])
                    )
                scene_ids.add(path.stem)
        ids[split], states_by_split[split] = scene_ids, hashes
    result = {
        "status": "COMPLETE_ARRAY_AND_SPLIT_AUDIT",
        "counts": dict(counts),
        "per_task": dict(tasks),
        "states_minus_actions_length": dict(alignment),
        "array_errors": failures,
        "scene_counts": {k: len(v) for k, v in ids.items()},
        "shared_scene_ids": sorted(ids["training"] & ids["evaluation"]),
        "shared_task_subtype_state_hashes": len(
            states_by_split["training"] & states_by_split["evaluation"]
        ),
        "scene_audit_scope": "Blind one-way split hashing only; no evaluation features, policy fitting or recovery outcomes computed",
        "success_scope": "Empty release-index success values are missing, never failure/success labels; no recovery inferred from labels or state reconstruction",
        "recorded_eef_scope": "Constant recorded EEF plus moving simulator coordinates is a contract warning; sampled physical forward-kinematics replay establishes the actual discrepancy",
        "members": members,
        "source_index_sha256": hashlib.sha256(
            (source / "metadata/mimicgen_generated.csv").read_bytes()
        ).hexdigest(),
    }
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_release(args.root, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "members"}))


if __name__ == "__main__":
    main()
