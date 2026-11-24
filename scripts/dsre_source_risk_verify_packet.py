"""Portable hash, calibration, selected-action and parent-bootstrap review.

No production selector or simulator import. Raw trajectory verification remains
in the separate physical audit and full local evidence archive.
"""

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def lines(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(packet):
    manifest = read(packet / "packet_manifest.json")
    members = {
        p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()
    }
    assert members == set(manifest["files"]) | {"packet_manifest.json"}
    assert not any(p.endswith(".log") or p.startswith("rss2027/") for p in members)
    for name, expected in manifest["files"].items():
        assert digest(packet / name) == expected, name
    sys.path[:0] = [str(packet / "source/scripts"), str(packet / "source/src")]
    from dsre_source_risk_audit import exact_upper
    from dsre_source_risk_numerical import intervals, isolated_imports

    isolated_imports()
    plan = read(packet / "study_plan.json")
    assert plan["calibration_seeds"] == list(range(15000000, 15000256))
    assert plan["test_seeds"] == list(range(16000000, 16000128))
    assert plan["risk"]["per_stratum_delta"] == 0.05 / 68
    qualification = read(packet / "qualification_audit.json")
    assert qualification["passed"] and qualification["counts"]["continuations"] == 50
    parents = lines(packet / "calibration_parent_labels.jsonl.gz")
    assert [p["seed"] for p in parents] == plan["calibration_seeds"]
    assert all(
        len(p["cells"]) == 5
        and {c["condition"] for c in p["cells"]} == {c[0] for c in plan["profiles"]}
        for p in parents
    )
    calibration = read(packet / "calibration_decision.json")
    assert calibration["complete_cohort"] and calibration["calibration_parents"] == 256
    for method in plan["methods"]:
        for action in ("continue", "recover"):
            assigned = [
                p
                for p in parents
                if any(c["proposals"][method] == action for c in p["cells"])
            ]
            errors = sum(
                any(
                    c["proposals"][method] == action
                    and not c["outcomes"][action + "_value"]
                    for c in p["cells"]
                )
                for p in assigned
            )
            n = len(assigned)
            upper = exact_upper(errors, n)
            reported = calibration["strata"][method + "|" + action]
            assert (n, errors) == (
                reported["assigned_parents"],
                reported["error_parents"],
            )
            assert abs(upper - reported["upper"]) < 1e-11
            assert reported["enabled"] == bool(n and upper <= 0.1)
    test_parents = lines(packet / "test_parent_labels.jsonl.gz")
    result = read(packet / "test_analysis.json")
    assert len(test_parents) == result["parents"]
    test_ids = [p["seed"] for p in test_parents]
    assert len(test_ids) == len(set(test_ids)) and set(test_ids) <= set(
        plan["test_seeds"]
    )
    if result["complete_cohort"]:
        assert test_ids == plan["test_seeds"]
    labels = {
        f"PickCube-v1/{p['seed']}/{c['condition']}": c
        for p in test_parents
        for c in p["cells"]
    }
    grouped = defaultdict(lambda: defaultdict(Counter))
    for rec in lines(packet / "test_metric_records.jsonl.gz"):
        key = "|".join(rec[k] for k in ("scenario", "mode", "method"))
        for name in [key + "|ALL"] + (
            [key + "|" + rec["condition"]] if rec["scenario"] == "clean" else []
        ):
            grouped[name][rec["group"]].update(rec["counts"])
        if rec["scenario"] == "clean" and rec["mode"] in ("proposal", "gated"):
            cell = labels[rec["id"]]
            action = cell["proposals"][rec["method"]]
            if (
                rec["mode"] == "gated"
                and action is not None
                and not calibration["strata"][rec["method"] + "|" + action]["enabled"]
            ):
                action = None
            assert rec["action"] == action
            adequate = bool(action) and cell["outcomes"][action + "_value"]
            assert rec["counts"]["adequate"] == int(adequate)
            assert rec["counts"]["inadequate"] == int(bool(action) and not adequate)
            assert rec["counts"]["stop"] == int(action is None)
    assert grouped.keys() == result["tables"].keys()
    for key, parent_counts in grouped.items():
        counts = Counter()
        for part in parent_counts.values():
            counts.update(part)
        assert {k: v for k, v in counts.items() if v} == {
            k: v for k, v in result["tables"][key]["counts"].items() if v
        }
    estimates = intervals(packet, grouped, lines(packet / "test_rows.jsonl.gz"))
    isolated_imports()
    return {
        "passed": True,
        "files_verified": len(manifest["files"]),
        "calibration_parents": len(parents),
        "test_parents": len(test_parents),
        "action_specific_calibration_bounds_verified": 34,
        **estimates,
        "scope": "Portable statistical review; full raw-state physical audit required separately",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    print(json.dumps(verify(parser.parse_args().packet)))
