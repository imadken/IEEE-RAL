"""Resumable, source-isolated fit and separate paired evaluation commands."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from .baselines import DESCRIPTIONS, decisions, proposals
from .bounds import calibrate, cp, qualifies, solve
from .certificate import minimum
from .diagnosis import plugin_diagnosis
from .partition import fit, route
from .schema import Observation, Pair, Source
from .views import guard_data_access, load_logs, save, sha


def learn(root: Path, regime: str):
    logdir = root / "learner"
    discovery_path = logdir / "discovery.json"
    vocabulary_path = logdir / "vocabulary.json"
    calibration_path = logdir / (
        "calibration_equal_execution.json"
        if regime == "paired_equal_execution"
        else "calibration.json"
    )
    queries_path = logdir / "queries.json"
    pairpath = (
        root
        / "paired_refinement"
        / (
            "calibration_equal_execution.json"
            if regime == "paired_equal_execution"
            else "calibration.json"
        )
    )
    allowed = [discovery_path, vocabulary_path, calibration_path, queries_path]
    paired = regime.startswith("paired")
    if paired:
        allowed.append(pairpath)
    accessed = guard_data_access(Path("results"), allowed, additional_roots=(root,))
    hashes = {str(p): sha(p) for p in allowed}
    discovery = load_logs(discovery_path)
    calibration = load_logs(calibration_path)
    queries = [
        Observation.model_validate(q).model_dump(mode="json")
        for q in json.loads(queries_path.read_text())
    ]
    vocab = tuple(json.loads(vocabulary_path.read_text()))
    scopes = {r.source_scope.model_dump_json() for r in discovery + calibration}
    if len(scopes) != 1:
        raise ValueError("SCOPE_MISMATCH")
    outcome_scope = (discovery + calibration)[0].source_scope
    if any(
        q.get("source_scope") != outcome_scope.model_dump(mode="json") for q in queries
    ):
        raise ValueError("SCOPE_MISMATCH")
    ids = [{r.parent_id for r in rows} for rows in (discovery, calibration)] + [
        {r["parent_id"] for r in queries}
    ]
    assert not ids[0] & ids[1] and not ids[0] & ids[2] and not ids[1] & ids[2]
    partition = fit(discovery, vocab)
    pairs = (
        [Pair.model_validate(r) for r in json.loads(pairpath.read_text())]
        if paired
        else []
    )
    source = Source.PAIRED if paired else Source.LOGGED
    if regime == "observational":
        calibration = [
            r.model_copy(update={"source_type": Source.OBSERVATIONAL})
            for r in calibration
        ]
        source = Source.OBSERVATIONAL
    bounds = {}
    leaves = {}
    k = len(set(partition.cells))
    for c in sorted(set(partition.cells)):
        logs = [r for r in calibration if route(partition, r.x) == c]
        ps = [r for r in pairs if route(partition, r.x) == c]
        e, ledger = calibrate(logs, ps, f"frozen_leaf:{c}", k)
        arms = [[int(r.y) for r in logs if r.action == a] for a in ("c", "r")]
        try:
            b = solve(e)
            bounds[c] = b
            witness = plugin_diagnosis(e, *[sum(v) / len(v) if v else 0 for v in arms])
            sensitivity = {
                ob: {str(toll): qualifies(b, ob, toll) for toll in (0, 0.02, 0.05)}
                for ob in ("useful", "harm_only", "completion")
            }
        except ValueError as error:
            b = None
            witness = {"status": str(error), "detail": "Fail closed"}
            sensitivity = {}
        leaves[c] = {
            "evidence": e.model_dump(mode="json"),
            "ledger": ledger,
            "bounds": b.model_dump(mode="json") if b else None,
            "diagnosis": witness.model_dump(mode="json")
            if hasattr(witness, "model_dump")
            else witness,
            "secondary": sensitivity,
        }
    prop = proposals(partition, discovery)
    output = []
    for query in queries:
        c = route(partition, query["x"])
        e = leaves[c]["evidence"] if c in leaves else None
        independence_pass = bool(
            e
            and e["overlap"]
            and source != Source.OBSERVATIONAL
            and e["p0"]["hi"] * (1 - e["p1"]["lo"]) <= 0.1
            and e["p1"]["lo"] - e["p0"]["hi"] >= 0.05
        )
        actions = decisions(c, bounds, prop, paired, independence_pass)
        cert = minimum(
            partition, query["x"], bounds, source, outcome_scope=outcome_scope
        )
        assert (actions["DSRE"] == "r") == (cert is not None)
        output.append(
            {
                "parent_id": query["parent_id"],
                "leaf": c,
                "actions": actions,
                "certificate": cert.model_dump(mode="json") if cert else None,
            }
        )
    equivalence = (
        {
            name: sum(row["actions"][name] == row["actions"]["DSRE"] for row in output)
            for name in output[0]["actions"]
        }
        if output
        else {}
    )
    result = {
        "regime": regime,
        "development_only": True,
        "source_type": source.value,
        "partition": partition.model_dump(mode="json"),
        "source_scope": outcome_scope.model_dump(mode="json"),
        "leaves": leaves,
        "proposals": prop,
        "decisions": output,
        "baseline_descriptions": DESCRIPTIONS,
        "equal_action_counts_vs_DSRE": equivalence,
        "n_evaluation_queries": len(output),
        "counts": {
            "discovery": len(discovery),
            "calibration_logs": len(calibration),
            "calibration_pairs": len(pairs),
        },
        "execution_budget": len(calibration) + len(pairs),
        "common_discovery_execution_budget": len(discovery),
        "input_whitelist_sha256": hashes,
        "successful_data_reads": list(accessed),
        "confidence_note": "Frozen leaf CP family, not a joint confidence claim over every exploratory evidence regime.",
    }
    save(root / "models" / (regime + ".json"), result)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k
                in (
                    "regime",
                    "counts",
                    "execution_budget",
                    "equal_action_counts_vs_DSRE",
                )
            }
        )
    )


def evaluate(root: Path, regime: str):
    """This evaluator may read paired labels; the learner never calls it."""
    # Each evaluated record is one independent parent, with no sibling pooling.
    model = json.loads((root / "models" / (regime + ".json")).read_text())
    pairs = {
        r.parent_id: r
        for r in [
            Pair.model_validate(r)
            for r in json.loads((root / "evaluator/evaluation_pairs.json").read_text())
        ]
    }
    n = len(pairs)
    models = {}
    rng = np.random.default_rng(2026111702)
    draws = rng.integers(0, n, (2000, n)) if n else None
    classes = Counter(f"{int(r.yc)}{int(r.yr)}" for r in pairs.values())
    for method in next(iter(model["decisions"]), {}).get("actions", {}):
        ys = []
        gains = []
        harms = []
        recovers = []
        rescued = []
        futile = []
        lengths = []
        for row in model["decisions"]:
            r = pairs[row["parent_id"]]
            recover = row["actions"][method] == "r"
            success = r.yr if recover else r.yc
            ys.append(success)
            gains.append(int(success) - int(r.yc))
            harms.append(recover and r.yc and not r.yr)
            recovers.append(recover)
            rescued.append(recover and not r.yc and r.yr)
            futile.append(recover and not r.yc and not r.yr)
            if method == "DSRE" and row["certificate"]:
                lengths.append(len(row["certificate"]["evidence"]))
        rr = sum(recovers)
        hh = sum(harms)
        boot = np.asarray(gains)[draws].mean(axis=1) if n else None
        bound = cp(hh, rr, 0.025)
        qualified_method = method not in (
            "empirical_utility",
            "naive_independence",
            "always_continue",
            "always_recover",
        )
        models[method] = {
            "n": n,
            "recover": rr,
            "continue": n - rr,
            "recovery_coverage": rr / n if n else None,
            "useful_qualification_coverage": rr / n if n and qualified_method else None,
            "success": sum(ys),
            "whole_policy_gain": sum(gains) / n if n else None,
            "gain_parent_bootstrap95": np.quantile(boot, [0.025, 0.975]).tolist()
            if n
            else None,
            "harmful_authorizations": hh,
            "harm_per_recover": hh / rr if rr else None,
            "harm_parent_CP95": bound.model_dump(),
            "rescues_selected": sum(rescued),
            "rescue_opportunities": sum(not r.yc and r.yr for r in pairs.values()),
            "futile_recoveries": sum(futile),
            "certificate_literal_mean": float(np.mean(lengths)) if lengths else None,
            "default_continue_completion": sum(ys),
            "explicit_defer_secondary_completion": sum(
                r.yr
                for row in model["decisions"]
                if row["actions"][method] == "r"
                for r in [pairs[row["parent_id"]]]
            ),
            "secondary_defer_note": "Unqualified states deferred, not assigned physical failure; selected successes counted separately.",
        }
    save(
        root / "evaluations" / (regime + ".json"),
        {
            "development_only": True,
            "four_cell_counts": dict(classes),
            "policies": models,
            "cost_note": "Every historical C/R macro uses70 controls; masked logs are reanalysis, no new execution wall cost inferred.",
            "interval_note": "One-parent descriptive intervals, not the earlier parent-any-condition estimand.",
        },
    )
    print(
        json.dumps(
            {"regime": regime, "classes": dict(classes), "DSRE": models.get("DSRE")}
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("learn", "evaluate"))
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--regime",
        choices=(
            "logged",
            "paired_equal_parent",
            "paired_equal_execution",
            "observational",
        ),
        default="logged",
    )
    args = parser.parse_args()
    (learn if args.stage == "learn" else evaluate)(args.root, args.regime)


if __name__ == "__main__":
    main()
