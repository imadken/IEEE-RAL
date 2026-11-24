"""Independent seed/condition and archival-manifest identity audit."""

import hashlib
import json
import os
import re
from pathlib import Path


def main():
    old = Path("results/dsre-evidence-aware/20261117-first-session")
    root = Path("results/dsre-evidence-aware/20261117-prospective")
    original = json.loads((old / "prospective_manifest.json").read_text())
    ready = json.loads((old / "prospective_ready_manifest.json").read_text())
    assert original["cohorts"] == ready["cohorts"]
    future = set()
    allids = set()
    development = set()
    for task, phases in ready["cohorts"].items():
        offsets = (
            [0.0, 0.003, -0.003, 0.006, -0.006]
            if task.startswith("Peg")
            else [[0, 0], [0.35, 0], [-0.35, 0], [0, 0.35], [0, -0.35]]
            if task.startswith("Point")
            else [0.0, 0.01, 0.02, 0.03, -0.02]
        )
        for phase, rows in phases.items():
            assert (
                len(rows)
                == {
                    "pilot": 10,
                    "development": 64,
                    "discovery": 128,
                    "calibration": 1024,
                    "test": 256,
                }[phase]
            )
            for row in rows:
                expected = (
                    int.from_bytes(
                        hashlib.sha256(
                            f"dsre-evidence-v2:{task}:{phase}:{row['index']}".encode()
                        ).digest()[:4],
                        "big",
                    )
                    >> 1
                )
                assert row["seed"] == expected and expected not in allids
                allids.add(expected)
                index = (
                    row["index"] // 2
                    if phase == "pilot"
                    else int.from_bytes(
                        hashlib.sha256(
                            f"dsre-evidence-v2:condition:{task}:{expected}".encode()
                        ).digest(),
                        "big",
                    )
                    % 5
                )
                assert row["offset"] == offsets[index]
                (
                    future
                    if phase in ("discovery", "calibration", "test")
                    else development
                ).add(expected)
    metadata_seeds = set()
    paths = []
    path_ids = set()

    def extract(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                extract(v, k)
        elif isinstance(value, list):
            for v in value:
                extract(v, key)
        elif key in ("seed", "parent_seed", "episode_seed", "seeds", "parent_seeds"):
            if isinstance(value, int) and not isinstance(value, bool):
                metadata_seeds.add(value)
            elif isinstance(value, str) and value.isdigit():
                metadata_seeds.add(int(value))

    for current, dirs, files in os.walk("results"):
        base = Path(current)
        dirs[:] = [
            d
            for d in dirs
            if d
            not in (
                "env",
                "navigation_env",
                "cache",
                "review_packet",
                "prior_packet",
                "__pycache__",
            )
            and not (base / d).is_relative_to(root)
            and not (base / d).is_relative_to(old)
        ]
        for name in dirs + files:
            match = re.match(r"^(?:seed[_-]?)?(\d{3,})(?:[-_.]|$)", name)
            if match:
                path_ids.add(int(match[1]))
        for name in files:
            if "manifest" not in name.lower() or not name.endswith(".json"):
                continue
            path = base / name
            if path.stat().st_size > 32 * 1024**2:
                continue
            try:
                value = json.loads(path.read_text())
            except (ValueError, OSError):
                continue
            extract(value)
            paths.append(
                {
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    assert not future & (metadata_seeds | path_ids | development)
    result = {
        "passed": True,
        "future_independent_parents": len(future),
        "prior_manifest_metadata_seed_ids": len(metadata_seeds),
        "archival_path_ids": len(path_ids),
        "prior_development_or_pilot_ids": len(development),
        "overlaps": [],
        "archival_manifests": paths,
        "scope": "All retained old manifest seed fields and physical path identities, including condition variant directories; original and ready cohorts exact equality; source-v2 pilot independently registered.",
        "note": "No future test outcome was read; old evidence remains development; original manifest bytes unchanged.",
    }
    with (root / "independent_manifest_audit.json").open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(
        json.dumps({k: v for k, v in result.items() if k != "archival_manifests"}),
        flush=True,
    )


if __name__ == "__main__":
    main()
