"""Portable official-class build/check adapted from the preserved workspace tooling. No physics."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


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
    verify_class()
    destination.mkdir(parents=True, exist_ok=True)
    for path in SOURCE.rglob("*"):
        if path.is_file() and path.suffix in (".tex", ".bib", ".pdf", ".svg", ".cls"):
            target = destination / path.relative_to(SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    shutil.copyfile(SOURCE / "IEEEtran.cls", destination / "IEEEtran.cls")
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
        shutil.copyfile(SOURCE / "IEEEtran.cls", probe / "IEEEtran.cls")
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
                    "class_sha256": sha(SOURCE / "IEEEtran.cls"),
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
    raw_bbox = run(["pdftotext", "-bbox", str(pdf), "-"])
    # Poppler can emit unmapped CMEX delimiter controls in otherwise valid
    # geometry XML. Drop only XML-forbidden controls for the geometry check;
    # do not alter the PDF, its text receipt or the original extraction.
    bbox = ET.fromstring(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_bbox))
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
        r"\\(geometry|fontsize|linespread|vspace|enlargethispage)\b"
        r"|\\(textwidth|textheight|oddsidemargin)\s*="
        r"|\\(?:setlength|addtolength)\s*\{\\(?:textwidth|textheight|oddsidemargin)\}",
        "\n".join(p.read_text() for p in SOURCE.glob("*.tex")),
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
        "scientific_completeness_requires_separate_review": True,
    }


def verify_class():
    expected = "d63d4bf27f29603a733d06e27ba5fbb40488acf9d1d696354a88b886758f70a7"
    assert sha(SOURCE / "IEEEtran.cls") == expected, "Official class mismatch"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.source.resolve()
    assert not args.output.resolve().is_relative_to(SOURCE), "Build outside source tree"
    pdf = build_in(args.output.resolve())
    result = inspect(pdf, args.output.resolve() / "main.log")
    (args.output / "build_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
