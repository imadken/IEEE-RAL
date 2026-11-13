"""Preserve prior evidence, verify follow-up inference, package and seal locally."""

import argparse
import fcntl
import hashlib
import json
import subprocess
import tarfile
import time
from pathlib import Path

import numpy as np
import psutil
from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_paper_finish import byte_size, format_audit, validate


def workers(root):
    current = psutil.Process()
    excluded = {current.pid, *[p.pid for p in current.parents()]}
    active = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if (
                process.pid not in excluded
                and str(root) in args
                and any(
                    Path(a).name.startswith(("dsre_followup_", "dsre_paper_"))
                    or Path(a).name == "reboot_overnight_worker.py"
                    for a in args
                )
            ):
                active.append(process.pid)
        except psutil.Error:
            pass
    return active


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def reconciled_validation_failures(root, jobs):
    failed = [j for j in jobs if j["exit_status"] != 0]
    if not failed:
        return []
    assert len(failed) == 1 and failed[0]["name"] == "validation"
    prior = read(root / "validation_attempts/first.json")
    reconciliation = read(root / "validation_reconciliation.json")
    assert (
        sha(root / "validation_attempts/first.json")
        == reconciliation["failed_validation_sha256"]
    )
    assert failed[0]["log_sha256"] == reconciliation["failed_log_sha256"]
    bad_checks = [c for c in prior["checks"] if c["exit_status"] != 0]
    assert len(bad_checks) == 1
    assert bad_checks[0]["command"] == ["git", "diff", "--check"]
    assert "trailing whitespace" in bad_checks[0]["stdout"]
    assert any(j["name"] == "validation_retry" and j["exit_status"] == 0 for j in jobs)
    assert read(root / "validation.json")["status"] == "PASS"
    return [
        "validation: preserved first-run whitespace failure, corrected and fully revalidated"
    ]


def maintained(root):
    initial = read(root / "initial.json")
    return [
        *[Path(n) for n in initial["authorized_updates"]],
        Path("config/dsre_followup.json"),
        *sorted(Path("scripts").glob("dsre_followup_*.py")),
        Path("tests/test_dsre_followup.py"),
        Path("rss2027/figures/necessity.pdf"),
        Path("rss2027/figures/necessity.png"),
        Path("rss2027/references.bib"),
        Path("rss2027/IEEEtran.cls"),
    ]


def preservation(root):
    initial = read(root / "initial.json")
    allowed = set(initial["authorized_updates"])
    counts = {}
    for category in ("prior_files", "prior_run_members", "historical_seals"):
        for name, expected in initial[category].items():
            path = Path(name)
            if category == "prior_files" and name in allowed:
                assert sha(root / "starting_files" / name) == expected, name
                original = subprocess.check_output(
                    ["git", "show", initial["base"] + ":" + name]
                )
                assert hashlib.sha256(original).hexdigest() == expected, name
            else:
                assert (sha(path) if path.is_file() else None) == expected, name
        counts[category] = len(initial[category])
    old = Path("results/dsre-rss2027/20261113T193554Z")
    seal = read(old / "completion_manifest.json")
    for name, expected in seal["maintained_files"].items():
        previous = subprocess.check_output(
            ["git", "show", initial["base"] + ":" + name]
        )
        assert hashlib.sha256(previous).hexdigest() == expected, name
    verify_freeze(root)
    return counts | {
        "authorized_paper_updates_preserved_in_starting_files_and_git": len(allowed),
        "previous_maintained_versions_verified_from_reviewed_commit": len(
            seal["maintained_files"]
        ),
        "frozen_pins": sum(
            len(read(root / "confirmation_freeze.json")[k])
            for k in ("source_sha256", "input_sha256")
        ),
    }


def numerical_audit(root):
    result = read(root / "suffix_results.json")
    records = read(root / "suffix_prediction_records.json")
    missing = read(root / "followup_missingness.json")
    assert len(records) == missing["primary_checkpoints"] * 20
    groups = {r["group"] for r in records}
    assert (
        len(groups) == missing["complete_parents"]
        and "PickCube-v1/6000033" not in groups
    )
    assert not groups & set(
        read(Path("results/dsre-rss2027/20261113T193554Z/physics_completed.json"))[
            "fully_completed_seed_parents"
        ]
    )
    names = {p["group"] for p in read(root / "fresh_seed_manifest.json")["parents"]}
    assert groups <= names and len(names) == 333
    recomputed = {}
    keys = 0
    for key, cell in result["tables"].items():
        task, budget, method, population = key.split("|")
        subset = [
            r
            for r in records
            if r["task"] == task
            and r["budget"] == int(budget)
            and r["method"] == method
            and (
                population == "all"
                or population == r["category"]
                or population
                == ("initial_success" if r["initial_success"] else "initial_failure")
                or population == "action_" + (r["action"] or "abstain")
            )
        ]
        assert len(subset) == cell["checkpoints"]
        for field in ("recommended", "successful", "unacceptable", "literals"):
            assert sum(r[field] for r in subset) == cell[field], (key, field)
            keys += 1
        assert cell["recommended"] == cell["successful"] + cell["unacceptable"]
        assert cell["abstained"] + cell["recommended"] == cell["checkpoints"]
        recomputed[key] = cell
    # Separate matrix implementation of all primary paired bootstrap endpoints.
    config = read(Path("config/dsre_followup.json"))
    bootstrap_checks = 0
    for tindex, task in enumerate(("PickCube-v1", "PushCube-v1")):
        task_parents = sorted({r["group"] for r in records if r["task"] == task})
        selected = {
            b: {
                r["id"]: r
                for r in records
                if r["task"] == task and r["method"] == "DSRE" and r["budget"] == b
            }
            for b in (0, 1)
        }
        for population in (
            "all",
            "initial_failure",
            "initial_success",
            "recover_only",
            "continue_only",
            "both",
            "neither",
        ):
            base = [
                r
                for r in selected[0].values()
                if population
                in (
                    "all",
                    r["category"],
                    "initial_success" if r["initial_success"] else "initial_failure",
                )
            ]
            expected = result["paired_intervals"][f"{task}|b1-b0|{population}"]
            for label, field in (
                ("success_difference", "successful"),
                ("coverage_difference", "recommended"),
                ("unacceptable_difference", "unacceptable"),
            ):
                if not base:
                    assert expected[label] is None
                    continue
                frame = np.zeros((len(task_parents), 2))
                for i, group in enumerate(task_parents):
                    same = [r for r in base if r["group"] == group]
                    frame[i] = [
                        sum(selected[1][r["id"]][field] - r[field] for r in same),
                        len(same),
                    ]
                rng = np.random.Generator(
                    np.random.PCG64(config["bootstrap_seed"] + tindex)
                )
                indices = rng.integers(
                    len(task_parents), size=(4000, len(task_parents))
                )
                sample = frame[indices].sum(axis=1)
                sample = sample[sample[:, 1] > 0]
                limits = np.percentile(sample[:, 0] / sample[:, 1], [2.5, 97.5])
                assert np.array_equal(
                    limits, np.asarray(expected[label]["parent_percentile95"])
                )
                assert (
                    float(frame[:, 0].sum() / frame[:, 1].sum())
                    == expected[label]["value"]
                )
                bootstrap_checks += 1
    lookup = {(r["id"], r["budget"], r["method"]): r for r in records}
    baseline_bootstrap_checks = 0
    for key, expected in result["paired_intervals"].items():
        if len(key.split("|")) != 4:
            continue
        task, budget_name, comparison, population = key.split("|")
        budget = int(budget_name[1:])
        method = comparison.removeprefix("DSRE-")
        parents = sorted({r["group"] for r in records if r["task"] == task})
        base = [
            r
            for r in records
            if r["task"] == task
            and r["budget"] == budget
            and r["method"] == "DSRE"
            and (population == "all" or not r["initial_success"])
        ]
        for label, field in (
            ("success_difference", "successful"),
            ("unacceptable_difference", "unacceptable"),
        ):
            if not base:
                assert expected[label] is None
                continue
            frame = np.array(
                [
                    [
                        sum(
                            r[field] - lookup[r["id"], budget, method][field]
                            for r in base
                            if r["group"] == group
                        ),
                        sum(r["group"] == group for r in base),
                    ]
                    for group in parents
                ],
                dtype=float,
            )
            rng = np.random.Generator(
                np.random.PCG64(config["bootstrap_seed"] + (task == "PushCube-v1"))
            )
            sampled = frame[rng.integers(len(parents), size=(4000, len(parents)))].sum(
                axis=1
            )
            sampled = sampled[sampled[:, 1] > 0]
            limits = np.percentile(sampled[:, 0] / sampled[:, 1], [2.5, 97.5])
            assert np.array_equal(
                limits, np.asarray(expected[label]["parent_percentile95"])
            ), (key, label)
            assert (
                float(frame[:, 0].sum() / frame[:, 1].sum()) == expected[label]["value"]
            )
            baseline_bootstrap_checks += 1
    pooled = read(root / "pooled_secondary_results.json")
    earlier = read(
        Path("results/dsre-rss2027/20261113T193554Z/fresh_stratified_tables.json")
    )
    pooled_checks = 0
    for key, cell in pooled["tables"].items():
        old_key = key.replace("|action_", "|")
        old_cell, new_cell = earlier.get(old_key, {}), result["tables"].get(key, {})
        for field in (
            "checkpoints",
            "parents",
            "recommended",
            "successful",
            "unacceptable",
            "literals",
        ):
            assert cell[field] == old_cell.get(field, 0) + new_cell.get(field, 0), (
                key,
                field,
            )
            pooled_checks += 1
    b7 = 0
    cart_disagreements = 0
    for row in records:
        if row["method"] == "DSRE":
            assert row["action"] == lookup[row["id"], row["budget"], "B7"]["action"]
            cart_disagreements += (
                row["action"]
                != lookup[row["id"], row["budget"], "CART2_strict"]["action"]
            )
            b7 += 1
    return {
        "status": "PASS",
        "stratified_fields_recomputed": keys,
        "primary_bootstrap_cells_independently_recomputed": bootstrap_checks,
        "strong_baseline_bootstrap_cells_independently_recomputed": baseline_bootstrap_checks,
        "B7_equal_views": b7,
        "strict_CART2_action_disagreements": cart_disagreements,
        "primary_parent_count": len(groups),
        "primary_checkpoints": missing["primary_checkpoints"],
        "pooled_secondary_fields_recomputed": pooled_checks,
    }


def paper_claim_audit(root):
    text = Path("rss2027/dsre_stage1.tex").read_text()
    results = read(root / "suffix_results.json")
    missing = read(root / "followup_missingness.json")
    fields = 0
    for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for budget in (0, 1):
            row = results["tables"][f"{task}|{budget}|DSRE|all"]
            failed = results["tables"].get(
                f"{task}|{budget}|DSRE|initial_failure",
                {"successful": 0, "checkpoints": 0},
            )
            expected = f"{label} & {budget} & {row['recommended']} / {row['successful']} / {row['unacceptable']} & {failed['successful']} / {failed['checkpoints']}"
            assert expected in text, expected
            fields += 5
    interval = results["paired_intervals"]["PickCube-v1|b1-b0|all"][
        "success_difference"
    ]
    if interval is not None:
        low, high = interval["parent_percentile95"]
        assert f"[{100 * low:.2f},{100 * high:.2f}]" in text
        fields += 2
    for key in (
        "PickCube-v1|b1-b0|initial_failure",
        "PickCube-v1|b1-b0|recover_only",
        "PickCube-v1|b1|DSRE-CART2_strict|all",
        "PickCube-v1|b1|DSRE-CART2_beta10|all",
    ):
        value = results["paired_intervals"][key]["success_difference"]
        low, high = value["parent_percentile95"]
        assert f"[{100 * low:.2f},{100 * high:.2f}]" in text
        fields += 2
    exception = read(root / "fresh_control_exception.json")["exceptions"]
    assert len(exception) == 1
    row = exception[0]["record"]
    assert sha(Path(exception[0]["source"])) == exception[0]["source_sha256"]
    assert (
        row["successful"] == 1 and row["literals"] == 3 and row["support_parents"] == 5
    )
    assert "three facts supported by five reference parents" in text
    assert f"{missing['complete_parents']}/333" in text
    old = read(
        Path("results/dsre-rss2027/20261113T193554Z/reused_stratified_tables.json")
    )
    old_counts = ",".join(
        str(old[f"PickCube-v1|{b}|CART2_strict|all"]["successful"]) for b in range(4)
    )
    assert old_counts in text and "201,224,224,217" == old_counts
    assert "296/422" in text and "16,880" in text
    assert "\\mathbb{I}" in text and "mathbf1" not in text
    assert "will update the claims" not in text
    for case in read(root / "physical_examples.json")["cases"]:
        assert sha(Path(case["source"])) == case["source_sha256"]
        assert f"{case['dx']:+.5f}" in text
        fields += 1
    return {
        "status": "PASS",
        "table_interval_and_physical_fields_checked": fields,
        "historical_CART_transcription_correction_verified": True,
        "primary_population": "New suffix only; old boundary excluded",
    }


def audit(root):
    assert not workers(root)
    assert read(root / "independent_audit.json")["status"] == "PASS"
    assert read(root / "old_prediction_regression.json")["status"] == "PASS"
    chunks = [read(p) for p in sorted((root / "chunks").glob("*_complete.json"))]
    assert all(
        (root / "chunks" / p.name.replace("_started", "_complete")).exists()
        for p in (root / "chunks").glob("*_started.json")
    )
    assert sum(c["wall_seconds"] for c in chunks) <= 10800
    marked = [
        read(p)
        for p in (root / "parent_progress").glob("*.json")
        if read(p)["status"] == "COMPLETE"
    ]
    source_checks = 0
    for parent in marked:
        for cell in parent["checkpoints"]:
            path = Path(cell["source"])
            summary = read(path.parent / "summary.json")
            assert sha(path) == cell["source_sha256"] == summary["source_sha256"]
            assert cell["id"] == summary["id"] and parent["group"] == summary["group"]
            source_checks += 1
    frozen = read(root / "confirmation_freeze.json")["source_sha256"]
    jobs = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    reconciled = reconciled_validation_failures(root, jobs)
    job_source_checks = 0
    for job in jobs:
        assert sha(root / (job["name"] + ".log")) == job["log_sha256"]
        for name, expected in frozen.items():
            assert job["source_sha256"].get(name) == expected, (job["name"], name)
            job_source_checks += 1
    chunk_audits = [
        read(p) for p in sorted((root / "chunks").glob("*_independent_audit.json"))
    ]
    assert len(chunk_audits) == len(chunks)
    assert all(c["status"] == "PASS" for c in chunk_audits)
    assert (
        sum(c["qualified_complete_parent_checkpoints_audited"] for c in chunk_audits)
        == source_checks
    )
    findings = {
        "status": "PASS",
        "preservation": preservation(root),
        "numerical": numerical_audit(root),
        "paper_claims": paper_claim_audit(root),
        "format": format_audit(root),
        "atomic_parent_source_links_checked": source_checks,
        "worker_frozen_source_hashes_checked": job_source_checks,
        "independent_chunk_audits": len(chunk_audits),
        "preserved_validation_history": reconciled,
        "workers": [],
        "audit_scope": "Separate raw-physics/rule/predicate and matrix-statistical implementations within same session; not external human replication.",
    }
    atomic(root / "final_audit.json", findings)
    print(
        json.dumps(
            {
                "status": "PASS",
                "parents": len(marked),
                "checkpoint_links": source_checks,
                "pages": 6,
            }
        ),
        flush=True,
    )


def finalize_physics(root):
    assert not workers(root)
    manifest = read(root / "fresh_seed_manifest.json")["parents"]
    progress = [read(p) for p in (root / "parent_progress").glob("*.json")]
    complete = [p for p in progress if p["status"] == "COMPLETE"]
    attempts = [read(p) for p in (root / "parent_attempts").glob("*.json")]
    assert len({p["group"] for p in attempts}) == len(attempts) <= 333
    chunks = [read(p) for p in sorted((root / "chunks").glob("*_complete.json"))]
    atomic(
        root / "physics_completed.json",
        {
            "status": "COMPLETE" if len(complete) == 333 else "INCOMPLETE",
            "registered_parents": 333,
            "registered_checkpoints": 666,
            "completed_parents": len(complete),
            "fully_completed_seed_parents": [p["group"] for p in complete],
            "attempted_parents": len(attempts),
            "untouched_parents": [
                p["group"]
                for p in manifest
                if p["group"] not in {s["group"] for s in attempts}
            ],
            "chunks": len(chunks),
            "cumulative_physics_wall_seconds": sum(c["wall_seconds"] for c in chunks),
            "chunk_cpu_seconds_sum": sum(c["cpu_seconds"] or 0 for c in chunks),
            "cpu_complete": all(
                c["cpu_seconds"] is not None
                and not c.get("cpu_is_last_checkpoint_lower_bound", False)
                for c in chunks
            ),
            "stop_reason": "COHORT_EXHAUSTED"
            if len(attempts) == 333
            else read(root / "study_halt.json")
            if (root / "study_halt.json").exists()
            else read(root / "physics_boundary.json")
            if (root / "physics_boundary.json").exists()
            else "OPERATIONAL_BOUNDARY_RECORDED",
            "new_fits": 0,
            "new_controllers": 0,
            "native_snapshot_restores": 0,
            "workers": [],
        },
    )
    print(json.dumps(read(root / "physics_completed.json")), flush=True)


def seal(root):
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert read(root / "validation.json")["status"] == "PASS"
        audit(root)
        gate = read(root / "scientific_gate.json")
        gate["PAPER_DRAFT_READY"] = (
            read(root / "final_audit.json")["format"]["status"] == "PASS"
        )
        gate["remaining_campaign_workers"] = []
        atomic(root / "scientific_gate.json", gate)
        files = maintained(root)
        names = [str(p) for p in files]
        assert (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", *names],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
        assert not subprocess.check_output(
            ["git", "diff", "HEAD", "--", *names], text=True
        )
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        reconciled_validation_failures(root, jobs)
        physical = read(root / "physics_completed.json")
        initial = read(root / "initial.json")
        resources = {
            "wall_seconds": time.time() - initial["started_epoch"],
            "session_wall_ceiling_seconds": 28800,
            "new_physics_cumulative_wall_seconds": physical[
                "cumulative_physics_wall_seconds"
            ],
            "new_physics_wall_ceiling_seconds": 10800,
            "independent_chunk_physics_cpu_seconds": physical["chunk_cpu_seconds_sum"],
            "all_completed_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "cpu_accounting_complete": physical["cpu_complete"],
            "manual_orchestration_cpu_allowance_seconds": 600,
            "old_interrupted_CPU_gap": "Preserved in earlier seal; not imputed or merged into new measured CPU",
            "new_model_fits": 0,
            "reused_fixed_CART_trees": 8,
            "gpu_training_seconds": 0,
            "paid_API_calls": 0,
            "physics_status": physical["status"],
            "new_primary_parent_count": physical["completed_parents"],
            "new_completed_primary_action_continuations": 4
            * physical["completed_parents"],
            "conservative_reused_toolchain_cache_bytes": byte_size(
                Path("/home/imad/.cache/tectonic")
            ),
            "maintained_bytes": sum(byte_size(p) for p in files),
            "workers": [],
            "artifact_budget_bytes": 1000000000,
        }
        resources["new_evidence_bytes_before_archive"] = byte_size(root)
        assert (
            resources["wall_seconds"] < 28800
            and resources["new_physics_cumulative_wall_seconds"] <= 10800
        )
        atomic(root / "resources.json", resources)
        archive = root / "supervisor_review.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            for path in files:
                stream.add(path, arcname=str(path))
            for path in sorted(root.iterdir()):
                if (
                    path.is_file()
                    and path.suffix in (".json", ".md", ".txt")
                    and path.name not in ("suffix_prediction_records.json",)
                ):
                    stream.add(path, arcname="evidence/" + path.name)
            stream.add(root / "commands.jsonl", arcname="evidence/commands.jsonl")
            stream.add(
                root / "validation.log",
                arcname="evidence/validation_attempts/first.log",
            )
            for directory in (
                "chunks",
                "template",
                "paper_versions",
                "validation_attempts",
            ):
                for path in sorted((root / directory).glob("*.json")):
                    stream.add(path, arcname=f"evidence/{directory}/{path.name}")
        resources["review_archive_bytes"] = byte_size(archive)
        resources[
            "conservative_total_new_artifact_bytes_with_11MB_transient_and_seal_allowance"
        ] = (
            byte_size(root)
            + resources["maintained_bytes"]
            + resources["conservative_reused_toolchain_cache_bytes"]
            + 11_000_000
        )
        assert (
            resources[
                "conservative_total_new_artifact_bytes_with_11MB_transient_and_seal_allowance"
            ]
            < 1000000000
        )
        atomic(root / "resources.json", resources)
        manifest = {
            "status": "COMPLETE_AUTHORIZED_FOLLOWUP"
            if physical["status"] == "COMPLETE"
            else "COMPLETE_CONDITIONAL_WORK_FOLLOWUP_INCOMPLETE",
            "branch": git("branch", "--show-current"),
            "commit": git("rev-parse", "HEAD"),
            "files": {
                str(p.relative_to(root)): sha(p)
                for p in root.rglob("*")
                if p.is_file() and p.name != "completion_manifest.json"
            },
            "maintained_files": {str(p): sha(p) for p in files},
            "preservation": preservation(root),
            "resources": resources,
            "archive": str(archive),
            "archive_sha256": sha(archive),
            "archive_bytes": byte_size(archive),
            "archive_accounting_scope": "Pre-archive accounting; outer manifest carries final size",
            "scientific_gate": read(root / "scientific_gate.json"),
            "workers": [],
            "no_push_upload_submission": True,
        }
        atomic(root / "completion_manifest.json", manifest)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "commit": manifest["commit"],
                    "archive": str(archive),
                    "wall_seconds": resources["wall_seconds"],
                    "physics_wall_seconds": resources[
                        "new_physics_cumulative_wall_seconds"
                    ],
                    "workers": [],
                }
            ),
            flush=True,
        )


def verify(root):
    manifest = read(root / "completion_manifest.json")
    for name, expected in manifest["files"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["maintained_files"].items():
        assert sha(Path(name)) == expected, name
    keep = preservation(root)
    assert not workers(root)
    print(
        json.dumps(
            {
                "status": "PASS",
                "sealed_members": len(manifest["files"]),
                "historical_preservation": keep,
                "commit": manifest["commit"],
                "new_evidence_bytes_including_seal": byte_size(root),
                "workers": [],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("finalize_physics", "validate", "audit", "seal", "verify"),
        required=True,
    )
    args = parser.parse_args()
    if args.stage != "verify" and (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    actions = {
        "finalize_physics": finalize_physics,
        "validate": validate,
        "audit": audit,
        "seal": seal,
        "verify": verify,
    }
    actions[args.stage](args.root)
