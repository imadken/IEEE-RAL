"""Read only requested columns of immutable public Parquets using bounded ranges."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

COLUMNS = [
    "action",
    "observation.state",
    "timestamp",
    "frame_index",
    "episode_index",
    "index",
    "task_index",
]
MAX_RANGE = 2_000_000
_LOGGER = logging.getLogger(__name__)


class ByteRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    total: int = Field(gt=0)

    def validate_response(self, header: str, count: int):
        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", header)
        if not match or tuple(map(int, match.groups())) != (
            self.start,
            self.end,
            self.total,
        ):
            raise ValueError("Server returned an unexpected Content-Range")
        if count != self.end - self.start + 1:
            raise ValueError("Incomplete byte-range response")


class TransferBudget:
    def __init__(self, root: Path, limit=6_000_000_000):
        self.root = root
        self.limit = limit
        self.lock = threading.Lock()
        self.cooldown_until = 0.0
        self.used = sum(
            r.get("bytes", 0)
            for r in [
                json.loads(s)
                for s in (root / "downloads.jsonl").read_text().splitlines()
            ]
        )

    def reserve(self, size):
        with self.lock:
            if time.time() < self.cooldown_until:
                raise ValueError("Rate-limit cooldown active; defer remaining files")
            if self.used + size > self.limit:
                raise ValueError("Initial download budget exhausted")
            self.used += size

    def cooldown(self, seconds):
        with self.lock:
            self.cooldown_until = max(self.cooldown_until, time.time() + seconds)

    def record(self, row):
        with self.lock, (self.root / "downloads.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")


class HTTPRangeFile(io.RawIOBase):
    def __init__(
        self, *, url, size, directory, root, budget, opener=urllib.request.urlopen
    ):
        super().__init__()
        self.url, self.size, self.position = url, size, 0
        self.directory, self.root, self.budget = directory, root, budget
        self.opener = opener
        self.records = []
        directory.mkdir(parents=True, exist_ok=True)

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = (
            offset
            if whence == 0
            else self.position + offset
            if whence == 1
            else self.size + offset
        )
        if not 0 <= position <= self.size:
            raise ValueError("Seek outside immutable object bounds")
        self.position = position
        return position

    def read(self, count=-1):
        count = (
            self.size - self.position
            if count < 0
            else min(count, self.size - self.position)
        )
        if count == 0:
            return b""
        if count > MAX_RANGE:
            raise ValueError("Refusing a large Parquet read; select bounded columns")
        start, end = self.position, self.position + count - 1
        requested = ByteRange(start=start, end=end, total=self.size)
        request = urllib.request.Request(
            self.url,
            headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
        )
        self.budget.reserve(count)
        try:
            with self.opener(request, timeout=45) as response:
                if response.status != 206:
                    raise ValueError(
                        "Server ignored Range; refusing an unbounded download"
                    )
                body = response.read(count + 1)
                requested.validate_response(
                    response.headers.get("Content-Range", ""), len(body)
                )
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry = (exc.headers or {}).get("Retry-After", "300")
                self.budget.cooldown(max(300, int(retry) if retry.isdigit() else 300))
            raise
        target = self.directory / f"range-{len(self.records):03d}-{start}-{end}.bin"
        target.write_bytes(body)
        row = {
            "url": self.url,
            "path": str(target.relative_to(self.root)),
            "start": start,
            "end": end,
            "total": self.size,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "http_status": 206,
            "content_range": f"bytes {start}-{end}/{self.size}",
        }
        self.records.append(row)
        self.budget.record(row)
        self.position += count
        return body


def project_one(root, repo, entry, budget):
    import pyarrow.parquet as pq

    name = repo["id"].split("/")[1]
    original = entry["path"]
    key = original.replace("/", "--").removesuffix(".parquet")
    parent = root / "ranges" / name / key
    attempt = len(list(parent.glob("attempt-*"))) if parent.exists() else 0
    directory = parent / f"attempt-{attempt:03d}"
    destination = root / "projected" / name / original
    if destination.exists():
        raise ValueError(f"Projection already exists: {destination}")
    url = f"https://huggingface.co/datasets/{repo['id']}/resolve/{repo['revision']}/{original}"
    source = HTTPRangeFile(
        url=url, size=entry["size"], directory=directory, root=root, budget=budget
    )
    parquet = pq.ParquetFile(source, pre_buffer=False, buffer_size=0)
    missing = set(COLUMNS) - set(parquet.schema_arrow.names)
    if missing:
        raise ValueError(f"Missing causal/index columns: {sorted(missing)}")
    table = parquet.read(columns=COLUMNS, use_threads=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, destination, compression="zstd")
    record = {
        "repository": repo["id"],
        "revision": repo["revision"],
        "original_path": original,
        "original_size": entry["size"],
        "original_lfs": entry.get("lfs"),
        "full_file_sha256_verified": False,
        "original_columns": parquet.schema_arrow.names,
        "rows": len(table),
        "columns": table.column_names,
        "projection": str(destination.relative_to(root)),
        "projection_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "ranges": source.records,
    }
    (directory / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--scope", choices=("probe", "all"), required=True)
    parser.add_argument("--retry-transient", action="store_true")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3, 4), default=4)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    registration = json.loads((root / "repository_registration.json").read_text())
    items = []
    for repo in registration["repositories"]:
        tree = json.loads(
            (root / "data" / repo["id"].split("/")[1] / "tree.json").read_text()
        )
        items.extend(
            (repo, entry)
            for entry in tree
            if entry["type"] == "file"
            and entry["path"].startswith("data/")
            and entry["path"].endswith(".parquet")
        )
    if args.scope == "probe":
        items = [
            next(x for x in items if x[0]["id"] == "REBOOT26/16mm-cylinder_install")
        ]
    else:
        items = [
            (repo, e)
            for repo, e in items
            if not (root / "projected" / repo["id"].split("/")[1] / e["path"]).exists()
        ]
    if args.retry_transient:
        previous = json.loads((root / "acquisition-all.json").read_text())
        eligible = {
            (e["repository"], e["path"])
            for e in previous["errors"]
            if "HTTPError" in e["error"] or "URLError" in e["error"]
        }
        items = [
            (repo, entry)
            for repo, entry in items
            if (repo["id"], entry["path"]) in eligible
        ]
    budget = TransferBudget(root)
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(project_one, root, repo, entry, budget): (repo, entry)
            for repo, entry in items
        }
        for future in as_completed(futures):
            repo, entry = futures[future]
            try:
                record = future.result()
                results.append(record)
            except Exception as exc:
                _LOGGER.exception("Retaining unsuccessful immutable-file projection")
                errors.append(
                    {
                        "repository": repo["id"],
                        "path": entry["path"],
                        "error": repr(exc),
                    }
                )
            if (len(results) + len(errors)) % 20 == 0 or len(items) == 1:
                print(
                    json.dumps(
                        {
                            "completed": len(results),
                            "errors": len(errors),
                            "total": len(items),
                            "reserved_download_bytes": budget.used,
                        }
                    ),
                    flush=True,
                )
    summary = {
        "scope": args.scope,
        "status": "PASS" if not errors else "PARTIAL",
        "completed_projections": len(results),
        "errors": errors,
        "reserved_total_download_bytes": budget.used,
    }
    target = root / f"acquisition-{args.scope}.json"
    if target.exists():
        target = (
            root
            / f"acquisition-{args.scope}-{len(list(root.glob('acquisition-' + args.scope + '*.json'))):02d}.json"
        )
    target.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
