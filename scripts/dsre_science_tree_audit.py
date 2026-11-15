"""Check robust CART is not weakened by unanimous fixed-action completions."""

import argparse
import itertools
import json
import time
from pathlib import Path

from dsre_followup_batch import atomic, read

from dual_rec.dsre.operational import OperationalRouter
from dual_rec.dsre.repair import RepairQuery


def audit(root):
    router = OperationalRouter(read(root / "frozen_routers.json"))
    results = {}
    for task, (_setting, _index, rules, trees) in router.settings.items():
        n = len(rules.table.scope.features)
        for depth, tree in trees.items():
            for target in (1, 0.9):
                points = {}
                leaves = {}
                for bits in itertools.product((False, True), repeat=n):
                    q = RepairQuery(scope=rules.table.scope, features=bits)
                    leaf = tree.predict(q, 0)
                    selected = [
                        rules.table.scope.features.index(f.feature)
                        for f in leaf.evidence
                    ]
                    rows = rules.match(q, selected)
                    means = rules.means(rows)
                    allowed = {
                        a
                        for i, a in enumerate(("continue", "recover"))
                        if rules.parent_count(rows) >= 2 and means[i] >= target
                    }
                    predicted = tree.predict(q, target).action
                    points[bits] = (allowed, predicted)
                    leaves[str([(f.feature, f.value) for f in leaf.evidence])] = {
                        "means": means,
                        "parents": rules.parent_count(rows),
                        "eligible": sorted(allowed),
                    }
                count = 0
                nonempty = 0
                for mask in itertools.product((False, True, None), repeat=n):
                    completed = [
                        v
                        for bits, v in points.items()
                        if all(
                            m is None or m == b for m, b in zip(mask, bits, strict=True)
                        )
                    ]
                    common = set.intersection(*(v[0] for v in completed))
                    actions = {v[1] for v in completed}
                    chosen = next(iter(actions)) if len(actions) == 1 else None
                    assert (chosen is None) == (not common), (
                        task,
                        depth,
                        target,
                        mask,
                        chosen,
                        common,
                    )
                    if chosen:
                        assert chosen in common
                        nonempty += 1
                    count += 1
                results[f"{task}|depth{depth}|target{target}"] = {
                    "masks_exhaustively_checked": count,
                    "nonempty_common_action_masks": nonempty,
                    "unanimous_frozen_action_equals_common_eligible_action": True,
                    "leaves": leaves,
                }
    result = {
        "passed": True,
        "models": results,
        "scope": "All ternary masks of each frozen6/7-fact interface, under unchanged two-parent support and targets1/.9. This equality is model-specific, not a theorem for arbitrary trees.",
        "epoch": time.time(),
    }
    atomic(root / "robust_tree_fairness_audit.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "ternary_masks": sum(
                    v["masks_exhaustively_checked"] for v in results.values()
                ),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a = p.parse_args()
    audit(a.root)
