"""Independent source/active-contact review, entirely from recorded native data."""

import argparse
import ast
import itertools
import json
import lzma
import math
from pathlib import Path

from rpd_pilot_common import BASE, PREFIX, TASKS, sha, verify_registration, write_json


def point_evidence(points):
    """A cached positive-gap, zero-impulse manifold is proximity, not active contact.

    Native penetration or a nonzero solver impulse is active contact evidence.
    This is retrospective evaluator interpretation, not a new success/eligibility
    threshold, sensor, force measurement or repair of the frozen prefix guard.
    """
    assert all(
        math.isfinite(p["separation"]) and all(math.isfinite(v) for v in p["impulse"])
        for p in points
    )
    return any(
        p["separation"] <= 0 or any(v != 0 for v in p["impulse"]) for p in points
    )


def contact(state):
    points = [p for c in state["evaluator_robot_object_contacts"] for p in c["points"]]
    return {
        "native_manifold_present": bool(points),
        "active_contact_evidence": point_evidence(points),
        "point_count": len(points),
        "min_separation_m": min((p["separation"] for p in points), default=None),
        "max_separation_m": max((p["separation"] for p in points), default=None),
        "max_native_impulse_norm": max(
            (math.sqrt(sum(v * v for v in p["impulse"])) for p in points), default=None
        ),
    }


def audit(output):
    assert not output.exists()
    output.mkdir(parents=True)
    verify_registration()
    code_path = Path("scripts/rpd_pilot_physics.py")
    tree = ast.parse(code_path.read_text())
    forbidden = {
        "restore",
        "reset",
        "set_state",
        "set_state_dict",
        "set_pose",
        "set_qpos",
    }
    calls = [
        n.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr in forbidden
    ]
    assert not calls
    tasks = {}
    for task in TASKS:
        rows = []
        for path in sorted((BASE / "physics" / task).glob("parent_*/*.json.xz")):
            with lzma.open(path, "rt") as stream:
                value = json.load(stream)
            row = value["row"]
            prefix = PREFIX[task]
            prefix_contacts = [contact(s) for s in value["records"][: prefix + 1]]
            if row["repeat"] == 0 and row["endpoint"] == "continue" and row["history"]:
                frames = [
                    contact(s)
                    for s in value["records"][prefix : prefix + row["delay_ticks"] + 1]
                ]
                rows.append(
                    {
                        "row_id": row["row_id"],
                        "raw_path": str(path),
                        "raw_sha256": sha(path),
                        "history": row["history"],
                        "parent_index": row["parent"]["index"],
                        "root_active_contact_evidence": frames[0][
                            "active_contact_evidence"
                        ],
                        "prefix_active_contact_boundary_count": sum(
                            c["active_contact_evidence"] for c in prefix_contacts
                        ),
                        "probe_tick_count": row["delay_ticks"],
                        "native_manifold_tick_count": sum(
                            c["native_manifold_present"] for c in frames[1:]
                        ),
                        "active_contact_tick_count": sum(
                            c["active_contact_evidence"] for c in frames[1:]
                        ),
                        "proximity_only_tick_count": sum(
                            c["native_manifold_present"]
                            and not c["active_contact_evidence"]
                            for c in frames[1:]
                        ),
                        "active_to_inactive_contact_transition": any(
                            a["active_contact_evidence"]
                            and not b["active_contact_evidence"]
                            for a, b in itertools.pairwise(frames)
                        ),
                        "frames": frames,
                        "scope": "Evaluator-only native solver/manifold diagnostics; no hardware force/damage claim. Root included separately. No matched-hold effect available.",
                    }
                )
        tasks[task] = {
            "histories": rows,
            "source_contact_boolean_semantics": "Legacy record.robot_object_contact checks native body-name manifold membership, not point penetration/impulse. It may include proximity-only records. Exact replay of that boolean was checked but is not proof of active contact.",
            "source_qualification_unchanged": "SOURCE_NOT_QUALIFIED; contact interpretation does not turn missing hold/outcome rows into qualified data",
        }
    result = {
        "passed": True,
        "physics_restarted": False,
        "tasks": tasks,
        "frozen_runner_sha256": sha(code_path),
        "forbidden_within_history_calls": calls,
        "diagnostic_inputs": "Fixed registered history menu; arm qpos/qvel first7, FK TCPxyz and native20Hz clock only. Object pose/contact/task labels are absent from recorded planner_frame.",
        "macro_privilege": "Unchanged native c/r macros internally use ideal object/goal state, as explicitly frozen; simulation-only, never claimed to be proprioceptive deployable hardware controllers.",
        "checkpoint_lineage": "Fresh World per evaluator episode, native seed reset in its unchanged constructor, full original prefix tape; root/controller custom matched across38returned branches/task. No restore invoked in new driver.",
        "statistical_scope": "No calibrated G, independent risk interval, population prevalence or held-out information gain. One parent exposed/task; macro/history branches correlated.",
        "native_failure_scope": "Started39th journal has no returned trace/backtrace. Exact stage and root cause are UNDETERMINED. Worker isolation is a future hypothesis only.",
        "source_semantics_limit": "Both cached-contact proxy interpretation and missing native-finalizer accounting are explicitly disclosed; original source and historical claims/evidence not rewritten.",
    }
    write_json(output / "source_review.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "active_contact_histories": {
                    t: sum(h["active_contact_tick_count"] > 0 for h in r["histories"])
                    for t, r in tasks.items()
                },
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
