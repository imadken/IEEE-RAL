"""Independent supervisor mathematics and historical falsification, before physics."""

import argparse
import gzip
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from dsre_last_common import ROOT, save, sha


def diagnostic(rows, dimensions):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row["features"][:dimensions])].append(row)
    stats = []
    for signature, cells in sorted(groups.items()):
        n = len(cells)
        pc = sum(r["c"] for r in cells) / n
        pr = sum(r["r"] for r in cells) / n
        h = sum(r["c"] and not r["r"] for r in cells) / n
        stats.append(
            {
                "x": signature,
                "n": n,
                "pc": pc,
                "pr": pr,
                "h": h,
                "gain": pr - pc,
                "log_h_upper": min(pc, 1 - pr),
                "paired_only": n >= 10
                and pr - pc >= 0.05 - 1e-12
                and h <= 0.1 + 1e-12
                and min(pc, 1 - pr) > 0.1 + 1e-12,
            }
        )
    return {
        "dimensions": dimensions,
        "signatures": len(groups),
        "paired_only": sum(r["paired_only"] for r in stats),
        "cells": stats,
    }


def frontier(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row["features"])].append(row)
    n = len(rows)
    common = sum(
        len(rs)
        for rs in groups.values()
        if all(r["c"] for r in rs) or all(r["r"] for r in rs)
    )
    cells = diagnostic(rows, len(rows[0]["features"]))["cells"] if n else []
    return {
        "n": n,
        "unique_parents": len({r["seed"] for r in rows}),
        "outcomes": dict(Counter(f"{int(r['c'])}{int(r['r'])}" for r in rows)),
        "action_capacity": sum(r["c"] or r["r"] for r in rows),
        "observable_common_action_rows": common,
        "signatures": len(groups),
        "empirical_log_certifiable": sum(
            c["n"]
            for c in cells
            if c["gain"] >= 0.05 - 1e-12 and c["log_h_upper"] <= 0.1 + 1e-12
        ),
        "empirical_paired_only": sum(
            c["n"]
            for c in cells
            if c["gain"] >= 0.05 - 1e-12
            and c["h"] <= 0.1 + 1e-12
            and c["log_h_upper"] > 0.1 + 1e-12
        ),
        "cells": cells,
        "neither_success_witnesses": [r for r in rows if not r["c"] and not r["r"]][:3],
        "opposite_action_witnesses": [
            {
                "signature": x,
                "c_only": next(r for r in rs if r["c"] and not r["r"]),
                "r_only": next(r for r in rs if r["r"] and not r["c"]),
            }
            for x, rs in groups.items()
            if any(r["c"] and not r["r"] for r in rs)
            and any(r["r"] and not r["c"] for r in rs)
        ][:3],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=ROOT / "existing_checks.json")
    args = p.parse_args()
    oracle = subprocess.run(
        [sys.executable, "research/dsre_final_science/supervisor_oracle.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    # Independent production implementation is vertex enumeration, not supervisor HiGHS.
    from dual_rec.evidence_aware.bounds import solve
    from dual_rec.evidence_aware.schema import Band, Evidence

    error = 0.0
    for pc in np.linspace(0, 1, 41):
        for pr in np.linspace(0, 1, 41):
            b = solve(
                Evidence(
                    p0=Band(lo=pc, hi=pc), p1=Band(lo=pr, hi=pr), scope="analytical"
                )
            )
            error = max(
                error,
                abs(b.harm_lower - max(0, pc - pr)),
                abs(b.harm_upper - min(pc, 1 - pr)),
                abs(b.gain_lower - (pr - pc)),
            )
    assert error < 1e-12
    old = Path(
        "results/dsre-operational/20261116T193049Z-dual-obligation/calibration_rows.json.gz"
    )
    with gzip.open(old, "rt") as handle:
        rows = json.load(handle)
    results = [diagnostic(rows, d) for d in (6, 7, 12)]
    assert len(rows) == 1280 and len({r["seed"] for r in rows}) == 256
    assert [r["signatures"] for r in results] == [10, 15, 52]
    assert [r["paired_only"] for r in results] == [0, 0, 0]
    catalog = Path("results/dsre-rss2027/20261113T193554Z/fresh_qualified.jsonl")
    paired = [json.loads(line) for line in catalog.read_text().splitlines() if line]
    strata = defaultdict(list)
    hashes = {str(old): sha(old), str(catalog): sha(catalog)}
    for row in paired:
        source = Path(row["source"])
        assert sha(source) == row["source_sha256"]
        hashes[str(source)] = row["source_sha256"]
        r = {
            "seed": row["seed"],
            "features": row["features"],
            "c": row["outcomes"]["continue_value"],
            "r": row["outcomes"]["recover_value"],
            "source": row["source"],
        }
        strata[row["task"] + "|" + row["condition"]].append(r)
        strata[row["task"] + "|ALL_CONDITIONS"].append(r)
    save(
        args.output,
        {
            "supervisor": json.loads(oracle.stdout),
            "production_grid_instances": 1681,
            "production_max_error": error,
            "old_pick": results,
            "historical_frontiers": {k: frontier(v) for k, v in strata.items()},
            "original_role": "All previously inspected historical roles retained; DEVELOPMENT_FOR_FINAL_ANALYSIS; never new held-out data",
            "limitations": "Empirical point estimates only. Conditions correlated within parent; no checkpoint-IID or additive gap claim.",
            "source_sha256": hashes,
            "unavailable_remote_convenience_files": [
                "DSRE_FINAL_THEORETICAL_CHECK.json",
                "DSRE_FINAL_EXISTING_DATA_CHECK.json",
                "DSRE_FINAL_EXISTING_DATA_DIAGNOSTIC.py",
            ],
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "signatures": [r["signatures"] for r in results],
                "paired_only": [r["paired_only"] for r in results],
                "production_max_error": error,
            }
        )
    )


if __name__ == "__main__":
    main()
