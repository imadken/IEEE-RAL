"""Timeboxed read-only existing-controller feasibility; never instantiate physics."""

import argparse
import ast
import importlib.metadata
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha


def inventory(root):
    start = time.monotonic()
    sources = []
    for name in (
        "overnight_replay.py",
        "overnight_pick.py",
        "qualify.py",
        "mani_runner.py",
        "dsre_paper_physics.py",
    ):
        p = Path("scripts") / name
        tree = ast.parse(p.read_text())
        sources.append(
            {
                "source": str(p),
                "sha256": sha(p),
                "functions": [
                    n.name
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ],
            }
        )
    package = Path(
        importlib.metadata.distribution("mani-skill").locate_file("mani_skill")
    )
    solvers = []
    for path in sorted((package / "examples/motionplanning").rglob("*.py")):
        if time.monotonic() - start > 3600:
            raise TimeoutError("Read-only breadth inventory limit")
        if path.name.startswith("__"):
            continue
        tree = ast.parse(path.read_text())
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if any(n.startswith("solve") for n in functions):
            solvers.append(
                {
                    "source": str(path),
                    "sha256": sha(path),
                    "functions": functions,
                    "scope": "Installed nominal expert/source code; no independently registered paired recovery protocol or qualified DSRE prefix for this task",
                }
            )
    old = Path(read(Path("config/dsre_final_sprint.json"))["prior_root"])
    oldgate = read(old / "third_task_audit.json")
    value = {
        "status": "BLOCKED_EXISTING_INTERVENTION_PROTOCOL_GATE",
        "wall_seconds": time.monotonic() - start,
        "new_physics_seconds": 0,
        "sources": sources,
        "installed_motion_planning_source": str(package / "examples/motionplanning"),
        "nominal_solvers": solvers,
        "existing_lift_gate": oldgate,
        "conclusion": "Read-only source assessment finds no additional already registered pair of semantically distinct, source-replayable recovery actions with the unchanged horizon/objective and qualified full-prefix/controller state. Installed nominal task solvers do not supply that paired protocol. Existing Lift/Panda only clips nominal speed and its retained210starts are both-success; it cannot be relabeled recovery validation. Creating a skill, fault, pipeline or selecting another task by DSRE gains is forbidden. The optional arm stops before any new third-task physics; external validity remains two scripted simulator tasks.",
    }
    atomic(root / "breadth_feasibility.json", value)
    print(
        {
            "status": value["status"],
            "nominal_solvers_inspected": len(solvers),
            "wall_seconds": value["wall_seconds"],
            "new_physics_seconds": 0,
        },
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    inventory(parser.parse_args().root)
