"""Independent LP agreement, scope soundness, and source boundary regressions."""

import importlib
import itertools
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from dual_rec.evidence_aware.acquisition import allocate
from dual_rec.evidence_aware.bounds import calibrate, cp, qualifies, solve
from dual_rec.evidence_aware.certificate import minimum, selected_scope
from dual_rec.evidence_aware.diagnosis import diagnose, plugin_diagnosis
from dual_rec.evidence_aware.partition import assignments, fit, route
from dual_rec.evidence_aware.schema import (
    Band,
    Evidence,
    OneAction,
    Pair,
    Partition,
    Scope,
    Source,
)


def scope():
    return Scope(
        task="t",
        controller_sha256="frozen",
        horizon=70,
        outcome="terminal",
        population="p",
        observation_protocol="x",
    )


def log(i, x=(False,), action="c", y=False):
    return OneAction(
        parent_id=str(i),
        x=x,
        action=action,
        y=y,
        propensity=0.5,
        controls=70,
        wall_seconds=1,
        source_scope=scope(),
    )


def exact(p0, p1, **kw):
    return Evidence(p0=Band(lo=p0, hi=p0), p1=Band(lo=p1, hi=p1), scope="same", **kw)


def test_independent_supervisor_grid_and_rectangles(monkeypatch):
    monkeypatch.syspath_prepend(str(Path.cwd()))
    ref = importlib.import_module("research.dsre_evidence_design.supervisor_reference")
    for p0, p1 in itertools.product(np.linspace(0, 1, 21), repeat=2):
        got = solve(exact(p0, p1))
        lo, _ = ref.joint_extreme(ref.Band(p0, p0), ref.Band(p1, p1), ref.HARM)
        hi, _ = ref.joint_extreme(
            ref.Band(p0, p0), ref.Band(p1, p1), ref.HARM, maximize=True
        )
        assert got.harm_lower == pytest.approx(lo, abs=1e-10)
        assert got.harm_upper == pytest.approx(hi, abs=1e-10)
        assert got.gain_lower == pytest.approx(p1 - p0, abs=1e-10)
    rng = np.random.default_rng(20261117)
    for _ in range(256):
        a, b = np.sort(rng.random(2)), np.sort(rng.random(2))
        e = Evidence(p0=Band(lo=a[0], hi=a[1]), p1=Band(lo=b[0], hi=b[1]), scope="same")
        got = solve(e)
        assert got.harm_upper == pytest.approx(min(a[1], 1 - b[0]))
        assert got.gain_lower == pytest.approx(b[0] - a[1])
        assert got.failure_upper == pytest.approx(1 - b[0])


def test_refinement_never_weakens_same_target():
    rng = np.random.default_rng(32)
    for _ in range(256):
        q = rng.dirichlet(np.ones(4))
        p0 = q[2] + q[3]
        p1 = q[1] + q[3]
        e = Evidence(
            p0=Band(lo=max(0, p0 - 0.1), hi=min(1, p0 + 0.1)),
            p1=Band(lo=max(0, p1 - 0.1), hi=min(1, p1 + 0.1)),
            scope="same",
        )
        refined = e.model_copy(
            update={
                "source_type": Source.PAIRED,
                "harm": Band(lo=max(0, q[2] - 0.03), hi=min(1, q[2] + 0.03)),
                "rescue": Band(lo=max(0, q[1] - 0.03), hi=min(1, q[1] + 0.03)),
            }
        )
        a, b = solve(e), solve(refined)
        assert b.harm_upper <= a.harm_upper + 1e-10
        assert b.gain_lower >= a.gain_lower - 1e-10


def test_two_world_witness_and_known_negative_controls():
    w = diagnose(exact(0.4, 0.6))
    assert w.status == "MARGINAL_IDENTIFICATION_BARRIER"
    for q in (w.favorable, w.unfavorable):
        assert q is not None and sum(q) == pytest.approx(1)
        assert q[2] + q[3] == pytest.approx(0.4)
        assert q[1] + q[3] == pytest.approx(0.6)
        assert q[1] - q[2] >= 0.05 - 1e-10
    assert w.favorable[2] <= 0.1 and w.unfavorable[2] > 0.1
    assert qualifies(solve(exact(0.05, 0.70)))
    assert 0.2 * (1 - 0.6) < 0.1 and solve(exact(0.2, 0.6)).harm_upper > 0.1
    assert diagnose(exact(0, 0)).status == "BENEFIT_UNSUPPORTED"
    pooled, subgroup = 0.1 * 0.8, 0.8
    assert pooled <= 0.1 and subgroup > 0.1


def test_cp_confidence_ledger_and_zero_support():
    assert cp(0, 0, 0.0015625) == Band(lo=0, hi=1)
    assert cp(0, 64, 0.0015625).hi == pytest.approx(1 - 0.0015625 ** (1 / 64))
    logs = [log(i, action="c" if i % 2 else "r") for i in range(32)]
    e, ledger = calibrate(logs, [], "leaf", 4)
    assert ledger["per_tail"] == 0.025 / 16
    assert e.p0.hi > 0 and e.p1.hi > 0
    e, _ = calibrate(logs[:1], [], "leaf", 4)
    assert diagnose(e).status == "NO_OVERLAP"
    with pytest.raises(ValueError, match="SCOPE_MISMATCH"):
        calibrate(
            logs,
            [
                Pair(
                    parent_id="new",
                    x=(False,),
                    yc=False,
                    yr=True,
                    source_scope=scope().model_copy(update={"population": "other"}),
                )
            ],
            "leaf",
            4,
        )


def test_fail_closed_and_single_action_contract():
    assert (
        diagnose(exact(0.2, 0.6, source_type=Source.OBSERVATIONAL)).status
        == "IDENTIFICATION_ASSUMPTION_UNSUPPORTED"
    )
    assert (
        diagnose(
            exact(0, 1, harm=Band(lo=0.5, hi=0.6), source_type=Source.PAIRED)
        ).status
        == "INCONSISTENT_BOUNDS"
    )
    assert (
        diagnose(exact(0, 1, harm=Band(lo=0, hi=0))).status
        == "COUNTERPART_SOURCE_MISMATCH"
    )
    with pytest.raises(ValidationError):
        OneAction(**log(0).model_dump(), unassigned_outcome=True)
    with pytest.raises(ValidationError):
        log(0).model_copy().parent_id = "mutated"
    e = Evidence(p0=Band(lo=0, hi=0.15), p1=Band(lo=0.5, hi=0.9), scope="t")
    assert plugin_diagnosis(e, 0.01, 0.7).status == "SAMPLE_LIMITED_AT_PLUGIN"


def test_minimum_scopes_against_independent_exhaustive_reference(monkeypatch):
    monkeypatch.syspath_prepend(str(Path.cwd()))
    ref = importlib.import_module("research.dsre_evidence_design.supervisor_reference")
    xs = assignments(3)
    cells = tuple(0 if not x[0] else 1 if not x[1] else 2 for x in xs)
    p = Partition(
        vocabulary=("a", "b", "unused"),
        cells=cells,
        tree=(0, -1, 1),
        discovery_parents=(),
    )
    good, bad = solve(exact(0.01, 0.8)), solve(exact(0.5, 0.5))
    for flags in itertools.product((False, True), repeat=3):
        bs = {c: good if flags[c] else bad for c in range(3)}
        approved = {i for i, v in enumerate(flags) if v}
        for x in xs:
            want = ref.minimal_certificate(x, cells, approved)
            got = minimum(p, x, bs, Source.LOGGED, outcome_scope=scope())
            assert (got is None) == (want is None)
            if got:
                assert tuple(p.vocabulary.index(n) for n, v in got.evidence) == want
                assert set(got.selected_leaf_scope) <= approved
    assert selected_scope(p, (True, False, False), (2,)) is None
    assert (
        minimum(
            p,
            (None, False, False),
            {0: good, 1: good, 2: good},
            Source.LOGGED,
            outcome_scope=scope(),
        )
        is None
    )
    assert (
        minimum(
            p,
            (False, False, False),
            {0: good, 1: good, 2: good},
            Source.LOGGED,
            outcome_scope=scope(),
        ).evidence
        == ()
    )


def test_discovery_partition_is_arm_observed_only_and_support_constrained():
    rows = [
        log(
            i,
            (bool(i % 2), bool((i // 2) % 2)),
            action="c" if (i // 4) % 2 else "r",
            y=bool(i % 2),
        )
        for i in range(128)
    ]
    p = fit(rows, ("predictive", "other"))
    assert len(set(p.cells)) == 2
    assert all(route(p, r.x) == int(r.x[0]) for r in rows)
    assert fit(rows[:8], ("predictive", "other")).tree == (-1, -1, -1)
    with pytest.raises(ValueError, match="Independent parent"):
        fit(rows + [rows[0]], ("predictive", "other"))


def test_data_access_guard_rejects_hidden_branch(tmp_path):
    allowed = tmp_path / "learner.json"
    hidden = tmp_path / "hidden.json"
    allowed.write_text("[]")
    hidden.write_text("[true]")
    command = """from pathlib import Path
from dual_rec.evidence_aware.views import guard_data_access
root=Path(__import__('sys').argv[1]); seen=guard_data_access(root,[root/'learner.json'])
assert (root/'learner.json').read_text()=='[]'
try: (root/'hidden.json').read_text()
except PermissionError: print('BLOCKED')
else: raise AssertionError('Leak')
assert len(seen)==1
"""
    result = subprocess.run(
        [sys.executable, "-c", command, str(tmp_path)],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH="src"),
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "BLOCKED"


def test_equal_execution_allocation_is_frozen_and_complete():
    diagnoses = {
        0: ("MARGINAL_IDENTIFICATION_BARRIER", 0.4, 0.2),
        1: ("SAMPLE_LIMITED_AT_PLUGIN", 0.1, 0.4),
    }
    masses = {0: 10, 1: 5}
    for strategy in (
        "witness",
        "all_logs",
        "all_pairs",
        "uniform_mix",
        "decision_uncertainty",
    ):
        a = allocate(strategy, diagnoses, masses, 24)
        assert sum(2 if kind == "pair" else 1 for _, kind in a.requests) == a.executions
        assert a.executions + a.unspent == 24
        assert allocate(strategy, diagnoses, masses, 64).executions == 64
    a = allocate("witness", diagnoses, masses, 24)
    assert all(kind == ("pair" if c == 0 else "log") for c, kind in a.requests)


def test_online_scope_mismatch_defaults_to_continue(tmp_path):
    from dual_rec.evidence_aware.schema import Observation, PolicyExecution

    with pytest.raises(ValidationError):
        Observation(parent_id="leak", x=(False,), source_scope=scope(), yr=True)

    model = {
        "partition": Partition(
            vocabulary=("x",), cells=(0, 0), tree=(-1, -1, -1), discovery_parents=()
        ).model_dump(mode="json"),
        "source_scope": scope().model_dump(mode="json"),
        "source_type": Source.LOGGED,
        "leaves": {"0": {"bounds": solve(exact(0.01, 0.8)).model_dump(mode="json")}},
    }
    model_path = tmp_path / "model.json"
    model_path.write_text(__import__("json").dumps(model))
    for matches in (True, False):
        query = tmp_path / f"query-{matches}.json"
        output = tmp_path / f"decision-{matches}.json"
        s = scope() if matches else scope().model_copy(update={"horizon": 400})
        query.write_text(
            __import__("json").dumps(
                {
                    "parent_id": "query",
                    "x": [False],
                    "source_scope": s.model_dump(mode="json"),
                }
            )
        )
        result = subprocess.run(
            [
                sys.executable,
                "scripts/dsre_evidence_online.py",
                str(model_path),
                str(query),
                str(output),
            ],
            env=dict(os.environ, PYTHONPATH="src"),
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr
        decision = __import__("json").loads(output.read_text())
        assert decision["action"] == ("r" if matches else "c")
        if not matches:
            assert decision["status"] == "SCOPE_MISMATCH"
    execution = PolicyExecution(
        parent_id="policy",
        x=(False,),
        action="c",
        y=False,
        controls=70,
        wall_seconds=1,
        source_scope=scope(),
    )
    assert (
        execution.propensity == 1
        and execution.source_type == "deterministic_frozen_policy"
    )
    with pytest.raises(ValidationError):
        OneAction.model_validate(execution.model_dump())


def test_paired_observation_and_repertoire_witnesses_remain_evaluator_only():
    from dual_rec.evidence_aware.diagnosis import (
        observation_aliasing,
        repertoire_failure,
    )

    pairs = [
        Pair(parent_id="c-only", x=(False,), yc=True, yr=False, source_scope=scope()),
        Pair(parent_id="r-only", x=(False,), yc=False, yr=True, source_scope=scope()),
    ]
    w = observation_aliasing(pairs)
    assert w.status == "OBSERVATION_ALIASING" and set(w.parent_ids) == {
        "c-only",
        "r-only",
    }
    both = Pair(
        parent_id="neither", x=(True,), yc=False, yr=False, source_scope=scope()
    )
    assert repertoire_failure(both).parent_ids == ("neither",)


def test_contact_canonicalization_preserves_exact_numeric_channels(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_evidence_audit import equal

    equal(
        {"contacts": [["left", "peg"], ["right", "peg"]]},
        {"contacts": [["peg", "right"], ["peg", "left"]]},
    )
    a = {
        "contacts": [
            ["left", "peg", [1.0, 2.0, 3.0]],
            ["right", "peg", [4.0, 5.0, 6.0]],
        ]
    }
    equal(
        a,
        {
            "contacts": [
                ["peg", "right", [4.0, 5.0, 6.0]],
                ["peg", "left", [1.0, 2.0, 3.0]],
            ]
        },
    )
    with pytest.raises(AssertionError):
        equal(
            a,
            {
                "contacts": [
                    ["peg", "right", [4.0, 5.0, 6.0]],
                    ["peg", "left", [1.000000001, 2.0, 3.0]],
                ]
            },
        )


def test_checkpoint_resume_never_reexecutes_completed_branch(tmp_path, monkeypatch):
    import gzip
    import json

    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_evidence_campaign import child

    from dual_rec.evidence_aware.views import sha

    spec = {
        "task": "PointMaze_UMaze-v3",
        "phase": "development",
        "index": 0,
        "seed": 123,
        "offset": [0, 0],
    }
    d = tmp_path / "physics/PointMaze_UMaze-v3/development/0"
    d.mkdir(parents=True)
    cached = {"spec": spec, "action": "c", "status": "COMPLETE"}
    with gzip.open(d / "assigned.json.gz", "wt") as stream:
        json.dump(cached, stream)
    (d / "assigned.execution.json").write_text(
        json.dumps({"source_sha256": sha(Path("scripts/dsre_evidence_tasks.py"))})
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("Completed physics was reexecuted"),
    )
    assert child(tmp_path, spec, "c", "assigned") == cached
    with pytest.raises(RuntimeError, match="identity mismatch"):
        child(tmp_path, spec, "r", "assigned")
