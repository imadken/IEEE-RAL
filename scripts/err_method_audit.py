"""Registered exact finite-world falsification suite and independent oracles."""

import argparse
import hashlib
import importlib.util
import json
import random
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

from err_cases import exhaustive_binary_cases, from_signatures, registered_cases
from err_independent_oracle import exhaustive, greedy, integer_program, verify_witnesses

from dual_rec.evidence_aware.evidence_resolution import resolve_evidence
from dual_rec.evidence_aware.experiment_resolvability import (
    minimum_resolving_experiments,
)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def reference_module():
    path = Path(
        "research/err_method_challenge/supervisor/finite_world_experiment_planner.py"
    )
    spec = importlib.util.spec_from_file_location("err_supplied_reference", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def reference_answer(reference, raw):
    laws = {
        e["experiment_id"]: {
            r["world_id"]: tuple(float(Fraction(p)) for p in r["probabilities"])
            for r in e["laws"]
        }
        for e in raw["experiments"]
    }
    worlds = tuple(
        reference.World(
            w["world_id"],
            w["obligation_verdict"],
            tuple((e, rows[w["world_id"]]) for e, rows in laws.items()),
        )
        for w in raw["worlds"]
    )
    result = reference.minimal_resolving_experiments(
        worlds, {e["experiment_id"]: Fraction(e["cost"]) for e in raw["experiments"]}
    )
    return (
        None
        if result["status"] == "impossible"
        else (result["cost"], tuple(result["experiments"]))
    )


def random_problems(registration):
    rng = random.Random(registration["seed"])
    grid = registration["random_grid"]
    for n in grid["world_counts"]:
        for m in grid["experiment_counts"]:
            for replication in range(grid["cases_each_grid_cell"]):
                labels = [bool(rng.randrange(2)) for _ in range(n)]
                labels[0], labels[-1] = False, True
                signatures = []
                for _ in range(m):
                    alphabet = rng.choice((2, 3))
                    rows = []
                    for i in range(n):
                        if i and rng.random() < 0.25:
                            rows.append(rows[rng.randrange(i)])
                        else:
                            counts = [rng.randrange(5) for _ in range(alphabet)]
                            if not sum(counts):
                                counts[0] = 1
                            rows.append(tuple(Fraction(k, sum(counts)) for k in counts))
                    signatures.append(rows)
                costs = [
                    Fraction(rng.randrange(9), rng.randrange(1, 6)) for _ in range(m)
                ]
                yield (n, m, replication), from_signatures(labels, signatures, costs)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    registration = json.loads(
        Path("research/err_method_challenge/registration.json").read_text()
    )
    reference = reference_module()
    start = time.perf_counter()
    counts = Counter()
    registered = {}

    def check(problem, *, milp=True, supplied_reference=True):
        raw = problem.model_dump(mode="json")
        began = time.perf_counter()
        result = minimum_resolving_experiments(problem)
        elapsed = time.perf_counter() - began
        truth = exhaustive(raw)
        got = (
            None
            if result.total_cost is None
            else (result.total_cost, result.selected_experiments)
        )
        assert got == truth, (raw, result, truth)
        verify_witnesses(raw, result.model_dump(mode="json"))
        counts["exact_exhaustive_agreements"] += 1
        counts[result.status] += 1
        if milp:
            try:
                assert integer_program(raw) == truth
                counts["MILP_agreements"] += 1
            except ValueError as error:
                assert (
                    str(error)
                    == "MILP_DOUBLE_INTEGER_RANGE_UNSUPPORTED_USE_EXACT_ORACLE"
                )
                counts["MILP_exact_cost_range_unsupported"] += 1
        old_reference = (
            reference_answer(reference, raw) if supplied_reference else truth
        )
        if supplied_reference:
            counts[
                "reference_agreements"
                if old_reference == truth
                else "reference_rounding_divergences"
            ] += 1
        heuristic = greedy(raw)
        pruned = greedy(raw, reverse_delete=True)
        if truth is not None:
            assert heuristic is not None and pruned is not None
            assert heuristic[0] >= truth[0] and pruned[0] >= truth[0]
            counts[
                "greedy_same_cost" if heuristic[0] == truth[0] else "greedy_higher_cost"
            ] += 1
            counts[
                "pruned_greedy_same_cost"
                if pruned[0] == truth[0]
                else "pruned_greedy_higher_cost"
            ] += 1
        return raw, result, truth, old_reference, heuristic, pruned, elapsed

    for name, problem in registered_cases().items():
        raw, result, truth, old, heuristic, pruned, elapsed = check(problem)
        if old != truth:
            assert name in ("reference_rounding_trap", "finite_sample_overlap")
        registered[name] = {
            "problem": raw,
            "production": result.model_dump(mode="json"),
            "typed_output": resolve_evidence(problem=problem).model_dump(mode="json"),
            "independent_exact_oracle": None
            if truth is None
            else [str(truth[0]), truth[1]],
            "supplied_reference_agrees": old == truth,
            "source_cost_greedy": None
            if heuristic is None
            else [str(heuristic[0]), heuristic[1]],
            "reverse_deleted_greedy": None
            if pruned is None
            else [str(pruned[0]), pruned[1]],
            "solver_wall_seconds": elapsed,
            "evidence_type": "ANALYTICAL_ONLY_NOT_ROBOT_EPISODES",
        }
    (output / "registered_cases_and_results.json").write_text(
        json.dumps(registered, indent=2) + "\n"
    )
    before_random = counts.copy()
    with (
        (output / "seeded_cases.jsonl").open("w") as cases,
        (output / "seeded_results.jsonl").open("w") as results,
    ):
        for index, problem in random_problems(registration):
            raw, result, truth, old, heuristic, pruned, elapsed = check(problem)
            assert old == truth
            cases.write(encoded({"index": index, "problem": raw}) + "\n")
            results.write(
                encoded(
                    {
                        "index": index,
                        "problem_sha256": hashlib.sha256(
                            encoded(raw).encode()
                        ).hexdigest(),
                        "result": result.model_dump(mode="json"),
                        "solver_wall_seconds": elapsed,
                        "greedy": None
                        if heuristic is None
                        else [str(heuristic[0]), heuristic[1]],
                        "pruned_greedy": None
                        if pruned is None
                        else [str(pruned[0]), pruned[1]],
                    }
                )
                + "\n"
            )
    random_counts = counts - before_random
    assert random_counts["exact_exhaustive_agreements"] == 504
    assert random_counts["MILP_agreements"] == 504
    exhaustive_counts = Counter()
    with (output / "exhaustive_binary_cases.jsonl").open("w") as stream:
        for n, m, labels, bits, costs, signatures in exhaustive_binary_cases():
            p = from_signatures(labels, signatures, costs)
            raw = p.model_dump(mode="json")
            result = minimum_resolving_experiments(p)
            truth = exhaustive(raw)
            got = (
                None
                if result.total_cost is None
                else (result.total_cost, result.selected_experiments)
            )
            assert got == truth
            verify_witnesses(raw, result.model_dump(mode="json"))
            exhaustive_counts[f"n{n}_m{m}"] += 1
            stream.write(
                encoded(
                    {
                        "n": n,
                        "m": m,
                        "verdicts": labels,
                        "bits": bits,
                        "costs": costs,
                        "status": result.status,
                        "selected": result.selected_experiments,
                        "cost": None
                        if result.total_cost is None
                        else str(result.total_cost),
                    }
                )
                + "\n"
            )
            assert time.perf_counter() - start < 7200, (
                "Bounded exact audit exceeded its 2h internal allowance"
            )
    assert sum(exhaustive_counts.values()) == 42160
    summary = {
        "passed": True,
        "registered_cases": len(registered),
        "random_grid": registration["random_grid"],
        "random_counts": dict(random_counts),
        "registered_and_random_counts": dict(counts),
        "exhaustive_binary_counts": dict(exhaustive_counts),
        "exhaustive_binary_cases": sum(exhaustive_counts.values()),
        "source_signatures": "Exact normalized probability vectors; no lucky outcomes, probability tolerances or hidden oracle labels",
        "global_minimum": "Independent exact enumeration agrees in all registered/random/exhaustive cases; a separate MILP agrees wherever exact integer costs fit its declared range",
        "baseline_equivalence": "B7 and direct bounds with the identical planner share all finite output semantics; no unique solver or sample-efficiency claim",
        "wall_seconds": time.perf_counter() - start,
        "new_physics": 0,
    }
    (output / "finite_world_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("research/err_method_challenge/results")
    )
    run(parser.parse_args().output)
