"""Exact discovery-only Boolean CART2 partition shared by all selectors."""

from itertools import product

from .schema import OneAction, Partition


def assignments(d):
    return tuple(product((False, True), repeat=d))


def cell(tree, x):
    root, left, right = tree
    if root < 0:
        return 0
    side = int(x[root])
    child = (left, right)[side]
    return 2 * side + (int(x[child]) if child >= 0 else 0)


def route(p: Partition, x):
    if len(x) != len(p.vocabulary) or any(v is None for v in x):
        return None
    index = sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))
    return p.cells[index]


def fit(logs: list[OneAction], vocabulary: tuple[str, ...]) -> Partition:
    d = len(vocabulary)
    if not 1 <= d <= 6 or any(len(r.x) != d for r in logs):
        raise ValueError("Declared observation vocabulary mismatch")
    if len({r.parent_id for r in logs}) != len(logs):
        raise ValueError("Independent parent unit required")
    usable = [r for r in logs if all(v is not None for v in r.x)]
    trees = [(-1, -1, -1)]
    for root in range(d):
        rest = [-1] + [i for i in range(d) if i != root]
        trees.extend((root, left, right) for left, right in product(rest, repeat=2))
    ranked = []
    for tree in trees:
        raw = [cell(tree, x) for x in assignments(d)]
        ids = {c: i for i, c in enumerate(sorted(set(raw)))}
        counts = {(c, a): [0, 0] for c in ids for a in ("c", "r")}
        for r in usable:
            count = counts[cell(tree, r.x), r.action]
            count[0] += 1
            count[1] += r.y
        if tree[0] >= 0 and any(n < 8 for n, _ in counts.values()):
            continue
        sse = sum(k - k * k / n for n, k in counts.values() if n)
        ranked.append(((round(sse, 12), len(ids), tree), tuple(ids[c] for c in raw)))
    score, cells = min(ranked, key=lambda item: item[0])
    return Partition(
        vocabulary=vocabulary,
        cells=cells,
        tree=score[2],
        discovery_parents=tuple(sorted(r.parent_id for r in logs)),
    )
