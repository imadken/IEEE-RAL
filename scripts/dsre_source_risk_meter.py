"""Meter bounded offline campaign commands without shell interpretation."""

import argparse
import json
import resource
import subprocess
import time
from pathlib import Path


def main(root, label, command):
    if command and command[0] == "--":
        command = command[1:]
    if not command or not label.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Explicit command and simple unique label required")
    folder = root / "metered"
    folder.mkdir(exist_ok=True)
    dest = folder / (label + ".json")
    if dest.exists():
        raise ValueError("Preserve prior measured attempts")
    start, before = time.monotonic(), resource.getrusage(resource.RUSAGE_CHILDREN)
    with (folder / (label + ".log")).open("x") as stream:
        child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        try:
            status = child.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            status = -15
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = {
        "command": command,
        "status": status,
        "wall_seconds": time.monotonic() - start,
        "cpu_seconds": after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime,
        "peak_child_rss_kib": after.ru_maxrss,
        "epoch": time.time(),
    }
    temporary = dest.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(dest)
    print(json.dumps(record), flush=True)
    if status:
        raise SystemExit(status if status > 0 else 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("label")
    p.add_argument("command", nargs=argparse.REMAINDER)
    a = p.parse_args()
    main(a.root, a.label, a.command)
