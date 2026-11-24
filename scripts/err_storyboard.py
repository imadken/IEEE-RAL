"""Editable Figure 1 storyboard, separate from all manuscript/final figures.

Write native flat OpenDocument shapes with the standard library. The installed
LibreOffice can export the shapes to PowerPoint; no Python dependency is added.
"""

import argparse
from html import escape
from pathlib import Path


def frame(name, x, y, w, h, lines, *, box="plain", text="body"):
    content = "".join(
        f'<text:p text:style-name="{text}">{escape(line)}</text:p>' for line in lines
    )
    return f'<draw:frame draw:name="{name}" draw:style-name="{box}" svg:x="{x}cm" svg:y="{y}cm" svg:width="{w}cm" svg:height="{h}cm"><draw:text-box>{content}</draw:text-box></draw:frame>'


def write(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    shapes = []
    shapes.append(
        frame(
            "title",
            0.7,
            0.4,
            32,
            1.3,
            ["What evidence would settle this recovery claim?"],
            text="title",
        )
    )
    shapes.append(
        frame(
            "subtitle",
            0.7,
            1.8,
            32,
            0.9,
            [
                "EDITABLE STORYBOARD • implemented finite-model prototype • empirical value remains a Stage 2 hypothesis"
            ],
            text="small",
        )
    )
    shapes.append(
        frame(
            "inputs",
            0.7,
            3,
            9.8,
            10.8,
            [
                "A  FACTS + SOURCE + OBLIGATION",
                "",
                "Recorded predecision facts",
                "Pick goal distance: 3.85 vs 2.21 cm",
                "Same five other recorded facts",
                "",
                "Fixed continue / recover macros",
                "Declared checkpoint and horizon",
                "",
                "Useful recovery: harm ≤ 0.10",
                "and expected gain ≥ 0.05",
                "",
                "Original whole-leaf calibration",
                "and source assumptions stay fixed",
            ],
            box="blue",
        )
    )
    shapes.append(
        frame(
            "models",
            11.1,
            3,
            10,
            10.8,
            [
                "B  COMPATIBLE OUTCOME LAWS",
                "",
                "ANALYTICAL WORLDS — NOT EPISODES",
                "",
                "Qlow  = (.4, .2, 0, .4)",
                "Qhigh = (0, .6, .4, 0)",
                "Order: (00, 01, 10, 11)",
                "",
                "Same p0 = .4 and p1 = .6",
                "Different harm: 0 versus .4",
                "",
                "One-arm laws cannot separate them.",
                "A qualified paired law can differ.",
                "Different laws ≠ finite-sample certainty.",
            ],
            box="amber",
        )
    )
    shapes.append(
        frame(
            "certified",
            21.7,
            3,
            11.4,
            3.3,
            [
                "C  CERTIFIED RECOVER",
                "Original minimum facts + whole scope",
                "One selected fixed action online",
            ],
            box="green",
        )
    )
    shapes.append(
        frame(
            "unresolved",
            21.7,
            6.7,
            11.4,
            3.3,
            [
                "UNRESOLVED",
                "Minimum identifying experiment-TYPE plan",
                "Offline data may also REFUTE recovery",
            ],
            box="amber",
        )
    )
    shapes.append(
        frame(
            "impossible",
            21.7,
            10.4,
            11.4,
            3.4,
            [
                "NOT RESOLVABLE WITH THIS MENU",
                "Opposite verdicts; identical available laws",
                "Return the explicit countermodel pair",
            ],
            box="grey",
        )
    )
    shapes.append(
        frame(
            "offline",
            0.7,
            14.3,
            32.4,
            1.1,
            [
                "OFFLINE: evidence collection and paired evaluation     · · ·     ONLINE: one fixed action only"
            ],
            box="grey",
            text="small",
        )
    )
    shapes.append(
        frame(
            "old_physics",
            0.7,
            15.8,
            32.4,
            1.4,
            [
                "Existing DSRE preliminaries, unchanged: Pick 84 rescues / 111 recoveries; Push 126 / 128.",
                "Instrumented B7 + identical planner is equivalent. No new physical paired-only case or acquisition gain.",
            ],
            text="small",
        )
    )
    shapes.append(
        frame(
            "scope",
            0.7,
            17.6,
            32.4,
            0.8,
            [
                "Story illustration only. No new manuscript figure, rollout, sensor-cost measurement or acceptance claim."
            ],
            text="small",
        )
    )
    slide1 = (
        '<draw:page draw:name="Figure_1_storyboard" draw:master-page-name="Default">'
        + "".join(shapes)
        + "</draw:page>"
    )
    page = [
        frame(
            "page_title",
            0.7,
            0.5,
            32,
            1.5,
            ["Five content pages + one references page"],
            text="title",
        )
    ]
    page.append(
        frame(
            "page_budget",
            0.9,
            3,
            31.8,
            11.3,
            [
                "1  Problem, testable hypothesis and Figure 1: why the evidence source matters.",
                "",
                "2  Fixed actions, q/h/g, source assumptions and conditional statistical scope.",
                "",
                "3  Finite-world resolving-menu objective, standard cover proof and exact algorithm.",
                "",
                "4  Unchanged Pick/Push preliminaries, recorded-fact witness, analytical source contrast; B7 equality.",
                "",
                "5  Novelty limits, falsifiable Stage 2 protocol, independent calibration and null outcomes.",
                "",
                "6  References only: include harm bounds, UPS/targeted queries, DRD/ECD, test-cover and RESCUE.",
            ],
            box="blue",
        )
    )
    page.append(
        frame(
            "do_not_claim",
            0.9,
            15.2,
            31.8,
            2.4,
            [
                "Do not claim: new generic experiment-selection theory; unique B7 solver; a finite-sample guarantee from signatures;",
                "actual paired-only robot evidence; new physical efficiency; or a repaired recovery skill.",
            ],
            box="amber",
            text="small",
        )
    )
    slide2 = (
        '<draw:page draw:name="Page_budget" draw:master-page-name="Default">'
        + "".join(page)
        + "</draw:page>"
    )
    styles = []
    for name, color in [
        ("plain", "#FFFFFF"),
        ("blue", "#EAF1FA"),
        ("amber", "#FFF1D8"),
        ("green", "#E6F3E9"),
        ("grey", "#EFF1F4"),
    ]:
        styles.append(
            f'<style:style style:name="{name}" style:family="graphic"><style:graphic-properties draw:fill="solid" draw:fill-color="{color}" draw:stroke="solid" svg:stroke-color="#B2BAC5" fo:padding="0.25cm" draw:textarea-vertical-align="top"/></style:style>'
        )
    for name, size, bold in [
        ("body", 14, "normal"),
        ("small", 12, "normal"),
        ("title", 25, "bold"),
    ]:
        styles.append(
            f'<style:style style:name="{name}" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0.15cm"/><style:text-properties fo:font-family="Liberation Sans" fo:font-size="{size}pt" fo:font-weight="{bold}" fo:color="#172A41"/></style:style>'
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        + """<office:document
      xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
      xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
      xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
      xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
      xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
      xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
      office:version="1.2" office:mimetype="application/vnd.oasis.opendocument.presentation">
      <office:styles/><office:automatic-styles>
      <style:page-layout style:name="wide"><style:page-layout-properties fo:page-width="33.867cm" fo:page-height="19.05cm" style:print-orientation="landscape"/></style:page-layout>
    """
        + "".join(styles)
        + '</office:automatic-styles><office:master-styles><style:master-page style:name="Default" style:page-layout-name="wide"/></office:master-styles><office:body><office:presentation>'
        + slide1
        + slide2
        + "</office:presentation></office:body></office:document>"
    )
    output.write_text(xml)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "research/err_method_challenge/presentation/figure1_storyboard.fodp"
        ),
    )
    write(parser.parse_args().output)
