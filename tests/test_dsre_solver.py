import random

import pytest
from pydantic import ValidationError

from dual_rec.dsre.baselines import OutcomeRules, OutcomeTree
from dual_rec.dsre.oracle import enumerate_oracle, verify_certificate
from dual_rec.dsre.schemas import Outcomes, Query, ReferenceRow, ReferenceTable, Scope
from dual_rec.dsre.solver import FiniteIndex


def example(data, x, minimum=1):
    scope = Scope(
        task="test",
        controller_sha256="a" * 64,
        features=tuple("abcdefgh"[: len(x)]),
        channels="test-observations",
    )
    table = ReferenceTable(
        scope=scope,
        rows=tuple(
            ReferenceRow(
                id=f"row/{i}",
                features=tuple(values),
                outcomes=Outcomes(continue_value=c, recover_value=r),
            )
            for i, (values, c, r) in enumerate(data)
        ),
    )
    return table, Query(scope=scope, features=tuple(x)), FiniteIndex(table, minimum)


def test_one_bit_equals_outcome_stump():
    table, query, solver = example(
        [([False], False, True), ([True], True, False)], [True]
    )
    certificate = solver.solve(query)
    tree = OutcomeTree(OutcomeRules(table, 1), 1).predict(query, 1)
    assert certificate.action == tree.action == "continue"
    assert certificate.evidence == tree.evidence and len(tree.evidence) == 1


def test_two_literals_required_and_each_has_real_bad_witness():
    table, query, solver = example(
        [
            ([True, True], True, False),
            ([False, True], False, True),
            ([True, False], False, True),
        ],
        [True, True],
    )
    certificate = solver.solve(query)
    assert len(certificate.evidence) == len(certificate.witnesses) == 2
    assert verify_certificate(
        table.model_dump(mode="json"),
        query.model_dump(mode="json"),
        certificate.model_dump(mode="json"),
        1,
    )


def test_tied_adequacy_need_not_preserve_policy_label():
    table, query, solver = example(
        [([False], True, True), ([True], False, True)], [False]
    )
    rules = OutcomeRules(table, 1)
    certificate = solver.solve(query)
    assert certificate.action == "recover" and not certificate.evidence
    assert rules.full(query, 1).action == rules.policy(query, 1).action == "continue"
    assert len(rules.policy(query, 1).evidence) == 1


def test_observation_equivalent_incompatible_actions():
    table, query, solver = example(
        [([True], True, False), ([True], False, True)], [True]
    )
    certificate = solver.solve(query)
    assert certificate.action is None and "OBSERVATION_AMBIGUITY" in certificate.reasons
    assert verify_certificate(
        table.model_dump(mode="json"),
        query.model_dump(mode="json"),
        certificate.model_dump(mode="json"),
        1,
    )


def test_failure_tie_is_not_adequate():
    _, query, solver = example([([True], False, False)], [True])
    certificate = solver.solve(query)
    assert certificate.action is None and "INADEQUATE_REPERTOIRE" in certificate.reasons


@pytest.mark.parametrize("x,reference", [([None], [True]), ([True], [None])])
def test_unknowns_do_not_exclude_bad_reference_rows(x, reference):
    _, query, solver = example([([True], True, False), (reference, False, True)], x)
    assert solver.solve(query).action is None


def test_empty_reference_missing_outcomes_scope_and_support():
    table, query, solver = example([], [True])
    assert solver.solve(query).reasons == ("INSUFFICIENT_REFERENCE_SUPPORT",)
    _, query, solver = example([([True], True, None)], [True])
    assert "OUTCOME_UNCERTAINTY" in solver.solve(query).reasons
    altered = query.model_copy(
        update={"scope": query.scope.model_copy(update={"horizon_steps": 71})}
    )
    assert solver.solve(altered).reasons == ("SCOPE_MISMATCH",)
    assert (
        FiniteIndex(table, 2).solve(Query(scope=table.scope, features=(True,))).action
        is None
    )


def test_genuine_greedy_counterexample():
    _, query, solver = example(
        [
            ([True, True, True], True, False),
            ([False, False, True], False, True),
            ([False, True, False], False, True),
        ],
        [True, True, True],
    )
    exact, greedy = solver.solve(query), solver.greedy(query)
    assert [f.feature for f in exact.evidence] == ["a"]
    assert [f.feature for f in greedy.evidence] == ["b", "c"]
    assert len(greedy.witnesses) == 2


def test_canonical_ties_and_reference_ids_do_not_leak_into_action():
    data = [([True, True], True, True), ([False, False], False, False)]
    table, query, solver = example(data, [True, True])
    exact = solver.solve(query)
    assert exact.action == "continue" and exact.evidence[0].feature == "a"
    changed = table.model_copy(
        update={
            "rows": tuple(
                r.model_copy(update={"id": "recover-fault/" + r.id})
                for r in reversed(table.rows)
            )
        }
    )
    other = FiniteIndex(changed, 1).solve(query)
    assert (other.action, other.evidence) == (exact.action, exact.evidence)


def test_empty_evidence_and_larger_support_tie():
    _, query, solver = example([([True], True, True), ([False], True, True)], [True])
    certificate = solver.solve(query)
    assert certificate.action == "continue" and certificate.support == 2
    assert not certificate.evidence and not certificate.witnesses
    _, query, solver = example(
        [
            ([True, True], True, False),
            ([True, False], True, False),
            ([False, False], False, False),
        ],
        [True, True],
    )
    assert solver.solve(query).evidence[0].feature == "a"


def test_independent_exhaustive_and_hitting_set_agreement():
    rng = random.Random(20261113)
    for _ in range(120):
        d = rng.randint(0, 6)
        x = [rng.choice([None, False, True]) for _ in range(d)]
        data = [
            (
                [rng.choice([None, False, True]) for _ in range(d)],
                rng.choice([None, False, True]),
                rng.choice([None, False, True]),
            )
            for _ in range(rng.randint(0, 12))
        ]
        table, query, solver = example(data, x)
        certificate = solver.solve(query)
        assert verify_certificate(
            table.model_dump(mode="json"),
            query.model_dump(mode="json"),
            certificate.model_dump(mode="json"),
            1,
        )
        assert enumerate_oracle(
            table.model_dump(mode="json"), query.model_dump(mode="json"), 1
        ) == enumerate_oracle(
            table.model_dump(mode="json"), query.model_dump(mode="json"), 1, True
        )


def test_runtime_contract_rejects_hidden_or_outcome_fields():
    table, query, _ = example([([True], True, False)], [True])
    with pytest.raises(ValidationError):
        Query.model_validate(
            query.model_dump() | {"condition": "offset002", "future_success": True}
        )
    with pytest.raises(ValidationError):
        ReferenceTable(scope=table.scope, rows=table.rows + table.rows)
    with pytest.raises(ValidationError):
        Query(scope=table.scope, features=(1,))
    with pytest.raises(ValidationError):
        Scope(
            task="test",
            controller_sha256="a",
            features=tuple("abcdefghi"),
            channels="test",
        )
