"""Independent dictionary/raw-state analysis; no editor or support-checker imports."""

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from dual_rec.explanation_repair.audit import (
    factual_claims,
    identity,
    raw_truth,
    true_claim,
)


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def literal_entails(sequence, claim):
    """Semantic credit for a complete supplied prefix, independently interpreted."""
    fact = claim["fact"]
    if claim["action"] != "command_log" or fact["entity"] != "command_log":
        return False
    if fact["predicate"] == "sequence":
        return json.loads(fact["value"]) == sequence
    if fact["predicate"] in ("listed", "missing"):
        return (fact["value"] in sequence) == (fact["predicate"] == "listed")
    if fact["predicate"] == "order":
        pair = json.loads(fact["value"])
        return (
            len(pair) == 2
            and pair[0] != pair[1]
            and all(sequence.count(a) == 1 for a in pair)
            and sequence.index(pair[0]) < sequence.index(pair[1])
        )
    return False


def metrics(input_row, result, oracle):
    original = factual_claims(input_row["input"]["claims"])
    output = factual_claims([g["claim"] for g in result["claims"]])
    supported = {key for key, claim in original.items() if oracle(claim) is True}
    retained = set(output) & supported
    sequences = [
        json.loads(c["fact"]["value"])
        for c in output.values()
        if c["action"] == "command_log"
        and c["fact"]["predicate"] == "sequence"
        and oracle(c) is True
    ]
    for key in supported - retained:
        claim = original[key]
        if any(literal_entails(sequence, claim) for sequence in sequences):
            retained.add(key)
    truths = [oracle(c) for c in output.values()]
    correct = (
        bool(original)
        and len(supported) == len(original)
        and not input_row["input"]["unparsed"]
        and all(c["kind"] != "hypothesis" for c in input_row["input"]["claims"])
    )
    unsupported = sum(t is not True for t in truths)
    return {
        "inputs": 1,
        "asserted": len(output),
        "established": sum(t is True for t in truths),
        "contradicted": sum(t is False for t in truths),
        "undetermined": sum(t is None for t in truths),
        "unsupported": unsupported,
        "any_unsupported": int(unsupported > 0),
        "supported_original": len(supported),
        "retained": len(retained),
        "informative": int(any(t is True for t in truths)),
        "correct_inputs": int(correct),
        "damaged": int(correct and (unsupported > 0 or retained != supported)),
        "cosmetic_change": int(
            correct and result["text"] != input_row["input"]["original_text"]
        ),
        "abstained": int(not output),
        "unresolved": int(bool(result["unresolved"])),
    }


RATIOS = {
    "unsupported_input_fraction": ("any_unsupported", "inputs"),
    "retention": ("retained", "supported_original"),
    "informative_fraction": ("informative", "inputs"),
    "damage_fraction": ("damaged", "correct_inputs"),
    "established_facts_per_input": ("established", "inputs"),
}


def paired_bootstrap(per_input, codes, draws, seed):
    groups = defaultdict(lambda: defaultdict(Counter))
    for row in per_input:
        group = "/".join(row["cell"].split("/")[:2])
        groups[group][row["code"]].update(row["metrics"])
    names = sorted(groups)
    tasks = sorted({g.split("/")[0] for g in names})
    strata = [
        [i for i, g in enumerate(names) if g.split("/")[0] == task] for task in tasks
    ]
    keys = sorted(next(iter(next(iter(groups.values())).values())).keys())
    array = np.asarray(
        [[[groups[g][c][k] for k in keys] for c in codes] for g in names], dtype=float
    )
    totals = array.sum(axis=0)
    rng = np.random.default_rng(seed)
    sampled = np.stack(
        [
            array[
                np.concatenate([rng.choice(s, len(s), replace=True) for s in strata])
            ].sum(axis=0)
            for _ in range(draws)
        ]
    )
    comparisons = {}
    for other in [c for c in codes if c != "B4"]:
        a, b = codes.index("B4"), codes.index(other)
        values = {}
        for name, (numerator, denominator) in RATIOS.items():
            n, d = keys.index(numerator), keys.index(denominator)
            delta = totals[a, n] / totals[a, d] - totals[b, n] / totals[b, d]
            dist = (
                sampled[:, a, n] / sampled[:, a, d]
                - sampled[:, b, n] / sampled[:, b, d]
            )
            values[name] = {
                "difference": float(delta),
                "percentile95": np.quantile(dist, [0.025, 0.975]).tolist(),
            }
        comparisons["B4-minus-" + other] = values
    return {
        "groups": len(names),
        "task_groups": {task: len(s) for task, s in zip(tasks, strata, strict=True)},
        "draws": draws,
        "seed": seed,
        "unit": "task-parent seed, both conditions and all variants together; tasks stratified",
        "comparisons": comparisons,
    }


def run(root):
    config = load(Path("config/explanation_repair_week2.json"))
    old = Path(config["week1_root"]) / config["week1_development"]
    cells = load(old / "physical_sources.json")
    truths = {}
    for cell in cells:
        with gzip.open(cell["source"], "rt") as stream:
            truths[cell["id"]] = (
                cell["task"],
                raw_truth(json.load(stream), cell["task"]),
            )
    inputs = {row["id"]: row for row in rows(old / "trace_inputs.jsonl")}
    totals, task_totals = defaultdict(Counter), defaultdict(Counter)
    per_input = []
    for row in rows(root / "trace_outputs.jsonl"):
        original = inputs[row["id"]]
        task, truth = truths[original["cell"]]
        scores = metrics(
            original,
            row["result"],
            lambda c, truth=truth, task=task: true_claim(c, truth, task),
        )
        totals[row["code"]].update(scores)
        task_totals[task + "/" + row["code"]].update(scores)
        per_input.append(
            {
                "id": row["id"],
                "cell": original["cell"],
                "variant": original["variant"],
                "code": row["code"],
                "metrics": scores,
            }
        )
    save(
        root / "trace_metrics.json",
        {
            "totals": {k: dict(v) for k, v in totals.items()},
            "by_task": {k: dict(v) for k, v in task_totals.items()},
            "interpretation": "Independent raw-state truth, conditional on declared transport preconditions. Previously used controlled development, not natural-language gold or new recovery evidence. Information count is not human utility.",
        },
    )
    save(root / "trace_per_input_metrics.json", per_input)
    save(
        root / "trace_paired_uncertainty.json",
        paired_bootstrap(
            per_input,
            list(config["methods"]),
            config["bootstrap_draws"],
            config["bootstrap_seed"],
        ),
    )
    controlled = {v["id"]: v for v in rows(root / "controls_frozen.jsonl")}
    control_totals, detail = defaultdict(Counter), []
    for row in rows(root / "control_outputs.jsonl"):
        original = controlled[row["id"]]
        true_set = {identity(c) for c in original["oracle_true"]}
        scores = metrics(
            original,
            row["result"],
            lambda c, true_set=true_set: True if identity(c) in true_set else None,
        )
        control_totals[row["code"]].update(scores)
        detail.append(
            {
                "id": row["id"],
                "code": row["code"],
                "metrics": scores,
                "text": row["result"]["text"],
                "decisions": [v["operation"] for v in row["result"]["decisions"]],
            }
        )
    save(
        root / "control_metrics.json",
        {
            "totals": {k: dict(v) for k, v in control_totals.items()},
            "detail": detail,
            "interpretation": "13 authored logical controls, not independent sampled tasks or released natural-language gold. Unsupported includes false and undetermined assertions; no interval used to imply population generalization.",
        },
    )
    public = rows(root / "public_inputs.jsonl")
    groups = defaultdict(Counter)
    for row in public:
        e = row["extraction"]
        groups[row["group"]].update(
            rows=1,
            complete=int(e["complete"]),
            partial=int(e["partial"]),
            factual=int(e["factual_claims"] > 0),
        )
    names = sorted(groups)
    matrix = np.asarray(
        [
            [groups[g][k] for k in ["rows", "complete", "partial", "factual"]]
            for g in names
        ]
    )
    rng = np.random.default_rng(config["bootstrap_seed"])
    samples = matrix[
        rng.integers(0, len(names), (config["bootstrap_draws"], len(names)))
    ].sum(axis=1)
    total = matrix.sum(axis=0)
    coverage = {
        name: {
            "count": int(total[i]),
            "fraction": float(total[i] / total[0]),
            "percentile95": np.quantile(
                samples[:, i] / samples[:, 0], [0.025, 0.975]
            ).tolist(),
        }
        for i, name in enumerate(["rows", "complete", "partial", "factual"])
        if i
    }
    public_counts = defaultdict(Counter)
    examples = defaultdict(list)
    by_id = {r["id"]: r for r in public}
    for row in rows(root / "public_outputs.jsonl"):
        result = row["result"]
        total = public_counts[row["code"]]
        total.update(
            rows=1,
            emitted_factual_slots=sum(
                g["claim"]["kind"] != "hypothesis" for g in result["claims"]
            ),
            no_factual_output=int(
                not any(g["claim"]["kind"] != "hypothesis" for g in result["claims"])
            ),
            unresolved=int(bool(result["unresolved"])),
            replacements=sum(c["operation"] == "replace" for c in result["decisions"]),
        )
        if row["code"] == "B4":
            original = by_id[row["id"]]
            category = (
                "literal_replacement_not_independently_graded"
                if any(c["operation"] == "replace" for c in result["decisions"])
                else "factual_extraction_no_replacement"
                if original["extraction"]["factual_claims"]
                else "hypothesis_only_or_parse_failure"
            )
            if len(examples[category]) < 4:
                examples[category].append(
                    {
                        "id": row["id"],
                        "original": original["original"],
                        "extraction": original["extraction"],
                        "result": result,
                    }
                )
    save(
        root / "public_analysis.json",
        {
            "quality": {
                key: "NOT_ASSESSED_WITHOUT_INDEPENDENT_ADJUDICATION"
                for key in [
                    "unsupported_assertions",
                    "supported_retention",
                    "correct_explanations_damaged",
                    "useful_diagnostic_content",
                    "repair_accuracy",
                ]
            },
            "coverage": coverage,
            "bootstrap": {
                "groups": len(groups),
                "draws": config["bootstrap_draws"],
                "seed": config["bootstrap_seed"],
                "unit": "conservative episode/template/exact-input alias components; pooled groups can cross tasks; grouping provenance incomplete",
            },
            "mechanical_counts_not_quality": {
                k: dict(v) for k, v in public_counts.items()
            },
        },
    )
    save(root / "representative_public_examples.json", dict(examples))
    print(
        json.dumps(
            {
                "trace_totals": {k: dict(v) for k, v in totals.items()},
                "control_totals": {k: dict(v) for k, v in control_totals.items()},
                "coverage": coverage,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
