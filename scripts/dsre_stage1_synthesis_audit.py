"""Check manuscript claims, provenance, official format and anonymity offline."""

import argparse
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from dsre_stage1_audit import has_reference_heading


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalize_bib_title(s):
    return " ".join(s.replace("{", "").replace("}", "").split()).lower()


def main(root, build):
    facts = read(root / "scientific_consolidation.json")
    source = Path("results/dsre-operational/20261115T195007Z-science-v12")
    rows = {}
    with gzip.open(source / "prospective_rows.jsonl.gz", "rt") as stream:
        for r in map(json.loads, stream):
            if r["population"] == "new_confirmation":
                rows[r["id"]] = r
    clean, strict, noisy = {}, {}, {}
    with gzip.open(source / "prospective_decisions.jsonl.gz", "rt") as stream:
        for d in map(json.loads, stream):
            if d["id"] in rows:
                if d["scenario"] == "clean" and d["mode"] == "point_proposal":
                    if d["method"] == "DSRE_risk":
                        clean[d["id"]] = d
                    if d["method"] == "DSRE_strict":
                        strict[d["id"]] = d
                if (d["scenario"], d["mode"], d["method"]) == (
                    "bound005",
                    "robust_proposal",
                    "DSRE_risk",
                ):
                    noisy[d["id"]] = d
    selected = [i for i, d in clean.items() if d["action"] == "recover"]
    assert len(selected) == 50
    assert (
        sum(
            not rows[i]["initial_success"]
            and not rows[i]["outcomes"]["continue_value"]
            and rows[i]["outcomes"]["recover_value"]
            for i in selected
        )
        == 48
    )
    assert sum(all(rows[i]["outcomes"].values()) for i in selected) == 1
    assert sum(not any(rows[i]["outcomes"].values()) for i in selected) == 1
    additions = [i for i in rows if clean[i]["adequate"] > strict[i]["adequate"]]
    assert len(additions) == 50 and all(rows[i]["initial_success"] for i in additions)
    assert all(
        clean[i]["required_selected"] == strict[i]["required_selected"] for i in rows
    )
    bad = [i for i, d in noisy.items() if d["inadequate"]]
    assert len(bad) == 5 and all(noisy[i]["action"] == "continue" for i in bad)
    assert sum(not rows[i]["initial_success"] for i in bad) == 4
    assert all(
        not rows[i]["outcomes"]["continue_value"]
        and rows[i]["outcomes"]["recover_value"]
        for i in bad
    )
    assert all(noisy[i]["false_assertions"] == 0 for i in rows)
    totals = {}
    for mode in ("point_proposal", "robust_proposal"):
        profiles = [
            facts["tables"][f"uniform0.005_r{rep}|{mode}|DSRE_risk"] for rep in range(3)
        ]
        totals[mode] = [
            sum(p["false_assertions"] for p in profiles),
            sum(p["literals"] for p in profiles),
        ]
    assert totals == {"point_proposal": [123, 1953], "robust_proposal": [0, 1507]}
    assert [
        facts["tables"][f"uniform0.005_r{rep}|robust_proposal|DSRE_risk"][
            "required_selected"
        ]
        for rep in range(3)
    ] == [14, 22, 16]
    assert all(
        facts["tables"][f"uniform0.005_r{rep}|robust_proposal|DSRE_risk"]["inadequate"]
        == 4
        for rep in range(3)
    )
    secondary = Counter()
    with gzip.open(source / "secondary_decisions.jsonl.gz", "rt") as stream:
        for d in map(json.loads, stream):
            if (
                d["id"] in rows
                and d["method"] == "DSRE_risk"
                and d["scenario"].startswith("delay")
            ):
                for k in ("inadequate", "stop"):
                    secondary[d["mode"], k] += d[k]
    assert secondary["point_proposal", "inadequate"] == 16
    assert secondary["robust_proposal", "stop"] == 640
    historical = []
    with gzip.open(source / "offline_rows.jsonl.gz", "rt") as stream:
        historical = [
            r
            for r in map(json.loads, stream)
            if r["population"] == "development_reference"
        ]
    assert len(historical) == 844
    assert all(
        sum(r["task"] == t for r in historical) == 422
        for t in ("PickCube-v1", "PushCube-v1")
    )
    push = [r for r in historical if r["task"] == "PushCube-v1"]
    assert len({r["group"] for r in push}) == 211
    assert sum(any(r["outcomes"].values()) for r in push) == 417
    calibration = read(
        Path(
            "results/dsre-operational/20261115T082827Z-recovery-evidence/calibration_decision.json"
        )
    )["strata"]["DSRE_risk|PickCube-v1|recover"]
    assert (calibration["new_assigned_parents"], calibration["new_error_parents"]) == (
        112,
        0,
    )
    assert abs(1 - (0.05 / 68) ** (1 / 112) - calibration["new_upper"]) < 1e-12
    assert min(n for n in range(1, 200) if 1 - (0.05 / 68) ** (1 / n) <= 0.1) == 69
    formal = facts["formal_regression"]
    assert formal["exhaustive_two_action_four_state_tables"] == 256
    assert facts["confirmation_failed_start_conflict_pairs_exist"] is False
    initial = read(root / "initial.json")
    for n in (
        ".gitignore",
        "uv.lock",
        "rss2027/dsre_full_paper_master.tex",
        "rss2027/dsre_full_paper_master.pdf",
        "rss2027/operational_references.bib",
    ):
        assert sha(Path(n)) == initial["file_sha256"][n], n
    p = build / "dsre_stage1.pdf"
    info = subprocess.check_output(["pdfinfo", str(p)], text=True)
    content = subprocess.check_output(["pdftotext", "-layout", str(p), "-"], text=True)
    pages = [s for s in content.split("\f") if s.strip()]
    assert len(pages) == 6
    assert [has_reference_heading(s) for s in pages] == [False] * 5 + [True]
    assert len(pages[4].split()) >= 350
    for forbidden in (
        "imad",
        "IEEE-RAL",
        "/home/",
        "github.com",
        "http://",
        "https://",
        "acknowledgment",
        "acknowledgement",
    ):
        assert forbidden.lower() not in (info + content).lower(), forbidden
    assert not re.search(r"^Author:\s*\S", info, re.MULTILINE)
    fonts = subprocess.check_output(["pdffonts", str(p)], text=True)
    assert all(
        "Type 1" in line and line.split()[-5] == "yes"
        for line in fonts.splitlines()[2:]
    )
    tex = Path("rss2027/dsre_stage1.tex").read_text()
    for forbidden in (
        r"\geometry",
        r"\textheight",
        r"\textwidth=",
        r"\baselinestretch",
        r"\vspace{-",
        r"\small",
        r"\scriptsize",
        r"\fontsize",
        r"\setlength",
    ):
        assert forbidden not in tex, forbidden
    assert (
        sha(Path("rss2027/IEEEtran.cls"))
        == sha(root / "official-author-kit/IEEEtran.cls")
        == initial["file_sha256"]["rss2027/IEEEtran.cls"]
    )
    log = (build / "dsre_stage1.log").read_text()
    assert "Overfull" not in log
    assert not re.search(r"(?:Citation|Reference).*undefined", log)
    assert "Undefined control sequence" not in log
    url_list = subprocess.check_output(["pdfinfo", "-url", str(p)], text=True)
    assert len(url_list.strip().splitlines()) <= 1, url_list
    bibliography = Path("rss2027/stage1_synthesis_references.bib").read_text()
    cited = {
        k.strip()
        for cs in re.findall(r"\\cite\w*\{([^}]+)\}", tex)
        for k in cs.split(",")
    }
    records = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    assert cited == records and len(cited) == 10
    citations = read(root / "citation_verification.json")
    assert {v["key"] for v in citations["records"]} == cited and all(
        v["verified"] for v in citations["records"]
    )

    for record in citations["records"]:
        entry = next(
            e
            for e in re.split(r"(?=@\w+\{)", bibliography)
            if re.match(r"@\w+\{" + record["key"] + ",", e)
        )
        title = re.search(r"title=\{(.*?)\},\s*\n", entry, re.DOTALL).group(1)
        assert normalize_bib_title(title) == normalize_bib_title(record["title"]), (
            record["key"]
        )
        assert re.search(r"year=\{" + str(record["year"]) + r"\}", entry), record["key"]
    for name in (
        "stage1_synthesis_outcomes.tex",
        "stage1_synthesis_decisions.tex",
        "stage1_synthesis_numbers.tex",
    ):
        assert r"\input{" + name.removesuffix(".tex") + "}" in tex
    for field, value in (
        ("pdfinfo.txt", info),
        ("pdffonts.txt", fonts),
        ("paper_text.txt", content),
        ("pdf_external_urls.txt", url_list),
    ):
        (root / field).write_text(value)
    report = {
        "passed": True,
        "paper_pdf_sha256": sha(p),
        "pages": 6,
        "content_pages": 5,
        "references_pages": 1,
        "words_by_page": [len(x.split()) for x in pages],
        "citations_verified": len(cited),
        "all_pdf_fonts_embedded_type1": True,
        "no_external_urls_or_identifying_metadata": True,
        "official_class_byte_identical": True,
        "overfull_boxes": 0,
        "unresolved_citations_or_references": 0,
        "class_load_TU_font_warnings": len(re.findall(r"LaTeX Font Warning:", log)),
        "font_warning_scope": "Official legacy class tunes TU fonts before the document's T1/Times packages. Final PDF font inventory is entirely embedded Type 1 Times/Computer Modern; no font or geometry override was introduced. Full warnings retained.",
        "raw_decision_composition_rechecked": True,
        "corrupted_literal_counts": totals,
        "historical_reference_and_clean_calibration_rechecked": True,
        "formal_regression": formal,
        "full_manuscript_and_shared_bibliography_preserved": True,
        "independent_numerical_report": "scientific_consolidation.json",
        "numerical_macro_ledger": "claim_source_ledger.json",
        "physical_witness_sources": "scientific_consolidation.json:physical_witnesses,historical_conflict_examples,minimum_certificate_example,measurement_example",
        "remaining_review": "Visual page review and adversarial scientific critique are separately recorded; machine checks do not establish novelty or acceptance.",
    }
    (root / "manuscript_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("build", type=Path)
    a = p.parse_args()
    main(a.root, a.build)
