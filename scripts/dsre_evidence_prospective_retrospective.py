"""Inspected historical acquisition curves; no confirmation or PAC claim."""

import json
from collections import Counter

from dsre_evidence_prospective import BUDGETS, OLD, ROOT, STRATEGIES

from dual_rec.evidence_aware.acquisition import allocate
from dual_rec.evidence_aware.bounds import calibrate, qualifies, solve
from dual_rec.evidence_aware.diagnosis import diagnose
from dual_rec.evidence_aware.partition import fit, route
from dual_rec.evidence_aware.schema import OneAction, Pair
from dual_rec.evidence_aware.views import hashed, save, sha


def main():
    historical = OLD / "historical"
    read = lambda p: json.loads(p.read_text())
    discovery = [
        OneAction.model_validate(r) for r in read(historical / "learner/discovery.json")
    ]
    vocabulary = tuple(read(historical / "learner/vocabulary.json"))
    candidates = read(historical / "learner/calibration.json") + read(
        historical / "learner/evaluation.json"
    )
    assert len(candidates) == 568
    partition = fit(discovery, vocabulary)
    masses = Counter(route(partition, r.x) for r in discovery)
    diagnostic = {}
    for c in masses:
        e, _ = calibrate(
            [r for r in discovery if route(partition, r.x) == c],
            [],
            f"development-diagnostic:{c}",
            len(masses),
        )
        b = solve(e)
        diagnostic[c] = (
            diagnose(e).status,
            b.harm_upper - b.harm_lower,
            b.gain_upper - b.gain_lower,
        )
    schedules = {}
    for strategy in STRATEGIES:
        requested = allocate(strategy, diagnostic, masses, 512)
        used = set()
        rows = []
        spent = 0
        for c, kind in requested.requests:
            available = [
                r
                for r in candidates
                if r["parent_id"] not in used and route(partition, r["x"]) == c
            ]
            if not available:
                available = [r for r in candidates if r["parent_id"] not in used]
            if not available:
                break
            chosen = min(
                available,
                key=lambda r: hashed("historical-acquisition:" + r["parent_id"]),
            )
            used.add(chosen["parent_id"])
            cost = 2 if kind == "pair" else 1
            boundary = next(b for b in BUDGETS if b > spent)
            if spent + cost > boundary:
                kind, cost = "log", 1
            spent += cost
            rows.append(
                {
                    "parent_id": chosen["parent_id"],
                    "kind": kind,
                    "cost": cost,
                    "cumulative_cost": spent,
                }
            )
        while spent < 512:
            available = [r for r in candidates if r["parent_id"] not in used]
            chosen = min(
                available,
                key=lambda r: hashed("historical-acquisition:" + r["parent_id"]),
            )
            used.add(chosen["parent_id"])
            spent += 1
            rows.append(
                {
                    "parent_id": chosen["parent_id"],
                    "kind": "log",
                    "cost": 1,
                    "cumulative_cost": spent,
                }
            )
        schedules[strategy] = {
            str(b): [r for r in rows if r["cumulative_cost"] <= b] for b in BUDGETS
        }
    out = ROOT / "historical_acquisition_v3"
    save(
        out / "schedule.json",
        {
            "schedules": schedules,
            "partition": partition.model_dump(mode="json"),
            "discovery": len(discovery),
            "candidate_count": len(candidates),
            "population": "960 previously inspected DEVELOPMENT parents",
            "status": "retrospective only; no independent performance test or PAC confirmation claim",
            "information": "schedule code reads observed-arm discovery and candidate contexts before paired labels; original data already inspected",
            "old_method": "original five-strategy allocator retained for historical mechanism curve; prospective decision-information comparator is stronger",
        },
    )
    # Read paired labels only after the retrospective schedules have been serialized.
    allpairs = read(historical / "paired_refinement/calibration.json") + read(
        historical / "evaluator/evaluation_pairs.json"
    )
    pairs = {r["parent_id"]: Pair.model_validate(r) for r in allpairs}
    logs = {r["parent_id"]: OneAction.model_validate(r) for r in candidates}
    results = []
    for strategy, bs in schedules.items():
        for budget, requests in bs.items():
            selectedlogs = [logs[r["parent_id"]] for r in requests]
            selectedpairs = [
                pairs[r["parent_id"]] for r in requests if r["kind"] == "pair"
            ]
            leaves = {}
            for c in masses:
                ls = [r for r in selectedlogs if route(partition, r.x) == c]
                ps = [r for r in selectedpairs if route(partition, r.x) == c]
                e, ledger = calibrate(ls, ps, f"development-leaf:{c}", len(masses))
                b = solve(e)
                leaves[c] = {
                    "qualified": qualifies(b),
                    "bounds": b.model_dump(mode="json"),
                    "ledger": ledger,
                }
            results.append(
                {
                    "strategy": strategy,
                    "budget": int(budget),
                    "logical_cost": sum(r["cost"] for r in requests),
                    "qualified_discovery_mass": sum(
                        masses[c] for c, l in leaves.items() if l["qualified"]
                    )
                    / len(discovery),
                    "leaves": leaves,
                    "status": "inspected development; coverage on discovery mass; no held-out gain claim",
                }
            )
    save(
        out / "results.json",
        {"schedule_sha256": sha(out / "schedule.json"), "curves": results},
    )
    print(
        json.dumps(
            [
                {
                    k: r[k]
                    for k in (
                        "strategy",
                        "budget",
                        "logical_cost",
                        "qualified_discovery_mass",
                    )
                }
                for r in results
            ]
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
