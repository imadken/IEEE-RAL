"""Exactly one frozen Push macro in a fresh native process."""

import argparse
import importlib.metadata
import json
import time
import traceback
from pathlib import Path

from dsre_evidence_tasks import plain, write
from dsre_last_common import ROOT, read, sha
from dsre_paper_physics import World, action_for
from overnight_replay import prefix_to_stage

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.replay import jsonable
from dual_rec.validation import array


def run(spec, action):
    world = World("PushCube-v1", spec["seed"], spec["condition"])
    world.wrapped._max_episode_steps = 200
    try:
        controls, prefix, _, _ = prefix_to_stage(world, "transport")
        checkpoint = jsonable(world.state(refresh=True))
        features = feature_values(
            ObservationHistory(
                first=observed_frame(
                    prefix[0]["time"], jsonable(prefix[0]["observation"])
                ),
                current=observed_frame(checkpoint["time"], checkpoint["observation"]),
            )
        )
        output = {
            "prefix": jsonable(prefix),
            "prefix_controls": jsonable(controls),
            "checkpoint": checkpoint,
            "controller_memory": jsonable(world.adapter.capture().custom),
            "features": features,
            "model_edit": jsonable(world.edit),
            "cached_initial": world.initial.tolist(),
            "cached_goal": world.goal.tolist(),
            "horizon": 70,
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("mani-skill", "sapien", "torch", "numpy")
            },
        }
        assert len(controls) == 53 and all(v is not None for v in features)
        if action == "policy":
            from dsre_last_model import select

            from dual_rec.evidence_aware.views import guard_data_access

            path = ROOT / "model_frozen.json"
            accessed = guard_data_access(Path("results"), [path])
            output["model_sha256"] = sha(path)
            output["decision"] = select(read(path), features)
            action = output["decision"]["actions"]["DSRE"]
            output["successful_reads"] = list(accessed)
            output["decision_epoch"] = time.time()
        output["executed_action"] = action
        initial_tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
        post, commands = [], []
        for j in range(70):
            command = action_for(
                world, "continue" if action == "c" else "recover", j, initial_tcp
            )
            commands.append(jsonable(command))
            post.append(jsonable(world.step(command)))
        return dict(
            output,
            status="COMPLETE",
            post=post,
            post_controls=commands,
            initial_tcp=initial_tcp.tolist(),
            success=bool(post[-1]["success"]),
        )
    finally:
        world.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--action", required=True, choices=("c", "r", "policy"))
    args = parser.parse_args()
    spec = read(args.spec)
    start = time.time()
    try:
        result = run(spec, args.action)
    except Exception as error:  # noqa: BLE001 -- retain failed source, no retry
        result = {
            "status": "FAILED_SOURCE",
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
    result.update(
        spec=spec,
        action=args.action,
        started_epoch=start,
        completed_epoch=time.time(),
        wall_seconds=time.time() - start,
    )
    write(args.output, plain(result))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k in ("status", "success", "wall_seconds", "error")
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
