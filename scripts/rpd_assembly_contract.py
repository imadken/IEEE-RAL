"""Frozen, bounded assembly source qualification; this module launches no physics."""

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.spatial.transform import Rotation

BASE = Path("research/rpd_assembly_preliminary_20261120")
PROPOSAL = Path("papers/rss2027_rpd_stage1/reviews/PROPOSED_PROTOCOL_AND_NUMERICS.json")
SCHEMA = "RPD_ASSEMBLY_NOMINAL_SOURCE_V1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    candidate_id: str
    phase: Literal["qual", "exploratory"]
    index: int = Field(ge=0)
    native_geometry_seed: int
    fault_seed_sha256: str

    @model_validator(mode="after")
    def fixed_namespace(self):
        prefix = (
            f"RPD-assembly-v1/qual/{self.index}"
            if self.phase == "qual"
            else f"RPD-assembly-prelim-v1/{self.index}"
        )
        assert self.candidate_id == prefix
        assert self.index < (12 if self.phase == "qual" else 24)
        assert self.native_geometry_seed == int.from_bytes(
            hashlib.sha256((prefix + "/geometry").encode()).digest()[:4], "big"
        )
        assert (
            self.fault_seed_sha256
            == hashlib.sha256((prefix + "/fault").encode()).hexdigest()
        )
        return self


class Job(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    candidate: Candidate
    intervention: Literal["screen", "hold", "preload", "dither", "direct"]
    action: Literal["none", "a0", "a1"]
    repeat: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def bounded_menu(self):
        assert (self.intervention == "screen") == (self.action == "none")
        if self.intervention == "direct":
            assert self.candidate.phase == "qual" and self.action == "a0"
        if self.candidate.phase == "exploratory":
            assert self.repeat == 0 and self.intervention != "direct"
        return self

    @property
    def job_id(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def candidates():
    old = json.loads(PROPOSAL.read_text())["candidate_inputs"]
    result = [
        Candidate(
            candidate_id=r["candidate_id"],
            phase="qual",
            index=r["index"],
            native_geometry_seed=r["native_geometry_seed"],
            fault_seed_sha256=r["PCG64_fault_seed_sha256"],
        )
        for r in old
        if r["phase"] == "qual"
    ]
    old_seeds = {r["native_geometry_seed"] for r in old}
    assert len(old) == len(old_seeds) == 588
    for index in range(24):
        prefix = f"RPD-assembly-prelim-v1/{index}"
        seed = int.from_bytes(
            hashlib.sha256((prefix + "/geometry").encode()).digest()[:4], "big"
        )
        assert seed not in old_seeds
        old_seeds.add(seed)
        result.append(
            Candidate(
                candidate_id=prefix,
                phase="exploratory",
                index=index,
                native_geometry_seed=seed,
                fault_seed_sha256=hashlib.sha256(
                    (prefix + "/fault").encode()
                ).hexdigest(),
            )
        )
    assert len(result) == 36 and len(old_seeds) == 612
    return result


def pose_matrix(raw):
    raw = np.asarray(raw, dtype=float).reshape(7)
    result = np.eye(4)
    result[:3, :3] = Rotation.from_quat(raw[[4, 5, 6, 3]]).as_matrix()
    result[:3, 3] = raw[:3]
    return result


def pose_raw(matrix):
    q = Rotation.from_matrix(np.asarray(matrix)[:3, :3]).as_quat()
    return np.r_[np.asarray(matrix)[:3, 3], q[[3, 0, 1, 2]]].tolist()


def transform(position, rotation=None):
    result = np.eye(4)
    result[:3, 3] = position
    if rotation is not None:
        result[:3, :3] = rotation
    return result


def fault(candidate, length):
    rng = np.random.Generator(np.random.PCG64(int(candidate.fault_seed_sha256, 16)))
    mode = int(rng.integers(0, 3))
    signs = rng.choice([-1, 1], size=2)
    transverse = rng.uniform(-0.003 / 4, 0.003 / 4, size=2)
    axis = int(rng.integers(0, 2))
    theta = float(np.arctan(0.003 / (2 * length)))
    dy, dz = transverse
    pitch = yaw = 0.0
    if mode == 0:
        dy = float(signs[0]) * 1.25 * 0.003
    elif mode == 1:
        dz = float(signs[1]) * 1.25 * 0.003
    elif axis == 0:
        pitch = float(signs[0]) * 2 * theta
    else:
        yaw = float(signs[0]) * 2 * theta
    return {
        "Z": mode,
        "dy": float(dy),
        "dz": float(dz),
        "pitch": pitch,
        "yaw": yaw,
        "theta_c": theta,
        "signs": signs.tolist(),
        "transverse_draws": transverse.tolist(),
        "axis_draw": axis,
    }


def goal_components(frame, length):
    peg = pose_matrix(frame["peg"])
    hole = pose_matrix(frame["hole"])
    relative = np.linalg.inv(hole) @ peg
    head = relative[:3, 3] + relative[:3, :3] @ np.array([length, 0, 0])
    theta = np.arctan(0.003 / (2 * length))
    angle = Rotation.from_matrix(relative[:3, :3]).magnitude()
    return {
        "head_depth": bool(-0.015 <= head[0] <= 0.015),
        "transverse": bool(np.max(np.abs(relative[1:3, 3])) <= 0.003 / 2),
        "orientation": bool(angle <= theta),
        "linear_speed": bool(np.linalg.norm(frame["peg_linear_velocity"]) <= 0.003),
        "angular_speed": bool(np.linalg.norm(frame["peg_angular_velocity"]) <= theta),
    }


def probe_target(root, intervention, k):
    assert intervention in ("hold", "preload", "dither") and 1 <= k <= 10
    target = np.asarray(root).copy()
    if intervention == "preload":
        v = k / 10
        target[0, 3] += 0.0015 * (3 * v**2 - 2 * v**3)
    if intervention == "dither" and k != 10:
        target[1, 3] += 0.003 * np.sin(2 * np.pi * k / 10)
    return target


def recovery_segments(start, length, action):
    # Public, root-frozen nominal peg-in-TCP estimate in BOTH macros.
    nominal_e = transform([0.060, 0, 0], Rotation.from_euler("X", np.pi).as_matrix())
    final_peg = transform([-length - 0.010, 0, 0])
    final_tcp = final_peg @ np.linalg.inv(nominal_e)
    if action == "a0":
        return [(40, final_tcp)]
    withdraw = np.asarray(start).copy()
    withdraw[0, 3] -= 0.012
    aligned_peg = transform([-2 * length - 0.006, 0, 0])
    return [
        (10, withdraw),
        (10, aligned_peg @ np.linalg.inv(nominal_e)),
        (40, final_tcp),
    ]


def registration_payload():
    proposal = json.loads(PROPOSAL.read_text())
    for name, expected in proposal["checks"]["source_sha256"].items():
        assert sha(name) == expected, f"Frozen source mismatch: {name}"
    extra = [
        ".venv/lib/python3.12/site-packages/mani_skill/envs/sapien_env.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/registration.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/structs/base.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/structs/actor.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/structs/articulation.py",
        ".venv/lib/python3.12/site-packages/mani_skill/agents/controllers/pd_joint_pos.py",
        "scripts/rpd_assembly_contract.py",
        "scripts/rpd_assembly_worker.py",
        "scripts/rpd_assembly_run.py",
        "scripts/rpd_assembly_audit.py",
        "tests/test_rpd_assembly.py",
        str(PROPOSAL),
        "papers/rss2027_rpd_stage1/reviews/STAGE2_VALIDATION_SPEC.md",
        "CODEX_ASSEMBLY_PRELIMINARY_PROTOCOL.md",
        "RPD_RSS2027_STAGE1_V21_EDITORIAL.pdf",
        sys.executable,
    ]
    extra += [
        str(p) for p in Path(".venv/lib/python3.12/site-packages/sapien").rglob("*.so")
    ]
    extra += [
        str(p)
        for p in Path(
            ".venv/lib/python3.12/site-packages/mani_skill/assets/robots/panda"
        ).rglob("*")
        if p.is_file()
    ]
    hashes = dict(proposal["checks"]["source_sha256"])
    hashes.update({p: sha(p) for p in extra})
    return {
        "schema": SCHEMA,
        "candidates": [r.model_dump() for r in candidates()],
        "source_sha256": hashes,
        "versions": {
            n: importlib.metadata.version(n)
            for n in ("mani-skill", "sapien", "numpy", "torch", "scipy", "pydantic")
        },
        "method": "NOMINAL_SOURCE_EXPLORATORY_NOT_LEARNED_RPD",
        "physics_qualification_cap_seconds": 10800,
        "episode_timeout_seconds": 60,
        "exploratory_maximum_source_episodes": 24 * 7,
        "exploratory_cap_seconds": 24 * 7 * 60,
        "total_artifact_limit_bytes": 2 * 1024**3,
        "source_choices": {
            "physics_hz": 100,
            "control_hz": 20,
            "wrapper_ticks": 200,
            "prefix_ticks": 30,
            "remaining_ticks": 80,
            "probe_ticks": 10,
            "root_grasp": {"min_force_N": 0.5, "max_angle_deg": 85},
            "IK": {
                "iterations": 100,
                "seed_arm": [
                    0,
                    np.pi / 8,
                    0,
                    -5 * np.pi / 8,
                    0,
                    3 * np.pi / 4,
                    -np.pi / 4,
                ],
            },
            "root_contact_samples": "six inclusive100Hz samples spanning0.05seconds; all>=0.5N",
            "goal_dwell_samples": 26,
            "two_policy_parameters": "same fixed nominal E for both;no learning from qualification/exploratory outcomes",
            "replay": "fresh process and fixed-prefix regeneration only; no get/set-state restoration",
            "root_parity": {
                "translation_m": 1e-5,
                "rotation_rad": 1e-4,
                "other_numeric_abs": 1e-5,
                "clock_and_flags": "exact",
            },
            "monitors": "native after_simulation_step hook, read-only100Hz; no state/controller mutation",
            "one_parent": "all seven/six branches and repeats cluster within original parent",
            "initialization_controller_reset": "once before any physical prefix step; never at root or between diagnostic and recovery",
            "C_does_not_short_circuit_physics": True,
            "terminal_goal": "stable mid-depth registered goal; native flag also logged; no relabeling",
            "exploratory_approval": "user requests execution if qualification passes",
        },
        "confirmation_execution_authorized": False,
    }


def active_registration_path():
    repaired = sorted(BASE.glob("registration_sourcefix[0-9][0-9].json"))
    return repaired[-1] if repaired else BASE / "registration.json"


def episode_directory(job):
    active = active_registration_path()
    suffix = (
        "_" + active.stem.removeprefix("registration_")
        if active.name != "registration.json"
        else ""
    )
    return BASE / "episodes" / (job.job_id + suffix)


def verify_registration():
    path = active_registration_path()
    packet = json.loads(path.read_text())
    expected = path.with_suffix(".sha256").read_text().strip()
    assert sha(path) == expected
    if path.name != "registration.json":
        old = json.loads((BASE / "registration.json").read_text())
        assert (
            sha(BASE / "registration.json")
            == (BASE / "registration.sha256").read_text().strip()
        )
        for name in (
            "schema",
            "candidates",
            "versions",
            "source_choices",
            "method",
            "physics_qualification_cap_seconds",
            "episode_timeout_seconds",
            "exploratory_cap_seconds",
        ):
            assert packet[name] == old[name], name
        for name, expected in old["source_sha256"].items():
            if not name.startswith(
                ("scripts/rpd_assembly_", "tests/test_rpd_assembly")
            ):
                assert packet["source_sha256"][name] == expected, name
    for name, value in packet["source_sha256"].items():
        assert sha(name) == value, name
    for name, value in packet["versions"].items():
        assert importlib.metadata.version(name) == value, name
    return packet


if __name__ == "__main__":
    write(BASE / "registration.json", registration_payload())
    (BASE / "registration.sha256").write_text(sha(BASE / "registration.json") + "\n")
    print("REGISTERED36 candidates;original512 confirmation closed;zero physics")
