"""Validate, audit, package and seal the conditional DSRE paper/evidence campaign."""

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import tarfile
import time
from pathlib import Path

import psutil


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def maintained():
    return [
        Path("config/dsre_rss2027.json"),
        *sorted(Path("scripts").glob("dsre_paper_*.py")),
        Path("tests/test_dsre_paper.py"),
        *sorted(Path("rss2027").glob("*.tex")),
        Path("rss2027/references.bib"),
        Path("rss2027/IEEEtran.cls"),
        Path("rss2027/dsre_stage1.pdf"),
        *sorted(Path("rss2027").glob("*.md")),
        *sorted(Path("rss2027/figures").glob("*.pdf")),
        *sorted(Path("rss2027/figures").glob("*.png")),
        Path("docs/DSRE_RSS2027_STRENGTHENED_RESULTS.md"),
        Path("docs/DSRE_RSS2027_REVIEWER_CRITIQUE.md"),
    ]


def workers(root):
    me = psutil.Process()
    excluded = {me.pid, *[p.pid for p in me.parents()]}
    found = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if (
                process.pid not in excluded
                and str(root) in args
                and any(
                    Path(a).name.startswith("dsre_paper_")
                    or Path(a).name == "reboot_overnight_worker.py"
                    for a in args
                )
            ):
                found.append(process.pid)
        except psutil.Error:
            pass
    return found


def preservation(root):
    initial = load(root / "initial.json")
    result = {}
    for category in ("prior_files", "historical_seals", "prior_run_members"):
        for name, expected in initial[category].items():
            p = Path(name)
            assert (sha(p) if p.is_file() else None) == expected, name
        result[category] = len(initial[category])
    frozen = load(root / "confirmation_freeze.json")
    amendment = load(root / "post_execution_source_amendment.json")
    for kind in ("source_sha256", "input_sha256"):
        for name, expected in frozen[kind].items():
            p = Path(name)
            if name == "scripts/dsre_paper_physics.py":
                old = Path(amendment["frozen_source_copy"])
                assert sha(old) == expected == amendment["before_sha256"]
                before = old.read_text()
                changed = before.replace(
                    'logging.exception("Prospective physics stopped; preserve completed parents")',
                    'logging.getLogger(__name__).exception(\n            "Prospective physics stopped; preserve completed parents"\n        )',
                )
                assert p.read_text() == changed and sha(p) == amendment["after_sha256"]
            else:
                assert sha(p) == expected, name
    result["frozen_pins"] = sum(
        len(frozen[k]) for k in ("source_sha256", "input_sha256")
    )
    result["logging_only_post_execution_amendment_verified"] = True
    return result


def validate(root):
    checks = []
    for argv in (
        ["uv", "run", "--no-sync", "pytest", "-q", "tests/test_dsre_paper.py"],
        ["uv", "run", "--no-sync", "pytest", "-q", "tests"],
        ["uv", "run", "--no-sync", "ruff", "check", "src", "scripts", "tests"],
        [
            "uv",
            "run",
            "--no-sync",
            "ruff",
            "format",
            "--check",
            "src",
            "scripts",
            "tests",
        ],
        ["git", "diff", "--check"],
    ):
        before = time.monotonic()
        result = subprocess.run(
            argv, text=True, capture_output=True, timeout=300, check=False
        )
        checks.append(
            {
                "command": argv,
                "exit_status": result.returncode,
                "wall_seconds": time.monotonic() - before,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        save(
            root / "validation.json",
            {
                "status": "PASS"
                if all(x["exit_status"] == 0 for x in checks)
                else "FAIL",
                "checks": checks,
            },
        )
        assert not result.returncode, (argv, result.stdout, result.stderr)
    print(
        json.dumps({"status": "PASS", "validation_commands": len(checks)}), flush=True
    )


def claims(root):
    paper = Path("rss2027/dsre_stage1.tex").read_text()
    reused = load(root / "reused_stratified_tables.json")
    fresh = load(root / "fresh_stratified_tables.json")
    count = 0
    for budget in range(4):
        row = reused[f"PickCube-v1|{budget}|DSRE|all"]
        failed = reused[f"PickCube-v1|{budget}|DSRE|initial_failure"]
        finite = load(root / "reused_finite_ceiling.json")[f"PickCube-v1|{budget}"][
            "mass"
        ]
        text = f"{budget} & {finite} & {row['recommended']} / {row['successful']} / {row['unacceptable']} & {failed['recommended']} / {failed['successful']} / {failed['unacceptable']}"
        assert text in paper, text
        count += 8
    for task, name in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
        for budget in (0, 1):
            row = fresh[f"{task}|{budget}|DSRE|all"]
            failed = fresh[f"{task}|{budget}|DSRE|initial_failure"]
            text = f"{name} & {budget} & {row['recommended']} / {row['successful']} / {row['unacceptable']} & {failed['successful']} / {failed['checkpoints']}"
            assert text in paper, text
            count += 7
    old_ci = load(root / "reused_paired_intervals.json")["PickCube-v1|b1-b0|all"]
    new_ci = load(root / "fresh_paired_intervals.json")["PickCube-v1|all"]["difference"]
    for ci in (old_ci, new_ci):
        text = f"[{ci['parent_percentile95'][0] * 100:.2f},{ci['parent_percentile95'][1] * 100:.2f}]"
        assert text in paper, text
        count += 3
    baseline = load(root / "fresh_strong_baseline_intervals.json")[
        "PickCube-v1|1|DSRE-CART2_beta10|all"
    ]["difference"]
    assert (
        f"[{baseline['parent_percentile95'][0] * 100:.2f},{baseline['parent_percentile95'][1] * 100:.2f}]"
        in paper
    )
    for task in ("PickCube-v1", "PushCube-v1"):
        for budget in (0, 1):
            assert (
                fresh[f"{task}|{budget}|DSRE|all"]["successful"]
                == fresh[f"{task}|{budget}|CART2_strict|all"]["successful"]
            )
    rows = load(root / "fresh_prediction_records.json")
    lookup = {(r["id"], r["budget"], r["method"]): r for r in rows}
    same = 0
    for row in rows:
        if row["method"] == "DSRE":
            assert (
                row["action"]
                == lookup[row["id"], row["budget"], "CART2_strict"]["action"]
            )
            assert row["action"] == lookup[row["id"], row["budget"], "B7"]["action"]
            same += 1
    assert (
        same == 264
        and load(root / "reused_independent_audit.json")["B7_equal_views"] == 16880
    )
    audit = load(root / "fresh_independent_audit.json")
    assert (
        audit["status"] == "PASS"
        and audit["qualified_checkpoint_traces_audited"] == 133
    )
    assert (
        audit["outcome_actions_audited"] == 18620
        and audit["prefix_states_audited"] == 18962
        and audit["maximum_action_error"] == 0
    )
    missing = load(root / "fresh_missingness.json")
    assert (
        len(missing["missing_checkpoints"]) == 667
        and missing["fully_completed_parents"] == 66
        and len(missing["qualified_orphan_conditions"]) == 1
    )
    assert (
        load(root / "paper_versions/first_complete.json")[
            "physics_finished_at_first_complete_draft"
        ]
        is False
    )
    for required in ("neither", "UNKNOWN", "NOT_CALIBRATED", "B7", "calibration"):
        assert (
            required.lower()
            in (paper + Path("rss2027/CLAIM_EVIDENCE_LEDGER.md").read_text()).lower()
        )
    assert "no fresh outcome result is claimed" not in paper.lower()
    return {
        "checked_numeric_table_and_interval_fields": count,
        "per_ID_fresh_DSRE_CART2_and_B7_equal_decisions": same,
        "status": "PASS",
        "claim_categories": [
            "theoretical_identity",
            "finite_reference",
            "exploratory_cross_fit",
            "incomplete_fresh_subset",
        ],
        "deployment": "NOT_CALIBRATED",
    }


def format_audit(root):
    pdf = Path("rss2027/dsre_stage1.pdf")
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    font_output = subprocess.check_output(["pdffonts", str(pdf)], text=True)
    assert re.search(r"Pages:\s+6\b", info)
    pages = [p for p in text.split("\f") if p.strip()]
    assert len(pages) == 6 and "REFERENCES" in pages[5].replace(" ", "").upper()
    assert all(len(p.split()) > 150 for p in pages[:5])
    for forbidden in (
        "imad",
        "/home/",
        "IEEE-RAL",
        "github.com",
        "http://",
        "https://",
        "acknowledgment",
        "acknowledgement",
    ):
        assert forbidden.lower() not in (info + text).lower(), forbidden
    assert not re.search(r"^Author:\s*\S", info, re.MULTILINE)
    fonts = font_output.splitlines()[2:]
    assert fonts and all(
        "Type 1" in line and line.split()[-5] == "yes" for line in fonts
    )
    assert (
        sha(Path("rss2027/IEEEtran.cls"))
        == load(root / "template/provenance.json")["class_sha256"]
    )
    source = Path("rss2027/dsre_stage1.tex").read_text()
    for forbidden in (
        "\\geometry",
        "\\textheight",
        "\\textwidth=",
        "\\baselinestretch",
        "\\vspace{-",
        "\\small",
        "\\scriptsize",
    ):
        assert forbidden not in source, forbidden
    log = (root / "paper_compile.log").read_text()
    assert "Overfull" not in log and "unrecoverable error" not in log
    result = {
        "status": "PASS",
        "pages": 6,
        "content_pages": 5,
        "reference_pages": 1,
        "official_class_unmodified": True,
        "font_records": len(fonts),
        "all_fonts_embedded_type1": True,
        "anonymous_metadata_and_text": True,
        "page_word_counts": [len(p.split()) for p in pages],
        "pdf_sha256": sha(pdf),
        "no_overfull_boxes": True,
        "minor_underfull_line_warnings": "Retained; no template spacing changes.",
    }
    (root / "paper_pdfinfo.txt").write_text(info)
    (root / "paper_pdffonts.txt").write_text(font_output)
    save(root / "paper_format_audit.json", result)
    return result


def audit(root):
    assert not workers(root), workers(root)
    result = {
        "status": "PASS",
        "preservation": preservation(root),
        "claims": claims(root),
        "format": format_audit(root),
        "workers": workers(root),
        "physics": "INCOMPLETE_RUNTIME_STOP_AVAILABLE_DATA_AUDITED",
        "review": "Same-session adversarial review and independent implementations; not external human replication.",
    }
    save(root / "final_independent_audit.json", result)
    print(
        json.dumps(
            {
                "status": "PASS",
                "prior_members": result["preservation"]["prior_run_members"],
                "pages": 6,
                "workers": [],
            }
        ),
        flush=True,
    )


def byte_size(path):
    if path.is_file():
        return path.stat().st_size
    return (
        sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
        if path.exists()
        else 0
    )


def seal(root):
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert load(root / "validation.json")["status"] == "PASS"
        audit(root)
        initial = load(root / "initial.json")
        jobs = [
            json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
        ]
        assert all(j["exit_status"] == 0 for j in jobs)
        interrupted = load(root / "physics_interruption.json")
        extras = [
            Path("/tmp/tectonic-rss2027.tar.gz"),
            Path("/tmp/tectonic-rss2027-bin"),
            Path("/tmp/rss2027-official-template.tar.gz"),
            Path("/tmp/rss2027-template-inspect"),
            Path("/home/imad/.cache/tectonic"),
        ]
        for pattern in (
            "dsre_paper*",
            "dsre-paper-*",
            "dsre_first_paper*",
            "dsre_times_paper*",
            "dsre_page*.png",
            "dsre_final_page*.png",
            "dsre_check_score.py",
            "tectonic*",
            "rss2027*",
        ):
            extras.extend(Path("/tmp").glob(pattern))
        extras = sorted(set(extras))
        resources = {
            "wall_seconds": time.time() - initial["started_epoch"],
            "session_wall_ceiling_seconds": 28800,
            "physics_wall_observed_upper_bound_seconds": interrupted[
                "wall_seconds_at_observed_absence_upper_bound"
            ],
            "physics_last_completed_trace_elapsed_seconds": interrupted[
                "last_qualified_trace_elapsed_lower_bound"
            ],
            "physics_wall_ceiling_seconds": 10800,
            "completed_worker_measured_cpu_seconds": sum(
                j["cpu_seconds"] for j in jobs
            ),
            "last_independently_metered_reanalysis_cpu_seconds": load(
                root / "reused_independent_audit.json"
            )["cpu_seconds"],
            "unmetered_orchestration_cpu_allowance_seconds": 600,
            "interrupted_physics_cpu_seconds": None,
            "cpu_accounting_status": "INCOMPLETE: terminated wrapper did not finalize rusage; no measured value imputed",
            "self_imposed_cpu_guard_seconds": initial["limits"]["cpu_seconds"],
            "self_imposed_cpu_guard_compliance": "Not independently verifiable for interrupted physics",
            "worker_peak_rss_kib": max(j["max_rss_kib"] for j in jobs),
            "peak_rss_scope": "Completed ledger jobs only; interrupted physics peak unavailable",
            "additional_external_toolchain_bytes": {
                str(p): byte_size(p) for p in extras
            },
            "maintained_artifact_bytes": sum(byte_size(p) for p in maintained()),
            "unlisted_transient_artifact_allowance_bytes": 10_000_000,
            "gpu_training_seconds": 0,
            "paid_api_calls": 0,
            "new_small_tree_fits": 8,
            "completed_physical_action_continuations": 266,
            "primary_complete_parent_action_continuations": 264,
            "qualified_checkpoints": 133,
            "complete_primary_seed_parents": 66,
            "incomplete_parent_count": 1,
            "not_started_parent_count": 333,
            "physics_relaunched_after_failure": False,
            "remaining_campaign_workers": [],
        }
        resources["evidence_bytes_before_archive"] = byte_size(root)
        resources["new_bytes_before_archive_conservative"] = (
            resources["evidence_bytes_before_archive"]
            + sum(resources["additional_external_toolchain_bytes"].values())
            + resources["maintained_artifact_bytes"]
        )
        assert (
            resources["wall_seconds"] < 28800
            and resources["physics_wall_observed_upper_bound_seconds"] < 10800
        )
        assert resources["new_bytes_before_archive_conservative"] < 950_000_000
        save(root / "resources.json", resources)
        tracked = {str(p): sha(p) for p in maintained()}
        assert (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", *tracked],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        ), "Commit every scoped deliverable before sealing"
        assert not subprocess.check_output(
            ["git", "diff", "HEAD", "--", *tracked], text=True
        ), "Scoped work must be committed before sealing"
        commit = git("rev-parse", "HEAD")
        save(
            root / "review_status.json",
            {
                "PAPER_DRAFT_READY": True,
                "FRESH_EVIDENCE_INCOMPLETE": True,
                "RSS_STAGE1_RESEARCH_READINESS": "NOT_ESTABLISHED_FOR_STRONG_SUBMISSION",
                "branch": git("branch", "--show-current"),
                "commit": commit,
                "workers": [],
                "no_submission_or_push": True,
            },
        )
        archive = root / "supervisor_review.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            for path in maintained():
                stream.add(path, arcname=str(path))
            for path in sorted(root.iterdir()):
                if (
                    path.is_file()
                    and path.suffix in (".json", ".md", ".txt")
                    and path.name
                    not in (
                        "fresh_prediction_records.json",
                        "reused_prediction_records.json",
                    )
                ):
                    stream.add(path, arcname="evidence/" + path.name)
            stream.add(
                root / "preregistration.md",
                arcname="evidence/preregistration_original.md",
            )
            stream.add(
                root / "paper_versions/first_complete.json",
                arcname="evidence/first_complete_draft_status.json",
            )
            for path in (root / "template").iterdir():
                if path.is_file():
                    stream.add(path, arcname="evidence/template/" + path.name)
        resources["review_archive_bytes"] = byte_size(archive)
        resources["final_additional_artifact_bytes_conservative"] = (
            byte_size(root)
            + sum(resources["additional_external_toolchain_bytes"].values())
            + resources["maintained_artifact_bytes"]
            + 1_000_000
            + resources["unlisted_transient_artifact_allowance_bytes"]
        )
        resources["seal_metadata_allowance_bytes"] = 1_000_000
        assert resources["final_additional_artifact_bytes_conservative"] < 1_000_000_000
        save(root / "resources.json", resources)
        # The archive has pre-archive accounting; the outer seal carries final sizes.
        members = {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and p.name != "completion_manifest.json"
        }
        manifest = {
            "status": "AUTHORIZED_CONDITIONAL_WORK_COMPLETE_PHYSICS_INCOMPLETE",
            "branch": git("branch", "--show-current"),
            "commit": commit,
            "paper_status": "PAPER_DRAFT_READY",
            "fresh_status": "FRESH_EVIDENCE_INCOMPLETE",
            "research_readiness": "NOT_ESTABLISHED_FOR_STRONG_SUBMISSION",
            "files": members,
            "maintained_files": tracked,
            "archive": str(archive),
            "archive_sha256": sha(archive),
            "archive_bytes": byte_size(archive),
            "archive_resources_scope": "Pre-archive accounting; final size and seal-metadata allowance are in the outer manifest",
            "resources": resources,
            "preservation": preservation(root),
            "workers": workers(root),
            "no_push_or_submission": True,
        }
        save(root / "completion_manifest.json", manifest)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "commit": commit,
                    "archive": str(archive),
                    "new_bytes": resources[
                        "final_additional_artifact_bytes_conservative"
                    ],
                    "wall_seconds": resources["wall_seconds"],
                    "workers": [],
                }
            ),
            flush=True,
        )


def verify(root):
    manifest = load(root / "completion_manifest.json")
    for name, expected in manifest["files"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["maintained_files"].items():
        assert sha(Path(name)) == expected, name
    preserved = preservation(root)
    assert not workers(root)
    actual_bytes = (
        byte_size(root)
        + sum(manifest["resources"]["additional_external_toolchain_bytes"].values())
        + sum(byte_size(Path(n)) for n in manifest["maintained_files"])
    )
    assert actual_bytes < 1_000_000_000
    print(
        json.dumps(
            {
                "status": "PASS",
                "sealed_members": len(manifest["files"]),
                "maintained_members": len(manifest["maintained_files"]),
                "preservation": preserved,
                "commit": manifest["commit"],
                "workers": [],
                "actual_additional_artifact_bytes": actual_bytes,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("validate", "audit", "seal", "verify"), required=True
    )
    args = parser.parse_args()
    if args.stage != "verify" and (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    globals()[args.stage](args.root)
