"""Prior independent rule/tree/witness checks, isolated from selector imports."""

from itertools import product

from dual_rec.dsre.repair_oracle import Oracle


def independent_tree_action(nodes, table, groups, x, target):
    """Read frozen splits, then recompute conservative leaf utility from raw rows."""
    node, path = 0, []
    while nodes[node]["feature"] is not None:
        feature = nodes[node]["feature"]
        if x[feature] is None:
            return None
        path.append(feature)
        node = nodes[node]["right"] if x[feature] else nodes[node]["left"]
    matched = [
        r for r in table["rows"] if all(r["features"][i] in (None, x[i]) for i in path)
    ]
    if len(matched) < 2 or len({groups[r["id"]] for r in matched}) < 2:
        return None
    means = [
        sum(r["outcomes"][a + "_value"] is True for r in matched) / len(matched)
        for a in ("continue", "recover")
    ]
    return (
        None
        if max(means) < target
        else ("recover" if means[1] > means[0] else "continue")
    )


class RouteAudit:
    def __init__(self, frozen):
        self.settings = {t: v["1"] for t, v in frozen["tasks"].items()}
        self.oracles = {
            t: Oracle(s["table"], s["parent_groups"]) for t, s in self.settings.items()
        }
        self.cache = {}

    def expected(self, task, values, method, robust):
        key = (task, tuple(values), method, robust)
        if key in self.cache:
            return self.cache[key]
        s = self.settings[task]
        o = self.oracles[task]
        query = {"scope": s["table"]["scope"], "features": values}
        if method in (
            "DSRE_strict",
            "B7",
            "DSRE_risk",
            "B7_risk",
            "B1_one_strict",
            "B1_two_strict",
            "B5_beta10",
        ):
            if method in ("DSRE_risk", "B7_risk"):
                answer = o.rule(query) or o.rule(query, 0.1, 2)
            elif method == "B5_beta10":
                answer = o.rule(query, 0.1)
            else:
                answer = o.rule(
                    query,
                    0,
                    1
                    if method == "B1_one_strict"
                    else 2
                    if method == "B1_two_strict"
                    else None,
                )
            value = answer["action"] if answer else None
        elif method in ("CART1_strict", "CART2_strict", "CART1_beta10", "CART2_beta10"):
            unknown = [i for i, v in enumerate(values) if v is None]
            completions = []
            for bits in (
                product((False, True), repeat=len(unknown)) if robust else [None]
            ):
                x = list(values)
                if bits is not None:
                    for i, v in zip(unknown, bits, strict=True):
                        x[i] = v
                completions.append(
                    independent_tree_action(
                        s["trees"][method[4]],
                        s["table"],
                        s["parent_groups"],
                        x,
                        0.9 if method.endswith("beta10") else 1,
                    )
                )
            value = completions[0] if len(set(completions)) == 1 else None
        elif method.startswith("B0_"):
            value = method.removeprefix("B0_")
        else:
            return "UNASSESSED"
        self.cache[key] = value
        return value


def verify_minimum(oracle, values, decision, risk=False):
    query = {"scope": oracle.table["scope"], "features": list(values)}
    expected = oracle.rule(query)
    if risk and expected is None:
        expected = oracle.rule(query, 0.1, 2)
    assert decision["action"] == (expected["action"] if expected else None)
    if expected:
        assert decision["evidence"] == expected["evidence"]
        if not risk:
            diagnosis = decision.get("diagnosis")
            if diagnosis:
                certificate = diagnosis["certificate"]
                assert set(certificate["matched_ids"]) == set(expected["matched_ids"])
                rows = {r["id"]: r for r in oracle.rows}
                names = oracle.table["scope"]["features"]
                for witness in certificate["witnesses"]:
                    assert witness["kind"] == "LITERAL_NECESSITY"
                    bad = rows[witness["states"][0]["id"]]
                    assert bad["outcomes"][expected["action"] + "_value"] is not True
                    for fact in expected["evidence"]:
                        if fact != witness["removed"]:
                            value = bad["features"][names.index(fact["feature"])]
                            assert value is None or value == fact["value"]
    elif "diagnosis" in decision:
        actual = {o["kind"] for o in decision["diagnosis"]["obstructions"]}
        assert actual == oracle.obstruction_types(query)
