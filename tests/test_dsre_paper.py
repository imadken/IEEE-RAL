"""Prospective evidence audits must reject corrupted physics and pseudo-replication."""

import copy
import gzip
import hashlib
import importlib
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def checker(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    return importlib.import_module("dsre_paper_confirmation")


def observation(obj=(0, 0, 0.02), tcp=(0, 0, 0.10), goal=(0.1, 0, 0.02)):
    return {
        "agent": {"qpos": [[0] * 7 + [0.02, 0.02]]},
        "extra": {
            "obj_pose": [[*obj, 1, 0, 0, 0]],
            "tcp_pose": [[*tcp, 1, 0, 0, 0]],
            "goal_pos": [list(goal)],
        },
    }


@pytest.mark.parametrize(
    "task,steps,expected_z,grippers",
    [
        (
            "PickCube-v1",
            [0, 7, 8, 21, 22, 33, 34, 45, 46],
            [0.25, 0.25, 0.2, 0.2, -0.25, -0.25, -0.25, -0.25, -0.25],
            [1, 1, 1, 1, 1, 1, -1, -1, -1],
        ),
        (
            "PushCube-v1",
            [0, 5, 6, 15, 16, 25, 26],
            [0.25, 0.25, 0.2, 0.2, -0.25, -0.25, -0.25],
            [-1] * 7,
        ),
    ],
)
def test_independent_action_phase_boundaries(
    checker, task, steps, expected_z, grippers
):
    obs = observation()
    for j, z, gripper in zip(steps, expected_z, grippers, strict=True):
        action = checker.expected_action(task, "recover", j, obs, [0, 0, 0.10])
        assert action[2] == pytest.approx(z)
        assert action[3] == gripper
        assert np.abs(action[:3]).max() <= 0.25


def test_predicates_use_predecision_geometry_and_strict_optional_boundary(checker):
    obs = observation(obj=(-0.02, 0, 0.02), goal=(0, 0, 0.02))
    primary, optional = checker.predicates(obs, obs)
    assert primary == [True, False, False, False, True, True]
    assert optional == [False, False, False, False, False, False]


def test_cluster_resampling_keeps_paired_conditions_as_one_parent(checker):
    rows = [{"group": str(g), "d": float(g)} for g in (0, 1) for _ in range(2)]
    interval = checker.cluster_interval(rows, "d", seed=9, draws=4000)
    assert interval["independent_parents"] == 2
    assert interval["value"] == 0.5
    assert interval["parent_percentile95"] == [0, 1]


def synthetic_record(checker, tmp_path):
    root = tmp_path
    (root / "confirmation_freeze.json").write_text("{}")
    obs = observation()
    base = {
        "position": [0, 0, 0.02],
        "quaternion": [1, 0, 0, 0],
        "qpos": [[0] * 9],
        "velocity": [0] * 15,
        "observation": obs,
        "time": 1.0,
        "success": True,
        "contacts": [],
    }
    record = {
        "cell": {"task": "PickCube-v1", "seed": 1, "condition": "nominal"},
        "freeze_sha256": checker.sha(root / "confirmation_freeze.json"),
        "future_trajectory_duplicate_executions": 0,
        "prefix": [copy.deepcopy(base), copy.deepcopy(base)],
        "prefix_actions": [[0] * 4],
        "canonical_start": copy.deepcopy(base),
        "canonical_controller_memory": {"target": [1, 2, 3]},
        "traces": {},
        "model": {
            "edit": {},
            "versions": {
                "mani-skill": "3.0.1",
                "sapien": "3.0.3",
                "torch": "2.5.1+cpu",
                "numpy": "1.26.4",
            },
        },
        "outcomes": {"continue_value": True, "recover_value": True},
    }
    for mode in ("continue", "recover"):
        frames = []
        for j in range(70):
            state = copy.deepcopy(base)
            state["time"] = 1.0 + (j + 1) * 0.05
            frames.append(
                {
                    "before_observation": copy.deepcopy(obs),
                    "action": checker.expected_action(
                        "PickCube-v1", mode, j, obs, [0, 0, 0.10]
                    ).tolist(),
                    "state": state,
                }
            )
        record["traces"][mode] = {
            "prefix_history": copy.deepcopy(record["prefix"]),
            "controller_memory": copy.deepcopy(record["canonical_controller_memory"]),
            "model_edit": {},
            "start": copy.deepcopy(base),
            "initial_tcp": [0, 0, 0.10],
            "frames": frames,
        }
    primary, optional = checker.predicates(obs, obs)
    summary = {
        "id": "PickCube-v1/1/nominal",
        **record["cell"],
        "features": primary,
        "optional_features": optional,
        "initial_success": True,
        "outcomes": record["outcomes"],
        "source": str(root / "trace.json.gz"),
    }
    return root, record, summary


def write_record(record, summary):
    path = Path(summary["source"])
    with gzip.open(path, "wt") as stream:
        json.dump(record, stream)
    summary["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_replay_audit_checks_actual_outcomes_and_actions(checker, tmp_path):
    root, record, summary = synthetic_record(checker, tmp_path)
    write_record(record, summary)
    audit = checker.audit_trace(summary, root)
    assert audit["outcome_controls_checked"] == 140
    assert audit["maximum_action_error"] == 0


@pytest.mark.parametrize(
    "corruption", ["memory", "prefix", "action", "outcome", "duplicate"]
)
def test_replay_audit_rejects_corruption_even_after_source_rehash(
    checker, tmp_path, corruption
):
    root, record, summary = synthetic_record(checker, tmp_path)
    if corruption == "memory":
        record["traces"]["recover"]["controller_memory"] = {"target": [4, 5, 6]}
    elif corruption == "prefix":
        record["traces"]["recover"]["prefix_history"][0]["position"][0] = 0.01
    elif corruption == "action":
        record["traces"]["recover"]["frames"][0]["action"][0] = 0.5
    elif corruption == "outcome":
        record["traces"]["recover"]["frames"][-1]["state"]["success"] = False
    else:
        record["future_trajectory_duplicate_executions"] = 1
    write_record(record, summary)
    with pytest.raises(AssertionError):
        checker.audit_trace(summary, root)


def test_independent_tree_requires_distinct_parent_support(checker):
    table = {
        "rows": [
            {
                "id": "a",
                "features": [True],
                "outcomes": {"continue_value": True, "recover_value": False},
            },
            {
                "id": "b",
                "features": [True],
                "outcomes": {"continue_value": True, "recover_value": False},
            },
        ]
    }
    nodes = [{"feature": None}]
    assert (
        checker.independent_tree_action(
            nodes, table, {"a": "same", "b": "same"}, [True], 1
        )
        is None
    )
    assert (
        checker.independent_tree_action(
            nodes, table, {"a": "one", "b": "two"}, [True], 1
        )
        == "continue"
    )


def test_sealed_evidence_cannot_be_overwritten(checker, tmp_path):
    (tmp_path / "completion_manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="sealed"):
        checker.evaluate(tmp_path)
    reanalysis = importlib.import_module("dsre_paper_reanalysis")
    with pytest.raises(ValueError, match="sealed"):
        reanalysis.reanalyze(tmp_path)
