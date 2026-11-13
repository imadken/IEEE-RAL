"""Local DSRE initialization, preservation, compact review archive and integrity seal."""

import argparse
import fcntl
import hashlib
import json
import resource
import subprocess
import tarfile
import time
from pathlib import Path

import psutil


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def maintained():
    return [
        *sorted(Path().glob("DSRE*.md")),
        *sorted(Path("docs").glob("DSRE*.md")),
        Path("config/dsre_stage1.json"),
        *sorted(Path("src/dual_rec/dsre").glob("*.py")),
        *sorted(Path("scripts").glob("dsre_*.py")),
        *sorted(Path("tests").glob("test_dsre_*.py")),
    ]


def document(name):
    original = Path(name)
    return original if original.is_file() else Path("docs") / name


def initialize(root):
    root.mkdir(parents=True, exist_ok=False)
    names = [n for n in git("ls-files", "-z").split("\0") if n]
    names += [str(p) for p in Path("docs").rglob("*") if p.is_file()]
    save(
        root / "initial.json",
        {
            "started_epoch": time.time(),
            "start_scope": "fresh bounded reproduction",
            "limits": {
                "wall_seconds": 28800,
                "cpu_seconds": 36000,
                "new_bytes": 1000000000,
            },
            "reserve": {
                "wall_seconds": 3600,
                "cpu_seconds": 1800,
                "new_bytes": 50000000,
            },
            "base": git("rev-parse", "HEAD"),
            "initial_status": git("status", "--short"),
            "prior_files": {
                n: sha(Path(n)) if Path(n).is_file() else None for n in names
            },
            "historical_seals": {
                str(p): sha(p)
                for p in Path("results").glob("**/completion_manifest.json")
            },
            "allowed_changes": [],
        },
    )
    (root / "commands.jsonl").write_text("")
    (root / "authority.txt").write_bytes(
        document("DSRE_CODEX_STAGE1_EXECUTION_CONTRACT.md").read_bytes()
    )
    save(
        root / "pre_evaluation_freeze.json",
        {
            "sha256": {
                str(document(p)) if p.endswith(".md") else p: sha(
                    document(p) if p.endswith(".md") else Path(p)
                )
                for p in [
                    "DSRE_CODEX_STAGE1_EXECUTION_CONTRACT.md",
                    "DSRE_STAGE1_PROTOCOL.md",
                    "DSRE_NOVELTY_MATRIX.md",
                    "config/dsre_stage1.json",
                ]
            },
            "status": "FRESH_REPRODUCTION_FIXED_SPEC",
        },
    )
    save(
        root / "analysis_plan.json",
        {
            "frozen_before_method_numbers": True,
            "conditional_interval_minimum_recommending_groups": 10,
            "matched_frontier_bands": {
                "coverage_absolute_fraction": 0,
                "unacceptable_action_rate": 0,
            },
            "evidence_caps": list(range(9)),
            "bootstrap": "2000 paired task/seed groups, both conditions together",
        },
    )
    print("Fresh bounded DSRE root:", root)


def preserve(root):
    initial = load(root / "initial.json")
    moved = (
        {
            r["original"]: r
            for r in load(root / "user_document_relocations.json")["moves"]
        }
        if (root / "user_document_relocations.json").exists()
        else {}
    )
    for name, expected in initial["prior_files"].items():
        actual = Path(name)
        if expected is not None and not actual.is_file() and name in moved:
            assert moved[name]["expected"] == expected and moved[name]["identical"]
            actual = Path(moved[name]["current"])
        assert (sha(actual) if actual.is_file() else None) == expected, name
    for name, expected in initial["historical_seals"].items():
        assert sha(Path(name)) == expected, name
    prior_members = 0
    for old in [
        Path("results/explanation-repair/20261113T091510Z"),
        Path("results/explanation-repair-week2/20261113T130926Z"),
    ]:
        for name, expected in load(old / "completion_manifest.json")["sha256"].items():
            assert sha(old / name) == expected, name
            prior_members += 1
    for path, expected in load(root / "source_members.json").items():
        assert sha(Path(path)) == expected, path
    return {
        "status": "PASS",
        "initial_tracked_and_user_document_paths": len(initial["prior_files"]),
        "historical_seals": len(initial["historical_seals"]),
        "complete_week1_week2_sealed_members": prior_members,
        "paired_source_members": len(load(root / "source_members.json")),
        "content_identical_document_relocations": len(moved),
        "gitignore_uv_lock_historical_evidence_unrelated_changes": "PRESERVED",
    }


def seal(root):
    assert not (root / "completion_manifest.json").exists()
    started = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        preservation = preserve(root)
        assert load(root / "validation.json")["status"] == "PASS"
        assert load(root / "independent_audit.json")["status"].startswith("PASS_")
        assert load(root / "independent_derived_audit.json")["status"].startswith(
            "PASS_"
        )
        if (root / "user_document_relocations.json").exists():
            assert load(root / "post_relocation_source_audit.json")[
                "status"
            ].startswith("PASS_")
        assert load(root / "experiment_completed.json")["status"] == "COMPLETE"
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        failed = {j["name"] for j in jobs if j["exit_status"]}
        resolved = load(root / "resolved_worker_failures.json")
        assert failed == set(resolved), (failed, set(resolved))
        ancestors = {p.pid for p in psutil.Process().parents()} | {psutil.Process().pid}
        workers = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                args = process.info["cmdline"] or []
                if (
                    process.pid not in ancestors
                    and any(
                        "dsre_" in a or "reboot_overnight_worker.py" in a for a in args
                    )
                    and any(str(root) in a for a in args)
                ):
                    workers.append(process.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        assert not workers, workers
        initial = load(root / "initial.json")
        accounting = {
            "wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": initial["start_scope"],
            "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
            "measured_seal_cpu_seconds_before_archive": time.process_time() - started,
            "unmetered_orchestration_cpu_allowance_seconds": 600,
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "gpu_seconds": 0,
            "new_simulator_continuations": 0,
            "new_models_downloaded": 0,
            "paid_api_calls": 0,
            "new_public_files_downloaded_bytes": 0,
            "public_primary_source_tool_traffic": "Not byte-metered; conservative 40MB transfer allowance below250MB budget, distinct from zero local dataset/model downloads",
            "worker_jobs": len(jobs),
            "preserved_resolved_failures": sorted(failed),
            "qualified_checkpoint_pairs": load(root / "data_qualification.json")[
                "pairs"
            ],
            "independent_seed_groups": load(root / "data_qualification.json")[
                "seed_groups"
            ],
            "four_category_trees_trained": load(root / "experiment_completed.json")[
                "trained_four_category_trees"
            ],
            "branch": git("branch", "--show-current"),
            "commit": git("rev-parse", "HEAD"),
            "workers_remaining": workers,
            "push_attempted": False,
            "preservation": preservation,
        }
        assert accounting["wall_seconds"] < initial["limits"]["wall_seconds"]
        assert (
            accounting["measured_worker_cpu_seconds"]
            + accounting["measured_seal_cpu_seconds_before_archive"]
            + 600
            < initial["limits"]["cpu_seconds"]
        )
        save(root / "resources.json", accounting)
        names = [
            "authority.txt",
            "user_document_relocations.json",
            "post_execution_path_amendment.json",
            "post_execution_path_amendment/dsre_experiment.py",
            "post_relocation_source_audit.json",
            "specification_status.json",
            "pre_evaluation_freeze.json",
            "experiment_freeze.json",
            "analysis_plan.json",
            "data_qualification.json",
            "qualification_exclusions.json",
            "qualification_correction.json",
            "paired_outcome_prevalence.json",
            "qualified_pairs.jsonl",
            "source_members.json",
            "e0_independent_agreement.json",
            "metrics.json",
            "paired_comparisons.json",
            "frontier.csv",
            "matched_frontier.json",
            "feature_collisions.json",
            "witness_examples.json",
            "method_runtime.json",
            "runtime_primary_comparison.json",
            "runtime_versions.json",
            "literature_inspection.json",
            "greedy_difference_diagnostics.json",
            "failed_start_metrics.json",
            "policy_outcome_disagreements.json",
            "calibration_feasibility.json",
            "frozen_router.json",
            "prospective_fresh_seed_plan.json",
            "PickCube-v1_prospective_cost.json",
            "PushCube-v1_prospective_cost.json",
            "independent_audit.json",
            "independent_derived_audit.json",
            "validation.json",
            "resolved_worker_failures.json",
            "resources.json",
        ]
        with tarfile.open(root / "supervisor_review.tar.gz", "w:gz") as archive:
            for name in names:
                if (root / name).exists():
                    archive.add(root / name, arcname="evidence/" + name)
            for p in sorted((root / "figures").glob("*.png")):
                archive.add(p, arcname="evidence/figures/" + p.name)
            for path in maintained():
                archive.add(path, arcname="source/" + str(path))
        members = {
            str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()
        }
        size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        assert size + 1000000 < initial["limits"]["new_bytes"]
        manifest = {
            "status": "COMPLETE_EXECUTABLE_STAGE1_PRELIMINARY_ONLY_BLUEPRINT_MISSING",
            "resources": accounting
            | {
                "logical_artifact_bytes_before_small_manifest": size,
                "seal_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            },
            "sha256": members,
            "source_sha256": {str(p): sha(p) for p in maintained()},
            "scientific_gate": "PRELIMINARY_ONLY; B7/B5at1 equivalence, strong simple baselines, calibration absent, blueprint consistency unavailable",
            "no_authorization": "No manuscript, new physics, independent calibration/confirmation or push",
        }
        save(root / "completion_manifest.json", manifest)
        print(json.dumps(manifest["resources"], indent=2))
        print("completion_manifest_sha256", sha(root / "completion_manifest.json"))


def verify(root):
    manifest = load(root / "completion_manifest.json")
    for name, expected in manifest["sha256"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert sha(Path(name)) == expected, name
    print(
        json.dumps(
            {
                "status": "PASS_SEAL_AND_PRESERVATION",
                "files": len(manifest["sha256"]),
                "preservation": preserve(root),
                "manifest_sha256": sha(root / "completion_manifest.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=["initialize", "seal", "verify"], required=True
    )
    args = parser.parse_args()
    {"initialize": initialize, "seal": seal, "verify": verify}[args.stage](args.root)
