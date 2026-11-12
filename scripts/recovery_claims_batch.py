"""Sequential process-isolated fixed parents with exact-seed retry and a failure ledger."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--root", type=Path, required=True)
p.add_argument("--split", required=True)
a = p.parse_args()
cfg = json.loads((a.root / "registration.json").read_text())
freeze_path = a.root / "confirmation_freeze.json"


def verify_frozen_sources():
    if a.split == "confirmation":
        frozen = json.loads(freeze_path.read_text())
        for name, expected in frozen["source_sha256"].items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
                raise RuntimeError(f"Frozen confirmation source changed: {name}")


verify_frozen_sources()
for task in cfg["tasks"]:
    for seed in cfg["seeds"][task][a.split]:
        for condition in cfg["conditions"][task]:
            verify_frozen_sources()
            destination = a.root / "parents" / a.split / task / f"{seed}-{condition}"
            if (destination / "checkpoint.json").exists():
                continue
            for attempt in range(2):
                t = time.monotonic()
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "scripts/recovery_claims_physics.py",
                            "--root",
                            str(a.root),
                            "--task",
                            task,
                            "--split",
                            a.split,
                            "--seed",
                            str(seed),
                            "--condition",
                            condition,
                        ],
                        timeout=300,
                        check=False,
                    )
                    code = result.returncode
                except subprocess.TimeoutExpired:
                    code = 124
                row = {
                    "task": task,
                    "seed": seed,
                    "condition": condition,
                    "split": a.split,
                    "attempt": attempt,
                    "exit_status": code,
                    "wall_seconds": time.monotonic() - t,
                }
                with (a.root / "parent_attempts.jsonl").open("a") as f:
                    f.write(json.dumps(row) + "\n")
                if code == 0 or (destination / "checkpoint.json").exists():
                    break
                if destination.exists():
                    failed = a.root / "failed_attempts"
                    failed.mkdir(exist_ok=True)
                    destination.rename(
                        failed / f"{a.split}-{task}-{seed}-{condition}-{attempt}"
                    )
