"""Plot released annotation timing only; this is not model alarm performance."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    plt.switch_backend("Agg")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    result = json.loads((root / "qualification.json").read_text())
    rows = result["raw_annotation_checks"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for valid, color, label in [
        (True, "#237aab", "Positive event window (57)"),
        (False, "#b33c35", "Empty/reversed window (3)"),
    ]:
        selected = [r for r in rows if r["event_window_in_actual_frames"] == valid]
        axes[0].scatter(
            [r["raw"]["failure"]["induced_at_frame"] / 30 for r in selected],
            [r["raw"]["failure"]["recovery_started_at_frame"] / 30 for r in selected],
            color=color,
            label=label,
            alpha=0.65,
        )
    axes[0].plot([0, 27], [0, 27], color="gray", linestyle="--", linewidth=1)
    axes[0].set(
        xlabel="Annotated failure onset (s)",
        ylabel="Annotated recovery start (s)",
        title="60 released sample annotations",
    )
    axes[0].legend(fontsize=8)
    axes[1].bar(["Cylinder", "USB-C", "RJ45"], [242, 244, 247], color="#bfcbd3")
    for index in range(3):
        axes[1].text(
            index, 15, "0 event/phase\nannotation files", ha="center", fontsize=9
        )
    axes[1].set(
        ylabel="Pilot episodes acquired", title="Fixed pilot: annotations unavailable"
    )
    fig.suptitle(
        "REBOOT release qualification — annotation audit, no trained detector",
        fontsize=12,
    )
    destination = root / "figures"
    destination.mkdir(exist_ok=True)
    fig.savefig(destination / "annotation_integrity.pdf")
    fig.savefig(destination / "annotation_integrity.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
