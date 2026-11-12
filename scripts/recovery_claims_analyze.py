"""Registered physical result tables and versioned per-execution certificates."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np

from dual_rec.contracts.claims import (
    Claim,
    MatchedEvidence,
    certify,
    discordance_upper,
    matched_effect,
)
from dual_rec.validation import compare

METHODS = [
    "B0",
    "B1",
    "B2",
    "B3",
    "B4",
    "M",
    "no_F3",
    "no_memory",
    "no_unknown",
    "no_completion",
]


def read(p):
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2, allow_nan=False) + "\n")


def boot(values, seed=20261112):
    if not values:
        return None
    x = np.asarray(values, float)
    g = np.random.default_rng(seed)
    b = [x[g.integers(len(x), size=len(x))].mean() for _ in range(2000)]
    return np.quantile(b, [0.025, 0.975]).tolist()


@lru_cache(maxsize=2)
def trace_file(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


def checkpoint_error(root, r):
    records = trace_file(str((root / r["source_path"]).parent / "traces.json.gz"))[
        "traces"
    ]
    route = (
        "fresh_prefix"
        if r["route"] in ["missing_provenance", "parent_rng"]
        else r["route"]
    )
    e = compare(
        records[r["action"] + "/reference"]["start"],
        records[r["action"] + "/" + route]["start"],
    )
    return max(
        e["position"] / 1e-5,
        e["angle"] / 1e-4,
        e["velocity"] / 1e-4,
        e["qpos"] / 1e-4,
        e["observation"] / 1e-4,
        e["time"] / 1e-9,
        0 if e["contacts"] else 2,
    )


def conservative_difference_interval(delta):
    n = len(delta)
    if not n:
        return None
    gain = sum(d == 1 for d in delta)
    loss = sum(d == -1 for d in delta)
    ug = discordance_upper(gain, n, 0.0125)
    ul = discordance_upper(loss, n, 0.0125)
    lg = 1 - discordance_upper(n - gain, n, 0.0125)
    ll = 1 - discordance_upper(n - loss, n, 0.0125)
    return [max(-1.0, lg - ul), min(1.0, ug - ll)]


def analyze(root):
    rows = []
    source_files = []
    for p in sorted((root / "parents").glob("*/*/*/outcomes.json")):
        for r in read(p):
            rows.append(r | {"source_path": str(p.relative_to(root))})
        source_files.append(
            {
                "path": str(p.relative_to(root)),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
        )
    for r in rows:
        r["checkpoint_error"] = checkpoint_error(root, r)
        r["recorded_trigger_flag"] = r["triggered"]
        if r["task"] == "PushCube-v1":
            from dual_rec.scenarios import failure_trigger

            prefix = trace_file(
                str((root / r["source_path"]).parent / "traces.json.gz")
            )["prefix"]
            r["triggered"] = failure_trigger(prefix)["failed"]
        elif r["task"] == "Lift":
            r["triggered"] = False
    groups = defaultdict(list)
    for r in rows:
        groups[(r["split"], r["task"], r["condition"], r["action"], r["route"])].append(
            r
        )
    # N6 swaps actual physically executed parents, retaining original outcome/control arrays.
    for key, rs in list(groups.items()):
        if key[-1] != "fresh_prefix" or len(rs) < 2:
            continue
        by_seed = {r["seed"]: r for r in rs}
        registered = sorted(read(root / "registration.json")["seeds"][key[1]][key[0]])
        for left, right in zip(registered[::2], registered[1::2], strict=True):
            if left not in by_seed or right not in by_seed:
                continue
            for a, b in [
                (by_seed[left], by_seed[right]),
                (by_seed[right], by_seed[left]),
            ]:
                rows.append(
                    b
                    | {
                        "route": "parent_rng",
                        "expected_history_hash": a["history_hash"],
                        "expected_seed": a["seed"],
                        "violation": "mismatched executed parent/history",
                        "continuations_executed": 0,
                        "original_source_path": b["source_path"],
                    }
                )
    certificates = []
    A = []
    B = []
    E = []
    D = []
    directory = root / "certificates"
    directory.mkdir(exist_ok=True)
    lookup = {
        (r["split"], r["task"], r["seed"], r["condition"], r["action"], r["route"]): r
        for r in rows
    }
    for r in rows:
        partner = lookup.get(
            (
                r["split"],
                r["task"],
                r["seed"],
                r["condition"],
                r["action"],
                "fresh_prefix",
            )
        )
        r["reference_qualified"] = bool(
            partner
            and partner["prefix_ok"]
            and partner["checkpoint_error"] <= 1
            and max(partner["state_errors"]) <= 1
            and trace_file(
                str((root / partner["source_path"]).parent / "traces.json.gz")
            )["traces"][partner["action"] + "/fresh_prefix"].get("controller_memory")
            is not None
            and trace_file(
                str((root / partner["source_path"]).parent / "traces.json.gz")
            )["traces"][partner["action"] + "/fresh_prefix"].get("controller_memory")
            == trace_file(
                str((root / partner["source_path"]).parent / "traces.json.gz")
            )["traces"][partner["action"] + "/reference"].get("controller_memory")
            == trace_file(
                str((root / partner["source_path"]).parent / "traces.json.gz")
            )["snapshot"]["custom"]
        )
    for r in rows:
        cohort = groups.get(
            (r["split"], r["task"], r["condition"], r["action"], r["route"]), []
        )
        qualified = [v for v in cohort if v["prefix_ok"] and v["reference_qualified"]]
        k = sum(v["success"] != v["reference_success"] for v in qualified)
        n = len(qualified)
        model = r["model_hash"]
        if r["route"] == "physics":
            model = hashlib.sha256(
                json.dumps(r["readback"], sort_keys=True).encode()
            ).hexdigest()
        complete = r["reference_qualified"]
        actual_route = (
            "fresh_prefix"
            if r["route"] in ("parent_rng", "missing_provenance")
            else r["route"]
        )
        raw = trace_file(str((root / r["source_path"]).parent / "traces.json.gz"))[
            "traces"
        ][r["action"] + "/" + actual_route]
        controller_hash = (
            hashlib.sha256(
                json.dumps(raw["controller_memory"], sort_keys=True).encode()
            ).hexdigest()
            if raw.get("controller_memory") is not None
            else None
        )
        raw_path = (root / r["source_path"]).parent / "traces.json.gz"
        completion_frames = trace_file(str(raw_path))["traces"][
            r["action"] + "/fresh_prefix"
        ]["frames"]
        c = Claim(
            task=r["task"],
            parent=str(r["seed"]),
            reference_parent=str(r.get("expected_seed", r["seed"])),
            action=r["action"],
            model_hash=model,
            reference_model_hash=r["model_hash"],
            history_hash=r["history_hash"],
            reference_history_hash=r.get("expected_history_hash", r["history_hash"]),
            controller_hash=controller_hash,
            reference_controller_hash=(
                hashlib.sha256(
                    json.dumps(
                        trace_file(str(raw_path))["traces"][
                            r["action"] + "/reference"
                        ].get("controller_memory"),
                        sort_keys=True,
                    ).encode()
                ).hexdigest()
                if trace_file(str(raw_path))["traces"][r["action"] + "/reference"].get(
                    "controller_memory"
                )
                is not None
                else None
            ),
            unobserved_state_fields=r["missing"] if r["model_hash"] is not None else [],
            budget=70,
            actions=r["actions"],
            expected_actions=r["expected_actions"],
            times=r["times"],
            success=[bool(f["state"]["success"]) for f in raw["frames"]],
            state_errors=r["state_errors"],
            checkpoint_error=r["checkpoint_error"],
            initial_success=r["initial_success"],
            contract_violation=r["violation"]
            or (None if r["prefix_ok"] else "fresh-prefix qualification failed"),
            state_injections=int(r["route"] == "midrollout_injection"),
            qualification_parents=n,
            discordances=k,
            completion_qualified=complete,
            completion_success=[bool(f["state"]["success"]) for f in completion_frames],
            trace_hash=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            raw_trace_path=str(raw_path.relative_to(root)),
            raw_trace_key=r["action"] + "/" + actual_route,
            source_path=r["source_path"],
        )
        ident = f"{r['split']}-{r['task']}-{r['seed']}-{r['condition']}-{r['action']}-{r['route']}"
        path = directory / (ident + ".bundle.json")
        save(path, c.model_dump())
        for method in METHODS:
            cert = certify(c, method)
            cert.update(
                split=r["split"],
                condition=r["condition"],
                route=r["route"],
                source_path=r["source_path"],
                bundle=str(path.relative_to(root)),
                bundle_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                control_status="invalid"
                if r["violation"]
                else "incomplete"
                if r["model_hash"] is None
                or controller_hash is None
                or c.reference_controller_hash is None
                else "valid"
                if r["prefix_ok"] and r["reference_qualified"]
                else "unqualified",
                replayed_route="fresh_prefix"
                if cert["completed_with_prefix"]
                else r["route"],
            )
            certificates.append(cert)
        save(
            directory / (ident + ".certificate.json"),
            certify(c)
            | {"bundle_sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        )
    pair_inputs = defaultdict(list)
    for path in sorted(directory.glob("*.bundle.json")):
        payload = read(path)
        if (
            payload.get("raw_trace_key", "").endswith("/fresh_prefix")
            and "parent_rng" not in path.name
            and "missing_provenance" not in path.name
        ):
            key = path.name.rsplit("-" + payload["action"] + "-", 1)[0]
            pair_inputs[key].append(Claim.model_validate(payload))
    pairs = []
    for key, branches in pair_inputs.items():
        if len(branches) == 2:
            pairs.append(
                {
                    "parent_cell": key,
                    **matched_effect(MatchedEvidence(branches=branches)),
                }
            )
    save(root / "matched_certificates.json", pairs)
    for key, rs in groups.items():
        split, task, condition, action, route = key
        qualified = [r for r in rs if r["prefix_ok"] and r["reference_qualified"]]
        B.append(
            {
                "split": split,
                "task": task,
                "condition": condition,
                "action": action,
                "route": route,
                "n": len(rs),
                "qualified": len(qualified),
                "trajectory_pass": sum(
                    max(r["state_errors"]) <= 1 and r.get("checkpoint_error", 0) <= 1
                    for r in rs
                ),
                "discordances": sum(
                    r["success"] != r["reference_success"] for r in qualified
                ),
                "upper": discordance_upper(
                    sum(r["success"] != r["reference_success"] for r in qualified),
                    len(qualified),
                ),
                "cost_error_max": max(
                    abs(r["cost_seconds"] - r["reference_cost_seconds"]) for r in rs
                ),
                "fixed_replay_wall_seconds": sum(
                    r.get("route_wall_seconds", 0) for r in rs
                ),
            }
        )
    parent_groups = defaultdict(list)
    for r in rows:
        if r["route"] == "fresh_prefix":
            parent_groups[(r["split"], r["task"], r["condition"])].append(r)
    for (split, task, condition), rs in parent_groups.items():
        pairs = defaultdict(dict)
        for r in rs:
            pairs[r["seed"]][r["action"]] = r
        valid = [
            v
            for v in pairs.values()
            if len(v) == 2
            and all(
                r["prefix_ok"]
                and r["reference_qualified"]
                and max(r["state_errors"]) <= 1
                and r.get("checkpoint_error", 0) <= 1
                for r in v.values()
            )
        ]
        fail = [
            v
            for v in valid
            if not v["continue"]["initial_success"] and v["continue"]["triggered"]
        ]
        A.append(
            {
                "split": split,
                "task": task,
                "condition": condition,
                "attempted": len(pairs),
                "qualified": len(valid),
                "initial_nonsuccess": sum(
                    not v["continue"]["initial_success"] for v in valid
                ),
                "triggered_failed": len(fail),
                "new_continue": sum(
                    not v["continue"]["initial_success"]
                    and v["continue"]["reference_first_hit"] is not None
                    for v in valid
                ),
                "new_recover": sum(
                    not v["recover"]["initial_success"]
                    and v["recover"]["reference_first_hit"] is not None
                    for v in valid
                ),
            }
        )
        for pop, selected in [
            ("all", valid),
            ("failed", fail),
            ("clean_success", [v for v in valid if v["continue"]["initial_success"]]),
        ]:
            delta = [
                int(v["recover"]["reference_success"])
                - int(v["continue"]["reference_success"])
                for v in selected
            ]
            E.append(
                {
                    "split": split,
                    "task": task,
                    "condition": condition,
                    "population": pop,
                    "n": len(selected),
                    "continue_success": sum(
                        v["continue"]["reference_success"] for v in selected
                    ),
                    "recover_success": sum(
                        v["recover"]["reference_success"] for v in selected
                    ),
                    "difference": float(np.mean(delta)) if delta else None,
                    "ci95": boot(delta),
                    "conservative_exact_difference_ci95": conservative_difference_interval(
                        delta
                    ),
                    "cost_difference": 0 if selected else None,
                    "cost_ci95": [0, 0] if selected else None,
                    "scope": "Fixed 70-step elapsed cost is equal by design; not cost to eventual completion",
                    "general_C4_power": len(fail) >= 30,
                }
            )
    C = []
    cells = defaultdict(list)
    for c in certificates:
        cells[
            (c["split"], c["task"], c["condition"], c["control_status"], c["method"])
        ].append(c)
    for key, cs in cells.items():
        C.append(
            dict(
                zip(
                    ["split", "task", "condition", "control_status", "method"],
                    key,
                    strict=True,
                )
            )
            | {
                s: sum(c["status"] == s for c in cs)
                for s in ["SUPPORTED", "REFUTED_CONTRACT", "INSUFFICIENT_EVIDENCE"]
            }
            | {"records": len(cs)}
        )
    for split in ["development", "confirmation"]:
        for task in ["PickCube-v1", "PushCube-v1", "Lift"]:
            for base in ["B1", "B2", "B4", "no_F3"]:
                for kind in ["valid", "invalid", "incomplete"]:
                    chosen = [
                        c
                        for c in certificates
                        if c["split"] == split
                        and c["task"] == task
                        and c["control_status"] == kind
                        and c["method"] in ["M", base]
                    ]
                    parents = defaultdict(lambda: defaultdict(list))
                    for c in chosen:
                        parents[c["parent"]][c["method"]].append(
                            c["status"] == "SUPPORTED"
                        )
                    means = {
                        p: float(np.mean(v["M"]) - np.mean(v[base]))
                        for p, v in parents.items()
                        if "M" in v and base in v
                    }
                    ds = list(means.values())
                    if kind == "invalid":
                        registered = sorted(
                            read(root / "registration.json")["seeds"][task][split]
                        )
                        ds = [
                            float(
                                np.mean(
                                    [means[str(p)] for p in [a, b] if str(p) in means]
                                )
                            )
                            for a, b in zip(
                                registered[::2], registered[1::2], strict=True
                            )
                            if str(a) in means or str(b) in means
                        ]
                    D.append(
                        {
                            "split": split,
                            "task": task,
                            "baseline": base,
                            "population": kind,
                            "parents": len(means),
                            "inference_clusters": len(ds),
                            "cluster_unit": "registered_parent_pair"
                            if kind == "invalid"
                            else "parent",
                            "admission_difference": float(np.mean(ds)) if ds else None,
                            "ci95": boot(ds),
                            "scope": "Parent means across clustered condition/action variants; all methods consume same physical evidence. Completion cost additional, no savings inferred from admission alone.",
                        }
                    )
    for name, data in [
        ("A_inventory", A),
        ("B_fidelity", B),
        ("C_acceptance", C),
        ("D_baselines", D),
        ("E_effects", E),
        ("F_robustness", [c for c in C if c["control_status"] != "valid"]),
        ("ablations", [c for c in C if c["method"].startswith("no_")]),
    ]:
        save(root / (name + ".json"), data)
        if data:
            with (root / (name + ".csv")).open("w") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                w.writerows(data)
    save(root / "source_records.json", source_files)
    save(root / "all_outcomes.json", rows)
    save(root / "all_certificates.json", certificates)
    print(
        {
            "physical_records": len(rows),
            "certificates": len(certificates),
            "parent_cells": len(A),
            "effects": len(E),
        }
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    assert not (a.root / "completion_manifest.json").exists()
    analyze(a.root)
