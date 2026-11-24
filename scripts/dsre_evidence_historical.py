"""Prepare masked DEVELOPMENT archives using outcome-blind parent selection."""

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from dsre_source_risk_audit import audit_cell

from dual_rec.dsre.features import PRIMARY
from dual_rec.evidence_aware.schema import OneAction, Pair, Scope
from dual_rec.evidence_aware.views import arm, condition, hashed, save, sha, split

CATALOGS = (
    ("20261115T195007Z-science-v12", ("prospective",)),
    ("20261116T130334Z-runtime-recovery", ("calibration", "test")),
    ("20261116T193049Z-dual-obligation", ("calibration", "test")),
)
PROFILES = ("nominal", "offset001", "offset002", "offset003", "offset_minus002")


def gz(p):
    with gzip.open(p, "rt") as f:
        return json.load(f)


def prepare(out):
    candidates = {}
    seals = {}
    duplicates = []
    for catalog, stages in CATALOGS:
        root = Path("results/dsre-operational") / catalog
        sealpath = root / "completion_manifest.json"
        seals[str(sealpath)] = sha(sealpath)
        members = {
            k: v["sha256"] for k, v in json.loads(sealpath.read_text())["files"].items()
        }
        for stage in stages:
            for directory in sorted((root / stage).iterdir()):
                if not directory.is_dir() or not directory.name.isdigit():
                    continue
                parent = directory.name
                selected = PROFILES[condition("PickCube-v1", parent)]
                folder = directory / selected
                if parent in candidates:
                    duplicates.append(str(folder))
                    continue
                candidates[parent] = (root, folder, members)
    # Freeze every parent/condition choice before reading any continuation file.
    schedule = [
        {
            "parent": parent,
            "directory": str(v[1]),
            "split": split("PickCube-v1", parent),
            "arm": arm("PickCube-v1", parent),
        }
        for parent, v in sorted(candidates.items())
    ]
    schedule_path = out / "historical_schedule.json"
    schedule_value = {
        "schedule": schedule,
        "seals": seals,
        "duplicate_seed_paths": duplicates,
        "population": "All available five-offset PickCube parents in three sealed catalogs; every row DEVELOPMENT",
        "condition_namespace": "dsre-evidence-v2:condition:<task>:<parent>",
        "split_rule": "parent SHA modulo10: 0..3 discovery,4..6 calibration,7..9 evaluation",
    }
    if schedule_path.exists():
        assert json.loads(schedule_path.read_text()) == schedule_value
    else:
        save(schedule_path, schedule_value)
    logs = {s: [] for s in ("discovery", "calibration", "evaluation")}
    pairs = {s: [] for s in logs}
    queries = []
    identities = set()
    provenance = []
    counts = Counter()
    versions = Counter()
    scope = Scope(
        task="PickCube-v1",
        controller_sha256=sha(Path("scripts/dsre_paper_physics.py")),
        horizon=70,
        outcome="terminal task evaluate.success after70 controls",
        population="independent parent; one hash-selected condition from five-offset mixture; DEVELOPMENT",
        observation_protocol="six existing PRIMARY semantic predicates from first/current state_dict",
    )
    for item in schedule:
        parent = item["parent"]
        root, folder, members = candidates[parent]
        # Check raw files against original unchanged seal before parsing.
        for name in ("screen.json.gz", "continue.json.gz", "recover.json.gz"):
            p = folder / name
            assert sha(p) == members[str(p.relative_to(root))], str(p)
        screen = gz(folder / "screen.json.gz")
        identity = hashlib.sha256(
            json.dumps(
                [
                    screen["model"],
                    screen["prefix_actions"],
                    screen["canonical_start"],
                    screen["canonical_controller_memory"],
                ],
                sort_keys=True,
            ).encode()
        ).hexdigest()
        if identity in identities:
            raise RuntimeError(
                "Duplicate full physical identity not caught by parent catalog"
            )
        identities.add(identity)
        # Pure independently transcribed physics auditor, no production estimator.
        audit, labels = audit_cell(screen, folder)
        counts.update(audit)
        x = screen["summary"]["features"]
        assigned = item["arm"]
        phase = item["split"]
        pid = hashlib.sha256(
            ("dsre-evidence-v2:parent:PickCube-v1:" + parent).encode()
        ).hexdigest()
        log = OneAction(
            parent_id=pid,
            x=x,
            action=assigned,
            propensity=0.5,
            y=labels["continue_value" if assigned == "c" else "recover_value"],
            controls=70,
            wall_seconds=0,
            source_scope=scope,
        )
        pair = Pair(
            parent_id=pid,
            x=x,
            yc=labels["continue_value"],
            yr=labels["recover_value"],
            source_scope=scope,
        )
        logs[phase].append(log.model_dump(mode="json"))
        pairs[phase].append(pair.model_dump(mode="json"))
        if phase == "evaluation":
            queries.append(
                {
                    "parent_id": pid,
                    "x": x,
                    "source_scope": scope.model_dump(mode="json"),
                }
            )
        provenance.append(
            {
                "parent_id": pid,
                "physical_identity": identity,
                "source": str(folder),
                "files": {
                    str(folder / n): sha(folder / n)
                    for n in ("screen.json.gz", "continue.json.gz", "recover.json.gz")
                },
                "initial_success": screen["summary"]["initial_success"],
            }
        )
        versions[json.dumps(screen["model"]["versions"], sort_keys=True)] += 1
    assert len(versions) == 1, versions
    for phase, records in logs.items():
        save(out / "learner" / (phase + ".json"), records)
        save(out / "evaluator" / (phase + "_pairs.json"), pairs[phase])
    save(out / "learner/queries.json", queries)
    save(out / "learner/vocabulary.json", list(PRIMARY))
    save(out / "evaluator/provenance.json", provenance)
    save(
        out / "historical_physical_audit.json",
        {
            "passed": True,
            "counts": dict(counts),
            "parents": len(identities),
            "versions": dict(versions),
            "split_counts": {s: len(logs[s]) for s in logs},
            "scope": scope.model_dump(mode="json"),
            "wall_cost_note": "Historical per-action wall not available in consistent units; zero in masked records is missing, not instantaneous execution.",
        },
    )
    # P learners receive only calibration pairs, explicitly charged at two outcomes.
    # No P discovery or evaluation pairs are exposed to the learner process.
    save(out / "paired_refinement/calibration.json", pairs["calibration"])
    chosen = sorted(
        logs["calibration"], key=lambda r: hashed("equal-execution:" + r["parent_id"])
    )[: len(logs["calibration"]) // 2]
    chosen_ids = {r["parent_id"] for r in chosen}
    save(out / "learner/calibration_equal_execution.json", chosen)
    save(
        out / "paired_refinement/calibration_equal_execution.json",
        [r for r in pairs["calibration"] if r["parent_id"] in chosen_ids],
    )
    print(
        json.dumps(
            {"parents": len(identities), "counts": {s: len(logs[s]) for s in logs}}
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    args = p.parse_args()
    prepare(args.root)
