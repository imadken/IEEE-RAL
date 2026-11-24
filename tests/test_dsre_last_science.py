"""Scientific boundary regressions for the last registered campaign."""

import hashlib

from dsre_last_common import arm
from dsre_last_existing import diagnostic
from dsre_last_model import regression_partition
from dsre_last_physical import native_abort

from dual_rec.evidence_aware.partition import route
from dual_rec.evidence_aware.schema import OneAction, Scope


def test_registered_first_bit_is_most_significant():
    for seed in range(910000000, 910000128):
        first_bit = (
            int(
                hashlib.sha256(f"DSRE-FINAL-PUSH-ARM-v1:{seed}".encode()).hexdigest()[
                    0
                ],
                16,
            )
            >= 8
        )
        assert arm(seed) == ("r" if first_bit else "c")


def test_all_predecision_native_abort_stages_are_uniform_but_not_endpoint_labels():
    for count in (0, 33, 120):
        raw = {
            "status": "FAILED_PREREQUISITE_OR_PREFIX",
            "phase": "prefix",
            "error": "UPSTREAM_SCREW_PLANNING_FAILED",
            "prefix": [{}] * (count + 1),
            "prefix_controls": [[]] * count,
            "post": [],
            "post_controls": [],
        }
        assert native_abort(raw)
        assert not native_abort(dict(raw, phase="post"))
        assert not native_abort(dict(raw, success=False))
        assert not native_abort(dict(raw, checkpoint={}))
        assert not native_abort(dict(raw, error="model mismatch"))


def test_historical_point_estimates_can_find_paired_only_regions():
    rows = [
        {"features": [False] * 6, "c": c, "r": r}
        for c, r, n in [(False, False, 4), (False, True, 2), (True, True, 4)]
        for _ in range(n)
    ]
    result = diagnostic(rows, 6)
    assert result["paired_only"] == 1
    assert result["cells"][0]["h"] == 0


def test_regression_regions_are_discovery_only_and_supported():
    scope = Scope(
        task="synthetic",
        controller_sha256="frozen",
        horizon=70,
        outcome="success",
        population="test",
        observation_protocol="6 measured bits",
    )
    rows = [
        OneAction(
            parent_id=str(i),
            x=[False] * 6,
            action=("c", "r")[i % 2],
            propensity=0.5,
            y=bool(i % 2),
            controls=70,
            wall_seconds=0,
            source_scope=scope,
        )
        for i in range(32)
    ]
    partition, coefficients, proposed = regression_partition(rows)
    assert len(set(partition.cells)) == 1
    assert proposed[route(partition, [False] * 6)]
    assert len(coefficients) == 2
