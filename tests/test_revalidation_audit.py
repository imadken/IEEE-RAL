"""Independent freshness audit catches guard, sensor and denominator mistakes."""

import copy
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "revalidation_audit",
    Path(__file__).resolve().parents[1] / "scripts/revalidation_audit.py",
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def fixture(*, recheck=False, bias=False):
    action = {
        "name": "complete",
        "pre": [{"atom": "p", "positive": True}],
        "add": ["g"],
        "delete": [],
    }
    drop = {
        "name": "drop",
        "pre": [{"atom": "p", "positive": True}],
        "add": [],
        "delete": ["p"],
    }
    cached = {"p": not bias, "q": False, "g": False}
    context = {
        "base": {
            "model": {"atoms": ["p", "q", "g"], "constraints": []},
            "evidence": dict(cached),
            "plan": [action],
            "goal": [{"atom": "g", "positive": True}],
            "queries": [{"name": a, "atoms": [a], "cost": 1} for a in ("p", "q", "g")],
            "consequence": {"p": 2},
            "schedule_offset": 0,
        },
        "trusted_anchor": ["p"],
        "cache_observations": dict(cached),
        "observed_at": {a: 0 for a in cached},
        "updated_at": {a: 0 for a in cached},
        "known_after_cache": [],
        "pre_gap": 0,
        "age": 1,
        "cache_time": 0,
        "query_delay": 0,
        "parameters": {
            "event_hazard": 0.1,
            "sensor_error": 0.02,
            "missing_probability": 0.1,
            "permission_threshold": 0.85,
            "periodic_interval": 1,
            "expiry_steps": 0,
        },
    }
    episode = {
        "episode_id": "blocks-strips-typed-13/0/0/hidden_nominal",
        "parent_id": "blocks-strips-typed-13",
        "family": "blocks",
        "split": "qualification",
        "checkpoint": 0,
        "schedule": 0,
        "regime": "hidden_nominal",
        "context": context,
        "oracle_cache_state": ["p"],
        "oracle_state": [],
        "persistent_bias": ["p"] if bias else [],
        "missing_queries": [],
        "external_actions": [None, "drop"],
        "actual_event_hazard": 0.1,
        "actual_sensor_error": 0,
        "source_hashes": {"domain": "d", "problem": "p"},
    }
    task = {
        "task_id": episode["parent_id"],
        "family": "blocks",
        "split": "qualification",
        "actions": [action, drop],
        "plan": [action],
        "nominal_states": [["p"], ["p", "g"]],
        "source_hashes": episode["source_hashes"],
    }
    method = "B4" if recheck else "B1"
    reading = {
        "atom": "p",
        "value": bias,
        "measured_at": 1,
        "source": "symbolic_inspection",
        "conflict": False,
    }
    evidence = dict(cached)
    if recheck:
        evidence["p"] = bias
    decision = {
        "method": method,
        "choice": "RECOVER" if recheck else "CONTINUE",
        "status": "BELIEF_INVALID" if recheck else "VALID",
        "evidence": evidence,
        "readings": [reading] if recheck else [],
        "initial_plan_probability": 0.8,
        "final_plan_probability": 0 if recheck else 0.8,
        "final_current_probability": 0 if recheck else 0.8,
        "stale_risks": {"p": 0.1},
        "decision_seconds": 0,
        "sensor_seconds": 0,
        "belief_hypotheses": 2,
        "belief_failure": None,
    }
    fingerprint = audit.hashlib.sha256(
        json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    wrong = int(not bias)
    row = {
        "episode_id": episode["episode_id"],
        "parent_id": episode["parent_id"],
        "family": "blocks",
        "regime": "hidden_nominal",
        "method": method,
        "budget": 1 if recheck else 0,
        "context_sha256": fingerprint,
        "decision": decision,
        "recovery": {
            "success": False,
            "reason": "NO_REPAIR" if recheck else "NOT_INVOKED",
            "plan": [],
        },
        "selected_plan": None if recheck else [action],
        "granted_actions": int(not recheck),
        "actually_executed_actions": 0,
        "false_permissions": int(not recheck),
        "actual_goal_at_end": 0,
        "actual_task_completion": 0,
        "safe_task_completion": 0,
        "decision_granted": int(not recheck),
        "refused_actions": int(recheck),
        "execution_coverage": int(not recheck),
        "authorized_empty_completion": 0,
        "rechecked_actions": int(recheck),
        "unsafe_episode": int(not recheck),
        "abstention": int(recheck),
        "unnecessary_abstention": 0,
        "oracle_nominal_valid": 0,
        "query_count": int(recheck),
        "recovery_invoked": int(recheck),
        "recovery_certified": 0,
        "recovery_accepted": 0,
        "recovery_actual_success": 0,
        "utility": -0.01 if recheck else -5,
        "invalidated_relevant_claims": wrong,
        "direct_detected": int(recheck and wrong),
        "direct_detection_queries": 1 if recheck and wrong else None,
        "direct_undetected": int(wrong and not recheck),
        "same_value_replies": 0,
        "unrevalidated_false_claims": wrong if not recheck else 0,
        "calibration_n": 1,
        "calibration_squared_error_sum": (0.1 - wrong) ** 2,
        "calibration_pairs": [[0.1, wrong]],
        "external_event_count": 1,
        "hidden_rate": 0.1,
        "sensor_error_actual": 0,
    }
    return episode, row, task


def test_false_grant_is_unsafe_even_when_domain_guard_prevents_transition():
    episode, row, task = fixture()
    values, errors = audit.audit_row(
        episode, row, {a["name"]: a for a in task["actions"]}
    )
    assert not errors
    assert values["granted_actions"] == values["false_permissions"] == 1
    assert values["actually_executed_actions"] == values["safe_task_completion"] == 0
    assert values["unsafe_episode"] == 1
    tampered = copy.deepcopy(row)
    tampered["safe_task_completion"] = 1
    assert any(
        "safe_task_completion" in error
        for error in audit.audit_row(
            episode, tampered, {a["name"]: a for a in task["actions"]}
        )[1]
    )


def test_failed_recovery_counts_as_refusal_not_safe_success_or_unsafe_execution():
    episode, row, task = fixture(recheck=True)
    values, errors = audit.audit_row(
        episode, row, {a["name"]: a for a in task["actions"]}
    )
    assert not errors
    assert values["abstention"] == values["refused_actions"] == 1
    assert (
        values["execution_coverage"]
        == values["safe_task_completion"]
        == values["unsafe_episode"]
        == 0
    )
    assert values["direct_detected"] == 1
    assert values["direct_detection_queries"] == 1


def test_persistent_corruption_is_the_sensor_tape_not_an_oracle_reveal():
    episode, row, task = fixture(recheck=True, bias=True)
    assert not audit.audit_episode(episode, task)
    assert not audit.audit_row(episode, row, {a["name"]: a for a in task["actions"]})[1]
    row["decision"]["readings"][0]["value"] = False
    assert any(
        "Sensor response" in error
        for error in audit.audit_row(
            episode, row, {a["name"]: a for a in task["actions"]}
        )[1]
    )


def test_zero_grants_are_undefined_conditional_risk_and_parent_weights_ignore_frames():
    assert (
        audit.conditional_error_rate([{"granted_actions": 0, "false_permissions": 0}])
        is None
    )
    episode, row, task = fixture()
    values, _ = audit.audit_row(episode, row, {a["name"]: a for a in task["actions"]})
    a = values | {"parent_id": "a"}
    b = values | {"parent_id": "b", "safe_task_completion": 1}
    grouped = audit.parent_means([a] * 100 + [b])
    assert (
        grouped["a"]["safe_task_completion"] + grouped["b"]["safe_task_completion"]
    ) / 2 == 0.5


def test_action_choice_and_runtime_fingerprint_tampering_are_detected():
    episode, row, task = fixture()
    row["selected_plan"] = [task["actions"][1]]
    row["context_sha256"] = "wrong"
    errors = audit.audit_row(episode, row, {a["name"]: a for a in task["actions"]})[1]
    assert any("CONTINUE" in error for error in errors)
    assert any("fingerprint" in error for error in errors)
    episode["context"]["trusted_anchor"] = []
    assert any("anchor" in error for error in audit.audit_episode(episode, task))


def test_source_transition_and_full_input_hash_are_independent_checks():
    episode, row, task = fixture()
    digest = audit.action_library_digest(task["actions"])
    episode["actions_sha256"] = row["actions_sha256"] = digest
    row["full_input_sha256"] = audit.hashlib.sha256(
        (row["context_sha256"] + digest).encode()
    ).hexdigest()
    assert not audit.audit_episode(episode, task)
    assert not audit.audit_row(episode, row, {a["name"]: a for a in task["actions"]})[1]
    row["full_input_sha256"] = "changed"
    assert any(
        "Combined" in error
        for error in audit.audit_row(
            episode, row, {a["name"]: a for a in task["actions"]}
        )[1]
    )
    episode["external_actions"][1] = "not-a-source-action"
    assert audit.audit_episode(episode, task)


def test_sparse_risk_keeps_zero_grant_groups_out_of_conditional_denominator():
    rows = [
        {"granted_actions": 1000, "false_permissions": 1},
        {"granted_actions": 0, "false_permissions": 0},
    ]
    assert audit.conditional_error_rate(rows) == 0.001
    assert audit.conditional_error_rate(rows[1:]) is None


def test_paired_bootstrap_uses_parents_instead_of_repeated_schedule_count():
    rows = []
    for parent, count, difference in (("a", 100, 1), ("b", 1, 0)):
        for schedule in range(count):
            for method in ("SVR", "B2"):
                metrics = dict.fromkeys(audit.METRICS, 0)
                metrics["safe_task_completion"] = difference if method == "SVR" else 0
                metrics["query_count"] = 1 if method == "SVR" else 2
                rows.append(
                    metrics
                    | {
                        "episode_id": f"{parent}/{schedule}",
                        "parent_id": parent,
                        "family": "domain",
                        "regime": "hidden_nominal",
                        "budget": 2,
                        "method": method,
                    }
                )
    result = audit.paired_primary(rows, "B2")
    assert result["n_pairs"] == 101
    assert result["n_parents"] == 2
    assert result["metrics"]["safe_task_completion"]["mean"] == 0.5
    assert result["metrics"]["query_count"]["ci"] == [-1, -1]
