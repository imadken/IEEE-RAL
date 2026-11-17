"""Independent numerical oracle for DSRE evidence-aware design.

This is supervisor design validation, not a robot experiment.  Dependencies:
Python 3.10+, NumPy, SciPy.  Run with --output <report.json>.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.optimize import linprog
from scipy.stats import beta

# Joint ordering: 00, 01, 10, 11, where first index is continuation success.
P0 = np.array([0., 0., 1., 1.])
P1 = np.array([0., 1., 0., 1.])
HARM = np.array([0., 0., 1., 0.])
RESCUE = np.array([0., 1., 0., 0.])
GAIN = RESCUE - HARM

@dataclass(frozen=True)
class Band:
    lo: float
    hi: float
    def __post_init__(self) -> None:
        if not (0 <= self.lo <= self.hi <= 1):
            raise ValueError(f'Invalid probability band: {self}')


def cp_band(k: int, n: int, tail: float) -> Band:
    """Exact two-sided interval, with each tail assigned probability `tail`."""
    if not (0 <= k <= n and 0 < tail < .5):
        raise ValueError('Invalid count or confidence allocation')
    if n == 0:
        return Band(0., 1.)
    lower = 0. if k == 0 else float(beta.ppf(tail, k, n-k+1))
    upper = 1. if k == n else float(beta.ppf(1-tail, k+1, n-k))
    return Band(lower, upper)


def joint_extreme(p0: Band, p1: Band, objective: np.ndarray, *,
                  maximize: bool = False, harm: Band | None = None,
                  rescue: Band | None = None) -> tuple[float, np.ndarray]:
    rows, limits = [], []
    constraints = [(P0, p0), (P1, p1)]
    if harm is not None:
        constraints.append((HARM, harm))
    if rescue is not None:
        constraints.append((RESCUE, rescue))
    for coefficient, band in constraints:
        rows.extend([coefficient, -coefficient])
        limits.extend([band.hi, -band.lo])
    result = linprog(-objective if maximize else objective,
        A_ub=np.asarray(rows), b_ub=np.asarray(limits),
        A_eq=np.ones((1, 4)), b_eq=[1.], bounds=[(0., 1.)]*4,
        method='highs')
    if not result.success:
        raise ValueError('Inconsistent evidence polytope; no certificate is allowed')
    q = np.asarray(result.x)
    assert np.min(q) >= -1e-8 and abs(float(q.sum())-1) < 1e-8
    return float(objective @ q), q


def evidence_measurable(mask: Sequence[int], cells: Sequence[int]) -> bool:
    """A display conjunction must be a union of whole frozen routing cells."""
    for cell in set(cells):
        values = {bool(mask[i]) for i, c in enumerate(cells) if c == cell}
        if len(values) > 1:
            return False
    return True


def minimal_certificate(query: Sequence[int], cell_ids: Sequence[int],
                        approved: set[int]) -> tuple[int, ...] | None:
    """Minimum conjunction over a complete finite binary feature space.

    Cells and approval are fixed, actions are cell-constant.  This procedure
    cannot split a calibrated leaf to extract a favorable hidden subgroup.
    """
    d = len(query)
    space = tuple(itertools.product((0, 1), repeat=d))
    if len(space) != len(cell_ids):
        raise ValueError('Cell assignment must cover the full binary space')
    for length in range(d+1):
        for subset in itertools.combinations(range(d), length):
            mask = [all(x[j] == query[j] for j in subset) for x in space]
            if not evidence_measurable(mask, cell_ids):
                continue
            matching = {cell_ids[i] for i, selected in enumerate(mask) if selected}
            if matching and matching.issubset(approved):
                return subset
    return None


def run_audit() -> dict:
    exact_error, cases, ident_cases = 0., 0, 0
    for p0, p1 in itertools.product(np.linspace(0, 1, 21), repeat=2):
        lower, qlo = joint_extreme(Band(p0,p0), Band(p1,p1), HARM)
        upper, qhi = joint_extreme(Band(p0,p0), Band(p1,p1), HARM, maximize=True)
        expected = (max(0.,p0-p1), min(p0,1-p1))
        exact_error = max(exact_error,abs(lower-expected[0]),abs(upper-expected[1]))
        for q in (qlo,qhi):
            assert abs(P0@q-p0) < 1e-8 and abs(P1@q-p1) < 1e-8
        gain, _ = joint_extreme(Band(p0,p0), Band(p1,p1), GAIN)
        assert abs(gain-(p1-p0)) < 1e-8
        alpha=.1
        by_upper = upper <= alpha+1e-10
        by_route = p0 <= alpha+1e-10 or p1 >= 1-alpha-1e-10
        assert by_upper == by_route
        if lower <= alpha+1e-10 and upper > alpha+1e-10:
            ident_cases += 1
        cases += 1
    assert exact_error < 1e-8

    rng=np.random.default_rng(20261117)
    rectangle_error=0.
    for _ in range(256):
        a=np.sort(rng.uniform(size=2)); b=np.sort(rng.uniform(size=2))
        p0,p1=Band(*a),Band(*b)
        lo,_=joint_extreme(p0,p1,HARM)
        hi,_=joint_extreme(p0,p1,HARM,maximize=True)
        gain,_=joint_extreme(p0,p1,GAIN)
        rectangle_error=max(rectangle_error,
            abs(lo-max(0,p0.lo-p1.hi)),abs(hi-min(p0.hi,1-p1.lo)),
            abs(gain-(p1.lo-p0.hi)))
    assert rectangle_error < 1e-8

    # Added paired constraints must not weaken bounds on the SAME distribution.
    nesting=0
    for _ in range(256):
        q=rng.dirichlet(np.ones(4))
        p0v,p1v=float(P0@q),float(P1@q)
        p0=Band(max(0,p0v-.1),min(1,p0v+.1))
        p1=Band(max(0,p1v-.1),min(1,p1v+.1))
        h=Band(max(0,q[2]-.03),min(1,q[2]+.03))
        r=Band(max(0,q[1]-.03),min(1,q[1]+.03))
        u0,_=joint_extreme(p0,p1,HARM,maximize=True)
        u1,_=joint_extreme(p0,p1,HARM,maximize=True,harm=h,rescue=r)
        l0,_=joint_extreme(p0,p1,GAIN)
        l1,_=joint_extreme(p0,p1,GAIN,harm=h,rescue=r)
        assert u1 <= u0+1e-8 and l1 >= l0-1e-8
        nesting += 1

    # Same marginals, opposite qualification verdicts.
    worlds=[np.array([.4,.2,0.,.4]),np.array([0.,.6,.4,0.])]
    for q in worlds:
        assert abs(P0@q-.4)<1e-10 and abs(P1@q-.6)<1e-10
        assert abs(GAIN@q-.2)<1e-10
    assert HARM@worlds[0] == 0 and abs(HARM@worlds[1]-.4)<1e-10

    # Naive independence can authorize a harmful policy at alpha=.1.
    bad=np.array([.2,.6,.2,0.])
    independence_harm=float((P0@bad)*(1-P1@bad))
    assert independence_harm < .1 and HARM@bad > .1

    # Frozen depth-two tree, expanded over all binary predicates, including an
    # unused feature. A certificate must not cut a leaf using that extra fact.
    space=tuple(itertools.product((0,1),repeat=3))
    cells=tuple(0 if x[0]==0 else (1 if x[1]==0 else 2) for x in space)
    extra_feature=[x[2]==1 for x in space]
    assert not evidence_measurable(extra_feature,cells)
    assert minimal_certificate((1,0,0),cells,{1}) == (0,1)
    assert minimal_certificate((1,0,0),cells,{1,2}) == (0,)
    assert minimal_certificate((0,0,0),cells,{0,1,2}) == ()
    assert minimal_certificate((0,0,0),cells,set()) is None
    certificate_checks=0
    for labels in itertools.product((0,1),repeat=3):
        approved={j for j,flag in enumerate(labels) if flag}
        for x in space:
            got=minimal_certificate(x,cells,approved)
            all_feasible=[]
            for subset_bits in itertools.product((0,1),repeat=3):
                subset=tuple(j for j,v in enumerate(subset_bits) if v)
                mask=[all(z[j]==x[j] for j in subset) for z in space]
                if evidence_measurable(mask,cells):
                    js={cells[i] for i,v in enumerate(mask) if v}
                    if js and js <= approved: all_feasible.append(subset)
            assert (got is None) == (not all_feasible)
            if got is not None:
                assert len(got)==min(map(len,all_feasible))
            certificate_checks+=1

    # A regional risk guarantee cannot be inherited by a selected subregion.
    pooled_harm=.10*.80 + .90*0.
    assert pooled_harm <= .1 and .80 > .1

    # Coherent evidence must fail closed, never project to a convenient model.
    caught=False
    try: joint_extreme(Band(0,0),Band(1,1),HARM,harm=Band(.5,.6))
    except ValueError: caught=True
    assert caught

    # Per-domain primary allocation: .025 marginal event, .025 pair-refinement
    # event, K=4 frozen cells, two Bernoulli quantities per event, two tails.
    tail=.025/(4*4)
    planning={str(n):cp_band(0,n,tail).hi for n in [32,64,96,128,256]}
    assert cp_band(0,0,tail)==Band(0,1)

    return {
        'description':'Supervisor mathematical/design checks only; no robot outcomes generated.',
        'marginal_grid_cases':cases, 'max_exact_harm_error':exact_error,
        'exact_marginal_nonidentification_cases_at_alpha_0_1':ident_cases,
        'random_interval_rectangles':256,'max_rectangle_error':rectangle_error,
        'paired_constraint_nesting_cases':nesting,
        'certificate_exhaustive_cases':certificate_checks,
        'same_marginal_worlds':[q.tolist() for q in worlds],
        'naive_independence_counterexample':{'joint':bad.tolist(),'predicted_harm':independence_harm,'actual_harm':float(HARM@bad)},
        'routing_counterexample':{'full_region_harm':pooled_harm,'chosen_subregion_harm':.8},
        'zero_error_upper_bounds_per_prespecified_tail':planning,
        'nonrandomized_logs_claim':'No causal certificate without supported identification assumptions.',
        'test_status':'PASS'
    }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('supervisor_validation.json'))
    args=parser.parse_args()
    result=run_audit()
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
