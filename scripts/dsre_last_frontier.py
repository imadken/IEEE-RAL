"""Read-only evidence availability analysis; historical roles remain historical."""

from collections import defaultdict
from pathlib import Path

from dsre_last_common import ROOT, read, save, sha
from dsre_last_existing import frontier


def main():
    historical = Path("results/dsre-evidence-aware/20261117-prospective/prospective")
    output = {}
    curves = {}
    inputs = {}
    for task in ("PickCube-v1", "PointMaze_UMaze-v3"):
        base = historical / task
        strata = defaultdict(list)
        unsupported = []
        for path in sorted((base / "test").glob("*.json")):
            selected = read(path)
            pp = base / "evaluator" / path.name
            pair = read(pp)
            inputs[str(path)] = sha(path)
            inputs[str(pp)] = sha(pp)
            if selected["status"] == "ALREADY_SOLVED_PREFIX":
                # Observed absorbing success precedes the recovery checkpoint;
                # its all-UNKNOWN packet is not a fabricated Boolean signature.
                continue
            if selected["x"] is None or any(v is None for v in selected["x"]):
                unsupported.append(
                    {
                        "source": str(path),
                        "x": selected["x"],
                        "status": selected["status"],
                    }
                )
                continue
            row = {
                "seed": selected["spec"]["seed"],
                "features": selected["x"],
                "c": pair["yc"],
                "r": pair["yr"],
                "source": str(path),
            }
            condition = str(selected["spec"]["offset"])
            strata[task + "|" + condition].append(row)
            strata[task + "|ALL_CONDITIONS"].append(row)
        evalpath = base / "evaluations/logged.json"
        e = read(evalpath)
        inputs[str(evalpath)] = sha(evalpath)
        output[task] = {
            "role": "Original prospective independent T, previously inspected; DEVELOPMENT_FOR_FINAL_ANALYSIS now",
            "empirical_frontiers": {k: frontier(v) for k, v in strata.items()},
            "registered_test": e["n_registered_test"],
            "complete_pairs": e["n_complete_oracle_pairs"],
            "checkpoint_pairs": e["n_recovery_checkpoint_pairs"],
            "absorbing_prefix": e["n_observed_absorbing_prefix_parents"],
            "policies": e["policies"],
            "equivalence": e["equivalence_vs_DSRE"],
            "unsupported_checkpoint_observations": unsupported,
        }
        curves[task] = {}
        for strategy in (
            "all_logs",
            "all_pairs",
            "witness",
            "uniform_mix",
            "decision_uncertainty",
        ):
            curves[task][strategy] = []
            for budget in (64, 128, 256, 512):
                ep = base / "evaluations" / f"{strategy}_{budget}.json"
                mp = base / "models" / f"{strategy}_{budget}.json"
                ev = read(ep)
                mo = read(mp)
                inputs[str(ep)] = sha(ep)
                inputs[str(mp)] = sha(mp)
                curves[task][strategy].append(
                    {
                        "registered_additional_action_budget": budget,
                        "actual_observed_calibration_actions": ev[
                            "logical_calibration_cost"
                        ],
                        "common_discovery_actions": 128,
                        "logs": mo["counts"]["calibration_logs"],
                        "pairs": mo["counts"]["calibration_pairs"],
                        "DSRE": ev["policies"]["DSRE"],
                    }
                )
                assert (
                    mo["counts"]["calibration_logs"] + mo["counts"]["calibration_pairs"]
                    == ev["logical_calibration_cost"]
                )
        if task == "PickCube-v1":
            final = [curves[task][s][-1]["DSRE"] for s in curves[task]]
            assert (
                len(
                    {
                        (v["success"], v["recover"], v["required_rescues"], v["harm"])
                        for v in final
                    }
                )
                == 1
            )
    newrows = []
    for p in sorted((ROOT / "records/test").glob("*.json")):
        r = read(p)
        newrows.append(
            {
                "seed": r["spec"]["seed"],
                "features": r["x"],
                "c": r["yc"],
                "r": r["yr"],
                "source": str(p),
                "condition": r["spec"]["condition"],
            }
        )
    if newrows:
        strata = defaultdict(list)
        for r in newrows:
            strata[r["condition"]].append(r)
            strata["ALL_CONDITIONS"].append(r)
        output["PushCube-v1"] = {
            "role": "Final registered prospective T, only opened after frozen C gate and selected execution",
            "empirical_frontiers": {k: frontier(v) for k, v in strata.items()},
        }
    save(
        ROOT / "evidence_frontier.json",
        {
            "tasks": output,
            "matched_historical_cost_curves": curves,
            "interpretation": "Separate action capacity, observable common action, empirical source sufficiency and calibrated policy coverage. No additive decomposition. Small-cell point estimates not confidence claims. Navigation conditional checkpoint denominator255 differs from raw256.",
            "input_sha256": inputs,
        },
    )


if __name__ == "__main__":
    main()
