"""Fixed secondary summaries, cost accounting and research-review figures."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from dual_rec.contracts.claims import discordance_upper


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def run(root):
    cfg = read(root / "registration.json")
    rows = read(root / "all_outcomes.json")
    certs = read(root / "all_certificates.json")
    ranks = defaultdict(dict)
    costs = defaultdict(list)
    for r in rows:
        if r["route"] not in ("parent_rng", "missing_provenance"):
            costs[(r["split"], r["task"], r["route"])].append(r)
        if r["reference_qualified"] and r["prefix_ok"]:
            key = (r["split"], r["task"], r["condition"], r["route"], r["seed"])
            ranks[key][r["action"]] = r
    rank_groups = defaultdict(list)
    for key, actions in ranks.items():
        if len(actions) != 2:
            continue
        a, b = actions["continue"], actions["recover"]
        ref = int(b["reference_success"]) - int(a["reference_success"])
        observed = int(b["success"]) - int(a["success"])
        rank_groups[key[:-1]].append((ref, observed))
    contrasts = []
    for key, values in rank_groups.items():
        contrasts.append(
            dict(zip(["split", "task", "condition", "route"], key, strict=True))
            | {
                "parents": len(values),
                "ranking_changes": sum(np.sign(a) != np.sign(b) for a, b in values),
                "contrast_disagreements": sum(a != b for a, b in values),
                "reference_mean": float(np.mean([a for a, _ in values])),
                "candidate_mean": float(np.mean([b for _, b in values])),
                "absolute_mean_difference": abs(
                    float(np.mean([b - a for a, b in values]))
                ),
                "scope": "Paired recorded binary contrasts; primary F3 bound uses union of two action discordance bounds, not ranking alone",
            }
        )
    save(root / "decision_contrasts.json", contrasts)
    bounds = []
    for split in ["development", "confirmation"]:
        for task in cfg["tasks"]:
            ids = sorted(cfg["seeds"][task][split])
            for method in sorted({c["method"] for c in certs}):
                selected = [
                    c
                    for c in certs
                    if c["split"] == split
                    and c["task"] == task
                    and c["method"] == method
                    and c["control_status"] == "invalid"
                ]
                by_parent = defaultdict(list)
                for c in selected:
                    by_parent[int(c["parent"])].append(c)
                clusters = [
                    [c for p in pair for c in by_parent[p]]
                    for pair in zip(ids[::2], ids[1::2], strict=True)
                ]
                clusters = [cs for cs in clusters if cs]
                errors = sum(
                    any(c["status"] == "SUPPORTED" for c in cs) for cs in clusters
                )
                bounds.append(
                    {
                        "split": split,
                        "task": task,
                        "method": method,
                        "invalid_records": len(selected),
                        "accepted_records": sum(
                            c["status"] == "SUPPORTED" for c in selected
                        ),
                        "parent_pair_clusters": len(clusters),
                        "clusters_with_acceptance": errors,
                        "upper": discordance_upper(errors, len(clusters), 0.05 / 3),
                        "alpha": 0.05 / 3,
                        "scope": "Any invalid-variant acceptance per fixed pair; three-task simultaneous family per method, not all methods",
                    }
                )
    save(root / "invalid_acceptance_bounds.json", bounds)
    accounting = []
    for key, values in costs.items():
        measured = [
            v["route_wall_seconds"] for v in values if "route_wall_seconds" in v
        ]
        accounting.append(
            dict(zip(["split", "task", "route"], key, strict=True))
            | {
                "continuations": len(values),
                "continuations_with_timing": len(measured),
                "wall_seconds_sum": sum(measured),
                "wall_seconds_median": float(np.median(measured)) if measured else None,
                "prefix_controls": sum(
                    v.get("prefix_controls_executed", 0) for v in values
                ),
                "continuation_controls": len(values) * 70,
                "scope": "Measured route creation/restoration plus prefix and continuation where applicable; source references counted separately in checkpoints",
            }
        )
    save(root / "qualification_costs.json", accounting)
    workflows = []
    for split in ["development", "confirmation"]:
        for task in cfg["tasks"]:
            for method in sorted({c["method"] for c in certs}):
                selected = [
                    c
                    for c in certs
                    if c["split"] == split
                    and c["task"] == task
                    and c["method"] == method
                    and c["route"] == "native_snapshot"
                ]
                workflows.append(
                    {
                        "split": split,
                        "task": task,
                        "method": method,
                        "native_claims": len(selected),
                        "supported": sum(c["status"] == "SUPPORTED" for c in selected),
                        "prefix_completed": sum(
                            c["completed_with_prefix"] for c in selected
                        ),
                        "unsupported": sum(
                            c["status"] != "SUPPORTED" for c in selected
                        ),
                        "scope": "All references and controls were actually collected; hypothetical avoided replay is not measured campaign savings",
                    }
                )
    save(root / "workflow_costs.json", workflows)
    examples = []
    for label, predicate in [
        (
            "decision_sufficient_trace_mismatch",
            lambda c: (
                c["route"] == "native_snapshot"
                and c["F1"] == "PASS"
                and not c["F2"]
                and c["F3"]["passed"]
            ),
        ),
        ("wrong_physics", lambda c: c["route"] == "physics"),
        ("missing_model", lambda c: c["route"] == "missing_provenance"),
        ("wrong_parent", lambda c: c["route"] == "parent_rng"),
    ]:
        selected = next(
            (
                c
                for c in certs
                if c["method"] == "M" and c["split"] == "confirmation" and predicate(c)
            ),
            None,
        )
        examples.append(
            {
                "case": label,
                "certificate": selected,
                "availability": "observed"
                if selected
                else "not observed; no manufactured example",
            }
        )
    save(root / "explanation_examples.json", examples)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    es = [
        e
        for e in read(root / "E_effects.json")
        if e["split"] == "confirmation" and e["population"] == "all" and e["n"]
    ]
    if es:
        fig, ax = plt.subplots(figsize=(8, 4))
        for i, e in enumerate(es):
            lo, hi = e["conservative_exact_difference_ci95"]
            ax.errorbar(
                e["difference"],
                i,
                xerr=[[e["difference"] - lo], [hi - e["difference"]]],
                fmt="o",
                color="black",
            )
        ax.set_yticks(
            range(len(es)),
            [e["task"] + "/" + e["condition"] + f" (n={e['n']})" for e in es],
        )
        ax.axvline(0, color="gray", linewidth=1)
        ax.set_xlabel(
            "Recovery minus continue: terminal success; conservative paired 95% CI"
        )
        fig.tight_layout()
        fig.savefig(figures / "paired_physical_effects.png", dpi=160)
        plt.close(fig)
    print(
        {
            "contrasts": len(contrasts),
            "bounds": len(bounds),
            "cost_cells": len(accounting),
        }
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    run(p.parse_args().root)
