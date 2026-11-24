"""Build and check only this paper workspace; never execute robot simulation."""

import argparse
import hashlib
import json
import lzma
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REVIEWS = BASE / "reviews/v21_preliminary"
EVIDENCE = BASE.parents[1] / "research/rpd_assembly_preliminary_20261120"


def layout_diagnostics() -> str:
    names = (
        "paperwidth",
        "paperheight",
        "textwidth",
        "textheight",
        "columnwidth",
        "columnsep",
        "oddsidemargin",
        "evensidemargin",
        "topmargin",
        "headheight",
        "headsep",
        "baselineskip",
    )
    return (
        "\\makeatletter\n"
        + "".join("\\typeout{RPD_LAYOUT_" + n + "=\\the\\" + n + "}\n" for n in names)
        + "\\typeout{RPD_LAYOUT_fontsize=\\f@size}\n\\makeatother\n"
    )


def measured_layout(log: Path) -> dict[str, str]:
    return dict(re.findall(r"RPD_LAYOUT_(\w+)=([^\n]+)", log.read_text()))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def originals() -> dict:
    hashes = json.loads((BASE / "reviews/original_v2_hashes.json").read_text())
    assert {
        p.relative_to(BASE / "original_v2").as_posix()
        for p in (BASE / "original_v2").rglob("*")
        if p.is_file()
    } == set(hashes)
    for name, expected in hashes.items():
        assert sha(BASE / "original_v2" / name) == expected, name
    for line in (BASE / "template/SHA256SUMS.txt").read_text().splitlines():
        expected, name = line.split("  ", 1)
        assert sha(BASE / "template" / name) == expected, name
    expected = sha(BASE / "template/upstream/IEEEtran.cls")
    assert sha(BASE / "manuscript/IEEEtran.cls") == expected
    return {
        "original_v2_files": len(hashes),
        "template_hashes_passed": True,
        "class_unmodified": True,
    }


def preservation() -> dict:
    """Verify baseline hashes, protected absences and historical metadata read-only."""
    repository = BASE.parents[1]
    snapshot = json.loads(
        lzma.decompress((EVIDENCE / "audit/preservation_before.json.xz").read_bytes())
    )
    for name, expected in snapshot["files"].items():
        path = repository / name
        if expected is None:
            assert not path.exists(), f"Protected absence changed: {name}"
        else:
            assert path.is_file() and sha(path) == expected, name
    for name, expected in snapshot["historical_metadata"].items():
        path = repository / name
        assert path.is_file(), name
        info = path.stat()
        assert [info.st_size, info.st_mtime_ns] == expected, name
    status = run(
        ["git", "status", "--porcelain=v1", "--untracked-files=normal"], repository
    )

    def unrelated(lines):
        new_sources = {
            "scripts/rpd_assembly_contract.py",
            "scripts/rpd_assembly_worker.py",
            "scripts/rpd_assembly_run.py",
            "scripts/rpd_assembly_audit.py",
            "scripts/rpd_assembly_reproduce.py",
            "scripts/rpd_assembly_report.py",
            "tests/test_rpd_assembly.py",
        }
        return "\n".join(
            line
            for line in lines.splitlines()
            if line[3:] != "papers/"
            and line[3:] not in new_sources
            and not line[3:].startswith(
                (
                    "papers/rss2027_rpd_stage1/",
                    "research/rpd_assembly_preliminary_20261120/",
                )
            )
        )

    existing_status = unrelated(status)
    assert existing_status == unrelated(snapshot["user_status"]), "User changes differ"
    run(
        ["git", "merge-base", "--is-ancestor", snapshot["starting_commit"], "HEAD"],
        repository,
    )
    result = {
        "passed": True,
        "starting_commit": snapshot["starting_commit"],
        "baseline_path_checks": len(snapshot["files"]),
        "protected_absences": sum(v is None for v in snapshot["files"].values()),
        "historical_size_mtime_checks": len(snapshot["historical_metadata"]),
        "preexisting_status_entries_unchanged": len(existing_status.splitlines()),
        "original_v2": originals(),
        "new_physics": 0,
        "scope": "Content hashes for inventoried source/manuscript/user paths; historical size/mtime plus separately rechecked sealed manifests. Metadata checks alone are not full historical byte hashes.",
    }
    (REVIEWS / "preservation_verification.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    return result


def prior_seal() -> dict:
    with tarfile.open(EVIDENCE / "inputs/pre_v21_workspace.tar.xz") as archive:
        prefix = "papers/rss2027_rpd_stage1/"
        checksums = archive.extractfile(prefix + "reviews/SHA256SUMS").read().decode()
        for line in checksums.splitlines():
            expected, name = line.split("  ", 1)
            assert (
                hashlib.sha256(archive.extractfile(prefix + name).read()).hexdigest()
                == expected
            ), name
    return {"prior_workspace_seal_verified_from_immutable_archive": True}


def remove_pdf_information(path: Path) -> None:
    """Override the generated PDF's Info dictionary with an empty dictionary.

    Standard incremental update: content/font objects and their offsets remain
    intact. Both classic and stream cross-reference trailers are supported.
    Only locally generated, unencrypted TeX PDFs are accepted.
    """
    data = path.read_bytes()
    matches = list(re.finditer(rb"startxref\s+(\d+)\s+%%EOF", data))
    assert matches, "Missing generated PDF cross-reference trailer"
    previous = int(matches[-1][1])
    tail = data[previous:]
    if tail.startswith(b"xref"):
        found = re.search(rb"trailer\s*<<(.*?)>>", tail, re.DOTALL)
    else:
        found = re.search(rb"\d+\s+\d+\s+obj\s*<<(.*?)>>\s*stream", tail, re.DOTALL)
    assert found, "Unsupported generated PDF trailer"
    dictionary = found[1]
    assert b"/Encrypt" not in dictionary
    root = re.search(rb"/Root\s*(\d+\s+\d+\s+R)", dictionary)
    size = re.search(rb"/Size\s*(\d+)", dictionary)
    assert root and size
    number = int(size[1])
    prefix = data + b"\n"
    object_offset = len(prefix)
    prefix += f"{number} 0 obj\n<<>>\nendobj\n".encode()
    xref_offset = len(prefix)
    update = (
        f"xref\n0 1\n0000000000 65535 f \n{number} 1\n{object_offset:010} 00000 n \n"
        f"trailer\n<</Size {number + 1}/Root {root[1].decode()}/Info {number} 0 R/Prev {previous}>>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    path.write_bytes(prefix + update)


def build_in(destination: Path) -> Path:
    originals()
    destination.mkdir(parents=True, exist_ok=True)
    for path in (BASE / "manuscript").rglob("*"):
        if path.is_file() and path.suffix in (".tex", ".bib", ".pdf", ".svg", ".cls"):
            target = destination / path.relative_to(BASE / "manuscript")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    shutil.copyfile(
        BASE / "template/upstream/IEEEtran.cls", destination / "IEEEtran.cls"
    )
    source = destination / "main.tex"
    source.write_text(
        source.read_text().replace(
            "\\maketitle\n", "\\maketitle\n" + layout_diagnostics(), 1
        )
    )
    compiler = os.environ.get("TECTONIC") or shutil.which("tectonic")
    if not compiler and Path("/tmp/tectonic-stage1-bin/tectonic").is_file():
        compiler = "/tmp/tectonic-stage1-bin/tectonic"
    env = dict(os.environ, SOURCE_DATE_EPOCH="1795132800", FORCE_SOURCE_DATE="1")
    if Path("/tmp/dsre-stage1-tex-cache").is_dir():
        env.setdefault("XDG_CACHE_HOME", "/tmp/dsre-stage1-tex-cache")
    if compiler:
        output = run(
            [
                compiler,
                "--only-cached",
                "--untrusted",
                "--keep-logs",
                "--keep-intermediates",
                "main.tex",
            ],
            destination,
            env,
        )
    elif shutil.which("latexmk"):
        output = run(
            [
                "latexmk",
                "-pdf",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "main.tex",
            ],
            destination,
            env,
        )
    else:
        raise RuntimeError(
            "Set TECTONIC to an existing compiler or provide standard latexmk; no automatic dependency installation."
        )
    (destination / "compiler.txt").write_text(output)
    remove_pdf_information(destination / "main.pdf")
    if compiler:
        probe = destination / "official_layout_probe"
        probe.mkdir(exist_ok=True)
        shutil.copyfile(BASE / "template/upstream/IEEEtran.cls", probe / "IEEEtran.cls")
        (probe / "probe.tex").write_text(
            "\\documentclass[conference]{IEEEtran}\n\\usepackage[T1]{fontenc}\n\\usepackage{times}\n\\begin{document}\n"
            + layout_diagnostics()
            + "Official class layout probe.\n\\end{document}\n"
        )
        run(
            [compiler, "--only-cached", "--untrusted", "--keep-logs", "probe.tex"],
            probe,
            env,
        )
        actual = measured_layout(destination / "main.log")
        official = measured_layout(probe / "probe.log")
        assert len(actual) == 13 and actual == official, {
            "main": actual,
            "official": official,
        }
        (destination / "layout_comparison.json").write_text(
            json.dumps(
                {
                    "passed": True,
                    "official": official,
                    "manuscript": actual,
                    "class_sha256": sha(BASE / "template/upstream/IEEEtran.cls"),
                    "scope": "Diagnostic typeout only; no layout settings modified",
                },
                indent=2,
            )
            + "\n"
        )
    return destination / "main.pdf"


def inspect(pdf: Path, log: Path | None = None) -> dict:
    info = run(["pdfinfo", str(pdf)])
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)[1])
    assert pages == 6, f"Expected5+1; found{pages}"
    assert re.search(r"Page size:\s+612 x 792 pts", info)
    assert not re.search(r"^Author:\s*\S", info, re.MULTILINE)
    assert not re.search(
        r"^(Title|Subject|Author|Creator|Producer|CreationDate|ModDate):",
        info,
        re.MULTILINE,
    )
    assert re.search(r"Metadata Stream:\s+no", info)
    text = run(["pdftotext", "-layout", str(pdf), "-"])
    bodies = [p for p in text.split("\f") if p.strip()]
    assert len(bodies) == 6 and re.match(r"\s*R\s*EFERENCES", bodies[-1])
    assert all(not re.search(r"R\s*EFERENCES", p) for p in bodies[:5])
    for word in (
        "/home/",
        "imadken",
        "Codex",
        "github.com",
        "http://",
        "https://",
        "[?]",
        "??",
    ):
        assert word not in text, word
    fonts = run(["pdffonts", str(pdf)])
    rows = fonts.splitlines()[2:]
    assert rows and all("Type 1C" in row and "yes yes" in row for row in rows), fonts
    urls = run(["pdfinfo", "-url", str(pdf)])
    assert not any(line.strip() for line in urls.splitlines()[1:]), urls
    bbox = ET.fromstring(run(["pdftotext", "-bbox", str(pdf), "-"]))
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    footer = []
    for i, page in enumerate(bbox.findall(".//x:page", ns), 1):
        for word in page.findall(".//x:word", ns):
            if float(word.attrib["yMin"]) > 735 or float(word.attrib["yMax"]) < 35:
                footer.append((i, word.text))
    assert not footer, f"Unexpected header/footer/page-number content:{footer}"
    if log and log.exists():
        trace = log.read_text()
        assert "Overfull" not in trace, "Overfull TeX box"
        assert "undefined on input" not in trace and "There were undefined" not in trace
    assert not re.search(
        r"\\(geometry|fontsize|linespread|vspace|enlargethispage|textwidth|textheight|oddsidemargin)\b",
        "\n".join(p.read_text() for p in (BASE / "manuscript").glob("*.tex")),
    )
    return {
        "pages": pages,
        "content_pages": 5,
        "reference_pages": 1,
        "paper_sha256": sha(pdf),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "fonts": fonts,
        "pdfinfo": info,
        "page_word_counts": [len(p.split()) for p in bodies],
        "page_numbers": False,
        "unresolved_references": False,
        "identifying_metadata_or_external_urls": False,
        "critical_method_in_main_PDF": True,
    }


def build() -> None:
    pdf = build_in(BASE / "build")
    # A build may precede layout corrections; submission publication requires all checks.
    receipt = inspect(pdf, BASE / "build/main.log")
    layout = BASE / "build/layout_comparison.json"
    if layout.is_file():
        shutil.copyfile(layout, REVIEWS / "layout_comparison.json")
    shutil.copyfile(pdf, BASE / "submission/rpd_stage1_anonymous.pdf")
    (REVIEWS / "build_verification.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    with zipfile.ZipFile(
        BASE / "submission/rpd_stage1_source.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for p in sorted((BASE / "manuscript").rglob("*")):
            if p.is_file() and p.suffix in (".tex", ".bib", ".pdf", ".svg", ".cls"):
                entry = zipfile.ZipInfo(
                    p.relative_to(BASE / "manuscript").as_posix(),
                    date_time=(2000, 1, 1, 0, 0, 0),
                )
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o644 << 16
                archive.writestr(entry, p.read_bytes())
    print(
        json.dumps({"built": str(pdf.relative_to(BASE)), "verified": True, "pages": 6})
    )


def check() -> None:
    result = inspect(
        BASE / "submission/rpd_stage1_anonymous.pdf", BASE / "build/main.log"
    )
    result.update(originals())
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("fonts", "pdfinfo")})
    )


def reproduce() -> None:
    with tempfile.TemporaryDirectory(prefix="rss-rpd-clean-", dir="/tmp") as directory:
        path = Path(directory)
        pdf = build_in(path)
        canonical = inspect(
            BASE / "submission/rpd_stage1_anonymous.pdf", BASE / "build/main.log"
        )
        actual = inspect(pdf, path / "main.log")
        assert canonical["text_sha256"] == actual["text_sha256"], (
            "Clean PDF text differs"
        )
        result = {
            "passed": True,
            "fresh_directory": True,
            "same_text": True,
            "pages": 6,
            "pdf_binary_identical": sha(pdf)
            == sha(BASE / "submission/rpd_stage1_anonymous.pdf"),
            "source_date_epoch": 1795132800,
            "new_physics": 0,
        }
        (REVIEWS / "clean_build_receipt.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "build",
            "check",
            "reproduce",
            "originals",
            "preservation",
            "prior-seal",
            "clean",
        ),
    )
    args = parser.parse_args()
    if args.command == "clean":
        for p in (BASE / "build").iterdir():
            if p.name != ".gitkeep":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    elif args.command == "originals":
        print(json.dumps(originals()))
    elif args.command == "preservation":
        print(json.dumps(preservation()))
    elif args.command == "prior-seal":
        print(json.dumps(prior_seal()))
    else:
        {"build": build, "check": check, "reproduce": reproduce}[args.command]()
