"""Qualification never promotes diagnostic compatibility to a method gate."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from dual_rec.recoverbench.qualification import (
    EngineeringEvidence,
    array_differences,
    canonical_xml,
    engineering_decision,
)


def test_xml_path_normalization_preserves_contact_settings():
    left = '<mujoco><asset><mesh file="/old/robosuite/assets/a.stl"/></asset><geom friction="1 0.1 0.01"/></mujoco>'
    relocated = left.replace("/old/", "/new/")
    assert canonical_xml(left) == canonical_xml(relocated)
    assert canonical_xml(left) != canonical_xml(
        left.replace('friction="1 ', 'friction="2 ')
    )


def test_compiled_comparison_detects_physics_even_with_matching_shapes():
    left = {"geom_friction": np.array([[1, 0.1, 0.01]]), "body_mass": np.ones(2)}
    right = {"geom_friction": np.array([[2, 0.1, 0.01]]), "body_mass": np.ones(2)}
    assert set(array_differences(left, right)) == {"geom_friction"}
    assert (
        array_differences(left, {"body_mass": np.ones(3)})["body_mass"]["reason"]
        == "shape"
    )


def test_gate_requires_qualified_independent_generation():
    fields = {
        "qualified_model": True,
        "source_semantics_identified": True,
        "official_generation_works": True,
        "independently_successful_scenes": 4,
        "distinct_recovery_trajectories": 2,
        "leakage_or_hidden_reset": False,
        "diagnostic_execution_works": True,
    }
    assert engineering_decision(EngineeringEvidence(**fields)) == "ENGINEERING_GO"
    for name, value in (
        ("qualified_model", False),
        ("official_generation_works", False),
        ("independently_successful_scenes", 3),
        ("distinct_recovery_trajectories", 1),
        ("leakage_or_hidden_reset", True),
    ):
        assert (
            engineering_decision(EngineeringEvidence(**(fields | {name: value})))
            != "ENGINEERING_GO"
        )
    assert (
        engineering_decision(
            EngineeringEvidence(**(fields | {"qualified_model": False}))
        )
        == "INCONCLUSIVE"
    )
    with pytest.raises(ValueError):
        EngineeringEvidence(**(fields | {"independently_successful_scenes": 9}))


def test_budget_and_reused_symlink_inputs(tmp_path):
    pytest.importorskip(
        "psutil", reason="Budget driver runs in the root Python environment"
    )
    spec = importlib.util.spec_from_file_location(
        "qualification_command",
        Path(__file__).parents[1] / "scripts/recoverbench_qualification_command.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    existing = tmp_path / "old"
    existing.mkdir()
    (existing / "input.npz").write_bytes(b"old")
    root = tmp_path / "new"
    root.mkdir()
    (root / "inputs").symlink_to(existing, target_is_directory=True)
    (root / "new.json").write_bytes(b"new")
    assert module.new_files(root) == [root / "new.json"]
    rows = [{"wall_seconds": 17999, "cpu_seconds": 0}]
    assert (
        module.budget_reason(rows, wall=1, cpu=0, size=0)
        == "aggregate_worker_wall_budget"
    )
    assert module.budget_reason([], wall=0, cpu=21600, size=0) == "CPU_budget"
    assert (
        module.budget_reason([], wall=0, cpu=0, size=3_950_000_000)
        == "new_artifact_budget"
    )
    environment = module.worker_environment(root)
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["TMPDIR"] == str(root.resolve() / "cache/tmp")
    assert environment["PYTEST_ADDOPTS"].endswith(
        "-o cache_dir=" + str(root.resolve() / "cache/pytest")
    )


def test_frozen_source_membership_and_generator_scene_separation():
    import json

    registration = json.loads(
        Path("config/recoverbench_qualification_20261111.json").read_text()
    )
    sources = registration["sources"]
    for task in ("stack", "pick_place"):
        selected = [s for s in sources if s["task"] == task]
        assert len(selected) == 6
        assert len({(s["error"], s["degree"]) for s in selected}) == 6
    assert len(registration["generator_scenes"]) == 8
    assert not {s["scene_id"] for s in sources} & {
        s["scene_id"] for s in registration["generator_scenes"]
    }
