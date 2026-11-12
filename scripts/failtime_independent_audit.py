"""Independent FailTime annotation, raw-trajectory and provenance verification.

This analyzer imports no runtime model, feature extractor, acquisition code or
alarm scorer. Video datasets are inventoried by name only and never decoded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Literal

import h5py
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ReleasedAnnotation(BaseModel):
    """Validate essential released fields without changing descriptive labels."""

    model_config = ConfigDict(extra="allow", allow_inf_nan=False, strict=True)
    sample: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    episode: str = Field(min_length=1)
    robot: str = Field(min_length=1)
    hdf5: str = Field(min_length=1)
    verdict: Literal["fail", "success"]
    onset: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_onset_and_path(self):
        if self.verdict == "fail" and self.onset is None:
            raise ValueError("Failure lacks released onset")
        path = Path(self.hdf5)
        if path.is_absolute() or ".." in path.parts or path.suffix != ".hdf5":
            raise ValueError("Unsafe or non-HDF5 episode path")
        return self


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def validate_rows(raw: list[dict]) -> tuple[list[ReleasedAnnotation], list[dict]]:
    """Retain each invalid row and duplicated physical identifier explicitly."""
    records, problems = [], []
    samples, physical = set(), set()
    for index, row in enumerate(raw):
        try:
            record = ReleasedAnnotation.model_validate(row)
        except ValidationError as exc:
            problems.append(
                {"index": index, "sample": row.get("sample"), "error": str(exc)}
            )
            continue
        key = (record.robot, record.hdf5)
        if record.sample in samples or key in physical:
            problems.append(
                {
                    "index": index,
                    "sample": record.sample,
                    "error": "Duplicated sample or source HDF5 identifier",
                }
            )
        samples.add(record.sample)
        physical.add(key)
        records.append(record)
    return records, problems


def annotation_counts(records: list[ReleasedAnnotation]) -> dict:
    task_counts = defaultdict(Counter)
    platform_counts = defaultdict(Counter)
    for record in records:
        task_counts[(record.robot, record.task_id)][record.verdict] += 1
        platform_counts[record.robot][record.verdict] += 1
    return {
        "episodes": len(records),
        "failures": sum(r.verdict == "fail" for r in records),
        "successes": sum(r.verdict == "success" for r in records),
        "tasks": len(task_counts),
        "platforms": {
            key: dict(value) for key, value in sorted(platform_counts.items())
        },
        "per_task": [
            {
                "robot": robot,
                "task_id": task,
                "failures": counts["fail"],
                "successes": counts["success"],
            }
            for (robot, task), counts in sorted(task_counts.items())
        ],
    }


def check_arrays(times: np.ndarray, eef: np.ndarray, onset: float | None) -> dict:
    """Require continuous finite samples; distinguish onset and follow-up support."""
    problems = []
    times, eef = np.asarray(times), np.asarray(eef)
    if times.ndim != 1 or len(times) < 2:
        problems.append("Insufficient one-dimensional timestamp sequence")
    if eef.ndim != 2 or eef.shape != (len(times), 16):
        problems.append("Expected one 16-channel bimanual state_eef row per timestamp")
    if not np.isfinite(times).all() or not np.isfinite(eef).all():
        problems.append("Nonfinite timestamps or proprioception")
    if problems:
        return {
            "valid": False,
            "problems": problems,
            "onset_in_bounds": False,
            "full_delay_window_observable": False,
        }
    intervals = np.diff(times)
    if np.any(intervals <= 0):
        problems.append("Timestamps do not increase strictly")
    else:
        median = float(np.median(intervals))
        if np.max(intervals) > 1.5 * median + 2e-5:
            problems.append("Missing sample-sized gaps in raw trajectory")
    if times[0] < -2e-6:
        problems.append("Negative initial timestamp")
    onset_valid = (
        onset is None or float(times[0]) - 2e-6 <= onset <= float(times[-1]) + 2e-6
    )
    if not onset_valid:
        problems.append("Released onset outside actual timestamps")
    return {
        "valid": not problems,
        "problems": problems,
        "frames": len(times),
        "start": float(times[0]),
        "end": float(times[-1]),
        "median_hz": float(1 / np.median(intervals)) if (intervals > 0).all() else None,
        "maximum_sample_gap": float(intervals.max()),
        "onset_in_bounds": bool(onset_valid),
        "full_delay_window_observable": bool(
            onset is not None and onset + 1 <= times[-1] + 2e-6
        ),
        "pre_onset_frames": int(np.sum(times < onset)) if onset is not None else None,
    }


def inspect_hdf5(path: Path, annotation: ReleasedAnnotation) -> dict:
    record = {
        "path": str(path),
        "sample": annotation.sample,
        "task_id": annotation.task_id,
        "robot": annotation.robot,
        "verdict": annotation.verdict,
    }
    if not path.is_file():
        return {
            **record,
            "available": False,
            "valid": False,
            "problems": ["Raw HDF5 unavailable"],
        }
    try:
        with h5py.File(path, "r") as stream:
            if "observation.state_eef" not in stream or "timestamp" not in stream:
                return {
                    **record,
                    "available": True,
                    "valid": False,
                    "problems": ["Missing actual timestamp or state_eef dataset"],
                }
            times = np.asarray(stream["timestamp"][:], dtype=np.float64)
            state = np.asarray(stream["observation.state_eef"][:], dtype=np.float64)
            result = check_arrays(times, state, annotation.onset)
            dataset_shapes = {
                key: list(value.shape)
                for key, value in stream.items()
                if isinstance(value, h5py.Dataset)
            }
            views = [key for key in stream if key.startswith("observation.images.")]
            attrs = {
                str(key): value.item() if isinstance(value, np.generic) else str(value)
                for key, value in stream.attrs.items()
            }
        signature = hashlib.sha256(
            np.ascontiguousarray(times).tobytes()
            + np.ascontiguousarray(state).tobytes()
        ).hexdigest()
        return {
            **record,
            **result,
            "available": True,
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "numeric_recording_sha256": signature,
            "dataset_shapes": dataset_shapes,
            "camera_groups_unread": views,
            "attributes": attrs,
            "time_source": "Actual timestamp dataset, not inferred fps",
        }
    except (OSError, ValueError, KeyError) as exc:
        return {**record, "available": True, "valid": False, "problems": [repr(exc)]}


def compare_releases(first: list[dict], second: list[dict]) -> dict:
    left = {r["sample"]: r for r in first}
    right = {r["sample"]: r for r in second}
    common = set(left) & set(right)
    return {
        "first": len(first),
        "second": len(second),
        "common": len(common),
        "first_only": sorted(set(left) - set(right)),
        "second_only": sorted(set(right) - set(left)),
        "changed_records": sorted(key for key in common if left[key] != right[key]),
    }


def audit(root: Path) -> dict:
    source_files = {}
    populations = {}
    schema_errors = {}
    records_by_split = {}
    for directory in ("metadata", "upstream/data"):
        for path in sorted((root / directory).glob("failtime_*/*.json")):
            key = str(path.relative_to(root))
            raw = read(path)
            validated, problems = validate_rows(raw)
            source_files[key] = digest(path)
            populations[key] = annotation_counts(validated)
            schema_errors[key] = problems
            records_by_split[key] = raw
    long_key = "metadata/failtime_long/test.json"
    long_rows, long_errors = validate_rows(records_by_split[long_key])
    tree = {
        entry["path"]: entry
        for entry in read(root / "hf_tree.json")
        if entry["type"] == "file"
    }
    source_files["hf_tree.json"] = digest(root / "hf_tree.json")
    source_files["hf_metadata.json"] = digest(root / "hf_metadata.json")
    checks = []
    for annotation in long_rows:
        filename = "failtime_long/" + annotation.hdf5
        entry = tree.get(filename)
        candidates = sorted(
            p for p in root.rglob(Path(annotation.hdf5).name) if p.is_file()
        )
        candidate = (
            candidates[0]
            if candidates
            else root / "unavailable" / Path(annotation.hdf5).name
        )
        result = inspect_hdf5(candidate, annotation)
        result.update(
            hf_path=filename,
            hf_entry_present=entry is not None,
            mirrors=[str(p) for p in candidates[1:]],
        )
        if entry and result["available"] and result.get("sha256"):
            expected = entry.get("lfs", {}).get("oid")
            result["hf_lfs_sha256"] = expected
            result["hf_size"] = entry["size"]
            result["file_identity_verified"] = bool(
                expected
                and expected == result["sha256"]
                and entry["size"] == result["bytes"]
            )
            if not result["file_identity_verified"]:
                result["valid"] = False
                result["problems"].append(
                    "Actual HDF5 bytes do not match pinned HF LFS hash/size"
                )
        else:
            result["file_identity_verified"] = False
            result["valid"] = False
        checks.append(result)
    verified = [r for r in checks if r["valid"] and r["file_identity_verified"]]
    duplicates = defaultdict(list)
    for row in verified:
        duplicates[row["numeric_recording_sha256"]].append(row["sample"])
    aliases = [ids for ids in duplicates.values() if len(ids) > 1]
    unique_verified = {r["numeric_recording_sha256"]: r for r in verified}.values()
    verified_counts = Counter(r["verdict"] for r in unique_verified)
    verified_tasks = {(r["robot"], r["task_id"]) for r in unique_verified}
    g0 = (
        not long_errors
        and verified_counts["fail"] >= 40
        and verified_counts["success"] >= 25
        and len(verified_tasks) >= 2
    )
    overlap = []
    comparisons = []
    keys = sorted(records_by_split)
    for index, left in enumerate(keys):
        for right in keys[index + 1 :]:
            if "failtime_short/" in left and "failtime_short/" in right:
                a = {(r["robot"], r["hdf5"]) for r in records_by_split[left]}
                b = {(r["robot"], r["hdf5"]) for r in records_by_split[right]}
                overlap.append(
                    {
                        "first": left,
                        "second": right,
                        "shared_source_recordings": len(a & b),
                    }
                )
    for cohort in ("long", "short"):
        for split in ("train", "calibration", "test"):
            a, b = (
                f"metadata/failtime_{cohort}/{split}.json",
                f"upstream/data/failtime_{cohort}/{split}.json",
            )
            if a in records_by_split and b in records_by_split:
                comparisons.append(
                    {
                        "hf": a,
                        "github": b,
                        **compare_releases(records_by_split[a], records_by_split[b]),
                    }
                )
    return {
        "status": "PASS"
        if not any(schema_errors.values())
        else "ANNOTATION_SCHEMA_PROBLEMS",
        "scope": "Independent annotation and raw-file audit; no model, primary loader or scorer imported",
        "hf_revision": read(root / "hf_metadata.json")["sha"],
        "github_revision": read(root / "upstream/github_commit.json")["sha"],
        "source_sha256": source_files,
        "metadata_populations": populations,
        "schema_errors": schema_errors,
        "release_comparisons": comparisons,
        "short_split_overlap": overlap,
        "long_annotated_file_inventory_count": sum(
            "failtime_long/episodes/" in key and key.endswith(".hdf5") for key in tree
        ),
        "long_declared_hdf5_bytes": sum(
            entry["size"]
            for key, entry in tree.items()
            if key.startswith("failtime_long/episodes/") and key.endswith(".hdf5")
        ),
        "short_raw_hdf5_files_in_failtime_inventory": sum(
            key.startswith("failtime_short/") and key.endswith(".hdf5") for key in tree
        ),
        "raw_episode_checks": checks,
        "numeric_duplicate_aliases": aliases,
        "verified_independent_raw_failures": verified_counts["fail"],
        "verified_independent_raw_successes": verified_counts["success"],
        "verified_raw_task_groups": len(verified_tasks),
        "G0": "DATA_GO" if g0 else "DATA_BLOCKED",
        "G0_requirements": "At least40 independently identified raw failures,25 raw successes,2 task groups; actual finite continuous proprioception and released onset within actual time bounds; pinned file hash/size verified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    result = audit(args.root)
    (args.root / "independent_data_audit.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "G0",
                    "verified_independent_raw_failures",
                    "verified_independent_raw_successes",
                    "verified_raw_task_groups",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
