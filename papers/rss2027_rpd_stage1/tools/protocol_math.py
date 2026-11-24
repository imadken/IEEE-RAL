"""Author-review design manifest and independent offline statistical checks.

This module has no environment/controller construction and produces no robot
observations. Candidate seeds and command samples are proposed inputs only.
"""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator
from scipy.optimize import brentq, minimize_scalar
from scipy.special import xlogy
from scipy.stats import beta, binom, norm

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]


class Protocol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["PROPOSED_AUTHOR_REVIEW_NOT_PHYSICS_QUALIFIED"] = (
        "PROPOSED_AUTHOR_REVIEW_NOT_PHYSICS_QUALIFIED"
    )
    new_physics_authorized: Literal[False] = False
    sim_hz: int = 100
    control_hz: int = 20
    episode_limit_ticks: int = 200
    prefix_ticks: int = 30
    probe_ticks: int = 10
    remaining_ticks: int = 80
    long_remaining_ticks: int = 160
    dwell_samples: int = 26
    clearance_m: float = 0.003
    qualification_candidates: int = 12
    discovery_candidates: int = 64
    confirmation_candidates: int = 512
    worker_hour_cap: int = 28
    source_timeout_seconds: int = 60
    root_feature_dim: int = 28
    response_feature_dim: int = 230

    @model_validator(mode="after")
    def source_clocks_match(self):
        assert self.sim_hz % self.control_hz == 0
        assert self.prefix_ticks + self.long_remaining_ticks <= self.episode_limit_ticks
        assert self.probe_ticks / self.control_hz == 0.5
        assert (self.dwell_samples - 1) / self.sim_hz == 0.25
        assert self.response_feature_dim == 23 * self.probe_ticks
        return self


def candidate_manifest(config: Protocol) -> list[dict]:
    records = []
    seeds = set()
    for phase, count in (
        ("qual", config.qualification_candidates),
        ("discovery", config.discovery_candidates),
        ("confirmation", config.confirmation_candidates),
    ):
        for index in range(count):
            prefix = f"RPD-assembly-v1/{phase}/{index}"
            geometry = int.from_bytes(
                hashlib.sha256((prefix + "/geometry").encode()).digest()[:4], "big"
            )
            assert geometry not in seeds, (
                "Collision in fixed candidate seeds; do not substitute IDs"
            )
            seeds.add(geometry)
            records.append(
                {
                    "candidate_id": prefix,
                    "phase": phase,
                    "index": index,
                    "native_geometry_seed": geometry,
                    "PCG64_fault_seed_sha256": hashlib.sha256(
                        (prefix + "/fault").encode()
                    ).hexdigest(),
                    "status": "DESIGN_INPUT_NOT_EXECUTED",
                }
            )
    return records


def lower(k: int, n: int, alpha: float = 0.025) -> float:
    return 0.0 if k == 0 else float(beta.ppf(alpha, k, n - k + 1))


def upper(k: int, n: int, alpha: float = 0.025) -> float:
    return 1.0 if k == n else float(beta.ppf(1 - alpha, k + 1, n - k))


def paired_exact(
    plus: int, minus: int, n: int, missing: int = 0
) -> tuple[float, float]:
    if min(plus, minus, missing) < 0 or plus + minus + missing > n:
        raise ValueError("Invalid independent-parent counts")
    return (
        lower(plus, n, 0.0125) - upper(minus + missing, n, 0.0125),
        upper(plus + missing, n, 0.0125) - lower(minus, n, 0.0125),
    )


def profile_interval(plus: int, minus: int, n: int) -> tuple[float, float]:
    """Standard asymptotic trinomial LR interval, with explicit boundary checks."""
    if n < 1 or min(plus, minus) < 0 or plus + minus > n:
        raise ValueError("Invalid paired counts")
    counts = np.array([plus, minus, n - plus - minus])
    unrestricted = float(np.sum(xlogy(counts, counts / n)))

    def likelihood_ratio(delta):
        a, b = max(0.0, -delta), (1 - delta) / 2

        def ll(q):
            probabilities = np.maximum(0.0, [q + delta, q, 1 - 2 * q - delta])
            return float(np.sum(xlogy(counts, probabilities)))

        optimum = max(ll(a), ll(b))
        if b > a:
            fit = minimize_scalar(
                lambda q: -ll(q),
                bounds=(a, b),
                method="bounded",
                options={"xatol": 1e-12},
            )
            optimum = max(optimum, -float(fit.fun))
        return 2 * (unrestricted - optimum) - 3.841459

    point = (plus - minus) / n
    lo = (
        -1.0
        if likelihood_ratio(-1.0) <= 0
        else brentq(likelihood_ratio, -1.0, point, xtol=1e-8)
    )
    hi = (
        1.0
        if likelihood_ratio(1.0) <= 0
        else brentq(likelihood_ratio, point, 1.0, xtol=1e-8)
    )
    return float(lo), float(hi)


def eb_lower(scores: list[float], missing: int = 0, alpha: float = 0.025) -> float:
    b = -math.log(0.001)
    n = len(scores) + missing
    if n < 2 or missing < 0 or any(not math.isfinite(x) or abs(x) > b for x in scores):
        raise ValueError(
            "At least two independent bounded parent contributions required"
        )
    mean = (sum(scores) - missing * b) / n
    variance = n * b * b / (n - 1) if missing else float(np.var(scores, ddof=1))
    return (
        mean
        - math.sqrt(2 * variance * math.log(2 / alpha) / n)
        - 14 * b * math.log(2 / alpha) / (3 * (n - 1))
    )


def brute_tree_example() -> dict:
    # Constructed complete three-world model, independent of the production planner.
    success = {
        "hold": [[1, 0], [1, 1], [0, 1]],
        "fine": [[1, 0], [0, 1], [0, 0]],
        "coarse": [[1, 0], [1, 1], [0, 1]],
    }
    responses = {"hold": [0, 0, 0], "fine": [0, 1, 2], "coarse": [0, 0, 1]}
    result = {}
    for probe, labels in responses.items():
        best = 0.0
        for actions in itertools.product((0, 1), repeat=max(labels) + 1):
            best = max(
                best, sum(success[probe][i][actions[labels[i]]] for i in range(3)) / 3
            )
        decomposed = (
            sum(
                max(
                    sum(success[probe][i][a] for i in range(3) if labels[i] == j)
                    for a in (0, 1)
                )
                for j in set(labels)
            )
            / 3
        )
        assert math.isclose(best, decomposed)
        result[probe] = best
    assert result == {"hold": 2 / 3, "fine": 2 / 3, "coarse": 1.0}
    return {
        "scope": "ANALYTICAL_WORLD_NOT_ROBOT_DATA",
        "brute_policy_tree_completion": result,
        "same_objective_and_Bayesian_consensus_equivalent": True,
    }


def checks() -> dict:
    config = Protocol()
    records = candidate_manifest(config)
    critical = next(k for k in range(513) if binom.sf(k - 1, 512, 0.1) <= 0.025)
    assert critical == 66
    command_y = [
        0.0 if k == 10 else 0.003 * math.sin(2 * math.pi * k / 10) for k in range(1, 11)
    ]
    assert command_y[-1] == 0.0 and len(command_y) == 10
    # Two analytical atoms show H1's two properties need not co-occur.
    disjoint = {
        "scope": "ANALYTICAL_DISTRIBUTION_NOT_EPISODES",
        "atoms": [
            {"probability": 0.1, "J": 1, "D": 0.0},
            {"probability": 0.9, "J": 0, "D": math.log(3)},
        ],
        "q": 0.1,
        "mean_score": 0.9 * math.log(3),
        "mean_weighted_score": 0.0,
    }
    values = {
        "status": "OFFLINE_MATH_ONLY_NO_PHYSICS",
        "H1_rejection_count_n512": critical,
        "H1_size_boundary": float(binom.sf(65, 512, 0.1)),
        "H1_component_power_at_true_rate15pct": float(binom.sf(65, 512, 0.15)),
        "H1_zero_event_upper975": upper(0, 512),
        "H2_normal_halfwidth": float(
            norm.ppf(0.975) * math.sqrt((0.20 - 0.10**2) / 512)
        ),
        "H2_profile_scope": "Asymptotic; <30discordances or any missing labels use conservative exact bounds; exact sensitivity always reported.",
        "paired_cases": {
            f"{p},{m}": {
                "profile": profile_interval(p, m, 512),
                "exact": paired_exact(p, m, 512),
            }
            for p, m in ((0, 0), (76, 26), (60, 30), (110, 12), (512, 0))
        },
        "feature_dimensions": {"X": 28, "Y": 230},
        "candidate_count": len(records),
        "all_native_seed_values_unique": True,
        "clocks": {
            "primary_total_ticks": 110,
            "sensitivity_total_ticks": 190,
            "wrapper_limit": 200,
            "dwell_samples": 26,
        },
        "dither_y_command_samples_m": command_y,
        "costs": {
            "discovery_terminal": 512,
            "confirmation_matched_terminal": 3072,
            "confirmation_shared_direct": 512,
            "base_terminal": 4096,
            "screening_source_episodes": 576,
            "final_estimator_parity_terminal": 16,
            "qualification_terminal_max": 98,
            "qualification_screening_max": 12,
            "maximum_base_source_episodes": 4798,
            "long_deadline_extra_terminal_max": 384,
            "extra_existing_skill_conditional": 192,
            "maximum_with_both_sensitivities": 5374,
        },
        "constructed_H1_disjoint_properties": disjoint,
        "constructed_planning": brute_tree_example(),
        "root_estimator": "Fit from discovery root X only; freeze per parent across probe/hold/direct. No response-dependent macro parameters.",
        "STOP": "Scored from recorded prefix completion flag, no imputed missing rollout",
        "available_extra_skill": None,
        "new_physics": 0,
    }
    assert values["costs"]["base_terminal"] == 64 * 8 + 512 * 7
    source_names = [
        ".venv/lib/python3.12/site-packages/mani_skill/envs/tasks/tabletop/peg_insertion_side.py",
        ".venv/lib/python3.12/site-packages/mani_skill/agents/robots/panda/panda.py",
        ".venv/lib/python3.12/site-packages/mani_skill/agents/controllers/pd_ee_pose.py",
        ".venv/lib/python3.12/site-packages/mani_skill/agents/controllers/utils/kinematics.py",
        ".venv/lib/python3.12/site-packages/mani_skill/utils/structs/types.py",
        ".venv/lib/python3.12/site-packages/mani_skill/envs/scene.py",
    ]
    values["source_sha256"] = {
        name: hashlib.sha256((REPO / name).read_bytes()).hexdigest()
        for name in source_names
    }
    values["installed_versions"] = {
        name: importlib.metadata.version(name)
        for name in ("mani-skill", "sapien", "numpy", "torch", "scipy", "pydantic")
    }
    return {
        "protocol": config.model_dump(),
        "checks": values,
        "candidate_inputs": records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = checks()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "passed": True,
                "new_physics": 0,
                "candidates": len(result["candidate_inputs"]),
            }
        )
    )
