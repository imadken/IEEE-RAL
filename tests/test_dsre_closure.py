"""Independent closure regressions for scope, provenance and source semantics."""

import itertools
import os
import subprocess
import sys
from pathlib import Path

import pytest
from dsre_closure_common import (
    b7_certificate,
    calibrated,
    canonical,
    cp,
    lp,
    matching_scope,
    output,
    passed,
    route,
    rule_library,
)
from dsre_closure_evaluate import independent_extrema
from dsre_closure_math import admissible, exact

from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.schema import Bounds, Partition, Scope, Source


def model():
    scope = Scope(
        task="ANALYTICAL_TEST",
        controller_sha256="fixed",
        horizon=70,
        outcome="binary terminal",
        population="synthetic theorem fixture",
        observation_protocol="three bits",
    )
    partition = {
        "vocabulary": ["a", "b", "irrelevant"],
        "cells": [
            0 if not x[0] else 1 if not x[1] else 2
            for x in itertools.product((False, True), repeat=3)
        ],
        "tree": [0, -1, 1],
        "discovery_parents": [],
    }
    leaves = {
        str(c): {
            "evidence": exact(*marginals),
            "bounds": lp(exact(*marginals)),
            "failure": None,
            "counts": [100, 100, 0],
        }
        for c, marginals in enumerate([(0.01, 0.8), (0.3, 0.2), (0.8, 0.8)])
    }
    return {
        "partition": partition,
        "leaves": leaves,
        "source_scope": scope.model_dump(mode="json"),
    }


def test_unknown_is_not_false_and_not_a_subcell_guarantee():
    m = model()
    assert route(m["partition"], (False, False, False)) == 0
    assert route(m["partition"], (None, False, False)) is None
    assert b7_certificate(m, (False, False, None), "useful") is None
    assert output(m, (False, False, None), "useful", None)["withholding"][
        "reasons"
    ] == ["UNAVAILABLE_OBSERVATIONS"]


def test_exhaustive_b7_matches_production_complete_certificate():
    m = model()
    p = Partition.model_validate(m["partition"])
    b = {int(c): Bounds.model_validate(v["bounds"]) for c, v in m["leaves"].items()}
    for obligation in ("harm_only", "completion", "useful"):
        rules = rule_library(
            m["partition"],
            {int(c) for c, v in m["leaves"].items() if passed(v["bounds"], obligation)},
        )
        for x in itertools.product((False, True), repeat=3):
            prod = minimum(
                p,
                x,
                b,
                Source.LOGGED,
                obligation,
                outcome_scope=Scope.model_validate(m["source_scope"]),
            )
            ordinary = b7_certificate(m, x, obligation, rules)
            assert canonical(
                prod.model_dump(mode="json") if prod else None
            ) == canonical(ordinary)


def test_deletion_names_the_exact_unqualified_cells():
    m = model()
    cert = b7_certificate(m, (False, False, False), "useful")
    assert cert["evidence"] == [["a", False]]
    assert cert["selected_leaf_scope"] == [0]
    assert cert["removal_witnesses"] == {"a": "unqualified leaves admitted: [1, 2]"}
    assert matching_scope(m["partition"], ((2, False),)) is None


def test_same_marginal_worlds_are_jointly_admissible():
    for q in ([0.4, 0.2, 0, 0.4], [0, 0.6, 0.4, 0]):
        admissible(q, exact(0.4, 0.6))
    low, high = independent_extrema((0.4, 0.6))
    assert low[2] == 0 and high[2] == pytest.approx(0.4)
    assert lp(exact(0.4, 0.6))["gain_lower"] == pytest.approx(0.2)


def test_insufficient_sample_is_not_structural_nonidentification():
    assert cp(0, 0, 0.0015625) == {"lo": 0.0, "hi": 1.0}
    records = [
        {
            "parent_id": str(i),
            "action": "r" if i % 2 else "c",
            "propensity": 0.5,
            "y": bool(i % 2),
        }
        for i in range(8)
    ]
    fitted = calibrated(records, [], 4, 0)
    assert not passed(fitted["bounds"], "useful")
    assert passed(lp(exact(0, 1)), "useful")
    assert fitted["bounds"]["harm_upper"] > 0.1


def test_ingestion_rejects_duplicate_unknown_propensity_and_mixed_scope():
    row = {
        "parent_id": "p",
        "action": "c",
        "propensity": 0.5,
        "y": False,
        "source_scope": {"task": "a"},
    }
    with pytest.raises(ValueError, match="DUPLICATE_PARENT"):
        calibrated([row, row], [], 1, 0)
    with pytest.raises(ValueError, match="PROPENSITY"):
        calibrated([dict(row, propensity=None)], [], 1, 0)
    with pytest.raises(ValueError, match="SCOPE_MISMATCH"):
        calibrated(
            [row, dict(row, parent_id="q", action="r", source_scope={"task": "b"})],
            [],
            1,
            0,
        )
    result = calibrated([dict(row, source_type="uncontrolled_observational")], [], 1, 0)
    assert result["failure"] == "IDENTIFICATION_ASSUMPTION_UNSUPPORTED"


def test_naive_independence_can_falsely_authorize():
    assert 0.2 * (1 - 0.6) < 0.1
    _, q = independent_extrema((0.2, 0.6))
    admissible(q, exact(0.2, 0.6))
    assert q[2] > 0.1 and q[1] - q[2] > 0.05
    assert not passed(lp(exact(0.2, 0.6)), "useful")


def test_cellwise_qualification_is_sufficient_not_necessary_for_pooled_average():
    assert not passed(lp(exact(1, 1)), "useful")
    assert passed(lp(exact(0.5, 1)), "useful")


def test_gain_prefilter_is_a_real_additional_objective():
    m = model()
    m["leaves"]["0"]["evidence"] = exact(1, 1)
    m["leaves"]["0"]["bounds"] = lp(exact(1, 1))
    cert = b7_certificate(m, (False, False, False), "harm_only")
    assert output(m, (False, False, False), "harm_only", cert)["action"] == "r"
    veto = output(m, (False, False, False), "harm_only", cert, prefilter=True)
    assert (
        veto["action"] == "c"
        and "FROZEN_DISCOVERY_GAIN_PREFILTER" in veto["withholding"]["reasons"]
    )


def test_L_process_cannot_read_a_paired_file(tmp_path):
    one = tmp_path / "L.json"
    pair = tmp_path / "P.json"
    one.write_text('{"y":true}')
    pair.write_text('{"yc":false,"yr":true}')
    program = """from pathlib import Path
from dual_rec.evidence_aware.views import guard_data_access
import sys
root=Path(sys.argv[1]);guard_data_access(root,[root/'L.json'])
assert (root/'L.json').read_text()
try: (root/'P.json').read_text()
except PermissionError: pass
else: raise AssertionError('Counterpart source leaked')
"""
    env = dict(os.environ, PYTHONPATH=str(Path.cwd() / "src"))
    subprocess.run([sys.executable, "-c", program, str(tmp_path)], env=env, check=True)
