"""One selected frozen PickCube macro; fresh-prefix reconstruction, never pairing."""

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

from dsre_evidence_tasks import plain, write
from dsre_paper_physics import World, action_for, initial

from dual_rec.dsre.features import ObservationHistory, feature_values, observed_frame
from dual_rec.overnight_pick import PickFault
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes


def run(spec, action):
    condition = "evidence-offset"
    case, prefix = initial(
        spec["seed"], PickFault(name=condition, offset_x=spec["offset"])
    )
    world = World("PickCube-v1", spec["seed"], "nominal")
    world.wrapped._max_episode_steps = 200
    try:
        states = [jsonable(world.state())]
        for command in case["prefix_actions"]:
            states.append(jsonable(world.step(command)))
        assert len(states) == len(prefix)
        assert all(
            passes(compare(jsonable(a), b)) for a, b in zip(prefix, states, strict=True)
        )
        checkpoint = jsonable(world.state(refresh=True))
        history = ObservationHistory(
            first=observed_frame(prefix[0]["time"], prefix[0]["observation"]),
            current=observed_frame(checkpoint["time"], checkpoint["observation"]),
        )
        features = feature_values(history)
        memory = jsonable(world.adapter.capture().custom)
        output = {
            "prefix": jsonable(prefix),
            "prefix_controls": case["prefix_actions"],
            "checkpoint": checkpoint,
            "controller_memory": memory,
            "features": features,
            "horizon": 70,
            "coupling": "deterministic simulator execution, no hardware transfer",
            "versions": {
                p: importlib.metadata.version(p)
                for p in ("mani-skill", "sapien", "torch", "numpy")
            },
        }
        if action == "screen":
            return dict(output, status="CHECKPOINT_ONLY")
        tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
        frames = []
        controls = []
        for j in range(70):
            command = action_for(
                world, "continue" if action == "c" else "recover", j, tcp
            )
            controls.append(jsonable(command))
            frames.append(jsonable(world.step(command)))
        return dict(
            output,
            status="COMPLETE",
            post=frames,
            post_controls=controls,
            success=bool(frames[-1]["success"]),
            planning_seconds=0.0,
            initial_tcp=tcp.tolist(),
        )
    finally:
        world.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--action", choices=("c", "r", "screen"), required=True)
    a = p.parse_args()
    spec = json.loads(a.spec.read_text())
    start = time.perf_counter()
    try:
        result = run(spec, a.action)
    except (
        AssertionError,
        RuntimeError,
        ValueError,
        AttributeError,
        TypeError,
        KeyError,
        OSError,
    ) as error:
        import traceback

        result = {
            "status": "FAILED_PREREQUISITE_OR_PREFIX",
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
    result.update(spec=spec, action=a.action, wall_seconds=time.perf_counter() - start)
    write(a.output, plain(result))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k in ("status", "error", "wall_seconds", "success")
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
