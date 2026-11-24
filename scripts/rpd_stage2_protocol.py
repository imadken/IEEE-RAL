"""Inactive fixed Stage 2 parent reservation and calibration-power arithmetic."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from scipy.stats import beta, binom


def write(output):
    assert not output.exists(), "Fresh output required"
    output.mkdir(parents=True)
    parents = []
    seen = set()
    for task, base in [("PickCube-v1", 2004000000), ("PushCube-v1", 2004100000)]:
        rows = []
        for phase, offset, n in [
            ("technical_pilot", 0, 10),
            ("discovery", 1000, 64),
            ("independent_calibration", 10000, 512),
            ("untouched_test", 20000, 256),
        ]:
            for i in range(n):
                seed = base + offset + i
                assert seed not in seen and seed < 2**31
                seen.add(seed)
                parent = hashlib.sha256(
                    f"RPD-S2-20261119|{task}|{phase}|{i}|{seed}".encode()
                ).hexdigest()
                rows.append(
                    {
                        "task": task,
                        "phase": phase,
                        "index": i,
                        "seed": seed,
                        "parent_id": parent,
                        "status": "INACTIVE_RESERVED_NOT_COLLECTED",
                        "qualified": None,
                        "outcome": None,
                        "condition": "nominal",
                        "evaluator_oracle_subset": False,
                    }
                )
        test = sorted(
            [r for r in rows if r["phase"] == "untouched_test"],
            key=lambda r: hashlib.sha256(
                ("RPD-ORACLE-SUBSET-v1|" + r["parent_id"]).encode()
            ).hexdigest(),
        )
        for row in test[:128]:
            row["evaluator_oracle_subset"] = True
        parents.extend(rows)
    assert len(parents) == 1684 and len({r["parent_id"] for r in parents}) == 1684
    manifest = output / "reserved_parents.jsonl"
    manifest.write_text(
        "".join(
            json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in parents
        )
    )
    tail = 0.05 / (2 * 6 * 4)
    perfect = math.ceil(math.log(tail) / math.log(0.9))
    powers = []
    for n in [64, 128, 256, 512]:
        passing = [k for k in range(1, n + 1) if beta.ppf(tail, k, n - k + 1) >= 0.9]
        minimum = min(passing) if passing else None
        powers.append(
            {
                "parents_in_frozen_terminal_leaf": n,
                "minimum_successes_to_qualify": minimum,
                "qualification_probability_if_true_success_0_99": 0
                if minimum is None
                else float(binom.sf(minimum - 1, n, 0.99)),
                "qualification_probability_if_true_success_0_95": 0
                if minimum is None
                else float(binom.sf(minimum - 1, n, 0.95)),
                "scope": "ANALYTICAL_DESIGN_POWER_NOT_OBSERVED_ROBOT_RATE",
            }
        )
    plan = {
        "status": "INACTIVE_PROPOSED_ONLY_NO_PHYSICS_AUTHORIZATION",
        "families": ["PickCube-v1", "PushCube-v1"],
        "independent_parent_slots_per_family": {
            "technical_pilot": 10,
            "discovery": 64,
            "calibration": 512,
            "test": 256,
        },
        "completed_new_parents_per_family": 0,
        "historical_seed_collision_check": "REQUIRED_BEFORE_COLLECTION_AGAINST_ALL_HISTORY; stop on collision without outcome-based replacement",
        "family_substitution": "PROHIBITED; retain a failed nominated family",
        "condition": "Nominal cached native prefix and natural reset distribution; no fault/task shopping",
        "sensor_menu": "Seven arm-joint qpos/qvel, FK TCP xyz and20Hz clock only",
        "discovery_encoding": "ONE binary split of ONE of the five frozen response bins; integer threshold candidates0..20. Maximize mean discovery Gini reduction for the root pose-cell label across both probes; lexicographic ties. Common frozen split for all methods before calibration; an uninformative split is a valid null.",
        "policy_limits": {
            "max_probes": 2,
            "probe_controls_each": 10,
            "recovery_macro_controls": 70,
            "post_checkpoint_controls_every_policy": 90,
            "terminal_leaves_at_most": 4,
        },
        "common_deadline": "Native hold pads after the70-control macro, or after STOP, to90 controls. Record macro-end and common-deadline native success. Never impute STOP or missing outcomes.",
        "policies": [
            "fixed_continue",
            "fixed_recover",
            "physical_safety_filtered_entropy",
            "one_step_task_consensus",
            "static_transition_ignored_ERR_ABLATION",
            "exact_viability_contingent",
        ],
        "same_objective_control": "Independent full-model strong/POMDP control with identical state, sensors, actions, horizon and worst-cost objective. Share identical executions; no new algorithmic gain is expected.",
        "same_information": "Identical discovery model, sensor/probe menu and calibration budget; evaluator oracle rows isolated. Static transition ignoring violates the model-based guarantee. It may receive the same independent empirical terminal gate, accurately labelled as such.",
        "data_allocation": {
            "pilot": 10 * 21 * 2,
            "discovery": 64 * 14,
            "calibration": 512 * 6,
            "selected_policy_test": 256 * 6,
            "held_out_oracle_evaluator_only": 128 * 14,
        },
        "maximum_native_episodes_per_family": 7716,
        "estimated_seconds_per_episode": {"PickCube-v1": 10, "PushCube-v1": 12},
        "future_wall_caps_worker_hours": {"PickCube-v1": 26, "PushCube-v1": 32},
        "pilot_cap_worker_hours_per_family": 2,
        "pilot_cap_included_in_family_cap": True,
        "future_storage_cap_GiB_per_family": 8,
        "resource_status": "ESTIMATES_REQUIRE_SEPARATE_FUTURE_CHARTER; no current authority for58worker-hours",
        "atomic_stop": "Close/seal the current native episode and parent at a ceiling. Keep incomplete counts without replacement.",
        "calibration": {
            "source": "New independent parents, frozen policy-induced terminal-history population; no DSRE interval transfer",
            "available_now": False,
            "future_optional_success_target": 0.9,
            "tasks": 2,
            "policies": 6,
            "frozen_terminal_strata_at_most": 4,
            "one_sided_CP_tail": tail,
            "familywise_alpha": 0.05,
            "minimum_all_success_leaf_parents": perfect,
            "design_power": powers,
            "gate": "LowerCP>=.90 in the WHOLE selected terminal stratum. Failure withholds/STOPs; no upstream replanning or policy refit on calibration outcomes.",
            "scope": "Conditional success of that fixed source/population/macro-with-padding; not universal G, path safety or complete physical dynamics. The current exact planner has no stochastic extension.",
            "missingness": "A post-qualification missing endpoint blocks unconditional complete-case CP claims without a justified censoring model; preserve missing labels and worst-case completion bounds.",
        },
        "H1": {
            "statement": "A discovery-frozen more-disambiguating probe can destroy the fixed-macro recovery option",
            "measurement": "Sixteen evaluator-only ROOT object-minus-TCP xy pose cells with cuts-.03,0,.03m. Condition the discovery-only Laplace-one decoder on the SAME root proprioceptive signature and then augment with each probe response. Quantize root qpos at.01rad, qvel at.1rad/s and TCP at.005m; unseen signatures use the discovery prior. Compare augmented decoders on untouched parents and report the root-only decoder. This is a conditional information PROXY, not Shannon mutual information or evidence about already-visible facts.",
            "probe_order": "Discovery decoder accuracy, then probe ID; freeze before calibration/test. Retain a tie.",
            "support_criterion": "Corrected lower bound on held-out decoder-accuracy difference>.05 AND lowerCP(prevalence K_low_nonempty/K_high_empty)>.05 on128 hash-fixed oracle parents. No favorable probe replacement.",
            "K": "Macros with actually recorded native success from the actual post-probe state at the same deadline",
        },
        "H2": {
            "statement": "At90 native controls, qualified viability-aware probing improves completion over filtered entropy by>.05",
            "test_parents": 256,
            "test": "Conservative paired bound L_CP(RPD_only_success)-U_CP(entropy_only_success); split endpoint alpha across both marginal tails",
            "full_model_control": "Expected equality; differences require an interface/model/tie-break audit, not a solver novelty claim",
            "secondary": [
                "actual probe controls",
                "native completion",
                "rescues vs no probe",
                "lost recoverability",
                "futile attempts",
                "withholding",
                "sampled allowed-set violations",
                "attrition",
            ],
        },
        "H3": {
            "statement": "Finite policy/obstruction classifications remain source-grounded in the fixed held-out oracle subset",
            "test": "Every physical witness has actual source rows; upperCP(model/source mismatch)<=.05 on128 oracle parents",
            "scope": "No-policy is horizon/menu conditional. Missing or unknown rows do not establish physical impossibility; zero observed mismatches is not an all-state guarantee.",
        },
        "hypothesis_alpha": {
            "endpoint_family_size": 8,
            "one_sided_endpoint_alpha": 0.05 / 8,
            "accounting": "Two H1 endpoints, one H2 and one H3, per family; paired-difference bounds split their endpoint alpha further across two tails",
        },
        "pilot_guards": [
            "Exact nominated source versions,20Hz,200-control episode limit, fixed prefix65/53; already-successful prefixes counted separately and never replaced",
            "Complete continuous traces and controller-memory lineage; no within-history reset, state injection or rewind",
            "Repeat parity: position<=1e-5m, orientation/qpos<=1e-4rad, velocity/observation<=1e-4,time<=1e-9s, exact contacts and task flags",
            "All native channels finite and all ten probe frames present; missing observations stop, never become false",
            "Verify nonzero native actuator/TCP effect against neutral hold. No positive task effect or favorable action diversity is required for qualification",
            "Object motion/contact change remains evaluator-only; force, damage and continuous-time safety are unmeasured",
            "A failed source/coupling guard blocks that family, without repair/task substitution in the registered study",
        ],
        "negative_interpretations": [
            "Passive or uninformative probes: no demonstrated physical tradeoff",
            "Motion but no option loss: H1 unestablished",
            "Full-model tie: expected known formulation",
            "No qualified terminal leaves: insufficient support, not invented success",
            "Both macros fail: fixed repertoire boundary, no new skill",
            "Model/source mismatch: narrow scope, not physical impossibility",
        ],
        "reserved_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }
    assert sum(plan["data_allocation"].values()) == 7716
    (output / "protocol.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "reserved_parents": len(parents),
                "actual_outcomes": 0,
                "maximum_future_episodes_per_family": 7716,
                "minimum_perfect_leaf_n": perfect,
                "design_power": powers,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    write(parser.parse_args().output)
