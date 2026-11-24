"""Independent measured-trace audit for nominal development; no simulator imports."""

import argparse
import hashlib
import json
import lzma
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp


def rigid(raw):
    a = np.asarray(raw)
    t = np.eye(4)
    t[:3, 3] = a[:3]
    t[:3, :3] = Rotation.from_quat(a[[4, 5, 6, 3]]).as_matrix()
    return t


def check(directory):
    row = json.loads(lzma.decompress((directory / "result.json.xz").read_bytes()))
    raw = (directory / "trace.jsonl").read_bytes()
    frames = [json.loads(line) for line in raw.splitlines()]
    config = row["configuration"]
    length = config["length"]
    theta = np.arctan(0.0015 / length)
    dwell = 0
    success = False
    limits = np.asarray(config["joint_limits"]).reshape(9, 2)
    violations = {k: [] for k in frames[0]["constraint_checks"]}
    for i, frame in enumerate(frames, 1):
        assert frame["substep"] == i and frame["time_seconds"] == i / 100
        assert frame["native_ticks_before_increment"] == (i - 1) // 5
        peg, tcp, hole = (rigid(frame[k]) for k in ("peg", "tcp", "hole"))
        relative = np.linalg.inv(hole) @ peg
        tip = relative[:3, 3] + relative[:3, 0] * length
        predicates = {
            "head_depth": abs(tip[0]) <= 0.015,
            "transverse": max(abs(relative[1, 3]), abs(relative[2, 3])) <= 0.0015,
            "orientation": Rotation.from_matrix(relative[:3, :3]).magnitude() <= theta,
            "linear_speed": np.dot(
                frame["peg_linear_velocity"], frame["peg_linear_velocity"]
            )
            <= 0.003**2,
            "angular_speed": np.dot(
                frame["peg_angular_velocity"], frame["peg_angular_velocity"]
            )
            <= theta**2,
        }
        assert all(
            bool(value) == frame["goal_components"][k]
            for k, value in predicates.items()
        )
        dwell = dwell + 1 if all(predicates.values()) else 0
        success |= dwell >= 26
        assert dwell == frame["goal_dwell"] and success == frame["completion_flag"]
        ref = row["initial_record"] if i <= 150 else row["root"]["frame"]
        e0 = np.linalg.inv(rigid(ref["tcp"])) @ rigid(ref["peg"])
        slip = np.linalg.inv(e0) @ np.linalg.inv(tcp) @ peg
        displacement = np.linalg.norm(slip[:3, 3])
        angle = Rotation.from_matrix(slip[:3, :3]).magnitude()
        np.testing.assert_allclose(
            displacement, frame["grasp_slip_translation_m"], rtol=0, atol=1e-10
        )
        np.testing.assert_allclose(
            angle, frame["grasp_slip_rotation_rad"], rtol=0, atol=1e-8
        )
        command, tcp_h = rigid(frame["command_H"]), np.linalg.inv(hole) @ tcp
        residual = command[:3, 3] - tcp_h[:3, 3]
        np.testing.assert_allclose(
            np.linalg.norm(residual), frame["tcp_residual_m"], rtol=0, atol=1e-12
        )
        q, qv = np.asarray(frame["qpos"]), np.asarray(frame["qvel"])
        nom = rigid(config["nominal_tcp_H"])
        expected_x = np.r_[
            q[:7],
            qv[:7],
            tcp_h[:3, 3],
            Rotation.from_matrix(nom[:3, :3].T @ tcp_h[:3, :3]).as_rotvec(),
            command[:3, 3],
            Rotation.from_matrix(nom[:3, :3].T @ command[:3, :3]).as_rotvec(),
            length,
            config["radius"],
        ]
        expected_y = np.r_[expected_x[:20], residual]
        np.testing.assert_allclose(expected_x, frame["online_X"], rtol=0, atol=1e-9)
        np.testing.assert_allclose(
            expected_y, frame["online_Y_sample"], rtol=0, atol=1e-9
        )
        pair_impulse = np.zeros(3)
        nonfinger_force = 0.0
        for contact in frame["contacts_evaluator_only"]:
            bodies = contact["bodies"]
            impulse = np.asarray(contact["net_impulse_Ns"])
            np.testing.assert_allclose(
                np.linalg.norm(impulse) / 0.01,
                contact["net_force_N"],
                rtol=0,
                atol=1e-10,
            )
            if set(bodies) == {"scene-0_peg_0", "scene-0_box_with_hole_0"}:
                pair_impulse += impulse if bodies[0] == "scene-0_peg_0" else -impulse
            if any(
                b.startswith("panda_") and "finger" not in b for b in bodies
            ) and any(b.startswith("scene-0_") for b in bodies):
                nonfinger_force = max(nonfinger_force, contact["net_force_N"])
        np.testing.assert_allclose(
            np.linalg.norm(pair_impulse) / 0.01,
            frame["peg_fixture_force_N"],
            rtol=0,
            atol=1e-5,
        )
        checks = {
            "joint_limits": np.all(q >= limits[:, 0] - 1e-7)
            and np.all(q <= limits[:, 1] + 1e-7),
            "joint_speed": np.max(abs(qv[:7])) <= 2,
            "tcp_residual": np.linalg.norm(residual) <= 0.012,
            "grasp_slip_translation": displacement <= 0.003,
            "grasp_slip_rotation": angle <= 2 * theta,
            "peg_fixture_force": frame["peg_fixture_force_N"]
            <= 10 * config["peg_mass_kg"] * 9.81,
            "nonfinger_robot_contact": nonfinger_force <= 0.5,
        }
        assert all(
            bool(value) == frame["constraint_checks"][k] for k, value in checks.items()
        )
        if i > 150:
            for k, value in checks.items():
                if not value:
                    violations[k].append(i)
    assert len(frames) == row["actual_physics_substeps"] == 550
    assert row["actual_control_ticks"] == 110
    assert success == row["terminal"]["completion"]
    assert (not any(violations.values())) == row["terminal"]["whole_postroot_compliant"]
    # Reconstruct all110 command endpoints separately, including public-vs-native frame distinction.
    nominal = rigid(config["nominal_tcp_H"])
    targets = [nominal.copy() for _ in range(10)]
    for k in range(1, 21):
        t = nominal.copy()
        v = k / 20
        t[0, 3] += 0.009 * (3 * v * v - 2 * v**3)
        targets.append(t)
    start = np.linalg.inv(rigid(config["hole_world"])) @ rigid(
        row["root"]["frame"]["tcp"]
    )
    e = np.eye(4)
    e[:3, 3] = [0.060, 0, 0]
    e[:3, :3] = Rotation.from_euler("X", np.pi).as_matrix()
    goal = np.eye(4)
    goal[:3, 3] = [-length - 0.010, 0, 0]
    end = goal @ np.linalg.inv(e)
    rotations = Slerp([0, 1], Rotation.from_matrix([start[:3, :3], end[:3, :3]]))
    for k in range(1, 41):
        v = k / 40
        t = np.eye(4)
        t[:3, 3] = start[:3, 3] + (end[:3, 3] - start[:3, 3]) * (3 * v * v - 2 * v**3)
        t[:3, :3] = rotations(v).as_matrix()
        targets.append(t)
    targets.extend([end] * 40)
    assert len(targets) == len(row["commands"]) == 110
    for k, (expected, actual) in enumerate(zip(targets, row["commands"]), 1):
        assert actual["control_tick"] == k
        np.testing.assert_allclose(
            expected, rigid(actual["target_H"]), rtol=0, atol=1e-9
        )
        for frame in frames[(k - 1) * 5 : k * 5]:
            np.testing.assert_allclose(
                rigid(actual["target_H"]), rigid(frame["command_H"]), rtol=0, atol=1e-12
            )
    last = frames[-1]
    final = np.linalg.inv(rigid(last["hole"])) @ rigid(last["peg"])
    tip = final[:3, 3] + final[:3, 0] * length
    return {
        "repeat": row["job"]["repeat"],
        "source_status": row["status"],
        "frames_checked": len(frames),
        "commands_checked": len(targets),
        "actual_goal": success,
        "whole_postroot_compliant": not any(violations.values()),
        "initial_postfailure_screen": row["original_postfailure_screen"],
        "trace_sha256": hashlib.sha256(raw).hexdigest(),
        "violations": {
            k: {"samples": len(v), "first_substep": min(v) if v else None}
            for k, v in violations.items()
        },
        "peak_TCP_residual_m": max(f["tcp_residual_m"] for f in frames[150:]),
        "peak_slip_translation_m": max(
            f["grasp_slip_translation_m"] for f in frames[150:]
        ),
        "peak_slip_rotation_rad": max(
            f["grasp_slip_rotation_rad"] for f in frames[150:]
        ),
        "peak_peg_fixture_force_N": max(f["peg_fixture_force_N"] for f in frames[150:]),
        "force_limit_N": 10 * config["peg_mass_kg"] * 9.81,
        "final_peg_head_H_m": tip.tolist(),
        "configuration_length_m": length,
        "no_clock_reset": True,
        "learner_boundary_checked": True,
        "contact_impulse_units_independently_checked": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [check(args.evidence / f"repeat{k}") for k in (0, 1)]
    roots = [
        json.loads(
            lzma.decompress((args.evidence / f"repeat{k}/result.json.xz").read_bytes())
        )["root"]
        for k in (0, 1)
    ]
    result = {
        "independent_audit_passed": True,
        "technical_development_parents": 1,
        "fresh_process_attempts": 2,
        "source_complete": 2,
        "missing_source_results": 0,
        "nominal_gate_passed": all(
            r["actual_goal"] and r["whole_postroot_compliant"] for r in reports
        ),
        "replay_trace_byte_identical": reports[0]["trace_sha256"]
        == reports[1]["trace_sha256"],
        "root_controller_drive_state_byte_equivalent": roots[0] == roots[1],
        "no_postfailure_hold_pair_available": True,
        "new_qualification_roots": 0,
        "new_exploratory_parents": 0,
        "confirmation_parents": 0,
        "rows": reports,
        "scope": "One new nominal-initialization development checkpoint repeated, not2 independent parents or H1/H2 evidence",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
