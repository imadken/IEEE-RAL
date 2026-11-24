"""Independent equations and replay checks; imports no learner or simulator."""

import numpy as np
from dsre_source_risk_audit import (
    difference,
    expected_action,
    predicates,
    state_equal,
    vec,
)


def push(branch):
    assert branch["status"] == "COMPLETE"
    assert len(branch["prefix_controls"]) == 53 and len(branch["prefix"]) == 54
    first = branch["prefix"][0]["observation"]
    cube, goal = vec(first, "obj_pose").copy(), vec(first, "goal_pos").copy()
    if branch["spec"]["condition"] == "misaligned":
        cube[1] += 0.07
        goal[1] += 0.07
    assert difference(cube, branch["cached_initial"]) < 1e-8
    assert difference(goal, branch["cached_goal"]) < 1e-8
    for j, (state, command) in enumerate(
        zip(branch["prefix"], branch["prefix_controls"])
    ):
        target = cube + [-0.055, 0, 0.12 if j < 20 else 0]
        if j >= 45:
            target = np.r_[goal[:2], cube[2]]
        expected = np.r_[
            np.clip(
                (target - vec(state["observation"], "tcp_pose")) / 0.1, -0.25, 0.25
            ),
            -1,
        ].astype(np.float32)
        assert difference(command, expected) < 2e-6
    state_equal(branch["prefix"][-1], branch["checkpoint"])
    primary, _ = predicates(first, branch["checkpoint"]["observation"])
    assert primary == branch["features"]
    assert len(branch["post"]) == len(branch["post_controls"]) == 70
    previous = branch["checkpoint"]
    for j, (command, state) in enumerate(
        zip(branch["post_controls"], branch["post"], strict=True)
    ):
        want = expected_action(
            "PushCube-v1",
            "continue" if branch["executed_action"] == "c" else "recover",
            j,
            previous["observation"],
            branch["initial_tcp"],
        )
        assert difference(command, want) < 2e-6
        assert abs(state["time"] - previous["time"] - 0.05) < 1e-8
        previous = state
    obj, goal = (
        vec(previous["observation"], "obj_pose"),
        vec(previous["observation"], "goal_pos"),
    )
    assert branch["success"] == bool(
        np.linalg.norm(obj[:2] - goal[:2]) < 0.1 and obj[2] < 0.025
    )


def parity(a, b, task):
    assert a["spec"] == b["spec"]
    assert a["prefix_controls"] == b["prefix_controls"]
    assert a["features"] == b["features"]
    if task == "PushCube-v1":
        assert a["model_edit"] == b["model_edit"]
        assert a["controller_memory"] == b["controller_memory"]
        assert len(a["prefix"]) == len(b["prefix"])
        for x, y in zip(a["prefix"], b["prefix"], strict=True):
            state_equal(x, y)
        state_equal(a["checkpoint"], b["checkpoint"])
    else:
        from dsre_evidence_audit import equal

        equal(a["prefix"], b["prefix"])
        equal(a["checkpoint"], b["checkpoint"])
        assert a["geometry"] == b["geometry"]


def peg(branch):
    from dsre_evidence_prospective_audit import physical

    physical(branch, "PegInsertionSide-v1")


def native_abort(branch):
    return (
        branch.get("status") == "FAILED_PREREQUISITE_OR_PREFIX"
        and branch.get("phase") == "prefix"
        and branch.get("error") == "UPSTREAM_SCREW_PLANNING_FAILED"
        and bool(branch.get("prefix"))
        and len(branch["prefix"]) == len(branch.get("prefix_controls", [])) + 1
        and not branch.get("post")
        and not branch.get("post_controls")
        and "checkpoint" not in branch
        and "success" not in branch
    )
