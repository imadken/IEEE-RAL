"""The offline handoff must reproduce, while preserving already-written evidence."""

import json

import pytest
import rpd_isolation_handoff as handoff


def test_json_only_handoff_repeated_run_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(handoff, "BASE", tmp_path)
    monkeypatch.setattr(
        handoff, "technical_view", lambda: {"records": [{"history": ("probe",)}]}
    )
    handoff.report(json_only=True)
    before = (tmp_path / "technical_matches.json").read_bytes()
    handoff.report(json_only=True)
    assert (tmp_path / "technical_matches.json").read_bytes() == before
    assert json.loads(before)["records"][0]["history"] == ["probe"]


def test_changed_input_never_overwrites_an_existing_technical_receipt(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(handoff, "BASE", tmp_path)
    monkeypatch.setattr(handoff, "technical_view", lambda: {"source": "first"})
    handoff.report(json_only=True)
    before = (tmp_path / "technical_matches.json").read_bytes()
    monkeypatch.setattr(handoff, "technical_view", lambda: {"source": "changed"})
    with pytest.raises(AssertionError):
        handoff.report(json_only=True)
    assert (tmp_path / "technical_matches.json").read_bytes() == before
