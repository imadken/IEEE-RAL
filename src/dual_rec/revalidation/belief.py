"""Finite joint state tracking with a persistent observation-error channel.

All transition and sensor probabilities are supplied runtime assumptions. The
model enumerates its hypotheses without consulting evaluator state or events.
This is standard Bayesian tracking and finite decision-tree enumeration.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from functools import cached_property, lru_cache
from math import exp, expm1, fsum, log, log1p
from types import MappingProxyType

from dual_rec.monitoring.semantics import Action, Lit, Model, regress

from .contracts import Reading, RevalidationContext

MAX_HYPOTHESES = 100_000


class BeliefLimit(ValueError):
    """The full joint model exceeds a declared bound; no truncation occurred."""


class InconsistentBelief(ValueError):
    """The supplied model gives the evidence/known success zero probability."""


class OracleLimit(BeliefLimit):
    """Exact finite decision enumeration is outside its reduced-state bounds."""


@dataclass(frozen=True)
class Hypothesis:
    before: int
    current: int
    weight: float
    log_weight: float = float("-inf")

    def __post_init__(self):
        if self.log_weight == float("-inf") and self.weight > 0:
            object.__setattr__(self, "log_weight", log(self.weight))


@dataclass(frozen=True)
class _ActionBits:
    positive: int
    negative: int
    add: int
    delete: int

    def enabled(self, state: int) -> bool:
        return state & self.positive == self.positive and not state & self.negative

    def apply(self, state: int) -> int:
        return (state & ~self.delete) | self.add


@dataclass(frozen=True, eq=False)
class _ActionLibrary:
    operators: tuple[_ActionBits, ...]


@lru_cache(maxsize=128)
def _compile_library(
    atoms: tuple[str, ...], actions: tuple[Action, ...]
) -> _ActionLibrary:
    indices = {atom: index for index, atom in enumerate(atoms)}

    def bits(values):
        result = 0
        for atom in values:
            if atom not in indices:
                raise ValueError("Action refers to an undeclared atom")
            result |= 1 << indices[atom]
        return result

    return _ActionLibrary(
        tuple(
            _ActionBits(
                bits(lit.atom for lit in action.pre if lit.positive),
                bits(lit.atom for lit in action.pre if not lit.positive),
                bits(action.add),
                bits(action.delete),
            )
            for action in actions
        )
    )


@lru_cache(maxsize=4096)
def _kernel(
    state: int,
    library: _ActionLibrary,
    fixed_positive: int,
    fixed_negative: int,
    hazard: float,
    steps: int,
) -> tuple[tuple[int, float], ...]:
    probability = _event_probability(hazard, steps)
    successors = []
    if probability:
        for action in library.operators:
            if action.enabled(state):
                successor = action.apply(state)
                if successor != state:
                    if (
                        successor & fixed_positive != fixed_positive
                        or successor & fixed_negative
                    ):
                        raise InconsistentBelief(
                            "Transition changes a fixed model proposition"
                        )
                    successors.append(successor)
    if not successors:
        return ((state, 1.0),)
    mass = defaultdict(float)
    if probability < 1:
        mass[state] = 1 - probability
    for successor in successors:
        mass[successor] += probability / len(successors)
    return tuple(sorted(mass.items()))


@lru_cache(maxsize=20_000)
def _required_masks(
    atoms: tuple[str, ...], plan: tuple[Action, ...], goal: tuple[Lit, ...]
) -> tuple[int, int] | None:
    indices = {atom: index for index, atom in enumerate(atoms)}
    for action in plan:
        referenced = {lit.atom for lit in action.pre} | action.add | action.delete
        if referenced - indices.keys():
            raise ValueError("Plan refers to an undeclared atom")
    if any(lit.atom not in indices for lit in goal):
        raise ValueError("Goal refers to an undeclared atom")
    required = regress(plan, goal)
    if required is None:
        return None
    positive = negative = 0
    for literal in required:
        if literal.atom not in indices:
            raise ValueError("Plan or goal refers to an undeclared atom")
        if literal.positive:
            positive |= 1 << indices[literal.atom]
        else:
            negative |= 1 << indices[literal.atom]
    return positive, negative


def terminal_utility(probability: float, threshold: float) -> float:
    """Frozen permission rule and utility, not an optimal stopping theorem."""
    return 6 * probability - 5 if probability >= threshold else -0.05 * probability


@dataclass(frozen=True)
class Belief:
    atoms: tuple[str, ...]
    hypotheses: tuple[Hypothesis, ...]
    cache: tuple[tuple[str, bool | None], ...]
    age: int
    cache_time: int
    query_time: int
    sensor_error: float
    missing_probability: float
    plan: tuple[Action, ...]
    goal: tuple[Lit, ...]
    readings: tuple[Reading, ...] = ()
    queryable_atoms: frozenset[str] | None = None

    @cached_property
    def indices(self) -> Mapping[str, int]:
        return MappingProxyType({atom: index for index, atom in enumerate(self.atoms)})

    @cached_property
    def cache_values(self) -> Mapping[str, bool | None]:
        return MappingProxyType(dict(self.cache))

    @property
    def queried_atoms(self) -> frozenset[str]:
        return frozenset(reading.atom for reading in self.readings)

    @cached_property
    def valid_labels(self) -> tuple[bool, ...]:
        masks = _required_masks(self.atoms, self.plan, self.goal)
        if masks is None:
            return (False,) * len(self.hypotheses)
        positive, negative = masks
        return tuple(
            h.current & positive == positive and not h.current & negative
            for h in self.hypotheses
        )

    @cached_property
    def plan_probability(self) -> float:
        if all(self.valid_labels):
            return 1.0
        return min(
            1.0,
            max(
                0.0,
                fsum(
                    h.weight
                    for h, valid in zip(self.hypotheses, self.valid_labels)
                    if valid
                ),
            ),
        )

    def probability(self, plan: tuple[Action, ...], goal: tuple[Lit, ...]) -> float:
        masks = _required_masks(self.atoms, plan, goal)
        if masks is None:
            return 0.0
        positive, negative = masks
        selected = tuple(
            h
            for h in self.hypotheses
            if h.current & positive == positive and not h.current & negative
        )
        if not selected:
            return 0.0
        if len(selected) == len(self.hypotheses):
            return 1.0
        return min(1.0, max(0.0, fsum(h.weight for h in selected)))

    def marginal(self, atom: str) -> float:
        bit = self._bit(atom)
        selected = tuple(h for h in self.hypotheses if h.current & bit)
        if len(selected) == len(self.hypotheses):
            return 1.0
        return min(1.0, max(0.0, fsum(h.weight for h in selected)))

    def stale_risk(self, atom: str, cached_value: bool | None) -> float:
        if cached_value is None:
            self._bit(atom)
            return 1.0
        if type(cached_value) is not bool:
            raise ValueError("Cached truth must be bool or None")
        probability = self.marginal(atom)
        return 1 - probability if cached_value else probability

    def _bit(self, atom: str) -> int:
        try:
            return 1 << self.indices[atom]
        except KeyError as error:
            raise ValueError("Reading refers to an undeclared atom") from error

    def _target(self, hypothesis: Hypothesis, measured_at: int) -> int:
        if measured_at == self.age:
            return hypothesis.current
        if measured_at == self.cache_time:
            return hypothesis.before
        raise ValueError("Reading timestamp is neither cache nor current time")

    def _true_response_probability(
        self, hypothesis: Hypothesis, atom: str, measured_at: int
    ) -> float:
        bit = self._bit(atom)
        truth = bool(self._target(hypothesis, measured_at) & bit)
        cached = self.cache_values.get(atom)
        if cached is not None:
            bias = bool(hypothesis.before & bit) != cached
            return float(truth != bias)
        first = next(
            (
                r
                for r in self.readings
                if r.atom == atom and r.value is not None and not r.conflict
            ),
            None,
        )
        if first is not None:
            bias = (
                bool(self._target(hypothesis, first.measured_at) & bit) != first.value
            )
            return float(truth != bias)
        return 1 - self.sensor_error if truth else self.sensor_error

    def predict_reading(self, atom: str, measured_at: int) -> float:
        self._bit(atom)
        if self.queryable_atoms is not None and atom not in self.queryable_atoms:
            raise ValueError("A projected virtual validity atom cannot be queried")
        responses = tuple(
            self._true_response_probability(h, atom, measured_at)
            for h in self.hypotheses
        )
        if all(response == 0 for response in responses):
            return 0.0
        if all(response == 1 for response in responses):
            return 1.0
        probability = fsum(
            h.weight * response for h, response in zip(self.hypotheses, responses)
        )
        return min(1.0, max(0.0, probability))

    def condition(self, reading: Reading) -> "Belief":
        self._bit(reading.atom)
        if (
            self.queryable_atoms is not None
            and reading.atom not in self.queryable_atoms
        ):
            raise ValueError("A projected virtual validity atom cannot be queried")
        if reading.measured_at not in {self.cache_time, self.age}:
            raise ValueError("Reading timestamp is neither cache nor current time")
        if reading in self.readings:
            return self
        if reading.atom in self.queried_atoms:
            raise ValueError("Repeated query atom; identical readings are idempotent")
        history = self.readings + (reading,)
        if reading.value is None or reading.conflict:
            return replace(self, readings=history)
        weighted = []
        for hypothesis in self.hypotheses:
            positive = self._true_response_probability(
                hypothesis, reading.atom, reading.measured_at
            )
            likelihood = positive if reading.value else 1 - positive
            if likelihood > 0:
                weighted.append(
                    (
                        hypothesis.before,
                        hypothesis.current,
                        hypothesis.log_weight + log(likelihood),
                    )
                )
        if not weighted:
            raise InconsistentBelief(
                "Observation has zero probability under the supplied model"
            )
        maximum = max(weight for _, _, weight in weighted)
        normalizer = maximum + log(
            fsum(exp(weight - maximum) for _, _, weight in weighted)
        )
        return replace(
            self,
            hypotheses=tuple(
                Hypothesis(
                    before, current, exp(weight - normalizer), weight - normalizer
                )
                for before, current, weight in weighted
            ),
            readings=history,
        )

    def expected_one_step_value(self, atom: str, threshold: float) -> float:
        if atom in self.queried_atoms:
            raise ValueError("Query atom already used")
        if self.queryable_atoms is not None and atom not in self.queryable_atoms:
            raise ValueError("A projected virtual validity atom cannot be queried")
        current = terminal_utility(self.plan_probability, threshold)
        positive = []
        negative = []
        valid_positive = []
        valid_negative = []
        for hypothesis, valid in zip(self.hypotheses, self.valid_labels):
            response = self._true_response_probability(
                hypothesis, atom, self.query_time
            )
            yes = hypothesis.weight * response
            no = hypothesis.weight * (1 - response)
            positive.append(yes)
            negative.append(no)
            if valid:
                valid_positive.append(yes)
                valid_negative.append(no)
        values = []
        for probability, valid_mass in (
            (fsum(positive), fsum(valid_positive)),
            (fsum(negative), fsum(valid_negative)),
        ):
            if probability > 0:
                posterior = min(1.0, max(0.0, valid_mass / probability))
                values.append(probability * terminal_utility(posterior, threshold))
        return (
            self.missing_probability * current
            + (1 - self.missing_probability) * fsum(values)
            - 0.01
        )

    def one_step_values(
        self, atoms: Iterable[str], threshold: float
    ) -> dict[str, float]:
        """Joint-mass evaluation without constructing per-query posterior objects."""
        return {atom: self.expected_one_step_value(atom, threshold) for atom in atoms}


def _event_probability(hazard: float, steps: int) -> float:
    if steps == 0 or hazard == 0:
        return 0.0
    if hazard == 1:
        return 1.0
    return -expm1(steps * log1p(-hazard))


def build_belief(ctx: RevalidationContext) -> Belief:
    return _build_belief(
        ctx.base.model,
        ctx.actions,
        ctx.trusted_anchor,
        tuple(sorted(ctx.cache_observations.items())),
        ctx.known_after_cache,
        ctx.pre_gap,
        ctx.age,
        ctx.cache_time,
        ctx.query_delay,
        ctx.parameters.event_hazard,
        ctx.parameters.sensor_error,
        ctx.parameters.missing_probability,
        ctx.base.plan,
        ctx.base.goal,
        MAX_HYPOTHESES,
    )


@lru_cache(maxsize=32)
def _build_belief(
    model: Model,
    actions: tuple[Action, ...],
    trusted_anchor: frozenset[str],
    observations: tuple[tuple[str, bool | None], ...],
    known_actions: tuple[Action, ...],
    pre_gap: int,
    age: int,
    cache_time: int,
    query_delay: int,
    hazard: float,
    sensor_error: float,
    missing_probability: float,
    plan: tuple[Action, ...],
    goal: tuple[Lit, ...],
    max_hypotheses: int,
) -> Belief:
    """Cache only immutable runtime model inputs, never evaluator labels/state."""
    atoms = tuple(sorted(model.atoms))
    indices = {atom: index for index, atom in enumerate(atoms)}

    def bits(values: Iterable[str]) -> int:
        mask = 0
        for atom in values:
            if atom not in indices:
                raise ValueError("State or action refers to an undeclared atom")
            mask |= 1 << indices[atom]
        return mask

    anchor = bits(trusted_anchor)
    for clause in model.constraints:
        if not any(bool(anchor & bits((lit.atom,))) == lit.positive for lit in clause):
            raise InconsistentBelief("Trusted anchor violates its declared model")
    fixed = tuple(clause[0] for clause in model.constraints if len(clause) == 1)
    fixed_positive = bits(lit.atom for lit in fixed if lit.positive)
    fixed_negative = bits(lit.atom for lit in fixed if not lit.positive)

    def check_static(state: int) -> None:
        if state & fixed_positive != fixed_positive or state & fixed_negative:
            raise InconsistentBelief("Transition changes a fixed model proposition")

    library = _compile_library(atoms, actions)
    known = _compile_library(atoms, known_actions).operators
    if cache_time == age and known:
        raise ValueError(
            "Known action history requires distinct cache/current timestamps"
        )
    query_time = age - query_delay
    if query_time not in {cache_time, age}:
        raise ValueError("Query delay targets an unsupported intermediate time")
    for atom, value in observations:
        bits((atom,))
        if value is not None and type(value) is not bool:
            raise ValueError("Cached observations must be Boolean or missing")

    def kernel(state: int, steps: int) -> dict[int, float]:
        return dict(
            _kernel(state, library, fixed_positive, fixed_negative, hazard, steps)
        )

    eta = sensor_error
    weighted_before = []
    for before, prior in kernel(anchor, pre_gap).items():
        matched = mismatched = 0
        for atom, value in observations:
            if value is None:
                continue
            if bool(before & bits((atom,))) == value:
                matched += 1
            else:
                mismatched += 1
        if mismatched and eta == 0:
            continue
        likelihood = matched * log1p(-eta) + (
            mismatched * log(eta) if mismatched else 0
        )
        current = before
        for action in known:
            if not action.enabled(current):
                break
            current = action.apply(current)
            check_static(current)
        else:
            weighted_before.append((before, current, log(prior) + likelihood))
    if not weighted_before:
        raise InconsistentBelief(
            "Cached observations or known action success have zero probability"
        )
    joint = {}
    for before, after_known, log_weight in weighted_before:
        for current, probability in kernel(after_known, age).items():
            if probability <= 0:
                continue
            key = before, current
            value = log_weight + log(probability)
            if key in joint:
                maximum = max(value, joint[key])
                value = maximum + log(exp(value - maximum) + exp(joint[key] - maximum))
            joint[key] = value
            if len(joint) > max_hypotheses:
                raise BeliefLimit(
                    "Joint belief exceeds 100000 hypotheses; no support was truncated"
                )
    if not joint:
        raise InconsistentBelief("No positive-probability joint state remains")
    maximum = max(joint.values())
    normalizer = maximum + log(fsum(exp(weight - maximum) for weight in joint.values()))
    hypotheses = tuple(
        Hypothesis(before, current, exp(weight - normalizer), weight - normalizer)
        for (before, current), weight in sorted(joint.items())
    )
    return Belief(
        atoms,
        hypotheses,
        observations,
        age,
        cache_time,
        query_time,
        eta,
        missing_probability,
        plan,
        goal,
    )


def expected_one_step_value(belief: Belief, atom: str, threshold: float) -> float:
    return belief.expected_one_step_value(atom, threshold)


def reduce_belief(belief: Belief, fixed_query_atoms: Iterable[str]) -> Belief:
    """Exact pushforward for one caller-fixed menu and the original goal label.

    Retaining before/current query bits preserves persistent-channel likelihoods;
    retaining the full continuation-validity label preserves its terminal utility.
    No observation of the virtual label is permitted. This is an exact reference
    only for the supplied fixed menu, not a ceiling for arbitrary extra queries.
    """
    selected = tuple(sorted(set(fixed_query_atoms)))
    if len(selected) > 8:
        raise OracleLimit("Exact projection supports at most 8 fixed query atoms")
    source_bits = tuple(belief._bit(atom) for atom in selected)
    if (
        belief.queryable_atoms is not None
        and not set(selected) <= belief.queryable_atoms
    ):
        raise ValueError("Projected virtual validity cannot enter the query menu")
    virtual = "__full_continuation_valid__"
    while virtual in belief.atoms:
        virtual += "_"
    atoms = selected + (virtual,)
    validity_bit = 1 << len(selected)
    groups = {}
    linear = defaultdict(list)
    for hypothesis, valid in zip(belief.hypotheses, belief.valid_labels):
        before = current = 0
        for index, source_bit in enumerate(source_bits):
            if hypothesis.before & source_bit:
                before |= 1 << index
            if hypothesis.current & source_bit:
                current |= 1 << index
        if valid:
            current |= validity_bit
        key = before, current
        weight = hypothesis.log_weight
        if key in groups:
            maximum = max(weight, groups[key])
            weight = maximum + log(exp(weight - maximum) + exp(groups[key] - maximum))
        groups[key] = weight
        linear[key].append(hypothesis.weight)
    hypotheses = tuple(
        Hypothesis(before, current, fsum(linear[before, current]), weight)
        for (before, current), weight in sorted(groups.items())
    )
    return Belief(
        atoms=atoms,
        hypotheses=hypotheses,
        cache=tuple((atom, value) for atom, value in belief.cache if atom in selected),
        age=belief.age,
        cache_time=belief.cache_time,
        query_time=belief.query_time,
        sensor_error=belief.sensor_error,
        missing_probability=belief.missing_probability,
        plan=(),
        goal=(Lit(atom=virtual),),
        readings=tuple(r for r in belief.readings if r.atom in selected),
        queryable_atoms=frozenset(selected),
    )


def _query_menu(queryatoms) -> tuple[tuple[str, str], ...]:
    if isinstance(queryatoms, Mapping):
        menu = tuple(sorted(queryatoms.items()))
    else:
        menu = []
        for query in queryatoms:
            if isinstance(query, str):
                menu.append((query, query))
            elif len(query.atoms) == 1:
                menu.append((query.name, next(iter(query.atoms))))
            else:
                raise ValueError("Belief oracle requires single-proposition queries")
        menu = tuple(sorted(menu))
    if len({name for name, _ in menu}) != len(menu):
        raise ValueError("Query names must be unique")
    return menu


def select_exact_query(
    belief: Belief, queryatoms, budget: int, threshold: float
) -> str | None:
    """Finite belief decision oracle for the declared utility and observation model."""
    if type(budget) is not int or budget < 0:
        raise ValueError("Budget must be a nonnegative integer")
    menu = _query_menu(queryatoms)
    if len(menu) > 8 or budget > 3:
        raise OracleLimit("Exact decision limit: 8 queries, 32 hypotheses, budget 3")
    for _, atom in menu:
        belief._bit(atom)
        if belief.queryable_atoms is not None and atom not in belief.queryable_atoms:
            raise ValueError("Projected virtual validity cannot enter the query menu")
    if len(belief.hypotheses) > 32:
        belief = reduce_belief(belief, (atom for _, atom in menu))
    if len(belief.hypotheses) > 32:
        raise OracleLimit(
            "Exact decision exceeds 32 projected hypotheses; no mass truncated"
        )
    memo = {}

    def value(node: Belief, available, remaining: int) -> tuple[float, str | None]:
        stop = terminal_utility(node.probability(node.plan, node.goal), threshold)
        if remaining == 0 or not available:
            return stop, None
        key = (
            tuple((h.before, h.current, h.log_weight) for h in node.hypotheses),
            tuple((r.atom, r.value, r.measured_at, r.conflict) for r in node.readings),
            available,
            remaining,
        )
        if key in memo:
            return memo[key]
        best, choice = stop, None
        for name, atom in available:
            if atom in node.queried_atoms:
                continue
            future = tuple(item for item in available if item[1] != atom)
            true_chance = node.predict_reading(atom, node.query_time)
            missing = node.condition(
                Reading(atom=atom, value=None, measured_at=node.query_time)
            )
            parts = [
                node.missing_probability * value(missing, future, remaining - 1)[0]
            ]
            for answer, chance in ((True, true_chance), (False, 1 - true_chance)):
                if chance:
                    posterior = node.condition(
                        Reading(atom=atom, value=answer, measured_at=node.query_time)
                    )
                    parts.append(
                        (1 - node.missing_probability)
                        * chance
                        * value(posterior, future, remaining - 1)[0]
                    )
            candidate = fsum(parts) - 0.01
            if candidate > best + 1e-12:
                best, choice = candidate, name
        memo[key] = best, choice
        return best, choice

    return value(belief, menu, budget)[1]
