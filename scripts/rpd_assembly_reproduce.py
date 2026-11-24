"""Post-registration independent command audit and clean-directory offline replay audit.

This script does not construct a simulator, launch a worker or select any parent.
"""

import argparse
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("research/rpd_assembly_preliminary_20261120")


def rigid(raw):
    values = np.asarray(raw)
    result = np.eye(4)
    result[:3, 3] = values[:3]
    result[:3, :3] = Rotation.from_quat(values[[4, 5, 6, 3]]).as_matrix()
    return result


def stage_point(position):
    result = np.eye(4)
    result[:3, 3] = position
    return result


def interpolation(start, end, count):
    orientation = Slerp([0, 1], Rotation.from_matrix([start[:3, :3], end[:3, :3]]))
    results = []
    for k in range(1, count + 1):
        v = k / count
        target = np.eye(4)
        target[:3, 3] = start[:3, 3] + (end[:3, 3] - start[:3, 3]) * v * v * (3 - 2 * v)
        target[:3, :3] = orientation(v).as_matrix()
        results.append(target)
    return results


def audit_commands():
    checked = []
    for path in sorted((ROOT / BASE / "episodes").glob("*/result.json.xz")):
        with lzma.open(path, "rt") as stream:
            row = json.load(stream)
        if row["status"] != "COMPLETE" or not row["commands"]:
            continue
        config, job = row["configuration"], row["job"]
        length = config["length"]
        initial = rigid(config["nominal_tcp_H"])
        expected = [initial.copy() for _ in range(10)]
        approach_end = initial.copy()
        approach_end[0, 3] += 0.009
        expected += interpolation(initial, approach_end, 20)
        frames = [
            json.loads(line)
            for line in path.with_name("trace.jsonl").read_text().splitlines()
        ]
        if "terminal" in row:
            direct = job["intervention"] == "direct"
            if not direct:
                for k in range(1, 11):
                    target = approach_end.copy()
                    if job["intervention"] == "preload":
                        v = k / 10
                        target[0, 3] += 0.0015 * v * v * (3 - 2 * v)
                    elif job["intervention"] == "dither" and k < 10:
                        target[1, 3] += 0.003 * np.sin(np.pi * k / 5)
                    expected.append(target)
            start_frame = frames[149 if direct else 199]
            # Commands use the declared public calibration, not the native
            # float32-rounded fixture view used for physical goal evaluation.
            hole = rigid(config["hole_world"])
            start = np.linalg.inv(hole) @ rigid(start_frame["tcp"])
            inverse_grasp = np.eye(4)
            inverse_grasp[:3, :3] = Rotation.from_euler("X", np.pi).as_matrix().T
            inverse_grasp[:3, 3] = [-0.060, 0, 0]
            endpoint = stage_point([-length - 0.010, 0, 0]) @ inverse_grasp
            if job["action"] == "a1":
                withdrawal = start.copy()
                withdrawal[0, 3] -= 0.012
                aligned = stage_point([-2 * length - 0.006, 0, 0]) @ inverse_grasp
                expected += interpolation(start, withdrawal, 10)
                expected += interpolation(withdrawal, aligned, 10)
                start = aligned
            expected += interpolation(start, endpoint, 40)
            expected += [endpoint.copy() for _ in range(110 - len(expected))]
        assert len(expected) == len(row["commands"])
        maximum_position = maximum_angle = maximum_native_position = (
            maximum_native_angle
        ) = 0.0
        for i, (target, actual) in enumerate(zip(expected, row["commands"]), 1):
            observed = rigid(actual["target_H"])
            dp = float(np.linalg.norm(target[:3, 3] - observed[:3, 3]))
            dr = float(
                Rotation.from_matrix(target[:3, :3].T @ observed[:3, :3]).magnitude()
            )
            maximum_position = max(maximum_position, dp)
            maximum_angle = max(maximum_angle, dr)
            assert dp < 1e-9 and dr < 1e-9, {
                "row": str(path),
                "tick": i,
                "dp": dp,
                "dr": dr,
                "expected": target.tolist(),
                "observed": observed.tolist(),
            }
            action = np.asarray(actual["native_action"])
            native_position = target[:3, 3] + np.array([0.665, 0.30, 0.15])
            np_error = float(np.linalg.norm(action[:3] - native_position))
            nr_error = float(
                Rotation.from_matrix(
                    target[:3, :3].T
                    @ Rotation.from_euler("XYZ", action[3:6]).as_matrix()
                ).magnitude()
            )
            maximum_native_position = max(maximum_native_position, np_error)
            maximum_native_angle = max(maximum_native_angle, nr_error)
            assert np_error < 3e-7 and nr_error < 3e-7
            assert action[6] == -1 and actual["control_tick"] == i
        checked.append(
            {
                "result": str(path.relative_to(ROOT)),
                "commands_checked": len(expected),
                "maximum_target_translation_error_m": maximum_position,
                "maximum_target_rotation_error_rad": maximum_angle,
                "maximum_native_float32_translation_error_m": maximum_native_position,
                "maximum_native_float32_rotation_error_rad": maximum_native_angle,
            }
        )
    return {
        "passed": True,
        "source_episode_command_sequences_checked": len(checked),
        "controller_commands_checked": sum(r["commands_checked"] for r in checked),
        "scope": "Independent equations for initialization/probes/hold/nominal macros and base-frameXYZ conversion;not a simulation rerun",
        "rows": checked,
    }


def clean_reproduction(reference):
    with tempfile.TemporaryDirectory(
        prefix="rpd-assembly-offline-", dir="/tmp"
    ) as name:
        destination = Path(name)
        code = ["scripts/rpd_assembly_contract.py", "scripts/rpd_assembly_audit.py"]
        data = [p for p in (ROOT / BASE / "episodes").rglob("*") if p.is_file()]
        data += list((ROOT / BASE).glob("registration*.json"))
        copied = {}
        for item in [ROOT / p for p in code] + data:
            relative = item.relative_to(ROOT)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
            before = hashlib.sha256(item.read_bytes()).hexdigest()
            assert hashlib.sha256(target.read_bytes()).hexdigest() == before
            copied[str(relative)] = before
        result_path = destination / "independent_audit.json"
        env = dict(
            os.environ,
            PYTHONPATH=str(destination / "scripts"),
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(destination / "scripts/rpd_assembly_audit.py"),
                "--output",
                str(result_path),
            ],
            cwd=destination,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        reproduced = json.loads(result_path.read_text())
        assert reproduced == json.loads(reference.read_text()), "Clean audit differs"
        return {
            "passed": True,
            "new_physics": 0,
            "fresh_directory": True,
            "source_and_evidence_files": copied,
            "summary_identical": True,
            "scope": "Only existing evidence and independently coded verifier copied;no native worker or simulator launched",
        }


def audit_repeats():
    records = []
    for path in sorted((ROOT / BASE / "episodes").glob("*/result.json.xz")):
        with lzma.open(path, "rt") as stream:
            row = json.load(stream)
        if row["status"] == "COMPLETE" and "terminal" in row:
            records.append((path, row))
    checks = []
    for path, row in records:
        job = row["job"]
        if job["repeat"] != 1:
            continue
        original = next(
            p
            for p, r in records
            if r["job"]["repeat"] == 0
            and r["job"]["candidate"] == job["candidate"]
            and r["job"]["intervention"] == job["intervention"]
            and r["job"]["action"] == job["action"]
        )
        a = [
            json.loads(line)
            for line in original.with_name("trace.jsonl").read_text().splitlines()
        ]
        b = [
            json.loads(line)
            for line in path.with_name("trace.jsonl").read_text().splitlines()
        ]
        assert len(a) == len(b) == 550
        dp = dr = other = 0.0
        for x, y in zip(a, b):
            assert x["substep"] == y["substep"] and x["goal_dwell"] == y["goal_dwell"]
            assert (
                x["completion_flag"] == y["completion_flag"]
                and x["constraint_checks"] == y["constraint_checks"]
            )
            for key in ("peg", "fixture", "hole", "tcp"):
                mx, my = rigid(x[key]), rigid(y[key])
                dp = max(dp, float(np.linalg.norm(mx[:3, 3] - my[:3, 3])))
                dr = max(
                    dr,
                    float(Rotation.from_matrix(mx[:3, :3].T @ my[:3, :3]).magnitude()),
                )
            for key in (
                "qpos",
                "qvel",
                "peg_linear_velocity",
                "peg_angular_velocity",
                "peg_fixture_force_vector_N",
                "online_X",
                "online_Y_sample",
            ):
                other = max(
                    other,
                    float(np.max(np.abs(np.asarray(x[key]) - np.asarray(y[key])))),
                )
        assert dp <= 1e-5 and dr <= 1e-4 and other <= 1e-5
        checks.append(
            {
                "parent": job["candidate"]["candidate_id"],
                "intervention": job["intervention"],
                "action": job["action"],
                "paired_frames": 550,
                "maximum_translation_m": dp,
                "maximum_rotation_rad": dr,
                "maximum_other_numeric_abs": other,
                "original": str(original.relative_to(ROOT)),
                "repeat": str(path.relative_to(ROOT)),
            }
        )
    return {
        "passed": bool(checks) and len(checks) == 14,
        "repeat_pairs": len(checks),
        "checks": checks,
        "scope": "Fourteen full-trajectory pairs at the first two eligible source parents only;not global native stability",
    }


def audit_observation_boundary():
    frames_checked = 0
    for path in sorted((ROOT / BASE / "episodes").glob("*/result.json.xz")):
        with lzma.open(path, "rt") as stream:
            row = json.load(stream)
        if row["status"] != "COMPLETE" or not row["commands"]:
            continue
        nominal = rigid(row["configuration"]["nominal_tcp_H"])
        limits = np.asarray(row["configuration"]["joint_limits"]).reshape(9, 2)
        length, radius = row["configuration"]["length"], row["configuration"]["radius"]
        for line in path.with_name("trace.jsonl").read_text().splitlines():
            frame = json.loads(line)
            q, v = np.asarray(frame["qpos"]), np.asarray(frame["qvel"])
            tcp_h = np.linalg.inv(rigid(frame["hole"])) @ rigid(frame["tcp"])
            command = rigid(frame["command_H"])
            tcp_rot = Rotation.from_matrix(
                nominal[:3, :3].T @ tcp_h[:3, :3]
            ).as_rotvec()
            command_rot = Rotation.from_matrix(
                nominal[:3, :3].T @ command[:3, :3]
            ).as_rotvec()
            residual = command[:3, 3] - tcp_h[:3, 3]
            expected_x = np.r_[
                q[:7],
                v[:7],
                tcp_h[:3, 3],
                tcp_rot,
                command[:3, 3],
                command_rot,
                length,
                radius,
            ]
            expected_y = np.r_[q[:7], v[:7], tcp_h[:3, 3], tcp_rot, residual]
            assert np.allclose(expected_x, frame["online_X"], rtol=0, atol=1e-9)
            assert np.allclose(expected_y, frame["online_Y_sample"], rtol=0, atol=1e-9)
            assert np.isclose(
                np.linalg.norm(residual), frame["tcp_residual_m"], atol=1e-12
            )
            checks = frame["constraint_checks"]
            assert checks["joint_limits"] == bool(
                np.all(q >= limits[:, 0] - 1e-7) and np.all(q <= limits[:, 1] + 1e-7)
            )
            assert checks["grasp_slip_translation"] == (
                frame["grasp_slip_translation_m"] <= 0.003
            )
            assert checks["grasp_slip_rotation"] == (
                frame["grasp_slip_rotation_rad"] <= 2 * np.arctan(0.003 / (2 * length))
            )
            frames_checked += 1
    return {
        "passed": True,
        "frames_checked": frames_checked,
        "root_feature_dimension": 28,
        "diagnostic_sample_dimension": 23,
        "diagnostic_sample_substeps": list(range(155, 201, 5)),
        "scope": "Reconstruct every recorded online scalar from whitelisted joint/TCP/command/publicgeometry fields. Force,Z,peg/grasp pose and alternative outcomes remain evaluator-only. No learned diagnostic model was fitted.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(exist_ok=False)
    for name, payload in (
        ("independent_command_audit.json", audit_commands()),
        ("independent_full_trace_parity.json", audit_repeats()),
        ("independent_observation_boundary.json", audit_observation_boundary()),
        ("clean_reproduction.json", clean_reproduction(args.reference)),
    ):
        (args.output_dir / name).write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps({"passed": True, "output": str(args.output_dir), "new_physics": 0})
    )
