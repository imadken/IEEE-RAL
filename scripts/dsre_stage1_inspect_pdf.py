"""Independent inspection of the submission artifact, without inference imports."""

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def command(*args):
    return subprocess.check_output(args, text=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(pdf, build):
    out = Path("research/dsre_stage1_manuscript")
    source = Path("rss2027/dsre_stage1.tex").read_text()
    info = command("pdfinfo", str(pdf))
    assert re.search(r"^Pages:\s+6$", info, re.MULTILINE)
    assert "612 x 792 pts" in info
    assert not re.search(r"^Author:\s*\S", info, re.MULTILINE)
    font_listing = command("pdffonts", str(pdf))
    font_rows = font_listing.splitlines()[2:]
    assert font_rows and all("Type 1" in row for row in font_rows)
    assert all(re.search(r"\byes\s+yes\s+yes\s+\d+\s+\d+$", row) for row in font_rows)
    text = command("pdftotext", "-layout", str(pdf), "-")
    pages = [p for p in text.split("\f") if p.strip()]
    reference = lambda p: bool(re.search(r"R\s*E\s*F\s*E\s*R\s*E\s*N\s*C\s*E\s*S", p))
    assert len(pages) == 6 and reference(pages[5])
    assert not any(reference(p) for p in pages[:5])
    assert "Fig. 1." in pages[0]
    assert "When Does Evidence Justify Robot Recovery?" in pages[0]
    assert "same marginal" in text.lower() or "identical marginal" in text.lower()
    assert source.count("Decision-Sufficient Recovery Explanations") == 1
    forbidden = [
        r"imad",
        r"IEEE-RAL",
        r"github",
        r"Codex",
        r"Charter",
        r"/home/",
        r"Stage 2",
        r"Gate [1-6]",
    ]
    for pattern in forbidden:
        assert not re.search(pattern, text, re.IGNORECASE), pattern
    assert not re.search(r"https?://|www\.", text, re.IGNORECASE)
    # PDF URI actions are listed separately from ordinary internal citations.
    urls = command("pdfinfo", "-url", str(pdf))
    assert not re.search(r"https?://", urls)
    for forbidden_tex in (
        r"\textheight",
        r"\textwidth",
        r"\linespread",
        r"\baselinestretch",
        r"\fontsize",
        r"\geometry",
        r"\vspace{-",
    ):
        assert forbidden_tex not in source, forbidden_tex
    assert source.startswith(r"\documentclass[conference]{IEEEtran}")
    bbox = command("pdftotext", "-bbox", str(pdf), "-")
    xml = ET.fromstring(bbox)
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    page_bounds = []
    for page in xml.findall(".//x:page", ns):
        words = page.findall("x:word", ns)
        assert words
        bounds = [
            min(float(w.attrib["xMin"]) for w in words),
            min(float(w.attrib["yMin"]) for w in words),
            max(float(w.attrib["xMax"]) for w in words),
            max(float(w.attrib["yMax"]) for w in words),
        ]
        assert bounds[0] >= 47 and bounds[2] <= 565
        assert bounds[1] >= 36 and bounds[3] < 750
        assert not any(
            re.fullmatch(r"[1-6]", w.text or "") and float(w.attrib["yMin"]) > 745
            for w in words
        )
        page_bounds.append(bounds)
    # Diagram has no text smaller than 7pt; inspect its editable SVG styles.
    figure_checks = {}
    for name in ("figure1_evidence", "figure2_identification"):
        svg = (Path("rss2027/stage1_evidence") / (name + ".svg")).read_text()
        sizes = [float(x) for x in re.findall(r"font-size:\s*([\d.]+)px", svg)]
        if not sizes:
            sizes = [float(x) for x in re.findall(r"font:\s*([\d.]+)px", svg)]
        assert sizes and min(sizes) >= 7, (name, sizes)
        assert 'width="251.28pt"' in svg
        figure_checks[name] = {
            "minimum_nominal_pt": min(sizes),
            "print_width_pt": 251.28,
            "pdf_sha256": sha(Path("rss2027/stage1_evidence") / (name + ".pdf")),
        }
    protected = json.loads((out / "preservation_before.json").read_text())
    for path, expected in protected["preserve"].items():
        assert sha(path) == expected, path
    official = Path("/tmp/rss2027-official/IEEEtran.cls")
    if official.exists():
        assert sha(official) == sha("rss2027/IEEEtran.cls")
    for filename in ("dsre_stage1.log", "dsre_stage1.blg"):
        content = (build / filename).read_text()
        assert "Overfull" not in content and "Warning--" not in content
        assert (
            "undefined references" not in content
            and "undefined citations" not in content
        )
    renders = out / "page_renders"
    renders.mkdir(exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-r", "140", "-png", str(pdf), str(renders / "page")], check=True
    )
    assert len(list(renders.glob("page-*.png"))) == 6
    report = {
        "passed": True,
        "pdf_sha256": sha(pdf),
        "tex_sha256": sha("rss2027/dsre_stage1.tex"),
        "pages": 6,
        "content_pages": [1, 2, 3, 4, 5],
        "reference_page": 6,
        "figure1_page": 1,
        "page_text_bounds": page_bounds,
        "embedded_type1_fonts": len(font_rows),
        "pdfinfo": info,
        "pdffonts": font_listing,
        "external_uri_actions": 0,
        "figure_checks": figure_checks,
        "protected_files_verified": len(protected["preserve"]),
        "rendered_pages": {str(p): sha(p) for p in sorted(renders.glob("*.png"))},
        "inspect_source_sha256": sha(__file__),
    }
    (out / "pdf_inspection.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "pdf_text.txt").write_text(text)
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "passed",
                    "pages",
                    "reference_page",
                    "embedded_type1_fonts",
                    "protected_files_verified",
                ]
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=Path("rss2027/dsre_stage1.pdf"))
    parser.add_argument("--build", type=Path, default=Path("/tmp/dsre-stage1-build"))
    args = parser.parse_args()
    inspect(args.pdf, args.build)
