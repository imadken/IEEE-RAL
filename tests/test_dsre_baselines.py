import pytest

from dual_rec.dsre.baselines import OutcomeRules, OutcomeTree
from dual_rec.dsre.schemas import Outcomes, Query, ReferenceRow, ReferenceTable, Scope
from dual_rec.dsre.solver import FiniteIndex


def setup():
    scope = Scope(
        task="test",
        controller_sha256="a" * 64,
        features=("a", "b", "c"),
        channels="test",
    )
    rows = tuple(
        ReferenceRow(
            id=str(i),
            features=values,
            outcomes=Outcomes(continue_value=c, recover_value=r),
        )
        for i, (values, c, r) in enumerate(
            [
                ((True, True, True), True, False),
                ((False, False, True), False, True),
                ((False, True, False), False, True),
            ]
        )
    )
    table = ReferenceTable(scope=scope, rows=rows)
    return table, Query(scope=scope, features=(True, True, True))


def test_plain_rule_and_mean_one_are_exactly_dsre():
    table, query = setup()
    rules = OutcomeRules(table, 1)
    exact = FiniteIndex(table, 1).solve(query)
    for result in [rules.minimum(query, 1), rules.minimum(query, exact=True)]:
        assert (result.action, result.evidence, result.support) == (
            exact.action,
            exact.evidence,
            exact.support,
        )


@pytest.mark.parametrize("budget", [1, 2])
def test_bounded_rule_evidence_and_support(budget):
    table, query = setup()
    result = OutcomeRules(table, 1).minimum(query, target=1, maximum_length=budget)
    assert len(result.evidence) <= budget and result.support >= 1
    unavailable = OutcomeRules(table, 99).minimum(
        query, target=1, maximum_length=budget
    )
    assert unavailable.action is None


def test_four_category_tree_keeps_both_and_neither_categories():
    table, query = setup()
    rows = tuple(
        ReferenceRow(
            id=str(i),
            features=(True, True, True),
            outcomes=Outcomes(continue_value=bool(i & 1), recover_value=bool(i & 2)),
        )
        for i in range(4)
    )
    rules = OutcomeRules(table.model_copy(update={"rows": rows}), 1)
    result = OutcomeTree(rules, 3).predict(query, 0.5)
    assert result.category_probabilities == (0.25, 0.25, 0.25, 0.25)
    assert result.action == "continue"
    assert OutcomeTree(rules, 3).predict(query, 1).action is None


def test_unknown_tree_query_abstains_and_unknown_reference_is_conservative():
    table, query = setup()
    rules = OutcomeRules(table, 1)
    tree = OutcomeTree(rules, 1)
    unknown = query.model_copy(update={"features": (None, None, None)})
    assert tree.predict(unknown, 1).action is None
    augmented = table.model_copy(
        update={
            "rows": table.rows
            + (
                ReferenceRow(
                    id="unknown",
                    features=(None, None, None),
                    outcomes=Outcomes(continue_value=False, recover_value=False),
                ),
            )
        }
    )
    assert OutcomeRules(augmented, 1).minimum(query, 1).action is None


def test_model_training_uses_reference_outcomes_not_query_or_id_hints():
    table, query = setup()
    rows = tuple(
        r.model_copy(
            update={
                "outcomes": Outcomes(continue_value=False, recover_value=True),
                "id": "continue-hint/" + r.id,
            }
        )
        for r in table.rows
    )
    switched = OutcomeRules(table.model_copy(update={"rows": rows}), 1)
    assert switched.full(query, 1).action == "recover"
    assert OutcomeTree(switched, 1).predict(query, 1).action == "recover"
    assert not OutcomeRules(table, 2).minimum(query, 1).action


def test_scope_mismatch_and_depth_budget_for_all_predictors():
    table, query = setup()
    rules = OutcomeRules(table, 1)
    mismatched = query.model_copy(
        update={"scope": query.scope.model_copy(update={"channels": "new-camera"})}
    )
    for result in [
        rules.minimum(mismatched),
        rules.full(mismatched),
        rules.policy(mismatched),
        OutcomeTree(rules).predict(mismatched),
    ]:
        assert result.action is None and result.reason == "SCOPE_MISMATCH"
    for depth in (1, 2, 3):
        assert len(OutcomeTree(rules, depth).predict(query, 1).evidence) <= depth
        assert len(OutcomeTree(rules, depth, 0.01).predict(query, 1).evidence) <= depth
