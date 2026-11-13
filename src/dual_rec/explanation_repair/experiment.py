"""Bounded development comparisons on public examples and reused physical traces."""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from .adapters import (
    PublicRecord,
    public_bundle,
    public_groups,
    select_action,
    trace_bundle,
)
from .core import assess, baselines, edit, render_claim
from .examples import worked_cases
from .schemas import Claim, Fact, Objective


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def append(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")


def variants(bundle):
    def version(name, claims, unparsed=None):
        return name, bundle.model_copy(
            update={
                "id": bundle.id + "/" + name,
                "claims": claims,
                "unparsed": unparsed or [],
                "original_text": " ".join(render_claim(c, bundle.query) for c in claims)
                if not unparsed
                else unparsed[0],
            }
        )

    current = bundle.claims
    flipped = current[0].model_copy(
        update={
            "fact": current[0].fact.model_copy(
                update={"value": not current[0].fact.value}
            )
        }
    )
    past = [
        Claim(id="history/" + r.id, kind="observation", fact=r.fact, window=r.window)
        for r in bundle.records
        if r.id.startswith("first/")
    ]
    stale = past[0].model_copy(update={"id": "stale", "window": bundle.query})
    model_claim = Claim(
        id="model",
        kind="implication",
        action="transport",
        fact=Fact(entity="transport", predicate="applicable", value=True),
        window=bundle.query,
    )
    return [
        version("unedited_template", current),
        version("partial_flip", [flipped, *current[1:]]),
        version(
            "unsupported",
            [
                Claim(
                    id="battery",
                    kind="observation",
                    fact=Fact(entity="battery", predicate="failed", value=True),
                    window=bundle.query,
                ),
                Claim(id="cause", kind="hypothesis", window=bundle.query),
            ],
        ),
        version("stale", [stale, *current[1:]]),
        version("historical_correct", [*past, *current]),
        version("action_model", [*current, model_claim]),
        version(
            "unparseable",
            [],
            ["Opaque diagnostic prose outside the fixed parser grammar."],
        ),
    ]


def public_comparisons(root, target):
    all_rows, errors = [], []
    for dataset, filename in [
        ("RoboFail", "RoboFail_generated.json"),
        ("CounterFactual", "CounterFactual_generated.json"),
    ]:
        for i, raw in enumerate(read(root / "upstream/data" / filename)):
            try:
                all_rows.append((dataset, PublicRecord.model_validate(raw)))
            except ValueError as exc:
                errors.append(
                    {"dataset": dataset, "index": i, "raw": raw, "error": str(exc)}
                )
    groups = public_groups(all_rows)
    summaries = {}
    output_counts = Counter()
    examples = []
    with (
        (target / "public_inputs.jsonl").open("w") as inputs,
        (target / "public_outputs.jsonl").open("w") as outputs,
    ):
        for (dataset, row), group in zip(all_rows, groups, strict=True):
            bundle, extraction = public_bundle(row, dataset)
            generation = (
                "template"
                if dataset == "CounterFactual"
                else "expert"
                if row.task_id.endswith("_gt_exp")
                else "GPT-3.5/REFLECT"
                if row.task_id.endswith("_reflect_exp")
                else "unresolved-source"
            )
            key = dataset + "/" + generation
            summary = summaries.setdefault(key, Counter())
            summary.update(
                rows=1,
                spans=extraction.spans,
                covered_spans=extraction.covered_spans,
                fully_extracted=int(extraction.spans > 0 and not extraction.unparsed),
                parsed_claims=len(bundle.claims),
                observation_spans=len(row.observation),
                parsed_observations=sum(
                    r.kind == "observation" for r in bundle.records
                ),
            )
            summary["original_label_" + row.label] += 1
            append(
                inputs,
                {
                    "id": bundle.id,
                    "dataset": dataset,
                    "generation": generation,
                    "group": group,
                    "original": row.model_dump(),
                    "input": bundle.model_dump(),
                    "extraction": extraction.model_dump(),
                    "partition": "development-interface-only",
                    "grouping_limit": "CF episode linkage unavailable; shared template families conservatively merged",
                },
            )
            result = baselines(bundle)
            for method, value in result.items():
                output_counts[(key, method, "rows")] += 1
                output_counts[(key, method, "emitted_parsed_claims")] += len(
                    value.claims
                )
                output_counts[(key, method, "fallbacks")] += not bool(value.claims)
                output_counts[(key, method, "unresolved_outputs")] += bool(
                    value.unresolved
                )
                output_counts[(key, method, "exact_text_preserved")] += (
                    value.text == row.explanation
                )
                append(
                    outputs,
                    {
                        "input_id": bundle.id,
                        "result": value.model_dump(),
                        "evaluation_status": "No gold repairs or independent natural-language repair judge; output/support labels are conditional software diagnostics only",
                    },
                )
            if len(examples) < 8 and (bundle.claims or dataset == "RoboFail"):
                examples.append(
                    {
                        "id": bundle.id,
                        "original": row.explanation,
                        "original_coherence_labels": [
                            row.label,
                            row.L_plan_exp,
                            row.L_obs_exp,
                        ],
                        "covered_spans": extraction.covered_spans,
                        "total_spans": extraction.spans,
                        "outputs": {m: v.text for m, v in result.items()},
                        "unparsed": extraction.unparsed,
                    }
                )
    save(
        target / "public_summary.json",
        {
            "rows": len(all_rows),
            "schema_errors": errors,
            "groups": len(set(groups)),
            "strata": {k: dict(v) for k, v in summaries.items()},
            "method_outputs": [
                {
                    "stratum": k,
                    "method": m,
                    **{
                        name: output_counts[(k, m, name)]
                        for name in [
                            "rows",
                            "emitted_parsed_claims",
                            "fallbacks",
                            "unresolved_outputs",
                            "exact_text_preserved",
                        ]
                    },
                }
                for k in summaries
                for m in [
                    "original",
                    "generic",
                    "delete",
                    "regenerate",
                    "proposed",
                    "no_temporal",
                    "no_action_model",
                ]
            ],
            "independent_gold_repair_evaluation": "NOT_AVAILABLE",
            "coherence_labels_changed": False,
            "train_test_split": "NONE: first-session descriptive development only",
        },
    )
    save(target / "public_examples.json", examples)


def trace_comparisons(root, target, config):
    old = Path(config["historical_root"])
    historical_manifest = read(old / "completion_manifest.json")
    inventory = historical_manifest["sha256"]
    registration = read(old / "registration.json")
    paired = {
        (p["task"], p["parent"], p["condition"]): p
        for p in read(old / "paired_certificate_index.json")
        if p["split"] == "confirmation"
    }
    sources, sensitivities, cell_rows, timing = [], [], [], []
    source_hashes = {}

    def verified(path):
        relative = str(path.relative_to(old))
        actual = sha(path)
        assert actual == inventory[relative], relative
        source_hashes[str(path)] = actual
        return path

    verified(old / "registration.json")
    verified(old / "paired_certificate_index.json")
    with (
        (target / "trace_inputs.jsonl").open("w") as inputs,
        (target / "trace_outputs.jsonl").open("w") as outputs,
    ):
        for task, conditions, count in [
            (
                "PickCube-v1",
                ["nominal", "offset002"],
                config["development_parents_per_task"],
            ),
            (
                "PushCube-v1",
                ["nominal", "misaligned"],
                config["development_parents_per_task"],
            ),
            ("Lift", ["nominal"], config["lift_preservation_parents"]),
        ]:
            for seed in registration["seeds"][task]["confirmation"][:count]:
                for condition in conditions:
                    source = verified(
                        old
                        / f"parents/confirmation/{task}/{seed}-{condition}/traces.json.gz"
                    )
                    parent = paired[(task, str(seed), condition)]
                    assert parent["status"] == "SUPPORTED"
                    for name in [
                        parent["bundle"],
                        parent["certificate"],
                        *parent["branch_bundles"],
                    ]:
                        verified(old / name)
                    assert read(old / parent["certificate"])["status"] == "SUPPORTED"
                    with gzip.open(source, "rt") as stream:
                        raw = json.load(stream)
                    branches = {
                        a: raw["traces"][a + "/reference"]
                        for a in ["continue", "recover"]
                    }
                    assert all(
                        t["prefix_ok"]
                        and len(t["frames"]) == 70
                        and len(t["actions"]) == 70
                        for t in branches.values()
                    )
                    identifier = f"{task}/{seed}/{condition}"
                    base = trace_bundle(raw, task, identifier)
                    actual = {
                        a: bool(t["frames"][-1]["state"]["success"])
                        for a, t in branches.items()
                    }
                    first_hits = {
                        a: not bool(t["start"]["success"])
                        and any(f["state"]["success"] for f in t["frames"])
                        for a, t in branches.items()
                    }
                    cell = {
                        "id": identifier,
                        "task": task,
                        "seed": seed,
                        "condition": condition,
                        "source": str(source),
                        "source_sha256": source_hashes[str(source)],
                        "qualified_pair": str(old / parent["bundle"]),
                        "old_partition": "confirmation",
                        "new_partition": "development-reused",
                        "outcomes": actual,
                        "new_first_hits": first_hits,
                        "initial_success": bool(
                            branches["continue"]["start"]["success"]
                        ),
                        "physical_continuations_new": 0,
                    }
                    cell_rows.append(cell)
                    sources.append(cell)
                    for variant, bundle in variants(base):
                        append(
                            inputs,
                            {
                                "id": bundle.id,
                                "cell": identifier,
                                "variant": variant,
                                "input": bundle.model_dump(),
                                "source": str(source),
                                "generator": "frozen deterministic templates"
                                if variant == "unedited_template"
                                else "declared controlled development variant",
                            },
                        )
                        started = time.perf_counter()
                        results = baselines(bundle)
                        elapsed = time.perf_counter() - started
                        timing.append(
                            {"id": bundle.id, "all_seven_methods_seconds": elapsed}
                        )
                        for method, result in results.items():
                            selected = select_action(task, bundle, result)
                            append(
                                outputs,
                                {
                                    "input_id": bundle.id,
                                    "cell": identifier,
                                    "variant": variant,
                                    "method": method,
                                    "result": result.model_dump(),
                                    "selected_action": selected,
                                    "actual_success": actual.get(selected),
                                    "new_first_hit": first_hits.get(selected),
                                    "action_controls": 0
                                    if selected == "abstain"
                                    else 70,
                                    "simulated_action_seconds": 0
                                    if selected == "abstain"
                                    else 3.5,
                                },
                            )
                        if variant == "unedited_template":
                            for method in [
                                "full_evidence_no_explanation",
                                "direct_structured_evidence",
                            ]:
                                selected = select_action(task, bundle)
                                append(
                                    outputs,
                                    {
                                        "input_id": bundle.id,
                                        "cell": identifier,
                                        "variant": variant,
                                        "method": method,
                                        "result": None,
                                        "selected_action": selected,
                                        "actual_success": actual.get(selected),
                                        "new_first_hit": first_hits.get(selected),
                                        "action_controls": 0
                                        if selected == "abstain"
                                        else 70,
                                        "simulated_action_seconds": 0
                                        if selected == "abstain"
                                        else 3.5,
                                    },
                                )
                        for weight in config["sensitivity_loss_weights"]:
                            result = edit(
                                bundle,
                                Objective.model_validate(
                                    config["objective"]
                                    | {"supported_fact_loss": weight}
                                ),
                            )
                            sensitivities.append(
                                {
                                    "input_id": bundle.id,
                                    "loss_weight": weight,
                                    "operations": [
                                        d.operation for d in result.decisions
                                    ],
                                    "same_as_frozen_default": [
                                        d.operation for d in result.decisions
                                    ]
                                    == [
                                        d.operation
                                        for d in results["proposed"].decisions
                                    ],
                                }
                            )
    save(target / "physical_sources.json", sources)
    save(target / "historical_members_used.json", source_hashes)
    save(target / "sensitivity.json", sensitivities)
    save(
        target / "runtime.json",
        {
            "bundles": len(timing),
            "total_seconds_all_methods": sum(
                t["all_seven_methods_seconds"] for t in timing
            ),
            "per_bundle_all_methods": timing,
            "scope": "All seven deterministic editor/baseline executions; JSON serialization, raw I/O, audit and process startup accounted separately by worker",
        },
    )
    return len(cell_rows)


def run(root: Path, attempt: str):
    target = root / attempt
    target.mkdir(exist_ok=False)
    config = read(Path("config/explanation_repair.json"))
    save(
        target / "frozen_specification.json",
        {
            "config": config,
            "sha256": {
                str(p): sha(p)
                for p in [
                    Path("EXPLANATION_REPAIR_PROTOCOL.md"),
                    Path("config/explanation_repair.json"),
                    *sorted(Path("src/dual_rec/explanation_repair").glob("*.py")),
                ]
            },
            "inference": "development only; no held-out confirmation",
        },
    )
    worked = []
    (target / "worked_inputs").mkdir()
    for case in worked_cases():
        save(target / "worked_inputs" / (case.id + ".json"), case.model_dump())
        outputs = baselines(case)
        worked.append(
            {
                "id": case.id,
                "input": case.model_dump(),
                "outputs": {k: v.model_dump() for k, v in outputs.items()},
                "initial_statuses": [assess(case, c).model_dump() for c in case.claims],
            }
        )
    save(target / "worked_cases.json", worked)
    public_comparisons(root, target)
    cells = trace_comparisons(root, target, config)
    save(
        target / "language_baselines.json",
        {
            "contradiction_reprompt": "NOT_RUN_IN_THIS_STRUCTURED_BATCH",
            "RARR_style": "NOT_RUN_IN_THIS_STRUCTURED_BATCH",
            "fresh_language_generator": "NOT_RUN_IN_THIS_STRUCTURED_BATCH",
            "reason": "This batch runs deterministic comparisons only. Consult the evidence-root language_backend_discovery.json and language/ outputs for separately qualified language diagnostics; no absence-of-weights claim is made here.",
            "generation_used": "Existing unedited public expert/GPT examples and explicitly deterministic simulator templates",
        },
    )
    save(
        root / "latest_development.json",
        {
            "attempt": attempt,
            "path": str(target),
            "cells": cells,
            "status": "COMPLETED_DEVELOPMENT_RUN",
            "new_physics": 0,
        },
    )
    print(
        {
            "attempt": attempt,
            "physical_cells_reused": cells,
            "public": read(target / "public_summary.json")["rows"],
            "new_physics": 0,
        }
    )
