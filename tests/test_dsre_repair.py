import random

import pytest

from dual_rec.dsre.features import ObservationHistory, ObservedFrame
from dual_rec.dsre.repair import (
    ParentIndex,
    ParentRules,
    RepairQuery,
    RepairScope,
    RepairTable,
)
from dual_rec.dsre.repair_selection import (
    ceiling_mass,
    optional_values,
    select_channels,
)
from dual_rec.dsre.schemas import Outcomes, ReferenceRow


def table_fixture(data, query, parents=None):
    scope = RepairScope(
        task="test",
        controller_sha256="a" * 64,
        features=tuple(f"f{i}" for i in range(len(query))),
        channels="fixed-test",
    )
    table = RepairTable(
        scope=scope,
        rows=tuple(
            ReferenceRow(
                id=str(i),
                features=tuple(x),
                outcomes=Outcomes(continue_value=c, recover_value=r),
            )
            for i, (x, c, r) in enumerate(data)
        ),
    )
    groups = parents or {r.id: r.id for r in table.rows}
    return table, RepairQuery(scope=scope, features=tuple(query)), groups


def test_refined_schema_keeps_historical_scope_unchanged():
    from pydantic import ValidationError

    from dual_rec.dsre.schemas import Scope

    t, q, g = table_fixture([([True] * 12, True, False)] * 2, [True] * 12)
    result = ParentIndex(t, g).diagnose(q)
    assert result.status == "STRICT_FINITE_REFERENCE" and not result.evidence
    with pytest.raises(ValidationError):
        Scope.model_validate(t.scope.model_dump())


def test_two_conditions_do_not_provide_two_independent_parents():
    t, q, g = table_fixture(
        [([True], True, False)] * 2, [True], {"0": "same-seed", "1": "same-seed"}
    )
    result = ParentIndex(t, g).diagnose(q)
    assert result.status == "REFERENCE_INSUFFICIENT"
    assert {o.kind for o in result.obstructions} == {"REFERENCE_INSUFFICIENT"}
    assert ParentRules(t, g).select(q).action is None


def test_ambiguity_and_inadequacy_overlap_and_more_observation_cannot_fix_neither():
    t, q, g = table_fixture(
        [([True], True, False), ([True], False, True), ([True], False, False)], [True]
    )
    result = ParentIndex(t, g).diagnose(q)
    assert {o.kind for o in result.obstructions} == {
        "REPERTOIRE_INADEQUATE",
        "OBSERVATIONAL_AMBIGUITY",
    }
    assert result.action is None
    assert len({id for o in result.obstructions for id in o.ids}) == 3


def test_missing_outcome_scope_and_reference_are_not_physical_impossibility():
    t, q, g = table_fixture([([True], True, None), ([True], True, False)], [True])
    assert {o.kind for o in ParentIndex(t, g).diagnose(q).obstructions} == {
        "REFERENCE_INSUFFICIENT"
    }
    wrong = q.model_copy(update={"scope": q.scope.model_copy(update={"task": "wrong"})})
    assert ParentIndex(t, g).diagnose(wrong).status == "REFERENCE_INSUFFICIENT"
    t, q, g = table_fixture([], [True])
    assert ParentIndex(t, g).diagnose(q).status == "REFERENCE_INSUFFICIENT"


def test_optional_values_signed_boundary_and_missing_packet():
    frame = ObservedFrame(
        time=1,
        object_position=(-0.02, 0.03, 0),
        goal_position=(0, 0, 0),
        tcp_position=(0.01, 0, 0),
        finger_positions=None,
    )
    history = ObservationHistory(first=None, current=frame)
    assert optional_values(history) == (False, False, False, True, False, True)
    missing = history.model_copy(
        update={"current": frame.model_copy(update={"goal_position": None})}
    )
    assert optional_values(missing)[:4] == (None,) * 4


def selection_rows():
    return [
        {
            "id": str(i),
            "group": str(i),
            "features": [True],
            "optional_features": [bool(i % 2), False, False, False, False, False],
            "outcomes": {"continue_value": i % 2 == 0, "recover_value": i % 2 == 1},
        }
        for i in range(4)
    ]


def test_exact_upgrade_resolves_collision_and_stops_at_minimum_cost():
    rows = selection_rows()
    assert ceiling_mass(rows, ()) == 0 and ceiling_mass(rows, (0,)) == 4
    for budget in (1, 2, 3):
        assert select_channels(rows, budget) == (0,)
        assert select_channels(rows, budget, "greedy_coverage") == (0,)
        assert select_channels(rows, budget, "greedy_entropy") == (0,)
    shuffled = list(reversed(rows))
    assert select_channels(shuffled, 3) == (0,)
    for method in ("canonical", "random"):
        assert select_channels(rows, 3, method) == select_channels(shuffled, 3, method)


def test_nested_refinement_ceiling_and_unknown_rules():
    rng = random.Random(17)
    for _ in range(40):
        rows = [
            {
                "id": str(i),
                "group": str(i),
                "features": [rng.choice([True, False, None])],
                "optional_features": [
                    rng.choice([True, False, None]) for _ in range(6)
                ],
                "outcomes": {
                    "continue_value": rng.choice([True, False]),
                    "recover_value": rng.choice([True, False]),
                },
            }
            for i in range(12)
        ]
        assert (
            ceiling_mass(rows, ())
            <= ceiling_mass(rows, (0,))
            <= ceiling_mass(rows, (0, 1))
            <= ceiling_mass(rows, tuple(range(6)))
        )
    t, q, g = table_fixture(
        [([True, True], True, False), ([True, None], False, True)], [True, True]
    )
    assert ParentIndex(t, g).diagnose(q).action is None


def test_exact_search_finds_known_two_channel_synergy_greedy_cannot():
    rows = []
    for a in (False, True):
        for b in (False, True):
            for repeat in range(2):
                rows.append(
                    {
                        "id": f"{a}/{b}/{repeat}",
                        "group": f"{a}/{b}/{repeat}",
                        "features": [True],
                        "optional_features": [a, b, False, False, False, False],
                        "outcomes": {"continue_value": a == b, "recover_value": a != b},
                    }
                )
    assert select_channels(rows, 2) == (0, 1)
    assert select_channels(rows, 2, "greedy_coverage") == ()
    assert select_channels(rows, 2, "greedy_entropy") == ()


def test_independent_parent_rule_and_obstruction_agreement():
    from dual_rec.dsre.repair_oracle import Oracle

    rng = random.Random(20261113)
    for _ in range(100):
        d = rng.randint(0, 6)
        data = [
            (
                [rng.choice((True, False, None)) for _ in range(d)],
                rng.choice((True, False, None)),
                rng.choice((True, False, None)),
            )
            for _ in range(rng.randint(0, 12))
        ]
        x = [rng.choice((True, False, None)) for _ in range(d)]
        t, q, g = table_fixture(data, x)
        g = {r.id: str(int(r.id) // 2) for r in t.rows}
        oracle = Oracle(t.model_dump(mode="json"), g)
        result = ParentIndex(t, g).diagnose(q)
        assert oracle.verify(q.model_dump(mode="json"), result.model_dump(mode="json"))
        for beta in (0, 0.1):
            expected = oracle.rule(q.model_dump(mode="json"), beta)
            found = ParentRules(t, g).select(q, beta)
            assert found.action == (expected["action"] if expected else None)
            if expected:
                assert found.evidence == result.evidence if beta == 0 else True


def test_adding_channel_cannot_remove_supported_broader_certificate():
    t, q, g = table_fixture(
        [([True, False], True, False), ([True, True], True, False)], [True, False]
    )
    output = ParentIndex(t, g).diagnose(q)
    assert output.action == "continue" and not output.evidence
    assert output.independent_parents == 2


def test_unqualified_row_is_reference_problem_not_a_physical_ambiguity():
    t, q, g = table_fixture([([True], True, False), ([True], False, True)], [True])
    t = t.model_copy(
        update={"rows": (t.rows[0].model_copy(update={"qualified": False}), t.rows[1])}
    )
    result = ParentIndex(t, g).diagnose(q)
    assert {o.kind for o in result.obstructions} == {"REFERENCE_INSUFFICIENT"}


def test_refined_serialization_and_frozen_offline_plan():
    from dual_rec.dsre.repair_interface import attach_plan, restore_output

    t, q, g = table_fixture([([True] * 12, True, False)] * 2, [True] * 12)
    result = ParentIndex(t, g).diagnose(q)
    assert restore_output(result.model_dump(mode="json")) == result
    plan = {
        "channels": [0],
        "budget": 1,
        "training_rows": 2,
        "training_ceiling_mass": 2,
        "reference_sha256": "a" * 64,
        "selector": "exact_coverage",
    }
    output = attach_plan(result, plan, 0)
    assert output.offline_upgrade.abstract_cost == 1
    assert output.offline_upgrade.guarantees_current_query_repair is False
    assert not output.deployment_enabled


def test_independent_oracle_rejects_wrong_action_and_witness():
    import copy

    from dual_rec.dsre.repair_oracle import Oracle

    t, q, g = table_fixture(
        [
            ([True], True, False),
            ([True], True, False),
            ([False], False, True),
            ([False], False, True),
        ],
        [True],
    )
    oracle = Oracle(t.model_dump(mode="json"), g)
    output = ParentIndex(t, g).diagnose(q).model_dump(mode="json")
    assert oracle.verify(q.model_dump(mode="json"), output)
    wrong = copy.deepcopy(output)
    wrong["action"] = "recover"
    with pytest.raises(AssertionError):
        oracle.verify(q.model_dump(mode="json"), wrong)
    wrong = copy.deepcopy(output)
    wrong["certificate"]["witnesses"][0]["states"][0]["id"] = "0"
    with pytest.raises(AssertionError):
        oracle.verify(q.model_dump(mode="json"), wrong)


@pytest.mark.parametrize(
    "script",
    ["prepare", "experiment", "analyze", "frontier", "audit", "review", "finish"],
)
def test_repair_entrypoints_refuse_sealed_root(tmp_path, script):
    import subprocess
    import sys

    (tmp_path / "completion_manifest.json").write_text("{}")
    argv = [
        sys.executable,
        "scripts/dsre_repair_" + script + ".py",
        "--root",
        str(tmp_path),
    ]
    if script == "finish":
        argv += ["--stage", "initialize"]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "Evidence sealed" in result.stderr + result.stdout
