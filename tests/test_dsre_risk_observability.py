import random

import pytest
from pydantic import ValidationError
from test_dsre_calibration import observations, router
from test_dsre_solver import example

from dual_rec.dsre.calibration import calibrate, gate, upper_bound
from dual_rec.dsre.observability import profile
from dual_rec.dsre.risk import RiskRules, RoutedDecision, TwoTierRouter
from dual_rec.dsre.risk_oracle import ceiling, exact_binomial_upper, rule


@pytest.mark.parametrize(
    "data,mass",
    [
        ([([True], True, True), ([True], True, True)], 2),
        ([([True], False, False), ([True], False, False)], 0),
        ([([True], True, False), ([True], False, True)], 0),
        ([([True], True, False), ([None], False, True)], 2),
    ],
)
def test_equal_signature_ceiling_and_independent_checker(data, mass):
    table, _, _ = example(data, [True])
    result = profile(table)
    assert result["summary"]["equal_adequate"]["mass"] == mass
    independent = ceiling(table.model_dump(mode="json"))
    assert sum(r["mass"] for r in independent if r["equal"]["good"]) == mass
    if data[-1][0] == [None]:
        assert result["summary"]["compatible_adequate"]["mass"] == 0
        assert result["summary"]["supported_grammar_mass"] == 0


def test_missing_reference_and_sparse_support_are_not_physical_failure():
    table, query, _ = example([], [True])
    assert profile(table)["summary"]["equal_ceiling"] is None
    result = TwoTierRouter(table).predict(query)
    assert result.tier == "INSUFFICIENT"
    assert result.strict.reasons == ("INSUFFICIENT_REFERENCE_SUPPORT",)
    table, query, _ = example([([True], True, False)], [True])
    assert profile(table)["summary"]["equal_ceiling"] == 1
    assert profile(table)["summary"]["supported_grammar_mass"] == 0
    assert TwoTierRouter(table).predict(query).action is None


def test_sparse_full_signature_can_have_supported_broader_rule():
    table, query, _ = example([([True], True, False), ([False], True, False)], [True])
    assert profile(table)["summary"]["supported_grammar_mass"] == 2
    result = TwoTierRouter(table).predict(query)
    assert result.tier == "STRICT_FINITE_REFERENCE" and not result.evidence


def test_neither_row_blocks_strict_but_risk_rule_is_provisional_only():
    table, query, _ = example(
        [([True], False, True)] * 19 + [([True], False, False)], [True]
    )
    result = TwoTierRouter(table).predict(query)
    assert result.tier == "PROVISIONAL_RISK_RULE"
    assert result.status == "PROVISIONAL_UNCALIBRATED"
    assert result.provisional.unacceptable == 1 and result.provisional.support == 20
    assert result.strict.action is None and result.deployable_action is None
    assert "INADEQUATE_REPERTOIRE" in result.strict.reasons
    modified = result.model_dump(mode="json") | {"status": "STRICT_FINITE_REFERENCE"}
    with pytest.raises(ValidationError):
        RoutedDecision.model_validate(modified)
    assert TwoTierRouter(table, beta=0.049).predict(query).action is None


def test_strict_priority_differs_from_unrestricted_b5():
    data = [([True], True, False)] * 19 + [([False], False, True)]
    table, query, _ = example(data, [True])
    result, b5 = TwoTierRouter(table).predict(query), RiskRules(table).select(query)
    assert result.action == b5.action == "continue"
    assert len(result.evidence) == 1 and len(b5.evidence) == 0
    assert result.tier == "STRICT_FINITE_REFERENCE"
    assert b5.unacceptable == 1


def test_error_precedes_action_and_support_ties_in_risk_tier():
    table, query, _ = example(
        [([True], False, True)] * 19 + [([True], True, True)], [True]
    )
    assert RiskRules(table).select(query).action == "recover"
    assert RiskRules(table).select(query).unacceptable == 0
    # Identical means, continue-first, independent of audit IDs/row order.
    table, query, _ = example([([True], True, True)] * 2, [True])
    assert RiskRules(table).select(query).action == "continue"


def test_unknown_outcomes_and_unknown_reference_features_remain_conservative():
    table, query, _ = example(
        [([True], True, False)] * 20 + [([None], None, False)], [True]
    )
    assert RiskRules(table).select(query).action is None
    assert TwoTierRouter(table).predict(query).action is None
    result = profile(table)
    assert result["summary"]["equal_unknown_outcomes"]["mass"] == 1
    assert result["summary"]["compatible_unknown_outcomes"]["mass"] == 21


def test_scopes_and_invalid_targets():
    table, query, _ = example([([True], True, True)] * 2, [True])
    wrong = query.model_copy(
        update={"scope": query.scope.model_copy(update={"task": "other"})}
    )
    assert RiskRules(table).select(wrong).reason == "SCOPE_MISMATCH"
    assert TwoTierRouter(table).predict(wrong).action is None
    for beta in (-0.1, 1.1):
        with pytest.raises(ValueError):
            RiskRules(table).select(query, beta)


def test_independent_exhaustive_risk_router_agreement():
    rng = random.Random(2026111301)
    for _ in range(160):
        d = rng.randint(0, 6)
        x = [rng.choice([True, False, None]) for _ in range(d)]
        data = [
            (
                [rng.choice([True, False, None]) for _ in range(d)],
                rng.choice([True, False, None]),
                rng.choice([True, False, None]),
            )
            for _ in range(rng.randint(0, 15))
        ]
        table, query, _ = example(data, x)
        for beta in (0.05, 0.1, 0.5):
            expected = rule(
                table.model_dump(mode="json"), query.model_dump(mode="json"), beta
            )
            found = RiskRules(table).select(query, beta)
            assert found.action == (expected["action"] if expected else None)
            if expected:
                for key in (
                    "action",
                    "evidence",
                    "support",
                    "matched_ids",
                    "unacceptable",
                ):
                    assert found.model_dump(mode="json")[key] == expected[key]
        actual = TwoTierRouter(table).predict(query)
        strict = rule(
            table.model_dump(mode="json"), query.model_dump(mode="json"), 0, True
        )
        assert (actual.tier == "STRICT_FINITE_REFERENCE") == bool(strict)


@pytest.mark.parametrize(
    "k,n", [(0, 0), (0, 1), (0, 41), (0, 42), (1, 42), (7, 200), (10, 10)]
)
def test_independent_decimal_binomial(k, n):
    assert upper_bound(k, n, 0.0125) == pytest.approx(
        exact_binomial_upper(k, n, 0.0125), abs=1e-12
    )


def test_calibration_zero_missing_dependent_and_rare_never_reroutes():
    frozen = router()
    independent = observations(42)
    enabled = calibrate(frozen, independent)
    assert enabled.strata[0].enabled
    assert not enabled.strata[1].enabled
    assert (
        gate("PickCube-v1", "recover", frozen.sha256, enabled).reason
        == "CALIBRATION_INSUFFICIENT"
    )
    with pytest.raises(ValueError):
        calibrate(frozen, independent + (independent[0],))
    unknown = independent[:-1] + (
        independent[-1].model_copy(update={"violated": None}),
    )
    assert calibrate(frozen, unknown).strata[0].upper == 1
    assert not any(s.enabled for s in calibrate(frozen, ()).strata)


def test_independent_audit_accepts_valid_output_and_rejects_corrupt_claims(monkeypatch):
    import copy
    import importlib

    monkeypatch.syspath_prepend("scripts")
    checker = importlib.import_module("dsre_v11_audit").verify_decision
    table, query, _ = example(
        [([True], False, True)] * 19 + [([True], False, False)], [True]
    )
    decision = {
        "method": "DSRE_v11",
        "beta": 0.1,
        "query": query.model_dump(mode="json"),
        "result": TwoTierRouter(table).predict(query).model_dump(mode="json"),
    }
    assert checker(table.model_dump(mode="json"), decision)
    for field, value in (
        ("status", "CERTIFIED"),
        ("action", "continue"),
        ("support", 0),
        ("deployable_action", "recover"),
    ):
        corrupted = copy.deepcopy(decision)
        corrupted["result"][field] = value
        with pytest.raises(AssertionError):
            checker(table.model_dump(mode="json"), corrupted)


def test_two_conditions_of_one_seed_are_not_two_calibration_parents():
    frozen = router()
    nominal = observations(1)[0].model_copy(update={"parent_id": "PickCube-v1/123"})
    offset = nominal.model_copy(update={"assigned_action": "recover"})
    with pytest.raises(ValueError, match="Repeated physical parents"):
        calibrate(frozen, (nominal, offset))


@pytest.mark.parametrize(
    "script", ["experiment", "analyze", "audit", "review", "finish"]
)
def test_v11_entrypoints_refuse_sealed_evidence(tmp_path, script):
    import subprocess
    import sys

    (tmp_path / "completion_manifest.json").write_text("{}")
    argv = [
        sys.executable,
        "scripts/dsre_v11_" + script + ".py",
        "--root",
        str(tmp_path),
    ]
    if script == "finish":
        argv += ["--stage", "initialize"]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "Evidence sealed" in result.stderr + result.stdout
