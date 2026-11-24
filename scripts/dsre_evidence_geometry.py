"""Recover immutable geometry by source reset only; never execute a future."""

import argparse
import gzip
import json
import random
from pathlib import Path

import gymnasium as gym
import mani_skill.envs  # noqa: F401
import numpy as np
import torch
from dsre_evidence_tasks import plain


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--phase", default="pilot")
    p.add_argument("--tag", default="-interface3")
    a = p.parse_args()
    manifest = json.loads((a.root / "prospective_manifest.json").read_text())
    rows = manifest["cohorts"]["PegInsertionSide-v1"][a.phase]
    for spec in rows:
        out = a.root / "geometry" / a.phase / (str(spec["seed"]) + ".json")
        if out.exists():
            continue
        random.seed(spec["seed"])
        np.random.seed(spec["seed"])
        torch.manual_seed(spec["seed"])
        env = gym.make(
            "PegInsertionSide-v1",
            num_envs=1,
            sim_backend="cpu",
            render_backend="none",
            obs_mode="state_dict",
            control_mode="pd_joint_pos",
            max_episode_steps=2400,
        )
        try:
            obs, _ = env.reset(seed=spec["seed"])
            e = env.unwrapped
            record = {
                "spec": spec,
                "initial_physical": plain(e.get_state_dict()),
                "peg_half_sizes": plain(e.peg_half_sizes),
                "hole_radii": plain(e.box_hole_radii),
                "initial_observation": plain(obs),
                "no_future_executed": True,
            }
            recorded = (
                a.root
                / "physics/PegInsertionSide-v1"
                / (a.phase + a.tag)
                / str(spec["index"])
                / ("c.json.gz" if a.phase == "pilot" else "assigned.json.gz")
            )
            receipt = recorded.with_name(
                recorded.name.removesuffix(".json.gz") + ".execution.json"
            )
            if recorded.exists() and receipt.exists():
                with gzip.open(recorded, "rt") as f:
                    branch = json.load(f)
                record["initial_physics_matches"] = record[
                    "initial_physical"
                ] == branch.get("prefix", [{}])[0].get("physical")
                assert record["initial_physics_matches"]
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x") as f:
                json.dump(record, f, indent=2)
        finally:
            env.close()
        print(spec["index"], "geometry only", flush=True)


if __name__ == "__main__":
    main()
