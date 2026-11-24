"""Archive only consumed source evidence and explicit ERR additions."""

import argparse
import hashlib
import io
import json
import lzma
import subprocess
import tarfile
import time
import zlib
from pathlib import Path

from err_reproduce import BASE, sha, verify_archive


def original_bytes(path):
    path = Path(path)
    if path.exists():
        return path.read_bytes()
    assert path.suffix == ".gz", path
    meta = json.loads(Path(str(path) + ".archive.json").read_text())
    compressed = path.with_suffix(".xz").read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == meta["xz_sha256"]
    decoded = lzma.decompress(compressed)
    assert hashlib.sha256(decoded).hexdigest() == meta["decoded_sha256"]
    compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
    rebuilt = bytes.fromhex(meta["header"]) + compressor.compress(decoded)
    if meta["sync_flush"]:
        rebuilt += compressor.flush(zlib.Z_SYNC_FLUSH)
    rebuilt += compressor.flush(zlib.Z_FINISH) + bytes.fromhex(meta["footer"])
    assert hashlib.sha256(rebuilt).hexdigest() == meta["original_gzip_sha256"]
    return rebuilt


def archive(path, names, expected=None):
    assert not path.exists(), f"Refusing to overwrite archive {path}"
    members = {}
    with tarfile.open(path, "x:xz", preset=6) as stream:
        for name in sorted(set(map(str, names))):
            content = original_bytes(name)
            digest = hashlib.sha256(content).hexdigest()
            if expected and name in expected:
                assert digest == expected[name], name
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(content), 0o644, 0
            stream.addfile(member, io.BytesIO(content))
            members[name] = digest
    verify_archive(path, members)
    return members


def raw_source():
    robot = json.loads((BASE / "final/robot/robot_context_witnesses.json").read_text())
    inputs = robot["input_sha256"]
    files = list(inputs)
    files += [str(p) for p in Path("src").rglob("*.py")]
    files += [str(p) for p in Path("scripts").glob("err_*.py")]
    files += [
        "scripts/dsre_closure_common.py",
        "scripts/dsre_source_risk_audit.py",
        "tests/test_experiment_resolvability.py",
        "pyproject.toml",
        "uv.lock",
    ]
    files += [str(p) for p in (BASE / "supervisor").iterdir() if p.is_file()]
    files += [str(BASE / "registration.json")]
    members = archive(BASE / "raw_source.tar.xz", files, inputs)
    manifest = {
        "archive_sha256": sha(BASE / "raw_source.tar.xz"),
        "members": members,
        "original_consumed_evidence": inputs,
        "reconstructed_original_gzip": [p for p in inputs if not Path(p).exists()],
        "scope": "Consumed D/C evidence only, assigned branches only; no hidden test/evaluator source",
        "new_physics": 0,
    }
    (BASE / "raw_source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "members": len(members),
                "archive_bytes": (BASE / "raw_source.tar.xz").stat().st_size,
            }
        )
    )


def additions():
    result = [
        Path("src/dual_rec/evidence_aware") / name
        for name in (
            "experiment_schema.py",
            "experiment_resolvability.py",
            "evidence_resolution.py",
        )
    ]
    result += list(Path("scripts").glob("err_*.py"))
    result += [Path("tests/test_experiment_resolvability.py")]
    result += list(Path("docs").glob("ERR_*.md"))
    result += [
        p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    return sorted(set(result))


def seal():
    before = json.loads((BASE / "preservation_before.json").read_text())
    checked = {}
    for group in ("files", "seals", "manuscripts"):
        for name, digest in before[group].items():
            if digest is None:
                assert not Path(name).exists(), (
                    f"Originally deleted path reappeared: {name}"
                )
            else:
                assert sha(name) == digest, f"Preservation failure: {name}"
        checked[group] = len(before[group])
    late = json.loads((BASE / "late_user_input.json").read_text())
    # The user ZIP is preserved separately; its original receipt supplies the hash.
    user_zip = Path("DSRE_RSS2027_EVIDENCE_RESOLUTION_METHOD_PACKAGE_20261119.zip")
    assert sha(user_zip) in json.dumps(late)
    freeze = json.loads((BASE / "final/scientific_code_freeze.json").read_text())
    for name, digest in freeze["scientific_code_sha256"].items():
        assert sha(name) == digest, name
    assert sha(BASE / "registration.json") == freeze["registration_sha256"]
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    receipt = {
        "original_head": before["head"],
        "preserved": checked,
        "late_user_zip_sha256": sha(user_zip),
        "scientific_freeze_verified": True,
        "original_user_status": before["status"],
        "status_before_commit": status,
        "calendar_wall_seconds": time.time() - before["started_epoch"],
        "new_physics": 0,
        "new_robot_outcomes": 0,
        "manuscripts_and_original_figures_unchanged": True,
    }
    assert receipt["calendar_wall_seconds"] < 48 * 3600
    (BASE / "preservation_after.json").write_text(json.dumps(receipt, indent=2) + "\n")
    excluded = {
        BASE / "integrity_manifest.json",
        BASE / "compact_package.tar.xz",
        BASE / "compact_manifest.json",
    }
    files = [p for p in additions() if p not in excluded]
    assert sum(p.stat().st_size for p in files) < 500000000
    members = archive(BASE / "compact_package.tar.xz", files)
    (BASE / "compact_manifest.json").write_text(
        json.dumps(
            {
                "archive_sha256": sha(BASE / "compact_package.tar.xz"),
                "members": members,
                "scope": "All explicit ERR additions except self-referential manifests/archive; includes raw source archive",
            },
            indent=2,
        )
        + "\n"
    )
    inventory = [p for p in additions() if p != BASE / "integrity_manifest.json"]
    manifest = {
        "files": {str(p): sha(p) for p in inventory},
        "total_addition_bytes": sum(p.stat().st_size for p in inventory),
        "base_commit": before["head"],
        "scope": "Explicit ERR additions; no unrelated user changes",
        "self_exclusion": "This manifest is anchored by the local Git commit, avoiding a self-hash cycle",
    }
    assert manifest["total_addition_bytes"] < 500000000
    (BASE / "integrity_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "sealed_files": len(inventory),
                "bytes": manifest["total_addition_bytes"],
                "preserved": checked,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-source", action="store_true")
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    assert args.raw_source != args.seal, "Select one archive operation"
    raw_source() if args.raw_source else seal()
