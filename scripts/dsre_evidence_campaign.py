"""Fixed pilot manifests and bounded foreground execution, without tuning."""

import argparse
import gzip
import hashlib
import json
import os
import re
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

from dual_rec.evidence_aware.views import save, seed, sha

ROOT = Path("results/dsre-evidence-aware/20261117-first-session")
TASKS = ("PegInsertionSide-v1", "PointMaze_UMaze-v3")


def freeze(root):
    historic = set()
    for current, dirs, _ in os.walk("results"):
        dirs[:] = [
            d
            for d in dirs
            if d
            not in ("cache", "env", "navigation_env", "review_packet", "prior_packet")
        ]
        for name in dirs:
            match = re.match(r"^(\d{3,})(?:-|$)", name)
            if match:
                historic.add(int(match.group(1)))
    used = set(historic)
    cohorts = {}
    collisions = []
    for task in TASKS + ("PickCube-v1",):
        cohorts[task] = {}
        for phase, count in (
            ("pilot", 10),
            ("development", 64),
            ("discovery", 128),
            ("calibration", 1024),
            ("test", 256),
        ):
            rows = []
            for index in range(count):
                number = seed(task, phase, index)
                attempt = 0
                while number in used:
                    attempt += 1
                    number = seed(task, phase + f":collision{attempt}", index)
                if attempt:
                    collisions.append([task, phase, index, attempt])
                used.add(number)
                offsets = (
                    (0.0, 0.003, -0.003, 0.006, -0.006)
                    if task == TASKS[0]
                    else ((0, 0), (0.35, 0), (-0.35, 0), (0, 0.35), (0, -0.35))
                    if task == TASKS[1]
                    else (0.0, 0.01, 0.02, 0.03, -0.02)
                )
                offset = (
                    offsets[index // 2]
                    if phase == "pilot"
                    else offsets[
                        int.from_bytes(
                            hashlib.sha256(
                                f"dsre-evidence-v2:condition:{task}:{number}".encode()
                            ).digest(),
                            "big",
                        )
                        % 5
                    ]
                )
                rows.append(
                    {
                        "task": task,
                        "phase": phase,
                        "index": index,
                        "seed": number,
                        "offset": offset,
                    }
                )
            cohorts[task][phase] = rows
    save(
        root / "prospective_manifest.json",
        {
            "cohorts": cohorts,
            "historic_seed_ids_checked": len(historic),
            "collisions": collisions,
            "frozen_epoch": time.time(),
            "source_sha256": {
                p: sha(Path(p))
                for p in (
                    "scripts/dsre_evidence_tasks.py",
                    "scripts/dsre_evidence_campaign.py",
                )
            },
            "execution": "Only 10-parent pilots and conditional <=64 development parents authorized this session. Full 128/1024/256 cohorts remain unexecuted.",
            "primary": {
                "harm": 0.10,
                "gain": 0.05,
                "delta_L": 0.025,
                "delta_P": 0.025,
                "tolls": [0, 0.02, 0.05],
            },
            "limits": {
                "session_wall_seconds": 43200,
                "new_physics_wall_seconds": 21600,
                "cpu_seconds": 43200,
                "new_artifact_bytes": 2 * 1024**3,
                "download_bytes": 1024**3,
            },
        },
    )


def child(root, spec, action, label, tag=""):
    task = spec["task"]
    directory = root / "physics" / task / (spec["phase"] + tag) / str(spec["index"])
    directory.mkdir(parents=True, exist_ok=True)
    specpath = directory / "spec.json"
    if not specpath.exists():
        save(specpath, spec)
    assert json.loads(specpath.read_text()) == spec
    output = directory / (label + ".json.gz")
    if output.exists():
        receipt = directory / (label + ".execution.json")
        if not receipt.exists():
            raise RuntimeError(
                "Incomplete branch has no execution receipt; preserve it"
            )
        source = Path(
            "scripts/dsre_evidence_grasp.py"
            if task == "PickCube-v1"
            else "scripts/dsre_evidence_tasks.py"
        )
        if json.loads(receipt.read_text())["source_sha256"] != sha(source):
            raise RuntimeError("Resume requires the exact frozen worker source")
        with gzip.open(output, "rt") as stream:
            cached = json.load(stream)
        if cached["spec"] != spec or cached["action"] != action:
            raise RuntimeError("Cached branch identity mismatch")
        return cached
    python = (
        (root / "navigation_env/bin/python").absolute()
        if task == TASKS[1]
        else Path(sys.executable)
    )
    env = os.environ.copy()
    env.update(
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        CUDA_VISIBLE_DEVICES="",
        VK_ICD_FILENAMES="/usr/share/vulkan/icd.d/lvp_icd.x86_64.json",
        PYTHONDONTWRITEBYTECODE="1",
    )
    # Navigation uses only its isolated packages and the controller script.
    if task == TASKS[1]:
        env.pop("PYTHONPATH", None)
    started = time.time()
    source_hash = sha(
        Path(
            "scripts/dsre_evidence_grasp.py"
            if task == "PickCube-v1"
            else "scripts/dsre_evidence_tasks.py"
        )
    )
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    command = [
        str(python),
        "scripts/dsre_evidence_grasp.py"
        if task == "PickCube-v1"
        else "scripts/dsre_evidence_tasks.py",
        str(specpath),
        str(output),
        "--action",
        action,
    ]
    with (directory / (label + ".log")).open("x") as log:
        proc = subprocess.Popen(
            command,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            status = proc.wait(timeout=180 if task == TASKS[0] else 40)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            status = proc.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    usage = {
        "command": command,
        "returncode": status,
        "started_epoch": started,
        "finished_epoch": time.time(),
        "wall_seconds": time.time() - started,
        "cpu_seconds": after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime,
        "source_sha256": source_hash,
    }
    save(directory / (label + ".execution.json"), usage)
    if not output.exists():
        result = {
            "status": "NATIVE_OR_PROCESS_FAILURE",
            "returncode": status,
            "spec": spec,
            "action": action,
        }
        with gzip.open(output, "xt") as f:
            json.dump(result, f)
    with gzip.open(output, "rt") as f:
        result = json.load(f)
    return result


def pilot(root, task, tag=""):
    manifest = json.loads((root / "prospective_manifest.json").read_text())
    results = []
    start = time.time()
    for spec in manifest["cohorts"][task]["pilot"]:
        if time.time() - start > 5400:
            results.append({"spec": spec, "status": "NOT_RUN_SETUP_CAP"})
            continue
        branches = {}
        for action in ("c", "r"):
            branches[action] = child(root, spec, action, action, tag)
            if branches[action]["status"] == "COMPLETE":
                branches[action + "_repeat"] = child(
                    root, spec, action, action + "_repeat", tag
                )
        results.append(
            {
                "spec": spec,
                "statuses": {a: r["status"] for a, r in branches.items()},
                "outcomes": {a: r.get("success") for a, r in branches.items()},
            }
        )
        print(json.dumps(results[-1]), flush=True)
    save(
        root / (task + "-pilot" + tag + "-attempts.json"),
        {"attempts": results, "wall_seconds": time.time() - start},
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("freeze", "pilot"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--attempt-tag", default="")
    args = parser.parse_args()
    if args.stage == "freeze":
        freeze(args.root)
    else:
        pilot(args.root, args.task, args.attempt_tag)


if __name__ == "__main__":
    main()
