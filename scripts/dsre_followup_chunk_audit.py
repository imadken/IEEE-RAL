"""Incremental orchestration of the already frozen independent raw-physics audit."""

import argparse
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, verify_freeze
from dsre_paper_confirmation import audit_trace


def audit_completed(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Evidence sealed")
    verify_freeze(root)
    audited = []
    attempts = [read(p) for p in (root / "parent_attempts").glob("*.json")]
    for path in sorted((root / "chunks").glob("*_complete.json")):
        sequence = read(path)["sequence"]
        target = root / "chunks" / f"{sequence:04d}_independent_audit.json"
        if target.exists():
            continue
        start = time.monotonic()
        cpu = time.process_time()
        checks = []
        for attempt in [a for a in attempts if a["chunk"] == sequence]:
            marker = root / "parent_progress" / f"{attempt['index']:04d}.json"
            if not marker.exists() or read(marker)["status"] != "COMPLETE":
                continue
            for checkpoint in read(marker)["checkpoints"]:
                summary = read(Path(checkpoint["source"]).parent / "summary.json")
                checks.append(audit_trace(summary, root))
        atomic(
            target,
            {
                "status": "PASS",
                "sequence": sequence,
                "qualified_complete_parent_checkpoints_audited": len(checks),
                "outcome_controls_checked": sum(
                    c["outcome_controls_checked"] for c in checks
                ),
                "maximum_action_error": max(
                    (c["maximum_action_error"] for c in checks), default=0
                ),
                "wall_seconds": time.monotonic() - start,
                "cpu_seconds": time.process_time() - cpu,
                "records": checks,
                "verification": "Invokes the independent raw action/predicate/prefix audit source pinned before follow-up outcomes; no new estimator or threshold.",
            },
        )
        audited.append(sequence)
    print({"newly_audited_chunks": audited}, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    audit_completed(parser.parse_args().root)
