"""Editable vector assembly schematic and explicit constructed-world example."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import (
    FancyArrowPatch,
    FancyBboxPatch,
    PathPatch,
    Polygon,
    Rectangle,
)
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D


def render(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "svg", "png"):
        render_one(directory, extension)


def render_one(directory: Path, extension: str) -> None:
    fig, ax = plt.subplots(figsize=(3.45, 3.05))
    ax.set(xlim=(0, 345), ylim=(0, 305))
    ax.axis("off")
    ink = "#183041"
    colors = ("#edf2f5", "#fff0e8", "#e3f2ec")

    def label(x, y, value, size=9.8, color=ink, center=False):
        size = max(size, 10.5)  # 7.56 pt native, above 7.5 pt at official column width.
        if extension == "pdf":
            path = TextPath(
                (0, 0), value, size=size, prop=FontProperties(family="DejaVu Sans")
            )
            dx = path.get_extents().width / 2 if center else 0
            ax.add_patch(
                PathPatch(
                    path,
                    facecolor=color,
                    linewidth=0,
                    transform=Affine2D().translate(x - dx, y) + ax.transData,
                )
            )
        else:
            ax.text(
                x,
                y,
                value,
                fontsize=size * 0.72,
                color=color,
                ha="center" if center else "left",
                va="baseline",
                fontfamily="DejaVu Sans",
            )

    def arrow(start, end):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=7,
                linewidth=0.8,
                color=ink,
            )
        )

    label(172, 291, "CONCEPTUAL SCENE · CONSTRUCTED WORLDS", 8.5, center=True)
    # Cross-section only: this is not a mesh, simulator frame, or measured contact.
    for y in (247, 211):
        ax.add_patch(
            Rectangle(
                (215, y), 82, 20, facecolor="#cbd4db", edgecolor=ink, linewidth=0.6
            )
        )
    ax.add_patch(
        Polygon(
            [(55, 234), (205, 244), (205, 256), (55, 246)],
            facecolor="#5d89a5",
            edgecolor=ink,
            linewidth=0.7,
        )
    )
    label(43, 218, "held peg", 8.8)
    label(253, 198, "fixture", 8.8, center=True)
    arrow((156, 218), (205, 218))
    label(164, 205, "insertion", 8.3, center=True)
    label(172, 177, "Same checkpoint · same 0.5 s · 3.5 s left", 9.3, center=True)
    cards = [
        ("HOLD", ["{a0}", "{a0, a1}", "{a1}"], "no response split"),
        ("FINE PROBE", ["{a0}", "{a1}", "EMPTY"], "A / B / C"),
        ("COARSE PROBE", ["{a0}", "{a0, a1}", "{a1}"], "AB / C"),
    ]
    for i, (title, options, response) in enumerate(cards):
        x = 5 + 115 * i
        ax.add_patch(
            FancyBboxPatch(
                (x, 52),
                105,
                108,
                boxstyle="round,pad=2,rounding_size=3",
                facecolor=colors[i],
                edgecolor="#8a9aa6",
                linewidth=0.6,
            )
        )
        arrow((172, 172), (x + 52, 164))
        label(x + 52, 147, title, 9.1, center=True)
        label(x + 52, 132, response, 9.0, center=True)
        for y, world, options_here in zip((112, 92, 72), "ABC", options, strict=True):
            label(x + 7, y, world, 10.1)
            label(
                x + 26,
                y,
                options_here,
                10.1,
                color="#ae392e" if options_here == "EMPTY" else ink,
            )
    label(
        172,
        37,
        "B loses one option; C loses the entire repertoire.",
        8.9,
        center=True,
    )
    label(172, 17, "Online coarse branch: AB → a0; C → a1", 9.6, center=True)
    fig.subplots_adjust(0, 0, 1, 1)
    with matplotlib.rc_context({"svg.fonttype": "none"}):
        fig.savefig(
            directory / f"figure1.{extension}",
            dpi=220,
            metadata={"Creator": "Scientific vector schematic"},
        )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    render(parser.parse_args().output)
