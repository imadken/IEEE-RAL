"""Apply one descriptive interval convention to frozen historical decisions."""

from collections import Counter
from pathlib import Path

from dsre_last_audit import metrics
from dsre_last_common import ROOT, read, save, sha


def main():
    tasks = {}
    for task in ("PickCube-v1", "PointMaze_UMaze-v3"):
        base = (
            Path("results/dsre-evidence-aware/20261117-prospective/prospective") / task
        )
        ep = base / "evaluations/logged.json"
        original = read(ep)
        rows = []
        for decision in original["decisions"]:
            pp = base / "evaluator" / (decision["parent_id"] + ".json")
            pair = read(pp)
            rows.append(
                {
                    "parent_id": decision["parent_id"],
                    "yc": pair["yc"],
                    "yr": pair["yr"],
                    "decision": decision,
                }
            )
        policies = metrics(rows)
        for method, p in policies.items():
            old = original["policies"][method]
            for new_name, old_name in [
                ("success", "success"),
                ("recover", "recover"),
                ("harm", "harm"),
                ("required_rescues", "required_rescues"),
                ("futile", "futile"),
            ]:
                assert p[new_name] == old[old_name]
        if task == "PickCube-v1":
            regression = read(ROOT / "legacy_regression/evaluation.json")
            assert {r["parent_id"] for r in regression["rows"]} == {
                r["parent_id"] for r in rows
            }
            policies.update(regression["policies"])
        tasks[task] = {
            "policies": policies,
            "four_cells": dict(Counter(f"{int(r['yc'])}{int(r['yr'])}" for r in rows)),
            "source_evaluation_sha256": sha(ep),
            "n": len(rows),
        }
    save(
        ROOT / "legacy_policy_rescoring.json",
        {
            "tasks": tasks,
            "role": "Previously inspected historical independent tests; original frozen outcomes/decisions unchanged; regression retrospectively frozen by the final registered conventional algorithm.",
            "intervals": "Common independent-parent bootstrap4000 draws seed2026111801 and descriptive exact CP95; original historical reports/intervals preserved. No across-method joint95 or hindsight optimality significance claim.",
        },
    )


if __name__ == "__main__":
    main()
