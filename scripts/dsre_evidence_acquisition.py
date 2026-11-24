"""Equal-cost DEVELOPMENT evidence reveals with disjoint diagnostic/calibration pools."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from dual_rec.evidence_aware.acquisition import allocate
from dual_rec.evidence_aware.bounds import calibrate, solve
from dual_rec.evidence_aware.diagnosis import diagnose
from dual_rec.evidence_aware.partition import fit, route
from dual_rec.evidence_aware.views import (
    guard_data_access,
    hashed,
    load_logs,
    save,
    sha,
)

STRATEGIES = ("witness", "all_logs", "all_pairs", "uniform_mix", "decision_uncertainty")


def prepare(root):
    out = root / "acquisition"
    logs = json.loads((root / "learner/calibration.json").read_text())
    pairs = json.loads((root / "paired_refinement/calibration.json").read_text())
    diagnostic = [
        r for r in logs if hashed("diagnostic-pool:" + r["parent_id"]) % 2 == 0
    ]
    final = [r for r in logs if hashed("diagnostic-pool:" + r["parent_id"]) % 2 != 0]
    ids = {r["parent_id"] for r in final}
    save(out / "diagnostic.json", diagnostic)
    save(
        out / "candidates.json",
        [{k: r[k] for k in ("parent_id", "x", "action")} for r in final],
    )
    save(out / "evaluator/final_logs.json", final)
    save(
        out / "evaluator/final_pairs.json", [r for r in pairs if r["parent_id"] in ids]
    )
    for name in ("discovery.json", "vocabulary.json"):
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "learner" / name, out / name)
    save(
        out / "protocol.json",
        {
            "budget_executions": 64,
            "pool_namespace": "diagnostic-pool:",
            "diagnostic_parents": len(diagnostic),
            "independent_final_parents": len(final),
            "confidence": "one fixed final allocation per strategy; curves descriptive, no simultaneous budget claim",
            "status": "Historical development masked evidence acquisition, not new physics execution",
            "fairness": "shared discovery partition; same64 revealed action outcomes; balanced single-arm requests; pair costs2",
            "strategies": list(STRATEGIES),
        },
    )


def plan(root):
    out = root / "acquisition"
    allowed = [
        out / n
        for n in (
            "diagnostic.json",
            "candidates.json",
            "discovery.json",
            "vocabulary.json",
            "protocol.json",
        )
    ]
    reads = guard_data_access(Path("results"), allowed, additional_roots=(out,))
    discovery = load_logs(out / "discovery.json")
    diagnostic = load_logs(out / "diagnostic.json")
    candidates = json.loads((out / "candidates.json").read_text())
    vocab = tuple(json.loads((out / "vocabulary.json").read_text()))
    partition = fit(discovery, vocab)
    masses = Counter(route(partition, r.x) for r in discovery)
    summaries = {}
    for c in masses:
        logs = [r for r in diagnostic if route(partition, r.x) == c]
        e, _ = calibrate(logs, [], f"diagnostic-leaf:{c}", len(masses))
        w = diagnose(e)
        try:
            b = solve(e)
            widths = b.harm_upper - b.harm_lower, b.gain_upper - b.gain_lower
        except ValueError:
            widths = 1.0, 2.0
        summaries[c] = (w.status, *widths)
    allocations = {}
    for strategy in STRATEGIES:
        a = allocate(strategy, summaries, masses, 64)
        used = set()
        requests = []
        arm_counts = Counter()
        for i, (c, kind) in enumerate(a.requests):
            population = [
                r
                for r in candidates
                if route(partition, r["x"]) == c and r["parent_id"] not in used
            ]
            if kind == "log":
                target = ("c", "r")[arm_counts[c] % 2]
                population = [r for r in population if r["action"] == target]
                arm_counts[c] += 1
            if not population:
                raise RuntimeError(
                    "Prespecified acquisition budget exceeds available outcome-blind support"
                )
            r = min(population, key=lambda v: hashed("acquire:" + v["parent_id"]))
            used.add(r["parent_id"])
            requests.append(
                {
                    "parent_id": r["parent_id"],
                    "leaf": c,
                    "kind": kind,
                    "cost": 2 if kind == "pair" else 1,
                }
            )
        allocations[strategy] = {
            "allocation": a.model_dump(mode="json"),
            "selected": requests,
        }
    save(
        out / "allocation_freeze.json",
        {
            "partition": partition.model_dump(mode="json"),
            "diagnostic": summaries,
            "allocations": allocations,
            "input_whitelist_sha256": {str(p): sha(p) for p in allowed},
            "successful_data_reads": list(reads),
            "final_outcomes_accessed": False,
        },
    )


def execute(root):
    out = root / "acquisition"
    plan = json.loads((out / "allocation_freeze.json").read_text())
    logs = {
        r["parent_id"]: r
        for r in json.loads((out / "evaluator/final_logs.json").read_text())
    }
    pairs = {
        r["parent_id"]: r
        for r in json.loads((out / "evaluator/final_pairs.json").read_text())
    }
    for strategy, data in plan["allocations"].items():
        run = out / strategy
        for name, source in (
            ("discovery.json", root / "learner/discovery.json"),
            ("vocabulary.json", root / "learner/vocabulary.json"),
            ("queries.json", root / "learner/queries.json"),
        ):
            (run / "learner").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, run / "learner" / name)
        selected = data["selected"]
        save(run / "learner/calibration.json", [logs[r["parent_id"]] for r in selected])
        save(
            run / "paired_refinement/calibration.json",
            [pairs[r["parent_id"]] for r in selected if r["kind"] == "pair"],
        )
        (run / "evaluator").mkdir(exist_ok=True)
        shutil.copyfile(
            root / "evaluator/evaluation_pairs.json",
            run / "evaluator/evaluation_pairs.json",
        )
        regime = (
            "paired_equal_parent"
            if any(r["kind"] == "pair" for r in selected)
            else "logged"
        )
        for stage in ("learn", "evaluate"):
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "dual_rec.evidence_aware.cli",
                    stage,
                    str(run),
                    "--regime",
                    regime,
                ],
                check=True,
                env=os.environ.copy(),
            )
        model = json.loads((run / "models" / (regime + ".json")).read_text())
        # Mixed acquisitions charge one outcome per log + one counterpart per pair.
        actual = len(selected) + sum(r["kind"] == "pair" for r in selected)
        assert actual == data["allocation"]["executions"] == 64
        evaluation = json.loads((run / "evaluations" / (regime + ".json")).read_text())
        save(
            run / "acquisition_result.json",
            {
                "strategy": strategy,
                "charged_action_outcomes": actual,
                "single_only_parents": sum(r["kind"] == "log" for r in selected),
                "paired_parents": sum(r["kind"] == "pair" for r in selected),
                "DSRE": evaluation["policies"]["DSRE"],
                "model_source": "mixed logs/paired refinement"
                if regime.startswith("paired")
                else "logs",
                "certificate_note": "Independent fixed-size final calibration; diagnostic outcomes excluded",
                "input_leakage": model["successful_data_reads"],
            },
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=("prepare", "plan", "execute"))
    p.add_argument("root", type=Path)
    a = p.parse_args()
    {"prepare": prepare, "plan": plan, "execute": execute}[a.stage](a.root)
