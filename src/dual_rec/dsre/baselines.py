"""Outcome-trained small rules, four-category CART and policy-faithful rules."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from .schemas import ACTIONS, LiteralFact, Query, Recommendation, ReferenceTable


def compatible(row, query, selected):
    return all(
        row.features[i] is None or row.features[i] == query.features[i]
        for i in selected
    )


def category(row):
    if (
        not row.qualified
        or row.outcomes.continue_value is None
        or row.outcomes.recover_value is None
    ):
        return None
    return int(row.outcomes.continue_value) + 2 * int(row.outcomes.recover_value)


class OutcomeRules:
    def __init__(self, table: ReferenceTable, minimum_support=2):
        if minimum_support < 1:
            raise ValueError("Minimum support must be positive")
        self.table = table
        self.minimum_support = minimum_support
        self.rows = list(table.rows)
        self._policy = {}

    def known(self, query):
        return sorted(
            (i for i, value in enumerate(query.features) if value is not None),
            key=lambda i: self.table.scope.features[i],
        )

    def match(self, query, selected):
        return [r for r in self.rows if compatible(r, query, selected)]

    def facts(self, query, selected):
        return tuple(
            LiteralFact(feature=self.table.scope.features[i], value=query.features[i])
            for i in selected
        )

    def means(self, matched):
        if not matched:
            return (0.0, 0.0)
        return tuple(
            sum(
                int(getattr(r.outcomes, a + "_value") is True)
                if category(r) is not None
                else 0
                for r in matched
            )
            / len(matched)
            for a in ACTIONS
        )

    def recommendation(self, method, query, selected, action, matched, reason):
        means = self.means(matched)
        histogram = (
            tuple(
                sum(category(r) == c for r in matched) / len(matched) for c in range(4)
            )
            if matched
            else None
        )
        return Recommendation(
            method=method,
            action=action,
            evidence=self.facts(query, selected) if action else (),
            support=len(matched),
            reason=reason,
            mean_utility=means[ACTIONS.index(action)] if action else None,
            treatment_effect=means[1] - means[0],
            category_probabilities=histogram,
        )

    def abstain(self, method, reason):
        return Recommendation(method=method, action=None, support=0, reason=reason)

    def full(self, query: Query, target=0.5, method="B3_full"):
        if query.scope != self.table.scope:
            return self.abstain(method, "SCOPE_MISMATCH")
        selected = self.known(query)
        matched = self.match(query, selected)
        if len(matched) < self.minimum_support:
            return self.abstain(method, "INSUFFICIENT_REFERENCE_SUPPORT")
        means = self.means(matched)
        action = ACTIONS[int(means[1] > means[0])]
        if max(means) < target:
            return self.abstain(method, "CONDITIONAL_MEAN_BELOW_TARGET")
        return self.recommendation(
            method,
            query,
            selected,
            action,
            matched,
            "FULL_PATTERN_CONDITIONAL_OUTCOME_MODEL",
        )

    def minimum(
        self,
        query: Query,
        target=0.9,
        maximum_length=None,
        method="B5_mean",
        exact=False,
    ):
        if query.scope != self.table.scope:
            return self.abstain(method, "SCOPE_MISMATCH")
        known = self.known(query)
        maximum = (
            len(known) if maximum_length is None else min(maximum_length, len(known))
        )
        for length in range(maximum + 1):
            candidates = []
            for selected in combinations(known, length):
                matched = self.match(query, selected)
                if len(matched) < self.minimum_support:
                    continue
                means = self.means(matched)
                for order, action in enumerate(ACTIONS):
                    valid = (
                        all(
                            r.qualified and action in r.outcomes.acceptable()
                            for r in matched
                        )
                        if exact
                        else means[order] >= target
                    )
                    if valid:
                        candidates.append(
                            (
                                (
                                    -len(matched),
                                    order,
                                    tuple(
                                        self.table.scope.features[i] for i in selected
                                    ),
                                ),
                                action,
                                selected,
                                matched,
                            )
                        )
            if candidates:
                _, action, selected, matched = min(candidates, key=lambda c: c[0])
                return self.recommendation(
                    method,
                    query,
                    selected,
                    action,
                    matched,
                    "EXACT_OUTCOME_PURITY_RULE"
                    if exact
                    else "CONDITIONAL_MEAN_RULE_NOT_UNIVERSAL_CERTIFICATE",
                )
        return self.abstain(method, "NO_RULE_WITHIN_FIXED_SUPPORT_RISK_LENGTH_BUDGET")

    def policy(self, query, target=0.5):
        method = "B4_policy"
        if query.scope != self.table.scope:
            return self.abstain(method, "SCOPE_MISMATCH")
        wanted = self.full(query, target).action
        if wanted is None:
            return self.abstain(method, "FULL_MODEL_ABSTAINS")
        for row in self.rows:
            if row.features not in self._policy:
                self._policy[row.features] = self.full(
                    Query(scope=self.table.scope, features=row.features), target
                ).action
        known = self.known(query)
        for length in range(len(known) + 1):
            choices = []
            for selected in combinations(known, length):
                matched = self.match(query, selected)
                if len(matched) >= self.minimum_support and all(
                    self._policy[r.features] == wanted for r in matched
                ):
                    choices.append(
                        (
                            (
                                -len(matched),
                                tuple(self.table.scope.features[i] for i in selected),
                            ),
                            selected,
                            matched,
                        )
                    )
            if choices:
                _, selected, matched = min(choices, key=lambda c: c[0])
                return self.recommendation(
                    method,
                    query,
                    selected,
                    wanted,
                    matched,
                    "REFERENCE_MODEL_LABEL_FAITHFUL_NOT_INTERVENTION_ADEQUACY",
                )
        return self.abstain(method, "NO_POLICY_LABEL_CERTIFICATE")


class OutcomeTree:
    """Boolean CART-style Gini splits with four outcome-category targets.

    Unknown training values distribute fractional weight to both children. Leaf
    routing support/means use conservative compatible rows, never the split weights.
    """

    def __init__(self, rules: OutcomeRules, depth=3, pruning_alpha=0.0):
        self.rules = rules
        self.depth = depth
        self.pruning_alpha = pruning_alpha
        self.nodes = []
        weights = np.array([float(category(r) is not None) for r in rules.rows])
        self.total_weight = max(float(weights.sum()), 1.0)
        self.root = self._grow(
            weights, tuple(range(len(rules.table.scope.features))), depth
        )

    def _impurity(self, weights):
        counts = np.array(
            [
                sum(
                    float(w)
                    for r, w in zip(self.rules.rows, weights, strict=True)
                    if category(r) == c
                )
                for c in range(4)
            ]
        )
        total = float(counts.sum())
        return (1 - float(counts / total @ (counts / total))) * total if total else 0.0

    def _grow(self, weights, available, depth):
        impurity = self._impurity(weights)
        node = {
            "feature": None,
            "left": None,
            "right": None,
            "weight": float(weights.sum()),
            "impurity": impurity,
        }
        index = len(self.nodes)
        self.nodes.append(node)
        if not depth or impurity <= 1e-12:
            return index
        choices = []
        for feature in sorted(
            available, key=lambda i: self.rules.table.scope.features[i]
        ):
            values = [r.features[feature] for r in self.rules.rows]
            left_known = sum(
                w for w, v in zip(weights, values, strict=True) if v is False
            )
            right_known = sum(
                w for w, v in zip(weights, values, strict=True) if v is True
            )
            if left_known <= 0 or right_known <= 0:
                continue
            proportion = left_known / (left_known + right_known)
            left = np.array(
                [
                    w if v is False else 0 if v is True else w * proportion
                    for w, v in zip(weights, values, strict=True)
                ]
            )
            right = weights - left
            if (
                min(int((left > 0).sum()), int((right > 0).sum()))
                < self.rules.minimum_support
            ):
                continue
            cost = self._impurity(left) + self._impurity(right)
            choices.append(
                (cost, self.rules.table.scope.features[feature], feature, left, right)
            )
        if not choices:
            return index
        cost, _, feature, left, right = min(choices, key=lambda c: c[:2])
        if cost >= impurity - 1e-12:
            return index
        node["feature"] = feature
        remaining = tuple(i for i in available if i != feature)
        node["left"] = self._grow(left, remaining, depth - 1)
        node["right"] = self._grow(right, remaining, depth - 1)
        if self.pruning_alpha:
            leaves, subtree = self._leaf_cost(index)
            if (
                impurity / self.total_weight
                <= subtree / self.total_weight + self.pruning_alpha * (leaves - 1)
            ):
                node.update(feature=None, left=None, right=None)
        return index

    def _leaf_cost(self, index):
        node = self.nodes[index]
        if node["feature"] is None:
            return 1, node["impurity"]
        a, b = self._leaf_cost(node["left"]), self._leaf_cost(node["right"])
        return a[0] + b[0], a[1] + b[1]

    def predict(self, query, target=0.9, method="B2"):
        if query.scope != self.rules.table.scope:
            return self.rules.abstain(method, "SCOPE_MISMATCH")
        selected, index = [], self.root
        while self.nodes[index]["feature"] is not None:
            node = self.nodes[index]
            feature = node["feature"]
            if query.features[feature] is None:
                return self.rules.abstain(method, "MISSING_TREE_PATH_OBSERVATION")
            selected.append(feature)
            index = node["right"] if query.features[feature] else node["left"]
        selected.sort(key=lambda i: self.rules.table.scope.features[i])
        matched = self.rules.match(query, selected)
        means = self.rules.means(matched)
        if len(matched) < self.rules.minimum_support or max(means) < target:
            return self.rules.abstain(
                method, "TREE_LEAF_SUPPORT_OR_CONDITIONAL_MEAN_INSUFFICIENT"
            )
        action = ACTIONS[int(means[1] > means[0])]
        return self.rules.recommendation(
            method, query, selected, action, matched, "FOUR_CATEGORY_OUTCOME_TREE_PATH"
        )
