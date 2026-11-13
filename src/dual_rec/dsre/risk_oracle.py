"""Dictionary-only independent enumerators and high precision binomial arithmetic.

No imports from the certificate solver, risk router, baseline or calibration code.
"""

import math
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations


def good(row):
    values = row["outcomes"]
    if not row.get("qualified", True) or None in values.values():
        return set()
    return {a for a in ("continue", "recover") if values[a + "_value"]}


def matches(row, x, indices):
    for index in indices:
        if row["features"][index] is not None and row["features"][index] != x[index]:
            return False
    return True


def rule(table, query, beta=0.1, strict=False, maximum_length=None, minimum=2):
    if query["scope"] != table["scope"]:
        return None
    names = table["scope"]["features"]
    known = [i for i, v in enumerate(query["features"]) if v is not None]
    candidates = []
    for count in range(len(known) + 1):
        if maximum_length is not None and count > maximum_length:
            continue
        for indices in combinations(known, count):
            matched = [
                r for r in table["rows"] if matches(r, query["features"], indices)
            ]
            if len(matched) < minimum:
                continue
            if any(
                not r.get("qualified", True) or None in r["outcomes"].values()
                for r in matched
            ):
                continue
            for order, action in enumerate(("continue", "recover")):
                errors = sum(action not in good(r) for r in matched)
                if (
                    errors
                    and strict
                    or Fraction(errors, len(matched)) > Fraction(str(beta))
                ):
                    continue
                evidence = sorted(
                    [
                        {"feature": names[i], "value": query["features"][i]}
                        for i in indices
                    ],
                    key=lambda f: f["feature"],
                )
                key = (
                    count,
                    *(() if strict else (Fraction(errors, len(matched)),)),
                    -len(matched),
                    order,
                    tuple(f["feature"] for f in evidence),
                )
                candidates.append(
                    (
                        key,
                        {
                            "action": action,
                            "evidence": evidence,
                            "support": len(matched),
                            "matched_ids": sorted(r["id"] for r in matched),
                            "unacceptable": errors,
                        },
                    )
                )
    return min(candidates, key=lambda c: c[0])[1] if candidates else None


def exact_binomial_upper(k, n, delta):
    if not 0 <= k <= n or not 0 < delta < 1:
        raise ValueError("Invalid binomial arguments")
    if not n or k == n:
        return 1.0
    with localcontext() as context:
        context.prec = 70
        target = Decimal(str(delta))
        low, high = Decimal(0), Decimal(1)
        for _ in range(240):
            probability = (low + high) / 2
            cdf = sum(
                Decimal(math.comb(n, i)) * probability**i * (1 - probability) ** (n - i)
                for i in range(k + 1)
            )
            if cdf > target:
                low = probability
            else:
                high = probability
        return float((low + high) / 2)


def ceiling(table):
    """Exhaustively test every fixed action on each exact and compatible signature."""
    details = []
    signatures = sorted({tuple(r["features"]) for r in table["rows"]}, key=str)
    for signature in signatures:
        equal = [r for r in table["rows"] if tuple(r["features"]) == signature]
        known = [i for i, v in enumerate(signature) if v is not None]
        compatible = [r for r in table["rows"] if matches(r, signature, known)]
        record = {"signature": list(signature), "mass": len(equal)}
        for label, rows in (("equal", equal), ("compatible", compatible)):
            feasible = []
            for action in ("continue", "recover"):
                if rows and all(action in good(row) for row in rows):
                    feasible.append(action)
            inadequate = any(
                r.get("qualified", True)
                and all(v is False for v in r["outcomes"].values())
                for r in rows
            )
            ambiguous = any(good(r) == {"continue"} for r in rows) and any(
                good(r) == {"recover"} for r in rows
            )
            record[label] = {
                "good": feasible,
                "inadequate": inadequate,
                "action_ambiguous": ambiguous,
                "overlap": inadequate and ambiguous,
                "unknown_outcomes": any(
                    not r.get("qualified", True) or None in r["outcomes"].values()
                    for r in rows
                ),
            }
        details.append(record)
    return details
