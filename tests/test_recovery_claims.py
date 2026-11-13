import pytest
from pydantic import ValidationError

from dual_rec.contracts.claims import Claim, certify, discordance_upper


def test_precision_and_missing_evidence():
    assert discordance_upper(0, 100, 0.005) > 0.05
    assert discordance_upper(0, 210, 0.005) < 0.025
    c = Claim(
        task="toy",
        parent="p",
        action="a",
        model_hash=None,
        history_hash="h",
        controller_hash="c",
        budget=2,
        actions=[[0.0], [0.0]],
        times=[0.05, 0.1],
        success=[False, True],
        state_errors=[0.0, 0.0],
    )
    assert certify(c)["status"] == "INSUFFICIENT_EVIDENCE"
    assert (
        certify(
            c.model_copy(
                update={"model_hash": "m", "contract_violation": "changed physics"}
            )
        )["status"]
        == "REFUTED_CONTRACT"
    )
    with pytest.raises(ValidationError):
        Claim(task="x", unobserved=1)


def test_wrong_budget_has_observed_witness():
    c = Claim(
        task="toy",
        parent="p",
        action="a",
        model_hash="m",
        history_hash="h",
        controller_hash="c",
        budget=3,
        actions=[[0.0], [0.0]],
        times=[0.05, 0.1],
        success=[False, True],
        state_errors=[0.0, 0.0],
    )
    assert certify(c)["witness"]["obligation"] == "budget"


def fixture_claim(**kwargs):
    values = {
        "task": "toy",
        "parent": "p",
        "action": "a",
        "model_hash": "m",
        "history_hash": "h",
        "controller_hash": "c",
        "reference_controller_hash": "c",
        "budget": 2,
        "actions": [[0.0], [0.0]],
        "times": [0.05, 0.1],
        "success": [False, True],
        "state_errors": [0.0, 0.0],
    }
    return Claim(**(values | kwargs))


def test_observed_controls_model_history_and_injection():
    for change, obligation in [
        ({"reference_model_hash": "other"}, "model_identity"),
        ({"reference_history_hash": "other"}, "history_identity"),
        ({"expected_actions": [[1.0], [0.0]]}, "first_wrong_control"),
        ({"state_injections": 1}, "state_injection"),
        ({"reference_controller_hash": "different"}, "controller_identity"),
    ]:
        assert certify(fixture_claim(**change))["witness"]["obligation"] == obligation


def test_finite_decision_fidelity_and_completion_never_override_bad_contract():
    c = fixture_claim(state_errors=[2.0, 2.0], qualification_parents=210)
    assert certify(c)["status"] == "SUPPORTED"
    assert certify(c, "B1")["status"] == "INSUFFICIENT_EVIDENCE"
    assert (
        certify(c.model_copy(update={"discordances": 50}))["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    c = fixture_claim(
        controller_hash=None,
        completion_qualified=True,
        completion_success=[False, True],
    )
    assert certify(c)["completed_with_prefix"]
    assert certify(c, "B4")["completed_with_prefix"]
    assert certify(c, "no_completion")["status"] == "INSUFFICIENT_EVIDENCE"
    assert (
        certify(c.model_copy(update={"model_hash": None}))["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert (
        certify(c.model_copy(update={"contract_violation": "wrong physics"}))["status"]
        == "REFUTED_CONTRACT"
    )


def test_unknown_ablation_is_explicitly_unsafe():
    c = fixture_claim(model_hash=None)
    assert certify(c)["status"] == "INSUFFICIENT_EVIDENCE"
    assert certify(c, "no_unknown")["status"] == "SUPPORTED"


def test_known_opaque_solver_state_does_not_supply_missing_provenance():
    c = fixture_claim(
        state_errors=[2.0, 2.0],
        qualification_parents=210,
        unobserved_state_fields=["hidden PhysX solver state"],
    )
    assert certify(c)["status"] == "SUPPORTED"
    assert certify(c)["F2_unobserved"] == ["hidden PhysX solver state"]
    assert (
        certify(c.model_copy(update={"controller_hash": None}))["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert certify(c, "B1")["status"] == "INSUFFICIENT_EVIDENCE"
    assert (
        certify(c.model_copy(update={"reference_controller_hash": None}))["status"]
        == "INSUFFICIENT_EVIDENCE"
    )


def test_exact_interval_nonzero_and_invalid_counts():
    from scipy.stats import beta

    for k, n in [(0, 100), (1, 100), (25, 100), (100, 100)]:
        expected = beta.ppf(0.995, k + 1, n - k) if k < n else 1
        assert discordance_upper(k, n) == pytest.approx(expected, abs=1e-10)
    with pytest.raises(ValueError):
        discordance_upper(5, 2)


def test_certificate_fresh_process_and_tamper(tmp_path):
    import json
    import os
    import subprocess
    import sys

    bundle = tmp_path / "bundle.json"
    output = tmp_path / "certificate.json"
    bundle.write_text(fixture_claim().model_dump_json())
    command = [
        sys.executable,
        "-m",
        "dual_rec.contracts.claims",
        "--bundle",
        str(bundle),
        "--output",
        str(output),
    ]
    env = os.environ | {"PYTHONPATH": "src"}
    subprocess.run(command, env=env, check=True, capture_output=True)
    subprocess.run(command + ["--verify"], env=env, check=True, capture_output=True)
    data = json.loads(output.read_text())
    data["status"] = "fabricated"
    output.write_text(json.dumps(data))
    assert (
        subprocess.run(
            command + ["--verify"], env=env, check=False, capture_output=True
        ).returncode
        != 0
    )


def test_matched_interventions_require_same_physical_history_and_budget():
    from dual_rec.contracts.claims import MatchedEvidence, matched_effect

    a = fixture_claim()
    b = fixture_claim(action="b")
    assert matched_effect(MatchedEvidence(branches=[a, b]))["status"] == "SUPPORTED"
    for field, value in [
        ("parent", "other"),
        ("history_hash", "other"),
        ("budget", 3),
        ("model_hash", "other"),
        ("controller_hash", "other"),
    ]:
        assert (
            matched_effect(
                MatchedEvidence(branches=[a, b.model_copy(update={field: value})])
            )["status"]
            == "REFUTED_CONTRACT"
        )


def test_review_archive_and_seal_detect_tampering(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    import recovery_claims_finalize as finalize

    payloads = {
        "initial.json": {"prior_files": {}},
        "historical_seal_hashes.json": {},
        "confirmation_freeze.json": {"source_sha256": {}},
        "secondary_source_hashes.json": {},
        "independent_audit.json": {"status": "PASS"},
    }
    for name, value in payloads.items():
        (tmp_path / name).write_text(json.dumps(value))
    monkeypatch.setattr(finalize, "maintained", list)
    finalize.archive(tmp_path)
    archive = tmp_path / "supervisor_review.tar.gz"
    manifest = {"sha256": {archive.name: finalize.sha(archive)}, "source_sha256": {}}
    (tmp_path / "completion_manifest.json").write_text(json.dumps(manifest))
    finalize.verify(tmp_path)
    archive.write_bytes(archive.read_bytes() + b"tampered")
    with pytest.raises(AssertionError):
        finalize.verify(tmp_path)


def test_independent_alarm_audit_uses_contiguous_observed_runs(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from recovery_claims_secondary_audit import alarm

    assert alarm([0, 0.05, 0.1, 0.15], [1, 1, 1, 1], 1) == 0.1
    assert alarm([0, 0.05, 0.1, 0.15], [1, None, 1, 1], 1) is None
    assert alarm([0, 0.05, 0.1], [1, 1, 1], 2) is None


def test_persisted_matched_claim_inputs_work_in_a_fresh_process(tmp_path, monkeypatch):
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from recovery_claims_secondary import persist_matched_inputs

    inputs = tmp_path / "certificates"
    inputs.mkdir()
    records = []
    for action in ["continue", "recover"]:
        path = inputs / (action + ".json")
        path.write_text(fixture_claim(action=action).model_dump_json())
        records.append(
            {
                "method": "M",
                "route": "fresh_prefix",
                "split": "confirmation",
                "task": "toy",
                "parent": "p",
                "condition": "nominal",
                "action": action,
                "bundle": str(path.relative_to(tmp_path)),
            }
        )
    index = persist_matched_inputs(tmp_path, records)
    assert len(index) == 1 and index[0]["status"] == "SUPPORTED"
    payload = json.loads((tmp_path / index[0]["bundle"]).read_text())
    assert len(payload["branches"]) == 2
    command = [
        sys.executable,
        "-m",
        "dual_rec.contracts.claims",
        "--bundle",
        str(tmp_path / index[0]["bundle"]),
        "--output",
        str(tmp_path / "fresh-paired-certificate.json"),
    ]
    subprocess.run(
        command, check=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"}
    )
    subprocess.run(
        command + ["--verify"],
        check=True,
        capture_output=True,
        env=os.environ | {"PYTHONPATH": "src"},
    )


def test_review_json_supports_numpy_scalar_counts(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    import numpy as np

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from recovery_claims_review import save

    target = tmp_path / "counts.json"
    save(target, {"count": np.int64(3)})
    assert json.loads(target.read_text()) == {"count": 3}
