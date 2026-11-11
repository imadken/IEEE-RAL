"""Event-history integrity, known effects and development-only calibration."""

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.semantics import (
    Action,
    Lit,
    Model,
    apply_action,
    relevant_atoms,
)
from dual_rec.revalidation.contracts import Parameters, RevalidationContext
from dual_rec.revalidation.episodes import (
    REGIMES,
    calibration,
    generate_episodes,
    support_consequence,
)


def task(split="development"):
    model = Model(atoms=frozenset({"p", "q", "r", "x", "g"}))
    plan = (
        Action(name="prepare", pre=(Lit(atom="p"),), add=frozenset({"r"})),
        Action(name="move", pre=(Lit(atom="r"),), add=frozenset({"x"})),
        Action(name="finish", pre=(Lit(atom="q"), Lit(atom="x")), add=frozenset({"g"})),
    )
    actions = plan + (
        Action(name="drop-p", pre=(Lit(atom="p"),), delete=frozenset({"p"})),
        Action(name="drop-q", pre=(Lit(atom="q"),), delete=frozenset({"q"})),
        Action(name="restore-q", add=frozenset({"q"})),
    )
    state = frozenset({"p", "q"})
    states = [sorted(state)]
    for action in plan:
        state = apply_action(action, state)
        states.append(sorted(state))
    return {
        "task_id": "public-style-unit",
        "family": "unit",
        "split": split,
        "model": model.model_dump(mode="json"),
        "actions": [a.model_dump(mode="json") for a in actions],
        "plan": [a.model_dump(mode="json") for a in plan],
        "goal": [{"atom": "g", "positive": True}],
        "nominal_states": states,
        "source_hashes": {"problem": "unit"},
    }


def parameters():
    return Parameters(
        event_hazard=0.1,
        sensor_error=0.02,
        missing_probability=0.1,
        permission_threshold=0.95,
        periodic_interval=1,
        expiry_steps=1,
    )


def episodes():
    return list(generate_episodes([task()], "development", parameters(), schedules=8))


def test_fixed_regime_grid_is_paired_deterministic_and_runtime_has_no_oracle_labels():
    first, second = episodes(), episodes()
    assert len(first) == 2 * 8 * len(REGIMES)
    assert [e.model_dump() for e in first] == [e.model_dump() for e in second]
    assert {e.checkpoint for e in first} == {1, 2}
    for episode in first:
        ctx = episode.context
        assert ctx.base.schedule_offset == 0
        assert all(len(q.atoms) == 1 and q.cost == 1 for q in ctx.base.queries)
        assert "oracle_state" not in ctx.model_dump()
        assert "actual_event_hazard" not in ctx.model_dump()
        assert "regime" not in ctx.model_dump()
        with pytest.raises(ValidationError):
            RevalidationContext.model_validate(
                ctx.model_dump() | {"actual_event_hazard": 1}
            )


def test_every_actual_state_change_is_an_applicable_declared_action():
    saw_change = False
    for episode in episodes():
        lookup = {a.name: a for a in episode.context.actions}
        state = episode.context.trusted_anchor
        pre, post = episode.external_actions
        if pre is not None:
            state = apply_action(lookup[pre], state)
            saw_change = True
        assert state == episode.oracle_cache_state
        for action in episode.context.known_after_cache:
            state = apply_action(action, state)
        if post is not None:
            state = apply_action(lookup[post], state)
            saw_change = True
        assert state == episode.oracle_state
    assert saw_change


def test_no_changes_and_recent_revalidation_controls():
    for episode in episodes():
        if episode.regime == "no_external":
            assert episode.external_actions == (None, None)
            assert episode.oracle_state == episode.context.trusted_anchor
            assert not episode.persistent_bias
        if episode.regime == "recent":
            assert episode.context.age == 0
            assert episode.external_actions[1] is None
            assert episode.oracle_state == episode.oracle_cache_state
            assert episode.context.base.evidence == episode.context.cache_observations


def test_unrelated_changes_respect_complete_declared_model_closure():
    count = 0
    for episode in episodes():
        if episode.regime != "unrelated_event":
            continue
        ctx = episode.context
        closure = relevant_atoms(ctx.base.model, {}, ctx.base.plan, ctx.base.goal)
        assert not ((episode.oracle_state ^ episode.oracle_cache_state) & closure)
        count += episode.external_actions[1] is not None
    assert count


def test_persistent_corruption_is_a_sensor_channel_not_an_action():
    corrupted = 0
    for episode in episodes():
        if episode.regime not in {"noise02", "noise10"}:
            continue
        assert episode.external_actions == (None, None)
        assert episode.oracle_state == episode.context.trusted_anchor
        for atom, value in episode.context.cache_observations.items():
            assert value == (
                (atom in episode.oracle_cache_state)
                != (atom in episode.persistent_bias)
            )
            corrupted += value != (atom in episode.oracle_state)
    assert corrupted


def test_background_proxy_is_excluded_from_unrelated_event_control():
    source = task()
    p, q = Lit(atom="p"), Lit(atom="q")
    source["model"] = Model(
        atoms=frozenset({"p", "q", "r", "x", "g"}),
        constraints=((p.negate(), q), (q.negate(), p)),
    ).model_dump(mode="json")
    selected = list(generate_episodes([source], "development", parameters()))
    for episode in selected:
        if episode.regime == "unrelated_event":
            # p is absent from both retained suffixes, but connected to required q.
            assert "p" in relevant_atoms(
                episode.context.base.model,
                {},
                episode.context.base.plan,
                episode.context.base.goal,
            )
            assert episode.external_actions[1] != "drop-p"


def test_missing_cache_falls_back_to_older_anchor_without_false_timestamp_refresh():
    seen = 0
    for episode in episodes():
        if episode.regime != "missing30":
            continue
        for atom, value in episode.context.cache_observations.items():
            if value is None:
                seen += 1
                assert episode.context.base.evidence[atom] == (
                    atom in episode.context.trusted_anchor
                )
                assert episode.context.observed_at[atom] == -1
                assert episode.context.updated_at[atom] == -1
    assert seen


def test_delayed_query_timestamp_and_observed_action_effect_projection():
    for episode in episodes():
        ctx = episode.context
        if episode.regime == "delayed":
            assert ctx.query_delay == ctx.age
            assert ctx.cache_time == 0
        if episode.regime == "known_action":
            assert ctx.cache_time == -1 and ctx.age == 0 and ctx.pre_gap == 0
            assert len(ctx.known_after_cache) == 1
            action = ctx.known_after_cache[0]
            for atom in action.add | action.delete:
                assert ctx.base.evidence[atom] == (atom in action.add)
                assert ctx.updated_at[atom] == 0
                assert ctx.observed_at[atom] == -1
            assert ctx.base.evidence == {
                atom: atom in episode.oracle_state for atom in ctx.base.model.atoms
            }


def test_signed_support_weights_do_not_count_future_producers_as_initial_supports():
    p, q, r = Lit(atom="p"), Lit(atom="q"), Lit(atom="r")
    plan = (
        Action(name="a", pre=(p,), add=frozenset({"q"})),
        Action(name="b", pre=(q,), add=frozenset({"r"})),
    )
    assert support_consequence(plan, (r,)) == {"p": 3.0}
    assert support_consequence((), (r,)) == {"r": 1.0}


def test_calibration_rejects_qualification_and_records_predeclared_smoothing(tmp_path):
    with pytest.raises(ValueError, match="development-only"):
        calibration([task("qualification")], tmp_path / "bad.json")
    with pytest.raises(ValueError, match="development-only"):
        calibration([], tmp_path / "empty.json")
    result = calibration([task()], tmp_path / "calibration.json")
    payload = json.loads((tmp_path / "calibration.json").read_text())
    assert payload["unit_intervals"] == 128
    assert result.event_hazard == (payload["observed_state_changes"] + 1) / 138
    assert result.sensor_error == (payload["sensor_errors"] + 1) / (
        payload["sensor_bits"] + 50
    )
    assert payload["parents"] == ["public-style-unit"]
    with pytest.raises(FileExistsError):
        calibration([task()], tmp_path / "calibration.json")


def test_split_and_resource_inputs_are_validated():
    with pytest.raises(ValueError, match="Unknown split"):
        list(generate_episodes([], "test", parameters()))
    with pytest.raises(ValueError, match="Schedule"):
        list(generate_episodes([], "development", parameters(), schedules=0))
