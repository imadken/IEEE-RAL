"""Seal all new evidence and package exact, restorable campaign traces."""

import gzip
import io
import json
import os
import tarfile
import time
from pathlib import Path

from dsre_last_common import ROOT, read, save, sha


def main():
    assert read(ROOT / "independent_final_audit.json")["passed"]
    assert read(ROOT / "independent_historical_pick_audit.json")["passed"]
    assert read(ROOT / "independent_historical_navigation_audit.json")["passed"]
    assert read(ROOT / "independent_historical_paired_audit.json")["passed"]
    assert not any(p.name.endswith(".partial") for p in ROOT.rglob("*"))
    seal = ROOT / "raw_evidence_seal.json"
    inventory = {
        str(p): sha(p) for p in sorted(ROOT.rglob("*")) if p.is_file() and p != seal
    }
    save(
        seal,
        {
            "epoch": time.time(),
            "files": len(inventory),
            "sha256": inventory,
            "scope": "Complete final-campaign evidence, including every new raw native trace losslessly stored with exact original gzip reconstruction; excludes self and later closure receipts. Historical files remain under unchanged original seals.",
        },
    )
    included = set()
    for base in ("src", "scripts", "tests"):
        included.update(
            p for p in Path(base).rglob("*.py") if "__pycache__" not in p.parts
        )
    included.update(p for p in ROOT.rglob("*") if p.is_file())
    included.update(Path("docs").glob("DSRE_FINAL_*.md"))
    included.add(Path("docs/DSRE_RSS2027_FINAL_SUPERVISOR_DECISION_20261118.md"))
    included.update(Path("research/dsre_final_science/figures").glob("*"))
    included.update(
        [
            Path("research/dsre_final_science/supervisor_oracle.py"),
            Path("research/dsre_evidence_design/supervisor_reference.py"),
        ]
    )
    for name in ("pyproject.toml", "uv.lock", "README.md", "AGENTS.md"):
        included.add(Path(name))
    # Full raw paired historical set used by E1; the old full prospective
    # trajectories remain local, with their independently repeated audits.
    catalog = Path("results/dsre-rss2027/20261113T193554Z/fresh_qualified.jsonl")
    included.add(catalog)
    included.update(
        Path(json.loads(line)["source"])
        for line in catalog.read_text().splitlines()
        if line
    )
    included.add(
        Path(
            "results/dsre-operational/20261116T193049Z-dual-obligation/calibration_rows.json.gz"
        )
    )
    for task in ("PickCube-v1", "PointMaze_UMaze-v3"):
        base = (
            Path("results/dsre-evidence-aware/20261117-prospective/prospective") / task
        )
        for sub in (
            "test",
            "evaluator",
            "models",
            "evaluations",
            "learner",
            "learner_records",
            "calibration",
            "discovery",
        ):
            included.update(p for p in (base / sub).rglob("*.json") if p.is_file())
    included.add(
        Path("results/dsre-evidence-aware/20261117-prospective/raw_evidence_seal.json")
    )
    included.add(
        Path("research/dsre_evidence_design/completion_review_receipt_20261118.json")
    )
    included.add(
        Path(
            "results/dsre-evidence-aware/20261118-source-eligibility/independent_source_reproductions.json"
        )
    )
    included.add(
        Path(
            "research/dsre_evidence_design/evidence_aware_completion_review_20261118.tar.gz"
        )
    )
    manifest = {
        "sha256": {str(p): sha(p) for p in sorted(included)},
        "scope": "Every final-campaign raw trace and metadata/code, all historical E1 paired trajectories and1280-row falsification input, complete Pick/navigation summary/model inputs, plus immutable prior compact bundle. Full older prospective raw physics is preserved locally and verified by the included full-audit reports; it is not falsely claimed all present in this compact bundle.",
    }
    target = Path("research/dsre_final_science/final_science_evidence_20261118.tar.gz")
    temporary = target.with_suffix(target.suffix + ".partial")
    assert not target.exists() and not temporary.exists()
    with (
        temporary.open("xb") as output,
        gzip.GzipFile(
            filename="", fileobj=output, mode="wb", mtime=0, compresslevel=6
        ) as compressed,
        tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar,
    ):
        for path in sorted(included):
            assert path.is_file() and not path.is_symlink()
            tar.add(path, arcname=str(path), recursive=False)
        payload = (json.dumps(manifest, indent=2) + "\n").encode()
        info = tarfile.TarInfo("FINAL_SCIENCE_MANIFEST.json")
        info.size = len(payload)
        info.mode = 0o644
        tar.addfile(info, io.BytesIO(payload))
    assert (
        temporary.stat().st_size
        + sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
        < 4 * 1024**3
    )
    os.link(temporary, target)
    temporary.unlink()
    print(
        json.dumps(
            {
                "path": str(target),
                "sha256": sha(target),
                "bytes": target.stat().st_size,
                "members": len(included) + 1,
                "raw_seal_sha256": sha(seal),
            }
        )
    )


if __name__ == "__main__":
    main()
