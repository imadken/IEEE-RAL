"""Offline nominal proofs, design precision and sealed-evidence recount for RPD V2.

No simulator, robot controller or environment constructor is imported or executed.
"""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from rpd_cases import model
from rpd_independent_oracle import exhaustive
from rpd_isolation_handoff import technical_view
from scipy.special import xlogy
from scipy.stats import beta, binom, chi2, norm

from dual_rec.recoverability.planner import plan_probes

BASE = Path("research/rpd_stage1_v2")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def illustration():
    """New constructed equal-duration model; original historical examples untouched."""
    roots = [f"{s}0" for s in "ABC"]
    held = [f"{s}H" for s in "ABC"]
    fine = [f"{s}F" for s in "ABC"]
    options = {"A": {"a0"}, "B": {"a0", "a1"}, "C": {"a1"}}
    successes = {}
    for state in roots + held + fine:
        g = (
            options[state[0]]
            if state[-1] != "F"
            else ({"a0"} if state[0] == "A" else {"a1"} if state[0] == "B" else set())
        )
        successes[state] = {a: a in g for a in ("a0", "a1")}
    transitions, observations, enabled = {}, {}, {}
    for p in ("hold", "p1_fine", "p2_coarse"):
        transitions[p] = {
            s: (s[0] + ("F" if p == "p1_fine" else "H")) if s in roots else s
            for s in successes
        }
        observations[p] = {
            s: (
                "same"
                if p == "hold"
                else s[0]
                if p == "p1_fine"
                else "AB"
                if s[0] in "AB"
                else "C"
            )
            for s in successes
        }
        enabled.update({(p, s): s in roots for s in successes})
    return model(
        successes,
        transitions,
        observations,
        costs={p: "1/2" for p in transitions},
        enabled=enabled,
        initial=roots,
        horizon=1,
        budget="1/2",
        name="CONSTRUCTED_EQUAL_DURATION_3WORLDS_CLOCK_AUGMENTED_V2",
    )


def nominal_regressions():
    checked = 0
    for bits, targets, observations, safety in itertools.product(
        itertools.product((False, True), repeat=4),
        itertools.product((0, 1), repeat=2),
        itertools.product(("y0", "y1"), repeat=2),
        itertools.product((False, True), repeat=2),
    ):
        g = {s: {"a0": False, "a1": False} for s in ("R0", "R1")}
        g.update({f"S{i}": {"a0": bits[2 * i], "a1": bits[2 * i + 1]} for i in (0, 1)})
        t = {"p": {s: f"S{targets[int(s[1])]}" if s.startswith("R") else s for s in g}}
        o = {"p": {s: observations[int(s[1])] for s in g}}
        enabled = {("p", s): s.startswith("R") for s in g}
        problem = model(
            g,
            t,
            o,
            costs={"p": "1/2"},
            enabled=enabled,
            path_safe={("p", f"R{i}"): safety[i] for i in (0, 1)},
            initial=["R0", "R1"],
            horizon=1,
            budget="1/2",
        )
        groups = {}
        for i in (0, 1):
            target = targets[i]
            groups.setdefault(observations[target], set()).add(f"S{target}")
        criterion = all(safety) and all(
            any(all(g[s][a] for s in group) for a in ("a0", "a1"))
            for group in groups.values()
        )
        result = plan_probes(problem)
        oracle, _ = exhaustive(problem.model_dump(mode="json"))
        assert (
            criterion
            == (oracle is not None)
            == (result.status == "ROBUST_FINITE_MODEL_RECOVERY")
        )
        checked += 1
    assert checked == 1024
    return checked


def lower(k, n, alpha):
    return 0.0 if k == 0 else float(beta.ppf(alpha, k, n - k + 1))


def upper(k, n, alpha):
    return 1.0 if k == n else float(beta.ppf(1 - alpha, k + 1, n - k))


def paired_profile_test(plus, minus, n, margin=0.05):
    """Standard trinomial profile LR at a positive risk-difference margin.

    Asymptotic test only; no finite-sample coverage claim. Counts with fewer than
    30 discordances use the separately specified conservative exact bound.
    """
    plus, minus = np.asarray(plus), np.asarray(minus)
    ties = n - plus - minus
    b = plus + minus - margin * (plus + 3 * minus + 2 * ties)
    c = minus * margin * (1 - margin)
    q = np.clip((b + np.sqrt(b * b + 8 * n * c)) / (4 * n), 0, (1 - margin) / 2)
    alternative = (
        xlogy(plus, plus / n) + xlogy(minus, minus / n) + xlogy(ties, ties / n)
    )
    null = xlogy(plus, q + margin) + xlogy(minus, q) + xlogy(ties, 1 - 2 * q - margin)
    reject = ((plus - minus) / n > margin) & (
        2 * (alternative - null) > chi2.ppf(0.95, 1)
    )
    lo = np.where(plus == 0, 0, beta.ppf(0.0125, plus, n - plus + 1))
    hi = np.where(minus == n, 1, beta.ppf(0.9875, minus + 1, n - minus))
    exact = np.atleast_1d(lo - hi > margin)
    return np.where(plus + minus < 30, exact, reject)


def precision():
    n, alpha = 512, 0.025
    critical = next(k for k in range(n + 1) if binom.sf(k - 1, n, 0.1) <= alpha)
    # Conservative exact paired completion difference, not an unpaired estimator.
    lo = np.array([lower(k, n, alpha / 2) for k in range(n + 1)])
    hi = np.array([upper(k, n, alpha / 2) for k in range(n + 1)])
    power = 0.0
    profile_power = 0.0
    for plus in range(n + 1):
        minus = np.arange(n - plus + 1)
        allowed = lo[plus] - hi[minus] > 0.05
        power += float(
            binom.pmf(plus, n, 0.15)
            * np.sum(binom.pmf(minus, n - plus, 0.05 / 0.85)[allowed])
        )
        profile = paired_profile_test(np.full(len(minus), plus), minus, n)
        profile_power += float(
            binom.pmf(plus, n, 0.15)
            * np.sum(binom.pmf(minus, n - plus, 0.05 / 0.85)[profile])
        )
    return {
        "scope": "ANALYTICAL_DESIGN_CALCULATIONS_NOT_ROBOT_OUTCOMES",
        "n": n,
        "alpha_per_primary_hypothesis": alpha,
        "H1_null_boundary": 0.1,
        "H1_reject_from_events": critical,
        "H1_test_size_at_boundary": float(binom.sf(critical - 1, n, 0.1)),
        "H1_power_at_true_rate_15pct": float(binom.sf(critical - 1, n, 0.15)),
        "H1_zero_event_upper975": 1 - alpha ** (1 / n),
        "H2_normal_halfwidth_at_discordance20pct_effect10pct": float(
            norm.ppf(0.975) * math.sqrt((0.20 - 0.10**2) / n)
        ),
        "H2_exact_conservative_bound_power_at_pplus15pct_pminus5pct": power,
        "H2_paired_profile_power_at_pplus15pct_pminus5pct": profile_power,
        "H2_primary_interval_scope": "Asymptotic trinomial profile-likelihood95%CI; <30discordant pairs use conservative exact CP-difference bounds. Exact CP sensitivity reported for all counts. No exact finite-sample H2 coverage claim.",
        "H2_all_zero_discordance_upper_unseen_plus": upper(0, n, alpha / 2),
        "confirmation_terminal_evaluations": 512 * 3 * 2,
        "discovery_terminal_evaluations": 64 * 3 * 2,
        "direct_selected_confirmation_evaluations": 512,
        "base_planned_evaluations_excluding_source_pilot_and_parity": 3968,
        "deadline_sensitivity_extra_evaluations": 64 * 3 * 2,
        "extra_skill_sensitivity_extra_evaluations_if_bound": 64 * 3,
        "information_bound": "Smoothed probabilities>=epsilon=1e-3; paired log-score difference in[-b,b], b=-log(epsilon). Empirical Bernstein L=mean-sqrt(2*unbiased_variance*log(2/alpha)/n)-14*b*log(2/alpha)/(3*(n-1)). Apply separately to probe-minus-baseline and probe-minus-hold contrasts; aggregate predictive signal, not per-erasure-event informativeness.",
        "H2_bound": "LowerCP(n_plus,n,alpha/2)-UpperCP(n_minus,n,alpha/2); no independence of discordant counts assumed. Conservative power is lower than normal halfwidth suggests.",
    }


def run(output):
    assert not output.exists(), "Fresh offline output required"
    output.mkdir(parents=True)
    example = illustration()
    raw = example.model_dump(mode="json")
    answer = plan_probes(example)
    oracle, count = exhaustive(raw)
    assert answer.policy.action_id == "p2_coarse" and oracle is not None
    g = {
        s["state_id"]: {r["action_id"] for r in s["recoveries"] if r["task_success"]}
        for s in raw["states"]
    }
    rows = [
        {
            "world": s,
            "hold_K": sorted(g[s + "H"]),
            "fine_K": sorted(g[s + "F"]),
            "coarse_K": sorted(g[s + "H"]),
        }
        for s in "ABC"
    ]
    details = {
        "scope": "CONSTRUCTED_FINITE_MODEL_NOT_ROBOT_DATA",
        "model": raw,
        "clock_seconds": {"initial": 4, "post_probe": 3.5},
        "equal_probe_durations_seconds": 0.5,
        "prior": {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3},
        "rows": rows,
        "information_nats": {
            "fine": math.log(3),
            "coarse": -(2 / 3) * math.log(2 / 3) - (1 / 3) * math.log(1 / 3),
            "hold": 0,
        },
        "fine_analytical_erasure_world": "C",
        "fine_analytical_partial_loss_world": "B",
        "best_robust_probe": answer.policy.action_id,
        "policy_tree_oracle_enumerated": count,
        "analytical_completion": {
            "fine": 2 / 3,
            "coarse": 1,
            "task_consensus": 1,
            "same_objective_planner": 1,
        },
    }
    save(output / "illustration.json", details)
    save(
        output / "nominal_verification.json",
        {
            "passed": True,
            "one_probe_equivalence_exhaustive_models": nominal_regressions(),
            "scope": "Finite deterministic complete model, admissible probe paths and complete support. Not a guarantee under physical/model mismatch.",
        },
    )
    sample = precision()
    supervisor = json.loads(
        (BASE / "supervisor/SAMPLE_PRECISION_CHECK.json").read_text()
    )
    assert (
        sample["H1_reject_from_events"]
        == supervisor["binomial_rejection_count_at_least"]
    )
    assert (
        abs(
            sample["H1_power_at_true_rate_15pct"] - supervisor["power_if_true_rate_.15"]
        )
        < 1e-12
    )
    assert (
        abs(
            sample["H2_normal_halfwidth_at_discordance20pct_effect10pct"]
            - supervisor["H2_approx_95_halfwidth_at_discordance_.20_and_effect_.10"]
        )
        < 1e-12
    )
    save(output / "precision.json", sample)
    source = Path(
        ".venv/lib/python3.12/site-packages/mani_skill/envs/tasks/tabletop/peg_insertion_side.py"
    )
    text = source.read_text()
    assert "_clearance = 0.003" in text and "Only head position is used in fact" in text
    save(
        output / "assembly_source_review.json",
        {
            "mode": "READ_ONLY_NO_ENVIRONMENT_CONSTRUCTION",
            "source": str(source),
            "sha256": sha(source),
            "task": "PegInsertionSide-v1",
            "robot": "panda_wristcam",
            "clearance_per_side_m": 0.003,
            "geometry": "Square peg cross-section and square opening; not a circular radial-clearance model",
            "half_length_source_m": [0.085, 0.125],
            "half_width_source_m": [0.015, 0.025],
            "axis": "hole-local+x",
            "native_success": "head-in-hole-frame x>=-.015m and abs(y/z)<=hole_half_width; no explicit full-body alignment/stability/force condition",
            "available_online_channels": "Seven arm qpos/qvel, native FK tcp_pose and declared execution history; no bound force sensor",
            "privileged_evaluator_fields": [
                "peg_pose",
                "box_hole_pose",
                "peg_half_size",
                "box_hole_radius",
                "contact points",
                "latent generator mode",
                "future outcomes",
            ],
            "leakage_limit": "If exact peg/hole geometry defining alignment label Z enters X, the label may already be observable; cannot call it hidden diagnostic information",
            "proposed_only": {
                "probe_seconds": 0.5,
                "remaining_seconds": 4,
                "deadline_sensitivity_seconds": 8,
                "axial": "bounded preload normalized to clearance",
                "lateral": "one zero-net transverse dither at equal axial depth",
                "hold": "same commanded equilibrium, not measured-pose recentering or frozen simulation",
            },
            "unbound": [
                "qualified grasped post-failure checkpoint and replay prefix",
                "lateral/angular generator ranges and friction strata",
                "servo mode, gains and physical amplitude/withdrawal limits",
                "declared pose-estimation/grasp-transform interface",
                "diagnostic target Z and final feature encoding",
                "pre-existing third recovery skill for optional catalogue sensitivity",
                "terminal predicate adequacy for intended assembly goal",
            ],
            "assembly_source_qualified": False,
            "assembly_or_confirmation_outcomes": 0,
            "old_blocked_prefix_not_restarted": True,
        },
    )
    science = Path("research/rpd_source_isolation_20261119/final_audit/summary.json")
    technical = Path("research/rpd_source_isolation_20261119/technical_matches.json")
    s = json.loads(science.read_text())
    v = json.loads(technical.read_text())
    recomputed = json.loads(json.dumps(technical_view()))
    assert recomputed == v, "Raw technical-view mismatch"
    raw_sources = {
        r["path"]: r["sha256"]
        for task in recomputed["tasks"].values()
        for row in task["rows"]
        for r in row["probe_sources"] + row["hold_sources"]
    }
    assert all(sha(p) == expected for p, expected in raw_sources.items())
    assert all(r["limited_source_completion"] for r in s["tasks"].values())
    save(
        output / "preliminary_recount.json",
        {
            "source_hashes": {str(p): sha(p) for p in (science, technical)},
            "actual_episodes": sum(r["returned_complete"] for r in s["tasks"].values()),
            "parents_per_task": 1,
            "technical_view_recomputed_from_raw": True,
            "matched_raw_sources_verified": raw_sources,
            "tasks": {
                t: {
                    "episodes": r["returned_complete"],
                    "matched_histories": len(v["tasks"][t]["rows"]),
                    "seconds": r["worker_wall_seconds"],
                    "full_erasure_in_retrospective_technical_histories": sum(
                        bool(z["erasure"]) for z in v["tasks"][t]["rows"]
                    ),
                    "partial_option_loss_histories": sum(
                        bool(z["lost"]) for z in v["tasks"][t]["rows"]
                    ),
                }
                for t, r in s["tasks"].items()
            },
            "scope": "Correlated already-inspected Pick/Push source cases, GDB supervised; not assembly data or H1/H2 confirmation. Original native failures preserved; no global stability or crash cause established.",
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "nominal_models": 1024,
                "new_physics": 0,
                "H2_conservative_power": sample[
                    "H2_exact_conservative_bound_power_at_pplus15pct_pminus5pct"
                ],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
