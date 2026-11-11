"""Compact recipes restore exact public models/plans without new experiments."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dual_rec.revalidation.contracts import Parameters
from dual_rec.revalidation.episodes import generate_episodes

SPEC = importlib.util.spec_from_file_location(
    "revalidation_prepare", ROOT / "scripts/revalidation_prepare.py"
)
prepare = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare
SPEC.loader.exec_module(prepare)

DOMAIN = """(define (domain history)
(:requirements :strips)
(:predicates (ready) (holding) (done))
(:action grasp :parameters () :precondition (ready)
 :effect (and (holding) (not (ready))))
(:action release :parameters () :precondition (holding)
 :effect (and (ready) (not (holding))))
(:action finish :parameters () :precondition (ready) :effect (done)))
"""
PROBLEM = """(define (problem history-task) (:domain history)
(:init (ready)) (:goal (done)))
"""


def fixture(tmp_path, monkeypatch, plan=None):
    cache = tmp_path / "cache"
    for name, text in (("domain", DOMAIN), ("problem", PROBLEM)):
        path = cache / f"unit/{name}.pddl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    parameters = Parameters(
        event_hazard=0.1,
        sensor_error=0.02,
        missing_probability=0.1,
        permission_threshold=0.85,
        periodic_interval=1,
        expiry_steps=0,
    )
    config = {
        "schema_version": 1,
        "run_id": "unit",
        "reviewed_base": "0" * 40,
        "source_repository": prepare.SOURCE_REPOSITORY,
        "source_revision": prepare.SOURCE_REVISION,
        "logiv_revision": prepare.PINNED_COMMIT,
        "parameters": parameters.model_dump(mode="json"),
        "primary_baseline": "B2",
        "input_tasks": [
            {
                "parent_id": "unit-task",
                "family": "unit",
                "split": "development",
                "paths": {name: f"unit/{name}.pddl" for name in ("domain", "problem")},
                "sha256": {
                    name: prepare.digest(cache / f"unit/{name}.pddl")
                    for name in ("domain", "problem")
                },
                "plan": plan or ["grasp", "release", "finish"],
            }
        ],
    }
    target = tmp_path / "configuration.json"
    target.write_text(json.dumps(config))
    monkeypatch.setattr(prepare, "_repository_inventory", lambda: ({}, []))
    monkeypatch.setattr(
        prepare,
        "_fetch_source",
        lambda _: pytest.fail("Local fixture must not access network"),
    )
    return target, cache, parameters


def test_restore_checks_both_transition_models_and_preserves_known_history(
    tmp_path, monkeypatch
):
    config, cache, parameters = fixture(tmp_path, monkeypatch)
    root = tmp_path / "restored"
    result = prepare.restore_inputs(config, root, cache)
    assert result["tasks"] == 1 and result["source_files"] == 2
    assert result["no_plan_search"] and result["no_experiments"]
    tasks = json.loads((root / "tasks.json").read_text())
    assert tasks[0]["nominal_states"] == [
        ["ready"],
        ["holding"],
        ["ready"],
        ["done", "ready"],
    ]
    episodes = list(generate_episodes(tasks, "development", parameters, schedules=1))
    known = [e for e in episodes if e.regime == "known_action"]
    assert len(known) == 2
    assert known[0].context.known_after_cache[0].name == "grasp"
    assert known[0].context.base.evidence["holding"] is True
    assert known[0].context.updated_at["holding"] == 0
    assert known[0].context.observed_at["holding"] == -1
    selection = json.loads((root / "selection.json").read_text())
    assert selection["primary_baseline"] == "B2"
    assert selection["parameters"] == parameters.model_dump(mode="json")


def test_hash_mismatch_is_preserved_and_rejected(tmp_path, monkeypatch):
    config, cache, _ = fixture(tmp_path, monkeypatch)
    bad = cache / "unit/problem.pddl"
    bad.write_text(PROBLEM + "; changed\n")
    before = bad.read_bytes()
    with pytest.raises(ValueError, match="SHA-256"):
        prepare.restore_inputs(config, tmp_path / "restored", cache)
    assert bad.read_bytes() == before
    status = json.loads((tmp_path / "restored/preparation_status.json").read_text())
    assert status["status"] == "FAILED"


@pytest.mark.parametrize(
    "plan,error",
    [
        (["release", "finish"], "precondition"),
        (["grasp", "release"], "goal"),
        (["imaginary"], "unsupported grounding"),
    ],
)
def test_invalid_frozen_plan_never_triggers_a_planning_search(
    tmp_path, monkeypatch, plan, error
):
    config, cache, _ = fixture(tmp_path, monkeypatch, plan)
    with pytest.raises(ValueError, match=error):
        prepare.restore_inputs(config, tmp_path / "restored", cache)


def test_existing_run_is_never_overwritten(tmp_path, monkeypatch):
    config, cache, _ = fixture(tmp_path, monkeypatch)
    root = tmp_path / "complete"
    root.mkdir()
    seal = root / "completion_manifest.json"
    seal.write_text("original seal")
    with pytest.raises(FileExistsError, match="Preserve existing run"):
        prepare.restore_inputs(config, root, cache)
    assert seal.read_text() == "original seal"


def test_existing_matching_cache_and_semantic_fingerprint_ignore_set_order(
    tmp_path, monkeypatch
):
    config, cache, _ = fixture(tmp_path, monkeypatch)
    root = tmp_path / "restored"
    for path in cache.rglob("*.pddl"):
        target = root / "public-pddl" / path.relative_to(cache)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    prepare.restore_inputs(config, root)
    task = json.loads((root / "tasks.json").read_text())[0]
    original = prepare.semantic_fingerprint(task)
    task["model"]["atoms"].reverse()
    task["actions"].reverse()
    for action in task["actions"]:
        action["pre"].reverse()
        action["add"].reverse()
        action["delete"].reverse()
    assert prepare.semantic_fingerprint(task) == original
    task["nominal_states"][0].append("holding")
    assert prepare.semantic_fingerprint(task) != original


def test_source_paths_are_relative_and_reads_are_bounded(tmp_path, monkeypatch):
    config, _, _ = fixture(tmp_path, monkeypatch)
    value = json.loads(config.read_text())
    value["input_tasks"][0]["paths"]["domain"] = "../escape.pddl"
    config.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="relative"):
        prepare.restore_inputs(config, tmp_path / "restored")
    oversized = b"x" * (prepare.MAX_SOURCE_BYTES + 1)
    monkeypatch.setattr(prepare, "_fetch_source", lambda _: oversized)
    with pytest.raises(ValueError, match="SHA-256/size"):
        prepare._source(
            tmp_path / "oversized",
            Path("source.pddl"),
            hashlib.sha256(oversized).hexdigest(),
            [],
        )
