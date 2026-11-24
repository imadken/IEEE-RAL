"""Read-only historical/source checks and pre-outcome neutral-control amendment."""

import importlib.metadata
import json
import os
import re
import subprocess
import time
from pathlib import Path

from rpd_pilot_common import (
    BASE,
    HOLD,
    OLD,
    PREFIX,
    TASKS,
    frozen_sources,
    parents,
    rows,
    sha,
    write_json,
)


def source_check():
    sources, versions = frozen_sources()
    for name, expected in sources.items():
        assert sha(name) == expected, name
    for name, expected in versions.items():
        assert importlib.metadata.version(name) == expected, name
    extra = [
        "src/dual_rec/physical_faults.py",
        ".venv/lib/python3.12/site-packages/sapien/pysapien/physx.pyi",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/registration.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/structs/articulation.py",
        ".venv/lib/python3.12/site-packages/mani_skill/agents/controllers/pd_joint_pos.py",
        ".venv/lib/python3.12/site-packages/mani_skill/envs/tasks/tabletop/pick_cube_cfgs.py",
    ]
    extra += list(
        map(str, Path(".venv/lib/python3.12/site-packages/sapien").glob("*.so"))
    )
    sources.update({p: sha(p) for p in extra})
    return {"passed": True, "hashes": sources, "versions": versions}


def snapshot():
    assert not BASE.exists(), "Fresh pilot directory required"
    BASE.mkdir(parents=True)
    status = subprocess.check_output(["git", "status", "--short"], text=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert head == "b00c441ffa88924c157dda51b8e4deff3934566b"
    old = json.loads((OLD / "preservation_before.json").read_text())
    for name, expected in old["files"].items():
        actual = sha(name) if Path(name).is_file() else None
        assert actual == expected, name
    files = set(subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0"))
    files |= set(old["files"])
    inventory = {
        name: sha(name) if Path(name).is_file() else None
        for name in sorted(files)
        if name
    }
    history = {}
    for root in (Path("results"), Path("research")):
        for p in root.rglob("*"):
            if (
                p.is_file()
                and not p.is_relative_to(BASE)
                and "__pycache__" not in p.parts
            ):
                s = p.stat()
                history[str(p)] = [s.st_size, s.st_mtime_ns]
    write_json(
        BASE / "preservation_before.json",
        {
            "head": head,
            "user_status": status,
            "files": inventory,
            "historical_file_metadata": history,
            "started_epoch": time.time(),
            "original_inventory_verified": len(old["files"]),
        },
    )
    return len(inventory), len(history)


def collision_check():
    targets = {p.seed for p in parents()}
    ids = {p.parent_id for p in parents()}
    seeds = set()
    historical_ids = set()
    inspected = {}
    path_ids = set()
    excluded = []
    seed_keys = {
        "seed",
        "seeds",
        "parent_seed",
        "parent_seeds",
        "episode_seed",
        "episode_seeds",
    }

    def extract(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                extract(v, k)
        elif isinstance(value, list):
            for v in value:
                extract(v, key)
        elif (
            key in seed_keys and isinstance(value, int) and not isinstance(value, bool)
        ):
            seeds.add(value)
        elif key in {"parent_id", "parent_ids"} and isinstance(value, str):
            historical_ids.add(value)

    for root_name in ("results", "research", "config"):
        for current, dirs, files in os.walk(root_name):
            base = Path(current)
            dirs[:] = [
                d
                for d in dirs
                if d not in {"env", "navigation_env", "cache", "__pycache__", ".venv"}
                and not (base / d).is_relative_to(BASE)
            ]
            for name in dirs + files:
                for match in re.finditer(r"(?:^|[^0-9])(\d{3,})(?:[^0-9]|$)", name):
                    path_ids.add(int(match[1]))
            for name in files:
                p = base / name
                if p == OLD / "final/stage2/reserved_parents.jsonl":
                    continue
                if p.suffix not in {".json", ".jsonl"}:
                    continue
                if p.stat().st_size > 64 * 1024**2:
                    excluded.append(str(p))
                    continue
                try:
                    if p.suffix == ".jsonl":
                        with p.open() as stream:
                            for line in stream:
                                if line.strip():
                                    extract(json.loads(line))
                    else:
                        extract(json.loads(p.read_text()))
                    inspected[str(p)] = sha(p)
                except (ValueError, UnicodeError):
                    excluded.append(str(p))
    overlaps = sorted(targets & (seeds | path_ids))
    id_overlaps = sorted(ids & historical_ids)
    result = {
        "passed": not overlaps and not id_overlaps,
        "reserved_parents": [p.model_dump() for p in parents()],
        "historical_seed_fields": len(seeds),
        "historical_path_seed_candidates": len(path_ids),
        "seed_overlaps": overlaps,
        "parent_id_overlaps": id_overlaps,
        "inspected_metadata_sha256": inspected,
        "excluded_metadata": excluded,
        "scope": "Retained structured metadata seed fields and all physical path identities; original RPD reservation excluded, not evidence of prior collection. No raw terminal labels used for selection.",
    }
    write_json(BASE / "seed_collision_audit.json", result)
    assert result["passed"], "SOURCE_NOT_QUALIFIED: historical identity collision"
    assert not excluded, (
        "SOURCE_NOT_QUALIFIED: unread metadata requires explicit review"
    )
    return result


def register():
    source = source_check()
    write_json(BASE / "source_preflight.json", source)
    collision_path = BASE / "seed_collision_audit.json"
    if collision_path.exists():
        collision = json.loads(collision_path.read_text())
        assert collision["passed"] and not collision["excluded_metadata"]
        for path, expected in collision["inspected_metadata_sha256"].items():
            assert sha(path) == expected, path
    else:
        collision_check()
    manifest = rows()
    with (BASE / "replay_manifest.jsonl").open("x") as stream:
        for row in manifest:
            stream.write(row.model_dump_json() + "\n")
    amendment = {
        "registered_before_new_physics": True,
        "registered_epoch": time.time(),
        "authority": "User-authorized final two-family physical feasibility pilot, 19 November 2026",
        "old_protocol_preserved": str(OLD / "final/stage2/protocol.json"),
        "old_protocol_sha256": sha(OLD / "final/stage2/protocol.json"),
        "old_reservation_sha256": sha(OLD / "final/stage2/reserved_parents.jsonl"),
        "tasks": TASKS,
        "prefix_controls": PREFIX,
        "control_hz": 20,
        "neutral_hold": {
            "command": HOLD,
            "ticks": [10, 20],
            "semantics": "Zero normalized Cartesian delta, native measured-current EE feedback every tick, gripper closed -1 matching last prefix command. This is a controlled hold, not frozen state; gravity/contact dynamics continue.",
        },
        "native_macro": "Unchanged dsre_paper_physics.action_for(world, mode, j, post_history_tcp), 70 ticks",
        "padding": "Zero EE delta, retain last actual gripper command; STOP retains history gripper or original closed gripper. Actual STOP outcome measured.",
        "deadline_controls": 90,
        "macro_endpoint": "after history delay+70 controls, also record deadline90; STOP has no macro endpoint",
        "episode_max_controls": 200,
        "episodes_per_task": 540,
        "parents_per_task": 10,
        "histories": "Original seven length0..2 plus neutral10 and neutral20, each c/r/STOP twice. Parents are independent units; branch observations are correlated.",
        "physics_worker_seconds_per_task": 10800,
        "compressed_bytes_per_task_cap": 3 * 1024**3,
        "runtime_measurement": "First registered empty/continue/repeat0 episode is startup/throughput measurement and retained in planned540, not an extra outcome. Before later parents reserve54*max episode wall seconds plus startup margin. Stop family on source failure. Hard cap overrides atomic completion if an unpredictable overrun occurs.",
        "replay": "Fresh native reset seed then exact registered prefix per isolated evaluator episode. No within-history reset, restore, state setter or teleport. Full prefix/controller-memory and repeated full-path checks.",
        "repeat_limits": {
            "position": 1e-5,
            "angle": 1e-4,
            "qpos": 1e-4,
            "velocity": 1e-4,
            "observation": 1e-4,
            "time": 1e-9,
            "contacts_and_task_flags": "exact",
            "controller_memory": "exact canonical JSON",
        },
        "allowed_set": {
            "arm": "Panda URDF joint limits +/-1e-6rad",
            "TCP": "abs(x/y)<=.60m,z in[.015,.50]",
            "object": "abs(x/y)<=.45m,z in[cube_half_size-.002,.50]",
            "scope": "Every20Hz control boundary; no force/damage/continuous-time guarantee. Post-probe violation retained adverse, not source attrition.",
        },
        "contact_mechanism": "Actual native robot-object contact during probe, plus measured motion/contact response vs identical-time neutral hold. No-contact and no-effect strata separate; native commands alone do not prove mechanism.",
        "object_motion_resolution_m": 1e-5,
        "tcp_motion_resolution_m": 1e-5,
        "K": "continue/recover successful native deadline90 outcomes, only when both repeated outcomes and source checks agree; compare identical d10/d20 hold. Missing and unstable outcomes give UNKNOWN, never empty set.",
        "erasure": "K_hold nonempty AND K_probe empty; creation converse. Lost/gained individual macro memberships separately. Require actual probe contact and sampled geometry for physical-mechanism conclusion.",
        "observation_analysis": "Frozen5mm TCP response bins/.01rad arm-motion/.1rad_s peak speed only; report descriptive distinctness and evaluator-only root object-minus-TCP16cell label within identical fixed root signatures. No fitted decoder, held-out information claim or favorable probe ordering.",
        "no_new_calibration": True,
        "full_stage2_inactive": True,
        "decisions": [
            "PHYSICAL_MECHANISM_OBSERVED",
            "QUALIFIED_NO_ERASURE_IN_PILOT",
            "SOURCE_NOT_QUALIFIED",
            "PROBE_NOT_MECHANISTIC",
        ],
    }
    write_json(BASE / "prephysics_amendment.json", amendment)
    files = [
        BASE / "source_preflight.json",
        BASE / "seed_collision_audit.json",
        BASE / "replay_manifest.jsonl",
        BASE / "prephysics_amendment.json",
    ]
    files += list(Path("scripts").glob("rpd_pilot_*.py"))
    files += [Path("tests/test_rpd_physical_pilot.py")]
    files += list((BASE / "supervisor").glob("*"))
    files += [Path(name) for name in source["hashes"]]
    files += [
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path("src/dual_rec/recoverability/adapters.py"),
        Path("docs/RPD_PHYSICAL_PILOT_METHOD_AND_AMENDMENT.md"),
        BASE / "prephysics_tests.txt",
    ]
    write_json(
        BASE / "prephysics_seal.json",
        {
            "registered_epoch": time.time(),
            "new_physics_so_far": 0,
            "files": {str(p): sha(p) for p in files},
        },
    )
    print(
        json.dumps(
            {
                "registered_rows": len(manifest),
                "collision_check_passed": True,
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["snapshot", "register"])
    args = parser.parse_args()
    if args.mode == "snapshot":
        print(snapshot())
    else:
        register()
