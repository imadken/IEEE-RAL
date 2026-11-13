"""Freeze controls/review inputs, then run exactly six deterministic methods."""

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from dual_rec.explanation_repair.adapters import PublicRecord
from dual_rec.explanation_repair.core import assess, run_method
from dual_rec.explanation_repair.experiment import read, save, sha
from dual_rec.explanation_repair.natural import language_bundle
from dual_rec.explanation_repair.schemas import (
    ActionModel,
    ActionRule,
    Claim,
    Fact,
    Record,
    RepairInput,
    Window,
)


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def jsonl(path, values):
    path.write_text("".join(json.dumps(v, allow_nan=False) + "\n" for v in values))


def controls():
    """Explicit authored truth tables, independent of support/editing outcomes."""
    now, past = Window(start=1, end=1), Window(start=0, end=0)
    closed = Fact(entity="fridge", predicate="open", value=False)
    opened = closed.model_copy(update={"value": True})

    def obs(name, fact, window=now):
        return Record(id=name, fact=fact, window=window, source="authored-control")

    def claim(name, fact, window=now, kind="observation", action=None):
        return Claim(id=name, fact=fact, window=window, kind=kind, action=action)

    def make(name, records, claims, truths, model=None):
        bundle = RepairInput(
            id=name,
            records=records,
            claims=claims,
            model=model or ActionModel(),
            query=now,
            original_text=name,
        )
        return {
            "id": name,
            "input": bundle.model_dump(mode="json"),
            "oracle_true": [c.model_dump(mode="json") for c in truths],
            "oracle_note": "Authored logical truth table, fixed before method evaluation; not released-language gold or a physics outcome",
        }

    old = claim("old", opened, past)
    new = claim("new", closed)
    records = [obs("past", opened, past), obs("current", closed)]
    result = [
        make("correct_historical", records, [old], [old, new]),
        make("temporally_misplaced", records, [claim("stale", opened)], [old, new]),
        make(
            "missing_evidence",
            [records[1]],
            [claim("battery", Fact(entity="battery", predicate="empty", value=True))],
            [new],
        ),
        make(
            "multiple_plausible_causes",
            [records[1]],
            [
                Claim(id="motor", kind="hypothesis", window=now),
                Claim(id="perception", kind="hypothesis", window=now),
            ],
            [new],
        ),
        make(
            "conflicting_observations",
            [obs("one", opened), obs("two", closed)],
            [claim("conflict", opened)],
            [],
        ),
        make("correct_no_repair", [records[1]], [new], [new]),
        make(
            "command_not_effect",
            [
                Record(
                    id="cmd",
                    fact=Fact(entity="robot", predicate="command", value="open fridge"),
                    window=now,
                    source="authored-control",
                    kind="command",
                    action="open fridge",
                )
            ],
            [claim("effect", opened)],
            [],
        ),
        make(
            "unanchored_history",
            [records[1]],
            [claim("unknown", closed, Window(clock="unknown", start=0, end=0))],
            [new],
        ),
    ]
    for value in (False, True):
        grasp = Fact(entity="cube", predicate="grasped", value=value)
        requirement = grasp.model_copy(update={"value": True})
        applicable = Fact(entity="transport", predicate="applicable", value=value)
        model = ActionModel(
            rules=[
                ActionRule(
                    id="requires-grasp", action="transport", preconditions=[requirement]
                )
            ]
        )
        truth = claim("truth", applicable, kind="implication", action="transport")
        asserted = claim(
            "asserted",
            applicable.model_copy(update={"value": True}),
            kind="implication",
            action="transport",
        )
        result.append(
            make(
                "valid_model" if value else "blocked_model",
                [obs("grasp", grasp)],
                [asserted],
                [claim("grasp", grasp), truth],
                model,
            )
        )
    for name, sequence, pair in [
        (
            "correct_order",
            ["pick up mug", "put mug on countertop"],
            ["pick up mug", "put mug on countertop"],
        ),
        (
            "wrong_order",
            ["pick up mug", "put mug on countertop"],
            ["put mug on countertop", "pick up mug"],
        ),
        (
            "ambiguous_repetition",
            ["pick up mug", "put mug on countertop", "pick up mug"],
            ["pick up mug", "put mug on countertop"],
        ),
    ]:
        window = Window(clock="plan_index", start=0, end=len(sequence) - 1)
        commands = [
            Record(
                id=f"cmd/{i}",
                fact=Fact(entity="robot", predicate="command", value=a),
                window=Window(clock="plan_index", start=i, end=i),
                source="authored-control",
                kind="command",
                action=a,
            )
            for i, a in enumerate(sequence)
        ]
        query = claim(
            "order",
            Fact(entity="command_log", predicate="order", value=json.dumps(pair)),
            window,
            "implication",
            "command_log",
        )
        truth = [
            claim(
                "sequence",
                Fact(
                    entity="command_log",
                    predicate="sequence",
                    value=json.dumps(sequence),
                ),
                window,
                "implication",
                "command_log",
            )
        ]
        if name != "ambiguous_repetition":
            truth.append(
                query.model_copy(
                    update={
                        "fact": query.fact.model_copy(
                            update={"value": json.dumps(sequence)}
                        )
                    }
                )
            )
        result.append(
            make(name, commands, [query], truth, ActionModel(command_log=True))
        )
    return result


def run(root):
    config = read(Path("config/explanation_repair_week2.json"))
    old = Path(config["week1_root"]) / config["week1_development"]
    freeze = read(root / "review_subset_freeze.json")
    wanted = {v["id"] for v in freeze["rows"]}
    source = rows(old / "public_inputs.jsonl")
    public, review, provisional = [], [], []
    totals = defaultdict(Counter)
    for row in source:
        bundle, extraction = language_bundle(
            PublicRecord.model_validate(row["original"]), row["dataset"]
        )
        public.append(
            {
                "id": row["id"],
                "dataset": row["dataset"],
                "generation": row["generation"],
                "group": row["group"],
                "original": row["original"],
                "input": bundle.model_dump(mode="json"),
                "extraction": extraction.model_dump(mode="json"),
            }
        )
        total = totals[row["dataset"] + "/" + row["generation"]]
        total.update(
            rows=1,
            complete=int(extraction.complete),
            partial=int(extraction.partial),
            none=int(not bundle.claims),
            factual_extracted=int(extraction.factual_claims > 0),
            hypothesis_only=int(bool(bundle.claims) and not extraction.factual_claims),
            recognized_clauses=extraction.recognized_clauses,
            clauses=len(extraction.clauses),
            residue=len(bundle.unparsed),
        )
        if row["id"] in wanted:
            # No method output in the blind review file; no invented human labels.
            for clause in extraction.clauses:
                review.append(
                    {
                        "id": row["id"],
                        "dataset": row["dataset"],
                        "generation": row["generation"],
                        "alias_group": row["group"],
                        "context": row["original"],
                        "clause": clause.model_dump(mode="json"),
                        "candidate_claims": [
                            c.model_dump(mode="json")
                            for c in bundle.claims
                            if c.id in clause.claim_ids
                        ],
                        "adjudicated_status": None,
                        "adjudicated_claims": None,
                        "independent_reviewer": None,
                        "information_to_preserve": None,
                        "dependency_review": None,
                        "instructions": "Review the source clause and complete context, correct extraction first, then supported/contradicted/undetermined per claim. Describe time/model dependencies and information worth preserving. Existing coherence labels/comments are context, not gold repairs. Do not inspect method outputs.",
                    }
                )
            for claim in bundle.claims:
                proof = assess(bundle, claim)
                provisional.append(
                    {
                        "id": row["id"],
                        "claim": claim.model_dump(mode="json"),
                        "machine_proposed_status": "undetermined"
                        if proof.status == "unknown"
                        else proof.status,
                        "proof": proof.model_dump(mode="json"),
                        "status": "PROVISIONAL_UNADJUDICATED_DO_NOT_SCORE",
                        "suggested_information_to_preserve": "candidate only"
                        if proof.status == "supported"
                        else "independent review required",
                        "dependency": {
                            "time": claim.window.model_dump(mode="json"),
                            "action": claim.action,
                            "references": claim.depends_on,
                        },
                    }
                )
    jsonl(root / "public_inputs.jsonl", public)
    jsonl(root / "review_blind.jsonl", review)
    jsonl(root / "review_provisional_not_gold.jsonl", provisional)
    controlled = controls()
    jsonl(root / "controls_frozen.jsonl", controlled)
    save(
        root / "evaluation_input_freeze.json",
        {
            "note": "Inputs, controls, review sheets and source frozen before six-method outputs",
            "hashes": {
                name: sha(root / name)
                for name in [
                    "public_inputs.jsonl",
                    "review_subset_freeze.json",
                    "review_blind.jsonl",
                    "review_provisional_not_gold.jsonl",
                    "controls_frozen.jsonl",
                ]
            },
            "source_hashes": {
                str(p): sha(p)
                for folder in ["src/dual_rec/explanation_repair", "scripts"]
                for p in Path(folder).glob("*week2*.py")
            }
            | {
                str(p): sha(p)
                for p in Path("src/dual_rec/explanation_repair").glob("*.py")
            },
            "config_sha256": sha(Path("config/explanation_repair_week2.json")),
        },
    )
    save(
        root / "public_coverage.json",
        {
            "strata": {k: dict(v) for k, v in totals.items()},
            "quality": "NOT_ASSESSED: no independent claim or repair adjudication",
            "review_examples": len(wanted),
            "review_clauses": len(review),
        },
    )
    runtime = defaultdict(list)
    for population, inputs in [
        ("public", public),
        ("trace", rows(old / "trace_inputs.jsonl")),
        ("control", controlled),
    ]:
        path = root / f"{population}_outputs.jsonl"
        with path.open("x") as stream:
            for row in inputs:
                bundle = RepairInput.model_validate(row["input"])
                for code, method in config["methods"].items():
                    started = time.perf_counter_ns()
                    result = run_method(bundle, method)
                    elapsed = time.perf_counter_ns() - started
                    assert result.menus_evaluated <= config["common_candidate_limit"]
                    runtime[population + "/" + code].append(elapsed / 1e6)
                    stream.write(
                        json.dumps(
                            {
                                "id": row["id"],
                                "code": code,
                                "method": method,
                                "runtime_ms": elapsed / 1e6,
                                "result": result.model_dump(mode="json"),
                            },
                            allow_nan=False,
                        )
                        + "\n"
                    )
                stream.flush()
    save(
        root / "runtime.json",
        {
            key: {
                "count": len(v),
                "total_ms": sum(v),
                "mean_ms": sum(v) / len(v),
                "max_ms": max(v),
            }
            for key, v in runtime.items()
        },
    )
    print(
        json.dumps(
            {
                "public": len(public),
                "traces": 595,
                "controls": len(controlled),
                "review_rows": len(wanted),
                "review_clauses": len(review),
                "coverage": {k: dict(v) for k, v in totals.items()},
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root)
