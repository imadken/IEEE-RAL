"""Seal local raw evidence and create a compact, independently verifiable bundle."""

import argparse
import gzip
import io
import json
import re
import tarfile
import time
from pathlib import Path

from dsre_evidence_prospective import OLD, ROOT, read

from dual_rec.evidence_aware.views import save, sha


def package(root):
    assert (root / "prospective_summary.json").exists()
    files = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.name
        not in (
            "raw_evidence_seal.json",
            "compact_receipt.json",
            "local_commit_receipt.json",
        )
    ]
    hashes = {str(p): sha(p) for p in sorted(files)}
    sealpath = root / "raw_evidence_seal.json"
    if sealpath.exists():
        previous = read(sealpath)
        for name, checksum in previous["sha256"].items():
            assert hashes.get(name) == checksum, f"Historical seal changed: {name}"
    else:
        save(
            sealpath,
            {
                "epoch": time.time(),
                "sha256": hashes,
                "files": len(hashes),
                "scope": "Complete local raw trajectories, assigned logs, access/model/source freezes, failure witnesses, independent audits and resource reports; excludes self and subsequent closure receipts.",
            },
        )
    included = {}
    for base in ("src", "scripts", "tests"):
        for path in Path(base).rglob("*.py"):
            if "__pycache__" not in path.parts:
                included[str(path)] = path
    for path in Path("docs").glob("DSRE_EVIDENCE_AWARE*.md"):
        included[str(path)] = path
    for name in ("DSRE_EVIDENCE_SPEC_V2.md", "DSRE_TASK_AND_EXECUTION_CONTRACT.md"):
        path = Path("docs") / name
        included[str(path)] = path
    path = Path("docs/DSRE_PROSPECTIVE_SOURCE_ELIGIBILITY_AND_COMPLETION_20261118.md")
    if path.exists():
        included[str(path)] = path
    for name in ("pyproject.toml", "uv.lock", "README.md", "AGENTS.md"):
        path = Path(name)
        if path.is_file():
            included[str(path)] = path
    for name in (
        "supervisor_reference.py",
        "supervisor_validation.json",
        "verify_prospective.py",
    ):
        path = Path("research/dsre_evidence_design") / name
        included[str(path)] = path
    for name in (
        "prospective_manifest.json",
        "prospective_ready_manifest.json",
        "navigation_requirements.txt",
    ):
        path = OLD / name
        if path.is_file():
            included[str(path)] = path
    for directory in ("learner", "paired_refinement", "evaluator"):
        for path in (OLD / "historical" / directory).glob("*.json"):
            included[str(path)] = path
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or "physics" in path.relative_to(root).parts
            or "navigation_env" in path.relative_to(root).parts
        ):
            continue
        if path.name in (
            "local_commit_receipt.json",
            "compact_receipt.json",
            "independent_compact_audit.json",
        ):
            continue
        included[str(path)] = path
    # Sampled physical branches, with failures always included.
    for directory in (root / "physics").glob("*/*/*"):
        specpath = directory / "spec.json"
        if not specpath.exists():
            continue
        spec = read(specpath)
        sample = spec["index"] == 0
        for path in directory.glob("*.execution.json"):
            included[str(path)] = path
        included[str(specpath)] = specpath
        for path in directory.glob("*.json.gz"):
            label = path.name.removesuffix(".json.gz")
            if not sample:
                marker = directory / (label + ".execution.json")
                if not marker.exists():
                    continue
                # Only status is selected here, after all execution/model freezes.
                with gzip.open(path, "rt") as f:
                    header = f.read(4096)
                    status = re.match(r'\{\s*"status"\s*:\s*"([A-Z_]+)"', header)
                    if status:
                        value = status.group(1)
                    else:
                        f.seek(0)
                        value = json.load(f)["status"]
                sample_failure = value not in ("COMPLETE", "CHECKPOINT_ONLY")
            else:
                sample_failure = False
            if sample or sample_failure:
                included[str(path)] = path
    manifest = {
        "sha256": {name: sha(path) for name, path in sorted(included.items())},
        "scope": "Complete model/data/count/source review; sampled physics plus every source failure; raw seal lists all every-parent trajectories retained locally.",
    }
    target = Path(
        "research/dsre_evidence_design/evidence_aware_prospective_review.tar.gz"
    )
    assert not target.exists()

    def add(tar, name, data):
        info = tarfile.TarInfo(name)
        info.size = len(data)
        info.mtime = 0
        info.mode = 0o644
        info.uid = info.gid = 0
        tar.addfile(info, io.BytesIO(data))

    with (
        target.open("xb") as output,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=output, mtime=0, compresslevel=6
        ) as gz,
        tarfile.open(fileobj=gz, mode="w") as tar,
    ):
        for name, path in sorted(included.items()):
            add(tar, name, path.read_bytes())
        add(
            tar,
            "COMPACT_MANIFEST.json",
            (json.dumps(manifest, indent=2) + "\n").encode(),
        )
    save(
        root / "compact_receipt.json",
        {
            "path": str(target),
            "sha256": sha(target),
            "bytes": target.stat().st_size,
            "members": len(included) + 1,
            "raw_seal_sha256": sha(root / "raw_evidence_seal.json"),
            "physics_scope": manifest["scope"],
        },
    )
    print(json.dumps(read(root / "compact_receipt.json")), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args()
    package(a.root)
