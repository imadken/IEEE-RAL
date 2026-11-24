"""Read-only independent first-violation census; never imports a simulator."""

import argparse
import csv
import hashlib
import json
from itertools import pairwise
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.repo / "research/rpd_assembly_preliminary_20261120"
    measurements = json.loads(
        (evidence / "audit/terminal_measurements.json").read_text()
    )
    independent = json.loads((evidence / "audit/independent_summary.json").read_text())
    rows = []
    matched_keys = set()
    for original in measurements:
        if original["repeat"]:
            continue
        key = (original["candidate_id"], original["intervention"], original["action"])
        if key in matched_keys:
            raise AssertionError(f"Repeated independent-branch key: {key}")
        matched_keys.add(key)
        path = args.repo / original["trace"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != original["trace_sha256"]:
            raise AssertionError(f"Source hash mismatch: {path}")
        frames = [json.loads(line) for line in raw.splitlines()]
        postroot = [frame for frame in frames if frame["substep"] > 150]
        if len(postroot) != 400:
            raise AssertionError("Expected four-second 100 Hz post-root trace")
        for before, after in pairwise(frames):
            if after["substep"] != before["substep"] + 1:
                raise AssertionError("Noncontiguous source clock")
        completion = any(frame["completion_flag"] for frame in postroot)
        if completion != original["completion"]:
            raise AssertionError("Independent recorded completion flag mismatch")
        constraints = list(postroot[0]["constraint_checks"])
        row = dict(zip(("parent", "intervention", "action"), key))
        row["completion"] = completion
        row["source_trace"] = original["trace"]
        row["source_trace_sha256"] = original["trace_sha256"]
        row["macro_first_substep"] = 151 if key[1] == "direct" else 201
        for constraint in constraints:
            failures = [
                f["substep"] for f in postroot if not f["constraint_checks"][constraint]
            ]
            if len(failures) != original["violations_100Hz"][constraint]:
                raise AssertionError(f"Constraint census mismatch: {constraint}")
            row[constraint + "_first_substep"] = min(failures) if failures else None
        for field in (
            "tcp_residual_m",
            "grasp_slip_translation_m",
            "grasp_slip_rotation_rad",
            "peg_fixture_force_N",
        ):
            row[field + "_peak"] = max(frame[field] for frame in postroot)
        rows.append(row)
    if len(rows) != 49 or len({r["parent"] for r in rows}) != 7:
        raise AssertionError("Historical source denominator differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "historical_first_violations.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "scope": "HISTORICAL_UNQUALIFIED_SOURCE; no new physics; timing is descriptive, not a cause diagnosis",
        "candidate_counts": independent["candidate_counts"],
        "distinct_terminal_branches": len(rows),
        "technical_parents": len({row["parent"] for row in rows}),
        "successful_completions": sum(row["completion"] for row in rows),
        "same_four_second_remaining_clock": True,
        "constraint_census": {},
        "new_source_attempts": 0,
        "new_exploratory_parents": 0,
        "new_confirmation_parents": 0,
    }
    for constraint in constraints:
        values = [row[constraint + "_first_substep"] for row in rows]
        failures = [v for v in values if v is not None]
        summary["constraint_census"][constraint] = {
            "branches_violating": len(failures),
            "first_failure_substep_min": min(failures) if failures else None,
            "first_failure_substep_max": max(failures) if failures else None,
            "first_failure_during_probe_or_hold": sum(
                value is not None and value < row["macro_first_substep"]
                for row, value in zip(rows, values)
            ),
        }
    (args.output_dir / "historical_source_preflight.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
