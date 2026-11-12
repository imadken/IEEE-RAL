"""Independent physical trace arithmetic and certificate checks; no compared code imports."""

import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta


def read(p):
    return json.loads(p.read_text())


def initial_score(a, b):
    def flat(x):
        if isinstance(x, dict):
            return [v for k in sorted(x) for v in flat(x[k])]
        return np.asarray(x, dtype=float).ravel().tolist()

    qa = np.asarray(a["quaternion"]).ravel()
    qb = np.asarray(b["quaternion"]).ravel()
    angle = 2 * math.acos(
        min(1, abs(float(np.dot(qa / np.linalg.norm(qa), qb / np.linalg.norm(qb)))))
    )
    return max(
        np.linalg.norm(np.asarray(a["position"]) - b["position"]) / 1e-5,
        angle / 1e-4,
        np.max(np.abs(np.asarray(a["velocity"]) - b["velocity"])) / 1e-4,
        np.max(np.abs(np.asarray(a["qpos"]) - b["qpos"])) / 1e-4,
        np.max(np.abs(np.array(flat(a["observation"])) - flat(b["observation"])))
        / 1e-4,
        abs(a["time"] - b["time"]) / 1e-9,
        0 if a["contacts"] == b["contacts"] else 2,
    )


def audit(root):
    rows = []
    physics_steps = 0
    continuations = 0
    traces_checked = 0
    for p in sorted((root / "parents").glob("*/*/*/outcomes.json")):
        records = read(p)
        meta = read(p.parent / "checkpoint.json")
        assert hashlib.sha256(p.read_bytes()).hexdigest() == meta["outcomes_sha256"]
        continuations += meta["physical_continuations"]
        physics_steps += meta.get("physics_control_steps", 0)
        with gzip.open(p.parent / "traces.json.gz", "rt") as f:
            raw = json.load(f)
        for r in records:
            if r["route"] == "missing_provenance":
                continue
            trace = raw["traces"][r["action"] + "/" + r["route"]]
            reference = raw["traces"][r["action"] + "/reference"]
            frames = trace["frames"]
            ref = reference["frames"]
            traces_checked += 1
            assert len(frames) == len(ref) == len(r["actions"]) == 70
            values = [bool(v["state"]["success"]) for v in frames]
            truth = [bool(v["state"]["success"]) for v in ref]
            assert values[-1] == r["success"] and truth[-1] == r["reference_success"]
            assert (
                next((i + 1 for i, v in enumerate(values) if v), None) == r["first_hit"]
            )
            assert [v["state"]["time"] for v in frames] == r["times"]
            errors = []

            def flatten(x):
                if isinstance(x, dict):
                    return [v for k in sorted(x) for v in flatten(x[k])]
                return np.asarray(x, dtype=float).ravel().tolist()

            for a, b in zip(ref, frames, strict=True):
                a, b = a["state"], b["state"]
                qa = np.asarray(a["quaternion"]).ravel()
                qb = np.asarray(b["quaternion"]).ravel()
                angle = 2 * math.acos(
                    min(
                        1,
                        abs(
                            float(
                                np.dot(qa / np.linalg.norm(qa), qb / np.linalg.norm(qb))
                            )
                        ),
                    )
                )
                e = max(
                    np.linalg.norm(np.asarray(a["position"]) - b["position"]) / 1e-5,
                    angle / 1e-4,
                    np.max(np.abs(np.asarray(a["velocity"]) - b["velocity"])) / 1e-4,
                    np.max(np.abs(np.asarray(a["qpos"]) - b["qpos"])) / 1e-4,
                    np.max(
                        np.abs(
                            np.array(flatten(a["observation"]))
                            - flatten(b["observation"])
                        )
                    )
                    / 1e-4,
                    abs(a["time"] - b["time"]) / 1e-9,
                    0 if a["contacts"] == b["contacts"] else 2,
                    0 if a["success"] == b["success"] else 2,
                )
                errors.append(float(e))
            # Arccos near zero can differ by a few ulps without crossing the
            # frozen threshold. Compare gate membership and physical residuals.
            assert [v <= 1 for v in errors] == [v <= 1 for v in r["state_errors"]], (
                p,
                r["route"],
            )
            if r["task"] == "PushCube-v1":
                pre = raw["prefix"]
                first, last = pre[-11], pre[-1]

                def distance(s):
                    return np.linalg.norm(
                        np.asarray(s["position"])[:2]
                        - np.asarray(s["observation"]["extra"]["goal_pos"][0])[:2]
                    )

                progress = distance(first) - distance(last)
                r["triggered"] = not last["success"] and (
                    progress < 0.01
                    or not any(v["robot_object_contact"] for v in pre[-10:])
                )
            elif r["task"] == "Lift":
                r["triggered"] = False
            r["checkpoint_error"] = initial_score(reference["start"], trace["start"])
            fresh = raw["traces"][r["action"] + "/fresh_prefix"]
            fresh_row = next(
                v
                for v in records
                if v["route"] == "fresh_prefix" and v["action"] == r["action"]
            )
            r["reference_qualified"] = (
                fresh_row["prefix_ok"]
                and max(fresh_row["state_errors"]) <= 1
                and initial_score(reference["start"], fresh["start"]) <= 1
                and fresh.get("controller_memory") is not None
                and fresh.get("controller_memory")
                == reference.get("controller_memory")
                == raw["snapshot"]["custom"]
            )
            rows.append(r)
    for b in read(root / "B_fidelity.json"):
        chosen = [
            r
            for r in rows
            if all(
                r[k] == b[k] for k in ["split", "task", "condition", "action", "route"]
            )
        ]
        if b["route"] == "missing_provenance":
            continue
        assert len(chosen) == b["n"]
        chosen = [r for r in chosen if r["prefix_ok"] and r["reference_qualified"]]
        assert len(chosen) == b["qualified"]
        k = sum(r["success"] != r["reference_success"] for r in chosen)
        assert b["discordances"] == k
        upper = (
            float(beta.ppf(1 - 0.005, k + 1, len(chosen) - k))
            if k < len(chosen)
            else 1.0
        )
        assert abs(upper - b["upper"]) < 1e-10
    # Check every emitted bundle against raw frame labels/time/controls and its
    # certificate digest. Independent contract status arithmetic follows actual
    # supplied observations, not the compared certify function.
    certificates = read(root / "all_certificates.json")
    bundle_cache = {}
    for cert in certificates:
        name = cert["bundle"]
        if name not in bundle_cache:
            bundle_cache[name] = read(root / name)
        c = bundle_cache[name]
        assert (
            hashlib.sha256((root / name).read_bytes()).hexdigest()
            == cert["bundle_sha256"]
        )
        badbudget = len(c["actions"]) != c["budget"] or len(c["times"]) != c["budget"]
        badmodel = (
            c["reference_model_hash"] is not None
            and c["model_hash"] is not None
            and c["reference_model_hash"] != c["model_hash"]
        )
        badparent = (
            c["reference_parent"] is not None and c["parent"] != c["reference_parent"]
        )
        badhistory = (
            c["reference_history_hash"] is not None
            and c["history_hash"] != c["reference_history_hash"]
        )
        badcontroller = (
            cert["method"] != "no_memory"
            and c.get("reference_controller_hash") is not None
            and c["controller_hash"] is not None
            and c["controller_hash"] != c["reference_controller_hash"]
        )
        badaction = c["actions"] != c["expected_actions"]
        injected = c["state_injections"] > 0
        wrongtime = not np.allclose(np.diff(c["times"]), 0.05, rtol=0, atol=1e-7)
        violation = bool(c["contract_violation"]) and not (
            cert["method"] == "no_memory"
            and c["contract_violation"].startswith("controller")
        )
        known_bad = (
            badbudget
            or badmodel
            or badparent
            or badhistory
            or badcontroller
            or badaction
            or injected
            or violation
            or wrongtime
        )
        missing = [
            k
            for k in [
                "model_hash",
                "history_hash",
                "controller_hash",
                "reference_controller_hash",
            ]
            if c[k] is None
        ]
        completable = bool(missing) and not any(
            f in missing for f in ["model_hash", "history_hash"]
        )
        f2 = (
            c["checkpoint_error"] <= 1
            and len(c["state_errors"]) == 70
            and max(c["state_errors"]) <= 1
        )
        method = cert["method"]
        upper = (
            float(
                beta.ppf(
                    1 - c["alpha"],
                    c["discordances"] + 1,
                    c["qualification_parents"] - c["discordances"],
                )
            )
            if c["qualification_parents"] > c["discordances"]
            else 1.0
        )
        decision = upper <= c["epsilon"] and method != "no_F3"
        if method == "B0":
            expected = "SUPPORTED"
        elif known_bad:
            expected = "REFUTED_CONTRACT"
        elif (
            method == "B3"
            or completable
            and c["completion_qualified"]
            and method in ["M", "B4", "no_F3", "no_unknown"]
        ):
            expected = "SUPPORTED"
        elif missing and not (
            method == "no_memory"
            and all(
                k in ["controller_hash", "reference_controller_hash"] for k in missing
            )
        ):
            expected = "INSUFFICIENT_EVIDENCE"
        elif method in ["B1", "B2"]:
            expected = "SUPPORTED" if f2 else "INSUFFICIENT_EVIDENCE"
        elif (
            method == "B4"
            or f2
            or decision
            or c["completion_qualified"]
            and method != "no_completion"
        ):
            expected = "SUPPORTED"
        else:
            expected = "INSUFFICIENT_EVIDENCE"
        if method == "no_unknown" and expected == "INSUFFICIENT_EVIDENCE":
            expected = "SUPPORTED"
        assert expected == cert["status"], (name, method, expected, cert["status"])
        assert bool(cert["witness"]) == bool(known_bad) or method in ["B0", "no_memory"]
    for e in read(root / "E_effects.json"):
        chosen = [
            r
            for r in rows
            if r["route"] == "fresh_prefix"
            and all(r[k] == e[k] for k in ["split", "task", "condition"])
        ]
        parents = defaultdict(dict)
        for r in chosen:
            parents[r["seed"]][r["action"]] = r
        selected = [
            v
            for _, v in sorted(parents.items())
            if len(v) == 2
            and all(
                r["prefix_ok"]
                and r["reference_qualified"]
                and r["checkpoint_error"] <= 1
                and max(r["state_errors"]) <= 1
                for r in v.values()
            )
        ]
        if e["population"] == "failed":
            selected = [
                v
                for v in selected
                if not v["continue"]["initial_success"] and v["continue"]["triggered"]
            ]
        if e["population"] == "clean_success":
            selected = [v for v in selected if v["continue"]["initial_success"]]
        assert len(selected) == e["n"]
        delta = [
            int(v["recover"]["reference_success"])
            - int(v["continue"]["reference_success"])
            for v in selected
        ]
        if delta:
            assert abs(sum(delta) / len(delta) - e["difference"]) < 1e-12
            n = len(delta)
            gain = sum(d == 1 for d in delta)
            loss = sum(d == -1 for d in delta)
            lower = lambda k, n=n: float(beta.ppf(0.0125, k, n - k + 1)) if k else 0.0
            upper = lambda k, n=n: (
                float(beta.ppf(0.9875, k + 1, n - k)) if k < n else 1.0
            )
            assert np.allclose(
                e["conservative_exact_difference_ci95"],
                [max(-1, lower(gain) - upper(loss)), min(1, upper(gain) - lower(loss))],
            )

            rng = np.random.default_rng(20261112)
            bs = [
                np.mean(rng.choice(delta, size=len(delta), replace=True))
                for _ in range(2000)
            ]
            assert np.allclose(np.quantile(bs, [0.025, 0.975]), e["ci95"])
    for report in read(root / "D_baselines.json"):
        picked = [
            c
            for c in certificates
            if c["split"] == report["split"]
            and c["task"] == report["task"]
            and c["control_status"] == report["population"]
            and c["method"] in ["M", report["baseline"]]
        ]
        parents = defaultdict(lambda: defaultdict(list))
        for c in picked:
            parents[c["parent"]][c["method"]].append(c["status"] == "SUPPORTED")
        values = {
            p: np.mean(v["M"]) - np.mean(v[report["baseline"]])
            for p, v in parents.items()
            if "M" in v and report["baseline"] in v
        }
        delta = list(values.values())
        if report["population"] == "invalid":
            ids = sorted(
                read(root / "registration.json")["seeds"][report["task"]][
                    report["split"]
                ]
            )
            delta = [
                np.mean([values[str(p)] for p in [a, b] if str(p) in values])
                for a, b in zip(ids[::2], ids[1::2], strict=True)
                if str(a) in values or str(b) in values
            ]
        if delta:
            rng = np.random.default_rng(20261112)
            bs = [
                float(np.mean(rng.choice(delta, size=len(delta), replace=True)))
                for _ in range(2000)
            ]
            assert np.isclose(np.mean(delta), report["admission_difference"])
            assert np.allclose(np.quantile(bs, [0.025, 0.975]), report["ci95"])
    result = {
        "status": "PASS",
        "physical_traces": traces_checked,
        "physical_continuations": continuations,
        "physics_control_steps_recorded": physics_steps,
        "certificates": len(certificates),
        "effect_cells": len(read(root / "E_effects.json")),
        "scope": "Independent software arithmetic, same operator; no independent human evaluation; exact binomial conditional on distinct parent seeds within each condition/action domain",
    }
    (root / "independent_audit.json").write_text(json.dumps(result, indent=2))
    print(result)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    audit(p.parse_args().root)
