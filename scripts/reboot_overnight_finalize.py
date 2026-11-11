"""Verify preservation and scientific completion, then seal local evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def files(root):
    return [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]


def preserve_prefix(current, original):
    if not current.startswith(original):
        raise ValueError("Historical document prefix changed")


def resource_limits(values):
    for key, cap in (
        ("campaign_wall_seconds", 36000),
        ("measured_cpu_seconds", 43200),
        ("gpu_seconds", 7200),
        ("additional_transfer_upper_bound_bytes", 2_000_000_000),
        ("storage_with_overhead_bound_bytes", 4_000_000_000),
    ):
        if not 0 <= values[key] < cap:
            raise ValueError(f"Resource boundary: {key}")


def active_workers():
    matches = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            argv = process.info["cmdline"] or []
            if any(
                arg.startswith("dual_rec.reboot.overnight_")
                or arg == "scripts/reboot_overnight_worker.py"
                for arg in argv
            ):
                matches.append(process.info["pid"])
        except psutil.Error:
            continue
    return matches


def verify(root):
    initial = json.loads((root / "initial.json").read_text())
    for name, expected in initial["prior_sha256"].items():
        if name in ("REBOOT_PHASE_PROTOCOL.md", "REBOOT_PHASE_REPORT.md"):
            original = subprocess.check_output(
                ["git", "show", initial["reviewed_base"] + ":" + name]
            )
            assert hashlib.sha256(original).hexdigest() == expected
            preserve_prefix(Path(name).read_bytes(), original)
        else:
            assert digest(Path(name)) == expected, name
    old = Path("results/reboot-phase/20261111T204459Z")
    assert digest(old / "completion_manifest.json") == initial["old_seal_sha256"]
    consumed = {}
    for name in ("consumed_inputs.json", "external_inputs.json"):
        consumed.update(json.loads((root / name).read_text()))
    for name, expected in consumed.items():
        assert digest(Path(name)) == expected, name
    registration = json.loads((root / "registration.json").read_text())
    assert digest(root / "registration.json") == digest(
        Path("config") / f"reboot_overnight_{root.name}.json"
    )
    assert digest(root / "registry.json") == registration["registry_sha256"]
    seal = json.loads((root / "main_prediction_seal.json").read_text())
    for name, expected in seal["sha256"].items():
        assert digest(root / name) == expected
    audit = json.loads((root / "independent_audit.json").read_text())
    assert (
        audit["status"] == "PASS"
        and audit["neural_checkpoints"] == 60
        and audit["total_checkpoints"] == 95
    )
    assert (
        audit["eligible_unique_recordings"] == 117
        and audit["unique_external_recordings"] == 306
    )
    assert audit["outcomes_sha256"] == digest(root / "outcomes.json")
    assert audit["paired_effects_sha256"] == digest(root / "paired_effects.json")
    for variant in ("Q", "QC"):
        examples = json.loads((root / f"streaming/examples_{variant}.json").read_text())
        for row in examples.values():
            if row["available"]:
                assert row["stream_alarm"] == row["batch_alarm"]
                assert row["maximum_stream_batch_score_difference"] < 1e-6
    rows = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    by_name = {r["name"]: r for r in rows}
    for job, source, archive in (
        (
            "train-frozen-five-folds",
            "src/dual_rec/reboot/overnight_models.py",
            "executed_overnight_models_v1.py",
        ),
        (
            "train-frozen-five-folds",
            "src/dual_rec/reboot/overnight_data.py",
            "executed_overnight_data_v1.py",
        ),
        (
            "train-frozen-five-folds",
            "src/dual_rec/reboot/overnight_experiment.py",
            "executed_overnight_experiment_v1.py",
        ),
        (
            "score-main-oof-and-seal",
            "src/dual_rec/reboot/overnight_metrics.py",
            "executed_overnight_metrics_v1.py",
        ),
        (
            "nominal-reference-shift",
            "src/dual_rec/reboot/overnight_diagnostics.py",
            "executed_overnight_diagnostics_v1.py",
        ),
        (
            "independent-recording-and-alarm-audit",
            "scripts/reboot_overnight_independent.py",
            "executed_overnight_independent_v1.py",
        ),
        (
            "train-frozen-five-folds",
            "scripts/reboot_overnight_worker.py",
            "executed_overnight_worker_v1.py",
        ),
    ):
        assert (
            digest(root / "provenance" / archive)
            == by_name[job]["source_sha256"][source]
        )
    for row in rows:
        assert digest(root / (row["name"] + ".log")) == row["log_sha256"]
    allowed_failures = {"compile-package", "new-code-lint"}
    assert all(r["exit_status"] == 0 or r["name"] in allowed_failures for r in rows)
    required = {
        "train-frozen-five-folds",
        "frozen-oof-and-sensor-controls",
        "nominal-reference-shift",
        "independent-recording-and-alarm-audit",
        "development-interval-permutation",
        "streaming-examples-both-inputs",
        "compact-tables-and-three-figures",
        "final-maintained-regression",
        "final-maintained-lint",
        "final-maintained-format",
    }
    passed = {r["name"] for r in rows if r["exit_status"] == 0}
    assert required <= passed, required - passed
    assert not active_workers(), "A campaign worker remains active"
    for name in ("alarm_frontier", "phase_comparison", "streaming_timeline"):
        assert (root / f"figures/{name}.pdf").exists()
    return (
        initial,
        rows,
        {
            "maintained_historical_files": len(initial["prior_sha256"]),
            "consumed_input_files": len(consumed),
            "old_seal_unchanged": True,
            "original_report_protocol_prefixes_preserved": True,
        },
    )


def main():
    started_cpu, started = time.process_time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    root = args.root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    initial, rows, preservation = verify(root)
    if args.seal:
        progress = json.loads((root / "progress.json").read_text())
        progress.update(
            phase="COMPLETE",
            active_research_workers=[],
            completed_utc=datetime.now(UTC).isoformat(),
        )
        (root / "progress.json").write_text(json.dumps(progress, indent=2) + "\n")
        with (root / "ledger.jsonl").open("a") as stream:
            stream.write(json.dumps(progress) + "\n")
    previous = (
        json.loads((root / "preseal_resources.json").read_text())
        if (root / "preseal_resources.json").exists()
        else {}
    )
    regular = files(root)
    values = {
        "campaign_wall_seconds": time.time() - initial["started_epoch"],
        "measured_worker_driver_cpu_seconds": sum(r["cpu_seconds"] for r in rows),
        "aggregate_worker_wall_seconds": sum(r["wall_seconds"] for r in rows),
        "gpu_seconds": 0,
        "paid_api_calls": 0,
        "additional_transfer_upper_bound_bytes": 1_000_000,
        "new_logical_bytes_before_seal": sum(p.stat().st_size for p in regular),
        "storage_with_overhead_bound_bytes": sum(p.stat().st_size for p in regular)
        + 50_000_000,
        "maximum_child_rss_kib": max(r["max_rss_kib"] for r in rows),
        "active_workers": [],
        "preservation": preservation,
        "metering_scope": "Foreground workers and drivers, plus successful closing checks. Initial bootstrap/editor/tool/metadata overhead and background host processes unmetered. Initial two-thread backend pools could overlap while spinning; final workers use passive OpenMP and BLAS1. GPU unavailable and no CUDA/model transfer attempted. One bounded official-tree connector fetch conservatively charged 1 MB; no packages/models/videos downloaded. New source/Git/tmp overhead charged 50 MB. Existing environments/inputs reused read-only.",
    }
    evidence = {}
    if args.seal:
        assert not subprocess.check_output(["git", "status", "--porcelain"], text=True)
        index = json.loads((root / "review_archive_index.json").read_text())
        assert (
            index["commit"]
            == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        )
        for name, expected in index["sha256"].items():
            assert digest(Path(name)) == expected
        evidence = {str(p.relative_to(root)): digest(p) for p in regular}
    values["closing_cpu_seconds"] = time.process_time() - started_cpu
    values["earlier_closing_cpu_seconds"] = previous.get(
        "closing_cpu_seconds", 0
    ) + previous.get("earlier_closing_cpu_seconds", 0)
    values["measured_cpu_seconds"] = (
        values["measured_worker_driver_cpu_seconds"]
        + values["closing_cpu_seconds"]
        + values["earlier_closing_cpu_seconds"]
    )
    values["closing_wall_seconds"] = time.monotonic() - started
    values["campaign_wall_seconds"] = time.time() - initial["started_epoch"]
    resource_limits(values)
    if args.seal:
        (root / "resources.json").write_text(json.dumps(values, indent=2) + "\n")
        evidence["resources.json"] = digest(root / "resources.json")
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", initial["reviewed_base"], "HEAD"], text=True
        ).splitlines()
        result = {
            "status": "COMPLETE_AUTHORIZED_OVERNIGHT_COMPARISON",
            "completed_utc": datetime.now(UTC).isoformat(),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "scientific_conclusion": "Phase accuracy/coherence gains did not yield improved timely recognition; premature alarms dominate. Exploratory released-annotation agreement, not physical recovery improvement or publication readiness.",
            "models": {
                "main_fits": 85,
                "development_permutation_fits": 10,
                "neural_fits": 60,
                "folds": 5,
                "seeds": [11, 23, 37],
            },
            "resources": values,
            "evidence_sha256": evidence,
            "maintained_sha256": {name: digest(Path(name)) for name in changed},
            "review_archive": {
                "path": str(root / "supervisor_review.tar.gz"),
                "sha256": digest(root / "supervisor_review.tar.gz"),
            },
            "symlink_targets": {
                str(p.relative_to(root)): os.readlink(p)
                for p in root.rglob("*")
                if p.is_symlink()
            },
            "scope": "All regular new evidence/cache files; reused inputs referenced by exact hashes. Completion manifest is nonrecursive; final verification is read-only. No research workers remain.",
        }
        (root / "completion_manifest.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    else:
        (root / "preseal_resources.json").write_text(
            json.dumps(values, indent=2) + "\n"
        )
    print(json.dumps(values, indent=2))


if __name__ == "__main__":
    main()
