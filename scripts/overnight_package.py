"""Retain complete compact recipes and predetermined examples of overnight data."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    output = root / "audit"
    output.mkdir(exist_ok=False)
    raw = {}
    with (
        (output / "scenario_registry.jsonl").open("x") as registry,
        (output / "recovery_actions.jsonl").open("x") as recoveries,
        gzip.open(output / "examples.jsonl.gz", "xt") as examples,
    ):
        for path in sorted((root / "d7b").glob("*/scenarios.jsonl.gz")):
            raw[str(path.relative_to(root))] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            with gzip.open(path, "rt") as stream:
                for line in stream:
                    case = json.loads(line)
                    recipe = {
                        k: v
                        for k, v in case.items()
                        if k not in ("history", "source_sha256")
                    }
                    recipe["split"] = path.parent.name
                    recipe["history_steps"] = [f["step"] for f in case["history"]]
                    recipe["history_sha256"] = hashlib.sha256(
                        json.dumps(case["history"], sort_keys=True).encode()
                    ).hexdigest()
                    recipe["source_sha256"] = hashlib.sha256(
                        json.dumps(case["source_sha256"], sort_keys=True).encode()
                    ).hexdigest()
                    registry.write(json.dumps(recipe, allow_nan=False) + "\n")
                    # Fixed first base seed of each split; never select by outcome.
                    if (
                        case["seed"] in (3100, 4100)
                        and path.parent.name != "calibration"
                    ):
                        examples.write(
                            json.dumps(
                                {
                                    "kind": "pick_history",
                                    "split": path.parent.name,
                                    "case": case,
                                }
                            )
                            + "\n"
                        )
        for path in sorted((root / "d7b").glob("*/traces.jsonl.gz")):
            raw[str(path.relative_to(root))] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            with gzip.open(path, "rt") as stream:
                for line in stream:
                    trial = json.loads(line)
                    compact = {k: v for k, v in trial.items() if k != "trace"}
                    compact["actions"] = [f["action"] for f in trial["trace"]]
                    compact["split"] = path.parent.name
                    recoveries.write(json.dumps(compact, allow_nan=False) + "\n")
        for path in sorted((root / "b").glob("*/raw.jsonl.gz")):
            raw[str(path.relative_to(root))] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            # Compact B rows already retain complete prefixes/action tapes and
            # all per-step errors. Raw trajectories stay local and hash-addressed.
        with gzip.open(root / "d7b/fitted/models.json.gz", "rt") as stream:
            fitted = json.load(stream)
        cv = {"training_seeds": fitted["training_seeds"], "models": {}}
        for regime, models in fitted["models"].items():
            cv["models"][regime] = {
                name: {k: v for k, v in info.items() if k != "model"}
                for name, info in models.items()
            }
        (output / "development_cv.json").open("x").write(json.dumps(cv, indent=2))
    model_path = root / "d7b/fitted/models.json.gz"
    raw[str(model_path.relative_to(root))] = {
        "sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "bytes": model_path.stat().st_size,
    }
    (output / "local_raw_sha256.json").open("x").write(json.dumps(raw, indent=2))
    vendor_root = Path(importlib.util.find_spec("mani_skill").origin).parent
    vendor_sources = {
        name: hashlib.sha256((vendor_root / name).read_bytes()).hexdigest()
        for name in [
            "envs/sapien_env.py",
            "envs/scene.py",
            "utils/structs/actor.py",
            "utils/structs/articulation.py",
        ]
    }
    api_scope = {
        "adapter_source": "src/dual_rec/replay.py",
        "adapter_sha256": hashlib.sha256(
            Path("src/dual_rec/replay.py").read_bytes()
        ).hexdigest(),
        "mani_skill_vendor_sources_sha256": vendor_sources,
        "ManiSkill": {
            "physics_api": "BaseEnv.get_state_dict/set_state_dict; ManiSkillScene.get_sim_state/set_sim_state",
            "included": [
                "registered dynamic actor poses and velocities",
                "articulation root pose/velocity and qpos/qvel",
                "public controller state",
                "explicit controller transients",
                "joint drive position/velocity targets",
                "environment and wrapper elapsed steps",
                "Python/NumPy/Torch and environment RNG states and aliases",
            ],
            "not_serialized": [
                "static actor/model/material configuration (kept fixed)",
                "applied joint forces (measured readback separately)",
                "opaque contact solver caches (not exposed or claimed inspected)",
                "arbitrary task/controller configurations outside the qualified tasks",
            ],
        },
        "MuJoCo": {
            "physics_api": "mj_getState/mj_setState with mjSTATE_INTEGRATION; mj_forward then integration-state reapplication",
            "included": [
                "integration fields including controls, applied forces and warmstart",
                "simple controller/composite/robot/gripper/observable/environment fields",
                "environment/Python/NumPy RNG",
            ],
            "scope": "Lift/Panda BASIC OSC_POSE without interpolation/cameras; same model within branch; derived kinematics/contact data recomputed, not arbitrary scene serialization",
        },
        "estimand": "Difference caused by this unchanged snapshot adapter after its native continuation, relative to fresh-prefix replay, using the identical native-generated action tape. Does not estimate two independently adapting closed-loop policies.",
        "attribution_limit": "Exposed-state readback errors are measured; no solver-cache causal ablation or universal engine claim is authorized.",
    }
    (output / "api_scope.json").open("x").write(json.dumps(api_scope, indent=2))
    print(
        json.dumps(
            {
                "compact_directory": str(output),
                "local_raw_files": len(raw),
                "local_raw_bytes": sum(v["bytes"] for v in raw.values()),
            }
        )
    )


if __name__ == "__main__":
    main()
