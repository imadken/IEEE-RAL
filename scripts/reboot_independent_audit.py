"""Recompute REBOOT validity from saved bytes without importing the main auditor."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class ArchivedRangeFile(io.RawIOBase):
    """Offline reconstruction from validated saved ranges; never fetches a gap."""

    def __init__(self, root, manifest):
        super().__init__()
        self.size, self.position = manifest["original_size"], 0
        self.pieces = []
        for row in manifest["ranges"]:
            path = root / row["path"]
            if digest(path) != row["sha256"]:
                raise ValueError("Archived range hash changed")
            body = path.read_bytes()
            if len(body) != row["end"] - row["start"] + 1:
                raise ValueError("Archived range length changed")
            self.pieces.append((row["start"], row["end"] + 1, body))

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        target = (
            offset
            if whence == 0
            else self.position + offset
            if whence == 1
            else self.size + offset
        )
        if not 0 <= target <= self.size:
            raise ValueError("Archived seek outside source bounds")
        self.position = target
        return target

    def read(self, count=-1):
        count = (
            self.size - self.position
            if count < 0
            else min(count, self.size - self.position)
        )
        target, cursor, pieces = self.position + count, self.position, []
        while cursor < target:
            candidates = [p for p in self.pieces if p[0] <= cursor < p[1]]
            if not candidates:
                raise ValueError(
                    "Requested bytes were not acquired; refusing to fill a gap"
                )
            start, end, body = max(candidates, key=lambda p: p[1])
            end = min(end, target)
            pieces.append(body[cursor - start : end - start])
            cursor = end
        self.position = target
        return b"".join(pieces)


def independently_check_annotation(raw, frames):
    bounds = [raw["phase_boundaries"][f"tau_{i}"] for i in range(6)]
    failure = raw.get("failure") or {}
    onset = failure.get("induced_at_frame", failure.get("t_f"))
    recovery = failure.get("recovery_started_at_frame", failure.get("t_r"))
    valid = onset in frames and recovery in frames and onset < recovery
    phase = None
    ordered = all(bounds[i] < bounds[i + 1] for i in range(5))
    if ordered:
        for index in range(5):
            if bounds[index] <= onset < bounds[index + 1]:
                phase = index + 1
                break
    return {
        "event_frames_in_bounds": bool(valid),
        "pre_recovery_frames": int(np.sum((frames >= onset) & (frames < recovery)))
        if valid
        else None,
        "origin_phase_at_onset": phase,
        "origin_matches_half_open_phase": phase == failure["originating_phase"]
        if ordered
        else None,
        "onset_on_phase_boundary": onset in bounds[1:-1] if ordered else None,
    }


def main():
    import pyarrow.parquet as pq

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    main_result = json.loads((root / "qualification.json").read_text())
    registration = json.loads((root / "repository_registration.json").read_text())
    columns = [
        "action",
        "observation.state",
        "timestamp",
        "frame_index",
        "episode_index",
        "index",
        "task_index",
    ]
    frames_by_id = defaultdict(list)
    hashes = defaultdict(list)
    projection_count = range_count = row_count = 0
    failures = []
    for path in sorted((root / "ranges").rglob("manifest.json")):
        record = json.loads(path.read_text())
        projection = root / record["projection"]
        if digest(projection) != record["projection_sha256"]:
            failures.append(str(projection) + ": projection hash")
            continue
        archived = ArchivedRangeFile(root, record)
        original = pq.ParquetFile(archived, pre_buffer=False).read(
            columns=columns, use_threads=False
        )
        saved = pq.ParquetFile(projection).read()
        if not original.equals(saved):
            failures.append(str(projection) + ": original range values differ")
        assert set(saved.column_names) == set(columns)
        episodes = np.asarray(saved["episode_index"])
        assert len(set(episodes)) == 1, (
            "Unexpected multi-episode source file needs explicit joining audit"
        )
        episode = int(episodes[0])
        frames = np.asarray(saved["frame_index"])
        frames_by_id[(record["repository"], episode)].append(frames)
        q = np.array(saved["observation.state"].to_pylist(), dtype="<f4")
        a = np.array(saved["action"].to_pylist(), dtype="<f4")
        t = np.array(saved["timestamp"], dtype="<f4")
        signature = hashlib.sha256(q.tobytes() + a.tobytes() + t.tobytes()).hexdigest()
        hashes[signature].append((record["repository"], episode))
        projection_count += 1
        range_count += len(record["ranges"])
        row_count += len(saved)
    annotations = {
        (r["repository"], r["episode"]): r for r in main_result["annotations"]
    }
    checked_annotations, independently_invalid = [], []
    pilot_annotation_files = 0
    metadata_counts, metadata_integrity, published_corrupt_metadata = [], [], []
    duration_buckets = defaultdict(Counter)
    for repo in registration["repositories"]:
        base = root / "data" / repo["id"].split("/")[1]
        phase_path = base / "meta/phase.json"
        pilot_annotation_files += int(
            repo["role"] != "sample_engineering_only" and phase_path.exists()
        )
        info = json.loads((base / "meta/info.json").read_text())
        tree = json.loads((base / "tree.json").read_text())
        for entry in tree:
            path = base / entry["path"]
            if entry["type"] != "file" or not path.is_file():
                continue
            content = path.read_bytes()
            expected = entry.get("lfs", {}).get("oid", entry["oid"])
            measured = (
                hashlib.sha256(content).hexdigest()
                if entry.get("lfs")
                else hashlib.sha1(
                    b"blob " + str(len(content)).encode() + b"\0" + content
                ).hexdigest()
            )
            if measured != expected or len(content) != entry["size"]:
                failures.append(str(path) + ": published metadata hash/size")
            metadata_integrity.append(
                {
                    "repository": repo["id"],
                    "path": entry["path"],
                    "matches_published_hash": measured == expected,
                }
            )
            if entry["path"].startswith("meta/episodes/"):
                try:
                    pq.ParquetFile(path)
                except (ValueError, OSError) as exc:
                    published_corrupt_metadata.append(
                        {
                            "repository": repo["id"],
                            "path": entry["path"],
                            "published_hash_matches": measured == expected,
                            "error": str(exc),
                        }
                    )
        actual = {
            key[1]: np.concatenate(value)
            for key, value in frames_by_id.items()
            if key[0] == repo["id"]
        }
        matching = next(
            r for r in main_result["repositories"] if r["repository"] == repo["id"]
        )
        if (
            len(actual) != matching["projected_episodes"]
            or sum(map(len, actual.values())) != matching["projected_frames"]
        ):
            failures.append(repo["id"] + ": episode/frame aggregation")
        metadata_counts.append(
            {
                "repository": repo["id"],
                "declared_episodes": info["total_episodes"],
                "actual_episodes": len(actual),
                "actual_frames": sum(map(len, actual.values())),
            }
        )
        for episode, frames in actual.items():
            assert np.array_equal(frames, np.arange(len(frames)))
            if repo["role"] in {"expert", "recovery"}:
                duration_buckets[(repo["object"], repo["operation"], len(frames))][
                    repo["role"]
                ] += 1
        if phase_path.exists():
            for raw in json.loads(phase_path.read_text())["episodes"]:
                episode = int(raw["episode_index"])
                independent = independently_check_annotation(raw, actual[episode])
                if (repo["id"], episode) not in annotations:
                    assert not 1 <= raw["failure"]["originating_phase"] <= 5
                    assert any(
                        int(e["raw_episode_index"]) == episode
                        for e in matching["annotation_parse_errors"]
                    )
                    independently_invalid.append(
                        {
                            "episode": episode,
                            "invalid_origin_phase": raw["failure"]["originating_phase"],
                            "event_window_in_bounds": independent[
                                "event_frames_in_bounds"
                            ],
                        }
                    )
                    continue
                target = annotations[(repo["id"], episode)]
                if any(independent[k] != target[k] for k in independent):
                    failures.append(f"Annotation mismatch {repo['id']}/{episode}")
                checked_annotations.append(independent)
    recomputed_purity = sum(max(v.values()) for v in duration_buckets.values()) / sum(
        sum(v.values()) for v in duration_buckets.values()
    )
    assert (
        abs(recomputed_purity - main_result["descriptive_duration_role_purity"]) < 1e-12
    )
    assert (
        pilot_annotation_files
        == main_result["label_integrity"]["pilot_repositories_with_annotations"]
        == 0
    )
    assert (
        main_result["status"] == "DATA_BLOCKED" and main_result["models_trained"] == []
    )
    assert (
        main_result["B0_B7_results"] is None
        and main_result["method_comparison_intervals"] is None
    )
    actual_duplicates = {
        key: sorted(values) for key, values in hashes.items() if len(values) > 1
    }
    reported = {
        r["state_action_time_sha256"]: sorted(
            (v["repository"], v["episode"]) for v in r["episodes"]
        )
        for r in main_result["duplicate_trajectories"]
    }
    assert actual_duplicates == reported
    result = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "projection_tables_checked": projection_count,
        "range_hashes_checked": range_count,
        "frame_rows_checked": row_count,
        "annotation_joins_checked": len(checked_annotations),
        "schema_invalid_annotations_checked": independently_invalid,
        "independent_annotation_counts": {
            "event_windows_in_bounds": sum(
                r["event_frames_in_bounds"] for r in checked_annotations
            ),
            "origin_phase_disagreements": sum(
                r["origin_matches_half_open_phase"] is False
                for r in checked_annotations
            ),
        },
        "metadata_counts": metadata_counts,
        "metadata_hashes_checked": len(metadata_integrity),
        "published_corrupt_metadata": published_corrupt_metadata,
        "duplicate_groups_checked": len(actual_duplicates),
        "duration_role_purity": recomputed_purity,
        "pilot_annotation_files": pilot_annotation_files,
        "scope": "All original acquired column ranges reparsed offline and compared with projections; labels and episode counts independently recomputed. No whole-file checksum claim for partial source objects.",
        "qualification_sha256": digest(root / "qualification.json"),
    }
    (root / "independent_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "metadata_counts"}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
