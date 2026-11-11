"""The small declared development grid; qualification never selects parameters."""

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

from .belief import build_belief
from .contracts import Parameters
from .episodes import generate_episodes
from .experiment import RecoveryCache, evaluate


def aggregate(rows):
    parents = defaultdict(list)
    for row in rows:
        parents[row["parent_id"]].append(row)
    fields = ("utility", "safe_task_completion", "unsafe_episode", "query_count")
    return {
        field: sum(
            sum(r[field] for r in group) / len(group) for group in parents.values()
        )
        / len(parents)
        for field in fields
    } | {"parents": len(parents), "decisions": len(rows)}


def select(root: Path):
    output = root / "selection"
    output.mkdir(exist_ok=False)
    raw = json.loads((root / "calibration/calibration.json").read_text())["parameters"]
    parameters = Parameters.model_validate(raw)
    tasks = json.loads((root / "tasks.json").read_text())
    episodes = [
        e
        for e in generate_episodes(tasks, "development", parameters)
        if e.regime in {"hidden_nominal", "no_external"}
    ]
    prior = {e.episode_id: build_belief(e.context) for e in episodes}
    repairs = RecoveryCache()
    summaries = []
    all_rows = []

    def compare(method, variant, changes):
        selected = parameters.model_copy(update=changes)
        rows = []
        for episode in episodes:
            context = episode.context.model_copy(update={"parameters": selected})
            trial = episode.model_copy(update={"context": context})
            row = evaluate(
                trial, method, 2, prior[episode.episode_id], repairs, "DEVELOPMENT_GRID"
            )
            row["variant"] = variant
            row["parameters"] = selected.model_dump(mode="json")
            rows.append(row)
        summary = {
            "method": method,
            "variant": variant,
            "parameters": selected.model_dump(mode="json"),
            **aggregate(rows),
        }
        summaries.append(summary)
        all_rows.extend(rows)
        return summary

    # Ties at numerical precision choose the more conservative threshold.
    theta_trials = [
        compare("B5", f"theta-{theta}", {"permission_threshold": theta})
        for theta in (0.85, 0.90, 0.95, 0.99)
    ]
    best = max(
        theta_trials,
        key=lambda s: (
            round(s["utility"], 12),
            s["parameters"]["permission_threshold"],
        ),
    )
    parameters = Parameters.model_validate(best["parameters"])
    d_trials = [
        compare("B2", f"period-{period}", {"periodic_interval": period})
        for period in (1, 2, 4)
    ]
    best_d = max(
        d_trials,
        key=lambda s: (round(s["utility"], 12), -s["parameters"]["periodic_interval"]),
    )
    parameters = parameters.model_copy(
        update={"periodic_interval": best_d["parameters"]["periodic_interval"]}
    )
    age_trials = [
        compare("B3", f"expiry-{age}", {"expiry_steps": age}) for age in (0, 1, 2, 4)
    ]
    best_age = max(
        age_trials,
        key=lambda s: (round(s["utility"], 12), -s["parameters"]["expiry_steps"]),
    )
    parameters = parameters.model_copy(
        update={"expiry_steps": best_age["parameters"]["expiry_steps"]}
    )
    final = [
        compare(method, "frozen-baseline", {}) for method in ("B2", "B3", "B4", "B5")
    ]
    primary = []
    for item in final:
        matched = [
            r
            for r in all_rows
            if r["method"] == item["method"]
            and r["variant"] == "frozen-baseline"
            and r["regime"] == "hidden_nominal"
        ]
        primary.append({"method": item["method"], **aggregate(matched)})
    chosen = min(
        primary,
        key=lambda s: (
            -round(s["utility"], 12),
            -s["safe_task_completion"],
            s["unsafe_episode"],
            s["query_count"],
            s["method"],
        ),
    )
    with gzip.open(output / "decisions.jsonl.gz", "wt", compresslevel=1) as stream:
        for row in all_rows:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    result = {
        "parameters": parameters.model_dump(mode="json"),
        "primary_baseline": chosen["method"],
        "selection_split": "development",
        "selection_regimes": ["hidden_nominal", "no_external"],
        "primary_selection_regime": "hidden_nominal",
        "budget": 2,
        "parameter_grid": summaries,
        "primary_candidates": primary,
        "development_parent_ids": sorted({e.parent_id for e in episodes}),
        "no_qualification_data_used": True,
    }
    (root / "selection.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "parameters": result["parameters"],
                "primary_baseline": chosen["method"],
                "primary_candidates": primary,
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    select(args.root)


if __name__ == "__main__":
    main()
