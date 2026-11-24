"""Post-freeze task counterexamples and descriptive acquisition frontiers."""

import csv
import json
from collections import defaultdict

from dsre_evidence_prospective import ROOT, TASKS, read

from dual_rec.evidence_aware.views import save, sha


def main():
    tasks = {}
    curve = []
    for task in TASKS:
        out = ROOT / "prospective" / task
        audit = out / "independent_prospective_audit_full.json"
        if not audit.exists() or not read(audit)["passed"]:
            tasks[task] = {
                "status": "No complete independently audited test; no task witnesses manufactured."
            }
            continue
        evaluation = out / "evaluations/logged.json"
        if not evaluation.exists():
            guardpath = out / "SOURCE_GUARD_FAILURE.json"
            tasks[task] = {
                "status": "Recorded source traces audited; no completed independent test or fitted recovery result. No task witnesses manufactured.",
                "source_guard": read(guardpath) if guardpath.exists() else None,
                "recorded_data_audit_sha256": sha(audit),
            }
            continue
        scores = read(evaluation)
        tests = {p.stem: read(p) for p in (out / "test").glob("*.json")}
        pairs = [read(p) for p in (out / "evaluator").glob("*.json")]
        neither = [
            p["parent_id"] for p in pairs if p["yc"] is False and p["yr"] is False
        ]
        harmful = [
            p["parent_id"] for p in pairs if p["yc"] is True and p["yr"] is False
        ]
        rescue = [p["parent_id"] for p in pairs if p["yc"] is False and p["yr"] is True]
        groups = defaultdict(dict)
        for p in pairs:
            if p.get("precheckpoint_absorption"):
                continue
            pattern = tuple(tests[p["parent_id"]]["x"])
            groups[pattern].setdefault(f"{int(p['yc'])}{int(p['yr'])}", p["parent_id"])
        alias = [
            {
                "x": list(x),
                "continue_only_parent": v["10"],
                "recover_only_parent": v["01"],
            }
            for x, v in groups.items()
            if "10" in v and "01" in v
        ]
        model = read(out / "models/logged.json")
        obligations = {}
        for c, leaf in model["leaves"].items():
            b = leaf["bounds"]
            obligations[c] = {
                "primary_useful": b["harm_upper"] <= 0.1 + 1e-12
                and b["gain_lower"] >= 0.05 - 1e-12,
                "harm_only": b["harm_upper"] <= 0.1 + 1e-12,
                "completion_only": b["failure_upper"] <= 0.1 + 1e-12,
                "diagnosis": leaf["diagnosis"],
                "bounds": b,
                "scope": "entire frozen leaf, measured valid-checkpoint observation protocol; unknown/absorbing contexts never receive R",
            }
        tasks[task] = {
            "status": "Independently audited held-out outcomes; evaluator-only diagnostics after every model freeze",
            "test_parents": scores["n_complete_oracle_pairs"],
            "valid_checkpoint_pairs": scores["n_recovery_checkpoint_pairs"],
            "neither_action_success": len(neither),
            "neither_action_witnesses": neither[:3],
            "recover_harms": len(harmful),
            "harm_witnesses": harmful[:3],
            "rescue_opportunities": len(rescue),
            "rescue_witnesses": rescue[:3],
            "same_observation_opposite_unique_action_witnesses": alias[:3],
            "unsupported_obligations_by_leaf": obligations,
            "evidence_sha256": sha(evaluation),
            "limitation": "Point examples establish only the named deterministic simulator executions. They are not individual real-world safety certificates or proof of population impossibility.",
        }
        schedule = read(out / "acquisition_schedule.json")
        for strategy, budgets in schedule["schedules"].items():
            for budget, requests in budgets.items():
                name = f"{strategy}_{budget}"
                metrics = read(out / "evaluations" / f"{name}.json")["policies"]["DSRE"]
                m = read(out / "models" / f"{name}.json")
                bounds = [v["bounds"] for v in m["leaves"].values()]
                curve.append(
                    {
                        "task": task,
                        "strategy": strategy,
                        "requested_additional_units": int(budget),
                        "actual_additional_units": sum(r["cost"] for r in requests),
                        "total_calibration_units": m["logical_calibration_executions"],
                        "test_n": metrics["n"],
                        "qualified_recoveries": metrics["recover"],
                        "qualified_coverage": metrics["coverage"],
                        "whole_policy_gain": metrics["whole_policy_gain"],
                        "mean_leaf_harm_width": sum(
                            b["harm_upper"] - b["harm_lower"] for b in bounds
                        )
                        / len(bounds),
                        "mean_leaf_gain_width": sum(
                            b["gain_upper"] - b["gain_lower"] for b in bounds
                        )
                        / len(bounds),
                    }
                )
    save(
        ROOT / "task_diagnostics_and_witnesses.json",
        {
            "tasks": tasks,
            "confidence": "Primary bounds retain the registered per-task family; evaluator examples and between-budget curves are descriptive, never new calibration inputs.",
        },
    )
    save(
        ROOT / "prospective_acquisition_frontiers.json",
        {
            "curves": curve,
            "primary_requested_budget": 512,
            "claim": "No superiority claimed from unmatched actual costs; a508-unit log result is not silently called512.",
        },
    )
    if curve:
        figures = ROOT / "figures"
        figures.mkdir(exist_ok=True)
        with (figures / "prospective_acquisition.csv").open("x", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(curve[0]))
            writer.writeheader()
            writer.writerows(curve)
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        completed = [t for t in TASKS if any(r["task"] == t for r in curve)]
        fig, axes = plt.subplots(
            1, len(completed), figsize=(6 * len(completed), 4), squeeze=False
        )
        for ax, task in zip(axes[0], completed, strict=True):
            for i, strategy in enumerate(
                (
                    "witness",
                    "all_logs",
                    "all_pairs",
                    "uniform_mix",
                    "decision_uncertainty",
                )
            ):
                rows = [
                    r for r in curve if r["task"] == task and r["strategy"] == strategy
                ]
                ax.plot(
                    [r["actual_additional_units"] for r in rows],
                    [r["qualified_coverage"] for r in rows],
                    label=strategy,
                    marker=["o", "s", "^", "v", "x"][i],
                    linestyle=["-", "--", ":", "-.", "--"][i],
                )
            ax.set(
                title=task,
                xlabel="Actual additional logical continuation units",
                ylabel="Qualified recovery coverage on full test",
                ylim=(-0.02, 1.02),
            )
            ax.legend(fontsize=8)
        fig.suptitle("Frozen prospective models; descriptive budget curves")
        fig.tight_layout()
        fig.savefig(figures / "prospective_acquisition.png", dpi=180)
        fig.savefig(figures / "prospective_acquisition.pdf")
        plt.close(fig)
    print(
        json.dumps(
            {
                t: {
                    k: v
                    for k, v in value.items()
                    if k
                    in (
                        "status",
                        "test_parents",
                        "neither_action_success",
                        "recover_harms",
                        "rescue_opportunities",
                    )
                }
                for t, value in tasks.items()
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
