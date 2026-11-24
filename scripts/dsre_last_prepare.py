"""Preservation, seed collision verification and pre-outcome registration."""

import gzip
import importlib.metadata
import json
import os
import re
import subprocess
import time
from pathlib import Path

from dsre_last_common import ROOT, arm, save, sha

from dual_rec.evidence_aware.views import condition


def main():
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        == "e8efd0fddf70a5405b5e9bda07e206655aa05d8b"
    )
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    save(
        ROOT / "preservation_start.json",
        {
            "epoch": time.time(),
            "git_status": subprocess.check_output(
                ["git", "status", "--porcelain"], text=True
            ),
            "tracked_sha256": {
                p: sha(p) if Path(p).is_file() else None for p in tracked if p
            },
            "historical_seals": {
                str(p): sha(p)
                for p in Path("results").rglob("*seal*.json")
                if not p.is_relative_to(ROOT)
            },
        },
    )
    push = []
    for phase, start, count in [
        ("native_pilot", 910010000, 4),
        ("discovery", 910000000, 128),
        ("calibration", 910001000, 1024),
        ("test", 910003000, 256),
    ]:
        push.extend(
            {
                "task": "PushCube-v1",
                "phase": phase,
                "index": i,
                "seed": start + i,
                "condition": ("nominal", "misaligned")[i % 2],
                "assigned": arm(start + i)
                if phase in ("discovery", "calibration")
                else None,
            }
            for i in range(count)
        )
    peg = []
    offsets = [0.0, 0.003, -0.003, 0.006, -0.006]
    for phase, start, count in [
        ("insertion_pilot", 920000000, 48),
        ("insertion_confirmation", 920001000, 96),
    ]:
        for i in range(count):
            seed = start + i
            ci = condition("PegInsertionSide-v1", str(seed))
            peg.append(
                {
                    "task": "PegInsertionSide-v1",
                    "phase": phase,
                    "index": i,
                    "seed": seed,
                    "offset": offsets[ci],
                    "condition_index": ci,
                    "observation_protocol": "Peg-observation-v2",
                }
            )
    seeds = {r["seed"] for r in push + peg}
    collisions = []
    files = paths = 0
    regex = re.compile(
        rb"(?<![0-9])(?:91000[0-9]{4}|91001000[0-3]|9200000[0-4][0-9]|9200010[0-9]{2})(?![0-9])"
    )
    # Native trace files are linked by their immutable specs/catalogues. Search all
    # historical paths, readable registration/metadata and compressed row tables.
    for base, directories, names in os.walk("results"):
        directories[:] = [
            d
            for d in directories
            if d not in ("__pycache__", ".pytest_cache", "review-copy", "review_copy")
            and not (Path(base) / d).is_relative_to(ROOT)
        ]
        for name in names:
            p = Path(base) / name
            paths += 1
            candidates = regex.findall(str(p).encode())
            if (
                p.suffix in (".json", ".jsonl", ".csv", ".md", ".txt")
                and p.stat().st_size < 200_000_000
            ):
                candidates += regex.findall(p.read_bytes())
                files += 1
            elif p.suffix == ".gz" and any(
                s in name
                for s in (
                    "rows",
                    "table",
                    "manifest",
                    "catalog",
                    "qualified",
                    "samples",
                )
            ):
                with gzip.open(p, "rb") as handle:
                    candidates += regex.findall(handle.read())
                files += 1
            for token in candidates:
                if int(token) in seeds:
                    collisions.append({"seed": int(token), "source": str(p)})
    save(
        ROOT / "seed_collision_check.json",
        {
            "passed": not collisions,
            "collisions": collisions,
            "paths_checked": paths,
            "metadata_files_checked": files,
            "coverage": "All historical result paths, plain manifests/specs/catalogues/reports and compressed row tables; full native traces linked by immutable specs and seed-indexed catalogues. RNG state integers are not treated as new parents.",
        },
    )
    assert not collisions, "REGISTERED_SEED_COLLISION_STOP_NO_REPLACEMENT"
    source = list(Path("src/dual_rec").rglob("*.py")) + list(
        Path("scripts").glob("*.py")
    )
    source += [
        Path("research/dsre_final_science/supervisor_oracle.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    package = Path(".venv/lib/python3.12/site-packages")
    for folder in (
        "mani_skill/envs/tasks/tabletop",
        "mani_skill/examples/motionplanning",
        "mani_skill/agents/controllers",
    ):
        source += list((package / folder).rglob("*.py"))
    save(
        ROOT / "registration.json",
        {
            "epoch": time.time(),
            "design_commit": "eea75861cbf57013e3983dfbcf08e2a4252c2a54",
            "supervisor_sha256": sha(
                "docs/DSRE_RSS2027_FINAL_SUPERVISOR_DECISION_20261118.md"
            ),
            "base_commit": "e8efd0fddf70a5405b5e9bda07e206655aa05d8b",
            "push": push,
            "peg": peg,
            "alpha": 0.1,
            "eta": 0.05,
            "delta_L": 0.025,
            "delta_P": 0.025,
            "per_tail": ".025/(4K)",
            "phase_order": [
                "existing_checks",
                "native_pilot",
                "discovery",
                "freeze_all_structures",
                "calibration",
                "freeze_bounds",
                "test_selected_then_isolated_evaluator",
                "insertion_pilot",
                "conditional_insertion_confirmation",
                "independent_audits",
            ],
            "pilot": "4 disjoint Push native-start parents, both unchanged macros twice in isolated processes. All 4 must pass full source/parity audits; no outcome-performance gate.",
            "source_eligibility": "Push fixed 53-control transport boundary, future70; prefix success does not exclude. Peg ANY native upstream screw planner abort before checkpoint -> NO_DECISION_CHECKPOINT with raw denominator. Model/controller/physics mismatch stops task. Eligible failure actual endpoint or MISSING; no imputation.",
            "insertion_condition": "Reuse five previously registered offsets and the existing condition hash, frozen uniformly before outcomes; aperture UNKNOWN excluded from five-predicate grammar.",
            "insertion_extension": "Only >=32 qualified checkpoints AND >=2 distinct10 AND >=2 distinct01 parents; then separate exploratory96 with all raw denominators; no formal calibration claim.",
            "partition": "Unchanged exact Boolean CART2 observed-arm SSE, K<=4, min8 per arm per split leaf; discovery only, PRIMARY6; canonical ties.",
            "baseline": "Exact B7 and direct partial ID same whole-leaf gate; CART discovery utility plus same gate; per-arm ridge regression lambda1/intercept unpenalized, clipped predictions, two frozen gain>=.05 regions with min8 per-arm support or collapsed common region; independently calibrate those whole regions at identical alpha eta and tail rule. Fixed C/R. No cross-method joint95 claim.",
            "access": "D/C physically one assigned macro only. Learner whitelisted opaque-ID OneAction records without seed/condition. Selected test macro executed before fresh isolated counterpart; no test fitting. Python audit hook audits trusted code, not an adversarial security sandbox.",
            "resources": {
                "cumulative_physics_worker_seconds": 12 * 3600,
                "collection_worker_seconds": 10 * 3600,
                "reserve_audit_seconds": 2 * 3600,
                "compressed_bytes": 4 * 1024**3,
                "concurrency": 4,
                "batch_parents": 4,
                "worker_timeout_seconds": 180,
                "conservative_parent_bound_seconds": 4 * 180,
                "hard_stop_utc": "2026-11-21T23:00:00+00:00",
            },
            "versions": {
                p: importlib.metadata.version(p)
                for p in (
                    "numpy",
                    "scipy",
                    "pydantic",
                    "torch",
                    "mani-skill",
                    "sapien",
                    "mplib",
                    "mujoco",
                    "gymnasium",
                )
            },
            "renderer": "/usr/share/vulkan/icd.d/lvp_icd.x86_64.json",
            "renderer_sha256": sha("/usr/share/vulkan/icd.d/lvp_icd.x86_64.json"),
            "source_sha256": {str(p): sha(p) for p in sorted(set(source))},
            "existing_checks_sha256": sha(ROOT / "existing_checks.json"),
            "seed_collision_sha256": sha(ROOT / "seed_collision_check.json"),
        },
    )
    print(
        json.dumps(
            {
                "registered": True,
                "parents": len(push) + len(peg),
                "historical_paths": paths,
                "metadata_files": files,
            }
        )
    )


if __name__ == "__main__":
    main()
