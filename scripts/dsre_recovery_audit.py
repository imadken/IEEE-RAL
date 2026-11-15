"""Independent raw-physics, admission and exact-binomial checks for recovery evidence."""

import argparse
import gzip
import json
import math
import time
from pathlib import Path

from dsre_followup_batch import atomic, read, sha, verify_freeze
from dsre_paper_confirmation import difference, expected_action, predicates, state_equal
from scipy.optimize import brentq
from scipy.stats import binom

from dual_rec.dsre.operational import METHODS


def gz(path):
    with gzip.open(path, "rt") as stream:
        return json.load(stream)


def exact_upper(k, n, alpha=0.05 / 68):
    if not n or k == n:
        return 1.0
    if k == 0:
        return -math.expm1(math.log(alpha) / n)
    return brentq(lambda p: binom.cdf(k, n, p) - alpha, k / n, 1, xtol=1e-14)


def audit_parent(root, stage, progress, compare_prior=False):
    p = read(progress)
    assert p["status"] == "COMPLETE"
    directory = root / stage / str(p["seed"])
    dec = read(directory / "decision.json")
    assert sha(directory / "decision.json") == p["decision_sha256"]
    if stage == "test":
        cohort = read(root / "test_recommendation_seal.json")
        begun = read(directory / "execution_started.json")
        assert cohort["parents"] == 160 and len(cohort["decisions"]) == 160
        assert cohort["decisions"][str(p["seed"])] == p["decision_sha256"]
        assert begun["cohort_seal_sha256"] == sha(
            root / "test_recommendation_seal.json"
        )
        assert dec["sealed_epoch"] <= cohort["epoch"] <= begun["epoch"]
    checks = {
        "cells": 0,
        "prefix_states": 0,
        "future_states": 0,
        "contact_states": 0,
        "continuations": 0,
        "all_simulated_controls": 0,
    }
    for cell_index, cell in enumerate(p["cells"]):
        c = cell["condition"]
        d = directory / c
        raw = gz(d / "screen.json.gz")
        assert sha(d / "screen.json.gz") == dec["screens"][c]
        assert raw["screened_epoch"] <= dec["sealed_epoch"]
        primary, optional = predicates(
            raw["prefix"][0]["observation"], raw["canonical_start"]["observation"]
        )
        assert (
            primary == raw["summary"]["features"]
            and optional == raw["summary"]["optional_features"]
        )
        assert raw["packet"]["values"] == primary + [optional[0]]
        assert raw["packet"]["full_values"] == primary + optional
        state_equal(raw["prefix"][-1], raw["canonical_start"])
        assert len(raw["prefix"]) == len(raw["prefix_actions"]) + 1
        checks["all_simulated_controls"] += 2 * len(raw["prefix_actions"])
        assert set(raw["proposals"]) == set(METHODS)
        for m in METHODS:
            assert (
                dec["all_actions"][cell_index][m]["proposal"]
                == raw["proposals"][m]["action"]
            )
        old = None
        if compare_prior:
            old = gz(
                Path("results/dsre-operational/20261114T140659Z/fresh/PickCube-v1")
                / f"{p['seed']}-{c}"
                / "trace.json.gz"
            )
            assert old["prefix_actions"] == raw["prefix_actions"]
            assert (
                old["canonical_controller_memory"] == raw["canonical_controller_memory"]
            )
            assert old["model"] == raw["model"]
            for a, b in zip(old["prefix"], raw["prefix"], strict=True):
                state_equal(a, b)
        for out in cell["outcomes"]:
            assert sha(Path(out["source"])) == out["sha256"]
            execution = gz(Path(out["source"]))
            mode = out["action"]
            assert dec["sealed_epoch"] < execution["completed_epoch"]
            assert execution["controller_memory"] == raw["canonical_controller_memory"]
            assert execution["model_edit"] == raw["model"]["edit"]
            for a, b in zip(raw["prefix"], execution["prefix_states"], strict=True):
                state_equal(a, b)
                checks["prefix_states"] += 1
                checks["contact_states"] += bool(b["contacts"])
            state_equal(raw["canonical_start"], execution["start"])
            previous = execution["start"]
            assert len(execution["frames"]) == 70
            for j, frame in enumerate(execution["frames"]):
                expected = expected_action(
                    "PickCube-v1",
                    mode,
                    j,
                    frame["before_observation"],
                    execution["initial_tcp"],
                )
                assert difference(expected, frame["action"]) <= 2e-6
                assert (
                    difference(previous["observation"], frame["before_observation"])
                    <= 1e-8
                )
                assert abs(frame["state"]["time"] - previous["time"] - 0.05) < 1e-8
                if old:
                    state_equal(
                        old["traces"][mode]["frames"][j]["state"], frame["state"]
                    )
                previous = frame["state"]
                checks["future_states"] += 1
                checks["contact_states"] += bool(previous["contacts"])
            assert (
                bool(previous["success"])
                == out["success"]
                == execution["terminal_success"]
            )
            checks["continuations"] += 1
            checks["all_simulated_controls"] += len(raw["prefix_actions"]) + 70
        checks["cells"] += 1
    return checks


def qualify(root):
    verify_freeze(root)
    checks = audit_parent(
        root, "qualification", root / "progress/qualification-0000.json", True
    )
    plan = read(root / "plan.json")
    new = set(plan["calibration_seeds"]) | set(plan["test_seeds"])
    assert len(new) == 4160
    # Exhaustively inspect prior seed manifests, including abandoned/failed attempts.
    manifests = []
    collisions = []
    for path in Path("results").rglob("*seed_manifest.json"):
        if root in path.parents:
            continue
        obj = read(path)
        manifests.append({"path": str(path), "sha256": sha(path)})

        def walk(x, manifest_path=path):
            if isinstance(x, dict):
                if x.get("seed") in new:
                    collisions.append({"path": str(manifest_path), "seed": x["seed"]})
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)

        walk(obj)
    assert not collisions, collisions
    result = {
        "passed": True,
        "checks": checks,
        "source_distribution_compatibility": "Both registered conditions exactly match old calibration parent8000000 prefix, controller memory, model versions and all280 future states under independent equations; no tolerance or physics change. Same seeded-reset distribution and predicate-only selection. New parent distribution conditional on each frozen recovery assignment.",
        "prior_seed_manifests": manifests,
        "new_seed_collisions": collisions,
        "plan_sha256": sha(root / "plan.json"),
        "epoch": time.time(),
    }
    atomic(root / "qualification_audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["qualify", "audit"])
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.command == "qualify":
        qualify(a.root)
    else:
        result = {}
        for stage in ("qualification", "calibration", "test"):
            total = {}
            n = 0
            for path in sorted((a.root / "progress").glob(stage + "-*.json")):
                if read(path)["status"] != "COMPLETE":
                    continue
                checks = audit_parent(a.root, stage, path)
                n += 1
                for k, v in checks.items():
                    total[k] = total.get(k, 0) + v
            result[stage] = {"parents": n, **total}
        atomic(
            a.root / "physics_audit.json",
            {"passed": True, "checks": result, "epoch": time.time()},
        )
        print(json.dumps(result))


if __name__ == "__main__":
    main()
