"""Source-correct exact experiment selection, independently checked."""

import copy
from fractions import Fraction

import pytest
from err_cases import causal_worlds, from_signatures, registered_cases
from err_independent_oracle import exhaustive, integer_program, verify_witnesses
from pydantic import ValidationError

from dual_rec.evidence_aware.evidence_resolution import (
    RepertoireInadequacy,
    resolve_evidence,
)
from dual_rec.evidence_aware.experiment_resolvability import (
    minimum_resolving_experiments,
)
from dual_rec.evidence_aware.experiment_schema import ExperimentProblem, World
from dual_rec.evidence_aware.schema import Certificate, Pair, Scope, Source


def certificate_fixture(**extra):
    values = {
        "obligation": "useful",
        "evidence": (("fact", False),),
        "selected_leaf_scope": (0,),
        "harm_upper": 0.02,
        "gain_lower": 0.5,
        "failure_upper": 0.4,
        "source_type": Source.LOGGED,
        "outcome_scope": Scope(
            task="ANALYTICAL_UNIT_FIXTURE",
            controller_sha256="fixed",
            horizon=70,
            outcome="terminal binary",
            population="declared fixture",
            observation_protocol="known facts",
        ),
        "confidence_family": "unit fixture, no robot result",
        "assumptions": ("valid fixture assumption",),
        "removal_witnesses": {"fact": "unqualified whole cell admitted"},
    }
    values.update(extra)
    return Certificate.model_validate(values)


@pytest.mark.parametrize("name", list(registered_cases()))
def test_registered_cases_match_two_independent_oracles(name):
    problem = registered_cases()[name]
    raw = problem.model_dump(mode="json")
    result = minimum_resolving_experiments(problem)
    expected = exhaustive(raw)
    actual = (
        None
        if result.total_cost is None
        else (result.total_cost, result.selected_experiments)
    )
    assert actual == expected
    if name == "fractional_cost_tolerance_trap":
        with pytest.raises(ValueError, match="MILP_DOUBLE_INTEGER_RANGE_UNSUPPORTED"):
            integer_program(raw)
        assert result.selected_experiments == ("B",)
    else:
        assert expected == integer_program(raw)
    verify_witnesses(raw, result.model_dump(mode="json"))


def test_exact_marginals_and_harm_need_a_paired_law():
    p = registered_cases()["same_marginals_with_pair"]
    a, b = p.worlds
    assert a.joint[2] + a.joint[3] == b.joint[2] + b.joint[3] == Fraction(2, 5)
    assert a.joint[1] + a.joint[3] == b.joint[1] + b.joint[3] == Fraction(3, 5)
    assert a.joint[2] == 0 and b.joint[2] == Fraction(2, 5)
    assert minimum_resolving_experiments(p).selected_experiments == ("paired_trial",)
    assert (
        minimum_resolving_experiments(
            registered_cases()["same_marginals_unpaired_only"]
        ).impossibility
        is not None
    )


def test_named_obligation_changes_a_nonempty_identifying_source_type():
    cases = registered_cases()
    assert minimum_resolving_experiments(
        cases["obligation_shift_three_worlds_completion"]
    ).selected_experiments == ("c_log",)
    assert minimum_resolving_experiments(
        cases["obligation_shift_three_worlds_useful"]
    ).selected_experiments == ("paired_trial",)


def test_type_identifiability_does_not_resolve_a_finite_noisy_observation():
    p = registered_cases()["finite_sample_overlap"]
    result = minimum_resolving_experiments(p)
    assert result.selected_experiments == ("e0",)
    assert all(law.probabilities[0] > 0 for law in p.experiments[0].laws)
    assert (
        not result.finite_sample_resolution_guaranteed
        and not result.physical_authorization
    )


def test_unanimous_catalogue_does_not_authorize_population_recovery():
    p = registered_cases()["unanimous_true_is_not_population_certificate"]
    result = resolve_evidence(problem=p)
    assert result.status == "UNRESOLVED" and not result.recovery_authorized
    assert result.experiment_plan.total_cost == 0
    assert (
        resolve_evidence(
            problem=registered_cases()["same_marginals_absolute_refuted"]
        ).status
        == "REFUTED_WITHIN_CATALOGUE"
    )
    assert resolve_evidence().status == "SOURCE_UNSUPPORTED"


def test_an_omitted_opposing_world_changes_the_conclusion():
    rows = [("2/5", "1/5", "0", "2/5"), ("0", "3/5", "2/5", "0")]
    incomplete = causal_worlds(rows[:1], paired=False)
    complete = causal_worlds(rows, paired=False)
    assert minimum_resolving_experiments(incomplete).unanimous_catalogue_verdict is True
    assert (
        minimum_resolving_experiments(complete).status
        == "NOT_RESOLVABLE_WITH_AVAILABLE_EVIDENCE"
    )
    raw = complete.model_dump(mode="json")
    raw["catalogue_scope"] = "CONTINUOUS_POPULATION"
    with pytest.raises(ValidationError):
        ExperimentProblem.model_validate(raw)


@pytest.mark.parametrize("bad", [-1, 0.1, True, "nan", "1/0", "not a rational"])
def test_approximate_or_invalid_costs_fail_closed(bad):
    raw = registered_cases()["same_marginals_with_pair"].model_dump(mode="json")
    raw["experiments"][0]["cost"] = bad
    with pytest.raises(ValidationError):
        ExperimentProblem.model_validate(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("qualified", False),
        ("provenance", []),
        ("assumptions", []),
        ("participant_selection", "WORLD_CLASS_DEPENDENT"),
        ("participant_sampling", "SELECT_TRUE_CLASSES_ONLY"),
        ("population_id", "DIFFERENT_CHECKPOINT_POPULATION"),
        ("kind", "NEW_RECOVERY_SKILL"),
        ("propensity", None),
    ],
)
def test_missing_biased_or_mismatched_source_metadata_is_not_equivalence(field, value):
    raw = registered_cases()["same_marginals_with_pair"].model_dump(mode="json")
    raw["experiments"][0]["source"][field] = value
    with pytest.raises(ValidationError):
        ExperimentProblem.model_validate(raw)


def test_paired_source_requires_coupling_and_true_joint_law():
    raw = registered_cases()["same_marginals_with_pair"].model_dump(mode="json")
    paired = next(e for e in raw["experiments"] if e["experiment_id"] == "paired_trial")
    paired["source"]["coupling"] = None
    with pytest.raises(ValidationError, match="coupling"):
        ExperimentProblem.model_validate(raw)
    paired["source"]["coupling"] = "declared coupling"
    paired["laws"][0]["probabilities"] = ["1", "0", "0", "0"]
    with pytest.raises(ValidationError, match="law disagrees"):
        ExperimentProblem.model_validate(raw)


def test_unmodelled_cross_experiment_correlations_are_rejected():
    p = from_signatures([True, False], [[("1/2", "1/2")] * 2] * 2, [1, 1])
    assert minimum_resolving_experiments(p).impossibility is not None
    # If shared draws were (00/11) vs (01/10), joint data would distinguish
    # these worlds despite both fair marginal laws. A joint menu item is needed.
    raw = p.model_dump(mode="json")
    raw["cross_experiment_law"] = "UNSPECIFIED_SHARED_PARENT_CORRELATION"
    with pytest.raises(ValidationError):
        ExperimentProblem.model_validate(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_world",
        "bad_normalization",
        "negative_probability",
        "wrong_verdict",
        "duplicate_world",
        "float_probability",
    ],
)
def test_malformed_worlds_and_laws_are_source_errors(mutation):
    raw = registered_cases()["same_marginals_with_pair"].model_dump(mode="json")
    row = raw["experiments"][0]["laws"][0]
    if mutation == "missing_world":
        raw["experiments"][0]["laws"].pop()
    elif mutation == "bad_normalization":
        row["probabilities"] = ["1/2", "1/4"]
    elif mutation == "negative_probability":
        row["probabilities"] = ["-1", "2"]
    elif mutation == "wrong_verdict":
        raw["worlds"][0]["obligation_verdict"] = False
    elif mutation == "duplicate_world":
        raw["worlds"].append(copy.deepcopy(raw["worlds"][0]))
    else:
        row["probabilities"] = [0.6, 0.4]
    with pytest.raises(ValidationError):
        ExperimentProblem.model_validate(raw)


def test_exact_small_difference_is_not_rounded_to_impossibility():
    p = registered_cases()["reference_rounding_trap"]
    a, b = p.worlds
    assert a.joint[2] < Fraction(1, 10) < b.joint[2]
    assert minimum_resolving_experiments(p).selected_experiments == ("paired_trial",)


def test_data_and_verdict_fields_are_immutable():
    w = World(world_id="fixed", obligation_verdict=True)
    with pytest.raises(ValidationError, match="frozen"):
        w.obligation_verdict = False
    p = registered_cases()["same_marginals_with_pair"]
    with pytest.raises(TypeError):
        p.experiments[0].laws[0].probabilities[0] = Fraction(0)


def test_canonical_solution_is_invariant_to_input_order():
    p = registered_cases()["zero_cost_required_and_redundant"]
    raw = p.model_dump(mode="json")
    raw["worlds"].reverse()
    raw["experiments"].reverse()
    for e in raw["experiments"]:
        e["laws"].reverse()
    assert minimum_resolving_experiments(p) == minimum_resolving_experiments(
        ExperimentProblem.model_validate(raw)
    )


def test_only_original_qualified_certificate_can_authorize_recovery():
    c = certificate_fixture()
    answer = resolve_evidence(certificate=c)
    assert answer.status == "CERTIFIED_RECOVER" and answer.recovery_authorized
    assert answer.certificate == c and answer.experiment_plan is None
    with pytest.raises(ValidationError):
        resolve_evidence(certificate=certificate_fixture(harm_upper=0.2))


@pytest.mark.parametrize(
    "extra",
    [
        {"harm_upper": 0.1 + 1e-13},
        {"gain_lower": 0.05 - 1e-13},
        {"obligation": "completion", "failure_upper": 0.1 + 1e-13},
    ],
)
def test_new_boundary_refuses_legacy_tolerance_only_authorization(extra):
    from dual_rec.evidence_aware.bounds import qualifies
    from dual_rec.evidence_aware.schema import Bounds

    c = certificate_fixture(**extra)
    b = Bounds(
        harm_lower=0,
        harm_upper=c.harm_upper,
        gain_lower=c.gain_lower,
        gain_upper=1,
        failure_upper=c.failure_upper,
        optimizers={},
    )
    assert qualifies(
        b, c.obligation
    )  # Original numerical tolerance is retained in the old source.
    with pytest.raises(ValidationError, match="original obligation/source gate"):
        resolve_evidence(certificate=c)


def test_repertoire_failure_requires_two_observed_false_endpoints():
    c = certificate_fixture()
    p = Pair(
        parent_id="ANALYTICAL_FIXTURE_NOT_ROBOT",
        x=(False,),
        yc=False,
        yr=False,
        source_scope=c.outcome_scope,
    )
    witness = RepertoireInadequacy(
        witnessed_pair=p,
        native_source_paths=("FIXTURE_C", "FIXTURE_R"),
        native_source_sha256=("0" * 64, "1" * 64),
        source_qualified=True,
    )
    assert witness.status == "REPERTOIRE_INADEQUATE" and witness.offline_evidence_only
    with pytest.raises(ValidationError):
        RepertoireInadequacy(
            witnessed_pair=p.model_copy(update={"yr": True}),
            native_source_paths=("FIXTURE_C", "FIXTURE_R"),
            native_source_sha256=("0" * 64, "1" * 64),
            source_qualified=True,
        )
    with pytest.raises(ValidationError):
        Pair(
            parent_id="missing",
            x=(False,),
            yc=False,
            yr=None,
            source_scope=c.outcome_scope,
        )
