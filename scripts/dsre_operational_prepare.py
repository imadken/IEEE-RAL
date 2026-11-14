"""Freeze a disjoint calibration/test campaign and unchanged scientific inputs."""

import argparse
import ast
import json
import math
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_repair_experiment import table_for

from dual_rec.dsre.operational import METHODS


def prepare(root):
    if (root / "confirmation_freeze.json").exists():
        raise ValueError("Already frozen")
    config = read(Path("config/dsre_operational.json"))
    old = Path(config["prior_root"])
    seal = read(old / "completion_manifest.json")
    for name, expected in seal["files"].items():
        assert sha(old / name) == expected, name
    for name, expected in seal["maintained_files"].items():
        assert sha(Path(name)) == expected, name
    # The source gate is evaluated before any new outcome, not after a favorable
    # third-task pilot. Lift's existing alternative is a speed clip, with no
    # registered failed-start recovery contrast in its retained qualified study.
    lift_source = Path("scripts/overnight_replay.py")
    tree = ast.parse(lift_source.read_text())
    continuation = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "continuation"
    )
    atomic(
        root / "third_task_audit.json",
        {
            "status": "BLOCKED_SOURCE_SEMANTICS_BEFORE_NEW_PHYSICS",
            "task_chosen_in_advance": "robosuite Lift/Panda",
            "source": str(lift_source),
            "source_sha256": sha(lift_source),
            "existing_continuation_source": ast.get_source_segment(
                lift_source.read_text(), continuation
            ),
            "historical_report": "docs/RECOVERY_CLAIMS_EXPERIMENTAL_REPORT.md",
            "historical_qualified_parents": 210,
            "historical_initial_failures": 0,
            "historical_continue_successes": 210,
            "historical_recover_successes": 210,
            "new_physics": 0,
            "reason": "Existing alternative clips nominal Cartesian command to +/-0.2; no registered distinct recovery procedure or varying adequacy/failed-start contrast. Snapshot immediate-readout issue is retained; no native restore is substituted. Creating a new controller or failure condition is forbidden.",
            "gate": "Require an existing distinct registered recovery intervention, paired varying outcomes, observable predecision vocabulary and qualified full-prefix/controller parity before a new cohort. Source prerequisites fail; no further physics on this arm.",
        },
    )
    parents = []
    old_groups = set()
    for path in Path("results").rglob("fresh_seed_manifest.json"):
        if path.parent == root:
            continue
        value = read(path)
        old_groups.update(p["group"] for p in value.get("parents", []) if "group" in p)
    # Inspect actual execution directories too, including interrupted attempts.
    existing = {
        f"{task}/{p.name.split('-')[0]}"
        for task in ("PickCube-v1", "PushCube-v1")
        for p in Path("results").glob(f"**/fresh/{task}/*")
        if p.is_dir()
    }
    count = config["calibration_parents_per_task"] + config["test_parents_per_task"]
    for i in range(count):
        for task, first, conditions in (
            ("PickCube-v1", config["pick_first_seed"], ["nominal", "offset002"]),
            ("PushCube-v1", config["push_first_seed"], ["nominal", "misaligned"]),
        ):
            group = f"{task}/{first + i}"
            assert group not in old_groups | existing, group
            parents.append(
                {
                    "index": len(parents),
                    "original_index": len(parents),
                    "group": group,
                    "task": task,
                    "seed": first + i,
                    "conditions": conditions,
                    "split": "calibration"
                    if i < config["calibration_parents_per_task"]
                    else "test",
                }
            )
    assert len(parents) == 520
    atomic(
        root / "fresh_seed_manifest.json",
        {
            "status": "FROZEN_BEFORE_OUTCOMES",
            "parents": parents,
            "primary_unit": "seed parent; both fixed conditions",
            "new_seed_overlap": [],
            "existing_manifest_groups_checked": len(old_groups),
            "existing_execution_directories_checked": len(existing),
        },
    )
    frozen = read(old / "frozen_routers.json")
    rows = [
        json.loads(line)
        for line in Path(
            "results/dsre-evidence-repair/20261113T180828Z/qualified_pairs.jsonl"
        )
        .read_text()
        .splitlines()
    ]
    for task, budgets in frozen["tasks"].items():
        source = [r for r in rows if r["task"] == task]
        full, groups = table_for(
            source, tuple(range(6)), budgets["1"]["table"]["scope"]
        )
        assert groups == budgets["1"]["parent_groups"]
        budgets["1"]["full_table"] = full.model_dump(mode="json")
    atomic(root / "frozen_routers.json", frozen)
    atomic(
        root / "calibration_plan.json",
        {
            "primary_router": "DSRE_risk",
            "methods": METHODS,
            "strata_per_method": 4,
            "target": 0.1,
            "primary_four_stratum_delta": 0.0125,
            "formal_global_delta_per_stratum": 0.05 / (4 * len(METHODS)),
            "zero_error_required_primary": math.ceil(math.log(0.0125) / math.log(0.9)),
            "zero_error_required_global": math.ceil(
                math.log(0.05 / (4 * len(METHODS))) / math.log(0.9)
            ),
            "calibration_parents_per_task": 180,
            "test_parents_per_task": 80,
            "forecast": "Historical strict Pick recover assignment17/166 implies about18/180; risk-tier assignments computed from frozen old inputs before outcomes. Rare recovery cannot be assumed certifiable. No outcome-directed replenishment.",
            "formal_scope": "Assigned-parent any-error across two registered conditions; checkpoint-weighted rates descriptive. All methods use global Bonferroni standard for operational comparisons. Four-stratum primary bounds also reported diagnostically, never used to loosen the gate.",
        },
    )
    for name in (
        "chunks",
        "parent_attempts",
        "parent_progress",
        "parent_live",
        "selected",
    ):
        (root / name).mkdir()
    protocol = Path("docs/DSRE_FULL_PAPER_SCIENCE_PROTOCOL.md")
    (root / "preregistration.md").write_bytes(protocol.read_bytes())
    sources = [
        Path("config/dsre_operational.json"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        *[
            Path("scripts") / n
            for n in (
                "dsre_operational_prepare.py",
                "dsre_operational_batch.py",
                "dsre_operational_analysis.py",
                "dsre_operational_observations.py",
                "dsre_operational_audit.py",
                "dsre_paper_physics.py",
                "dsre_paper_confirmation.py",
                "dsre_paper_reanalysis.py",
                "dsre_repair_experiment.py",
                "dsre_followup_analysis.py",
                "dsre_followup_batch.py",
                "overnight_replay.py",
                "overnight_pick.py",
                "mani_runner.py",
                "qualify.py",
            )
        ],
    ]
    inputs = [
        root / n
        for n in (
            "authority.txt",
            "preregistration.md",
            "fresh_seed_manifest.json",
            "frozen_routers.json",
            "calibration_plan.json",
            "third_task_audit.json",
            "environment.json",
            "preflight_regression.json",
            "offline_preflight_audit.json",
        )
    ]
    inputs += [
        old / "completion_manifest.json",
        old / "confirmation_freeze.json",
        Path("uv.lock"),
    ]
    atomic(
        root / "confirmation_freeze.json",
        {
            "status": "FROZEN_BEFORE_NEW_OUTCOMES",
            "source_sha256": {str(p): sha(p) for p in sources},
            "input_sha256": {str(p): sha(p) for p in inputs},
            "original_router_sha256": sha(old / "frozen_routers.json"),
            "new_model_fits": 0,
            "maximum_new_parents": 520,
            "old_sealed_members_verified": len(seal["files"]),
        },
    )
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "parents": 520,
                "calibration": 360,
                "test": 160,
                "methods": len(METHODS),
                "third_task": "BLOCKED_SOURCE_SEMANTICS",
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    prepare(parser.parse_args().root)
