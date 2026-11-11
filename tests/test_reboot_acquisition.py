"""Reject ambiguous or unbounded remote reads before any model sees the data."""

import io
import urllib.error
from typing import ClassVar

import pytest

from dual_rec.reboot.acquisition import (
    MAX_RANGE,
    ByteRange,
    HTTPRangeFile,
    TransferBudget,
)


def test_content_range_rejects_wrong_coordinates_or_truncated_data():
    requested = ByteRange(start=10, end=19, total=100)
    requested.validate_response("bytes 10-19/100", 10)
    with pytest.raises(ValueError, match="Content-Range"):
        requested.validate_response("bytes 0-9/100", 10)
    with pytest.raises(ValueError, match="Incomplete"):
        requested.validate_response("bytes 10-19/100", 9)


def test_range_file_records_exact_bytes_and_position(tmp_path):
    (tmp_path / "downloads.jsonl").write_text("")
    budget = TransferBudget(tmp_path, limit=100)

    class Response(io.BytesIO):
        status = 206
        headers: ClassVar[dict[str, str]] = {"Content-Range": "bytes 10-19/100"}

    def opener(request, timeout):
        assert request.headers["Range"] == "bytes=10-19"
        assert timeout == 45
        return Response(b"0123456789")

    source = HTTPRangeFile(
        url="https://example.invalid/file",
        size=100,
        directory=tmp_path / "ranges",
        root=tmp_path,
        budget=budget,
        opener=opener,
    )
    source.seek(10)
    assert source.read(10) == b"0123456789"
    assert source.tell() == 20 and budget.used == 10
    assert source.records[0]["bytes"] == 10
    with pytest.raises(ValueError, match="bounds"):
        source.seek(-1)


def test_ignored_ranges_never_read_the_large_response_body(tmp_path):
    (tmp_path / "downloads.jsonl").write_text("")

    class Response(io.BytesIO):
        status = 200

        def read(self, size=-1):
            raise AssertionError("Must reject status before consuming body")

    source = HTTPRangeFile(
        url="https://example.invalid/file",
        size=MAX_RANGE + 1,
        directory=tmp_path / "ranges",
        root=tmp_path,
        budget=TransferBudget(tmp_path),
        opener=lambda *a, **k: Response(),
    )
    with pytest.raises(ValueError, match="ignored Range"):
        source.read(10)
    with pytest.raises(ValueError, match="large Parquet read"):
        source.read()


def test_download_budget_is_enforced_before_network_requests(tmp_path):
    (tmp_path / "downloads.jsonl").write_text('{"bytes": 9}\n')
    budget = TransferBudget(tmp_path, limit=10)
    with pytest.raises(ValueError, match="budget"):
        budget.reserve(2)


@pytest.mark.parametrize("headers", [None, {"Retry-After": "5"}])
def test_rate_limit_defers_other_files_before_more_requests(tmp_path, headers):
    (tmp_path / "downloads.jsonl").write_text("")
    budget = TransferBudget(tmp_path)
    calls = []

    def opener(request, timeout):
        calls.append(request)
        raise urllib.error.HTTPError(
            request.full_url, 429, "Rate limited", headers, None
        )

    source = HTTPRangeFile(
        url="https://example.invalid/file",
        size=100,
        directory=tmp_path / "ranges",
        root=tmp_path,
        budget=budget,
        opener=opener,
    )
    with pytest.raises(urllib.error.HTTPError):
        source.read(10)
    with pytest.raises(ValueError, match="cooldown"):
        source.read(10)
    assert len(calls) == 1
