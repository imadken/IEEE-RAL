"""Prospective interface and independent-calibration regression checks."""

import json
import os
import subprocess
import sys

import pytest
from dsre_evidence_prospective import identity, scope, vocabulary
from dsre_evidence_tasks import PEG_V2_VOCAB, peg_observation_v2

from dual_rec.evidence_aware.schema import Observation, OneAction
from dual_rec.evidence_aware.views import arm, seed


def test_peg_unknown_is_removed_from_eligible_grammar():
    telemetry = [True, False, True, False, None, True]
    assert peg_observation_v2(telemetry) == [True, False, True, False, True]
    assert telemetry[4] is None
    assert len(PEG_V2_VOCAB) == 5
    assert "aperture_below_source_threshold" not in PEG_V2_VOCAB
    with pytest.raises(ValueError, match="UNKNOWN"):
        peg_observation_v2([True] * 6)


def test_fresh_parent_identity_ignores_condition_and_phase_metadata():
    a = {
        "task": "PegInsertionSide-v1",
        "seed": 123,
        "offset": 0,
        "phase": "calibration",
    }
    assert identity(a) == identity(dict(a, offset=0.003, phase="test"))
    assert arm(a["task"], str(a["seed"])) in ("c", "r")
    assert seed(a["task"], "source-v2-qualification", 0) != seed(a["task"], "test", 0)


def test_endpoint_unknown_cannot_be_a_label():
    sc = scope("PegInsertionSide-v1")
    assert len(vocabulary(sc.task)) == 5
    kwargs = {
        "parent_id": "x",
        "x": [True] * 5,
        "action": "c",
        "propensity": 0.5,
        "controls": 0,
        "wall_seconds": 1,
        "source_scope": sc,
        "y": None,
    }
    with pytest.raises(ValueError):
        OneAction(**kwargs)
    with pytest.raises(ValueError):
        Observation(parent_id="x", x=[True] * 5, source_scope=sc, yr=True)


def test_guard_rejects_unselected_acquisition_label(tmp_path):
    allowed = tmp_path / "selected.json"
    hidden = tmp_path / "hidden.json"
    allowed.write_text(json.dumps({"y": True}))
    hidden.write_text(json.dumps({"yr": False}))
    code = """
import sys
from pathlib import Path
from dual_rec.evidence_aware.views import guard_data_access
root = Path(sys.argv[1]); permitted = root/'selected.json'
guard_data_access(root,[permitted])
assert permitted.read_text()
try:
    (root/'hidden.json').read_text()
except PermissionError:
    print('BLOCKED')
else:
    raise AssertionError('hidden counterpart accessible')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=True,
    )
    assert result.stdout.strip() == "BLOCKED"


def test_frozen_acquisition_model_can_only_read_its_own_labels(tmp_path):
    from dual_rec.evidence_aware.schema import Pair, Partition
    from dual_rec.evidence_aware.views import save

    out = tmp_path / "prospective/PointMaze_UMaze-v3"
    sc = scope("PointMaze_UMaze-v3")
    partition = Partition(
        vocabulary=vocabulary(sc.task),
        cells=(0,) * 64,
        tree=(-1, -1, -1),
        discovery_parents=("disjoint-discovery",),
    )
    save(
        out / "discovery_freeze.json",
        {
            "partition": partition.model_dump(mode="json"),
            "proposals": {"0": {"utility": True, "ensemble": True, "naive": True}},
        },
    )
    save(
        out / "acquisition_schedule.json",
        {
            "base_ids": ["a"],
            "schedules": {"all_pairs": {"64": [{"parent_id": "b", "kind": "pair"}]}},
        },
    )
    for pid, action, success in [("a", "c", False), ("b", "r", True)]:
        record = OneAction(
            parent_id=pid,
            x=[False] * 6,
            action=action,
            propensity=0.5,
            y=success,
            controls=200,
            wall_seconds=1,
            source_scope=sc,
        )
        save(
            out / "learner_records/calibration" / f"{pid}.json",
            record.model_dump(mode="json"),
        )
    pair = Pair(parent_id="b", x=[False] * 6, yc=False, yr=True, source_scope=sc)
    save(out / "paired_refinement/b.json", pair.model_dump(mode="json"))
    save(
        out / "acquisition_pairs/hidden.json",
        {"not_a_valid_pair": "must never be read"},
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/dsre_evidence_prospective_fit.py",
            "freeze_one",
            "--root",
            str(tmp_path),
            "--task",
            sc.task,
            "--model",
            "all_pairs_64",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    model = json.loads((out / "models/all_pairs_64.json").read_text())
    assert model["pair_parent_ids"] == ["b"]
    assert model["counts"]["calibration_logs"] == 2
    assert all("hidden.json" not in path for path in model["successful_data_reads"])


def test_expected_absorbing_prefix_is_distinct_from_a_hard_source_failure(tmp_path):
    from dsre_evidence_prospective import is_blocked, persist

    out = tmp_path / "prospective/PointMaze_UMaze-v3"
    persist(
        out / "SOURCE_GUARD_FAILURE.json",
        {"spec": {"seed": 7}, "stage": "screen", "status": "ALREADY_SOLVED_PREFIX"},
    )
    assert is_blocked(out)
    (tmp_path / "G2_absorbing_prefix_clarification.json").write_text("{}")
    assert not is_blocked(out)
    persist(
        out / "SOURCE_GUARD_FAILURE.json",
        {"spec": {"seed": 8}, "stage": "screen", "status": "MISSING_TERMINAL_OUTCOME"},
    )
    assert is_blocked(out)


def test_absorbing_prefix_preserves_observed_success_without_fabricating_a_log(
    tmp_path, monkeypatch
):
    import dsre_evidence_prospective as campaign

    from dual_rec.evidence_aware.views import save

    task = "PointMaze_UMaze-v3"
    spec = {
        "task": task,
        "phase": "calibration",
        "index": 9,
        "seed": 1078846034,
        "offset": [0, 0.35],
    }
    save(tmp_path / "registration.json", {"cohorts": {task: {"calibration": [spec]}}})
    save(tmp_path / "prospective" / task / "acquisition_schedule.json", {})
    monkeypatch.setattr(
        campaign,
        "bounded_child",
        lambda *args: {
            "status": "ALREADY_SOLVED_PREFIX",
            "features": None,
            "success": True,
        },
    )
    campaign.collect(tmp_path, task, "calibration", limit=1, only_index=9)
    pid = campaign.identity(spec)
    record = json.loads(
        (tmp_path / "prospective" / task / "calibration" / f"{pid}.json").read_text()
    )
    assert record["y"] is True and record["x"] is None
    assert record["valid_recovery_checkpoint"] is False
    assert "record" not in record
    assert not (
        tmp_path / "prospective" / task / "learner_records/calibration" / f"{pid}.json"
    ).exists()
    assert not campaign.is_blocked(tmp_path / "prospective" / task)


def test_missing_terminal_is_not_absorption_or_failure_imputation(
    tmp_path, monkeypatch
):
    import dsre_evidence_prospective as campaign

    from dual_rec.evidence_aware.views import save

    task = "PointMaze_UMaze-v3"
    spec = {
        "task": task,
        "phase": "calibration",
        "index": 0,
        "seed": 123,
        "offset": [0, 0],
    }
    save(tmp_path / "registration.json", {"cohorts": {task: {"calibration": [spec]}}})
    save(tmp_path / "prospective" / task / "acquisition_schedule.json", {})
    monkeypatch.setattr(
        campaign, "bounded_child", lambda *args: {"status": "MISSING_TERMINAL_OUTCOME"}
    )
    campaign.collect(tmp_path, task, "calibration", limit=1, only_index=0)
    record = json.loads(
        (
            tmp_path
            / "prospective"
            / task
            / "calibration"
            / f"{campaign.identity(spec)}.json"
        ).read_text()
    )
    assert record["y"] is None and "record" not in record
    assert campaign.is_blocked(tmp_path / "prospective" / task)
