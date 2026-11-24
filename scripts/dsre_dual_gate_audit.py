"""Independent six-obligation risk and predecision audit; no selector imports."""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from dsre_dual_adjudication import assert_isolated, gz, read, sha, write_once
from dsre_source_risk_audit import exact_upper
from scipy.stats import beta


def independent_bounds(rows):
    parents = defaultdict(list)
    for row in rows:
        parents[row["seed"]].append(row)
    result = {}
    for method in ("DSRE_risk", "CART2_beta10"):
        for action, endpoint in (
            ("recover", "absolute"),
            ("recover", "nondegradation"),
            ("continue", "absolute"),
        ):
            n = k = 0
            for cells in parents.values():
                relevant = [c for c in cells if c["proposals"][method] == action]
                if not relevant:
                    continue
                n += 1
                errors = [
                    (
                        (c["c"] and not c["r"])
                        if endpoint == "nondegradation"
                        else not c["r" if action == "recover" else "c"]
                    )
                    for c in relevant
                ]
                k += any(errors)
            upper = exact_upper(k, n, 0.05 / 6)
            check = float(beta.ppf(1 - 0.05 / 6, k + 1, n - k)) if n and k < n else 1.0
            assert abs(check - upper) < 1e-12
            result[f"{method}|{action}|{endpoint}"] = {
                "assigned_parents": n,
                "error_parents": k,
                "upper": upper,
                "qualified": bool(n and upper <= 0.1),
            }
    assert_isolated()
    return result


def verify(root):
    plan = read(root / "study_plan.json")
    rows = gz(root / "calibration_rows.json.gz")
    assert {r["seed"] for r in rows} == set(plan["calibration_seeds"]) and len(
        rows
    ) == 1280
    assert read(root / "calibration_physics_audit.json")["complete_cohort"]
    observed = independent_bounds(rows)
    reported = read(root / "dual_calibration.json")
    assert reported["complete_cohort"] and reported["parents"] == 256
    assert reported["family_alpha"] == 0.05 and reported["family_size"] == 6
    assert set(reported["bounds"]) == set(observed)
    for key, actual in observed.items():
        expected = reported["bounds"][key]
        assert all(
            actual[k] == expected[k]
            for k in ("assigned_parents", "error_parents", "qualified")
        )
        assert abs(actual["upper"] - expected["upper"]) < 1e-12
        assert expected["delta"] == 0.05 / 6 and expected["target"] == 0.1
    result = {
        "passed": True,
        "claims": 6,
        "parents": 256,
        "independent_binomial_and_beta_limits_match_original_bisection": True,
        "no_selector_imported": True,
        "calibration_sha256": sha(root / "dual_calibration.json"),
        "epoch": time.time(),
    }
    write_once(root / "dual_calibration_audit.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    verify(parser.parse_args().root)
