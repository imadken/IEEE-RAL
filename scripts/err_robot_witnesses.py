"""D/C-only robot context witnesses; no test/evaluator source is readable."""

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
from dsre_closure_common import (
    INPUTS,
    TASKS,
    b7_certificate,
    calibrated,
    canonical,
    matching_scope,
    passed,
    paths,
    read,
    route,
)
from dsre_source_risk_audit import predicates, vec
from err_cases import problem, source
from err_independent_oracle import exhaustive, greedy, verify_witnesses

from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.evidence_resolution import resolve_evidence
from dual_rec.evidence_aware.experiment_resolvability import (
    minimum_resolving_experiments,
)
from dual_rec.evidence_aware.schema import Bounds, Certificate, Partition, Scope, Source
from dual_rec.evidence_aware.views import guard_data_access


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def phase_paths(task, phase):
    p = paths(task)
    learner = p["base"] / (
        f"learner/{phase}.json" if task == "PushCube-v1" else f"learner_records/{phase}"
    )
    records = p["base"] / (f"records/{phase}" if task == "PushCube-v1" else phase)
    return learner, records


def certificate(model, x, obligation="useful"):
    return minimum(
        Partition.model_validate(model["partition"]),
        x,
        {
            int(c): Bounds.model_validate(v["bounds"])
            for c, v in model["leaves"].items()
            if v["bounds"]
        },
        Source.LOGGED,
        obligation,
        outcome_scope=Scope.model_validate(model["source_scope"]),
    )


def native_context(task, row, phase):
    p = paths(task)
    _, records = phase_paths(task, phase)
    metadata = next(
        r
        for r in (read(f) for f in sorted(records.glob("*.json")))
        if r.get("parent_id", r.get("record", {}).get("parent_id")) == row["parent_id"]
    )
    name = "assigned" if task == "PushCube-v1" else "randomized_assigned"
    raw_path = (
        p["physics"] / phase / str(metadata["spec"]["index"]) / (name + ".json.gz")
    )
    raw = read(raw_path)
    first, current = raw["prefix"][0]["observation"], raw["checkpoint"]["observation"]
    primary, _ = predicates(first, current)
    assert primary == raw["features"] == row["x"]
    controls = len(raw["prefix_controls"])
    assert (70 <= controls <= 90) if task == "PickCube-v1" else controls == 53
    return {
        "parent_id": row["parent_id"],
        "phase": phase,
        "x": row["x"],
        "native": str(raw_path),
        "original_gzip_sha256": INPUTS[str(raw_path)],
        "spec": metadata["spec"],
        "source_scope": row["source_scope"],
        "assigned_action_only": row["action"],
        "alternative_outcome_available_to_learner": False,
        "predecision_time": raw["checkpoint"]["time"],
        "prefix_controls": controls,
        "object_position": vec(current, "obj_pose").tolist(),
        "hand_position": vec(current, "tcp_pose").tolist(),
        "goal_position": vec(current, "goal_pos").tolist(),
        "goal_distance": float(
            np.linalg.norm(vec(current, "obj_pose") - vec(current, "goal_pos"))
        ),
        "hand_object_distance": float(
            np.linalg.norm(vec(current, "tcp_pose") - vec(current, "obj_pose"))
        ),
        "interpretation": "Actual native predecision telemetry and one assigned D/C outcome; no alternative/test label read",
    }


def context_problem(model, x, missing, anchors):
    partial = tuple(None if i == missing else value for i, value in enumerate(x))
    completions = [
        z
        for z in itertools.product((False, True), repeat=6)
        if all(value is None or value == z[i] for i, value in enumerate(partial))
    ]
    population = model["source_scope"]["task"] + ":FROZEN_REGION_CONTEXT_PREDICATE"
    worlds, mapping = [], []
    actual = {tuple(a["x"]): a for a in anchors}
    for index, z in enumerate(completions):
        leaf = model["leaves"][str(route(model["partition"], z))]
        good = passed(leaf["bounds"], "useful")
        if not good:
            assert (
                leaf["bounds"]["gain_upper"] < 0.05
                or leaf["bounds"]["harm_lower"] > 0.10
            )
        name = f"context{index}"
        worlds.append({"world_id": name, "obligation_verdict": good})
        mapping.append(
            {
                "world_id": name,
                "x": z,
                "region": route(model["partition"], z),
                "verdict_semantics": "Frozen whole-leaf qualification/refutation on its original simultaneous event; NOT individual success or a known causal joint Q",
                "native_anchor": actual.get(tuple(z)),
                "origin": "ACTUALLY_RECORDED_PREDECISION_CONTEXT"
                if tuple(z) in actual
                else "LOGICAL_BOOLEAN_COMPLETION_NOT_A_ROBOT_EPISODE",
            }
        )
    name = model["partition"]["vocabulary"][missing]
    all_actual = all(row["native_anchor"] is not None for row in mapping)
    experiment = {
        "experiment_id": "reveal_" + name,
        "cost": 1,
        "alphabet": ("False", "True"),
        "laws": [
            {
                "world_id": row["world_id"],
                "probabilities": (int(not row["x"][missing]), int(row["x"][missing])),
            }
            for row in mapping
        ],
        "source": source(
            "predecision_observation",
            population,
            provenance=tuple(
                a["native"] + ":" + a["original_gzip_sha256"] for a in anchors
            )
            + (
                "Original frozen Boolean partition and registered predicate definition",
            ),
            participant_sampling="FIXED_CONTEXT_READ"
            if all_actual
            else "DECLARED_ANALYTICAL",
            law_origin="RECORDED_PREDECISION_FACTS"
            if all_actual
            else "KNOWN_ANALYTICAL_MODEL",
            context_operation="CONTEXT_REFINEMENT",
            recorded_channels=(name,),
            observation_timing="PREDECISION",
        ),
    }
    p = problem(
        worlds,
        [experiment],
        population=population,
        cost_unit="ONE_REGISTERED_RECORDED_FACT_LOOKUP_NOT_MEASURED_SENSOR_COST",
    )
    return partial, p, mapping


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    registration_path = Path("research/err_method_challenge/registration.json")
    allowed = [registration_path]
    for task in TASKS:
        p = paths(task)
        allowed.extend([p["model"], p["discovery"]])
        for phase in ("discovery", "calibration"):
            learner, records = phase_paths(task, phase)
            allowed.extend(
                sorted(learner.glob("*.json")) if learner.is_dir() else [learner]
            )
            allowed.extend(sorted(records.glob("*.json")))
            stem = "assigned" if task == "PushCube-v1" else "randomized_assigned"
            allowed.extend((p["physics"] / phase).glob("*/" + stem + ".json.gz"))
            for archived in (p["physics"] / phase).glob("*/" + stem + ".json.xz"):
                allowed.extend(
                    [
                        archived,
                        archived.with_suffix(".gz"),
                        Path(str(archived.with_suffix(".gz")) + ".archive.json"),
                    ]
                )
    accesses = guard_data_access(
        Path("results"),
        allowed,
        additional_roots=(
            Path("research/err_method_challenge"),
            Path("research/dsre_experimental_closure"),
        ),
    )
    registration = read(registration_path)
    tasks = {}
    for task in TASKS:
        model = read(paths(task)["model"])
        assert model["partition"] == read(paths(task)["discovery"])["partition"]
        logs, phase_by_parent = [], {}
        for phase in ("discovery", "calibration"):
            learner, _ = phase_paths(task, phase)
            phase_rows = (
                [read(f) for f in sorted(learner.glob("*.json"))]
                if learner.is_dir()
                else read(learner)
            )
            assert len(phase_rows) == (128 if phase == "discovery" else 1024)
            logs.extend(phase_rows)
            phase_by_parent.update({r["parent_id"]: phase for r in phase_rows})
        assert len({r["parent_id"] for r in logs}) == 1152
        positive, negative = [], []
        for row in logs:
            leaf = model["leaves"][str(route(model["partition"], row["x"]))]
            (positive if passed(leaf["bounds"], "useful") else negative).append(row)
        root = 0 if task == "PickCube-v1" else 1
        candidates = [
            (a, b)
            for a in positive
            for b in negative
            if a["x"][root] != b["x"][root]
            and all(a["x"][j] == b["x"][j] for j in range(6) if j != root)
        ]
        if not candidates:
            candidates = [
                (a, b)
                for a in positive
                for b in negative
                if a["x"][root] != b["x"][root]
            ]
        a, b = min(
            candidates,
            key=lambda rows: digest(
                registration["physical_context_selection_namespace"]
                + task
                + rows[0]["parent_id"]
                + rows[1]["parent_id"]
            ),
        )
        anchors = [
            native_context(task, row, phase_by_parent[row["parent_id"]])
            for row in (a, b)
        ]
        partial, p, mapping = context_problem(model, a["x"], root, anchors)
        selected = certificate(model, a["x"])
        assert selected is not None and certificate(model, partial) is None
        ordinary = Certificate.model_validate(b7_certificate(model, a["x"], "useful"))
        assert canonical(selected.model_dump(mode="json")) == canonical(
            ordinary.model_dump(mode="json")
        )
        full_answer = resolve_evidence(certificate=selected)
        b7_answer = resolve_evidence(certificate=ordinary)
        assert full_answer == b7_answer
        plan = minimum_resolving_experiments(p)
        assert (plan.total_cost, plan.selected_experiments) == exhaustive(
            p.model_dump(mode="json")
        )
        verify_witnesses(p.model_dump(mode="json"), plan.model_dump(mode="json"))
        assert plan.total_cost == Fraction(1)
        contextual = resolve_evidence(problem=p)
        ordinary_partial = b7_certificate(model, partial, "useful")
        assert ordinary_partial is None
        b7_with_planner = resolve_evidence(certificate=ordinary_partial, problem=p)
        assert contextual == b7_with_planner
        approved = {
            int(c)
            for c, leaf in model["leaves"].items()
            if passed(leaf["bounds"], "useful")
        }
        removals = []
        indices = tuple(
            (model["partition"]["vocabulary"].index(name), value)
            for name, value in selected.evidence
        )
        for removed, value in indices:
            admitted = matching_scope(
                model["partition"], tuple(v for v in indices if v[0] != removed)
            )
            bad = [] if admitted is None else sorted(set(admitted) - approved)
            assert admitted is None or bad
            removals.append(
                {
                    "removed": [model["partition"]["vocabulary"][removed], value],
                    "new_scope": admitted,
                    "forbidden_split": admitted is None,
                    "bad_whole_cells": {str(c): model["leaves"][str(c)] for c in bad},
                    "countermodel_type": "CALIBRATION_COMPATIBLE_ANALYTICAL_DISTRIBUTIONS_NOT_ROBOT_EPISODES",
                }
            )
        exhaustive_certificates = 0
        for x in itertools.product((False, True), repeat=6):
            for obligation in ("harm_only", "completion", "useful"):
                c = certificate(model, x, obligation)
                b7 = b7_certificate(model, x, obligation)
                assert canonical(c.model_dump(mode="json") if c else None) == canonical(
                    b7
                )
                exhaustive_certificates += 1
        underpowered = []
        for cell in approved:
            small = sorted(
                [
                    r
                    for r in logs
                    if phase_by_parent[r["parent_id"]] == "calibration"
                    and route(model["partition"], r["x"]) == cell
                ],
                key=lambda row: digest("ERR-SAMPLE-SUPPORT-v1" + row["parent_id"]),
            )[:8]
            fitted = calibrated(small, [], len(model["leaves"]), cell)
            if not passed(fitted["bounds"], "useful"):
                underpowered.append(
                    {
                        "whole_leaf": cell,
                        "evidence": fitted,
                        "type": "SOURCE_OR_STATISTICAL_SUPPORT_MISSING_NOT_MENU_IMPOSSIBILITY",
                        "source_parent_ids": [r["parent_id"] for r in small],
                    }
                )
        tasks[task] = {
            "source_scope": model["source_scope"],
            "D_parents": 128,
            "C_parents": 1024,
            "actual_predecision_anchors": anchors,
            "partial_packet": partial,
            "declared_context_problem": p.model_dump(mode="json"),
            "context_world_provenance": mapping,
            "context_output": contextual.model_dump(mode="json"),
            "B7_with_identical_planner_output": b7_with_planner.model_dump(mode="json"),
            "identifying_type_cost": str(plan.total_cost),
            "original_full_packet_output": full_answer.model_dump(mode="json"),
            "actual_assigned_action": a["action"],
            "frozen_policy_proposal": "r",
            "new_intervention_executed": False,
            "B7_full_original_certificate_equal": True,
            "B7_identical_planner_equal": True,
            "direct_ID_same_menu_and_processor_equal": True,
            "greedy_plan": str(greedy(p.model_dump(mode="json"))),
            "literal_removal_countermodels": removals,
            "complete_Boolean_certificate_comparisons": exhaustive_certificates,
            "small_sample_support_cases": underpowered,
            "physical_paired_only_obligation": "NOT_ESTABLISHED; causal joint-world experiments remain separately analytical",
            "repertoire_evidence_in_this_view": "D/C one-arm records do not expose paired both-failure endpoints; no repertoire label imputed",
            "interpretation": "Retrospective recorded-fact/context capability, not a new sensor, new rollout, minimum noisy-trial budget or individual success guarantee",
        }
        print(
            task,
            "native anchors",
            [r["parent_id"] for r in anchors],
            "context plan",
            plan.selected_experiments,
            flush=True,
        )
    assert all(
        "/test/" not in p and "evaluator" not in p and "counterpart" not in p
        for p in accesses
    )
    result = {
        "passed": True,
        "tasks": tasks,
        "successful_reads": list(accesses),
        "input_sha256": dict(INPUTS),
        "learner_evaluator_separation": "Isolated whitelist contains only original D/C learner inputs, frozen models, D/C assigned native branches and registered facts; all test/evaluator/counterpart paths excluded",
        "new_physics": 0,
        "new_physical_sample_count": 0,
    }
    (output / "robot_context_witnesses.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("research/err_method_challenge/results")
    )
    run(parser.parse_args().output)
