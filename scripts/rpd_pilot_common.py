"""Immutable inputs and pure measurement contracts for the bounded RPD pilot."""

import hashlib
import itertools
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BASE = Path("research/rpd_physical_pilot_20261119")
OLD = Path("research/rpd_method_challenge")
TASKS = ("PickCube-v1", "PushCube-v1")
MENUS = {
    "PickCube-v1": ("micro_lift", "release_settle"),
    "PushCube-v1": ("forward_tap", "lateral_sweep"),
}
PREFIX = {"PickCube-v1": 65, "PushCube-v1": 53}
HOLD = (0.0, 0.0, 0.0, -1.0)


class Parent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    task: Literal["PickCube-v1", "PushCube-v1"]
    phase: Literal["technical_pilot"]
    index: int = Field(ge=0, lt=10)
    seed: int = Field(ge=0)
    parent_id: str = Field(pattern="^[0-9a-f]{64}$")
    condition: Literal["nominal"]


class ReplayRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    parent: Parent
    history: tuple[str, ...]
    endpoint: Literal["continue", "recover", "STOP"]
    repeat: Literal[0, 1]
    row_id: str
    delay_ticks: Literal[0, 10, 20]
    macro_ticks: Literal[0, 70]
    deadline_ticks: Literal[90] = 90


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def parents():
    path = OLD / "final/stage2/reserved_parents.jsonl"
    protocol = json.loads((OLD / "final/stage2/protocol.json").read_text())
    assert sha(path) == protocol["reserved_manifest_sha256"]
    found = []
    for line in path.read_text().splitlines():
        value = json.loads(line)
        if value["phase"] != "technical_pilot":
            continue
        assert value["outcome"] is None and value["qualified"] is None
        parent = Parent.model_validate(value)
        assert (
            parent.parent_id
            == hashlib.sha256(
                f"RPD-S2-20261119|{parent.task}|technical_pilot|{parent.index}|{parent.seed}".encode()
            ).hexdigest()
        )
        found.append(parent)
    assert len(found) == len({p.seed for p in found}) == 20
    assert all(sum(p.task == t for p in found) == 10 for t in TASKS)
    return found


def histories(task):
    probes = MENUS[task]
    return [
        (),
        *((p,) for p in probes),
        *itertools.product(probes, repeat=2),
        ("neutral10",),
        ("neutral20",),
    ]


def delay(history):
    if history == ("neutral10",):
        return 10
    if history == ("neutral20",):
        return 20
    return 10 * len(history)


def rows():
    result = []
    for parent in parents():
        for history in histories(parent.task):
            for endpoint in ("continue", "recover", "STOP"):
                for repeat in (0, 1):
                    row_id = digest([parent.parent_id, history, endpoint, repeat])
                    result.append(
                        ReplayRow(
                            parent=parent,
                            history=history,
                            endpoint=endpoint,
                            repeat=repeat,
                            row_id=row_id,
                            delay_ticks=delay(history),
                            macro_ticks=0 if endpoint == "STOP" else 70,
                        )
                    )
    assert len(result) == len({r.row_id for r in result}) == 1080
    return result


def read_rows():
    return [
        ReplayRow.model_validate_json(line)
        for line in (BASE / "replay_manifest.jsonl").read_text().splitlines()
    ]


def frozen_sources():
    audit = json.loads((OLD / "final/source/source_and_adapters.json").read_text())
    return audit["source_sha256"], audit["versions"]


def verify_registration():
    seal = json.loads((BASE / "prephysics_seal.json").read_text())
    for path, expected in seal["files"].items():
        assert sha(path) == expected, f"FROZEN_SOURCE_CONFLICT: {path}"
    return seal
