"""Bounded E0 oracle study and qualification of existing DSRE development pairs."""

import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from dual_rec.dsre.data import construct, digest
from dual_rec.dsre.oracle import verify_certificate
from dual_rec.dsre.schemas import Outcomes, Query, ReferenceRow, ReferenceTable, Scope
from dual_rec.dsre.solver import FiniteIndex


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def e0(root):
    rng = random.Random(20261113)
    comparisons, maximum_d, witnesses, insufficiencies = 0, 0, 0, Counter()
    examples = []
    started = time.perf_counter()
    for case in range(1200):
        d = case % 9
        scope = Scope(
            task="E0-logical-only",
            controller_sha256="0" * 64,
            features=tuple("abcdefgh"[:d]),
            channels="authored-not-physics",
        )
        table = ReferenceTable(
            scope=scope,
            rows=tuple(
                ReferenceRow(
                    id=f"{case}/{i}",
                    features=tuple(
                        rng.choice([False, False, True, True, None]) for _ in range(d)
                    ),
                    outcomes=Outcomes(
                        continue_value=rng.choice([False, True, None]),
                        recover_value=rng.choice([False, True, None]),
                    ),
                )
                for i in range(rng.randrange(1, 16))
            ),
        )
        query = Query(
            scope=scope,
            features=tuple(rng.choice([False, True, None]) for _ in range(d)),
        )
        minimum = 1 + case % 3
        result = FiniteIndex(table, minimum).solve(query)
        verify_certificate(
            table.model_dump(mode="json"),
            query.model_dump(mode="json"),
            result.model_dump(mode="json"),
            minimum,
        )
        comparisons += 1
        maximum_d = max(maximum_d, d)
        witnesses += len(result.witnesses)
        insufficiencies.update(result.reasons)
        if len(examples) < 12:
            examples.append(
                {
                    "table": table.model_dump(mode="json"),
                    "query": query.model_dump(mode="json"),
                    "minimum_support": minimum,
                    "certificate": result.model_dump(mode="json"),
                }
            )
    save(
        root / "e0_independent_agreement.json",
        {
            "status": "PASS",
            "independent_exhaustive_and_hitting_set_cases": comparisons,
            "maximum_features": maximum_d,
            "witnesses_checked": witnesses,
            "insufficiency_reasons": dict(insufficiencies),
            "wall_seconds": time.perf_counter() - started,
            "scope": "Logical correctness only; no invented simulator outcomes",
            "examples": examples,
        },
    )
    print(
        {
            "E0": "PASS",
            "cases": comparisons,
            "maximum_d": maximum_d,
            "witnesses": witnesses,
        },
        flush=True,
    )


def qualify(root):
    config = json.loads(Path("config/dsre_stage1.json").read_text())
    controller_paths = [
        "scripts/recovery_claims_physics.py",
        "scripts/overnight_replay.py",
        "scripts/overnight_pick.py",
        "src/dual_rec/overnight_pick.py",
        "src/dual_rec/scenarios.py",
    ]
    source_seal = json.loads(
        (Path(config["source_root"]) / "completion_manifest.json").read_text()
    )
    confirmation_freeze_path = Path(config["source_root"]) / "confirmation_freeze.json"
    assert (
        digest(confirmation_freeze_path)
        == source_seal["sha256"]["confirmation_freeze.json"]
    )
    source_pins = (
        json.loads(confirmation_freeze_path.read_text())["source_sha256"]
        | source_seal["source_sha256"]
    )
    controllers = {p: digest(Path(p)) for p in controller_paths}
    for p, expected in controllers.items():
        assert source_pins[p] == expected, p
    table, exclusions = construct(config, root)
    totals = defaultdict(Counter)
    for row in table:
        a, b = row["outcomes"]["continue_value"], row["outcomes"]["recover_value"]
        category = (
            "both"
            if a and b
            else "continue_only"
            if a
            else "recover_only"
            if b
            else "neither"
        )
        total = totals[row["task"]]
        total.update(
            pairs=1,
            **{category: 1},
            already_successful_start=int(row["initial_success"]),
            failed_start=int(not row["initial_success"]),
            privileged_grasp_missing=int(row["privileged_features"][-2] is None),
            reference_memory_not_explicit=int(not row["reference_memory_recorded"]),
        )
    manifest = {
        "status": "PASS" if table else "NO_QUALIFIED_PAIRS",
        "pairs": len(table),
        "seed_groups": len({r["group"] for r in table}),
        "exclusions": len(exclusions),
        "per_task": {task: dict(v) for task, v in totals.items()},
        "controllers_sha256": controllers,
        "controller_identity": __import__("hashlib")
        .sha256(json.dumps(controllers, sort_keys=True).encode())
        .hexdigest(),
        "source_files": len(json.loads((root / "source_members.json").read_text())),
        "primary_utility": config["utility"],
        "development_only": True,
        "new_physics": 0,
        "feature_map": "predecision-observation-only primary six, separate privileged-eight",
        "table_sha256": digest(root / "qualified_pairs.jsonl"),
    }
    save(root / "data_qualification.json", manifest)
    print(json.dumps(manifest), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=["e0", "qualify"], required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"e0": e0, "qualify": qualify}[args.stage](args.root)
