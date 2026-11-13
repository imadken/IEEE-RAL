"""Read-only legacy adapters and frozen future-evaluator package; no model training."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from dual_rec.contracts.checks import first_alarm
from dual_rec.contracts.claims import (
    AlarmEvidence,
    MatchedEvidence,
    certify_alarm,
    matched_effect,
)

SOURCES = {}


def load(p):
    SOURCES[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def persist_matched_inputs(root, certificates):
    grouped = defaultdict(list)
    for c in certificates:
        if c["method"] == "M" and c["route"] == "fresh_prefix":
            grouped[(c["split"], c["task"], c["parent"], c["condition"])].append(c)
    directory = root / "matched_bundles"
    directory.mkdir(exist_ok=True)
    index = []
    for key, cs in sorted(grouped.items()):
        if len(cs) != 2:
            continue
        cs.sort(key=lambda c: c["action"])
        payload = {"branches": [load(root / c["bundle"]) for c in cs]}
        ident = "-".join(key)
        bundle = directory / (ident + ".bundle.json")
        output = directory / (ident + ".certificate.json")
        save(bundle, payload)
        result = matched_effect(MatchedEvidence.model_validate(payload))
        digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
        save(output, result | {"bundle_sha256": digest})
        index.append(
            dict(zip(["split", "task", "parent", "condition"], key, strict=True))
            | {
                "bundle": str(bundle.relative_to(root)),
                "certificate": str(output.relative_to(root)),
                "bundle_sha256": digest,
                "branch_bundles": [c["bundle"] for c in cs],
                "status": result["status"],
            }
        )
    save(root / "paired_certificate_index.json", index)
    return index


def main(root):
    save(
        root / "worker_runtime_versions.json",
        {
            "python": sys.version,
            "executable": sys.executable,
            "sys_path": sys.path,
            "packages": {
                n: importlib.metadata.version(n)
                for n in [
                    "numpy",
                    "pydantic",
                    "scipy",
                    "mani-skill",
                    "sapien",
                    "robosuite",
                    "mujoco",
                    "torch",
                ]
            },
            "worker_environment": {
                k: os.environ.get(k)
                for k in [
                    "CUDA_VISIBLE_DEVICES",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMBA_NUM_THREADS",
                    "PYTHONPATH",
                ]
            },
            "scope": "Recorded in the same unchanged bounded-worker interpreter/path construction used for physics; historical borrowed analysis dependencies explicit. No packages installed or locks changed.",
        },
    )
    old = Path("results/recovery-contracts/20261112T124115Z")
    dest = root / "external_applications"
    dest.mkdir(exist_ok=True)
    reports = []
    reboot_population_controls = []
    for case in ["reboot_uncollapsed_aliases", "reboot_missing_temporal_target"]:
        payload = load(old / f"contract_applications/{case}_input.json")
        result = certify_alarm(
            AlarmEvidence(task="REBOOT", parent=case, evidence=payload)
        )
        reboot_population_controls.append({"case": case, "certificate": result})
    save(dest / "reboot_population_controls.json", reboot_population_controls)
    labels = load(old / "contract_applications/failtime_event_labels_input.json")
    registry = load(old / "failtime/fold0/cohort_qualification.json")
    partitions = load(old / "crossfit_partitions.json")
    ids = []
    for fold in partitions:
        design = load(
            old / f"contract_applications/failtime_fold{fold['fold']}_design_input.json"
        )
        for sample in fold["splits"]["evaluation"]:
            stream = load(
                old / f"contract_applications/failtime_stream_{sample}_input.json"
            )
            e = {
                k: v
                for d in [labels, design, stream]
                for k, v in d.items()
                if v is not None
            }
            claim = AlarmEvidence(task="FailTime-Long", parent=sample, evidence=e)
            out = certify_alarm(claim)
            save(dest / (sample + ".json"), out)
            save(dest / (sample + ".bundle.json"), claim.model_dump())
            reports.append(out)
            ids.append(sample)
    assert len(ids) == len(set(ids)) == 100
    # Exactly the existing REBOOT score streams and original numerical tolerance.
    reboot = Path("results/reboot-overnight/20261111T224622Z")
    thresholds = load(reboot / "thresholds.json")
    reg = load(reboot / "registry.json")
    oldout = {
        (r["group"], r["variant"], r["method"]): r
        for r in load(reboot / "outcomes.json")
        if r["stress"] == "clean" and r["boundary_delta"] == 0
    }
    reboot_results = []
    for r in reg:
        if not r["eligible"]:
            continue
        group = r["group"]
        prediction_path = (
            reboot
            / f"predictions/fold{r['fold']}/Q/clean/evaluation/{group.split(':')[1]}.npz"
        )
        SOURCES[str(prediction_path)] = hashlib.sha256(
            prediction_path.read_bytes()
        ).hexdigest()
        data = np.load(prediction_path)
        theta = thresholds[f"{r['fold']}:Q:B3"]["threshold"]
        alarm = oldout[(group, "Q", "B3")]["alarm_time"]
        e = {
            "alarm": {
                "time": data["time"].tolist(),
                "scores": data["B3"].tolist(),
                "threshold": theta,
                "tolerance": 2e-6,
                "reported_alarm": alarm,
            }
        }
        original = certify_alarm(AlarmEvidence(task="REBOOT", parent=group, evidence=e))
        bundle_name = "reboot-" + group.replace(":", "-") + ".bundle.json"
        save(
            dest / bundle_name,
            AlarmEvidence(task="REBOOT", parent=group, evidence=e).model_dump(),
        )
        mutated = None
        if r["role"] == "recovery":
            bad = copy.deepcopy(e)
            bad["alarm"]["reset_times"] = [r["onset"]]
            keep = data["time"] >= r["onset"]
            bad["alarm"]["reported_alarm"] = first_alarm(
                data["time"][keep], data["B3"][keep], theta, 0.1, 2e-6
            )
            mutated = certify_alarm(
                AlarmEvidence(task="REBOOT", parent=group, evidence=bad)
            )
            save(
                dest / ("INVALID-reset-" + bundle_name),
                AlarmEvidence(task="REBOOT", parent=group, evidence=bad).model_dump(),
            )
            assert mutated["status"] == "REFUTED_CONTRACT"
        reboot_results.append(
            {"group": group, "original": original, "INVALID_reset": mutated}
        )
    save(dest / "reboot.json", reboot_results)
    save(
        root / "external_summary.json",
        {
            "failtime_records": len(reports),
            "failtime_roles": {
                role: sum(r["verdict"] == role for r in registry)
                for role in ["fail", "success"]
            },
            "censored_onsets_retained": sum(
                not r["onset_within_observed"] for r in registry
            ),
            "failtime_statuses": {
                s: sum(r["status"] == s for r in reports)
                for s in ["SUPPORTED", "REFUTED_CONTRACT", "INSUFFICIENT_EVIDENCE"]
            },
            "reboot_records": len(reboot_results),
            "reboot_eligible_roles": {
                role: sum(r["role"] == role and r["eligible"] for r in reg)
                for role in ["recovery", "reference"]
            },
            "reboot_population_controls": reboot_population_controls,
            "invalid_reset_witnesses": sum(
                r["INVALID_reset"] is not None for r in reboot_results
            ),
            "scope": "Protocol evidence only, unchanged saved scores/models. No physical failure-onset or recovery-effect claim.",
        },
    )
    package = root / "external_evaluator"
    (package / "bundles").mkdir(parents=True, exist_ok=True)
    answers = {}
    allc = load(root / "all_certificates.json")
    pair_index = persist_matched_inputs(root, allc)
    for task in ["PickCube-v1", "PushCube-v1", "Lift"]:
        for route in [
            "fresh_prefix",
            "native_snapshot",
            "physics",
            "controller_memory",
            "missing_provenance",
            "parent_rng",
        ]:
            candidates = [
                c
                for c in allc
                if c["method"] == "M"
                and c["split"] == "confirmation"
                and c["task"] == task
                and c["route"] == route
                and c["action"] == "recover"
            ]
            if not candidates:
                continue
            selected = min(candidates, key=lambda c: int(c["parent"]))
            bundle = load(root / selected["bundle"])
            name = task + "-" + route + ".json"
            source = root / bundle["raw_trace_path"]
            target = package / bundle["raw_trace_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copyfile(source, target)
            save(package / "bundles" / name, bundle)
            answers[name] = selected["status"]
    for task in ["PickCube-v1", "PushCube-v1", "Lift"]:
        choices = [
            p for p in pair_index if p["split"] == "confirmation" and p["task"] == task
        ]
        if not choices:
            continue
        chosen = min(choices, key=lambda p: int(p["parent"]))
        payload = load(root / chosen["bundle"])
        name = task + "-matched-effect.json"
        for branch in payload["branches"]:
            source = root / branch["raw_trace_path"]
            target = package / branch["raw_trace_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copyfile(source, target)
        save(package / "bundles" / name, payload)
        answers[name] = chosen["status"]
    failtime_bundle = dest / (min(ids) + ".bundle.json")
    reset_bundle = min(dest.glob("INVALID-reset-*.bundle.json"))
    for name, source in [
        ("FailTime-online.json", failtime_bundle),
        ("REBOOT-invalid-reset.json", reset_bundle),
    ]:
        payload = load(source)
        save(package / "bundles" / name, payload)
        answers[name] = certify_alarm(AlarmEvidence.model_validate(payload))["status"]
    # Include only source code and public dependency declarations; no answer key.
    for relative in [
        "dual_rec/__init__.py",
        "dual_rec/contracts/__init__.py",
        "dual_rec/contracts/checks.py",
        "dual_rec/contracts/claims.py",
    ]:
        p = package / "src" / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("src") / relative, p)
    (package / "run.py").write_text(
        """import os,subprocess,sys\nfrom pathlib import Path\np=Path(__file__).resolve().parent\nos.environ['PYTHONPATH']=str(p/'src')\nout=p/'outputs';out.mkdir(exist_ok=True)\nfor b in sorted((p/'bundles').glob('*.json')):\n c=out/(b.stem+'.certificate.json')\n command=[sys.executable,'-m','dual_rec.contracts.claims','--bundle',str(b),'--output',str(c)]\n if not c.exists():subprocess.run(command,check=True)\n subprocess.run(command+['--verify'],check=True)\n"""
    )
    (package / "requirements.txt").write_text(
        "".join(
            f"{name}=={importlib.metadata.version(name)}\n"
            for name in ["numpy", "pydantic"]
        )
    )
    (package / "README.md").write_text(
        "# Frozen verifier cases\n\nRun `uv run --no-sync python PATH/TO/external_evaluator/run.py` from the original qualified repository environment, or use an existing environment with requirements.txt dependencies. No simulator or trained weights are required. Execution, matched-alternative and online-alarm bundles use the common API. Outputs include independent-process raw-trace and certificate-hash verification. Full-cohort uncertainty was independently audited in the main evidence root; this compact package carries representative records and their declared qualification counts. The answer key is deliberately outside this package. This is a future-evaluator package, not a completed human study. Source recorder provenance remains a trusted assumption.\n"
    )
    save(root / "secondary_source_hashes.json", SOURCES)
    save(root / "evaluator_answer_key.json", answers)
    save(
        package / "SHA256.json",
        {
            str(p.relative_to(package)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in package.rglob("*")
            if p.is_file()
            and p.name != "SHA256.json"
            and "outputs" not in p.relative_to(package).parts
        },
    )
    print({"external_bundles": len(answers), "human_evaluation": False})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    assert not (a.root / "completion_manifest.json").exists(), "Evidence sealed"
    main(a.root)
