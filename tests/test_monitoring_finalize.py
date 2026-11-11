"""Finalization refuses evidence drift and counts dependency hardlinks once."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "monitoring_finalize",
    Path(__file__).resolve().parents[1] / "scripts/monitoring_finalize.py",
)
finalizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalizer)


def test_preservation_detects_mutation_and_missing_files(tmp_path):
    path = tmp_path / "record"
    path.write_text("negative evidence")
    hashes = {str(path): finalizer.digest(path)}
    assert finalizer.verify_hashes(hashes) == 1
    path.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        finalizer.verify_hashes(hashes)
    path.unlink()
    with pytest.raises(ValueError, match="changed"):
        finalizer.verify_hashes(hashes)


def test_artifact_usage_deduplicates_hardlinked_environment_cache(tmp_path):
    a, b = tmp_path / "env", tmp_path / "cache"
    a.mkdir()
    b.mkdir()
    (a / "package").write_bytes(b"x" * 100)
    (b / "package").hardlink_to(a / "package")
    usage = finalizer.unique_bytes([a, b])
    assert usage["unique_file_inodes"] == 1
    assert usage["unique_logical_bytes_before_seal"] == 100


def test_finalize_never_reopens_sealed_run(tmp_path):
    (tmp_path / "completion_manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="already sealed"):
        finalizer.finalize(tmp_path, tmp_path / "report")
