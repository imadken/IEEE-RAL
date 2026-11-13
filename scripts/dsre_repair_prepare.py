"""Qualify fixed predecision telemetry against immutable raw prefix packets."""

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from dsre_audit import flatten

from dual_rec.dsre.features import ObservationHistory, observed_frame
from dual_rec.dsre.repair_selection import OPTIONAL, optional_values


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare(root):
    config = load(Path("config/dsre_evidence_repair.json"))
    old = Path(config["input_root"])
    assert load(root / "input_audit.json")["status"] == "PASS"
    assert sha(old / "qualified_pairs.jsonl") == config["table_sha256"]
    source = [
        json.loads(s) for s in (old / "qualified_pairs.jsonl").read_text().splitlines()
    ]
    availability = {task: Counter() for task in ("PickCube-v1", "PushCube-v1")}
    enriched = []
    raw_checks = 0
    for row in source:
        history = ObservationHistory.model_validate(row["runtime_history"])
        assert history.current.time == row["checkpoint_time"]
        optional = optional_values(history)
        # Independent arithmetic directly on the recorded packet, not the adapter.
        with gzip.open(row["source"], "rt") as stream:
            raw = json.load(stream)
        packet = raw["prefix"][-1]
        assert packet["time"] == history.current.time
        assert observed_frame(packet["time"], packet["observation"]) == history.current
        extra = packet["observation"]["extra"]
        obj, goal, hand = (
            flatten(extra.get(name, []))[:3]
            for name in ("obj_pose", "goal_pos", "tcp_pose")
        )
        differences = [
            obj[0] - goal[0] if len(obj) == len(goal) == 3 else None,
            obj[1] - goal[1] if len(obj) == len(goal) == 3 else None,
            hand[0] - obj[0] if len(hand) == len(obj) == 3 else None,
        ]
        expected = tuple(
            None if d is None else d < -0.02 if sign < 0 else d > 0.02
            for d in differences
            for sign in (-1, 1)
        )
        assert optional == expected
        assert row["runtime_history"]["first"]["time"] <= history.current.time
        availability[row["task"]].update(
            {
                name: int(value is not None)
                for name, value in zip(OPTIONAL, optional, strict=True)
            }
        )
        enriched.append(
            row
            | {
                "optional_features": optional,
                "optional_source": "prefix[-1].observation.extra.{obj_pose,tcp_pose,goal_pos}",
                "optional_timestamp": history.current.time,
            }
        )
        raw_checks += 1
        if raw_checks % 100 == 0:
            print(json.dumps({"raw_packets_checked": raw_checks}), flush=True)
    with (root / "qualified_pairs.jsonl").open("x") as stream:
        for row in enriched:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    save(
        root / "feature_qualification.json",
        {
            "status": "PASS",
            "pairs": len(enriched),
            "table_sha256": sha(root / "qualified_pairs.jsonl"),
            "original_table_sha256": sha(old / "qualified_pairs.jsonl"),
            "raw_packets_checked": raw_checks,
            "availability": availability,
            "channels": OPTIONAL,
            "source_timing": "last prefix packet, equal decision timestamp",
            "privileged_channels_in_primary": False,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    prepare(args.root)
