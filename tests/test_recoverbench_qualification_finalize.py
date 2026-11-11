"""Protect cumulative findings and the immutability of closed rescue evidence."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rescue_finalize",
    Path(__file__).parents[1] / "scripts/recoverbench_qualification_finalize.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preservation_allows_append_but_rejects_rewritten_findings():
    MODULE.require_original_prefix(
        b"previous negative\nnew evidence\n", b"previous negative\n"
    )
    with pytest.raises(ValueError, match="rewritten"):
        MODULE.require_original_prefix(
            b"previous positive\nnew evidence\n", b"previous negative\n"
        )


def test_sealed_evidence_rejects_further_work(tmp_path):
    MODULE.require_unsealed(tmp_path)
    (tmp_path / "completion_manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="sealed"):
        MODULE.require_unsealed(tmp_path)
