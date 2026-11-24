"""Source exclusions require an actual zero-control predecision failure."""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dsre_evidence_eligible import source_failure


def test_only_exact_predecision_planner_failure_is_eligible_for_review():
    record = {
        "status": "FAILED_PREREQUISITE_OR_PREFIX",
        "error": "UPSTREAM_SCREW_PLANNING_FAILED",
        "phase": "prefix",
        "traceback": "line 443, in insertion",
        "prefix": [{"qpos": [0.1, 0.2]}],
        "prefix_controls": [],
        "post_controls": [],
    }
    assert source_failure(record)
    for changes in (
        {"prefix_controls": [[0.1]]},
        {"checkpoint": {}},
        {"success": False},
        {"error": "controller failure"},
        {"phase": "post"},
        {"traceback": "line 444, in insertion"},
        {"prefix": [{"qpos": [float("nan")]}]},
    ):
        altered = copy.deepcopy(record)
        altered.update(changes)
        assert not source_failure(altered)
