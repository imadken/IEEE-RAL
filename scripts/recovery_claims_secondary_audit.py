"""Independent saved-score alarms, denominator checks and verifier-package smoke run."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np


def read(p):
    return json.loads(p.read_text())


def alarm(times, scores, threshold, persistence=0.1, tolerance=1e-7):
    t = np.asarray(times, float)
    v = np.asarray(scores, float)
    mask = np.isfinite(v) & (v >= threshold)
    boundaries = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    for begin, end in boundaries.reshape(-1, 2):
        eligible = np.flatnonzero(t[begin:end] - t[begin] >= persistence - tolerance)
        if len(eligible):
            return float(t[begin + eligible[0]])
    return None


def same(a, b, tolerance):
    assert (
        a is None
        and b is None
        or a is not None
        and b is not None
        and abs(a - b) <= tolerance
    ), (a, b)


def corrupt_header_checks(root):
    """Software-only corruption checks reuse real outcomes; no new physics labels."""
    directory = root / "mechanical_controls"
    directory.mkdir(exist_ok=True)
    certificates = read(root / "all_certificates.json")
    checks = []
    for task in ["PickCube-v1", "PushCube-v1", "Lift"]:
        source = next(
            (
                c
                for c in certificates
                if c["task"] == task
                and c["split"] == "confirmation"
                and c["method"] == "M"
                and c["route"] == "fresh_prefix"
                and c["F1"] == "PASS"
            ),
            None,
        )
        if source is None:
            checks.append(
                {
                    "task": task,
                    "status": "BLOCKED",
                    "reason": "No F1-qualified physical record for isolated declaration-corruption check",
                }
            )
            continue
        original = read(root / source["bundle"])
        for mutation in ["budget", "time"]:
            bad = json.loads(json.dumps(original))
            if mutation == "budget":
                bad["budget"] -= 1
            else:
                bad["times"][1] += 0.001
            bundle = directory / f"{task}-{mutation}.bundle.json"
            output = directory / f"{task}-{mutation}.certificate.json"
            bundle.write_text(json.dumps(bad, indent=2) + "\n")
            command = [
                sys.executable,
                "-m",
                "dual_rec.contracts.claims",
                "--bundle",
                str(bundle),
                "--output",
                str(output),
            ]
            if not output.exists():
                subprocess.run(command, check=True, capture_output=True)
            result = read(output)
            assert (
                result["status"] == "REFUTED_CONTRACT"
                and result["witness"]["obligation"] == mutation
            )
            verified = subprocess.run(
                command + ["--verify"], check=False, capture_output=True
            )
            assert (verified.returncode == 0) == (mutation == "budget")
            checks.append(
                {
                    "task": task,
                    "mutation": mutation,
                    "status": result["status"],
                    "witness": result["witness"],
                    "raw_verifier_exit_status": verified.returncode,
                    "source_bundle": source["bundle"],
                    "scope": "Mechanically corrupted declaration on unchanged real controls/outcomes, not an additional physically mutated rollout",
                }
            )
    (root / "mechanical_control_checks.json").write_text(
        json.dumps(
            {
                "status": "INCOMPLETE"
                if any(c["status"] == "BLOCKED" for c in checks)
                else "PASS",
                "cases": checks,
            },
            indent=2,
        )
        + "\n"
    )


def run(root):
    old = Path("results/recovery-contracts/20261112T124115Z")
    prior_seals = {}
    for prior in [old, Path("results/reboot-overnight/20261111T224622Z")]:
        seal = read(prior / "completion_manifest.json")
        key = "sha256" if "sha256" in seal else "evidence_sha256"
        prior_seals[prior] = seal[key]
    verified_prior_members = set()

    def verify_prior_member(path):
        for parent, inventory in prior_seals.items():
            if path.is_relative_to(parent):
                assert (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    == inventory[str(path.relative_to(parent))]
                )
                verified_prior_members.add(str(path))

    registry = read(old / "failtime/fold0/cohort_qualification.json")
    assert sum(r["verdict"] == "fail" for r in registry) == 57
    assert sum(r["verdict"] == "success" for r in registry) == 43
    assert sum(not r["onset_within_observed"] for r in registry) == 1
    partitions = read(old / "crossfit_partitions.json")
    seen = []
    for fold in partitions:
        design = read(
            old / f"contract_applications/failtime_fold{fold['fold']}_design_input.json"
        )
        groups = {}
        for r in design["recordings"]:
            groups.setdefault(r["task_group"], set()).add(r["partition"])
        assert all(len(parts) == 1 for parts in groups.values())
        for sample in fold["splits"]["evaluation"]:
            record = read(
                old / f"contract_applications/failtime_stream_{sample}_input.json"
            )["alarm"]
            risk_path = (
                old / f"failtime/fold{fold['fold']}/risks/evaluation/clean/{sample}.npz"
            )
            verify_prior_member(risk_path)
            with np.load(risk_path) as raw:
                assert np.allclose(raw["time"], record["time"])
                assert np.allclose(
                    raw["MCSFA"], np.asarray(record["scores"], float), equal_nan=True
                )
            observed = alarm(
                record["time"],
                record["scores"],
                record["threshold"],
                record["persistence"],
                record["tolerance"],
            )
            same(observed, record["reported_alarm"], record["tolerance"])
            seen.append(sample)
    assert len(seen) == len(set(seen)) == 100
    reboot = Path("results/reboot-overnight/20261111T224622Z")
    registry = read(reboot / "registry.json")
    assert sum(r["eligible"] and r["role"] == "recovery" for r in registry) == 55
    assert sum(r["eligible"] and r["role"] == "reference" for r in registry) == 62
    by_group = {r["group"]: r for r in registry}
    thresholds = read(reboot / "thresholds.json")
    old_results = {
        (r["group"], r["variant"], r["method"]): r
        for r in read(reboot / "outcomes.json")
        if r["stress"] == "clean" and r["boundary_delta"] == 0
    }
    copied = read(root / "external_applications/reboot.json")
    assert len(copied) == 117
    for r in copied:
        registration = by_group[r["group"]]
        with np.load(
            reboot
            / f"predictions/fold{registration['fold']}/Q/clean/evaluation/{r['group'].split(':')[1]}.npz"
        ) as raw:
            threshold = thresholds[f"{registration['fold']}:Q:B3"]["threshold"]
            original = alarm(raw["time"], raw["B3"], threshold, tolerance=2e-6)
            same(original, old_results[(r["group"], "Q", "B3")]["alarm_time"], 2e-6)
            if registration["role"] == "recovery":
                keep = raw["time"] >= registration["onset"]
                reset = alarm(
                    raw["time"][keep], raw["B3"][keep], threshold, tolerance=2e-6
                )
                witness = r["INVALID_reset"]["witness"]
                assert r["INVALID_reset"]["status"] == "REFUTED_CONTRACT"
                same(witness["observed_alarm"], reset, 2e-6)
                same(witness["expected_continuous_alarm"], original, 2e-6)
                assert witness["reset_times"] == [registration["onset"]]
    controls = read(root / "external_applications/reboot_population_controls.json")
    assert controls[0]["certificate"]["status"] == "REFUTED_CONTRACT"
    assert controls[1]["certificate"]["status"] == "INSUFFICIENT_EVIDENCE"
    sources = read(root / "secondary_source_hashes.json")
    for name, expected in sources.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected
        verify_prior_member(Path(name))
    package = root / "external_evaluator"
    for name, expected in read(package / "SHA256.json").items():
        assert hashlib.sha256((package / name).read_bytes()).hexdigest() == expected
    subprocess.run(
        [sys.executable, str(package / "run.py")],
        check=True,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
    )
    answers = read(root / "evaluator_answer_key.json")
    for name, expected in answers.items():
        assert (
            read(package / "outputs" / (Path(name).stem + ".certificate.json"))[
                "status"
            ]
            == expected
        )
    corrupt_header_checks(root)
    result = {
        "status": "PASS",
        "failtime_scores_rechecked": 100,
        "reboot_scores_rechecked": 117,
        "reset_witnesses_recomputed": 55,
        "censored_onsets_retained": 1,
        "task_group_separation_verified": True,
        "external_fresh_process_cases": len(answers),
        "reused_members_checked_against_historical_seals": len(verified_prior_members),
        "scope": "Independent numerical software paths, not an independent human study; saved models and annotations unchanged",
    }
    (root / "external_evaluator_smoke.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(result)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    assert not (a.root / "completion_manifest.json").exists(), "Evidence sealed"
    run(a.root)
