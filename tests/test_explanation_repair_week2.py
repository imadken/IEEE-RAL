import json

from dual_rec.explanation_repair.adapters import PublicRecord
from dual_rec.explanation_repair.core import assess, run_method
from dual_rec.explanation_repair.natural import language_bundle


def row(explanation, plan=None):
    return PublicRecord(
        task_id="example",
        plan_until_failure=plan or ["pick up mug", "put mug on countertop"],
        action="put mug on countertop",
        observation=["Mug is inside robot gripper", "Fridge is closed"],
        explanation=explanation,
        label="E",
        L_plan_exp="E",
        L_obs_exp="E",
    )


def test_literal_command_order_repair_and_strong_regeneration():
    bundle, extraction = language_bundle(
        row("Wrong plan - put mug on countertop before pick up mug"), "test"
    )
    assert extraction.complete
    assert assess(bundle, bundle.claims[0]).status == "contradicted"
    result = run_method(bundle, "proposed")
    assert result.decisions[0].operation == "replace"
    assert json.loads(result.claims[0].claim.fact.value) == [
        "pick up mug",
        "put mug on countertop",
    ]
    regenerated = run_method(bundle, "regenerate")
    assert any(g.claim.fact.predicate == "sequence" for g in regenerated.claims)
    assert not run_method(bundle, "unconstrained").claims


def test_repeated_occurrences_abstain():
    bundle, _ = language_bundle(
        row(
            "pick up mug before put mug on countertop",
            ["pick up mug", "put mug on countertop", "pick up mug"],
        ),
        "test",
    )
    assert assess(bundle, bundle.claims[0]).status == "unknown"
    assert not run_method(bundle, "proposed").claims


def test_historical_state_does_not_borrow_current_evidence():
    bundle, extraction = language_bundle(row("Fridge was closed"), "test")
    assert extraction.complete
    assert bundle.claims[0].window.clock == "unknown"
    assert assess(bundle, bundle.claims[0]).status == "unknown"


def test_causal_parse_is_not_causal_truth_and_residue_survives():
    bundle, extraction = language_bundle(
        row("Book is blocking remote control. Alien telemetry caused failure"), "test"
    )
    assert extraction.partial
    assert bundle.claims[0].kind == "hypothesis"
    assert "Alien telemetry caused failure" in bundle.unparsed
    assert not run_method(bundle, "proposed").claims


def test_command_is_not_effect_and_labels_are_not_inputs():
    original = row("Mug is on top of countertop")
    bundle, _ = language_bundle(original, "test")
    # Countertop is not an observed argument; commanded placement cannot prove it.
    assert not bundle.claims
    changed, _ = language_bundle(
        original.model_copy(
            update={"label": "C", "comment": "invented gold", "L_obs_exp": "C"}
        ),
        "test",
    )
    assert changed == bundle


def test_negated_temporal_event_not_asserted_as_positive_order():
    bundle, extraction = language_bundle(
        row("did not pick up mug before put mug on countertop"), "test"
    )
    assert not extraction.complete
    assert not bundle.claims


def test_correct_literal_explanation_is_preserved():
    bundle, extraction = language_bundle(row("Fridge is closed"), "test")
    assert extraction.complete
    result = run_method(bundle, "proposed")
    assert result.decisions[0].operation == "keep"
    assert result.claims[0].claim.fact == bundle.claims[0].fact
