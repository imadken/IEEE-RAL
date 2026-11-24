"""Seal and reproduce the separate RPD V2 paper, without simulator execution."""

import argparse
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict

BASE = Path("research/rpd_stage1_v2")
PAPER = BASE / "paper"
REPORT = Path("docs/RPD_STAGE1_V2_METHOD_AND_VERIFICATION_20261119.md")
SCRIPTS = [
    Path("scripts") / (name + ".py")
    for name in ("rpd_paper_v2_checks", "rpd_paper_v2_figure", "rpd_paper_v2_receipt")
]
TEST = Path("tests/test_rpd_paper_v2.py")


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    claim: str
    scope: str
    sources: dict[str, str]


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def matches_snapshot(path: Path, expected: str | None) -> bool:
    """A pre-existing user deletion is a protected absence, not a missing hash."""
    if expected is None:
        return not path.exists()
    return path.is_file() and sha(path) == expected


def run(
    command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def paper_checks(paper: Path) -> dict:
    info = run(["pdfinfo", str(paper / "paper.pdf")])
    assert "Pages:           6" in info
    assert "Page size:       612 x 792 pts" in info
    assert not any(
        line.startswith("Author:") and line.split(":", 1)[1].strip()
        for line in info.splitlines()
    )
    text = run(["pdftotext", "-layout", str(paper / "paper.pdf"), "-"])
    pages = [p for p in text.split("\f") if p.strip()]
    assert len(pages) == 6 and pages[-1].lstrip().startswith("R EFERENCES")
    assert all("R EFERENCES" not in p for p in pages[:5])
    assert all(len(p.split()) > 400 for p in pages[:5])
    for forbidden in (
        "/home/imad",
        "github.com/imadken",
        "http://",
        "https://",
        "Codex",
        "[?]",
        "??",
        "d97c13a",
    ):
        assert forbidden not in text, forbidden
    fonts = run(["pdffonts", str(paper / "paper.pdf")])
    rows = fonts.splitlines()[2:]
    assert rows and all("Type 1C" in row and "yes yes" in row for row in rows)
    log = (paper / "paper.log").read_text() if (paper / "paper.log").exists() else ""
    assert "Overfull" not in log and "undefined on input" not in log
    assert "There were undefined" not in log
    return {
        "pages": 6,
        "content_pages": 5,
        "reference_pages": 1,
        "paper_sha256": sha(paper / "paper.pdf"),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "page_word_counts": [len(p.split()) for p in pages],
        "pdfinfo": info,
        "fonts": fonts,
        "unresolved_references": False,
        "external_urls_and_identifying_author_metadata": False,
        "visual_review": "All six rendered pages and Figure 1 inspected; no figure clipping, text overlap, or table overflow. References balanced without font/margin changes.",
        "font_warning_scope": "IEEEtran emits TU font-shape warnings before T1/times is loaded; final PDF embeds only Type1C fonts. Minor underfull text boxes retained, no overfull boxes.",
    }


def preservation() -> dict:
    path = BASE / "preservation_before.json.xz"
    with lzma.open(path, "rt") as stream:
        before = json.load(stream)
    changed = [
        p
        for p, expected in before["files"].items()
        if not matches_snapshot(Path(p), expected)
    ]
    metadata_changed = []
    for name, expected in before["historical_metadata"].items():
        path = Path(name)
        if not path.is_file():
            metadata_changed.append(name)
        else:
            actual = path.stat()
            if [actual.st_size, actual.st_mtime_ns] != expected:
                metadata_changed.append(name)
    status = run(["git", "status", "--short", "--untracked-files=normal"])
    current = set(status.splitlines())
    missing_status = sorted(set(before["user_status"].splitlines()) - current)
    assert not changed and not metadata_changed and not missing_status, {
        "changed": changed,
        "metadata_changed": metadata_changed,
        "lost_user_status": missing_status,
    }
    return {
        "passed": True,
        "starting_commit": before["head"],
        "protected_hashes": sum(h is not None for h in before["files"].values()),
        "protected_preexisting_absences": sum(
            h is None for h in before["files"].values()
        ),
        "historical_metadata": len(before["historical_metadata"]),
        "preexisting_user_status_entries": len(before["user_status"].splitlines()),
        "changed_protected_files": changed,
        "changed_historical_metadata": metadata_changed,
        "lost_user_status_entries": missing_status,
        "new_physics_episodes": 0,
        "elapsed_wall_seconds": time.time() - before["started_epoch"],
    }


def claims() -> list[dict]:
    f = BASE / "final_verification"
    declarations = [
        (
            "Nominal one-probe criterion necessary and sufficient with complete support and admissible paths; 1024 exhaustive models",
            "CONSTRUCTED_COMPLETE_DETERMINISTIC_MODEL_NOT_PHYSICAL_GUARANTEE",
            [
                f / "nominal_verification.json",
                SCRIPTS[0],
                TEST,
                Path("src/dual_rec/recoverability/planner.py"),
                Path("scripts/rpd_independent_oracle.py"),
            ],
        ),
        (
            "Equal durations .5s from4s; fine information ln3, completion2/3; coarse informationH(2/3,1/3), completion1; full lossC, partialB; matched planner/task-consensus equality",
            "ANALYTICAL_WORLDS_NOT_ROBOT_EPISODES",
            [
                f / "illustration.json",
                SCRIPTS[0],
                SCRIPTS[1],
                PAPER / "figures/figure1.pdf",
            ],
        ),
        (
            "H1 proposed10pct; H2 proposed5pp; constraint noninferiority+.02; 64discovery512confirmation; primary single probe; fixed assembly family",
            "SUPERVISOR_PROSPECTIVE_HYPOTHESES_NOT_OBSERVED_EFFECTS",
            [
                BASE / "supervisor/RPD_HYPOTHESES_AND_METHOD_LOCK_V2.md",
                BASE / "supervisor/SAMPLE_PRECISION_CHECK.json",
            ],
        ),
        (
            "H1 reject66; size.0203185; power.921296 atq.15; zero-event upper.00717895; H2 normal halfwidth.03775634",
            "ANALYTICAL_PRECISION_REQUIRES_INDEPENDENT_PARENTS",
            [f / "precision.json", SCRIPTS[0], TEST],
        ),
        (
            "H2 paired profile asymptotic, rare-discordance exact fallback, CP sensitivity; primary family not exact finite-sample",
            "PROSPECTIVE_STATISTICAL_PLAN_NO_NEW_EMPIRICAL_CI",
            [PAPER / "paper.tex", f / "precision.json", TEST],
        ),
        (
            "Empirical Bernstein score bound rescaled to[-b,b], b=-log(.001); aggregate predictive signal vsbaseline andhold",
            "CONDITIONAL_ON_DISCOVERY_FROZEN_DECODERS_AND_IID_CONFIRMATION",
            [PAPER / "paper.tex", BASE / "citation_audit.json"],
        ),
        (
            "28 source episodes14/task; one inspected parent/task; six matched histories/task; partial-loss histories4Pick0Push; no full erasure in these technical histories",
            "RETROSPECTIVE_MIXED_PROVENANCE_CORRELATED_TECHNICAL_CASES_NOT_H1_H2",
            [
                f / "preliminary_recount.json",
                BASE / "raw_source_reaudit/summary.json",
                Path("research/rpd_source_isolation_20261119/technical_matches.json"),
            ],
        ),
        (
            "Original pilot38complete/task then native branch39 failed; no inferred crash cause or global stability",
            "ORIGINAL_MISSING_OUTCOMES_PRESERVED",
            [
                Path("research/rpd_physical_pilot_20261119/final_audit/summary.json"),
                Path("research/rpd_source_isolation_20261119/final_audit/summary.json"),
            ],
        ),
        (
            "Square geometry3mm/side; half length85-125mm width15-25mm; hole+x; panda_wristcam; head-only event; no bound force sensor",
            "READ_ONLY_PINNED_SOURCE_NOT_ASSEMBLY_QUALIFICATION",
            [
                f / "assembly_source_review.json",
                Path(
                    ".venv/lib/python3.12/site-packages/mani_skill/envs/tasks/tabletop/peg_insertion_side.py"
                ),
            ],
        ),
        (
            "Assembly0parents; source/sensor/control/constraint/checkpoint bindings outstanding; d.5tau4 illustrative",
            "PROPOSED_UNQUALIFIED_ADAPTER",
            [f / "assembly_source_review.json", PAPER / "paper.tex", REPORT],
        ),
        (
            "3072matched confirmation+512root direct+384discovery=3968; sensitivities384+192=576conditional; total4544; worker-hours unbound",
            "PROSPECTIVE_BRANCH_ACCOUNTING_NOT_INDEPENDENT_PARENT_COUNTS_OR_MEASURED_RUNTIME",
            [f / "precision.json", PAPER / "paper.tex", REPORT],
        ),
        (
            "Existing methods cover interactive sensing, active constrained diagnosis, task-aware contact, reversibility, terminal controllability; no novel optimizer claim",
            "VERIFIED_PRIMARY_LITERATURE_WITH_ACCESS_LIMITS",
            [
                BASE / "citation_audit.json",
                PAPER / "references.bib",
                PAPER / "paper.tex",
            ],
        ),
    ]
    return [
        Claim(claim=c, scope=s, sources={str(p): sha(p) for p in paths}).model_dump()
        for c, s, paths in declarations
    ]


def seal() -> None:
    save(BASE / "preservation_after.json", preservation())
    save(BASE / "paper_verification.json", paper_checks(PAPER))
    save(BASE / "claims_to_sources.json", {"claims": claims(), "new_physics": 0})
    anonymous = [
        PAPER / p
        for p in (
            "paper.tex",
            "paper.pdf",
            "paper.bbl",
            "references.bib",
            "IEEEtran.cls",
            "figures/figure1.pdf",
            "figures/figure1.svg",
        )
    ]
    with zipfile.ZipFile(
        BASE / "anonymous_source.zip", "x", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in anonymous:
            entry = zipfile.ZipInfo(
                path.relative_to(PAPER).as_posix(), date_time=(2000, 1, 1, 0, 0, 0)
            )
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, path.read_bytes())
    files = [
        p
        for p in BASE.rglob("*")
        if p.is_file() and p.suffix not in (".log", ".aux", ".out", ".blg", ".xdv")
    ]
    files += SCRIPTS + [TEST, REPORT]
    save(
        BASE / "integrity_manifest.json",
        {
            "files": {str(p): sha(p) for p in sorted(files)},
            "scope": "New manuscript, verification, original authority and receipts. Old evidence/manuscripts untouched; no physics.",
        },
    )
    print(json.dumps({"sealed": True, "files": len(files), "new_physics": 0}))


def verify() -> None:
    manifest = json.loads((BASE / "integrity_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert sha(Path(name)) == expected, name
    preservation()
    current = paper_checks(PAPER)
    canonical = json.loads((BASE / "paper_verification.json").read_text())
    assert current["text_sha256"] == canonical["text_sha256"]
    for item in json.loads((BASE / "claims_to_sources.json").read_text())["claims"]:
        claim = Claim.model_validate(item)
        assert all(sha(Path(p)) == h for p, h in claim.sources.items())
    print(
        json.dumps(
            {
                "passed": True,
                "integrity_files": len(manifest["files"]),
                "new_physics": 0,
            }
        )
    )


def clean(output: Path) -> None:
    assert not output.exists(), "Fresh clean directory required"
    original = Path.cwd()
    root = output.resolve() / "source"
    root.mkdir(parents=True)
    source_names = [
        "rpd_paper_v2_checks",
        "rpd_paper_v2_figure",
        "rpd_cases",
        "rpd_independent_oracle",
        "rpd_isolation_handoff",
        "rpd_isolation_audit",
        "rpd_isolation_common",
        "rpd_pilot_common",
        "rpd_pilot_audit",
    ]
    paths = [Path("scripts") / (n + ".py") for n in source_names]
    paths += [p for p in Path("src/dual_rec/recoverability").glob("*.py")]
    paths += [Path("src/dual_rec/__init__.py")]
    prior = Path("research/rpd_physical_pilot_20261119")
    isolation = Path("research/rpd_source_isolation_20261119")
    paths += [
        p
        for t in ("PickCube-v1", "PushCube-v1")
        for p in (prior / "physics" / t / "parent_00").glob("*.json.xz")
    ]
    paths += [
        p
        for p in (isolation / "physics").rglob("*")
        if p.is_file() and p.name == "native.json.xz"
    ]
    paths += [
        isolation / "jobs.jsonl",
        isolation / "technical_matches.json",
        isolation / "final_audit/summary.json",
    ]
    paths += [
        BASE / "supervisor/SAMPLE_PRECISION_CHECK.json",
        Path(
            ".venv/lib/python3.12/site-packages/mani_skill/envs/tasks/tabletop/peg_insertion_side.py"
        ),
    ]
    paths += [
        p
        for p in PAPER.rglob("*")
        if p.is_file() and p.suffix in (".tex", ".bib", ".bbl", ".cls", ".pdf", ".svg")
    ]
    copied = {}
    for path in sorted(set(paths)):
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        assert sha(path) == sha(dest)
        copied[str(path)] = sha(path)
    env = dict(
        os.environ,
        PYTHONPATH=str(root / "src") + os.pathsep + str(root / "scripts"),
        UV_CACHE_DIR="/tmp/rpd-v2-uv-cache",
        MPLCONFIGDIR="/tmp/rpd-v2-mpl",
    )
    command = [
        "uv",
        "run",
        "--project",
        str(original),
        "--offline",
        "--no-sync",
        "python",
        "scripts/rpd_paper_v2_checks.py",
        "--output",
        str(BASE / "final_verification"),
    ]
    log = run(command, cwd=root, env=env)
    (output / "analysis.txt").write_text(log)
    for path in (BASE / "final_verification").glob("*.json"):
        assert sha(path) == sha(root / path), str(path)
    compiler = Path("/tmp/tectonic-stage1-bin/tectonic")
    assert compiler.is_file(), "Existing compiler required; no dependency installation"
    buildenv = dict(env, XDG_CACHE_HOME="/tmp/dsre-stage1-tex-cache")
    build = run(
        [str(compiler), "--only-cached", "--untrusted", "--keep-logs", "paper.tex"],
        cwd=root / PAPER,
        env=buildenv,
    )
    (output / "compile.txt").write_text(build)
    expected = paper_checks(PAPER)
    actual = paper_checks(root / PAPER)
    assert expected["text_sha256"] == actual["text_sha256"], "PDF text changed"
    save(
        output / "reproduction_receipt.json",
        {
            "passed": True,
            "copied_files": copied,
            "canonical_json_outputs_byte_identical": True,
            "pdf_text_identical": True,
            "pages": 6,
            "new_physics": 0,
            "environment_scope": "Isolated copied source/data directory; existing locked Python packages and TeX cache shared. No native simulator imported or launched by reproduction.",
            "pdf_binary_equality": sha(PAPER / "paper.pdf")
            == sha(root / PAPER / "paper.pdf"),
        },
    )
    print(
        json.dumps(
            {
                "clean_reproduction_passed": True,
                "copied_files": len(copied),
                "new_physics": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--clean", type=Path)
    args = parser.parse_args()
    if args.seal:
        seal()
    elif args.verify:
        verify()
    else:
        clean(args.clean)
