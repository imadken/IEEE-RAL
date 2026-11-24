"""Lossless storage of new traces with exact original gzip reconstruction."""

import gzip
import hashlib
import io
import json
import lzma
import os
import struct
import time
import zlib
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reconstruct(data, metadata):
    compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
    payload = compressor.compress(data)
    if metadata["sync_flush"]:
        payload += compressor.flush(zlib.Z_SYNC_FLUSH)
    payload += compressor.flush(zlib.Z_FINISH)
    result = (
        bytes.fromhex(metadata["header"]) + payload + bytes.fromhex(metadata["footer"])
    )
    assert digest(result) == metadata["original_gzip_sha256"]
    return result


def archive(path):
    path = Path(path)
    assert path.suffix == ".gz" and not path.is_symlink()
    started = time.time()
    original = path.read_bytes()
    data = gzip.decompress(original)
    position = 10
    flags = original[3]
    if flags & 4:
        position += 2 + struct.unpack("<H", original[position : position + 2])[0]
    for bit in (8, 16):
        if flags & bit:
            position = original.index(b"\0", position) + 1
    if flags & 2:
        position += 2
    metadata = {
        "original_gzip_sha256": digest(original),
        "decoded_sha256": digest(data),
        "header": original[:position].hex(),
        "footer": original[-8:].hex(),
        "zlib_version": zlib.ZLIB_RUNTIME_VERSION,
        "sync_flush": False,
        "original_gzip_bytes": len(original),
    }
    for sync in (False, True):
        metadata["sync_flush"] = sync
        try:
            rebuilt = reconstruct(data, metadata)
        except AssertionError:
            continue
        assert rebuilt == original
        break
    else:
        raise RuntimeError("Cannot reproduce original gzip bytes; original retained")
    compressed = lzma.compress(data, preset=6)
    assert lzma.decompress(compressed) == data
    metadata.update(
        xz_sha256=digest(compressed),
        xz_bytes=len(compressed),
        archive_wall_seconds=time.time() - started,
    )
    target = path.with_suffix(".xz")
    sidecar = Path(str(path) + ".archive.json")
    with target.open("xb") as handle:
        handle.write(compressed)
    with sidecar.open("x") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    assert digest(path.read_bytes()) == metadata["original_gzip_sha256"]
    path.unlink()
    return metadata


def restore(path):
    path = Path(path)
    if path.exists():
        return
    metadata = json.loads(Path(str(path) + ".archive.json").read_text())
    compressed = path.with_suffix(".xz").read_bytes()
    assert digest(compressed) == metadata["xz_sha256"]
    data = lzma.decompress(compressed)
    assert digest(data) == metadata["decoded_sha256"]
    original = reconstruct(data, metadata)
    temporary = path.with_name(path.name + f".restore-{os.getpid()}")
    with temporary.open("xb") as handle:
        handle.write(original)
    try:
        os.link(temporary, path)
    except FileExistsError:
        assert digest(path.read_bytes()) == metadata["original_gzip_sha256"]
    finally:
        temporary.unlink()


def read(path):
    path = Path(path)
    if path.suffix == ".gz":
        if path.exists():
            with gzip.open(path, "rt") as handle:
                return json.load(handle)
        metadata = json.loads(Path(str(path) + ".archive.json").read_text())
        compressed = path.with_suffix(".xz").read_bytes()
        assert digest(compressed) == metadata["xz_sha256"]
        data = lzma.decompress(compressed)
        assert digest(data) == metadata["decoded_sha256"]
        return json.load(io.BytesIO(data))
    return json.loads(path.read_text())
