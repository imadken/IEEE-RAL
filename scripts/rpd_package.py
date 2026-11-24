"""Compact source snapshots and scoped final preservation seals for RPD."""

import argparse
import hashlib
import io
import json
import lzma
import tarfile
import time
import zlib
from pathlib import Path

from rpd_reproduce import BASE, archive_check, sha


def bytes_for(path):
    path = Path(path)
    if path.exists():
        return path.read_bytes()
    assert path.suffix == ".gz"
    meta = json.loads(Path(str(path) + ".archive.json").read_text())
    compressed = path.with_suffix(".xz").read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == meta["xz_sha256"]
    raw = lzma.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == meta["decoded_sha256"]
    compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
    original = bytes.fromhex(meta["header"]) + compressor.compress(raw)
    if meta["sync_flush"]:
        original += compressor.flush(zlib.Z_SYNC_FLUSH)
    original += compressor.flush(zlib.Z_FINISH) + bytes.fromhex(meta["footer"])
    assert hashlib.sha256(original).hexdigest() == meta["original_gzip_sha256"]
    return original


def archive(path, files, expected=None):
    assert not path.exists(), path
    members = {}
    with tarfile.open(path, "x:xz") as stream:
        for name in sorted(set(map(str, files))):
            content = bytes_for(name)
            digest = hashlib.sha256(content).hexdigest()
            if expected and name in expected:
                assert expected[name] == digest, name
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o644
            member.mtime = 0
            stream.addfile(member, io.BytesIO(content))
            members[name] = digest
    archive_check(path, members)
    return members


def additions():
    files = list(Path("src/dual_rec/recoverability").glob("*.py")) + list(
        Path("scripts").glob("rpd_*.py")
    )
    files += [
        Path("tests/test_recoverability_planner.py"),
        Path("docs/RPD_METHODOLOGY_ORIGINALITY_CHALLENGE.md"),
    ]
    files += [
        p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    return sorted(set(files))


def source_bundle():
    source = json.loads((BASE / "final/source/source_and_adapters.json").read_text())
    expected = {**source["source_sha256"], **source["historical_source_input_sha256"]}
    files = list(expected) + [
        str(p) for p in Path("src/dual_rec/recoverability").glob("*.py")
    ]
    files += [str(p) for p in Path("scripts").glob("rpd_*.py")]
    files += [
        "src/dual_rec/__init__.py",
        "scripts/dsre_closure_common.py",
        "tests/test_recoverability_planner.py",
        "pyproject.toml",
        "uv.lock",
        str(BASE / "registration.json"),
    ]
    files += [str(p) for p in (BASE / "supervisor").iterdir() if p.is_file()]
    members = archive(BASE / "source_bundle.tar.xz", files, expected)
    (BASE / "source_bundle_manifest.json").write_text(
        json.dumps(
            {
                "archive_sha256": sha(BASE / "source_bundle.tar.xz"),
                "members": members,
                "scope": "Exact core/static-source/old D-C sensor dependencies; no published papers, manuscripts or hidden test trajectories",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "source_members": len(members),
                "bytes": (BASE / "source_bundle.tar.xz").stat().st_size,
            }
        )
    )


def seal():
    before = json.loads((BASE / "preservation_before.json").read_text())
    for group in ["files", "seals", "manuscripts"]:
        for name, digest in before[group].items():
            assert (
                (not Path(name).exists()) if digest is None else sha(name) == digest
            ), (group, name)
    freeze = json.loads((BASE / "final/code_freeze.json").read_text())
    assert all(sha(p) == h for p, h in freeze["code_sha256"].items())
    assert sha(BASE / "registration.json") == freeze["registration_sha256"]
    preserved = {g: len(before[g]) for g in ["files", "seals", "manuscripts"]}
    (BASE / "preservation_after.json").write_text(
        json.dumps(
            {
                "passed": True,
                "preserved": preserved,
                "base_commit": before["head"],
                "calendar_wall_seconds": time.time() - before["started_epoch"],
                "new_physics": 0,
                "manuscript_edits": 0,
            },
            indent=2,
        )
        + "\n"
    )
    exclude = {
        BASE / "compact_package.tar.xz",
        BASE / "compact_manifest.json",
        BASE / "integrity_manifest.json",
    }
    files = [p for p in additions() if p not in exclude]
    members = archive(BASE / "compact_package.tar.xz", files)
    (BASE / "compact_manifest.json").write_text(
        json.dumps(
            {
                "archive_sha256": sha(BASE / "compact_package.tar.xz"),
                "members": members,
            },
            indent=2,
        )
        + "\n"
    )
    inventory = [p for p in additions() if p != BASE / "integrity_manifest.json"]
    total = sum(p.stat().st_size for p in inventory)
    assert total < 100000000
    assert time.time() - before["started_epoch"] < 48 * 3600
    (BASE / "integrity_manifest.json").write_text(
        json.dumps(
            {
                "files": {str(p): sha(p) for p in inventory},
                "new_package_bytes": total,
                "base_commit": before["head"],
                "scope": "Only new RPD additions; manifest anchored by the local Git commit",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {"sealed_files": len(inventory), "bytes": total, "preserved": preserved}
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", action="store_true")
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    assert args.sources != args.seal
    source_bundle() if args.sources else seal()
