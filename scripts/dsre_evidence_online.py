"""Execute a frozen certificate library using observations and no outcome data."""

import argparse
import json
import time
from pathlib import Path

from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.schema import Bounds, Observation, Partition, Scope, Source
from dual_rec.evidence_aware.views import guard_data_access, save, sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument("model", type=Path)
    p.add_argument("observation", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    reads = guard_data_access(
        Path("results"),
        [a.model, a.observation],
        additional_roots=(a.model.parent.parent,),
    )
    model = json.loads(a.model.read_text())
    query = Observation.model_validate_json(a.observation.read_text()).model_dump(
        mode="json"
    )
    partition = Partition.model_validate(model["partition"])
    bounds = {
        int(c): Bounds.model_validate(v["bounds"])
        for c, v in model["leaves"].items()
        if v["bounds"] is not None
    }
    scope_matches = (
        query.get("source_scope") == model.get("source_scope")
        and model.get("source_scope") is not None
    )
    cert = (
        minimum(
            partition,
            query["x"],
            bounds,
            Source(model["source_type"]),
            outcome_scope=Scope.model_validate(model["source_scope"]),
        )
        if scope_matches
        else None
    )
    save(
        a.output,
        {
            "parent_id": query["parent_id"],
            "action": "r" if cert else "c",
            "certificate": cert.model_dump(mode="json") if cert else None,
            "model_sha256": sha(a.model),
            "successful_data_reads": list(reads),
            "selected_before_execution_epoch": time.time(),
            "status": "CERTIFIED_USEFUL_RECOVERY"
            if cert
            else "UNQUALIFIED"
            if scope_matches
            else "SCOPE_MISMATCH",
            "fallback": "continue; explicit defer retained as separate protocol",
        },
    )


if __name__ == "__main__":
    main()
