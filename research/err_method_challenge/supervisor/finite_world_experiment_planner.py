"""Independent finite-world reference for obligation-resolving experiment synthesis.

This is an analytical design checker, NOT a trained policy, field test, or
finite-sample population guarantee. All experiments here reveal their ideal
population signatures. Statistical estimation requires a separate procedure.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import isclose
import json


@dataclass(frozen=True)
class World:
    label: str
    outcome: bool  # Whether the named obligation is satisfied
    observations: tuple[tuple[str, tuple[float, ...]], ...]

    def signature(self, name: str) -> tuple[float, ...]:
        return tuple(round(float(x), 12) for x in dict(self.observations)[name])


def minimal_resolving_experiments(
    worlds: tuple[World, ...], costs: dict[str, int]
) -> dict:
    """Find minimum-cost experiment subset separating all opposite-verdict worlds.

    The experiments are noiseless ideal signatures of population distributions.
    Tie-break by experiment count and lexicographic names.
    """
    names = sorted(costs)
    required = {(i, j) for i in range(len(worlds)) for j in range(i+1, len(worlds))
                if worlds[i].outcome != worlds[j].outcome}
    distinguishable = {name: {ij for ij in required if worlds[ij[0]].signature(name) != worlds[ij[1]].signature(name)}
                       for name in names}
    if any(all(ij not in v for v in distinguishable.values()) for ij in required):
        return {"status": "impossible", "unresolved_pairs": [
            [worlds[i].label, worlds[j].label] for i, j in sorted(required)
            if all((i,j) not in v for v in distinguishable.values())]}
    candidates=[]
    for n in range(len(names)+1):
        for es in combinations(names,n):
            covered=set().union(*(distinguishable[e] for e in es)) if es else set()
            if covered==required:
                candidates.append((sum(costs[e] for e in es),len(es),es))
    cost,k,solution=min(candidates)
    return {"status":"resolvable", "cost":cost, "experiments":list(solution),
            "opposite_verdict_pairs":len(required)}


def joint_world(q00: float, q01: float, q10: float, q11: float) -> dict:
    assert isclose(q00+q01+q10+q11,1,abs_tol=1e-12)
    return {"p_continue":q10+q11,"p_recover":q01+q11,
            "binary_harm":q10,"gain":q01-q10,
            "paired_joint":(q00,q01,q10,q11)}


if __name__=="__main__":
    a=joint_world(.4,.2,0,.4)
    b=joint_world(0,.6,.4,0)
    assert isclose(a["p_continue"],b["p_continue"])
    assert isclose(a["p_recover"],b["p_recover"])
    assert isclose(a["gain"],b["gain"])
    assert a["binary_harm"]<=.10 and b["binary_harm"]>.10
    worlds=(
      World("low_harm",True,(("continue_log",(a["p_continue"],)),
           ("recover_log",(a["p_recover"],)), ("paired_trial",a["paired_joint"]))),
      World("high_harm",False,(("continue_log",(b["p_continue"],)),
           ("recover_log",(b["p_recover"],)), ("paired_trial",b["paired_joint"]))),
    )
    must_pair=minimal_resolving_experiments(worlds,{"continue_log":1,"recover_log":1,"paired_trial":2})
    assert must_pair["experiments"]==["paired_trial"]
    no_pair=minimal_resolving_experiments(worlds,{"continue_log":1,"recover_log":1})
    assert no_pair["status"]=="impossible"
    # Nontrivial weighted separator cover: only two cheap sources jointly suffice.
    multi=(
      World("T1",True,(("x",(0,)),("y",(0,)),("oracle",(0,)))),
      World("T2",True,(("x",(1,)),("y",(1,)),("oracle",(0,)))),
      World("F1",False,(("x",(1,)),("y",(0,)),("oracle",(1,)))),
      World("F2",False,(("x",(0,)),("y",(1,)),("oracle",(1,)))),
    )
    multi_plan=minimal_resolving_experiments(multi,{"x":1,"y":1,"oracle":4})
    assert multi_plan["experiments"]==["x","y"]
    assert multi_plan["cost"]==2
    print(json.dumps({"scope":"analytical finite-world illustration, not robot result",
                      "same_marginal_harm":[a["binary_harm"],b["binary_harm"]],
                      "marginals":{"continue":a["p_continue"],"recover":a["p_recover"]},
                      "single_action_logs":no_pair,
                      "including_paired_trial":must_pair,
                      "minimum_cost_two_information_sources":multi_plan},indent=2))
