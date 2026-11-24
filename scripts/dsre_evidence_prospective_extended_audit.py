"""Independent extrema, countermodel and frozen-acquisition membership checks.

Imports no production inference, collector or simulator. Operates on sealed JSON
and execution receipts; the separate full audit checks every raw physical trace.
"""

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


def read(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as handle:
        return json.load(handle)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route(partition, x):
    assert x is not None and all(isinstance(v, bool) for v in x)
    index = sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))
    return partition["cells"][index]


def constraints(evidence):
    rows, rhs = [], []
    for name, vector in (
        ("p0", [0, 0, 1, 1]),
        ("p1", [0, 1, 0, 1]),
        ("harm", [0, 0, 1, 0]),
        ("rescue", [0, 1, 0, 0]),
    ):
        band = evidence[name]
        if band is not None:
            rows.extend([vector, [-v for v in vector]])
            rhs.extend([band["hi"], -band["lo"]])
    return np.asarray(rows), np.asarray(rhs)


def feasible(q, a, b):
    q = np.asarray(q)
    assert q.shape == (4,) and np.min(q) >= -1e-9
    assert abs(q.sum() - 1) < 1e-9 and np.max(a @ q - b) < 1e-9
    return q


def run(root, output):
    counts = Counter()
    maxerror = 0.0
    tasks = {}
    for task in ("PointMaze_UMaze-v3", "PickCube-v1", "PegInsertionSide-v1"):
        out = root / "prospective" / task
        schedulepath = out / "acquisition_schedule.json"
        partitionpath = out / "discovery_freeze.json"
        failures = []
        for phase, folder, rawlabel in (
            ("discovery", "discovery", "randomized_assigned"),
            ("calibration", "screens", "acquisition_screen"),
            ("calibration", "calibration", "randomized_assigned"),
            ("test", "test", "selected_policy"),
        ):
            for path in (out / folder).glob("*.json"):
                record = read(path)
                if record["status"] in (
                    "COMPLETE",
                    "CHECKPOINT_ONLY",
                    "OBSERVED_ABORT_ENDPOINT",
                    "ALREADY_SOLVED_PREFIX",
                ):
                    continue
                spec = record["spec"]
                rawpath = (
                    root
                    / "physics"
                    / task
                    / phase
                    / str(spec["index"])
                    / (rawlabel + ".json.gz")
                )
                raw = read(rawpath)
                assert raw["status"] == record["status"]
                assert raw.get("success") is None and record.get("y") is None
                assert not (out / "learner_records" / phase / path.name).exists()
                assert "record" not in record
                if folder == "screens":
                    assert not (
                        out / "learner_observations/calibration" / path.name
                    ).exists()
                failures.append(
                    {
                        "phase": phase,
                        "index": spec["index"],
                        "seed": spec["seed"],
                        "status": raw["status"],
                        "error": raw.get("error"),
                        "checkpoint_present": raw.get("checkpoint") is not None,
                        "raw_sha256": digest(rawpath),
                        "no_label_imputation": True,
                    }
                )
                counts["source_failure_witnesses"] += 1
        if not schedulepath.exists():
            tasks[task] = {"acquisition": "NOT_FROZEN", "source_failures": failures}
            continue
        schedule = read(schedulepath)
        frozen = read(partitionpath)
        partition = frozen["partition"]
        contexts = {
            p.stem: read(p)
            for p in (out / "learner_observations/calibration").glob("*.json")
        }
        metadata = {p.stem: read(p) for p in (out / "screens").glob("*.json")}
        expectedbase = {pid for pid in contexts if metadata[pid]["spec"]["index"] < 512}
        expectedcandidates = set(contexts) - expectedbase
        assert set(schedule["base_ids"]) == expectedbase
        assert set(schedule["candidate_ids"]) == expectedcandidates
        assert schedule["epoch"] >= max(r["epoch"] for r in metadata.values())
        assert schedule["epoch"] >= frozen["epoch"]
        for name, checksum in schedule["method_source_sha256"].items():
            assert digest(Path(name)) == checksum
            counts["pinned_method_hashes"] += 1
        for receiptpath in (root / "physics" / task / "calibration").glob(
            "*/randomized_assigned.execution.json"
        ):
            assert schedule["epoch"] <= read(receiptpath)["started_epoch"]
            counts["allocation_before_calibration_receipts"] += 1
        for strategy, budgets in schedule["schedules"].items():
            previous = []
            for budget, requests in budgets.items():
                assert requests[: len(previous)] == previous
                assert len({r["parent_id"] for r in requests}) == len(requests)
                assert sum(r["cost"] for r in requests) <= int(budget)
                assert all(
                    r["cost"] == (2 if r["kind"] == "pair" else 1) for r in requests
                )
                for c in set(partition["cells"]):
                    candidates = sorted(
                        [
                            pid
                            for pid in expectedcandidates
                            if route(partition, contexts[pid]["x"]) == c
                        ],
                        key=lambda pid: int(
                            hashlib.sha256(
                                ("prospective-acquire:" + pid).encode()
                            ).hexdigest(),
                            16,
                        ),
                    )
                    chosen = [r["parent_id"] for r in requests if r["leaf"] == c]
                    assert chosen == candidates[: len(chosen)]
                    counts["outcome_blind_leaf_prefixes"] += 1
                for request in requests:
                    pid = request["parent_id"]
                    assert pid in expectedcandidates
                    assert request["leaf"] == route(partition, contexts[pid]["x"])
                modelpath = out / "models" / f"{strategy}_{budget}.json"
                if modelpath.exists():
                    model = read(modelpath)
                    assert set(model["log_parent_ids"]) == expectedbase | {
                        r["parent_id"] for r in requests
                    }
                    assert set(model["pair_parent_ids"]) == {
                        r["parent_id"] for r in requests if r["kind"] == "pair"
                    }
                    assert model["logical_calibration_executions"] == len(
                        expectedbase
                    ) + sum(r["cost"] for r in requests)
                    counts["exact_strategy_memberships"] += 1
                previous = requests
        allpath = out / "all_models_frozen.json"
        if allpath.exists():
            allmodels = read(allpath)
            assert allmodels["test_outcomes_accessed"] is False
            assert allmodels["acquisition_schedule_sha256"] == digest(schedulepath)
            for name, checksum in allmodels["models"].items():
                assert digest(out / "models" / (name + ".json")) == checksum
            for receiptpath in (root / "physics" / task / "test").glob(
                "*/policy_screen.execution.json"
            ):
                assert read(receiptpath)["started_epoch"] >= allmodels["epoch"]
                counts["all_models_frozen_before_test"] += 1
        for path in (out / "models").glob("*.json"):
            model = read(path)
            if path.stem == "logged":
                expectedlogs = {
                    p.stem for p in (out / "learner_records/calibration").glob("*.json")
                }
                assert (
                    set(model["log_parent_ids"]) == expectedlogs
                    and not model["pair_parent_ids"]
                )
            for leaf in model["leaves"].values():
                a, b = constraints(leaf["evidence"])
                for name, objective, maximize in (
                    ("harm_lower", [0, 0, 1, 0], False),
                    ("harm_upper", [0, 0, 1, 0], True),
                    ("gain_lower", [0, 1, -1, 0], False),
                    ("gain_upper", [0, 1, -1, 0], True),
                    ("failure_upper", [1, 0, 1, 0], True),
                ):
                    vector = np.asarray(objective)
                    result = linprog(
                        -vector if maximize else vector,
                        A_ub=a,
                        b_ub=b,
                        A_eq=np.ones((1, 4)),
                        b_eq=[1],
                        bounds=(0, None),
                        method="highs",
                    )
                    assert result.success
                    q = feasible(leaf["bounds"]["optimizers"][name], a, b)
                    error = max(
                        abs(vector @ result.x - leaf["bounds"][name]),
                        abs(vector @ q - leaf["bounds"][name]),
                    )
                    maxerror = max(maxerror, float(error))
                    assert error < 1e-9
                    counts["all_objective_extrema_and_optimizers"] += 1
                witness = leaf["diagnosis"]
                if witness["favorable"] is not None:
                    favorable = feasible(witness["favorable"], a, b)
                    unfavorable = feasible(witness["unfavorable"], a, b)
                    for vector in ([0, 0, 1, 1], [0, 1, 0, 1]):
                        assert abs(np.dot(favorable - unfavorable, vector)) < 1e-9
                    assert (
                        favorable[2] <= 0.1 + 1e-9
                        and favorable[1] - favorable[2] >= 0.05 - 1e-9
                    )
                    assert unfavorable[2] > 0.1
                    counts["constructive_same_marginal_world_pairs"] += 1
        tasks[task] = {
            "acquisition": "INDEPENDENT_TIMING_MEMBERSHIP_AND_LEAF_EXCHANGEABILITY_CHECKED",
            "source_failures": failures,
        }
    assert not any(n.startswith("dual_rec.evidence_aware") for n in sys.modules)
    result = {
        "passed": True,
        "counts": dict(counts),
        "tasks": tasks,
        "max_numerical_error": maxerror,
        "production_inference_imported": False,
        "audit_source_sha256": digest(Path(__file__)),
        "limitation": "Checks the registered hash-random within-leaf inclusion and observed time order under the stated exchangeability assumptions; no cross-budget significance guarantee.",
    }
    with output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run(args.root, args.output or args.root / "independent_extended_audit.json")
