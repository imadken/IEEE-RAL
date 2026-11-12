"""Bounded immutable FailTime metadata and fixed-fixture acquisition."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_SHA = "63dafa9b703be0347d80f63d049304269f8d000f"
DATASET = "ChangUoA/FailTime"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fetch(root, url, path, limit=2_000_000):
    """One bounded public request, no retries, with every received byte recorded."""
    used = sum(
        json.loads(s).get("bytes", 0)
        for s in (root / "downloads.jsonl").read_text().splitlines()
    )
    if used + limit > 8_000_000_000:
        raise ValueError("Download reservation exceeds campaign cap")
    start = time.monotonic()
    record = {"url": url, "path": str(path.relative_to(root)), "bytes": 0}
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            body = response.read(limit + 1)
            record.update(
                status=response.status,
                bytes=len(body),
                sha256=hashlib.sha256(body).hexdigest(),
            )
            if len(body) > limit:
                raise ValueError("Response exceeded reserved request size")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            return body
    except (urllib.error.URLError, ValueError) as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["wall_seconds"] = time.monotonic() - start
        with (root / "downloads.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")


def metadata(root):
    revision = json.loads((root / "hf_metadata.json").read_text())["sha"]
    fetch(
        root,
        f"https://huggingface.co/api/datasets/{DATASET}/tree/{revision}?recursive=true&expand=false&limit=1000",
        root / "hf_tree.json",
    )
    for name in (
        "README.md",
        "failtime_long/test.json",
        "failtime_short/train.json",
        "failtime_short/test.json",
    ):
        fetch(
            root,
            f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{name}",
            root / "metadata" / name,
        )
    for name in (
        "README.md",
        "protracer/data.py",
        "protracer/changepoint.py",
        "protracer/evaluation.py",
        "data/failtime_long/test.json",
        "data/failtime_short/train.json",
        "data/failtime_short/calibration.json",
        "data/failtime_short/test.json",
    ):
        fetch(
            root,
            f"https://raw.githubusercontent.com/Chang-AIML/ProTracer/{GITHUB_SHA}/code/{name}",
            root / "upstream" / name,
        )
    rows = json.loads((root / "metadata/failtime_long/test.json").read_text())
    classes = sorted({(r["robot"], r["verdict"]) for r in rows})
    selected = []
    # Fixed class order, then SHA-256(task/episode) lexicographic order; maximum three.
    for robot, verdict in classes:
        choices = sorted(
            [r for r in rows if (r["robot"], r["verdict"]) == (robot, verdict)],
            key=lambda r: hashlib.sha256(
                (r["task_id"] + "/" + r["sample"]).encode()
            ).hexdigest(),
        )
        if choices and len(selected) < 3:
            selected.append(choices[0])
    save(
        root / "fixture_selection.json",
        {
            "rule": "Sorted (robot,verdict), first SHA256(task_id/sample) per class; maximum three before any raw signals",
            "available_classes": classes,
            "selected": selected,
        },
    )
    tree = json.loads((root / "hf_tree.json").read_text())
    print(
        json.dumps(
            {
                "revision": revision,
                "long_annotations": len(rows),
                "hdf5_files": sum(r["path"].endswith(".hdf5") for r in tree),
                "hdf5_bytes": sum(
                    r.get("size", 0) for r in tree if r["path"].endswith(".hdf5")
                ),
                "fixtures": [r["sample"] for r in selected],
            }
        )
    )


def fixtures(root):
    """Download complete fixed fixtures only if their declared sizes fit the cap."""
    revision = json.loads((root / "hf_metadata.json").read_text())["sha"]
    tree = {r["path"]: r for r in json.loads((root / "hf_tree.json").read_text())}
    records = []
    for row in json.loads((root / "fixture_selection.json").read_text())["selected"]:
        name = "failtime_long/" + row["hdf5"]
        entry = tree[name]
        destination = root / "fixtures" / Path(name).name
        try:
            body = fetch(
                root,
                f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{name}",
                destination,
                entry["size"],
            )
            expected = entry.get("lfs", {}).get("oid")
            digest = hashlib.sha256(body).hexdigest()
            if expected and digest != expected:
                raise ValueError("LFS SHA256 mismatch")
            records.append(
                {
                    "sample": row["sample"],
                    "path": str(destination.relative_to(root)),
                    "sha256": digest,
                    "bytes": len(body),
                    "status": "downloaded",
                }
            )
        except (urllib.error.URLError, ValueError) as exc:
            records.append(
                {"sample": row["sample"], "status": "unavailable", "error": str(exc)}
            )
    save(root / "fixture_acquisition.json", records)
    print(json.dumps(records))


def cohort(root):
    import h5py
    import numpy as np

    revision = json.loads((root / "hf_metadata.json").read_text())["sha"]
    tree = {r["path"]: r for r in json.loads((root / "hf_tree.json").read_text())}
    rows = json.loads((root / "metadata/failtime_long/test.json").read_text())
    result = []
    for row in sorted(
        rows,
        key=lambda r: hashlib.sha256(
            (r["task_id"] + "/" + r["sample"]).encode()
        ).hexdigest(),
    ):
        name = "failtime_long/" + row["hdf5"]
        entry = tree[name]
        fixture = root / "fixtures" / Path(name).name
        destination = fixture if fixture.exists() else root / "raw" / Path(name).name
        record = {
            **row,
            "path": str(destination.relative_to(root)),
            "expected_sha256": entry["lfs"]["oid"],
        }
        try:
            if not destination.exists():
                fetch(
                    root,
                    f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{name}",
                    destination,
                    entry["size"],
                )
            with destination.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != entry["lfs"]["oid"]:
                raise ValueError("LFS hash mismatch")
            with h5py.File(destination, "r") as f:
                t = np.asarray(f["timestamp"][:], dtype=np.float64).reshape(-1)
                eef = np.asarray(f["observation.state_eef"][:], dtype=np.float64)
                frame = f["frame_index"][:]
                schema = {
                    k: {"shape": list(f[k].shape), "dtype": str(f[k].dtype)}
                    for k in f
                    if isinstance(f[k], h5py.Dataset)
                }
                views = [k for k in f if k.startswith("observation.images.")]
            assert eef.shape == (len(t), 16) and len(t) > 2, "EEF shape/support"
            assert (
                np.isfinite(t).all()
                and np.isfinite(eef).all()
                and (np.diff(t) > 0).all()
            ), "Invalid continuous signals"
            assert np.array_equal(frame, np.arange(len(t))), (
                "Nonconsecutive frame index"
            )
            assert abs(t[0]) < 1e-6, "Episode does not start at zero"
            if row["verdict"] == "fail":
                assert np.isfinite(row["onset"]) and row["onset"] >= 0, (
                    "Invalid onset value"
                )
            path = root / "arrays" / (row["sample"] + ".npz")
            path.parent.mkdir(exist_ok=True)
            np.savez_compressed(path, time=t, eef=eef)
            record.update(
                status="verified",
                onset_within_observed=bool(
                    row["verdict"] != "fail" or t[0] <= row["onset"] <= t[-1]
                ),
                sha256=digest,
                frames=len(t),
                duration=float(t[-1]),
                median_dt=float(np.median(np.diff(t))),
                schema=schema,
                views=views,
                arrays=str(path.relative_to(root)),
                arrays_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                timely_window_fully_observable=bool(
                    row["verdict"] != "fail" or row["onset"] + 1 <= t[-1]
                ),
                signal_sha256=hashlib.sha256(t.tobytes() + eef.tobytes()).hexdigest(),
            )
        except (
            urllib.error.URLError,
            ValueError,
            AssertionError,
            OSError,
            KeyError,
        ) as exc:
            record.update(status="unavailable_or_invalid", error=str(exc))
        result.append(record)
        save(root / "cohort_qualification.json", result)
        if len(result) % 10 == 0:
            print(
                json.dumps(
                    {
                        "completed": len(result),
                        "verified": sum(r["status"] == "verified" for r in result),
                    }
                ),
                flush=True,
            )
    valid = [r for r in result if r["status"] == "verified"]
    fail = sum(r["verdict"] == "fail" and r["onset_within_observed"] for r in valid)
    success = sum(r["verdict"] == "success" for r in valid)
    duplicates = len(valid) - len({r["signal_sha256"] for r in valid})
    gate = {
        "status": "DATA_GO"
        if fail >= 40
        and success >= 25
        and len({r["task_id"] for r in valid}) >= 2
        and duplicates == 0
        else "DATA_BLOCKED",
        "verified_failures": fail,
        "verified_references": success,
        "verified_tasks": len({r["task_id"] for r in valid}),
        "unavailable_or_invalid": len(result) - len(valid),
        "signal_duplicates": duplicates,
        "declared": len(result),
        "verified_signal_recordings": len(valid),
        "failure_onsets_outside_observation": sum(
            r["verdict"] == "fail" and not r["onset_within_observed"] for r in valid
        ),
    }
    save(root / "data_gate.json", gate)
    print(json.dumps(gate))


def short_access(root):
    """Pin original Short source and match fixed IDs without favorable selection."""
    source = "sii-rhos-ai/ViFailback-Dataset"
    body = fetch(
        root,
        f"https://huggingface.co/api/datasets/{source}?expand%5B%5D=sha",
        root / "short_access/metadata.json",
    )
    info = json.loads(body)
    revision = info["sha"]
    results = []
    cache = {}
    for split in ("train", "calibration", "test"):
        rows = json.loads(
            (root / f"upstream/data/failtime_short/{split}.json").read_text()
        )
        row = min(
            rows,
            key=lambda r: hashlib.sha256(
                (r["task_id"] + "/" + r["sample"]).encode()
            ).hexdigest(),
        )
        task = row["task_id"]
        try:
            if task not in cache:
                data = fetch(
                    root,
                    f"https://huggingface.co/api/datasets/{source}/tree/{revision}/raw_data/{task}?recursive=true&limit=1000",
                    root / f"short_access/{task}.json",
                )
                cache[task] = json.loads(data)
            target = "raw_data/" + row["hdf5"].removeprefix("episodes/")
            found = next((r for r in cache[task] if r["path"] == target), None)
            results.append(
                {
                    "split": split,
                    "sample": row["sample"],
                    "task_id": task,
                    "expected_raw_path": target,
                    "entry": found,
                    "matching_task_bytes": sum(
                        r.get("size", 0) for r in cache[task] if r["type"] == "file"
                    ),
                    "raw_downloaded": False,
                }
            )
        except urllib.error.URLError as exc:
            results.append(
                {
                    "split": split,
                    "sample": row["sample"],
                    "error": str(exc),
                    "raw_downloaded": False,
                }
            )
    save(
        root / "short_access.json",
        {
            "repository": source,
            "revision": revision,
            "selection": "First SHA256(task_id/sample) in each released split; annotation matching only",
            "results": results,
            "disposition": "Original raw source is public; full official Short cohort is not qualified within remaining campaign transfer budget. No Short training, official-test claim, or partial favorable comparison. Preserve train/calibration overlap evidence.",
        },
    )
    print(json.dumps(results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("metadata", "fixtures", "cohort", "short-access"),
        required=True,
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {
        "metadata": metadata,
        "fixtures": fixtures,
        "cohort": cohort,
        "short-access": short_access,
    }[args.stage](args.root)


if __name__ == "__main__":
    main()
