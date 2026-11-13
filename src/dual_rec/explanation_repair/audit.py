"""Independent raw-trace metric implementation; no editor/support imports."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def identity(claim):
    fact = claim["fact"]
    return (
        claim["kind"],
        None if fact is None else (fact["entity"], fact["predicate"], fact["value"]),
        claim["window"]["clock"],
        claim["window"]["start"],
        claim["window"]["end"],
        claim["action"],
    )


def raw_truth(raw, task):
    truth = {}
    reference = raw["traces"]["continue/reference"]
    for state in [reference["prefix_history"][0], reference["start"]]:
        time = state["time"]
        if task == "Lift":
            truth[("cube", "grasped", time)] = bool(state["is_grasped"])
            continue
        obs = state["observation"]["extra"]
        if task == "PickCube-v1":
            truth[("cube", "grasped", time)] = bool(obs["is_grasped"][0])
        # Evaluator uses recorded physical position and an observed task target,
        # rather than the editor projection or its boolean support labels.
        position = state["position"]
        observed = obs["obj_pose"][0][:3]
        assert max(abs(a - b) for a, b in zip(position, observed, strict=True)) < 1e-6
        goal = obs["goal_pos"][0][:3]
        truth[("cube", "near_goal", time)] = math.dist(position, goal) <= 0.03
        contact = any(
            ("cube" in str(a) and "panda" in str(b))
            or ("cube" in str(b) and "panda" in str(a))
            for a, b in state["contacts"]
        )
        assert contact == state["robot_object_contact"]
        truth[("robot", "contact", time)] = contact
    return truth


def true_claim(claim, truth, task):
    window = claim["window"]
    if window["clock"] != "seconds" or window["start"] != window["end"]:
        return None
    fact = claim["fact"]
    if fact is None or claim["kind"] == "hypothesis":
        return None
    time = window["start"]
    if claim["kind"] == "observation":
        target = (fact["entity"], fact["predicate"], time)
        return None if target not in truth else truth[target] == fact["value"]
    if (
        claim["action"] != "transport"
        or fact["entity"] != "transport"
        or fact["predicate"] != "applicable"
    ):
        return None
    key = (
        ("robot", "contact", time)
        if task == "PushCube-v1"
        else ("cube", "grasped", time)
    )
    if key not in truth:
        return None
    if claim["kind"] == "recommendation" and not truth[key]:
        return False
    return fact["value"] == truth[key]


def unique_claims(claims):
    return {identity(c): c for c in claims}


def factual_claims(claims):
    # A declared hypothesis is not an asserted observation or an established
    # causal fact. Its unresolved status is reported separately, not added to a
    # favorable factual-error denominator for the editor.
    return unique_claims([c for c in claims if c["kind"] != "hypothesis"])


def temporal_error(claim, truth):
    if claim["kind"] != "observation" or claim["fact"] is None:
        return False
    fact = claim["fact"]
    current = (fact["entity"], fact["predicate"], claim["window"]["start"])
    return (
        current in truth
        and truth[current] != fact["value"]
        and any(
            e == fact["entity"]
            and p == fact["predicate"]
            and t != current[2]
            and v == fact["value"]
            for (e, p, t), v in truth.items()
        )
    )


def public_integrity(root, target):
    original = {
        dataset + "/" + r["task_id"]: r
        for dataset, filename in [
            ("RoboFail", "RoboFail_generated.json"),
            ("CounterFactual", "CounterFactual_generated.json"),
        ]
        for r in load(root / "upstream/data" / filename)
    }
    episodes, families, aliases = {}, {}, {}
    totals = defaultdict(Counter)
    seen = set()
    for row in rows(target / "public_inputs.jsonl"):
        assert row["original"] == original[row["id"]] | (
            {"comment": None} if "comment" not in original[row["id"]] else {}
        )
        assert row["partition"] == "development-interface-only"
        assert row["input"]["query"] == {"clock": "snapshot", "start": 0.0, "end": 0.0}
        assert not row["input"]["model"]["rules"]
        extraction = row["extraction"]
        assert (
            extraction["covered_spans"] + len(extraction["unparsed"])
            == extraction["spans"]
        )
        assert len(row["input"]["claims"]) == len(extraction["claims"])
        record = row["original"]
        total = totals[row["dataset"] + "/" + row["generation"]]
        total.update(
            rows=1,
            spans=extraction["spans"],
            covered_spans=extraction["covered_spans"],
            fully_extracted=int(extraction["spans"] > 0 and not extraction["unparsed"]),
        )
        total["label_" + record["label"]] += 1
        identifier = record["task_id"]
        if row["dataset"] == "RoboFail":
            episode = identifier.split("_gt_")[0].split("_pred_")[0]
            assert episodes.setdefault(episode, row["group"]) == row["group"]
        else:
            family = identifier.split("autogen_", 1)[-1][:-2]
            assert families.setdefault(family, row["group"]) == row["group"]
        alias = json.dumps(
            [record["plan_until_failure"], record["observation"]], sort_keys=True
        )
        assert aliases.setdefault(alias, row["group"]) == row["group"]
        assert row["id"] not in seen
        seen.add(row["id"])
    assert seen == set(original)
    output_count = sum(1 for _ in rows(target / "public_outputs.jsonl"))
    assert output_count == len(original) * 7
    return {
        "status": "PASS_COUNTS_AND_SOURCE_INTEGRITY",
        "records": len(seen),
        "output_rows": output_count,
        "strata": {k: dict(v) for k, v in totals.items()},
        "gold_repair_quality": "NOT_ASSESSED: gold repairs and independent natural-language semantic annotation unavailable",
        "grouping": "No split; episode/template/exact-input aliases share conservative development groups",
    }


def run(root: Path):
    target = Path(load(root / "latest_development.json")["path"])
    cells = load(target / "physical_sources.json")
    truth_by_cell, cell_info = {}, {}
    raw_checks = 0
    for cell in cells:
        path = Path(cell["source"])
        assert digest(path) == cell["source_sha256"]
        with gzip.open(path, "rt") as stream:
            raw = json.load(stream)
        truth_by_cell[cell["id"]] = raw_truth(raw, cell["task"])
        cell_info[cell["id"]] = cell
        for action in ["continue", "recover"]:
            trace = raw["traces"][action + "/reference"]
            assert trace["prefix_ok"] and len(trace["actions"]) == 70
            assert trace["frames"][-1]["state"]["success"] == cell["outcomes"][action]
            assert (
                abs(trace["frames"][-1]["state"]["time"] - trace["start"]["time"] - 3.5)
                < 1e-6
            )
            assert cell["new_first_hits"][action] == (
                not trace["start"]["success"]
                and any(f["state"]["success"] for f in trace["frames"])
            )
            raw_checks += 1
    inputs = {r["id"]: r for r in rows(target / "trace_inputs.jsonl")}
    for row in inputs.values():
        truth = truth_by_cell[row["cell"]]
        for record in row["input"]["records"]:
            if record["kind"] == "observation":
                fact = record["fact"]
                assert (
                    truth[
                        (fact["entity"], fact["predicate"], record["window"]["start"])
                    ]
                    == fact["value"]
                )
    scores = defaultdict(Counter)
    recovery = defaultdict(Counter)
    paired = defaultdict(dict)
    violations = []
    examples = []
    emitted_checked = 0
    hypotheses_emitted = 0
    historical_renderings_checked = 0
    result_rows = 0
    for row in rows(target / "trace_outputs.jsonl"):
        result_rows += 1
        data = inputs[row["input_id"]]
        bundle = data["input"]
        cell = cell_info[row["cell"]]
        task = cell["task"]
        truth = truth_by_cell[cell["id"]]
        query = bundle["query"]["start"]
        observation = (
            truth[("cube", "grasped", query)]
            if task == "PickCube-v1"
            else truth[("robot", "contact", query)]
            if task == "PushCube-v1"
            else True
        )
        expected_action = "continue" if observation else "recover"
        assert row["selected_action"] == expected_action
        assert row["actual_success"] == cell["outcomes"][expected_action]
        assert row["action_controls"] == 70 and row["simulated_action_seconds"] == 3.5
        key = (task, cell["condition"], row["variant"], row["method"])
        r = recovery[key]
        r.update(
            cells=1,
            selected_success=int(row["actual_success"]),
            continue_success=int(cell["outcomes"]["continue"]),
            selected_recover=int(expected_action == "recover"),
            harm_vs_continue=int(
                not row["actual_success"] and cell["outcomes"]["continue"]
            ),
            benefit_vs_continue=int(
                row["actual_success"] and not cell["outcomes"]["continue"]
            ),
            abstain=0,
            controls=70,
        )
        paired[(task, row["variant"], row["cell"])][row["method"]] = row[
            "actual_success"
        ]
        if row["result"] is None:
            continue
        result = row["result"]
        for grounded in result["claims"]:
            window = grounded["claim"]["window"]
            if window != bundle["query"]:
                assert f"At t={window['start']:g} s," in result["text"]
                historical_renderings_checked += 1
        original = factual_claims(bundle["claims"])
        supported = {
            k for k, c in original.items() if true_claim(c, truth, task) is True
        }
        output = factual_claims([g["claim"] for g in result["claims"]])
        hypotheses = len(
            unique_claims(
                [
                    g["claim"]
                    for g in result["claims"]
                    if g["claim"]["kind"] == "hypothesis"
                ]
            )
        )
        hypotheses_emitted += hypotheses
        factual = {k: true_claim(c, truth, task) for k, c in output.items()}
        errors = sum(v is not True for v in factual.values())
        s = scores[(task, row["variant"], row["method"])]
        correct_input = (
            bool(original)
            and len(supported) == len(original)
            and not bundle["unparsed"]
        )
        s.update(
            inputs=1,
            causal_hypotheses_emitted=hypotheses,
            emitted_unique_claims=len(output),
            unsupported_assertions=errors,
            contradicted_assertions=sum(v is False for v in factual.values()),
            unverified_assertions=sum(v is None for v in factual.values()),
            original_supported_unique=len(supported),
            original_supported_retained=len(supported & set(output)),
            informative_outputs=int(any(v is True for v in factual.values())),
            fallbacks=int(not output),
            temporal_errors=sum(temporal_error(c, truth) for c in output.values()),
            correct_inputs=int(correct_input),
            correct_input_exact_text_preserved=int(
                correct_input and result["text"] == bundle["original_text"]
            ),
            unassessed_original_text_spans=len(bundle["unparsed"])
            if result["text"] == bundle["original_text"]
            else 0,
        )
        emitted_checked += len(output)
        if row["method"] == "proposed":
            if errors:
                violations.append(
                    {
                        "input": row["input_id"],
                        "kind": "independently unsupported proposed assertion",
                        "errors": errors,
                    }
                )
            ids = {x["id"]: x for x in bundle["records"]}
            for g in result["claims"]:
                assert g["support"]["evidence"] and all(
                    i in ids and ids[i]["kind"] == "observation"
                    for i in g["support"]["evidence"]
                )
            assert result["max_menu_size"] <= 4
            assert len(result["decisions"]) == len(bundle["claims"])
            if len(examples) < 10 and row["variant"] in [
                "partial_flip",
                "unsupported",
                "historical_correct",
            ]:
                examples.append(
                    {
                        "id": row["input_id"],
                        "original": bundle["original_text"],
                        "repaired": result["text"],
                        "unresolved": result["unresolved"],
                        "support_identifiers": [g["support"] for g in result["claims"]],
                        "selected": row["selected_action"],
                        "reused_actual_success": row["actual_success"],
                    }
                )
    score_rows = []
    for (task, variant, method), counts in sorted(scores.items()):
        values = dict(counts)
        values["unsupported_assertion_rate"] = (
            counts["unsupported_assertions"] / counts["emitted_unique_claims"]
            if counts["emitted_unique_claims"]
            else None
        )
        values["supported_fact_retention"] = (
            counts["original_supported_retained"] / counts["original_supported_unique"]
            if counts["original_supported_unique"]
            else None
        )
        score_rows.append(
            {"task": task, "variant": variant, "method": method, **values}
        )
    write(target / "independent_claim_metrics.json", score_rows)
    write(
        target / "independent_recovery_metrics.json",
        [
            {"task": t, "condition": c, "variant": v, "method": m, **dict(counts)}
            for (t, c, v, m), counts in sorted(recovery.items())
        ],
    )
    deltas = []
    for task in sorted({c["task"] for c in cells}):
        for method in [
            "original",
            "generic",
            "delete",
            "regenerate",
            "full_evidence_no_explanation",
            "direct_structured_evidence",
        ]:
            values = [
                int(v["proposed"]) - int(v[method])
                for (t, variant, _), v in paired.items()
                if t == task and variant == "unedited_template"
            ]
            deltas.append(
                {
                    "task": task,
                    "comparator": method,
                    "condition_cells": len(values),
                    "paired_success_difference": sum(values) / len(values),
                    "discordant_cells": sum(v != 0 for v in values),
                    "scope": "Development reused outcomes; identical observation-dominant selector makes explanation conditions identical by construction, not a confirmation equivalence test",
                }
            )
    write(target / "paired_recovery_comparisons.json", deltas)
    write(target / "repair_examples.json", examples)
    public = public_integrity(root, target)
    write(target / "independent_public_integrity.json", public)
    old = Path(load(Path("config/explanation_repair.json"))["historical_root"])
    seal = load(old / "completion_manifest.json")["sha256"]
    for name, expected in load(target / "historical_members_used.json").items():
        assert digest(Path(name)) == expected == seal[str(Path(name).relative_to(old))]
    for name, expected in load(target / "frozen_specification.json")["sha256"].items():
        assert digest(Path(name)) == expected
    write(
        target / "independent_audit.json",
        {
            "status": "PASS",
            "raw_cells": len(cells),
            "actual_reference_continuations_checked": raw_checks,
            "trace_input_variants": len(inputs),
            "result_rows": result_rows,
            "unique_emitted_assertions_evaluated": emitted_checked,
            "causal_hypotheses_counted_separately": hypotheses_emitted,
            "historical_text_time_qualifiers_checked": historical_renderings_checked,
            "proposed_soundness_violations": violations,
            "public_records_checked": public["records"],
            "historical_source_members_verified": len(
                load(target / "historical_members_used.json")
            ),
            "scope": "Separate raw-state/contact/time/outcome interpreter and metrics, not editor support labels; grasp sensor/recording trust and fixed grounding remain assumptions; public gold semantic repairs and human evaluation unavailable",
        },
    )
    print(load(target / "independent_audit.json"))
