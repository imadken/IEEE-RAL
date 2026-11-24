"""Offline checks of pilot contrasts, observation masks and exact control budgets."""

import copy

import pytest
from rpd_pilot_audit import (
    compare_options,
    fixed_probe,
    independent_response,
    required_packet,
)
from rpd_pilot_common import MENUS, delay, histories, parents, rows

from dual_rec.recoverability.adapters import (
    encode_response,
    mask_native_state,
    probe_commands,
)


def state(index):
    return {
        "time": index / 20,
        "observation": {
            "agent": {"qpos": [[0.0] * 9], "qvel": [[0.0] * 9]},
            "extra": {
                "tcp_pose": [[0.0, 0.0, 0.1 + index * 0.0007, 1, 0, 0, 0]],
                "obj_pose": [[9] * 7],
                "is_grasped": [True],
            },
        },
        "future_success": True,
        "contacts": ["hidden"],
    }


def test_exact_old_reservations_and_added_controls():
    assert len(parents()) == 20
    manifest = rows()
    assert len(manifest) == 1080
    for parent in parents():
        assigned = [r for r in manifest if r.parent == parent]
        assert len(assigned) == 54
        assert (
            sum(
                bool(r.history) and r.history[0].startswith("neutral") for r in assigned
            )
            == 12
        )
        assert (
            sum(
                not r.history or not r.history[0].startswith("neutral")
                for r in assigned
            )
            == 42
        )
        assert all(r.delay_ticks + r.macro_ticks <= 90 for r in assigned)


@pytest.mark.parametrize("task", MENUS)
def test_original_commands_not_replaced(task):
    assert len(histories(task)) == 9
    for probe in MENUS[task]:
        assert fixed_probe(task, probe) == [
            list(a) for a in probe_commands(task, probe)
        ]
    for history in histories(task):
        assert delay(history) in (0, 10, 20)
    assert len(fixed_probe(task, "neutral10")) == 10
    assert len(fixed_probe(task, "neutral20")) == 20


@pytest.mark.parametrize(
    "hold,probe,erasure,creation,lost,gained",
    [
        (["continue"], [], True, False, ["continue"], []),
        ([], ["recover"], False, True, [], ["recover"]),
        (["continue", "recover"], ["recover"], False, False, ["continue"], []),
        (["continue"], ["recover"], False, False, ["continue"], ["recover"]),
        ([], [], False, False, [], []),
    ],
)
def test_paired_hold_estimand(hold, probe, erasure, creation, lost, gained):
    result = compare_options(hold, probe)
    assert result == {
        "status": "KNOWN",
        "erasure": erasure,
        "creation": creation,
        "lost": lost,
        "gained": gained,
    }


@pytest.mark.parametrize("hold,probe", [(None, []), (["continue"], None), (None, None)])
def test_missing_outcomes_are_not_empty_option_sets(hold, probe):
    assert compare_options(hold, probe)["status"] == "UNKNOWN"
    assert compare_options(hold, probe)["erasure"] is None


def test_independent_response_and_hidden_field_separation():
    frames = [state(i) for i in range(11)]
    allowed = tuple(mask_native_state(s) for s in frames)
    assert encode_response(allowed).model_dump(mode="json") == independent_response(
        frames
    )
    modified = copy.deepcopy(frames)
    for s in modified:
        s["future_success"] = False
        s["contacts"] = []
        s["observation"]["extra"]["obj_pose"] = [[0] * 7]
        s["observation"]["extra"]["is_grasped"] = [False]
    assert independent_response(modified) == independent_response(frames)
    assert required_packet(frames[0]) == mask_native_state(frames[0]).model_dump(
        mode="json"
    )


def test_missing_frame_or_clock_is_source_failure():
    frames = [mask_native_state(state(i)) for i in range(11)]
    with pytest.raises(ValueError):
        encode_response(tuple(frames[:-1]))
    with pytest.raises(ValueError):
        encode_response((frames[0], *frames[2:], frames[-1]))
