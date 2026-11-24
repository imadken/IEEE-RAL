"""Independent offline recount from native raw traces, with no simulator execution."""

import argparse
import ast
import collections
import itertools
import json
import lzma
import math
from pathlib import Path

import numpy as np
from rpd_pilot_common import BASE, MENUS, PREFIX, TASKS, sha, write_json


def delta(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            return math.inf
        return max((delta(a[k], b[k]) for k in a), default=0.0)
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
        return math.inf
    return float(np.max(np.abs(x - y))) if x.size else 0.0


def check_parity(left, right):
    if len(left) != len(right):
        return False
    for a, b in zip(left, right, strict=True):
        if np.linalg.norm(np.array(a["position"]) - b["position"]) > 1e-5:
            return False
        u, v = np.array(a["quaternion"]), np.array(b["quaternion"])
        angle = 2 * np.arccos(
            np.clip(abs(u @ v) / np.linalg.norm(u) / np.linalg.norm(v), 0, 1)
        )
        if angle > 1e-4:
            return False
        if any(
            delta(a[k], b[k]) > tolerance
            for k, tolerance in [
                ("velocity", 1e-4),
                ("qpos", 1e-4),
                ("observation", 1e-4),
                ("time", 1e-9),
            ]
        ):
            return False
        if any(
            a[k] != b[k]
            for k in (
                "contacts",
                "success",
                "native_task_flags",
                "wrapper_flags",
                "controller_memory",
            )
        ):
            return False
    return True


def required_packet(state):
    obs = state["observation"]
    return {
        "time_seconds": state["time"],
        "arm_qpos": obs["agent"]["qpos"][0][:7],
        "arm_qvel": obs["agent"]["qvel"][0][:7],
        "tcp_xyz": obs["extra"]["tcp_pose"][0][:3],
        "source": "NATIVE_ARM_PROPRIOCEPTION_AND_FORWARD_KINEMATICS",
    }


def independent_response(states):
    assert len(states) == 11
    frames = [required_packet(s) for s in states]
    assert all(
        abs(b["time_seconds"] - a["time_seconds"] - 0.05) <= 1e-9
        for a, b in itertools.pairwise(frames)
    )
    first, last = frames[0], frames[-1]
    return {
        "displacement_bins_5mm": [
            math.floor((b - a) / 0.005)
            for a, b in zip(first["tcp_xyz"], last["tcp_xyz"], strict=True)
        ],
        "arm_motion_bin_0_01rad": math.floor(
            math.sqrt(
                sum(
                    (b - a) ** 2
                    for a, b in zip(first["arm_qpos"], last["arm_qpos"], strict=True)
                )
            )
            / 0.01
        ),
        "peak_arm_speed_bin_0_1rad_s": math.floor(
            max(abs(v) for f in frames for v in f["arm_qvel"]) / 0.1
        ),
        "timestamp": last["time_seconds"],
        "physical_effect_qualified": False,
        "interpretation": "OBSERVED_KINEMATIC_RESPONSE_NOT_A_CONTACT_FORCE_OR_SUCCESS_LABEL",
    }


def source_geometry(state, metadata):
    joints = np.asarray(state["qpos"])[0, :7]
    limits = np.asarray(metadata["joint_limits"]).reshape(-1, 2)[:7]
    tcp = np.array(required_packet(state)["tcp_xyz"])
    obj = np.array(state["position"])
    return {
        "arm": bool(
            np.all(joints >= limits[:, 0] - 1e-6)
            and np.all(joints <= limits[:, 1] + 1e-6)
        ),
        "TCP": bool(np.all(np.abs(tcp[:2]) <= 0.60) and 0.015 <= tcp[2] <= 0.50),
        "object": bool(
            np.all(np.abs(obj[:2]) <= 0.45)
            and metadata["cube_half_size"] - 0.002 <= obj[2] <= 0.50
        ),
    }


def fixed_probe(task, probe):
    # Separately assembled from the sealed supervisor command table.
    closed = [0.0, 0.0, 0.0, -1.0]
    if probe == "neutral10":
        return [closed] * 10
    if probe == "neutral20":
        return [closed] * 20
    menu = {
        "PickCube-v1": {
            "micro_lift": [[0.0, 0.0, 0.025, -1.0]] * 4 + [closed] * 6,
            "release_settle": [[0.0, 0.0, 0.0, 1.0]] * 10,
        },
        "PushCube-v1": {
            "forward_tap": [[0.05, 0.0, 0.0, -1.0]] * 4 + [closed] * 6,
            "lateral_sweep": [[0.0, 0.05, 0.0, -1.0]] * 4 + [closed] * 6,
        },
    }
    return menu[task][probe]


def native_macro(task, endpoint, j, state, initial_tcp):
    extra = state["observation"]["extra"]
    cube = np.array(extra["obj_pose"][0][:3])
    tcp = np.array(extra["tcp_pose"][0][:3])
    goal = np.array(extra["goal_pos"][0])
    grip = -1.0
    if task == "PickCube-v1":
        target = goal.copy()
        if endpoint == "recover":
            if j < 8:
                target, grip = initial_tcp + [0, 0, 0.10], 1.0
            elif j < 22:
                target, grip = cube + [0, 0, 0.10], 1.0
            elif j < 34:
                target, grip = cube, 1.0
            elif j < 46:
                target = cube
    else:
        target = np.r_[goal[:2], cube[2]]
        if endpoint == "recover":
            if j < 6:
                target = initial_tcp + [0, 0, 0.08]
            elif j < 16:
                target = cube + [-0.055, 0, 0.10]
            elif j < 26:
                target = cube + [-0.055, 0, 0]
    return (
        np.r_[np.clip((target - tcp) / 0.1, -0.25, 0.25), grip]
        .astype(np.float32)
        .tolist()
    )


def inspect_trace(result):
    row = result["row"]
    task, prefix = row["parent"]["task"], PREFIX[row["parent"]["task"]]
    states, actions = result["records"], result["actions"]
    errors = []
    if len(states) != len(actions) + 1:
        errors.append("frame_count")
    for i, state in enumerate(states):
        if abs(state["time"] - i / 20) > 1e-9:
            errors.append(f"clock:{i}")
        if state["planner_frame"] != required_packet(state):
            errors.append(f"sensor_mask:{i}")
        if not np.isfinite(
            list(required_packet(state)["arm_qpos"])
            + list(required_packet(state)["arm_qvel"])
            + list(required_packet(state)["tcp_xyz"])
        ).all():
            errors.append(f"nonfinite:{i}")
        if state["success"] != bool(state["native_task_flags"]["success"][0]):
            errors.append(f"task_success:{i}")
    completed = result["status"] == "COMPLETE"
    if completed and len(actions) != prefix + 90:
        errors.append("deadline")
    offset = prefix
    observations = []
    for probe in row["history"]:
        commands = fixed_probe(task, probe)
        if len(actions) < offset + len(commands):
            break
        if (
            delta(
                actions[offset : offset + len(commands)],
                np.asarray(commands, dtype=np.float32),
            )
            != 0
        ):
            errors.append(f"probe_command:{probe}")
        if not probe.startswith("neutral"):
            observations.append(
                {
                    "probe": probe,
                    "response": independent_response(states[offset : offset + 11]),
                    "start_control": offset,
                    "end_control": offset + 10,
                }
            )
        offset += len(commands)
    if observations != result["probe_observations"]:
        errors.append("response_encoding")
    if completed:
        initial_tcp = np.array(required_packet(states[offset])["tcp_xyz"])
        for j in range(row["macro_ticks"]):
            expected = native_macro(
                task, row["endpoint"], j, states[offset + j], initial_tcp
            )
            if delta(actions[offset + j], expected) > 1e-7:
                errors.append(f"native_macro_command:{j}")
        if row["macro_ticks"] and (
            result["macro_end_success"] != states[offset + 70]["success"]
            or result["macro_end_control"] != offset + 70
        ):
            errors.append("macro_endpoint")
        padding_start = offset + row["macro_ticks"]
        grip = actions[padding_start - 1][-1] if padding_start else -1.0
        if any(delta(a, [0, 0, 0, grip]) != 0 for a in actions[padding_start:]):
            errors.append("padding")
        if result["deadline_success"] != states[-1]["success"]:
            errors.append("deadline_label")
    geometry = (
        [source_geometry(s, result["source_runtime"]) for s in states]
        if "source_runtime" in result
        else []
    )
    return {
        "passed": not errors,
        "errors": errors,
        "frames": len(states),
        "whole_path_allowed": bool(geometry) and all(all(g.values()) for g in geometry),
        "suffix_allowed": bool(geometry)
        and all(all(g.values()) for g in geometry[prefix:]),
        "violations": {
            k: [i for i, g in enumerate(geometry) if not g[k]]
            for k in ("arm", "TCP", "object")
        },
        "native_success": states[-1]["success"] if completed else None,
    }


def K(branches, history):
    selected = set()
    for endpoint in ("continue", "recover"):
        pair = [branches.get((tuple(history), endpoint, r)) for r in (0, 1)]
        if any(
            p is None
            or p["status"] != "COMPLETE"
            or not p.get("source_checkpoint_qualified")
            for p in pair
        ):
            return None
        if not check_parity(pair[0]["records"], pair[1]["records"]):
            return None
        if pair[0]["deadline_success"]:
            selected.add(endpoint)
    return sorted(selected)


def compare_options(hold, probe):
    if hold is None or probe is None:
        return {
            "status": "UNKNOWN",
            "erasure": None,
            "creation": None,
            "lost": None,
            "gained": None,
        }
    a, b = set(hold), set(probe)
    return {
        "status": "KNOWN",
        "erasure": bool(a and not b),
        "creation": bool(b and not a),
        "lost": sorted(a - b),
        "gained": sorted(b - a),
    }


def root_description(state):
    frame = required_packet(state)
    signature = (
        [math.floor(x / 0.01) for x in frame["arm_qpos"]]
        + [math.floor(x / 0.1) for x in frame["arm_qvel"]]
        + [math.floor(x / 0.005) for x in frame["tcp_xyz"]]
    )
    rel = np.array(state["position"][:2]) - frame["tcp_xyz"][:2]
    label = [int(np.searchsorted([-0.03, 0, 0.03], v, side="right")) for v in rel]
    return {"signature": signature, "evaluator_root_pose_cell": label}


def audit(output):
    assert not output.exists()
    output.mkdir(parents=True)
    seal = json.loads((BASE / "prephysics_seal.json").read_text())
    for name, expected in seal["files"].items():
        assert sha(name) == expected, name
    raw_hashes = {}
    task_results = {}
    case_checks = []
    all_checks = True
    for task in TASKS:
        task_path = BASE / "physics" / task
        available = {}
        for path in sorted(task_path.glob("parent_*/*.json.xz")):
            raw_hashes[str(path)] = sha(path)
            with lzma.open(path, "rt") as stream:
                result = json.load(stream)
            row = result["row"]
            key = (
                row["parent"]["index"],
                tuple(row["history"]),
                row["endpoint"],
                row["repeat"],
            )
            assert key not in available
            inspection = inspect_trace(result)
            all_checks &= inspection["passed"]
            case_checks.append(
                {"path": str(path), "row_id": row["row_id"], **inspection}
            )
            result["independent_inspection"] = inspection
            available[key] = result
        parent_results = []
        comparisons = []
        response_distinctness = {}
        for index in range(10):
            branches = {
                key[1:]: value for key, value in available.items() if key[0] == index
            }
            first = next(iter(branches.values()), None)
            roots = [
                v["records"][: PREFIX[task] + 1]
                for v in branches.values()
                if len(v["records"]) > PREFIX[task]
            ]
            root_agreement = (
                all(check_parity(roots[0], r) for r in roots[1:]) if roots else None
            )
            full_memory_agreement = (
                len(
                    {
                        json.dumps(v.get("root_controller_custom"), sort_keys=True)
                        for v in branches.values()
                        if "root_controller_custom" in v
                    }
                )
                <= 1
            )
            statuses = collections.Counter(v["status"] for v in branches.values())
            qualified = (
                len(branches) == 54
                and statuses == {"COMPLETE": 54}
                and bool(root_agreement)
                and full_memory_agreement
            )
            ks = {}
            for history in [
                (),
                *((p,) for p in MENUS[task]),
                *itertools.product(MENUS[task], repeat=2),
                ("neutral10",),
                ("neutral20",),
            ]:
                ks["/".join(history) or "empty"] = (
                    K(branches, history) if qualified else None
                )
                if history and not history[0].startswith("neutral"):
                    condition = branches.get((tuple(history), "continue", 0))
                    hold_name = "neutral10" if len(history) == 1 else "neutral20"
                    hold = branches.get(((hold_name,), "continue", 0))
                    comparison = {
                        "parent_index": index,
                        "history": list(history),
                        "delay_ticks": len(history) * 10,
                        "K_hold": K(branches, (hold_name,)) if qualified else None,
                        "K_probe": K(branches, history) if qualified else None,
                    }
                    comparison.update(
                        compare_options(comparison["K_hold"], comparison["K_probe"])
                    )
                    if condition and len(condition["records"]) > PREFIX[
                        task
                    ] + 10 * len(history):
                        suffix = condition["records"][
                            PREFIX[task] : PREFIX[task] + 10 * len(history) + 1
                        ]
                        contact_frames = [
                            i
                            for i, s in enumerate(suffix[1:], 1)
                            if any(
                                c["points"]
                                for c in s["evaluator_robot_object_contacts"]
                            )
                        ]
                        comparison["probe_contact_control_frames"] = contact_frames
                        comparison["contact_probe"] = bool(contact_frames)
                        comparison["sampled_geometry_during_probe_allowed"] = all(
                            all(
                                source_geometry(s, condition["source_runtime"]).values()
                            )
                            for s in suffix
                        )
                        comparison["probe_object_displacement_m"] = float(
                            np.linalg.norm(
                                np.array(suffix[-1]["position"]) - suffix[0]["position"]
                            )
                        )
                        comparison["probe_tcp_displacement_m"] = float(
                            np.linalg.norm(
                                np.array(required_packet(suffix[-1])["tcp_xyz"])
                                - required_packet(suffix[0])["tcp_xyz"]
                            )
                        )
                        comparison["both_macro_paths_sampled_allowed"] = all(
                            branches.get((tuple(history), a, r), {})
                            .get("independent_inspection", {})
                            .get("suffix_allowed", False)
                            for a in ("continue", "recover")
                            for r in (0, 1)
                        )
                        comparison["hold_macro_paths_sampled_allowed"] = all(
                            branches.get(((hold_name,), a, r), {})
                            .get("independent_inspection", {})
                            .get("suffix_allowed", False)
                            for a in ("continue", "recover")
                            for r in (0, 1)
                        )
                        if hold and len(hold["records"]) > PREFIX[task] + 10 * len(
                            history
                        ):
                            at = PREFIX[task] + 10 * len(history)
                            comparison["object_difference_from_matched_hold_m"] = float(
                                np.linalg.norm(
                                    np.array(condition["records"][at]["position"])
                                    - hold["records"][at]["position"]
                                )
                            )
                            comparison["tcp_difference_from_matched_hold_m"] = float(
                                np.linalg.norm(
                                    np.array(
                                        required_packet(condition["records"][at])[
                                            "tcp_xyz"
                                        ]
                                    )
                                    - required_packet(hold["records"][at])["tcp_xyz"]
                                )
                            )
                            comparison["contact_trace_differs_from_hold"] = any(
                                a["contacts"] != b["contacts"]
                                for a, b in zip(
                                    suffix,
                                    hold["records"][PREFIX[task] : at + 1],
                                    strict=True,
                                )
                            )
                        comparison["mechanistic_contact_response"] = comparison[
                            "contact_probe"
                        ] and (
                            comparison.get("object_difference_from_matched_hold_m", 0)
                            > 1e-5
                            or comparison.get("contact_trace_differs_from_hold", False)
                        )
                    comparisons.append(comparison)
            root_info = (
                root_description(first["records"][PREFIX[task]])
                if first and len(first["records"]) > PREFIX[task]
                else None
            )
            if root_info:
                response_distinctness.setdefault(
                    json.dumps(root_info["signature"]), []
                ).append(root_info["evaluator_root_pose_cell"])
            outcomes = {
                "/".join(h) or "empty": {
                    e: {
                        "macro_end": v["macro_end_success"],
                        "deadline": v["deadline_success"],
                    }
                    for (hh, e, r), v in branches.items()
                    if hh == h and r == 0
                }
                for h in dict.fromkeys(k[0] for k in branches)
            }
            parent_results.append(
                {
                    "parent_index": index,
                    "attempted_rows": len(branches),
                    "completed_rows": statuses["COMPLETE"],
                    "failed_rows": statuses["FAILED"],
                    "ineligible_rows": statuses["INELIGIBLE_ALREADY_COMPLETE"],
                    "missing_rows": 54 - len(branches),
                    "qualified": qualified,
                    "prefix_replay_agreement": root_agreement,
                    "root_controller_memory_agreement": full_memory_agreement,
                    "K": ks,
                    "root": root_info,
                    "outcomes_repeat0": outcomes,
                    "failures": [
                        v["failure"] for v in branches.values() if v.get("failure")
                    ],
                }
            )
        qualifying_comparisons = [c for c in comparisons if c["status"] == "KNOWN"]
        mechanisms = [
            c for c in qualifying_comparisons if c.get("mechanistic_contact_response")
        ]
        erasures = [
            c
            for c in mechanisms
            if c["erasure"]
            and c.get("sampled_geometry_during_probe_allowed")
            and c.get("both_macro_paths_sampled_allowed")
            and c.get("hold_macro_paths_sampled_allowed")
        ]
        nqualified = sum(p["qualified"] for p in parent_results)
        decision = (
            "SOURCE_NOT_QUALIFIED"
            if nqualified < 10
            else "PHYSICAL_MECHANISM_OBSERVED"
            if erasures
            else "QUALIFIED_NO_ERASURE_IN_PILOT"
            if mechanisms
            else "PROBE_NOT_MECHANISTIC"
        )
        invocations = [
            json.loads(p.read_text()) for p in task_path.glob("invocation_*.json")
        ]
        response_bins = {
            probe: len(
                {
                    json.dumps(v["probe_observations"][0]["response"], sort_keys=True)
                    for (i, h, e, r), v in available.items()
                    if h == (probe,)
                    and e == "continue"
                    and r == 0
                    and v["probe_observations"]
                }
            )
            for probe in MENUS[task]
        }
        statuses = collections.Counter(v["status"] for v in available.values())
        task_results[task] = {
            "decision": decision,
            "registered_parents": 10,
            "qualified_complete_parents": nqualified,
            "attempted_parents": sum(p["attempted_rows"] > 0 for p in parent_results),
            "planned_episodes": 540,
            "attempted_episodes": len(available),
            "complete_episodes": statuses["COMPLETE"],
            "failed_episodes": statuses["FAILED"],
            "ineligible_episodes": statuses["INELIGIBLE_ALREADY_COMPLETE"],
            "unattempted_episodes": 540 - len(available),
            "parents": parent_results,
            "comparisons": comparisons,
            "known_comparisons": len(qualifying_comparisons),
            "mechanistic_contact_comparisons": len(mechanisms),
            "erasure_comparisons_all_known": sum(
                c["erasure"] for c in qualifying_comparisons
            ),
            "creation_comparisons_all_known": sum(
                c["creation"] for c in qualifying_comparisons
            ),
            "sampled_allowed_mechanistic_erasure_comparisons": len(erasures),
            "parent_indices_with_mechanistic_allowed_erasure": sorted(
                {c["parent_index"] for c in erasures}
            ),
            "response_distinctness_including_timestamp": response_bins,
            "root_signature_groups": len(response_distinctness),
            "root_signature_groups_with_varying_hidden_pose_cell": sum(
                len({tuple(z) for z in labels}) > 1
                for labels in response_distinctness.values()
            ),
            "worker_wall_seconds": sum(i["worker_wall_seconds"] for i in invocations),
            "compressed_task_bytes": sum(
                p.stat().st_size for p in task_path.rglob("*") if p.is_file()
            ),
            "startup_and_episode_seconds": [
                {"startup": v.get("startup_seconds"), "episode": v["runtime_seconds"]}
                for v in available.values()
            ],
            "native_controls": sum(len(v["actions"]) for v in available.values()),
            "outcome_counts_correlated_branches": dict(
                collections.Counter(
                    str(v["deadline_success"]) for v in available.values()
                )
            ),
            "stops": invocations,
            "no_new_discovery_or_calibration_or_test_parents": True,
        }
        all_checks &= all(
            p["prefix_replay_agreement"] is not False
            and p["root_controller_memory_agreement"]
            for p in parent_results
        )
        assert task_results[task]["worker_wall_seconds"] <= 10800
        assert task_results[task]["compressed_task_bytes"] < 3 * 1024**3
    code = ast.parse(Path("scripts/rpd_pilot_physics.py").read_text())
    forbidden = [
        n.attr
        for n in ast.walk(code)
        if isinstance(n, ast.Attribute)
        and n.attr
        in {"restore", "reset", "set_state", "set_state_dict", "set_pose", "set_qpos"}
    ]
    assert not forbidden
    write_json(
        output / "raw_manifest.json", {"files": raw_hashes, "algorithm": "sha256"}
    )
    write_json(
        output / "case_checks.json",
        {
            "passed": all_checks,
            "cases": case_checks,
            "forbidden_within_history_API_calls": forbidden,
        },
    )
    summary = {
        "passed": all_checks,
        "tasks": task_results,
        "scope": "Technical feasibility only, independent parentN<=10 per task; no prevalence, causal-population, calibrated-success, force or continuous-time safety guarantee.",
        "new_full_stage2_parents": 0,
        "manuscript_edits": 0,
    }
    write_json(output / "summary.json", summary)
    print(
        json.dumps(
            {
                "passed": all_checks,
                "tasks": {
                    t: {
                        k: v
                        for k, v in r.items()
                        if k
                        in {
                            "decision",
                            "registered_parents",
                            "qualified_complete_parents",
                            "attempted_episodes",
                            "complete_episodes",
                            "unattempted_episodes",
                            "failed_episodes",
                            "known_comparisons",
                            "erasure_comparisons_all_known",
                            "worker_wall_seconds",
                        }
                    }
                    for t, r in task_results.items()
                },
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
