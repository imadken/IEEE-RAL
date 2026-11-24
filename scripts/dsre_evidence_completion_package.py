"""Seal follow-up evidence and preserve the prior verified bundle unchanged."""

import gzip
import hashlib
import io
import json
import os
import tarfile
import time
from pathlib import Path

ROOT = Path("results/dsre-evidence-aware/20261118-source-eligibility")
OLD = Path("results/dsre-evidence-aware/20261117-prospective")


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def save(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main():
    assert json.loads((ROOT / "independent_followup_audit.json").read_text())["passed"]
    assert json.loads(
        (ROOT / "legacy_navigation_independent_full_audit.json").read_text()
    )["passed"]
    assert json.loads(
        (ROOT / "legacy_pickcube_independent_full_audit.json").read_text()
    )["passed"]
    inventory = {
        str(p): sha(p)
        for p in sorted(ROOT.rglob("*"))
        if p.is_file()
        and p.name
        not in (
            "raw_evidence_completion_seal.json",
            "completion_compact_receipt.json",
            "completion_verification_receipt.json",
            "final_commit_receipt.json",
        )
    }
    seal = ROOT / "raw_evidence_completion_seal.json"
    value = {
        "epoch": time.time(),
        "sha256": inventory,
        "files": len(inventory),
        "historical_full_raw_seal_sha256": sha(OLD / "raw_evidence_seal.json"),
        "scope": "All follow-up regular files and old explicit file references; historical discovery directory link is covered by the unchanged full prior seal. Excludes self and subsequent closure receipts.",
    }
    if seal.exists():
        for name, checksum in json.loads(seal.read_text())["sha256"].items():
            assert sha(Path(name)) == checksum
    else:
        save(seal, value)
    included = {}
    for base in ("src", "scripts", "tests"):
        for path in Path(base).rglob("*.py"):
            if "__pycache__" not in path.parts:
                included[str(path)] = path
    for path in Path("docs").glob("DSRE_EVIDENCE_AWARE*.md"):
        included[str(path)] = path
    for name in (
        "DSRE_EVIDENCE_SPEC_V2.md",
        "DSRE_TASK_AND_EXECUTION_CONTRACT.md",
        "DSRE_PROSPECTIVE_SOURCE_ELIGIBILITY_AND_COMPLETION_20261118.md",
    ):
        path = Path("docs") / name
        included[str(path)] = path
    for name in ("pyproject.toml", "uv.lock", "README.md", "AGENTS.md"):
        path = Path(name)
        included[str(path)] = path
    for name in (
        "supervisor_reference.py",
        "supervisor_validation.json",
        "verify_completion.py",
        "verify_prospective.py",
        "evidence_aware_prospective_review.tar.gz",
        "prospective_closure_20261118.json",
        "source_eligibility_amendment_20261118.json",
        "source_eligibility_proof_20261118.json",
        "source_eligibility_proof_20261118.tar.gz",
    ):
        path = Path("research/dsre_evidence_design") / name
        included[str(path)] = path
    for path in ROOT.rglob("*"):
        if not path.is_file() or "physics" in path.relative_to(ROOT).parts:
            continue
        if path.name in (
            "completion_compact_receipt.json",
            "completion_verification_receipt.json",
            "final_commit_receipt.json",
        ):
            continue
        included[str(path)] = path
    for directory in (ROOT / "physics").glob("*/*/*"):
        index = int(directory.name)
        for path in directory.iterdir():
            if not path.is_file():
                continue
            # Every new trace is included; old larger physical traces are sampled.
            if (
                not path.is_symlink()
                and not path.resolve().is_relative_to(OLD.resolve())
                or path.name.endswith(".execution.json")
                or path.name == "spec.json"
                or index in (0, 259, 364)
            ):
                included[str(path)] = path
    # Do not include the entire historical discovery tree through its directory link.
    for name in list(included):
        path = Path(name)
        if (
            "/physics/PegInsertionSide-v1/discovery/" in name
            and path.suffix == ".gz"
            and path.parent.name != "0"
        ):
            del included[name]
    manifest = {
        "sha256": {name: sha(path) for name, path in sorted(included.items())},
        "scope": "Every new source trace plus complete follow-up metadata/code, original verified legacy numerical bundle and old sampled physics. Every-parent older physics remains locally preserved under the unchanged original seal; full independent raw audits are included.",
    }
    target = Path(
        "research/dsre_evidence_design/evidence_aware_completion_review_20261118.tar.gz"
    )
    temporary = target.with_suffix(target.suffix + ".partial")
    assert not target.exists() and not temporary.exists()
    with (
        temporary.open("xb") as output,
        gzip.GzipFile(
            filename="", fileobj=output, mode="wb", mtime=0, compresslevel=6
        ) as gz,
        tarfile.open(fileobj=gz, mode="w") as tar,
    ):

        def add(name, data):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            item.mtime = 0
            item.mode = 0o644
            tar.addfile(item, io.BytesIO(data))

        for name, path in sorted(included.items()):
            add(name, path.read_bytes())
        add(
            "COMPLETION_MANIFEST.json", (json.dumps(manifest, indent=2) + "\n").encode()
        )
    os.link(temporary, target)
    temporary.unlink()
    receipt = {
        "path": str(target),
        "sha256": sha(target),
        "bytes": target.stat().st_size,
        "members": len(included) + 1,
        "raw_seal_sha256": sha(seal),
        "prior_raw_seal_sha256": sha(OLD / "raw_evidence_seal.json"),
        "scope": manifest["scope"],
    }
    save(ROOT / "completion_compact_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
