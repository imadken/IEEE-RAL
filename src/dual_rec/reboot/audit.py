"""Qualify actual REBOOT episode/event joins and document missing supervision."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .contracts import PhaseEpisode, causal_signals, event_integrity

_LOGGER = logging.getLogger(__name__)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def metadata_rows(base):
    import pyarrow.parquet as pq

    rows, errors, columns = [], [], set()
    for path in sorted((base / "meta/episodes").rglob("*.parquet")):
        try:
            source = pq.ParquetFile(path)
            columns.update(source.schema_arrow.names)
            chosen = [
                k for k in source.schema_arrow.names if not k.startswith("stats/")
            ]
            rows.extend(source.read(columns=chosen).to_pylist())
        except Exception as exc:
            _LOGGER.exception("Retaining unreadable published episode metadata")
            errors.append(
                {
                    "path": str(path.relative_to(base)),
                    "error": repr(exc),
                    "sha256": digest_bytes(path.read_bytes()),
                }
            )
    return rows, errors, sorted(columns)


def episode_arrays(root, name):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    grouped = defaultdict(list)
    for path in sorted((root / "projected" / name / "data").rglob("*.parquet")):
        table = pq.ParquetFile(path).read()
        indexes = np.asarray(table["episode_index"])
        for episode in np.unique(indexes):
            grouped[int(episode)].append(
                table.filter(pc.equal(table["episode_index"], int(episode)))
            )
    result = {}

    for episode, tables in grouped.items():
        table = pa.concat_tables(tables)
        order = np.argsort(np.asarray(table["frame_index"]), kind="stable")
        result[episode] = {
            "qpos": np.array(table["observation.state"].to_pylist(), dtype=np.float32)[
                order
            ],
            "actions": np.array(table["action"].to_pylist(), dtype=np.float32)[order],
            "timestamp": np.asarray(table["timestamp"])[order],
            "frame_index": np.asarray(table["frame_index"])[order],
            "index": np.asarray(table["index"])[order],
            "task_index": np.asarray(table["task_index"])[order],
        }
    return result


def physical_hash(arrays):
    value = b"".join(
        np.ascontiguousarray(arrays[k], dtype="<f4").tobytes()
        for k in ("qpos", "actions", "timestamp")
    )
    return digest_bytes(value)


def annotation_coverage_complete(repositories):
    pilot = [r for r in repositories if r["role"] in {"expert", "recovery"}]
    cells = {(r["object"], r["operation"], r["role"]) for r in pilot}
    required = {
        (obj, operation, role)
        for obj in ("cylinder", "usb_c", "rj45")
        for operation in ("install", "remove")
        for role in ("expert", "recovery")
    }
    return required <= cells and all(
        r["phase_annotation_file"]
        and r["annotation_entries"] == r["projected_episodes"]
        and not r["annotation_parse_errors"]
        for r in pilot
    )


def audit(root):
    registration = json.loads((root / "repository_registration.json").read_text())
    summary, episodes, annotations, file_checks = [], [], [], []
    raw_annotation_checks = []
    hashes = defaultdict(list)
    for repo in registration["repositories"]:
        name = repo["id"].split("/")[1]
        base = root / "data" / name
        info = json.loads((base / "meta/info.json").read_text())
        tree = json.loads((base / "tree.json").read_text())
        paths = {v["path"]: v for v in tree if v["type"] == "file"}
        for path in [
            p
            for p in base.rglob("*")
            if p.is_file() and str(p.relative_to(base)) in paths
        ]:
            entry = paths[str(path.relative_to(base))]
            body = path.read_bytes()
            if entry.get("lfs"):
                expected, actual = entry["lfs"]["oid"], digest_bytes(body)
            else:
                expected, actual = (
                    entry["oid"],
                    hashlib.sha1(
                        b"blob " + str(len(body)).encode() + b"\0" + body
                    ).hexdigest(),
                )
            file_checks.append(
                {
                    "repository": repo["id"],
                    "path": str(path.relative_to(base)),
                    "bytes": len(body),
                    "matches_published_hash": expected == actual,
                    "published_hash": expected,
                }
            )
        meta, meta_errors, columns = metadata_rows(base)
        meta_by_id = defaultdict(list)
        for row in meta:
            meta_by_id[row["episode_index"]].append(row)
        arrays = episode_arrays(root, name)
        annotation_file = base / "meta/phase.json"
        raw_phase = (
            json.loads(annotation_file.read_text())
            if annotation_file.exists()
            else None
        )
        phase_by_id = defaultdict(list)
        annotation_parse_errors = []
        if raw_phase:
            for raw in raw_phase.get("episodes", []):
                raw_id = int(raw["episode_index"])
                failure = raw.get("failure") or {}
                onset = failure.get("induced_at_frame", failure.get("t_f"))
                recovery = failure.get("recovery_started_at_frame", failure.get("t_r"))
                actual = arrays.get(raw_id, {}).get("frame_index", np.array([]))
                raw_annotation_checks.append(
                    {
                        "repository": repo["id"],
                        "episode": raw_id,
                        "raw": raw,
                        "event_window_in_actual_frames": bool(
                            isinstance(onset, int)
                            and isinstance(recovery, int)
                            and onset in actual
                            and recovery in actual
                            and onset < recovery
                        ),
                    }
                )
                try:
                    parsed = PhaseEpisode.model_validate(raw)
                    phase_by_id[parsed.episode_index].append((parsed, raw))
                except ValueError as exc:
                    annotation_parse_errors.append(
                        {
                            "raw_episode_index": raw.get("episode_index"),
                            "error": str(exc),
                        }
                    )
        timing_errors, finite_errors, mismatched_lengths, video_errors = [], [], [], []
        for episode, data in sorted(arrays.items()):
            frames, timestamps = data["frame_index"], data["timestamp"]
            length = len(frames)
            aligned = np.array_equal(frames, np.arange(length))
            finite = bool(
                np.isfinite(data["qpos"]).all()
                and np.isfinite(data["actions"]).all()
                and np.isfinite(timestamps).all()
            )
            dt_error = (
                float(np.max(np.abs(np.diff(timestamps) - 1 / info["fps"])))
                if length > 1
                else None
            )
            timestamp_error = float(np.max(np.abs(timestamps - frames / info["fps"])))
            if (
                not aligned
                or np.any(np.diff(timestamps) <= 0)
                or timestamp_error > 1e-4
            ):
                timing_errors.append(episode)
            if (
                not finite
                or data["qpos"].shape != (length, 14)
                or data["actions"].shape != (length, 14)
            ):
                finite_errors.append(episode)
            metadata = meta_by_id.get(episode, [])
            if len(metadata) != 1 or metadata[0]["length"] != length:
                mismatched_lengths.append(episode)
            if len(metadata) == 1:
                row = metadata[0]
                for key in info["features"]:
                    start, end = (
                        f"videos/{key}/from_timestamp",
                        f"videos/{key}/to_timestamp",
                    )
                    if (
                        start in row
                        and end in row
                        and abs(row[end] - row[start] - length / info["fps"]) > 0.07
                    ):
                        video_errors.append(
                            {
                                "episode": episode,
                                "camera": key,
                                "declared_span": row[end] - row[start],
                                "trajectory_span": length / info["fps"],
                            }
                        )
            fingerprint = physical_hash(data)
            hashes[fingerprint].append(
                {"repository": repo["id"], "episode": episode, "role": repo["role"]}
            )
            joint_ids = [i for i in range(14) if i not in (6, 13)]
            motion = np.linalg.norm(np.diff(data["qpos"][:, joint_ids], axis=0), axis=1)
            trailing_static = 0
            for magnitude in motion[::-1]:
                if magnitude >= 1e-4:
                    break
                trailing_static += 1
            # Exercise only causal observability contracts, never fit a classifier.
            causal = (
                causal_signals(data["qpos"], data["actions"], timestamps)
                if finite and aligned and np.all(np.diff(timestamps) > 0)
                else None
            )
            item = {
                "repository": repo["id"],
                "object": repo["object"],
                "operation": repo["operation"],
                "role": repo["role"],
                "episode": episode,
                "frames": length,
                "time_end": float(timestamps[-1]),
                "state_action_time_sha256": fingerprint,
                "max_timestamp_error_s": timestamp_error,
                "max_dt_error_s": dt_error,
                "finite_state_action": finite,
                "contiguous_episode_frames": bool(aligned),
                "trailing_low_joint_motion_frames_at_1e-4_rad": trailing_static,
                "causal_channels": causal.shape[1] if causal is not None else None,
                "has_event_annotation": episode in phase_by_id,
            }
            episodes.append(item)
            if episode in phase_by_id:
                if len(phase_by_id[episode]) != 1:
                    annotation_parse_errors.append(
                        {"episode": episode, "error": "duplicate episode annotation"}
                    )
                    continue
                annotation, raw = phase_by_id[episode][0]
                verdict = event_integrity(annotation, frames)
                event = annotation.failure
                annotations.append(
                    {
                        "repository": repo["id"],
                        "episode": episode,
                        "actual_frames": length,
                        "annotation_duration": annotation.duration_frames,
                        "annotation_repository": raw.get(
                            "repo_id", raw_phase.get("dataset")
                        ),
                        "annotation_repository_matches": raw.get(
                            "repo_id", raw_phase.get("dataset")
                        )
                        == repo["id"],
                        "operator_id": raw.get("operator_id"),
                        "collection_session": raw.get("collection_session"),
                        "onset_frame": event.onset_frame if event else None,
                        "recovery_frame": event.recovery_frame if event else None,
                        "originating_phase": event.originating_phase if event else None,
                        "failure_mode": event.failure_mode if event else None,
                        **verdict,
                    }
                )
                if repo["role"] == "sample_engineering_only" and episode < 3:
                    folder = root / "examples"
                    folder.mkdir(exist_ok=True)
                    np.savez_compressed(folder / f"sample-{episode:02d}.npz", **data)
        summary.append(
            {
                "repository": repo["id"],
                "revision": repo["revision"],
                "object": repo["object"],
                "operation": repo["operation"],
                "role": repo["role"],
                "declared_episodes": info["total_episodes"],
                "declared_frames": info["total_frames"],
                "metadata_episode_rows": len(meta),
                "metadata_unique_episodes": len(meta_by_id),
                "metadata_errors": meta_errors,
                "metadata_columns": columns,
                "projected_episodes": len(arrays),
                "projected_frames": sum(len(v["frame_index"]) for v in arrays.values()),
                "phase_annotation_file": raw_phase is not None,
                "annotation_entries": sum(len(v) for v in phase_by_id.values()),
                "annotation_parse_errors": annotation_parse_errors,
                "timing_error_episodes": timing_errors,
                "state_action_error_episodes": finite_errors,
                "missing_or_inconsistent_episode_metadata": mismatched_lengths,
                "video_metadata_span_errors": video_errors,
                "runtime_feature_names": info["features"]["observation.state"].get(
                    "names"
                ),
                "advertised_depth_channels": [
                    k for k in info["features"] if k.endswith("_depth")
                ],
                "event_or_session_data_fields": [
                    k
                    for k in info["features"]
                    if any(
                        x in k.lower()
                        for x in ("phase", "failure", "operator", "session")
                    )
                ],
            }
        )
        print(
            json.dumps(
                {
                    "repository": repo["id"],
                    "projected_episodes": len(arrays),
                    "phase_annotation_entries": sum(
                        len(v) for v in phase_by_id.values()
                    ),
                    "metadata_errors": len(meta_errors),
                }
            ),
            flush=True,
        )
    duplicates = [
        {"state_action_time_sha256": key, "episodes": rows}
        for key, rows in hashes.items()
        if len(rows) > 1
    ]
    pilot = [r for r in summary if r["role"] != "sample_engineering_only"]
    sample = [
        a
        for a in annotations
        if a["repository"].endswith("sample_recovery-demonstration")
    ]
    label_stats = {
        "raw_sample_annotation_entries": len(raw_annotation_checks),
        "raw_sample_positive_event_windows": sum(
            r["event_window_in_actual_frames"] for r in raw_annotation_checks
        ),
        "schema_invalid_sample_entries": sum(
            len(r["annotation_parse_errors"]) for r in summary
        ),
        "sample_annotations": len(sample),
        "event_windows_in_bounds": sum(a["event_frames_in_bounds"] for a in sample),
        "origin_phase_matches": sum(
            a["origin_matches_half_open_phase"] is True for a in sample
        ),
        "origin_phase_disagreements": sum(
            a["origin_matches_half_open_phase"] is False for a in sample
        ),
        "nonboundary_origin_disagreements": sum(
            a["origin_matches_half_open_phase"] is False
            and a["onset_on_phase_boundary"] is False
            for a in sample
        ),
        "duration_mismatches": sum(
            a["annotation_duration"] != a["actual_frames"] for a in sample
        ),
        "onsets_on_whole_seconds": sum(
            a["onset_frame"] is not None and a["onset_frame"] % 30 == 0 for a in sample
        ),
        "recoveries_on_whole_seconds": sum(
            a["recovery_frame"] is not None and a["recovery_frame"] % 30 == 0
            for a in sample
        ),
        "operators": dict(Counter(a["operator_id"] for a in sample)),
        "sessions": dict(Counter(a["collection_session"] for a in sample)),
        "failure_modes": dict(Counter(a["failure_mode"] for a in sample)),
        "pilot_repositories_with_annotations": sum(
            r["phase_annotation_file"] for r in pilot
        ),
    }
    duration_buckets = defaultdict(Counter)
    for row in episodes:
        if row["role"] in {"expert", "recovery"}:
            duration_buckets[(row["object"], row["operation"], row["frames"])][
                row["role"]
            ] += 1
    purity = sum(max(v.values()) for v in duration_buckets.values()) / sum(
        sum(v.values()) for v in duration_buckets.values()
    )
    result = {
        "status": "INCONCLUSIVE"
        if annotation_coverage_complete(summary)
        else "DATA_BLOCKED",
        "reason": "Independent event validation still required"
        if annotation_coverage_complete(summary)
        else "The fixed pilot repositories lack annotation coverage for the three-object early-recognition target",
        "repositories": summary,
        "episodes": episodes,
        "annotations": annotations,
        "raw_annotation_checks": raw_annotation_checks,
        "label_integrity": label_stats,
        "duplicate_trajectories": duplicates,
        "metadata_file_integrity": file_checks,
        "all_metadata_hashes_match_release": all(
            v["matches_published_hash"] for v in file_checks
        ),
        "descriptive_duration_role_purity": purity,
        "duration_purity_scope": "Whole-release object/operation/length bucket identifiability, uses final duration; NOT causal or held-out failure recognition performance",
        "models_trained": [],
        "B0_B7_results": None,
        "method_comparison_intervals": None,
        "alarm_delay_frontier": None,
        "video_sync_scope": "Declared metadata spans only; RGB/depth content alignment not independently established, no video decoded",
    }
    (root / "qualification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "reason",
                    "label_integrity",
                    "all_metadata_hashes_match_release",
                    "descriptive_duration_role_purity",
                )
            }
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence is sealed")
    audit(args.root)


if __name__ == "__main__":
    main()
