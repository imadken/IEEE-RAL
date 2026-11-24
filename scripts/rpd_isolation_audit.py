"""Independent native parity, matched availability and bounded source-scope audit."""

import argparse
import json
import lzma
from pathlib import Path

from rpd_isolation_common import BASE, PREFIX, TASKS, jobs, sha, write_json
from rpd_pilot_audit import check_parity, inspect_trace


def read_raw(path):
    with lzma.open(path, "rt") as stream:
        return json.load(stream)


def inspect_job(job):
    directory = BASE / "physics" / job.row.parent.task / job.job_id
    status = directory / "process.json"
    native = directory / "native.json.xz"
    if not status.exists():
        return {"job_id": job.job_id, "status": "NOT_RUN", "source_passed": False}
    receipt = json.loads(status.read_text())
    result = {
        "job_id": job.job_id,
        "phase": job.phase,
        "task": job.row.parent.task,
        "source_passed": False,
        "process": receipt,
        "status": "MISSING_NATIVE_OUTCOME",
    }
    if not native.exists():
        return result
    raw = read_raw(native)
    assert raw["row"] == job.row.model_dump(mode="json")
    inspection = inspect_trace(raw)
    canonical = read_raw(job.original_continue_path)
    n = PREFIX[job.row.parent.task]
    prefix = check_parity(canonical["records"][: n + 1], raw["records"][: n + 1])
    config = raw.get("source_runtime") == canonical["source_runtime"]
    memory = raw.get("root_controller_custom") == canonical["root_controller_custom"]
    probe_prefix = None
    if job.phase == "failed_row_replay" and len(raw["records"]) >= n + 21:
        probe_prefix = check_parity(
            canonical["records"][: n + 21], raw["records"][: n + 21]
        )
    passed = (
        receipt["returncode"] == 0
        and not receipt["timed_out"]
        and raw["status"] == "COMPLETE"
        and raw["source_checkpoint_qualified"]
        and inspection["passed"]
        and prefix
        and config
        and memory
        and (probe_prefix if job.phase == "failed_row_replay" else True)
    )
    result.update(
        {
            "status": raw["status"],
            "source_passed": bool(passed),
            "raw_path": str(native),
            "raw_sha256": sha(native),
            "trace_checks": inspection,
            "prefix_matches_original": prefix,
            "root_memory_matches_original": memory,
            "runtime_config_matches_original": config,
            "probe_prefix_matches_original_continue": probe_prefix,
            "macro_end_success": raw["macro_end_success"],
            "deadline_success": raw["deadline_success"],
        }
    )
    return result


def first_gate():
    selected = [j for j in jobs() if j.phase == "failed_row_replay"]
    checks = [inspect_job(j) for j in selected]
    pairs = {}
    for task in TASKS:
        pair = [j for j in selected if j.row.parent.task == task]
        paths = [BASE / "physics" / task / j.job_id / "native.json.xz" for j in pair]
        pairs[task] = all(p.exists() for p in paths) and check_parity(
            read_raw(paths[0])["records"], read_raw(paths[1])["records"]
        )
    return {
        "passed": len(checks) == 4
        and all(c["source_passed"] for c in checks)
        and all(pairs.values()),
        "checks": checks,
        "full_cross_process_repeat_parity": pairs,
        "gate_scope": "Return/clock/source/replay parity, not requirement that task success is1; same row repeated, zero independent parents.",
    }


def audit(output):
    assert not output.exists()
    output.mkdir(parents=True)
    gate = first_gate()
    checks = [inspect_job(j) for j in jobs()]
    tasks = {}
    for task in TASKS:
        selected = [j for j in jobs() if j.row.parent.task == task]
        available = [c for c in checks if c.get("task") == task]
        repeat_pairs = []
        for history in (("neutral10",), ("neutral20",)):
            for endpoint in ("continue", "recover", "STOP"):
                pair = [
                    j
                    for j in selected
                    if j.row.history == history and j.row.endpoint == endpoint
                ]
                paths = [
                    BASE / "physics" / task / j.job_id / "native.json.xz" for j in pair
                ]
                passed = (
                    len(paths) == 2
                    and all(p.exists() for p in paths)
                    and check_parity(
                        read_raw(paths[0])["records"], read_raw(paths[1])["records"]
                    )
                )
                repeat_pairs.append(
                    {"history": history, "endpoint": endpoint, "passed": passed}
                )
        measured = sum(c["process"]["wall_seconds"] for c in available)
        assert measured <= 1200
        byte_count = sum(
            p.stat().st_size
            for p in (BASE / "physics" / task).rglob("*")
            if p.is_file()
        )
        assert byte_count <= 100 * 1024**2
        outcomes = []
        for j in selected:
            check = next(c for c in checks if c["job_id"] == j.job_id)
            outcomes.append(
                {
                    "phase": j.phase,
                    "row_id": j.row.row_id,
                    "replica": j.isolation_replica,
                    "history": j.row.history,
                    "endpoint": j.row.endpoint,
                    "status": check["status"],
                    "source_passed": check["source_passed"],
                    "macro_end": check.get("macro_end_success"),
                    "deadline": check.get("deadline_success"),
                }
            )
        tasks[task] = {
            "planned": 14,
            "attempted": len(available),
            "returned_complete": sum(c["status"] == "COMPLETE" for c in available),
            "passed_source_checks": sum(c["source_passed"] for c in available),
            "not_run": 14 - len(available),
            "new_independent_parents": 0,
            "previously_exposed_parent_index": 0,
            "neutral_repeat_pairs": repeat_pairs,
            "outcomes": outcomes,
            "worker_wall_seconds": measured,
            "output_bytes": byte_count,
            "limited_source_completion": len(available) == 14
            and all(c["source_passed"] for c in available)
            and all(p["passed"] for p in repeat_pairs),
            "global_source_stability": "NOT_ESTABLISHED",
        }
    neutral_started = [c for c in checks if c.get("phase") == "neutral_control"]
    assert not neutral_started or gate["passed"], "GLOBAL_FOUR_ROW_GATE_VIOLATION"
    result = {
        "audit_passed": True,
        "four_row_gate": gate,
        "checks": checks,
        "tasks": tasks,
        "H1_status": "UNTESTED_POPULATION_HYPOTHESIS; fixed already inspected parent0 technical replays are not independent confirmation",
        "H2_status": "UNTESTED_NO_DECODER_NO_HELD_OUT_POLICY_STUDY",
        "global_stability": "NOT_ESTABLISHED_BY28SOURCE_EPISODES",
        "cause": "If isolated rows complete, the failed history/macro is executable in this topology. It does not identify the historical crash cause or prove accumulated process state was responsible.",
        "old_failed_attempts": "PRESERVED_UNKNOWN; new linked outcomes do not retroactively repair the two lost original traces",
        "full_pilot_and_stage2_resumed": False,
    }
    write_json(output / "summary.json", result)
    print(
        json.dumps(
            {
                "audit_passed": True,
                "four_row_gate": gate["passed"],
                "tasks": {
                    t: {
                        k: r[k]
                        for k in (
                            "attempted",
                            "returned_complete",
                            "limited_source_completion",
                            "worker_wall_seconds",
                        )
                    }
                    for t, r in tasks.items()
                },
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
