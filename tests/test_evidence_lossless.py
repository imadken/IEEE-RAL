"""Verify exact byte recovery and fail-closed archive integrity."""

import gzip
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dsre_evidence_lossless import archive, read, restore


def test_archive_restores_exact_original_gzip(tmp_path):
    path = tmp_path / "trace.json.gz"
    value = {"status": "COMPLETE", "states": [[0.125, 4, True]] * 1000}
    with gzip.open(path, "xt", compresslevel=6) as handle:
        json.dump(value, handle)
    original = path.read_bytes()
    metadata = archive(path)
    assert not path.exists() and read(path) == value
    assert metadata["original_gzip_sha256"] == hashlib.sha256(original).hexdigest()
    restore(path)
    assert path.read_bytes() == original


def test_corruption_rejected_and_historical_links_preserved(tmp_path):
    path = tmp_path / "trace.json.gz"
    with gzip.open(path, "xt", compresslevel=6) as handle:
        json.dump({"x": [1, 2, 3]}, handle)
    link = tmp_path / "historical.json.gz"
    link.symlink_to(path)
    with pytest.raises(AssertionError):
        archive(link)
    assert path.exists()
    archive(path)
    path.with_suffix(".xz").write_bytes(b"corrupted")
    with pytest.raises(AssertionError):
        restore(path)
    assert not path.exists()
