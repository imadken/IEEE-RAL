"""Read-only portable statistics audit; full raw physics is verified separately."""

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(packet):
    manifest = read(packet / "packet_manifest.json")
    members = {
        p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()
    }
    assert members == set(manifest["files"]) | {"packet_manifest.json"}
    assert not any(
        name.endswith(".log") or name.startswith("rss2027/") for name in members
    )
    for name, expected in manifest["files"].items():
        assert digest(packet / name) == expected, name
    sys.path[:0] = [str(packet / "source/scripts"), str(packet / "source/src")]
    import numpy as np
    from dsre_dual_adjudication import assert_isolated, gz
    from dsre_dual_gate_audit import independent_bounds
    from dsre_dual_numerical import check_interval, independently_count, policy_actions

    assert_isolated()
    plan = read(packet / "study_plan.json")
    assert plan["calibration_seeds"] == list(range(17000000, 17000256))
    assert plan["test_seeds"] == list(range(18000000, 18000128))
    assert (
        plan["risk"]["per_claim_delta"] == 0.05 / 6 and plan["risk"]["family_size"] == 6
    )
    calibration = gz(packet / "calibration_rows.json.gz")
    test = gz(packet / "test_rows.json.gz")
    assert len(calibration) == 1280 and len(test) == 640
    assert {r["seed"] for r in calibration} == set(plan["calibration_seeds"])
    assert {r["seed"] for r in test} == set(plan["test_seeds"])
    bounds = independent_bounds(calibration)
    sealed = read(packet / "dual_calibration.json")
    assert sealed["complete_cohort"] and sealed["parents"] == 256
    assert len(bounds) == len(sealed["bounds"]) == 6
    for key, value in bounds.items():
        for field in ("assigned_parents", "error_parents", "qualified"):
            assert value[field] == sealed["bounds"][key][field]
        assert abs(value["upper"] - sealed["bounds"][key]["upper"]) < 1e-12
    lookup = {(r["seed"], r["condition"]): r for r in test}
    assert len(lookup) == 640
    actions = {
        identity: policy_actions(packet, row) for identity, row in lookup.items()
    }
    grouped, unique = defaultdict(lambda: defaultdict(Counter)), set()
    with gzip.open(packet / "policy_records.jsonl.gz", "rt") as stream:
        for line in stream:
            rec = json.loads(line)
            key = (rec["seed"], rec["condition"], rec["policy"])
            assert key not in unique
            unique.add(key)
            identity = key[:2]
            action = actions[identity][rec["policy"]]
            assert action == rec["action"]
            count = independently_count(lookup[identity], action)
            assert count == rec["counts"]
            for population in ("ALL", rec["condition"]):
                grouped[rec["policy"] + "|" + population][rec["seed"]].update(count)
    assert len(unique) == 8320
    result = read(packet / "dual_results.json")
    assert grouped.keys() == result["tables"].keys()
    sample = np.random.Generator(np.random.PCG64(2026111603)).integers(
        0, 128, (4000, 128)
    )
    ratios = {
        "completion": ("success", "rows"),
        "coverage": ("acted", "rows"),
        "conditional_success": ("success", "acted"),
        "required_recovery_recall": ("required_selected", "required"),
        "useful_recoveries_per_R": ("required_selected", "recover"),
        "recovery_per_failed_start": ("required_selected", "initially_unsuccessful"),
        "harm_per_R": ("harm_R", "recover"),
        "futile_per_R": ("futile_R", "recover"),
        "matched_recovery_effect": ("physical_recovery_gain", "recover"),
        "completion_effect_vs_continue": ("completion_minus_continue", "rows"),
    }
    checks = 0
    for key, parents in grouped.items():
        total = Counter()
        for values in parents.values():
            total.update(values)
        assert dict(total) == result["tables"][key]["counts"]
        ids = sorted(parents)
        assert len(ids) == 128
        for name, (num, den) in ratios.items():
            check_interval(
                [parents[p][num] for p in ids],
                [parents[p][den] for p in ids],
                sample,
                result["tables"][key]["intervals"][name],
            )
            checks += 1
    contrast_fields = {
        "completion": ("success", "rows"),
        "coverage": ("acted", "rows"),
        "required_recovery_recall": ("required_selected", "required"),
        "harm": ("harm_R", "rows"),
        "futile_recovery_burden": ("futile_R", "rows"),
        "recovery_attempt_rate": ("recover", "rows"),
    }
    for key, reported in result["comparisons"].items():
        pair, population, metric = key.split("|")
        a, b = pair.split("_minus_")
        left, right = grouped[a + "|" + population], grouped[b + "|" + population]
        num, den = contrast_fields[metric]
        ids = sorted(left)
        check_interval(
            [left[p][num] - right[p][num] for p in ids],
            [left[p][den] for p in ids],
            sample,
            reported,
        )
    assert read(packet / "independent_dual_numerical_audit.json")["passed"]
    assert_isolated()
    return {
        "passed": True,
        "files_verified": len(manifest["files"]),
        "claims": 6,
        "calibration_parents": 256,
        "test_parents": 128,
        "policy_records": len(unique),
        "tables": len(grouped),
        "intervals": checks,
        "paired_intervals": len(result["comparisons"]),
        "scope": "Portable statistical/decision-seal check; full state/contact qualification remains in independently audited local raw archive",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    print(json.dumps(verify(parser.parse_args().packet)))
