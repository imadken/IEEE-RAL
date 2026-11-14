"""Independent audit entrypoints; no simulation, fit or calibration updates."""

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_final_analysis import audit_rows
from dsre_final_verify import verify_sources
from dsre_followup_batch import atomic, read, sha
from dsre_operational_analysis import qualified


def preservation(root):
    initial = read(root / "initial.json")
    allowed = set(initial["authorized_updates"])
    for name, expected in initial["prior_files"].items():
        if name in allowed:
            assert sha(root / "starting_files" / name) == expected
            original = subprocess.check_output(
                ["git", "show", initial["base"] + ":" + name]
            )
            import hashlib

            assert hashlib.sha256(original).hexdigest() == expected
        else:
            assert sha(Path(name)) == expected, name
    for name, expected in initial["historical_seals"].items():
        assert sha(Path(name)) == expected, name
    old = Path(initial["prior_root"])
    seal = read(old / "completion_manifest.json")
    for name, expected in seal["files"].items():
        assert sha(old / name) == expected, name
    for name, expected in seal["maintained_files"].items():
        import hashlib

        assert (
            hashlib.sha256(
                subprocess.check_output(["git", "show", initial["base"] + ":" + name])
            ).hexdigest()
            == expected
        ), name
    amendment = read(root / "qualification_nonruntime_amendment.json")
    assert sha(Path(amendment["old_source"])) == amendment["before_sha256"]
    assert sha(Path(amendment["file"])) == amendment["after_sha256"]
    for kind in ("source_sha256", "input_sha256"):
        for name, expected in read(root / "qualification_freeze.json")[kind].items():
            path = (
                Path(amendment["old_source"])
                if name == amendment["file"]
                else Path(name)
            )
            assert sha(path) == expected, name
    verify_sources(root)
    prior_followup = Path("results/dsre-followup/20261113T205403Z")
    inherited = read(prior_followup / "completion_manifest.json")
    for name, expected in inherited["files"].items():
        assert sha(prior_followup / name) == expected, name
    for name, expected in read(prior_followup / "initial.json")[
        "prior_run_members"
    ].items():
        assert sha(Path(name)) == expected, name
    return {
        "status": "PASS",
        "historical_seals": len(initial["historical_seals"]),
        "old_operational_members": len(seal["files"]),
        "initial_existing_files": len(initial["prior_files"]),
        "qualification_preparer_only_amendment_preserved": True,
        "old_followup_members": len(inherited["files"]),
        "inherited_prior_run_members": len(
            read(prior_followup / "initial.json")["prior_run_members"]
        ),
    }


def chunks(root):
    verify_sources(root)
    _, rows, _ = qualified(root)
    for path in sorted((root / "chunks").glob("*_complete.json")):
        dest = path.with_name(path.name.replace("_complete", "_audit"))
        if dest.exists():
            continue
        groups = set(read(path)["completed_parents"])
        selected = [r for r in rows if r["group"] in groups]
        proof = audit_rows(root, selected)
        atomic(dest, proof)
    print(
        json.dumps(
            {
                "status": "PASS",
                "complete_parents": len(rows) // 2,
                "chunks_audited": len(list((root / "chunks").glob("*_audit.json"))),
            }
        ),
        flush=True,
    )


def numerical(root):
    from dsre_operational_audit import audit_calibration
    from dsre_operational_finish import table_audit

    result = read(root / "operational_results.json")
    records = read(root / "test_records.json")
    checks = table_audit(records, result["tables"])
    lookup = {(r["id"], r["method"]): r for r in records if r["mode"] == "calibrated"}
    intervals = 0
    for key, values in result["paired_intervals"].items():
        task, contrast, pop = key.split("|")
        other = contrast.removeprefix("DSRE_risk-")
        base = [
            r
            for r in records
            if r["task"] == task
            and r["method"] == "DSRE_risk"
            and r["mode"] == "calibrated"
        ]
        parents = sorted({r["group"] for r in base})
        rs = [
            r
            for r in base
            if pop
            in (
                "all",
                r["category"],
                "initial_success" if r["initial_success"] else "initial_failure",
            )
        ]
        for field, value in values.items():
            if not rs:
                assert value is None
                continue
            frame = np.asarray(
                [
                    [
                        sum(
                            r[field] - lookup[r["id"], other][field]
                            for r in rs
                            if r["group"] == p
                        ),
                        sum(r["group"] == p for r in rs),
                    ]
                    for p in parents
                ],
                dtype=float,
            )
            rng = np.random.Generator(
                np.random.PCG64(2026111401 + int(task == "PushCube-v1"))
            )
            samples = frame[rng.integers(len(parents), size=(4000, len(parents)))].sum(
                axis=1
            )
            samples = samples[samples[:, 1] > 0]
            assert np.array_equal(
                np.percentile(samples[:, 0] / samples[:, 1], [2.5, 97.5]),
                value["parent_percentile95"],
            ), key
            assert frame[:, 0].sum() / frame[:, 1].sum() == value["value"]
            intervals += 1
    assignments = read(root / "test_assignment_errors.json")
    for key, value in assignments.items():
        method, task, action = key.split("|")
        selected = [
            r
            for r in records
            if r["mode"] == "proposal"
            and r["method"] == method
            and r["task"] == task
            and r["action"] == action
        ]
        assert value["assigned_parents"] == len({r["group"] for r in selected})
        assert value["error_parents"] == len(
            {r["group"] for r in selected if r["unacceptable"]}
        )
        assert value["checkpoints"] == len(selected) and value["no_gate_update"]
    bounds = audit_calibration(
        read(root / "calibration_records.json"),
        read(root / "calibration_decision.json")["strata"],
    )
    return {
        "status": "PASS",
        "table_fields_recounted": checks,
        "paired_interval_fields_recomputed": intervals,
        "complete_parents": len({r["group"] for r in records}),
        "heldout_assignment_strata_checked": len(assignments),
        "unchanged_calibration_bounds": bounds,
    }


def sensitivity(root):
    """Independently reconstruct weighted parent arrays and all registered CIs."""
    from dsre_operational_finish import table_audit

    counts = {}
    for name in ("historical", "heldout"):
        value = read(root / f"{name}_robustness.json")
        records = read(Path(value["source"]))
        fields = table_audit(records, value["tables"])
        by = defaultdict(list)
        for r in records:
            family = (
                r["scenario"].split("_r")[0]
                if r["scenario"].startswith("noise")
                else r["scenario"]
            )
            by[r["task"], r["method"], r["mode"], family].append(r)
        verified = 0
        metrics = (
            "successful",
            "unacceptable",
            "deferred",
            "action_unstable",
            "certificate_unstable",
            "false_confidence",
            "newly_unacceptable",
        )
        for key, entry in value["parent_intervals"].items():
            task, method, mode, scenario, pop = key.split("|")
            rs = by[task, method, mode, scenario]
            clean = {r["id"]: r for r in by[task, method, mode, "clean"]}
            groups = sorted({r["group"] for r in rs})
            vectors = {p: np.zeros(8) for p in groups}
            rep = 3 if scenario.startswith("noise") else 1
            for r in rs:
                if pop == "threshold_proximal" and not r["threshold_proximal"]:
                    continue
                clean_r = clean[r["id"]]
                vectors[r["group"]] += (
                    np.asarray(
                        [
                            r["successful"],
                            r["unacceptable"],
                            r["deferred"],
                            r["action"] != clean_r["action"],
                            not r["certificate_stable"],
                            r["false_confidence"],
                            bool(r["unacceptable"] and not clean_r["unacceptable"]),
                            1,
                        ],
                        dtype=float,
                    )
                    / rep
                )
            matrix = np.asarray([vectors[p] for p in groups])
            n = matrix[:, -1].sum()
            assert (
                entry["parents"] == len(groups)
                and abs(entry["effective_checkpoints"] - n) < 1e-9
            )
            if not n:
                assert entry["status"] == "NOT_ESTIMABLE_EMPTY_SUBGROUP"
                continue
            rng = np.random.Generator(
                np.random.PCG64(2026111401 + int(task == "PushCube-v1"))
            )
            sampled = matrix[rng.integers(len(groups), size=(4000, len(groups)))].sum(
                axis=1
            )
            sampled = sampled[sampled[:, -1] > 0]
            for i, metric in enumerate(metrics):
                expected = np.percentile(sampled[:, i] / sampled[:, -1], [2.5, 97.5])
                assert np.allclose(
                    expected, entry[metric]["parent_percentile95"], rtol=0, atol=1e-12
                ), (key, metric)
                assert abs(matrix[:, i].sum() / n - entry[metric]["value"]) < 1e-12
                verified += 1
        counts[name] = {
            "table_fields_recounted": fields,
            "interval_fields_recomputed": verified,
            "prediction_views": len(records),
        }
    return {
        "status": "PASS",
        "populations": counts,
        "replicates_and_conditions_not_independent_parents": True,
    }


def corrupted_raw(root):
    from dsre_final_verify import load_trace
    from dsre_operational_audit import audit_observation_values, audit_rules
    from dsre_operational_observations import (
        SCENARIOS,
        observation_packet,
        packet_from_summary,
    )

    from dual_rec.dsre.operational import OperationalRouter, gated_action

    frozen = read(root / "frozen_routers.json")
    router = OperationalRouter(frozen)
    cal = read(root / "calibration_decision.json")["strata"]
    records = read(root / "heldout_corruption_records.json")
    grouped = defaultdict(list)
    for r in records:
        grouped[r["id"], r["scenario"]].append(r)
    expected = {}
    representatives = []
    proof_records = []
    views = 0
    for row in qualified(root)[1]:
        raw = load_trace(row)
        clean = packet_from_summary(row, frozen)
        truth = {
            a: bool(raw["traces"][a]["frames"][-1]["state"]["success"])
            for a in ("continue", "recover")
        }
        for scenario in SCENARIOS:
            packet, metadata = observation_packet(raw, row["task"], scenario, frozen)
            audit_observation_values(packet, metadata, scenario)
            key = (packet.task, packet.values, packet.full_values)
            rs = grouped[row["id"], scenario]
            assert len(rs) == 34
            proposed = {r["method"]: r for r in rs if r["mode"] == "proposal"}
            if key not in expected:
                expected[key] = {
                    m: (r["action"], r["evidence"]) for m, r in proposed.items()
                }
                address = row["id"] + "@" + scenario
                representatives.append(
                    row
                    | {
                        "id": address,
                        "features": list(packet.full_values[:6]),
                        "optional_features": list(packet.full_values[6:]),
                    }
                )
                proof_records.extend(
                    r | {"id": address, "scenario": "clean"} for r in proposed.values()
                )
            for r in rs:
                action, facts = expected[key][r["method"]]
                actual = (
                    gated_action(r["method"], r["task"], action, cal)
                    if r["mode"] == "calibrated"
                    else action
                )
                assert (
                    r["proposed_action"] == action
                    and r["action"] == actual
                    and r["evidence"] == facts
                )
                good = int(actual is not None and truth[actual])
                assert (
                    r["successful"] == good
                    and r["unacceptable"] == int(actual is not None) - good
                )
                names = (
                    router.full[row["task"]].table.scope.features
                    if r["method"] == "full_signature_strict"
                    else router.settings[row["task"]][2].table.scope.features
                )
                values = (
                    clean.full_values
                    if r["method"] == "full_signature_strict"
                    else clean.values
                )
                contradicted = sum(
                    values[names.index(f["feature"])] is not None
                    and values[names.index(f["feature"])] != f["value"]
                    for f in facts
                )
                assert r["contradicted_certificate_facts"] == contradicted
                assert r["false_confidence"] == int(
                    action is not None and contradicted > 0
                )
                views += 1
    proof = audit_rules(router, representatives, proof_records)
    return {
        "status": "PASS",
        "new_corrupted_prediction_views_from_raw": views,
        "distinct_corrupted_queries": len(representatives),
        "independent_rule_tree_oracle": proof,
        "audit_addresses_do_not_add_experimental_parents": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("chunks", "preservation", "numerical", "sensitivity", "corrupted_raw"),
        required=True,
    )
    args = parser.parse_args()
    if args.stage == "chunks":
        chunks(args.root)
    else:
        result = {
            "preservation": preservation,
            "numerical": numerical,
            "sensitivity": sensitivity,
            "corrupted_raw": corrupted_raw,
        }[args.stage](args.root)
        atomic(args.root / f"{args.stage}_audit.json", result)
        print(result, flush=True)
