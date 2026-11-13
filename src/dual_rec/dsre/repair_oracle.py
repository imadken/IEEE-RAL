"""Independent integer-mask rule oracle and instrumentation checks, no solver import."""

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from math import log2
from random import Random


def action_set(row):
    if not row.get("qualified", True) or None in row["outcomes"].values():
        return set()
    return {a for a in ("continue", "recover") if row["outcomes"][a + "_value"]}


def features(row, selected, privileged=False):
    v = [*row["features"], *[row["optional_features"][i] for i in selected]]
    return v + row["privileged_features"][-2:] if privileged else v


def finite_mass(rows, selected, privileged=False):
    signatures = {tuple(features(r, selected, privileged)) for r in rows}
    total = 0
    for signature in signatures:
        same = [
            r for r in rows if tuple(features(r, selected, privileged)) == signature
        ]
        if any(all(a in action_set(r) for r in same) for a in ("continue", "recover")):
            total += len(same)
    return total


def entropy(rows, selected):
    partitions = defaultdict(list)
    for r in rows:
        partitions[tuple(features(r, selected))].append(r)
    value = 0
    for partition in partitions.values():
        distribution = Counter(tuple(sorted(action_set(r))) for r in partition)
        value += sum(
            -n / len(rows) * log2(n / len(partition)) for n in distribution.values()
        )
    return value


def select(rows, budget, method, available, seed):
    candidates = [
        subset
        for size in range(min(budget, len(available)) + 1)
        for subset in combinations(sorted(available), size)
    ]
    if method == "exact_coverage":
        scored = [(-finite_mass(rows, c), len(c), c) for c in candidates]
        return min(scored)[2]
    if method in ("canonical", "random"):
        order = sorted(available)
        if method == "random":
            order = Random(seed).sample(order, len(order))
        return tuple(sorted(order[:budget]))
    selected = ()
    score = (
        (lambda j: finite_mass(rows, j))
        if method == "greedy_coverage"
        else (lambda j: -entropy(rows, j))
    )
    tolerance = 1e-12 if method == "greedy_entropy" else 0
    for _ in range(budget):
        options = [
            tuple(sorted((*selected, i))) for i in available if i not in selected
        ]
        if not options:
            break
        scores = {j: score(j) for j in options}
        best = max(scores.values())
        winner = min(j for j in options if scores[j] >= best - tolerance)
        if scores[winner] <= score(selected) + tolerance:
            break
        selected = winner
    return selected


class Oracle:
    def __init__(self, table, parent_groups):
        self.table, self.rows, self.groups = table, table["rows"], parent_groups
        self.all_mask = (1 << len(self.rows)) - 1
        self.masks = {}
        for i in range(len(table["scope"]["features"])):
            for value in (False, True):
                mask = 0
                for j, r in enumerate(self.rows):
                    if r["features"][i] is None or r["features"][i] == value:
                        mask |= 1 << j
                self.masks[i, value] = mask
        self.bad = {
            a: sum(1 << i for i, r in enumerate(self.rows) if a not in action_set(r))
            for a in ("continue", "recover")
        }
        self.support_cache = {}

    def indices(self, mask):
        result = []
        while mask:
            low = mask & -mask
            result.append(low.bit_length() - 1)
            mask ^= low
        return result

    def parents(self, mask):
        if mask not in self.support_cache:
            self.support_cache[mask] = len(
                {self.groups[self.rows[i]["id"]] for i in self.indices(mask)}
            )
        return self.support_cache[mask]

    def match(self, x, selected):
        mask = self.all_mask
        for i in selected:
            mask &= self.masks[i, x[i]]
        return mask

    def rule(self, query, beta=0, maximum_length=None):
        if query["scope"] != self.table["scope"]:
            return None
        x = query["features"]
        names = self.table["scope"]["features"]
        known = sorted(
            [i for i, v in enumerate(x) if v is not None], key=lambda i: names[i]
        )
        maximum = (
            len(known) if maximum_length is None else min(maximum_length, len(known))
        )
        for length in range(maximum + 1):
            candidates = []
            for selected in combinations(known, length):
                mask = self.match(x, selected)
                if self.parents(mask) < 2:
                    continue
                ids = self.indices(mask)
                if any(
                    not self.rows[i].get("qualified", True)
                    or None in self.rows[i]["outcomes"].values()
                    for i in ids
                ):
                    continue
                n = mask.bit_count()
                for order, action in enumerate(("continue", "recover")):
                    k = (mask & self.bad[action]).bit_count()
                    ratio = Fraction(k, n)
                    if ratio <= Fraction(str(beta)):
                        key = (ratio, -n, order, tuple(names[i] for i in selected))
                        candidates.append((key, action, selected, mask, k))
            if candidates:
                _, action, selected, mask, k = min(candidates, key=lambda c: c[0])
                return {
                    "action": action,
                    "evidence": [
                        {"feature": names[i], "value": x[i]} for i in selected
                    ],
                    "support": mask.bit_count(),
                    "matched_ids": sorted(
                        self.rows[i]["id"] for i in self.indices(mask)
                    ),
                    "independent_parents": self.parents(mask),
                    "unacceptable": k,
                }
        return None

    def obstruction_types(self, query):
        if query["scope"] != self.table["scope"]:
            return {"REFERENCE_INSUFFICIENT"}
        x = query["features"]
        mask = self.match(x, [i for i, v in enumerate(x) if v is not None])
        rows = [self.rows[i] for i in self.indices(mask)]
        result = set()
        if any(
            r.get("qualified", True)
            and r["outcomes"] == {"continue_value": False, "recover_value": False}
            for r in rows
        ):
            result.add("REPERTOIRE_INADEQUATE")
        if any(action_set(r) == {"continue"} for r in rows) and any(
            action_set(r) == {"recover"} for r in rows
        ):
            result.add("OBSERVATIONAL_AMBIGUITY")
        if self.parents(mask) < 2 or any(
            None in r["outcomes"].values() or not r.get("qualified", True) for r in rows
        ):
            result.add("REFERENCE_INSUFFICIENT")
        return result

    def verify(self, query, result):
        expected = self.rule(query)
        assert result["action"] == (expected["action"] if expected else None)
        if expected:
            for field in ("action", "evidence", "support", "independent_parents"):
                assert result[field] == expected[field], field
            assert result["status"] == "STRICT_FINITE_REFERENCE"
        else:
            kinds = self.obstruction_types(query)
            assert {o["kind"] for o in result["obstructions"]} == kinds
            assert result["status"] == (
                "REFERENCE_INSUFFICIENT"
                if "REFERENCE_INSUFFICIENT" in kinds
                else "INSUFFICIENT"
            )
        rows = {r["id"]: r for r in self.rows}
        names = self.table["scope"]["features"]
        for witness in result["certificate"]["witnesses"]:
            if witness["kind"] == "LITERAL_NECESSITY":
                remaining = [f for f in result["evidence"] if f != witness["removed"]]
                for state in witness["states"]:
                    r = rows[state["id"]]
                    assert result["action"] not in action_set(r)
                    assert all(
                        r["features"][names.index(f["feature"])] in (None, f["value"])
                        for f in remaining
                    )
        for obstruction in result["obstructions"]:
            states = [rows[id] for id in obstruction["ids"]]
            for r in states:
                assert all(
                    v is None or r["features"][i] in (None, v)
                    for i, v in enumerate(query["features"])
                )
            if obstruction["kind"] == "REPERTOIRE_INADEQUATE":
                assert states and states[0]["outcomes"] == {
                    "continue_value": False,
                    "recover_value": False,
                }
            if obstruction["kind"] == "OBSERVATIONAL_AMBIGUITY":
                assert (
                    len(states) == 2
                    and action_set(states[0])
                    and action_set(states[1])
                    and not action_set(states[0]) & action_set(states[1])
                )
        return True
