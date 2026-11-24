"""Frozen inputs for the user-authorized four-row plus conditional24-row diagnostic."""

import json
import lzma
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator
from rpd_pilot_common import BASE as PRIOR
from rpd_pilot_common import (
    PREFIX,
    TASKS,
    ReplayRow,
    digest,
    read_rows,
    sha,
    write_json,
)

__all__ = [
    "BASE",
    "PREFIX",
    "PRIOR",
    "START",
    "TASKS",
    "Job",
    "jobs",
    "planned_jobs",
    "sha",
    "verify_registration",
    "write_json",
]

BASE = Path("research/rpd_source_isolation_20261119")
START = "121faf7311d67363cba3e3031d4ec650a378c809"


class Job(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    job_id: str
    phase: Literal["failed_row_replay", "neutral_control"]
    isolation_replica: int
    row: ReplayRow
    original_continue_path: str

    @model_validator(mode="after")
    def only_authorized_rows(self):
        assert self.row.parent.index == 0
        if self.phase == "failed_row_replay":
            assert self.isolation_replica in (0, 1)
            assert self.row.endpoint == "recover" and self.row.repeat == 0
            expected = (
                "release_settle"
                if self.row.parent.task == "PickCube-v1"
                else "lateral_sweep"
            )
            assert self.row.history == (expected, expected)
        else:
            assert self.isolation_replica == self.row.repeat
            assert self.row.history in (("neutral10",), ("neutral20",))
        return self


def planned_jobs():
    rows = [r for r in read_rows() if r.parent.index == 0]
    jobs = []
    for task in TASKS:
        interrupted = json.loads((PRIOR / "final_audit/summary.json").read_text())[
            "tasks"
        ][task]["interrupted_rows"]
        assert len(interrupted) == 1
        failed = ReplayRow.model_validate(interrupted[0])
        assert failed in rows
        previous = next(
            r
            for r in rows
            if r.parent.task == task
            and r.history == failed.history
            and r.endpoint == "continue"
            and r.repeat == 0
        )
        canonical_path = (
            PRIOR / "physics" / task / "parent_00" / (previous.row_id + ".json.xz")
        )
        with lzma.open(canonical_path, "rt") as stream:
            canonical = json.load(stream)
        assert canonical["status"] == "COMPLETE"
        for replica in (0, 1):
            jobs.append(
                Job(
                    job_id=digest(["RPD-SOURCE-ISOLATION", failed.row_id, replica]),
                    phase="failed_row_replay",
                    isolation_replica=replica,
                    row=failed,
                    original_continue_path=str(canonical_path),
                )
            )
        for row in rows:
            if row.parent.task == task and row.history in (
                ("neutral10",),
                ("neutral20",),
            ):
                jobs.append(
                    Job(
                        job_id=digest(["RPD-SOURCE-ISOLATION-HOLD", row.row_id]),
                        phase="neutral_control",
                        isolation_replica=row.repeat,
                        row=row,
                        original_continue_path=str(canonical_path),
                    )
                )
    assert len(jobs) == 28 and len({j.job_id for j in jobs}) == 28
    return jobs


def jobs():
    return [
        Job.model_validate_json(line)
        for line in (BASE / "jobs.jsonl").read_text().splitlines()
    ]


def verify_registration():
    packet = json.loads((BASE / "prephysics_seal.json").read_text())
    for path, expected in packet["files"].items():
        assert sha(path) == expected, path
    return packet
