"""Reproducible audits, scientific readiness and immutable final-evidence package."""

import argparse
import json
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

from dsre_final_audit import corrupted_raw, numerical, preservation, sensitivity
from dsre_final_verify import verify_sources
from dsre_followup_batch import atomic, read, sha
from dsre_operational_finish import format_full, workers
from dsre_paper_finish import byte_size, format_audit, validate


def maintained(root):
    return [
        *[Path(p) for p in read(root / "initial.json")["authorized_updates"]],
        Path("config/dsre_final_sprint.json"),
        *sorted(Path("scripts").glob("dsre_final_*.py")),
        Path("tests/test_dsre_final_execution.py"),
        *[
            Path("docs") / name
            for name in (
                "DSRE_FINAL_SPRINT_PREREGISTRATION.md",
                "DSRE_FINAL_OPERATIONAL_RESULTS.md",
                "DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md",
                "DSRE_RSS2027_SUBMISSION_READINESS.md",
            )
        ],
        *[
            Path("rss2027/figures") / name
            for name in (
                "final_operational.pdf",
                "final_operational.png",
                "final_robustness.pdf",
                "final_robustness.png",
            )
        ],
        Path("rss2027/IEEEtran.cls"),
        Path("rss2027/operational_references.bib"),
        Path("rss2027/figures/frontier.png"),
        Path("rss2027/figures/frontier.pdf"),
    ]


def paper_claims(root):
    from dsre_final_report import row

    r = read(root / "operational_results.json")
    cal = read(root / "calibration_decision.json")
    records = read(root / "test_records.json")
    checked = 0
    for filename in ("rss2027/dsre_stage1.tex", "rss2027/dsre_full_paper_master.tex"):
        text = Path(filename).read_text()
        assert f"{r['complete_parents']}/159" in text and "79" in text and "80" in text
        assert "160" in text and "excluded" in text and "B7" in text
        for method, label in (
            ("DSRE_strict", "Strict DSRE"),
            ("DSRE_risk", "Risk tier"),
            ("B7_risk", "Ordinary risk"),
            ("CART1_beta10", "CART1 .9"),
            ("CART2_beta10", "CART2 .9"),
            ("B5_beta10", "B5 .10"),
            ("B0_continue", "Always continue"),
            ("B0_recover", "Always recover"),
        ):
            values = [
                row(r["tables"], task, method)
                for task in ("PickCube-v1", "PushCube-v1")
            ]
            expected = (
                label
                + " & "
                + " & ".join(
                    f"{v['successful']}/{v['unacceptable']}/{v['deferred']}"
                    for v in values
                )
            )
            assert expected in text, (filename, expected)
            checked += 6
        for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
            counts = "/".join(
                str(row(r["tables"], task, pop=p)["checkpoints"])
                for p in ("continue_only", "recover_only", "both", "neither")
            )
            data = [
                v
                for v in records
                if v["task"] == task
                and v["method"] == "DSRE_risk"
                and v["mode"] == "calibrated"
            ]
            value = row(r["tables"], task)
            maintained_continue = sum(
                v["successful"] and v["initial_success"] and v["action"] == "continue"
                for v in data
            )
            other = (
                value["successful"]
                - maintained_continue
                - value["required_recovery_success"]
            )
            partition = f"{maintained_continue} & {value['required_recovery_success']} & {other} & {value['unacceptable']}/{value['deferred']}"
            assert partition in text and counts in text, (filename, task, partition)
            checked += 9
            for action, short in (("continue", "C"), ("recover", "R")):
                b = cal["strata"][f"DSRE_risk|{task}|{action}"]
                expected = f"{label} & {short} & {b['assigned_parents']}/{b['error_parents']} & {100 * b['upper']:.2f}\\% & {'on' if b['enabled'] else 'NC'}"
                assert expected in text, (filename, expected)
                checked += 4
            for other in ("DSRE_strict", "CART2_beta10"):
                value = r["paired_intervals"][f"{task}|DSRE_risk-{other}|all"][
                    "successful"
                ]
                if value:
                    lo, hi = value["parent_percentile95"]
                    assert f"[{100 * lo:.2f},{100 * hi:.2f}]" in text
                    assert f"{100 * value['value']:+.2f}" in text
                    checked += 3
        for term in (
            "tab:primarydecomp",
            "conditional",
            "STOP",
            "finite",
            "calibration",
            "idealized",
            "recovery",
        ):
            assert term.lower() in text.lower(), term
        assert "currently being collected" not in text and "PLANNED" not in text
    return {
        "status": "PASS",
        "count_and_interval_fields_checked": checked,
        "actual_postmortem_exclusion_and_no_trial_inflation": True,
    }


def figure_claims(root):
    from dsre_final_report import row

    tables = read(root / "operational_results.json")["tables"]
    robust = read(root / "heldout_robustness.json")["parent_intervals"]
    data = read(root / "figure_data.json")
    count = 0
    for p in data["operational"]:
        r = row(tables, p["task"], p["method"])
        expected = (
            r["failed_start_success"] - r["required_recovery_success"]
            if p["field"] == "other"
            else r[p["field"]]
        )
        assert p["N"] == r["checkpoints"] and p["count"] == expected
        assert p["percent"] == 100 * expected / r["checkpoints"]
        count += 1
    for p in data["sensitivity"]:
        r = robust[f"{p['task']}|{p['method']}|proposal|{p['scenario']}|all"]
        assert (
            p["good"] == 100 * r["successful"]["value"]
            and p["bad"] == 100 * r["unacceptable"]["value"]
        )
        assert (
            p["low"] == 100 * r["successful"]["parent_percentile95"][0]
            and p["high"] == 100 * r["successful"]["parent_percentile95"][1]
        )
        count += 1
    return {
        "status": "PASS",
        "plotted_points_independently_checked": count,
        "tables_and_parent_intervals_separately_audited": True,
    }


def audit(root):
    assert not workers(root)
    verify_sources(root)
    jobs = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    engineering_failures = []
    for job in jobs:
        assert sha(root / (job["name"] + ".log")) == job["log_sha256"]
        if job["exit_status"]:
            assert job["exit_status"] == 1
            log = (root / (job["name"] + ".log")).read_text()
            if job["name"] == "presentation":
                assert "ModuleNotFoundError: No module named 'dsre_final_report'" in log
                cause = "Wrapper omits scripts from PYTHONPATH; corrected invocation adds scripts before imports"
            else:
                assert job["name"] == "validation"
                failed = read(root / "validation_initial_failure.json")
                assert failed["status"] == "FAIL"
                assert "2 failed, 514 passed, 4 skipped" in log
                assert "No module named 'dsre_final_analysis'" in log
                assert "No module named 'dsre_final_batch'" in log
                assert (
                    sha(root / "validation_initial_test_source.py")
                    == job["source_sha256"]["tests/test_dsre_final_execution.py"]
                )
                cause = "Two test entrypoint imports lacked a scripts path outside their fixture; fixed shared path fixture, unchanged assertions"
            engineering_failures.append(
                {
                    "job": job["name"],
                    "exit_status": 1,
                    "cause": cause,
                    "new_scientific_or_physics_collection": False,
                    "preserved_log_sha256": job["log_sha256"],
                }
            )
        freeze = read(
            root
            / (
                "qualification_freeze.json"
                if job["name"] == "physics_p0"
                else "confirmation_freeze.json"
            )
        )
        for name, expected in freeze["source_sha256"].items():
            assert job["source_sha256"].get(name) == expected, (job["name"], name)
    from dsre_operational_finish import robustness_oracle_audit

    output = {
        "status": "PASS",
        "preserved_engineering_failures": engineering_failures,
        "preservation": preservation(root),
        "numerical": numerical(root),
        "sensitivity": sensitivity(root),
        "new_raw_corruption": corrupted_raw(root),
        "historical_raw_corruption": robustness_oracle_audit(
            Path(read(root / "initial.json")["prior_root"])
        ),
        "paper_claims": paper_claims(root),
        "figure_claims": figure_claims(root),
        "stage1_format": format_audit(root),
        "master_format": format_full(root),
        "workers": [],
        "scope": "Separate same-session equations, raw-state verifiers, direct tree/bitset oracle and numerical implementations; not external human replication",
    }
    outputs = [
        "operational_results.json",
        "test_records.json",
        "independent_audit.json",
        "test_assignment_errors.json",
        "historical_robustness.json",
        "heldout_robustness.json",
        "heldout_corruption_records.json",
        "physical_examples.json",
        "breadth_feasibility.json",
        "validation.json",
        "figure_data.json",
    ]
    output["input_sha256"] = {
        str(p): sha(p) for p in [*maintained(root), *[root / name for name in outputs]]
    }
    atomic(root / "final_audit.json", output)
    print(
        json.dumps(
            {
                "status": "PASS",
                "complete_test_parents": read(root / "operational_results.json")[
                    "complete_parents"
                ],
                "stage1_pages": 6,
                "master_pages": output["master_format"]["total_pages"],
            }
        ),
        flush=True,
    )


def readiness(root):
    r = read(root / "operational_results.json")
    stage_format = format_audit(root)
    master_format = format_full(root)
    validation = read(root / "validation.json")
    assert validation["status"] == "PASS" and len(validation["checks"]) == 5
    full_tests = validation["checks"][1]["stdout"].strip().splitlines()[-1]
    jobs = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    physical = sum(j["wall_seconds"] for j in jobs if j["name"].startswith("physics_"))
    lines = [
        "# DSRE RSS2027: submission-readiness assessment",
        "",
        f"Branch: `research/dsre-rss2027-final-evidence`; reviewed starting commit `873556b54ce9f783326ee2c08bd0303447ed041d`. Evidence `{root}`. The exact final local commit SHA and final resource totals are in the linked completion_manifest.json; embedding a commit's own SHA into its tracked contents would be circular.",
        "",
        "## Method",
        "",
        "The robot-intervention information contract is fully scoped: fixed two skills/horizon, minimum observable adequate-action facts, explicit observation/repertoire/reference witnesses, original statistical gate and STOP semantics. Exact B7 and ordinary capped-risk equivalences remain; no new solver, calibration theorem, controller or user-trust benefit is claimed. Existing sufficient explanations, robust action intersection and selective classification are acknowledged.",
        "",
        "## Evidence",
        "",
        f"Actual continuation: {r['complete_parents']}/{r['planned_parents']} untouched parents; {r['checkpoints']} primary paired checkpoints. Original contaminated 8000180 is retained/excluded, not rerun or replaced; this is a disclosed deviation from the original 160, not 160 pristine trials. P0 validates the repaired executor on inspected states before collection. Raw action/prefix/model/memory/source and selected-future evidence is independently checked. No test tuning or new fits.",
        "",
        "The independent calibration is unchanged: Pick continue 180/1 and Push recover 180/1 each have global parent-any-error upper 5.194%; Pick recover 13/0 upper 42.594% remains NOT CERTIFIED; Push continue unassigned. Observed test errors never recertify rare strata or change eligibility. Matched ordinary controls and every four-category/initial-state decomposition are in DSRE_FINAL_OPERATIONAL_RESULTS.md. Completion credit counts STOP as zero, even on already-successful checkpoints; maintenance is not new physical recovery.",
        "",
        "Fixed-grid corruption is offline sensitivity against actual unchanged physical labels; historical 333-parent and new held-out populations are separate. Noise repetitions and conditions are not independent parents. Clean confidence does not transfer to corrupted sensors. The optional breadth result and source gate are explicit in DSRE_FINAL_ROBUSTNESS_AND_BREADTH.md.",
        "",
        "## Paper and blind checks",
        "",
        f"The compiled master has {master_format['content_pages']} content pages plus one references page ({master_format['total_pages']} total); Stage 1 has {stage_format['content_pages']} content pages plus one references page ({stage_format['pages']} total). Text, metadata, embedded Type1 fonts, unchanged official class and no-overfull checks pass. Final numerical claims and plotted values are separately audited in final_audit.json; page evidence is in paper_format_audit.json and page_checks/. The official 2027 CFP was reverified live: Stage 1 December 4, 2026 23:59 AoE; invited final April 16, 2027. No external appendix or website evidence is assumed available to Stage 1 reviewers. All 13 existing bibliography items were checked in primary records; preprints are labeled, no invented acceptance venues.",
        "",
        f"Validation: {full_tests}. The focused paper tests, maintained-source Ruff check/format and Git diff check also pass. The initial validation import failure is preserved in validation_initial_failure.json and its original test source; adding the shared script-path fixture changes no test assertions or scientific sources. A presentation import failure is likewise retained with its corrected invocation in commands.jsonl.",
        "",
        "CFP: https://roboticsconference.org/information/cfp/ . Primary metadata and exact class/bibliography hashes: cfp_verification.json, citation_verification.json and template/provenance.json.",
        "",
        "## Strongest remaining objections and Stage2 plan",
        "",
        "The strongest objection is method distinctiveness: an ordinary rule/tree/constant may achieve the same measured operating point under the same risk standard. This remains an intervention-grounded systems characterization, not algorithmic superiority. The other objection is scope: simple deterministic tasks, idealized observations, a scoring convention for STOP, rare unqualified recovery and absent distinct third-task validation limit broader robotics claims.",
        "",
        "If invited, retain the same research question and methodology. Prioritize a genuinely source-qualified existing third action pair with varying adequacy and an independent cohort; validate realistic predecision observations without privileged outcomes; and preregister a fixed independent rare-action calibration allocation. Pick recovery needs at least 56 additional error-free independent assignments merely to reach the global zero-error minimum 69; fixed sample planning must account for assignment rarity and possible errors. No sample-until-pass, pooling inspected test labels, new controller or alternative project is authorized by this plan.",
        "",
        "## Resources and preservation",
        "",
        f"At this report generation: physics {physical:.3f}/14400 seconds; measured worker CPU {sum(j['cpu_seconds'] for j in jobs):.3f}s; evidence {byte_size(root)}bytes. Final totals, measured peak worker RSS, conservative ancillary allowance, complete source/data hashes, archive hash, exact commit and worker status are recorded at sealing in completion_manifest.json/resources.json. Session ceiling 10 h, new artifacts 2 GB. No paid API, GPU training, new model fits or new controllers.",
        "",
        "Historical seals, failed attempts, old calibrated 360-parent study, 333-parent confirmation, .gitignore,uv.lock and unrelated user changes remain preserved. Raw traces/logs are sealed locally and excluded from the Git commit. No push, publication, author contact or conference submission.",
        "",
        "**Scientific decision:** method correctness, empirical completion and formal paper compliance are separate judgments. Actual evidence and weaknesses above require principal-researcher review; no publication readiness or acceptance guarantee is asserted.",
    ]
    Path("docs/DSRE_RSS2027_SUBMISSION_READINESS.md").write_text(
        "\n".join(lines) + "\n"
    )


def seal(root):
    assert not (root / "completion_manifest.json").exists()
    verify_sources(root)
    audit_result = read(root / "final_audit.json")
    assert audit_result["status"] == "PASS"
    for name, expected in audit_result["input_sha256"].items():
        assert sha(Path(name)) == expected, name
    assert not workers(root)
    paths = maintained(root)
    names = [str(p) for p in paths]
    assert (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", *names],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    assert not subprocess.check_output(["git", "diff", "HEAD", "--", *names])
    jobs = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    initial = read(root / "initial.json")
    r = read(root / "operational_results.json")
    resources = {
        "wall_seconds_to_seal": time.time() - initial["started_epoch"],
        "wall_ceiling_seconds": 36000,
        "physics_wall_seconds": sum(
            j["wall_seconds"] for j in jobs if j["name"].startswith("physics_")
        ),
        "physics_ceiling_seconds": 14400,
        "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
        "maximum_worker_rss_kib": max(j["max_rss_kib"] for j in jobs),
        "unmetered_orchestration_cpu_allowance_seconds": 900,
        "reserved_postseal_verification_wall_seconds": 900,
        "accounting_scope": "Measured bounded workers through seal; the CPU allowance also covers final read-only reproduction. Final wall is separately measured after reproduction.",
        "new_fits": 0,
        "new_controllers": 0,
        "gpu_training_seconds": 0,
        "paid_API_calls": 0,
        "complete_test_parents": r["complete_parents"],
        "qualified_primary_checkpoints": r["checkpoints"],
        "paired_test_action_continuations": 2 * r["checkpoints"],
        "selected_test_continuations": read(root / "independent_audit.json")["heldout"][
            "selected_executions"
        ],
        "qualification_both_action_replays": 8,
        "evidence_bytes_before_archive": byte_size(root),
        "workers": [],
    }
    cohort = {p["group"] for p in read(root / "fresh_seed_manifest.json")["parents"]}
    resources["qualification_selected_repeats"] = sum(
        read(p)["new_continuations"]
        for p in (root / "selected").glob("*/*/execution.json")
        if f"{p.parent.parent.name}/{p.parent.name.split('-')[0]}" not in cohort
    )
    resources["all_new_action_continuations"] = (
        resources["paired_test_action_continuations"]
        + resources["selected_test_continuations"]
        + 8
        + resources["qualification_selected_repeats"]
    )
    assert (
        resources["wall_seconds_to_seal"] + 900 < 36000
        and resources["physics_wall_seconds"] <= 14400
    )
    provenance = {
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "maintained_files": {str(p): sha(p) for p in paths},
        "resources_before_archive": resources.copy(),
        "scope": "Compact supervisor review with compilable paper sources. Raw traces remain in the sealed local root; numerical reproduction requires the preserved repository inputs. Final archive accounting is outside this archive in resources.json/completion_manifest.json.",
    }
    atomic(root / "package_provenance.json", provenance)
    atomic(root / "resources.json", resources)
    archive = root / "supervisor_review.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for p in paths:
            tar.add(p, arcname=str(p))
        tar.add(
            root / "qualification_prepare_source.py",
            arcname="evidence/qualification_prepare_source.py",
        )
        for p in sorted(root.iterdir()):
            if (
                p.is_file()
                and p.suffix in (".json", ".md", ".txt", ".jsonl")
                and not p.name.endswith("_records.json")
                and p.name not in ("calibration_records.json", "resources.json")
            ):
                tar.add(p, arcname="evidence/" + p.name)
    resources["archive_bytes"] = byte_size(archive)
    resources["conservative_new_artifact_bytes"] = (
        byte_size(root)
        + sum(byte_size(p) for p in paths)
        + byte_size(Path("/home/imad/.cache/tectonic"))
        + 11000000
    )
    assert resources["conservative_new_artifact_bytes"] < 2000000000
    atomic(root / "resources.json", resources)
    manifest = {
        "status": "COMPLETE_159_PARENT_FINAL_EVIDENCE"
        if r["complete_parents"] == 159
        else "COMPLETE_VALID_WORK_WITH_INCOMPLETE_TEST_COHORT",
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "files": {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and p.name != "completion_manifest.json"
        },
        "maintained_files": {str(p): sha(p) for p in paths},
        "archive": str(archive),
        "archive_sha256": sha(archive),
        "resources": resources,
        "workers": [],
        "no_push_publication_or_submission": True,
    }
    atomic(root / "completion_manifest.json", manifest)
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ("status", "commit", "archive", "archive_sha256", "workers")
            }
        ),
        flush=True,
    )


def verify(root):
    m = read(root / "completion_manifest.json")
    for name, expected in m["files"].items():
        assert sha(root / name) == expected, name
    for name, expected in m["maintained_files"].items():
        assert sha(Path(name)) == expected, name
    assert not workers(root)
    print(
        json.dumps(
            {
                "status": "PASS",
                "sealed_members": len(m["files"]),
                "commit": m["commit"],
                "workers": [],
            }
        ),
        flush=True,
    )


def reproduce(root):
    verify(root)
    scratch = Path(tempfile.mkdtemp(prefix="dsre-final-reproduction-"))
    outputs = {
        "final_audit.json",
        "paper_pdfinfo.txt",
        "paper_pdffonts.txt",
        "paper_format_audit.json",
    }
    for p in root.iterdir():
        if p.name not in outputs:
            (scratch / p.name).symlink_to(p.resolve(), target_is_directory=p.is_dir())
    audit(scratch)
    print(
        json.dumps(
            {
                "sealed_evidence_unchanged": str(root),
                "reproduced_audit": str(scratch / "final_audit.json"),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("validate", "readiness", "audit", "seal", "verify", "reproduce"),
        required=True,
    )
    args = parser.parse_args()
    {
        "validate": validate,
        "readiness": readiness,
        "audit": audit,
        "seal": seal,
        "verify": verify,
        "reproduce": reproduce,
    }[args.stage](args.root)
