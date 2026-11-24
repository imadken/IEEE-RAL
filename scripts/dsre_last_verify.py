"""Fresh-extraction reproduction of the final bundle; executes zero physics."""

import argparse
import gzip
import hashlib
import json
import lzma
import os
import subprocess
import sys
import tarfile
import tempfile
import time
import zlib
from pathlib import Path


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify(archive, output=None):
    started = time.time()
    origin = Path.cwd()
    archive = archive.resolve()
    root = Path(tempfile.mkdtemp(prefix="dsre-final-reproduction-", dir="/tmp"))
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(root, filter="data")
    manifest = read(root / "FINAL_SCIENCE_MANIFEST.json")
    for name, checksum in manifest["sha256"].items():
        assert sha(root / name) == checksum, name
    campaign = Path("results/dsre-evidence-aware/20261118-final-science")
    seal = read(root / campaign / "raw_evidence_seal.json")
    for name, checksum in seal["sha256"].items():
        assert sha(root / name) == checksum, name
    # Native libraries are the exact installed locked runtime; no simulator import
    # or execution is used by the extracted independent audit.
    (root / ".venv").symlink_to(origin / ".venv", target_is_directory=True)
    environment = dict(
        os.environ,
        PYTHONPATH="src:scripts:.",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    restored = 0
    original_bytes = archived_bytes = 0
    for path in sorted((root / campaign / "physics").rglob("*.json.gz.archive.json")):
        meta = read(path)
        xz = path.with_name(path.name.removesuffix(".gz.archive.json") + ".xz")
        compressed = xz.read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == meta["xz_sha256"]
        data = lzma.decompress(compressed)
        assert hashlib.sha256(data).hexdigest() == meta["decoded_sha256"]
        compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
        payload = compressor.compress(data)
        if meta["sync_flush"]:
            payload += compressor.flush(zlib.Z_SYNC_FLUSH)
        payload += compressor.flush(zlib.Z_FINISH)
        original = (
            bytes.fromhex(meta["header"]) + payload + bytes.fromhex(meta["footer"])
        )
        assert hashlib.sha256(original).hexdigest() == meta["original_gzip_sha256"]
        assert gzip.decompress(original) == data
        original_bytes += len(original)
        archived_bytes += len(compressed)
        restored += 1
    commands = [
        [
            "scripts/dsre_last_existing.py",
            "--output",
            "/tmp/" + root.name + "-existing.json",
        ],
        ["scripts/dsre_last_paired_history_audit.py"],
        [
            "scripts/dsre_last_audit.py",
            "--compact",
            "--output",
            "/tmp/" + root.name + "-audit.json",
        ],
    ]
    # The historical paired audit has an immutable output path; remove only the
    # extracted copy after its original manifest hash has already been verified.
    (root / campaign / "independent_historical_paired_audit.json").unlink()
    for i, args in enumerate(commands):
        with (root / f"reproduction-{i}.log").open("w") as log:
            result = subprocess.run(
                [sys.executable, *args],
                cwd=root,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode:
            raise RuntimeError(
                f"EXTRACTED_REPRODUCTION_FAILED:{root}/reproduction-{i}.log"
            )
    independent = read("/tmp/" + root.name + "-audit.json")
    original = read(root / campaign / "independent_final_audit.json")
    for key in (
        "phases",
        "policies",
        "four_cells",
        "physics_worker_seconds",
        "physics_processes",
        "paired_hindsight_completion",
        "equal_action_counts_vs_DSRE",
    ):
        assert independent[key] == original[key], key
    assert independent["production_inference_imported"] is False
    assert independent["historical_preservation_rechecked"] is False
    receipt = {
        "passed": True,
        "archive": str(archive.relative_to(origin)),
        "archive_sha256": sha(archive),
        "archive_bytes": archive.stat().st_size,
        "verified_manifest_files": len(manifest["sha256"]),
        "verified_new_seal_files": len(seal["sha256"]),
        "exactly_reconstructed_new_gzip_traces": restored,
        "original_gzip_bytes": original_bytes,
        "lossless_xz_bytes": archived_bytes,
        "compression_net_trace_saving_bytes": original_bytes - archived_bytes,
        "extraction_directory": str(root),
        "independent_numerical_physical_access_and_counts_reproduced": True,
        "mathematical_and_old_signature_checks_reproduced": True,
        "all_historical_E1_paired_trajectories_rechecked": True,
        "full_older_raw_preservation_scope": "Separately verified locally; not all older prospective raw traces are included in the compact bundle.",
        "physics_executed_by_verifier": False,
        "elapsed_seconds": time.time() - started,
        "verification_script_sha256": sha(__file__),
    }
    if output:
        with output.open("x") as f:
            json.dump(receipt, f, indent=2)
            f.write("\n")
    print(json.dumps(receipt), flush=True)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--archive",
        type=Path,
        default=Path(
            "research/dsre_final_science/final_science_evidence_20261118.tar.gz"
        ),
    )
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    verify(args.archive, args.output)
