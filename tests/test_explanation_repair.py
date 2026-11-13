import pytest
from pydantic import ValidationError

from dual_rec.explanation_repair.adapters import (
    PublicRecord,
    extract,
    parse_facts,
    public_bundle,
    public_groups,
    select_action,
)
from dual_rec.explanation_repair.core import assess, baselines, edit, observe
from dual_rec.explanation_repair.examples import worked_cases
from dual_rec.explanation_repair.schemas import (
    ActionModel,
    Predicate,
    RepairInput,
    Window,
)


def test_correct_explanation_is_preserved_with_support_ids():
    bundle = worked_cases()[0]
    result = edit(bundle)
    assert result.text == bundle.original_text
    assert result.decisions[0].operation == "keep"
    assert result.claims[0].support.evidence == ["g"]


def test_selective_repair_keeps_supported_diagnostic_content():
    result = edit(worked_cases()[1])
    assert [d.operation for d in result.decisions] == ["replace", "keep"]
    assert result.claims[0].claim.fact.value is True
    assert result.claims[1].claim.fact.value is False
    assert result.max_menu_size <= 4


def test_unknown_battery_is_not_rendered_as_failure_or_empty_success():
    result = edit(worked_cases()[2])
    assert not result.claims
    assert len(result.unresolved) == 2
    assert "does not establish" in result.text
    assert "battery is failed" not in result.text


def test_commands_never_prove_their_intended_effects():
    b = worked_cases()[3]
    without_observation = b.model_copy(update={"records": b.records[1:]})
    assert assess(without_observation, b.claims[0]).status == "unknown"
    result = edit(b)
    assert result.claims[0].claim.fact.value is False
    blocked = result.claims[1]
    assert blocked.claim.kind == "implication"
    assert blocked.support.rules == ["transport-grasp"]
    assert "unique physical cause" in result.text


def test_temporal_distinctions_and_conflicts_are_not_flattened():
    bundle = worked_cases()[4]
    normal = edit(bundle)
    assert [c.operation for c in normal.decisions] == ["keep", "keep", "unknown"]
    assert "At t=0 s, cube is grasped." in normal.text
    assert "cube is not grasped." in normal.text
    assert normal.decisions[2].evaluation.evidence == ["contact-no", "contact-yes"]
    ablated = edit(bundle, temporal=False)
    assert ablated.claims[0].claim.fact.value is False
    assert not ablated.claims[0].support.reason.startswith("Visible observation")


@pytest.mark.parametrize("action", ["transport", "unmodeled-action"])
def test_possible_state_change_blocks_declared_persistence(action):
    b = worked_cases()[3]
    old = b.records[0].model_copy(update={"window": Window(start=0, end=0)})
    command = b.records[1].model_copy(update={"action": action})
    model = b.model.model_copy(
        update={"persistent": [Predicate(entity="cube", predicate="grasped")]}
    )
    b = b.model_copy(update={"records": [old, command], "model": model})
    assert observe(b, old.fact, b.query).status == "unknown"


def test_explicit_persistence_without_state_change_is_conditional_support():
    b = worked_cases()[0]
    old = b.records[0].model_copy(update={"window": Window(start=0, end=0)})
    b = b.model_copy(
        update={
            "records": [old],
            "model": ActionModel(
                persistent=[Predicate(entity="cube", predicate="grasped")]
            ),
        }
    )
    proof = observe(b, old.fact, b.query)
    assert proof.status == "supported"
    assert proof.basis == "model_deduction"
    assert proof.rules == ["persistence/cube/grasped"]
    assert "Under the declared persistence model" in edit(b).text
    assert edit(b, action_model=False).decisions[0].operation == "unknown"


def test_invisible_record_does_not_prove_absence():
    b = worked_cases()[0]
    b = b.model_copy(
        update={
            "records": [b.records[0].model_copy(update={"visibility": "not_visible"})]
        }
    )
    assert assess(b, b.claims[0]).status == "unknown"


def test_overlapping_conflicting_observation_cannot_be_ignored():
    b = worked_cases()[0]
    long = b.records[0].model_copy(update={"window": Window(start=0, end=2)})
    other = b.records[0].model_copy(
        update={"id": "other", "fact": long.fact.model_copy(update={"value": False})}
    )
    b = b.model_copy(update={"records": [long, other]})
    assert assess(b, b.claims[0]).status == "unknown"


def test_no_action_model_ablation_cannot_claim_model_support():
    result = edit(worked_cases()[3], action_model=False)
    assert result.decisions[1].operation == "unknown"


def test_long_explanation_and_forward_references_are_not_truncated():
    b = worked_cases()[0]
    claims = [
        b.claims[0].model_copy(
            update={"id": str(i), "depends_on": [str(i - 1)] if i else []}
        )
        for i in range(13)
    ]
    b = b.model_copy(update={"claims": list(reversed(claims))})
    result = edit(b)
    assert len(result.claims) == 13
    assert {c.origin for c in result.claims} == {str(i) for i in range(13)}
    assert all(c.operation == "keep" for c in result.decisions)


def test_changed_and_cyclic_references_are_explicitly_unresolved():
    b = worked_cases()[1]
    dependent = b.claims[1].model_copy(update={"depends_on": ["g"]})
    result = edit(b.model_copy(update={"claims": [b.claims[0], dependent]}))
    assert result.decisions[1].operation == "unknown"
    cyclic = [
        b.claims[0].model_copy(update={"depends_on": ["goal"]}),
        b.claims[1].model_copy(update={"depends_on": ["g"]}),
    ]
    result = edit(b.model_copy(update={"claims": cyclic}))
    assert len(result.decisions) == 2
    assert all("cyclic" in u for u in result.unresolved)


def test_regeneration_and_deletion_are_strong_equal_information_controls():
    b = worked_cases()[1]
    outputs = baselines(b)
    assert len(outputs["delete"].claims) == 1
    assert len(outputs["regenerate"].claims) == 2
    assert len(outputs["proposed"].claims) == 2
    assert not outputs["generic"].claims


def test_public_adapter_does_not_invent_timestamps_models_or_gold_repairs():
    row = PublicRecord(
        task_id="task-2_gt_step_3_gt_exp",
        plan_until_failure=["pick up cup"],
        action="pick up cup",
        observation=["cup is inside robot gripper"],
        explanation="cup is inside robot gripper.",
        label="E",
        L_plan_exp="N",
        L_obs_exp="E",
    )
    b, parsed = public_bundle(row, "RoboFail")
    assert parsed.covered_spans == 1
    assert b.query.clock == "snapshot"
    assert not b.model.rules
    assert b.records[-1].kind == "command"
    assert row.label == "E"
    assert b.records[0].fact.value == "cup"


def test_causal_or_conditional_prose_is_not_promoted_to_observation():
    w = Window(clock="snapshot", start=0, end=0)
    for text in ["The robot failed because battery is failed.", "If cup is grasped."]:
        parsed = extract(text, w)
        assert not parsed.claims
        assert parsed.unparsed
    parsed = extract("cube is grasped. Unknown grammar. cube is not near goal.", w)
    assert parsed.spans == 3 and parsed.covered_spans == 2
    assert len(parsed.unparsed) == 1


def test_public_parser_does_not_swallow_complex_prose_as_an_object_name():
    for sentence in [
        "A cube is inside the tray already and the robot never removed it.",
        "A cube is below the box at the beginning of execution.",
        "As a result, the robot cannot open a box that is closed.",
        "cube is inside tray while the robot moves away.",
    ]:
        assert parse_facts(sentence) == []
    assert len(parse_facts("mug (filled with water and clean)")) == 2
    assert parse_facts("The cube is inside the tray")[0].value == "tray"


def test_counterfactual_template_and_episode_aliases_share_groups():
    row = PublicRecord(
        task_id="task-2_gt_step_3_gt_exp",
        plan_until_failure=["one"],
        action="one",
        observation=[],
        explanation="unparsed",
        label="E",
        L_plan_exp="N",
        L_obs_exp="E",
    )
    rf = row.model_copy(
        update={
            "task_id": "task-2_pred_step_8_reflect_exp",
            "plan_until_failure": ["other"],
        }
    )
    cf = row.model_copy(
        update={"task_id": "other-xyz-autogen_dropped_e", "plan_until_failure": ["cf"]}
    )
    cf2 = row.model_copy(
        update={
            "task_id": "different-abc-autogen_dropped_c",
            "plan_until_failure": ["cf2"],
        }
    )
    groups = public_groups(
        [
            ("RoboFail", row),
            ("RoboFail", rf),
            ("CounterFactual", cf),
            ("CounterFactual", cf2),
        ]
    )
    assert groups[0] == groups[1]
    assert groups[2] == groups[3]


def test_selector_gets_same_information_and_unknown_sensor_abstains():
    b = worked_cases()[0]
    assert (
        select_action("PickCube-v1", b, "unreliable explanation")
        == select_action("PickCube-v1", b, "correct explanation")
        == "continue"
    )
    assert (
        select_action("PickCube-v1", b.model_copy(update={"records": []})) == "abstain"
    )
    invalid = b.records[0].model_copy(
        update={"fact": b.records[0].fact.model_copy(update={"value": "unknown"})}
    )
    assert (
        select_action("PickCube-v1", b.model_copy(update={"records": [invalid]}))
        == "abstain"
    )


def test_input_validation_rejects_bad_time_and_duplicate_identifiers():
    with pytest.raises(ValidationError):
        Window(start=2, end=1)
    with pytest.raises(ValidationError):
        Window(start=float("nan"), end=1)
    b = worked_cases()[0]
    with pytest.raises(ValidationError):
        RepairInput.model_validate(
            b.model_dump() | {"records": [b.records[0].model_dump()] * 2}
        )


def test_snapshot_is_not_a_past_seconds_observation():
    b = worked_cases()[0]
    b = b.model_copy(
        update={
            "records": [
                b.records[0].model_copy(
                    update={"window": Window(clock="snapshot", start=1, end=1)}
                )
            ]
        }
    )
    assert assess(b, b.claims[0]).status == "unknown"


def test_standalone_cli_repairs_an_input_and_refuses_output_overwrite(tmp_path):
    import json
    import os
    import subprocess
    import sys

    source = tmp_path / "input.json"
    target = tmp_path / "output.json"
    source.write_text(worked_cases()[2].model_dump_json())
    command = [
        sys.executable,
        "scripts/explanation_repair_run.py",
        "--input",
        str(source),
        "--output",
        str(target),
    ]
    run = subprocess.run(
        command,
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(target.read_text())
    assert not result["claims"] and len(result["unresolved"]) == 2
    assert "battery is failed" not in run.stdout
    original_bytes = target.read_bytes()
    repeat = subprocess.run(
        command,
        env=os.environ | {"PYTHONPATH": "src"},
        capture_output=True,
        check=False,
    )
    assert repeat.returncode != 0 and target.read_bytes() == original_bytes


def test_independent_metrics_count_unique_facts_and_reject_stale_values():
    from dual_rec.explanation_repair.audit import (
        factual_claims,
        true_claim,
        unique_claims,
    )

    old = worked_cases()[4].claims[0].model_dump()
    duplicate = old | {"id": "duplicate"}
    assert len(unique_claims([old, duplicate])) == 1
    truth = {("cube", "grasped", 0): True, ("cube", "grasped", 1): False}
    assert true_claim(old, truth, "PickCube-v1") is True
    stale = old | {"window": {"clock": "seconds", "start": 1, "end": 1}}
    assert true_claim(stale, truth, "PickCube-v1") is False
    fabricated = old | {
        "fact": {"entity": "battery", "predicate": "failed", "value": True}
    }
    assert true_claim(fabricated, truth, "PickCube-v1") is None
    hypothesis = worked_cases()[2].claims[1].model_dump()
    assert len(factual_claims([old, duplicate, hypothesis])) == 1


def test_language_schema_does_not_turn_numeric_output_into_observed_truth(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from explanation_repair_language import LanguageClaims
    from explanation_repair_language_audit import schema_valid

    good = '{"facts":[{"entity":"cube","predicate":"grasped","value":true}],"unresolved":[]}'
    assert LanguageClaims.model_validate_json(good).facts[0].value is True
    assert schema_valid(good)
    bad = good.replace("true", "1")
    with pytest.raises(ValidationError):
        LanguageClaims.model_validate_json(bad)
    assert not schema_valid(bad)
    assert not schema_valid(good + " unsupported trailing prose")


def test_language_packet_keeps_provenance_out_of_model_features(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from explanation_repair_language import cases, prompt

    b = worked_cases()[0].model_dump()
    b["id"] = "PickCube/42/offset002"
    b["records"][0]["source"] = "old/PickCube/42/offset002/traces.json.gz"
    target = tmp_path / "development"
    target.mkdir()
    (tmp_path / "latest_development.json").write_text(json.dumps({"path": str(target)}))
    (target / "worked_cases.json").write_text("[]")
    (target / "public_inputs.jsonl").write_text("")
    (target / "trace_inputs.jsonl").write_text(
        json.dumps(
            {
                "id": b["id"],
                "variant": "partial_flip",
                "input": b,
                "source": "old/PickCube/42/offset002/traces.json.gz",
            }
        )
        + "\n"
    )
    case = cases(tmp_path, {"sampling_salt": "fixed", "public_per_source": 3})[0]
    actual_prompt = prompt(case, "Check the same visible observations.")
    assert "offset002" not in actual_prompt and "traces.json.gz" not in actual_prompt
    assert "offset002" in case["bundle"]["records"][0]["source"]
    assert case["evidence"]["records"][0]["id"] == b["records"][0]["id"]


def test_structured_editor_and_selector_are_invariant_to_provenance_labels():
    b = worked_cases()[1]
    changed = b.model_copy(
        update={
            "records": [
                r.model_copy(
                    update={"source": "fault-offset002-or-nominal-cohort-metadata"}
                )
                for r in b.records
            ]
        }
    )
    assert edit(b).model_dump() == edit(changed).model_dump()
    assert select_action("PickCube-v1", b) == select_action("PickCube-v1", changed)
