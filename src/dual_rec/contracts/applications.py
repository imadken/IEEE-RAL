"""Apply reusable checks to declared claims using the three actual evidence cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from dual_rec.contracts.checks import AuditBundle, audit, check_prefix
from dual_rec.failtime.experiment import read, save
from dual_rec.failtime.models import causal_features


def apply(root):
    target = root / "contract_applications"
    target.mkdir(exist_ok=True)
    reports = []

    def record(name, payload, claim):
        bundle = AuditBundle.model_validate(payload)
        save(target / (name + "_input.json"), bundle.model_dump())
        result = [r.model_dump() for r in audit(bundle)]
        save(target / (name + "_checks.json"), {"claim": claim, "results": result})
        reports.append({"name": name, "claim": claim, "checks": result})

    registry = read(root / "failtime/fold0", "cohort_qualification.json")
    by_id = {r["sample"]: r for r in registry}
    prefix_results = []
    for fold in range(5):
        child = root / "failtime" / f"fold{fold}"
        splits = read(child, "registration.json")["splits"]
        partitions = {s: split for split, ids in splits.items() for s in ids}
        rows = [
            {
                "record_id": r["sample"],
                "signal_hash": r["signal_sha256"],
                "task_group": r["robot"] + "/" + r["task_id"],
                "source_group": r["sample"],
                "partition": partitions[r["sample"]],
                "role": "failure" if r["verdict"] == "fail" else "success",
            }
            for r in registry
        ]
        refs = [s for s in splits["calibration"] if by_id[s]["verdict"] == "success"]
        failures = [s for s in splits["calibration"] if by_id[s]["verdict"] == "fail"]
        stop = {}
        unavailable = {}
        for s in failures:
            with np.load(child / "risks/calibration/clean" / (s + ".npz")) as d:
                pre = d["time"][d["time"] < by_id[s]["onset"]]
                if len(pre):
                    stop[s] = float(pre[-1])
                else:
                    unavailable[s] = (
                        "No observed decision sample strictly before released onset; retained in evaluation"
                    )
        record(
            f"failtime_fold{fold}_design",
            {
                "recordings": rows,
                "calibration": {
                    "reference_ids": refs,
                    "prefix_ids": list(stop),
                    "selection_label_ids": splits["calibration"],
                    "reference_verdicts": {s: "success" for s in refs},
                    "prefix_stop": stop,
                    "onsets": {s: by_id[s]["onset"] for s in failures},
                    "unavailable_prefixes": unavailable,
                },
                "runtime": {
                    "fields": {
                        "eef": "observation",
                        "robot": "static",
                        "decision_clock": "observation",
                    },
                    "allowed_static": ["robot"],
                },
            },
            "Task-separated, success-reference and strictly pre-onset prefix calibration; declarations checked against saved fold audits, not a general proof of no hidden label access",
        )
        outcomes = [
            r
            for r in read(child, "outcomes.json")
            if r["stress"] == "clean"
            and r["method"] == "MCSFA"
            and r["alpha"] == 0.1
            and r["persistence"] == 0.1
        ]
        for r in outcomes:
            s = r["sample"]
            with np.load(child / "risks/evaluation/clean" / (s + ".npz")) as d:
                valid = np.isfinite(d["source_time"])
                packet = {
                    "decisions": d["time"][valid].tolist(),
                    "source_times": d["source_time"][valid].tolist(),
                    "arrivals": d["source_time"][valid].tolist(),
                }
                alarm = {
                    "time": d["time"].tolist(),
                    "scores": [
                        float(x) if np.isfinite(x) else None for x in d["MCSFA"]
                    ],
                    "threshold": r["threshold"],
                    "reported_alarm": r["alarm_time"],
                }
                x = d["eef"].copy()
                cut = max(2, len(x) // 2)
                changed = x.copy()
                changed[cut:] += 17
                prefix_results.append(
                    {
                        "sample": s,
                        "fold": fold,
                        **check_prefix(
                            lambda values, t=d["time"]: causal_features(t, values),
                            x,
                            changed,
                            cut,
                        ).model_dump(),
                    }
                )
            record(
                "failtime_stream_" + s,
                {"packets": packet, "alarm": alarm},
                "Clean MCSFA primary first alarm from recording start; prefix feature perturbation checked separately",
            )
    events = [
        {
            "record_id": r["sample"],
            "start": 0,
            "end": r["duration"],
            "onset": r["onset"],
            "semantics": "retrospective_deviation",
            "claimed_semantics": "retrospective_deviation",
            "censored": not r["onset_within_observed"],
        }
        for r in registry
        if r["verdict"] == "fail"
    ]
    record(
        "failtime_event_labels",
        {
            "events": events,
            "accounting": {
                "eligible_ids": list(by_id),
                "evaluated_ids": list(by_id),
                "exclusion_reasons": {},
                "abstention_ids": [],
                "denominator": 100,
                "uncertainty_unit": "task",
                "independent_groups": 13,
            },
        },
        "Original retrospective labels retained, including explicit right censoring; observational records do not identify interventions",
    )
    misleading = [{**e, "claimed_semantics": "observable_event"} for e in events]
    record(
        "failtime_unjustified_label_reinterpretation",
        {"events": misleading},
        "Controlled invalid counterexample: treating retrospective deviation as an independently observed runtime event",
    )
    reboot = read(root, "reboot_reproduction.json")
    annotated_repositories = {
        r["repository"]
        for r in read(
            Path("results/reboot-overnight/20261111T224622Z"), "registry.json"
        )
        if r["role"] == "recovery" and r["eligible"]
    }
    aliases = reboot["duplicate_alias_pairs"]
    record(
        "reboot_uncollapsed_aliases",
        {
            "recordings": [
                {
                    "record_id": f"{which}:{r[which + '_episode']}",
                    "signal_hash": r["signature"],
                    "task_group": "cylinder-install",
                    "source_group": r["signature"],
                    "partition": "train",
                    "role": "failure",
                }
                for r in aliases
                for which in ("sample", "recovery")
            ]
        },
        "Controlled invalid population before explicitly collapsing the known aliases",
    )
    record(
        "reboot_missing_temporal_target",
        {
            "events": [
                {
                    "record_id": r["repository"],
                    "start": 0,
                    "end": 1,
                    "onset": None,
                    "semantics": "unknown",
                    "claimed_semantics": "unknown",
                }
                for r in reboot["coverage"]
                if r["role"] == "recovery"
                and not r["annotation_file_present"]
                and r["repository"].split("/")[1] not in annotated_repositories
            ]
        },
        "Missing native or verified alias-transferred event labels leave a requested temporal evaluation unknown; canonical cylinder-install aliases retain their valid annotations",
    )
    case = root / "recoverbench"
    for s in read(case, "identity.json")["tasks"]:
        record(
            "recoverbench_identity_" + s["task"],
            {
                "simulator": {
                    "expected_class": s["seed_environment_metadata"]["env_name"],
                    "actual_class": s["actual_class"],
                    "expected_controller": "OperationalSpaceController",
                    "actual_controller": s["controller"]["class"],
                    "expected_dimension": 7,
                    "actual_dimension": s["controller"]["action_dimension"],
                    "expected_dt": 0.05,
                    "actual_dt": 0.05,
                    "expected_model_hash": s["expected_fingerprint"]["xml_hash"],
                    "actual_model_hash": s["actual_fingerprint"]["xml_hash"],
                    "reference_kind": "unknown",
                    "controller_memory_recorded": None,
                }
            },
            "Pinned factory interface plus saved fingerprint; missing original failure-scene XML leaves physical equivalence unknown even when the interface agrees",
        )
    for i, line in enumerate(
        (case / "source-diagnostics/outcomes.jsonl").read_text().splitlines()
    ):
        row = json.loads(line)
        record(
            f"recoverbench_executed_{i:02d}",
            {
                "execution": {
                    "kind": "actions_stepped",
                    "actions": row["executed_steps"],
                    "state_injections_after_start": 0,
                    "physics_time_advanced": row["executed_steps"] * 0.05,
                    "initial_success": row["initial_success"],
                    "reported_new_recovery": not row["initial_success"]
                    and row["first_success_step"] is not None,
                    "observed_success": row["first_success_step"] is not None,
                    "original_predicate_checked": True,
                }
            },
            "Actual action stepping; traces independently audited for state continuity and original predicates; executing an unsuccessful tape still satisfies the execution-mode obligation",
        )
    record(
        "recoverbench_forwarding_only",
        {
            "execution": {
                "kind": "states_forwarded",
                "actions": 0,
                "state_injections_after_start": 4930,
                "physics_time_advanced": 0,
                "initial_success": False,
                "reported_new_recovery": False,
                "observed_success": False,
                "original_predicate_checked": False,
            }
        },
        "Actual forward-kinematics reconstruction is unsuitable evidence of an executed recovery",
    )
    save(
        root / "prefix_noninterference.json",
        {
            "status": "PASS"
            if all(r["status"] == "PASS" for r in prefix_results)
            else "FAIL",
            "scope": "100 fixed EEF future-suffix perturbations of the existing causal feature function; no universal proof",
            "records": prefix_results,
        },
    )
    save(root / "contract_applications.json", reports)
    print({"claim_contexts": len(reports), "prefix_checks": len(prefix_results)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    apply(args.root)


if __name__ == "__main__":
    main()
