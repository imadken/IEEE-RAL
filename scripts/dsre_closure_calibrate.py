"""E1: freeze obligation contrasts using calibration only, never test labels."""

import hashlib
import itertools
import json
import time
from pathlib import Path

from dsre_closure_common import (
    INPUTS,
    OBLIGATIONS,
    ROOT,
    TASKS,
    b7_certificate,
    calibrated,
    canonical,
    output,
    passed,
    paths,
    read,
    route,
    rule_library,
    save,
)

from dual_rec.evidence_aware.bounds import calibrate, solve
from dual_rec.evidence_aware.certificate import minimum
from dual_rec.evidence_aware.schema import OneAction, Partition, Scope, Source
from dual_rec.evidence_aware.views import guard_data_access


def main():
    allowed = [ROOT / "registration.json"]
    for task in TASKS:
        allowed.extend(paths(task)[key] for key in ("model", "discovery"))
        calibration = paths(task)["calibration"]
        allowed.extend(
            sorted(calibration.glob("*.json"))
            if calibration.is_dir()
            else [calibration]
        )
    accesses = guard_data_access(Path("results"), allowed, additional_roots=(ROOT,))
    registration = read(ROOT / "registration.json")
    tasks = {}
    for task in TASKS:
        source = read(paths(task)["model"])
        freeze = read(paths(task)["discovery"])
        assert source["partition"] == freeze["partition"]
        calibration = paths(task)["calibration"]
        logs = (
            [read(p) for p in sorted(calibration.glob("*.json"))]
            if calibration.is_dir()
            else read(calibration)
        )
        assert len(logs) == len({r["parent_id"] for r in logs}) == 1024
        assert all(
            r["propensity"] == 0.5 and r["counterpart_exposed"] is False for r in logs
        )
        partition = source["partition"]
        p = Partition.model_validate(partition)
        k = len(set(partition["cells"]))
        model = {
            "partition": partition,
            "source_scope": source["source_scope"],
            "proposals": source["proposals"],
            "leaves": {},
        }
        production_bounds = {}
        max_error = 0.0
        for cell in sorted(set(partition["cells"])):
            records = [r for r in logs if route(partition, r["x"]) == cell]
            independent = calibrated(records, [], k, cell)
            evidence, ledger = calibrate(
                [OneAction.model_validate(r) for r in records],
                [],
                f"frozen_leaf:{cell}",
                k,
            )
            got = solve(evidence)
            for field in (
                "harm_lower",
                "harm_upper",
                "gain_lower",
                "gain_upper",
                "failure_upper",
            ):
                max_error = max(
                    max_error,
                    abs(independent["bounds"][field] - getattr(got, field)),
                    abs(
                        independent["bounds"][field]
                        - source["leaves"][str(cell)]["bounds"][field]
                    ),
                )
            assert ledger["per_tail"] == independent["tail"]
            production_bounds[cell] = got
            model["leaves"][str(cell)] = independent
        assert max_error < 1e-10
        queries, checks, timing = [], {}, {}
        for obligation in OBLIGATIONS:
            approved = {
                int(c)
                for c, v in model["leaves"].items()
                if passed(v["bounds"], obligation)
            }
            start = time.perf_counter()
            rules = rule_library(partition, approved)
            library_seconds = time.perf_counter() - start
            checks[obligation] = {
                "queries": 0,
                "full_output_equal": 0,
                "unknown_queries": 0,
                "minimum_certificates": 0,
                "literal_deletions": 0,
                "approved_leaves": sorted(approved),
            }
            timing[obligation] = {
                "B7_library_seconds": library_seconds,
                "B7_query_seconds": 0.0,
                "DSRE_query_seconds": 0.0,
                "comparison_note": "Same CPU process, tiny d=6; diagnostic timing, no solver-speed advantage claim",
            }
            for x in itertools.product((None, False, True), repeat=6):
                start = time.perf_counter()
                cert = minimum(
                    p,
                    x,
                    production_bounds,
                    Source.LOGGED,
                    obligation,
                    outcome_scope=Scope.model_validate(source["source_scope"]),
                )
                timing[obligation]["DSRE_query_seconds"] += time.perf_counter() - start
                start = time.perf_counter()
                ordinary = b7_certificate(model, x, obligation, rules)
                timing[obligation]["B7_query_seconds"] += time.perf_counter() - start
                cert = cert.model_dump(mode="json") if cert else None
                assert canonical(cert) == canonical(ordinary), (task, obligation, x)
                dsre = output(model, x, obligation, cert)
                b7 = output(model, x, obligation, ordinary)
                assert canonical(dsre) == canonical(b7)
                checks[obligation]["queries"] += 1
                checks[obligation]["full_output_equal"] += 1
                if any(v is None for v in x):
                    assert cert is None and dsre["withholding"]["reasons"] == [
                        "UNAVAILABLE_OBSERVATIONS"
                    ]
                    checks[obligation]["unknown_queries"] += 1
                    continue
                if cert:
                    checks[obligation]["minimum_certificates"] += 1
                    checks[obligation]["literal_deletions"] += len(cert["evidence"])
                cell = route(partition, x)
                queries.append(
                    {
                        "x": x,
                        "obligation": obligation,
                        "leaf": cell,
                        "output": dsre,
                        "B7_output": b7,
                        "B7_full_output_sha256": hashlib.sha256(
                            json.dumps(canonical(b7), sort_keys=True).encode()
                        ).hexdigest(),
                        "CART_gain_prefilter": not model["proposals"][str(cell)][
                            "utility"
                        ],
                    }
                )
        tasks[task] = {
            "model": model,
            "queries": queries,
            "checks": checks,
            "timing": timing,
            "max_independent_bound_error": max_error,
        }
        print(task, {o: checks[o]["approved_leaves"] for o in OBLIGATIONS}, flush=True)
    save(
        ROOT / "E1/calibration_freeze.json",
        {
            "created_epoch": time.time(),
            "registration": registration,
            "tasks": tasks,
            "input_sha256": INPUTS,
            "successful_reads": list(accesses),
            "role": "Secondary obligation contrasts; C-only deterministic rules. Retrospective analysis, not a new untouched confirmation.",
            "B7_status": "CERTIFICATE_EQUIVALENCE",
            "shared_postprocessing": "Identical source/bound/scope/witness instrumentation deliberately supplied to every method",
        },
    )


if __name__ == "__main__":
    main()
