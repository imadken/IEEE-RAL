"""Seal a source-qualification failure without inventing calibration/test data."""

import argparse
import json
import re
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def unobserved_strata(methods):
    return {
        m + "|" + a: {
            "assigned_parents": 0,
            "observed_error_parents": 0,
            "risk_point_estimate": None,
            "upper": 1.0,
            "upper_scope": "Uninformative n=0 convention, not an estimated 100% error rate",
            "delta": 0.05 / 68,
            "enabled": False,
            "status": "NOT_QUALIFIED_INCOMPLETE_COHORT",
        }
        for m in methods
        for a in ("continue", "recover")
    }


def summarize(root):
    plan = read(root / "study_plan.json")
    halt = read(root / "study_halt.json")
    assert halt["stage"] == "qualification" and halt["returncode"] == -11
    for stage in ("calibration", "test"):
        assert not list((root / stage).rglob("screen.json.gz"))
        assert not list((root / stage).rglob("continue.json.gz"))
        assert not list((root / stage).rglob("recover.json.gz"))
        assert not list((root / "attempts").glob(stage + "-*.json"))
    assert not list((root / "attempts").glob("test_*.json"))
    assert not (root / "calibration_decision.json").exists()
    assert not (root / "calibration_seal.json").exists()
    assert not (root / "test_recommendation_seal.json").exists()
    diagnostic = read(root / "metered/inspected_prefix_diagnostic.json")
    assert diagnostic["status"] in (-11, 139)
    trace = (root / "metered/inspected_prefix_diagnostic.log").read_text()
    assert (
        "Segmentation fault" in trace and "common.py" in trace and "build_cube" in trace
    )
    assert "line 87 in build_cube" in trace
    assert read(root / "metered/import_diagnostic.json")["status"] == 0
    assert read(root / "metered/qualification_audit_attempt.json")["status"] != 0
    qualified = root / "qualification" / str(plan["qualification_seeds"][0])
    assert not list(qualified.rglob("screen.json.gz"))
    assert not list(qualified.rglob("continue.json.gz"))
    assert not list(qualified.rglob("recover.json.gz"))
    report = {
        "scientific_gate": "PHYSICS_OR_DATA_BLOCKED",
        "experimental_campaign_complete": False,
        "defined_boundary_reached": "Pinned-runtime qualification fails before any new parent outcomes",
        "qualification": {
            "attempted_old_parents": 1,
            "completed_parents": 0,
            "registered_old_parents": 1,
            "saved_prefixes": 0,
            "saved_continuations": 0,
            "status": "RUNTIME_CONSTRUCTION_BLOCKED",
        },
        "calibration": {
            "planned_parents": 256,
            "planned_checkpoints": 1280,
            "planned_continuations": 2560,
            "started_parents": 0,
            "completed_parents": 0,
            "complete_cohort": False,
        },
        "test": {
            "planned_parents": 128,
            "planned_checkpoints": 640,
            "planned_continuations": 1280,
            "started_parents": 0,
            "completed_parents": 0,
            "complete_cohort": False,
            "adequate": None,
            "inadequate": None,
            "stop": None,
            "coverage": None,
            "conditional_success": None,
            "paired_outcome_classes": None,
            "initially_unsuccessful": None,
            "required_recoveries": None,
            "required_recovery_recall": None,
            "harms_from_recovery": None,
            "maintenance": None,
            "paired_effects": None,
        },
        "strata": unobserved_strata(plan["methods"]),
        "new_empirical_method_comparison": "NOT_ESTIMABLE; mathematical identities retained, not vacuous empirical ties",
        "native_failure": {
            "first_attempt_returncode": -11,
            "independent_prefix_probe_status": diagnostic["status"],
            "fault_site": "SAPIEN RenderMaterial creation in ManiSkill actors/common.py:87, called by build_cube during PickCube scene initialization",
            "root_cause": "Not determined; fault site is observed. No claim that hardware, drivers, historical results or physics definitions changed.",
            "serialization_repair_applicable": False,
            "frames": re.findall(r'File "([^"]+)", line (\d+) in ([^\n]+)', trace),
        },
        "input_time_and_new_physical_audit": "No new saved states or labels to validate; qualification not passed",
        "prior_evidence": {
            "source": "results/dsre-operational/20261115T195007Z-science-v12",
            "confirmation_parents": 128,
            "checkpoints": 640,
            "action_mass": 592,
            "seven_fact_common_action_mass": 256,
            "DSRE_risk_adequate_inadequate_stop": [401, 2, 237],
            "DSRE_required_recoveries_selected_total": [48, 238],
            "ordinary_rules": "Exact identity retained",
            "risk_status": "These remain old unqualified proposals; never pooled into the present calibration/test",
        },
        "remaining_preregistered_work": "All256 calibration parents and all128 test parents remain never-started; no replacement or enrichment",
        "source_changes": "None to DSRE, skills, environment packages, frozen models or thresholds",
        "manuscript_edit": False,
        "new_training": 0,
        "push": False,
        "submission": False,
    }
    (root / "blocked_scientific_results.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    return report


def figures(root, report):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(7, 2.8))
    plt.rcParams.update({"pdf.fonttype": 42})
    ax = axes[0]
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axhline(10, color="#a34a45", linestyle="--", linewidth=1)
    ax.set_xlabel("Held-out accepted coverage (%)")
    ax.set_ylabel("Parent-action error upper bound (%)")
    ax.set_title("No empirical risk–coverage point", fontsize=10)
    ax.text(
        0.5,
        0.6,
        "Calibration: 0 / 256 parents\nTest: 0 / 128 parents\nRates and effects undefined",
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=10,
    )
    ax.text(0.03, 0.13, "10% qualification target", transform=ax.transAxes, fontsize=8)
    ax = axes[1]
    ns = list(range(1, 257))
    upper = [100 * (1 - (0.05 / 68) ** (1 / n)) for n in ns]
    ax.plot(ns, upper, color="#3976a8")
    ax.axhline(10, color="#a34a45", linestyle="--", linewidth=1)
    ax.axvline(69, color="#777777", linestyle=":", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 256)
    ax.set_title("Design-only support; zero errors", fontsize=10)
    ax.set_xlabel("Independent assigned parents")
    ax.set_ylabel("Exact one-sided upper bound (%)")
    ax.text(
        0.55,
        0.6,
        "δ = 0.05 / 68\n69 error-free\nassigned parents\nneeded",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.suptitle(
        "New-source execution blocked at pinned-runtime preflight", fontsize=11
    )
    fig.tight_layout()
    output = Path("docs/figures")
    output.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(
            output / ("dsre_source_risk_coverage." + ext), dpi=300, bbox_inches="tight"
        )
    plt.close(fig)
    rows = [
        r"\begin{tabular}{lrrl}\hline",
        r"Cohort & Planned parents & Completed & Inference\\\hline",
        r"Old-seed preflight & 1 & 0 & Native initialization failure\\",
        r"Independent calibration & 256 & 0 & No action qualified\\",
        r"Untouched test & 128 & 0 & Coverage/recall not estimable\\\hline",
        r"\end{tabular}",
    ]
    (output / "dsre_source_risk_table.tex").write_text("\n".join(rows) + "\n")
    data = {
        "plot": "No empirical points: n=0. Right-hand curve is analytic design-only CP with zero assumed errors, not measured performance.",
        "registered_delta": 0.05 / 68,
        "target": 0.1,
        "support_curve": {str(n): u / 100 for n, u in zip(ns, upper, strict=True)},
        "source": "blocked_scientific_results.json; study_plan.json.risk",
        "cohort_table": report["calibration"] | {"test": report["test"]},
    }
    (root / "figure_source_data.json").write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    result = summarize(a.root)
    figures(a.root, result)
    print(
        json.dumps(
            {
                "gate": result["scientific_gate"],
                "new_calibration_parents": 0,
                "new_test_parents": 0,
                "new_action_strata_qualified": 0,
                "rates": "undefined",
            }
        ),
        flush=True,
    )
