"""Bounded live qualification on four already inspected calibration states only."""

import argparse
import gzip
import importlib.metadata
import json
import time
from pathlib import Path

from dsre_final_verify import load_trace, verify_execution, verify_sources
from dsre_followup_batch import atomic, read, sha
from dsre_operational_batch import selected_branch
from dsre_operational_observations import packet_from_summary
from dsre_paper_physics import Cell, World, action_for

from dual_rec.dsre.operational import OperationalRouter
from dual_rec.replay import jsonable
from dual_rec.validation import array, compare, passes


def qualify(root):
    verify_sources(root, "qualification_freeze.json")
    assert not (root / "qualification_seal.json").exists()
    old = Path(read(Path("config/dsre_final_sprint.json"))["prior_root"])
    router = OperationalRouter(read(root / "frozen_routers.json"))
    calibration = read(root / "calibration_decision.json")
    results = []
    versions = {
        p: importlib.metadata.version(p)
        for p in ("mani-skill", "sapien", "torch", "numpy", "scipy", "pydantic")
    }
    assert versions == read(old / "worker_environment.json")["versions"], versions
    atomic(root / "worker_environment.json", {"versions": versions})
    current = {}
    try:
        for source in read(Path("config/dsre_final_sprint.json"))[
            "qualification_sources"
        ]:
            summary = read(old / "fresh" / source / "summary.json")
            raw = load_trace(summary)
            assert raw == json.loads(json.dumps(raw, allow_nan=False))
            assert raw["cell"]["seed"] not in (8000180,)
            packet = packet_from_summary(summary, read(root / "frozen_routers.json"))
            assert set(packet.model_dump()) == {"task", "values", "full_values"}
            for action in ("continue", "recover"):
                current = {"source": source, "action": action, "phase": "prefix"}
                condition = (
                    "misaligned" if summary["condition"] == "misaligned" else "nominal"
                )
                world = World(summary["task"], summary["seed"], condition)
                world.wrapped._max_episode_steps = 200
                deadline = time.monotonic() + 120
                try:
                    states = [jsonable(world.state())]
                    for command in raw["prefix_actions"]:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("qualification prefix deadline")
                        states.append(jsonable(world.step(command)))
                    memory = jsonable(world.adapter.capture().custom)
                    start = jsonable(world.state(refresh=True))
                    current.update(
                        prefix_states=states,
                        controller_memory=memory,
                        model_edit=jsonable(world.edit),
                        start=start,
                    )
                    errors = [
                        compare(a, b)
                        for a, b in zip(raw["prefix"], states, strict=True)
                    ]
                    assert all(passes(e) for e in errors)
                    assert passes(compare(raw["canonical_start"], start))
                    assert (
                        memory == raw["canonical_controller_memory"]
                        and world.edit == raw["model"]["edit"]
                    )
                    tcp = array(world.env.agent.tcp.pose.p).reshape(3).copy()
                    current.update(phase="future", initial_tcp=tcp.tolist(), frames=[])
                    for i in range(70):
                        if time.monotonic() >= deadline:
                            raise TimeoutError("qualification future deadline")
                        command = action_for(world, action, i, tcp)
                        before = world.state()
                        state = world.step(command)
                        current["frames"].append(
                            {
                                "before_observation": jsonable(before["observation"]),
                                "action": jsonable(command),
                                "state": jsonable(state),
                            }
                        )
                    current["terminal_success"] = bool(
                        current["frames"][-1]["state"]["success"]
                    )
                    proof = verify_execution(raw, current, summary["task"], action)
                    directory = root / "qualification" / source
                    directory.mkdir(parents=True, exist_ok=True)
                    path = directory / (action + ".json.gz")
                    with gzip.open(path, "wt") as stream:
                        json.dump(current, stream, allow_nan=False)
                    results.append(
                        {
                            "source": source,
                            "source_sha256": summary["source_sha256"],
                            "action": action,
                            "terminal_success": current["terminal_success"],
                            "execution": str(path),
                            "sha256": sha(path),
                            **proof,
                        }
                    )
                finally:
                    world.close()
            selected_branch(
                Cell(
                    task=summary["task"],
                    seed=summary["seed"],
                    condition=summary["condition"],
                ),
                summary,
                root,
                router,
                calibration,
                time.monotonic() + 120,
            )
            selected_directory = (
                root
                / "selected"
                / summary["task"]
                / f"{summary['seed']}-{summary['condition']}"
            )
            selected_result = read(selected_directory / "execution.json")
            if selected_result["new_continuations"]:
                with gzip.open(
                    selected_directory / "execution.json.gz", "rt"
                ) as stream:
                    actual = json.load(stream)
                verify_execution(
                    raw, actual, summary["task"], selected_result["action"]
                )
        assert any(r["terminal_success"] for r in results) and any(
            not r["terminal_success"] for r in results
        )
        assert all(r["nonempty_contact_states"] for r in results)
        atomic(
            root / "qualification_results.json",
            {
                "status": "PASS",
                "inspected_states": 4,
                "both_action_executions": len(results),
                "executions": results,
                "independent_verifier": "Independent raw state/quat/direct controller equations, separate from production compare",
                "contaminated_parent_rerun": False,
            },
        )
        atomic(
            root / "qualification_seal.json",
            {
                "status": "PASS",
                "epoch": time.time(),
                "results_sha256": sha(root / "qualification_results.json"),
                "source_freeze_sha256": sha(root / "qualification_freeze.json"),
            },
        )
        print(
            json.dumps(
                {"status": "QUALIFIED", "states": 4, "both_action_executions": 8}
            ),
            flush=True,
        )
    except Exception as error:
        current["reason"] = str(error)
        with gzip.open(root / "qualification_failure.json.gz", "wt") as stream:
            json.dump(current, stream, allow_nan=False)
        atomic(
            root / "qualification_failure.json",
            {
                "status": "FAIL",
                "reason": str(error),
                "phase": current.get("phase"),
                "source": current.get("source"),
                "action": current.get("action"),
            },
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    qualify(parser.parse_args().root)
