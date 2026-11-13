"""Independent exhaustive/difference-set oracle; no solver/schema imports."""

from itertools import combinations


def acceptable(row, action):
    out = row["outcomes"]
    if (
        not row["qualified"]
        or out["continue_value"] is None
        or out["recover_value"] is None
    ):
        return False
    values = (int(out["continue_value"]), int(out["recover_value"]))
    value = values[("continue", "recover").index(action)]
    return value >= 1 and max(values) - value <= 0


def enumerate_oracle(table, query, minimum_support=2, hitting_sets=False):
    if query["scope"] != table["scope"]:
        return None
    names, x = table["scope"]["features"], query["features"]
    known = sorted(
        (i for i, value in enumerate(x) if value is not None), key=lambda i: names[i]
    )
    options = []
    for count in range(len(known) + 1):
        for selected in combinations(known, count):
            matched = [
                r
                for r in table["rows"]
                if all(
                    r["features"][i] is None or r["features"][i] == x[i]
                    for i in selected
                )
            ]
            if len(matched) < minimum_support:
                continue
            for order, action in enumerate(("continue", "recover")):
                if hitting_sets:
                    differences = [
                        {
                            i
                            for i in known
                            if r["features"][i] is not None and r["features"][i] != x[i]
                        }
                        for r in table["rows"]
                        if not acceptable(r, action)
                    ]
                    valid = all(
                        set(selected) & difference for difference in differences
                    )
                else:
                    valid = all(acceptable(r, action) for r in matched)
                if valid:
                    rank = (
                        count,
                        -len(matched),
                        order,
                        tuple(names[i] for i in selected),
                    )
                    options.append(
                        (
                            rank,
                            {
                                "action": action,
                                "evidence": [
                                    {"feature": names[i], "value": x[i]}
                                    for i in selected
                                ],
                                "support": len(matched),
                                "matched_ids": sorted(r["id"] for r in matched),
                            },
                        )
                    )
    return min(options, key=lambda v: v[0])[1] if options else None


def verify_certificate(table, query, certificate, minimum_support=2):
    expected = enumerate_oracle(table, query, minimum_support)
    hit = enumerate_oracle(table, query, minimum_support, True)
    assert hit == expected
    if expected is None:
        assert certificate["action"] is None
    else:
        for field in ["action", "evidence", "support", "matched_ids"]:
            assert certificate[field] == expected[field], field
    by_id = {r["id"]: r for r in table["rows"]}
    names = table["scope"]["features"]
    necessary = []
    for witness in certificate["witnesses"]:
        states = [by_id[s["id"]] for s in witness["states"]]
        if witness["kind"] == "LITERAL_NECESSITY":
            removed = witness["removed"]
            remaining = [f for f in certificate["evidence"] if f != removed]
            assert all(
                all(
                    r["features"][names.index(f["feature"])] in (None, f["value"])
                    for f in remaining
                )
                for r in states
            )
            assert states and not acceptable(states[0], certificate["action"])
            necessary.append(removed)
        elif witness["kind"] == "INCOMPATIBLE_ACTIONS":
            sets = [
                {a for a in ("continue", "recover") if acceptable(r, a)} for r in states
            ]
            assert len(sets) == 2 and sets[0] and sets[1] and not sets[0] & sets[1]
        elif witness["kind"] == "INADEQUATE_ACTIONS":
            assert states and states[0]["outcomes"] == {
                "continue_value": False,
                "recover_value": False,
            }
        elif witness["kind"] == "UNEXCLUDABLE_BAD_ROW":
            assert states and not acceptable(states[0], witness["action"])
            assert all(
                v is None or states[0]["features"][i] in (None, v)
                for i, v in enumerate(query["features"])
            )
    if expected:
        assert sorted(necessary, key=lambda f: f["feature"]) == certificate["evidence"]
    return True
