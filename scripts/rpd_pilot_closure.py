"""Forensic attempt/missingness accounting after a native worker termination.

This audit never restarts a simulator. Raw trace checks and qualification are
separate: a started journal with no returned trace is an attempted missing
outcome, not an unattempted episode and never a fabricated terminal failure.
"""

import argparse
import collections
import json
import lzma
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rpd_pilot_audit import (
    check_parity,
    inspect_trace,
    required_packet,
    root_description,
    source_geometry,
)
from rpd_pilot_common import BASE, PREFIX, TASKS, read_rows, sha, write_json


class Counts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    registered: int = Field(ge=0)
    attempted: int = Field(ge=0)
    complete: int = Field(ge=0)
    interrupted_missing_outcome: int = Field(ge=0)
    unattempted: int = Field(ge=0)
    missing_terminal_labels: int = Field(ge=0)

    @model_validator(mode="after")
    def conservation(self):
        assert self.attempted == self.complete + self.interrupted_missing_outcome
        assert self.registered == self.attempted + self.unattempted
        assert (
            self.missing_terminal_labels
            == self.interrupted_missing_outcome + self.unattempted
        )
        return self


def count_status(statuses):
    counts = collections.Counter(statuses)
    assert set(counts) <= {
        "COMPLETE",
        "INTERRUPTED_MISSING_OUTCOME",
        "UNATTEMPTED_SOURCE_GUARD",
    }
    return Counts(
        registered=len(statuses),
        attempted=counts["COMPLETE"] + counts["INTERRUPTED_MISSING_OUTCOME"],
        complete=counts["COMPLETE"],
        interrupted_missing_outcome=counts["INTERRUPTED_MISSING_OUTCOME"],
        unattempted=counts["UNATTEMPTED_SOURCE_GUARD"],
        missing_terminal_labels=len(statuses) - counts["COMPLETE"],
    )


def audit(output):
    assert not output.exists()
    output.mkdir(parents=True)
    exit_record = json.loads((BASE / "native_process_exit_receipt.json").read_text())
    trace_audit = json.loads(
        (BASE / "independent_trace_audit/summary.json").read_text()
    )
    assert trace_audit["passed"]
    manifest = read_rows()
    summaries = {}
    canonical = []
    errors = []
    for task in TASKS:
        selected = [r for r in manifest if r.parent.task == task]
        directory = BASE / "physics" / task
        native_exit = exit_record["tasks"][task]
        assert native_exit["exit_code"] == 139
        returned = {}
        started = {}
        for marker in directory.glob("parent_*/*.started.json"):
            value = json.loads(marker.read_text())
            assert value["row_id"] not in started
            started[value["row_id"]] = {
                "path": str(marker),
                "sha256": sha(marker),
                **value,
            }
        for path in directory.glob("parent_*/*.json.xz"):
            with lzma.open(path, "rt") as stream:
                value = json.load(stream)
            row_id = value["row"]["row_id"]
            assert row_id in started and row_id not in returned
            inspection = inspect_trace(value)
            assert value["status"] == "COMPLETE" and inspection["passed"]
            value["raw_path"] = str(path)
            value["raw_sha256"] = sha(path)
            value["inspection"] = inspection
            returned[row_id] = value
        assert set(started) <= {r.row_id for r in selected}
        task_canonical = []
        for row in selected:
            raw = returned.get(row.row_id)
            journal = started.get(row.row_id)
            status = (
                "COMPLETE"
                if raw
                else "INTERRUPTED_MISSING_OUTCOME"
                if journal
                else "UNATTEMPTED_SOURCE_GUARD"
            )
            task_canonical.append(
                {
                    "row": row.model_dump(mode="json"),
                    "status": status,
                    "macro_end_success": raw["macro_end_success"] if raw else None,
                    "deadline_success": raw["deadline_success"] if raw else None,
                    "journal": journal,
                    "raw_path": raw["raw_path"] if raw else None,
                    "raw_sha256": raw["raw_sha256"] if raw else None,
                    "unknown_native_stage": status == "INTERRUPTED_MISSING_OUTCOME",
                }
            )
        counts = count_status([r["status"] for r in task_canonical])
        per_parent = []
        repeat_checks = []
        known_probe_effects = []
        grouped_history = collections.defaultdict(dict)
        for index in range(10):
            assigned = [
                r for r in task_canonical if r["row"]["parent"]["index"] == index
            ]
            observed = [
                v for v in returned.values() if v["row"]["parent"]["index"] == index
            ]
            c = count_status([r["status"] for r in assigned])
            roots = [v["records"][: PREFIX[task] + 1] for v in observed]
            root_parity = (
                all(check_parity(roots[0], root) for root in roots[1:])
                if roots
                else None
            )
            memories = [v["root_controller_custom"] for v in observed]
            memory_equal = (
                all(m == memories[0] for m in memories[1:]) if memories else None
            )
            assert root_parity is not False and memory_equal is not False
            source_rows = {
                (
                    tuple(v["row"]["history"]),
                    v["row"]["endpoint"],
                    v["row"]["repeat"],
                ): v
                for v in observed
            }
            for (history, endpoint, repeat), value in source_rows.items():
                if repeat == 1 and (history, endpoint, 0) in source_rows:
                    first = source_rows[(history, endpoint, 0)]
                    passed = check_parity(first["records"], value["records"])
                    repeat_checks.append(
                        {
                            "parent_index": index,
                            "history": history,
                            "endpoint": endpoint,
                            "passed": passed,
                        }
                    )
                    assert passed
                if repeat == 0:
                    grouped_history[history][(index, endpoint)] = value
                    if (
                        history
                        and not history[0].startswith("neutral")
                        and endpoint == "continue"
                    ):
                        start = PREFIX[task]
                        stop = start + 10 * len(history)
                        states = value["records"][start : stop + 1]
                        contacts = [
                            j
                            for j, s in enumerate(states[1:], 1)
                            if any(
                                c["points"]
                                for c in s["evaluator_robot_object_contacts"]
                            )
                        ]
                        known_probe_effects.append(
                            {
                                "parent_index": index,
                                "history": history,
                                "probe_delay_ticks": 10 * len(history),
                                "raw_path": value["raw_path"],
                                "raw_sha256": value["raw_sha256"],
                                "probe_contact_ticks": contacts,
                                "contact_tick_count": len(contacts),
                                "object_displacement_m": float(
                                    np.linalg.norm(
                                        np.array(states[-1]["position"])
                                        - states[0]["position"]
                                    )
                                ),
                                "tcp_displacement_m": float(
                                    np.linalg.norm(
                                        np.array(required_packet(states[-1])["tcp_xyz"])
                                        - required_packet(states[0])["tcp_xyz"]
                                    )
                                ),
                                "sampled_probe_allowed": all(
                                    all(
                                        source_geometry(
                                            s, value["source_runtime"]
                                        ).values()
                                    )
                                    for s in states
                                ),
                                "macro_deadline_native_success": value[
                                    "deadline_success"
                                ],
                                "matched_hold_contact_effect": "UNKNOWN_NO_MATCHED_HOLD",
                                "response": value["probe_observations"],
                            }
                        )
            per_parent.append(
                {
                    "parent": assigned[0]["row"]["parent"],
                    "counts": c.model_dump(),
                    "prefix_parity_on_returned_rows": root_parity,
                    "controller_memory_on_returned_rows": memory_equal,
                    "all_returned_rows_trace_valid": all(
                        v["inspection"]["passed"] for v in observed
                    ),
                    "qualified_complete_parent": c.complete == 54
                    and bool(root_parity)
                    and bool(memory_equal),
                    "original_checkpoint_contact_observed": any(
                        v["records"][PREFIX[task]]["robot_object_contact"]
                        for v in observed
                    )
                    if observed
                    else None,
                    "root_descriptor": root_description(
                        observed[0]["records"][PREFIX[task]]
                    )
                    if observed
                    else None,
                }
            )
        history_results = []
        for history in dict.fromkeys(tuple(r.history) for r in selected):
            data = grouped_history[history]
            cells = {}
            for endpoint in ("continue", "recover", "STOP"):
                found = [v for (i, e), v in data.items() if e == endpoint]
                cells[endpoint] = {
                    "returned_repeat0_parents": len(found),
                    "native_macro_end_successes": sum(
                        v["macro_end_success"] is True for v in found
                    )
                    if endpoint != "STOP"
                    else None,
                    "native_deadline_successes": sum(
                        v["deadline_success"] is True for v in found
                    ),
                }
            history_results.append({"history": history, "endpoints": cells})
        wall_sums = sum(v["runtime_seconds"] for v in returned.values())
        known_controls = sum(len(v["actions"]) for v in returned.values())
        interrupted = [
            r for r in task_canonical if r["status"] == "INTERRUPTED_MISSING_OUTCOME"
        ]
        console_start = native_exit["console_birth_epoch"]
        wall_upper = native_exit["exit_observed_no_later_than_epoch"] - console_start
        assert 0 < wall_upper < 10800
        # No neutral branch was collected: no erasure/creation or matched effect is estimable.
        neutral_returned = sum(
            bool(v["row"]["history"]) and v["row"]["history"][0].startswith("neutral")
            for v in returned.values()
        )
        assert neutral_returned == 0
        summaries[task] = {
            "verdict": "SOURCE_NOT_QUALIFIED",
            "counts": counts.model_dump(),
            "registered_parents": 10,
            "attempted_parents": sum(p["counts"]["attempted"] > 0 for p in per_parent),
            "complete_qualified_parents": sum(
                p["qualified_complete_parent"] for p in per_parent
            ),
            "untouched_parents": sum(p["counts"]["attempted"] == 0 for p in per_parent),
            "parents": per_parent,
            "repeat_checks": repeat_checks,
            "successful_repeat_checks": len(repeat_checks),
            "returned_prefix_replay_rows": len(returned),
            "history_endpoint_counts_repeat0": history_results,
            "known_probe_effects": known_probe_effects,
            "neutral_hold_returned_rows": neutral_returned,
            "K_hold": "UNKNOWN_MISSING",
            "K_probe": "NOT_IDENTIFIED_AGAINST_MATCHED_HOLD",
            "erasure_count": None,
            "creation_count": None,
            "lost_or_preserved_membership_vs_hold": None,
            "matched_eligible_parent_probe_denominator": 0,
            "interrupted_rows": [r["row"] for r in interrupted],
            "complete_trace_frame_count": sum(
                len(v["records"]) for v in returned.values()
            ),
            "known_native_controls": known_controls,
            "known_probe_control_count": sum(
                v["row"]["delay_ticks"] for v in returned.values()
            ),
            "native_controls_unreturned_row_range": [0, PREFIX[task] + 90],
            "measured_completed_episode_wall_seconds": wall_sums,
            "actual_total_worker_wall_seconds": "NOT_EXACTLY_MEASURED_NATIVE_FINALIZER_DID_NOT_RUN",
            "conservative_total_worker_wall_upper_seconds": wall_upper,
            "startup_seconds": [v.get("startup_seconds") for v in returned.values()],
            "native_process_exit": native_exit,
            "raw_compressed_bytes": sum(
                p.stat().st_size for p in directory.rglob("*") if p.is_file()
            ),
            "source_scope": "Finite/control/repeat checks passed only for38 returned rows; native worker crash blocks the fixed parent and family. No old calibration transfer.",
            "new_discovery_calibration_test_parents": 0,
        }
        canonical.extend(task_canonical)
    with (output / "all_registered_rows.jsonl").open("x") as stream:
        for r in canonical:
            stream.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
    summary = {
        "audit_passed": not errors,
        "source_qualified": False,
        "decision": "SOURCE_NOT_QUALIFIED",
        "tasks": summaries,
        "errors": errors,
        "supersedes_raw_only_counters": "independent_trace_audit/summary.json counts38 returned files and no invocation finalizer; it does not count the39th started journal or measure worker time. This forensic ledger is authoritative for attempts, missingness and cost.",
        "causal_mechanism_result": "UNRESOLVED_MISSING_MATCHED_NEUTRAL_HOLDS_NOT_A_NEGATIVE_ERASURE_RESULT",
        "root_cause": "UNDETERMINED_NATIVE_SIGSEGV; no stack/core/checkpoint trace returned for39th row. No new physics for diagnosis or repair.",
        "original_manuscript_and_evidence_edit_count": 0,
        "new_full_stage2_parents": 0,
    }
    write_json(output / "summary.json", summary)
    print(
        json.dumps(
            {
                "audit_passed": summary["audit_passed"],
                "decision": summary["decision"],
                "tasks": {t: r["counts"] for t, r in summaries.items()},
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
