"""Scientific review figures, known baseline identities and one dormant prospective plan."""

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dsre_repair_analyze import model_outputs


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def review(root):
    metrics = load(root / "metrics.json")
    profiles = load(root / "full_reference_frontiers.json")
    finite = load(root / "finite_profiles.json")
    outputs = defaultdict(dict)
    overlap = defaultdict(Counter)
    for design, d, p, result in model_outputs(root):
        key = (design["task"], d["selector"], d["budget"], p["id"])
        outputs[key][p["method"]] = result
        if p["method"] == "DSRE":
            causes = tuple(
                sorted(o["kind"] for o in result["diagnosis"]["obstructions"])
            )
            overlap[f"{design['task']}|{d['selector']}|{d['budget']}"][
                "+".join(causes) if causes else "STRICT_RECOMMENDATION"
            ] += 1
    identities = {}
    for t in ("PickCube-v1", "PushCube-v1"):
        for b in range(4):
            total = equal_b7 = equal_two = 0
            for (task, selector, budget, id), methods in outputs.items():
                if task != t or budget != b:
                    continue
                total += 1
                a = methods["DSRE"]
                b7 = methods["B7"]
                two = methods["B1_two_strict"]
                equal_b7 += all(a[f] == b7[f] for f in ("action", "evidence")) and (
                    not a["action"] or a["support"] == b7["support"]
                )
                equal_two += all(a[f] == two[f] for f in ("action", "evidence"))
            identities[f"{t}|{b}"] = {
                "views": total,
                "DSRE_B7_equal": equal_b7,
                "DSRE_pure_two_literal_equal": equal_two,
            }
    save(root / "baseline_identities.json", identities)
    save(root / "obstruction_overlap.json", {k: dict(v) for k, v in overlap.items()})
    directory = root / "figures"
    directory.mkdir(exist_ok=True)
    colors = {
        "exact_coverage": "tab:blue",
        "greedy_coverage": "tab:orange",
        "greedy_entropy": "tab:green",
        "canonical": "tab:red",
        "random": "tab:purple",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, t in zip(axes, ("PickCube-v1", "PushCube-v1"), strict=True):
        for selector, color in colors.items():
            selected = [profiles[t][f"{selector}|{b}"] for b in range(4)]
            ax.plot(
                [len(p["channels"]) for p in selected],
                [
                    p["profile"]["finite_profile"]["actionable_mass"] / 422 * 100
                    for p in selected
                ],
                marker="o",
                label=selector,
                color=color,
                alpha=0.8,
            )
        upper = (
            finite[t]["diagnostics"]["all"]["profile"]["absolute_actionable_upper_mass"]
            / 422
            * 100
        )
        ax.axhline(upper, color="black", linestyle=":", label="non-neither upper bound")
        allmass = (
            finite[t]["diagnostics"]["all"]["profile"]["actionable_mass"] / 422 * 100
        )
        ax.scatter(
            [6],
            [allmass],
            marker="*",
            s=110,
            color="black",
            label="all six: diagnostic",
        )
        ax.set(
            title=t,
            xlabel="Added abstract predicate channels",
            ylabel="Full-table actionable ceiling (%)",
            ylim=(-2, 102),
            xlim=(-0.15, 6.2),
        )
        ax.grid(alpha=0.2)
    axes[1].legend(fontsize=7)
    fig.suptitle(
        "Offline finite reference: channel cost is not sensor hardware, time or energy"
    )
    fig.savefig(directory / "finite_frontier.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for col, t in enumerate(("PickCube-v1", "PushCube-v1")):
        for selector, color in colors.items():
            cells = [
                metrics[f"{t}|{selector}|{b}|DSRE|all_starts|all"] for b in range(4)
            ]
            x = [c["rates"]["mean_added_channels"]["value"] for c in cells]
            axes[0, col].plot(
                x,
                [
                    c["rates"]["successful_strict_coverage"]["value"] * 100
                    for c in cells
                ],
                marker="o",
                color=color,
                label=selector,
            )
            axes[1, col].plot(
                x,
                [
                    c["rates"]["unsuccessful_action_per_checkpoint"]["value"] * 100
                    for c in cells
                ],
                marker="o",
                color=color,
                label=selector,
            )
        axes[0, col].set(
            title=t,
            ylabel="Successful strict-reference choices / all (%)",
            ylim=(-2, 72),
        )
        axes[1, col].set(
            xlabel="Mean added abstract predicate channels",
            ylabel="Unacceptable recommendations / all (%)",
            ylim=(-0.1, 2),
        )
        for ax in axes[:, col]:
            ax.grid(alpha=0.2)
    axes[0, 1].legend(fontsize=7)
    fig.suptitle(
        "Exploratory grouped cross-fit; errors prevent zero-error claims; no hardware/time/energy cost measured"
    )
    fig.savefig(directory / "held_out_frontier.png", dpi=160)
    plt.close(fig)
    graph = load(root / "ambiguity_graph.json")["PushCube-v1"]
    edges = graph["ambiguity_edges"]
    vertices = {id for e in edges for id in e["ids"]}
    data = {v["id"]: v for v in graph["vertices"]}
    left = sorted(id for id in vertices if data[id]["good"] == ["continue"])
    right = sorted(vertices - set(left))
    positions = {id: (0, i) for i, id in enumerate(left)} | {
        id: (1, i) for i, id in enumerate(right)
    }
    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    for e in edges:
        a, b = (positions[id] for id in e["ids"])
        ax.plot([a[0], b[0]], [a[1], b[1]], color="gray", alpha=0.7)
    for id, (x, y) in positions.items():
        ax.scatter(
            [x], [y], s=80, color="tab:blue" if x == 0 else "tab:orange", zorder=3
        )
        ax.text(
            x + (-0.025 if x == 0 else 0.025),
            y,
            id,
            ha="right" if x == 0 else "left",
            va="center",
            fontsize=8,
        )
    ax.set(
        xlim=(-1.2, 2.2),
        ylim=(-0.4, max((p[1] for p in positions.values()), default=0) + 0.5),
        title="PushCube: all six opposing-action edges remain inseparable on the declared menu",
    )
    ax.axis("off")
    fig.suptitle(
        "Actual witness graph; optional cost = abstract predicates, not hardware/time/energy"
    )
    fig.savefig(directory / "ambiguity_graph.png", dpi=160)
    plt.close(fig)
    # One conditional, frozen future plan, explicitly not justified for execution by this gate.
    assignments = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        for action in ("continue", "recover"):
            c = metrics[f"{task}|exact_coverage|1|DSRE|all_starts|{action}"]["counts"]
            rate = c["recommended"] / 422
            assignments[task + "/" + action] = {
                "crossfit_assigned": c["recommended"],
                "denominator": 422,
                "frequency": rate,
                "expected_from_200": 200 * rate,
                "expected_parents_for_42": math.ceil(42 / rate) if rate else None,
                "expected_from_conditional_calibration_plan": (
                    1400 if task == "PickCube-v1" else 200
                )
                * rate,
            }
    plan = {
        "status": "DORMANT_NOT_JUSTIFIED_FOR_EXECUTION",
        "count": 1,
        "authorization": "No fresh physics authorized; supervisor must first resolve scientific distinctiveness and Push observability limits",
        "purpose": "If later justified, prospectively test the single lowest nonzero registered instrumentation budget (b=1), selected on full development training only",
        "method": {
            "budget": 1,
            "PickCube-v1_channels": profiles["PickCube-v1"]["exact_coverage|1"][
                "channels"
            ],
            "PushCube-v1_channels": profiles["PushCube-v1"]["exact_coverage|1"][
                "channels"
            ],
            "controller_actions_horizon_features": "unchanged current fixed repertoire and telemetry thresholds",
            "router_reference_sha256": hashlib.sha256(
                (root / "full_reference_frontiers.json").read_bytes()
            ).hexdigest(),
        },
        "calibration_parents": {"PickCube-v1": 1400, "PushCube-v1": 200},
        "confirmation_parents": {"PickCube-v1": 1400, "PushCube-v1": 200},
        "sampling": "one existing condition per independent fresh seed, balanced before outcomes; calibration/confirmation/development pools disjoint; no seed manifest or workers launched",
        "alpha": 0.1,
        "delta": 0.05,
        "strata": 4,
        "per_stratum_delta": 0.0125,
        "zero_error_assigned_required": 42,
        "gating": "freeze whole router; missing or unsupported stratum disables its proposed action, no rerouting; never pool unused Push strata",
        "assignments": assignments,
        "total_new_parents_if_separately_authorized": 3200,
        "matched_reference_and_fresh_branches_per_parent": 4,
        "total_branches_if_authorized": 12800,
        "postcheckpoint_controls_if_authorized": 896000,
        "historical_pair_fresh_median_seconds": {
            "PickCube-v1": 3.9696,
            "PushCube-v1": 2.6377,
        },
        "serial_wall_estimate_hours_with_1_5_overhead": (
            2800 * 2 * 3.9696 + 400 * 2 * 2.6377
        )
        * 1.5
        / 3600,
        "precision": "At1400 independent confirmation parents, a bounded paired difference in [-1,1] has worst-case normal95 half-width about5.24pp; not adequate for a reliably precise one-checkpoint development contrast",
        "limitations": "Assignment expectations are not guarantees. Any errors raise needed calibration support. Strict Push routes no actions under this menu, so neither Push stratum can qualify at any planned sample count. Scientific gate does not justify this roughly10h simulation expenditure.",
    }
    save(root / "prospective_plan.json", plan)
    save(
        root / "review_completed.json",
        {
            "status": "COMPLETE",
            "figures": 3,
            "identity_views": sum(p["views"] for p in identities.values()),
            "DSRE_B7_equal": sum(p["DSRE_B7_equal"] for p in identities.values()),
            "prospective_plans": 1,
            "new_physics": 0,
        },
    )
    print(json.dumps(load(root / "review_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    review(args.root)
