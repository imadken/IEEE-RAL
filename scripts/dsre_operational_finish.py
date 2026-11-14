"""Read-only numerical/preservation audits, scoped review packaging and final seal."""

import argparse
import gzip
import hashlib
import json
import subprocess
import tarfile
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import psutil
from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_operational_analysis import SUM_FIELDS
from dsre_operational_audit import audit_calibration, audit_rules
from dsre_operational_observations import observation_packet
from dsre_paper_confirmation import state_equal
from dsre_paper_finish import byte_size, format_audit, validate

from dual_rec.dsre.operational import OperationalRouter, gated_action


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def workers(root):
    current = psutil.Process()
    excluded = {current.pid, *[p.pid for p in current.parents()]}
    active = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = p.info["cmdline"] or []
            if (
                p.pid not in excluded
                and (str(root) in args or str(root.resolve()) in args)
                and any(
                    Path(a).name.startswith("dsre_operational_")
                    or Path(a).name == "reboot_overnight_worker.py"
                    for a in args
                )
            ):
                active.append(p.pid)
        except psutil.Error:
            pass
    return active


def maintained(root):
    return [
        *[Path(n) for n in read(root / "initial.json")["authorized_updates"]],
        Path("config/dsre_operational.json"),
        Path("src/dual_rec/dsre/operational.py"),
        *sorted(Path("scripts").glob("dsre_operational_*.py")),
        Path("tests/test_dsre_operational.py"),
        Path("docs/DSRE_FULL_PAPER_SCIENCE_PROTOCOL.md"),
        Path("rss2027/dsre_full_paper_master.tex"),
        Path("rss2027/dsre_full_paper_master.pdf"),
        Path("rss2027/operational_references.bib"),
        *[
            Path("rss2027/figures") / n
            for n in (
                "operational.pdf",
                "operational.png",
                "observation_robustness.pdf",
                "observation_robustness.png",
            )
        ],
        Path("rss2027/IEEEtran.cls"),
    ]


def preservation(root):
    initial = read(root / "initial.json")
    allowed = set(initial["authorized_updates"])
    for name, expected in initial["prior_files"].items():
        if name in allowed:
            assert sha(root / "starting_files" / name) == expected
            assert (
                hashlib.sha256(
                    subprocess.check_output(
                        ["git", "show", initial["base"] + ":" + name]
                    )
                ).hexdigest()
                == expected
            )
        else:
            assert sha(Path(name)) == expected, name
    for name, expected in initial["historical_seals"].items():
        assert sha(Path(name)) == expected, name
    old = Path("results/dsre-followup/20261113T205403Z")
    seal = read(old / "completion_manifest.json")
    for name, expected in seal["files"].items():
        assert sha(old / name) == expected, name
    for name, expected in read(old / "initial.json")["prior_run_members"].items():
        assert sha(Path(name)) == expected, name
    for name, expected in seal["maintained_files"].items():
        assert (
            hashlib.sha256(
                subprocess.check_output(["git", "show", initial["base"] + ":" + name])
            ).hexdigest()
            == expected
        ), name
    verify_freeze(root)
    return {
        "status": "PASS",
        "initial_existing_files": len(initial["prior_files"]),
        "historical_seals": len(initial["historical_seals"]),
        "old_followup_members": len(seal["files"]),
        "inherited_prior_run_members": len(
            read(old / "initial.json")["prior_run_members"]
        ),
        "frozen_pins": sum(
            len(read(root / "confirmation_freeze.json")[k])
            for k in ("source_sha256", "input_sha256")
        ),
        "earlier_maintained_versions_verified_from_git": len(seal["maintained_files"]),
    }


def table_audit(records, tables):
    counts = defaultdict(lambda: defaultdict(int))
    parents = defaultdict(set)
    for r in records:
        base = f"{r['task']}|{r['method']}|{r['mode']}|{r['scenario']}"
        for pop in (
            "all",
            r["condition"],
            "initial_success" if r["initial_success"] else "initial_failure",
            r["category"],
        ):
            key = base + "|" + pop
            counts[key]["checkpoints"] += 1
            parents[key].add(r["group"])
            for field in SUM_FIELDS:
                counts[key][field] += r[field]
    assert set(counts) == set(tables)
    fields = 0
    for key, expected in tables.items():
        for field, value in counts[key].items():
            assert value == expected[field], (key, field)
            fields += 1
        assert len(parents[key]) == expected["parents"]
        assert (
            expected["successful"] + expected["unacceptable"] == expected["recommended"]
        )
        assert expected["successful"] == expected["autonomous_completion"]
    return fields


def numerical(
    root, result_name="operational_results.json", record_name="test_records.json"
):
    result = read(root / result_name)
    records = read(root / record_name)
    fields = table_audit(records, result["tables"])
    lookup = {(r["id"], r["method"]): r for r in records if r["mode"] == "calibrated"}
    bootstraps = 0
    for key, values in result["paired_intervals"].items():
        task, contrast, pop = key.split("|")
        method = contrast.removeprefix("DSRE_risk-")
        rows = [
            r
            for r in records
            if r["task"] == task
            and r["method"] == "DSRE_risk"
            and r["mode"] == "calibrated"
        ]
        parents = sorted({r["group"] for r in rows})
        rows = [
            r
            for r in rows
            if pop
            in (
                "all",
                r["category"],
                "initial_success" if r["initial_success"] else "initial_failure",
            )
        ]
        for field, value in values.items():
            if not rows:
                assert value is None
                continue
            frame = np.array(
                [
                    [
                        sum(
                            r[field] - lookup[r["id"], method][field]
                            for r in rows
                            if r["group"] == g
                        ),
                        sum(r["group"] == g for r in rows),
                    ]
                    for g in parents
                ],
                dtype=float,
            )
            rng = np.random.Generator(
                np.random.PCG64(2026111401 + (task == "PushCube-v1"))
            )
            sampled = frame[rng.integers(len(parents), size=(4000, len(parents)))].sum(
                axis=1
            )
            sampled = sampled[sampled[:, 1] > 0]
            limits = np.percentile(sampled[:, 0] / sampled[:, 1], [2.5, 97.5])
            assert np.array_equal(limits, np.asarray(value["parent_percentile95"])), (
                key,
                field,
            )
            assert float(frame[:, 0].sum() / frame[:, 1].sum()) == value["value"]
            bootstraps += 1
    for r in records:
        if r["method"] == "DSRE_risk" and r["mode"] == "calibrated":
            assert r["action"] == lookup[r["id"], "B7_risk"]["action"]
    robustness = read(root / "observation_robustness.json")
    corrupt = read(root / "robustness_records.json")
    robustness_fields = table_audit(corrupt, robustness["tables"])
    calibration = (
        read(root / "calibration_decision.json")
        if (root / "calibration_decision.json").exists()
        else None
    )
    bounds = (
        audit_calibration(
            read(root / "calibration_records.json"), calibration["strata"]
        )
        if calibration
        else {"status": "NOT_CERTIFIED_NO_COMPLETE_CALIBRATION"}
    )
    if calibration:
        assert (
            sha(root / "calibration_decision.json")
            == read(root / "calibration_seal.json")["sha256"]
        )
        test_attempts = [
            read(p)
            for p in (root / "parent_attempts").glob("*.json")
            if read(p)["split"] == "test"
        ]
        assert all(
            p["epoch"] >= read(root / "calibration_seal.json")["epoch"]
            for p in test_attempts
        )
    return {
        "status": "PASS",
        "operational_fields_recounted": fields,
        "bootstrap_fields_recomputed": bootstraps,
        "corruption_fields_recounted": robustness_fields,
        "calibration": bounds,
        "B7_risk_exact_actions": True if records else "NOT_ASSESSABLE_EMPTY_POPULATION",
        "B7_risk_action_views_compared": sum(
            r["method"] == "DSRE_risk" and r["mode"] == "calibrated" for r in records
        ),
        "calibration_sealed_before_test": bool(calibration),
        "population_result": result_name,
        "paired_effects_estimable": bool(records),
    }


def selected_future_audit(root):
    frames = 0
    executions = 0
    max_position = 0.0
    for path in (root / "selected").glob("*/*/execution.json.gz"):
        with gzip.open(path, "rt") as stream:
            observed = json.load(stream)
        summary = read(
            root / "fresh" / path.parent.parent.name / path.parent.name / "summary.json"
        )
        with gzip.open(summary["source"], "rt") as stream:
            paired = json.load(stream)
        target = paired["traces"][observed["action"]]
        state_equal(observed["start"], target["start"])
        assert observed["controller_memory"] == paired["canonical_controller_memory"]
        assert observed["model_edit"] == paired["model"]["edit"]
        assert len(observed["frames"]) == len(target["frames"]) == 70
        for a, b in zip(observed["frames"], target["frames"], strict=True):
            state_equal(a["state"], b["state"])
            max_position = max(
                max_position,
                float(
                    np.linalg.norm(
                        np.asarray(a["state"]["position"]) - b["state"]["position"]
                    )
                ),
            )
            frames += 1
        executions += 1
    return {
        "status": "PASS" if executions else "NOT_ASSESSABLE_NO_SELECTED_CONTINUATIONS",
        "selected_executions": executions,
        "selected_future_states_checked": frames,
        "maximum_selected_position_difference": max_position,
        "qualification_scope": "Check actually completed selected branches only. No executed branches means parity is unassessed; the failed selected live-prefix diagnostics were not saved. Actual paired-prefix states are separately audited.",
    }


def format_full(root):
    pdf = Path("rss2027/dsre_full_paper_master.pdf")
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    fonts = subprocess.check_output(["pdffonts", str(pdf)], text=True)
    pages = [p for p in text.split("\f") if p.strip()]
    assert 7 <= len(pages) <= 9 and "REFERENCES" in pages[-1].replace(" ", "").upper()
    assert "PLANNED" not in text
    assert all("Type 1" in l and l.split()[-5] == "yes" for l in fonts.splitlines()[2:])
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
    assert "Overfull" not in (root / "master_compile.log").read_text()
    return {
        "status": "PASS",
        "total_pages": len(pages),
        "content_pages": len(pages) - 1,
        "reference_pages": 1,
        "anonymous_and_embedded_type1": True,
        "pdf_sha256": sha(pdf),
    }


def paper_claims(root):
    result = read(root / "operational_results.json")
    cal = (
        read(root / "calibration_decision.json")
        if (root / "calibration_decision.json").exists()
        else {"strata": {}}
    )
    checked = 0
    view = (
        read(root / "exploratory_operational_results.json")
        if not result["complete_parents"]
        else result
    )
    records = read(
        root
        / (
            "historical_operational_records.json"
            if not result["complete_parents"]
            else "test_records.json"
        )
    )
    for filename in ("rss2027/dsre_stage1.tex", "rss2027/dsre_full_paper_master.tex"):
        text = Path(filename).read_text()
        assert (
            f"{result['calibration_parents']}/360" in text
            and f"{result['complete_parents']}/160" in text
        )
        assert "B7" in text and "69" in text and "42" in text
        assert "calibration" in text.lower() and "defer" in text.lower()
        for task, label in (("PickCube-v1", "Pick"), ("PushCube-v1", "Push")):
            for action, short in (("continue", "C"), ("recover", "R")):
                b = cal["strata"].get(
                    f"DSRE_risk|{task}|{action}",
                    {
                        "assigned_parents": 0,
                        "error_parents": 0,
                        "upper": 1.0,
                        "enabled": False,
                    },
                )
                expected = f"{label} & {short} & {b['assigned_parents']}/{b['error_parents']} & {100 * b['upper']:.2f}\\% & {'on' if b['enabled'] else 'NC'}"
                assert expected in text, (filename, expected)
                checked += 4
            value = (
                view["paired_intervals"]
                .get(f"{task}|DSRE_risk-DSRE_strict|all", {})
                .get("successful")
            )
            if value:
                lo, hi = value["parent_percentile95"]
                assert f"[{100 * lo:.2f},{100 * hi:.2f}]" in text
                checked += 2
            rows = [
                r
                for r in records
                if r["task"] == task
                and r["method"] == "DSRE_risk"
                and r["mode"] == "calibrated"
            ]
            cm = sum(
                r["successful"] and r["action"] == "continue" and r["initial_success"]
                for r in rows
            )
            rr = sum(r["required_recovery_success"] for r in rows)
            other = sum(r["successful"] for r in rows) - cm - rr
            deferred = sum(r["deferred"] for r in rows)
            bad = sum(r["unacceptable"] for r in rows)
            assert f"{label} & {cm} & {rr} & {other} & {deferred}/{bad}" in text
            checked += 5
        if not result["complete_parents"]:
            assert "NOT ESTIMABLE" in text and "inspected" in text
        assert "tab:primarydecomp" in text
        assert "Lift" in text and (
            "blocked" in text.lower() or "failed" in text.lower()
        )
        assert "PLANNED" not in text
        checked += 6
    return {
        "status": "PASS",
        "main_calibration_and_interval_fields_checked": checked,
        "historical_and_new_populations_separated": True,
        "primary_completion_decomposition_present": True,
    }


def robustness_oracle_audit(root):
    from dsre_followup_analysis import collect

    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    calibration = (
        read(root / "calibration_decision.json")["strata"]
        if (root / "calibration_decision.json").exists()
        else {}
    )
    records = read(root / "robustness_records.json")
    by = defaultdict(list)
    for r in records:
        by[r["id"], r["scenario"]].append(r)
    _, historical, _ = collect(Path("results/dsre-followup/20261113T205403Z"))
    representatives = []
    representative_records = []
    expected = {}
    checked = 0
    for row in historical:
        with gzip.open(row["source"], "rt") as stream:
            raw = json.load(stream)
        truth = {
            a: bool(raw["traces"][a]["frames"][-1]["state"]["success"])
            for a in ("continue", "recover")
        }
        for scenario in read(root / "observation_robustness.json")["scenarios"]:
            packet, _ = observation_packet(raw, row["task"], scenario, frozen)
            key = (packet.task, packet.values, packet.full_values)
            group = by[row["id"], scenario]
            proposal = {r["method"]: r for r in group if r["mode"] == "proposal"}
            if key not in expected:
                expected[key] = {
                    m: (r["action"], r["evidence"]) for m, r in proposal.items()
                }
                # Synthetic audit addresses identify observations, not new seeds
                # or measurements; raw source and original parent remain fixed.
                address = row["id"] + "@" + scenario
                representatives.append(
                    row
                    | {
                        "id": address,
                        "features": list(packet.full_values[:6]),
                        "optional_features": list(packet.full_values[6:]),
                    }
                )
                representative_records.extend(
                    r | {"id": address, "scenario": "clean"} for r in proposal.values()
                )
            for r in group:
                proposed, evidence = expected[key][r["method"]]
                assert r["proposed_action"] == proposed and r["evidence"] == evidence
                action = (
                    gated_action(r["method"], r["task"], proposed, calibration)
                    if r["mode"] == "calibrated"
                    else proposed
                )
                good = int(action is not None and truth[action])
                assert (
                    r["action"] == action
                    and r["successful"] == good
                    and r["unacceptable"] == int(action is not None) - good
                )
                checked += 1
    proof = audit_rules(router, representatives, representative_records)
    return {
        "status": "PASS",
        "corrupted_prediction_views_checked_from_raw": checked,
        "distinct_corrupted_queries": len(representatives),
        "independent_rule_tree_proof": proof,
        "scope": "Same original parents and outcomes, all fixed scenarios; audit addresses are not extra experimental samples",
    }


def audit(root):
    assert not workers(root)
    assert read(root / "independent_audit.json")["status"] == "PASS"
    jobs = [json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()]
    freeze = read(root / "confirmation_freeze.json")
    source_checks = 0
    for job in jobs:
        assert job["exit_status"] == 0, (job["name"], job["exit_status"])
        assert sha(root / (job["name"] + ".log")) == job["log_sha256"]
        for name, expected in freeze["source_sha256"].items():
            assert job["source_sha256"].get(name) == expected, (job["name"], name)
            source_checks += 1
    physical = sum(j["wall_seconds"] for j in jobs if j["name"].startswith("physics_"))
    assert physical <= 10800
    findings = {
        "status": "PASS",
        "preservation": preservation(root),
        "numerical": numerical(root),
        "exploratory_numerical": numerical(
            root,
            "exploratory_operational_results.json",
            "historical_operational_records.json",
        ),
        "selected_future": selected_future_audit(root),
        "paper_claims": paper_claims(root),
        "corruption_oracles": robustness_oracle_audit(root),
        "stage1_format": format_audit(root),
        "full_paper_format": format_full(root),
        "physics_outer_worker_wall_seconds": physical,
        "worker_source_hashes_checked": source_checks,
        "workers": [],
        "audit_scope": "Separate same-session implementations, not external human replication",
    }
    atomic(root / "final_audit.json", findings)
    print(
        json.dumps(
            {
                "status": "PASS",
                "test_parents": read(root / "operational_results.json")[
                    "complete_parents"
                ],
                "physics_wall_seconds": physical,
                "stage1_pages": 6,
                "master_pages": findings["full_paper_format"]["total_pages"],
            }
        ),
        flush=True,
    )


def seal(root):
    if (root / "completion_manifest.json").exists():
        raise ValueError("Already sealed")
    assert read(root / "validation.json")["status"] == "PASS"
    audit(root)
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
    gate = read(root / "scientific_gate.json")
    gate["PAPER_DRAFT_READY"] = True
    gate["paper"] = (
        "FORMALLY_COMPLETE_8_PLUS_1_MASTER_AND_5_PLUS_1_STAGE1; limitations explicit; scientific significance requires supervisor judgment"
    )
    gate["remaining_workers"] = []
    atomic(root / "scientific_gate.json", gate)
    resources = {
        "wall_seconds": time.time() - initial["started_epoch"],
        "session_wall_ceiling_seconds": 28800,
        "new_physics_outer_wall_seconds": sum(
            j["wall_seconds"] for j in jobs if j["name"].startswith("physics_")
        ),
        "new_physics_ceiling_seconds": 10800,
        "measured_worker_cpu_seconds": sum(j["cpu_seconds"] for j in jobs),
        "maximum_worker_rss_kib": max(j["max_rss_kib"] for j in jobs),
        "manual_orchestration_and_independent_audit_cpu_allowance_seconds": 900,
        "new_fits": 0,
        "gpu_training_seconds": 0,
        "paid_API_calls": 0,
        "new_controllers": 0,
        "new_qualified_paired_checkpoints": read(root / "missingness.json")[
            "qualified_cells"
        ],
        "new_paired_action_continuations": 2
        * read(root / "missingness.json")["qualified_cells"],
        "new_selected_execution_continuations": read(root / "independent_audit.json")[
            "selected_execution"
        ]["new_selected_action_continuations"],
        "completed_test_parents": read(root / "operational_results.json")[
            "complete_parents"
        ],
        "completed_calibration_parents": read(root / "operational_results.json")[
            "calibration_parents"
        ],
        "new_evidence_bytes_before_archive": byte_size(root),
        "maintained_bytes": sum(byte_size(p) for p in paths),
        "workers": [],
    }
    assert (
        resources["wall_seconds"] < 28800
        and resources["new_physics_outer_wall_seconds"] <= 10800
    )
    atomic(root / "resources.json", resources)
    archive = root / "supervisor_review.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        for path in paths:
            stream.add(path, arcname=str(path))
        for p in sorted(root.iterdir()):
            if (
                p.is_file()
                and p.suffix in (".json", ".md", ".txt", ".jsonl", ".patch")
                and not p.name.endswith("_records.json")
                and p.name
                not in (
                    "robustness_records.json",
                    "preflight_records.json",
                    "draft_routers.json",
                )
            ):
                stream.add(p, arcname="evidence/" + p.name)
        for name in ("chunks", "template"):
            for p in sorted((root / name).glob("*.json")):
                stream.add(p, arcname=f"evidence/{name}/{p.name}")
    resources["review_archive_bytes"] = byte_size(archive)
    resources["conservative_new_artifact_bytes"] = (
        byte_size(root)
        + resources["maintained_bytes"]
        + byte_size(Path("/home/imad/.cache/tectonic"))
        + 11000000
    )
    assert resources["conservative_new_artifact_bytes"] < 1000000000
    atomic(root / "resources.json", resources)
    manifest = {
        "status": "COMPLETE_AUTHORIZED_OPERATIONAL_CAMPAIGN"
        if resources["completed_test_parents"] == 160
        else "COMPLETE_VALID_WORK_TEST_COHORT_INCOMPLETE",
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "files": {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and p.name != "completion_manifest.json"
        },
        "maintained_files": {str(p): sha(p) for p in paths},
        "resources": resources,
        "archive": str(archive),
        "archive_sha256": sha(archive),
        "archive_bytes": byte_size(archive),
        "scientific_gate": gate,
        "workers": [],
        "no_push_submission_or_upload": True,
    }
    atomic(root / "completion_manifest.json", manifest)
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ("status", "commit", "archive", "archive_bytes", "workers")
            }
        ),
        flush=True,
    )


def verify(root):
    m = read(root / "completion_manifest.json")
    for n, expected in m["files"].items():
        assert sha(root / n) == expected, n
    for n, expected in m["maintained_files"].items():
        assert sha(Path(n)) == expected, n
    assert not workers(root)
    print(
        json.dumps(
            {
                "status": "PASS",
                "sealed_members": len(m["files"]),
                "preservation": preservation(root),
                "commit": m["commit"],
                "workers": [],
            }
        ),
        flush=True,
    )


def reproduce(root):
    """Recompute raw numerical/rule proofs without writing into sealed evidence."""
    verify(root)
    scratch = Path(tempfile.mkdtemp(prefix="dsre-operational-audit-"))
    outputs = {
        "final_audit.json",
        "paper_pdfinfo.txt",
        "paper_pdffonts.txt",
        "paper_format_audit.json",
    }
    for path in root.iterdir():
        if path.name not in outputs:
            (scratch / path.name).symlink_to(
                path.resolve(), target_is_directory=path.is_dir()
            )
    audit(scratch)
    print(
        json.dumps(
            {
                "read_only_evidence": str(root),
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
        choices=("validate", "audit", "seal", "verify", "reproduce"),
        required=True,
    )
    args = parser.parse_args()
    {
        "validate": validate,
        "audit": audit,
        "seal": seal,
        "verify": verify,
        "reproduce": reproduce,
    }[args.stage](args.root)
