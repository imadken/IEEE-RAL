"""Independent offline reconstruction of assembly goals, source scope and option sets."""

import argparse
import json
import lzma
from pathlib import Path

import numpy as np
from rpd_assembly_contract import BASE, Job, active_registration_path, sha, write
from scipy.spatial.transform import Rotation


def matrix(raw):
    raw = np.asarray(raw)
    result = np.eye(4)
    result[:3, 3] = raw[:3]
    result[:3, :3] = Rotation.from_quat(raw[[4, 5, 6, 3]]).as_matrix()
    return result


def independently_goal(frame, length):
    hole, peg = matrix(frame["hole"]), matrix(frame["peg"])
    position = hole[:3, :3].T @ (peg[:3, 3] - hole[:3, 3])
    orientation = hole[:3, :3].T @ peg[:3, :3]
    tip = position + orientation[:, 0] * length
    angle = Rotation.from_matrix(orientation).magnitude()
    theta = np.arctan(0.0015 / length)
    return bool(
        abs(tip[0]) <= 0.015
        and max(abs(position[1]), abs(position[2])) <= 0.0015
        and angle <= theta
        and np.dot(frame["peg_linear_velocity"], frame["peg_linear_velocity"])
        <= 0.003**2
        and np.dot(frame["peg_angular_velocity"], frame["peg_angular_velocity"])
        <= theta**2
    )


def compare_roots(a, b):
    errors = []
    metrics = {
        "maximum_translation_m": 0.0,
        "maximum_rotation_rad": 0.0,
        "maximum_other_abs": 0.0,
    }

    def visit(x, y, name):
        if isinstance(x, dict):
            if not isinstance(y, dict) or set(x) != set(y):
                errors.append(name + ": keys differ")
                return
            for key in x:
                # Contact records can reorder without changing native state/forces.
                if key != "contacts_evaluator_only":
                    visit(x[key], y[key], name + "/" + key)
        elif isinstance(x, list):
            try:
                xx, yy = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
            except (ValueError, TypeError):
                if x != y:
                    errors.append(name)
                return
            if xx.shape != yy.shape:
                errors.append(name + ": shapes differ")
                return
            if xx.size:
                delta = float(np.max(np.abs(xx - yy)))
                metrics["maximum_other_abs"] = max(metrics["maximum_other_abs"], delta)
                if delta > 1e-5:
                    errors.append(name + ": numeric tolerance")
        elif isinstance(x, (float, int)) and not isinstance(x, bool):
            if abs(x - y) > (
                0 if "substep" in name or "tick" in name or "dwell" in name else 1e-5
            ):
                errors.append(name)
        elif x != y:
            errors.append(name)

    # Pose equivalence is quaternion-sign invariant, with the declared angular tolerance.
    for key in ("peg", "fixture", "hole", "tcp"):
        x, y = matrix(a["frame"][key]), matrix(b["frame"][key])
        dp = float(np.linalg.norm(x[:3, 3] - y[:3, 3]))
        dr = float(Rotation.from_matrix(x[:3, :3].T @ y[:3, :3]).magnitude())
        metrics["maximum_translation_m"] = max(metrics["maximum_translation_m"], dp)
        metrics["maximum_rotation_rad"] = max(metrics["maximum_rotation_rad"], dr)
        if dp > 1e-5 or dr > 1e-4:
            errors.append(key + ": pose tolerance")
    x = {
        **a,
        "frame": {
            k: v
            for k, v in a["frame"].items()
            if k not in ("peg", "fixture", "hole", "tcp")
        },
    }
    y = {
        **b,
        "frame": {
            k: v
            for k, v in b["frame"].items()
            if k not in ("peg", "fixture", "hole", "tcp")
        },
    }
    visit(x, y, "root")
    return {"passed": not errors, "errors": errors, **metrics}


def check_row(directory):
    directory = Path(directory)
    with lzma.open(directory / "result.json.xz", "rt") as stream:
        row = json.load(stream)
    job = Job.model_validate(row["job"])
    assert job.job_id == row["job_id"]
    frames = [
        json.loads(line)
        for line in (directory / "trace.jsonl").read_text().splitlines()
    ]
    assert len(frames) == row["actual_physics_substeps"]
    for i, frame in enumerate(frames, 1):
        assert frame["substep"] == i and frame["time_seconds"] == i / 100
        assert frame["native_ticks_before_increment"] == (i - 1) // 5
        assert np.isfinite(
            np.asarray(frame["qpos"] + frame["qvel"] + frame["peg"] + frame["tcp"])
        ).all()
        assert len(frame["online_X"]) == 28 and len(frame["online_Y_sample"]) == 23
        assert np.isclose(
            np.linalg.norm(frame["peg_fixture_force_vector_N"]),
            frame["peg_fixture_force_N"],
        )
    if row["status"] != "COMPLETE":
        return {
            "passed": False,
            "status": row["status"],
            "retained_frames": len(frames),
        }
    config = row["configuration"]
    if not frames:
        assert row["eligibility"]["disposition"] == "KNOWN_INELIGIBLE"
        assert any(
            reason.startswith("INITIAL_IK") for reason in row["eligibility"]["reasons"]
        )
        return {
            "passed": True,
            "source_complete": True,
            "root_available": False,
            "retained_frames": 0,
        }
    assert frames[-1]["substep"] in (150, 550)
    assert row["actual_control_ticks"] == len(frames) // 5
    dwell, completed = 0, False
    for frame in frames:
        valid = independently_goal(frame, config["length"])
        assert valid == all(frame["goal_components"].values())
        dwell = dwell + 1 if valid else 0
        completed |= dwell >= 26
        assert dwell == frame["goal_dwell"] and completed == frame["completion_flag"]
        checks = frame["constraint_checks"]
        assert checks["joint_speed"] == bool(
            max(abs(v) for v in frame["qvel"][:7]) <= 2
        )
        assert checks["tcp_residual"] == (frame["tcp_residual_m"] <= 0.012)
        assert checks["peg_fixture_force"] == (
            frame["peg_fixture_force_N"] <= 10 * config["peg_mass_kg"] * 9.81
        )
        e = np.linalg.inv(matrix(frame["tcp"])) @ matrix(frame["peg"])
        reference = (
            row["initial_record"] if frame["substep"] <= 150 else row["root"]["frame"]
        )
        e0 = np.linalg.inv(matrix(reference["tcp"])) @ matrix(reference["peg"])
        slip = np.linalg.inv(e0) @ e
        assert np.isclose(
            np.linalg.norm(slip[:3, 3]), frame["grasp_slip_translation_m"], atol=1e-10
        )
        assert np.isclose(
            Rotation.from_matrix(slip[:3, :3]).magnitude(),
            frame["grasp_slip_rotation_rad"],
            atol=1e-8,
        )
        grasp = all(
            np.linalg.norm(f) >= 0.5
            and np.dot(f, d) / (np.linalg.norm(f) * np.linalg.norm(d))
            >= np.cos(np.deg2rad(85)) - 1e-7
            for f, d in zip(
                frame["finger_peg_forces_N"], frame["finger_opening_directions"]
            )
        )
        assert grasp == frame["native_grasp"]
    root = row["root"]["frame"]
    expected_reasons = []
    if row["root"]["completion_flag"]:
        expected_reasons.append("ALREADY_COMPLETED")
    if not root["native_grasp"]:
        expected_reasons.append("NO_NATIVE_TWO_FINGER_GRASP")
    if not all(f["peg_fixture_force_N"] >= 0.5 for f in frames[144:150]):
        expected_reasons.append("NO_PERSISTENT_REGISTERED_CONTACT")
    if not 0.00075 <= root["tcp_residual_m"] <= 0.012:
        expected_reasons.append("ROOT_TCP_RESIDUAL_OUTSIDE_REGISTERED_RANGE")
    expected_reasons += [
        "ROOT_" + name
        for name, passed in root["constraint_checks"].items()
        if not passed
    ]
    assert row["eligibility"]["reasons"] == expected_reasons
    assert (not expected_reasons) == (
        row["eligibility"]["disposition"] == "KNOWN_ELIGIBLE"
    )
    if "terminal" in row:
        assert len(frames) == 550 and row["terminal"]["completion"] == completed
        prefix = [root] + frames[150:200]
        path = [root] + frames[150:]
        assert row["terminal"]["diagnostic_path_compliant"] == all(
            all(f["constraint_checks"].values()) for f in prefix
        )
        assert row["terminal"]["whole_postroot_compliant"] == all(
            all(f["constraint_checks"].values()) for f in path
        )
    return {
        "passed": True,
        "source_complete": True,
        "root_available": True,
        "retained_frames": len(frames),
        "independent_goal_recomputation": True,
        "independent_eligibility_recomputation": True,
        "root_contact_N": root["peg_fixture_force_N"],
        "root_grasp": root["native_grasp"],
    }


def summarize():
    registration = json.loads(active_registration_path().read_text())
    entries = []
    for path in sorted((BASE / "episodes").glob("*/process.json")):
        process = json.loads(path.read_text())
        result = path.parent / "result.json.xz"
        checked = (
            check_row(path.parent)
            if result.exists()
            else {"passed": False, "status": "MISSING_SOURCE_RESULT"}
        )
        row = None
        if result.exists():
            with lzma.open(result, "rt") as stream:
                row = json.load(stream)
        entries.append(
            {
                "directory": str(path.parent),
                "process": process,
                "independent_audit": checked,
                "row": row,
            }
        )
    output = {
        "source_registration_sha256": sha(active_registration_path()),
        "candidate_counts": {},
        "actual_source_episodes": len(entries),
        "actual_worker_seconds": sum(e["process"]["wall_seconds"] for e in entries),
        "native_crashes": sum(e["process"]["returncode"] == -11 for e in entries),
        "missing_source_results": sum(e["row"] is None for e in entries),
        "source_errors": sum(
            e["row"] is not None and e["row"]["status"] != "COMPLETE" for e in entries
        ),
        "all_existing_rows_independently_verified": all(
            e["independent_audit"]["passed"] for e in entries
        ),
        "confirmation_attempts": 0,
        "H1_validated": False,
        "H2_validated": False,
        "method": registration["method"],
        "parents": [],
    }
    for candidate in registration["candidates"]:
        matches = [
            e
            for e in entries
            if e["row"]
            and e["row"]["job"]["candidate"]["candidate_id"]
            == candidate["candidate_id"]
        ]
        screen = next(
            (
                e
                for e in matches
                if e["row"]["job"]["intervention"] == "screen"
                and e["row"]["status"] == "COMPLETE"
            ),
            None,
        )
        if screen:
            disposition = screen["row"]["eligibility"]["disposition"]
        elif any(
            e["process"]["candidate_id"] == candidate["candidate_id"] for e in entries
        ):
            disposition = "UNKNOWN"
        else:
            disposition = "NOT_ATTEMPTED"
        parent = {
            "candidate_id": candidate["candidate_id"],
            "phase": candidate["phase"],
            "disposition": disposition,
            "screen_reasons": screen["row"]["eligibility"].get("reasons", [])
            if screen
            else [],
            "matched_branches": {},
            "option_comparisons": [],
        }
        roots = []
        for e in matches:
            row = e["row"]
            if screen and row["root"]:
                parity = compare_roots(screen["row"]["root"], row["root"])
                roots.append(parity)
            job = row["job"]
            if (
                job["intervention"] != "screen"
                and job["repeat"] == 0
                and "terminal" in row
            ):
                parent["matched_branches"][
                    job["intervention"] + "/" + job["action"]
                ] = {
                    **row["terminal"],
                    "source_trace": e["directory"] + "/trace.jsonl",
                    "trace_sha256": sha(Path(e["directory"]) / "trace.jsonl"),
                    "source_valid": e["independent_audit"]["passed"]
                    and all(r["passed"] for r in roots),
                }
        parent["all_root_replays_passed"] = (
            all(r["passed"] for r in roots) if roots else None
        )
        for p in ("preload", "dither"):
            branches = parent["matched_branches"]
            required = [p + "/" + a for a in ("a0", "a1")] + [
                "hold/" + a for a in ("a0", "a1")
            ]
            if not all(k in branches and branches[k]["source_valid"] for k in required):
                continue
            kp = [a for a in ("a0", "a1") if branches[p + "/" + a]["completion"]]
            kh = [a for a in ("a0", "a1") if branches["hold/" + a]["completion"]]
            compliant = all(branches[k]["diagnostic_path_compliant"] for k in required)
            parent["option_comparisons"].append(
                {
                    "probe": p,
                    "K_hold": kh,
                    "K_probe": kp,
                    "individual_options_lost": sorted(set(kh) - set(kp)),
                    "individual_options_created": sorted(set(kp) - set(kh)),
                    "full_erasure": bool(kh) and not kp,
                    "full_creation": not kh and bool(kp),
                    "probe_and_hold_compliant": compliant,
                    "joint_compliant_erasure": bool(kh) and not kp and compliant,
                }
            )
        output["parents"].append(parent)
    for phase, count in (("qual", 12), ("exploratory", 24)):
        parents = [p for p in output["parents"] if p["phase"] == phase]
        output["candidate_counts"][phase] = {
            "fixed": count,
            **{
                key: sum(p["disposition"] == key for p in parents)
                for key in (
                    "KNOWN_ELIGIBLE",
                    "KNOWN_INELIGIBLE",
                    "UNKNOWN",
                    "NOT_ATTEMPTED",
                )
            },
            "complete_probe_hold_comparisons": sum(
                len(p["option_comparisons"]) for p in parents
            ),
            "full_erasures": sum(
                c["full_erasure"] for p in parents for c in p["option_comparisons"]
            ),
            "joint_compliant_erasures": sum(
                c["joint_compliant_erasure"]
                for p in parents
                for c in p["option_comparisons"]
            ),
        }
    output["attempts"] = [{k: v for k, v in e.items() if k != "row"} for e in entries]
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize()
    write(args.output, report)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("parents", "attempts")}
        )
    )
