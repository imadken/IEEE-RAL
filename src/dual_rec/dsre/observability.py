"""Elementary finite-table observability profiles, separate from deployment risk."""

from collections import Counter, defaultdict
from itertools import combinations

from .baselines import compatible
from .schemas import ACTIONS, Query, ReferenceTable


def good(row):
    return set(row.outcomes.acceptable()) if row.qualified else set()


def intersection(rows):
    result = set(ACTIONS)
    for row in rows:
        result &= good(row)
    return tuple(a for a in ACTIONS if a in result) if rows else ()


def classify(rows):
    inadequate = [
        r.id
        for r in rows
        if r.qualified
        and r.outcomes.continue_value is False
        and r.outcomes.recover_value is False
    ]
    unknown = [
        r.id
        for r in rows
        if not r.qualified
        or any(v is None for v in (r.outcomes.continue_value, r.outcomes.recover_value))
    ]
    left = next((r for r in rows if good(r) == {"continue"}), None)
    right = next((r for r in rows if good(r) == {"recover"}), None)
    return {
        "inadequate": bool(inadequate),
        "action_ambiguous": left is not None and right is not None,
        "unknown_outcomes": bool(unknown),
        "inadequate_witness": inadequate[:1],
        "ambiguity_witness": [left.id, right.id] if left and right else [],
        "unknown_witness": unknown[:1],
    }


def outcome_category(row):
    if not row.qualified or any(
        v is None for v in (row.outcomes.continue_value, row.outcomes.recover_value)
    ):
        return "unknown"
    adequate = good(row)
    if len(adequate) == 2:
        return "both"
    return next(iter(adequate)) if adequate else "neither"


def group_has(group, kind, label):
    if label == "adequate":
        return bool(group[kind + "_good"])
    causes = group[kind + "_causes"]
    if label == "overlap":
        return causes["inadequate"] and causes["action_ambiguous"]
    return causes[label]


def profile(table: ReferenceTable, minimum_support=2):
    if minimum_support < 1:
        raise ValueError("Minimum support must be positive")
    groups = defaultdict(list)
    for row in sorted(table.rows, key=lambda r: r.id):
        groups[row.features].append(row)
    details = []
    for signature, equal in sorted(groups.items(), key=lambda item: str(item[0])):
        known = tuple(i for i, v in enumerate(signature) if v is not None)
        query = Query(scope=table.scope, features=signature)
        matched = [r for r in table.rows if compatible(r, query, known)]
        equal_good, compatible_good = intersection(equal), intersection(matched)
        # A broader pure rule can satisfy support even when the full pattern is sparse.
        achievable = any(
            len(part := [r for r in table.rows if compatible(r, query, subset)])
            >= minimum_support
            and bool(intersection(part))
            for length in range(len(known) + 1)
            for subset in combinations(known, length)
        )
        counts = Counter(outcome_category(r) for r in equal)
        scores = {a: sum(a in good(r) for r in equal) for a in ACTIONS}
        best = max(ACTIONS, key=lambda a: scores[a])
        majority = min(
            counts,
            key=lambda c: (
                -counts[c],
                ("continue", "recover", "both", "neither", "unknown").index(c),
            ),
        )
        naive_action = {
            "continue": "continue",
            "recover": "recover",
            "both": "continue",
        }.get(majority)
        non_neither = [r for r in equal if good(r)]
        details.append(
            {
                "signature": signature,
                "mass": len(equal),
                "ids": [r.id for r in equal],
                "categories": dict(counts),
                "equal_good": equal_good,
                "compatible_good": compatible_good,
                "compatible_support": len(matched),
                "equal_causes": classify(equal),
                "compatible_causes": classify(matched),
                "known_query_literals": len(known),
                "full_pattern_support_below_minimum": len(matched) < minimum_support,
                "strict_supported_rule_exists": achievable,
                "ignoring_neither_false_purity": not equal_good
                and bool(intersection(non_neither)),
                "best_nonuniversal": {
                    "action": best,
                    "adequate": scores[best],
                    "unacceptable": len(equal) - scores[best],
                    "recommended": len(equal),
                    "status": "HINDSIGHT_DIAGNOSTIC_ONLY",
                },
                "naive_category_majority": {
                    "category": majority,
                    "action": naive_action,
                    "recommended": len(equal) if naive_action else 0,
                    "unacceptable": len(equal) - scores[naive_action]
                    if naive_action
                    else 0,
                },
            }
        )
    summary = {
        "groups": len(details),
        "rows": len(table.rows),
        "minimum_support": minimum_support,
    }
    for kind in ("equal", "compatible"):
        for label in (
            "adequate",
            "inadequate",
            "action_ambiguous",
            "overlap",
            "unknown_outcomes",
        ):
            chosen = [g for g in details if group_has(g, kind, label)]
            summary[kind + "_" + label] = {
                "groups": len(chosen),
                "mass": sum(g["mass"] for g in chosen),
            }
        mass = summary[kind + "_adequate"]["mass"]
        summary[kind + "_ceiling"] = mass / len(table.rows) if table.rows else None
    summary["supported_grammar_mass"] = sum(
        g["mass"] for g in details if g["strict_supported_rule_exists"]
    )
    for label in ("best_nonuniversal", "naive_category_majority"):
        summary[label] = {
            key: sum(g[label][key] for g in details)
            for key in ("recommended", "unacceptable")
        }
    summary["ignoring_neither_false_purity_mass"] = sum(
        g["mass"] for g in details if g["ignoring_neither_false_purity"]
    )
    return {"summary": summary, "signatures": details}
