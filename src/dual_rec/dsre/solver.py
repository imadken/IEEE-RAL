"""Exact small-vocabulary search and finite-table insufficiency witnesses."""

from itertools import combinations

from .schemas import (
    ACTIONS,
    Certificate,
    LiteralFact,
    Query,
    ReferenceTable,
    Witness,
    WitnessState,
)


class FiniteIndex:
    def __init__(self, table: ReferenceTable, minimum_support: int = 2):
        if minimum_support < 1:
            raise ValueError("Minimum support must be positive")
        self.table = table
        self.rows = sorted(table.rows, key=lambda r: r.id)
        self.minimum_support = minimum_support
        self.all_mask = (1 << len(self.rows)) - 1
        self.compatible = {}
        for i in range(len(table.scope.features)):
            for value in (False, True):
                self.compatible[i, value] = sum(
                    1 << j
                    for j, r in enumerate(self.rows)
                    if r.features[i] is None or r.features[i] == value
                )
        self.acceptable = {
            a: sum(
                1 << j
                for j, r in enumerate(self.rows)
                if r.qualified and a in r.outcomes.acceptable()
            )
            for a in ACTIONS
        }

    def known(self, query):
        return sorted(
            (i for i, value in enumerate(query.features) if value is not None),
            key=lambda i: self.table.scope.features[i],
        )

    def match(self, query, indices):
        mask = self.all_mask
        for i in indices:
            mask &= self.compatible[i, query.features[i]]
        return mask

    def ids(self, mask):
        return tuple(r.id for i, r in enumerate(self.rows) if mask & (1 << i))

    def valid(self, action, mask):
        return (
            mask.bit_count() >= self.minimum_support
            and mask & ~self.acceptable[action] == 0
        )

    def facts(self, query, indices):
        return tuple(
            LiteralFact(feature=self.table.scope.features[i], value=query.features[i])
            for i in indices
        )

    def state(self, i):
        row = self.rows[i]
        return WitnessState(
            id=row.id,
            features=row.features,
            outcomes=row.outcomes,
            acceptable=row.outcomes.acceptable() if row.qualified else (),
        )

    def first(self, mask):
        return (mask & -mask).bit_length() - 1

    def certificate(
        self, query, action, indices, evaluated, exactness="MINIMUM_CARDINALITY"
    ):
        mask = self.match(query, indices)
        assert self.valid(action, mask)
        witnesses = []
        for i in indices:
            expanded = self.match(query, [j for j in indices if j != i])
            bad = expanded & ~self.acceptable[action]
            if not bad:
                raise ValueError(
                    "Nonnecessary literal in a purported minimum/subset-minimal certificate"
                )
            witnesses.append(
                Witness(
                    kind="LITERAL_NECESSITY",
                    action=action,
                    removed=self.facts(query, [i])[0],
                    states=(self.state(self.first(bad)),),
                    reason="Removing this literal admits a reference state where this action is not qualified and adequate",
                )
            )
        return Certificate(
            status="SUFFICIENT",
            action=action,
            evidence=self.facts(query, indices),
            support=mask.bit_count(),
            matched_ids=self.ids(mask),
            scope=self.table.scope,
            witnesses=tuple(witnesses),
            exactness=exactness,
            subsets_evaluated=evaluated,
        )

    def insufficient(self, query, evaluated=0):
        if query.scope != self.table.scope:
            return Certificate(
                status="INSUFFICIENT",
                action=None,
                support=0,
                scope=self.table.scope,
                reasons=("SCOPE_MISMATCH",),
                exactness="NONE",
            )
        mask = self.match(query, self.known(query))
        indices = [i for i in range(len(self.rows)) if mask & (1 << i)]
        reasons, witnesses = [], []
        if mask.bit_count() < self.minimum_support:
            reasons.append("INSUFFICIENT_REFERENCE_SUPPORT")
            witnesses.append(
                Witness(
                    kind="SUPPORT",
                    reason=f"Most-specific available observations match {mask.bit_count()} rows, minimum {self.minimum_support}; no sufficient broader rule exists",
                )
            )
        unknown = [
            i
            for i in indices
            if not self.rows[i].qualified
            or self.rows[i].outcomes.continue_value is None
            or self.rows[i].outcomes.recover_value is None
        ]
        if unknown:
            reasons.append("OUTCOME_UNCERTAINTY")
            witnesses.append(
                Witness(
                    kind="UNKNOWN_OUTCOMES",
                    states=(self.state(unknown[0]),),
                    reason="An observationally compatible row lacks a complete qualified intervention pair",
                )
            )
        inadequate = [
            i
            for i in indices
            if self.rows[i].qualified
            and self.rows[i].outcomes.continue_value is False
            and self.rows[i].outcomes.recover_value is False
        ]
        if inadequate:
            reasons.append("INADEQUATE_REPERTOIRE")
            witnesses.append(
                Witness(
                    kind="INADEQUATE_ACTIONS",
                    states=(self.state(inadequate[0]),),
                    reason="Both measured interventions fail absolute adequacy; zero regret at a failure tie is insufficient",
                )
            )
        for left, right in combinations(indices, 2):
            a, b = set(self.state(left).acceptable), set(self.state(right).acceptable)
            if a and b and not a & b:
                reasons.append("OBSERVATION_AMBIGUITY")
                witnesses.append(
                    Witness(
                        kind="INCOMPATIBLE_ACTIONS",
                        states=(self.state(left), self.state(right)),
                        reason="Available observations cannot exclude states with disjoint acceptable-action sets",
                    )
                )
                break
        if any(v is None for v in query.features):
            reasons.append("MISSING_OBSERVATIONS")
        for action in ACTIONS:
            bad = mask & ~self.acceptable[action]
            if bad:
                witnesses.append(
                    Witness(
                        kind="UNEXCLUDABLE_BAD_ROW",
                        action=action,
                        states=(self.state(self.first(bad)),),
                        reason="No available known-opposite query literal excludes this action's bad row",
                    )
                )
        if not reasons:
            reasons.append("INSUFFICIENT_REFERENCE_SUPPORT")
        return Certificate(
            status="INSUFFICIENT",
            action=None,
            support=mask.bit_count(),
            matched_ids=self.ids(mask),
            scope=self.table.scope,
            reasons=tuple(reasons),
            witnesses=tuple(witnesses),
            exactness="NONE",
            subsets_evaluated=evaluated,
        )

    def solve(self, query: Query):
        if query.scope != self.table.scope:
            return self.insufficient(query)
        known, evaluated = self.known(query), 0
        for length in range(len(known) + 1):
            candidates = []
            for indices in combinations(known, length):
                mask = self.match(query, indices)
                evaluated += 1
                for order, action in enumerate(ACTIONS):
                    if self.valid(action, mask):
                        candidates.append(
                            (
                                (
                                    -mask.bit_count(),
                                    order,
                                    tuple(
                                        self.table.scope.features[i] for i in indices
                                    ),
                                ),
                                action,
                                indices,
                            )
                        )
            if candidates:
                _, action, indices = min(candidates)
                return self.certificate(query, action, indices, evaluated)
        return self.insufficient(query, evaluated)

    def greedy(self, query: Query):
        if query.scope != self.table.scope:
            return self.insufficient(query)
        known, candidates, evaluated = self.known(query), [], 0
        for order, action in enumerate(ACTIONS):
            selected = list(known)
            evaluated += 1
            if not self.valid(action, self.match(query, selected)):
                continue
            for i in known:
                trial = [j for j in selected if i != j]
                evaluated += 1
                if self.valid(action, self.match(query, trial)):
                    selected = trial
            mask = self.match(query, selected)
            candidates.append(
                (
                    (
                        len(selected),
                        -mask.bit_count(),
                        order,
                        tuple(self.table.scope.features[i] for i in selected),
                    ),
                    action,
                    selected,
                )
            )
        if candidates:
            _, action, indices = min(candidates)
            return self.certificate(query, action, indices, evaluated, "SUBSET_MINIMAL")
        return self.insufficient(query, evaluated)
