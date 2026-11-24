"""Independent physical, eligibility, source-access and numerical follow-up audit.

No production inference or collector is imported. Full raw traces are decoded
independently, including exact reconstruction of every new gzip container.
"""

import argparse
import gzip
import hashlib
import json
import lzma
import math
import sys
import zlib
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_evidence_audit import equal
from dsre_evidence_prospective_audit import audit as numerical_audit
from dsre_evidence_prospective_audit import physical
from scipy.optimize import linprog

TASK = "PegInsertionSide-v1"
NO_CHECKPOINT = "NO_DECISION_CHECKPOINT_SOURCE_PLANNER_FAILURE"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    path = Path(path)
    if path.suffix == ".gz":
        if path.exists():
            with gzip.open(path, "rt") as handle:
                return json.load(handle)
        metadata = json.loads(Path(str(path) + ".archive.json").read_text())
        compressed = path.with_suffix(".xz").read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == metadata["xz_sha256"]
        data = lzma.decompress(compressed)
        assert hashlib.sha256(data).hexdigest() == metadata["decoded_sha256"]
        compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
        body = compressor.compress(data)
        if metadata["sync_flush"]:
            body += compressor.flush(zlib.Z_SYNC_FLUSH)
        body += compressor.flush(zlib.Z_FINISH)
        original = (
            bytes.fromhex(metadata["header"]) + body + bytes.fromhex(metadata["footer"])
        )
        assert hashlib.sha256(original).hexdigest() == metadata["original_gzip_sha256"]
        assert gzip.decompress(original) == data
        return json.loads(data)
    return json.loads(path.read_text())


def pid(spec):
    return hashlib.sha256(
        f"prospective-parent:{spec['task']}:{spec['seed']}".encode()
    ).hexdigest()


def cell(partition, x):
    assert x is not None and len(x) == 5 and all(isinstance(v, bool) for v in x)
    return partition["cells"][sum(int(v) << (4 - i) for i, v in enumerate(x))]


def source_failure(raw):
    assert raw["status"] == "FAILED_PREREQUISITE_OR_PREFIX"
    assert raw["error"] == "UPSTREAM_SCREW_PLANNING_FAILED" and raw["phase"] == "prefix"
    assert "line 443, in insertion" in raw["traceback"]
    assert (
        len(raw["prefix"]) == 1
        and not raw["prefix_controls"]
        and not raw["post_controls"]
    )
    assert all(raw.get(k) is None for k in ("checkpoint", "success", "features"))

    def finite(value):
        if isinstance(value, dict):
            return all(finite(v) for v in value.values())
        if isinstance(value, list):
            return all(finite(v) for v in value)
        return not isinstance(value, (int, float)) or math.isfinite(value)

    assert finite(raw["prefix"][0])


def run(root, output, numerical_output, compact=False):
    out = root / "prospective" / TASK
    counts = Counter()
    amendment = read(root / "eligibility_amendment.json")
    registration = read(root / "registration.json")
    assert (
        amendment["assigned_calibration_outcomes_opened"]
        == amendment["test_outcomes_opened"]
        == 0
    )
    for name, checksum in amendment["method_sha256"].items():
        assert sha(Path(name)) == checksum, name
    guardpath = out / "SOURCE_GUARD_FAILURE.json"
    guard_review = None
    if guardpath.exists():
        guard = read(guardpath)
        spec = guard["spec"]
        directory = root / "physics" / TASK / spec["phase"] / str(spec["index"])
        raw = read(directory / "acquisition_screen.json.gz")
        assert raw["spec"] == spec and raw["phase"] == "prefix"
        assert raw["status"] == "FAILED_PREREQUISITE_OR_PREFIX"
        assert raw["error"] == "UPSTREAM_SCREW_PLANNING_FAILED"
        assert len(raw["prefix"]) == len(raw["prefix_controls"]) + 1
        for i, packet in enumerate(raw["prefix"]):
            assert packet["elapsed"] == [i]
            assert all(math.isfinite(v) for v in np.asarray(packet["qpos"]).ravel())
            assert all(math.isfinite(v) for v in np.asarray(packet["qvel"]).ravel())
            for name in ("peg", "hole", "tcp", "drive_targets", "drive_velocities"):
                assert np.all(np.isfinite(np.asarray(packet[name])))
        assert all(raw.get(k) is None for k in ("checkpoint", "features", "success"))
        assert len(raw["prefix_controls"]) > 0
        assert "line 444, in insertion" in raw["traceback"]
        guard_review = {
            "independently_reviewed": True,
            "spec": spec,
            "last_attempted_stage": "Second prefix move: move(grasp), worker line444",
            "prefix_controls": len(raw["prefix_controls"]),
            "prefix_states": len(raw["prefix"]),
            "elapsed_steps": raw["prefix"][-1]["elapsed"],
            "finite_recorded_physics": True,
            "executable_decision_checkpoint": False,
            "observed_intervention_outcome": None,
            "eligibility_ruling": "Outside registered zero-control source-exclusion rule; independent review preserves hard guard, does not silently widen eligibility or change checkpoint.",
            "requires_supervisor_source_ruling_before_resume": True,
        }
        counts["independently_reviewed_unapproved_postcontrol_prefix_failure"] += 1
    rows_by_phase = {}
    for phase in ("discovery", "calibration", "test"):
        rows = {p.stem: read(p) for p in (out / phase).glob("*.json")}
        rows_by_phase[phase] = rows
        original = registration["cohorts"][TASK][phase]
        assert (
            len(original) == {"discovery": 128, "calibration": 1024, "test": 256}[phase]
        )
        assert set(rows) <= {pid(s) for s in original}
        for parent, row in rows.items():
            spec = row["spec"]
            assert pid(spec) == parent and spec["phase"] == phase
            directory = root / "physics" / TASK / phase / str(spec["index"])
            if row["status"] == NO_CHECKPOINT:
                assert (
                    row.get("y") is None
                    and row.get("action") is None
                    and row.get("x") is None
                )
                assert not (out / "learner_records" / phase / f"{parent}.json").exists()
                if phase == "test":
                    assert not (out / "online_decisions" / f"{parent}.json").exists()
                    pair = read(out / "evaluator" / f"{parent}.json")
                    assert pair["yc"] is None and pair["yr"] is None
                    if not compact:
                        raw = read(directory / "policy_screen.json.gz")
                        source_failure(raw)
                        for repeat in (1, 2):
                            other = read(
                                directory / f"eligibility_repeat_{repeat}.json.gz"
                            )
                            source_failure(other)
                            equal(raw["prefix"], other["prefix"])
                        counts["independently_reproduced_test_source_exclusions"] += 1
                counts[phase + "_no_decision_source_failure"] += 1
                continue
            assert row["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT")
            if phase != "test":
                behavior = (
                    int(
                        hashlib.sha256(
                            f"dsre-evidence-v2:arm:{TASK}:{spec['seed']}".encode()
                        ).hexdigest(),
                        16,
                    )
                    % 2
                )
                assert row["action"] == ("c", "r")[behavior]
                assert (
                    row["record"]["propensity"] == 0.5
                    and not row["record"]["counterpart_exposed"]
                )
                assert (
                    not {"yc", "yr", "seed", "offset", "condition", "fault", "oracle"}
                    & row["record"].keys()
                )
            if phase == "calibration":
                assert "CONDITIONAL ON" in row["record"]["source_scope"]["population"]
            counts[phase + "_eligible_outcomes"] += 1
            if not compact:
                label = "selected_policy" if phase == "test" else "randomized_assigned"
                raw = read(directory / f"{label}.json.gz")
                assert (
                    raw["spec"] == spec
                    and raw["action"] == row["action"]
                    and raw["success"] == row["y"]
                )
                assert raw["features"] == row["x"]
                physical(raw, TASK)
                counts["physically_audited_assigned_or_selected"] += 1
                if phase in ("calibration", "test"):
                    screen = read(
                        directory
                        / (
                            "policy_screen.json.gz"
                            if phase == "test"
                            else "acquisition_screen.json.gz"
                        )
                    )
                    for key in ("prefix", "prefix_controls", "checkpoint", "features"):
                        equal(screen[key], raw[key])
                receipt = read(directory / f"{label}.execution.json")
                assert (
                    receipt["source_sha256"]
                    == amendment["method_sha256"]["scripts/dsre_evidence_tasks.py"]
                )
                assert receipt["finished_epoch"] <= row["epoch"]
                if phase != "discovery":
                    assert receipt["started_epoch"] >= amendment["epoch"]
                if phase == "test":
                    primary = read(out / "all_models_frozen.json")
                    assert receipt["started_epoch"] >= primary["epoch"]
                    pair = read(out / "evaluator" / f"{parent}.json")
                    assert pair["first_seal_sha256"] == sha(
                        out / "test" / f"{parent}.json"
                    )
                    other = read(directory / "evaluator_counterpart.json.gz")
                    assert (
                        read(directory / "evaluator_counterpart.execution.json")[
                            "started_epoch"
                        ]
                        >= row["epoch"]
                    )
                    for key in ("prefix", "prefix_controls", "checkpoint", "features"):
                        equal(raw[key], other[key])
                    physical(other, TASK)
                    c, r = (
                        (raw["success"], other["success"])
                        if row["action"] == "c"
                        else (other["success"], raw["success"])
                    )
                    assert pair["yc"] == c and pair["yr"] == r
                    counts["physical_counterfactual_pairs"] += 1
        print(json.dumps({"audit_phase": phase, "counts": dict(counts)}), flush=True)
    for file in (out / "screens").glob("*.json"):
        row = read(file)
        parent, spec = row["parent_id"], row["spec"]
        assert pid(spec) == parent
        if row["status"] == NO_CHECKPOINT:
            assert not (out / "learner_observations/calibration" / file.name).exists()
            directory = root / "physics" / TASK / "calibration" / str(spec["index"])
            raw = read(directory / "acquisition_screen.json.gz")
            source_failure(raw)
            proof = read(out / "eligibility" / file.name)
            assert proof["status"] == NO_CHECKPOINT
            if spec["index"] == 259:
                source = read(root / "independent_source_reproductions.json")
                paths = [Path(r["raw_path"]) for r in source["reproductions"]]
            else:
                paths = [directory / f"eligibility_repeat_{i}.json.gz" for i in (1, 2)]
            for path in paths:
                other = read(path)
                source_failure(other)
                equal(raw["prefix"], other["prefix"])
            counts["independently_reproduced_source_exclusions"] += 1
        else:
            assert row["status"] == "CHECKPOINT_ONLY"
            if not compact:
                raw = read(
                    root
                    / "physics"
                    / TASK
                    / "calibration"
                    / str(spec["index"])
                    / "acquisition_screen.json.gz"
                )
                assert raw["status"] == row["status"] and raw["features"] == row["x"]
                counts["physical_calibration_screens"] += 1
    schedulepath = out / "acquisition_schedule.json"
    if schedulepath.exists():
        schedule = read(schedulepath)
        partition = read(out / "discovery_freeze.json")["partition"]
        contexts = {
            p.stem: read(p)
            for p in (out / "learner_observations/calibration").glob("*.json")
        }
        screened = {p.stem: read(p) for p in (out / "screens").glob("*.json")}
        base = {p for p in contexts if screened[p]["spec"]["index"] < 512}
        candidates = set(contexts) - base
        assert (
            set(schedule["base_ids"]) == base
            and set(schedule["candidate_ids"]) == candidates
        )
        for parent, row in rows_by_phase["calibration"].items():
            if row["status"] != NO_CHECKPOINT:
                receipt = read(
                    root
                    / "physics"
                    / TASK
                    / "calibration"
                    / str(row["spec"]["index"])
                    / "randomized_assigned.execution.json"
                )
                assert (
                    receipt["started_epoch"] >= schedule["epoch"] >= amendment["epoch"]
                )
        for strategy, budgets in schedule["schedules"].items():
            previous = []
            for budget, requests in budgets.items():
                assert requests[: len(previous)] == previous
                assert sum(r["cost"] for r in requests) <= int(budget)
                assert len({r["parent_id"] for r in requests}) == len(requests)
                for leaf in set(partition["cells"]):
                    eligible = sorted(
                        [
                            p
                            for p in candidates
                            if cell(partition, contexts[p]["x"]) == leaf
                        ],
                        key=lambda p: int(
                            hashlib.sha256(
                                ("prospective-acquire:" + p).encode()
                            ).hexdigest(),
                            16,
                        ),
                    )
                    chosen = [r["parent_id"] for r in requests if r["leaf"] == leaf]
                    assert chosen == eligible[: len(chosen)]
                    counts["outcome_blind_leaf_prefixes"] += 1
                modelpath = out / "models" / f"{strategy}_{budget}.json"
                if modelpath.exists():
                    model = read(modelpath)
                    assert set(model["log_parent_ids"]) == base | {
                        r["parent_id"] for r in requests
                    }
                    assert set(model["pair_parent_ids"]) == {
                        r["parent_id"] for r in requests if r["kind"] == "pair"
                    }
                    assert model["logical_calibration_executions"] == len(base) + sum(
                        r["cost"] for r in requests
                    )
                    counts["exact_strategy_memberships"] += 1
                previous = requests
    for path in (out / "acquisition_pairs").glob("*.json"):
        entry = read(path)
        row = rows_by_phase["calibration"][path.stem]
        assert entry["schedule_sha256"] == sha(schedulepath)
        if not compact:
            directory = (
                root / "physics" / TASK / "calibration" / str(row["spec"]["index"])
            )
            first = read(directory / "randomized_assigned.json.gz")
            other = read(directory / "acquisition_counterpart.json.gz")
            for key in ("prefix", "prefix_controls", "checkpoint", "features"):
                equal(first[key], other[key])
            physical(other, TASK)
            counts["physical_acquisition_pairs"] += 1
    maxerror = 0.0
    for path in (out / "models").glob("*.json"):
        model = read(path)
        assert "CONDITIONAL ON" in model["source_scope"]["population"]
        for name in model["successful_data_reads"]:
            assert "/evaluator/" not in name and "/test/" not in name
        for leaf in model["leaves"].values():
            rows, rhs = [], []
            for field, coefficient in (
                ("p0", [0, 0, 1, 1]),
                ("p1", [0, 1, 0, 1]),
                ("harm", [0, 0, 1, 0]),
                ("rescue", [0, 1, 0, 0]),
            ):
                band = leaf["evidence"][field]
                if band is not None:
                    rows.extend([coefficient, [-v for v in coefficient]])
                    rhs.extend([band["hi"], -band["lo"]])
            a, b = np.asarray(rows), np.asarray(rhs)
            for field, coefficient, maximum in (
                ("harm_lower", [0, 0, 1, 0], False),
                ("harm_upper", [0, 0, 1, 0], True),
                ("gain_lower", [0, 1, -1, 0], False),
                ("gain_upper", [0, 1, -1, 0], True),
                ("failure_upper", [1, 0, 1, 0], True),
            ):
                v = np.asarray(coefficient)
                answer = linprog(
                    -v if maximum else v,
                    A_ub=a,
                    b_ub=b,
                    A_eq=np.ones((1, 4)),
                    b_eq=[1],
                    bounds=(0, None),
                    method="highs",
                )
                assert answer.success
                q = np.asarray(leaf["bounds"]["optimizers"][field])
                assert (
                    min(q) >= -1e-9
                    and abs(q.sum() - 1) < 1e-9
                    and max(a @ q - b) < 1e-9
                )
                error = max(
                    abs(v @ answer.x - leaf["bounds"][field]),
                    abs(v @ q - leaf["bounds"][field]),
                )
                assert error < 1e-9
                maxerror = max(maxerror, float(error))
                counts["all_extrema_and_optimizers"] += 1
    numerical_audit(
        root, TASK, numerical_only=True, relocated=compact, output=numerical_output
    )
    assert not any(n.startswith("dual_rec.evidence_aware") for n in sys.modules)
    result = {
        "passed": True,
        "counts": dict(counts),
        "max_numerical_error": maxerror,
        "source_guard": read(guardpath) if guardpath.exists() else None,
        "source_guard_independent_review": guard_review,
        "production_inference_imported": False,
        "raw_physics_complete_in_this_audit": not compact,
        "scope": "Source-eligible checkpoints and fixed whole leaves only. A passed record audit does not erase a preserved hard qualification blocker.",
        "audit_source_sha256": sha(Path(__file__)),
    }
    with output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--numerical-output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    run(args.root, args.output, args.numerical_output, args.compact)
