"""Inactive, seed-fixed future protocol reservation. Never run a simulator."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from dual_rec.evidence_aware.views import condition


def write(output):
    output.mkdir(parents=True, exist_ok=True)
    seen_seeds, seen_ids = set(), set()
    counts = Counter()
    offsets = [0.0, 0.01, 0.02, 0.03, -0.02]
    with (output / "reserved_parents.jsonl").open("w") as stream:
        for task, base in [("PickCube-v1", 2003000000), ("PushCube-v1", 2003100000)]:
            phases = [
                ("source_qualification", 0, 4),
                ("discovery", 1000, 128),
                ("planning_base", 2000, 512),
            ]
            phases += [
                (f"calibration_bank_{j}", 10000 + 2000 * j, 1024) for j in range(6)
            ]
            phases += [("untouched_test", 30000, 256)]
            for phase, start, size in phases:
                for index in range(size):
                    seed = base + start + index
                    parent = hashlib.sha256(
                        f"ERR-S2-20261119|{task}|{phase}|{index}|{seed}".encode()
                    ).hexdigest()
                    first_bit = (
                        hashlib.sha256(
                            f"ERR-S2-ARM-v1|{task}|{seed}".encode()
                        ).digest()[0]
                        >> 7
                    )
                    assert (
                        seed not in seen_seeds
                        and parent not in seen_ids
                        and seed < 2**31
                    )
                    seen_seeds.add(seed)
                    seen_ids.add(parent)
                    row = {
                        "task": task,
                        "phase": phase,
                        "index": index,
                        "seed": seed,
                        "parent_id": parent,
                        "assigned_first_arm": ("c", "r")[first_bit],
                        "propensity": "1/2",
                        "status": "RESERVED_NOT_COLLECTED",
                        "eligible": None,
                        "outcome": None,
                    }
                    if task == "PickCube-v1":
                        row["offset"] = offsets[condition(task, str(seed))]
                        row["checkpoint"] = (
                            "Original missed-lift/drop from70, otherwise90 controls"
                        )
                    else:
                        row["condition"] = ("nominal", "misaligned")[index % 2]
                        row["cached_controller_y_offset_m"] = (
                            0 if index % 2 == 0 else 0.07
                        )
                        row["checkpoint"] = "Original fixed53 controls"
                    row["macro_horizon_controls"] = 70
                    counts[task + ":" + phase] += 1
                    stream.write(
                        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                    )
    summary = {
        "status": "INACTIVE_PROPOSED_STAGE2_PROTOCOL_NO_PHYSICS_AUTHORIZATION",
        "primary_task": "PushCube-v1",
        "secondary_task": "PickCube-v1_requires_separate_budget",
        "reserved_parents_per_task": 7044,
        "reserved_slots_by_phase": dict(counts),
        "source_check_outcomes_per_task": 16,
        "actual_outcomes_currently_collected": 0,
        "calibration_bank_selection": "L first1024; P first512; mixture first512 L plus next256 P; remaining slots unopened",
        "calibration_designs": [
            "L_only",
            "P_only",
            "ERR",
            "cost_greedy",
            "uniform_mixture",
            "cost_aware_uncertainty",
        ],
        "actual_max_macro_outcomes_per_family": 7312,
        "source_checks_and_repeats_are_not_additional_independent_parents": True,
        "historical_seed_collision_check": "REQUIRED_AGAINST_ALL_HISTORY_BEFORE_ANY_NEW_OUTCOMES; stop on collision, no outcome-dependent replacement",
        "condition_rule": "Original five-offset condition hash for Pick; original balanced nominal/misaligned Push condition definition",
        "generator_scope": "Declared future reservations only; no new qualified cohort or terminal outcome is claimed",
        "reserved_manifest_sha256": hashlib.sha256(
            (output / "reserved_parents.jsonl").read_bytes()
        ).hexdigest(),
    }
    (output / "protocol_reservation.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(
        json.dumps(
            {"reserved_parents": len(seen_ids), "new_physics": 0, "new_outcomes": 0}
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/err_method_challenge/stage2_reservation"),
    )
    write(parser.parse_args().output)
