"""Read-only source audit and post hoc STOP sensitivity on frozen DSRE decisions."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_final_analysis import audit_rows
from dsre_final_audit import numerical
from dsre_final_verify import load_trace, verify_sources
from dsre_followup_batch import atomic, read
from dsre_operational_analysis import qualified
from dsre_paper_confirmation import predicates
from pydantic import BaseModel, ConfigDict

PRIOR = Path("results/dsre-operational/20261114T180630Z")
REFERENCE = Path("results/dsre-evidence-repair/20261113T180828Z/qualified_pairs.jsonl")
TASKS = ("PickCube-v1", "PushCube-v1")


class SecondaryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: str = "POST_HOC_SECONDARY_NOT_NEW_CONFIRMATION"
    compositions: tuple[str, ...] = ("primary", "fallback_continue", "fallback_recover")
    bootstrap_draws: int = 4000
    bootstrap_seed: int = 2026111401
    hold_interpretation: str = (
        "Count success at defer only; terminal hold outcome unmeasured"
    )
    guarantee: str = (
        "Fallbacks unqualified; no inheritance of original risk eligibility"
    )
    new_physics: int = 0
    new_fits: int = 0


def counts(rows, composition="primary"):
    """Keep observed defer state distinct from both measured action outcomes."""
    result = dict.fromkeys(
        (
            "N",
            "parents",
            "good",
            "bad",
            "stop",
            "success_at_defer",
            "unsuccessful_at_defer",
            "required_recovery",
            "maintained",
            "parent_any_error",
        ),
        0,
    )
    result["N"] = len(rows)
    result["parents"] = len({r["group"] for r in rows})
    bad_parents = set()
    strata = {a: {"assigned": set(), "errors": set()} for a in ("continue", "recover")}
    for r in rows:
        action = r["action"]
        if action is None:
            result[
                "success_at_defer" if r["initial_success"] else "unsuccessful_at_defer"
            ] += 1
            if composition != "primary":
                action = composition.removeprefix("fallback_")
        if action is None:
            result["stop"] += 1
            continue
        good = bool(r["truth"][action])
        result["good" if good else "bad"] += 1
        result["maintained"] += int(good and r["initial_success"])
        result["required_recovery"] += int(
            good
            and action == "recover"
            and not r["initial_success"]
            and not r["truth"]["continue"]
        )
        strata[action]["assigned"].add(r["group"])
        if not good:
            bad_parents.add(r["group"])
            strata[action]["errors"].add(r["group"])
    result["parent_any_error"] = len(bad_parents)
    result["assignment_errors"] = {
        a: {"assigned_parents": len(v["assigned"]), "error_parents": len(v["errors"])}
        for a, v in strata.items()
    }
    assert result["good"] + result["bad"] + result["stop"] == result["N"]
    result["status"] = "DESCRIPTIVE" if rows else "EMPTY_NO_TRIALS"
    return result


def parent_interval(rows, values, seed, draws=4000):
    """Original two conditions form one resampled parent; empty strata add no N."""
    if not rows:
        return {
            "value": 0.0,
            "ci95": [0.0, 0.0],
            "parents": 0,
            "N": 0,
            "status": "EMPTY_NO_TRIALS",
        }
    groups = sorted({r["group"] for r in rows})
    frame = np.asarray(
        [
            [
                sum(v for r, v in zip(rows, values, strict=True) if r["group"] == g),
                sum(r["group"] == g for r in rows),
            ]
            for g in groups
        ],
        dtype=float,
    )
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = frame[rng.integers(len(groups), size=(draws, len(groups)))].sum(axis=1)
    return {
        "value": float(sum(values) / len(rows)),
        "ci95": np.percentile(samples[:, 0] / samples[:, 1], [2.5, 97.5]).tolist(),
        "parents": len(groups),
        "N": len(rows),
        "status": "DESCRIPTIVE",
    }


def scores(rows, composition):
    return [
        int(r["truth"][r["action"] or composition.removeprefix("fallback_")])
        if r["action"] is not None or composition != "primary"
        else 0
        for r in rows
    ]


def finite_ceiling(rows, selected):
    groups = defaultdict(list)
    for r in rows:
        signature = tuple(r["features"]) + tuple(
            r["optional_features"][i] for i in selected
        )
        groups[signature].append(r)
    return sum(
        len(rs)
        for rs in groups.values()
        if any(
            all(r["outcomes"][a + "_value"] for r in rs)
            for a in ("continue", "recover")
        )
    )


def source_audit(root):
    verify_sources(PRIOR)
    _, rows, missing = qualified(PRIOR)
    assert len(rows) == 318 and not missing
    proof = audit_rows(PRIOR, rows)
    table_proof = numerical(PRIOR)
    data = []
    for row in rows:
        raw = load_trace(row)
        truth = {
            a: bool(raw["traces"][a]["frames"][-1]["state"]["success"])
            for a in ("continue", "recover")
        }
        assert truth == {a: row["outcomes"][a + "_value"] for a in truth}
        data.append(
            {
                "id": row["id"],
                "group": row["group"],
                "task": row["task"],
                "condition": row["condition"],
                "initial_success": bool(raw["canonical_start"]["success"]),
                "truth": truth,
                "source": row["source"],
                "source_sha256": row["source_sha256"],
            }
        )
    reference = [json.loads(s) for s in REFERENCE.read_text().splitlines()]
    finite = read(
        Path("results/dsre-rss2027/20261113T193554Z/reused_finite_ceiling.json")
    )
    ceilings = {}
    for task in TASKS:
        rs = [r for r in reference if r["task"] == task]
        assert len(rs) == 422
        for budget in (0, 1, 6):
            old = finite[f"{task}|{budget}"]
            value = finite_ceiling(rs, old["selected"])
            assert value == old["mass"]
            ceilings[f"{task}|{budget}"] = value
    summary = {}
    for task in TASKS:
        rs = [r for r in data if r["task"] == task]
        summary[task] = {
            "N": len(rs),
            "parents": len({r["group"] for r in rs}),
            "categories": {
                f"{int(c)}{int(v)}": sum(
                    r["truth"]["continue"] == c and r["truth"]["recover"] == v
                    for r in rs
                )
                for c, v in ((True, False), (False, True), (True, True), (False, False))
            },
            "raw_continue": sum(r["truth"]["continue"] for r in rs),
            "raw_recover": sum(r["truth"]["recover"] for r in rs),
        }
    case_proof = []
    for case in read(PRIOR / "physical_examples.json")["cases"]:
        raw = load_trace(case)
        assert all(
            bool(raw["traces"][a + "/reference"]["frames"][-1]["state"]["success"])
            == case["outcomes"][a + "_value"]
            for a in ("continue", "recover")
        )
        primary, optional = predicates(
            raw["prefix"][0]["observation"], raw["prefix"][-1]["observation"]
        )
        assert (
            list(primary) == case["features"]
            and list(optional) == case["optional_features"]
        )
        if "dx" in case:
            obs = raw["prefix"][-1]["observation"]["extra"]
            dx = (
                np.asarray(obs["obj_pose"]).reshape(-1)[0]
                - np.asarray(obs["goal_pos"]).reshape(-1)[0]
            )
            assert abs(dx - case["dx"]) < 1e-12
        case_proof.append(
            {
                "case": case["case"],
                "id": case["id"],
                "source": case["source"],
                "sha256": case["source_sha256"],
            }
        )
    atomic(root / "primary_rows.json", data)
    atomic(
        root / "source_audit.json",
        {
            "status": "PASS",
            "summary": summary,
            "paired_selected_and_rule_audit": proof,
            "original_tables_intervals_calibration": table_proof,
            "finite_ceilings": ceilings,
            "physical_case_sources": case_proof,
            "scope": "Read-only independent implementations; no new outcomes or full-paper work",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "source_rows": len(data),
                "selected_repeats": proof["selected_executions"],
            }
        ),
        flush=True,
    )


def secondary(root):
    plan = SecondaryPlan.model_validate(read(root / "secondary_plan.json"))
    assert read(root / "source_audit.json")["status"] == "PASS"
    raw = {r["id"]: r for r in read(root / "primary_rows.json")}
    frozen = read(PRIOR / "test_records.json")
    tables, intervals, contrasts = {}, {}, {}
    for task_index, task in enumerate(TASKS):
        seed = plan.bootstrap_seed + task_index
        for mode in ("calibrated", "proposal"):
            by = defaultdict(list)
            for r in frozen:
                if r["task"] == task and r["mode"] == mode:
                    row = raw[r["id"]] | {
                        "action": r["action"],
                        "category": r["category"],
                    }
                    assert row["initial_success"] == r["initial_success"]
                    assert counts([row])["good"] == r["successful"]
                    by[r["method"]].append(row)
            for method, rows in by.items():
                for composition in plan.compositions:
                    key = f"{task}|{mode}|{method}|{composition}"
                    tables[key] = counts(rows, composition)
                    intervals[key] = parent_interval(
                        rows, scores(rows, composition), seed, plan.bootstrap_draws
                    )
                    for pop in (
                        "nominal",
                        "offset002",
                        "misaligned",
                        "continue_only",
                        "recover_only",
                        "both",
                        "neither",
                        "initial_success",
                        "initial_failure",
                    ):
                        rs = [
                            r
                            for r in rows
                            if pop
                            in (
                                r["condition"],
                                r["category"],
                                "initial_success"
                                if r["initial_success"]
                                else "initial_failure",
                            )
                        ]
                        tables[key + "|" + pop] = counts(rs, composition)
            for other in by:
                primary = by["DSRE_risk"]
                lookup = {r["id"]: r for r in by[other]}
                matched = [lookup[r["id"]] for r in primary]
                for composition in plan.compositions:
                    delta = np.asarray(scores(primary, composition)) - np.asarray(
                        scores(matched, composition)
                    )
                    key = f"{task}|{mode}|DSRE_risk-{other}|{composition}"
                    contrasts[key] = parent_interval(
                        primary, delta.tolist(), seed, plan.bootstrap_draws
                    )
                    if mode == "calibrated" and composition == "primary":
                        old = read(PRIOR / "operational_results.json")[
                            "paired_intervals"
                        ][f"{task}|DSRE_risk-{other}|all"]["successful"]
                        assert (
                            contrasts[key]["value"] == old["value"]
                            and contrasts[key]["ci95"] == old["parent_percentile95"]
                        )
    atomic(
        root / "stop_sensitivity.json",
        {
            "status": "POST_HOC_SECONDARY",
            "plan": plan.model_dump(mode="json"),
            "counts": tables,
            "parent_completion_intervals": intervals,
            "paired_completion_contrasts": contrasts,
            "no_gate_update": True,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "descriptive_tables": len(tables),
                "paired_intervals": len(contrasts),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("source", "secondary"), required=True)
    args = parser.parse_args()
    {"source": source_audit, "secondary": secondary}[args.stage](args.root)
