"""Fixed robot routing and parent-action calibration, with stop on abstention.

These adapters retain the existing DSRE/rule/tree semantics. Outcome fields are
absent from the runtime input contract; they enter only retrospective scoring.
"""

from itertools import combinations
from typing import Literal

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence

from .baselines import OutcomeTree
from .calibration import upper_bound
from .repair import ParentIndex, ParentRules, RepairQuery, RepairTable

METHODS = (
    "DSRE_strict",
    "B7",
    "DSRE_risk",
    "B7_risk",
    "B1_one_strict",
    "B1_two_strict",
    "CART1_strict",
    "CART2_strict",
    "CART2_pruned_strict",
    "CART1_beta10",
    "CART2_beta10",
    "B5_beta10",
    "B0_continue",
    "B0_recover",
    "full_signature_strict",
    "greedy_pure_rule",
    "policy_faithful",
)
ACTIONS = ("continue", "recover")


class PolicyInput(Evidence):
    task: Literal["PickCube-v1", "PushCube-v1"]
    values: tuple[bool | None, ...] = Field(min_length=6, max_length=7)
    full_values: tuple[bool | None, ...] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def consistent_information(self):
        expected = self.full_values[:6] + (
            (self.full_values[6],) if self.task == "PickCube-v1" else ()
        )
        if self.values != expected:
            raise ValueError("Shared predecision facts must agree across comparators")
        return self


def compact(rule, rules, status):
    result = rule.model_dump(mode="json") if hasattr(rule, "model_dump") else rule
    evidence = result.get("evidence", [])
    return {
        "action": result.get("action"),
        "evidence": evidence,
        "support": result.get("support", 0),
        "independent_parents": result.get("independent_parents", 0),
        "status": status if result.get("action") else "INSUFFICIENT",
    }


class OperationalRouter:
    """Load previously frozen trees and references; never fit on calibration/test."""

    def __init__(self, frozen):
        self.settings, self.cache, self.full = {}, {}, {}
        for task, budgets in frozen["tasks"].items():
            setting = budgets["1"]
            table = RepairTable.model_validate(setting["table"])
            rules = ParentRules(table, setting["parent_groups"], 2)
            trees = {}
            for depth, nodes in setting["trees"].items():
                tree = OutcomeTree.__new__(OutcomeTree)
                tree.rules, tree.nodes, tree.root = rules, nodes, 0
                trees[depth] = tree
            self.settings[task] = (
                setting,
                ParentIndex(table, setting["parent_groups"], 2),
                rules,
                trees,
            )
            if "full_table" in setting:
                full = RepairTable.model_validate(setting["full_table"])
                self.full[task] = ParentRules(full, setting["parent_groups"], 2)

    @staticmethod
    def _rule(rules, query, beta=0, cap=None):
        result = rules.select(query, beta, cap)
        value = compact(
            result,
            rules,
            "STRICT_FINITE_REFERENCE" if beta == 0 else "PROVISIONAL_UNCALIBRATED",
        )
        ids = set(result.matched_ids)
        value["independent_parents"] = rules.parent_count(
            [r for r in rules.rows if r.id in ids]
        )
        return value

    @staticmethod
    def _greedy(rules, query):
        candidates = []
        for action in ACTIONS:
            selected = []
            remaining = sorted(
                rules.known(query), key=lambda i: rules.table.scope.features[i]
            )
            while True:
                rows = rules.match(query, selected)
                if rules.parent_count(rows) < 2:
                    break
                errors = sum(action not in r.outcomes.acceptable() for r in rows)
                if errors == 0:
                    candidates.append(
                        (
                            len(selected),
                            -len(rows),
                            ACTIONS.index(action),
                            tuple(selected),
                            action,
                            rows,
                        )
                    )
                    break
                options = []
                for i in remaining:
                    child = rules.match(query, [*selected, i])
                    if rules.parent_count(child) >= 2:
                        bad = sum(action not in r.outcomes.acceptable() for r in child)
                        options.append(
                            (bad, -len(child), rules.table.scope.features[i], i)
                        )
                if not options or min(options)[0] >= errors:
                    break
                i = min(options)[-1]
                selected.append(i)
                remaining.remove(i)
        if not candidates:
            return {
                "action": None,
                "evidence": [],
                "support": 0,
                "independent_parents": 0,
                "status": "INSUFFICIENT",
            }
        _, _, _, selected, action, rows = min(candidates, key=lambda x: x[:4])
        return {
            "action": action,
            "evidence": [
                {"feature": rules.table.scope.features[i], "value": query.features[i]}
                for i in selected
            ],
            "support": len(rows),
            "independent_parents": rules.parent_count(rows),
            "status": "STRICT_FINITE_REFERENCE",
        }

    def route(self, packet: PolicyInput):
        key = (packet.task, packet.values, packet.full_values)
        if key in self.cache:
            return self.cache[key]
        _setting, index, rules, trees = self.settings[packet.task]
        if len(packet.values) != len(rules.table.scope.features):
            raise ValueError("Runtime vocabulary differs from frozen router")
        query = RepairQuery(scope=rules.table.scope, features=packet.values)
        diagnosis = index.diagnose(query)
        strict = compact(diagnosis, rules, "STRICT_FINITE_REFERENCE")
        strict["diagnosis"] = diagnosis.model_dump(mode="json")
        strict["status"] = diagnosis.status
        output = {"DSRE_strict": strict, "B7": self._rule(rules, query)}
        output["DSRE_risk"] = (
            strict if strict["action"] else self._rule(rules, query, 0.1, 2)
        )
        output["B7_risk"] = (
            output["B7"] if output["B7"]["action"] else self._rule(rules, query, 0.1, 2)
        )
        for name, cap in (("B1_one_strict", 1), ("B1_two_strict", 2)):
            output[name] = self._rule(rules, query, 0, cap)
        output["B5_beta10"] = self._rule(rules, query, 0.1)
        for name in ("CART1_strict", "CART2_strict", "CART1_beta10", "CART2_beta10"):
            result = trees[name[4]].predict(
                query, 0.9 if name.endswith("beta10") else 1
            )
            value = compact(
                result,
                rules,
                "PROVISIONAL_UNCALIBRATED"
                if name.endswith("beta10")
                else "STRICT_FINITE_REFERENCE",
            )
            rows = (
                rules.match(
                    query,
                    [
                        rules.table.scope.features.index(f.feature)
                        for f in result.evidence
                    ],
                )
                if result.action
                else []
            )
            value["independent_parents"] = rules.parent_count(rows)
            if result.action and value["independent_parents"] < 2:
                value = value | {
                    "action": None,
                    "evidence": [],
                    "status": "REFERENCE_INSUFFICIENT",
                }
            output[name] = value
        pruned = dict(output["CART2_strict"])
        if pruned["independent_parents"] < 10:
            pruned.update(action=None, evidence=[], status="REFERENCE_INSUFFICIENT")
        output["CART2_pruned_strict"] = pruned
        for action in ACTIONS:
            output["B0_" + action] = {
                "action": action,
                "evidence": [],
                "support": len(rules.rows),
                "independent_parents": rules.parent_count(rules.rows),
                "status": "FIXED_POLICY_UNCALIBRATED",
            }
        output["greedy_pure_rule"] = self._greedy(rules, query)
        full_rules = self.full.get(packet.task)
        if full_rules:
            fq = RepairQuery(scope=full_rules.table.scope, features=packet.full_values)
            known = full_rules.known(fq)
            matched = full_rules.match(fq, known)
            action = next(
                (
                    a
                    for a in ACTIONS
                    if full_rules.parent_count(matched) >= 2
                    and all(a in r.outcomes.acceptable() for r in matched)
                ),
                None,
            )
            output["full_signature_strict"] = {
                "action": action,
                "evidence": [
                    {
                        "feature": full_rules.table.scope.features[i],
                        "value": fq.features[i],
                    }
                    for i in known
                ]
                if action
                else [],
                "support": len(matched),
                "independent_parents": full_rules.parent_count(matched),
                "status": "STRICT_FINITE_REFERENCE" if action else "INSUFFICIENT",
            }
        else:
            output["full_signature_strict"] = output["B7"]
        # The frozen CART decision is the explained label. Its adequacy is NOT used
        # to create the explanation: reference labels come only from that tree.
        target = output["CART2_beta10"]["action"]
        output["policy_faithful"] = self._faithful(packet.task, query, target)
        assert output["B7"]["action"] == strict["action"]
        assert output["B7_risk"]["action"] == output["DSRE_risk"]["action"]
        self.cache[key] = output
        return output

    def _faithful(self, task, query, target):
        _, _, rules, trees = self.settings[task]
        if not hasattr(self, "policy_labels"):
            self.policy_labels = {}
        if task not in self.policy_labels:
            labels = {}
            for r in rules.rows:
                x = tuple(r.features)
                if x not in labels:
                    q = RepairQuery(scope=rules.table.scope, features=x)
                    leaf = trees["2"].predict(q, 0.9)
                    matched = (
                        rules.match(
                            q,
                            [
                                rules.table.scope.features.index(f.feature)
                                for f in leaf.evidence
                            ],
                        )
                        if leaf.action
                        else []
                    )
                    labels[x] = (
                        leaf.action if rules.parent_count(matched) >= 2 else None
                    )
            self.policy_labels[task] = labels
        if target:
            known = sorted(
                rules.known(query), key=lambda i: rules.table.scope.features[i]
            )
            for size in range(len(known) + 1):
                candidates = []
                for subset in combinations(known, size):
                    rows = rules.match(query, subset)
                    if rules.parent_count(rows) >= 2 and all(
                        self.policy_labels[task][tuple(r.features)] == target
                        for r in rows
                    ):
                        candidates.append((-len(rows), subset, rows))
                if candidates:
                    _, subset, rows = min(candidates, key=lambda x: x[:2])
                    return {
                        "action": target,
                        "evidence": [
                            {
                                "feature": rules.table.scope.features[i],
                                "value": query.features[i],
                            }
                            for i in subset
                        ],
                        "support": len(rows),
                        "independent_parents": rules.parent_count(rows),
                        "status": "POLICY_LABEL_FAITHFUL_ONLY",
                    }
        return {
            "action": None,
            "evidence": [],
            "support": 0,
            "independent_parents": 0,
            "status": "INSUFFICIENT",
        }


def calibrate_records(records, planned_complete=True):
    """Conservative any-error parent-action strata, global fixed-method family.

    The formal bound concerns an assigned parent with its two registered
    conditions, not arbitrary time points or checkpoint-weighted deployment.
    """
    result = {}
    delta = 0.05 / (4 * len(METHODS))
    for method in METHODS:
        for task in ("PickCube-v1", "PushCube-v1"):
            for action in ACTIONS:
                selected = [
                    r
                    for r in records
                    if r["method"] == method
                    and r["task"] == task
                    and r["action"] == action
                ]
                groups = {r["group"] for r in selected}
                errors = {r["group"] for r in selected if r["unacceptable"]}
                bound = upper_bound(len(errors), len(groups), delta)
                primary_bound = upper_bound(len(errors), len(groups), 0.0125)
                result[f"{method}|{task}|{action}"] = {
                    "assigned_parents": len(groups),
                    "error_parents": len(errors),
                    "assigned_checkpoints": len(selected),
                    "upper": bound,
                    "primary_four_stratum_upper": primary_bound,
                    "delta": delta,
                    "target": 0.1,
                    "enabled": planned_complete and bool(groups) and bound <= 0.1,
                    "status": "CERTIFIED_PARENT_ACTION_SCOPE"
                    if planned_complete and groups and bound <= 0.1
                    else "NOT_CERTIFIED",
                    "scope": "Fixed router; seed-parent any-error across two registered conditions conditional on assignment; IID-seed simulator scope only",
                }
    return result


def gated_action(method, task, proposed, calibration):
    if proposed is None:
        return None
    bound = calibration.get(f"{method}|{task}|{proposed}")
    return proposed if bound and bound["enabled"] else None
