"""Sealing must reject changed or missing evidence."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "recoverbench_finalize",
    Path(__file__).parents[1] / "scripts/recoverbench_finalize.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_hash_verification_rejects_tampering_and_missing_files(tmp_path):
    evidence = tmp_path / "outcomes.jsonl"
    evidence.write_bytes(b"original")
    expected = {str(evidence): hashlib.sha256(b"original").hexdigest()}
    MODULE.verify_hashes(expected)
    evidence.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Preservation/hash failure"):
        MODULE.verify_hashes(expected)
    evidence.unlink()
    with pytest.raises(ValueError, match="Preservation/hash failure"):
        MODULE.verify_hashes(expected)
