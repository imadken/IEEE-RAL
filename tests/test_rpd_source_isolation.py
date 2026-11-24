"""Authorization, same-input and resource guards for source diagnosis only."""

import pytest
from pydantic import ValidationError
from rpd_isolation_common import Job, planned_jobs
from rpd_isolation_run import affordable


def test_exact_four_then_twenty_four_and_unchanged_failed_inputs():
    selected = planned_jobs()
    assert len(selected) == 28
    first = [j for j in selected if j.phase == "failed_row_replay"]
    holds = [j for j in selected if j.phase == "neutral_control"]
    assert len(first) == 4 and len(holds) == 24
    for task in ("PickCube-v1", "PushCube-v1"):
        pair = [j for j in first if j.row.parent.task == task]
        assert pair[0].row == pair[1].row
        assert pair[0].job_id != pair[1].job_id
        assert pair[0].row.repeat == 0
        assert sum(j.row.parent.task == task for j in holds) == 12
        assert {j.row.parent.index for j in selected if j.row.parent.task == task} == {
            0
        }


def test_new_parent_and_replacement_history_rejected():
    value = planned_jobs()[0].model_dump(mode="json")
    value["row"]["parent"]["index"] = 1
    with pytest.raises(ValidationError):
        Job.model_validate(value)
    value = planned_jobs()[0].model_dump(mode="json")
    value["row"]["history"] = ["micro_lift"]
    with pytest.raises(ValidationError):
        Job.model_validate(value)


@pytest.mark.parametrize(
    "spent,previous,bytes_used,allowed",
    [
        (0, [], 0, True),
        (1199, [1], 0, False),
        (0, [], 100 * 1024**2, False),
        (1180, [20], 0, False),
        (30, [10], 2 * 1024**2, True),
    ],
)
def test_atomic_budget_guard(spent, previous, bytes_used, allowed):
    assert affordable(spent, previous, bytes_used) == allowed
