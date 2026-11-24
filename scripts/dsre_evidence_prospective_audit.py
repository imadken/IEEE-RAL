"""Independent provenance, physical, exact-binomial and certificate audit.

No production inference, prospective collector, or simulator module is imported.
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from dsre_evidence_audit import check_nav, check_peg, equal, read, save
from dsre_evidence_statistical_audit import cp


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parent(spec):
    return hashlib.sha256(
        f"prospective-parent:{spec['task']}:{spec['seed']}".encode()
    ).hexdigest()


def assign(task, number):
    return ("c", "r")[
        int.from_bytes(
            hashlib.sha256(f"dsre-evidence-v2:arm:{task}:{number}".encode()).digest(),
            "big",
        )
        % 2
    ]


def cell(partition, x):
    if x is None or any(v is None for v in x):
        return None
    return partition["cells"][sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))]


def check_grasp(branch):
    from dsre_source_risk_audit import difference, expected_action, vec

    assert len(branch["post"]) == 70
    previous = branch["checkpoint"]
    for j, (command, state) in enumerate(
        zip(branch["post_controls"], branch["post"], strict=True)
    ):
        want = expected_action(
            "PickCube-v1",
            "continue" if branch["action"] == "c" else "recover",
            j,
            previous["observation"],
            branch["initial_tcp"],
        )
        assert difference(command, want) < 2e-6
        assert abs(state["time"] - previous["time"] - 0.05) < 1e-8
        previous = state
    obs = previous["observation"]
    qvel = np.asarray(obs["agent"]["qvel"]).reshape(-1)[:-2]
    assert branch["success"] == bool(
        np.linalg.norm(vec(obs, "obj_pose") - vec(obs, "goal_pos")) <= 0.025
        and np.max(abs(qvel)) <= 0.2
    )


def physical(branch, task):
    if task == "PointMaze_UMaze-v3":
        check_nav(branch)
    elif task == "PickCube-v1":
        check_grasp(branch)
    else:
        if branch["status"] == "OBSERVED_ABORT_ENDPOINT":
            from scipy.spatial.transform import Rotation

            terminal = branch["terminal"]
            peg, hole = np.asarray(terminal["peg"][0]), np.asarray(terminal["hole"][0])

            def rotation(q):
                return Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()

            length = branch["geometry"]["peg_half_sizes"][0][0]
            radius = branch["geometry"]["hole_radii"][0]
            head = peg[:3] + rotation(peg[3:])[:, 0] * length
            local = rotation(hole[3:]).T @ (head - hole[:3])
            assert branch["success"] == bool(
                local[0] >= -0.015
                and abs(local[1]) <= radius
                and abs(local[2]) <= radius
            )
            assert branch["action_stopped"] and branch["terminal_observed"]
            assert (
                len(branch["post"])
                == len(branch["post_controls"])
                == branch["executed_controls"]
                <= 400
            )
            elapsed = branch["checkpoint"]["elapsed"][0]
            for packet in branch["post"]:
                assert packet["elapsed"][0] == elapsed + 1
                elapsed += 1
            assert terminal["elapsed"][0] == elapsed
        else:
            check_peg(branch, branch["geometry"])
        assert branch["feature_telemetry"][4] is None
        assert branch["features"] == [
            v for i, v in enumerate(branch["feature_telemetry"]) if i != 4
        ]
        if branch["status"] == "COMPLETE":
            assert len(branch["post_controls"]) == 400


def audit(root, task, numerical_only=False, relocated=False, output=None):
    out = root / "prospective" / task
    counts = Counter()
    failures = []
    maxerror = 0.0
    bands = 0
    certificates = 0
    extrema = 0
    if not numerical_only:
        for phase in ("discovery", "calibration", "test"):
            for path in sorted((out / phase).glob("*.json")):
                record = read(path)
                spec = record["spec"]
                pid = record["parent_id"]
                assert parent(spec) == pid
                assert spec["phase"] == phase and task == spec["task"]
                d = root / "physics" / task / phase / str(spec["index"])
                if record["status"] == "ALREADY_SOLVED_PREFIX":
                    label = (
                        "policy_screen" if phase == "test" else "randomized_assigned"
                    )
                    branch = read(d / f"{label}.json.gz")
                    assert (
                        branch["status"] == "ALREADY_SOLVED_PREFIX"
                        and branch["success"] is True
                    )
                    assert (
                        branch["features"] is None
                        and len(branch["prefix_controls"]) <= 20
                    )
                    last = branch["prefix"][-1]["obs"]
                    assert (
                        np.linalg.norm(
                            np.asarray(last["achieved_goal"])
                            - np.asarray(last["desired_goal"])
                        )
                        <= 0.45
                    )
                    assert record.get("y") is True and "record" not in record
                    assert not (
                        out / "learner_records" / phase / f"{pid}.json"
                    ).exists()
                    counts[phase + "_observed_absorbing_prefix"] += 1
                    if phase != "test":
                        assert (
                            branch["action"]
                            == record["action"]
                            == assign(task, spec["seed"])
                        )
                    if phase == "calibration":
                        screening = read(d / "acquisition_screen.json.gz")
                        assert screening["status"] == "ALREADY_SOLVED_PREFIX"
                        equal(screening["prefix"], branch["prefix"])
                        equal(screening["prefix_controls"], branch["prefix_controls"])
                    if phase == "test":
                        assert (
                            record["precheckpoint_absorption"]
                            and not record["selected_future_executed"]
                        )
                        assert record["action"] == "c"
                        other = read(d / "evaluator_counterpart.json.gz")
                        equal(branch["prefix"], other["prefix"])
                        equal(branch["prefix_controls"], other["prefix_controls"])
                        assert (
                            other["status"] == "ALREADY_SOLVED_PREFIX"
                            and other["success"] is True
                        )
                        receipt = read(d / "evaluator_counterpart.execution.json")
                        assert record["epoch"] <= receipt["started_epoch"]
                    continue
                if record["status"] not in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                    failures.append(
                        {
                            "phase": phase,
                            "index": spec["index"],
                            "status": record["status"],
                        }
                    )
                    continue
                label = "selected_policy" if phase == "test" else "randomized_assigned"
                branch = read(d / f"{label}.json.gz")
                receipt = read(d / f"{label}.execution.json")
                assert (
                    branch["action"] == record["action"]
                    and branch["success"] == record["y"]
                )
                assert branch["features"] == record["x"]
                physical(branch, task)
                assert receipt["finished_epoch"] <= record["epoch"]
                counts[phase] += 1
                if phase != "test":
                    log = record["record"]
                    assert log["propensity"] == 0.5 and not log["counterpart_exposed"]
                    assert log["action"] == assign(task, spec["seed"])
                    assert (
                        not {
                            "yc",
                            "yr",
                            "condition",
                            "offset",
                            "seed",
                            "oracle",
                            "fault",
                        }
                        & log.keys()
                    )
                    assert not (d / "evaluator_counterpart.json.gz").exists()
                if phase == "calibration":
                    schedule = read(out / "acquisition_schedule.json")
                    assert schedule["epoch"] <= receipt["started_epoch"]
                    screen = read(d / "acquisition_screen.json.gz")
                    for k in ("prefix", "prefix_controls", "checkpoint", "features") + (
                        ("controller_memory",) if task == "PickCube-v1" else ()
                    ):
                        equal(screen[k], branch[k])
                if phase == "test":
                    screened = read(d / "policy_screen.json.gz")
                    for key in (
                        "prefix",
                        "prefix_controls",
                        "checkpoint",
                        "features",
                    ) + (("controller_memory",) if task == "PickCube-v1" else ()):
                        equal(screened[key], branch[key])
                    observation = read(out / "online_observations" / f"{pid}.json")
                    assert observation["x"] == branch["features"]
                    frozen = read(out / "all_models_frozen.json")
                    decision = read(out / "online_decisions" / f"{pid}.json")
                    assert (
                        frozen["epoch"]
                        <= decision["selected_before_execution_epoch"]
                        <= receipt["started_epoch"]
                    )
                    assert (
                        decision["action"] == record["action"]
                        and decision["model_sha256"] == frozen["models"]["logged"]
                    )
                    assert all(
                        "/evaluator/" not in p
                        for p in decision["successful_data_reads"]
                    )
                    counterpath = d / "evaluator_counterpart.json.gz"
                    if counterpath.exists():
                        other = read(counterpath)
                        cr = read(d / "evaluator_counterpart.execution.json")
                        assert record["epoch"] <= cr["started_epoch"]
                        if other["status"] in ("COMPLETE", "OBSERVED_ABORT_ENDPOINT"):
                            for k in (
                                "prefix",
                                "prefix_controls",
                                "checkpoint",
                                "features",
                            ):
                                equal(branch[k], other[k])
                            physical(other, task)
                            counts["test_pairs"] += 1
                        else:
                            failures.append(
                                {
                                    "phase": "test_counterpart",
                                    "index": spec["index"],
                                    "status": other["status"],
                                }
                            )
        for path in sorted((out / "screens").glob("*.json")):
            record = read(path)
            spec = record["spec"]
            raw = read(
                root
                / "physics"
                / task
                / "calibration"
                / str(spec["index"])
                / "acquisition_screen.json.gz"
            )
            assert raw["status"] == record["status"]
            if raw["status"] == "CHECKPOINT_ONLY":
                assert raw["features"] == record["x"]
                counts["calibration_screens_with_checkpoint"] += 1
            else:
                witness = {
                    "phase": "calibration_screen",
                    "index": spec["index"],
                    "seed": spec["seed"],
                    "status": raw["status"],
                    "prefix_controls": len(raw.get("prefix_controls", [])),
                    "terminal_success_observed": raw.get("success"),
                    "valid_recovery_checkpoint": False,
                }
                if raw["status"] == "ALREADY_SOLVED_PREFIX":
                    last = raw["prefix"][-1]["obs"]
                    assert (
                        np.linalg.norm(
                            np.asarray(last["achieved_goal"])
                            - np.asarray(last["desired_goal"])
                        )
                        <= 0.45
                    )
                    assert raw["success"] is True and len(raw["prefix_controls"]) <= 20
                    witness["missing_terminal_label"] = False
                    witness["classification"] = (
                        "expected precheckpoint attrition with observed success"
                    )
                    witness["hard_source_failure"] = False
                failures.append(witness)
                counts["calibration_screens_without_checkpoint"] += 1
        schedulepath = out / "acquisition_schedule.json"
        if schedulepath.exists():
            schedule = read(schedulepath)
            for budgets in schedule["schedules"].values():
                prior = []
                for budget, requests in budgets.items():
                    assert sum(r["cost"] for r in requests) <= int(budget)
                    assert all(
                        r["cost"] == (2 if r["kind"] == "pair" else 1) for r in requests
                    )
                    assert requests[: len(prior)] == prior
                    assert len({r["parent_id"] for r in requests}) == len(requests)
                    assert all(
                        r["parent_id"] in schedule["candidate_ids"] for r in requests
                    )
                    prior = requests
                for name in schedule["successful_data_reads"]:
                    assert (
                        "/learner_observations/calibration/" in name
                        or "/learner/discovery.json" in name
                        or name.endswith("/discovery_freeze.json")
                    )
            scheduledpairs = {
                r["parent_id"]
                for b in schedule["schedules"].values()
                for r in b["512"]
                if r["kind"] == "pair"
            }
            for file in (out / "acquisition_pairs").glob("*.json"):
                entry = read(file)
                pid = entry["pair"]["parent_id"]
                assert pid in scheduledpairs
                assert entry["schedule_sha256"] == digest(schedulepath)
                original = read(out / "calibration" / f"{pid}.json")
                d = (
                    root
                    / "physics"
                    / task
                    / "calibration"
                    / str(original["spec"]["index"])
                )
                receipt = read(d / "acquisition_counterpart.execution.json")
                assert (
                    schedule["epoch"] <= original["epoch"] <= receipt["started_epoch"]
                )
                first = read(d / "randomized_assigned.json.gz")
                other = read(d / "acquisition_counterpart.json.gz")
                for key in ("prefix", "prefix_controls", "checkpoint", "features") + (
                    ("controller_memory",) if task == "PickCube-v1" else ()
                ):
                    equal(first[key], other[key])
                physical(other, task)
                counts["acquisition_pairs"] += 1
    # Independent source oracle and direct binomial-CDF inversion.
    reference = Path("research/dsre_evidence_design/supervisor_reference.py")
    spec = importlib.util.spec_from_file_location("independent_reference", reference)
    ref = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = ref
    spec.loader.exec_module(ref)
    for path in sorted((out / "models").glob("*.json")):
        model = read(path)
        partition = model["partition"]
        good = set()
        logs = [
            read(out / "calibration" / f"{pid}.json")["record"]
            for pid in model["log_parent_ids"]
        ]
        pairs = [
            read(out / "acquisition_pairs" / f"{pid}.json")["pair"]
            for pid in model["pair_parent_ids"]
        ]
        for input_path, checksum in model["input_whitelist_sha256"].items():
            assert digest(Path(input_path)) == checksum
        whitelist_absolute = {
            str(Path(p).resolve()) for p in model["input_whitelist_sha256"]
        }
        for accessed in model["successful_data_reads"]:
            counts["whitelisted_data_reads"] += 1
            assert accessed in whitelist_absolute or (
                relocated
                and any(
                    not Path(p).is_absolute() and accessed.endswith("/" + p)
                    for p in model["input_whitelist_sha256"]
                )
            )
            assert "/evaluator/" not in accessed
            if "/paired_refinement/" in accessed:
                assert Path(accessed).stem in model["pair_parent_ids"]
            if "/calibration/" in accessed:
                assert Path(accessed).stem in model["log_parent_ids"]
        for c, leaf in model["leaves"].items():
            ls = [r for r in logs if cell(partition, r["x"]) == int(c)]
            ps = [r for r in pairs if cell(partition, r["x"]) == int(c)]
            tail = 0.025 / (4 * len(set(partition["cells"])))
            assert leaf["ledger"]["per_tail"] == tail
            groups = {
                n: [r["y"] for r in ls if r["action"] == a]
                for n, a in [("p0", "c"), ("p1", "r")]
            }
            if ps:
                groups.update(
                    harm=[r["yc"] and not r["yr"] for r in ps],
                    rescue=[not r["yc"] and r["yr"] for r in ps],
                )
            for name, ys in groups.items():
                lo, hi = cp(sum(ys), len(ys), tail)
                actual = leaf["evidence"][name]
                maxerror = max(maxerror, abs(lo - actual["lo"]), abs(hi - actual["hi"]))
                assert maxerror < 1e-10
                bands += 1
            e = leaf["evidence"]
            b = leaf["bounds"]
            extras = {
                name: ref.Band(**e[name])
                for name in ("harm", "rescue")
                if e[name] is not None
            }
            for field, v, maximize in [
                ("harm_upper", ref.HARM, True),
                ("gain_lower", ref.GAIN, False),
                ("failure_upper", np.array([1, 0, 1, 0]), True),
            ]:
                want, _ = ref.joint_extreme(
                    ref.Band(**e["p0"]),
                    ref.Band(**e["p1"]),
                    v,
                    maximize=maximize,
                    **extras,
                )
                maxerror = max(maxerror, abs(want - b[field]))
                assert abs(want - b[field]) < 1e-9
                extrema += 1
            if b["harm_upper"] <= 0.1 + 1e-10 and b["gain_lower"] >= 0.05 - 1e-10:
                good.add(int(c))
        evaluated = out / "evaluations" / path.name
        if evaluated.exists():
            results = read(evaluated)
            space = list(
                itertools.product((False, True), repeat=len(partition["vocabulary"]))
            )
            for row in results["decisions"]:
                cert = row["certificate"]
                assert (row["leaf"] in good) == (cert is not None)
                if cert:
                    query = read(out / "test" / f"{row['parent_id']}.json")["x"]
                    expected = ref.minimal_certificate(query, partition["cells"], good)
                    got = tuple(
                        partition["vocabulary"].index(n) for n, v in cert["evidence"]
                    )
                    assert got == expected
                    scope = {
                        partition["cells"][i]
                        for i, x in enumerate(space)
                        if all(x[j] == query[j] for j in got)
                    }
                    assert scope == set(cert["selected_leaf_scope"]) and scope <= good
                    assert (
                        abs(
                            cert["harm_upper"]
                            - max(
                                model["leaves"][str(c)]["bounds"]["harm_upper"]
                                for c in scope
                            )
                        )
                        < 1e-12
                    )
                    assert (
                        abs(
                            cert["gain_lower"]
                            - min(
                                model["leaves"][str(c)]["bounds"]["gain_lower"]
                                for c in scope
                            )
                        )
                        < 1e-12
                    )
                    assert cert["outcome_scope"] == model["source_scope"]
                    for dropped in got:
                        keep = tuple(i for i in got if i != dropped)
                        flags = {}
                        for index, x in enumerate(space):
                            flags.setdefault(partition["cells"][index], set()).add(
                                all(x[i] == query[i] for i in keep)
                            )
                        if any(len(v) > 1 for v in flags.values()):
                            expected_witness = "conjunction splits a calibrated leaf"
                        else:
                            admitted = {c for c, v in flags.items() if True in v}
                            expected_witness = "unqualified leaves admitted: " + str(
                                sorted(admitted - good)
                            )
                        assert (
                            cert["removal_witnesses"][partition["vocabulary"][dropped]]
                            == expected_witness
                        )
                    certificates += 1
            decisions = results["decisions"]
            n = len(decisions)
            rng = np.random.Generator(np.random.PCG64(2026111702))
            draws = rng.integers(0, n, (2000, n)) if n else None
            for method, metrics in results["policies"].items():
                matrix = []
                for decision in decisions:
                    pair = read(out / "evaluator" / f"{decision['parent_id']}.json")
                    c, r = int(pair["yc"]), int(pair["yr"])
                    recover = decision["actions"][method] == "r"
                    y = r if recover else c
                    matrix.append(
                        [
                            recover,
                            y,
                            y - c,
                            recover * c * (1 - r),
                            recover * (1 - c) * r,
                            recover * (1 - c) * (1 - r),
                        ]
                    )
                array = np.asarray(matrix, dtype=int)
                total = array.sum(axis=0)
                for field, index in (
                    ("recover", 0),
                    ("success", 1),
                    ("gain_total", 2),
                    ("harm", 3),
                    ("required_rescues", 4),
                    ("futile", 5),
                ):
                    assert metrics[field] == int(total[index])
                    counts["independent_metric_counts"] += 1
                weights = np.asarray([np.bincount(draw, minlength=n) for draw in draws])
                want = np.percentile(weights @ array[:, 2] / n, [2.5, 97.5])
                assert (
                    np.max(abs(want - np.asarray(metrics["gain_parent_bootstrap95"])))
                    < 1e-12
                )
                lo, hi = cp(int(total[3]), int(total[0]), 0.025)
                band = metrics["harm_per_recover_CP95"]
                assert max(abs(lo - band["lo"]), abs(hi - band["hi"])) < 1e-10
                counts["independent_metric_intervals"] += 4
            counts["scored_models"] += 1
    assert not any(name.startswith("dual_rec.evidence_aware") for name in sys.modules)
    save(
        output
        or out
        / (
            "independent_compact_audit.json"
            if numerical_only
            else "independent_prospective_audit_full.json"
        ),
        {
            "passed": True,
            "task": task,
            "counts": dict(counts),
            "qualification_failures": failures,
            "CP_bands": bands,
            "LP_extrema": extrema,
            "minimum_certificates": certificates,
            "max_numerical_error": maxerror,
            "production_inference_imported": False,
            "audit_source_sha256": digest(Path(__file__)),
        },
    )
    print(
        json.dumps(
            {
                "audit": task,
                "counts": dict(counts),
                "CP_bands": bands,
                "failures": failures,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--task", required=True)
    p.add_argument("--numerical-only", action="store_true")
    p.add_argument("--relocated", action="store_true")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    audit(a.root, a.task, a.numerical_only, a.relocated, a.output)
