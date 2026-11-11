"""Recheck saved predicate snapshots through the independently imported simulator.

Restored snapshots are offline diagnostics, never executed recovery successes.
Contact caches can differ after forwarding; report every disagreement explicitly.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml


def check(root: Path, split: str):
    source = next((root / "upstream/source").iterdir())
    sys.path.insert(0, str(source))
    from error_benchmark.scripts.utils.script_utils import create_env

    rows = [
        json.loads(line)
        for line in (root / split / "outcomes.jsonl").read_text().splitlines()
    ]
    checked, mismatches, stored = [], [], []
    for task in ("pick_place", "stack"):
        config = yaml.safe_load(
            (source / "error_benchmark/configs/tasks" / (task + ".yaml")).read_text()
        )
        np.random.seed(3101)
        env = create_env(
            config,
            str(root / "data/seed_demos" / (task + ".hdf5")),
            enable_camera=False,
            has_renderer=False,
        )
        env.reset()
        seen = set()
        try:
            for row in rows:
                case = row.get("case", row.get("pair", {}))
                row_task = case.get("task_name", case.get("target_task"))
                if task != row_task or row.get("error"):
                    continue
                retained = {}
                with gzip.open(root / row["trace_path"], "rt") as trace:
                    for line in trace:
                        frame = json.loads(line)
                        if frame["kind"] == "initial":
                            retained["initial"] = frame
                        else:
                            retained["terminal"] = frame
                            if (
                                frame["official_success"]
                                and "first_success" not in retained
                            ):
                                retained["first_success"] = frame
                for kind, frame in retained.items():
                    # Independent reconstruction: no replay-worker restore helper.
                    env.sim.set_state_from_flattened(np.asarray(frame["state"]))
                    env.sim.forward()
                    actual = bool(env._check_success())
                    record = {
                        "task": task,
                        "trace": row["trace_path"],
                        "kind": kind,
                        "step": frame.get("step", 0),
                        "recorded_predicate": frame["official_success"],
                        "reconstructed_predicate": actual,
                        "matches": actual == frame["official_success"],
                    }
                    checked.append(record)
                    if not record["matches"]:
                        mismatches.append(record)
                member = case.get("archive_member", case.get("source_member"))
                if member not in seen:
                    seen.add(member)
                    with np.load(root / "data" / member, allow_pickle=False) as arrays:
                        for index in (0, len(arrays["states"]) - 1):
                            env.sim.set_state_from_flattened(arrays["states"][index])
                            env.sim.forward()
                            stored.append(
                                {
                                    "task": task,
                                    "member": member,
                                    "state_index": index,
                                    "reconstructed_task_predicate": bool(
                                        env._check_success()
                                    ),
                                    "scope": "Stored-state geometry only, never counted as executed recovery",
                                }
                            )
        finally:
            env.close()
    return {
        "status": "PASS" if not mismatches else "SNAPSHOT_PREDICATE_DISAGREEMENT",
        "split": split,
        "checked_snapshots": len(checked),
        "mismatches": mismatches,
        "checked": checked,
        "stored_source_snapshots": stored,
        "scope": "Offline independent state-forwarding predicate check; does not waive fingerprint or establish full replay fidelity",
        "outcome_sha256": hashlib.sha256(
            (root / split / "outcomes.jsonl").read_bytes()
        ).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument(
        "--split", choices=("source-replay", "transfer-audit"), required=True
    )
    args = parser.parse_args()
    output = args.root / args.split / "physics_audit.json"
    if output.exists():
        raise FileExistsError("Do not overwrite independent physics checks")
    result = check(args.root.resolve(), args.split)
    output.write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"checked", "stored_source_snapshots"}
            }
        )
    )


if __name__ == "__main__":
    main()
