"""Summarize the registered, unqualified RecoverBench interface diagnostics."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def cluster_interval(values, groups, *, seed=20261111, repetitions=2000):
    """Percentile interval, resampling whole original-trajectory clusters."""
    if len(values) != len(groups) or not values:
        raise ValueError("Nonempty values and matching cluster IDs required")
    clusters = defaultdict(list)
    for value, group in zip(values, groups, strict=True):
        clusters[group].append(float(value))
    sums = np.array([sum(v) for v in clusters.values()])
    sizes = np.array([len(v) for v in clusters.values()])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(sizes), size=(repetitions, len(sizes)))
    means = sums[draws].sum(axis=1) / sizes[draws].sum(axis=1)
    return np.quantile(means, [0.025, 0.975]).tolist()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def summarize(root):
    sources = read_rows(root / "source-replay/outcomes.jsonl")
    transfers = read_rows(root / "transfer-audit/outcomes.jsonl")
    original = [
        row
        for row in sources
        if row["repeat"] == 0 and row["variant"] == "recorded_start_no_neutral"
    ]
    neutral = {
        row["case"]["archive_member"]: row
        for row in sources
        if row["repeat"] == 0 and row["variant"] == "official_start_one_neutral"
    }

    def source_group(row):
        case = row["case"]
        meta = json.loads(
            (
                root
                / "data/training_scenes"
                / case["task_name"]
                / "scenes"
                / (case["scene_id"] + ".json")
            ).read_text()
        )
        return case["task_name"] + "/" + meta["dataset"]["trajectory_id"]

    repeat_groups = defaultdict(list)
    for row in sources:
        repeat_groups[(row["case"]["archive_member"], row["variant"])].append(row)
    repeat_checks = []
    for (member, variant), rows in repeat_groups.items():
        if len(rows) < 2:
            continue
        states = []
        for row in rows:
            with gzip.open(root / row["trace_path"], "rt") as stream:
                states.append(np.array([json.loads(s)["state"] for s in stream]))
        repeat_checks.append(
            {
                "source": member,
                "variant": variant,
                "repeats": len(rows),
                "max_state_difference": max(
                    float(np.max(np.abs(state - states[0]))) for state in states[1:]
                ),
            }
        )
    tables = []
    for task in ("pick_place", "stack"):
        for category in (
            None,
            "grasp_wrong_pose",
            "drop_at_wrong_place",
            "trajectory_regression",
        ):
            for degree in (None, "D0", "D1"):
                src = [
                    r
                    for r in original
                    if r["case"]["task_name"] == task
                    and (category is None or r["case"]["error_name"] == category)
                    and (degree is None or r["case"]["degree"] == degree)
                ]
                target = [
                    r
                    for r in transfers
                    if r["pair"]["target_task"] == task
                    and (category is None or r["pair"]["target_error"] == category)
                    and (degree is None or r["pair"]["target_degree"] == degree)
                ]
                scene_groups = defaultdict(list)
                for row in target:
                    scene_groups[row["pair"]["target_scene"]].append(row)
                coverage = [
                    int(any(r["success"] for r in rows))
                    for rows in scene_groups.values()
                ]
                groups = [
                    rows[0]["pair"]["target_source_group"]
                    for rows in scene_groups.values()
                ]
                paired = [
                    int(
                        neutral[r["case"]["archive_member"]][
                            "official_success_observed"
                        ]
                    )
                    - int(r["official_success_observed"])
                    for r in src
                ]
                tables.append(
                    {
                        "task": task,
                        "error": category,
                        "degree": degree,
                        "source_recordings": len(src),
                        "source_scenes": len({r["case"]["scene_id"] for r in src}),
                        "source_parent_groups": len({source_group(r) for r in src}),
                        "source_success": sum(
                            r["official_success_observed"] for r in src
                        ),
                        "source_already_success": sum(
                            r["initial_success"] for r in src
                        ),
                        "source_new_success": sum(
                            r["official_success_observed"] and not r["initial_success"]
                            for r in src
                        ),
                        "neutral_success_difference": float(np.mean(paired)),
                        "paired_cluster_interval": cluster_interval(
                            paired, [source_group(r) for r in src]
                        ),
                        "transfer_attempts": len(target),
                        "transfer_success": sum(r["success"] for r in target),
                        "target_scenes": len(scene_groups),
                        "target_parent_groups": len(set(groups)),
                        "covered_targets": sum(coverage),
                        "diagnostic_coverage_cluster_interval": cluster_interval(
                            coverage, groups
                        ),
                        "max_contact_penetration_m": max(
                            r["max_contact_penetration_m"] for r in target
                        ),
                    }
                )
    geometry = []
    original_by_member = {r["case"]["archive_member"]: r for r in original}
    source_positions = {}
    for member, row in original_by_member.items():
        with gzip.open(root / row["trace_path"], "rt") as stream:
            first = json.loads(next(stream))
        # Initial rows record EEF in the same physical wrapper convention.
        source_positions[member] = first.get("eef")
    for row in transfers:
        position = source_positions[row["pair"]["source_member"]]
        if position is not None:
            geometry.append(
                {
                    "target": row["pair"]["target_scene"],
                    "source": row["pair"]["source_member"],
                    "eef_shift_m": float(
                        np.linalg.norm(np.array(position) - row["initial_eef"])
                    ),
                    "success": row["success"],
                }
            )
    prefix = {}
    for budget in (100, 200, 500):
        covered = {
            r["pair"]["target_scene"]
            for r in transfers
            if r["success"] and r["first_success_step"] <= budget
        }
        prefix[str(budget)] = len(covered)
    return {
        "scope": "Fingerprint-invalid identity-tape diagnostics; NOT official RSR or ACRR evaluation",
        "bootstrap": {
            "seed": 20261111,
            "repetitions": 2000,
            "unit": "original clean trajectory, stratified by reported task/cell",
            "limitation": "Descriptive, conditional intervals; tiny selected clusters, degenerate zero cells, no model-compatibility uncertainty",
        },
        "source_rows": len(sources),
        "transfer_rows": len(transfers),
        "source_counted_steps": sum(r["executed_steps"] for r in sources),
        "target_counted_steps": sum(r["executed_steps"] for r in transfers),
        "repeat_checks": repeat_checks,
        "tables": tables,
        "coverage_by_action_prefix": prefix,
        "geometry": geometry,
        "successful_transfers": [r for r in transfers if r["success"]],
        "main_paired_method_contrast": None,
        "false_rejections": None,
        "rejection_frontier": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    result = summarize(args.root)
    (args.root / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "source_rows",
                    "transfer_rows",
                    "source_counted_steps",
                    "target_counted_steps",
                    "coverage_by_action_prefix",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
