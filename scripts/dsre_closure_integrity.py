"""Verify original seals and guarded insertion boundaries without new physics."""

from collections import Counter
from pathlib import Path

from dsre_closure_common import INPUTS, NEW, OLD, ROOT, read, save, sha


def main():
    seals = []
    for directory in (OLD, NEW):
        path = directory / "raw_evidence_seal.json"
        seal = read(path)
        reconstructed = 0
        for name, expected in seal["sha256"].items():
            p = Path(name)
            if p.is_file():
                actual = sha(p)
            else:
                read(p)
                actual = INPUTS[name]
                reconstructed += 1
            assert actual == expected, name
        seals.append(
            {
                "seal": str(path),
                "sha256": sha(path),
                "members": len(seal["sha256"]),
                "exact_original_gzip_reconstructions": reconstructed,
                "passed": True,
            }
        )
        print(
            "Original raw seal passed", directory.name, len(seal["sha256"]), flush=True
        )
    root = Path("results/dsre-evidence-aware/20261118-source-eligibility")
    proof = read(root / "independent_source_reproductions.json")
    repetitions = []
    for rep in proof["reproductions"]:
        raw = read(rep["raw_path"])
        assert (
            raw["spec"]["seed"] == 180937078
            and raw["status"] == "FAILED_PREREQUISITE_OR_PREFIX"
        )
        assert (
            len(raw["prefix"]) == 1
            and not raw["prefix_controls"]
            and not raw["post_controls"]
        )
        assert all(
            raw.get(key) is None for key in ("checkpoint", "features", "success")
        )
        repetitions.append(
            {
                "raw": rep["raw_path"],
                "spec": raw["spec"],
                "native_error": raw["error"],
                "controls": 0,
                "checkpoint": False,
                "outcome": None,
                "sha256": INPUTS[rep["raw_path"]],
            }
        )
    assert len(repetitions) == 2
    for name, expected in proof["source_fingerprints"].items():
        assert sha(name) == expected
    guard = read(root / "prospective/PegInsertionSide-v1/SOURCE_GUARD_FAILURE.json")
    old = OLD / "prospective/PegInsertionSide-v1"
    discovery = len(list((old / "discovery").glob("*.json")))
    assert discovery == 128
    assert not list((old / "calibration").glob("*.json")) and not list(
        (old / "test").glob("*.json")
    )
    pilot = [read(p) for p in (NEW / "records/insertion_pilot").glob("*.json")]
    assert len(pilot) == 48 and all(not r["missing"] for r in pilot)
    cells = Counter(str(int(r["yc"])) + str(int(r["yr"])) for r in pilot)
    decision = read(NEW / "insertion_extension_decision.json")
    assert decision["outcomes"] == dict(cells) and decision["extend"] is False
    save(
        ROOT / "E0/raw_integrity_and_insertion_boundary.json",
        {
            "passed": True,
            "raw_seals": seals,
            "original_zero_control_failure_reproductions": repetitions,
            "native_source_fingerprints": len(proof["source_fingerprints"]),
            "later_nonzero_prefix_guard": guard,
            "old_insertion": {
                "discovery": 128,
                "calibration_outcomes": 0,
                "test_decisions": 0,
                "registered_calibration": 1024,
                "registered_test": 256,
                "status": "RETIRED_SOURCE_BLOCKED; no restart authorized",
            },
            "new_insertion_pilot": {
                "registered": 48,
                "qualified": 48,
                "four_cells": dict(cells),
                "missing_endpoints": 0,
                "continue_only_diversity": cells.get("10", 0),
                "conditional_confirmation_completed": 0,
                "conditional_reserved": 96,
                "extended": False,
            },
            "input_sha256": INPUTS,
        },
    )


if __name__ == "__main__":
    main()
