import copy
import gzip
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from dual_rec.dsre.data import digest, qualify_pair

SOURCE = Path("results/recovery-claims/20261112T152155Z")
CELL = SOURCE / "parents/confirmation/PickCube-v1/103343-nominal"


@pytest.fixture(scope="module")
def physical_pair():
    if not CELL.exists():
        pytest.skip("Optional sealed local paired-physics evidence unavailable")
    with gzip.open(CELL / "traces.json.gz", "rt") as stream:
        raw = json.load(stream)
    return (
        raw,
        json.loads((CELL / "outcomes.json").read_text()),
        json.loads(Path("config/dsre_stage1.json").read_text()),
    )


def test_real_pair_sources_are_sealed_and_both_fresh_branches_qualify(physical_pair):
    raw, metadata, config = physical_pair
    manifest = json.loads((SOURCE / "completion_manifest.json").read_text())
    for name in ("outcomes.json", "traces.json.gz"):
        assert (
            digest(CELL / name)
            == manifest["sha256"][str((CELL / name).relative_to(SOURCE))]
        )
    assert set(qualify_pair(raw, metadata, config)) == {"continue", "recover"}


@pytest.mark.parametrize(
    "field", ["prefix_ok", "history_hash", "success", "state_errors"]
)
def test_corrupted_record_never_becomes_a_qualified_outcome(physical_pair, field):
    raw, metadata, config = physical_pair
    altered = copy.deepcopy(metadata)
    row = next(
        r for r in altered if r["action"] == "continue" and r["route"] == "fresh_prefix"
    )
    row[field] = {
        "prefix_ok": False,
        "history_hash": "wrong",
        "success": not row["success"],
        "state_errors": [2.0] * 70,
    }[field]
    with pytest.raises(ValueError):
        qualify_pair(raw, altered, config)


def test_missing_fresh_action_and_controller_memory_cannot_fall_back_to_snapshot(
    physical_pair,
):
    raw, metadata, config = physical_pair
    missing = [
        r
        for r in metadata
        if not (r["action"] == "recover" and r["route"] == "fresh_prefix")
    ]
    with pytest.raises(ValueError):
        qualify_pair(raw, missing, config)
    traces = raw["traces"] | {
        "continue/fresh_prefix": raw["traces"]["continue/fresh_prefix"]
        | {"controller_memory": {}}
    }
    with pytest.raises(ValueError):
        qualify_pair(raw | {"traces": traces}, metadata, config)
    traces = raw["traces"] | {
        "continue/fresh_prefix": raw["traces"]["continue/fresh_prefix"]
        | {"prefix_history": None}
    }
    with pytest.raises(ValueError):
        qualify_pair(raw | {"traces": traces}, metadata, config)


def test_parent_groups_and_folds_ignore_labels_and_condition_names():
    folds = runpy.run_path("scripts/dsre_experiment.py")["folds"]
    config = {"tasks": ["test"], "folds": 5, "fold_salt": "test/"}
    rows = [
        {
            "id": f"{seed}/{condition}",
            "task": "test",
            "group": f"test/{seed}",
            "outcomes": {"continue_value": True},
            "condition": condition,
        }
        for seed in range(20)
        for condition in ("nominal", "fault")
    ]
    expected = folds(rows, config)
    altered = [
        r | {"condition": "different", "outcomes": {"recover_value": False}}
        for r in reversed(rows)
    ]
    assert folds(altered, config) == expected
    assert len(expected) == 20
    assert set(expected.values()) == set(range(5))


def test_reproduction_finds_protocol_after_document_relocation(tmp_path, monkeypatch):
    locate = runpy.run_path("scripts/dsre_experiment.py")["protocol_path"]
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    moved = tmp_path / "docs/DSRE_STAGE1_PROTOCOL.md"
    moved.write_text("frozen protocol")
    assert locate().resolve() == moved
    original = tmp_path / "DSRE_STAGE1_PROTOCOL.md"
    original.write_text("frozen protocol")
    assert locate().resolve() == original


@pytest.mark.parametrize("script", ["dsre_audit.py", "dsre_verify_analysis.py"])
def test_audit_cli_refuses_to_mutate_a_sealed_run(tmp_path, script):
    seal = tmp_path / "completion_manifest.json"
    seal.write_text("{}\n")
    result = subprocess.run(
        [sys.executable, "scripts/" + script, "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0 and "Evidence sealed" in result.stderr
    assert list(tmp_path.iterdir()) == [seal]
