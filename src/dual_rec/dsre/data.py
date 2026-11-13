"""Read-only qualification of existing matched fresh-prefix intervention records."""

import gzip
import hashlib
import json
from pathlib import Path

from dual_rec.validation import compare, passes

from .features import ObservationHistory, feature_values, observed_frame


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def value_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def boolean(value):
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value if isinstance(value, bool) else None


def qualify_pair(raw, rows, config):
    """Qualify both fresh branches, never substitute a native snapshot."""
    chosen = {
        a: [r for r in rows if r["action"] == a and r["route"] == "fresh_prefix"]
        for a in config["actions"]
    }
    if any(len(v) != 1 for v in chosen.values()):
        raise ValueError("Missing or duplicate fresh-prefix action outcome")
    chosen = {a: v[0] for a, v in chosen.items()}
    if len(raw["prefix"]) != len(raw["prefix_actions"]) + 1:
        raise ValueError("Incomplete registered prefix")
    model_hashes = {r["model_hash"] for r in chosen.values()}
    if len(model_hashes) != 1:
        raise ValueError("Action branches use different physical models")
    history_hash = value_digest(raw["prefix_actions"])
    for action, row in chosen.items():
        trace = raw["traces"][action + "/fresh_prefix"]
        reference = raw["traces"][action + "/reference"]
        if (
            reference.get("controller_memory") is None
            or reference.get("prefix_history") is None
            or trace.get("prefix_history") is None
        ):
            raise ValueError(
                "Missing retained complete reference/fresh prefix history or reference controller memory"
            )
        if not row["prefix_ok"] or row["history_hash"] != history_hash:
            raise ValueError("Unqualified or mismatched executed prefix")
        if row["model_hash"] != value_digest(row["model"]):
            raise ValueError("Physical model digest mismatch")
        if not passes(compare(raw["prefix"][-1], trace["start"])):
            raise ValueError("Fresh branch checkpoint differs from registered history")
        if not passes(compare(reference["start"], trace["start"])):
            raise ValueError("Fresh/reference checkpoints differ")
        if trace.get("controller_memory") != raw["snapshot"]["custom"]:
            raise ValueError(
                "Fresh controller memory differs from registered checkpoint"
            )
        if (
            reference.get("controller_memory") is not None
            and reference["controller_memory"] != trace["controller_memory"]
        ):
            raise ValueError("Reference/fresh controller memory differs")
        for history in (reference["prefix_history"], trace["prefix_history"]):
            if len(history) != len(raw["prefix"]) or not all(
                passes(compare(a, b))
                for a, b in zip(history, raw["prefix"], strict=True)
            ):
                raise ValueError(
                    "Reference/fresh history failed complete-prefix parity"
                )
        if (
            len(trace["frames"]) != config["horizon_steps"]
            or len(reference["frames"]) != config["horizon_steps"]
        ):
            raise ValueError("Wrong continuation horizon")
        if (
            len(row["actions"]) != config["horizon_steps"]
            or row["actions"] != row["expected_actions"]
        ):
            raise ValueError("Controls differ from frozen branch action tape")
        if (
            len(row["state_errors"]) != config["horizon_steps"]
            or max(row["state_errors"]) > 1
        ):
            raise ValueError("Fresh-prefix continuation fidelity failed")
        if not all(
            passes(compare(a["state"], b["state"]))
            for a, b in zip(trace["frames"], reference["frames"], strict=True)
        ):
            raise ValueError("Raw fresh/reference trajectory parity failed")
        if any(
            abs(frame["state"]["time"] - trace["start"]["time"] - (i + 1) * 0.05) > 1e-8
            for i, frame in enumerate(trace["frames"])
        ):
            raise ValueError("Physical time budget differs")
        terminal = bool(trace["frames"][-1]["state"]["success"])
        if (
            terminal != row["success"]
            or terminal != row["reference_success"]
            or bool(trace["start"]["success"]) != row["initial_success"]
        ):
            raise ValueError(
                "Stored terminal/initial outcome differs from raw trajectory"
            )
        first_hit = next(
            (
                i + 1
                for i, frame in enumerate(trace["frames"])
                if frame["state"]["success"]
            ),
            None,
        )
        if first_hit != row["first_hit"]:
            raise ValueError(
                "Stored first-hit control-step index differs from raw trajectory"
            )
    if not passes(
        compare(
            raw["traces"]["continue/fresh_prefix"]["start"],
            raw["traces"]["recover/fresh_prefix"]["start"],
        )
    ):
        raise ValueError("Continue/recover start states differ")
    return chosen


def construct(config, root):
    source_root = Path(config["source_root"])
    seal_path = source_root / "completion_manifest.json"
    seal = read(seal_path)
    members = seal["sha256"]
    registration = read(source_root / "registration.json")
    sources = {
        str(seal_path): digest(seal_path),
        str(source_root / "registration.json"): digest(
            source_root / "registration.json"
        ),
    }
    for name in ("registration.json", "confirmation_freeze.json"):
        path = source_root / name
        if digest(path) != members[name]:
            raise ValueError("Historical registration/freeze digest mismatch")
        sources[str(path)] = digest(path)
    table, exclusions, canonical = [], [], {}
    checkpoint_path = root / "qualification_checkpoint.json"
    code_sha = digest(Path(__file__))
    completed = set()
    if checkpoint_path.exists():
        checkpoint = read(checkpoint_path)
        if checkpoint["code_sha256"] != code_sha:
            raise ValueError(
                "Qualification code changed; preserve this attempt and use a fresh qualification root"
            )
        table, exclusions = checkpoint["table"], checkpoint["exclusions"]
        sources.update(checkpoint["sources"])
        for name, expected in sources.items():
            if digest(Path(name)) != expected:
                raise ValueError("Checkpoint source changed: " + name)
        completed = {r["id"] for r in table + exclusions}
        canonical = {r["canonical_checkpoint_sha256"]: r["id"] for r in table}
    for task in config["tasks"]:
        for split in ("development", "confirmation"):
            for seed in registration["seeds"][task][split]:
                for condition in registration["conditions"][task]:
                    identifier = f"{task}/{seed}/{condition}"
                    if identifier in completed:
                        continue
                    folder = (
                        source_root / "parents" / split / task / f"{seed}-{condition}"
                    )
                    try:
                        paths = [folder / "outcomes.json", folder / "traces.json.gz"]
                        for path in paths:
                            expected = members[str(path.relative_to(source_root))]
                            if digest(path) != expected:
                                raise ValueError("Sealed source digest mismatch")
                            sources[str(path)] = expected
                        with gzip.open(paths[1], "rt") as stream:
                            raw = json.load(stream)
                        chosen = qualify_pair(raw, read(paths[0]), config)
                        if any(
                            r["task"] != task
                            or r["seed"] != seed
                            or r["condition"] != condition
                            or r["split"] != split
                            for r in chosen.values()
                        ):
                            raise ValueError(
                                "Registered parent identity differs from raw outcomes"
                            )
                        history = ObservationHistory(
                            first=observed_frame(
                                raw["prefix"][0]["time"],
                                raw["prefix"][0]["observation"],
                            ),
                            current=observed_frame(
                                raw["prefix"][-1]["time"],
                                raw["prefix"][-1]["observation"],
                            ),
                        )
                        features = feature_values(history)
                        checkpoint_hash = value_digest(
                            {
                                "task": task,
                                "prefix_actions": raw["prefix_actions"],
                                "checkpoint": raw["prefix"][-1],
                                "memory": raw["snapshot"]["custom"],
                            }
                        )
                        if checkpoint_hash in canonical:
                            raise ValueError(
                                "Duplicate canonical physical parent: "
                                + canonical[checkpoint_hash]
                            )
                        canonical[checkpoint_hash] = identifier
                        current = raw["prefix"][-1]
                        table.append(
                            {
                                "id": identifier,
                                "task": task,
                                "seed": seed,
                                "group": f"{task}/{seed}",
                                "condition_audit_only": condition,
                                "old_split_development_only": split,
                                "canonical_checkpoint_sha256": checkpoint_hash,
                                "source": str(paths[1]),
                                "outcomes_source": str(paths[0]),
                                "source_sha256": sources[str(paths[1])],
                                "runtime_history": history.model_dump(mode="json"),
                                "features": features,
                                "coarse_features": feature_values(history, coarse=True),
                                "privileged_features": features
                                + (
                                    boolean(
                                        current["observation"]
                                        .get("extra", {})
                                        .get("is_grasped")
                                    ),
                                    boolean(current.get("robot_object_contact")),
                                ),
                                "outcomes": {
                                    a + "_value": chosen[a]["success"]
                                    for a in config["actions"]
                                },
                                "initial_success": bool(current["success"]),
                                "new_first_hits": {
                                    a: not current["success"]
                                    and any(
                                        f["state"]["success"]
                                        for f in raw["traces"][a + "/fresh_prefix"][
                                            "frames"
                                        ]
                                    )
                                    for a in config["actions"]
                                },
                                "checkpoint_time": current["time"],
                                "prefix_controls": len(raw["prefix_actions"]),
                                "history_hash": chosen["continue"]["history_hash"],
                                "model_hash_audit_only": chosen["continue"][
                                    "model_hash"
                                ],
                                "route_wall_seconds": {
                                    a: chosen[a]["route_wall_seconds"]
                                    for a in config["actions"]
                                },
                                "qualification": "FULL_MATCHED_FRESH_PREFIX_RAW_PARITY",
                                "reference_memory_recorded": all(
                                    raw["traces"][a + "/reference"].get(
                                        "controller_memory"
                                    )
                                    is not None
                                    for a in config["actions"]
                                ),
                            }
                        )
                    except (KeyError, ValueError, OSError, TypeError) as error:
                        exclusions.append(
                            {
                                "id": identifier,
                                "source": str(folder),
                                "reason": str(error),
                                "status": "EXCLUDED_NO_IMAGINED_OUTCOMES",
                            }
                        )
                    if (len(table) + len(exclusions)) % 20 == 0:
                        checkpoint_path.write_text(
                            json.dumps(
                                {
                                    "code_sha256": code_sha,
                                    "table": table,
                                    "exclusions": exclusions,
                                    "sources": sources,
                                },
                                allow_nan=False,
                            )
                            + "\n"
                        )
                        print(
                            json.dumps(
                                {
                                    "qualified": len(table),
                                    "excluded": len(exclusions),
                                    "last_parent": identifier,
                                }
                            ),
                            flush=True,
                        )
    (root / "qualified_pairs.jsonl").write_text(
        "".join(json.dumps(r, allow_nan=False) + "\n" for r in table)
    )
    (root / "qualification_exclusions.json").write_text(
        json.dumps(exclusions, indent=2) + "\n"
    )
    (root / "source_members.json").write_text(json.dumps(sources, indent=2) + "\n")
    return table, exclusions
