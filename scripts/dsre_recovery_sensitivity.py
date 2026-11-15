"""Prespecified offline STOP compositions; no inherited gate or new controller."""

import argparse
import time
from pathlib import Path

import numpy as np
from dsre_followup_batch import atomic, read, sha
from dsre_recovery_analysis import ratio_interval
from dsre_recovery_audit import gz

from dual_rec.dsre.operational import METHODS


def register(root):
    assert not list((root / "test").glob("*/*/continue.json.gz"))
    assert not list((root / "test").glob("*/*/recover.json.gz"))
    atomic(
        root / "stop_sensitivity_plan.json",
        {
            "epoch": time.time(),
            "source_sha256": sha(Path(__file__)),
            "compositions": [
                "primary_STOP_zero",
                "already_successful_at_STOP_no_hold_outcome",
                "STOP_continue",
                "STOP_recover",
            ],
            "rule": "Retain every nonSTOP action; replace STOP only by the named fixed existing action. No outcome-selected fallback, gate, threshold or controller. Offline sensitivity only; no transferred risk guarantee. Same compositions as the historical Stage1 analysis.",
            "bootstrap": {"draws": 4000, "seed": 2026111501, "unit": "parent"},
            "test_future_outcomes_observed": False,
        },
    )


def analyze(root):
    assert (
        sha(Path(__file__))
        == read(root / "stop_sensitivity_plan.json")["source_sha256"]
    )
    records = read(root / "test_records.json")
    truth = {}
    initial = {}
    for path in sorted((root / "progress").glob("test-*.json")):
        p = read(path)
        if p["status"] != "COMPLETE":
            continue
        d = root / "test" / str(p["seed"])
        for c in p["cells"]:
            key = f"PickCube-v1/{p['seed']}/{c['condition']}"
            truth[key] = {
                a: bool(
                    gz(d / c["condition"] / (a + ".json.gz"))["frames"][-1]["state"][
                        "success"
                    ]
                )
                for a in ("continue", "recover")
            }
            initial[key] = bool(
                gz(d / c["condition"] / "screen.json.gz")["canonical_start"]["success"]
            )
    base = [
        r for r in records if r["method"] == "DSRE_risk" and r["mode"] == "calibrated"
    ]
    groups = [r["group"] for r in base]
    n = len(set(groups))
    if not n:
        atomic(root / "stop_sensitivity.json", {"status": "NO_QUALIFIED_TEST_PARENTS"})
        return
    indices = np.random.default_rng(2026111501).integers(0, n, (4000, n))
    scores = {}
    tables = {}
    contrasts = {}
    for m in METHODS:
        rows = [r for r in records if r["method"] == m and r["mode"] == "calibrated"]
        assert [r["id"] for r in rows] == [r["id"] for r in base]
        for name, fallback in (
            ("primary", None),
            ("STOP_continue", "continue"),
            ("STOP_recover", "recover"),
        ):
            selected = [r["action"] if r["action"] else fallback for r in rows]
            good = [
                int(bool(a) and truth[r["id"]][a])
                for r, a in zip(rows, selected, strict=True)
            ]
            acted = [int(bool(a)) for a in selected]
            scores[m, name] = good
            tables[m + "|" + name] = {
                "N": len(rows),
                "parents": n,
                "good": sum(good),
                "bad": sum(acted) - sum(good),
                "stop": len(rows) - sum(acted),
                "success_at_original_STOP": sum(
                    r["action"] is None and initial[r["id"]] for r in rows
                ),
                "required_recovery": sum(
                    a == "recover"
                    and not initial[r["id"]]
                    and not truth[r["id"]]["continue"]
                    and truth[r["id"]]["recover"]
                    for r, a in zip(rows, selected, strict=True)
                ),
                "completion_interval": ratio_interval(
                    good, [1] * len(rows), groups, indices
                ),
                "scope": "Original gate applies only to primary; composed fallbacks are unqualified descriptive sensitivities, no hold outcome inferred.",
            }
    for name in ("primary", "STOP_continue", "STOP_recover"):
        for m in METHODS:
            delta = [
                a - b
                for a, b in zip(scores["DSRE_risk", name], scores[m, name], strict=True)
            ]
            contrasts[m + "|" + name] = ratio_interval(
                delta, [1] * len(delta), groups, indices
            )
    atomic(
        root / "stop_sensitivity.json",
        {
            "status": "COMPLETE" if n == 160 else "INCOMPLETE_COHORT",
            "tables": tables,
            "paired_risk_minus_baselines": contrasts,
            "plan_sha256": sha(root / "stop_sensitivity_plan.json"),
            "epoch": time.time(),
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["register", "analyze"])
    p.add_argument("root", type=Path)
    a = p.parse_args()
    if a.command == "register":
        register(a.root)
    else:
        analyze(a.root)
