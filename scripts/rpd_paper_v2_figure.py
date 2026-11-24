"""Render the explicitly constructed RPD V2 thesis figure, without robot data."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(3.45, 2.9))
    ax.set(xlim=(0, 345), ylim=(0, 290))
    ax.axis("off")
    font = FontProperties(family="DejaVu Sans")
    colors = {
        "ink": "#182b3a",
        "hold": "#eaf0f4",
        "fine": "#fff0e6",
        "coarse": "#e1f1eb",
    }

    def label(x, y, text, size=8, color="ink", center=False):
        path = TextPath((0, 0), text, size=size * 1.12, prop=font)
        offset = path.get_extents().width / 2 if center else 0
        ax.add_patch(
            PathPatch(
                path,
                transform=Affine2D().translate(x - offset, y) + ax.transData,
                facecolor=colors.get(color, color),
                linewidth=0,
            )
        )

    def box(x, y, width, height, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=2,rounding_size=3",
                facecolor=colors[color],
                edgecolor="#8ca0aa",
                linewidth=0.65,
            )
        )

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=7,
                linewidth=0.7,
                color=colors["ink"],
            )
        )

    label(172, 277, "CONSTRUCTED EXAMPLE · no robot measurements", 7.1, center=True)
    box(62, 244, 221, 22, "hold")
    label(172, 252, "Ambiguous checkpoint: A, B or C; 4 s left", 7.6, center=True)
    columns = [
        (
            5,
            "hold",
            "HOLD (0.5 s)",
            "no distinction",
            ["{a0}", "{a0, a1}", "{a1}"],
            "0 nats",
        ),
        (
            120,
            "fine",
            "FINE (0.5 s)",
            "A / B / C",
            ["{a0}", "{a1}", "EMPTY"],
            "1.099 nats",
        ),
        (
            235,
            "coarse",
            "COARSE (0.5 s)",
            "AB / C",
            ["{a0}", "{a0, a1}", "{a1}"],
            "0.637 nats",
        ),
    ]
    for x, color, title, response, options, info in columns:
        arrow(172, 242, x + 52, 218)
        box(x, 79, 105, 136, color)
        label(x + 52, 201, title, 7.6, center=True)
        label(x + 52, 185, response, 8, center=True)
        label(x + 52, 170, info, 7.5, center=True)
        for y, world, choices in zip((149, 129, 109), "ABC", options, strict=True):
            label(x + 7, y, world, 8)
            label(
                x + 26,
                y,
                choices,
                8.3,
                color="#b43a2c" if choices == "EMPTY" else "ink",
            )
        label(x + 52, 88, "K at 3.5 s remaining", 7.1, center=True)
    label(172, 64, "B: one option lost.  C: all options lost.", 7.5, center=True)
    arrow(287, 76, 287, 49)
    box(5, 5, 335, 42, "coarse")
    label(172, 34, "Online: execute only the selected branch", 8, center=True)
    label(172, 17, "Coarse response AB → a0; response C → a1", 8, center=True)
    fig.subplots_adjust(0, 0, 1, 1)
    for extension in ("pdf", "svg", "png"):
        fig.savefig(
            output / f"figure1.{extension}",
            dpi=220,
            metadata={"Creator": "Vector scientific illustration"},
        )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    render(parser.parse_args().output)
