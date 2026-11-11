"""Closing checks enforce preservation, hard budgets and the sealed boundary."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "reboot_finalize",
    Path(__file__).resolve().parents[1] / "scripts/reboot_finalize.py",
)
finalize = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalize)


def test_historical_inventory_rejects_even_one_changed_byte(tmp_path):
    path = tmp_path / "old.json"
    path.write_bytes(b"old evidence\n")
    expected = {"old.json": hashlib.sha256(path.read_bytes()).hexdigest()}
    finalize.verify_inventory(tmp_path, expected)
    path.write_bytes(b"old evidence ")
    with pytest.raises(ValueError, match="Historical file changed"):
        finalize.verify_inventory(tmp_path, expected)


def test_historical_seal_accepts_recorded_symlinks_but_rejects_extra_files(tmp_path):
    (tmp_path / "original").write_bytes(b"evidence")
    (tmp_path / "alias").symlink_to("original")
    (tmp_path / "completion_manifest.json").write_text("{}")
    expected = {
        name: finalize.digest(tmp_path / name) for name in ("original", "alias")
    }
    finalize.verify_sealed_tree(tmp_path, expected)
    # A regular-file-only prior seal may omit its pytest symlink fixtures.
    finalize.verify_sealed_tree(tmp_path, {"original": expected["original"]})
    (tmp_path / "unexpected").write_text("new")
    with pytest.raises(ValueError, match="inventory changed"):
        finalize.verify_sealed_tree(tmp_path, expected)


@pytest.mark.parametrize(
    ("name", "limit"),
    [
        ("elapsed_campaign_wall_seconds", 28800),
        ("measured_cpu_seconds_with_closing", 36000),
        ("charged_cpu_seconds_upper_bound", 36000),
        ("gpu_wall_seconds", 7200),
        ("download_bytes_conservative_bound", 6_000_000_000),
        ("new_storage_conservative_bound_bytes", 10_000_000_000),
    ],
)
def test_each_resource_budget_is_hard(name, limit):
    resources = dict.fromkeys(
        [
            "elapsed_campaign_wall_seconds",
            "measured_cpu_seconds_with_closing",
            "charged_cpu_seconds_upper_bound",
            "gpu_wall_seconds",
            "download_bytes_conservative_bound",
            "new_storage_conservative_bound_bytes",
        ],
        0,
    )
    finalize.resource_limits(resources)
    with pytest.raises(ValueError, match=name):
        finalize.resource_limits(resources | {name: limit})


def test_completed_evidence_cannot_be_reopened(tmp_path):
    finalize.require_unsealed(tmp_path)
    (tmp_path / "completion_manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="sealed"):
        finalize.require_unsealed(tmp_path)


def test_failed_request_without_body_is_distinct_from_unhashed_saved_data(tmp_path):
    failed = {"error": "DNS unavailable", "path": "not-saved"}
    assert finalize.verify_downloads(tmp_path, [failed]) == 0
    with pytest.raises(ValueError, match="lacks an integrity hash"):
        finalize.verify_downloads(tmp_path, [failed | {"bytes": 5}])
    with pytest.raises(ValueError, match="lacks an integrity hash"):
        finalize.verify_downloads(tmp_path, [{"path": "not-saved"}])
