"""Independent policy-tree enumeration and POMDP reduction, no planner imports."""

from fractions import Fraction
from functools import cache
from itertools import product


def index(raw):
    states = {s["state_id"]: s for s in raw["states"]}
    g = {
        s: {r["action_id"]: r for r in value["recoveries"]}
        for s, value in states.items()
    }
    probes = {
        p["probe_id"]: {**p, "table": {t["state_id"]: t for t in p["transitions"]}}
        for p in raw["probes"]
    }
    return states, g, probes


def all_policy_trees(raw, support=None, h=None, budget="ROOT"):
    """Enumerate all legal trees, including STOP and unsuccessful recoveries.

    There is no cost pruning, Bellman minimization or production branch helper.
    Only impossible observation branches are omitted.
    """
    support = tuple(sorted(raw["initial_support"])) if support is None else support
    h = raw["horizon"] if h is None else h
    if budget == "ROOT":
        budget = (
            None if raw["max_probe_cost"] is None else Fraction(raw["max_probe_cost"])
        )
    states, _, probes = index(raw)
    yield ("STOP", None, ())
    for action in sorted(raw["recovery_actions"]):
        yield ("RECOVER", action, ())
    if not h:
        return
    for name, p in sorted(probes.items()):
        c = Fraction(p["cost"])
        if budget is not None and c > budget:
            continue
        rows = [p["table"][s] for s in support]
        if not all(row["enabled"] for row in rows):
            continue
        if raw["require_physical_safety"] and any(
            not states[s]["physically_allowed"] for s in support
        ):
            continue
        if raw["require_physical_safety"] and any(
            not row["path_safe"] or not states[row["successor"]]["physically_allowed"]
            for row in rows
        ):
            continue
        groups = {}
        for row in rows:
            groups.setdefault(row["observation"], set()).add(row["successor"])
        options = [
            (
                obs,
                tuple(
                    all_policy_trees(
                        raw,
                        tuple(sorted(successors)),
                        h - 1,
                        None if budget is None else budget - c,
                    )
                ),
            )
            for obs, successors in sorted(groups.items())
        ]
        for children in product(*(trees for _, trees in options)):
            yield (
                "PROBE",
                name,
                tuple(
                    (entry[0], child)
                    for entry, child in zip(options, children, strict=True)
                ),
            )


def rollout(raw, tree, initial_state):
    states, g, probes = index(raw)
    s, remaining, spent = initial_state, raw["horizon"], Fraction(0)
    trace = []
    if raw["require_physical_safety"] and not states[s]["physically_allowed"]:
        return False, spent, trace
    while True:
        kind, name, children = tree
        if kind == "STOP":
            return False, spent, trace
        if kind == "RECOVER":
            r = g[s][name]
            return (
                r["task_success"]
                and (not raw["require_physical_safety"] or r["path_safe"]),
                spent,
                trace,
            )
        assert kind == "PROBE" and remaining > 0
        p = probes[name]
        row = p["table"][s]
        assert row["enabled"]
        if raw["require_physical_safety"]:
            assert row["path_safe"] and states[row["successor"]]["physically_allowed"]
        spent += Fraction(p["cost"])
        assert raw["max_probe_cost"] is None or spent <= Fraction(raw["max_probe_cost"])
        trace.append(
            {
                "probe": name,
                "before": s,
                "after": row["successor"],
                "observation": row["observation"],
            }
        )
        s = row["successor"]
        remaining -= 1
        tree = dict(children)[row["observation"]]


def exhaustive(raw):
    best, count = None, 0
    for tree in all_policy_trees(raw):
        count += 1
        outcomes = [rollout(raw, tree, s) for s in raw["initial_support"]]
        if all(r[0] for r in outcomes):
            cost = max(r[1] for r in outcomes)
            if best is None or cost < best[0]:
                best = (cost, tree)
    return best, count


def check_policy(raw, policy):
    """Check recorded supports independently, then replay every initial world."""
    _states, _, probes = index(raw)

    def convert(node, support):
        assert node["belief"] == sorted(support)
        if node["decision"] != "PROBE":
            assert not node["branches"]
            return node["decision"], node["action_id"], ()
        p = probes[node["action_id"]]
        groups = {}
        for s in support:
            row = p["table"][s]
            assert row["enabled"]
            groups.setdefault(row["observation"], set()).add(row["successor"])
        branches = {b["observation"]: b["child"] for b in node["branches"]}
        assert set(branches) == set(groups) and len(branches) == len(node["branches"])
        return (
            "PROBE",
            node["action_id"],
            tuple(
                (o, convert(branches[o], sorted(groups[o]))) for o in sorted(branches)
            ),
        )

    tree = convert(policy, sorted(raw["initial_support"]))
    return [rollout(raw, tree, s) for s in raw["initial_support"]]


def pomdp_value(raw):
    """Exact finite Bayesian Bellman control on explicit terminal transitions.

    Recover goes to GOAL/FAIL; STOP to HALT; unsafe paths to AVOID. GOAL,
    FAIL and HALT are accounting terminals, not restored physical states.
    Only the probability-one minimum worst-cost subproblem matches RPD.
    """
    states, g, probes = index(raw)
    safe = raw["require_physical_safety"]

    @cache
    def value(belief, h, budget):
        weights = dict(belief)
        if safe and any(not states[s]["physically_allowed"] for s in weights):
            return Fraction(0), None
        best_probability = Fraction(0)
        goal_costs = []
        for action in raw["recovery_actions"]:
            probability = sum(
                (
                    w
                    for s, w in belief
                    if g[s][action]["task_success"]
                    and (not safe or g[s][action]["path_safe"])
                ),
                Fraction(0),
            )
            best_probability = max(best_probability, probability)
            if probability == 1:
                goal_costs.append(Fraction(0))
        if h:
            for p in probes.values():
                cost = Fraction(p["cost"])
                if budget is not None and cost > budget:
                    continue
                if not all(p["table"][s]["enabled"] for s in weights):
                    continue
                if safe and any(
                    not p["table"][s]["path_safe"]
                    or not states[p["table"][s]["successor"]]["physically_allowed"]
                    for s in weights
                ):
                    continue
                groups = {}
                for s, w in belief:
                    row = p["table"][s]
                    branch = groups.setdefault(row["observation"], {})
                    target = row["successor"]
                    branch[target] = branch.get(target, Fraction(0)) + w
                probability = Fraction(0)
                branch_costs = []
                for branch in groups.values():
                    mass = sum(branch.values())
                    posterior = tuple(sorted((s, w / mass) for s, w in branch.items()))
                    p_goal, c_goal = value(
                        posterior, h - 1, None if budget is None else budget - cost
                    )
                    probability += mass * p_goal
                    branch_costs.append(c_goal)
                best_probability = max(best_probability, probability)
                if probability == 1:
                    assert all(c is not None for c in branch_costs)
                    goal_costs.append(cost + max(branch_costs))
        return best_probability, min(goal_costs) if goal_costs else None

    n = len(raw["initial_support"])
    return value(
        tuple(sorted((s, Fraction(1, n)) for s in raw["initial_support"])),
        raw["horizon"],
        None if raw["max_probe_cost"] is None else Fraction(raw["max_probe_cost"]),
    )


def verify_obstruction(raw, proof):
    """Check every no-policy branch without calling either optimization solver."""
    states, g, probes = index(raw)
    safe = raw["require_physical_safety"]

    def verify(p, support, horizon, budget):
        assert p["belief"] == sorted(support) and p["remaining_horizon"] == horizon
        assert (
            None if p["remaining_cost"] is None else Fraction(p["remaining_cost"])
        ) == budget
        if p["reason"] == "INITIAL_STATE_UNSAFE":
            assert safe and p["unsafe_states"]
            assert set(p["unsafe_states"]) == {
                s for s in support if not states[s]["physically_allowed"]
            }
            return
        assert not safe or all(states[s]["physically_allowed"] for s in support)
        examples = {e["action_id"]: e for e in p["recoveries"]}
        assert set(examples) == set(raw["recovery_actions"]) and len(examples) == len(
            p["recoveries"]
        )
        for action, e in examples.items():
            assert e["state_id"] in support
            r = g[e["state_id"]][action]
            assert (
                (not r["task_success"])
                if e["reason"] == "TASK_FAILURE"
                else (safe and not r["path_safe"])
            )
        if horizon == 0:
            assert p["reason"] == "NO_COMMON_RECOVERY_AT_HORIZON" and not p["probes"]
            return
        assert p["reason"] == "ALL_PROBES_BLOCKED"
        blocked = {e["probe_id"]: e for e in p["probes"]}
        assert set(blocked) == set(probes) and len(blocked) == len(p["probes"])
        for name, e in blocked.items():
            probe = probes[name]
            rows = probe["table"]
            cost = Fraction(probe["cost"])
            if e["reason"] == "DISABLED":
                assert e["state_id"] in support and not rows[e["state_id"]]["enabled"]
            elif e["reason"] == "PHYSICAL_PATH_UNSAFE":
                row = rows[e["state_id"]]
                assert safe and e["state_id"] in support and row["enabled"]
                assert (
                    not row["path_safe"]
                    or not states[row["successor"]]["physically_allowed"]
                )
            elif e["reason"] == "COST_BUDGET":
                assert budget is not None and cost > budget
            else:
                assert e["reason"] == "LOSING_BRANCH" and horizon > 0
                assert all(rows[s]["enabled"] for s in support)
                assert budget is None or cost <= budget
                assert not safe or all(
                    rows[s]["path_safe"]
                    and states[rows[s]["successor"]]["physically_allowed"]
                    for s in support
                )
                successors = {
                    rows[s]["successor"]
                    for s in support
                    if rows[s]["observation"] == e["observation"]
                }
                assert successors
                verify(
                    e["child"],
                    successors,
                    horizon - 1,
                    None if budget is None else budget - cost,
                )

    verify(
        proof,
        set(raw["initial_support"]),
        raw["horizon"],
        None if raw["max_probe_cost"] is None else Fraction(raw["max_probe_cost"]),
    )
