"""Independently recalculate released-source/target control outcome ledgers.

This interpreter imports neither the replay worker nor a selection policy.
Simulator predicate reconstruction is a separate physical check; this audit
verifies actual recorded predicate events and complete action/state accounting.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a, b):
    return math.isclose(a, b, abs_tol=1e-8, rel_tol=1e-10)


def audit(root: Path, split: str):
    directory = root / split
    status = json.loads((directory / "status.json").read_text())
    rows = [
        json.loads(line)
        for line in (directory / "outcomes.jsonl").read_text().splitlines()
    ]
    errors, recomputed = [], []
    seen = set()
    target_states = defaultdict(set)
    expected_total = status["records" if split == "source-replay" else "pairs"]
    if expected_total != len(rows):
        errors.append("Completed-status outcome count mismatch")
    for row in rows:
        if row.get("error"):
            errors.append({"reason": "Recorded execution exception", "row": row})
            continue
        source = row.get("case", row.get("pair"))
        member = source.get("archive_member", source.get("source_member"))
        task = source.get("task_name", source.get("target_task"))
        identity = row.get("record_id") or (source["target_scene"], member)
        if identity in seen:
            errors.append({"identity": identity, "reason": "Duplicate outcome"})
        seen.add(identity)
        source_path = root / "data" / member
        if digest(source_path) != row["source_sha256"]:
            errors.append({"identity": identity, "reason": "Source checksum changed"})
        with np.load(source_path, allow_pickle=False) as arrays:
            actions = arrays["actions"].copy()
            source_start = arrays["states"][0].copy()
        trace_path = root / row["trace_path"]
        if digest(trace_path) != row["trace_sha256"]:
            errors.append({"identity": identity, "reason": "Trace checksum changed"})
        first_success = None
        steps = contacts = 0
        initial = previous = None
        with gzip.open(trace_path, "rt") as stream:
            for line in stream:
                frame = json.loads(line)
                state = np.asarray(frame["state"], dtype=float)
                if not np.isfinite(state).all():
                    errors.append(
                        {"identity": identity, "reason": "Nonfinite trace state"}
                    )
                if frame["kind"] == "initial":
                    if initial is not None or steps:
                        errors.append(
                            {
                                "identity": identity,
                                "reason": "Repeated/out-of-order initialization",
                            }
                        )
                    initial = previous = state
                    if bool(frame["official_success"]) != row["initial_success"]:
                        errors.append(
                            {
                                "identity": identity,
                                "reason": "Initial predicate mismatch",
                            }
                        )
                    continue
                if initial is None:
                    errors.append(
                        {"identity": identity, "reason": "Missing initial frame"}
                    )
                    break
                steps += 1
                if frame["step"] != steps or not np.array_equal(
                    np.asarray(frame["action"]), actions[steps - 1]
                ):
                    errors.append(
                        {
                            "identity": identity,
                            "reason": "Control order/content mismatch",
                        }
                    )
                if not close(float(state[0] - previous[0]), 0.05):
                    errors.append(
                        {
                            "identity": identity,
                            "reason": "Incorrect physical time advance",
                            "step": steps,
                        }
                    )
                previous = state
                contacts += frame["contacts"]
                if frame["official_success"] and first_success is None:
                    first_success = steps
        if steps != row["executed_steps"] or row["first_success_step"] != first_success:
            errors.append(
                {
                    "identity": identity,
                    "reason": "First-success/step denominator mismatch",
                }
            )
        flag = row[
            "official_success_observed" if split == "source-replay" else "success"
        ]
        if flag != (first_success is not None):
            errors.append(
                {
                    "identity": identity,
                    "reason": "Outcome differs from predicate event trace",
                }
            )
        if split == "source-replay":
            if steps != len(actions) or steps > 1500:
                errors.append(
                    {"identity": identity, "reason": "Source horizon mismatch"}
                )
            if row["variant"] == "recorded_start_no_neutral" and not np.array_equal(
                initial, source_start
            ):
                errors.append(
                    {
                        "identity": identity,
                        "reason": "Recorded initial state not restored exactly",
                    }
                )
            if row["variant"] == "official_start_one_neutral" and not close(
                initial[0] - source_start[0], 0.05
            ):
                errors.append(
                    {
                        "identity": identity,
                        "reason": "Neutral initialization not one control step",
                    }
                )
            if not close(row["physics_time_advance"], steps * 0.05):
                errors.append(
                    {"identity": identity, "reason": "Total physical time mismatch"}
                )
        else:
            if steps > 500 or (
                first_success is None and steps != min(len(actions), 500)
            ):
                errors.append(
                    {"identity": identity, "reason": "Target action budget mismatch"}
                )
            if first_success is not None and first_success != steps:
                errors.append(
                    {
                        "identity": identity,
                        "reason": "Transfer continued beyond first success",
                    }
                )
            if contacts != row["contacts_total"]:
                errors.append(
                    {
                        "identity": identity,
                        "reason": "Contact observation count mismatch",
                    }
                )
            current_hash = hashlib.sha256(
                np.asarray(initial, dtype="<f8").tobytes()
            ).hexdigest()
            if current_hash != row["post_neutral_state_sha256"]:
                errors.append(
                    {"identity": identity, "reason": "Target input-state hash mismatch"}
                )
            target_states[task, source["target_scene"]].add(current_hash)
            target_path = (
                root
                / "data/training_scenes"
                / task
                / "scenes"
                / (source["target_scene"] + ".npz")
            )
            if digest(target_path) != row["target_sha256"]:
                errors.append(
                    {"identity": identity, "reason": "Target checksum changed"}
                )
            if source["source_scene"] == source["target_scene"]:
                errors.append(
                    {
                        "identity": identity,
                        "reason": "Own-source scene called a cross-transfer",
                    }
                )
        recomputed.append(
            {
                "task": task,
                "success": first_success is not None,
                "steps": steps,
                "fingerprint_matches": row["fingerprint_matches"],
                "source": member,
                "variant": row.get("variant"),
                "repeat": row.get("repeat"),
                "target": source.get("target_scene"),
                "error_category": source.get("error_name", source.get("target_error")),
                "degree": source.get("degree", source.get("target_degree")),
            }
        )
    if any(len(values) != 1 for values in target_states.values()):
        errors.append(
            "Compared candidate executions did not share identical post-neutral target states"
        )
    groups = defaultdict(list)
    for row in recomputed:
        if split == "source-replay" and row["repeat"] != 0:
            continue
        groups[row["task"], row["variant"]].append(row)
    result = {
        "status": "PASS" if not errors else "FAIL",
        "split": split,
        "checked_rows": len(recomputed),
        "checked_control_steps": sum(r["steps"] for r in recomputed),
        "mismatches": errors,
        "source_replay_unique_candidate_variant_counts": [
            {
                "task": key[0],
                "variant": key[1],
                "attempts": len(cohort),
                "successes": sum(r["success"] for r in cohort),
            }
            for key, cohort in sorted(groups.items(), key=lambda x: str(x[0]))
        ],
        "independent_target_scenes": len(target_states),
        "identical_compared_target_states": all(
            len(v) == 1 for v in target_states.values()
        ),
        "fingerprint_pass_rows": sum(r["fingerprint_matches"] for r in recomputed),
        "scope": "Independent trace arithmetic, source controls and immutable input hashes; simulator predicate-event flags are recalculated temporally, not assumed independently validated physics",
        "source_sha256": {
            str(path): digest(path)
            for path in (
                directory / "status.json",
                directory / "outcomes.jsonl",
                Path(__file__),
            )
        },
        "recomputed": recomputed,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("source-replay", "transfer-audit"), required=True
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.root / args.split / "audit.json"
    if output.exists():
        raise FileExistsError("Preserve previous independent audits")
    result = audit(args.root, args.split)
    output.write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"recomputed", "source_sha256"}
            }
        )
    )
    return int(result["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
