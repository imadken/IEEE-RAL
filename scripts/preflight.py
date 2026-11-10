"""Report safe hardware/version metadata without creating a simulator or changing drivers."""

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def preflight():
    names = ["mani-skill", "sapien", "robosuite", "mujoco", "torch", "numpy"]
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "missing"
    gpu = "nvidia-smi unavailable; Vulkan rendering compatibility remains untested"
    if shutil.which("nvidia-smi"):
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        gpu = (
            result.stdout.strip()
            if result.returncode == 0
            else f"nvidia-smi failed (exit {result.returncode})"
        )
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "versions": versions,
        "nvidia": gpu,
        "vulkan_icds": [
            str(p)
            for root in ["/usr/share/vulkan/icd.d", "/etc/vulkan/icd.d"]
            for p in Path(root).glob("*.json")
        ],
        "note": "CPU physics is required first. CPU-only PyTorch does not diagnose Vulkan rendering support. No driver installation is attempted.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = preflight()
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
