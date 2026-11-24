"""Independent review of an observed stopped-macro endpoint; no new physics."""

import hashlib
import json
import sys
from pathlib import Path

from dsre_evidence_lossless import read
from dsre_evidence_prospective_audit import physical


def main():
    path, output = map(Path, sys.argv[1:])
    record = read(path)
    assert record["status"] == "OBSERVED_ABORT_ENDPOINT"
    assert record["error"] == "UPSTREAM_SCREW_PLANNING_FAILED"
    assert (
        record["phase"] == "post"
        and record["action_stopped"]
        and record["terminal_observed"]
    )
    assert isinstance(record["success"], bool)
    physical(record, "PegInsertionSide-v1")
    assert not any(name.startswith("dual_rec.evidence_aware") for name in sys.modules)
    result = {
        "passed": True,
        "trace": str(path),
        "success": record["success"],
        "executed_future_controls": record["executed_controls"],
        "observation": "Actual finite source-evaluable endpoint of the stopped fixed macro; never source-excluded or imputed",
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
