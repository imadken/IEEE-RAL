"""Independent numerical and recorded-physics audit; no production solver import."""

import argparse
import gzip
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def read(p):
    if str(p).endswith(".gz"):
        with gzip.open(p, "rt") as f:
            return json.load(f)
    return json.loads(p.read_text())


def save(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        json.dump(v, f, indent=2)
        f.write("\n")


def numerical(root, relocated=False):
    path = Path("research/dsre_evidence_design/supervisor_reference.py")
    spec = importlib.util.spec_from_file_location("reference_oracle", path)
    ref = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = ref
    spec.loader.exec_module(ref)
    cases = 0
    largest = 0.0
    certificates = 0
    accesses = 0
    for file in sorted((root / "models").glob("*.json")):
        model = read(file)
        partition = model["partition"]
        space = list(
            itertools.product((False, True), repeat=len(partition["vocabulary"]))
        )
        good = set()
        for c, leaf in model["leaves"].items():
            e = leaf["evidence"]
            b = leaf["bounds"]
            if b is None:
                continue
            p0 = ref.Band(**e["p0"])
            p1 = ref.Band(**e["p1"])
            extras = {
                k: ref.Band(**e[k]) for k in ("harm", "rescue") if e[k] is not None
            }
            for field, vector, maximize in (
                ("harm_lower", ref.HARM, False),
                ("harm_upper", ref.HARM, True),
                ("gain_lower", ref.GAIN, False),
                ("gain_upper", ref.GAIN, True),
                ("failure_upper", np.array([1, 0, 1, 0]), True),
            ):
                want, _ = ref.joint_extreme(p0, p1, vector, maximize=maximize, **extras)
                largest = max(largest, abs(want - b[field]))
                assert abs(want - b[field]) < 1e-8
                q = np.asarray(b["optimizers"][field])
                assert q.min() >= -1e-9 and abs(q.sum() - 1) < 1e-8
                for v, band in (
                    (ref.P0, p0),
                    (ref.P1, p1),
                    (ref.HARM, extras.get("harm")),
                    (ref.RESCUE, extras.get("rescue")),
                ):
                    if band:
                        assert band.lo - 1e-8 <= v @ q <= band.hi + 1e-8
                cases += 1
            if b["harm_upper"] <= 0.1 + 1e-10 and b["gain_lower"] >= 0.05 - 1e-10:
                good.add(int(c))
        for row in model["decisions"]:
            cert = row["certificate"]
            if not cert:
                continue
            # Independent oracle examines every conjunction over the entire cube.
            query = next(
                x
                for x in space
                if all(
                    x[partition["vocabulary"].index(n)] == v
                    for n, v in cert["evidence"]
                )
                and partition["cells"][space.index(x)] == row["leaf"]
            )
            want = ref.minimal_certificate(query, partition["cells"], good)
            got = tuple(partition["vocabulary"].index(n) for n, v in cert["evidence"])
            assert got == want
            mask = [all(x[i] == query[i] for i in got) for x in space]
            scope = {partition["cells"][i] for i, v in enumerate(mask) if v}
            assert scope == set(cert["selected_leaf_scope"]) and scope <= good
            certificates += 1
        whitelist = set(model["input_whitelist_sha256"])
        for name in model["successful_data_reads"]:
            direct = name in {str(Path(n).resolve()) for n in whitelist}
            moved = relocated and any(
                not Path(n).is_absolute() and name.endswith("/" + Path(n).as_posix())
                for n in whitelist
            )
            assert direct or moved
            assert "/evaluator/" not in name
            if model["regime"] in ("logged", "observational"):
                assert "/paired_refinement/" not in name
            accesses += 1
    assert not any(n.startswith("dual_rec.evidence_aware") for n in sys.modules)
    save(
        root / "independent_numerical_audit.json",
        {
            "passed": True,
            "LP_extrema_checked": cases,
            "max_error": largest,
            "minimum_scope_certificates_checked": certificates,
            "whitelisted_reads_checked": accesses,
            "production_solver_imported": False,
        },
    )


def canonical_contacts(value):
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return [canonical_contacts(v) for v in value]
    if isinstance(value, dict) and "contacts" in value:
        contacts = value["contacts"]
        if contacts and isinstance(contacts[0][0], str):
            contacts = sorted(
                [[*sorted(row[:2]), *row[2:]] for row in contacts], key=repr
            )
            return dict(value, contacts=contacts)
    return value


def equal(a, b):
    # Native contact enumeration order is not a physical state channel.
    # Canonicalize actor-pair order; every numeric value remains exact.
    assert canonical_contacts(a) == canonical_contacts(b), (
        "Full recorded state/controller/contact replay mismatch"
    )


def control_nav(before, route, index):
    pos = np.asarray(before["observation"][:2])
    vel = np.asarray(before["observation"][2:4])
    while (
        index < len(route) - 1 and np.linalg.norm(np.asarray(route[index]) - pos) <= 0.2
    ):
        index += 1
    return np.clip(2 * (np.asarray(route[index]) - pos) - 0.8 * vel, -1, 1).astype(
        np.float32
    ).tolist(), index


def check_nav(branch):
    assert branch["horizon"] == 200 and branch["episodic"]
    prefix = branch["prefix"]
    controls = branch["prefix_controls"]
    assert len(controls) == 20 and len(prefix) == 21
    index = 0
    for before, command in zip(prefix, controls):
        want, index = control_nav(before["obs"], before["route"], index)
        equal(want, command)
    before = branch["checkpoint"]
    index = 0 if branch["action"] == "r" else before["index"]
    route = branch["post"][0]["route"]
    assert route[-1] == before["goal"]
    for state, command in zip(branch["post"], branch["post_controls"], strict=True):
        want, index = control_nav(before["obs"], route, index)
        equal(want, command)
        assert abs(state["time"] - before["time"] - 0.01) < 1e-10
        before = state
    distance = np.linalg.norm(
        np.asarray(before["obs"]["achieved_goal"])
        - np.asarray(before["obs"]["desired_goal"])
    )
    assert branch["success"] == bool(distance <= 0.45)
    assert len(branch["post"]) <= 200
    assert branch["success"] or len(branch["post"]) == 200


def check_peg(branch, geometry):
    from scipy.spatial.transform import Rotation

    assert geometry["initial_physical"] == branch["prefix"][0]["physical"]
    length = geometry["peg_half_sizes"][0][0]
    radius = geometry["hole_radii"][0]
    state = branch["post"][-1]
    peg = np.asarray(state["peg"][0])
    hole = np.asarray(state["hole"][0])
    rotation = lambda q: Rotation.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    head = peg[:3] + rotation(peg[3:])[:, 0] * length
    local = rotation(hole[3:]).T @ (head - hole[:3])
    success = bool(
        local[0] >= -0.015 and abs(local[1]) <= radius and abs(local[2]) <= radius
    )
    assert success == branch["success"]
    previous = branch["checkpoint"]["elapsed"][0]
    for packet in branch["post"]:
        assert packet["elapsed"][0] == previous + 1
        previous = packet["elapsed"][0]


def pilot(root, task, tag):
    folder = root / "physics" / task / ("pilot" + tag)
    counts = Counter()
    attempts = []
    classes = Counter()
    usable = []
    for index in range(10):
        d = folder / str(index)
        branches = {a: read(d / (a + ".json.gz")) for a in ("c", "r")}
        status = "FAILED"
        reason = None
        try:
            assert all(b["status"] == "COMPLETE" for b in branches.values())
            equal(branches["c"]["prefix"], branches["r"]["prefix"])
            equal(branches["c"]["prefix_controls"], branches["r"]["prefix_controls"])
            equal(branches["c"]["checkpoint"], branches["r"]["checkpoint"])
            equal(branches["c"]["features"], branches["r"]["features"])
            for a, b in branches.items():
                repeat = read(d / (a + "_repeat.json.gz"))
                assert repeat["status"] == "COMPLETE"
                for key in (
                    "prefix",
                    "prefix_controls",
                    "checkpoint",
                    "features",
                    "post",
                    "post_controls",
                    "success",
                ):
                    equal(b[key], repeat[key])
                if task == "PointMaze_UMaze-v3":
                    check_nav(b)
                else:
                    assert b["horizon"] == 400 and len(b["post"]) == 400
                    assert len(b["prefix"]) == len(b["prefix_controls"]) + 1
                    assert len(b["post_controls"]) == 400
                    assert (
                        "drive_velocities" in b["checkpoint"]
                        and "controller_transient" in b["checkpoint"]
                    )
                    geometry = read(
                        root / "geometry/pilot" / (str(b["spec"]["seed"]) + ".json")
                    )
                    check_peg(b, geometry)
                counts["prefix_states"] += len(b["prefix"])
                counts["future_states"] += len(b["post"])
                counts["branches"] += 1
            status = "QUALIFIED"
            usable.append(index)
            classes[
                f"{int(branches['c']['success'])}{int(branches['r']['success'])}"
            ] += 1
        except (AssertionError, FileNotFoundError, KeyError) as error:
            reason = str(error) or "Incomplete checkpoint or branch"
        attempts.append(
            {
                "index": index,
                "seed": branches["c"]["spec"]["seed"],
                "status": status,
                "reason": reason,
                "branch_status": {a: b["status"] for a, b in branches.items()},
            }
        )
    save(
        root / (task + "-qualification" + tag + ".json"),
        {
            "technical_pass": len(usable) >= 8,
            "usable_parents": len(usable),
            "usable_indices": usable,
            "attempts": attempts,
            "counts": dict(counts),
            "four_cell_counts": dict(classes),
            "replay_criterion": "exact equality of every recorded prefix/controller/contact state and repeated action/future state",
            "scope": "technical task qualification, outcome diversity reported separately; DEVELOPMENT",
        },
    )
    print(task, len(usable), dict(classes), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=("numerical", "pilot"))
    p.add_argument("root", type=Path)
    p.add_argument("--task")
    p.add_argument("--relocated", action="store_true")
    p.add_argument("--tag", default="-interface2")
    a = p.parse_args()
    if a.stage == "numerical":
        numerical(a.root, a.relocated)
    else:
        pilot(a.root, a.task, a.tag)
