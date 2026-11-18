"""Supervisor numerical audit of CLASSICAL two-arm partial-identification bounds.
This is mathematical design verification, not new robotics experiment or a new theorem.
Requires scipy, numpy. Run: python research/dsre_final_science/supervisor_oracle.py
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog

alpha, eta = 0.10, 0.05
Aeq = np.array([[1.,1.,1.,1.],[0.,0.,1.,1.],[0.,1.,0.,1.]])
c = np.array([0.,0.,1.,0.])
max_err = 0.
for pc in np.linspace(0,1,41):
    for pr in np.linspace(0,1,41):
        eq = np.array([1.,pc,pr])
        lo = linprog(c, A_eq=Aeq, b_eq=eq, bounds=(0,None), method="highs")
        hi = linprog(-c, A_eq=Aeq, b_eq=eq, bounds=(0,None), method="highs")
        assert lo.success and hi.success
        max_err = max(max_err, abs(lo.fun-max(0,pc-pr)), abs(-hi.fun-min(pc,1-pr)))
assert max_err < 1e-12
for pc in np.linspace(0,1,201):
    for pr in np.linspace(0,1,201):
        exact = min(pc,1-pr) <= alpha+1e-12 and pr-pc >= eta-1e-12
        region = (pc <= alpha+1e-12 or pr >= 1-alpha-1e-12) and pr-pc >= eta-1e-12
        assert exact == region
worlds = [(0.4,0.2,0.0,0.4),(0.0,0.6,0.4,0.0)]
assert all(abs(w[2]+w[3]-.4)<1e-12 and abs(w[1]+w[3]-.6)<1e-12 for w in worlds)
print(json.dumps({"scope":"mathematics only, not new robotics data",
 "LP_problems":1681,"maximum_numerical_discrepancy":max_err,
 "exact_marginal_certification":"pr-pc>=.05 and (pc<=.10 or pr>=.90)",
 "equal_marginal_counterexample_harms":[w[2] for w in worlds]},indent=2))
