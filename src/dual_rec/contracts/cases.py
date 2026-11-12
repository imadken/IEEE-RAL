"""Fixed case-study reproduction from immutable signals and action ledgers."""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

import numpy as np

from dual_rec.contracts.checks import first_alarm
from dual_rec.failtime.experiment import digest, read, save

REBOOT = Path("results/reboot-overnight/20261111T224622Z")
PHASE = Path("results/reboot-phase/20261111T204459Z")
RECOVER = Path("results/recoverbench-qualification-rescue/20261111T195432Z")


def peak_readout(time, scores, onset):
    finite = np.flatnonzero(np.isfinite(scores))
    if not len(finite):
        return {"peak_time": None, "absolute_error": None, "within_one_second": False}
    index = finite[np.argmax(scores[finite])]
    estimate = float(time[index])
    error = abs(estimate - onset)
    return {
        "peak_time": estimate,
        "absolute_error": error,
        "within_one_second": error <= 1 + 1e-7,
    }


def reboot(root):
    # Re-execute the historical independent row-wise raw decoder, rather than
    # trusting published duplicate counts or importing the original main audit.
    reader = runpy.run_path("scripts/reboot_overnight_independent.py")["raw_recordings"]
    arrays = {
        name: reader(PHASE, name)
        for name in (
            "sample_recovery-demonstration",
            "16mm-cylinder_recovery_install",
            "16mm-cylinder_install",
        )
    }
    aliases = []
    for index, a in arrays["sample_recovery-demonstration"].items():
        matches = [
            i
            for i, b in arrays["16mm-cylinder_recovery_install"].items()
            if a["signature"] == b["signature"]
        ]
        assert len(matches) == 1
        aliases.append(
            {
                "sample_episode": index,
                "recovery_episode": matches[0],
                "signature": a["signature"],
            }
        )
    raw = read(PHASE, "data/sample_recovery-demonstration/meta/phase.json")["episodes"]
    raw_results = []
    for label in raw:
        i = int(label["episode_index"])
        f = label["failure"]
        a = arrays["sample_recovery-demonstration"][i]
        left = f.get("t_f", f.get("induced_at_frame"))
        right = f.get("t_r", f.get("recovery_started_at_frame"))
        schema = (
            type(f["originating_phase"]) is int and 1 <= f["originating_phase"] <= 5
        )
        in_bounds = (
            type(left) is int and type(right) is int and 0 <= left < right < len(a["t"])
        )
        raw_results.append(
            {
                "episode": i,
                "frames": len(a["t"]),
                "schema_valid": schema,
                "event_bounds_valid": in_bounds,
                "eligible": schema and in_bounds,
                "raw_annotation": label,
            }
        )
    registry = read(REBOOT, "registry.json")
    eligible = [r for r in registry if r["eligible"]]
    assert sorted(r["episode"] for r in raw_results if not r["eligible"]) == [
        16,
        26,
        35,
        37,
        48,
    ]
    thresholds = read(REBOOT, "thresholds.json")
    old = {
        (r["group"], r["variant"], r["method"]): r
        for r in read(REBOOT, "outcomes.json")
        if r["stress"] == "clean" and r["boundary_delta"] == 0
    }
    outcomes = []
    for row in eligible:
        for variant in ("Q", "QC"):
            path = (
                REBOOT
                / "predictions"
                / f"fold{row['fold']}"
                / variant
                / "clean/evaluation"
                / (row["group"].split(":")[1] + ".npz")
            )
            with np.load(path) as data:
                t = data["time"]
                exposure = min(float(data["horizon"]), row["frames"] / 30 - 1 / 30)
                for method in ("B0", "B1", "B2", "B3", "P0", "P1", "P2"):
                    theta = thresholds[f"{row['fold']}:{variant}:{method}"]["threshold"]
                    scores = data[method]
                    alarm = first_alarm(t, scores, theta, 0.1, 2e-6)
                    failure = row["role"] == "recovery"
                    timely = premature = reset = False
                    peak = {}
                    if failure:
                        low = row["onset"]
                        high = min(row["recovery"], exposure)
                        timely = alarm is not None and low <= alarm < high
                        premature = alarm is not None and alarm < low
                        keep = t >= low
                        when = first_alarm(t[keep], scores[keep], theta, 0.1, 2e-6)
                        reset = when is not None and when < high
                        peak = peak_readout(t, scores, low)
                    result = {
                        "group": row["group"],
                        "variant": variant,
                        "method": method,
                        "role": row["role"],
                        "alarm_time": alarm,
                        "timely": timely,
                        "premature": premature,
                        "reference_alarm": not failure and alarm is not None,
                        "INVALID_onset_reset_timely": reset,
                        **peak,
                    }
                    prior = old[(row["group"], variant, method)]
                    for field in (
                        "alarm_time",
                        "timely",
                        "premature",
                        "reference_alarm",
                    ):
                        assert result[field] == prior[field]
                    assert reset == prior.get("optimistic_post_onset_reset", False)
                    outcomes.append(result)
    summary = []
    for variant in ("Q", "QC"):
        for method in ("B0", "B1", "B2", "B3", "P0", "P1", "P2"):
            selected = [
                r for r in outcomes if r["variant"] == variant and r["method"] == method
            ]
            summary.append(
                {
                    "variant": variant,
                    "method": method,
                    "failures": 55,
                    "references": 62,
                    **{
                        k: sum(r[k] for r in selected)
                        for k in (
                            "timely",
                            "premature",
                            "reference_alarm",
                            "INVALID_onset_reset_timely",
                        )
                    },
                    "retrospective_peak_within_1s": sum(
                        r.get("within_one_second", False) for r in selected
                    ),
                    "peak_mae": float(
                        np.mean(
                            [
                                r["absolute_error"]
                                for r in selected
                                if r.get("absolute_error") is not None
                            ]
                        )
                    ),
                }
            )
    qualification = read(PHASE, "qualification.json")
    coverage = []
    for repo in read(PHASE, "repository_registration.json")["repositories"]:
        name = repo["id"].split("/")[1]
        phase = PHASE / "data" / name / "meta/phase.json"
        coverage.append(
            {
                "repository": repo["id"],
                "role": repo["role"],
                "annotation_file_present": phase.exists(),
                "annotation_file_sha256": digest(phase) if phase.exists() else None,
            }
        )
    save(
        root / "reboot_reproduction.json",
        {
            "status": "PASS",
            "outcome_rows": len(outcomes),
            "summary": summary,
            "duplicate_alias_pairs": aliases,
            "raw_annotation_results": raw_results,
            "coverage": coverage,
            "historical_gate": qualification["status"],
            "canonical_recoveries": 55,
            "canonical_references": 62,
            "scope": "Re-executed raw decoder and continuous scorer; reset is INVALID hidden-event diagnostic, not attributed to original REBOOT evaluation",
        },
    )
    save(root / "reboot_outcomes.json", outcomes)
    print(
        {
            "status": "PASS",
            "reboot_outcomes": len(outcomes),
            "duplicate_pairs": len(aliases),
        }
    )


def prepare_recoverbench(root):
    case = root / "recoverbench"
    case.mkdir(exist_ok=True)
    for name in ("data", "upstream"):
        target = case / name
        if not target.exists():
            target.symlink_to((RECOVER / name).resolve(), target_is_directory=True)
    config = read(RECOVER, "registration.json")
    config.update(run=str(case), reproduction_of=str(RECOVER))
    save(case / "registration.json", config)
    save(
        root / "recoverbench_inputs.json",
        {
            "source_registration_sha256": digest(RECOVER / "registration.json"),
            "new_registration_sha256": digest(case / "registration.json"),
            "environment": "results/recoverbench-transfer/20261111T172759Z/env/bin/python",
            "scope": "Exact fixed source membership and two workflows; no benchmark policy evaluation or new adapter",
        },
    )


def recoverbench(root):
    case = root / "recoverbench"
    new = [
        json.loads(s)
        for s in (case / "source-diagnostics/outcomes.jsonl").read_text().splitlines()
    ]
    old = [
        json.loads(s)
        for s in (RECOVER / "source-diagnostics/outcomes.jsonl")
        .read_text()
        .splitlines()
    ]
    before = {(r["case"]["archive_member"], r["variant"]): r for r in old}
    matched = []
    for row in new:
        prior = before[(row["case"]["archive_member"], row["variant"])]
        fields = (
            "initial_success",
            "first_success_step",
            "terminal_success",
            "executed_steps",
        )
        matched.append(
            {
                "task": row["case"]["task"],
                "source": row["case"]["archive_member"],
                "variant": row["variant"],
                "matches_recorded_outcomes": all(row[k] == prior[k] for k in fields),
            }
        )
    summary = []
    for task in ("stack", "pick_place"):
        for variant in sorted({r["variant"] for r in new}):
            rs = [
                r for r in new if r["case"]["task"] == task and r["variant"] == variant
            ]
            summary.append(
                {
                    "task": task,
                    "variant": variant,
                    "sources": len(rs),
                    "initial_success": sum(r["initial_success"] for r in rs),
                    "first_hit_success": sum(
                        r["first_success_step"] is not None for r in rs
                    ),
                    "new_success": sum(
                        not r["initial_success"] and r["first_success_step"] is not None
                        for r in rs
                    ),
                    "terminal_success": sum(r["terminal_success"] for r in rs),
                }
            )
    identities = read(case, "identity.json")["tasks"]
    prior_id = read(RECOVER, "identity.json")["tasks"]
    identity = []
    for row in identities:
        old_row = next(r for r in prior_id if r["task"] == row["task"])
        identity.append(
            {
                "task": row["task"],
                "matches_recorded_actual_class": row["actual_class"]
                == old_row["actual_class"],
                "matches_recorded_fingerprint": row["actual_fingerprint"]
                == old_row["actual_fingerprint"],
                "actual_class": row["actual_class"],
                "expected_class": row["seed_environment_metadata"]["env_name"],
                "actual_fingerprint": row["actual_fingerprint"],
                "expected_fingerprint": row["expected_fingerprint"],
            }
        )
    scope = "New actual physics executions in the existing pinned stack; local release-interface/checker-vs-raw diagnostics, not authors original policy evaluation"
    save(
        root / "recoverbench_reproduction.json",
        {
            "status": "PASS"
            if all(r["matches_recorded_outcomes"] for r in matched)
            and all(
                r["matches_recorded_actual_class"] and r["matches_recorded_fingerprint"]
                for r in identity
            )
            else "REPRODUCTION_DISCREPANCY",
            "summary": summary,
            "rows": len(new),
            "controls": sum(r["executed_steps"] for r in new),
            "comparisons": matched,
            "identity": identity,
            "scope": scope,
        },
    )
    print({"recoverbench_rows": len(new), "summary": summary})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("reboot", "prepare-recoverbench", "recoverbench"),
        required=True,
    )
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {
        "reboot": reboot,
        "prepare-recoverbench": prepare_recoverbench,
        "recoverbench": recoverbench,
    }[args.stage](args.root)


if __name__ == "__main__":
    main()
