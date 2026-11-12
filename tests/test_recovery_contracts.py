"""Known-valid/invalid evidence for each reusable obligation, without fits."""

import json
import runpy
import tarfile
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from dual_rec.contracts.analysis import wilson
from dual_rec.contracts.checks import AuditBundle, audit, check_prefix

FIXTURES = Path("tests/fixtures/recovery_contracts")
VALID = json.loads((FIXTURES / "valid.json").read_text())
INVALID = json.loads((FIXTURES / "invalid.json").read_text())


@pytest.mark.parametrize("name", list(INVALID))
def test_known_valid_and_invalid_obligations(name):
    good = {r.check: r for r in audit(AuditBundle.model_validate(VALID))}
    bad = {r.check: r for r in audit(AuditBundle.model_validate(INVALID[name]))}
    assert good[name].status == "PASS"
    assert bad[name].status == "FAIL"


def test_missing_evidence_remains_unknown():
    assert all(r.status == "UNKNOWN" for r in audit(AuditBundle()))


def test_zero_events_do_not_imply_population_equivalence():
    assert wilson(0, 5)[1] == pytest.approx(0.43448246478317476)
    assert wilson(0, 57)[1] > 0.06
    assert wilson(0, 0) is None


def test_unavailable_pre_onset_prefix_is_explicit_and_keeps_the_record():
    data = json.loads(json.dumps(VALID))
    calibration = data["calibration"]
    missing = calibration["prefix_ids"].pop()
    calibration["prefix_stop"].pop(missing)
    calibration["unavailable_prefixes"] = {missing: "No observed pre-onset sample"}
    results = {r.check: r for r in audit(AuditBundle.model_validate(data))}
    assert results["independent_calibration"].status == "PASS"
    assert missing in {r["record_id"] for r in data["recordings"]}
    calibration["unavailable_prefixes"][missing] = ""
    results = {r.check: r for r in audit(AuditBundle.model_validate(data))}
    assert results["independent_calibration"].status == "FAIL"


def test_group_separation_follows_the_declared_generalization_claim():
    data = json.loads(json.dumps(VALID))
    for row in data["recordings"]:
        row["task_group"] = "one-shared-task"
    results = {r.check: r for r in audit(AuditBundle.model_validate(data))}
    assert results["group_separation"].status == "FAIL"
    data["separation_units"] = ["source"]
    results = {r.check: r for r in audit(AuditBundle.model_validate(data))}
    assert results["group_separation"].status == "PASS"
    with pytest.raises(ValidationError):
        AuditBundle.model_validate({"separation_units": []})


def test_prefix_perturbation_exposes_whole_episode_normalization():
    before = np.array([1.0, 2.0, 3.0, 4.0])
    after = np.array([1.0, 2.0, 30.0, 40.0])
    assert (
        check_prefix(lambda x: np.r_[0, np.diff(x)], before, after, 2).status == "PASS"
    )
    assert check_prefix(lambda x: x - x.mean(), before, after, 2).status == "FAIL"
    assert check_prefix(lambda x: x, before, after + 1, 2).status == "UNKNOWN"


def test_typed_boundary_does_not_accept_hidden_annotation_fields():
    with pytest.raises(ValidationError):
        AuditBundle.model_validate({"unreported_onset": 1})


def test_censoring_is_explicit_and_not_physical_relabeling():
    d = {
        "events": [
            {
                "record_id": "censored",
                "start": 0,
                "end": 1,
                "onset": 1.1,
                "semantics": "retrospective_deviation",
                "claimed_semantics": "retrospective_deviation",
                "censored": True,
            }
        ]
    }
    assert (
        next(
            r for r in audit(AuditBundle.model_validate(d)) if r.check == "event_bounds"
        ).status
        == "PASS"
    )
    d["events"][0]["excluded"] = True
    assert (
        next(
            r for r in audit(AuditBundle.model_validate(d)) if r.check == "event_bounds"
        ).status
        == "FAIL"
    )


def test_clean_seed_cannot_certify_original_scene_identity():
    d = {"simulator": {**VALID["simulator"], "reference_kind": "clean_seed"}}
    assert (
        next(
            r
            for r in audit(AuditBundle.model_validate(d))
            if r.check == "simulator_identity"
        ).status
        == "UNKNOWN"
    )


def test_missing_required_event_is_unknown_not_a_valid_localization_target():
    event = {**VALID["events"][0], "onset": None, "semantics": "unknown"}
    checks = {
        r.check: r for r in audit(AuditBundle.model_validate({"events": [event]}))
    }
    assert checks["event_bounds"].status == "UNKNOWN"
    assert checks["event_semantics"].status == "UNKNOWN"


def test_randomized_physical_trials_need_assignment_provenance_not_identical_states():
    pair = {
        **VALID["branches"][0],
        "assignment": "randomized",
        "state_hashes": ["a", "b"],
    }
    results = {
        r.check: r for r in audit(AuditBundle.model_validate({"branches": [pair]}))
    }
    assert results["intervention_effect"].status == "FAIL"
    pair["randomization_provenance"] = "toy fixture: seeded assignment before outcomes"
    results = {
        r.check: r for r in audit(AuditBundle.model_validate({"branches": [pair]}))
    }
    assert results["intervention_effect"].status == "PASS"


def test_review_archive_excludes_borrowed_raw_inputs_and_weights(tmp_path, monkeypatch):
    finalize = runpy.run_path("scripts/recovery_contracts_finalize.py")
    monkeypatch.chdir(tmp_path)
    root = Path("run")
    (root / "literature").mkdir(parents=True)
    (root / "literature/inspection_manifest.json").write_text("{}")
    (root / "predictions.json").write_text('{"verified": true}')
    (root / "model.pt").write_bytes(b"checkpoint kept outside review archive")
    old = Path("old_data")
    old.mkdir()
    (old / "private_raw.npz").write_bytes(b"borrowed input")
    (root / "data").symlink_to(old.resolve(), target_is_directory=True)
    report = Path("report.md")
    report.write_text("Review scope")
    finalize["archive"].__globals__["maintained"] = lambda: [report]
    finalize["archive"](root)
    with tarfile.open(root / "supervisor_review.tar.gz") as archive:
        names = archive.getnames()
        assert "evidence/predictions.json" in names and "maintained/report.md" in names
        assert not any("private_raw" in name or name.endswith(".pt") for name in names)
        assert archive.extractfile("maintained/report.md").read() == b"Review scope"
