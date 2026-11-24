"""Constructive C-only certificate/obstruction records after the model freeze."""

from collections import Counter
from pathlib import Path

from dsre_last_common import ROOT, read, save, sha

from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.diagnosis import plugin_diagnosis
from dual_rec.evidence_aware.partition import assignments, route
from dual_rec.evidence_aware.schema import Bounds, Evidence, Partition, Scope, Source
from dual_rec.evidence_aware.views import guard_data_access


def main():
    reads = guard_data_access(
        Path("results"), [ROOT / "model_frozen.json", ROOT / "learner/calibration.json"]
    )
    model = read(ROOT / "model_frozen.json")
    logs = read(ROOT / "learner/calibration.json")
    p = Partition.model_validate(model["partition"])
    scope = Scope.model_validate(model["source_scope"])
    bs = {
        int(c): Bounds.model_validate(v["bounds"])
        for c, v in model["leaves"].items()
        if v["bounds"]
    }
    leaves = {}
    for c, entry in model["leaves"].items():
        rows = [r for r in logs if route(p, r["x"]) == int(c)]
        arms = [[r["y"] for r in rows if r["action"] == a] for a in ("c", "r")]
        means = [sum(v) / len(v) if v else 0 for v in arms]
        diagnosis = plugin_diagnosis(Evidence.model_validate(entry["evidence"]), *means)
        leaves[c] = {
            "diagnosis": diagnosis.model_dump(mode="json"),
            "point_marginals": means,
            "obstruction_optimizers": entry["bounds"]["optimizers"]
            if entry["bounds"]
            else None,
        }
    queries = []
    for x in assignments(6):
        certs = {}
        for obligation in ("useful", "harm_only", "completion"):
            c = minimum(p, x, bs, Source.LOGGED, obligation, outcome_scope=scope)
            certs[obligation] = c.model_dump(mode="json") if c else None
        queries.append({"x": x, "leaf": route(p, x), "certificates": certs})
    save(
        ROOT / "source_obligation_witnesses.json",
        {
            "source": "C-only; no test labels or counterparts opened by this explanation process",
            "model_sha256": sha(ROOT / "model_frozen.json"),
            "successful_reads": list(reads),
            "leaves": leaves,
            "queries": queries,
            "analytical_same_marginal_worlds": [
                {"q": [0.4, 0.2, 0, 0.4], "pc": 0.4, "pr": 0.6, "gain": 0.2, "harm": 0},
                {"q": [0, 0.6, 0.4, 0], "pc": 0.4, "pr": 0.6, "gain": 0.2, "harm": 0.4},
            ],
            "status_counts": dict(
                Counter(v["diagnosis"]["status"] for v in leaves.values())
            ),
            "note": "Full64 Boolean cube enumerates declared logical scopes, not64 physically observed checkpoints. Actual query frequencies and finite-reference opposing-action/both-failure witnesses are separately in evidence_frontier.json.",
        },
    )


if __name__ == "__main__":
    main()
