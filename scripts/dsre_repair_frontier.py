"""Separate finite ceilings, parent-supported coverage and actual physical collisions."""

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from dsre_repair_experiment import load, save, table_for

from dual_rec.dsre.repair import ParentIndex, RepairQuery, RepairTable
from dual_rec.dsre.repair_interface import attach_plan, restore_output
from dual_rec.dsre.repair_selection import (
    OPTIONAL,
    good,
    profile,
    select_channels,
    values,
)


def supported_profile(table, groups):
    index = ParentIndex(table, groups)
    outputs = []
    masses = defaultdict(int)
    for r in table.rows:
        masses[r.features] += 1
    for signature, mass in sorted(masses.items(), key=lambda p: str(p[0])):
        output = index.diagnose(RepairQuery(scope=table.scope, features=signature))
        outputs.append(
            {
                "signature": signature,
                "mass": mass,
                "output": output.model_dump(mode="json"),
            }
        )
    return {
        "rows": len(table.rows),
        "exact_signatures": len(masses),
        "supported_grammar_mass": sum(
            p["mass"] for p in outputs if p["output"]["action"]
        ),
        "signature_outputs": outputs,
    }


def frontier(root):
    config = load(Path("config/dsre_evidence_repair.json"))
    data = [
        json.loads(s) for s in (root / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    by_id = {r["id"]: r for r in data}
    (root / "supported_profiles").mkdir(exist_ok=True)
    for path in sorted((root / "models").glob("*.json")):
        target = root / "supported_profiles" / path.name
        if target.exists():
            continue
        m = load(path)
        table = RepairTable.model_validate(m["table"])
        save(target, supported_profile(table, m["parent_groups"]))
    full = {}
    graphs = {}
    worked = []
    for task in ("PickCube-v1", "PushCube-v1"):
        population = [r for r in data if r["task"] == task]
        template = load(
            Path(config["input_root"])
            / "crossfit"
            / f"pose_proprioception__{task}__fold0.model.json"
        )["scope"]
        full[task] = {}
        distinct = {}
        for selector in config["selectors"]:
            for budget in config["budgets"]:
                selected = select_channels(
                    population, budget, selector, seed=config["random_order_seed"]
                )
                if selected not in distinct:
                    table, groups = table_for(population, selected, template)
                    distinct[selected] = {
                        "finite_profile": profile(population, selected),
                        **supported_profile(table, groups),
                    }
                full[task][f"{selector}|{budget}"] = {
                    "channels": selected,
                    "profile": distinct[selected],
                }
        edges = []
        blocked = []
        for a, b in combinations(population, 2):
            if a["features"] != b["features"]:
                continue
            ga, gb = good(a), good(b)
            if not ga or not gb:
                continue
            if ga & gb:
                continue
            separating = [
                OPTIONAL[i]
                for i, (x, y) in enumerate(
                    zip(a["optional_features"], b["optional_features"], strict=True)
                )
                if x is not None and y is not None and x != y
            ]
            edges.append(
                {
                    "ids": [a["id"], b["id"]],
                    "shared_primary_signature": a["features"],
                    "outcomes": [a["outcomes"], b["outcomes"]],
                    "optional_values": [a["optional_features"], b["optional_features"]],
                    "separating_channels": separating,
                    "unresolved_on_full_menu": not separating,
                }
            )
        primary = profile(population, ())
        for group in primary["signatures"]:
            if group["inadequate"]:
                row = by_id[group["inadequate_witness"][0]]
                blocked.append(
                    {
                        "id": row["id"],
                        "outcomes": row["outcomes"],
                        "primary": row["features"],
                        "optional": row["optional_features"],
                        "kind": "REPERTOIRE_INADEQUATE",
                        "no_sensor_can_fix_actual_neither": True,
                    }
                )
        graphs[task] = {
            "vertices": [
                {
                    "id": r["id"],
                    "good": sorted(good(r)),
                    "primary": r["features"],
                    "optional": r["optional_features"],
                }
                for r in population
            ],
            "ambiguity_edges": edges,
            "inadequacy_witnesses": blocked,
            "edges": len(edges),
            "separable_edges": sum(bool(e["separating_channels"]) for e in edges),
        }
        if edges:
            # Predefined informative ranking: real opposing outcomes, one-channel separation, most separators, IDs.
            best = min(
                edges,
                key=lambda e: (
                    not bool(e["separating_channels"]),
                    -len(e["separating_channels"]),
                    e["ids"],
                ),
            )
            worked.append(
                {
                    "task": task,
                    "example": "opposing_good_sets",
                    "edge": best,
                    "records": [by_id[id] for id in best["ids"]],
                }
            )
    save(root / "full_reference_frontiers.json", full)
    save(root / "ambiguity_graph.json", graphs)
    # Prefer a newly pure failed-start child for the second explanatory example.
    # This selects an illustration after evaluation, never a feature map or threshold.
    if len(worked) < 2:
        entry = full["PickCube-v1"]["exact_coverage|1"]
        selected = entry["channels"]
        children = entry["profile"]["signature_outputs"]
        parents = full["PickCube-v1"]["exact_coverage|0"]["profile"]["finite_profile"][
            "signatures"
        ]
        candidates = []
        for child in children:
            parent = next(
                g for g in parents if g["signature"] == child["signature"][:6]
            )
            members = [
                r
                for r in data
                if r["task"] == "PickCube-v1"
                and values(r, selected) == tuple(child["signature"])
            ]
            if (
                child["output"]["action"]
                and not parent["good"]
                and any(not r["initial_success"] for r in members)
            ):
                candidates.append((child, parent, members))
        if candidates:
            child, parent, members = min(
                candidates, key=lambda p: (-p[0]["mass"], p[1]["signature"])
            )
            row = min(
                (r for r in members if not r["initial_success"]), key=lambda r: r["id"]
            )
            bad = by_id[parent["inadequate_witness"][0]]
            worked.append(
                {
                    "task": "PickCube-v1",
                    "example": "one_channel_separates_new_pure_failed_start_child",
                    "records": [row, bad],
                    "added_channels": selected,
                    "child_mass": child["mass"],
                    "refinement_certificate": child["output"],
                    "interpretation": "Full-table child is adequate with parent support; the actual neither row remains inadequate. This is an illustrative development witness, not held-out recovery improvement.",
                }
            )
    # If no such child exists, retain an actual inadequacy contrast instead.
    if len(worked) < 2:
        for task in ("PickCube-v1", "PushCube-v1"):
            candidates = [r for r in data if r["task"] == task and not good(r)]
            if candidates:
                row = min(candidates, key=lambda r: r["id"])
                partner = next(
                    (
                        r
                        for r in sorted(data, key=lambda r: r["id"])
                        if r["task"] == task
                        and r["features"] == row["features"]
                        and good(r)
                    ),
                    None,
                )
                worked.append(
                    {
                        "task": task,
                        "example": "neither_in_observation_class",
                        "records": [row] + ([partner] if partner else []),
                    }
                )
                break
    if (root / "worked_examples.json").exists() and not (
        root / "initial_worked_examples.json"
    ).exists():
        (root / "initial_worked_examples.json").write_bytes(
            (root / "worked_examples.json").read_bytes()
        )
    save(root / "worked_examples.json", worked[:2])
    interface_examples = []
    for designpath in sorted((root / "designs").glob("*.json")):
        design = load(designpath)
        d = next(
            x
            for x in design["selected_designs"]
            if x["selector"] == "exact_coverage" and x["budget"] == 1
        )
        model = load(root / "models" / (d["model"] + ".json"))
        base = next(
            s["ceiling_mass"] for s in design["subset_scores"] if not s["channels"]
        )
        for p in model["decisions"].values():
            if p["method"] == "DSRE" and p["result"]["action"] is None:
                output = restore_output(p["result"]["diagnosis"])
                interface_examples.append(
                    attach_plan(output, d, base).model_dump(mode="json")
                )
                break
    save(root / "interface_examples.json", interface_examples)
    save(
        root / "frontier_completed.json",
        {
            "status": "COMPLETE",
            "training_supported_models": len(
                list((root / "supported_profiles").glob("*.json"))
            ),
            "graph_edges": sum(g["edges"] for g in graphs.values()),
            "worked_examples": len(worked[:2]),
        },
    )
    print(json.dumps(load(root / "frontier_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    frontier(args.root)
