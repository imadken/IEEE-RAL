"""Editable conceptual diagrams reconstructed from supplied V4.4, no robot data."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch, Rectangle
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

INK = "#224652"


def label(ax, x, y, text, size, extension, color=INK, weight="normal"):
    if extension == "pdf":
        path = TextPath(
            (0, 0),
            text,
            size=size,
            prop=FontProperties(family="DejaVu Sans", weight=weight),
        )
        bounds = path.get_extents()
        transform = Affine2D().translate(
            x - (bounds.x0 + bounds.width / 2), y - (bounds.y0 + bounds.height / 2)
        )
        ax.add_patch(
            PathPatch(
                path, color=color, linewidth=0, transform=transform + ax.transData
            )
        )
    else:
        ax.text(
            x,
            y,
            text,
            size=size,
            ha="center",
            va="center",
            color=color,
            fontfamily="DejaVu Sans",
            weight=weight,
        )


def box(ax, x, y, width, height, fill, edge="#9fb6bf"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=3",
            facecolor=fill,
            edgecolor=edge,
            linewidth=0.6,
        )
    )


def arrow(ax, start, end, color=INK, double=False):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="<->" if double else "-|>",
            color=color,
            mutation_scale=8,
            linewidth=1,
        )
    )


def figure1(directory, extension):
    fig, ax = plt.subplots(figsize=(3.43, 1.34))
    ax.set(xlim=(0, 247), ylim=(0, 96.5))
    ax.axis("off")
    for i, (title, subtitle, color) in enumerate(
        [
            ("HOLD", "Options may remain", "#487b89"),
            ("PRELOAD", "Options may be lost", "#bd6558"),
            ("DITHER", "A correction may remain", "#258b81"),
        ]
    ):
        x = 82 * i
        box(ax, x + 1, 81, 80, 14, color, color)
        label(ax, x + 41, 88, title, 8, extension, "white", "bold")
        box(ax, x + 1, 0, 80, 16, "#f0f5f7")
        # Split final label to keep all native text >=7.5pt at column width.
        if i == 2:
            label(ax, x + 41, 10.9, "A correction", 7.5, extension, color)
            label(ax, x + 41, 3.5, "may remain", 7.5, extension, color)
        else:
            label(ax, x + 41, 8, subtitle, 7.5, extension, color)
        # Cross-section schematic, not simulator geometry or observed contact.
        ax.add_patch(
            Rectangle(
                (x + 25, 64), 32, 12, facecolor="#75848a", edgecolor=INK, linewidth=0.7
            )
        )
        for dx in (26, 51):
            ax.add_patch(
                Rectangle(
                    (x + dx, 45),
                    5,
                    20,
                    facecolor="#a2adb2",
                    edgecolor=INK,
                    linewidth=0.7,
                )
            )
        ax.add_patch(
            Rectangle(
                (x + 37, 24), 8, 32, facecolor="#c7d2d5", edgecolor=INK, linewidth=0.6
            )
        )
        for dx in (21, 46):
            ax.add_patch(
                Rectangle(
                    (x + dx, 18),
                    15,
                    17,
                    facecolor="#c4cccf",
                    edgecolor=INK,
                    linewidth=0.6,
                )
            )
        if i == 1:
            arrow(ax, (x + 64, 59), (x + 64, 39), color)
        if i == 2:
            arrow(ax, (x + 21, 41), (x + 61, 41), color, True)
    fig.subplots_adjust(0, 0, 1, 1)
    with matplotlib.rc_context(
        {"svg.fonttype": "none", "svg.hashsalt": "RPD-V45-conceptual-20261121"}
    ):
        metadata = (
            {"Creator": None, "Date": None}
            if extension == "svg"
            else {"Creator": None, "CreationDate": None, "ModDate": None}
        )
        fig.savefig(directory / f"figure1.{extension}", metadata=metadata)
    plt.close(fig)


def figure2(directory, extension):
    fig, ax = plt.subplots(figsize=(6.92, 1.9))
    ax.set(xlim=(0, 498.24), ylim=(0, 136.8))
    ax.axis("off")
    box(ax, 1, 79, 496, 57, "#f1f7f9")
    box(ax, 1, 1, 496, 72, "#f6f8f9")
    for x, title, first, second in [
        (6, "Observation", "history h; belief b", ""),
        (130, "Probe decision", "probe, direct or STOP", ""),
        (254, "Physical response", "new state + signal y", ""),
        (378, "Recovery choice", "feedback action a(y)", ""),
    ]:
        box(ax, x, 85, 112, 30, "white")
        label(ax, x + 56, 105, title, 8.5, extension, weight="bold")
        label(ax, x + 56, 93, first, 7.8, extension)
        if x < 378:
            arrow(ax, (x + 113, 100), (x + 123, 100))
    label(ax, 48, 126, "ONLINE", 8, extension, weight="bold")
    label(ax, 64, 63, "OFFLINE EVALUATION", 8, extension, weight="bold")
    box(ax, 6, 19, 111, 29, "white")
    label(ax, 61.5, 37, "One checkpoint s", 8.5, extension, weight="bold")
    label(ax, 61.5, 26, "same remaining time", 7.8, extension)
    box(ax, 139, 35, 127, 22, "#e0eff2")
    box(ax, 139, 7, 127, 22, "#fae8df")
    label(ax, 202.5, 49, "Neutral hold H(d)", 8.2, extension, weight="bold")
    label(ax, 202.5, 39, "duration d", 7.5, extension)
    label(ax, 202.5, 21, "Physical probe T(p)", 8.2, extension, weight="bold")
    label(ax, 202.5, 11, "same duration d", 7.5, extension)
    for target in (46, 18):
        ax.plot([118, 128, 128], [33, 33, target], color=INK, linewidth=0.7)
        arrow(ax, (128, target), (138, target))
    box(ax, 295, 16, 196, 34, "white")
    label(ax, 393, 42, "Replay both fixed corrections", 8.5, extension, weight="bold")
    label(ax, 393, 31, "Goal sets, constraints and signal", 7.8, extension)
    label(ax, 393, 21, "Compare K after hold and probe", 8, extension, weight="bold")
    for y in (46, 18):
        ax.plot([267, 279, 279], [y, y, 33], color=INK, linewidth=0.7)
        arrow(ax, (279, 33), (294, 33))
    fig.subplots_adjust(0, 0, 1, 1)
    with matplotlib.rc_context(
        {"svg.fonttype": "none", "svg.hashsalt": "RPD-V45-conceptual-20261121"}
    ):
        metadata = (
            {"Creator": None, "Date": None}
            if extension == "svg"
            else {"Creator": None, "CreationDate": None, "ModDate": None}
        )
        fig.savefig(directory / f"figure2.{extension}", metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "svg"):
        figure1(args.output, suffix)
        figure2(args.output, suffix)
