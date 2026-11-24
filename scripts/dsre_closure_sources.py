"""E2 masked source views, followed by a strictly whitelisted learner process."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from dsre_closure_common import (
    INPUTS,
    OBLIGATIONS,
    ROOT,
    TASKS,
    calibrated,
    hashed,
    passed,
    read,
    route,
    save,
)


def materialize():
    registration = read(ROOT / "registration.json")
    evidence = read(ROOT / "E0/recount/independent_numbers.json")["results"]
    frozen = read(ROOT / "E1/calibration_freeze.json")["tasks"]
    inventory = []
    for task in TASKS:
        model = frozen[task]["model"]
        partition = {
            "partition": model["partition"],
            "source_scope": model["source_scope"],
        }
        save(ROOT / "E2/views" / task / "partition.json", partition)
        rows = sorted(
            evidence[task]["paired_test"],
            key=lambda r: hashed(
                registration["source_order_namespace"], task, r["parent_id"]
            ),
        )
        assert len(rows) == len({r["parent_id"] for r in rows}) == 256
        assert not {r["parent_id"] for r in rows} & set(
            model["partition"]["discovery_parents"]
        )
        for panel in ("shared_parents", "disjoint_parents"):
            for source in ("L", "P"):
                available = (
                    rows
                    if panel == "shared_parents"
                    else rows[:128]
                    if source == "L"
                    else rows[128:]
                )
                for budget in registration["source_budgets"]:
                    n = budget if source == "L" else budget // 2
                    entry = {
                        "task": task,
                        "panel": panel,
                        "source": source,
                        "budget": budget,
                        "available_parents": len(available),
                        "parents_required": n,
                        "supported": n <= len(available),
                        "role": "RETROSPECTIVE_MASKED_DEVELOPMENT; no untouched confirmation",
                        "original_source_pool_cost": 512,
                        "new_physics": 0,
                    }
                    if not entry["supported"]:
                        entry["reason"] = (
                            "INSUFFICIENT_DISTINCT_QUALIFIED_PARENTS_AT_THIS_LOGICAL_BUDGET"
                        )
                        inventory.append(entry)
                        continue
                    chosen = available[:n]
                    logs, pairs = [], []
                    for r in chosen:
                        arm = ("c", "r")[
                            int(
                                hashed(
                                    registration["source_arm_namespace"],
                                    task,
                                    r["parent_id"],
                                ),
                                16,
                            )
                            % 2
                        ]
                        logs.append(
                            {
                                "parent_id": r["parent_id"],
                                "x": r["x"],
                                "action": arm,
                                "propensity": 0.5,
                                "y": r["yc"] if arm == "c" else r["yr"],
                                "counterpart_exposed": False,
                                "provenance": "Hash-masked from qualified paired simulator outcomes; not a new genuinely randomized execution log",
                            }
                        )
                        if source == "P":
                            pairs.append(
                                {
                                    "parent_id": r["parent_id"],
                                    "x": r["x"],
                                    "yc": r["yc"],
                                    "yr": r["yr"],
                                }
                            )
                    view = ROOT / "E2/views" / task / f"{panel}_{source}_{budget}.json"
                    save(
                        view,
                        {
                            "logs": logs,
                            "pairs": pairs,
                            "visible_action_outcomes": len(logs) + len(pairs),
                            "counterpart_exposure_authorized": source == "P",
                            "budget": budget,
                            "qualification_only": True,
                            "no_independent_test_scoring": True,
                        },
                    )
                    entry["view"] = str(view)
                    entry["parent_ids"] = [r["parent_id"] for r in chosen]
                    inventory.append(entry)
    save(
        ROOT / "E2/view_inventory.json",
        {
            "created_epoch": time.time(),
            "views": inventory,
            "input_sha256": INPUTS,
            "source_boundary": "L learner receives only the masked assigned label; P is explicitly budgeted two-outcome evidence.",
            "inference_scope": "Original test roles are retired ONLY for this retrospective source-view analysis; they remain original-test outcomes for E1. No source-curve result is a new prospective confirmation or a test-policy evaluation.",
            "disjointness": "Shared panel reuses parents across source views and is a dependent paired comparison. Disjoint panel has distinct L/P parents; both exclude discovery. Neither pools incompatible sources.",
        },
    )


def fit_view(index):
    from pathlib import Path

    from dual_rec.evidence_aware.views import guard_data_access

    inventory_path = ROOT / "E2/view_inventory.json"
    inventory = read(inventory_path)
    entry = dict(inventory["views"][index])
    assert entry["supported"]
    partition_path = ROOT / "E2/views" / entry["task"] / "partition.json"
    allowed = [inventory_path, partition_path, Path(entry["view"])]
    accesses = guard_data_access(Path("results"), allowed, additional_roots=(ROOT,))
    model = read(partition_path)
    view = read(entry["view"])
    logs, pairs = view["logs"], view["pairs"]
    assert len(logs) + len(pairs) == entry["budget"]
    assert len({r["parent_id"] for r in logs}) == len(logs)
    assert len({r["parent_id"] for r in pairs}) == len(pairs)
    if entry["source"] == "L":
        assert pairs == [] and not view["counterpart_exposure_authorized"]
        assert all(not ({"yc", "yr"} & set(r)) for r in logs)
    partition = model["partition"]
    k = len(set(partition["cells"]))
    leaves = {
        str(cell): calibrated(
            [r for r in logs if route(partition, r["x"]) == cell],
            [r for r in pairs if route(partition, r["x"]) == cell],
            k,
            cell,
        )
        for cell in sorted(set(partition["cells"]))
    }
    entry["leaves"] = leaves
    entry["qualified_leaves"] = {
        o: [int(c) for c, v in leaves.items() if passed(v["bounds"], o)]
        for o in OBLIGATIONS
    }
    entry["confidence"] = {
        "delta_L": 0.025,
        "delta_P": 0.025,
        "tail": 0.025 / (4 * k),
        "scope": "One fixed source view only; curves/descriptive comparisons have no simultaneous family claim",
    }
    entry["visible_outcomes"] = len(logs) + len(pairs)
    entry["paired_blocks_are_independent"] = False if pairs else None
    entry["paired_dependence_note"] = (
        "First-label and paired constraints may share parents; Bonferroni does not require independent constraint events. Parents within each block are distinct."
    )
    entry["successful_reads"] = list(accesses)
    entry["input_sha256"] = dict(INPUTS)
    entry["isolated_process"] = True
    save(ROOT / "E2/fits" / f"{index}.json", entry)


def learn():
    inventory = read(ROOT / "E2/view_inventory.json")
    results = []
    for index, entry in enumerate(inventory["views"]):
        if entry["supported"]:
            subprocess.run(
                [sys.executable, __file__, "fit_view", "--index", str(index)],
                check=True,
            )
            entry = read(ROOT / "E2/fits" / f"{index}.json")
            assert set(entry["successful_reads"]) <= {
                str(Path(p).resolve()) for p in entry["input_sha256"]
            }
        results.append(entry)
    save(
        ROOT / "E2/source_curves.json",
        {
            "results": results,
            "input_sha256": INPUTS,
            "separation": "Every source/budget is fitted in its own process with exactly its partition and its masked/budgeted view whitelisted. L processes cannot read P files or original evaluator branches.",
            "timing_note": "No online robot or new simulation executions; visible-outcome budgets are not historical sunk collection costs",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("materialize", "learn", "fit_view"))
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.stage == "fit_view":
        fit_view(args.index)
    else:
        (materialize if args.stage == "materialize" else learn)()
